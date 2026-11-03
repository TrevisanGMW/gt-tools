"""Programmatic project launching and completion tracking, intended for scripts and AI agents."""

import os
import tempfile
import time

from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_projects
from gt.tools.batch_processor import batch_processor_worker


DEFAULT_POLL_INTERVAL = 0.5
NOTHING_TO_LAUNCH_RESULT = {
    "finished": True,
    "outcome": "succeeded",
    "reason": "No worker jobs were needed; nothing was launched.",
}


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
    return ProjectRun(runner.process, result_dir, runner.run_id)
