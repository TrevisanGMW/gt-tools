import unittest
import logging
import sys
import os
import tempfile

# Logging Setup
from unittest.mock import MagicMock, patch

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tests import maya_test_tools
from gt.core import prefs as core_prefs


class TestPrefsCore(unittest.TestCase):
    def setUp(self):
        self.mocked_str = "mocked_data"
        self.mocked_dict = {"mocked_key_a": "mocked_value_a",
                            "mocked_key_b": "mocked_value_b"}
        self.temp_dir = maya_test_tools.generate_test_temp_dir()
        self.prefs = core_prefs.Prefs(prefs_name="mock_prefs", location_dir=self.temp_dir)

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    @patch('gt.core.prefs.get_maya_preferences_dir')
    def test_get_prefs_dir(self, mocked_get_prefs_dir):
        mocked_get_prefs_dir.return_value = "mocked_path"

        # Patch PACKAGE_NAME inside the core_prefs module where it is being used
        with patch.object(core_prefs, 'PACKAGE_NAME', 'mocked_package_name', create=True):
            result = core_prefs.get_prefs_dir()
            expected = os.path.join("mocked_path", "mocked_package_name", core_prefs.PACKAGE_PREFS_DIR)
            self.assertEqual(expected, result)

    def test_set_and_get_float(self):
        self.prefs = core_prefs.Prefs("mock_prefs")
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
        package_prefs = core_prefs.PackagePrefs()
        file_name = package_prefs.file_name
        result = file_name.endswith(f"{core_prefs.PACKAGE_GLOBAL_PREFS}.{core_prefs.PACKAGE_PREFS_EXT}")
        expected = True
        self.assertTrue(expected, result)

    def test_set_user_files_sub_folder(self):
        self.prefs.set_user_files_sub_folder('new_sub_folder')
        self.assertEqual(self.prefs.sub_folder, 'new_sub_folder')

    def test_get_prefs_name(self):
        result = self.prefs.get_prefs_name()
        expected = "mock_prefs"
        self.assertEqual(expected, result)
        new_prefs = core_prefs.Prefs("mocked_name")
        result = new_prefs.get_prefs_name()
        expected = "mocked_name"
        self.assertEqual(expected, result)

    def test_get_user_files_dir_path(self):
        result = self.prefs.get_user_files_dir_path()
        expected = os.path.join(self.temp_dir, self.prefs.get_prefs_name())
        self.assertEqual(expected, result)
        self.prefs.set_user_files_sub_folder('new_sub_folder')
        result = self.prefs.get_user_files_dir_path()
        expected = os.path.join(self.temp_dir, 'new_sub_folder')
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

    def test_get_all_user_files(self):
        self.prefs.write_user_file(file_name="user_file.txt", content="mocked_content", is_json=False)
        result = self.prefs.get_all_user_files(verbose=False)
        expected = {"user_file.txt": os.path.join(self.temp_dir, 'mock_prefs', 'user_file.txt')}
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

    def test_init_custom_cache_dir(self):
        custom_cache_dir = os.path.join(self.temp_dir, "mocked_cache")
        os.makedirs(custom_cache_dir)
        cache = core_prefs.PackageCache(custom_cache_dir=custom_cache_dir)
        cache.get_cache_dir()
        self.assertEqual(custom_cache_dir, cache.cache_dir)
        self.assertTrue(os.path.exists(cache.cache_dir))

    def test_clear_cache(self):
        custom_cache_dir = os.path.join(self.temp_dir, "mocked_cache")
        os.makedirs(custom_cache_dir)
        cache = core_prefs.PackageCache(custom_cache_dir=custom_cache_dir)
        test_file = os.path.join(custom_cache_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        cache.add_path_to_cache_list(test_file)
        cache.clear_cache()
        self.assertFalse(os.path.exists(test_file))
        self.assertFalse(os.path.exists(cache.cache_dir))

    def test_clear_purge_cache_dir(self):
        custom_cache_dir = os.path.join(self.temp_dir, "mocked_cache")
        os.makedirs(custom_cache_dir)
        cache = core_prefs.PackageCache(custom_cache_dir=custom_cache_dir)
        test_file = os.path.join(custom_cache_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        cache.purge_cache_dir()
        self.assertFalse(os.path.exists(test_file))
        self.assertFalse(os.path.exists(cache.cache_dir))

    def test_get_cache_dir(self):
        cache = core_prefs.PackageCache(custom_cache_dir=self.temp_dir)
        self.assertEqual(cache.get_cache_dir(), self.temp_dir)
        self.assertTrue(os.path.exists(self.temp_dir))

    def test_add_path_list_single_path(self):
        cache = core_prefs.PackageCache(self.temp_dir)
        test_file = os.path.join(self.temp_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        cache.add_path_to_cache_list(test_file)
        self.assertEqual(cache.cache_paths, [test_file])

    def test_get_cache_paths_list(self):
        cache = core_prefs.PackageCache(self.temp_dir)
        test_file = os.path.join(self.temp_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        cache.add_path_to_cache_list(test_file)
        self.assertEqual(cache.get_cache_paths_list(), [test_file])

    def test_add_path_list_multiple_paths(self):
        cache = core_prefs.PackageCache(custom_cache_dir=self.temp_dir)
        test_file1 = os.path.join(self.temp_dir, 'test_file1.txt')
        test_file2 = os.path.join(self.temp_dir, 'test_file2.txt')
        with open(test_file1, 'w') as f:
            f.write('Test content')
        with open(test_file2, 'w') as f:
            f.write('Test content')
        cache.add_path_to_cache_list([test_file1, test_file2])
        self.assertEqual(cache.cache_paths, [test_file1, test_file2])


class TestRecentProjects(unittest.TestCase):
    def setUp(self):
        self.preferences = {}
        self.prefs = MagicMock()
        self.prefs.get_raw_preferences.return_value = self.preferences
        self.recent_projects = core_prefs.RecentProjects(self.prefs, "recent_projects", max_count=5)

    def test_add_path_keeps_newest_five(self):
        paths = [os.path.join(tempfile.gettempdir(), f"project_{index}.rig") for index in range(6)]

        for file_path in paths:
            self.recent_projects.add_path(file_path)

        expected = [os.path.normpath(os.path.abspath(path)) for path in reversed(paths[1:])]
        self.assertEqual(expected, self.recent_projects.get_paths())

    def test_add_path_moves_duplicate_to_front(self):
        first_path = os.path.join(tempfile.gettempdir(), "first.rig")
        second_path = os.path.join(tempfile.gettempdir(), "second.rig")
        self.recent_projects.add_path(first_path)
        self.recent_projects.add_path(second_path)

        result = self.recent_projects.add_path(first_path)

        expected = [os.path.normpath(os.path.abspath(first_path)),
                    os.path.normpath(os.path.abspath(second_path))]
        self.assertEqual(expected, result)

    def test_get_paths_ignores_invalid_values_and_duplicates(self):
        project_path = os.path.join(tempfile.gettempdir(), "project.rig")
        self.preferences["recent_projects"] = [project_path, None, "", project_path]

        result = self.recent_projects.get_paths()

        expected = [os.path.normpath(os.path.abspath(project_path))]
        self.assertEqual(expected, result)

    def test_remove_path_saves_updated_preferences(self):
        project_path = os.path.join(tempfile.gettempdir(), "project.rig")
        self.recent_projects.add_path(project_path)
        self.prefs.save.reset_mock()

        result = self.recent_projects.remove_path(project_path)

        self.assertEqual([], result)
        self.assertEqual([], self.preferences["recent_projects"])
        self.prefs.save.assert_called_once_with()

    def test_clear_saves_empty_list(self):
        self.preferences["recent_projects"] = ["project.rig"]

        self.recent_projects.clear()

        self.assertEqual([], self.preferences["recent_projects"])
        self.prefs.save.assert_called_once_with()
