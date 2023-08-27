"""
 Inbetween Generator -> Simple script used to create Inbetween Transforms
 github.com/TrevisanGMW/gt-tools -  2020-02-04
"""
from maya import OpenMayaUI as OpenMayaUI
from PySide2.QtWidgets import QWidget
from shiboken2 import wrapInstance
from PySide2.QtGui import QIcon
import maya.cmds as cmds

# Script Name
script_name = "GT - Add Offset Transform"

# Version
script_version = "?.?.?"  # Module version (init)

# Settings
settings = {'outliner_color': [.5, 1, .4]}


# Main Form ============================================================================
def build_gui_add_offset_transform():
    window_name = "build_gui_add_offset_transform"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

        # Main GUI Start Here =================================================================================

    # Build UI
    window_gui_generate_inbetween = cmds.window(window_name, title=script_name + "  (v" + script_version + ')',
                                                titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 330)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 260), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_offset_transform())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 320)], cs=[(1, 10)], p=content_main)

    cmds.separator(h=15, p=body_column)

    mid_container = cmds.rowColumnLayout(p=body_column, numberOfRows=1, h=25)
    transform_type = cmds.optionMenu(p=mid_container, label='  Layer Type')
    cmds.menuItem(label='Group')
    cmds.menuItem(label='Joint')
    cmds.menuItem(label='Locator')

    transform_parent_type = cmds.optionMenu(p=mid_container, label='  Parent Type')
    cmds.menuItem(label='Selection')
    cmds.menuItem(label='Parent')
    cmds.text("  ", p=mid_container)

    cmds.separator(h=10, style='none', p=body_column)  # Empty Space
    cmds.rowColumnLayout(p=body_column, numberOfRows=1, h=25)
    color_slider = cmds.colorSliderGrp(label='Outliner Color  ', rgb=(settings.get("outliner_color")[0],
                                                                      settings.get("outliner_color")[1],
                                                                      settings.get("outliner_color")[2]),
                                       columnWidth=((1, 85), (3, 130)), cc=lambda x: update_stored_values())

    cmds.separator(h=15, p=body_column)
    bottom_container = cmds.rowColumnLayout(p=body_column, adj=True)
    cmds.text('New Transform Suffix:', p=bottom_container)
    desired_tag = cmds.textField(p=bottom_container, text="_offset", enterCommand=lambda x: create_inbetween(
        parse_text_field(cmds.textField(desired_tag, q=True, text=True))[0],
        cmds.optionMenu(transform_parent_type, q=True, value=True),
        cmds.optionMenu(transform_type, q=True, value=True)))
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.button(l="Generate", bgc=(.6, .6, .6),
                c=lambda x: create_inbetween(parse_text_field(cmds.textField(desired_tag, q=True, text=True))[0],
                                             cmds.optionMenu(transform_parent_type, q=True, value=True),
                                             cmds.optionMenu(transform_type, q=True, value=True)))
    cmds.separator(h=10, style='none')  # Empty Space

    # Updates Stored Values
    def update_stored_values():
        settings["outliner_color"] = cmds.colorSliderGrp(color_slider, q=True, rgb=True)
        # print(settings.get("outliner_color")) Debugging

    # Show and Lock Window
    cmds.showWindow(window_gui_generate_inbetween)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/hsGraphMaterial.png')
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


# Creates Help GUI
def build_gui_help_offset_transform():
    window_name = "build_gui_help_generate_inbetween"
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
    cmds.text(l='This script creates a inbetween transform for the selected', align="left")
    cmds.text(l='elements', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Layer Type:', align="left", fn="boldLabelFont")
    cmds.text(l='This pull-down menu determines what type object will', align="left")
    cmds.text(l='be created.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Parent Type:', align="left", fn="boldLabelFont")
    cmds.text(l='This pull-down menu determines where the pivot point', align="left")
    cmds.text(l='of the generated element will be extracted from.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Outliner Color:', align="left", fn="boldLabelFont")
    cmds.text(l='Determines the outliner color of the generated element.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='New Transform Suffix:', align="left", fn="boldLabelFont")
    cmds.text(l='Determines the suffix to be added to generated', align="left")
    cmds.text(l='transforms.', align="left")
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
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


# Main Function
# layer_tag = string to use as tag
# parent_type = parent, or selection (determines the pivot)
# layer_type = joint, locator or group(also nothing) : inbetween type
def create_inbetween(layer_tag, parent_type, layer_type):
    selection = cmds.ls(selection=True)

    for obj in selection:
        cmds.select(clear=True)
        inbetween_transform = ''
        if layer_type == "Joint":
            inbetween_transform = cmds.joint(name=(obj + layer_tag))
        if layer_type == "Locator":
            inbetween_transform = cmds.spaceLocator(name=(obj + layer_tag))[0]
        if layer_type == "Group":
            inbetween_transform = cmds.group(name=(obj + layer_tag), empty=True)

        cmds.setAttr(inbetween_transform + ".useOutlinerColor", True)
        cmds.setAttr(inbetween_transform + ".outlinerColor", settings.get("outliner_color")[0],
                     settings.get("outliner_color")[1], settings.get("outliner_color")[2])
        selection_parent = cmds.listRelatives(obj, parent=True) or []

        if len(selection_parent) != 0 and parent_type == "Parent":
            constraint = cmds.parentConstraint(selection_parent[0], inbetween_transform)
            cmds.delete(constraint)
            cmds.parent(inbetween_transform, selection_parent[0])
            cmds.parent(obj, inbetween_transform)
        elif len(selection_parent) == 0 and parent_type == "Parent":
            cmds.parent(obj, inbetween_transform)

        if len(selection_parent) != 0 and parent_type == "Selection":
            constraint = cmds.parentConstraint(obj, inbetween_transform)
            cmds.delete(constraint)
            cmds.parent(inbetween_transform, selection_parent[0])
            cmds.parent(obj, inbetween_transform)
        elif len(selection_parent) == 0 and parent_type == "Selection":
            constraint = cmds.parentConstraint(obj, inbetween_transform)
            cmds.delete(constraint)
            cmds.parent(obj, inbetween_transform)


# Function to Parse textField data
def parse_text_field(text_field_data):
    text_field_data_no_spaces = text_field_data.replace(" ", "")
    if len(text_field_data_no_spaces) <= 0:
        return []
    else:
        return_list = text_field_data_no_spaces.split(",")
        empty_objects = []
        for obj in return_list:
            if '' == obj:
                empty_objects.append(obj)
        for obj in empty_objects:
            return_list.remove(obj)
        return return_list


# Run Script
if __name__ == '__main__':
    build_gui_add_offset_transform()
