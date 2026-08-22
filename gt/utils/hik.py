"""
HumanIK (HIK) Utilities

This module provides common functionalities for managing HumanIK character
definitions, retargeting, XML IO, and baking within Maya.

Import Line:
    import gt.utils.hik as utils_hik
"""

import json
import logging
import os
import tempfile
import xml.etree.ElementTree as ET

import maya.api.OpenMaya as om
import maya.cmds as cmds
import maya.mel as mel

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Maya's strict ordered array of HumanIK slots. 
# Required for native UI compatibility when exporting/importing XML.
HIK_CHARACTERIZE_KEYS = (
    "Reference", "Hips", "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot",
    "Spine", "LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand", "Head",
    "LeftToeBase", "RightToeBase", "LeftShoulder", "RightShoulder", "Neck", "LeftFingerBase", "RightFingerBase",
    "Spine1", "Spine2", "Spine3", "Spine4", "Spine5", "Spine6", "Spine7", "Spine8", "Spine9",
    "Neck1", "Neck2", "Neck3", "Neck4", "Neck5", "Neck6", "Neck7", "Neck8", "Neck9",
    "LeftUpLegRoll", "LeftLegRoll", "RightUpLegRoll", "RightLegRoll", "LeftArmRoll", "LeftForeArmRoll",
    "RightArmRoll", "RightForeArmRoll", "HipsTranslation",
    "LeftHandThumb1", "LeftHandThumb2", "LeftHandThumb3", "LeftHandThumb4",
    "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3", "LeftHandIndex4",
    "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3", "LeftHandMiddle4",
    "LeftHandRing1", "LeftHandRing2", "LeftHandRing3", "LeftHandRing4",
    "LeftHandPinky1", "LeftHandPinky2", "LeftHandPinky3", "LeftHandPinky4",
    "LeftHandExtraFinger1", "LeftHandExtraFinger2", "LeftHandExtraFinger3", "LeftHandExtraFinger4",
    "RightHandThumb1", "RightHandThumb2", "RightHandThumb3", "RightHandThumb4",
    "RightHandIndex1", "RightHandIndex2", "RightHandIndex3", "RightHandIndex4",
    "RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3", "RightHandMiddle4",
    "RightHandRing1", "RightHandRing2", "RightHandRing3", "RightHandRing4",
    "RightHandPinky1", "RightHandPinky2", "RightHandPinky3", "RightHandPinky4",
    "RightHandExtraFinger1", "RightHandExtraFinger2", "RightHandExtraFinger3", "RightHandExtraFinger4",
    "LeftFootThumb1", "LeftFootThumb2", "LeftFootThumb3", "LeftFootThumb4",
    "LeftFootIndex1", "LeftFootIndex2", "LeftFootIndex3", "LeftFootIndex4",
    "LeftFootMiddle1", "LeftFootMiddle2", "LeftFootMiddle3", "LeftFootMiddle4",
    "LeftFootRing1", "LeftFootRing2", "LeftFootRing3", "LeftFootRing4",
    "LeftFootPinky1", "LeftFootPinky2", "LeftFootPinky3", "LeftFootPinky4",
    "LeftFootExtraFinger1", "LeftFootExtraFinger2", "LeftFootExtraFinger3", "LeftFootExtraFinger4",
    "RightFootThumb1", "RightFootThumb2", "RightFootThumb3", "RightFootThumb4",
    "RightFootIndex1", "RightFootIndex2", "RightFootIndex3", "RightFootIndex4",
    "RightFootMiddle1", "RightFootMiddle2", "RightFootMiddle3", "RightFootMiddle4",
    "RightFootRing1", "RightFootRing2", "RightFootRing3", "RightFootRing4",
    "RightFootPinky1", "RightFootPinky2", "RightFootPinky3", "RightFootPinky4",
    "RightFootExtraFinger1", "RightFootExtraFinger2", "RightFootExtraFinger3", "RightFootExtraFinger4",
    "LeftInHandThumb", "LeftInHandIndex", "LeftInHandMiddle", "LeftInHandRing", "LeftInHandPinky", "LeftInHandExtraFinger",
    "RightInHandThumb", "RightInHandIndex", "RightInHandMiddle", "RightInHandRing", "RightInHandPinky", "RightInHandExtraFinger",
    "LeftInFootThumb", "LeftInFootIndex", "LeftInFootMiddle", "LeftInFootRing", "LeftInFootPinky", "LeftInFootExtraFinger",
    "RightInFootThumb", "RightInFootIndex", "RightInFootMiddle", "RightInFootRing", "RightInFootPinky", "RightInFootExtraFinger",
    "LeftShoulderExtra", "RightShoulderExtra",
    "LeafLeftUpLegRoll1", "LeafLeftLegRoll1", "LeafRightUpLegRoll1", "LeafRightLegRoll1",
    "LeafLeftArmRoll1", "LeafLeftForeArmRoll1", "LeafRightArmRoll1", "LeafRightForeArmRoll1",
    "LeafLeftUpLegRoll2", "LeafLeftLegRoll2", "LeafRightUpLegRoll2", "LeafRightLegRoll2",
    "LeafLeftArmRoll2", "LeafLeftForeArmRoll2", "LeafRightArmRoll2", "LeafRightForeArmRoll2",
    "LeafLeftUpLegRoll3", "LeafLeftLegRoll3", "LeafRightUpLegRoll3", "LeafRightLegRoll3",
    "LeafLeftArmRoll3", "LeafLeftForeArmRoll3", "LeafRightArmRoll3", "LeafRightForeArmRoll3",
    "LeafLeftUpLegRoll4", "LeafLeftLegRoll4", "LeafRightUpLegRoll4", "LeafRightLegRoll4",
    "LeafLeftArmRoll4", "LeafLeftForeArmRoll4", "LeafRightArmRoll4", "LeafRightForeArmRoll4",
    "LeafLeftUpLegRoll5", "LeafLeftLegRoll5", "LeafRightUpLegRoll5", "LeafRightLegRoll5",
    "LeafLeftArmRoll5", "LeafLeftForeArmRoll5", "LeafRightArmRoll5", "LeafRightForeArmRoll5"
)

