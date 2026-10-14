"""Auto Rigger descriptions for the shared environment-variable browser."""

from gt.ui.environment_variables_dialog import (
    EnvironmentVariablesDialog as _EnvironmentVariablesDialog,
)


BUILT_IN_ENVIRONMENT_VARIABLE_DESCRIPTIONS = {
    "project-name": "Display name of the current Auto Rigger project.",
    "project-alias": "Optional alias assigned to the current project.",
    "project-sanitized-name": "Project name cleaned for file and folder names.",
    "temp-dir": "Operating system temporary folder.",
    "home-dir": "Current user's home folder.",
    "desktop-dir": "Current user's Desktop folder.",
    "tests-data-dir": "Test data folder packaged with gt-tools.",
    "scene-dir": "Folder containing the current Maya scene, when saved.",
    "project-dir": "Resolved root folder for the current rig project.",
    "project-file-dir": "Folder containing the saved rig project file.",
    "year": "Current year using four digits.",
    "month": "Current month using two digits.",
    "day": "Current day of the month using two digits.",
    "time": "Current time in hours, minutes, and seconds.",
    "hostname": "Name of the computer running Maya.",
    "module-name": "Display name of the currently selected rig module.",
    "module-sanitized-name": "Selected module name cleaned for file and folder names.",
}


class AutoRiggerEnvironmentVariablesDialog(_EnvironmentVariablesDialog):
    """Environment-variable browser configured for Auto Rigger tokens."""

    def __init__(self, refresh_callback, parent=None):
        """Initializes the Auto Rigger environment-variable browser.

        Args:
            refresh_callback (callable): Function returning the latest variables.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(
            refresh_callback=refresh_callback,
            parent=parent,
            title="Auto Rigger Environment Variables",
            descriptions=BUILT_IN_ENVIRONMENT_VARIABLE_DESCRIPTIONS,
        )
