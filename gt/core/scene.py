"""
Scene Utilities

Import Line:
    import gt.core.scene as core_scene
"""

import maya.cmds as cmds
import subprocess
import logging
import math
import sys
import os
import re
import html

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_FRAME_RATE = 48000
DEFAULT_FILE_EXTENSIONS = (".ma", ".mb", ".fbx")


def get_frame_rate():
    """
    Get the scene frame rate as a number
    Result:
        float: describing the scene frame rate. If operation fails "0.0" is returned instead
    """
    frame_rate = cmds.currentUnit(query=True, time=True) or ""
    if frame_rate == "film":
        return 24.0
    if frame_rate == "show":
        return 48.0
    if frame_rate == "pal":
        return 25.0
    if frame_rate == "ntsc":
        return 30.0
    if frame_rate == "palf":
        return 50.0
    if frame_rate == "ntscf":
        return 60.0
    if "fps" in frame_rate:
        return float(frame_rate.replace("fps", ""))
    logger.debug('Unable to detect scene frame rate. Returned "0.0".')
    return 0.0


def set_frame_rate(frame_rate):
    """
    Sets the frame rate of the current Maya scene.

    This function allows you to set the frame rate of the current Maya scene
    by providing either a numerical frame rate (e.g., 24, 30, 60) or a valid
    time unit string (e.g., "film", "ntsc", "palf"). The function maps common
    frame rates to Maya's internal time unit names and sets the scene's frame
    rate accordingly.

    Args:
        frame_rate (int | float | str): The desired frame rate for the scene.
            This can be either a number representing the frame rate (e.g., 24, 30, 60)
            or a string representing Maya's internal time unit name
            (e.g., "film", "ntsc", "palf").

    Notes:
        - If an unsupported numerical frame rate is provided, the function logs a
          debug message indicating that the input is invalid.
        - If an unsupported or invalid string is provided, the function logs a
          debug message indicating that the input is invalid.

    Examples:
        To set the scene's frame rate to 24 fps:
        set_frame_rate(24)

        To set the scene's frame rate using a time unit string:
        set_frame_rate("film")
    """
    # Dictionary mapping common frame-rates to Maya's internal time unit names
    frame_rate_mapping = {
        23.976: "23.976fps",
        24: "film",
        25: "pal",
        29.97: "29.97fps",
        30: "ntsc",
        47.952: "47.952fps",
        48: "show",
        50: "palf",
        59.94: "59.94fps",
        60: "ntscf",
    }

    if isinstance(frame_rate, str):
        # Set the scene's frame rate directly if a valid string is provided
        if frame_rate in frame_rate_mapping.values():
            cmds.currentUnit(time=frame_rate)
            logger.debug(f"Scene frame rate set to {frame_rate}.")
            return
        elif frame_rate.endswith("fps"):
            try:
                cmds.currentUnit(time=frame_rate)
                return
            except Exception as e:
                logger.debug(f"Unrecognized frame rate value. Issue: {e}")
    elif isinstance(frame_rate, (int, float)):
        # Check if the provided numerical frame-rate is supported
        if frame_rate in frame_rate_mapping:
            # Set the scene's frame rate using the mapped value
            cmds.currentUnit(time=frame_rate_mapping[frame_rate])
            logger.debug(f"Scene frame rate set to {frame_rate} fps.")
            return
        elif frame_rate <= MAX_FRAME_RATE:
            try:
                cmds.currentUnit(time=f"{int(frame_rate)}fps")
                return
            except Exception as e:
                logger.debug(f"Unrecognized frame rate value. Issue: {e}")
    logger.debug("Invalid input. Please provide a number or a valid time unit string.")


def get_distance_in_meters():
    """
    Get the number units necessary to make a meter
    Returns:
        float describing the amount of units necessary to make a meter
    """
    unit = cmds.currentUnit(query=True, linear=True) or ""
    if unit == "mm":
        return 1000
    elif unit == "cm":
        return 100
    elif unit == "km":
        return 0.001
    elif unit == "in":
        return 39.3701
    elif unit == "ft":
        return 3.28084
    elif unit == "yd":
        return 1.09361
    elif unit == "mi":
        return 0.000621371
    return 1


def open_scene_file(file_path, force=False):
    """Opens a scene file after resolving unsaved changes.

    Args:
        file_path (str): Scene file path to open.
        force (bool, optional): Force opening and discard unsaved changes.
            Defaults to False.
    """
    operation_force = _resolve_scene_open_force(force=bool(force))
    if operation_force is None:
        return False
    cmds.file(file_path, open=True, force=operation_force)
    return True


