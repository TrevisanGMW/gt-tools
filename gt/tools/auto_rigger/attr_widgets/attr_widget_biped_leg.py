"""
Auto Rigger Biped Leg Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleBipedLeg(AttrWidget):
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
        self.add_widget_separator_line(label_text="Leg Preferences")
        self.add_widget_auto_serialized_fields(ignore_attrs=["setup_name", "rig_pose_knee_rot"])
        self.add_module_attr_widget_double_slider(
            attr_name="rig_pose_knee_rot",
            min_double=-180,
            max_double=180,
            nice_name="Control Pose Knee Rotation",
            tooltip="Controls the offset added to the knee pose.",
        )
        self.add_widget_action_buttons()
        ensure_coplanarity_label = [
            cb for cb in self.findChildren(ui_qt.QtWidgets.QLabel) if "Ensure Coplanarity" in cb.text()
        ]
        if ensure_coplanarity_label:
            _tooltip = (
                "It ensures that the leg joints are coplanar, in order to improve "
                "the switching between IK and FK. True by default (recommended)."
            )
            ensure_coplanarity_label[0].setToolTip(_tooltip)
