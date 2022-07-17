"""
 GT fSpy Importer - Imports a JSON file exported out of fSpy
 github.com/TrevisanGMW/gt-tools -  2020-12-10

 0.1a - 2020-12-10
 Created main function
 Added focal length calculation

 1.0 - 2020-12-11
 Initial Release
 Added GUI
 Added Sanity Checks
 
 1.1 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)
 
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

import maya.OpenMayaUI as omui
import maya.cmds as cmds
import base64
import json
import math
import sys
import os

# Script Name
script_name = "GT fSpy Importer"

# Version
script_version = "1.1"

# Python Version
python_version = sys.version_info.major

def build_gui_fspy_importer():
    ''' Builds Main UI '''
    window_name = "build_gui_fspy_importer"
    if cmds.window(window_name, exists =True):
        cmds.deleteUI(window_name)    

    # Main GUI Start Here =================================================================================
    
    # Build UI
    build_gui_fspy_importer = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',\
                          titleBar=True, mnb=False, mxb=False, sizeable =True)
                             
    cmds.window(window_name, e=True, s=True, wh=[1,1])
    
    content_main = cmds.columnLayout(adj = True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 340)], cs=[(1, 10)], p=content_main) # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 270), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)], p=content_main) # Title Column
    cmds.text(" ", bgc=title_bgc_color) # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color,  fn="boldLabelFont", align="left")
    cmds.button( l ="Help", bgc=title_bgc_color, c=lambda x:build_gui_help_fspy_importer())
    cmds.separator(h=3, style='none', p=content_main) # Empty Space
    
    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 340)], cs=[(1,10)], p=content_main)

    # Generate Images
    # Icon
    icons_folder_dir = cmds.internalVar(userBitmapsDir=True) 
    icon_image = icons_folder_dir + 'gt_fspy_importer.png'
    
    if os.path.isdir(icons_folder_dir) == False:
        icon_image = ':/camera.open.svg'
    
    if os.path.isdir(icons_folder_dir) and os.path.exists(icon_image) == False:
        image_enconded = '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'
        #image_64_decode = base64.decodestring(image_enconded)
        image_64_decode = base64.b64decode(image_enconded)
        image_result = open(icon_image, 'wb')
        image_result.write(image_64_decode)
        image_result.close()
        
        
    cmds.separator(h=7, style='none', p=body_column) # Empty Space
    
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,2)])
    cmds.text('JSON File Path:', font='tinyBoldLabelFont', align='left')
    cmds.rowColumnLayout(nc=2, cw=[(1, 290),(2, 30)], cs=[(1,0),(2,5)], p=body_column)
    json_file_path_txtfld = cmds.textField(pht='Path Pointing to JSON File')
    open_json_btn = cmds.iconTextButton( style='iconAndTextVertical', image1=':/folder-open.png', label='',\
                                         statusBarMessage='Open fSpy JSON File',\
                                         olc=[1,0,0] , enableBackground=True, h=30,\
                                         command=lambda: load_json_path())

    cmds.separator(h=5, style='none', p=body_column) # Empty Space
    
   
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,2)], p=body_column)
    cmds.text('Image File Path:', font='tinyBoldLabelFont', align='left')
    cmds.rowColumnLayout(nc=2, cw=[(1, 290),(2, 30)], cs=[(1,0),(2,5)], p=body_column)
    image_file_path_txtfld = cmds.textField(pht='Path Pointing to Image File')
    open_image_btn = cmds.iconTextButton( style='iconAndTextVertical', image1=':/folder-open.png', label='',\
                                          statusBarMessage='Open fSpy Image File',\
                                          olc=[1,0,0] , enableBackground=True, h=30,\
                                          command=lambda: load_image_path())
    
    cmds.separator(h=10, style='none', p=body_column) # Empty Space                  
    cmds.rowColumnLayout(nc=3, cw=[(1, 140),(2, 100),(3, 100)], cs=[(1,2)], p=body_column)
    
    set_resolution_chk = cmds.checkBox('Set Scene Resolution', value=True)
    convert_axis_z_to_y = cmds.checkBox('+Z Axis is +Y', value=True)
    lock_camera_chk = cmds.checkBox('Lock Camera', value=True)
    
    cmds.separator(h=10, style='none', p=body_column) # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 330)], cs=[(1,0)], p=body_column)

    cmds.button(l ="Import  (Generate Camera)", bgc=(.6, .6, .6), c=lambda x:check_before_run())
    cmds.separator(h=10, style='none', p=body_column) # Empty Space   
    

    def check_before_run():
        ''' Performs a few sanity checks before running the script '''
        set_resolution = cmds.checkBox(set_resolution_chk, q=True, value=True)
        convert_z_to_y = cmds.checkBox(convert_axis_z_to_y, q=True, value=True)
        lock_camera = cmds.checkBox(lock_camera_chk, q=True, value=True)
        
        is_valid = True
        
        json_path = cmds.textField(json_file_path_txtfld, q=True, text=True)
        image_path = cmds.textField(image_file_path_txtfld, q=True, text=True)
        
        if json_path == '':
            cmds.warning('The JSON file path is empty.')
            is_valid = False
            
        if image_path == '':
            cmds.warning('The image file path is empty.')
            is_valid = False
        
        if json_path != '' and os.path.exists(json_path) == False:
            cmds.warning('The provided JSON path doesn\'t seem to point to an existing file.')
            is_valid = False
            
        if image_path != '' and os.path.exists(image_path) == False:
            cmds.warning('The provided image path doesn\'t seem to point to an existing file.')
            is_valid = False
   
        try:
            if is_valid:
                with open(json_path) as json_file:
                    json_data = json.load(json_file)
                image_width = json_data['imageWidth']
        except:
            is_valid = False
            cmds.warning('The provided JSON file seems to be missing some data.')

        if is_valid:
            gt_import_fspy_json(json_path,image_path, convert_up_axis_z_to_y=convert_z_to_y, lock_camera=lock_camera, set_scene_resolution=set_resolution)
            
        
    def load_json_path():
        ''' Invoke open file dialog so the user can select a JSON file (Populates the "json_file_path_txtfld" with user input) '''
        multiple_filters = "JSON fSpy Files (*.json);;All Files (*.*)"
        file_path = cmds.fileDialog2(fileFilter=multiple_filters, dialogStyle=2, fm=1, caption='Select fSpy JSON File', okc='Select JSON')

        if file_path:
            cmds.textField(json_file_path_txtfld, e=True, text=file_path[0])
            try:
                extension = os.path.splitext(file_path[0])[1]
                if extension == '.fspy':
                    cmds.warning('You selected an "fSpy" file. This script only supports "json" files. Please select another file.')
            except:
                pass
    
    def load_image_path():
        ''' Invoke open file dialog so the user can select an image file (Populates the "image_file_path_txtfld" with user input) '''
        multiple_filters = "Image Files (*.*)"
        file_path = cmds.fileDialog2(fileFilter=multiple_filters, dialogStyle=2, fm=1, caption='Select fSpy JSON File', okc='Select JSON')

        if file_path:
            cmds.textField(image_file_path_txtfld, e=True, text=file_path[0])
            try:
                extension = os.path.splitext(file_path[0])[1]
                if extension == '.fspy':
                    cmds.warning('You selected an "fSpy" file. Please update this path to an image.')
                elif extension == '.json':
                    cmds.warning('You selected a "json" file. Please update this path to an image.')
            except:
                pass

    # Show and Lock Window
    cmds.showWindow(build_gui_fspy_importer)
    cmds.window(window_name, e=True, s=False)
    
    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_name)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(icon_image)
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


def build_gui_help_fspy_importer():
    ''' Builds the Help UI for GT Maya to Discord '''
    window_name = "build_gui_help_fspy_importer"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title= script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1,1])

    main_column = cmds.columnLayout(p= window_name)
   
    # Title Text
    cmds.separator(h=12, style='none') # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column) # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column) # Title Column
    cmds.text(script_name + " Help", bgc=[.4,.4,.4],  fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column) # Empty Space
    
    # Body ====================
    help_font = 'smallPlainLabelFont'
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.text(l=script_name + ' allows you import the data of a JSON\n file (exported out of fSpy) into Maya', align="center")
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='Don\'t know what fSpy is? Visit their website:', align="center")
    cmds.text(l='<a href="https://fspy.io/">https://fspy.io/</a>', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='How it works:', align="center", fn="boldLabelFont")
    cmds.text(l='Using the JSON file, this script applies the exported matrix to a', align="center", font=help_font)
    cmds.text(l='camera so it matches the position and rotation identified in fSpy.\n It also calculates the focal length assuming that the default\n camera in Maya is a 35mm camera.', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    cmds.text(l='How to use it:', align="center", fn="boldLabelFont")
    cmds.text(l='Step 1: Create a camera match in fSpy.\n(There is a tutorial about it on their website)', align="center", font=help_font)
    cmds.separator(h=4, style='none') # Empty Space
    cmds.text(l='Step 2: Export the data\n "File > Export > Camera parameters as JSON"', align="center", font=help_font)
    cmds.separator(h=4, style='none') # Empty Space
    cmds.text(l='Step 3: Load the files\nIn Maya, run the script and load your JSON and Image files', align="center", font=help_font)
    cmds.separator(h=4, style='none') # Empty Space
    cmds.text(l='Step 4: Use the Import button to generate the camera', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='JSON File Path:', align="center", fn="boldLabelFont")
    cmds.text(l='This is a path pointing to the JSON file you exported out of fSpy', align="center", font=help_font)
    cmds.text(l='In case the file was altered or exported/created using another\n program it might not work as expected.', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Image File Path:', align="center", fn="boldLabelFont")
    cmds.text(l='A path pointing to the image file you used for your camera match', align="center", font=help_font)
    cmds.text(l='Do not change the resolution of the image file or crop the image\nor it might not work properly.', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Set Scene Resolution:', align="center", fn="boldLabelFont")
    cmds.text(l='Uses the size of the image to determine the resolution of the scene', align="center", font=help_font)
    cmds.text(l='Settings found under "Render Settings > Image Size" (Resolution)', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='+Z Axis is +Y:', align="center", fn="boldLabelFont")
    cmds.text(l='Rotates the camera so the default +Z axis becomes +Y', align="center", font=help_font)
    cmds.text(l='This might be necessary in case the default settings were used', align="center", font=help_font)
    cmds.text(l='inside fSpy. This is because different softwares use different\n world coordinate systems.', align="center", font=help_font)
    cmds.separator(h=10, style='none') # Empty Space
    
    cmds.text(l='Lock Camera', align="center", fn="boldLabelFont")
    cmds.text(l='Locks the generated camera, so you don\'t accidenty move it', align="center", font=help_font)
   
    cmds.separator(h=15, style='none') # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1,1,1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140),(2, 140)], cs=[(1,10),(2, 0)], p=main_column)
    cmds.separator(h=15, style='none') # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1,1,1])
    cmds.separator(h=7, style='none') # Empty Space
    
    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1,10)], p=main_column)
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')
    
    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)
    
    # Set Window Icon
    qw = omui.MQtUtil.findWindow(window_name)
    if python_version == 3:
        widget = wrapInstance(int(qw), QWidget)
    else:
        widget = wrapInstance(long(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)
    
    def close_help_gui():
        ''' Closes the Help GUI '''
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


def gt_import_fspy_json(json_path,
                        image_path,
                        convert_up_axis_z_to_y=True,
                        lock_camera=True,
                        set_scene_resolution=True):
    '''
    Imports the data from a JSON file exported out of fSpy
    It creates a camera and an image plane and use the read data to update it.
    
            Parameters:
                json_path (string): A path pointing to the json file exported out of fSpy
                image_path (string): A path pointing to the image used in fSpy (must be the same one used for the JSON)
                convert_up_axis_z_to_y (bool): Converts the Up Axis of the camera to be +Y instead of +Z
                lock_camera (bool): Locks the default channels: Translate, Rotate and Scale for the camera.
                set_scene_resolution (bool): Uses the resolution from the image to set the scene resolution.

    '''
    function_name = 'GT fSpy Importer'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        # Read json_file
        with open(json_path) as json_file:
            json_data = json.load(json_file)
            
        # Create a camera an group it
        group = cmds.group( em=True, name='camera_fspy_grp' )
        camera_transform, camera_shape = cmds.camera(dr=True, overscan=1.3)
        cmds.parent(camera_transform, group)

        # Apply Matrix
        xform_matrix_list = []
        rows = json_data['cameraTransform']['rows']
        matrix = zip(rows[0],rows[1],rows[2],rows[3])

        for number in matrix:
            xform_matrix_list += number

        cmds.xform(camera_transform, matrix=xform_matrix_list)
        
        # Create Image Plane
        image_transform, image_shape = cmds.imagePlane(camera=camera_transform)
        cmds.setAttr(image_shape + '.imageName', image_path, type='string')
        
        # Compute Focal Length
        fov_horizontal = json_data['horizontalFieldOfView']
        fov_vertical = json_data['verticalFieldOfView']

        image_width = json_data['imageWidth']
        image_height = json_data['imageHeight']

        aspect_ratio = float(image_width) / float(image_height)
        h_aperture = float(24) # 36 x 24 (35mm) default in Maya
        v_aperture = h_aperture * aspect_ratio

        tan = math.tan((fov_horizontal / 2.0))
        focal_length = v_aperture / (2.0 * tan)

        cmds.setAttr(camera_shape + '.fl', focal_length)
        
        if convert_up_axis_z_to_y:
            cmds.rotate(-90, 0 ,0, group)
            cmds.makeIdentity(group, apply=True, r=1)
            message = 'Camera <span style=\"color:#FF0000;text-decoration:underline;\"> +Z </span> was converted to <span style=\"color:#FF0000;text-decoration:underline;\"> +Y </span>'
            cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
            
        if lock_camera:
            for attr in ['t', 'r', 's']:
                for axis in ['x', 'y', 'z']:
                    cmds.setAttr(camera_transform + '.' + attr + axis, lock=True)
                    cmds.setAttr(image_transform + '.' + attr + axis, lock=True)
                    
        if set_scene_resolution:
            cmds.setAttr( "defaultResolution.width", int(image_width) )
            cmds.setAttr( "defaultResolution.height", int(image_height) )
            cmds.setAttr( "defaultResolution.pixelAspect", 1 )
            cmds.setAttr( "defaultResolution.dar", aspect_ratio )
            message = 'Scene resolution changed to: <span style=\"color:#FF0000;text-decoration:underline;\">' +  str(image_width) + 'x'  +  str(image_height) +' </span>'
            cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
        
        camera_transform = cmds.rename(camera_transform, 'camera_fspy')
        
    except Exception as e:
        raise e
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
  

if __name__ == '__main__':
    build_gui_fspy_importer()