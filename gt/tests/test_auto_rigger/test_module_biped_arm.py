import unittest
import logging
import sys
import os

import gt.tools.auto_rigger.modules.module_biped_arm as module_arm
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.tests.maya_test_tools.maya_test_tools as maya_test_tools
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.package_setup.package_tools_maya_plugins as tools_maya_plugins
import maya.cmds as cmds

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


class TestModuleBipedArm(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        tools_maya_plugins.load_startup_plugins()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)

    def test_module_biped_arm_inheritance(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        result = isinstance(arm_module_instance, tools_rig_frm.ModuleGeneric)
        expected = True
        self.assertEqual(expected, result)

    def test_module_arm_inheritance_passthrough(self):
        arm_module_instance = module_arm.ModuleBipedArm(
            name="mocked_arm", prefix="mocked_prefix", suffix="mocked_suffix"
        )
        result = arm_module_instance.name
        expected = "mocked_arm"
        self.assertEqual(expected, result)
        result = arm_module_instance.prefix
        expected = "mocked_prefix"
        self.assertEqual(expected, result)
        result = arm_module_instance.suffix
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_arm_basic_proxy_compliance(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        # Proxies Type
        result = type(arm_module_instance.proxies)
        expected = list
        self.assertEqual(expected, result, '"proxies" variable must be a list.')
        # Number of proxies
        result = len(arm_module_instance.proxies)
        expected = 4
        self.assertEqual(expected, result)
        # Proxy type (Proxies should only carry tools_rig_frm.Proxy objects)
        for proxy in arm_module_instance.proxies:
            message = f'An element in the proxies list is not a proxy instance. Issue object: "{str(proxy)}"'
            self.assertIsInstance(proxy, tools_rig_frm.Proxy, message)
        # Variable Names (Must end with "_proxy")
        proxy_vars = {
            key: value for key, value in vars(arm_module_instance).items() if isinstance(value, tools_rig_frm.Proxy)
        }
        for proxy_var_key in proxy_vars.keys():
            message = f'A proxy variables was not named correctly. Incorrect variable: "{str(proxy_var_key)}"'
            self.assertTrue(proxy_var_key.endswith("_proxy"), message)

    def test_module_arm_default_proxy_prefix(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        arm_prefix = arm_module_instance.get_prefix()
        expected = None
        self.assertEqual(expected, arm_prefix)

    def test_module_arm_default_proxy_suffix(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        arm_suffix = arm_module_instance.get_suffix()
        expected = None
        self.assertEqual(expected, arm_suffix)

    def test_module_arm_check_default_orientation(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        an_orientation_data = arm_module_instance.get_orientation_data()
        result = an_orientation_data.get_method()
        expected = "automatic"
        self.assertEqual(expected, result)

    def test_module_arm_proxy_names(self):
        arm_names = ["clavicle", "upperArm", "lowerArm", "hand"]
        arm_module_instance = module_arm.ModuleBipedArm()
        for proxy in arm_module_instance.proxies:
            result = proxy.get_name()
            self.assertEqual(arm_names[arm_module_instance.proxies.index(proxy)], result)

    def test_module_arm_meta_purpose_names(self):
        arm_names = ["clavicle", "upperArm", "lowerArm", "hand"]
        arm_module_instance = module_arm.ModuleBipedArm()
        for proxy in arm_module_instance.proxies:
            result = proxy.get_meta_purpose()
            self.assertEqual(arm_names[arm_module_instance.proxies.index(proxy)], result)

    def test_module_arm_clavicle_proxy_driver_types(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        result = arm_module_instance.clavicle_proxy.get_driver_types()
        expected = [tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        self.assertEqual(expected, result)

    def test_module_arm_upperarm_proxy_driver_types(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        result = arm_module_instance.upperarm_proxy.get_driver_types()
        expected = [tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        self.assertEqual(expected, result)

    def test_module_arm_lowerarm_proxy_driver_types(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        result = arm_module_instance.lowerarm_proxy.get_driver_types()
        expected = [
            tools_rig_const.RiggerDriverTypes.GENERIC,
            tools_rig_const.RiggerDriverTypes.FK,
            tools_rig_const.RiggerDriverTypes.IK,
        ]
        self.assertEqual(expected, result)

    def test_module_arm_hand_proxy_driver_types(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        result = arm_module_instance.hand_proxy.get_driver_types()
        expected = [
            tools_rig_const.RiggerDriverTypes.GENERIC,
            tools_rig_const.RiggerDriverTypes.FK,
            tools_rig_const.RiggerDriverTypes.IK,
            tools_rig_const.RiggerDriverTypes.SWITCH,
        ]
        self.assertEqual(expected, result)

    def test_module_arm_get_module_as_dict(self):
        # Default Module
        arm_module_instance = module_arm.ModuleBipedArm()
        a_arm_as_dict = arm_module_instance.get_module_as_dict()
        self.assertIsInstance(a_arm_as_dict, dict)
        expected_keys = sorted(
            [
                "active",
                "expanded",
                "auto_pole_vector",
                "clavicle_world",
                "create_twist_joints",
                "lowerarm_twist_joints",
                "module",
                "name",
                "orientation",
                "proxies",
                "rig_pose_clavicle_rot",
                "rig_pose_elbow_rot",
                "setup_name",
                "upperarm_twist_joints",
                "uuid",
            ]
        )
        result_keys = sorted(list(a_arm_as_dict.keys()))
        self.assertEqual(expected_keys, result_keys)
        expected_module_value = "ModuleBipedArm"
        result_module_value = a_arm_as_dict.get("module")
        self.assertEqual(expected_module_value, result_module_value)
        # Change Module and Test Module Level Serialization
        arm_module_instance.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")
        a_arm_as_dict = arm_module_instance.get_module_as_dict()
        self.assertIn("parent", a_arm_as_dict)
        # Transfer data to a new arm module
        a_2nd_arm_module = module_arm.ModuleBipedArm()
        a_2nd_arm_module.read_data_from_dict(a_arm_as_dict)
        expected = arm_module_instance.get_module_as_dict()
        result = a_2nd_arm_module.get_module_as_dict()
        self.assertEqual(expected, result)

    def test_module_arm_read_proxies_from_dict(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        arm_module_instance.clavicle_proxy.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")  # Changed the proxy
        a_arm_as_dict = arm_module_instance.get_module_as_dict()
        # Create a second module (new)
        a_2nd_arm_module = module_arm.ModuleBipedArm()
        a_2nd_arm_module.read_proxies_from_dict(a_arm_as_dict.get("proxies"))
        expected = arm_module_instance.clavicle_proxy.get_uuid()
        result = a_2nd_arm_module.clavicle_proxy.get_uuid()
        self.assertEqual(expected, result)

    def test_module_arm_build_proxy(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        proxy_data_list = arm_module_instance.build_proxy()
        # Check ProxyData objects
        for proxy_data in proxy_data_list:
            self.assertIsInstance(proxy_data, tools_rig_frm.ProxyData)
            self.assertTrue(cmds.objExists(proxy_data.get_long_name()))
        # Check Maya Scene
        expected_nodes = [
            "clavicle_offset",
            "clavicle",
            "upperArm_offset",
            "upperArm",
            "lowerArm_offset",
            "lowerArm",
            "hand_offset",
            "hand",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("clavicle.proxyUUID"))
        self.assertTrue(cmds.objExists("upperArm.proxyUUID"))
        self.assertTrue(cmds.objExists("lowerArm.proxyUUID"))
        self.assertTrue(cmds.objExists("hand.proxyUUID"))

    def test_module_arm_build_proxy_within_project(self):
        arm_module_instance = module_arm.ModuleBipedArm()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(arm_module_instance)
        a_project.build_proxy()
        expected_nodes = [
            "clavicle_offset",
            "clavicle",
            "upperArm_offset",
            "upperArm",
            "lowerArm_offset",
            "lowerArm",
            "hand_offset",
            "hand",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("clavicle.proxyUUID"))
        self.assertTrue(cmds.objExists("upperArm.proxyUUID"))
        self.assertTrue(cmds.objExists("lowerArm.proxyUUID"))
        self.assertTrue(cmds.objExists("hand.proxyUUID"))

    def test_module_arm_prefixes(self):
        a_lf_arm_module = module_arm.ModuleBipedArmLeft()
        a_proxy = a_lf_arm_module.get_prefix()
        expected = "L"
        self.assertEqual(expected, a_proxy)
        a_rt_arm_module = module_arm.ModuleBipedArmRight()
        a_proxy = a_rt_arm_module.get_prefix()
        expected = "R"
        self.assertEqual(expected, a_proxy)

    def test_module_arm_left_twists(self):
        a_lf_arm_module = module_arm.ModuleBipedArmLeft()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_lf_arm_module)
        a_project.build_proxy()
        a_project.build_skeleton()
        result = type(a_lf_arm_module.lowerarm_twist_joints)
        expected = list
        self.assertEqual(expected, result)
        result = len(a_lf_arm_module.lowerarm_twist_joints)
        expected = 3
        self.assertEqual(expected, result)
        result = type(a_lf_arm_module.upperarm_twist_joints)
        expected = list
        self.assertEqual(expected, result)
        result = len(a_lf_arm_module.upperarm_twist_joints)
        expected = 3
        self.assertEqual(expected, result)

    def test_module_arm_right_twists(self):
        a_rt_arm_module = module_arm.ModuleBipedArmRight()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_rt_arm_module)
        a_project.build_proxy()
        a_project.build_skeleton()
        result = type(a_rt_arm_module.lowerarm_twist_joints)
        expected = list
        self.assertEqual(expected, result)
        result = len(a_rt_arm_module.lowerarm_twist_joints)
        expected = 3
        self.assertEqual(expected, result)
        result = type(a_rt_arm_module.upperarm_twist_joints)
        expected = list
        self.assertEqual(expected, result)
        result = len(a_rt_arm_module.upperarm_twist_joints)
        expected = 3
        self.assertEqual(expected, result)

    def test_module_arm_build_rig(self):
        arm_module_instance = module_arm.ModuleBipedArm(prefix="C")
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(arm_module_instance)
        a_project.build_proxy()
        a_project.build_rig()
        expected_elements = [
            "C_clavicle_JNT",
            "C_upperArm_JNT",
            "C_lowerArm_JNT",
            "C_hand_JNT",
            "C_hand_JNT_parentConstraint",
            "C_lowerArm_JNT_parentConstraint",
            "C_upperArm_JNT_parentConstraint",
            "C_clavicle_JNT_parentConstraint",
            "C_clavicle_offset",
            "C_clavicle_CTRL",
            "C_upperArm_offset",
            "C_upperArm_CTRL",
            "C_lowerArm_offset",
            "C_lowerArm_CTRL",
            "C_hand_offset",
            "C_hand_CTRL",
            "C_upperArm_refGrp",
            "C_hand_IK_offset",
            "C_hand_IK_CTRL",
            "C_hand_IKOffset_CTRL",
            "C_hand_IK_offsetData",
            "C_lowerArm_aimGrp",
            "C_arm_offset",
            "C_arm_CTRL",
            "C_arm_offset_parentConstraint",
            "C_hand_automation_grp",
            "C_hand_ikHandle",
            "C_hand_ikHandle_poleVectorConstraint1",
            "C_hand_ikHandle_pointConstraint1",
            "C_clavicle_JNT_fk",
            "C_upperArm_JNT_fk",
            "C_lowerArm_JNT_fk",
            "C_hand_JNT_fk",
            "C_hand_JNT_fk_parentConstraint",
            "C_handSwitch_loc",
            "C_lowerArm_JNT_fk_parentConstraint",
            "C_lowerArmSwitch_loc",
            "C_upperArm_JNT_fk_parentConstraint",
            "C_clavicle_JNT_fk_parentConstraint",
            "C_clavicle_JNT_ik",
            "C_upperArm_JNT_ik",
            "C_lowerArm_JNT_ik",
            "C_hand_JNT_ik",
            "C_hand_JNT_ik_orientConstraint1",
            "C_handFkOffsetRef_loc",
            "C_lowerArmFkOffsetRef_loc",
            "C_upperArmFkOffsetRef_loc",
            "C_clavicle_JNT_ik_parentConstraint1",
            "C_lowerArm_IK_CTRL_cluster",
            "C_lowerArm_JNT_ik_cluster",
        ]
        for obj in expected_elements:
            self.assertTrue(cmds.objExists(obj))

    def test_module_arm_find_drivers_from_module(self):
        a_arm_module = module_arm.ModuleBipedArm(prefix="C")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_arm_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        expected = [
            "|rig|controls|C_global_CTRL|C_arm_offset|C_arm_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_clavicle_offset|C_clavicle_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_clavicle_offset|C_clavicle_CTRL|C_upperArm_offset"
            "|C_upperArm_parentOffset|C_upperArm_CTRL|C_lowerArm_offset|C_lowerArm_CTRL|C_hand_offset|C_hand_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_hand_IK_offset|C_hand_IK_parentOffset|C_hand_IK_CTRL"
            "|C_hand_IKOffset_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_hand_IK_offset|C_hand_IK_parentOffset|C_hand_IK_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_clavicle_offset|C_clavicle_CTRL|C_upperArm_offset"
            "|C_upperArm_parentOffset|C_upperArm_CTRL|C_lowerArm_offset|C_lowerArm_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_lowerArm_twistGrp_offset|C_lowerArm_twistGrp"
            "|C_lowerArm_IK_offset|C_lowerArm_IK_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_clavicle_offset|C_clavicle_CTRL|C_upperArm_offset"
            "|C_upperArm_parentOffset|C_upperArm_CTRL",
        ]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_arm_module.get_uuid(), filter_driver_type=None  # No filter means all types
        )
        self.assertEqual(expected, result)

    def test_module_arm_proxy_pose_default(self):
        an_arm_module = module_arm.ModuleBipedArm()
        # Setup Project
        a_proxy = tools_rig_frm.Proxy()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_arm_module)
        a_project.add_to_modules(a_proxy)
        a_project.build_proxy()

        world_position_proxy = [
            ("clavicle", [0.0, 130.0, 0.0]),
            ("upperArm", [0.0, 130.0, 17.2]),
            ("lowerArm", [0.01, 130.0, 37.7]),
            ("hand", [0.0, 130.0, 58.2]),
        ]

        for joint_name, expected in world_position_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("clavicle", [0.0, 0.0, 0.0]),
            ("upperArm", [0.0, 0.0, 0.0]),
            ("lowerArm", [0.0, -90.0, 0.0]),
            ("hand", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_arm_proxy_pose_a(self):
        an_arm_module = module_arm.ModuleBipedArm()
        # Setup Project
        an_arm_module.clavicle_proxy.set_initial_position(xyz=[30, 10, 60])
        an_arm_module.upperarm_proxy.set_initial_position(xyz=[20, 5, 60])
        an_arm_module.lowerarm_proxy.set_initial_position(xyz=[30, 50, 10])
        an_arm_module.hand_proxy.set_initial_position(xyz=[30, 5, 90])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_arm_module)
        a_project.build_proxy()

        world_position_proxy = [
            ("clavicle", [30.0, 10.0, 60.0]),
            ("upperArm", [20.0, 5.0, 60.0]),
            ("lowerArm", [30.0, 50.0, 10.0]),
            ("hand", [30.0, 5.0, 90.0]),
        ]

        for joint_name, expected in world_position_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("clavicle", [0.0, 0.0, 0.0]),
            ("upperArm", [0.0, 0.0, 0.0]),
            ("lowerArm", [60.66, -71.57, 0.0]),
            ("hand", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_arm_proxy_pose_b(self):
        an_arm_module = module_arm.ModuleBipedArm()
        # Setup Project
        an_arm_module.clavicle_proxy.set_initial_position(xyz=[50, 110, 55])
        an_arm_module.upperarm_proxy.set_initial_position(xyz=[24, 54, 62])
        an_arm_module.lowerarm_proxy.set_initial_position(xyz=[20, 2, 1])
        an_arm_module.hand_proxy.set_initial_position(xyz=[20, 52, 72])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_arm_module)
        a_project.build_proxy()

        world_position_proxy = [
            ("clavicle", [50.0, 110.0, 55.0]),
            ("upperArm", [24.0, 54.0, 62.0]),
            ("lowerArm", [28.29, -0.38, 3.84]),
            ("hand", [20.0, 52.0, 72.0]),
        ]

        for joint_name, expected in world_position_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("clavicle", [0.0, 0.0, 0.0]),
            ("upperArm", [0.0, 0.0, 0.0]),
            ("lowerArm", [49.99, -65.91, -153.43]),
            ("hand", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_arm_joint_pose_default(self):
        an_arm_module = module_arm.ModuleBipedArm(clavicle_world=False)
        # Setup Project
        a_proxy = tools_rig_frm.Proxy()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_arm_module)
        a_project.add_to_modules(a_proxy)
        a_project.build_proxy()
        a_project.build_rig()

        world_position_joint = [
            ("clavicle_JNT", [0.0, 130.0, 0.0]),
            ("upperArm_JNT", [0.0, 130.0, 17.2]),
            ("lowerArm_JNT", [20.50, 130.0, 17.20]),
            ("hand_JNT", [41.0, 130.0, 17.27]),
            # FK joints
            ("clavicle_JNT_fk", [0.0, 130.0, 0.0]),
            ("upperArm_JNT_fk", [0.0, 130.0, 17.2]),
            ("lowerArm_JNT_fk", [20.5, 130.0, 17.2]),
            ("hand_JNT_fk", [41.0, 130.0, 17.27]),
            # IK joints
            ("clavicle_JNT_ik", [0.0, 130.0, 0.0]),
            ("upperArm_JNT_ik", [0.0, 130.0, 17.2]),
            ("lowerArm_JNT_ik", [20.5, 130.0, 17.2]),
            ("hand_JNT_ik", [41.0, 130.0, 17.27]),
        ]

        for joint_name, expected in world_position_joint:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_joint = [
            ("clavicle_JNT", [-90.0, -90.0, 0.0]),
            ("upperArm_JNT", [-90.0, 0.0, 0.0]),
            ("lowerArm_JNT", [-90.0, -0.20, 0.0]),
            ("hand_JNT", [-90.0, 0.0, 0.0]),
            # FK joints
            ("clavicle_JNT_fk", [-90.0, -90.0, 0.0]),
            ("upperArm_JNT_fk", [-90.0, 0.0, 0.0]),
            ("lowerArm_JNT_fk", [-90.0, -0.20, 0.0]),
            ("hand_JNT_fk", [-90.0, 0.0, 0.0]),
            # IK joints
            ("clavicle_JNT_ik", [-90.0, -90.0, 0.0]),
            ("upperArm_JNT_ik", [-90.0, 0.0, 0.0]),
            ("lowerArm_JNT_ik", [-90.0, -0.20, 0.0]),
            ("hand_JNT_ik", [-90.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_joint:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_arm_joint_pose_a(self):
        an_arm_module = module_arm.ModuleBipedArm()
        # Setup Project
        an_arm_module.clavicle_proxy.set_initial_position(xyz=[30, 10, 60])
        an_arm_module.upperarm_proxy.set_initial_position(xyz=[20, 5, 60])
        an_arm_module.lowerarm_proxy.set_initial_position(xyz=[30, 50, 10])
        an_arm_module.hand_proxy.set_initial_position(xyz=[30, 5, 90])
        a_proxy = tools_rig_frm.Proxy()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_arm_module)
        a_project.add_to_modules(a_proxy)
        a_project.build_proxy()
        a_project.build_rig()

        world_position_joint = [
            ("clavicle_JNT", [30.0, 10.0, 60.0]),
            ("upperArm_JNT", [41.18, 10.0, 60.0]),
            ("lowerArm_JNT", [109.19, 10.0, 60.0]),
            ("hand_JNT", [200.97, 10.0, 60.32]),
            # FK joints
            ("clavicle_JNT_fk", [30.0, 10.0, 60.0]),
            ("upperArm_JNT_fk", [41.18, 10.0, 60.0]),
            ("lowerArm_JNT_fk", [109.19, 10.0, 60.0]),
            ("hand_JNT_fk", [200.97, 10.0, 60.32]),
            # IK joints
            ("clavicle_JNT_ik", [30.0, 10.0, 60.0]),
            ("upperArm_JNT_ik", [41.18, 10.0, 60.0]),
            ("lowerArm_JNT_ik", [109.19, 10.0, 60.07]),
            ("hand_JNT_ik", [200.98, 10.0, 60.32]),
        ]

        for joint_name, expected in world_position_joint:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_joint = [
            ("clavicle_JNT", [-90.0, 0.0, 0.0]),
            ("upperArm_JNT", [-90.0, 0.0, 0.0]),
            ("lowerArm_JNT", [-90.0, -0.2, 0.0]),
            ("hand_JNT", [-90.0, 0.0, 0.0]),
            # FK joints
            ("clavicle_JNT_fk", [-90.0, 0.0, 0.0]),
            ("upperArm_JNT_fk", [-90.0, 0.0, 0.0]),
            ("lowerArm_JNT_fk", [-90.0, -0.2, 0.0]),
            ("hand_JNT_fk", [-90.0, 0.0, 0.0]),
            # IK joints
            ("clavicle_JNT_ik", [-90.0, 0.0, 0.0]),
            ("upperArm_JNT_ik", [-90.0, -0.06, -0.0]),
            ("lowerArm_JNT_ik", [-90.0, -0.16, 0.0]),
            ("hand_JNT_ik", [-90.0, 0.0, 0.04]),
        ]

        for joint_name, expected in world_rotation_joint:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_arm_joint_pose_b(self):
        an_arm_module = module_arm.ModuleBipedArm(clavicle_world=False)
        # Setup Project
        an_arm_module.clavicle_proxy.set_initial_position(xyz=[50, 110, 55])
        an_arm_module.upperarm_proxy.set_initial_position(xyz=[24, 54, 62])
        an_arm_module.lowerarm_proxy.set_initial_position(xyz=[20, 2, 1])
        an_arm_module.hand_proxy.set_initial_position(xyz=[20, 52, 72])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_arm_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_position_joint = [
            ("clavicle_JNT", [50.0, 110.0, 55.0]),
            ("upperArm_JNT", [110.0, 110.0, 38.85]),
            ("lowerArm_JNT", [189.74, 110.0, 38.85]),
            ("hand_JNT", [276.11, 110.0, 39.15]),
            # FK joints
            ("clavicle_JNT_fk", [50.0, 110.0, 55.0]),
            ("upperArm_JNT_fk", [110.0, 110.0, 38.85]),
            ("lowerArm_JNT_fk", [189.74, 110.0, 38.85]),
            ("hand_JNT_fk", [276.11, 110.0, 39.15]),
            # IK joints
            ("clavicle_JNT_ik", [50.0, 110.0, 55.0]),
            ("upperArm_JNT_ik", [110.0, 110.0, 38.85]),
            ("lowerArm_JNT_ik", [189.74, 110.0, 38.85]),
            ("hand_JNT_ik", [276.11, 110.0, 39.15]),
        ]

        for joint_name, expected in world_position_joint:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_joint = [
            ("clavicle_JNT", [-90.0, 15.07, 0.0]),
            ("upperArm_JNT", [-90.0, 0.0, 0.0]),
            ("lowerArm_JNT", [-90.0, -0.2, 0.0]),
            ("hand_JNT", [-90.0, 0.0, 0.0]),
            # FK joints
            ("clavicle_JNT_fk", [-90.0, 15.07, 0.0]),
            ("upperArm_JNT_fk", [-90.0, 0.0, 0.0]),
            ("lowerArm_JNT_fk", [-90.0, -0.2, 0.0]),
            ("hand_JNT_fk", [-90.0, 0.0, 0.0]),
            # IK joints
            ("clavicle_JNT_ik", [-90.0, 15.07, 0.0]),
            ("upperArm_JNT_ik", [-90.0, -0.0, 0.0]),
            ("lowerArm_JNT_ik", [-90.0, -0.2, 0.0]),
            ("hand_JNT_ik", [-90.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_joint:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_arm_control_pose_default(self):
        an_arm_module = module_arm.ModuleBipedArm(clavicle_world=False)
        # Setup Project
        a_proxy = tools_rig_frm.Proxy()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_arm_module)
        a_project.add_to_modules(a_proxy)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_controls = [
            ("arm_CTRL", [41.0, 130.0, 17.27]),
            ("clavicle_CTRL", [0.0, 130.0, 0.0]),
            ("upperArm_CTRL", [0.0, 130.0, 17.2]),
            ("lowerArm_CTRL", [20.5, 130.0, 17.2]),
            ("hand_CTRL", [41.0, 130.0, 17.27]),
            ("hand_IK_CTRL", [41.0, 130.0, 17.27]),
            ("lowerArm_IK_CTRL", [20.54, 130.0, -7.4]),
            ("upperArm_JNT_ik", [0.0, 130.0, 17.2]),
        ]

        for joint_name, expected in world_positions_controls:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_controls = [
            ("arm_CTRL", [0.0, 0.0, 0.0]),
            ("clavicle_CTRL", [-90.0, -90.0, 0.0]),
            ("upperArm_CTRL", [-90.0, 0.0, 0.0]),
            ("lowerArm_CTRL", [-90.0, -0.2, 0.0]),
            ("hand_CTRL", [-90.0, 0.0, 0.0]),
            ("hand_IK_CTRL", [0.0, 0.0, 0.0]),
            ("lowerArm_IK_CTRL", [0.0, 0.0, 0.0]),
            ("upperArm_JNT_ik", [-90.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_controls:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_arm_control_pose_a(self):
        an_arm_module = module_arm.ModuleBipedArm(clavicle_world=False)
        # Setup Project
        an_arm_module.clavicle_proxy.set_initial_position(xyz=[30, 10, 60])
        an_arm_module.upperarm_proxy.set_initial_position(xyz=[20, 5, 60])
        an_arm_module.lowerarm_proxy.set_initial_position(xyz=[30, 50, 10])
        an_arm_module.hand_proxy.set_initial_position(xyz=[30, 5, 90])
        a_proxy = tools_rig_frm.Proxy()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_arm_module)
        a_project.add_to_modules(a_proxy)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_controls = [
            ("arm_CTRL", [200.97, 10.0, 60.32]),
            ("clavicle_CTRL", [30.0, 10.0, 60.0]),
            ("upperArm_CTRL", [41.18, 10.0, 60.0]),
            ("lowerArm_CTRL", [109.19, 10.0, 60.0]),
            ("hand_CTRL", [200.97, 10.0, 60.32]),
            ("hand_IK_CTRL", [200.97, 10.0, 60.32]),
            ("lowerArm_IK_CTRL", [109.38, 10.0, -35.88]),
            ("upperArm_JNT_ik", [41.18, 10.0, 60.0]),
        ]

        for joint_name, expected in world_positions_controls:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_controls = [
            ("arm_CTRL", [0.0, 0.0, 0.0]),
            ("clavicle_CTRL", [-90.0, 0.0, 0.0]),
            ("upperArm_CTRL", [-90.0, 0.0, 0.0]),
            ("lowerArm_CTRL", [-90.0, -0.2, 0.0]),
            ("hand_CTRL", [-90.0, 0.0, 0.0]),
            ("hand_IK_CTRL", [0.0, 0.0, 0.0]),
            ("lowerArm_IK_CTRL", [0.0, 0.0, 0.0]),
            ("upperArm_JNT_ik", [-90.0, -0.06, -0.0]),
        ]

        for joint_name, expected in world_rotation_controls:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_arm_control_pose_b(self):
        an_arm_module = module_arm.ModuleBipedArm(clavicle_world=False)
        # Setup Project
        an_arm_module.clavicle_proxy.set_initial_position(xyz=[50, 110, 55])
        an_arm_module.upperarm_proxy.set_initial_position(xyz=[24, 54, 62])
        an_arm_module.lowerarm_proxy.set_initial_position(xyz=[20, 2, 1])
        an_arm_module.hand_proxy.set_initial_position(xyz=[20, 52, 72])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_arm_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_controls = [
            ("arm_CTRL", [276.11, 110.0, 39.15]),
            ("clavicle_CTRL", [50.0, 110.0, 55.0]),
            ("upperArm_CTRL", [110.0, 110.0, 38.85]),
            ("lowerArm_CTRL", [189.74, 110.0, 38.85]),
            ("hand_CTRL", [276.11, 110.0, 39.15]),
            ("hand_IK_CTRL", [276.11, 110.0, 39.15]),
            ("lowerArm_IK_CTRL", [189.92, 110.0, -60.82]),
            ("upperArm_JNT_ik", [110.0, 110.0, 38.85]),
        ]

        for joint_name, expected in world_positions_controls:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_controls = [
            ("arm_CTRL", [0.0, 0.0, 0.0]),
            ("clavicle_CTRL", [-90.0, 15.07, 0.0]),
            ("upperArm_CTRL", [-90.0, 0.0, 0.0]),
            ("lowerArm_CTRL", [-90.0, -0.2, 0.0]),
            ("hand_CTRL", [-90.0, 0.0, 0.0]),
            ("hand_IK_CTRL", [0.0, 0.0, 0.0]),
            ("lowerArm_IK_CTRL", [0.0, 0.0, 0.0]),
            ("upperArm_JNT_ik", [-90.0, -0.0, -0.0]),
        ]

        for joint_name, expected in world_rotation_controls:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_arm_same_joint_position(self):
        a_arm_module = module_arm.ModuleBipedArm(prefix="C")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_arm_module)
        a_project.build_proxy()
        a_project.build_rig()
        jnts = ["C_clavicle_JNT", "C_upperArm_JNT", "C_lowerArm_JNT", "C_hand_JNT"]
        for jnt in jnts:
            fk_jnt = f"{jnt}_fk"
            ik_jnt = f"{jnt}_ik"
            fk_mat = cmds.xform(fk_jnt, q=True, m=True, ws=True)
            ik_mat = cmds.xform(ik_jnt, q=True, m=True, ws=True)
            self.assertTrue(fk_mat, ik_mat)