def _resolve_scene_open_force(force=False):
    """Resolves whether a scene file operation may discard changes.

    Args:
        force (bool, optional): Force the operation without asking. Defaults
            to False.

    Returns:
        bool or None: Force value to use for the Maya file command, or None
        when the user cancels the operation.
    """
    if force or not cmds.file(query=True, modified=True):
        return bool(force)

    user_choice = cmds.confirmDialog(
        title="Unsaved Changes",
        message="The current file has unsaved changes. What would you like to do?",
        button=["Save", "Don't Save", "Cancel"],
        defaultButton="Cancel",
        cancelButton="Cancel",
        dismissString="Cancel",
        icon="warning",
    )
    if user_choice == "Cancel":
        return None
    if user_choice == "Save":
        cmds.file(save=True)
        return False
    return True


def _normalize_file_extensions(file_extensions):
    """Normalizes a file-extension setting into a unique lowercase tuple.

    Args:
        file_extensions (str or list or tuple): Extensions separated by commas,
            spaces, or semicolons. A leading dot and wildcard are optional.

    Returns:
        tuple: Normalized file extensions, including their leading dots.
    """
    if file_extensions is None:
        file_extensions = DEFAULT_FILE_EXTENSIONS
    if isinstance(file_extensions, str):
        file_extensions = re.split(r"[,;\s]+", file_extensions)

    normalized_extensions = []
    for file_extension in file_extensions:
        extension = str(file_extension).strip().lower().lstrip("*")
        if extension in ("", "and", "or"):
            continue
        if not extension.startswith("."):
            extension = f".{extension}"
        if extension not in normalized_extensions:
            normalized_extensions.append(extension)
    return tuple(normalized_extensions)


def get_scene_files(directory_path, file_extensions=None):
    """Lists supported scene files in a directory in deterministic order.

    Args:
        directory_path (str): Directory to search.
        file_extensions (str or list or tuple, optional): Accepted file
            extensions. Defaults to Maya ASCII, Maya Binary, and FBX files.

    Returns:
        list: Absolute file paths sorted by filename, or an empty list.
    """
    directory_path = os.path.abspath(os.path.expanduser(str(directory_path or "")))
    extensions = _normalize_file_extensions(file_extensions)
    if not os.path.isdir(directory_path) or not extensions:
        return []

    try:
        file_names = os.listdir(directory_path)
    except OSError as exception:
        logger.warning(f'Unable list scene files in "{directory_path}". Issue: "{exception}".')
        return []

    file_paths = []
    for file_name in file_names:
        file_path = os.path.join(directory_path, file_name)
        if not os.path.isfile(file_path):
            continue
        if os.path.splitext(file_name)[1].lower() in extensions:
            file_paths.append(os.path.abspath(file_path))
    return sorted(file_paths, key=lambda path: (os.path.basename(path).casefold(), path.casefold()))


def get_adjacent_file_data(
    current_file_path,
    direction,
    file_extensions=None,
    loop_directory=False,
):
    """Resolves a neighboring supported file and its folder position.

    Args:
        current_file_path (str): Current scene file path.
        direction (int): Navigation direction. Use ``-1`` for previous or
            ``1`` for next.
        file_extensions (str or list or tuple, optional): Accepted file
            extensions. Defaults to Maya ASCII, Maya Binary, and FBX files.
        loop_directory (bool, optional): Wraps navigation at either end of the
            directory. Defaults to False.

    Returns:
        dict or None: Data containing ``file_path``, ``position``, and ``total``
        when an adjacent file exists; otherwise ``None``.
    """
    if direction not in (-1, 1):
        raise ValueError("File navigation direction must be -1 or 1.")

    current_file_path = os.path.abspath(os.path.expanduser(str(current_file_path or "")))
    directory_path = os.path.dirname(current_file_path)
    scene_files = get_scene_files(directory_path, file_extensions=file_extensions)
    normalized_current_path = os.path.normcase(os.path.normpath(current_file_path))
    normalized_scene_files = [
        os.path.normcase(os.path.normpath(scene_file)) for scene_file in scene_files
    ]
    if normalized_current_path not in normalized_scene_files:
        return None

    current_index = normalized_scene_files.index(normalized_current_path)
    adjacent_index = current_index + direction
    if adjacent_index < 0 or adjacent_index >= len(scene_files):
        if not loop_directory:
            return None
        adjacent_index %= len(scene_files)

    return {
        "file_path": scene_files[adjacent_index],
        "position": adjacent_index + 1,
        "total": len(scene_files),
    }