HIK_PROPERTY_NODE_TYPE = "HIKProperty2State"
HIK_PROPERTY_EXCLUDED_ATTRIBUTES = {
    "message",
    "caching",
    "frozen",
    "isHistoricallyInteresting",
    "nodeState",
    "binMembership",
    "OutputPropertySetState",
}
HIK_PROPERTY_SUPPORTED_TYPES = {
    "bool",
    "byte",
    "char",
    "short",
    "long",
    "enum",
    "float",
    "double",
    "doubleAngle",
    "doubleLinear",
    "string",
}
HIK_POSE_FILE_FORMAT = "gt_hik_pose"
HIK_POSE_FILE_VERSION = 1
HIK_TRANSFORM_ATTRIBUTES = {
    "translateX",
    "translateY",
    "translateZ",
    "rotateX",
    "rotateY",
    "rotateZ",
    "scaleX",
    "scaleY",
    "scaleZ",
    "tx",
    "ty",
    "tz",
    "rx",
    "ry",
    "rz",
    "sx",
    "sy",
    "sz",
    "visibility",
}
HIK_EFFECTOR_POSE_ATTRIBUTES = {
    "pinning",
    "pinT",
    "pinR",
    "pivotOffsetX",
    "pivotOffsetY",
    "pivotOffsetZ",
    "reachTranslation",
    "reachRotation",
}
HIK_FOOT_CHANNEL_MIRROR_IDS = {
    "Foot",
    "AnkleEffector",
}
HIK_MIRRORED_CHANNEL_MULTIPLIERS = {
    "tx": -1,
    "ty": 1,
    "tz": 1,
    "rx": -1,
    "ry": -1,
    "rz": 1,
    "sx": 1,
    "sy": 1,
    "sz": 1,
}


def _source_mel_procedure(proc_name):
    """
    Dynamically hunts down and sources the internal Maya MEL script containing the 
    specified procedure by recursively scanning the Maya installation directory.
    Bypasses version-specific naming changes and folder structures.

    Args:
        proc_name (str): The name of the MEL procedure to search for.

    Returns:
        bool: True if successfully found and sourced, False otherwise.
    """
    try:
        if mel.eval(f'exists "{proc_name}"'):
            return True
            
        maya_location = os.environ.get("MAYA_LOCATION", "")
        if not maya_location:
            maya_location = os.path.dirname(os.path.dirname(cmds.about(ext=True)))
            
        search_dirs = [
            os.path.join(maya_location, "scripts"),
            os.path.join(maya_location, "plug-ins")
        ]
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                continue
                
            for root, _, files in os.walk(search_dir):
                for f in files:
                    if f.endswith(".mel"):
                        file_path = os.path.join(root, f)
                        try:
                            with open(file_path, "r", encoding="utf-8", errors="ignore") as file_content:
                                if f"proc {proc_name}" in file_content.read():
                                    file_path_f = file_path.replace("\\", "/")
                                    mel.eval(f'source "{file_path_f}"')
                                    logger.debug(f'Successfully sourced MEL script for {proc_name}: {file_path_f}')
                                    return True
                        except Exception:
                            continue
                            
    except Exception as e:
        logger.debug(f'Error dynamically sourcing script for {proc_name}. Issue: {e}')
    
    return False


def get_hik_characters():
    """
    Retrieves a list of all HumanIK character nodes in the scene.

    Returns:
        list: A list of HIKCharacterNode names.
    """
    return cmds.ls(type="HIKCharacterNode") or []


def get_hik_property_node(character_node, create_if_missing=False):
    """Gets the property-state node associated with a HumanIK character.

    Args:
        character_node (str): HumanIK character node.
        create_if_missing (bool, optional): Create and connect a property node
            when the character does not already have one.

    Returns:
        str: HIKProperty2State node, or an empty string when unavailable.
    """
    if not cmds.objExists(character_node) or cmds.nodeType(character_node) != "HIKCharacterNode":
        logger.warning(f'Invalid HumanIK character node: "{character_node}".')
        return ""
    property_plug = f"{character_node}.propertyState"
    property_nodes = cmds.listConnections(
        property_plug,
        source=True,
        destination=False,
        type=HIK_PROPERTY_NODE_TYPE,
    ) or []
    if not property_nodes:
        property_nodes = cmds.listConnections(
            character_node,
            source=True,
            destination=True,
            type=HIK_PROPERTY_NODE_TYPE,
        ) or []
    if property_nodes:
        return property_nodes[0]
    if not create_if_missing:
        return ""

    property_name = f"{character_node.rpartition(':')[-1]}_properties"
    property_node = cmds.createNode(HIK_PROPERTY_NODE_TYPE, name=property_name)
    cmds.connectAttr(f"{property_node}.OutputPropertySetState", property_plug, force=True)
    logger.info(f'Created HumanIK property node "{property_node}" for "{character_node}".')
    return property_node


def get_hik_properties(character_node):
    """Gets serializable retarget properties for a HumanIK character.

    Args:
        character_node (str): HumanIK character node.

    Returns:
        dict: Writable HumanIK property names and values.
    """
    property_node = get_hik_property_node(character_node)
    if not property_node:
        logger.warning(f'No HumanIK property node found for "{character_node}".')
        return {}
    properties = {}
    for attribute_name in cmds.listAttr(property_node, settable=True) or []:
        if attribute_name in HIK_PROPERTY_EXCLUDED_ATTRIBUTES:
            continue
        plug = f"{property_node}.{attribute_name}"
        try:
            attribute_type = cmds.getAttr(plug, type=True)
            if attribute_type not in HIK_PROPERTY_SUPPORTED_TYPES:
                continue
            value = cmds.getAttr(plug)
            if value is not None:
                properties[attribute_name] = value
        except Exception as exception:
            logger.debug(f'Unable to read HumanIK property "{plug}". Issue: {exception}')
    return properties


def set_hik_properties(character_node, properties, create_if_missing=False):
    """Sets retarget properties on a HumanIK character.

    Unknown, locked, connected, and unsupported properties are skipped so data
    exported by a different Maya version can still be applied safely.

    Args:
        character_node (str): HumanIK character node.
        properties (dict): Property names mapped to JSON-compatible values.
        create_if_missing (bool, optional): Create the HIK property node when absent.

    Returns:
        dict: Property names and values successfully applied.
    """
    if not isinstance(properties, dict):
        logger.warning("HumanIK properties must be provided as a dictionary.")
        return {}
    property_node = get_hik_property_node(character_node, create_if_missing=create_if_missing)
    if not property_node:
        logger.warning(f'No HumanIK property node found for "{character_node}".')
        return {}
    applied_properties = {}
    for attribute_name, value in properties.items():
        if attribute_name in HIK_PROPERTY_EXCLUDED_ATTRIBUTES:
            continue
        if not cmds.attributeQuery(attribute_name, node=property_node, exists=True):
            logger.debug(f'Unknown HumanIK property skipped: "{attribute_name}".')
            continue
        plug = f"{property_node}.{attribute_name}"
        try:
            attribute_type = cmds.getAttr(plug, type=True)
            if attribute_type not in HIK_PROPERTY_SUPPORTED_TYPES or not cmds.getAttr(plug, settable=True):
                continue
            if attribute_type == "string":
                cmds.setAttr(plug, "" if value is None else str(value), type="string")
            else:
                cmds.setAttr(plug, value)
            applied_properties[attribute_name] = cmds.getAttr(plug)
        except Exception as exception:
            logger.warning(f'Unable to set HumanIK property "{plug}". Issue: {exception}')
    try:
        cmds.dgdirty(property_node)
        cmds.refresh(force=True)
    except Exception:
        pass
    return applied_properties


