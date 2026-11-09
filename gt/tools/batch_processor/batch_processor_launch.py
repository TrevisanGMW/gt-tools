"""Programmatic project launching and completion tracking, intended for scripts and AI agents."""

import os
import sys
import tempfile
import time

from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_projects
from gt.tools.batch_processor import batch_processor_worker


DEFAULT_POLL_INTERVAL = 0.5
DEFAULT_STALE_AFTER = 120.0
LAUNCH_FILE_NAME = "launch.json"
UNKNOWN_EXIT_CODE = -1
WINDOWS_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
WINDOWS_STILL_ACTIVE = 259
WINDOWS_ERROR_ACCESS_DENIED = 5
NOTHING_TO_LAUNCH_RESULT = {
    "finished": True,
    "outcome": "succeeded",
    "reason": "No worker jobs were needed; nothing was launched.",
}


def is_process_alive(process_id):
    """Checks whether a process with the given id is still running.

    Args:
        process_id (int): Operating system process id.

    Returns:
        bool: True while the process exists. False for an empty or invalid id.
    """
    try:
        process_id = int(process_id)
    except (TypeError, ValueError):
        return False
    if process_id <= 0:
        return False
    if sys.platform == "win32":
        return _is_windows_process_alive(process_id)
    try:
        os.kill(process_id, 0)
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _is_windows_process_alive(process_id):
    """Checks a Windows process through its exit code, without extra dependencies.

    Args:
        process_id (int): Windows process id.

    Returns:
        bool: True while the process exists and has not exited.
    """
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.OpenProcess.restype = wintypes.HANDLE
    kernel32.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel32.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
    kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
    handle = kernel32.OpenProcess(WINDOWS_PROCESS_QUERY_LIMITED_INFORMATION, False, process_id)
    if not handle:
        return ctypes.get_last_error() == WINDOWS_ERROR_ACCESS_DENIED
    try:
        exit_code = wintypes.DWORD()
        if not kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code)):
            return True
        return exit_code.value == WINDOWS_STILL_ACTIVE
    finally:
        kernel32.CloseHandle(handle)


class AttachedProcess:
    """Process stand-in for a tracker started by another process, followed through its files.

    It mimics the parts of ``subprocess.Popen`` that ``ProjectRun`` uses (``pid``, ``poll``
    and ``returncode``). The tracker counts as exited when its process is gone or when it
    stops publishing heartbeats for longer than ``stale_after`` seconds.
    """

    def __init__(self, process_id, status_file, started_at=None, stale_after=DEFAULT_STALE_AFTER):
        """Stores what is needed to follow the tracker.

        Args:
            process_id (int): Tracker process id, or None when unknown.
            status_file (str): Tracker ``status.json`` path.
            started_at (float, optional): Launch time (epoch seconds), used before the first heartbeat.
            stale_after (float, optional): Seconds without a heartbeat before the tracker counts
                as exited. None disables the heartbeat check.
        """
        self.pid = process_id
        self.status_file = status_file
        self.started_at = started_at
        self.stale_after = stale_after
        self.returncode = None

    def poll(self):
        """Gets the exit state of the followed tracker.

        Returns:
            int: ``UNKNOWN_EXIT_CODE`` once the tracker is gone (its real exit code is not
                available to other processes), or None while it is running.
        """
        if self.returncode is None and (not is_process_alive(self.pid) or self.is_stale()):
            self.returncode = UNKNOWN_EXIT_CODE
        return self.returncode

    def is_stale(self):
        """Checks whether the tracker stopped publishing heartbeats before finishing.

        Returns:
            bool: True when the last heartbeat (or the launch time) is older than ``stale_after``.
        """
        if self.stale_after is None:
            return False
        status = batch_processor_projects.read_json(self.status_file)
        if status.get("finished"):
            return False
        last_seen = status.get("heartbeat") or self.started_at
        if not last_seen:
            return False
        return time.time() - float(last_seen) > float(self.stale_after)


def write_launch_file(result_dir, process, run_id, project_path):
    """Records how a run was launched so other processes can reconnect to it later.

    Args:
        result_dir (str): Run result directory.
        process (subprocess.Popen): Tracker process, or None when nothing was launched.
        run_id (str): Unique run id.
        project_path (str): Launched project file.

    Returns:
        str: Path of the written launch file.
    """
    launch_path = os.path.join(result_dir, LAUNCH_FILE_NAME)
    batch_processor_projects.write_json(launch_path, {
        "schema_version": batch_processor_projects.SCHEMA_VERSION,
        "run_id": run_id or "",
        "process_id": getattr(process, "pid", None),
        "nothing_launched": process is None,
        "launched_at": time.time(),
        "project_path": os.path.abspath(project_path),
    })
    return launch_path


