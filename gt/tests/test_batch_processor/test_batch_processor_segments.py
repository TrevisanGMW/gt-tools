"""
Unit tests for batch processor input segmentation (Start New Input List).

These tests cover the pure-Python segment logic and the single-input reset
flag. They avoid Maya imports so they run outside a Maya environment.
"""

import logging
import os
import sys
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


class TestBatchProcessorSegments(unittest.TestCase):
    def _build_input_task(self, start_new_input_list=False, enabled=True):
        """Builds an input task with the segment flag set as requested.

        Args:
            start_new_input_list (bool, optional): Segment-start flag value.
            enabled (bool, optional): Whether the task is enabled.

        Returns:
            TaskInput: Configured input task.
        """
        task = tasks.TaskInput()
        task.settings["start_new_input_list"] = start_new_input_list
        task.enabled = enabled
        return task

    def _build_process_task(self, enabled=True):
        """Builds a simple processing task.

        Args:
            enabled (bool, optional): Whether the task is enabled.

        Returns:
            BatchTask: Rename processing task.
        """
        task = tasks.create_task(task_type=constants.TaskType.RENAME)
        task.enabled = enabled
        return task

    def test_default_flag_is_false(self):
        expected = False
        task = tasks.TaskInput()
        self.assertEqual(expected, task.settings.get("start_new_input_list"))
        self.assertEqual(expected, task.starts_new_input_list())

    def test_process_task_never_starts_segment(self):
        expected = False
        process_task = self._build_process_task()
        process_task.settings["start_new_input_list"] = True
        self.assertEqual(expected, process_task.starts_new_input_list())

    def test_single_segment_when_no_reset_flag(self):
        model = batch_processor_model.BatchProcessorModel()
        model.tasks = [
            self._build_input_task(),
            self._build_process_task(),
            self._build_input_task(),
            self._build_process_task(),
        ]
        expected = 1
        self.assertEqual(expected, len(model.get_task_segments()))
        self.assertFalse(model.has_input_segments())

    def test_two_segments_split_at_reset_flag(self):
        model = batch_processor_model.BatchProcessorModel()
        first_input = self._build_input_task()
        first_process = self._build_process_task()
        second_input = self._build_input_task(start_new_input_list=True)
        second_process = self._build_process_task()
        model.tasks = [first_input, first_process, second_input, second_process]

        segments = model.get_task_segments()

        expected = 2
        self.assertEqual(expected, len(segments))
        self.assertEqual([first_input, first_process], segments[0])
        self.assertEqual([second_input, second_process], segments[1])
        self.assertTrue(model.has_input_segments())

    def test_flag_on_first_task_is_noop(self):
        model = batch_processor_model.BatchProcessorModel()
        model.tasks = [
            self._build_input_task(start_new_input_list=True),
            self._build_process_task(),
        ]
        expected = 1
        self.assertEqual(expected, len(model.get_task_segments()))

    def test_non_reset_second_input_merges_into_segment(self):
        model = batch_processor_model.BatchProcessorModel()
        model.tasks = [
            self._build_input_task(),
            self._build_input_task(start_new_input_list=False),
            self._build_process_task(),
        ]
        segments = model.get_task_segments()
        expected = 1
        self.assertEqual(expected, len(segments))
        self.assertEqual(3, len(segments[0]))

    def test_disabled_reset_input_does_not_split_enabled_segments(self):
        model = batch_processor_model.BatchProcessorModel()
        model.tasks = [
            self._build_input_task(),
            self._build_process_task(),
            self._build_input_task(start_new_input_list=True, enabled=False),
            self._build_process_task(),
        ]
        # get_task_segments defaults to enabled tasks, so the disabled reset input is excluded.
        expected = 1
        self.assertEqual(expected, len(model.get_task_segments()))

    def test_forced_separator_shows_without_reset(self):
        task = tasks.TaskInput()
        task.settings["start_new_input_list"] = False
        task.settings["force_segment_separator"] = True
        self.assertTrue(task.shows_segment_separator())
        self.assertFalse(task.starts_new_input_list())

    def test_reset_flag_alone_does_not_show_separator(self):
        # Starting a new segment no longer forces a divider; the divider is
        # controlled solely by the "Add Separator" (force_segment_separator) flag.
        task = tasks.TaskInput()
        task.settings["start_new_input_list"] = True
        task.settings["force_segment_separator"] = False
        self.assertFalse(task.shows_segment_separator())

    def test_no_separator_by_default(self):
        task = tasks.TaskInput()
        self.assertFalse(task.shows_segment_separator())

    def test_separator_shown_on_any_task_with_flag(self):
        # The divider is generic: any task can show it via force_segment_separator.
        process_task = self._build_process_task()
        self.assertFalse(process_task.shows_segment_separator())
        process_task.settings["force_segment_separator"] = True
        self.assertTrue(process_task.shows_segment_separator())

    def test_forced_separator_does_not_create_runtime_segment(self):
        model = batch_processor_model.BatchProcessorModel()
        first_input = self._build_input_task()
        first_process = self._build_process_task()
        marker_input = self._build_input_task()
        marker_input.settings["force_segment_separator"] = True
        model.tasks = [first_input, first_process, marker_input]
        # A forced separator is purely visual; it must not split runtime segments.
        expected = 1
        self.assertEqual(expected, len(model.get_task_segments()))

    def test_segment_color_name_defaults_and_custom(self):
        task = tasks.TaskInput()
        self.assertEqual("blue_light_sky", task.get_segment_color_name())
        task.settings["segment_color"] = "orange"
        self.assertEqual("orange", task.get_segment_color_name())

    def test_segment_display_name_defaults_when_empty(self):
        expected = "New Input Segment"
        task = tasks.TaskInput()
        self.assertEqual(expected, task.get_segment_display_name())

    def test_zip_task_run_once_default_true(self):
        zip_task = tasks.create_task(task_type=constants.TaskType.ZIP_COMPRESS)
        self.assertTrue(zip_task.settings.get("run_once_after_multi_instance"))

    def test_map_hierarchy_task_run_once_default_true(self):
        map_task = tasks.create_task(task_type=constants.TaskType.MAP_HIERARCHY)
        self.assertTrue(map_task.settings.get("run_once_after_multi_instance"))
        self.assertTrue(map_task.supports_run_once_after_jobs)

    def test_map_hierarchy_task_supports_separator(self):
        map_task = tasks.create_task(task_type=constants.TaskType.MAP_HIERARCHY)
        self.assertFalse(map_task.shows_segment_separator())
        self.assertEqual("New Segment", map_task.get_segment_display_name())
        map_task.settings["force_segment_separator"] = True
        map_task.settings["segment_name"] = "Remap"
        self.assertTrue(map_task.shows_segment_separator())
        self.assertEqual("Remap", map_task.get_segment_display_name())

    def test_optional_run_once_tasks_default_to_unchecked(self):
        for task_type in [
            constants.TaskType.FOLDER_COMPARE_VALIDATE,
            constants.TaskType.FILE_INTEGRITY_VALIDATE,
            constants.TaskType.MAYA_SCENE_VALIDATE,
            constants.TaskType.DELETE_PROJECT_FILES,
        ]:
            task = tasks.create_task(task_type=task_type)
            self.assertTrue(task.supports_run_once_after_jobs, task_type)
            self.assertFalse(task.settings.get("run_once_after_multi_instance"), task_type)
            self.assertFalse(task.shows_segment_separator(), task_type)
            self.assertEqual("blue_light_sky", task.get_segment_color_name(), task_type)

    def test_zip_task_supports_separator(self):
        zip_task = tasks.create_task(task_type=constants.TaskType.ZIP_COMPRESS)
        self.assertFalse(zip_task.shows_segment_separator())
        self.assertEqual("New Segment", zip_task.get_segment_display_name())
        zip_task.settings["force_segment_separator"] = True
        zip_task.settings["segment_name"] = "Finalize"
        self.assertTrue(zip_task.shows_segment_separator())
        self.assertEqual("Finalize", zip_task.get_segment_display_name())

    def test_segment_display_name_uses_custom_value(self):
        expected = "FBX Retarget"
        task = tasks.TaskInput()
        task.settings["segment_name"] = "  FBX Retarget  "
        self.assertEqual(expected, task.get_segment_display_name())

    def test_incoming_files_for_task_scoped_to_its_segment(self):
        model = batch_processor_model.BatchProcessorModel()
        first_input = self._build_input_task()
        first_process = self._build_process_task()
        second_input = self._build_input_task(start_new_input_list=True)
        second_process = self._build_process_task()
        model.tasks = [first_input, first_process, second_input, second_process]

        # Each input task reports its own discovered files.
        first_input.discover_files = lambda project: ["/in/a.fbx", "/in/b.fbx"]
        second_input.discover_files = lambda project: ["/mid/c.ma"]

        first_segment_files = model.discover_incoming_files_for_task(first_process)
        second_segment_files = model.discover_incoming_files_for_task(second_process)

        self.assertEqual(["/in/a.fbx", "/in/b.fbx"], first_segment_files)
        self.assertEqual(["/mid/c.ma"], second_segment_files)

    def test_three_segments(self):
        model = batch_processor_model.BatchProcessorModel()
        model.tasks = [
            self._build_input_task(),
            self._build_process_task(),
            self._build_input_task(start_new_input_list=True),
            self._build_process_task(),
            self._build_input_task(start_new_input_list=True),
            self._build_process_task(),
        ]
        expected = 3
        self.assertEqual(expected, len(model.get_task_segments()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
