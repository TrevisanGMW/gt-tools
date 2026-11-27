"""Settings, portable calibration profiles, and schema rules for Auto Annotate."""

import copy
import json
import math
import os
import re
import statistics
import tempfile
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import parse_qsl, urlsplit

from gt.tools.annotation_tracker import annotation_tracker_model
from gt.tools.annotation_tracker import auto_annotation_rules as rules


PREFS_NAME = "auto_annotation_prefs"
SETTINGS_FORMAT = "auto_annotation"
LEGACY_SETTINGS_FORMAT = "gt_auto_annotation"
SETTINGS_VERSION = 1
PROFILE_VERSION = 2
DEFAULT_IDLE_SPEED = 0.22
DEFAULT_WALK_SPEED = 2.55
DEFAULT_STANDING_CUES = {"pelvis_height": 0.82, "knee_flexion": 65.0, "torso_pitch": 32.0, "torso_roll": 24.0}
PROFILE_NAME_LENGTH = 60
DEFAULT_PROFILE_NAME = "Custom Profile"
FILL_MODES = ("gaps", "overwrite")
CALIBRATION_STATES = ("idle", "walk", "run", "sprint")
VLM_PROVIDERS = {
    "local": ("http://localhost:1234/v1/chat/completions", "qwen2.5-vl-7b-instruct", ""),
    "openai": ("https://api.openai.com/v1/responses", "", "OPENAI_API_KEY"),
    "anthropic": ("https://api.anthropic.com/v1/messages", "", "ANTHROPIC_API_KEY"),
}
DEFAULT_SETTINGS = {
    "use_profile": False,
    "calibration": None,
    "skeleton_mode": "auto",
    "skeleton_root": "",
    "joint_map": {},
    "short_name_fallback": True,
    "show_full_joint_paths": False,
    "pose_field": rules.RANGE_NAME_FIELD,
    "fill_mode": "gaps",
    "auto_save": False,
    "auto_set_quality": True,
    "quality_preset": {},
    "commercial_use": None,
    "file_source_mode": "keep",
    "file_source": "",
    "file_source_pattern": "",
    "file_source_depth": 1,
    "file_source_order": "nearest",
    "file_source_fallback": "none",
    "file_style_source": "vlm",
    "file_style": "",
    "auto_set_clipped": True,
    "auto_set_annotated": True,
    "vlm_mode": "off",
    "vlm_provider": "local",
    "vlm_endpoint": "",
    "vlm_model": "",
    "vlm_key_env": "",
    "vlm_threshold": 0.85,
    "vlm_max_images": 40,
    "vlm_timeout": 90,
    "vlm_local_auto_load": True,
    "vlm_local_eject_other_models": False,
    "allow_remote_vlm": False,
    "vlm_view_side": True,
    "vlm_view_front": True,
    "vlm_view_travel": True,
    "vlm_view_top": True,
    "vlm_poses_per_image": 6,
    "vlm_max_tokens": 16384,
    "vlm_style_threshold": 0.5,
    "vlm_style_forced": True,
    "vlm_style_recheck": True,
    "vlm_context_images": True,
    "vlm_replace_existing": True,
    "vlm_replace_threshold": 0.9,
    "vlm_guidance": (
        "interaction_type describes a character acting on something: carrying, pushing, pulling, climbing, "
        "avoiding, gesturing or sustaining an interaction. Plain walking, running, waiting or standing is not an "
        "interaction, so leave interaction fields out for it. Use navigate only when the character interacts with "
        "something while moving, such as opening a door while passing through it or pushing an obstacle aside."
    ),
    "vlm_log_changes": False,
    "vlm_image_width": 1024,
    "vlm_fields": [
        "style", "context", "stance", "override_style", "interaction_type", "interaction_scope", "interaction_item",
    ],
}
VLM_FIELD_CHOICES = tuple(DEFAULT_SETTINGS["vlm_fields"])

# Typical differences between nearby poses, in leg lengths or degrees.
FEATURE_SCALES = {
    "pelvis_height": 0.12,
    "left_foot_height": 0.10,
    "right_foot_height": 0.10,
    "knee_height": 0.12,
    "knee_flexion": 20.0,
    "thigh_ratio": 0.18,
    "foot_separation": 0.22,
    "foot_forward": 0.20,
    "torso_pitch": 8.0,
    "torso_roll": 8.0,
    "left_hand_reach": 0.20,
    "right_hand_reach": 0.20,
    "hand_separation": 0.25,
    "speed": 0.65,
}


