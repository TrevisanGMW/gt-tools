"""
Option Window - Generic reusable builder for quick "option box" style windows.

This module provides a small, self-contained window class used to quickly assemble
Maya-style option windows (the little box to the right of a menu item) for utilities
and tools. It focuses on actions rather than persistent preferences, letting a caller
populate a window with comboboxes, checkboxes, buttons and button grids in just a few
lines, without manually building layouts each time.

Import Line:
    import gt.ui.option_window as ui_option_window

Use Example:
    window = ui_option_window.OptionWindow(title="Delete Keyframes",
                                           object_name="gtDeleteKeyframesOptions")
    scope_combo = window.add_combobox("Scope", ["Selected Objects", "All Objects"])
    window.add_button("Delete Keyframes", command=lambda: run(scope_combo), variant="primary")
    window.show_window()
"""

import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as qt_utils
import gt.ui.qt_import as ui_qt
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Button variants mapped to the object names used by the stylesheet.
BUTTON_VARIANTS = ("normal", "primary", "warning", "success")


class OptionWindow(ui_qt.QtWidgets.QDialog):
    """
    Generic option window used to quickly build small action/option dialogs.

    The window is non-modal so the user can keep interacting with the Maya scene
    (selecting objects, scrubbing the timeline) while it is open. Only one window
    per ``object_name`` is kept alive at a time, so reopening replaces the old one.

    Attributes:
        controls (dict): Map of control key to the created widget for later lookup.
    """

    LABEL_WIDTH = 110
    CONTROL_HEIGHT = 24
    BUTTON_HEIGHT = 28

    def __init__(self, title, object_name, icon=None, description=None, parent=None, version=None):
        """
        Initializes the OptionWindow.

        Args:
            title (str): Window title (also used as the header label).
            object_name (str): Stable Qt object name. Used to keep the window a
                singleton (reopening closes the previous instance with the same name).
            icon (str, optional): Path to a window icon resource.
            description (str, optional): Short helper text shown under the header.
            parent (QWidget, optional): Parent widget. When omitted, the Maya main
                window is used if available.
            version (str, optional): Optional version appended to the window title.
        """
        if parent is None:
            parent = self._resolve_maya_parent()
        super().__init__(parent=parent)

        self.controls = {}
        self._title = title

        window_title = title
        if version:
            window_title = f"{title} - (v{version})"

        self.setObjectName(object_name)
        self.setWindowTitle(window_title)
        self.setModal(False)
        self.setWindowFlags(self.windowFlags() | ui_qt.QtLib.WindowFlag.Tool)
        self.setAttribute(self._get_delete_on_close_attribute(), True)
        if icon:
            self.setWindowIcon(ui_qt.QtGui.QIcon(icon))
        self.setStyleSheet(self._build_stylesheet())

        self._close_existing_windows()

        self._main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        self._main_layout.setContentsMargins(12, 12, 12, 12)
        self._main_layout.setSpacing(6)

        if description:
            self.add_label(description)

    # ------------------------------------------------------------------ helpers

    @staticmethod
    def _get_delete_on_close_attribute():
        """
        Resolves the WA_DeleteOnClose attribute across PySide2 and PySide6.

        Returns:
            Qt.WidgetAttribute: The delete-on-close widget attribute.
        """
        if ui_qt.IS_PYSIDE6:
            return ui_qt.QtCore.Qt.WidgetAttribute.WA_DeleteOnClose
        return ui_qt.QtCore.Qt.WA_DeleteOnClose

    @staticmethod
    def _resolve_maya_parent():
        """
        Resolves the Maya main window to use as a parent when available.

        Returns:
            QWidget or None: Maya main window if running inside Maya, otherwise None.
        """
        try:
            return qt_utils.get_maya_main_window()
        except Exception as exception:
            logger.debug(f'Unable to resolve Maya main window. Issue: "{exception}".')
            return None

    def _close_existing_windows(self):
        """Closes any previously opened OptionWindow that shares this object name."""
        object_name = self.objectName()
        if not object_name:
            return
        try:
            for widget in ui_qt.QtWidgets.QApplication.allWidgets():
                if widget is self:
                    continue
                if isinstance(widget, OptionWindow) and widget.objectName() == object_name:
                    widget.close()
                    widget.deleteLater()
        except Exception as exception:
            logger.debug(f'Unable to close existing option windows. Issue: "{exception}".')

    def _build_field_row(self, label, control):
        """
        Adds a labeled row (label on the left, control on the right) to the window.

        Args:
            label (str): Row label text.
            control (QWidget): Control widget placed next to the label.
        """
        row_layout = ui_qt.QtWidgets.QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(6)
        label_widget = ui_qt.QtWidgets.QLabel(label)
        label_widget.setObjectName("optionFieldLabel")
        label_widget.setMinimumWidth(self.LABEL_WIDTH)
        row_layout.addWidget(label_widget)
        row_layout.addWidget(control, stretch=1)
        self._main_layout.addLayout(row_layout)

    def _create_button(self, spec):
        """
        Creates a styled push button from a spec dictionary.

        Args:
            spec (dict): Button description with keys:
                label (str): Button text.
                command (callable): Called when the button is clicked.
                variant (str, optional): One of BUTTON_VARIANTS. Defaults to "normal".
                tooltip (str, optional): Tooltip text.

        Returns:
            QPushButton: The created button.
        """
        variant = spec.get("variant", "normal")
        if variant not in BUTTON_VARIANTS:
            logger.debug(f'Unknown button variant "{variant}". Falling back to "normal".')
            variant = "normal"
        button = ui_qt.QtWidgets.QPushButton(spec.get("label", ""))
        button.setObjectName(f"option_{variant}_button")
        button.setMinimumHeight(self.BUTTON_HEIGHT)
        if spec.get("tooltip"):
            button.setToolTip(spec.get("tooltip"))
        command = spec.get("command")
        if callable(command):
            button.clicked.connect(lambda: self._run_command(command))
        return button

    @staticmethod
    def _run_command(command):
        """
        Runs a button command, logging any exception instead of crashing the UI.

        Args:
            command (callable): The command to execute.
        """
        try:
            command()
        except Exception as exception:
            logger.warning(f'Option action failed. Issue: "{exception}".')

    # -------------------------------------------------------------- public build

    def add_label(self, text):
        """
        Adds a wrapped description/helper label to the window.

        Args:
            text (str): Label text.

        Returns:
            QLabel: The created label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setObjectName("optionDescription")
        label.setWordWrap(True)
        self._main_layout.addWidget(label)
        return label

    def add_section(self, label):
        """
        Adds a section separator with a label.

        Args:
            label (str): Section label text.

        Returns:
            QLabel: The created section label.
        """
        section = ui_qt.QtWidgets.QLabel(label)
        section.setObjectName("optionSection")
        self._main_layout.addSpacing(2)
        self._main_layout.addWidget(section)
        return section

    def add_combobox(self, label, items, default=None, tooltip=None, key=None):
        """
        Adds a labeled combobox.

        Args:
            label (str): Row label text.
            items (list): List of string options.
            default (str, optional): Item selected by default.
            tooltip (str, optional): Tooltip text.
            key (str, optional): Lookup key stored in ``controls``. Defaults to label.

        Returns:
            QComboBox: The created combobox.
        """
        combo = ui_qt.QtWidgets.QComboBox()
        combo.setMinimumHeight(self.CONTROL_HEIGHT)
        for item in items:
            combo.addItem(str(item))
        if default is not None and default in items:
            combo.setCurrentText(str(default))
        if tooltip:
            combo.setToolTip(tooltip)
        self._build_field_row(label, combo)
        self.controls[key or label] = combo
        return combo

    def add_checkbox(self, label, checked=False, tooltip=None, key=None):
        """
        Adds a checkbox.

        Args:
            label (str): Checkbox label text.
            checked (bool, optional): Initial checked state. Defaults to False.
            tooltip (str, optional): Tooltip text.
            key (str, optional): Lookup key stored in ``controls``. Defaults to label.

        Returns:
            QCheckBox: The created checkbox.
        """
        checkbox = ui_qt.QtWidgets.QCheckBox(label)
        checkbox.setChecked(bool(checked))
        if tooltip:
            checkbox.setToolTip(tooltip)
        self._main_layout.addWidget(checkbox)
        self.controls[key or label] = checkbox
        return checkbox

    def add_button(self, label, command, variant="normal", tooltip=None):
        """
        Adds a single full-width button.

        Args:
            label (str): Button text.
            command (callable): Called when the button is clicked.
            variant (str, optional): One of BUTTON_VARIANTS. Defaults to "normal".
            tooltip (str, optional): Tooltip text.

        Returns:
            QPushButton: The created button.
        """
        button = self._create_button(
            {"label": label, "command": command, "variant": variant, "tooltip": tooltip}
        )
        self._main_layout.addWidget(button)
        return button

    def add_button_row(self, specs):
        """
        Adds a horizontal row of buttons.

        Args:
            specs (list): List of button spec dictionaries (see ``_create_button``).

        Returns:
            list: The created buttons in order.
        """
        row_layout = ui_qt.QtWidgets.QHBoxLayout()
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(4)
        buttons = []
        for spec in specs:
            button = self._create_button(spec)
            row_layout.addWidget(button)
            buttons.append(button)
        self._main_layout.addLayout(row_layout)
        return buttons

    def add_button_grid(self, button_rows, label=None):
        """
        Adds a grid of buttons. Useful for spatial pickers such as pivot anchors.

        Args:
            button_rows (list): List of rows, where each row is a list of button
                spec dictionaries (see ``_create_button``). Use ``None`` for an
                empty cell.
            label (str, optional): Optional section label shown above the grid.

        Returns:
            list: Flat list of the created buttons (skipping empty cells).
        """
        if label:
            self.add_section(label)
        grid_layout = ui_qt.QtWidgets.QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(4)
        buttons = []
        for row_index, row in enumerate(button_rows):
            for column_index, spec in enumerate(row):
                if not spec:
                    continue
                button = self._create_button(spec)
                grid_layout.addWidget(button, row_index, column_index)
                buttons.append(button)
        self._main_layout.addLayout(grid_layout)
        return buttons

    def show_window(self):
        """Sizes, centers and shows the window."""
        self.adjustSize()
        qt_utils.center_window(self)
        self.show()

    # --------------------------------------------------------------- stylesheet

    @staticmethod
    def _build_stylesheet():
        """
        Builds the window stylesheet.

        Returns:
            str: Combined Maya base stylesheet and option-window styling.
        """
        return ui_res_lib.Stylesheet.maya_dialog_base + """
            QLabel#optionSection { color: #aaaaaa; font-weight: bold; }
            QLabel#optionDescription { color: #aaaaaa; font-style: italic; }
            QLabel#optionFieldLabel { color: #dddddd; }
            QCheckBox { color: #dddddd; }
            QComboBox { background-color: #2b2b2b; border: 1px solid #444444; padding: 1px 4px; }
            QPushButton#option_normal_button {
                background-color: #5c5c5c; border: 1px solid #444444; color: #dddddd; padding: 2px 6px;
            }
            QPushButton#option_normal_button:hover { background-color: #696969; }
            QPushButton#option_primary_button {
                background-color: #9a9a9a; border: 1px solid #444444; color: #202020; padding: 2px 6px;
            }
            QPushButton#option_primary_button:hover { background-color: #aaaaaa; }
            QPushButton#option_warning_button {
                background-color: #7d5340; border: 1px solid #444444; color: #f0f0f0; padding: 2px 6px;
            }
            QPushButton#option_warning_button:hover { background-color: #8c5e48; }
            QPushButton#option_success_button {
                background-color: #4f6d4f; border: 1px solid #444444; color: #f0f0f0; padding: 2px 6px;
            }
            QPushButton#option_success_button:hover { background-color: #5a7c5a; }
            QPushButton:pressed { background-color: #4b4b4b; }
        """


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        demo_window = OptionWindow(
            title="Sample Options",
            object_name="gtSampleOptions",
            description="Demonstration of the generic option window builder.",
        )
        demo_window.add_combobox("Scope", ["Selected Objects", "All Objects"])
        demo_window.add_checkbox("Include children", checked=True)
        demo_window.add_button("Primary Action", command=lambda: print("primary"), variant="primary")
        demo_window.add_button_row(
            [
                {"label": "Action A", "command": lambda: print("a")},
                {"label": "Action B", "command": lambda: print("b")},
            ]
        )
        demo_window.show_window()
