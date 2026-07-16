"""Tests for the standalone Batch Processor tracker state model."""

import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock


test_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_dir)
package_root_dir = os.path.dirname(tests_dir)
for path in [package_root_dir, tests_dir]:
    if path not in sys.path:
        sys.path.append(path)

from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_events
from gt.tools.batch_processor.tracker import tracker_model
from gt.tools.batch_processor.tracker import tracker_scheduler


class TestBatchProcessorTracker(unittest.TestCase):
    """Tests tracker state transitions without Maya or Qt."""

    def create_job(self):
        """Creates a two-task test job.

        Returns:
            TrackerJob: Test job.
        """
        definitions = [
            {"id": "rename", "number": 1, "name": "Rename", "icon": "ui_rename"},
            {"id": "save", "number": 2, "name": "Save", "icon": "ui_save"},
        ]
        return tracker_model.TrackerJob("job-0001", 1, "C:/input/source.ma", definitions)

    def test_completed_warning_status_uses_requested_short_label(self):
        expected = "Completed (Warnings)"
        self.assertEqual(expected, tracker_constants.Status.COMPLETED_WARNINGS)

    def test_every_status_has_a_progress_color(self):
        status_values = [
            value
            for key, value in vars(tracker_constants.Status).items()
            if key.isupper() and isinstance(value, str)
        ]

        for status in status_values:
            self.assertIn(status, tracker_constants.STATUS_COLORS)

    def test_job_progress_aggregates_task_progress(self):
        job = self.create_job()
        job.tasks[0].progress = 100
        job.tasks[1].progress = 50

        expected = 75
        self.assertEqual(expected, job.progress)

    def test_session_health_state_uses_expected_precedence(self):
        job = self.create_job()
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [job], "C:/session")

        expected = tracker_constants.HealthState.STARTING
        self.assertEqual(expected, session.health_state)
        job.status = tracker_constants.Status.RUNNING
        expected = tracker_constants.HealthState.RUNNING
        self.assertEqual(expected, session.health_state)
        job.status = tracker_constants.Status.COMPLETED
        session.finish()
        expected = tracker_constants.HealthState.COMPLETED
        self.assertEqual(expected, session.health_state)
        job.status = tracker_constants.Status.COMPLETED_WARNINGS
        expected = tracker_constants.HealthState.WARNING
        self.assertEqual(expected, session.health_state)
        job.status = tracker_constants.Status.FAILED
        expected = tracker_constants.HealthState.ERROR
        self.assertEqual(expected, session.health_state)
        session.aborting = True
        expected = tracker_constants.HealthState.ABORTED
        self.assertEqual(expected, session.health_state)

    def test_skipped_task_produces_completed_warning_job(self):
        job = self.create_job()
        job.apply_event(
            {"event": "task_finished", "task_id": "rename", "status": "skipped"},
            flag_skips_as_warnings=True,
        )
        job.apply_event(
            {"event": "task_finished", "task_id": "save", "status": "succeeded"},
            flag_skips_as_warnings=True,
        )
        job.apply_event(
            {"event": "job_finished", "status": "completed"},
            flag_skips_as_warnings=True,
        )

        expected = tracker_constants.Status.COMPLETED_WARNINGS
        self.assertEqual(expected, job.status)
        expected = tracker_constants.Status.SKIPPED
        self.assertEqual(expected, job.tasks[0].status)
        expected = 0
        self.assertEqual(expected, job.warnings)
        self.assertTrue(any("Skipped 1 item" in message for level, message in job.tasks[0].messages))

    def test_skipped_task_can_complete_without_warning(self):
        job = self.create_job()
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [job], "C:/session")
        session.apply_event(
            {"event": "task_finished", "job_id": job.id, "task_id": "rename", "status": "skipped"}
        )
        session.apply_event(
            {"event": "task_finished", "job_id": job.id, "task_id": "save", "status": "succeeded"}
        )
        session.apply_event({"event": "job_finished", "job_id": job.id, "status": "completed"})

        session.set_flag_skips_as_warnings(False)

        expected = tracker_constants.Status.COMPLETED
        self.assertEqual(expected, job.status)
        expected = tracker_constants.Status.SKIPPED
        self.assertEqual(expected, job.tasks[0].status)
        expected = 0
        self.assertEqual(expected, job.warnings)
        self.assertTrue(
            any(
                "Skipped 1 item." in message
                for level, message in job.tasks[0].messages
            )
        )

    def test_skip_notice_does_not_increment_task_warnings(self):
        job = self.create_job()
        job.apply_event(
            {
                "event": "skip_notice",
                "task_id": "rename",
                "message": "Output exists and will be skipped.",
            }
        )

        expected = 0
        self.assertEqual(expected, job.tasks[0].warnings)
        self.assertTrue(any(level == "Info" for level, message in job.tasks[0].messages))

    def test_error_event_fails_task_and_job(self):
        job = self.create_job()
        job.apply_event({"event": "error", "task_id": "rename", "message": "Failed"})
        job.apply_event({"event": "task_finished", "task_id": "rename", "status": "failed"})
        job.apply_event({"event": "job_finished", "status": "failed"})

        expected = tracker_constants.Status.FAILED
        self.assertEqual(expected, job.status)
        expected = 1
        self.assertEqual(expected, job.errors)

    def test_event_reader_preserves_partial_line_until_complete(self):
        file_handle, event_path = tempfile.mkstemp(suffix=".jsonl")
        os.close(file_handle)
        self.addCleanup(lambda: os.path.isfile(event_path) and os.remove(event_path))
        reader = tracker_events.EventReader(event_path)
        with open(event_path, "w", encoding="utf-8") as event_file:
            event_file.write('{"schema_version": 1, "event": "job_started"')

        expected = []
        self.assertEqual(expected, reader.read_new())
        with open(event_path, "a", encoding="utf-8") as event_file:
            event_file.write("}\n")

        expected = ["job_started"]
        result = reader.read_new()
        self.assertEqual(expected, [event.get("event") for event in result])

    def test_scheduler_consumes_events_and_completes_job(self):
        class FakeProcess:
            """Controllable scheduler process double."""

            def __init__(self):
                """Initializes a running process double."""
                self.pid = 1234
                self.return_code = None

            def poll(self):
                """Gets the configured return code.

                Returns:
                    int or None: Configured process state.
                """
                return self.return_code

        session_dir = tempfile.mkdtemp(prefix="gt_tracker_scheduler_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        project_log_path = os.path.join(session_dir, "project.log")
        with open(project_log_path, "w", encoding="utf-8") as project_log:
            project_log.write("Launcher output\n")
        job = tracker_model.TrackerJob(
            "job-0001",
            1,
            "C:/input/source.ma",
            [{"id": "rename", "number": 1, "name": "Rename", "icon": "ui_progress"}],
        )
        session = tracker_model.TrackerSession(
            "Test",
            "C:/project",
            1,
            [job],
            session_dir,
            project_log_path=project_log_path,
        )
        options = types.SimpleNamespace(
            no_log=False,
            task_time_logs=False,
            mayapy="mayapy",
            project_file="project.batch",
            run_from_task_id="",
            run_to_task_id="",
            final_task_id=[],
        )
        fake_process = FakeProcess()
        with mock.patch.object(tracker_scheduler.subprocess, "Popen", return_value=fake_process):
            scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
            scheduler.tick()
            worker_log_path = scheduler.running["job-0001"]["log_path"]
            with open(worker_log_path, "w", encoding="utf-8") as worker_log:
                worker_log.write("Worker task output\n")
            scheduler.tick()
            event_path = os.path.join(session_dir, "events", "job-0001.jsonl")
            writer = tracker_events.EventWriter(event_path, "job-0001")
            writer.emit("job_started")
            writer.emit("task_started", task_id="rename", total_items=1)
            writer.emit("task_progress", task_id="rename", completed_items=1, total_items=1)
            writer.emit("task_finished", task_id="rename", status="succeeded", completed_items=1, total_items=1)
            writer.emit("job_finished", status="completed")
            writer.close()
            scheduler.tick()
            fake_process.return_code = 0
            scheduler.tick()

        expected = tracker_constants.Status.COMPLETED
        self.assertEqual(expected, job.status)
        expected = 100
        self.assertEqual(expected, session.progress)
        self.assertTrue(session.finished)
        with open(project_log_path, "r", encoding="utf-8") as project_log:
            project_log_text = project_log.read()
        self.assertIn("Launcher output", project_log_text)
        self.assertIn("Worker task output", project_log_text)
        self.assertIn("Tasks 1/1 | Files 1/1 | Progress 100%", project_log_text)


if __name__ == "__main__":
    unittest.main()
