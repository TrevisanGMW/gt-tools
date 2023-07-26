"""
 GT fSpy Importer - Imports a JSON file exported out of fSpy
 github.com/TrevisanGMW/gt-tools -  2020-12-10
"""
from PySide2.QtWidgets import QWidget
import maya.OpenMayaUI as OpenMayaUI
from shiboken2 import wrapInstance
from gt.ui import resource_library
from PySide2.QtGui import QIcon
import maya.cmds as cmds
import logging
import base64
import json
import math
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_fspy_importer")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT fSpy Importer"

# Version
script_version = "?.?.?"  # Module version (init)


def build_gui_fspy_importer():
    """ Builds Main UI """
    window_name = "build_gui_fspy_importer"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name)

        # Main GUI Start Here =================================================================================

    # Build UI
    window_gui_fspy_importer = cmds.window(window_name, title=script_name + '  (v' + script_version + ')',
                                           titleBar=True, mnb=False, mxb=False, sizeable=True)

    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    content_main = cmds.columnLayout(adj=True)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 340)], cs=[(1, 10)], p=content_main)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 270), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p=content_main)  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_fspy_importer())
    cmds.separator(h=3, style='none', p=content_main)  # Empty Space

    # Body ====================
    body_column = cmds.rowColumnLayout(nc=1, cw=[(1, 340)], cs=[(1, 10)], p=content_main)

    cmds.separator(h=7, style='none', p=body_column)  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 2)])
    cmds.text('JSON File Path:', font='tinyBoldLabelFont', align='left')
    cmds.rowColumnLayout(nc=2, cw=[(1, 290), (2, 30)], cs=[(1, 0), (2, 5)], p=body_column)
    json_file_path_txt_fld = cmds.textField(pht='Path Pointing to JSON File')
    cmds.iconTextButton(style='iconAndTextVertical', image1=':/folder-open.png', label='',
                        statusBarMessage='Open fSpy JSON File',
                        olc=[1, 0, 0], enableBackground=True, h=30,
                        command=lambda: load_json_path())

    cmds.separator(h=5, style='none', p=body_column)  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 2)], p=body_column)
    cmds.text('Image File Path:', font='tinyBoldLabelFont', align='left')
    cmds.rowColumnLayout(nc=2, cw=[(1, 290), (2, 30)], cs=[(1, 0), (2, 5)], p=body_column)
    image_file_path_txtfld = cmds.textField(pht='Path Pointing to Image File')
    cmds.iconTextButton(style='iconAndTextVertical', image1=':/folder-open.png', label='',
                        statusBarMessage='Open fSpy Image File',
                        olc=[1, 0, 0], enableBackground=True, h=30,
                        command=lambda: load_image_path())

    cmds.separator(h=10, style='none', p=body_column)  # Empty Space
    cmds.rowColumnLayout(nc=3, cw=[(1, 140), (2, 100), (3, 100)], cs=[(1, 2)], p=body_column)

    set_resolution_chk = cmds.checkBox('Set Scene Resolution', value=True)
    convert_axis_z_to_y = cmds.checkBox('+Z Axis is +Y', value=True)
    lock_camera_chk = cmds.checkBox('Lock Camera', value=True)

    cmds.separator(h=10, style='none', p=body_column)  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 330)], cs=[(1, 0)], p=body_column)

    cmds.button(l="Import  (Generate Camera)", bgc=(.6, .6, .6), c=lambda x: check_before_run())
    cmds.separator(h=10, style='none', p=body_column)  # Empty Space

    def check_before_run():
        """ Performs a few sanity checks before running the script """
        set_resolution = cmds.checkBox(set_resolution_chk, q=True, value=True)
        convert_z_to_y = cmds.checkBox(convert_axis_z_to_y, q=True, value=True)
        lock_camera = cmds.checkBox(lock_camera_chk, q=True, value=True)

        is_valid = True

        json_path = cmds.textField(json_file_path_txt_fld, q=True, text=True)
        image_path = cmds.textField(image_file_path_txtfld, q=True, text=True)

        if json_path == '':
            cmds.warning('The JSON file path is empty.')
            is_valid = False

        if image_path == '':
            cmds.warning('The image file path is empty.')
            is_valid = False

        if json_path != '' and os.path.exists(json_path) is False:
            cmds.warning("The provided JSON path doesn't seem to point to an existing file.")
            is_valid = False

        if image_path != '' and os.path.exists(image_path) is False:
            cmds.warning("The provided image path doesn't seem to point to an existing file.")
            is_valid = False

        try:
            if is_valid:
                with open(json_path) as json_file:
                    json_data = json.load(json_file)
                image_width = json_data['imageWidth']
                logger.debug(str(image_width))
        except Exception as e:
            logger.debug(str(e))
            is_valid = False
            cmds.warning('The provided JSON file seems to be missing some data.')

        if is_valid:
            gt_import_fspy_json(json_path, image_path, convert_up_axis_z_to_y=convert_z_to_y, lock_camera=lock_camera,
                                set_scene_resolution=set_resolution)

    def load_json_path():
        """ 
        Invoke open file dialog so the user can select a JSON file 
        (Populates the "json_file_path_txt_fld" with user input) 
        """
        multiple_filters = "JSON fSpy Files (*.json);;All Files (*.*)"
        file_path = cmds.fileDialog2(fileFilter=multiple_filters, dialogStyle=2, fm=1, caption='Select fSpy JSON File',
                                     okc='Select JSON')

        if file_path:
            cmds.textField(json_file_path_txt_fld, e=True, text=file_path[0])
            try:
                extension = os.path.splitext(file_path[0])[1]
                if extension == '.fspy':
                    cmds.warning('You selected an "fSpy" file. '
                                 'This script only supports "json" files. Please select another file.')
            except Exception as e:
                logger.debug(str(e))

    def load_image_path():
        """
        Invoke open file dialog so the user can select an image file 
        (Populates the "image_file_path_txtfld" with user input) 
        """
        multiple_filters = "Image Files (*.*)"
        file_path = cmds.fileDialog2(fileFilter=multiple_filters, dialogStyle=2, fm=1, caption='Select fSpy JSON File',
                                     okc='Select JSON')

        if file_path:
            cmds.textField(image_file_path_txtfld, e=True, text=file_path[0])
            try:
                extension = os.path.splitext(file_path[0])[1]
                if extension == '.fspy':
                    cmds.warning('You selected an "fSpy" file. Please update this path to an image.')
                elif extension == '.json':
                    cmds.warning('You selected a "json" file. Please update this path to an image.')
            except Exception as e:
                logger.debug(str(e))

    # Show and Lock Window
    cmds.showWindow(window_gui_fspy_importer)
    cmds.window(window_name, e=True, s=False)

    # Remove the focus from the textfield and give it to the window
    cmds.setFocus(window_name)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(resource_library.Icon.tool_fspy_importer)
    widget.setWindowIcon(icon)

    # Main GUI Ends Here =================================================================================


