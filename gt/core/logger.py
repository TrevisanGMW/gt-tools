"""
Logger Module

Import Line:
    import gt.core.logger as core_log
"""

import gt.utils.system as utils_system
import gt.core.setup as core_setup
import gt.ui.qt_import as ui_qt
import logging
import os


# Constants
PACKAGE_LOGS_DIR = "logs"
LOG_FILE_EXT = "log"


class CustomSeverityLevels:
    SUCCESS = 21
    OPERATION = 22

    @classmethod
    def get_all_levels(cls):
        """
        Returns a list of all severity level names.

        Returns:
            list[str]: A list of severity level names defined as class attributes.
        """
        return [attr for attr in dir(cls) if not attr.startswith("__") and isinstance(getattr(cls, attr), int)]

    @classmethod
    def get_levels_dict(cls):
        """
        Returns a dictionary with severity level names as keys and their values.

        Returns:
            dict[str, int]: A dictionary mapping severity level names to integer values.
        """
        return {attr: getattr(cls, attr) for attr in cls.get_all_levels()}


# Formatting
class LogFormatting:
    def __init__(self):
        """
        Constant tuple RGB values used as colors.
        """

    LOG_DATE = "%b-%d, %H:%M:%S"  # Nov-19, 12:34:56
    LOG_FILE = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"  # <date> [WARNING] - <source> - A message
    CONSOLE_DATE = "%H:%M:%S"  # 12:34:56
    CONSOLE = "%(asctime)s - [%(levelname)s] - %(message)s"  # <date> [WARNING] - A message


# New Log Severity Levels --------------------------------------------------------------------------
def add_log_level(level_name, level_num):
    """
    Adds a custom log level to the logging module and logger class.

    Args:
        level_name (str): The name of the custom log level (e.g., 'SUCCESS').
        level_num (int): The numeric value for the custom log level (e.g., 25).
    """
    if not hasattr(logging, level_name.upper()):
        logging.addLevelName(level_num, level_name.upper())

        def log_for_level(self, msg, *args, **kwargs):
            """
            Log a message at the specified log level if enabled.

            Args:
                msg (str): The log message format string.
                *args: Variable length argument list for the message formatting.
                **kwargs: Arbitrary keyword arguments passed to the logger.
            """
            if self.isEnabledFor(level_num):
                self._log(level_num, msg, args, **kwargs)

        # Attach the custom level method to the Logger class
        setattr(logging.Logger, level_name.lower(), log_for_level)


def add_custom_log_levels():
    """
    Adds all custom severity levels defined in CustomSeverityLevels to the logging module.
    """
    levels = CustomSeverityLevels.get_levels_dict()
    for level_name, level_num in levels.items():
        add_log_level(level_name, level_num)


# Logger Setup -------------------------------------------------------------------------------------
def get_logs_dir(create_if_missing=True):
    """
    Gets the path to the package "logs" directory. e.g. ".../Documents/maya/gt_tools/logs"
    Args:
        create_if_missing (bool, optional): If True, it creates a missing directory.
    Returns:
        str: Path to package prefs dir. e.g. ".../Documents/maya/gt_tools/logs"
    """
    _maya_preferences_dir = utils_system.get_maya_preferences_dir(utils_system.get_system())
    _package_parent_dir = os.path.join(_maya_preferences_dir, core_setup.PACKAGE_NAME)
    _logs_dir = os.path.join(_package_parent_dir, PACKAGE_LOGS_DIR)
    _logs_dir = _logs_dir.replace("/", "\\")
    if create_if_missing:
        if not os.path.exists(_logs_dir):
            os.makedirs(_logs_dir)
    return _logs_dir