def create_definition(character_name="Character"):
    """
    Creates a new HumanIK character definition. 

    Args:
        character_name (str): The desired name for the new character definition.

    Returns:
        str: The name of the created HIK character node.
    """
    try:
        if not cmds.pluginInfo("mayaHIK", query=True, loaded=True):
            cmds.loadPlugin("mayaHIK")

        mel.eval(f'hikCreateCharacter("{character_name}")')
        logger.info(f'Created HIK character definition: "{character_name}"')
        return character_name
    except Exception as e:
        logger.error(f'Failed to create character definition. Issue: {e}')
        return ""


def rename_definition(character_node, new_name):
    """
    Renames an existing HumanIK character definition and updates the HIK UI.

    Args:
        character_node (str): The current name of the HIK character node.
        new_name (str): The new name for the definition.

    Returns:
        str: The newly renamed node string, or empty string if it failed.
    """
    if not cmds.objExists(character_node):
        logger.warning(f'Cannot rename. Node "{character_node}" does not exist.')
        return ""

    renamed_node = cmds.rename(character_node, new_name)
    
    try:
        mel.eval('hikUpdateCharacterList()')
    except Exception:
        pass
    
    return renamed_node


def set_definition_lock(character_node, lock_state=True):
    """Locks or unlocks a HumanIK character definition.

    Args:
        character_node (str): HumanIK character definition node.
        lock_state (bool): Whether the definition should be locked.
    """
    """
    Locks or unlocks a HumanIK character definition.
    Safely simulates the exact native MEL UI button click to ensure all 
    hidden C++ retargeting validations are triggered.
    """
    if not cmds.objExists(character_node):
        logger.warning(f'Node "{character_node}" does not exist.')
        return False

    state_int = 1 if lock_state else 0
    lock_plug = f"{character_node}.InputCharacterizationLock"

    if not cmds.objExists(lock_plug):
        return False

    current_state = cmds.getAttr(lock_plug)
    if current_state == state_int:
        return True  # Already in the correct state

    try:
        # 1. Prep UI and set current character
        mel.eval('source "hikGlobalUtils.mel"')
        try:
            mel.eval('source "hikDefinitionOperations.mel"')
        except Exception:
            pass
            
        mel.eval(f'hikSetCurrentCharacter("{character_node}")')

        # 2. Fire the exact procedure the lock button uses
        mel.eval('if (exists("hikToggleLockDefinition")) { hikToggleLockDefinition(); }')

    except Exception as e:
        logger.debug(f'Native MEL lock toggle failed: {e}')

    # 3. Fallback and enforcement
    final_state = cmds.getAttr(lock_plug)
    if final_state != state_int:
        cmds.setAttr(lock_plug, state_int)

    # 4. FORCE EVALUATION
    current_time = cmds.currentTime(query=True)
    cmds.currentTime(current_time)
    cmds.refresh(force=True)

    state_str = "Locked" if lock_state else "Unlocked"
    logger.info(f'{state_str} character definition: "{character_node}"')
    return True


def set_definition_source(target_character, source_character=None):
    """
    Assigns a retargeting source to a target HumanIK character definition.
    This uses the core batch-processing MEL commands to safely bypass 
    UI namespace bugs and automatically build the HIKRetargeterNode graph.

    Args:
        target_character (str): The character definition that will receive animation.
        source_character (str, optional): The character definition to drive the target. 
                                          If None, source is cleared (set to Stance).
    
    Returns:
        bool: True if successful, False otherwise.
    """
    if not cmds.objExists(target_character):
        logger.warning(f'Target character "{target_character}" does not exist.')
        return False

    if cmds.nodeType(target_character) != "HIKCharacterNode":
        logger.warning(f'"{target_character}" is not a valid HIKCharacterNode.')
        return False

    try:
        if not cmds.pluginInfo("mayaHIK", query=True, loaded=True):
            cmds.loadPlugin("mayaHIK")

        if not source_character:
            mel.eval(f'mayaHIKsetStanceInput("{target_character}")')
            logger.info(f'Cleared source for "{target_character}".')
        else:
            if not cmds.objExists(source_character):
                logger.warning(f'Source character "{source_character}" does not exist.')
                return False
                
            if cmds.nodeType(source_character) != "HIKCharacterNode":
                logger.warning(f'"{source_character}" is not a valid HIKCharacterNode.')
                return False
            
            mel.eval(f'mayaHIKsetCharacterInput("{target_character}", "{source_character}")')
            logger.info(f'Assigned "{source_character}" as source for "{target_character}".')

        try:
            mel.eval('hikUpdateSourceList()')
            mel.eval('hikUpdateContextualUI()')
        except Exception:
            pass

        return True
    except Exception as e:
        logger.error(f'Failed to set source. Issue: {e}')
        return False


def delete_unused_definitions():
    """
    Finds and deletes any HIK character definitions that have no skeleton bones 
    assigned to them (unused/empty definitions).

    Returns:
        list: A list of deleted character definition names.
    """
    deleted_nodes = []
    hik_nodes = get_hik_characters()
    
    for node in hik_nodes:
        connected_bones = cmds.listConnections(node, source=True, destination=False, type="transform")
        if not connected_bones:
            cmds.delete(node)
            deleted_nodes.append(node)
            
    if deleted_nodes:
        logger.info(f'Deleted unused HIK definitions: {deleted_nodes}')
        try:
            mel.eval('hikUpdateCharacterList()')
        except Exception:
            pass
            
    return deleted_nodes


def get_character_namespace(character_node):
    """
    Attempts to retrieve the namespace of the skeleton assigned to the HIK character.

    Args:
        character_node (str): The HIK character node to evaluate.

    Returns:
        str: The namespace of the associated skeleton (e.g., "Char_A"), or empty 
             string if no namespace is found.
    """
    if not cmds.objExists(character_node):
        return ""

    connected_bones = cmds.listConnections(character_node, source=True, destination=False, type="transform")
    if connected_bones:
        first_bone = connected_bones[0]
        if ":" in first_bone:
            return first_bone.rpartition(":")[0]
            
    if ":" in character_node:
        return character_node.rpartition(":")[0]
        
    return ""


def _resolve_hik_character(character_node):
    """Resolves a HumanIK character name, including a unique namespaced match.

    Args:
        character_node (str): Character node name or unqualified character name.

    Returns:
        str: Resolved HIKCharacterNode name, or an empty string when unresolved.
    """
    if not isinstance(character_node, str) or not character_node.strip():
        logger.warning("A HumanIK character name is required.")
        return ""

    requested_name = character_node.strip().lstrip(":")
    if cmds.objExists(requested_name):
        try:
            if cmds.nodeType(requested_name) == "HIKCharacterNode":
                return requested_name
        except Exception:
            pass

    matches = cmds.ls(requested_name, type="HIKCharacterNode") or []
    if ":" not in requested_name:
        namespaced_matches = cmds.ls(f"*:{requested_name}", type="HIKCharacterNode") or []
        matches.extend(namespaced_matches)
    matches = sorted(set(matches))

    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        logger.warning(
            f'HumanIK character name "{character_node}" is ambiguous. '
            f"Use a namespace-qualified name. Matches: {matches}"
        )
    else:
        logger.warning(f'HumanIK character "{character_node}" was not found.')
    return ""


