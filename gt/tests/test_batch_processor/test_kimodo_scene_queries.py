"""Opt-in scene-query checks: set GT_TEST_KIMODO_SCENE_QUERIES=1 under mayapy."""

import hashlib
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from gt.tools.batch_processor import batch_processor_maya as maya_runtime
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor.batch_processor_task_base import WorkItem
from gt.tools.batch_processor.tasks.task_kimodo_base import read_json, write_record
from gt.tools.batch_processor.tasks.task_kimodo_definition import TaskKimodoDefinition
from gt.tools.batch_processor.tasks.task_kimodo_generate import TaskKimodoGenerate, save_motion_scene


@unittest.skipUnless(os.environ.get("GT_TEST_KIMODO_SCENE_QUERIES") == "1", "Opt-in Maya integration test")
class TestKimodoSceneQueries(unittest.TestCase):
    """Checks scene prompts, quiet query failures, and source contents in saved outputs."""

    @classmethod
    def setUpClass(cls):
        """Creates an owned standalone session without touching interactive Maya."""
        import maya.standalone

        if maya_runtime.is_maya_session_available():
            raise unittest.SkipTest("Run in a fresh mayapy process to protect the current scene.")
        maya.standalone.initialize(name="python")
        cls.standalone = maya.standalone
        cls.commands = maya_runtime.get_maya_cmds(initialize_standalone=False)

    @classmethod
    def tearDownClass(cls):
        """Releases the standalone session owned by this test class."""
        cls.standalone.uninitialize()

    def setUp(self):
        """Creates disposable outputs and a curve scene, or reads the supplied sandbox scene."""
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.commands.file(new=True, force=True)
        self.project = batch_processor_model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.temporary.name
        self.project.set_suppress_custom_environment_query_errors(True)
        self.project.set_custom_environment_variables({
            "kimodo-prompt": {"value": 'cmds.getAttr("kimodo_trajectory.prompt")', "query": True},
        })
        self.scene = os.environ.get("GT_KIMODO_QUERY_SCENE")
        if not self.scene:
            self.scene = os.path.join(self.temporary.name, "input.ma")
            curve = self.commands.curve(name="kimodo_trajectory", degree=1,
                                        point=[(0, 0, 0), (0, 0, 100)])
            self.commands.addAttr(curve, longName="prompt", dataType="string")
            self.commands.setAttr(f"{curve}.prompt", '[[2, "Walk"], [1, "Stop"]]', type="string")
            self.commands.currentUnit(time="30fps")
            self.commands.playbackOptions(minTime=1, maxTime=90)
            maya_runtime.save_scene(self.scene, file_type="mayaAscii")
        with open(self.scene, "rb") as source_file:
            self.source_digest = hashlib.sha256(source_file.read()).hexdigest()
        self.task = TaskKimodoDefinition(settings={
            "prompt_mode": "text", "prompt_text": "{kimodo-prompt}",
            "path_nodes": "kimodo_trajectory", "path_samples": 8,
        })
        self.item = WorkItem(self.scene)

    def tearDown(self):
        """Closes disposable scenes and verifies that the input bytes were preserved."""
        self.commands.file(new=True, force=True)
        with open(self.scene, "rb") as source_file:
            self.assertEqual(self.source_digest, hashlib.sha256(source_file.read()).hexdigest())

    def test_scene_prompt_preflight_and_definition_capture(self):
        """Validates from an empty scene and captures the query's actual prompt sequence."""
        self.commands.file(new=True, force=True)
        output_dir = os.path.join(self.temporary.name, "definitions")
        self.assertEqual([], self.task.validate(self.project).errors)
        self.assertEqual([], self.task.validate_work_items([self.item], self.project, output_dir).errors)
        self.assertFalse(self.commands.objExists("kimodo_trajectory"))
        outputs = self.task.execute(self.item, self.project, output_dir)
        prompt = self.commands.getAttr("kimodo_trajectory.prompt")
        expected = [description for duration, description in json.loads(prompt)]
        definition = read_json(outputs[0].current_path)
        self.assertEqual(expected, [entry["text"] for entry in definition["prompts"]])
        self.assertEqual("root2d", definition["constraints"][0]["type"])
        self.assertEqual(self.scene, outputs[0].metadata["kimodo"]["source_scene"])

    def test_missing_attribute_query_is_silent(self):
        """Suppresses actual Maya command errors and restores its script editor flags."""
        self.commands.file(new=True, force=True)
        previous_state = self.commands.scriptEditorInfo(query=True, suppressErrors=True)
        stdout = io.StringIO()
        stderr = io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr), mock.patch.object(
            batch_processor_model.logger, "error"
        ) as log_error:
            environment = self.project.get_environment_variables(include_neighbor_paths=False)
        self.assertEqual("", environment["{kimodo-prompt}"])
        self.assertEqual("", stdout.getvalue())
        self.assertEqual("", stderr.getvalue())
        self.assertEqual(previous_state, self.commands.scriptEditorInfo(query=True, suppressErrors=True))
        log_error.assert_not_called()

    def test_saved_output_preserves_curve_and_handles_namespace_collisions(self):
        """Imports a real source scene into a saved generated scene without losing its nodes."""
        identity = [[1, 0, 0], [0, 1, 0], [0, 0, 1]]
        motion = {
            "schema_version": 1,
            "coordinates": {"units": "meters", "up": "y", "forward": "+z",
                            "rotations": "column_local_matrix"},
            "fps": 30.0, "frame_count": 2,
            "skeleton": {"id": "somaskel77", "joint_names": [f"joint_{index}" for index in range(77)],
                         "parents": [-1] + [0] * 76, "offsets": [[0, 0, 0]] + [[1, 0, 0]] * 76},
            "root_positions": [[0, 1, 0], [0, 1, 1]],
            "local_rotations": [[identity] * 77, [identity] * 77],
        }
        motion_path = os.path.join(self.temporary.name, "motion.json")
        write_record(motion_path, motion)
        settings = TaskKimodoGenerate().settings
        settings.update(add_humanik=False, import_incoming_scene=True, incoming_scene_path=self.scene)
        output_path = os.path.join(self.temporary.name, "generated.ma")
        save_motion_scene(motion_path, output_path, settings)
        self.commands.file(output_path, open=True, force=True, executeScriptNodes=False)
        self.assertTrue(self.commands.objExists("kimodo_trajectory"))
        self.assertEqual(77, len(self.commands.ls("kimodo:*", type="joint")))
        self.assertTrue(self.commands.getAttr("kimodo_trajectory.prompt"))
        self.assertEqual(2, self.commands.playbackOptions(query=True, maxTime=True))
        self.commands.namespace(add="kimodo_collision")
        self.commands.createNode("transform", name="kimodo_collision:source_node")
        collision_scene = os.path.join(self.temporary.name, "collision.ma")
        maya_runtime.save_scene(collision_scene, file_type="mayaAscii")
        settings.update(namespace="kimodo_collision", incoming_scene_path=collision_scene)
        result = save_motion_scene(motion_path, output_path, settings)
        self.assertEqual("kimodo_collision1", result["namespace"])
        self.assertTrue(self.commands.objExists("kimodo_collision:source_node"))


if __name__ == "__main__":
    unittest.main()
