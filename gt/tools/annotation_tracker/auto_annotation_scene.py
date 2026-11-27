"""Read-only Maya sampling and humanoid joint resolution for Auto Annotate."""

import json
import math
import re
from collections import defaultdict

from gt.tools.annotation_tracker import annotation_tracker_model


PELVIS_ALIASES = ("pelvis", "hips", "hip", "cog", "root", "hipcenter")
ROLE_ALIASES = {
    "upper_leg": ("thigh", "upleg", "upperleg", "hip", "femur"),
    "knee": ("calf", "leg", "lowerleg", "shin", "knee", "tibia"),
    "foot": ("foot", "ankle"),
    "toe": ("ball", "toe", "toe_base", "toebase"),
    "heel": ("heel", "heelend"),
    "shoulder": ("clavicle", "shoulder", "collar"),
    "arm": ("upperarm", "arm", "humerus"),
    "forearm": ("lowerarm", "forearm", "elbow"),
    "hand": ("hand", "wrist"),
}
SIDES = {"left": ("left", "l", "lf"), "right": ("right", "r", "rt")}
ROLE_NAMES = ("pelvis", "spine", "chest", "neck", "head") + tuple(
    f"{side}_{role}" for side in SIDES for role in ROLE_ALIASES
)
SPINE_ALIASES = ("spine", "spine01", "spine1", "lowerback", "lowerspine")
CHEST_ALIASES = ("upperchest", "chest", "spine3", "spine03", "spine2", "spine02", "spine1", "spine01", "spine")
NECK_ALIASES = ("neck", "neck01", "neck1")
HEAD_ALIASES = ("head", "head01", "head1")
MOTION_SAMPLE_ROLES = ("pelvis", "spine", "chest", "neck", "head") + tuple(
    f"{side}_{role}" for side in SIDES for role in ("upper_leg", "knee", "foot", "toe", "arm", "forearm", "hand")
)


def _joint_name(path):
    """Extracts a normalized leaf name independent of DAG paths and namespaces.

    Args:
        path (str): Maya DAG path.

    Returns:
        str: Normalized leaf name.
    """
    return re.sub(r"[^a-z0-9]", "", path.rsplit("|", 1)[-1].rsplit(":", 1)[-1].lower())


def _name_score(name, aliases):
    """Ranks known joint aliases, accounting for common joint-name prefixes.

    Args:
        name (str): Normalized Maya joint name.
        aliases (tuple): Ordered normalized aliases.

    Returns:
        int: Positive match score, or zero.
    """
    if name in aliases:
        return 100 - aliases.index(name)
    shortened = re.sub(r"^(mixamorig|bip\d*|biped|jnt|def)(?=\w)", "", name)
    return 70 - aliases.index(shortened) if shortened in aliases else 0


def _side_aliases(side, role):
    """Builds common prefix and suffix spellings for a sided joint.

    Args:
        side (str): Side name.
        role (str): Joint role from the alias table.

    Returns:
        tuple: Normalized aliases in anatomical preference order.
    """
    return tuple(
        value
        for alias in ROLE_ALIASES[role]
        for marker in SIDES[side]
        for value in (f"{marker}{alias.replace('_', '')}", f"{alias.replace('_', '')}{marker}")
    )


def _best_joint(paths, names, aliases, required_parent):
    """Selects an unambiguous joint in one required anatomical branch.

    Args:
        paths (list): Candidate joint paths.
        names (dict): Normalized names keyed by path.
        aliases (tuple): Supported aliases.
        required_parent (str): Required ancestor DAG path.

    Returns:
        str: Best path, or an empty string when unavailable or ambiguous.
    """
    prefix = f"{required_parent}|"
    scores = defaultdict(list)
    for path in paths:
        if path.startswith(prefix):
            score = _name_score(names[path], aliases)
            if score:
                scores[score].append(path)
    if not scores:
        return ""
    winners = scores[max(scores)]
    return winners[0] if len(winners) == 1 else ""


