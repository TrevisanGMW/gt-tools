"""Validate Python task: reporter, return-value handling, and execution without Maya."""

import json
import os
import tempfile
import unittest

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_run_state as run_state
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor import batch_processor_tasks
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor.tasks import task_validation_python as validation_python


class TestValidationReporter(unittest.TestCase):
    """Checks reporter counting, statuses, and serialization."""

    def test_errors_and_warnings_drive_status(self):
        """Reports failed when errors exist and warning when only warnings exist."""
        reporter = validation_python.ValidationReporter()
        self.assertEqual(validation_python.STATUS_PASSED, reporter.get_status())
        reporter.warning("Check this.")
        self.assertEqual(validation_python.STATUS_WARNING, reporter.get_status())
        reporter.error("Broken.", node="|root")
        self.assertEqual(validation_python.STATUS_FAILED, reporter.get_status())
        self.assertEqual(1, reporter.get_error_count())
        self.assertEqual(1, reporter.get_warning_count())

    def test_warnings_count_as_issues_only_when_enabled(self):
        """Lets the task decide whether warnings are issues."""
        reporter = validation_python.ValidationReporter()
        reporter.warning("Soft problem.")
        reporter.info("Note.")
        self.assertTrue(reporter.has_issues(warnings_are_issues=True))
        self.assertFalse(reporter.has_issues(warnings_are_issues=False))

    def test_check_records_counts_and_reports_failures(self):
        """Only reports the message when the condition is false."""
        reporter = validation_python.ValidationReporter()
        self.assertTrue(reporter.check(True, "Never reported."))
        self.assertFalse(reporter.check([], "Missing node.", severity="Warning", node="root"))
        self.assertEqual(2, reporter.checks_run)
        self.assertEqual(1, reporter.checks_passed)
        self.assertEqual([{"severity": "Warning", "message": "Missing node.", "node": "root"}], reporter.entries)

    def test_details_are_json_safe(self):
        """Converts tuples, sets, and objects into JSON-compatible values."""
        reporter = validation_python.ValidationReporter()
        reporter.error("Bad values.", values=(1, 2), owner=object())
        report = reporter.to_dict()
        json.dumps(report)
        self.assertEqual([1, 2], report["issues"][0]["values"])


class TestApplyScriptResult(unittest.TestCase):
    """Checks every supported run(context) return value."""

    def apply(self, result):
        """Applies a result to a new reporter.

        Args:
            result (object): Script return value.

        Returns:
            ValidationReporter: Updated reporter.
        """
        reporter = validation_python.ValidationReporter()
        validation_python.apply_script_result(result, reporter)
        return reporter

    def test_none_and_true_pass(self):
        """Adds nothing for passing return values."""
        self.assertEqual([], self.apply(None).entries)
        self.assertEqual([], self.apply(True).entries)

    def test_false_and_string_fail(self):
        """Turns False and strings into errors."""
        self.assertEqual(1, self.apply(False).get_error_count())
        self.assertEqual("Bad file.", self.apply("Bad file.").entries[0]["message"])

    def test_list_items_become_issues(self):
        """Accepts strings and issue dictionaries."""
        reporter = self.apply(["Missing root.", {"severity": "Warning", "message": "Odd name.", "node": "a"}])
        self.assertEqual(1, reporter.get_error_count())
        self.assertEqual(1, reporter.get_warning_count())
        self.assertEqual("a", reporter.entries[1]["node"])

    def test_status_dictionaries(self):
        """Maps dictionary status values onto the reporter."""
        self.assertEqual(validation_python.STATUS_FAILED, self.apply({"status": "failed"}).get_status())
        self.assertEqual(validation_python.STATUS_WARNING, self.apply({"status": "warning"}).get_status())
        skipped = self.apply({"status": "skipped", "reason": "Not a rig."})
        self.assertEqual("Not a rig.", skipped.skip_reason)
        self.assertEqual(validation_python.STATUS_SKIPPED, skipped.get_status())
        passed = self.apply({"status": "passed", "message": "All good."})
        self.assertEqual(validation_python.STATUS_PASSED, passed.get_status())

    def test_failed_status_does_not_duplicate_reported_errors(self):
        """Uses the issue list instead of adding a generic failure."""
        reporter = self.apply({"status": "failed", "issues": ["Specific problem."]})
        self.assertEqual(["Specific problem."], [entry["message"] for entry in reporter.entries])


class TestExecuteValidationScript(unittest.TestCase):
    """Checks inline execution, run(context), and script errors."""

    def test_script_uses_validation_global_and_run(self):
        """Combines reporter calls with the run(context) return value."""
        script = (
            "validation.warning('From the global.')\n"
            "def run(context):\n"
            "    return [context['file_name']]\n"
        )
        reporter = validation_python.execute_validation_script(
            script, {"file_name": "scene.ma"}, validation_python.ValidationReporter()
        )
        self.assertEqual(["From the global.", "scene.ma"], [entry["message"] for entry in reporter.entries])

    def test_exception_is_recorded_as_script_error(self):
        """Keeps the traceback in the report instead of raising."""
        reporter = validation_python.execute_validation_script(
            "raise ValueError('boom')", {}, validation_python.ValidationReporter()
        )
        self.assertTrue(reporter.script_error)
        self.assertIn("ValueError: boom", reporter.entries[0]["message"])
        self.assertIn("traceback", reporter.entries[0])

    def test_sample_scripts_compile(self):
        """Keeps every shipped example script valid Python."""
        samples = task_utils.get_script_samples(validation_python.SAMPLE_SCRIPTS_DIRECTORY)
        self.assertGreaterEqual(len(samples), 10)
        for sample in samples:
            compile(task_utils.load_script_file(sample["path"]), sample["path"], "exec")


