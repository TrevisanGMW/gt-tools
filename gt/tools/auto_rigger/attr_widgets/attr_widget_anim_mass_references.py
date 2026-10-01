"""
Auto Rigger Anim Mass References Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *


class AttrWidgetModuleAnimMassReferences(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.reference_fields = {}  # Key: attribute name, Value: text field
        self.mirror_left_pattern_field = None
        self.mirror_right_pattern_field = None

        self.add_widget_module_header()
        self.add_widget_module_parent()
        self.add_widget_code_data_editor()

        attributes = vars(self.module)
        weight_attrs = [attr for attr in attributes if attr.endswith("_weight")]
        color_attrs = [attr for attr in attributes if attr.endswith("_color")]
        left_attrs = self.module.get_side_reference_attrs("left")
        right_attrs = self.module.get_side_reference_attrs("right")
        center_attrs = ["head", "thorax", "abdomen"]
        general_attrs = ["add_com_to_skeleton", "com_locator_scale"]
        categorized_attrs = weight_attrs + color_attrs + left_attrs + right_attrs + center_attrs + general_attrs

        # General ----------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="General")
        self.add_module_attr_widget_checkbox(
            attr_name="add_com_to_skeleton",
            nice_name="Add COM to Skeleton",
            tooltip="Adds a center of mass joint to the skeleton, so it gets exported with it.",
        )
        self.add_module_attr_widget_int_slider(
            attr_name="com_locator_scale",
            attr_value=None,
            min_int=1,
            max_int=50,
            nice_name="COM Locator Scale",
            tooltip="Size of the center of mass locator.",
        )
        # Anything new that is not categorized yet
        self.add_widget_auto_serialized_fields(ignore_attrs=list(categorized_attrs))

        # References -------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Center References")
        self.add_reference_fields(attr_names=center_attrs)
        self.add_widget_separator_line(label_text="Left References")
        self.add_reference_fields(attr_names=left_attrs)
        self.add_widget_separator_line(label_text="Right References")
        self.add_reference_fields(attr_names=right_attrs)

        # Mirror -----------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Mirror References")
        self.add_widget_mirror_references()

        # Weights ----------------------------------------------------------------------------
        self.add_widget_separator_line(
            label_text="Mass Weights", tooltip="Relative mass of each body part used to calculate the center of mass."
        )
        for attr in weight_attrs:
            self.add_module_attr_widget_double_slider(
                attr_name=attr,
                min_double=0,
                max_double=50,
                precision=3,
            )

        # Colors -----------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Colors")
        for attr in color_attrs:
            self.add_module_attr_widget_double3_spinbox(
                attr_name=attr,
                precision=3,
            )

    # Parameter Widgets ----------------------------------------------------------------------------------------
    def add_reference_fields(self, attr_names):
        """
        Adds a text field for each provided reference attribute and stores them so they can be refreshed.
        Side words are removed from the label since the section already describes the side.
        Args:
            attr_names (list): A list of module attribute names. e.g. ["left_hand", "left_foot"]
        """
        for attr_name in attr_names:
            nice_name = core_str.snake_to_title(attr_name)
            for side in ("Left ", "Right "):
                nice_name = core_str.remove_prefix(input_string=nice_name, prefix=side)
            self.reference_fields[attr_name] = self.add_module_attr_widget_text_field(
                attr_name=attr_name,
                nice_name=nice_name,
                tooltip=f'Scene object used as the "{core_str.snake_to_title(attr_name)}" reference.',
            )

    def add_widget_mirror_references(self):
        """
        Adds the search and replace fields and the buttons used to mirror the side references.
        """
        left_prefix = core_naming.NamingConstants.Prefix.LEFT
        right_prefix = core_naming.NamingConstants.Prefix.RIGHT
        pattern_tooltip = (
            "Search and replace pattern used when mirroring.\n"
            "Mirroring Left to Right replaces the left pattern with the right pattern, and vice versa."
        )

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        left_label = ui_qt.QtWidgets.QLabel("Left Pattern:")
        left_label.setToolTip(pattern_tooltip)
        self.mirror_left_pattern_field = ui_qt.QtWidgets.QLineEdit(f"{left_prefix}_")
        self.mirror_left_pattern_field.setPlaceholderText(f'e.g. "{left_prefix}_"')
        self.mirror_left_pattern_field.setToolTip(pattern_tooltip)
        right_label = ui_qt.QtWidgets.QLabel("Right Pattern:")
        right_label.setToolTip(pattern_tooltip)
        self.mirror_right_pattern_field = ui_qt.QtWidgets.QLineEdit(f"{right_prefix}_")
        self.mirror_right_pattern_field.setPlaceholderText(f'e.g. "{right_prefix}_"')
        self.mirror_right_pattern_field.setToolTip(pattern_tooltip)
        _layout.addWidget(left_label)
        _layout.addWidget(self.mirror_left_pattern_field)
        _layout.addWidget(right_label)
        _layout.addWidget(self.mirror_right_pattern_field)
        self.content_layout.addLayout(_layout)

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        left_to_right_btn = ui_qt.QtWidgets.QPushButton("Mirror Left to Right")
        left_to_right_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_right_arrow))
        left_to_right_btn.setToolTip(
            "Overwrites the right references using the left references,\n"
            "replacing the left pattern with the right pattern."
        )
        left_to_right_btn.clicked.connect(partial(self.on_button_mirror_references_clicked, source_side="left"))
        right_to_left_btn = ui_qt.QtWidgets.QPushButton("Mirror Right to Left")
        right_to_left_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_action_left_arrow))
        right_to_left_btn.setToolTip(
            "Overwrites the left references using the right references,\n"
            "replacing the right pattern with the left pattern."
        )
        right_to_left_btn.clicked.connect(partial(self.on_button_mirror_references_clicked, source_side="right"))
        _layout.addWidget(left_to_right_btn)
        _layout.addWidget(right_to_left_btn)
        self.content_layout.addLayout(_layout)

    # Callbacks ------------------------------------------------------------------------------------------------
    def on_button_mirror_references_clicked(self, *args, source_side):
        """
        Mirrors the side references using the search and replace patterns, then updates the text fields.
        Args:
            *args: Qt signal arguments.
            source_side (str): Side used as source. Accepted values: "left", "right".
        """
        left_pattern = self.mirror_left_pattern_field.text()
        right_pattern = self.mirror_right_pattern_field.text()
        search, replace = (left_pattern, right_pattern) if source_side == "left" else (right_pattern, left_pattern)
        updated_attrs = self.module.mirror_side_references(source_side=source_side, search=search, replace=replace)
        for attr_name, value in updated_attrs.items():
            text_field = self.reference_fields.get(attr_name)
            if text_field:
                text_field.blockSignals(True)
                text_field.setText(value)
                text_field.blockSignals(False)
        if updated_attrs:
            target_side = "right" if source_side == "left" else "left"
            logger.info(
                f'Mirrored {len(updated_attrs)} reference(s) from {source_side} to {target_side} '
                f'(search: "{search}", replace: "{replace}").'
            )
