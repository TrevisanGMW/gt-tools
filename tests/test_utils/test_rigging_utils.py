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
from gt.utils import rigging_utils


class TestRiggingUtils(unittest.TestCase):
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

    def test_duplicate_joint_for_automation(self):
        joint_one = maya_test_tools.cmds.joint(name="one_jnt")
        maya_test_tools.cmds.select(clear=True)
        maya_test_tools.cmds.joint(name="two_jnt")
        # Before Operation
        expected = ['|one_jnt', '|two_jnt']
        result = maya_test_tools.cmds.ls(typ="joint", long=True)
        self.assertEqual(expected, result)
        # Operation Result
        result = rigging_utils.duplicate_joint_for_automation(joint=joint_one, suffix="mocked",
                                                              parent=None, connect_rot_order=True)
        expected = '|one_jnt_mocked'
        self.assertEqual(expected, result)
        # After Operation
        result = maya_test_tools.cmds.ls(typ="joint", long=True)
        expected = ['|one_jnt', '|one_jnt_mocked', '|two_jnt']
        self.assertEqual(expected, result)

    def test_duplicate_joint_for_automation_parent(self):
        joint_one = maya_test_tools.cmds.joint(name="one_jnt")
        maya_test_tools.cmds.select(clear=True)
        maya_test_tools.cmds.joint(name="two_jnt")
        a_group = maya_test_tools.cmds.group(name="a_group", empty=True, world=True)
        # Before Operation
        result = maya_test_tools.cmds.ls(typ="joint", long=True)
        expected = ['|one_jnt', '|two_jnt']
        self.assertEqual(expected, result)
        # Operation Result
        result = rigging_utils.duplicate_joint_for_automation(joint=joint_one, suffix="mocked",
                                                              parent=a_group, connect_rot_order=True)
        expected = '|a_group|one_jnt_mocked'
        self.assertEqual(expected, result)
        # After Operation
        result = maya_test_tools.cmds.ls(typ="joint", long=True)
        expected = ['|one_jnt', '|a_group|one_jnt_mocked', '|two_jnt']
        self.assertEqual(expected, result)

    def test_duplicate_joint_for_automation_rot_order(self):
        joint_one = maya_test_tools.cmds.joint(name="one_jnt")
        maya_test_tools.cmds.select(clear=True)
        joint_two = maya_test_tools.cmds.joint(name="two_jnt")
        a_group = maya_test_tools.cmds.group(name="a_group", empty=True, world=True)

        expected = ['|one_jnt', '|two_jnt']
        result = maya_test_tools.cmds.ls(typ="joint", long=True)
        self.assertEqual(expected, result)

        jnt_as_node = rigging_utils.duplicate_joint_for_automation(joint=joint_one, suffix="mocked",
                                                                   parent=a_group, connect_rot_order=True)
        expected = ['one_jnt']
        result = maya_test_tools.cmds.listConnections(jnt_as_node)
        self.assertEqual(expected, result)
        jnt_as_node = rigging_utils.duplicate_joint_for_automation(joint=joint_two, suffix="mocked",
                                                                   parent=a_group, connect_rot_order=False)
        expected = None
        result = maya_test_tools.cmds.listConnections(jnt_as_node)
        self.assertEqual(expected, result)

    def test_rescale_joint_radius(self):
        joint_one = maya_test_tools.cmds.joint(name="one_jnt")
        maya_test_tools.cmds.select(clear=True)
        joint_two = maya_test_tools.cmds.joint(name="two_jnt")

        expected = 1
        result = maya_test_tools.cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)

        rigging_utils.rescale_joint_radius(joint_list=joint_one, multiplier=5)

        expected = 5
        result = maya_test_tools.cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)

        rigging_utils.rescale_joint_radius(joint_list=[joint_one, joint_two], multiplier=2)

        expected = 10
        result = maya_test_tools.cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)
        expected = 2
        result = maya_test_tools.cmds.getAttr(f'{joint_two}.radius')
        self.assertEqual(expected, result)

    def test_rescale_joint_radius_initial_value(self):
        joint_one = maya_test_tools.cmds.joint(name="one_jnt")
        maya_test_tools.cmds.select(clear=True)

        expected = 1
        result = maya_test_tools.cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)

        rigging_utils.rescale_joint_radius(joint_list=joint_one, multiplier=2, initial_value=5)

        expected = 10
        result = maya_test_tools.cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)

    def test_expose_rotation_order(self):
        joint_one = maya_test_tools.cmds.joint(name="one_jnt")
        maya_test_tools.cmds.select(clear=True)

        expected = False
        result = maya_test_tools.cmds.objExists(f'{joint_one}.rotationOrder')
        self.assertEqual(expected, result)

        rigging_utils.expose_rotation_order(target=joint_one, attr_enum='xyz:yzx:zxy:xzy:yxz:zyx')

        expected = True
        result = maya_test_tools.cmds.objExists(f'{joint_one}.rotationOrder')
        self.assertEqual(expected, result)

        expected = ['one_jnt.rotationOrder', 'one_jnt']
        result = maya_test_tools.cmds.listConnections(f'{joint_one}.rotationOrder', connections=True)
        self.assertEqual(expected, result)

    def test_offset_control_orientation(self):
        ctrl = maya_test_tools.cmds.curve(point=[[0.0, 0.0, 1.0], [0.0, 0.0, 0.667], [0.0, 0.0, 0.0],
                                                [0.0, 0.0, -1.0], [0.0, 0.0, -1.667], [0.0, 0.0, -2.0]],
                                          degree=3, name='mocked_ctrl')
        control_offset = maya_test_tools.cmds.group(name="offset", empty=True, world=True)
        maya_test_tools.cmds.parent(ctrl, control_offset)
        # Before Offset
        rx = maya_test_tools.cmds.getAttr(f'{control_offset}.rx')
        ry = maya_test_tools.cmds.getAttr(f'{control_offset}.ry')
        rz = maya_test_tools.cmds.getAttr(f'{control_offset}.rz')
        expected_rx = 0
        expected_ry = 0
        expected_rz = 0
        self.assertEqual(expected_rx, rx)
        self.assertEqual(expected_ry, ry)
        self.assertEqual(expected_rz, rz)
        expected = [0.0, 0.0, 1.0]
        result = maya_test_tools.cmds.xform(f'{ctrl}.cv[0]', query=True, worldSpace=True, translation=True)
        self.assertEqual(expected, result)
        # Run Offset
        rigging_utils.offset_control_orientation(ctrl=ctrl,
                                                 offset_transform=control_offset,
                                                 orient_tuple=(90, 0, 0))
        # After Offset
        rx = maya_test_tools.cmds.getAttr(f'{control_offset}.rx')
        ry = maya_test_tools.cmds.getAttr(f'{control_offset}.ry')
        rz = maya_test_tools.cmds.getAttr(f'{control_offset}.rz')
        expected_rx = 90
        expected_ry = 0
        expected_rz = 0
        self.assertEqual(expected_rx, rx)
        self.assertEqual(expected_ry, ry)
        self.assertEqual(expected_rz, rz)
        expected = [0.0, 0.0, 1.0]
        result = maya_test_tools.cmds.xform(f'{ctrl}.cv[0]', query=True, worldSpace=True, translation=True)
        self.assertEqual(expected, result)
