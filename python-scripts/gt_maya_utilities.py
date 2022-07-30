"""
 GT Maya Utilities
 github.com/TrevisanGMW - 2020-09-13
 
 - 2020-10-17
 Added move pivot to bottom/top
 Added copy/paste material
 Added move to origin
 
 - 2020-10-21
 Updated reset transform to better handle translate
 Added Uniform LRA Toggle
 Changed the order of the functions to match the menu
 
 - 2020-11-11
 Updates "references_import" to better handle unloaded references
 Added "references_remove"
 Added "curves_combine"
 Added "curves_separate"
 
 - 2020-11-13
 Updated combine and separate functions to work with Bezier curves
 
 - 2020-11-14
 Added "convert_bif_to_mesh"
 
 - 2020-11-16
 Added "delete_nucleus_nodes"
 Updated "delete_display_layers" to have inView feedback
 Updated "delete_keyframes" to have inView feedback
 
 - 2020-11-22
 Updated about window text
 
 - 2020-12-03
 Changed the background color for the title in the "About" window
 Changed the order of a few functions
 Added function to unlock/unhide default channels
 
 - 2021-01-05
 Added Uniform Joint Label Toggle
 
 - 2021-02-05
 Added "Select Non-Unique Objects" Utility
 
 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)
 Added refresh to combine curves function as they were not automatically updating after re-parenting shapes
 
 - 2021-06-25
 Updated bif to mesh to work with newer versions of bifrost
 Updated bif to mesh to delete empty meshes (objects that weren't geometry)
 Added function to delete all locators
 
 - 2021-10-25
 Updated bif to mesh to work with newer versions of bifrost
 Updated bif to mesh to delete empty meshes (objects that weren't geometry)
 Added function to delete all locators
 
 - 2021-10-10
 Created Full HUD Toggle
 
 - 2021-10-10
 Fixed gtu full hud toggle as it would return an error if xGen was not loaded
  
 - 2022-01-04
 Renamed script to "gt_maya_utilities"
  
 - 2022-01-04
 Renamed script to "gt_maya_utilities"

 - 2022-06-29
 Added string to notepad (txt)
 Renamed functions

 - 2022-07-30
 Removed versions
 Removed prefix "gtu_" from functions
     - Added or updated feedback for:
       - Force Reload File
       - Unlock Default Channels
       - Unhide Default Channels
       - Uniform LRA Toggle
       - Full Hud Toggle
       - Select Non-Unique Objects

    - Added validation
       - Uniform LRA Toggle
       - Uniform Joint Label Toggle
       - Reset Transforms

 TODO:
     New functions:
        Reset Display Type and Color
        Assign lambert to everything function (Maybe assign to object missing shaders)
        Add Unlock all attributes
        Add unhide attributes (provide list?)
        Add Remove pasted_ function
        Add assign checkerboard function (already in bonus tools > rendering)
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
import logging
import random
import sys
from maya import OpenMayaUI as OpenMayaUI

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_utilities")
logger.setLevel(logging.INFO)

''' ____________________________ General Functions ____________________________'''


def force_reload_file():
    """ Reopens the opened file (to revert any changes done to the file) """
    if cmds.file(query=True, exists=True):  # Check to see if it was ever saved
        file_path = cmds.file(query=True, expandName=True)
        if file_path is not None:
            cmds.file(file_path, open=True, force=True)
    else:
        cmds.warning('Unable to force reload. File was never saved.')


def open_resource_browser():
    """ Opens Maya's Resource Browser """
    try:
        import maya.app.general.resourceBrowser as resourceBrowser
        resourceBrowser.resourceBrowser().run()
    except Exception as e:
        logger.debug(str(e))


def unlock_default_channels():
    """ Unlocks Translate, Rotate, Scale for the selected objects """
    function_name = 'GTU Unlock Default Channels'
    errors = ''
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    selection = cmds.ls(selection=True, long=True)
    selection_short = cmds.ls(selection=True)
    unlocked_counter = 0
    try:
        for obj in selection:
            try:
                cmds.setAttr(obj + '.translateX', lock=False)
                cmds.setAttr(obj + '.translateY', lock=False)
                cmds.setAttr(obj + '.translateZ', lock=False)
                cmds.setAttr(obj + '.rotateX', lock=False)
                cmds.setAttr(obj + '.rotateY', lock=False)
                cmds.setAttr(obj + '.rotateZ', lock=False)
                cmds.setAttr(obj + '.scaleX', lock=False)
                cmds.setAttr(obj + '.scaleY', lock=False)
                cmds.setAttr(obj + '.scaleZ', lock=False)
                cmds.setAttr(obj + '.v', lock=False)
                unlocked_counter += 1
            except Exception as e:
                errors += str(e) + '\n'
        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning('Some channels were not unlocked . Open the script editor for a list of errors.')
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)

    in_view_message = '<' + str(random.random()) + '>'
    in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(unlocked_counter) + ' </span>'
    is_plural = 'objects had their'
    if unlocked_counter == 1:
        is_plural = 'object had its'
    description = ' default channels unlocked.'
    in_view_message += is_plural + description

    cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)

    if unlocked_counter == 1:
        sys.stdout.write('\n"' + str(selection_short[0]) + '" ' + is_plural + description)
    else:
        sys.stdout.write('\n' + str(unlocked_counter) + ' ' + is_plural + description)


