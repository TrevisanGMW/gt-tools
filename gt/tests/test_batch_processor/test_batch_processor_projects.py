"""Regression coverage for nested project contracts, eligibility and processes."""

import datetime
import json
import os
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock

from gt.tools.batch_processor import batch_processor_projects as projects
from gt.tools.batch_processor import batch_processor_project_service as service
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_worker
from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_model
from gt.tools.batch_processor.tracker import tracker_scheduler
from gt.tools.batch_processor.tracker import tracker_events


class TestBatchProjects(unittest.TestCase):
    """Tests orchestration without initializing Maya or Qt."""

    def setUp(self):
        """Creates a disposable project root and clean inherited runtime state."""
        temporary = tempfile.TemporaryDirectory(prefix="gt_child_projects_")
        self.addCleanup(temporary.cleanup)
        self.root = temporary.name
        patcher = mock.patch.dict(os.environ, {projects.ANCESTRY_VARIABLE: "[]"})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.parent = batch_processor_model.BatchProcessorModel()
        self.parent.tasks = []
        self.parent.environment_variables["project-dir"] = self.root
        self.task = self.parent.add_task(tasks.TaskRunBatchProject())

    def make_scheduler(self, count=3):
        """Builds a real scheduler with child launch jobs and mocked processes.

        Args:
            count (int, optional): Number of child jobs.

        Returns:
            TrackerScheduler: Scheduler ready for eligibility evaluation.
        """
        jobs = [tracker_model.TrackerJob(f"job-{index}", index, f"child_{index}.batch", [
            {"id": self.task.id, "number": 1, "name": self.task.display_name}])
                for index in range(1, count + 1)]
        session = tracker_model.TrackerSession("Parent", self.root, 2, jobs, os.path.join(self.root, "session"))
        options = types.SimpleNamespace(max_retries=0, timeout_minutes=0, no_log=True, task_time_logs=False)
        return tracker_scheduler.TrackerScheduler(session, options, project=self.parent)

    def make_child(self, name="child", multi=True):
        """Saves a real file-copy project for preparation and process tests.

        Args:
            name (str, optional): Unique child name.
            multi (bool, optional): Saved execution mode.

        Returns:
            tuple: Source project path and expected output file.
        """
        root = os.path.join(self.root, name)
        os.makedirs(root)
        source = os.path.join(root, "input.txt")
        with open(source, "w", encoding="utf-8") as stream:
            stream.write("nested project input")
        child = batch_processor_model.BatchProcessorModel()
        child.tasks = []
        child.project_name = name
        child.run_settings.update(multi_instance=multi, worker_count=2, purge_logs_on_run=False)
        child.add_task(tasks.TaskInput(settings={"explicit_files": [source], "extensions": [".txt"]}))
        child.add_task(tasks.TaskRename(settings={
            "source_mode": "incoming", "target_path": "{project-dir}/output", "overwrite": False}))
        path = os.path.join(root, f"{name}.batch")
        child.save_to_file(path)
        return path, os.path.join(root, "output", "input.txt")

    def mark_finished(self, job, status):
        """Applies a consistent terminal state to a dependency.

        Args:
            job (TrackerJob): Job to finish.
            status (str): Terminal status.
        """
        job.status = status
        job.completed_at = tracker_events.utc_now_iso()
        for task in job.tasks:
            task.status = status
            task.progress = 100

    def test_registry_and_serialization(self):
        """Preserves launch settings and stable type keys across serialization."""
        self.task.settings["ignore_self"] = False
        restored = tasks.create_task_from_dict(self.task.to_dict())
        self.assertEqual(self.task.to_dict(), restored.to_dict())

    def test_timezone_is_required(self):
        """Rejects ambiguous local schedule timestamps."""
        with self.assertRaises(ValueError):
            projects.parse_start_time("2026-10-21T22:00:00")
        expected = datetime.datetime(2026, 10, 22, 5, tzinfo=datetime.timezone.utc)
        self.assertEqual(expected, projects.parse_start_time("2026-10-21T22:00:00-07:00"))

    def test_short_local_schedule_uses_parent_start_day_and_year(self):
        """Resolves easy-to-write times against a fixed parent start date."""
        reference = datetime.datetime(2026, 10, 20, 12).astimezone()
        expected = datetime.datetime(2026, 10, 20, 22, 15).astimezone(datetime.timezone.utc)
        self.assertEqual(expected, projects.parse_start_time("22:15", reference))
        tomorrow = datetime.datetime(2026, 10, 21, 2, 30).astimezone(datetime.timezone.utc)
        self.assertEqual(tomorrow, projects.parse_start_time("10-21 02:30", reference))

    def test_retired_controls_have_no_runtime_effect(self):
        """Removes old serialized controls without disabling child tasks."""
        task = tasks.TaskRunBatchProject(settings={"disabled_task_types": ["rename"],
                                                 "project_retries": 20, "project_timeout_minutes": 1})
        self.assertNotIn("disabled_task_types", task.settings)
        self.assertNotIn("project_retries", task.settings)
        self.assertNotIn("project_timeout_minutes", task.settings)

    def test_self_input_is_ignored_by_default_and_recursion_stays_guarded(self):
        """Excludes the current project and preserves recursion protection when disabled."""
        path, output = self.make_child()
        self.parent.project_file_path = path
        self.assertTrue(self.task.settings["ignore_self"])
        incoming = [path, os.path.join(self.root, "other.batch")]
        self.assertEqual(incoming[1:], projects.filter_project_inputs(incoming, self.task, self.parent))
        item = tasks.WorkItem(path)
        self.assertEqual(item, self.task.execute(item, self.parent, ""))
        self.task.settings["ignore_self"] = False
        self.assertEqual(incoming, projects.filter_project_inputs(incoming, self.task, self.parent))
        self.assertTrue(self.task.validate_work_items([item], self.parent, "").errors)

    def test_self_input_is_reported_as_ignored_in_preview(self):
        """Shows the self-exclusion without a false recursion error in previews."""
        path, output = self.make_child()
        self.parent.project_file_path = path
        self.parent.tasks.insert(0, tasks.TaskInput(settings={"explicit_files": [path], "extensions": [".batch"]}))
        rows = service.preview_projects(self.task, self.parent)
        self.assertTrue(rows[0]["ignored"])
        self.assertEqual([], rows[0]["errors"])

    def test_segment_materialization_excludes_self_before_creating_jobs(self):
        """Does not introduce failed dependencies when a later input segment finds itself."""
        scheduler = self.make_scheduler(0)
        own_path = os.path.join(self.root, "parent.batch")
        self.parent.project_file_path = own_path
        scheduler.segments = [{"input_tasks": [], "definitions": [
            {"id": self.task.id, "number": 1, "name": self.task.display_name}]}]
        with mock.patch.object(self.parent, "discover_segment_input_files", return_value=[own_path, "child.batch"]):
            scheduler._materialize_segment(0)
        self.assertEqual(["child.batch"], [job.source_file for job in scheduler.session.regular_jobs])

    def test_invalid_schedule_and_override_report_errors(self):
        """Reports malformed settings before launching a process."""
        self.task.settings.update(not_before="tonight", worker_count=-1)
        self.assertEqual(2, len(self.task.validate(self.parent).errors))

    def test_parent_requires_standalone_mode(self):
        """Keeps scheduling waits outside the interactive Maya process."""
        self.parent.run_settings["multi_instance"] = False
        self.assertTrue(self.task.validate(self.parent).errors)

    def test_recursion_and_depth(self):
        """Rejects self-launches and limits nesting before subprocess startup."""
        path = os.path.join(self.root, "project.batch")
        with self.assertRaisesRegex(ValueError, "Recursive"):
            projects.get_ancestry(path, path)
        with mock.patch.dict(os.environ, {projects.ANCESTRY_VARIABLE: json.dumps(["a.batch", "b.batch"])}):
            with self.assertRaisesRegex(ValueError, "depth"):
                projects.get_ancestry("c.batch", maximum_depth=1)

    def test_runtime_overrides_preserve_source_bytes(self):
        """Overrides a copied model and preserves saved project settings and bytes."""
        path, output = self.make_child()
        with open(path, "rb") as stream:
            original = stream.read()
        self.task.settings.update(override_worker_count=True, worker_count=1,
                                  override_timeout_minutes=True, timeout_minutes=0)
        child, ancestry = projects.prepare_project(path, self.task.settings)
        self.assertEqual(1, child.run_settings["worker_count"])
        self.assertEqual(True, child.tasks[1].enabled)
        with open(path, "rb") as stream:
            self.assertEqual(original, stream.read())

    def test_snapshot_keeps_original_project_file_tokens(self):
        """Resolves project-file-dir and project-path against the saved child source."""
        path, output = self.make_child()
        child, ancestry = projects.prepare_project(path, self.task.settings)
        snapshot = child.to_dict()
        snapshot["runtime_options"] = {"source_project_file": path}
        snapshot_path = os.path.join(self.root, "snapshot.batch")
        projects.write_json(snapshot_path, snapshot)
        restored = batch_processor_model.BatchProcessorModel.from_file(snapshot_path)
        self.assertEqual(os.path.dirname(path), restored.get_project_file_dir())
        self.assertEqual(path, restored.get_environment_variables(include_braces=False)["project-path"])

    def test_preview_reports_overrides_without_execution(self):
        """Previews effective worker limits without creating outputs."""
        path, output = self.make_child()
        self.parent.tasks.insert(0, tasks.TaskInput(settings={"explicit_files": [path], "extensions": [".batch"]}))
        self.task.settings.update(override_worker_count=True, worker_count=3)
        rows = service.preview_projects(self.task, self.parent)
        self.assertEqual(3, rows[0]["workers"])
        self.assertFalse(os.path.exists(output))

    def test_incomplete_task_result_cannot_be_success(self):
        """Rejects completion when a worker left enabled processing tasks unresolved."""
        scheduler = self.make_scheduler(1)
        scheduler.session.jobs[0].status = tracker_constants.Status.COMPLETED
        self.assertEqual("failed", projects.build_result(scheduler.session)["outcome"])

    def test_project_lock_is_exclusive_and_released(self):
        """Prevents concurrent execution and permits a later run."""
        with service.project_lock(self.root, "child.batch"):
            with self.assertRaisesRegex(RuntimeError, "already processing"):
                with service.project_lock(self.root, "child.batch"):
                    self.fail("Lock unexpectedly acquired twice.")
        with service.project_lock(self.root, "child.batch"):
            pass

    def test_independent_queue_fills_only_available_slots(self):
        """Limits simultaneous child launches to the parent's worker count."""
        scheduler = self.make_scheduler()

        def launch(job):
            """Records an occupied worker slot.

            Args:
                job (TrackerJob): Launched job.
            """
            scheduler.running[job.id] = {"job": job}

        with mock.patch.object(scheduler, "_launch_job", side_effect=launch) as mocked:
            scheduler._launch_available_jobs()
        self.assertEqual(2, mocked.call_count)
        self.assertEqual(1, len(scheduler.regular_queue))

    def test_scheduled_wait_does_not_take_a_slot(self):
        """Keeps waiting children queued without launching a worker."""
        scheduler = self.make_scheduler()
        self.task.settings["not_before"] = "2099-01-01T00:00:00Z"
        with mock.patch.object(scheduler, "_launch_job") as launch:
            scheduler._launch_available_jobs()
        self.assertEqual(0, launch.call_count)
        self.assertEqual(3, len(scheduler.regular_queue))

    def test_deadline_blocks_and_finishes_queue(self):
        """Makes expired launch conditions terminal instead of waiting forever."""
        scheduler = self.make_scheduler()
        self.task.settings["launch_deadline"] = "2000-01-01T00:00:00Z"
        scheduler._launch_available_jobs()
        self.assertEqual([], scheduler.regular_queue)
        self.assertTrue(scheduler._is_finished())
        self.assertEqual(tracker_constants.Status.BLOCKED, scheduler.session.jobs[0].status)

    def test_ordered_dependency_uses_input_order(self):
        """Waits for the actual predecessor regardless of free worker capacity."""
        scheduler = self.make_scheduler()
        self.task.settings["queue_mode"] = "Ordered Chain"
        first, second, third = scheduler.session.jobs
        self.assertTrue(scheduler.project_queue.eligible(first))
        self.assertFalse(scheduler.project_queue.eligible(second))
        self.mark_finished(first, tracker_constants.Status.COMPLETED)
        self.assertTrue(scheduler.project_queue.eligible(second))
        self.assertFalse(scheduler.project_queue.eligible(third))

    def test_exhausted_failure_blocks_success_chain(self):
        """Propagates permanent failure through an ordered success dependency."""
        scheduler = self.make_scheduler()
        self.task.settings["queue_mode"] = "Ordered Chain"
        self.mark_finished(scheduler.session.jobs[0], tracker_constants.Status.FAILED)
        self.assertFalse(scheduler.project_queue.eligible(scheduler.session.jobs[1]))
        self.assertEqual(tracker_constants.Status.BLOCKED, scheduler.session.jobs[1].status)

    def test_retry_does_not_deadlock_on_queued_dependent(self):
        """Requeues a failed predecessor while its successor is still waiting."""
        scheduler = self.make_scheduler()
        self.task.settings["queue_mode"] = "Ordered Chain"
        scheduler.max_retries = 1
        first, second, third = scheduler.session.jobs
        scheduler.regular_queue.remove(first)
        self.mark_finished(first, tracker_constants.Status.FAILED)
        self.assertFalse(scheduler.project_queue.eligible(second))
        self.assertTrue(scheduler.project_queue.advance_retries())
        self.assertIn(first, scheduler.regular_queue)
        self.assertEqual(1, scheduler.job_retry_counts[first.id])

    def test_parent_retry_setting_governs_child_launches(self):
        """Uses the current project's existing retry budget for child launch jobs."""
        scheduler = self.make_scheduler()
        job = scheduler.session.jobs[0]
        self.mark_finished(job, tracker_constants.Status.FAILED)
        scheduler.regular_queue = []
        self.assertFalse(scheduler._retries_remaining(job))
        self.assertFalse(scheduler._advance_retries())
        scheduler.max_retries = 2
        self.assertTrue(scheduler._retries_remaining(job))
        self.assertTrue(scheduler.project_queue.advance_retries())

    def test_failure_trigger_and_completion_trigger(self):
        """Allows recovery and unconditional sequencing after a failed predecessor."""
        scheduler = self.make_scheduler()
        self.task.settings.update(queue_mode="Ordered Chain", dependency_outcome="Failure")
        first, second, third = scheduler.session.jobs
        self.mark_finished(first, tracker_constants.Status.FAILED)
        self.assertTrue(scheduler.project_queue.eligible(second))
        self.task.settings["dependency_outcome"] = "Completion"
        self.assertTrue(scheduler.project_queue.eligible(second))

    def test_group_requires_all_previous_jobs_successful(self):
        """Evaluates the previous input segment as a complete dependency group."""
        scheduler = self.make_scheduler()
        self.task.settings["queue_mode"] = "Groups"
        first, second, third = scheduler.session.jobs
        third.segment_index = 1
        self.mark_finished(first, tracker_constants.Status.COMPLETED)
        self.assertFalse(scheduler.project_queue.eligible(third))
        self.mark_finished(second, tracker_constants.Status.COMPLETED)
        self.assertTrue(scheduler.project_queue.eligible(third))

    def test_stop_launching_blocks_remaining_projects(self):
        """Stops new launches after a permanent failure without canceling active jobs."""
        scheduler = self.make_scheduler()
        self.task.settings["failure_policy"] = "Stop Launching"
        self.mark_finished(scheduler.session.jobs[0], tracker_constants.Status.FAILED)
        self.assertFalse(scheduler.project_queue.eligible(scheduler.session.jobs[1]))
        self.assertEqual(tracker_constants.Status.BLOCKED, scheduler.session.jobs[1].status)

    def test_recovered_retry_is_warning_and_exhausted_timeout_is_failure(self):
        """Separates recovered failure history from unresolved terminal failures."""
        scheduler = self.make_scheduler(1)
        job = scheduler.session.jobs[0]
        self.mark_finished(job, tracker_constants.Status.COMPLETED)
        scheduler.session.finish()
        self.assertEqual("warning", projects.build_result(scheduler.session, {job.id: 1})["outcome"])
        self.mark_finished(job, tracker_constants.Status.TIMED_OUT)
        result = projects.build_result(scheduler.session)
        self.assertEqual("failed", result["outcome"])
        self.assertEqual(1, result["counts"]["timed_out"])

    def test_empty_outcome_is_explicit(self):
        """Applies the configured policy to empty project sessions."""
        scheduler = self.make_scheduler(0)
        self.assertEqual("warning", projects.build_result(scheduler.session)["outcome"])
        self.assertEqual("failed", projects.build_result(scheduler.session, empty_policy="Failure")["outcome"])

    def test_terminal_result_does_not_wait_for_process_exit(self):
        """Accepts a valid result while the child tracker remains open."""
        request = {"run_id": "test", "run_dir": self.root, "settings": self.task.settings}
        projects.write_json(os.path.join(self.root, "result.json"), {
            "schema_version": 1, "run_id": "test", "finished": True, "outcome": "succeeded"})
        process = mock.Mock()
        result = service.wait_for_result(process, request, {})
        self.assertEqual("succeeded", result["outcome"])
        process.poll.assert_not_called()

    def test_missing_final_result_is_failure(self):
        """Rejects a clean exit that never published its completion contract."""
        process = mock.Mock(returncode=0)
        process.poll.return_value = 0
        with self.assertRaisesRegex(RuntimeError, "without a final result"):
            service.wait_for_result(process, {"run_id": "test", "run_dir": self.root,
                                             "settings": self.task.settings}, {})

    def test_heartbeat_timeout_is_failure(self):
        """Detects a stalled scheduler independently of task progress."""
        projects.write_json(os.path.join(self.root, "status.json"), {"run_id": "test", "heartbeat": 1})
        with self.assertRaisesRegex(RuntimeError, "heartbeat"):
            service.wait_for_result(mock.Mock(), {"run_id": "test", "run_dir": self.root,
                                                 "settings": self.task.settings}, {})

    def test_reporter_publishes_final_result_and_honors_cancel(self):
        """Publishes a versioned result only after the scheduler finishes."""
        scheduler = self.make_scheduler(1)
        scheduler.options.result_file = os.path.join(self.root, "result.json")
        scheduler.options.status_file = os.path.join(self.root, "status.json")
        scheduler.options.control_file = os.path.join(self.root, "control.json")
        scheduler.options.run_id = "test"
        projects.write_json(scheduler.options.control_file, {"action": "cancel", "run_id": "test"})
        scheduler.tick()
        self.assertEqual("canceled", projects.read_json(scheduler.options.result_file)["outcome"])

    @unittest.skipUnless("mayapy" in os.path.basename(sys.executable).lower(), "Requires mayapy")
    def test_real_nested_multi_and_single_projects(self):
        """Runs real child supervisors, schedulers and workers for both saved modes."""
        for multi in (True, False):
            with self.subTest(multi=multi):
                path, output = self.make_child(name=f"child_{multi}", multi=multi)
                self.task.settings.update(show_tracker=False, logs_path=os.path.join(self.root, "child_logs"))
                result = self.task.execute(tasks.WorkItem(path), self.parent, "", context={"run_id": "parent"})
                self.assertTrue(os.path.isfile(output))
                self.assertEqual("succeeded", result.metadata["child_project_result"]["outcome"])
                self.assertFalse(result.metadata["child_project_result"]["empty"])

    @unittest.skipUnless("mayapy" in os.path.basename(sys.executable).lower() and os.name == "nt",
                         "Requires Windows mayapy and Qt")
    def test_real_tracker_can_remain_open_after_parent_task_finishes(self):
        """Completes the launch task while its actual Qt tracker process stays alive."""
        import ctypes

        path, output = self.make_child("retained")
        self.task.settings.update(show_tracker=True, window_policy="Keep Open",
                                  logs_path=os.path.join(self.root, "retained_logs"))
        tracker_pid = None
        try:
            with mock.patch.dict(os.environ, {"QT_QPA_PLATFORM": "offscreen"}):
                item = self.task.execute(tasks.WorkItem(path), self.parent, "", context={"run_id": "parent"})
            result = item.metadata["child_project_result"]
            status = projects.read_json(os.path.join(os.path.dirname(result["session_dir"]), "status.json"))
            tracker_pid = status["tracker_pid"]
            handle = ctypes.windll.kernel32.OpenProcess(0x00100000, False, tracker_pid)
            self.assertTrue(handle)
            try:
                self.assertEqual(258, ctypes.windll.kernel32.WaitForSingleObject(handle, 0))
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)
            self.assertTrue(os.path.isfile(output))
            self.assertEqual("succeeded", result["outcome"])
        finally:
            if tracker_pid:
                subprocess.run(["taskkill", "/PID", str(tracker_pid), "/F"], capture_output=True, check=False,
                               creationflags=subprocess.CREATE_NO_WINDOW)

    @unittest.skipUnless("mayapy" in os.path.basename(sys.executable).lower(), "Requires mayapy")
    def test_parent_tracker_receives_exhausted_child_failure(self):
        """Tracks successful and failing children through the complete parent pipeline."""
        good_path, good_output = self.make_child("good")
        bad_path, bad_output = self.make_child("bad")
        bad = batch_processor_model.BatchProcessorModel.from_file(bad_path)
        bad.run_settings["max_retries"] = 1
        obstruction = os.path.join(os.path.dirname(bad_path), "not_a_directory")
        with open(obstruction, "w", encoding="utf-8") as stream:
            stream.write("An existing file prevents output directory creation.")
        bad.tasks[1].settings["target_path"] = obstruction
        bad.save_to_file(bad_path)
        self.parent.tasks.insert(0, tasks.TaskInput(settings={
            "explicit_files": [good_path, bad_path], "extensions": [".batch"]}))
        self.task.settings.update(show_tracker=False, logs_path=os.path.join(self.root, "children"))
        self.parent.run_settings.update(worker_count=2, max_retries=0)
        parent_path = os.path.join(self.root, "parent.batch")
        self.parent.tasks[0].settings["explicit_files"].append(parent_path)
        self.parent.save_to_file(parent_path)
        runner = batch_processor_worker.MultiInstanceBatchRunner()
        result_file = os.path.join(self.root, "parent_result.json")
        runner.run(self.parent, runtime_options={
            "headless": True, "result_file": result_file, "run_id": "parent",
            "session_dir": os.path.join(self.root, "parent_session")})
        try:
            runner.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            from gt.tools.batch_processor.tracker.tracker_process_utils import terminate_process_tree

            terminate_process_tree(runner.process, force=True)
            self.fail("Parent orchestration did not finish within 30 seconds.")
        result = projects.read_json(result_file)
        self.assertEqual("failed", result["outcome"])
        self.assertEqual(1, result["counts"]["failed"])
        self.assertEqual(0, result["counts"]["retried"])
        self.assertTrue(os.path.isfile(good_output))
        from pathlib import Path

        children = [projects.read_json(str(path)) for path in Path(self.root, "children").rglob("result.json")]
        failed = next(child for child in children if child["outcome"] == "failed")
        self.assertEqual(1, failed["counts"]["retried"])

    @unittest.skipUnless("mayapy" in os.path.basename(sys.executable).lower(), "Requires mayapy")
    def test_cancellation_reaches_child_scheduler(self):
        """Cancels a running native single-instance script through the durable control file."""
        path, output = self.make_child("cancel", multi=False)
        child = batch_processor_model.BatchProcessorModel.from_file(path)
        child.tasks.insert(1, tasks.TaskPythonScript(settings={
            "run_once_before_multi_instance": True,
            "script_text": "import time\ntime.sleep(30)"}))
        child.save_to_file(path)
        run_dir = os.path.join(self.root, "cancel_run")
        os.makedirs(run_dir)
        request = {"project_file": os.path.join(run_dir, "effective.batch"),
                   "source_project_file": path, "run_id": "cancel-test", "parent_run_id": "parent",
                   "run_dir": run_dir, "settings": dict(self.task.settings, show_tracker=False)}
        snapshot = child.to_dict()
        snapshot["runtime_options"] = {"source_project_file": path}
        projects.write_json(request["project_file"], snapshot)
        request_file = os.path.join(run_dir, "request.json")
        projects.write_json(request_file, request)
        from gt.tools.batch_processor.tracker import project_main
        from gt.tools.batch_processor.tracker.tracker_process_utils import terminate_process_tree

        process = subprocess.Popen([sys.executable, project_main.__file__, "--request-file", request_file],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
        try:
            deadline = time.monotonic() + 15
            while not projects.read_json(os.path.join(run_dir, "status.json")):
                if process.poll() is not None or time.monotonic() > deadline:
                    self.fail("Child scheduler did not start.")
                time.sleep(0.1)
            projects.write_json(os.path.join(run_dir, "control.json"), {"action": "cancel", "run_id": "cancel-test"})
            process.wait(timeout=15)
            result = projects.read_json(os.path.join(run_dir, "result.json"))
            self.assertEqual("canceled", result["outcome"])
            self.assertFalse(os.path.isfile(output))
        finally:
            terminate_process_tree(process, force=True)


if __name__ == "__main__":
    unittest.main()
