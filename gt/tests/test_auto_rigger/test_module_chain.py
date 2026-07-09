import unittest
import logging
import sys
import os

import gt.tools.auto_rigger.modules.module_chain as module_chain
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


class TestModuleChain(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        tools_maya_plugins.load_startup_plugins()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)

    def test_module_biped_chain_inheritance(self):
        chain_module_instance = module_chain.ModuleChain()
        result = isinstance(chain_module_instance, tools_rig_frm.ModuleGeneric)
        expected = True
        self.assertEqual(expected, result)

    def test_module_chain_inheritance_passthrough(self):
        chain_module_instance = module_chain.ModuleChain(
            name="mocked_chain", prefix="mocked_prefix", suffix="mocked_suffix"
        )
        result = chain_module_instance.name
        expected = "mocked_chain"
        self.assertEqual(expected, result)
        result = chain_module_instance.prefix
        expected = "mocked_prefix"
        self.assertEqual(expected, result)
        result = chain_module_instance.suffix
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_chain_basic_proxy_compliance(self):
        chain_module_instance = module_chain.ModuleChain()
        # Proxies Type
        result = type(chain_module_instance.proxies)
        expected = list
        self.assertEqual(expected, result, '"proxies" variable must be a list.')
        # Number of proxies
        result = len(chain_module_instance.proxies)
        expected = 3
        self.assertEqual(expected, result)
        # Proxy type (Proxies should only carry tools_rig_frm.Proxy objects)
        for proxy in chain_module_instance.proxies:
            message = f'An element in the proxies list is not a proxy instance. Issue object: "{str(proxy)}"'
            self.assertIsInstance(proxy, tools_rig_frm.Proxy, message)
        # Variable Names (Must end with "_proxy")
        proxy_vars = {
            key: value for key, value in vars(chain_module_instance).items() if isinstance(value, tools_rig_frm.Proxy)
        }
        for proxy_var_key in proxy_vars.keys():
            message = f'A proxy variables was not named correctly. Incorrect variable: "{str(proxy_var_key)}"'
            self.assertTrue(proxy_var_key.endswith("_proxy"), message)

    def test_module_chain_default_proxy_prefix(self):
        chain_module_instance = module_chain.ModuleChain()
        chain_prefix = chain_module_instance.get_prefix()
        expected = "C"
        self.assertEqual(expected, chain_prefix)

    def test_module_chain_default_proxy_suffix(self):
        chain_module_instance = module_chain.ModuleChain()
        chain_suffix = chain_module_instance.get_suffix()
        expected = None
        self.assertEqual(expected, chain_suffix)

    def test_module_chain_check_default_orientation(self):
        chain_module_instance = module_chain.ModuleChain()
        an_orientation_data = chain_module_instance.get_orientation_data()
        result = an_orientation_data.get_method()
        expected = "automatic"
        self.assertEqual(expected, result)

    def test_module_chain_proxy_names(self):
        chain_names = ["chain01", "chain02", "chain03"]
        chain_module_instance = module_chain.ModuleChain()
        for proxy in chain_module_instance.proxies:
            result = proxy.get_name()
            self.assertEqual(chain_names[chain_module_instance.proxies.index(proxy)], result)

    def test_module_chain_meta_purpose_names(self):
        chain_names = ["chain01", "chain02", "chain03"]
        chain_module_instance = module_chain.ModuleChain()
        for proxy in chain_module_instance.proxies:
            result = proxy.get_meta_purpose()
            self.assertEqual(chain_names[chain_module_instance.proxies.index(proxy)], result)

    def test_module_chain_base_proxy_driver_types(self):
        chain_module_instance = module_chain.ModuleChain()
        result = chain_module_instance.chain_base_proxy.get_driver_types()
        expected = [tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        self.assertEqual(expected, result)

    def test_module_chain_end_proxy_driver_types(self):
        chain_module_instance = module_chain.ModuleChain()
        result = chain_module_instance.chain_end_proxy.get_driver_types()
        expected = [tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        self.assertEqual(expected, result)

    def test_module_chain_get_module_as_dict(self):
        # Default Module
        chain_module_instance = module_chain.ModuleChain()
        a_chain_as_dict = chain_module_instance.get_module_as_dict()
        self.assertIsInstance(a_chain_as_dict, dict)
        expected_keys = sorted(
            [
                "active",
                "expanded",
                "chain_base_name",
                "chain_num",
                "ctrl_shapes",
                "module",
                "name",
                "orientation",
                "prefix",
                "proxies",
                "rot_order",
                "setup_name",
                "uuid",
            ]
        )
        result_keys = sorted(list(a_chain_as_dict.keys()))
        self.assertEqual(expected_keys, result_keys)
        expected_module_value = "ModuleChain"
        result_module_value = a_chain_as_dict.get("module")
        self.assertEqual(expected_module_value, result_module_value)
        # Change Module and Test Module Level Serialization
        chain_module_instance.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")
        a_chain_as_dict = chain_module_instance.get_module_as_dict()
        self.assertIn("parent", a_chain_as_dict)
        # Transfer data to a new chain module
        a_2nd_chain_module = module_chain.ModuleChain()
        a_2nd_chain_module.read_data_from_dict(a_chain_as_dict)
        expected = chain_module_instance.get_module_as_dict()
        result = a_2nd_chain_module.get_module_as_dict()
        self.assertEqual(expected, result)

    def test_module_chain_read_proxies_from_dict(self):
        chain_module_instance = module_chain.ModuleChain()
        chain_module_instance.chain_base_proxy.set_parent_uuid(
            "550e8400-e29b-41d4-a716-446655440000"
        )  # Changed the proxy
        a_chain_as_dict = chain_module_instance.get_module_as_dict()
        # Create a second module (new)
        a_2nd_chain_module = module_chain.ModuleChain()
        a_2nd_chain_module.read_proxies_from_dict(a_chain_as_dict.get("proxies"))
        expected = chain_module_instance.chain_base_proxy.get_uuid()
        result = a_2nd_chain_module.chain_base_proxy.get_uuid()
        self.assertEqual(expected, result)

    def test_module_chain_build_proxy(self):
        chain_module_instance = module_chain.ModuleChain()
        proxy_data_list = chain_module_instance.build_proxy()
        # Check ProxyData objects
        for proxy_data in proxy_data_list:
            self.assertIsInstance(proxy_data, tools_rig_frm.ProxyData)
            self.assertTrue(cmds.objExists(proxy_data.get_long_name()))
        # Check Maya Scene
        expected_nodes = [
            "C_chain01_offset",
            "C_chain01",
            "C_chain02_offset",
            "C_chain02",
            "C_chain03_offset",
            "C_chain03",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("C_chain01.proxyUUID"))
        self.assertTrue(cmds.objExists("C_chain02.proxyUUID"))
        self.assertTrue(cmds.objExists("C_chain03.proxyUUID"))

    def test_module_chain_build_proxy_within_project(self):
        chain_module_instance = module_chain.ModuleChain()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(chain_module_instance)
        a_project.build_proxy()
        expected_nodes = [
            "C_chain01_offset",
            "C_chain01",
            "C_chain02_offset",
            "C_chain02",
            "C_chain03_offset",
            "C_chain03",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("C_chain01.proxyUUID"))
        self.assertTrue(cmds.objExists("C_chain02.proxyUUID"))
        self.assertTrue(cmds.objExists("C_chain03.proxyUUID"))

    def test_module_chain_build_rig(self):
        chain_module_instance = module_chain.ModuleChain()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(chain_module_instance)
        a_project.build_proxy()
        a_project.build_rig()
        expected_elements = [
            "C_chain01_JNT",
            "C_chain02_JNT",
            "C_chain03_JNT",
            "C_chain01_offset",
            "C_chain01_CTRL",
            "C_chain02_offset",
            "C_chain02_CTRL",
            "C_chain03_offset",
            "C_chain03_CTRL",
            "C_chain01_JNT_fk",
            "C_chain02_JNT_fk",
            "C_chain03_JNT_fk",
            "C_chain01_JNT_fk_parentConstraint",
            "C_chain02_JNT_fk_parentConstraint",
            "C_chain03_JNT_fk_parentConstraint",
        ]

        for obj in expected_elements:
            self.assertTrue(cmds.objExists(obj))

    def test_module_chain_find_drivers_from_module(self):
        chain_module_instance = module_chain.ModuleChain()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(chain_module_instance)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        expected = [
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_chain01_offset|C_chain01_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_chain01_offset|C_chain01_CTRL|C_chain02_offset"
            "|C_chain02_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_chain01_offset|C_chain01_CTRL|C_chain02_offset"
            "|C_chain02_CTRL|C_chain03_offset|C_chain03_CTRL",
        ]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=chain_module_instance.get_uuid(), filter_driver_type=None  # No filter means all types
        )
        self.assertEqual(expected, result)
