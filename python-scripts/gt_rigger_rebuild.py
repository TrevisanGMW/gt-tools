"""
GT Rigger - Biped Rigger Re-build Script (Rebuilder)
github.com/TrevisanGMW/gt-tools - 2022-09-28

v0.0.1 - 2022-09-28
Created initial setup

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


# Run
if __name__ == '__main__':
    # data_biped = GTBipedRiggerData()
    # data_facial = GTBipedRiggerFacialData()
    # data_corrective = GTBipedRiggerCorrectiveData()

    logger.setLevel(logging.DEBUG)
    extracted_json = extract_metadata(data_biped)
    biped_metadata = get_metadata(find_main_ctrl())

    transfer_biped_base_settings(data_biped, biped_metadata)
