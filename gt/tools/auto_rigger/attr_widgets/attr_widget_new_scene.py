"""
Auto Rigger New Scene Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *
import gt.tools.auto_rigger.rigger_scene_options as tools_rig_scene_opts


class AttrWidgetModuleNewScene(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Each known scene option is displayed as a row with an activation checkbox and a value field.
        Inactive options are removed from the "scene_options" dictionary, so they are not applied.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.scene_option_widgets = {}  # Key: option key, Value: (activation checkbox, value widget)
        self.unknown_options_label = None

        self.add_widget_module_header()
        self.add_widget_code_data_editor()

        self.add_widget_separator_line(label_text="New Scene Preferences")
        for section in tools_rig_scene_opts.get_scene_option_sections():
            self.add_widget_scene_options_section(section=section)

        # --------------------------------- Utilities ---------------------------------
        self.add_widget_separator_line(label_text="Utilities")
        self.add_widget_scene_options_utilities()
        self.refresh_scene_option_widgets()

    # Parameter Widgets ----------------------------------------------------------------------------------------
    def add_widget_scene_options_section(self, section):
        """
        Adds a titled grid with all the scene options that belong to the provided section.
        Args:
            section (str): Name of the section. e.g. "Units"
        """
        section_label = ui_qt.QtWidgets.QLabel(section)
        section_label.setStyleSheet("color: grey;")
        self.content_layout.addWidget(section_label)

        grid_layout = ui_qt.QtWidgets.QGridLayout()
        grid_layout.setContentsMargins(0, 0, 0, 8)  # L-T-R-B
        grid_layout.setColumnStretch(2, 1)
        row = 0
        for option in tools_rig_scene_opts.get_scene_option_definitions():
            if option.section != section:
                continue
            self.add_widget_scene_option_row(option=option, grid_layout=grid_layout, row=row)
            row += 1
        self.content_layout.addLayout(grid_layout)

    def add_widget_scene_option_row(self, option, grid_layout, row):
        """
        Adds an activation checkbox, a label and a value widget for a scene option.
        Args:
            option (SceneOption): The scene option definition.
            grid_layout (QGridLayout): Layout that receives the widgets.
            row (int): Row index used in the grid layout.
        """
        tooltip = (
            f"{option.tooltip}\n\n"
            f'Dictionary key: "{option.key}"\n'
            f"When unchecked, this option is not applied to the new scene."
        )
        checkbox = ui_qt.QtWidgets.QCheckBox()
        checkbox.setToolTip(tooltip)
        label = ui_qt.QtWidgets.QLabel(f"{option.nice_name}:")
        label.setToolTip(tooltip)
        value_widget = self.create_scene_option_value_widget(option=option)
        value_widget.setToolTip(tooltip)

        grid_layout.addWidget(checkbox, row, 0)
        grid_layout.addWidget(label, row, 1)
        grid_layout.addWidget(value_widget, row, 2)
        self.scene_option_widgets[option.key] = (checkbox, value_widget)

        checkbox.stateChanged.connect(partial(self.on_scene_option_changed, key=option.key))
        if isinstance(value_widget, ui_qt.QtWidgets.QComboBox):
            value_widget.currentIndexChanged.connect(partial(self.on_scene_option_changed, key=option.key))
        elif isinstance(value_widget, ui_qt.QtWidgets.QCheckBox):
            value_widget.stateChanged.connect(partial(self.on_scene_option_changed, key=option.key))
        else:
            value_widget.valueChanged.connect(partial(self.on_scene_option_changed, key=option.key))

    @staticmethod
    def create_scene_option_value_widget(option):
        """
        Creates the widget used to edit the value of a scene option according to its type.
        Args:
            option (SceneOption): The scene option definition.
        Returns:
            QWidget: A QComboBox, QCheckBox, QSpinBox or QDoubleSpinBox.
        """
        option_type = tools_rig_scene_opts.SceneOptionType
        if option.value_type == option_type.ENUM:
            value_widget = ui_qt.QtWidgets.QComboBox()
            for item in option.items:
                value_widget.addItem(str(item), item)
            return value_widget
        if option.value_type == option_type.BOOL:
            return ui_qt.QtWidgets.QCheckBox()
        if option.value_type == option_type.INT:
            value_widget = ui_qt.QtWidgets.QSpinBox()
            value_widget.setMinimum(option.minimum if option.minimum is not None else -2_147_483_648)
            value_widget.setMaximum(option.maximum if option.maximum is not None else 2_147_483_647)
            return value_widget
        value_widget = ui_qt.QtWidgets.QDoubleSpinBox()
        value_widget.setDecimals(option.decimals)
        value_widget.setMinimum(option.minimum if option.minimum is not None else -1e10)
        value_widget.setMaximum(option.maximum if option.maximum is not None else 1e10)
        return value_widget

    def add_widget_scene_options_utilities(self):
        """
        Adds the reset and raw dictionary buttons, and a label listing keys that are only editable as raw data.
        """
        self.unknown_options_label = ui_qt.QtWidgets.QLabel()
        self.unknown_options_label.setWordWrap(True)
        self.unknown_options_label.setStyleSheet("color: grey;")
        self.content_layout.addWidget(self.unknown_options_label)

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        reset_btn = ui_qt.QtWidgets.QPushButton("Reset to Defaults")
        reset_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset))
        reset_btn.setToolTip("Activates all known scene options and sets them to their default values.")
        reset_btn.clicked.connect(self.on_button_reset_scene_options_clicked)
        _layout.addWidget(reset_btn)
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_dictionary_editor(
            attr_name="scene_options",
            layout=_layout,
            tooltip="Opens the scene options as a raw dictionary. Used for advanced or additional keys.",
            dict_editor_tooltip='See "core_scene.set_scene_from_dict()" for all recognized keys and values.',
        )

    # Refresh --------------------------------------------------------------------------------------------------
    def get_scene_options(self):
        """
        Gets the scene options dictionary from the module.
        Returns:
            dict: Scene options dictionary. Empty if the module has no valid options.
        """
        scene_options = getattr(self.module, "scene_options", None)
        if not isinstance(scene_options, dict):
            return {}
        return scene_options

    def refresh_scene_option_widgets(self):
        """
        Updates all scene option widgets so they match the data stored in the module. Signals are blocked
        during the update, so the module data is not modified.
        """
        scene_options = self.get_scene_options()
        for key, (checkbox, value_widget) in self.scene_option_widgets.items():
            option = tools_rig_scene_opts.get_scene_option_definition(key)
            is_enabled = key in scene_options
            value = option.coerce_value(scene_options.get(key)) if is_enabled else option.default
            checkbox.blockSignals(True)
            value_widget.blockSignals(True)
            checkbox.setChecked(is_enabled)
            self.set_scene_option_widget_value(value_widget=value_widget, value=value)
            value_widget.setEnabled(is_enabled)
            checkbox.blockSignals(False)
            value_widget.blockSignals(False)

        unknown_keys = tools_rig_scene_opts.get_unknown_scene_option_keys(scene_options)
        if unknown_keys:
            formatted_keys = ", ".join(f'"{key}"' for key in unknown_keys)
            self.unknown_options_label.setText(f"Additional keys (edit using the raw dictionary): {formatted_keys}")
        self.unknown_options_label.setVisible(bool(unknown_keys))

    @staticmethod
    def set_scene_option_widget_value(value_widget, value):
        """
        Sets the value of a scene option widget.
        Args:
            value_widget (QWidget): A QComboBox, QCheckBox, QSpinBox or QDoubleSpinBox.
            value (any): Value to display.
        """
        if isinstance(value_widget, ui_qt.QtWidgets.QComboBox):
            index = value_widget.findData(value)
            if index == -1:  # Keep values that are not listed as options (e.g. "film")
                value_widget.addItem(str(value), value)
                index = value_widget.findData(value)
            value_widget.setCurrentIndex(index)
        elif isinstance(value_widget, ui_qt.QtWidgets.QCheckBox):
            value_widget.setChecked(bool(value))
        else:
            value_widget.setValue(value)

    @staticmethod
    def get_scene_option_widget_value(value_widget):
        """
        Gets the value from a scene option widget.
        Args:
            value_widget (QWidget): A QComboBox, QCheckBox, QSpinBox or QDoubleSpinBox.
        Returns:
            any: Value currently displayed by the widget.
        """
        if isinstance(value_widget, ui_qt.QtWidgets.QComboBox):
            return value_widget.currentData()
        if isinstance(value_widget, ui_qt.QtWidgets.QCheckBox):
            return value_widget.isChecked()
        return value_widget.value()

    # Callbacks ------------------------------------------------------------------------------------------------
    def on_scene_option_changed(self, *args, key):
        """
        Stores the state of a scene option row in the module. Inactive options are removed from the dictionary.
        Args:
            *args: Qt signal arguments.
            key (str): Scene option key associated with the edited row.
        """
        checkbox, value_widget = self.scene_option_widgets.get(key)
        is_enabled = checkbox.isChecked()
        value_widget.setEnabled(is_enabled)
        self.module.scene_options = tools_rig_scene_opts.get_updated_scene_options(
            scene_options=self.get_scene_options(),
            key=key,
            is_enabled=is_enabled,
            value=self.get_scene_option_widget_value(value_widget),
        )

    def on_button_reset_scene_options_clicked(self, *args):
        """
        Resets all known scene options to their default values. Additional (unknown) keys are preserved.
        Args:
            *args: Qt signal arguments.
        """
        scene_options = self.get_scene_options()
        reset_options = tools_rig_scene_opts.get_default_scene_options()
        for key in tools_rig_scene_opts.get_unknown_scene_option_keys(scene_options):
            reset_options[key] = scene_options.get(key)
        self.module.scene_options = reset_options
        self.refresh_scene_option_widgets()
        logger.info(f'Scene options for "{self.module.get_name()}" were reset to their default values.')

    def set_module_attr_value_from_dictionary_editor(self, *args, attr, data_getter):
        """
        Updates the scene options using the raw dictionary editor, then refreshes the scene option widgets.
        Args:
            attr (str): Name of the module attribute (variable) to set.
            data_getter (callable): A function used to retrieve the data string
        """
        super().set_module_attr_value_from_dictionary_editor(*args, attr=attr, data_getter=data_getter)
        self.refresh_scene_option_widgets()
