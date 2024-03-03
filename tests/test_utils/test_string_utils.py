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

    def test_extract_digits_no_digits(self):
        input_string = "No digits here!"
        expected = ""
        result = string_utils.extract_digits(input_string=input_string,
                                             can_be_negative=False)
        self.assertEqual(expected, result)

    def test_extract_digits_mixed_characters(self):
        input_string = "It costs $20.99 only."
        expected = "2099"
        result = string_utils.extract_digits(input_string=input_string,
                                             can_be_negative=False)
        self.assertEqual(expected, result)

    def test_extract_digits_special_characters(self):
        input_string = "Password: $ecr3t!!123"
        expected = "3123"
        result = string_utils.extract_digits(input_string=input_string,
                                             can_be_negative=False)
        self.assertEqual(expected, result)

    def test_extract_digits_empty_string(self):
        input_string = ""
        expected = ""
        result = string_utils.extract_digits(input_string=input_string,
                                             can_be_negative=False)
        self.assertEqual(expected, result)

    def test_extract_digits_only_digits(self):
        input_string = "9876543210"
        expected = "9876543210"
        result = string_utils.extract_digits(input_string=input_string,
                                             can_be_negative=False)
        self.assertEqual(expected, result)

    def test_extract_digits_negative_num(self):
        input_string = "a string -150"
        expected = "-150"
        result = string_utils.extract_digits(input_string=input_string,
                                             can_be_negative=True)
        self.assertEqual(expected, result)

    def test_extract_digits_as_int(self):
        expected = 123
        result = string_utils.extract_digits_as_int("abc123def",
                                                    can_be_negative=False,
                                                    only_first_match=True,
                                                    default=0)
        self.assertEqual(expected, result)

    def test_extract_digits_as_int_no_digits(self):
        expected = 0
        result = string_utils.extract_digits_as_int("no_digits_here",
                                                    can_be_negative=False,
                                                    only_first_match=True,
                                                    default=0)
        self.assertEqual(expected, result)

    def test_extract_digits_as_int_separated_digits_first_only(self):
        expected = 1
        result = string_utils.extract_digits_as_int("1_test_2",
                                                    can_be_negative=False,
                                                    only_first_match=True,
                                                    default=0)
        self.assertEqual(expected, result)

    def test_extract_digits_as_int_separated_digits_all(self):
        expected = 123
        result = string_utils.extract_digits_as_int("1_test_2_then_3",
                                                    can_be_negative=False,
                                                    only_first_match=False,
                                                    default=0)
        self.assertEqual(expected, result)

    def test_extract_digits_as_int_alternative_default(self):
        expected = -1
        result = string_utils.extract_digits_as_int("no_digits_here",
                                                    can_be_negative=False,
                                                    only_first_match=False,
                                                    default=-1)
        self.assertEqual(expected, result)

    def test_extract_digits_as_int_negative_number_only_first_match(self):
        expected = -100
        result = string_utils.extract_digits_as_int("negative string -100",
                                                    can_be_negative=True,
                                                    only_first_match=True,
                                                    default=0)
        self.assertEqual(expected, result)

    def test_extract_digits_as_int_negative_number_all_digits(self):
        expected = -150
        result = string_utils.extract_digits_as_int("negative string -150",
                                                    can_be_negative=True,
                                                    only_first_match=False,
                                                    default=0)
        self.assertEqual(expected, result)

    def test_get_int_as_rank_first(self):
        expected = '1st'
        result = string_utils.get_int_as_rank(1)
        self.assertEqual(expected, result)

    def test_get_int_as_rank_second(self):
        expected = '2nd'
        result = string_utils.get_int_as_rank(2)
        self.assertEqual(expected, result)

    def test_get_int_as_rank_third(self):
        expected = '3rd'
        result = string_utils.get_int_as_rank(3)
        self.assertEqual(expected, result)

    def test_get_int_as_rank_4th_to_10th(self):
        for i in range(4, 11):
            with self.subTest(i=i):
                expected = f'{i}th'
                result = string_utils.get_int_as_rank(i)
                self.assertEqual(expected, result)

    def test_get_int_as_rank_11th_to_13th(self):
        for i in range(11, 14):
            with self.subTest(i=i):
                expected = f'{i}th'
                result = string_utils.get_int_as_rank(i)
                self.assertEqual(expected, result)

    def test_get_int_as_rank_14th_to_20th(self):
        for i in range(14, 21):
            with self.subTest(i=i):
                expected = f'{i}th'
                result = string_utils.get_int_as_rank(i)
                self.assertEqual(expected, result)

    def test_get_int_as_rank_21st_to_100th(self):
        for i in range(21, 101):
            with self.subTest(i=i):
                last_digit = i % 10
                suffix_dict = {1: "st", 2: "nd", 3: "rd"}
                expected_suffix = suffix_dict.get(last_digit, "th")
                expected = f'{i}{expected_suffix}'
                result = string_utils.get_int_as_rank(i)
                self.assertEqual(expected, result)

    def test_get_int_to_en_zero(self):
        expected = "zero"
        result = string_utils.get_int_as_en(0)
        self.assertEqual(expected, result)

    def test_get_int_to_en_positive_single_digit(self):
        expected = "five"
        result = string_utils.get_int_as_en(5)
        self.assertEqual(expected, result)

        expected = "nine"
        result = string_utils.get_int_as_en(9)
        self.assertEqual(expected, result)

    def test_get_int_to_en_positive_double_digit(self):
        expected = "ten"
        result = string_utils.get_int_as_en(10)
        self.assertEqual(expected, result)

        expected = "twenty-one"
        result = string_utils.get_int_as_en(21)
        self.assertEqual(expected, result)

        expected = "ninety-nine"
        result = string_utils.get_int_as_en(99)
        self.assertEqual(expected, result)

    def test_get_int_to_en_positive_hundreds(self):
        expected = "one hundred"
        result = string_utils.get_int_as_en(100)
        self.assertEqual(expected, result)

        expected = "one hundred and twenty-three"
        result = string_utils.get_int_as_en(123)
        self.assertEqual(expected, result)

        expected = "nine hundred and ninety-nine"
        result = string_utils.get_int_as_en(999)
        self.assertEqual(expected, result)

    def test_get_int_to_en_positive_thousands(self):
        expected = "one thousand"
        result = string_utils.get_int_as_en(1000)
        self.assertEqual(expected, result)

        expected = "two thousand, three hundred and forty-five"
        result = string_utils.get_int_as_en(2345)
        self.assertEqual(expected, result)

        expected = "nine thousand, nine hundred and ninety-nine"
        result = string_utils.get_int_as_en(9999)
        self.assertEqual(expected, result)

    def test_get_int_to_en_positive_millions(self):
        expected = "one million"
        result = string_utils.get_int_as_en(1000000)
        self.assertEqual(expected, result)

        expected = ("one million, two hundred and thirty-four thousand, "
                    "five hundred and sixty-seven")
        result = string_utils.get_int_as_en(1234567)
        self.assertEqual(expected, result)

        expected = ("nine million, nine hundred and ninety-nine thousand, "
                    "nine hundred and ninety-nine")
        result = string_utils.get_int_as_en(9999999)
        self.assertEqual(expected, result)

    def test_get_int_to_en_positive_billions(self):
        expected = "one billion"
        result = string_utils.get_int_as_en(1000000000)
        self.assertEqual(expected, result)

        expected = ("one billion, two hundred and thirty-four million, "
                    "five hundred and sixty-seven thousand, eight hundred and ninety")
        result = string_utils.get_int_as_en(1234567890)
        self.assertEqual(expected, result)

        expected = ("nine billion, nine hundred and ninety-nine million, "
                    "nine hundred and ninety-nine thousand, nine hundred and ninety-nine")
        result = string_utils.get_int_as_en(9999999999)
        self.assertEqual(expected, result)

    def test_get_int_to_en_positive_trillions(self):
        expected = "one trillion"
        result = string_utils.get_int_as_en(1000000000000)
        self.assertEqual(expected, result)

        expected = ("one trillion, two hundred and thirty-four billion, "
                    "five hundred and sixty-seven million, eight hundred and ninety thousand, "
                    "one hundred and twenty-three")
        result = string_utils.get_int_as_en(1234567890123)
        self.assertEqual(expected, result)

        expected = ("nine trillion, nine hundred and ninety-nine billion, "
                    "nine hundred and ninety-nine million, nine hundred and ninety-nine thousand, "
                    "nine hundred and ninety-nine")
        result = string_utils.get_int_as_en(9999999999999)
        self.assertEqual(expected, result)

    def test_get_int_to_en_negative_numbers(self):
        expected = "negative five"
        result = string_utils.get_int_as_en(-5)
        self.assertEqual(expected, result)

        expected = ("negative nine hundred and eighty-seven million, "
                    "six hundred and fifty-four thousand, three hundred and twenty-one")
        result = string_utils.get_int_as_en(-987654321)
        self.assertEqual(expected, result)

    def test_get_int_to_en_non_integer_input(self):
        with self.assertRaises(AssertionError):
            string_utils.get_int_as_en(3.5)

    def test_upper_first_char(self):
        with self.assertRaises(AssertionError):
            string_utils.get_int_as_en(3.5)

    def test_upper_first_char_with_long_string(self):
        result = string_utils.upper_first_char("hello")
        self.assertEqual(result, "Hello")

    def test_upper_first_char_with_single_character(self):
        result = string_utils.upper_first_char("h")
        self.assertEqual(result, "H")

    def test_upper_first_char_with_empty_string(self):
        result = string_utils.upper_first_char("")
        self.assertEqual(result, "")

    def test_upper_first_char_with_none_input(self):
        with self.assertRaises(ValueError):
            string_utils.upper_first_char(None)