def reload_file(force=False):
    """Reopens the current file, optionally bypassing Maya's save warning.

    Args:
        force (bool, optional): Force the file open and discard unsaved changes.
            Defaults to False.

    Returns:
        bool: True when a saved scene was sent to Maya for reopening.
    """
    if cmds.file(query=True, exists=True):  # Check to see if it was ever saved
        file_path = cmds.file(query=True, expandName=True)
        if file_path is not None:
            return open_scene_file(file_path, force=bool(force))
    cmds.warning("Unable to reload. File was never saved.")
    return False


def force_reload_file():
    """Reopens the current file and discards unsaved changes.

    Returns:
        bool: True when a saved scene was sent to Maya for reopening.
    """
    return reload_file(force=True)


def open_adjacent_file(
    direction,
    file_extensions=None,
    force=False,
    loop_directory=False,
):
    """Opens the previous or next supported file in the current folder.

    Args:
        direction (int): Navigation direction. Use ``-1`` for previous or
            ``1`` for next.
        file_extensions (str or list or tuple, optional): Accepted file
            extensions. Defaults to Maya ASCII, Maya Binary, and FBX files.
        force (bool, optional): Force opening and discard unsaved changes.
            Defaults to False.
        loop_directory (bool, optional): Wraps navigation at either end of the
            directory. Defaults to False.

    Returns:
        dict or None: Opened-file data containing ``file_path``, ``position``,
        and ``total`` when successful; otherwise ``None``.
    """
    if not cmds.file(query=True, exists=True):
        cmds.warning("Unable to open adjacent file. The current scene was never saved.")
        return None

    current_file_path = cmds.file(query=True, expandName=True)
    adjacent_file_data = get_adjacent_file_data(
        current_file_path=current_file_path,
        direction=direction,
        file_extensions=file_extensions,
        loop_directory=loop_directory,
    )
    if not adjacent_file_data:
        cmds.warning("Unable to open adjacent file. No matching file was found.")
        return None

    adjacent_file_path = adjacent_file_data["file_path"]
    if not open_scene_file(adjacent_file_path, force=bool(force)):
        return None
    direction_label = "previous" if direction == -1 else "next"
    import gt.core.feedback as core_fback

    filename = html.escape(os.path.basename(adjacent_file_path))
    direction_style = "font-weight:bold;text-decoration:underline;"
    filename_style = "color:#66CCFF;"
    count_style = "color:#FFCC66;font-weight:bold;text-decoration:underline;"
    feedback_message = (
        "Open "
        f'<span style="{direction_style}">{direction_label}</span> file '
        f'<span style="{filename_style}">"{filename}"</span> - '
        f'<span style="{count_style}">('
        f'{adjacent_file_data["position"]} of {adjacent_file_data["total"]})</span>'
    ).strip()
    feedback = core_fback.FeedbackMessage(
        general_overwrite=feedback_message,
        style_general=None,
    )
    feedback.print_inview_message(stay_time=4000, system_write=False)
    return adjacent_file_data


def open_file_dir():
    """Opens the directory where the Maya file is saved"""
    fail_message = "Unable to open directory. Path printed to script editor instead."

    def open_dir(path):
        """
        Open path
        Args:
            path (str): Path to open using
        """
        if sys.platform == "win32":  # Windows
            # explorer needs forward slashes
            filebrowser_path = os.path.join(os.getenv("WINDIR"), "explorer.exe")
            path = os.path.normpath(path)

            if os.path.isdir(path):
                subprocess.run([filebrowser_path, path])
            elif os.path.isfile(path):
                subprocess.run([filebrowser_path, "/select,", path])
        elif sys.platform == "darwin":  # Mac-OS
            try:
                subprocess.call(["open", "-R", path])
            except Exception as exception:
                logger.debug(str(exception))
                print(path)
                cmds.warning(fail_message)
        else:  # Linux/Other
            print(path)
            cmds.warning(fail_message)

    if cmds.file(query=True, exists=True):  # Check to see if it was ever saved
        file_path = cmds.file(query=True, expandName=True)
        if file_path is not None:
            try:
                open_dir(file_path)
            except Exception as e:
                logger.debug(str(e))
                print(file_path)
                cmds.warning(fail_message)
    else:
        cmds.warning("Unable to open directory. File was never saved.")


