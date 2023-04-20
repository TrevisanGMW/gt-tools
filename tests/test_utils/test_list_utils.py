import os
import sys
import logging
import tempfile
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_list_utils")
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from utils import list_utils


class TestListUtils(unittest.TestCase):
    def test_get_list_difference(self):
        list_a = ["1", "2", "3", "a", "b", "c"]
        list_b = ["1", "a"]
        expected = (['2', '3', 'b', 'c'], [])
        result = list_utils.get_list_difference(list_a=list_a, list_b=list_b)
        self.assertEqual(expected, result)

    def test_get_list_intersection(self):
        list_a = ["1", "2", "3", "a", "b", "c"]
        list_b = ["1", "a"]
        expected = ['1', 'a']
        result = list_utils.get_list_intersection(list_a=list_a, list_b=list_b)
        self.assertEqual(expected, result)

    def test_get_list_missing_elements(self):
        list_a = ["1", "2", "3", "a", "b", "c"]
        list_b = ["1", "a"]
        expected = ['2', '3', 'b', 'c']
        result = list_utils.get_list_missing_elements(expected_list=list_a, result_list=list_b)
        self.assertEqual(expected, result)

    def test_make_flat_list(self):
        list_a = ["1"]
        list_b = ["2", ["3"]]
        list_c = [[["4"]], ["5"]]
        list_d = []
        list_e = [[[[[["6"]]]]]]
        expected = ["1", "2", "3", "4", "5", "6"]
        result = list_utils.make_flat_list(list_a, list_b, list_c, list_d, list_e)
        self.assertEqual(expected, result)

    def test_get_list_missing_elements(self):
        list_a = ["1", 2, "a", "b"]
        list_b = ["1", "a"]
        expected = ['2', '3', 'b', 'c']
        result = list_utils.remove_numbers()
        self.assertEqual(expected, result)
