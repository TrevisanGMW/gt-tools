"""
Display Utilities - Update how you see elements in the viewport
This script should not import "maya.cmds" as it's also intended to be used outside of Maya.
github.com/TrevisanGMW/gt-tools
"""
import maya.cmds as cmds
import maya.mel as mel
import logging
import random
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def toggle_uniform_lra():
    """
    Makes the visibility of the Local Rotation Axis uniform among
    the selected objects according to the current state of the majority of them.
    """
    function_name = 'Uniform LRA Toggle'
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

    function_name = 'Uniform Joint Label Toggle'
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
            message = 'No joints found in this scene.'
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


def set_joint_name_as_label():
    """
    Transfer the selected joint name to
    """

    selection_joints = cmds.ls(selection=True, typ="joint") or []

    if not selection_joints:
        cmds.warning("No joints found in selection. Select joints and try again.")
        return

    function_name = 'GTU Set Joint Name as Label'
    counter = 0
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        for joint in selection_joints:
            short_name = get_short_name(joint)
            cmds.setAttr(joint + '.side', 0)  # Center (No Extra String)
            cmds.setAttr(joint + '.type', 18)  # Other
            cmds.setAttr(joint + '.otherType', short_name, typ="string")
            counter += 1
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)

    if counter > 0:
        is_plural = 'labels were'
        if counter == 1:
            is_plural = 'label was'
        in_view_message = '<' + str(random.random()) + '>'
        in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(counter)
        in_view_message += '</span> joint ' + is_plural + ' updated.'
        message = '\n' + str(counter) + ' joint ' + is_plural + ' updated.'
        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
        sys.stdout.write(message)
    else:
        in_view_message = '<' + str(random.random()) + '>'
        in_view_message += 'No labels were updated.'
        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)


def generate_udim_previews():
    """ Generates UDIM previews for all file nodes """
    errors = ''
    all_file_nodes = cmds.ls(type='file')
    for file_node in all_file_nodes:
        try:
            mel.eval('generateUvTilePreview ' + file_node + ';')
        except Exception as e:
            errors += str(e) + '\n'

    if errors:
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)

    unique_message = '<' + str(random.random()) + '>'
    message = unique_message + 'Previews generated for all <span style=\"color:#FF0000;text-decoration:underline;\"> ' \
                               'UDIM</span> file nodes.'
    cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)


def reset_joint_display():
    """
    Resets the radius and drawStyle attributes for all joints,
    then changes the global multiplier (jointDisplayScale) back to one
    """
    errors = ''
    target_radius = 1
    counter = 0
    all_joints = cmds.ls(type='joint', long=True)
    all_joints_short = cmds.ls(type='joint')
    for obj in all_joints:
        try:
            if cmds.objExists(obj):
                if cmds.getAttr(obj + ".radius", lock=True) is False:
                    cmds.setAttr(obj + '.radius', 1)

                if cmds.getAttr(obj + ".v", lock=True) is False:
                    cmds.setAttr(obj + '.v', 1)

                if cmds.getAttr(obj + ".drawStyle", lock=True) is False:
                    cmds.setAttr(obj + '.drawStyle', 0)
                counter += 1
        except Exception as exception:
            logger.debug(str(exception))
            errors += str(exception) + '\n'
    cmds.jointDisplayScale(target_radius)

    if counter > 0:
        affected = str(counter)
        is_plural = 'joints had their'
        if counter == 1:
            is_plural = 'had its'
            affected = '"' + all_joints_short[0] + '"'
        in_view_message = '<' + str(random.random()) + '>'
        in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + affected
        in_view_message += '</span> ' + is_plural + ' display reset.'
        message = '\n' + affected + ' ' + is_plural + ' "radius", "drawStyle" and "visibility" attributes reset.'
        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
        sys.stdout.write(message)
    else:
        in_view_message = '<' + str(random.random()) + '>'
        in_view_message += 'No joints found in this scene.'
        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)

    if errors:
        print(('#' * 50) + '\n')
        print(errors)
        print('#' * 50)
        cmds.warning('A few joints were not fully reset. Open script editor for more details.')


def delete_display_layers():
    """ Deletes all display layers """
    function_name = 'Delete All Display Layers'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    try:
        display_layers = cmds.ls(type='displayLayer')
        deleted_counter = 0
        for layer in display_layers:
            if layer != 'defaultLayer':
                cmds.delete(layer)
                deleted_counter += 1
        in_view_message = '<' + str(random.random()) + '>'
        if deleted_counter > 0:
            in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter)
            in_view_message += ' </span>'
            is_plural = 'layers were'
            if deleted_counter == 1:
                is_plural = 'layer was'
            in_view_message += is_plural + ' deleted.'
        else:
            in_view_message += 'No display layers found in this scene.'

        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
