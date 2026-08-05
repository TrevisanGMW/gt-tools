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

    def test_session_get_job_names_groups_results_in_original_order(self):
        """Tests global-copy result grouping and original job ordering."""
        failed_job = self.create_job()
        failed_job.name = "failed.ma"
        failed_job.status = tracker_constants.Status.FAILED
        failed_job.tasks[0].errors = 1
        warning_job = self.create_job()
        warning_job.name = "warning.ma"
        warning_job.status = tracker_constants.Status.COMPLETED_WARNINGS
        warning_job.tasks[0].warnings = 1
        completed_job = self.create_job()
        completed_job.name = "completed.ma"
        completed_job.status = tracker_constants.Status.COMPLETED
        skipped_job = self.create_job()
        skipped_job.name = "skipped.ma"
        skipped_job.status = tracker_constants.Status.COMPLETED_WARNINGS
        skipped_job.tasks[0].status = tracker_constants.Status.SKIPPED
        skipped_job.tasks[0].skipped_items = 1
        finalization_job = tracker_model.TrackerJob(
            "finalization",
            5,
            "",
            [],
            is_finalization=True,
        )
        finalization_job.status = tracker_constants.Status.FAILED
        session = tracker_model.TrackerSession(
            "Test",
            "C:/project",
            1,
            [failed_job, warning_job, completed_job, skipped_job, finalization_job],
            "C:/session",
        )

        self.assertEqual(["failed.ma"], session.get_job_names("failed"))
        self.assertEqual(["warning.ma"], session.get_job_names("warning"))
        self.assertEqual(["completed.ma"], session.get_job_names("completed"))
        self.assertEqual(["skipped.ma"], session.get_job_names("skipped"))
        expected = ["failed.ma", "warning.ma", "completed.ma", "skipped.ma"]
        self.assertEqual(expected, session.get_job_names("all"))

    def test_clean_completed_copy_excludes_skips_when_skip_warnings_are_disabled(self):
        """Tests that skipped work never appears in the clean-completion copy list."""
        skipped_job = self.create_job()
        skipped_job.status = tracker_constants.Status.COMPLETED
        skipped_job.tasks[0].status = tracker_constants.Status.SKIPPED
        skipped_job.tasks[0].skipped_items = 1
        session = tracker_model.TrackerSession(
            "Test",
            "C:/project",
            1,
            [skipped_job],
            "C:/session",
        )

        self.assertEqual([], session.get_job_names("completed"))
        self.assertEqual([skipped_job.name], session.get_job_names("skipped"))

    def test_job_reset_for_restart_clears_runtime_state(self):
        """Tests that restarting clears prior job and task runtime results."""
        job = self.create_job()
        job.status = tracker_constants.Status.FAILED
        job.started_at = "started"
        job.completed_at = "completed"
        job.worker = "1"
        job.log_path = "worker.log"
        job.completion_result = "failed"
        task = job.tasks[0]
        task.status = tracker_constants.Status.FAILED
        task.progress = 100
        task.errors = 1
        task.messages.append(("Error", "Failed"))

        job.reset_for_restart()

        expected = tracker_constants.Status.QUEUED
        self.assertEqual(expected, job.status)
        self.assertEqual("", job.started_at)
        self.assertEqual("", job.completed_at)
        self.assertEqual("", job.log_path)
        self.assertEqual(expected, task.status)
        self.assertEqual(0, task.progress)
        self.assertEqual(0, task.errors)
        self.assertEqual([], task.messages)

    def test_scheduler_restarts_terminal_regular_job(self):
        """Tests that a finished regular job can return to the scheduler queue."""
        session_dir = tempfile.mkdtemp(prefix="gt_tracker_restart_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        job = self.create_job()
        job.status = tracker_constants.Status.FAILED
        job.tasks[0].status = tracker_constants.Status.FAILED
        job.tasks[0].progress = 100
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [job], session_dir)
        session.finished = True
        session.aborting = True
        session.completed_at = "completed"
        options = types.SimpleNamespace(no_log=True, task_time_logs=False)
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        scheduler.regular_queue = []

        result = scheduler.restart_job(job)

        self.assertTrue(result)
        self.assertEqual([job], scheduler.regular_queue)
        self.assertFalse(session.finished)
        self.assertFalse(session.aborting)
        self.assertEqual("", session.completed_at)
        expected = tracker_constants.Status.QUEUED
        self.assertEqual(expected, job.status)

    def test_scheduler_rejects_active_and_finalization_job_restarts(self):
        """Tests that unsafe or unsupported restart targets remain protected."""
        session_dir = tempfile.mkdtemp(prefix="gt_tracker_restart_guard_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        active_job = self.create_job()
        active_job.status = tracker_constants.Status.RUNNING
        final_job = tracker_model.TrackerJob(
            "finalization",
            2,
            "",
            [],
            is_finalization=True,
        )
        final_job.status = tracker_constants.Status.COMPLETED
        session = tracker_model.TrackerSession(
            "Test",
            "C:/project",
            1,
            [active_job, final_job],
            session_dir,
        )
        options = types.SimpleNamespace(no_log=True, task_time_logs=False)
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)

        self.assertFalse(scheduler.can_restart_job(active_job))
        self.assertFalse(scheduler.can_restart_job(final_job))

    def test_restart_preserves_terminal_finalization_state(self):
        """Tests that a single-job restart does not rerun project finalization."""
        session_dir = tempfile.mkdtemp(prefix="gt_tracker_restart_final_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        job = self.create_job()
        job.status = tracker_constants.Status.FAILED
        final_job = tracker_model.TrackerJob(
            "finalization",
            2,
            "",
            [{"id": "archive", "number": 1, "name": "Archive"}],
            is_finalization=True,
        )
        final_job.status = tracker_constants.Status.SKIPPED
        final_job.tasks[0].status = tracker_constants.Status.SKIPPED
        final_job.tasks[0].progress = 100
        session = tracker_model.TrackerSession(
            "Test",
            "C:/project",
            1,
            [job, final_job],
            session_dir,
        )
        session.finished = True
        options = types.SimpleNamespace(no_log=True, task_time_logs=False)
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        scheduler.regular_queue = []

        scheduler.restart_job(job)
        scheduler.regular_queue = []
        result = scheduler._advance_finalization()

        self.assertFalse(result)
        expected = tracker_constants.Status.SKIPPED
        self.assertEqual(expected, final_job.status)

    def test_scheduler_cancels_queued_regular_job(self):
        """Tests that canceling queued work removes it without launching a process."""
        session_dir = tempfile.mkdtemp(prefix="gt_tracker_cancel_queue_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        job = self.create_job()
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [job], session_dir)
        options = types.SimpleNamespace(no_log=True, task_time_logs=False)
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)

        result = scheduler.cancel_job(job)

        self.assertTrue(result)
        self.assertEqual([], scheduler.regular_queue)
        expected = tracker_constants.Status.CANCELED
        self.assertEqual(expected, job.status)
        self.assertTrue(all(task.status == expected for task in job.tasks))

    def test_scheduler_cancels_running_job_without_reporting_failure(self):
        """Tests graceful and forced termination of an individual running worker."""
        class FakeProcess:
            """Controllable process double for individual cancellation."""

            def __init__(self):
                """Initializes a running process double."""
                self.return_code = None

            def poll(self):
                """Gets the configured process return code.

                Returns:
                    int or None: Current fake process state.
                """
                return self.return_code

        session_dir = tempfile.mkdtemp(prefix="gt_tracker_cancel_running_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        job = self.create_job()
        job.status = tracker_constants.Status.RUNNING
        job.tasks[0].status = tracker_constants.Status.RUNNING
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [job], session_dir)
        options = types.SimpleNamespace(no_log=True, task_time_logs=False)
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        scheduler.regular_queue = []
        process = FakeProcess()
        scheduler.running[job.id] = {
            "process": process,
            "job": job,
            "final_task": None,
            "log_path": "",
            "cancel_requested_at": None,
            "cancel_force_requested": False,
        }
        with mock.patch.object(tracker_scheduler.time, "monotonic", side_effect=[10.0, 14.0]):
            with mock.patch.object(tracker_scheduler.tracker_process_utils, "terminate_process_tree") as terminate:
                result = scheduler.cancel_job(job)
                forced = scheduler._advance_job_cancellations()

        self.assertTrue(result)
        self.assertTrue(forced)
        self.assertEqual(
            [mock.call(process, force=False), mock.call(process, force=True)],
            terminate.call_args_list,
        )
        process.return_code = 1
        job.completion_result = "completed"
        scheduler._collect_finished_processes()
        session.set_flag_skips_as_warnings(False)
        expected = tracker_constants.Status.CANCELED
        self.assertEqual(expected, job.status)
        self.assertEqual(0, job.errors)
        self.assertTrue(all(task.status == expected for task in job.tasks))

    def test_session_get_job_paths_groups_results_in_original_order(self):
        """Tests that global path-copy grouping mirrors job-name grouping."""
        failed_job = self.create_job()
        failed_job.name = "failed.ma"
        failed_job.source_file = "C:/input/failed.ma"
        failed_job.status = tracker_constants.Status.FAILED
        failed_job.tasks[0].errors = 1
        timed_out_job = self.create_job()
        timed_out_job.name = "timeout.ma"
        timed_out_job.source_file = "C:/input/timeout.ma"
        timed_out_job.status = tracker_constants.Status.TIMED_OUT
        completed_job = self.create_job()
        completed_job.name = "completed.ma"
        completed_job.source_file = "C:/input/completed.ma"
        completed_job.status = tracker_constants.Status.COMPLETED
        session = tracker_model.TrackerSession(
            "Test",
            "C:/project",
            1,
            [failed_job, timed_out_job, completed_job],
            "C:/session",
        )

        expected_failed = [os.path.normpath("C:/input/failed.ma"), os.path.normpath("C:/input/timeout.ma")]
        self.assertEqual(expected_failed, session.get_job_paths("failed"))
        self.assertEqual([os.path.normpath("C:/input/completed.ma")], session.get_job_paths("completed"))
        expected_all = [
            os.path.normpath("C:/input/failed.ma"),
            os.path.normpath("C:/input/timeout.ma"),
            os.path.normpath("C:/input/completed.ma"),
        ]
        self.assertEqual(expected_all, session.get_job_paths("all"))

    def test_scheduler_times_out_running_job_and_marks_timed_out(self):
        """Tests that a job exceeding the timeout is force-canceled and relabeled."""
        class FakeProcess:
            """Controllable process double for timeout handling."""

            def __init__(self):
                """Initializes a running process double."""
                self.return_code = None

            def poll(self):
                """Gets the configured process return code.

                Returns:
                    int or None: Current fake process state.
                """
                return self.return_code

        session_dir = tempfile.mkdtemp(prefix="gt_tracker_timeout_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        job = self.create_job()
        job.status = tracker_constants.Status.RUNNING
        job.tasks[0].status = tracker_constants.Status.RUNNING
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [job], session_dir)
        options = types.SimpleNamespace(no_log=True, task_time_logs=False, timeout_minutes=5)
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        scheduler.regular_queue = []
        process = FakeProcess()
        scheduler.running[job.id] = {
            "process": process,
            "job": job,
            "final_task": None,
            "log_path": "",
            "cancel_requested_at": None,
            "cancel_force_requested": False,
            "started_monotonic": 0.0,
            "timed_out": False,
        }

        with mock.patch.object(tracker_scheduler.time, "monotonic", return_value=600.0):
            with mock.patch.object(tracker_scheduler.tracker_process_utils, "terminate_process_tree") as terminate:
                timed_out = scheduler._advance_timeouts()

        self.assertTrue(timed_out)
        terminate.assert_called_once_with(process, force=True)
        self.assertIn(job.id, scheduler.timed_out_jobs)
        process.return_code = 1
        scheduler._collect_finished_processes()
        self.assertEqual(tracker_constants.Status.FAILED, job.status)

        changed = scheduler._finalize_timed_out_jobs()

        self.assertTrue(changed)
        self.assertEqual(tracker_constants.Status.TIMED_OUT, job.status)
        self.assertNotIn(job.id, scheduler.timed_out_jobs)

    def test_timed_out_job_with_retries_remaining_is_requeued_not_relabeled(self):
        """Tests that a timed-out job is retried before it is marked timed out."""
        session_dir = tempfile.mkdtemp(prefix="gt_tracker_timeout_retry_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        job = self.create_job()
        job.status = tracker_constants.Status.FAILED
        job.tasks[0].status = tracker_constants.Status.FAILED
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [job], session_dir)
        options = types.SimpleNamespace(
            no_log=True, task_time_logs=False, timeout_minutes=5, max_retries=2
        )
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        scheduler.regular_queue = []
        scheduler.timed_out_jobs.add(job.id)

        finalized = scheduler._finalize_timed_out_jobs()

        self.assertFalse(finalized)
        self.assertEqual(tracker_constants.Status.FAILED, job.status)

        retried = scheduler._advance_retries()

        self.assertTrue(retried)
        self.assertEqual([job], scheduler.regular_queue)
        self.assertEqual(tracker_constants.Status.QUEUED, job.status)
        self.assertNotIn(job.id, scheduler.timed_out_jobs)

    def test_request_restart_cancels_and_requeues_running_job(self):
        """Tests that restarting an active job cancels it then queues it again."""
        class FakeProcess:
            """Controllable process double for deferred restart."""

            def __init__(self):
                """Initializes a running process double."""
                self.return_code = None

            def poll(self):
                """Gets the configured process return code.

                Returns:
                    int or None: Current fake process state.
                """
                return self.return_code

        session_dir = tempfile.mkdtemp(prefix="gt_tracker_restart_active_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        job = self.create_job()
        job.status = tracker_constants.Status.RUNNING
        job.tasks[0].status = tracker_constants.Status.RUNNING
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [job], session_dir)
        options = types.SimpleNamespace(no_log=True, task_time_logs=False)
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        scheduler.regular_queue = []
        process = FakeProcess()
        scheduler.running[job.id] = {
            "process": process,
            "job": job,
            "final_task": None,
            "log_path": "",
            "cancel_requested_at": None,
            "cancel_force_requested": False,
            "started_monotonic": 0.0,
            "timed_out": False,
        }

        self.assertTrue(scheduler.can_request_restart_job(job))
        with mock.patch.object(tracker_scheduler.tracker_process_utils, "terminate_process_tree"):
            requested = scheduler.request_restart_job(job)

        self.assertTrue(requested)
        self.assertIn(job.id, scheduler.pending_restarts)
        process.return_code = 1
        scheduler._collect_finished_processes()
        self.assertEqual(tracker_constants.Status.CANCELED, job.status)

        advanced = scheduler._advance_pending_restarts()

        self.assertTrue(advanced)
        self.assertEqual([job], scheduler.regular_queue)
        self.assertEqual(tracker_constants.Status.QUEUED, job.status)
        self.assertNotIn(job.id, scheduler.pending_restarts)

    def test_canceled_regular_job_skips_finalization(self):
        """Tests that run-once finalization does not process an incomplete batch."""
        session_dir = tempfile.mkdtemp(prefix="gt_tracker_cancel_final_test_")
        self.addCleanup(lambda: os.path.isdir(session_dir) and shutil.rmtree(session_dir))
        job = self.create_job()
        job.status = tracker_constants.Status.CANCELED
        final_job = tracker_model.TrackerJob(
            "finalization",
            2,
            "",
            [{"id": "archive", "number": 1, "name": "Archive"}],
            is_finalization=True,
        )
        session = tracker_model.TrackerSession(
            "Test",
            "C:/project",
            1,
            [job, final_job],
            session_dir,
        )
        options = types.SimpleNamespace(no_log=True, task_time_logs=False)
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        scheduler.regular_queue = []

        result = scheduler._advance_finalization()

        self.assertTrue(result)
        expected = tracker_constants.Status.SKIPPED
        self.assertEqual(expected, final_job.status)
        self.assertEqual(expected, final_job.tasks[0].status)

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

    def create_completed_job(self, name="done.ma", size=None, status=None):
        """Creates a terminal job with a fixed ten-second run time.

        Args:
            name (str, optional): Job display name.
            size (int, optional): Cached source size in bytes.
            status (str, optional): Terminal status to assign.

        Returns:
            TrackerJob: Completed test job.
        """
        job = self.create_job()
        job.name = name
        job.status = status or tracker_constants.Status.COMPLETED
        job.started_at = "2026-01-01T00:00:00+00:00"
        job.completed_at = "2026-01-01T00:00:10+00:00"
        if size is not None:
            job._source_size = size
        return job

    def test_estimate_is_none_before_any_job_completes(self):
        """Tests that no estimate is offered until one job finishes."""
        session = tracker_model.TrackerSession(
            "Test", "C:/project", 1, [self.create_job(), self.create_job()], "C:/session"
        )

        self.assertIsNone(session.estimate_remaining_seconds())

    def test_estimate_is_zero_when_all_jobs_complete(self):
        """Tests that a fully completed batch reports no remaining time."""
        done = self.create_completed_job(size=0)
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [done], "C:/session")

        expected = 0.0
        self.assertEqual(expected, session.estimate_remaining_seconds())

    def test_estimate_uses_simple_average_when_sizes_unavailable(self):
        """Tests the per-job fallback used when file sizes are missing."""
        done = self.create_completed_job(size=0)
        pending_one = self.create_job()
        pending_two = self.create_job()
        pending_one._source_size = 0
        pending_two._source_size = 0
        session = tracker_model.TrackerSession(
            "Test", "C:/project", 1, [done, pending_one, pending_two], "C:/session"
        )

        expected = 20.0
        self.assertAlmostEqual(expected, session.estimate_remaining_seconds())

    def test_estimate_weights_remaining_time_by_source_file_size(self):
        """Tests that a larger remaining file scales the estimate."""
        done = self.create_completed_job(size=100)
        pending = self.create_job()
        pending._source_size = 300
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [done, pending], "C:/session")

        expected = 30.0
        self.assertAlmostEqual(expected, session.estimate_remaining_seconds())

    def test_estimate_divides_projected_work_by_worker_count(self):
        """Tests that concurrent workers shorten the projected wall-clock time."""
        done = self.create_completed_job(size=0)
        pending_jobs = [self.create_job() for _ in range(4)]
        for job in pending_jobs:
            job._source_size = 0
        session = tracker_model.TrackerSession(
            "Test", "C:/project", 2, [done] + pending_jobs, "C:/session"
        )

        expected = 20.0
        self.assertAlmostEqual(expected, session.estimate_remaining_seconds())

    def test_estimate_ignores_finalization_jobs(self):
        """Tests that the finalization phase does not distort the estimate."""
        done = self.create_completed_job(size=0)
        pending = self.create_job()
        pending._source_size = 0
        final_job = tracker_model.TrackerJob("finalization", 3, "", [], is_finalization=True)
        session = tracker_model.TrackerSession(
            "Test", "C:/project", 1, [done, pending, final_job], "C:/session"
        )

        expected = 10.0
        self.assertAlmostEqual(expected, session.estimate_remaining_seconds())

    def test_source_size_is_read_from_disk_only_once(self):
        """Tests that the source size is stat-ed once and cached afterward."""
        job = self.create_job()
        with mock.patch.object(tracker_model.os.path, "getsize", return_value=512) as getsize:
            first = job.get_source_size()
            second = job.get_source_size()

        self.assertEqual(512, first)
        self.assertEqual(512, second)
        getsize.assert_called_once()


if __name__ == "__main__":
    unittest.main()