def set_scene_from_dict(scene_dict):
    """
    Sets various scene options in Maya based on key-value pairs from the input dictionary.

    Args:
    scene_dict (dict):
        A dictionary containing scene settings. The following keys are supported:

        "linear_unit" (str): Sets the scene's linear unit (e.g., 'cm', 'm').
        "angular_unit" (str): Sets the scene's angular unit (e.g., 'deg', 'rad').
        "frame_rate" (str, int): Sets the scene's frame rate (e.g., 30, 'pal'). Calls `set_frame_rate` function.
        "multi_sample" (bool): Enables or disables multi-sample antialiasing.
        "multi_sample_count" (int): Sets the level of multi-sample antialiasing.
        "persp_clip_plane_near" (float): Sets the near clipping plane of the perspective camera.
        "persp_clip_plane_far" (float): Sets the far clipping plane of the perspective camera.
        "display_textures" (bool): Enables texture visibility across all viewports if set to True.
        "playback_frame_start" (float): Sets the start frame of the playback timeline. (range)
        "playback_frame_end" (float): Sets the end frame of the playback timeline. (range)
        "animation_frame_start" (float): Sets the start frame of the animation timeline.
        "animation_frame_end" (float): Sets the end frame of the animation timeline.
        "animation_frame_start_rounding" (bool): Rounds the start frame to the nearest integer.
        "animation_frame_end_rounding" (bool): Rounds the end frame to the nearest integer.
        "playback_frame_start_rounding" (bool): Rounds playback start frame to the nearest integer. (range)
        "playback_frame_end_rounding" (bool): Rounds playback end frame to the nearest integer. (range)
        "animation_frame_start_floor": (bool): Floors (rounds down) the start frame to the nearest integer.
        "animation_frame_end_ceil": (bool): Floors the end frame to the nearest integer.
        "playback_frame_start_floor" (bool): Ceils (rounds up) playback start frame to the nearest integer. (range)
        "playback_frame_end_ceil" (bool): Ceils (rounds up) playback end frame to the nearest integer. (range)
        "current_time" (float): Sets the current time on the timeline.
        "use_default_material" (bool): Sets the state of the "Use default material" panel preference.
        "grid_size" (float): Sets the grid size.
        "grid_spacing" (float): Sets the grid spacing.
        "grid_divisions" (int): Sets the grid division.

    This function adjusts the scene's units, frame rate, multi-sample settings, clipping planes,
    texture visibility, playback options, animation options, time rounding and more based on values
    provided in the dictionary. Each option is set only if its corresponding key exists in the dictionary.
    Unrecognized keys are ignored.
    """
    # Set Scene Linear Unit (Scale)
    option_key = "linear_unit"
    if option_key in scene_dict:
        cmds.currentUnit(linear=scene_dict.get(option_key))

    # Set Scene Angular Unit
    option_key = "angular_unit"
    if option_key in scene_dict:
        cmds.currentUnit(angle=scene_dict.get(option_key))

    # Set scene frame-rate
    option_key = "frame_rate"
    if option_key in scene_dict:
        set_frame_rate(scene_dict.get(option_key))

    # Set the multi-sample count (multisampling anti-aliasing level)
    option_key = "multi_sample"
    if option_key in scene_dict:
        _value = scene_dict.get(option_key)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", _value)
    option_key = "multi_sample_count"
    if option_key in scene_dict:
        _value = scene_dict.get(option_key)
        cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", _value)

    # Persp Camera Setup
    option_key = "persp_clip_plane_near"
    if option_key in scene_dict:
        _value = scene_dict.get(option_key)
        cmds.setAttr("perspShape.nearClipPlane", _value)
    option_key = "persp_clip_plane_far"
    if option_key in scene_dict:
        _value = scene_dict.get(option_key)
        cmds.setAttr("perspShape.farClipPlane", _value)

    # Enable texture visibility
    option_key = "display_textures"
    if option_key in scene_dict and scene_dict.get(option_key) is True:
        all_viewports = cmds.getPanel(type="modelPanel") or []
        # Iterate through each viewport and enable texture display
        for viewport in all_viewports:
            cmds.modelEditor(viewport, edit=True, displayTextures=True)

    # ----------------------------------------- Timeline management -----------------------------------------
    # Playback Start and End
    option_key = "playback_frame_start"
    if option_key in scene_dict:
        cmds.playbackOptions(min=scene_dict.get(option_key))
    option_key = "playback_frame_end"
    if option_key in scene_dict:
        cmds.playbackOptions(max=scene_dict.get(option_key))

    # Animation Start and End
    option_key = "animation_frame_start"
    if option_key in scene_dict:
        cmds.playbackOptions(animationStartTime=scene_dict.get(option_key))
    option_key = "animation_frame_end"
    if option_key in scene_dict:
        cmds.playbackOptions(animationEndTime=scene_dict.get(option_key))

    # Playback Start End Rounding
    current_frame = cmds.currentTime(q=True)
    option_key = "playback_frame_start_rounding"
    if option_key in scene_dict:
        start_frame = cmds.playbackOptions(q=True, minTime=True)
        rounded_current_frame = math.floor(current_frame)
        rounded_start_frame = math.floor(start_frame)
        cmds.currentTime(rounded_current_frame)
        cmds.playbackOptions(min=rounded_start_frame)
    option_key = "animation_frame_end_rounding"
    if option_key in scene_dict:
        end_frame = cmds.playbackOptions(q=True, maxTime=True)
        rounded_current_frame = math.ceil(current_frame)
        rounded_end_frame = math.ceil(end_frame)
        cmds.currentTime(rounded_current_frame)
        cmds.playbackOptions(max=rounded_end_frame)

    # Animation Start End Rounding
    option_key = "animation_frame_start_rounding"
    if option_key in scene_dict:
        start_frame = cmds.playbackOptions(q=True, animationStartTime=True)
        rounded_current_frame = round(current_frame)
        rounded_start_frame = round(start_frame)
        cmds.currentTime(rounded_current_frame)
        cmds.playbackOptions(animationStartTime=rounded_start_frame)
    option_key = "playback_frame_end_rounding"
    if option_key in scene_dict:
        end_frame = cmds.playbackOptions(q=True, animationEndTime=True)
        rounded_current_frame = round(current_frame)
        rounded_end_frame = round(end_frame)
        cmds.currentTime(rounded_current_frame)
        cmds.playbackOptions(animationEndTime=rounded_end_frame)

    # Playback Start End Flooring/Ceiling
    option_key = "playback_frame_start_floor"
    if option_key in scene_dict:
        start_frame = cmds.playbackOptions(q=True, minTime=True)
        rounded_current_frame = math.floor(current_frame)
        rounded_start_frame = math.floor(start_frame)
        cmds.currentTime(rounded_current_frame)
        cmds.playbackOptions(min=rounded_start_frame)
    option_key = "playback_frame_end_ceil"
    if option_key in scene_dict:
        end_frame = cmds.playbackOptions(q=True, maxTime=True)
        rounded_current_frame = math.ceil(current_frame)
        rounded_end_frame = math.ceil(end_frame)
        cmds.currentTime(rounded_current_frame)
        cmds.playbackOptions(max=rounded_end_frame)

    # Animation Start End Flooring/Ceiling
    option_key = "animation_frame_start_floor"
    if option_key in scene_dict:
        start_frame = cmds.playbackOptions(q=True, animationStartTime=True)
        rounded_current_frame = math.floor(current_frame)
        rounded_start_frame = math.floor(start_frame)
        cmds.currentTime(rounded_current_frame)
        cmds.playbackOptions(animationStartTime=rounded_start_frame)
    option_key = "animation_frame_end_ceil"
    if option_key in scene_dict:
        end_frame = cmds.playbackOptions(q=True, animationEndTime=True)
        rounded_current_frame = math.ceil(current_frame)
        rounded_end_frame = math.ceil(end_frame)
        cmds.currentTime(rounded_current_frame)
        cmds.playbackOptions(animationEndTime=rounded_end_frame)

    # Current Time
    option_key = "current_time"
    if option_key in scene_dict:
        cmds.currentTime(scene_dict.get(option_key))

    # Use Default Material
    option_key = "use_default_material"
    if option_key in scene_dict:
        _panel = None
        try:  # Get the active model panel
            _panel = cmds.getPanel(withFocus=True)
            if not cmds.getPanel(typeOf=_panel) == "modelPanel":
                # Try to find a visible model panel if focus is not on one
                for p in cmds.getPanel(type="modelPanel"):
                    if cmds.modelEditor(p, query=True, visible=True):
                        _panel = p
                        break
                else:
                    logger.debug("No active model panel found.")
            if _panel:
                cmds.modelEditor(_panel, edit=True, useDefaultMaterial=scene_dict.get(option_key))
        except Exception as e:
            logger.debug(f"Unable to find a model panel. Issue: {e}")

    # Grid Settings
    grid_size_key = "grid_size"
    grid_spacing_key = "grid_spacing"
    grid_divisions_key = "grid_divisions"
    grid_keys = [grid_size_key, grid_spacing_key, grid_divisions_key]
    if any(key in scene_dict for key in grid_keys):
        import gt.core.display as core_display

        # Grid Size
        if grid_size_key in scene_dict:
            core_display.set_grid_divisions(
                grid_size=scene_dict.get(grid_size_key) or None, grid_spacing=None, grid_divisions=None
            )
        # Grid Spacing
        if grid_spacing_key in scene_dict:
            core_display.set_grid_divisions(
                grid_size=None, grid_spacing=scene_dict.get(grid_spacing_key) or None, grid_divisions=None
            )
        # Grid Divisions
        if grid_divisions_key in scene_dict:
            core_display.set_grid_divisions(
                grid_size=None, grid_spacing=None, grid_divisions=scene_dict.get(grid_divisions_key) or None
            )