class TestTaskValidationPythonScript(unittest.TestCase):
    """Checks registration, settings validation, and execution without loading scenes."""

    def setUp(self):
        """Creates a temporary project with one input file."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.temp_dir.name, "hero_rig.ma")
        with open(self.input_path, "w", encoding="utf-8") as file_stream:
            file_stream.write("//Maya ASCII")
        self.log_dir = os.path.join(self.temp_dir.name, "logs")
        self.project = batch_processor_model.BatchProcessorModel()
        run_state.initialize(self.project, "sample-run")

    def tearDown(self):
        """Removes the temporary project."""
        self.temp_dir.cleanup()

    def create_task(self, script_text, **settings):
        """Creates a scene-less Validate Python task.

        Args:
            script_text (str): Inline validation script.
            **settings: Additional setting overrides.

        Returns:
            TaskValidationPythonScript: Configured task.
        """
        task = batch_processor_tasks.create_task(constants.TaskType.PYTHON_SCRIPT_VALIDATE)
        task.settings.update({"script_text": script_text, "load_scene": False, "pass_environment_arguments": False})
        task.settings.update(settings)
        return task

    def execute(self, task):
        """Executes a task against the temporary input file.

        Args:
            task (TaskValidationPythonScript): Task to execute.

        Returns:
            WorkItem: Returned work item.
        """
        work_item = task_base.WorkItem(source_path=self.input_path)
        return task.execute(work_item, self.project, self.log_dir, context={"item_index": 1})

    def read_log(self, task):
        """Reads the validation log written by a task.

        Args:
            task (TaskValidationPythonScript): Task that wrote the log.

        Returns:
            dict: Log data.
        """
        log_path = os.path.join(self.log_dir, "validate_validate_python.json")
        with open(log_path, "r", encoding="utf-8") as file_stream:
            return json.load(file_stream)

    def test_task_is_registered(self):
        """Creates the task from its type key."""
        task = batch_processor_tasks.create_task(constants.TaskType.PYTHON_SCRIPT_VALIDATE)
        self.assertIsInstance(task, validation_python.TaskValidationPythonScript)
        self.assertEqual("Validation", task.category)

    def test_validate_reports_empty_and_syntax_errors(self):
        """Blocks empty scripts and syntax errors before running."""
        self.assertTrue(self.create_task("").validate(self.project).errors)
        self.assertTrue(self.create_task("def broken(:").validate(self.project).errors)
        self.assertEqual([], self.create_task("validation.info('ok')").validate(self.project).errors)

    def test_validate_reports_missing_external_file(self):
        """Requires the external script to exist."""
        task = self.create_task("", script_mode="External File", script_path=os.path.join(self.temp_dir.name, "x.py"))
        self.assertTrue(task.validate(self.project).errors)

    def test_issues_are_logged_without_failing_by_default(self):
        """Writes the issue log and keeps the work item when Fail On Issues is off."""
        task = self.create_task("validation.error('Missing root.')")
        result = self.execute(task)
        self.assertEqual(task_base.normalize_path(self.input_path), result.current_path)
        log_data = self.read_log(task)
        self.assertTrue(log_data["has_issues"])
        self.assertEqual("failed", log_data["entries"][0]["status"])
        self.assertEqual("Missing root.", log_data["entries"][0]["issues"][0]["message"])

    def test_fail_on_issues_raises(self):
        """Fails the task when issues exist and Fail On Issues is on."""
        task = self.create_task("validation.error('Missing root.')", fail_on_issues=True)
        with self.assertRaises(RuntimeError):
            self.execute(task)

    def test_warnings_can_be_ignored(self):
        """Passes warning-only results when warnings are not issues."""
        task = self.create_task("validation.warning('Soft.')", fail_on_issues=True, warnings_are_issues=False)
        self.execute(task)
        self.assertFalse(os.path.exists(os.path.join(self.log_dir, "validate_validate_python.json")))

    def test_script_error_fails_even_without_fail_on_issues(self):
        """Treats a crashing script as a task failure by default, after logging it."""
        task = self.create_task("raise RuntimeError('crash')")
        with self.assertRaises(RuntimeError):
            self.execute(task)
        self.assertTrue(self.read_log(task)["entries"][0]["script_error"])

    def test_skip_raises_task_skip(self):
        """Lets scripts skip files that do not apply."""
        task = self.create_task("validation.skip('Not a rig.')")
        with self.assertRaises(task_base.TaskSkip):
            self.execute(task)

    def test_context_exposes_file_values(self):
        """Exposes the standard batch values to the script."""
        task = self.create_task(
            "validation.check(context['file_name'] == 'hero_rig.ma', 'Wrong file name.')\n"
            "validation.check(not scene_loaded, 'Scene should not be loaded.')\n",
            fail_on_issues=True,
        )
        self.execute(task)


if __name__ == "__main__":
    unittest.main()
