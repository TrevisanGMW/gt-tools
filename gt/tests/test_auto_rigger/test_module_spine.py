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
import gt.tools.auto_rigger.modules.module_spine as tools_mod_spine
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.core.color as core_color
from gt.tests import maya_test_tools

cmds = maya_test_tools.cmds


class TestModuleSpine(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_module_spine_inheritance(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        result = isinstance(a_spine_module, tools_rig_frm.ModuleGeneric)
        expected = True
        self.assertEqual(expected, result)

    def test_module_spine_inheritance_passthrough(self):
        a_spine_module = tools_mod_spine.ModuleSpine(name="mocked_name", prefix="mocked_prefix", suffix="mocked_suffix")
        result = a_spine_module.name
        expected = "mocked_name"
        self.assertEqual(expected, result)
        result = a_spine_module.prefix
        expected = "mocked_prefix"
        self.assertEqual(expected, result)
        result = a_spine_module.suffix
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_spine_basic_proxy_compliance(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        # Proxies Type
        result = type(a_spine_module.proxies)
        expected = list
        self.assertEqual(expected, result, '"proxies" variable must be a list.')
        # Number of proxies
        result = len(a_spine_module.proxies)
        expected = 4
        self.assertEqual(expected, result)
        # Proxy type (Proxies should only carry tools_rig_frm.Proxy objects)
        for proxy in a_spine_module.proxies:
            message = f'An element in the proxies list is not a proxy instance. Issue object: "{str(proxy)}"'
            self.assertIsInstance(proxy, tools_rig_frm.Proxy, message)
        # Variable Names (Must end with "_proxy")
        proxy_vars = {
            key: value for key, value in vars(a_spine_module).items() if isinstance(value, tools_rig_frm.Proxy)
        }
        for proxy_var_key in proxy_vars.keys():
            message = f'A proxy variables was not named correctly. Incorrect variable: "{str(proxy_var_key)}"'
            self.assertTrue(proxy_var_key.endswith("_proxy"), message)

    def test_module_spine_get_module_as_dict(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        a_spine_as_dict = a_spine_module.get_module_as_dict()
        self.assertIsInstance(a_spine_as_dict, dict)

        expected_keys = sorted(
            [
                "active",
                "expanded",
                "cog_name",
                "dropoff_rate",
                "hips_name",
                "module",
                "name",
                "orientation",
                "prefix",
                "proxies",
                "setup_name",
                "spine_number",
                "uuid",
                "world_ctrls",
            ]
        )
        result_keys = sorted(list(a_spine_as_dict.keys()))
        self.assertEqual(expected_keys, result_keys)

        expected_module_value = "ModuleSpine"
        result_module_value = a_spine_as_dict.get("module")
        self.assertEqual(expected_module_value, result_module_value)

        # Change Module and Test Module Level Serialization
        a_spine_module.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")
        a_spine_as_dict = a_spine_module.get_module_as_dict()
        self.assertIn("parent", a_spine_as_dict)

        # Transfer data to a new spine module
        a_2nd_spine_module = tools_mod_spine.ModuleSpine()
        a_2nd_spine_module.read_data_from_dict(a_spine_as_dict)
        expected = a_spine_module.get_module_as_dict()
        result = a_2nd_spine_module.get_module_as_dict()
        self.assertEqual(expected, result)

    def test_module_spine_read_proxies_from_dict(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        a_spine_module.hip_proxy.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")  # Changed the proxy
        a_spine_as_dict = a_spine_module.get_module_as_dict()
        # Create a second new module
        a_2nd_spine_module = tools_mod_spine.ModuleSpine()
        a_2nd_spine_module.read_proxies_from_dict(a_spine_as_dict.get("proxies"))
        expected = a_spine_module.hip_proxy.get_uuid()
        result = a_2nd_spine_module.hip_proxy.get_uuid()
        self.assertEqual(expected, result)

    def test_module_spine_build_proxy(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        proxy_data_list = a_spine_module.build_proxy()

        # Check ProxyData objects
        for proxy_data in proxy_data_list:
            self.assertIsInstance(proxy_data, tools_rig_frm.ProxyData)
            self.assertTrue(cmds.objExists(proxy_data.get_long_name()))

        # Check Maya Scene
        expected_nodes = [
            "C_hips",
            "C_hips_offset",
            "C_spine01",
            "C_spine01_offset",
            "C_spine02",
            "C_spine02_offset",
            "C_spine03",
            "C_spine03_offset",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node), f'Missing expected node: "{node}""')
            if not node.endswith("_offset"):
                self.assertTrue(cmds.objExists(f"{node}.proxyUUID"))

    def test_module_spine_build_proxy_within_project(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()

        expected_nodes = [
            "C_hips",
            "C_hips_offset",
            "C_spine01",
            "C_spine01_offset",
            "C_spine02",
            "C_spine02_offset",
            "C_spine03",
            "C_spine03_offset",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node), f'Missing expected node: "{node}""')
            if not node.endswith("_offset"):
                self.assertTrue(cmds.objExists(f"{node}.proxyUUID"))

    def test_module_spine_serialization(self):
        # Create Initial Test Setup
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_spine_module = tools_mod_spine.ModuleSpine()  # Default initial location (origin)
        a_2nd_spine_module = tools_mod_spine.ModuleSpine()
        a_2nd_spine_module.hip_proxy.set_name("secondHip")
        a_2nd_spine_module.hip_proxy.set_initial_position(x=10)  # Starts a little bit to the side
        a_2nd_spine_module.set_prefix("ABC")
        a_proxy = a_generic_module.add_new_proxy()
        a_proxy_uuid = a_proxy.get_uuid()  # Store UUID for later
        a_proxy.set_initial_position(x=5)  # Starts a little bit to the side
        a_proxy.set_parent_uuid_from_proxy(a_spine_module.hip_proxy)  # Generic Proxy is the child of the hip
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.add_to_modules(a_generic_module)
        a_project.add_to_modules(a_2nd_spine_module)
        # Build Proxy, Modify it, Read changes
        a_project.build_proxy()
        cmds.xform("C_hips", t=(0, 15, 0), ws=True)
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
        result_ty = cmds.xform("C_hips", t=True, q=True, ws=True)[1]
        self.assertEqual(expected_ty, result_ty)
        expected_tx = 10
        result_tx = cmds.getAttr("ABC_secondHip.tx")
        self.assertEqual(expected_tx, result_tx)
        expected_tx = 5
        result_tx = cmds.getAttr("proxy.tx")
        self.assertEqual(expected_tx, result_tx)
        # Test Build Rig with Ingested Data
        a_2nd_project.build_rig()
        expected_ty = 15
        result_ty = cmds.getAttr("C_hips_JNT.ty")
        self.assertEqual(expected_ty, result_ty)
        expected_tx = 10
        result_tx = cmds.getAttr("ABC_secondHip_JNT.tx")
        self.assertEqual(expected_tx, result_tx)
        expected_tx = 5
        result_tx = cmds.xform("proxy_JNT", t=True, q=True, ws=True)[0]
        self.assertEqual(expected_tx, result_tx)
        expected_proxy_uuid = a_proxy_uuid
        result_tx = cmds.getAttr(f"proxy_JNT.{tools_rig_const.RiggerConstants.ATTR_JOINT_UUID}")
        self.assertEqual(expected_proxy_uuid, result_tx)

    def test_module_spine_find_drivers_from_module(self):
        # Create multiple modules to test separation
        a_1st_spine_module = tools_mod_spine.ModuleSpine()
        a_2nd_spine_module = tools_mod_spine.ModuleSpine()
        # Set prefix name
        a_2nd_spine_module.set_prefix("SCN")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_spine_module)
        a_project.add_to_modules(a_2nd_spine_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        expected = sorted(
            [
                "C_cogOffset_CTRL",
                "C_cogPivot_CTRL",
                "C_cog_CTRL",
                "C_hipsOffset_CTRL",
                "C_hipsPivot_CTRL",
                "C_hips_CTRL",
                "C_spine01_CTRL",
                "C_spine02_CTRL",
                "C_spine03_CTRL",
                "C_spine03_driver",
                "C_spineMid_IK_CTRL",
                "C_spineOffset_IK_CTRL",
                "C_spinePivot_IK_CTRL",
                "C_spine_CTRL",
                "C_spine_IK_CTRL",
            ]
        )
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_spine_module.get_uuid(), filter_driver_type=None  # No filter means all types
        )
        result = sorted([node.get_short_name() for node in result])
        self.assertEqual(expected, result)

        # Check what you get when filtering by type with FK.
        expected = sorted(
            [
                "C_hips_CTRL",
                "C_spine01_CTRL",
                "C_spine02_CTRL",
                "C_spine03_CTRL",
            ]
        )
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_spine_module.get_uuid(), filter_driver_type=tools_rig_const.RiggerDriverTypes.FK
        )
        result = sorted([node.get_short_name() for node in result])
        self.assertEqual(expected, result)

        # Check what you get when filtering by type with IK.
        expected = sorted(["C_spineMid_IK_CTRL", "C_spine_IK_CTRL"])
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_spine_module.get_uuid(), filter_driver_type=tools_rig_const.RiggerDriverTypes.IK
        )
        result = sorted([node.get_short_name() for node in result])
        self.assertEqual(expected, result)

        # Check what you get when filtering by type with Switch.
        expected = sorted(["C_spine_CTRL"])
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_spine_module.get_uuid(), filter_driver_type=tools_rig_const.RiggerDriverTypes.SWITCH
        )
        result = sorted([node.get_short_name() for node in result])
        self.assertEqual(expected, result)

    def test_module_spine_proxy_pose_default(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()

        world_positions_proxy = [
            ("C_hips", [0.0, 84.5, 0.0]),
            ("C_spine01", [0.0, 94.5, 0.0]),
            ("C_spine02", [0.0, 104.5, 0.0]),
            ("C_spine03", [0.0, 114.5, 0.0]),
        ]

        for joint_name, expected in world_positions_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("C_hips", [0.0, 0.0, 0.0]),
            ("C_spine01", [0.0, 0.0, 0.0]),
            ("C_spine02", [0.0, 0.0, 0.0]),
            ("C_spine03", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_spine_proxy_pose_a(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        # Setup Project
        a_spine_module.chest_proxy.set_initial_position(xyz=[2, 10, 8])
        a_spine_module.hip_proxy.set_initial_position(xyz=[9, 5, 4])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()

        world_positions_proxy = [
            ("C_hips", [9.0, 5.0, 4.0]),
            ("C_spine01", [6.67, 6.67, 5.33]),
            ("C_spine02", [4.33, 8.33, 6.67]),
            ("C_spine03", [2.0, 10.0, 8.0]),
        ]

        for joint_name, expected in world_positions_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("C_hips", [0.0, 0.0, 0.0]),
            ("C_spine01", [0.0, 0.0, 0.0]),
            ("C_spine02", [0.0, 0.0, 0.0]),
            ("C_spine03", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_spine_proxy_pose_b(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        # Setup Project
        a_spine_module.chest_proxy.set_initial_position(xyz=[5, 6, 33])
        a_spine_module.hip_proxy.set_initial_position(xyz=[4, 23, 1])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()

        world_positions_proxy = [
            ("C_hips", [4.0, 23.0, 1.0]),
            ("C_spine01", [4.33, 17.33, 11.67]),
            ("C_spine02", [4.67, 11.67, 22.33]),
            ("C_spine03", [5.0, 6.0, 33.0]),
        ]

        for joint_name, expected in world_positions_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("C_hips", [0.0, 0.0, 0.0]),
            ("C_spine01", [0.0, 0.0, 0.0]),
            ("C_spine02", [0.0, 0.0, 0.0]),
            ("C_spine03", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_spine_joint_pose_default(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_joints = [
            ("C_hips_JNT", [0.0, 84.5, 0.0]),
            ("C_spine01_JNT", [0.0, 94.5, 0.0]),
            ("C_spine02_JNT", [0.0, 104.5, 0.0]),
            ("C_spine03_JNT", [0.0, 114.5, 0.0]),
            ("C_hips_JNT_fk", [0.0, 84.5, 0.0]),
            ("C_spine01_JNT_fk", [0.0, 94.5, 0.0]),
            ("C_spine02_JNT_fk", [0.0, 104.5, 0.0]),
            ("C_spine03_JNT_fk", [0.0, 114.5, 0.0]),
            ("C_hips_JNT_ik", [0.0, 84.5, 0.0]),
            ("C_spine01_JNT_ik", [0.0, 94.5, 0.0]),
            ("C_spine02_JNT_ik", [0.0, 104.5, 0.0]),
            ("C_spine03_JNT_ik", [0.0, 114.5, 0.0]),
        ]

        for joint_name, expected in world_positions_joints:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_joints = [
            ("C_hips_JNT", [90.0, 90.0, 0.0]),
            ("C_spine01_JNT", [90.0, 90.0, 0.0]),
            ("C_spine02_JNT", [90.0, 90.0, 0.0]),
            ("C_spine03_JNT", [90.0, 90.0, 0.0]),
            ("C_hips_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_spine01_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_spine02_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_spine03_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_hips_JNT_ik", [90.0, 90.0, 0.0]),
            ("C_spine01_JNT_ik", [90.0, 90.0, 0.0]),
            ("C_spine02_JNT_ik", [90.0, 90.0, 0.0]),
            ("C_spine03_JNT_ik", [90.0, 90.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_joints:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_spine_joint_pose_a(self):
        a_spine_module = tools_mod_spine.ModuleSpine(world_ctrls=True)
        # Setup Project
        a_spine_module.chest_proxy.set_initial_position(xyz=[2, 10, 8])
        a_spine_module.hip_proxy.set_initial_position(xyz=[9, 5, 4])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_joints = [
            ("C_hips_JNT", [9.0, 5.0, 4.0]),
            ("C_spine01_JNT", [6.67, 6.67, 5.33]),
            ("C_spine02_JNT", [4.33, 8.33, 6.67]),
            ("C_spine03_JNT", [2.0, 10.0, 8.0]),
            ("C_hips_JNT_fk", [9.0, 5.0, 4.0]),
            ("C_spine01_JNT_fk", [6.67, 6.67, 5.33]),
            ("C_spine02_JNT_fk", [4.33, 8.33, 6.67]),
            ("C_spine03_JNT_fk", [2.0, 10.0, 8.0]),
            ("C_hips_JNT_ik", [9.0, 5.0, 4.0]),
            ("C_spine01_JNT_ik", [6.67, 6.67, 5.33]),
            ("C_spine02_JNT_ik", [4.33, 8.33, 6.67]),
            ("C_spine03_JNT_ik", [2.0, 10.0, 8.0]),
        ]

        for joint_name, expected in world_positions_joints:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_joints = [
            ("C_hips_JNT", [90.0, 90.0, 0.0]),
            ("C_spine01_JNT", [90.0, 90.0, 0.0]),
            ("C_spine02_JNT", [90.0, 90.0, 0.0]),
            ("C_spine03_JNT", [90.0, 90.0, 0.0]),
            ("C_hips_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_spine01_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_spine02_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_spine03_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_hips_JNT_ik", [90.0, 90.0, 0.0]),
            ("C_spine01_JNT_ik", [90.0, 90.0, 0.0]),
            ("C_spine02_JNT_ik", [90.0, 90.0, 0.0]),
            ("C_spine03_JNT_ik", [90.0, 90.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_joints:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_spine_joint_pose_b(self):
        a_spine_module = tools_mod_spine.ModuleSpine(world_ctrls=True)
        # Setup Project
        cmds.file(new=True, force=True)
        a_spine_module.chest_proxy.set_initial_position(xyz=[5, 6, 33])
        a_spine_module.hip_proxy.set_initial_position(xyz=[4, 23, 1])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_joints = [
            ("C_hips_JNT", [4.0, 23.0, 1.0]),
            ("C_spine01_JNT", [4.33, 17.33, 11.67]),
            ("C_spine02_JNT", [4.67, 11.67, 22.33]),
            ("C_spine03_JNT", [5.0, 6.0, 33.0]),
            ("C_hips_JNT_fk", [4.0, 23.0, 1.0]),
            ("C_spine01_JNT_fk", [4.33, 17.33, 11.67]),
            ("C_spine02_JNT_fk", [4.67, 11.67, 22.33]),
            ("C_spine03_JNT_fk", [5.0, 6.0, 33.0]),
            ("C_hips_JNT_ik", [4.0, 23.0, 1.0]),
            ("C_spine01_JNT_ik", [4.33, 17.33, 11.67]),
            ("C_spine02_JNT_ik", [4.67, 11.67, 22.33]),
            ("C_spine03_JNT_ik", [5.0, 6.0, 33.0]),
        ]

        for joint_name, expected in world_positions_joints:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_joints = [
            ("C_hips_JNT", [90.0, 90.0, 0.0]),
            ("C_spine01_JNT", [90.0, 90.0, 0.0]),
            ("C_spine02_JNT", [90.0, 90.0, 0.0]),
            ("C_spine03_JNT", [90.0, 90.0, 0.0]),
            ("C_hips_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_spine01_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_spine02_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_spine03_JNT_fk", [90.0, 90.0, 0.0]),
            ("C_hips_JNT_ik", [90.0, 90.0, 0.0]),
            ("C_spine01_JNT_ik", [90.0, 90.0, 0.0]),
            ("C_spine02_JNT_ik", [90.0, 90.0, 0.0]),
            ("C_spine03_JNT_ik", [90.0, 90.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_joints:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_spine_control_pose_default(self):
        a_spine_module = tools_mod_spine.ModuleSpine()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_controls = [
            ("C_cog_CTRL", [0.0, 84.5, 0.0]),
            ("C_spine_CTRL", [0.0, 84.5, 0.0]),
            ("C_hips_CTRL", [0.0, 84.5, 0.0]),
            ("C_hipsOffset_CTRL", [0.0, 84.5, 0.0]),
            ("C_hipsPivot_CTRL", [0.0, 84.5, 0.0]),
            ("C_spine01_CTRL", [0.0, 94.5, 0.0]),
            ("C_spine02_CTRL", [0.0, 104.5, 0.0]),
            ("C_spine03_CTRL", [0.0, 114.5, 0.0]),
            ("C_spine_IK_CTRL", [0.0, 114.5, 0.0]),
            ("C_spineOffset_IK_CTRL", [0.0, 114.5, 0.0]),
            ("C_spinePivot_IK_CTRL", [0.0, 114.5, 0.0]),
            ("C_spineMid_IK_CTRL", [0.0, 99.5, 0.0]),
        ]

        for joint_name, expected in world_positions_controls:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_controls = [
            ("C_cog_CTRL", [0.0, 0.0, 0.0]),
            ("C_spine_CTRL", [0.0, 0.0, 0.0]),
            ("C_hips_CTRL", [90.0, 90.0, 0.0]),
            ("C_hipsOffset_CTRL", [90.0, 90.0, 0.0]),
            ("C_hipsPivot_CTRL", [0.0, 0.0, 0.0]),
            ("C_spine01_CTRL", [90.0, 90.0, 0.0]),
            ("C_spine02_CTRL", [90.0, 90.0, 0.0]),
            ("C_spine03_CTRL", [90.0, 90.0, 0.0]),
            ("C_spine_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_spineOffset_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_spinePivot_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_spineMid_IK_CTRL", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_controls:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_spine_control_pose_a(self):
        a_spine_module = tools_mod_spine.ModuleSpine(world_ctrls=True)
        # Setup Project
        a_spine_module.chest_proxy.set_initial_position(xyz=[2, 10, 8])
        a_spine_module.hip_proxy.set_initial_position(xyz=[9, 5, 4])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_controls = [
            ("C_cog_CTRL", [9.0, 5.0, 4.0]),
            ("C_spine_CTRL", [9.0, 5.0, 4.0]),
            ("C_hips_CTRL", [9.0, 5.0, 4.0]),
            ("C_hipsOffset_CTRL", [9.0, 5.0, 4.0]),
            ("C_hipsPivot_CTRL", [9.0, 5.0, 4.0]),
            ("C_spine01_CTRL", [6.67, 6.67, 5.33]),
            ("C_spine02_CTRL", [4.33, 8.33, 6.67]),
            ("C_spine03_CTRL", [2.0, 10.0, 8.0]),
            ("C_spine_IK_CTRL", [2.0, 10.0, 8.0]),
            ("C_spineOffset_IK_CTRL", [2.0, 10.0, 8.0]),
            ("C_spinePivot_IK_CTRL", [2.0, 10.0, 8.0]),
            ("C_spineMid_IK_CTRL", [5.5, 7.5, 6.0]),
        ]

        for joint_name, expected in world_positions_controls:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_controls = [
            ("C_cog_CTRL", [0.0, 0.0, 0.0]),
            ("C_spine_CTRL", [0.0, 0.0, 0.0]),
            ("C_hips_CTRL", [90.0, 90.0, 0.0]),
            ("C_hipsOffset_CTRL", [90.0, 90.0, 0.0]),
            ("C_hipsPivot_CTRL", [0.0, 0.0, 0.0]),
            ("C_spine01_CTRL", [90.0, 90.0, 0.0]),
            ("C_spine02_CTRL", [90.0, 90.0, 0.0]),
            ("C_spine03_CTRL", [90.0, 90.0, 0.0]),
            ("C_spine_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_spineOffset_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_spinePivot_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_spineMid_IK_CTRL", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_controls:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_spine_control_pose_b(self):
        a_spine_module = tools_mod_spine.ModuleSpine(world_ctrls=True)
        # Setup Project
        cmds.file(new=True, force=True)
        a_spine_module.chest_proxy.set_initial_position(xyz=[5, 6, 33])
        a_spine_module.hip_proxy.set_initial_position(xyz=[4, 23, 1])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_spine_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_controls = [
            ("C_cog_CTRL", [4.0, 23.0, 1.0]),
            ("C_spine_CTRL", [4.0, 23.0, 1.0]),
            ("C_hips_CTRL", [4.0, 23.0, 1.0]),
            ("C_hipsOffset_CTRL", [4.0, 23.0, 1.0]),
            ("C_hipsPivot_CTRL", [4.0, 23.0, 1.0]),
            ("C_spine01_CTRL", [4.33, 17.33, 11.67]),
            ("C_spine02_CTRL", [4.67, 11.67, 22.33]),
            ("C_spine03_CTRL", [5.0, 6.0, 33.0]),
            ("C_spine_IK_CTRL", [5.0, 6.0, 33.0]),
            ("C_spineOffset_IK_CTRL", [5.0, 6.0, 33.0]),
            ("C_spinePivot_IK_CTRL", [5.0, 6.0, 33.0]),
            ("C_spineMid_IK_CTRL", [4.5, 14.5, 17.0]),
        ]

        for joint_name, expected in world_positions_controls:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_controls = [
            ("C_cog_CTRL", [0.0, 0.0, 0.0]),
            ("C_spine_CTRL", [0.0, 0.0, 0.0]),
            ("C_hips_CTRL", [90.0, 90.0, 0.0]),
            ("C_hipsOffset_CTRL", [90.0, 90.0, 0.0]),
            ("C_hipsPivot_CTRL", [0.0, 0.0, 0.0]),
            ("C_spine01_CTRL", [90.0, 90.0, 0.0]),
            ("C_spine02_CTRL", [90.0, 90.0, 0.0]),
            ("C_spine03_CTRL", [90.0, 90.0, 0.0]),
            ("C_spine_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_spineOffset_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_spinePivot_IK_CTRL", [0.0, 0.0, 0.0]),
            ("C_spineMid_IK_CTRL", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_controls:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)
