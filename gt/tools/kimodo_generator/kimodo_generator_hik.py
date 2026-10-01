"""Scoped HumanIK definition creation for imported Kimodo skeletons.

Pure settings and mapping helpers import without Maya. Runtime operations reuse
gt.utils.hik, whose MEL wrappers initialize Maya's native HIK characterization.
"""

import json
import math
import os
import re
import tempfile
import threading
import xml.etree.ElementTree as ET
from gt.core.io import read_json_dict


REQUIRED_SLOTS = ("Hips", "Spine", "Head", "LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg",
                  "RightFoot", "LeftArm", "LeftForeArm", "LeftHand", "RightArm", "RightForeArm", "RightHand")
POSE_CHANNELS = ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")


def default_settings():
    """Returns empty optional overrides and safe characterization defaults.

    Returns:
        dict: Serializable HumanIK preferences.
    """
    return {"character_name": "", "definition_path": "", "tpose_path": "",
            "reference_frame": None, "lock_definition": True}


def validate_settings(settings, check_files=False):
    """Validates optional overrides without resolving blank paths against the CWD.

    Args:
        settings (dict): User settings; omitted keys use defaults.
        check_files (bool): Whether supplied paths must exist before scene edits.

    Returns:
        dict: Normalized settings.
    """
    if not isinstance(settings, dict) or set(settings) - set(default_settings()):
        raise ValueError("Invalid HumanIK settings.")
    result = dict(default_settings(), **settings)
    for key in ("character_name", "definition_path", "tpose_path"):
        if not isinstance(result[key], str):
            raise ValueError(f"HumanIK {key} must be text.")
        result[key] = result[key].strip()
    name = result["character_name"]
    if name and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
        raise ValueError("Use a HumanIK character name containing letters, numbers, and underscores.")
    frame = result["reference_frame"]
    if frame is not None and (type(frame) not in (int, float) or not math.isfinite(frame)):
        raise ValueError("HumanIK reference frame must be a finite number, or blank.")
    if frame is not None and result["tpose_path"]:
        raise ValueError("Choose either a reference frame or a T-pose file, not both.")
    if type(result["lock_definition"]) is not bool:
        raise ValueError("HumanIK lock_definition must be a boolean.")
    if check_files:
        for key in ("definition_path", "tpose_path"):
            if result[key] and (not os.path.isabs(result[key]) or not os.path.isfile(result[key])):
                raise ValueError(f"Choose an existing absolute path for HumanIK {key}: {result[key]}")
    return result


def soma_mapping(skeleton):
    """Maps the supported SOMA77 names explicitly, including its non-HIK leg names.

    Args:
        skeleton (dict): Imported exchange metadata.

    Returns:
        dict: HumanIK slot to skeleton joint name.
    """
    names = skeleton.get("joint_names", [])
    if skeleton.get("id") != "somaskel77" or len(names) != 77:
        raise ValueError("Automatic HumanIK mapping requires SOMA77. Provide an XML definition for this skeleton.")
    mapping = {"Hips": "Hips", "Spine": "Spine1", "Spine1": "Spine2", "Spine2": "Chest",
               "Neck": "Neck1", "Neck1": "Neck2", "Head": "Head"}
    for side in ("Left", "Right"):
        for slot, joint in (("UpLeg", "Leg"), ("Leg", "Shin"), ("Foot", "Foot"), ("ToeBase", "ToeBase"),
                            ("Shoulder", "Shoulder"), ("Arm", "Arm"), ("ForeArm", "ForeArm"), ("Hand", "Hand")):
            mapping[f"{side}{slot}"] = f"{side}{joint}"
        for index in range(1, 4):
            mapping[f"{side}HandThumb{index}"] = f"{side}HandThumb{index}"
        for finger in ("Index", "Middle", "Ring", "Pinky"):
            mapping[f"{side}InHand{finger}"] = f"{side}Hand{finger}1"
            for index in range(1, 4):
                mapping[f"{side}Hand{finger}{index}"] = f"{side}Hand{finger}{index + 1}"
    missing = sorted(set(mapping.values()) - set(names))
    if missing:
        raise ValueError(f"SOMA skeleton names have changed. Supply a matching XML definition. Missing: {missing}")
    return mapping


