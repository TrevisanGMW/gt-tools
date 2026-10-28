"""Import-safe contracts and validation for nested Batch Processor runs."""

import datetime
import json
import os
import re
import tempfile


SCHEMA_VERSION = 1
ANCESTRY_VARIABLE = "GT_BATCH_PROJECT_ANCESTRY"
RUN_DIRECTORY_VARIABLE = "GT_BATCH_PROJECT_RUN_DIRECTORY"
QUEUE_MODES = ["Independent", "Ordered Chain", "Groups"]
DEPENDENCY_OUTCOMES = ["Completion", "Success", "Failure"]
WINDOW_POLICIES = ["Keep Open", "Close When Finished", "Close On Success"]
FAILURE_POLICIES = ["Continue", "Stop Launching"]
SUCCESS_OUTCOMES = {"succeeded", "warning"}


def canonical_path(path):
    """Gets an absolute comparison path, including junction resolution.

    Args:
        path (str): Nonempty filesystem path.

    Returns:
        str: Normalized absolute path.
    """
    if not path or not str(path).strip():
        raise ValueError("A project path is required.")
    return os.path.normcase(os.path.realpath(os.path.abspath(path)))


def read_json(path):
    """Reads a JSON object, tolerating an absent or not-yet-published file.

    Args:
        path (str): JSON file path.

    Returns:
        dict: Parsed object, or an empty dictionary.
    """
    try:
        with open(path, "r", encoding="utf-8") as stream:
            data = json.load(stream)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def write_json(path, data):
    """Publishes JSON atomically without replacing any source project.

    Args:
        path (str): Destination path.
        data (dict): JSON-compatible payload.
    """
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".batch_", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False, sort_keys=True)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)


