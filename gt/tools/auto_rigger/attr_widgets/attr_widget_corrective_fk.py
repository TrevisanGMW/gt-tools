"""
Auto Rigger Corrective Fk Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_corrective_base import *

class AttrWidgetModuleCorrectiveFK(AttrWidgetModuleBaseCorrective):
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
        # Driven Keys Interface ----------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Control Preferences")
        self.add_module_attr_widget_text_field(attr_name="ctrl_shape", nice_name="Control Shape")
        self.add_override_color_ctrls_combobox(
            attr_name="ctrl_color",
            nice_name="Control Color",
            tooltip="Select the color of the controls in the module.",
        )
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
        self.add_module_attr_widget_checkbox(
            attr_name="include_scale",
            nice_name="Include Scale",
            tooltip="When checked, the scale of the control will be unlocked, and a scale constraint between the "
            "control and the corrective joint will be created.",
            layout=_layout,
        )
        self.add_widget_read_write_buttons()
        # Misc --------------------------------------------------------------------------------------------------
        # Initial Refresh
        self.refresh_driver_lookup_table()

    def on_btn_set_driven_key_clicked(self, index):
        """
        Opens the Maya dialog for setting driven keys with pre-populated values.
        Args:
            index (int): Index used to determine the driver attribute.
        """
        item = self.table_driver_lookup_wdg.item(index, 2)  # 2 = Attribute
        if item:
            import maya.cmds as cmds
            import maya.mel as mel

            driver_attr = item.text()
            if not cmds.objExists(driver_attr):
                logger.warning(f"Driver attribute not available. Make sure it exists and the rig built then try again.")
                return
            driven_grp = self.module.get_driven_groups()
            cmds.select(driven_grp, replace=True)
            mel.eval('setDrivenKeyWindow "" {""};')
            driver = driver_attr
            if "." in driver_attr:
                driver = driver_attr.split(".")[0]
            cmds.select(driver, replace=True)
            mel.eval('updateSetDrivenWnd("driver", "", {""});')
            cmds.select(clear=True)
        else:
            logger.warning(f"No driver attribute provided.")