def read_mapping(path, skeleton):
    """Loads native HumanIK Match List XML, resolving names only within this skeleton.

    Args:
        path (str): Optional custom XML path.
        skeleton (dict): Imported skeleton metadata.

    Returns:
        dict: Validated slot-to-short-joint mapping.
    """
    if not path:
        return soma_mapping(skeleton)
    try:
        root = ET.parse(path).getroot()
    except (ET.ParseError, OSError) as error:
        raise ValueError(f"Could not read HumanIK definition XML: {error}") from error
    mapping = {}
    for item in root.findall(".//match_list/item"):
        slot = item.get("key", "")
        name = item.get("value", "").rsplit("|", 1)[-1].rsplit(":", 1)[-1]
        if not slot or not name:
            continue
        if slot in mapping:
            raise ValueError(f"Duplicate HumanIK XML slot: {slot}")
        mapping[slot] = name
    missing = set(REQUIRED_SLOTS) - set(mapping)
    if missing:
        raise ValueError(f"HumanIK XML is missing required slots: {', '.join(sorted(missing))}")
    absent = set(mapping.values()) - set(skeleton["joint_names"])
    if absent or len(set(mapping.values())) != len(mapping):
        raise ValueError("HumanIK XML contains missing joints or assigns the same joint to multiple slots.")
    return mapping


def read_pose(path, joint_names):
    """Validates the local-channel .pose JSON format used by the batch processor.

    Args:
        path (str): T-pose file explicitly chosen by the user.
        joint_names (list): Allowed joints in the imported skeleton.

    Returns:
        dict: Pose values scoped to known joint names.
    """
    pose = read_json_dict(path)
    if not isinstance(pose, dict) or not pose:
        raise ValueError("T-pose file is empty or invalid. Use a batch-processor/core.pose .pose JSON file.")
    validated = {}
    for raw_name, channels in pose.items():
        name = raw_name.rsplit("|", 1)[-1].rsplit(":", 1)[-1]
        if name not in joint_names or name in validated or not isinstance(channels, dict) or not channels:
            raise ValueError(f"T-pose contains an unknown, duplicate, or invalid joint: {raw_name}")
        for channel, value in channels.items():
            if channel not in POSE_CHANNELS or type(value) not in (int, float) or not math.isfinite(value):
                raise ValueError(f"Invalid T-pose channel: {raw_name}.{channel}")
        validated[name] = channels
    return validated


def _resolve_joints(group, skeleton):
    """Resolves the exact imported hierarchy without matching unrelated scene nodes.

    Args:
        group (str): Kimodo placement group.
        skeleton (dict): Stored hierarchy metadata.

    Returns:
        dict: Short names mapped to full joint paths.
    """
    import maya.cmds as cmds

    joints = cmds.listRelatives(group, allDescendents=True, type="joint", fullPath=True) or []
    mapping = {joint.rsplit("|", 1)[-1].rsplit(":", 1)[-1]: joint for joint in joints}
    if len(mapping) != len(joints) or set(mapping) != set(skeleton["joint_names"]):
        raise ValueError("The imported skeleton hierarchy was renamed or changed. Reimport before defining HumanIK.")
    for index, name in enumerate(skeleton["joint_names"]):
        parent_index = skeleton["parents"][index]
        parent = group if parent_index == -1 else mapping[skeleton["joint_names"][parent_index]]
        if (cmds.listRelatives(mapping[name], parent=True, fullPath=True) or [None])[0] != parent:
            raise ValueError("The imported joint hierarchy changed. Reimport before defining HumanIK.")
    return mapping


def _capture_stance(character):
    """Captures native HIK reference offsets even when its UI has never been opened.

    Maya exposes stance capture and solver finalization only as MEL procedures.
    The shared lock helper may fall back to an attribute without capturing these
    offsets, so capture explicitly before locking. The identifier is generated
    and validated locally, never taken from XML or pose contents.

    Args:
        character (str): Newly created, validated root-namespace character name.
    """
    import maya.mel as mel
    from gt.utils import hik

    hik._source_mel_procedure("hikReadStancePoseTRSOffsets")
    mel.eval(f'hikReadStancePoseTRSOffsets("{character}")')


def _finalize_character(character):
    """Ensures native solver/property nodes exist after the definition is locked.

    Args:
        character (str): Newly created root-namespace character name.
    """
    import maya.mel as mel
    from gt.utils import hik

    hik._source_mel_procedure("hikPostCharacterisationStep")
    mel.eval(f'hikPostCharacterisationStep("{character}")')


