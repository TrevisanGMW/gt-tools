"""Qt view for Transfer Transforms."""

from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib


class TransferTransformsView(metaclass=MayaWindowMeta):
    """Main window for transferring and storing transform values."""

    ATTRIBUTE_LABELS = {
        "tx": "Translate X",
        "ty": "Translate Y",
        "tz": "Translate Z",
        "rx": "Rotate X",
        "ry": "Rotate Y",
        "rz": "Rotate Z",
        "sx": "Scale X",
        "sy": "Scale Y",
        "sz": "Scale Z",
    }

    def __init__(self, parent=None, version=None):
        """Initializes the window.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version.
        """
        super().__init__(parent=parent)
        self.setWindowTitle("Transfer Transforms" + (f" - (v{version})" if version else ""))
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_transfer_transforms))
        self.setMinimumWidth(340)
        self.attribute_widgets = {}
        self.clipboard_fields = {}
        self.setStyleSheet(ui_res_lib.Stylesheet.maya_dialog_base)
        self._build_widgets()
        self.adjustSize()
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds all interface widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        title_bar = ui_qt.QtWidgets.QWidget()
        title_bar.setObjectName("transfer_transforms_title_bar")
        title_bar.setStyleSheet(
            "QWidget#transfer_transforms_title_bar { background-color: #5A5A5A; }"
            "QPushButton { background-color: transparent; border: 0; border-left: 1px solid #707070; "
            "padding: 6px 12px; }"
            "QPushButton:hover { background-color: #666666; }"
            "QPushButton:pressed { background-color: #484848; }"
        )
        title_layout = ui_qt.QtWidgets.QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(0)
        title_label = ui_qt.QtWidgets.QLabel("Transfer Transforms")
        title_font = title_label.font()
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.reset_button = ui_qt.QtWidgets.QPushButton("Reset")
        self.help_button = ui_qt.QtWidgets.QPushButton("Help")
        self.reset_button.setToolTip("Reset all persistent options to their defaults.")
        self.help_button.setToolTip("Show Transfer Transforms usage instructions.")
        title_layout.addWidget(title_label, 1)
        title_layout.addWidget(self.reset_button)
        title_layout.addWidget(self.help_button)
        main_layout.addWidget(title_bar)

        main_layout.addWidget(self._build_transform_options())
        main_layout.addWidget(self._build_side_section())

        file_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.export_button = ui_qt.QtWidgets.QPushButton("Export Transforms")
        self.import_button = ui_qt.QtWidgets.QPushButton("Import Transforms")
        file_layout.addWidget(self.export_button)
        file_layout.addWidget(self.import_button)
        main_layout.addLayout(file_layout)

        self.transfer_button = ui_qt.QtWidgets.QPushButton("Transfer (Source / Targets)")
        self.transfer_button.setStyleSheet(ui_res_lib.Stylesheet.btn_push_bright)
        self.transfer_button.setToolTip("Transfer from the first selected object to every later selection.")
        main_layout.addWidget(self.transfer_button)
        main_layout.addWidget(self.create_separator("Copy and Paste Transforms"))
        main_layout.addLayout(self._build_clipboard_grid())

        clipboard_button_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.get_button = ui_qt.QtWidgets.QPushButton("Get TRS")
        self.set_button = ui_qt.QtWidgets.QPushButton("Set TRS")
        clipboard_button_layout.addWidget(self.get_button)
        clipboard_button_layout.addWidget(self.set_button)
        main_layout.addLayout(clipboard_button_layout)

        self.status_label = ui_qt.QtWidgets.QLabel("Ready.")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

    def _build_transform_options(self):
        """Builds channel enable and invert controls.

        Returns:
            QWidget: Transform options widget.
        """
        container = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(3)
        channel_header = ui_qt.QtWidgets.QLabel("Channel")
        transfer_header = ui_qt.QtWidgets.QLabel("Transfer")
        invert_header = ui_qt.QtWidgets.QLabel("Invert")
        header_style = "background-color: #505050; padding: 3px;"
        for header in (channel_header, transfer_header, invert_header):
            header.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            header.setStyleSheet(header_style)
            header.setSizePolicy(
                ui_qt.QtWidgets.QSizePolicy.Expanding,
                ui_qt.QtWidgets.QSizePolicy.Preferred,
            )
        layout.addWidget(channel_header, 0, 0)
        layout.addWidget(transfer_header, 0, 1)
        layout.addWidget(invert_header, 0, 2)
        row = 1
        for attribute, label in self.ATTRIBUTE_LABELS.items():
            if attribute in ("rx", "sx"):
                line = ui_qt.QtWidgets.QFrame()
                line.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
                line.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)
                layout.addWidget(line, row, 0, 1, 3)
                row += 1
            enabled_checkbox = ui_qt.QtWidgets.QCheckBox()
            inverted_checkbox = ui_qt.QtWidgets.QCheckBox()
            channel_label = ui_qt.QtWidgets.QLabel(label)
            channel_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            layout.addWidget(channel_label, row, 0)
            layout.addWidget(enabled_checkbox, row, 1, ui_qt.QtLib.AlignmentFlag.AlignCenter)
            layout.addWidget(inverted_checkbox, row, 2, ui_qt.QtLib.AlignmentFlag.AlignCenter)
            self.attribute_widgets[attribute] = {
                "enabled": enabled_checkbox,
                "inverted": inverted_checkbox,
            }
            row += 1
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)
        return container

    def _build_side_section(self):
        """Builds side-tag and mirror controls.

        Returns:
            QWidget: Side transfer widget.
        """
        group = ui_qt.QtWidgets.QGroupBox("Side-to-Side Transfer")
        layout = ui_qt.QtWidgets.QGridLayout(group)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(6)
        left_tag_label = ui_qt.QtWidgets.QLabel("Left Side Tag")
        right_tag_label = ui_qt.QtWidgets.QLabel("Right Side Tag")
        left_tag_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        right_tag_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(left_tag_label, 0, 0)
        layout.addWidget(right_tag_label, 0, 1)
        self.left_tag_field = ui_qt.QtWidgets.QLineEdit()
        self.right_tag_field = ui_qt.QtWidgets.QLineEdit()
        for field in (self.left_tag_field, self.right_tag_field):
            field.setMinimumWidth(100)
            field.setSizePolicy(
                ui_qt.QtWidgets.QSizePolicy.Ignored,
                ui_qt.QtWidgets.QSizePolicy.Preferred,
            )
        self.left_tag_field.setPlaceholderText("L_")
        self.right_tag_field.setPlaceholderText("R_")
        layout.addWidget(self.left_tag_field, 1, 0)
        layout.addWidget(self.right_tag_field, 1, 1)
        self.right_to_left_button = ui_qt.QtWidgets.QPushButton("From Right to Left")
        self.left_to_right_button = ui_qt.QtWidgets.QPushButton("From Left to Right")
        layout.addWidget(self.right_to_left_button, 2, 0, 1, 2)
        layout.addWidget(self.left_to_right_button, 3, 0, 1, 2)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        return group

    def _build_clipboard_grid(self):
        """Builds editable session TRS fields.

        Returns:
            QGridLayout: Clipboard field layout.
        """
        layout = ui_qt.QtWidgets.QGridLayout()
        layout.setHorizontalSpacing(5)
        axis_colors = {"X": "#7A3030", "Y": "#306E3A", "Z": "#303F7A"}
        for column, axis in enumerate(("X", "Y", "Z"), start=1):
            label = ui_qt.QtWidgets.QLabel(axis)
            label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            label.setStyleSheet(f"background-color: {axis_colors.get(axis)}; padding: 2px;")
            layout.addWidget(label, 0, column)
        validator = ui_qt.QtGui.QDoubleValidator(self)
        validator.setNotation(ui_qt.QtGui.QDoubleValidator.StandardNotation)
        for row, prefix in enumerate(("T", "R", "S"), start=1):
            row_label = ui_qt.QtWidgets.QLabel(prefix)
            row_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            layout.addWidget(row_label, row, 0)
            for column, axis in enumerate(("x", "y", "z"), start=1):
                attribute = f"{prefix.lower()}{axis}"
                field = ui_qt.QtWidgets.QLineEdit()
                field.setMinimumWidth(100)
                field.setSizePolicy(
                    ui_qt.QtWidgets.QSizePolicy.Ignored,
                    ui_qt.QtWidgets.QSizePolicy.Preferred,
                )
                field.setValidator(validator)
                field.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignRight)
                self.clipboard_fields[attribute] = field
                layout.addWidget(field, row, column)
        for column in range(1, 4):
            layout.setColumnStretch(column, 1)
        return layout

    @staticmethod
    def create_separator(text):
        """Creates a centered section separator.

        Args:
            text (str): Section label.

        Returns:
            QWidget: Separator widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(7)
        for index in range(3):
            if index == 1:
                label = ui_qt.QtWidgets.QLabel(text)
                label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
                layout.addWidget(label)
            else:
                line = ui_qt.QtWidgets.QFrame()
                line.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
                line.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)
                layout.addWidget(line, 1)
        return widget

    def set_status(self, message, level="info"):
        """Shows concise feedback at the bottom of the window.

        Args:
            message (str): Status text.
            level (str, optional): Feedback severity.
        """
        colors = {
            "info": "#B8B8B8",
            "success": "#8BCB88",
            "warning": "#E2BE72",
            "error": "#E58A8A",
        }
        self.status_label.setStyleSheet(f"color: {colors.get(level, colors['info'])};")
        self.status_label.setText(message)

    def show_help(self):
        """Shows concise workflow instructions."""
        ui_qt.QtWidgets.QMessageBox.information(
            self,
            "Transfer Transforms Help",
            "Enable the channels to process and optionally invert their values.\n\n"
            "Transfer uses the first selected object as the source and every later selection as a target.\n\n"
            "Side-to-side transfer pairs selected objects by the Left and Right tags.\n\n"
            "Get TRS stores enabled values in the fields; Set TRS applies them to all selected objects. "
            "Import and Export store complete TRS values for selected scene objects.",
        )


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = TransferTransformsView()
        window.show()
