"""Smooths isolated rotation jumps after HumanIK has baked to the skeleton.

Load this sample in HumanIK > Post Script, enable the script, and bake to Skeleton.
It can also run in Maya's Python Script Editor. No files are opened or saved.
Use DRY_RUN to inspect the reported joints, pop frames, and filter windows first.

Detection compares wrapped angular speed with the median speed nearby. This is
a heuristic: deliberate abrupt motion can also qualify. Raise MIN_SPEED or
SPIKE_RATIO to preserve more motion; lower them to detect smaller pops.
Times and speeds use scene frames, not seconds. Dense baked keys are expected.
As with manual Butterworth filtering, Euler-filter baked rotations first if
their channels contain Euler branch flips. This script does not Euler-filter
the whole clip, which could change animation outside the requested windows.
"""

# ------------------------------- Settings ---------------------------------
JOINT_NAMES = ["upperarm_r", "upperarm_l"]
IGNORE_NAMESPACES = True  # Match these leaf names in any namespace, including nested ones.
NAMESPACE = ""  # Used only when IGNORE_NAMESPACES is False; "" means the root namespace.
LIMIT_TO_BATCH_TARGET = True  # In a HumanIK task, restrict matches to imported target nodes.
ROTATION_CHANNELS = ["rotateX", "rotateY", "rotateZ"]

START_FRAME = None  # None uses each curve's first key, regardless of playback range.
END_FRAME = None  # None uses each curve's last key.
MIN_SPEED = 20.0  # Minimum wrapped angular speed in degrees per frame.
SPIKE_RATIO = 4.0  # Speed must also exceed this multiple of the nearby median.
NEIGHBORHOOD_FRAMES = 10.0  # Radius used to measure surrounding motion.
MAX_KEY_GAP = 1.5  # Ignore transitions across larger gaps; increase for coarser bakes.

FRAMES_BEFORE = 10.0  # Filter window is centered on the later key of a detected jump.
FRAMES_AFTER = 10.0
FILTER_ALL_ROTATION_CHANNELS = True  # Smooth XYZ together when any channel detects a pop.
CUTOFF_FREQUENCY = 3.0  # Butterworth cutoff in Hz; lower values smooth more strongly.
SAMPLING_RATE = None  # None uses scene FPS. Must exceed twice CUTOFF_FREQUENCY.
KEEP_KEYS_ON_FRAME = True  # Maya's Butterworth option to place output keys on whole frames.
DRY_RUN = False  # True reports proposed changes without modifying animation.

import math
import statistics


def matches_joint_name(node, joint_names, ignore_namespaces=True, namespace=""):
    """Matches an exact joint leaf name without depending on Maya selection.

    Args:
        node (str): Full DAG path or node name.
        joint_names (list): Unqualified joint names to match.
        ignore_namespaces (bool): Whether all namespaces are eligible.
        namespace (str): Exact namespace when namespace matching is enabled.

    Returns:
        bool: Whether the node matches.
    """
    leaf = node.rsplit("|", 1)[-1]
    if ignore_namespaces:
        return leaf.rsplit(":", 1)[-1] in joint_names
    prefix = f"{namespace.strip(':')}:" if namespace.strip(":") else ""
    return leaf in {f"{prefix}{name}" for name in joint_names}


def detect_pop_frames(times, values, min_speed, spike_ratio, neighborhood, max_key_gap):
    """Finds unusually fast transitions in ordered, densely keyed degree values.

    A 360-degree Euler wrap alone is ignored. Detection uses original keys and
    completes before any filtering. The returned frame is the transition's end.

    Args:
        times (list): Strictly increasing key times in scene frames.
        values (list): Rotation values in degrees.
        min_speed (float): Minimum degrees per frame.
        spike_ratio (float): Minimum speed relative to the local median.
        neighborhood (float): Neighboring transition radius in scene frames.
        max_key_gap (float): Largest key interval eligible for detection.

    Returns:
        list: Detected pop frames.
    """
    transitions = []
    for index in range(1, len(times)):
        interval = times[index] - times[index - 1]
        if interval <= 0 or interval > max_key_gap:
            continue
        delta = (values[index] - values[index - 1] + 180.0) % 360.0 - 180.0
        transitions.append((times[index], abs(delta) / interval))
    pops = []
    for index, (frame, speed) in enumerate(transitions):
        if speed < min_speed:
            continue
        neighbors = [
            other_speed
            for other_index, (other_frame, other_speed) in enumerate(transitions)
            if other_index != index and abs(other_frame - frame) <= neighborhood
        ]
        if neighbors and speed >= spike_ratio * max(statistics.median(neighbors), 0.001):
            pops.append(frame)
    return pops


