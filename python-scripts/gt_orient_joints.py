"""
 GT Orient Joints - Script for orienting multiple joints in a more predictable way
 github.com/TrevisanGMW/gt-tools - 2023-01-19

 0.0.1 - 2023-01-19
 Initial GUI

"""

import maya.cmds as cmds
import maya.api.OpenMaya as om
import logging
import random
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
script_version = "0.0.2"


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
    cmds.text('Orientation Settings:')
    cmds.separator(h=7, style='none')  # Empty Space

    rb_axis_width = 45
    cmds.rowColumnLayout(nc=5, cw=[(1, 75), (2, rb_axis_width), (3, rb_axis_width), (4, rb_axis_width)],
                         cs=[(1, 0), (2, 0), (3, 0), (4, 0)],
                         p=body_column)
    cmds.text('Aim Axis:')
    cmds.radioCollection()
    cmds.radioButton(label='X', select=True)
    cmds.radioButton(label='Y')
    cmds.radioButton(label='Z')
    option_menu_aim = cmds.optionMenu(label='')
    cmds.menuItem(label='+')
    cmds.menuItem(label='-')

    cmds.text('Up Axis:')
    cmds.radioCollection()
    cmds.radioButton(label='X', select=True)
    cmds.radioButton(label='Y')
    cmds.radioButton(label='Z')
    option_menu_up = cmds.optionMenu(label='')
    cmds.menuItem(label='+')
    cmds.menuItem(label='-')

    cmds.text('World Up:')
    cmds.radioCollection()
    cmds.radioButton(label='X', select=True)
    cmds.radioButton(label='Y')
    cmds.radioButton(label='Z')
    option_menu_aim = cmds.optionMenu(label='')
    cmds.menuItem(label='+')
    cmds.menuItem(label='-')

    cmds.rowColumnLayout(nc=1, cw=[(1, 240)], cs=[(1, 10)], p=body_column)
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.button(l="Orient Joints", bgc=(.6, .6, .6), c=lambda x: validate_and_run())
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


def orient_joint(joint_list,
                 aim_axis=(1, 0, 0),
                 up_axis=(1, 0, 0),
                 up_dir=(1, 0, 0),
                 detect_up_dir=False):
    """
    Orient Joint list in a more predictable way (when compared to Maya)
    Args:
        joint_list (list): A list of joints (strings) - Name of the joints
        aim_axis (optional, tuple): Aim axis
        up_axis (optional, tuple):
        up_dir (optional, tuple):
        detect_up_dir (optional, bool): If it should attempt to auto-detect up direction
    """
    starting_up = om.MVector((0, 0, 0))
    index = 0
    for jnt in joint_list:

        # Store Parent
        parent = cmds.listRelatives(jnt, parent=True) or []
        if len(parent) != 0:
            parent = parent[0]

        # Un-parent children
        children = cmds.listRelatives(jnt, children=True, typ="transform") or []
        children += cmds.listRelatives(jnt, children=True, typ="joint") or []
        if len(children) > 0:
            children = cmds.parent(children, w=True)

        # Determine aim joint (if available)
        aim_target = ""
        for child in children:
            if cmds.nodeType(child) == "joint":
                aim_target = child

        if aim_target != "":
            up_vec = (0, 0, 0)

            if detect_up_dir:
                pos_jnt_ws = cmds.xform(jnt, q=True, ws=True, rp=True)

                # Use itself in case it doesn't have a parent
                pos_parent_ws = pos_jnt_ws
                if parent != "":
                    pos_parent_ws = cmds.xform(parent, q=True, ws=True, rp=True)

                tolerance = 0.0001
                if parent == "" or (abs(pos_jnt_ws[0] - pos_parent_ws[0]) <= tolerance and
                                    abs(pos_jnt_ws[1] - pos_parent_ws[1]) <= tolerance and
                                    abs(pos_jnt_ws[2] - pos_parent_ws[2]) <= tolerance):
                    aim_children = cmds.listRelatives(aim_target, children=True) or []
                    aim_child = ""

                    for child in aim_children:
                        if cmds.nodeType(child) == "joint":
                            aim_child = child

                    up_vec = get_cross_direction(jnt, aim_target, aim_child)
                else:
                    print("parent", parent)
                    print("jnt", jnt)
                    print("aim_target", aim_target)
                    up_vec = get_cross_direction(parent, jnt, aim_target)

            if not detect_up_dir or (up_vec[0] == 0.0 and
                                     up_vec[1] == 0.0 and
                                     up_vec[2] == 0.0):
                up_vec = up_dir

            cmds.delete(cmds.aimConstraint(aim_target, jnt,
                                           aim=aim_axis,
                                           upVector=up_axis,
                                           worldUpVector=up_vec,
                                           worldUpType="vector"))

            current_up = om.MVector(up_vec).normal()
            dot = get_dot_product(current_up, starting_up)
            starting_up = om.MVector(up_vec).normal()

            # Flip in case dot is negative (wrong way)
            if index > 0 and dot <= 0.0:
                cmds.xform(jnt, r=True, os=True, ra=(aim_axis[0] * 180.0, aim_axis[1] * 180.0, aim_axis[2] * 180.0))
                starting_up *= -1.0

            cmds.joint(jnt, e=True, zeroScaleOrient=True)
            cmds.makeIdentity(jnt, apply=True)
        elif parent != "":
            cmds.delete(cmds.orientConstraint(parent, jnt, weight=1))
            cmds.joint(jnt, e=True, zeroScaleOrient=True)
            cmds.makeIdentity(jnt, apply=True)

        if len(children) > 0:
            cmds.parent(children, jnt)
        index += 1