def get_hik_control_rig(character_node):
    """Gets the control-set node associated with a HumanIK character.

    Args:
        character_node (str): HumanIK character node or unique character name.

    Returns:
        str: HIKControlSetNode name, or an empty string when unavailable.
    """
    resolved_character = _resolve_hik_character(character_node)
    if not resolved_character:
        return ""

    control_rigs = cmds.listConnections(
        resolved_character,
        source=True,
        destination=True,
        type="HIKControlSetNode",
    ) or []
    if control_rigs:
        return control_rigs[0]

    expected_control_rig = f"{resolved_character}_ControlRig"
    if cmds.objExists(expected_control_rig):
        try:
            if cmds.nodeType(expected_control_rig) == "HIKControlSetNode":
                return expected_control_rig
        except Exception:
            pass
    return ""


def _get_node_from_plug(plug):
    """Gets the node portion of a Maya plug string.

    Args:
        plug (str): Maya plug such as ``node.attribute``.

    Returns:
        str: Node name without its attribute.
    """
    if not isinstance(plug, str):
        return ""
    return plug.rpartition(".")[0]


def _is_transform_node(node):
    """Checks whether a Maya node derives from a transform.

    Args:
        node (str): Maya node name.

    Returns:
        bool: True when the node is a transform-derived DAG node.
    """
    if not node or not cmds.objExists(node):
        return False
    try:
        return bool(cmds.objectType(node, isAType="transform"))
    except Exception:
        return False


def _get_hik_control_map(character_node):
    """Builds stable HumanIK control identifiers mapped to scene controls.

    Control-set attribute names are used as identifiers so the map remains
    portable across character names and namespaces. A generated-name fallback
    keeps discovery available when a damaged rig is missing graph connections.

    Args:
        character_node (str): HumanIK character node or unique character name.

    Returns:
        dict: Control identifiers mapped to long DAG paths.
    """
    resolved_character = _resolve_hik_character(character_node)
    if not resolved_character:
        return {}

    control_map = {}
    control_rig = get_hik_control_rig(resolved_character)
    if control_rig:
        connections = cmds.listConnections(
            control_rig,
            source=True,
            destination=False,
            connections=True,
            plugs=True,
        ) or []
        for index in range(0, len(connections) - 1, 2):
            first_plug = connections[index]
            second_plug = connections[index + 1]
            first_node = _get_node_from_plug(first_plug)
            second_node = _get_node_from_plug(second_plug)

            if first_node == control_rig:
                control_plug = first_plug
                source_node = second_node
            elif second_node == control_rig:
                control_plug = second_plug
                source_node = first_node
            else:
                continue
            if not _is_transform_node(source_node):
                continue

            control_id = control_plug.partition(".")[2]
            long_names = cmds.ls(source_node, long=True) or []
            if control_id and long_names:
                control_map[control_id] = long_names[0]

    control_prefix = f"{resolved_character}_Ctrl_"
    generated_controls = cmds.ls(f"{control_prefix}*", long=True) or []
    connected_controls = set(control_map.values())
    for control in generated_controls:
        if not _is_transform_node(control):
            continue
        if control in connected_controls:
            continue
        short_name = control.rpartition("|")[2]
        if not short_name.startswith(control_prefix):
            continue
        control_id = short_name[len(control_prefix) :]
        if control_id:
            control_map.setdefault(control_id, control)
            connected_controls.add(control)
    return control_map


def get_hik_control_rig_controls(character_node):
    """Finds all generated FK and IK controls for a HumanIK character.

    Discovery uses the HIKControlSetNode connections and therefore includes
    mapped fingers, toes, extra fingers, extra toes, and auxiliary effectors.
    Generated control names are used as a fallback when connections are absent.

    Args:
        character_node (str): HumanIK character node or unique character name.

    Returns:
        list: Long DAG paths for all discovered control-rig controls.
    """
    control_map = _get_hik_control_map(character_node)
    if not control_map:
        logger.warning(f'No HumanIK control-rig controls found for "{character_node}".')
        return []
    return [control_map[control_id] for control_id in sorted(control_map)]


def _get_hik_control_groups(control_map):
    """Separates HumanIK controls into mirrored pairs and center controls.

    Args:
        control_map (dict): Control identifiers mapped to scene controls.

    Returns:
        tuple: Paired ``(left_id, right_id)`` entries and center identifiers.
    """
    pairs = []
    center_ids = []
    for control_id in sorted(control_map):
        if "Left" in control_id:
            right_id = control_id.replace("Left", "Right", 1)
            if right_id in control_map:
                pairs.append((control_id, right_id))
        elif "Right" not in control_id:
            center_ids.append(control_id)
    return pairs, center_ids


def _get_hik_pose_attributes(control):
    """Captures keyable and HIK effector attributes not represented by a matrix.

    Args:
        control (str): HumanIK control node.

    Returns:
        dict: Attribute names mapped to scalar JSON-compatible values.
    """
    attributes = {}
    attribute_names = set(cmds.listAttr(control, keyable=True) or [])
    for attribute_name in HIK_EFFECTOR_POSE_ATTRIBUTES:
        if cmds.attributeQuery(attribute_name, node=control, exists=True):
            attribute_names.add(attribute_name)
    for attribute_name in sorted(attribute_names):
        if attribute_name in HIK_TRANSFORM_ATTRIBUTES:
            continue
        plug = f"{control}.{attribute_name}"
        try:
            value = cmds.getAttr(plug)
        except Exception as exception:
            logger.debug(f'Unable to read HumanIK pose attribute "{plug}". Issue: {exception}')
            continue
        if isinstance(value, (bool, int, float, str)):
            attributes[attribute_name] = value
    return attributes


def _capture_hik_pose(control_map, world_space=False):
    """Captures matrices and custom pose attributes for HumanIK controls.

    Args:
        control_map (dict): Control identifiers mapped to scene controls.
        world_space (bool): Whether matrices should be captured in world space.

    Returns:
        dict: Control identifiers mapped to matrix and attribute data.
    """
    pose_data = {}
    for control_id, control in control_map.items():
        try:
            if world_space:
                matrix = cmds.xform(control, query=True, matrix=True, worldSpace=True)
            else:
                matrix = cmds.xform(control, query=True, matrix=True, objectSpace=True)
        except Exception as exception:
            logger.warning(f'Unable to capture HumanIK control "{control}". Issue: {exception}')
            continue
        pose_data[control_id] = {
            "matrix": [float(value) for value in matrix],
            "channels": _get_hik_transform_channels(control),
            "attributes": _get_hik_pose_attributes(control),
        }
    return pose_data


