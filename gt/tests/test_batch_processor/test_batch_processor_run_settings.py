"""
Unit tests for run settings that change during a multi-instance run.

Covers the pure run settings helpers, the "Settings Override" task, the
model plan, the scheduler's live updates, and the external request file. Worker
subprocesses are never started; process launches are replaced by fakes.
"""

import logging
import os
import shutil
import sys
import tempfile
import types
import unittest
from unittest import mock

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
from gt.tools.batch_processor import batch_processor_launch
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_projects
from gt.tools.batch_processor import batch_processor_run_settings as run_settings
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_main
from gt.tools.batch_processor.tracker import tracker_model
from gt.tools.batch_processor.tracker import tracker_scheduler


def create_settings_task(**overrides):
    """Creates a Settings Override task with the given overrides enabled.

    Args:
        **overrides: Run setting values keyed by run setting key.

    Returns:
        TaskSettingsOverride: Configured task.
    """
    task = tasks.create_task(task_type=constants.TaskType.SETTINGS_OVERRIDE)
    for setting_key, value in overrides.items():
        task.settings[run_settings.get_override_flag_key(setting_key)] = True
        task.settings[setting_key] = value
    return task


def create_segmented_model():
    """Builds a two-segment project with Settings Override tasks in several positions.

    Layout: Input, Settings(workers=2), Rename, Settings(retries=3, mid-segment),
    Input(new segment), Settings(workers=8), Rename, Settings(timeout=5, trailing).

    Returns:
        tuple: (BatchProcessorModel, dict of named tasks).
    """
    model = batch_processor_model.BatchProcessorModel()
    named = {
        "input_1": tasks.TaskInput(),
        "settings_1": create_settings_task(worker_count=2),
        "rename_1": tasks.create_task(task_type=constants.TaskType.RENAME),
        "settings_mid": create_settings_task(max_retries=3),
        "input_2": tasks.TaskInput(),
        "settings_2": create_settings_task(worker_count=8),
        "rename_2": tasks.create_task(task_type=constants.TaskType.RENAME),
        "settings_trailing": create_settings_task(timeout_minutes=5),
    }
    named["input_2"].settings["start_new_input_list"] = True
    model.tasks = list(named.values())
    return model, named


class FakeProcess:
    """Process stand-in that never finishes."""

    pid = 1234

    def poll(self):
        """Reports the process as still running.

        Returns:
            None: Always running.
        """
        return None


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


class TestRunSettingsHelpers(unittest.TestCase):
    def test_overrides_only_include_enabled_flags(self):
        settings = {
            "override_worker_count": True,
            "worker_count": "6",
            "override_max_retries": False,
            "max_retries": 4,
        }

        result = run_settings.build_overrides_from_task_settings(settings)

        expected = {"worker_count": 6}
        self.assertEqual(expected, result)

    def test_values_are_clamped(self):
        self.assertEqual(1, run_settings.normalize_setting_value("worker_count", 0))
        self.assertEqual(0, run_settings.normalize_setting_value("max_retries", -2))
        self.assertEqual(0, run_settings.normalize_setting_value("timeout_minutes", "bad"))
        self.assertEqual("2025", run_settings.normalize_setting_value("preferred_maya_version", " 2025 "))

    def test_state_reports_changes(self):
        state = run_settings.RunSettingsState(worker_count=2)

        changes, protected = state.apply({"worker_count": 6, "max_retries": 0})

        expected = [("worker_count", 2, 6)]
        self.assertEqual(expected, changes)
        self.assertEqual([], protected)
        self.assertEqual(6, state.worker_count)

    def test_manual_change_is_overwritten_by_tasks_by_default(self):
        state = run_settings.RunSettingsState(worker_count=2)
        state.apply({"worker_count": 10}, manual=True)

        changes, _protected = state.apply({"worker_count": 4})

        self.assertEqual([("worker_count", 10, 4)], changes)
        self.assertEqual(4, state.worker_count)

    def test_manual_change_is_kept_when_requested(self):
        state = run_settings.RunSettingsState(worker_count=2, keep_manual_changes=True)
        state.apply({"worker_count": 10}, manual=True)

        changes, protected = state.apply({"worker_count": 4, "max_retries": 2})

        self.assertEqual([("max_retries", 0, 2)], changes)
        self.assertEqual(["worker_count"], protected)
        self.assertEqual(10, state.worker_count)

    def test_describe_changes(self):
        result = run_settings.describe_changes([("worker_count", 2, 6), ("max_retries", 1, 0)])

        expected = "Max workers 2 -> 6, Retries 1 -> 0 (off)"
        self.assertEqual(expected, result)

    def test_schedule_assigns_overrides_to_barriers(self):
        model, _named = create_segmented_model()

        schedule = run_settings.build_run_settings_schedule(model.get_task_segments())

        expected_segments = [{"worker_count": 2}, {"max_retries": 3, "worker_count": 8}]
        self.assertEqual(expected_segments, schedule["segments"])
        self.assertEqual({"timeout_minutes": 5}, schedule["final"])

    def test_schedule_carries_overrides_past_segments_without_processing(self):
        settings_task = create_settings_task(worker_count=3)
        empty_input = tasks.TaskInput()
        next_input = tasks.TaskInput()
        next_input.settings["start_new_input_list"] = True
        rename = tasks.create_task(task_type=constants.TaskType.RENAME)
        segments = [[empty_input, settings_task], [next_input, rename]]

        schedule = run_settings.build_run_settings_schedule(segments)

        self.assertEqual([{"worker_count": 3}], schedule["segments"])

    def test_disabled_settings_task_is_ignored(self):
        settings_task = create_settings_task(worker_count=3)
        settings_task.enabled = False

        self.assertEqual({}, run_settings.collect_overrides([settings_task]))

    def test_mid_segment_tasks_are_found(self):
        model, named = create_segmented_model()

        result = run_settings.find_mid_segment_tasks(model.get_task_segments())

        expected = [named["settings_mid"], named["settings_trailing"]]
        self.assertEqual(expected, result)


