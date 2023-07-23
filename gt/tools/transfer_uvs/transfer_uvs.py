"""
 GT Transfer UVs - Script for exporting/importing or transferring UVs
 github.com/TrevisanGMW - 2021-06-22
 Tested on Maya 2020.4 - Windows 10
"""

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2 import QtWidgets, QtGui, QtCore
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide import QtWidgets, QtGui, QtCore
    from PySide.QtGui import QIcon, QWidget

import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as OpenMayaUI
import maya.OpenMaya as OpenMaya
import logging
import random
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_transfer_uvs")
logger.setLevel(logging.INFO)

# Script Name
script_name = 'GT - Transfer UVs'

# Script Version
script_version = "?.?.?"  # Module version (init)

# Python Version
python_version = sys.version_info.major


def build_gui_uv_transfer():
    """ Builds the UI for GT Sphere Types """
    if cmds.window("build_gui_uv_transfer", exists=True):
        cmds.deleteUI("build_gui_uv_transfer")

        # main dialog Start Here =================================================================================

    window_gui_uv_transfer = cmds.window("build_gui_uv_transfer", title=script_name + ' - (v' + script_version + ')',
                                         titleBar=True, minimizeButton=False, maximizeButton=False, sizeable=True)
    cmds.window(window_gui_uv_transfer, e=True, s=True, wh=[1, 1])
    content_main = cmds.columnLayout(adj=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 200)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 145), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(' ', bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_uv_transfer())
    cmds.separator(h=10, p=content_main)  # Empty Space

    cmds.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 200), (2, 100), (3, 10)], cs=[(1, 10), (2, 5), (3, 5)])

    cmds.separator(h=5, p=content_main, st="none")
    cmds.rowColumnLayout(p=content_main, numberOfColumns=3, columnWidth=[(1, 100), (2, 100), (3, 10)],
                         cs=[(1, 10), (2, 5)])
    cmds.separator(h=3, p=content_main, st="none")
    cmds.button(l="Export UVs", c=lambda x: uv_export(), w=100)
    cmds.button(l="Import UVs", c=lambda x: uv_import())

    cmds.rowColumnLayout(p=content_main, numberOfColumns=1, columnWidth=[(1, 205), (2, 1), (3, 10)],
                         cs=[(1, 10), (2, 5), (3, 5)])
    cmds.button(l="Transfer from Source to Target(s)", c=lambda x: uv_transfer_source_target(), w=100)
    cmds.separator(h=10, st="none")

    # Show and Lock Window
    cmds.showWindow(window_gui_uv_transfer)
    cmds.window(window_gui_uv_transfer, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_gui_uv_transfer)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/uvChooser.svg')

    widget.setWindowIcon(icon)

    # main dialog Ends Here =================================================================================


