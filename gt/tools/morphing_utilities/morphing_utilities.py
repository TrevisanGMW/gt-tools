"""
 GT Morphing Utilities
 github.com/TrevisanGMW/gt-tools - 2020-11-15
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
import maya.mel as mel
import logging
import random
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_blend_utilities")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT - Morphing Utilities"

# Version:
script_version = "?.?.?"  # Module version (init)

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


def get_target_index(blend_shape_node, target):
    """
    Get the target index of the specified target found in blend_shape_node
    Args:
        blend_shape_node (string): Name of the blend shape node
        target (string): Name of the target
    Returns:
        Integer of the index number for the target
    """
    # Get attribute alias
    alias_list = cmds.aliasAttr(blend_shape_node, q=True)
    alias_index = alias_list.index(target)
    alias_attr = alias_list[alias_index + 1]
    target_index = int(alias_attr.split('[')[-1].split(']')[0])
    return target_index


def get_target_list(blend_shape_node):
    """
    Args:
        blend_shape_node (string) : Name of the blend shape node
    Returns:
         the target list for the input blend_shape_node
    """

    # Get attribute alias
    target_list = cmds.listAttr(blend_shape_node + '.w', m=True) or []
    return target_list


def get_next_available_target_index(blend_shape_node):
    """
    Get the next available blend_shape_node target index
    Args:
        blend_shape_node (string): Name of blend shape node to get the next available target index
    Returns:
        Int of the next available index
    """
    # Get blend_shape_node target list
    target_list = get_target_list(blend_shape_node)
    if not target_list:
        return 0

    # Create next index
    last_index = get_target_index(blend_shape_node, target_list[-1])
    next_index = last_index + 1
    return next_index


def get_target_name(blend_shape_node, target_geo):
    """
    Get blend_shape_node target alias for specified target geometry
    Args:
        blend_shape_node (string): Blend Shape node to get target name
        target_geo (string): BlendShape target geometry to get alia name
    Returns:
        String of the target alias
    """
    # Get Target Shapes
    target_shape = []
    non_intermediate_shapes = cmds.listRelatives(target_geo, shapes=True, noIntermediate=True, path=True)
    if non_intermediate_shapes:
        target_shape.extend(non_intermediate_shapes)

    if not target_shape:
        target_shape = cmds.ls(cmds.listRelatives(target_geo, allDescendents=True, path=True),
                               shapes=True, noIntermediate=True)
    # Find Target Connection
    target_conn = cmds.listConnections(target_shape, shapes=True, destination=True,
                                       source=False, plugs=False, connections=True)
    target_conn_ind = target_conn.index(blend_shape_node)
    target_conn_attr = target_conn[target_conn_ind - 1]
    target_conn_plug = cmds.listConnections(target_conn_attr, sh=True, p=True, d=True, s=False)[0]

    # Get Target Index
    target_ind = int(target_conn_plug.split('.')[2].split('[')[1].split(']')[0])
    # Get Target Alias
    target_alias = cmds.aliasAttr(blend_shape_node + '.weight[' + str(target_ind) + ']', q=True)
    return target_alias


def add_target(blend_shape_node, target=None, base_mesh='',
               target_index=-1, target_alias='',
               target_weight=1.0, topology_check=False):
    """
    Add a new target to the provided blend shape node
    Args:
        blend_shape_node (string): Name of blend_shape_node to use
        target (optional, string): New blend shape target geometry (if empty, base is used)
        base_mesh (optional, string): blend shape base_mesh geometry. If empty, use first connection on base_mesh geo
        target_index (optional, int): The target index. If "-1", use next available index.
        target_alias (optional, string):  Define the target alias (nickname)
        target_weight (optional, float): Set initial target weight value
        topology_check (optional, bool): If active, check topology before creating
    Returns:
        Name of the newly created target with its blend shape node as prefix. E.g. "blendShape1.myTarget"
    """
    # Get Base Geometry
    if not target:
        target = get_blend_mesh(blend_shape_node)
    if not base_mesh:
        base_mesh = get_blend_mesh(blend_shape_node)
        logger.debug("base_mesh: " + str(base_mesh))

    # Get Target Index
    if target_index < 0:
        target_index = get_next_available_target_index(blend_shape_node)
        logger.debug("target_index: " + str(target_index))

    # Add Target
    cmds.blendShape(blend_shape_node, e=True, t=(base_mesh, target_index, target, 1.0), topologyCheck=topology_check)

    # Get Current Target Name
    target_name = get_target_name(blend_shape_node, target)

    # Update Target Alias
    if target_alias:
        target_index = get_target_index(blend_shape_node, target_name)
        cmds.aliasAttr(target_alias, blend_shape_node + '.weight[' + str(target_index) + ']')
        target_name = target_alias

    if target_weight:
        cmds.setAttr(blend_shape_node + '.' + target_name, target_weight)
    return blend_shape_node + '.' + target_name


def duplicate_blend_target(blend_node, blend_index):
    """
    Duplicate a blend target based on its index
    Args:
        blend_node (string): Blend shape node
        blend_index (int): Index of the blend target
    """
    # Hack to Enforce Selection - Pattern used for when selecting blend target using shape editor
    selected_blend = blend_node + "." + str(blend_index) + "/"
    cmds.optionVar(rm="blendShapeEditorTreeViewSelection")
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", ""))  # Empty strings (Matching output pattern)
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", ""))
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", ""))
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", ""))
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", selected_blend))
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", ""))
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", ""))
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", ""))
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", selected_blend))
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", selected_blend))
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", "0"))  # 0
    cmds.optionVar(sva=("blendShapeEditorTreeViewSelection", selected_blend))
    logger.debug(str(cmds.optionVar(q="blendShapeEditorTreeViewSelection")))
    mel.eval("blendShapeEditorDuplicateTargets")
    cmds.optionVar(rm="blendShapeEditorTreeViewSelection")


def duplicate_flip_blend_target(blend_node, target_name, duplicate_name=None, symmetry_axis='x'):
    """
        Duplicates and flip targets matching the provided name
        Args:
            blend_node (string) Name of the blend shape node
            target_name (string) Name of the blend shape target to duplicate and flip
            duplicate_name (optional, string): New name for the duplicated target
            symmetry_axis (string, optional) Which axis to use when mirroring (default: x)
        """
    cmds.select(d=True)  # Deselect
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True)

    duplicate_target_index = get_target_index(blend_node, target_name)
    duplicate_blend_target(blend_node, duplicate_target_index)

    # Get Newly Generated Targets
    blendshape_names_refresh = cmds.listAttr(blend_node + '.w', m=True)
    blendshape_names_new_only = list(set(blendshape_names_refresh) - set(blendshape_names))

    duplicate_target_name = ""
    if blendshape_names_new_only:
        duplicate_target_name = blendshape_names_new_only[0]
    if duplicate_target_name:
        duplicate_target_index = get_target_index(blend_node, duplicate_target_name)
        cmds.blendShape(blend_node, e=True,
                        flipTarget=[(0, duplicate_target_index)],
                        symmetryAxis=symmetry_axis,
                        symmetrySpace=1)  # 0=topological, 1=object, 2=UV
        if duplicate_name:
            rename_blend_target(blend_node, duplicate_target_name, duplicate_name)
        else:
            new_name = duplicate_target_name.replace('Copy', 'Flipped')
            rename_blend_target(blend_node, duplicate_target_name, new_name)

    # Return Generated Targets
    blendshape_names_refresh = cmds.listAttr(blend_node + '.w', m=True)
    blendshape_names_new_only = list(set(blendshape_names_refresh) - set(blendshape_names))
    for blend in blendshape_names_new_only:
        try:
            cmds.setAttr(blend_node + "." + blend, 0)
        except Exception as e:
            logger.debug(str(e))
    return blendshape_names_new_only


def duplicate_mirror_blend_target(blend_node, target_name, duplicate_name=None,
                                  symmetry_axis='x', mirror_direction="-"):
    """
        Duplicates and mirror targets matching the provided name
        Args:
            blend_node (string) Name of the blend shape node
            target_name (string) Name of the blend shape target to duplicate and flip
            duplicate_name (optional, string): New name for the duplicated target
            symmetry_axis (optional, string) Which axis to use when mirroring (default: x)
            mirror_direction (optional, string): Direction of the mirror operation (either "+" or "-") - Default "-"
        """
    cmds.select(d=True)  # Deselect
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True)

    mirror_dir = 0  # 0=negative,1=positive
    if mirror_direction == '+':
        mirror_dir = 1

    duplicate_target_index = get_target_index(blend_node, target_name)
    duplicate_blend_target(blend_node, duplicate_target_index)

    # Get Newly Generated Targets
    blendshape_names_refresh = cmds.listAttr(blend_node + '.w', m=True)
    blendshape_names_new_only = list(set(blendshape_names_refresh) - set(blendshape_names))

    duplicate_target_name = ""
    if blendshape_names_new_only:
        duplicate_target_name = blendshape_names_new_only[0]
    if duplicate_target_name:
        duplicate_target_index = get_target_index(blend_node, duplicate_target_name)
        cmds.blendShape(blend_node, e=True,
                        mirrorTarget=[(0, duplicate_target_index)],
                        mirrorDirection=mirror_dir,  # 0=negative,1=positive
                        symmetrySpace=1,  # 0=topological, 1=object, 2=UV
                        symmetryAxis=symmetry_axis,  # for object symmetrySpace
                        )
        if duplicate_name:
            rename_blend_target(blend_node, duplicate_target_name, duplicate_name)
        else:
            new_name = duplicate_target_name.replace('Copy', 'Mirrored')
            rename_blend_target(blend_node, duplicate_target_name, new_name)

    # Return Generated Targets
    blendshape_names_refresh = cmds.listAttr(blend_node + '.w', m=True)
    blendshape_names_new_only = list(set(blendshape_names_refresh) - set(blendshape_names))
    for blend in blendshape_names_new_only:
        try:
            cmds.setAttr(blend_node + "." + blend, 0)
        except Exception as e:
            logger.debug(str(e))
    return blendshape_names_new_only


def duplicate_flip_filtered_targets(blend_node, search_string, replace_string=None, symmetry_axis='x'):
    """
    Duplicate targets that match search string and flip them
    Args:
        blend_node (string): Name of the blend shape node to be used in the operation
        search_string (string): Only targets with this provided string will be included in the operation
        replace_string (optional, string): If provided, a search and replace operation will happen on the string to
                                    determine the new name of the flipped target. For example, if search is "Right" and
                                    replace is "Left", a target named "eyeBlinkRight" will be renamed "eyeBlinkLeft".
                                    If not provided, new targets will have a suffix "_Flipped"
        symmetry_axis (string, optional) Which axis to use when mirroring (default: x)
    Returns:
        Number of operations (Total number of flipped targets)
    """
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True) or []
    pairs_to_rename = {}
    logger.debug("search_string:" + search_string)
    logger.debug("replace_string:" + str(replace_string))

    for i in range(len(blendshape_names)):
        blend = blendshape_names[i]
        if search_string in blend:
            if replace_string:
                new_name = blend.replace(search_string, replace_string)
            else:
                new_name = replace_string
            pairs_to_rename[blend] = new_name

    number_operations = 0
    for key, value in pairs_to_rename.items():
        try:
            duplicate_flip_blend_target(blend_node, key, duplicate_name=value, symmetry_axis=symmetry_axis)
            number_operations += 1
        except Exception as exc:
            logger.debug(str(exc))
    return number_operations


def duplicate_mirror_filtered_targets(blend_node, search_string, replace_string=None,
                                      symmetry_axis='x', mirror_direction="-"):
    """
    Duplicate targets that match the search string and mirror them
    Args:
        blend_node (string): Name of the blend shape node to be used in the operation
        search_string (string): Only targets with this provided string will be included in the operation
        replace_string (optional, string): If provided, a search and replace operation will happen on the string to
                                    determine the new name of the flipped target. For example, if search is "Right" and
                                    replace is "Left", a target named "eyeBlinkRight" will be renamed "eyeBlinkLeft".
                                    If not provided, new targets will have a suffix "_Flipped"
        symmetry_axis (string, optional) Which axis to use when mirroring (default: x)
        mirror_direction (optional, string): Direction of the mirror operation (default "-")
    Returns:
        Number of operations (Total number of flipped targets)
    """
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True) or []
    pairs_to_rename = {}
    logger.debug("search_string:" + search_string)
    logger.debug("replace_string:" + str(replace_string))

    for i in range(len(blendshape_names)):
        blend = blendshape_names[i]
        if search_string in blend:
            if replace_string:
                new_name = blend.replace(search_string, replace_string)
            else:
                new_name = replace_string
            pairs_to_rename[blend] = new_name

    number_operations = 0
    for key, value in pairs_to_rename.items():
        try:
            duplicate_mirror_blend_target(blend_node, key,
                                          duplicate_name=value,
                                          symmetry_axis=symmetry_axis,
                                          mirror_direction=mirror_direction)
            number_operations += 1
        except Exception as exc:
            logger.debug(str(exc))
    return number_operations


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

    def _validate_current_blend_settings(blend_node):
        """Checks if basic elements are available before running targeted operations"""
        if blend_node:
            if not cmds.objExists(blend_node):
                cmds.warning('Unable to blend shape node. Please try loading the object again.')
                return False
        else:
            cmds.warning('Select a blend shape node to be used as target.')
            return False
        return True

    def _validate_search_replace(operation="default"):
        """ Checks elements one last time before running the script """
        update_settings()

        blend_node = morphing_util_settings.get('blend_node')
        is_valid = _validate_current_blend_settings(blend_node)
        if not is_valid:
            return is_valid

        # # Run Script
        logger.debug('Search and Replace Function Called')
        replace_string = morphing_util_settings.get('replace_string').replace(' ', '')
        search_string = morphing_util_settings.get('search_string').replace(' ', '')

        if operation == "default":
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
        elif operation == "flip":
            symmetry_axis = cmds.optionMenu(symmetry_option_menu, q=True, value=True)
            current_selection = cmds.ls(selection=True)
            cmds.undoInfo(openChunk=True, chunkName=script_name)  # Start undo chunk
            try:
                if not replace_string:
                    replace_string = None
                num_affected = duplicate_flip_filtered_targets(blend_node, search_string, replace_string,
                                                               symmetry_axis=symmetry_axis)
                operation_inview_feedback(num_affected, action="duplicated and flipped")
                return True
            except Exception as e:
                logger.debug(str(e))
                return False
            finally:
                cmds.undoInfo(closeChunk=True, chunkName=script_name)
                cmds.select(current_selection)
        elif operation == "mirror":
            symmetry_axis = cmds.optionMenu(symmetry_option_menu, q=True, value=True)
            mirror_direction = cmds.optionMenu(mirror_option_menu, q=True, value=True)
            current_selection = cmds.ls(selection=True)
            cmds.undoInfo(openChunk=True, chunkName=script_name)  # Start undo chunk
            try:
                if not replace_string:
                    replace_string = None
                num_affected = duplicate_mirror_filtered_targets(blend_node, search_string, replace_string,
                                                                 symmetry_axis=symmetry_axis,
                                                                 mirror_direction=mirror_direction)
                operation_inview_feedback(num_affected, action="duplicated and mirrored")
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

    def _validate_set_target_values():
        """Validate set targets and run operation"""
        blend_node = morphing_util_settings.get('blend_node')
        is_valid = _validate_current_blend_settings(blend_node)
        if not is_valid:
            return is_valid
        new_target_value = cmds.floatField(set_target_value, q=True, value=True)
        set_targets_value(blend_node, new_target_value)

    def _validate_extract_current_targets():
        """Validate set targets and run operation"""
        blend_node = morphing_util_settings.get('blend_node')
        is_valid = _validate_current_blend_settings(blend_node)
        if not is_valid:
            return is_valid
        bake_current_state(blend_node)

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

    cmds.separator(h=10, style='none')  # Empty Space
    cmds.button(l="Search and Replace Target Names", bgc=(.6, .6, .6), c=lambda x: _validate_search_replace())
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text("Search & Replace With Operations:")
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 120), (2, 120)], cs=[(1, 15), (2, 15)], p=content_main)

    mirror_option_menu = cmds.optionMenu(label='Mirror Direction:')
    cmds.menuItem(label='-')
    cmds.menuItem(label='+')
    symmetry_option_menu = cmds.optionMenu(label='Symmetry Axis:')
    cmds.menuItem(label='x')
    cmds.menuItem(label='y')
    cmds.menuItem(label='z')
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 245), (2, 15)], cs=[(1, 10)], p=content_main)
    cmds.button(l="Search, Replace While Duplicating and Flipping ",
                c=lambda x: _validate_search_replace("flip"))
    flip_help_message = 'This option duplicates filtered targets and flips them. \nIt uses the "Search" text-field ' \
                        'as a filter, which means that only targets containing the provided string are be used in the' \
                        ' operation. If empty, all targets will be used.\nThe same "Search" field is used to rename' \
                        ' the filtered targets using the "Replace" string in the search/replace operation. ' \
                        'If "Replace" is not provided, an extra suffix "_Flipped" automatically added to the end of ' \
                        'the new targets to avoid conflicting names.'
    flip_help_title = "Duplicate and Flip"
    cmds.button(l="?", bgc=(.3, .3, .3), height=15,
                c=lambda x: build_custom_help_window(flip_help_message, flip_help_title))
    cmds.separator(h=7, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 245), (2, 15)], cs=[(1, 10)], p=content_main)
    cmds.button(l="Search, Replace While Duplicating and Mirroring ",
                c=lambda x: _validate_search_replace("mirror"))
    mirror_help_message = 'This option duplicates filtered targets and mirrors them. \nIt uses the "Search"' \
                          ' text-field as a filter, which means that only targets containing the provided string are' \
                          ' be used in the operation. If empty, all targets will be used.\nThe same "Search" field is' \
                          ' used to rename the filtered targets using the "Replace" string in the search/replace ' \
                          'operation. If "Replace" is not provided, an extra suffix "_Flipped" automatically added to' \
                          ' the end of the new targets to avoid conflicting names.'
    mirror_help_title = "Duplicate and Mirror"
    cmds.button(l="?", bgc=(.3, .3, .3), height=15,
                c=lambda x: build_custom_help_window(mirror_help_message, mirror_help_title))
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.separator(h=5)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 180), (2, 70)], cs=[(1, 10), (2, 10)], p=content_main)
    cmds.button(l="Set All Target Values To", bgc=(.6, .6, .6), c=lambda x: _validate_set_target_values())
    set_target_value = cmds.floatField(value=1, precision=1)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 260)], cs=[(1, 10)], p=content_main)
    cmds.button(l="Extract Targets At Current Values", bgc=(.6, .6, .6),
                c=lambda x: _validate_extract_current_targets())
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


def set_targets_value(blend_node, value):
    """
    Set the value of all targets found in the blend shape node
    Args:
        blend_node (string): Name of the blend shape node
        value (float): Value to update the blend shape targets (e.g. 0.5) - Default range is 0 to 1

    """
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True) or []
    errors = []
    for target in blendshape_names:
        try:
            cmds.setAttr(blend_node + "." + target, value)
        except Exception as e:
            errors.append(str(e))
    if errors:
        for error in errors:
            print(error)


def bake_current_state(blend_node):
    """
    Extracts targets as independent meshes (Not referenced by the blend shape node in any way)
    Args:
        blend_node (string) : Name of the blend shape node to use in the operation
    TODO:
        Add lock and connection checks
    """
    blendshape_names = cmds.listAttr(blend_node + '.w', m=True) or []
    errors = []
    target_values = {}
    target_mesh = get_blend_mesh(blend_node)
    for target in blendshape_names:  # Store original values
        try:
            value = cmds.getAttr(blend_node + "." + target)
            target_values[target] = value
            cmds.setAttr(blend_node + "." + target, 0)  # Temporarily
        except Exception as e:
            errors.append(str(e))
    for target in blendshape_names:  # Bake shapes
        try:
            value = target_values.get(target)
            cmds.setAttr(blend_node + "." + target, value)
            new_suffix = "_" + str(int(value*100)) + "pct"
            cmds.duplicate(target_mesh, name=target_mesh + "_" + target + new_suffix)
            cmds.setAttr(blend_node + "." + target, 0)
        except Exception as e:
            errors.append(str(e))
    for target in blendshape_names:  # Bring back original values
        try:
            value = target_values.get(target)
            cmds.setAttr(blend_node + "." + target, value)
        except Exception as e:
            errors.append(str(e))
    if errors:
        for error in errors:
            print(error)


def get_blend_mesh(blend_node):
    if cmds.objectType(blend_node) != "blendShape":
        cmds.warning("Provided node \"" + str(blend_node) + "\" is not a blend shape node.")
        return
    target_mesh = cmds.listConnections(blend_node + ".outputGeometry") or []
    if len(target_mesh) > 0:
        return target_mesh[0]


def build_custom_help_window(input_text, help_title='', *args):
    """
    Creates a help window to display the provided text

    Args:
        input_text (string): Text used as help, this is displayed in a scroll fields.
        help_title (optional, string)

    Returns:
        body_column: Used to add more UI elements in case the help menu needs it
    """
    logger.debug(str(args))
    window_name = help_title.replace(" ", "_").replace("-", "_").lower().strip() + "_help_window"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=help_title + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    main_column = cmds.columnLayout(p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)  # Title Column
    cmds.text(help_title + ' Help', bgc=(.4, .4, .4), fn='boldLabelFont', align='center')
    cmds.separator(h=10, style='none', p=main_column)  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)

    help_scroll_field = cmds.scrollField(editable=False, wordWrap=True, fn='smallPlainLabelFont')

    cmds.scrollField(help_scroll_field, e=True, ip=0, it=input_text)
    cmds.scrollField(help_scroll_field, e=True, ip=1, it='')  # Bring Back to the Top

    return_column = cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)

    # Close Button
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda x: close_help_gui())
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
        """ Closes help windows """
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)

    return return_column


# Build UI
if __name__ == '__main__':
    debugging = False
    if debugging:
        logger.setLevel(logging.DEBUG)
        morphing_util_settings['morphing_obj'] = 'target_obj'
        morphing_util_settings['blend_node'] = 'blendShape1'
    build_gui_morphing_utilities()
