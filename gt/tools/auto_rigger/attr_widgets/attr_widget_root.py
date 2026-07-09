"""
Auto Rigger Root Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleRoot(AttrWidget):
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
        self.add_widget_module_parent()
        self.add_widget_proxy_basic_table()
        self.add_widget_separator_line(label_text="Root Preferences")

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.addStretch()
        self.content_layout.addLayout(_layout)

        _tooltip = "If active, the root will inherit the rotation found on the root proxy."
        self.add_module_attr_widget_checkbox(
            attr_name="matches_proxy_rot",
            nice_name="Match Proxy Rotation",
            tooltip=_tooltip,
            layout=_layout,
        )
        _layout.addStretch()
        _tooltip = "When enabled, a different scale setup is created for the root joint and its children.\n"
        _tooltip += " 1. Segment scale compensation is disabled on the root joint's children.\n"
        _tooltip += " 2. Inherit transformations are disabled on the root joint.\n"
        _tooltip += " 3. The skeleton group's scale is directly connect to the root joint scale.\n"
        _tooltip += "This allows compatibility with game engines as the root drives the scale directly."
        self.add_module_attr_widget_checkbox(
            attr_name="enable_scale",
            tooltip=_tooltip,
            layout=_layout,
        )
        _layout.addStretch()
        self.add_widget_action_buttons()


# IK Base (Used by other AttrWidgets)
