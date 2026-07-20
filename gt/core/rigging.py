"""
Rigging Utilities

Import Line:
    import gt.core.rigging as core_rigging
"""

import gt.core.constraint as core_cnstr
import gt.core.transform as core_trans
import gt.core.hierarchy as core_hrchy
import gt.core.feedback as core_fback
import gt.core.naming as core_naming
import gt.core.iterable as core_iter
import gt.core.color as core_color
import gt.core.attr as core_attr
import gt.core.node as core_node
import gt.core.math as core_math
import gt.core.undo as core_undo
import gt.core.str as core_str
import maya.cmds as cmds
import functools
import logging
import random
import math
import uuid
import os

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
    ATTR_SHOW_OFFSET = "showOffsetCtrl"
    ATTR_SHOW_PIVOT = "showPivotCtrl"
    ATTR_INFLUENCE_SWITCH = "influenceSwitch"
    ATTR_IMPORT_OFFSET_REF = "isImportOffsetGrp"
    ATTR_TWIST_SETUP = "twistSetup"
    # Separator Attributes
    SEPARATOR_OPTIONS = "options"
    SEPARATOR_CONTROL = "controlOptions"
    SEPARATOR_SWITCH = "switchOptions"
    SEPARATOR_SPACE = "spaceOptions"
    SEPARATOR_INFLUENCE = "influenceOptions"
    # Default control parent groups base names
    OFFSET_PARENT_GROUP = "offset"


def get_twist_setup_from_target(target):
    """Gets the native twist setup connected to a target transform.

    Args:
        target (str, Node): Transform or joint driven by a twist setup.

    Returns:
        str or None: Connected twist setup node, if one exists.
    """
    target = str(target)
    if not target or not cmds.objExists(target):
        return None

    setup_attr = f"{target}.{RiggingConstants.ATTR_TWIST_SETUP}"
    if cmds.objExists(setup_attr):
        setup_nodes = cmds.listConnections(setup_attr, source=True, destination=False) or []
        for setup_node in setup_nodes:
            if cmds.objExists(f"{setup_node}.twist"):
                return setup_node
    return None


def create_twist_extraction_network(
    driver,
    driven,
    twist_weight=1.0,
    twist_axis=0,
    driver_rest_offset_matrix=None,
    target_rest_matrix=None,
    name=None,
):
    """Creates a Maya-native quaternion twist extraction network.

    The network uses Maya dependency nodes that do not require a plug-in. The
    driver's local quaternion is projected onto the requested axis, normalized
    by a ``composeMatrix`` node, and interpolated from identity by
    ``blendMatrix``.

    Args:
        driver (str, Node): Transform from which local twist is extracted.
        driven (str, Node): Transform whose offset parent matrix receives twist.
        twist_weight (float, optional): Twist multiplier from -1.0 to 1.0.
        twist_axis (int, str, optional): Twist axis as 0/1/2 or X/Y/Z.
        driver_rest_offset_matrix (tuple, list, optional): Matrix inserted
            between the driver world and parent inverse matrices.
        target_rest_matrix (tuple, list, optional): Matrix multiplied after the
            weighted twist rotation.
        name (str, optional): Name for the network node that stores settings.

    Returns:
        Node: Network node containing the twist and target rest attributes.

    Raises:
        ValueError: If an input is invalid or the driven transform is already
            connected to another offset parent matrix setup.
    """
    driver = str(driver)
    driven = str(driven)
    for label, obj in [("driver", driver), ("driven", driven)]:
        if not obj or not cmds.objExists(obj):
            raise ValueError(f'Unable to create twist extraction network. Invalid {label}: "{obj}".')

    axis_lookup = {0: "X", 1: "Y", 2: "Z", "X": "X", "Y": "Y", "Z": "Z"}
    axis_key = twist_axis.upper() if isinstance(twist_axis, str) else twist_axis
    axis = axis_lookup.get(axis_key)
    if not axis:
        raise ValueError(f'Invalid twist axis: "{twist_axis}". Use 0/1/2 or X/Y/Z.')
    if not isinstance(twist_weight, (int, float)) or not -1.0 <= twist_weight <= 1.0:
        raise ValueError("Twist weight must be a number between -1.0 and 1.0.")

    driver_rest_offset_values = None
    if driver_rest_offset_matrix is not None:
        driver_rest_offset_values = list(driver_rest_offset_matrix)
        if len(driver_rest_offset_values) != 16:
            raise ValueError("Driver rest offset matrix must contain 16 values.")

    target_rest_values = None
    if target_rest_matrix is not None:
        target_rest_values = list(target_rest_matrix)
        if len(target_rest_values) != 16:
            raise ValueError("Target rest matrix must contain 16 values.")

    offset_parent_attr = f"{driven}.offsetParentMatrix"
    if not cmds.objExists(offset_parent_attr):
        raise ValueError(f'The driven transform does not have an offset parent matrix: "{driven}".')
    existing_setup = get_twist_setup_from_target(driven)
    if existing_setup:
        raise ValueError(f'The driven transform already has a twist setup: "{existing_setup}".')
    existing_inputs = cmds.listConnections(offset_parent_attr, source=True, destination=False, plugs=True) or []
    if existing_inputs:
        raise ValueError(f'The driven offset parent matrix already has an input: "{existing_inputs[0]}".')

    driven_short_name = core_naming.get_short_name(driven)
    setup_name = name or f"{driven_short_name}_twistNode"
    setup_node = cmds.createNode("network", name=core_naming.get_short_name(setup_name))
    cmds.addAttr(
        setup_node,
        longName="twist",
        attributeType="double",
        defaultValue=twist_weight,
        minValue=-1.0,
        maxValue=1.0,
        keyable=True,
    )
    cmds.addAttr(setup_node, longName="targetRestMatrix", dataType="matrix")
    if target_rest_values:
        cmds.setAttr(f"{setup_node}.targetRestMatrix", target_rest_values, type="matrix")

    setup_message_attr = f"{driven}.{RiggingConstants.ATTR_TWIST_SETUP}"
    if not cmds.objExists(setup_message_attr):
        cmds.addAttr(driven, longName=RiggingConstants.ATTR_TWIST_SETUP, attributeType="message")
    cmds.connectAttr(f"{setup_node}.message", setup_message_attr)

    local_matrix = cmds.createNode("multMatrix", name=f"{driven_short_name}_twistLocal")
    decompose_matrix = cmds.createNode("decomposeMatrix", name=f"{driven_short_name}_twistDecompose")
    negate_values = cmds.createNode("multiplyDivide", name=f"{driven_short_name}_twistNegate")
    sign_condition = cmds.createNode("condition", name=f"{driven_short_name}_twistSign")
    compose_matrix = cmds.createNode("composeMatrix", name=f"{driven_short_name}_twistCompose")
    blend_matrix = cmds.createNode("blendMatrix", name=f"{driven_short_name}_twistBlend")
    output_matrix = cmds.createNode("multMatrix", name=f"{driven_short_name}_twistOutput")

    cmds.connectAttr(f"{driver}.worldMatrix[0]", f"{local_matrix}.matrixIn[0]")
    parent_inverse_index = 1
    if driver_rest_offset_values:
        cmds.setAttr(f"{local_matrix}.matrixIn[1]", driver_rest_offset_values, type="matrix")
        parent_inverse_index = 2
    cmds.connectAttr(
        f"{driver}.parentInverseMatrix[0]", f"{local_matrix}.matrixIn[{parent_inverse_index}]"
    )
    cmds.connectAttr(f"{local_matrix}.matrixSum", f"{decompose_matrix}.inputMatrix")

    quaternion_axis_attr = f"{decompose_matrix}.outputQuat{axis}"
    cmds.connectAttr(quaternion_axis_attr, f"{negate_values}.input1X")
    cmds.connectAttr(f"{setup_node}.twist", f"{negate_values}.input1Y")
    cmds.setAttr(f"{negate_values}.input2", -1, -1, 1, type="double3")

    cmds.setAttr(f"{sign_condition}.operation", 4)
    cmds.connectAttr(f"{setup_node}.twist", f"{sign_condition}.firstTerm")
    cmds.connectAttr(f"{negate_values}.outputX", f"{sign_condition}.colorIfTrueR")
    cmds.connectAttr(quaternion_axis_attr, f"{sign_condition}.colorIfFalseR")
    cmds.connectAttr(f"{negate_values}.outputY", f"{sign_condition}.colorIfTrueG")
    cmds.connectAttr(f"{setup_node}.twist", f"{sign_condition}.colorIfFalseG")

    cmds.setAttr(f"{compose_matrix}.useEulerRotation", False)
    cmds.connectAttr(f"{sign_condition}.outColorR", f"{compose_matrix}.inputQuat{axis}")
    cmds.connectAttr(f"{decompose_matrix}.outputQuatW", f"{compose_matrix}.inputQuatW")
    cmds.connectAttr(f"{compose_matrix}.outputMatrix", f"{blend_matrix}.target[0].targetMatrix")
    cmds.connectAttr(f"{sign_condition}.outColorG", f"{blend_matrix}.target[0].weight")
    cmds.setAttr(f"{blend_matrix}.target[0].translateWeight", 0)
    cmds.setAttr(f"{blend_matrix}.target[0].scaleWeight", 0)
    cmds.setAttr(f"{blend_matrix}.target[0].shearWeight", 0)

    cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{output_matrix}.matrixIn[0]")
    cmds.connectAttr(f"{setup_node}.targetRestMatrix", f"{output_matrix}.matrixIn[1]")
    cmds.connectAttr(f"{output_matrix}.matrixSum", offset_parent_attr)
    return core_node.Node(setup_node)