def unhide_default_channels():
    """ Un-hides Translate, Rotate, Scale for the selected objects """
    function_name = 'GTU Unhide Default Channels'
    errors = ''
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    selection = cmds.ls(selection=True, long=True)
    selection_short = cmds.ls(selection=True)
    unlocked_counter = 0
    try:
        for obj in selection:
            try:
                cmds.setAttr(obj + '.translateX', keyable=True)
                cmds.setAttr(obj + '.translateY', keyable=True)
                cmds.setAttr(obj + '.translateZ', keyable=True)
                cmds.setAttr(obj + '.rotateX', keyable=True)
                cmds.setAttr(obj + '.rotateY', keyable=True)
                cmds.setAttr(obj + '.rotateZ', keyable=True)
                cmds.setAttr(obj + '.scaleX', keyable=True)
                cmds.setAttr(obj + '.scaleY', keyable=True)
                cmds.setAttr(obj + '.scaleZ', keyable=True)
                cmds.setAttr(obj + '.v', keyable=True)
                unlocked_counter += 1
            except Exception as e:
                errors += str(e) + '\n'
        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning('Some channels were not made visible. Open the script editor for a list of errors.')
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)

    in_view_message = '<' + str(random.random()) + '>'
    in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(unlocked_counter) + ' </span>'
    is_plural = 'objects had their'
    if unlocked_counter == 1:
        is_plural = 'object had its'
    description = ' default channels made visible.'
    in_view_message += is_plural + description

    cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
    if unlocked_counter == 1:
        sys.stdout.write('\n"' + str(selection_short[0]) + '" ' + is_plural + description)
    else:
        sys.stdout.write('\n' + str(unlocked_counter) + ' ' + is_plural + description)