def _get_hik_transform_channels(control):
    """Captures local transform channels from a HumanIK control.

    Args:
        control (str): HumanIK control node.

    Returns:
        dict: Available translate, rotate, and scale channel values.
    """
    channels = {}
    for attribute_name in HIK_MIRRORED_CHANNEL_MULTIPLIERS:
        plug = f"{control}.{attribute_name}"
        if not cmds.objExists(plug):
            continue
        try:
            channels[attribute_name] = cmds.getAttr(plug)
        except Exception as exception:
            logger.debug(f'Unable to read HumanIK transform channel "{plug}". Issue: {exception}')
    return channels


def _get_hik_side_base_id(control_id):
    """Gets a side-independent HumanIK identifier without its array index.

    Args:
        control_id (str): Stable HumanIK control-set identifier.

    Returns:
        str: Identifier with the first Left or Right token removed.
    """
    base_id = control_id.partition("[")[0]
    if "Left" in base_id:
        return base_id.replace("Left", "", 1)
    if "Right" in base_id:
        return base_id.replace("Right", "", 1)
    return base_id


def _uses_hik_foot_channel_mirror(control_id):
    """Checks whether a HumanIK control requires channel-safe mirroring.

    Args:
        control_id (str): Stable HumanIK control-set identifier.

    Returns:
        bool: True for generated foot and ankle controls.
    """
    return _get_hik_side_base_id(control_id) in HIK_FOOT_CHANNEL_MIRROR_IDS


def _mirror_hik_transform_channels(channels):
    """Mirrors local channels using HumanIK lower-limb axis conventions.

    Args:
        channels (dict): Local translate, rotate, and scale channel values.

    Returns:
        dict: Mirrored channel values.
    """
    if not isinstance(channels, dict):
        return {}
    mirrored_channels = {}
    for attribute_name, multiplier in HIK_MIRRORED_CHANNEL_MULTIPLIERS.items():
        if attribute_name in channels:
            mirrored_channels[attribute_name] = channels[attribute_name] * multiplier
    return mirrored_channels


def _mirror_transform_matrix(matrix, reference_matrix=None):
    """Mirrors a transform matrix across the X axis.

    When a reference matrix is supplied, its YZ plane becomes the mirror plane.
    This allows world-space HumanIK poses to mirror around the character rather
    than around the Maya world origin.

    Args:
        matrix (list): Flat 16-value Maya transform matrix.
        reference_matrix (list, optional): World matrix defining the mirror plane.

    Returns:
        list: Mirrored flat 16-value matrix.
    """
    source_matrix = om.MMatrix(matrix)
    reflection_matrix = om.MMatrix(
        [
            -1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ]
    )
    if reference_matrix:
        reference = om.MMatrix(reference_matrix)
        source_matrix = source_matrix * reference.inverse()
        mirrored_matrix = reflection_matrix * source_matrix * reflection_matrix
        return list(mirrored_matrix * reference)
    return list(reflection_matrix * source_matrix * reflection_matrix)


def _build_mirrored_hik_control_data(target_id, source_data, reference_matrix=None):
    """Builds mirrored pose data for one HumanIK target control.

    Generated HIK foot and ankle controls use adjusted local rotation axes.
    Those controls receive mirrored channels to avoid Maya decomposing a matrix
    into unstable Euler values.

    Args:
        target_id (str): Stable identifier for the target HumanIK control.
        source_data (dict): Captured source matrix, channels, and attributes.
        reference_matrix (list, optional): World matrix defining the mirror plane.

    Returns:
        dict: Mirrored pose data ready to apply to the target control.
    """
    mirrored_data = {
        "matrix": _mirror_transform_matrix(
            source_data.get("matrix"),
            reference_matrix=reference_matrix,
        ),
        "attributes": dict(source_data.get("attributes", {})),
    }
    if _uses_hik_foot_channel_mirror(target_id):
        mirrored_data["channels"] = _mirror_hik_transform_channels(
            source_data.get("channels", {}),
        )
        mirrored_data["apply_channels"] = True
    return mirrored_data


def _set_hik_pose_attributes(control, attributes):
    """Applies writable custom pose attributes to a HumanIK control.

    Args:
        control (str): Target HumanIK control.
        attributes (dict): Attribute names mapped to scalar values.

    Returns:
        bool: True when at least one custom attribute was applied.
    """
    applied = False
    if not isinstance(attributes, dict):
        return applied
    for attribute_name, value in attributes.items():
        if attribute_name in HIK_TRANSFORM_ATTRIBUTES:
            continue
        if not cmds.attributeQuery(attribute_name, node=control, exists=True):
            continue
        plug = f"{control}.{attribute_name}"
        try:
            if not cmds.getAttr(plug, settable=True):
                continue
            if cmds.getAttr(plug, type=True) == "string":
                cmds.setAttr(plug, "" if value is None else str(value), type="string")
            else:
                cmds.setAttr(plug, value)
            applied = True
        except Exception as exception:
            logger.debug(f'Unable to set HumanIK pose attribute "{plug}". Issue: {exception}')
    return applied


def _set_hik_transform_channels(control, channels):
    """Applies writable local transform channels to a HumanIK control.

    Args:
        control (str): Target HumanIK control.
        channels (dict): Transform channel names mapped to values.

    Returns:
        bool: True when at least one transform channel was applied.
    """
    applied = False
    if not isinstance(channels, dict):
        return applied
    for attribute_name in HIK_MIRRORED_CHANNEL_MULTIPLIERS:
        if attribute_name not in channels:
            continue
        plug = f"{control}.{attribute_name}"
        if not cmds.objExists(plug):
            continue
        try:
            if not cmds.getAttr(plug, settable=True):
                continue
            cmds.setAttr(plug, channels[attribute_name])
            applied = True
        except Exception as exception:
            logger.debug(f'Unable to set HumanIK transform channel "{plug}". Issue: {exception}')
    return applied


def _get_control_depth(control):
    """Gets the DAG depth of a HumanIK control.

    Args:
        control (str): HumanIK control node.

    Returns:
        int: Number of DAG separators in the control's long path.
    """
    long_names = cmds.ls(control, long=True) or []
    if not long_names:
        return 0
    return long_names[0].count("|")


