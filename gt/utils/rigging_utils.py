"""
Rigging Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.transform_utils import get_component_positions_as_dict, set_component_positions_from_dict
from gt.tools.auto_rigger.rig_constants import RiggerConstants
from gt.utils.hierarchy_utils import duplicate_as_node
from gt.utils.attr_utils import connect_attr, get_attr
from gt.utils.naming_utils import NamingConstants
from gt.utils import hierarchy_utils
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def duplicate_joint_for_automation(joint, suffix=NamingConstants.Suffix.DRIVEN, parent=None, connect_rot_order=True):
    """
    Preset version of the "duplicate_as_node" function used to duplicate joints for automation.
    Args:
        joint (str, Node): The joint to be duplicated
        suffix (str, optional): The suffix to be added at the end of the duplicated joint.
        parent (str, optional): If provided, and it exists, the duplicated object will be parented to this object.
        connect_rot_order (bool, optional): If True, it will create a connection between the original joint rotate
                                            order and the duplicate joint rotate order.
                                            (duplicate receives from original)
    Returns:
        str, None: A node (that has a str base) of the duplicated object, or None if it failed.
    """
    if not joint or not cmds.objExists(str(joint)):
        return
    jnt_as_node = duplicate_as_node(to_duplicate=str(joint), name=f'{joint.get_short_name()}_{suffix}',
                                    parent_only=True, delete_attrs=True, input_connections=False)
    if connect_rot_order:
        connect_attr(source_attr=f'{str(joint)}.rotateOrder', target_attr_list=f'{jnt_as_node}.rotateOrder')
    if parent:
        hierarchy_utils.parent(source_objects=jnt_as_node, target_parent=parent)
    return jnt_as_node


def rescale_joint_radius(joint_list, multiplier, initial_value=None):
    """
    Re-scales the joint radius attribute of the provided joints.
    It gets the original value and multiply it by the provided "multiplier" argument.
    Args:
        joint_list (list, str): Path to the target joints.
        multiplier (int, float): Value to multiply the radius by. For example "0.5" means 50% of the original value.
        initial_value (int, float, optional): If provided, this value is used instead of getting the joint radius.
                        Useful for when the radius could be zero (0) causing the multiplication to always be zero (0).
    """
    if joint_list and isinstance(joint_list, str):
        joint_list = [joint_list]
    for jnt in joint_list:
        if not cmds.objExists(f'{jnt}.radius'):
            continue
        scaled_radius = get_attr(f'{jnt}.radius') * multiplier
        if isinstance(initial_value, (int, float)):
            scaled_radius = initial_value * multiplier
        cmds.setAttr(f'{jnt}.radius', scaled_radius)


def expose_rotation_order(target, attr_enum='xyz:yzx:zxy:xzy:yxz:zyx'):
    """
    Creates an attribute to control the rotation order of the target object and connects the attribute
    to the hidden "rotationOrder" attribute.
    Args:
        target (str): Path to the target object (usually a control)
        attr_enum (str, optional): The ENUM used to create the custom rotation order enum.
                                   Default is "xyz", "yzx", "zxy", "xzy", "yxz", "zyx"  (Separated using ":")
    """
    cmds.addAttr(target, longName='rotationOrder', attributeType='enum', keyable=True,
                 en=attr_enum, niceName='Rotate Order')
    cmds.connectAttr(f'{target}.rotationOrder', f'{target}.rotateOrder', f=True)


def offset_control_orientation(ctrl, offset_transform, orient_tuple):
    """
    Offsets orientation of the control offset transform, while maintaining the original curve shape point position.
    Args:
        ctrl (str, Node): Path to the control transform (with curve shapes)
        offset_transform (str, Node): Path to the control offset transform.
        orient_tuple (tuple): A tuple with X, Y and Z values used as offset.
                              e.g. (90, 0, 0)  # offsets orientation 90 in X
    """
    for obj in [ctrl, offset_transform]:
        if not obj or not cmds.objExists(obj):
            logger.debug(f'Unable to offset control orientation, not all objects were found in the scene. '
                         f'Missing: {str(obj)}')
            return
    cv_pos_dict = get_component_positions_as_dict(obj_transform=ctrl, full_path=True, world_space=True)
    cmds.rotate(*orient_tuple, offset_transform, relative=True, objectSpace=True)
    set_component_positions_from_dict(component_pos_dict=cv_pos_dict)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # cmds.file(new=True, force=True)
    # cmds.viewFit(all=True)
