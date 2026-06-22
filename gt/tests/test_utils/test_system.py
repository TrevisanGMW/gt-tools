from unittest.mock import patch, MagicMock
from contextlib import redirect_stdout
from datetime import datetime
import tempfile
import unittest
import logging
import pathlib
import sys
import io
import os

# Logging Setup
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
import gt.utils.system as utils_system
from gt.utils.system import time_profiler
import gt.tests.maya_test_tools as maya_test_tools


class TestSystemUtils(unittest.TestCase):
    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    def test_get_system(self):
        result = utils_system.get_system()
        expected = sys.platform
        self.assertEqual(expected, result)

    @patch("sys.platform", "mocked_platform")
    def test_get_system_mocked(self):
        result = utils_system.get_system()
        expected = "mocked_platform"
        self.assertEqual(expected, result)

    @patch("gt.utils.system.get_system", return_value=utils_system.OS_MAC)
    def test_is_system_macos_returns_true(self, mock_get_system):
        result = utils_system.is_system_macos()
        self.assertTrue(result)

    @patch("gt.utils.system.get_system", return_value=utils_system.OS_WINDOWS)
    def test_is_system_macos_returns_false(self, mock_get_system):
        result = utils_system.is_system_macos()
        self.assertFalse(result)

    @patch("gt.utils.system.get_system", return_value=utils_system.OS_WINDOWS)
    def test_is_system_windows_returns_true(self, mock_get_system):
        result = utils_system.is_system_windows()
        self.assertTrue(result)

    @patch("gt.utils.system.get_system", return_value=utils_system.OS_MAC)
    def test_is_system_windows_returns_false(self, mock_get_system):
        result = utils_system.is_system_windows()
        self.assertFalse(result)

    @patch("gt.utils.system.get_system", return_value=utils_system.OS_LINUX)
    def test_is_system_linux_returns_true(self, mock_get_system):
        result = utils_system.is_system_linux()
        self.assertTrue(result)

    @patch("gt.utils.system.get_system", return_value=utils_system.OS_MAC)
    def test_is_system_linux_returns_false(self, mock_get_system):
        result = utils_system.is_system_linux()
        self.assertFalse(result)

    def test_get_temp_folder(self):
        result = utils_system.get_temp_dir()
        expected = tempfile.gettempdir()
        self.assertEqual(expected, result)

    @patch("gt.utils.system.get_system")
    def test_get_home_dir(self, mock_get_system):
        mock_get_system.return_value = "mocked_value"
        result = utils_system.get_home_dir()
        expected = pathlib.Path.home()  # Exactly what the function returns
        self.assertEqual(expected, result)

    @patch("gt.utils.system.get_home_dir")
    def test_get_desktop_path(self, mock_get_home_dir):
        mock_get_home_dir.return_value = "path"
        result = utils_system.get_desktop_path()
        expected = os.path.join("path", "Desktop")
        self.assertEqual(expected, result)

    def test_get_maya_install_dir_win32(self):
        result = utils_system.get_maya_install_dir(utils_system.OS_WINDOWS)
        expected = r"C:\Program Files\Autodesk"
        self.assertEqual(expected, result)

    def test_get_maya_install_dir_mac(self):
        result = utils_system.get_maya_install_dir(utils_system.OS_MAC)
        expected = f"/Applications/Autodesk"
        self.assertEqual(expected, result)

    def test_get_maya_install_dir_key_error(self):
        with self.assertRaises(KeyError):
            utils_system.get_maya_install_dir(system="random_missing_key")

    def test_get_maya_path_win32(self):
        result = utils_system.get_maya_path(system=utils_system.OS_WINDOWS, version="2024", get_maya_python=False)
        expected = f"C:\\Program Files\\Autodesk\\Maya2024\\bin\\maya.exe"
        self.assertEqual(expected, result)

    def test_get_maya_path_mac(self):
        result = utils_system.get_maya_path(system=utils_system.OS_MAC, version="2023", get_maya_python=False)
        expected = "/Applications/Autodesk/maya2023/Maya.app/Contents/bin/maya"
        self.assertEqual(expected, result)

    def test_get_maya_path_key_error(self):
        with self.assertRaises(KeyError):
            utils_system.get_maya_path(system="random_missing_key", version="2024", get_maya_python=False)

    @patch("os.getenv")
    @patch("subprocess.run")
    @patch("gt.utils.system.get_system")
    def test_open_file_dir_win32(self, mock_get_system, mock_subprocess_run, mock_getenv):
        mock_getenv.return_value = "mocked_win_dir_path"
        target_folder = tempfile.gettempdir()
        mock_get_system.return_value = utils_system.OS_WINDOWS
        utils_system.open_file_dir(target_folder)
        mock_get_system.assert_called_once()
        mock_subprocess_run.assert_called_once()
        result = str(mock_subprocess_run.call_args)
        mocked_win_dir_path = os.path.join("mocked_win_dir_path", "explorer.exe")
        expected = f"call({str([mocked_win_dir_path, target_folder])})"
        self.assertEqual(expected, result)

    @patch("subprocess.call")
    @patch("gt.utils.system.get_system")
    def test_open_file_dir_mac(self, mock_get_system, mock_subprocess_call):
        temp_folder = tempfile.gettempdir()
        mock_get_system.return_value = utils_system.OS_MAC
        utils_system.open_file_dir(temp_folder)
        mock_get_system.assert_called_once()
        mock_subprocess_call.assert_called_once()
        result = str(mock_subprocess_call.call_args)
        expected = f'call({str(["open", "-R", temp_folder])})'
        self.assertEqual(expected, result)

    def test_get_maya_preferences_dir_win32(self):
        result = utils_system.get_maya_preferences_dir(system=utils_system.OS_WINDOWS)
        generated_path = os.path.join(os.path.expanduser("~"), "Documents", "maya")
        expected = os.path.normpath(generated_path)
        self.assertEqual(expected, result)

    def test_get_maya_preferences_dir_mac(self):
        result = utils_system.get_maya_preferences_dir(system=utils_system.OS_MAC)
        expected = os.path.join(os.path.expanduser("~"), "Library", "Preferences", "Autodesk", "maya")
        self.assertEqual(expected, result)

    @patch("gt.utils.system.get_maya_preferences_dir")
    def test_get_available_maya_preferences(self, mock_get_maya_preferences_dir):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        mock_get_maya_preferences_dir.return_value = test_temp_dir
        result = {}
        try:
            for folder in ["2020", "2024", "folder", "scripts", "2023backup"]:
                test_obj = os.path.join(test_temp_dir, folder)
                if not os.path.exists(test_obj):
                    os.mkdir(test_obj)
            result = utils_system.get_available_maya_preferences_dirs(use_maya_commands=False)
        except Exception as e:
            logger.warning(f"Failed to test maya preferences: Issue:{e}")
        mock_get_maya_preferences_dir.assert_called_once()
        expected = {"2020": os.path.join(test_temp_dir, "2020"), "2024": os.path.join(test_temp_dir, "2024")}
        self.assertEqual(expected, result)

    @patch("gt.utils.system.get_maya_install_dir")
    def test_get_available_maya_install_dirs(self, mock_get_maya_install_dir):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        mock_get_maya_install_dir.return_value = test_temp_dir
        result = {}
        try:
            for folder in ["Maya2020", "maya2024", "folder", "scripts", "2023backup", "maya2023backup"]:
                test_obj = os.path.join(test_temp_dir, folder)
                if not os.path.exists(test_obj):
                    os.mkdir(test_obj)
            result = utils_system.get_available_maya_install_dirs()
        except Exception as e:
            logger.warning(f"Failed to test maya preferences: Issue:{e}")
        mock_get_maya_install_dir.assert_called_once()
        expected = {"2020": os.path.join(test_temp_dir, "Maya2020"), "2024": os.path.join(test_temp_dir, "maya2024")}
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("gt.utils.system.get_system")
    @patch("gt.utils.system.get_available_maya_install_dirs")
    def test_get_maya_executable_win32(self, mock_install_dirs, mock_get_system, mock_exists):
        mock_install_dirs.return_value = {"2022": "mocked_path", "2024": "mocked_path"}
        mock_get_system.return_value = utils_system.OS_WINDOWS
        mock_exists.return_value = True
        result = utils_system.get_maya_executable()
        mock_install_dirs.assert_called_once()
        mock_exists.assert_called_once()
        expected = r"C:\Program Files\Autodesk\Maya2024\bin\maya.exe"
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("gt.utils.system.get_system")
    @patch("gt.utils.system.get_available_maya_install_dirs")
    def test_get_maya_executable_win32_preferred_version(self, mock_install_dirs, mock_get_system, mock_exists):
        mock_install_dirs.return_value = {"2020": "mocked_path", "2024": "mocked_path"}
        mock_get_system.return_value = utils_system.OS_WINDOWS
        mock_exists.return_value = True
        result = utils_system.get_maya_executable(preferred_version="2020")
        mock_install_dirs.assert_called_once()
        mock_exists.assert_called_once()
        expected = r"C:\Program Files\Autodesk\Maya2020\bin\maya.exe"
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("gt.utils.system.get_system")
    @patch("gt.utils.system.get_available_maya_install_dirs")
    def test_get_maya_executable_win32_maya_python(self, mock_install_dirs, mock_get_system, mock_exists):
        mock_install_dirs.return_value = {"2020": "mocked_path", "2024": "mocked_path"}
        mock_get_system.return_value = utils_system.OS_WINDOWS
        mock_exists.return_value = True  # Skip check to see if it exists
        result = utils_system.get_maya_executable(get_maya_python=True)
        mock_install_dirs.assert_called_once()
        mock_exists.assert_called_once()
        expected = r"C:\Program Files\Autodesk\Maya2024\bin\mayapy.exe"
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("gt.utils.system.get_system")
    @patch("gt.utils.system.get_available_maya_install_dirs")
    def test_get_maya_executable_mac(self, mock_install_dirs, mock_get_system, mock_exists):
        mock_install_dirs.return_value = {"2022": "mocked_path", "2024": "mocked_path"}
        mock_get_system.return_value = utils_system.OS_MAC
        mock_exists.return_value = True  # Skip check to see if it exists
        result = utils_system.get_maya_executable()
        mock_install_dirs.assert_called_once()
        mock_exists.assert_called_once()
        expected = r"/Applications/Autodesk/maya2024/Maya.app/Contents/bin/maya"
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("gt.utils.system.get_system")
    @patch("gt.utils.system.get_available_maya_install_dirs")
    def test_get_maya_executable_mac_preferred_version(self, mock_install_dirs, mock_get_system, mock_exists):
        mock_install_dirs.return_value = {"2020": "mocked_path", "2024": "mocked_path"}
        mock_get_system.return_value = utils_system.OS_MAC
        mock_exists.return_value = True  # Skip check to see if it exists
        result = utils_system.get_maya_executable(preferred_version="2020")
        mock_install_dirs.assert_called_once()
        mock_exists.assert_called_once()
        expected = r"/Applications/Autodesk/maya2020/Maya.app/Contents/bin/maya"
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("gt.utils.system.get_system")
    @patch("gt.utils.system.get_available_maya_install_dirs")
    def test_get_maya_executable_mac_maya_python(self, mock_install_dirs, mock_get_system, mock_exists):
        mock_install_dirs.return_value = {"2020": "mocked_path", "2024": "mocked_path"}
        mock_get_system.return_value = utils_system.OS_MAC  # Force Mac
        mock_exists.return_value = True  # Skip check to see if it exists
        result = utils_system.get_maya_executable(get_maya_python=True)
        mock_install_dirs.assert_called_once()
        mock_exists.assert_called_once()
        expected = r"/Applications/Autodesk/maya2024/Maya.app/Contents/bin/mayapy"
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("subprocess.check_call")
    def test_launch_maya_from_path(self, mock_check_call, mock_exists):
        mock_exists.return_value = True  # Skip check to see if it exists
        utils_system.launch_maya_from_path(maya_path="mocked_path")
        mock_exists.assert_called_once()
        mock_check_call.assert_called_once()
        result = str(mock_check_call.call_args)
        expected = "call(['mocked_path'])"
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("subprocess.check_call")
    def test_launch_maya_from_path_python_script(self, mock_check_call, mock_exists):
        mock_exists.return_value = True  # Skip check to see if it exists
        utils_system.launch_maya_from_path(maya_path="mocked_path", python_script="py")
        mock_exists.assert_called_once()
        mock_check_call.assert_called_once()
        result = str(mock_check_call.call_args)
        expected = (
            "call(['mocked_path', '-c', " "'python(\"import base64; exec (base64.urlsafe_b64decode(b\\'cHk=\\'))\")'])"
        )
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("subprocess.check_call")
    def test_launch_maya_from_path_additional_args(self, mock_check_call, mock_exists):
        mock_exists.return_value = True  # Skip check to see if it exists
        utils_system.launch_maya_from_path(maya_path="mocked_path", additional_args=["a", "b"])
        mock_exists.assert_called_once()
        mock_check_call.assert_called_once()
        result = str(mock_check_call.call_args)
        expected = "call(['mocked_path', 'a', 'b'])"
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("subprocess.check_call")
    @patch("gt.utils.system.get_maya_executable")
    def test_launch_maya(self, mock_get_maya_executable, mock_check_call, mock_exists):
        mock_get_maya_executable.return_value = "mocked_path"
        mock_exists.return_value = True  # Skip check to see if it exists
        utils_system.launch_maya()
        mock_exists.assert_called_once()
        mock_check_call.assert_called_once()
        result = str(mock_check_call.call_args)
        expected = "call(['mocked_path'])"
        self.assertEqual(expected, result)

    @patch("os.path.exists")
    @patch("subprocess.check_call")
    @patch("gt.utils.system.get_maya_executable")
    def test_launch_maya_preferred_version(self, mock_get_maya_executable, mock_check_call, mock_exists):
        mock_get_maya_executable.return_value = "mocked_path"
        mock_exists.return_value = True  # Skip check to see if it exists
        utils_system.launch_maya(preferred_version="2024")
        mock_exists.assert_called_once()
        mock_check_call.assert_called_once()
        result_one = str(mock_check_call.call_args)
        result_two = str(mock_get_maya_executable.call_args)
        expected = ["call(['mocked_path'])", "call(preferred_version='2024')"]
        self.assertEqual(expected, [result_one, result_two])

    @patch("os.path.exists")
    @patch("subprocess.call")
    @patch("gt.utils.system.get_maya_executable")
    def test_run_script_using_maya_python(self, mock_get_maya_executable, mock_call, mock_exists):
        mock_get_maya_executable.return_value = "mocked_headless_path"
        mock_exists.return_value = True  # Skip check to see if it exists
        utils_system.run_script_using_maya_python("mocked_script_path")
        mock_exists.assert_called_once()
        mock_call.assert_called_once()
        result = str(mock_call.call_args)
        expected = "call(['mocked_headless_path', 'mocked_script_path'])"
        self.assertEqual(expected, result)

    def test_process_launch_options_value_error(self):
        with self.assertRaises(ValueError):
            utils_system.process_launch_args([])

    @patch("sys.stdout.write", MagicMock)
    def test_process_launch_options_value_unrecognized(self):
        result = utils_system.process_launch_args(["mocked_script_name", "-unrecognized_test"])
        expected = False
        self.assertEqual(expected, result)

    @patch("gt.core.setup.install_package")
    def test_process_launch_options_install(self, mock_install_package):
        utils_system.process_launch_args(["mocked_script_name", "-install"])
        mock_install_package.assert_called_once()
        result = str(mock_install_package.call_args)
        expected = "call(clean_install=False)"
        self.assertEqual(expected, result)

    @patch("gt.core.setup.install_package")
    def test_process_launch_options_install_clean(self, mock_install_package):
        utils_system.process_launch_args(["mocked_script_name", "-install", "-clean"])
        mock_install_package.assert_called_once()
        result = str(mock_install_package.call_args)
        expected = "call(clean_install=True)"
        self.assertEqual(expected, result)

    @patch("gt.tools.package_setup.launcher_entry_point")
    def test_process_launch_options_install_gui(self, mock_launcher_entry_point):
        utils_system.process_launch_args(["mocked_script_name", "-install", "-gui"])
        mock_launcher_entry_point.assert_called_once()

    @patch("gt.core.setup.uninstall_package")
    def test_process_launch_options_uninstall(self, mock_uninstall_package):
        result = utils_system.process_launch_args(["mocked_script_name", "-uninstall"])
        mock_uninstall_package.assert_called_once()
        expected = True
        self.assertEqual(expected, result)

    @patch("gt.utils.system.load_package_menu")
    def test_process_launch_options_launch(self, mock_launch):
        result = utils_system.process_launch_args(["mocked_script_name", "-launch"])
        mock_launch.assert_called_once()
        expected = True
        self.assertEqual(expected, result)

    @patch("tests.run_all_tests_with_summary")
    def test_process_launch_options_test(self, mock_tests):
        result = utils_system.process_launch_args(["mocked_script_name", "-test", "-all"])
        mock_tests.assert_called_once()
        expected = True
        self.assertEqual(expected, result)

    @patch("gt.utils.system.eval")
    @patch("importlib.import_module")
    def test_initialize_from_package_calling(self, mock_import_module, mock_eval):
        result = utils_system.initialize_from_package("mocked_import_path", "mocked_entry_point_function")
        mock_import_module.assert_called_once()
        mock_eval.assert_called_once()
        expected = True
        self.assertEqual(expected, result)

    @patch("gt.utils.system.eval")
    @patch("importlib.import_module")
    def test_initialize_from_package_arguments(self, mock_import_module, mock_eval):
        utils_system.initialize_from_package("mocked_import_path", "mocked_entry_point_function")
        mock_import_module.assert_called_once()
        mock_eval.assert_called_once()
        expected = "call('module.mocked_entry_point_function()')"
        result = str(mock_eval.call_args)
        self.assertEqual(expected, result)

    @patch("gt.utils.system.initialize_from_package")
    def test_initialize_utility(self, mock_initialize_from_package):
        utils_system.initialize_utility("mocked_import_path", "mocked_entry_point_function")
        mock_initialize_from_package.assert_called_once()
        expected_one = "import_path='gt.core.mocked_import_path'"
        expected_two = "entry_point_function='mocked_entry_point_function'"
        result = str(mock_initialize_from_package.call_args_list)
        for expected in [expected_one, expected_two]:
            self.assertIn(expected, result)

    @patch("gt.utils.system.launch_maya")
    def test_load_package_menu_launching_maya(self, mock_launch_maya):
        utils_system.load_package_menu(launch_maya_app=True)
        mock_launch_maya.assert_called_once()
        result_kwargs = str(mock_launch_maya.call_args)
        expected_key = "python_script"
        self.assertIn(expected_key, result_kwargs)

    @patch("gt.tools.package_setup.gt_tools_maya_menu.load_menu")
    def test_load_package_menu_injecting(self, mock_load_menu):
        utils_system.load_package_menu(launch_maya_app=False)
        mock_load_menu.assert_called_once()

    def test_function_execution_time(self):
        @time_profiler
        def temp_function(*args, **kwargs):
            pass

        with io.StringIO() as buf, redirect_stdout(buf):
            temp_function("abc", input="def")
            result = buf.getvalue()

        self.assertRegex(result, r"\D*0\.\d+\D*")  # Characters #.### Characters
        self.assertTrue(result.startswith("Execution Time: "))
        self.assertIn(" - Function: ", result)

    def test_function_return_value(self):
        @time_profiler
        def add_numbers(a, b):
            return a + b

        result = add_numbers(2, 3)
        self.assertEqual(result, 5)

    def test_function_with_args_and_kwargs(self):
        @time_profiler
        def greet_person(name, message="Hello"):
            return f"{message}, {name}!"

        result = greet_person("Barbara", message="Hi")
        self.assertEqual(result, "Hi, Barbara!")

    def test_single_valid_callback(self):
        # Test with a single valid callback function
        mock_callback = MagicMock()
        utils_system.callback(mock_callback)
        mock_callback.assert_called_once()

    def test_multiple_valid_callbacks(self):
        # Test with multiple valid callback functions
        mock_callback1 = MagicMock()
        mock_callback2 = MagicMock()
        utils_system.callback([mock_callback1, mock_callback2])
        mock_callback1.assert_called_once()
        mock_callback2.assert_called_once()

    def test_list_conversion(self):
        # Test that the input is correctly converted to a list
        mock_callback = MagicMock()
        utils_system.callback(mock_callback)
        mock_callback.assert_called_once()

        # Make sure the function is called with correct arguments
        mock_callback2 = MagicMock()
        utils_system.callback(mock_callback2, 1, 2, key1="value1", key2="value2")
        mock_callback2.assert_called_once_with(1, 2, key1="value1", key2="value2")

    def test_execute_deferred(self):
        mocked_function = MagicMock()
        utils_system.execute_deferred(func=mocked_function)
        mocked_function.assert_called_once()

    def test_execute_deferred_string(self):
        utils_system.execute_deferred(func="logger.debug('')")

    @patch("maya.OpenMaya.MGlobal.mayaState")
    def test_execute_deferred_called(self, mocked_maya_state):
        utils_system.execute_deferred(func="logger.debug('')")
        mocked_maya_state.assert_called_once()

    def test_successful_import(self):
        # Test importing a valid class
        imported_object = utils_system.import_from_path("math.sqrt")
        import math

        self.assertEqual(math.sqrt, imported_object)

    def test_import_non_class_int(self):
        imported_object = utils_system.import_from_path("builtins.int")
        self.assertEqual(int, imported_object)

    def test_import_non_class_print(self):
        # Test importing a non-class object
        imported_object = utils_system.import_from_path("builtins.print")
        import builtins

        self.assertEqual(builtins.print, imported_object)

    def test_import_invalid_path(self):
        # Test importing an invalid class path
        imported_object = utils_system.import_from_path("nonexistent_module.NonexistentClass")
        self.assertIsNone(imported_object)

    def test_no_arguments(self):
        def func():
            pass

        args, kwargs = utils_system.get_function_arguments(func)
        self.assertEqual(args, [])
        self.assertEqual(kwargs, [])

    def test_with_arguments(self):
        def func(a, b, c=0, d=1):
            pass

        args, kwargs = utils_system.get_function_arguments(func)
        self.assertEqual(args, ["a", "b"])
        self.assertEqual(kwargs, ["c", "d"])

    def test_kwargs_as_dict_true(self):
        def sample_function(a, b=10, c="hello"):
            pass

        args, kwargs = utils_system.get_function_arguments(sample_function, kwargs_as_dict=True)

        expected_args = ["a"]
        expected_kwargs = {"b": 10, "c": "hello"}

        self.assertEqual(args, expected_args)
        self.assertEqual(kwargs, expected_kwargs)

    def test_kwargs_as_dict_false(self):
        def sample_function(a, b=10, c="hello"):
            pass

        args, kwargs = utils_system.get_function_arguments(sample_function, kwargs_as_dict=False)

        expected_args = ["a"]
        expected_kwargs = ["b", "c"]

        self.assertEqual(args, expected_args)
        self.assertEqual(kwargs, expected_kwargs)

    def test_get_docstring(self):
        def function_with_docstring():
            """
            This is an example function.
            It does nothing but demonstrate how to use the get_docstring function.
            """
            pass

        self.assertEqual(utils_system.get_docstring(function_with_docstring), function_with_docstring.__doc__)

    def test_get_docstring_empty(self):
        def no_docstring_function():
            pass

        expected_docstring = ""
        result = utils_system.get_docstring(no_docstring_function)
        self.assertEqual(expected_docstring, result)

    def test_get_docstring_without_tabs_or_new_lines(self):
        def example_function():
            """
            This is an example docstring.

                This line has a leading tab.
            """
            pass

        expected_docstring = "This is an example docstring.\n\nThis line has a leading tab."
        result = utils_system.get_docstring(example_function, strip=True, strip_new_lines=True)
        self.assertEqual(expected_docstring, result)

    def test_get_docstring_without_tabs(self):
        def example_function():
            """
            This is an example docstring.

                This line has a leading tab.
            """
            pass

        expected_docstring = "\nThis is an example docstring.\n\nThis line has a leading tab.\n"
        result = utils_system.get_docstring(example_function, strip=True, strip_new_lines=False)
        self.assertEqual(expected_docstring, result)

    def test_get_docstring_non_callable(self):
        non_callable_object = 42
        with self.assertRaises(ValueError):
            utils_system.get_docstring(non_callable_object)

    def test_get_docstring_non_callable_none(self):
        with self.assertRaises(ValueError):
            utils_system.get_docstring(None)

    def test_default_format(self):
        expected = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        result = utils_system.get_formatted_time()
        self.assertEqual(expected, result)

    def test_custom_format(self):
        custom_format = "%A, %B %d, %Y - %I:%M %p"
        expected = datetime.now().strftime(custom_format)
        result = utils_system.get_formatted_time(format_str=custom_format)
        self.assertEqual(expected, result)

    def test_execution_success(self):
        code = "result = 2 + 2"
        expected = None  # No exceptions raised
        result = utils_system.execute_python_code(code)
        self.assertEqual(expected, result)

    def test_execution_error_without_raise(self):
        code = "result = 1 / 0"
        expected = None  # Exception caught, no error raised
        logging.disable(logging.WARNING)
        result = utils_system.execute_python_code(code)
        logging.disable(logging.NOTSET)
        self.assertEqual(expected, result)

    def test_execution_error_with_raise(self):
        code = "result = unknown_variable"
        with self.assertRaises(NameError):
            utils_system.execute_python_code(code, raise_errors=True)

    def test_log_and_raise(self):
        code = "result = 1 / 0"
        with self.assertRaises(ZeroDivisionError):
            utils_system.execute_python_code(code, raise_errors=True, verbose=True)

    def test_create_object_from_local_namespace(self):
        class MyClass:
            pass

        obj = utils_system.create_object("MyClass", class_path=locals())
        self.assertIsInstance(obj, MyClass)

    def test_create_object_with_module_path(self):
        # Test creating an object by specifying a module path
        obj = utils_system.create_object("JSONDecoder", class_path="json")
        import json

        self.assertIsInstance(obj, json.JSONDecoder)

    def test_create_object_with_invalid_module_path(self):
        # Test creating an object with an invalid module path
        with self.assertRaises(ImportError):
            utils_system.create_object("MyClass", class_path="non_existent_module")

    def test_create_object_with_missing_class_in_module(self):
        # Test creating an object when the class is missing in the module
        with self.assertRaises(NameError):
            utils_system.create_object("NonExistentClass")

    def test_create_object_with_warning(self):
        logging.disable(logging.WARNING)
        utils_system.create_object("NonExistentClass", raise_errors=False)
        logging.disable(logging.NOTSET)