def build_gui_help_fspy_importer():
    """ Builds the Help UI for GT Maya to Discord """
    window_name = "build_gui_help_fspy_importer"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    main_column = cmds.columnLayout(p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)  # Title Column
    cmds.text(script_name + " Help", bgc=[.4, .4, .4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column)  # Empty Space

    # Body ====================
    help_font = 'smallPlainLabelFont'
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
    cmds.text(l=script_name + ' allows you import the data of a JSON\n file (exported out of fSpy) into Maya',
              align="center")
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='Don\'t know what fSpy is? Visit their website:', align="center")
    cmds.text(l='<a href="https://fspy.io/">https://fspy.io/</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='How it works:', align="center", fn="boldLabelFont")
    cmds.text(l='Using the JSON file, this script applies the exported matrix to a', align="center", font=help_font)
    cmds.text(l='camera so it matches the position and rotation identified in fSpy.\n '
                'It also calculates the focal length assuming that the default\n camera in Maya is a 35mm camera.',
              align="center", font=help_font)
    cmds.separator(h=10, style='none')  # Empty Space
    cmds.text(l='How to use it:', align="center", fn="boldLabelFont")
    cmds.text(l='Step 1: Create a camera match in fSpy.\n(There is a tutorial about it on their website)',
              align="center", font=help_font)
    cmds.separator(h=4, style='none')  # Empty Space
    cmds.text(l='Step 2: Export the data\n "File > Export > Camera parameters as JSON"', align="center", font=help_font)
    cmds.separator(h=4, style='none')  # Empty Space
    cmds.text(l='Step 3: Load the files\nIn Maya, run the script and load your JSON and Image files', align="center",
              font=help_font)
    cmds.separator(h=4, style='none')  # Empty Space
    cmds.text(l='Step 4: Use the Import button to generate the camera', align="center", font=help_font)
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='JSON File Path:', align="center", fn="boldLabelFont")
    cmds.text(l='This is a path pointing to the JSON file you exported out of fSpy', align="center", font=help_font)
    cmds.text(
        l='In case the file was altered or exported/created using another\n program it might not work as expected.',
        align="center", font=help_font)
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='Image File Path:', align="center", fn="boldLabelFont")
    cmds.text(l='A path pointing to the image file you used for your camera match', align="center", font=help_font)
    cmds.text(l='Do not change the resolution of the image file or crop the image\nor it might not work properly.',
              align="center", font=help_font)
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='Set Scene Resolution:', align="center", fn="boldLabelFont")
    cmds.text(l='Uses the size of the image to determine the resolution of the scene', align="center", font=help_font)
    cmds.text(l='Settings found under "Render Settings > Image Size" (Resolution)', align="center", font=help_font)
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='+Z Axis is +Y:', align="center", fn="boldLabelFont")
    cmds.text(l='Rotates the camera so the default +Z axis becomes +Y', align="center", font=help_font)
    cmds.text(l='This might be necessary in case the default settings were used', align="center", font=help_font)
    cmds.text(l='inside fSpy. This is because different software use different\n world coordinate systems.',
              align="center", font=help_font)
    cmds.separator(h=10, style='none')  # Empty Space

    cmds.text(l='Lock Camera', align="center", fn="boldLabelFont")
    cmds.text(l="Locks the generated camera, so you don't accidentally move it", align="center", font=help_font)

    cmds.separator(h=15, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p=main_column)
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p=main_column)
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style='none')  # Empty Space

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
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
        """ Closes the Help GUI """
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


