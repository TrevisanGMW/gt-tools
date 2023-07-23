import unittest
import logging
import sys
import os

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
from gt.tools.sample_tool import sample_model


class TestSampleToolModel(unittest.TestCase):
    def setUp(self):
        self.model = sample_model.SampleToolModel()

    def test_add_item(self):
        # Test if an item is added correctly
        self.model.add_item("Item 1")
        self.assertEqual(["Item 1"], self.model.get_items())

        # Test if multiple items are added correctly
        self.model.add_item("Item 2")
        self.model.add_item("Item 3")
        self.assertEqual(["Item 1", "Item 2", "Item 3"], self.model.get_items())

    def test_remove_item(self):
        # Test if removing an item at a valid index works correctly
        self.model.add_item("Item 1")
        self.model.add_item("Item 2")
        self.model.add_item("Item 3")

        self.model.remove_item(1)
        self.assertEqual(["Item 1", "Item 3"], self.model.get_items())

    def test_get_items(self):
        # Test if the get_items method returns an empty list initially
        self.assertEqual([], self.model.get_items())

        # Test if the get_items method returns the correct list of items
        self.model.add_item("Item 1")
        self.model.add_item("Item 2")
        self.model.add_item("Item 3")

        self.assertEqual(["Item 1", "Item 2", "Item 3"], self.model.get_items())

