"""Opt-in tests using disposable Maya standalone scenes and a running GT bridge."""

import os
import json
import unittest
import tempfile


class TestKimodoInputScene(unittest.TestCase):
    """Checks evaluated capture from an explicitly supplied HumanIK source scene."""

    def test_live_capture(self):
        """Captures the supplied scene without saving or baking the source file."""
        scene = os.environ.get("GT_KIMODO_INPUT_SCENE")
        if not scene:
            self.skipTest("Set GT_KIMODO_INPUT_SCENE to run the large scene integration check.")
        import maya.standalone
        import maya.cmds as cmds
        from gt.utils import kimodo

        maya.standalone.initialize(name="python")
        try:
            cmds.file(scene, open=True, force=True, executeScriptNodes=False, prompt=False)
            captures = []
            for frame in (296, 423, 648):
                cmds.currentTime(frame, edit=True, update=True)
                self.assertEqual(True, cmds.getAttr("kimodo_pose:motion.isConstraintPose"))
                skeleton = json.loads(cmds.getAttr("kimodo_pose:motion.kimodoSkeleton"))
                differences = []
                for index, name in enumerate(skeleton["joint_names"][1:], 1):
                    actual = cmds.getAttr(f"kimodo_pose:{name}.translate")[0]
                    delta = max(abs(value / 100 - expected) for value, expected in
                                zip(actual, skeleton["offsets"][index]))
                    differences.append((delta, name, actual, skeleton["offsets"][index]))
                print(f"OFFSET_DIAGNOSTIC {frame}: {sorted(differences, reverse=True)[:3]}", flush=True)
                captures.append(kimodo.capture_pose(
                    "kimodo_pose:motion", frame_index=frame - 296, bone_offset_tolerance=0.001))
            self.assertEqual([0, 127, 352], [value["frame_indices"][0] for value in captures])
            self.assertNotEqual(captures[0]["local_joints_rot"], captures[1]["local_joints_rot"])
            print("KIMODO_CAPTURE_OK: live HumanIK poses at 296, 423, 648", flush=True)
            from gt.tools.batch_processor.tasks.task_kimodo_definition import TaskKimodoDefinition
            from gt.tools.batch_processor.tasks.task_kimodo_generate import TaskKimodoGenerate
            from gt.tools.batch_processor.batch_processor_task_base import WorkItem
            from gt.tools.batch_processor.tasks.task_kimodo_base import read_json

            output = tempfile.mkdtemp(prefix="gt_kimodo_batch_smoke_")
            capture_task = TaskKimodoDefinition(settings={"use_marker": True})
            definitions = capture_task.execute(WorkItem(scene), None, os.path.join(output, "definitions"))
            definition = read_json(definitions[0].current_path)
            self.assertEqual([0, 127, 352], [entry["frame_indices"][0] for entry in definition["constraints"]])
            self.assertEqual(353, int(definition["prompts"][0]["duration_seconds"] * 30))
            print(f"KIMODO_DEFINITION_OK: {definitions[0].current_path}", flush=True)
            if os.environ.get("GT_KIMODO_RUN_GENERATION") == "1":
                generate_task = TaskKimodoGenerate()
                outputs = generate_task.execute(definitions[0], None, os.path.join(output, "animations"))
                self.assertEqual(1, len(outputs))
                cmds.file(outputs[0].current_path, open=True, force=True, executeScriptNodes=False)
                self.assertEqual(77, len(cmds.ls(type="joint")))
                self.assertEqual(1, len(cmds.ls(type="HIKCharacterNode")))
                self.assertEqual(353, int(cmds.playbackOptions(query=True, maxTime=True)))
                self.assertGreater(cmds.keyframe("kimodo:Hips", query=True, keyframeCount=True), 0)
                print(f"KIMODO_GENERATION_OK: {outputs[0].current_path}", flush=True)
        finally:
            cmds.file(new=True, force=True)
            maya.standalone.uninitialize()


class TestKimodoAnimatedRootPath(unittest.TestCase):
    """Captures an animated trajectory driver through the definition task's scene capture."""

    @classmethod
    def setUpClass(cls):
        """Initializes standalone only when no Maya session already exists."""
        try:
            import maya.standalone
        except ImportError:
            raise unittest.SkipTest("Requires mayapy.")
        try:
            maya.standalone.initialize(name="python")
        except RuntimeError:
            raise unittest.SkipTest("Run in a fresh mayapy process to protect the current scene.")
        cls.standalone = maya.standalone

    @classmethod
    def tearDownClass(cls):
        """Releases the standalone session owned by this test class."""
        cls.standalone.uninitialize()

    def test_animated_driver_samples_position_and_heading(self):
        """Samples a keyed locator over the playback range with node headings and a backward offset."""
        import maya.cmds as cmds
        from gt.tools.batch_processor.tasks.task_kimodo_definition import TaskKimodoDefinition, capture_scene

        cmds.file(new=True, force=True)
        cmds.currentUnit(linear="cm", time="ntsc", angle="deg")
        driver = cmds.spaceLocator(name="kimodo_trajectory")[0]
        cmds.setKeyframe(driver, attribute="translateZ", time=1, value=0)
        cmds.setKeyframe(driver, attribute="translateZ", time=31, value=100)
        cmds.setKeyframe(driver, attribute="rotateY", time=1, value=0)
        cmds.setKeyframe(driver, attribute="rotateY", time=31, value=90)
        cmds.playbackOptions(minTime=1, maxTime=31)
        settings = TaskKimodoDefinition().get_default_settings()
        settings.update(path_nodes="kimodo_trajectory", path_samples=4, root_heading="node",
                        root_heading_offset=180.0, capture_first=False, capture_last=False)
        captured = capture_scene(settings, lambda message: None)
        self.assertEqual([1, 11, 21, 31], captured["path_frames"])
        self.assertAlmostEqual(1.0, captured["path"]["smooth_root_2d"][-1][1], places=6)
        self.assertAlmostEqual(-1.0, captured["path"]["global_root_heading"][0][0], places=6)
        self.assertAlmostEqual(-1.0, captured["path"]["global_root_heading"][-1][1], places=6)


if __name__ == "__main__":
    unittest.main()
