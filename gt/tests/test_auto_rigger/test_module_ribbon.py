import unittest
import logging
import sys
import os

import gt.tools.auto_rigger.modules.module_ribbon as module_ribbon
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


class TestModuleRibbon(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        tools_maya_plugins.load_startup_plugins()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)

    def test_module_biped_ribbon_inheritance(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        result = isinstance(ribbon_module_instance, tools_rig_frm.ModuleGeneric)
        expected = True
        self.assertEqual(expected, result)

    def test_module_ribbon_inheritance_passthrough(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon(
            name="mocked_ribbon", prefix="mocked_prefix", suffix="mocked_suffix"
        )
        result = ribbon_module_instance.name
        expected = "mocked_ribbon"
        self.assertEqual(expected, result)
        result = ribbon_module_instance.prefix
        expected = "mocked_prefix"
        self.assertEqual(expected, result)
        result = ribbon_module_instance.suffix
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_ribbon_basic_proxy_compliance(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        # Proxies Type
        result = type(ribbon_module_instance.proxies)
        expected = list
        self.assertEqual(expected, result, '"proxies" variable must be a list.')
        # Number of proxies
        result = len(ribbon_module_instance.proxies)
        expected = 4
        self.assertEqual(expected, result)
        # Proxy type (Proxies should only carry tools_rig_frm.Proxy objects)
        for proxy in ribbon_module_instance.proxies:
            message = f'An element in the proxies list is not a proxy instance. Issue object: "{str(proxy)}"'
            self.assertIsInstance(proxy, tools_rig_frm.Proxy, message)
        # Variable Names (Must end with "_proxy")
        proxy_vars = {
            key: value for key, value in vars(ribbon_module_instance).items() if isinstance(value, tools_rig_frm.Proxy)
        }
        for proxy_var_key in proxy_vars.keys():
            message = f'A proxy variables was not named correctly. Incorrect variable: "{str(proxy_var_key)}"'
            self.assertTrue(proxy_var_key.endswith("_proxy"), message)

    def test_module_ribbon_default_proxy_prefix(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        ribbon_prefix = ribbon_module_instance.get_prefix()
        expected = "C"
        self.assertEqual(expected, ribbon_prefix)

    def test_module_ribbon_default_proxy_suffix(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        ribbon_suffix = ribbon_module_instance.get_suffix()
        expected = None
        self.assertEqual(expected, ribbon_suffix)

    def test_module_ribbon_check_default_orientation(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        an_orientation_data = ribbon_module_instance.get_orientation_data()
        result = an_orientation_data.get_method()
        expected = "automatic"
        self.assertEqual(expected, result)

    def test_module_ribbon_proxy_names(self):
        ribbon_names = ["ribbonBase", "ribbon01", "ribbon02", "ribbonEnd"]
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        for proxy in ribbon_module_instance.proxies:
            result = proxy.get_name()
            self.assertEqual(ribbon_names[ribbon_module_instance.proxies.index(proxy)], result)

    def test_module_ribbon_meta_purpose_names(self):
        ribbon_names = ["ribbonBase", "ribbon01", "ribbon02", "ribbonEnd"]
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        for proxy in ribbon_module_instance.proxies:
            result = proxy.get_meta_purpose()
            self.assertEqual(ribbon_names[ribbon_module_instance.proxies.index(proxy)], result)

    def test_module_ribbon_base_proxy_driver_types(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        result = ribbon_module_instance.base_proxy.get_driver_types()
        expected = [
            tools_rig_const.RiggerDriverTypes.GENERIC,
            tools_rig_const.RiggerDriverTypes.FK,
            tools_rig_const.RiggerDriverTypes.IK,
        ]
        self.assertEqual(expected, result)

    def test_module_ribbon_end_proxy_driver_types(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        result = ribbon_module_instance.end_proxy.get_driver_types()
        expected = [
            tools_rig_const.RiggerDriverTypes.GENERIC,
            tools_rig_const.RiggerDriverTypes.FK,
            tools_rig_const.RiggerDriverTypes.IK,
        ]
        self.assertEqual(expected, result)

    def test_module_ribbon_get_module_as_dict(self):
        # Default Module
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        a_ribbon_as_dict = ribbon_module_instance.get_module_as_dict()
        self.assertIsInstance(a_ribbon_as_dict, dict)
        expected_keys = sorted(
            [
                "active",
                "cable_ctrls",
                "division_last_num",
                "divisions",
                "expanded",
                "fk_ctrl_shapes",
                "ik_ctrl_shapes",
                "middle_proxies_reset",
                "module",
                "name",
                "num_ctrls",
                "orientation",
                "prefix",
                "proxies",
                "ribbon_base_name",
                "ribbon_end_name",
                "rot_order",
                "rotate_ribbon",
                "setup_name",
                "uuid",
                "equidistant",
                "proxy_inherit_name",
                "span_multiplier",
            ]
        )
        result_keys = sorted(list(a_ribbon_as_dict.keys()))
        self.assertEqual(expected_keys, result_keys)
        expected_module_value = "ModuleRibbon"
        result_module_value = a_ribbon_as_dict.get("module")
        self.assertEqual(expected_module_value, result_module_value)
        # Change Module and Test Module Level Serialization
        ribbon_module_instance.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")
        a_ribbon_as_dict = ribbon_module_instance.get_module_as_dict()
        self.assertIn("parent", a_ribbon_as_dict)
        # Transfer data to a new ribbon module
        a_2nd_ribbon_module = module_ribbon.ModuleRibbon()
        a_2nd_ribbon_module.read_data_from_dict(a_ribbon_as_dict)
        expected = ribbon_module_instance.get_module_as_dict()
        result = a_2nd_ribbon_module.get_module_as_dict()
        self.assertEqual(expected, result)

    def test_module_ribbon_read_proxies_from_dict(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        ribbon_module_instance.base_proxy.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")  # Changed the proxy
        a_ribbon_as_dict = ribbon_module_instance.get_module_as_dict()
        # Create a second module (new)
        a_2nd_ribbon_module = module_ribbon.ModuleRibbon()
        a_2nd_ribbon_module.read_proxies_from_dict(a_ribbon_as_dict.get("proxies"))
        expected = ribbon_module_instance.base_proxy.get_uuid()
        result = a_2nd_ribbon_module.base_proxy.get_uuid()
        self.assertEqual(expected, result)

    def test_module_ribbon_build_proxy(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        proxy_data_list = ribbon_module_instance.build_proxy()
        # Check ProxyData objects
        for proxy_data in proxy_data_list:
            self.assertIsInstance(proxy_data, tools_rig_frm.ProxyData)
            self.assertTrue(cmds.objExists(proxy_data.get_long_name()))
        # Check Maya Scene
        expected_nodes = [
            "C_ribbonBase_offset",
            "C_ribbonBase",
            "C_ribbon01_offset",
            "C_ribbon01",
            "C_ribbon02_offset",
            "C_ribbon02",
            "C_ribbonEnd_offset",
            "C_ribbonEnd",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("C_ribbonBase.proxyUUID"))
        self.assertTrue(cmds.objExists("C_ribbon01.proxyUUID"))
        self.assertTrue(cmds.objExists("C_ribbon02.proxyUUID"))
        self.assertTrue(cmds.objExists("C_ribbonEnd.proxyUUID"))

    def test_module_ribbon_build_proxy_within_project(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(ribbon_module_instance)
        a_project.build_proxy()
        expected_nodes = [
            "C_ribbonBase_offset",
            "C_ribbonBase",
            "C_ribbon01_offset",
            "C_ribbon01",
            "C_ribbon02_offset",
            "C_ribbon02",
            "C_ribbonEnd_offset",
            "C_ribbonEnd",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("C_ribbonBase.proxyUUID"))
        self.assertTrue(cmds.objExists("C_ribbon01.proxyUUID"))
        self.assertTrue(cmds.objExists("C_ribbon02.proxyUUID"))
        self.assertTrue(cmds.objExists("C_ribbonEnd.proxyUUID"))

    def test_module_ribbon_build_rig(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(ribbon_module_instance)
        a_project.build_proxy()
        a_project.build_rig()
        expected_elements = [
            "C_ribbonBase_JNT",
            "C_ribbon01_JNT",
            "C_ribbon02_JNT",
            "C_ribbonEnd_JNT",
            "C_ribbonEnd_JNT_parentConstraint",
            "C_ribbon02_JNT_parentConstraint",
            "C_ribbon01_JNT_parentConstraint",
            "C_ribbonBase_JNT_parentConstraint",
            "C_ribbonGlobal_offset",
            "C_ribbonGlobal_CTRL",
            "C_ribbonBase_IK_offset",
            "C_ribbonBase_IK_CTRL",
            "C_ribbon01_IK_offset",
            "C_ribbon01_IK_CTRL",
            "C_ribbon02_IK_offset",
            "C_ribbon02_IK_CTRL",
            "C_ribbonEnd_IK_offset",
            "C_ribbonEnd_IK_CTRL",
            "C_ribbonBase_offset",
            "C_ribbonBase_CTRL",
            "C_ribbon01_offset",
            "C_ribbon01_CTRL",
            "C_ribbon02_offset",
            "C_ribbon02_CTRL",
            "C_ribbonEnd_offset",
            "C_ribbonEnd_CTRL",
            "C_ribbon_grp",
            "C_ribbon_sur",
            "C_ribbonFollicle_01",
            "C_ribbonBase_JNT_fk",
            "C_ribbonFollicle_02",
            "C_ribbon01_JNT_fk",
            "C_ribbonFollicle_03",
            "C_ribbon02_JNT_fk",
            "C_ribbonFollicle_04",
            "C_ribbonEnd_JNT_fk",
            "C_ribbon_sur_twist",
            "C_ribbon_sur_wave",
            "C_ribbonTwistHandle",
            "C_ribbonSineHandle",
            "C_ribbon_bind_grp",
            "C_ribbonBase_IK_bind",
            "C_ribbonBase_IK_bind_parentConstraint1",
            "C_ribbon01_IK_bind",
            "C_ribbon01_IK_bind_parentConstraint1",
            "C_ribbon02_IK_bind",
            "C_ribbon02_IK_bind_parentConstraint1",
            "C_ribbonEnd_IK_bind",
            "C_ribbonEnd_IK_bind_parentConstraint1",
        ]

        for obj in expected_elements:
            self.assertTrue(cmds.objExists(obj), f"Missing expected object: {obj}")

    def test_module_ribbon_find_drivers_from_module(self):
        ribbon_module_instance = module_ribbon.ModuleRibbon()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(ribbon_module_instance)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        expected = [
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_ribbonGlobal_offset|C_ribbonGlobal_CTRL"
            "|C_ribbonBase_offset|C_ribbonBase_CTRL|C_ribbon01_offset|C_ribbon01_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_ribbonGlobal_offset|C_ribbonGlobal_CTRL"
            "|C_ribbon01_IK_offset|C_ribbon01_IK_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_ribbonGlobal_offset|C_ribbonGlobal_CTRL"
            "|C_ribbonBase_offset|C_ribbonBase_CTRL|C_ribbon01_offset|C_ribbon01_CTRL"
            "|C_ribbon02_offset|C_ribbon02_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_ribbonGlobal_offset|C_ribbonGlobal_CTRL"
            "|C_ribbon02_IK_offset|C_ribbon02_IK_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_ribbonGlobal_offset|C_ribbonGlobal_CTRL"
            "|C_ribbonBase_offset|C_ribbonBase_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_ribbonGlobal_offset|C_ribbonGlobal_CTRL"
            "|C_ribbonBase_IK_offset|C_ribbonBase_IK_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_ribbonGlobal_offset|C_ribbonGlobal_CTRL"
            "|C_ribbonBase_offset|C_ribbonBase_CTRL|C_ribbon01_offset|C_ribbon01_CTRL"
            "|C_ribbon02_offset|C_ribbon02_CTRL|C_ribbonEnd_offset|C_ribbonEnd_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_ribbonGlobal_offset|C_ribbonGlobal_CTRL"
            "|C_ribbonEnd_IK_offset|C_ribbonEnd_IK_CTRL",
        ]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=ribbon_module_instance.get_uuid(), filter_driver_type=None  # No filter means all types
        )
        self.assertEqual(expected, result)
