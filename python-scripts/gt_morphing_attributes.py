"""
GT Blends to Attributes
github.com/TrevisanGMW/gt-tools - 2022-03-17

0.0.1 - 2022-03-17
Create core function

0.0.2 - 2022-07-23
Create GUI

0.0.3 - 2022-07-23
Added settings

TODO:
    Create filter logic
    Connect core function

"""
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
import logging
import random
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_blends_to_attributes")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT - Add Morphing Attributes"

# Version:
script_version = "0.0.3"

# Settings
morphing_attr_settings = {'morphing_obj': '',
                          'blend_node': '',
                          'attr_holder': '',
                          'filter_string': '',
                          'filter_type': 'includes',
                          'filter_undesired': False,
                          'modify_range': True,
                          'new_range_min': 0,
                          'new_range_max': 10,
                          'old_range_min': 0,
                          'old_range_max': 1,
                          'ignore_connected': True,
                          'add_separator': True,
                          }


def blends_to_attr(morphing_obj, blend_node, attr_holder):
    logger.debug(str(morphing_obj))
    selection_target = attr_holder
    blendshape_node = blend_node
    blendshape_names = cmds.listAttr(blendshape_node + '.w', m=True)

    modify_range = True
    attribute_range_min = 0
    attribute_range_max = 10
    blend_range_min = 0
    blend_range_max = 1

    ignore_connected = True
    add_separator_attribute = True
    custom_separator_attr = ''
    method = 'includes'

    undesired_filter_strings = ['corrective']
    desired_blends = []
    desired_filter_strings = ['jaw', 'cheek', 'mouth', 'nose']
    filtered_blends = []

    # Find desired blends
    for target in blendshape_names:
        for desired_filter_string in desired_filter_strings:
            if method == 'includes':
                if desired_filter_string in target:
                    filtered_blends.append(target)
            elif method == 'startswith':
                if target.startswith(desired_filter_string):
                    filtered_blends.append(target)
            elif method == 'endswith':
                if target.endswith(desired_filter_string):
                    filtered_blends.append(target)

    if len(desired_filter_strings) == 0:  # If filter empty, use everything
        filtered_blends = blendshape_names

    if ignore_connected:  # Pre-ignore connected blends
        accessible_blends = []
        for blend in filtered_blends:
            connections = cmds.listConnections(blendshape_node + '.' + blend, destination=False, plugs=True) or []
            if len(connections) == 0:
                accessible_blends.append(blend)
    else:
        accessible_blends = filtered_blends

    # Remove undesired blends from list
    undesired_blends = []
    for target in desired_blends:
        for undesired_string in undesired_filter_strings:
            if undesired_string in target:
                undesired_blends.append(target)
    for blend in accessible_blends:
        if blend not in undesired_blends:
            desired_blends.append(blend)

    # Separator Attribute
    if len(desired_blends) != 0 and add_separator_attribute:
        separator_attr = 'blends'
        if custom_separator_attr:
            separator_attr = custom_separator_attr
        cmds.addAttr(selection_target, ln=separator_attr, at='enum', en='-------------:', keyable=True)
        cmds.setAttr(selection_target + '.' + separator_attr, e=True, lock=True)

    # Create Blend Drivers
    desired_blends.sort()
    for target in desired_blends:
        if modify_range:
            cmds.addAttr(selection_target, ln=target, at='double', k=True,
                         maxValue=attribute_range_max, minValue=attribute_range_min)
            remap_node = cmds.createNode('remapValue', name='remap_bs_' + target)
            cmds.setAttr(remap_node + '.inputMax', attribute_range_max)
            cmds.setAttr(remap_node + '.inputMin', attribute_range_min)
            cmds.setAttr(remap_node + '.outputMax', blend_range_max)
            cmds.setAttr(remap_node + '.outputMin', blend_range_min)
            cmds.connectAttr(selection_target + '.' + target, remap_node + '.inputValue')
            cmds.connectAttr(remap_node + '.outValue', blendshape_node + '.' + target, force=True)
        else:
            cmds.addAttr(selection_target, ln=target, at='double', k=True, maxValue=1, minValue=0)
            cmds.connectAttr(selection_target + '.' + target, blendshape_node + '.' + target, force=True)


