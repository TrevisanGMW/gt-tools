"""
Auto Rigger Biped Finger Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleBipedFinger(AttrWidget):
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
        self.add_widget_separator_line(label_text="Finger Preferences")

        textfield_names = "Name"
        finger_mapping = {
            "meta": "meta_name",
            "thumb": "thumb_name",
            "index": "index_name",
            "middle": "middle_name",
            "ring": "ring_name",
            "pinky": "pinky_name",
            "extra": "extra_name",
        }
        # Add Other Attributes
        ignore_attrs = list(finger_mapping.keys()) + list(finger_mapping.values())
        self.add_widget_auto_serialized_fields(ignore_attrs=ignore_attrs)
        # Activation / Name Lines
        for activation_attr, name_attr in finger_mapping.items():
            # Create and Add Layout
            _layout = ui_qt.QtWidgets.QHBoxLayout()
            _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
            self.content_layout.addLayout(_layout)
            # Create Activation Checkbox and Name Textfield
            _checkbox = self.add_module_attr_widget_checkbox(attr_name=activation_attr, layout=_layout)
            _textfield = self.add_module_attr_widget_text_field(
                attr_name=name_attr, layout=_layout, nice_name=textfield_names
            )
            _textfield.setEnabled(_checkbox.isChecked())
            refresh_name_func = partial(self.refresh_name, field=_textfield, label=activation_attr)
            _textfield.editingFinished.connect(refresh_name_func)
            # Create Enabled Connection
            _checkbox.stateChanged.connect(_textfield.setEnabled)
            refresh_proxies_func = partial(self.refresh_proxies)
            _checkbox.stateChanged.connect(refresh_proxies_func)

        self.add_widget_action_buttons()

    def refresh_proxies(self, *args):
        """
        Refresh the module's proxies list and update the proxy table UI.

        Args:
            *args: Additional positional arguments (ignored).
        """
        self.module.refresh_proxies_list()
        self.refresh_proxy_basic_table()

    def refresh_name(self, *args, field, label):
        """
        Update the name of a specific proxy and refresh the proxy table UI.

        Args:
            *args: Additional positional arguments (ignored).
            field (QLineEdit): The text input widget containing the new proxy name.
            label (str): The label identifying which proxy to rename.
        """
        if field:
            proxy_name = field.text()
            self.module.set_proxies_name(label, proxy_name)
            self.refresh_proxy_basic_table()
