from unittest.mock import patch, MagicMock
import unittest
import tempfile
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from tests import maya_test_tools
from gt.utils import session_utils


class TestSessionUtils(unittest.TestCase):
    def test_is_script_in_interactive_maya(self):
        expected = False
        result = session_utils.is_script_in_interactive_maya()  # "maya##.exe"
        self.assertEqual(expected, result)

    def test_is_script_in_py_maya(self):
        expected = True
        result = session_utils.is_script_in_py_maya()  # "mayapy.exe"
        self.assertEqual(expected, result)

    def test_get_temp_folder(self):
        expected = tempfile.gettempdir()
        result = session_utils.get_temp_dir()
        self.assertEqual(expected, result)

    def test_get_loaded_modules(self):
        expected = ["fake", "state"]
        result = session_utils.get_loaded_modules(expected)
        self.assertEqual(expected, result)

    def test_get_maya_version(self):
        maya_test_tools.import_maya_standalone()
        expected = maya_test_tools.eval_mel_code("about -v;")
        result = session_utils.get_maya_version()
        self.assertEqual(expected, result)

    def test_is_maya_standalone_initialized(self):
        maya_test_tools.import_maya_standalone()
        expected = True
        result = session_utils.is_maya_standalone_initialized()
        self.assertEqual(expected, result)

    @patch('importlib.import_module')
    @patch('inspect.getfile')
    @patch('gt.utils.session_utils.print_when_true')
    def test_successful_import(self, mock_print_when_true, mock_getfile, mock_import_module):
        # Arrange
        module_name = 'example_module'
        mock_import_module.return_value = MagicMock()
        mock_getfile.return_value = '/path/to/module.py'

        # Act
        result = session_utils.get_module_path(module_name, verbose=True)

        # Assert
        mock_import_module.assert_called_once_with(module_name)
        mock_getfile.assert_called_once_with(mock_import_module.return_value)
        mock_print_when_true.assert_called_once_with('/path/to/module.py', use_system_write=True, do_print=True)
        self.assertEqual(result, '/path/to/module.py')

    @patch('importlib.import_module', side_effect=ImportError)
    @patch('gt.utils.feedback_utils.print_when_true')
    def test_import_error(self, mock_print_when_true, mock_import_module):
        # Arrange
        module_name = 'non_existent_module'

        # Act
        result = session_utils.get_module_path(module_name, verbose=False)

        # Assert
        mock_import_module.assert_called_once_with(module_name)
        mock_print_when_true.assert_not_called()
        self.assertIsNone(result)

    @patch('os.path.exists')
    @patch('gt.utils.session_utils.get_module_path')
    def test_get_loaded_package_module_paths(self, mocked_module_path, mocked_exists):
        mocked_module_path.return_value = "Documents/gt-tools/gt/__init__.py"
        mocked_exists.return_value = True
        result = session_utils.get_loaded_package_module_paths()
        expected = ['Documents/gt-tools/gt/__init__.py', 'Documents/gt-tools/gt', 'Documents/gt-tools']
        self.assertEqual(expected, result)
