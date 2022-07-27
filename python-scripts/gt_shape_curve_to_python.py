"""
 Python Curve Generator
 github.com/TrevisanGMW/gt-tools -  2020-01-02
 
 1.1 - 2020-01-03
 Minor patch adjustments to the script
 
 1.2 - 2020-06-07
 Fixed random window widthHeight issue.
 Updated naming convention to make it clearer. (PEP8)
 Added length checker for selection before running.
 
 1.3 - 2020-06-17
 Changed UI
 Added help menu
 Added icon
 
 1.4 - 2020-06-27
 No longer failing to generate curves with non-unique names
 Tweaked the color and text for the title and help menu
  
 1.5 - 2021-01-26
 Fixed way the curve is generated to account for closed and opened curves
 
 1.6 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.6.1 - 2022-07-14
 Added logger
 Added patch version
 PEP8 General cleanup

 1.6.2 - 2022-07-14
 Updated script name
 Increased the size of the output window
 Updated help

"""

import maya.cmds as cmds
import logging
from maya import OpenMayaUI as OpenMayaUI
from decimal import *

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
logger = logging.getLogger("gt_shape_curve_to_python")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT - Extract Python Curve"

# Version:
script_version = "1.6.2"

# Default Settings
close_curve = False
add_import = False


# Function for the "Run Code" button
def run_output_code(out):
    try:
        exec(out)
    except Exception as e:
        cmds.warning("Something is wrong with your code!")
        cmds.warning(e)


# Main Form ============================================================================
def build_gui_py_curve():
    window_name = "build_gui_py_curve"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

        # Main GUI Start Here =================================================================================

    window_gui_py_curve = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
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
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_py_curve())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 470)], cs=[(1, 10)], p=content_main)

    cmds.rowColumnLayout(nc=1, cw=[(1, 460)], cs=[(1, 70)])

    settings = cmds.checkBoxGrp(columnWidth2=[260, 1], numberOfCheckBoxes=2,
                                label1='Add import \"maya.cmds\" ', label2="Force Open", v1=add_import, v2=close_curve)

    cmds.rowColumnLayout(nc=1, cw=[(1, 490)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.button(l="Extract Curve to Python", bgc=(.6, .6, .6), c=lambda x: generate_python_curve())
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
                                label='Crv',
                                tooltip='Extracted curve',
                                image="curveBezier.png",
                                label_color=(0, 0.84, 0.81),
                                label_bgc_color=(0, 0, 0, 1),
                                )
            cmds.inViewMessage(amg='<span style=\"color:#FFFF00;\">Current Python Curve Command'
                                   '</span> was added as a button to your current shelf.',
                               pos='botLeft', fade=True, alpha=.9)
        else:
            cmds.warning('Unable to save to shelf. "Output Python Curve" is empty.')

    def generate_python_curve():

        not_curve_error = "Please make sure you selected a Nurbs Curve or a Bezier Curve object before generating it"

        if len(cmds.ls(selection=True)) != 0:
            getcontext().prec = 5

            sel_one = cmds.ls(sl=1)[0]

            shape = cmds.listRelatives(sel_one, s=1, fullPath=True)[0]
            type_checker = str(cmds.objectType(shape))

            if "nurbsCurve" in type_checker or "bezierCurve" in type_checker:

                opened_curve = cmds.checkBoxGrp(settings, q=True, value2=True)

                per_state = cmds.getAttr(shape + '.form')
                knots_string = ''
                extra_cvs_per = ''
                is_periodic = False

                if not opened_curve and per_state == 2:
                    is_periodic = True
                    curve_info = cmds.arclen(sel_one, ch=True)
                    curve_knots = cmds.getAttr(curve_info + '.knots[*]')
                    knots_string = ', per=True, k=' + str(curve_knots)
                    cmds.delete(curve_info)

                cvs = cmds.getAttr(shape + '.cv[*]')
                cvs_list = []

                for c in cvs:
                    cvs_list.append(
                        [float(Decimal("%.3f" % c[0])), float(Decimal("%.3f" % c[1])), float(Decimal("%.3f" % c[2]))])

                if is_periodic and len(cvs) > 2:
                    extra_cvs_per = ', '
                    for i in range(3):
                        if i != 2:
                            extra_cvs_per += str(cvs_list[i]) + ', '
                        else:
                            extra_cvs_per += str(cvs_list[i])

                if cmds.checkBoxGrp(settings, q=True, value1=True):
                    out = 'import maya.cmds as cmds\n\ncmds.curve(p='
                else:
                    out = 'cmds.curve(p='

                out += '[%s' % ', '.join(map(str, cvs_list))
                out += extra_cvs_per + '], d=' + str(cmds.getAttr(shape + '.degree')) + knots_string + ')'

                print("#" * 100)
                print(out)
                print("#" * 100)

                cmds.scrollField(output_python, edit=True, wordWrap=True, text=out, sl=True)
                cmds.setFocus(output_python)
            else:
                cmds.warning(not_curve_error)
                cmds.scrollField(output_python, edit=True, wordWrap=True, text=not_curve_error, sl=True)
                cmds.setFocus(output_python)
        else:
            cmds.warning(not_curve_error)

    # Show and Lock Window
    cmds.showWindow(window_gui_py_curve)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/pythonFamily.png')
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


# Creates Help GUI
def build_gui_help_py_curve():
    window_name = "build_gui_help_py_curve"
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
    cmds.text(l='This script generates the Python code necessary to create', align="left")
    cmds.text(l='a selected curve.', align="left")
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='Make sure you delete the curve\'s history before ', align="left")
    cmds.text(l='generating the code.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Add import "maya.cmds":', align="left", fn="boldLabelFont")
    cmds.text(l='Adds a line that imports Maya\'s API. This is necessary', align="left")
    cmds.text(l='when running python scripts.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Force Open: ', align="left", fn="boldLabelFont")
    cmds.text(l="Doesn't check if the curve is periodic leaving it open.", align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='"Generate" button:', align="left", fn="boldLabelFont")
    cmds.text(l='Outputs the python code necessary to create the curve', align="left")
    cmds.text(l='inside the "Output Python Curve" box.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Run Code:', align="left", fn="boldLabelFont")
    cmds.text(l='Attempts to run the code (or anything written) inside ', align="left")
    cmds.text(l='"Output Python Curve" box', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Save To Shelf:', align="left", fn="boldLabelFont")
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


# Build UI
if __name__ == '__main__':
    build_gui_py_curve()