def toggle_uniform_lra():
    """
    Makes the visibility of the Local Rotation Axis uniform among 
    the selected objects according to the current state of the majority of them.  
    """

    function_name = 'GTU Uniform LRA Toggle'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        errors = ''
        selection = cmds.ls(selection=True, long=True) or []
        if not selection:
            cmds.warning('Select at least one object and try again.')
            return

        inactive_lra = []
        active_lra = []
        operation_result = 'off'

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
                    operation_result = 'on'
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
                    operation_result = 'on'
                except Exception as e:
                    errors += str(e) + '\n'
        else:
            for obj in active_lra:
                try:
                    cmds.setAttr(obj + '.displayLocalAxis', 0)
                except Exception as e:
                    errors += str(e) + '\n'

        in_view_message = '<' + str(random.random()) + '>'
        in_view_message += '<span>LRA Visibility set to: </span>'
        in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + operation_result + '</span>'
        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
        sys.stdout.write('\n' + 'Local Rotation Axes Visibility set to: "' + operation_result + '"')

        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning("The script couldn't read or write some LRA states. Open script editor for more info.")
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def toggle_uniform_jnt_label():
    """
    Makes the visibility of the Joint Labels uniform according to the current state of the majority of them.  
    """

    function_name = 'GTU Uniform Joint Label Toggle'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        errors = ''
        joints = cmds.ls(type='joint', long=True)

        inactive_label = []
        active_label = []
        operation_result = 'off'

        for obj in joints:
            try:
                current_label_state = cmds.getAttr(obj + '.drawLabel')
                if current_label_state:
                    active_label.append(obj)
                else:
                    inactive_label.append(obj)
            except Exception as e:
                errors += str(e) + '\n'

        if len(active_label) == 0:
            for obj in inactive_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 1)
                    operation_result = 'on'
                except Exception as e:
                    errors += str(e) + '\n'
        elif len(inactive_label) == 0:
            for obj in active_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 0)
                except Exception as e:
                    errors += str(e) + '\n'
        elif len(active_label) > len(inactive_label):
            for obj in inactive_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 1)
                    operation_result = 'on'
                except Exception as e:
                    errors += str(e) + '\n'
        else:
            for obj in active_label:
                try:
                    cmds.setAttr(obj + '.drawLabel', 0)
                except Exception as e:
                    errors += str(e) + '\n'

        if len(joints) > 0:
            in_view_message = '<' + str(random.random()) + '>'
            in_view_message += '<span>Joint Label Visibility set to: </span>'
            in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + operation_result
            in_view_message += '</span>'
            cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('\n' + 'Joint Label Visibility set to: "' + operation_result + '"')
        else:
            unique_message = '<' + str(random.random()) + '>'
            message = 'No joints found in the scene.'
            cmds.inViewMessage(amg=unique_message + message, pos='botLeft', fade=True, alpha=.9)
            sys.stdout.write('\n' + message)

        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning("The script couldn't read or write some \"drawLabel\" states. "
                         "Open script editor for more info.")
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def toggle_full_hud():
    """ Toggles common HUD options so all the common ones are either active or inactive  """
    hud_current_state = {}

    # 1 - Animation Details
    hud_current_state['animationDetailsVisibility'] = int(mel.eval('optionVar -q animationDetailsVisibility;'))
    # 2 - Cache
    try:
        from maya.plugin.evaluator.CacheUiHud import CachePreferenceHud
        hud_current_state['CachePreferenceHud'] = int(CachePreferenceHud().get_value() or 0)
    except Exception as e:
        logger.debug(str(e))
        hud_current_state['CachePreferenceHud'] = 0
    # 3 - Camera Names
    hud_current_state['cameraNamesVisibility'] = int(mel.eval('optionVar -q cameraNamesVisibility;'))
    # 4 - Caps Lock
    hud_current_state['capsLockVisibility'] = int(mel.eval('optionVar -q capsLockVisibility;'))
    # 5 - Current Asset
    hud_current_state['currentContainerVisibility'] = int(mel.eval('optionVar -q currentContainerVisibility;'))
    # 6 - Current Frame
    hud_current_state['currentFrameVisibility'] = int(mel.eval('optionVar -q currentFrameVisibility;'))
    # 7 - Evaluation
    hud_current_state['evaluationVisibility'] = int(mel.eval('optionVar -q evaluationVisibility;'))
    # 8 - Focal Length
    hud_current_state['focalLengthVisibility'] = int(mel.eval('optionVar -q focalLengthVisibility;'))
    # 9 - Frame Rate
    hud_current_state['frameRateVisibility'] = int(mel.eval('optionVar -q frameRateVisibility;'))
    # 10 - HumanIK Details
    hud_current_state['hikDetailsVisibility'] = int(mel.eval('optionVar -q hikDetailsVisibility;'))
    # 11 - Material Loading Details
    hud_current_state['materialLoadingDetailsVisibility'] = int(
        mel.eval('optionVar -q materialLoadingDetailsVisibility;'))
    # 12 - Object Details
    hud_current_state['objectDetailsVisibility'] = int(mel.eval('optionVar -q objectDetailsVisibility;'))
    # 13 - Origin Axis - Ignored as non-hud element
    # hud_current_state['originAxesMenuUpdate'] = mel.eval('optionVar -q originAxesMenuUpdate;')
    # 14 - Particle Count
    hud_current_state['particleCountVisibility'] = int(mel.eval('optionVar -q particleCountVisibility;'))
    # 15 - Poly Count
    hud_current_state['polyCountVisibility'] = int(mel.eval('optionVar -q polyCountVisibility;'))
    # 16 - Scene Timecode
    hud_current_state['sceneTimecodeVisibility'] = int(mel.eval('optionVar -q sceneTimecodeVisibility;'))
    # 17 - Select Details
    hud_current_state['selectDetailsVisibility'] = int(mel.eval('optionVar -q selectDetailsVisibility;'))
    # 18 - Symmetry
    hud_current_state['symmetryVisibility'] = int(mel.eval('optionVar -q symmetryVisibility;'))
    # 19 - View Axis
    hud_current_state['viewAxisVisibility'] = int(mel.eval('optionVar -q viewAxisVisibility;'))
    # 20 - Viewport Renderer
    hud_current_state['viewportRendererVisibility'] = int(mel.eval('optionVar -q viewportRendererVisibility;'))
    # ------- Separator -------
    # 21 - In-view Messages
    hud_current_state['inViewMessageEnable'] = int(mel.eval('optionVar -q inViewMessageEnable;'))
    # 22 - In-view Editors
    hud_current_state['inViewEditorVisible'] = int(mel.eval('optionVar -q inViewEditorVisible;'))
    # Conditional - XGen Info
    hud_current_state['xgenHUDVisibility'] = int(mel.eval('optionVar -q xgenHUDVisibility;'))

    # Check if toggle ON or OFF
    toggle = True
    count = 0
    for item_state in hud_current_state:
        if hud_current_state.get(item_state):
            count += 1
    # More than half is on, so OFF else ON (Default)
    if count > len(hud_current_state) / 2:
        toggle = False

    # Toggles non-standard hud elements
    if toggle:
        mel.eval('setAnimationDetailsVisibility(true)')
        try:
            from maya.plugin.evaluator.CacheUiHud import CachePreferenceHud
            CachePreferenceHud().set_value(True)
        except Exception as e:
            logger.debug(str(e))
        mel.eval('setCameraNamesVisibility(true)')
        mel.eval('setCapsLockVisibility(true)')
        mel.eval('setCurrentContainerVisibility(true)')
        mel.eval('setCurrentFrameVisibility(true)')
        mel.eval('SetEvaluationManagerHUDVisibility(1)')
        mel.eval('setFocalLengthVisibility(true)')
        mel.eval('setFrameRateVisibility(true)')
        if not hud_current_state.get('hikDetailsVisibility'):
            cmds.ToggleHikDetails()
            mel.eval('catchQuiet(setHikDetailsVisibility(true));')
        mel.eval('ToggleMaterialLoadingDetailsHUDVisibility(true)')
        mel.eval('setObjectDetailsVisibility(true)')
        mel.eval('setParticleCountVisibility(true)')
        mel.eval('setPolyCountVisibility(true)')
        mel.eval('setSceneTimecodeVisibility(true)')
        mel.eval('setSelectDetailsVisibility(true)')
        mel.eval('setSymmetryVisibility(true)')
        mel.eval('setViewAxisVisibility(true)')
        mel.eval('setViewportRendererVisibility(true)')
        mel.eval('catchQuiet(setXGenHUDVisibility(true));')

        if not hud_current_state.get('inViewMessageEnable'):
            cmds.ToggleInViewMessage()
        if not hud_current_state.get('inViewEditorVisible'):
            cmds.ToggleInViewEditor()
    else:
        mel.eval('setAnimationDetailsVisibility(false)')
        try:
            from maya.plugin.evaluator.CacheUiHud import CachePreferenceHud
            CachePreferenceHud().set_value(False)
        except Exception as e:
            logger.debug(str(e))
        mel.eval('setCurrentContainerVisibility(false)')
        mel.eval('setCurrentFrameVisibility(false)')
        mel.eval('SetEvaluationManagerHUDVisibility(0)')
        mel.eval('setFocalLengthVisibility(false)')
        mel.eval('setFrameRateVisibility(false)')
        if hud_current_state.get('hikDetailsVisibility'):
            cmds.ToggleHikDetails()
            mel.eval('catchQuiet(setHikDetailsVisibility(false));')
            mel.eval('catchQuiet(hikDetailsKeyingMode());')
        mel.eval('ToggleMaterialLoadingDetailsHUDVisibility(false)')
        mel.eval('setObjectDetailsVisibility(false)')
        mel.eval('setParticleCountVisibility(false)')
        mel.eval('setPolyCountVisibility(false)')
        mel.eval('setSceneTimecodeVisibility(false)')
        mel.eval('setSelectDetailsVisibility(false)')
        mel.eval('setViewportRendererVisibility(false)')
        mel.eval('catchQuiet(setXGenHUDVisibility(false));')
    # Default states are preserved: camera names, caps lock, symmetry, view axis, in-view messages and in-view editor
    print("?")
    # Give feedback
    operation_result = 'off'
    if toggle:
        operation_result = 'on'
    in_view_message = '<' + str(random.random()) + '>'
    in_view_message += '<span>Hud Visibility set to: </span>'
    in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + operation_result
    in_view_message += '</span>'
    cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
    sys.stdout.write('\n' + 'Hud Visibility set to: "' + operation_result + '"')


