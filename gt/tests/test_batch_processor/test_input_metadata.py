"""Regression tests for the Input Metadata task, its helpers, and runtime variables."""

import os
import tempfile
import unittest
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_input_metadata as input_metadata
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.batch_processor_item_context import work_item_context
from gt.tools.batch_processor.tasks.task_kimodo_base import resolve_motion_text, uses_runtime_variables


def build_row(input_key, *values, enabled=True):
    """Builds a metadata row for tests.

    Args:
        input_key (str): Row input key.
        *values: Slot values in slot order.
        enabled (bool, optional): Whether the row applies.

    Returns:
        dict: Row data.
    """
    return input_metadata.create_row(input_key, list(values), enabled)


class TestInputMetadataHelpers(unittest.TestCase):
    """Exercises pure naming, matching, and merging helpers."""

    def test_clean_slot_name(self):
        """Cleans user names into variable-safe names."""
        self.assertEqual("shot-code", input_metadata.clean_slot_name("  Shot Code "))
        self.assertEqual("speed-scale", input_metadata.clean_slot_name("speed_scale"))
        self.assertEqual("a-b", input_metadata.clean_slot_name("A--b!!"))
        self.assertEqual("", input_metadata.clean_slot_name("  ---  "))

    def test_slot_name_errors(self):
        """Rejects digit-first and duplicate names."""
        self.assertIn("digit", input_metadata.get_slot_name_error("1st"))
        self.assertEqual("", input_metadata.get_slot_name_error("seed"))
        settings = {"slot_count": 2, "slot_names": ["seed", "Seed"], "metadata_rows": []}
        self.assertEqual(1, len(input_metadata.get_settings_errors(settings)))
        settings["slot_count"] = 1
        self.assertEqual([], input_metadata.get_settings_errors(settings))

    def test_item_identities(self):
        """Builds every matchable identity of an item."""
        identities = input_metadata.get_item_identities("Walk\\Walk_090.ma", input_file="Walk_090")
        self.assertEqual(["walk/walk_090.ma", "walk/walk_090", "walk_090.ma", "walk_090"], identities)

    def test_row_matching(self):
        """Matches exact keys case-insensitively and glob patterns."""
        identities = input_metadata.get_item_identities("walk/walk_090.ma")
        self.assertTrue(input_metadata.row_matches("WALK_090", identities))
        self.assertTrue(input_metadata.row_matches("walk/walk_090.ma", identities))
        self.assertTrue(input_metadata.row_matches("*_090", identities))
        self.assertTrue(input_metadata.row_matches("*", identities))
        self.assertFalse(input_metadata.row_matches("walk_09", identities))
        self.assertFalse(input_metadata.row_matches("", identities))

    def test_resolve_values_later_rows_override(self):
        """Applies rows top to bottom with empty cells setting nothing."""
        rows = [build_row("*", "default", "keep"), build_row("walk_090", "517", ""),
                build_row("walk_090", "999", "", enabled=False)]
        values, matched = input_metadata.resolve_values(rows, 2, input_metadata.get_item_identities("walk_090.ma"))
        self.assertEqual({0: "517", 1: "keep"}, values)
        self.assertEqual([rows[0]["id"], rows[1]["id"]], matched)

    def test_merge_metadata_keeps_earlier_values(self):
        """Writes number and name keys and keeps earlier values for empty slots."""
        merged = input_metadata.merge_metadata({"1": "old", "note": "upstream"}, {1: "fast"}, ["", "speed"], 2)
        self.assertEqual({"1": "old", "note": "upstream", "2": "fast", "speed": "fast"}, merged)

    def test_replace_metadata_variables_is_literal(self):
        """Inserts values literally and resolves unknown metadata variables to empty text."""
        runtime = {"input-meta-seed": "{project-dir}", "input-meta-1": "517"}
        result = input_metadata.replace_metadata_variables("{input_meta_seed}/{INPUT-META-1}/{input-meta-x}", runtime)
        self.assertEqual("{project-dir}/517/", result)