def _apply_hik_pose_data(control_map, pose_data, world_space, chunk_name, prefer_channels=False):
    """Applies captured pose data in hierarchy order inside an undo chunk.

    Args:
        control_map (dict): Control identifiers mapped to target controls.
        pose_data (dict): Control identifiers mapped to matrix and attributes.
        world_space (bool): Whether matrices should be applied in world space.
        chunk_name (str): Maya undo chunk label.
        prefer_channels (bool): Apply stored local channels instead of matrices
            when channel data is available.

    Returns:
        list: Controls that received matrix or custom attribute data.
    """
    applied_controls = []
    target_ids = [control_id for control_id in pose_data if control_id in control_map]
    target_ids.sort(key=lambda control_id: _get_control_depth(control_map[control_id]))
    undo_chunk_open = False
    try:
        cmds.undoInfo(openChunk=True, chunkName=chunk_name)
        undo_chunk_open = True
        for control_id in target_ids:
            control = control_map[control_id]
            control_data = pose_data.get(control_id)
            if not isinstance(control_data, dict):
                continue
            matrix = control_data.get("matrix")
            use_channels = bool(control_data.get("apply_channels") or prefer_channels)
            transform_applied = False
            if use_channels and control_data.get("channels"):
                transform_applied = _set_hik_transform_channels(
                    control,
                    control_data.get("channels"),
                )
            elif isinstance(matrix, (list, tuple)) and len(matrix) == 16:
                try:
                    if world_space:
                        cmds.xform(control, matrix=matrix, worldSpace=True)
                    else:
                        cmds.xform(control, matrix=matrix, objectSpace=True)
                    transform_applied = True
                except Exception as exception:
                    logger.warning(f'Unable to apply HumanIK pose to "{control}". Issue: {exception}')
            attributes_applied = _set_hik_pose_attributes(
                control,
                control_data.get("attributes", {}),
            )
            if transform_applied or attributes_applied:
                applied_controls.append(control)
    finally:
        if undo_chunk_open:
            cmds.undoInfo(closeChunk=True, chunkName=chunk_name)
    return applied_controls


def mirror_hik_pose(character_node, source_side="left", affect_center=False, world_space=False):
    """Mirrors one side of a HumanIK control-rig pose onto the other side.

    Side pairs come directly from HIK control-set identifiers, so all mapped
    fingers, toes, extra digits, and auxiliary effectors are included. In world
    space, the character Reference control defines the mirror plane when present.

    Args:
        character_node (str): HumanIK character node or unique character name.
        source_side (str): Side to copy from. Accepted values are ``left`` and
            ``right``.
        affect_center (bool): Whether center controls should mirror in place.
        world_space (bool): Use world matrices when True or local matrices when
            False.

    Returns:
        list: Controls successfully modified by the mirror operation.

    Raises:
        ValueError: If ``source_side`` is not ``left`` or ``right``.
    """
    normalized_side = str(source_side).strip().lower()
    if normalized_side not in {"left", "right"}:
        raise ValueError('source_side must be either "left" or "right".')

    control_map = _get_hik_control_map(character_node)
    if not control_map:
        logger.warning(f'No HumanIK control-rig controls found for "{character_node}".')
        return []
    control_pairs, center_ids = _get_hik_control_groups(control_map)
    captured_pose = _capture_hik_pose(control_map, world_space=world_space)
    reference_matrix = None
    if world_space and "Reference" in captured_pose:
        reference_matrix = captured_pose["Reference"].get("matrix")

    mirrored_pose = {}
    for left_id, right_id in control_pairs:
        source_id = left_id if normalized_side == "left" else right_id
        target_id = right_id if normalized_side == "left" else left_id
        source_data = captured_pose.get(source_id)
        if not source_data:
            continue
        mirrored_pose[target_id] = _build_mirrored_hik_control_data(
            target_id,
            source_data,
            reference_matrix=reference_matrix,
        )

    if affect_center:
        for control_id in center_ids:
            source_data = captured_pose.get(control_id)
            if not source_data:
                continue
            mirrored_pose[control_id] = {
                "matrix": _mirror_transform_matrix(
                    source_data.get("matrix"),
                    reference_matrix=reference_matrix,
                ),
                "attributes": dict(source_data.get("attributes", {})),
            }

    if not mirrored_pose:
        logger.warning(f'No mirrorable HumanIK control pairs found for "{character_node}".')
        return []
    return _apply_hik_pose_data(
        control_map,
        mirrored_pose,
        world_space=world_space,
        chunk_name="Mirror HumanIK Pose",
    )


def flip_hik_pose(character_node, affect_center=False, world_space=False):
    """Flips a HumanIK pose by swapping and mirroring its left and right sides.

    Args:
        character_node (str): HumanIK character node or unique character name.
        affect_center (bool): Whether center controls should mirror in place.
        world_space (bool): Use world matrices when True or local matrices when
            False.

    Returns:
        list: Controls successfully modified by the flip operation.
    """
    control_map = _get_hik_control_map(character_node)
    if not control_map:
        logger.warning(f'No HumanIK control-rig controls found for "{character_node}".')
        return []
    control_pairs, center_ids = _get_hik_control_groups(control_map)
    captured_pose = _capture_hik_pose(control_map, world_space=world_space)
    reference_matrix = None
    if world_space and "Reference" in captured_pose:
        reference_matrix = captured_pose["Reference"].get("matrix")

    flipped_pose = {}
    for left_id, right_id in control_pairs:
        left_data = captured_pose.get(left_id)
        right_data = captured_pose.get(right_id)
        if not left_data or not right_data:
            continue
        flipped_pose[left_id] = _build_mirrored_hik_control_data(
            left_id,
            right_data,
            reference_matrix=reference_matrix,
        )
        flipped_pose[right_id] = _build_mirrored_hik_control_data(
            right_id,
            left_data,
            reference_matrix=reference_matrix,
        )

    if affect_center:
        for control_id in center_ids:
            source_data = captured_pose.get(control_id)
            if not source_data:
                continue
            flipped_pose[control_id] = {
                "matrix": _mirror_transform_matrix(
                    source_data.get("matrix"),
                    reference_matrix=reference_matrix,
                ),
                "attributes": dict(source_data.get("attributes", {})),
            }

    if not flipped_pose:
        logger.warning(f'No flippable HumanIK control pairs found for "{character_node}".')
        return []
    return _apply_hik_pose_data(
        control_map,
        flipped_pose,
        world_space=world_space,
        chunk_name="Flip HumanIK Pose",
    )


def export_hik_pose(character_node, file_path, world_space=False):
    """Exports a HumanIK control-rig pose to a JSON file.

    Stable HIK identifiers are stored instead of character-specific node names,
    allowing the pose to be imported onto another character or namespace.

    Args:
        character_node (str): HumanIK character node or unique character name.
        file_path (str): Destination JSON or pose file path.
        world_space (bool): Store world matrices when True or local matrices when
            False.

    Returns:
        bool: True when the pose file was written successfully.
    """
    if not isinstance(file_path, str) or not file_path.strip():
        logger.warning("A HumanIK pose output path is required.")
        return False
    resolved_character = _resolve_hik_character(character_node)
    if not resolved_character:
        return False
    control_map = _get_hik_control_map(resolved_character)
    if not control_map:
        logger.warning(f'No HumanIK control-rig controls found for "{character_node}".')
        return False

    absolute_path = os.path.abspath(file_path)
    output_directory = os.path.dirname(absolute_path)
    if not os.path.isdir(output_directory):
        logger.warning(f'HumanIK pose output directory does not exist: "{output_directory}".')
        return False

    file_data = {
        "format": HIK_POSE_FILE_FORMAT,
        "version": HIK_POSE_FILE_VERSION,
        "character": resolved_character.rpartition(":")[2],
        "world_space": bool(world_space),
        "controls": _capture_hik_pose(control_map, world_space=world_space),
    }
    temporary_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=output_directory,
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = temporary_file.name
            json.dump(file_data, temporary_file, indent=4, sort_keys=True)
            temporary_file.write("\n")
        os.replace(temporary_path, absolute_path)
        logger.info(f'Exported HumanIK pose to "{absolute_path}".')
        return True
    except Exception as exception:
        logger.error(f'Unable to export HumanIK pose to "{absolute_path}". Issue: {exception}')
        return False
    finally:
        if temporary_path and os.path.exists(temporary_path):
            try:
                os.remove(temporary_path)
            except OSError:
                pass


