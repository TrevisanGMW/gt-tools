"""Tests for programmatic project launching and completion tracking."""

import os
import tempfile
import time
import unittest
from unittest import mock

from gt.tools.batch_processor import batch_processor_launch
from gt.tools.batch_processor import batch_processor_projects as projects


class FakeProcess:
    """Process stand-in with a controllable exit state."""

    def __init__(self, returncode=None):
        """Stores the simulated return code.

        Args:
            returncode (int, optional): None while running.
        """
        self.returncode = returncode

    def poll(self):
        """Gets the simulated return code.

        Returns:
            int: Return code or None while running.
        """
        return self.returncode


class TestProjectRun(unittest.TestCase):
    """Checks result reading, waiting, and cancellation without launching trackers."""

    def setUp(self):
        """Creates an isolated result directory."""
        directory = tempfile.TemporaryDirectory(prefix="gt_launch_")
        self.addCleanup(directory.cleanup)
        self.result_dir = directory.name

    def test_wait_returns_published_result(self):
        run = batch_processor_launch.ProjectRun(FakeProcess(), self.result_dir, "run-1")
        self.assertFalse(run.is_finished())
        projects.write_json(run.result_file, {"finished": True, "outcome": "succeeded"})
        expected_result = "succeeded"
        self.assertEqual(expected_result, run.wait(timeout=2, poll_interval=0.01)["outcome"])
        self.assertTrue(run.is_finished())

    def test_wait_times_out_while_running(self):
        run = batch_processor_launch.ProjectRun(FakeProcess(), self.result_dir, "run-1")
        with self.assertRaises(TimeoutError):
            run.wait(timeout=0.05, poll_interval=0.01)

    def test_wait_raises_when_process_exits_without_result(self):
        run = batch_processor_launch.ProjectRun(FakeProcess(returncode=1), self.result_dir, "run-1")
        with self.assertRaises(RuntimeError):
            run.wait(timeout=2, poll_interval=0.01)

    def test_nothing_launched_reports_success(self):
        run = batch_processor_launch.ProjectRun(None, self.result_dir, "")
        self.assertEqual("succeeded", run.wait()["outcome"])
        self.assertEqual(100, run.get_progress())

    def test_cancel_writes_matching_control_request(self):
        run = batch_processor_launch.ProjectRun(FakeProcess(), self.result_dir, "run-1")
        run.cancel()
        expected_control = {"action": "cancel", "run_id": "run-1"}
        self.assertEqual(expected_control, projects.read_json(run.control_file))

    def test_launch_project_rejects_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            batch_processor_launch.launch_project(os.path.join(self.result_dir, "missing.batch"))


class TestAttachedRun(unittest.TestCase):
    """Checks reconnecting to a run from its result directory."""

    def setUp(self):
        """Creates an isolated result directory."""
        directory = tempfile.TemporaryDirectory(prefix="gt_attach_")
        self.addCleanup(directory.cleanup)
        self.result_dir = directory.name

    def write_launch(self, process_id, launched_at=None, nothing_launched=False):
        """Writes a launch file as ``launch_project`` does.

        Args:
            process_id (int): Simulated tracker process id.
            launched_at (float, optional): Launch time, defaults to now.
            nothing_launched (bool, optional): Simulates a run without worker jobs.
        """
        projects.write_json(os.path.join(self.result_dir, batch_processor_launch.LAUNCH_FILE_NAME), {
            "run_id": "run-7",
            "process_id": process_id,
            "nothing_launched": nothing_launched,
            "launched_at": time.time() if launched_at is None else launched_at,
        })

    def test_attach_rejects_empty_directory(self):
        with self.assertRaises(FileNotFoundError):
            batch_processor_launch.ProjectRun.attach(self.result_dir)

    def test_attach_follows_live_process_until_result(self):
        self.write_launch(os.getpid())
        run = batch_processor_launch.ProjectRun.attach(self.result_dir)
        expected_run_id = "run-7"
        self.assertEqual(expected_run_id, run.run_id)
        self.assertIsNone(run.process.poll())
        with self.assertRaises(TimeoutError):
            run.wait(timeout=0.05, poll_interval=0.01)
        projects.write_json(run.result_file, {"finished": True, "outcome": "warning"})
        self.assertEqual("warning", run.wait(timeout=2, poll_interval=0.01)["outcome"])

    def test_attach_reports_dead_process(self):
        self.write_launch(0)
        run = batch_processor_launch.ProjectRun.attach(self.result_dir)
        with self.assertRaises(RuntimeError):
            run.wait(timeout=2, poll_interval=0.01)

    def test_stale_heartbeat_counts_as_exited(self):
        self.write_launch(os.getpid())
        projects.write_json(os.path.join(self.result_dir, "status.json"), {"heartbeat": time.time() - 600})
        run = batch_processor_launch.ProjectRun.attach(self.result_dir, stale_after=60)
        expected_code = batch_processor_launch.UNKNOWN_EXIT_CODE
        self.assertEqual(expected_code, run.process.poll())

    def test_stale_check_can_be_disabled(self):
        self.write_launch(os.getpid(), launched_at=time.time() - 600)
        run = batch_processor_launch.ProjectRun.attach(self.result_dir, stale_after=None)
        self.assertIsNone(run.process.poll())

    def test_attach_without_launch_uses_status_pid(self):
        projects.write_json(os.path.join(self.result_dir, "status.json"), {
            "run_id": "run-9", "tracker_pid": os.getpid(), "heartbeat": time.time(),
        })
        run = batch_processor_launch.ProjectRun.attach(self.result_dir)
        expected_process_id = os.getpid()
        self.assertEqual(expected_process_id, run.process.pid)
        self.assertEqual("run-9", run.run_id)

    def test_attach_nothing_launched_reports_success(self):
        self.write_launch(None, nothing_launched=True)
        run = batch_processor_launch.ProjectRun.attach(self.result_dir)
        self.assertEqual("succeeded", run.wait()["outcome"])

    def test_write_launch_file_records_process(self):
        path = batch_processor_launch.write_launch_file(
            self.result_dir, mock.Mock(pid=4321), "run-3", os.path.join(self.result_dir, "a.batch"))
        expected_process_id = 4321
        self.assertEqual(expected_process_id, projects.read_json(path)["process_id"])
        self.assertFalse(projects.read_json(path)["nothing_launched"])


class TestIsProcessAlive(unittest.TestCase):
    """Checks the dependency-free process liveness helper."""

    def test_current_process_is_alive(self):
        self.assertTrue(batch_processor_launch.is_process_alive(os.getpid()))

    def test_invalid_ids_are_not_alive(self):
        for process_id in (None, 0, -5, "abc"):
            self.assertFalse(batch_processor_launch.is_process_alive(process_id))
