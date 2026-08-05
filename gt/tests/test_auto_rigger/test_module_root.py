import unittest
import logging
import json
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
import gt.core.color as core_color
from gt.tests import maya_test_tools

cmds = maya_test_tools.cmds


class TestModuleRoot(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_module_root_inheritance(self):
        a_root_module = tools_mod_root.ModuleRoot()
        result = isinstance(a_root_module, tools_rig_frm.ModuleGeneric)
        expected = True
        self.assertEqual(expected, result)

    def test_module_root_inheritance_passthrough(self):
        a_root_module = tools_mod_root.ModuleRoot(name="mocked_root", prefix="mocked_prefix", suffix="mocked_suffix")
        result = a_root_module.name
        expected = "mocked_root"
        self.assertEqual(expected, result)
        result = a_root_module.prefix
        expected = "mocked_prefix"
        self.assertEqual(expected, result)
        result = a_root_module.suffix
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_root_basic_proxy_compliance(self):
        a_root_module = tools_mod_root.ModuleRoot()
        # Proxies Type
        result = type(a_root_module.proxies)
        expected = list
        self.assertEqual(expected, result, '"proxies" variable must be a list.')
        # Number of proxies
        result = len(a_root_module.proxies)
        expected = 1
        self.assertEqual(expected, result)
        # Proxy type (Proxies should only carry tools_rig_frm.Proxy objects)
        for proxy in a_root_module.proxies:
            message = f'An element in the proxies list is not a proxy instance. Issue object: "{str(proxy)}"'
            self.assertIsInstance(proxy, tools_rig_frm.Proxy, message)
        # Variable Names (Must end with "_proxy")
        proxy_vars = {
            key: value for key, value in vars(a_root_module).items() if isinstance(value, tools_rig_frm.Proxy)
        }
        for proxy_var_key in proxy_vars.keys():
            message = f'A proxy variables was not named correctly. Incorrect variable: "{str(proxy_var_key)}"'
            self.assertTrue(proxy_var_key.endswith("_proxy"), message)

    def test_module_root_default_proxy_prefix(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_proxy = a_root_module.get_prefix()
        expected = "C"
        self.assertEqual(expected, a_proxy)

    def test_module_root_default_proxy_suffix(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_proxy = a_root_module.get_suffix()
        expected = None
        self.assertEqual(expected, a_proxy)

    def test_module_root_default_proxy_orientation_data(self):
        a_root_module = tools_mod_root.ModuleRoot()
        an_orientation_data = a_root_module.get_orientation_data()
        result = an_orientation_data.get_method()
        expected = "inherit"
        self.assertEqual(expected, result)

    def test_module_root_default_proxy_name(self):
        a_root_module = tools_mod_root.ModuleRoot()
        result = a_root_module.root_proxy.get_name()
        expected = "root"
        self.assertEqual(expected, result)

    def test_module_root_default_proxy_locator_scale(self):
        a_root_module = tools_mod_root.ModuleRoot()
        result = a_root_module.root_proxy.get_locator_scale()
        expected = 3
        self.assertEqual(expected, result)

    def test_module_root_default_proxy_meta_purpose(self):
        a_root_module = tools_mod_root.ModuleRoot()
        result = a_root_module.root_proxy.get_meta_purpose()
        expected = "root"
        self.assertEqual(expected, result)

    def test_module_root_default_proxy_driver_types(self):
        a_root_module = tools_mod_root.ModuleRoot()
        result = a_root_module.root_proxy.get_driver_types()
        expected = [tools_rig_const.RiggerDriverTypes.BLOCK, tools_rig_const.RiggerDriverTypes.FK]
        self.assertEqual(expected, result)

    def test_module_root_default_proxy_color(self):
        """
        Not a really necessary/valuable test, but I'll leave it here to test default value.
        """
        a_root_module = tools_mod_root.ModuleRoot()
        a_attr_dict = a_root_module.root_proxy.get_attr_dict()
        result = a_attr_dict.get("colorDefault")
        expected = list(core_color.ColorConstants.RigProxy.TWEAK)
        self.assertEqual(expected, result)

    def test_module_root_get_module_as_dict(self):
        # Default Module
        a_root_module = tools_mod_root.ModuleRoot()
        a_root_as_dict = a_root_module.get_module_as_dict()
        self.assertIsInstance(a_root_as_dict, dict)
        expected_keys = sorted(
            [
                "active",
                "code",
                "enable_scale",
                "expanded",
                "matches_proxy_rot",
                "module",
                "name",
                "orientation",
                "prefix",
                "proxies",
                "uuid",
            ]
        )
        result_keys = sorted(list(a_root_as_dict.keys()))
        self.assertEqual(expected_keys, result_keys)
        expected_module_value = "ModuleRoot"
        result_module_value = a_root_as_dict.get("module")
        self.assertEqual(expected_module_value, result_module_value)
        # Change Module and Test Module Level Serialization
        a_root_module.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")
        a_root_as_dict = a_root_module.get_module_as_dict()
        self.assertIn("parent", a_root_as_dict)
        # Transfer data to a new root module
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module.read_data_from_dict(a_root_as_dict)
        expected = a_root_module.get_module_as_dict()
        result = a_2nd_root_module.get_module_as_dict()
        self.assertEqual(expected, result)

    def test_module_root_read_proxies_from_dict(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_root_module.root_proxy.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")  # Changed the proxy
        a_root_as_dict = a_root_module.get_module_as_dict()
        # Create a second module (new)
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module.read_proxies_from_dict(a_root_as_dict.get("proxies"))
        expected = a_root_module.root_proxy.get_uuid()
        result = a_2nd_root_module.root_proxy.get_uuid()
        self.assertEqual(expected, result)

    def test_module_root_build_proxy(self):
        a_root = tools_mod_root.ModuleRoot()
        proxy_data_list = a_root.build_proxy()
        # Check ProxyData objects
        for proxy_data in proxy_data_list:
            self.assertIsInstance(proxy_data, tools_rig_frm.ProxyData)
            self.assertTrue(cmds.objExists(proxy_data.get_long_name()))
        # Check Maya Scene
        expected_nodes = ["C_root", "C_root_offset"]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("C_root.proxyUUID"))

    def test_module_root_build_proxy_within_project(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        expected_nodes = ["C_root", "C_root_offset"]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("C_root.proxyUUID"))

    def test_module_root_build_proxy_setup_root_visibility(self):
        """
        This test is somewhat narrow. We don't need to test all attributes for all modules.
        Feel free to focus on testing only attributes that are vital to the functionality of the module instead.
        """
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        result_exists = cmds.objExists("C_globalProxy.rootVisibility")
        result_type = cmds.getAttr("C_globalProxy.rootVisibility", typ=True)
        result_connection = cmds.listConnections("C_globalProxy.rootVisibility", plugs=True)
        expected_exists = True
        expected_type = "bool"
        expected_connection = [
            "locShape.visibility",
            "sphereShape.visibility",
            "snappingPointShape.visibility",
            "sphereShapeOrig.visibility",
            "locShapeOrig.visibility",
        ]
        self.assertEqual(expected_exists, result_exists)
        self.assertEqual(result_type, expected_type)
        self.assertEqual(result_connection, expected_connection)

    def test_module_root_build_rig(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()
        expected_elements = [
            "C_root_JNT",
            "C_root_offset",
            "C_root_parentOffset",
            "C_root_CTRL",
        ]
        for obj in expected_elements:
            self.assertTrue(cmds.objExists(obj))

    def test_module_root_build_rig_ctrl_color(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.build_proxy()
        a_project.build_rig()
        color_tuple = cmds.getAttr("C_root_CTRL.overrideColorRGB")[0]
        result = tuple(round(value, 3) for value in color_tuple)
        expected = core_color.ColorConstants.RigProxy.TWEAK
        self.assertEqual(expected, result)

    def test_module_root_multiple_root_modules(self):
        """
        This helps validate non-unique name issues.
        It means that all elements are accessed using UUID or full path.
        """
        a_root_module_one = tools_mod_root.ModuleRoot()
        a_root_module_two = tools_mod_root.ModuleRoot()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module_one)
        a_project.add_to_modules(a_root_module_two)
        a_project.build_proxy()
        a_project.build_rig()
        expected_elements = [
            "C_root_JNT",
            "C_root_JNT1",
            "C_root_offset",
            "C_root_offset2",
            "C_root_offset|C_root_parentOffset|C_root_CTRL",
            "C_root_offset2|C_root_parentOffset|C_root_CTRL",
        ]
        for obj in expected_elements:
            self.assertTrue(cmds.objExists(obj), f"Missing expected object: {obj}")

    def test_module_root_position_multiple_root_modules(self):
        a_root_module_one = tools_mod_root.ModuleRoot()
        a_root_module_two = tools_mod_root.ModuleRoot()
        a_root_module_two.root_proxy.set_initial_position(x=10)

        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module_one)
        a_project.add_to_modules(a_root_module_two)
        a_project.build_proxy()
        a_project.build_rig()

        expected_a_root_one_pos = [(0.0, 0.0, 0.0)]
        result_a_root_one = cmds.getAttr("C_root_JNT.translate")
        self.assertEqual(expected_a_root_one_pos, result_a_root_one)

        expected_a_root_two_pos = [(10.0, 0.0, 0.0)]
        result_a_root_two = cmds.getAttr("C_root_JNT1.translate")
        self.assertEqual(expected_a_root_two_pos, result_a_root_two)

        expected_a_root_ctrl_pos = [(0.0, 0.0, 0.0)]
        result_a_root_ctrl = cmds.getAttr("C_root_offset|C_root_parentOffset|C_root_CTRL.translate")
        self.assertEqual(expected_a_root_ctrl_pos, result_a_root_ctrl)

        expected_a_root_two_ctrl_pos = cmds.getAttr("C_root_JNT1.worldMatrix")
        result_a_root_two_ctrl = cmds.getAttr("C_root_offset2|C_root_parentOffset|C_root_CTRL.worldMatrix")
        self.assertEqual(expected_a_root_two_ctrl_pos, result_a_root_two_ctrl)

    def test_module_root_parenting_modules(self):
        a_root_module = tools_mod_root.ModuleRoot()
        a_module = tools_rig_frm.ModuleGeneric()
        a_proxy = a_module.add_new_proxy()
        a_proxy.set_parent_uuid_from_proxy(a_root_module.root_proxy)
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.add_to_modules(a_module)
        a_project.build_proxy()
        a_project.build_rig()
        result = cmds.ls(typ="joint")

        expected = ["C_root_JNT", "proxy_JNT"]
        self.assertEqual(expected, result, f"Failed to build expected joints.")
        result = cmds.listRelatives("C_root_JNT", typ="joint", children=True)
        expected = ["proxy_JNT"]
        self.assertEqual(expected, result, f'Missing expected child for "C_root_JNT".')
        self.assertTrue(cmds.objExists("|rig|skeleton|C_root_JNT|proxy_JNT"))

    def test_module_root_serialization(self):
        # Create Initial Test Setup
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_root_module = tools_mod_root.ModuleRoot()  # Default initial location (origin)
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        a_2nd_root_module.root_proxy.set_initial_position(x=10)  # Starts a little bit to the side
        a_2nd_root_module.set_prefix("ABC")
        a_proxy = a_generic_module.add_new_proxy()
        a_proxy_uuid = a_proxy.get_uuid()  # Store UUID for later
        a_proxy.set_initial_position(x=5)  # Starts a little bit to the side
        a_proxy.set_parent_uuid_from_proxy(a_root_module.root_proxy)  # Generic Proxy is the child of the root
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_root_module)
        a_project.add_to_modules(a_generic_module)
        a_project.add_to_modules(a_2nd_root_module)
        # Build Proxy, Modify it, Read changes
        a_project.build_proxy()
        cmds.setAttr("C_root.ty", 15)  # Move "a_root_module.root_proxy" up a bit
        a_project.read_data_from_scene()
        a_project.build_rig()
        a_project_as_dict = a_project.get_project_as_dict()  # Serialized Dictionary
        a_project_as_json = json.dumps(a_project_as_dict)  # Emulate JSON environment

        # Create New Project and Ingest Data -------------------------------------------------------------------
        cmds.file(new=True, force=True)  # Clear Scene
        a_2nd_project = tools_rig_frm.RigProject()
        a_2nd_project_ingest_dict = json.loads(a_project_as_json)
        a_2nd_project.read_data_from_dict(a_2nd_project_ingest_dict)
        a_2nd_project.build_proxy()
        # Test Proxies and Data Transfer
        expected_ty = 15
        result_ty = cmds.getAttr("C_root.ty")
        self.assertEqual(expected_ty, result_ty)
        expected_tx = 10
        result_tx = cmds.getAttr("ABC_secondRoot.tx")
        self.assertEqual(expected_tx, result_tx)
        expected_tx = 5
        result_tx = cmds.getAttr("proxy.tx")
        self.assertEqual(expected_tx, result_tx)
        # Test Build Rig with Ingested Data
        a_2nd_project.build_rig()
        expected_ty = 15
        result_ty = cmds.getAttr("C_root_JNT.ty")
        self.assertEqual(expected_ty, result_ty)
        expected_tx = 10
        result_tx = cmds.getAttr("ABC_secondRoot_JNT.tx")
        self.assertEqual(expected_tx, result_tx)
        expected_tx = 5
        result_tx = cmds.getAttr("proxy_JNT.tx")
        self.assertEqual(expected_tx, result_tx)
        expected_proxy_uuid = a_proxy_uuid
        result_tx = cmds.getAttr(f"proxy_JNT.{tools_rig_const.RiggerConstants.ATTR_JOINT_UUID}")
        self.assertEqual(expected_proxy_uuid, result_tx)

    def test_module_root_find_drivers_from_module(self):
        # Create multiple modules to test separation
        a_1st_root_module = tools_mod_root.ModuleRoot()
        a_2nd_root_module = tools_mod_root.ModuleRoot()
        # Configure Proxies
        a_2nd_root_module.root_proxy.set_name("secondRoot")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_root_module)
        a_project.add_to_modules(a_2nd_root_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        expected = ["|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL"]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module.get_uuid(), filter_driver_type=None  # No filter means all types
        )
        self.assertEqual(expected, result)
        # Check what you get when filtering by type. The root only has one type, FK so that's the only test.
        expected = ["|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_root_offset|C_root_parentOffset|C_root_CTRL"]
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_root_module.get_uuid(), filter_driver_type=tools_rig_const.RiggerDriverTypes.FK
        )
        self.assertEqual(expected, result)