def load_settings():
    """Loads local preferences, copying a legacy linked profile when possible.

    Returns:
        dict: Independent copy of persisted settings and defaults.
    """
    preferences = _maya_preferences()
    if preferences is None:
        from gt.core.io import read_json_dict

        path = _prefs_directory() / f"{PREFS_NAME}.json"
        stored = read_json_dict(str(path)) if path.is_file() else {}
    else:
        stored = preferences.get_raw_preferences()
    if "calibration" not in stored and ("profile_location" in stored or "profile_path" in stored):
        try:
            stored = dict(stored, calibration=read_profile(get_profile_path(stored)))
        except FileNotFoundError:
            pass
        except (OSError, ValueError) as error:
            print(f"[Auto Annotate] Could not import legacy calibration. {error}")
    return normalize_settings(stored, validate_credentials=False)


def reset_settings(calibration=None, use_profile=False, pose_field=None):
    """Restores preferences, optionally retaining embedded calibration.

    Args:
        calibration (dict, optional): Calibration to keep.
        use_profile (bool): Whether to keep using that calibration.
        pose_field (str, optional): Label source of the retained profile.

    Returns:
        dict: Independent default settings.
    """
    defaults = copy.deepcopy(DEFAULT_SETTINGS)
    if calibration is not None:
        defaults.update(calibration=normalize_profile(calibration), use_profile=use_profile)
        if pose_field:
            defaults["pose_field"] = pose_field
        save_settings(defaults)
    else:
        path = _prefs_directory() / f"{PREFS_NAME}.json"
        path.unlink(missing_ok=True)
    return defaults


def save_settings(settings):
    """Persists supported preferences using GT-Tools preferences.

    Args:
        settings (dict): Settings supplied by Annotation Setup.
    """
    values = normalize_settings(settings)
    values.pop("schema", None)
    preferences = _maya_preferences()
    directory = Path(preferences.get_dir_path()) if preferences is not None else _prefs_directory()
    _write_json(directory / f"{PREFS_NAME}.json", values)


def normalize_settings(values, validate_credentials=True):
    """Builds independent Setup settings from a local or exported dictionary.

    Args:
        values (dict): Partial or complete Auto Annotate preferences.
        validate_credentials (bool): Rejects embedded credentials in portable or saved settings.

    Returns:
        dict: Validated preferences over defaults, plus an optional exported schema.
    """
    if not isinstance(values, dict):
        raise ValueError("Auto Annotate settings must be an object.")
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    for key, default in DEFAULT_SETTINGS.items():
        if key not in values:
            continue
        value = values[key]
        if key == "calibration":
            settings[key] = normalize_profile(value) if value is not None else None
            continue
        if key == "commercial_use":
            valid = value is None or type(value) is bool
        elif type(default) is float:
            valid = type(value) in (int, float) and math.isfinite(value)
        else:
            valid = type(value) is type(default)
        if not valid:
            raise ValueError(f"Invalid value for Auto Annotate setting '{key}'.")
        settings[key] = copy.deepcopy(value)
    if settings["calibration"] is not None and "pose_field" not in values:
        settings["pose_field"] = settings["calibration"].get("label_source", "stance")
    if not settings["pose_field"].strip() or settings["pose_field"] == "state":
        raise ValueError("Choose Range names or a schema field other than State for learned labels.")
    if not all(isinstance(role, str) and isinstance(path, str) for role, path in settings["joint_map"].items()):
        raise ValueError("Skeleton mapping must contain joint names or DAG paths.")
    for key, choices in (
        ("skeleton_mode", ("auto", "manual")), ("vlm_mode", ("off", "review", "auto")),
        ("vlm_provider", VLM_PROVIDERS), ("file_style_source", ("keep", "fixed", "vlm")),
        ("fill_mode", FILL_MODES), ("file_source_mode", ("keep", "fixed", "path")),
        ("file_source_order", ("nearest", "outermost")),
        ("file_source_fallback", ("none", "text", "folder")),
    ):
        if settings[key] not in choices:
            raise ValueError(f"Invalid value for Auto Annotate setting '{key}'.")
    if not (
        0 <= settings["vlm_threshold"] <= 1 and 1 <= settings["vlm_max_images"] <= 200
        and 1 <= settings["vlm_timeout"] <= 300 and 3 <= settings["vlm_poses_per_image"] <= 12
        and 512 <= settings["vlm_image_width"] <= 2048
        and (settings["vlm_max_tokens"] == 0 or 256 <= settings["vlm_max_tokens"] <= 65536) and 0 <= settings["vlm_replace_threshold"] <= 1 and 0 <= settings["vlm_style_threshold"] <= 1 and len(settings["vlm_guidance"]) <= 2000
    ):
        raise ValueError("VLM threshold, frame limit, or timeout is outside the supported range.")
    if not 0 <= settings["file_source_depth"] <= 40 or len(settings["file_source"]) > 200:
        raise ValueError("The Source search depth or fixed value is outside the supported range.")
    try:
        validate_source_pattern(settings["file_source_pattern"])
    except re.error as error:
        raise ValueError(f"The Source folder pattern is not a valid regular expression. {error}") from error
    if settings["file_style"].strip().lower() == "none":
        settings["file_style"] = ""
    if not all(field in VLM_FIELD_CHOICES for field in settings["vlm_fields"]):
        raise ValueError("The VLM field list contains an unknown field.")
    if validate_credentials:
        validate_vlm_credentials(settings["vlm_key_env"], settings["vlm_endpoint"])
    if "schema" in values:
        if not isinstance(values["schema"], dict) or not values["schema"]:
            raise ValueError("The exported Annotation Tracker schema is invalid.")
        settings["schema"] = copy.deepcopy(values["schema"])
    return settings