def select_non_unique_objects():
    """ Selects all non-unique objects (objects with the same short name) """

    def get_short_name(full_name):
        """
            Get the name of the objects without its path (Maya returns full path if name is not unique)

            Args:
                full_name (string) - object to extract short name
            """
        output_short_name = ''
        if full_name == '':
            return ''
        split_path = full_name.split('|')
        if len(split_path) >= 1:
            output_short_name = split_path[len(split_path) - 1]
        return output_short_name

    all_transforms = cmds.ls(type='transform')
    short_names = []
    non_unique_transforms = []
    for obj in all_transforms:  # Get all Short Names
        short_names.append(get_short_name(obj))

    for obj in all_transforms:
        short_name = get_short_name(obj)
        if short_names.count(short_name) > 1:
            non_unique_transforms.append(obj)

    cmds.select(non_unique_transforms, r=True)

    if len(non_unique_transforms) > 0:
        in_view_message = '<span style=\"color:#FF0000;text-decoration:underline;\">'
        in_view_message += str(len(non_unique_transforms)) + '</span> non-unique objects were selected.'
        message = '\n' + str(len(non_unique_transforms)) + ' non-unique objects were found in this scene. ' \
                                                           'Rename them to avoid conflicts.'
    else:
        in_view_message = 'All objects seem to have unique names in this scene.'
        message = 'No repeated names found in the scene.'
    cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
    sys.stdout.write(message)


def references_import():
    """ Imports all references """
    errors = ''
    r_file = ''
    try:
        refs = cmds.ls(rf=True)
        for i in refs:
            try:
                r_file = cmds.referenceQuery(i, f=True)
                cmds.file(r_file, importReference=True)
            except Exception as e:
                errors += str(e) + '(' + r_file + ')\n'
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")
    if errors != '':
        cmds.warning('Not all references were imported. Open the script editor for more information.')
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)


def references_remove():
    """ Removes all references """
    errors = ''
    r_file = ''
    try:
        refs = cmds.ls(rf=True)
        for i in refs:
            try:
                r_file = cmds.referenceQuery(i, f=True)
                cmds.file(r_file, removeReference=True)
            except Exception as e:
                errors += str(e) + '(' + r_file + ')\n'
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Something went wrong. Maybe you don't have any references to import?")
    if errors != '':
        cmds.warning('Not all references were removed. Open the script editor for more information.')
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)


""" ____________________________ Material Functions ____________________________"""


def generate_udim_previews():
    """ Generates UDIM previews for all file nodes """
    all_file_nodes = cmds.ls(type='file')
    for file_node in all_file_nodes:
        try:
            mel.eval('generateUvTilePreview ' + file_node + ';')
        except Exception as e:
            print(e)
    message = 'Previews generated for all <span style=\"color:#FF0000;text-decoration:underline;\"> ' \
              'UDIM</span> file nodes.'
    cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)


def material_copy():
    """ Copies selected material to clipboard """
    selection = cmds.ls(selection=True)
    try:
        mel.eval('ConvertSelectionToFaces;')
        cmds.polyClipboard(copy=True, shader=True)
        cmds.inViewMessage(amg='Material <hl>copied</hl> to the clipboard.', pos='midCenterTop', fade=True)
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Couldn't copy material. Make sure you selected an object or component before copying.")
    cmds.select(selection)


def material_paste():
    """ Copies selected material to clipboard """
    try:
        cmds.polyClipboard(paste=True, shader=True)
    except Exception as e:
        logger.debug(str(e))
        cmds.warning("Couldn't paste material. Make sure you copied a material first, "
                     "then selected the target objects or components.")


""" ____________________________ Layout Functions ____________________________"""


def move_pivot_to_top():
    """ Moves pivot point to the top of the boundary box """
    selection = cmds.ls(selection=True)

    for obj in selection:
        bbox = cmds.exactWorldBoundingBox(obj)  # extracts bounding box
        top = [(bbox[0] + bbox[3]) / 2, bbox[4], (bbox[2] + bbox[5]) / 2]  # find top
        cmds.xform(obj, piv=top, ws=True)


def move_pivot_to_base():
    """ Moves pivot point to the base of the boundary box """
    selection = cmds.ls(selection=True)

    for obj in selection:
        bbox = cmds.exactWorldBoundingBox(obj)  # extracts bounding box
        bottom = [(bbox[0] + bbox[3]) / 2, bbox[1], (bbox[2] + bbox[5]) / 2]  # find bottom
        cmds.xform(obj, piv=bottom, ws=True)  # sends pivot to bottom


def move_to_origin():
    """ Moves selected objects back to origin """
    function_name = 'GTU Move to Origin'
    errors = ''
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    selection = cmds.ls(selection=True)
    try:
        for obj in selection:
            try:
                cmds.move(0, 0, 0, obj, a=True, rpr=True)  # rpr flag moves it according to the pivot
            except Exception as e:
                errors += str(e) + '\n'
        if errors != '':
            print('#### Errors: ####')
            print(errors)
            cmds.warning('Some objects could not be moved to the origin. Open the script editor for a list of errors.')
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


