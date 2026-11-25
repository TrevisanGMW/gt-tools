"""
Motion Evaluation Skeleton Templates - Role mapping that keeps evaluation skeleton-agnostic.

A skeleton template maps evaluation roles (hips, left_foot, ...) to one or more
candidate joint names. Templates contain no scene data, so the built-in ones
only describe public skeletons. Custom templates are saved by the user as JSON.

Template layout:
    {
        "schema": "motion_eval_skeleton",
        "version": 1,
        "name": "My Skeleton",
        "description": "",
        "up_axis": "scene",
        "roles": {"hips": ["pelvis"], "left_foot": ["foot_l"], ...}
    }
"""

import copy
import json
import os

TEMPLATE_SCHEMA = "motion_eval_skeleton"
TEMPLATE_VERSION = 1
TEMPLATE_FILE_EXTENSION = ".json"
UP_AXIS_VALUES = ["scene", "y", "z"]

# Role key, label, required for biped mode, description
ROLE_DEFINITIONS = [
    ("root", "Root", False, "Optional top node such as a trajectory or reference joint."),
    ("hips", "Hips", True, "Pelvis joint. Used as the center of mass and root speed source."),
    ("spine", "Spine", True, "Lowest spine joint."),
    ("chest", "Chest", False, "Upper spine joint. Improves the torso proxy."),
    ("neck", "Neck", False, "Neck joint. Improves the torso proxy."),
    ("head", "Head", True, "Head joint."),
    ("left_up_leg", "Left Thigh", True, "Left hip/thigh joint."),
    ("left_leg", "Left Knee", True, "Left knee/calf joint."),
    ("left_foot", "Left Foot", True, "Left ankle/foot joint."),
    ("left_toe", "Left Toe", False, "Left toe/ball joint. Improves contact and knee checks."),
    ("left_heel", "Left Heel", False, "Optional left heel joint. Improves contact detection."),
    ("right_up_leg", "Right Thigh", True, "Right hip/thigh joint."),
    ("right_leg", "Right Knee", True, "Right knee/calf joint."),
    ("right_foot", "Right Foot", True, "Right ankle/foot joint."),
    ("right_toe", "Right Toe", False, "Right toe/ball joint. Improves contact and knee checks."),
    ("right_heel", "Right Heel", False, "Optional right heel joint. Improves contact detection."),
    ("left_shoulder", "Left Clavicle", False, "Left clavicle/shoulder joint."),
    ("left_arm", "Left Upper Arm", False, "Left upper arm joint."),
    ("left_forearm", "Left Forearm", False, "Left elbow/forearm joint."),
    ("left_hand", "Left Hand", False, "Left hand/wrist joint."),
    ("right_shoulder", "Right Clavicle", False, "Right clavicle/shoulder joint."),
    ("right_arm", "Right Upper Arm", False, "Right upper arm joint."),
    ("right_forearm", "Right Forearm", False, "Right elbow/forearm joint."),
    ("right_hand", "Right Hand", False, "Right hand/wrist joint."),
]
ROLE_KEYS = [role[0] for role in ROLE_DEFINITIONS]
ROLE_LABELS = {role[0]: role[1] for role in ROLE_DEFINITIONS}
ROLE_DESCRIPTIONS = {role[0]: role[3] for role in ROLE_DEFINITIONS}
REQUIRED_BIPED_ROLES = [role[0] for role in ROLE_DEFINITIONS if role[2]]

