"""
Auto Rigger Head Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleHead(AttrWidget):
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

        self.add_widget_separator_line(label_text="Head Preferences")
        # Create and Add Layout
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        neck_num_slider = self.add_module_attr_widget_int_slider(
            attr_name="neck_number",
            min_int=1,
            tooltip="Number of neck elements between the base neck and the head.",
        )
        refresh_proxies_func = partial(self.refresh_proxies, slider=neck_num_slider)
        neck_num_slider.intValueChanged.connect(refresh_proxies_func)
        self.add_module_attr_widget_text_field(attr_name="prefix_eye_left", layout=_layout)
        self.add_module_attr_widget_text_field(attr_name="prefix_eye_right", layout=_layout)
        self.content_layout.addLayout(_layout)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_checkbox(attr_name="build_jaw", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="build_eyes", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="delete_head_jaw_bind_jnt", layout=_layout)
        self.content_layout.addLayout(_layout)
        self.add_widget_action_buttons()

    def refresh_proxies(self, *args, slider):
        """
        Update the number of middle neck proxies based on the slider value and refresh the proxy table UI.

        Args:
            *args: Additional positional arguments (ignored).
            slider: Slider widget providing the new middle neck count.
        """
        if slider:
            # set spine number
            neck_number = int(slider.int_value())
            self.module.set_mid_neck_num(neck_number)
            # refresh interface
            self.refresh_proxy_basic_table()
