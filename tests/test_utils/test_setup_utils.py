import os
import sys
import logging
import unittest
from unittest.mock import patch, MagicMock

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
from utils import setup_utils


class TestSetupUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    def test_get_maya_settings_dir_exists(self):
        settings_dir = setup_utils.get_maya_preferences_dir()
        result = os.path.exists(settings_dir)
        expected = True
        self.assertEqual(expected, result)

    def test_get_maya_settings_dir_is_folder(self):
        settings_dir = setup_utils.get_maya_preferences_dir()
        result = os.path.isdir(settings_dir)
        expected = True
        self.assertEqual(expected, result)

    @patch('maya.cmds.about')
    def test_get_maya_settings_dir_about_key(self, mock_about):
        mock_about.return_value = "mocked_path"
        setup_utils.get_maya_preferences_dir()
        result = str(mock_about.call_args)
        expected = "call(preferences=True)"
        self.assertEqual(expected, result)

    def test_get_package_requirements_keys(self):
        result = setup_utils.get_package_requirements()
        expected_items = ["__init__.py", "tools", "ui", "utils"]
        for item in expected_items:
            self.assertIn(item, result)

    def test_get_package_requirements_path_exists(self):
        result_dict = setup_utils.get_package_requirements()
        self.assertIsInstance(result_dict, dict)
        for value in result_dict.values():
            exists = os.path.exists(str(value))
            self.assertEqual(True, exists)

    def test_copy_package_requirements(self):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()  # Create test elements
        source_dir = os.path.join(test_temp_dir, "source_dir")
        target_dir = os.path.join(test_temp_dir, "target_dir")
        requirement_dir_one = os.path.join(source_dir, "dir_one")
        requirement_dir_two = os.path.join(source_dir, "dir_two")
        requirement_py = os.path.join(source_dir, "empty.py")
        undesired_pyc = os.path.join(source_dir, "empty.pyc")
        undesired_dir_one = os.path.join(requirement_dir_one, "__pycache__")
        undesired_dir_two = os.path.join(source_dir, "__pycache__")
        for path in [source_dir,
                     target_dir,
                     requirement_dir_one,
                     requirement_dir_two,
                     undesired_dir_one,
                     undesired_dir_two]:
            if not os.path.exists(path):
                os.mkdir(path)
        for file in [requirement_py, undesired_pyc]:
            with open(file, 'w'):
                pass  # Create empty file
        mocked_package_requirements = {"dir_one": str(requirement_dir_one),
                                       "dir_two": str(requirement_dir_two),
                                       "empty.py": str(requirement_py)}
        setup_utils.copy_package_requirements(target_folder=target_dir,
                                              package_requirements=mocked_package_requirements)
        source_result = sorted(os.listdir(source_dir))
        source_expected = sorted(['dir_one', 'dir_two', 'empty.py', 'empty.pyc', '__pycache__'])
        self.assertEqual(source_expected, source_result)
        target_result = sorted(os.listdir(target_dir))
        target_expected = sorted(['dir_one', 'dir_two', 'empty.py'])
        self.assertEqual(target_expected, target_result)

    def test_remove_previous_install(self):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()  # Create test elements
        mocked_install_dir = os.path.join(test_temp_dir, setup_utils.PACKAGE_NAME)
        mocked_install_content_one = os.path.join(mocked_install_dir, "dir_one")
        mocked_install_content_two = os.path.join(mocked_install_dir, "dir_two")
        mocked_pyc = os.path.join(mocked_install_dir, "empty.pyc")
        mocked_py = os.path.join(mocked_install_dir, "empty.py")
        for path in [mocked_install_dir, mocked_install_content_one, mocked_install_content_two]:
            if not os.path.exists(path):
                os.mkdir(path)
        for file in [mocked_pyc, mocked_py]:
            with open(file, 'w'):
                pass  # Create empty file
        expected = True
        result = os.path.exists(mocked_install_dir)
        self.assertEqual(expected, result)
        setup_utils.remove_previous_install(target_path=mocked_install_dir)
        expected = False
        result = os.path.exists(mocked_install_dir)
        self.assertEqual(expected, result)

    def test_check_installation_integrity(self):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()  # Create test elements
        for requirement in setup_utils.PACKAGE_REQUIREMENTS:
            if "." in requirement:  # Assuming files have an extension
                with open(os.path.join(test_temp_dir, requirement), 'w'):
                    pass
            else:
                dir_path = os.path.join(test_temp_dir, requirement)
                if not os.path.exists(dir_path):
                    os.mkdir(dir_path)
        result = setup_utils.check_installation_integrity(package_target_folder=test_temp_dir)
        expected = True
        self.assertEqual(expected, result)

    @patch('utils.setup_utils.get_available_maya_preferences_dirs')
    def test_generate_scripts_dir_list_invalid_preferences(self, mock_get_preferences):
        mock_get_preferences.return_value = {'1234': 'invalid_path'}
        result = setup_utils.generate_scripts_dir_list(file_name=setup_utils.PACKAGE_USER_SETUP,
                                                       only_existing=False)
        expected = []
        self.assertEqual(expected, result)

    @patch('utils.setup_utils.get_available_maya_preferences_dirs')
    def test_generate_scripts_dir_list_not_existing(self, mock_get_preferences):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        mocked_scripts_dir = os.path.join(test_temp_dir, "scripts")
        if not os.path.exists(mocked_scripts_dir):
            os.mkdir(mocked_scripts_dir)
        mock_get_preferences.return_value = {'2020': test_temp_dir}
        result = setup_utils.generate_scripts_dir_list(file_name=setup_utils.PACKAGE_USER_SETUP,
                                                       only_existing=False)
        expected = [os.path.join(mocked_scripts_dir, setup_utils.PACKAGE_USER_SETUP)]
        self.assertEqual(expected, result)

    @patch('utils.setup_utils.get_available_maya_preferences_dirs')
    def test_generate_scripts_dir_list_existing_false(self, mock_get_preferences):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        mocked_scripts_dir = os.path.join(test_temp_dir, "scripts")
        if not os.path.exists(mocked_scripts_dir):
            os.mkdir(mocked_scripts_dir)
        mock_get_preferences.return_value = {'2020': test_temp_dir}
        result = setup_utils.generate_scripts_dir_list(file_name=setup_utils.PACKAGE_USER_SETUP,
                                                       only_existing=True)
        expected = []
        self.assertEqual(expected, result)

    @patch('utils.setup_utils.get_available_maya_preferences_dirs')
    def test_generate_scripts_dir_list_existing_true(self, mock_get_preferences):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        mocked_scripts_dir = os.path.join(test_temp_dir, "scripts")
        mocked_file_name = os.path.join(mocked_scripts_dir, setup_utils.PACKAGE_USER_SETUP)
        if not os.path.exists(mocked_scripts_dir):
            os.mkdir(mocked_scripts_dir)
        with open(mocked_file_name, 'w'):
            pass  # Create empty file
        mock_get_preferences.return_value = {'2020': test_temp_dir}
        result = setup_utils.generate_scripts_dir_list(file_name=setup_utils.PACKAGE_USER_SETUP,
                                                       only_existing=True)
        expected = [os.path.join(mocked_scripts_dir, setup_utils.PACKAGE_USER_SETUP)]
        self.assertEqual(expected, result)

    @patch('utils.setup_utils.get_available_maya_preferences_dirs')
    def test_add_entry_line_existing_default(self, mock_get_preferences):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        mocked_scripts_dir = os.path.join(test_temp_dir, "scripts")
        mocked_file_name = os.path.join(mocked_scripts_dir, setup_utils.PACKAGE_USER_SETUP)
        if not os.path.exists(mocked_scripts_dir):
            os.mkdir(mocked_scripts_dir)
        with open(mocked_file_name, 'w'):
            pass  # Create empty file
        mock_get_preferences.return_value = {'2020': test_temp_dir}
        setup_utils.add_entry_line(file_path=mocked_file_name,
                                   create_missing_file=False)
        expected = [setup_utils.PACKAGE_ENTRY_LINE + "\n"]
        with open(mocked_file_name) as file:
            result = file.readlines()
        self.assertEqual(expected, result)

    @patch('utils.setup_utils.get_available_maya_preferences_dirs')
    def test_add_entry_line_not_existing(self, mock_get_preferences):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        mocked_scripts_dir = os.path.join(test_temp_dir, "scripts")
        mocked_file_name = os.path.join(mocked_scripts_dir, setup_utils.PACKAGE_USER_SETUP)
        if not os.path.exists(mocked_scripts_dir):
            os.mkdir(mocked_scripts_dir)
        mock_get_preferences.return_value = {'2020': test_temp_dir}
        setup_utils.add_entry_line(file_path=mocked_file_name,
                                   create_missing_file=True)
        expected = [setup_utils.PACKAGE_ENTRY_LINE + "\n"]
        with open(mocked_file_name) as file:
            result = file.readlines()
        self.assertEqual(expected, result)

    @patch('utils.setup_utils.get_available_maya_preferences_dirs')
    def test_add_entry_line_with_content(self, mock_get_preferences):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        mocked_scripts_dir = os.path.join(test_temp_dir, "scripts")
        mocked_file_name = os.path.join(mocked_scripts_dir, setup_utils.PACKAGE_USER_SETUP)
        if not os.path.exists(mocked_scripts_dir):
            os.mkdir(mocked_scripts_dir)
        with open(mocked_file_name, 'w') as file:
            file.write("# Mocked content")
        mock_get_preferences.return_value = {'2020': test_temp_dir}
        setup_utils.add_entry_line(file_path=mocked_file_name,
                                   create_missing_file=True)
        expected = ['# Mocked content\n', setup_utils.PACKAGE_ENTRY_LINE + "\n"]
        with open(mocked_file_name) as file:
            result = file.readlines()
        self.assertEqual(expected, result)

    @patch('utils.setup_utils.get_available_maya_preferences_dirs')
    def test_add_entry_line_missing(self, mock_get_preferences):
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
        mocked_scripts_dir = os.path.join(test_temp_dir, "scripts")
        mocked_file_name = os.path.join(mocked_scripts_dir, setup_utils.PACKAGE_USER_SETUP)
        if not os.path.exists(mocked_scripts_dir):
            os.mkdir(mocked_scripts_dir)
        mock_get_preferences.return_value = {'2020': test_temp_dir}
        logging.disable(logging.WARNING)
        setup_utils.add_entry_line(file_path=mocked_file_name,
                                   create_missing_file=False)
        logging.disable(logging.NOTSET)
        expected = False
        result = os.path.exists(mocked_file_name)
        self.assertEqual(expected, result)
