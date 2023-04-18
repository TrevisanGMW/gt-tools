import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_session_utils")
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils import session_utils


class Test_SessionUtils(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        pass

    def test_is_script_in_interactive_maya(self):
        expected = False
        result = session_utils.is_script_in_interactive_maya()  # "maya##.exe"
        # Assert Results
        self.assertEqual(result, expected)

    def test_is_script_in_py_maya(self):
        expected = True
        result = session_utils.is_script_in_py_maya()  # "mayapy.exe"
        # Assert Results
        self.assertEqual(result, expected)
