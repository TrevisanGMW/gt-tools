"""
Auto Rigger Attribute Hub Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleAttributeHub(AttrWidget):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Attribute Hub Preferences")
        self.add_widget_code_data_editor()
        self.add_widget_auto_serialized_fields(ignore_attrs=["parent_constraint_type", "attr_mapping", "attr_values"])
        import gt.core.constraint as core_cnstr

        _potential_constraints = [
            core_cnstr.ConstraintTypes.POINT,
            core_cnstr.ConstraintTypes.PARENT,
            core_cnstr.ConstraintTypes.ORIENT,
        ]
        self.add_module_attr_widget_combobox(
            attr_name="parent_constraint_type",
            items=_potential_constraints,
        )
        # Create and Add Layout
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_dictionary_editor(attr_name="attr_mapping", layout=_layout)
        self.add_module_attr_widget_dictionary_editor(attr_name="attr_values", layout=_layout)
        self.content_layout.addLayout(_layout)
        self.add_widget_action_buttons()
