"""

 GT Utilities
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-09-13
 Functions were named with a "gtu" (GT Utilities) prefix to avoid conflicts.
 
 1.1 - 2020-10-17
 Added move pivot to bottom/top
 Added copy/paste material
 Added move to origin
 
 1.2 - 2020-10-21
 Updated reset transform to better handle translate
 Added Uniform LRA Toggle
 Changed the order of the functions to match the menu
 
 1.3 - 2020-11-11
 Updates "gtu_import_references" to better handle unloaded references
 Added "gtu_remove_references"
 Added "gtu_combine_curves"
 Added "gtu_separate_curves"
 
 To Do:
 Add proper error handling to all functions.
 New functions:
    Reset Display Type and Color
    Find/Rename non-unique names - Enforce unique names
    Remove Custom Colors - select object types, outliner or viewport - colorPickCursor.png - use string to determine a list of types
    Assign lambert to everything function (Maybe assing to objects missing shaders)
    Add Unlock all attributes
    Add unhide attributes (provide list?)
    Add Remove pasted_ function
    Add assign checkboard function (already in bonus tools > rendering)
    Force focus (focus without looking at children)
    Brute force clean models (export OBJ and reimport)
 New options:
    Import all references : Add function to use a string to ignore certain references
    Reset Transforms : Add reset only translate, rotate or scale
    Delete all keyframes : Include option to delete or not set driven keys
    Reset persp camera : Reset all other attributes too (including transform?)
    Delete Display Layers : only empty? ignore string?
    Delete Namespaces : only empty? ignore string?
    
"""
import maya.cmds as cmds
import maya.mel as mel
from maya import OpenMayaUI as omui

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget
    
# Script Version
gtu_script_version = "1.3"
    
''' ____________________________ General Functions ____________________________'''
def gtu_reload_file():
    ''' Reopens the opened file (to revert back any changes done to the file) '''        
    if cmds.file(query=True, exists=True): # Check to see if it was ever saved
                file_path = cmds.file(query=True, expandName=True)
                if file_path is not None:
                    cmds.file(file_path, open=True, force=True)
    else:
        cmds.warning('File was never saved.')
        
def gtu_open_resource_browser():
    ''' Opens Maya's Resource Browser '''        
    try:
        import maya.app.general.resourceBrowser as resourceBrowser

        resourceBrowser.resourceBrowser().run()
    except:
        pass
        
def gtu_import_references():
    ''' Imports all references ''' 
    try:
        errors = ''
        refs = cmds.ls(rf=True)
        for i in refs:
            try:
                r_file = cmds.referenceQuery(i, f=True)
                cmds.file(r_file, importReference=True)
            except Exception as e:
                errors += str(e) + '(' + r_file + ')\n'
    except:
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")
    if errors != '':
        cmds.warning('Not all references were imported. Open the script editor for more information.')
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)
        

def gtu_remove_references():
    ''' Removes all references ''' 
    try:
        errors = ''
        refs = cmds.ls(rf=True)
        for i in refs:
            try:
                r_file = cmds.referenceQuery(i, f=True)
                cmds.file(r_file, removeReference=True)
            except Exception as e:
                errors += str(e) + '(' + r_file + ')\n'
    except:
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")
    if errors != '':
        cmds.warning('Not all references were removed. Open the script editor for more information.')
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)


def gtu_uniform_lra_toggle():
    ''' 
    Makes the visibility of the Local Rotation Axis uniform among 
    the selected objects according to the current state of the majority of them.  
    '''

    function_name = 'GTU Uniform LRA Toggle'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        errors = ''
        selection = cmds.ls(selection=True)
        
        inactive_lra = []
        active_lra = []
        
        for obj in selection:
            try:
                current_lra_state = cmds.getAttr(obj + '.displayLocalAxis')
                if current_lra_state:
                    active_lra.append(obj)
                else:
                    inactive_lra.append(obj)
            except Exception as e:
                errors += str(e) + '\n'
           
        if len(active_lra) == 0:
            for obj in inactive_lra:
                try:
                    cmds.setAttr(obj + '.displayLocalAxis', 1)
                except Exception as e:
                    errors += str(e) + '\n'
        elif len(inactive_lra) == 0:
            for obj in active_lra:
                try:
                    cmds.setAttr(obj + '.displayLocalAxis', 0)
                except Exception as e:
                    errors += str(e) + '\n'
        elif len(active_lra) > len(inactive_lra):
            for obj in inactive_lra:
                try:
                    cmds.setAttr(obj + '.displayLocalAxis', 1)
                except Exception as e:
                    errors += str(e) + '\n'
        else:
            for obj in active_lra:
                try:
                    cmds.setAttr(obj + '.displayLocalAxis', 0)
                except Exception as e:
                    errors += str(e) + '\n'
        

        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning('The script couldn\'t read or write some LRA states. Open script editor for more info.')
    except:
        pass
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def gtu_combine_curves():
    ''' 
    Moves the shape objects of all selected curves under a single group (combining them) 
    '''
    errors = ''
    try:
        function_name = 'GTU Combine Curves'
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        selection = cmds.ls(sl = True, absoluteName=True)
        valid_selection = True
        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) != 'nurbsCurve':
                    valid_selection = False
                    cmds.warning('Make sure you selected only curves.')
            
        if valid_selection and len(selection) < 2:
            cmds.warning('You need to select at least two curves.')
            valid_selection = False
            
        if valid_selection:
            shapes = cmds.listRelatives(shapes=True, fullPath=True)
            for obj in range(len(selection)):
                cmds.makeIdentity(selection[obj], apply=True, rotate=True, scale=True, translate=True)

            group = cmds.group(empty=True, world=True, name=selection[0])
            cmds.select(shapes[0])
            for obj in range(1, (len(shapes))):
                cmds.select(shapes[obj], add=True)
                
            cmds.select(group, add=True) 
            cmds.parent(relative=True, shape=True)
            cmds.delete(selection)   
         
    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occured when combining the curves. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)

