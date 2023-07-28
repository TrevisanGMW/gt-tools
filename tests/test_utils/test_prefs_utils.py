import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from tests import maya_test_tools
from gt.utils import prefs_utils


class TestPrefsUtils(unittest.TestCase):
    def setUp(self):
        self.mocked_str = "mocked_data"
        self.mocked_dict = {"mocked_key_a": "mocked_value_a",
                            "mocked_key_b": "mocked_value_b"}
        self.temp_dir = maya_test_tools.generate_test_temp_dir()
        self.prefs = prefs_utils.Prefs(prefs_name="mock_prefs", location_dir=self.temp_dir)

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    def test_set_and_get_float(self):
        self.prefs = prefs_utils.Prefs("mock_prefs")
        self.prefs.set_float('pi', 3.14159)
        self.assertEqual(self.prefs.get_float('pi'), 3.14159)
        self.assertEqual(self.prefs.get_float('not_found', 42.0), 42.0)

    def test_set_and_get_int(self):
        self.prefs.set_int('age', 25)
        self.assertEqual(self.prefs.get_int('age'), 25)
        self.assertEqual(self.prefs.get_int('not_found', 0), 0)

    def test_set_and_get_string(self):
        self.prefs.set_string('name', 'John Doe')
        self.assertEqual(self.prefs.get_string('name'), 'John Doe')
        self.assertEqual(self.prefs.get_string('not_found', 'Unknown'), 'Unknown')

    def test_delete_key(self):
        self.prefs.set_float('pi', 3.14159)
        self.prefs.delete_key('pi')
        self.assertFalse(self.prefs.has_key('pi'))

    def test_delete_all(self):
        self.prefs.set_float('pi', 3.14159)
        self.prefs.set_int('age', 25)
        self.prefs.set_string('name', 'John Doe')

        self.prefs.delete_all()
        self.assertFalse(self.prefs.has_key('pi'))
        self.assertFalse(self.prefs.has_key('age'))
        self.assertFalse(self.prefs.has_key('name'))

    def test_get_raw_json(self):
        self.prefs.set_float('pi', 3.14159)
        self.prefs.set_int('age', 25)
        self.prefs.set_string('name', 'John Doe')

        raw_json_data = self.prefs.get_raw_json()
        expected_json = {
            'pi': 3.14159,
            'age': 25,
            'name': 'John Doe'
        }
        self.assertEqual(raw_json_data, expected_json)

    def test_purge_prefs_folder(self):
        self.assertTrue(os.path.exists(self.temp_dir))
        self.prefs.purge_preferences_dir(purge_preferences=True)
        self.assertFalse(os.path.exists(self.temp_dir))
