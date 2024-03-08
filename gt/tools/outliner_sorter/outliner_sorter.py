"""
 GT Outliner Manager - General Outliner organization script
 github.com/TrevisanGMW/gt-tools - 2022-08-18
"""
from gt.utils.outliner_utils import reorder_up, reorder_down, reorder_front, reorder_back, outliner_sort
from gt.utils.outliner_utils import OutlinerSortOptions
from gt.utils.request_utils import open_package_docs_url_in_browser
from maya import OpenMayaUI as OpenMayaUI
from PySide2.QtWidgets import QWidget
from gt.ui import resource_library
from shiboken2 import wrapInstance
from PySide2.QtGui import QIcon
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_outliner_sorter")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT - Outliner Sorter"

# Version:
script_version = "?.?.?"  # Module version (init)


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
            is_ascending = True
            if 'Descending' in cmds.optionMenu(ascending_option_menu, q=True, value=True):
                is_ascending = False

            if operation == 'reorder_up':
                reorder_up(current_selection)
            elif operation == 'reorder_down':
                reorder_down(current_selection)
            elif operation == 'reorder_front':
                reorder_front(current_selection)
            elif operation == 'reorder_back':
                reorder_back(current_selection)
            elif operation == 'sort_attribute':
                current_attr = cmds.textField(custom_attr_textfield, q=True, text=True) or ''
                if current_attr.startswith('.'):
                    current_attr = current_attr[1:]
                outliner_sort(current_selection, operation=OutlinerSortOptions.ATTRIBUTE,
                              attr=current_attr, is_ascending=is_ascending)
            elif operation == 'sort_name':
                outliner_sort(current_selection, operation=OutlinerSortOptions.NAME, is_ascending=is_ascending)
            elif operation == 'shuffle':
                outliner_sort(current_selection, operation=OutlinerSortOptions.SHUFFLE)

        except Exception as e:
            logger.debug(str(e))

        finally:
            cmds.undoInfo(closeChunk=True, chunkName=script_name)

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
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: open_package_docs_url_in_browser())
    cmds.separator(h=5, style='none')  # Empty Space

    # 1. Deformed Mesh (Source) ------------------------------------------
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Sort Utilities / Settings:')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 130), (2, 130)], cs=[(1, 10), (2, 5)], p=content_main)
    cmds.button(l="Move Up", c=lambda x: validate_operation("reorder_up"), w=130)
    cmds.button(l="Move Front", c=lambda x: validate_operation("reorder_front"), w=130)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 130), (2, 130)], cs=[(1, 10), (2, 5)], p=content_main)
    cmds.button(l="Move Down", c=lambda x: validate_operation("reorder_down"), w=130)
    cmds.button(l="Move Back", c=lambda x: validate_operation("reorder_back"), w=130)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 130), (2, 130)], cs=[(1, 10), (2, 5)], p=content_main)
    cmds.button(l="Shuffle", c=lambda x: validate_operation("shuffle"))
    ascending_option_menu = cmds.optionMenu(label='')
    cmds.menuItem(label='    Sort Ascending')
    cmds.menuItem(label='    Sort Descending')

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    # Sort by Name ------------------------------------------
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.separator(h=5)
    cmds.rowColumnLayout(nc=1, cw=[(1, 265)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.button(l="Sort by Name", bgc=(.6, .6, .6), c=lambda x: validate_operation('sort_name'))
    # cmds.separator(h=10, style='none')  # Empty Space

    # Sort by Attribute ------------------------------------------
    cmds.rowColumnLayout(nc=1, cw=[(1, 265)], cs=[(1, 10), (2, 5)], p=content_main)
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.text("Sort by Attribute")
    cmds.separator(h=7, style='none')  # Empty Space

    def update_sort_attr(*args):
        menu_option = args[0].replace(' ', '')
        attr = menu_option[0].lower() + menu_option[1:]

        if attr == 'customAttribute':
            cmds.textField(custom_attr_textfield, e=True, en=True)
            cmds.textField(custom_attr_textfield, e=True, text='')
        else:
            cmds.textField(custom_attr_textfield, e=True, en=False)
            cmds.textField(custom_attr_textfield, e=True, text=attr)

    cmds.rowColumnLayout(nc=2, cw=[(1, 130), (2, 130)], cs=[(1, 10), (2, 5)], p=content_main)
    sort_attr_option = cmds.optionMenu(label='', cc=update_sort_attr)
    menu_items = ['Custom Attribute', '',
                  'Translate X', 'Translate Y', 'Translate Z', '',
                  'Rotate X', 'Rotate Y', 'Rotate Z',  '',
                  'Scale X', 'Scale Y', 'Scale Z', ]
    for item in menu_items:
        if item == '':
            cmds.menuItem(divider=True)
        else:
            cmds.menuItem(label=item)

    cmds.optionMenu(sort_attr_option, e=True, sl=4)
    custom_attr_textfield = cmds.textField(text='translateY', pht='Custom Attribute', en=False)
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 265)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=7, style='none')  # Empty Space

    cmds.button(l="Sort by Attribute", bgc=(.6, .6, .6), c=lambda x: validate_operation('sort_attribute'))
    cmds.separator(h=10, style='none')  # Empty Space

    # Show and Lock Window
    cmds.showWindow(window_gui_blends_to_attr)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(resource_library.Icon.tool_outliner_sorter)
    widget.setWindowIcon(icon)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_name)


if __name__ == '__main__':
    # logger.setLevel(logging.DEBUG)
    build_gui_outliner_sorter()