def gtu_separate_curves():
    ''' 
    Moves the shapes instead of a curve to individual transforms (separating curves) 
    '''
    errors = ''
    try:
        function_name = 'GTU Separate Curves'
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        selection = cmds.ls(sl = True)
        valid_selection = True
        
        curve_shapes = []
        
        if len(selection) < 1:
            valid_selection = False
            cmds.warning('You need to select at least one curve.')
            
        
        if valid_selection:
            for obj in selection:
                shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                for shape in shapes:
                    if cmds.objectType(shape) == 'nurbsCurve':
                        curve_shapes.append(shape)
            
            if len(curve_shapes) == 0:
                cmds.warning('You need to select at least one curve.')
            elif len(curve_shapes) > 1:
                for obj in curve_shapes:
                    cmds.makeIdentity(obj, apply=True, rotate=True, scale=True, translate=True)
                    group = cmds.group(empty=True, world=True, name=obj.replace('Shape',''))
                    cmds.parent(obj, group, relative=True, shape=True)
            else:
                cmds.warning('The selected curve contains only one shape.')
                
            

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occured when combining the curves. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)



''' ____________________________ Material Functions ____________________________'''

def gtu_copy_material():
    ''' Copies selected material to clipboard ''' 
    selection = cmds.ls(selection=True)
    try:
        mel.eval('ConvertSelectionToFaces;')
        cmds.polyClipboard( copy=True, shader=True )
        cmds.inViewMessage( amg='Material <hl>copied</hl> to the clipboard.', pos='midCenterTop', fade=True )
    except:
        cmds.warning('Couldn\'t copy material. Make sure you selected an object or component before copying.')
    cmds.select(selection)
    
def gtu_paste_material():
    ''' Copies selected material to clipboard ''' 
    try:
        cmds.polyClipboard( paste=True, shader=True )
    except:
        cmds.warning('Couldn\'t paste material. Make sure you copied a material first, then selected the target objects or components.')

''' ____________________________ Layout Functions ____________________________'''

def gtu_move_pivot_to_top():
    ''' Moves pivot point to the top of the boundary box '''     
    selection = cmds.ls(selection=True) 

    for obj in selection:
        bbox = cmds.exactWorldBoundingBox(obj) # extracts bounding box
        top = [(bbox[0] + bbox[3])/2, bbox[4], (bbox[2] + bbox[5])/2] # find top
        cmds.xform(obj, piv=top, ws=True) 
        
def gtu_move_pivot_to_base():
    ''' Moves pivot point to the base of the boundary box '''     
    selection = cmds.ls(selection=True) 

    for obj in selection:
        bbox = cmds.exactWorldBoundingBox(obj) # extracts bounding box
        bottom = [(bbox[0] + bbox[3])/2, bbox[1], (bbox[2] + bbox[5])/2] # find bottom
        cmds.xform(obj, piv=bottom, ws=True) # sends pivot to bottom
        
def gtu_move_to_origin():
    ''' Moves selected objects back to origin '''  
    function_name = 'GTU Move to Origin'
    errors = ''
    cmds.undoInfo(openChunk=True, chunkName=function_name) # Start undo chunk
    selection = cmds.ls(selection=True) 
    try:   
        for obj in selection:
            try:
                cmds.move(0, 0, 0, obj, a=True,rpr=True) #rpr flag moves it according to the pivot
            except Exception as e:
                errors += str(e) + '\n'
        if errors != '':
                print('#### Errors: ####')
                print(errors)
                cmds.warning('Some objects could not be moved to the origin. Open the script editor for a list of errors.')
    except:
        pass
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
        
