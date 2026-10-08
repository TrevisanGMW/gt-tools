"""Disposable mayapy integration tests; never mutate an existing Maya session."""

import os
import tempfile
import unittest
from unittest.mock import patch

from gt.utils import kimodo
from test_kimodo import sample_motion


class TestKimodoMaya(unittest.TestCase):
    """Verifies skeleton construction, timing, and scene-state preservation."""

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

    def setUp(self):
        """Creates a disposable scene and motion file."""
        import maya.cmds as cmds

        cmds.file(new=True, force=True)
        cmds.currentUnit(linear="cm", time="film", angle="deg")
        cmds.upAxis(axis="y", rotateView=False)
        self.temporary = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.temporary.name, "motion.json")
        kimodo._write_json(self.path, sample_motion())

    def tearDown(self):
        """Removes temporary test artifacts."""
        self.temporary.cleanup()

    def test_import_timing_and_world_positions(self):
        """Matches a known rotation and meters-to-centimeters conversion at 24 FPS."""
        import maya.cmds as cmds

        selected = cmds.createNode("transform", name="existing_selection")
        cmds.select(selected)
        cmds.currentTime(12)
        original_range = (cmds.playbackOptions(query=True, min=True), cmds.playbackOptions(query=True, max=True))
        result = kimodo.import_motion(self.path, start_frame=10)
        self.assertEqual(77, len(result["joints"]))
        self.assertEqual([selected], cmds.ls(selection=True))
        self.assertEqual(12, cmds.currentTime(query=True))
        self.assertEqual("film", cmds.currentUnit(query=True, time=True))
        self.assertEqual(original_range, (cmds.playbackOptions(query=True, min=True),
                                          cmds.playbackOptions(query=True, max=True)))
        self.assertAlmostEqual(10.8, result["end_frame"])
        self.assertEqual([10.0, 10.8], cmds.keyframe(result["joints"][0], attribute="translateZ",
                                                  query=True, timeChange=True))
        cmds.currentTime(10)
        self.assertEqual([100.0, 100.0, 0.0], cmds.xform(result["joints"][1], query=True,
                                                       worldSpace=True, translation=True))
        cmds.currentTime(10.8)
        position = cmds.xform(result["joints"][1], query=True, worldSpace=True, translation=True)
        for expected, actual in zip([0, 200, 100], position):
            self.assertAlmostEqual(expected, actual, places=5)

    def test_z_up_meters_and_namespace_collision(self):
        """Converts the placement group without changing axes or overwriting nodes."""
        import maya.cmds as cmds

        cmds.currentUnit(linear="m")
        cmds.upAxis(axis="z", rotateView=False)
        result = kimodo.import_motion(self.path)
        cmds.currentTime(1)
        position = cmds.xform(result["joints"][1], query=True, worldSpace=True, translation=True)
        for expected, actual in zip([1, 0, 1], position):
            self.assertAlmostEqual(expected, actual, places=5)
        before = cmds.ls(long=True)
        with self.assertRaises(ValueError):
            kimodo.import_motion(self.path)
        self.assertEqual(before, cmds.ls(long=True))
        self.assertEqual("z", cmds.upAxis(query=True, axis=True))
        self.assertEqual("m", cmds.currentUnit(query=True, linear=True))

    def test_invalid_motion_leaves_scene_untouched(self):
        """Completes validation before creating any Maya nodes."""
        import maya.cmds as cmds

        invalid = sample_motion()
        invalid["root_positions"][0][1] = "invalid"
        kimodo._write_json(self.path, invalid)
        before = cmds.ls(long=True)
        with self.assertRaises(ValueError):
            kimodo.import_motion(self.path)
        self.assertEqual(before, cmds.ls(long=True))

    def test_nonroot_namespace_and_failed_import_cleanup(self):
        """Restores namespace and selection even when key creation fails."""
        import maya.cmds as cmds

        cmds.namespace(add="working")
        cmds.namespace(setNamespace=":working")
        selected = cmds.createNode("transform", name="keep")
        cmds.select(selected)
        with patch.object(cmds, "setKeyframe", side_effect=RuntimeError("Test key failure")):
            with self.assertRaisesRegex(RuntimeError, "Test key failure"):
                kimodo.import_motion(self.path)
        self.assertFalse(cmds.namespace(exists=":kimodo"))
        self.assertEqual(":working", cmds.namespaceInfo(currentNamespace=True, absoluteName=True))
        self.assertEqual([selected], cmds.ls(selection=True))
        result = kimodo.import_motion(self.path)
        self.assertEqual(77, len(result["joints"]))
        self.assertEqual(":working", cmds.namespaceInfo(currentNamespace=True, absoluteName=True))

    def test_pose_capture_ignores_placement_and_preserves_rotations(self):
        """Captures local pose values with a transformed placement group."""
        import maya.cmds as cmds

        result = kimodo.import_motion(self.path)
        cmds.currentTime(1.8)
        cmds.setAttr(f"{result['group']}.translateX", 500)
        constraint = kimodo.capture_pose(result["group"], frame_index=29)
        self.assertEqual([29], constraint["frame_indices"])
        for expected, actual in zip([0, 1, 1], constraint["root_positions"][0]):
            self.assertAlmostEqual(expected, actual, places=5)
        preview = kimodo.preview_pose(constraint, sample_motion(), namespace="preview")
        self.assertEqual(77, len(preview["joints"]))

    def test_hips_capture_is_a_pelvis_end_effector(self):
        """Stores hips-only captures as native end-effector constraints with the full pose data."""
        import maya.cmds as cmds

        result = kimodo.import_motion(self.path)
        cmds.currentTime(1.8)
        full_body = kimodo.capture_pose(result["group"], frame_index=29)
        hips = kimodo.capture_pose(result["group"], frame_index=29, constraint_type="hips")
        self.assertEqual("end-effector", hips["type"])
        self.assertEqual(["Hips"], hips["joint_names"])
        self.assertEqual(full_body["root_positions"], hips["root_positions"])
        self.assertEqual(full_body["local_joints_rot"], hips["local_joints_rot"])

    def test_root_path_capture_transforms_world_to_generation_space(self):
        """Captures explicit locator timing in the selected skeleton's local space."""
        import maya.cmds as cmds

        result = kimodo.import_motion(self.path)
        cmds.setAttr(f"{result['group']}.translateX", 500)
        first = cmds.spaceLocator()[0]
        second = cmds.spaceLocator()[0]
        cmds.setAttr(f"{first}.translate", 500, 0, 0)
        cmds.setAttr(f"{second}.translate", 600, 0, 200)
        constraint = kimodo.capture_root_path([first, second], [0, 29], result["group"])
        self.assertEqual([[0, 0], [1, 2]], constraint["smooth_root_2d"])
        self.assertNotIn("global_root_heading", constraint)

    def test_root_path_node_heading_uses_transform_z_axis(self):
        """Encodes each locator's world +Z axis, including the backward offset."""
        import maya.cmds as cmds

        first = cmds.spaceLocator()[0]
        second = cmds.spaceLocator()[0]
        cmds.setAttr(f"{second}.translateZ", 100)
        cmds.setAttr(f"{second}.rotateY", 90)
        constraint = kimodo.capture_root_path([first, second], [0, 29], heading_mode="node")
        for expected, actual in zip([1, 0, 0, 1], sum(constraint["global_root_heading"], [])):
            self.assertAlmostEqual(expected, actual, places=6)
        constraint = kimodo.capture_root_path([first, second], [0, 29], heading_mode="node", heading_offset=180)
        self.assertAlmostEqual(-1, constraint["global_root_heading"][0][0], places=6)

    def test_root_path_curve_heading_follows_tangent(self):
        """Faces along a straight curve drawn toward +X."""
        import maya.cmds as cmds

        curve = cmds.curve(point=[(0, 0, 0), (100, 0, 0), (200, 0, 0)], degree=1)
        constraint = kimodo.capture_root_path([curve], [0, 10, 20], heading_mode="path")
        for cosine, sine in constraint["global_root_heading"]:
            self.assertAlmostEqual(0, cosine, places=6)
            self.assertAlmostEqual(1, sine, places=6)

    def test_root_path_samples_animated_transform_over_time(self):
        """Samples keyed travel and rotation without changing the current time."""
        import maya.cmds as cmds

        driver = cmds.spaceLocator(name="trajectory_driver")[0]
        cmds.setKeyframe(driver, attribute="translateZ", time=1, value=0)
        cmds.setKeyframe(driver, attribute="translateZ", time=11, value=100)
        cmds.setKeyframe(driver, attribute="rotateY", time=1, value=0)
        cmds.setKeyframe(driver, attribute="rotateY", time=11, value=90)
        cmds.currentTime(5)
        constraint = kimodo.capture_root_path([driver], [0, 1, 2], heading_mode="node", sample_times=[1, 6, 11])
        self.assertEqual(5, cmds.currentTime(query=True))
        self.assertAlmostEqual(0, constraint["smooth_root_2d"][0][1], places=6)
        self.assertAlmostEqual(1, constraint["smooth_root_2d"][2][1], places=6)
        self.assertAlmostEqual(1, constraint["global_root_heading"][2][1], places=6)
        travel = kimodo.capture_root_path([driver], [0, 1, 2], heading_mode="path", sample_times=[1, 6, 11])
        self.assertAlmostEqual(1, travel["global_root_heading"][0][0], places=6)
        with self.assertRaises(ValueError):
            kimodo.capture_root_path([driver], [0, 1], sample_times=[1])

    @unittest.skipUnless(os.environ.get("GT_KIMODO_TEST_MOTION"), "No generated sample supplied.")
    def test_real_generation_matches_native_npz(self):
        """Compares every imported joint at three sample times with Kimodo's output."""
        import maya.cmds as cmds
        import numpy as np

        path = os.environ["GT_KIMODO_TEST_MOTION"]
        motion = kimodo._read_json(path)
        with np.load(os.path.join(os.path.dirname(path), "motion.npz"), allow_pickle=False) as archive:
            positions = archive["posed_joints"]
        result = kimodo.import_motion(path, namespace="generated", start_frame=1)
        maximum_error = 0.0
        for frame_index in (0, motion["frame_count"] // 2, motion["frame_count"] - 1):
            cmds.currentTime(1 + frame_index * 24.0 / motion["fps"])
            for joint_index, joint in enumerate(result["joints"]):
                actual = cmds.xform(joint, query=True, worldSpace=True, translation=True)
                for expected_value, actual_value in zip(positions[frame_index, joint_index] * 100, actual):
                    maximum_error = max(maximum_error, abs(float(expected_value) - actual_value))
        print(f"Kimodo native-output comparison: maximum joint-position error {maximum_error:.6f} cm")
        self.assertLess(maximum_error, 0.01)
        scene_path = os.path.join(self.temporary.name, "generated.ma")
        requested_output = os.environ.get("GT_KIMODO_TEST_SCENE")
        if requested_output:
            if os.path.exists(requested_output):
                self.fail("Refusing to overwrite an existing test scene.")
            scene_path = requested_output
        cmds.file(rename=scene_path)
        cmds.file(save=True, type="mayaAscii")


if __name__ == "__main__":
    unittest.main()
