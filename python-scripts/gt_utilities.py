"""
 GT Utilities
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-09-13
 Functions were named with a "gtu" (GT Utilities) prefix to avoid conflicts.
 
 1.1 - 2020/10/17
 Added move pivot to bottom/top
 Added copy/paste material
 Added move to origin
 
 To Do:
 Add proper error handling to all functions.
 Force focus (focus without looking at children)
 Assign lambert1 to components missing shaders
 Add assign checkboard function (already in bonus tools > rendering)
 Add Remove pasted_ function.
 Enforce unique names
 Add Unlock all attributes
 Add unhide attributes (provide list?)
 Add assign lambert to everything function
 Add delete history function (also non deformer version of it)
 Move all meshes (or other type?) to root/world
 Add options to most functions.
 
     Create functions:
        Normalize/Reset LRA display - menuIconDisplay.png 
        Remove Custom Colors - select object types, outliner or viewport - colorPickCursor.png - use string to determine a list of types
        Find/Rename non-unique names
        
     Create option windows (use optionVars)
        Delete Namespaces
            only empty? ignore string?

        Delete Display Layers
            only empty? ignore string?

        Reset persp camera
            create persp if missing
            reset all other attributes too (including transform?)

        BBox Pivot and Center 
            Add options
            Maybe change the name of the function

        Delete all keyframes
            Include or not set driven keys

        Reset Transforms
            Reset translate? scale? rot? 
        
        (Normalize?)Reset Joint Radius
            LRA, Display Type, Color, etc...
        
        Import all references
            String to ignore certain references
            

    
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
gtu_script_version = 1.1


def gtu_delete_display_layers():
    ''' Deletes all display layers '''
    display_layers = cmds.ls(type = 'displayLayer')
    for layer in display_layers:
        if layer != 'defaultLayer':
            cmds.delete(layer)


def gtu_delete_namespaces():
    '''Deletes all namespaces in the scene'''
    cmds.undoInfo(openChunk=True, chunkName='Delete all namespaces')
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
        cmds.undoInfo(closeChunk=True, chunkName='Delete all namespaces')


def gtu_reset_transforms():
    '''
    Reset transforms. 
    It checks for incomming connections, then set the attribute to 0 if there are none
    Currently affects Joints, meshes and transforms.
    '''
    all_joints = cmds.ls(type='joint')
    all_meshes = cmds.ls(type='mesh')
    all_transforms = cmds.ls(type='transform')
    
    for obj in all_meshes:
        try:
            mesh_transform = ''
            mesh_transform_extraction = cmds.listRelatives(obj, allParents=True) or []
            if len(mesh_transform_extraction) > 0:
                mesh_transform = mesh_transform_extraction[0]
            
            if len(mesh_transform_extraction) > 0 and cmds.objExists(mesh_transform) and 'shape' not in cmds.nodeType(mesh_transform, inherited=True):
                mesh_connection_rx = cmds.listConnections( mesh_transform + '.rotateX', d=False, s=True ) or []
                if not len(mesh_connection_rx) > 0:
                    if cmds.getAttr(mesh_transform + '.rotateX', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.rotateX', 0)
                mesh_connection_ry = cmds.listConnections( mesh_transform + '.rotateY', d=False, s=True ) or []
                if not len(mesh_connection_ry) > 0:
                    if cmds.getAttr(mesh_transform + '.rotateY', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.rotateY', 0)
                mesh_connection_rz = cmds.listConnections( mesh_transform + '.rotateZ', d=False, s=True ) or []
                if not len(mesh_connection_rz) > 0:
                    if cmds.getAttr(mesh_transform + '.rotateZ', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.rotateZ', 0)

                mesh_connection_sx = cmds.listConnections( mesh_transform + '.scaleX', d=False, s=True ) or []
                if not len(mesh_connection_sx) > 0:
                    if cmds.getAttr(mesh_transform + '.scaleX', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.scaleX', 1)
                mesh_connection_sy = cmds.listConnections( mesh_transform + '.scaleY', d=False, s=True ) or []
                if not len(mesh_connection_sy) > 0:
                    if cmds.getAttr(mesh_transform + '.scaleY', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.scaleY', 1)
                mesh_connection_sz = cmds.listConnections( mesh_transform + '.scaleZ', d=False, s=True ) or []
                if not len(mesh_connection_sz) > 0:
                    if cmds.getAttr(mesh_transform + '.scaleZ', lock=True) is False:
                        cmds.setAttr(mesh_transform + '.scaleZ', 1)
        except Exception as e:
            raise e
            
    for jnt in all_joints:
        try:
            joint_connection_rx = cmds.listConnections( jnt + '.rotateX', d=False, s=True ) or []
            if not len(joint_connection_rx) > 0:
                if cmds.getAttr(jnt + '.rotateX', lock=True) is False:
                    cmds.setAttr(jnt + '.rotateX', 0)
            joint_connection_ry = cmds.listConnections( jnt + '.rotateY', d=False, s=True ) or []
            if not len(joint_connection_ry) > 0:
                if cmds.getAttr(jnt + '.rotateY', lock=True) is False:
                    cmds.setAttr(jnt + '.rotateY', 0)
            joint_connection_rz = cmds.listConnections( jnt + '.rotateZ', d=False, s=True ) or []
            if not len(joint_connection_rz) > 0:
                if cmds.getAttr(jnt + '.rotateZ', lock=True) is False:
                    cmds.setAttr(jnt + '.rotateZ', 0)

            joint_connection_sx = cmds.listConnections( jnt + '.scaleX', d=False, s=True ) or []
            if not len(joint_connection_sx) > 0:
                if cmds.getAttr(jnt + '.scaleX', lock=True) is False:
                    cmds.setAttr(jnt + '.scaleX', 1)
            joint_connection_sy = cmds.listConnections( jnt + '.scaleY', d=False, s=True ) or []
            if not len(joint_connection_sy) > 0:
                if cmds.getAttr(jnt + '.scaleY', lock=True) is False:
                    cmds.setAttr(jnt + '.scaleY', 1)
            joint_connection_sz = cmds.listConnections( jnt + '.scaleZ', d=False, s=True ) or []
            if not len(joint_connection_sz) > 0:
                if cmds.getAttr(jnt + '.scaleZ', lock=True) is False:
                    cmds.setAttr(jnt + '.scaleZ', 1)
        except Exception as e:
            raise e

    for obj in all_transforms:
        if 'ctrl' in obj.lower() and 'ctrlgrp' not in obj.lower():
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


def gtu_reset_joint_sizes():
    ''' Resets the radius attribute back to one in all joints, then changes the global multiplier (jointDisplayScale) back to one '''
    try:
        desired_size = 1
        all_joints = cmds.ls(type='joint')
        for obj in all_joints:
            if cmds.objExists(obj):
                if cmds.getAttr(obj + ".radius" ,lock=True) is False:
                    cmds.setAttr(obj + '.radius', 1)
                    #change_obj_color(obj ,rgb_color=(.4,0,.4))
                    
                    # if 'endJnt' in obj:  # Add option to differentiate certain joints (maybe based on a string)
                    #     change_obj_color(obj ,rgb_color=(1,0,0))
                    
                    # Add check here for joint visibility type, it should be skeleton (so it's not invisible or bbox)
                    
                if cmds.getAttr(obj + ".v" ,lock=True) is False:
                    cmds.setAttr(obj + '.v', 1)   
        cmds.jointDisplayScale(1)
        # for obj in all_joints:
        #     if cmds.objExists(obj):
        #         if cmds.getAttr(obj + ".radius" ,lock=True) is False:
        #             cmds.select(obj)
        #             cmds.ls(selection=True)[0]
        #             cmds.setAttr(obj + '.radius', desired_size)
        #             cmds.select(d=True)
        # cmds.jointDisplayScale(1)
    except Exception as exception:
        raise exception
        #pass # Add everything to a string and print accordingly (error handling)
        # cmds.scrollField(output_scroll_field, e=True, clear=True)
        # cmds.scrollField(output_scroll_field, e=True, ip=0, it=str(exception) + '\n')
            
                    
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

def gtu_move_pivot_to_base():
    ''' Moves pivot point to the base of the boundary box '''     
    selection = cmds.ls(selection=True) 

    for obj in selection:
        bbox = cmds.exactWorldBoundingBox(obj) # extracts bounding box
        bottom = [(bbox[0] + bbox[3])/2, bbox[1], (bbox[2] + bbox[5])/2] # find bottom
        cmds.xform(obj, piv=bottom, ws=True) # sends pivot to bottom

def gtu_move_pivot_to_top():
    ''' Moves pivot point to the top of the boundary box '''     
    selection = cmds.ls(selection=True) 

    for obj in selection:
        bbox = cmds.exactWorldBoundingBox(obj) # extracts bounding box
        top = [(bbox[0] + bbox[3])/2, bbox[4], (bbox[2] + bbox[5])/2] # find top
        cmds.xform(obj, piv=top, ws=True) 
        
def gtu_move_to_origin():
    ''' Moves selected objects back to origin '''     
    selection = cmds.ls(selection=True) 

    for obj in selection:
        cmds.move(0, 0, 0, obj, a=True,rpr=True) #rpr flag moves it according to the pivot


def gtu_import_references():
    ''' Imports all references ''' 
    try:
        refs = cmds.ls(rf=True)
        for i in refs:
            r_file = cmds.referenceQuery(i, f=True)
            cmds.file(r_file, importReference=True)
    except:
        cmds.warning("Something went wrong. Maybe you don't have any references to import?") # Handle this better...

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
            
            
#gtu_import_references()
#gtu_delete_display_layers()        
#gtu_delete_namespaces()   
#gtu_reset_transforms()    
#gtu_delete_keyframes()     
#gtu_reset_persp_shape_attributes()         
#gtu_reset_joint_sizes()
#gtu_reload_file()
#gtu_open_resource_browser()
#gtu_import_references()
#gtu_move_to_origin()
#gtu_move_pivot_to_base()
#gtu_move_pivot_to_top()
#gtu_copy_material()
#gtu_paste_material()
#gtu_build_gui_about_gt_tools()