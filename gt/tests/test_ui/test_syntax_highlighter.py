import gt.ui.qt_import as ui_qt
import os
import sys
import unittest

test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)

from gt.ui.syntax_highlighter import PythonSyntaxHighlighter


class TestPythonSyntaxHighlighter(unittest.TestCase):
    """Tests the Python syntax highlighter."""

    @classmethod
    def setUpClass(cls):
        """Creates a Qt application for syntax highlighter tests."""
        app = ui_qt.QtWidgets.QApplication.instance()
        if not app:
            cls.app = ui_qt.QtWidgets.QApplication(sys.argv)

    @staticmethod
    def _get_foreground_color(text, block_number, target_text):
        """Gets the foreground color applied to text in a document block.

        Args:
            text (str): Full document text to highlight.
            block_number (int): Index of the text block to inspect.
            target_text (str): Text whose format should be returned.

        Returns:
            tuple or None: RGB color tuple, or None when the target has no format.
        """
        document = ui_qt.QtGui.QTextDocument(text)
        highlighter = PythonSyntaxHighlighter(document, comment_rgb=[17, 34, 51])
        highlighter.rehighlight()
        block = document.findBlockByNumber(block_number)
        target_index = block.text().find(target_text)
        for format_range in block.layout().formats():
            range_end = format_range.start + format_range.length
            if format_range.start <= target_index < range_end:
                color = format_range.format.foreground().color()
                return color.red(), color.green(), color.blue()
        return None

    def test_triple_quoted_strings_use_comment_color(self):
        """Tests triple-quoted docstrings and variables use the comment color."""
        source = (
            '"""Module header docstring.\n'
            "It spans multiple blocks.\n"
            '"""\n'
            "\n"
            "def example():\n"
            '    """Function docstring."""\n'
            "    description = '''Variable text.\n"
            "    It spans multiple blocks.\n"
            "    '''"
        )
        expected_result = (17, 34, 51)
        text_locations = [
            (0, "Module"),
            (1, "spans"),
            (2, '"""'),
            (5, "Function"),
            (6, "Variable"),
            (7, "spans"),
            (8, "'''"),
        ]

        for block_number, target_text in text_locations:
            result = self._get_foreground_color(source, block_number, target_text)
            self.assertEqual(expected_result, result)
