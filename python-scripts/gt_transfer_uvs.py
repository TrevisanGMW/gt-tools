"""
 GT Transfer UVs - Script for exporting/importing or transfering UVs
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2021-06-22 - github.com/TrevisanGMW
 Tested on Maya 2020.4 - Windows 10
 
 1.1 - 2021-06-22
 Iterate through all intermediate objects to guarantee they all have the same UVs

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
import maya.OpenMayaUI as omui
import random
import sys
import os

# Script Name
script_name = 'GT - Transfer UVs'

# Script Version
script_version = '1.1'

#Python Version
python_version = sys.version_info.major

def build_gui_uv_transfer():
    ''' Builds the UI for GT Sphere Types '''
    if cmds.window("build_gui_uv_transfer", exists =True):
        cmds.deleteUI("build_gui_uv_transfer")    

    # main dialog Start Here =================================================================================

    build_gui_uv_transfer = cmds.window("build_gui_uv_transfer", title=script_name + ' - (v' + script_version + ')',\
                          titleBar=True,minimizeButton=False,maximizeButton=False, sizeable =True)
    cmds.window(build_gui_uv_transfer, e=True, s=True, wh=[1,1])
    content_main = cmds.columnLayout(adj = True)
    
    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 200)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 145), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(' ', bgc=title_bgc_color) # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color,  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:open_transfer_uvs_docs())
    cmds.separator(h=10, p=content_main) # Empty Space
    
    cmds.rowColumnLayout(numberOfColumns=1, columnWidth=[(1, 200), (2, 100),(3,10)], cs=[(1,10),(2,5),(3,5)])
        
    cmds.separator(h=5, p=content_main, st="none" )
    cmds.rowColumnLayout( p=content_main, numberOfColumns=3, columnWidth=[(1, 100), (2, 100),(3,10)], cs=[(1,10),(2,5)])
    cmds.separator(h=3, p=content_main, st="none" )
    cmds.button( l ="Export UVs", c=lambda x:uv_export(), w=100)
    cmds.button( l ="Import UVs", c=lambda x:uv_import())

    cmds.rowColumnLayout(p=content_main, numberOfColumns=1, columnWidth=[(1, 205), (2, 1),(3,10)], cs=[(1,10),(2,5),(3,5)])
    cmds.button( l ="Transfer from Source to Target(s)", c=lambda x:uv_transfer_source_target(), w=100)
    cmds.separator(h=10, st="none" )
 
 
    # Show and Lock Window
    cmds.showWindow(build_gui_uv_transfer)
    cmds.window(build_gui_uv_transfer, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(build_gui_uv_transfer)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/uvChooser.svg')
    
    widget.setWindowIcon(icon)

    # main dialog Ends Here =================================================================================
    
def uv_import():
    ''' Imports an OBJ file containing UVs (It meshes should be identical for this to work) ''' 
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
            file_name = cmds.fileDialog2(fileFilter=script_name + " - Obj File (*.obj)", dialogStyle=2, fileMode= 1, okCaption= 'Import', caption= 'Importing Obj with UVs for "' + script_name + '"') or []
            
            if len(file_name) > 0:
                uv_file = file_name[0]
                file_exists = True
            else:
                file_exists = False
            
            if file_exists:
                #try: 
                    import_ns = 'tempObj_' + str(int(random.random()*1000)) + '_'
                    cmds.file(file_name, i=True, type='OBJ', ignoreVersion=True, ra=True, mergeNamespacesOnClash=False, namespace=import_ns, options='obj', pr=True, importTimeRange='combine')
                 
                    imported_objects = cmds.ls (import_ns + ":*") 
                    imported_shapes = cmds.ls(imported_objects, type='mesh')
                    
                    if len(imported_shapes) > 0:
                        error_occured = False
                        transfer_count = 0
                        for obj in selection:
                            try:
                                transfer_history = cmds.transferAttributes(imported_objects[0], obj, transferPositions=0, transferNormals=0, transferUVs=2, transferColors=2, sampleSpace=4, searchMethod=3, colorBorders=1)
                                history = cmds.listHistory( obj )
                                intermediate_objs = []
                                for obj in history:
                                    if cmds.objectType(obj) == 'mesh':
                                        if cmds.objExists(obj + '.intermediateObject'):
                                            if cmds.getAttr(obj + '.intermediateObject') == True:
                                                intermediate_objs.append(obj) 
                                
                                for obj in intermediate_objs:
                                    cmds.setAttr(obj + '.intermediateObject', 0)
                                    cmds.transferAttributes(imported_objects[0], obj, transferPositions=0, transferNormals=0, transferUVs=2, transferColors=2, sampleSpace=4, searchMethod=3, colorBorders=1)
                                    cmds.delete(obj, constructionHistory = True)
                                    cmds.setAttr(obj + '.intermediateObject', 1)
                                    
                                try:
                                    cmds.delete(transfer_history)
                                except:
                                    pass
                                    
                                transfer_count += 1
                            except:
                                error_occured = True
                        cmds.delete(imported_objects)
                        cmds.select(selection)
                            
                        unique_message = '<' + str(random.random()) + '>'
                        if transfer_count == 1:
                            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(transfer_count) + '</span><span style=\"color:#FFFFFF;\"> object received transfered UVs.</span>', pos='botLeft', fade=True, alpha=.9)
                        else:
                            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(transfer_count) + '</span><span style=\"color:#FFFFFF;\"> objects received transfered UVs.</span>', pos='botLeft', fade=True, alpha=.9)
                        if error_occured:
                            cmds.warning('Some UVs could not be transfered, please make sure you\'re using identical meshes.')
                            
                        # Clean Up Imported Objects
                        delete_temp_namespace(import_ns)
                    else:
                        cmds.warning('Imported Mesh with UVs couldn\'t be accessed. Please make sure it was exported correctly.')
            else:
                cmds.warning('Couldn\'t read the file. Please make sure the selected file is accessible.')
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)

def uv_transfer_source_target():
    ''' Transfers UVs from a source object to target objects ''' 
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
            error_occured = False
            transfer_count = 0
            for obj in selection:
                if obj != selection[0]:
                    try:
                        transfer_history = cmds.transferAttributes(selection[0], obj, transferPositions=0, transferNormals=0, transferUVs=2, transferColors=2, sampleSpace=4, searchMethod=3, colorBorders=1)

                        history = cmds.listHistory( obj )
                        intermediate_objs = []
                        for obj in history:
                            if cmds.objectType(obj) == 'mesh':
                                if cmds.objExists(obj + '.intermediateObject'):
                                    if cmds.getAttr(obj + '.intermediateObject') == True:
                                        intermediate_objs.append(obj)

                        for obj in intermediate_objs:
                            cmds.setAttr(obj + '.intermediateObject', 0)
                            cmds.transferAttributes(selection[0], obj, transferPositions=0, transferNormals=0, transferUVs=2, transferColors=2, sampleSpace=4, searchMethod=3, colorBorders=1)
                            cmds.delete(obj, constructionHistory = True)
                            cmds.setAttr(obj + '.intermediateObject', 1)
                        
                        try:
                            cmds.delete(transfer_history)
                        except:
                            pass
                        transfer_count += 1
        
                    except Exception as e:
                        error_occured = True
            unique_message = '<' + str(random.random()) + '>'
            if transfer_count == 1:
                cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(transfer_count) + '</span><span style=\"color:#FFFFFF;\"> object received transfered UVs.</span>', pos='botLeft', fade=True, alpha=.9)
            else:
                cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(transfer_count) + '</span><span style=\"color:#FFFFFF;\"> objects received transfered UVs.</span>', pos='botLeft', fade=True, alpha=.9)
            if error_occured:
                cmds.warning('Some UVs could not be transfered, please make sure you\'re using identical meshes.')
        except Exception as e:
            cmds.warning(str(e))
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=function_name)

def uv_export():
    ''' Exports an OBJ file containing the model and UVs to be imported in another scene/model. ''' 
    # Validate Proxy and Write file
    is_valid = False
    successfully_created_file = False
    
    selection = cmds.ls(selection=True)

    # Determine naming and validate
    export_name='untitled'
    if len(selection) == 1:
        shapes = cmds.listRelatives(selection[0], shapes=True, fullPath=True) or []
        if len(shapes) > 0:
            if cmds.objectType(shapes[0]) == 'mesh':
                export_name = selection[-1]
                is_valid = True
            else:
                cmds.warning('Please select an object of the type "Mesh".')
    elif len(selection) == 0:
        cmds.warning('Please select at least one object.')
    else:
        cmds.warning('Please select only one object.')

    if is_valid:
        file_name = cmds.fileDialog2(fileFilter=script_name + " - OBJ File (*.obj)", dialogStyle=2, okCaption= 'Export UVs', caption= 'Exporting OBJ with UVs for "' + script_name + '"') or []
        if len(file_name) > 0:
            uv_file = file_name[0]
            successfully_created_file = True

    if successfully_created_file and is_valid:
        try:
            cmds.file(uv_file, pr=1, typ="OBJexport",es=1, f=True, op="materials=0")
            unique_message = '<' + str(random.random()) + '>'
            cmds.inViewMessage(amg=unique_message + '<span style=\"color:#FF0000;text-decoration:underline;\">UV Obj</span><span style=\"color:#FFFFFF;\"> exported.</span>', pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('UV Obj exported to the file "' + uv_file + '".')
        except Exception as e:
            print (e)
            successfully_created_file = False
            cmds.warning('Couldn\'t write to file. Please make sure the exporting directory is accessible.')
            
def delete_temp_namespace(temp_namespace):
    ''' 
    Deletes the provided namespace
    
                Parameters:
                    temp_namespace (string): Namespace to be deleted
    '''
    default_namespaces = ['UI', 'shared']

    def num_children(namespace):
        ''' Used as a sort key, this will sort namespaces by how many children they have. '''
        return namespace.count(':')

    namespaces = [namespace for namespace in cmds.namespaceInfo(lon=True, r=True) if namespace not in default_namespaces]

    # Reverse List
    namespaces.sort(key=num_children, reverse=True) # So it does the children first

    for namespace in namespaces:
        if namespace not in default_namespaces and namespace == temp_namespace:
            mel.eval('namespace -mergeNamespaceWithRoot -removeNamespace "' + namespace + '";')

def open_transfer_uvs_docs():
        ''' Opens a web browser with the docs about this script '''
        cmds.showHelp ('https://github.com/TrevisanGMW/gt-tools/tree/release/docs#-gt-transfer-uvs-', absolute=True) 
        
# Build UI
if __name__ == "__main__":
    build_gui_uv_transfer()