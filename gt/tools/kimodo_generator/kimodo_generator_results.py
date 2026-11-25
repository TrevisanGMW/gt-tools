"""Pure result-status and narrowly scoped local download cleanup helpers."""

import hashlib
import os
from gt.core.io import read_json_dict
from gt.utils import kimodo


def local_status(job):
    """Checks tracked files independently of the remote generation state.

    Args:
        job (dict): History entry with downloaded paths.

    Returns:
        str: downloaded, missing files, download failed, or not downloaded.
    """
    paths = job.get("paths", {})
    if paths:
        expected = {item["name"] for item in job.get("artifacts", [])} | {"result.json"}
        if expected - set(paths) or any(not os.path.isfile(path) for path in paths.values()):
            return "missing files"
        return "downloaded"
    return "download failed" if job.get("download_error") else "not downloaded"


def maya_status(job):
    """Reports optional scene export state independently of downloaded motion files.

    Args:
        job (dict): History entry.

    Returns:
        str: Scene export state.
    """
    if job.get("exporting_maya"):
        return "creating Maya files"
    if job.get("maya_export_error"):
        return "Maya export failed"
    if job.get("maya_files"):
        if any(not os.path.isfile(path) for path in job["maya_files"].values()):
            return "Maya files missing"
        return "ready"
    return "not created"


def display_status(job):
    """Returns a user-facing status without overwriting the server's job state.

    Args:
        job (dict): Persisted job entry.

    Returns:
        str: Combined local/server status for the table.
    """
    if job.get("cleanup_error"):
        return "cleanup failed"
    if job.get("cleanup_requested"):
        return "cleanup pending"
    if job.get("downloading"):
        return "downloading"
    maya = maya_status(job)
    if maya not in ("ready", "not created"):
        return maya
    local = local_status(job)
    if local != "not downloaded":
        return local
    if job.get("status") == "succeeded" and job.get("operation") != "download_model":
        return "ready to download"
    return job["status"]


def display_stage_and_request(job):
    """Builds useful stage and request details for a compact results-table cell.

    Args:
        job (dict): Persisted generation or model-download entry.

    Returns:
        str: Title-cased stage followed by model and request details.
    """
    stage = str(job.get("stage") or job.get("status") or "Unknown").replace("_", " ").title()
    definition = job.get("definition") if isinstance(job.get("definition"), dict) else {}
    resolved = job.get("resolved") if isinstance(job.get("resolved"), dict) else {}
    model = definition.get("model") or resolved.get("model")
    details = [stage]
    if model:
        details.append(str(model))
    if job.get("operation") == "download_model":
        details.append("Model Download")
        return " · ".join(details)
    prompts = definition.get("prompts") if isinstance(definition.get("prompts"), list) else []
    parameters = definition.get("parameters") if isinstance(definition.get("parameters"), dict) else {}
    if prompts:
        try:
            duration = sum(float(segment.get("duration_seconds", 0)) for segment in prompts)
        except (TypeError, ValueError):
            duration = 0
        segment_label = "Segment" if len(prompts) == 1 else "Segments"
        request = f"{duration:g}s / {len(prompts)} {segment_label}"
        if parameters.get("diffusion_steps") is not None:
            request += f" / {parameters['diffusion_steps']} Steps"
        details.append(request)
    return " · ".join(details)


def delete_local_artifacts(job, dry_run=False):
    """Deletes the validated local directory belonging to a selected job.

    Args:
        job (dict): History entry identifying the downloaded job.
        dry_run (bool): Validate and report without deleting files.

    Returns:
        dict: Deleted or planned paths, preserved paths, and the job directory.
    """
    import shutil

    paths = job.get("paths", {})
    directory = job.get("download_directory", "")
    if paths:
        if any(not os.path.isabs(path) for path in paths.values()):
            raise ValueError("Downloaded paths must be absolute.")
        directories = {os.path.dirname(os.path.abspath(path)) for path in paths.values()}
        if len(directories) != 1:
            raise ValueError("Downloaded paths do not share one job directory.")
        recorded_directory = directories.pop()
        if directory and os.path.normcase(os.path.abspath(directory)) != os.path.normcase(recorded_directory):
            raise ValueError("Downloaded directory does not match recorded paths.")
        directory = recorded_directory
    if not directory:
        return {"deleted": [], "preserved": [], "directory": ""}
    job_id = job["job_id"]
    kimodo._validate_job_id(job_id)
    if not os.path.isabs(directory) or os.path.basename(os.path.normpath(directory)) != job_id:
        raise ValueError("Local folder is not this job's absolute ID directory.")
    directory = kimodo._validate_job_directory(os.path.dirname(os.path.normpath(directory)), job_id)
    manifest_path = os.path.join(directory, "result.json")
    if os.path.isfile(manifest_path):
        manifest = read_json_dict(manifest_path)
        if manifest and manifest.get("job_id") != job_id:
            raise ValueError("Local manifest belongs to another job.")
    deleted = [directory] if os.path.isdir(directory) else []
    if deleted and not dry_run:
        shutil.rmtree(directory)
    return {"deleted": deleted, "preserved": [], "directory": directory}