BUILTIN_TEMPLATES = {
    "maya_humanik": {
        "schema": TEMPLATE_SCHEMA,
        "version": TEMPLATE_VERSION,
        "name": "Maya HumanIK",
        "description": (
            "Default HumanIK skeleton created by Maya (Skeleton > Create Skeleton) and used by Maya's "
            "example characters. Prefixed names such as 'Character1_Hips' are matched automatically."
        ),
        "up_axis": "scene",
        "roles": {
            "root": ["Reference"],
            "hips": ["Hips"],
            "spine": ["Spine"],
            "chest": ["Spine2", "Spine1"],
            "neck": ["Neck"],
            "head": ["Head"],
            "left_up_leg": ["LeftUpLeg"],
            "left_leg": ["LeftLeg"],
            "left_foot": ["LeftFoot", "s_genrig_LeftFoot"],
            "left_toe": ["LeftToeBase"],
            "right_up_leg": ["RightUpLeg"],
            "right_leg": ["RightLeg"],
            "right_foot": ["RightFoot", "s_genrig_RightFoot"],
            "right_toe": ["RightToeBase"],
            "left_shoulder": ["LeftShoulder"],
            "left_arm": ["LeftArm"],
            "left_forearm": ["LeftForeArm"],
            "left_hand": ["LeftHand"],
            "right_shoulder": ["RightShoulder"],
            "right_arm": ["RightArm"],
            "right_forearm": ["RightForeArm"],
            "right_hand": ["RightHand"],
        },
    },
    "unreal_mannequin": {
        "schema": TEMPLATE_SCHEMA,
        "version": TEMPLATE_VERSION,
        "name": "Unreal Mannequin",
        "description": "Unreal Engine example mannequin skeleton (UE4 and UE5 joint names).",
        "up_axis": "scene",
        "roles": {
            "root": ["root"],
            "hips": ["pelvis"],
            "spine": ["spine_01"],
            "chest": ["spine_05", "spine_03"],
            "neck": ["neck_01"],
            "head": ["head"],
            "left_up_leg": ["thigh_l"],
            "left_leg": ["calf_l"],
            "left_foot": ["foot_l"],
            "left_toe": ["ball_l"],
            "right_up_leg": ["thigh_r"],
            "right_leg": ["calf_r"],
            "right_foot": ["foot_r"],
            "right_toe": ["ball_r"],
            "left_shoulder": ["clavicle_l"],
            "left_arm": ["upperarm_l"],
            "left_forearm": ["lowerarm_l"],
            "left_hand": ["hand_l"],
            "right_shoulder": ["clavicle_r"],
            "right_arm": ["upperarm_r"],
            "right_forearm": ["lowerarm_r"],
            "right_hand": ["hand_r"],
        },
    },
}
DEFAULT_TEMPLATE_KEY = "maya_humanik"


# ------------------------------------------------ Template Data ------------------------------------------------
def get_builtin_template_keys():
    """Gets the keys of the built-in templates in display order.

    Returns:
        list: Built-in template keys.
    """
    return list(BUILTIN_TEMPLATES.keys())


def get_builtin_template(template_key):
    """Gets a copy of a built-in template.

    Args:
        template_key (str): Built-in template key.

    Returns:
        dict: Template copy.

    Raises:
        KeyError: If the key is unknown.
    """
    if template_key not in BUILTIN_TEMPLATES:
        raise KeyError(f'Unknown built-in skeleton template: "{template_key}"')
    return copy.deepcopy(BUILTIN_TEMPLATES[template_key])


def create_template(name="New Skeleton", roles=None, description="", up_axis="scene"):
    """Creates a new template dictionary.

    Args:
        name (str): Display name.
        roles (dict, optional): Role to candidate-name mapping.
        description (str): Optional description.
        up_axis (str): "scene", "y", or "z".

    Returns:
        dict: Normalized template.
    """
    return normalize_template(
        {
            "schema": TEMPLATE_SCHEMA,
            "version": TEMPLATE_VERSION,
            "name": name,
            "description": description,
            "up_axis": up_axis,
            "roles": roles or {},
        }
    )


def normalize_candidates(value):
    """Converts a role value into a clean list of candidate names.

    Args:
        value (str or list): Comma-separated names or a list of names.

    Returns:
        list: Unique, stripped candidate names in their original order.
    """
    if value is None:
        return []
    if isinstance(value, str):
        value = value.split(",")
    candidates = []
    for name in value:
        name = str(name or "").strip()
        if name and name not in candidates:
            candidates.append(name)
    return candidates


