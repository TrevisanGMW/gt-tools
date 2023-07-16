"""
 GT Make IK Stretchy - Solution for making simple IK systems stretchy.
 github.com/TrevisanGMW/gt-tools -  2020-03-13

 1.1 - 2020-06-07
 Fixed random window widthHeight issue.
 Updated naming convention to make it clearer. (PEP8)
 
 1.2 - 2020-06-17
 Added window icon
 Added help menu
 Changed GUI
 
 1.3 - 2020-11-15
 Tweaked the color and text for the title and help menu
 
 1.4 - 2020-12-29
 Recreate a big portion of the main function
 Changed script name from "Make Stretchy Legs" to "Make IK Stretchy"
 Added load ik handle button
 Added load attribute holder button
 Added stretchy name system
 Created functions to validate objects
 Created functions to update GUI
 Updated help
 
 1.5 - 2021-01-03
 Updated stretchy system to avoid cycles and errors
 Removed incorrect Help GUI call line from standalone version
 Updated the help info to match changes
 Added option to return the joint under the ikHandle
 Updated stretchy system to account for any curvature
 
 1.5.1 - 2021-01-04
 Changed stretchy system, so it doesn't use a floatConstant node
 
 1.5.2- 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.5.3
 Added patch to version
 Added logger
 PEP8 Cleanup
 
"""
import math

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

from maya import OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import random
import sys

# Script Name
script_name = "GT - Make IK Stretchy"

# Version:
script_version = "1.5.3"

# Settings
gt_make_ik_stretchy_settings = {'ik_handle': '',
                                'attr_holder': ''
                                }


