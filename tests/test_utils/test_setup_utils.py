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
        # Create test elements
        test_temp_dir = maya_test_tools.generate_test_temp_dir()
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
