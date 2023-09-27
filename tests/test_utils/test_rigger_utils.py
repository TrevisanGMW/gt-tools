from unittest.mock import MagicMock, patch
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
from gt.utils.transform_utils import Transform
from gt.utils.rigger_utils import Proxy
from tests import maya_test_tools
from gt.utils import rigger_utils


class TestProxyUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        self.proxy = Proxy()
        self.proxy_data = rigger_utils.ProxyData(name="proxy1", offset="offset1", setup=("setup1", "setup2"))

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_proxy_constants(self):
        attributes = vars(rigger_utils.RiggerConstants)
        keys = [attr for attr in attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for key in keys:
            constant = getattr(rigger_utils.RiggerConstants, key)
            if not constant:
                raise Exception(f'Missing proxy constant data: {key}')
            if not isinstance(constant, str):
                raise Exception(f'Incorrect proxy constant type: {key}')

    def test_repr(self):
        expected = "proxy1"
        result = repr(self.proxy_data)
        self.assertEqual(expected, result)

    def test_get_short_name(self):
        expected = "proxy1"
        result = self.proxy_data.get_short_name()
        self.assertEqual(expected, result)

    def test_get_long_name(self):
        expected = "proxy1"
        result = self.proxy_data.get_long_name()
        self.assertEqual(expected, result)

    def test_get_offset(self):
        expected = "offset1"
        result = self.proxy_data.get_offset()
        self.assertEqual(expected, result)

    def test_get_setup(self):
        expected = ("setup1", "setup2")
        result = self.proxy_data.get_setup()
        self.assertEqual(expected, result)

    def test_proxy_default(self):
        result = self.proxy.build()
        self.assertTrue(self.proxy.is_valid())
        expected = "|proxy_offset|proxy"
        self.assertEqual(expected, str(result))
        expected = "proxy"
        self.assertEqual(expected, result.get_short_name())
        self.assertTrue(isinstance(result, rigger_utils.ProxyData))
        expected = "|proxy_offset"
        self.assertEqual(expected, result.offset)
        expected = ("proxy_LocScaleHandle",)
        self.assertEqual(expected, result.setup)

    def test_proxy_init(self):
        from gt.utils import transform_utils
        from gt.utils import curve_utils
        mocked_transform = transform_utils.Transform(position=(0, 10, 0))
        expected_name = "mocked_name"
        expected_curve = curve_utils.get_curve("circle")
        expected_uuid = "123e4567-e89b-12d3-a456-426655440000"
        expected_metadata = {"metadata": "value"}
        proxy = Proxy(name=expected_name,
                      transform=mocked_transform,
                      offset_transform=mocked_transform,
                      curve=expected_curve,
                      uuid=expected_uuid,
                      parent_uuid=expected_uuid,
                      metadata=expected_metadata)
        self.assertEqual(expected_name, proxy.name)
        self.assertEqual(mocked_transform, proxy.transform)
        self.assertEqual(mocked_transform, proxy.offset_transform)
        self.assertEqual(expected_curve, proxy.curve)
        self.assertEqual(expected_uuid, proxy.uuid)
        self.assertEqual(expected_uuid, proxy.parent_uuid)
        self.assertEqual(expected_metadata, proxy.metadata)
        self.assertTrue(proxy.is_valid())

    def test_proxy_build(self):
        result = self.proxy.build()
        expected_long_name = "|proxy_offset|proxy"
        expected_short_name = "proxy"
        self.assertEqual(expected_long_name, str(result))
        self.assertEqual(expected_short_name, result.get_short_name())
        self.assertTrue(isinstance(result, rigger_utils.ProxyData))
        self.assertTrue(maya_test_tools.cmds.objExists(f'{result}.{rigger_utils.RiggerConstants.SEPARATOR_ATTR}'))
        self.assertTrue(maya_test_tools.cmds.objExists(f'{result}.{rigger_utils.RiggerConstants.PROXY_ATTR_UUID}'))
        self.assertTrue(maya_test_tools.cmds.objExists(f'{result}.{rigger_utils.RiggerConstants.PROXY_ATTR_UUID}'))

    def test_proxy_custom_curve(self):
        from gt.utils.curve_utils import Curves
        proxy = Proxy(curve=Curves.circle)
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
        proxy = Proxy(uuid=expected_uuid)
        result = proxy.get_uuid()
        self.assertEqual(expected_uuid, result)

    def test_proxy_get_parent_uuid_default(self):
        expected_parent_uuid = "123e4567-e89b-12d3-a456-426655440002"
        proxy = Proxy(parent_uuid=expected_parent_uuid)
        result = proxy.get_parent_uuid()
        self.assertEqual(expected_parent_uuid, result)

    def test_proxy_set_name(self):
        self.proxy.set_name("description")
        result = self.proxy.get_name()
        expected = "description"
        self.assertEqual(expected, result)
        result = self.proxy.build()
        expected = "description"
        self.assertEqual(expected, result.get_short_name())

    def test_proxy_set_transform(self):
        transform = Transform(position=(0, 10, 0))
        self.proxy.set_transform(transform=transform)
        result = self.proxy.transform
        self.assertEqual(transform, result)

    def test_proxy_set_position(self):
        transform = Transform(position=(0, 10, 0))
        self.proxy.set_position(0, 10, 0)
        result = self.proxy.transform
        self.assertEqual(transform, result)

    def test_proxy_set_rotation(self):
        transform = Transform(rotation=(0, 10, 0))
        self.proxy.set_rotation(0, 10, 0)
        result = self.proxy.transform
        self.assertEqual(transform, result)

    def test_proxy_set_scale(self):
        transform = Transform(scale=(0, 10, 0))
        self.proxy.set_scale(0, 10, 0)
        result = self.proxy.transform
        self.assertEqual(transform, result)

    def test_proxy_set_offset_transform(self):
        transform = Transform(position=(0, 10, 0))
        self.proxy.set_offset_transform(transform=transform)
        result = self.proxy.offset_transform
        self.assertEqual(transform, result)

    def test_proxy_set_offset_position(self):
        transform = Transform(position=(0, 10, 0))
        self.proxy.set_offset_position(0, 10, 0)
        result = self.proxy.offset_transform
        self.assertEqual(transform, result)

    def test_proxy_set_offset_rotation(self):
        transform = Transform(rotation=(0, 10, 0))
        self.proxy.set_offset_rotation(0, 10, 0)
        result = self.proxy.offset_transform
        self.assertEqual(transform, result)

    def test_proxy_set_offset_scale(self):
        transform = Transform(scale=(0, 10, 0))
        self.proxy.set_offset_scale(0, 10, 0)
        result = self.proxy.offset_transform
        self.assertEqual(transform, result)

    def test_proxy_set_curve(self):
        from gt.utils import curve_utils
        curve = curve_utils.Curves.circle
        self.proxy.set_curve(curve)
        result = self.proxy.curve
        self.assertEqual(curve, result)

    def test_proxy_set_curve_inherit_name(self):
        from gt.utils import curve_utils
        curve = curve_utils.Curves.circle
        self.proxy.set_curve(curve=curve, inherit_curve_name=True)
        result = self.proxy.curve
        self.assertEqual(curve, result)
        result = self.proxy.get_name()
        expected = self.proxy.curve.get_name()
        self.assertEqual(expected, result)

    def test_proxy_set_locator_scale(self):
        self.proxy.set_locator_scale(2)
        result = self.proxy.locator_scale
        expected = 2
        self.assertEqual(expected, result)

    def test_proxy_metadata_default(self):
        result = self.proxy.metadata
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

    def test_proxy_set_uuid_invalid(self):
        original_uuid = self.proxy.uuid
        logging.disable(logging.WARNING)
        self.proxy.set_uuid("invalid_uuid")
        logging.disable(logging.NOTSET)
        result = self.proxy.uuid
        self.assertEqual(original_uuid, result)

    def test_proxy_set_uuid_valid(self):
        valid_uuid = "123e4567-e89b-12d3-a456-426655440000"
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
        valid_uuid = "123e4567-e89b-12d3-a456-426655440000"
        self.proxy.set_parent_uuid(valid_uuid)
        result = self.proxy.parent_uuid
        self.assertEqual(valid_uuid, result)

    def test_proxy_get_metadata(self):
        mocked_dict = {"metadata_key": "metadata_value"}
        self.proxy.set_metadata_dict(mocked_dict)
        result = self.proxy.get_metadata()
        self.assertEqual(mocked_dict, result)
