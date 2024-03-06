import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from tests import maya_test_tools
from gt.utils import joint_utils
cmds = maya_test_tools.cmds


class TestJointUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def assertAlmostEqualSigFig(self, arg1, arg2, tolerance=2):
        """
        Asserts that two numbers are almost equal up to a given number of significant figures.

        Args:
            self (object): The current test case or class object.
            arg1 (float): The first number for comparison.
            arg2 (float): The second number for comparison.
            tolerance (int, optional): The number of significant figures to consider for comparison. Default is 2.

        Returns:
            None

        Raises:
            AssertionError: If the significands of arg1 and arg2 differ by more than the specified tolerance.

        Example:
            obj = TestClass()
            obj.assertAlmostEqualSigFig(3.145, 3.14159, tolerance=3)
            # No assertion error will be raised as the first 3 significant figures are equal (3.14)
        """
        if tolerance > 1:
            tolerance = tolerance - 1

        str_formatter = '{0:.' + str(tolerance) + 'e}'
        significand_1 = float(str_formatter.format(arg1).split('e')[0])
        significand_2 = float(str_formatter.format(arg2).split('e')[0])

        exponent_1 = int(str_formatter.format(arg1).split('e')[1])
        exponent_2 = int(str_formatter.format(arg2).split('e')[1])

        self.assertEqual(significand_1, significand_2)
        self.assertEqual(exponent_1, exponent_2)

    def test_orient_joint(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")
        cmds.select(clear=True)
        joint_three = cmds.joint(name="three_jnt")
        cmds.setAttr(f'{joint_two}.tx', 3)
        cmds.setAttr(f'{joint_two}.tz', -3)
        cmds.setAttr(f'{joint_three}.tx', 6)
        cmds.setAttr(f'{joint_three}.tz', -6)
        cmds.parent(joint_two, joint_one)
        cmds.parent(joint_three, joint_two)
        joints = [joint_one, joint_two, joint_three]

        joint_utils.orient_joint(joint_list=joints,
                                 aim_axis=(1, 0, 0),
                                 up_axis=(0, 1, 0),
                                 up_dir=(0, 1, 0))

        one_x = cmds.getAttr(f'{joint_one}.jointOrientX')
        one_y = cmds.getAttr(f'{joint_one}.jointOrientY')
        one_z = cmds.getAttr(f'{joint_one}.jointOrientZ')
        self.assertAlmostEqualSigFig(0, one_x, tolerance=3)
        self.assertAlmostEqualSigFig(45, one_y, tolerance=3)
        self.assertAlmostEqualSigFig(0, one_z, tolerance=3)
        for jnt in [joint_two, joint_three]:
            jnt_x = cmds.getAttr(f'{jnt}.jointOrientX')
            jnt_y = cmds.getAttr(f'{jnt}.jointOrientY')
            jnt_z = cmds.getAttr(f'{jnt}.jointOrientZ')
            self.assertAlmostEqualSigFig(0, jnt_x, tolerance=3)
            self.assertAlmostEqualSigFig(0, jnt_y, tolerance=3)
            self.assertAlmostEqualSigFig(0, jnt_z, tolerance=3)

    def test_orient_joint_aim_z(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")
        cmds.select(clear=True)
        joint_three = cmds.joint(name="three_jnt")
        cmds.setAttr(f'{joint_two}.tx', 3)
        cmds.setAttr(f'{joint_two}.tz', -3)
        cmds.setAttr(f'{joint_three}.tx', 6)
        cmds.setAttr(f'{joint_three}.tz', -6)
        cmds.parent(joint_two, joint_one)
        cmds.parent(joint_three, joint_two)
        joints = [joint_one, joint_two, joint_three]

        joint_utils.orient_joint(joint_list=joints,
                                 aim_axis=(0, 0, 1),
                                 up_axis=(0, 1, 0),
                                 up_dir=(0, 1, 0))

        one_x = cmds.getAttr(f'{joint_one}.jointOrientX')
        one_y = cmds.getAttr(f'{joint_one}.jointOrientY')
        one_z = cmds.getAttr(f'{joint_one}.jointOrientZ')
        self.assertAlmostEqualSigFig(0, one_x, tolerance=3)
        self.assertAlmostEqualSigFig(135, one_y, tolerance=3)
        self.assertAlmostEqualSigFig(0, one_z, tolerance=3)
        for jnt in [joint_two, joint_three]:
            jnt_x = cmds.getAttr(f'{jnt}.jointOrientX')
            jnt_y = cmds.getAttr(f'{jnt}.jointOrientY')
            jnt_z = cmds.getAttr(f'{jnt}.jointOrientZ')
            self.assertAlmostEqualSigFig(0, jnt_x, tolerance=3)
            self.assertAlmostEqualSigFig(0, jnt_y, tolerance=3)
            self.assertAlmostEqualSigFig(0, jnt_z, tolerance=3)

    def test_orient_joint_aim_z_up_x(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")
        cmds.select(clear=True)
        joint_three = cmds.joint(name="three_jnt")
        cmds.setAttr(f'{joint_two}.tx', 3)
        cmds.setAttr(f'{joint_two}.tz', -3)
        cmds.setAttr(f'{joint_three}.tx', 6)
        cmds.setAttr(f'{joint_three}.tz', -6)
        cmds.parent(joint_two, joint_one)
        cmds.parent(joint_three, joint_two)
        joints = [joint_one, joint_two, joint_three]

        joint_utils.orient_joint(joint_list=joints,
                                 aim_axis=(0, 0, 1),
                                 up_axis=(1, 0, 0),
                                 up_dir=(0, 1, 0))

        one_x = cmds.getAttr(f'{joint_one}.jointOrientX')
        one_y = cmds.getAttr(f'{joint_one}.jointOrientY')
        one_z = cmds.getAttr(f'{joint_one}.jointOrientZ')
        self.assertAlmostEqualSigFig(135, round(one_x, 3), tolerance=4)
        self.assertAlmostEqualSigFig(0, round(one_y, 3), tolerance=3)
        self.assertAlmostEqualSigFig(90, round(one_z, 3), tolerance=4)
        for jnt in [joint_two, joint_three]:
            jnt_x = cmds.getAttr(f'{jnt}.jointOrientX')
            jnt_y = cmds.getAttr(f'{jnt}.jointOrientY')
            jnt_z = cmds.getAttr(f'{jnt}.jointOrientZ')
            self.assertAlmostEqualSigFig(0, jnt_x, tolerance=3)
            self.assertAlmostEqualSigFig(0, jnt_y, tolerance=3)
            self.assertAlmostEqualSigFig(0, jnt_z, tolerance=3)

    def test_orient_joint_aim_x_negative(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")
        cmds.select(clear=True)
        joint_three = cmds.joint(name="three_jnt")
        cmds.setAttr(f'{joint_two}.tx', 3)
        cmds.setAttr(f'{joint_two}.tz', -3)
        cmds.setAttr(f'{joint_three}.tx', 6)
        cmds.setAttr(f'{joint_three}.tz', -6)
        cmds.parent(joint_two, joint_one)
        cmds.parent(joint_three, joint_two)
        joints = [joint_one, joint_two, joint_three]

        joint_utils.orient_joint(joint_list=joints,
                                 aim_axis=(-1, 0, 0),
                                 up_axis=(0, 1, 0),
                                 up_dir=(0, 1, 0))

        one_x = cmds.getAttr(f'{joint_one}.jointOrientX')
        one_y = cmds.getAttr(f'{joint_one}.jointOrientY')
        one_z = cmds.getAttr(f'{joint_one}.jointOrientZ')
        self.assertAlmostEqualSigFig(0, round(one_x, 3), tolerance=4)
        self.assertAlmostEqualSigFig(225, round(one_y, 3), tolerance=3)
        self.assertAlmostEqualSigFig(0, round(one_z, 3), tolerance=4)
        for jnt in [joint_two, joint_three]:
            jnt_x = cmds.getAttr(f'{jnt}.jointOrientX')
            jnt_y = cmds.getAttr(f'{jnt}.jointOrientY')
            jnt_z = cmds.getAttr(f'{jnt}.jointOrientZ')
            self.assertAlmostEqualSigFig(0, jnt_x, tolerance=3)
            self.assertAlmostEqualSigFig(0, jnt_y, tolerance=3)
            self.assertAlmostEqualSigFig(0, jnt_z, tolerance=3)

    def test_copy_parent_orients(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")
        cmds.select(clear=True)
        joint_three = cmds.joint(name="three_jnt")
        cmds.setAttr(f'{joint_two}.tx', 3)
        cmds.setAttr(f'{joint_two}.tz', -3)
        cmds.setAttr(f'{joint_three}.tx', 6)
        cmds.setAttr(f'{joint_three}.tz', -6)
        cmds.setAttr(f'{joint_one}.jointOrientY', 33)
        cmds.parent(joint_two, joint_one)
        cmds.parent(joint_three, joint_two)

        joint_utils.copy_parent_orients(joint_list=joint_two)

        one_x = cmds.getAttr(f'{joint_one}.jointOrientX')
        one_y = cmds.getAttr(f'{joint_one}.jointOrientY')
        one_z = cmds.getAttr(f'{joint_one}.jointOrientZ')
        self.assertAlmostEqualSigFig(0, one_x, tolerance=3)
        self.assertAlmostEqualSigFig(33, one_y, tolerance=3)
        self.assertAlmostEqualSigFig(0, one_z, tolerance=3)
        two_x = cmds.getAttr(f'{joint_two}.jointOrientX')
        two_y = cmds.getAttr(f'{joint_two}.jointOrientY')
        two_z = cmds.getAttr(f'{joint_two}.jointOrientZ')
        self.assertAlmostEqualSigFig(0, two_x, tolerance=3)
        self.assertAlmostEqualSigFig(0, two_y, tolerance=3)
        self.assertAlmostEqualSigFig(0, two_z, tolerance=3)
        three_x = cmds.getAttr(f'{joint_three}.jointOrientX')
        three_y = cmds.getAttr(f'{joint_three}.jointOrientY')
        three_z = cmds.getAttr(f'{joint_three}.jointOrientZ')
        self.assertAlmostEqualSigFig(0, three_x, tolerance=3)
        self.assertAlmostEqualSigFig(-33, three_y, tolerance=3)
        self.assertAlmostEqualSigFig(0, three_z, tolerance=3)

    def test_reset_orients(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")
        cmds.select(clear=True)
        joint_three = cmds.joint(name="three_jnt")
        cmds.setAttr(f'{joint_two}.tx', 3)
        cmds.setAttr(f'{joint_two}.tz', -3)
        cmds.setAttr(f'{joint_three}.tx', 6)
        cmds.setAttr(f'{joint_three}.tz', -6)
        cmds.setAttr(f'{joint_one}.jointOrientX', 33)
        cmds.setAttr(f'{joint_two}.jointOrientY', 33)
        cmds.setAttr(f'{joint_three}.jointOrientZ', 33)
        cmds.parent(joint_two, joint_one)
        cmds.parent(joint_three, joint_two)

        joint_utils.reset_orients(joint_list=joint_two)

        two_x = cmds.getAttr(f'{joint_two}.jointOrientX')
        two_y = cmds.getAttr(f'{joint_two}.jointOrientY')
        two_z = cmds.getAttr(f'{joint_two}.jointOrientZ')
        self.assertAlmostEqualSigFig(-33, two_x, tolerance=3)
        self.assertAlmostEqualSigFig(0, two_y, tolerance=3)
        self.assertAlmostEqualSigFig(0, two_z, tolerance=3)

        joint_utils.reset_orients(joint_list=joint_one)

        one_x = cmds.getAttr(f'{joint_one}.jointOrientX')
        one_y = cmds.getAttr(f'{joint_one}.jointOrientY')
        one_z = cmds.getAttr(f'{joint_one}.jointOrientZ')
        self.assertAlmostEqualSigFig(0, one_x, tolerance=3)
        self.assertAlmostEqualSigFig(0, one_y, tolerance=3)
        self.assertAlmostEqualSigFig(0, one_z, tolerance=3)
        three_x = cmds.getAttr(f'{joint_three}.jointOrientX')
        three_y = cmds.getAttr(f'{joint_three}.jointOrientY')
        three_z = cmds.getAttr(f'{joint_three}.jointOrientZ')
        self.assertAlmostEqualSigFig(0, three_x, tolerance=3)
        self.assertAlmostEqualSigFig(0, three_y, tolerance=3)
        self.assertAlmostEqualSigFig(33, three_z, tolerance=3)

        joint_utils.reset_orients(joint_list=joint_three)

        three_x = cmds.getAttr(f'{joint_three}.jointOrientX')
        three_y = cmds.getAttr(f'{joint_three}.jointOrientY')
        three_z = cmds.getAttr(f'{joint_three}.jointOrientZ')
        self.assertAlmostEqualSigFig(0, three_x, tolerance=3)
        self.assertAlmostEqualSigFig(0, three_y, tolerance=3)
        self.assertAlmostEqualSigFig(0, three_z, tolerance=3)

    def test_convert_joints_to_mesh_selected_one(self):
        joint = cmds.joint()
        cmds.select(joint)
        result = joint_utils.convert_joints_to_mesh()
        expected = [f'{joint}JointMesh']
        self.assertEqual(expected, result)

    def test_convert_joints_to_mesh_selected_hierarchy(self):
        joint_one = cmds.joint()
        cmds.joint()
        cmds.select(joint_one)
        result = joint_utils.convert_joints_to_mesh()
        expected = [f'{joint_one}AsMesh']
        self.assertEqual(expected, result)

    def test_convert_joints_to_mesh_str_input(self):
        joint_one = cmds.joint()
        result = joint_utils.convert_joints_to_mesh(root_jnt=joint_one)
        expected = [f'{joint_one}JointMesh']
        self.assertEqual(expected, result)

    def test_set_joint_radius(self):
        test_joints = [cmds.joint(p=(0, 10, 0)),
                       cmds.joint(p=(0, 5, .1)),
                       cmds.joint(p=(0, 0, 0))]
        result = joint_utils.set_joint_radius(joints=test_joints, radius=5)
        expected = ["|joint1", "|joint1|joint2", "|joint1|joint2|joint3"]
        self.assertEqual(expected, result)

        expected = 5
        for jnt in result:
            radius = cmds.getAttr(f'{jnt}.radius')
            self.assertEqual(expected, radius)
