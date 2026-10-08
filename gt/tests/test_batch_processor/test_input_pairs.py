"""Regression tests for file assignments, custom input names, and worker reconstruction."""

import json
import os
import tempfile
import unittest
from unittest import mock
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_worker as worker
from gt.tools.batch_processor import batch_processor_maya as maya_runtime
from gt.tools.batch_processor.batch_processor_item_context import is_string_scene, work_item_context
from gt.tools.batch_processor.tasks import task_input_pairs as pairs
from gt.tools.batch_processor.tasks.task_kimodo_base import resolve_motion_text


class TestInputPairs(unittest.TestCase):
    """Exercises both pair modes outside Maya with isolated folders."""

    def setUp(self):
        """Creates an isolated project and input directory."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.input_dir = os.path.join(self.directory.name, "inputs")
        os.makedirs(self.input_dir)

    def create_file(self, relative_path):
        """Creates a disposable input file, including nested directories.

        Args:
            relative_path (str): Path relative to the input directory.

        Returns:
            str: Absolute input file path.
        """
        path = os.path.join(self.input_dir, relative_path)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as input_file:
            input_file.write("// disposable input\n")
        return path

    def create_task(self, **settings):
        """Creates the active input task with project-relative discovery.

        Args:
            **settings: Settings overriding task defaults.

        Returns:
            TaskInputPairs: Registered input task.
        """
        settings.setdefault("source_path", "inputs")
        task = tasks.TaskInputPairs(settings=settings)
        self.project.tasks = [task]
        return task

    def test_folder_reconciliation_and_recovery(self):
        """Retains missing assigned rows and IDs, drops missing empty rows, and recovers restored files."""
        assigned = self.create_file("untitled.ma")
        empty = self.create_file("empty.ma")
        task = self.create_task()
        rows = task.get_pair_rows(self.project, synchronize=True)
        assigned_row = next(row for row in rows if row["input_file"] == "untitled.ma")
        assigned_row["input_string"] = "Untitled Maya File"
        assigned_id = assigned_row["id"]
        os.remove(assigned)
        os.remove(empty)
        available = self.create_file("new.ma")
        rows = task.get_pair_rows(self.project, synchronize=True)
        self.assertEqual(["untitled.ma", "new.ma"], [row["input_file"] for row in rows])
        self.assertEqual(assigned_id, rows[0]["id"])
        self.assertEqual(1, len(task.validate(self.project).warnings))
        self.assertEqual([available], task.discover_files(self.project))
        self.create_file("untitled.ma")
        items = task.prepare(self.project)
        recovered = next(item for item in items if item.metadata["input_file"] == "untitled")
        self.assertEqual("Untitled Maya File", recovered.metadata["input_string"])
        self.assertEqual(assigned_id, recovered.metadata["input_pair_id"])
        self.assertFalse(is_string_scene(recovered))

    def test_nested_files_filters_and_folder_workers(self):
        """Distinguishes repeated filenames by relative path and retains file metadata in workers."""
        self.create_file("first/untitled.ma")
        self.create_file("second/untitled.ma")
        self.create_file("ignored.txt")
        task = self.create_task(folder_pairs=[pairs.create_pair("first/untitled.ma", "First")])
        items = task.prepare(self.project)
        self.assertEqual(2, len(items))
        self.assertEqual("First", items[0].metadata["input_string"])
        self.assertEqual("first", items[0].metadata["source_relative_dir"])
        for item in items:
            self.assertEqual(item.to_dict(), worker.create_initial_work_item(self.project, item.source_path).to_dict())
        task.settings["include_subdirectories"] = False
        self.assertEqual(["first/untitled.ma"],
                         [row["input_file"] for row in task.get_pair_rows(self.project)])
        self.assertEqual([], task.discover_files(self.project))

    def test_hidden_folder_pairs_keep_values_ids_and_order_across_serialization(self):
        """Retains a hidden assignment through visible edits, refreshes, and a project reload."""
        self.create_file("first.ma")
        self.create_file("second.ma")
        task = self.create_task(folder_pairs=[pairs.create_pair("first.ma", "First", enabled=False),
                                             pairs.create_pair("second.ma", "Second")])
        original = dict(task.settings["folder_pairs"][0])
        task.settings["excluded_files"] = ["first.ma"]
        rows = task.get_pair_rows(self.project, synchronize=True)
        self.assertEqual(["second.ma"], [row["input_file"] for row in rows])
        rows[0]["input_string"] = "Edited second"
        task.set_pair_rows(rows)
        restored = model.BatchProcessorModel()
        restored.read_data_from_dict(json.loads(json.dumps(self.project.to_dict())))
        restored_task = restored.tasks[0]
        self.assertEqual(["second.ma"], [row["input_file"] for row in restored_task.get_pair_rows(restored)])
        self.assertEqual(original, restored_task.settings["folder_pairs"][0])
        restored_task.settings["excluded_files"] = []
        recovered = restored_task.get_pair_rows(restored, synchronize=True)
        self.assertEqual(["first.ma", "second.ma"], [row["input_file"] for row in recovered])
        self.assertEqual(original, recovered[0])
        self.assertEqual("Edited second", recovered[1]["input_string"])

    def test_folder_statistics_include_missing_assigned_and_hidden_pairs(self):
        """Counts physical file types and pair availability independently of active descriptions."""
        self.create_file("assigned.ma")
        self.create_file("unassigned.ma")
        self.create_file("inactive.mb")
        self.create_file("hidden.ma")
        self.create_file("ignored.txt")
        task = self.create_task(
            excluded_files=["hidden.ma"],
            folder_pairs=[pairs.create_pair("assigned.ma", "Assigned"),
                          pairs.create_pair("inactive.mb", "Inactive", enabled=False),
                          pairs.create_pair("hidden.ma", "Hidden"), pairs.create_pair("missing.ma", "Retain me")])
        statistics = task.get_file_statistics(self.project)
        expected = {"resolved_count": 2, "total_count": 5, "file_type_count": 3, "pair_count": 4,
                    "assigned_count": 3, "unassigned_count": 1, "inactive_count": 1, "hidden_count": 1,
                    "unavailable_count": 1, "missing_count": 1, "missing_assigned_count": 1}
        self.assertEqual(expected, {key: statistics[key] for key in expected})
        self.assertEqual({".ma": 3, ".mb": 1, ".txt": 1}, statistics["extension_counts"])
        self.assertEqual({".ma": 2}, statistics["resolved_extension_counts"])
        task.settings["extensions"] = [".mb"]
        statistics = task.get_file_statistics(self.project)
        self.assertEqual(2, statistics["unavailable_count"])
        self.assertEqual(1, statistics["missing_assigned_count"])

    def test_manual_statistics_do_not_treat_virtual_names_as_missing_files(self):
        """Counts named scenes, inactive rows, and unnamed descriptions without a source folder."""
        task = self.create_task(input_mode="manual", manual_pairs=[pairs.create_pair("Walk", "Walking"),
                                pairs.create_pair("Run", "", enabled=False), pairs.create_pair("", "No name")])
        statistics = task.get_file_statistics(self.project)
        expected = {"resolved_count": 1, "total_count": 0, "file_type_count": 0, "pair_count": 3,
                    "assigned_count": 2, "unassigned_count": 1, "inactive_count": 1, "hidden_count": 0,
                    "missing_assigned_count": 0, "unavailable_count": 0, "unnamed_count": 1}
        self.assertEqual(expected, {key: statistics[key] for key in expected})
        self.assertEqual({".ma": 1}, statistics["resolved_extension_counts"])

    def test_manual_names_identity_and_round_trip(self):
        """Uses custom names without files and keeps independent stable IDs through serialization."""
        rows = [pairs.create_pair("Custom Walk", "A person walks"), pairs.create_pair("Custom Walk", "A person runs")]
        task = self.create_task(input_mode="manual", manual_pairs=rows)
        initial = task.prepare(self.project)
        task.settings["manual_pairs"].reverse()
        self.assertEqual([item.source_path for item in reversed(initial)],
                         [item.source_path for item in task.prepare(self.project)])
        restored = model.BatchProcessorModel()
        restored.read_data_from_dict(json.loads(json.dumps(self.project.to_dict())))
        self.assertIsInstance(restored.tasks[0], tasks.TaskInputPairs)
        items = restored.tasks[0].prepare(restored)
        self.assertEqual(2, len(set(item.source_path for item in items)))
        for item in items:
            self.assertTrue(is_string_scene(item))
            self.assertFalse(os.path.exists(item.source_path))
            self.assertEqual("Custom Walk.ma", item.metadata["source_relative_path"])
            self.assertEqual("", item.metadata["source_relative_dir"])
            self.assertEqual(item.to_dict(), worker.create_initial_work_item(restored, item.source_path).to_dict())
        self.assertFalse(os.path.exists(task.get_input_dir(self.project)))

    def test_segment_workers_use_their_own_assignments(self):
        """Reconstructs the current segment's pair when several segments use the same file."""
        path = self.create_file("untitled.ma")
        first = self.create_task(folder_pairs=[pairs.create_pair("untitled.ma", "First")])
        first_process = tasks.TaskPythonScript()
        second = tasks.TaskInputPairs(settings={"source_path": "inputs", "start_new_input_list": True,
                                               "folder_pairs": [pairs.create_pair("untitled.ma", "Second")]})
        second_process = tasks.TaskPythonScript()
        self.project.tasks = [first, first_process, second, second_process]
        self.assertEqual("First", worker.create_initial_work_item(
            self.project, path, run_from_task_id=first_process.id).metadata["input_string"])
        self.assertEqual("Second", worker.create_initial_work_item(
            self.project, path, run_from_task_id=second_process.id).metadata["input_string"])

    def test_folder_ids_match_worker_snapshots_before_discovery(self):
        """Gives newly discovered folder rows the same ID when a worker snapshot predates discovery."""
        path = self.create_file("untitled.ma")
        task = self.create_task()
        snapshot = json.loads(json.dumps(self.project.to_dict()))
        item = task.prepare(self.project)[0]
        restored = model.BatchProcessorModel()
        restored.read_data_from_dict(snapshot)
        self.assertEqual(item.to_dict(), worker.create_initial_work_item(restored, path).to_dict())

    def test_literal_runtime_values_and_restoration(self):
        """Inserts both placeholders once and keeps original input names after downstream output changes."""
        name = "Custom {project-dir} $USER"
        description = '  caf\u00e9 {input-file} {project-dir}\nsecond line  '
        task = self.create_task(input_mode="manual", manual_pairs=[pairs.create_pair(name, description)])
        item = task.prepare(self.project)[0]
        previous = {"input-file": "previous", "input-string": "previous string"}
        self.project._input_string_environment = previous
        with mock.patch.object(maya_runtime, "new_scene") as new_scene:
            with work_item_context(self.project, item):
                self.assertEqual(f"{name}: {description}",
                                 self.project.resolve_template("{input-file}: {input-string}"))
                self.assertEqual(name, self.project.resolve_template("{INPUT_FILE}"))
                self.assertEqual(name, self.project.get_environment_variables(include_braces=False)["input-file"])
                self.assertEqual(f"{name}: {description}",
                                 resolve_motion_text("{input-file}: {input-string}", self.project, work_item=item))
            new_scene.assert_called_once()
        self.assertEqual(previous, self.project._input_string_environment)
        item.current_path = os.path.join(self.directory.name, "changed.json")
        with work_item_context(self.project, item):
            self.assertEqual(name, self.project.resolve_template("{input-file}"))

    def test_validation_and_import_safety(self):
        """Rejects unsafe names and JSON paths while allowing inactive and unnamed manual rows."""
        for filename in ("../outside", "C:/outside", "bad:name", "CON", "trailing.", "null\x00name"):
            with self.subTest(filename=filename):
                task = self.create_task(input_mode="manual", manual_pairs=[pairs.create_pair(filename, "Prompt")])
                self.assertTrue(task.validate(self.project).errors)
                self.assertEqual([], task.discover_files(self.project))
        task = self.create_task(input_mode="manual", manual_pairs=[pairs.create_pair(),
                                pairs.create_pair("Valid", ""), pairs.create_pair("bad/name", "", enabled=False)])
        self.assertEqual([], task.validate(self.project).errors)
        self.assertEqual(["Valid"], [item.metadata["input_file"] for item in task.prepare(self.project)])
        for data in ({"version": 5}, {"version": 1, "mode": "folder", "pairs": [pairs.create_pair("../outside.ma")]},
                     {"version": 1, "mode": "manual", "pairs": [pairs.create_pair("bad:name")]},
                     {"version": 1, "mode": "manual", "pairs": "invalid"}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                pairs.read_pair_data(data)
        task = self.create_task(source_path="")
        self.assertEqual("", task.get_input_dir(self.project))
        unset_project = model.BatchProcessorModel()
        self.assertEqual("", tasks.TaskInputPairs().get_input_dir(unset_project))

    def test_kimodo_custom_output_and_metadata(self):
        """Builds Kimodo definitions with custom names and descriptions without accessing a source scene."""
        task = self.create_task(input_mode="manual", manual_pairs=[pairs.create_pair("Custom Walk", "A person walks")])
        item = task.prepare(self.project)[0]
        definition_task = tasks.TaskKimodoDefinition(settings={"use_input_string": True})
        output_dir = os.path.join(self.directory.name, "definitions")
        with mock.patch.object(maya_runtime, "get_maya_cmds") as commands:
            outputs = definition_task.execute(item, self.project, output_dir)
        commands.assert_not_called()
        self.assertEqual(1, len(outputs))
        self.assertEqual("Custom Walk.json", os.path.basename(outputs[0].current_path))
        self.assertEqual("Custom Walk", outputs[0].metadata["input_file"])
        with open(outputs[0].current_path, encoding="utf-8") as definition_file:
            definition = json.load(definition_file)
        self.assertEqual("A person walks", definition["prompts"][0]["text"])
