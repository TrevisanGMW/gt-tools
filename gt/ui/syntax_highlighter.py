import gt.ui.qt_import as ui_qt


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
    _color = ui_qt.QtGui.QColor()
    if isinstance(color, str):
        _color.setNamedColor(color)
    elif isinstance(color, ui_qt.QtGui.QColor):
        _color = color
    else:
        _color.setRgb(*color)
    # Set Text Style
    _format = ui_qt.QtGui.QTextCharFormat()
    _format.setForeground(_color)
    if "bold" in str(style):
        _format.setFontWeight(ui_qt.QtLib.Font.Bold)
    if "italic" in str(style):
        _format.setFontItalic(True)
    return _format


class PythonSyntaxHighlighter(ui_qt.QtGui.QSyntaxHighlighter):
    """Syntax highlighter for the Python language."""

    # Python keywords
    keywords = [
        "and",
        "assert",
        "break",
        "class",
        "continue",
        "def",
        "del",
        "elif",
        "else",
        "except",
        "exec",
        "finally",
        "for",
        "from",
        "global",
        "if",
        "import",
        "in",
        "is",
        "lambda",
        "not",
        "or",
        "pass",
        "print",
        "raise",
        "return",
        "try",
        "while",
        "yield",
        "None",
        "True",
        "False",
    ]

    # Python operators
    operators = [
        "=",
        "==",
        "!=",
        "<",
        "<=",
        ">",
        ">=",
        "\+",
        "-",
        "\*",
        "/",
        "//",
        "\%",
        "\*\*",
        "\+=",
        "-=",
        "\*=",
        "/=",
        "\%=",
        "\^",
        "\|",
        "\&",
        "\~",
        ">>",
        "<<",
    ]

    # Python braces
    braces = [
        "\{",
        "\}",
        "\(",
        "\)",
        "\[",
        "\]",
    ]

    dunder_methods = [
        "__init__",
        "__del__",
        "__str__",
        "__repr__",
        "__len__",
        "__getitem__",
        "__setitem__",
        "__delitem__",
        "__iter__",
        "__next__",
        "__contains__",
        "__call__",
        "__eq__",
        "__ne__",
        "__lt__",
        "__le__",
        "__gt__",
        "__ge__",
        "__add__",
        "__sub__",
        "__mul__",
        "__truediv__",
        "__floordiv__",
        "__mod__",
        "__pow__",
        "__enter__",
        "__exit__",
    ]

    def __init__(
        self,
        document,
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
        """
        Initializes the syntax highlighter with customizable color styles for Python code elements.

        Defines default text formats for keywords, operators, braces, definitions, strings,
        comments, numbers, and special identifiers (e.g., 'self', dunder methods).
        Allows overriding these default colors by providing RGB tuples for each category.

        Args:
            document: The QTextDocument instance to apply highlighting to.
            keyword_rgb (list or tuple, optional): RGB color for keywords.
            operator_rgb (list or tuple, optional): RGB color for operators.
            braces_rgb (list or tuple, optional): RGB color for braces.
            def_class_rgb (list or tuple, optional): RGB color for 'def' and 'class' keywords.
            quotation_single_rgb (list or tuple, optional): RGB color for single-quoted strings.
            quotation_double_rgb (list or tuple, optional): RGB color for double-quoted strings.
            string_rgb (list or tuple, optional): RGB color for string literals.
            function_call_rgb (list or tuple, optional): RGB color for function calls.
            comment_rgb (list or tuple, optional): RGB color for comments.
            self_rgb (list or tuple, optional): RGB color for the 'self' keyword.
            number_rgb (list or tuple, optional): RGB color for numeric literals.
            dunder_rgb (list or tuple, optional): RGB color for dunder methods (e.g., __init__).
        """
        super().__init__(document)

        style_keyword = get_text_format([213, 95, 222], "bold")  # Purple
        style_operator = get_text_format([255, 255, 255])
        style_braces = get_text_format([255, 255, 255])
        style_def_class = get_text_format([97, 175, 239], "bold")  # Purple
        style_quotation_single = get_text_format([120, 120, 120])
        style_quotation_double = get_text_format([110, 110, 110])
        style_string = get_text_format([137, 202, 120])  # Soft Green
        style_function_call = get_text_format([97, 175, 239])  # Soft Blue
        style_comment = get_text_format([128, 128, 128])
        style_self = get_text_format([220, 105, 225], "bold")
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
        self.quotation_single = (ui_qt.QtLib.QtCore.QRegExp("'''"), 1, style_quotation_double)
        self.quotation_double = (ui_qt.QtLib.QtCore.QRegExp('"""'), 2, style_quotation_double)

        # Rules
        rules = []
        rules += [(rf"\b{word}\b", 0, style_keyword) for word in self.keywords]
        rules += [(rf"{operator}", 0, style_operator) for operator in self.operators]
        rules += [(rf"{brace}", 0, style_braces) for brace in self.braces]
        rules += [
            # 'self'
            (r"\bself\b", 0, style_self),
            # Double-quoted string
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, style_quotation_single),
            # Single-quoted string
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, style_quotation_single),
            # Function Call
            (r"\b\w+\s*(?=\()", 0, style_function_call),
            # Dunder methods
            (r"\b__(\w+)__\b", 0, style_dunder),
            # 'def' followed by an identifier
            (r"\bdef\b\s*(\w+)", 1, style_def_class),
            # 'class' followed by an identifier
            (r"\bclass\b\s*(\w+)", 1, style_def_class),
            # Numeric literals
            (r"\b[+-]?[0-9]+[lL]?\b", 0, style_number),
            (r"\b[+-]?0[xX][0-9A-Fa-f]+[lL]?\b", 0, style_number),
            (r"\b[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b", 0, style_number),
            # Strings Non-comments
            (r'"[^"]*"|"""[^"]*"""', 0, style_string),
            (r"'[^']*'|'''[^']*'''", 0, style_string),
            # From '#' until a newline
            (r"#[^\n]*", 0, style_comment),
        ]
        rules += [(rf"(?<!\bdef )\b{dunder}\b", 0, style_dunder) for dunder in self.dunder_methods]
        # Build a QRegExp for each pattern
        self.rules = [
            (ui_qt.QtLib.QtCore.QRegExp(regex_pattern), index, style) for (regex_pattern, index, style) in rules
        ]

    def highlightBlock(self, text):
        """
        Apply syntax highlighting to the given block of text.
        Args:
            text (str): The text to be syntax highlighted.
        """
        if ui_qt.IS_PYSIDE6:
            # Apply syntax formatting based on rules
            for expression, nth, format_str in self.rules:
                # Create QRegularExpression object for the pattern
                regex = expression

                # Find all matches in the text
                match_iterator = regex.globalMatch(text)
                while match_iterator.hasNext():
                    match = match_iterator.next()
                    start = match.capturedStart(nth)
                    length = match.capturedLength(nth)
                    self.setFormat(start, length, format_str)

            # Apply multi-line string matching
            in_multiline = self.match_multiline(text, *self.quotation_single)
            if not in_multiline:
                self.match_multiline(text, *self.quotation_double)

            self.setCurrentBlockState(0)
        else:
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
        if ui_qt.IS_PYSIDE6:
            # If inside a multi-line string, start from the beginning of the text
            if self.previousBlockState() == in_state:
                start = 0
                add = 0
            # Otherwise, look for the delimiter in the current line
            else:
                match_iterator = delimiter.globalMatch(text)
                if match_iterator.hasNext():
                    match = match_iterator.next()
                    start = match.capturedStart()
                    add = match.capturedLength()
                else:
                    start = -1
                    add = 0

            # As long as there's a delimiter match on this line...
            while start >= 0:
                match_iterator = delimiter.globalMatch(text, start + add)
                if match_iterator.hasNext():
                    end_match = match_iterator.next()
                    end_start = end_match.capturedStart()
                    if end_start >= add:  # Ending delimiter on this line?
                        length = end_start - start + add + end_match.capturedLength()
                        self.setCurrentBlockState(0)
                        self.setFormat(start, length, style)  # Apply style
                    # Multi-line string continues
                    else:
                        self.setCurrentBlockState(in_state)
                        length = len(text) - start + add
                        self.setFormat(start, length, style)  # Apply style
                        break  # String continues to the next line
                    start = (
                        delimiter.globalMatch(text, start + length).next().capturedStart()
                    )  # Continue searching on the next line
                else:
                    self.setCurrentBlockState(in_state)
                    length = len(text) - start + add
                    self.setFormat(start, length, style)  # Apply style
                    break  # String continues to the next line

            return self.currentBlockState() == in_state
        else:
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


