import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Script
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.ui import resource_library


class TestResourceLibrary(unittest.TestCase):
    def test_color_rgb_black_class(self):
        result = resource_library.Color.RGB.black
        expected = "rgba(0,0,0,255)"
        self.assertEqual(expected, result)

    def test_color_rgb_white_class(self):
        result = resource_library.Color.RGB.white
        expected = "rgba(255,255,255,255)"
        self.assertEqual(expected, result)

    def test_color_hex_black_class(self):
        result = resource_library.Color.Hex.black
        expected = "#000000"
        self.assertEqual(expected, result)

    def test_color_hex_white_class(self):
        result = resource_library.Color.Hex.white
        expected = "#FFFFFF"
        self.assertEqual(expected, result)