def build_filter_windows(pop_frames, first_frame, last_frame, frames_before, frames_after):
    """Clips and merges overlapping windows so a region is filtered only once.

    Args:
        pop_frames (list): Detected transition end frames.
        first_frame (float): Earliest allowed frame.
        last_frame (float): Latest allowed frame.
        frames_before (float): Padding before each pop.
        frames_after (float): Padding after each pop.

    Returns:
        list: Non-overlapping (start, end) tuples.
    """
    windows = []
    for frame in sorted(set(pop_frames)):
        start = max(first_frame, frame - frames_before)
        end = min(last_frame, frame + frames_after)
        if start >= end:
            continue
        if windows and start <= windows[-1][1]:
            windows[-1] = (windows[-1][0], max(end, windows[-1][1]))
        else:
            windows.append((start, end))
    return windows


def validate_settings(sampling_rate):
    """Rejects invalid configuration before editing any animation.

    Args:
        sampling_rate (float): Resolved Butterworth sampling rate in FPS.

    Raises:
        ValueError: If a setting is invalid.
    """
    positive_settings = {
        "MIN_SPEED": MIN_SPEED,
        "SPIKE_RATIO": SPIKE_RATIO,
        "NEIGHBORHOOD_FRAMES": NEIGHBORHOOD_FRAMES,
        "MAX_KEY_GAP": MAX_KEY_GAP,
        "CUTOFF_FREQUENCY": CUTOFF_FREQUENCY,
        "SAMPLING_RATE": sampling_rate,
    }
    for name, value in positive_settings.items():
        if not math.isfinite(value) or value <= 0:
            raise ValueError(f"{name} must be a finite positive number.")
    for name, value in {"FRAMES_BEFORE": FRAMES_BEFORE, "FRAMES_AFTER": FRAMES_AFTER}.items():
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be a finite non-negative number.")
    if FRAMES_BEFORE + FRAMES_AFTER <= 0:
        raise ValueError("The filter window must span more than zero frames.")
    if SPIKE_RATIO <= 1:
        raise ValueError("SPIKE_RATIO must exceed 1.")
    if CUTOFF_FREQUENCY >= sampling_rate / 2.0:
        raise ValueError("CUTOFF_FREQUENCY must be below half the sampling rate.")
    for frame in (START_FRAME, END_FRAME):
        if frame is not None and not math.isfinite(frame):
            raise ValueError("START_FRAME and END_FRAME must be finite numbers or None.")
    if START_FRAME is not None and END_FRAME is not None and START_FRAME > END_FRAME:
        raise ValueError("START_FRAME cannot exceed END_FRAME.")
    if not JOINT_NAMES or any(
        not isinstance(name, str) or not name or ":" in name or "|" in name for name in JOINT_NAMES
    ):
        raise ValueError("JOINT_NAMES must contain unqualified joint names.")
    if not ROTATION_CHANNELS or not set(ROTATION_CHANNELS) <= {"rotateX", "rotateY", "rotateZ"}:
        raise ValueError("ROTATION_CHANNELS must contain rotateX, rotateY, and/or rotateZ.")


def get_target_joints(cmds, runtime_context):
    """Resolves names and restricts batch runs to their imported target skeleton.

    Args:
        cmds (module): Maya commands module.
        runtime_context (dict): Optional HumanIK post-script globals.

    Returns:
        list: Sorted matching joint DAG paths.
    """
    if LIMIT_TO_BATCH_TARGET and "imported_target_nodes" in runtime_context:
        target_nodes = runtime_context.get("imported_target_nodes") or []
        # An empty batch target must never fall back to matching the source rig.
        candidates = cmds.ls(target_nodes, type="joint", long=True) if target_nodes else []
    else:
        candidates = cmds.ls(type="joint", long=True)
    return sorted({
        joint for joint in candidates or []
        if matches_joint_name(joint, JOINT_NAMES, IGNORE_NAMESPACES, NAMESPACE)
    })


