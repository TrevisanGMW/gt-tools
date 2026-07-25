"""
Unit tests for segmented multi-instance (parallel) execution.

Covers the pure-Python pieces that can run without Maya or Qt: the tracker
segment builder and the scheduler's phased barrier logic. Worker subprocess
launching and the Qt tracker view require a Maya/mayapy environment and are not
exercised here.
"""

import logging
import os
import shutil
import sys
import tempfile
import types
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Scripts
test_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_main
from gt.tools.batch_processor.tracker import tracker_model
from gt.tools.batch_processor.tracker import tracker_scheduler


class FakeSegmentProject:
    """Minimal project stand-in that returns preset files per segment marker."""

    def __init__(self, files_by_marker):
        """Initializes the fake project.

        Args:
            files_by_marker (dict): Mapping of input-task marker to file lists.
        """
        self.files_by_marker = files_by_marker

    def discover_segment_input_files(self, segment_tasks):
        """Returns preset files for a segment marker.

        Args:
            segment_tasks (object): Segment input-task marker.

        Returns:
            list: Preset files for the marker.
        """
        return list(self.files_by_marker.get(segment_tasks, []))


class TestSegmentBuilder(unittest.TestCase):
    def _make_segmented_model(self):
        """Builds a two-segment model (input, rename, reset-input, rename).

        Returns:
            BatchProcessorModel: Configured model.
        """
        model = batch_processor_model.BatchProcessorModel()
        first_input = tasks.InputTask()
        first_process = tasks.create_task(task_type=constants.TaskType.RENAME)
        second_input = tasks.InputTask()
        second_input.settings["start_new_input_list"] = True
        second_process = tasks.create_task(task_type=constants.TaskType.RENAME)
        model.tasks = [first_input, first_process, second_input, second_process]
        return model

    def test_build_segments_splits_processing_tasks(self):
        model = self._make_segmented_model()
        args = types.SimpleNamespace(run_from_task_id="", run_to_task_id="", final_task_id=[])

        segments, final_definitions, final_tasks = tracker_main.build_segments(model, args)

        expected = 2
        self.assertEqual(expected, len(segments))
        self.assertEqual([], final_definitions)
        self.assertEqual([], final_tasks)
        self.assertEqual(1, len(segments[0]["task_ids"]))
        self.assertEqual(1, len(segments[1]["task_ids"]))
        self.assertNotEqual(segments[0]["task_ids"], segments[1]["task_ids"])

    def test_single_segment_project_reports_one_segment(self):
        model = batch_processor_model.BatchProcessorModel()
        model.tasks = [tasks.InputTask(), tasks.create_task(task_type=constants.TaskType.RENAME)]
        args = types.SimpleNamespace(run_from_task_id="", run_to_task_id="", final_task_id=[])

        segments, _, _ = tracker_main.build_segments(model, args)

        expected = 1
        self.assertEqual(expected, len(segments))


class TestSchedulerSegmentBarrier(unittest.TestCase):
    def setUp(self):
        self.session_dir = tempfile.mkdtemp(prefix="gt_seg_sched_test_")
        self.addCleanup(lambda: os.path.isdir(self.session_dir) and shutil.rmtree(self.session_dir))

    def _make_scheduler(self):
        """Builds a two-segment scheduler backed by a fake project.

        Returns:
            TrackerScheduler: Segmented scheduler ready to advance.
        """
        segments = [
            {
                "index": 0,
                "input_tasks": "seg0",
                "processing_tasks": [],
                "definitions": [{"id": "t1", "number": 1, "name": "Retarget", "icon": ""}],
                "task_ids": ["t1"],
            },
            {
                "index": 1,
                "input_tasks": "seg1",
                "processing_tasks": [],
                "definitions": [{"id": "t2", "number": 1, "name": "Export", "icon": ""}],
                "task_ids": ["t2"],
            },
        ]
        project = FakeSegmentProject(
            {"seg0": ["/in/a.fbx", "/in/b.fbx"], "seg1": ["/out/a.ma"]}
        )
        session = tracker_model.TrackerSession("T", "C:/p", 1, [], self.session_dir)
        options = types.SimpleNamespace(no_log=True, task_time_logs=False)
        return tracker_scheduler.TrackerScheduler(
            session=session, options=options, project=project, segments=segments
        )

    def _complete_segment_jobs(self, scheduler, segment_index):
        """Simulates every job of a segment finishing successfully.

        Args:
            scheduler (TrackerScheduler): Scheduler under test.
            segment_index (int): Segment whose jobs should complete.
        """
        for job in scheduler._segment_jobs(segment_index):
            if job in scheduler.regular_queue:
                scheduler.regular_queue.remove(job)
            job.status = tracker_constants.Status.COMPLETED

    def test_scheduler_reports_segmented_mode(self):
        scheduler = self._make_scheduler()
        self.assertTrue(scheduler.segmented)
        self.assertEqual(0, scheduler.current_segment_index)

    def test_first_segment_materializes_one_job_per_file(self):
        scheduler = self._make_scheduler()

        changed = scheduler._advance_segments()

        self.assertTrue(changed)
        self.assertEqual(2, len(scheduler.session.jobs))
        self.assertEqual(2, len(scheduler.regular_queue))
        for job in scheduler.session.jobs:
            self.assertEqual(0, job.segment_index)
            self.assertTrue(job.name.startswith("[Seg 1] "))
        self.assertTrue(scheduler._segments_remaining())
        self.assertFalse(scheduler._segment_complete(0))

    def test_barrier_holds_until_segment_complete(self):
        scheduler = self._make_scheduler()
        scheduler._advance_segments()  # materialize segment 0

        # Still running segment 0 -> advancing must not create segment 1 jobs.
        no_change = scheduler._advance_segments()
        self.assertFalse(no_change)
        self.assertEqual(2, len(scheduler.session.jobs))

        self._complete_segment_jobs(scheduler, 0)
        changed = scheduler._advance_segments()
        self.assertTrue(changed)
        self.assertEqual(1, scheduler.current_segment_index)
        self.assertEqual(3, len(scheduler.session.jobs))
        segment_one_jobs = scheduler._segment_jobs(1)
        self.assertEqual(1, len(segment_one_jobs))
        self.assertEqual(1, segment_one_jobs[0].segment_index)

    def test_finished_only_after_all_segments(self):
        scheduler = self._make_scheduler()
        scheduler._advance_segments()
        self._complete_segment_jobs(scheduler, 0)
        scheduler._advance_segments()
        self.assertTrue(scheduler._segments_remaining())
        self._complete_segment_jobs(scheduler, 1)
        self.assertFalse(scheduler._segments_remaining())
        self.assertTrue(scheduler._is_finished())

    def test_non_segmented_scheduler_is_inert(self):
        session = tracker_model.TrackerSession("T", "C:/p", 1, [], self.session_dir)
        options = types.SimpleNamespace(no_log=True, task_time_logs=False)
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        self.assertFalse(scheduler.segmented)
        self.assertFalse(scheduler._segments_remaining())