class ProjectRun:
    """Handle for a project launched in its own tracker process."""

    def __init__(self, process, result_dir, run_id):
        """Stores the launched process and its result location.

        Args:
            process (subprocess.Popen): Tracker process, or None when nothing was launched.
            result_dir (str): Directory holding ``result.json``, ``status.json`` and ``control.json``.
            run_id (str): Unique run id used to match cancel requests.
        """
        self.process = process
        self.result_dir = result_dir
        self.run_id = run_id
        self.result_file = os.path.join(result_dir, "result.json")
        self.status_file = os.path.join(result_dir, "status.json")
        self.control_file = os.path.join(result_dir, "control.json")

    @classmethod
    def attach(cls, result_dir, stale_after=DEFAULT_STALE_AFTER):
        """Reconnects to a run from its result directory, for example from another process.

        Use this when the process that launched the run has exited. Waiting, progress,
        cancellation and run settings work as for a handle returned by ``launch_project``.

        Args:
            result_dir (str): Result directory of the run.
            stale_after (float, optional): Seconds without a tracker heartbeat before the run
                counts as dead. None disables the heartbeat check.

        Returns:
            ProjectRun: Handle following the run.

        Raises:
            FileNotFoundError: When the directory holds no launch, status, or result file.
        """
        launch = batch_processor_projects.read_json(os.path.join(result_dir, LAUNCH_FILE_NAME))
        status = batch_processor_projects.read_json(os.path.join(result_dir, "status.json"))
        result = batch_processor_projects.read_json(os.path.join(result_dir, "result.json"))
        if not launch and not status and not result:
            raise FileNotFoundError(f"No Batch Processor run was published in: {result_dir}")
        run_id = launch.get("run_id") or status.get("run_id") or result.get("run_id") or ""
        if launch.get("nothing_launched"):
            return cls(None, result_dir, run_id)
        process_id = launch.get("process_id") or status.get("tracker_pid")
        status_file = os.path.join(result_dir, "status.json")
        process = AttachedProcess(process_id, status_file, launch.get("launched_at"), stale_after)
        return cls(process, result_dir, run_id)

    def get_result(self):
        """Reads the published result without waiting.

        Returns:
            dict: Result with ``finished``, ``outcome`` (succeeded, warning, failed, ...),
                ``counts`` and per-job details, or an empty dict while still running.
        """
        if self.process is None:
            return dict(NOTHING_TO_LAUNCH_RESULT)
        result = batch_processor_projects.read_json(self.result_file)
        return result if result.get("finished") else {}

    def is_finished(self):
        """Checks whether the project has published its final result.

        Returns:
            bool: True once finished.
        """
        return bool(self.get_result())

    def get_progress(self):
        """Reads the latest published progress.

        Returns:
            int: Overall progress from 0 to 100 (0 before the first publication).
        """
        if self.process is None:
            return 100
        return int(batch_processor_projects.read_json(self.status_file).get("progress") or 0)

    def wait(self, timeout=None, poll_interval=DEFAULT_POLL_INTERVAL):
        """Blocks until the project finishes and returns its result.

        Reading a small JSON file is the only work done while waiting; the tracker
        and workers are not affected.

        Args:
            timeout (float, optional): Maximum seconds to wait. None waits indefinitely.
            poll_interval (float, optional): Seconds between checks.

        Returns:
            dict: Final result.

        Raises:
            TimeoutError: When the timeout elapses first (the run keeps going).
            RuntimeError: When the tracker process exits without publishing a result.
        """
        started = time.monotonic()
        while True:
            result = self.get_result()
            if result:
                return result
            if self.process.poll() is not None:
                result = self.get_result()
                if result:
                    return result
                raise RuntimeError(f"Tracker exited ({self.process.returncode}) without publishing a result.")
            if timeout is not None and time.monotonic() - started >= timeout:
                raise TimeoutError(f"Project did not finish within {timeout} seconds.")
            time.sleep(poll_interval)

    def cancel(self):
        """Asks the tracker to abort the run; running workers are stopped and the result reports it."""
        if self.process is not None:
            batch_processor_projects.write_json(self.control_file, {"action": "cancel", "run_id": self.run_id})

    def set_run_settings(
        self,
        worker_count=None,
        max_retries=None,
        timeout_minutes=None,
        preferred_maya_version=None,
        keep_manual_changes=None,
    ):
        """Changes run settings of the running project, like editing them in the tracker.

        Only the given values change. Lowering ``worker_count`` never stops running
        jobs; new jobs wait until enough workers finish. A new timeout applies to
        jobs launched afterwards. A Maya version change affects new workers only.

        Args:
            worker_count (int, optional): Maximum concurrent workers.
            max_retries (int, optional): Retry attempts per failed job.
            timeout_minutes (int, optional): Per-job timeout in minutes, 0 disables it.
            preferred_maya_version (str, optional): Maya version for new workers, "" for the launch mayapy.
            keep_manual_changes (bool, optional): When True, later Settings Override tasks
                do not overwrite values changed here or in the tracker.

        Returns:
            int: Request sequence number, or 0 when nothing was launched or nothing was given.
        """
        if self.process is None:
            return 0
        requested = {
            "worker_count": worker_count,
            "max_retries": max_retries,
            "timeout_minutes": timeout_minutes,
            "preferred_maya_version": preferred_maya_version,
        }
        settings = {key: value for key, value in requested.items() if value is not None}
        if not settings and keep_manual_changes is None:
            return 0
        request_path = batch_processor_projects.get_run_settings_request_path(self.control_file)
        previous = batch_processor_projects.read_json(request_path)
        sequence = int(previous.get("sequence") or 0) + 1
        batch_processor_projects.write_json(request_path, {
            "run_id": self.run_id,
            "sequence": sequence,
            "settings": settings,
            "keep_manual_changes": keep_manual_changes,
        })
        return sequence

    def get_run_settings(self):
        """Reads the run settings the tracker last published.

        Returns:
            dict: Current run settings, or an empty dict before the first publication.
        """
        if self.process is None:
            return {}
        return dict(batch_processor_projects.read_json(self.status_file).get("run_settings") or {})

    def close(self):
        """Closes the tracker (and any workers) if it is still running, for example after a finished run."""
        if self.process is not None and self.process.poll() is None:
            from gt.tools.batch_processor.tracker import tracker_process_utils

            tracker_process_utils.terminate_process_tree(self.process, force=True)


