"""Process supervision and preview services for nested batch projects."""

import json
import hashlib
import os
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager

from gt.tools.batch_processor import batch_processor_projects as projects
from gt.tools.batch_processor.batch_processor_task_base import sanitize_filename


LAUNCH_TIMEOUT_SECONDS = 120
HEARTBEAT_TIMEOUT_SECONDS = 120


def preview_projects(task, parent):
    """Resolves child inputs and effective settings without launching or saving.

    Args:
        task (TaskRunBatchProject): Launch task.
        parent (BatchProcessorModel): Parent project.

    Returns:
        list: Preview dictionaries with validation messages.
    """
    rows = []
    segment = next((segment for segment in parent.get_task_segments() if task in segment), [])
    inputs = [candidate for candidate in segment if candidate.is_input_task and candidate.enabled]
    paths = parent.discover_segment_input_files(inputs)
    seen = set()
    roots = {}
    for path in paths:
        row = {"path": path, "errors": [], "warnings": []}
        try:
            if projects.is_ignored_project(path, task, parent):
                row.update(ignored=True, reason="Current project excluded by Auto Ignore This Project.")
                rows.append(row)
                continue
            key = projects.canonical_path(path)
            if key in seen:
                raise ValueError(f"Duplicate project: {path}")
            seen.add(key)
            child, ancestry = projects.prepare_project(path, task.settings, parent.project_file_path)
            validation = child.validate_project()
            row.update({"workers": child.run_settings["worker_count"] if child.run_settings["multi_instance"] else 1,
                        "timeout_minutes": child.run_settings["timeout_minutes"],
                        "max_retries": child.run_settings["max_retries"],
                        "project_dir": child.get_project_dir(),
                        "ancestry": ancestry, "errors": validation.errors, "warnings": validation.warnings})
            row["output_folders"] = sorted({
                candidate.resolve_task_path(child, task_index=child.get_task_environment_index(candidate))
                for candidate in child.get_enabled_tasks()
                if not candidate.is_input_task and candidate.writes_to_target_path()})
            root = projects.canonical_path(child.get_project_dir())
            if root in roots:
                row["warnings"].append(f"Project folder is also used by {roots[root]}; check output collisions.")
            roots[root] = path
        except Exception as error:
            row["errors"].append(str(error))
        rows.append(row)
    return rows


def run_project(task, work_item, parent, context):
    """Launches an isolated child and waits for its durable project result.

    Args:
        task (TaskRunBatchProject): Launch settings.
        work_item (WorkItem): Child project input.
        parent (BatchProcessorModel): Owning project.
        context (dict): Tracker reporting callbacks.

    Returns:
        dict: Successful child result.

    Raises:
        RuntimeError: If the child fails or cannot publish a verified result.
    """
    root = parent.resolve_template_path(task.settings["logs_path"], task=task)
    if not root or not os.path.isabs(root):
        raise ValueError("Child project logs must resolve to an absolute folder.")
    with project_lock(root, work_item.current_path):
        return execute_project(task, work_item, parent, context, root)


