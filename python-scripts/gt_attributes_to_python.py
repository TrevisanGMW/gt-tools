"""
 GT Attributes to Python
 github.com/TrevisanGMW/gt-tools - 2021-12-01

 0.0.2 - 2022-03-31
 Re-created script after losing it to hard drive corruption

 0.0.3 - 2022-04-19
 Added option to strip zeroes
 Added auto conversion of "-0"s into "0"s for clarity

 0.0.4 - 2022-07-22
 Added GUI
 Added logger

 0.0.5 - 2022-07-22
 Increased the size of the UI
 Added "Extract User-Defined Attributes" function

 1.0.0 - 2022-07-26
 Added save to shelf
 Updated help

 1.0.1 - 2022-10-06
 Added triple quote to string attributes

 TODO:
    Add options

"""
from maya import OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import maya.mel as mel
import logging
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

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_shape_extract_state")
logger.setLevel(logging.INFO)

# Script Name
script_name = 'GT Attributes to Python'

# Version:
script_version = "1.0.1"

DIMENSIONS = ['x', 'y', 'z']
DEFAULT_CHANNELS = ['t', 'r', 's']

# if __name__ == '__main__':
#     # default_attr_to_python(None, use_loop=True)
#     attr_to_list(None, separate_channels=False)


def attr_to_list(obj_list, printing=True, decimal_place=2, separate_channels=False, strip_zeroes=True):
    """
    Returns transforms as list
    Args:
        obj_list (list, none): List objects to extract the transform from (if empty, it will try to use selection)
        printing (optional, bool): If active, the function will print the values to the script editor
        decimal_place (optional, int): How precise you want the extracted values to be (formats the float it gets)
        separate_channels (optional, bool): If separating channels, it will return T, R and S as different lists
        strip_zeroes (optional, bool): If active, it will remove unnecessary zeroes (e.g. 0.0 -> 0)

    Returns:
        A list with transform values. [TX, TY, TZ, RX, RY, RZ, SX, SY, SZ]
        For example: attr_list = [0, 0, 0, 15, 15, 15, 1, 1, 1] # TRS (XYZ)

    """
    if not obj_list:
        obj_list = cmds.ls(selection=True)
    if not obj_list:
        return

    output = ''
    if printing:
        output += ('#' * 80)

    for obj in obj_list:
        output += '\n# Transform Data for "' + obj + '":\n'
        data = []
        for channel in DEFAULT_CHANNELS:  # TRS
            for dimension in DIMENSIONS:  # XYZ
                value = cmds.getAttr(obj + '.' + channel + dimension)
                if strip_zeroes:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f"))).rstrip('0').rstrip('.')
                    if formatted_value == '-0':
                        formatted_value = '0'
                    data.append(formatted_value)
                else:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f")))
                    if formatted_value == '-0.0':
                        formatted_value = '0.0'
                    data.append(formatted_value)

        if not separate_channels:
            output += 'object = "' + str(obj) + '"\n'
            output += 'trs_attr_list = ' + str(data).replace("'", "") + '\n'
        else:
            output += 'object = "' + str(obj) + '"\n'
            output += 't_attr_list = [' + str(data[0]) + ', ' + str(data[1]) + ', ' + str(data[2]) + ']\n'
            output += 'r_attr_list = [' + str(data[3]) + ', ' + str(data[4]) + ', ' + str(data[5]) + ']\n'
            output += 's_attr_list = [' + str(data[6]) + ', ' + str(data[7]) + ', ' + str(data[8]) + ']\n'

    # Return / Print
    if printing:
        output += ('#' * 80)
        if output.replace('#', ''):
            print(output)
            return output
        else:
            print('No data found. Make sure your selection at least one object with unlocked transforms.')
            return None
    else:
        return output


