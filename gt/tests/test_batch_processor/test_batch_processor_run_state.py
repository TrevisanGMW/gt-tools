"""Cumulative batch results and project scripts, without Maya or server calls."""

import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest import mock

from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_run_state as run_state
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor import batch_processor_worker
from gt.tools.batch_processor.tasks import task_python_script, task_validation
from gt.tools.batch_processor.tracker import tracker_constants, tracker_model, tracker_scheduler
from gt.tools.batch_processor.tracker import tracker_worker


class TestBatchRunState(unittest.TestCase):
    """Checks project flags, monotonic failures and serialization boundaries."""

    def setUp(self):
        """Creates a simple validation followed by a project Python task."""
        self.project = batch_processor_model.BatchProcessorModel()
        self.validation = task_validation.TaskValidationFileIntegrity()
        self.final = task_python_script.TaskPythonScript(settings={
            "run_once_after_multi_instance": True, "script_text": "pass"})
        self.project.tasks = [self.validation, self.final]

    def test_unknown_before_execution_and_reserved_names(self):
        """Does not certify a loaded or newly constructed batch project."""
        environment = self.project.get_environment_variables(self.final, include_braces=False)
        self.assertEqual("0", environment["batch-status-known"])
        self.assertEqual("0", environment["batch-previous-tasks-succeeded"])
        self.assertFalse(self.project.is_custom_environment_name_available("{batch-tasks-failed}"))

    def test_successful_previous_tasks_and_validation_are_visible(self):
        """Excludes the running final task from the completed-task requirement."""
        run_state.initialize(self.project, "sample-run")
        run_state.record_validation(self.project, True)
        run_state.record_task(self.project, self.validation, "succeeded")
        environment = self.project.get_environment_variables(self.final, include_braces=False)
        self.assertEqual("1", environment["batch-previous-tasks-succeeded"])
        self.assertEqual("1", environment["batch-validation-passed"])
        self.assertEqual("1", environment["batch-task-run-once"])
        self.assertEqual("project", environment["batch-run-scope"])
        self.assertEqual("0", environment["batch-tasks-failed"])

    def test_failure_and_validation_issues_are_never_erased_by_success(self):
        """Keeps task and validation failures independent of later successes."""
        run_state.initialize(self.project, "sample-run")
        run_state.record_validation(self.project, False)
        run_state.record_validation(self.project, True)
        run_state.record_task(self.project, self.validation, "failed")
        run_state.record_task(self.project, self.validation, "succeeded")
        environment = run_state.get_environment_variables(self.project, self.final)
        self.assertEqual("1", environment["batch-tasks-failed"])
        self.assertEqual("1", environment["batch-validation-failed"])
        self.assertEqual("0", environment["batch-validation-passed"])
        self.assertEqual("0", environment["batch-previous-tasks-succeeded"])

    def test_skipped_tasks_are_incomplete(self):
        """Does not treat an enabled task's skip as completed work."""
        run_state.initialize(self.project, "sample-run")
        run_state.record_task(self.project, self.validation, "skipped")
        environment = run_state.get_environment_variables(self.project, self.final)
        self.assertEqual("1", environment["batch-tasks-incomplete"])
        self.assertEqual("0", environment["batch-tasks-failed"])

    def test_no_validation_shortened_run_and_nonfinal_task_are_not_certified(self):
        """Requires actual validation and all previous enabled processing tasks."""
        run_state.initialize(self.project, "sample-run")
        environment = run_state.get_environment_variables(self.project, self.final)
        self.assertEqual("0", environment["batch-validation-passed"])
        self.assertEqual("0", environment["batch-previous-tasks-succeeded"])
        environment = run_state.get_environment_variables(self.project, self.validation)
        self.assertEqual("0", environment["batch-is-final-task"])

    def test_new_run_resets_results_and_state_is_not_serialized(self):
        """Never carries run flags into project saves or the next run."""
        run_state.initialize(self.project, "old-run")
        run_state.record_validation(self.project, False)
        run_state.initialize(self.project, "new-run")
        self.assertEqual("0", run_state.get_environment_variables(self.project, self.final)["batch-validation-failed"])
        self.assertNotIn("_batch_run_state", json.dumps(self.project.to_dict()))

    def test_decode_rejects_invalid_boolean_and_missing_fields(self):
        """Malformed worker state cannot imply success."""
        state = run_state.new_state("sample-run")
        self.assertEqual(state, run_state.decode_state(json.dumps(state)))
        state["tasks_failed"] = "false"
        self.assertIsNone(run_state.decode_state(json.dumps(state)))
        self.assertIsNone(run_state.decode_state("{}"))
        self.assertIsNone(run_state.decode_state("invalid"))

    def test_merge_propagates_unknown_and_failed_validation(self):
        """Combines worker results without losing incomplete information."""
        good = run_state.new_state("sample-run")
        bad = dict(good, validation_failed=True)
        merged = run_state.merge_states([good, bad, None], "sample-run", "project")
        self.assertFalse(merged["known"])
        self.assertTrue(merged["validation_failed"])

    def test_validation_issues_are_recorded_with_failure_policy_disabled(self):
        """Records actual integrity issues even when execution returns normally."""
        run_state.initialize(self.project, "sample-run")
        item = task_base.WorkItem(source_path="sample.ma")
        with mock.patch.object(self.validation, "collect_file_issues", return_value=[{"severity": "Warning"}]), \
                mock.patch.object(self.validation, "write_validation_log_if_needed"):
            self.validation.execute(item, self.project, "unused")
        self.assertTrue(self.project._batch_run_state["validation_failed"])

    def test_scene_validation_warning_and_empty_checks_block_validation_pass(self):
        """Records warnings and configurations that performed no checks."""
        task = task_validation.TaskValidationMayaScene()
        item = task_base.WorkItem(source_path="sample.ma")
        for results in ([{"status_value": 2}], []):
            run_state.initialize(self.project, "sample-run")
            with mock.patch.object(task_validation.task_utils, "load_source_scene"), \
                    mock.patch.object(task, "run_validators", return_value=results), \
                    mock.patch.object(task, "write_validation_log_if_needed"):
                task.execute(item, self.project, "unused")
            self.assertTrue(self.project._batch_run_state["validation_failed"])


