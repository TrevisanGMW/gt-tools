"""
Color Manager Compatibility Entry Point
"""

from gt.tools.color_manager import color_manager_model


script_name = "Color Manager"
script_version = "?.?.?"

UI_MODE_MINIMAL = color_manager_model.UI_MODE_MINIMAL
UI_MODE_DEFAULT = color_manager_model.UI_MODE_DEFAULT
UI_MODE_COMPLETE = color_manager_model.UI_MODE_COMPLETE
UI_MODES = color_manager_model.UI_MODES
CURRENT_COLOR_UNCONVERTED = color_manager_model.CURRENT_COLOR_UNCONVERTED
CURRENT_COLOR_CONVERTED = color_manager_model.CURRENT_COLOR_CONVERTED
CURRENT_COLOR_MODES = color_manager_model.CURRENT_COLOR_MODES

normalize_saved_colors = color_manager_model.normalize_saved_colors
colors_match = color_manager_model.colors_match
convert_color_for_outliner = color_manager_model.convert_color_for_outliner
convert_color_from_outliner = color_manager_model.convert_color_from_outliner


def build_gui_color_manager():
    """Builds and shows the Color Manager UI.

    Returns:
        ColorManagerController: Active tool controller.
    """
    from gt.tools.color_manager import color_manager_controller
    from gt.tools.color_manager import color_manager_view

    model = color_manager_model.ColorManagerModel()
    view = color_manager_view.ColorManagerView(version=script_version)
    controller = color_manager_controller.ColorManagerController(model=model, view=view)
    controller.start()
    return controller


def get_persistent_settings_color_manager():
    """Loads persistent settings into a new model.

    Returns:
        ColorManagerModel: Model with loaded preferences.
    """
    model = color_manager_model.ColorManagerModel()
    model.load_preferences()
    return model


def reset_persistent_settings_color_manager():
    """Clears persistent Color Manager preferences."""
    model = color_manager_model.ColorManagerModel()
    model.reset_preferences()
    build_gui_color_manager()


def build_gui_help_color_manager():
    """Builds a compact help window for compatibility with legacy callers."""
    cmds = color_manager_model.get_maya_cmds()
    window_name = "build_gui_help_color_manager"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)
    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, sizeable=True)
    cmds.columnLayout(adjustableColumn=True)
    cmds.separator(height=12, style="none")
    cmds.text(label="Color Manager", font="boldLabelFont", align="center")
    cmds.separator(height=8, style="none")
    cmds.text(label="Applies outliner, drawing override, or wireframe colors to selected Maya objects.", align="center")
    cmds.separator(height=8, style="none")
    cmds.button(label="Reset Persistent Settings", height=30, command=lambda *args: reset_persistent_settings_color_manager())
    cmds.separator(height=5, style="none")
    cmds.button(label="OK", height=30, command=lambda *args: cmds.deleteUI(window_name, window=True))
    cmds.separator(height=8, style="none")
    cmds.showWindow(window_name)


if __name__ == "__main__":
    build_gui_color_manager()
