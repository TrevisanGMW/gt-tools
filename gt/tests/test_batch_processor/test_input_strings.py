"""Regression tests for virtual inputs, worker reconstruction, and Kimodo text definitions."""

import json
import os
import tempfile
import unittest
from unittest import mock
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_worker as worker
from gt.tools.batch_processor import batch_processor_maya as maya_runtime
from gt.tools.batch_processor.tasks import task_input_strings
from gt.tools.batch_processor.batch_processor_item_context import execute_work_item, work_item_context, is_string_scene


class TestInputStrings(unittest.TestCase):
    """Exercises text inputs without requiring Maya or a Kimodo server."""

    def setUp(self):
        """Creates an isolated project with duplicates and literal punctuation."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.values = ['Walk / turn: "left" {project-dir} $HOME', "  café runs  ", "Walk", "Walk", ""]
        self.input_task = tasks.TaskInputStrings(settings={"strings": self.values})
        self.project.tasks = [self.input_task]

    def test_round_trip_and_worker_reconstruction(self):
        """Keeps literal values and duplicate identities across project and worker serialization."""
        restored = model.BatchProcessorModel()
        restored.read_data_from_dict(json.loads(json.dumps(self.project.to_dict())))
        items = restored.discover_input_work_items()
        self.assertEqual(self.values[:-1], [item.metadata["input_string"] for item in items])
        self.assertEqual(4, len(set(item.source_path for item in items)))
        self.assertEqual(4, len(restored.discover_segment_input_files(restored.tasks)))
        for item in items:
            rebuilt = worker.create_initial_work_item(restored, item.source_path)
            self.assertEqual(item.to_dict(), rebuilt.to_dict())
            self.assertTrue(is_string_scene(tasks.WorkItem.from_dict(item.to_dict())))
            self.assertFalse(os.path.exists(item.source_path))
        self.assertFalse(os.path.exists(self.input_task.get_input_dir(self.project)))

    def test_invalid_rows(self):
        """Rejects malformed rows and ignores blank entries without trimming nonblank values."""
        for values in ([], [" "], [None], "Walk", ["one\ntwo"], ["null\x00value"]):
            with self.subTest(values=values):
                task = tasks.TaskInputStrings(settings={"strings": values})
                self.assertTrue(task.validate(self.project).errors)
                self.assertEqual([], task.discover_files(self.project))
        self.assertEqual([], self.input_task.validate(self.project).errors)

    def test_names_use_at_least_two_digits_and_expand_with_input_count(self):
        """Uses consistent padding across each input list, including repeated string values."""
        cases = (
            (1, "string_01.ma", "string_01.ma"),
            (9, "string_01.ma", "string_09.ma"),
            (10, "string_01.ma", "string_10.ma"),
            (99, "string_01.ma", "string_99.ma"),
            (100, "string_001.ma", "string_100.ma"),
            (110, "string_001.ma", "string_110.ma"),
            (1000, "string_0001.ma", "string_1000.ma"),
        )
        for count, first_name, last_name in cases:
            with self.subTest(count=count):
                self.input_task.settings["strings"] = ["Walk"] * count
                items = self.input_task.prepare(self.project)
                names = [os.path.basename(item.source_path) for item in items]
                self.assertEqual(first_name, names[0])
                self.assertEqual(last_name, names[-1])
                self.assertEqual(count, len(set(names)))
                self.assertEqual(sorted(names), names)

    def test_padding_counts_only_active_nonblank_inputs(self):
        """Keeps two digits when inactive and blank rows make the stored table longer."""
        self.input_task.settings.update(
            strings=["Walk"] * 110 + ["", "  "],
            string_enabled=[True, True] + [False] * 108 + [True, True],
        )
        items = self.input_task.prepare(self.project)
        self.assertEqual(["string_01.ma", "string_02.ma"],
                         [os.path.basename(item.source_path) for item in items])

    def test_separate_input_tasks_keep_distinct_virtual_paths(self):
        """Reconstructs matching row names independently using each task's virtual root."""
        other_task = tasks.TaskInputStrings(settings={"strings": [self.values[0]]})
        self.project.add_task(other_task)
        first_item = self.input_task.prepare(self.project)[0]
        other_item = other_task.prepare(self.project)[0]
        self.assertEqual("string_01.ma", os.path.basename(first_item.source_path))
        self.assertEqual("string_01.ma", os.path.basename(other_item.source_path))
        self.assertNotEqual(first_item.source_path, other_item.source_path)
        for item in (first_item, other_item):
            self.assertEqual(item.to_dict(), worker.create_initial_work_item(self.project, item.source_path).to_dict())

    def test_inactive_rows_are_skipped_and_not_counted(self):
        """Skips unchecked rows and assigns consecutive indexes to the remaining rows."""
        task = tasks.TaskInputStrings(settings={"strings": ["A", "B", "", "C"],
                                                "string_enabled": [True, False, True]})
        items = task.prepare(self.project)
        self.assertEqual(["A", "C"], [item.metadata["input_string"] for item in items])
        self.assertEqual([1, 2], [item.metadata["input_string_index"] for item in items])
        task.settings["string_enabled"] = [False, False, True, False]
        self.assertTrue(task.validate(self.project).errors)
        task.settings["string_enabled"] = "yes"
        self.assertTrue(task.validate(self.project).errors)

    def test_number_range(self):
        """Replaces strings with inclusive numbers in either direction and rejects huge ranges."""
        task = tasks.TaskInputStrings(settings={"strings": [], "input_mode": "number_range",
                                                "number_start": 3, "number_end": 5})
        self.assertEqual([], task.validate(self.project).errors)
        items = task.prepare(self.project)
        self.assertEqual(["3", "4", "5"], [item.metadata["input_string"] for item in items])
        self.assertEqual([1, 2, 3], [item.metadata["input_string_index"] for item in items])
        self.assertEqual(["string_01.ma", "string_02.ma", "string_03.ma"],
                         [os.path.basename(item.source_path) for item in items])
        task.settings.update(number_start=2, number_end=0)
        self.assertEqual(["2", "1", "0"], [item.metadata["input_string"] for item in task.prepare(self.project)])
        task.settings.update(number_start=0, number_end=10 ** 6)
        self.assertTrue(task.validate(self.project).errors)
        task.settings.update(number_start="1", number_end=2)
        self.assertTrue(task.validate(self.project).errors)
        self.assertEqual([], task.discover_files(self.project))

    def test_number_range_step_filter_and_skip_list(self):
        """Applies step, odd/even filtering, and skipped numbers, then indexes the survivors."""
        task = tasks.TaskInputStrings(settings={"input_mode": "number_range", "number_start": 1, "number_end": 12,
                                                "number_step": 1, "number_filter": "even",
                                                "number_skip": "4, 8-10"})
        items = task.prepare(self.project)
        self.assertEqual(["2", "6", "12"], [item.metadata["input_string"] for item in items])
        self.assertEqual([1, 2, 3], [item.metadata["input_string_index"] for item in items])
        task.settings.update(number_filter="all", number_skip="", number_step=5, number_start=20, number_end=0)
        self.assertEqual(["20", "15", "10", "5", "0"], task_input_strings.get_number_values(task.settings))
        self.assertEqual({-3, -2, -1, 7, 9}, task_input_strings.parse_number_skip_list("-3..-1 7 9;"))
        for bad_settings in ({"number_step": 0}, {"number_skip": "1, two"}, {"number_filter": "prime"},
                             {"number_start": 1, "number_end": 1, "number_step": 1, "number_skip": "1"}):
            with self.subTest(settings=bad_settings):
                task.settings.update(number_start=0, number_end=10, number_step=1, number_filter="all",
                                     number_skip="")
                task.settings.update(bad_settings)
                self.assertTrue(task.validate(self.project).errors)

    def test_input_file_mode(self):
        """Reads nonblank file lines at prepare time, resolving project-relative paths."""
        task = tasks.TaskInputStrings(settings={"strings": ["ignored"], "input_mode": "file",
                                                "input_file_path": "prompts.txt"})
        self.assertIn("not found", task.validate(self.project).errors[0])
        with open(os.path.join(self.directory.name, "prompts.txt"), "w", encoding="utf-8-sig") as line_file:
            line_file.write("  café  \n\nWalk\nWalk\n")
        items = task.prepare(self.project)
        self.assertEqual(["  café  ", "Walk", "Walk"], [item.metadata["input_string"] for item in items])
        self.assertEqual([1, 2, 3], [item.metadata["input_string_index"] for item in items])
        self.assertEqual(["string_01.ma", "string_02.ma", "string_03.ma"],
                         [os.path.basename(item.source_path) for item in items])
        restored = model.BatchProcessorModel()
        restored.read_data_from_dict(json.loads(json.dumps(self.project.to_dict())))
        restored.tasks = [tasks.TaskInputStrings.from_dict(task.to_dict())]
        for item in items:
            self.assertEqual(item.to_dict(), worker.create_initial_work_item(restored, item.source_path).to_dict())
        with open(os.path.join(self.directory.name, "prompts.txt"), "w", encoding="utf-8") as line_file:
            line_file.write("\n  \n")
        self.assertTrue(task.validate(self.project).errors)
        task.settings["input_file_path"] = ""
        self.assertTrue(task.validate(self.project).errors)
        self.assertEqual("table", task_input_strings.get_input_mode({"input_mode": "unknown"}))

    def test_context_restores_environment_after_error_and_real_output(self):
        """Restores caller values and opens only actual outputs after the initial empty scene."""
        item = self.input_task.prepare(self.project)[0]
        previous_runtime = {"input-string": "previous", "input-string-index": 9}
        self.project._input_string_environment = previous_runtime
        with mock.patch.object(maya_runtime, "new_scene") as new_scene, \
                mock.patch.object(maya_runtime, "get_maya_cmds") as commands:
            with self.assertRaisesRegex(RuntimeError, "failure"):
                with work_item_context(self.project, item):
                    self.assertEqual(self.values[0], self.project.resolve_template("{input-string}"))
                    self.assertEqual("1", self.project.resolve_template("{input-string-index}"))
                    maya_runtime.open_scene(item.current_path)
                    self.assertEqual([], maya_runtime.import_file(item.current_path))
                    with self.assertRaisesRegex(ValueError, "no source file"):
                        maya_runtime.save_scene(item.current_path)
                    commands.assert_not_called()
                    raise RuntimeError("failure")
            self.assertEqual(previous_runtime, self.project._input_string_environment)
            self.assertEqual("previous", self.project.resolve_template("{input-string}"))
            output = tasks.WorkItem(item.source_path, current_path=os.path.join(self.directory.name, "real.ma"),
                                    metadata=item.metadata)
            with work_item_context(self.project, output):
                maya_runtime.open_scene(output.current_path)
                environment = self.project.get_environment_variables(include_braces=False)
                self.assertEqual(self.values[0], environment["input-string"])
            new_scene.assert_called_once()
            commands.return_value.file.assert_called_once()

    def test_single_runner_row_context_and_scene_isolation(self):
        """Runs every duplicate row with a new scene and its own runtime environment."""
        task = tasks.TaskPythonScript(settings={"source_mode": "incoming", "script_text": "pass"})
        self.project.add_task(task)
        seen = []

        def execute(item, project, output_dir, context=None):
            """Records the runtime value seen by a downstream task.

            Args:
                item (WorkItem): Current item.
                project (BatchProcessorModel): Owning project.
                output_dir (str): Task output directory.
                context (dict, optional): Tracker context.

            Returns:
                WorkItem: Unchanged item.
            """
            seen.append((project.get_environment_variables(include_braces=False)["input-string"],
                         project.resolve_template("{input-string}")))
            return item

        with mock.patch.object(task, "execute", side_effect=execute), \
                mock.patch.object(maya_runtime, "new_scene") as new_scene:
            tracker = worker.SingleInstanceBatchRunner().run(self.project)
        self.assertEqual(0, tracker.failed)
        self.assertEqual([(value, value) for value in self.values[:-1]], seen)
        self.assertEqual(4, new_scene.call_count)

    def test_kimodo_definitions_from_strings_without_capture(self):
        """Writes prompt definitions with stable seeds, variations, and no source file access."""
        task = tasks.TaskKimodoDefinition(settings={"use_input_string": True, "variations": 2})
        self.project.add_task(task)
        item = self.input_task.prepare(self.project)[0]
        output_dir = os.path.join(self.directory.name, "definitions")
        self.assertEqual([], task.validate_work_items([item], self.project, output_dir).errors)
        with mock.patch.object(maya_runtime, "get_maya_cmds") as commands:
            outputs = task.execute(item, self.project, output_dir)
        commands.assert_not_called()
        self.assertEqual(2, len(outputs))
        self.assertEqual(["string_01_v001.json", "string_01_v002.json"],
                         [os.path.basename(output.current_path) for output in outputs])
        for output in outputs:
            with open(output.current_path, encoding="utf-8") as definition_file:
                definition = json.load(definition_file)
            self.assertEqual(self.values[0], definition["prompts"][0]["text"])
            self.assertEqual([], definition["constraints"])
            self.assertEqual(task.settings["definition"]["prompts"][0]["duration_seconds"],
                             definition["prompts"][0]["duration_seconds"])
            self.assertEqual(self.values[0], output.metadata["input_string"])
            self.assertFalse(is_string_scene(output))
        with self.assertRaises(tasks.TaskSkip):
            task.execute(item, self.project, output_dir)
        self.assertFalse(os.path.exists(item.source_path))

    def test_kimodo_definition_names_follow_padded_string_names(self):
        """Writes definition filenames and names using the input list's digit width."""
        task = tasks.TaskKimodoDefinition(settings={"use_input_string": True})
        self.project.add_task(task)
        cases = ((3, "string_01.json", "string_03.json"),
                 (110, "string_001.json", "string_110.json"))
        for count, first_name, last_name in cases:
            with self.subTest(count=count):
                self.input_task.settings["strings"] = ["Walk"] * count
                items = self.input_task.prepare(self.project)
                output_dir = os.path.join(self.directory.name, f"definitions_{count}")
                for item, expected_name in ((items[0], first_name), (items[-1], last_name)):
                    with mock.patch.object(maya_runtime, "get_maya_cmds") as commands:
                        outputs = task.execute(item, self.project, output_dir)
                    commands.assert_not_called()
                    self.assertEqual([expected_name], [os.path.basename(output.current_path) for output in outputs])
                    with open(outputs[0].current_path, encoding="utf-8") as definition_file:
                        self.assertEqual(os.path.splitext(expected_name)[0], json.load(definition_file)["name"])

    def test_output_directory_uses_current_row(self):
        """Resolves row tokens at execution time and rejects modifying nonexistent source files."""
        task = tasks.TaskPythonScript(settings={"source_mode": "incoming", "script_text": "pass",
                                               "target_path": "{project-dir}/row_{input-string-index}"})
        self.project.add_task(task)
        item = self.input_task.prepare(self.project)[1]
        with mock.patch.object(maya_runtime, "new_scene"), mock.patch.object(task, "execute") as execute:
            execute_work_item(task, item, self.project, self.directory.name)
            self.assertEqual(os.path.join(self.directory.name, "row_2"), execute.call_args.args[2])
            task.settings["output_mode"] = tasks.OUTPUT_MODE_MODIFY
            with self.assertRaisesRegex(ValueError, "no source file"):
                execute_work_item(task, item, self.project, self.directory.name)

    def test_packaged_template_definitions(self):
        """Runs the packaged string template through definition output with no input directory."""
        from gt.tools.batch_processor import batch_processor_templates

        loaders = {}
        batch_processor_templates.BatchProcessorTemplates.populate_with_template_files(
            batch_processor_templates.PACKAGE_TEMPLATE_SOURCE_DIR, loaders)
        project = loaders["Kimodo_From_Strings"]()
        project.project_file_path = os.path.join(self.directory.name, "prompts.batch")
        definition_task = project.tasks[1]
        with mock.patch.object(maya_runtime, "new_scene"):
            tracker = worker.SingleInstanceBatchRunner().run(project, run_to_task_id=definition_task.id)
        self.assertEqual(0, tracker.failed)
        self.assertEqual(3, tracker.succeeded)
        self.assertFalse(os.path.exists(os.path.join(self.directory.name, "01_input")))
        output_dir = definition_task.resolve_task_path(project)
        for item, value in zip(project.tasks[0].prepare(project), project.tasks[0].settings["strings"]):
            path = definition_task.output_path(item, output_dir)
            with open(path, encoding="utf-8") as definition_file:
                expected_prompts = [
                    {"duration_seconds": seconds, "text": description}
                    for seconds, description in json.loads(value)
                ]
                self.assertEqual(expected_prompts, json.load(definition_file)["prompts"])
