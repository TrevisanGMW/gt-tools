import json
import os
import sys
import tempfile
import unittest

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)

from gt.tests import maya_test_tools
from gt.utils import hik as utils_hik

cmds = maya_test_tools.cmds


class TestHikUtils(unittest.TestCase):
    """Tests HumanIK generated control-rig pose utilities."""

    CONTROL_IDS = [
        "Reference",
        "Hips",
        "LeftArm",
        "RightArm",
        "LeftHandExtraFinger1",
        "RightHandExtraFinger1",
        "LeftFootExtraFinger1",
        "RightFootExtraFinger1",
    ]

    @classmethod
    def setUpClass(cls):
        """Initializes Maya standalone and loads the HumanIK plug-in."""
        maya_test_tools.import_maya_standalone(initialize=True)
        if not cmds.pluginInfo("mayaHIK", query=True, loaded=True):
            cmds.loadPlugin("mayaHIK")

    @classmethod
    def tearDownClass(cls):
        """Clears test nodes before unloading the HumanIK plug-in."""
        maya_test_tools.force_new_scene()
        if cmds.pluginInfo("mayaHIK", query=True, loaded=True):
            cmds.unloadPlugin("mayaHIK")

    def setUp(self):
        """Creates a small namespaced HumanIK control graph for each test."""
        maya_test_tools.force_new_scene()
        cmds.namespace(add="hero")
        self.character = cmds.createNode("HIKCharacterNode", name="hero:Character")
        self.control_rig = cmds.createNode("HIKControlSetNode", name="hero:Character_ControlRig")
        cmds.connectAttr(
            f"{self.character}.OutputCharacterDefinition",
            f"{self.control_rig}.InputCharacterDefinition",
        )

        self.controls = {}
        for control_id in self.CONTROL_IDS:
            control = cmds.createNode("transform", name=f"hero:Character_Ctrl_{control_id}")
            cmds.addAttr(control, longName="ControlSet", attributeType="message")
            cmds.addAttr(control, longName="poseValue", attributeType="double", keyable=True)
            cmds.connectAttr(
                f"{control}.ControlSet",
                f"{self.control_rig}.{control_id}",
                force=True,
            )
            self.controls[control_id] = control

        reference = self.controls["Reference"]
        for control_id, control in self.controls.items():
            if control_id != "Reference":
                cmds.parent(control, reference)

    def assert_matrix_almost_equal(self, expected, result, places=6):
        """Asserts that two flat Maya matrices are almost equal.

        Args:
            expected (list): Expected 16-value matrix.
            result (list): Actual 16-value matrix.
            places (int): Decimal precision used for comparisons.
        """
        self.assertEqual(len(expected), len(result))
        for expected_value, result_value in zip(expected, result):
            self.assertAlmostEqual(expected_value, result_value, places=places)

    def assert_values_almost_equal(self, expected, result, places=6):
        """Asserts that two numeric sequences are almost equal.

        Args:
            expected (list or tuple): Expected numeric values.
            result (list or tuple): Actual numeric values.
            places (int): Decimal precision used for comparisons.
        """
        self.assertEqual(len(expected), len(result))
        for expected_value, result_value in zip(expected, result):
            self.assertAlmostEqual(expected_value, result_value, places=places)

    def get_matrix(self, control_id, world_space=False):
        """Gets a test control matrix.

        Args:
            control_id (str): Stable test control identifier.
            world_space (bool): Whether to query the world matrix.

        Returns:
            list: Flat 16-value Maya matrix.
        """
        control = self.controls[control_id]
        if world_space:
            return cmds.xform(control, query=True, matrix=True, worldSpace=True)
        return cmds.xform(control, query=True, matrix=True, objectSpace=True)

    def add_hik_control(self, control_id, node_type):
        """Adds a connected native HumanIK control to the test rig.

        Args:
            control_id (str): HumanIK control-set attribute identifier.
            node_type (str): Maya node type used for the generated control.

        Returns:
            str: Created HumanIK control node.
        """
        name_suffix = control_id.partition("[")[0]
        control = cmds.createNode(node_type, name=f"hero:Character_Ctrl_{name_suffix}")
        if not cmds.attributeQuery("ControlSet", node=control, exists=True):
            cmds.addAttr(control, longName="ControlSet", attributeType="message")
        cmds.connectAttr(
            f"{control}.ControlSet",
            f"{self.control_rig}.{control_id}",
            force=True,
        )
        cmds.parent(control, self.controls["Reference"])
        self.controls[control_id] = control
        return control

    def test_get_hik_control_rig_controls_finds_namespaced_controls(self):
        """Finds connected controls when given an unqualified unique name."""
        expected = {cmds.ls(control, long=True)[0] for control in self.controls.values()}
        result = set(utils_hik.get_hik_control_rig_controls("Character"))
        self.assertEqual(expected, result)

    def test_get_hik_control_rig_controls_uses_generated_name_fallback(self):
        """Includes generated controls that are missing control-set connections."""
        extra_control = cmds.createNode(
            "transform",
            name="hero:Character_Ctrl_LeftCustomToe",
        )
        expected = cmds.ls(extra_control, long=True)[0]
        result = utils_hik.get_hik_control_rig_controls(self.character)
        self.assertIn(expected, result)

    def test_get_hik_control_map_does_not_duplicate_array_effectors(self):
        """Uses a connected effector ID instead of adding its generated-name alias."""
        effector = cmds.createNode(
            "transform",
            name="hero:Character_Ctrl_LeftWristEffector",
        )
        cmds.addAttr(effector, longName="ControlSet", attributeType="message")
        cmds.connectAttr(
            f"{effector}.ControlSet",
            f"{self.control_rig}.LeftWristEffector[0]",
            force=True,
        )

        result = utils_hik._get_hik_control_map(self.character)

        self.assertIn("LeftWristEffector[0]", result)
        self.assertNotIn("LeftWristEffector", result)

    def test_mirror_hik_pose_uses_stable_channels_for_foot_and_ankle(self):
        """Avoids unstable matrix decomposition on generated lower-limb controls."""
        left_foot = self.add_hik_control("LeftFoot", "hikFKJoint")
        right_foot = self.add_hik_control("RightFoot", "hikFKJoint")
        left_ankle = self.add_hik_control("LeftAnkleEffector[0]", "hikIKEffector")
        right_ankle = self.add_hik_control("RightAnkleEffector[0]", "hikIKEffector")
        for control in [left_foot, right_foot, left_ankle, right_ankle]:
            cmds.setAttr(
                f"{control}.jointOrient",
                -90,
                -63.43494882292201,
                -90,
            )

        cmds.setAttr(f"{self.controls['Reference']}.translateX", 10)
        cmds.setAttr(f"{left_foot}.rotate", 20, 30, 40)
        cmds.setAttr(f"{left_ankle}.translate", 2, 3, 4)
        cmds.setAttr(f"{left_ankle}.rotate", 10, 25, 35)
        utils_hik.mirror_hik_pose(self.character, source_side="left", world_space=False)

        self.assert_values_almost_equal(
            (-20, -30, 40),
            cmds.getAttr(f"{right_foot}.rotate")[0],
        )
        self.assert_values_almost_equal(
            (-2, 3, 4),
            cmds.getAttr(f"{right_ankle}.translate")[0],
        )
        self.assert_values_almost_equal(
            (-10, -25, 35),
            cmds.getAttr(f"{right_ankle}.rotate")[0],
        )
        cmds.setAttr(f"{right_ankle}.translate", 0, 0, 0)
        cmds.setAttr(f"{right_ankle}.rotate", 0, 0, 0)
        utils_hik.mirror_hik_pose(self.character, source_side="left", world_space=True)
        self.assert_values_almost_equal(
            (-2, 3, 4),
            cmds.getAttr(f"{right_ankle}.translate")[0],
        )
        self.assert_values_almost_equal(
            (-10, -25, 35),
            cmds.getAttr(f"{right_ankle}.rotate")[0],
        )
        world_translation = cmds.xform(
            right_ankle,
            query=True,
            translation=True,
            worldSpace=True,
        )
        self.assertAlmostEqual(8, world_translation[0])

    def test_mirror_hik_pose_copies_left_side_and_extra_digits(self):
        """Mirrors left controls, extra fingers, and extra toes onto the right."""
        source_ids = ["LeftArm", "LeftHandExtraFinger1", "LeftFootExtraFinger1"]
        cmds.addAttr(self.controls["LeftArm"], longName="reachTranslation", attributeType="double")
        cmds.addAttr(self.controls["RightArm"], longName="reachTranslation", attributeType="double")
        cmds.setAttr(f"{self.controls['LeftArm']}.reachTranslation", 0.75)
        for index, control_id in enumerate(source_ids, start=1):
            cmds.setAttr(f"{self.controls[control_id]}.translate", index, index + 1, index + 2)
            cmds.setAttr(f"{self.controls[control_id]}.rotate", index * 10, index * 20, index * 30)
            cmds.setAttr(f"{self.controls[control_id]}.poseValue", index * 2)

        expected_matrices = {
            control_id.replace("Left", "Right", 1): utils_hik._mirror_transform_matrix(
                self.get_matrix(control_id)
            )
            for control_id in source_ids
        }
        cmds.setAttr(f"{self.controls['Hips']}.translateX", 4)

        result = utils_hik.mirror_hik_pose(
            self.character,
            source_side="left",
            affect_center=False,
            world_space=False,
        )

        for source_id in source_ids:
            target_id = source_id.replace("Left", "Right", 1)
            self.assert_matrix_almost_equal(expected_matrices[target_id], self.get_matrix(target_id))
            expected_value = cmds.getAttr(f"{self.controls[source_id]}.poseValue")
            result_value = cmds.getAttr(f"{self.controls[target_id]}.poseValue")
            self.assertEqual(expected_value, result_value)
        self.assertEqual(0.75, cmds.getAttr(f"{self.controls['RightArm']}.reachTranslation"))
        self.assertEqual(4, cmds.getAttr(f"{self.controls['Hips']}.translateX"))
        self.assertEqual(3, len(result))

    def test_mirror_hik_pose_can_affect_center_controls(self):
        """Mirrors center controls in place only when explicitly requested."""
        cmds.setAttr(f"{self.controls['Hips']}.translateX", 4)
        result = utils_hik.mirror_hik_pose(
            self.character,
            source_side="left",
            affect_center=True,
            world_space=False,
        )
        self.assertEqual(-4, cmds.getAttr(f"{self.controls['Hips']}.translateX"))
        self.assertIn(cmds.ls(self.controls["Hips"], long=True)[0], result)

    def test_flip_hik_pose_swaps_both_sides(self):
        """Swaps both sides from a snapshot so neither side overwrites the other."""
        left_control = self.controls["LeftArm"]
        right_control = self.controls["RightArm"]
        cmds.setAttr(f"{left_control}.translate", 3, 4, 5)
        cmds.setAttr(f"{left_control}.rotate", 10, 20, 30)
        cmds.setAttr(f"{left_control}.poseValue", 7)
        cmds.setAttr(f"{right_control}.translate", -8, 2, 1)
        cmds.setAttr(f"{right_control}.rotate", -5, 15, 25)
        cmds.setAttr(f"{right_control}.poseValue", 11)
        expected_left = utils_hik._mirror_transform_matrix(self.get_matrix("RightArm"))
        expected_right = utils_hik._mirror_transform_matrix(self.get_matrix("LeftArm"))

        utils_hik.flip_hik_pose(self.character, affect_center=False, world_space=False)

        self.assert_matrix_almost_equal(expected_left, self.get_matrix("LeftArm"))
        self.assert_matrix_almost_equal(expected_right, self.get_matrix("RightArm"))
        self.assertEqual(11, cmds.getAttr(f"{left_control}.poseValue"))
        self.assertEqual(7, cmds.getAttr(f"{right_control}.poseValue"))

    def test_flip_hik_pose_uses_stable_channels_for_feet(self):
        """Flips generated feet without matrix-to-Euler decomposition artifacts."""
        left_foot = self.add_hik_control("LeftFoot", "hikFKJoint")
        right_foot = self.add_hik_control("RightFoot", "hikFKJoint")
        for control in [left_foot, right_foot]:
            cmds.setAttr(
                f"{control}.jointOrient",
                -90,
                -63.43494882292201,
                -90,
            )
        cmds.setAttr(f"{left_foot}.rotate", 20, 30, 40)
        cmds.setAttr(f"{right_foot}.rotate", -5, 15, 25)

        utils_hik.flip_hik_pose(self.character, affect_center=False, world_space=False)

        self.assert_values_almost_equal(
            (5, -15, 25),
            cmds.getAttr(f"{left_foot}.rotate")[0],
        )
        self.assert_values_almost_equal(
            (-20, -30, 40),
            cmds.getAttr(f"{right_foot}.rotate")[0],
        )

    def test_mirror_hik_pose_world_space_uses_reference_plane(self):
        """Mirrors world transforms around the character Reference control."""
        cmds.setAttr(f"{self.controls['Reference']}.translateX", 10)
        cmds.setAttr(f"{self.controls['LeftArm']}.translateX", 2)

        utils_hik.mirror_hik_pose(
            self.character,
            source_side="left",
            affect_center=False,
            world_space=True,
        )

        result = cmds.xform(
            self.controls["RightArm"],
            query=True,
            translation=True,
            worldSpace=True,
        )
        self.assertAlmostEqual(8, result[0])

    def test_export_and_import_hik_pose_preserves_stable_control_ids(self):
        """Round-trips a namespaced pose without storing scene control names."""
        left_control = self.controls["LeftArm"]
        cmds.setAttr(f"{left_control}.translate", 3, 4, 5)
        cmds.setAttr(f"{left_control}.rotate", 10, 20, 30)
        cmds.setAttr(f"{left_control}.poseValue", 9)
        expected_matrix = self.get_matrix("LeftArm")

        with tempfile.TemporaryDirectory() as temp_directory:
            pose_path = os.path.join(temp_directory, "test_hik.pose")
            result = utils_hik.export_hik_pose(
                self.character,
                pose_path,
                world_space=False,
            )
            self.assertTrue(result)
            with open(pose_path, "r", encoding="utf-8") as pose_file:
                pose_data = json.load(pose_file)

            self.assertEqual(utils_hik.HIK_POSE_FILE_FORMAT, pose_data.get("format"))
            self.assertIn("LeftHandExtraFinger1", pose_data.get("controls"))
            self.assertNotIn("hero:Character_Ctrl_LeftArm", pose_data.get("controls"))

            cmds.setAttr(f"{left_control}.translate", 0, 0, 0)
            cmds.setAttr(f"{left_control}.rotate", 0, 0, 0)
            cmds.setAttr(f"{left_control}.poseValue", 0)
            applied_controls = utils_hik.import_hik_pose(self.character, pose_path)

        self.assertIn(cmds.ls(left_control, long=True)[0], applied_controls)
        self.assert_matrix_almost_equal(expected_matrix, self.get_matrix("LeftArm"))
        self.assertEqual(9, cmds.getAttr(f"{left_control}.poseValue"))

    def test_mirror_hik_pose_rejects_invalid_source_side(self):
        """Rejects unsupported side labels instead of guessing intent."""
        with self.assertRaises(ValueError):
            utils_hik.mirror_hik_pose(self.character, source_side="center")


if __name__ == "__main__":
    unittest.main()