def read_settings_file(path):
    """Reads a portable settings file without touching GT-Tools preferences.

    Args:
        path (str or Path): Exported Auto Annotate settings JSON path.

    Returns:
        dict: Complete settings with embedded calibration and optional schema.
    """
    with Path(path).open(encoding="utf-8-sig") as stream:
        data = json.load(stream)
    if not isinstance(data, dict) or data.get("format") not in (SETTINGS_FORMAT, LEGACY_SETTINGS_FORMAT):
        raise ValueError("Choose an Auto Annotate settings export.")
    if type(data.get("version")) is not int or data["version"] != SETTINGS_VERSION:
        raise ValueError("This Auto Annotate settings version is unsupported.")
    return normalize_settings(data.get("settings"))


def write_settings_file(path, settings):
    """Exports one JSON document with settings, calibration, and the run schema.

    Args:
        path (str or Path): Destination JSON path.
        settings (dict): Current setup and optional active schema.
    """
    data = {"format": SETTINGS_FORMAT, "version": SETTINGS_VERSION, "settings": normalize_settings(settings)}
    _write_json(Path(path), data)


def validate_vlm_credentials(key_name, endpoint=""):
    """Keeps API credentials out of saved VLM preference fields.

    Args:
        key_name (str): Environment variable name, or blank for the provider default.
        endpoint (str, optional): Provider URL without embedded credentials.
    """
    if key_name and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", key_name):
        raise ValueError("Enter an environment variable name such as OPENAI_API_KEY or ANTHROPIC_API_KEY.")
    if endpoint:
        parsed = urlsplit(endpoint)
        secret_parameters = {
            "apikey", "xapikey", "key", "token", "accesstoken", "credential", "password", "secret", "authorization"
        }
        parameters = {re.sub(r"[^a-z]", "", key.lower()) for key, _ in parse_qsl(parsed.query, keep_blank_values=True)}
        if parsed.username is not None or parsed.password is not None or parameters & secret_parameters:
            raise ValueError(
                "Use a provider URL without credentials. Supply the key through its environment variable."
            )


def _maya_preferences():
    """Gets the repository preference reader when Maya is available.

    Returns:
        Prefs or None: GT-Tools preferences, or None in standalone Python.
    """
    try:
        from gt.core.prefs import Prefs
    except ModuleNotFoundError as error:
        if error.name not in ("maya", "maya.cmds"):
            raise
        return None
    return Prefs(PREFS_NAME)


def _prefs_directory():
    """Resolves the GT-Tools Prefs directory in and outside Maya.

    Returns:
        Path: GT-Tools preference directory.
    """
    try:
        from gt.core.prefs import get_prefs_dir
    except ModuleNotFoundError as error:
        if error.name not in ("maya", "maya.cmds"):
            raise
        from gt.utils.system import get_maya_preferences_dir, get_system

        return Path(get_maya_preferences_dir(get_system())) / "gt-tools" / "prefs"
    return Path(get_prefs_dir())


SOURCE_PATTERN_PRESETS = (
    (
        "Three parts, last is 3 digits (whole folder name)",
        r"^[A-Za-z0-9-]+_[A-Za-z0-9-]+_\d{3}.*$", "set-a_walk_001_r21_testing",
    ),
    (
        "Three parts, last is 3 digits (stop after the digits)",
        r"^[A-Za-z0-9-]+_[A-Za-z0-9-]+_\d{3}", "set-a_walk_001_r21_testing",
    ),
    ("Text followed by a number (name_001)", r"^[A-Za-z0-9-]+_\d+", "walkset_012_extra"),
    ("Everything before the first underscore", r"^([^_]+)", "walkset_012_extra"),
    (
        "Everything before a version or run tag (_v001, _r21)",
        r"^(.+?)(?:_[vr]\d+.*)?$", "set-a_walk_001_r21_testing",
    ),
)


def preview_source_preset(pattern, sample):
    """Shows what a preset pattern extracts from a sample folder name.

    Args:
        pattern (str): Regular expression.
        sample (str): Example folder name.

    Returns:
        str: Extracted text.
    """
    return find_source_in_path(f"Z:\\{sample}\\scene.ma", pattern, 1)


