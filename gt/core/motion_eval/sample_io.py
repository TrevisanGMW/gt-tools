"""
Motion Evaluation Sample IO - Saves and loads sampled motion as JSON "motion sample" files.

Pure Python. A motion sample holds everything the checks read (world matrices per
frame, parents, frame rate, units, up axis), so it can be evaluated in any Python 3
without Maya or Blender (see hosts.sample_host). Useful for motion that never lives
in a DCC, such as the output of a motion model:

    from motion_eval import sample_io

    sample = sample_io.create_sample(
        fps=30,
        start_frame=1,
        up_axis="y",
        meters_per_unit=0.01,
        nodes={
            "|Hips": {"parent": None, "matrices": hips_matrices},
            "|Hips|LeftUpLeg": {"parent": "|Hips", "matrices": left_up_leg_matrices},
        },
    )
    sample_io.save_sample(sample, "walk_01.motion.json")

Each matrix is a flat list of 16 floats in row-major, row-vector layout (translation at
indices 12, 13, 14); math_utils.compose_matrix builds one from a position, a rotation
quaternion, and a scale. Node paths use "|" between hierarchy levels; the last part is
the joint name the skeleton templates match.

A sample of an open Maya or Blender scene is saved with:

    sample_io.save_sample(sampling.sample_scene(mode, template, frame_range), "walk_01.motion.json")
"""

import json
import os

SAMPLE_SCHEMA = "motion_eval_sample"
SAMPLE_VERSION = 1
SAMPLE_EXTENSION = ".motion.json"
SAMPLE_KEYS = ["fps", "start_frame", "frame_count", "up_axis", "meters_per_unit", "nodes", "joints", "roles",
               "warnings", "source", "extra"]


def is_sample_file(file_path):
    """Checks whether a path is a motion sample file.

    Args:
        file_path (str): File path.

    Returns:
        bool: True for files ending with SAMPLE_EXTENSION.
    """
    return str(file_path).lower().endswith(SAMPLE_EXTENSION)


def create_sample(fps, start_frame, nodes, up_axis="y", meters_per_unit=0.01, joints=None, source=""):
    """Builds a sample dictionary (the format evaluation.evaluate_sample reads).

    Args:
        fps (float): Frames per second.
        start_frame (int): Frame number of the first matrix.
        nodes (dict): Node path to {"parent": path or None, "matrices": [16 floats per frame]}.
        up_axis (str): "y" or "z".
        meters_per_unit (float): Size of one unit in meters (0.01 for centimeters).
        joints (list, optional): Node paths that are joints. Defaults to every node.
        source (str, optional): Where the motion came from (recorded only).

    Returns:
        dict: Sample.

    Raises:
        ValueError: If the sample is invalid.
    """
    nodes = {str(path): {"parent": data.get("parent"), "matrices": [list(matrix) for matrix in data["matrices"]]}
             for path, data in (nodes or {}).items()}
    frame_counts = {len(data["matrices"]) for data in nodes.values()}
    sample = {
        "fps": float(fps),
        "start_frame": int(start_frame),
        "frame_count": frame_counts.pop() if len(frame_counts) == 1 else 0,
        "up_axis": str(up_axis).lower(),
        "meters_per_unit": float(meters_per_unit),
        "nodes": nodes,
        "joints": list(joints) if joints is not None else sorted(nodes),
        "roles": {},
        "warnings": [],
        "source": str(source or ""),
    }
    errors = validate_sample(sample)
    if errors:
        raise ValueError(errors[0])
    return sample


def validate_sample(sample):
    """Checks a sample before it is saved or evaluated.

    Args:
        sample (dict): Sample.

    Returns:
        list: Error messages. Empty when valid.
    """
    errors = []
    nodes = sample.get("nodes") or {}
    if not nodes:
        errors.append("The motion sample has no nodes.")
    if str(sample.get("up_axis") or "").lower() not in ("y", "z"):
        errors.append('The motion sample "up_axis" must be "y" or "z".')
    if float(sample.get("fps") or 0.0) <= 0.0:
        errors.append("The motion sample needs a frame rate above 0.")
    frame_count = int(sample.get("frame_count") or 0)
    if frame_count < 2:
        errors.append("Every node of a motion sample needs the same number of matrices (at least two frames).")
    for path, data in nodes.items():
        matrices = data.get("matrices") or []
        if len(matrices) != frame_count:
            errors.append(f'Node "{path}" has {len(matrices)} matrices, expected {frame_count}.')
            break
        if any(len(matrix) != 16 for matrix in matrices):
            errors.append(f'Node "{path}" has a matrix without 16 values.')
            break
        parent = data.get("parent")
        if parent is not None and parent not in nodes:
            errors.append(f'Node "{path}" has parent "{parent}", which is not in the sample.')
            break
    return errors


def save_sample(sample, file_path):
    """Saves a sample as a motion sample JSON file.

    Args:
        sample (dict): Sample (from create_sample or sampling.sample_scene).
        file_path (str): Destination path. SAMPLE_EXTENSION is added when missing.

    Returns:
        str: Written path.

    Raises:
        ValueError: If the sample is invalid.
    """
    payload = {key: sample[key] for key in SAMPLE_KEYS if key in sample}
    payload.setdefault("joints", sorted(payload.get("nodes") or {}))
    payload.setdefault("frame_count", len(next(iter((payload.get("nodes") or {}).values()), {}).get("matrices", [])))
    errors = validate_sample(payload)
    if errors:
        raise ValueError(errors[0])
    payload["schema"] = SAMPLE_SCHEMA
    payload["version"] = SAMPLE_VERSION
    if not is_sample_file(file_path):
        file_path = f"{file_path}{SAMPLE_EXTENSION}"
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temporary_path = f"{file_path}.{os.getpid()}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as sample_file:
        json.dump(payload, sample_file)
    os.replace(temporary_path, file_path)
    return file_path


def load_sample(file_path):
    """Loads a motion sample file.

    Args:
        file_path (str): Motion sample path.

    Returns:
        dict: Sample.

    Raises:
        ValueError: If the file is not a valid motion sample.
    """
    with open(file_path, "r", encoding="utf-8") as sample_file:
        payload = json.load(sample_file)
    if not isinstance(payload, dict) or payload.get("schema") != SAMPLE_SCHEMA:
        raise ValueError(f"{os.path.basename(file_path)} is not a motion sample file.")
    sample = {key: payload[key] for key in SAMPLE_KEYS if key in payload}
    sample.setdefault("joints", sorted(sample.get("nodes") or {}))
    sample.setdefault("roles", {})
    sample.setdefault("warnings", [])
    errors = validate_sample(sample)
    if errors:
        raise ValueError(f"{os.path.basename(file_path)}: {errors[0]}")
    return sample
