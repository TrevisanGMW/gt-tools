# Enables Viewport 2.0 anti-aliasing in the merged scene.
# These values live on the hardwareRenderingGlobals node, so they are saved with the scene
# and apply when it is opened in Maya.
import sys
import maya.cmds as cmds

MULTI_SAMPLE_COUNT = 16  # 8 or 16 are common review values.
SMOOTH_WIREFRAME = True

cmds.setAttr("hardwareRenderingGlobals.multiSampleEnable", 1)
cmds.setAttr("hardwareRenderingGlobals.multiSampleCount", MULTI_SAMPLE_COUNT)
if SMOOTH_WIREFRAME:
    cmds.setAttr("hardwareRenderingGlobals.lineAAEnable", 1)
sys.stdout.write(f"Anti-aliasing enabled ({MULTI_SAMPLE_COUNT} samples).\n")
