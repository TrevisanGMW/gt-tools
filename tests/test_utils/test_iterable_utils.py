import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Test String Utilities
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

    def test_default_keys_per_line(self):
        sample_dict = {
            'name': 'John Doe',
            'age': 30,
            'city': 'Vancouver',
            'email': 'john@example.com',
            'occupation': 'Software Engineer'
        }
        expected_result = ('{"name": "John Doe", "age": 30,\n'
                           '"city": "Vancouver", "email": "john@example.com",\n'
                           '"occupation": "Software Engineer"}')
        result = iterable_utils.format_dict_with_keys_per_line(sample_dict)
        self.assertEqual(result, expected_result)

    def test_custom_keys_per_line(self):
        sample_dict = {
            'a': 1,
            'b': 2,
            'c': 3,
            'd': 4,
            'e': 5,
        }
        expected_result = ('{'
                           '"a": 1, "b": 2,\n'
                           '"c": 3, "d": 4,\n'
                           '"e": 5}')
        result = iterable_utils.format_dict_with_keys_per_line(sample_dict, keys_per_line=2)
        self.assertEqual(result, expected_result)

    def test_single_key_per_line(self):
        sample_dict = {
            'key1': 'value1',
            'key2': 'value2',
            'key3': 'value3'
        }
        expected_result = ('{"key1": "value1",\n'
                           '"key2": "value2",\n'
                           '"key3": "value3"}')
        result = iterable_utils.format_dict_with_keys_per_line(sample_dict, keys_per_line=1)
        self.assertEqual(result, expected_result)

    def test_bracket_new_line(self):
        input_dict = {
            'key1': 'value1',
            'key2': 'value2',
        }
        expected = '{\n"key1": "value1", "key2": "value2"\n}'
        result = iterable_utils.format_dict_with_keys_per_line(input_dict, bracket_new_line=True)
        self.assertEqual(expected, result)