def normalize_template(template):
    """Normalizes a template dictionary, keeping only known roles.

    Args:
        template (dict): Raw template data.

    Returns:
        dict: Normalized copy.
    """
    template = template if isinstance(template, dict) else {}
    raw_roles = template.get("roles") if isinstance(template.get("roles"), dict) else {}
    roles = {}
    for role_key in ROLE_KEYS:
        candidates = normalize_candidates(raw_roles.get(role_key))
        if candidates:
            roles[role_key] = candidates
    up_axis = str(template.get("up_axis") or "scene").strip().lower()
    if up_axis not in UP_AXIS_VALUES:
        up_axis = "scene"
    return {
        "schema": TEMPLATE_SCHEMA,
        "version": TEMPLATE_VERSION,
        "name": str(template.get("name") or "Unnamed Skeleton").strip() or "Unnamed Skeleton",
        "description": str(template.get("description") or ""),
        "up_axis": up_axis,
        "roles": roles,
    }


def validate_template(template, require_biped=False):
    """Validates template structure.

    Args:
        template (dict): Template data.
        require_biped (bool): Require every biped role to have candidates.

    Returns:
        list: Error messages. Empty when valid.
    """
    errors = []
    if not isinstance(template, dict):
        return ["Skeleton template must be a dictionary."]
    schema = template.get("schema")
    if schema and not str(schema).endswith(TEMPLATE_SCHEMA):
        errors.append(f'Unexpected skeleton template schema "{schema}".')
    roles = template.get("roles")
    if not isinstance(roles, dict):
        errors.append('Skeleton template is missing its "roles" dictionary.')
        return errors
    unknown_roles = sorted(set(roles.keys()) - set(ROLE_KEYS))
    if unknown_roles:
        errors.append(f"Unknown skeleton roles: {', '.join(unknown_roles)}")
    for role_key, value in roles.items():
        if not isinstance(value, (str, list, tuple)):
            errors.append(f'Role "{role_key}" must be a name or a list of names.')
    if require_biped:
        normalized = normalize_template(template)
        missing = [role for role in REQUIRED_BIPED_ROLES if role not in normalized["roles"]]
        if missing:
            errors.append(f"Biped mode requires these roles: {', '.join(missing)}")
    return errors


def load_template(file_path):
    """Loads a template JSON file.

    Args:
        file_path (str): Template file path.

    Returns:
        dict: Normalized template.

    Raises:
        IOError: If the file cannot be read.
        ValueError: If the content is invalid.
    """
    with open(file_path, "r", encoding="utf-8") as stream:
        data = json.load(stream)
    errors = validate_template(data)
    if errors:
        raise ValueError(f"Invalid skeleton template ({file_path}): {errors[0]}")
    return normalize_template(data)


def save_template(template, file_path):
    """Saves a template as readable JSON.

    Args:
        template (dict): Template data.
        file_path (str): Destination path. Missing folders are created.

    Returns:
        str: Written file path.
    """
    directory = os.path.dirname(os.path.abspath(file_path))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(file_path, "w", encoding="utf-8") as stream:
        json.dump(normalize_template(template), stream, indent=4)
    return file_path


# ------------------------------------------------ Resolution ------------------------------------------------
def split_node_name(node_path):
    """Splits a Maya node path into namespace and base name.

    Args:
        node_path (str): Node name or long DAG path.

    Returns:
        tuple: (namespace, base_name). The namespace is "" when absent.
    """
    short_name = str(node_path).split("|")[-1]
    if ":" in short_name:
        namespace, base_name = short_name.rsplit(":", 1)
        return namespace, base_name
    return "", short_name


