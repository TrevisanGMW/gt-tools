"""Option window for resetting joint display attributes."""

from gt.ui import option_window as ui_option_window
from gt.ui import resource_library as ui_res_lib
from gt.ui import qt_utils


def open_reset_joint_display_options():
    """Opens joint-display options with scene and selected-joint scopes.

    Returns:
        OptionWindow: Created joint-display option window.
    """
    window = ui_option_window.OptionWindow(
        title="Reset Joint Display",
        object_name="gtResetJointDisplayOptions",
        icon=ui_res_lib.Icon.util_reset_jnt_display,
        description="Selection affects selected joints only. The global multiplier always affects the entire scene.",
        workspace_restore_factory="gt.tools.utility_options.joint_display_options.open_reset_joint_display_options",
    )
    scope_combo = window.add_combobox(
        "Scope", ["Entire Scene", "Selection"], default="Entire Scene",
        tooltip="Affect all joints or only directly selected joints (excluding descendants).",
    )
    radius_field = window.add_double_spinbox(
        "Radius", default=1.0, minimum=0.0, maximum=1000000.0, decimals=3,
        tooltip="Target joint radius. Locked attributes are skipped.",
    )
    draw_style_combo = window.add_combobox(
        "Draw Style", ["Bone", "Multi-child as Box", "None", "Joint"], default="Bone",
    )
    visibility_checkbox = window.add_checkbox(
        "Visibility", checked=True, tooltip="Target visibility of affected joints.",
    )
    global_checkbox = window.add_checkbox(
        "Set Global Scale", checked=True, tooltip="Apply the scene-wide joint display multiplier.",
    )
    global_field = window.add_double_spinbox(
        "Global Multiplier", default=1.0, minimum=0.001, maximum=1000000.0, decimals=3,
        tooltip="Scene-wide joint display scale, including in Selection scope.",
    )
    global_checkbox.toggled.connect(lambda enabled: window.set_row_enabled(global_field, enabled))
    status_label = window.add_label("Ready.")

    def _reset():
        """Applies the displayed values to joints in the current scope."""
        import maya.cmds as cmds
        from gt.core import display as core_display

        joints = None
        if scope_combo.currentText() == "Selection":
            joints = cmds.ls(selection=True, type="joint", long=True) or []
            if not joints:
                status_label.setText("No joints selected. Nothing changed.")
                return
        count = core_display.reset_joint_display(
            jnt_list=joints,
            radius=radius_field.value(),
            draw_style=draw_style_combo.currentIndex(),
            visibility=visibility_checkbox.isChecked(),
            global_scale=global_field.value() if global_checkbox.isChecked() else None,
        )
        status_label.setText(f"Updated {count} joints. Locked or connected attributes may be skipped.")

    window.add_button("Reset Joint Display", _reset, variant="primary", icon=ui_res_lib.Icon.util_reset_jnt_display)
    window.show_window()
    return window


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        open_reset_joint_display_options()
