"""
Motion Evaluation Presets - Check registry, defaults, and override-only preset storage.

A preset stores only the values that differ from the defaults, so improved
defaults in future versions still reach every untouched setting.

Preset layout (stored):
    {
        "schema": "motion_eval_preset",
        "version": 1,
        "name": "Default",
        "mode": "general",
        "settings": {"overall_fail_below": 40},
        "checks": {"foot_slide": {"fail_below": 30, "parameters": {"slide_speed": 1.0}}}
    }
"""

from .checks_base import ParameterSpec, MODE_GENERAL, MODE_VALUES
from .checks_general import GENERAL_CHECKS
from .checks_biped import BIPED_CHECKS
from .checks_limits import LIMIT_CHECKS
from .checks_pose import POSE_CHECKS
import hashlib
import copy
import json
import os
import re

PRESET_SCHEMA = "motion_eval_preset"
PRESET_VERSION = 1
DEFAULT_PRESET_NAME = "Default"

SCORE_METHOD_PENALTY_SUM = "penalty_sum"
SCORE_METHOD_WEIGHTED_AVERAGE = "weighted_average"
SCORE_METHOD_MINIMUM = "minimum"
SCORE_METHODS = [SCORE_METHOD_PENALTY_SUM, SCORE_METHOD_WEIGHTED_AVERAGE, SCORE_METHOD_MINIMUM]
GROUND_MODES = ["auto", "fixed"]

CHECK_DEFINITIONS = list(GENERAL_CHECKS) + list(BIPED_CHECKS) + list(LIMIT_CHECKS) + list(POSE_CHECKS)
CHECKS_BY_KEY = {check.key: check for check in CHECK_DEFINITIONS}

GLOBAL_PARAMETERS = [
    ParameterSpec("score_method", "Score Method", SCORE_METHOD_PENALTY_SUM,
                  tooltip=("How the check scores combine into the overall score:\n"
                           "penalty_sum: 100 minus every weighted check deficit (strict, default).\n"
                           "weighted_average: weighted mean of the check scores (lenient).\n"
                           "minimum: the lowest check score."),
                  choices=SCORE_METHODS),
    ParameterSpec("overall_warn_below", "Warn Below", 80, 0, 100,
                  "Overall score below which the result is a warning.\n"
                  "A single check can also warn on its own (see the Warn < column)."),
    ParameterSpec("overall_fail_below", "Fail Below", 50, 0, 100,
                  "Overall score below which the result fails.\n"
                  "0 never fails on the overall score; checks can still fail on their own."),
    ParameterSpec("min_issue_frames", "Min Issue Frames", 1, 1, 600,
                  "Ignore issues shorter than this many frames, in every check.\n"
                  "Raise it to forgive one-frame glitches."),
    ParameterSpec("ignore_ranges", "Ignore Frames", "",
                  tooltip="Frames left out of every check, for example \"10-24, 80\".\n"
                          "Use it for intentional actions such as a teleport or a cut."),
    ParameterSpec("contact_height_ratio", "Contact Height", 0.06, 0.005, 1.0,
                  "Biped only. Height above the floor where a foot stops touching the ground,\n"
                  "as a ratio of the leg length (0.06 = 6% of the leg, about 5 cm on an adult)."),
    ParameterSpec("contact_min_base_speed", "Contact Speed", 0.5, 0.01, 100.0,
                  "Biped only. Lowest character speed (leg lengths per second) used to judge\n"
                  "whether a foot moves too fast to be planted. Keeps idles from looking airborne."),
    ParameterSpec("ground_mode", "Ground Mode", "auto",
                  tooltip=("Biped only. How Ground Penetration finds the ground:\n"
                           "auto: the typical height of each planted foot joint (works on slopes and offsets).\n"
                           "fixed: the Ground Height value."),
                  choices=GROUND_MODES),
    ParameterSpec("ground_height", "Ground Height", 0.0, -1000000.0, 1000000.0,
                  "Biped only. Ground height in scene units along the up axis.\n"
                  "Used when Ground Mode is fixed."),
]
GLOBAL_PARAMETERS_BY_KEY = {parameter.key: parameter for parameter in GLOBAL_PARAMETERS}