def read_rotation_curve(cmds, joint, channel):
    """Reads a directly baked rotation curve, skipping live rigs and shared curves.

    Animation layers, constraints, and live HumanIK connections must be baked to
    the skeleton first. Shared curves are skipped to protect other scene nodes.

    Args:
        cmds (module): Maya commands module.
        joint (str): Joint DAG path.
        channel (str): Rotation attribute.

    Returns:
        dict or None: Curve data, or None when no safely editable baked curve exists.
    """
    plug = f"{joint}.{channel}"
    inputs = cmds.listConnections(plug, source=True, destination=False) or []
    if not inputs:
        return None
    curve = inputs[0]
    if len(inputs) != 1 or cmds.nodeType(curve) != "animCurveTA":
        print(f"Rotation pop filter: skipped {plug}; bake to Skeleton first.", flush=True)
        return None
    destinations = cmds.listConnections(f"{curve}.output", source=False, destination=True, plugs=True) or []
    if (
        len(destinations) != 1 or cmds.getAttr(plug, lock=True)
        or cmds.lockNode(curve, query=True, lock=True)[0]
        or cmds.referenceQuery(curve, isNodeReferenced=True)
    ):
        print(f"Rotation pop filter: skipped locked, referenced, or shared curve {curve}.", flush=True)
        return None
    times = cmds.keyframe(curve, query=True, timeChange=True) or []
    values = cmds.keyframe(curve, query=True, valueChange=True) or []
    if len(times) < 4:
        return None
    if cmds.currentUnit(query=True, angle=True) == "rad":
        values = [math.degrees(value) for value in values]
    pops = detect_pop_frames(times, values, MIN_SPEED, SPIKE_RATIO, NEIGHBORHOOD_FRAMES, MAX_KEY_GAP)
    first_frame = max(times[0], START_FRAME) if START_FRAME is not None else times[0]
    last_frame = min(times[-1], END_FRAME) if END_FRAME is not None else times[-1]
    pops = [frame for frame in pops if first_frame <= frame <= last_frame]
    return {"curve": curve, "times": times, "pops": pops, "start": first_frame, "end": last_frame}


def smooth_rotation_pops(runtime_context=None):
    """Detects and locally filters baked rotation pops using the settings above.

    Args:
        runtime_context (dict, optional): HumanIK task globals, when run in batch.

    Returns:
        list: Reports containing joint, curve, detected frames, and filter windows.
    """
    import maya.cmds as cmds
    import maya.api.OpenMaya as om

    sampling_rate = SAMPLING_RATE
    if sampling_rate is None:
        sampling_rate = 1.0 / om.MTime(1.0, om.MTime.uiUnit()).asUnits(om.MTime.kSeconds)
    validate_settings(sampling_rate)
    joints = get_target_joints(cmds, runtime_context or {})
    if not joints:
        print("Rotation pop filter: no matching target joints.", flush=True)
        return []
    reports = []
    for joint in joints:
        curves = [read_rotation_curve(cmds, joint, channel) for channel in dict.fromkeys(ROTATION_CHANNELS)]
        curves = [curve for curve in curves if curve]
        joint_pops = sorted({frame for curve in curves for frame in curve["pops"]})
        for curve in curves:
            pops = joint_pops if FILTER_ALL_ROTATION_CHANNELS else curve["pops"]
            windows = build_filter_windows(pops, curve["start"], curve["end"], FRAMES_BEFORE, FRAMES_AFTER)
            windows = [
                (start, end) for start, end in windows
                if sum(start <= frame <= end for frame in curve["times"]) >= 4
            ]
            if windows:
                reports.append({"joint": joint, "curve": curve["curve"], "pops": pops, "windows": windows})
    action = "Would filter" if DRY_RUN else "Filter"
    for report in reports:
        print(
            f"Rotation pop filter: {action} {report['joint']} ({report['curve']}); "
            f"pop frames {report['pops']}; windows {report['windows']}.", flush=True,
        )
    if reports and not DRY_RUN:
        selected_keys = {
            curve: cmds.keyframe(curve, query=True, selected=True, timeChange=True) or []
            for curve in cmds.keyframe(query=True, selected=True, name=True) or []
        }
        cmds.undoInfo(openChunk=True, chunkName="Smooth Rotation Pops")
        try:
            for report in reports:
                for start, end in report["windows"]:
                    filtered_count = cmds.filterCurve(
                        report["curve"], filter="butterworth", startTime=start, endTime=end,
                        cutoffFrequency=CUTOFF_FREQUENCY, samplingRate=sampling_rate,
                        keepKeysOnFrame=KEEP_KEYS_ON_FRAME, selectedKeys=False,
                    )
                    if not filtered_count:
                        raise RuntimeError(f"Butterworth did not filter {report['curve']} at {start}-{end}.")
        finally:
            try:
                cmds.selectKey(clear=True)
                for curve, frames in selected_keys.items():
                    for frame in frames:
                        cmds.selectKey(curve, add=True, time=(frame, frame))
            finally:
                cmds.undoInfo(closeChunk=True)
    print(
        f"Rotation pop filter: {'dry run; ' if DRY_RUN else ''}"
        f"{len(joints)} matching joint(s), {len(reports)} curve(s) with filter windows.", flush=True,
    )
    return reports

smooth_rotation_pops(globals())
