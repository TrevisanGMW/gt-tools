"""
Rigging Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.transform_utils import get_component_positions_as_dict, set_component_positions_from_dict, match_translate
from gt.utils.attr_utils import connect_attr, get_attr, add_attr, delete_user_defined_attrs, set_attr_state, set_attr
from gt.utils.attr_utils import DEFAULT_ATTRS
from gt.utils.constraint_utils import ConstraintTypes, constraint_targets
from gt.utils.naming_utils import NamingConstants, get_short_name
from gt.utils.iterable_utils import sanitize_maya_list
from gt.utils.color_utils import set_color_outliner
from gt.utils.node_utils import Node, create_node
from gt.utils.math_utils import dist_xyz_to_xyz
from gt.utils.string_utils import get_int_as_en
from gt.utils.hierarchy_utils import duplicate_object
from gt.utils import hierarchy_utils
import maya.cmds as cmds
import logging
import random


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RiggingConstants:
    def __init__(self):
        """
        Constant values used by rigging systems.
        e.g. Attribute names, dictionary keys or initial values.
        """
    # Common Attributes
    ATTR_SHOW_OFFSET = 'showOffsetCtrl'
    ATTR_INFLUENCE_SWITCH = 'influenceSwitch'
    # Separator Attributes
    SEPARATOR_OPTIONS = "options"
    SEPARATOR_CONTROL = "controlOptions"


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
        str, Node, None: A node (that has a str as base) of the duplicated object, or None if it failed.
    """
    if not joint or not cmds.objExists(str(joint)):
        return
    jnt_as_node = duplicate_object(obj=joint, name=f'{get_short_name(joint)}_{suffix}',
                                   parent_only=True, reset_attributes=True, input_connections=False)
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


