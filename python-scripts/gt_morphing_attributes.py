"""
GT Blends to Attributes
github.com/TrevisanGMW/gt-tools - 2022-03-17

0.0.1 - 2022-03-17
Create core function

0.0.2 - 2022-07-23
Create GUI

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
script_version = "0.0.2"

# Settings
gt_blends_to_attr_settings = {'blend_mesh': '',
                              'blend_node': '',
                              'attr_holder': '',
                              }


def blends_to_attr():
    selection_source = cmds.ls(selection=True)[0]  # First selected object - Geo with BS
    selection_target = cmds.ls(selection=True)[1]  # Second selected object - Curve
    history = cmds.listHistory(selection_source)
    blendshape_node = cmds.ls(history, type='blendShape')[0]
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

    def select_blend_shape_node():
        error_message = "Unable to locate blend shape node. Please try again."
        blend_node = cmds.textScrollList(blend_nodes_scroll_list, q=True, selectItem=True) or []
        if blend_node:
            if cmds.objExists(blend_node[0]):
                sys.stdout.write('"' + str(blend_node[0]) + '" will be used when creating attributes.')
                gt_blends_to_attr_settings['blend_node'] = blend_node[0]
            else:
                cmds.warning(error_message)
                gt_blends_to_attr_settings['blend_node'] = ''
        else:
            cmds.warning(error_message)
            gt_blends_to_attr_settings['blend_node'] = ''

    def object_load_handler(operation):
        """
        Function to handle load buttons. It updates the UI to reflect the loaded data.

        Args:
            operation (str): String to determine function ("blend_mesh" or "attr_holder")
        """
        def failed_to_load_source(failed_message="Failed to Load"):
            cmds.button(source_object_status, l=failed_message, e=True, bgc=(1, .4, .4), w=130)
            cmds.textScrollList(blend_nodes_scroll_list, e=True, removeAll=True)
            gt_blends_to_attr_settings['blend_mesh'] = ''

        def failed_to_load_target(failed_message="Failed to Load"):
            cmds.button(attr_holder_status, l=failed_message, e=True, bgc=(1, .4, .4), w=130)
            gt_blends_to_attr_settings['attr_holder'] = ''

        # Blend Mesh
        if operation == 'blend_mesh':
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
                    gt_blends_to_attr_settings['blend_mesh'] = current_selection[0]
                    cmds.button(source_object_status, l=gt_blends_to_attr_settings.get('blend_mesh'),
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
                gt_blends_to_attr_settings['attr_holder'] = current_selection[0]
                cmds.button(attr_holder_status, l=gt_blends_to_attr_settings.get('attr_holder'), e=True,
                            bgc=(.6, .8, .6), w=130)
            else:
                cmds.warning("Something went wrong, make sure you selected just one object and try again.")

    def validate_operation():
        """ Checks elements one last time before running the script """
        print("validate then run")
        # is_valid = False
        # stretchy_name = None
        # attr_holder = None
        #
        # stretchy_prefix = cmds.textField(stretchy_system_prefix, q=True, text=True).replace(' ', '')
        #
        # # Name
        # if stretchy_prefix != '':
        #     stretchy_name = stretchy_prefix
        #
        # # ikHandle
        # if gt_blends_to_attr_settings.get('ik_handle') == '':
        #     cmds.warning('Please load an ikHandle first before running the script.')
        #     is_valid = False
        # else:
        #     if cmds.objExists(gt_blends_to_attr_settings.get('ik_handle')):
        #         is_valid = True
        #     else:
        #         cmds.warning('"' + str(gt_blends_to_attr_settings.get('ik_handle')) +
        #                      "\" couldn't be located. "
        #                      "Make sure you didn't rename or deleted the object after loading it")
        #
        # # Attribute Holder
        # if is_valid:
        #     if gt_blends_to_attr_settings.get('attr_holder') != '':
        #         if cmds.objExists(gt_blends_to_attr_settings.get('attr_holder')):
        #             attr_holder = gt_blends_to_attr_settings.get('attr_holder')
        #         else:
        #             cmds.warning('"' + str(gt_blends_to_attr_settings.get('attr_holder')) +
        #                          "\" couldn't be located. "
        #                          "Make sure you didn't rename or deleted the object after loading it. "
        #                          "A simpler version of the stretchy system was created.")
        #     else:
        #         sys.stdout.write(
        #             'An attribute holder was not provided. A simpler version of the stretchy system was created.')
        #
        # # Run Script
        # if is_valid:
        #     if stretchy_name:
        #         make_stretchy_ik(gt_blends_to_attr_settings.get('ik_handle'), stretchy_name=stretchy_name,
        #                          attribute_holder=attr_holder)
        #     else:
        #         make_stretchy_ik(gt_blends_to_attr_settings.get('ik_handle'), stretchy_name='temp',
        #                          attribute_holder=attr_holder)

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

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    cmds.separator(h=5, style='none')  # Empty Space
    #
    # cmds.text('Text Here:')
    # stretchy_system_prefix = cmds.textField(text='', pht='Text Here (Optional)')

    # cmds.separator(h=10, style='none')  # Empty Space
    cmds.text('1. Deformed Mesh (Source):')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 129), (2, 130)], cs=[(1, 10)], p=content_main)
    cmds.button(l="Load Morphing Object", c=lambda x: object_load_handler("blend_mesh"), w=130)
    source_object_status = cmds.button(l="Not loaded yet", bgc=(.2, .2, .2), w=130,
                                   c=lambda x: select_existing_object(gt_blends_to_attr_settings.get('blend_mesh')))

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Blend Shape Nodes:', font="smallPlainLabelFont")
    blend_nodes_scroll_list = cmds.textScrollList(numberOfRows=8, allowMultiSelection=False, height=70,
                                                  selectCommand=select_blend_shape_node)

    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('2. Attribute Holder (Target):')
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 129), (2, 130)], cs=[(1, 10)], p=content_main)

    cmds.button(l="Load Attribute Holder", c=lambda x: object_load_handler("attr_holder"), w=130)
    attr_holder_status = cmds.button(l="Not loaded yet", bgc=(.2, .2, .2), w=130,
                                     c=lambda x: select_existing_object(
                                         gt_blends_to_attr_settings.get('attr_holder')))

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
    build_gui_morphing_attributes()