""" ____________________________ Reset Functions ____________________________"""


def reset_transforms():
    """
    Reset transforms. 
    It checks for incoming connections, then set the attribute to 0 if there are none
    It resets transforms, but ignores translate for joints.
    """
    function_name = 'GTU Reset Transforms'
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    output_errors = ''
    current_selection = cmds.ls(selection=True)

    def reset_trans(selection):
        errors = ''
        for obj in selection:
            try:
                type_check = cmds.listRelatives(obj, children=True) or []

                if len(type_check) > 0 and cmds.objectType(type_check) != 'joint':
                    obj_connection_tx = cmds.listConnections(obj + '.tx', d=False, s=True) or []
                    if not len(obj_connection_tx) > 0:
                        if cmds.getAttr(obj + '.tx', lock=True) is False:
                            cmds.setAttr(obj + '.tx', 0)
                    obj_connection_ty = cmds.listConnections(obj + '.ty', d=False, s=True) or []
                    if not len(obj_connection_ty) > 0:
                        if cmds.getAttr(obj + '.ty', lock=True) is False:
                            cmds.setAttr(obj + '.ty', 0)
                    obj_connection_tz = cmds.listConnections(obj + '.tz', d=False, s=True) or []
                    if not len(obj_connection_tz) > 0:
                        if cmds.getAttr(obj + '.tz', lock=True) is False:
                            cmds.setAttr(obj + '.tz', 0)

                obj_connection_rx = cmds.listConnections(obj + '.rotateX', d=False, s=True) or []
                if not len(obj_connection_rx) > 0:
                    if cmds.getAttr(obj + '.rotateX', lock=True) is False:
                        cmds.setAttr(obj + '.rotateX', 0)
                obj_connection_ry = cmds.listConnections(obj + '.rotateY', d=False, s=True) or []
                if not len(obj_connection_ry) > 0:
                    if cmds.getAttr(obj + '.rotateY', lock=True) is False:
                        cmds.setAttr(obj + '.rotateY', 0)
                obj_connection_rz = cmds.listConnections(obj + '.rotateZ', d=False, s=True) or []
                if not len(obj_connection_rz) > 0:
                    if cmds.getAttr(obj + '.rotateZ', lock=True) is False:
                        cmds.setAttr(obj + '.rotateZ', 0)

                obj_connection_sx = cmds.listConnections(obj + '.scaleX', d=False, s=True) or []
                if not len(obj_connection_sx) > 0:
                    if cmds.getAttr(obj + '.scaleX', lock=True) is False:
                        cmds.setAttr(obj + '.scaleX', 1)
                obj_connection_sy = cmds.listConnections(obj + '.scaleY', d=False, s=True) or []
                if not len(obj_connection_sy) > 0:
                    if cmds.getAttr(obj + '.scaleY', lock=True) is False:
                        cmds.setAttr(obj + '.scaleY', 1)
                obj_connection_sz = cmds.listConnections(obj + '.scaleZ', d=False, s=True) or []
                if not len(obj_connection_sz) > 0:
                    if cmds.getAttr(obj + '.scaleZ', lock=True) is False:
                        cmds.setAttr(obj + '.scaleZ', 1)
            except Exception as exception:
                logger.debug(str(exception))
                errors += str(exception) + '\n'
            return errors

    try:
        output_errors = reset_trans(current_selection)
    except Exception as e:
        logger.debug(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)

    if output_errors != '':
        cmds.warning("Some objects couldn't be reset. Open the script editor for a list of errors.")


def reset_joint_display():
    """
    Resets the radius attribute back to one in all joints,
    then changes the global multiplier (jointDisplayScale) back to one
    """
    try:
        desired_size = 1
        all_joints = cmds.ls(type='joint')
        for obj in all_joints:
            if cmds.objExists(obj):
                if cmds.getAttr(obj + ".radius", lock=True) is False:
                    cmds.setAttr(obj + '.radius', 1)

                if cmds.getAttr(obj + ".v", lock=True) is False:
                    cmds.setAttr(obj + '.v', 1)
        cmds.jointDisplayScale(desired_size)

    except Exception as exception:
        raise exception


def reset_persp_shape_attributes():
    """
    If persp shape exists (default camera), reset its attributes
    """
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
        except Exception as e:
            logger.debug(str(e))


""" ____________________________ Delete Functions ____________________________"""