class TestUpdateRunSettingsTask(unittest.TestCase):
    def test_task_is_registered_and_not_processing(self):
        task = tasks.create_task(task_type=constants.TaskType.SETTINGS_OVERRIDE)

        self.assertTrue(task.is_settings_override_task)
        self.assertFalse(tasks.is_processing_task(task))
        self.assertFalse(task.includes_task_index())
        self.assertEqual({}, task.get_overrides())

    def test_task_round_trips_through_serialization(self):
        task = create_settings_task(worker_count=5, preferred_maya_version="2025")

        restored = tasks.create_task_from_dict(task.to_dict())

        expected = {"worker_count": 5, "preferred_maya_version": "2025"}
        self.assertEqual(expected, restored.get_overrides())

    def test_legacy_type_key_loads_as_settings_override(self):
        data = create_settings_task(worker_count=3).to_dict()
        data["task_type"] = "update_run_settings"

        restored = tasks.create_task_from_dict(data)

        self.assertEqual(constants.TaskType.SETTINGS_OVERRIDE, restored.task_type)
        self.assertEqual({"worker_count": 3}, restored.get_overrides())

    def test_validation_warns_without_overrides(self):
        model = batch_processor_model.BatchProcessorModel()
        task = tasks.create_task(task_type=constants.TaskType.SETTINGS_OVERRIDE)
        model.tasks = [tasks.TaskInput(), task]

        result = task.validate(model)

        self.assertEqual([], result.errors)
        self.assertEqual(1, len(result.warnings))

    def test_validation_warns_for_mid_segment_placement(self):
        model, named = create_segmented_model()
        model.run_settings["multi_instance"] = True

        mid_result = named["settings_mid"].validate(model)
        leading_result = named["settings_2"].validate(model)

        self.assertTrue(any("mid-segment" in warning for warning in mid_result.warnings))
        self.assertEqual([], leading_result.warnings)

    def test_execute_passes_items_through(self):
        task = create_settings_task(worker_count=2)
        items = [tasks.WorkItem(source_path="C:/in/a.ma")]

        result = task.execute(None, None, "", context={"work_items": items})

        self.assertEqual(items, result)


class TestRunSettingsPlan(unittest.TestCase):
    def test_full_run_plan(self):
        model, _named = create_segmented_model()
        model.run_settings["worker_count"] = 30

        plan = model.build_run_settings_plan(model.get_enabled_tasks())

        self.assertEqual(2, plan["initial"]["worker_count"])
        self.assertEqual(0, plan["initial"]["max_retries"])
        self.assertEqual(2, len(plan["segments"]))
        self.assertEqual({"timeout_minutes": 5}, plan["final"])

    def test_run_from_task_includes_earlier_settings_tasks(self):
        model, named = create_segmented_model()
        model.run_settings["worker_count"] = 30
        enabled = model.get_enabled_tasks()
        selected = enabled[enabled.index(named["rename_2"]):]

        plan = model.build_run_settings_plan(selected)

        self.assertEqual(8, plan["initial"]["worker_count"])
        self.assertEqual(3, plan["initial"]["max_retries"])

    def test_tracker_definitions_exclude_settings_tasks(self):
        model, named = create_segmented_model()
        args = types.SimpleNamespace(run_from_task_id="", run_to_task_id="", final_task_id=[])

        segments, _final_definitions, _final_tasks = tracker_main.build_segments(model, args)
        plan = tracker_main.build_run_settings_plan(model, args)

        self.assertEqual([[named["rename_1"].id], [named["rename_2"].id]], [s["task_ids"] for s in segments])
        self.assertEqual(len(segments), len(plan["segments"]))


