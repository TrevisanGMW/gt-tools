"""
GT Extract Bound Joints - Extract or Transfer bound joints
github.com/TrevisanGMW/gt-tools - 2022-06-22

0.0.1 - 2022-06-22
Core function

0.0.2 - 2022-07-14
Added GUI

0.0.3 - 2022-07-20
Added skinCluster check

1.0.0 - 2022-07-20
Added Filter non-existent and include mesh checkboxes

1.0.1 - 2022-07-20
Updated help menu

1.0.2 - 2022-07-22
Increased the size of the output window

1.1.0 - 2022-07-26
Added "Save to Shelf" button
Added "Extract Bound Joints to Selection Sets" button

Todo:
    Add Transfer functions
    Add save as set button
    Add save to shelf
"""
from maya import OpenMayaUI as OpenMayaUI
import maya.cmds as cmds
import maya.mel as mel
import logging

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
logger = logging.getLogger("gt_extract_bound_joints")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT - Extract Bound Joints"

# Version
script_version = "1.1.0"

# Settings
extract_joints_settings = {'filter_non_existent': True,
                           'include_mesh': True,
                           }


# Function for the "Run Code" button
def run_output_code(out):
    try:
        exec(out)
    except Exception as e:
        cmds.warning("Something is wrong with your code!")
        cmds.warning(e)


# Main Window ============================================================================
def build_gui_extract_bound_joints():
    window_name = "build_gui_extract_bound_joints"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

    # Main GUI Start Here =================================================================================
    window_gui_extract_bound_joints = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                                  titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 500)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 425), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_extract_bound_joints())
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 500)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 200)], cs=[(1, 70), (2, 15)])
    filter_non_existent_chk = cmds.checkBox("Include Non-Existent Filter", value=True,
                                            cc=lambda x: _btn_update_settings())
    include_mesh_chk = cmds.checkBox("Include Bound Mesh", value=True, cc=lambda x: _btn_update_settings())
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 235), (2, 235)], cs=[(1, 15), (2, 10)], p=content_main)
    cmds.button(l="Extract Bound Joints to Python", bgc=(.6, .6, .6),
                c=lambda x: _btn_extract_bound_validation('python'))
    cmds.button(l="Extract Bound Joints to Selection Sets", bgc=(.6, .6, .6),
                c=lambda x: _btn_extract_bound_validation('set'))
    cmds.separator(h=10, style='none', p=content_main)  # Empty Space
    cmds.separator(h=10, p=content_main)

    # Bottom ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 490)], cs=[(1, 10)], p=content_main)
    cmds.text(label='Output - Selection Command:')
    output_python = cmds.scrollField(editable=True, wordWrap=True, height=200)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 235), (2, 235)], cs=[(1, 15), (2, 15)], p=content_main)
    cmds.button(l="Run Code", c=lambda x: run_output_code(cmds.scrollField(output_python, query=True, text=True)))
    cmds.button(l="Save to Shelf", c=lambda x: _btn_add_to_shelf())
    cmds.separator(h=10, style='none')  # Empty Space

    def _btn_update_settings():
        extract_joints_settings['filter_non_existent'] = cmds.checkBox(filter_non_existent_chk, q=True, value=True)
        extract_joints_settings['include_mesh'] = cmds.checkBox(include_mesh_chk, q=True, value=True)

    def _btn_add_to_shelf():
        command = cmds.scrollField(output_python, query=True, text=True) or ''
        if command:
            create_shelf_button(command,
                                label='bJnts',
                                tooltip='Extracted joints',
                                image="smoothSkin.png",  # Default Python Icon
                                label_color=(.97, 0, 1.7),  # Default Red
                                label_bgc_color=(0, 0, 0, 1),  # Default Black
                                )
            cmds.inViewMessage(amg='<span style=\"color:#FFFF00;\">Current Selection Command'
                                   '</span> was added as a button to your current shelf.',
                               pos='botLeft', fade=True, alpha=.9)
        else:
            cmds.warning('Unable to save to shelf. "Output- Selection Command" is empty.')

    def _btn_extract_bound_validation(operation_target='python'):
        """
        Validation before extracting python or set out of the bound mesh
        Args:
            operation_target (optional, string): "python" will output python code into the scrollField,
                                                 "set" will create selection sets

        """
        selection = cmds.ls(selection=True) or []

        if len(selection) == 0:
            cmds.warning('Nothing selected. Please select a bound mesh and try again.')
            return

        valid_nodes = []
        for sel in selection:
            shapes = cmds.listRelatives(sel, shapes=True, children=False) or []
            if shapes:
                if cmds.objectType(shapes[0]) == 'mesh' or cmds.objectType(shapes[0]) == 'nurbsSurface':
                    valid_nodes.append(sel)

        if operation_target == 'python':
            commands = []
            for transform in valid_nodes:
                message = '# Joint influences found in "' + transform + '":'
                message += '\nbound_list = '
                bound_joints = get_bound_joints(transform)

                if not bound_joints:
                    cmds.warning('Unable to find skinCluster for "' + transform + '".')
                    return

                if extract_joints_settings.get('include_mesh'):
                    bound_joints.insert(0, transform)

                message += str(bound_joints)

                if extract_joints_settings.get('filter_non_existent'):
                    message += '\nbound_list = [jnt for jnt in bound_list if cmds.objExists(jnt)]'

                message += '\ncmds.select(bound_list)'

                commands.append(message)

            cmds.scrollField(output_python, edit=True, wordWrap=True, text='', sl=True)
            command = ''
            for cmd in commands:
                command += cmd + '\n\n'

            print('#' * 80)
            print(command)
            print('#' * 80)

            cmds.scrollField(output_python, edit=True, wordWrap=True, text=command, sl=True)
            cmds.scrollField(output_python, e=True, ip=1, it='')  # Bring Back to the Top
            cmds.setFocus(output_python)

        if operation_target == 'set':
            for transform in valid_nodes:
                bound_joints = get_bound_joints(transform)
                if extract_joints_settings.get('include_mesh'):
                    bound_joints.insert(0, transform)
                new_set = cmds.sets(name=transform + "_jointSet", empty=True)
                for jnt in bound_joints:
                    cmds.sets(jnt, add=new_set)

    # Show and Lock Window
    cmds.showWindow(window_gui_extract_bound_joints)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/smoothSkin.png')
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


