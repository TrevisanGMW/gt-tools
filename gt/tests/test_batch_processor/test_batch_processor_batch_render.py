"""Unit tests for the Batch Processor Maya batch render task."""

import logging
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Scripts
test_package_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_package_dir)
package_root_dir = os.path.dirname(tests_dir)
for path_to_append in [package_root_dir, tests_dir]:
    if path_to_append not in sys.path:
        sys.path.append(path_to_append)

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor.tasks import task_batch_render


class TestBatchProcessorBatchRender(unittest.TestCase):
    """Tests batch render settings, path assembly, and command construction."""

    def setUp(self):
        """Creates a temporary folder and a default batch render task."""
        self.temp_dir = tempfile.mkdtemp()
        self.task = tasks.create_task(constants.TaskType.BATCH_RENDER)

    def tearDown(self):
        """Removes the temporary folder created for the test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_work_item(self, file_name="shot_010.ma"):
        """Creates a work item pointing at a scene inside the temporary folder.

        Args:
            file_name (str, optional): Scene file name.

        Returns:
            WorkItem: Work item used by the tests.
        """
        scene_path = os.path.join(self.temp_dir, "scenes", file_name)
        return tasks.WorkItem(source_path=scene_path, current_path=scene_path)

    def test_batch_render_task_is_registered(self):
        expected = "TaskBatchRender"
        self.assertEqual(expected, self.task.__class__.__name__)

        expected = "Outputs"
        self.assertEqual(expected, self.task.category)

        expected = True
        self.assertEqual(expected, self.task.is_output_task)

    def test_batch_render_task_class_is_available_from_registry(self):
        expected = task_batch_render.TaskBatchRender
        self.assertEqual(expected, tasks.get_task_class(constants.TaskType.BATCH_RENDER))

    def test_default_target_path_points_at_the_output_folder(self):
        expected = "{project-dir}/{output-dir}"
        self.assertEqual(expected, self.task.settings.get("target_path"))

    def test_default_settings_use_folder_per_file_and_scene_token(self):
        expected = True
        self.assertEqual(expected, self.task.settings.get("create_folder_per_file"))

        expected = "<Scene>"
        self.assertEqual(expected, self.task.settings.get("file_name_prefix"))

        expected = task_batch_render.PROJECT_MODE_AUTO
        self.assertEqual(expected, self.task.settings.get("project_mode"))

    def test_output_dir_creates_one_folder_per_incoming_file(self):
        work_item = self.create_work_item()
        output_dir = self.task.build_render_output_dir(work_item, os.path.join(self.temp_dir, "renders"))

        expected = os.path.normpath(os.path.join(self.temp_dir, "renders", "shot_010"))
        self.assertEqual(expected, os.path.normpath(output_dir))

    def test_output_dir_is_flat_when_folder_per_file_is_disabled(self):
        self.task.settings["create_folder_per_file"] = False
        work_item = self.create_work_item()
        output_dir = self.task.build_render_output_dir(work_item, os.path.join(self.temp_dir, "renders"))

        expected = os.path.normpath(os.path.join(self.temp_dir, "renders"))
        self.assertEqual(expected, os.path.normpath(output_dir))

    def test_file_name_prefix_resolves_batch_tokens_and_keeps_render_tokens(self):
        self.task.settings["file_name_prefix"] = "<Scene>_{name}_{ext}_<Camera>"
        prefix = self.task.build_file_name_prefix(self.create_work_item())

        expected = "<Scene>_shot_010_ma_<Camera>"
        self.assertEqual(expected, prefix)

    def test_empty_file_name_prefix_keeps_the_scene_prefix(self):
        self.task.settings["file_name_prefix"] = "   "

        expected = ""
        self.assertEqual(expected, self.task.build_file_name_prefix(self.create_work_item()))

    def test_render_command_omits_disabled_overrides(self):
        command = self.task.build_render_command(
            executable_path="Render.exe",
            work_item=self.create_work_item(),
            output_dir=os.path.join(self.temp_dir, "renders", "shot_010"),
            project=None,
        )

        expected = False
        self.assertEqual(expected, "-x" in command)
        self.assertEqual(expected, "-s" in command)
        self.assertEqual(expected, "-cam" in command)

        expected = True
        self.assertEqual(expected, "-rd" in command)
        self.assertEqual(expected, "-im" in command)

    def test_frame_progress_callbacks_are_passed_by_default(self):
        command = self.task.build_render_command(
            executable_path="Render.exe",
            work_item=self.create_work_item(),
            output_dir=os.path.join(self.temp_dir, "renders"),
            project=None,
        )

        expected = True
        self.assertEqual(expected, "-preRender" in command)
        self.assertEqual(expected, "-preFrame" in command)
        self.assertEqual(expected, "-postFrame" in command)

    def test_disabled_frame_progress_removes_every_callback(self):
        self.task.settings["report_frame_progress"] = False

        expected = []
        self.assertEqual(expected, self.task.build_callback_arguments())

    def test_render_command_includes_enabled_overrides(self):
        self.task.settings.update(
            {
                "override_resolution": True,
                "width": 1280,
                "height": 720,
                "override_frame_range": True,
                "start_frame": 5,
                "end_frame": 20,
                "frame_step": 2,
                "override_camera": True,
                "camera_name": "renderCam",
                "override_image_format": True,
                "image_format": "exr",
                "override_frame_padding": True,
                "frame_padding": 5,
                "skip_existing_frames": True,
            }
        )

        expected = [
            "-x",
            "1280",
            "-y",
            "720",
            "-s",
            "5",
            "-e",
            "20",
            "-b",
            "2",
            "-cam",
            "renderCam",
            "-of",
            "exr",
            "-pad",
            "5",
            "-skipExistingFrames",
            "true",
        ]
        self.assertEqual(expected, self.task.build_override_arguments())

    def test_version_label_override_uses_a_pre_render_statement(self):
        self.task.settings["override_version_label"] = True
        self.task.settings["version_label"] = "v001"
        self.task.settings["report_frame_progress"] = False
        arguments = self.task.build_callback_arguments()

        expected = ["-preRender", 'setAttr -type "string" defaultRenderGlobals.renderVersion "v001";']
        self.assertEqual(expected, arguments)

    def test_version_label_override_escapes_quotes(self):
        expected = 'setAttr -type "string" defaultRenderGlobals.renderVersion "v\\"001";'
        self.assertEqual(expected, task_batch_render.build_version_label_mel('v"001'))

    def test_render_command_ends_with_the_incoming_scene(self):
        work_item = self.create_work_item()
        command = self.task.build_render_command(
            executable_path="Render.exe",
            work_item=work_item,
            output_dir=os.path.join(self.temp_dir, "renders"),
            project=None,
        )

        expected = os.path.normpath(work_item.current_path)
        self.assertEqual(expected, os.path.normpath(command[-1]))

    def test_render_command_appends_extra_arguments_before_the_scene(self):
        self.task.settings["extra_arguments"] = "-rl all"
        command = self.task.build_render_command(
            executable_path="Render.exe",
            work_item=self.create_work_item(),
            output_dir=os.path.join(self.temp_dir, "renders"),
            project=None,
        )

        expected = ["-rl", "all"]
        self.assertEqual(expected, command[-3:-1])

    def test_auto_project_mode_finds_the_scene_workspace(self):
        project_dir = os.path.join(self.temp_dir, "maya_project")
        scenes_dir = os.path.join(project_dir, "scenes")
        os.makedirs(scenes_dir)
        with open(os.path.join(project_dir, "workspace.mel"), "w", encoding="utf-8") as workspace_file:
            workspace_file.write("//Maya workspace\n")
        scene_path = os.path.join(scenes_dir, "shot_010.ma")
        work_item = tasks.WorkItem(source_path=scene_path, current_path=scene_path)

        expected = os.path.normpath(project_dir)
        self.assertEqual(expected, os.path.normpath(self.task.resolve_maya_project_dir(work_item, None)))

    def test_auto_project_mode_returns_empty_without_a_workspace(self):
        expected = ""
        self.assertEqual(expected, self.task.resolve_maya_project_dir(self.create_work_item(), None))

    def test_disabled_project_setting_is_not_passed_to_the_renderer(self):
        self.task.settings["set_project"] = False

        expected = ""
        self.assertEqual(expected, self.task.resolve_maya_project_dir(self.create_work_item(), None))

    def test_rendered_images_are_detected_for_both_frame_conventions(self):
        expected = True
        self.assertEqual(expected, task_batch_render.is_rendered_image("shot.png.0001"))
        self.assertEqual(expected, task_batch_render.is_rendered_image("shot.0001.png"))
        self.assertEqual(expected, task_batch_render.is_rendered_image("shot.EXR"))

        expected = False
        self.assertEqual(expected, task_batch_render.is_rendered_image("shot_render.log"))
        self.assertEqual(expected, task_batch_render.is_rendered_image("shot_010.ma"))

    def test_list_rendered_files_finds_images_in_layer_subfolders(self):
        layer_dir = os.path.join(self.temp_dir, "renders", "rs_beauty")
        os.makedirs(layer_dir)
        for file_name in ["shot.png.0001", "shot.png.0002", "shot_render.log"]:
            with open(os.path.join(layer_dir, file_name), "w", encoding="utf-8") as image_file:
                image_file.write("data")

        expected = ["shot.png.0001", "shot.png.0002"]
        rendered_files = task_batch_render.list_rendered_files(os.path.join(self.temp_dir, "renders"))
        self.assertEqual(expected, [os.path.basename(path) for path in rendered_files])

    def test_validation_rejects_modify_in_place(self):
        self.task.settings["output_mode"] = "modify_in_place"

        expected = False
        self.assertEqual(expected, self.task.validate(None).is_valid())

    def test_validation_rejects_unknown_prefix_tokens(self):
        self.task.settings["file_name_prefix"] = "{unknown}"
        errors = self.task.validate(None).errors

        expected = 1
        self.assertEqual(expected, len([error for error in errors if "{unknown}" in error]))

    def test_validation_accepts_maya_render_tokens(self):
        self.task.settings["file_name_prefix"] = "<Scene>_<Camera>_<Version>"
        errors = self.task.validate(None).errors

        expected = []
        self.assertEqual(expected, [error for error in errors if "prefix" in error])

    def test_validation_rejects_inverted_frame_range(self):
        self.task.settings.update({"override_frame_range": True, "start_frame": 20, "end_frame": 5})
        errors = self.task.validate(None).errors

        expected = 1
        self.assertEqual(expected, len([error for error in errors if "end frame" in error]))

    def test_validation_requires_a_camera_name_when_overriding_the_camera(self):
        self.task.settings.update({"override_camera": True, "camera_name": "  "})
        errors = self.task.validate(None).errors

        expected = 1
        self.assertEqual(expected, len([error for error in errors if "camera" in error]))

    def test_validation_requires_a_custom_project_path(self):
        self.task.settings["project_mode"] = task_batch_render.PROJECT_MODE_CUSTOM
        errors = self.task.validate(None).errors

        expected = 1
        self.assertEqual(expected, len([error for error in errors if "project path" in error]))

    def test_existing_images_are_skipped_when_overwrite_is_disabled(self):
        work_item = self.create_work_item()
        output_dir = self.task.build_render_output_dir(work_item, os.path.join(self.temp_dir, "renders"))
        os.makedirs(output_dir)
        with open(os.path.join(output_dir, "shot_010.png.0001"), "w", encoding="utf-8") as image_file:
            image_file.write("data")

        with self.assertRaises(task_batch_render.task_base.TaskSkip):
            self.task.execute(work_item, project=None, step_output_dir=os.path.join(self.temp_dir, "renders"))

    def test_execute_reports_rendered_files_and_returns_the_output_folder(self):
        work_item = self.create_work_item()
        step_output_dir = os.path.join(self.temp_dir, "renders")
        output_dir = self.task.build_render_output_dir(work_item, step_output_dir)
        self.task.settings["write_process_log"] = False

        def fake_render(command, log_path="", monitor=None):
            """Creates fake rendered images instead of launching the renderer.

            Args:
                command (list): Command that would have been executed.
                log_path (str, optional): Unused log path.
                monitor (RenderProgressMonitor, optional): Unused progress monitor.

            Returns:
                tuple: Return code and captured process output.
            """
            for frame in [1, 2]:
                image_path = os.path.join(output_dir, "shot_010.png.000{0}".format(frame))
                with open(image_path, "w", encoding="utf-8") as image_file:
                    image_file.write("data")
            return 0, ""

        with mock.patch.object(task_batch_render, "find_render_executable", return_value="Render.exe"):
            with mock.patch.object(self.task, "run_render_process", side_effect=fake_render):
                result = self.task.execute(work_item, project=None, step_output_dir=step_output_dir)

        expected = os.path.normpath(output_dir)
        self.assertEqual(expected, os.path.normpath(result.current_path))

        expected = 2
        self.assertEqual(expected, result.metadata.get("rendered_file_count"))

    def test_execute_fails_when_the_renderer_creates_no_images(self):
        work_item = self.create_work_item()
        self.task.settings["write_process_log"] = False

        with mock.patch.object(task_batch_render, "find_render_executable", return_value="Render.exe"):
            with mock.patch.object(self.task, "run_render_process", return_value=(0, "")):
                with self.assertRaises(RuntimeError):
                    self.task.execute(work_item, project=None, step_output_dir=os.path.join(self.temp_dir, "out"))

    def test_execute_fails_when_the_renderer_returns_an_error_code(self):
        work_item = self.create_work_item()
        self.task.settings["write_process_log"] = False

        with mock.patch.object(task_batch_render, "find_render_executable", return_value="Render.exe"):
            with mock.patch.object(self.task, "run_render_process", return_value=(1, "boom")):
                with self.assertRaises(RuntimeError):
                    self.task.execute(work_item, project=None, step_output_dir=os.path.join(self.temp_dir, "out"))

    def create_monitor(self, output_dir=""):
        """Creates a progress monitor with recording callbacks.

        Args:
            output_dir (str, optional): Directory watched for rendered images.

        Returns:
            tuple: Monitor, recorded messages, and recorded progress reports.
        """
        messages = []
        progress = []

        def record_progress(completed_units, total_units, unit_label=""):
            """Records one progress report.

            Args:
                completed_units (int): Frames reported so far.
                total_units (int): Total frames.
                unit_label (str, optional): Unit label.
            """
            progress.append((completed_units, total_units, unit_label))

        monitor = task_batch_render.RenderProgressMonitor(
            output_dir=output_dir or os.path.join(self.temp_dir, "renders"),
            scene_name="shot_010.ma",
            task_type=constants.TaskType.BATCH_RENDER,
            report_message=messages.append,
            report_progress=record_progress,
        )
        return monitor, messages, progress

    def test_monitor_reports_progress_for_each_started_frame(self):
        monitor, messages, progress = self.create_monitor()
        monitor.process_line("{0} 1 100 1 1".format(task_batch_render.MARKER_RANGE))
        monitor.process_line("{0} 42".format(task_batch_render.MARKER_FRAME_START))

        expected = 100
        self.assertEqual(expected, monitor.total_frames)

        expected = (42, 100, "frames")
        self.assertEqual(expected, progress[-1])

        expected = True
        self.assertEqual(expected, "Rendering frame 42 (42/100)" in messages[-1])

    def test_monitor_reports_the_rendered_path_when_a_frame_finishes(self):
        output_dir = os.path.join(self.temp_dir, "renders")
        os.makedirs(output_dir)
        monitor, messages, _ = self.create_monitor(output_dir=output_dir)
        monitor.process_line("{0} 1 100 1 1".format(task_batch_render.MARKER_RANGE))
        image_path = os.path.join(output_dir, "shot_010.png.0041")
        with open(image_path, "w", encoding="utf-8") as image_file:
            image_file.write("data")
        monitor.process_line("{0} 41".format(task_batch_render.MARKER_FRAME_END))

        expected = True
        self.assertEqual(expected, "Rendered frame 41 (41/100)" in messages[-1])
        self.assertEqual(expected, "shot_010.png.0041" in messages[-1])

    def test_monitor_uses_the_step_to_resolve_frame_indexes(self):
        monitor, _, progress = self.create_monitor()
        monitor.process_line("{0} 10 30 5 1".format(task_batch_render.MARKER_RANGE))
        monitor.process_line("{0} 20".format(task_batch_render.MARKER_FRAME_START))

        expected = 5
        self.assertEqual(expected, monitor.total_frames)

        expected = (3, 5, "frames")
        self.assertEqual(expected, progress[-1])

    def test_monitor_treats_a_disabled_animation_range_as_one_frame(self):
        monitor, _, progress = self.create_monitor()
        monitor.process_line("{0} 1 100 1 0".format(task_batch_render.MARKER_RANGE))

        expected = 1
        self.assertEqual(expected, monitor.total_frames)

    def test_monitor_ignores_unrelated_renderer_output(self):
        monitor, messages, progress = self.create_monitor()
        monitor.process_line("00:00:01 1816MB | Arnold 7.3.7.0 rendering")

        expected = []
        self.assertEqual(expected, messages)
        self.assertEqual(expected, progress)

    def test_disabled_monitor_reports_nothing(self):
        monitor, messages, progress = self.create_monitor()
        monitor.is_enabled = False
        monitor.process_line("{0} 1 100 1 1".format(task_batch_render.MARKER_RANGE))
        monitor.process_line("{0} 42".format(task_batch_render.MARKER_FRAME_START))

        expected = []
        self.assertEqual(expected, messages)
        self.assertEqual(expected, progress)

    def test_frame_count_helper_handles_ranges_and_steps(self):
        expected = 100
        self.assertEqual(expected, task_batch_render.count_frames(1, 100, 1))

        expected = 5
        self.assertEqual(expected, task_batch_render.count_frames(10, 30, 5))

        expected = 1
        self.assertEqual(expected, task_batch_render.count_frames(7, 7, 1))

        expected = 0
        self.assertEqual(expected, task_batch_render.count_frames(10, 1, 1))
        self.assertEqual(expected, task_batch_render.count_frames("bad", 1, 1))

    def test_expected_frame_count_follows_the_frame_range_override(self):
        expected = 0
        self.assertEqual(expected, self.task.get_expected_frame_count())

        self.task.settings.update({"override_frame_range": True, "start_frame": 1, "end_frame": 24, "frame_step": 1})

        expected = 24
        self.assertEqual(expected, self.task.get_expected_frame_count())

    def test_serialized_task_round_trips_its_settings(self):
        self.task.settings.update({"width": 800, "version_label": "v012", "create_folder_per_file": False})
        restored_task = tasks.create_task_from_dict(self.task.to_dict())

        expected = 800
        self.assertEqual(expected, restored_task.settings.get("width"))

        expected = "v012"
        self.assertEqual(expected, restored_task.settings.get("version_label"))

        expected = False
        self.assertEqual(expected, restored_task.settings.get("create_folder_per_file"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
