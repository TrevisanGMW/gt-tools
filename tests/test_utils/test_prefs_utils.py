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

    def test_set_and_get_bool(self):
        self.prefs.set_bool('exists', True)
        self.assertEqual(self.prefs.get_bool('exists'), True)
        self.assertEqual(self.prefs.get_bool('not_found', 'Unknown'), 'Unknown')

    def test_delete_key(self):
        self.prefs.set_float('pi', 3.14159)
        self.prefs.delete_key('pi')
        self.assertFalse(self.prefs.is_key_available('pi'))

    def test_delete_all(self):
        self.prefs.set_float('pi', 3.14159)
        self.prefs.set_int('age', 25)
        self.prefs.set_string('name', 'John Doe')

        self.prefs.delete_all()
        self.assertFalse(self.prefs.is_key_available('pi'))
        self.assertFalse(self.prefs.is_key_available('age'))
        self.assertFalse(self.prefs.is_key_available('name'))

    def test_get_raw_preferences(self):
        self.prefs.set_float('pi', 3.14159)
        self.prefs.set_int('age', 25)
        self.prefs.set_string('name', 'John Doe')

        raw_json_data = self.prefs.get_raw_preferences()
        expected_json = {
            'pi': 3.14159,
            'age': 25,
            'name': 'John Doe'
        }
        self.assertEqual(raw_json_data, expected_json)

    def test_set_raw_preferences(self):
        expected_json = {
            'pi': 3.14159,
            'age': 25,
            'name': 'John Doe'
        }
        self.prefs.set_raw_preferences(pref_dict=expected_json)
        raw_dict_data = self.prefs.get_raw_preferences()
        self.assertEqual(raw_dict_data, expected_json)

    def test_purge_prefs_folder(self):
        self.assertTrue(os.path.exists(self.temp_dir))
        self.prefs.purge_preferences_dir(purge_preferences=True)
        self.assertFalse(os.path.exists(self.temp_dir))

    def test_package_prefs(self):
        package_prefs = prefs_utils.PackagePrefs()
        file_name = package_prefs.file_name
        result = file_name.endswith(f"{prefs_utils.PACKAGE_GLOBAL_PREFS}.{prefs_utils.PACKAGE_PREFS_EXT}")
        expected = True
        self.assertTrue(expected, result)

    def test_set_user_files_sub_folder(self):
        self.prefs.set_user_files_sub_folder('new_sub_folder')
        self.assertEqual(self.prefs.sub_folder, 'new_sub_folder')

    def test_set_user_files_sub_folder_unchanged(self):
        self.assertEqual(self.prefs.sub_folder, 'mock_prefs')

    def test_set_user_files_sub_folder_created(self):
        self.prefs.write_user_file(file_name="user_file.txt", content="mocked_content", is_json=False)
        custom_file = os.path.join(self.temp_dir, 'mock_prefs')
        is_dir = os.path.isdir(custom_file)
        self.assertTrue(is_dir)

    def test_write_user_file(self):
        self.prefs.write_user_file(file_name="user_file.txt", content="mocked_content", is_json=False)
        custom_file = os.path.join(self.temp_dir, 'mock_prefs', 'user_file.txt')
        with open(custom_file, "r") as data_file:
            result = data_file.read()
        expected = 'mocked_content'
        self.assertEqual(expected, result)

    def test_get_user_file(self):
        self.prefs.write_user_file(file_name="user_file.txt", content="mocked_content", is_json=False)
        result = self.prefs.get_user_file(file_name='user_file.txt')
        expected = os.path.join(self.temp_dir, 'mock_prefs', 'user_file.txt')
        self.assertEqual(expected, result)

    def test_get_user_file_missing_sub_folder(self):
        result = self.prefs.get_user_file(file_name='mocked_missing_file.ext', verbose=False)
        expected = None
        self.assertEqual(expected, result)

    def test_get_user_file_missing_file(self):
        self.prefs.write_user_file(file_name="user_file.txt", content="mocked_content", is_json=False)
        result = self.prefs.get_user_file(file_name='mocked_missing_file.ext', verbose=False)
        expected = None
        self.assertEqual(expected, result)
