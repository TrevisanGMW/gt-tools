import os
import sys
import pathlib
import logging
import unittest
import tempfile
from unittest.mock import patch, Mock

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
from utils import system_utils


class TestSystemUtils(unittest.TestCase):
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
        mock_get_system.return_value = "random_value"
        result = system_utils.get_home_dir()
        expected = pathlib.Path.home()  # Exactly what the function returns
        self.assertEqual(expected, result)

    @patch('utils.system_utils.get_home_dir')
    def test_get_desktop_path(self, mock_get_home_dir):
        mock_get_home_dir.return_value = "path"
        result = system_utils.get_desktop_path()
        expected = os.path.join("path", "Desktop")
        self.assertEqual(expected, result)
