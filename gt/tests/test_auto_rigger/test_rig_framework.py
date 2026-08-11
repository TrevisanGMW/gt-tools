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
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.core.transform as core_trans
import gt.core.naming as core_naming
from gt.tests import maya_test_tools
import gt.core.curve as core_curve
import gt.core.color as core_color
import gt.core.uuid as core_uuid

cmds = maya_test_tools.cmds


class TestRigFramework(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        # Useful Variables
        self.a_valid_uuid = "123e4567-e89b-12d3-a456-426655440000"
        # Helper Classes
        self.proxy_data = tools_rig_frm.ProxyData(
            name="mocked_name",
            offset="mocked_offset",
            setup=("mocked_setup1", "mocked_setup2", "mocked_setup3"),
            uuid=self.a_valid_uuid,
        )
        self.code_data = tools_rig_frm.CodeData()
        self.orient = tools_rig_frm.OrientationData()
        # Main Classes
        self.proxy = tools_rig_frm.Proxy()
        self.module = tools_rig_frm.ModuleGeneric()
        self.project = tools_rig_frm.RigProject()
        # Configure Instances
        self.proxy.uuid = self.a_valid_uuid

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    # ----------------------------------------------- ProxyData -----------------------------------------------
    def test_proxy_data_repr(self):
        expected = "mocked_name"
        result = repr(self.proxy_data)
        self.assertEqual(expected, result)
        result = str(self.proxy_data)
        self.assertEqual(expected, result)

    def test_proxy_data_get_short_name(self):
        expected = "mocked_name"
        result = self.proxy_data.get_short_name()
        self.assertEqual(expected, result)

    def test_proxy_data_get_long_name(self):
        expected = "mocked_name"
        result = self.proxy_data.get_long_name()
        self.assertEqual(expected, result)

    def test_proxy_data_get_offset(self):
        expected = "mocked_offset"
        result = self.proxy_data.get_offset()
        self.assertEqual(expected, result)

    def test_proxy_data_get_setup(self):
        expected = ("mocked_setup1", "mocked_setup2", "mocked_setup3")
        result = self.proxy_data.get_setup()
        self.assertEqual(expected, result)

    def test_proxy_data_get_proxy_data_uuid(self):
        result = self.proxy_data.get_uuid()
        expected = self.a_valid_uuid
        self.assertEqual(expected, result)

    # ------------------------------------------- OrientationData -------------------------------------------
    def test_orient_set_data_from_dict(self):
        mocked_dict = {
            "method": "inherit",
            "aim_axis": (1, 0, 0),
            "up_axis": (0, 1, 0),
            "up_dir": (0, 0, 1),
            "world_aligned": True,
        }
        self.orient.set_data_from_dict(mocked_dict)
        result_method = self.orient.get_method()
        expected = "inherit"
        self.assertEqual(expected, result_method)

        result_aim_axis = self.orient.get_aim_axis()
        expected = (1, 0, 0)
        self.assertEqual(expected, result_aim_axis)

        result_up_axis = self.orient.get_up_axis()
        expected = (0, 1, 0)
        self.assertEqual(expected, result_up_axis)

        result_up_dir = self.orient.get_up_dir()
        expected = (0, 0, 1)
        self.assertEqual(expected, result_up_dir)

        result_world_aligned = self.orient.get_world_aligned()
        expected = True
        self.assertEqual(expected, result_world_aligned)

    def test_orient_set_data_from_dict_no_dict(self):
        self.orient.set_data_from_dict(None)

        result_method = self.orient.get_method()
        expected = "automatic"
        self.assertEqual(expected, result_method)

        result_aim_axis = self.orient.get_aim_axis()
        expected = (1, 0, 0)
        self.assertEqual(expected, result_aim_axis)

        result_up_axis = self.orient.get_up_axis()
        expected = (0, 1, 0)
        self.assertEqual(expected, result_up_axis)

        result_up_dir = self.orient.get_up_dir()
        expected = (0, 1, 0)
        self.assertEqual(expected, result_up_dir)

        result_world_aligned = self.orient.get_world_aligned()
        expected = False
        self.assertEqual(expected, result_world_aligned)

    def test_orient_string_conversion_returns(self):
        mocked_dict = {
            "method": "inherit",
            "aim_axis": (1, 0, 0),
            "up_axis": (0, 1, 0),
            "up_dir": (0, 0, 1),
            "world_aligned": True,
        }
        self.orient.set_data_from_dict(mocked_dict)
        expected = "Method: inherit (aim_axis=(1, 0, 0), up_axis=(0, 1, 0), up_dir=(0, 0, 1)), world_aligned=True)"
        self.assertEqual(expected, self.orient.__repr__())
        self.assertEqual(expected, str(self.orient))

    # ---------------------------------------------- CodeData ----------------------------------------------
    def test_code_data_data_from_dict(self):
        mocked_dict = {"order": "post_build", "code": "code_mocked"}
        self.code_data.set_data_from_dict(mocked_dict)
        result_order = self.code_data.get_order()
        expected_order = "post_build"
        self.assertEqual(expected_order, result_order)
        result_code = self.code_data.get_execution_code()
        expected_code = "code_mocked"
        self.assertEqual(expected_code, result_code)

    def test_code_data_get_order(self):
        self.code_data.set_order("post_build")
        result = self.code_data.get_order()
        expected = "post_build"
        self.assertEqual(expected, result)
        self.code_data.set_order("post_skeleton")
        result = self.code_data.get_order()
        expected = "post_skeleton"
        self.assertEqual(expected, result)

    def test_code_data_get_order_default(self):
        result = self.code_data.get_order()
        expected = "pre_proxy"
        self.assertEqual(expected, result)

    def test_code_data_get_data_as_dict(self):
        mocked_dict = {"order": "post_build", "code": "code_mocked"}
        self.code_data.set_data_from_dict(mocked_dict)
        result = self.code_data.get_data_as_dict()
        self.assertEqual(mocked_dict, result)

    def test_code_data_get_data_as_dict_default(self):
        result = self.code_data.get_data_as_dict()
        expected = {"order": "pre_proxy", "code": ""}
        self.assertEqual(expected, result)

    # ------------------------------------------------- Proxy -------------------------------------------------
    def test_proxy_default_values(self):
        result = self.proxy.build()
        self.assertTrue(self.proxy.is_valid())
        expected = "|proxy_offset|proxy"
        self.assertEqual(expected, str(result))
        expected = "proxy"
        self.assertEqual(expected, result.get_short_name())
        self.assertTrue(isinstance(result, tools_rig_frm.ProxyData))
        expected = "|proxy_offset"
        self.assertEqual(expected, result.offset)
        expected = ("proxy_LocScaleHandle",)
        self.assertEqual(expected, result.setup)

    def test_proxy_init_and_basic_setters(self):
        expected_name = "mocked_name"
        expected_uuid = "123e4567-e89b-12d3-a456-426655440000"
        proxy = tools_rig_frm.Proxy(name=expected_name, uuid=expected_uuid)
        self.assertEqual(expected_name, proxy.name)
        self.assertEqual(expected_uuid, proxy.uuid)

        expected_name = "mocked_name_two"
        proxy.set_name("mocked_name_two")
        self.assertEqual(expected_name, proxy.name)

        mocked_transform = core_trans.Transform(position=(0, 10, 0))
        proxy.set_transform(mocked_transform)
        self.assertEqual(mocked_transform, proxy.transform)

        proxy.set_offset_transform(mocked_transform)
        self.assertEqual(mocked_transform, proxy.offset_transform)

        expected_curve = core_curve.get_curve("circle")
        proxy.set_curve(expected_curve)
        self.assertEqual(expected_curve, proxy.curve)

        proxy.set_uuid(expected_uuid)
        self.assertEqual(expected_uuid, proxy.uuid)

        expected_parent_uuid = "30a72080-8f1b-474d-be19-65b81da497f4"
        proxy.set_parent_uuid(expected_parent_uuid)
        self.assertEqual(expected_parent_uuid, proxy.parent_uuid)

        expected_metadata = {"metadata": "value"}
        proxy.set_metadata_dict(expected_metadata)
        self.assertEqual(expected_metadata, proxy.metadata)
        self.assertTrue(proxy.is_valid())

    def test_proxy_build(self):
        result = self.proxy.build()
        expected_long_name = "|proxy_offset|proxy"
        self.assertEqual(expected_long_name, str(result))
        expected_short_name = "proxy"
        self.assertEqual(expected_short_name, result.get_short_name())
        self.assertTrue(isinstance(result, tools_rig_frm.ProxyData))
        self.assertTrue(cmds.objExists(f"{result}.{tools_rig_const.RiggerConstants.ATTR_PROXY_UUID}"))

    def test_proxy_custom_curve(self):
        proxy = tools_rig_frm.Proxy()
        proxy.set_curve(core_curve.Curves.circle)
        result = proxy.build()
        self.assertTrue(proxy.is_valid())
        expected = "proxy"
        self.assertEqual(expected, result.get_short_name())

    def test_proxy_get_name_default(self):
        result = self.proxy.get_name()
        expected = "proxy"
        self.assertEqual(expected, result)

    def test_proxy_get_uuid_default(self):
        expected_uuid = "123e4567-e89b-12d3-a456-426655440000"
        proxy = tools_rig_frm.Proxy(uuid=expected_uuid)
        result = proxy.get_uuid()
        self.assertEqual(expected_uuid, result)

    def test_proxy_get_parent_uuid_default(self):
        expected_parent_uuid = "123e4567-e89b-12d3-a456-426655440002"
        proxy = tools_rig_frm.Proxy()
        proxy.set_parent_uuid(expected_parent_uuid)
        result = proxy.get_parent_uuid()
        self.assertEqual(expected_parent_uuid, result)

    def test_proxy_get_locator_scale(self):
        self.proxy.set_locator_scale(5)
        result = self.proxy.get_locator_scale()
        expected = 5
        self.assertEqual(expected, result)
        self.proxy.set_locator_scale(15)
        result = self.proxy.get_locator_scale()
        expected = 15
        self.assertEqual(expected, result)
        self.proxy.set_locator_scale(1.5)
        result = self.proxy.get_locator_scale()
        expected = 1.5
        self.assertEqual(expected, result)

    def test_proxy_get_attr_dict(self):
        self.proxy.set_attr_dict({"mocked_item": "mocked_value"})
        result = self.proxy.get_attr_dict()
        expected = {"mocked_item": "mocked_value"}
        self.assertEqual(expected, result)

    def test_proxy_is_valid(self):
        result = self.proxy.is_valid()
        self.assertTrue(result)

    def test_proxy_set_transform(self):
        transform = core_trans.Transform(position=(0, 10, 0))
        self.proxy.set_transform(transform=transform)
        result = self.proxy.transform
        self.assertEqual(transform, result)

    def test_proxy_build_apply_offset_transform(self):
        self.proxy.build(apply_transforms=True)
        self.proxy.set_offset_transform(core_trans.Transform(position=(0, 10, 0)))
        self.proxy.apply_offset_transform()
        result = cmds.getAttr("proxy_offset.translate")
        expected = [(0.0, 10.0, 0.0)]
        self.assertEqual(expected, result)

    def test_proxy_build_apply_transforms_no_offset(self):
        self.proxy.set_transform(core_trans.Transform(position=(80, 10, 70)))
        self.proxy.apply_transforms(apply_offset=True)
        self.proxy.build(apply_transforms=True)
        extracted_from_ = cmds.getAttr("proxy_offset.translate")
        result_proxy = cmds.getAttr("proxy.translate")
        expected_offset = [(0.0, 0.0, 0.0)]
        expected_proxy = [(80.0, 10.0, 70.0)]
        self.assertEqual(extracted_from_, expected_offset)
        self.assertEqual(result_proxy, expected_proxy)
        self.assertEqual(extracted_from_, expected_offset)
        self.assertEqual(result_proxy, expected_proxy)

    def test_proxy_build_apply_transforms_offset(self):
        self.proxy.set_transform(core_trans.Transform(position=(80, 10, 70)))
        self.proxy.set_offset_transform(core_trans.Transform(position=(90, 10, 1)))
        self.proxy.apply_transforms(apply_offset=True)
        self.proxy.build(apply_transforms=True)
        result_offset = cmds.getAttr("proxy_offset.translate")
        result_proxy = cmds.getAttr("proxy.translate")
        expected_offset = [(90.0, 10.0, 1.0)]
        expected_proxy = [(-10.0, 0.0, 69.0)]
        self.assertEqual(result_offset, expected_offset)
        self.assertEqual(result_proxy, expected_proxy)

    def test_proxy_get_proxy_as_dict(self):
        self.proxy.set_name(name="mocked_name_two")
        self.proxy.set_parent_uuid(uuid="123e4567-e89b-12d3-a456-426655440000")
        self.proxy.set_attr_dict({"mocked_item": "mocked_value"})
        result = self.proxy.get_proxy_as_dict()
        expected = {
            "name": "mocked_name_two",
            "parent": "123e4567-e89b-12d3-a456-426655440000",
            "attributes": {"mocked_item": "mocked_value"},
        }
        self.assertEqual(expected, result)

    def test_proxy_set_name(self):
        self.proxy.set_name("mocked_proxy_name")
        result = self.proxy.get_name()
        expected = "mocked_proxy_name"
        self.assertEqual(expected, result)
        result = self.proxy.build()
        expected = "mocked_proxy_name"
        self.assertEqual(expected, result.get_short_name())
        expected = "|mocked_proxy_name_offset|mocked_proxy_name"
        self.assertEqual(expected, result.get_long_name())
        # Invalid Names
        logging.disable(logging.WARNING)
        self.proxy.set_name(None)
        self.proxy.set_name(1)
        logging.disable(logging.NOTSET)
        result = self.proxy.get_name()
        expected = "mocked_proxy_name"
        self.assertEqual(expected, result)

    def test_proxy_set_initial_position(self):
        self.proxy.set_initial_position(x=0, y=10, z=90)
        result_proxy = str(self.proxy.transform)
        result_offset = str(self.proxy.offset_transform)
        expected_initial_position = "position=(x=0, y=10, z=90), rotation=(x=0, y=0, z=0), scale=(x=1, y=1, z=1)"
        self.assertEqual(expected_initial_position, result_proxy)
        self.assertEqual(expected_initial_position, result_offset)

    def test_proxy_set_initial_transform(self):
        self.proxy.set_initial_transform(
            transform=core_trans.Transform(position=(12, 34, 5.67), rotation=(89, 1.23, 100000), scale=(0, 0.1, 400))
        )
        result_proxy = str(self.proxy.transform)
        result_offset = str(self.proxy.offset_transform)
        expected_initial_transform = (
            "position=(x=12, y=34, z=5.67), rotation=(x=89, y=1.23, z=100000), scale=(x=0, y=0.1, z=400)"
        )
        # Sets transform and offset transform at the same time (so they should both be the same
        self.assertEqual(expected_initial_transform, result_proxy)
        self.assertEqual(expected_initial_transform, result_offset)

    def test_proxy_set_position(self):
        # Basic
        transform = core_trans.Transform(position=(0, 10, 0))
        self.proxy.set_position(0, 10, 0)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Floats, large and negative values
        transform = core_trans.Transform(position=(-1, 0.1, 100000))
        self.proxy.set_position(-1, 0.1, 100000)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Reset Transform
        self.proxy.transform = core_trans.Transform(position=(0, 0, 0))
        # Only X
        transform = core_trans.Transform(position=(5, 0, 0))
        self.proxy.set_position(x=5)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Only Y
        transform = core_trans.Transform(position=(5, 10, 0))
        self.proxy.set_position(y=10)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Only Z
        transform = core_trans.Transform(position=(5, 10, 15))
        self.proxy.set_position(z=15)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # XYZ
        transform = core_trans.Transform(position=(1, 2, 3))
        self.proxy.set_position(xyz=(1, 2, 3))
        result = self.proxy.transform
        self.assertEqual(transform, result)

    def test_proxy_set_rotation(self):
        # Basic
        transform = core_trans.Transform(rotation=(0, 10, 0))
        self.proxy.set_rotation(0, 10, 0)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Floats, large and negative values
        transform = core_trans.Transform(rotation=(-1, 0.1, 100000))
        self.proxy.set_rotation(-1, 0.1, 100000)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Reset Transform
        self.proxy.transform = core_trans.Transform(rotation=(0, 0, 0))
        # Only X
        transform = core_trans.Transform(rotation=(15, 0, 0))
        self.proxy.set_rotation(x=15)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Only Y
        transform = core_trans.Transform(rotation=(15, 30, 0))
        self.proxy.set_rotation(y=30)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Only Z
        transform = core_trans.Transform(rotation=(15, 30, 45))
        self.proxy.set_rotation(z=45)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # XYZ
        transform = core_trans.Transform(rotation=(1, 2, 3))
        self.proxy.set_rotation(xyz=(1, 2, 3))
        result = self.proxy.transform
        self.assertEqual(transform, result)

    def test_proxy_set_scale(self):
        # Basic
        transform = core_trans.Transform(scale=(0, 10, 0))
        self.proxy.set_scale(0, 10, 0)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Floats, large and negative values
        transform = core_trans.Transform(scale=(-1, 0.1, 100000))
        self.proxy.set_scale(-1, 0.1, 100000)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Reset Transform
        self.proxy.transform = core_trans.Transform(scale=(1, 1, 1))
        # Only X
        transform = core_trans.Transform(scale=(5, 1, 1))
        self.proxy.set_scale(x=5)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Only Y
        transform = core_trans.Transform(scale=(5, 10, 1))
        self.proxy.set_scale(y=10)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # Only Z
        transform = core_trans.Transform(scale=(5, 10, 15))
        self.proxy.set_scale(z=15)
        result = self.proxy.transform
        self.assertEqual(transform, result)
        # XYZ
        transform = core_trans.Transform(scale=(1, 2, 3))
        self.proxy.set_scale(xyz=(1, 2, 3))
        result = self.proxy.transform
        self.assertEqual(transform, result)

    def test_proxy_set_offset_transform(self):
        transform = core_trans.Transform(position=(5, 10, 20), rotation=(15, 30, 45), scale=(1, 2, 3))
        self.proxy.set_offset_transform(transform=transform)
        result = self.proxy.offset_transform
        self.assertEqual(transform, result)

    def test_proxy_set_offset_position(self):
        transform = core_trans.Transform(position=(0, 10, 0))
        self.proxy.set_offset_position(0, 10, 0)
        result = self.proxy.offset_transform
        self.assertEqual(transform, result)

    def test_proxy_set_offset_rotation(self):
        transform = core_trans.Transform(rotation=(0, 10, 0))
        self.proxy.set_offset_rotation(0, 10, 0)
        result = self.proxy.offset_transform
        self.assertEqual(transform, result)

    def test_proxy_set_offset_scale(self):
        transform = core_trans.Transform(scale=(0, 10, 0))
        self.proxy.set_offset_scale(0, 10, 0)
        result = self.proxy.offset_transform
        self.assertEqual(transform, result)

    def test_proxy_set_curve(self):
        curve = core_curve.Curves.circle
        self.proxy.set_curve(curve)
        result = self.proxy.curve
        self.assertEqual(curve, result)

    def test_proxy_set_curve_inherit_name(self):
        curve = core_curve.Curves.circle
        self.proxy.set_curve(curve=curve, inherit_curve_name=True)
        result = self.proxy.curve
        self.assertEqual(curve, result)
        result = self.proxy.get_name()
        expected = self.proxy.curve.get_name()
        self.assertEqual(expected, result)

    def test_proxy_set_locator_scale(self):
        self.proxy.set_locator_scale(2)
        result = self.proxy.attr_dict.get("locatorScale")
        expected = 2
        self.assertEqual(expected, result)
        self.proxy.set_locator_scale(15)
        result = self.proxy.attr_dict.get("locatorScale")
        expected = 15
        self.assertEqual(expected, result)

    def test_proxy_set_attr_dict(self):
        expected = {"attrName": 2}
        self.proxy.set_attr_dict(expected)
        result = self.proxy.attr_dict
        self.assertEqual(expected, result)
        expected = {"attrNameTwo": True, "attrNameThree": 1.23}
        self.proxy.set_attr_dict(expected)
        result = self.proxy.attr_dict
        self.assertEqual(expected, result)

    def test_proxy_metadata_default(self):
        result = self.proxy.metadata
        expected = None
        self.assertEqual(expected, result)
        result = tools_rig_frm.Proxy().metadata
        expected = None
        self.assertEqual(expected, result)

    def test_proxy_set_metadata_dict(self):
        mocked_dict = {"metadata_key": "metadata_value"}
        self.proxy.set_metadata_dict(mocked_dict)
        result = self.proxy.metadata
        self.assertEqual(mocked_dict, result)

    def test_proxy_add_to_metadata(self):
        mocked_dict = {"metadata_key": "metadata_value"}
        self.proxy.set_metadata_dict(mocked_dict)
        self.proxy.add_to_metadata(key="new_key", value="new_value")
        result = self.proxy.metadata
        expected = {"metadata_key": "metadata_value", "new_key": "new_value"}
        self.assertEqual(expected, result)

    def test_proxy_add_driver_type(self):
        self.proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.IK])
        result_existing_drivers = self.proxy.metadata.get(tools_rig_const.RiggerConstants.META_PROXY_DRIVERS)
        expected_drivers = [
            tools_rig_const.RiggerDriverTypes.GENERIC,
            tools_rig_const.RiggerDriverTypes.FK,
            tools_rig_const.RiggerDriverTypes.IK,
        ]
        self.assertEqual(result_existing_drivers, expected_drivers)

    def test_proxy_clean_driver_type(self):
        self.proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.proxy.clear_driver_types()
        result_non_existing_drivers = self.proxy.get_driver_types()
        expected_drivers = None
        self.assertEqual(result_non_existing_drivers, expected_drivers)

    def test_proxy_set_uuid_invalid(self):
        original_uuid = self.proxy.uuid
        logging.disable(logging.WARNING)
        self.proxy.set_uuid("invalid_uuid")
        logging.disable(logging.NOTSET)
        result = self.proxy.uuid
        self.assertEqual(original_uuid, result)

    def test_proxy_set_uuid_valid(self):
        valid_uuid = "4c0c8e52-b7bc-48fb-8e07-e98f7236568a"
        self.proxy.set_uuid(valid_uuid)
        result = self.proxy.uuid
        self.assertEqual(valid_uuid, result)

    def test_proxy_set_parent_uuid_invalid(self):
        logging.disable(logging.WARNING)
        self.proxy.set_parent_uuid("invalid_uuid")
        logging.disable(logging.NOTSET)
        result = self.proxy.parent_uuid
        expected = None
        self.assertEqual(expected, result)

    def test_proxy_set_parent_uuid_valid(self):
        valid_uuid = "4c0c8e52-b7bc-48fb-8e07-e98f7236568a"
        self.proxy.set_parent_uuid(valid_uuid)
        result = self.proxy.parent_uuid
        self.assertEqual(valid_uuid, result)

    def test_proxy_set_parent_uuid_from_proxy(self):
        mocked_proxy = tools_rig_frm.Proxy()
        self.proxy.set_parent_uuid_from_proxy(mocked_proxy)
        result = self.proxy.parent_uuid
        self.assertEqual(mocked_proxy.uuid, result)

    def test_proxy_clear_uuid_valid(self):
        mocked_proxy = tools_rig_frm.Proxy()
        self.proxy.set_parent_uuid_from_proxy(mocked_proxy)
        self.proxy.clear_parent_uuid()
        expected = None
        result = self.proxy.parent_uuid
        self.assertEqual(expected, result)

    def test_proxy_set_meta_purpose(self):
        self.proxy.set_meta_purpose("purpose")
        result = self.proxy.get_metadata()
        expected = {"proxyPurpose": "purpose"}
        self.assertEqual(expected, result)

    def test_proxy_get_metadata(self):
        mocked_dict = {"metadata_key": "metadata_value"}
        self.proxy.set_metadata_dict(mocked_dict)
        result = self.proxy.get_metadata()
        self.assertEqual(mocked_dict, result)

    def test_proxy_get_meta_purpose(self):
        self.proxy.set_meta_purpose("purpose")
        result = self.proxy.get_meta_purpose()
        expected = "purpose"
        self.assertEqual(expected, result)

    def test_proxy_get_meta_no_purpose(self):
        self.proxy.set_meta_purpose(None)
        result = self.proxy.get_meta_purpose()
        expected = None
        self.assertEqual(expected, result)

    def test_proxy_get_metadata_value(self):
        mocked_dict = {"metadata_key": "metadata_value"}
        self.proxy.set_metadata_dict(mocked_dict)
        result = self.proxy.get_metadata()
        self.assertEqual(mocked_dict, result)

    def test_proxy_read_data_from_dict(self):
        mocked_dict = {"metadata_key": "metadata_value", "locatorScale": "4", "transform": "5"}
        self.proxy.set_metadata_dict(mocked_dict)
        dictionary = self.proxy.read_data_from_dict(mocked_dict)
        result = dictionary.metadata
        expected_dictionary = mocked_dict
        self.assertEqual(expected_dictionary, result)

    def test_proxy_get_mirrored_transform(self):
        self.proxy.set_position(x=6, y=10, z=2)
        self.proxy.set_rotation(x=5, y=45, z=30)
        self.proxy.set_scale(x=1.2, y=1.6, z=1.4)
        mirrored_proxy = tools_rig_frm.Proxy(name="mirrored_proxy")
        mirrored_transform = self.proxy.get_mirrored_transform()
        mirrored_proxy.set_transform(mirrored_transform)
        transform = mirrored_proxy.transform
        position = [transform.position.x, transform.position.y, transform.position.z]
        self.assertEqual([-6.0, 10.0, 2.0], position)
        rotation = [transform.rotation.x, transform.rotation.y, transform.rotation.z]
        self.assertEqual([-175.0, -45.0, -30.0], rotation)
        scale = [transform.scale.x, transform.scale.y, transform.scale.z]
        self.assertEqual([1.2, 1.6, 1.4], scale)

    # --------------------------------------------- ModuleGeneric ---------------------------------------------
    def test_module_set_proxies(self):
        a_1st_proxy = tools_rig_frm.Proxy(name="a_1st_proxy")
        a_2nd_proxy = tools_rig_frm.Proxy(name="a_2nd_proxy")
        a_3rd_proxy = tools_rig_frm.Proxy(name="a_3rd_proxy")
        proxy_list = [a_1st_proxy, a_2nd_proxy, a_3rd_proxy]
        self.module.set_proxies(proxy_list)
        self.assertEqual(proxy_list, self.module.proxies)

    def test_module_remove_from_proxies(self):
        a_1st_proxy = tools_rig_frm.Proxy(name="a_1st_proxy")
        a_2nd_proxy = tools_rig_frm.Proxy(name="a_2nd_proxy")
        a_3rd_proxy = tools_rig_frm.Proxy(name="a_3rd_proxy")
        proxy_list = [a_1st_proxy, a_2nd_proxy, a_3rd_proxy]
        self.module.set_proxies(proxy_list)
        self.assertEqual(proxy_list, self.module.proxies)
        self.module.remove_from_proxies(a_2nd_proxy)
        result = self.module.get_proxies()
        expected = [a_1st_proxy, a_3rd_proxy]
        self.assertEqual(expected, result)

    def test_module_get_proxies(self):
        a_1st_proxy = tools_rig_frm.Proxy(name="proxy_1")
        a_2nd_proxy = tools_rig_frm.Proxy(name="proxy_2")
        a_3rd_proxy = tools_rig_frm.Proxy(name="proxy_3")
        a_4th_proxy = tools_rig_frm.Proxy(name="proxy_4")

        a_module = tools_rig_frm.ModuleGeneric()
        a_module.add_to_proxies(a_1st_proxy)
        a_module.add_to_proxies(a_2nd_proxy)
        a_module.add_to_proxies(a_3rd_proxy)
        a_module.add_to_proxies(a_4th_proxy)
        root_dummy = core_uuid.generate_uuid()

        # test 00 - default without sorting, entry sequence
        proxies = a_module.get_proxies()
        expected = ["proxy_1", "proxy_2", "proxy_3", "proxy_4"]
        result = [pp.name for pp in proxies]
        self.assertEqual(expected, result)

        # test 01 - set standard fk and proxies setup inverted
        a_1st_proxy.set_parent_uuid(root_dummy)
        a_2nd_proxy.set_parent_uuid(a_1st_proxy.get_uuid())
        a_3rd_proxy.set_parent_uuid(a_2nd_proxy.get_uuid())
        a_4th_proxy.set_parent_uuid(a_3rd_proxy.get_uuid())

        a_1st_proxy.set_setup_driver_uuid(a_2nd_proxy.get_uuid())
        a_2nd_proxy.set_setup_driver_uuid(a_3rd_proxy.get_uuid())
        a_3rd_proxy.set_setup_driver_uuid(a_4th_proxy.get_uuid())
        a_4th_proxy.set_setup_driver_uuid(root_dummy)

        proxies_by_parent = a_module.get_proxies(sort_by="parent")
        expected = ["proxy_1", "proxy_2", "proxy_3", "proxy_4"]
        result = [pp.name for pp in proxies_by_parent]
        self.assertEqual(expected, result)
        proxies_by_driver = a_module.get_proxies(sort_by="setup_driver")
        expected = ["proxy_4", "proxy_3", "proxy_2", "proxy_1"]
        result = [pd.name for pd in proxies_by_driver]
        self.assertEqual(expected, result)

        # reset
        [prx.clear_parent_uuid() for prx in a_module.get_proxies()]
        [prx.clear_setup_driver_uuid() for prx in a_module.get_proxies()]

        # test 02 - set standard fk and skip proxies setup hierarchy
        a_1st_proxy.set_parent_uuid(root_dummy)
        a_2nd_proxy.set_parent_uuid(a_1st_proxy.get_uuid())
        a_3rd_proxy.set_parent_uuid(a_2nd_proxy.get_uuid())
        a_4th_proxy.set_parent_uuid(a_3rd_proxy.get_uuid())

        proxies_by_parent = a_module.get_proxies(sort_by="parent")
        expected = ["proxy_1", "proxy_2", "proxy_3", "proxy_4"]
        result = [pp.name for pp in proxies_by_parent]
        self.assertEqual(expected, result)
        proxies_by_driver = a_module.get_proxies(sort_by="setup_driver")
        expected = ["proxy_1", "proxy_2", "proxy_3", "proxy_4"]
        result = [pd.name for pd in proxies_by_driver]
        self.assertEqual(expected, result)

        # reset
        [prx.clear_parent_uuid() for prx in a_module.get_proxies()]
        [prx.clear_setup_driver_uuid() for prx in a_module.get_proxies()]

        # test 03 - set standard fk and override one for proxies setup
        a_1st_proxy.set_parent_uuid(root_dummy)
        a_2nd_proxy.set_parent_uuid(a_1st_proxy.get_uuid())
        a_3rd_proxy.set_parent_uuid(a_2nd_proxy.get_uuid())
        a_4th_proxy.set_parent_uuid(a_3rd_proxy.get_uuid())

        a_3rd_proxy.set_setup_driver_uuid(a_4th_proxy.get_uuid())
        a_4th_proxy.set_setup_driver_uuid(a_1st_proxy.get_uuid())

        proxies_by_parent = a_module.get_proxies(sort_by="parent")
        expected = ["proxy_1", "proxy_2", "proxy_3", "proxy_4"]
        result = [pp.name for pp in proxies_by_parent]
        self.assertEqual(expected, result)
        proxies_by_driver = a_module.get_proxies(sort_by="setup_driver")
        expected = ["proxy_1", "proxy_2", "proxy_4", "proxy_3"]
        result = [pd.name for pd in proxies_by_driver]
        self.assertEqual(expected, result)

    def test_module_set_orientation(self):
        _orientation = tools_rig_frm.OrientationData(aim_axis=(90, 0, 70), up_axis=(60, 0, 1), up_dir=(0, 0, 0))
        self.module.set_orientation(orientation_data=_orientation)
        result = self.module.get_orientation_data()
        self.assertEqual(_orientation, result)

    def test_module_set_orientation_method(self):
        self.module.set_orientation_method(method="world")
        result = self.module.get_orientation_method()
        expected = "world"
        self.assertEqual(expected, result)
        self.module.set_orientation_method(method="automatic")
        result = self.module.get_orientation_method()
        expected = "automatic"
        self.assertEqual(expected, result)
        self.module.set_orientation_method(method="inherit")
        result = self.module.get_orientation_method()
        expected = "inherit"
        self.assertEqual(expected, result)

    def test_module_get_prefix(self):
        result = self.module.get_prefix()
        expected = None
        self.assertEqual(expected, result)
        a_module = tools_rig_frm.ModuleGeneric(prefix="mocked_prefix")
        result = a_module.get_prefix()
        expected = "mocked_prefix"
        self.assertEqual(expected, result)

    def test_module_set_prefix(self):
        self.module.set_prefix(prefix="mocked_prefix")
        result = self.module.get_prefix()
        expected = "mocked_prefix"
        self.assertEqual(expected, result)

    def test_module_get_suffix(self):
        result = self.module.get_suffix()
        expected = None
        self.assertEqual(expected, result)
        a_module = tools_rig_frm.ModuleGeneric(suffix="mocked_suffix")
        result = a_module.get_suffix()
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_set_suffix(self):
        self.module.set_suffix(suffix="mocked_suffix")
        result = self.module.get_suffix()
        expected = "mocked_suffix"
        self.assertEqual(expected, result)

    def test_module_read_data_from_scene(self):
        a_proxy_one = tools_rig_frm.Proxy(name="a_proxy_one")
        a_proxy_two = tools_rig_frm.Proxy(name="a_proxy_two")
        a_1st_module = tools_rig_frm.ModuleGeneric()
        a_2nd_module = tools_rig_frm.ModuleGeneric()
        a_project = tools_rig_frm.RigProject()
        a_1st_module.add_to_proxies(a_proxy_one)
        a_2nd_module.add_to_proxies(a_proxy_two)
        a_project.add_to_modules(a_1st_module)
        a_project.add_to_modules(a_2nd_module)
        a_project.build_proxy()
        # Modify proxy
        cmds.setAttr(f"a_proxy_one.ty", 15)
        cmds.setAttr(f"a_proxy_two.tx", 25)
        a_1st_module.read_data_from_scene()
        a_2nd_module.read_data_from_scene()
        a_1st_module_dict = a_1st_module.get_module_as_dict()
        a_2nd_module_dict = a_2nd_module.get_module_as_dict()
        a_1st_proxy_dict = a_1st_module_dict.get("proxies")
        a_2nd_proxy_dict = a_2nd_module_dict.get("proxies")
        a_1st_proxy_pos = a_1st_proxy_dict.get(a_proxy_one.get_uuid()).get("transform").get("position")
        a_2nd_proxy_pos = a_2nd_proxy_dict.get(a_proxy_two.get_uuid()).get("transform").get("position")
        expected = (0, 15, 0)
        self.assertEqual(expected, a_1st_proxy_pos)
        expected = (25, 0, 0)
        self.assertEqual(expected, a_2nd_proxy_pos)

    # --------------------------------------------- RigProject ---------------------------------------------
    def test_project_read_data_from_scene(self):
        a_1st_proxy = tools_rig_frm.Proxy(name="a_1st_proxy")
        a_2nd_proxy = tools_rig_frm.Proxy(name="a_2nd_proxy")
        a_module = tools_rig_frm.ModuleGeneric()
        a_project = tools_rig_frm.RigProject()
        a_module.add_to_proxies(a_1st_proxy)
        a_module.add_to_proxies(a_2nd_proxy)
        a_project.add_to_modules(a_module)
        a_project.build_proxy()
        cmds.setAttr("a_1st_proxy.ty", 20)
        cmds.setAttr("a_2nd_proxy.tx", 15)
        a_project.read_data_from_scene()
        a_1st_proxy_dict = a_1st_proxy.get_proxy_as_dict()
        a_2nd_proxy_dict = a_2nd_proxy.get_proxy_as_dict()
        result_1st_proxy_transform = a_1st_proxy_dict.get("transform")
        result_2nd_proxy_transform = a_2nd_proxy_dict.get("transform")
        expected_1st_proxy_transform = {
            "position": (0.0, 20.0, 0.0),
            "rotation": (0.0, 0.0, 0.0),
            "scale": (1.0, 1.0, 1.0),
        }
        self.assertEqual(expected_1st_proxy_transform, result_1st_proxy_transform)
        expected_2nd_proxy_transform = {
            "position": (15.0, 0.0, 0.0),
            "rotation": (0.0, 0.0, 0.0),
            "scale": (1.0, 1.0, 1.0),
        }
        self.assertEqual(expected_2nd_proxy_transform, result_2nd_proxy_transform)

    def test_project_get_project_as_dict(self):
        _uuid = "z56xvx"
        self.project.uuid = _uuid
        result = self.project.get_project_as_dict()
        expected = {
            "name": "Untitled",
            "uuid": _uuid,
            "modules": [],
            "preferences": {
                "alias": None,
                "build_control_rig": True,
                "control_rig_pose_name": f"{core_naming.NamingConstants.Poses.TPOSE}",
                "delete_proxy_after_build": True,
                "export_anim_blendshapes": False,
                "apply_control_rig_pose": True,
                "hide_skeleton": True,
                "project_dir": "{project-file-dir}",
                "view_fit_skeleton": True,
            },
        }
        self.assertEqual(expected, result)

    def test_project_build_proxy_check_elements(self):
        a_proxy = tools_rig_frm.Proxy()
        a_module = tools_rig_frm.ModuleGeneric()
        a_project = tools_rig_frm.RigProject()
        a_module.add_to_proxies(a_proxy)
        a_project.add_to_modules(a_module)
        a_project.build_proxy()
        expected = ["rig_proxy", "C_globalProxy", "root_ctrlCircleShape", "root_ctrlArrowShape"]
        for obj in expected:
            self.assertTrue(cmds.objExists(obj))
        self.assertTrue(cmds.objExists(obj))

    def test_project_build_rig_check_elements(self):
        a_1st_proxy = tools_rig_frm.Proxy(name="proxy_1")
        a_2nd_proxy = tools_rig_frm.Proxy()
        a_1st_module = tools_rig_frm.ModuleGeneric()
        a_2nd_module = tools_rig_frm.ModuleGeneric(name="proxy_2")
        a_1st_proxy.set_name(name="proxy_extra")
        a_2nd_module.set_prefix("mocked_second")
        a_project = tools_rig_frm.RigProject()
        a_1st_module.add_to_proxies(a_1st_proxy)
        a_2nd_module.add_to_proxies(a_2nd_proxy)
        a_project.add_to_modules(a_1st_module)
        a_project.add_to_modules(a_2nd_module)
        a_project.build_proxy()
        cmds.setAttr("proxy_extra.tx", 15)
        a_project.build_rig()
        expected = [
            "rig",
            "root_ctrlCircleShape",
            "root_ctrlArrowShape",
            "C_global_CTRL",
            "C_globalOffset_CTRL",
            "C_globalOffset_CTRLShape",
            "geometry",
            "skeleton",
            "controls",
            "setup",
            "proxy_extra_JNT",
            "mocked_second_proxy_JNT",
        ]

        for obj in expected:
            self.assertTrue(cmds.objExists(obj))
        self.assertTrue(cmds.objExists(obj))
        result_transform = cmds.getAttr("proxy_extra_JNT.translate")
        expected_transform = [(15.0, 0.0, 0.0)]
        self.assertEqual(expected_transform, result_transform)

        result_transform = cmds.getAttr("mocked_second_proxy_JNT.translate")
        expected_transform = [(0.0, 0.0, 0.0)]
        self.assertEqual(expected_transform, result_transform)