SCORING_PARAMETERS = [
    ParameterSpec("enabled", "Enabled", True, tooltip="Run this check."),
    ParameterSpec("weight", "Weight", 1.0, 0.0, 10.0,
                  "How much this check counts in the overall score.\n0 still reports the check but ignores it."),
    ParameterSpec("warn_below", "Warn Below", 85, 0, 100, "The check warns when its score is below this value."),
    ParameterSpec("fail_below", "Fail Below", 50, 0, 100,
                  "The check fails (and fails the whole result) when its score is below this value.\n"
                  "0 = this check can only warn."),
    ParameterSpec("allow_failure", "Allow Failure", False,
                  tooltip="Turn this check's failures into warnings,\nso it can never fail the result on its own."),
    ParameterSpec("event_penalty", "Event Penalty", 0.0, 0.0, 100.0,
                  "Points removed for every separate issue (a run of flagged frames)."),
    ParameterSpec("frame_penalty", "Frame Penalty", 2.0, 0.0, 100.0,
                  "Points removed per percent of the clip flagged by this check.\n"
                  "2 means a check that flags 10% of the frames loses 20 points."),
]
SCORING_PARAMETERS_BY_KEY = {parameter.key: parameter for parameter in SCORING_PARAMETERS}


# ------------------------------------------------ Registry ------------------------------------------------
def get_check(check_key):
    """Gets a check definition.

    Args:
        check_key (str): Check key.

    Returns:
        CheckDefinition or None: Definition when registered.
    """
    return CHECKS_BY_KEY.get(check_key)


def get_checks_for_mode(mode):
    """Gets the checks that run in a mode, in display order.

    Args:
        mode (str): Evaluation mode.

    Returns:
        list: CheckDefinition objects.
    """
    return [check for check in CHECK_DEFINITIONS if check.is_available_in_mode(mode)]


def get_mode_display_label(mode):
    """Builds a mode label with its number of checks, for example "General (9 checks)".

    Args:
        mode (str): Evaluation mode.

    Returns:
        str: Display label.
    """
    from .checks_base import MODE_LABELS

    return f"{MODE_LABELS.get(mode, mode)} ({len(get_checks_for_mode(mode))} checks)"


def get_mode_check_summary(mode):
    """Describes which check groups run in a mode, for example "9 General + 10 Biped checks".

    Args:
        mode (str): Evaluation mode.

    Returns:
        str: Readable summary.
    """
    from .checks_base import MODE_LABELS

    counts = {}
    for check in get_checks_for_mode(mode):
        counts[check.mode] = counts.get(check.mode, 0) + 1
    parts = [f"{count} {MODE_LABELS.get(check_mode, check_mode)}" for check_mode, count in counts.items()]
    return f"{' + '.join(parts)} checks"


def get_check_defaults(check_key):
    """Gets every default value of a check.

    Args:
        check_key (str): Check key.

    Returns:
        dict: Scoring defaults plus a "parameters" dictionary.
    """
    check = CHECKS_BY_KEY[check_key]
    defaults = check.get_scoring_defaults()
    defaults["parameters"] = check.get_parameter_defaults()
    return defaults


def get_global_defaults():
    """Gets the default global settings.

    Returns:
        dict: Global parameter defaults.
    """
    return {parameter.key: parameter.default for parameter in GLOBAL_PARAMETERS}


def create_preset(name=DEFAULT_PRESET_NAME, mode=MODE_GENERAL):
    """Creates an empty (all-default) preset.

    Args:
        name (str): Preset name.
        mode (str): Evaluation mode.

    Returns:
        dict: Stored preset layout.
    """
    return {
        "schema": PRESET_SCHEMA,
        "version": PRESET_VERSION,
        "name": name,
        "mode": mode if mode in MODE_VALUES else MODE_GENERAL,
        "settings": {},
        "checks": {},
    }


DEFAULT_PRESET = create_preset()


