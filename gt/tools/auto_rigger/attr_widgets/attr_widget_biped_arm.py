"""
Auto Rigger Biped Arm Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleBipedArm(AttrWidget):
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
        self.add_widget_separator_line(label_text="Arm Preferences")
        self.add_widget_auto_serialized_fields(
            ignore_attrs=[
                "setup_name",
                "clavicle_world",
                "rig_pose_elbow_rot",
                "rig_pose_clavicle_rot",
                "create_twist_joints",
                "auto_pole_vector",
            ]
        )
        self.add_module_attr_widget_checkbox(
            attr_name="create_twist_joints",
            nice_name="Create Twist Joints",
            tooltip="When active, two twist joints will be included along with their twist setup nodes.\n"
            "These joints are placed between the main joints in hierarchy. Two twist joints per parent/child.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="clavicle_world",
            nice_name="Clavicle Ctrl World Orientation",
            tooltip="Sets the clavicle ctrl in world orientation.",
        )
        self.add_module_attr_widget_checkbox(
            attr_name="auto_pole_vector",
            nice_name="Auto Pole Vector",
            tooltip="Applies an automation that makes the pole vector control follow the end/effector control.",
        )
        self.add_module_attr_widget_double_slider(
            attr_name="rig_pose_elbow_rot",
            min_double=-180,
            max_double=180,
            nice_name="Rig Pose Elbow Rotation",
            tooltip="Controls the offset added to the elbow pose.\n"
            "It will be applied when 'Apply Control Rig Pose' is active.\n"
            "Is often necessary to get the correct elbow behaviour due to the solver implied direction.",
        )
        self.add_module_attr_widget_double3_spinbox(
            attr_name="rig_pose_clavicle_rot",
            nice_name="Control Pose Clavicle Rotation",
            tooltip="Controls the offset added to the clavicle pose.\n"
            "It will be applied when 'Apply Control Rig Pose' is active.\n"
            "This will help when a different rotation in the clavicle is necessary to achieve the TPose.",
            minimum=-360,
            maximum=360,
        )
        self.add_widget_action_buttons()
