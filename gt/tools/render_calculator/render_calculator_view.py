"""Qt view for the Render Calculator tool."""

from gt.ui import qt_import as ui_qt
from gt.ui import qt_utils
from gt.ui import resource_library as ui_res_lib
from gt.tools.render_calculator.render_calculator_model import (
    MAX_INPUT_VALUE,
    UNIT_LABELS,
)


class RenderCalculatorView(metaclass=qt_utils.MayaWindowMeta):
    """Responsive dockable interface for calculating render durations."""

    def __init__(self, parent=None, version=None):
        """Initializes the Render Calculator view.

        Args:
            parent (QWidget, optional): Parent Maya widget.
            version (str, optional): Tool version displayed in the window title.
        """
        super().__init__(parent=parent)
        self.setObjectName("RenderCalculator")
        window_title = "Render Calculator"
        if version:
            window_title += f" (v{version})"
        self.setWindowTitle(window_title)
        self.setWindowIcon(
            ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_render_calculator)
        )
        self.setMinimumSize(390, 285)
        self.resize(430, 340)
        self.setStyleSheet(self._build_stylesheet())
        self._build_widgets()
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds the responsive calculator layout."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(10)

        settings_layout = ui_qt.QtWidgets.QGridLayout()
        settings_layout.setHorizontalSpacing(8)
        settings_layout.setVerticalSpacing(8)
        settings_layout.setColumnStretch(1, 1)

        self.time_per_frame_spinbox = self._create_spinbox()
        self.unit_combo = ui_qt.QtWidgets.QComboBox()
        self.unit_combo.addItems(UNIT_LABELS)
        self.unit_combo.setMinimumWidth(92)
        self.unit_combo.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Minimum,
            ui_qt.QtLib.SizePolicy.Fixed,
        )

        self.num_frames_spinbox = self._create_spinbox()
        self.get_current_button = ui_qt.QtWidgets.QPushButton("Get Current")
        self.get_current_button.setObjectName("utilityButton")
        self.get_current_button.setMinimumWidth(92)

        self.num_machines_spinbox = self._create_spinbox()
        self.reset_button = ui_qt.QtWidgets.QPushButton("Reset")
        self.reset_button.setObjectName("utilityButton")
        self.reset_button.setMinimumWidth(92)

        settings_layout.addWidget(
            self._create_label("Average Time Per Frame:"), 0, 0
        )
        settings_layout.addWidget(self.time_per_frame_spinbox, 0, 1)
        settings_layout.addWidget(self.unit_combo, 0, 2)

        settings_layout.addWidget(
            self._create_label("Total Number of Frames:"), 1, 0
        )
        settings_layout.addWidget(self.num_frames_spinbox, 1, 1)
        settings_layout.addWidget(self.get_current_button, 1, 2)

        settings_layout.addWidget(
            self._create_label("Total Number of Machines:"), 2, 0
        )
        settings_layout.addWidget(self.num_machines_spinbox, 2, 1)
        settings_layout.addWidget(self.reset_button, 2, 2)
        main_layout.addLayout(settings_layout)

        separator = ui_qt.QtWidgets.QFrame()
        separator.setFrameShape(ui_qt.QtLib.FrameStyle.HLine)
        separator.setFrameShadow(ui_qt.QtLib.FrameStyle.Sunken)
        main_layout.addWidget(separator)

        self.status_label = ui_qt.QtWidgets.QLabel()
        self.status_label.setObjectName("statusLabel")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.status_label.setVisible(False)
        main_layout.addWidget(self.status_label)

        output_label = ui_qt.QtWidgets.QLabel("Render Time:")
        output_label.setObjectName("outputLabel")
        output_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        main_layout.addWidget(output_label)

        self.output_text = ui_qt.QtWidgets.QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(100)
        self.output_text.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Expanding,
            ui_qt.QtLib.SizePolicy.Expanding,
        )
        main_layout.addWidget(self.output_text, 1)

    @staticmethod
    def _create_label(text):
        """Creates a right-aligned settings label.

        Args:
            text (str): Label text.

        Returns:
            QLabel: Configured settings label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setAlignment(
            ui_qt.QtLib.AlignmentFlag.AlignRight
            | ui_qt.QtLib.AlignmentFlag.AlignVCenter
        )
        label.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Minimum,
            ui_qt.QtLib.SizePolicy.Fixed,
        )
        return label

    @staticmethod
    def _create_spinbox():
        """Creates a numeric input using the calculator input range.

        Returns:
            QSpinBox: Configured numeric input.
        """
        spinbox = ui_qt.QtWidgets.QSpinBox()
        spinbox.setRange(1, MAX_INPUT_VALUE)
        spinbox.setMinimumWidth(68)
        spinbox.setSizePolicy(
            ui_qt.QtLib.SizePolicy.Expanding,
            ui_qt.QtLib.SizePolicy.Fixed,
        )
        return spinbox

    @staticmethod
    def _build_stylesheet():
        """Builds the calculator stylesheet with legacy-inspired colors.

        Returns:
            str: Qt stylesheet used by the view.
        """
        return ui_res_lib.Stylesheet.maya_dialog_base + """
            QLabel {
                color: #d6d6d6;
                font-weight: normal;
            }
            QSpinBox, QComboBox {
                min-height: 22px;
                background-color: #5b5b5b;
                border: 1px solid #707070;
                color: #eeeeee;
                padding: 1px 4px;
            }
            QPushButton#utilityButton {
                min-height: 24px;
                background-color: #5b5b5b;
                border: 1px solid #444444;
                color: #e0e0e0;
                padding: 2px 6px;
            }
            QPushButton#utilityButton:hover {
                background-color: #6b6b6b;
            }
            QPushButton#utilityButton:pressed {
                background-color: #4b4b4b;
            }
            QLabel#outputLabel {
                color: #c9c9c9;
                font-weight: bold;
            }
            QLabel#statusLabel {
                color: #d6b656;
            }
            QTextEdit {
                background-color: #2e2e2e;
                border: 1px solid #303030;
                color: #e0e0e0;
                padding: 4px;
                font-family: Consolas, Monospace;
            }
        """

    def set_input_values(self, time_per_frame, num_frames, num_machines, unit):
        """Updates all input widgets from model values.

        Args:
            time_per_frame (int): Average render time for one frame.
            num_frames (int): Number of frames to render.
            num_machines (int): Number of machines sharing the render.
            unit (str): Unit calculation key.
        """
        widgets = [
            self.time_per_frame_spinbox,
            self.num_frames_spinbox,
            self.num_machines_spinbox,
            self.unit_combo,
        ]
        previous_block_states = [widget.blockSignals(True) for widget in widgets]
        try:
            self.time_per_frame_spinbox.setValue(time_per_frame)
            self.num_frames_spinbox.setValue(num_frames)
            self.num_machines_spinbox.setValue(num_machines)
            self.unit_combo.setCurrentText(self._unit_to_label(unit))
        finally:
            for widget, previous_state in zip(widgets, previous_block_states):
                widget.blockSignals(previous_state)

    @staticmethod
    def _unit_to_label(unit):
        """Converts a calculation unit key into a combo-box label.

        Args:
            unit (str): Unit key.

        Returns:
            str: Display label for the unit.
        """
        labels_by_unit = {
            "seconds": "Second(s)",
            "minutes": "Minute(s)",
            "hours": "Hour(s)",
        }
        return labels_by_unit.get(str(unit).lower(), "Second(s)")

    def set_frame_count(self, frame_count):
        """Updates the frame controls from the current Maya timeline.

        Args:
            frame_count (int): Inclusive playback-range frame count.
        """
        previous_block_state = self.num_frames_spinbox.blockSignals(True)
        try:
            self.num_frames_spinbox.setValue(frame_count)
        finally:
            self.num_frames_spinbox.blockSignals(previous_block_state)

    def set_result_text(self, text):
        """Displays a newly calculated render summary.

        Args:
            text (str): Render summary to display.
        """
        self.output_text.setPlainText(text)
        self.output_text.moveCursor(ui_qt.QtLib.TextCursor.Start)

    def set_status(self, message="", is_error=False):
        """Displays a compact status message below the settings.

        Args:
            message (str): Status message to display.
            is_error (bool): Whether the message represents an error.
        """
        self.status_label.setText(str(message or ""))
        self.status_label.setProperty("error", bool(is_error))
        self.status_label.setVisible(bool(message))
        self.status_label.style().unpolish(self.status_label)
        self.status_label.style().polish(self.status_label)


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        window = RenderCalculatorView(version="dev")
        window.show()