def import_hik_pose(character_node, file_path, world_space=None):
    """Imports a JSON HumanIK pose onto a generated control rig.

    The stored coordinate space is used by default. Passing ``world_space``
    explicitly allows callers to override how the stored matrices are applied.

    Args:
        character_node (str): HumanIK character node or unique character name.
        file_path (str): Source pose file path.
        world_space (bool, optional): Override the coordinate space stored in the
            file. True applies world matrices and False applies local matrices.

    Returns:
        list: Controls successfully modified by the imported pose.
    """
    if not isinstance(file_path, str) or not os.path.isfile(file_path):
        logger.warning(f'HumanIK pose file does not exist: "{file_path}".')
        return []
    try:
        with open(file_path, "r", encoding="utf-8") as pose_file:
            file_data = json.load(pose_file)
    except (OSError, ValueError) as exception:
        logger.warning(f'Unable to read HumanIK pose file "{file_path}". Issue: {exception}')
        return []

    if not isinstance(file_data, dict) or file_data.get("format") != HIK_POSE_FILE_FORMAT:
        logger.warning(f'File is not a supported HumanIK pose: "{file_path}".')
        return []
    if file_data.get("version") != HIK_POSE_FILE_VERSION:
        logger.warning(
            f'Unsupported HumanIK pose version "{file_data.get("version")}" in "{file_path}".'
        )
        return []
    pose_data = file_data.get("controls")
    if not isinstance(pose_data, dict):
        logger.warning(f'HumanIK pose file has no valid control data: "{file_path}".')
        return []

    control_map = _get_hik_control_map(character_node)
    if not control_map:
        logger.warning(f'No HumanIK control-rig controls found for "{character_node}".')
        return []
    apply_world_space = file_data.get("world_space", False) if world_space is None else bool(world_space)
    applied_controls = _apply_hik_pose_data(
        control_map,
        pose_data,
        world_space=apply_world_space,
        chunk_name="Import HumanIK Pose",
        prefer_channels=not apply_world_space,
    )
    if applied_controls:
        logger.info(f'Imported HumanIK pose from "{os.path.abspath(file_path)}".')
    else:
        logger.warning(f'No matching HumanIK controls were updated from "{file_path}".')
    return applied_controls


def export_definition_to_xml(character_node, file_path, prefix=""):
    """
    Exports the bone mapping of a HumanIK character definition to an XML file.
    Uses a strict master list of keys to ensure 1:1 parity with Maya's native UI.

    Args:
        character_node (str): The HIK character node to export.
        file_path (str): The absolute path where the XML will be saved.
        prefix (str, optional): A string prefix to append to the mapped joint names.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not cmds.objExists(character_node):
        logger.warning(f'Cannot export. Node "{character_node}" does not exist.')
        return False

    try:
        mapped_bones = {}
        plugs = cmds.listConnections(character_node, connections=True, destination=False, source=True, plugs=True)
        if plugs:
            for i in range(0, len(plugs), 2):
                dest_plug = plugs[i]
                source_plug = plugs[i+1]
                
                hik_attribute = dest_plug.split('.')[-1]
                
                xml_key = hik_attribute[0].upper() + hik_attribute[1:]
                raw_bone = source_plug.split('.')[0].split('|')[-1].split(':')[-1]
                mapped_bones[xml_key] = f"{prefix}{raw_bone}" if prefix else raw_bone

        xml_content = ['<config_root>', '\t<match_list>']
        for key in HIK_CHARACTERIZE_KEYS:
            bone_name = mapped_bones.get(key, "")
            xml_content.append(f'\t\t<item key="{key}" value="{bone_name}"/>')

        xml_content.append('\t</match_list>')
        xml_content.append('</config_root>')

        with open(file_path, "w", encoding="utf-8") as file:
            file.write("\n".join(xml_content))
            
        logger.info(f'Successfully exported 1:1 HIK Match List to: "{file_path}"')
        return True
    except Exception as e:
        logger.error(f'Failed to export XML Match List. Issue: {e}')
        return False


def import_definition_from_xml(character_node, file_path, prefix="", search_namespace="", replace_namespace=""):
    """
    Imports a bone mapping from a native HumanIK XML Match List (<config_root> schema).
    Creates native two-way message connections to satisfy Maya's internal MEL validation.

    Args:
        character_node (str): The target HIK character node.
        file_path (str): The absolute path to the XML template file.
        prefix (str, optional): A prefix to add to the XML bone names.
        search_namespace (str, optional): A namespace string to search for on the bones.
        replace_namespace (str, optional): The string to replace the searched namespace with.

    Returns:
        bool: True if successful, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.warning(f'File path does not exist: "{file_path}"')
        return False
        
    if not cmds.objExists(character_node):
        logger.warning(f'Target node "{character_node}" does not exist.')
        return False

    try:
        set_definition_lock(character_node, lock_state=False)

        tree = ET.parse(file_path)
        root = tree.getroot()
        
        imported_bones_count = 0

        for item in root.findall(".//item"):
            xml_key = item.get("key")
            bone_name = item.get("value")
            
            if not bone_name or not xml_key:
                continue
            
            if prefix:
                bone_name = f"{prefix}{bone_name}"
            
            if search_namespace or replace_namespace:
                bone_name = bone_name.replace(search_namespace, replace_namespace)
            
            if cmds.objExists(bone_name):
                connected = False
                
                # 1. Forward Connection (Joint -> Character Node)
                try:
                    cmds.connectAttr(f"{bone_name}.message", f"{character_node}.{xml_key}", force=True)
                    connected = True
                except Exception:
                    pass
                
                if not connected:
                    maya_attr = xml_key[0].lower() + xml_key[1:]
                    try:
                        cmds.connectAttr(f"{bone_name}.message", f"{character_node}.{maya_attr}", force=True)
                        connected = True
                    except Exception as connect_err:
                        logger.debug(f'Could not connect {bone_name} to {xml_key} or {maya_attr}. Issue: {connect_err}')
                        
                if connected:
                    imported_bones_count += 1
                    
                    # 2. Reverse Connection (Character Node -> Joint) 
                    # Required to prevent "No object matches name: [Bone].Character" error during lock
                    if not cmds.attributeQuery("Character", node=bone_name, exists=True):
                        cmds.addAttr(bone_name, longName="Character", attributeType="message")
                    
                    try:
                        cmds.connectAttr(f"{character_node}.message", f"{bone_name}.Character", force=True)
                    except Exception:
                        pass
            else:
                logger.debug(f'Skipped mapping {xml_key}: Joint "{bone_name}" not found in scene.')
        
        if imported_bones_count == 0:
            logger.warning('No bones were successfully mapped! Verify skeleton and namespaces.')
        else:
            logger.info(f'Successfully imported {imported_bones_count} bones from HIK Match List.')
            
        try:
            mel.eval('hikUpdateCharacterList()')
            mel.eval('hikUpdateContextualUI()')
            mel.eval('hikUpdateSkeletonUI()')
        except Exception:
            pass
            
        return True
    except Exception as e:
        logger.error(f'Failed to import XML Match List. Issue: {e}')
        return False