# Main Form ============================================================================
def build_gui_make_ik_stretchy():
    window_name = "build_gui_make_ik_stretchy"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

        # Main GUI Start Here =================================================================================

    # Build UI
    window_gui_make_ik_stretchy = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                              titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_make_stretchy_ik())
    cmds.separator(h=5, style='none')  # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    cmds.text(l='This script makes an IK setup stretchy.', align="center", fn='boldLabelFont')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='Load an ikHandle and click on "Make Stretchy"', align="center")
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='To use this script to its full potential, provide\n an object to be the attribute holder.\n'
                '(Usually the control driving the ikHandle)\n\nBy default the attribute holder determines the\n '
                'stretch, to change this behavior, constraint\n "stretchyTerm_end" to another object.', align="center")
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text('Stretchy System Prefix:')
    stretchy_system_prefix = cmds.textField(text='', pht='Stretchy System Prefix (Optional)')

    cmds.separator(h=10, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 129), (2, 130)], cs=[(1, 0)])
    cmds.button(l="Load IK Handle", c=lambda x: object_load_handler("ik_handle"), w=130)
    ik_handle_status = cmds.button(l="Not loaded yet", bgc=(.2, .2, .2), w=130,
                                   c=lambda x: select_existing_object(gt_make_ik_stretchy_settings.get('ik_handle')))

    cmds.rowColumnLayout(nc=2, cw=[(1, 129), (2, 130)], cs=[(1, 0)], p=body_column)
    cmds.button(l="Load Attribute Holder", c=lambda x: object_load_handler("attr_holder"), w=130)
    attr_holder_status = cmds.button(l="Not loaded yet", bgc=(.2, .2, .2), w=130,
                                     c=lambda x: select_existing_object(
                                         gt_make_ik_stretchy_settings.get('attr_holder')))

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    cmds.separator(h=7, style='none')  # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=7, style='none')  # Empty Space

    cmds.button(l="Make Stretchy", bgc=(.6, .6, .6), c=lambda x: validate_operation())
    cmds.separator(h=10, style='none')  # Empty Space

    # Show and Lock Window
    cmds.showWindow(window_gui_make_ik_stretchy)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/ikSCsolver.svg')
    widget.setWindowIcon(icon)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_name)

    # Main GUI Ends Here =================================================================================

    def object_load_handler(operation):
        """
        Function to handle load buttons. It updates the UI to reflect the loaded data.
        
        Args:
            operation (str): String to determine function (Currently either "ik_handle" or "attr_holder")
        
        """

        # Check If Selection is Valid
        received_valid_element = False

        # ikHandle
        if operation == 'ik_handle':
            current_selection = cmds.ls(selection=True, type='ikHandle')

            if len(current_selection) == 0:
                cmds.warning("Nothing selected. Please select an ikHandle and try again.")
            elif len(current_selection) > 1:
                cmds.warning("You selected more than one ikHandle! Please select only one")
            elif cmds.objectType(current_selection[0]) == "ikHandle":
                gt_make_ik_stretchy_settings['ik_handle'] = current_selection[0]
                received_valid_element = True
            else:
                cmds.warning("Something went wrong, make sure you selected just one ikHandle and try again.")

            # ikHandle Update GUI
            if received_valid_element:
                cmds.button(ik_handle_status, l=gt_make_ik_stretchy_settings.get('ik_handle'), e=True, bgc=(.6, .8, .6),
                            w=130)
            else:
                cmds.button(ik_handle_status, l="Failed to Load", e=True, bgc=(1, .4, .4), w=130)

        # Attr Holder
        if operation == 'attr_holder':
            current_selection = cmds.ls(selection=True)
            if len(current_selection) == 0:
                cmds.warning("Nothing selected. Assuming you don\'t want an attribute holder. "
                             "To select an attribute holder, select only one object "
                             "(usually a control curve) and try again.")
                gt_make_ik_stretchy_settings['attr_holder'] = ''
            elif len(current_selection) > 1:
                cmds.warning("You selected more than one object! Please select only one")
            elif cmds.objExists(current_selection[0]):
                gt_make_ik_stretchy_settings['attr_holder'] = current_selection[0]
                received_valid_element = True
            else:
                cmds.warning("Something went wrong, make sure you selected just one object and try again.")

            # Attr Holder Update GUI
            if received_valid_element:
                cmds.button(attr_holder_status, l=gt_make_ik_stretchy_settings.get('attr_holder'), e=True,
                            bgc=(.6, .8, .6), w=130)
            else:
                cmds.button(attr_holder_status, l="Not provided", e=True, bgc=(.2, .2, .2), w=130)

    def validate_operation():
        """ Checks elements one last time before running the script """

        is_valid = False
        stretchy_name = None
        attr_holder = None

        stretchy_prefix = cmds.textField(stretchy_system_prefix, q=True, text=True).replace(' ', '')

        # Name
        if stretchy_prefix != '':
            stretchy_name = stretchy_prefix

        # ikHandle
        if gt_make_ik_stretchy_settings.get('ik_handle') == '':
            cmds.warning('Please load an ikHandle first before running the script.')
            is_valid = False
        else:
            if cmds.objExists(gt_make_ik_stretchy_settings.get('ik_handle')):
                is_valid = True
            else:
                cmds.warning('"' + str(gt_make_ik_stretchy_settings.get('ik_handle')) +
                             "\" couldn't be located. "
                             "Make sure you didn't rename or deleted the object after loading it")

        # Attribute Holder
        if is_valid:
            if gt_make_ik_stretchy_settings.get('attr_holder') != '':
                if cmds.objExists(gt_make_ik_stretchy_settings.get('attr_holder')):
                    attr_holder = gt_make_ik_stretchy_settings.get('attr_holder')
                else:
                    cmds.warning('"' + str(gt_make_ik_stretchy_settings.get('attr_holder')) +
                                 "\" couldn't be located. "
                                 "Make sure you didn't rename or deleted the object after loading it. "
                                 "A simpler version of the stretchy system was created.")
            else:
                sys.stdout.write(
                    'An attribute holder was not provided. A simpler version of the stretchy system was created.')

        # Run Script
        if is_valid:
            if stretchy_name:
                make_stretchy_ik(gt_make_ik_stretchy_settings.get('ik_handle'), stretchy_name=stretchy_name,
                                 attribute_holder=attr_holder)
            else:
                make_stretchy_ik(gt_make_ik_stretchy_settings.get('ik_handle'), stretchy_name='temp',
                                 attribute_holder=attr_holder)


