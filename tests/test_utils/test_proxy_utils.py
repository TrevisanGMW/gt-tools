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
        expected = "proxy_crv"
        self.assertEqual(expected, result)

    def test_proxy_custom_curve(self):
        from gt.utils.curve_utils import Curves
        proxy = Proxy(curve=Curves.circle)
        result = proxy.build()
        self.assertTrue(proxy.is_proxy_valid())
        expected = "proxy_crv"
        self.assertEqual(expected, result)

    def test_get_name_default(self):
        result = self.proxy.get_name()
        expected = "proxy_crv"
        self.assertEqual(expected, result)

    def test_set_name(self):
        self.proxy.set_name("description")
        result = self.proxy.get_name()
        expected = "description"
        self.assertEqual(expected, result)
        result = self.proxy.build()
        expected = "description"
        self.assertEqual(expected, result)
