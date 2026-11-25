"""
Motion Evaluation Scoring - Converts raw check findings into 0-100 scores and statuses.
"""

from .checks_base import (
    STATUS_DISABLED,
    STATUS_FAILED,
    STATUS_PASSED,
    STATUS_SEVERITY,
    STATUS_SKIPPED,
    STATUS_WARNING,
    format_frame_spans,
)
from . import presets
from . import math_utils

MAX_REPORTED_SPANS = 20
MAX_REPORTED_OFFENDERS = 8


def clamp_score(value):
    """Clamps and rounds a score.

    Args:
        value (float): Raw score.

    Returns:
        int: Score from 0 to 100.
    """
    return int(round(max(0.0, min(100.0, float(value)))))


def get_check_status(score, check_values):
    """Gets the status of a scored check.

    Args:
        score (int): Check score.
        check_values (dict): Resolved check settings.

    Returns:
        str: Passed, warning, or failed.
    """
    if score < check_values["fail_below"]:
        return STATUS_WARNING if check_values["allow_failure"] else STATUS_FAILED
    if score < check_values["warn_below"]:
        return STATUS_WARNING
    return STATUS_PASSED


def filter_flagged_frames(flagged, ignored_indexes, min_issue_frames):
    """Removes ignored frames and issue spans that are too short.

    Args:
        flagged (set): Flagged frame indexes.
        ignored_indexes (set): Indexes excluded from evaluation.
        min_issue_frames (int): Shortest span kept.

    Returns:
        list: Remaining inclusive index spans.
    """
    remaining = set(flagged) - set(ignored_indexes)
    return [span for span in math_utils.indexes_to_spans(remaining) if span[1] - span[0] + 1 >= min_issue_frames]


def score_check(check, check_values, raw_result, evaluated_frame_count, ignored_indexes, settings, start_frame):
    """Scores one check result.

    Args:
        check (CheckDefinition): Check definition.
        check_values (dict): Resolved check settings.
        raw_result (CheckResult): Raw findings.
        evaluated_frame_count (int): Frames evaluated after ignore ranges.
        ignored_indexes (set): Ignored frame indexes.
        settings (dict): Resolved global settings.
        start_frame (int): Frame number of index zero.

    Returns:
        dict: Report entry for the check.
    """
    entry = {
        "key": check.key,
        "label": check.label,
        "mode": check.mode,
        "enabled": True,
        "weight": check_values["weight"],
        "warn_below": check_values["warn_below"],
        "fail_below": check_values["fail_below"],
        "allow_failure": check_values["allow_failure"],
        "parameters": dict(check_values["parameters"]),
        "score": None,
        "status": STATUS_SKIPPED,
        "flagged_frames": 0,
        "events": 0,
        "spans": [],
        "offenders": [],
        "details": list(raw_result.details),
        "skip_reason": raw_result.skip_reason,
    }
    if raw_result.skip_reason:
        return entry
    spans = filter_flagged_frames(raw_result.flagged, ignored_indexes, settings["min_issue_frames"])
    flagged_count = sum(end - start + 1 for start, end in spans)
    event_count = len(spans) if raw_result.event_count is None else int(raw_result.event_count)
    flagged_percent = 100.0 * flagged_count / float(max(1, evaluated_frame_count))
    score = clamp_score(
        100.0 - event_count * check_values["event_penalty"] - flagged_percent * check_values["frame_penalty"]
    )
    offenders = sorted(raw_result.offenders.items(), key=lambda item: (-item[1], item[0]))
    entry.update(
        {
            "score": score,
            "status": get_check_status(score, check_values),
            "flagged_frames": flagged_count,
            "flagged_percent": round(flagged_percent, 2),
            "events": event_count,
            "spans": format_frame_spans(spans, start_frame, MAX_REPORTED_SPANS),
            "offenders": [{"name": name, "frames": count} for name, count in offenders[:MAX_REPORTED_OFFENDERS]],
        }
    )
    return entry


def disabled_check_entry(check, reason="Disabled in the preset."):
    """Builds a report entry for a check that did not run.

    Args:
        check (CheckDefinition): Check definition.
        reason (str): Why the check did not run.

    Returns:
        dict: Report entry.
    """
    return {
        "key": check.key,
        "label": check.label,
        "mode": check.mode,
        "enabled": False,
        "score": None,
        "status": STATUS_DISABLED,
        "skip_reason": reason,
    }


def combine_scores(check_entries, method):
    """Combines scored checks into the overall score.

    Args:
        check_entries (list): Report entries from score_check.
        method (str): One of presets.SCORE_METHODS.

    Returns:
        int: Overall score. 100 when no check produced a score.
    """
    scored = [entry for entry in check_entries if entry.get("score") is not None and entry.get("weight", 0) > 0]
    if not scored:
        return 100
    if method == presets.SCORE_METHOD_MINIMUM:
        return clamp_score(min(entry["score"] for entry in scored))
    if method == presets.SCORE_METHOD_WEIGHTED_AVERAGE:
        total_weight = sum(entry["weight"] for entry in scored)
        return clamp_score(sum(entry["score"] * entry["weight"] for entry in scored) / total_weight)
    return clamp_score(100.0 - sum((100.0 - entry["score"]) * entry["weight"] for entry in scored))


def get_overall_status(score, check_entries, settings):
    """Gets the evaluation status from the overall score and check statuses.

    Args:
        score (int): Overall score.
        check_entries (list): Report entries.
        settings (dict): Resolved global settings.

    Returns:
        str: Passed, warning, or failed.
    """
    status = STATUS_PASSED
    if score < settings["overall_fail_below"]:
        status = STATUS_FAILED
    elif score < settings["overall_warn_below"]:
        status = STATUS_WARNING
    for entry in check_entries:
        entry_status = entry.get("status")
        if entry_status in (STATUS_WARNING, STATUS_FAILED) and STATUS_SEVERITY[entry_status] > STATUS_SEVERITY[status]:
            status = entry_status
    return status
