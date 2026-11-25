"""
Multi-File Importer Scene

Scene-level settings applied around an import:
- Frame rate, linear unit and up axis: applied before importing (so keys land on the right frames) and,
  optionally, applied again after importing, because some importers (e.g. FBX "Let FBX Set Frame Rate")
  change them.
- Timeline range and review overrides: applied after importing.

Resolution helpers are pure Python. Functions that change the scene import Maya when called.
"""

from gt.tools.multi_file_importer import multi_file_importer_constants as constants
from gt.tools.multi_file_importer import multi_file_importer_formats as formats
from gt.tools.multi_file_importer import multi_file_importer_model as model
import gt.core.timeline as core_timeline
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SCENE_TARGET_SETTINGS = {
    formats.FILE_INFO_FPS: ("frame_rate_source", "frame_rate_custom", "Frame rate"),
    formats.FILE_INFO_LINEAR_UNIT: ("linear_unit_source", "linear_unit_custom", "Linear unit"),
    formats.FILE_INFO_UP_AXIS: ("up_axis_source", "up_axis_custom", "Up axis"),
}
SHADING_FLAGS = {
    constants.SHADING_SMOOTH: {"displayAppearance": "smoothShaded", "wireframeOnShaded": False},
    constants.SHADING_WIREFRAME_ON_SHADED: {"displayAppearance": "smoothShaded", "wireframeOnShaded": True},
    constants.SHADING_WIREFRAME: {"displayAppearance": "wireframe", "wireframeOnShaded": False},
    constants.SHADING_FLAT: {"displayAppearance": "flatShaded", "wireframeOnShaded": False},
}
LIGHTING_FLAGS = {
    constants.LIGHTING_DEFAULT: "default",
    constants.LIGHTING_ALL: "all",
    constants.LIGHTING_FLAT: "flat",
}
IMPORTED_STATUSES = (constants.STATUS_IMPORTED, constants.STATUS_WARNING)


# ------------------------------------------------------------------ pure resolution
def resolve_scene_targets(settings, file_paths, info_reader=formats.read_file_info):
    """Resolves the frame rate, linear unit and up axis to apply before importing.

    Args:
        settings (dict): Tool settings.
        file_paths (list): Files that will be imported, in order.
        info_reader (callable, optional): Function returning file info for a path. Replaceable in tests.

    Returns:
        tuple: (targets, warnings). targets maps FILE_INFO_* keys to values for settings that should
            change; warnings lists messages for values that could not be resolved.
    """
    targets = {}
    warnings = []
    file_paths = list(file_paths or [])
    info_cache = {}
    for info_key, (source_key, custom_key, label) in SCENE_TARGET_SETTINGS.items():
        source = settings.get(source_key, constants.SOURCE_KEEP)
        if source == constants.SOURCE_KEEP:
            continue
        if source == constants.SOURCE_CUSTOM:
            custom_value = settings.get(custom_key)
            if info_key == formats.FILE_INFO_FPS:
                custom_value = model.parse_frame_rate(custom_value)
            if custom_value:
                targets[info_key] = custom_value
            continue
        if not file_paths:
            continue
        file_path = file_paths[0] if source == constants.SOURCE_FIRST else file_paths[-1]
        if file_path not in info_cache:
            info_cache[file_path] = info_reader(file_path) or {}
        value = info_cache[file_path].get(info_key)
        if value:
            targets[info_key] = value
        else:
            warnings.append(f'{label} not stored in "{file_path}"; kept the current value.')
    return targets, warnings


def build_final_targets(targets, original_state):
    """Builds the values to reapply after importing.

    Settings left on "Keep Current" go back to the value the scene had before the import.

    Args:
        targets (dict): Result of resolve_scene_targets.
        original_state (dict): Scene values captured before importing (see capture_scene_state).

    Returns:
        dict: FILE_INFO_* key to value.
    """
    final_targets = dict(original_state or {})
    final_targets.update(targets or {})
    return final_targets


