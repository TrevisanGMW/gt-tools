"""
GT Rigger - Biped Rigger Re-build Script (Rebuilder)
github.com/TrevisanGMW/gt-tools - 2022-09-28

0.0.1 - 2022-09-28
Created initial setup

0.0.2 - 2022-09-29
Added control shape extraction

TODO
    Add bound joint extraction
    Add skin weights extraction
    Add control custom attributes extraction

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


def extract_python_curve_shape(curve_transforms, printing=False):
    """
    Extracts the Python code necessary to reshape
    Args:
        curve_transforms (list of strings): Transforms carrying curve shapes inside them (nurbs or bezier)
        printing: Whether to print the extracted python code. If False it will only return the code.

    Returns:
        python_string (string): Python code with the current state of the selected curves (their shape)

    Copied from "gt_shape_extract_shape"
    """
    result = ''
    if printing:
        result += ('#' * 80)
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
        # print(accepted_shapes)
        for shape in accepted_shapes:
            curve_data = zip(cmds.ls('%s.cv[*]' % shape, flatten=True), cmds.getAttr(shape + '.cv[*]'))
            curve_data_list = list(curve_data)
            # Assemble command:
            if curve_data_list:
                result += '# Curve data for "' + str(shape).split('|')[-1] + '":\n'
                result += 'for cv in ' + str(curve_data_list) + ':\n'
                result += '    cmds.xform(cv[0], os=True, t=cv[1])\n\n'

    if result.endswith('\n\n\n'):  # Removes unnecessary spaces at the end
        result = result[:-2]

    # Return / Print
    if printing:
        result += ('#' * 80)
        if result.replace('#', ''):
            print(result)
            return result
        else:
            print('No data found. Make sure your selection contains nurbs or bezier curves.')
            return None
    else:
        return result


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

    proxy_elements = data_biped.elements_default # Doesn't work, create ctrl list
    found_controls = []
    for proxy in proxy_elements:
        potential_ctrl = proxy.replace('_proxy_crv', '_ctrl')
        if cmds.objExists(potential_ctrl):
            found_controls.append(potential_ctrl)

    curve_commands = extract_python_curve_shape(found_controls)