def _auto_candidate(pelvis, paths, names):
    """Finds limbs that belong to the same pelvis hierarchy.

    Args:
        pelvis (str): Candidate pelvis joint.
        paths (list): Descendant joint paths.
        names (dict): Normalized joint names.

    Returns:
        dict: Candidate anatomical role mapping.
    """
    mapping = {"pelvis": pelvis}
    for role, aliases in (
        ("spine", SPINE_ALIASES), ("chest", CHEST_ALIASES), ("neck", NECK_ALIASES), ("head", HEAD_ALIASES)
    ):
        joint = _best_joint(paths, names, aliases, pelvis)
        if joint:
            mapping[role] = joint
    if mapping.get("chest") == mapping.get("spine"):
        mapping.pop("chest", None)
    for side in SIDES:
        parent = pelvis
        for role in ("upper_leg", "knee", "foot", "toe"):
            joint = _best_joint(paths, names, _side_aliases(side, role), parent)
            if joint:
                mapping[f"{side}_{role}"] = joint
                parent = joint
        foot = mapping.get(f"{side}_foot")
        if foot:
            heel = _best_joint(paths, names, _side_aliases(side, "heel"), foot)
            if heel:
                mapping[f"{side}_heel"] = heel
        parent = mapping.get("chest") or mapping.get("spine") or pelvis
        for role in ("shoulder", "arm", "forearm", "hand"):
            joint = _best_joint(paths, names, _side_aliases(side, role), parent)
            if joint:
                mapping[f"{side}_{role}"] = joint
                parent = joint
    return mapping


def _resolve_manual_joint(name, paths, scope=None, short_name_fallback=True):
    """Resolves an explicit joint mapping inside its character hierarchy.

    Args:
        name (str): Joint name or path supplied by the user.
        paths (list): Available joint paths.
        scope (str, optional): Root or pelvis to constrain resolution.
        short_name_fallback (bool): Tries a short name after a missing DAG path.

    Returns:
        str: Unique joint path.

    Raises:
        ValueError: If the joint cannot be found unambiguously.
    """
    candidates = [path for path in paths if not scope or path == scope or path.startswith(f"{scope}|")]
    if name in candidates:
        return name
    if "|" in name and not short_name_fallback:
        raise ValueError(
            f"The manual joint path '{name}' is missing. Update the mapping or enable Short-name fallback."
        )
    leaf = name.rsplit("|", 1)[-1]
    matches = [path for path in candidates if path.endswith(f"|{leaf}")]
    if not matches:
        matches = [path for path in candidates if _joint_name(path) == _joint_name(leaf)]
    if len(matches) != 1:
        issue = "ambiguous" if matches else "missing"
        raise ValueError(f"The manual joint '{name}' is {issue}. Update the skeleton mapping.")
    return matches[0]


def _find_skeleton_root(cmds, name, short_name_fallback):
    """Locates a unique root, optionally retrying with its short name.

    Args:
        cmds (module): Maya commands.
        name (str): Skeleton root transform or joint.
        short_name_fallback (bool): Uses a unique short name when a saved path is missing.

    Returns:
        str: Root DAG path, or an empty string for unrestricted discovery.
    """
    if not name:
        return ""
    queries = [(name,)]
    if "|" in name and short_name_fallback:
        leaf = name.rsplit("|", 1)[-1]
        base = leaf.rsplit(":", 1)[-1]
        queries.extend(((leaf,), (base, f"*:{base}")))
    for patterns in queries:
        matches = cmds.ls(*patterns, long=True, type="transform") or []
        matches.extend(cmds.ls(*patterns, long=True, type="joint") or [])
        matches = list(dict.fromkeys(matches))
        if len(matches) == 1:
            return matches[0]
        if matches:
            break
    raise ValueError("Skeleton root is missing or ambiguous. Choose its full Maya DAG path.")


