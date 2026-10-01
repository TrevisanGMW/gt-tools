"""Source-only HumanIK helpers using the batch processor's pose and XML formats."""

import json
from gt.core.io import write_json
from gt.tools.kimodo_generator import kimodo_generator_hik as humanik


def source_joints(group):
    """Resolves only the selected Kimodo hierarchy.

    Args:
        group (str): Imported group or descendant.

    Returns:
        tuple: Skeleton metadata and scoped joint mapping.
    """
    import maya.cmds as cmds
    from gt.utils import kimodo

    group = kimodo.find_pose_group(group)
    skeleton = json.loads(cmds.getAttr(f"{group}.kimodoSkeleton"))
    return skeleton, humanik._resolve_joints(group, skeleton)


def source_character(group):
    """Finds the character attached to this import instead of guessing from its name.

    Args:
        group (str): Imported group or descendant.

    Returns:
        str: Unambiguous source HumanIK character.
    """
    import maya.cmds as cmds

    unused, joints = source_joints(group)
    characters = set()
    for joint in joints.values():
        characters.update(cmds.listConnections(f"{joint}.message", type="HIKCharacterNode") or [])
    if len(characters) != 1:
        raise ValueError("The source must have one HumanIK definition. Add its definition first.")
    return characters.pop()


def export_pose(group, path):
    """Exports the current source pose using the same format as the batch task.

    Args:
        group (str): Imported source hierarchy.
        path (str): Confirmed output path.
    """
    from gt.core import pose

    unused, joints = source_joints(group)
    if write_json(path, pose.get_pose_as_dict(list(joints.values()))) is None:
        raise OSError(f"Could not write pose: {path}")


def export_definition(character, path):
    """Exports a native HumanIK XML using the batch task's shared helper.

    Args:
        character (str): Existing source or target character.
        path (str): Confirmed output path.
    """
    from gt.utils import hik

    if not hik.export_definition_to_xml(character, path):
        raise OSError(f"Could not export HumanIK XML: {path}")


def apply_pose(group, settings):
    """Applies the reference pose at the current frame after UI confirmation.

    Existing animation connections remain intact. Animated channels receive a
    current-frame key; unanimated channels are set directly. Maya Undo restores it.

    Args:
        group (str): Imported source hierarchy.
        settings (dict): Source pose overrides.

    Returns:
        int: Number of posed joints.
    """
    import maya.cmds as cmds

    options = humanik.validate_settings(settings)
    skeleton, joints = source_joints(group)
    pose = humanik.reference_pose(skeleton, joints, options)
    if pose is None:
        pose = {name: {channel: cmds.getAttr(f"{joint}.{channel}", time=options["reference_frame"])
                       for channel in humanik.POSE_CHANNELS[:6]} for name, joint in joints.items()}
    channels = []
    for name, values in pose.items():
        for channel, value in values.items():
            plug = f"{joints[name]}.{channel}"
            source = cmds.connectionInfo(plug, sourceFromDestination=True)
            driven = source and not cmds.nodeType(source.split(".")[0]).startswith("animCurve")
            if cmds.getAttr(plug, lock=True) or driven:
                raise ValueError(f"Cannot pose locked or driven channel: {plug}")
            channels.append((plug, value, bool(source)))
    auto_key = cmds.autoKeyframe(query=True, state=True)
    cmds.undoInfo(openChunk=True, chunkName="Test Kimodo HumanIK Pose")
    try:
        cmds.autoKeyframe(state=False)
        for plug, value, animated in channels:
            if animated:
                cmds.setKeyframe(plug, value=value, time=cmds.currentTime(query=True))
            else:
                cmds.setAttr(plug, value)
        cmds.currentTime(cmds.currentTime(query=True), edit=True)
    finally:
        cmds.autoKeyframe(state=auto_key)
        cmds.undoInfo(closeChunk=True)
    return len(pose)
