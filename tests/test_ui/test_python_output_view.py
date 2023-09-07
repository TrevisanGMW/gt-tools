from PySide2.QtWidgets import QApplication
from unittest.mock import MagicMock
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Script
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.ui.python_output_view import PythonOutputView


class TestPythonOutputView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if not app:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        # Create an instance of PythonOutputView
        self.python_output_view = PythonOutputView()

    def test_clear_python_output(self):
        # Test clearing Python output
        self.python_output_view.output_python_box.get_text_edit().setPlainText("Sample text")
        self.python_output_view.clear_python_output()
        result = self.python_output_view.get_python_output_text()
        expected = ""
        self.assertEqual(result, expected)

    def test_set_python_output_text(self):
        # Test setting Python output text
        self.python_output_view.set_python_output_text("Sample text")
        result = self.python_output_view.get_python_output_text()
        expected = "Sample text"
        self.assertEqual(result, expected)

    def test_get_python_output_text(self):
        # Test getting Python output text
        self.python_output_view.output_python_box.get_text_edit().setPlainText("Sample text")
        result = self.python_output_view.get_python_output_text()
        expected = "Sample text"
        self.assertEqual(result, expected)
