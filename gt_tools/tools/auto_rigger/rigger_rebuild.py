"""
GT Rigger - Biped Rigger Re-build Script (Rebuilder)
github.com/TrevisanGMW/gt-tools - 2022-09-28

0.0.1 - 2022-09-28
Created initial setup

0.0.2 to 0.0.3 - 2022-09-30
Added initial control shape extraction
Added data object (control list)

0.0.4 to 0.0.5 - 2022-10-05
Separated extract, re-build and transfer into their own functions

0.0.6 - 2022-10-05
Added control generation to rebuild function
Added more debug prints to current functions

0.0.7 - 2022-10-06
Added user-defined attributes extraction and transfer

0.0.8 to 0.0.9 - 2022-10-13
Added facial and corrective proxy extraction
Added facial and corrective rebuild steps

0.0.10 to 0.0.11 - 2022-11-03
Added functionary to extract default channels (TRS+V)
Added transform extraction (for the position of a few controls)
Renamed extract and set attribute functions

0.0.12 to 0.0.13 - 2022-11-04
Added "evaluate_python_string" to be used in teardown and setup actions
Added teardown and setup script execution

0.0.14 - 2023-01-10
Un-parented objects found inside geometry_grp before rebuilding


UI Idea:
 [<Activation>]   <STEP-NAME>  <STEP-STATUS>  <HELP-?>

TODO
    Add bound joint extraction
    Add skin weights extraction
    Add control custom attributes extraction
    Add corrective and facial reference position
    Add side GUI, fingers and feet positioning
"""
from rigger_utilities import *
from rigger_data import *
from rigger_facial_logic import create_facial_proxy
from rigger_corrective_logic import create_corrective_proxy
import rigger_biped_gui as rigger_gui
import maya.cmds as cmds
import traceback
import logging
import json
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_rigger_rebuild")
logger.setLevel(logging.INFO)

# Data Object
data_rebuild = GTBipedRiggerRebuildData()
# if not data_biped:  # Create one in case not already available
data_biped = GTBipedRiggerData()
data_facial = GTBipedRiggerFacialData()
data_corrective = GTBipedRiggerCorrectiveData()


def evaluate_python_string(py_string, custom_error_message=None):
    """
    Executes provided string python code

    Args:
        py_string (string): Python code to be executed. e.g. "print("hello world")"
        custom_error_message (string, optional): If provided, this string will be used as a warning for when an error
                                                 occurs during the code execution

    Returns:
        operation_result (bool): True if there were no errors, False if an error occurred during execution
    """
    try:
        exec(py_string)
        return True
    except Exception as e:
        if custom_error_message:
            cmds.warning(custom_error_message)
        else:
            cmds.warning("An error occurred while executing string python code. "
                         "(Open script editor for more information)")
        logger.debug(str(e))
        logger.debug(traceback.format_exc())
        return False


def extract_proxy_metadata(data_object):
    """ Extracts Rig Metadata """
    proxy_source_obj_name = data_object.proxy_storage_variables.get('source_object_name')
    proxy_attr_name = data_object.proxy_storage_variables.get('attr_name')

    # Source Object Validation
    if not cmds.objExists(proxy_source_obj_name):
        return

    # Source Attribute Validation
    proxy_attr = proxy_source_obj_name + '.' + proxy_attr_name
    if not cmds.objExists(proxy_attr):
        return

    # Attempt to Extract Proxy
    export_dict = cmds.getAttr(proxy_attr)
    try:
        export_dict = json.loads(str(export_dict))
    except Exception as e:
        logger.debug(str(e))

    return export_dict


def transfer_biped_base_settings(data_object, metadata):
    """
    Update base settings so when rebuilding the rig, it will follow the same rules

    ARgs:
        data_object: biped data object, used to build the rig (carry the used settings)
        metadata: Extracted metadata, JSON format containing rigging settings
    """
    to_transfer = ['using_no_ssc_skeleton', 'uniform_ctrl_orient', 'worldspace_ik_orient', 'simplify_spine']
    for option in to_transfer:
        if metadata.get(option) is not None:
            # logger.debug(str(option) + ': ' + str(metadata.get(option)))
            data_object.settings[option] = metadata.get(option)


