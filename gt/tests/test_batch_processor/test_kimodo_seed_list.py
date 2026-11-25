"""Regression tests for the Kimodo Definition "Seed list" seed policy."""

import os
import tempfile
import unittest
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_input_metadata as input_metadata
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.tasks import task_kimodo_base as kimodo_base
from gt.tools.batch_processor.tasks import task_kimodo_definition as definition_task
from gt.tools.batch_processor.tasks.task_kimodo_definition import TaskKimodoDefinition


class TestSeedListHelpers(unittest.TestCase):
    """Exercises seed list parsing and planning."""

    def test_parse_seed_list_formats(self):
        """Accepts brackets, commas, semicolons, spaces, repeatable and skip entries."""
        self.assertEqual([123, 456, 789], kimodo_base.parse_seed_list("[123, 456, 789]"))
        self.assertEqual(["*", "-", 7], kimodo_base.parse_seed_list(" * ; -\n7 "))
        self.assertEqual([], kimodo_base.parse_seed_list("  "))
        self.assertEqual([], kimodo_base.parse_seed_list("[]"))

    def test_parse_seed_list_rejects_bad_entries(self):
        """Rejects negative, non-integer, and out-of-range seeds."""
        for text in ("12a", "-5", "1.5", "4294967296"):
            with self.assertRaises(ValueError):
                kimodo_base.parse_seed_list(text)

    def test_build_seed_plan(self):
        """Maps entries to definition positions, skipping "-" and filling missing entries with "*"."""
        self.assertEqual((3, [(1, 123), (2, 456), (3, 789)]), kimodo_base.build_seed_plan([123, 456, 789], 1))
        self.assertEqual((5, [(1, None), (3, 789), (4, None), (5, None)]),
                         kimodo_base.build_seed_plan(["*", "-", 789], 5))
        self.assertEqual((3, [(3, 789)]), kimodo_base.build_seed_plan(["-", "-", 789], 1))
        self.assertEqual((2, [(1, None), (2, None)]), kimodo_base.build_seed_plan([], 2))


class TestSeedListDefinitions(unittest.TestCase):
    """Exercises the Kimodo Definition task with the list seed policy."""

    def setUp(self):
        """Creates a list-policy task and a per-file twin for comparison."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.task = TaskKimodoDefinition(settings={"variations": 3})
        self.task.settings.update(seed_policy="list", variation_ranges={"guidance_text": [1, 3]},
                                  prompt_choices="Walk\nRun")
        self.per_file = TaskKimodoDefinition(settings=dict(self.task.settings, seed_policy="per_file"))

    def build_item(self, name="walk_090.ma", metadata=None):
        """Builds a work item for an existing Maya ASCII stand-in file.

        Args:
            name (str): Input file name.
            metadata (dict, optional): Work item metadata.

        Returns:
            WorkItem: Incoming item.
        """
        path = os.path.join(self.directory.name, name)
        with open(path, "w", encoding="utf-8") as scene_file:
            scene_file.write("//Maya ASCII\n")
        return tasks.WorkItem(source_path=path, metadata=metadata or {}, source_root=self.directory.name)

    def test_listed_seed_changes_only_the_generation_seed(self):
        """Keeps per-file variation choices while using the exact listed seed."""
        definition = self.task.settings["definition"]
        listed = definition_task.vary_definition(definition, self.task.settings, "a.ma", 2, seed=517)
        repeatable = definition_task.vary_definition(definition, self.per_file.settings, "a.ma", 2)
        default = definition_task.vary_definition(definition, self.task.settings, "a.ma", 2)
        self.assertEqual(517, listed["parameters"]["seed"])
        self.assertEqual(repeatable["parameters"]["seed"], default["parameters"]["seed"])
        self.assertEqual(repeatable["parameters"]["guidance"], listed["parameters"]["guidance"])
        self.assertEqual(repeatable["prompts"], listed["prompts"])

    def test_seed_plan_reads_input_metadata(self):
        """Resolves {input-meta-seed} per input and falls back to repeatable seeds when empty."""
        self.task.settings["seed_list"] = "{input-meta-seed}"
        metadata_task = tasks.create_task(constants.TaskType.INPUT_METADATA)
        metadata_task.settings.update(slot_count=1, slot_names=["seed", "", "", "", ""])
        metadata_task.set_rows([input_metadata.create_row("walk_090", ["*, -, 789"], True)])
        matched = metadata_task.execute(self.build_item(), self.project, "")
        unmatched = metadata_task.execute(self.build_item("run_000.ma"), self.project, "")
        self.assertEqual((3, [(1, None), (3, 789)]), self.task.get_seed_plan(self.project, matched))
        self.assertEqual((3, [(1, None), (2, None), (3, None)]), self.task.get_seed_plan(self.project, unmatched))
        self.assertEqual((3, [(1, None), (2, None), (3, None)]), self.task.get_seed_plan(self.project, None))

    def test_build_definitions_follow_plan(self):
        """Creates only planned definitions, in order, with their exact seeds."""
        captured = {"frames": [], "start": 0, "end": 60, "source_fps": 30, "poses": [],
                    "path_frames": [0, 30, 60], "path": {
                        "type": "root2d", "frame_indices": [0, 1, 2], "smooth_root_2d": [[0, 0], [0, 1], [0, 2]]}}
        base = self.task.base_definition(None)
        definitions = self.task.build_definitions(captured, base, "a.ma", plan=[(1, None), (3, 789)])
        repeatable = self.per_file.build_definitions(captured, base, "a.ma")
        self.assertEqual(2, len(definitions))
        self.assertEqual(repeatable[0]["parameters"]["seed"], definitions[0]["parameters"]["seed"])
        self.assertEqual(789, definitions[1]["parameters"]["seed"])
        self.assertEqual(repeatable[2]["prompts"], definitions[1]["prompts"])

    def test_output_names_keep_definition_positions(self):
        """Names a lone listed definition after its position so promotion keeps official names."""
        item = self.build_item()
        directory = os.path.join(self.directory.name, "out")
        path = self.task.output_path(item, directory, variation=3, seed=789, variation_count=3)
        self.assertEqual("walk_090_v003.json", os.path.basename(path))

    def test_validation(self):
        """Reports invalid static and per-input lists, and accepts variables and valid lists."""
        self.task.settings["seed_list"] = "1, 2, x"
        self.assertTrue(any("Seed list" in error for error in self.task.validate(self.project).errors))
        self.task.settings["seed_list"] = "{input-meta-seed}"
        self.assertFalse(any("Seed list" in error for error in self.task.validate(self.project).errors))
        bad_item = self.build_item(metadata={input_metadata.METADATA_KEY: {"seed": "abc"}})
        good_item = self.build_item("run_000.ma", metadata={input_metadata.METADATA_KEY: {"seed": "-, 5"}})
        directory = os.path.join(self.directory.name, "out")
        result = self.task.validate_work_items([bad_item, good_item], self.project, directory)
        self.assertEqual(1, len([error for error in result.errors if "Seed list" in error]))


if __name__ == "__main__":
    unittest.main()
