"""Pure helpers for handing an open Batch Processor session over to another process."""

import json
import os
import tempfile


HANDOFF_SCHEMA_VERSION = 1
RECOVERY_FILE_NAME = "recovery.json"
READY_FILE_NAME = "ready.json"
READY_STATUS = "ready"
FAILED_STATUS = "failed"


def create_handoff_directory():
    """Creates a private temporary folder for one hand-off.

    Returns:
        str: Folder path.
    """
    return tempfile.mkdtemp(prefix="gt_batch_relaunch_")


def build_recovery_payload(project_data, source_project_file, saved_state):
    """Builds the data needed to continue an open project in another process.

    Args:
        project_data (dict): Current project data, including unsaved changes.
        source_project_file (str): Saved project path, or empty for an untitled project.
        saved_state (dict): Project data as of the last save, used to keep the unsaved-changes
            marker accurate. None when the project was never marked clean.

    Returns:
        dict: Serializable recovery payload.
    """
    return {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "project": project_data,
        "source_project_file": source_project_file or "",
        "saved_state": saved_state,
    }


def write_json_file(file_path, data):
    """Writes JSON atomically so a reader never sees a half-written file.

    Args:
        file_path (str): Destination path.
        data (dict): Serializable data.
    """
    temporary_path = f"{file_path}.tmp"
    with open(temporary_path, "w", encoding="utf-8") as json_file:
        json.dump(data, json_file, indent=2, sort_keys=True)
    os.replace(temporary_path, file_path)


def read_json_file(file_path):
    """Reads a JSON object, tolerating a missing or unreadable file.

    Args:
        file_path (str): File path.

    Returns:
        dict: File contents, or an empty dict.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def write_ready_file(file_path, status=READY_STATUS, error=""):
    """Tells the launching process whether the hand-off worked.

    Args:
        file_path (str): Ready file path. Ignored when empty.
        status (str, optional): ``ready`` or ``failed``.
        error (str, optional): Failure description.
    """
    if file_path:
        write_json_file(file_path, {"status": status, "error": str(error)})
