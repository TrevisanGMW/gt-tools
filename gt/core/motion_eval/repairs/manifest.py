"""
Patch manifest: a JSON file that says which take gets which repair steps.

    {
        "schema": "motion_eval_patches",
        "version": 1,
        "template": "data/custom_skeleton.json",   # optional skeleton (path or built-in key)
        "on_error": "warn",                         # "warn" keeps going, "fail" raises
        "takes": {
            "walk_042_v003": {
                "seed": 4711,                       # optional fingerprint
                "frame_range": [0, 311],            # optional fingerprint
                "note": "left foot slide 120-141",
                "steps": [
                    {"fix": "foot_lock", "preset": "contact", "frames": [120, 141]},
                    {"script": "custom/walk_042_v003.py", "frames": [200, 215], "params": {}}
                ]
            }
        }
    }

Relative paths are relative to the manifest's folder. Pure module: no scene access.
"""

import json
import os

from . import registry

SCHEMA = "motion_eval_patches"
VERSION = 1
ON_ERROR_VALUES = ("warn", "fail")


def create_manifest(template="", on_error="warn"):
    """Creates an empty manifest.

    Args:
        template (str): Skeleton template path or built-in key.
        on_error (str): "warn" or "fail".

    Returns:
        dict: Manifest.
    """
    return {"schema": SCHEMA, "version": VERSION, "template": template, "on_error": on_error, "takes": {}}


def load_manifest(file_path):
    """Loads a manifest, returning an empty one when the file is missing.

    Args:
        file_path (str): Manifest path.

    Returns:
        dict: Manifest.

    Raises:
        ValueError: When the file exists but is not a manifest.
    """
    if not file_path or not os.path.isfile(file_path):
        return create_manifest()
    with open(file_path, "r", encoding="utf-8") as stream:
        data = json.load(stream)
    if not isinstance(data, dict) or not isinstance(data.get("takes"), dict):
        raise ValueError(f'Not a patch manifest (no "takes" object): {file_path}')
    return data


def save_manifest(manifest, file_path):
    """Saves a manifest as readable JSON.

    Args:
        manifest (dict): Manifest.
        file_path (str): Destination path.
    """
    directory = os.path.dirname(os.path.abspath(file_path))
    os.makedirs(directory, exist_ok=True)
    temporary_path = f"{file_path}.tmp"
    with open(temporary_path, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(manifest, stream, indent=2, ensure_ascii=False)
        stream.write("\n")
    os.replace(temporary_path, file_path)


def find_take(manifest, take_names):
    """Finds the entry of the first matching take name (case-insensitive).

    Args:
        manifest (dict): Manifest.
        take_names (list): Candidate names (file stems), in priority order.

    Returns:
        tuple: (take name as stored, entry), or (None, None).
    """
    stored = dict((str(name).lower(), name) for name in (manifest.get("takes") or {}))
    for take_name in take_names:
        key = stored.get(str(take_name or "").lower())
        if key is not None:
            return key, manifest["takes"][key]
    return None, None


def set_take(manifest, take_name, entry):
    """Adds or replaces a take entry (replacing any spelling of the same name).

    Args:
        manifest (dict): Manifest, changed in place.
        take_name (str): Take name.
        entry (dict): Take entry.
    """
    remove_take(manifest, take_name)
    manifest.setdefault("takes", {})[take_name] = entry


def remove_take(manifest, take_name):
    """Removes a take entry.

    Args:
        manifest (dict): Manifest, changed in place.
        take_name (str): Take name (any case).

    Returns:
        bool: True when an entry was removed.
    """
    takes = manifest.setdefault("takes", {})
    for name in list(takes):
        if name.lower() == str(take_name).lower():
            del takes[name]
            return True
    return False


def resolve_path(path, base_dir):
    """Resolves a manifest path against the manifest folder.

    Args:
        path (str): Absolute or relative path.
        base_dir (str): Manifest folder.

    Returns:
        str: Absolute path.
    """
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(base_dir, path))