class LogSyntaxHighlighter(ui_qt.QtGui.QSyntaxHighlighter):
    """Custom highlighter for log messages."""

    def __init__(self, document):
        """
        Initializes the syntax highlighter with predefined text formats.

        Sets up text formats for timestamps, log levels, messages, and
        initializes a list for additional custom regex patterns and formats.

        Args:
            document: A QTextDocument instance that this highlighter will be applied to.
        """
        super().__init__(document)

        self.date_format = get_text_format([160, 160, 160])  # Light Grey
        self.level_formats = {
            "SUCCESS": get_text_format([0, 255, 0]),  # Green - Custom Level
            "OPERATION": get_text_format([173, 216, 230]),  # Light Blue - Custom Level
            "DEBUG": get_text_format([128, 128, 128]),  # Grey
            "INFO": get_text_format([255, 255, 235]),  # Light Yellow
            "WARNING": get_text_format([255, 255, 0]),  # Yellow
            "ERROR": get_text_format([255, 127, 127]),  # Light Red
            "CRITICAL": get_text_format([255, 0, 0], style="bold"),  # Solid Red
        }
        self.message_format = get_text_format([255, 255, 255])  # White - Message after the severity level

        # Dictionary to store additional patterns and formats
        self.custom_patterns = []

    def add_pattern(self, pattern, text_format, capture_group=0):
        """
        Add a custom pattern and its format to the highlighter.

        Args:
            pattern (str): The regular expression pattern to match.
            text_format (QTextCharFormat): The format to apply to matches.
            capture_group (int, optional): Captured group index to format. Defaults to the full match.
        """
        regex = ui_qt.QtCore.QRegularExpression(pattern)
        self.custom_patterns.append((regex, text_format, int(capture_group)))

    def highlightBlock(self, text):
        """
        Applies syntax highlighting to a block of log text.

        Highlights specific parts of the text, including:
          - A timestamp at the beginning of the line (format HH:MM:SS).
          - Log levels enclosed in square brackets (e.g., [INFO], [ERROR]).
          - Custom regex patterns defined in `self.custom_patterns`.

        Uses predefined text formats such as `self.date_format`, `self.level_formats`,
        and `self.message_format` to style the matched text portions.

        Args:
            text (str): A single line of text to be highlighted.
        """
        # Match the date (e.g., 12:34:56)
        date_pattern = r"^\d{2}:\d{2}:\d{2}"
        date_match = ui_qt.QtCore.QRegularExpression(date_pattern).match(text)
        if date_match.hasMatch():
            start = date_match.capturedStart()
            length = date_match.capturedLength()
            self.setFormat(start, length, self.date_format)

        # Match the log level (e.g., [INFO])
        levels = "|".join(self.level_formats.keys())  # Formats levels for regex. e.g. "level1|level2|level3"
        level_pattern = rf"\[({levels})\]"
        level_match = ui_qt.QtCore.QRegularExpression(level_pattern).match(text)
        if level_match.hasMatch():
            start = level_match.capturedStart()
            length = level_match.capturedLength()
            level = level_match.captured(1)
            self.setFormat(start, length, self.level_formats.get(level, self.message_format))

        # Apply custom patterns
        for regex, text_format, capture_group in self.custom_patterns:
            match_iter = regex.globalMatch(text)  # Get all matches for the pattern
            while match_iter.hasNext():
                match = match_iter.next()
                start = match.capturedStart(capture_group)
                length = match.capturedLength(capture_group)
                if start < 0 or length < 1:
                    continue
                self.setFormat(start, length, text_format)


