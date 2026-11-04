"""
Motion Evaluation Batch Summary - Combines evaluation reports of many files.

Pure Python helpers used by batch tools (for example the Batch Processor
"Validate Animation" task) to write one summary, JSON report, or graph for a
whole batch, and per-file summaries. Nothing here imports Maya or Qt.
"""

from .checks_base import STATUS_DISABLED, STATUS_FAILED, STATUS_PASSED, STATUS_SKIPPED
from .checks_base import STATUS_WARNING
from . import evaluation
import datetime
import os

BATCH_REPORT_VERSION = 1
STATUS_ORDER = [STATUS_FAILED, STATUS_WARNING, STATUS_PASSED, STATUS_SKIPPED]


def build_batch_entry(report, source_path):
    """Builds the compact per-file entry kept for batch outputs.

    Args:
        report (dict): Evaluation report of one file.
        source_path (str): Evaluated file path.

    Returns:
        dict: Entry with the file, score, status, and each enabled check's result.
    """
    checks = []
    for entry in report.get("checks") or []:
        if entry.get("status") == STATUS_DISABLED:
            continue
        checks.append(
            {
                "key": entry.get("key"),
                "label": entry.get("label") or entry.get("key"),
                "score": entry.get("score"),
                "status": entry.get("status"),
                "flagged_frames": entry.get("flagged_frames", 0),
                "events": entry.get("events", 0),
                "spans": entry.get("spans") or [],
            }
        )
    return {
        "source": str(source_path or ""),
        "name": os.path.basename(str(source_path or "")) or str(report.get("scene") or ""),
        "score": report.get("score"),
        "status": report.get("status"),
        "mode_label": report.get("mode_label"),
        "template": report.get("template") or "",
        "preset": report.get("preset") or "",
        "frame_range": report.get("frame_range") or [],
        "fps": report.get("fps"),
        "flagged_frames": report.get("flagged_frames", 0),
        "warnings": list(report.get("warnings") or []),
        "checks": checks,
    }


def sort_batch_entries(entries):
    """Sorts entries from the lowest score to the highest, then by file name.

    Args:
        entries (list): Batch entries.

    Returns:
        list: Sorted copy.
    """
    def sort_key(entry):
        """Builds the sort key of one entry.

        Args:
            entry (dict): Batch entry.

        Returns:
            tuple: (score, lowercase name).
        """
        score = entry.get("score")
        return (-1 if score is None else score, str(entry.get("name") or "").lower())

    return sorted(entries, key=sort_key)


def get_issue_checks(entry):
    """Gets the checks of an entry that warned or failed, worst first.

    Args:
        entry (dict): Batch entry.

    Returns:
        list: Check dictionaries with a warning or failed status.
    """
    issues = [check for check in entry.get("checks") or [] if check.get("status") in (STATUS_FAILED, STATUS_WARNING)]
    return sorted(issues, key=lambda check: (check.get("status") != STATUS_FAILED, check.get("score") or 0))


def build_batch_totals(entries):
    """Counts results across a batch.

    Args:
        entries (list): Batch entries.

    Returns:
        dict: File counts per status, score statistics, and per-check status counts.
    """
    status_counts = dict((status, 0) for status in STATUS_ORDER)
    scores = []
    checks = {}
    for entry in entries:
        status = entry.get("status")
        status_counts[status] = status_counts.get(status, 0) + 1
        if entry.get("score") is not None:
            scores.append(entry["score"])
        for check in entry.get("checks") or []:
            counts = checks.setdefault(
                check.get("key"),
                {"label": check.get("label"), STATUS_PASSED: 0, STATUS_WARNING: 0, STATUS_FAILED: 0, STATUS_SKIPPED: 0},
            )
            check_status = check.get("status")
            counts[check_status] = counts.get(check_status, 0) + 1
    return {
        "files": len(entries),
        "statuses": status_counts,
        "average_score": round(sum(scores) / float(len(scores)), 1) if scores else None,
        "lowest_score": min(scores) if scores else None,
        "highest_score": max(scores) if scores else None,
        "checks": checks,
    }


