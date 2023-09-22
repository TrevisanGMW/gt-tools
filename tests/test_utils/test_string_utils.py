import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.utils import string_utils


class TestStringUtils(unittest.TestCase):
    def test_remove_string_prefix(self):
        string_to_test = "oneTwoThree"
        expected = "TwoThree"
        result = string_utils.remove_prefix(input_string=string_to_test, prefix="one")
        self.assertEqual(expected, result)

    def test_remove_string_prefix_no_change(self):
        string_to_test = "oneTwoThree"
        expected = string_to_test
        result = string_utils.remove_prefix(input_string=string_to_test, prefix="Two")
        self.assertEqual(expected, result)

    def test_remove_string_suffix(self):
        string_to_test = "oneTwoThree"
        expected = "oneTwo"
        result = string_utils.remove_suffix(input_string=string_to_test, suffix="Three")
        self.assertEqual(expected, result)

    def test_remove_string_suffix_no_change(self):
        string_to_test = "oneTwoThree"
        expected = string_to_test
        result = string_utils.remove_suffix(input_string=string_to_test, suffix="Two")
        self.assertEqual(expected, result)

    def test_camel_case_to_snake_case(self):
        string_to_test = "oneTwoThree"
        expected = "one_two_three"
        result = string_utils.camel_to_snake(camel_case_string=string_to_test)
        self.assertEqual(expected, result)

    def test_camel_case_to_snake_case_no_change(self):
        string_to_test = "one_two_three"
        expected = string_to_test
        result = string_utils.camel_to_snake(camel_case_string=string_to_test)
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

    def test_remove_strings(self):
        # Test removing strings from the input
        input_string = "left_elbow_ctrl"
        undesired_string_list = ["left", "ctrl"]
        result = string_utils.remove_strings_from_string(input_string, undesired_string_list)
        expected = "_elbow_"
        self.assertEqual(expected, result)

    def test_remove_prefix_only(self):
        # Test removing prefix strings only
        input_string = "one_two"
        undesired_string_list = ["one"]
        result = string_utils.remove_strings_from_string(input_string, undesired_string_list, only_prefix=True)
        expected = "_two"
        self.assertEqual(expected, result)

    def test_remove_suffix_only(self):
        # Test removing suffix strings only
        input_string = "one_two"
        undesired_string_list = ["two"]
        result = string_utils.remove_strings_from_string(input_string, undesired_string_list, only_suffix=True)
        expected = "one_"
        self.assertEqual(expected, result)

    def test_remove_prefix_and_suffix_raises_error(self):
        # Test that an error is raised when both only_prefix and only_suffix are True
        input_string = "test_string"
        undesired_string_list = ["test"]
        with self.assertRaises(ValueError):
            string_utils.remove_strings_from_string(input_string, undesired_string_list,
                                                    only_prefix=True, only_suffix=True)

    def test_no_strings_to_remove(self):
        # Test when there are no strings to remove
        input_string = "hello_world"
        undesired_string_list = ["not_present", "something_else"]
        result = string_utils.remove_strings_from_string(input_string, undesired_string_list)
        expected = "hello_world"
        self.assertEqual(expected, result)

    def test_extract_digits_no_digits(self):
        input_string = "No digits here!"
        self.assertEqual(string_utils.extract_digits(input_string), "")

    def test_extract_digits_mixed_characters(self):
        input_string = "It costs $20.99 only."
        self.assertEqual(string_utils.extract_digits(input_string), "2099")

    def test_extract_digits_special_characters(self):
        input_string = "Password: $ecr3t!!123"
        self.assertEqual(string_utils.extract_digits(input_string), "3123")

    def test_extract_digits_empty_string(self):
        input_string = ""
        self.assertEqual(string_utils.extract_digits(input_string), "")

    def test_extract_digits_only_digits(self):
        input_string = "9876543210"
        self.assertEqual(string_utils.extract_digits(input_string), "9876543210")

    def test_single_word(self):
        expected = "hello"
        result = string_utils.snake_to_camel("hello")
        self.assertEqual(expected, result)

    def test_two_words(self):
        expected = "helloWorld"
        result = string_utils.snake_to_camel("hello_world")
        self.assertEqual(expected, result)

    def test_multiple_words(self):
        expected = "myVariableName"
        result = string_utils.snake_to_camel("my_variable_name")
        self.assertEqual(expected, result)

    def test_long_string(self):
        expected = "aLongSnakeCaseStringWithManyWords"
        result = string_utils.snake_to_camel("a_long_snake_case_string_with_many_words")
        self.assertEqual(expected, result)

    def test_empty_string(self):
        expected = ""
        result = string_utils.snake_to_camel("")
        self.assertEqual(expected, result)

    def test_single_letter_words(self):
        expected = "aBCDEF"
        result = string_utils.snake_to_camel("a_b_c_d_e_f")
        self.assertEqual(expected, result)

    def test_numbers_in_string(self):
        expected = "version210"
        result = string_utils.snake_to_camel("version_2_1_0")
        self.assertEqual(expected, result)
        