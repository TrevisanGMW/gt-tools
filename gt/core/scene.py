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

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MAX_FRAME_RATE = 48000


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


def force_reload_file():
    """Reopens the opened file (to revert any changes done to the file)"""
    if cmds.file(query=True, exists=True):  # Check to see if it was ever saved
        file_path = cmds.file(query=True, expandName=True)
        if file_path is not None:
            cmds.file(file_path, open=True, force=True)
    else:
        cmds.warning("Unable to force reload. File was never saved.")


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


if __name__ == "__main__":
    from pprint import pprint

    # set_frame_rate("2fps")
    out = None
    # out = get_distance_in_meters()
    set_scene_from_dict({"use_default_material": False})
    pprint(out)