def validate_source_pattern(pattern):
    """Checks a Source folder pattern without using it.

    Args:
        pattern (str): Regular expression, or an empty string for the whole folder name.

    Returns:
        Pattern or None: Compiled expression, or None when the pattern is empty.
    """
    if len(pattern) > 300:
        raise re.error("The pattern is longer than 300 characters.")
    return re.compile(pattern) if pattern else None


def find_source_in_path(path, pattern="", max_depth=1, order="nearest"):
    """Finds a Source value in the folders above a scene file.

    Folders are tried from the one next to the file upward. A pattern is searched anywhere inside each folder name,
    so a longer folder name can still yield its matching part. Group 1 is used when the pattern has groups.

    Args:
        path (str): Scene file path.
        pattern (str, optional): Regular expression. An empty pattern uses the whole folder name.
        max_depth (int): Folders above the file to search, or 0 for all of them.
        order (str): ``nearest`` tries the closest folder first. ``outermost`` tries the highest folder first.

    Returns:
        str: Matching text, or an empty string when nothing matches.
    """
    folders = [part for part in re.split(r"[\\/]+", path or "")[:-1] if part and not part.endswith(":")]
    nearest_first = folders[::-1]
    if max_depth:
        nearest_first = nearest_first[:max_depth]
    candidates = nearest_first[::-1] if order == "outermost" else nearest_first
    expression = validate_source_pattern(pattern)
    for folder in candidates:
        if expression is None:
            return folder
        match = expression.search(folder)
        if match:
            groups = [group for group in match.groups() if group]
            return groups[0] if groups else match.group(0)
    return ""


def get_profile_path(settings, project_dir=None):
    """Resolves a legacy calibration link or an explicit runtime override.

    Args:
        settings (dict): Effective profile settings.
        project_dir (str, optional): Base directory for relative batch paths.

    Returns:
        Path: Absolute JSON path.
    """
    if settings.get("profile_location") != "custom":
        return _prefs_directory() / "annotation_data" / "profile.json"
    value = str(settings.get("profile_path") or "").strip()
    if not value:
        raise ValueError("Choose a custom profile JSON file.")
    path = Path(os.path.expandvars(value)).expanduser()
    if not path.is_absolute():
        if not project_dir:
            raise ValueError("Choose an absolute profile path outside Batch Processor.")
        path = Path(project_dir) / path
    return path


def new_profile():
    """Creates an empty portable calibration profile.

    Returns:
        dict: Current profile version and empty pose examples.
    """
    return {"profile_version": PROFILE_VERSION, "poses": {}}


def copy_default_profile():
    """Creates an editable snapshot of the built-in calibration rules.

    Returns:
        dict: Independent profile with default rules and speed thresholds.
    """
    return dict(
        new_profile(),
        label_source=rules.RANGE_NAME_FIELD,
        rules=dict(rules.DEFAULT_RULES),
        locomotion={"idle_max_speed": DEFAULT_IDLE_SPEED, "walk_max_speed": DEFAULT_WALK_SPEED},
    )


def describe_profile(profile, active):
    """Builds a one-line description of the motion cue profile used for a run.

    Args:
        profile (dict or None): Calibration applied to the run.
        active (bool): Whether a custom profile is enabled.

    Returns:
        str: Human-readable profile summary.
    """
    if not active or not profile:
        return "Built-in calibration profile (default rules and speed thresholds)"
    name = profile.get("name") or DEFAULT_PROFILE_NAME
    poses = profile.get("poses", {})
    pose_labels = ", ".join(sorted(poses)) or "none"
    locomotion = profile.get("locomotion", {})
    speeds = ", ".join(f"{key.split('_')[0]} <= {value:g}" for key, value in locomotion.items()) or "default speeds"
    cues = f", {len(profile['pose_cues'])} cues enabled" if "pose_cues" in profile else ""
    return (
        f"Custom calibration profile '{name}': {sum(len(items) for items in poses.values())} pose example(s) "
        f"[{pose_labels}], {speeds}{cues}"
    )