def launch_project(
    project_path,
    start_minimized=True,
    run_from_task_id=None,
    run_to_task_id=None,
    close_when_finished=True,
    result_dir=None,
):
    """Launches a saved Batch Processor project in its standalone tracker.

    The tracker runs in its own process, so this returns right after launching.
    Use the returned ``ProjectRun`` to wait for or inspect the result. With
    ``start_minimized`` (the default) the tracker opens as a tray icon (or a
    minimized taskbar window when no tray exists) regardless of the user's
    tracker preferences, which keeps automated test runs non-invasive. The
    project always runs through the multi-instance tracker so a tracker exists.
    It does not create the editor's run log or purge old logs.

    Args:
        project_path (str): Path to the saved ``.batch`` project file.
        start_minimized (bool, optional): Launch the tracker minimized.
        run_from_task_id (str, optional): Task id to start from.
        run_to_task_id (str, optional): Task id to stop after.
        close_when_finished (bool, optional): Close the tracker window and process as soon
            as the run ends (default). Pass False to leave it open for inspection; the
            tracker process then keeps running until closed, so do not wait on its exit.
        result_dir (str, optional): Where to publish result files. Defaults to a new temp folder.

    Returns:
        ProjectRun: Handle with ``wait()``, ``get_result()``, ``get_progress()``, ``cancel()``
            and ``close()``.

    Raises:
        FileNotFoundError: When the project file does not exist.
    """
    if not os.path.isfile(project_path):
        raise FileNotFoundError(f"Batch Processor project not found: {project_path}")
    project = batch_processor_model.BatchProcessorModel.from_file(project_path)
    result_dir = result_dir or tempfile.mkdtemp(prefix="gt_batch_run_")
    runner = batch_processor_worker.MultiInstanceBatchRunner(
        start_minimized=start_minimized,
        result_dir=result_dir,
        window_policy="Close When Finished" if close_when_finished else None,
    )
    runner.run(project, run_from_task_id=run_from_task_id, run_to_task_id=run_to_task_id)
    write_launch_file(result_dir, runner.process, runner.run_id, project_path)
    return ProjectRun(runner.process, result_dir, runner.run_id)
