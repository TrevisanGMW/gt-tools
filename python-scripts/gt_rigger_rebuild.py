"""
GT Rigger - Biped Rigger Re-build Script (Rebuilder)
github.com/TrevisanGMW/gt-tools - 2022-09-28

0.0.1 - 2022-09-28
Created initial setup

0.0.2 to 0.0.3 - 2022-09-30
Added initial control shape extraction
Added data object (control list)

TODO
    Add bound joint extraction
    Add skin weights extraction
    Add control custom attributes extraction
    Add corrective and facial reference position
    Add side GUI, fingers and feet positioning
"""
from gt_rigger_game_exporter import find_main_ctrl
from gt_rigger_biped_gui import *
from gt_rigger_utilities import *
from gt_rigger_data import *
import maya.cmds as cmds
import logging
import random
import json
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_rigger_rebuild")
logger.setLevel(logging.INFO)

# Data Object
data_rebuild = GTBipedRiggerRebuildData()


def extract_metadata(data_object):
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
    to_transfer = ['using_no_ssc_skeleton', 'uniform_ctrl_orient', 'worldspace_ik_orient', 'simplify_spine']
    for option in to_transfer:
        if metadata.get(option) is not None:
            logger.debug(str(option) + ': ' + str(metadata.get(option)))
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


def apply_python_curve_shape_data(extracted_curves):
    """
    Applies JSON data extracted from curves using  extract_python_curve_shape_data
    Args:
        extracted_curves (json, dict): JSON data extracted using "extract_python_curve_shape_data"
    """
    errors = ''
    for key in extracted_curves:
        curve_data = extracted_curves.get(key)
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
    # logger.debug(str(e))


# Run
if __name__ == '__main__':
    # data_biped = GTBipedRiggerData()
    # data_facial = GTBipedRiggerFacialData()
    # data_corrective = GTBipedRiggerCorrectiveData()

    logger.setLevel(logging.DEBUG)
    #
    # extracted_json = extract_metadata(data_biped)
    # biped_metadata = get_metadata(find_main_ctrl())
    #
    # transfer_biped_base_settings(data_biped, biped_metadata)

    found_controls = []
    for control in data_rebuild.controls:
        if cmds.objExists(control):
            found_controls.append(control)

    # extracted_curves = extract_python_curve_shape_data(found_controls)

    apply_python_curve_shape_data(extracted_curves)