# ------------------------------------------------ Resolve / Compact ------------------------------------------------
def resolve_preset(preset):
    """Merges preset overrides onto the defaults and validates every value.

    Args:
        preset (dict): Stored (override-only) or already resolved preset.

    Returns:
        dict: Fully populated preset with "settings" and "checks" for every registered check.
    """
    preset = preset if isinstance(preset, dict) else {}
    mode = preset.get("mode") if preset.get("mode") in MODE_VALUES else MODE_GENERAL
    raw_settings = preset.get("settings") if isinstance(preset.get("settings"), dict) else {}
    settings = {}
    for parameter in GLOBAL_PARAMETERS:
        settings[parameter.key] = parameter.coerce(raw_settings.get(parameter.key, parameter.default))
    raw_checks = preset.get("checks") if isinstance(preset.get("checks"), dict) else {}
    checks = {}
    for check in CHECK_DEFINITIONS:
        raw_check = raw_checks.get(check.key) if isinstance(raw_checks.get(check.key), dict) else {}
        resolved = {}
        for key, default in check.get_scoring_defaults().items():
            resolved[key] = SCORING_PARAMETERS_BY_KEY[key].coerce(raw_check.get(key, default))
        raw_parameters = raw_check.get("parameters") if isinstance(raw_check.get("parameters"), dict) else {}
        resolved["parameters"] = {
            parameter.key: parameter.coerce(raw_parameters.get(parameter.key, parameter.default))
            for parameter in check.parameters
        }
        checks[check.key] = resolved
    return {
        "schema": PRESET_SCHEMA,
        "version": PRESET_VERSION,
        "name": str(preset.get("name") or DEFAULT_PRESET_NAME),
        "mode": mode,
        "settings": settings,
        "checks": checks,
    }


def values_equal(value_a, value_b):
    """Compares preset values, tolerating float rounding.

    Args:
        value_a (object): First value.
        value_b (object): Second value.

    Returns:
        bool: True when equal.
    """
    if isinstance(value_a, float) or isinstance(value_b, float):
        try:
            return abs(float(value_a) - float(value_b)) <= 1e-9
        except (TypeError, ValueError):
            return False
    return value_a == value_b


def compact_preset(preset):
    """Keeps only the values that differ from the defaults.

    Args:
        preset (dict): Stored or resolved preset.

    Returns:
        dict: Override-only preset suitable for storage.
    """
    resolved = resolve_preset(preset)
    compact = create_preset(name=resolved["name"], mode=resolved["mode"])
    for key, default in get_global_defaults().items():
        if not values_equal(resolved["settings"][key], default):
            compact["settings"][key] = resolved["settings"][key]
    for check in CHECK_DEFINITIONS:
        defaults = get_check_defaults(check.key)
        resolved_check = resolved["checks"][check.key]
        overrides = {}
        for key, default in defaults.items():
            if key == "parameters":
                continue
            if not values_equal(resolved_check[key], default):
                overrides[key] = resolved_check[key]
        parameter_overrides = {
            key: value
            for key, value in resolved_check["parameters"].items()
            if not values_equal(value, defaults["parameters"][key])
        }
        if parameter_overrides:
            overrides["parameters"] = parameter_overrides
        if overrides:
            compact["checks"][check.key] = overrides
    return compact


def count_overrides(preset):
    """Counts the values that differ from the defaults.

    Args:
        preset (dict): Stored or resolved preset.

    Returns:
        int: Number of changed values.
    """
    compact = compact_preset(preset)
    total = len(compact["settings"])
    for overrides in compact["checks"].values():
        total += len([key for key in overrides if key != "parameters"])
        total += len(overrides.get("parameters", {}))
    return total


def set_check_value(preset, check_key, key, value):
    """Sets one check value (scoring setting or detection parameter) and returns a compact preset.

    Args:
        preset (dict): Stored or resolved preset.
        check_key (str): Check key.
        key (str): Scoring key or detection parameter key.
        value (object): New value.

    Returns:
        dict: Updated compact preset.
    """
    resolved = resolve_preset(preset)
    check_values = resolved["checks"][check_key]
    if key in SCORING_PARAMETERS_BY_KEY:
        check_values[key] = SCORING_PARAMETERS_BY_KEY[key].coerce(value)
    else:
        specs = {parameter.key: parameter for parameter in CHECKS_BY_KEY[check_key].parameters}
        if key not in specs:
            raise KeyError(f'Unknown parameter "{key}" for check "{check_key}".')
        check_values["parameters"][key] = specs[key].coerce(value)
    return compact_preset(resolved)


