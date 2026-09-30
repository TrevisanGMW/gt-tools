"""Coordination cleanup regressions using real filesystem locks and isolated outputs."""

import os
import subprocess
import sys
import tempfile
import time
import types
import unittest
from unittest import mock
from gt.tools.batch_processor import batch_processor_model, batch_processor_worker
from gt.tools.batch_processor.batch_processor_task_base import WorkItem, TaskSkip
from gt.tools.batch_processor.tasks import task_kimodo_base as base
from gt.tools.batch_processor.tasks import task_kimodo_definition as definition
from gt.tools.batch_processor.tracker import tracker_constants, tracker_model, tracker_scheduler


class TestKimodoCoordination(unittest.TestCase):
    """Checks clean outputs, worker barriers, and preservation of unrelated files."""

    def setUp(self):
        """Creates a task, source placeholder, and isolated output folder."""
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = temporary.name
        self.output = os.path.join(self.root, "output")
        self.task = definition.TaskKimodoDefinition(settings={"target_path": self.output})
        self.item = WorkItem(os.path.join(self.root, "source.ma"))
        base.write_record(self.item.current_path, {})
        self.project = batch_processor_model.BatchProcessorModel()
        self.project.get_input_task().settings.update(input_dir=self.root, extensions=[".ma"])
        self.project.add_task(self.task)

    def create_claim(self):
        """Creates a reservation and inactive per-input coordination lock."""
        context = {"defer_kimodo_coordination_cleanup": True}
        with self.task.recovery_lock(self.item, self.output, context=context):
            self.task.reserve_outputs(self.item, [os.path.join(self.output, "result.json")], self.output)

    def test_cleanup_preserves_recovery_and_unrelated_outputs(self):
        """Deletes coordination records without touching retry data or published files."""
        self.create_claim()
        cache = os.path.join(self.task.recovery_directory(self.item, self.output), "capture.json")
        result = os.path.join(self.output, "result.json")
        base.write_record(cache, {"retry": True})
        base.write_record(result, {"published": True})
        base.cleanup_project_coordination(self.project)
        self.assertFalse(os.path.exists(os.path.join(self.output, ".kimodo-coordination")))
        self.assertEqual({"retry": True}, base.read_json(cache))
        self.assertEqual({"published": True}, base.read_json(result))

    def test_unknown_coordination_contents_are_preserved(self):
        """Refuses to sweep unrecognized files from the owned folder."""
        self.create_claim()
        path = os.path.join(self.output, ".kimodo-coordination", "notes.json")
        base.write_record(path, {"keep": True})
        self.assertFalse(base.purge_coordination(self.output))
        self.assertEqual({"keep": True}, base.read_json(path))

    def test_cleanup_rejects_unset_or_relative_destinations(self):
        """Never interprets an unset output folder as the current working directory."""
        for directory in ("", "relative-output"):
            with self.subTest(directory=directory), self.assertRaises(ValueError):
                base.purge_coordination(directory)

    def test_cleanup_rejects_linked_coordination(self):
        """Leaves coordination symlinks and their external contents untouched."""
        target = os.path.join(self.root, "external")
        base.write_record(os.path.join(target, "keep.json"), {"keep": True})
        os.makedirs(self.output)
        link = os.path.join(self.output, ".kimodo-coordination")
        try:
            os.symlink(target, link, target_is_directory=True)
        except OSError:
            self.skipTest("Directory symlinks are unavailable for this Windows account.")
        with self.assertRaises(ValueError):
            base.purge_coordination(self.output)
        self.assertEqual({"keep": True}, base.read_json(os.path.join(target, "keep.json")))

    def test_active_worker_prevents_cleanup(self):
        """Uses another Python process to prove active locks survive a cleanup attempt."""
        ready = os.path.join(self.root, "ready.json")
        script = "\n".join([
            "import sys",
            "from gt.tools.batch_processor.tasks.task_kimodo_definition import TaskKimodoDefinition",
            "from gt.tools.batch_processor.tasks.task_kimodo_base import write_record",
            "from gt.tools.batch_processor.batch_processor_task_base import WorkItem",
            "task = TaskKimodoDefinition()",
            "with task.recovery_lock(WorkItem(sys.argv[1]), sys.argv[2],",
            "                        context={'defer_kimodo_coordination_cleanup': True}):",
            "    write_record(sys.argv[3], {'ready': True})",
            "    sys.stdin.readline()",
        ])
        process = subprocess.Popen([sys.executable, "-c", script, self.item.current_path, self.output, ready],
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            deadline = time.monotonic() + 15
            while not os.path.isfile(ready) and time.monotonic() < deadline and process.poll() is None:
                time.sleep(0.02)
            self.assertTrue(os.path.isfile(ready), "Lock-holding worker did not become ready.")
            self.assertFalse(base.purge_coordination(self.output))
            self.assertTrue(os.path.isdir(os.path.join(self.output, ".kimodo-coordination", "locks")))
            unused_stdout, stderr = process.communicate("release\n", timeout=10)
            self.assertEqual(0, process.returncode, stderr)
            self.assertTrue(base.purge_coordination(self.output))
        finally:
            if process.poll() is None:
                process.kill()
                process.communicate(timeout=10)

    def test_shared_destination_respects_retention(self):
        """A task opting out prevents another task sharing its destination from purging it."""
        self.create_claim()
        self.project.add_task(definition.TaskKimodoDefinition(settings={
            "target_path": self.output, "purge_coordination_on_finish": False}))
        base.cleanup_project_coordination(self.project)
        self.assertTrue(os.path.isdir(os.path.join(self.output, ".kimodo-coordination")))

    def test_single_runner_cleans_after_final_input(self):
        """Runs the actual single-process runner and captures portable definitions with fake Maya calls."""
        self.task.settings.update(source_mode="source_path", source_path=self.item.current_path)
        captured = {"frames": [], "start": 1, "end": 120, "source_fps": 30, "poses": [],
                    "path": None, "path_frames": []}
        with mock.patch.object(definition.batch_processor_maya, "get_maya_cmds"), \
                mock.patch.object(definition, "capture_scene", return_value=captured):
            result = batch_processor_worker.SingleInstanceBatchRunner().run(self.project)
        self.assertEqual(0, result.failed)
        self.assertEqual(["source.json"], os.listdir(self.output))

    def test_standalone_definition_cleans_after_success_and_skip(self):
        """Direct task calls clean both folder types even when every output already exists."""
        captured = {"frames": [], "start": 1, "end": 120, "source_fps": 30, "poses": [],
                    "path": None, "path_frames": []}
        with mock.patch.object(definition.batch_processor_maya, "get_maya_cmds"), \
                mock.patch.object(definition, "capture_scene", return_value=captured):
            self.task.execute(self.item, None, self.output)
            with self.assertRaises(TaskSkip):
                self.task.execute(self.item, None, self.output)
        self.assertEqual(["source.json"], os.listdir(self.output))

    def test_tracker_cleans_when_all_workers_finish(self):
        """Exercises scheduler completion and limits cleanup to this run's task IDs."""
        self.create_claim()
        job = tracker_model.TrackerJob("job-1", 1, self.item.current_path, [
            {"id": self.task.id, "number": 1, "name": "Kimodo Definition"}])
        job.status = tracker_constants.Status.COMPLETED
        job.tasks[0].status = tracker_constants.Status.COMPLETED
        session = tracker_model.TrackerSession("Test", self.root, 1, [job], os.path.join(self.root, "session"))
        scheduler = tracker_scheduler.TrackerScheduler(session, types.SimpleNamespace(), project=self.project)
        scheduler.regular_queue.clear()
        scheduler.tick()
        self.assertTrue(session.finished)
        self.assertFalse(os.path.exists(os.path.join(self.output, ".kimodo-coordination")))


if __name__ == "__main__":
    unittest.main()
