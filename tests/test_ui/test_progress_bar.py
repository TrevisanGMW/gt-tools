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
from gt.ui.progress_bar import ProgressBarWindow


class TestProgressBar(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if not app:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        self.window = ProgressBarWindow()

    def test_set_progress_bar_value(self):
        window = ProgressBarWindow()
        window.show()

        # Test setting the progress bar value
        window.set_progress_bar_value(50)
        self.assertEqual(window.progress_bar.value(), 50)

    def test_add_text_to_output_box(self):
        window = ProgressBarWindow()

        # Test adding text to the output box
        text_to_add = "This is a test message."
        window.add_text_to_output_box(text_to_add)
        output_text = window.get_output_box_plain_text()
        self.assertIn(text_to_add, output_text)

    def test_change_line_color(self):
        window = ProgressBarWindow()

        # Test changing the color of a specific line
        text_to_add = "This is a test message."
        window.add_text_to_output_box(text_to_add)
        window.change_line_color(line_number=1, color="red")

        # Get the formatted text and check if it contains the color tag
        output_text = window.get_output_box_plain_text()
        self.assertIn(text_to_add, output_text)

    def test_change_last_line_color(self):
        window = ProgressBarWindow()

        # Test changing the color of the last line
        text_to_add1 = "This is line 1."
        text_to_add2 = "This is line 2."
        window.add_text_to_output_box(text_to_add1)
        window.add_text_to_output_box(text_to_add2)
        window.change_last_line_color("blue")

        # Get the formatted text and check if the last line contains the color tag
        output_text = window.get_output_box_plain_text()
        self.assertIn(text_to_add1, output_text)
        self.assertIn(text_to_add2, output_text)