def setup_common_logger(
    name=None,
    log_file_handler=True,
    log_file_name=None,
    log_file_ext="log",
    log_file_level=logging.DEBUG,
    log_file_msg_fmt=LogFormatting.LOG_FILE,
    log_file_date_fmt=LogFormatting.LOG_DATE,
    log_file_max_size_bytes=1024 * 1024,  # 1MB size limit
    console_handler=False,
    console_level=logging.INFO,
    console_msg_fmt=LogFormatting.CONSOLE,
    console_date_fmt=LogFormatting.CONSOLE_DATE,
    console_configure_root=True,
    clear_existing_handlers=False,
    propagate=True,
):
    """
    Sets up a logger for logging messages to both a file and the console.

    This function configures a logger to write log messages to both a log file and
    the console, with options for formatting and logging level customization.
    It ensures that duplicate handlers are not added to the logger and can be
    used with both custom file logging and console logging.

    If no `name` is provided, the root logger is configured. The log file path
    and name can be customized, and if a console handler is specified, it will
    log to the console in addition to the file.

    Args:
        name (str, optional): The name of the logger. If `None`, the root logger is used.
        log_file_handler (bool, optional): If True, a log file is created to store logged messages.
        log_file_name (str, optional): Full path or filename for the log file. If not provided, defaults
                                       to "root.log" for the root logger or a lowercase, underscore-separated
                                       version of the logger's name.
        log_file_ext (str, optional): Extension for the log file. Defaults to "log".
        log_file_level (int, optional): The logging level for the log file handler.
        log_file_msg_fmt (str, optional): Format string for log messages used in the log file.
        log_file_date_fmt (str, optional): Format the date that appears in the log messages when logging to a file.
        log_file_max_size_bytes (int, optional): The max size for the log file before becoming a backup.
                                                 Only one backup file is retained. After that it will be overwritten.
        console_handler (bool, optional): If True, a console handler is added to log messages to the console.
        console_level (int, optional): The logging level for the console handler.
        console_msg_fmt (str, optional): Format string for log messages used in the console output.
        console_date_fmt (str, optional): Format the date that appears in the log messages when logging to the console.
        console_configure_root (bool, optional): If True, configures the existing console handler found in the root.
        clear_existing_handlers (bool, optional): If True, clears existing handlers before adding new ones.
        propagate (bool, optional): If True, logged messages are propagated to parent loggers.

    Returns:
        logging.Logger: The configured logger instance.
    """
    from logging import handlers

    RotatingFileHandler = handlers.RotatingFileHandler  # Just so the class call is shorter

    # Determine logger name and file path
    logger_name = name or "root"
    logger = logging.getLogger(name)
    logger.propagate = propagate

    if clear_existing_handlers:
        for handler in logger.handlers[:]:  # Use a copy of the list to avoid modification issues
            logger.removeHandler(handler)
            handler.close()  # Close the handler if necessary

    # Determine log file path if required
    if log_file_name is None:
        log_file_name = logger_name.lower().replace(" ", "_")
    if not os.path.isabs(log_file_name):
        log_file_name = os.path.join(get_logs_dir(), f"{log_file_name}.{log_file_ext}")

    # Create and configure handlers
    handlers = []
    if log_file_handler and not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        try:
            file_handler = RotatingFileHandler(log_file_name, maxBytes=log_file_max_size_bytes, backupCount=1)
            file_handler.setLevel(log_file_level)
            handlers.append(file_handler)
        except Exception as e:
            logger.warning(f"Failed to set up file handler: {e}")

    # Set formatter and add handlers to the logger
    log_formatter = logging.Formatter(log_file_msg_fmt, datefmt=log_file_date_fmt)
    for handler in handlers:
        handler.setFormatter(log_formatter)
        logger.addHandler(handler)

    # Setup Console Handler
    console_handler_instance = None
    if console_handler:
        console_handler_instance = logging.StreamHandler()

    if console_handler_instance:
        console_formatter = logging.Formatter(console_msg_fmt, datefmt=console_date_fmt)
        console_handler_instance.setFormatter(console_formatter)

        console_handler_instance.setLevel(console_level)

        if console_handler_instance not in logger.handlers:
            logger.addHandler(console_handler_instance)

    # Configure Root Console Handler
    if console_configure_root:
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                console_handler_instance = handler
                break
        if console_handler_instance:
            console_formatter = logging.Formatter(console_msg_fmt, datefmt=console_date_fmt)
            console_handler_instance.setFormatter(console_formatter)

    return logger


def setup_root_logger(console_msg_fmt=LogFormatting.CONSOLE, console_date_fmt=LogFormatting.CONSOLE_DATE):
    """
    Returns the root logger with the expected formatting.
    Args:
        console_msg_fmt (str, optional): Format string for log messages used in the console output.
        console_date_fmt (str, optional): Format the date that appears in the log messages when logging to the console.
    Returns:
        logging.Logger: The configured root logger instance.
    """
    return setup_common_logger(
        console_msg_fmt=console_msg_fmt, console_date_fmt=console_date_fmt, clear_existing_handlers=False
    )