def gt_import_fspy_json(json_path,
                        image_path,
                        convert_up_axis_z_to_y=True,
                        lock_camera=True,
                        set_scene_resolution=True):
    """
    Imports the data from a JSON file exported out of fSpy
    It creates a camera and an image plane and use the read data to update it.
    
    Args:
        json_path (string): A path pointing to the json file exported out of fSpy
        image_path (string): A path pointing to the image used in fSpy (must be the same one used for the JSON)
        convert_up_axis_z_to_y (bool): Converts the Up Axis of the camera to be +Y instead of +Z
        lock_camera (bool): Locks the default channels: Translate, Rotate and Scale for the camera.
        set_scene_resolution (bool): Uses the resolution from the image to set the scene resolution.

    """
    function_name = 'GT fSpy Importer'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        # Read json_file
        with open(json_path) as json_file:
            json_data = json.load(json_file)

        # Create a camera and group it
        group = cmds.group(em=True, name='camera_fspy_grp')
        camera_transform, camera_shape = cmds.camera(dr=True, overscan=1.3)
        cmds.parent(camera_transform, group)

        # Apply Matrix
        xform_matrix_list = []
        rows = json_data['cameraTransform']['rows']
        matrix = zip(rows[0], rows[1], rows[2], rows[3])

        for number in matrix:
            xform_matrix_list += number

        cmds.xform(camera_transform, matrix=xform_matrix_list)

        # Create Image Plane
        image_transform, image_shape = cmds.imagePlane(camera=camera_transform)
        cmds.setAttr(image_shape + '.imageName', image_path, type='string')

        # Compute Focal Length
        fov_horizontal = json_data['horizontalFieldOfView']
        # fov_vertical = json_data['verticalFieldOfView']

        image_width = json_data['imageWidth']
        image_height = json_data['imageHeight']

        aspect_ratio = float(image_width) / float(image_height)
        h_aperture = float(24)  # 36 x 24 (35mm) default in Maya
        v_aperture = h_aperture * aspect_ratio

        tan = math.tan((fov_horizontal / 2.0))
        focal_length = v_aperture / (2.0 * tan)

        cmds.setAttr(camera_shape + '.fl', focal_length)

        if convert_up_axis_z_to_y:
            cmds.rotate(-90, 0, 0, group)
            cmds.makeIdentity(group, apply=True, r=1)
            message = 'Camera <span style=\"color:#FF0000;text-decoration:underline;\"> ' \
                      '+Z </span> was converted to <span style=\"color:#FF0000;text-decoration:underline;\"> +Y </span>'
            cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)

        if lock_camera:
            for attr in ['t', 'r', 's']:
                for axis in ['x', 'y', 'z']:
                    cmds.setAttr(camera_transform + '.' + attr + axis, lock=True)
                    cmds.setAttr(image_transform + '.' + attr + axis, lock=True)

        if set_scene_resolution:
            cmds.setAttr("defaultResolution.width", int(image_width))
            cmds.setAttr("defaultResolution.height", int(image_height))
            cmds.setAttr("defaultResolution.pixelAspect", 1)
            cmds.setAttr("defaultResolution.dar", aspect_ratio)
            message = 'Scene resolution changed to: <span style=\"color:#FF0000;text-decoration:underline;\">' + str(
                image_width) + 'x' + str(image_height) + ' </span>'
            cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)

        cmds.rename(camera_transform, 'camera_fspy')

    except Exception as e:
        raise e
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


if __name__ == '__main__':
    build_gui_fspy_importer()
