"""
 GT Orient Joints - Script for orienting multiple joints in a more predictable way
 github.com/TrevisanGMW/gt-tools - 2023-01-19

 0.0.1 - 2023-01-19
 Initial GUI

"""
import maya.cmds as cmds
import traceback
import logging
import random
import copy
from maya import OpenMayaUI as OpenMayaUI

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_orient_joints")
logger.setLevel(logging.INFO)

# Script Name:
script_name = "GT Orient Joints"

# Version:
script_version = "0.0.1"


# Renamer UI ============================================================================
def build_gui_orient_joints():
    """ Builds the UI for GT Renamer """
    window_name = "build_gui_orient_joints"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

        # ===================================================================================

    window_gui_renamer = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                     titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout()

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main)
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_orient_joints())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.rowColumnLayout(nc=2, cw=[(1, 100), (2, 130)], cs=[(1, 45)])
    selection_type_rc = cmds.radioCollection()
    selection_type_selected = cmds.radioButton(label='Selected', select=True)
    selection_type_hierarchy = cmds.radioButton(label='Hierarchy')

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=5, style='none')  # Empty Space

    # Prefix and Suffix ================
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 0)], p=body_column)
    cmds.separator(h=10)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Prefix and Suffix')
    cmds.separator(h=7, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=4, cw=[(1, 50), (2, 50), (3, 50), (4, 85)], cs=[(1, 0), (2, 0), (3, 0), (4, 10)],
                         p=body_column)
    cmds.text('Aim Axis:')
    cmds.radioCollection()
    cmds.radioButton(label='X', select=True)
    cmds.radioButton(label='Y')
    cmds.radioButton(label='Z')

    cmds.text('Up Axis:')
    cmds.radioCollection()
    cmds.radioButton(label='X', select=True)
    cmds.radioButton(label='Y')
    cmds.radioButton(label='Z')

    cmds.text('World Up:')
    cmds.radioCollection()
    cmds.radioButton(label='X', select=True)
    cmds.radioButton(label='Y')
    cmds.radioButton(label='Z')

    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1, 10)], p=body_column)
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.button(l="Orient Joints", bgc=(.6, .6, .6), c=lambda x: start_renaming('search_and_replace'))
    cmds.separator(h=15, style='none')  # Empty Space

    # Show and Lock Window
    cmds.showWindow(window_gui_renamer)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/orientJoint.png')
    widget.setWindowIcon(icon)


def build_gui_help_orient_joints():
    """ Creates the Help GUI for GT Renamer """
    window_name = "build_gui_help_orient_joints"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    main_column = cmds.columnLayout(p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)  # Title Column
    cmds.text(script_name + " Help", bgc=[.4, .4, .4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column)  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
    cmds.text(l='Script for orienting joints.', align="center")
    cmds.separator(h=15, style='none')  # Empty Space

    cmds.text(l='Modes:', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='- Selected: uses selected objects when orienting.', align="left", font='smallPlainLabelFont')
    cmds.text(l='- Hierarchy: uses hierarchy when orienting.', align="left", font='smallPlainLabelFont')

    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='TBD', align="left", font='smallPlainLabelFont')
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p=main_column)
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p=main_column)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style='none')  # Empty Space

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)

    cmds.separator(h=10, style='none')
    cmds.separator(h=5, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')

    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)

    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


def orient_joints_inview_feedback(affected_num):
    """
    Prints an inViewMessage to give feedback to the user about how many objects were affected.
    Uses the module "random" to force identical messages to appear at the same time.

    Args:
        affected_num (int): how many objects were renamed.
    """
    if affected_num != 0:
        message = '<' + str(random.random()) + '><span style=\"color:#FF0000;text-decoration:underline;\">' + str(
            affected_num)

        if affected_num == 1:
            message += '</span><span style=\"color:#FFFFFF;\"> joint was affected.</span>'
        else:
            message += '</span><span style=\"color:#FFFFFF;\"> joints were affected.</span>'
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)


if __name__ == '__main__':
    build_gui_orient_joints()
    # logger.setLevel(logging.DEBUG)
    # logger.debug('Logging Set to DEBUG MODE')
    # sel = cmds.ls(selection=True)
    # rename_and_letter(sel, 'newName_', is_uppercase=True, keep_name=False)