def _legacy_profile(data):
    """Imports compatible calibration statistics from a version 1 profile.

    Args:
        data (dict): Legacy dataset profile data.

    Returns:
        dict: Portable calibration data with measurements in current units.
    """
    profile = new_profile()
    calibration = data.get("calibration") or {}
    scene = data.get("scene") or {}
    thresholds = data.get("thresholds") or {}
    postures = data.get("postures") or {}
    if not all(isinstance(section, dict) for section in (calibration, scene, thresholds, postures)):
        raise ValueError("Legacy annotation profile settings are invalid.")
    length = calibration.get("leg_length") or scene.get("leg_length")
    fps = scene.get("fps", 30)
    if isinstance(length, (int, float)) and length > 0 and isinstance(fps, (int, float)) and fps > 0:
        scale = fps / length
        idle = calibration.get("idle_max_velocity", thresholds.get("idle_max_velocity"))
        bands = calibration.get("locomotion_bands", thresholds.get("locomotion_bands", []))
        walk = next((
            band.get("max_velocity") for band in bands if isinstance(band, dict) and band.get("state") == "walk"
        ), None) if isinstance(bands, list) else None
        if isinstance(idle, (int, float)) and isinstance(walk, (int, float)) and 0 < idle < walk:
            profile["locomotion"] = {"idle_max_speed": idle * scale, "walk_max_speed": walk * scale}
    stance_statistics = postures.get("stance_statistics") or {}
    if not isinstance(stance_statistics, dict):
        raise ValueError("Legacy posture statistics must be a dictionary.")
    for label, descriptors in stance_statistics.items():
        if not isinstance(descriptors, dict):
            continue
        features = {}
        for name in ("pelvis_height", "knee_flexion", "knee_height", "thigh_ratio"):
            values = descriptors.get(name)
            if not isinstance(values, dict):
                continue
            bounds = [values.get(key) for key in ("p05", "median", "p95")]
            if all(type(value) in (int, float) and math.isfinite(value) for value in bounds):
                features[name] = bounds
        pelvis_statistics = descriptors.get("pelvis_height")
        count = pelvis_statistics.get("sample_count", 0) if isinstance(pelvis_statistics, dict) else 0
        if len(features) == 4 and type(count) is int and count > 0:
            profile["poses"][label] = [{"sample_count": count, "features": features}]
    return profile


def normalize_profile(data):
    """Validates a profile and retains only portable measurements.

    Args:
        data (dict): Parsed profile or explicit profile input.

    Returns:
        dict: Validated calibration in the current format.
    """
    if not isinstance(data, dict):
        raise ValueError("An annotation profile must be a JSON object.")
    version = data.get("profile_version")
    if version == 1:
        data = _legacy_profile(data)
    elif version != PROFILE_VERSION:
        raise ValueError(f"Unsupported annotation profile version: {version}.")

    profile = new_profile()
    profile["poses"] = _normalize_examples(data.get("poses", {}))
    if "name" in data:
        if not isinstance(data["name"], str):
            raise ValueError("The calibration profile name must be text.")
        if data["name"].strip():
            profile["name"] = data["name"].strip()[:PROFILE_NAME_LENGTH]
    if "label_source" in data:
        source = data["label_source"]
        if not isinstance(source, str) or not source.strip() or source == "state":
            raise ValueError("The calibration label source is invalid.")
        profile["label_source"] = source
    if "rules" in data:
        profile["rules"] = rules.normalize_rules(data["rules"])
    if "pose_cues" in data:
        cues = data["pose_cues"]
        if not isinstance(cues, list) or not all(isinstance(cue, str) for cue in cues):
            raise ValueError("Enabled pose cues must be a list of names.")
        profile["pose_cues"] = [cue for cue in FEATURE_SCALES if cue in cues]
    if "locomotion_examples" in data:
        profile["locomotion_examples"] = _normalize_examples(data["locomotion_examples"], speed_only=True)

    locomotion = data.get("locomotion")
    if locomotion is not None:
        idle = locomotion.get("idle_max_speed") if isinstance(locomotion, dict) else None
        walk = locomotion.get("walk_max_speed") if isinstance(locomotion, dict) else None
        if not all(type(value) in (int, float) and math.isfinite(value) for value in (idle, walk)):
            raise ValueError("Locomotion thresholds must contain finite idle and walk speeds.")
        if not 0 < idle < walk:
            raise ValueError("Locomotion thresholds must increase from idle to walk.")
        profile["locomotion"] = {"idle_max_speed": idle, "walk_max_speed": walk}
        if "run_max_speed" in locomotion:
            run = locomotion["run_max_speed"]
            if type(run) not in (int, float) or not math.isfinite(run) or run <= walk:
                raise ValueError("The calibrated run limit must be higher than the walk limit.")
            profile["locomotion"]["run_max_speed"] = run
    return profile


