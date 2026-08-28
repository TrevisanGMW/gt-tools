"""Sets 30fps timing, a 0-120 frame range, grid defaults, Y-up, undo, and anti-aliasing."""

import maya.cmds as cmds


# Editable scene defaults
FRAME_RATE = "ntsc"  # Maya's 30fps time unit.
TIMELINE_START_FRAME = 0
TIMELINE_END_FRAME = 120

GRID_VISIBLE = True
GRID_LENGTH_AND_WIDTH = 12
GRID_LINES_EVERY = 5
GRID_SUBDIVISIONS = 5

UP_AXIS = "y"
ROTATE_VIEW_FOR_UP_AXIS_CHANGE = True

ENABLE_UNDO_QUEUE = True

ANTI_ALIASING_SAMPLE_COUNT = 16


# Scene timing
cmds.currentUnit(time=FRAME_RATE)
cmds.playbackOptions(
    minTime=TIMELINE_START_FRAME,
    maxTime=TIMELINE_END_FRAME,
    animationStartTime=TIMELINE_START_FRAME,
    animationEndTime=TIMELINE_END_FRAME,
)

# Viewport grid defaults
cmds.grid(
    toggle=GRID_VISIBLE,
    size=GRID_LENGTH_AND_WIDTH,
    spacing=GRID_LINES_EVERY,
    divisions=GRID_SUBDIVISIONS,
)

# Scene orientation
if cmds.upAxis(query=True, axis=True).lower() != UP_AXIS.lower():
    cmds.upAxis(axis=UP_AXIS, rotateView=ROTATE_VIEW_FOR_UP_AXIS_CHANGE)

# Enable the undo queue when it is disabled without changing its configured size.
if ENABLE_UNDO_QUEUE:
    if not cmds.undoInfo(query=True, state=True):
        cmds.undoInfo(state=True)

# Viewport anti-aliasing
cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", ANTI_ALIASING_SAMPLE_COUNT)