@contextmanager
def project_lock(root, source_path):
    """Prevents concurrent launches of the same source in a shared log root.

    Locks are released by the operating system after crashes; lock files remain
    as harmless bookkeeping and never require deleting source data.

    Args:
        root (str): Shared log root.
        source_path (str): Original child project.

    Yields:
        None: Exclusive execution scope.
    """
    lock_dir = os.path.join(root, "project_locks")
    os.makedirs(lock_dir, exist_ok=True)
    digest = hashlib.sha256(projects.canonical_path(source_path).encode("utf-8")).hexdigest()
    with open(os.path.join(lock_dir, f"{digest}.lock"), "a+b") as stream:
        stream.seek(0, os.SEEK_END)
        if stream.tell() == 0:
            stream.write(b"0")
            stream.flush()
        stream.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError(f"Child project is already processing: {source_path}") from error
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == "win32":
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def execute_project(task, work_item, parent, context, root):
    """Prepares artifacts and supervises one exclusively owned child.

    Args:
        task (TaskRunBatchProject): Launch settings.
        work_item (WorkItem): Child input.
        parent (BatchProcessorModel): Parent project.
        context (dict): Tracker callbacks.
        root (str): Validated log root.

    Returns:
        dict: Verified child result.
    """
    from gt.tools.batch_processor import batch_processor_worker
    from gt.tools.batch_processor.tracker import tracker_process_utils

    child, ancestry = projects.prepare_project(
        work_item.current_path, task.settings, parent.project_file_path)
    validation = child.validate_project()
    if validation.errors:
        raise RuntimeError(f"Child project validation failed: {'; '.join(validation.errors)}")
    run_id = uuid.uuid4().hex
    parent_id = str(context.get("run_id") or "run")
    parent_folder = sanitize_filename(parent_id)
    # A display name may contain path separators; it is never a directory path.
    run_dir = os.path.join(root, parent_folder,
                           f"{sanitize_filename(child.project_name)}_{run_id[:12]}")
    os.makedirs(run_dir, exist_ok=False)
    snapshot = os.path.join(run_dir, "effective.batch")
    data = child.to_dict()
    data["environment_variables"]["project-dir"] = child.get_project_dir()
    data["runtime_options"] = {"source_project_file": work_item.current_path}
    projects.write_json(snapshot, data)
    request = {"project_file": snapshot, "source_project_file": work_item.current_path,
               "run_id": run_id, "parent_run_id": parent_id, "run_dir": run_dir,
               "settings": task.settings}
    request_path = os.path.join(run_dir, "request.json")
    projects.write_json(request_path, request)
    result_path = os.path.join(run_dir, "result.json")
    control_path = os.path.join(run_dir, "control.json")
    log_path = os.path.join(run_dir, "launcher.log")
    executable, warning = batch_processor_worker.resolve_mayapy_executable(
        child.run_settings.get("preferred_maya_version"))
    environment = dict(os.environ)
    environment.pop("GT_BATCH_RUN_STATE", None)
    environment[projects.ANCESTRY_VARIABLE] = json.dumps(ancestry)
    environment[projects.RUN_DIRECTORY_VARIABLE] = run_dir
    environment["PYTHONIOENCODING"] = "utf-8"
    command = [executable, os.path.join(os.path.dirname(__file__), "tracker", "project_main.py"),
               "--request-file", request_path]
    process = None
    report_log = context.get("report_log")
    for artifact in (log_path, snapshot, request_path, result_path, os.path.join(run_dir, "project.log")):
        if callable(report_log):
            report_log(artifact)
    try:
        with open(log_path, "a", encoding="utf-8") as output:
            if warning:
                output.write(f"{warning}\n")
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=output,
                                       env=environment, shell=False,
                                       creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
        register = context.get("register_child_project")
        if callable(register):
            register(run_id, control_path, result_path)
        result = wait_for_result(process, request, context)
        # The supervisor exits after publication even when the separate tracker
        # window is retained. Reap it so its launcher log handle is released.
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass
        message = context.get("report_message")
        if callable(message):
            message(f"Child '{child.project_name}': {result.get('outcome')}; "
                    f"counts={result.get('counts')}; result={result_path}")
        if result.get("outcome") not in projects.SUCCESS_OUTCOMES:
            raise RuntimeError(f"Child project '{child.project_name}' {result.get('outcome')}: "
                               f"{result.get('reason')}. Result: {result_path}")
        if result["outcome"] == "warning":
            report_warning = context.get("report_warning")
            if callable(report_warning):
                report_warning(f"Child '{child.project_name}' completed with warnings: {result.get('counts')}")
        return result
    finally:
        if process and not projects.read_json(result_path).get("finished"):
            projects.write_json(control_path, {"action": "cancel", "run_id": run_id})
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                tracker_process_utils.terminate_process_tree(process, force=True)
        if not projects.read_json(result_path).get("finished"):
            error = sys.exc_info()[1]
            projects.write_json(result_path, {
                "schema_version": projects.SCHEMA_VERSION, "run_id": run_id,
                "parent_run_id": parent_id, "source_project_file": work_item.current_path,
                "finished": True, "outcome": "failed", "reason": str(error or "Child launch interrupted."),
                "counts": {"failed": 1}})
        unregister = context.get("unregister_child_project")
        if callable(unregister):
            unregister(run_id)


def wait_for_result(process, request, context):
    """Monitors child liveness, startup and processing deadlines.

    Args:
        process (subprocess.Popen): Owned child supervisor.
        request (dict): Launch manifest.
        context (dict): Progress callbacks.

    Returns:
        dict: Verified terminal child result.
    """
    run_dir = request["run_dir"]
    settings = request["settings"]
    result_path = os.path.join(run_dir, "result.json")
    started = time.monotonic()
    while True:
        result = projects.read_json(result_path)
        if result.get("finished") and result.get("run_id") == request["run_id"]:
            if result.get("schema_version") != projects.SCHEMA_VERSION:
                raise RuntimeError("Unsupported child project result schema.")
            return result
        status = projects.read_json(os.path.join(run_dir, "status.json"))
        if status.get("run_id") != request["run_id"]:
            status = {}
        elapsed = time.monotonic() - started
        launch_timeout = LAUNCH_TIMEOUT_SECONDS
        if not status and launch_timeout and elapsed > launch_timeout:
            raise RuntimeError("Child project startup timed out.")
        heartbeat_timeout = HEARTBEAT_TIMEOUT_SECONDS
        if status and heartbeat_timeout and time.time() - status.get("heartbeat", 0) > heartbeat_timeout:
            raise RuntimeError("Child project heartbeat timed out.")
        callback = context.get("report_progress")
        if callable(callback) and status:
            callback(int(status.get("progress", 0)), 100, "child project %")
        if process.poll() is not None:
            # One last read covers publication immediately before supervisor exit.
            result = projects.read_json(result_path)
            if result.get("finished") and result.get("run_id") == request["run_id"]:
                if result.get("schema_version") != projects.SCHEMA_VERSION:
                    raise RuntimeError("Unsupported child project result schema.")
                return result
            raise RuntimeError(f"Child supervisor exited ({process.returncode}) without a final result. "
                               f"See {os.path.join(run_dir, 'launcher.log')}")
        time.sleep(0.25)
