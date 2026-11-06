"""
Motion Evaluation - Runs the checks on sampled motion and builds the report.

``evaluate_sample`` is pure. ``evaluate_scene`` samples the open Maya scene first
(Maya imports happen inside the sampling module only when it is called).
"""

from .checks_base import MotionData, MODE_BIPED, MODE_LABELS
from . import presets
from . import scoring
from . import templates
from . import math_utils
from . import __version__ as PACKAGE_VERSION
import traceback
import datetime
import logging

logger = logging.getLogger(__name__)

REPORT_VERSION = 1
EVALUATOR_NAME = "core.motion_eval"


def get_ignored_indexes(settings, start_frame, frame_count):
    """Converts ignore ranges into frame indexes.

    Args:
        settings (dict): Resolved global settings.
        start_frame (int): First sampled frame.
        frame_count (int): Number of sampled frames.

    Returns:
        set: Ignored frame indexes inside the sampled range.
    """
    ignored = set()
    for start, end in presets.parse_frame_ranges(settings.get("ignore_ranges", "")):
        for frame in range(start, end + 1):
            index = frame - start_frame
            if 0 <= index < frame_count:
                ignored.add(index)
    return ignored


def run_check(check, data, check_values):
    """Runs one check and converts crashes into skipped results.

    Args:
        check (CheckDefinition): Check definition.
        data (MotionData): Sampled motion.
        check_values (dict): Resolved check settings.

    Returns:
        CheckResult: Raw findings.
    """
    from .checks_base import CheckResult

    missing_roles = data.missing_roles(check.required_roles) if check.required_roles else []
    if missing_roles:
        return CheckResult.skipped(f"Missing roles: {', '.join(missing_roles)}")
    missing_data = [key for key in check.required_data if data.get_extra(key) is None]
    if missing_data:
        return CheckResult.skipped(f"Needs scene data this program does not provide: {', '.join(missing_data)}")
    try:
        return check.function(data, dict(check_values["parameters"]))
    except Exception as exception:
        logger.debug(traceback.format_exc())
        return CheckResult.skipped(f"Check error: {type(exception).__name__}: {exception}")


def evaluate_sample(sample, preset=None, template=None, include_series=False):
    """Evaluates sampled motion with a preset.

    Args:
        sample (dict): Sample produced by ``sampling.sample_scene`` (or synthetic data).
        preset (dict, optional): Stored or resolved preset. Defaults to the default preset.
        template (dict, optional): Skeleton template recorded in the report.
        include_series (bool): Store each check's measured per-frame signal under entry["chart"]
            so graphs can be exported (see report_graphs). Use strip_series before saving large logs.

    Returns:
        dict: Evaluation report with the overall score, status, and per-check entries.
    """
    resolved = presets.resolve_preset(preset or presets.DEFAULT_PRESET)
    settings = resolved["settings"]
    mode = resolved["mode"]
    data = MotionData(sample, mode=mode, settings=settings)
    ignored_indexes = get_ignored_indexes(settings, data.start_frame, data.frame_count)
    evaluated_frame_count = max(1, data.frame_count - len(ignored_indexes))
    entries = []
    for check in presets.get_checks_for_mode(mode):
        check_values = resolved["checks"][check.key]
        if not check_values["enabled"]:
            entries.append(scoring.disabled_check_entry(check))
            continue
        raw_result = run_check(check, data, check_values)
        entry = scoring.score_check(
            check=check,
            check_values=check_values,
            raw_result=raw_result,
            evaluated_frame_count=evaluated_frame_count,
            ignored_indexes=ignored_indexes,
            settings=settings,
            start_frame=data.start_frame,
        )
        if include_series and not raw_result.skip_reason:
            chart = raw_result.get_chart_data()
            if chart:
                entry["chart"] = chart
        entries.append(entry)
    score = scoring.combine_scores(entries, settings["score_method"])
    status = scoring.get_overall_status(score, entries, settings)
    all_flagged = set()
    for entry in entries:
        for start, end in entry.get("spans") or []:
            all_flagged.update(range(start, end + 1))
    return {
        "version": REPORT_VERSION,
        "evaluator": EVALUATOR_NAME,
        "evaluator_version": PACKAGE_VERSION,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "mode_label": MODE_LABELS.get(mode, mode),
        "preset": resolved["name"],
        "template": (template or {}).get("name", ""),
        "settings_hash": presets.get_settings_hash(resolved, template),
        "score": score,
        "status": status,
        "frame_range": [data.start_frame, data.start_frame + data.frame_count - 1],
        "frame_count": data.frame_count,
        "fps": data.fps,
        "reference_length": round(data.get_reference_length(), 4),
        "meters_per_unit": data.meters_per_unit,
        "sampled_nodes": len(data.nodes),
        "roles": dict(data.roles),
        "ignored_frames": len(ignored_indexes),
        "ignored_ranges": math_utils.indexes_to_spans(index + data.start_frame for index in ignored_indexes),
        "flagged_frames": len(all_flagged),
        "settings": dict(settings),
        "checks": entries,
        "warnings": list(sample.get("warnings") or []),
    }


