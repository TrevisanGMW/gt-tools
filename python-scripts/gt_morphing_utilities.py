"""
 GT Morphing Utilities
 github.com/TrevisanGMW/gt-tools - 2020-11-15

 0.0.1 to 0.0.2 - 2020-11-15
 Added "delete_blends_target"
 Added "delete_blends_targets"
 Added "delete_all_blend_targets"

 

 TODO:
    Add search/replace renamer
    Add error handling

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
script_version = "0.0.3"


# Settings
morphing_util_settings = {'morphing_obj': '',
                          'blend_node': '',
                          'attr_holder': '',
                          'search_string': '',
                          'replace_string': '',
                          'desired_filter_type': 'includes',
                          'undesired_filter_type': 'includes',
                          'ignore_case': True,
                          'modify_range': True,
                          'new_range_min': 0,
                          'new_range_max': 10,
                          'old_range_min': 0,
                          'old_range_max': 1,
                          'ignore_connected': True,
                          'add_separator': True,
                          'sort_attr': True,
                          'delete_instead': False,
                          }


def delete_blends_targets(blend_node):
    """
    Delete all blend targets found in the provided blend shape node

    Args:
        blend_node (string) Name of the blend shape node
    """
    cmds.select(d=True)  # Deselect
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True)
    for i in range(len(blendshape_names)):
        cmds.removeMultiInstance(blend_node + ".weight[" + str(i) + "]", b=True)
        cmds.removeMultiInstance(blend_node + ".inputTarget[0].inputTargetGroup[" + str(i) + "]", b=True)


def delete_all_blend_targets():
    """
    Delete all blend shape targets (not the nodes, only the targets)
    Dependencies:
        delete_blends_targets()
    """
    cmds.select(d=True)  # Deselect
    for blend_node in cmds.ls(typ="blendShape"):
        delete_blends_targets(blend_node)


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
    Deletes any blend shape nodes found under the history of the provided object

    Args:
        obj (String): name of the object. e.g. "pSphere1"
    """
    history = cmds.listHistory(obj)
    for node in history:
        if cmds.objectType(node) == "blendShape":
            cmds.delete(node)


