"""
Motion Evaluation Outputs - Writes summaries, JSON reports, and graphs for evaluated files.

Used by the headless runner (runner.py) and by batch tools, so every caller
produces the same files:

    <output_dir>/batch_summary.txt      whole batch, files sorted by score
    <output_dir>/batch_report.json      whole batch, machine readable
    <output_dir>/batch_scores.png       whole batch, one row per file
    <output_dir>/<file>/<file>_summary.txt, <file>_report.json, <file>_00_summary.png, <file>_NN_<check>.png

With "file_folders" off, per-file outputs are written directly in <output_dir>.
Text and JSON writing is pure Python; graphs import Qt lazily (see report_graphs).
"""

from . import batch_summary
from . import evaluation
from .checks_base import STATUS_FAILED
import json
import os
import re

BATCH_SUMMARY_FILE_NAME = "batch_summary.txt"
BATCH_REPORT_FILE_NAME = "batch_report.json"
BATCH_GRAPH_FILE_NAME = "batch_scores.png"
DEFAULT_TITLE = "Validate Animation"
DEFAULT_OUTPUT_OPTIONS = {
    "file_folders": True,
    "summary_batch": True,
    "summary_per_file": False,
    "report_batch": False,
    "report_per_file": False,
    "graphs_batch": False,
    "graphs_per_file": False,
    "graphs_only_on_failure": True,
}
FILE_OUTPUT_KEYS = ["summary_per_file", "report_per_file", "graphs_per_file"]
BATCH_OUTPUT_KEYS = ["summary_batch", "report_batch", "graphs_batch"]


def resolve_output_options(options=None):
    """Merges output options with the defaults.

    Args:
        options (dict, optional): Partial options. Unknown keys are ignored.

    Returns:
        dict: Complete options.
    """
    resolved = dict(DEFAULT_OUTPUT_OPTIONS)
    for key, value in (options or {}).items():
        if key in resolved:
            resolved[key] = bool(value)
    return resolved


def has_outputs(options):
    """Checks whether any output is enabled.

    Args:
        options (dict): Output options.

    Returns:
        bool: True when at least one summary, report, or graph is on.
    """
    resolved = resolve_output_options(options)
    return any(resolved[key] for key in FILE_OUTPUT_KEYS + BATCH_OUTPUT_KEYS)


def has_batch_outputs(options):
    """Checks whether any whole-batch output is enabled.

    Args:
        options (dict): Output options.

    Returns:
        bool: True when a batch summary, report, or graph is on.
    """
    resolved = resolve_output_options(options)
    return any(resolved[key] for key in BATCH_OUTPUT_KEYS)


def needs_series(options):
    """Checks whether evaluation must keep graph series (per-file graphs).

    Args:
        options (dict): Output options.

    Returns:
        bool: True when per-file graphs are on.
    """
    return resolve_output_options(options)["graphs_per_file"]


def get_file_prefix(source_path):
    """Builds the safe file-name prefix used for one file's outputs.

    Args:
        source_path (str): Evaluated file path.

    Returns:
        str: Lowercase name made of letters, digits, dashes, and underscores.
    """
    scene_name = os.path.splitext(os.path.basename(str(source_path or "")))[0]
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", scene_name).strip("_")
    return cleaned.lower() or "untitled"


def get_file_output_dir(output_dir, source_path, options=None, relative_dir=""):
    """Gets the folder of one file's outputs.

    Args:
        output_dir (str): Output folder.
        source_path (str): Evaluated file path.
        options (dict, optional): Output options ("file_folders").
        relative_dir (str, optional): Source sub-folder kept under the output folder (file folders only).

    Returns:
        str: <output_dir>/<relative_dir>/<file> with file folders, otherwise output_dir.
    """
    if not resolve_output_options(options)["file_folders"]:
        return output_dir
    parts = [output_dir] + ([relative_dir] if relative_dir else []) + [get_file_prefix(source_path)]
    return os.path.join(*parts)


def write_file_outputs(report, source_path, output_dir, options=None, relative_dir=""):
    """Writes the enabled per-file summary, JSON report, and graphs.

    Args:
        report (dict): Evaluation report. Per-file graphs need a report made with include_series=True.
        source_path (str): Evaluated file path (used for names and recorded in the report).
        output_dir (str): Output folder.
        options (dict, optional): Output options.
        relative_dir (str, optional): Source sub-folder kept under the output folder.

    Returns:
        list: Written file paths.
    """
    resolved = resolve_output_options(options)
    directory = get_file_output_dir(output_dir, source_path, resolved, relative_dir)
    prefix = get_file_prefix(source_path)
    written = []
    if resolved["summary_per_file"]:
        lines = batch_summary.build_file_summary_lines(report, source_path)
        written.append(write_text_file(os.path.join(directory, f"{prefix}_summary.txt"), "\n".join(lines)))
    if resolved["report_per_file"]:
        payload = evaluation.strip_series(report)
        payload["source"] = str(source_path or "")
        written.append(write_json_file(os.path.join(directory, f"{prefix}_report.json"), payload))
    if resolved["graphs_per_file"]:
        if not resolved["graphs_only_on_failure"] or report.get("status") == STATUS_FAILED:
            from . import report_graphs

            written.extend(report_graphs.export_report_graphs(report, directory, file_prefix=prefix))
    return written


def write_batch_outputs(entries, output_dir, options=None, settings=None, title=DEFAULT_TITLE):
    """Writes the enabled whole-batch summary, JSON report, and graph.

    Args:
        entries (list): Entries from batch_summary.build_batch_entry, one per evaluated file.
        output_dir (str): Output folder.
        options (dict, optional): Output options.
        settings (dict, optional): Evaluation settings recorded in the batch report.
        title (str): Title used in the summary and graph.

    Returns:
        list: Written file paths.
    """
    resolved = resolve_output_options(options)
    written = []
    if resolved["summary_batch"]:
        lines = batch_summary.build_batch_summary_lines(entries, title=title)
        written.append(write_text_file(os.path.join(output_dir, BATCH_SUMMARY_FILE_NAME), "\n".join(lines)))
    if resolved["report_batch"]:
        payload = batch_summary.build_batch_report(entries, settings=settings)
        written.append(write_json_file(os.path.join(output_dir, BATCH_REPORT_FILE_NAME), payload))
    if resolved["graphs_batch"]:
        from . import report_graphs

        graph_path = os.path.join(output_dir, BATCH_GRAPH_FILE_NAME)
        if report_graphs.render_batch_chart(batch_summary.build_batch_chart(entries, title=title), graph_path):
            written.append(graph_path)
    return written


def write_text_file(file_path, text):
    """Writes a UTF-8 text file through a temporary file, so readers never see partial data.

    Args:
        file_path (str): Destination path. Its folder is created when missing.
        text (str): Contents.

    Returns:
        str: Written path.
    """
    directory = os.path.dirname(file_path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    temporary_path = f"{file_path}.{os.getpid()}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as output_file:
        output_file.write(text + "\n")
    os.replace(temporary_path, file_path)
    return file_path


def write_json_file(file_path, data):
    """Writes indented JSON through a temporary file.

    Args:
        file_path (str): Destination path.
        data (dict): JSON-compatible data.

    Returns:
        str: Written path.
    """
    return write_text_file(file_path, json.dumps(data, indent=4, sort_keys=True))
