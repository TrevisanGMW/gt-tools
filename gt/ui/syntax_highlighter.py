from PySide2.QtGui import QTextCharFormat, QColor, QSyntaxHighlighter, QFont
from PySide2.QtWidgets import QTextEdit
from PySide2.QtCore import QRegExp
import sys


def get_text_format(color, style=None):
    """
    Return a QTextCharFormat with the given attributes.

    Args:
        color (str, QColor, list, tuple): A string with a named color, a QColor or an RGB list/tuple.
                                         e.g. "white", [255, 0, 0], QColor(255, 0, 0)
        style (str, optional): Additional style attributes, e.g., "bold" or "italic".

    Returns:
        QTextCharFormat: QTextCharFormat with specified attributes.
    """
    # Set Color
    _color = QColor()
    if isinstance(color, str):
        _color.setNamedColor(color)
    elif isinstance(color, QColor):
        _color = color
    else:
        _color.setRgb(*color)
    # Set Text Style
    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in str(style):
        _format.setFontWeight(QFont.Bold)
    if 'italic' in str(style):
        _format.setFontItalic(True)
    return _format


class PythonSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False',
    ]

    # Python operators
    operators = [
        '=', '==', '!=', '<', '<=', '>', '>=',
        '\+', '-', '\*', '/', '//', '\%', '\*\*',
        '\+=', '-=', '\*=', '/=', '\%=',
        '\^', '\|', '\&', '\~', '>>', '<<',
    ]

    # Python braces
    braces = [
        '\{', '\}', '\(', '\)', '\[', '\]',
    ]

    dunder_methods = [
        "__init__", "__del__", "__str__", "__repr__", "__len__",
        "__getitem__", "__setitem__", "__delitem__", "__iter__", "__next__",
        "__contains__", "__call__", "__eq__", "__ne__", "__lt__", "__le__",
        "__gt__", "__ge__", "__add__", "__sub__", "__mul__", "__truediv__",
        "__floordiv__", "__mod__", "__pow__", "__enter__", "__exit__",
    ]

    def __init__(self, document,
                 keyword_rgb=None,
                 operator_rgb=None,
                 braces_rgb=None,
                 def_class_rgb=None,
                 quotation_single_rgb=None,
                 quotation_double_rgb=None,
                 string_rgb=None,
                 function_call_rgb=None,
                 comment_rgb=None,
                 self_rgb=None,
                 number_rgb=None,
                 dunder_rgb=None,
                 ):
        super().__init__(document)

        style_keyword = get_text_format([213, 95, 222], 'bold')  # Purple
        style_operator = get_text_format([255, 255, 255])
        style_braces = get_text_format([255, 255, 255])
        style_def_class = get_text_format([97, 175, 239], 'bold')  # Purple
        style_quotation_single = get_text_format([120, 120, 120])
        style_quotation_double = get_text_format([110, 110, 110])
        style_string = get_text_format([137, 202, 120])  # Soft Green
        style_function_call = get_text_format([97, 175, 239])  # Soft Blue
        style_comment = get_text_format([128, 128, 128])
        style_self = get_text_format([220, 105, 225], 'bold')
        style_number = get_text_format([209, 154, 102])  # Soft Orange
        style_dunder = get_text_format([239, 89, 111])  # Soft Red

        # Overwrites
        if keyword_rgb and isinstance(keyword_rgb, (list, tuple)) and len(keyword_rgb) == 3:
            style_keyword = get_text_format(keyword_rgb)
        if operator_rgb and isinstance(operator_rgb, (list, tuple)) and len(operator_rgb) == 3:
            style_operator = get_text_format(operator_rgb)
        if braces_rgb and isinstance(braces_rgb, (list, tuple)) and len(braces_rgb) == 3:
            style_braces = get_text_format(braces_rgb)
        if def_class_rgb and isinstance(def_class_rgb, (list, tuple)) and len(def_class_rgb) == 3:
            style_def_class = get_text_format(def_class_rgb)
        if quotation_single_rgb and isinstance(quotation_single_rgb, (list, tuple)) and len(quotation_single_rgb) == 3:
            style_quotation_single = get_text_format(quotation_single_rgb)
        if quotation_double_rgb and isinstance(quotation_double_rgb, (list, tuple)) and len(quotation_double_rgb) == 3:
            style_quotation_double = get_text_format(quotation_double_rgb)
        if string_rgb and isinstance(string_rgb, (list, tuple)) and len(string_rgb) == 3:
            style_string = get_text_format(string_rgb)
        if function_call_rgb and isinstance(function_call_rgb, (list, tuple)) and len(function_call_rgb) == 3:
            style_function_call = get_text_format(function_call_rgb)
        if comment_rgb and isinstance(comment_rgb, (list, tuple)) and len(comment_rgb) == 3:
            style_comment = get_text_format(comment_rgb)
        if self_rgb and isinstance(self_rgb, (list, tuple)) and len(self_rgb) == 3:
            style_self = get_text_format(self_rgb)
        if number_rgb and isinstance(number_rgb, (list, tuple)) and len(number_rgb) == 3:
            style_number = get_text_format(number_rgb)
        if dunder_rgb and isinstance(dunder_rgb, (list, tuple)) and len(dunder_rgb) == 3:
            style_dunder = get_text_format(dunder_rgb)

        # Multi-line strings (expression, flag, style)
        self.quotation_single = (QRegExp("'''"), 1, style_quotation_double)
        self.quotation_double = (QRegExp('"""'), 2, style_quotation_double)

        # Rules
        rules = []
        rules += [(rf'\b{word}\b', 0, style_keyword) for word in self.keywords]
        rules += [(rf'{operator}', 0, style_operator) for operator in self.operators]
        rules += [(rf'{brace}', 0, style_braces) for brace in self.braces]
        rules += [
            # 'self'
            (r'\bself\b', 0, style_self),
            # Double-quoted string
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, style_quotation_single),
            # Single-quoted string
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, style_quotation_single),
            # Function Call
            (r'\b\w+\s*(?=\()', 0, style_function_call),
            # Dunder methods
            (r'\b__(\w+)__\b', 0, style_dunder),
            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, style_def_class),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, style_def_class),
            # From '#' until a newline
            (r'#[^\n]*', 0, style_comment),
            # Numeric literals
            (r'\b[+-]?[0-9]+[lL]?\b', 0, style_number),
            (r'\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b', 0, style_number),
            (r'\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, style_number),
            # Strings Non-comments
            (r'"[^"]*"|"""[^"]*"""', 0, style_string),
            (r"'[^']*'|'''[^']*'''", 0, style_string),
        ]
        rules += [(rf'(?<!\bdef )\b{dunder}\b', 0, style_dunder) for dunder in self.dunder_methods]
        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(regex_pattern), index, style) for (regex_pattern, index, style) in rules]

    def highlightBlock(self, text):
        """
        Apply syntax highlighting to the given block of text.
        Args:
            text (str): The text to be syntax highlighted.
        """
        # Do other syntax formatting
        for expression, nth, format_str in self.rules:
            index = expression.indexIn(text, 0)

            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format_str)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.quotation_single)
        if not in_multiline:
            self.match_multiline(text, *self.quotation_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """
        Highlight multi-line strings in the provided text using the specified delimiter, state, and style.

        Args:
            text (str): The text to be processed.
            delimiter (QRegExp): Regular expression pattern used to identify the delimiters.
            in_state (int): State indicator for multi-line strings.
            style (QTextCharFormat): The text style to apply to the highlighted multi-line strings.

        Returns:
            bool: True if the current block state matches the specified in_state; otherwise, False.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            end = delimiter.indexIn(text, start + add)
            if end >= add:  # Ending delimiter on this line?
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
                self.setFormat(start, length, style)  # Apply style
            # No multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
                self.setFormat(start, length, style)  # Apply style
                break  # String continues to the next line
            start = delimiter.indexIn(text, start + length)  # Continue searching on the next line

        return self.currentBlockState() == in_state


if __name__ == "__main__":
    from PySide2.QtWidgets import QMainWindow
    from gt.ui import qt_utils
    import inspect

    with qt_utils.QtApplicationContext():
        main_window = QMainWindow()
        qt_utils.resize_to_screen(main_window, percentage=40)
        qt_utils.center_window(main_window)
        main_window.setStyleSheet("QTextEdit { background-color: #1D1D1D; color: #ffffff; }")
        text_edit = QTextEdit(main_window)
        highlighter = PythonSyntaxHighlighter(text_edit.document())
        main_window.setCentralWidget(text_edit)
        text_edit.setText(inspect.getsource(sys.modules[__name__]))
        main_window.show()