def strip_series(report):
    """Copies a report without the per-frame graph series (keeps logs and exports small).

    Args:
        report (dict): Evaluation report.

    Returns:
        dict: Shallow report copy whose check entries have no "chart" key.
    """
    stripped = dict(report)
    stripped["checks"] = [
        {key: value for key, value in entry.items() if key != "chart"} for entry in report.get("checks") or []
    ]
    return stripped


def get_required_data(resolved_preset):
    """Lists the extra scene data the enabled checks of a preset need.

    Args:
        resolved_preset (dict): Resolved preset.

    Returns:
        list: Extra data keys (see CheckDefinition.required_data), in check order.
    """
    keys = []
    for check in presets.get_checks_for_mode(resolved_preset["mode"]):
        if resolved_preset["checks"][check.key]["enabled"]:
            keys.extend(key for key in check.required_data if key not in keys)
    return keys


def evaluate_scene(preset=None, template=None, frame_range=None, general_scope=None, node_names=None,
                   include_series=False):
    """Samples the open scene of the active host (Maya, Blender, or a motion sample) and evaluates it.

    Args:
        preset (dict, optional): Stored or resolved preset.
        template (dict, optional): Skeleton template. Required in biped mode.
        frame_range (tuple, optional): (start, end) frames. Defaults to the playback range.
        general_scope (str, optional): Node scope used in general mode (see sampling.GENERAL_SCOPES).
        node_names (list, optional): Nodes used by the "Node List" scope.
        include_series (bool): Store per-check graph series in the report.

    Returns:
        dict: Evaluation report.

    Raises:
        ValueError: If the preset, template, or scene cannot be evaluated.
    """
    from . import sampling

    resolved = presets.resolve_preset(preset or presets.DEFAULT_PRESET)
    errors = presets.validate_preset(resolved)
    if errors:
        raise ValueError(errors[0])
    if resolved["mode"] == MODE_BIPED:
        if not template:
            raise ValueError("Biped mode needs a skeleton template.")
        template_errors = templates.validate_template(template, require_biped=True)
        if template_errors:
            raise ValueError(template_errors[0])
    sample = sampling.sample_scene(
        mode=resolved["mode"],
        template=template,
        frame_range=frame_range,
        general_scope=general_scope,
        node_names=node_names,
        extra_data=get_required_data(resolved),
    )
    report = evaluate_sample(sample, preset=resolved, template=template, include_series=include_series)
    report["scene"] = sampling.get_scene_name()
    return report


def summarize_report(report, max_spans=4):
    """Builds readable lines describing a report.

    Args:
        report (dict): Evaluation report.
        max_spans (int): Frame spans listed per check.

    Returns:
        list: Report lines.
    """
    lines = [
        f"Score: {report.get('score')}/100 [{str(report.get('status', '')).upper()}]",
        f"Mode: {report.get('mode_label')} | Template: {report.get('template') or '-'} | "
        f"Frames: {report.get('frame_range')} @ {report.get('fps')} fps",
    ]
    for warning in report.get("warnings") or []:
        lines.append(f"Warning: {warning}")
    for entry in report.get("checks") or []:
        if entry.get("status") == "disabled":
            continue
        if entry.get("score") is None:
            lines.append(f"  - {entry['label']}: skipped ({entry.get('skip_reason')})")
            continue
        span_text = ", ".join(f"{start}-{end}" for start, end in (entry.get("spans") or [])[:max_spans])
        suffix = f" | frames {span_text}" if span_text else ""
        lines.append(
            f"  - {entry['label']}: {entry['score']} [{entry['status']}] "
            f"({entry.get('flagged_frames', 0)} frame(s), {entry.get('events', 0)} event(s)){suffix}"
        )
    return lines


def get_report_spans(report):
    """Collects every flagged frame span across checks.

    Args:
        report (dict): Evaluation report.

    Returns:
        list: Merged inclusive frame spans.
    """
    frames = set()
    for entry in report.get("checks") or []:
        for start, end in entry.get("spans") or []:
            frames.update(range(start, end + 1))
    return math_utils.indexes_to_spans(frames)