def find_changed_values(expected_state, current_state):
    """Lists scene values that an importer changed.

    Args:
        expected_state (dict): Values the scene should have.
        current_state (dict): Values the scene has now.

    Returns:
        list: Labels of the values that differ, e.g. ["Frame rate"].
    """
    changed_labels = []
    for info_key, (_, _, label) in SCENE_TARGET_SETTINGS.items():
        expected_value = expected_state.get(info_key)
        current_value = current_state.get(info_key)
        if expected_value is None or current_value is None:
            continue
        if info_key == formats.FILE_INFO_FPS:
            if abs(float(expected_value) - float(current_value)) > 0.001:
                changed_labels.append(label)
        elif str(expected_value).lower() != str(current_value).lower():
            changed_labels.append(label)
    return changed_labels


def resolve_timeline_range(settings, records):
    """Resolves the timeline range after importing.

    Records carry two ranges in current scene frames: "time_range" (from keys or the format) and
    "stored_range" (the timeline saved in the file, when the format stores one).

    Args:
        settings (dict): Tool settings.
        records (list): Import records in import order.

    Returns:
        tuple: (start, end) range, or None when the timeline should not change.
    """
    mode = settings.get("timeline_mode", constants.TIMELINE_KEYFRAMES)
    imported_records = [record for record in records if record.get("status") in IMPORTED_STATUSES]
    time_range = None
    if mode == constants.TIMELINE_MANUAL:
        time_range = (settings.get("timeline_start"), settings.get("timeline_end"))
    elif mode == constants.TIMELINE_KEYFRAMES:
        time_range = core_timeline.combine_time_ranges([record.get("time_range") for record in imported_records])
    elif mode == constants.TIMELINE_STORED:
        time_range = core_timeline.combine_time_ranges(
            [record.get("stored_range") or record.get("time_range") for record in imported_records]
        )
    elif mode in (constants.TIMELINE_FIRST, constants.TIMELINE_LAST) and imported_records:
        record = imported_records[0] if mode == constants.TIMELINE_FIRST else imported_records[-1]
        time_range = record.get("stored_range") or record.get("time_range")
    if not core_timeline.is_valid_time_range(time_range):
        return None
    if settings.get("timeline_round") and mode != constants.TIMELINE_MANUAL:
        return core_timeline.round_time_range(time_range, core_timeline.ROUNDING_OUTWARD)
    return float(time_range[0]), float(time_range[1])


def scale_time_range(time_range, from_fps, to_fps):
    """Converts a frame range between frame rates, keeping real-world timing.

    Args:
        time_range (tuple): (start, end) range.
        from_fps (float): Frame rate the range is expressed in.
        to_fps (float): Target frame rate.

    Returns:
        tuple: Converted range, or the input when a rate is unknown.
    """
    if not core_timeline.is_valid_time_range(time_range) or not from_fps or not to_fps:
        return time_range
    ratio = float(to_fps) / float(from_fps)
    return float(time_range[0]) * ratio, float(time_range[1]) * ratio


def build_viewport_flags(settings):
    """Builds the modelEditor flags for the enabled review overrides.

    Args:
        settings (dict): Tool settings.

    Returns:
        dict: modelEditor flag to value.
    """
    flags = {}
    if settings.get("review_textures"):
        flags["displayTextures"] = settings.get("review_textures_value") == constants.SHOW
    if settings.get("review_joints"):
        flags["joints"] = settings.get("review_joints_value") == constants.SHOW
    if settings.get("review_shading"):
        flags.update(SHADING_FLAGS.get(settings.get("review_shading_value"), {}))
    if settings.get("review_lighting"):
        flags["displayLights"] = LIGHTING_FLAGS.get(settings.get("review_lighting_value"), "default")
    if settings.get("review_grid"):
        flags["grid"] = settings.get("review_grid_value") == constants.SHOW
    return flags


