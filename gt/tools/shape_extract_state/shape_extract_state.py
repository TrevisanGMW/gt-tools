"""
GT Extract Shape State - Outputs the python code containing the current shape data for the selected curves
github.com/TrevisanGMW/gt-tools - 2021-10-01
"""
from maya import OpenMayaUI as OpenMayaUI
from PySide2.QtWidgets import QWidget
from shiboken2 import wrapInstance
from gt.ui import resource_library
from PySide2.QtGui import QIcon
import maya.cmds as cmds
import maya.mel as mel
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_shape_extract_state")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT - Extract Shape State"

# Version
script_version = "?.?.?"  # Module version (init)


def extract_python_curve_shape(curve_transforms, printing=False):
    """
    Extracts the Python code necessary to reshape
    Args:
        curve_transforms (list of strings): Transforms carrying curve shapes inside them (nurbs or bezier)
        printing: Whether to print the extracted python code. If False it will only return the code.

    Returns:
        python_string (string): Python code with the current state of the selected curves (their shape)

    """
    output = ''
    if printing:
        output += ('#' * 80)
    for crv in curve_transforms:
        valid_types = ['nurbsCurve', 'bezierCurve']
        accepted_shapes = []
        curve_shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
        # Filter valid shapes:
        for shape in curve_shapes:
            current_shape_type = cmds.objectType(shape)
            if current_shape_type in valid_types:
                accepted_shapes.append(shape)

        # Extract CVs into Python code:
        # print(accepted_shapes)
        for shape in accepted_shapes:
            curve_data = zip(cmds.ls('%s.cv[*]' % shape, flatten=True), cmds.getAttr(shape + '.cv[*]'))
            curve_data_list = list(curve_data)
            # Assemble command:
            if curve_data_list:
                output += '# Curve data for "' + str(shape).split('|')[-1] + '":\n'
                output += 'for cv in ' + str(curve_data_list) + ':\n'
                output += '    cmds.xform(cv[0], os=True, t=cv[1])\n\n\n'

    if output.endswith('\n\n\n'):  # Removes unnecessary spaces at the end
        output = output[:-2]

    # Return / Print
    if printing:
        output += ('#' * 80)
        if output.replace('#', ''):
            print(output)
            return output
        else:
            print('No data found. Make sure your selection contains nurbs or bezier curves.')
            return None
    else:
        return output


# Function for the "Run Code" button
def run_output_code(out):
    try:
        exec(out)
    except Exception as e:
        cmds.warning("Something is wrong with your code!")
        cmds.warning(e)


# Main Form ============================================================================
def build_gui_curve_shape_state():
    window_name = "build_gui_curve_shape_state"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    # Main GUI Start Here =================================================================================
    window_gui_curve_shape_state = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                               titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 500)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 430), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_curve_shape_state())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 500)], cs=[(1, 10)], p=content_main)
    cmds.rowColumnLayout(nc=1, cw=[(1, 490)], cs=[(1, 0)])
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.button(l="Extract State", bgc=(.6, .6, .6), c=lambda x: _btn_extract_python_curve_shape())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space
    cmds.separator(h=10, p=content_main)

    # Bottom ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 490)], cs=[(1, 10)], p=content_main)
    cmds.text(label='Output Python Curve')
    output_python = cmds.scrollField(editable=True, wordWrap=True, height=200)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 235), (2, 235)], cs=[(1, 15), (2, 15)], p=content_main)
    cmds.button(l="Run Code", c=lambda x: run_output_code(cmds.scrollField(output_python, query=True, text=True)))
    cmds.button(l="Save to Shelf", c=lambda x: _btn_add_to_shelf())
    cmds.separator(h=10, style='none')  # Empty Space

    def _btn_add_to_shelf():
        command = cmds.scrollField(output_python, query=True, text=True) or ''
        if command:
            create_shelf_button(command,
                                label='setCrv',
                                tooltip='Extracted Curve State',
                                image="editRenderPass.png",
                                label_color=(0, .84, .81))
            cmds.inViewMessage(amg='<span style=\"color:#FFFF00;\">Python Output Curve'
                                   '</span> was added as a button to your current shelf.',
                               pos='botLeft', fade=True, alpha=.9)
        else:
            cmds.warning('Unable to save to shelf. "Output Python Curve" is empty.')

    def _btn_extract_python_curve_shape():
        selection = cmds.ls(selection=True) or []

        if len(selection) == 0:
            cmds.warning('Make sure you selected at least one curve and try again.')
            return

        output_python_command = extract_python_curve_shape(selection, False)
        output_python_print = extract_python_curve_shape(selection, True)
        if len(output_python_command) == 0:
            cmds.warning('Make sure you selected at least one curve and try again.')
            return

        print(output_python_print)
        if len(selection) == 1:
            sys.stdout.write('Curve shape state for "' + str(selection[0] + '" extracted. '
                                                                            '(Output to Script Editor and GUI)'))
        else:
            sys.stdout.write('Curve shape state for ' + str(len(selection)) + ' curves extracted. '
                                                                              '(Output to Script Editor and GUI)')
        cmds.scrollField(output_python, e=True, ip=1, it='')  # Bring Back to the Top
        cmds.scrollField(output_python, edit=True, wordWrap=True, text='', sl=True)
        cmds.scrollField(output_python, edit=True, wordWrap=True, text=output_python_command, sl=True)
        cmds.setFocus(output_python)

    # Show and Lock Window
    cmds.showWindow(window_gui_curve_shape_state)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(resource_library.Icon.crv_state)
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


