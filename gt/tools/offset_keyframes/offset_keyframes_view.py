"""Dockable Qt view for Offset Keyframes."""

from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib

from gt.tools.offset_keyframes import offset_keyframes_model as offset_model


class OffsetKeyframesView(metaclass=MayaWindowMeta):
    """Builds the dockable Offset Keyframes interface."""

    def __init__(self, parent=None, version=None):
        """Initializes the Offset Keyframes window.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version displayed in the title.
        """
        super().__init__(parent=parent)
        self.controller = None
        self.setWindowTitle("Offset Keyframes" + (f" - (v{version})" if version else ""))
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_offset_keyframes))
        self.setMinimumWidth(370)
        self._build_widgets()
        self.resize_to_contents()
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds all interface widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        main_layout.addWidget(self.create_separator("Offset Keyframes"))

        scope_layout = ui_qt.QtWidgets.QHBoxLayout()
        scope_layout.addWidget(ui_qt.QtWidgets.QLabel("Offset Scope:"))
        self.scope_combo = ui_qt.QtWidgets.QComboBox()
        self.scope_combo.setToolTip(
            "All Keys keeps the whole animation curve intact. Selected Keys uses Graph Editor selections. "
            "Current Frame onward and Playback Range constrain the change."
        )
        self.scope_combo.addItem("All Keys on Selection", offset_model.SCOPE_ALL)
        self.scope_combo.addItem("Selected Keys Only", offset_model.SCOPE_SELECTED)
        self.scope_combo.addItem("Current Frame Onward", offset_model.SCOPE_CURRENT)
        self.scope_combo.addItem("Playback Range", offset_model.SCOPE_PLAYBACK)
        scope_layout.addWidget(self.scope_combo, 1)
        self.euler_filter_check = ui_qt.QtWidgets.QCheckBox("Apply Euler Filter")
        self.euler_filter_check.setToolTip(
            "Runs Maya's Euler filter on changed curves. Disable it for intentional rotations larger than 180 degrees."
        )
        scope_layout.addWidget(self.euler_filter_check)
        main_layout.addLayout(scope_layout)

        amount_layout = ui_qt.QtWidgets.QHBoxLayout()
        amount_layout.addWidget(ui_qt.QtWidgets.QLabel("Frames:"))
        self.offset_spin = self._create_frame_spinbox()
        self.offset_spin.setToolTip("Frame amount used by Offset Left and Offset Right.")
        amount_layout.addWidget(self.offset_spin, 1)
        self.offset_left_button = ui_qt.QtWidgets.QPushButton("Offset Left")
        self.offset_right_button = ui_qt.QtWidgets.QPushButton("Offset Right")
        self.offset_left_button.setToolTip("Moves the selected animation earlier without changing key values.")
        self.offset_right_button.setToolTip("Moves the selected animation later without changing key values.")
        amount_layout.addWidget(self.offset_left_button)
        amount_layout.addWidget(self.offset_right_button)
        main_layout.addLayout(amount_layout)

        nudge_layout = ui_qt.QtWidgets.QHBoxLayout()
        nudge_layout.addWidget(ui_qt.QtWidgets.QLabel("Nudge:"))
        self.nudge_buttons = []
        for amount in [-10, -5, -1, 1, 5, 10]:
            button = ui_qt.QtWidgets.QPushButton(f"{amount:+g}")
            button.setProperty("offset_amount", amount)
            button.setToolTip(
                f"Nudge selected animation {abs(amount):g} frame(s) "
                f"{'left' if amount < 0 else 'right'}."
            )
            button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Expanding)
            nudge_layout.addWidget(button, 1)
            self.nudge_buttons.append(button)
        main_layout.addLayout(nudge_layout, 1)

        main_layout.addWidget(self.create_separator("Stagger Selection"))
        stagger_layout = ui_qt.QtWidgets.QHBoxLayout()
        stagger_layout.addWidget(ui_qt.QtWidgets.QLabel("Step:"))
        self.stagger_spin = self._create_frame_spinbox()
        self.stagger_spin.setToolTip(
            "Frame increment between adjacent selected objects. The first selected object remains unchanged."
        )
        stagger_layout.addWidget(self.stagger_spin, 1)
        self.stagger_left_button = ui_qt.QtWidgets.QPushButton("Stagger Left")
        self.stagger_right_button = ui_qt.QtWidgets.QPushButton("Stagger Right")
        self.stagger_left_button.setToolTip("Offsets every next selected object earlier by the configured step.")
        self.stagger_right_button.setToolTip("Offsets every next selected object later by the configured step.")
        stagger_layout.addWidget(self.stagger_left_button)
        stagger_layout.addWidget(self.stagger_right_button)
        main_layout.addLayout(stagger_layout)

        self.message_label = ui_qt.QtWidgets.QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.message_label.setVisible(False)
        self._message_timer = ui_qt.QtCore.QTimer(self)
        self._message_timer.setSingleShot(True)
        self._message_timer.timeout.connect(self.clear_message)
        main_layout.addWidget(self.message_label)

    @staticmethod
    def _create_frame_spinbox():
        """Creates a signed frame spin box.

        Returns:
            QDoubleSpinBox: Configured frame input.
        """
        spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
        spinbox.setDecimals(3)
        spinbox.setRange(0.001, 1000000.0)
        spinbox.setSingleStep(1.0)
        spinbox.setKeyboardTracking(False)
        return spinbox

    @staticmethod
    def create_separator(text):
        """Creates a section divider.

        Args:
            text (str): Section label.

        Returns:
            QWidget: Divider widget.
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

    def get_settings(self):
        """Gets current settings from the widgets.

        Returns:
            dict: Serializable settings.
        """
        return {
            "offset_amount": self.offset_spin.value(),
            "scope": self.scope_combo.currentData(),
            "stagger_step": self.stagger_spin.value(),
            "apply_euler_filter": self.euler_filter_check.isChecked(),
        }

    def set_settings(self, settings):
        """Updates widgets without requiring a UI rebuild.

        Args:
            settings (dict): Settings to display.
        """
        settings = settings or {}
        self.offset_spin.setValue(float(settings.get("offset_amount", 1.0)))
        self.stagger_spin.setValue(float(settings.get("stagger_step", 1.0)))
        self.euler_filter_check.setChecked(bool(settings.get("apply_euler_filter")))
        scope = settings.get("scope", offset_model.SCOPE_ALL)
        scope_index = self.scope_combo.findData(scope)
        self.scope_combo.setCurrentIndex(max(0, scope_index))

    def set_message(self, message, level="info"):
        """Displays concise action feedback.

        Args:
            message (str): Message to display.
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
        self.message_label.setVisible(bool(message))
        self._message_timer.stop()
        if message:
            self._message_timer.start(3000)

    def clear_message(self):
        """Clears and hides the temporary action feedback message."""
        self.message_label.clear()
        self.message_label.setVisible(False)

    def resize_to_contents(self):
        """Sizes floating windows to their useful minimum."""
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