# ----------------------------------------- Scene file information -----------------------------------------
SCENE_INFO_FPS = "fps"
SCENE_INFO_LINEAR_UNIT = "linear_unit"
SCENE_INFO_UP_AXIS = "up_axis"
SCENE_INFO_TIME_RANGE = "time_range"
LINEAR_UNIT_ALIASES = {
    "mm": "mm",
    "millimeter": "mm",
    "cm": "cm",
    "centimeter": "cm",
    "m": "m",
    "meter": "m",
    "km": "km",
    "kilometer": "km",
    "in": "in",
    "inch": "in",
    "ft": "ft",
    "foot": "ft",
    "yd": "yd",
    "yard": "yd",
    "mi": "mi",
    "mile": "mi",
}
CENTIMETERS_PER_LINEAR_UNIT = {
    "mm": 0.1,
    "cm": 1.0,
    "m": 100.0,
    "km": 100000.0,
    "in": 2.54,
    "ft": 30.48,
    "yd": 91.44,
    "mi": 160934.4,
}
TIME_UNIT_FPS = {
    "game": 15.0,
    "film": 24.0,
    "pal": 25.0,
    "ntsc": 30.0,
    "show": 48.0,
    "palf": 50.0,
    "ntscf": 60.0,
    "millisec": 1000.0,
    "sec": 1.0,
    "23.976fps": 23.976,
    "29.97fps": 29.97,
    "29.97df": 29.97,
    "47.952fps": 47.952,
    "59.94fps": 59.94,
}
SCENE_FILE_HEAD_SIZE = 2 * 1024 * 1024
SCENE_FILE_TAIL_SIZE = 8 * 1024 * 1024
MAYA_CURRENT_UNIT_PATTERN = re.compile(rb"currentUnit((?:\s+-[A-Za-z]+\s+\"?[A-Za-z0-9.]+\"?)+)")
MAYA_FLAG_PATTERN = re.compile(rb"-(?P<flag>[A-Za-z]+)\s+\"?(?P<value>[A-Za-z0-9.]+)\"?")
MAYA_Z_UP_PATTERNS = (b'upAxis -ax \\"z\\"', b'upAxis -ax "z"')
# Maya binary (IFF) headers store units as tagged chunks, e.g. b"TUNI" + size bytes + b"ntsc\x00".
MAYA_BINARY_TIME_PATTERN = re.compile(
    rb"TUNI.{4,16}?(?P<value>[0-9.]+fps|[0-9.]+df|film|ntscf|ntsc|palf|pal|game|show)\x00", re.S
)
MAYA_BINARY_LINEAR_PATTERN = re.compile(rb"LUNI.{4,16}?(?P<value>mm|cm|km|m|in|ft|yd|mi)\x00", re.S)