# Creates Help GUI
def build_gui_help_curve_shape_state():
    window_name = "build_gui_help_curve_shape_state"
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
    cmds.text(l='This script generates the Python code necessary to recreate\na curve shape state', align="left")
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='"Extract State" button:', align="left", fn="boldLabelFont")
    cmds.text(l='Outputs the python code necessary to recreate the current', align="left")
    cmds.text(l='curve shape state inside the "Output Python Curve" box.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Run Code:', align="left", fn="boldLabelFont")
    cmds.text(l='Attempts to run the code (or anything written) inside ', align="left")
    cmds.text(l='"Output Python Curve" box', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Save to Shelf:', align="left", fn="boldLabelFont")
    cmds.text(l='Saves to shelf as a button the code (or anything written) inside ', align="left")
    cmds.text(l='"Output Python Curve" box', align="left")
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


def create_shelf_button(command,
                        label='',
                        tooltip='',
                        image=None,  # Default Python Icon
                        label_color=(1, 0, 0),  # Default Red
                        label_bgc_color=(0, 0, 0, 1),  # Default Black
                        bgc_color=None
                        ):
    """
    Add a shelf button to the current shelf (according to the provided parameters)

    Args:
        command (str): A string containing the code or command you want the button to run when clicking on it.
                       e.g. "print("Hello World")"
        label (str): The label of the button. This is the text you see below it.
        tooltip (str): The help message you get when hovering the button.
        image (str): The image used for the button (defaults to Python icon if none)
        label_color (tuple): A tuple containing three floats,
                             these are RGB 0 to 1 values to determine the color of the label.
        label_bgc_color (tuple): A tuple containing four floats,
                                 these are RGBA 0 to 1 values to determine the background of the label.
        bgc_color (tuple): A tuple containing three floats,
                           these are RGB 0 to 1 values to determine the background of the icon

    """
    maya_version = int(cmds.about(v=True))

    shelf_top_level = mel.eval('$temp=$gShelfTopLevel')
    if not cmds.tabLayout(shelf_top_level, exists=True):
        cmds.warning('Shelf is not visible')
        return

    if not image:
        image = 'pythonFamily.png'

    shelf_tab = cmds.shelfTabLayout(shelf_top_level, query=True, selectTab=True)
    shelf_tab = shelf_top_level + '|' + shelf_tab

    # Populate extra arguments according to the current Maya version
    kwargs = {}
    if maya_version >= 2009:
        kwargs['commandRepeatable'] = True
    if maya_version >= 2011:
        kwargs['overlayLabelColor'] = label_color
        kwargs['overlayLabelBackColor'] = label_bgc_color
        if bgc_color:
            kwargs['enableBackground'] = bool(bgc_color)
            kwargs['backgroundColor'] = bgc_color

    return cmds.shelfButton(parent=shelf_tab, label=label, command=command,
                            imageOverlayLabel=label, image=image, annotation=tooltip,
                            width=32, height=32, align='center', **kwargs)


if __name__ == '__main__':
    build_gui_curve_shape_state()
