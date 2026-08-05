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
import gt.tools.auto_rigger.modules.module_root as tools_mod_root
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.core.rigging as core_rigging
from gt.tests import maya_test_tools
import gt.core.node as core_node

cmds = maya_test_tools.cmds


class TestRigUtils(unittest.TestCase):
    """
    Most tests follow the same order of the functions found in the rig_utils script from top to bottom.
    Only some of them might be in a slightly different order to account for validation before use.
    """

    def setUp(self):
        maya_test_tools.force_new_scene()
        self.temp_dir = maya_test_tools.generate_test_temp_dir()
        self.file_path = os.path.join(self.temp_dir, "test_file.txt")
        if os.path.exists(self.file_path):
            maya_test_tools.unlock_file_permissions(self.file_path)

    def tearDown(self):
        if os.path.exists(self.file_path):
            maya_test_tools.unlock_file_permissions(self.file_path)
        maya_test_tools.delete_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    # ------------------------------------------ Lookup functions ------------------------------------------
    def test_find_proxy_from_uuid(self):
        a_1st_valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        a_2nd_valid_uuid = "631b5e34-58af-48c3-80e0-c41fe7a56470"
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_1st_proxy = a_generic_module.add_new_proxy()
        a_2nd_proxy = a_generic_module.add_new_proxy()
        a_1st_proxy.set_name("firstProxy")
        a_2nd_proxy.set_name("secondProxy")
        a_1st_proxy.set_uuid(a_1st_valid_uuid)
        a_2nd_proxy.set_uuid(a_2nd_valid_uuid)
        a_generic_module.build_proxy()

        expected = "|firstProxy_offset|firstProxy"
        result = tools_rig_utils.find_proxy_from_uuid(uuid_string=a_1st_valid_uuid)
        self.assertEqual(expected, result)

        expected = "|secondProxy_offset|secondProxy"
        result = tools_rig_utils.find_proxy_from_uuid(uuid_string=a_2nd_valid_uuid)
        self.assertEqual(expected, result)

    def test_find_proxy_from_uuid_missing(self):
        a_valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        unused_uuid = "631b5e34-58af-48c3-80e0-c41fe7a56470"
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_proxy = a_generic_module.add_new_proxy()
        a_proxy.set_uuid(a_valid_uuid)
        a_generic_module.build_proxy()

        expected = None
        result = tools_rig_utils.find_proxy_from_uuid(uuid_string=unused_uuid)
        self.assertEqual(expected, result)

    def test_find_joint_from_uuid(self):
        a_1st_valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        a_2nd_valid_uuid = "631b5e34-58af-48c3-80e0-c41fe7a56470"
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_1st_proxy = a_generic_module.add_new_proxy()
        a_2nd_proxy = a_generic_module.add_new_proxy()
        a_1st_proxy.set_name("firstProxy")
        a_2nd_proxy.set_name("secondProxy")
        a_1st_proxy.set_uuid(a_1st_valid_uuid)
        a_2nd_proxy.set_uuid(a_2nd_valid_uuid)
        a_generic_module.build_proxy()
        a_generic_module.build_skeleton_joints()

        expected = "|firstProxy_JNT"
        result = tools_rig_utils.find_joint_from_uuid(uuid_string=a_1st_valid_uuid)
        self.assertEqual(expected, result)
        expected = "|secondProxy_JNT"
        result = tools_rig_utils.find_joint_from_uuid(uuid_string=a_2nd_valid_uuid)
        self.assertEqual(expected, result)

    def test_find_joint_from_uuid_missing(self):
        a_valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        unused_uuid = "631b5e34-58af-48c3-80e0-c41fe7a56470"
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_proxy = a_generic_module.add_new_proxy()
        a_proxy.set_uuid(a_valid_uuid)
        a_generic_module.build_proxy()
        a_generic_module.build_skeleton_joints()

        expected = None
        result = tools_rig_utils.find_joint_from_uuid(uuid_string=unused_uuid)
        self.assertEqual(expected, result)

    def test_find_driver_from_uuid(self):
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()
        a_project.build_rig()

        # Get Driver from 1st Module
        root_1st_purpose = a_1st_root_module.root_proxy.get_meta_purpose()
        root_1st_fk_driver = a_1st_root_module.root_proxy.get_driver_types()[1]  # 0 = block  1 = root
        root_1st_driver_uuid = f"{a_1st_root_module.get_uuid()}-{root_1st_fk_driver}-{root_1st_purpose}"

        expected = "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL"
        result = tools_rig_utils.find_driver_from_uuid(uuid_string=root_1st_driver_uuid)
        self.assertEqual(expected, result)

        # Get Driver from 2nd Module
        root_2nd_module_uuid = a_2nd_root_module.get_uuid()
        root_2nd_purpose = a_2nd_root_module.root_proxy.get_meta_purpose()
        root_2nd_fk_driver = a_2nd_root_module.root_proxy.get_driver_types()[1]  # 0 = block  1 = root
        root_2nd_driver_uuid = f"{root_2nd_module_uuid}-{root_2nd_fk_driver}-{root_2nd_purpose}"

        expected = "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_secondRoot_offset|C_secondRoot_parentOffset"
        expected += "|C_secondRoot_CTRL"
        result = tools_rig_utils.find_driver_from_uuid(uuid_string=root_2nd_driver_uuid)
        self.assertEqual(expected, result)

    def test_find_drivers_from_joint(self):
        a_1st_valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        a_2nd_valid_uuid = "631b5e34-58af-48c3-80e0-c41fe7a56470"
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        a_1st_root_module.root_proxy.set_uuid(a_1st_valid_uuid)
        a_2nd_root_module.root_proxy.set_uuid(a_2nd_valid_uuid)
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()
        a_project.build_rig()

        # Get 1st Root Joint
        root_1st_jnt = tools_rig_utils.find_joint_from_uuid(uuid_string=a_1st_valid_uuid)

        expected = {
            "fk": "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL"
        }
        result = tools_rig_utils.find_drivers_from_joint(source_joint=root_1st_jnt)
        self.assertEqual(expected, result)
        expected = {}
        result = tools_rig_utils.find_drivers_from_joint(source_joint=root_1st_jnt, skip_block_drivers=True)
        self.assertEqual(expected, result)

        # Get 2nd Root Joint
        root_2nd_jnt = tools_rig_utils.find_joint_from_uuid(uuid_string=a_2nd_valid_uuid)
        expected = {
            "fk": "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_secondRoot_offset|C_secondRoot_parentOffset|C_secondRoot_CTRL"
        }
        result = tools_rig_utils.find_drivers_from_joint(source_joint=root_2nd_jnt)
        self.assertEqual(expected, result)
        expected = {}
        result = tools_rig_utils.find_drivers_from_joint(source_joint=root_2nd_jnt, skip_block_drivers=True)
        self.assertEqual(expected, result)

    def test_add_driver_uuid_attr(self):
        """This test is out of order because the next test requires it"""
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        a_generic_group = maya_test_tools.create_group(name="a_generic_group")
        root_module_uuid = a_root_module.get_uuid()
        mocked_driver = "mockedDriver"
        mocked_purpose = "mockedPurpose"
        expected = f"{root_module_uuid}-{mocked_driver}-{mocked_purpose}"
        result = tools_rig_utils.add_driver_uuid_attr(
            target_driver=a_generic_group,
            module_uuid=root_module_uuid,
            driver_type=mocked_driver,
            proxy_purpose=mocked_purpose,
        )
        self.assertEqual(expected, result)
        uuid_attr = tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID
        uuid_attr_path = f"{a_generic_group}.{uuid_attr}"
        self.assertTrue(cmds.objExists(uuid_attr_path))
        result = cmds.getAttr(uuid_attr_path)
        self.assertEqual(expected, result)

    def test_add_driver_uuid_attr_alternative_parameters(self):
        """This test is out of order because the next test requires it"""
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        # A 1st group
        a_1st_group = maya_test_tools.create_group(name="a_1st_group")
        root_module_uuid = a_root_module.get_uuid()
        expected = f"{root_module_uuid}-unknown-unknown"
        result = tools_rig_utils.add_driver_uuid_attr(
            target_driver=a_1st_group,
            module_uuid=root_module_uuid,
            driver_type=None,
            proxy_purpose=None,
        )
        self.assertEqual(expected, result)
        uuid_attr = tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID
        uuid_attr_path = f"{a_1st_group}.{uuid_attr}"
        self.assertTrue(cmds.objExists(uuid_attr_path))
        result = cmds.getAttr(uuid_attr_path)
        self.assertEqual(expected, result)

        # A 2nd group
        a_2nd_group = maya_test_tools.create_group(name="a_2nd_group")
        mocked_driver = "mockedDriver"
        expected = f"{root_module_uuid}-{mocked_driver}-unknown"
        result = tools_rig_utils.add_driver_uuid_attr(
            target_driver=a_2nd_group,
            module_uuid=root_module_uuid,
            driver_type=mocked_driver,
            proxy_purpose=None,
        )
        self.assertEqual(expected, result)

        # A 3rd group
        a_3rd_group = maya_test_tools.create_group(name="a_3rd_group")
        mocked_purpose = "mockedPurpose"
        expected = f"{root_module_uuid}-unknown-{mocked_purpose}"
        result = tools_rig_utils.add_driver_uuid_attr(
            target_driver=a_3rd_group,
            module_uuid=root_module_uuid,
            driver_type=None,
            proxy_purpose=mocked_purpose,
        )
        self.assertEqual(expected, result)

    def test_find_drivers_from_joint_extra_manual_drivers(self):
        a_1st_valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        a_2nd_valid_uuid = "631b5e34-58af-48c3-80e0-c41fe7a56470"
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        a_1st_extra_driver = "generic"
        a_2nd_extra_driver = "mocked"
        a_1st_root_module.root_proxy.add_driver_type([a_1st_extra_driver, a_2nd_extra_driver])
        a_1st_root_module.root_proxy.set_uuid(a_1st_valid_uuid)
        a_2nd_root_module.root_proxy.set_uuid(a_2nd_valid_uuid)
        a_2nd_root_module.root_proxy.set_initial_position(x=10)
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        # Get Useful data
        a_1st_proxy_purpose = a_1st_root_module.root_proxy.get_meta_purpose()
        # Create Project and Build
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()
        a_project.build_rig()

        a_1st_group = maya_test_tools.create_group(name="a_1st_group")
        a_1st_root_module._add_driver_uuid_attr(  # Uses "tools_rig_utils.add_driver_uuid_attr()"
            target_driver=a_1st_group, driver_type=a_1st_extra_driver, proxy_purpose=a_1st_proxy_purpose
        )
        a_2nd_group = maya_test_tools.create_group(name="a_2nd_group")
        a_1st_root_module._add_driver_uuid_attr(  # Uses "tools_rig_utils.add_driver_uuid_attr()"
            target_driver=a_2nd_group, driver_type=a_2nd_extra_driver, proxy_purpose=a_1st_proxy_purpose
        )

        # Get 1st Root Joint
        root_1st_jnt = tools_rig_utils.find_joint_from_uuid(uuid_string=a_1st_valid_uuid)

        expected = {
            "fk": "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL",
            "generic": "|a_1st_group",
            "mocked": "|a_2nd_group",
        }
        result = tools_rig_utils.find_drivers_from_joint(source_joint=root_1st_jnt)
        self.assertEqual(expected, result)
        expected = {}
        result = tools_rig_utils.find_drivers_from_joint(source_joint=root_1st_jnt, skip_block_drivers=True)
        self.assertEqual(expected, result)
        cmds.delete(a_1st_group)
        expected = {
            "fk": "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL",
            "generic": "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_JNT_driver",
            "mocked": "|a_2nd_group",
        }
        result = tools_rig_utils.find_drivers_from_joint(
            source_joint=root_1st_jnt, skip_block_drivers=False, create_missing_generic=True
        )
        self.assertEqual(expected, result)

        # Get 2nd Root Joint
        root_2nd_jnt = tools_rig_utils.find_joint_from_uuid(uuid_string=a_2nd_valid_uuid)
        expected = {
            "fk": "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_secondRoot_offset|C_secondRoot_parentOffset|C_secondRoot_CTRL"
        }
        result = tools_rig_utils.find_drivers_from_joint(source_joint=root_2nd_jnt)
        self.assertEqual(expected, result)
        expected = {}
        result = tools_rig_utils.find_drivers_from_joint(source_joint=root_2nd_jnt, skip_block_drivers=True)
        self.assertEqual(expected, result)

    def test_find_object_with_attr(self):
        a_1st_cube = maya_test_tools.create_poly_cube(name="a_1st_cube")
        a_2nd_cube = maya_test_tools.create_poly_cube(name="a_2nd_cube")
        a_1st_lookup_attr = "lookUpAttr1st"
        a_2nd_lookup_attr = "lookUpAttr2nd"
        cmds.addAttr(a_1st_cube, longName=a_1st_lookup_attr, attributeType="bool")
        cmds.addAttr(a_2nd_cube, longName=a_2nd_lookup_attr, attributeType="double")

        expected = "|a_1st_cube"
        result = tools_rig_utils.find_object_with_attr(attr_name=a_1st_lookup_attr)
        self.assertEqual(expected, result)
        expected = "|a_2nd_cube"
        result = tools_rig_utils.find_object_with_attr(attr_name=a_2nd_lookup_attr)
        self.assertEqual(expected, result)

    def test_find_object_with_attr_obj_type(self):
        a_multiply_divide_node = cmds.createNode("multiplyDivide", name="a_multiply_divide_node")
        a_2nd_cube = maya_test_tools.create_poly_cube(name="a_2nd_cube")
        a_1st_lookup_attr = "lookUpAttr1stShape"
        a_2nd_lookup_attr = "lookUpAttr2nd"
        cmds.addAttr(a_multiply_divide_node, longName=a_1st_lookup_attr, attributeType="bool")  # Shape, not a transform
        cmds.addAttr(a_2nd_cube, longName=a_2nd_lookup_attr, attributeType="double")

        expected = None
        result = tools_rig_utils.find_object_with_attr(attr_name=a_1st_lookup_attr, transform_lookup="transform")
        self.assertEqual(expected, result)
        expected = "a_multiply_divide_node"
        result = tools_rig_utils.find_object_with_attr(attr_name=a_1st_lookup_attr, obj_type="multiplyDivide")
        self.assertEqual(expected, result)
        expected = "|a_2nd_cube"
        result = tools_rig_utils.find_object_with_attr(attr_name=a_2nd_lookup_attr)
        self.assertEqual(expected, result)

    def test_find_object_with_attr_lookup_list(self):
        a_1st_cube = maya_test_tools.create_poly_cube(name="a_1st_cube")
        a_2nd_cube = maya_test_tools.create_poly_cube(name="a_2nd_cube")
        a_3rd_cube = maya_test_tools.create_poly_cube(name="a_3rd_cube")
        a_1st_lookup_attr = "lookUpAttr1st"
        a_2nd_lookup_attr = "lookUpAttr2nd"
        a_3rd_lookup_attr = "lookUpAttr3rd"
        cmds.addAttr(a_1st_cube, longName=a_1st_lookup_attr, attributeType="bool")
        cmds.addAttr(a_2nd_cube, longName=a_2nd_lookup_attr, attributeType="bool")
        cmds.addAttr(a_3rd_cube, longName=a_3rd_lookup_attr, attributeType="bool")

        all_cubes = [a_1st_cube, a_2nd_cube, a_3rd_cube]
        only_2nd_and_3rd = [a_2nd_cube, a_3rd_cube]

        expected = "|a_1st_cube"
        result = tools_rig_utils.find_object_with_attr(attr_name=a_1st_lookup_attr, lookup_list=all_cubes)
        self.assertEqual(expected, result)
        expected = None
        result = tools_rig_utils.find_object_with_attr(attr_name=a_1st_lookup_attr, lookup_list=[a_2nd_cube])
        self.assertEqual(expected, result)
        expected = "|a_2nd_cube"
        result = tools_rig_utils.find_object_with_attr(attr_name=a_2nd_lookup_attr, lookup_list=[a_2nd_cube])
        self.assertEqual(expected, result)
        expected = "|a_2nd_cube"
        result = tools_rig_utils.find_object_with_attr(attr_name=a_2nd_lookup_attr, lookup_list=only_2nd_and_3rd)
        self.assertEqual(expected, result)

    def test_find_root_group_proxy(self):
        expected = None
        result = tools_rig_utils.find_root_group_proxy()
        self.assertEqual(expected, result)

        a_group = maya_test_tools.create_group(name="a_group")
        cmds.addAttr(a_group, longName=tools_rig_const.RiggerConstants.REF_ATTR_ROOT_PROXY, attributeType="bool")

        expected = "|a_group"
        result = tools_rig_utils.find_root_group_proxy()
        self.assertEqual(expected, result)

    def test_find_root_group_rig(self):
        expected = None
        result = tools_rig_utils.find_root_group_rig()
        self.assertEqual(expected, result)

        a_group = maya_test_tools.create_group(name="a_group")
        cmds.addAttr(a_group, longName=tools_rig_const.RiggerConstants.REF_ATTR_ROOT_RIG, attributeType="bool")

        expected = "|a_group"
        result = tools_rig_utils.find_root_group_rig()
        self.assertEqual(expected, result)

    def test_find_ctrl_global(self):
        expected = None
        result = tools_rig_utils.find_ctrl_global()
        self.assertEqual(expected, result)

        a_group = maya_test_tools.create_group(name="a_group")
        cmds.addAttr(a_group, longName=tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL, attributeType="bool")

        expected = None
        result = tools_rig_utils.find_ctrl_global(use_transform=False)  # Expecting a curve, none found
        self.assertEqual(expected, result)
        expected = "|a_group"
        result = tools_rig_utils.find_ctrl_global(use_transform=True)  # Accepts transforms
        self.assertEqual(expected, result)

        a_curve = cmds.circle(name="a_curve", ch=False)[0]
        cmds.addAttr(a_curve, longName=tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL, attributeType="bool")
        expected = "|a_curve"
        result = tools_rig_utils.find_ctrl_global(use_transform=False)
        self.assertEqual(expected, result)
        expected = "|a_curve"
        result = tools_rig_utils.find_ctrl_global(use_transform=True)
        self.assertEqual(expected, result)

    def test_find_ctrl_global_offset(self):
        expected = None
        result = tools_rig_utils.find_ctrl_global_offset()
        self.assertEqual(expected, result)

        a_group = maya_test_tools.create_group(name="a_group")
        cmds.addAttr(
            a_group, longName=tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_OFFSET, attributeType="bool"
        )

        expected = None
        result = tools_rig_utils.find_ctrl_global_offset(use_transform=False)  # Expecting a curve, none found
        self.assertEqual(expected, result)
        expected = "|a_group"
        result = tools_rig_utils.find_ctrl_global_offset(use_transform=True)  # Accepts transforms
        self.assertEqual(expected, result)

        a_curve = cmds.circle(name="a_curve", ch=False)[0]
        cmds.addAttr(
            a_curve, longName=tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_OFFSET, attributeType="bool"
        )
        expected = "|a_curve"
        result = tools_rig_utils.find_ctrl_global_offset(use_transform=False)
        self.assertEqual(expected, result)
        expected = "|a_curve"
        result = tools_rig_utils.find_ctrl_global_offset(use_transform=True)
        self.assertEqual(expected, result)

    def test_find_ctrl_global_proxy(self):
        expected = None
        result = tools_rig_utils.find_ctrl_global_proxy()
        self.assertEqual(expected, result)

        a_group = maya_test_tools.create_group(name="a_group")
        cmds.addAttr(a_group, longName=tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_PROXY, attributeType="bool")

        expected = None
        result = tools_rig_utils.find_ctrl_global_proxy(use_transform=False)  # Expecting a curve, none found
        self.assertEqual(expected, result)
        expected = "|a_group"
        result = tools_rig_utils.find_ctrl_global_proxy(use_transform=True)  # Accepts transforms
        self.assertEqual(expected, result)

        a_curve = cmds.circle(name="a_curve", ch=False)[0]
        cmds.addAttr(a_curve, longName=tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_PROXY, attributeType="bool")
        expected = "|a_curve"
        result = tools_rig_utils.find_ctrl_global_proxy(use_transform=False)
        self.assertEqual(expected, result)
        expected = "|a_curve"
        result = tools_rig_utils.find_ctrl_global_proxy(use_transform=True)
        self.assertEqual(expected, result)

    def test_find_skeleton_group(self):
        expected = None
        result = tools_rig_utils.find_skeleton_group()
        self.assertEqual(expected, result)

        a_group = maya_test_tools.create_group(name="a_group")
        cmds.addAttr(a_group, longName=tools_rig_const.RiggerConstants.REF_ATTR_SKELETON, attributeType="bool")

        expected = "|a_group"
        result = tools_rig_utils.find_skeleton_group()
        self.assertEqual(expected, result)

    def test_find_setup_group(self):
        expected = None
        result = tools_rig_utils.find_setup_group()
        self.assertEqual(expected, result)

        a_group = maya_test_tools.create_group(name="a_group")
        cmds.addAttr(a_group, longName=tools_rig_const.RiggerConstants.REF_ATTR_SETUP, attributeType="bool")

        expected = "|a_group"
        result = tools_rig_utils.find_setup_group()
        self.assertEqual(expected, result)

    def test_find_vis_lines_from_uuid(self):
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        a_1st_proxy_uuid = a_1st_root_module.root_proxy.get_uuid()
        a_2nd_proxy_uuid = a_2nd_root_module.root_proxy.get_uuid()
        # Configure Proxies
        a_1st_root_module.root_proxy.set_parent_uuid(a_2nd_proxy_uuid)
        a_2nd_root_module.root_proxy.set_initial_position(x=10)
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()  # Only available during proxy step

        expected = ("|rig_proxy|visualization_lines|C_root_to_C_secondRoot",)
        result = tools_rig_utils.find_vis_lines_from_uuid(parent_uuid=a_2nd_proxy_uuid, child_uuid=a_1st_proxy_uuid)
        self.assertEqual(expected, result)

    def test_find_or_create_joint_automation_group(self):
        expected = "|jointAutomation"
        result = tools_rig_utils.find_or_create_joint_automation_group()
        self.assertEqual(expected, result)

    def test_find_drivers_from_module(self):
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        # Configure Proxies
        a_2nd_root_module.root_proxy.set_initial_position(x=10)
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        expected = ["|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL"]
        result = tools_rig_utils.find_drivers_from_module(source_uuid=a_1st_root_module.get_uuid())
        self.assertEqual(expected, result)

    def test_find_drivers_from_module_manual_extra_drivers(self):
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        # Configure Proxies
        a_1st_extra_driver = "generic"
        a_2nd_extra_driver = "mocked"
        a_3rd_extra_driver = "third"
        a_1st_root_module.root_proxy.add_driver_type([a_1st_extra_driver, a_2nd_extra_driver])
        a_2nd_root_module.root_proxy.set_initial_position(x=10)
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        # Get Useful data
        a_1st_proxy_purpose = a_1st_root_module.root_proxy.get_meta_purpose()
        a_1st_root_module_uuid = a_1st_root_module.get_uuid()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        # ----------------------------------------- Create -----------------------------------------
        # Create extra drivers (manually)
        a_custom_purpose = "customPurpose"
        a_1st_group = maya_test_tools.create_group(name="a_1st_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_1st_group, driver_type=a_1st_extra_driver, proxy_purpose=a_1st_proxy_purpose
        )
        a_2nd_group = maya_test_tools.create_group(name="a_2nd_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_2nd_group, driver_type=a_2nd_extra_driver, proxy_purpose=a_1st_proxy_purpose
        )
        a_3rd_group = maya_test_tools.create_group(name="a_3rd_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_3rd_group, driver_type=a_3rd_extra_driver, proxy_purpose="randomPurpose"
        )
        a_4th_group = maya_test_tools.create_group(name="a_4th_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_4th_group, driver_type="randomDriver", proxy_purpose=a_custom_purpose
        )
        a_5th_group = maya_test_tools.create_group(name="a_5th_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_5th_group, driver_type="randomDriver", proxy_purpose="randomPurpose"
        )
        a_6th_group = maya_test_tools.create_group(name="a_6th_group")
        a_1st_root_module._add_driver_uuid_attr(target_driver=a_6th_group, driver_type=None, proxy_purpose=None)

        # ------------------------------------------ Test ------------------------------------------
        # No filters, should return all drivers
        expected = [
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL",
            "|a_1st_group",
            "|a_2nd_group",
            "|a_3rd_group",
            "|a_4th_group",
            "|a_5th_group",
            "|a_6th_group",
        ]
        result = tools_rig_utils.find_drivers_from_module(source_uuid=a_1st_root_module_uuid)
        self.assertEqual(expected, result)

        # Only Generic drivers (a_1st_extra_driver)
        expected = ["|a_1st_group"]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module_uuid, filter_driver_type=a_1st_extra_driver
        )
        self.assertEqual(expected, result)

        # Only Default Purposes (a_1st_proxy_purpose)
        expected = ["|a_4th_group"]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module_uuid, filter_driver_purpose=a_custom_purpose
        )
        self.assertEqual(expected, result)

    def test_find_drivers_from_module_filter_driver_type(self):
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        # Configure Proxies
        a_1st_extra_driver = "generic"
        a_2nd_extra_driver = "mocked"
        a_1st_root_module.root_proxy.add_driver_type([a_1st_extra_driver, a_2nd_extra_driver])
        a_2nd_root_module.root_proxy.set_initial_position(x=10)
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        # Get Useful data
        a_1st_proxy_purpose = a_1st_root_module.root_proxy.get_meta_purpose()
        a_1st_root_module_uuid = a_1st_root_module.get_uuid()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        # ----------------------------------------- Create -----------------------------------------
        # Create extra drivers (manually)
        a_1st_group = maya_test_tools.create_group(name="a_1st_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_1st_group, driver_type=a_1st_extra_driver, proxy_purpose=a_1st_proxy_purpose
        )
        a_2nd_group = maya_test_tools.create_group(name="a_2nd_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_2nd_group, driver_type=a_2nd_extra_driver, proxy_purpose=a_1st_proxy_purpose
        )

        # ------------------------------------------ Test ------------------------------------------
        # No filters, should return all drivers
        expected = [
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL",
            "|a_1st_group",
            "|a_2nd_group",
        ]
        result = tools_rig_utils.find_drivers_from_module(source_uuid=a_1st_root_module_uuid)
        self.assertEqual(expected, result)

        # Only Generic drivers (a_1st_extra_driver)
        expected = ["|a_1st_group"]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module_uuid, filter_driver_type=a_1st_extra_driver
        )
        self.assertEqual(expected, result)

        # Only Mocked drivers (a_2nd_extra_driver)
        expected = ["|a_2nd_group"]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module_uuid, filter_driver_type=a_2nd_extra_driver
        )
        self.assertEqual(expected, result)

    def test_find_drivers_from_module_filter_purpose(self):
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        # Configure Proxies
        a_1st_extra_driver = "generic"
        a_2nd_extra_driver = "mocked"
        a_1st_root_module.root_proxy.add_driver_type([a_1st_extra_driver, a_2nd_extra_driver])
        a_2nd_root_module.root_proxy.set_initial_position(x=10)
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        # Get Useful data
        a_1st_proxy_purpose = a_1st_root_module.root_proxy.get_meta_purpose()
        a_1st_root_module_uuid = a_1st_root_module.get_uuid()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        # ----------------------------------------- Create -----------------------------------------
        # Create extra drivers (manually)
        a_1st_custom_purpose = "mocked_purpose_one"
        a_2nd_custom_purpose = "mocked_purpose_two"
        a_1st_group = maya_test_tools.create_group(name="a_1st_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_1st_group, driver_type=a_1st_extra_driver, proxy_purpose=a_1st_custom_purpose
        )
        a_2nd_group = maya_test_tools.create_group(name="a_2nd_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_2nd_group, driver_type=a_2nd_extra_driver, proxy_purpose=a_2nd_custom_purpose
        )
        a_3rd_group = maya_test_tools.create_group(name="a_3rd_group")
        a_1st_root_module._add_driver_uuid_attr(
            target_driver=a_3rd_group, driver_type=a_2nd_extra_driver, proxy_purpose=a_1st_proxy_purpose
        )

        # ------------------------------------------ Test ------------------------------------------
        # No filters, should return all drivers (Test clear function is still functional)
        expected = [
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL",
            "|a_1st_group",
            "|a_2nd_group",
            "|a_3rd_group",
        ]
        result = tools_rig_utils.find_drivers_from_module(source_uuid=a_1st_root_module_uuid)
        self.assertEqual(expected, result)

        # Only Root Purpose drivers (a_1st_proxy_purpose)
        expected = [
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL",
            "|a_3rd_group",
        ]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module_uuid, filter_driver_purpose=a_1st_proxy_purpose
        )
        self.assertEqual(expected, result)

        # Only 1st Custom Purpose drivers (a_1st_custom_purpose)
        expected = ["|a_1st_group"]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module_uuid, filter_driver_purpose=a_1st_custom_purpose
        )
        self.assertEqual(expected, result)

        # Only 2nd Custom Purpose drivers (a_2nd_custom_purpose)
        expected = ["|a_2nd_group"]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module_uuid, filter_driver_purpose=a_2nd_custom_purpose
        )
        self.assertEqual(expected, result)

        # Only Mocked drivers with 2nd custom driver (The only one matching this is the "a_2nd_group")
        expected = ["|a_2nd_group"]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module_uuid,
            filter_driver_type=a_2nd_extra_driver,
            filter_driver_purpose=a_2nd_custom_purpose,
        )
        self.assertEqual(expected, result)

    # ------------------------------------------ Create functions ------------------------------------------
    def test_create_proxy_visualization_lines(self):
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_1st_proxy = a_generic_module.add_new_proxy()
        a_2nd_proxy = a_generic_module.add_new_proxy()
        a_3rd_proxy = a_generic_module.add_new_proxy()
        # Configure Proxies
        a_1st_proxy.set_name("first")
        a_2nd_proxy.set_name("second")
        a_2nd_proxy.set_initial_position(x=10)
        a_3rd_proxy.set_initial_position(x=20)
        # Create Hierarchy
        a_2nd_proxy.set_parent_uuid_from_proxy(a_1st_proxy)
        a_3rd_proxy.set_parent_uuid_from_proxy(a_2nd_proxy)
        # Build Module Proxy (No project)
        a_generic_module.build_proxy()

        # Run Function
        expected = [
            ("second_to_first", "second_cluster", "first_cluster"),
            ("proxy2_to_second", "proxy2_cluster", "second_cluster1"),
        ]
        result = tools_rig_utils.create_proxy_visualization_lines(
            proxy_list=a_generic_module.get_proxies(), lines_parent=None
        )
        self.assertEqual(expected, result)

    def test_create_proxy_visualization_lines_parented(self):
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_1st_proxy = a_generic_module.add_new_proxy()
        a_2nd_proxy = a_generic_module.add_new_proxy()
        a_3rd_proxy = a_generic_module.add_new_proxy()
        # Configure Proxies
        a_1st_proxy.set_name("first")
        a_2nd_proxy.set_name("second")
        a_2nd_proxy.set_initial_position(x=10)
        a_3rd_proxy.set_initial_position(x=20)
        # Create Hierarchy and Target Parent
        a_2nd_proxy.set_parent_uuid_from_proxy(a_1st_proxy)
        a_3rd_proxy.set_parent_uuid_from_proxy(a_2nd_proxy)
        target_parent = maya_test_tools.create_group(name="target_parent")
        # Build Module Proxy (No project)
        a_generic_module.build_proxy()

        # Run Function
        tools_rig_utils.create_proxy_visualization_lines(
            proxy_list=a_generic_module.get_proxies(), lines_parent=target_parent
        )
        expected = [
            "|target_parent|second_to_first",
            "|target_parent|second_cluster",
            "|target_parent|first_cluster",
            "|target_parent|proxy2_to_second",
            "|target_parent|proxy2_cluster",
            "|target_parent|second_cluster1",
        ]
        result = cmds.listRelatives(target_parent, children=True, fullPath=True)
        self.assertEqual(expected, result)

    def test_create_ctrl_rig_global(self):
        expected = "|global_CTRL"
        result = tools_rig_utils.create_ctrl_rig_global()
        self.assertEqual(expected, result)
        self.assertIsInstance(result, core_node.Node)
        expected = "|mocked_global"
        result = tools_rig_utils.create_ctrl_rig_global(name="mocked_global")
        self.assertEqual(expected, result)

    def test_create_root_group(self):
        expected = "|rig"
        result = tools_rig_utils.create_root_group(is_proxy=False)  # Default: is_proxy=False
        self.assertEqual(expected, result)
        self.assertIsInstance(result, core_node.Node)
        look_attr = tools_rig_const.RiggerConstants.REF_ATTR_ROOT_RIG
        look_attr_path = f"{expected}.{look_attr}"
        result = cmds.objExists(look_attr_path)
        self.assertTrue(result)

    def test_create_root_group_proxy(self):
        expected = "|rig_proxy"
        result = tools_rig_utils.create_root_group(is_proxy=True)  # Default: is_proxy=False
        self.assertEqual(expected, result)
        self.assertIsInstance(result, core_node.Node)
        look_attr = tools_rig_const.RiggerConstants.REF_ATTR_ROOT_PROXY
        look_attr_path = f"{expected}.{look_attr}"
        result = cmds.objExists(look_attr_path)
        self.assertTrue(result)

    def test_create_ctrl_proxy_global(self):
        expected = "|C_global_CTRL"
        result = tools_rig_utils.create_ctrl_global()
        self.assertEqual(expected, result)
        self.assertIsInstance(result, core_node.Node)
        look_attr = tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL
        look_attr_path = f"{expected}.{look_attr}"
        result = cmds.objExists(look_attr_path)
        self.assertTrue(result)

    def test_create_ctrl_proxy_global_alternative_prefix(self):
        expected = "|ABC_global_CTRL"
        result = tools_rig_utils.create_ctrl_global(prefix="ABC")
        self.assertEqual(expected, result)
        self.assertIsInstance(result, core_node.Node)
        look_attr = tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL
        look_attr_path = f"{expected}.{look_attr}"
        result = cmds.objExists(look_attr_path)
        self.assertTrue(result)

    def test_create_ctrl_global_offset(self):
        expected = "|C_globalOffset_CTRL"
        result = tools_rig_utils.create_ctrl_global_offset()
        self.assertEqual(expected, result)
        self.assertIsInstance(result, core_node.Node)
        look_attr = tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_OFFSET
        look_attr_path = f"{expected}.{look_attr}"
        result = cmds.objExists(look_attr_path)
        self.assertTrue(result)

    def test_create_ctrl_global_offset_alternative_prefix(self):
        expected = "|ABC_globalOffset_CTRL"
        result = tools_rig_utils.create_ctrl_global_offset(prefix="ABC")
        self.assertEqual(expected, result)
        self.assertIsInstance(result, core_node.Node)
        look_attr = tools_rig_const.RiggerConstants.REF_ATTR_CTRL_GLOBAL_OFFSET
        look_attr_path = f"{expected}.{look_attr}"
        result = cmds.objExists(look_attr_path)
        self.assertTrue(result)

    def test_create_utility_groups(self):
        expected = {}
        result = tools_rig_utils.create_utility_groups()  # Nothing activated
        self.assertEqual(expected, result)
        expected = {"geometryGroupLookupAttr": "|geometry"}
        result = tools_rig_utils.create_utility_groups(geometry=True)
        self.assertEqual(expected, result)
        expected = {"skeletonGroupLookupAttr": "|skeleton"}
        result = tools_rig_utils.create_utility_groups(skeleton=True)
        self.assertEqual(expected, result)
        expected = {"controlsGroupLookupAttr": "|controls"}
        result = tools_rig_utils.create_utility_groups(control=True)
        self.assertEqual(expected, result)
        expected = {"setupGroupLookupAttr": "|setup"}
        result = tools_rig_utils.create_utility_groups(setup=True)
        self.assertEqual(expected, result)
        expected = {"linesGroupLookupAttr": "|visualization_lines"}
        result = tools_rig_utils.create_utility_groups(line=True)
        self.assertEqual(expected, result)
        # All groups at the same time
        maya_test_tools.force_new_scene()
        expected = {
            "controlsGroupLookupAttr": "|controls",
            "geometryGroupLookupAttr": "|geometry",
            "linesGroupLookupAttr": "|visualization_lines",
            "setupGroupLookupAttr": "|setup",
            "skeletonGroupLookupAttr": "|skeleton",
        }
        result = tools_rig_utils.create_utility_groups(
            geometry=True, skeleton=True, control=True, setup=True, line=True
        )
        self.assertEqual(expected, result)

    def test_create_utility_groups_target_parent(self):
        target_parent = maya_test_tools.create_group(name="mocked_parent")
        expected = {}
        result = tools_rig_utils.create_utility_groups()  # Nothing activated
        self.assertEqual(expected, result)
        expected = {"geometryGroupLookupAttr": "|mocked_parent|geometry"}
        result = tools_rig_utils.create_utility_groups(geometry=True, target_parent=target_parent)
        self.assertEqual(expected, result)
        expected = {"skeletonGroupLookupAttr": "|mocked_parent|skeleton"}
        result = tools_rig_utils.create_utility_groups(skeleton=True, target_parent=target_parent)
        self.assertEqual(expected, result)
        expected = {"controlsGroupLookupAttr": "|mocked_parent|controls"}
        result = tools_rig_utils.create_utility_groups(control=True, target_parent=target_parent)
        self.assertEqual(expected, result)
        expected = {"setupGroupLookupAttr": "|mocked_parent|setup"}
        result = tools_rig_utils.create_utility_groups(setup=True, target_parent=target_parent)
        self.assertEqual(expected, result)
        expected = {"linesGroupLookupAttr": "|mocked_parent|visualization_lines"}
        result = tools_rig_utils.create_utility_groups(line=True, target_parent=target_parent)
        self.assertEqual(expected, result)
        # All groups at the same time
        maya_test_tools.force_new_scene()
        target_parent = maya_test_tools.create_group(name="mocked_parent")
        expected = {
            "controlsGroupLookupAttr": "|mocked_parent|controls",
            "geometryGroupLookupAttr": "|mocked_parent|geometry",
            "linesGroupLookupAttr": "|mocked_parent|visualization_lines",
            "setupGroupLookupAttr": "|mocked_parent|setup",
            "skeletonGroupLookupAttr": "|mocked_parent|skeleton",
        }
        result = tools_rig_utils.create_utility_groups(
            geometry=True, skeleton=True, control=True, setup=True, line=True, target_parent=target_parent
        )
        self.assertEqual(expected, result)

    # ------------------------------------------ Misc functions ------------------------------------------
    def test_get_automation_group_setup_group(self):
        tools_rig_utils.find_setup_group()
        expected = "|generalAutomation"
        result = tools_rig_utils.get_automation_group()
        self.assertEqual(expected, result)
        expected_in_scene = "generalAutomation"
        found_in_scene = cmds.ls(typ="transform")
        self.assertIn(expected_in_scene, found_in_scene)

    def test_parent_proxies(self):
        a_1st_valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        a_2nd_valid_uuid = "631b5e34-58af-48c3-80e0-c41fe7a56470"
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_1st_proxy = a_generic_module.add_new_proxy()
        a_2nd_proxy = a_generic_module.add_new_proxy()
        a_1st_proxy.set_name("firstProxy")
        a_2nd_proxy.set_name("secondProxy")
        a_1st_proxy.set_uuid(a_1st_valid_uuid)
        a_2nd_proxy.set_uuid(a_2nd_valid_uuid)
        a_2nd_proxy.set_parent_uuid_from_proxy(a_1st_proxy)  # Required so parenting happens
        a_generic_module.build_proxy()
        expected = [
            "|secondProxy_offset|secondProxy|locShape",
            "|firstProxy_offset|firstProxy|locShape",
            "|secondProxy_offset|secondProxy|locShapeOrig",
            "|firstProxy_offset|firstProxy|locShapeOrig",
            "|secondProxy_offset|secondProxy|sphereShape",
            "|firstProxy_offset|firstProxy|sphereShape",
            "|secondProxy_offset|secondProxy|sphereShapeOrig",
            "|firstProxy_offset|firstProxy|sphereShapeOrig",
        ]
        result = cmds.ls(typ="nurbsCurve", long=True)
        self.assertEqual(expected, result)
        tools_rig_utils.parent_proxies(proxy_list=a_generic_module.proxies)
        expected = [
            "|firstProxy_offset|firstProxy|secondProxy_offset|secondProxy|locShape",
            "|firstProxy_offset|firstProxy|locShape",
            "|firstProxy_offset|firstProxy|secondProxy_offset|secondProxy|locShapeOrig",
            "|firstProxy_offset|firstProxy|locShapeOrig",
            "|firstProxy_offset|firstProxy|secondProxy_offset|secondProxy|sphereShape",
            "|firstProxy_offset|firstProxy|sphereShape",
            "|firstProxy_offset|firstProxy|secondProxy_offset|secondProxy|sphereShapeOrig",
            "|firstProxy_offset|firstProxy|sphereShapeOrig",
        ]
        result = cmds.ls(typ="nurbsCurve", long=True)
        self.assertEqual(expected, result)

    def test_get_proxy_offset(self):
        a_1st_valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        a_2nd_valid_uuid = "631b5e34-58af-48c3-80e0-c41fe7a56470"
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_1st_proxy = a_generic_module.add_new_proxy()
        a_2nd_proxy = a_generic_module.add_new_proxy()
        a_1st_proxy.set_name("firstProxy")
        a_2nd_proxy.set_name("secondProxy")
        a_1st_proxy.set_uuid(a_1st_valid_uuid)
        a_2nd_proxy.set_uuid(a_2nd_valid_uuid)
        a_2nd_proxy.set_parent_uuid_from_proxy(a_1st_proxy)  # Required so parenting happens
        proxy_data_list = a_generic_module.build_proxy()

        expected_offsets = ["|firstProxy_offset", "|secondProxy_offset"]
        result_offsets = []
        for proxy_data in proxy_data_list:
            proxy_path = proxy_data.get_long_name()
            offset = tools_rig_utils.get_proxy_offset(proxy_name=proxy_path)
            result_offsets.append(offset)

        self.assertEqual(expected_offsets, result_offsets)

    def test_get_meta_purpose_from_dict(self):
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_1st_proxy = a_generic_module.add_new_proxy()
        a_2nd_proxy = a_generic_module.add_new_proxy()
        a_1st_proxy.set_name("firstProxy")
        a_2nd_proxy.set_name("secondProxy")
        a_2nd_proxy.set_meta_purpose("mocked_purpose")

        expected = None
        result = tools_rig_utils.get_meta_purpose_from_dict(metadata_dict=a_1st_proxy.get_metadata())
        self.assertEqual(expected, result)
        expected = "mocked_purpose"
        result = tools_rig_utils.get_meta_purpose_from_dict(metadata_dict=a_2nd_proxy.get_metadata())
        self.assertEqual(expected, result)

    def test_get_automation_group_basic(self):
        expected = "|generalAutomation"
        result = tools_rig_utils.get_automation_group()
        self.assertEqual(expected, result)
        expected_in_scene = "generalAutomation"
        found_in_scene = cmds.ls(typ="transform")
        self.assertIn(expected_in_scene, found_in_scene)

    def test_get_automation_group_default_setup(self):
        rig_grp = tools_rig_utils.create_root_group()
        tools_rig_utils.create_utility_groups(setup=True, target_parent=rig_grp)
        expected = "|rig|setup|generalAutomation"
        result = tools_rig_utils.get_automation_group()
        self.assertEqual(expected, result)
        expected = "|rig|setup|mockedName"
        result = tools_rig_utils.get_automation_group(name="mockedName")
        self.assertEqual(expected, result)
        expected = "|rig|setup|mockedName|mockedSubgroup"
        result = tools_rig_utils.get_automation_group(name="mockedName", subgroup="mockedSubgroup")
        self.assertEqual(expected, result)

    def test_get_driven_joint(self):
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        # Configure Proxies
        a_2nd_root_module.root_proxy.set_initial_position(x=10)
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        # Get Useful data
        a_1st_proxy_uuid = a_1st_root_module.root_proxy.get_uuid()
        a_2nd_proxy_uuid = a_2nd_root_module.root_proxy.get_uuid()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for the joints to be created
        expected = "|C_root_JNT_driven"
        result = tools_rig_utils.get_driven_joint(uuid_string=a_1st_proxy_uuid)
        self.assertEqual(expected, result)
        expected = ["C_root_JNT_driven_parentConstraint1"]
        result = cmds.listRelatives(result, typ="parentConstraint")
        self.assertEqual(expected, result)
        expected = "|C_secondRoot_JNT_mocked"
        result = tools_rig_utils.get_driven_joint(
            uuid_string=a_2nd_proxy_uuid, suffix="mocked", constraint_to_source=False
        )
        self.assertEqual(expected, result)
        expected = None
        result = cmds.listRelatives(result, typ="parentConstraint")
        self.assertEqual(expected, result)

    def test_get_drivers_list_from_joint(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for the joints to be created
        source_joint = tools_rig_utils.find_joint_from_uuid(a_root_module.root_proxy.get_uuid())
        expected = ["block", "fk"]
        result = tools_rig_utils.get_drivers_list_from_joint(source_joint=source_joint)
        self.assertEqual(expected, result)
        # Test another value
        mocked_drivers = str(["mocked_one", "mocked_two", "mocked_three"])
        cmds.setAttr(
            f"{source_joint}.{tools_rig_const.RiggerConstants.ATTR_JOINT_DRIVERS}", mocked_drivers, typ="string"
        )
        expected = ["mocked_one", "mocked_two", "mocked_three"]
        result = tools_rig_utils.get_drivers_list_from_joint(source_joint=source_joint)
        self.assertEqual(expected, result)

    def test_add_driver_to_joint(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for the joints to be created
        source_joint = tools_rig_utils.find_joint_from_uuid(a_root_module.root_proxy.get_uuid())
        expected = ["block", "fk"]
        result = tools_rig_utils.get_drivers_list_from_joint(source_joint=source_joint)
        self.assertEqual(expected, result)
        # Test adding more drivers value
        mocked_drivers = ["mocked_one", "mocked_two", "mocked_three"]
        tools_rig_utils.add_driver_to_joint(target_joint=source_joint, new_drivers=mocked_drivers)
        expected = ["block", "fk", "mocked_one", "mocked_two", "mocked_three"]
        result = tools_rig_utils.get_drivers_list_from_joint(source_joint=source_joint)
        self.assertEqual(expected, result)

    def test_get_driver_uuids_from_joint(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for the joints to be created
        source_joint = tools_rig_utils.find_joint_from_uuid(a_root_module.root_proxy.get_uuid())
        module_uuid = a_root_module.get_uuid()
        expected = {"block": f"{module_uuid}-block-root", "fk": f"{module_uuid}-fk-root"}
        result = tools_rig_utils.get_driver_uuids_from_joint(source_joint=source_joint)
        self.assertEqual(expected, result)
        expected = [f"{module_uuid}-block-root", f"{module_uuid}-fk-root"]
        result = tools_rig_utils.get_driver_uuids_from_joint(source_joint=source_joint, as_list=True)
        self.assertEqual(expected, result)

    def test_get_generic_driver(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for the joints to be created
        source_joint = tools_rig_utils.find_joint_from_uuid(a_root_module.root_proxy.get_uuid())
        expected = None
        result = tools_rig_utils.get_generic_driver(source_joint=source_joint, add_missing_driver=False)
        self.assertEqual(expected, result)
        expected = "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_JNT_driver"
        result = tools_rig_utils.get_generic_driver(source_joint=source_joint, add_missing_driver=True)
        self.assertEqual(expected, result)

    def test_get_generic_driver_transform_available(self):
        a_root_module = tools_mod_root.ModuleRoot()
        _generic_driver = tools_rig_const.RiggerDriverTypes.GENERIC
        _root_purpose = a_root_module.root_proxy.get_meta_purpose()
        a_root_module.root_proxy.add_driver_type(_generic_driver)
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        # ----------------------------------------- Create -----------------------------------------
        # Create extra drivers (manually)
        a_generic_group = maya_test_tools.create_group(name="a_generic_group")
        a_root_module._add_driver_uuid_attr(
            target_driver=a_generic_group, driver_type=_generic_driver, proxy_purpose=_root_purpose
        )

        # ------------------------------------------ Test ------------------------------------------
        source_joint = tools_rig_utils.find_joint_from_uuid(a_root_module.root_proxy.get_uuid())
        expected = "|a_generic_group"
        result = tools_rig_utils.get_generic_driver(source_joint=source_joint, add_missing_driver=False)
        self.assertEqual(expected, result)
        result = tools_rig_utils.get_generic_driver(source_joint=source_joint, add_missing_driver=True)
        self.assertEqual(expected, result)

    def test_connect_supporting_driver(self):
        a_root_module = tools_mod_root.ModuleRoot()
        _generic_driver = tools_rig_const.RiggerDriverTypes.GENERIC
        _root_purpose = a_root_module.root_proxy.get_meta_purpose()
        a_root_module.root_proxy.add_driver_type(_generic_driver)
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        # ----------------------------------------- Create -----------------------------------------
        # Create extra drivers (manually)
        parent_driver = maya_test_tools.create_group(name="a_parent_driver")
        a_1st_child_driver = maya_test_tools.create_group(name="a_1st_child_driver")
        a_2nd_child_driver = maya_test_tools.create_group(name="a_2nd_child_driver")
        driver_uuid = a_root_module._add_driver_uuid_attr(
            target_driver=parent_driver, driver_type=_generic_driver, proxy_purpose=_root_purpose
        )
        _child_driver_attr = tools_rig_const.RiggerConstants.ATTR_DRIVER_CHILD

        # ------------------------------------------ Test ------------------------------------------
        # First Supporting Driver
        expected_attr = f"a_1st_child_driver.{_child_driver_attr}"
        result_attr = tools_rig_utils.connect_supporting_driver(
            source_parent_driver=parent_driver, target_child_driver=a_1st_child_driver
        )
        self.assertEqual(expected_attr, result_attr)
        self.assertTrue(cmds.objExists(f"{a_1st_child_driver}.{_child_driver_attr}"))
        self.assertTrue(cmds.objExists(result_attr))
        result_value = cmds.getAttr(result_attr)
        self.assertEqual(driver_uuid, result_value)
        # Second Supporting Driver
        expected_attr = f"a_2nd_child_driver.{_child_driver_attr}"
        result_attr = tools_rig_utils.connect_supporting_driver(
            source_parent_driver=parent_driver, target_child_driver=a_2nd_child_driver
        )
        self.assertEqual(expected_attr, result_attr)
        self.assertTrue(cmds.objExists(f"{a_2nd_child_driver}.{_child_driver_attr}"))
        self.assertTrue(cmds.objExists(result_attr))
        result_value = cmds.getAttr(result_attr)
        self.assertEqual(driver_uuid, result_value)

    def test_get_supporting_drivers(self):
        a_root_module = tools_mod_root.ModuleRoot()
        _generic_driver = tools_rig_const.RiggerDriverTypes.GENERIC
        _root_purpose = a_root_module.root_proxy.get_meta_purpose()
        a_root_module.root_proxy.add_driver_type(_generic_driver)
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        # ----------------------------------------- Create -----------------------------------------
        # Create extra drivers (manually)
        parent_driver = maya_test_tools.create_group(name="a_parent_driver")
        a_1st_child_driver = maya_test_tools.create_group(name="a_1st_child_driver")
        a_2nd_child_driver = maya_test_tools.create_group(name="a_2nd_child_driver")
        a_root_module._add_driver_uuid_attr(
            target_driver=parent_driver, driver_type=_generic_driver, proxy_purpose=_root_purpose
        )

        # ------------------------------------------ Test ------------------------------------------
        # First Supporting Driver
        tools_rig_utils.connect_supporting_driver(
            source_parent_driver=parent_driver, target_child_driver=a_1st_child_driver
        )
        tools_rig_utils.connect_supporting_driver(
            source_parent_driver=parent_driver, target_child_driver=a_2nd_child_driver
        )
        expected = ["|a_2nd_child_driver", "|a_1st_child_driver"]
        result = tools_rig_utils.get_supporting_drivers(source_driver=parent_driver)
        self.assertEqual(expected, result)

    def test_update_uuids_in_dict_with_nested_structure(self):
        data = {
            "object1": {
                "uuid": "123",
                "children": [{"uuid": "456", "name": "Child1"}, {"uuid": "789", "name": "Child2"}],
            }
        }
        uuid_mapping = {"123": "abc", "456": "def", "789": "ghi"}
        expected = {
            "object1": {
                "uuid": "abc",
                "children": [{"uuid": "def", "name": "Child1"}, {"uuid": "ghi", "name": "Child2"}],
            }
        }
        result = tools_rig_utils.update_uuids_in_dict(data, uuid_mapping)
        self.assertEqual(expected, result)

    def test_update_uuids_in_dict_with_non_uuid_values(self):
        data = ["123", "456", "not-a-uuid"]
        uuid_mapping = {"123": "abc", "456": "def"}
        expected = ["abc", "def", "not-a-uuid"]
        result = tools_rig_utils.update_uuids_in_dict(data, uuid_mapping)
        self.assertEqual(expected, result)

    def test_create_twist_setup_uses_native_nodes(self):
        """Tests that auto-rigger twist setups use native Maya networks."""
        start_joint = cmds.joint(name="L_start_JNT")
        cmds.joint(name="L_end_JNT", position=(10, 0, 0))
        twist_joints = []
        for index in range(3):
            twist_joint = cmds.duplicate(start_joint, parentOnly=True, name=f"L_twist0{index + 1}_JNT")[0]
            cmds.parent(twist_joint, start_joint)
            twist_joints.append(twist_joint)

        setup_nodes = tools_rig_utils.create_twist_setup(
            twist_jnt_list=twist_joints,
            mid_joints=2,
            side="L",
        )

        expected_weights = [1 / 3, 2 / 3, 1.0]
        self.assertEqual(3, len(setup_nodes))
        for index, setup_node in enumerate(setup_nodes):
            twist_joint = twist_joints[index]
            self.assertEqual("network", cmds.nodeType(str(setup_node)))
            self.assertAlmostEqual(expected_weights[index], cmds.getAttr(f"{setup_node}.twist"))
            expected = [str(setup_node)]
            result = cmds.listConnections(
                f"{twist_joint}.{core_rigging.RiggingConstants.ATTR_TWIST_SETUP}",
                source=True,
                destination=False,
            )
            self.assertEqual(expected, result)
