"""Add Offset Transform view."""

import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib


class AddOffsetTransformView(metaclass=qt_utils.MayaWindowMeta):
    """Qt interface for adding offset transforms."""

    def __init__(self, parent=None, version=None):
        """Initializes the view.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version.
        """
        super().__init__(parent=parent)
        title = "Add Offset Transform"
        if version:
            title += " - (v{})".format(version)
        self.setWindowTitle(title)
        self.setMinimumWidth(390)
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_add_inbetween))
        self.setStyleSheet(ui_res_lib.Stylesheet.maya_dialog_base + ui_res_lib.Stylesheet.combobox_base)
        self._build_widgets()
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds the interface with padded cards and outer margins."""
        layout = ui_qt.QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(10)
        description = ui_qt.QtWidgets.QLabel(
            "Insert a group, joint, or locator above each selected object without changing its world-space pose."
        )
        description.setWordWrap(True)
        layout.addWidget(description)

        settings_group = ui_qt.QtWidgets.QGroupBox("Offset Settings")
        settings_layout = ui_qt.QtWidgets.QGridLayout(settings_group)
        settings_layout.setContentsMargins(12, 14, 12, 12)
        settings_layout.setHorizontalSpacing(10)
        settings_layout.setVerticalSpacing(10)
        self.transform_type_combo = ui_qt.QtWidgets.QComboBox()
        self.transform_type_combo.addItems(["Group", "Joint", "Locator"])
        self.pivot_source_combo = ui_qt.QtWidgets.QComboBox()
        self.pivot_source_combo.addItems(["Selection", "Parent"])
        self.transform_suffix_field = ui_qt.QtWidgets.QLineEdit()
        self.transform_suffix_field.setPlaceholderText("offset")
        self.color_button = ui_qt.QtWidgets.QPushButton("Choose Color...")
        self.color_swatch = ui_qt.QtWidgets.QFrame()
        self.color_swatch.setFixedSize(42, 24)
        self.color_swatch.setFrameShape(ui_qt.QtLib.FrameStyle.StyledPanel)
        self.color_swatch.setToolTip("Outliner color assigned to newly created offsets.")
        settings_layout.addWidget(ui_qt.QtWidgets.QLabel("Transform Type"), 0, 0)
        settings_layout.addWidget(self.transform_type_combo, 0, 1)
        settings_layout.addWidget(ui_qt.QtWidgets.QLabel("Match Pivot From"), 1, 0)
        settings_layout.addWidget(self.pivot_source_combo, 1, 1)
        settings_layout.addWidget(ui_qt.QtWidgets.QLabel("New Transform Suffix"), 2, 0)
        settings_layout.addWidget(self.transform_suffix_field, 2, 1)
        settings_layout.addWidget(ui_qt.QtWidgets.QLabel("Outliner Color"), 3, 0)
        color_layout = ui_qt.QtWidgets.QHBoxLayout()
        color_layout.setSpacing(6)
        color_layout.addWidget(self.color_swatch)
        color_layout.addWidget(self.color_button, 1)
        settings_layout.addLayout(color_layout, 3, 1)
        layout.addWidget(settings_group)

        pivot_hint = ui_qt.QtWidgets.QLabel(
            "Selection matches the new offset to each selected object. "
            "Parent matches it to the object's current parent."
        )
        pivot_hint.setWordWrap(True)
        pivot_hint.setStyleSheet("color: #999999;")
        layout.addWidget(pivot_hint)

        button_layout = ui_qt.QtWidgets.QHBoxLayout()
        button_layout.setSpacing(8)
        self.reset_button = ui_qt.QtWidgets.QPushButton("Reset Settings")
        self.create_button = ui_qt.QtWidgets.QPushButton("Add Offset Transform")
        self.reset_button.setMinimumHeight(40)
        self.reset_button.setStyleSheet("QPushButton { padding-left: 18px; padding-right: 18px; }")
        self.create_button.setMinimumHeight(40)
        self.create_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright)
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.create_button, 1)
        layout.addLayout(button_layout)

    def set_color(self, color):
        """Updates the color swatch.

        Args:
            color (list): RGB float components.
        """
        red = int(float(color[0]) * 255)
        green = int(float(color[1]) * 255)
        blue = int(float(color[2]) * 255)
        self.color_swatch.setStyleSheet(
            "background-color: rgb({0}, {1}, {2}); border: 1px solid #777777;".format(red, green, blue)
        )


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = AddOffsetTransformView()
        window.show()