def reference_pose(skeleton, joints, options):
    """Resolves optional pose data or the default Kimodo rest stance.

    Args:
        skeleton (dict): Import metadata.
        joints (dict): Scoped joint paths.
        options (dict): Validated HumanIK settings.

    Returns:
        dict or None: Local pose channels, or None when using a reference frame.
    """
    import maya.api.OpenMaya as om
    if options["tpose_path"]:
        pose = read_pose(options["tpose_path"], list(joints))
    elif options["reference_frame"] is not None:
        pose = None
    else:
        # Unknown skeletons need an explicit stance instead of assuming their rest convention.
        try:
            soma_mapping(skeleton)
        except ValueError as error:
            raise ValueError("Unknown rest stance. Supply XML and a T-pose file or reference frame.") from error
        scale = om.MDistance(1, om.MDistance.kMeters).asUnits(om.MDistance.uiUnit())
        pose = {}
        neutral_heights = []
        for index, name in enumerate(skeleton["joint_names"]):
            pose[name] = dict(rx=0.0, ry=0.0, rz=0.0)
            parent = skeleton["parents"][index]
            neutral_heights.append((neutral_heights[parent] if parent >= 0 else 0)
                                   + skeleton["offsets"][index][1])
            if index:
                pose[name].update(zip(("tx", "ty", "tz"), [value * scale for value in skeleton["offsets"][index]]))
        # Ground the temporary reference stance instead of inheriting a crouched
        # animated root height. Saved animation/values are restored after capture.
        pose[skeleton["joint_names"][0]]["ty"] = -min(neutral_heights) * scale
    if options["tpose_path"] and (set(skeleton["joint_names"]) - set(pose)
                                 or any(set(POSE_CHANNELS[:6]) - set(values) for values in pose.values())):
        raise ValueError("Supply a complete T-pose for the imported skeleton so no animated joints define the stance.")
    return pose


