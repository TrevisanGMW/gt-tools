"""Regression coverage for per-file filtering, safe routing, and both runners."""

import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from gt.tools.batch_processor import batch_processor_file_control as file_control
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor import batch_processor_worker
from gt.tools.batch_processor.tasks import task_python_script
from gt.tools.batch_processor.tasks import task_validation_python
from gt.tools.batch_processor.tasks import task_validation
from gt.tools.batch_processor.tracker import tracker_worker


class TestFileControl(unittest.TestCase):
    """Exercises routing using real temporary files and mocked Maya scene I/O."""

    def setUp(self):
        """Creates isolated inputs and a project with no machine-specific paths."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "input" / "clip.ma"
        self.source.parent.mkdir()
        self.source.write_text("original scene", encoding="utf-8")
        self.project = batch_processor_model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = str(self.root)
        self.project.run_settings["create_task_time_log"] = False
        self.project.get_input_module().settings.update({
            "input_dir": str(self.source.parent), "extensions": [".ma"],
        })
        self.task = task_python_script.TaskPythonScript(settings={
            "source_mode": "incoming", "script_text": "pass", "pass_environment_arguments": False,
        })
        self.project.add_task(self.task)
        self.item = task_base.WorkItem(str(self.source))
        self.output = self.root / "output" / "characters" / "clip.ma"
        self.control = file_control.FileControl(self.task, self.project, self.item, str(self.output))

    def assert_filtered(self, action, *args):
        """Executes an action that must terminate this file intentionally.

        Args:
            action (callable): Filtering or routing action.
            *args: Arguments supplied to the action.

        Returns:
            FileFiltered: Raised control-flow signal.
        """
        with self.assertRaises(file_control.FileFiltered) as result:
            action(*args)
        return result.exception

    def test_skip_does_not_create_output(self):
        """A skipped file leaves no automatic output or reservation."""
        self.assert_filtered(self.control.skip_file, "unwanted file")
        self.assertFalse(self.output.parent.exists())
        self.assertEqual("original scene", self.source.read_text(encoding="utf-8"))

    def test_custom_subfolder_preserves_filename_and_input(self):
        """Users can name the subfolder and retain source-relative output folders."""
        self.assert_filtered(self.control.save_to_subfolder, "excluded")
        destination = self.output.parent / "excluded" / "clip.ma"
        self.assertEqual("original scene", destination.read_text(encoding="utf-8"))
        self.assertEqual([destination], list(destination.parent.iterdir()))
        self.assertTrue(self.source.exists())

    def test_custom_environment_variable_destination(self):
        """Custom folder templates resolve through the existing project environment."""
        self.project.set_custom_environment_variables({"filter-root": {
            "value": "{project-dir}/exports/filtered", "query": False,
        }})
        self.assert_filtered(self.control.save_to_folder, "{filter-root}")
        self.assertTrue((self.root / "exports" / "filtered" / "clip.ma").is_file())

    def test_missing_project_does_not_resolve_against_working_directory(self):
        """An unset project directory cannot redirect a relative path into the cwd."""
        self.project.environment_variables["project-dir"] = ""
        with self.assertRaises(ValueError):
            self.control.save_to_folder("filtered")

    def test_invalid_subfolders_and_variables_are_rejected(self):
        """Empty paths, unresolved variables, and escaping subfolders never write."""
        for folder in ("", "..", "../outside", "{missing-variable}", str(self.root)):
            with self.subTest(folder=folder), self.assertRaises(ValueError):
                self.control.save_to_subfolder(folder)

    def test_source_overwrite_is_rejected_even_with_overwrite_enabled(self):
        """Routing never replaces the incoming source."""
        self.task.settings["overwrite"] = True
        with self.assertRaises(ValueError):
            self.control.save_to_folder(str(self.source.parent))
        self.assertEqual("original scene", self.source.read_text(encoding="utf-8"))

    def test_modify_can_skip_but_cannot_route(self):
        """Modify retains its existing meaning while filtering can prevent saving."""
        self.task.settings["output_mode"] = task_base.OUTPUT_MODE_MODIFY
        self.assert_filtered(self.control.skip_file)
        with self.assertRaises(ValueError):
            self.control.save_to_subfolder()

    def test_overwrite_off_preserves_existing_destination(self):
        """An existing routed output is reused without being replaced."""
        self.assert_filtered(self.control.save_to_subfolder)
        destination = self.output.parent / "filtered" / "clip.ma"
        destination.write_text("existing", encoding="utf-8")
        self.assert_filtered(self.control.save_to_subfolder)
        self.assertEqual("existing", destination.read_text(encoding="utf-8"))
        self.task.settings["overwrite"] = True
        self.assert_filtered(self.control.save_to_subfolder)
        self.assertEqual("original scene", destination.read_text(encoding="utf-8"))

    def test_failed_save_cleans_owned_temporary_files_and_preserves_existing_output(self):
        """Save failures remove owned files and release the destination claim."""
        self.assert_filtered(self.control.save_to_subfolder)
        destination = self.output.parent / "filtered" / "clip.ma"
        self.control.write_scene = True
        self.task.settings["overwrite"] = True
        with mock.patch.object(
            task_python_script.batch_processor_maya, "save_scene", side_effect=RuntimeError("save")
        ):
            with self.assertRaises(RuntimeError):
                self.control.save_to_subfolder()
        self.assertEqual("original scene", destination.read_text(encoding="utf-8"))
        self.assertEqual([destination], list(destination.parent.iterdir()))

    def test_active_destination_claim_is_not_removed(self):
        """A competing operation's claim is preserved and prevents writing."""
        destination = self.output.parent / "filtered" / "clip.ma"
        destination.parent.mkdir(parents=True)
        lock_path = Path(f"{destination}.filter.lock")
        lock_path.write_text("another worker", encoding="utf-8")
        with self.assertRaises(RuntimeError):
            self.control.save_to_subfolder()
        self.assertEqual("another worker", lock_path.read_text(encoding="utf-8"))
        self.assertFalse(destination.exists())

    def test_stop_unwinds_existing_context_managers(self):
        """The stop signal releases existing locks instead of terminating the process."""
        self.root.mkdir(exist_ok=True)
        destination = str(self.root / "example")
        with self.assertRaises(file_control.FileFiltered):
            with file_control.destination_lock(destination):
                self.control.skip_file()
        self.assertFalse(Path(f"{destination}.filter.lock").exists())

    def test_preview_and_project_scripts_cannot_filter(self):
        """Editor previews and run-once tasks cannot perform file disposition actions."""
        self.control.preview = True
        with self.assertRaises(ValueError):
            self.control.skip_file()
        self.control.preview = False
        self.control.work_item = None
        with self.assertRaises(ValueError):
            self.control.save_to_subfolder()

    def test_existing_task_skip_still_forwards_input_in_both_runners(self):
        """The new signal never changes legacy TaskSkip pass-through behavior."""
        append_helpers = (
            batch_processor_worker.SingleInstanceBatchRunner._append_skipped_output_items,
            tracker_worker.append_skipped_output_items,
        )
        for append in append_helpers:
            with self.subTest(helper=append.__module__):
                outputs = []
                append(outputs, task_base.TaskSkip("unchanged"), self.item)
                self.assertEqual([self.item], outputs)
                outputs = []
                append(outputs, file_control.FileFiltered("filtered"), self.item)
                self.assertEqual([], outputs)

    def test_python_filter_stops_later_scripts_and_automatic_save(self):
        """Stopping from inline code prevents both subsequent code and scene saving."""
        self.task.settings["script_text"] = (
            "context['control'].skip_file('excluded')\nraise AssertionError('continued')"
        )
        with mock.patch.object(self.task, "load_source_scene"), \
                mock.patch.object(task_python_script.batch_processor_maya, "save_scene") as save:
            self.assert_filtered(self.task.execute, self.item, self.project, str(self.output.parent))
        save.assert_not_called()

    def test_python_route_saves_scene_at_destination_and_does_not_auto_save(self):
        """The routed scene contains the in-memory scene and produces one save only."""
        self.task.settings["script_text"] = "context['control'].save_to_subfolder('filtered')"

        def save_scene(path):
            """Writes a stand-in for Maya's current scene.

            Args:
                path (str): Temporary scene path.
            """
            Path(path).write_text("processed scene", encoding="utf-8")

        with mock.patch.object(self.task, "load_source_scene"), \
                mock.patch.object(task_python_script.batch_processor_maya, "get_maya_cmds"), \
                mock.patch.object(task_python_script.batch_processor_maya, "save_scene",
                                  side_effect=save_scene) as save:
            self.assert_filtered(self.task.execute, self.item, self.project, str(self.output.parent))
        self.assertEqual(1, save.call_count)
        self.assertEqual("processed scene", (self.output.parent / "filtered" / "clip.ma").read_text(encoding="utf-8"))
        self.assertFalse(self.output.exists())

    def test_external_and_batch_scripts_support_all_file_controls(self):
        """File scripts share control actions and stop before any later script or auto-save."""
        actions = {
            "skip": "context['control'].skip_file('matched')",
            "subfolder": "context['control'].save_to_subfolder('excluded', reason='matched')",
            "custom": "context['control'].save_to_folder('{project-dir}/custom', reason='matched')",
        }

        def save_scene(path):
            """Writes the scene contents supplied by the mocked Maya runtime.

            Args:
                path (str): Requested temporary scene path.
            """
            Path(path).write_text("processed scene", encoding="utf-8")

        for mode in ("External File", "Batch Directory"):
            for action_name, action in actions.items():
                for use_run_function in (False, True):
                    with self.subTest(mode=mode, action=action_name, run_function=use_run_function):
                        case_dir = self.root / f"{mode}_{action_name}_{use_run_function}"
                        case_dir.mkdir()
                        first_script = case_dir / "01_filter.py"
                        second_script = case_dir / "02_later.py"
                        script_text = action
                        if use_run_function:
                            script_text = (
                                'def run(context):\n    """Filters the current file.\n\n'
                                '    Args:\n        context (dict): Per-file runtime values.\n    """\n'
                                f"    {action}\n"
                            )
                        first_script.write_text(script_text, encoding="utf-8")
                        second_script.write_text("raise AssertionError('later script ran')", encoding="utf-8")
                        self.task.settings.update({
                            "script_mode": mode,
                            "external_scripts": [{"path": str(path), "enabled": True}
                                                 for path in (first_script, second_script)],
                            "batch_directories": [{"path": str(case_dir)}],
                        })
                        destination = self.root / "custom" / "clip.ma"
                        if destination.exists():
                            destination.unlink()
                        with mock.patch.object(self.task, "load_source_scene"), \
                                mock.patch.object(task_python_script.batch_processor_maya, "get_maya_cmds"), \
                                mock.patch.object(task_python_script.batch_processor_maya, "save_scene",
                                                  side_effect=save_scene) as save:
                            self.assert_filtered(
                                self.task.execute, self.item, self.project, str(case_dir / "output")
                            )
                        self.assertEqual(0 if action_name == "skip" else 1, save.call_count)
                        self.assertFalse((case_dir / "output" / "clip.ma").exists())
                        if action_name == "subfolder":
                            destination = case_dir / "output" / "excluded" / "clip.ma"
                        if action_name != "skip":
                            self.assertEqual("processed scene", destination.read_text(encoding="utf-8"))

    def test_single_runner_all_filtered_does_not_rediscover_or_fail(self):
        """An empty filtered stream stops cleanly before the next processing task."""
        self.task.settings["script_text"] = "context['control'].skip_file('excluded')"
        next_task = task_python_script.TaskPythonScript(settings={"script_text": "raise AssertionError('continued')"})
        self.project.add_task(next_task)
        with mock.patch.object(self.task, "load_source_scene"), mock.patch.object(next_task, "execute") as execute:
            tracker = batch_processor_worker.SingleInstanceBatchRunner().run(self.project)
        self.assertEqual(0, tracker.failed)
        self.assertEqual(1, tracker.skipped)
        execute.assert_not_called()

    def test_single_runner_mixed_inputs_only_forwards_accepted_files(self):
        """Accepted inputs continue while filtered inputs disappear from the stream."""
        accepted = self.source.parent / "accepted.ma"
        accepted.write_text("accepted scene", encoding="utf-8")
        self.task.settings["script_text"] = (
            "if context['file_name'] == 'clip.ma': context['control'].skip_file('excluded')"
        )
        next_task = task_python_script.TaskPythonScript(settings={"script_text": "pass"})
        self.project.add_task(next_task)
        with mock.patch.object(self.task, "load_source_scene"), \
                mock.patch.object(task_python_script.batch_processor_maya, "save_scene"), \
                mock.patch.object(next_task, "execute", side_effect=lambda item, *args, **kwargs: item) as execute:
            tracker = batch_processor_worker.SingleInstanceBatchRunner().run(self.project)
        self.assertEqual(0, tracker.failed)
        self.assertEqual(1, execute.call_count)
        self.assertEqual(str(accepted), execute.call_args.args[0].source_path)

    def test_validation_on_issues_copies_input_and_stops(self):
        """The optional validation policy preserves logs and original file bytes."""
        validation = task_validation_python.TaskValidationPythonScript(settings={
            "script_text": "validation.error('bad file')", "load_scene": False,
            "issue_action": "Copy to folder and stop", "filter_folder": "excluded",
        })
        self.assert_filtered(validation.execute, self.item, self.project, str(self.output.parent))
        self.assertEqual("original scene", (self.output.parent / "excluded" / "clip.ma").read_text(encoding="utf-8"))
        self.assertTrue(list(self.output.parent.glob("validate_*.json")))

    def test_validation_script_control_signal_is_not_a_script_error(self):
        """Python validation understands intentional filtering raised by user code."""
        validation = task_validation_python.TaskValidationPythonScript(settings={
            "script_text": "context['control'].skip_file('excluded')", "load_scene": False,
        })
        self.assert_filtered(validation.execute, self.item, self.project, str(self.output.parent))

    def test_integrity_filter_preserves_report_and_input(self):
        """File Integrity supports the same filter policy without loading Maya."""
        validation = task_validation.TaskValidationFileIntegrity(settings={
            "maximum_file_size_bytes": 1, "issue_action": "Stop processing file",
        })
        self.assert_filtered(validation.execute, self.item, self.project, str(self.output.parent))
        self.assertTrue(list(self.output.parent.glob("validate_*.json")))
        self.assertTrue(self.source.exists())

    def test_scene_validation_copies_source_bytes_without_saving_scene(self):
        """Scene validation routes a copy while leaving scene saving to Python tasks."""
        validation = task_validation.TaskValidationMayaScene(settings={
            "issue_action": "Copy to folder and stop",
        })
        with mock.patch.object(task_validation.task_utils, "load_source_scene"), \
                mock.patch.object(validation, "run_validators", return_value=[{"status_value": 2}]), \
                mock.patch.object(task_python_script.batch_processor_maya, "save_scene") as save:
            self.assert_filtered(validation.execute, self.item, self.project, str(self.output.parent))
        save.assert_not_called()
        self.assertEqual("original scene", (self.output.parent / "filtered" / "clip.ma").read_text(encoding="utf-8"))

    def test_validation_script_errors_still_fail_with_filtering_enabled(self):
        """Unexpected validation exceptions are never treated as matching files."""
        validation = task_validation_python.TaskValidationPythonScript(settings={
            "script_text": "raise RuntimeError('broken script')", "load_scene": False,
            "issue_action": "Copy to folder and stop",
        })
        with self.assertRaises(RuntimeError):
            validation.execute(self.item, self.project, str(self.output.parent))
        self.assertFalse((self.output.parent / "filtered").exists())

    def test_worker_all_filtered_reports_remaining_tasks_skipped_and_exits_successfully(self):
        """The subprocess entry point does not fail or execute tasks after filtering."""
        self.task.settings["script_text"] = "context['control'].skip_file('excluded')"
        next_task = task_python_script.TaskPythonScript(settings={"script_text": "raise AssertionError('continued')"})
        self.project.add_task(next_task)
        event_file = str(self.root / "events.jsonl")
        arguments = [
            "worker", "--project-file", "unused.batch", "--source-file", str(self.source),
            "--event-file", event_file, "--job-id", "test", "--worker-id", "1",
        ]
        with mock.patch("sys.argv", arguments), \
                mock.patch.object(batch_processor_model.BatchProcessorModel, "from_file", return_value=self.project), \
                mock.patch.object(self.task, "load_source_scene"), \
                mock.patch.object(next_task, "execute") as execute, contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as exit_result:
                tracker_worker.main()
        self.assertEqual(0, exit_result.exception.code)
        execute.assert_not_called()
        events = [json.loads(line) for line in Path(event_file).read_text(encoding="utf-8").splitlines()]
        task_events = [event for event in events if event["event"] == "task_finished"]
        self.assertEqual(["skipped", "skipped"], [event["status"] for event in task_events])


if __name__ == "__main__":
    unittest.main()