''' ____________________________ Reset Functions ____________________________'''

def gtu_reset_transforms():
    '''
    Reset transforms. 
    It checks for incomming connections, then set the attribute to 0 if there are none
    It resets transforms, but ignores translate for joints.
    '''
    function_name = 'GTU Reset Transforms'
    errors = ''
    cmds.undoInfo(openChunk=True, chunkName=function_name) # Start undo chunk
    
    selection = cmds.ls(selection=True)

    def reset_transforms():
        for obj in selection:
            try:
                type_check = cmds.listRelatives(obj, children=True) or []

                if len(type_check) > 0 and cmds.objectType(type_check) != 'joint':
                    obj_connection_tx = cmds.listConnections( obj + '.tx', d=False, s=True ) or []
                    if not len(obj_connection_tx) > 0:
                        if cmds.getAttr(obj + '.tx', lock=True) is False:
                            cmds.setAttr(obj + '.tx', 0)
                    obj_connection_ty = cmds.listConnections( obj + '.ty', d=False, s=True ) or []
                    if not len(obj_connection_ty) > 0:
                        if cmds.getAttr(obj + '.ty', lock=True) is False:
                            cmds.setAttr(obj + '.ty', 0)
                    obj_connection_tz = cmds.listConnections( obj + '.tz', d=False, s=True ) or []
                    if not len(obj_connection_tz) > 0:
                        if cmds.getAttr(obj + '.tz', lock=True) is False:
                            cmds.setAttr(obj + '.tz', 0)
                
                obj_connection_rx = cmds.listConnections( obj + '.rotateX', d=False, s=True ) or []
                if not len(obj_connection_rx) > 0:
                    if cmds.getAttr(obj + '.rotateX', lock=True) is False:
                        cmds.setAttr(obj + '.rotateX', 0)
                obj_connection_ry = cmds.listConnections( obj + '.rotateY', d=False, s=True ) or []
                if not len(obj_connection_ry) > 0:
                    if cmds.getAttr(obj + '.rotateY', lock=True) is False:
                        cmds.setAttr(obj + '.rotateY', 0)
                obj_connection_rz = cmds.listConnections( obj + '.rotateZ', d=False, s=True ) or []
                if not len(obj_connection_rz) > 0:
                    if cmds.getAttr(obj + '.rotateZ', lock=True) is False:
                        cmds.setAttr(obj + '.rotateZ', 0)

                obj_connection_sx = cmds.listConnections( obj + '.scaleX', d=False, s=True ) or []
                if not len(obj_connection_sx) > 0:
                    if cmds.getAttr(obj + '.scaleX', lock=True) is False:
                        cmds.setAttr(obj + '.scaleX', 1)
                obj_connection_sy = cmds.listConnections( obj + '.scaleY', d=False, s=True ) or []
                if not len(obj_connection_sy) > 0:
                    if cmds.getAttr(obj + '.scaleY', lock=True) is False:
                        cmds.setAttr(obj + '.scaleY', 1)
                obj_connection_sz = cmds.listConnections( obj + '.scaleZ', d=False, s=True ) or []
                if not len(obj_connection_sz) > 0:
                    if cmds.getAttr(obj + '.scaleZ', lock=True) is False:
                        cmds.setAttr(obj + '.scaleZ', 1)
            except Exception as e:
                errors = errors + str(e + '\n')
        
    try:
        reset_transforms()
    except Exception as e:
        pass
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
        
    if errors != '':
        cmds.warning('Some objects couldn\'t be reset. Open the script editor for a list of errors.')


def gtu_reset_joint_sizes():
    ''' Resets the radius attribute back to one in all joints, then changes the global multiplier (jointDisplayScale) back to one '''
    try:
        desired_size = 1
        all_joints = cmds.ls(type='joint')
        for obj in all_joints:
            if cmds.objExists(obj):
                if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                    cmds.setAttr(obj + '.radius', 1)
                    
                if cmds.getAttr(obj + ".v" ,lock=True) is False:
                    cmds.setAttr(obj + '.v', 1)   
        cmds.jointDisplayScale(1)

    except Exception as exception:
        raise exception
        
