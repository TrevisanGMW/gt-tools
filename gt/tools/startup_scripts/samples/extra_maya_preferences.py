"""Applies extra Maya preferences and defaults.

Set each ``SET_*`` switch to True to apply its paired value. Every preference
change is disabled by default.
"""

import maya.cmds as cmds


# Home screen
SET_HOMESCREEN_ON_STARTUP_STATE = False
HOMESCREEN_ON_STARTUP_STATE = False

# Home menu bar icon
SET_HOME_MENU_BAR_ICON_STATE = False
HOME_MENU_BAR_ICON_STATE = False

# ViewCube
SET_VIEW_CUBE_STATE = False
VIEW_CUBE_STATE = False

# Cached playback
SET_CACHED_PLAYBACK_STATE = False
CACHED_PLAYBACK_STATE = False

# Playback speed
SET_PLAYBACK_SPEED = False
PLAYBACK_SPEED = 1.0

# Perspective camera clipping
SET_PERSP_NEAR_CLIP_PLANE = False
PERSP_NEAR_CLIP_PLANE = 1.0

# Transform tool settings
RESET_MOVE_TOOL_SETTINGS = False
RESET_ROTATE_TOOL_SETTINGS = False
RESET_SCALE_TOOL_SETTINGS = False


IS_INTERACTIVE_MAYA = not cmds.about(batch=True)


if SET_HOMESCREEN_ON_STARTUP_STATE:
    cmds.optionVar(intValue=("showHomeScreenOnStartup", int(HOMESCREEN_ON_STARTUP_STATE)))

if SET_HOME_MENU_BAR_ICON_STATE:
    cmds.optionVar(intValue=("showHomeMenubarIcon", int(HOME_MENU_BAR_ICON_STATE)))
    if IS_INTERACTIVE_MAYA:
        cmds.appHome(iconVisible=HOME_MENU_BAR_ICON_STATE)

if SET_VIEW_CUBE_STATE:
    cmds.optionVar(intValue=("viewCubeShowCube", int(VIEW_CUBE_STATE)))
    if IS_INTERACTIVE_MAYA:
        cmds.viewManip(visible=VIEW_CUBE_STATE)

if SET_CACHED_PLAYBACK_STATE:
    from maya.plugin.evaluator.cache_preferences import CachePreferenceEnabled

    cached_playback_preference = CachePreferenceEnabled()
    cached_playback_preference.set_value(CACHED_PLAYBACK_STATE)
    cached_playback_preference.set_state_from_preference()

if SET_PLAYBACK_SPEED:
    cmds.optionVar(floatValue=("timeSliderPlaySpeed", PLAYBACK_SPEED))
    cmds.playbackOptions(playbackSpeed=PLAYBACK_SPEED)

if SET_PERSP_NEAR_CLIP_PLANE and cmds.objExists("perspShape"):
    cmds.setAttr("perspShape.nearClipPlane", PERSP_NEAR_CLIP_PLANE)

if RESET_MOVE_TOOL_SETTINGS:
    cmds.resetTool("Move")

if RESET_ROTATE_TOOL_SETTINGS:
    cmds.resetTool("Rotate")

if RESET_SCALE_TOOL_SETTINGS:
    cmds.resetTool("Scale")
