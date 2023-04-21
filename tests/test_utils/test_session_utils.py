import os
import sys
import logging
import tempfile
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_session_utils")
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from utils import session_utils


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
        result = session_utils.get_temp_folder()
        self.assertEqual(expected, result)

    def test_get_loaded_modules(self):
        expected = ["fake", "state"]
        result = session_utils.get_loaded_modules(expected)
        self.assertEqual(expected, result)

    def test_fail_one_purpose(self):
        expected = True
        result = False
        self.assertEqual(expected, result)