def uv_import():
    """ Imports an OBJ file containing UVs (It meshes should be identical for this to work) """
    # Validate
    is_valid = False

    selection = cmds.ls(selection=True)

    if len(selection) > 0:
        is_valid = True
    else:
        cmds.warning('Please select at least one target mesh.')

    function_name = 'GT Import UVs'
    cmds.undoInfo(openChunk=True, chunkName=function_name)

    try:
        if is_valid:
            file_name = cmds.fileDialog2(fileFilter=script_name + " - Obj File (*.obj)", dialogStyle=2, fileMode=1,
                                         okCaption='Import',
                                         caption='Importing Obj with UVs for "' + script_name + '"') or []

            if len(file_name) > 0:
                # uv_file = file_name[0]
                file_exists = True
            else:
                file_exists = False

            if file_exists:
                # try:
                import_ns = 'tempObj_' + str(int(random.random() * 1000)) + '_'
                cmds.file(file_name, i=True, type='OBJ', ignoreVersion=True, ra=True, mergeNamespacesOnClash=False,
                          namespace=import_ns, options='obj', pr=True, importTimeRange='combine')

                imported_objects = cmds.ls(import_ns + ":*")
                imported_shapes = cmds.ls(imported_objects, type='mesh')

                if len(imported_shapes) > 0:
                    error_occurred = False
                    transfer_count = 0
                    for obj in selection:
                        try:
                            transfer_history = cmds.transferAttributes(imported_objects[0], obj, transferPositions=0,
                                                                       transferNormals=0, transferUVs=2,
                                                                       transferColors=2, sampleSpace=4, searchMethod=3,
                                                                       colorBorders=1)
                            history = cmds.listHistory(obj)
                            intermediate_objs = []
                            for hist in history:
                                if cmds.objectType(hist) == 'mesh':
                                    if cmds.objExists(hist + '.intermediateObject'):
                                        if cmds.getAttr(hist + '.intermediateObject') is True:
                                            intermediate_objs.append(hist)

                            for i_obj in intermediate_objs:
                                cmds.setAttr(i_obj + '.intermediateObject', 0)
                                cmds.transferAttributes(imported_objects[0], i_obj, transferPositions=0,
                                                        transferNormals=0, transferUVs=2, transferColors=2,
                                                        sampleSpace=4, searchMethod=3, colorBorders=1)
                                cmds.delete(i_obj, constructionHistory=True)
                                cmds.setAttr(i_obj + '.intermediateObject', 1)

                            try:
                                cmds.delete(transfer_history)
                            except Exception as e:
                                logger.debug(str(e))

                            if are_uvs_identical(imported_objects[0], obj):
                                transfer_count += 1
                        except Exception as e:
                            logger.debug(str(e))
                            error_occurred = True
                    cmds.delete(imported_objects)
                    cmds.select(selection)

                    unique_message = '<' + str(random.random()) + '>'
                    if transfer_count == 1:
                        unique_message += '<span style=\"color:#FF0000;text-decoration:underline;\">'
                        unique_message += str(transfer_count)
                        unique_message += '</span><span style=\"color:#FFFFFF;\"> ' \
                                          'object received transferred UVs.</span>'
                        cmds.inViewMessage(amg=unique_message, pos='botLeft', fade=True, alpha=.9)
                        sys.stdout.write(str(transfer_count) + ' object received transferred UVs.')
                    else:
                        unique_message += '<span style=\"color:#FF0000;text-decoration:underline;\">'
                        unique_message += str(transfer_count)
                        unique_message += '</span><span style=\"color:#FFFFFF;\"> ' \
                                          'objects received transferred UVs.</span>'
                        cmds.inViewMessage(amg=unique_message, pos='botLeft', fade=True, alpha=.9)
                        sys.stdout.write(str(transfer_count) + ' objects received transferred UVs.')
                    if error_occurred:
                        warning = 'Some UVs were not transferred as expected, please make sure you\'re using '
                        warning += 'identical meshes. (Consider its history and intermediate objects)'
                        cmds.warning(warning)

                    # Clean Up Imported Objects
                    delete_temp_namespace(import_ns)
                else:
                    warning = "Imported Mesh with UVs couldn't be accessed. Please make sure it was exported correctly."
                    cmds.warning(warning)
            else:
                cmds.warning("Couldn't read the file. Please make sure the selected file is accessible.")
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def uv_transfer_source_target():
    """ Transfers UVs from a source object to target objects """
    # Validate
    is_valid = False

    selection = cmds.ls(selection=True)

    if len(selection) > 1:
        is_valid = True
    else:
        cmds.warning('Please select at least one source and one target.')

    if is_valid:
        function_name = 'GT Transfer UVs'
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        try:
            error_occurred = False
            transfer_count = 0
            for obj in selection:
                if obj != selection[0]:
                    try:
                        transfer_history = cmds.transferAttributes(selection[0], obj, transferPositions=0,
                                                                   transferNormals=0, transferUVs=2, transferColors=2,
                                                                   sampleSpace=4, searchMethod=3, colorBorders=1)

                        history = cmds.listHistory(obj)
                        intermediate_objs = []
                        for hist in history:
                            if cmds.objectType(hist) == 'mesh':
                                if cmds.objExists(hist + '.intermediateObject'):
                                    if cmds.getAttr(hist + '.intermediateObject') is True:
                                        intermediate_objs.append(hist)

                        logger.debug(str(intermediate_objs))
                        for i_obj in intermediate_objs:
                            cmds.setAttr(i_obj + '.intermediateObject', 0)
                            cmds.transferAttributes(selection[0], i_obj, transferPositions=0, transferNormals=0,
                                                    transferUVs=2, transferColors=2, sampleSpace=4, searchMethod=3,
                                                    colorBorders=1)
                            cmds.delete(i_obj, constructionHistory=True)
                            cmds.setAttr(i_obj + '.intermediateObject', 1)
                        try:
                            cmds.delete(transfer_history)
                        except Exception as e:
                            logger.debug(str(e))

                        if are_uvs_identical(selection[0], obj):
                            transfer_count += 1

                    except Exception as e:
                        logger.debug(str(e))
                        error_occurred = True
            unique_message = '<' + str(random.random()) + '>'
            if transfer_count == 1:
                unique_message += '<span style=\"color:#FF0000;text-decoration:underline;\">'
                unique_message += str(transfer_count)
                unique_message += '</span><span style=\"color:#FFFFFF;\"> object received transferred UVs.</span>'
                cmds.inViewMessage(amg=unique_message, pos='botLeft', fade=True, alpha=.9)
                sys.stdout.write(str(transfer_count) + ' object received transferred UVs.')
            else:
                unique_message += '<span style=\"color:#FF0000;text-decoration:underline;\">'
                unique_message += str(transfer_count)
                unique_message += '</span><span style=\"color:#FFFFFF;\"> objects received transferred UVs.</span>'
                cmds.inViewMessage(amg=unique_message, pos='botLeft', fade=True, alpha=.9)
                sys.stdout.write(str(transfer_count) + ' objects received transferred UVs.')
            if error_occurred:
                warning = 'Some UVs were not transferred as expected, please make sure '
                warning += 'you\'re using identical meshes. (Consider its history and intermediate objects)'
                cmds.warning(warning)
        except Exception as e:
            cmds.warning(str(e))
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=function_name)


