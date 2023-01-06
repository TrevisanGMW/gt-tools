"""
 GT Morphing Utilities
 github.com/TrevisanGMW/gt-tools - 2020-11-15

 0.0.1 to 0.0.2 - 2022-11-15
 Added "delete_blends_target"
 Added "delete_blends_targets"
 Added "delete_all_blend_targets"

 0.0.3 to 0.0.4 - 2022-12-23
 Created initial GUI
 Added search and replace
 Added window icon

 1.0.0 - 2022-12-23
 Initial release (basic utilities)

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
logger = logging.getLogger("gt_blend_utilities")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT - Blend Utilities"

# Version:
script_version = "1.0.0"

# Settings
morphing_util_settings = {'morphing_obj': '',
                          'blend_node': '',
                          'search_string': '',
                          'replace_string': '',
                          }


def delete_blends_targets(blend_node):
    """
    Delete all blend targets found in the provided blend shape node

    Args:
        blend_node (string) Name of the blend shape node

    Returns:
        number of removed targets
    """
    removed_num = 0
    cmds.select(d=True)  # Deselect
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True) or []
    if len(blendshape_names) == 0:
        return 0
    for i in range(len(blendshape_names)):
        cmds.removeMultiInstance(blend_node + ".weight[" + str(i) + "]", b=True)
        cmds.removeMultiInstance(blend_node + ".inputTarget[0].inputTargetGroup[" + str(i) + "]", b=True)
        removed_num += 1
    return removed_num


def delete_all_blend_targets():
    """
    Delete all blend shape targets (not the nodes, only the targets)

    Dependencies:
        delete_blends_targets()

    Returns
        removed_number: number of removed targets
    """
    removed_num = 0
    cmds.select(d=True)  # Deselect
    for blend_node in cmds.ls(typ="blendShape"):
        removed_num += delete_blends_targets(blend_node)
    return removed_num


def delete_blends_target(blend_node, target_name):
    """
    Deletes only the provided blend target
    Args:
        blend_node (string) Name of the blend shape node
        target_name (string) Name of the blend shape target to delete
    """
    cmds.select(d=True)  # Deselect
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True)

    for i in range(len(blendshape_names)):
        if blendshape_names[i] == target_name:
            cmds.removeMultiInstance(blend_node + ".weight[" + str(i) + "]", b=True)
            cmds.removeMultiInstance(blend_node + ".inputTarget[0].inputTargetGroup[" + str(i) + "]", b=True)


def delete_blend_nodes(obj):
    """
    Deletes any blend shape nodes found under the history of the provided object.

    Args:
        obj (String): name of the object. e.g. "pSphere1"
    """
    history = cmds.listHistory(obj)
    for node in history:
        if cmds.objectType(node) == "blendShape":
            cmds.delete(node)


def delete_all_blend_nodes():
    """
    Deletes all blend shape nodes in the scene

    Returns:
        number of deleted blend shape nodes
    """
    removed_num = 0
    for node in cmds.ls(typ="blendShape") or []:
        if cmds.objectType(node) == "blendShape":
            cmds.delete(node)
            removed_num += 1
    return removed_num


def rename_blend_target(blend_shape, target, new_name):
    """ Renames the provided blend shape target """
    cmds.aliasAttr(new_name, blend_shape + '.' + target)
    return new_name


def search_replace_blend_targets(blend_node, search_string, replace_string):
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True) or []
    pairs_to_rename = {}
    logger.debug("search_string:" + search_string)
    logger.debug("replace_string:" + replace_string)
    for i in range(len(blendshape_names)):
        blend = blendshape_names[i]
        if search_string in blend:
            pairs_to_rename[blend] = blend.replace(search_string, replace_string)

    number_operations = 0
    for key, value in pairs_to_rename.items():
        try:
            rename_blend_target(blend_node, key, value)
            number_operations += 1
        except Exception as exc:
            logger.debug(str(exc))
    return number_operations


def build_gui_morphing_utilities():
    def update_settings(*args):
        logger.debug(str(args))
        search_string = cmds.textField(desired_filter_textfield, q=True, text=True)
        replace_string = cmds.textField(undesired_filter_textfield, q=True, text=True)

        morphing_util_settings['search_string'] = search_string
        morphing_util_settings['replace_string'] = replace_string

        logger.debug('Updated Settings Called')
        logger.debug('search_string: ' + str(morphing_util_settings.get('search_string')))
        logger.debug('replace_string: ' + str(morphing_util_settings.get('replace_string')))
  
    def select_blend_shape_node():
        error_message = "Unable to locate blend shape node. Please try again."
        blend_node = cmds.textScrollList(blend_nodes_scroll_list, q=True, selectItem=True) or []
        if blend_node:
            if cmds.objExists(blend_node[0]):
                sys.stdout.write('"' + str(blend_node[0]) + '" will be used when executing utilities.\n')
                morphing_util_settings['blend_node'] = blend_node[0]
            else:
                cmds.warning(error_message)
                morphing_util_settings['blend_node'] = ''
        else:
            cmds.warning(error_message)
            morphing_util_settings['blend_node'] = ''

    def object_load_handler(operation):
        """
        Function to handle load buttons. It updates the UI to reflect the loaded data.

        Args:
            operation (str): String to determine function ("morphing_obj" or "attr_holder")
        """
        def failed_to_load_source(failed_message="Failed to Load"):
            cmds.button(source_object_status, l=failed_message, e=True, bgc=(1, .4, .4), w=130)
            cmds.textScrollList(blend_nodes_scroll_list, e=True, removeAll=True)
            morphing_util_settings['morphing_obj'] = ''

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
                    morphing_util_settings['morphing_obj'] = current_selection[0]
                    cmds.button(source_object_status, l=morphing_util_settings.get('morphing_obj'),
                                e=True, bgc=(.6, .8, .6), w=130)
                    cmds.textScrollList(blend_nodes_scroll_list, e=True, removeAll=True)
                    cmds.textScrollList(blend_nodes_scroll_list, e=True, append=blendshape_nodes)

    def _validate_search_replace():
        """ Checks elements one last time before running the script """
        update_settings()

        # Blend Shape Node
        blend_node = morphing_util_settings.get('blend_node')
        if blend_node:
            if not cmds.objExists(blend_node):
                cmds.warning('Unable to blend shape node. Please try loading the object again.')
                return False
        else:
            cmds.warning('Select a blend shape node to be used as target.')
            return False

        # # Run Script
        logger.debug('Main Function Called')
        replace_string = morphing_util_settings.get('replace_string').replace(' ', '')
        search_string = morphing_util_settings.get('search_string').replace(' ', '')

        current_selection = cmds.ls(selection=True)
        cmds.undoInfo(openChunk=True, chunkName=script_name)  # Start undo chunk
        try:
            num_affected = search_replace_blend_targets(blend_node, search_string, replace_string)
            operation_inview_feedback(num_affected, action="renamed")
            return True
        except Exception as e:
            logger.debug(str(e))
            return False
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=script_name)
            cmds.select(current_selection)

    def _delete_all_blend_targets_btn():
        removed_num = delete_all_blend_targets()
        operation_inview_feedback(removed_num, action="deleted")

    def _delete_all_blend_nodes_btn():
        removed_num = delete_all_blend_nodes()
        operation_inview_feedback(removed_num, action="deleted")

    window_name = "build_gui_morphing_utilities"
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
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: _open_gt_tools_documentation())
    cmds.separator(h=5, style='none')  # Empty Space

    # General Utilities
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('General Utilities:')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 125), (2, 125)], cs=[(1, 10), (2, 10)], p=content_main)
    cmds.button(l="Delete All\nBlend Shape Nodes", c=lambda x: _delete_all_blend_nodes_btn())
    cmds.button(l="Delete All\nBlend Shape Targets", c=lambda x: _delete_all_blend_targets_btn())
    cmds.separator(h=5, style='none')  # Empty Space

    # Deformed Mesh (Source) ------------------------------------------
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Deformed Mesh (Source):')
    cmds.separator(h=5, style='none')  # Empty Space

    cmds.rowColumnLayout(nc=2, cw=[(1, 129), (2, 130)], cs=[(1, 10)], p=content_main)
    cmds.button(l="Load Morphing Object", c=lambda x: object_load_handler("morphing_obj"), w=130)
    source_object_status = cmds.button(l="Not loaded yet", bgc=(.2, .2, .2), w=130,
                                       c=lambda x: select_existing_object(morphing_util_settings.get('morphing_obj')))

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text('Blend Shape Nodes:', font="smallPlainLabelFont")
    blend_nodes_scroll_list = cmds.textScrollList(numberOfRows=8, allowMultiSelection=False, height=70,
                                                  selectCommand=select_blend_shape_node)

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)

    # Search and Replace Target Names ------------------------------------------
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.text("Search and Replace Target Names:")
    cmds.separator(h=7, style='none')  # Empty Space

    text_label_width = 90
    text_field_width = 150

    cmds.rowColumnLayout(nc=2, cw=[(1, text_label_width), (2, text_field_width)], cs=[(1, 10), (2, 5)], p=content_main)

    cmds.text("Search:")
    desired_filter_textfield = cmds.textField(text='', pht='Text to Search', cc=update_settings)

    cmds.rowColumnLayout(nc=2, cw=[(1, text_label_width), (2, text_field_width)], cs=[(1, 10), (2, 5)], p=content_main)
    cmds.text("Replace:")
    undesired_filter_textfield = cmds.textField(text='', pht='Text to Replace', cc=update_settings)

    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=7, style='none')  # Empty Space

    cmds.button(l="Search and Replace Target Names", bgc=(.6, .6, .6), c=lambda x: _validate_search_replace())
    cmds.separator(h=10, style='none')  # Empty Space

    # Show and Lock Window
    cmds.showWindow(window_gui_blends_to_attr)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/falloff_blend.png')
    widget.setWindowIcon(icon)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_name)


def _open_gt_tools_documentation():
    """ Opens a web browser with the auto rigger docs  """
    cmds.showHelp('https://github.com/TrevisanGMW/gt-tools/tree/release/docs#-gt-morphing-utilities-', absolute=True)


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


def operation_inview_feedback(number_of_changes, action="affected"):
    """
    Prints an inViewMessage to give feedback to the user about how many objects were affected.
    Uses the module "random" to force identical messages to appear at the same time.

    Args:
        number_of_changes (int): How many objects were affected.
        action (string, optional): Description of the action. e.g. "deleted", "renamed", or "affected"
    """
    message = '<' + str(random.random()) + '><span style=\"color:#FF0000;text-decoration:underline;\">'
    message += str(number_of_changes)
    if number_of_changes == 1:
        message += '</span><span style=\"color:#FFFFFF;\"> element was ' + action + '.</span>'
    else:
        message += '</span><span style=\"color:#FFFFFF;\"> elements were ' + action + '.</span>'
    cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)


# Build UI
if __name__ == '__main__':
    debugging = False
    if debugging:
        logger.setLevel(logging.DEBUG)
        morphing_util_settings['morphing_obj'] = 'target_obj'
        morphing_util_settings['blend_node'] = 'blendShape1'
    build_gui_morphing_utilities()
