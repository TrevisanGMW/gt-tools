"""
Color Manager View
"""

from functools import partial

from gt.tools.color_manager import color_manager_model as model
from gt.ui.qt_utils import MayaWindowMeta
import gt.ui.qt_utils as qt_utils
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt


class ColorManagerView(metaclass=MayaWindowMeta):
    """Qt view for Color Manager."""

    def __init__(self, parent=None, controller=None, version=None):
        """Initializes the view.

        Args:
            parent (QWidget, optional): Parent widget.
            controller (ColorManagerController, optional): Controller reference.
            version (str, optional): Tool version.
        """
        super().__init__(parent=parent)
        self.controller = controller
        self.version = version
        self._is_updating = False
        self.current_color = [0.3, 0.3, 0.3]
        self.mode_button = None
        self.mode_combo = None
        self.target_combo = None
        self.current_color_mode_combo = None
        self.preview_button = None
        self.get_color_button = None
        self.brightness_slider = None
        self.outliner_checkbox = None
        self.viewport_checkbox = None
        self.saved_section_widget = None
        self.saved_rows_layout = None
        self.import_export_widget = None
        self.complete_preferences_widget = None
        self.auto_outliner_to_viewport_checkbox = None
        self.auto_viewport_to_outliner_checkbox = None

        self.set_window_title()
        self.setMinimumWidth(360)
        self.setWindowFlags(
            self.windowFlags()
            | ui_qt.QtLib.WindowFlag.WindowMaximizeButtonHint
            | ui_qt.QtLib.WindowFlag.WindowMinimizeButtonHint
        )
        self.setWindowIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.tool_color_manager))
        self.create_widgets()
        self.create_layout()
        self.apply_stylesheet()
        self.resize_to_contents()
        qt_utils.center_window(self)

    def set_window_title(self):
        """Sets the window title."""
        title = "Color Manager"
        if self.version:
            title += " - (v{0})".format(self.version)
        self.setWindowTitle(title)

    def create_widgets(self):
        """Creates persistent widgets used by the view."""
        self.mode_button = ui_qt.QtWidgets.QPushButton(model.UI_MODE_MINIMAL)
        self.mode_button.setMinimumWidth(112)
        self.mode_button.setMinimumHeight(34)
        self.mode_button.setToolTip("Toggle Color Manager UI mode.")
        self.mode_button.clicked.connect(lambda *args: self.controller.cycle_ui_mode())

        self.mode_combo = ui_qt.QtWidgets.QComboBox()
        self.mode_combo.addItems(model.COLOR_MODES)
        self.mode_combo.setToolTip("Viewport color behavior.")
        self.mode_combo.currentTextChanged.connect(lambda value: self.controller.set_color_mode(value))

        self.target_combo = ui_qt.QtWidgets.QComboBox()
        self.target_combo.addItems(model.TARGETS)
        self.target_combo.setToolTip("Apply color to selected transforms or their shapes.")
        self.target_combo.currentTextChanged.connect(lambda value: self.controller.set_target(value))

        self.current_color_mode_combo = ui_qt.QtWidgets.QComboBox()
        self.current_color_mode_combo.addItems(model.CURRENT_COLOR_MODES)
        self.current_color_mode_combo.setToolTip(
            "Choose whether clicked or read colors appear as their original swatch value "
            "or as the value converted for Maya's viewport."
        )
        self.current_color_mode_combo.currentTextChanged.connect(
            lambda value: self.controller.set_current_color_mode(value)
        )

        self.preview_button = ui_qt.QtWidgets.QPushButton()
        self.preview_button.setMinimumWidth(72)
        self.preview_button.setMinimumHeight(30)
        self.preview_button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        self.preview_button.setToolTip("Open color picker.")
        self.preview_button.clicked.connect(self.open_color_picker)

        self.get_color_button = ui_qt.QtWidgets.QPushButton("Get")
        self.configure_text_button(self.get_color_button, minimum_height=30)
        get_button_width = self.get_color_button.sizeHint().width() + 8
        self.get_color_button.setMinimumWidth(max(56, get_button_width))
        self.get_color_button.setToolTip("Get the color from the selected object.")
        self.get_color_button.clicked.connect(lambda *args: self.controller.get_selection_color())

        self.brightness_slider = ui_qt.QtWidgets.QSlider(ui_qt.QtLib.Orientation.Horizontal)
        self.brightness_slider.setRange(0, 100)
        self.brightness_slider.setSingleStep(1)
        self.brightness_slider.setPageStep(10)
        self.brightness_slider.setToolTip("Adjust color brightness.")
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)

        self.outliner_checkbox = ui_qt.QtWidgets.QCheckBox("Outliner")
        self.outliner_checkbox.setToolTip("Apply color to the outliner color.")
        self.outliner_checkbox.toggled.connect(lambda value: self.controller.set_outliner(value))
        self.viewport_checkbox = ui_qt.QtWidgets.QCheckBox("Viewport")
        self.viewport_checkbox.setToolTip("Apply color to viewport drawing override or wireframe color.")
        self.viewport_checkbox.toggled.connect(lambda value: self.controller.set_viewport(value))

        self.auto_outliner_to_viewport_checkbox = ui_qt.QtWidgets.QCheckBox("Outliner to Viewport")
        self.auto_outliner_to_viewport_checkbox.setToolTip(
            "Convert unconverted colors before viewport application or converted Current Color display."
        )
        self.auto_outliner_to_viewport_checkbox.toggled.connect(
            lambda value: self.controller.set_auto_adjust_outliner_to_viewport(value)
        )
        self.auto_viewport_to_outliner_checkbox = ui_qt.QtWidgets.QCheckBox("Viewport to Outliner")
        self.auto_viewport_to_outliner_checkbox.setToolTip(
            "Convert the derived viewport color before applying it to the Outliner."
        )
        self.auto_viewport_to_outliner_checkbox.toggled.connect(
            lambda value: self.controller.set_auto_adjust_viewport_to_outliner(value)
        )

    def create_layout(self):
        """Creates the main view layout."""
        main_layout = ui_qt.QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        separator_outer_spacing = 8
        main_layout.addLayout(self.create_title_bar())
        main_layout.addSpacing(separator_outer_spacing)
        main_layout.addWidget(self.create_separator())
        main_layout.addSpacing(14)
        main_layout.addLayout(self.create_current_color_row())
        main_layout.addSpacing(10)
        main_layout.addLayout(self.create_preset_color_row())
        main_layout.addSpacing(separator_outer_spacing)
        main_layout.addWidget(self.create_separator())
        main_layout.addSpacing(10)
        main_layout.addLayout(self.create_apply_options_row())
        main_layout.addSpacing(8)

        self.saved_section_widget = self.create_saved_colors_section()
        main_layout.addWidget(self.saved_section_widget)
        main_layout.addSpacing(6)
        self.complete_preferences_widget = self.create_complete_preferences_section()
        main_layout.addWidget(self.complete_preferences_widget)

        main_layout.addSpacing(4)
        main_layout.addLayout(self.create_action_buttons_row())

    def create_title_bar(self):
        """Creates the top title and mode bar.

        Returns:
            QHBoxLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        title_label = ui_qt.QtWidgets.QLabel("Color Manager")
        title_label.setMinimumHeight(34)
        title_label.setObjectName("ColorManagerTitle")
        layout.addWidget(title_label, 1)
        self.mode_button.setObjectName("ColorManagerModeButton")
        layout.addWidget(self.mode_button)
        return layout

    def create_current_color_row(self):
        """Creates current color controls.

        Returns:
            QHBoxLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(10)
        label = ui_qt.QtWidgets.QLabel("Current Color")
        label.setSizePolicy(ui_qt.QtLib.SizePolicy.Fixed, ui_qt.QtLib.SizePolicy.Preferred)
        label.setToolTip("Current RGB color.")
        layout.addWidget(label)
        layout.addWidget(self.preview_button, 2)
        layout.addWidget(self.brightness_slider, 3)
        layout.addWidget(self.get_color_button)
        return layout

    def create_preset_color_row(self):
        """Creates default color swatches.

        Returns:
            QHBoxLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(3)
        for color in model.PRESET_COLORS:
            button = self.create_color_button(
                color=color,
                tooltip="Apply preset color {0}.".format(self.format_rgb_values(color)),
                callback=lambda rgb=color: self.controller.apply_preset_color(rgb),
            )
            button.setFixedHeight(self.preview_button.minimumHeight())
            layout.addWidget(button, 1)
        return layout

    def create_apply_options_row(self):
        """Creates Set Color For controls.

        Returns:
            QHBoxLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        label = ui_qt.QtWidgets.QLabel("Set Color For")
        label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        label.setToolTip("Choose which color systems are affected.")
        layout.addWidget(label, 1)
        layout.addWidget(self.outliner_checkbox, 1)
        layout.addWidget(self.viewport_checkbox, 1)
        return layout

    def create_saved_colors_section(self):
        """Creates saved color controls.

        Returns:
            QWidget: Saved colors section widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Preferred)
        layout = ui_qt.QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        header_layout = ui_qt.QtWidgets.QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(6)
        label = self.create_section_label("Saved Colors")
        header_layout.addWidget(label, 1)
        add_button = ui_qt.QtWidgets.QPushButton()
        add_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_plus))
        add_button.setFixedSize(30, 28)
        add_button.setToolTip("Save the current color.")
        add_button.clicked.connect(lambda *args: self.controller.save_current_color())
        header_layout.addWidget(add_button)
        layout.addLayout(header_layout)

        self.import_export_widget = ui_qt.QtWidgets.QWidget()
        import_export_layout = ui_qt.QtWidgets.QHBoxLayout(self.import_export_widget)
        import_export_layout.setContentsMargins(0, 0, 0, 0)
        import_export_layout.setSpacing(6)
        import_button = ui_qt.QtWidgets.QPushButton("Import")
        self.configure_text_button(import_button, minimum_height=32)
        import_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_import))
        import_button.setToolTip("Import saved colors from JSON.")
        import_button.clicked.connect(lambda *args: self.controller.import_saved_colors())
        export_button = ui_qt.QtWidgets.QPushButton("Export")
        self.configure_text_button(export_button, minimum_height=32)
        export_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_export))
        export_button.setToolTip("Export saved colors to JSON.")
        export_button.clicked.connect(lambda *args: self.controller.export_saved_colors())
        clear_button = ui_qt.QtWidgets.QPushButton("Clear")
        self.configure_text_button(clear_button, minimum_height=32)
        clear_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        clear_button.setToolTip("Clear all saved colors.")
        clear_button.clicked.connect(lambda *args: self.controller.clear_saved_colors())
        import_export_layout.addWidget(import_button, 1)
        import_export_layout.addWidget(export_button, 1)
        import_export_layout.addWidget(clear_button, 1)
        layout.addWidget(self.import_export_widget)

        self.saved_rows_layout = ui_qt.QtWidgets.QVBoxLayout()
        self.saved_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.saved_rows_layout.setSpacing(4)
        layout.addLayout(self.saved_rows_layout)
        return widget

    def create_complete_preferences_section(self):
        """Creates Complete-mode behavior controls.

        Returns:
            QWidget: Preferences section widget.
        """
        widget = ui_qt.QtWidgets.QWidget()
        widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Preferred)
        layout = ui_qt.QtWidgets.QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        layout.addWidget(self.create_section_label("Preferences"))
        option_layout = ui_qt.QtWidgets.QHBoxLayout()
        option_layout.setContentsMargins(0, 0, 0, 0)
        option_layout.setSpacing(8)
        option_layout.addLayout(self.create_labeled_widget("Mode", self.mode_combo), 1)
        option_layout.addLayout(self.create_labeled_widget("Target", self.target_combo), 1)
        layout.addLayout(option_layout)
        layout.addLayout(self.create_labeled_widget("Current Color", self.current_color_mode_combo))
        checkbox_layout = ui_qt.QtWidgets.QHBoxLayout()
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(8)
        checkbox_layout.addWidget(
            self.auto_outliner_to_viewport_checkbox,
            1,
            ui_qt.QtLib.AlignmentFlag.AlignCenter,
        )
        checkbox_layout.addWidget(
            self.auto_viewport_to_outliner_checkbox,
            1,
            ui_qt.QtLib.AlignmentFlag.AlignCenter,
        )
        layout.addLayout(checkbox_layout)
        return widget

    def create_action_buttons_row(self):
        """Creates Reset and Apply buttons.

        Returns:
            QVBoxLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QVBoxLayout()
        layout.setContentsMargins(0, 2, 0, 0)
        layout.setSpacing(6)
        reset_button = ui_qt.QtWidgets.QPushButton("Reset")
        self.configure_text_button(reset_button, minimum_height=34)
        reset_button.setToolTip("Reset selected objects to their default colors.")
        reset_button.clicked.connect(lambda *args: self.controller.apply_color(reset=True))
        apply_button = ui_qt.QtWidgets.QPushButton("Apply")
        self.configure_text_button(apply_button, minimum_height=38)
        apply_button.setObjectName("ColorManagerApplyButton")
        apply_button.setToolTip("Apply the current color to selected objects.")
        apply_button.clicked.connect(lambda *args: self.controller.apply_color(reset=False))
        layout.addWidget(reset_button)
        layout.addWidget(apply_button)
        return layout

    def update_from_model(self, color_model):
        """Updates widgets from model state.

        Args:
            color_model (ColorManagerModel): Model state.
        """
        self._is_updating = True
        self.set_combo_value(self.mode_combo, color_model.color_mode)
        self.set_combo_value(self.target_combo, color_model.target)
        self.set_combo_value(self.current_color_mode_combo, color_model.current_color_mode)
        self.outliner_checkbox.setChecked(bool(color_model.set_outliner))
        self.viewport_checkbox.setChecked(bool(color_model.set_viewport))
        self.auto_outliner_to_viewport_checkbox.setChecked(bool(color_model.auto_adjust_outliner_to_viewport))
        self.auto_viewport_to_outliner_checkbox.setChecked(bool(color_model.auto_adjust_viewport_to_outliner))
        self.set_current_color(color_model.current_color)
        self.refresh_saved_colors(color_model.saved_colors)
        self.set_ui_mode(color_model.ui_mode)
        self._is_updating = False

    def set_ui_mode(self, ui_mode):
        """Updates visible sections for the active UI mode.

        Args:
            ui_mode (str): UI mode.
        """
        self.mode_button.setText(str(ui_mode or model.UI_MODE_MINIMAL))
        show_saved = ui_mode in [model.UI_MODE_DEFAULT, model.UI_MODE_COMPLETE]
        show_complete = ui_mode == model.UI_MODE_COMPLETE
        if self.saved_section_widget:
            self.saved_section_widget.setVisible(show_saved)
        if self.import_export_widget:
            self.import_export_widget.setVisible(show_complete)
        if self.complete_preferences_widget:
            self.complete_preferences_widget.setVisible(show_complete)
        self.resize_to_contents()

    def resize_to_contents(self):
        """Resizes a floating window to the smallest height required by its active mode."""
        try:
            if hasattr(self, "isFloating") and not self.isFloating():
                return
        except (AttributeError, RuntimeError):
            pass
        self.updateGeometry()
        self.adjustSize()
        content_height = self.sizeHint().height()
        if content_height > 0:
            self.resize(max(self.width(), self.minimumWidth()), content_height)

    def get_current_color(self):
        """Gets the current RGB color.

        Returns:
            list: Current RGB color.
        """
        return model.normalize_color(self.current_color)

    def set_current_color(self, color):
        """Updates current RGB controls.

        Args:
            color (list): RGB color.
        """
        normalized_color = model.normalize_color(color)
        self.current_color = normalized_color
        self.refresh_color_button(self.preview_button, normalized_color)
        brightness = int(round(max(normalized_color) * 100))
        self.brightness_slider.blockSignals(True)
        self.brightness_slider.setValue(brightness)
        self.brightness_slider.blockSignals(False)

    def refresh_saved_colors(self, saved_colors):
        """Refreshes saved color rows without rebuilding the window.

        Args:
            saved_colors (list): Saved RGB colors.
        """
        self.clear_saved_rows()
        normalized_colors = model.normalize_saved_colors(saved_colors)
        if not normalized_colors:
            empty_label = ui_qt.QtWidgets.QLabel("No saved colors.")
            empty_label.setStyleSheet("color: grey;")
            self.saved_rows_layout.addWidget(empty_label)
            return
        for index, color in enumerate(normalized_colors):
            self.saved_rows_layout.addWidget(self.create_saved_color_row(color=color, index=index))

    def clear_saved_rows(self):
        """Clears saved color row widgets."""
        if not self.saved_rows_layout:
            return
        while self.saved_rows_layout.count():
            item = self.saved_rows_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def create_saved_color_row(self, color, index):
        """Creates one saved color row.

        Args:
            color (list): Saved RGB color.
            index (int): Saved color index.

        Returns:
            QWidget: Row widget.
        """
        normalized_color = model.normalize_color(color)
        widget = ui_qt.QtWidgets.QWidget()
        widget.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Preferred)
        layout = ui_qt.QtWidgets.QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        swatch_button = self.create_color_button(
            color=normalized_color,
            tooltip="Apply saved color {0}.".format(self.format_rgb_values(normalized_color)),
            callback=lambda rgb=normalized_color: self.controller.apply_saved_color(rgb),
        )
        swatch_button.setFixedWidth(34)
        layout.addWidget(swatch_button)
        for channel, value in zip(["R", "G", "B"], normalized_color):
            label = ui_qt.QtWidgets.QLabel("{0} {1:.3f}".format(channel, value))
            label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
            label.setMinimumWidth(1)
            label.setToolTip("{0} channel value.".format(channel))
            layout.addWidget(label, 1)
        delete_button = ui_qt.QtWidgets.QPushButton()
        delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        delete_button.setFixedSize(30, 28)
        delete_button.setToolTip("Delete saved color {0}.".format(self.format_rgb_values(normalized_color)))
        delete_button.clicked.connect(partial(self.controller.delete_saved_color, index))
        layout.addWidget(delete_button)
        return widget

    def on_brightness_changed(self, value):
        """Handles brightness slider changes.

        Args:
            value (int): Slider value from 0 to 100.
        """
        if self._is_updating:
            return
        brightness = max(0.0, min(1.0, float(value) / 100.0))
        current_color = model.normalize_color(self.current_color)
        current_brightness = max(current_color)
        if current_brightness <= 0:
            new_color = [brightness, brightness, brightness]
        else:
            scale = brightness / current_brightness
            new_color = [max(0.0, min(1.0, channel * scale)) for channel in current_color]
        self.set_current_color(new_color)
        self.controller.set_current_color(new_color)

    def open_color_picker(self):
        """Opens a QColorDialog and applies the selected color."""
        color = self.get_current_color()
        initial_color = ui_qt.QtGui.QColor.fromRgbF(color[0], color[1], color[2])
        picked_color = ui_qt.QtWidgets.QColorDialog.getColor(initial_color, self, "Choose Color")
        if not picked_color.isValid():
            return
        new_color = [picked_color.redF(), picked_color.greenF(), picked_color.blueF()]
        self.set_current_color(new_color)
        self.controller.set_current_color(new_color)

    def create_color_button(self, color, tooltip, callback):
        """Creates a responsive color swatch button.

        Args:
            color (list): RGB color.
            tooltip (str): Button tooltip.
            callback (callable): Click callback.

        Returns:
            QPushButton: Created button.
        """
        button = ui_qt.QtWidgets.QPushButton()
        button.setMinimumHeight(26)
        button.setMinimumWidth(18)
        button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        button.setToolTip(tooltip)
        button.clicked.connect(lambda *args: callback())
        self.refresh_color_button(button, color)
        return button

    @staticmethod
    def configure_text_button(button, minimum_height=32):
        """Configures a text button so its label remains visible in compact layouts.

        Args:
            button (QPushButton): Button to configure.
            minimum_height (int, optional): Minimum button height.
        """
        button.setObjectName("ColorManagerTextButton")
        button.setMinimumHeight(int(minimum_height))
        button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)

    @staticmethod
    def refresh_color_button(button, color):
        """Updates a button background color.

        Args:
            button (QPushButton): Button to update.
            color (list): RGB color.
        """
        normalized_color = model.normalize_color(color)
        rgb_values = [int(value * 255) for value in normalized_color]
        button.setStyleSheet(
            "QPushButton {{ background-color: rgb({0}, {1}, {2}); border: none; border-radius: 2px; }}"
            "QPushButton:hover {{ border: none; }}".format(
                rgb_values[0],
                rgb_values[1],
                rgb_values[2],
            )
        )

    @staticmethod
    def create_labeled_widget(label_text, widget):
        """Creates a compact label+widget layout.

        Args:
            label_text (str): Label text.
            widget (QWidget): Widget.

        Returns:
            QHBoxLayout: Created layout.
        """
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = ui_qt.QtWidgets.QLabel("{0}:".format(label_text))
        label.setMinimumWidth(48)
        layout.addWidget(label)
        layout.addWidget(widget, 1)
        return layout

    @staticmethod
    def create_section_label(text):
        """Creates a section label.

        Args:
            text (str): Label text.

        Returns:
            QLabel: Created label.
        """
        label = ui_qt.QtWidgets.QLabel(text)
        label.setStyleSheet("color: grey; font-weight: bold;")
        label.setMinimumHeight(22)
        return label

    @staticmethod
    def create_separator():
        """Creates a horizontal separator.

        Returns:
            QFrame: Separator widget.
        """
        separator = ui_qt.QtWidgets.QFrame()
        separator.setFrameShape(ui_qt.QtWidgets.QFrame.HLine)
        separator.setFrameShadow(ui_qt.QtWidgets.QFrame.Sunken)
        return separator

    @staticmethod
    def set_combo_value(combo_box, value):
        """Sets a combo box value when present.

        Args:
            combo_box (QComboBox): Combo box to update.
            value (str): Desired text.
        """
        index = combo_box.findText(str(value or ""))
        if index >= 0:
            combo_box.setCurrentIndex(index)

    @staticmethod
    def format_rgb_values(color):
        """Formats RGB values for display.

        Args:
            color (list): RGB color.

        Returns:
            str: Formatted RGB text.
        """
        normalized_color = model.normalize_color(color)
        return "R {0:.3f}, G {1:.3f}, B {2:.3f}".format(
            normalized_color[0],
            normalized_color[1],
            normalized_color[2],
        )

    def apply_stylesheet(self):
        """Applies repository UI styling."""
        stylesheet = ui_res_lib.Stylesheet.maya_dialog_base
        stylesheet += ui_res_lib.Stylesheet.combobox_base
        stylesheet += ui_res_lib.Stylesheet.checkbox_base
        stylesheet += ui_res_lib.Stylesheet.line_edit_base
        stylesheet += ui_res_lib.Stylesheet.btn_push_base
        stylesheet += ui_res_lib.Stylesheet.slider_base
        stylesheet += """
        QLabel#ColorManagerTitle {
            background-color: rgb(95, 95, 95);
            color: rgb(230, 230, 230);
            font-weight: bold;
            padding-left: 10px;
        }
        QPushButton#ColorManagerModeButton {
            background-color: rgb(95, 95, 95);
            color: rgb(235, 235, 235);
            border: none;
            border-left: 1px solid rgb(76, 76, 76);
            border-radius: 0px;
            padding-top: 6px;
            padding-bottom: 6px;
            padding-left: 10px;
            padding-right: 10px;
        }
        QPushButton#ColorManagerModeButton:hover {
            background-color: rgb(112, 112, 112);
        }
        QPushButton#ColorManagerTextButton {
            padding: 6px 10px;
        }
        QPushButton#ColorManagerApplyButton {
            background-color: rgb(188, 188, 188);
            color: rgb(28, 28, 28);
            font-weight: bold;
            border: 1px solid rgb(125, 125, 125);
            padding: 6px 10px;
        }
        QPushButton#ColorManagerApplyButton:hover {
            background-color: rgb(205, 205, 205);
        }
        """
        self.setStyleSheet(stylesheet)