def _normalize_examples(groups, speed_only=False):
    """Validates example groups and drops fields outside the portable format.

    Args:
        groups (dict): Labels mapped to example summaries.
        speed_only (bool): Keeps only speed samples for locomotion calibration.

    Returns:
        dict: Normalized examples grouped by label.
    """
    if not isinstance(groups, dict):
        raise ValueError("Calibration samples must be a mapping of labels to examples.")
    result = {}
    for label, examples in groups.items():
        if not isinstance(label, str) or not label.strip() or not isinstance(examples, list):
            raise ValueError("Calibration labels must each contain a list of examples.")
        if speed_only and label not in CALIBRATION_STATES:
            continue
        normalized = []
        for example in examples:
            if not isinstance(example, dict) or not isinstance(example.get("features"), dict):
                raise ValueError(f"Invalid calibration example for '{label}'.")
            features = {}
            for name, limits in example["features"].items():
                if name not in FEATURE_SCALES or (speed_only and name != "speed"):
                    continue
                if (
                    not isinstance(limits, list)
                    or len(limits) != 3
                    or not all(type(value) in (int, float) and math.isfinite(value) for value in limits)
                    or limits != sorted(limits)
                ):
                    raise ValueError(f"Invalid calibration values for '{label}' ({name}).")
                features[name] = list(limits)
            sample_count = example.get("sample_count")
            if type(sample_count) is not int or sample_count < 1 or not features:
                raise ValueError(f"Missing calibration samples for '{label}'.")
            entry = {"sample_count": sample_count, "features": features}
            if not speed_only:
                if "threshold" in example:
                    threshold = example["threshold"]
                    if type(threshold) not in (int, float) or not math.isfinite(threshold) or not 0 <= threshold <= 4:
                        raise ValueError(f"Invalid match threshold for '{label}'.")
                    entry["threshold"] = threshold
                if "minimum_frames" in example:
                    minimum = example["minimum_frames"]
                    if type(minimum) is not int or not 1 <= minimum <= 10000:
                        raise ValueError(f"Invalid minimum frame count for '{label}'.")
                    entry["minimum_frames"] = minimum
                if "suffix" in example:
                    if not isinstance(example["suffix"], str) or len(example["suffix"].strip()) > 100:
                        raise ValueError(f"Invalid range suffix for '{label}'.")
                    entry["suffix"] = example["suffix"].strip()
                if example.get("state") == "activity":
                    entry["state"] = "activity"
            normalized.append(entry)
        if normalized:
            result[label] = normalized
    return result


def read_profile(path):
    """Reads a portable JSON profile.

    Args:
        path (str or Path): Profile location.

    Returns:
        dict: Validated calibration.
    """
    with Path(path).open(encoding="utf-8-sig") as profile_file:
        return normalize_profile(json.load(profile_file))


def write_profile(path, profile):
    """Exports a standalone calibration snapshot.

    Args:
        path (str or Path): Destination JSON file.
        profile (dict): Embedded calibration to export.
    """
    _write_json(Path(path), normalize_profile(profile))


def has_calibration(profile):
    """Reports whether a profile contains measurements or learned thresholds.

    Args:
        profile (dict or None): Embedded calibration.

    Returns:
        bool: True when the profile contains examples or custom detection settings.
    """
    return bool(profile and ("rules" in profile or any(
        profile.get(key) for key in ("poses", "locomotion_examples", "locomotion")
    )))


def get_training_labels(item, source, field=None):
    """Gets the pose and speed labels that can be learned from a Tracker range.

    Args:
        item (dict): Stored Tracker range and metadata.
        source (str): Range names or the schema field for custom pose labels.
        field (dict, optional): Schema definition when using a named field.

    Returns:
        tuple: Learnable pose label and locomotion state, or empty strings.
    """
    data = item.get("custom_data", {})
    name = item.get("name", "").strip()
    stored_state = data.get("state")
    state = stored_state or name.lower()
    state = state if state in CALIBRATION_STATES else ""
    if source == rules.RANGE_NAME_FIELD:
        if isinstance(stored_state, str) and name.lower().startswith(f"{stored_state.lower()}_"):
            name = name[len(stored_state) + 1:]
        generic = {"range", "idle", "enter", "exit", "stand", "none", "---", *rules.LOCOMOTION_STATES}
        pose = name if name.lower() not in generic else ""
    else:
        value = data.get(source)
        pose = value.strip() if value != "none" and supports_value(field, value) else ""
    if not pose and is_activity_example(item):
        pose = name or "activity"
    return pose, state


def is_activity_example(item):
    """Checks for a deliberate activity label in a range's State field.

    Args:
        item (dict): Stored Tracker range.

    Returns:
        bool: True when training should assign the activity state on a match.
    """
    return item.get("custom_data", {}).get("state") == "activity"


