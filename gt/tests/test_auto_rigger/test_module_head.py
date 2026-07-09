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
import gt.tools.auto_rigger.modules.module_head as tools_mod_head
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
from gt.tests import maya_test_tools

cmds = maya_test_tools.cmds


class TestModuleHead(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_module_head_inheritance(self):
        a_head_module = tools_mod_head.ModuleHead()
        result = isinstance(a_head_module, tools_rig_frm.ModuleGeneric)
        expected = True
        self.assertEqual(expected, result)

    def test_module_head_inheritance_passthrough(self):
        a_head_module = tools_mod_head.ModuleHead(name="mocked_name", prefix="mocked_prefix", suffix="mocked_suffix")
        result = a_head_module.name
        expected = "mocked_name"
        self.assertEqual(expected, result)
        result = a_head_module.prefix
        expected = "mocked_prefix"
        self.assertEqual(expected, result)
        result = a_head_module.suffix
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_head_basic_proxy_compliance(self):
        a_head_module = tools_mod_head.ModuleHead()
        # Proxies Type
        result = type(a_head_module.proxies)
        expected = list
        self.assertEqual(expected, result, '"proxies" variable must be a list.')
        # Number of proxies
        result = len(a_head_module.proxies)
        expected = 8
        self.assertEqual(expected, result)
        # Proxy type (Proxies should only carry tools_rig_frm.Proxy objects)
        for proxy in a_head_module.proxies:
            message = f'An element in the proxies list is not a proxy instance. Issue object: "{str(proxy)}"'
            self.assertIsInstance(proxy, tools_rig_frm.Proxy, message)
        # Variable Names (Must end with "_proxy")
        proxy_vars = {
            key: value for key, value in vars(a_head_module).items() if isinstance(value, tools_rig_frm.Proxy)
        }
        for proxy_var_key in proxy_vars.keys():
            message = f'A proxy variables was not named correctly. Incorrect variable: "{str(proxy_var_key)}"'
            self.assertTrue(proxy_var_key.endswith("_proxy"), message)

    def test_module_head_get_module_as_dict(self):
        a_head_module = tools_mod_head.ModuleHead()
        a_head_as_dict = a_head_module.get_module_as_dict()
        self.assertIsInstance(a_head_as_dict, dict)

        expected_keys = sorted(
            [
                "active",
                "expanded",
                "build_eyes",
                "build_jaw",
                "code",
                "delete_head_jaw_bind_jnt",
                "module",
                "name",
                "neck_number",
                "orientation",
                "prefix",
                "prefix_eye_left",
                "prefix_eye_right",
                "proxies",
                "uuid",
            ]
        )
        result_keys = sorted(list(a_head_as_dict.keys()))
        self.assertEqual(expected_keys, result_keys)

        expected_module_value = "ModuleHead"
        result_module_value = a_head_as_dict.get("module")
        self.assertEqual(expected_module_value, result_module_value)

        # Change Module and Test Module Level Serialization
        a_head_module.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")
        a_head_as_dict = a_head_module.get_module_as_dict()
        self.assertIn("parent", a_head_as_dict)

        # Transfer data to a new head module
        a_2nd_head_module = tools_mod_head.ModuleHead()
        a_2nd_head_module.read_data_from_dict(a_head_as_dict)
        expected = a_head_module.get_module_as_dict()
        result = a_2nd_head_module.get_module_as_dict()
        self.assertEqual(expected, result)

    def test_module_head_read_proxies_from_dict(self):
        a_head_module = tools_mod_head.ModuleHead()
        a_head_module.neck_base_proxy.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")  # Changed the proxy
        a_head_as_dict = a_head_module.get_module_as_dict()
        # Create a second new module
        a_2nd_head_module = tools_mod_head.ModuleHead()
        a_2nd_head_module.read_proxies_from_dict(a_head_as_dict.get("proxies"))
        expected = a_head_module.neck_base_proxy.get_uuid()
        result = a_2nd_head_module.neck_base_proxy.get_uuid()
        self.assertEqual(expected, result)

    def test_module_head_build_proxy(self):
        a_head_module = tools_mod_head.ModuleHead()
        proxy_data_list = a_head_module.build_proxy()

        # Check ProxyData objects
        for proxy_data in proxy_data_list:
            self.assertIsInstance(proxy_data, tools_rig_frm.ProxyData)
            self.assertTrue(cmds.objExists(proxy_data.get_long_name()))

        # Check Maya Scene
        expected_nodes = [
            "C_jawEnd",
            "C_jawEnd_offset",
            "C_jaw",
            "C_jaw_offset",
            "R_eye",
            "R_eye_offset",
            "L_eye",
            "L_eye_offset",
            "C_headEnd",
            "C_headEnd_offset",
            "C_head",
            "C_head_offset",
            "C_neck02",
            "C_neck02_offset",
            "C_neck01",
            "C_neck01_offset",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node), f'Missing expected node: "{node}""')
            if not node.endswith("_offset"):
                self.assertTrue(cmds.objExists(f"{node}.proxyUUID"))

    def test_module_head_build_proxy_within_project(self):
        a_head_module = tools_mod_head.ModuleHead()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_head_module)
        a_project.build_proxy()

        expected_nodes = [
            "C_jawEnd",
            "C_jawEnd_offset",
            "C_jaw",
            "C_jaw_offset",
            "R_eye",
            "R_eye_offset",
            "L_eye",
            "L_eye_offset",
            "C_headEnd",
            "C_headEnd_offset",
            "C_head",
            "C_head_offset",
            "C_neck02",
            "C_neck02_offset",
            "C_neck01",
            "C_neck01_offset",
        ]
        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node), f'Missing expected node: "{node}""')
            if not node.endswith("_offset"):
                self.assertTrue(cmds.objExists(f"{node}.proxyUUID"))

    def test_module_head_serialization(self):
        # Create Initial Test Setup
        a_generic_module = tools_rig_frm.ModuleGeneric()
        a_head_module = tools_mod_head.ModuleHead()  # Default initial location (origin)
        a_2nd_head_module = tools_mod_head.ModuleHead()
        a_2nd_head_module.neck_base_proxy.set_name("secondNeck")
        a_2nd_head_module.neck_base_proxy.set_initial_position(x=10)  # Starts a little bit to the side
        a_2nd_head_module.set_prefix("ABC")
        a_proxy = a_generic_module.add_new_proxy()
        a_proxy_uuid = a_proxy.get_uuid()  # Store UUID for later
        a_proxy.set_initial_position(x=5)  # Starts a little bit to the side
        a_proxy.set_parent_uuid_from_proxy(a_head_module.neck_base_proxy)  # Generic Proxy is the child of the neck
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_head_module)
        a_project.add_to_modules(a_generic_module)
        a_project.add_to_modules(a_2nd_head_module)
        # Build Proxy, Modify it, Read changes
        a_project.build_proxy()
        cmds.xform("C_neck01", t=(0, 15, 0), ws=True)
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
        result_ty = cmds.xform("C_neck01", t=True, q=True, ws=True)[1]
        self.assertEqual(expected_ty, result_ty)
        expected_tx = 10
        result_tx = cmds.getAttr("ABC_secondNeck.tx")
        self.assertEqual(expected_tx, result_tx)
        expected_tx = 5
        result_tx = cmds.getAttr("proxy.tx")
        self.assertEqual(expected_tx, result_tx)
        # Test Build Rig with Ingested Data
        a_2nd_project.build_rig()
        expected_ty = 15
        result_ty = cmds.getAttr("C_neck01_JNT.ty")
        self.assertEqual(expected_ty, result_ty)
        expected_tx = 10
        result_tx = cmds.getAttr("ABC_secondNeck_JNT.tx")
        self.assertEqual(expected_tx, result_tx)
        expected_tx = 5
        result_tx = cmds.xform("proxy_JNT", t=True, q=True, ws=True)[0]
        self.assertEqual(expected_tx, result_tx)
        expected_proxy_uuid = a_proxy_uuid
        result_tx = cmds.getAttr(f"proxy_JNT.{tools_rig_const.RiggerConstants.ATTR_JOINT_UUID}")
        self.assertEqual(expected_proxy_uuid, result_tx)

    def test_module_head_find_drivers_from_module(self):
        # Create multiple modules to test separation
        a_1st_head_module = tools_mod_head.ModuleHead()
        a_2nd_head_module = tools_mod_head.ModuleHead()
        # Set prefix name
        a_2nd_head_module.set_prefix("SCN")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_1st_head_module)
        a_project.add_to_modules(a_2nd_head_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        expected = sorted(
            [
                "R_eye_CTRL",
                "L_eye_CTRL",
                "C_mainEye_CTRL",
                "C_jaw_CTRL",
                "C_headOffset_CTRL",
                "C_head_CTRL",
                "C_neck02_CTRL",
                "C_neck01_CTRL",
            ]
        )
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_head_module.get_uuid(), filter_driver_type=None  # No filter means all types
        )
        result = sorted([node.get_short_name() for node in result])
        self.assertEqual(expected, result)

        # Check what you get when filtering by type with FK.
        expected = sorted(
            [
                "C_jaw_CTRL",
                "C_head_CTRL",
                "C_neck02_CTRL",
                "C_neck01_CTRL",
            ]
        )
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_head_module.get_uuid(), filter_driver_type=tools_rig_const.RiggerDriverTypes.FK
        )
        result = sorted([node.get_short_name() for node in result])
        self.assertEqual(expected, result)

        # Check what you get when filtering by type with AIM.
        expected = sorted(["C_mainEye_CTRL", "L_eye_CTRL", "R_eye_CTRL"])
        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_1st_head_module.get_uuid(), filter_driver_type=tools_rig_const.RiggerDriverTypes.AIM
        )
        result = sorted([node.get_short_name() for node in result])
        self.assertEqual(expected, result)

    def test_module_head_proxy_pose_default(self):
        an_head_module = tools_mod_head.ModuleHead()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_head_module)
        a_project.build_proxy()

        world_positions_proxy = [
            ("C_neck01", [0.0, 137.0, 0.0]),
            ("C_neck02", [0.0, 139.75, 0.0]),
            ("C_head", [0.0, 142.5, 0.0]),
            ("C_headEnd", [0.0, 160.0, 0.0]),
            ("C_jaw", [0.0, 147.5, 2.5]),
            ("C_jawEnd", [0.0, 142.5, 11.0]),
            ("L_eye", [3.5, 151.0, 8.7]),
            ("R_eye", [-3.5, 151.0, 8.7]),
        ]

        for joint_name, expected in world_positions_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("C_neck01", [0.0, 0.0, 0.0]),
            ("C_neck02", [0.0, 0.0, 0.0]),
            ("C_head", [0.0, 0.0, 0.0]),
            ("C_headEnd", [0.0, 0.0, 0.0]),
            ("C_jaw", [0.0, 0.0, 0.0]),
            ("C_jawEnd", [0.0, 0.0, 0.0]),
            ("L_eye", [0.0, 0.0, 0.0]),
            ("R_eye", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_head_proxy_pose_a(self):
        an_head_module = tools_mod_head.ModuleHead()
        # Setup Project
        an_head_module.neck_base_proxy.set_initial_position(xyz=[30, 10, 60])
        an_head_module.head_end_proxy.set_initial_position(xyz=[20, 5, 60])
        an_head_module.head_proxy.set_initial_position(xyz=[50, 50, 10])
        an_head_module.head_end_proxy.set_initial_position(xyz=[33, 35, 90])
        an_head_module.jaw_proxy.set_initial_position(xyz=[34, 51, 5])
        an_head_module.jaw_end_proxy.set_initial_position(xyz=[37, 57, 91])
        an_head_module.lt_eye_proxy.set_initial_position(xyz=[67, 45, 3])
        an_head_module.rt_eye_proxy.set_initial_position(xyz=[35, 2, 1])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_head_module)
        a_project.build_proxy()

        world_positions_proxy = [
            ("C_neck01", [30.0, 10.0, 60.0]),
            ("C_neck02", [40.0, 30.0, 35.0]),
            ("C_head", [50.0, 50.0, 10.0]),
            ("C_headEnd", [33.0, 35.0, 90.0]),
            ("C_jaw", [34.0, 51.0, 5.0]),
            ("C_jawEnd", [37.0, 57.0, 91.0]),
            ("L_eye", [67.0, 45.0, 3.0]),
            ("R_eye", [35.0, 2.0, 1.0]),
        ]

        for joint_name, expected in world_positions_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("C_neck01", [0.0, 0.0, 0.0]),
            ("C_neck02", [0.0, 0.0, 0.0]),
            ("C_head", [0.0, 0.0, 0.0]),
            ("C_headEnd", [0.0, 0.0, 0.0]),
            ("C_jaw", [0.0, 0.0, 0.0]),
            ("C_jawEnd", [0.0, 0.0, 0.0]),
            ("L_eye", [0.0, 0.0, 0.0]),
            ("R_eye", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_head_proxy_pose_b(self):
        an_head_module = tools_mod_head.ModuleHead()
        # Setup Project
        cmds.file(new=True, force=True)
        an_head_module.neck_base_proxy.set_initial_position(xyz=[1, 2, 4])
        an_head_module.head_end_proxy.set_initial_position(xyz=[4, 2, 2])
        an_head_module.head_proxy.set_initial_position(xyz=[67, 2, 10])
        an_head_module.head_end_proxy.set_initial_position(xyz=[2, 1, 6])
        an_head_module.jaw_proxy.set_initial_position(xyz=[4, 1, 1])
        an_head_module.jaw_end_proxy.set_initial_position(xyz=[2, 7, 8])
        an_head_module.lt_eye_proxy.set_initial_position(xyz=[8, 8, 5])
        an_head_module.rt_eye_proxy.set_initial_position(xyz=[5, 4, 2])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_head_module)
        a_project.build_proxy()

        world_positions_proxy = [
            ("C_neck01", [1.0, 2.0, 4.0]),
            ("C_neck02", [34.0, 2.0, 7.0]),
            ("C_head", [67.0, 2.0, 10.0]),
            ("C_headEnd", [2.0, 1.0, 6.0]),
            ("C_jaw", [4.0, 1.0, 1.0]),
            ("C_jawEnd", [2.0, 7.0, 8.0]),
            ("L_eye", [8.0, 8.0, 5.0]),
            ("R_eye", [5.0, 4.0, 2.0]),
        ]

        for joint_name, expected in world_positions_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("C_neck01", [0.0, 0.0, 0.0]),
            ("C_neck02", [0.0, 0.0, 0.0]),
            ("C_head", [0.0, 0.0, 0.0]),
            ("C_headEnd", [0.0, 0.0, 0.0]),
            ("C_jaw", [0.0, 0.0, 0.0]),
            ("C_jawEnd", [0.0, 0.0, 0.0]),
            ("L_eye", [0.0, 0.0, 0.0]),
            ("R_eye", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_head_joint_pose_default(self):
        an_head_module = tools_mod_head.ModuleHead()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_head_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_joints = [
            ("C_neck01_JNT", [0.0, 137.0, 0.0]),
            ("C_neck02_JNT", [0.0, 139.75, 0.0]),
            ("C_head_JNT", [0.0, 142.5, 0.0]),
            ("L_eye_JNT", [3.5, 151.0, 8.7]),
            ("R_eye_JNT", [-3.5, 151.0, 8.7]),
            ("C_jaw_JNT", [0.0, 147.5, 2.5]),
        ]

        for joint_name, expected in world_positions_joints:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_joints = [
            ("C_neck01_JNT", [90.0, 90.0, 0.0]),
            ("C_neck02_JNT", [90.0, 90.0, 0.0]),
            ("C_head_JNT", [90.0, 90.0, 0.0]),
            ("L_eye_JNT", [90.0, 90.0, 0.0]),
            ("R_eye_JNT", [90.0, 90.0, 0.0]),
            ("C_jaw_JNT", [90.0, 90.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_joints:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_head_joint_pose_a(self):
        an_head_module = tools_mod_head.ModuleHead()
        # Setup Project
        an_head_module.neck_base_proxy.set_initial_position(xyz=[30, 10, 60])
        an_head_module.head_end_proxy.set_initial_position(xyz=[20, 5, 60])
        an_head_module.head_proxy.set_initial_position(xyz=[50, 50, 10])
        an_head_module.head_end_proxy.set_initial_position(xyz=[33, 35, 90])
        an_head_module.jaw_proxy.set_initial_position(xyz=[34, 51, 5])
        an_head_module.jaw_end_proxy.set_initial_position(xyz=[37, 57, 91])
        an_head_module.lt_eye_proxy.set_initial_position(xyz=[67, 45, 3])
        an_head_module.rt_eye_proxy.set_initial_position(xyz=[35, 2, 1])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_head_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_joints = [
            ("C_neck01_JNT", [30.0, 10.0, 60.0]),
            ("C_neck02_JNT", [40.0, 30.0, 35.0]),
            ("C_head_JNT", [50.0, 50, 10]),
            ("L_eye_JNT", [67.0, 45, 3]),
            ("R_eye_JNT", [35.0, 2, 1]),
            ("C_jaw_JNT", [34, 51, 5]),
        ]

        for joint_name, expected in world_positions_joints:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_joints = [
            ("C_neck01_JNT", [90.0, 90.0, 0.0]),
            ("C_neck02_JNT", [90.0, 90.0, 0.0]),
            ("C_head_JNT", [90.0, 90.0, 0.0]),
            ("L_eye_JNT", [90.0, 90.0, 0.0]),
            ("R_eye_JNT", [90.0, 90.0, 0.0]),
            ("C_jaw_JNT", [90.0, 90.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_joints:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_head_joint_pose_b(self):
        an_head_module = tools_mod_head.ModuleHead()
        # Setup Project
        an_head_module.neck_base_proxy.set_initial_position(xyz=[1, 2, 4])
        an_head_module.head_end_proxy.set_initial_position(xyz=[4, 2, 2])
        an_head_module.head_proxy.set_initial_position(xyz=[67, 2, 10])
        an_head_module.head_end_proxy.set_initial_position(xyz=[2, 1, 6])
        an_head_module.jaw_proxy.set_initial_position(xyz=[4, 1, 1])
        an_head_module.jaw_end_proxy.set_initial_position(xyz=[2, 7, 8])
        an_head_module.lt_eye_proxy.set_initial_position(xyz=[8, 8, 5])
        an_head_module.rt_eye_proxy.set_initial_position(xyz=[5, 4, 2])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_head_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_joints = [
            ("C_neck01_JNT", [1.0, 2.0, 4.0]),
            ("C_neck02_JNT", [34.0, 2.0, 7.0]),
            ("C_head_JNT", [67.0, 2.0, 10.0]),
            ("L_eye_JNT", [8.0, 8.0, 5.0]),
            ("R_eye_JNT", [5.0, 4.0, 2.0]),
            ("C_jaw_JNT", [4.0, 1.0, 1.0]),
        ]

        for joint_name, expected in world_positions_joints:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_joints = [
            ("C_neck01_JNT", [90.0, 90.0, 0.0]),
            ("C_neck02_JNT", [90.0, 90.0, 0.0]),
            ("C_head_JNT", [90.0, 90.0, 0.0]),
            ("L_eye_JNT", [90.0, 90.0, 0.0]),
            ("R_eye_JNT", [90.0, 90.0, 0.0]),
            ("C_jaw_JNT", [90.0, 90.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_joints:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_head_control_pose_default(self):
        an_head_module = tools_mod_head.ModuleHead()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_head_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_controls = [
            ("C_neck01_CTRL", [0.0, 137.0, 0.0]),
            ("C_neck02_CTRL", [0.0, 139.75, 0.0]),
            ("C_head_CTRL", [0.0, 142.5, 0.0]),
            ("C_jaw_CTRL", [0.0, 147.5, 2.5]),
            ("C_mainEye_CTRL", [0.0, 151.0, 29.7]),
            ("L_eye_CTRL", [3.5, 151.0, 29.7]),
            ("R_eye_CTRL", [-3.5, 151.0, 29.7]),
        ]

        for joint_name, expected in world_positions_controls:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_controls = [
            ("C_neck01_CTRL", [90.0, 90.0, 0.0]),
            ("C_neck02_CTRL", [90.0, 90.0, 0.0]),
            ("C_head_CTRL", [90.0, 90.0, 0.0]),
            ("C_jaw_CTRL", [90.0, 90.0, 0.0]),
            ("C_mainEye_CTRL", [0.0, 0.0, 0.0]),
            ("L_eye_CTRL", [0.0, 0.0, 0.0]),
            ("R_eye_CTRL", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_controls:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_head_control_pose_a(self):
        an_head_module = tools_mod_head.ModuleHead()
        # Setup Project
        an_head_module.neck_base_proxy.set_initial_position(xyz=[30, 10, 60])
        an_head_module.head_end_proxy.set_initial_position(xyz=[20, 5, 60])
        an_head_module.head_proxy.set_initial_position(xyz=[50, 50, 10])
        an_head_module.head_end_proxy.set_initial_position(xyz=[33, 35, 90])
        an_head_module.jaw_proxy.set_initial_position(xyz=[34, 51, 5])
        an_head_module.jaw_end_proxy.set_initial_position(xyz=[37, 57, 91])
        an_head_module.lt_eye_proxy.set_initial_position(xyz=[67, 45, 3])
        an_head_module.rt_eye_proxy.set_initial_position(xyz=[35, 2, 1])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_head_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_controls = [
            ("C_neck01_CTRL", [30.0, 10.0, 60.0]),
            ("C_neck02_CTRL", [40.0, 30.0, 35.0]),
            ("C_head_CTRL", [50.0, 50.0, 10.0]),
            ("C_jaw_CTRL", [34.0, 51.0, 5.0]),
            ("C_mainEye_CTRL", [50.0, 45.0, 163.91]),
            ("L_eye_CTRL", [67.0, 45.0, 163.91]),
            ("R_eye_CTRL", [35.0, 2.0, 161.91]),
        ]

        for joint_name, expected in world_positions_controls:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_controls = [
            ("C_neck01_CTRL", [90.0, 90.0, 0.0]),
            ("C_neck02_CTRL", [90.0, 90.0, 0.0]),
            ("C_head_CTRL", [90.0, 90.0, 0.0]),
            ("C_jaw_CTRL", [90.0, 90.0, 0.0]),
            ("C_mainEye_CTRL", [0.0, 0.0, 0.0]),
            ("L_eye_CTRL", [0.0, 0.0, 0.0]),
            ("R_eye_CTRL", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_controls:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_head_control_pose_b(self):
        an_head_module = tools_mod_head.ModuleHead()
        # Setup Project
        cmds.file(new=True, force=True)
        an_head_module.neck_base_proxy.set_initial_position(xyz=[1, 2, 4])
        an_head_module.head_end_proxy.set_initial_position(xyz=[4, 2, 2])
        an_head_module.head_proxy.set_initial_position(xyz=[67, 2, 10])
        an_head_module.head_end_proxy.set_initial_position(xyz=[2, 1, 6])
        an_head_module.jaw_proxy.set_initial_position(xyz=[4, 1, 1])
        an_head_module.jaw_end_proxy.set_initial_position(xyz=[2, 7, 8])
        an_head_module.lt_eye_proxy.set_initial_position(xyz=[8, 8, 5])
        an_head_module.rt_eye_proxy.set_initial_position(xyz=[5, 4, 2])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(an_head_module)
        a_project.build_proxy()
        a_project.build_rig()

        world_positions_controls = [
            ("C_neck01_CTRL", [1.0, 2.0, 4.0]),
            ("C_neck02_CTRL", [34.0, 2.0, 7.0]),
            ("C_head_CTRL", [67.0, 2.0, 10.0]),
            ("C_jaw_CTRL", [4.0, 1.0, 1.0]),
            ("C_mainEye_CTRL", [67.0, 8.0, 22.49]),
            ("L_eye_CTRL", [8.0, 8.0, 22.49]),
            ("R_eye_CTRL", [5.0, 4.0, 19.49]),
        ]

        for joint_name, expected in world_positions_controls:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_controls = [
            ("C_neck01_CTRL", [90.0, 90.0, 0.0]),
            ("C_neck02_CTRL", [90.0, 90.0, 0.0]),
            ("C_head_CTRL", [90.0, 90.0, 0.0]),
            ("C_jaw_CTRL", [90.0, 90.0, 0.0]),
            ("C_mainEye_CTRL", [0.0, 0.0, 0.0]),
            ("L_eye_CTRL", [0.0, 0.0, 0.0]),
            ("R_eye_CTRL", [0.0, 0.0, 0.0]),
        ]

        for joint_name, expected in world_rotation_controls:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)