def resolve_skeleton(cmds, mode="auto", skeleton_root="", joint_map=None, short_name_fallback=True):
    """Resolves a single humanoid skeleton for the current scene.

    Args:
        cmds (module): Maya commands module.
        mode (str): "auto" for discovery or "manual" for an explicit mapping.
        skeleton_root (str): Optional DAG path or name to constrain discovery.
        joint_map (dict, optional): Explicit role-to-joint names for manual mode.
        short_name_fallback (bool): Uses a unique short name when a saved DAG path is missing.

    Returns:
        dict: Anatomy roles mapped to Maya joint paths for this run.

    Raises:
        ValueError: If the skeleton is absent, incomplete, or ambiguous.
    """
    root = _find_skeleton_root(cmds, skeleton_root, short_name_fallback)
    paths = cmds.ls(type="joint", long=True) or []
    if root:
        paths = [path for path in paths if path == root or path.startswith(f"{root}|")]
    if not paths:
        raise ValueError("No joints found. Open a skeleton scene or choose its root in Annotation Setup.")

    required = {"pelvis", "left_foot", "right_foot"}
    if mode == "manual":
        joint_map = joint_map or {}
        if not required.issubset({role for role, name in joint_map.items() if name}):
            raise ValueError("Manual mapping requires a pelvis and both feet.")
        pelvis = _resolve_manual_joint(joint_map["pelvis"], paths, short_name_fallback=short_name_fallback)
        mapping = {"pelvis": pelvis}
        mapping.update({
            role: _resolve_manual_joint(joint_map[role], paths, pelvis, short_name_fallback)
            for role in ROLE_NAMES if role != "pelvis" and joint_map.get(role)
        })
        if len(mapping) != len(set(mapping.values())):
            raise ValueError("Assign a different joint to each skeleton role.")
        for side in SIDES:
            leg = [mapping[role] for role in (f"{side}_upper_leg", f"{side}_knee", f"{side}_foot") if role in mapping]
            if any(not child.startswith(f"{parent}|") for parent, child in zip(leg, leg[1:])):
                raise ValueError(f"The manual {side} upper leg, knee and foot must follow the joint hierarchy.")
        return mapping
    if mode != "auto":
        raise ValueError("Skeleton mode must be auto or manual.")

    names = {path: _joint_name(path) for path in paths}
    candidates = []
    for path in paths:
        score = _name_score(names[path], PELVIS_ALIASES)
        if not score:
            continue
        descendants = [joint for joint in paths if joint.startswith(f"{path}|")]
        mapping = _auto_candidate(path, descendants, names)
        if required.issubset(mapping):
            primary = 0 if names[path] == "root" else 1
            candidates.append((primary, len(mapping), score, mapping))
    if not candidates:
        raise ValueError("Could not resolve a pelvis and both feet in one skeleton. Set a manual mapping.")

    # Prefer anatomical pelvis joints over ancestors named root on the same rig.
    finalists = [
        entry for entry in candidates
        if not any(
            other[3]["pelvis"].startswith(f'{entry[3]["pelvis"]}|')
            and other[:3] >= entry[:3] for other in candidates
        )
    ]
    if len(finalists) != 1:
        names = ", ".join(entry[3]["pelvis"] for entry in finalists[:4])
        raise ValueError(f"Multiple skeleton candidates: {names}. Choose a skeleton root or manual mapping.")
    return finalists[0][3]


def playback_bounds(cmds):
    """Gets the inclusive annotation frame bounds for the scene playback range.

    Args:
        cmds (module): Maya commands module.

    Returns:
        tuple: First and last integer playback frames.
    """
    return (
        math.ceil(cmds.playbackOptions(query=True, minTime=True)),
        math.floor(cmds.playbackOptions(query=True, maxTime=True)),
    )