def extract_python_curve_shape_data(curve_transforms):
    """
    Extracts the Python code necessary to reshape
    Args:
        curve_transforms (list of strings): Transforms carrying curve shapes inside them (nurbs or bezier)

    Returns:
        python_string (string): Python code with the current state of the selected curves (their shape)

    Modified version of the function from "gt_shape_extract_shape"
    """
    result = {}

    for crv in curve_transforms:
        valid_types = ['nurbsCurve', 'bezierCurve']
        accepted_shapes = []
        curve_shapes = cmds.listRelatives(crv, shapes=True, fullPath=True) or []
        # Filter valid shapes:
        for shape in curve_shapes:
            current_shape_type = cmds.objectType(shape)
            if current_shape_type in valid_types:
                accepted_shapes.append(shape)

        # Extract CVs into Python code:
        for shape in accepted_shapes:
            extracted_crv_data = zip(cmds.ls('%s.cv[*]' % shape, flatten=True), cmds.getAttr(shape + '.cv[*]'))
            curve_data_list = list(extracted_crv_data)
            if curve_data_list:
                result[str(shape).split('|')[-1]] = curve_data_list
    else:
        return result


def apply_python_curve_shape_data(extracted_shapes):
    """
    Applies JSON data extracted from curves using  extract_python_curve_shape_data
    Args:
        extracted_shapes (json, dict): JSON data extracted using "extract_python_curve_shape_data"
    """
    errors = ''
    for key in extracted_shapes:
        curve_data = extracted_shapes.get(key)
        for cv in curve_data:
            try:
                cmds.xform(cv[0], os=True, t=cv[1])
            except Exception as e:
                error = str(e)
                if ".cv" in str(e):
                    error = error.split('.')[0]
                if error not in errors:
                    errors += error + '\n'

    if errors:
        print("*" * 80)
        print("Errors when updating shapes:")
        print(errors)


def extract_dict_attributes(obj_list, default_channels=False, user_defined=True):
    """
    Extracts attributes and store them in a dictionary
    Args:
        obj_list (list, none): List objects to extract the transform from (if empty, it will try to use selection)
        default_channels (bool, optional) If it should include default channels (TRS)
        user_defined (bool, optional) If it should include user-defined attributes

    Returns:
        dictionary with extracted values. Key = "object.attribute" Value = "attributeValue"

    """
    if not obj_list:
        obj_list = cmds.ls(selection=True)
    if not obj_list:
        return

    output = {}

    # Default channels (TRS+V)
    if default_channels:
        for obj in obj_list:
            for channel in ["t", "r", "s"]:  # TRS
                for axis in ["x", "y", "z"]:  # XYZ
                    value = cmds.getAttr(obj + '.' + channel + axis)
                    output[obj + '.' + channel + axis] = str(value)
            visible = cmds.getAttr(obj + '.v')  # Visibility
            output[obj + '.v'] = str(visible)

    # User-defined
    if user_defined:
        for obj in obj_list:
            attributes = cmds.listAttr(obj, userDefined=True) or []
            if attributes:
                for attr in attributes:  # TRS
                    attr_type = cmds.getAttr(obj + '.' + attr, typ=True)
                    value = cmds.getAttr(obj + '.' + attr)
                    if attr_type != 'double3':
                        output[obj + '.' + attr] = str(value)
    return output


def set_dict_attributes(user_defined_dict):
    """
    Sets attributes found in a dictionary

    Args:
        user_defined_dict (dict): Dictionary where the key is the object and its attribute and
                                  the value is the value to set. Key = "object.attribute" Value = "attributeValue"
    """
    for key in user_defined_dict:
        try:
            if cmds.objExists(key):
                if not cmds.getAttr(key, lock=True) and not cmds.listConnections(key, source=True, destination=False):
                    attr_type = cmds.getAttr(key, typ=True)
                    if attr_type != 'string':
                        eval('cmds.setAttr("' + key + '", ' + user_defined_dict.get(key) + ')')
                    else:
                        eval('cmds.setAttr("' + key + '", """' + user_defined_dict.get(key) + '""", typ="string")')
        except Exception as e:
            logger.debug(str(e))


