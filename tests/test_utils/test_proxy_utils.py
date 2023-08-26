from unittest.mock import MagicMock, patch
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from tests import maya_test_tools
from gt.utils.proxy_utils import Proxy
from gt.utils import proxy_utils


class TestProxyUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        self.proxy = Proxy()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_proxy_default(self):
        result = self.proxy.build()
        self.assertTrue(self.proxy.is_proxy_valid())
        expected = "proxy"
        self.assertEqual(expected, str(result))
        self.assertEqual(expected, result.get_short_name())
        self.assertTrue(isinstance(result, proxy_utils.ProxyData))
        expected = "proxy_offset"
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
        self.assertTrue(proxy.is_proxy_valid())

    def test_proxy_custom_curve(self):
        from gt.utils.curve_utils import Curves
        proxy = Proxy(curve=Curves.circle)
        result = proxy.build()
        self.assertTrue(proxy.is_proxy_valid())
        expected = "proxy"
        self.assertEqual(expected, result.get_short_name())

    def test_proxy_get_name_default(self):
        result = self.proxy.get_name()
        expected = "proxy"
        self.assertEqual(expected, result)

    def test_proxy_set_name(self):
        self.proxy.set_name("description")
        result = self.proxy.get_name()
        expected = "description"
        self.assertEqual(expected, result)
        result = self.proxy.build()
        expected = "description"
        self.assertEqual(expected, result.get_short_name())

    def test_proxy_build(self):
        result = self.proxy.build()
        expected = "proxy"
        self.assertEqual(expected, str(result))
        # TODO, check basic attributes
        self.assertEqual(expected, result.get_short_name())

