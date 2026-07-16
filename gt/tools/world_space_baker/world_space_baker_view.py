"""Responsive Qt view for World Space Baker."""

from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib


class WorldSpaceBakerView(metaclass=MayaWindowMeta):
    """Main window for extracting and baking world-space animation."""

    def __init__(self, parent=None, version=None):
        """Initializes the World Space Baker window.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version displayed in the title.
        """
        super().__init__(parent=parent)
        self.setWindowTitle("World Space Baker" + (f" - (v{version})" if version else ""))
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_world_space_baker))
        self.setMinimumWidth(320)
        self._build_widgets()
        self.resize_to_contents()
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds all interface widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        title_bar = ui_qt.QtWidgets.QWidget()
        title_bar.setObjectName("world_space_baker_title_bar")
        title_bar.setStyleSheet(
            "QWidget#world_space_baker_title_bar { background-color: #5A5A5A; }"
            "QPushButton { background-color: transparent; border: 0; border-left: 1px solid #707070; "
            "padding: 6px 12px; }"
            "QPushButton:hover { background-color: #666666; }"
            "QPushButton:pressed { background-color: #484848; }"
        )
        title_layout = ui_qt.QtWidgets.QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 0, 0)
        title_layout.setSpacing(0)
        title_label = ui_qt.QtWidgets.QLabel("World Space Baker")
        title_font = title_label.font()
        title_font.setBold(True)
        title_label.setFont(title_font)
        self.help_button = ui_qt.QtWidgets.QPushButton("Help")
        self.help_button.setToolTip("Show World Space Baker usage instructions.")
        title_layout.addWidget(title_label, 1)
        title_layout.addWidget(self.help_button)
        main_layout.addWidget(title_bar)

        main_layout.addWidget(self.create_separator("1. Target(s)"))
        target_layout = ui_qt.QtWidgets.QHBoxLayout()
        target_layout.setSpacing(6)
        self.load_selection_button = ui_qt.QtWidgets.QPushButton("Load Selection")
        self.target_status_button = ui_qt.QtWidgets.QPushButton("Not loaded yet")
        target_button_height = max(
            self.load_selection_button.sizeHint().height(),
            self.target_status_button.sizeHint().height(),
        )
        self.load_selection_button.setMinimumHeight(target_button_height)
        self.target_status_button.setMinimumHeight(target_button_height)
        self.target_status_button.setToolTip("Select the currently loaded objects.")
        self.target_status_button.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        target_layout.addWidget(self.load_selection_button, 1)
        target_layout.addWidget(self.target_status_button, 1)
        main_layout.addLayout(target_layout)

        main_layout.addWidget(self.create_separator("2. Animation Range"))
        range_layout = ui_qt.QtWidgets.QGridLayout()
        range_layout.setHorizontalSpacing(6)
        self.start_frame_spinbox = self._create_frame_spinbox()
        self.end_frame_spinbox = self._create_frame_spinbox()
        self.get_start_button = ui_qt.QtWidgets.QPushButton("Get")
        self.get_end_button = ui_qt.QtWidgets.QPushButton("Get")
        range_layout.addWidget(ui_qt.QtWidgets.QLabel("Start:"), 0, 0)
        range_layout.addWidget(self.start_frame_spinbox, 0, 1)
        range_layout.addWidget(self.get_start_button, 0, 2)
        range_layout.addWidget(ui_qt.QtWidgets.QLabel("End:"), 0, 3)
        range_layout.addWidget(self.end_frame_spinbox, 0, 4)
        range_layout.addWidget(self.get_end_button, 0, 5)
        range_layout.setColumnStretch(1, 1)
        range_layout.setColumnStretch(4, 1)
        main_layout.addLayout(range_layout)

        self.extract_button = ui_qt.QtWidgets.QPushButton("Extract World Space")
        self._set_action_button_style(self.extract_button)
        main_layout.addWidget(self.extract_button)

        main_layout.addWidget(self.create_separator("3. Stored Data Status"))
        stored_layout = ui_qt.QtWidgets.QHBoxLayout()
        stored_label = ui_qt.QtWidgets.QLabel("Stored Keys:")
        stored_font = stored_label.font()
        stored_font.setBold(True)
        stored_label.setFont(stored_font)
        self.stored_status_label = ui_qt.QtWidgets.QLabel("No Data")
        self.stored_status_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.stored_status_label.setWordWrap(True)
        self.stored_status_label.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        stored_layout.addWidget(stored_label)
        stored_layout.addWidget(self.stored_status_label, 1)
        main_layout.addLayout(stored_layout)

        self.bake_button = ui_qt.QtWidgets.QPushButton("Bake World Space")
        self._set_action_button_style(self.bake_button)
        main_layout.addWidget(self.bake_button)

        self.message_label = ui_qt.QtWidgets.QLabel("Load one or more animated objects to begin.")
        self.message_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.message_label.setWordWrap(True)
        self.message_label.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        main_layout.addWidget(self.message_label)
        self.set_workflow_enabled(False)
        self.set_target_state("Not loaded yet", "empty")

    @staticmethod
    def _create_frame_spinbox():
        """Creates a frame-range spin box.

        Returns:
            QSpinBox: Configured frame input.
        """
        spinbox = ui_qt.QtWidgets.QSpinBox()
        spinbox.setRange(-1000000, 1000000)
        spinbox.setSizePolicy(
            ui_qt.QtWidgets.QSizePolicy.Ignored,
            ui_qt.QtWidgets.QSizePolicy.Preferred,
        )
        return spinbox

    @staticmethod
    def _set_action_button_style(button):
        """Applies the legacy-inspired neutral action color.

        Args:
            button (QPushButton): Button to style.
        """
        button.setStyleSheet(
            "QPushButton { background-color: #4D4D4D; padding: 5px; }"
            "QPushButton:hover { background-color: #5A5A5A; }"
            "QPushButton:disabled { background-color: #353535; color: #777777; }"
        )

    @staticmethod
    def create_separator(text):
        """Creates a responsive section separator.

        Args:
            text (str): Section label.

        Returns:
            QWidget: Separator widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 5, 0, 0)
        layout.setSpacing(7)
        left_line = ui_qt.QtWidgets.QFrame()
        right_line = ui_qt.QtWidgets.QFrame()
        for line in [left_line, right_line]:
            line.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
            line.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)
        label = ui_qt.QtWidgets.QLabel(text)
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        layout.addWidget(left_line, 1)
        layout.addWidget(label)
        layout.addWidget(right_line, 1)
        return widget

    def set_frame_range(self, start_frame, end_frame):
        """Updates both frame inputs.

        Args:
            start_frame (int): Start-frame value.
            end_frame (int): End-frame value.
        """
        self.start_frame_spinbox.setValue(int(start_frame))
        self.end_frame_spinbox.setValue(int(end_frame))

    def get_frame_range(self):
        """Gets both frame input values.

        Returns:
            tuple: Start and end frames.
        """
        return self.start_frame_spinbox.value(), self.end_frame_spinbox.value()

    def set_workflow_enabled(self, has_targets, has_data=False):
        """Updates controls that depend on loaded targets or extracted data.

        Args:
            has_targets (bool): Whether valid targets are loaded.
            has_data (bool, optional): Whether extracted data is available.
        """
        for widget in [
            self.start_frame_spinbox,
            self.end_frame_spinbox,
            self.get_start_button,
            self.get_end_button,
            self.extract_button,
        ]:
            widget.setEnabled(bool(has_targets))
        self.bake_button.setEnabled(bool(has_data))

    def set_target_state(self, label, state):
        """Updates the target button label and color.

        Args:
            label (str): Button text.
            state (str): Empty, loaded, or error state.
        """
        colors = {
            "empty": ("#333333", "#414141"),
            "loaded": ("#638563", "#739873"),
            "error": ("#9A5555", "#AC6262"),
        }
        base_color, hover_color = colors.get(state, colors["empty"])
        self.target_status_button.setText(label)
        self.target_status_button.setStyleSheet(
            f"QPushButton {{ background-color: {base_color}; }}"
            f"QPushButton:hover {{ background-color: {hover_color}; }}"
        )

    def set_message(self, message, level="info"):
        """Displays concise workflow feedback.

        Args:
            message (str): Status message.
            level (str, optional): Info, success, warning, or error.
        """
        colors = {
            "info": "#B8B8B8",
            "success": "#8BCB88",
            "warning": "#E2BE72",
            "error": "#E58A8A",
        }
        self.message_label.setStyleSheet(f"color: {colors.get(level, colors['info'])};")
        self.message_label.setText(message)

    def show_help(self):
        """Shows tool workflow and safety information without author details."""
        ui_qt.QtWidgets.QMessageBox.information(
            self,
            "World Space Baker Help",
            "1. Select one or more animated objects and click Load Selection.\n\n"
            "2. Set the inclusive animation range. The Get buttons use the current timeline frame.\n\n"
            "3. Click Extract World Space to store translate and rotate samples in memory.\n\n"
            "4. Change constraints, hierarchy, or animation as needed, then click Bake World Space to key the stored "
            "world-space transforms.\n\n"
            "Extracted data lasts only for the current tool session. Baking is undoable in one chunk.",
        )

    def resize_to_contents(self):
        """Starts a floating window at the smallest useful content size."""
        try:
            if hasattr(self, "isFloating") and not self.isFloating():
                return
        except (AttributeError, RuntimeError):
            pass
        self.updateGeometry()
        self.adjustSize()
        content_size = self.sizeHint()
        if content_size.isValid():
            self.resize(max(content_size.width(), self.minimumWidth()), content_size.height())


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = WorldSpaceBakerView()
        window.show()
