import gt.ui.line_text_widget as ui_line_text_widget
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as ui_qt_utils
import gt.core.logger as core_log
import gt.ui.qt_import as ui_qt
from functools import partial
import logging
import sys


class RiggerLoggingView(metaclass=ui_qt_utils.MayaWindowMeta):
    DOCK_HEIGHT_PERCENTAGE = 0.15
    DOCK_MINIMUM_HEIGHT = 60

    def __init__(self, parent=None):
        """
        Initializes the Auto Rigger Logging window.

        Args:
            parent (QWidget, optional): The parent widget for this window. Defaults to None.
        """
        super().__init__(parent)

        self.setWindowTitle("Auto Rigger Logging")
        self.setGeometry(100, 100, 800, 600)

        stylesheet = ui_res_lib.Stylesheet.scroll_bar_base
        stylesheet += ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.list_widget_base
        self.setStyleSheet(stylesheet)

        self.log_widget = ui_line_text_widget.LineTextWidget(self)
        from gt.ui.syntax_highlighter import LogSyntaxHighlighter, get_text_format

        highlighter = LogSyntaxHighlighter(self.log_widget.get_text_edit().document())

        # Add a pattern for words inside parentheses (Steps)
        redish_white = get_text_format([239, 224, 187])
        highlighter.add_pattern(r"(\s-\s\([a-zA-Z\s]+\))", redish_white)

        self.log_widget.get_text_edit().setReadOnly(True)
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.log_widget)
        self.setLayout(layout)
        self.setup_loggers()

        # Icon
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.dev_code))

        # Adjust window
        ui_qt_utils.resize_to_screen(self, percentage=20)
        ui_qt_utils.center_window(self)

        # Initial Values
        self._is_open = False

        # Enable custom context menu for the QTextEdit
        self.log_widget.get_text_edit().setContextMenuPolicy(ui_qt.QtCore.Qt.CustomContextMenu)
        self.log_widget.get_text_edit().customContextMenuRequested.connect(self.show_context_menu)

    def setup_loggers(self):
        """Gets the root logger along with all loggers belonging to the auto rigger and give them a handler"""
        # Get the logger
        root_logger = core_log.setup_root_logger()
        rigger_logger_name = core_log.get_logger_name(__name__)
        loggers = core_log.get_loggers_by_name_prefix(rigger_logger_name)
        loggers.append(root_logger)

        # Create and add the custom handler
        qt_handler = core_log.TextWidgetLogHandler(self.log_widget)
        qt_handler.setLevel(logging.DEBUG)  # Adjust level as needed
        formatter = logging.Formatter(core_log.LogFormatting.CONSOLE, datefmt=core_log.LogFormatting.CONSOLE_DATE)
        qt_handler.setFormatter(formatter)
        for logger in loggers:
            if qt_handler in logger.handlers:
                continue
            logger.addHandler(qt_handler)

    def show_if_not_visible(self, dock_to_control=None):
        """Shows the log window and optionally docks it below another Maya control.

        Args:
            dock_to_control (str, optional): Maya workspace-control name to dock
                below. This is ignored outside interactive Maya.
        """
        dock_height = self.get_dock_height(dock_to_control)
        if not self._is_open:
            if dock_height:
                self.resize(self.width(), dock_height)
            self.show()
            self._is_open = True
        elif not dock_to_control:
            # Bring the dialog to the front if it's already open
            self.raise_()
            self.activateWindow()
        if dock_to_control:
            self.dock_below_control(dock_to_control, dock_height=dock_height)

    def get_dock_height(self, target_control):
        """Gets a compact log height based on an existing Maya workspace control.

        Args:
            target_control (str): Maya workspace-control name used as the size
                reference.

        Returns:
            int or None: Desired log-pane height, or None when unavailable.
        """
        if not target_control:
            return None
        try:
            from maya import cmds

            if not cmds.workspaceControl(target_control, query=True, exists=True):
                return None
            target_height = cmds.workspaceControl(target_control, query=True, height=True)
            if not target_height:
                return None
            calculated_height = int(float(target_height) * self.DOCK_HEIGHT_PERCENTAGE)
            return max(self.DOCK_MINIMUM_HEIGHT, calculated_height)
        except Exception as exception:
            logging.getLogger(__name__).debug(
                f'Unable to determine Auto Rigger log window height. Issue: "{exception}".'
            )
            return None

    def dock_below_control(self, target_control, dock_height=None):
        """Docks this log view below an existing Maya workspace control.

        Args:
            target_control (str): Maya workspace-control name to dock below.
            dock_height (int, optional): Height to use for the docked log pane.

        Returns:
            bool: True if the log view was docked successfully.
        """
        if not target_control:
            return False
        try:
            from maya import cmds

            log_workspace_control = f"{self.objectName()}WorkspaceControl"
            if not cmds.workspaceControl(log_workspace_control, query=True, exists=True):
                return False
            if not cmds.workspaceControl(target_control, query=True, exists=True):
                return False
            cmds.workspaceControl(
                log_workspace_control,
                edit=True,
                dockToControl=(target_control, "bottom"),
            )
            if dock_height:
                cmds.workspaceControl(log_workspace_control, edit=True, resizeHeight=dock_height)
            return True
        except Exception as exception:
            logging.getLogger(__name__).debug(
                f'Unable to dock Auto Rigger log window below "{target_control}". Issue: "{exception}".'
            )
            return False

    def closeEvent(self, event):
        """
        Updates the "_is_open" variable when closing the window
        Args:
            event (QCloseEvent): The close event triggered when the window is closing.
        """
        # Reset the flag when the dialog is closed
        self._is_open = False
        super().closeEvent(event)

    def show_context_menu(self, position):
        """
        Displays a customized context menu for the log widget's text edit.

        Args:
            position (QPoint): The position (usually from a mouse event) where the context menu should appear,
                               relative to the log widget's text edit.

        Behavior:
            The menu is shown at the global screen position corresponding to the provided local position.
        """
        # Get the default context menu
        text_edit = self.log_widget.get_text_edit()

        # Create a default context menu and add logger controls to it.
        menu = text_edit.createStandardContextMenu()

        # Add a submenu for logger levels
        logger_menu = ui_qt.QtWidgets.QMenu("Set Logger Level", self)

        # Logger levels and their corresponding values
        levels = {
            "Debug": logging.DEBUG,
            "Info": logging.INFO,
            "Success": core_log.CustomSeverityLevels.SUCCESS,
            "Operation": core_log.CustomSeverityLevels.OPERATION,
            "Warning": logging.WARNING,
            "Error": logging.ERROR,
            "Critical": logging.CRITICAL,
        }

        # Add actions for each logger level
        for level_name, level_value in levels.items():
            action = ui_qt.QtLib.QtGui.QAction(level_name, self)
            action.setCheckable(True)  # Allow toggling
            action.setChecked(self.get_logger_level() == level_value)
            _func = partial(self.set_logger_level, level_value)
            action.triggered.connect(_func)
            logger_menu.addAction(action)

        existing_actions = menu.actions()
        if existing_actions:
            menu.insertMenu(existing_actions[0], logger_menu)
            menu.insertSeparator(existing_actions[0])
        else:
            menu.addMenu(logger_menu)

        # Add a 'Clear' action to the default menu
        clear_action = ui_qt.QtLib.QtGui.QAction("Clear", self)
        clear_action.triggered.connect(text_edit.clear)
        menu.addSeparator()
        menu.addAction(clear_action)

        # Show the menu at the cursor position
        exec_method = getattr(menu, "exec_", None)
        if not exec_method:
            exec_method = getattr(menu, "exec")
        exec_method(text_edit.mapToGlobal(position))

    def clear_log_widget(self):
        """Clears the text found in the log widget"""
        text_edit = self.log_widget.get_text_edit()
        text_edit.clear()

    @staticmethod
    def set_logger_level(level):
        """
        Sets the logging level of the auto rigger loggers and the root handler affecting it.
        Args:
            level (int): The severity level integer used to set the logger level.
        """
        rigger_logger_name = core_log.get_logger_name(__name__)
        loggers = core_log.get_loggers_by_name_prefix(rigger_logger_name)
        for logger in loggers:
            logger.setLevel(level)
            logger.info(f'Rigger logger level set to: "{logging.getLevelName(level)}".')
            sys.stdout.write(f'Auto Rigger logger level set to: "{logging.getLevelName(level)}"\n')
        # Change root logger handler level
        root_logger = core_log.setup_root_logger()
        for handler in root_logger.handlers:
            if isinstance(handler, core_log.TextWidgetLogHandler):
                handler.setLevel(level)

    @staticmethod
    def get_logger_level():
        """
        Gets the level of the first detected auto rigger logger.
        Returns:
            int: Logger level of the first detected auto rigger logger.
        """
        rigger_logger_name = core_log.get_logger_name(__name__)
        loggers = core_log.get_loggers_by_name_prefix(rigger_logger_name)
        for logger in loggers:
            return logger.level


if __name__ == "__main__":
    # Logging Setup
    a_logger_name = core_log.get_logger_name(__name__)
    a_logger = core_log.setup_common_logger(name=a_logger_name, propagate=False)
    a_logger.setLevel(logging.INFO)
    core_log.add_custom_log_levels()

    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext():
        window = RiggerLoggingView()
        window.show()

        core_log.add_custom_log_levels()

        logger_instance = logging.getLogger("my_logger")
        logger_instance.setLevel(logging.DEBUG)

        # Example log messages
        logger_instance.debug("This is a debug message.")
        logger_instance.operation("This is an operation message.")  # Custom level
        logger_instance.success("This is a success message.")  # Custom level
        logger_instance.info("This is an info message.")
        logger_instance.warning("This is a warning message.")
        logger_instance.error("This is an error message.")
        logger_instance.critical("This is a critical message.")
        logger_instance.critical("This is a (critical) message.")
        logger_instance.critical("[CRITICAL] - (Building) A message here")
        logger_instance.critical("[CRITICAL] - (Post Script): A message here")
        logger_instance.critical("[CRITICAL] - (Post Script): A message here (optimized)")