def copy_parent_orients(joint_list):
    """
    Copy the orientations from its world (parent)
    Args:
        joint_list (list, string): A list of joints to receive the orientation of their parents.
                                   If a string is given instead, it will be auto converted into a list for processing.
    """
    if isinstance(joint_list, str):
        joint_list = [joint_list]
    for jnt in joint_list:
        cmds.joint(jnt, e=True, orientJoint="none", zeroScaleOrient=True)


def get_dot_product(vector_a, vector_b):
    """
    Returns dot product
        Args:
            vector_a (list, MVector): first vector
            vector_b (list, MVector): second vector
    """
    if type(vector_a) != 'OpenMaya.MVector':
        vector_a = om.MVector(vector_a)
    if type(vector_b) != 'OpenMaya.MVector':
        vector_b = om.MVector(vector_b)
    return vector_a * vector_b


def get_cross_product(vector_a, vector_b, vector_c):
    """
    Get Cross Product
        Args:
            vector_a (list): A list of floats
            vector_b (list): A list of floats
            vector_c (list): A list of floats
        Returns:
            MVector: cross product
    """
    if type(vector_a) != 'OpenMaya.MVector':
        vector_a = om.MVector(vector_a)
    if type(vector_b) != 'OpenMaya.MVector':
        vector_b = om.MVector(vector_b)
    if type(vector_c) != 'OpenMaya.MVector':
        vector_c = om.MVector(vector_c)

    vector_a = om.MVector([vector_a[0]-vector_b[0],
                           vector_a[1]-vector_b[1],
                           vector_a[2]-vector_b[2]])

    vector_b = om.MVector([vector_c[0]-vector_b[0],
                           vector_c[1]-vector_b[1],
                           vector_c[2]-vector_b[2]])

    return vector_a ^ vector_b


def get_cross_direction(obj_a, obj_b, obj_c):
    """
    Get Cross Direction
        Args:
            obj_a (string): Name of the first object. (Must exist in scene)
            obj_b (string): Name of the second object. (Must exist in scene)
            obj_c (string): Name of the third object. (Must exist in scene)
        Returns:
            MVector: cross direction of the objects
    """
    cross = [0, 0, 0]
    for obj in [obj_a, obj_b, obj_c]:
        if not cmds.objExists(obj):
            return cross
    pos_a = cmds.xform(obj_a, q=True, ws=True, rp=True)
    pos_b = cmds.xform(obj_b, q=True, ws=True, rp=True)
    pos_c = cmds.xform(obj_c, q=True, ws=True, rp=True)

    return get_cross_product(pos_a, pos_b, pos_c).normal()


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    build_gui_orient_joints()
