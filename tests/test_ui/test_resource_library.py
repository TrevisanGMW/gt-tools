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
    def test_get_resource_path(self):
        result = resource_library.get_resource_path(resource_name="name", resource_folder="folder")
        expected = os.path.join("folder", "name")
        self.assertEqual(expected, result)

    def test_get_resource_path_sub_folder(self):
        result = resource_library.get_resource_path(resource_name="name", resource_folder="folder", sub_folder="sub")
        expected = os.path.join("folder", "sub", "name")
        self.assertEqual(expected, result)

    def test_get_icon_path(self):
        result = resource_library.get_icon_path(icon_name="package_logo.svg")
        expected = os.path.join(resource_library.ResourceDirConstants.DIR_ICONS, "package_logo.svg")
        self.assertEqual(expected, result)

    def test_get_font_path(self):
        result = resource_library.get_font_path(font_name="Roboto-Regular.ttf")
        expected = os.path.join(resource_library.ResourceDirConstants.DIR_FONTS, "Roboto-Regular.ttf")
        self.assertEqual(expected, result)

    def test_get_stylesheet_content(self):
        result = resource_library.get_stylesheet_content(stylesheet_name="maya_basic_dialog")
        expected = "QWidget"
        self.assertIn(expected, result)

    def test_process_stylesheet_variables(self):
        mocked_variables = {"@original": "modified"}
        result = resource_library.process_stylesheet_variables(stylesheet_content="@original",
                                                               stylesheet_variables=mocked_variables)
        expected = "modified;"
        self.assertEqual(expected, result)

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

    def test_rgba_string_to_hex(self):
        result = resource_library.rgba_string_to_hex("rgba(255,255,255,255)")
        expected = "#FFFFFF"
        self.assertEqual(expected, result)

    def test_resource_dir_constants(self):

        all_dirs_attributes = vars(resource_library.ResourceDirConstants)

        all_dirs_keys = [attr for attr in all_dirs_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for dir_key in all_dirs_keys:
            dir_path = getattr(resource_library.ResourceDirConstants, dir_key)
            if not dir_path:
                raise Exception(f'Missing proper file path for directory: {dir_key}')
            if not os.path.exists(dir_path):
                raise Exception(f'Missing constant directory: {dir_path}')

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

    def test_icon_paths_existence(self):
        all_icon_attributes = vars(resource_library.Icon)
        all_icon_keys = [attr for attr in all_icon_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for icon_key in all_icon_keys:
            icon_path = getattr(resource_library.Icon, icon_key)
            if not icon_path:
                raise Exception(f'Missing file path for icon: {icon_key}')
            if not os.path.exists(icon_path):
                raise Exception(f'Missing file for an icon path: {icon_path}')

    def test_stylesheet_variables(self):
        all_attributes = dir(resource_library.StylesheetVariables)
        stylesheet_keys = [attr for attr in all_attributes if not (attr.startswith('__') and attr.endswith('__'))]

        for stylesheet_key in stylesheet_keys:
            stylesheet_content = getattr(resource_library.StylesheetVariables, stylesheet_key)
            if not isinstance(stylesheet_content, dict):
                raise Exception(f'Stylesheet output should be "dict" but returned "{type(stylesheet_content)}"'
                                f' for stylesheet key: "{stylesheet_key}:.')
            if len(stylesheet_content) == 0:
                raise Exception(f'Stylesheet returned an empty dictionary: {stylesheet_key}')

    def test_stylesheets(self):
        all_attributes = dir(resource_library.Stylesheet)
        stylesheet_keys = [attr for attr in all_attributes if not (attr.startswith('__') and attr.endswith('__'))]

        for stylesheet_key in stylesheet_keys:
            stylesheet_content = getattr(resource_library.Stylesheet, stylesheet_key)
            if not isinstance(stylesheet_content, str):
                raise Exception(f'Stylesheet output should be "str" but returned "{type(stylesheet_content)}"'
                                f' for stylesheet key: "{stylesheet_key}:.')
            if stylesheet_content == "":
                raise Exception(f'Stylesheet returned an empty string. Stylesheet key: "{stylesheet_key}".')

    def test_font_paths_existence(self):
        all_icon_attributes = vars(resource_library.Font)
        all_font_keys = [attr for attr in all_icon_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for font_key in all_font_keys:
            font_path = getattr(resource_library.Font, font_key)
            if not font_path:
                raise Exception(f'Missing file path for font: {font_key}')
            if not os.path.exists(font_path):
                raise Exception(f'Missing file for a font path: {font_path}')