def create_definition(group=None, settings=None):
    """Characterizes an imported skeleton while preserving its existing animation.

    Native HIK operations use the repository's small MEL wrappers.

    Args:
        group (str, optional): Imported group or selected descendant.
        settings (dict, optional): Optional definition/pose/name overrides.

    Returns:
        dict: Created character, target group, and mapped-joint count.
    """
    import maya.cmds as cmds
    from gt.utils import kimodo

    if threading.current_thread() is not threading.main_thread():
        raise RuntimeError("Create the HumanIK definition on Maya's main thread.")
    options = validate_settings(settings or {}, check_files=True)
    group = kimodo.find_pose_group(group)
    skeleton = json.loads(cmds.getAttr(f"{group}.kimodoSkeleton"))
    joints = _resolve_joints(group, skeleton)
    mapping = read_mapping(options["definition_path"], skeleton)
    pose = reference_pose(skeleton, joints, options)
    for joint in joints.values():
        existing = cmds.listConnections(f"{joint}.message", type="HIKCharacterNode", destination=True) or []
        if existing:
            raise ValueError(f"This skeleton already has a HumanIK definition: {existing[0]}. Manage it in HumanIK.")
        if not options["tpose_path"] and options["reference_frame"] is None:
            if any(abs(value) > 0.00001 for value in cmds.getAttr(f"{joint}.jointOrient")[0]):
                raise ValueError("Joint orientations changed. Supply an explicit T-pose or reference frame.")
    name = options["character_name"] or "kimodo"
    if not options["character_name"]:
        suffix = 1
        while cmds.objExists(f":{name}") or cmds.namespace(exists=f":{name}"):
            name = f"kimodo{suffix}"
            suffix += 1
    if cmds.objExists(f":{name}") or cmds.namespace(exists=f":{name}"):
        raise ValueError(f"HumanIK name is occupied by a node or namespace: {name}. Choose another name.")
    from gt.utils import hik as utils_hik

    unknown_slots = set(mapping) - set(utils_hik.HIK_CHARACTERIZE_KEYS)
    if unknown_slots:
        raise ValueError(f"Unknown HumanIK XML slots: {sorted(unknown_slots)}")
    # Load required HIK infrastructure before changing the skeleton.
    for plugin in ("mayaHIK", "mayaCharacterization"):
        if not cmds.pluginInfo(plugin, query=True, loaded=True):
            cmds.loadPlugin(plugin, quiet=True)
    utils_hik._source_mel_procedure("hikCreateCharacter")
    before_nodes = set(cmds.ls() or [])
    selected = cmds.ls(selection=True, long=True) or []
    original_time = cmds.currentTime(query=True)
    original_namespace = cmds.namespaceInfo(currentNamespace=True, absoluteName=True)
    auto_key = cmds.autoKeyframe(query=True, state=True)
    saved = []
    character = None
    succeeded = False
    new_character_attrs = [joint for joint in joints.values()
                           if not cmds.attributeQuery("Character", node=joint, exists=True)]
    cmds.undoInfo(openChunk=True, chunkName="Define Kimodo HumanIK")
    try:
        cmds.autoKeyframe(state=False)
        cmds.namespace(setNamespace=":")
        if options["reference_frame"] is not None:
            cmds.currentTime(options["reference_frame"], edit=True)
        if pose is not None:
            for short_name, values in pose.items():
                for channel, value in values.items():
                    plug = f"{joints[short_name]}.{channel}"
                    source = cmds.connectionInfo(plug, sourceFromDestination=True) or ""
                    if source and not cmds.nodeType(source.split(".")[0]).startswith("animCurve"):
                        raise ValueError(f"Unsupported driven channel: {plug}. Use an unmodified Kimodo import.")
                    saved.append((plug, cmds.getAttr(plug), source, cmds.getAttr(plug, lock=True)))
                    cmds.setAttr(plug, lock=False)
                    if source:
                        cmds.disconnectAttr(source, plug)
                    cmds.setAttr(plug, value)
        character = utils_hik.create_definition(name)
        if not character or not cmds.objExists(character):
            raise RuntimeError("Maya could not create the HumanIK character. Check the HIK plugin and Script Editor.")
        # Generate a resolved temporary match list so even namespaced custom XML
        # can only connect joints belonging to the selected Kimodo hierarchy.
        root = ET.Element("config_root")
        matches = ET.SubElement(root, "match_list")
        for slot, joint_name in mapping.items():
            ET.SubElement(matches, "item", key=slot, value=joints[joint_name])
        with tempfile.TemporaryDirectory(prefix="gt_kimodo_hik_") as directory:
            path = os.path.join(directory, "definition.xml")
            ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)
            if not utils_hik.import_definition_from_xml(character, path):
                raise RuntimeError("HumanIK could not apply the joint mapping.")
        for slot in mapping:
            plug = f"{character}.{slot}"
            if not cmds.objExists(plug):
                plug = f"{character}.{slot[0].lower()}{slot[1:]}"
            if not cmds.listConnections(plug, source=True, destination=False):
                raise RuntimeError(f"HumanIK did not map {slot}.")
        _capture_stance(character)
        if options["lock_definition"]:
            if not utils_hik.set_definition_lock(character, True):
                raise ValueError("HumanIK could not lock the definition. Supply a valid T-pose and XML mapping.")
            _finalize_character(character)
        succeeded = True
    finally:
        restore_errors = []
        for plug, value, source, locked in reversed(saved):
            try:
                cmds.setAttr(plug, value)
            except RuntimeError as error:
                restore_errors.append(f"{plug}: {error}")
            finally:
                try:
                    if source and not cmds.isConnected(source, plug):
                        cmds.connectAttr(source, plug, force=True)
                    cmds.setAttr(plug, lock=locked)
                except RuntimeError as error:
                    restore_errors.append(f"{plug}: {error}")
        try:
            if not succeeded:
                created = [node for node in set(cmds.ls() or []) - before_nodes
                           if cmds.nodeType(node).startswith("HIK")]
                if created:
                    cmds.delete(created)
                for joint in new_character_attrs:
                    if cmds.attributeQuery("Character", node=joint, exists=True):
                        cmds.deleteAttr(f"{joint}.Character")
        finally:
            try:
                cmds.currentTime(original_time, edit=True)
                cmds.namespace(setNamespace=original_namespace)
                cmds.select(selected, replace=True) if selected else cmds.select(clear=True)
            finally:
                cmds.autoKeyframe(state=auto_key)
                cmds.undoInfo(closeChunk=True)
        if restore_errors:
            raise RuntimeError("Could not fully restore HumanIK pose channels: " + "; ".join(restore_errors))
    return {"character": character, "group": group, "mapped_joints": len(mapping),
            "locked": bool(cmds.getAttr(f"{character}.InputCharacterizationLock"))}
