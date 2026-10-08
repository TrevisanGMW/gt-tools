"""Optional ClearML helpers for Maya, batch scripts, and ordinary Python.

Importing this module neither imports ClearML nor connects to a server. Dataset
uploads create immutable, parent-linked revisions under a stable project/name.
No helper initializes a current Task or changes the executing Maya process into
a ClearML agent. Configure the optional SDK through clearml.conf or environment
variables before calling a network operation.
"""

import hashlib
import importlib
import json
import logging
import os
import re
import time
from collections import Counter
from datetime import datetime, timezone


logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
FINAL_DATASET_STATUSES = ("completed", "published", "closed")
ACTIVE_DATASET_STATUSES = ("created", "in_progress", "queued")


class ClearMLUnavailableError(ImportError):
    """Indicates that the optional SDK or one of its dependencies is missing."""


class DatasetUploadError(RuntimeError):
    """Reports an unsuccessful upload and retains its draft dataset ID."""

    def __init__(self, dataset_id, stage, error):
        """Builds a failure message suitable for a UI or batch log.

        Args:
            dataset_id (str): Created draft, which is retained for diagnosis.
            stage (str): Operation that failed.
            error (Exception): Underlying failure.
        """
        self.dataset_id = dataset_id
        self.stage = stage
        super().__init__(f"Dataset {dataset_id} failed during {stage}: {error}. Draft retained.")


def _get_sdk():
    """Loads the optional SDK only when it is required.

    Returns:
        module: Imported ClearML SDK.

    Raises:
        ClearMLUnavailableError: ClearML or a dependency cannot be imported.
    """
    try:
        return importlib.import_module("clearml")
    except ImportError as error:
        raise ClearMLUnavailableError(
            "ClearML is unavailable in this Python environment. Use a Python "
            "interpreter with the clearml SDK installed and configured."
        ) from error


def is_clearml_available():
    """Checks SDK importability without authenticating or installing packages.

    Returns:
        bool: Whether ClearML and its required dependencies can be imported.
    """
    try:
        _get_sdk()
        return True
    except ClearMLUnavailableError:
        return False


