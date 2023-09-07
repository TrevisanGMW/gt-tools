from PySide2.QtWidgets import QApplication
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
from gt.ui.input_window_text import InputWindowText


class TestInputWindowText(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if not app:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        self.window = InputWindowText()

    def test_window_title(self):
        expected_title = "New Window Title"
        self.window.set_window_title(expected_title)
        self.assertEqual(self.window.windowTitle(), expected_title)

    def test_text_field_text(self):
        expected_text = "Sample Text"
        self.window.set_text_field_text(expected_text)
        self.assertEqual(self.window.get_text_field_text(), expected_text)

    def test_text_field_placeholder(self):
        expected_placeholder = "Enter text here"
        self.window.set_text_field_placeholder(expected_placeholder)
        self.assertEqual(self.window.text_field.placeholderText(), expected_placeholder)

    def test_confirm_button_text(self):
        expected_button_text = "OK"
        self.window.set_confirm_button_text(expected_button_text)
        self.assertEqual(self.window.confirm_button.text(), expected_button_text)

    def test_message_label(self):
        expected_message = "This is a test message"
        self.window.set_message(expected_message)
        self.assertEqual(self.window.description_label.text(), expected_message)
