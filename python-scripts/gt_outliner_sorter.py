"""
 GT Outliner Manager - General Outliner organization script
 github.com/TrevisanGMW/gt-tools - 2022-08-18

 0.1.0 - 2022-08-20
 Added reorder utility functions

 0.2.0 - 2022-08-21
 Added main sort function

 0.3.0 - 2022-08-21
 Added main sort function

 0.3.1 - 2022-08-22
 Added ascending/descending option to sort function
 Added attribute operation to sort function

 0.4.0 to 0.4.1 - 2022-08-23
 Changed script name from "Outliner Manager" to "Outliner Sorter"
 Added attribute operation to sort function
 Started GUI
    - Created Main Window
    - Added validate_operation and connected utilities
    - Added Sort by Attribute, custom attribute field and default channel drop-down menu

"""
from maya import OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import logging
import random

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

logging.basicConfig()
logger = logging.getLogger("gt_outliner_sorter")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT - Outliner Sorter"

# Version:
script_version = "0.4.1"


def reorder_up(obj_list):
    """
    Reorder objects in the outliner relative to their siblings (move them up)
    Args:
        obj_list: List of objects to be reordered (not existing objects are ignored)

    Returns:
        operation_result: True = at least one object was updated, False = unable to find valid objects
    """
    valid_obj_list = []
    for obj in obj_list:
        if cmds.objExists(obj):
            valid_obj_list.append(obj)
    cmds.reorder(valid_obj_list, relative=-1)
    if valid_obj_list:
        return True
    else:
        return False


def reorder_down(obj_list):
    """
    Reorder objects in the outliner relative to their siblings (move them down)
    Args:
        obj_list: List of objects to be reordered (not existing objects are ignored)

    Returns:
        operation_result: True = at least one object was updated, False = unable to find valid objects
    """
    valid_obj_list = []
    for obj in obj_list:
        if cmds.objExists(obj):
            valid_obj_list.append(obj)
    cmds.reorder(valid_obj_list, relative=1)
    if valid_obj_list:
        return True
    else:
        return False


def reorder_front(obj_list):
    """
    Reorder objects in the outliner relative to their siblings (move them to the top)
    Args:
        obj_list: List of objects to be reordered (not existing objects are ignored)

    Returns:
        operation_result: True = at least one object was updated, False = unable to find valid objects
    """
    valid_obj_list = []
    for obj in obj_list:
        if cmds.objExists(obj):
            valid_obj_list.append(obj)
    cmds.reorder(valid_obj_list, front=True)
    if valid_obj_list:
        return True
    else:
        return False


def reorder_back(obj_list):
    """
    Reorder objects in the outliner relative to their siblings (move them to the bottom)
    Args:
        obj_list: List of objects to be reordered (not existing objects are ignored)

    Returns:
        operation_result: True = at least one object was updated, False = unable to find valid objects
    """
    valid_obj_list = []
    for obj in obj_list:
        if cmds.objExists(obj):
            valid_obj_list.append(obj)
    cmds.reorder(valid_obj_list, back=True)
    if valid_obj_list:
        return True
    else:
        return False


def get_short_name(obj):
    """
    Get the name of the objects without its path (Maya returns full path if name is not unique)

    Args:
        obj (string) : object to extract short name

    Returns:
        short_name (string) : Name of the object without its full path
    """
    short_name = ''
    if obj == '':
        return ''
    split_path = obj.split('|')
    if len(split_path) >= 1:
        short_name = split_path[len(split_path) - 1]
    return short_name


def outliner_sort(obj_list, sort_operation='name', is_ascending=True, attr='ty'):
    logger.debug('obj_list: ' + str(obj_list))
    issues = ''

    target_objects = {}

    for target_obj in obj_list:
        short_name = get_short_name(target_obj)
        target_objects[short_name] = target_obj

    sorted_target = sorted(target_objects, reverse=is_ascending)

    if sort_operation == 'name':
        for target_key in sorted_target:
            try:
                reorder_front([target_objects.get(target_key)])
            except Exception as e:
                issues += str(e) + '\n'
            logger.debug('target_value: ' + str([target_objects.get(target_key)]))

    if sort_operation == 'shuffle':
        random.shuffle(obj_list)
        for target_obj in obj_list:
            try:
                reorder_front([target_obj])
            except Exception as e:
                issues += str(e) + '\n'
            logger.debug('target_value: ' + str([target_obj]))

    if sort_operation == 'attribute':
        value_dict = {}
        for target_obj in obj_list:
            try:
                value = cmds.getAttr(target_obj + '.' + attr)
            except Exception as e:
                logger.debug(str(e))
                value = 0
            logger.debug(target_obj + ' ' + str(value))
            value_dict[target_obj] = value

        sorted_dict = dict(sorted(value_dict.items(), key=lambda item: item[1], reverse=not is_ascending))
        for key in sorted_dict:
            try:
                reorder_front([key])
            except Exception as e:
                issues += str(e) + '\n'
            logger.debug('target_value: ' + str([key]))

    if issues:
        print(issues)



