"""Pure timing helpers for eased, independently staggered foot locks."""


def resolve_timing(params, fps):
    """Resolves frame durations, scaling unspecified defaults to the scene rate.

    Args:
        params (dict): Optional blend, blend_in, blend_out and stagger values.
        fps (float): Scene frames per second.

    Returns:
        tuple: Entry, release and stagger durations in frames.
    """
    scale = max(1.0, float(fps)) / 30.0
    legacy = params.get("blend")
    durations = []
    for name, default in (("blend_in", 12), ("blend_out", 16), ("stagger", 8)):
        value = params.get(name)
        if value is None and name != "stagger":
            value = legacy
        durations.append(max(0, int(round(default * scale if value is None else float(value)))))
    return tuple(durations)


def stagger_spans(spans, limits, stagger, lead_index=0):
    """Offsets two full-lock spans within their measured contact and clip bounds.

    Short intervals reduce the stagger. Single legs keep their original timing.
    Independent clamping can shorten a hold instead of extending it past contact.

    Args:
        spans (list): Requested inclusive frame ranges, one per foot.
        limits (list): Allowed inclusive contact ranges, one per foot.
        stagger (int): Requested time difference between the two feet.
        lead_index (int): Index of the foot engaging and releasing first.

    Returns:
        list: Inclusive full-lock ranges with safe, deterministic timing.
    """
    result = [tuple(span) for span in spans]
    if len(spans) != 2:
        return result
    overlap = min(span[1] for span in spans) - max(span[0] for span in spans) + 1
    if overlap <= 1:
        return result
    stagger = min(max(0, int(stagger)), overlap - 1)
    for index, (span, bounds) in enumerate(zip(spans, limits)):
        offset = -(stagger // 2) if index == lead_index else stagger - stagger // 2
        start = min(bounds[1], max(bounds[0], span[0] + offset))
        end = max(start, min(bounds[1], max(bounds[0], span[1] + offset)))
        result[index] = (start, end)
    return result


def bounded_weights(frame_count, blend_in, blend_out, offset=0):
    """Fits easing inside an issue span, preserving two frames at each edge.

    Spans shorter than seven frames cannot support both guard frames and useful
    easing. They receive zero influence instead of extending into adjacent motion.

    Args:
        frame_count (int): Number of frames in the inclusive issue interval.
        blend_in (int): Requested entry length.
        blend_out (int): Requested release length.
        offset (int): Requested temporal shift of the full-lock phase.

    Returns:
        list: Smooth weights with no influence at either edge of the issue.
    """
    if frame_count < 7:
        return [0.0] * frame_count
    entry = max(2, int(blend_in))
    release = max(2, int(blend_out))
    budget = frame_count - 3
    if entry + release > budget:
        entry = max(2, min(budget - 2, int(round(budget * entry / float(entry + release)))))
        release = budget - entry
    shift = max(2 - entry, min(release - 2, int(offset)))
    start = 1 + entry + shift
    end = frame_count - 2 - release + shift
    weights = []
    for index in range(frame_count):
        if index <= 1 or index >= frame_count - 2:
            weights.append(0.0)
            continue
        if index < start:
            fraction = (index - 1) / float(start - 1)
        elif index > end:
            fraction = (frame_count - 2 - index) / float(frame_count - 2 - end)
        else:
            fraction = 1.0
        weights.append(fraction * fraction * (3.0 - 2.0 * fraction))
    return weights