def default_attr_to_python(obj_list, printing=True, use_loop=False, decimal_place=2, strip_zeroes=True):
    """
    Returns a string
    Args:
        obj_list (list, none): List objects to extract the transform from (if empty, it will try to use selection)
        printing (optional, bool): If active, the function will print the values to the script editor
        use_loop (optional, bool): If active, it will use a for loop in the output code (instead of simple lines)
        decimal_place (optional, int): How precise you want the extracted values to be (formats the float it gets)
        strip_zeroes (optional, bool): If active, it will remove unnecessary zeroes (e.g. 0.0 -> 0)

    Returns:
        Python code with extracted transform values

    """
    if not obj_list:
        obj_list = cmds.ls(selection=True)
    if not obj_list:
        return

    output = ''
    if printing:
        output += ('#' * 80)

    for obj in obj_list:
        output += '\n# Transform Data for "' + obj + '":\n'
        data = {}
        for channel in DEFAULT_CHANNELS:  # TRS
            for dimension in DIMENSIONS:  # XYZ
                # Extract Values
                value = cmds.getAttr(obj + '.' + channel + dimension)
                if strip_zeroes:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f"))).rstrip('0').rstrip(
                        '.')
                    if formatted_value == '-0':
                        formatted_value = '0'
                else:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f")))
                    if formatted_value == '-0.0':
                        formatted_value = '0.0'
                    output += formatted_value + ')\n'
                # Populate Value Messages/Data
                if not cmds.getAttr(obj + '.' + channel + dimension, lock=True) and not use_loop:
                    output += 'cmds.setAttr("' + obj + '.' + channel + dimension + '", '
                    # Populate Non-loop output
                    output += formatted_value + ')\n'
                else:
                    data[channel + dimension] = formatted_value

        # Loop Version
        if use_loop:
            output += 'for key, value in ' + str(data) + '.items():\n'
            output += '\tif not cmds.getAttr(' + obj + '. + key, lock=True):\n'
            output += '\t\tcmds.setAttr("' + obj + '." + key, value)\n'

    # Return / Print
    if printing:
        output += ('#' * 80)
        if output.replace('#', ''):
            print(output)
            return output
        else:
            print('No data found. Make sure your selection at least one object with unlocked transforms.')
            return None
    else:
        return output