def match_candidate(node_path, candidate):
    """Matches a node against a candidate name, allowing a name prefix such as "Character1_".

    Args:
        node_path (str): Node name or path.
        candidate (str): Candidate base name from a template.

    Returns:
        tuple or None: (namespace, prefix) group key when matched, otherwise None.
    """
    namespace, base_name = split_node_name(node_path)
    lower_base = base_name.lower()
    lower_candidate = candidate.lower()
    if lower_base == lower_candidate:
        return namespace, ""
    if lower_base.endswith(lower_candidate):
        prefix = base_name[: len(base_name) - len(candidate)]
        if prefix.endswith("_"):
            return namespace, prefix
    return None


def find_role_matches(role_candidates, node_paths):
    """Finds every node matching a role, grouped by namespace and prefix.

    Args:
        role_candidates (list): Candidate names in priority order.
        node_paths (list): Scene node paths.

    Returns:
        dict: Group key (namespace, prefix) to the best matching node path.
    """
    matches = {}
    for candidate in role_candidates:
        for node_path in node_paths:
            group_key = match_candidate(node_path, candidate)
            if group_key is not None and group_key not in matches:
                matches[group_key] = node_path
    return matches


def resolve_template_roles(template, node_paths, required_roles=None):
    """Resolves template roles to scene nodes.

    When several characters match (different namespaces or prefixes), the group
    resolving the most roles wins and a warning is added.

    Args:
        template (dict): Skeleton template.
        node_paths (list): Candidate scene node paths (for example every joint).
        required_roles (list, optional): Roles reported as missing when unresolved.

    Returns:
        dict: {"roles": {role: path}, "group": str, "missing_required": list,
               "missing_optional": list, "warnings": list}
    """
    template = normalize_template(template)
    node_paths = [str(path) for path in node_paths or []]
    required_roles = list(required_roles if required_roles is not None else REQUIRED_BIPED_ROLES)
    role_matches = {
        role_key: find_role_matches(candidates, node_paths)
        for role_key, candidates in template["roles"].items()
    }
    group_scores = {}
    for matches in role_matches.values():
        for group_key in matches:
            group_scores[group_key] = group_scores.get(group_key, 0) + 1
    warnings = []
    chosen_group = None
    if group_scores:
        ranked_groups = sorted(group_scores.items(), key=lambda item: (-item[1], item[0]))
        chosen_group = ranked_groups[0][0]
        if len(ranked_groups) > 1 and ranked_groups[1][1] == ranked_groups[0][1]:
            warnings.append(
                f'Several characters match this template equally; using "{format_group(chosen_group)}".'
            )
    roles = {}
    for role_key, matches in role_matches.items():
        if chosen_group in matches:
            roles[role_key] = matches[chosen_group]
    missing_required = [role for role in required_roles if role not in roles]
    missing_optional = [role for role in ROLE_KEYS if role not in roles and role not in required_roles]
    return {
        "roles": roles,
        "group": format_group(chosen_group) if chosen_group else "",
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "warnings": warnings,
    }


def format_group(group_key):
    """Formats a (namespace, prefix) group key for messages.

    Args:
        group_key (tuple): Namespace and prefix.

    Returns:
        str: Readable group label such as "hero:Character1_".
    """
    if not group_key:
        return ""
    namespace, prefix = group_key
    label = f"{namespace}:{prefix}" if namespace else prefix
    return label or "<no prefix>"


def detect_builtin_template(node_paths):
    """Finds the built-in template that best matches the scene.

    Args:
        node_paths (list): Scene joint paths.

    Returns:
        tuple: (template_key or None, resolution dict or None).
    """
    best_key = None
    best_resolution = None
    best_count = 0
    for template_key in get_builtin_template_keys():
        resolution = resolve_template_roles(BUILTIN_TEMPLATES[template_key], node_paths)
        resolved_count = len(resolution["roles"])
        if resolution["missing_required"]:
            continue
        if resolved_count > best_count:
            best_key, best_resolution, best_count = template_key, resolution, resolved_count
    return best_key, best_resolution
