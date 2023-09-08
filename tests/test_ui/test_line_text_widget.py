from PySide2.QtWidgets import QApplication, QDialog, QVBoxLayout
from PySide2.QtGui import QColor
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
from gt.ui.line_text_widget import LineTextWidget


class TestLineTextWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if not app:
            cls.app = QApplication(sys.argv)

    def test_line_number_color(self):
        line_text_widget = LineTextWidget()
        line_text_widget.set_line_number_color(color=QColor(255, 0, 0))  # Set a red color
        self.assertEqual(line_text_widget.number_bar.number_color, QColor(255, 0, 0))

    def test_line_number_bold_color(self):
        line_text_widget = LineTextWidget()
        line_text_widget.line_number_bold_color(color=QColor(0, 255, 0))  # Set a green color
        self.assertEqual(line_text_widget.number_bar.number_bold_color, QColor(0, 255, 0))

    def test_dialog_with_syntax_highlighter(self):
        from gt.ui.syntax_highlighter import PythonSyntaxHighlighter
        dialog = QDialog()
        layout = QVBoxLayout(dialog)
        line_text_widget = LineTextWidget()
        dialog.setLayout(layout)
        layout.addWidget(line_text_widget)
        PythonSyntaxHighlighter(line_text_widget.get_text_edit().document())
