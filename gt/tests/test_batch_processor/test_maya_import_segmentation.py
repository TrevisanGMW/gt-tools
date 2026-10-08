"""Regression tests for Import/Open Maya segmentation and generated source folders."""

import os
import sys
import tempfile
import unittest
from unittest import mock

from gt.tools.batch_processor import batch_processor_maya as maya_runtime
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_worker as worker
from gt.tools.batch_processor.tracker import tracker_worker


class TestMayaImportSegmentation(unittest.TestCase):
    """Checks import phase scheduling, validation, and persisted settings."""

    def setUp(self):
        """Creates a disposable project with two source files."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.project.project_file_path = os.path.join(self.directory.name, "project.batch")
        self.project.run_settings["create_log"] = False
        self.project.run_settings["create_task_time_log"] = False
        self.input_directory = os.path.join(self.directory.name, "source")
        os.makedirs(self.input_directory)
        self.project.tasks[0].settings["source_path"] = self.input_directory
        self.generated_directory = os.path.join(self.directory.name, "generated")
        for filename in ("first.ma", "second.ma"):
            self.write_scene(os.path.join(self.input_directory, filename))
        self.tracker_command = []

    @staticmethod
    def write_scene(output_path, file_type=None):
        """Writes a disposable scene fixture instead of calling Maya.

        Args:
            output_path (str): Fixture path to write.
            file_type (str, optional): File type accepted for the save-scene mock.
        """
        with open(output_path, "w", encoding="utf-8") as scene_file:
            scene_file.write("// Disposable scene fixture.\n")

    def capture_tracker_launch(self, command, **kwargs):
        """Captures a tracker command without launching worker processes.

        Args:
            command (list): Tracker launch arguments.
            **kwargs: Process launch options.

        Returns:
            object: Dummy process object.
        """
        self.tracker_command = list(command)
        for option in ("--project-file", "--job-file"):
            temporary_path = command[command.index(option) + 1]
            self.addCleanup(os.remove, temporary_path)
        return object()

    def test_new_and_loaded_tasks_keep_segmentation_options_disabled(self):
        """Enables both phase capabilities while keeping old projects at their previous defaults."""
        for task in (tasks.TaskMayaImport(), tasks.create_task_from_dict({
                "task_type": "maya_import", "parameters": {"source_path": self.input_directory}})):
            with self.subTest(parameters=task.settings):
                self.assertTrue(task.supports_run_once_before_jobs)
                self.assertTrue(task.supports_run_once_after_jobs)
                for key in ("allow_missing_input_directory", "run_once_before_multi_instance",
                            "run_once_after_multi_instance", "force_segment_separator"):
                    self.assertEqual(False, task.settings[key])
                self.assertEqual(True, task.settings["segmentation_collapsed"])

    def test_allow_missing_folder_suppresses_only_that_tasks_source_warning(self):
        """Leaves other tasks' missing source checks active."""
        import_task = self.project.add_task(tasks.TaskMayaImport(settings={
            "source_path": self.generated_directory,
        }))
        rename_task = self.project.add_task(tasks.TaskRename(settings={
            "source_path": self.generated_directory,
        }))
        self.assertEqual(1, len(import_task.validate_common_settings(self.project).warnings))
        import_task.settings["allow_missing_input_directory"] = True
        self.assertEqual([], import_task.validate_common_settings(self.project).warnings)
        self.assertEqual(1, len(rename_task.validate_common_settings(self.project).warnings))
        self.assertFalse(os.path.exists(self.generated_directory))

    def test_other_settings_and_conflicting_run_phases_still_fail_validation(self):
        """Keeps scene, script, and run-phase validation active with a deferred source folder."""
        import_task = self.project.add_task(tasks.TaskMayaImport(settings={
            "source_path": self.generated_directory,
            "allow_missing_input_directory": True,
            "run_once_before_multi_instance": True,
            "run_once_after_multi_instance": True,
            "output_extension": ".fbx",
            "set_framerate": True,
            "framerate": 0,
            "run_post_script": True,
        }))
        result = self.project.validate_project(task_list=[import_task])
        self.assertEqual(4, len(result.errors))
        self.assertTrue(any("both before and after" in error for error in result.errors))
        self.assertTrue(any("output extension" in error for error in result.errors))
        self.assertTrue(any("framerate" in error for error in result.errors))
        self.assertTrue(any("post script" in error for error in result.errors))

    def test_allowed_missing_folder_still_requires_inputs_when_task_executes(self):
        """Fails execution if the preceding work never creates the source files."""
        self.project.add_task(tasks.TaskMayaImport(settings={
            "source_path": self.generated_directory,
            "allow_missing_input_directory": True,
        }))
        self.assertEqual([], self.project.validate_project().errors)
        with self.assertRaisesRegex(RuntimeError, "No source files found"):
            worker.SingleInstanceBatchRunner().run(self.project)
        self.assertFalse(os.path.exists(self.generated_directory))

    def test_project_round_trip_preserves_import_segmentation_settings(self):
        """Restores run timing, missing-folder handling, and the visual separator."""
        expected = {
            "allow_missing_input_directory": True,
            "run_once_after_multi_instance": True,
            "run_once_before_multi_instance": False,
            "force_segment_separator": True,
            "segmentation_collapsed": False,
            "segment_name": "Import generated files",
            "segment_color": "blue_light_sky",
        }
        import_task = self.project.add_task(tasks.TaskMayaImport(settings=expected))
        self.project.save_to_file(self.project.project_file_path)
        restored = model.BatchProcessorModel.from_file(self.project.project_file_path).get_task(import_task.id)
        for key, value in expected.items():
            self.assertEqual(value, restored.settings[key])
        self.assertTrue(restored.shows_segment_separator())

    def test_before_phase_imports_sources_before_tracker_launch(self):
        """Runs the import folder before launch and excludes the task from regular workers."""
        import_task = self.project.add_task(tasks.TaskMayaImport(settings={
            "source_path": self.input_directory,
            "target_path": self.generated_directory,
            "scene_load_mode": "Open",
            "run_once_before_multi_instance": True,
        }))
        self.project.add_task(tasks.TaskRename())

        def launch_tracker(command, **kwargs):
            """Checks that preflight output exists before capturing the tracker launch.

            Args:
                command (list): Tracker launch arguments.
                **kwargs: Process launch options.

            Returns:
                object: Dummy process object.
            """
            for filename in ("first.ma", "second.ma"):
                self.assertTrue(os.path.isfile(os.path.join(self.generated_directory, filename)))
            return self.capture_tracker_launch(command, **kwargs)

        with mock.patch.object(worker, "find_mayapy_executable", return_value=sys.executable), \
                mock.patch.object(worker.subprocess, "Popen", side_effect=launch_tracker) as launch_mock, \
                mock.patch.object(maya_runtime, "open_scene") as open_mock, \
                mock.patch.object(maya_runtime, "apply_scene_options"), \
                mock.patch.object(maya_runtime, "save_scene", side_effect=self.write_scene):
            worker.MultiInstanceBatchRunner().run(self.project)

        launch_mock.assert_called_once()
        self.assertEqual(2, open_mock.call_count)
        for argument in ("--skip-task-id", "--completed-preflight-task-id"):
            self.assertEqual(import_task.id, self.tracker_command[self.tracker_command.index(argument) + 1])
        self.assertNotIn("--final-task-id", self.tracker_command)

    def test_after_phase_waits_for_generated_sources_and_discovers_them_later(self):
        """Defers import until finalization and reads the source folder after outputs exist."""
        self.project.add_task(tasks.TaskRename(settings={"target_path": self.generated_directory}))
        output_directory = os.path.join(self.directory.name, "imported")
        import_task = self.project.add_task(tasks.TaskMayaImport(settings={
            "source_path": self.generated_directory,
            "target_path": output_directory,
            "scene_load_mode": "Open",
            "allow_missing_input_directory": True,
            "run_once_after_multi_instance": True,
        }))
        with mock.patch.object(worker, "find_mayapy_executable", return_value=sys.executable), \
                mock.patch.object(worker.subprocess, "Popen", side_effect=self.capture_tracker_launch), \
                mock.patch.object(maya_runtime, "open_scene") as open_mock:
            worker.MultiInstanceBatchRunner().run(self.project)
        open_mock.assert_not_called()
        self.assertFalse(os.path.exists(self.generated_directory))
        self.assertEqual(import_task.id, self.tracker_command[self.tracker_command.index("--final-task-id") + 1])

        os.makedirs(self.generated_directory)
        source_path = os.path.join(self.generated_directory, "generated.ma")
        self.write_scene(source_path)
        work_items = tracker_worker.discover_final_task_work_items(self.project, import_task, worker, tasks)
        self.assertEqual([source_path], [item.current_path for item in work_items])
        with mock.patch.object(maya_runtime, "open_scene") as open_mock, \
                mock.patch.object(maya_runtime, "apply_scene_options"), \
                mock.patch.object(maya_runtime, "save_scene", side_effect=self.write_scene):
            result = worker.SingleInstanceBatchRunner().run(
                self.project, run_from_task_id=import_task.id, run_to_task_id=import_task.id)
        open_mock.assert_called_once_with(source_path, load_relevant_plugins=True)
        self.assertEqual(1, result.succeeded)
        self.assertEqual(0, result.failed)
        self.assertTrue(os.path.isfile(os.path.join(output_directory, "generated.ma")))


if __name__ == "__main__":
    unittest.main(verbosity=2)