def normalize_linear_unit(unit_name):
    """Converts a Maya or file linear unit name to its short form.

    Args:
        unit_name (str): Unit such as "centimeter" or "cm".

    Returns:
        str: Short unit ("cm", "m", ...), or an empty string when unknown.
    """
    return LINEAR_UNIT_ALIASES.get(str(unit_name or "").strip().lower(), "")


def get_closest_linear_unit(centimeters_per_unit, tolerance=0.01):
    """Finds the Maya linear unit matching a size in centimeters per unit.

    Args:
        centimeters_per_unit (float): Size of one unit in centimeters (e.g. 100 for meters).
        tolerance (float, optional): Relative tolerance for a match.

    Returns:
        str: Short unit name, or an empty string when nothing matches.
    """
    try:
        centimeters_per_unit = float(centimeters_per_unit)
    except (TypeError, ValueError):
        return ""
    if centimeters_per_unit <= 0:
        return ""
    for unit_name, unit_size in CENTIMETERS_PER_LINEAR_UNIT.items():
        if abs(unit_size - centimeters_per_unit) <= unit_size * tolerance:
            return unit_name
    return ""


def get_fps_from_time_unit(time_unit):
    """Converts a Maya time unit name to frames per second.

    Args:
        time_unit (str): Maya time unit such as "film", "ntsc" or "120fps".

    Returns:
        float: Frames per second, or 0.0 when unknown.
    """
    time_unit = str(time_unit or "").strip().lower()
    if time_unit in TIME_UNIT_FPS:
        return TIME_UNIT_FPS[time_unit]
    if time_unit.endswith("fps"):
        try:
            return float(time_unit[:-3])
        except ValueError:
            return 0.0
    return 0.0


