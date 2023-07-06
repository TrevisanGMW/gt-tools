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
        settings_dir = setup_utils.get_maya_settings_dir()
        result = os.path.exists(settings_dir)
        expected = True
        self.assertEqual(expected, result)

    def test_get_maya_settings_dir_is_folder(self):
        settings_dir = setup_utils.get_maya_settings_dir()
        result = os.path.isdir(settings_dir)
        expected = True
        self.assertEqual(expected, result)

    @patch('maya.cmds.about')
    def test_get_maya_settings_dir_about_key(self, mock_about):
        setup_utils.get_maya_settings_dir()
        result = mock_about.call_args.kwargs
        expected = {'preferences': True}
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