# Creates Help GUI
def build_gui_help_extract_bound_joints():
    window_name = "build_gui_help_extract_bound_joints"
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
    cmds.text(l='This script generates the Python code necessary to select\nall joints influencing a skinCluster node',
              align="left")
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='Include Non-Existent Filter:', align="left", fn="boldLabelFont")
    cmds.text(l='Adds a line of code that ignores objects not found in the scene.\n', align="left")
    cmds.text(l='Include Bound Mesh:', align="left", fn="boldLabelFont")
    cmds.text(l='Determines if the selected bound mesh will be included in the\nextracted list.\n', align="left")
    cmds.text(l='"Extract Bound Joints" button:', align="left", fn="boldLabelFont")
    cmds.text(l='Outputs the python code necessary to reselect the joints', align="left")
    cmds.text(l='inside the "Output Python Curve" box.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Run Code:', align="left", fn="boldLabelFont")
    cmds.text(l='Attempts to run the code (or anything written) inside ', align="left")
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


def get_bound_joints(obj):
    """
    Gets a list of joints bound to the skin cluster of the object
    Args:
        obj: Name of the object to extract joints from (must contain a skinCluster node)

    Returns:
        joints (list): List of joints bound to this object
    """
    if not cmds.objExists(obj):
        logger.warning('Object "' + obj + '" was not found in the scene.')
        return

    history = cmds.listHistory(obj) or []
    skin_clusters = cmds.ls(history, type='skinCluster') or []

    if len(skin_clusters) != 0:
        skin_cluster = skin_clusters[0]
    else:
        logger.debug('history: ', str(history))
        logger.debug('skin_clusters: ', str(skin_clusters))
        logger.warning('Object "' + obj + "\" doesn't seem to be bound to any joints.")
        return

    connections = cmds.listConnections(skin_cluster + '.influenceColor') or []
    joints = []
    for obj in connections:
        if cmds.objectType(obj) == 'joint':
            joints.append(obj)
    return joints


def create_shelf_button(command,
                        label='',
                        name=None,
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
        name (str): The name of the button as seen inside the shelf editor.
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
    build_gui_extract_bound_joints()
