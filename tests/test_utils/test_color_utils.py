import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from tests.maya_test_tools import maya_test_utils
from utils import color_utils


class TestColorUtils(unittest.TestCase):
    def setUp(self):
        maya_test_utils.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_utils.import_maya_standalone()  # Start Maya Headless (mayapy.exe)

    def test_set_color_override_viewport(self):
        test_obj = 'test_cube'
        maya_test_utils.create_poly_cube(name=test_obj)

        expected = (0, 0.5, 1)
        result = color_utils.set_color_override_viewport(test_obj, rgb_color=expected)
        self.assertEqual(expected, result)

    def test_set_color_override_outliner(self):
        test_obj = 'test_cube'
        maya_test_utils.create_poly_cube(name=test_obj)

        expected = (0, 0.5, 1)
        result = color_utils.set_color_override_outliner(test_obj, rgb_color=expected)
        self.assertEqual(expected, result)
