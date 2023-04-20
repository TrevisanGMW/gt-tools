import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_string_utils")
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from utils import string_utils


class TestStringUtils(unittest.TestCase):
    def test_remove_string_prefix(self):
        string_to_test = "oneTwoThree"
        expected = "TwoThree"
        result = string_utils.remove_string_prefix(input_string=string_to_test, prefix="one")
        self.assertEqual(expected, result)

    def test_remove_string_prefix_no_change(self):
        string_to_test = "oneTwoThree"
        expected = string_to_test
        result = string_utils.remove_string_prefix(input_string=string_to_test, prefix="Two")
        self.assertEqual(expected, result)

    def test_remove_string_suffix(self):
        string_to_test = "oneTwoThree"
        expected = "oneTwo"
        result = string_utils.remove_string_suffix(input_string=string_to_test, suffix="Three")
        self.assertEqual(expected, result)

    def test_remove_string_suffix_no_change(self):
        string_to_test = "oneTwoThree"
        expected = string_to_test
        result = string_utils.remove_string_suffix(input_string=string_to_test, suffix="Two")
        self.assertEqual(expected, result)

    def test_camel_case_to_snake_case(self):
        string_to_test = "oneTwoThree"
        expected = "one_two_three"
        result = string_utils.camel_case_to_snake_case(camel_case_string=string_to_test)
        self.assertEqual(expected, result)

    def test_camel_case_to_snake_case_no_change(self):
        string_to_test = "one_two_three"
        expected = string_to_test
        result = string_utils.camel_case_to_snake_case(camel_case_string=string_to_test)
        self.assertEqual(expected, result)

    def test_camel_case_split(self):
        string_to_test = "oneTwoThree"
        expected = ['one', 'Two', 'Three']
        result = string_utils.camel_case_split(input_string=string_to_test)
        self.assertEqual(expected, result)

    def test_string_list_to_snake_case(self):
        string_list = ['one', 'Two', 'Three']
        expected = "one_two_three"
        result = string_utils.string_list_to_snake_case(string_list=string_list)
        self.assertEqual(expected, result)

    def test_string_list_to_snake_case_separating_string(self):
        string_list = ['one', 'Two', 'Three']
        expected = "one-two-three"
        result = string_utils.string_list_to_snake_case(string_list=string_list, separating_string="-")
        self.assertEqual(expected, result)

    def test_string_list_to_snake_case_force_lowercase(self):
        string_list = ['one', 'Two', 'Three']
        expected = "one_Two_Three"
        result = string_utils.string_list_to_snake_case(string_list=string_list, force_lowercase=False)
        self.assertEqual(expected, result)

    def test_remove_numbers(self):
        input_string = "1a2b3c"
        expected = "abc"
        result = string_utils.remove_digits(input_string=input_string)
        self.assertEqual(expected, result)

    def test_remove_strings_from_string(self):
        input_string = "1a2b3c"
        to_remove_list = ["a", "c", "3"]
        expected = "12b"
        result = string_utils.remove_strings_from_string(input_string=input_string,
                                                         undesired_string_list=to_remove_list)
        self.assertEqual(expected, result)

    def test_fail(self):
        input_string = "1a2b3c"
        to_remove_list = ["a", "c", "3"]
        expected = "1f2b"
        result = string_utils.remove_strings_from_string(input_string=input_string,
                                                         undesired_string_list=to_remove_list)
        self.assertEqual(expected, result)