def extract_current_rig_data(data_rebuild_object):
    """
    Extracts data from current rig
    Args:
       data_rebuild_object (GTBipedRiggerRebuildData): data object used to store extracted data
    """
    # Find Available Controls
    logger.debug("*_*_* EXTRACTING CURRENT RIG:")
    logger.debug("searching for available controls...")
    found_controls = []
    for control in data_rebuild.controls:
        if cmds.objExists(control):
            found_controls.append(control)

    # Missing Main Ctrl - Exit
    if data_rebuild_object.main_ctrl not in found_controls:
        cmds.warning("Missing ")
        return False

    # -------- Base / Biped Proxy --------
    # Extract Base Proxy Data
    logger.debug("extracting base proxy transforms...")
    extracted_base_proxy_json = extract_proxy_metadata(data_biped)  # Re-build base proxy
    data_rebuild_object.extracted_base_proxy_json = extracted_base_proxy_json

    # Extract Base Rig Settings
    logger.debug("extracting settings (metadata)...")
    extracted_biped_metadata = get_metadata(data_rebuild_object.main_ctrl)  # Find previous settings
    data_rebuild_object.extracted_base_metadata = extracted_biped_metadata

    # -------- Facial Proxy --------
    facial_proxy_source = data_facial.proxy_storage_variables.get('source_object_name')
    facial_proxy_attr = data_facial.proxy_storage_variables.get('attr_name')
    if cmds.objExists(facial_proxy_source + '.' + facial_proxy_attr):
        logger.debug("extracting facial proxy transforms...")
        extracted_facial_proxy_json = extract_proxy_metadata(data_facial)  # Re-build base proxy
        data_rebuild_object.extracted_facial_proxy_json = extracted_facial_proxy_json

    # -------- Corrective Proxy --------
    corrective_proxy_source = data_corrective.proxy_storage_variables.get('source_object_name')
    corrective_proxy_attr = data_corrective.proxy_storage_variables.get('attr_name')
    if cmds.objExists(corrective_proxy_source + '.' + corrective_proxy_attr):
        logger.debug("extracting corrective proxy transforms...")
        extracted_corrective_proxy_json = extract_proxy_metadata(data_corrective)  # Re-build base proxy
        data_rebuild_object.extracted_corrective_proxy_json = extracted_corrective_proxy_json

    # Extract Shapes
    logger.debug("extracting control shapes...")
    data_rebuild_object.extracted_shape_data = extract_python_curve_shape_data(found_controls)

    # Extract Custom Attr
    logger.debug("extracting control shapes...")
    data_rebuild_object.extracted_custom_attr = extract_dict_attributes(found_controls)

    # Extract Default Channel Attributes
    transforms_to_store = []
    for obj in data_rebuild.transforms_to_store:
        if cmds.objExists(obj):
            transforms_to_store.append(obj)
    # if data_rebuild_object.settings.get("extract_pose"):
    #     transforms_to_store += found_controls
    data_rebuild_object.extracted_transform_data = extract_dict_attributes(transforms_to_store,
                                                                           default_channels=True,
                                                                           user_defined=False)
    # Extract Teardown/Setup Scripts TODO @@@
    data_rebuild_object.extracted_teardown_script = "print('test teardown script')"
    data_rebuild_object.extracted_setup_script = "print('test setup script')"


def rebuild_biped_rig(data_rebuild_object):
    """
    Deletes old rig and recreates it using the extracted data
    Args:
        data_rebuild_object (GTBipedRiggerRebuildData): extracted data stored in rebuild object
    """
    logger.debug("*_*_* REBUILDING RIG:")
    logger.debug("running teardown script...")
    if data_rebuild_object.extracted_teardown_script:
        error_message = "An error occurred while executing teardown script. "
        error_message += "(Open script editor for more information)"
        evaluate_python_string(data_rebuild_object.extracted_teardown_script,
                               custom_error_message=error_message)

    # Un-parent geometry
    geometry_objects = []
    if cmds.objExists("geometry_grp"):
        geometry_objects = cmds.listRelatives("geometry_grp", children=True)
    world_unparent(geometry_objects)

    # Delete current
    logger.debug("deleting current rig...")
    rig_root = ''
    if cmds.objExists(data_rebuild_object.rig_root):
        rig_root = data_rebuild_object.rig_root
    else:  # In case default rig root doesn't exist, try to find using skeleton_grp
        if cmds.objExists(data_rebuild_object.skeleton_grp):
            skeleton_grp_parent = cmds.listRelatives(data_rebuild_object.skeleton_grp, allParents=True) or []
            if skeleton_grp_parent:
                rig_root = skeleton_grp_parent[0]

    # Couldn't delete the rig, cancel operation
    if not rig_root:
        return False
    else:
        cmds.delete(rig_root)

    # -------- Rebuild Base / Biped --------
    logger.debug("recreating/importing base proxy...")
    rigger_gui.create_biped_proxy(data_biped)
    rigger_gui.import_biped_proxy_pose(source_dict=data_rebuild_object.extracted_base_proxy_json)

    # Rebuild Base Rig
    logger.debug("recreating base rig...")
    rigger_gui.validate_biped_operation('create_biped_rig')

    # -------- Rebuild Facial --------
    if data_rebuild_object.extracted_facial_proxy_json:
        logger.debug("recreating/importing facial proxy...")
        create_facial_proxy(data_facial)
        rigger_gui.import_facial_proxy_pose(source_dict=data_rebuild_object.extracted_facial_proxy_json)

    # Rebuild Facial Rig
    logger.debug("recreating facial rig...")
    rigger_gui.validate_facial_operation('create_facial_rig')

    # -------- Rebuild Corrective --------
    if data_rebuild_object.extracted_corrective_proxy_json:
        logger.debug("recreating/importing corrective proxy...")
        create_corrective_proxy(data_corrective)
        rigger_gui.import_corrective_proxy_pose(source_dict=data_rebuild_object.extracted_corrective_proxy_json)

    # Rebuild Facial Rig
    logger.debug("recreating facial rig...")
    rigger_gui.validate_corrective_operation('create_corrective_rig')

    return True