class TestSchedulerRunSettings(unittest.TestCase):
    def setUp(self):
        self.session_dir = tempfile.mkdtemp(prefix="gt_run_settings_test_")
        self.addCleanup(lambda: os.path.isdir(self.session_dir) and shutil.rmtree(self.session_dir))

    def create_scheduler(self, job_count=4, worker_count=1, plan=None, segments=None, project=None, **options):
        """Creates a scheduler with regular jobs and fake process launches.

        Args:
            job_count (int, optional): Number of regular jobs.
            worker_count (int, optional): Initial worker limit.
            plan (dict, optional): Run settings plan.
            segments (list, optional): Segment descriptors.
            project (object, optional): Segment file provider.
            **options: Extra tracker options.

        Returns:
            TrackerScheduler: Scheduler under test.
        """
        jobs = [] if segments else [
            tracker_model.TrackerJob(f"job-{index}", index, f"C:/in/{index}.ma",
                                     [{"id": "t1", "number": 1, "name": "Task"}])
            for index in range(1, job_count + 1)
        ]
        session = tracker_model.TrackerSession("Test", "C:/project", worker_count, jobs, self.session_dir)
        option_values = dict(no_log=True, task_time_logs=False, mayapy="C:/maya/mayapy.exe",
                             project_file="C:/project/snapshot.batch", run_from_task_id="",
                             run_to_task_id="", final_task_id=[])
        option_values.update(options)
        return tracker_scheduler.TrackerScheduler(
            session=session,
            options=types.SimpleNamespace(**option_values),
            segments=segments,
            project=project,
            run_settings_plan=plan,
        )

    def test_raising_worker_limit_launches_more_jobs(self):
        scheduler = self.create_scheduler(job_count=4, worker_count=1)
        with mock.patch.object(tracker_scheduler.subprocess, "Popen", return_value=FakeProcess()):
            scheduler._launch_available_jobs()
            self.assertEqual(1, len(scheduler.running))

            changes = scheduler.update_run_settings({"worker_count": 3}, manual=True)
            scheduler._launch_available_jobs()

        self.assertEqual([("worker_count", 1, 3)], changes)
        self.assertEqual(3, scheduler.session.worker_count)
        self.assertEqual(3, len(scheduler.running))

    def test_lowering_worker_limit_keeps_running_jobs(self):
        scheduler = self.create_scheduler(job_count=4, worker_count=3)
        with mock.patch.object(tracker_scheduler.subprocess, "Popen", return_value=FakeProcess()):
            scheduler._launch_available_jobs()
            scheduler.update_run_settings({"worker_count": 1}, manual=True)
            scheduler._launch_available_jobs()

        self.assertEqual(3, len(scheduler.running))
        self.assertEqual(1, len(scheduler.regular_queue))

    def test_timeout_is_stored_per_job_at_launch(self):
        scheduler = self.create_scheduler(job_count=2, worker_count=1, timeout_minutes=2)
        with mock.patch.object(tracker_scheduler.subprocess, "Popen", return_value=FakeProcess()):
            scheduler._launch_available_jobs()
            scheduler.update_run_settings({"timeout_minutes": 9}, manual=True)
            scheduler.update_run_settings({"worker_count": 2}, manual=True)
            scheduler._launch_available_jobs()

        timeouts = [data["timeout_seconds"] for data in scheduler.running.values()]
        self.assertEqual([120, 540], timeouts)

    def test_maya_version_change_updates_worker_command(self):
        scheduler = self.create_scheduler(job_count=1)
        with mock.patch("gt.tools.batch_processor.batch_processor_worker.find_mayapy_for_version",
                        return_value="C:/maya2024/mayapy.exe"):
            scheduler.update_run_settings({"preferred_maya_version": "2024"})
        with mock.patch.object(tracker_scheduler.subprocess, "Popen", return_value=FakeProcess()) as popen:
            scheduler._launch_available_jobs()

        command = popen.call_args[0][0]
        self.assertEqual("C:/maya2024/mayapy.exe", command[0])

    def test_missing_maya_version_keeps_current_mayapy(self):
        scheduler = self.create_scheduler(job_count=1)
        with mock.patch("gt.tools.batch_processor.batch_processor_worker.find_mayapy_for_version",
                        return_value=""):
            scheduler.update_run_settings({"preferred_maya_version": "2019"})

        self.assertEqual("C:/maya/mayapy.exe", scheduler.run_settings.mayapy_path)

    def test_non_segmented_plan_applies_at_start(self):
        plan = {"segments": [{"worker_count": 5}], "final": {}}

        scheduler = self.create_scheduler(job_count=1, worker_count=1, plan=plan)

        self.assertEqual(5, scheduler.session.worker_count)

    def test_segment_overrides_apply_when_segment_starts(self):
        segments = [
            {"index": 0, "input_tasks": "seg0", "processing_tasks": [],
             "definitions": [{"id": "t1", "number": 1, "name": "A", "icon": ""}], "task_ids": ["t1"]},
            {"index": 1, "input_tasks": "seg1", "processing_tasks": [],
             "definitions": [{"id": "t2", "number": 1, "name": "B", "icon": ""}], "task_ids": ["t2"]},
        ]
        project = FakeSegmentProject({"seg0": ["C:/in/a.fbx"], "seg1": ["C:/out/a.ma"]})
        plan = {"segments": [{"worker_count": 2}, {"worker_count": 6}], "final": {}}
        scheduler = self.create_scheduler(plan=plan, segments=segments, project=project)

        scheduler._advance_segments()
        self.assertEqual(2, scheduler.session.worker_count)
        for job in scheduler._segment_jobs(0):
            scheduler.regular_queue.remove(job)
            job.status = tracker_constants.Status.COMPLETED
        scheduler._advance_segments()

        self.assertEqual(6, scheduler.session.worker_count)

    def test_final_overrides_apply_before_finalization(self):
        final_job = tracker_model.TrackerJob("finalization", 2, "", [{"id": "zip", "number": 1, "name": "Zip"}],
                                             is_finalization=True)
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [final_job], self.session_dir)
        options = types.SimpleNamespace(no_log=True, task_time_logs=False, mayapy="C:/maya/mayapy.exe",
                                        project_file="C:/project/snapshot.batch")
        plan = {"segments": [], "final": {"timeout_minutes": 7}}
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options, run_settings_plan=plan)

        with mock.patch.object(tracker_scheduler.subprocess, "Popen", return_value=FakeProcess()):
            scheduler._advance_finalization()

        self.assertEqual(7, scheduler.run_settings.timeout_minutes)

    def test_state_file_includes_run_settings(self):
        scheduler = self.create_scheduler(job_count=1, worker_count=2)

        state = batch_processor_projects.read_json(os.path.join(self.session_dir, "session.json"))

        self.assertEqual(2, state["run_settings"]["worker_count"])