def _required_text(value, label):
    """Validates an explicit string without inventing a fallback.

    Args:
        value (str): Requested value.
        label (str): Field name used in the error.

    Returns:
        str: Stripped, nonempty text.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} is required.")
    return value.strip()


def _directory_path(directory):
    """Resolves an existing directory while rejecting unset input.

    Args:
        directory (str or os.PathLike): Source folder.

    Returns:
        str: Absolute, canonical folder path.
    """
    path = _required_text(os.fspath(directory), "Source directory")
    path = os.path.realpath(os.path.abspath(os.path.expanduser(path)))
    if not os.path.isdir(path):
        raise ValueError(f"Source directory does not exist: {path}")
    return path


def _raise_walk_error(error):
    """Prevents unreadable subfolders from being silently omitted.

    Args:
        error (OSError): Directory traversal failure.
    """
    raise error


def inspect_directory(directory):
    """Counts every file recursively without requiring ClearML or Maya.

    Hidden files are included. Symlinks, junctions, and paths escaping the root
    are rejected so the preview and upload cover the same bounded source tree.
    The signature detects changes to paths, sizes, and modification times; it
    is not a content checksum. ClearML hashes file contents during staging.

    Args:
        directory (str or os.PathLike): Existing source folder.

    Returns:
        dict: Canonical directory, file records, counts, sizes, extension counts,
            and a source signature. File paths use relative forward slashes.
    """
    root = _directory_path(directory)
    records = []
    directory_count = 0
    for current_root, directories, filenames in os.walk(root, onerror=_raise_walk_error):
        directories.sort()
        for name in directories + sorted(filenames):
            path = os.path.join(current_root, name)
            resolved = os.path.realpath(path)
            if os.path.islink(path) or os.path.normcase(resolved) != os.path.normcase(path):
                raise ValueError(f"Linked paths are unsupported: {path}")
            if os.path.commonpath([root, resolved]) != root:
                raise ValueError(f"Path escapes the source folder: {path}")
        directory_count += len(directories)
        for filename in sorted(filenames):
            path = os.path.join(current_root, filename)
            if not os.path.isfile(path):
                raise ValueError(f"Unsupported source entry: {path}")
            stat_result = os.stat(path)
            records.append({
                "path": os.path.relpath(path, root).replace(os.sep, "/"),
                "size_bytes": stat_result.st_size,
                "modified_ns": stat_result.st_mtime_ns,
            })
    records.sort(key=lambda entry: entry["path"])
    extensions = Counter(os.path.splitext(entry["path"])[1].lower() or "(no extension)"
                         for entry in records)
    signature = hashlib.sha256(json.dumps(records, sort_keys=True).encode("utf-8")).hexdigest()
    return {
        "directory": root,
        "files": records,
        "file_count": len(records),
        "directory_count": directory_count,
        "size_bytes": sum(entry["size_bytes"] for entry in records),
        "extension_counts": dict(sorted(extensions.items())),
        "source_signature": signature,
    }


def _list_service(service_name, fields):
    """Paginates a read-only API service without initializing a Task.

    Args:
        service_name (str): SDK service name.
        fields (list): Public fields to retrieve.

    Returns:
        list: Plain dictionaries returned by the service.
    """
    _get_sdk()
    from clearml.backend_api.session.client import APIClient

    service = getattr(APIClient(), service_name)
    items = []
    page = 0
    while True:
        batch = [item.to_dict() for item in service.get_all(
            page=page, page_size=500, only_fields=fields)]
        items.extend(batch)
        if len(batch) < 500:
            return items
        page += 1


def list_projects():
    """Lists visible projects, including their full hierarchy paths.

    Returns:
        list: Project dictionaries containing IDs, names, and descriptions.
    """
    return sorted(_list_service("projects", ["id", "name", "description"]),
                  key=lambda entry: entry["name"])


def list_queues():
    """Lists existing agent queues without creating or changing them.

    Returns:
        list: Queue dictionaries containing IDs and names.
    """
    return sorted(_list_service("queues", ["id", "name"]), key=lambda entry: entry["name"])


def list_datasets(project_name=None, dataset_name=None, only_completed=True, include_archived=False):
    """Lists revisions using literal names and an exact project scope.

    Args:
        project_name (str, optional): Full project path; excludes subprojects.
        dataset_name (str, optional): Exact stable dataset name.
        only_completed (bool, optional): Excludes unfinished revisions.
        include_archived (bool, optional): Include archived revisions in read-only results.

    Returns:
        list: JSON-compatible revision records. Archives are excluded by default.
    """
    if project_name is not None:
        project_name = _required_text(project_name, "Project name")
    if dataset_name is not None:
        dataset_name = _required_text(dataset_name, "Dataset name")
    entries = _get_sdk().Dataset.list_datasets(
        dataset_project=project_name,
        partial_name=f"^{re.escape(dataset_name)}$" if dataset_name else None,
        only_completed=only_completed,
        recursive_project_search=False,
        include_archived=include_archived,
    )
    return [dict(entry, created=str(entry.get("created", "")), status=str(entry.get("status", "")))
            for entry in entries
            if (project_name is None or entry.get("project") == project_name)
            and (dataset_name is None or entry.get("name") == dataset_name)]


def _latest_revision(entries):
    """Selects the most recently created finalized revision deterministically.

    Args:
        entries (list): Revision dictionaries for one project/name family.

    Returns:
        dict or None: Latest finalized record, or None for a new family.
    """
    completed = [entry for entry in entries if entry.get("status") in FINAL_DATASET_STATUSES]
    return max(completed, key=lambda entry: (entry.get("created", ""), entry["id"])) if completed else None


def _predict_dataset_version(entries):
    """Estimates the SDK's automatic version using its own version parser.

    Args:
        entries (list): All known revisions, including archived revisions.

    Returns:
        str or None: Expected version, or None if the SDK cannot compare labels.
    """
    if not entries:
        return "1.0.0"
    version_class = importlib.import_module("clearml.utilities.version").Version
    versions = [version_class(entry["version"]) for entry in entries
                if version_class.is_valid_version_string(entry.get("version"))]
    try:
        return str(max(versions).get_next_version()) if versions else "1.0.0"
    except (TypeError, ValueError):
        return None


def get_dataset_target_info(project_name, dataset_name, dataset_version=None):
    """Reads an exact upload target without downloading data or recording lineage.

    Automatic versions are estimates: SDK allocation may race with another client.
    Archived versions influence the estimate, but are not selected as parents.

    Args:
        project_name (str): Exact public project path, excluding child projects.
        dataset_name (str): Literal dataset family name.
        dataset_version (str, optional): Explicit version override to check.

    Returns:
        dict: Existence, finalized parent, revision counts, version estimate, and blockers.
    """
    project_name = _required_text(project_name, "Project name")
    dataset_name = _required_text(dataset_name, "Dataset name")
    if dataset_version is not None:
        dataset_version = _required_text(dataset_version, "Dataset version")
    entries = list_datasets(project_name, dataset_name, only_completed=False)
    all_entries = list_datasets(project_name, dataset_name, only_completed=False, include_archived=True)
    parent = _latest_revision(entries)
    active_ids = [entry["id"] for entry in entries if entry.get("status") in ACTIVE_DATASET_STATUSES]
    blockers = []
    if active_ids:
        blockers.append(f"Active draft/upload: {', '.join(active_ids)}")
    if entries and parent is None:
        blockers.append("No finalized revision is available; review unfinished or failed revisions.")
    if dataset_version and any(entry.get("version") == dataset_version for entry in all_entries):
        blockers.append(f"Version {dataset_version} already exists. Choose an unused version.")
    return {
        "project_name": project_name, "dataset_name": dataset_name,
        "exists": bool(all_entries), "revision_count": len(entries),
        "archived_revision_count": len({entry["id"] for entry in all_entries}
                                       - {entry["id"] for entry in entries}),
        "parent_id": parent["id"] if parent else None,
        "parent_version": parent.get("version") if parent else None,
        "next_version": dataset_version or _predict_dataset_version(all_entries),
        "version_is_estimate": dataset_version is None, "blockers": blockers,
    }


def get_dataset(dataset_id=None, project_name=None, dataset_name=None):
    """Gets a finalized dataset by pinned ID or exact project/name.

    Name lookup uses creation time, so automatic uploads extend the most recent
    finalized revision even when legacy versions contain dates or custom text.
    As with the SDK, using a dataset inside a current Task can record lineage on
    that Task. Catalog listing through list_datasets does not record lineage.

    Args:
        dataset_id (str, optional): Immutable revision ID; preferred by workers.
        project_name (str, optional): Required for lookup by name.
        dataset_name (str, optional): Required for lookup by name.

    Returns:
        clearml.Dataset: Finalized dataset handle.
    """
    if dataset_id:
        dataset_id = _required_text(dataset_id, "Dataset ID")
    else:
        project_name = _required_text(project_name, "Project name")
        dataset_name = _required_text(dataset_name, "Dataset name")
        record = _latest_revision(list_datasets(project_name, dataset_name))
        if not record:
            raise ValueError(f"No finalized dataset found: {project_name}/{dataset_name}")
        dataset_id = record["id"]
    dataset = _get_sdk().Dataset.get(dataset_id=dataset_id, auto_create=False,
                                    writable_copy=False, silence_alias_warnings=True)
    if not dataset.is_final():
        raise ValueError(f"Dataset {dataset_id} is not finalized.")
    return dataset


def preview_dataset_upload(directory, dataset_name, project_name, update_mode="overlay"):
    """Builds an upload plan without creating or modifying a dataset.

    Args:
        directory (str or os.PathLike): Folder to upload recursively.
        dataset_name (str): Stable dataset family name.
        project_name (str): Full project path.
        update_mode (str, optional): overlay retains absent inherited files;
            snapshot omits them from the new revision.

    Returns:
        dict: Source summary, parent ID/version, and proposed removed paths.

    Raises:
        ValueError: Empty source, invalid mode, or another upload is active.
    """
    dataset_name = _required_text(dataset_name, "Dataset name")
    project_name = _required_text(project_name, "Project name")
    if update_mode not in ("overlay", "snapshot"):
        raise ValueError("Update mode must be overlay or snapshot.")
    summary = inspect_directory(directory)
    if not summary["file_count"]:
        raise ValueError("The source folder contains no files.")
    entries = list_datasets(project_name, dataset_name, only_completed=False)
    active = [entry["id"] for entry in entries if entry.get("status") in ACTIVE_DATASET_STATUSES]
    if active:
        raise ValueError(f"This dataset has an active draft/upload: {', '.join(active)}")
    parent_record = _latest_revision(entries)
    if entries and parent_record is None:
        raise ValueError("Existing revisions are unfinished or failed; inspect them before retrying.")
    removed_files = []
    if parent_record and update_mode == "snapshot":
        parent = get_dataset(dataset_id=parent_record["id"])
        source_paths = {entry["path"] for entry in summary["files"]}
        removed_files = sorted(set(parent.list_files()) - source_paths)
    return dict(summary, dataset_name=dataset_name, project_name=project_name,
                update_mode=update_mode, parent_id=parent_record["id"] if parent_record else None,
                parent_version=parent_record.get("version") if parent_record else None,
                removed_files=removed_files, status="preview")


def upload_directory(directory, dataset_name, project_name, commit_message,
                     update_mode="overlay", tags=None, output_uri=None, dataset_version=None,
                     dry_run=False, allow_removed_files=False, expected_parent_id=None,
                     expected_source_signature=None, progress_callback=None):
    """Uploads a folder as a new, parent-linked revision with a commit message.

    Every file, including hidden files and nested folders, is included. Local
    inputs and older revisions are preserved. Network/authentication errors are
    propagated; they are never interpreted as a missing dataset. Failed drafts
    are retained and their ID is included in DatasetUploadError.

    Args:
        directory (str or os.PathLike): Existing, nonempty source folder.
        dataset_name (str): Stable dataset name, unchanged between revisions.
        project_name (str): Full project path; created by the SDK if absent.
        commit_message (str): Description of this revision's changes; may be empty.
        update_mode (str, optional): overlay or snapshot; default is overlay.
        tags (list, optional): None copies the finalized parent's user tags;
            a supplied list replaces them for the new revision. An empty list
            explicitly clears them. New families have no automatic tags.
        output_uri (str, optional): Storage URI; None uses SDK configuration.
        dataset_version (str, optional): Version field; None lets the SDK increment.
        dry_run (bool, optional): Returns the read-only plan without writing.
        allow_removed_files (bool, optional): Explicit approval for snapshot omissions.
        expected_parent_id (str, optional): Abort if the latest parent changed;
            use an empty string to require that the family is still new.
        expected_source_signature (str, optional): Abort if the preview changed.
        progress_callback (callable, optional): Receives a stage text message.

    Returns:
        dict: Preview or success record containing revision ID/version and parent.

    Raises:
        ValueError: Validation fails before dataset creation.
        DatasetUploadError: Staging, upload, or finalization fails after creation.
    """
    if not isinstance(commit_message, str):
        raise ValueError("Commit message must be a string (empty is allowed).")
    commit_message = commit_message.strip()
    if tags is not None and (not isinstance(tags, (list, tuple))
                             or any(not isinstance(tag, str) or not tag.strip() for tag in tags)):
        raise ValueError("Tags must be a list of nonempty strings.")
    if dataset_version is not None:
        dataset_version = _required_text(dataset_version, "Dataset version")
    if output_uri is not None:
        output_uri = _required_text(output_uri, "Output URI")
    plan = preview_dataset_upload(directory, dataset_name, project_name, update_mode)
    if expected_parent_id is not None and (plan["parent_id"] or "") != expected_parent_id:
        raise ValueError("The latest dataset revision changed. Preview again before uploading.")
    if expected_source_signature and plan["source_signature"] != expected_source_signature:
        raise ValueError("The source folder changed. Preview again before uploading.")
    if dataset_version is not None:
        versions = list_datasets(plan["project_name"], plan["dataset_name"],
                                 only_completed=False, include_archived=True)
        if any(entry.get("version") == dataset_version for entry in versions):
            raise ValueError(f"Version {dataset_version} already exists. Choose an unused version.")
    if dry_run:
        return dict(plan, commit_message=commit_message)
    if plan["removed_files"] and not allow_removed_files:
        raise ValueError(f"Snapshot would omit {len(plan['removed_files'])} inherited files. "
                         "Review the dry run and set allow_removed_files=True to continue.")
    parent = get_dataset(dataset_id=plan["parent_id"]) if plan["parent_id"] else None
    revision_tags = list(parent.tags or []) if tags is None and parent else list(tags or [])
    _report_progress(progress_callback, "Creating a new dataset revision")
    dataset = _get_sdk().Dataset.create(
        dataset_name=plan["dataset_name"], dataset_project=plan["project_name"],
        parent_datasets=[parent] if parent else [], use_current_task=False,
        description=commit_message, dataset_tags=revision_tags,
        output_uri=output_uri, dataset_version=dataset_version,
    )
    stage = "staging"
    try:
        _report_progress(progress_callback, f"Staging {plan['file_count']} files")
        if update_mode == "snapshot":
            dataset.sync_folder(local_path=plan["directory"], verbose=False)
        else:
            dataset.add_files(path=plan["directory"], local_base_folder=plan["directory"],
                              recursive=True, verbose=False)
        if inspect_directory(plan["directory"])["source_signature"] != plan["source_signature"]:
            raise ValueError("Source files changed while staging. Preview again before retrying.")
        dataset.set_metadata({
            "commit_message": commit_message, "update_mode": update_mode,
            "file_count": plan["file_count"], "size_bytes": plan["size_bytes"],
            "parent_id": plan["parent_id"],
            "uploaded_at_utc": datetime.now(timezone.utc).isoformat(),
        }, metadata_name="gt_tools_upload")
        stage = "upload"
        _report_progress(progress_callback, "Uploading files")
        if dataset.upload(show_progress=False, verbose=False) is False:
            raise RuntimeError("The SDK reported an unsuccessful upload.")
        stage = "finalization"
        _report_progress(progress_callback, "Finalizing the dataset revision")
        if not dataset.finalize(auto_upload=False, raise_on_error=True):
            raise RuntimeError("The SDK did not finalize the dataset.")
    except Exception as error:
        logger.exception("Dataset %s failed during %s", dataset.id, stage)
        raise DatasetUploadError(dataset.id, stage, error) from error
    result = {
        "status": "succeeded", "dataset_id": dataset.id, "version": dataset.version,
        "dataset_name": plan["dataset_name"], "project_name": plan["project_name"],
        "parent_id": plan["parent_id"], "commit_message": commit_message,
        "update_mode": update_mode, "file_count": plan["file_count"],
        "size_bytes": plan["size_bytes"], "removed_files": plan["removed_files"],
        "tags": revision_tags,
    }
    logger.info("Uploaded %s/%s revision %s (%s), %s source files", project_name,
                dataset_name, dataset.version, dataset.id, plan["file_count"])
    _report_progress(progress_callback, f"Uploaded revision {dataset.version}: {dataset.id}")
    return result


def _report_progress(callback, message):
    """Reports status without allowing a UI failure to break an upload.

    Args:
        callback (callable or None): Optional progress receiver.
        message (str): Human-readable stage.
    """
    if callback:
        try:
            callback(message)
        except Exception:
            logger.exception("ClearML progress receiver failed")


def download_dataset(dataset_id=None, project_name=None, dataset_name=None):
    """Downloads a finalized revision into the SDK's managed local cache.

    Treat the returned directory as read-only. Copy files into your own output
    directory before editing them or producing a new dataset revision.

    Args:
        dataset_id (str, optional): Pinned revision ID.
        project_name (str, optional): Full project path for name lookup.
        dataset_name (str, optional): Stable name for name lookup.

    Returns:
        str: Local cache directory containing the resolved dataset files.
    """
    return get_dataset(dataset_id, project_name, dataset_name).get_local_copy(raise_on_error=True)


def list_dataset_files(dataset_id):
    """Lists the resolved relative paths in a pinned revision.

    Args:
        dataset_id (str): Finalized dataset revision ID.

    Returns:
        list: Sorted relative paths, including inherited files.
    """
    return sorted(get_dataset(dataset_id=dataset_id).list_files())


def list_tasks(project_name, task_name=None, tags=None, include_archived=False):
    """Finds tasks in an exact project using a literal optional task name.

    Args:
        project_name (str): Full project path.
        task_name (str, optional): Exact task name.
        tags (list, optional): SDK tag filters.
        include_archived (bool, optional): Includes archived tasks when True.

    Returns:
        list: SDK Task handles; no tasks are created or enqueued.
    """
    project_name = _required_text(project_name, "Project name")
    if task_name is not None:
        task_name = _required_text(task_name, "Task name")
    sdk = _get_sdk()
    task_ids = sdk.Task.query_tasks(
        project_name=project_name, task_name=f"^{re.escape(task_name)}$" if task_name else None,
        tags=tags, task_filter={} if include_archived else {"system_tags": ["__$not", "archived"]},
    )
    return sdk.Task.get_tasks(task_ids=task_ids) if task_ids else []


def get_task(task_id):
    """Retrieves a task using its stable ID.

    Args:
        task_id (str): ClearML task ID.

    Returns:
        clearml.Task: Existing task handle.
    """
    return _get_sdk().Task.get_task(task_id=_required_text(task_id, "Task ID"))


def get_task_status(task_id):
    """Reads the current server status for a task.

    Args:
        task_id (str): ClearML task ID.

    Returns:
        str: Current status such as queued, in_progress, completed, or failed.
    """
    return str(get_task(task_id).get_status())


def enqueue_task(task_id, queue_name):
    """Enqueues an existing task for execution by a configured ClearML agent.

    Args:
        task_id (str): Created task ID.
        queue_name (str): Existing queue name.

    Returns:
        str: Enqueued task ID. Execution requires an agent listening to the queue.
    """
    task_id = _required_text(task_id, "Task ID")
    queue_name = _required_text(queue_name, "Queue name")
    _get_sdk().Task.enqueue(task=task_id, queue_name=queue_name, force=False)
    return task_id


def run_task(template_task_id, queue_name, task_name=None, parameters=None, project_name=None):
    """Clones a task template, merges parameters, and enqueues the new run.

    The template and current Maya process are preserved. Clone or enqueue
    failures leave the new task available for diagnosis. Dataset inputs should
    be passed as pinned revision IDs in the task's existing parameter keys.

    Args:
        template_task_id (str): Configured executable template task.
        queue_name (str): Existing agent queue.
        task_name (str, optional): Name of the cloned run.
        parameters (dict, optional): Flat SDK parameter keys, e.g. Args/dataset_id.
        project_name (str, optional): Existing destination project; defaults to template.

    Returns:
        str: New enqueued task ID.
    """
    queue_name = _required_text(queue_name, "Queue name")
    if parameters is not None and not isinstance(parameters, dict):
        raise ValueError("Task parameters must be a dictionary.")
    if task_name is not None:
        task_name = _required_text(task_name, "Task name")
    if queue_name not in [entry["name"] for entry in list_queues()]:
        raise ValueError(f"Queue does not exist: {queue_name}")
    sdk = _get_sdk()
    project_id = None
    if project_name is not None:
        project_name = _required_text(project_name, "Project name")
        project_id = sdk.Task.get_project_id(project_name)
        if not project_id:
            raise ValueError(f"Destination project does not exist: {project_name}")
    source = get_task(template_task_id)
    cloned = sdk.Task.clone(source_task=source, name=task_name, project=project_id)
    try:
        if parameters:
            values = dict(cloned.get_parameters() or {})
            values.update(parameters)
            cloned.set_parameters(values)
        return enqueue_task(cloned.id, queue_name)
    except Exception as error:
        raise RuntimeError(f"Task {cloned.id} could not be enqueued: {error}. Clone retained.") from error


def create_task(project_name, task_name, script, repo=None, branch=None, commit=None,
                requirements_file=None):
    """Creates an executable remote task without initializing a current Task.

    Args:
        project_name (str): Target project path.
        task_name (str): User-facing task name.
        script (str): Python entry point; repository-relative when repo is supplied.
        repo (str, optional): Remote repository URL or local repository path.
        branch (str, optional): Repository branch.
        commit (str, optional): Pinned source commit.
        requirements_file (str, optional): Dependency file used by the remote agent.

    Returns:
        str: Created task ID; call enqueue_task explicitly to run it.
    """
    task = _get_sdk().Task.create(
        project_name=_required_text(project_name, "Project name"),
        task_name=_required_text(task_name, "Task name"),
        task_type="data_processing", script=_required_text(script, "Script path"),
        repo=repo, branch=branch, commit=commit, requirements_file=requirements_file,
    )
    return task.id


def upload_task_artifact(task_id, artifact_name, path, metadata=None, overwrite=False):
    """Uploads a file or folder artifact without removing its local source.

    Args:
        task_id (str): Existing task ID.
        artifact_name (str): Stable artifact name.
        path (str or os.PathLike): Local file or folder.
        metadata (dict, optional): Additional artifact metadata.
        overwrite (bool, optional): Allows replacing an existing named artifact.

    Returns:
        bool: True when accepted; False when an existing artifact was skipped.
    """
    artifact_name = _required_text(artifact_name, "Artifact name")
    path = os.path.abspath(os.path.expanduser(_required_text(os.fspath(path), "Artifact path")))
    if not os.path.exists(path):
        raise ValueError(f"Artifact path does not exist: {path}")
    task = get_task(task_id)
    if not overwrite and artifact_name in task.artifacts:
        logger.info("Skipping existing artifact %s on task %s", artifact_name, task_id)
        return False
    return bool(task.upload_artifact(
        name=artifact_name, artifact_object=path, metadata=metadata,
        delete_after_upload=False, wait_on_upload=True,
    ))


def wait_for_task(task_id, timeout=3600, poll_interval=5):
    """Waits for a terminal task status in batch code or a separate process.

    This blocking helper should not run on Maya's UI thread. Completion status
    is returned explicitly; failed and stopped tasks do not count as success.

    Args:
        task_id (str): Task to monitor.
        timeout (float, optional): Maximum elapsed seconds.
        poll_interval (float, optional): Seconds between status requests.

    Returns:
        str: Terminal status: completed, published, closed, failed, or stopped.

    Raises:
        TimeoutError: The task does not reach a terminal status within timeout.
    """
    if timeout <= 0 or poll_interval <= 0:
        raise ValueError("Timeout and poll interval must be positive.")
    deadline = time.monotonic() + timeout
    while True:
        status = get_task_status(task_id)
        if status in ("completed", "published", "closed", "failed", "stopped"):
            return status
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"Timed out waiting for task {task_id}.")
        time.sleep(min(poll_interval, remaining))