def delete_namespaces():
    """Deletes all namespaces in the scene"""
    function_name = 'GTU Delete All Namespaces'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        default_namespaces = ['UI', 'shared']

        def num_children(namespace):
            """Used as a sort key, this will sort namespaces by how many children they have."""
            return namespace.count(':')

        namespaces = [namespace for namespace in cmds.namespaceInfo(lon=True, r=True) if
                      namespace not in default_namespaces]

        # Reverse List
        namespaces.sort(key=num_children, reverse=True)  # So it does the children first

        logger.debug(namespaces)

        for namespace in namespaces:
            if namespace not in default_namespaces:
                mel.eval('namespace -mergeNamespaceWithRoot -removeNamespace "' + namespace + '";')
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_display_layers():
    """ Deletes all display layers """
    function_name = 'GTU Delete All Display Layers'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        display_layers = cmds.ls(type='displayLayer')
        deleted_counter = 0
        for layer in display_layers:
            if layer != 'defaultLayer':
                cmds.delete(layer)
                deleted_counter += 1
        message = '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter) + ' </span>'
        is_plural = 'layers were'
        if deleted_counter == 1:
            is_plural = 'layer was'
        message += is_plural + ' deleted.'

        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_keyframes():
    """Deletes all keyframes. (Doesn't include Set Driven Keys)"""
    function_name = 'GTU Delete All Keyframes'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        keys_ta = cmds.ls(type='animCurveTA')
        keys_tl = cmds.ls(type='animCurveTL')
        keys_tt = cmds.ls(type='animCurveTT')
        keys_tu = cmds.ls(type='animCurveTU')
        # keys_ul = cmds.ls(type='animCurveUL') # Use optionVar to determine if driven keys should be deleted
        # keys_ua = cmds.ls(type='animCurveUA')
        # keys_ut = cmds.ls(type='animCurveUT')
        # keys_uu = cmds.ls(type='animCurveUU')
        deleted_counter = 0
        all_keyframes = keys_ta + keys_tl + keys_tt + keys_tu
        for obj in all_keyframes:
            try:
                cmds.delete(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))
        message = '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter) + ' </span>'
        is_plural = 'keyframe nodes were'
        if deleted_counter == 1:
            is_plural = 'keyframe node was'
        message += is_plural + ' deleted.'

        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_nucleus_nodes():
    """ Deletes all elements related to particles """
    errors = ''
    function_name = 'GTU Delete Nucleus Nodes'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)

        # Without Transform
        emitters = cmds.ls(typ='pointEmitter')
        solvers = cmds.ls(typ='nucleus')
        instancers = cmds.ls(typ='instancer')

        no_transforms = emitters + instancers + solvers + instancers

        # With Transform
        nparticle_nodes = cmds.ls(typ='nParticle')
        spring_nodes = cmds.ls(typ='spring')
        particle_nodes = cmds.ls(typ='particle')
        nrigid_nodes = cmds.ls(typ='nRigid')
        ncloth_nodes = cmds.ls(typ='nCloth')
        pfxhair_nodes = cmds.ls(typ='pfxHair')
        hair_nodes = cmds.ls(typ='hairSystem')
        nconstraint_nodes = cmds.ls(typ='dynamicConstraint')

        transforms = nparticle_nodes + spring_nodes + particle_nodes + nrigid_nodes
        transforms += ncloth_nodes + pfxhair_nodes + hair_nodes + nconstraint_nodes

        # Fields/Solvers Types
        # airField
        # dragField
        # newtonField
        # radialField
        # turbulenceField
        # uniformField
        # vortexField
        # volumeAxisField

        deleted_counter = 0
        for obj in transforms:
            try:
                parent = cmds.listRelatives(obj, parent=True) or []
                cmds.delete(parent[0])
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))
        for obj in no_transforms:
            try:
                cmds.delete(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        message = '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter) + ' </span>'
        is_plural = 'objects were'
        if deleted_counter == 1:
            is_plural = 'object was'
        message += is_plural + ' deleted.'

        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


def delete_user_defined_attributes():
    """ Deletes all User defined attributes for the selected objects. """
    function_name = 'GTU Delete User Defined Attributes'
    cmds.undoInfo(openChunk=True, chunkName=function_name)

    selection = cmds.ls(selection=True)
    if selection == 0:
        cmds.warning('Select at least one target object to delete custom attributes')
        return

    try:
        custom_attributes = []
        for sel in selection:
            attributes = cmds.listAttr(sel, userDefined=True) or []
            for attr in attributes:
                custom_attributes.append(sel + '.' + attr)

        deleted_counter = 0
        for obj in custom_attributes:
            try:
                cmds.deleteAttr(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))
        message = '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter) + ' </span>'
        is_plural = 'user defined attributes were'
        if deleted_counter == 1:
            is_plural = 'user defined attribute was'
        message += is_plural + ' deleted.'

        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_unused_nodes():
    """
    Creates a txt file and writes a list of objects to it (with necessary code used to select it, in Mel and Python)

    """
    num_deleted_nodes = mel.eval('MLdeleteUnused();')
    print(num_deleted_nodes)


def delete_all_locators():
    """ Deletes all locators """
    errors = ''
    function_name = 'GTU Delete All Locators'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)

        # With Transform
        locators = cmds.ls(typ='locator')

        deleted_counter = 0
        for obj in locators:
            try:
                parent = cmds.listRelatives(obj, parent=True) or []
                cmds.delete(parent[0])
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        message = '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter) + ' </span>'
        is_plural = 'locators were'
        if deleted_counter == 1:
            is_plural = 'locator was'
        message += is_plural + ' deleted.'

        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred when deleting locators. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


""" ____________________________ External Functions ____________________________"""


def curves_combine():
    """ Moves the shape objects of all selected curves under a single group (combining them) """
    errors = ''
    function_name = 'GTU Combine Curves'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        selection = cmds.ls(sl=True, absoluteName=True)
        valid_selection = True
        acceptable_types = ['nurbsCurve', 'bezierCurve']
        bezier_in_selection = []

        for obj in selection:
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
            for shape in shapes:
                if cmds.objectType(shape) == 'bezierCurve':
                    bezier_in_selection.append(obj)
                if cmds.objectType(shape) not in acceptable_types:
                    valid_selection = False
                    cmds.warning('Make sure you selected only curves.')

        if valid_selection and len(selection) < 2:
            cmds.warning('You need to select at least two curves.')
            valid_selection = False

        if len(bezier_in_selection) > 0 and valid_selection:
            user_input = cmds.confirmDialog(title='Bezier curve detected!',
                                            message='A bezier curve was found in your selection.\n'
                                                    'Would you like to convert Bezier to NURBS before combining?',
                                            button=['Yes', 'No'],
                                            defaultButton='Yes',
                                            cancelButton='No',
                                            dismissString='No',
                                            icon="warning")
            if user_input == 'Yes':
                for obj in bezier_in_selection:
                    logger.debug(str(obj))
                    cmds.bezierCurveToNurbs()

        if valid_selection:
            shapes = cmds.listRelatives(shapes=True, fullPath=True)
            for obj in range(len(selection)):
                cmds.makeIdentity(selection[obj], apply=True, rotate=True, scale=True, translate=True)

            group = cmds.group(empty=True, world=True, name=selection[0])
            cmds.refresh()
            cmds.select(shapes[0])
            for obj in range(1, (len(shapes))):
                cmds.select(shapes[obj], add=True)

            cmds.select(group, add=True)
            cmds.parent(relative=True, shape=True)
            cmds.delete(selection)

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred when combining the curves. Open the script editor for more information.')
    finally:

        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