class TestSchedulerRetries(unittest.TestCase):
    def setUp(self):
        self.session_dir = tempfile.mkdtemp(prefix="gt_retry_sched_test_")
        self.addCleanup(lambda: os.path.isdir(self.session_dir) and shutil.rmtree(self.session_dir))

    def _make_scheduler(self, max_retries):
        """Builds a non-segmented two-job scheduler with a retry budget.

        Args:
            max_retries (int): Configured retry count.

        Returns:
            TrackerScheduler: Scheduler ready for retry advancement.
        """
        definitions = [{"id": "t1", "number": 1, "name": "Rename", "icon": ""}]
        jobs = [
            tracker_model.TrackerJob(
                job_id="job-0001", number=1, source_file="/in/a.ma", task_definitions=definitions
            ),
            tracker_model.TrackerJob(
                job_id="job-0002", number=2, source_file="/in/b.ma", task_definitions=definitions
            ),
        ]
        session = tracker_model.TrackerSession("T", "C:/p", 1, jobs, self.session_dir)
        options = types.SimpleNamespace(no_log=True, task_time_logs=False, max_retries=max_retries)
        return tracker_scheduler.TrackerScheduler(session=session, options=options)

    @staticmethod
    def _drain_as_failed(scheduler, job):
        """Simulates a job draining out of the active scope as failed.

        Args:
            scheduler (TrackerScheduler): Scheduler under test.
            job (TrackerJob): Job to mark failed and dequeue.
        """
        if job in scheduler.regular_queue:
            scheduler.regular_queue.remove(job)
        job.status = tracker_constants.Status.FAILED

    def test_retries_disabled_never_requeues(self):
        scheduler = self._make_scheduler(max_retries=0)
        failed_job = scheduler.session.regular_jobs[0]
        self._drain_as_failed(scheduler, failed_job)
        scheduler.regular_queue = []

        self.assertFalse(scheduler._advance_retries())
        self.assertEqual(tracker_constants.Status.FAILED, failed_job.status)

    def test_failed_job_requeued_until_budget_exhausted(self):
        scheduler = self._make_scheduler(max_retries=2)
        failed_job, passing_job = scheduler.session.regular_jobs
        passing_job.status = tracker_constants.Status.COMPLETED
        self._drain_as_failed(scheduler, failed_job)
        scheduler.regular_queue = [job for job in scheduler.regular_queue if job is not passing_job]

        # First retry.
        self.assertTrue(scheduler._advance_retries())
        self.assertIn(failed_job, scheduler.regular_queue)
        self.assertEqual(tracker_constants.Status.QUEUED, failed_job.status)
        self.assertEqual(1, scheduler.job_retry_counts[failed_job.id])

        # Second retry after failing again.
        self._drain_as_failed(scheduler, failed_job)
        self.assertTrue(scheduler._advance_retries())
        self.assertEqual(2, scheduler.job_retry_counts[failed_job.id])

        # Budget exhausted: stays failed, never retried again.
        self._drain_as_failed(scheduler, failed_job)
        self.assertFalse(scheduler._advance_retries())
        self.assertEqual(tracker_constants.Status.FAILED, failed_job.status)
        self.assertNotIn(passing_job.id, scheduler.job_retry_counts)

    def test_no_retry_while_active_work_remains(self):
        scheduler = self._make_scheduler(max_retries=3)
        failed_job = scheduler.session.regular_jobs[0]
        failed_job.status = tracker_constants.Status.FAILED
        # The second job is still queued, so retries must wait for the scope to drain.
        self.assertFalse(scheduler._advance_retries())
        self.assertEqual({}, scheduler.job_retry_counts)


if __name__ == "__main__":
    unittest.main(verbosity=2)