def check_fingerprint(entry, seed=None, frame_range=None):
    """Checks that a patch was written for this exact generation.

    A value only counts when both the entry and the scene know it.

    Args:
        entry (dict): Take entry.
        seed (int, optional): Seed of the scene's generation.
        frame_range (tuple, optional): Scene (start, end) frames.

    Returns:
        tuple: (matches, reason).
    """
    entry_seed = entry.get("seed")
    if entry_seed not in (None, "") and seed not in (None, ""):
        if str(entry_seed).strip() != str(seed).strip():
            return False, f"seed {seed} is not the patched seed {entry_seed}"
    entry_range = entry.get("frame_range")
    if entry_range and frame_range:
        if [int(round(float(value))) for value in entry_range] != [int(round(float(value))) for value in frame_range]:
            return False, f"frame range {list(frame_range)} is not the patched range {list(entry_range)}"
    return True, ""


def validate_step(step, base_dir, index):
    """Validates one step.

    Args:
        step (dict): Step.
        base_dir (str): Manifest folder.
        index (int): Step number for messages.

    Returns:
        list: Error messages.
    """
    label = f"step {index}"
    if not isinstance(step, dict):
        return [f"{label} is not an object."]
    errors = []
    frames = step.get("frames")
    if frames is not None or "fix" in step:
        if not (isinstance(frames, (list, tuple)) and len(frames) == 2
                and all(isinstance(value, (int, float)) for value in frames) and frames[0] <= frames[1]):
            errors.append(f'{label}: "frames" must be [start, end] with start <= end.')
    if "fix" in step and "script" in step:
        errors.append(f'{label}: use either "fix" or "script", not both.')
    elif "fix" in step:
        try:
            definition = registry.get_fix(step["fix"])
        except KeyError as error:
            errors.append(f"{label}: {error.args[0]}")
        else:
            unknown = sorted(set(step.get("params") or {}) - set(definition.parameters))
            if unknown:
                errors.append(f'{label}: unknown {definition.key} params: {", ".join(unknown)}.')
            try:
                definition.get_preset(step.get("preset"))
            except KeyError as error:
                errors.append(f"{label}: {error.args[0]}")
    elif "script" in step:
        script_path = resolve_path(str(step["script"]), base_dir)
        if not script_path.lower().endswith(".py") or not os.path.isfile(script_path):
            errors.append(f"{label}: script not found: {script_path}")
    else:
        errors.append(f'{label} needs "fix" or "script".')
    if "nodes" in step and not isinstance(step["nodes"], list):
        errors.append(f'{label}: "nodes" must be a list.')
    if "params" in step and not isinstance(step["params"], dict):
        errors.append(f'{label}: "params" must be an object.')
    return errors


def validate_entry(entry, base_dir):
    """Validates one take entry.

    Args:
        entry (dict): Take entry.
        base_dir (str): Manifest folder.

    Returns:
        list: Error messages.
    """
    if not isinstance(entry, dict):
        return ["entry is not an object."]
    steps = entry.get("steps")
    if not isinstance(steps, list) or not steps:
        return ['"steps" must be a non-empty list.']
    errors = []
    for index, step in enumerate(steps, 1):
        errors.extend(validate_step(step, base_dir, index))
    frame_range = entry.get("frame_range")
    if frame_range is not None and not (isinstance(frame_range, (list, tuple)) and len(frame_range) == 2):
        errors.append('"frame_range" must be [start, end].')
    return errors


def validate_manifest(manifest, base_dir):
    """Validates a whole manifest.

    Args:
        manifest (dict): Manifest.
        base_dir (str): Manifest folder.

    Returns:
        list: Error messages prefixed with the take name.
    """
    errors = []
    if str(manifest.get("on_error") or "warn") not in ON_ERROR_VALUES:
        errors.append(f'"on_error" must be one of {", ".join(ON_ERROR_VALUES)}.')
    for take_name, entry in sorted((manifest.get("takes") or {}).items()):
        errors.extend(f"{take_name}: {error}" for error in validate_entry(entry, base_dir))
    return errors
