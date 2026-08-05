import unittest
import logging
import sys
import os

import gt.tools.auto_rigger.modules.module_biped_finger as module_finger
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


class TestModuleBipedFinger(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)

    def test_module_biped_finger_inheritance(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        result = isinstance(finger_module_instance, tools_rig_frm.ModuleGeneric)
        expected = True
        self.assertEqual(expected, result)

    def test_module_finger_inheritance_passthrough(self):
        finger_module_instance = module_finger.ModuleBipedFingers(
            name="mocked_finger", prefix="mocked_prefix", suffix="mocked_suffix"
        )
        result = finger_module_instance.name
        expected = "mocked_finger"
        self.assertEqual(expected, result)
        result = finger_module_instance.prefix
        expected = "mocked_prefix"
        self.assertEqual(expected, result)
        result = finger_module_instance.suffix
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_finger_basic_proxy_compliance(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        # Proxies Type
        result = type(finger_module_instance.proxies)
        expected = list
        self.assertEqual(expected, result, '"proxies" variable must be a list.')
        # Number of proxies
        result = len(finger_module_instance.proxies)
        expected = 24
        self.assertEqual(expected, result)
        # Proxy type (Proxies should only carry tools_rig_frm.Proxy objects)
        for proxy in finger_module_instance.proxies:
            message = f'An element in the proxies list is not a proxy instance. Issue object: "{str(proxy)}"'
            self.assertIsInstance(proxy, tools_rig_frm.Proxy, message)
        # Variable Names (Must end with "_proxy")
        proxy_vars = {
            key: value for key, value in vars(finger_module_instance).items() if isinstance(value, tools_rig_frm.Proxy)
        }
        for proxy_var_key in proxy_vars.keys():
            message = f'A proxy variables was not named correctly. Incorrect variable: "{str(proxy_var_key)}"'
            self.assertTrue(proxy_var_key.endswith("_proxy"), message)

    def test_module_finger_default_proxy_prefix(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        finger_prefix = finger_module_instance.get_prefix()
        expected = None
        self.assertEqual(expected, finger_prefix)

    def test_module_finger_default_proxy_suffix(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        finger_suffix = finger_module_instance.get_suffix()
        expected = None
        self.assertEqual(expected, finger_suffix)

    def test_module_finger_check_default_orientation(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        an_orientation_data = finger_module_instance.get_orientation_data()
        result = an_orientation_data.get_method()
        expected = "automatic"
        self.assertEqual(expected, result)

    def test_module_finger_proxy_names(self):
        finger_names = [
            "indexMeta",
            "middleMeta",
            "ringMeta",
            "pinkyMeta",
            "thumb01",
            "thumb02",
            "thumb03",
            "thumbEnd",
            "index01",
            "index02",
            "index03",
            "indexEnd",
            "middle01",
            "middle02",
            "middle03",
            "middleEnd",
            "ring01",
            "ring02",
            "ring03",
            "ringEnd",
            "pinky01",
            "pinky02",
            "pinky03",
            "pinkyEnd",
        ]
        finger_module_instance = module_finger.ModuleBipedFingers()
        for proxy in finger_module_instance.proxies:
            result = proxy.get_name()
            self.assertEqual(finger_names[finger_module_instance.proxies.index(proxy)], result)

    def test_module_finger_meta_purpose_names(self):
        finger_names = [
            "indexMeta",
            "middleMeta",
            "ringMeta",
            "pinkyMeta",
            "thumb01",
            "thumb02",
            "thumb03",
            "thumbEnd",
            "index01",
            "index02",
            "index03",
            "indexEnd",
            "middle01",
            "middle02",
            "middle03",
            "middleEnd",
            "ring01",
            "ring02",
            "ring03",
            "ringEnd",
            "pinky01",
            "pinky02",
            "pinky03",
            "pinkyEnd",
        ]

        temp = []
        finger_module_instance = module_finger.ModuleBipedFingers()
        for proxy in finger_module_instance.proxies:
            result = proxy.get_meta_purpose()
            temp.append(result)
            self.assertEqual(finger_names[finger_module_instance.proxies.index(proxy)], result)

    def test_module_finger_meta_proxy_driver_types(self):
        finger_module_instance = module_finger.ModuleBipedFingers(extra=True)
        expected = [tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        result = finger_module_instance.meta_index_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.meta_middle_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.meta_ring_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.meta_pinky_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.meta_extra_proxy.get_driver_types()
        self.assertEqual(expected, result)

    def test_module_finger_thumb_proxy_driver_types(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        expected = [tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        result = finger_module_instance.thumb01_proxy.get_driver_types()
        self.assertEqual(expected, result)
        expected = [tools_rig_const.RiggerDriverTypes.FK]
        result = finger_module_instance.thumb02_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.thumb03_proxy.get_driver_types()
        self.assertEqual(expected, result)

    def test_module_finger_index_proxy_driver_types(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        expected = [tools_rig_const.RiggerDriverTypes.FK]
        result = finger_module_instance.index01_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.index02_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.index03_proxy.get_driver_types()
        self.assertEqual(expected, result)

    def test_module_finger_middle_proxy_driver_types(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        expected = [tools_rig_const.RiggerDriverTypes.FK]
        result = finger_module_instance.middle01_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.middle02_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.middle03_proxy.get_driver_types()
        self.assertEqual(expected, result)

    def test_module_finger_ring_proxy_driver_types(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        expected = [tools_rig_const.RiggerDriverTypes.FK]
        result = finger_module_instance.ring01_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.ring02_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.ring03_proxy.get_driver_types()
        self.assertEqual(expected, result)

    def test_module_finger_pinky_proxy_driver_types(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        expected = [tools_rig_const.RiggerDriverTypes.FK]
        result = finger_module_instance.pinky01_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.pinky02_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.pinky03_proxy.get_driver_types()
        self.assertEqual(expected, result)

    def test_module_finger_extra_proxy_driver_types(self):
        finger_module_instance = module_finger.ModuleBipedFingers(extra=True)
        expected = [tools_rig_const.RiggerDriverTypes.FK]
        result = finger_module_instance.extra01_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.extra02_proxy.get_driver_types()
        self.assertEqual(expected, result)
        result = finger_module_instance.extra03_proxy.get_driver_types()
        self.assertEqual(expected, result)

    def test_module_finger_get_module_as_dict(self):
        # Default Module
        finger_module_instance = module_finger.ModuleBipedFingers(extra=True)
        a_finger_as_dict = finger_module_instance.get_module_as_dict()
        self.assertIsInstance(a_finger_as_dict, dict)
        expected_keys = sorted(
            [
                "active",
                "expanded",
                "extra",
                "extra_name",
                "index",
                "index_name",
                "meta",
                "meta_name",
                "middle",
                "middle_name",
                "module",
                "name",
                "orientation",
                "pinky",
                "pinky_name",
                "proxies",
                "ring",
                "ring_name",
                "setup_name",
                "thumb",
                "thumb_name",
                "uuid",
            ]
        )
        result_keys = sorted(list(a_finger_as_dict.keys()))
        self.assertEqual(expected_keys, result_keys)
        expected_module_value = "ModuleBipedFingers"
        result_module_value = a_finger_as_dict.get("module")
        self.assertEqual(expected_module_value, result_module_value)
        # Change Module and Test Module Level Serialization
        finger_module_instance.set_parent_uuid("550e8400-e29b-41d4-a716-446655440000")
        a_finger_as_dict = finger_module_instance.get_module_as_dict()
        self.assertIn("parent", a_finger_as_dict)
        # Transfer data to a new module
        a_2nd_finger_module = module_finger.ModuleBipedFingers(extra=True)
        a_2nd_finger_module.read_data_from_dict(a_finger_as_dict)
        expected = finger_module_instance.get_module_as_dict()
        result = a_2nd_finger_module.get_module_as_dict()
        self.assertEqual(expected, result)

    def test_module_finger_read_proxies_from_dict(self):
        finger_module_instance = module_finger.ModuleBipedFingers(meta=True)
        finger_module_instance.meta_index_proxy.set_parent_uuid(
            "550e8400-e29b-41d4-a716-446655440000"
        )  # Changed the proxy
        a_finger_as_dict = finger_module_instance.get_module_as_dict()
        # Create a second module (new)
        a_2nd_finger_module = module_finger.ModuleBipedFingers()
        a_2nd_finger_module.read_proxies_from_dict(a_finger_as_dict.get("proxies"))
        expected = finger_module_instance.meta_index_proxy.get_uuid()
        result = a_2nd_finger_module.meta_index_proxy.get_uuid()
        self.assertEqual(expected, result)

    def test_module_leg_build_proxy(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        proxy_data_list = finger_module_instance.build_proxy()
        # Check ProxyData objects
        for proxy_data in proxy_data_list:
            self.assertIsInstance(proxy_data, tools_rig_frm.ProxyData)
            self.assertTrue(cmds.objExists(proxy_data.get_long_name()))
        # Check Maya Scene
        expected_nodes = [
            "indexMeta_offset",
            "indexMeta",
            "index01_offset",
            "index01",
            "index02_offset",
            "index02",
            "index03_offset",
            "index03",
            "indexEnd_offset",
            "indexEnd",
            "middleMeta_offset",
            "middleMeta",
            "middle01_offset",
            "middle01",
            "middle02_offset",
            "middle02",
            "middle03_offset",
            "middle03",
            "middleEnd_offset",
            "middleEnd",
            "ringMeta_offset",
            "ringMeta",
            "ring01_offset",
            "ring01",
            "ring02_offset",
            "ring02",
            "ring03_offset",
            "ring03",
            "ringEnd_offset",
            "ringEnd",
            "pinkyMeta_offset",
            "pinkyMeta",
            "pinky01_offset",
            "pinky01",
            "pinky02_offset",
            "pinky02",
            "pinky03_offset",
            "pinky03",
            "pinkyEnd_offset",
            "pinkyEnd",
            "thumb01_offset",
            "thumb01",
            "thumb02_offset",
            "thumb02",
            "thumb03_offset",
            "thumb03",
            "thumbEnd_offset",
            "thumbEnd",
        ]

        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("indexMeta.proxyUUID"))
        self.assertTrue(cmds.objExists("middleMeta.proxyUUID"))
        self.assertTrue(cmds.objExists("ringMeta.proxyUUID"))
        self.assertTrue(cmds.objExists("pinkyMeta.proxyUUID"))
        self.assertTrue(cmds.objExists("index01.proxyUUID"))
        self.assertTrue(cmds.objExists("index02.proxyUUID"))
        self.assertTrue(cmds.objExists("index03.proxyUUID"))
        self.assertTrue(cmds.objExists("indexEnd.proxyUUID"))
        self.assertTrue(cmds.objExists("middle01.proxyUUID"))
        self.assertTrue(cmds.objExists("middle02.proxyUUID"))
        self.assertTrue(cmds.objExists("middle03.proxyUUID"))
        self.assertTrue(cmds.objExists("middleEnd.proxyUUID"))
        self.assertTrue(cmds.objExists("ring01.proxyUUID"))
        self.assertTrue(cmds.objExists("ring02.proxyUUID"))
        self.assertTrue(cmds.objExists("ring03.proxyUUID"))
        self.assertTrue(cmds.objExists("ring03.proxyUUID"))
        self.assertTrue(cmds.objExists("ringEnd.proxyUUID"))
        self.assertTrue(cmds.objExists("pinky01.proxyUUID"))
        self.assertTrue(cmds.objExists("pinky02.proxyUUID"))
        self.assertTrue(cmds.objExists("pinky03.proxyUUID"))
        self.assertTrue(cmds.objExists("pinkyEnd.proxyUUID"))
        self.assertTrue(cmds.objExists("thumb01.proxyUUID"))
        self.assertTrue(cmds.objExists("thumb02.proxyUUID"))
        self.assertTrue(cmds.objExists("thumb03.proxyUUID"))
        self.assertTrue(cmds.objExists("thumbEnd.proxyUUID"))

    def test_module_leg_build_proxy_within_project(self):
        finger_module_instance = module_finger.ModuleBipedFingers()
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(finger_module_instance)
        a_project.build_proxy()
        expected_nodes = [
            "indexMeta_offset",
            "indexMeta",
            "index01_offset",
            "index01",
            "index02_offset",
            "index02",
            "index03_offset",
            "index03",
            "indexEnd_offset",
            "indexEnd",
            "middleMeta_offset",
            "middleMeta",
            "middle01_offset",
            "middle01",
            "middle02_offset",
            "middle02",
            "middle03_offset",
            "middle03",
            "middleEnd_offset",
            "middleEnd",
            "ringMeta_offset",
            "ringMeta",
            "ring01_offset",
            "ring01",
            "ring02_offset",
            "ring02",
            "ring03_offset",
            "ring03",
            "ringEnd_offset",
            "ringEnd",
            "pinkyMeta_offset",
            "pinkyMeta",
            "pinky01_offset",
            "pinky01",
            "pinky02_offset",
            "pinky02",
            "pinky03_offset",
            "pinky03",
            "pinkyEnd_offset",
            "pinkyEnd",
            "thumb01_offset",
            "thumb01",
            "thumb02_offset",
            "thumb02",
            "thumb03_offset",
            "thumb03",
            "thumbEnd_offset",
            "thumbEnd",
        ]

        for node in expected_nodes:
            self.assertTrue(cmds.objExists(node))
        self.assertTrue(cmds.objExists("indexMeta.proxyUUID"))
        self.assertTrue(cmds.objExists("middleMeta.proxyUUID"))
        self.assertTrue(cmds.objExists("ringMeta.proxyUUID"))
        self.assertTrue(cmds.objExists("pinkyMeta.proxyUUID"))
        self.assertTrue(cmds.objExists("index01.proxyUUID"))
        self.assertTrue(cmds.objExists("index02.proxyUUID"))
        self.assertTrue(cmds.objExists("index03.proxyUUID"))
        self.assertTrue(cmds.objExists("indexEnd.proxyUUID"))
        self.assertTrue(cmds.objExists("middle01.proxyUUID"))
        self.assertTrue(cmds.objExists("middle02.proxyUUID"))
        self.assertTrue(cmds.objExists("middle03.proxyUUID"))
        self.assertTrue(cmds.objExists("middleEnd.proxyUUID"))
        self.assertTrue(cmds.objExists("ring01.proxyUUID"))
        self.assertTrue(cmds.objExists("ring02.proxyUUID"))
        self.assertTrue(cmds.objExists("ring03.proxyUUID"))
        self.assertTrue(cmds.objExists("ring03.proxyUUID"))
        self.assertTrue(cmds.objExists("ringEnd.proxyUUID"))
        self.assertTrue(cmds.objExists("pinky01.proxyUUID"))
        self.assertTrue(cmds.objExists("pinky02.proxyUUID"))
        self.assertTrue(cmds.objExists("pinky03.proxyUUID"))
        self.assertTrue(cmds.objExists("pinkyEnd.proxyUUID"))
        self.assertTrue(cmds.objExists("thumb01.proxyUUID"))
        self.assertTrue(cmds.objExists("thumb02.proxyUUID"))
        self.assertTrue(cmds.objExists("thumb03.proxyUUID"))
        self.assertTrue(cmds.objExists("thumbEnd.proxyUUID"))

    def test_module_finger_prefixes(self):
        a_lf_finger_module = module_finger.ModuleBipedFingersLeft()
        a_proxy = a_lf_finger_module.get_prefix()
        expected = "L"
        self.assertEqual(expected, a_proxy)
        a_rt_finger_module = module_finger.ModuleBipedFingersRight()
        a_proxy = a_rt_finger_module.get_prefix()
        expected = "R"
        self.assertEqual(expected, a_proxy)

    def test_module_finger_build_rig(self):
        finger_module_instance = module_finger.ModuleBipedFingers(prefix="C")
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(finger_module_instance)
        a_project.build_proxy()
        a_project.build_rig()
        expected_elements = [
            "C_indexMeta_JNT",
            "C_index01_JNT",
            "C_index02_JNT",
            "C_index03_JNT",
            "C_index03_JNT_parentConstraint1",
            "C_index02_JNT_parentConstraint1",
            "C_index01_JNT_parentConstraint1",
            "C_indexMeta_JNT_parentConstraint1",
            "C_middleMeta_JNT",
            "C_middle01_JNT",
            "C_middle02_JNT",
            "C_middle03_JNT",
            "C_middle03_JNT_parentConstraint1",
            "C_middle02_JNT_parentConstraint1",
            "C_middle01_JNT_parentConstraint1",
            "C_middleMeta_JNT_parentConstraint1",
            "C_ringMeta_JNT",
            "C_ring01_JNT",
            "C_ring02_JNT",
            "C_ring03_JNT",
            "C_ring03_JNT_parentConstraint1",
            "C_ring02_JNT_parentConstraint1",
            "C_ring01_JNT_parentConstraint1",
            "C_ringMeta_JNT_parentConstraint1",
            "C_pinkyMeta_JNT",
            "C_pinky01_JNT",
            "C_pinky02_JNT",
            "C_pinky03_JNT",
            "C_pinky03_JNT_parentConstraint1",
            "C_pinky02_JNT_parentConstraint1",
            "C_pinky01_JNT_parentConstraint1",
            "C_pinkyMeta_JNT_parentConstraint1",
            "C_thumb01_JNT",
            "C_thumb02_JNT",
            "C_thumb03_JNT",
            "C_thumb03_JNT_parentConstraint1",
            "C_thumb02_JNT_parentConstraint1",
            "C_thumb01_JNT_parentConstraint1",
            "C_fingers_driven",
            "C_fingers_offset",
            "C_fingers_CTRL",
            "C_indexMeta_offset",
            "C_indexMeta_driver",
            "C_indexMeta_CTRL",
            "C_index01_offset",
            "C_index01_dataCurl|",
            "C_index01_driver",
            "C_index01_CTRL",
            "C_index02_offset",
            "C_index02_dataCurl|",
            "C_index02_driver",
            "C_index02_CTRL",
            "C_index03_offset",
            "C_index03_dataCurl|",
            "C_index03_driver",
            "C_index03_CTRL",
            "C_middleMeta_offset",
            "C_middleMeta_driver",
            "C_middleMeta_CTRL",
            "C_middle01_offset",
            "C_middle01_dataCurl|",
            "C_middle01_driver",
            "C_middle01_CTRL",
            "C_middle02_offset",
            "C_middle02_dataCurl|",
            "C_middle02_driver",
            "C_middle02_CTRL",
            "C_middle03_offset",
            "C_middle03_dataCurl|",
            "C_middle03_driver",
            "C_middle03_CTRL",
            "C_ringMeta_offset",
            "C_ringMeta_driver",
            "C_ringMeta_CTRL",
            "C_ring01_offset",
            "C_ring01_dataCurl|",
            "C_ring01_driver",
            "C_ring01_CTRL",
            "C_ring02_offset",
            "C_ring02_dataCurl|",
            "C_ring02_driver",
            "C_ring02_CTRL",
            "C_ring03_offset",
            "C_ring03_dataCurl|",
            "C_ring03_driver",
            "C_ring03_CTRL",
            "C_pinkyMeta_offset",
            "C_pinkyMeta_driver",
            "C_pinkyMeta_CTRL",
            "C_pinky01_offset",
            "C_pinky01_dataCurl|",
            "C_pinky01_driver",
            "C_pinky01_CTRL",
            "C_pinky02_offset",
            "C_pinky02_dataCurl|",
            "C_pinky02_driver",
            "C_pinky02_CTRL",
            "C_pinky03_offset",
            "C_pinky03_dataCurl|",
            "C_pinky03_driver",
            "C_pinky03_CTRL",
            "C_thumb01_offset",
            "C_thumb01_dataCurl|",
            "C_thumb01_driver",
            "C_thumb01_CTRL",
            "C_thumb02_offset",
            "C_thumb02_dataCurl|",
            "C_thumb02_driver",
            "C_thumb02_CTRL",
            "C_thumb03_offset",
            "C_thumb03_dataCurl|",
            "C_thumb03_driver",
            "C_thumb03_CTRL",
        ]
        for obj in expected_elements:
            self.assertTrue(cmds.objExists(obj))

    def test_module_finger_find_drivers_from_module(self):
        a_finger_module = module_finger.ModuleBipedFingers(prefix="C")
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_finger_module)
        a_project.build_proxy()
        a_project.build_rig()  # Required for drivers to be created

        expected = [
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_fingers_offset|C_fingers_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_indexMeta_offset|C_indexMeta_driver"
            "|C_indexMeta_CTRL|C_index01_offset|C_index01_dataCurl|C_index01_driver|C_index01_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_indexMeta_offset|C_indexMeta_driver"
            "|C_indexMeta_CTRL|C_index01_offset|C_index01_dataCurl|C_index01_driver|C_index01_CTRL|C_index02_offset"
            "|C_index02_dataCurl|C_index02_driver|C_index02_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_indexMeta_offset|C_indexMeta_driver"
            "|C_indexMeta_CTRL|C_index01_offset|C_index01_dataCurl|C_index01_driver|C_index01_CTRL|C_index02_offset"
            "|C_index02_dataCurl|C_index02_driver|C_index02_CTRL|C_index03_offset|C_index03_dataCurl|C_index03_driver"
            "|C_index03_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_indexMeta_offset|C_indexMeta_driver"
            "|C_indexMeta_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_middleMeta_offset|C_middleMeta_driver"
            "|C_middleMeta_CTRL|C_middle01_offset|C_middle01_dataCurl|C_middle01_driver|C_middle01_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_middleMeta_offset|C_middleMeta_driver"
            "|C_middleMeta_CTRL|C_middle01_offset|C_middle01_dataCurl|C_middle01_driver|C_middle01_CTRL"
            "|C_middle02_offset|C_middle02_dataCurl|C_middle02_driver|C_middle02_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_middleMeta_offset|C_middleMeta_driver"
            "|C_middleMeta_CTRL|C_middle01_offset|C_middle01_dataCurl|C_middle01_driver|C_middle01_CTRL"
            "|C_middle02_offset|C_middle02_dataCurl|C_middle02_driver|C_middle02_CTRL|C_middle03_offset"
            "|C_middle03_dataCurl|C_middle03_driver|C_middle03_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_middleMeta_offset|C_middleMeta_driver"
            "|C_middleMeta_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_pinkyMeta_offset|C_pinkyMeta_driver"
            "|C_pinkyMeta_CTRL|C_pinky01_offset|C_pinky01_dataCurl|C_pinky01_driver|C_pinky01_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_pinkyMeta_offset|C_pinkyMeta_driver"
            "|C_pinkyMeta_CTRL|C_pinky01_offset|C_pinky01_dataCurl|C_pinky01_driver|C_pinky01_CTRL|C_pinky02_offset"
            "|C_pinky02_dataCurl|C_pinky02_driver|C_pinky02_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_pinkyMeta_offset|C_pinkyMeta_driver"
            "|C_pinkyMeta_CTRL|C_pinky01_offset|C_pinky01_dataCurl|C_pinky01_driver|C_pinky01_CTRL|C_pinky02_offset"
            "|C_pinky02_dataCurl|C_pinky02_driver|C_pinky02_CTRL|C_pinky03_offset|C_pinky03_dataCurl|C_pinky03_driver"
            "|C_pinky03_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_pinkyMeta_offset|C_pinkyMeta_driver"
            "|C_pinkyMeta_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_ringMeta_offset|C_ringMeta_driver"
            "|C_ringMeta_CTRL|C_ring01_offset|C_ring01_dataCurl|C_ring01_driver|C_ring01_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_ringMeta_offset|C_ringMeta_driver"
            "|C_ringMeta_CTRL|C_ring01_offset|C_ring01_dataCurl|C_ring01_driver|C_ring01_CTRL|C_ring02_offset"
            "|C_ring02_dataCurl|C_ring02_driver|C_ring02_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_ringMeta_offset|C_ringMeta_driver"
            "|C_ringMeta_CTRL|C_ring01_offset|C_ring01_dataCurl|C_ring01_driver|C_ring01_CTRL|C_ring02_offset"
            "|C_ring02_dataCurl|C_ring02_driver|C_ring02_CTRL|C_ring03_offset|C_ring03_dataCurl|C_ring03_driver"
            "|C_ring03_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_ringMeta_offset|C_ringMeta_driver"
            "|C_ringMeta_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_thumb01_offset|C_thumb01_dataCurl"
            "|C_thumb01_driver|C_thumb01_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_thumb01_offset|C_thumb01_dataCurl"
            "|C_thumb01_driver|C_thumb01_CTRL|C_thumb02_offset|C_thumb02_dataCurl|C_thumb02_driver|C_thumb02_CTRL",
            "|rig|controls|C_global_CTRL|C_globalOffset_CTRL|C_fingers_driven|C_thumb01_offset|C_thumb01_dataCurl"
            "|C_thumb01_driver|C_thumb01_CTRL|C_thumb02_offset|C_thumb02_dataCurl|C_thumb02_driver|C_thumb02_CTRL"
            "|C_thumb03_offset|C_thumb03_dataCurl|C_thumb03_driver|C_thumb03_CTRL",
        ]

        result = tools_rig_utils.find_drivers_from_module(
            source_uuid=a_finger_module.get_uuid(), filter_driver_type=None  # No filter means all types
        )
        self.assertEqual(expected, result)

    def test_module_finger_proxy_pose_default(self):
        a_finger_module = module_finger.ModuleBipedFingers()
        # Setup Project
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_finger_module)
        a_project.build_proxy()

        world_positions_proxy = [
            ("indexMeta_offset", [-2.0, 125.0, 0.0]),
            ("indexMeta", [-2.0, 125.0, 0.0]),
            ("index01", [-2.0, 130.0, 0.0]),
            ("index02", [-2.0, 130.0, 3.0]),
            ("index03", [-2.0, 130.0, 6.0]),
            ("indexEnd", [-2.0, 130.0, 9.0]),
            ("middleMeta", [0.0, 125.0, 0.0]),
            ("middle01", [0.0, 130.0, 0.0]),
            ("middle02", [0.0, 130.0, 3.0]),
            ("middle03", [0.0, 130.0, 6.0]),
            ("middleEnd", [0.0, 130.0, 9.0]),
            ("thumb01", [-4.0, 130.0, 0.0]),
            ("thumb02", [-4.0, 130.0, 3.0]),
            ("thumb03", [-4.0, 130.0, 6.0]),
            ("thumbEnd", [-4.0, 130.0, 9.0]),
            ("ringMeta", [-2.0, 125.0, 0.0]),
            ("ring01", [2.0, 130.0, 0.0]),
            ("ring02", [2.0, 130.0, 3.0]),
            ("ring03", [2.0, 130.0, 6.0]),
            ("ringEnd", [2.0, 130.0, 9.0]),
            ("pinkyMeta", [-4.0, 125.0, 0.0]),
            ("pinky01", [4.0, 130.0, 0.0]),
            ("pinky02", [4.0, 130.0, 3.0]),
            ("pinky03", [4.0, 130.0, 6.0]),
            ("pinkyEnd", [4.0, 130.0, 9.0]),
        ]

        for joint_name, expected in world_positions_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("indexMeta_offset", [0.0, 0.0, 0.0]),
            ("indexMeta", [0.0, 0.0, 0.0]),
            ("index01", [0.0, 0.0, 0.0]),
            ("index02", [0.0, 0.0, 0.0]),
            ("index03", [0.0, 0.0, 0.0]),
            ("indexEnd", [0.0, 0.0, 0.0]),
            ("middleMeta", [0.0, 0.0, 0.0]),
            ("middle01", [0.0, 0.0, 0.0]),
            ("middle02", [0.0, 0.0, 0.0]),
            ("middle03", [0.0, 0.0, 0.0]),
            ("middleEnd", [0.0, 0.0, 0.0]),
            ("thumb01", [0.0, 0.0, 0.0]),
            ("thumb02", [0.0, 0.0, 0.0]),
            ("thumb03", [0.0, 0.0, 0.0]),
            ("thumbEnd", [0.0, 0.0, 0.0]),
            ("ringMeta", [0.0, 0.0, 0.0]),
            ("ring01", [0.0, 0.0, 0.0]),
            ("ring02", [0.0, 0.0, 0.0]),
            ("ring03", [0.0, 0.0, 0.0]),
            ("ringEnd", [0.0, 0.0, 0.0]),
            ("pinkyMeta", [0.0, 0.0, 0.0]),
            ("pinky01", [0.0, 0.0, 0.0]),
            ("pinky02", [0.0, 0.0, 0.0]),
            ("pinky03", [0.0, 0.0, 0.0]),
            ("pinkyEnd", [0.0, 0.0, 0.0]),
        ]
        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_finger_proxy_pose_a(self):
        a_finger_module = module_finger.ModuleBipedFingers()
        # Setup Project
        a_finger_module.meta_index_proxy.set_initial_position(xyz=[1, 2, 3])
        a_finger_module.meta_ring_proxy.set_initial_position(xyz=[1, 2, 3])
        a_finger_module.meta_middle_proxy.set_initial_position(xyz=[1, 2, 3])
        a_finger_module.meta_pinky_proxy.set_initial_position(xyz=[1, 2, 3])
        a_finger_module.index01_proxy.set_initial_position(xyz=[1, 2, 3])
        a_finger_module.index02_proxy.set_initial_position(xyz=[4, 5, 6])
        a_finger_module.index03_proxy.set_initial_position(xyz=[7, 8, 9])
        a_finger_module.middle01_proxy.set_initial_position(xyz=[1, 2, 3])
        a_finger_module.middle02_proxy.set_initial_position(xyz=[4, 5, 6])
        a_finger_module.middle03_proxy.set_initial_position(xyz=[7, 8, 9])
        a_finger_module.ring01_proxy.set_initial_position(xyz=[1, 2, 3])
        a_finger_module.ring02_proxy.set_initial_position(xyz=[4, 5, 6])
        a_finger_module.ring03_proxy.set_initial_position(xyz=[7, 8, 9])
        a_finger_module.pinky01_proxy.set_initial_position(xyz=[1, 2, 3])
        a_finger_module.pinky02_proxy.set_initial_position(xyz=[4, 5, 6])
        a_finger_module.pinky03_proxy.set_initial_position(xyz=[7, 8, 9])
        a_finger_module.thumb01_proxy.set_initial_position(xyz=[1, 2, 3])
        a_finger_module.thumb02_proxy.set_initial_position(xyz=[4, 5, 6])
        a_finger_module.thumb03_proxy.set_initial_position(xyz=[7, 8, 9])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_finger_module)
        a_project.build_proxy()

        world_positions_proxy = [
            ("indexMeta_offset", [1.0, 2.0, 3.0]),
            ("indexMeta", [1.0, 2.0, 3.0]),
            ("index01", [1.0, 2.0, 3.0]),
            ("index02", [4.0, 5.0, 6.0]),
            ("index03", [7.0, 8.0, 9.0]),
            ("indexEnd", [-2.0, 130.0, 9.0]),
            ("middleMeta", [1.0, 2.0, 3.0]),
            ("middle01", [1.0, 2.0, 3.0]),
            ("middle02", [4.0, 5.0, 6.0]),
            ("middle03", [7.0, 8.0, 9.0]),
            ("middleEnd", [0.0, 130.0, 9.0]),
            ("thumb01", [1.0, 2.0, 3.0]),
            ("thumb02", [4.0, 5.0, 6.0]),
            ("thumb03", [7.0, 8.0, 9.0]),
            ("thumbEnd", [-4.0, 130.0, 9.0]),
            ("ringMeta", [1.0, 2.0, 3.0]),
            ("ring01", [1.0, 2.0, 3.0]),
            ("ring02", [4.0, 5.0, 6.0]),
            ("ring03", [7.0, 8.0, 9.0]),
            ("ringEnd", [2.0, 130.0, 9.0]),
            ("pinkyMeta", [1.0, 2.0, 3.0]),
            ("pinky01", [1.0, 2.0, 3.0]),
            ("pinky02", [4.0, 5.0, 6.0]),
            ("pinky03", [7.0, 8.0, 9.0]),
            ("pinkyEnd", [4.0, 130.0, 9.0]),
        ]

        for joint_name, expected in world_positions_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("indexMeta_offset", [0.0, 0.0, 0.0]),
            ("indexMeta", [0.0, 0.0, 0.0]),
            ("index01", [0.0, 0.0, 0.0]),
            ("index02", [0.0, 0.0, 0.0]),
            ("index03", [0.0, 0.0, 0.0]),
            ("indexEnd", [0.0, 0.0, 0.0]),
            ("middleMeta", [0.0, 0.0, 0.0]),
            ("middle01", [0.0, 0.0, 0.0]),
            ("middle02", [0.0, 0.0, 0.0]),
            ("middle03", [0.0, 0.0, 0.0]),
            ("middleEnd", [0.0, 0.0, 0.0]),
            ("thumb01", [0.0, 0.0, 0.0]),
            ("thumb02", [0.0, 0.0, 0.0]),
            ("thumb03", [0.0, 0.0, 0.0]),
            ("thumbEnd", [0.0, 0.0, 0.0]),
            ("ringMeta", [0.0, 0.0, 0.0]),
            ("ring01", [0.0, 0.0, 0.0]),
            ("ring02", [0.0, 0.0, 0.0]),
            ("ring03", [0.0, 0.0, 0.0]),
            ("ringEnd", [0.0, 0.0, 0.0]),
            ("pinkyMeta", [0.0, 0.0, 0.0]),
            ("pinky01", [0.0, 0.0, 0.0]),
            ("pinky02", [0.0, 0.0, 0.0]),
            ("pinky03", [0.0, 0.0, 0.0]),
            ("pinkyEnd", [0.0, 0.0, 0.0]),
        ]
        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    def test_module_finger_proxy_pose_b(self):
        a_finger_module = module_finger.ModuleBipedFingers()
        # Setup Project
        a_finger_module.meta_index_proxy.set_initial_position(xyz=[4, 5, 6])
        a_finger_module.meta_ring_proxy.set_initial_position(xyz=[5, 6, 6])
        a_finger_module.meta_middle_proxy.set_initial_position(xyz=[5, 3, 1])
        a_finger_module.meta_pinky_proxy.set_initial_position(xyz=[7, 7, 7])
        a_finger_module.index01_proxy.set_initial_position(xyz=[3, 2, 1])
        a_finger_module.index02_proxy.set_initial_position(xyz=[4, 3, 3])
        a_finger_module.index03_proxy.set_initial_position(xyz=[23, 8, 4])
        a_finger_module.middle01_proxy.set_initial_position(xyz=[1, 2, 1])
        a_finger_module.middle02_proxy.set_initial_position(xyz=[3, 3, 3])
        a_finger_module.middle03_proxy.set_initial_position(xyz=[5, 5, 1])
        a_finger_module.ring01_proxy.set_initial_position(xyz=[23, 44, 5])
        a_finger_module.ring02_proxy.set_initial_position(xyz=[5, 6, 7])
        a_finger_module.ring03_proxy.set_initial_position(xyz=[8, 9, 8])
        a_finger_module.pinky01_proxy.set_initial_position(xyz=[7, 8, 5])
        a_finger_module.pinky02_proxy.set_initial_position(xyz=[5, 8, 5])
        a_finger_module.pinky03_proxy.set_initial_position(xyz=[8, 6, 6])
        a_finger_module.thumb01_proxy.set_initial_position(xyz=[2, 2, 1])
        a_finger_module.thumb02_proxy.set_initial_position(xyz=[5, 3, 2])
        a_finger_module.thumb03_proxy.set_initial_position(xyz=[4, 1, 6])
        a_project = tools_rig_frm.RigProject()
        a_project.add_to_modules(a_finger_module)
        a_project.build_proxy()

        world_positions_proxy = [
            ("indexMeta_offset", [4.0, 5.0, 6.0]),
            ("indexMeta", [4.0, 5.0, 6.0]),
            ("index01", [3.0, 2.0, 1.0]),
            ("index02", [4.0, 3.0, 3.0]),
            ("index03", [23.0, 8.0, 4.0]),
            ("indexEnd", [-2.0, 130.0, 9.0]),
            ("middleMeta", [5.0, 3.0, 1.0]),
            ("middle01", [1.0, 2.0, 1.0]),
            ("middle02", [3.0, 3.0, 3.0]),
            ("middle03", [5.0, 5.0, 1.0]),
            ("middleEnd", [0.0, 130.0, 9.0]),
            ("thumb01", [2.0, 2.0, 1.0]),
            ("thumb02", [5.0, 3.0, 2.0]),
            ("thumb03", [4.0, 1.0, 6.0]),
            ("thumbEnd", [-4.0, 130.0, 9.0]),
            ("ringMeta", [5.0, 6.0, 6.0]),
            ("ring01", [23.0, 44.0, 5.0]),
            ("ring02", [5.0, 6.0, 7.0]),
            ("ring03", [8.0, 9.0, 8.0]),
            ("ringEnd", [2.0, 130.0, 9.0]),
            ("pinkyMeta", [7.0, 7.0, 7.0]),
            ("pinky01", [7.0, 8.0, 5.0]),
            ("pinky02", [5.0, 8.0, 5.0]),
            ("pinky03", [8.0, 6.0, 6.0]),
            ("pinkyEnd", [4.0, 130.0, 9.0]),
        ]

        for joint_name, expected in world_positions_proxy:
            precision = 2
            result_translation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, translation=True)
            rounded_translation = [round(coord, precision) for coord in result_translation]
            self.assertAlmostEqual(expected, rounded_translation)

        world_rotation_proxy = [
            ("indexMeta_offset", [0.0, 0.0, 0.0]),
            ("indexMeta", [0.0, 0.0, 0.0]),
            ("index01", [0.0, 0.0, 0.0]),
            ("index02", [0.0, 0.0, 0.0]),
            ("index03", [0.0, 0.0, 0.0]),
            ("indexEnd", [0.0, 0.0, 0.0]),
            ("middleMeta", [0.0, 0.0, 0.0]),
            ("middle01", [0.0, 0.0, 0.0]),
            ("middle02", [0.0, 0.0, 0.0]),
            ("middle03", [0.0, 0.0, 0.0]),
            ("middleEnd", [0.0, 0.0, 0.0]),
            ("thumb01", [0.0, 0.0, 0.0]),
            ("thumb02", [0.0, 0.0, 0.0]),
            ("thumb03", [0.0, 0.0, 0.0]),
            ("thumbEnd", [0.0, 0.0, 0.0]),
            ("ringMeta", [0.0, 0.0, 0.0]),
            ("ring01", [0.0, 0.0, 0.0]),
            ("ring02", [0.0, 0.0, 0.0]),
            ("ring03", [0.0, 0.0, 0.0]),
            ("ringEnd", [0.0, 0.0, 0.0]),
            ("pinkyMeta", [0.0, 0.0, 0.0]),
            ("pinky01", [0.0, 0.0, 0.0]),
            ("pinky02", [0.0, 0.0, 0.0]),
            ("pinky03", [0.0, 0.0, 0.0]),
            ("pinkyEnd", [0.0, 0.0, 0.0]),
        ]
        for joint_name, expected in world_rotation_proxy:
            precision = 2
            result_rotation = cmds.xform(f"{joint_name}", query=True, worldSpace=True, rotation=True)
            rounded_rotation = [round(coord, precision) for coord in result_rotation]
            self.assertAlmostEqual(expected, rounded_rotation)

    # TODO check joints and controls - a_project.build_rig isn't working for me for some reasons