def normalize_up_axis(up_axis):
    """Normalizes an up axis value.

    Args:
        up_axis (str): Axis name in any case.

    Returns:
        str: "y" or "z", or an empty string when unknown.
    """
    up_axis = str(up_axis or "").strip().lower()
    return up_axis if up_axis in ("y", "z") else ""


def parse_maya_current_unit(data):
    """Parses the first currentUnit command of Maya ASCII data.

    Args:
        data (bytes): Maya ASCII bytes.

    Returns:
        dict: SCENE_INFO_FPS and SCENE_INFO_LINEAR_UNIT when found.
    """
    match = MAYA_CURRENT_UNIT_PATTERN.search(data or b"")
    if not match:
        return {}
    file_info = {}
    for flag_match in MAYA_FLAG_PATTERN.finditer(match.group(1)):
        flag = flag_match.group("flag").decode("ascii", "ignore")
        value = flag_match.group("value").decode("ascii", "ignore")
        if flag in ("t", "time") and get_fps_from_time_unit(value):
            file_info[SCENE_INFO_FPS] = get_fps_from_time_unit(value)
        elif flag in ("l", "linear") and normalize_linear_unit(value):
            file_info[SCENE_INFO_LINEAR_UNIT] = normalize_linear_unit(value)
    return file_info


def parse_maya_binary_units(data):
    """Parses the time and linear unit tags of Maya binary data.

    Args:
        data (bytes): Maya binary header bytes.

    Returns:
        dict: SCENE_INFO_FPS and SCENE_INFO_LINEAR_UNIT when found.
    """
    file_info = {}
    time_match = MAYA_BINARY_TIME_PATTERN.search(data or b"")
    if time_match:
        fps = get_fps_from_time_unit(time_match.group("value").decode("ascii", "ignore"))
        if fps:
            file_info[SCENE_INFO_FPS] = fps
    linear_match = MAYA_BINARY_LINEAR_PATTERN.search(data or b"")
    if linear_match:
        linear_unit = normalize_linear_unit(linear_match.group("value").decode("ascii", "ignore"))
        if linear_unit:
            file_info[SCENE_INFO_LINEAR_UNIT] = linear_unit
    return file_info


def read_scene_file_info(file_path):
    """Reads frame rate, linear unit, up axis and playback range from a .ma or .mb file without opening it.

    Args:
        file_path (str): Maya scene path.

    Returns:
        dict: Known SCENE_INFO_* values. Empty when the file cannot be read.
    """
    import gt.core.timeline as core_timeline

    try:
        file_size = os.path.getsize(file_path)
        with open(file_path, "rb") as scene_file:
            head_bytes = scene_file.read(SCENE_FILE_HEAD_SIZE)
            tail_bytes = b""
            if file_size > SCENE_FILE_HEAD_SIZE:
                scene_file.seek(max(SCENE_FILE_HEAD_SIZE, file_size - SCENE_FILE_TAIL_SIZE))
                tail_bytes = scene_file.read()
    except (IOError, OSError) as exception:
        logger.debug(f'Unable to read "{file_path}". Issue: {exception}')
        return {}
    if file_path.lower().endswith(".mb"):
        file_info = parse_maya_binary_units(head_bytes)
    else:
        file_info = parse_maya_current_unit(head_bytes)
    scanned_bytes = head_bytes + tail_bytes
    file_info[SCENE_INFO_UP_AXIS] = "z" if any(pattern in scanned_bytes for pattern in MAYA_Z_UP_PATTERNS) else "y"
    playback_range = core_timeline.read_stored_playback_range(file_path)
    if playback_range:
        file_info[SCENE_INFO_TIME_RANGE] = playback_range
    return file_info


