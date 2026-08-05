"""Create FK Driver model and Maya runtime operations."""

import logging


logger = logging.getLogger(__name__)


DEFAULT_CUSTOM_CURVE_CODE = "cmds.circle(normal=[1, 0, 0], radius=1.0, constructionHistory=False)"
CUBE_CURVE_POINTS = [
    [-0.5, 0.5, 0.5], [0.5, 0.5, 0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5],
    [-0.5, 0.5, 0.5], [-0.5, -0.5, 0.5], [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5],
    [0.5, -0.5, 0.5], [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5],
    [0.5, 0.5, -0.5], [0.5, -0.5, -0.5], [-0.5, -0.5, -0.5], [-0.5, 0.5, -0.5],
]
PIN_CURVE_POINTS = [
    [0.0, 0.0, 0.0], [0.0, 4.0, 0.0], [0.57, 4.58, 0.0], [0.4, 4.99, 0.0],
    [0.0, 5.15, 0.0], [-0.4, 4.99, 0.0], [-0.57, 4.58, 0.0], [-0.4, 4.18, 0.0],
    [0.0, 4.0, 0.0],
]


class CreateFkDriverModel:
    """Stores Create FK Driver settings and performs Maya scene operations."""

    DEFAULT_SETTINGS = {
        "mimic_hierarchy": True,
        "constraint_joints": True,
        "colorize_controls": True,
        "include_hierarchy": True,
        "curve_type": "Circle",
        "curve_radius": 1.0,
        "joint_suffix": "_JNT",
        "control_suffix": "_CTRL",
        "control_group_suffix": "_offset",
        "ignored_strings": "endJnt, eye",
        "custom_curve_code": DEFAULT_CUSTOM_CURVE_CODE,
    }

    def __init__(self):
        """Initializes default settings and loads stored preferences."""
        self.settings = dict(self.DEFAULT_SETTINGS)
        self.load_preferences()

    @staticmethod
    def parse_comma_separated(value):
        """Converts comma-separated text into clean non-empty values.

        Args:
            value (str): Comma-separated text.

        Returns:
            list: Clean values in input order.
        """
        return [item.strip() for item in str(value or "").split(",") if item.strip()]

    def load_preferences(self):
        """Loads current settings from the repository preference system."""
        try:
            from gt.core.prefs import Prefs

            preferences = Prefs("create_fk_driver")
            raw_preferences = preferences.get_raw_preferences()
            for key, default_value in self.DEFAULT_SETTINGS.items():
                value = raw_preferences.get(key, default_value)
                if isinstance(default_value, bool):
                    value = bool(value)
                elif isinstance(default_value, float):
                    value = float(value)
                else:
                    value = str(value)
                self.settings[key] = value
        except Exception as exception:
            logger.debug("Unable to load Create FK Driver preferences: %s", exception)

    def save_preferences(self):
        """Writes current settings to the repository preference system."""
        from gt.core.prefs import Prefs

        preferences = Prefs("create_fk_driver")
        preferences.set_raw_preferences(dict(self.settings))
        preferences.save()

    def set_setting(self, key, value, save=True):
        """Updates one known setting.

        Args:
            key (str): Setting name.
            value (object): New setting value.
            save (bool, optional): Whether to immediately save preferences.
        """
        if key not in self.DEFAULT_SETTINGS:
            return
        self.settings[key] = value
        if save:
            self.save_preferences()

    def reset_preferences(self):
        """Restores defaults and writes them to preferences."""
        self.settings = dict(self.DEFAULT_SETTINGS)
        self.save_preferences()

    def generate_fk_drivers(self):
        """Creates FK controls and driver groups for selected Maya joints.

        Returns:
            list: Created control transforms.

        Raises:
            RuntimeError: If no joints are selected or a required suffix is empty.
        """
        import maya.cmds as cmds

        selected_joints = cmds.ls(selection=True, type="joint", long=True) or []
        if not selected_joints:
            raise RuntimeError("Select at least one joint before creating FK drivers.")
        if self.settings.get("include_hierarchy"):
            descendants = cmds.listRelatives(selected_joints, allDescendents=True, type="joint", fullPath=True) or []
            selected_joints = selected_joints + list(reversed(descendants))
        selected_joints = list(dict.fromkeys(selected_joints))
        ignored_strings = self.parse_comma_separated(self.settings.get("ignored_strings"))
        selected_joints = [
            joint for joint in selected_joints
            if not any(ignore_text in self._short_name(joint) for ignore_text in ignored_strings)
        ]
        created_controls = []
        control_by_joint = {}
        cmds.undoInfo(openChunk=True, chunkName="Create FK Drivers")
        try:
            for joint in selected_joints:
                joint_short_name = self._short_name(joint)
                joint_suffix = str(self.settings.get("joint_suffix") or "")
                if joint_suffix and joint_short_name.endswith(joint_suffix):
                    base_name = joint_short_name[:-len(joint_suffix)]
                else:
                    base_name = joint_short_name
                control_name = base_name + str(self.settings.get("control_suffix") or "")
                group_name = base_name + str(self.settings.get("control_group_suffix") or "")
                control = self._create_control(control_name)
                group = cmds.group(name=group_name, empty=True)
                cmds.parent(control, group)
                constraint = cmds.parentConstraint(joint, group)
                cmds.delete(constraint)
                if self.settings.get("colorize_controls"):
                    self._colorize_control(control)
                if self.settings.get("constraint_joints"):
                    cmds.parentConstraint(control, joint)
                control_by_joint[joint] = control
                created_controls.append(control)

            if self.settings.get("mimic_hierarchy"):
                for joint, control in control_by_joint.items():
                    parent_joint = cmds.listRelatives(joint, parent=True, fullPath=True) or []
                    if parent_joint and parent_joint[0] in control_by_joint:
                        group = cmds.listRelatives(control, parent=True, fullPath=True)[0]
                        cmds.parent(group, control_by_joint[parent_joint[0]])
            cmds.select(created_controls or [], replace=True)
            return created_controls
        finally:
            cmds.undoInfo(closeChunk=True, chunkName="Create FK Drivers")

    def _create_control(self, control_name):
        """Creates the configured control curve.

        Args:
            control_name (str): Requested transform name.

        Returns:
            str: Created control transform.
        """
        import maya.cmds as cmds

        curve_type = self.settings.get("curve_type") or "Circle"
        radius = float(self.settings.get("curve_radius") or 1.0)
        if curve_type == "Cube":
            control = cmds.curve(point=CUBE_CURVE_POINTS, degree=1)
            cmds.scale(radius, radius, radius, control)
            cmds.makeIdentity(control, apply=True, scale=True)
        elif curve_type == "Pin":
            control = cmds.curve(point=PIN_CURVE_POINTS, degree=1)
            cmds.scale(radius, radius, radius, control)
            cmds.makeIdentity(control, apply=True, scale=True)
        elif curve_type == "Custom Python":
            control = self._create_custom_control()
        else:
            control = cmds.circle(normal=[1, 0, 0], radius=radius, constructionHistory=False)[0]
        return cmds.rename(control, control_name)

    def _create_custom_control(self):
        """Executes user-provided Maya curve code and returns its new transform.

        Returns:
            str: Created transform.

        Raises:
            RuntimeError: If the code creates no transform.
        """
        import maya.cmds as cmds

        before = set(cmds.ls(transforms=True) or [])
        local_scope = {"cmds": cmds}
        exec(str(self.settings.get("custom_curve_code") or ""), {"__builtins__": {}}, local_scope)
        created = [node for node in cmds.ls(transforms=True) or [] if node not in before]
        if not created:
            raise RuntimeError("Custom curve code did not create a transform.")
        return created[-1]

    @staticmethod
    def _short_name(node):
        """Gets a DAG node's short name.

        Args:
            node (str): Node path.

        Returns:
            str: Short node name.
        """
        return str(node or "").split("|")[-1]

    @staticmethod
    def _colorize_control(control):
        """Applies the established side-based control colors.

        Args:
            control (str): Control transform.
        """
        import maya.cmds as cmds

        short_name = CreateFkDriverModel._short_name(control).lower()
        color_index = 17
        if short_name.startswith("right_") or short_name.startswith("r_"):
            color_index = 13
        elif short_name.startswith("left_") or short_name.startswith("l_"):
            color_index = 6
        cmds.setAttr(control + ".overrideEnabled", 1)
        cmds.setAttr(control + ".overrideColor", color_index)