def create_stretchy_ik_setup(ik_handle, attribute_holder=None, prefix=None):
    """
    Creates measure nodes and use them to determine when the joints should be scaled up causing a stretchy effect.

    Args:
        ik_handle (str, Node) : Name of the IK Handle (joints will be extracted from it)
        attribute_holder (str, Node): The name of an object. If it exists, custom attributes will be added to it.
                    These attributes allow the user to control whether the system is active,as well as its operation.
                    Needed for complete stretchy system, otherwise volume preservation is skipped.
        prefix (str, optional): Prefix name to be used when creating the system.

    Returns:
        str, Node: Setup group containing the system elements. e.g. "stretchy_grp".
                   To find other related items, see destination connections from "message".
                   e.g. "stretchy_grp.message" is connected to "stretchyTerm_end.termEnd" describing the relationship.
    """
    # Get elements
    ik_joints = cmds.ikHandle(ik_handle, query=True, jointList=True)
    children_last_jnt = cmds.listRelatives(ik_joints[-1], children=True, type='joint') or []

    # Prefix
    _prefix = ''
    if prefix and isinstance(prefix, str):
        _prefix = f'{prefix}_'

    # Find end joint
    end_ik_jnt = ''
    if len(children_last_jnt) == 1:
        end_ik_jnt = children_last_jnt[0]
    elif len(children_last_jnt) > 1:  # Find Joint Closest to ikHandle (when multiple joints are found)
        jnt_magnitude_pairs = []
        for jnt in children_last_jnt:
            ik_handle_ws_pos = cmds.xform(ik_handle, query=True, translation=True, worldSpace=True)
            jnt_ws_pos = cmds.xform(jnt, query=True, translation=True, worldSpace=True)
            mag = dist_xyz_to_xyz(ik_handle_ws_pos[0], ik_handle_ws_pos[1], ik_handle_ws_pos[2],
                                  jnt_ws_pos[0], jnt_ws_pos[1], jnt_ws_pos[2])
            jnt_magnitude_pairs.append([jnt, mag])
        # Find The Lowest Distance
        current_jnt = jnt_magnitude_pairs[1:][0]
        current_closest = jnt_magnitude_pairs[1:][1]
        for pair in jnt_magnitude_pairs:
            if pair[1] < current_closest:
                current_closest = pair[1]
                current_jnt = pair[0]
        end_ik_jnt = current_jnt

    dist_one = cmds.distanceDimension(startPoint=(1, random.random() * 10, 1),
                                      endPoint=(2, random.random() * 10, 2))
    dist_one_transform = cmds.listRelatives(dist_one, parent=True, fullPath=True)[0]
    dist_one_transform = Node(dist_one_transform)
    start_loc_one, end_loc_one = cmds.listConnections(dist_one)
    start_loc_one = Node(start_loc_one)
    end_loc_one = Node(end_loc_one)

    match_translate(source=ik_joints[0], target_list=start_loc_one)
    match_translate(source=ik_handle, target_list=end_loc_one)

    # Rename Distance One Nodes
    dist_one_transform.rename(f"{_prefix}stretchyTerm_stretchyDistance")
    start_loc_one.rename(f"{_prefix}stretchyTerm_start")
    end_loc_one.rename(f"{_prefix}stretchyTerm_end")

    dist_nodes = {}  # [distance_node_transform, start_loc, end_loc, ik_handle_joint]
    for index in range(len(ik_joints)):
        dist_mid = cmds.distanceDimension(startPoint=(1, random.random() * 10, 1),
                                           endPoint=(2, random.random() * 10, 2))
        dist_mid_transform = cmds.listRelatives(dist_mid, parent=True, fullPath=True)[0]
        start_loc, end_loc = cmds.listConnections(dist_mid)
        # Convert To Nodes
        dist_mid = Node(dist_mid)
        dist_mid_transform = Node(dist_mid_transform)
        start_loc = Node(start_loc)
        end_loc = Node(end_loc)
        # Rename Nodes
        dist_mid.rename(f"{_prefix}defaultTerm{get_int_as_en(index + 1).capitalize()}_stretchyDistanceShape")
        dist_mid_transform.rename(f"{_prefix}defaultTerm{get_int_as_en(index + 1).capitalize()}_stretchyDistance")
        start_loc.rename(f"{_prefix}defaultTerm{get_int_as_en(index + 1).capitalize()}_start")
        end_loc.rename(f"{_prefix}defaultTerm{get_int_as_en(index + 1).capitalize()}_end")

        match_translate(source=ik_joints[index], target_list=start_loc)
        if index < (len(ik_joints) - 1):
            match_translate(source=ik_joints[index + 1], target_list=end_loc)
        else:
            match_translate(source=end_ik_jnt, target_list=end_loc)
        dist_nodes[dist_mid] = [dist_mid_transform, start_loc, end_loc, ik_joints[index]]
        index += 1

    # Organize Basic Hierarchy
    stretchy_grp = cmds.group(name=f"{_prefix}stretchy_grp", empty=True, world=True)
    stretchy_grp = Node(stretchy_grp)
    hierarchy_utils.parent(source_objects=[dist_one_transform, start_loc_one, end_loc_one], target_parent=stretchy_grp)

    # Connect, Colorize and Organize Hierarchy
    default_dist_sum_node = create_node(node_type='plusMinusAverage', name=f"{_prefix}defaultTermSum_plus")
    index = 0
    for node in dist_nodes:
        cmds.connectAttr(f"{node}.distance", f"{default_dist_sum_node}.input1D[{index}]")
        for obj in dist_nodes.get(node):
            if cmds.objectType(obj) != 'joint':
                set_color_outliner(obj_list=obj, rgb_color=(1, .5, .5))
                cmds.parent(obj, stretchy_grp)
        index += 1

    # Outliner Color
    set_color_outliner(obj_list=[dist_one_transform, start_loc_one, end_loc_one], rgb_color=(.5, 1, .2))

    # Connect Nodes
    nonzero_stretch_condition_node = create_node(node_type='condition', name=f"{_prefix}stretchyNonZero_condition")
    nonzero_multiply_node = create_node(node_type='multiplyDivide', name=f"{_prefix}onePctDistCondition_multiply")
    cmds.connectAttr(f"{default_dist_sum_node}.output1D", f"{nonzero_multiply_node}.input1X")
    cmds.setAttr(f"{nonzero_multiply_node}.input2X", 0.01)
    cmds.connectAttr(f"{nonzero_multiply_node}.outputX", f"{nonzero_stretch_condition_node}.colorIfTrueR")
    cmds.connectAttr(f"{nonzero_multiply_node}.outputX", f"{nonzero_stretch_condition_node}.secondTerm")
    cmds.setAttr(f"{nonzero_stretch_condition_node}.operation", 5)

    stretch_normalization_node = create_node(node_type='multiplyDivide', name=f"{_prefix}distNormalization_divide")
    cmds.connectAttr(f"{dist_one_transform}.distance", f"{nonzero_stretch_condition_node}.firstTerm")
    cmds.connectAttr(f"{dist_one_transform}.distance", f"{nonzero_stretch_condition_node}.colorIfFalseR")
    cmds.connectAttr(f"{nonzero_stretch_condition_node}.outColorR", f"{stretch_normalization_node}.input1X")

    cmds.connectAttr(f"{default_dist_sum_node}.output1D", f"{stretch_normalization_node}.input2X")

    cmds.setAttr(f"{stretch_normalization_node}.operation", 2)

    stretch_condition_node = create_node(node_type='condition', name=f"{_prefix}stretchyAutomation_condition")
    cmds.setAttr(f"{stretch_condition_node}.operation", 3)
    cmds.connectAttr(f"{nonzero_stretch_condition_node}.outColorR", f"{stretch_condition_node}.firstTerm")
    cmds.connectAttr(f"{default_dist_sum_node}.output1D", f"{stretch_condition_node}.secondTerm")
    cmds.connectAttr(f"{stretch_normalization_node}.outputX", f"{stretch_condition_node}.colorIfTrueR")

    # Constraints
    cmds.pointConstraint(ik_joints[0], start_loc_one)
    start_loc_condition = ''
    for node in dist_nodes:
        if dist_nodes.get(node)[3] == ik_joints[0:][0]:
            start_loc_condition = cmds.pointConstraint(ik_joints[0], dist_nodes.get(node)[1])

    # Attribute Holder Setup
    if attribute_holder:
        if cmds.objExists(attribute_holder):
            cmds.pointConstraint(attribute_holder, end_loc_one)
            cmds.addAttr(attribute_holder, ln='stretch', at='double', k=True, minValue=0, maxValue=1)
            cmds.setAttr(f"{attribute_holder}.stretch", 1)
            cmds.addAttr(attribute_holder, ln='squash', at='double', k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder, ln='stretchFromSource', at='bool', k=True)
            cmds.addAttr(attribute_holder, ln='saveVolume', at='double', k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder, ln='baseVolumeMultiplier', at='double', k=True, minValue=0, maxValue=1)
            cmds.setAttr(f"{attribute_holder}.baseVolumeMultiplier", .5)
            cmds.addAttr(attribute_holder, ln='minimumVolume', at='double', k=True, minValue=0.01, maxValue=1)
            cmds.addAttr(attribute_holder, ln='maximumVolume', at='double', k=True, minValue=0)
            cmds.setAttr(f"{attribute_holder}.minimumVolume", .4)
            cmds.setAttr(f"{attribute_holder}.maximumVolume", 2)
            cmds.setAttr(f"{attribute_holder}.stretchFromSource", 1)

            # Stretch From Body
            from_body_reverse_node = create_node(node_type='reverse', name=f"{_prefix}stretchFromSource_reverse")
            cmds.connectAttr(f"{attribute_holder}.stretchFromSource", f"{from_body_reverse_node}.inputX")
            cmds.connectAttr(f"{from_body_reverse_node}.outputX", f"{start_loc_condition[0]}.w0")

            # Squash
            squash_condition_node = create_node(node_type='condition', name=f"{_prefix}squashAutomation_condition")
            cmds.setAttr(f"{squash_condition_node}.secondTerm", 1)
            cmds.setAttr(f"{squash_condition_node}.colorIfTrueR", 1)
            cmds.setAttr(f"{squash_condition_node}.colorIfFalseR", 3)
            cmds.connectAttr(f"{attribute_holder}.squash", f"{squash_condition_node}.firstTerm")
            cmds.connectAttr(f"{squash_condition_node}.outColorR", f"{stretch_condition_node}.operation")

            # Stretch
            activation_blend_node = create_node(node_type='blendTwoAttr', name=f"{_prefix}stretchyActivation_blend")
            cmds.setAttr(f"{activation_blend_node}.input[0]", 1)
            cmds.connectAttr(f"{stretch_condition_node}.outColorR", f"{activation_blend_node}.input[1]")
            cmds.connectAttr(f"{attribute_holder}.stretch", f"{activation_blend_node}.attributesBlender")

            for jnt in ik_joints:
                cmds.connectAttr(f"{activation_blend_node}.output", f"{jnt}.scaleX")

            # Save Volume
            save_volume_condition_node = create_node(node_type='condition', name=f"{_prefix}saveVolume_condition")
            volume_normalization_divide_node = create_node(node_type='multiplyDivide',
                                                           name=f"{_prefix}volumeNormalization_divide")
            volume_value_divide_node = create_node(node_type='multiplyDivide', name=f"{_prefix}volumeValue_divide")
            xy_divide_node = create_node(node_type='multiplyDivide', name=f"{_prefix}volumeXY_divide")
            volume_blend_node = create_node(node_type='blendTwoAttr', name=f"{_prefix}volumeActivation_blend")
            volume_clamp_node = create_node(node_type='clamp', name=f"{_prefix}volumeLimits_clamp")
            volume_base_blend_node = create_node(node_type='blendTwoAttr', name=f"{_prefix}volumeBase_blend")

            cmds.setAttr(f"{save_volume_condition_node}.secondTerm", 1)
            cmds.setAttr(f"{volume_normalization_divide_node}.operation", 2)  # Divide
            cmds.setAttr(f"{volume_value_divide_node}.operation", 2)  # Divide
            cmds.setAttr(f"{xy_divide_node}.operation", 2)  # Divide

            cmds.connectAttr(f"{nonzero_stretch_condition_node}.outColorR",
                             f"{volume_normalization_divide_node}.input1X")  # Distance One
            cmds.connectAttr(f"{default_dist_sum_node}.output1D",
                             f"{volume_normalization_divide_node}.input2X")

            cmds.connectAttr(f"{volume_normalization_divide_node}.outputX",
                             f"{volume_value_divide_node}.input1X")
            cmds.connectAttr(f"{stretch_normalization_node}.outputX",
                             f"{volume_value_divide_node}.input2X")

            cmds.connectAttr(f"{volume_value_divide_node}.outputX", f"{xy_divide_node}.input1X")
            cmds.connectAttr(f"{stretch_normalization_node}.outputX", f"{xy_divide_node}.input2X")

            cmds.setAttr(f"{volume_blend_node}.input[0]", 1)
            cmds.connectAttr(f"{xy_divide_node}.outputX", f"{volume_blend_node}.input[1]")

            cmds.connectAttr(f"{attribute_holder}.saveVolume", f"{volume_blend_node}.attributesBlender")

            cmds.connectAttr(f"{volume_blend_node}.output", f"{save_volume_condition_node}.colorIfTrueR")

            cmds.connectAttr(f"{attribute_holder}.stretch", f"{save_volume_condition_node}.firstTerm")
            cmds.connectAttr(f"{attribute_holder}.minimumVolume", f"{volume_clamp_node}.minR")
            cmds.connectAttr(f"{attribute_holder}.maximumVolume", f"{volume_clamp_node}.maxR")

            # Base Multiplier
            cmds.setAttr(f"{volume_base_blend_node}.input[0]", 1)
            cmds.connectAttr(f"{save_volume_condition_node}.outColorR",
                             f"{volume_base_blend_node}.input[1]")
            cmds.connectAttr(f"{attribute_holder}.baseVolumeMultiplier",
                             f"{volume_base_blend_node}.attributesBlender")

            # Connect to Joints
            cmds.connectAttr(f"{volume_base_blend_node}.output", f"{ik_joints[0]}.scaleY")
            cmds.connectAttr(f"{volume_base_blend_node}.output", f"{ik_joints[0]}.scaleZ")

            for jnt in ik_joints[1:]:
                cmds.connectAttr(f"{save_volume_condition_node}.outColorR", f"{jnt}.scaleY")
                cmds.connectAttr(f"{save_volume_condition_node}.outColorR", f"{jnt}.scaleZ")

        else:
            for jnt in ik_joints:
                cmds.connectAttr(f"{stretch_condition_node}.outColorR", f"{jnt}.scaleX")
    else:
        for jnt in ik_joints:
            cmds.connectAttr(f"{stretch_condition_node}.outColorR", f"{jnt}.scaleX")

    # Add relationship connections
    add_attr(obj_list=start_loc_one, attr_type="string", attributes=['termStart'])
    add_attr(obj_list=end_loc_one, attr_type="string", attributes=['termEnd'])
    connect_attr(source_attr=f'{stretchy_grp}.message', target_attr_list=f'{start_loc_one}.termStart')
    connect_attr(source_attr=f'{stretchy_grp}.message', target_attr_list=f'{end_loc_one}.termEnd')

    return stretchy_grp

