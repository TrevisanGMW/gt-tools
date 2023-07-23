import unittest
import logging
import sys
import os
import re

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

    def test_rgb_to_hex_without_alpha(self):
        # Test RGB values without alpha
        self.assertEqual(resource_library.rgba_to_hex(255, 0, 0), "#FF0000")
        self.assertEqual(resource_library.rgba_to_hex(0, 255, 0), "#00FF00")
        self.assertEqual(resource_library.rgba_to_hex(0, 0, 255), "#0000FF")
        self.assertEqual(resource_library.rgba_to_hex(128, 128, 128), "#808080")

    def test_rgba_to_hex_with_alpha(self):
        # Test RGBA values with alpha
        self.assertEqual(resource_library.rgba_to_hex(255, 0, 0, 128, True), "#FF000080")
        self.assertEqual(resource_library.rgba_to_hex(0, 255, 0, 64, True), "#00FF0040")
        self.assertEqual(resource_library.rgba_to_hex(0, 0, 255, 192, True), "#0000FFC0")
        self.assertEqual(resource_library.rgba_to_hex(128, 128, 128, 255, True), "#808080FF")

    def test_rgba_to_hex_without_alpha(self):
        # Test RGBA values without alpha (alpha should default to 255)
        self.assertEqual(resource_library.rgba_to_hex(255, 0, 0, include_alpha=False), "#FF0000")
        self.assertEqual(resource_library.rgba_to_hex(0, 255, 0, include_alpha=False), "#00FF00")
        self.assertEqual(resource_library.rgba_to_hex(0, 0, 255, include_alpha=False), "#0000FF")
        self.assertEqual(resource_library.rgba_to_hex(128, 128, 128, include_alpha=False), "#808080")

    def test_rgb_to_hex(self):
        # Test RGB values without alpha
        self.assertEqual(resource_library.rgb_to_hex(255, 0, 0), "#FF0000")
        self.assertEqual(resource_library.rgb_to_hex(0, 255, 0), "#00FF00")
        self.assertEqual(resource_library.rgb_to_hex(0, 0, 255), "#0000FF")
        self.assertEqual(resource_library.rgb_to_hex(128, 128, 128), "#808080")

    def test_rgb_to_hex_boundary_values(self):
        # Test boundary values
        self.assertEqual(resource_library.rgb_to_hex(0, 0, 0), "#000000")  # Test black
        self.assertEqual(resource_library.rgb_to_hex(255, 255, 255), "#FFFFFF")  # Test white
        self.assertEqual(resource_library.rgb_to_hex(0, 0, 0), "#000000")  # Test black
        self.assertEqual(resource_library.rgb_to_hex(255, 255, 255), "#FFFFFF")  # Test white

    def test_valid_rgb_string(self):
        rgb_string = "rgb(255, 255, 255)"
        result = resource_library.parse_rgb_numbers(rgb_string)
        self.assertEqual(result, (255, 255, 255))

    def test_limit_rgb_string(self):
        rgb_string = "rgb(256, 255, 255)"  # R value exceeds 255
        result = resource_library.parse_rgb_numbers(rgb_string)
        self.assertEqual(result, (255, 255, 255))

    def test_invalid_rgba_string(self):
        rgba_string = "rgba(100, 150, 200, 1.5)"  # Alpha value exceeds 1.0
        result = resource_library.parse_rgb_numbers(rgba_string)
        self.assertIsNone(result)

    def test_invalid_format(self):
        rgb_string = "rgb(100, 150, 200, 0.5)"  # Wrong format, no alpha in rgb
        result = resource_library.parse_rgb_numbers(rgb_string)
        self.assertIsNone(result)

    def test_empty_string(self):
        result = resource_library.parse_rgb_numbers("")
        self.assertIsNone(result)

    def test_non_matching_string(self):
        rgb_string = "hsl(100, 50%, 50%)"  # Non-matching string
        result = resource_library.parse_rgb_numbers(rgb_string)
        self.assertIsNone(result)

    def test_hex_color_pattern(self):
        all_attributes = dir(resource_library.Color.Hex)
        user_attributes = [attr for attr in all_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for hex_color in user_attributes:
            attribute_content = getattr(resource_library.Color.Hex, hex_color)
            match = re.match(r'^#[A-F0-9]{6}(?:[A-F0-9]{2})?$', attribute_content)
            if not match:
                raise Exception(f'"{attribute_content}" does not match expected HEX pattern: '
                                f'\n1. Only uppercase characters.\n2. Expected length (6-8 chars)'
                                f'\n3. Start with "#".\n4. No three digit HEX values.')

    def test_rgb_color_pattern(self):
        all_attributes = dir(resource_library.Color.RGB)
        user_attributes = [attr for attr in all_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        pattern = r'^(rgb|rgba)\((25[0-5]|2[0-4]\d|1\d{2}|[1-9]\d|[0-9]),\s*(25[0-5]|2[0-4]\d|1\d{2}|' \
                  r'[1-9]\d|[0-9]),\s*(25[0-5]|2[0-4]\d|1\d{2}|[1-9]\d|[0-9])(?:,\s*((?:25[0-5]|2[0-4]\d|' \
                  r'1\d{2}|[1-9]\d|[0-9])|0))?\)$'
        for rgb_color in user_attributes:
            attribute_content = getattr(resource_library.Color.RGB, rgb_color)
            match = re.match(pattern, attribute_content)
            if not match:
                raise Exception(f'"{attribute_content}" does not match expected RGB pattern:'
                                f'\n1.It should start with either "rgb" or "rgba".'
                                f'\n2.It should always contain at least one "(" and one ")" '
                                f'\n3.It can have 3 or 4 numbers, but not more or less than that.'
                                f'\n4."rgb" or "rgba" should be lower case.')