class TestExternalRunSettingsRequests(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="gt_run_settings_request_")
        self.addCleanup(lambda: os.path.isdir(self.root) and shutil.rmtree(self.root))
        self.control_file = os.path.join(self.root, "control.json")

    def test_project_run_writes_increasing_sequence(self):
        run = batch_processor_launch.ProjectRun(FakeProcess(), self.root, "run-1")

        first = run.set_run_settings(worker_count=4)
        second = run.set_run_settings(max_retries=2, keep_manual_changes=True)

        request_path = batch_processor_projects.get_run_settings_request_path(self.control_file)
        request = batch_processor_projects.read_json(request_path)
        self.assertEqual(1, first)
        self.assertEqual(2, second)
        self.assertEqual({"max_retries": 2}, request["settings"])
        self.assertTrue(request["keep_manual_changes"])
        self.assertEqual(0, run.set_run_settings())

    def test_reporter_applies_each_request_once(self):
        session_dir = os.path.join(self.root, "session")
        job = tracker_model.TrackerJob("job-1", 1, "C:/in/a.ma", [{"id": "t1", "number": 1, "name": "Task"}])
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [job], session_dir)
        options = types.SimpleNamespace(
            no_log=True, task_time_logs=False, mayapy="C:/maya/mayapy.exe",
            result_file=os.path.join(self.root, "result.json"),
            status_file=os.path.join(self.root, "status.json"),
            control_file=self.control_file, run_id="run-1",
        )
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        run = batch_processor_launch.ProjectRun(FakeProcess(), self.root, "run-1")
        run.set_run_settings(worker_count=6)

        scheduler.project_reporter.tick()
        scheduler.update_run_settings({"worker_count": 2})
        scheduler.project_reporter.tick()

        self.assertEqual(2, scheduler.session.worker_count)
        self.assertIn("worker_count", scheduler.run_settings.manual_keys)
        self.assertEqual(6, run.get_run_settings()["worker_count"])

    def test_reporter_ignores_other_runs(self):
        session_dir = os.path.join(self.root, "session")
        session = tracker_model.TrackerSession("Test", "C:/project", 1, [], session_dir)
        options = types.SimpleNamespace(
            no_log=True, task_time_logs=False, result_file=os.path.join(self.root, "result.json"),
            control_file=self.control_file, run_id="run-1",
        )
        scheduler = tracker_scheduler.TrackerScheduler(session=session, options=options)
        batch_processor_launch.ProjectRun(FakeProcess(), self.root, "other").set_run_settings(worker_count=6)

        scheduler.project_reporter.tick()

        self.assertEqual(1, scheduler.session.worker_count)


if __name__ == "__main__":
    unittest.main()
