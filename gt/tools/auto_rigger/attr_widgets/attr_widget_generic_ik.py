"""
Auto Rigger Generic Ik Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_ik_base import *

class AttrWidgetModuleGenericIK(AttrWidgetModuleBaseIK):
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
        self.add_widget_separator_line(label_text="Generic IK Preferences")
        self.add_setup_name_field()
        self.add_module_attr_widget_checkbox(
            attr_name="create_twist_joints",
            nice_name="Create Twist Joints",
            tooltip="When active, two twist joints will be included along with their twist setup nodes.\n"
            "These joints are placed between the main joints in hierarchy. Two twist joints per parent/child.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="ik_world",
            nice_name="IK Ctrl World Oriented",
            tooltip="Sets the IK controls in world orientation instead of using the orientation found in the proxy.\n"
            "When checked, the orientation of the end/effector control will match the origin/world.\nWhen unchecked"
            ", the orientation of the joints is used to determine the end/effector control's orientation.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="auto_pole_vector",
            nice_name="Auto Pole Vector",
            tooltip="Applies an automation that makes the pole vector control follow the end/effector control.",
        )
        self.add_module_attr_widget_double_slider(
            attr_name="rig_pose_mid_rot",
            min_double=-180,
            max_double=180,
            nice_name="Control Pose Elbow Rotation",
            tooltip="Controls the offset added to the elbow pose.\n"
            "It will be applied when 'Apply Control Rig Pose' is active.\n"
            "Is often necessary to get the correct elbow behaviour due to the solver implied direction.",
        )

        self.add_widget_action_buttons()
