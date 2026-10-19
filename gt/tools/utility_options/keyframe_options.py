"""
Keyframe Utility Options

Option windows for keyframe-related utilities. These assemble a generic OptionWindow and
wire its controls to the keyframe functions in "gt.core.anim".
"""

import gt.ui.option_window as ui_option_window
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_utils as qt_utils
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Combobox option labels
SCOPE_SELECTED = "Selected Objects"
SCOPE_ALL = "All Objects"
KEY_TYPE_TIME = "Time (Animation)"
KEY_TYPE_DOUBLE = "Double (Driven)"
KEY_TYPE_BOTH = "Both"


def _get_key_type_map():
    """
    Builds the mapping between the keyframe-type combobox labels and their scope values.

    Returns:
        dict: Map of display label to KeyframeScope value, ordered Time, Double, Both.
    """
    from gt.core import anim as core_anim

    scope = core_anim.KeyframeScope
    return {
        KEY_TYPE_TIME: scope.TIME,
        KEY_TYPE_DOUBLE: scope.DOUBLE,
        KEY_TYPE_BOTH: scope.BOTH,
    }


def _resolve_obj_list(scope_combo):
    """
    Resolves the object scope from the scope combobox at click time.

    Args:
        scope_combo (QComboBox): The scope combobox.

    Returns:
        list or None: Selected objects unless "All Objects" is explicitly chosen.
            None means scene-wide.
    """
    import maya.cmds as cmds

    if scope_combo.currentText() == SCOPE_ALL:
        return None
    return cmds.ls(selection=True, long=True, objectsOnly=True) or []


def _resolve_key_scope(key_type_combo):
    """
    Resolves the keyframe scope value from the keyframe-type combobox.

    Args:
        key_type_combo (QComboBox): The keyframe-type combobox.

    Returns:
        str: A KeyframeScope value (defaults to KeyframeScope.TIME).
    """
    key_type_map = _get_key_type_map()
    return key_type_map.get(key_type_combo.currentText(), key_type_map[KEY_TYPE_TIME])


def open_delete_keyframes_options():
    """
    Opens the "Delete Keyframes" option window.

    Returns:
        OptionWindow: The created option window.
    """
    from gt.core import anim as core_anim

    window = ui_option_window.OptionWindow(
        title="Delete Keyframes",
        object_name="gtDeleteKeyframesOptions",
        icon=ui_res_lib.Icon.util_delete_keyframes,
        description=(
            "Selected Objects uses the current Maya selection when you press a button. "
            "With no objects selected, the action does nothing."
        ),
        workspace_restore_factory=(
            "gt.tools.utility_options.keyframe_options.open_delete_keyframes_options"
        ),
    )
    scope_combo = window.add_combobox(
        "Scope",
        [SCOPE_SELECTED, SCOPE_ALL],
        default=SCOPE_ALL,
        tooltip="Affect only selected objects or every object in the scene.",
    )
    key_type_combo = window.add_combobox(
        "Keyframe Type",
        [KEY_TYPE_TIME, KEY_TYPE_DOUBLE, KEY_TYPE_BOTH],
        default=KEY_TYPE_TIME,
        tooltip="Time keyframes are standard animation. Double keyframes are Set Driven Keys.",
    )

    def _run_scoped_action(action):
        """Runs a keyframe action with the objects resolved from the current scope.

        Args:
            action (callable): Action that accepts an object list, or None for all objects.
        """
        obj_list = _resolve_obj_list(scope_combo)
        if obj_list is not None and not obj_list:
            import maya.cmds as cmds

            cmds.warning(
                '"Selected Objects" scope is active, but no objects are selected. '
                "No keyframes were changed."
            )
            return
        action(obj_list)

    def _delete_all(obj_list):
        """Deletes all keyframe curves matching the selected options."""
        core_anim.delete_keyframes(
            key_scope=_resolve_key_scope(key_type_combo),
            obj_list=obj_list,
        )

    def _delete_before(obj_list):
        """Deletes keyframes located before the current frame."""
        core_anim.delete_keyframes_before_current_frame(
            obj_list=obj_list,
            key_scope=_resolve_key_scope(key_type_combo),
        )

    def _delete_current(obj_list):
        """Deletes keyframes located on the current frame."""
        core_anim.delete_keyframes_at_current_frame(
            obj_list=obj_list,
            key_scope=_resolve_key_scope(key_type_combo),
        )

    def _delete_after(obj_list):
        """Deletes keyframes located after the current frame."""
        core_anim.delete_keyframes_after_current_frame(
            obj_list=obj_list,
            key_scope=_resolve_key_scope(key_type_combo),
        )

    def _delete_outside_timeline(obj_list):
        """Deletes time keyframes located outside the animation timeline."""
        core_anim.delete_time_keyframes_outside_animation_range(
            obj_list=obj_list,
        )

    def _delete_outside_playback_range(obj_list):
        """Deletes time keyframes located outside the playback range."""
        core_anim.delete_time_keyframes_outside_playback_range(
            obj_list=obj_list,
        )

    window.add_button(
        "Delete Keyframes",
        command=lambda: _run_scoped_action(_delete_all),
        variant="primary",
    )
    window.add_button_row(
        [
            {
                "label": "Delete Outside Timeline",
                "command": lambda: _run_scoped_action(_delete_outside_timeline),
                "tooltip": "Keep time keyframes within Maya's Animation Start and End range.",
            },
            {
                "label": "Delete Outside Playback Range",
                "command": lambda: _run_scoped_action(_delete_outside_playback_range),
                "tooltip": "Keep time keyframes within Maya's current Playback Start and End range.",
            },
        ]
    )
    window.add_button_row(
        [
            {"label": "Delete Before Current Frame", "command": lambda: _run_scoped_action(_delete_before),
             "tooltip": "Remove keys before the current frame (curves are kept)."},
            {"label": "Delete Current Frame", "command": lambda: _run_scoped_action(_delete_current),
             "tooltip": "Remove time keys on the current frame only (curves are kept)."},
            {"label": "Delete After Current Frame", "command": lambda: _run_scoped_action(_delete_after),
             "tooltip": "Remove keys after the current frame (curves are kept)."},
        ]
    )
    window.show_window()
    return window


if __name__ == "__main__":
    with qt_utils.QtApplicationContext():
        open_delete_keyframes_options()
