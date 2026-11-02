"""Tests for programmatic project launching and completion tracking."""

import os
import tempfile
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
