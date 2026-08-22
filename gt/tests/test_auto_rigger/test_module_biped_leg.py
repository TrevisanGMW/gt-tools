import unittest
import logging
import sys
import os

import gt.tools.auto_rigger.modules.module_biped_leg as module_leg
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.tools.auto_rigger.control_rig_pose as tools_control_pose
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


class TestModuleBipedLeg(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        tools_maya_plugins.load_startup_plugins()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)

    def test_module_biped_leg_inheritance(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        result = isinstance(leg_module_instance, tools_rig_frm.ModuleGeneric)
        expected = True
        self.assertEqual(expected, result)

    def test_module_leg_inheritance_passthrough(self):
        leg_module_instance = module_leg.ModuleBipedLeg(
            name="mocked_leg", prefix="mocked_prefix", suffix="mocked_suffix"
        )
        result = leg_module_instance.name
        expected = "mocked_leg"
        self.assertEqual(expected, result)
        result = leg_module_instance.prefix
        expected = "mocked_prefix"
        self.assertEqual(expected, result)
        result = leg_module_instance.suffix
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_leg_basic_proxy_compliance(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        # Proxies Type
        result = type(leg_module_instance.proxies)
        expected = list
        self.assertEqual(expected, result, '"proxies" variable must be a list.')
        # Number of proxies
        result = len(leg_module_instance.proxies)
        expected = 8
        self.assertEqual(expected, result)
        # Proxy type (Proxies should only carry tools_rig_frm.Proxy objects)
        for proxy in leg_module_instance.proxies:
            message = f'An element in the proxies list is not a proxy instance. Issue object: "{str(proxy)}"'
            self.assertIsInstance(proxy, tools_rig_frm.Proxy, message)
        # Variable Names (Must end with "_proxy")
        proxy_vars = {
            key: value for key, value in vars(leg_module_instance).items() if isinstance(value, tools_rig_frm.Proxy)
        }
        for proxy_var_key in proxy_vars.keys():
            message = f'A proxy variables was not named correctly. Incorrect variable: "{str(proxy_var_key)}"'
            self.assertTrue(proxy_var_key.endswith("_proxy"), message)

    def test_module_leg_default_proxy_prefix(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        leg_prefix = leg_module_instance.get_prefix()
        expected = None
        self.assertEqual(expected, leg_prefix)

    def test_module_leg_default_proxy_suffix(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        leg_suffix = leg_module_instance.get_suffix()
        expected = None
        self.assertEqual(expected, leg_suffix)

    def test_module_leg_check_default_orientation(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        an_orientation_data = leg_module_instance.get_orientation_data()
        result = an_orientation_data.get_method()
        expected = "automatic"
        self.assertEqual(expected, result)

    def test_module_leg_proxy_names(self):
        leg_names = ["upperLeg", "lowerLeg", "foot", "ball", "toe", "heel", "bankLeft", "bankRight"]
        leg_module_instance = module_leg.ModuleBipedLeg()
        for proxy in leg_module_instance.proxies:
            result = proxy.get_name()
            self.assertEqual(leg_names[leg_module_instance.proxies.index(proxy)], result)

    def test_module_leg_meta_purpose_names(self):
        leg_names = ["upperLeg", "lowerLeg", "foot", "ball", "toe", "heel", "bankLeft", "bankRight"]
        leg_module_instance = module_leg.ModuleBipedLeg()
        for proxy in leg_module_instance.proxies:
            result = proxy.get_meta_purpose()
            self.assertEqual(leg_names[leg_module_instance.proxies.index(proxy)], result)

    def test_module_leg_upperleg_proxy_driver_types(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        result = leg_module_instance.upperleg_proxy.get_driver_types()
        expected = [tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        self.assertEqual(expected, result)

    def test_module_leg_lowerleg_proxy_driver_types(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        result = leg_module_instance.lowerleg_proxy.get_driver_types()
        expected = [
            tools_rig_const.RiggerDriverTypes.GENERIC,
            tools_rig_const.RiggerDriverTypes.FK,
            tools_rig_const.RiggerDriverTypes.IK,
        ]
        self.assertEqual(expected, result)

    def test_module_leg_foot_proxy_driver_types(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        result = leg_module_instance.foot_proxy.get_driver_types()
        expected = [
            tools_rig_const.RiggerDriverTypes.GENERIC,
            tools_rig_const.RiggerDriverTypes.FK,
            tools_rig_const.RiggerDriverTypes.IK,
        ]
        self.assertEqual(expected, result)

    def test_module_leg_ball_proxy_driver_types(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        result = leg_module_instance.ball_proxy.get_driver_types()
        expected = [tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        self.assertEqual(expected, result)

    def test_module_leg_toe_proxy_driver_types(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        result = leg_module_instance.toe_proxy.get_driver_types()
        expected = [tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.IK]
        self.assertEqual(expected, result)

    def test_module_leg_get_module_as_dict(self):
        # Default Module
        leg_module_instance = module_leg.ModuleBipedLeg()
        a_leg_as_dict = leg_module_instance.get_module_as_dict()
        self.assertIsInstance(a_leg_as_dict, dict)
        expected_keys = sorted(
            [
                "active",
                "expanded",
                "auto_pole_vector",
                "code",
                "create_twist_joints",
                "delete_toe_bind_jnt",
                "ensure_coplanarity",
                "lowerleg_twist_joints",
                "module",
                "name",
                "orientation",
                "proxies",
                "rig_pose_knee_rot",
                "setup_name",
                "upperleg_twist_joints",
                "uuid",
            ]
        )
        result_keys = sorted(list(a_leg_as_dict.keys()))
        self.assertEqual(expected_keys, result_keys)
        expected_module_value = "ModuleBipedLeg"
        result_module_value = a_leg_as_dict.get("module")
        self.assertEqual(expected_module_value, result_module_value)
        # Change Module and Test Module Level Serialization
        leg_module_instance.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")
        a_leg_as_dict = leg_module_instance.get_module_as_dict()
        self.assertIn("parent", a_leg_as_dict)
        # Transfer data to a new leg module
        a_2nd_leg_module = module_leg.ModuleBipedLeg()
        a_2nd_leg_module.read_data_from_dict(a_leg_as_dict)
        expected = leg_module_instance.get_module_as_dict()
        result = a_2nd_leg_module.get_module_as_dict()
        self.assertEqual(expected, result)

    def test_module_leg_read_proxies_from_dict(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        leg_module_instance.upperleg_proxy.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")  # Changed the proxy
        a_leg_as_dict = leg_module_instance.get_module_as_dict()
        # Create a second module (new)
        a_2nd_leg_module = module_leg.ModuleBipedLeg()
        a_2nd_leg_module.read_proxies_from_dict(a_leg_as_dict.get("proxies"))
        expected = leg_module_instance.upperleg_proxy.get_uuid()
        result = a_2nd_leg_module.upperleg_proxy.get_uuid()
        self.assertEqual(expected, result)

    def test_module_leg_build_proxy(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        proxy_data_list = leg_module_instance.build_proxy()
        # Check ProxyData objects
        for proxy_data in proxy_data_list:
            self.assertIsInstance(proxy_data, tools_rig_frm.ProxyData)
            self.assertTrue(cmds.objExists(proxy_data.get_long_name()))
        # Check Maya Scene
        expected_nodes = [
            "upperLeg_offset",
            "upperLeg",
            "lowerLeg_offset",
            "lowerLeg",
            "foot_offset",
            "foot",
            "heel_offset",
            "heel",
            "bankLeft_offset",
            "bankLeft",
            "bankRight_offset",
            "bankRight",
            "ball_offset",
            "ball",
            "toe_offset",
            "toe",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("upperLeg.proxyUUID"))
        self.assertTrue(cmds.objExists("lowerLeg.proxyUUID"))
        self.assertTrue(cmds.objExists("foot.proxyUUID"))
        self.assertTrue(cmds.objExists("heel.proxyUUID"))
        self.assertTrue(cmds.objExists("bankLeft.proxyUUID"))
        self.assertTrue(cmds.objExists("bankRight.proxyUUID"))
        self.assertTrue(cmds.objExists("ball.proxyUUID"))
        self.assertTrue(cmds.objExists("toe.proxyUUID"))

    def test_module_leg_build_proxy_within_project(self):
        leg_module_instance = module_leg.ModuleBipedLeg()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(leg_module_instance)
        a_project.build_proxy()
        expected_nodes = [
            "upperLeg_offset",
            "upperLeg",
            "lowerLeg_offset",
            "lowerLeg",
            "foot_offset",
            "foot",
            "heel_offset",
            "heel",
            "bankLeft_offset",
            "bankLeft",
            "bankRight_offset",
            "bankRight",
            "ball_offset",
            "ball",
            "toe_offset",
            "toe",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("upperLeg.proxyUUID"))
        self.assertTrue(cmds.objExists("lowerLeg.proxyUUID"))
        self.assertTrue(cmds.objExists("foot.proxyUUID"))
        self.assertTrue(cmds.objExists("heel.proxyUUID"))
        self.assertTrue(cmds.objExists("bankLeft.proxyUUID"))
        self.assertTrue(cmds.objExists("bankRight.proxyUUID"))
        self.assertTrue(cmds.objExists("ball.proxyUUID"))
        self.assertTrue(cmds.objExists("toe.proxyUUID"))

    def test_module_leg_prefixes(self):
        a_lf_leg_module = module_leg.ModuleBipedLegLeft()
        a_proxy = a_lf_leg_module.get_prefix()
        expected = "L"
        self.assertEqual(expected, a_proxy)
        a_rt_leg_module = module_leg.ModuleBipedLegRight()
        a_proxy = a_rt_leg_module.get_prefix()
        expected = "R"
        self.assertEqual(expected, a_proxy)

    def test_module_leg_left_twists(self):
        a_lf_leg_module = module_leg.ModuleBipedLegLeft()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_lf_leg_module)
        a_project.build_proxy()
        a_project.build_skeleton()
        result = type(a_lf_leg_module.lowerleg_twist_joints)
        expected = list
        self.assertEqual(expected, result)
        result = len(a_lf_leg_module.lowerleg_twist_joints)
        expected = 3
        self.assertEqual(expected, result)
        result = type(a_lf_leg_module.upperleg_twist_joints)
        expected = list
        self.assertEqual(expected, result)
        result = len(a_lf_leg_module.upperleg_twist_joints)
        expected = 3
        self.assertEqual(expected, result)

    def test_module_leg_right_twists(self):
        a_rt_leg_module = module_leg.ModuleBipedLegRight()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_rt_leg_module)
        a_project.build_proxy()
        a_project.build_skeleton()
        result = type(a_rt_leg_module.lowerleg_twist_joints)
        expected = list
        self.assertEqual(expected, result)
        result = len(a_rt_leg_module.lowerleg_twist_joints)
        expected = 3
        self.assertEqual(expected, result)
        result = type(a_rt_leg_module.upperleg_twist_joints)
        expected = list
        self.assertEqual(expected, result)
        result = len(a_rt_leg_module.upperleg_twist_joints)
        expected = 3
        self.assertEqual(expected, result)

    def test_module_leg_joint_pose_default(self):
        a_leg_module = module_leg.ModuleBipedLeg(prefix="C")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.set_control_rig_pose_mode(tools_control_pose.ControlRigPoseMode.AUTOMATIC)
        a_project.add_to_modules(a_leg_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_joint = [
            ("C_upperLeg_JNT", [0.0, 84.5, 0.0]),
            ("C_lowerLeg_JNT", [0.0, 47.0, 0.0]),
            ("C_foot_JNT", [0.0, 9.54, -1.96]),
            ("C_ball_JNT", [0.0, -0.06, 11.14]),
            ("C_upperLeg_JNT_fk", [0.0, 84.5, 0.0]),
            ("C_lowerLeg_JNT_fk", [0.0, 47.0, 0.0]),
            ("C_foot_JNT_fk", [0.0, 9.54, -1.96]),
            ("C_ball_JNT_fk", [0.0, -0.06, 11.14]),
            ("C_toe_JNT_fk", [0.0, -0.06, 21.44]),
            ("C_upperLeg_JNT_ik", [0.0, 84.5, 0.0]),
            ("C_lowerLeg_JNT_ik", [0.0, 47.0, 0.0]),
            ("C_foot_JNT_ik", [0.0, 9.54, -1.96]),
            ("C_ball_JNT_ik", [0.0, -0.06, 11.14]),
            ("C_toe_JNT_ik", [0.0, -0.06, 21.44]),
        ]

        for joint_name, expected in world_positions_joint:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertListEqual(expected, rounded_translation)

        world_rotation_joint = [
            ("C_upperLeg_JNT", [90.0, -90.0, 0.0]),
            ("C_lowerLeg_JNT", [90.0, 3.0, -90.0]),
            ("C_foot_JNT", [90.0, -90.0, 0.0]),
            ("C_ball_JNT", [0.0, -90.0, 0.0]),
            ("C_upperLeg_JNT_fk", [90.0, -90.0, 0.0]),
            ("C_lowerLeg_JNT_fk", [90.0, 3.0, -90.0]),
            ("C_foot_JNT_fk", [90.0, -90.0, 0.0]),
            ("C_ball_JNT_fk", [0.0, -90.0, 0.0]),
            ("C_toe_JNT_fk", [0.0, 0.0, 0.0]),
            ("C_upperLeg_JNT_ik", [90.0, -90.0, 0.0]),
            ("C_lowerLeg_JNT_ik", [90.0, 3.0, -90.0]),
            ("C_foot_JNT_ik", [90.0, -90.0, 0.0]),
            ("C_ball_JNT_ik", [0.0, -90.0, 0.0]),
            ("C_toe_JNT_ik", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_joint:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertListEqual(expected, rounded_rotation)

    def test_module_leg_control_pose_default(self):
        a_leg_module = module_leg.ModuleBipedLeg(prefix="C")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.set_control_rig_pose_mode(tools_control_pose.ControlRigPoseMode.AUTOMATIC)
        a_project.add_to_modules(a_leg_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_control = [
            ("C_upperLeg_CTRL", [0.0, 84.5, 0.0]),
            ("C_lowerLeg_CTRL", [0.0, 47.0, 0.0]),
            ("C_foot_CTRL", [0.0, 9.54, -1.96]),
            ("C_ball_CTRL", [0.0, -0.06, 11.14]),
            ("C_lowerLeg_IK_CTRL", [0.0, 47.0, 37.5]),
            ("C_foot_IK_CTRL", [0.0, 9.54, -1.96]),
            ("C_leg_CTRL", [0.0, 9.54, -1.96]),
            ("C_toe_IK_CTRL", [0.0, -0.06, 11.14]),
        ]

        for joint_name, expected in world_positions_control:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertListEqual(expected, rounded_translation)

        world_rotation_control = [
            ("C_upperLeg_CTRL", [90.0, -90.0, 0.0]),
            ("C_lowerLeg_CTRL", [90.0, 3.0, -90.0]),
            ("C_foot_CTRL", [90.0, -90.0, 0.0]),
            ("C_ball_CTRL", [0.0, -90.0, 0.0]),
            ("C_lowerLeg_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_foot_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_leg_CTRL", [0.0, 0.0, 0.0]),
            ("C_toe_IK_CTRL", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_control:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertListEqual(expected, rounded_rotation)