# Creates Help GUI
def build_gui_help_make_stretchy_ik():
    """ Creates GUI for Make Stretchy IK """
    window_name = "build_gui_help_make_stretchy_ik"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    cmds.columnLayout("main_column", p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column")  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")  # Title Column
    cmds.text(script_name + " Help", bgc=[.4, .4, .4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column")  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.text(l='This script makes an IK setup stretchy.', align="center")
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='Load an ikHandle, then click on "Make Stretchy"', align="center")
    cmds.separator(h=15, style='none')  # Empty Space

    cmds.text(l='Stretchy System Prefix:', align="center")
    cmds.text(l='As the name suggests, it determined the prefix\nused when naming nodes for the stretchy system.\n'
                'If nothing is provided, it will be\n automatically named "temp".', align="center")
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='Load IK Handle:', align="center")
    cmds.text(l='Use this button to load your ikHandle.\nThe joints will be automatically extracted from it.',
              align="center")
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='Load Attribute Holder:', align="center")
    cmds.text(l='Use this button to load your attribute holder.\nThis is usually a control.\n'
                'A few custom attributes will be added to this object,\n so the user can control the stretchy system.',
              align="center")

    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Important:', align="center", fn="boldLabelFont")
    cmds.text(
        l='The ikHandle cannot be outside of a group.\n So it will be automatically grouped when this is the case.',
        align="center")
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(
        l='If an attribute holder is not provided, a simpler version\n of the stretchy system will be created instead.',
        align="center")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p="main_column")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style='none')  # Empty Space

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.separator(h=10, style='none')
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
        """ Closes Help Window """
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


def select_existing_object(obj):
    """
    Selects an object in case it exists 
    
    Args:
        obj (str): Object it will try to select

    """
    if obj != '':
        if cmds.objExists(obj):
            cmds.select(obj)
            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(
                obj) + '</span><span style=\"color:#FFFFFF;\"> selected.</span>', pos='botLeft', fade=True, alpha=.9)
        else:
            cmds.warning('"' + str(
                obj) + "\" couldn't be selected. Make sure you didn't rename or deleted the object after loading it")
    else:
        cmds.warning('Nothing loaded. Please load an object before attempting to select it.')


def change_outliner_color(obj, rgb_color=(1, 1, 1)):
    """
    Sets the outliner color for the selected object 
    
    Args:
        obj (str): Name (path) of the object to change.
        rgb_color (tuple): RGB Color to change it to
    
    """
    if cmds.objExists(obj) and cmds.getAttr(obj + '.useOutlinerColor', lock=True) is False:
        cmds.setAttr(obj + '.useOutlinerColor', 1)
        cmds.setAttr(obj + '.outlinerColorR', rgb_color[0])
        cmds.setAttr(obj + '.outlinerColorG', rgb_color[1])
        cmds.setAttr(obj + '.outlinerColorB', rgb_color[2])