def create_switch_setup(source_a, source_b, target_base, attr_holder, visibility_a=None, visibility_b=None,
                        shape_visibility=True, attr_influence=RiggingConstants.ATTR_INFLUENCE_SWITCH,
                        constraint_type=ConstraintTypes.PARENT, maintain_offset=False, prefix=None):
    """
    Creates a switch setup to control the influence between two systems.
    Creates a constraint
    Switch Range: 0.0 to 1.0
    System A Range: 0.0 to 0.5
    System B Range: 0.5 to 1.0

    Args:
        source_a (list, tuple, str): The objects or attributes representing the first system.
        source_b (list, tuple, str): The objects or attributes representing the second system.
        target_base (list, tuple, str): The target objects affected by the switch setup. (usually a base skeleton)
        attr_holder (str): The attribute holder object name/path.
                           This is the switch control, the influence attribute is found under this object.
                           Output attributes are also found under this object, but are hidden.
                           These are the source attributes that are plugged on the system objects.
                           'influenceA', 'influenceB': 0.0 to 1.0 value of the influence. (B is A inverted)
                           'visibilityA', 'visibilityB': On or Off visibility values according to range.
        visibility_a (list, optional): The objects affected by the visibility of the first system.
        visibility_b (list, optional): The objects affected by the visibility of the second system.
        shape_visibility (bool, optional): Whether to affect the visibility of shapes or the main objects.
        attr_influence (str, optional): The name of the attribute controlling the influence.
                                    Default is "RiggingConstants.ATTR_INFLUENCE_SWITCH".
                                    If attribute already exists, it's used as is.
        constraint_type (str, optional): The type of constraint to create. Default is parent.
        maintain_offset (bool, optional): Whether to maintain offset in constraints. Default is Off.
        prefix (str, optional): Prefix for naming created nodes.

    Returns:
        tuple: A tuple with the switch output attributes. ()
    """
    # Check attr holder and convert it to Node
    if not attr_holder or not cmds.objExists(attr_holder):
        logger.warning(f'Missing attribute holder. Switch setup was skipped.')
        return
    attr_holder = Node(attr_holder)
    # Strings to List
    if isinstance(source_a, str):
        source_a = [source_a]
    if isinstance(source_b, str):
        source_b = [source_b]
    if isinstance(target_base, str):
        target_base = [target_base]

    # Tuple to List
    if isinstance(source_a, tuple):
        source_a = list(source_a)
    if isinstance(source_b, tuple):
        source_b = list(source_b)
    if isinstance(target_base, tuple):
        target_base = list(target_base)

    # Length Check
    list_len = {len(source_a), len(source_b), len(target_base)}
    if len(list_len) != 1:
        logger.warning(f'Unable to create switch setup. All input lists must be of the same length.')
        return

    # Prefix
    _prefix = ''
    if prefix:
        _prefix = f'{prefix}_'

    # Switch Setup
    attr_influence_a = f'influenceA'
    attr_influence_b = f'influenceB'
    attr_vis_a = f'visibilityA'
    attr_vis_b = f'visibilityB'
    add_attr(obj_list=attr_holder, attributes=attr_influence, attr_type='double', is_keyable=True, maximum=1, minimum=0)
    add_attr(obj_list=attr_holder, attributes=attr_influence_a, attr_type='double', is_keyable=False)
    add_attr(obj_list=attr_holder, attributes=attr_influence_b, attr_type='double', is_keyable=False)
    add_attr(obj_list=attr_holder, attributes=attr_vis_a, attr_type='bool', is_keyable=False)
    add_attr(obj_list=attr_holder, attributes=attr_vis_b, attr_type='bool', is_keyable=False)
    # Setup Visibility Condition
    cmds.setAttr(f'{attr_holder}.{attr_influence}', 1)
    condition = create_node(node_type='condition', name=f'{_prefix}switchVisibility_condition')
    cmds.connectAttr(f'{attr_holder}.{attr_influence}', f'{condition}.firstTerm')
    set_attr(attribute_path=f'{condition}.operation', value=4)  # Operation = Less Than (4)
    set_attr(attribute_path=f'{condition}.secondTerm', value=0.5)  # Range A:0->0.5  B: 0.5->1
    set_attr(obj_list=condition, attr_list=["colorIfTrueR", "colorIfTrueG", "colorIfTrueB"], value=1)
    set_attr(obj_list=condition, attr_list=["colorIfFalseR", "colorIfFalseG", "colorIfFalseB"], value=0)
    reverse_visibility = create_node(node_type='reverse', name=f'{_prefix}switchVisibility_reverse')
    cmds.connectAttr(f'{condition}.outColorR', f'{reverse_visibility}.inputX', f=True)
    # Setup Influence Reversal
    reverse_influence = create_node(node_type='reverse', name=f'{_prefix}switchInfluence_reverse')
    cmds.connectAttr(f'{attr_holder}.{attr_influence}', f'{reverse_influence}.inputX', f=True)

    # Send Data back to Attr Holder
    cmds.connectAttr(f'{attr_holder}.{attr_influence}', f'{attr_holder}.{attr_influence_a}', f=True)
    cmds.connectAttr(f'{reverse_influence}.outputX', f'{attr_holder}.{attr_influence_b}', f=True)
    cmds.connectAttr(f'{reverse_visibility}.outputX', f'{attr_holder}.{attr_vis_a}', f=True)
    cmds.connectAttr(f'{condition}.outColorR', f'{attr_holder}.{attr_vis_b}', f=True)

    # Constraints
    constraints = []
    for source_a, source_b, target in zip(source_a, source_b, target_base):
        _constraints = constraint_targets(source_driver=[source_a, source_b], target_driven=target,
                                          constraint_type=constraint_type, maintain_offset=maintain_offset)
        if _constraints:
            constraints.extend(_constraints)
    for constraint in constraints:
        cmds.connectAttr(f'{attr_holder}.{attr_influence_a}', f'{constraint}.w0', force=True)
        cmds.connectAttr(f'{attr_holder}.{attr_influence_b}', f'{constraint}.w1', force=True)

    # Visibility Setup
    if isinstance(visibility_a, str):
        visibility_a = [visibility_a]
    if not visibility_a:
        visibility_a = []
    else:
        visibility_a = sanitize_maya_list(input_list=visibility_a)
    if isinstance(visibility_b, str):
        visibility_b = [visibility_b]
    if not visibility_b:
        visibility_b = []
    else:
        visibility_b = sanitize_maya_list(input_list=visibility_b)
    for obj_a in visibility_a:
        if shape_visibility:
            for shape in cmds.listRelatives(obj_a, shapes=True, fullPath=True) or []:
                cmds.connectAttr(f'{attr_holder}.{attr_vis_a}', f'{shape}.v', f=True)
        else:
            cmds.connectAttr(f'{attr_holder}.{attr_vis_a}', f'{obj_a}.v', f=True)
    for obj_b in visibility_b:
        if shape_visibility:
            for shape in cmds.listRelatives(obj_b, shapes=True, fullPath=True) or []:
                cmds.connectAttr(f'{attr_holder}.{attr_vis_b}', f'{shape}.v', f=True)
        else:
            cmds.connectAttr(f'{attr_holder}.{attr_vis_b}', f'{obj_b}.v', f=True)
    # Return Data
    return (f'{attr_holder}.{attr_influence_a}', f'{attr_holder}.{attr_influence_b}',
            f'{attr_holder}.{attr_vis_a}', f'{attr_holder}.{attr_vis_b}')


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.viewFit(all=True)
