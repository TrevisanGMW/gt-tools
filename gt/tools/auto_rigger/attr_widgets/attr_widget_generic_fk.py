"""
Auto Rigger Generic Fk Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleGenericFK(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Used for generic nodes with options to edit parents and proxies directly.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_code_data_editor(add_activation=True, add_order_editor=True, add_code_editor=True)
        self.add_widget_proxy_parent_table()
        self.add_widget_auto_serialized_fields(
            ignore_attrs=["extra_control_parent_groups", "ctrl_color", "ctrl_shape", "include_scale"]
        )

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_text_field(
            attr_name="ctrl_shape",
            nice_name="Control Shape",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="include_scale",
            nice_name="Include Scale",
            tooltip="When checked, the scale of the control will be unlocked, and a scale constraint between the "
            "control and the joint will be created.",
            layout=_layout,
        )
        self.add_override_color_ctrls_combobox(
            attr_name="ctrl_color",
            nice_name="Control Color",
            tooltip="Select the color of the controls in the module.",
        )
        extra_groups_field = self.add_extra_groups_widget_field(
            attr_name="extra_control_parent_groups",
            nice_name="Extra Parent Groups",
            tooltip="Write here the groups you want to have as offsets, separated by commas, spaces will be deleted.",
            placeholder='Separate group names using commas. e.g. "one, two, three"',
        )
        refresh_name_func = partial(self.refresh_extra_groups, field=extra_groups_field)
        extra_groups_field.textChanged.connect(refresh_name_func)

        self.add_widget_action_buttons()

    def refresh_extra_groups(self, *args, field):
        """
        Updates the module's extra parent groups based on the text from the given input field.

        Args:
            *args: Additional arguments (ignored).
            field (QLineEdit or similar): Text input widget containing the extra groups string.
        """
        if field:
            extra_groups = field.text()
            self.module.set_extra_parent_groups(extra_groups)
            self.refresh_proxy_parent_table()

    def add_extra_groups_widget_field(self, attr_name, nice_name=None, layout=None, tooltip=None, placeholder=None):
        """
        Args:
            attr_name (str, optional): The name of the attribute found in the module class (name of the variable)
                       This name is used to find the variable and set its value in the module instance.
            nice_name (str, optional): If a nice name is provided, that's what is shown in the UI, otherwise an auto
                                       formatted version of the variable name is used instead (title case)
            layout (QBoxLayout, optional): If provided, this layout is used instead of creating a new QHBoxLayout.
            tooltip (str, optional): If provided, this becomes the tooltip for the created element.
            placeholder (str, optional): Placeholder text added to the text-field
        """
        _formatted_attr_name = core_str.snake_to_title(attr_name)
        if nice_name:
            _formatted_attr_name = nice_name
        # Create Layout
        if layout:
            _layout = layout
        else:
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
        # Create Widgets
        label = ui_qt.QtWidgets.QLabel(f"{_formatted_attr_name}:")
        text_field = ui_qt_utils.ConfirmableQLineEdit()
        attr_value = getattr(self.module, attr_name)
        if attr_value:
            attr_value = ",".join(attr_value)
            attr_value = attr_value.replace(" ", "")
            text_field.setText(attr_value)
        text_field.setFixedHeight(35)
        if tooltip:
            text_field.setToolTip(tooltip)
            label.setToolTip(tooltip)
        if placeholder:
            text_field.setPlaceholderText(placeholder)
        # Add to Widgets
        _layout.addWidget(label)
        _layout.addWidget(text_field)
        # Connect
        _func = partial(self.set_module_attr_value_from_field, attr=attr_name, field=text_field)
        text_field.textChanged.connect(_func)

        return text_field
