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

 0.4.0 - 2022-08-23
 Changed script name from "Outliner Manager" to "Outliner Sorter"
 Added attribute operation to sort function
 Started GUI

"""
from maya import OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import logging
import random
import sys

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
script_version = "0.4.0"


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
    def update_settings(*args):
        logger.debug(str(args))
        desired_filter_string = cmds.textField(desired_filter_textfield, q=True, text=True)
        undesired_filter_string = cmds.textField(undesired_filter_textfield, q=True, text=True)
        desired_filter_option_string = str(cmds.optionMenu(desired_filter_option, q=True, value=True))
        undesired_filter_option_string = str(cmds.optionMenu(undesired_filter_option, q=True, value=True))

        ignore_connected_value = cmds.checkBox(ignore_connected_chk, q=True, value=True)
        add_separator_value = cmds.checkBox(add_separator_chk, q=True, value=True)
        modify_range_value = cmds.checkBox(modify_range_chk, q=True, value=True)
        ignore_case_value = cmds.checkBox(ignore_case_chk, q=True, value=True)
        delete_instead_value = cmds.checkBox(delete_instead_chk, q=True, value=True)
        sort_value = cmds.checkBox(sort_chk, q=True, value=True)

        old_min_int = cmds.intField(old_min_int_field, q=True, value=True)
        old_max_int = cmds.intField(old_max_int_field, q=True, value=True)
        new_min_int = cmds.intField(new_min_int_field, q=True, value=True)
        new_max_int = cmds.intField(new_max_int_field, q=True, value=True)

        if modify_range_value:
            cmds.rowColumnLayout(range_column, e=True, en=True)
        else:
            cmds.rowColumnLayout(range_column, e=True, en=False)

        morphing_attr_settings['modify_range'] = modify_range_value
        morphing_attr_settings['ignore_connected'] = ignore_connected_value
        morphing_attr_settings['add_separator'] = add_separator_value
        morphing_attr_settings['desired_filter_string'] = desired_filter_string
        morphing_attr_settings['undesired_filter_string'] = undesired_filter_string
        morphing_attr_settings['ignore_case'] = ignore_case_value
        morphing_attr_settings['desired_filter_type'] = desired_filter_option_string.replace(' ', '').lower()
        morphing_attr_settings['undesired_filter_type'] = undesired_filter_option_string.replace(' ', '').lower()
        morphing_attr_settings['old_range_min'] = old_min_int
        morphing_attr_settings['old_range_max'] = old_max_int
        morphing_attr_settings['new_range_min'] = new_min_int
        morphing_attr_settings['new_range_max'] = new_max_int
        morphing_attr_settings['delete_instead'] = delete_instead_value
        morphing_attr_settings['sort_attr'] = sort_value

        logger.debug('Updated Settings Called')
        logger.debug('modify_range: ' + str(morphing_attr_settings.get('modify_range')))
        logger.debug('ignore_connected: ' + str(morphing_attr_settings.get('ignore_connected')))
        logger.debug('add_separator: ' + str(morphing_attr_settings.get('add_separator')))
        logger.debug('desired_filter_string: ' + str(morphing_attr_settings.get('desired_filter_string')))
        logger.debug('undesired_filter_string: ' + str(morphing_attr_settings.get('undesired_filter_string')))
        logger.debug('ignore_case: ' + str(morphing_attr_settings.get('ignore_case')))
        logger.debug('sort_attr: ' + str(morphing_attr_settings.get('sort_attr')))
        logger.debug('desired_filter_type: ' + str(morphing_attr_settings.get('desired_filter_type')))
        logger.debug('undesired_filter_type: ' + str(morphing_attr_settings.get('undesired_filter_type')))
        logger.debug('old_range_min: ' + str(morphing_attr_settings.get('old_range_min')))
        logger.debug('old_range_max: ' + str(morphing_attr_settings.get('old_range_max')))
        logger.debug('new_range_min: ' + str(morphing_attr_settings.get('new_range_min')))
        logger.debug('new_range_max: ' + str(morphing_attr_settings.get('new_range_max')))
        logger.debug('delete_instead: ' + str(morphing_attr_settings.get('delete_instead')))

    def select_blend_shape_node():
        error_message = "Unable to locate blend shape node. Please try again."
        blend_node = cmds.textScrollList(blend_nodes_scroll_list, q=True, selectItem=True) or []
        if blend_node:
            if cmds.objExists(blend_node[0]):
                sys.stdout.write('"' + str(blend_node[0]) + '" will be used when creating attributes.')
                morphing_attr_settings['blend_node'] = blend_node[0]
            else:
                cmds.warning(error_message)
                morphing_attr_settings['blend_node'] = ''
        else:
            cmds.warning(error_message)
            morphing_attr_settings['blend_node'] = ''

    def object_load_handler(operation):
        """
        Function to handle load buttons. It updates the UI to reflect the loaded data.

        Args:
            operation (str): String to determine function ("morphing_obj" or "attr_holder")
        """
        def failed_to_load_source(failed_message="Failed to Load"):
            cmds.button(source_object_status, l=failed_message, e=True, bgc=(1, .4, .4), w=130)
            cmds.textScrollList(blend_nodes_scroll_list, e=True, removeAll=True)
            morphing_attr_settings['morphing_obj'] = ''

        def failed_to_load_target(failed_message="Failed to Load"):
            cmds.button(attr_holder_status, l=failed_message, e=True, bgc=(1, .4, .4), w=130)
            morphing_attr_settings['attr_holder'] = ''

        # Blend Mesh
        if operation == 'morphing_obj':
            current_selection = cmds.ls(selection=True) or []
            if not current_selection:
                cmds.warning("Nothing selected. Please select a mesh try again.")
                failed_to_load_source()
                return

            if len(current_selection) > 1:
                cmds.warning("You selected more than one source object! Please select only one object and try again.")
                failed_to_load_source()
                return

            if cmds.objExists(current_selection[0]):
                history = cmds.listHistory(current_selection[0])
                blendshape_nodes = cmds.ls(history, type='blendShape') or []
                if not blendshape_nodes:
                    cmds.warning("Unable to find blend shape nodes on the selected object.")
                    failed_to_load_source()
                    return
                else:
                    morphing_attr_settings['morphing_obj'] = current_selection[0]
                    cmds.button(source_object_status, l=morphing_attr_settings.get('morphing_obj'),
                                e=True, bgc=(.6, .8, .6), w=130)
                    cmds.textScrollList(blend_nodes_scroll_list, e=True, removeAll=True)
                    cmds.textScrollList(blend_nodes_scroll_list, e=True, append=blendshape_nodes)

        # Attr Holder
        if operation == 'attr_holder':
            current_selection = cmds.ls(selection=True)
            if len(current_selection) == 0:
                cmds.warning("Nothing selected.")
                failed_to_load_target()
                return
            elif len(current_selection) > 1:
                cmds.warning("You selected more than one object! Please select only one")
                failed_to_load_target()
                return
            elif cmds.objExists(current_selection[0]):
                morphing_attr_settings['attr_holder'] = current_selection[0]
                cmds.button(attr_holder_status, l=morphing_attr_settings.get('attr_holder'), e=True,
                            bgc=(.6, .8, .6), w=130)
            else:
                cmds.warning("Something went wrong, make sure you selected just one object and try again.")

    def validate_operation():
        """ Checks elements one last time before running the script """
        update_settings()

        # Attribute Holder
        attr_holder = morphing_attr_settings.get('attr_holder')
        if attr_holder:
            if not cmds.objExists(attr_holder):
                cmds.warning('Unable to locate attribute holder. Please try loading the object again.')
                return False
        else:
            cmds.warning('Missing attribute holder. Make sure you loaded an object and try again.')
            return False

        # Blend Shape Node
        blend_node = morphing_attr_settings.get('blend_node')
        if blend_node:
            if not cmds.objExists(blend_node):
                cmds.warning('Unable to blend shape node. Please try loading the object again.')
                return False
        else:
            cmds.warning('Select a blend shape node to be used as source.')
            return False

        # # Run Script
        logger.debug('Main Function Called')
        undesired_strings = morphing_attr_settings.get('undesired_filter_string').replace(' ', '')
        if undesired_strings:
            undesired_strings = undesired_strings.split(',')
        else:
            undesired_strings = []
        desired_strings = morphing_attr_settings.get('desired_filter_string').replace(' ', '')
        if desired_strings:
            desired_strings = desired_strings.split(',')
        else:
            desired_strings = []

        current_selection = cmds.ls(selection=True)
        cmds.undoInfo(openChunk=True, chunkName=script_name)  # Start undo chunk
        try:
            blend_attr_list = blends_to_attr(blend_node, attr_holder, desired_strings, undesired_strings,
                                             desired_method=morphing_attr_settings.get('desired_filter_type'),
                                             undesired_method=morphing_attr_settings.get('undesired_filter_type'),
                                             ignore_connected=morphing_attr_settings.get('ignore_connected'),
                                             add_separator=morphing_attr_settings.get('add_separator'),
                                             ignore_case=morphing_attr_settings.get('ignore_case'),
                                             modify_range=morphing_attr_settings.get('modify_range'),
                                             old_min=morphing_attr_settings.get('old_range_min'),
                                             old_max=morphing_attr_settings.get('old_range_max'),
                                             new_min=morphing_attr_settings.get('new_range_min'),
                                             new_max=morphing_attr_settings.get('new_range_max'),
                                             delete_instead=morphing_attr_settings.get('delete_instead'),
                                             sort_attr=morphing_attr_settings.get('sort_attr'))

            if blend_attr_list:
                message = '<' + str(random.random()) + '>'
                message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(len(blend_attr_list))
                message += ' </span>'
                is_plural = 'morphing attributes were'
                if len(blend_attr_list) == 1:
                    is_plural = 'morphing attribute was'
                operation_message = ' created/connected.'
                if morphing_attr_settings.get('delete_instead'):
                    operation_message = ' deleted.'
                message += is_plural + operation_message
                cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
                sys.stdout.write(str(len(blend_attr_list)) + ' ' + is_plural + operation_message)
                return True
            else:
                if morphing_attr_settings.get('delete_instead'):
                    sys.stdout.write('No attributes were deleted. Review your settings and try again.')
                else:
                    sys.stdout.write('No attributes were created. Review your settings and try again.')

            return False
        except Exception as e:
            logger.debug(str(e))
            return False
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
    cmds.button(l="Move Down", c=lambda x: validate_operation("reorder_down"), w=130)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 130), (2, 130)], cs=[(1, 10), (2, 5)], p=content_main)
    cmds.button(l="Move Front", c=lambda x: validate_operation("reorder_front"), w=130)
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
    undesired_filter_textfield = cmds.textField(text='', pht='Custom Attribute (Optional)', cc=update_settings)
    undesired_filter_option = cmds.optionMenu(label='', cc=update_settings)
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

    cmds.button(l="Sort by Attribute", bgc=(.6, .6, .6), c=lambda x: validate_operation())
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
