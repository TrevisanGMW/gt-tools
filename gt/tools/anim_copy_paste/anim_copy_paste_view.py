"""Dockable Qt view for Copy/Paste Animation."""

from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_import as ui_qt
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib

from gt.tools.anim_copy_paste import anim_copy_paste_model as copy_model


class ResponsiveActionButton(ui_qt.QtWidgets.QPushButton):
    """Action button that expands with its layout without forcing a text width."""

    def minimumSizeHint(self):
        """Keeps the useful height while allowing horizontal layout expansion.

        Returns:
            QSize: Minimum button size without an artificial text-width limit.
        """
        size = super().minimumSizeHint()
        size.setWidth(0)
        return size


class AnimCopyPasteView(metaclass=MayaWindowMeta):
    """Builds the dockable Copy/Paste Animation interface."""

    def __init__(self, parent=None, version=None):
        """Initializes the Copy/Paste Animation window.

        Args:
            parent (QWidget, optional): Parent widget.
            version (str, optional): Tool version displayed in the title.
        """
        super().__init__(parent=parent)
        self.controller = None
        self._action_buttons = []
        self._screen_handle = None
        self.setWindowTitle("Copy/Paste Animation" + (f" - (v{version})" if version else ""))
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_anim_copy_paste))
        self._build_widgets()
        self._update_ui_scale_metrics()
        self.resize_to_contents()
        qt_utils.center_window(self)

    def _build_widgets(self):
        """Builds all interface widgets."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(8)

        main_layout.addWidget(self._build_title_bar())
        main_layout.addWidget(self.create_separator("1. Copy Animation"))
        copy_scope_layout = ui_qt.QtWidgets.QHBoxLayout()
        copy_scope_label = ui_qt.QtWidgets.QLabel("Copy Scope:")
        copy_scope_label.setToolTip("Controls which keys are stored when Copy Animation is pressed.")
        self.copy_scope_combo = ui_qt.QtWidgets.QComboBox()
        self.copy_scope_combo.addItem(
            "All Animation", copy_model.AnimCopyPasteConstants.CopyScope.ALL
        )
        self.copy_scope_combo.addItem(
            "Selected Keyframes", copy_model.AnimCopyPasteConstants.CopyScope.SELECTED
        )
        self.copy_scope_combo.addItem(
            "Keys at and Before Current Time",
            copy_model.AnimCopyPasteConstants.CopyScope.BEFORE_CURRENT,
        )
        self.copy_scope_combo.addItem(
            "Keys at and After Current Time",
            copy_model.AnimCopyPasteConstants.CopyScope.AFTER_CURRENT,
        )
        self._set_combo_item_tooltips(
            self.copy_scope_combo,
            [
                "Copies every time-keyed channel from the selected Maya objects.",
                "Copies only keyframes selected in Maya's Graph Editor or Dope Sheet. "
                "Keep the animated objects selected while making the key selection.",
                "Copies keys on or before Maya's current timeline frame. "
                "Use this to capture the beginning of an animation or transition.",
                "Copies keys on or after Maya's current timeline frame. "
                "Use this to capture the end of an animation or transition.",
            ],
        )
        self.copy_scope_combo.setToolTip(
            "All Animation stores every keyed channel on the selected objects.\n\n"
            "Selected Keyframes stores only keys selected in Maya's Graph Editor or Dope Sheet; "
            "the selected keys can identify their own source objects.\n\n"
            "Before and After scopes include a key exactly on the current frame."
        )
        copy_scope_layout.addWidget(copy_scope_label)
        copy_scope_layout.addWidget(self.copy_scope_combo, 1)
        main_layout.addLayout(copy_scope_layout)
        self.copy_button = ResponsiveActionButton("Copy Animation")
        self.copy_button.setToolTip(
            "Stores animation from the selected objects in a persistent JSON cache using the Copy Scope above."
        )
        self._set_button_icon(self.copy_button, ui_res_lib.Icon.anim_copy)
        self._set_emphasized_button_style(self.copy_button)
        main_layout.addWidget(self.copy_button)
        self.cache_summary_label = ui_qt.QtWidgets.QLabel("No copied animation.")
        self.cache_summary_label.setWordWrap(True)
        self.cache_summary_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.cache_summary_label.setToolTip(
            "Summarizes the animation currently stored in the shared persistent cache."
        )
        main_layout.addWidget(self.cache_summary_label)
        self.details_button = ui_qt.QtWidgets.QPushButton("Show Stored Animation Details")
        self.details_button.setToolTip(
            "Opens a line-numbered, syntax-highlighted report listing every stored object, "
            "channel, key count, and key frame."
        )
        main_layout.addWidget(self.details_button)

        main_layout.addWidget(self.create_separator("2. Destination Mapping"))
        mapping_layout = ui_qt.QtWidgets.QFormLayout()
        mapping_layout.setLabelAlignment(ui_qt.QtLib.AlignmentFlag.AlignRight)
        self.mapping_combo = ui_qt.QtWidgets.QComboBox()
        self.mapping_combo.addItem(
            "Selection Order", copy_model.AnimCopyPasteConstants.MappingMode.SELECTION
        )
        self.mapping_combo.addItem(
            "Name / Hierarchy (Ignore Namespace)", copy_model.AnimCopyPasteConstants.MappingMode.NAME
        )
        self.mapping_combo.addItem(
            "Namespace Swap (Characters)", copy_model.AnimCopyPasteConstants.MappingMode.NAMESPACE
        )
        self._set_combo_item_tooltips(
            self.mapping_combo,
            [
                "After copying, select destination objects in the same order as their source objects. "
                "The first copied object pastes to the first selected destination, and so on. "
                "When one source object was copied, it pastes to every selected destination.",
                "After copying, select equivalent destination controls or joints. Their complete DAG hierarchy "
                "must match the copied hierarchy after namespace prefixes are ignored. "
                "For example, |source:rig|source:hand matches |target:rig|target:hand.",
                "Enter the Target Namespace below. The tool replaces the copied character namespace in each "
                "stored control or joint path, then pastes to the matching target path automatically. "
                "No destination selection is required when the two characters share the same hierarchy.",
            ],
        )
        self.mapping_combo.setToolTip(
            "Selection Order pairs copied objects with destination objects in their selection order. "
            "When one object was copied, it is pasted to every selected destination.\n\n"
            "Name / Hierarchy matches selected destinations by their long DAG path after namespaces are removed. "
            "Use it when equivalent controls are selected on another character.\n\n"
            "Namespace Swap replaces the copied character namespace with Target Namespace and finds matching "
            "controls or joints automatically; destination objects do not need to be selected."
        )
        mapping_layout.addRow(
            self._create_tooltip_label("Object Mapping:", self.mapping_combo.toolTip()),
            self.mapping_combo,
        )
        self.source_namespace_field = ui_qt.QtWidgets.QLineEdit()
        self.source_namespace_field.setPlaceholderText("Optional — auto-detect when empty")
        self.source_namespace_field.setToolTip(
            "Used only with Namespace Swap. Enter the copied character namespace without a trailing colon, "
            "for example source_rig. Leave it blank to derive it from each stored object."
        )
        mapping_layout.addRow(
            self._create_tooltip_label("Source Namespace:", self.source_namespace_field.toolTip()),
            self.source_namespace_field,
        )
        self.target_namespace_field = ui_qt.QtWidgets.QLineEdit()
        self.target_namespace_field.setPlaceholderText("Required for Namespace Swap, e.g. target_rig")
        self.target_namespace_field.setToolTip(
            "Used only with Namespace Swap. Enter the destination character namespace without a trailing colon. "
            "The tool changes |source_rig:root|source_rig:joint into "
            "|target_rig:root|target_rig:joint before pasting."
        )
        mapping_layout.addRow(
            self._create_tooltip_label("Target Namespace:", self.target_namespace_field.toolTip()),
            self.target_namespace_field,
        )
        self.source_attribute_field = ui_qt.QtWidgets.QLineEdit()
        self.source_attribute_field.setPlaceholderText("Optional, e.g. translateX")
        self.source_attribute_field.setToolTip(
            "Limit the paste to this copied channel. Set a destination channel below "
            "to paste animation into another channel."
        )
        mapping_layout.addRow(
            self._create_tooltip_label("Source Channel:", self.source_attribute_field.toolTip()),
            self.source_attribute_field,
        )
        self.destination_attribute_field = ui_qt.QtWidgets.QLineEdit()
        self.destination_attribute_field.setPlaceholderText("Optional, e.g. rotateY")
        self.destination_attribute_field.setToolTip(
            "Destination channel used with Source Channel. Leave empty to use the copied channel name."
        )
        mapping_layout.addRow(
            self._create_tooltip_label("Destination Channel:", self.destination_attribute_field.toolTip()),
            self.destination_attribute_field,
        )
        main_layout.addLayout(mapping_layout)

        main_layout.addWidget(self.create_separator("3. Paste Animation"))
        paste_frame_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.current_frame_radio = ui_qt.QtWidgets.QRadioButton("Current Frame")
        self.custom_frame_radio = ui_qt.QtWidgets.QRadioButton("Frame:")
        self.paste_frame_spin = self._create_frame_spinbox()
        self.current_frame_radio.setToolTip("Starts copied animation at Maya's current timeline frame.")
        self.custom_frame_radio.setToolTip("Starts copied animation at the frame entered on the right.")
        self.paste_frame_spin.setToolTip("Custom destination frame for the copied animation.")
        self.paste_frame_button_group = ui_qt.QtWidgets.QButtonGroup(self)
        self.paste_frame_button_group.addButton(self.current_frame_radio)
        self.paste_frame_button_group.addButton(self.custom_frame_radio)
        paste_frame_layout.addWidget(self.current_frame_radio)
        paste_frame_layout.addWidget(self.custom_frame_radio)
        paste_frame_layout.addWidget(self.paste_frame_spin, 1)
        main_layout.addLayout(paste_frame_layout)

        self.euler_filter_check = ui_qt.QtWidgets.QCheckBox("Apply Euler Filter After Paste")
        self.euler_filter_check.setToolTip(
            "Runs Maya's Euler filter on pasted rotation curves. Disable for intentional "
            "rotations larger than 180 degrees."
        )
        euler_filter_layout = ui_qt.QtWidgets.QHBoxLayout()
        euler_filter_layout.addStretch()
        euler_filter_layout.addWidget(self.euler_filter_check)
        euler_filter_layout.addStretch()
        main_layout.addLayout(euler_filter_layout)

        paste_buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.paste_insert_button = ResponsiveActionButton("Paste Insert")
        self.paste_replace_button = ResponsiveActionButton("Paste (Replace)")
        self.paste_insert_button.setToolTip(
            "Inserts the copied chunk at the destination frame and shifts future animation to preserve it."
        )
        self.paste_replace_button.setToolTip(
            "Clears each affected destination channel, then pastes the copied animation. Confirmation is required."
        )
        self._set_button_icon(self.paste_insert_button, ui_res_lib.Icon.anim_paste_insert)
        self._set_button_icon(self.paste_replace_button, ui_res_lib.Icon.anim_paste)
        self._set_emphasized_button_style(self.paste_insert_button)
        self.paste_replace_button.setStyleSheet(
            "QPushButton { background-color: #565656; padding: 6px; }"
            "QPushButton:hover { background-color: #646464; }"
        )
        paste_buttons_layout.addWidget(self.paste_insert_button, 1)
        paste_buttons_layout.addWidget(self.paste_replace_button, 1)
        main_layout.addLayout(paste_buttons_layout, 1)

        main_layout.addWidget(self.create_separator("Cache Management"))
        cache_buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.import_button = ui_qt.QtWidgets.QPushButton("Import JSON")
        self.export_button = ui_qt.QtWidgets.QPushButton("Export JSON")
        self.clear_cache_button = ui_qt.QtWidgets.QPushButton("Clear Cache")
        self.import_button.setToolTip(
            "Loads a portable animation JSON file into the shared Copy/Paste Animation cache."
        )
        self.export_button.setToolTip("Writes the copied animation to a portable JSON file.")
        self.clear_cache_button.setToolTip("Deletes only Copy/Paste Animation's cached animation JSON file.")
        self.clear_cache_button.setStyleSheet(
            "QPushButton { background-color: #484848; }"
            "QPushButton:hover { background-color: #565656; }"
        )
        cache_buttons_layout.addWidget(self.import_button)
        cache_buttons_layout.addWidget(self.export_button)
        cache_buttons_layout.addWidget(self.clear_cache_button)
        main_layout.addLayout(cache_buttons_layout)

        self.message_label = ui_qt.QtWidgets.QLabel(
            "Copy animation, configure destination mapping, then choose a paste mode."
        )
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.message_label)
        self.current_frame_radio.toggled.connect(self._update_paste_frame_enabled)

    def _build_title_bar(self):
        """Builds the compact title and help row.

        Returns:
            QWidget: Configured title-bar widget.
        """
        title_bar = ui_qt.QtWidgets.QWidget()
        title_bar.setObjectName("anim_copy_paste_title_bar")
        title_bar.setStyleSheet(
            "QWidget#anim_copy_paste_title_bar { background-color: #5A5A5A; }"
            "QPushButton { background-color: transparent; border: 0; border-left: 1px solid #707070; "
            "padding: 6px 12px; }"
            "QPushButton:hover { background-color: #666666; }"
        )
        layout = ui_qt.QtWidgets.QHBoxLayout(title_bar)
        layout.setContentsMargins(10, 0, 0, 0)
        title_label = ui_qt.QtWidgets.QLabel("Copy/Paste Animation")
        font = title_label.font()
        font.setBold(True)
        title_label.setFont(font)
        self.help_button = ui_qt.QtWidgets.QPushButton("Help")
        self.help_button.setToolTip("Show Copy/Paste Animation workflow information.")
        layout.addWidget(title_label, 1)
        layout.addWidget(self.help_button)
        return title_bar

    @staticmethod
    def _create_frame_spinbox():
        """Creates a destination-frame spin box.

        Returns:
            QDoubleSpinBox: Configured frame input.
        """
        spinbox = ui_qt.QtWidgets.QDoubleSpinBox()
        spinbox.setDecimals(3)
        spinbox.setRange(-1000000.0, 1000000.0)
        spinbox.setSingleStep(1.0)
        spinbox.setKeyboardTracking(False)
        return spinbox

    @staticmethod
    def _set_emphasized_button_style(button):
        """Applies a brighter neutral style to a prominent action button.

        Args:
            button (QPushButton): Button to style.
        """
        button.setStyleSheet(
            "QPushButton { background-color: #626262; padding: 6px; }"
            "QPushButton:hover { background-color: #707070; }"
        )

    def _set_button_icon(self, button, icon_path):
        """Assigns an accessible icon to a primary action button.

        Args:
            button (QPushButton): Button receiving the icon.
            icon_path (str): Absolute path to an SVG or raster icon.
        """
        button.setIcon(ui_qt.QtGui.QIcon(icon_path))
        if button not in self._action_buttons:
            self._action_buttons.append(button)
        self._configure_action_button(button)

    def _configure_action_button(self, button):
        """Applies responsive sizing to a primary action button.

        Args:
            button (QPushButton): Button to resize.
        """
        size_policy = getattr(ui_qt.QtWidgets.QSizePolicy, "Policy", ui_qt.QtWidgets.QSizePolicy)
        button.setSizePolicy(size_policy.Expanding, size_policy.Expanding)
        button.setMinimumHeight(self._get_action_button_minimum_height())
        icon_size = self._get_action_icon_size()
        button.setIconSize(ui_qt.QtCore.QSize(icon_size, icon_size))

    def _update_ui_scale_metrics(self):
        """Updates font-relative metrics for standard and high-DPI displays."""
        self.setMinimumWidth(self._get_minimum_width())
        for button in self._action_buttons:
            self._configure_action_button(button)

    def _get_minimum_width(self):
        """Gets a font-relative width that keeps mapping controls readable.

        Returns:
            int: Minimum window width in Qt logical pixels.
        """
        metrics = self.fontMetrics()
        text_width = self._get_text_width(metrics, "Namespace Swap (Characters)")
        return max(455, text_width + 240)

    def _get_action_button_minimum_height(self):
        """Gets a font-relative minimum height for prominent actions.

        Returns:
            int: Button height in Qt logical pixels.
        """
        return max(42, self.fontMetrics().height() * 2 + 12)

    def _get_action_icon_size(self):
        """Gets a legible icon size derived from the active UI font.

        Returns:
            int: Square icon size in Qt logical pixels.
        """
        return max(30, min(44, self.fontMetrics().height() * 2 + 4))

    @staticmethod
    def _get_text_width(metrics, text):
        """Gets text width across supported Qt versions.

        Args:
            metrics (QFontMetrics): Metrics used to measure text.
            text (str): Text to measure.

        Returns:
            int: Width of the provided text.
        """
        if hasattr(metrics, "horizontalAdvance"):
            return metrics.horizontalAdvance(text)
        return metrics.width(text)

    @staticmethod
    def _create_tooltip_label(text, tooltip):
        """Creates a form label with the same tooltip as its input.

        Args:
            text (str): Visible label text.
            tooltip (str): Detailed usage guidance for the paired input.

        Returns:
            QLabel: Configured label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setToolTip(tooltip)
        return label

    @staticmethod
    def _set_combo_item_tooltips(combo_box, tooltips):
        """Sets detailed tooltips for every option in a combo box.

        Args:
            combo_box (QComboBox): Combo box whose choices receive tooltips.
            tooltips (list): Tooltip text in the same order as the choices.
        """
        qt_enum = ui_qt.QtCore.Qt
        item_data_role = getattr(qt_enum, "ItemDataRole", None)
        if item_data_role:
            tooltip_role = item_data_role.ToolTipRole
        else:
            tooltip_role = qt_enum.ToolTipRole
        for index, tooltip in enumerate(tooltips or []):
            combo_box.setItemData(index, tooltip, tooltip_role)

    def showEvent(self, event):
        """Refreshes font-relative UI metrics when the window is shown.

        Args:
            event (QShowEvent): Qt show event.
        """
        super().showEvent(event)
        self._update_ui_scale_metrics()
        window_handle = self.windowHandle()
        if not window_handle or window_handle == self._screen_handle:
            return
        self._screen_handle = window_handle
        window_handle.screenChanged.connect(lambda *args: self._update_ui_scale_metrics())

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

    def _update_paste_frame_enabled(self):
        """Enables custom-frame input only when selected."""
        self.paste_frame_spin.setEnabled(self.custom_frame_radio.isChecked())

    def get_settings(self):
        """Gets the current view settings.

        Returns:
            dict: Serializable tool settings.
        """
        return {
            "copy_scope": self.copy_scope_combo.currentData(),
            "mapping_mode": self.mapping_combo.currentData(),
            "source_namespace": self.source_namespace_field.text(),
            "target_namespace": self.target_namespace_field.text(),
            "source_attribute": self.source_attribute_field.text(),
            "destination_attribute": self.destination_attribute_field.text(),
            "paste_at_current_frame": self.current_frame_radio.isChecked(),
            "paste_frame": self.paste_frame_spin.value(),
            "apply_euler_filter": self.euler_filter_check.isChecked(),
        }

    def set_settings(self, settings):
        """Updates widgets with persistent settings.

        Args:
            settings (dict): Settings to display.
        """
        settings = settings or {}
        copy_scope_index = self.copy_scope_combo.findData(
            settings.get("copy_scope", copy_model.AnimCopyPasteConstants.CopyScope.ALL)
        )
        self.copy_scope_combo.setCurrentIndex(max(0, copy_scope_index))
        mapping_index = self.mapping_combo.findData(
            settings.get("mapping_mode", copy_model.AnimCopyPasteConstants.MappingMode.SELECTION)
        )
        self.mapping_combo.setCurrentIndex(max(0, mapping_index))
        self.source_namespace_field.setText(str(settings.get("source_namespace") or ""))
        self.target_namespace_field.setText(str(settings.get("target_namespace") or ""))
        self.source_attribute_field.setText(str(settings.get("source_attribute") or ""))
        self.destination_attribute_field.setText(str(settings.get("destination_attribute") or ""))
        self.current_frame_radio.setChecked(bool(settings.get("paste_at_current_frame", True)))
        self.custom_frame_radio.setChecked(not self.current_frame_radio.isChecked())
        self.paste_frame_spin.setValue(float(settings.get("paste_frame", 1.0)))
        self.euler_filter_check.setChecked(bool(settings.get("apply_euler_filter")))
        self._update_paste_frame_enabled()

    def set_cache_summary(self, summary):
        """Updates the copied-animation status line.

        Args:
            summary (str): Current cache summary.
        """
        self.cache_summary_label.setText(summary)

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

    def show_help(self):
        """Shows concise usage guidance."""
        ui_qt.QtWidgets.QMessageBox.information(
            self,
            "Copy/Paste Animation Help",
            "Copy Animation stores keyed channels from selected objects in a persistent JSON cache, so it remains "
            "available in another Maya session. Use Copy Scope to store all keys, only selected Graph Editor or "
            "Dope Sheet keys, or keys before or after the current frame.\n\n"
            "Paste Insert adds the copied chunk at the chosen frame and shifts future keys. Paste Replace clears each "
            "affected target channel before applying the copied animation.\n\n"
            "Use Selection Order for arbitrary source-to-target pairs, Name / Hierarchy for matching selected "
            "controls on another character, or Namespace Swap to paste directly from one character namespace "
            "to another. "
            "Use the channel fields to paste one source channel onto another destination channel.",
        )

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