class TestProjectPythonTask(unittest.TestCase):
    """Checks that a run-once script never opens or saves source scenes."""

    def test_project_script_runs_once_and_preserves_incoming_items(self):
        """Executes exactly once despite multiple incoming files."""
        project = batch_processor_model.BatchProcessorModel()
        task = task_python_script.TaskPythonScript(settings={
            "run_once_after_multi_instance": True, "script_text": "def run(context):\n    return None"})
        items = [task_base.WorkItem(source_path="first.usd"), task_base.WorkItem(source_path="second.usd")]
        with mock.patch.object(task, "run_inline_python_script", return_value=None) as execute, \
                mock.patch.object(task, "load_source_scene") as load, \
                mock.patch.object(task_python_script.batch_processor_maya, "save_scene") as save:
            result = task.execute(None, project, "unused", {"work_items": items})
        self.assertEqual(items, result)
        execute.assert_called_once()
        self.assertIn("batch-status-known", execute.call_args.args[1]["env"])
        load.assert_not_called()
        save.assert_not_called()
        self.assertFalse(task.writes_to_target_path())

    def test_skipped_script_is_tracked_as_skipped(self):
        """Turns a script's returned skip result into a tracker skip."""
        project = batch_processor_model.BatchProcessorModel()
        task = task_python_script.TaskPythonScript(settings={
            "run_once_after_multi_instance": True, "script_text": "pass"})
        with mock.patch.object(task, "run_inline_python_script", return_value={"status": "skipped"}):
            with self.assertRaises(task_base.TaskSkip):
                task.execute(None, project, "unused")

    def test_single_runner_exposes_prior_validation_and_resets_next_run(self):
        """Tests the real runner's state updates with only scene operations mocked."""
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            project = batch_processor_model.BatchProcessorModel()
            project.environment_variables["project-dir"] = directory
            project.environment_variables["input-dir"] = "."
            Path(directory, "sample.ma").write_text("sample", encoding="utf-8")
            validation = task_validation.TaskValidationFileIntegrity(settings={"minimum_file_size": 0})
            final = task_python_script.TaskPythonScript(settings={
                "run_once_after_multi_instance": True, "script_text": "pass"})
            project.tasks.extend([validation, final])
            items = [task_base.WorkItem(source_path=str(Path(directory, "sample.ma")))]
            captured = []
            runner = batch_processor_worker.SingleInstanceBatchRunner()
            with mock.patch.object(runner, "_get_initial_source_files", return_value=[items[0].current_path]), \
                    mock.patch.object(project.tasks[0], "prepare", return_value=items), \
                    mock.patch.object(runner, "_get_task_source_items",
                                      side_effect=lambda **kwargs: kwargs["current_items"]), \
                    mock.patch.object(validation, "collect_file_issues", return_value=[]), \
                    mock.patch.object(validation, "write_validation_log_if_needed"), \
                    mock.patch.object(final, "run_inline_python_script",
                                      side_effect=lambda code, context: captured.append(context["env"])):
                runner.run(project)
            self.assertEqual(1, len(captured))
            self.assertEqual("1", captured[0]["batch-previous-tasks-succeeded"])
            self.assertEqual("1", captured[0]["batch-validation-passed"])