if __name__ == "__main__":
    from gt.ui import qt_utils

    # Python Syntax Highlighter Test --------------------------------------------------------
    def test_python_highlighter():
        import inspect
        import sys

        with qt_utils.QtApplicationContext():
            main_window = ui_qt.QtWidgets.QMainWindow()

            qt_utils.resize_to_screen(main_window, percentage=40)
            qt_utils.center_window(main_window)
            main_window.setStyleSheet("QTextEdit { background-color: #1D1D1D; color: #ffffff; }")
            text_edit = ui_qt.QtWidgets.QTextEdit(main_window)
            highlighter = PythonSyntaxHighlighter(text_edit.document())
            main_window.setCentralWidget(text_edit)
            mocked_text = '# Transform Data for "pSphere1":\n' + inspect.getsource(sys.modules[__name__])
            text_edit.setText(mocked_text)
            main_window.show()

    # Log Syntax Highlighter Test ----------------------------------------------------------
    def test_log_highlighter():
        with qt_utils.QtApplicationContext():
            main_window = ui_qt.QtWidgets.QMainWindow()

            qt_utils.resize_to_screen(main_window, percentage=40)
            qt_utils.center_window(main_window)
            main_window.setStyleSheet("QTextEdit { background-color: #1D1D1D; color: #ffffff; }")
            text_edit = ui_qt.QtWidgets.QTextEdit(main_window)
            highlighter = LogSyntaxHighlighter(text_edit.document())
            # Add Custom Formats
            ip_format = get_text_format([0, 191, 255])  # Deep Sky Blue
            highlighter.add_pattern(r"\b\d{1,3}(\.\d{1,3}){3}\b", ip_format)
            url_format = get_text_format([255, 140, 0])  # Dark Orange
            highlighter.add_pattern(r"https?://[^\s]+", url_format)
            # Make it not editable
            text_edit.setReadOnly(True)
            main_window.setCentralWidget(text_edit)
            mocked_logs = [
                "12:00:00 - [DEBUG] - This is a debug message.",
                "12:01:00 - [SUCCESS] - This is a custom success message.",
                "12:02:00 - [INFO] - This is an info message.",
                "12:03:00 - [WARNING] - This is a warning message.",
                "12:04:00 - [ERROR] - This is an error message.",
                "12:05:00 - [CRITICAL] - This is a critical message.",
                "12:05:00 - [CRITICAL] - Test 192.168.0.1 as a highlighted IP.",
                "12:05:00 - [CRITICAL] - Test https://www.github.com/ as a highlighted website.",
                "A test message that don't match the regex set for the log syntax.",
            ]
            text_edit.append("\n".join(mocked_logs))
            main_window.show()

    # Tests: ----------------------------------------------------------------------------------
    # test_python_highlighter()
    test_log_highlighter()