def gtu_reset_persp_shape_attributes():
    '''
    If persp shape exists (default camera), reset its attributes
    '''
    if cmds.objExists('perspShape'):
        try:
            cmds.setAttr('perspShape' + ".focalLength", 35)
            cmds.setAttr('perspShape' + ".verticalFilmAperture", 0.945)
            cmds.setAttr('perspShape' + ".horizontalFilmAperture", 1.417)
            cmds.setAttr('perspShape' + ".lensSqueezeRatio", 1)
            cmds.setAttr('perspShape' + ".fStop", 5.6)
            cmds.setAttr('perspShape' + ".focusDistance", 5)
            cmds.setAttr('perspShape' + ".shutterAngle", 144)
            cmds.setAttr('perspShape' + ".locatorScale", 1)
            cmds.setAttr('perspShape' + ".nearClipPlane", 0.100)
            cmds.setAttr('perspShape' + ".farClipPlane", 10000.000)
            cmds.setAttr('perspShape' + ".cameraScale", 1)
            cmds.setAttr('perspShape' + ".preScale", 1)
            cmds.setAttr('perspShape' + ".postScale", 1)
            cmds.setAttr('perspShape' + ".depthOfField", 0)
        except:
            pass
            
''' ____________________________ Delete Functions ____________________________'''   

def gtu_delete_namespaces():
    '''Deletes all namespaces in the scene'''
    function_name = 'GTU Delete All Namespaces'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        default_namespaces = ['UI', 'shared']

        def num_children(namespace):
            '''Used as a sort key, this will sort namespaces by how many children they have.'''
            return namespace.count(':')

        namespaces = [namespace for namespace in cmds.namespaceInfo(lon=True, r=True) if namespace not in default_namespaces]
        
        # Reverse List
        namespaces.sort(key=num_children, reverse=True) # So it does the children first

        print(namespaces)

        for namespace in namespaces:
            if namespace not in default_namespaces:
                mel.eval('namespace -mergeNamespaceWithRoot -removeNamespace "' + namespace + '";')
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
        
def gtu_delete_display_layers():
    ''' Deletes all display layers '''
    display_layers = cmds.ls(type = 'displayLayer')
    for layer in display_layers:
        if layer != 'defaultLayer':
            cmds.delete(layer)
            
def gtu_delete_keyframes():
    '''Deletes all nodes of the type "animCurveTA" (keyframes)'''
    keys_ta = cmds.ls(type='animCurveTA')
    keys_tl = cmds.ls(type='animCurveTL')
    keys_tt = cmds.ls(type='animCurveTT')
    keys_tu = cmds.ls(type='animCurveTU')
    #keys_ul = cmds.ls(type='animCurveUL') # Use optionVar to determine if driven keys should be deleted
    #keys_ua = cmds.ls(type='animCurveUA')
    #keys_ut = cmds.ls(type='animCurveUT')
    #keys_uu = cmds.ls(type='animCurveUU')
    all_keyframes = keys_ta + keys_tl + keys_tt + keys_tu
    for obj in all_keyframes:
        try:
            cmds.delete(obj)
        except:
            pass
            
''' ____________________________ External Functions ____________________________'''   

def gtu_build_gui_about_gt_tools():
    ''' Creates "About" window for the GT Tools menu ''' 
     
    stored_gt_tools_version_exists = cmds.optionVar(exists=("gt_tools_version"))

    # Define Version
    if stored_gt_tools_version_exists:
        gt_version = cmds.optionVar(q=("gt_tools_version"))
    else:
        gt_version = '?'
     
    window_name = "gtu_build_gui_about_gt_tools"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title="About - GT Tools", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    cmds.columnLayout("main_column", p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column") # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column") # Title Column
    cmds.text("GT Tools", bgc=[0,.5,0],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column") # Empty Space
        
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.text(l='Version Installed: ' + gt_version, align="center", fn="boldLabelFont")
    cmds.separator(h=5, style='none') # Empty Space
    cmds.text(l='GT Tools is a free collection of Maya scripts', align="center")
    
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='About:', align="center", fn="boldLabelFont")
    cmds.text(l='The pull-down menu provides easy access to a variety of \ntools, and each sub-menus has been organized to\ncontain related tools.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='All of these items are supplied as is.\nYou alone are soley responsible for any issues.\nUse at your own risk.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='Hopefully these scripts are helpful to you\nas they are to me.', align="center")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p="main_column")
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p="main_column")
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=7, style='none') # Empty Space
    
    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)
            
            
''' ____________________________ Testing ____________________________'''   
#gtu_reload_file()
#gtu_open_resource_browser()
#gtu_import_references()
#gtu_remove_references()
#gtu_uniform_lra_toggle()
#gtu_combine_curves()
#gtu_separate_curves()

#gtu_copy_material()
#gtu_paste_material()

#gtu_move_pivot_to_top()
#gtu_move_pivot_to_base()
#gtu_move_to_origin()

#gtu_reset_joint_sizes()
#gtu_reset_transforms()
#gtu_reset_persp_shape_attributes()  

#gtu_delete_namespaces()
#gtu_delete_display_layers()
#gtu_delete_keyframes()

#gtu_build_gui_about_gt_tools()