def build_batch_summary_lines(entries, title="Validate Animation"):
    """Builds a readable summary of a whole batch, with files sorted by score.

    Args:
        entries (list): Batch entries.
        title (str): First line of the summary.

    Returns:
        list: Text lines.
    """
    totals = build_batch_totals(entries)
    statuses = totals["statuses"]
    lines = [
        f"{title} - Batch Summary",
        f"Created: {datetime.datetime.now().isoformat(sep=' ', timespec='seconds')}",
        f"Files: {totals['files']} | Passed: {statuses.get(STATUS_PASSED, 0)} | "
        f"Warning: {statuses.get(STATUS_WARNING, 0)} | Failed: {statuses.get(STATUS_FAILED, 0)}",
        f"Score: average {format_score(totals['average_score'])} | lowest {format_score(totals['lowest_score'])} | "
        f"highest {format_score(totals['highest_score'])}",
        "",
        "Checks with issues (files warned / failed):",
    ]
    issue_rows = [
        (counts["label"], counts.get(STATUS_WARNING, 0), counts.get(STATUS_FAILED, 0))
        for counts in totals["checks"].values()
        if counts.get(STATUS_WARNING, 0) or counts.get(STATUS_FAILED, 0)
    ]
    issue_rows.sort(key=lambda row: (-row[2], -row[1], str(row[0])))
    if not issue_rows:
        lines.append("  none")
    label_width = max([len(str(row[0])) for row in issue_rows] or [0])
    for label, warned, failed in issue_rows:
        lines.append(f"  {str(label).ljust(label_width)}  {warned} warned / {failed} failed")
    lines.extend(["", "Files (lowest score first):"])
    sorted_entries = sort_batch_entries(entries)
    name_width = min(60, max([len(entry.get("name") or "") for entry in sorted_entries] or [0]))
    for entry in sorted_entries:
        issues = ", ".join(f"{check['label']} {check.get('score')}" for check in get_issue_checks(entry))
        status = str(entry.get("status") or "").upper()
        lines.append(
            f"  {format_score(entry.get('score')).rjust(3)}  {status.ljust(7)}  "
            f"{str(entry.get('name') or '').ljust(name_width)}  {issues or '-'}"
        )
    return lines


def build_file_summary_lines(report, source_path):
    """Builds the readable summary of one file.

    Args:
        report (dict): Evaluation report.
        source_path (str): Evaluated file path.

    Returns:
        list: Text lines.
    """
    return [f"File: {source_path}", f"Created: {report.get('created_at')}", ""] + evaluation.summarize_report(
        report, max_spans=20
    )


def build_batch_report(entries, settings=None):
    """Builds the JSON-ready report of a whole batch.

    Args:
        entries (list): Batch entries.
        settings (dict, optional): Evaluation settings shared by the batch.

    Returns:
        dict: Batch report with totals and the files sorted by score.
    """
    return {
        "version": BATCH_REPORT_VERSION,
        "evaluator": evaluation.EVALUATOR_NAME,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "settings": dict(settings or {}),
        "totals": build_batch_totals(entries),
        "files": sort_batch_entries(entries),
    }


def build_batch_chart(entries, title="Validate Animation"):
    """Describes the batch chart: one row per file, one column per check.

    Args:
        entries (list): Batch entries.
        title (str): Chart title.

    Returns:
        dict: Chart description used by report_graphs.render_batch_chart.
    """
    totals = build_batch_totals(entries)
    check_columns = []
    for entry in entries:
        for check in entry.get("checks") or []:
            column = (check.get("key"), check.get("label"))
            if column not in check_columns:
                check_columns.append(column)
    rows = []
    for entry in sort_batch_entries(entries):
        statuses = dict((check.get("key"), check.get("status")) for check in entry.get("checks") or [])
        rows.append(
            {
                "label": entry.get("name") or "",
                "score": entry.get("score"),
                "status": entry.get("status"),
                "cells": [statuses.get(key) for key, _label in check_columns],
            }
        )
    statuses = totals["statuses"]
    return {
        "title": f"{title}: {totals['files']} file(s), average score {format_score(totals['average_score'])}",
        "subtitle": f"Passed {statuses.get(STATUS_PASSED, 0)} | Warning {statuses.get(STATUS_WARNING, 0)} | "
                    f"Failed {statuses.get(STATUS_FAILED, 0)} | lowest score first | cells: green passed, "
                    "yellow warning, red failed, grey skipped",
        "columns": [label for _key, label in check_columns],
        "rows": rows,
    }


def format_score(score):
    """Formats a score for text output.

    Args:
        score (int or float or None): Score.

    Returns:
        str: Score text, or "-" when missing.
    """
    if score is None:
        return "-"
    if isinstance(score, float) and not score.is_integer():
        return f"{score:.1f}"
    return str(int(score))
