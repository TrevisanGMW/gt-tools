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
from gt.tests import maya_test_tools
from gt.core import rigging as core_rigging

cmds = maya_test_tools.cmds


class TestRiggingCore(unittest.TestCase):
    temp_dir = ""
    test_fbx_path = ""
    test_ma_path = ""
    test_ma_no_transforms_path = ""

    @classmethod
    def setUpClass(cls):
        """Initializes Maya Standalone and creates temporary files for testing."""
        maya_test_tools.import_maya_standalone(initialize=True)
        cls.temp_dir = maya_test_tools.generate_test_temp_dir()

        # Create a simple FBX file with a sphere
        cmds.file(new=True, force=True)
        cmds.polySphere(name="test_sphere")
        cls.test_fbx_path = os.path.join(cls.temp_dir, "test_sphere.fbx")
        cmds.loadPlugin("fbxmaya.mll", quiet=True)
        cmds.file(cls.test_fbx_path, force=True, options="v=0;", type="FBX export", es=True)

        # Create a simple MA file with a cube
        cmds.file(new=True, force=True)
        cmds.polyCube(name="test_cube")
        cls.test_ma_path = os.path.join(cls.temp_dir, "test_cube.ma")
        cmds.file(rename=cls.test_ma_path)
        cmds.file(save=True, type="mayaAscii")

        # Create a MA file with no transforms
        cmds.file(new=True, force=True)
        cmds.shadingNode("lambert", asShader=True, name="test_material")
        cls.test_ma_no_transforms_path = os.path.join(cls.temp_dir, "no_transforms.ma")
        cmds.file(rename=cls.test_ma_no_transforms_path)
        cmds.file(save=True, type="mayaAscii")

    @classmethod
    def tearDownClass(cls):
        """Cleans up the temporary directory."""
        maya_test_tools.delete_test_temp_dir()

    def setUp(self):
        """Resets the Maya scene before each individual test runs."""
        maya_test_tools.force_new_scene()

    def test_duplicate_joint_for_automation(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        cmds.joint(name="two_jnt")
        # Before Operation
        expected = ["|one_jnt", "|two_jnt"]
        result = cmds.ls(typ="joint", long=True)
        self.assertEqual(expected, result)
        # Operation Result
        result = core_rigging.duplicate_joint_for_automation(
            joint=joint_one, suffix="mocked", parent=None, connect_rot_order=True
        )
        expected = "|one_jnt_mocked"
        self.assertEqual(expected, result)
        # After Operation
        result = cmds.ls(typ="joint", long=True)
        expected = ["|one_jnt", "|one_jnt_mocked", "|two_jnt"]
        self.assertEqual(expected, result)

    def test_duplicate_joint_for_automation_parent(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        cmds.joint(name="two_jnt")
        a_group = cmds.group(name="a_group", empty=True, world=True)
        # Before Operation
        result = cmds.ls(typ="joint", long=True)
        expected = ["|one_jnt", "|two_jnt"]
        self.assertEqual(expected, result)
        # Operation Result
        result = core_rigging.duplicate_joint_for_automation(
            joint=joint_one, suffix="mocked", parent=a_group, connect_rot_order=True
        )
        expected = "|a_group|one_jnt_mocked"
        self.assertEqual(expected, result)
        # After Operation
        result = cmds.ls(typ="joint", long=True)
        expected = ["|one_jnt", "|a_group|one_jnt_mocked", "|two_jnt"]
        self.assertEqual(expected, result)

    def test_duplicate_joint_for_automation_rot_order(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")
        a_group = cmds.group(name="a_group", empty=True, world=True)

        expected = ["|one_jnt", "|two_jnt"]
        result = cmds.ls(typ="joint", long=True)
        self.assertEqual(expected, result)

        jnt_as_node = core_rigging.duplicate_joint_for_automation(
            joint=joint_one, suffix="mocked", parent=a_group, connect_rot_order=True
        )
        expected = ["one_jnt"]
        result = cmds.listConnections(jnt_as_node)
        self.assertEqual(expected, result)
        jnt_as_node = core_rigging.duplicate_joint_for_automation(
            joint=joint_two, suffix="mocked", parent=a_group, connect_rot_order=False
        )
        expected = None
        result = cmds.listConnections(jnt_as_node)
        self.assertEqual(expected, result)

    def test_rescale_joint_radius(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)
        joint_two = cmds.joint(name="two_jnt")

        expected = 1
        result = cmds.getAttr(f"{joint_one}.radius")
        self.assertEqual(expected, result)

        core_rigging.rescale_joint_radius(joint_list=joint_one, multiplier=5)

        expected = 5
        result = cmds.getAttr(f"{joint_one}.radius")
        self.assertEqual(expected, result)

        core_rigging.rescale_joint_radius(joint_list=[joint_one, joint_two], multiplier=2)

        expected = 10
        result = cmds.getAttr(f"{joint_one}.radius")
        self.assertEqual(expected, result)
        expected = 2
        result = cmds.getAttr(f"{joint_two}.radius")
        self.assertEqual(expected, result)

    def test_rescale_joint_radius_initial_value(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)

        expected = 1
        result = cmds.getAttr(f"{joint_one}.radius")
        self.assertEqual(expected, result)

        core_rigging.rescale_joint_radius(joint_list=joint_one, multiplier=2, initial_value=5)

        expected = 10
        result = cmds.getAttr(f"{joint_one}.radius")
        self.assertEqual(expected, result)

    def test_expose_rotation_order(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)

        expected = False
        result = cmds.objExists(f"{joint_one}.rotationOrder")
        self.assertEqual(expected, result)

        core_rigging.expose_rotation_order(target=joint_one, attr_enum="xyz:yzx:zxy:xzy:yxz:zyx")

        expected = True
        result = cmds.objExists(f"{joint_one}.rotationOrder")
        self.assertEqual(expected, result)

        expected = ["one_jnt.rotationOrder", "one_jnt"]
        result = cmds.listConnections(f"{joint_one}.rotationOrder", connections=True)
        self.assertEqual(expected, result)

    def test_expose_rotation_order_attr_name(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)

        expected = False
        result = cmds.objExists(f"{joint_one}.mockedAttr")
        self.assertEqual(expected, result)

        core_rigging.expose_rotation_order(
            target=joint_one, attr_enum="xyz:yzx:zxy:xzy:yxz:zyx", attr_name="mockedAttr"
        )

        expected = True
        result = cmds.objExists(f"{joint_one}.mockedAttr")
        self.assertEqual(expected, result)

        expected = ["one_jnt.mockedAttr", "one_jnt"]
        result = cmds.listConnections(f"{joint_one}.mockedAttr", connections=True)
        self.assertEqual(expected, result)

    def test_expose_rotation_order_return(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.select(clear=True)

        expected = f"{joint_one}.mockedAttr"
        result = core_rigging.expose_rotation_order(
            target=joint_one, attr_enum="xyz:yzx:zxy:xzy:yxz:zyx", attr_name="mockedAttr"
        )
        self.assertEqual(expected, result)

    def test_expose_rotation_order_inheritance(self):
        joint_one = cmds.joint(name="one_jnt")
        cmds.setAttr(f"{joint_one}.rotateOrder", 2)
        cmds.select(clear=True)

        core_rigging.expose_rotation_order(target=joint_one, attr_enum="xyz:yzx:zxy:xzy:yxz:zyx")

        expected = 2
        result = cmds.getAttr(f"{joint_one}.rotationOrder")
        self.assertEqual(expected, result)

    def test_expose_shapes_visibility_return(self):
        ctrl_one = cmds.circle(ch=False)[0]
        cmds.select(clear=True)

        expected = f"{ctrl_one}.mockedAttr"
        result = core_rigging.expose_shapes_visibility(target=ctrl_one, attr_name="mockedAttr")
        self.assertEqual(expected, result)

    def test_expose_shapes_visibility_types_nurbs(self):
        ctrl_one = cmds.circle(ch=False)[0]
        locator = cmds.spaceLocator()[0]

        # Merge loc shape with nurbs circle
        shapes = cmds.listRelatives(locator, shapes=True, fullPath=True) or []
        for shape in shapes:
            cmds.parent(shape, ctrl_one, relative=True, shape=True)

        cmds.select(clear=True)

        expected_shapes = ["|nurbsCircle1|nurbsCircleShape1", "|nurbsCircle1|locatorShape1"]
        result_shapes = cmds.listRelatives(ctrl_one, shapes=True, fullPath=True) or []
        self.assertEqual(expected_shapes, result_shapes)

        expected_attr = f"{ctrl_one}.shapeVisibility"
        result_attr = core_rigging.expose_shapes_visibility(target=ctrl_one, shapes_type="nurbsCurve")
        self.assertEqual(expected_attr, result_attr)

        # Set Vis as False
        cmds.setAttr(expected_attr, False)

        should_be_false = [f"|nurbsCircle1|nurbsCircleShape1.v", expected_attr]
        for obj in should_be_false:
            result = cmds.getAttr(obj)
            self.assertFalse(result)

        should_be_true = [f"|nurbsCircle1|locatorShape1.v"]  # As it's not included in the expose visibility
        for obj in should_be_true:
            result = cmds.getAttr(obj)
            self.assertTrue(result)

    def test_expose_shapes_visibility_types_locator(self):
        ctrl_one = cmds.circle(ch=False)[0]
        locator = cmds.spaceLocator()[0]

        # Merge loc shape with nurbs circle
        shapes = cmds.listRelatives(locator, shapes=True, fullPath=True) or []
        for shape in shapes:
            cmds.parent(shape, ctrl_one, relative=True, shape=True)

        cmds.select(clear=True)

        expected_shapes = ["|nurbsCircle1|nurbsCircleShape1", "|nurbsCircle1|locatorShape1"]
        result_shapes = cmds.listRelatives(ctrl_one, shapes=True, fullPath=True) or []
        self.assertEqual(expected_shapes, result_shapes)

        expected_attr = f"{ctrl_one}.shapeVisibility"
        result_attr = core_rigging.expose_shapes_visibility(target=ctrl_one, shapes_type="locator")
        self.assertEqual(expected_attr, result_attr)

        # Set Vis as False
        cmds.setAttr(expected_attr, False)

        should_be_false = [f"|nurbsCircle1|locatorShape1.v", expected_attr]
        for obj in should_be_false:
            result = cmds.getAttr(obj)
            self.assertFalse(result)

        should_be_true = [f"|nurbsCircle1|nurbsCircleShape1.v"]  # As it's not included in the expose visibility
        for obj in should_be_true:
            result = cmds.getAttr(obj)
            self.assertTrue(result)

    def test_expose_shapes_visibility_no_shapes(self):
        empty_transform = cmds.group(empty=True, world=True)

        expected = []
        result = cmds.listRelatives(empty_transform, shapes=True, fullPath=True) or []
        self.assertEqual(expected, result)

        expected_attr = None
        result_attr = core_rigging.expose_shapes_visibility(target=empty_transform, shapes_type="locator")
        self.assertEqual(expected_attr, result_attr)

        expected = False
        result = cmds.objExists(f"{empty_transform}.shapeVisibility")
        self.assertEqual(expected, result)

    def test_expose_shapes_visibility_default_value(self):
        ctrl_one = cmds.circle(ch=False)[0]
        ctrl_two = cmds.circle(ch=False)[0]

        cmds.select(clear=True)

        # Test True
        expected_attr = f"{ctrl_one}.shapeVisibility"
        result_attr = core_rigging.expose_shapes_visibility(target=ctrl_one, default_value=True)
        self.assertEqual(expected_attr, result_attr)

        expected = True
        result = cmds.getAttr(result_attr)
        self.assertEqual(expected, result)

        # Test False
        expected_attr = f"{ctrl_two}.shapeVisibility"
        result_attr = core_rigging.expose_shapes_visibility(target=ctrl_two, default_value=False)
        self.assertEqual(expected_attr, result_attr)

        expected = False
        result = cmds.getAttr(result_attr)
        self.assertEqual(expected, result)

    def test_offset_control_orientation(self):
        ctrl = cmds.curve(
            point=[
                [0.0, 0.0, 1.0],
                [0.0, 0.0, 0.667],
                [0.0, 0.0, 0.0],
                [0.0, 0.0, -1.0],
                [0.0, 0.0, -1.667],
                [0.0, 0.0, -2.0],
            ],
            degree=3,
            name="mocked_ctrl",
        )
        control_offset = cmds.group(name="offset", empty=True, world=True)
        cmds.parent(ctrl, control_offset)
        # Before Offset
        rx = cmds.getAttr(f"{control_offset}.rx")
        ry = cmds.getAttr(f"{control_offset}.ry")
        rz = cmds.getAttr(f"{control_offset}.rz")
        expected_rx = 0
        expected_ry = 0
        expected_rz = 0
        self.assertEqual(expected_rx, rx)
        self.assertEqual(expected_ry, ry)
        self.assertEqual(expected_rz, rz)
        expected = [0.0, 0.0, 1.0]
        result = cmds.xform(f"{ctrl}.cv[0]", query=True, worldSpace=True, translation=True)
        self.assertEqual(expected, result)
        # Run Offset
        core_rigging.offset_control_orientation(ctrl=ctrl, offset_transform=control_offset, orient_tuple=(90, 0, 0))
        # After Offset
        rx = cmds.getAttr(f"{control_offset}.rx")
        ry = cmds.getAttr(f"{control_offset}.ry")
        rz = cmds.getAttr(f"{control_offset}.rz")
        expected_rx = 90
        expected_ry = 0
        expected_rz = 0
        self.assertEqual(expected_rx, rx)
        self.assertEqual(expected_ry, ry)
        self.assertEqual(expected_rz, rz)
        expected = [0.0, 0.0, 1.0]
        result = cmds.xform(f"{ctrl}.cv[0]", query=True, worldSpace=True, translation=True)
        self.assertEqual(expected, result)

    def test_create_stretchy_ik_setup(self):
        test_joints = [cmds.joint(p=(0, 10, 0)), cmds.joint(p=(0, 5, 0.1)), cmds.joint(p=(0, 0, 0))]
        an_ik_handle = cmds.ikHandle(
            n="spineConstraint_SC_ikHandle", sj=test_joints[0], ee=test_joints[-1], sol="ikRPsolver"
        )[0]

        cube = cmds.polyCube(ch=False)[0]  # Control in this case
        cmds.delete(cmds.pointConstraint(test_joints[-1], cube))
        cmds.parentConstraint(cube, an_ik_handle, maintainOffset=True)
        from gt.core.joint import orient_joint

        orient_joint(test_joints)

        stretchy_grp = core_rigging.create_stretchy_ik_setup(ik_handle=an_ik_handle, prefix=None, attribute_holder=cube)
        expected = "|stretchy_grp"
        self.assertEqual(expected, stretchy_grp)

    def test_create_switch_setup(self):
        base_list = [
            cmds.joint(p=(0, 10, 0), name="base_top"),
            cmds.joint(p=(0, 5, 0.1), name="base_mid"),
            cmds.joint(p=(0, 0, 0), name="base_end"),
        ]
        cmds.select(clear=True)
        a_list = [
            cmds.joint(p=(0, 10, 0), name="a_top"),
            cmds.joint(p=(0, 5, 0.1), name="a_mid"),
            cmds.joint(p=(0, 0, 0), name="a_end"),
        ]
        cmds.select(clear=True)
        b_list = [
            cmds.joint(p=(0, 10, 0), name="b_top"),
            cmds.joint(p=(0, 5, 0.1), name="b_mid"),
            cmds.joint(p=(0, 0, 0), name="b_end"),
        ]
        attr_holder = cmds.circle(name="attr_holder", ch=False)[0]
        vis_a = cmds.polyCube(name="vis_a_cube", ch=False)[0]
        vis_b = cmds.polyCube(name="vis_b_cube", ch=False)[0]

        switch_attrs = core_rigging.create_switch_setup(
            source_a=a_list,
            source_b=b_list,
            target_base=base_list,
            attr_holder=attr_holder,
            visibility_a=vis_a,
            visibility_b=vis_b,
        )

        expected = (
            "|attr_holder.influenceA",
            "|attr_holder.influenceB",
            "|attr_holder.visibilityA",
            "|attr_holder.visibilityB",
        )
        self.assertEqual(expected, switch_attrs)

        expected = True
        shape = cmds.listRelatives(f"{vis_a}", shapes=True)[0]
        result = cmds.getAttr(f"{shape}.v")
        self.assertEqual(expected, result)
        expected = False
        shape = cmds.listRelatives(f"{vis_b}", shapes=True)[0]
        result = cmds.getAttr(f"{shape}.v")
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

        cmds.setAttr(f"{attr_holder}.{core_rigging.RiggingConstants.ATTR_INFLUENCE_SWITCH}", 0)

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
        base_list = [
            cmds.joint(p=(0, 10, 0), name="base_top"),
            cmds.joint(p=(0, 5, 0.1), name="base_mid"),
            cmds.joint(p=(0, 0, 0), name="base_end"),
        ]
        cmds.select(clear=True)
        a_list = [
            cmds.joint(p=(0, 10, 0), name="a_top"),
            cmds.joint(p=(0, 5, 0.1), name="a_mid"),
            cmds.joint(p=(0, 0, 0), name="a_end"),
        ]
        cmds.select(clear=True)
        b_list = [
            cmds.joint(p=(0, 10, 0), name="b_top"),
            cmds.joint(p=(0, 5, 0.1), name="b_mid"),
            cmds.joint(p=(0, 0, 0), name="b_end"),
        ]
        attr_holder = cmds.circle(name="attr_holder", ch=False)[0]
        vis_a = cmds.polyCube(name="vis_a_cube", ch=False)[0]
        vis_b = cmds.polyCube(name="vis_b_cube", ch=False)[0]

        switch_attrs = core_rigging.create_switch_setup(
            source_a=a_list,
            source_b=b_list,
            target_base=base_list,
            attr_holder=attr_holder,
            visibility_a=vis_a,
            visibility_b=vis_b,
            shape_visibility=False,
        )

        expected = (
            "|attr_holder.influenceA",
            "|attr_holder.influenceB",
            "|attr_holder.visibilityA",
            "|attr_holder.visibilityB",
        )
        self.assertEqual(expected, switch_attrs)

        expected = True
        result = cmds.getAttr(f"{vis_a}.v")
        self.assertEqual(expected, result)
        expected = False
        result = cmds.getAttr(f"{vis_b}.v")
        self.assertEqual(expected, result)

    def test_add_limit_lock_translate_setup(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        attr = core_rigging.add_limit_lock_translate_setup(
            target=cube_one, lock_attr="lockTranslate", attr_holder=None, default_value=True
        )
        expected = f"{cube_one}.lockTranslate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        default_dimensions = ["X", "Y", "Z"]
        for dimension in default_dimensions:
            expected = 0
            min_limit = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 0
            max_limit = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_translate_setup_with_attr_holder(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_translate_setup(
            target=cube_one, lock_attr="lockTranslate", attr_holder=cube_two, default_value=True
        )
        expected = f"{cube_two}.lockTranslate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        default_dimensions = ["X", "Y", "Z"]
        for dimension in default_dimensions:
            expected = 0
            min_limit = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 0
            max_limit = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_translate_setup_with_attr_limit_value(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_translate_setup(
            target=cube_one, lock_attr="lockTranslate", attr_holder=cube_two, default_value=True, limit_value=2
        )
        expected = f"{cube_two}.lockTranslate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        default_dimensions = ["X", "Y", "Z"]
        for dimension in default_dimensions:
            expected = 2
            min_limit = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 2
            max_limit = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_translate_setup_with_default_value(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_translate_setup(
            target=cube_one, lock_attr="lockTranslate", attr_holder=cube_two, default_value=False
        )
        expected = f"{cube_two}.lockTranslate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertFalse(result)

    def test_add_limit_lock_translate_setup_with_custom_attr(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_translate_setup(
            target=cube_one, lock_attr="lockT", attr_holder=cube_two, default_value=False
        )
        expected = f"{cube_two}.lockT"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertFalse(result)

    def test_add_limit_lock_translate_setup_with_dimensions(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        dimension_tuple = ("x", "z")
        unlisted_dimensions = "y"
        attr = core_rigging.add_limit_lock_translate_setup(
            target=cube_one,
            lock_attr="lockTranslate",
            dimensions=dimension_tuple,
            attr_holder=cube_two,
            default_value=True,
        )
        expected = f"{cube_two}.lockTranslate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        for dimension in dimension_tuple:  # X, Z
            expected = 0
            min_limit = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 0
            max_limit = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

        for dimension in unlisted_dimensions:  # Y
            expected = -1
            min_limit = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 1
            max_limit = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minTrans{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxTrans{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_rotate_setup(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        attr = core_rigging.add_limit_lock_rotate_setup(
            target=cube_one, lock_attr="lockRotate", attr_holder=None, default_value=True
        )
        expected = f"{cube_one}.lockRotate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        default_dimensions = ["X", "Y", "Z"]
        for dimension in default_dimensions:
            expected = 0
            min_limit = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 0
            max_limit = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_rotate_setup_with_attr_holder(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_rotate_setup(
            target=cube_one, lock_attr="lockRotate", attr_holder=cube_two, default_value=True
        )
        expected = f"{cube_two}.lockRotate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        default_dimensions = ["X", "Y", "Z"]
        for dimension in default_dimensions:
            expected = 0
            min_limit = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 0
            max_limit = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_rotate_setup_with_attr_limit_value(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_rotate_setup(
            target=cube_one, lock_attr="lockRotate", attr_holder=cube_two, default_value=True, limit_value=2
        )
        expected = f"{cube_two}.lockRotate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        default_dimensions = ["X", "Y", "Z"]
        for dimension in default_dimensions:
            expected = 2
            min_limit = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 2
            max_limit = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_rotate_setup_with_default_value(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_rotate_setup(
            target=cube_one, lock_attr="lockRotate", attr_holder=cube_two, default_value=False
        )
        expected = f"{cube_two}.lockRotate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertFalse(result)

    def test_add_limit_lock_rotate_setup_with_custom_attr(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_rotate_setup(
            target=cube_one, lock_attr="lockR", attr_holder=cube_two, default_value=False
        )
        expected = f"{cube_two}.lockR"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertFalse(result)

    def test_add_limit_lock_rotate_setup_with_dimensions(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        dimension_tuple = ("x", "z")
        unlisted_dimensions = "y"
        attr = core_rigging.add_limit_lock_rotate_setup(
            target=cube_one,
            lock_attr="lockRotate",
            dimensions=dimension_tuple,
            attr_holder=cube_two,
            default_value=True,
        )
        expected = f"{cube_two}.lockRotate"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        for dimension in dimension_tuple:  # X, Z
            expected = 0
            min_limit = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 0
            max_limit = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

        for dimension in unlisted_dimensions:  # Y
            expected = -45
            min_limit = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 45
            max_limit = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_scale_setup(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        attr = core_rigging.add_limit_lock_scale_setup(
            target=cube_one, lock_attr="lockScale", attr_holder=None, default_value=True
        )
        expected = f"{cube_one}.lockScale"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        default_dimensions = ["X", "Y", "Z"]
        for dimension in default_dimensions:
            expected = 1
            min_limit = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 1
            max_limit = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_scale_setup_with_attr_holder(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_scale_setup(
            target=cube_one, lock_attr="lockScale", attr_holder=cube_two, default_value=True
        )
        expected = f"{cube_two}.lockScale"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        default_dimensions = ["X", "Y", "Z"]
        for dimension in default_dimensions:
            expected = 1
            min_limit = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 1
            max_limit = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_scale_setup_with_limit_value(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_scale_setup(
            target=cube_one, lock_attr="lockScale", attr_holder=cube_two, default_value=True, limit_value=2
        )
        expected = f"{cube_two}.lockScale"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        default_dimensions = ["X", "Y", "Z"]
        for dimension in default_dimensions:
            expected = 2
            min_limit = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 2
            max_limit = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_scale_setup_with_default_value(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_scale_setup(
            target=cube_one, lock_attr="lockScale", attr_holder=cube_two, default_value=False
        )
        expected = f"{cube_two}.lockScale"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertFalse(result)

    def test_add_limit_lock_scale_setup_with_custom_attr(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        attr = core_rigging.add_limit_lock_scale_setup(
            target=cube_one, lock_attr="lockR", attr_holder=cube_two, default_value=False
        )
        expected = f"{cube_two}.lockR"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertFalse(result)

    def test_add_limit_lock_scale_setup_with_dimensions(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        dimension_tuple = ("x", "z")
        unlisted_dimensions = "y"
        attr = core_rigging.add_limit_lock_scale_setup(
            target=cube_one, lock_attr="lockScale", dimensions=dimension_tuple, attr_holder=cube_two, default_value=True
        )
        expected = f"{cube_two}.lockScale"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        for dimension in dimension_tuple:  # X, Z
            expected = 1
            min_limit = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 1
            max_limit = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

        for dimension in unlisted_dimensions:  # Y
            expected = -1
            min_limit = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 1
            max_limit = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minScale{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxScale{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_rotate_with_exception_z(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        attr = core_rigging.add_limit_lock_rotate_with_exception(target=cube_one, exception="z")

        expected = f"{cube_one}.lockXY"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        dimension_tuple = ("x", "y")
        for dimension in dimension_tuple:  # X, Y
            expected = 0
            min_limit = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 0
            max_limit = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

        unlisted_dimensions = "z"
        for dimension in unlisted_dimensions:  # Z
            expected = -45
            min_limit = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 45
            max_limit = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, max_limit_en)

    def test_add_limit_lock_rotate_with_exception_xy(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        attr = core_rigging.add_limit_lock_rotate_with_exception(target=cube_one, exception=("x", "y"))

        expected = f"{cube_one}.lockZ"
        self.assertEqual(expected, attr)

        result = cmds.objExists(attr)
        self.assertTrue(result)

        result = cmds.getAttr(attr)
        self.assertTrue(result)

        dimension_tuple = "z"
        for dimension in dimension_tuple:
            expected = 0
            min_limit = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 0
            max_limit = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}LimitEnable")
            expected = True
            self.assertEqual(expected, max_limit_en)

        unlisted_dimensions = ("x", "y")
        for dimension in unlisted_dimensions:
            expected = -45
            min_limit = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}Limit")
            self.assertEqual(expected, min_limit)
            expected = 45
            max_limit = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}Limit")
            self.assertEqual(expected, max_limit)
            min_limit_en = cmds.getAttr(f"{cube_one}.minRot{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, min_limit_en)
            max_limit_en = cmds.getAttr(f"{cube_one}.maxRot{dimension.upper()}LimitEnable")
            expected = False
            self.assertEqual(expected, max_limit_en)

    def test_create_enum_switch_creates_enum_attribute(self):
        ctrl = cmds.circle(name="Test_CTRL")[0]
        cube = cmds.polyCube(name="TestCube")[0]

        core_rigging.create_enum_switch(
            attribute_holder=ctrl, targets=[cube], display_names=["One"], attr_name="testEnum"
        )

        self.assertTrue(cmds.attributeQuery("testEnum", node=ctrl, exists=True))

    def test_create_enum_switch_enum_controls_visibility(self):
        ctrl = cmds.circle(name="Switch_CTRL")[0]
        red = cmds.polyCube(name="Red")[0]
        green = cmds.polyCube(name="Green")[0]
        blue = cmds.polyCube(name="Blue")[0]

        targets = [[red], [green, blue]]

        core_rigging.create_enum_switch(
            attribute_holder=ctrl,
            targets=targets,
            display_names=["RedOnly", "GreenBlue"],
            attr_name="visMode",
            controlled_attrs="visibility",
        )

        attr = f"{ctrl}.visMode"

        # Check state 0 (Red only visible)
        cmds.setAttr(attr, 0)
        self.assertEqual(cmds.getAttr(f"{red}.visibility"), True)
        self.assertEqual(cmds.getAttr(f"{green}.visibility"), False)
        self.assertEqual(cmds.getAttr(f"{blue}.visibility"), False)

        # Check state 1 (Green+Blue visible)
        cmds.setAttr(attr, 1)
        self.assertEqual(cmds.getAttr(f"{red}.visibility"), False)
        self.assertEqual(cmds.getAttr(f"{green}.visibility"), True)
        self.assertEqual(cmds.getAttr(f"{blue}.visibility"), True)

    def test_create_enum_switch_supports_multiple_controlled_attrs(self):
        ctrl = cmds.circle(name="MultiAttr_CTRL")[0]
        cube1 = cmds.polyCube(name="Cube1")[0]
        cube2 = cmds.polyCube(name="Cube2")[0]

        cmds.setAttr(f"{cube1}.translateX", lock=False)
        cmds.setAttr(f"{cube2}.translateX", lock=False)

        core_rigging.create_enum_switch(
            attribute_holder=ctrl,
            targets=[[cube1], [cube2]],
            display_names=["One", "Two"],
            attr_name="mode",
            controlled_attrs=["visibility"],
        )

        self.assertTrue(cmds.attributeQuery("mode", node=ctrl, exists=True))

    def test_create_enum_switch_default_index_applied(self):
        ctrl = cmds.circle(name="Default_CTRL")[0]
        red = cmds.polyCube(name="RedCube")[0]
        green = cmds.polyCube(name="GreenCube")[0]

        core_rigging.create_enum_switch(
            attribute_holder=ctrl,
            targets=[[red], [green]],
            display_names=["Red", "Green"],
            attr_name="colorMode",
            controlled_attrs="visibility",
            default_index=1,
        )

        self.assertEqual(cmds.getAttr(f"{ctrl}.colorMode"), 1)
        self.assertEqual(cmds.getAttr(f"{green}.visibility"), True)
        self.assertEqual(cmds.getAttr(f"{red}.visibility"), False)

    def test_create_enum_switch_raises_if_attr_exists(self):
        ctrl = cmds.circle(name="Duplicate_CTRL")[0]
        cube = cmds.polyCube(name="CubeX")[0]

        # First creation should work
        core_rigging.create_enum_switch(
            attribute_holder=ctrl, targets=[cube], display_names=["Only"], attr_name="dupAttr"
        )

        # Second attempt with same attr should fail
        with self.assertRaises(ValueError):
            core_rigging.create_enum_switch(
                attribute_holder=ctrl, targets=[cube], display_names=["Only"], attr_name="dupAttr"
            )

    def test_create_enum_switch_raises_on_invalid_object(self):
        ctrl = cmds.circle(name="Bad_CTRL")[0]

        with self.assertRaises(ValueError):
            core_rigging.create_enum_switch(
                attribute_holder=ctrl, targets=["nonExistentObject"], display_names=["Fake"]
            )

    def test_create_enum_switch_raises_on_mismatched_display_names(self):
        ctrl = cmds.circle(name="Mismatch_CTRL")[0]
        a = cmds.polyCube(name="A")[0]
        b = cmds.polyCube(name="B")[0]

        with self.assertRaises(ValueError):
            core_rigging.create_enum_switch(attribute_holder=ctrl, targets=[[a], [b]], display_names=["OnlyOne"])

    def test_import_with_offset_fbx_creates_group_and_applies_offset(self):
        """Tests successful FBX import, group creation, and default offset."""
        # 1. Assign expected value
        expected_group_name = "imported"
        expected_rotation_y = -90.0

        # 2. Assign result value
        result_group_name = core_rigging.import_with_offset(self.test_fbx_path, rotate_offset=[0, -90, 0])

        # 3. Assert equality and conditions
        self.assertEqual(result_group_name, expected_group_name)
        self.assertTrue(cmds.objExists(expected_group_name))

        children = cmds.listRelatives(expected_group_name, children=True, type="transform")
        self.assertIn("test_sphere", children)

        result_rotation_y = cmds.getAttr("test_sphere.rotateY")
        self.assertAlmostEqual(result_rotation_y, expected_rotation_y, places=3)

    def test_import_with_offset_group_is_reused_on_second_import(self):
        """Tests that the tracking group is found and reused."""
        # Run the import twice with different files
        core_rigging.import_with_offset(self.test_fbx_path)
        core_rigging.import_with_offset(self.test_ma_path)

        # 1. Assign expected value
        expected_group_count = 1
        expected_child_count = 2

        # 2. Assign result value
        _ref_attr = core_rigging.RiggingConstants.ATTR_IMPORT_OFFSET_REF
        result_groups = [n for n in cmds.ls(type="transform") if cmds.attributeQuery(_ref_attr, node=n, exists=True)]
        result_children = cmds.listRelatives(result_groups[0], children=True, type="transform")

        # 3. Assert equality
        self.assertEqual(len(result_groups), expected_group_count)
        self.assertEqual(len(result_children), expected_child_count)

    def test_import_with_offset_custom_offset_is_applied_correctly(self):
        """Tests that custom translate and rotate offsets are applied."""
        # 1. Assign expected value
        expected_translate = (10.0, 20.0, 30.0)
        expected_rotate = (15.0, 45.0, 60.0)

        # 2. Assign result value
        group = core_rigging.import_with_offset(
            self.test_ma_path, translate_offset=expected_translate, rotate_offset=expected_rotate
        )
        child_node = cmds.listRelatives(group, children=True, type="transform")[0]
        result_translate = cmds.getAttr(f"{child_node}.translate")[0]
        result_rotate = cmds.getAttr(f"{child_node}.rotate")[0]

        # 3. Assert equality (using assertAlmostEqual for float comparisons)
        for i in range(3):
            self.assertAlmostEqual(result_translate[i], expected_translate[i], places=3)
            self.assertAlmostEqual(result_rotate[i], expected_rotate[i], places=3)

    def test_import_with_offset_import_with_no_transforms_returns_none(self):
        """Tests that importing a file with no transforms fails gracefully."""
        # 1. Assign expected value
        expected = None

        # 2. Assign result value
        result = core_rigging.import_with_offset(self.test_ma_no_transforms_path)

        # 3. Assert equality
        self.assertEqual(result, expected)

        # Verify that no group was created
        _ref_attr = core_rigging.RiggingConstants.ATTR_IMPORT_OFFSET_REF
        groups = [n for n in cmds.ls(type="transform") if cmds.attributeQuery(_ref_attr, node=n, exists=True)]
        self.assertEqual(len(groups), 0)