def blends_to_attr(blend_node, attr_holder, search_strings, replace_strings,
                   desired_method='includes', undesired_method='includes', sort_attr=True,
                   ignore_connected=True, add_separator=True, ignore_case=True, delete_instead=False,
                   modify_range=True, old_min=0, old_max=1, new_min=0, new_max=10):
    """

    Args:
        blend_node (string): Blend shape node used to extract desired morphing targets
        attr_holder (string): Object to receive attributes (usually a control curve)
        search_strings (list): A list of desired strings (targets with these strings will be added)
        replace_strings (list): A list of undesired strings (targets with these strings will be ignored)
        desired_method (string): Method using during filtering "includes", "startswith" or "endswith"
        undesired_method (string): Method using during filtering "includes", "startswith" or "endswith"
        sort_attr: If it should sort the list or use the original order
        ignore_connected: If it should ignore morphing targets that already have an incoming connection
        add_separator: Added a locked attribute used as a separator
        ignore_case: If it should ignore the capitalization of the strings when filtering
        delete_instead: If active, it won't create attributes, but will instead attempt to delete them
        modify_range: If it should remap the range of the target and attribute values
        old_min: old minimum value (usually, 0)
        old_max: old maximum value (usually, 1)
        new_min: new minimum value (usually, 0)
        new_max: new maximum value (usually, 10)

    Returns:
        created_attributes (list)
    """
    custom_separator_attr = ''
    remap_morphing_suffix = 'remap_morphing_'
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True)
    filtered_blends = []

    # Find desired blends
    for target in blendshape_names:
        for search_string in search_strings:
            target_compare = target
            string_compare = search_string
            if ignore_case:
                target_compare = target_compare.lower()
                string_compare = string_compare.lower()
            if desired_method == 'includes':
                if string_compare in target_compare:
                    filtered_blends.append(target)
            elif desired_method == 'startswith':
                if target_compare.startswith(string_compare):
                    filtered_blends.append(target)
            elif desired_method == 'endswith':
                if target_compare.endswith(string_compare):
                    filtered_blends.append(target)

    if len(search_strings) == 0:  # If filter empty, use everything
        filtered_blends = blendshape_names

    accessible_blends = []
    if ignore_connected:  # Pre-ignore connected blends
        for blend in filtered_blends:
            connections = cmds.listConnections(blend_node + '.' + blend, destination=False, plugs=True) or []
            if len(connections) == 0:
                accessible_blends.append(blend)
    else:
        accessible_blends = filtered_blends
    if delete_instead:
        accessible_blends = filtered_blends

    # Find desired blends
    accessible_and_desired_blends = []
    undesired_blends = []
    for target in accessible_blends:
        for replace_string in replace_strings:
            target_compare = target
            string_compare = replace_string
            if ignore_case:
                target_compare = target_compare.lower()
                string_compare = string_compare.lower()
            if undesired_method == 'includes':
                if string_compare in target_compare:
                    undesired_blends.append(target)
            elif undesired_method == 'startswith':
                if target_compare.startswith(string_compare):
                    undesired_blends.append(target)
            elif undesired_method == 'endswith':
                if target_compare.endswith(string_compare):
                    undesired_blends.append(target)

    for blend in accessible_blends:
        if blend not in undesired_blends:
            accessible_and_desired_blends.append(blend)

    # Separator Attribute
    current_attributes = cmds.listAttr(attr_holder, userDefined=True) or []
    separator_attr = 'blends'
    if custom_separator_attr:
        separator_attr = custom_separator_attr
    if separator_attr in current_attributes or custom_separator_attr in current_attributes:
        add_separator = False

    if len(accessible_and_desired_blends) != 0 and add_separator and not delete_instead:
        cmds.addAttr(attr_holder, ln=separator_attr, at='enum', en='-------------:', keyable=True)
        cmds.setAttr(attr_holder + '.' + separator_attr, e=True, lock=True)

    # Delete Attributes
    deleted_attributes = []
    if delete_instead:
        for target in accessible_and_desired_blends:
            if target in current_attributes:
                if not cmds.getAttr(attr_holder + '.' + target, lock=True):
                    connections = cmds.listConnections(attr_holder + '.' + target, source=True) or []
                    if connections and cmds.objectType(connections[0]) == 'remapValue' \
                            and str(connections[0]).startswith(remap_morphing_suffix):
                        cmds.delete(connections[0])
                    cmds.deleteAttr(attr_holder + '.' + target)
                    deleted_attributes.append(attr_holder + '.' + target)
        try:
            cmds.setAttr(attr_holder + '.' + separator_attr, e=True, lock=False)
            cmds.deleteAttr(attr_holder + '.' + separator_attr)
            deleted_attributes.append(attr_holder + '.' + separator_attr)
        except Exception as e:
            logger.debug(str(e))
        return deleted_attributes

    # Create Blend Drivers
    if sort_attr:
        accessible_and_desired_blends.sort()
    for target in accessible_and_desired_blends:
        if modify_range:
            if target not in current_attributes:
                cmds.addAttr(attr_holder, ln=target, at='double', k=True,
                             maxValue=new_max, minValue=new_min)
            else:
                cmds.warning('"' + target + '" already existed on attribute holder. '
                                            'Please check if no previous connections were lost.')
            remap_node = cmds.createNode('remapValue', name=remap_morphing_suffix + target)
            cmds.setAttr(remap_node + '.inputMax', new_max)
            cmds.setAttr(remap_node + '.inputMin', new_min)
            cmds.setAttr(remap_node + '.outputMax', old_max)
            cmds.setAttr(remap_node + '.outputMin', old_min)
            cmds.connectAttr(attr_holder + '.' + target, remap_node + '.inputValue')
            cmds.connectAttr(remap_node + '.outValue', blend_node + '.' + target, force=True)
        else:
            if target not in current_attributes:
                cmds.addAttr(attr_holder, ln=target, at='double', k=True, maxValue=1, minValue=0)
            else:
                cmds.warning('"' + target + '" already existed on attribute holder. '
                                            'Please check if no previous connections were lost')
            cmds.connectAttr(attr_holder + '.' + target, blend_node + '.' + target, force=True)

    return accessible_and_desired_blends


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

        def failed_to_load_target(failed_message="Failed to Load"):
            cmds.button(attr_holder_status, l=failed_message, e=True, bgc=(1, .4, .4), w=130)
            morphing_util_settings['attr_holder'] = ''

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
                morphing_util_settings['attr_holder'] = current_selection[0]
                cmds.button(attr_holder_status, l=morphing_util_settings.get('attr_holder'), e=True,
                            bgc=(.6, .8, .6), w=130)
            else:
                cmds.warning("Something went wrong, make sure you selected just one object and try again.")

    def validate_operation():
        """ Checks elements one last time before running the script """
        update_settings()

        # Attribute Holder
        attr_holder = morphing_util_settings.get('attr_holder')
        if attr_holder:
            if not cmds.objExists(attr_holder):
                cmds.warning('Unable to locate attribute holder. Please try loading the object again.')
                return False
        else:
            cmds.warning('Missing attribute holder. Make sure you loaded an object and try again.')
            return False

        # Blend Shape Node
        blend_node = morphing_util_settings.get('blend_node')
        if blend_node:
            if not cmds.objExists(blend_node):
                cmds.warning('Unable to blend shape node. Please try loading the object again.')
                return False
        else:
            cmds.warning('Select a blend shape node to be used as source.')
            return False

        # # Run Script
        logger.debug('Main Function Called')
        undesired_strings = morphing_util_settings.get('replace_string').replace(' ', '')
        if undesired_strings:
            undesired_strings = undesired_strings.split(',')
        else:
            undesired_strings = []
        desired_strings = morphing_util_settings.get('search_string').replace(' ', '')
        if desired_strings:
            desired_strings = desired_strings.split(',')
        else:
            desired_strings = []

        current_selection = cmds.ls(selection=True)
        cmds.undoInfo(openChunk=True, chunkName=script_name)  # Start undo chunk
        try:
            blend_attr_list = blends_to_attr(blend_node, attr_holder, desired_strings, undesired_strings,
                                             desired_method=morphing_util_settings.get('desired_filter_type'),
                                             undesired_method=morphing_util_settings.get('undesired_filter_type'),
                                             ignore_connected=morphing_util_settings.get('ignore_connected'),
                                             add_separator=morphing_util_settings.get('add_separator'),
                                             ignore_case=morphing_util_settings.get('ignore_case'),
                                             modify_range=morphing_util_settings.get('modify_range'),
                                             old_min=morphing_util_settings.get('old_range_min'),
                                             old_max=morphing_util_settings.get('old_range_max'),
                                             new_min=morphing_util_settings.get('new_range_min'),
                                             new_max=morphing_util_settings.get('new_range_max'),
                                             delete_instead=morphing_util_settings.get('delete_instead'),
                                             sort_attr=morphing_util_settings.get('sort_attr'))

            if blend_attr_list:
                message = '<' + str(random.random()) + '>'
                message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(len(blend_attr_list))
                message += ' </span>'
                is_plural = 'morphing attributes were'
                if len(blend_attr_list) == 1:
                    is_plural = 'morphing attribute was'
                operation_message = ' created/connected.'
                if morphing_util_settings.get('delete_instead'):
                    operation_message = ' deleted.'
                message += is_plural + operation_message
                cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
                sys.stdout.write(str(len(blend_attr_list)) + ' ' + is_plural + operation_message)
                return True
            else:
                if morphing_util_settings.get('delete_instead'):
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

    # 3. Settings and Filters ------------------------------------------
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

    cmds.button(l="Rename Morphing Targets", bgc=(.6, .6, .6), c=lambda x: validate_operation())
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
    # TODO: Create documentation @@@


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
    debugging = False
    if debugging:
        logger.setLevel(logging.DEBUG)
        morphing_util_settings['morphing_obj'] = 'source_obj'
        morphing_util_settings['attr_holder'] = 'target_obj'
        morphing_util_settings['blend_node'] = 'blendShape1'
    build_gui_morphing_utilities()
    # def get_selection_blend_node(obj)

    # if __name__ == '__main__':
    #     logger.setLevel(logging.DEBUG)
    #     first_selection = cmds.ls(selection=True)[0]
    #     # delete_blend_nodes(first_selection)