class TestTrackerRunState(unittest.TestCase):
    """Checks cross-worker result transfer at the finalization barrier."""

    def setUp(self):
        """Creates two successful jobs and a single deferred Python task."""
        self.regular = []
        for number in (1, 2):
            definition = {"id": "validation", "number": 1, "name": "Validation"}
            job = tracker_model.TrackerJob(str(number), number, "sample.ma", [definition])
            job.status = tracker_constants.Status.COMPLETED
            job.tasks[0].status = tracker_constants.Status.COMPLETED
            state = run_state.new_state("sample-run")
            state.update(validation_checked=True, completed_task_ids=["validation"])
            job.apply_event({"event": "run_state", "state": state})
            self.regular.append(job)
        definition = {"id": "final-script", "number": 1, "name": "Final Python Script"}
        self.final_job = tracker_model.TrackerJob("final", 3, "", [definition], is_finalization=True)
        self.scheduler = tracker_scheduler.TrackerScheduler.__new__(tracker_scheduler.TrackerScheduler)
        self.scheduler.session = types.SimpleNamespace(regular_jobs=self.regular, session_dir="sample-run")
        self.scheduler.run_seed = run_state.new_state("sample-run")
        self.scheduler.job_retry_counts = {}

    def test_project_barrier_combines_all_workers(self):
        """Marks only the final worker as having verified project-wide results."""
        state = self.scheduler._build_worker_run_state(self.final_job, self.final_job.tasks[0])
        self.assertTrue(state["known"])
        self.assertEqual("project", state["scope"])
        self.assertTrue(state["validation_checked"])
        self.assertEqual(["validation"], state["completed_task_ids"])
        worker = self.scheduler._build_worker_run_state(self.regular[0])
        self.assertEqual("worker", worker["scope"])

    def test_any_worker_validation_failure_is_sticky(self):
        """Includes failures from every job in a later successful finalization."""
        self.regular[1].runtime_state["validation_failed"] = True
        state = self.scheduler._build_worker_run_state(self.final_job, self.final_job.tasks[0])
        self.assertTrue(state["validation_failed"])

    def test_missing_worker_results_and_skipped_items_block(self):
        """Does not interpret successful exit alone as confirmed complete work."""
        self.regular[1].runtime_state = None
        state = self.scheduler._build_worker_run_state(self.final_job, self.final_job.tasks[0])
        self.assertFalse(state["known"])
        self.regular[0].tasks[0].skipped_items = 1
        state = self.scheduler._build_worker_run_state(self.final_job, self.final_job.tasks[0])
        self.assertTrue(state["tasks_incomplete"])

    def test_successful_retry_retains_failure(self):
        """A retry cannot erase an earlier failed project result."""
        self.scheduler.job_retry_counts["1"] = 1
        state = self.scheduler._build_worker_run_state(self.final_job, self.final_job.tasks[0])
        self.assertTrue(state["tasks_failed"])

    def test_job_restart_and_events_never_clear_failures(self):
        """Keeps failed attempts even after a fresh worker reports success."""
        job = self.regular[0]
        job.status = tracker_constants.Status.FAILED
        job.reset_for_restart()
        job.apply_event({"event": "run_state", "state": run_state.new_state("sample-run")})
        self.assertTrue(job.runtime_state["tasks_failed"])
        self.assertTrue(job.runtime_state["tasks_incomplete"])

    def test_final_worker_receives_project_results_and_runs_without_maya(self):
        """Loads a generic test script created entirely inside this repository."""
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            script = Path(directory, "example_task.py")
            script.write_text(
                "def run(context):\n"
                "    environment = context['env']\n"
                "    assert environment['batch-status-known'] == '1'\n"
                "    assert environment['batch-run-scope'] == 'project'\n"
                "    assert environment['batch-previous-tasks-succeeded'] == '1'\n"
                "    assert environment['batch-validation-passed'] == '1'\n",
                encoding="utf-8",
            )
            project = batch_processor_model.BatchProcessorModel()
            project.project_name = "Example Project"
            project.environment_variables["project-dir"] = directory
            validation = task_validation.TaskValidationFileIntegrity()
            final = task_python_script.TaskPythonScript(settings={
                "run_once_after_multi_instance": True, "script_mode": "External File",
                "external_scripts": [{"path": str(script), "enabled": True}],
            })
            project.tasks = [validation, final]
            seed = run_state.new_state("sample-run", "project")
            seed.update(validation_checked=True, completed_task_ids=[validation.id])
            event_file = str(Path(directory, "events.jsonl"))
            arguments = types.SimpleNamespace(
                project_file="unused.batch", source_file="", final_task_id=final.id,
                task_id=[], job_id="final", event_file=event_file, worker_id="3", total_jobs="2",
                log_file="", task_time_log_file="", hold_open_seconds=0,
                flag_running_tasks=False, flag_skipped_tasks=False,
            )
            with mock.patch.dict(os.environ, {run_state.WORKER_STATE_VARIABLE: json.dumps(seed)}), \
                    mock.patch.object(tracker_worker, "parse_args", return_value=arguments), \
                    mock.patch.object(batch_processor_model.BatchProcessorModel, "from_file", return_value=project), \
                    mock.patch.object(task_python_script.batch_processor_maya, "save_scene") as save:
                with self.assertRaises(SystemExit) as exit_result:
                    tracker_worker.main()
            self.assertEqual(0, exit_result.exception.code)
            save.assert_not_called()
            events = [json.loads(line) for line in Path(event_file).read_text(encoding="utf-8").splitlines()]
            states = [event["state"] for event in events if event["event"] == "run_state"]
            self.assertTrue(states[-1]["validation_checked"])
            self.assertIn(final.id, states[-1]["completed_task_ids"])
