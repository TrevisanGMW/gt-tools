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
from gt.utils import iterable_utils


class TestListUtils(unittest.TestCase):
    def setUp(self):
        self.mocked_dict = {'apple': 3, 'banana': 5, 'cherry': 7, 'date': 9}
        self.mocked_list = ["1", "2", "3", "a", "b", "c"]

    def test_get_list_difference(self):
        list_a = self.mocked_list
        list_b = ["1", "a"]
        expected = (['2', '3', 'b', 'c'], [])
        result = iterable_utils.get_list_difference(list_a=list_a, list_b=list_b)
        self.assertEqual(expected, result)

    def test_get_list_intersection(self):
        list_a = self.mocked_list
        list_b = ["1", "a"]
        expected = ['1', 'a']
        result = iterable_utils.get_list_intersection(list_a=list_a, list_b=list_b)
        self.assertEqual(expected, result)

    def test_get_list_missing_elements(self):
        list_a = self.mocked_list
        list_b = ["1", "a"]
        expected = ['2', '3', 'b', 'c']
        result = iterable_utils.get_list_missing_elements(expected_list=list_a, result_list=list_b)
        self.assertEqual(expected, result)

    def test_make_flat_list(self):
        list_a = ["1"]
        list_b = ["2", ["3"]]
        list_c = [[["4"]], ["5"]]
        list_d = []
        list_e = [[[[[["6"]]]]]]
        expected = ["1", "2", "3", "4", "5", "6"]
        result = iterable_utils.make_flat_list(list_a, list_b, list_c, list_d, list_e)
        self.assertEqual(expected, result)

    def test_get_list_missing_elements_two(self):
        list_a = ["1", "2", "a", "b"]
        list_b = ["1", "a"]
        expected = ['2', 'b']
        result = iterable_utils.get_list_missing_elements(expected_list=list_a, result_list=list_b)
        self.assertEqual(expected, result)

    def test_next_item(self):
        next_item = iterable_utils.get_next_dict_item(self.mocked_dict, 'banana')
        self.assertEqual(next_item, ('cherry', 7))

    def test_no_next_item(self):
        next_item = iterable_utils.get_next_dict_item(self.mocked_dict, 'date')
        self.assertIsNone(next_item)

    def test_cycle_enabled(self):
        next_item = iterable_utils.get_next_dict_item(self.mocked_dict, 'date', cycle=True)
        self.assertEqual(next_item, ('apple', 3))

    def test_cycle_disabled(self):
        next_item = iterable_utils.get_next_dict_item(self.mocked_dict, 'date', cycle=False)
        self.assertIsNone(next_item)

    def test_next_item_last_key(self):
        next_item = iterable_utils.get_next_dict_item(self.mocked_dict, 'cherry')
        self.assertEqual(next_item, ('date', 9))

    def test_cycle_enabled_last_key(self):
        next_item = iterable_utils.get_next_dict_item(self.mocked_dict, 'cherry', cycle=True)
        self.assertEqual(next_item, ('date', 9))

    def test_cycle_disabled_last_key(self):
        next_item = iterable_utils.get_next_dict_item(self.mocked_dict, 'date', cycle=False)
        self.assertIsNone(next_item)

    def test_remove_duplicates(self):
        self.assertEqual(iterable_utils.remove_list_duplicates([1, 2, 2, 3, 4, 4, 5]), [1, 2, 3, 4, 5])
        self.assertEqual(iterable_utils.remove_list_duplicates([1, 1, 1, 1, 1]), [1])
        self.assertEqual(iterable_utils.remove_list_duplicates([5, 4, 3, 2, 1]), [1, 2, 3, 4, 5])
        self.assertEqual(iterable_utils.remove_list_duplicates([]), [])

    def test_remove_duplicates_ordered(self):
        self.assertEqual(iterable_utils.remove_list_duplicates_ordered([1, 2, 2, 3, 4, 4, 5]), [1, 2, 3, 4, 5])
        self.assertEqual(iterable_utils.remove_list_duplicates_ordered([1, 1, 1, 1, 1]), [1])
        self.assertEqual(iterable_utils.remove_list_duplicates_ordered([5, 4, 3, 2, 1]), [5, 4, 3, 2, 1])
        self.assertEqual(iterable_utils.remove_list_duplicates_ordered([]), [])

    def test_identical_keys(self):
        dict1 = {'a': 1, 'b': 2, 'c': 3}
        dict2 = {'c': 3, 'a': 1, 'b': 2}
        expected = True
        result = iterable_utils.compare_identical_dict_keys(dict1, dict2)
        self.assertEqual(expected, result)

    def test_different_keys(self):
        dict1 = {'a': 1, 'b': 2}
        dict2 = {'c': 3, 'd': 4}
        expected = False
        result = iterable_utils.compare_identical_dict_keys(dict1, dict2)
        self.assertEqual(expected, result)

    def test_empty_dicts(self):
        dict1 = {}
        dict2 = {}
        expected = True
        result = iterable_utils.compare_identical_dict_keys(dict1, dict2)
        self.assertEqual(expected, result)

    def test_one_empty_dict(self):
        dict1 = {'a': 1, 'b': 2}
        dict2 = {}
        expected = False
        result1 = iterable_utils.compare_identical_dict_keys(dict1, dict2)
        result2 = iterable_utils.compare_identical_dict_keys(dict2, dict1)
        self.assertEqual(expected, result1)
        self.assertEqual(expected, result2)

    def test_identical_dicts(self):
        dict1 = {'a': 1, 'b': 'hello', 'c': [1, 2, 3]}
        dict2 = {'a': 2, 'b': 'world', 'c': [4, 5, 6]}
        expected = True
        result = iterable_utils.compare_identical_dict_values_types(dict1, dict2)
        self.assertEqual(expected, result)

    def test_different_types(self):
        dict1 = {'a': 1, 'b': 'hello'}
        dict2 = {'a': 'string', 'b': 123}
        expected = False
        result = iterable_utils.compare_identical_dict_values_types(dict1, dict2)
        self.assertEqual(expected, result)

    def test_missing_key(self):
        dict1 = {'a': 1, 'b': 'hello'}
        dict2 = {'a': 1, 'c': 'world'}
        expected = False
        result = iterable_utils.compare_identical_dict_values_types(dict1, dict2)
        self.assertEqual(expected, result)

    def test_round_numbers_in_list_integers(self):
        input_list = [1, 2, 3]
        expected_result = [1, 2, 3]
        result = iterable_utils.round_numbers_in_list(input_list, num_digits=0)
        self.assertEqual(result, expected_result)

    def test_round_numbers_in_list_floats(self):
        input_list = [1.2345, 2.6789, 3.0]
        expected_result = [1, 3, 3]
        result = iterable_utils.round_numbers_in_list(input_list, num_digits=0)
        self.assertEqual(result, expected_result)

    def test_round_numbers_in_list_to_2_digits(self):
        input_list = [1.2345, 2.6789, 3.0]
        expected_result = [1.23, 2.68, 3.0]
        result = iterable_utils.round_numbers_in_list(input_list, num_digits=2)
        self.assertEqual(result, expected_result)

    def test_round_numbers_in_list_ignore_non_numeric_values(self):
        input_list = [1, 'two', 3.5, 'four']
        expected_result = [1, 'two', 4, 'four']
        result = iterable_utils.round_numbers_in_list(input_list, num_digits=0)
        self.assertEqual(result, expected_result)

    def test_get_highest_int_from_str_list(self):
        expected = 987
        result = iterable_utils.get_highest_int_from_str_list(["proxy123", "proxy456", "proxy987"])
        self.assertEqual(expected, result)

        expected = 3
        result = iterable_utils.get_highest_int_from_str_list(["no_match1", "no_match2", "no_match3"])
        self.assertEqual(expected, result)

        # Test when the list is empty
        expected = 0
        result = iterable_utils.get_highest_int_from_str_list([])
        self.assertEqual(expected, result)

        # Test when the list does not contain numbers
        expected = 0
        result = iterable_utils.get_highest_int_from_str_list(["hello", "world", ""])
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_default_formatting(self):
        input_dict = {'a': 1, 'b': {'c': 2, 'd': {'e': 3}}}
        expected = "{\n 'a': 1, 'b': {'c': 2, 'd': {'e': 3}}\n}"
        result = iterable_utils.dict_as_formatted_str(input_dict)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_custom_formatting(self):
        input_dict = {'x': [1, 2, 3], 'y': {'z': 'hello'}}
        expected = "{\n  'x': [1, 2, 3],\n  'y': {'z': 'hello'}\n}"
        result = iterable_utils.dict_as_formatted_str(input_dict, indent=2, width=30,
                                                      format_braces=True, sort_dicts=False)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_sort_dicts(self):
        input_dict = {'b': 2, 'a': 1, 'c': {'z': 26, 'y': 25}}
        expected = "{\n 'a': 1,\n 'b': 2,\n 'c': {'y': 25, 'z': 26}\n}"
        result = iterable_utils.dict_as_formatted_str(input_dict, sort_dicts=True, width=30)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_custom_depth(self):
        input_dict = {'a': {'b': {'c': {'d': 42}}}}
        expected = "{\n 'a': {'b': {...}}\n}"
        result = iterable_utils.dict_as_formatted_str(input_dict, depth=2)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_no_format_braces(self):
        input_dict = {'a': 1, 'b': {'c': 2}}
        expected = "{'a': 1, 'b': {'c': 2}}"
        result = iterable_utils.dict_as_formatted_str(input_dict, format_braces=False)
        self.assertEqual(expected, result)

    def test_dict_as_formatted_str_no_format_braces_on_key_per_line(self):
        input_dict = {'a': 1, 'b': {'c': 2}}
        expected = "{'a': 1,\n 'b': {'c': 2}}"
        result = iterable_utils.dict_as_formatted_str(input_dict,
                                                      format_braces=False,
                                                      one_key_per_line=True)
        self.assertEqual(expected, result)