def set_global_value(preset, key, value):
    """Sets one global setting and returns a compact preset.

    Args:
        preset (dict): Stored or resolved preset.
        key (str): Global setting key.
        value (object): New value.

    Returns:
        dict: Updated compact preset.
    """
    resolved = resolve_preset(preset)
    resolved["settings"][key] = GLOBAL_PARAMETERS_BY_KEY[key].coerce(value)
    return compact_preset(resolved)


def reset_check(preset, check_key):
    """Restores one check to its defaults.

    Args:
        preset (dict): Stored or resolved preset.
        check_key (str): Check key.

    Returns:
        dict: Updated compact preset.
    """
    compact = compact_preset(preset)
    compact["checks"].pop(check_key, None)
    return compact


# ------------------------------------------------ Helpers ------------------------------------------------
def parse_frame_ranges(text):
    """Parses frame ranges such as "10-24, 80".

    Args:
        text (str): Comma or space separated frames and ranges.

    Returns:
        list: Inclusive [start, end] frame spans.

    Raises:
        ValueError: If a token is not a frame or range.
    """
    ranges = []
    for token in re.split(r"[,;\s]+", str(text or "").strip()):
        if not token:
            continue
        match = re.fullmatch(r"(-?\d+)(?:(?:-|:|\.\.)(-?\d+))?", token)
        if not match:
            raise ValueError(f'Invalid frame range "{token}". Use frames like "12" or ranges like "10-24".')
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) is not None else start
        ranges.append([min(start, end), max(start, end)])
    return ranges


def validate_preset(preset):
    """Validates a preset before running.

    Args:
        preset (dict): Stored or resolved preset.

    Returns:
        list: Error messages. Empty when valid.
    """
    errors = []
    if not isinstance(preset, dict):
        return ["Evaluation preset must be a dictionary."]
    schema = preset.get("schema")
    if schema and not str(schema).endswith(PRESET_SCHEMA):
        errors.append(f'Unexpected evaluation preset schema "{schema}".')
    if preset.get("mode") and preset.get("mode") not in MODE_VALUES:
        errors.append(f'Unknown evaluation mode "{preset.get("mode")}".')
    resolved = resolve_preset(preset)
    try:
        parse_frame_ranges(resolved["settings"]["ignore_ranges"])
    except ValueError as exception:
        errors.append(str(exception))
    enabled_checks = [
        check.key for check in get_checks_for_mode(resolved["mode"]) if resolved["checks"][check.key]["enabled"]
    ]
    if not enabled_checks:
        errors.append("Enable at least one check for the selected mode.")
    return errors


def get_settings_hash(preset, template=None):
    """Builds a short hash identifying the settings that produced a score.

    Args:
        preset (dict): Stored or resolved preset.
        template (dict, optional): Skeleton template used.

    Returns:
        str: First 12 characters of a SHA-1 digest.
    """
    payload = {"preset": compact_preset(preset), "template": (template or {}).get("roles", {})}
    text = json.dumps(payload, sort_keys=True)
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def load_preset(file_path):
    """Loads a preset JSON file.

    Args:
        file_path (str): Preset file path.

    Returns:
        dict: Compact preset.

    Raises:
        IOError: If the file cannot be read.
        ValueError: If the content is invalid.
    """
    with open(file_path, "r", encoding="utf-8") as stream:
        data = json.load(stream)
    errors = [error for error in validate_preset(data) if "Enable at least one" not in error]
    if errors:
        raise ValueError(f"Invalid evaluation preset ({file_path}): {errors[0]}")
    return compact_preset(data)


def save_preset(preset, file_path):
    """Saves a preset as readable, override-only JSON.

    Args:
        preset (dict): Stored or resolved preset.
        file_path (str): Destination path. Missing folders are created.

    Returns:
        str: Written file path.
    """
    directory = os.path.dirname(os.path.abspath(file_path))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory)
    with open(file_path, "w", encoding="utf-8") as stream:
        json.dump(compact_preset(preset), stream, indent=4)
    return file_path


def copy_preset(preset):
    """Deep copies a preset.

    Args:
        preset (dict): Preset to copy.

    Returns:
        dict: Independent copy.
    """
    return copy.deepcopy(preset)