def curves_separate():
    """
    Moves the shapes instead of a curve to individual transforms (separating curves) 
    """
    errors = ''
    acceptable_types = ['nurbsCurve', 'bezierCurve']

    def get_short_name(full_name):
        """
        Get the name of the objects without its path (Maya returns full path if name is not unique)

        Args:
            full_name (string) - object to extract short name
        """
        short_name = ''
        if full_name == '':
            return ''
        split_path = full_name.split('|')
        if len(split_path) >= 1:
            short_name = split_path[len(split_path) - 1]
        return short_name

    function_name = 'GTU Separate Curves'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        selection = cmds.ls(sl=True)
        valid_selection = True

        curve_shapes = []
        parent_transforms = []

        if len(selection) < 1:
            valid_selection = False
            cmds.warning('You need to select at least one curve.')

        if valid_selection:
            for obj in selection:
                shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                for shape in shapes:
                    if cmds.objectType(shape) in acceptable_types:
                        curve_shapes.append(shape)

            if len(curve_shapes) == 0:
                cmds.warning('You need to select at least one curve.')
            elif len(curve_shapes) > 1:
                for obj in curve_shapes:
                    parent = cmds.listRelatives(obj, parent=True) or []
                    for par in parent:
                        if par not in parent_transforms:
                            parent_transforms.append(par)
                        cmds.makeIdentity(par, apply=True, rotate=True, scale=True, translate=True)
                    group = cmds.group(empty=True, world=True, name=get_short_name(obj).replace('Shape', ''))
                    cmds.parent(obj, group, relative=True, shape=True)
            else:
                cmds.warning('The selected curve contains only one shape.')

            for obj in parent_transforms:
                shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                if cmds.objExists(obj) and cmds.objectType(obj) == 'transform' and len(shapes) == 0:
                    cmds.delete(obj)

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred when separating the curves. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


def convert_bif_to_mesh():
    """
    Converts Bifrost geometry to Maya geometry
    """
    errors = ''
    function_name = 'GTU Convert Bif to Mesh'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        valid_selection = True

        selection = cmds.ls(selection=True)
        bif_objects = []
        bif_graph_objects = []

        if len(selection) < 1:
            valid_selection = False
            cmds.warning('You need to select at least one bif object.')

        if valid_selection:
            for obj in selection:
                shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                for shape in shapes:
                    if cmds.objectType(shape) == 'bifShape':
                        bif_objects.append(shape)
                    if cmds.objectType(shape) == 'bifrostGraphShape':
                        bif_graph_objects.append(shape)

            for bif in bif_objects:
                parent = cmds.listRelatives(bif, parent=True) or []
                for par in parent:
                    source_mesh = cmds.listConnections(par + '.inputSurface', source=True, plugs=True) or []
                    for sm in source_mesh:
                        conversion_node = cmds.createNode("bifrostGeoToMaya")
                        cmds.connectAttr(sm, conversion_node + '.bifrostGeo')
                        mesh_node = cmds.createNode("mesh")
                        mesh_transform = cmds.listRelatives(mesh_node, parent=True) or []
                        cmds.connectAttr(conversion_node + '.mayaMesh[0]', mesh_node + '.inMesh')
                        cmds.rename(mesh_transform[0], 'bifToGeo1')
                        try:
                            cmds.hyperShade(assign='lambert1')
                        except Exception as e:
                            logger.debug(str(e))

            for bif in bif_graph_objects:
                bifrost_attributes = cmds.listAttr(bif, fp=True, inUse=True, read=True) or []
                for output in bifrost_attributes:
                    conversion_node = cmds.createNode("bifrostGeoToMaya")
                    cmds.connectAttr(bif + '.' + output, conversion_node + '.bifrostGeo')
                    mesh_node = cmds.createNode("mesh")
                    mesh_transform = cmds.listRelatives(mesh_node, parent=True) or []
                    cmds.connectAttr(conversion_node + '.mayaMesh[0]', mesh_node + '.inMesh')
                    bif_mesh = cmds.rename(mesh_transform[0], 'bifToGeo1')
                    try:
                        cmds.hyperShade(assign='lambert1')
                    except Exception as e:
                        logger.debug(str(e))

                    vtx = cmds.ls(bif_mesh + '.vtx[*]', fl=True) or []
                    if len(vtx) == 0:
                        try:
                            cmds.delete(bif_mesh)
                            # cmds.delete(conversion_node)
                            # cmds.delete(mesh_node)
                        except Exception as e:
                            logger.debug(str(e))
    except Exception as e:
        errors += str(e) + '\n'
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        cmds.warning('An error occurred when converting bif to mesh. Open the script editor for more information.')
        print('######## Errors: ########')
        print(errors)


