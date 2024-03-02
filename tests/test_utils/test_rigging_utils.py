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

    def test_duplicate_object_children(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        maya_test_tools.cmds.parent(cube_two, cube_one)
        # Duplicate
        duplicated_obj = rigging_utils.duplicate_object(obj=cube_one, name=None,
                                                        parent_to_world=True, reset_attributes=True)
        expected = '|cube_one1'
        self.assertEqual(expected, duplicated_obj)
        # Check Children
        result = maya_test_tools.cmds.listRelatives(cube_one, children=True)
        expected = ['cube_oneShape', 'cube_two']
        self.assertEqual(expected, result)
        result = maya_test_tools.cmds.listRelatives(duplicated_obj, children=True)
        expected = ['cube_one1Shape']
        self.assertEqual(expected, result)

    def test_duplicate_object_naming(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        maya_test_tools.cmds.parent(cube_two, cube_one)
        # Duplicate
        duplicated_obj = rigging_utils.duplicate_object(obj=cube_one, name="mocked_cube",
                                                        parent_to_world=True, reset_attributes=True)
        expected = '|mocked_cube'
        self.assertEqual(expected, duplicated_obj)

    def test_duplicate_object_parenting(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        maya_test_tools.cmds.parent(cube_two, cube_one)
        # Duplicate; World Parenting
        duplicated_obj = rigging_utils.duplicate_object(obj=cube_two, name="world_parent",
                                                        parent_to_world=True, reset_attributes=True)
        expected = '|world_parent'
        self.assertEqual(expected, duplicated_obj)
        # Duplicate; Keep Parent
        duplicated_obj = rigging_utils.duplicate_object(obj=cube_two, name="keep_parent",
                                                        parent_to_world=False, reset_attributes=True)
        expected = '|cube_one|keep_parent'
        self.assertEqual(expected, duplicated_obj)

    def test_duplicate_object_attrs(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        maya_test_tools.cmds.addAttr(cube_one, ln='test', at='bool', k=True)  # Add User-defined attribute
        maya_test_tools.cmds.setAttr(f'{cube_one}.tx', lock=True)  # Lock TranslateX
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        maya_test_tools.cmds.parent(cube_two, cube_one)
        # Duplicate
        duplicated_obj = rigging_utils.duplicate_object(obj=cube_one, name="mocked_cube",
                                                        parent_to_world=True, reset_attributes=True)
        # Original Item
        expected = True
        result = maya_test_tools.cmds.getAttr(f'{cube_one}.tx', lock=True)
        self.assertEqual(expected, result)
        expected = True
        result = maya_test_tools.cmds.objExists(f'{cube_one}.test')
        self.assertEqual(expected, result)
        # Duplicate
        expected = False
        result = maya_test_tools.cmds.getAttr(f'{duplicated_obj}.tx', lock=True)
        self.assertEqual(expected, result)
        expected = False
        result = maya_test_tools.cmds.objExists(f'{duplicated_obj}.test')
        self.assertEqual(expected, result)

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

    def test_create_stretchy_ik_setup(self):
        test_joints = [maya_test_tools.cmds.joint(p=(0, 10, 0)),
                       maya_test_tools.cmds.joint(p=(0, 5, .1)),
                       maya_test_tools.cmds.joint(p=(0, 0, 0))]
        an_ik_handle = maya_test_tools.cmds.ikHandle(n='spineConstraint_SC_ikHandle',
                                                     sj=test_joints[0], ee=test_joints[-1],
                                                     sol='ikRPsolver')[0]

        cube = maya_test_tools.cmds.polyCube(ch=False)[0]  # Control in this case
        maya_test_tools.cmds.delete(maya_test_tools.cmds.pointConstraint(test_joints[-1], cube))
        maya_test_tools.cmds.parentConstraint(cube, an_ik_handle, maintainOffset=True)
        from gt.utils.joint_utils import orient_joint
        orient_joint(test_joints)

        stretchy_grp = rigging_utils.create_stretchy_ik_setup(ik_handle=an_ik_handle,
                                                              prefix=None, attribute_holder=cube)
        expected = "|stretchy_grp"
        self.assertEqual(expected, stretchy_grp)