def get_control_parent_group_name_list():
    """
    Gets the list of base names needed to create the default parent groups
    for every control in the rig.

    Returns:
        ctrl_parent_group_list (list): list of base names
    """
    ctrl_parent_group_list = [RiggingConstants.OFFSET_PARENT_GROUP]
    return ctrl_parent_group_list


def duplicate_joint_for_automation(
    joint, suffix=core_naming.NamingConstants.Suffix.DRIVEN, parent=None, connect_rot_order=True
):
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
    jnt_as_node = core_hrchy.duplicate_object(
        obj=joint,
        name=f"{core_naming.get_short_name(joint)}_{suffix}",
        parent_only=True,
        reset_attributes=True,
        input_connections=False,
    )
    if connect_rot_order:
        core_attr.connect_attr(source_attr=f"{str(joint)}.rotateOrder", target_attr_list=f"{jnt_as_node}.rotateOrder")
    if parent:
        core_hrchy.parent(source_objects=jnt_as_node, target_parent=parent)
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
        if not cmds.objExists(f"{jnt}.radius"):
            continue
        scaled_radius = core_attr.get_attr(f"{jnt}.radius") * multiplier
        if isinstance(initial_value, (int, float)):
            scaled_radius = initial_value * multiplier
        cmds.setAttr(f"{jnt}.radius", scaled_radius)


def expose_rotation_order(target, attr_enum="xyz:yzx:zxy:xzy:yxz:zyx", attr_name="rotationOrder"):
    """
    Creates an attribute to control the rotation order of the target object and connects the attribute
    to the hidden "rotationOrder" attribute.
    The original value found in the hidden "rotateOrder" attribute is retained.
    Args:
        target (str, Node): Path to the target object (usually a control)
        attr_enum (str, optional): The ENUM used to create the custom rotation order enum.
                                   Default is "xyz", "yzx", "zxy", "xzy", "yxz", "zyx"  (Separated using ":")
        attr_name (str, optional): Name of the driving attribute. Default is "rotationOrder".
    Returns:
        str: The path to the created attribute.
    """
    _original_rot_order = cmds.getAttr(f"{target}.rotateOrder") or 0
    cmds.addAttr(target, longName=attr_name, attributeType="enum", keyable=True, en=attr_enum, niceName="Rotate Order")
    cmds.setAttr(f"{target}.{attr_name}", _original_rot_order)
    cmds.connectAttr(f"{target}.{attr_name}", f"{target}.rotateOrder", f=True)
    return f"{target}.{attr_name}"


