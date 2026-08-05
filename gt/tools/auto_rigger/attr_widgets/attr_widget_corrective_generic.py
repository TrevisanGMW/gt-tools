"""
Auto Rigger Corrective Generic Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_corrective_base import *

class AttrWidgetModuleCorrectiveGeneric(AttrWidgetModuleBaseCorrective):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for a corrective module.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_module_prefix_suffix()
        self.add_widget_module_orientation()
        self.add_widget_code_data_editor(add_activation=False, add_order_editor=True, add_code_editor=False)
        # Driver Lookup Table ------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Driver Lookup Table")
        self.add_widget_driver_lookup_table()
        # Driven Proxy Table -------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Driven Proxy Table")
        self.add_widget_proxy_parent_table()
        # TRS Multiplier Preferences -----------------------------------------------------------------------------
        self.add_widgets_multiplier_fields()
        # Driven Keys Interface ----------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Driven Keys Interface")
        self.add_module_attr_widget_path(attr_name="driven_keys_dir", dir_only=True)
        # Purge Directory?
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.scroll_content_layout.addLayout(_layout)
        self.clear_target_dir_chk = self.add_module_attr_widget_checkbox(
            attr_name="clear_target_dir", nice_name="Clear Target Directory When Writing", layout=_layout
        )
        self.add_widget_read_write_buttons()
        # Misc --------------------------------------------------------------------------------------------------
        # Initial Refresh
        self.refresh_driver_lookup_table()