@contextmanager
def _lock_profile(path):
    """Guards a profile update against a second Maya session.

    Args:
        path (Path): Destination JSON file.

    Yields:
        None: The caller may read and update the profile.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.with_suffix(f"{path.suffix}.lock").open("a+b") as lock:
        try:
            lock.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise OSError("This profile is being updated in another session. Try calibrating again.") from error
        yield


def _write_json(path, data):
    """Replaces a destination JSON file after writing the complete payload.

    Args:
        path (Path): Destination JSON path.
        data (dict): Validated portable data.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent, mode="w", encoding="utf-8", suffix=".tmp", delete=False
        ) as profile_file:
            temporary_path = Path(profile_file.name)
            json.dump(data, profile_file, indent=2, ensure_ascii=False, allow_nan=False)
            profile_file.write("\n")
            profile_file.flush()
            os.fsync(profile_file.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _update_locomotion_thresholds(profile):
    """Adjusts speed bands when neighboring labels have distinct measurements.

    Args:
        profile (dict): Profile that owns the accumulated examples and thresholds.
    """
    summaries = {}
    for state, examples in profile.get("locomotion_examples", {}).items():
        if sum(example["sample_count"] for example in examples) >= 8:
            speeds = [example["features"]["speed"] for example in examples]
            lower = statistics.median(row[0] for row in speeds)
            upper = statistics.median(row[2] for row in speeds)
            summaries[state] = (lower, upper)
    old = profile.get("locomotion", {})
    thresholds = dict({"idle_max_speed": DEFAULT_IDLE_SPEED, "walk_max_speed": DEFAULT_WALK_SPEED}, **old)
    learned = {}
    for low, high, key in (
        ("idle", "walk", "idle_max_speed"), ("walk", "run", "walk_max_speed"), ("run", "sprint", "run_max_speed"),
    ):
        if low in summaries and high in summaries and 0 <= summaries[low][1] < summaries[high][0]:
            learned[key] = round((summaries[low][1] + summaries[high][0]) / 2, 5)
    thresholds.update(learned)
    if learned and 0 < thresholds["idle_max_speed"] < thresholds["walk_max_speed"]:
        if thresholds.get("run_max_speed", math.inf) <= thresholds["walk_max_speed"]:
            thresholds.pop("run_max_speed")
        profile["locomotion"] = thresholds


def refresh_locomotion(profile):
    """Rebuilds speed limits from the remaining speed cues after one was deleted.

    Args:
        profile (dict): Calibration profile, changed in place. Limits fall back to the defaults when no speed cue
            can set them.
    """
    profile.pop("locomotion", None)
    if profile.get("locomotion_examples"):
        _update_locomotion_thresholds(profile)


def merge_profile_examples(profile, examples, locomotion_examples=None):
    """Adds distinct measurements to a copy of embedded calibration data.

    Args:
        profile (dict or None): Existing embedded calibration.
        examples (dict): Pose labels mapped to new normalized examples.
        locomotion_examples (dict, optional): State labels with normalized speed summaries.

    Returns:
        dict: Updated portable calibration.
    """
    profile = normalize_profile(profile) if profile is not None else new_profile()
    for section, new_examples in (("poses", examples), ("locomotion_examples", locomotion_examples)):
        if not new_examples:
            continue
        stored = profile.setdefault(section, {})
        for label, label_examples in new_examples.items():
            existing = stored.setdefault(label, [])
            for example in label_examples:
                duplicate = next((
                    saved for saved in existing
                    if saved["features"] == example["features"] and saved["sample_count"] == example["sample_count"]
                ), None)
                if duplicate is None:
                    existing.append(example)
                elif example.get("state") == "activity":
                    duplicate["state"] = "activity"
    profile = normalize_profile(profile)
    if locomotion_examples:
        _update_locomotion_thresholds(profile)
    return profile


def add_profile_examples(path, examples, locomotion_examples=None):
    """Appends distinct examples and atomically saves a calibration profile.

    Args:
        path (Path): Destination JSON file.
        examples (dict): Pose labels mapped to new normalized examples.
        locomotion_examples (dict, optional): State labels with normalized speed summaries.

    Returns:
        dict: The saved profile.
    """
    with _lock_profile(path):
        profile = new_profile()
        if path.exists():
            with path.open(encoding="utf-8") as profile_file:
                current = json.load(profile_file)
            profile = normalize_profile(current)
            if current.get("profile_version") != PROFILE_VERSION:
                raise ValueError(
                    "Choose a new JSON file for calibration. The selected profile uses the old format."
                )
        profile = merge_profile_examples(profile, examples, locomotion_examples)
        _write_json(path, profile)
        return profile


def summarize_example(descriptors, feature_names=None):
    """Summarizes the measured cues of a labeled calibration range.

    Args:
        descriptors (list): Normalized per-frame pose cues.
        feature_names (tuple, optional): Features to include in the example.

    Returns:
        dict: Sample count and 10th, 50th, and 90th percentile per feature.
    """
    features = {}
    for name in feature_names or FEATURE_SCALES:
        values = sorted(sample[name] for sample in descriptors if name in sample)
        if values:
            last = len(values) - 1
            features[name] = [
                round(values[round(last * 0.1)], 5),
                round(statistics.median(values), 5),
                round(values[round(last * 0.9)], 5),
            ]
    return {"sample_count": len(descriptors), "features": features}


def get_schema_fields(schema, section):
    """Indexes named schema fields for validation and generation.

    Args:
        schema (dict): Active Annotation Tracker schema.
        section (str): Schema section name.

    Returns:
        dict: Fields keyed by field name.
    """
    return {
        field["name"]: field
        for field in annotation_tracker_model.flatten_schema_items(schema.get(section, []))
        if field.get("name")
    }


def supports_value(field, value):
    """Checks whether a generated value fits a schema field.

    Args:
        field (dict or None): Schema definition.
        value (object): Candidate field value.

    Returns:
        bool: Whether the type, options, and bounds permit the value.
    """
    if not field:
        return False
    kind = field.get("type")
    if kind == "enum":
        return isinstance(value, str) and value in field.get("options", [])
    if kind == "string":
        return isinstance(value, str) and bool(value.strip())
    if kind == "integer":
        return (
            type(value) is int
            and field.get("minimum", value) <= value <= field.get("maximum", value)
        )
    return kind == "boolean" and type(value) is bool


def is_empty(value):
    """Checks whether an annotation field is empty.

    Args:
        value (object): Stored annotation value.

    Returns:
        bool: Whether an automation can fill the value.
    """
    return value is None or (isinstance(value, str) and value.strip() in ("", "---"))


def clear_ranges(ranges, start, end):
    """Removes unlocked ranges from a frame span, keeping any parts outside it.

    Args:
        ranges (list): Tracker range dictionaries.
        start (int): First frame to clear.
        end (int): Last frame to clear.

    Returns:
        tuple: Remaining ranges and the number of ranges that were replaced.
    """
    kept = []
    replaced = 0
    for item in ranges:
        if item.get("locked") or item["end"] < start or item["start"] > end:
            kept.append(item)
            continue
        replaced += 1
        if item["start"] < start:
            kept.append(dict(item, end=start - 1))
        if item["end"] > end:
            right = dict(item, start=end + 1)
            if item["start"] < start:
                right.pop("id", None)
            kept.append(right)
    return kept, replaced


def uncovered_spans(ranges, start, end):
    """Finds inclusive gaps without expanding the range into a set of frames.

    Args:
        ranges (list): Tracker range dictionaries.
        start (int): First frame to check.
        end (int): Last frame to check.

    Returns:
        list: Inclusive frame pairs for each gap.
    """
    cursor = start
    gaps = []
    for item in sorted(ranges, key=lambda item: item["start"]):
        if item["end"] < cursor:
            continue
        if item["start"] > end:
            break
        if item["start"] > cursor:
            gaps.append((cursor, item["start"] - 1))
        cursor = max(cursor, item["end"] + 1)
    if cursor <= end:
        gaps.append((cursor, end))
    return gaps


def validate_annotation(schema, file_data, ranges, start, end):
    """Checks Tracker schema requirements and full playback coverage.

    Args:
        schema (dict): Active schema.
        file_data (dict): Candidate scene file metadata.
        ranges (list): Candidate scene ranges.
        start (int): First playback frame.
        end (int): Last playback frame.

    Returns:
        list: Diagnostics for incomplete or invalid annotations.
    """
    if not schema:
        return ["No schema loaded."]
    validation_schema = dict(schema, validation=dict(schema.get("validation", {}), full_coverage=False))
    items = [
        SimpleNamespace(
            start=item["start"], end=item["end"], display_name=item["name"], custom_data=item["custom_data"]
        )
        for item in ranges
    ]
    errors = annotation_tracker_model.collect_validation_errors(validation_schema, items, file_data, start, end)
    if not schema.get("validation", {}).get("allow_overlap", True):
        ordered = sorted(items, key=lambda item: item.start)
        for left, right in zip(ordered, ordered[1:]):
            if left.end == right.start:
                errors.append(f"Range '{left.display_name}' and '{right.display_name}' share frame {left.end}.")
    gaps = uncovered_spans(ranges, start, end)
    if gaps:
        display = ", ".join(f"{first}-{last}" for first, last in gaps[:5])
        suffix = f" and {len(gaps) - 5} more" if len(gaps) > 5 else ""
        errors.append(f"Uncovered playback frames: {display}{suffix}.")
    range_fields = get_schema_fields(schema, "frame_range")
    sections = [("File", get_schema_fields(schema, "file_level"), file_data)]
    sections.extend((f"Range '{item.display_name}'", range_fields, item.custom_data) for item in items)
    for label, fields, values in sections:
        for name, field in fields.items():
            value = values.get(name)
            if field.get("type") in ("enum", "boolean", "integer", "string"):
                if not is_empty(value) and not supports_value(field, value):
                    errors.append(f"{label} has an invalid value for '{name}'.")
    return errors