def expose_shapes_visibility(target, shapes_type="nurbsCurve", attr_name="shapeVisibility", default_value=True):
    """
    Creates an attribute to control the visibility of the shapes found under of the provided transform.
    Args:
        target (str, Node): Path to the target object (usually a control)
        shapes_type (str, optional): Type used to filter only certain shapes. If set to None all shapes are included.
        attr_name (str, optional): Name of the driving attribute. Default is "shapeVisibility".
        default_value (bool, optional): Default value of the newly created attribute "shapeVisibility".
    Returns:
        str or None: The path to the created attribute or None if no shapes are found.
    """
    _extra_params = {}
    if shapes_type:
        _extra_params["typ"] = shapes_type
    shapes = cmds.listRelatives(target, shapes=True, fullPath=True, **_extra_params) or []
    if not shapes:
        return
    core_attr.add_attr(obj_list=target, attr_type="bool", attributes=attr_name, default=default_value, is_keyable=False)
    for shape in shapes:
        cmds.connectAttr(f"{target}.{attr_name}", f"{shape}.v")
    return f"{target}.{attr_name}"


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
            logger.debug(
                f"Unable to offset control orientation, not all objects were found in the scene. "
                f"Missing: {str(obj)}"
            )
            return
    cv_pos_dict = core_trans.get_component_positions_as_dict(obj_transform=ctrl, full_path=True, world_space=True)
    cmds.rotate(*orient_tuple, offset_transform, relative=True, objectSpace=True)
    core_trans.set_component_positions_from_dict(component_pos_dict=cv_pos_dict)


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
    children_last_jnt = cmds.listRelatives(ik_joints[-1], children=True, type="joint") or []

    # Prefix
    _prefix = ""
    if prefix and isinstance(prefix, str):
        _prefix = f"{prefix}_"

    # Find end joint
    end_ik_jnt = ""
    if len(children_last_jnt) == 1:
        end_ik_jnt = children_last_jnt[0]
    elif len(children_last_jnt) > 1:  # Find Joint Closest to ikHandle (when multiple joints are found)
        jnt_magnitude_pairs = []
        for jnt in children_last_jnt:
            ik_handle_ws_pos = cmds.xform(ik_handle, query=True, translation=True, worldSpace=True)
            jnt_ws_pos = cmds.xform(jnt, query=True, translation=True, worldSpace=True)
            mag = core_math.dist_xyz_to_xyz(
                ik_handle_ws_pos[0],
                ik_handle_ws_pos[1],
                ik_handle_ws_pos[2],
                jnt_ws_pos[0],
                jnt_ws_pos[1],
                jnt_ws_pos[2],
            )
            jnt_magnitude_pairs.append([jnt, mag])
        # Find The Lowest Distance
        current_jnt = jnt_magnitude_pairs[1:][0]
        current_closest = jnt_magnitude_pairs[1:][1]
        for pair in jnt_magnitude_pairs:
            if pair[1] < current_closest:
                current_closest = pair[1]
                current_jnt = pair[0]
        end_ik_jnt = current_jnt

    dist_one = cmds.distanceDimension(startPoint=(1, random.random() * 10, 1), endPoint=(2, random.random() * 10, 2))
    dist_one_transform = cmds.listRelatives(dist_one, parent=True, fullPath=True)[0]
    dist_one_transform = core_node.Node(dist_one_transform)
    start_loc_one, end_loc_one = cmds.listConnections(dist_one)
    start_loc_one = core_node.Node(start_loc_one)
    end_loc_one = core_node.Node(end_loc_one)

    core_trans.match_translate(source=ik_joints[0], target_list=start_loc_one)
    core_trans.match_translate(source=ik_handle, target_list=end_loc_one)

    # Rename Distance One Nodes
    dist_one_transform.rename(f"{_prefix}stretchyTerm_stretchyDistance")
    start_loc_one.rename(f"{_prefix}stretchyTerm_start")
    end_loc_one.rename(f"{_prefix}stretchyTerm_end")

    dist_nodes = {}  # [distance_node_transform, start_loc, end_loc, ik_handle_joint]
    for index in range(len(ik_joints)):
        dist_mid = cmds.distanceDimension(
            startPoint=(1, random.random() * 10, 1), endPoint=(2, random.random() * 10, 2)
        )
        dist_mid_transform = cmds.listRelatives(dist_mid, parent=True, fullPath=True)[0]
        start_loc, end_loc = cmds.listConnections(dist_mid)
        # Convert To Nodes
        dist_mid = core_node.Node(dist_mid)
        dist_mid_transform = core_node.Node(dist_mid_transform)
        start_loc = core_node.Node(start_loc)
        end_loc = core_node.Node(end_loc)
        # Rename Nodes
        dist_mid.rename(f"{_prefix}defaultTerm{core_str.get_int_as_en(index + 1).capitalize()}_stretchyDistanceShape")
        dist_mid_transform.rename(
            f"{_prefix}defaultTerm{core_str.get_int_as_en(index + 1).capitalize()}_stretchyDistance"
        )
        start_loc.rename(f"{_prefix}defaultTerm{core_str.get_int_as_en(index + 1).capitalize()}_start")
        end_loc.rename(f"{_prefix}defaultTerm{core_str.get_int_as_en(index + 1).capitalize()}_end")

        core_trans.match_translate(source=ik_joints[index], target_list=start_loc)
        if index < (len(ik_joints) - 1):
            core_trans.match_translate(source=ik_joints[index + 1], target_list=end_loc)
        else:
            core_trans.match_translate(source=end_ik_jnt, target_list=end_loc)
        dist_nodes[dist_mid] = [dist_mid_transform, start_loc, end_loc, ik_joints[index]]
        index += 1

    # Organize Basic Hierarchy
    stretchy_grp = cmds.group(name=f"{_prefix}stretchy_grp", empty=True, world=True)
    stretchy_grp = core_node.Node(stretchy_grp)
    core_hrchy.parent(source_objects=[dist_one_transform, start_loc_one, end_loc_one], target_parent=stretchy_grp)

    # Connect, Colorize and Organize Hierarchy
    default_dist_sum_node = core_node.create_node(node_type="plusMinusAverage", name=f"{_prefix}defaultTermSum_plus")
    index = 0
    for node in dist_nodes:
        cmds.connectAttr(f"{node}.distance", f"{default_dist_sum_node}.input1D[{index}]")
        for obj in dist_nodes.get(node):
            if cmds.objectType(obj) != "joint":
                core_color.set_color_outliner(obj_list=obj, rgb_color=(1, 0.5, 0.5))
                cmds.parent(obj, stretchy_grp)
        index += 1

    # Outliner Color
    core_color.set_color_outliner(obj_list=[dist_one_transform, start_loc_one, end_loc_one], rgb_color=(0.5, 1, 0.2))

    # Connect Nodes
    nonzero_stretch_condition_node = core_node.create_node(
        node_type="condition", name=f"{_prefix}stretchyNonZero_condition"
    )
    nonzero_multiply_node = core_node.create_node(
        node_type="multiplyDivide", name=f"{_prefix}onePctDistCondition_multiply"
    )
    cmds.connectAttr(f"{default_dist_sum_node}.output1D", f"{nonzero_multiply_node}.input1X")
    cmds.setAttr(f"{nonzero_multiply_node}.input2X", 0.01)
    cmds.connectAttr(f"{nonzero_multiply_node}.outputX", f"{nonzero_stretch_condition_node}.colorIfTrueR")
    cmds.connectAttr(f"{nonzero_multiply_node}.outputX", f"{nonzero_stretch_condition_node}.secondTerm")
    cmds.setAttr(f"{nonzero_stretch_condition_node}.operation", 5)

    stretch_normalization_node = core_node.create_node(
        node_type="multiplyDivide", name=f"{_prefix}distNormalization_divide"
    )
    cmds.connectAttr(f"{dist_one_transform}.distance", f"{nonzero_stretch_condition_node}.firstTerm")
    cmds.connectAttr(f"{dist_one_transform}.distance", f"{nonzero_stretch_condition_node}.colorIfFalseR")
    cmds.connectAttr(f"{nonzero_stretch_condition_node}.outColorR", f"{stretch_normalization_node}.input1X")

    cmds.connectAttr(f"{default_dist_sum_node}.output1D", f"{stretch_normalization_node}.input2X")

    cmds.setAttr(f"{stretch_normalization_node}.operation", 2)

    stretch_condition_node = core_node.create_node(node_type="condition", name=f"{_prefix}stretchyAutomation_condition")
    cmds.setAttr(f"{stretch_condition_node}.operation", 3)
    cmds.connectAttr(f"{nonzero_stretch_condition_node}.outColorR", f"{stretch_condition_node}.firstTerm")
    cmds.connectAttr(f"{default_dist_sum_node}.output1D", f"{stretch_condition_node}.secondTerm")
    cmds.connectAttr(f"{stretch_normalization_node}.outputX", f"{stretch_condition_node}.colorIfTrueR")

    # Constraints
    cmds.pointConstraint(ik_joints[0], start_loc_one)
    start_loc_condition = ""
    for node in dist_nodes:
        if dist_nodes.get(node)[3] == ik_joints[0:][0]:
            start_loc_condition = cmds.pointConstraint(ik_joints[0], dist_nodes.get(node)[1])

    # Attribute Holder Setup
    if attribute_holder:
        if cmds.objExists(attribute_holder):
            cmds.pointConstraint(attribute_holder, end_loc_one)
            cmds.addAttr(attribute_holder, ln="stretch", at="double", k=True, minValue=0, maxValue=1)
            cmds.setAttr(f"{attribute_holder}.stretch", 1)
            cmds.addAttr(attribute_holder, ln="squash", at="double", k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder, ln="stretchFromSource", at="bool", k=True)
            cmds.addAttr(attribute_holder, ln="saveVolume", at="double", k=True, minValue=0, maxValue=1)
            cmds.addAttr(attribute_holder, ln="baseVolumeMultiplier", at="double", k=True, minValue=0, maxValue=1)
            cmds.setAttr(f"{attribute_holder}.baseVolumeMultiplier", 0.5)
            cmds.addAttr(attribute_holder, ln="minimumVolume", at="double", k=True, minValue=0.01, maxValue=1)
            cmds.addAttr(attribute_holder, ln="maximumVolume", at="double", k=True, minValue=0)
            cmds.setAttr(f"{attribute_holder}.minimumVolume", 0.4)
            cmds.setAttr(f"{attribute_holder}.maximumVolume", 2)
            cmds.setAttr(f"{attribute_holder}.stretchFromSource", 1)

            # Stretch From Body
            from_body_reverse_node = core_node.create_node(
                node_type="reverse", name=f"{_prefix}stretchFromSource_reverse"
            )
            cmds.connectAttr(f"{attribute_holder}.stretchFromSource", f"{from_body_reverse_node}.inputX")
            cmds.connectAttr(f"{from_body_reverse_node}.outputX", f"{start_loc_condition[0]}.w0")

            # Squash
            squash_condition_node = core_node.create_node(
                node_type="condition", name=f"{_prefix}squashAutomation_condition"
            )
            cmds.setAttr(f"{squash_condition_node}.secondTerm", 1)
            cmds.setAttr(f"{squash_condition_node}.colorIfTrueR", 1)
            cmds.setAttr(f"{squash_condition_node}.colorIfFalseR", 3)
            cmds.connectAttr(f"{attribute_holder}.squash", f"{squash_condition_node}.firstTerm")
            cmds.connectAttr(f"{squash_condition_node}.outColorR", f"{stretch_condition_node}.operation")

            # Stretch
            activation_blend_node = core_node.create_node(
                node_type="blendTwoAttr", name=f"{_prefix}stretchyActivation_blend"
            )
            cmds.setAttr(f"{activation_blend_node}.input[0]", 1)
            cmds.connectAttr(f"{stretch_condition_node}.outColorR", f"{activation_blend_node}.input[1]")
            cmds.connectAttr(f"{attribute_holder}.stretch", f"{activation_blend_node}.attributesBlender")

            for jnt in ik_joints:
                cmds.connectAttr(f"{activation_blend_node}.output", f"{jnt}.scaleX")

            # Save Volume
            save_volume_condition_node = core_node.create_node(
                node_type="condition", name=f"{_prefix}saveVolume_condition"
            )
            volume_normalization_divide_node = core_node.create_node(
                node_type="multiplyDivide", name=f"{_prefix}volumeNormalization_divide"
            )
            volume_value_divide_node = core_node.create_node(
                node_type="multiplyDivide", name=f"{_prefix}volumeValue_divide"
            )
            xy_divide_node = core_node.create_node(node_type="multiplyDivide", name=f"{_prefix}volumeXY_divide")
            volume_blend_node = core_node.create_node(node_type="blendTwoAttr", name=f"{_prefix}volumeActivation_blend")
            volume_clamp_node = core_node.create_node(node_type="clamp", name=f"{_prefix}volumeLimits_clamp")
            volume_base_blend_node = core_node.create_node(node_type="blendTwoAttr", name=f"{_prefix}volumeBase_blend")

            cmds.setAttr(f"{save_volume_condition_node}.secondTerm", 1)
            cmds.setAttr(f"{volume_normalization_divide_node}.operation", 2)  # Divide
            cmds.setAttr(f"{volume_value_divide_node}.operation", 2)  # Divide
            cmds.setAttr(f"{xy_divide_node}.operation", 2)  # Divide

            cmds.connectAttr(
                f"{nonzero_stretch_condition_node}.outColorR", f"{volume_normalization_divide_node}.input1X"
            )  # Distance One
            cmds.connectAttr(f"{default_dist_sum_node}.output1D", f"{volume_normalization_divide_node}.input2X")

            cmds.connectAttr(f"{volume_normalization_divide_node}.outputX", f"{volume_value_divide_node}.input1X")
            cmds.connectAttr(f"{stretch_normalization_node}.outputX", f"{volume_value_divide_node}.input2X")

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
            cmds.connectAttr(f"{save_volume_condition_node}.outColorR", f"{volume_base_blend_node}.input[1]")
            cmds.connectAttr(f"{attribute_holder}.baseVolumeMultiplier", f"{volume_base_blend_node}.attributesBlender")

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
    core_attr.add_attr(obj_list=start_loc_one, attr_type="string", attributes=["termStart"])
    core_attr.add_attr(obj_list=end_loc_one, attr_type="string", attributes=["termEnd"])
    core_attr.connect_attr(source_attr=f"{stretchy_grp}.message", target_attr_list=f"{start_loc_one}.termStart")
    core_attr.connect_attr(source_attr=f"{stretchy_grp}.message", target_attr_list=f"{end_loc_one}.termEnd")

    return stretchy_grp


