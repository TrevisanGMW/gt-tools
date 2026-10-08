"""Pure motion-text parsing, variable resolution, and definition execution tests."""

import copy
import json
import os
import tempfile
import unittest
import sys
import types
from unittest import mock

from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_task_base as base
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor.tasks import task_kimodo_base as kimodo_base
from gt.tools.batch_processor.tasks.task_kimodo_definition import TaskKimodoDefinition
from gt.tools.batch_processor.tasks import task_kimodo_definition as definition_task


class TestKimodoMotionText(unittest.TestCase):
    """Checks format limits, literal substitution, and retained authoring data."""

    def test_order_and_punctuation(self):
        """Keeps fractional durations and punctuation in descriptions unambiguous."""
        descriptions = ['Walk, turn (left), and say "hello".', "Arrête-toi; don't move."]
        text = json.dumps([[2.5, descriptions[0]], [1, descriptions[1]]])
        self.assertEqual([
            {"duration_seconds": 2.5, "text": descriptions[0]},
            {"duration_seconds": 1, "text": descriptions[1]},
        ], kimodo_base.parse_motion_text(text))

    def test_invalid_sequences_and_limits(self):
        """Rejects malformed pairs, invalid numbers, empty descriptions, and excess lengths."""
        invalid = [
            "", "[]", "not JSON", "(2, Walk), (1, Stop)", '{"seconds": 2}',
            '[[2, "Walk", "extra"]]', '[[true, "Walk"]]', '[[0, "Walk"]]',
            '[[-1, "Walk"]]', '[[31, "Walk"]]', '[[NaN, "Walk"]]',
            '[[Infinity, "Walk"]]', '[[2, " "]]', '[[2, null]]',
            json.dumps([[10 ** 1000, "Walk"]]),
            json.dumps([[1, "Walk"]] * 17), json.dumps([[30, "Walk"]] * 5),
            json.dumps([[1, "x" * 10001]]), '__import__("os").getcwd()',
        ]
        for text in invalid:
            with self.subTest(text=text[:60]), self.assertRaises(ValueError):
                kimodo_base.parse_motion_text(text)

    def test_table_default_and_mode_round_trip(self):
        """Retains table rows across text mode changes and serialization."""
        task = TaskKimodoDefinition()
        self.assertEqual("table", task.settings["prompt_mode"])
        table = copy.deepcopy(task.settings["definition"]["prompts"])
        task.settings.update(prompt_mode="text", prompt_text=kimodo_base.MOTION_TEXT_EXAMPLE)
        self.assertEqual([2, 1], [prompt["duration_seconds"] for prompt in task.base_definition(None)["prompts"]])
        self.assertEqual(table, task.settings["definition"]["prompts"])
        restored = TaskKimodoDefinition.from_dict(task.to_dict())
        self.assertEqual("text", restored.settings["prompt_mode"])
        self.assertEqual(task.base_definition(None)["prompts"], restored.base_definition(None)["prompts"])
        task.settings["prompt_mode"] = "table"
        self.assertEqual(table, task.base_definition(None)["prompts"])

    def test_runtime_sequences_and_literal_description_variables(self):
        """Resolves input metadata without treating braces, quotes, or paths as JSON syntax."""
        project = batch_processor_model.BatchProcessorModel()
        project.set_custom_environment_variables({"seconds": "2.5", "motion": "{input-string}"})
        task = TaskKimodoDefinition(settings={"prompt_mode": "text", "prompt_text": "{motion}"})
        sequences = [[[2, "Walk {project-name}"], [1, "Stop"]], [[3, "Run"]]]
        for pairs in sequences:
            item = base.WorkItem("walk.ma", metadata={"input_string": json.dumps(pairs)})
            self.assertEqual([{"duration_seconds": duration, "text": text} for duration, text in pairs],
                             task.base_definition(project, item)["prompts"])
        value = 'Say "hello", then follow C:\\poses\\walk (left); {project-name}.'
        item = base.WorkItem("walk.ma", metadata={"input_string": value, "input_string_index": 0})
        task.settings["prompt_text"] = '[["{seconds}", "{input-string}"], [1, "{input-string-index}"]]'
        self.assertEqual([
            {"duration_seconds": 2.5, "text": value}, {"duration_seconds": 1, "text": "0"},
        ], task.base_definition(project, item)["prompts"])

    def test_filename_and_os_environment(self):
        """Uses the current filename and keeps Windows path characters literal."""
        project = batch_processor_model.BatchProcessorModel()
        item = base.WorkItem("original.ma", current_path='C:/clips/Walk, turn (left).ma')
        task = TaskKimodoDefinition(settings={"prompt_mode": "text", "prompt_text": (
            '[[2, "{input-file-stem}"], [1, "{input-file-name}"], [1, "{input-file-path}"]]')})
        prompts = task.base_definition(project, item)["prompts"]
        self.assertEqual(["Walk, turn (left)", "Walk, turn (left).ma", item.current_path],
                         [prompt["text"] for prompt in prompts])
        with mock.patch.dict(os.environ, {"GT_KIMODO_TEST_SEQUENCE": '[[2, "Walk"]]'}):
            task.settings["prompt_text"] = "%GT_KIMODO_TEST_SEQUENCE%"
            self.assertEqual("Walk", task.base_definition(project, item)["prompts"][0]["text"])

    def test_scene_queries_wait_for_each_source_scene(self):
        """Defers direct and aliased queries and resolves them after opening each input."""
        project = batch_processor_model.BatchProcessorModel()
        project.set_custom_environment_variables({
            "kimodo-prompt": {"value": 'cmds.getAttr("kimodo_trajectory.prompt")', "query": True},
            "motion": {"value": "{kimodo-prompt}", "query": False},
        })
        task = TaskKimodoDefinition(settings={"prompt_mode": "text", "prompt_text": "{motion}"})
        commands = types.ModuleType("maya.cmds")
        commands.file = mock.Mock()
        commands.getAttr = mock.Mock()
        maya_module = types.ModuleType("maya")
        maya_module.cmds = commands
        captured = {"frames": [], "poses": [], "path": None, "path_frames": [],
                    "start": 0, "end": 59, "source_fps": 30}
        with tempfile.TemporaryDirectory() as directory, mock.patch.dict(
            sys.modules, {"maya": maya_module, "maya.cmds": commands}
        ), mock.patch.object(batch_processor_maya, "get_maya_cmds", return_value=commands), mock.patch.object(
            definition_task, "capture_scene", return_value=captured
        ):
            project.environment_variables["project-dir"] = directory
            items = []
            for name in ("Walk", "Run"):
                path = os.path.join(directory, f"{name}.ma")
                with open(path, "w", encoding="utf-8") as scene_file:
                    scene_file.write("// Source scene stand-in")
                items.append(base.WorkItem(path))
            output_dir = os.path.join(directory, "output")
            for token in ("{kimodo-prompt}", "{motion}"):
                task.settings["prompt_text"] = token
                self.assertEqual([], task.validate(project).errors)
                self.assertTrue(task.validate(project).warnings)
                self.assertEqual([], task.validate_work_items(items, project, output_dir).errors)
            commands.file.assert_not_called()
            commands.getAttr.assert_not_called()
            for item in items:
                description = os.path.splitext(os.path.basename(item.current_path))[0]
                commands.getAttr.return_value = json.dumps([[2, description]])
                commands.file.reset_mock()
                outputs = task.execute(item, project, output_dir)
                commands.file.assert_called_once_with(
                    item.current_path, open=True, force=True, executeScriptNodes=False, prompt=False
                )
                self.assertEqual(item.current_path, outputs[0].metadata["kimodo"]["source_scene"])
                with open(outputs[0].current_path, encoding="utf-8") as definition_file:
                    self.assertEqual(description, json.load(definition_file)["prompts"][0]["text"])

    def test_invalid_scene_prompt_fails_after_scene_is_opened(self):
        """Keeps runtime validation strict when a query returns malformed motion text."""
        project = batch_processor_model.BatchProcessorModel()
        project.set_custom_environment_variables({
            "motion": {"value": "'not JSON'", "query": True},
        })
        task = TaskKimodoDefinition(settings={"prompt_mode": "text", "prompt_text": "{motion}"})
        maya_module = types.ModuleType("maya")
        commands = types.ModuleType("maya.cmds")
        maya_module.cmds = commands
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "input.ma")
            with open(path, "w", encoding="utf-8") as scene_file:
                scene_file.write("// Source scene stand-in")
            with mock.patch.dict(sys.modules, {"maya": maya_module, "maya.cmds": commands}), mock.patch.object(
                batch_processor_maya, "get_maya_cmds"
            ) as get_commands:
                self.assertEqual([], task.validate(project).errors)
                with self.assertRaisesRegex(ValueError, "Motion text must be JSON pairs"):
                    task.execute(base.WorkItem(path), project, os.path.join(directory, "output"))
                get_commands.return_value.file.assert_called_once()

    def test_inactive_rows_and_template_prompts(self):
        """Validates active text even when retained local or template prompts are invalid."""
        task = TaskKimodoDefinition(settings={"prompt_mode": "text", "prompt_text": '[[2, "Walk"]]'})
        task.settings["definition"]["prompts"][0]["duration_seconds"] = "invalid"
        self.assertEqual([], task.validate(None).errors)
        template = {"definition": copy.deepcopy(task.settings["definition"]), "constraints": []}
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "setup.json")
            with open(path, "w", encoding="utf-8") as stream:
                json.dump(template, stream)
            task.settings["template_path"] = path
            self.assertEqual([{"duration_seconds": 2, "text": "Walk"}], task.base_definition(None)["prompts"])
            self.assertEqual("invalid", task.settings["definition"]["prompts"][0]["duration_seconds"])

    def test_motion_text_respects_source_timing_and_retime(self):
        """Fits segment proportions to source timing or uses requested durations with retiming."""
        task = TaskKimodoDefinition(settings={"prompt_mode": "text", "prompt_text": '[[2, "Walk"], [1, "Stop"]]'})
        captured = {"frames": [], "poses": [], "path": None, "path_frames": [],
                    "start": 0, "end": 119, "source_fps": 30}
        definition = task.base_definition(None)
        resolved = task.build_definitions(captured, definition, "walk.ma")[0]
        self.assertEqual([80, 40], [int(prompt["duration_seconds"] * 30) for prompt in resolved["prompts"]])
        task.settings["duration_mode"] = "definition"
        with self.assertRaisesRegex(ValueError, "enable Retime Constraints"):
            task.build_definitions(captured, definition, "walk.ma")
        task.settings["retime_constraints"] = True
        resolved = task.build_definitions(captured, definition, "walk.ma")[0]
        self.assertEqual([60, 30], [int(prompt["duration_seconds"] * 30) for prompt in resolved["prompts"]])

    def test_preflight_and_execution_use_each_input(self):
        """Creates complete text definitions without scene commands and rejects bad rows before execution."""
        project = batch_processor_model.BatchProcessorModel()
        task = TaskKimodoDefinition(settings={
            "prompt_mode": "text", "prompt_text": "{input-string}", "use_input_string": True,
            "variations": 2, "prompt_replacements": [{"variation": 2, "search": "Walk", "replace": "Run"}],
        })
        project.add_task(task)
        original = copy.deepcopy(task.settings["definition"])
        with tempfile.TemporaryDirectory() as directory:
            identity = os.path.join(directory, "virtual.ma")
            item = base.WorkItem(identity, metadata={
                "input_string": '[[2, "Walk"], [1, "Stop"]]', "input_string_path": identity,
            })
            output_dir = os.path.join(directory, "output")
            self.assertEqual([], task.validate(project).errors)
            self.assertTrue(task.validate(project).warnings)
            self.assertEqual([], task.validate_work_items([item], project, output_dir).errors)
            with mock.patch.object(batch_processor_maya, "get_maya_cmds") as commands:
                outputs = task.execute(item, project, output_dir)
            commands.assert_not_called()
            for output, expected_first in zip(outputs, ("Walk", "Run")):
                with open(output.current_path, encoding="utf-8") as stream:
                    definition = json.load(stream)
                self.assertEqual([expected_first, "Stop"], [prompt["text"] for prompt in definition["prompts"]])
                self.assertEqual([2, 1], [prompt["duration_seconds"] for prompt in definition["prompts"]])
            item.metadata["input_string"] = "invalid"
            self.assertTrue(task.validate_work_items([item], project, output_dir).errors)
            with self.assertRaises(ValueError), mock.patch.object(batch_processor_maya, "get_maya_cmds") as commands:
                task.execute(item, project, output_dir)
            commands.assert_not_called()
        self.assertEqual(original, task.settings["definition"])


if __name__ == "__main__":
    unittest.main()