def get_logger_name(module_path, remove_package=True, depth=2, clear_main=True):
    """
    Generates a logger name based on a module's path, with options to modify its format.

    Args:
        module_path (str):
            The full dotted path of the module (e.g., "gt.core.utils").
        remove_package (bool, optional):
            If True, removes the package prefix (defined by `PACKAGE_MAIN_MODULE`) found in the setup module.
        depth (int, optional):
            Limits the depth of the returned logger name by keeping only the first
            `depth` segments of the module path. Defaults to 2. e.g. "core.logger" (2 elements)
        clear_main (bool, optional):
            If True, replaces "__main__" with "main" to avoid special naming for the main script. Defaults to True.

    Returns:
        str: The formatted logger name based on the provided module path and options.

    Examples:
        get_logger_name("gt.core.utils")
        # Output: 'gt.core'

        get_logger_name("gt.core.utils", depth=1)
        # Output: 'gt'

        get_logger_name("__main__", clear_main=True)
        # Output: 'main'
    """
    import gt.core.str as core_str
    import gt.core.setup as core_setup

    _module_path = module_path
    if remove_package:
        _module_path = core_str.remove_prefix(input_string=_module_path, prefix=f"{core_setup.PACKAGE_MAIN_MODULE}.")

    if "." in module_path:
        module_path_list = _module_path.split(".")
        adjusted_path_list = module_path_list[: min(depth, len(module_path_list))]
        _module_path = ".".join(adjusted_path_list)

    if clear_main and _module_path == "__main__":
        _module_path = "main"

    return _module_path


def get_loggers_by_name_prefix(prefix):
    """
    Returns a list of loggers whose names start with the given pattern.

    Args:
        prefix (str): The prefix pattern to search for in logger names.

    Returns:
        list: A list of loggers whose names start with the specified pattern.
    """
    loggers = [
        logger
        for logger in logging.Logger.manager.loggerDict.values()
        if isinstance(logger, logging.Logger) and logger.name.startswith(prefix)
    ]
    return loggers


class TextWidgetLogHandler(logging.Handler):
    def __init__(self, log_widget):
        """
        Initialize the handler with the target log widget.

        Args:
            log_widget (QTextEdit or compatible): The widget that will receive log messages.
        """
        super().__init__()
        self.log_widget = log_widget

    def emit(self, record):
        """
        Emit a log record.

        Formats the record and appends it to the associated text widget.
        If the widget has a `get_text_edit()` method, it appends via that.
        Handles the case where the widget has been deleted by disabling the handler.

        Args:
            record (logging.LogRecord): The log record to be emitted.
        """
        # Format the log message
        msg = self.format(record)

        if not self.log_widget:
            return

        try:
            # Use Duck Typing instead of isinstance to survive module reloads
            if hasattr(self.log_widget, "get_text_edit"):
                self.log_widget.get_text_edit().append(msg)
            elif hasattr(self.log_widget, "append"):
                self.log_widget.append(msg)
        except RuntimeError:
            # QTextEdit already deleted, deactivate handler
            self.log_widget = None

        # Refresh App
        ui_qt.QtWidgets.QApplication.processEvents()


if __name__ == "__main__":
    auto_rigger_logger_instance = setup_common_logger(
        name="tools.auto_rigger",
        console_handler=False,
        console_configure_root=True,
    )
    auto_rigger_logger_instance.warning("This is a test message")
    import gt.ui.line_text_widget as ui_line_text_widget
    import gt.ui.resource_library as ui_res_lib
    import gt.ui.qt_import as ui_qt

    class ExampleDialog(ui_qt.QtWidgets.QDialog):
        def __init__(self, parent=None):
            super().__init__(parent)

            self.setWindowTitle("Line Text Widget Example")
            self.setGeometry(100, 100, 800, 600)

            stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
            stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
            stylesheet += ui_res_lib.Stylesheet.list_widget_base
            self.setStyleSheet(stylesheet)

            self.log_widget = ui_line_text_widget.LineTextWidget(self)
            from gt.ui.syntax_highlighter import LogSyntaxHighlighter

            LogSyntaxHighlighter(self.log_widget.get_text_edit().document())
            self.log_widget.get_text_edit().setReadOnly(True)
            layout = ui_qt.QtWidgets.QVBoxLayout(self)
            layout.addWidget(self.log_widget)
            self.setLayout(layout)
            self.setup_logger()

        def setup_logger(self):
            # Get the logger
            logger = setup_common_logger()
            logger.setLevel(logging.DEBUG)  # Adjust level as needed

            # Create and add the custom handler
            qt_handler = TextWidgetLogHandler(self.log_widget)
            qt_handler.setLevel(logging.DEBUG)  # Adjust level as needed
            formatter = logging.Formatter(LogFormatting.CONSOLE, datefmt=LogFormatting.CONSOLE_DATE)
            qt_handler.setFormatter(formatter)
            logger.addHandler(qt_handler)

    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext():
        window = ExampleDialog()
        window.show()

        add_custom_log_levels()

        a_logger_instance = logging.getLogger("my_logger")

        # Example log messages
        a_logger_instance.success("This is a success message.")  # Custom level
        a_logger_instance.debug("This is a debug message.")
        a_logger_instance.operation("This is an operation message.")  # Custom level
        a_logger_instance.info("This is an info message.")
        a_logger_instance.warning("This is a warning message.")
        a_logger_instance.error("This is an error message.")
        a_logger_instance.critical("This is a critical message.")