def user_attr_to_python(obj_list, printing=True):
    """
    Returns a string
    Args:
        obj_list (list, none): List objects to extract the transform from (if empty, it will try to use selection)
        printing (optional, bool): If active, the function will print the values to the script editor

    Returns:
        Python code with extracted transform values

    """
    if not obj_list:
        obj_list = cmds.ls(selection=True)
    if not obj_list:
        return

    output = ''
    if printing:
        output += ('#' * 80)

    for obj in obj_list:
        output += '\n# User-Defined Attribute Data for "' + obj + '":\n'
        attributes = cmds.listAttr(obj, userDefined=True) or []
        if not attributes:
            output += '# No user-defined attributes found on this object.\n'
        else:
            for attr in attributes:  # TRS
                # not cmds.getAttr(obj + '.' + attr, lock=True) # TODO Check if locked
                attr_type = cmds.getAttr(obj + '.' + attr, typ=True)
                value = cmds.getAttr(obj + '.' + attr)
                if attr_type == 'double3':
                    pass
                elif attr_type == 'string':
                    output += 'cmds.setAttr("' + obj + '.' + attr + '", """' + str(value) + '""", typ="string")\n'
                else:
                    output += 'cmds.setAttr("' + obj + '.' + attr + '", ' + str(value) + ')\n'

    # Return / Print
    if printing:
        output += ('#' * 80)
        if output.replace('#', ''):
            print(output)
            return output
        else:
            print('No data found. Make sure your selection at least one object with user-defined attributes.')
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
def build_gui_attr_to_python():
    window_name = "build_gui_attr_to_python"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    # Main GUI Start Here =================================================================================
    window_gui_attr_to_python = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
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
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_attr_to_python())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 500)], cs=[(1, 10)], p=content_main)

    default_attr_button_cw = 243
    cmds.rowColumnLayout(nc=2, cw=[(1, default_attr_button_cw), (2, default_attr_button_cw)],
                         cs=[(1, 10), (2, 5)], p=content_main)

    cmds.button(l="Extract Default Attributes to \"setAttr\"", bgc=(.6, .6, .6),
                c=lambda x: _btn_extract_attr(attr_type='default'))
    cmds.button(l="Extract Default Attributes to List", bgc=(.6, .6, .6),
                c=lambda x: _btn_extract_attr(attr_type='list'))
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 490)], cs=[(1, 10)], p=content_main)
    cmds.button(l="Extract User-Defined Attributes", bgc=(.6, .6, .6),
                c=lambda x: _btn_extract_attr(attr_type='user'))
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space
    cmds.separator(h=10, p=content_main)

    # Bottom ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 490)], cs=[(1, 10)], p=content_main)
    cmds.text(label='Output Python Code')
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
                                label='setAttr',
                                tooltip='Extracted Attributes',
                                image="editRenderPass.png",
                                label_color=(0, .84, .81))
            cmds.inViewMessage(amg='<span style=\"color:#FFFF00;\">Python Output Command'
                                   '</span> was added as a button to your current shelf.',
                               pos='botLeft', fade=True, alpha=.9)
        else:
            cmds.warning('Unable to save to shelf. "Output Python Code" is empty.')

    def _btn_extract_attr(attr_type='default'):
        selection = cmds.ls(selection=True) or []

        if len(selection) == 0:
            cmds.warning('Make sure you selected at least one object and try again.')
            return

        if attr_type == 'list':
            output_python_command = attr_to_list(selection, printing=False, decimal_place=2,
                                                 separate_channels=False, strip_zeroes=True)
        elif attr_type == 'user':
            output_python_command = user_attr_to_python(selection, printing=False)
        else:
            output_python_command = default_attr_to_python(selection, printing=False, use_loop=False,
                                                           decimal_place=2, strip_zeroes=True)
        if len(output_python_command) == 0:
            cmds.warning('Make sure you selected at least one object and try again.')
            return

        if output_python_command.startswith('\n'):
            output_python_command = output_python_command[1:]

        print(output_python_command)
        if len(selection) == 1:
            sys.stdout.write('Attributes for "' + str(selection[0] + '" extracted. '
                                                                     '(Output to Script Editor and GUI)'))
        else:
            sys.stdout.write('Attributes extracted for ' + str(len(selection)) + ' objects. '
                                                                                 '(Output to Script Editor and GUI)')
        cmds.scrollField(output_python, e=True, ip=1, it='')  # Bring Back to the Top
        cmds.scrollField(output_python, edit=True, wordWrap=True, text='', sl=True)
        cmds.scrollField(output_python, edit=True, wordWrap=True, text=output_python_command, sl=True)
        cmds.setFocus(output_python)

    # Show and Lock Window
    cmds.showWindow(window_gui_attr_to_python)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/attributes.png')
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


# Creates Help GUI
def build_gui_help_attr_to_python():
    window_name = "build_gui_help_attr_to_python"
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
    cmds.text(l='"Extract Default Attributes to \"setAttr\"" button:', align="left", fn="boldLabelFont")
    cmds.text(l='Outputs the python code necessary to set the TRS \n(Translate, Rotate, and Scale) attributes '
                'back to their\ncurrent value.', align="left")
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='Run Code:', align="left", fn="boldLabelFont")
    cmds.text(l='Attempts to run the code (or anything written) inside ', align="left")
    cmds.text(l='"Output Python Curve" box', align="left")
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='Save to Shelf:', align="left", fn="boldLabelFont")
    cmds.text(l='Creates a shelf button with the code (or anything written) inside ', align="left")
    cmds.text(l='"Output Python Code" box', align="left")
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
    build_gui_attr_to_python()