def transfer_current_rig_data(data_rebuild_object):
    """
    Transfer data back to a rig after it's generated
    Args:
        data_rebuild_object (GTBipedRiggerRebuildData): extracted data stored in rebuild object
    """
    logger.debug("*_*_* TRANSFERRING DATA TO NEW RIG:")

    # Transfer Shape Data
    if data_rebuild_object.extracted_shape_data:
        logger.debug("transferring shape data...")
        apply_python_curve_shape_data(data_rebuild_object.extracted_shape_data)

    # Transfer User-defined Attributes
    set_dict_attributes(data_rebuild_object.extracted_custom_attr)
    # Transfer Stored Transforms
    set_dict_attributes(data_rebuild_object.extracted_transform_data)

    logger.debug("running setup script...")
    if data_rebuild_object.extracted_setup_script:
        error_message = "An error occurred while executing rig setup script. "
        error_message += "(Open script editor for more information)"
        evaluate_python_string(data_rebuild_object.extracted_setup_script,
                               custom_error_message=error_message)


def update_general_settings(data_rebuild_object):
    """
    Transfer previous settings to data object so new rig is generated with the same options
    Forces auto merge to be active
    Args:
        data_rebuild_object (GTBipedRiggerRebuildData): extracted data stored in rebuild object
    """
    logger.debug("*_*_* UPDATING GENERAL RIGGING SETTINGS:")

    # Transfer Base Settings
    if data_rebuild_object.extracted_base_proxy_json and data_rebuild_object.extracted_base_metadata:
        logger.debug("transferring previous settings (metadata)...")
        transfer_biped_base_settings(data_biped, data_rebuild_object.extracted_base_metadata)

    # Force Auto Merging
    data_biped.settings['auto_merge'] = True
    data_facial.settings['auto_merge'] = True
    data_corrective.settings['auto_merge'] = True


def validate_rebuild(character_template=''):
    """
    Validate operation and rebuild rig
    Args:
        character_template (string, optional): Path to a character template
    """
    # Using current loaded rig
    if not find_item(name=data_rebuild.main_ctrl, item_type='transform', log_fail=False) and not character_template:
        cmds.warning('"Load a template or a character file before rebuilding. ' +
                     '(Unable to find "' + data_rebuild.main_ctrl + '")')
        return
    # Using saved template
    if character_template:
        if os.path.exists(character_template):
            pass  # Add logic for loading template here

    # Extract Data to Rebuild Object
    extract_current_rig_data(data_rebuild)

    # Transferring Settings
    update_general_settings(data_rebuild)

    # Rebuild Rig if data is available
    rebuild_biped_rig(data_rebuild)

    # Transfer Data to Rebuilt Rig
    transfer_current_rig_data(data_rebuild)


def world_unparent(obj_list):
    """
    Tries to parent list of objects to the world removing them from whatever hierarchy they might be in

    Args:
        obj_list (list): A list of strings with the name of the objects to un-parent.
    """
    for obj in obj_list:
        try:
            cmds.parent(obj, world=True)
        except Exception as e:
            logger.deubg(str(e))


def validate_extract_gui():
    """
    Validate operation and rebuild rig
    """
    # Using current loaded rig
    if not find_item(name=data_rebuild.main_ctrl, item_type='transform', log_fail=False):
        cmds.warning('"Load a template or a character file before rebuilding. ' +
                     '(Unable to find "' + data_rebuild.main_ctrl + '")')
        return

    # Extract Data to Rebuild Object
    extract_current_rig_data(data_rebuild)

    # Transferring Settings
    update_general_settings(data_rebuild)

    print(data_rebuild)

    # # Rebuild Rig if data is available
    # rebuild_biped_rig(data_rebuild)
    #
    # # Transfer Data to Rebuilt Rig
    # transfer_current_rig_data(data_rebuild)


# Run
if __name__ == '__main__':
    # data_biped = GTBipedRiggerData()
    # data_facial = GTBipedRiggerFacialData()
    # data_corrective = GTBipedRiggerCorrectiveData()

    logger.setLevel(logging.DEBUG)

    validate_rebuild()
    # validate_extract_gui()
    # evaluate_python_string("cmds.sphere()")
    # print(data_rebuild.extracted_corrective_proxy_json)
    # extract_current_rig_data(data_rebuild)
    # print(data_rebuild.extracted_corrective_proxy_json)

    # found_controls = []
    # for control in data_rebuild.controls:
    #     if cmds.objExists(control):
    #         found_controls.append(control)
    # out = extract_dict_attributes(found_controls)
    # import pprint
    # pprint.pprint(out)