def bake_to_skeleton(character_node, force_proxy=False):
    """
    Bakes the current animation from the retargeting source down to the skeleton.
    Uses the native HIK UI command 'hikBakeCharacter 0'. If running headless and 
    the MEL script cannot be found, it safely falls back to a Proxy Constraint bake.

    Args:
        character_node (str): The HIK character node to bake.
        force_proxy (bool, optional): If True, skips the native MEL attempt and 
                                      forces the pure Python proxy fallback method.

    Returns:
        bool: True if bake was successful, False otherwise.
    """
    if not cmds.objExists(character_node):
        logger.warning(f'Cannot bake. Node "{character_node}" does not exist.')
        return False

    if not cmds.pluginInfo("mayaHIK", query=True, loaded=True):
        cmds.loadPlugin("mayaHIK")
        
    # Unconditionally prep the HIK environment so internal MEL functions work properly
    try:
        mel.eval('source "hikGlobalUtils.mel"')
        mel.eval('source "hikCharacterControlsUI.mel"')
        mel.eval("HIKCharacterControlsTool;")
        mel.eval(f'hikSetCurrentCharacter("{character_node}")')
    except Exception:
        pass

    if not force_proxy:
        # 1. Attempt the Native UI MEL approach
        try:
            _source_mel_procedure("hikBakeCharacter")
            mel.eval('hikBakeCharacter 0')
            mel.eval('hikSetCurrentSourceFromCharacter(hikGetCurrentCharacter())')
            
            try:
                mel.eval('hikUpdateSourceList')
                mel.eval('hikUpdateContextualUI')
            except Exception:
                pass

            logger.info(f'Successfully baked animation to skeleton using native MEL for: "{character_node}"')
            return True

        except Exception as mel_err:
            logger.debug(f'Native MEL bake crashed, triggering pure Python proxy fallback. Issue: {mel_err}')

    # 2. PYTHON FALLBACK: Proxy Bake (Headless-safe)
    logger.info(f'Using Python Proxy baking for: "{character_node}"')
    
    bones_to_bake = []
    plugs = cmds.listConnections(character_node, connections=True, destination=False, source=True, plugs=True)
    if plugs:
        for i in range(0, len(plugs), 2):
            dest_plug = plugs[i]
            source_plug = plugs[i+1]
            
            hik_attr = dest_plug.split('.')[-1]
            if hik_attr in ["InputCharacter", "OutputCharacter", "reference"]:
                continue
                
            source_node = source_plug.split('.')[0]
            if cmds.objectType(source_node, isAType="transform") or cmds.objectType(source_node, isAType="joint"):
                bones_to_bake.append(source_node)
                
    bones_to_bake = list(set(bones_to_bake))
    if not bones_to_bake:
        logger.warning(f'No bones found mapped to "{character_node}".')
        return False

    start_time = cmds.playbackOptions(query=True, minTime=True)
    end_time = cmds.playbackOptions(query=True, maxTime=True)
    
    proxies = []
    cmds.refresh(suspend=True)
    try:
        for bone in bones_to_bake:
            bone_short = bone.split(':')[-1]
            proxy = cmds.spaceLocator(name=f"{bone_short}_hikProxyBake")[0]
            cmds.parentConstraint(bone, proxy, maintainOffset=False)
            proxies.append(proxy)
            
        cmds.bakeResults(proxies, time=(start_time, end_time), simulation=True)
        set_definition_source(character_node, None)

        current_time = cmds.currentTime(query=True)
        cmds.currentTime(current_time)

        for bone in bones_to_bake:
            for attr in ['translate', 'rotate']:
                for axis in ['X', 'Y', 'Z']:
                    plug = f"{bone}.{attr}{axis}"
                    conns = cmds.listConnections(plug, source=True, destination=False, plugs=True)
                    if conns and not cmds.getAttr(plug, lock=True):
                        cmds.disconnectAttr(conns[0], plug)

        for proxy, bone in zip(proxies, bones_to_bake):
            try:
                cmds.parentConstraint(proxy, bone, maintainOffset=False)
            except Exception:
                pass

        cmds.bakeResults(bones_to_bake, time=(start_time, end_time), simulation=True, disableImplicitControl=True)
        logger.info(f'Successfully proxy-baked animation to skeleton for: "{character_node}"')
        return True

    except Exception as e:
        logger.error(f'Failed to proxy-bake to skeleton. Issue: {e}')
        return False
        
    finally:
        # GUARANTEED CLEANUP: Always runs, even if the script crashes midway.
        cmds.refresh(suspend=False)
        valid_proxies = [p for p in proxies if cmds.objExists(p)]
        if valid_proxies:
            cmds.delete(valid_proxies)


def bake_to_control_rig(character_node):
    """
    Bakes the current animation to the HIK Control Rig associated with the definition.
    Uses the silent 'hikBakeToControlRig 0' command to skip UI dialogs natively.

    Args:
        character_node (str): The HIK character node to bake.

    Returns:
        bool: True if bake was successful, False otherwise.
    """
    if not cmds.objExists(character_node):
        logger.warning(f'Cannot bake. Node "{character_node}" does not exist.')
        return False

    if not cmds.pluginInfo("mayaHIK", query=True, loaded=True):
        cmds.loadPlugin("mayaHIK")
        
    # Unconditionally prep the HIK environment so internal MEL functions work properly
    try:
        mel.eval('source "hikGlobalUtils.mel"')
        mel.eval('source "hikCharacterControlsUI.mel"')
        mel.eval("HIKCharacterControlsTool;")
        mel.eval(f'hikSetCurrentCharacter("{character_node}")')
    except Exception:
        pass

    try:
        _source_mel_procedure("hikBakeToControlRig")
        
        try:
            mel.eval('hikBakeToControlRig 0')
        except Exception:
            mel.eval('hikBakeToControlRig()')
            
        mel.eval('hikSetCurrentSourceFromCharacter(hikGetCurrentCharacter())')
        
        try:
            mel.eval('hikUpdateSourceList')
            mel.eval('hikUpdateContextualUI')
        except Exception:
            pass

        logger.info(f'Successfully baked animation to control rig using silent native MEL for: "{character_node}"')
        return True

    except Exception as mel_err:
        logger.error(f'Failed to natively bake to control rig. Issue: {mel_err}')
        return False


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