def make_stretchy_ik(ik_handle, stretchy_name='temp', attribute_holder=None):
    """
    Creates two measure tools and use them to determine when the joints should be scaled up causing a stretchy effect.
    
    Args:
        ik_handle (string) : Name of the IK Handle (joints will be extracted from it)
        stretchy_name (string): Name to be used when creating system (optional, if not provided it will be "temp")
        attribute_holder (string): The name of an object. If it exists, custom attributes will be added to it.
                                   These attributes allow the user to control whether the system is active,
                                   as well as its operation.
                                   For a more complete stretchy system you have to provide a valid object in this
                                   parameter as without it volume preservation is skipped

    Returns:
        list (list): A list with the end locator one (to be attached to the IK control) the stretchy_grp
                    (system elements) and the end_ik_jnt (joint under the ikHandle)
    """

    def calculate_distance(pos_a_x, pos_a_y, pos_a_z, pos_b_x, pos_b_y, pos_b_z):
        """
        Calculates the magnitude (in this case distance) between two objects
        
        Args:
            pos_a_x (float): Position X for object A
            pos_a_y (float): Position Y for object A
            pos_a_z (float): Position Z for object A
            pos_b_x (float): Position X for object B
            pos_b_y (float): Position Y for object B
            pos_b_z (float): Position Z for object B

        Returns:
            magnitude (float): Distance between two objects
        
        """
        dx = pos_a_x - pos_b_x
        dy = pos_a_y - pos_b_y
        dz = pos_a_z - pos_b_z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def int_to_en(num):
        """
        Given an int32 number, returns an English word for it.
        
        Args:
            num (int) and integer to be converted to English words.

        Returns:
            number (string): The input number as words
        """
        d = {0: 'zero', 1: 'one', 2: 'two', 3: 'three', 4: 'four', 5: 'five',
             6: 'six', 7: 'seven', 8: 'eight', 9: 'nine', 10: 'ten',
             11: 'eleven', 12: 'twelve', 13: 'thirteen', 14: 'fourteen',
             15: 'fifteen', 16: 'sixteen', 17: 'seventeen', 18: 'eighteen',
             19: 'nineteen', 20: 'twenty',
             30: 'thirty', 40: 'forty', 50: 'fifty', 60: 'sixty',
             70: 'seventy', 80: 'eighty', 90: 'ninety'}
        k = 1000
        m = k * 1000
        b = m * 1000
        t = b * 1000

        assert (0 <= num)

        if num < 20:
            return d[num]

        if num < 100:
            if num % 10 == 0:
                return d[num]
            else:
                return d[num // 10 * 10] + '-' + d[num % 10]

        if num < k:
            if num % 100 == 0:
                return d[num // 100] + ' hundred'
            else:
                return d[num // 100] + ' hundred and ' + int_to_en(num % 100)

        if num < m:
            if num % k == 0:
                return int_to_en(num // k) + ' thousand'
            else:
                return int_to_en(num // k) + ' thousand, ' + int_to_en(num % k)

        if num < b:
            if (num % m) == 0:
                return int_to_en(num // m) + ' million'
            else:
                return int_to_en(num // m) + ' million, ' + int_to_en(num % m)

        if num < t:
            if (num % b) == 0:
                return int_to_en(num // b) + ' billion'
            else:
                return int_to_en(num // b) + ' billion, ' + int_to_en(num % b)

        if num % t == 0:
            return int_to_en(num // t) + ' trillion'
        else:
            return int_to_en(num // t) + ' trillion, ' + int_to_en(num % t)

    # ######### Start of Make Stretchy Function ##########

    ik_handle_joints = cmds.ikHandle(ik_handle, q=True, jointList=True)
    children_last_jnt = cmds.listRelatives(ik_handle_joints[-1], children=True, type='joint') or []

    # Find end joint
    end_ik_jnt = ''
    if len(children_last_jnt) == 1:
        end_ik_jnt = children_last_jnt[0]
    elif len(children_last_jnt) > 1:  # Find Joint Closest to ikHandle
        jnt_magnitude_pairs = []
        for jnt in children_last_jnt:
            ik_handle_ws_pos = cmds.xform(ik_handle, q=True, t=True, ws=True)
            jnt_ws_pos = cmds.xform(jnt, q=True, t=True, ws=True)
            mag = calculate_distance(ik_handle_ws_pos[0], ik_handle_ws_pos[1], ik_handle_ws_pos[2], jnt_ws_pos[0],
                                     jnt_ws_pos[1], jnt_ws_pos[2])
            jnt_magnitude_pairs.append([jnt, mag])
        # Find The Lowest Distance
        current_jnt = jnt_magnitude_pairs[1:][0]
        current_closest = jnt_magnitude_pairs[1:][1]
        for pair in jnt_magnitude_pairs:
            if pair[1] < current_closest:
                current_closest = pair[1]
                current_jnt = pair[0]
        end_ik_jnt = current_jnt

    distance_one = cmds.distanceDimension(sp=(1, random.random() * 10, 1), ep=(2, random.random() * 10, 2))
    distance_one_transform = cmds.listRelatives(distance_one, parent=True, f=True) or [][0]
    distance_one_locators = cmds.listConnections(distance_one)
    cmds.delete(cmds.pointConstraint(ik_handle_joints[0], distance_one_locators[0]))
    cmds.delete(cmds.pointConstraint(ik_handle, distance_one_locators[1]))

    # Rename Distance One Nodes
    distance_node_one = cmds.rename(distance_one_transform, stretchy_name + "_stretchyTerm_strechyDistance")
    start_loc_one = cmds.rename(distance_one_locators[0], stretchy_name + "_stretchyTerm_start")
    end_loc_one = cmds.rename(distance_one_locators[1], stretchy_name + "_stretchyTerm_end")

    distance_nodes = {}  # [distance_node_transform, start_loc, end_loc, ik_handle_joint]
    for index in range(len(ik_handle_joints)):
        distance_node = cmds.distanceDimension(sp=(1, random.random() * 10, 1), ep=(2, random.random() * 10, 2))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, f=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)

        distance_node = cmds.rename(distance_node, stretchy_name + '_defaultTerm' + int_to_en(
            index + 1).capitalize() + '_strechyDistanceShape')
        distance_node_transform = cmds.rename(distance_node_transform, stretchy_name + '_defaultTerm' + int_to_en(
            index + 1).capitalize() + '_strechyDistance')
        start_loc = cmds.rename(distance_node_locators[0],
                                stretchy_name + '_defaultTerm' + int_to_en(index + 1).capitalize() + '_start')
        end_loc = cmds.rename(distance_node_locators[1],
                              stretchy_name + '_defaultTerm' + int_to_en(index + 1).capitalize() + '_end')

        cmds.delete(cmds.pointConstraint(ik_handle_joints[index], start_loc))
        if index < (len(ik_handle_joints) - 1):
            cmds.delete(cmds.pointConstraint(ik_handle_joints[index + 1], end_loc))
        else:
            cmds.delete(cmds.pointConstraint(end_ik_jnt, end_loc))

        distance_nodes[distance_node] = [distance_node_transform, start_loc, end_loc, ik_handle_joints[index]]

        index += 1

    # Organize Basic Hierarchy
    stretchy_grp = cmds.group(name=stretchy_name + "_stretchy_grp", empty=True, world=True)
    cmds.parent(distance_node_one, stretchy_grp)
    cmds.parent(start_loc_one, stretchy_grp)
    cmds.parent(end_loc_one, stretchy_grp)

    # Connect, Colorize and Organize Hierarchy
    default_distance_sum_node = cmds.createNode('plusMinusAverage', name=stretchy_name + "_defaultTermSum_plus")
    index = 0
    for node in distance_nodes:
        cmds.connectAttr('%s.distance' % node, '%s.input1D' % default_distance_sum_node + '[' + str(index) + ']')
        for obj in distance_nodes.get(node):
            if cmds.objectType(obj) != 'joint':
                change_outliner_color(obj, (1, .5, .5))
                cmds.parent(obj, stretchy_grp)
        index += 1

    # Outliner Color
    for obj in [distance_node_one, start_loc_one, end_loc_one]:
        change_outliner_color(obj, (.5, 1, .2))

    # Connect Nodes
    nonzero_stretch_condition_node = cmds.createNode('condition', name=stretchy_name + "_strechyNonZero_condition")
    nonzero_multiply_node = cmds.createNode('multiplyDivide', name=stretchy_name + "_onePctDistCondition_multiply")
    cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.input1X' % nonzero_multiply_node)
    cmds.setAttr(nonzero_multiply_node + ".input2X", 0.01)
    cmds.connectAttr('%s.outputX' % nonzero_multiply_node, '%s.colorIfTrueR' % nonzero_stretch_condition_node)
    cmds.connectAttr('%s.outputX' % nonzero_multiply_node, '%s.secondTerm' % nonzero_stretch_condition_node)
    cmds.setAttr(nonzero_stretch_condition_node + ".operation", 5)

    stretch_normalization_node = cmds.createNode('multiplyDivide', name=stretchy_name + "_distNormalization_divide")
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.firstTerm' % nonzero_stretch_condition_node)
    cmds.connectAttr('%s.distance' % distance_node_one, '%s.colorIfFalseR' % nonzero_stretch_condition_node)
    cmds.connectAttr('%s.outColorR' % nonzero_stretch_condition_node, '%s.input1X' % stretch_normalization_node)

    cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.input2X' % stretch_normalization_node)

    cmds.setAttr(stretch_normalization_node + ".operation", 2)

    stretch_condition_node = cmds.createNode('condition', name=stretchy_name + "_strechyAutomation_condition")
    cmds.setAttr(stretch_condition_node + ".operation", 3)
    cmds.connectAttr('%s.outColorR' % nonzero_stretch_condition_node,
                     '%s.firstTerm' % stretch_condition_node)  # Distance One
    cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.secondTerm' % stretch_condition_node)
    cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.colorIfTrueR' % stretch_condition_node)

    # Constraints
    cmds.pointConstraint(ik_handle_joints[0], start_loc_one)
    start_loc_condition = ''
    for node in distance_nodes:
        if distance_nodes.get(node)[3] == ik_handle_joints[0:][0]:
            start_loc_condition = cmds.pointConstraint(ik_handle_joints[0], distance_nodes.get(node)[1])

    # Attribute Holder Setup
    if attribute_holder:
        if cmds.objExists(attribute_holder):
            cmds.pointConstraint(attribute_holder, end_loc_one)
            cmds.addAttr(attribute_holder, ln='stretch', at='double', k=True, minValue=0, maxValue=1)
            cmds.setAttr(attribute_holder + ".stretch", 1)
            cmds.addAttr(attribute_holder, ln='squash', at='double', k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder, ln='stretchFromSource', at='bool', k=True)
            cmds.addAttr(attribute_holder, ln='saveVolume', at='double', k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder, ln='baseVolumeMultiplier', at='double', k=True, minValue=0, maxValue=1)
            cmds.setAttr(attribute_holder + ".baseVolumeMultiplier", .5)
            cmds.addAttr(attribute_holder, ln='minimumVolume', at='double', k=True, minValue=0.01, maxValue=1)
            cmds.addAttr(attribute_holder, ln='maximumVolume', at='double', k=True, minValue=0)
            cmds.setAttr(attribute_holder + ".minimumVolume", .4)
            cmds.setAttr(attribute_holder + ".maximumVolume", 2)
            cmds.setAttr(attribute_holder + ".stretchFromSource", 1)

            # Stretch From Body
            from_body_reverse_node = cmds.createNode('reverse', name=stretchy_name + '_stretchFromSource_reverse')
            cmds.connectAttr('%s.stretchFromSource' % attribute_holder, '%s.inputX' % from_body_reverse_node)
            cmds.connectAttr('%s.outputX' % from_body_reverse_node, '%s.w0' % start_loc_condition[0])

            # Squash
            squash_condition_node = cmds.createNode('condition', name=stretchy_name + "_squashAutomation_condition")
            cmds.setAttr(squash_condition_node + ".secondTerm", 1)
            cmds.setAttr(squash_condition_node + ".colorIfTrueR", 1)
            cmds.setAttr(squash_condition_node + ".colorIfFalseR", 3)
            cmds.connectAttr('%s.squash' % attribute_holder, '%s.firstTerm' % squash_condition_node)
            cmds.connectAttr('%s.outColorR' % squash_condition_node, '%s.operation' % stretch_condition_node)

            # Stretch
            activation_blend_node = cmds.createNode('blendTwoAttr', name=stretchy_name + "_strechyActivation_blend")
            cmds.setAttr(activation_blend_node + ".input[0]", 1)
            cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.input[1]' % activation_blend_node)
            cmds.connectAttr('%s.stretch' % attribute_holder, '%s.attributesBlender' % activation_blend_node)

            for jnt in ik_handle_joints:
                cmds.connectAttr('%s.output' % activation_blend_node, '%s.scaleX' % jnt)

            # Save Volume
            save_volume_condition_node = cmds.createNode('condition', name=stretchy_name + "_saveVolume_condition")
            volume_normalization_divide_node = cmds.createNode('multiplyDivide',
                                                               name=stretchy_name + "_volumeNormalization_divide")
            volume_value_divide_node = cmds.createNode('multiplyDivide', name=stretchy_name + "_volumeValue_divide")
            xy_divide_node = cmds.createNode('multiplyDivide', name=stretchy_name + "_volumeXY_divide")
            volume_blend_node = cmds.createNode('blendTwoAttr', name=stretchy_name + "_volumeActivation_blend")
            volume_clamp_node = cmds.createNode('clamp', name=stretchy_name + "_volumeLimits_clamp")
            volume_base_blend_node = cmds.createNode('blendTwoAttr', name=stretchy_name + "_volumeBase_blend")

            cmds.setAttr(save_volume_condition_node + ".secondTerm", 1)
            cmds.setAttr(volume_normalization_divide_node + ".operation", 2)  # Divide
            cmds.setAttr(volume_value_divide_node + ".operation", 2)  # Divide
            cmds.setAttr(xy_divide_node + ".operation", 2)  # Divide

            cmds.connectAttr('%s.outColorR' % nonzero_stretch_condition_node,
                             '%s.input2X' % volume_normalization_divide_node)  # Distance One
            cmds.connectAttr('%s.output1D' % default_distance_sum_node, '%s.input1X' % volume_normalization_divide_node)

            cmds.connectAttr('%s.outputX' % volume_normalization_divide_node, '%s.input2X' % volume_value_divide_node)
            cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.input1X' % volume_value_divide_node)

            cmds.connectAttr('%s.outputX' % volume_value_divide_node, '%s.input2X' % xy_divide_node)
            cmds.connectAttr('%s.outputX' % stretch_normalization_node, '%s.input1X' % xy_divide_node)

            cmds.setAttr(volume_blend_node + ".input[0]", 1)
            cmds.connectAttr('%s.outputX' % xy_divide_node, '%s.input[1]' % volume_blend_node)

            cmds.connectAttr('%s.saveVolume' % attribute_holder, '%s.attributesBlender' % volume_blend_node)

            cmds.connectAttr('%s.output' % volume_blend_node, '%s.inputR' % volume_clamp_node)
            cmds.connectAttr('%s.outputR' % volume_clamp_node, '%s.colorIfTrueR' % save_volume_condition_node)

            cmds.connectAttr('%s.stretch' % attribute_holder, '%s.firstTerm' % save_volume_condition_node)
            cmds.connectAttr('%s.minimumVolume' % attribute_holder, '%s.minR' % volume_clamp_node)
            cmds.connectAttr('%s.maximumVolume' % attribute_holder, '%s.maxR' % volume_clamp_node)

            # Base Multiplier
            cmds.setAttr(volume_base_blend_node + ".input[0]", 1)
            cmds.connectAttr('%s.outColorR' % save_volume_condition_node, '%s.input[1]' % volume_base_blend_node)
            cmds.connectAttr('%s.baseVolumeMultiplier' % attribute_holder,
                             '%s.attributesBlender' % volume_base_blend_node)

            # Connect to Joints
            cmds.connectAttr('%s.output' % volume_base_blend_node, '%s.scaleY' % ik_handle_joints[0])
            cmds.connectAttr('%s.output' % volume_base_blend_node, '%s.scaleZ' % ik_handle_joints[0])

            for jnt in ik_handle_joints[1:]:
                cmds.connectAttr('%s.outColorR' % save_volume_condition_node, '%s.scaleY' % jnt)
                cmds.connectAttr('%s.outColorR' % save_volume_condition_node, '%s.scaleZ' % jnt)

        else:
            for jnt in ik_handle_joints:
                cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.scaleX' % jnt)
    else:
        for jnt in ik_handle_joints:
            cmds.connectAttr('%s.outColorR' % stretch_condition_node, '%s.scaleX' % jnt)

    return [end_loc_one, stretchy_grp, end_ik_jnt]


# Build UI
if __name__ == '__main__':
    build_gui_make_ik_stretchy()