def sample_joints(cmds, mapping, start, end):
    """Samples the joints used for annotation cues with canonical Y-up positions.

    Args:
        cmds (module): Maya commands module.
        mapping (dict): Resolved Maya joint paths by anatomical role.
        start (int): First sample frame.
        end (int): Last sample frame, inclusive.

    Returns:
        dict: First frame, sample frame rate, and per-frame positions.
    """
    from gt.core.anim import sample_animation_range
    from gt.core.scene import get_fps_from_time_unit

    fps = get_fps_from_time_unit(cmds.currentUnit(query=True, time=True))
    if not fps or not math.isfinite(fps) or fps < 0:
        raise ValueError("Could not resolve the Maya scene frame rate.")
    z_up = cmds.upAxis(query=True, axis=True).lower() == "z"
    sampled_roles = {role: mapping[role] for role in MOTION_SAMPLE_ROLES if role in mapping}

    def capture_positions():
        """Captures the current joints as Y-up positions.

        Returns:
            dict: World-space position for each mapped role.
        """
        positions = {}
        for role, path in sampled_roles.items():
            point = cmds.xform(path, query=True, worldSpace=True, translation=True)
            if not all(math.isfinite(value) for value in point):
                raise ValueError(f"Joint '{role}' has a non-finite position.")
            positions[role] = (point[0], point[2], -point[1]) if z_up else tuple(point)
        return positions

    samples = sample_animation_range(capture_positions, start, end)
    return {"start": start, "fps": fps, "positions": [positions for _, positions in samples]}


def read_payload(cmds, context=None):
    """Reads the live Tracker or scene data with IDs and locks intact.

    Args:
        cmds (module): Maya commands module.
        context (dict, optional): Automation context with a live payload getter.

    Returns:
        dict: Normalized scene payload.

    Raises:
        ValueError: If stored tracker data is malformed.
    """
    get_live_payload = (context or {}).get("get_annotation_payload")
    if get_live_payload is not None:
        return get_live_payload()
    node_name = annotation_tracker_model.SCENE_DATA_NODE_NAME
    attribute = annotation_tracker_model.SCENE_DATA_ATTRIBUTE
    if not cmds.objExists(node_name):
        return {"file_data": {}, "range_data": []}
    if cmds.nodeType(node_name) != "network":
        raise ValueError(f"'{node_name}' exists but is not an Annotation Tracker network node.")
    if not cmds.attributeQuery(attribute, node=node_name, exists=True):
        return {"file_data": {}, "range_data": []}
    raw_data = cmds.getAttr(f"{node_name}.{attribute}")
    if not raw_data:
        return {"file_data": {}, "range_data": []}
    data = json.loads(raw_data)
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("file_data", {}), dict)
        or not isinstance(data.get("range_data", []), list)
    ):
        raise ValueError("Existing Annotation Tracker data is invalid.")
    return annotation_tracker_model.build_scene_payload(data.get("file_data", {}), data.get("range_data", []))


def has_valid_clips(cmds):
    """Checks for valid Clip Tracker ranges in the scene.

    Args:
        cmds (module): Maya commands module.

    Returns:
        bool: Whether a clip with a valid range exists.
    """
    from gt.tools.anim_clip_tracker.clip_tracker_model import CLIP_ATTR_NAME, CLIP_NODE_NAME, normalize_clip_data

    if not cmds.objExists(CLIP_NODE_NAME) or not cmds.attributeQuery(
        CLIP_ATTR_NAME, node=CLIP_NODE_NAME, exists=True
    ):
        return False
    clips = json.loads(cmds.getAttr(f"{CLIP_NODE_NAME}.{CLIP_ATTR_NAME}") or "[]")
    if isinstance(clips, dict):
        clips = clips.get("clips", [])
    if not isinstance(clips, list):
        raise ValueError("Clip Tracker data must contain a list of clips.")
    for item in clips:
        if isinstance(item, dict) and "start" in item and "end" in item:
            try:
                clip = normalize_clip_data([item])[0]
            except (TypeError, ValueError, OverflowError):
                continue
            if clip["start"] <= clip["end"]:
                return True
    return False
