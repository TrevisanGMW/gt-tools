"""Sets Maya's current timeline frame to a configurable value."""

import maya.cmds as cmds


CURRENT_FRAME = 1

cmds.currentTime(CURRENT_FRAME, edit=True)