def load_file_into_scene(
    file_path, file_type=None, namespace="", reference=False, execute_script_nodes=True, extra_kwargs=None
):
    """Imports or references a file with Maya's file command and reports what it created.

    Note: Maya's file import flushes the undo queue, so it cannot be undone.

    Args:
        file_path (str): File to load.
        file_type (str, optional): Maya translator name, e.g. "FBX". Maya detects it when omitted.
        namespace (str, optional): Namespace for new nodes.
        reference (bool, optional): Reference instead of import.
        execute_script_nodes (bool, optional): Allow script nodes stored in the file to run (imports only).
        extra_kwargs (dict, optional): Extra flags passed to cmds.file.

    Returns:
        tuple: (new_nodes, reference_node). new_nodes are long names; reference_node is empty for imports.
    """
    import gt.core.uuid as core_uuid

    node_ids_before = core_uuid.capture_scene_uuids()
    references_before = set(cmds.ls(type="reference") or [])
    file_kwargs = {"ignoreVersion": True, "returnNewNodes": True}
    if reference:
        file_kwargs.update({"reference": True, "mergeNamespacesOnClash": False})
    else:
        file_kwargs.update({"i": True, "executeScriptNodes": bool(execute_script_nodes)})
    if file_type:
        file_kwargs["type"] = file_type
    if namespace:
        file_kwargs["namespace"] = namespace
    file_kwargs.update(extra_kwargs or {})
    returned_nodes = cmds.file(file_path, **file_kwargs) or []
    new_nodes = core_uuid.get_nodes_created_since(node_ids_before)
    for node in cmds.ls(returned_nodes, long=True) or []:
        if node not in new_nodes:
            new_nodes.append(node)
    reference_node = ""
    if reference:
        for candidate_node in sorted(set(cmds.ls(type="reference") or []) - references_before):
            if candidate_node.endswith("sharedReferenceNode"):
                continue
            try:
                cmds.referenceQuery(candidate_node, filename=True)
            except RuntimeError:
                continue
            reference_node = candidate_node
            break
    return new_nodes, reference_node


def create_new_scene(prompt_save=True):
    """Starts a new scene, offering to save unsaved changes first.

    Untitled scenes open a "Save Scene As" dialog when the user chooses Save.

    Args:
        prompt_save (bool, optional): Ask about unsaved changes. When False, changes are discarded.

    Returns:
        bool: True when a new scene was created, False when the user cancelled.
    """
    if prompt_save and cmds.file(query=True, modified=True):
        user_choice = cmds.confirmDialog(
            title="Unsaved Changes",
            message="The current scene has unsaved changes. Save them before starting a new scene?",
            button=["Save", "Don't Save", "Cancel"],
            defaultButton="Save",
            cancelButton="Cancel",
            dismissString="Cancel",
            icon="warning",
        )
        if user_choice == "Cancel":
            return False
        if user_choice == "Save" and not save_current_scene():
            return False
    cmds.file(new=True, force=True)
    return True


def save_current_scene():
    """Saves the current scene, asking for a path when it has never been saved.

    Returns:
        bool: True when the scene was saved, False when the user cancelled the dialog.
    """
    scene_path = cmds.file(query=True, sceneName=True)
    if scene_path:
        cmds.file(save=True)
        return True
    picked_paths = cmds.fileDialog2(
        caption="Save Scene As",
        fileMode=0,
        fileFilter="Maya ASCII (*.ma);;Maya Binary (*.mb)",
        dialogStyle=2,
    )
    if not picked_paths:
        return False
    scene_path = picked_paths[0]
    file_type = "mayaBinary" if scene_path.lower().endswith(".mb") else "mayaAscii"
    cmds.file(rename=scene_path)
    cmds.file(save=True, type=file_type)
    return True


if __name__ == "__main__":
    from pprint import pprint

    # set_frame_rate("2fps")
    out = None
    # out = get_distance_in_meters()
    set_scene_from_dict({"use_default_material": False})
    pprint(out)