class TestInputMetadataTask(unittest.TestCase):
    """Exercises the task model, execution, and runtime variables outside Maya."""

    def setUp(self):
        """Creates a project with an input folder and an Input Metadata task."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.input_dir = os.path.join(self.directory.name, "inputs")
        os.makedirs(os.path.join(self.input_dir, "walk"))
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.task = tasks.create_task(constants.TaskType.INPUT_METADATA)
        self.task.settings.update(slot_count=2, slot_names=["Seed", "note", "", "", ""])
        self.task.set_rows([build_row("walk_090", "517", "best take"), build_row("*_180", "623")])
        self.project.tasks = [self.task]

    def build_item(self, relative_path):
        """Builds an incoming work item below the input folder.

        Args:
            relative_path (str): Path relative to the input folder.

        Returns:
            WorkItem: Work item with source-relative metadata.
        """
        return tasks.WorkItem(source_path=os.path.join(self.input_dir, relative_path), source_root=self.input_dir)

    def test_task_flags_and_registration(self):
        """Registers a pass-through, indexless task in the Inputs menu category."""
        self.assertIs(tasks.TaskInputMetadata, tasks.get_task_class(constants.TaskType.INPUT_METADATA))
        self.assertTrue(self.task.uses_incoming_files())
        self.assertFalse(self.task.writes_to_target_path())
        self.assertFalse(self.task.is_input_task)
        self.assertFalse(self.task.includes_task_index())
        self.assertIn(tasks.TaskInputMetadata, tasks.get_task_categories()["Inputs"])

    def test_serialization_round_trip(self):
        """Keeps slot names and rows through serialization."""
        restored = tasks.create_task_from_dict(self.task.to_dict())
        self.assertEqual(self.task.get_rows(), restored.get_rows())
        self.assertEqual(["seed", "note", "", "", ""], restored.get_slot_names())

    def test_execute_attaches_metadata_without_changing_paths(self):
        """Returns the same paths with number and name keys."""
        item = self.build_item("walk/walk_090.ma")
        item.metadata["custom"] = "kept"
        output = self.task.execute(item, self.project, "")
        self.assertEqual(item.current_path, output.current_path)
        self.assertEqual(item.source_path, output.source_path)
        self.assertEqual("kept", output.metadata["custom"])
        expected = {"1": "517", "seed": "517", "2": "best take", "note": "best take"}
        self.assertEqual(expected, output.metadata[input_metadata.METADATA_KEY])
        self.assertNotIn(input_metadata.METADATA_KEY, item.metadata)

    def test_unmatched_item_gets_empty_values(self):
        """Gives unmatched items empty values so variables still resolve."""
        output = self.task.execute(self.build_item("run_000.ma"), self.project, "")
        self.assertEqual({"1": "", "seed": "", "2": "", "note": ""}, output.metadata[input_metadata.METADATA_KEY])

    def test_chained_tasks_merge(self):
        """Lets a later task override set values while keeping the rest."""
        later = tasks.create_task(constants.TaskType.INPUT_METADATA)
        later.settings.update(slot_count=1, slot_names=["seed", "", "", "", ""])
        later.set_rows([build_row("walk_090", "777")])
        first = self.task.execute(self.build_item("walk/walk_090.ma"), self.project, "")
        second = later.execute(first, self.project, "")
        self.assertEqual("777", second.metadata[input_metadata.METADATA_KEY]["seed"])
        self.assertEqual("best take", second.metadata[input_metadata.METADATA_KEY]["note"])

    def test_validation(self):
        """Reports invalid names as errors and rows matching no upstream input as warnings."""
        for relative_path in ("walk/walk_090.ma", "run_000.ma"):
            with open(os.path.join(self.input_dir, relative_path), "w", encoding="utf-8") as input_file:
                input_file.write("//Maya ASCII\n")
        input_task = tasks.create_task(constants.TaskType.INPUT)
        input_task.settings.update(source_path=self.input_dir, include_subdirectories=True, extensions=[".ma"])
        self.project.tasks = [input_task, self.task]
        result = self.task.validate(self.project)
        self.assertEqual([], result.errors)
        self.assertEqual(1, len(result.warnings))
        self.assertIn("*_180", result.warnings[0])
        self.assertEqual([], self.task.validate_work_items([], self.project, "").warnings)
        self.task.settings["slot_names"] = ["2nd", "", "", "", ""]
        self.assertEqual(1, len(self.task.validate(self.project).errors))
        self.assertEqual(1, len(self.task.validate_work_items([], self.project, "").errors))

    def test_runtime_variables(self):
        """Exposes values to templates and environment while an item runs."""
        output = self.task.execute(self.build_item("walk/walk_090.ma"), self.project, "")
        with work_item_context(self.project, output):
            resolved = self.project.resolve_template("{input-meta-seed}_{input_meta_1}_{input-meta-note}")
            environment = self.project.get_environment_variables(include_braces=False)
        self.assertEqual("517_517_best take", resolved)
        self.assertEqual("517", environment["input-meta-seed"])
        self.assertEqual("", self.project.resolve_template("{input-meta-seed}"))

    def test_kimodo_motion_text_reads_metadata(self):
        """Lets motion text use metadata variables like any other per-input value."""
        output = self.task.execute(self.build_item("walk/walk_090.ma"), self.project, "")
        self.assertTrue(uses_runtime_variables("A person walks. {input-meta-note}"))
        self.assertEqual("note: best take", resolve_motion_text("note: {input-meta-note}", self.project,
                                                                work_item=output))

    def test_custom_variables_cannot_use_metadata_prefix(self):
        """Reserves the input-meta- prefix for metadata variables."""
        self.assertFalse(model.BatchProcessorModel.is_custom_environment_name_available("{input-meta-seed}"))
        self.assertTrue(model.BatchProcessorModel.is_custom_environment_name_available("{my-seed}"))


if __name__ == "__main__":
    unittest.main()