def uv_export():
    """ Exports an OBJ file containing the model and UVs to be imported in another scene/model. """
    # Validate Proxy and Write file
    is_valid = False
    successfully_created_file = False

    selection = cmds.ls(selection=True)

    # Determine naming and validate
    if len(selection) == 1:
        shapes = cmds.listRelatives(selection[0], shapes=True, fullPath=True) or []
        if len(shapes) > 0:
            if cmds.objectType(shapes[0]) == 'mesh':
                is_valid = True
            else:
                cmds.warning('Please select an object of the type "Mesh".')
    elif len(selection) == 0:
        cmds.warning('Please select at least one object.')
    else:
        cmds.warning('Please select only one object.')

    uv_file = None
    if is_valid:
        file_name = cmds.fileDialog2(fileFilter=script_name + " - OBJ File (*.obj)", dialogStyle=2,
                                     okCaption='Export UVs',
                                     caption='Exporting OBJ with UVs for "' + script_name + '"') or []
        if len(file_name) > 0:
            uv_file = file_name[0]
            successfully_created_file = True

    if successfully_created_file and is_valid:
        try:
            cmds.file(uv_file, pr=1, typ="OBJexport", es=1, f=True, op="materials=0")
            unique_message = '<' + str(random.random()) + '>'
            unique_message += '<span style=\"color:#FF0000;text-decoration:underline;\">'
            unique_message += 'UV Obj</span><span style=\"color:#FFFFFF;\"> exported.</span>'
            cmds.inViewMessage(amg=unique_message, pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('UV Obj exported to the file "' + uv_file + '".')
        except Exception as e:
            logger.info(str(e))
            successfully_created_file = False
            logger.debug('successfully_created_file' + str(successfully_created_file))
            cmds.warning("Couldn't write to file. Please make sure the exporting directory is accessible.")


def delete_temp_namespace(temp_namespace):
    """
    Deletes the provided namespace
    
                Parameters:
                    temp_namespace (string): Namespace to be deleted
    """
    default_namespaces = ['UI', 'shared']

    def num_children(namespace):
        """ Used as a sort key, this will sort namespaces by how many children they have. """
        return namespace.count(':')

    namespaces = [namespace for namespace in cmds.namespaceInfo(lon=True, r=True) if
                  namespace not in default_namespaces]

    # Reverse List
    namespaces.sort(key=num_children, reverse=True)  # So it does the children first

    for namespace in namespaces:
        if namespace not in default_namespaces and namespace == temp_namespace:
            mel.eval('namespace -mergeNamespaceWithRoot -removeNamespace "' + namespace + '";')


def open_transfer_uvs_docs():
    """ Opens a web browser with the docs about this script """
    cmds.showHelp('https://github.com/TrevisanGMW/gt-tools/tree/release/docs#-gt-transfer-uvs-', absolute=True)


def get_uv_shells(obj):
    """
    Returns a list with all UV sets
    
            Returns:
                all_sets = A list with all sets
    """
    selection = OpenMaya.MSelectionList()
    selection.add(obj)
    sel_iter = OpenMaya.MItSelectionList(selection, OpenMaya.MFn.kMesh)
    shape_path = OpenMaya.MDagPath()
    sel_iter.getDagPath(shape_path)
    mesh_node = shape_path.fullPathName()
    uv_sets = cmds.polyUVSet(mesh_node, query=True, allUVSets=True)
    all_sets = []
    for uv_set in uv_sets:
        shape_fn = OpenMaya.MFnMesh(shape_path)
        shells = OpenMaya.MScriptUtil()
        shells.createFromInt(0)
        nb_uv_shells = shells.asUintPtr()

        u_array = OpenMaya.MFloatArray()  # U coordinates
        v_array = OpenMaya.MFloatArray()  # V coordinates
        shell_ids = OpenMaya.MIntArray()  # The container for the uv shell Ids

        shape_fn.getUVs(u_array, v_array)
        shape_fn.getUvShellsIds(shell_ids, nb_uv_shells, uv_set)

        shells = {}
        for i, n in enumerate(shell_ids):
            if n in shells:
                shells[n].append('%s.map[%i]' % (obj, i))
            else:
                shells[n] = ['%s.map[%i]' % (obj, i)]
        all_sets.append({uv_set: shells})
    return all_sets


def are_uvs_identical(obj_a, obj_b):
    """
    Compares the UVs of objects A and B and returns True if they are different or False if they are not.
    
            Returns:
                is_identical(bool) : True if objects are different
    """
    is_identical = True

    obj_a_uvs = get_uv_shells(obj_a)
    obj_b_uvs = get_uv_shells(obj_b)

    if len(obj_a_uvs) > 0 and len(obj_b_uvs) > 0:
        uvs_a_list = obj_a_uvs[0].get(list(obj_a_uvs[0].keys())[0])[0]
        uvs_b_list = obj_b_uvs[0].get(list(obj_b_uvs[0].keys())[0])[0]

        uv_pairs = zip(uvs_a_list, uvs_b_list)

        for uv_pair in uv_pairs:
            if is_identical:
                uv_sample_a = cmds.polyEditUV(uv_pair[0], query=True)
                uv_sample_b = cmds.polyEditUV(uv_pair[1], query=True)
                if uv_sample_a != uv_sample_b:
                    is_identical = False

    return is_identical


# Creates Help GUI
def build_gui_help_uv_transfer():
    window_name = "build_gui_help_uv_transfer"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    cmds.columnLayout("main_column", p=window_name)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column")  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")  # Title Column
    cmds.text(script_name + " Help", bgc=title_bgc_color, fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column")  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")

    cmds.text(l='Script used to quickly transfer UVs between objects.\nIt allows you to export or import UVs or'
                ' transfer\n them from an object to other objects in the scene.\n\nThis script automatically bakes '
                'the UVs onto the\n intermediate object allowing you to transfer UVs\nwithout generating history.',
              align="center")
    cmds.separator(h=15, style='none')  # Empty Space

    cmds.text(l='Export UVs', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='Exports an OBJ file containing the model and its UVs\n(similar to simply exporting and OBJ file '
                'through the file menu)', align="center", font='smallPlainLabelFont')

    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='Import UVs', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='Imports the previously exported OBJ file and transfers\n its UVs to the intermediate object '
                'of your selection.\nIt allows you to import the UVs without generating history.',
              align="center", font='smallPlainLabelFont')

    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='Transfer from Source to Target(s)', align="center", fn="tinyBoldLabelFont")
    cmds.text(l='Allows you to quickly transfer UVs from the first object\nin your selection to the other objects '
                'in the same selection.\n Thus, you first select your source, then your targets.\n '
                'This method will also use the intermediate object,\n so no construction history will be left behind.',
              font='smallPlainLabelFont')

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


# Build UI
if __name__ == "__main__":
    build_gui_uv_transfer()