def build_gui_outliner_sorter():
    """ Creates window for Outliner Sorter """
    def validate_operation(operation):
        """ Checks elements one last time before running the script """
        logger.debug('operation: ' + str(operation))

        current_selection = cmds.ls(selection=True, long=True) or []

        if not current_selection:
            cmds.warning('Nothing selected. Please select objects you want to sort and try again.')
            return False

        cmds.undoInfo(openChunk=True, chunkName=script_name)  # Start undo chunk
        try:
            if operation == 'reorder_up':
                reorder_up(current_selection)
            elif operation == 'reorder_down':
                reorder_down(current_selection)
            elif operation == 'reorder_front':
                reorder_front(current_selection)
            elif operation == 'reorder_back':
                reorder_back(current_selection)

        except Exception as e:
            logger.debug(str(e))

        finally:
            cmds.undoInfo(closeChunk=True, chunkName=script_name)
            cmds.select(current_selection)

    window_name = "build_gui_outliner_sorter"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    # Build UI
    window_gui_blends_to_attr = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                            titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 275)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 55)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: _open_gt_tools_documentation())
    cmds.separator(h=5, style='none')  # Empty Space

    # 1. Deformed Mesh (Source) ------------------------------------------
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Sort Utilities:')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 130), (2, 130)], cs=[(1, 10), (2, 5)], p=content_main)
    cmds.button(l="Move Up", c=lambda x: validate_operation("reorder_up"), w=130)
    cmds.button(l="Move Front", c=lambda x: validate_operation("reorder_front"), w=130)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 130), (2, 130)], cs=[(1, 10), (2, 5)], p=content_main)
    cmds.button(l="Move Down", c=lambda x: validate_operation("reorder_down"), w=130)
    cmds.button(l="Move Back", c=lambda x: validate_operation("reorder_back"), w=130)

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    # Sort by Attribute ------------------------------------------
    cmds.rowColumnLayout(nc=1, cw=[(1, 265)], cs=[(1, 10), (2, 5)], p=content_main)
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.text("Sort by Attribute")
    cmds.separator(h=7, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 165)], cs=[(1, 10), (2, 5)], p=content_main)
    undesired_filter_textfield = cmds.textField(text='', pht='Custom Attribute (Optional)')
    undesired_filter_option = cmds.optionMenu(label='')
    cmds.menuItem(label='translateX')
    cmds.menuItem(label='translateY')
    cmds.menuItem(label='translateZ')
    cmds.menuItem(label='rotateX')
    cmds.menuItem(label='rotateY')
    cmds.menuItem(label='rotateZ')
    cmds.menuItem(label='scaleX')
    cmds.menuItem(label='scaleY')
    cmds.menuItem(label='scaleZ')
    cmds.menuItem(label='visibility')
    cmds.menuItem(label='custom')
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 265)], cs=[(1, 10)], p=content_main)
    # cmds.separator(h=7, style='none')  # Empty Space
    # cmds.separator(h=5)
    cmds.separator(h=7, style='none')  # Empty Space

    cmds.button(l="Sort by Attribute", bgc=(.6, .6, .6), c=lambda x: validate_operation('sort_attribute'))
    cmds.separator(h=10, style='none')  # Empty Space

    # Show and Lock Window
    cmds.showWindow(window_gui_blends_to_attr)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/outliner.png')
    widget.setWindowIcon(icon)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_name)


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    selection = cmds.ls(selection=True, long=True)
    # cmds.reorder(selection[0], front=True)
    # reorder_up(selection)
    # reorder_back(selection)
    # outliner_sort(selection, is_ascending=True)
    # outliner_sort(selection, sort_operation='shuffle')
    # outliner_sort(selection, sort_operation='attribute', attr='ty', is_ascending=True)
    build_gui_outliner_sorter()