# ------------------------------------------------------------------ Maya runtime
def capture_scene_state():
    """Captures the scene frame rate, linear unit and up axis.

    Returns:
        dict: FILE_INFO_* key to value.
    """
    import maya.cmds as cmds
    import gt.core.scene as core_scene

    return {
        formats.FILE_INFO_FPS: core_scene.get_frame_rate(),
        formats.FILE_INFO_LINEAR_UNIT: core_scene.normalize_linear_unit(cmds.currentUnit(query=True, linear=True)),
        formats.FILE_INFO_UP_AXIS: cmds.upAxis(query=True, axis=True),
    }


def apply_scene_targets(targets):
    """Applies frame rate, linear unit and up axis values that differ from the scene.

    Changing the frame rate keeps keys at the same real-world time (they move to new frame numbers).

    Args:
        targets (dict): FILE_INFO_* key to value.

    Returns:
        list: Messages describing what changed.
    """
    import maya.cmds as cmds
    import gt.core.scene as core_scene

    messages = []
    current_state = capture_scene_state()
    frame_rate = targets.get(formats.FILE_INFO_FPS)
    if frame_rate and abs(float(frame_rate) - float(current_state[formats.FILE_INFO_FPS] or 0)) > 0.001:
        frame_rate = float(frame_rate)
        frame_rate = int(frame_rate) if frame_rate.is_integer() else round(frame_rate, 3)
        core_scene.set_frame_rate(frame_rate)
        messages.append(f"frame rate {frame_rate}")
    linear_unit = targets.get(formats.FILE_INFO_LINEAR_UNIT)
    if linear_unit and current_state[formats.FILE_INFO_LINEAR_UNIT] != linear_unit:
        cmds.currentUnit(linear=linear_unit)
        messages.append(f"unit {linear_unit}")
    up_axis = targets.get(formats.FILE_INFO_UP_AXIS)
    if up_axis and current_state[formats.FILE_INFO_UP_AXIS] != up_axis:
        cmds.upAxis(axis=up_axis, rotateView=True)
        messages.append(f"up axis {up_axis.upper()}")
    return messages


def apply_timeline_range(time_range):
    """Sets the playback and animation range.

    Args:
        time_range (tuple): (start, end) range, or None to keep the current range.
    """
    if time_range:
        core_timeline.set_playback_range(time_range, set_current_time=False)


def apply_review_overrides(settings, imported_nodes=None):
    """Applies the enabled review overrides to the scene and viewports.

    Args:
        settings (dict): Tool settings.
        imported_nodes (list, optional): Nodes framed by "Frame imported content".

    Returns:
        list: Warnings for overrides that could not be applied.
    """
    import maya.cmds as cmds
    import gt.core.display as core_display

    warnings = []
    if settings.get("review_anti_aliasing"):
        try:
            cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", True)
            cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", int(settings["review_anti_aliasing_samples"]))
        except Exception as exception:
            warnings.append(f"Anti-aliasing not applied: {exception}")
    viewport_flags = build_viewport_flags(settings)
    has_model_panels = bool(cmds.getPanel(type="modelPanel"))
    if viewport_flags and has_model_panels and not core_display.set_model_panels_options(**viewport_flags):
        warnings.append("Viewport overrides were not applied (no model panel accepted them).")
    if settings.get("review_clip_planes"):
        for camera_shape in cmds.ls(type="camera") or []:
            if cmds.getAttr(f"{camera_shape}.orthographic"):
                continue
            try:
                cmds.setAttr(f"{camera_shape}.nearClipPlane", float(settings["review_clip_near"]))
                cmds.setAttr(f"{camera_shape}.farClipPlane", float(settings["review_clip_far"]))
            except Exception as exception:
                logger.debug(f"Unable to set clip planes on {camera_shape}: {exception}")
    if settings.get("review_go_to_start"):
        cmds.currentTime(cmds.playbackOptions(query=True, minTime=True), edit=True)
    if settings.get("review_frame_content"):
        core_display.frame_nodes_in_viewports(imported_nodes or None)
    if settings.get("review_clear_selection"):
        cmds.select(clear=True)
    return warnings