def parse_start_time(value, reference=None):
    """Parses a short local schedule or a previously saved ISO timestamp.

    Args:
        value (str): HH:MM, MM-DD HH:MM, an ISO timestamp, or empty.
        reference (datetime.datetime, optional): Parent start time. Short dates
            use its local year and short times use its local calendar day.

    Returns:
        datetime.datetime or None: UTC-aware timestamp.

    Raises:
        ValueError: If the timestamp is invalid or an ISO date lacks a timezone.
    """
    if not value or not str(value).strip():
        return None
    text = str(value).strip()
    time_only = bool(re.fullmatch(r"\d{1,2}:\d{2}", text))
    short_date = bool(re.fullmatch(r"\d{1,2}-\d{1,2}\s+\d{1,2}:\d{2}", text))
    if time_only or short_date:
        local_reference = (reference or datetime.datetime.now(datetime.timezone.utc)).astimezone()
        pattern = "%H:%M" if time_only else "%m-%d %H:%M"
        # Supplying a leap year permits February 29 before applying the actual year.
        parsed = datetime.datetime.strptime(f"2000 {text}", f"%Y {pattern}")
        parsed = parsed.replace(year=local_reference.year)
        if time_only:
            parsed = parsed.replace(month=local_reference.month, day=local_reference.day)
        return parsed.astimezone(datetime.timezone.utc)
    parsed = datetime.datetime.fromisoformat(text.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("Scheduled times require a timezone, for example 2026-10-21T22:00:00-07:00.")
    return parsed.astimezone(datetime.timezone.utc)


def is_ignored_project(source_path, task, project):
    """Checks whether a launch input is the current project and should be ignored.

    Args:
        source_path (str): Candidate child project.
        task (BatchTask): Task defining the input policy.
        project (BatchProcessorModel): Current parent project.

    Returns:
        bool: Whether the candidate must be excluded before queueing.
    """
    return bool(task and task.task_type == "run_batch_project" and task.settings.get("ignore_self", True)
                and project.project_file_path
                and canonical_path(source_path) == canonical_path(project.project_file_path))


def filter_project_inputs(source_files, task, project):
    """Excludes the launching project while preserving all other input ordering.

    Args:
        source_files (list): Discovered paths.
        task (BatchTask): First processing task.
        project (BatchProcessorModel): Parent model.

    Returns:
        list: Eligible input paths.
    """
    return [path for path in source_files if not is_ignored_project(path, task, project)]


def get_ancestry(source_path, parent_path="", maximum_depth=4):
    """Validates nesting and returns the child's project ancestry.

    Args:
        source_path (str): Child source project.
        parent_path (str, optional): Original parent project.
        maximum_depth (int, optional): Maximum number of nested projects.

    Returns:
        list: Canonical ancestor and child paths.
    """
    try:
        ancestors = json.loads(os.environ.get(ANCESTRY_VARIABLE, "[]"))
    except ValueError as error:
        raise ValueError("Invalid inherited batch project ancestry.") from error
    if not isinstance(ancestors, list) or any(not isinstance(path, str) for path in ancestors):
        raise ValueError("Invalid inherited batch project ancestry.")
    ancestors = [canonical_path(path) for path in ancestors]
    if parent_path:
        parent = canonical_path(parent_path)
        if not ancestors or ancestors[-1] != parent:
            ancestors.append(parent)
    child = canonical_path(source_path)
    if child in ancestors:
        raise ValueError(f"Recursive batch project launch: {source_path}")
    if len(ancestors) >= int(maximum_depth) + 1:
        raise ValueError(f"Maximum nested project depth ({maximum_depth}) exceeded.")
    return ancestors + [child]


def prepare_project(source_path, settings, parent_path=""):
    """Loads a child and applies overrides exclusively to its in-memory model.

    Args:
        source_path (str): Original .batch project.
        settings (dict): Launch task settings.
        parent_path (str, optional): Original parent project.

    Returns:
        tuple: Child model and ancestry.
    """
    from gt.tools.batch_processor.batch_processor_model import BatchProcessorModel

    if os.path.splitext(source_path)[1].lower() != ".batch" or not os.path.isfile(source_path):
        raise ValueError(f"Expected an existing .batch project: {source_path}")
    ancestry = get_ancestry(source_path, parent_path, settings.get("maximum_depth", 4))
    project = BatchProcessorModel.from_file(source_path)
    for key in ("worker_count", "timeout_minutes", "max_retries"):
        if settings.get(f"override_{key}"):
            project.run_settings[key] = int(settings[key])
    project.run_settings["purge_logs_on_run"] = False
    return project, ancestry


def build_result(session, retry_counts=None, run_id="", parent_run_id="", empty_policy="Warning"):
    """Builds a final outcome from terminal jobs rather than cumulative history.

    Args:
        session (TrackerSession): Completed tracker session.
        retry_counts (dict, optional): Retry counts indexed by job ID.
        run_id (str, optional): Unique child run ID.
        parent_run_id (str, optional): Parent run ID.
        empty_policy (str, optional): Warning or Failure for empty runs.

    Returns:
        dict: Versioned immutable project result.
    """
    from gt.tools.batch_processor.tracker.tracker_constants import Status

    retry_counts = retry_counts or {}
    counts = {"succeeded": 0, "failed": 0, "timed_out": 0, "canceled": 0,
              "blocked": 0, "skipped": 0, "warnings": 0, "retried": sum(retry_counts.values())}
    for job in session.jobs:
        if job.status == Status.TIMED_OUT:
            counts["timed_out"] += 1
        elif job.status == Status.CANCELED:
            counts["canceled"] += 1
        elif job.status == Status.BLOCKED:
            counts["blocked"] += 1
        elif job.status == Status.FAILED or job.errors or any(
                task.status not in (Status.COMPLETED, Status.COMPLETED_WARNINGS, Status.SKIPPED)
                for task in job.tasks):
            counts["failed"] += 1
        elif job.status == Status.SKIPPED:
            counts["skipped"] += 1
        elif job.status in (Status.COMPLETED, Status.COMPLETED_WARNINGS):
            counts["succeeded"] += 1
        else:
            counts["failed"] += 1
        counts["warnings"] += job.warnings
    empty = not any(job.tasks and not getattr(job, "empty", False) for job in session.jobs)
    if session.aborting or counts["canceled"]:
        outcome = "canceled"
    elif counts["failed"] or counts["timed_out"] or counts["blocked"] or (empty and empty_policy == "Failure"):
        outcome = "failed"
    elif empty or counts["warnings"] or counts["retried"] or counts["skipped"]:
        outcome = "warning"
    else:
        outcome = "succeeded"
    return {
        "schema_version": SCHEMA_VERSION, "run_id": run_id, "parent_run_id": parent_run_id,
        "source_project_file": session.source_project_file, "outcome": outcome,
        "started_at": session.started_at, "completed_at": session.completed_at,
        "session_dir": session.session_dir, "project_log_path": session.project_log_path,
        "counts": counts, "empty": empty, "finished": True,
        "reason": "No work discovered." if empty else f"Project {outcome}.",
    }
