"""
Attribute Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.feedback_utils import FeedbackMessage
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

DEFAULT_CHANNELS = ['t', 'r', 's']
DEFAULT_DIMENSIONS = ['x', 'y', 'z']


def set_unlocked_os_attr(target, attr, value):
    """
    Sets an attribute to the provided value in case it's not locked (Uses "cmds.setAttr" function so object space)

    Args:
        target (str): Name of the target object (object that will receive transforms)
        attr (str): Name of the attribute to apply (no need to add ".", e.g. "rx" would be enough)
        value (float): Value used to set attribute. e.g. 1.5, 2, 5...
    """
    try:
        if not cmds.getAttr(target + '.' + attr, lock=True):
            cmds.setAttr(target + '.' + attr, value)
    except Exception as e:
        logger.debug(str(e))


def set_unlocked_ws_attr(target, attr, value_tuple):
    """
    Sets an attribute to the provided value in case it's not locked (Uses "cmds.xform" function with world space)

    Args:
        target (str): Name of the target object (object that will receive transforms)
        attr (str): Name of the attribute to apply (no need to add ".", e.g. "rx" would be enough)
        value_tuple (tuple): A tuple with three (3) floats used to set attributes. e.g. (1.5, 2, 5)

    """
    try:
        if attr == 'translate':
            cmds.xform(target, ws=True, t=value_tuple)
        if attr == 'rotate':
            cmds.xform(target, ws=True, ro=value_tuple)
        if attr == 'scale':
            cmds.xform(target, ws=True, s=value_tuple)
    except Exception as e:
        logger.debug(str(e))


def get_existing_attribute_value(obj, attr, not_found_result=None):
    """
    Tries to get attribute out of an object.
    If either obj or attribute doesn't exist, it returns the provided parameter: not_found_result
    Args:
        obj (str): Object name
        attr (str): attribute long or short name, for example "visibility" or "v" (no need for ".")
        not_found_result (optional, any): This is returned in case the attribute is not found.

    Returns:
        Value stored in the attribute, or not_found_result if attribute doesn't exist
    """
    if not cmds.objExists(obj):
        logger.debug("Object not found: " + str(obj))
        return not_found_result
    attributes = cmds.listAttr(obj) or []
    if attr in attributes:
        return cmds.getAttr(obj + "." + attr)
    else:
        return not_found_result
        
        
def hide_lock_default_attributes(obj, include_visibility=False):
    """
    Locks default TRS channels
    Args:
        obj (str): Name of the object to lock TRS attributes
        include_visibility (optional, bool): If active, also locks and hides visibility
    """
    for channel in ['t', 'r', 's']:
        for axis in ['x', 'y', 'z']:
            cmds.setAttr(obj + '.' + channel + axis, l=True, k=False, channelBox=False)
    if include_visibility:
        cmds.setAttr(obj + '.v', l=True, k=False, channelBox=False)


def add_attributes(target_list,
                   attributes,
                   attr_type,
                   minimum, maximum,
                   default, status='keyable'):

    logger.debug('target_list: ' + str(target_list))
    logger.debug('attributes: ' + str(attributes))
    logger.debug('attr_type: ' + str(attr_type))
    logger.debug('minimum: ' + str(minimum))
    logger.debug('maximum: ' + str(maximum))
    logger.debug('default: ' + str(default))
    logger.debug('status: ' + str(status))

    issues = ''

    for target_obj in target_list:
        current_user_attributes = cmds.listAttr(target_obj, userDefined=True) or []
        print(current_user_attributes)
        for attr in attributes:
            if attr not in current_user_attributes:
                cmds.addAttr(target_obj, ln=attr, at=attr_type, k=True)
            else:
                issue = '\nUnable to add "' + target_obj + '.' + attr + '".'
                issue += ' Object already has an attribute with the same name'
                issues += issue

    if issues:
        print(issues)

 
def attr_to_list(obj_list, printing=True, decimal_place=2, separate_channels=False, strip_zeroes=True):
    """
    Returns transforms as list
    Args:
        obj_list (list, none): List objects to extract the transform from (if empty, it will try to use selection)
        printing (optional, bool): If active, the function will print the values to the script editor
        decimal_place (optional, int): How precise you want the extracted values to be (formats the float it gets)
        separate_channels (optional, bool): If separating channels, it will return T, R and S as different lists
        strip_zeroes (optional, bool): If active, it will remove unnecessary zeroes (e.g. 0.0 -> 0)

    Returns:
        A list with transform values. [TX, TY, TZ, RX, RY, RZ, SX, SY, SZ]
        For example: attr_list = [0, 0, 0, 15, 15, 15, 1, 1, 1] # TRS (XYZ)

    """
    if not obj_list:
        obj_list = cmds.ls(selection=True)
    if not obj_list:
        return

    output = ''
    if printing:
        output += ('#' * 80)

    for obj in obj_list:
        output += '\n# Transform Data for "' + obj + '":\n'
        data = []
        for channel in DEFAULT_CHANNELS:  # TRS
            for dimension in DEFAULT_DIMENSIONS:  # XYZ
                value = cmds.getAttr(obj + '.' + channel + dimension)
                if strip_zeroes:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f"))).rstrip('0').rstrip('.')
                    if formatted_value == '-0':
                        formatted_value = '0'
                    data.append(formatted_value)
                else:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f")))
                    if formatted_value == '-0.0':
                        formatted_value = '0.0'
                    data.append(formatted_value)

        if not separate_channels:
            output += 'object = "' + str(obj) + '"\n'
            output += 'trs_attr_list = ' + str(data).replace("'", "") + '\n'
        else:
            output += 'object = "' + str(obj) + '"\n'
            output += 't_attr_list = [' + str(data[0]) + ', ' + str(data[1]) + ', ' + str(data[2]) + ']\n'
            output += 'r_attr_list = [' + str(data[3]) + ', ' + str(data[4]) + ', ' + str(data[5]) + ']\n'
            output += 's_attr_list = [' + str(data[6]) + ', ' + str(data[7]) + ', ' + str(data[8]) + ']\n'

    # Return / Print
    if printing:
        output += ('#' * 80)
        if output.replace('#', ''):
            print(output)
            return output
        else:
            print('No data found. Make sure your selection at least one object with unlocked transforms.')
            return None
    else:
        return output
        
        
def default_attr_to_python(obj_list, printing=True, use_loop=False, decimal_place=2, strip_zeroes=True):
    """
    TODO
    Args:
        obj_list (list, none): List objects to extract the transform from (if empty, it will try to use selection)
        printing (optional, bool): If active, the function will print the values to the script editor
        use_loop (optional, bool): If active, it will use a for loop in the output code (instead of simple lines)
        decimal_place (optional, int): How precise you want the extracted values to be (formats the float it gets)
        strip_zeroes (optional, bool): If active, it will remove unnecessary zeroes (e.g. 0.0 -> 0)

    Returns:
        Python code with extracted transform values

    """
    if not obj_list:
        obj_list = cmds.ls(selection=True)
    if not obj_list:
        return

    output = ''
    if printing:
        output += ('#' * 80)

    for obj in obj_list:
        output += '\n# Transform Data for "' + obj + '":\n'
        data = {}
        for channel in DEFAULT_CHANNELS:  # TRS
            for dimension in DEFAULT_DIMENSIONS:  # XYZ
                # Extract Values
                value = cmds.getAttr(obj + '.' + channel + dimension)
                if strip_zeroes:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f"))).rstrip('0').rstrip(
                        '.')
                    if formatted_value == '-0':
                        formatted_value = '0'
                else:
                    formatted_value = str(float(format(value, "." + str(decimal_place) + "f")))
                    if formatted_value == '-0.0':
                        formatted_value = '0.0'
                    output += formatted_value + ')\n'
                # Populate Value Messages/Data
                if not cmds.getAttr(obj + '.' + channel + dimension, lock=True) and not use_loop:
                    output += 'cmds.setAttr("' + obj + '.' + channel + dimension + '", '
                    # Populate Non-loop output
                    output += formatted_value + ')\n'
                else:
                    data[channel + dimension] = formatted_value

        # Loop Version
        if use_loop:
            output += 'for key, value in ' + str(data) + '.items():\n'
            output += '\tif not cmds.getAttr(' + obj + '. + key, lock=True):\n'
            output += '\t\tcmds.setAttr("' + obj + '." + key, value)\n'

    # Return / Print
    if printing:
        output += ('#' * 80)
        if output.replace('#', ''):
            print(output)
            return output
        else:
            print('No data found. Make sure your selection at least one object with unlocked transforms.')
            return None
    else:
        return output


def user_attr_to_python(obj_list, printing=True):
    """
    Returns a string
    Args:
        obj_list (list, none): List objects to extract the transform from (if empty, it will try to use selection)
        printing (optional, bool): If active, the function will print the values to the script editor

    Returns:
        Python code with extracted transform values

    """
    if not obj_list:
        obj_list = cmds.ls(selection=True)
    if not obj_list:
        return

    output = ''
    if printing:
        output += ('#' * 80)

    for obj in obj_list:
        output += '\n# User-Defined Attribute Data for "' + obj + '":\n'
        attributes = cmds.listAttr(obj, userDefined=True) or []
        if not attributes:
            output += '# No user-defined attributes found on this object.\n'
        else:
            for attr in attributes:  # TRS
                # not cmds.getAttr(obj + '.' + attr, lock=True) # TODO Check if locked
                attr_type = cmds.getAttr(obj + '.' + attr, typ=True)
                value = cmds.getAttr(obj + '.' + attr)
                if attr_type == 'double3':
                    pass
                elif attr_type == 'string':
                    output += 'cmds.setAttr("' + obj + '.' + attr + '", """' + str(value) + '""", typ="string")\n'
                else:
                    output += 'cmds.setAttr("' + obj + '.' + attr + '", ' + str(value) + ')\n'

    # Return / Print
    if printing:
        output += ('#' * 80)
        if output.replace('#', ''):
            print(output)
            return output
        else:
            print('No data found. Make sure your selection at least one object with user-defined attributes.')
            return None
    else:
        return output


def unlock_default_channels():
    """ Unlocks Translate, Rotate, Scale for the selected objects """
    function_name = 'Unlock Default Channels'
    errors = ''
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    selection = cmds.ls(selection=True, long=True)
    if not selection:
        cmds.warning('Nothing selected. Please select an object and try again.')
        return
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

    feedback = FeedbackMessage(quantity=unlocked_counter,
                               singular='object had its',
                               plural='objects had their',
                               conclusion='default channels unlocked.')
    feedback.print_inview_message()


def unhide_default_channels():
    """ Un-hides Translate, Rotate, Scale for the selected objects """
    function_name = 'GTU Unhide Default Channels'
    errors = ''
    cmds.undoInfo(openChunk=True, chunkName=function_name)  # Start undo chunk
    selection = cmds.ls(selection=True, long=True)
    if not selection:
        cmds.warning('Nothing selected. Please select an object and try again.')
        return
    selection_short = cmds.ls(selection=True)
    unhide_counter = 0
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
                unhide_counter += 1
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

    feedback = FeedbackMessage(quantity=unhide_counter,
                               singular='object had its',
                               plural='objects had their',
                               conclusion='default channels made visible.')
    feedback.print_inview_message()


def delete_user_defined_attributes(delete_locked=True):
    """
    Deletes all User defined attributes for the selected objects.
    Args:
        delete_locked (bool, optional): If active, it will also delete locked attributes.
    """
    function_name = 'Delete User Defined Attributes'
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
                custom_attributes.append(f'{sel}.{attr}')

        deleted_counter = 0
        for attr in custom_attributes:
            try:
                if delete_locked:
                    cmds.setAttr(f"{attr}", lock=False)
                cmds.deleteAttr(attr)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        feedback = FeedbackMessage(quantity=deleted_counter,
                                   singular='user-defined attribute was',
                                   plural='user-defined attributes were',
                                   conclusion='deleted.',
                                   zero_overwrite_message='No user defined attributes were deleted.')
        feedback.print_inview_message()

    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def add_attr_double_three(obj, attr_name, suffix="RGB", keyable=True):
    """
    Creates a double3 attribute and populates it with three (3) double attributes of the same name + suffix
    Args:
        obj (str): Name of the object to receive new attributes
        attr_name (str): Name of the attribute to be created
        suffix (str, optional) : Used as suffix for the three created attributes
        keyable (bool, optional): Determines if the attributes should be keyable or not. (Must be a 3 character string)
                                  First attribute uses the first letter, second the second letter, etc...
    """
    cmds.addAttr(obj, ln=attr_name, at='double3', k=keyable)
    cmds.addAttr(obj, ln=attr_name + suffix[0], at='double', k=keyable, parent=attr_name)
    cmds.addAttr(obj, ln=attr_name + suffix[1], at='double', k=keyable, parent=attr_name)
    cmds.addAttr(obj, ln=attr_name + suffix[2], at='double', k=keyable, parent=attr_name)


def add_separator_attr(target_object, attr_name="separator", custom_value=None):
    """
    Creates a locked enum attribute to be used as a separator
    Args:
        target_object (str): Name of the object to affect in the operation
        attr_name (str, optional): Name of the attribute to add. Use camelCase for this string as it will obey the
                                   "niceName" pattern in Maya. e.g. "niceName" = "Nice Name"
        custom_value (str, None, optional): Enum value for the separator value.
                                               If not provided, default is "-------------".
    Returns:
        str: Full path to created attribute. 'target_object.attr_name'
    """
    separator_value = "-"*13
    if custom_value:
        separator_value = custom_value
    attribute_path = f'{target_object}.{attr_name}'
    if not cmds.objExists(attribute_path):
        cmds.addAttr(target_object, ln=attr_name, at='enum', en=separator_value, keyable=True)
        cmds.setAttr(attribute_path, e=True, lock=True)
    else:
        logger.warning(f'Separator attribute "{attribute_path}" already exists. Add Separator operation skipped.')
    return f'{target_object}.{attr_name}'


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    add_separator_attr(cmds.ls(selection=True)[0])
    out = None
    pprint(out)