def convert_joints_to_mesh(combine_mesh=True):
    """
    Converts a joint hierarchy into a mesh representation of it (Helpful when sending it to sculpting apps)
    Args:
        combine_mesh: Combines generated meshes into one

    Returns:
        A list of generated meshes
    """
    selection = cmds.ls(selection=True, type='joint')
    if len(selection) != 1:
        cmds.warning('Please selection only the root joint and try again.')
        return
    cmds.select(selection[0], replace=True)
    cmds.select(hierarchy=True)
    joints = cmds.ls(selection=True, type='joint')

    generated_mesh = []
    for obj in reversed(joints):
        if cmds.objExists(obj):
            joint_name = obj.split('|')[-1]
            radius = cmds.getAttr(obj + '.radius')
            joint_sphere = cmds.polySphere(radius=radius * .5,
                                           subdivisionsAxis=8,
                                           subdivisionsHeight=8,
                                           axis=[1, 0, 0],
                                           name=joint_name + 'JointMesh',
                                           ch=False)
            generated_mesh.append(joint_sphere[0])
            cmds.delete(cmds.parentConstraint(obj, joint_sphere))
            joint_parent = cmds.listRelatives(obj, parent=True) or []
            if joint_parent:
                joint_cone = cmds.polyCone(radius=radius * .5,
                                           subdivisionsAxis=4,
                                           name=joint_name + 'BoneMesh',
                                           ch=False)
                generated_mesh.append(joint_cone[0])
                bbox = cmds.exactWorldBoundingBox(joint_cone)
                bottom = [(bbox[0] + bbox[3]) / 2, bbox[1], (bbox[2] + bbox[5]) / 2]
                cmds.xform(joint_cone, piv=bottom, ws=True)
                cmds.move(1, joint_cone, moveY=True)
                cmds.rotate(90, joint_cone, rotateX=True)
                cmds.rotate(90, joint_cone, rotateY=True)
                cmds.makeIdentity(joint_cone, rotate=True, apply=True)

                cmds.delete(cmds.parentConstraint(joint_parent, joint_cone))
                cmds.delete(cmds.aimConstraint(obj, joint_cone))

                child_pos = cmds.xform(obj, t=True, ws=True, query=True)
                cmds.xform(joint_cone[0] + '.vtx[4]', t=child_pos, ws=True)
    if combine_mesh:
        cmds.select(generated_mesh, replace=True)
        mesh = cmds.polyUnite()
        cmds.select(clear=True)
        cmds.delete(mesh, constructionHistory=True)
        mesh = cmds.rename(mesh[0], selection[0] + 'AsMesh')
        return [mesh]
    else:
        return generated_mesh


""" ____________________________ About Window ____________________________"""


def build_gui_about_gt_tools():
    """ Creates "About" window for the GT Tools menu """

    stored_gt_tools_version_exists = cmds.optionVar(exists="gt_tools_version")

    # Define Version
    if stored_gt_tools_version_exists:
        gt_version = cmds.optionVar(q="gt_tools_version")
    else:
        gt_version = '?'

    window_name = "build_gui_about_gt_tools"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title="About - GT Tools", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    cmds.columnLayout("main_column", p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column")  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")  # Title Column
    cmds.text("GT Tools", bgc=[.4, .4, .4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p="main_column")  # Empty Space

    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.text(l='Version Installed: ' + gt_version, align="center", fn="boldLabelFont")
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='GT Tools is a free collection of Maya scripts', align="center")

    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='About:', align="center", fn="boldLabelFont")
    cmds.text(l='This is my collection of scripts for Autodesk Maya.\n'
                'These scripts were created with the aim of automating,\n e'
                'nhancing or simply filling the missing details of what\n I find lacking in Maya.', align="center")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(
        l='When installed you can find a pull-down menu that\n provides easy access to a variety of related tools.',
        align="center")
    cmds.separator(h=5, style='none')  # Empty Space
    cmds.text(l='This menu contains sub-menus that have been\n organized to contain related tools.\n '
                'For example: modeling, rigging, utilities, etc...', align="center")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='All of these items are supplied as is.\nYou alone are responsible for any issues.\n'
                'Use at your own risk.', align="center")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Hopefully these scripts are helpful to you\nas they are to me.', align="center")
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


def output_string_to_notepad(string, file_name='tmp'):
    """
    Creates a txt file and writes a list of objects to it (with necessary code used to select it, in Mel and Python)

    Args:
        string (string): A list of string to be exported to a txt file
        file_name (string): Name of the generated file

    """
    temp_dir = cmds.internalVar(userTmpDir=True)
    txt_file = temp_dir + file_name + '.txt'

    f = open(txt_file, 'w')
    f.write(string)
    f.close()

    notepad_command = 'exec("notepad ' + txt_file + '");'
    mel.eval(notepad_command)


# """ ____________________________ Functions Calls ____________________________"""
if __name__ == '__main__':
    pass
    # force_reload_file()
    # open_resource_browser()
    # unlock_default_channels()
    # unhide_default_channels()
    # references_import()
    # references_remove()
    # toggle_uniform_lra()
    # toggle_uniform_jnt_label()
    # select_non_unique_objects()
    #
    # generate_udim_previews()
    # material_copy()
    # material_paste()
    #
    # move_pivot_to_top()
    # move_pivot_to_base()
    # move_to_origin()
    #
    # reset_joint_display()
    # reset_transforms()
    # reset_persp_shape_attributes()
    #
    # delete_namespaces()
    # delete_display_layers()
    # delete_keyframes()
    # delete_nucleus_nodes()
    # delete_user_defined_attributes()
    # delete_unused_nodes()
    # delete_all_locators()
    #
    # # --- Outside Utilities ---
    # curves_combine()
    # curves_separate()
    # convert_bif_to_mesh()
    #
    # build_gui_about_gt_tools()
    #
    # # --- Other Functions ---
    # toggle_full_hud()
    # convert_joints_to_mesh()
    # output_string_to_notepad('Test')
