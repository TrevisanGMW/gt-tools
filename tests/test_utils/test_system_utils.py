import os
import sys
import pathlib
import logging
import unittest
import tempfile
from unittest.mock import patch

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
from utils import system_utils


class TestSystemUtils(unittest.TestCase):
    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    def test_get_system(self):
        result = system_utils.get_system()
        expected = sys.platform
        self.assertEqual(expected, result)

    @patch('sys.platform', 'mocked_platform')
    def test_get_system_two(self):
        result = system_utils.get_system()
        expected = "mocked_platform"
        self.assertEqual(expected, result)

    def test_get_temp_folder(self):
        result = system_utils.get_temp_folder()
        expected = tempfile.gettempdir()
        self.assertEqual(expected, result)

    @patch('utils.system_utils.get_system')
    def test_get_home_dir(self, mock_get_system):
        mock_get_system.return_value = "mocked_value"
        result = system_utils.get_home_dir()
        expected = pathlib.Path.home()  # Exactly what the function returns
        self.assertEqual(expected, result)

    @patch('utils.system_utils.get_home_dir')
    def test_get_desktop_path(self, mock_get_home_dir):
        mock_get_home_dir.return_value = "path"
        result = system_utils.get_desktop_path()
        expected = os.path.join("path", "Desktop")
        self.assertEqual(expected, result)

    def test_get_maya_install_dir_win32(self):
        result = system_utils.get_maya_install_dir(system_utils.OS_WINDOWS)
        expected = f"C:\\Program Files\\Autodesk\\"
        self.assertEqual(expected, result)

    def test_get_maya_install_dir_mac(self):
        result = system_utils.get_maya_install_dir(system_utils.OS_MAC)
        expected = f"/Applications/Autodesk/"
        self.assertEqual(expected, result)

    def test_get_maya_install_dir_key_error(self):
        with self.assertRaises(KeyError):
            system_utils.get_maya_install_dir("random_missing_key")

    def test_get_maya_path_win32(self):
        result = system_utils.get_maya_path(system=system_utils.OS_WINDOWS,
                                            version='2024',
                                            get_maya_python=False)
        expected = os.path.normpath(f'C:\\Program Files\\Autodesk\\Maya2024\\bin\\maya.exe')
        self.assertEqual(expected, result)

    def test_get_maya_path_mac(self):
        result = system_utils.get_maya_path(system=system_utils.OS_MAC,
                                            version='2023',
                                            get_maya_python=False)
        expected = os.path.normpath(f"/Applications/Autodesk//maya2023/Maya.app/Contents/bin/maya")
        self.assertEqual(expected, result)

    def test_get_maya_path_key_error(self):
        with self.assertRaises(KeyError):
            system_utils.get_maya_path(system="random_missing_key",
                                       version='2024',
                                       get_maya_python=False)

    @patch('subprocess.run')
    def test_open_file_dir_win32(self, mock_subprocess_run):
        with patch('utils.system_utils.get_system') as mock_get_system:
            temp_folder = tempfile.gettempdir()
            mock_get_system.return_value = system_utils.OS_WINDOWS
            system_utils.open_file_dir(temp_folder)
            mock_get_system.assert_called_once()  # Make sure get system is called
            mock_subprocess_run.assert_called_once()  # Make sure subprocess.run is called
            result = mock_subprocess_run.call_args.args[0]
            expected = ['C:\\WINDOWS\\explorer.exe', temp_folder]
            self.assertEqual(expected, result)

    @patch('subprocess.call')
    def test_open_file_dir_mac(self, mock_subprocess_call):
        with patch('utils.system_utils.get_system') as mock_get_system:
            temp_folder = tempfile.gettempdir()
            mock_get_system.return_value = system_utils.OS_MAC
            system_utils.open_file_dir(temp_folder)
            mock_get_system.assert_called_once()  # Make sure get system is called
            mock_subprocess_call.assert_called_once()  # Make sure subprocess.run is called
            result = mock_subprocess_call.call_args.args[0]
            expected = ["open", "-R", temp_folder]
            self.assertEqual(expected, result)

    def test_get_maya_settings_dir_win32(self):
        result = system_utils.get_maya_settings_dir(system=system_utils.OS_WINDOWS)
        generated_path = os.path.join(os.path.expanduser('~'), "Documents", "maya")
        expected = os.path.normpath(generated_path)
        self.assertEqual(expected, result)

    def test_get_maya_settings_dir_mac(self):
        result = system_utils.get_maya_settings_dir(system=system_utils.OS_MAC)
        generated_path = os.path.join(os.path.expanduser('~'), "Library", "Preferences", "Autodesk", "maya")
        expected = os.path.normpath(generated_path)
        self.assertEqual(expected, result)

    @patch('utils.system_utils.get_maya_settings_dir')
    def test_get_available_maya_preferences(self, mock_get_maya_settings_dir):
        test_temp_dir = maya_test_tools.create_test_temp_dir()
        mock_get_maya_settings_dir.return_value = test_temp_dir
        result = {}
        try:
            for folder in ["2020", "2024", "folder", "scripts", "2023backup"]:
                test_obj = os.path.join(test_temp_dir, folder)
                if not os.path.exists(test_obj):
                    os.mkdir(test_obj)
            result = system_utils.get_available_maya_preferences_dirs(use_maya_commands=False)
        except Exception as e:
            logger.warning(f"Failed to test maya preferences: Issue:{e}")
        mock_get_maya_settings_dir.assert_called_once()

        expected = {"2020": os.path.join(test_temp_dir, "2020"),
                    "2024": os.path.join(test_temp_dir, "2024")}
        self.assertEqual(expected, result)

    @patch('utils.system_utils.get_maya_install_dir')
    def test_get_available_maya_install_dirs(self, mock_get_maya_install_dir):
        test_temp_dir = maya_test_tools.create_test_temp_dir()
        mock_get_maya_install_dir.return_value = test_temp_dir
        result = {}
        try:
            for folder in ["Maya2020", "maya2024", "folder", "scripts", "2023backup", "maya2023backup"]:
                test_obj = os.path.join(test_temp_dir, folder)
                if not os.path.exists(test_obj):
                    os.mkdir(test_obj)
            result = system_utils.get_available_maya_install_dirs()
        except Exception as e:
            logger.warning(f"Failed to test maya preferences: Issue:{e}")
        mock_get_maya_install_dir.assert_called_once()

        expected = {"2020": os.path.join(test_temp_dir, "Maya2020"),
                    "2024": os.path.join(test_temp_dir, "maya2024")}
        self.assertEqual(expected, result)
