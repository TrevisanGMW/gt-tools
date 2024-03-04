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
cmds = maya_test_tools.cmds

class TestRiggingUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_duplicate_joint_for_automation(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        cmds.joint(name="two_jnt")
        # Before Operation
        expected = ['|one_jnt', '|two_jnt']
        result = cmds.ls(typ="joint", long=True)
        self.assertEqual(expected, result)
        # Operation Result
        result = rigging_utils.duplicate_joint_for_automation(joint=joint_one, suffix="mocked",
                                                              parent=None, connect_rot_order=True)
        expected = '|one_jnt_mocked'
        self.assertEqual(expected, result)
        # After Operation
        result = cmds.ls(typ="joint", long=True)
        expected = ['|one_jnt', '|one_jnt_mocked', '|two_jnt']
        self.assertEqual(expected, result)

    def test_duplicate_joint_for_automation_parent(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        cmds.joint(name="two_jnt")
        a_group = cmds.group(name="a_group", empty=True, world=True)
        # Before Operation
        result = cmds.ls(typ="joint", long=True)
        expected = ['|one_jnt', '|two_jnt']
        self.assertEqual(expected, result)
        # Operation Result
        result = rigging_utils.duplicate_joint_for_automation(joint=joint_one, suffix="mocked",
                                                              parent=a_group, connect_rot_order=True)
        expected = '|a_group|one_jnt_mocked'
        self.assertEqual(expected, result)
        # After Operation
        result = cmds.ls(typ="joint", long=True)
        expected = ['|one_jnt', '|a_group|one_jnt_mocked', '|two_jnt']
        self.assertEqual(expected, result)

    def test_duplicate_joint_for_automation_rot_order(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")
        a_group = cmds.group(name="a_group", empty=True, world=True)

        expected = ['|one_jnt', '|two_jnt']
        result = cmds.ls(typ="joint", long=True)
        self.assertEqual(expected, result)

        jnt_as_node = rigging_utils.duplicate_joint_for_automation(joint=joint_one, suffix="mocked",
                                                                   parent=a_group, connect_rot_order=True)
        expected = ['one_jnt']
        result = cmds.listConnections(jnt_as_node)
        self.assertEqual(expected, result)
        jnt_as_node = rigging_utils.duplicate_joint_for_automation(joint=joint_two, suffix="mocked",
                                                                   parent=a_group, connect_rot_order=False)
        expected = None
        result = cmds.listConnections(jnt_as_node)
        self.assertEqual(expected, result)

    def test_rescale_joint_radius(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")

        expected = 1
        result = cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)

        rigging_utils.rescale_joint_radius(joint_list=joint_one, multiplier=5)

        expected = 5
        result = cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)

        rigging_utils.rescale_joint_radius(joint_list=[joint_one, joint_two], multiplier=2)

        expected = 10
        result = cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)
        expected = 2
        result = cmds.getAttr(f'{joint_two}.radius')
        self.assertEqual(expected, result)

    def test_rescale_joint_radius_initial_value(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)

        expected = 1
        result = cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)

        rigging_utils.rescale_joint_radius(joint_list=joint_one, multiplier=2, initial_value=5)

        expected = 10
        result = cmds.getAttr(f'{joint_one}.radius')
        self.assertEqual(expected, result)

    def test_expose_rotation_order(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)

        expected = False
        result = cmds.objExists(f'{joint_one}.rotationOrder')
        self.assertEqual(expected, result)

        rigging_utils.expose_rotation_order(target=joint_one, attr_enum='xyz:yzx:zxy:xzy:yxz:zyx')

        expected = True
        result = cmds.objExists(f'{joint_one}.rotationOrder')
        self.assertEqual(expected, result)

        expected = ['one_jnt.rotationOrder', 'one_jnt']
        result = cmds.listConnections(f'{joint_one}.rotationOrder', connections=True)
        self.assertEqual(expected, result)

    def test_offset_control_orientation(self):
        ctrl = cmds.curve(point=[[0.0, 0.0, 1.0], [0.0, 0.0, 0.667], [0.0, 0.0, 0.0],
                                                [0.0, 0.0, -1.0], [0.0, 0.0, -1.667], [0.0, 0.0, -2.0]],
                                          degree=3, name='mocked_ctrl')
        control_offset = cmds.group(name="offset", empty=True, world=True)
        cmds.parent(ctrl, control_offset)
        # Before Offset
        rx = cmds.getAttr(f'{control_offset}.rx')
        ry = cmds.getAttr(f'{control_offset}.ry')
        rz = cmds.getAttr(f'{control_offset}.rz')
        expected_rx = 0
        expected_ry = 0
        expected_rz = 0
        self.assertEqual(expected_rx, rx)
        self.assertEqual(expected_ry, ry)
        self.assertEqual(expected_rz, rz)
        expected = [0.0, 0.0, 1.0]
        result = cmds.xform(f'{ctrl}.cv[0]', query=True, worldSpace=True, translation=True)
        self.assertEqual(expected, result)
        # Run Offset
        rigging_utils.offset_control_orientation(ctrl=ctrl,
                                                 offset_transform=control_offset,
                                                 orient_tuple=(90, 0, 0))
        # After Offset
        rx = cmds.getAttr(f'{control_offset}.rx')
        ry = cmds.getAttr(f'{control_offset}.ry')
        rz = cmds.getAttr(f'{control_offset}.rz')
        expected_rx = 90
        expected_ry = 0
        expected_rz = 0
        self.assertEqual(expected_rx, rx)
        self.assertEqual(expected_ry, ry)
        self.assertEqual(expected_rz, rz)
        expected = [0.0, 0.0, 1.0]
        result = cmds.xform(f'{ctrl}.cv[0]', query=True, worldSpace=True, translation=True)
        self.assertEqual(expected, result)

    def test_create_stretchy_ik_setup(self):
        test_joints = [cmds.joint(p=(0, 10, 0)),
                       cmds.joint(p=(0, 5, .1)),
                       cmds.joint(p=(0, 0, 0))]
        an_ik_handle = cmds.ikHandle(n='spineConstraint_SC_ikHandle',
                                                     sj=test_joints[0], ee=test_joints[-1],
                                                     sol='ikRPsolver')[0]

        cube = cmds.polyCube(ch=False)[0]  # Control in this case
        cmds.delete(cmds.pointConstraint(test_joints[-1], cube))
        cmds.parentConstraint(cube, an_ik_handle, maintainOffset=True)
        from gt.utils.joint_utils import orient_joint
        orient_joint(test_joints)

        stretchy_grp = rigging_utils.create_stretchy_ik_setup(ik_handle=an_ik_handle,
                                                              prefix=None, attribute_holder=cube)
        expected = "|stretchy_grp"
        self.assertEqual(expected, stretchy_grp)

    def test_create_switch_setup(self):
        base_list = [cmds.joint(p=(0, 10, 0), name="base_top"),
                     cmds.joint(p=(0, 5, .1), name="base_mid"),
                     cmds.joint(p=(0, 0, 0), name="base_end")]
        cmds.select(clear=True)
        a_list = [cmds.joint(p=(0, 10, 0), name="a_top"),
                  cmds.joint(p=(0, 5, .1), name="a_mid"),
                  cmds.joint(p=(0, 0, 0), name="a_end")]
        cmds.select(clear=True)
        b_list = [cmds.joint(p=(0, 10, 0), name="b_top"),
                  cmds.joint(p=(0, 5, .1), name="b_mid"),
                  cmds.joint(p=(0, 0, 0), name="b_end")]
        attr_holder = cmds.circle(name='attr_holder', ch=False)[0]
        vis_a = cmds.polyCube(name='vis_a_cube', ch=False)[0]
        vis_b = cmds.polyCube(name='vis_b_cube', ch=False)[0]

        switch_attrs = rigging_utils.create_switch_setup(source_a=a_list, source_b=b_list,
                                                         target_base=base_list, attr_holder=attr_holder,
                                                         visibility_a=vis_a, visibility_b=vis_b)

        expected = ('|attr_holder.influenceA', '|attr_holder.influenceB', 
                    '|attr_holder.visibilityA', '|attr_holder.visibilityB')
        self.assertEqual(expected, switch_attrs)

        expected = True
        shape = cmds.listRelatives(f'{vis_a}', shapes=True)[0]
        result = cmds.getAttr(f'{shape}.v')
        self.assertEqual(expected, result)
        expected = False
        shape = cmds.listRelatives(f'{vis_b}', shapes=True)[0]
        result = cmds.getAttr(f'{shape}.v')
        self.assertEqual(expected, result)

        result = cmds.getAttr(switch_attrs[0])
        expected = 1
        self.assertEqual(expected, result)

        result = cmds.getAttr(switch_attrs[1])
        expected = 0
        self.assertEqual(expected, result)

        result = cmds.getAttr(switch_attrs[2])
        expected = True
        self.assertEqual(expected, result)

        result = cmds.getAttr(switch_attrs[3])
        expected = False
        self.assertEqual(expected, result)

        cmds.setAttr(f'{attr_holder}.{rigging_utils.RiggingConstants.ATTR_INFLUENCE_SWITCH}', 0)

        result = cmds.getAttr(switch_attrs[0])
        expected = 0
        self.assertEqual(expected, result)

        result = cmds.getAttr(switch_attrs[1])
        expected = 1
        self.assertEqual(expected, result)

        result = cmds.getAttr(switch_attrs[2])
        expected = False
        self.assertEqual(expected, result)

        result = cmds.getAttr(switch_attrs[3])
        expected = True
        self.assertEqual(expected, result)



    def test_create_switch_setup_transform_visibility(self):
        base_list = [cmds.joint(p=(0, 10, 0), name="base_top"),
                     cmds.joint(p=(0, 5, .1), name="base_mid"),
                     cmds.joint(p=(0, 0, 0), name="base_end")]
        cmds.select(clear=True)
        a_list = [cmds.joint(p=(0, 10, 0), name="a_top"),
                  cmds.joint(p=(0, 5, .1), name="a_mid"),
                  cmds.joint(p=(0, 0, 0), name="a_end")]
        cmds.select(clear=True)
        b_list = [cmds.joint(p=(0, 10, 0), name="b_top"),
                  cmds.joint(p=(0, 5, .1), name="b_mid"),
                  cmds.joint(p=(0, 0, 0), name="b_end")]
        attr_holder = cmds.circle(name='attr_holder', ch=False)[0]
        vis_a = cmds.polyCube(name='vis_a_cube', ch=False)[0]
        vis_b = cmds.polyCube(name='vis_b_cube', ch=False)[0]

        switch_attrs = rigging_utils.create_switch_setup(source_a=a_list, source_b=b_list,
                                                         target_base=base_list, attr_holder=attr_holder,
                                                         visibility_a=vis_a, visibility_b=vis_b,
                                                         shape_visibility=False)

        expected = ('|attr_holder.influenceA', '|attr_holder.influenceB',
                    '|attr_holder.visibilityA', '|attr_holder.visibilityB')
        self.assertEqual(expected, switch_attrs)

        expected = True
        result = cmds.getAttr(f'{vis_a}.v')
        self.assertEqual(expected, result)
        expected = False
        result = cmds.getAttr(f'{vis_b}.v')
        self.assertEqual(expected, result)
