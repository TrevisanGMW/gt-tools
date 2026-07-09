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

# Import Utility and Maya Test Tools
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.tests import maya_test_tools
from gt.core import session as core_session


class TestSessionCore(unittest.TestCase):
    def test_is_script_in_interactive_maya(self):
        expected = False
        result = core_session.is_script_in_interactive_maya()  # "maya##.exe"
        self.assertEqual(expected, result)

    def test_is_script_in_py_maya(self):
        expected = True
        result = core_session.is_script_in_py_maya()  # "mayapy.exe"
        self.assertEqual(expected, result)

    def test_get_temp_folder(self):
        expected = tempfile.gettempdir()
        result = core_session.get_temp_dir()
        self.assertEqual(expected, result)

    def test_get_loaded_modules(self):
        expected = ["fake", "state"]
        result = core_session.get_loaded_modules(expected)
        self.assertEqual(expected, result)

    def test_get_maya_version(self):
        maya_test_tools.import_maya_standalone()
        expected = maya_test_tools.eval_mel_code("about -v;")
        result = core_session.get_maya_version()
        self.assertEqual(expected, result)

    def test_is_maya_standalone_initialized(self):
        maya_test_tools.import_maya_standalone()
        expected = True
        result = core_session.is_maya_standalone_initialized()
        self.assertEqual(expected, result)

    @patch("importlib.import_module")
    @patch("inspect.getfile")
    @patch("gt.core.session.print_when_true")
    def test_successful_import(self, mock_print_when_true, mock_getfile, mock_import_module):
        # Arrange
        module_name = "example_module"
        mock_import_module.return_value = MagicMock()
        mock_getfile.return_value = "/path/to/module.py"

        # Act
        result = core_session.get_module_path(module_name, verbose=True)

        # Assert
        mock_import_module.assert_called_once_with(module_name)
        mock_getfile.assert_called_once_with(mock_import_module.return_value)
        mock_print_when_true.assert_called_once_with("/path/to/module.py", use_system_write=True, do_print=True)
        self.assertEqual(result, "/path/to/module.py")

    @patch("importlib.import_module", side_effect=ImportError)
    @patch("gt.core.feedback.print_when_true")
    def test_import_error(self, mock_print_when_true, mock_import_module):
        # Arrange
        module_name = "non_existent_module"

        # Act
        result = core_session.get_module_path(module_name, verbose=False)

        # Assert
        mock_import_module.assert_called_once_with(module_name)
        mock_print_when_true.assert_not_called()
        self.assertIsNone(result)