def create_switch_setup(
    source_a,
    source_b,
    target_base,
    attr_holder,
    visibility_a=None,
    visibility_b=None,
    shape_visibility=True,
    attr_influence=RiggingConstants.ATTR_INFLUENCE_SWITCH,
    constraint_type=core_cnstr.ConstraintTypes.PARENT,
    maintain_offset=False,
    prefix=None,
    invert=False,
):
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
        attr_holder (str, Node): The attribute holder object name/path.
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
        invert (bool, optional): inverts the influences. You cannot just invert the given sources and visibilities,
                                 you need to use this flag also to flip the connection with the constraint

    Returns:
        tuple: A tuple with the switch output attributes.
    """
    # Check attr holder and convert it to Node
    if not attr_holder or not cmds.objExists(attr_holder):
        logger.warning(f"Missing attribute holder. Switch setup was skipped.")
        return
    attr_holder = core_node.Node(attr_holder)
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

    if invert:
        source_a, source_b = source_b, source_a
        visibility_a, visibility_b = visibility_b, visibility_a

    # Length Check
    list_len = {len(source_a), len(source_b), len(target_base)}
    if len(list_len) != 1:
        logger.warning(f"Unable to create switch setup. All input lists must be of the same length.")
        return

    # Prefix
    _prefix = ""
    if prefix:
        _prefix = f"{prefix}_"

    # Switch Setup
    attr_influence_a = f"influenceA"
    attr_influence_b = f"influenceB"
    attr_vis_a = f"visibilityA"
    attr_vis_b = f"visibilityB"
    core_attr.add_attr(
        obj_list=attr_holder, attributes=attr_influence, attr_type="double", is_keyable=True, maximum=1, minimum=0
    )
    core_attr.add_attr(obj_list=attr_holder, attributes=attr_influence_a, attr_type="double", is_keyable=False)
    core_attr.add_attr(obj_list=attr_holder, attributes=attr_influence_b, attr_type="double", is_keyable=False)
    core_attr.add_attr(obj_list=attr_holder, attributes=attr_vis_a, attr_type="bool", is_keyable=False)
    core_attr.add_attr(obj_list=attr_holder, attributes=attr_vis_b, attr_type="bool", is_keyable=False)
    # Setup Visibility Condition
    cmds.setAttr(f"{attr_holder}.{attr_influence}", 1)
    condition = core_node.create_node(node_type="condition", name=f"{_prefix}switchVisibility_condition")
    cmds.connectAttr(f"{attr_holder}.{attr_influence}", f"{condition}.firstTerm")
    core_attr.set_attr(attribute_path=f"{condition}.operation", value=4)  # Operation = Less Than (4)
    core_attr.set_attr(attribute_path=f"{condition}.secondTerm", value=0.5)  # Range A:0->0.5  B: 0.5->1
    core_attr.set_attr(obj_list=condition, attr_list=["colorIfTrueR", "colorIfTrueG", "colorIfTrueB"], value=1)
    core_attr.set_attr(obj_list=condition, attr_list=["colorIfFalseR", "colorIfFalseG", "colorIfFalseB"], value=0)
    reverse_visibility = core_node.create_node(node_type="reverse", name=f"{_prefix}switchVisibility_reverse")
    cmds.connectAttr(f"{condition}.outColorR", f"{reverse_visibility}.inputX", f=True)
    # Setup Influence Reversal
    reverse_influence = core_node.create_node(node_type="reverse", name=f"{_prefix}switchInfluence_reverse")
    cmds.connectAttr(f"{attr_holder}.{attr_influence}", f"{reverse_influence}.inputX", f=True)

    # Send Data back to Attr Holder
    cmds.connectAttr(f"{attr_holder}.{attr_influence}", f"{attr_holder}.{attr_influence_a}", f=True)
    cmds.connectAttr(f"{reverse_influence}.outputX", f"{attr_holder}.{attr_influence_b}", f=True)
    cmds.connectAttr(f"{reverse_visibility}.outputX", f"{attr_holder}.{attr_vis_a}", f=True)
    cmds.connectAttr(f"{condition}.outColorR", f"{attr_holder}.{attr_vis_b}", f=True)

    # Constraints
    constraints = []
    for source_a, source_b, target in zip(source_a, source_b, target_base):
        _constraints = core_cnstr.constraint_targets(
            source_driver=[source_a, source_b],
            target_driven=target,
            constraint_type=constraint_type,
            maintain_offset=maintain_offset,
        )
        if _constraints:
            constraints.extend(_constraints)
    for constraint in constraints:
        if invert:
            cmds.connectAttr(f"{attr_holder}.{attr_influence_b}", f"{constraint}.w0", force=True)
            cmds.connectAttr(f"{attr_holder}.{attr_influence_a}", f"{constraint}.w1", force=True)
        else:
            cmds.connectAttr(f"{attr_holder}.{attr_influence_a}", f"{constraint}.w0", force=True)
            cmds.connectAttr(f"{attr_holder}.{attr_influence_b}", f"{constraint}.w1", force=True)

    # Visibility Setup
    if isinstance(visibility_a, str):
        visibility_a = [visibility_a]
    if not visibility_a:
        visibility_a = []
    else:
        visibility_a = core_iter.sanitize_maya_list(input_list=visibility_a)
    if isinstance(visibility_b, str):
        visibility_b = [visibility_b]
    if not visibility_b:
        visibility_b = []
    else:
        visibility_b = core_iter.sanitize_maya_list(input_list=visibility_b)
    for obj_a in visibility_a:
        if shape_visibility:
            for shape in cmds.listRelatives(obj_a, shapes=True, fullPath=True) or []:
                cmds.connectAttr(f"{attr_holder}.{attr_vis_a}", f"{shape}.v", f=True)
        else:
            cmds.connectAttr(f"{attr_holder}.{attr_vis_a}", f"{obj_a}.v", f=True)
    for obj_b in visibility_b:
        if shape_visibility:
            for shape in cmds.listRelatives(obj_b, shapes=True, fullPath=True) or []:
                cmds.connectAttr(f"{attr_holder}.{attr_vis_b}", f"{shape}.v", f=True)
        else:
            cmds.connectAttr(f"{attr_holder}.{attr_vis_b}", f"{obj_b}.v", f=True)
    # Return Data
    return (
        f"{attr_holder}.{attr_influence_a}",
        f"{attr_holder}.{attr_influence_b}",
        f"{attr_holder}.{attr_vis_a}",
        f"{attr_holder}.{attr_vis_b}",
    )


def add_limit_lock_translate_setup(
    target, lock_attr="lockTranslate", dimensions=("x", "y", "z"), attr_holder=None, default_value=True, limit_value=0
):
    """
    Creates a translation lock attribute. If active, it sets the limit of the translation.

    Args:
        target (str, Node): Name/Path to the target object. Object that will receive the attribute.
        lock_attr (str, optional) : Name of the lock attribute. Default is "lockTranslate"
        dimensions (tuple, optional): List of affected dimensions. Default is "x", "y", and "z"
        attr_holder (str, Node, optional): If provided, the target and attribute holder objects can be different.
                                        The default is "None" which means the "target" is also the attribute holder.
                                        Target: receives the limit and won't be able to move when attribute is active.
                                        Attribute Holder (attr_holder): receives the attribute that controls limit.
        default_value (bool, optional): Determines the initial value of lock attribute. Default is "True"
        limit_value (float, int, optional): Limit that defines "locked" for the target object. Default: 0 for translate.
    Returns:
        str: Path to the created attribute.
    """
    # Determine Attribute Holder
    _attr_holder = attr_holder
    if not _attr_holder:
        _attr_holder = target
    # Create Attribute
    core_attr.add_attr(obj_list=_attr_holder, attributes=lock_attr, attr_type="bool", default=default_value)
    # Create Connections
    for dimension in dimensions:  # Default is: x, y, z
        cmds.setAttr(f"{target}.minTrans{dimension.upper()}Limit", limit_value)
        cmds.setAttr(f"{target}.maxTrans{dimension.upper()}Limit", limit_value)
        cmds.connectAttr(f"{_attr_holder}.{lock_attr}", f"{target}.minTrans{dimension.upper()}LimitEnable")
        cmds.connectAttr(f"{_attr_holder}.{lock_attr}", f"{target}.maxTrans{dimension.upper()}LimitEnable")
    return f"{_attr_holder}.{lock_attr}"


def add_limit_lock_rotate_setup(
    target, lock_attr="lockRotate", dimensions=("x", "y", "z"), attr_holder=None, default_value=True, limit_value=0
):
    """
    Creates a rotation lock attribute. If active, it sets the limit of the rotation.

    Args:
        target (str, Node): Name/Path to the target object. Object that will receive the attribute.
        lock_attr (str, optional) : Name of the lock attribute. Default is "lockRotate"
        dimensions (tuple, optional): List of affected dimensions. Default is "x", "y", and "z"
        attr_holder (str, Node, optional): If provided, the target and attribute holder objects can be different.
                                        The default is "None" which means the "target" is also the attribute holder.
                                        Target: receives the limit and won't be able to move when attribute is active.
                                        Attribute Holder (attr_holder): receives the attribute that controls limit.
        default_value (bool, optional): Determines the initial value of lock attribute. Default is "True"
        limit_value (float, int, optional): Limit value that defines "locked" for the target. Default is 0 for rotate.
    Returns:
        str: Path to the created attribute.
    """
    # Determine Attribute Holder
    _attr_holder = attr_holder
    if not _attr_holder:
        _attr_holder = target
    # Create Attribute
    core_attr.add_attr(obj_list=_attr_holder, attributes=lock_attr, attr_type="bool", default=default_value)
    # Create Connections
    for dimension in dimensions:  # x, y, z
        cmds.setAttr(f"{target}.minRot{dimension.upper()}Limit", limit_value)
        cmds.setAttr(f"{target}.maxRot{dimension.upper()}Limit", limit_value)
        cmds.connectAttr(f"{_attr_holder}.{lock_attr}", f"{target}.minRot{dimension.upper()}LimitEnable")
        cmds.connectAttr(f"{_attr_holder}.{lock_attr}", f"{target}.maxRot{dimension.upper()}LimitEnable")
    return f"{_attr_holder}.{lock_attr}"


def add_limit_lock_scale_setup(
    target, lock_attr="lockScale", dimensions=("x", "y", "z"), attr_holder=None, default_value=True, limit_value=1
):
    """
    Creates a scale lock attribute. If active, it sets the limit of the scale.

    Args:
        target (str, Node): Name/Path to the target object. Object that will receive the attribute.
        lock_attr (str, optional) : Name of the lock attribute. Default is "locScale"
        dimensions (tuple, optional): List of affected dimensions. Default is "x", "y", and "z"
        attr_holder (str, Node, optional): If provided, the target and attribute holder objects can be different.
                                        The default is "None" which means the "target" is also the attribute holder.
                                        Target: receives the limit and won't be able to move when attribute is active.
                                        Attribute Holder (attr_holder): receives the attribute that controls limit.
        default_value (bool, optional): Determines the initial value of lock attribute. Default is "True"
        limit_value (float, int, optional): Limit value that defines "locked" for the target. Default is 1 for scale.
    Returns:
        str: Path to the created attribute.
    """
    # Determine Attribute Holder
    _attr_holder = attr_holder
    if not _attr_holder:
        _attr_holder = target
    # Create Attribute
    core_attr.add_attr(obj_list=_attr_holder, attributes=lock_attr, attr_type="bool", default=default_value)
    # Create Connections
    for dimension in dimensions:  # x, y, z
        cmds.setAttr(f"{target}.minScale{dimension.upper()}Limit", limit_value)
        cmds.setAttr(f"{target}.maxScale{dimension.upper()}Limit", limit_value)
        cmds.connectAttr(f"{_attr_holder}.{lock_attr}", f"{target}.minScale{dimension.upper()}LimitEnable")
        cmds.connectAttr(f"{_attr_holder}.{lock_attr}", f"{target}.maxScale{dimension.upper()}LimitEnable")
    return f"{_attr_holder}.{lock_attr}"


def add_limit_lock_rotate_with_exception(
    target, lock_attr=None, exception="z", attr_holder=None, default_value=True, limit_value=0
):
    """
    Since it's common to lock other rotate channels, but one. This passthrough function pre-populates the arguments
    of "add_limit_lock_rotate_setup" to lock

    Args:
        target (str, Node): Name/Path to the target object. Object that will receive the attribute.
        lock_attr (str, optional) : Name of the lock attribute. If not provided, one will be generated based
                                    on the exception value. For example, if the exception is "z" than the lock name
                                    becomes "lockXY". (removing the exception from the name)
        exception (str, tuple, optional): Exception dimension. This is the dimension to be ignored when creating
                                          the lock setup.
        attr_holder (str, Node, optional): If provided, the target and attribute holder objects can be different.
                                        The default is "None" which means the "target" is also the attribute holder.
                                        Target: receives the limit and won't be able to move when attribute is active.
                                        Attribute Holder (attr_holder): receives the attribute that controls limit.
        default_value (bool, optional): Determines the initial value of lock attribute. Default is "True"
        limit_value (float, int, optional): Limit value that defines "locked" for the target. Default is 0 for rotate.
    Returns:
        str: Path to the created attribute.
    """
    # Determine Lock Attr
    _lock_attr = lock_attr
    if not _lock_attr:
        _lock_attr = "lockXYZ"
        for char in exception:
            _lock_attr = _lock_attr.replace(char.upper(), "")
    # Determine Dimensions
    _dimensions = []
    for dimension in ("x", "y", "z"):
        if dimension not in tuple(exception):
            _dimensions.append(dimension)
    _dimensions = tuple(_dimensions)
    return add_limit_lock_rotate_setup(
        target=target,
        lock_attr=_lock_attr,
        dimensions=_dimensions,
        attr_holder=attr_holder,
        default_value=default_value,
        limit_value=limit_value,
    )


def create_enum_switch(
    attribute_holder,
    targets,
    display_names=None,
    attr_name="modeSwitch",
    controlled_attrs="visibility",
    default_index=0,
    none_label="None",
):
    """
    Adds an enum attribute to `attribute_holder` that controls one or more attributes
    (e.g., visibility, translateX) across different target objects or groups of objects.

    Args:
        attribute_holder (str): Node to receive the enum attribute.
        targets (list): List of strings, None, or lists of strings/None. Each entry defines one enum state.
        display_names (list of str or None, optional): Friendly names for the enum values.
                                        Must match `targets` in length.
                                        None entries will use the first object name in the group or `none_label`.
        attr_name (str): Name of the enum attribute to add.
        controlled_attrs (str or list of str): Attribute(s) to control (e.g., "visibility", "translateX").
                                               Can be a string or a list of strings.
        default_index (int): Index of the enum value that should be active after setup. Default is 0.
        none_label (str): Label to use for enum items corresponding to None targets. Default is "None".
    """
    if not cmds.objExists(attribute_holder):
        raise ValueError(f"Attribute holder '{attribute_holder}' does not exist.")

    # Normalize controlled attributes
    if isinstance(controlled_attrs, str):
        controlled_attrs = [controlled_attrs]

    # Normalize targets to list of lists
    normalized_targets = []
    all_objects = set()
    for entry in targets:
        if entry is None:
            group = []
        elif isinstance(entry, str):
            group = [entry]
        elif isinstance(entry, list):
            group = [obj for obj in entry if obj is not None]
        else:
            raise TypeError("Each target must be a string, list of strings, or None.")
        normalized_targets.append(group)
        all_objects.update(group)

    # Validate objects exist (skip empty groups)
    for obj in all_objects:
        if not cmds.objExists(obj):
            raise ValueError(f"Target object '{obj}' does not exist.")

    # Resolve display names
    if display_names:
        if len(display_names) != len(normalized_targets):
            raise ValueError("Length of display_names must match number of targets.")
        enum_labels = []
        for i, (group, name) in enumerate(zip(normalized_targets, display_names)):
            if name is None:
                label = group[0].split("|")[-1] if group else none_label
            else:
                label = name
            enum_labels.append(label)
    else:
        enum_labels = [group[0].split("|")[-1] if group else none_label for group in normalized_targets]

    enum_string = ":".join(enum_labels)

    # Add the enum attribute
    if cmds.attributeQuery(attr_name, node=attribute_holder, exists=True):
        raise ValueError(f"Attribute '{attr_name}' already exists on '{attribute_holder}'.")

    cmds.addAttr(attribute_holder, longName=attr_name, attributeType="enum", enumName=enum_string, keyable=True)
    driver_attr = f"{attribute_holder}.{attr_name}"

    # Set driven keys
    for enum_index, group in enumerate(normalized_targets):
        for obj in group:  # only iterate real objects, skip None
            for attr in controlled_attrs:
                driven_attr = f"{obj}.{attr}"
                if not cmds.objExists(driven_attr):
                    raise ValueError(f"Driven attribute '{driven_attr}' does not exist.")
                cmds.setAttr(driver_attr, enum_index)
                cmds.setAttr(driven_attr, True)
                cmds.setDrivenKeyframe(driven_attr, currentDriver=driver_attr)

        # Ensure other objects are turned off for this enum
        inactive_objects = all_objects - set(group)
        for obj in inactive_objects:
            for attr in controlled_attrs:
                driven_attr = f"{obj}.{attr}"
                cmds.setAttr(driver_attr, enum_index)
                cmds.setAttr(driven_attr, False)
                cmds.setDrivenKeyframe(driven_attr, currentDriver=driver_attr)

    # Set to default value
    if not (0 <= default_index < len(normalized_targets)):
        logging.warning(f"Default index {default_index} is out of range for {len(normalized_targets)} targets.")

    cmds.setAttr(driver_attr, default_index)


def duplicate_and_offset_mesh(
    source_mesh,
    offset,
    parent=None,
    block_selection_attr=None,
    driver_joint=None,
    hide_original=True,
    suffix="_preview",
    condition=None,
):
    """
    Duplicate (or reuse) a preview mesh, create (or reuse) a carrier joint constrained
    to the driver joint, and apply conditional offsets on translation, rotation, and scale
    that stack across multiple calls.

    Args:
        source_mesh (str): Name of the mesh to duplicate.
        offset (Transform, Vector3, tuple/list of 3,6, or 9 elements, optional): Position/rotation/scale offsets.
            - 3 elements = translation only
            - 6 elements = translation + rotation
            - 9 elements = translation + rotation + scale
        parent (str, optional): Node under which the duplicate mesh and carrier joint will be parented.
        block_selection_attr (str, optional): Attribute to connect to the duplicate's overrideEnabled.
        driver_joint (str, optional): Joint to duplicate as the carrier joint for the duplicate mesh.
        hide_original (bool): Whether to hide the original mesh (default True).
        suffix (str, optional): Suffix to be added to the duplicated mesh.
        condition (str, optional): Maya attribute (e.g., "ctrl.visibility") that drives whether
            the offset is applied.

    Returns:
        tuple[str, str]: (duplicated mesh, carrier joint)
    """
    # --- Parse offset ---
    rot_x = rot_y = rot_z = scl_x = scl_y = scl_z = None

    if isinstance(offset, core_trans.Transform):
        pos_x, pos_y, pos_z = offset.position.get_as_tuple()
        rot_x, rot_y, rot_z = offset.rotation.get_as_tuple()
        scl_x, scl_y, scl_z = offset.scale.get_as_tuple()
    elif isinstance(offset, core_trans.Vector3):
        pos_x, pos_y, pos_z = offset.get_as_tuple()
    elif isinstance(offset, (tuple, list)):
        if len(offset) == 3:
            pos_x, pos_y, pos_z = offset
        elif len(offset) == 6:
            pos_x, pos_y, pos_z = offset[:3]
            rot_x, rot_y, rot_z = offset[3:]
        elif len(offset) == 9:
            pos_x, pos_y, pos_z = offset[:3]
            rot_x, rot_y, rot_z = offset[3:6]
            scl_x, scl_y, scl_z = offset[6:]
        else:
            raise ValueError("Offset tuple/list must have 3, 6, or 9 elements.")
    else:
        raise ValueError("Offset must be Transform, Vector3, or a 3/6/9-element tuple/list.")

    dup_mesh = f"{source_mesh}{suffix}"

    # --- Duplicate mesh if needed ---
    if not cmds.objExists(dup_mesh):
        dup_mesh = cmds.duplicate(source_mesh, name=dup_mesh)[0]
        core_attr.set_attr(attribute_path=f"{dup_mesh}.v", value=1)
        if hide_original and cmds.objExists(source_mesh):
            core_attr.set_attr(attribute_path=f"{source_mesh}.v", value=0)

    # --- Carrier joint setup ---
    carrier_joint = None
    pcon = None
    scon = None
    if driver_joint:
        driver_short = core_naming.get_short_name(driver_joint)
        dupe_short = core_naming.get_short_name(dup_mesh)
        carrier_joint = f"{driver_short}_{dupe_short}_offsetJnt"

        if not cmds.objExists(carrier_joint):
            carrier_joint = cmds.duplicate(driver_joint, parentOnly=True, name=carrier_joint)[0]
            cmds.setAttr(f"{carrier_joint}.v", 0)
            pcon = cmds.parentConstraint(driver_joint, carrier_joint, maintainOffset=False)[0]
            scon = cmds.scaleConstraint(driver_joint, carrier_joint, maintainOffset=False)
            if cmds.objExists(dup_mesh):
                cmds.skinCluster(
                    carrier_joint, dup_mesh, toSelectedBones=True, bindMethod=0, skinMethod=0, normalizeWeights=1
                )
        else:
            existing_pcons = cmds.listRelatives(carrier_joint, type="parentConstraint") or []
            pcon = (
                existing_pcons[0]
                if existing_pcons
                else cmds.parentConstraint(driver_joint, carrier_joint, maintainOffset=False)[0]
            )
            existing_scons = cmds.listRelatives(carrier_joint, type="scaleConstraint") or []
            scon = (
                existing_scons[0]
                if existing_scons
                else cmds.scaleConstraint(driver_joint, carrier_joint, maintainOffset=False)[0]
            )

        # --- Determine target index for pcon ---
        targets = cmds.parentConstraint(pcon, q=True, tl=True) or []
        t_index = targets.index(driver_joint) if driver_joint in targets else 0

        # --- Helper to create/reuse PMA ---
        def get_pma(name):
            """
            Get an existing plusMinusAverage node by name, or create one if it doesn't exist.

            Args:
                name (str): The desired name of the plusMinusAverage node.

            Returns:
                str: The name of the existing or newly created plusMinusAverage node.
            """
            if not cmds.objExists(name):
                pma = cmds.createNode("plusMinusAverage", name=name)
                cmds.setAttr(f"{pma}.operation", 1)  # Sum
                return pma
            return name

        # --- Translation PMA (start at 0,0,0) ---
        pma_trans = get_pma(f"{dup_mesh}_offsetSum_trans")
        for axis, child in (("X", "output3Dx"), ("Y", "output3Dy"), ("Z", "output3Dz")):
            attr = f"{pcon}.target[{t_index}].targetOffsetTranslate{axis}"
            if cmds.getAttr(attr, lock=True):
                core_attr.set_attr_state(attr, locked=False)
            if not cmds.listConnections(f"{pma_trans}.output3D.{child}", plugs=True):
                cmds.connectAttr(f"{pma_trans}.output3D.{child}", attr, force=True)

        # --- Rotation PMA (start at 0,0,0) ---
        if rot_x is not None:
            pma_rot = get_pma(f"{dup_mesh}_offsetSum_rot")
            for axis, child in (("X", "output3Dx"), ("Y", "output3Dy"), ("Z", "output3Dz")):
                attr = f"{pcon}.target[{t_index}].targetOffsetRotate{axis}"
                if cmds.getAttr(attr, lock=True):
                    core_attr.set_attr_state(attribute_path=attr, locked=False)
                if not cmds.listConnections(f"{pma_rot}.output3D.{child}", plugs=True):
                    cmds.connectAttr(f"{pma_rot}.output3D.{child}", attr, force=True)

        # --- Scale PMA (start at 1, 1, 1) ---
        if scl_x is not None:
            pma_scl = get_pma(f"{dup_mesh}_offsetSum_scl")
            if not cmds.getAttr(f"{pma_scl}.input3D[0]", multiIndices=True):
                cmds.setAttr(f"{pma_scl}.input3D[0].input3Dx", 1)
                cmds.setAttr(f"{pma_scl}.input3D[0].input3Dy", 1)
                cmds.setAttr(f"{pma_scl}.input3D[0].input3Dz", 1)
            for axis, child, attr_name in zip(
                ("X", "Y", "Z"), ("output3Dx", "output3Dy", "output3Dz"), ("offsetX", "offsetY", "offsetZ")
            ):
                attr = f"{scon[0]}.{attr_name}"
                if cmds.getAttr(attr, lock=True):
                    core_attr.set_attr_state(attribute_path=attr, locked=False)
                if not cmds.listConnections(f"{pma_scl}.output3D.{child}", plugs=True):
                    cmds.connectAttr(f"{pma_scl}.output3D.{child}", attr, force=True)

        # --- Connect new condition to PMAs separately ---
        if condition:
            # Translation
            if pos_x is not None or pos_y is not None or pos_z is not None:
                cond_trans = cmds.createNode("condition", name=f"{dup_mesh}_offsetCond_trans")
                cmds.setAttr(f"{cond_trans}.operation", 0)  # Equal
                cmds.setAttr(f"{cond_trans}.secondTerm", 1)
                cmds.connectAttr(condition, f"{cond_trans}.firstTerm", force=True)
                for ch, val in (("R", pos_x or 0), ("G", pos_y or 0), ("B", pos_z or 0)):
                    cmds.setAttr(f"{cond_trans}.colorIfTrue{ch}", val)
                    cmds.setAttr(f"{cond_trans}.colorIfFalse{ch}", 0)
                used = cmds.getAttr(f"{pma_trans}.input3D", multiIndices=True) or []
                next_idx = (max(used) + 1) if used else 0
                cmds.connectAttr(f"{cond_trans}.outColor", f"{pma_trans}.input3D[{next_idx}]", force=True)

            # Rotation (If available)
            if rot_x is not None:
                cond_rot = cmds.createNode("condition", name=f"{dup_mesh}_offsetCond_rot")
                cmds.setAttr(f"{cond_rot}.operation", 0)  # Equal
                cmds.setAttr(f"{cond_rot}.secondTerm", 1)
                cmds.connectAttr(condition, f"{cond_rot}.firstTerm", force=True)
                for ch, val in (("R", rot_x), ("G", rot_y), ("B", rot_z)):
                    cmds.setAttr(f"{cond_rot}.colorIfTrue{ch}", val)
                    cmds.setAttr(f"{cond_rot}.colorIfFalse{ch}", 0)
                used = cmds.getAttr(f"{pma_rot}.input3D", multiIndices=True) or []
                next_idx = (max(used) + 1) if used else 0
                cmds.connectAttr(f"{cond_rot}.outColor", f"{pma_rot}.input3D[{next_idx}]", force=True)

            # Scale (If available)
            if scl_x is not None:
                cond_scl = cmds.createNode("condition", name=f"{dup_mesh}_offsetCond_scl")
                cmds.setAttr(f"{cond_scl}.operation", 0)  # Equal
                cmds.setAttr(f"{cond_scl}.secondTerm", 1)
                cmds.connectAttr(condition, f"{cond_scl}.firstTerm", force=True)
                for ch, val in (("R", scl_x), ("G", scl_y), ("B", scl_z)):
                    cmds.setAttr(f"{cond_scl}.colorIfTrue{ch}", val)
                    cmds.setAttr(f"{cond_scl}.colorIfFalse{ch}", 0)
                used = cmds.getAttr(f"{pma_scl}.input3D", multiIndices=True) or []
                next_idx = (max(used) + 1) if used else 0
                cmds.connectAttr(f"{cond_scl}.outColor", f"{pma_scl}.input3D[{next_idx}]", force=True)

    # --- Parent carrier joint and mesh only if not already parented ---
    if parent and cmds.objExists(parent):
        if carrier_joint and cmds.objExists(carrier_joint):
            if cmds.listRelatives(carrier_joint, parent=True) != [parent]:
                core_hrchy.parent(source_objects=carrier_joint, target_parent=parent)
        if cmds.objExists(dup_mesh):
            if cmds.listRelatives(dup_mesh, parent=True) != [parent]:
                core_hrchy.parent(source_objects=dup_mesh, target_parent=parent)

    # --- Display controls ---
    if block_selection_attr and cmds.objExists(dup_mesh):
        connections = cmds.listConnections(f"{dup_mesh}.overrideEnabled", plugs=True) or []
        if block_selection_attr not in connections:
            try:
                cmds.connectAttr(block_selection_attr, f"{dup_mesh}.overrideEnabled", force=True)
            except Exception as e:
                logger.debug(f"Failed to connect block_selection_attr: {e}")
        else:
            logger.debug(f"{dup_mesh}.overrideEnabled already connected; skipping.")

    if cmds.objExists(dup_mesh):
        core_attr.set_attr(attribute_path=f"{dup_mesh}.overrideDisplayType", value=2)
        core_attr.set_attr(attribute_path=f"{dup_mesh}.v", value=True)

    return dup_mesh, carrier_joint


def create_fk_wave_setup(
    controls,
    driven_axis="rotateZ",
    setup_name=None,
    separator_name="sineWave",
    default_amplitude=5.0,
    default_wavelength=2.0,
    default_envelope=1.0,
):
    """
    Rigs a sine wave deformer onto a sequence of FK controls.

    This function first adds the necessary control attributes to the lead control.
    It then creates a node network using an expression to generate the wave
    motion, which is applied to newly created offset groups above each control.

    Args:
        controls (list[str]): A list of control names in sequential order. (Base first)
        driven_axis (str, optional): The rotation axis to drive. Defaults to 'rotateZ'.
        setup_name (str, optional): A name to add to create attributes and elements. Default None (no extra name)
        separator_name (str, optional): The name for the separator attribute that
                                        groups the wave controls. Defaults to 'waveControls'.
        default_amplitude (float, optional): The default value for the amplitude attribute.
        default_wavelength (float, optional): The default value for the waveLength attribute.
        default_envelope (float, optional): The default value for the default_envelope attribute.
    """
    if not controls or not all(cmds.objExists(c) for c in controls):
        logger.warning("Input is not a valid list of existing controls. Aborting.")
        return

    driver_control = controls[0]
    num_controls = len(controls)

    # --- Add Wave Attributes to Driver Control ---
    core_attr.add_separator_attr(target_object=driver_control, attr_name=separator_name)

    attributes_to_add = {
        "envelope": {
            "longName": "envelope",
            "attributeType": "float",
            "minValue": 0,
            "maxValue": 1,
            "defaultValue": default_envelope,
        },
        "amplitude": {
            "longName": "amplitude",
            "attributeType": "float",
            "defaultValue": default_amplitude,
        },
        "waveLength": {
            "longName": "waveLength",
            "attributeType": "float",
            "minValue": 0.01,
            "defaultValue": default_wavelength,
        },
        "offset": {
            "longName": "offset",
            "attributeType": "float",
            "defaultValue": 0,
        },
        "dropoff": {
            "longName": "dropoff",
            "attributeType": "float",
            "minValue": 0,
            "maxValue": 1,
            "defaultValue": 0,
        },
    }

    if setup_name is None:
        setup_name = ""

    attr_paths = {}
    for attr, properties in attributes_to_add.items():
        long_name = properties["longName"]
        if setup_name:
            long_name = f"{setup_name}{long_name.upper()}"

        if not cmds.attributeQuery(long_name, node=driver_control, exists=True):
            # Create a copy of the properties to avoid modifying the base dictionary
            new_properties = properties.copy()
            new_properties["longName"] = long_name
            cmds.addAttr(driver_control, keyable=True, **new_properties)
        attr_paths[attr] = f"{driver_control}.{long_name}"

    # --- Build Node Network ---
    time_node = cmds.createNode("time", name=f"{driver_control}_wave_time")

    for index, control in enumerate(controls):
        offset_group = core_hrchy.add_offset_transform(control, transform_suffix="wave")[0]

        wave_output_node = cmds.createNode("unitConversion", name=f"{control}_waveOutput")

        phase_offset_node = cmds.createNode("plusMinusAverage", name=f"{control}_phaseOffset")
        cmds.setAttr(f"{phase_offset_node}.input1D[0]", index)
        cmds.connectAttr(attr_paths["offset"], f"{phase_offset_node}.input1D[1]")

        wavelength_inv_node = cmds.createNode("multiplyDivide", name=f"{control}_wavelengthInv")
        cmds.setAttr(f"{wavelength_inv_node}.operation", 2)  # Divide
        cmds.setAttr(f"{wavelength_inv_node}.input1X", 1.0)
        cmds.connectAttr(attr_paths["waveLength"], f"{wavelength_inv_node}.input2X")

        expression_string = (
            f"float $twoPi = {2 * math.pi};\n"
            f"float $time = {time_node}.outTime;\n"
            f"float $phase = {phase_offset_node}.output1D;\n"
            f'float $amp = {attr_paths["amplitude"]};\n'
            f"float $freq = {wavelength_inv_node}.outputX;\n"
            f"{wave_output_node}.input = $amp * sin(($time + $phase) * $freq * $twoPi);"
        )

        cmds.expression(string=expression_string, name=f"{control}_wave_expr")

        dropoff_ramp_node = cmds.createNode("multiplyDivide", name=f"{control}_dropoffRamp")
        cmds.setAttr(f"{dropoff_ramp_node}.operation", 2)  # Divide
        cmds.setAttr(f"{dropoff_ramp_node}.input1X", float(index))
        denominator = float(num_controls - 1) if num_controls > 1 else 1.0
        cmds.setAttr(f"{dropoff_ramp_node}.input2X", denominator)

        dropoff_amount_node = cmds.createNode("multiplyDivide", name=f"{control}_dropoffAmount")
        cmds.connectAttr(attr_paths["dropoff"], f"{dropoff_amount_node}.input1X")
        cmds.connectAttr(f"{dropoff_ramp_node}.outputX", f"{dropoff_amount_node}.input2X")

        dropoff_scale_node = cmds.createNode("plusMinusAverage", name=f"{control}_dropoffScale")
        cmds.setAttr(f"{dropoff_scale_node}.operation", 2)  # Subtract
        cmds.setAttr(f"{dropoff_scale_node}.input1D[0]", 1.0)
        cmds.connectAttr(f"{dropoff_amount_node}.outputX", f"{dropoff_scale_node}.input1D[1]")

        wave_and_dropoff_node = cmds.createNode("multiplyDivide", name=f"{control}_mult_wave_dropoff")
        cmds.connectAttr(f"{wave_output_node}.output", f"{wave_and_dropoff_node}.input1X")
        cmds.connectAttr(f"{dropoff_scale_node}.output1D", f"{wave_and_dropoff_node}.input2X")

        final_value_node = cmds.createNode("multiplyDivide", name=f"{control}_mult_envelope")
        cmds.connectAttr(attr_paths["envelope"], f"{final_value_node}.input1X")
        cmds.connectAttr(f"{wave_and_dropoff_node}.outputX", f"{final_value_node}.input2X")

        cmds.connectAttr(f"{final_value_node}.outputX", f"{offset_group}.{driven_axis}")


@core_undo.undo_chunk
def import_with_offset(
    file_paths,
    group_name="imported",
    tracking_attribute=RiggingConstants.ATTR_IMPORT_OFFSET_REF,
    translate_offset=(0.0, 0.0, 0.0),
    rotate_offset=(0.0, 0.0, 0.0),
):
    """Imports 3D models, applies a baked transform offset, and organizes them.

    This function finds or creates a main, trackable container group. It uses the
    FbxImporter class for FBX files, importing them into a temporary namespace to
    prevent name clashes. A world-space transformation is applied to the new
    top-level objects before they are parented.

    Args:
        file_paths (list[str] or str): A single file path or a list of paths to import.
        group_name (str, optional): The name of the main container group to find or create.
        tracking_attribute (str, optional): The name of the boolean attribute used to identify.
        translate_offset (tuple[float], optional): The translation offset (X, Y, Z) to apply.
        rotate_offset (tuple[float], optional): The rotation offset (X, Y, Z) in degrees to apply.

    Returns:
        str or None: The name of the main container group if new nodes were successfully imported,
                     otherwise None.
    """
    # --- Ensure necessary importer plugins are loaded ---
    cmds.loadPlugin("fbxmaya.mll", quiet=True)
    cmds.loadPlugin("objExport.mll", quiet=True)

    # --- Import files and identify new nodes ---
    if not isinstance(file_paths, list):
        file_paths = [file_paths]

    imported_nodes_this_run = []
    temp_namespaces_created = set()

    file_type_map = {
        ".ma": "mayaAscii",
        ".mb": "mayaBinary",
        ".obj": "OBJ",
    }

    for file_path in file_paths:
        if not os.path.exists(file_path):
            cmds.warning(f'File path does not exist, skipping: "{file_path}"')
            continue

        file_extension = os.path.splitext(file_path)[1].lower()

        try:
            new_nodes = []
            if file_extension == ".fbx":
                # Use the specified FbxImporter class pattern
                temp_namespace = f"fbx_import_{uuid.uuid4().hex[:8]}"
                temp_namespaces_created.add(temp_namespace)

                import gt.utils.fbx as utils_fbx

                fbx_importer = utils_fbx.FbxImporter()
                with fbx_importer as fbx:
                    fbx.set_preferences_animation()
                    new_nodes = fbx.import_file(path=file_path, namespace=temp_namespace)
            else:
                # Use the original logic for other file types
                file_type = file_type_map.get(file_extension)
                if not file_type:
                    cmds.warning(f'Unsupported file type "{file_extension}" for file: {file_path}. Skipping.')
                    continue

                nodes_before = set(cmds.ls(assemblies=True))
                cmds.file(
                    file_path, i=True, type=file_type, ignoreVersion=True, mergeNamespacesOnClash=False, namespace=":"
                )
                nodes_after = set(cmds.ls(assemblies=True))
                new_nodes = list(nodes_after - nodes_before)

            if new_nodes:
                imported_nodes_this_run.extend(new_nodes)

        except Exception as error:
            cmds.warning(f'Failed to import "{file_path}". Error: {error}')
            continue

    if not imported_nodes_this_run:
        cmds.warning("Import operation completed, but no new top-level nodes were found in the scene.")
        return None

    # --- Filter for transform nodes only ---
    transform_nodes_to_modify = [node for node in imported_nodes_this_run if cmds.nodeType(node) == "transform"]

    if not transform_nodes_to_modify:
        cmds.warning("Import operation did not result in any new top-level transform nodes.")
        return None

    # --- Find or create the main container group (DEFERRED to this point) ---
    main_container_group = None
    all_transforms = cmds.ls(type="transform")
    for transform_node in all_transforms:
        if cmds.attributeQuery(tracking_attribute, node=transform_node, exists=True):
            main_container_group = transform_node
            break

    if main_container_group is None:
        main_container_group = cmds.group(empty=True, name=group_name, world=True)
        cmds.addAttr(main_container_group, longName=tracking_attribute, attributeType="bool")
        cmds.setAttr(f"{main_container_group}.{tracking_attribute}", True)
        cmds.setAttr(f"{main_container_group}.{tracking_attribute}", lock=True)
        _grp_color = core_color.ColorConstants.RGB.WHITE_LAVENDER
        core_color.set_color_outliner(obj_list=main_container_group, rgb_color=_grp_color)

    # --- Apply offset directly to imported objects, pivoting from the world origin ---
    if any(val != 0 for val in rotate_offset):
        cmds.rotate(
            rotate_offset[0],
            rotate_offset[1],
            rotate_offset[2],
            transform_nodes_to_modify,
            pivot=(0, 0, 0),
            relative=True,
            worldSpace=True,
        )

    if any(val != 0 for val in translate_offset):
        cmds.move(
            translate_offset[0],
            translate_offset[1],
            translate_offset[2],
            transform_nodes_to_modify,
            relative=True,
            worldSpace=True,
        )

    # --- Parent the transformed nodes to the main group ---
    cmds.parent(transform_nodes_to_modify, main_container_group)

    # --- Merge namespaces without adding to undo history ---
    is_undo_enabled = cmds.undoInfo(query=True, state=True)
    if is_undo_enabled:
        cmds.undoInfo(stateWithoutFlush=False)
    try:
        for namespace in temp_namespaces_created:
            if cmds.namespace(exists=namespace):
                cmds.namespace(moveNamespace=(namespace, ":"), force=True)
                cmds.namespace(removeNamespace=namespace)
    finally:
        if is_undo_enabled:
            cmds.undoInfo(stateWithoutFlush=True)

    return main_container_group


def open_import_with_offset_dialog(
    group_name="imported",
    tracking_attribute=RiggingConstants.ATTR_IMPORT_OFFSET_REF,
    translate_offset=(0.0, 0.0, 0.0),
    rotate_offset=(0.0, 0.0, 0.0),
):
    """Opens a dialog to select files and imports them using import_with_offset.

    This function provides a user interface for the import_with_offset operation.
    It prompts the user to select multiple files, sanitizes the selection to
    ensure only valid file types are used, then calls the core import function.
    Finally, it provides in-view feedback on the result.

    Args:
        group_name (str, optional): The name of the main container group to find or create.
        tracking_attribute (str, optional): The name of the boolean attribute used to identify.
        translate_offset (tuple[float], optional): The translation offset (X, Y, Z) to apply.
        rotate_offset (tuple[float], optional): The rotation offset (X, Y, Z) in degrees to apply.

    Returns:
        int: The number of valid files that were successfully imported.
    """
    _ALLOWED_EXTENSIONS = (".ma", ".mb", ".fbx", ".obj")

    # Determine dialog captions based on whether an offset is being applied
    is_translate_zero = all(v == 0.0 for v in translate_offset)
    is_rotate_zero = all(v == 0.0 for v in rotate_offset)

    if is_translate_zero and is_rotate_zero:
        dialog_caption = "Select File(s) to Import"
        dialog_ok_caption = "Import"
    else:
        dialog_caption = "Select File(s) to Import with Offset"
        dialog_ok_caption = "Import With Offset"

    # Create a file filter string from the list of allowed extensions
    extension_wildcards = " ".join([f"*{ext}" for ext in _ALLOWED_EXTENSIONS])
    file_filter = f"Supported Files ({extension_wildcards})"

    # Assume the file dialog utility returns a list of paths or None
    import gt.ui.file_dialog as ui_file_dialog

    selected_paths = ui_file_dialog.file_dialog(
        caption=dialog_caption,
        write_mode=False,
        dir_only=False,
        file_filter=file_filter,
        ok_caption=dialog_ok_caption,
        cancel_caption="Cancel",
        multiple_files=True,
    )

    if not selected_paths:
        logger.debug("Import cancelled by user.")
        return 0

    # Filter the selected paths to ensure they have a valid extension
    sanitized_paths = [path for path in selected_paths if os.path.splitext(path)[1].lower() in _ALLOWED_EXTENSIONS]

    if not sanitized_paths:
        cmds.warning("No files with valid extensions (.ma, .mb, .fbx, .obj) were selected.")
        return 0

    # Call the core import function with the sanitized list and provided arguments
    result_group = import_with_offset(
        file_paths=sanitized_paths,
        group_name=group_name,
        tracking_attribute=tracking_attribute,
        translate_offset=translate_offset,
        rotate_offset=rotate_offset,
    )

    # Provide feedback to the user if the import function succeeded
    if result_group:
        num_imported = len(sanitized_paths)
        feedback = core_fback.FeedbackMessage(
            quantity=num_imported,
            singular="file was",
            plural="files were",
            conclusion=f"imported into group '{result_group}'.",
        )
        feedback.print_inview_message()
        return num_imported

    # The underlying import_with_offset function will provide its own warnings on failure
    return 0


def find_control(target_suffix, ignore_namespace="source"):
    """
    Finds a control in the scene matching the suffix, filtering out specific namespaces.

    Args:
        target_suffix (str): The suffix of the control to find.
        ignore_namespace (str): A namespace to exclude from the search.

    Returns:
        str or None: The full path to the control if found, else None.
    """
    matches = cmds.ls(f"*:{target_suffix}", long=True) or []
    matches = [m for m in matches if f"|{ignore_namespace}:" not in m]

    if not matches and cmds.objExists(target_suffix):
        return target_suffix

    return matches[0] if matches else None


def find_joint(suffix, rig_namespace):
    """
    Finds a specific joint given the rig namespace.

    Args:
        suffix (str): The joint name suffix.
        rig_namespace (str): The namespace of the rig.

    Returns:
        str or None: The found joint name or None.
    """
    candidate = f"{rig_namespace}:{suffix}"
    if cmds.objExists(candidate):
        return candidate

    matches = cmds.ls(f"{rig_namespace}:*{suffix}", long=True)
    return matches[0] if matches else None


def find_node_by_suffix(node_name):
    """
    Tries to find a node by name, falling back to a global suffix search.

    Args:
        node_name (str): The name or suffix to search for.

    Returns:
        str or None: The found node full name.
    """
    if cmds.objExists(node_name):
        return node_name

    bare_name = node_name.split(":")[-1]
    matches = cmds.ls(f"*:{bare_name}", long=True) or []

    return matches[0] if matches else None


def snap_node(source_node, target_node, mode="position"):
    """
    Snaps a source node to a target node based on the specified mode.

    Args:
        source_node (str): The object to move.
        target_node (str): The target location.
        mode (str): 'position', 'rotation', or 'world y only'.
    """
    try:
        target_pos = cmds.xform(target_node, query=True, worldSpace=True, translation=True)
        source_pos = cmds.xform(source_node, query=True, worldSpace=True, translation=True)

        final_pos = target_pos
        if "world y only" in mode.lower():
            final_pos = [source_pos[0], target_pos[1], source_pos[2]]

        cmds.xform(source_node, worldSpace=True, translation=final_pos)

    except Exception as e:
        logger.error(f"Error snapping {source_node} to {target_node}: {e}")


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    open_import_with_offset_dialog()

    # for idx in range(1, 17):
    #     index_str = str(idx).zfill(2)
    #     mouth_controls = [
    #         f"mouth_A_{index_str}_CTRL",
    #         f"mouth_B_{index_str}_CTRL",
    #         f"mouth_C_{index_str}_CTRL",
    #         f"mouth_D_{index_str}_CTRL",
    #         f"mouth_E_{index_str}_CTRL",
    #     ]
    #
    #     create_fk_wave_setup(
    #         controls=mouth_controls,
    #         driven_axis="rotateZ",
    #         default_amplitude=15,
    #         default_wavelength=7,
    #         default_envelope=0,
    #     )