def build_gui_morphing_attributes():

    def update_settings(*args):
        logger.debug(str(args))
        filter_string = cmds.textField(filter_textfield, q=True, text=True)
        filter_option_string = str(cmds.optionMenu(filter_option, q=True, value=True))

        ignore_connected_value = cmds.checkBox(ignore_connected_chk, q=True,
                                               value=morphing_attr_settings.get('ignore_connected'))
        add_separator_value = cmds.checkBox(add_separator_chk, q=True,
                                            value=morphing_attr_settings.get('add_separator'))
        modify_range_value = cmds.checkBox(modify_range_chk, q=True,
                                           value=morphing_attr_settings.get('modify_range'))
        filter_undesired_value = cmds.checkBox(filter_undesired_chk, q=True,
                                               value=morphing_attr_settings.get('filter_undesired'))

        old_min_int = cmds.intField(old_min_int_field, q=True, value=True)
        old_max_int = cmds.intField(old_max_int_field, q=True, value=True)
        new_min_int = cmds.intField(new_min_int_field, q=True, value=True)
        new_max_int = cmds.intField(new_max_int_field, q=True, value=True)

        if modify_range_value:
            cmds.rowColumnLayout(range_column, e=True, en=True)
        else:
            cmds.rowColumnLayout(range_column, e=True, en=False)

        if filter_undesired_value:
            cmds.textField(filter_textfield, e=True, pht='Undesired Filter (Optional)')
        else:
            cmds.textField(filter_textfield, e=True, pht='Desired Filter (Optional)')

        morphing_attr_settings['modify_range'] = modify_range_value
        morphing_attr_settings['ignore_connected'] = ignore_connected_value
        morphing_attr_settings['add_separator'] = add_separator_value
        morphing_attr_settings['filter_string'] = filter_string
        morphing_attr_settings['filter_undesired'] = filter_undesired_value
        morphing_attr_settings['filter_type'] = filter_option_string.replace(' ', '').lower()
        morphing_attr_settings['old_range_min'] = old_min_int
        morphing_attr_settings['old_range_max'] = old_max_int
        morphing_attr_settings['new_range_min'] = new_min_int
        morphing_attr_settings['new_range_max'] = new_max_int

        logger.debug('modify_range: ' + str(morphing_attr_settings.get('modify_range')))
        logger.debug('ignore_connected: ' + str(morphing_attr_settings.get('ignore_connected')))
        logger.debug('add_separator: ' + str(morphing_attr_settings.get('add_separator')))
        logger.debug('filter_string: ' + str(morphing_attr_settings.get('filter_string')))
        logger.debug('filter_undesired: ' + str(morphing_attr_settings.get('filter_undesired')))
        logger.debug('filter_type: ' + str(morphing_attr_settings.get('filter_type')))
        logger.debug('old_range_min: ' + str(morphing_attr_settings.get('old_range_min')))
        logger.debug('old_range_max: ' + str(morphing_attr_settings.get('old_range_max')))
        logger.debug('new_range_min: ' + str(morphing_attr_settings.get('new_range_min')))
        logger.debug('new_range_max: ' + str(morphing_attr_settings.get('new_range_max')))

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

        # Morphing Object
        morphing_obj = morphing_attr_settings.get('morphing_obj')
        if morphing_obj:
            if not cmds.objExists(morphing_obj):
                cmds.warning('Unable to locate morphing object. Please try loading the object again.')
                return
        else:
            cmds.warning('Missing morphing object. Make sure you loaded an object and try again.')
            return

        # Attribute Holder
        attr_holder = morphing_attr_settings.get('attr_holder')
        if attr_holder:
            if not cmds.objExists(attr_holder):
                cmds.warning('Unable to locate attribute holder. Please try loading the object again.')
                return
        else:
            cmds.warning('Missing attribute holder. Make sure you loaded an object and try again.')
            return

        # Blend Shape Node
        blend_node = morphing_attr_settings.get('blend_node')
        if blend_node:
            if not cmds.objExists(blend_node):
                cmds.warning('Unable to blend shape node. Please try loading the object again.')
                return
        else:
            cmds.warning('Select a blend shape node to be used as source.')
            return

        # # Run Script
        logger.debug('Main Function Called')
        blends_to_attr(morphing_obj, blend_node, attr_holder)

    window_name = "build_gui_morphing_attributes"
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
    cmds.rowColumnLayout(nc=1, cw=[(1, 270)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 200), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_morphing_attr())
    cmds.separator(h=5, style='none')  # Empty Space

    # 1. Deformed Mesh (Source) ------------------------------------------
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('1. Deformed Mesh (Source):')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 129), (2, 130)], cs=[(1, 10)], p=content_main)
    cmds.button(l="Load Morphing Object", c=lambda x: object_load_handler("morphing_obj"), w=130)
    source_object_status = cmds.button(l="Not loaded yet", bgc=(.2, .2, .2), w=130,
                                       c=lambda x: select_existing_object(morphing_attr_settings.get('morphing_obj')))

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Blend Shape Nodes:', font="smallPlainLabelFont")
    blend_nodes_scroll_list = cmds.textScrollList(numberOfRows=8, allowMultiSelection=False, height=70,
                                                  selectCommand=select_blend_shape_node)

    # 2. Attribute Holder (Target) ------------------------------------------
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('2. Attribute Holder (Target):')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 129), (2, 130)], cs=[(1, 10)], p=content_main)

    cmds.button(l="Load Attribute Holder", c=lambda x: object_load_handler("attr_holder"), w=130)
    attr_holder_status = cmds.button(l="Not loaded yet", bgc=(.2, .2, .2), w=130,
                                     c=lambda x: select_existing_object(
                                         morphing_attr_settings.get('attr_holder')))

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    # 3. Settings and Filters ------------------------------------------
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.text("3. Settings and Filters")
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 165)], cs=[(1, 10), (2, 5)], p=content_main)
    filter_textfield = cmds.textField(text='', pht='Desired Filter (Optional)', cc=update_settings)
    filter_option = cmds.optionMenu(label='', cc=update_settings)
    cmds.menuItem(label='Includes')
    cmds.menuItem(label='Starts With')
    cmds.menuItem(label='Ends With')
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 120)], cs=[(1, 30), (2, 5)], p=content_main)
    ignore_connected_chk = cmds.checkBox("Ignore Connected", cc=update_settings, value=True)
    add_separator_chk = cmds.checkBox("Add Separator", cc=update_settings, value=True)
    cmds.separator(h=7, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 120)], cs=[(1, 30), (2, 5)], p=content_main)
    modify_range_chk = cmds.checkBox("Modify Range", cc=update_settings, value=True)
    filter_undesired_chk = cmds.checkBox("Filter Undesired", cc=update_settings)
    cmds.separator(h=10, style='none')  # Empty Space

    range_column = cmds.rowColumnLayout(nc=4, cw=[(1, 50)], cs=[(1, 30), (2, 5), (3, 30), (4, 5)], p=content_main)
    cmds.text("Old Min:")
    old_min_int_field = cmds.intField(width=30, value=morphing_attr_settings.get('old_range_min'), cc=update_settings)
    cmds.text("Old Max:")
    old_max_int_field = cmds.intField(width=30, value=morphing_attr_settings.get('old_range_max'), cc=update_settings)
    cmds.text("New Min:")
    new_min_int_field = cmds.intField(width=30, value=morphing_attr_settings.get('new_range_min'), cc=update_settings)
    cmds.text("New Max:")
    new_max_int_field = cmds.intField(width=30, value=morphing_attr_settings.get('new_range_max'), cc=update_settings)

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=7, style='none')  # Empty Space

    cmds.button(l="Create Morphing Attributes", bgc=(.6, .6, .6), c=lambda x: validate_operation())
    cmds.separator(h=10, style='none')  # Empty Space

    # Show and Lock Window
    cmds.showWindow(window_gui_blends_to_attr)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/ikSCsolver.svg')
    widget.setWindowIcon(icon)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_name)


# Creates Help GUI
def build_gui_help_morphing_attr():
    """ Creates GUI for Make Stretchy IK """
    window_name = "build_gui_help_morphing_attr"
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
    cmds.text(l='Help Place Holder', align="center")
    cmds.separator(h=5, style='none')  # Empty Space

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


# Build UI
if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    build_gui_morphing_attributes()
