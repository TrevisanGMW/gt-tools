"""Tests for the Merge Input task helpers, settings, and validation (no Maya required)."""

import os
import sys
import tempfile
import unittest
from unittest import mock

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_merge_input
from gt.tools.batch_processor.tasks import task_merge_input_utils as merge_utils
from gt.tools.batch_processor.tasks import task_utils


class TestMergeInputUtils(unittest.TestCase):
    """Checks pure Merge Input helpers."""

    def test_resolve_input_tokens(self):
        result = merge_utils.resolve_input_tokens(
            "{input-name}_{input-index}_{input-index-padded}", r"C:\shots\walk_01.ma", 3, 12
        )
        expected = "walk_01_3_03"
        self.assertEqual(expected, result)

    def test_sanitize_maya_name(self):
        expected = "_01_walk_take"
        self.assertEqual(expected, merge_utils.sanitize_maya_name("01 walk-take"))
        expected = "fallback"
        self.assertEqual(expected, merge_utils.sanitize_maya_name("---", "fallback"))

    def test_build_unique_name_is_case_insensitive(self):
        used_names = {"Walk"}
        expected = "walk_1"
        self.assertEqual(expected, merge_utils.build_unique_name("walk", used_names))
        expected = "walk_2"
        self.assertEqual(expected, merge_utils.build_unique_name("walk", used_names))

    def test_combine_time_ranges_ignores_invalid_entries(self):
        result = merge_utils.combine_time_ranges([(10, 20), None, (30, 5), (-4, 12)])
        expected = (-4.0, 20.0)
        self.assertEqual(expected, result)
        self.assertIsNone(merge_utils.combine_time_ranges([None]))

    def test_resolve_time_range_modes(self):
        keyframe_range = (1, 100)
        first_range = (1, 24)
        manual_range = (5, 6)
        expected = (1.0, 100.0)
        self.assertEqual(expected, merge_utils.resolve_time_range(
            merge_utils.TIME_RANGE_KEYFRAMES, keyframe_range, first_range, manual_range
        ))
        expected = (1.0, 24.0)
        self.assertEqual(expected, merge_utils.resolve_time_range(
            merge_utils.TIME_RANGE_FIRST_INPUT, keyframe_range, first_range, manual_range
        ))
        expected = (5.0, 6.0)
        self.assertEqual(expected, merge_utils.resolve_time_range(
            merge_utils.TIME_RANGE_MANUAL, keyframe_range, first_range, manual_range
        ))
        self.assertIsNone(merge_utils.resolve_time_range(
            merge_utils.TIME_RANGE_KEEP, keyframe_range, first_range, manual_range
        ))

    def test_build_sequential_offsets_skips_inputs_without_keys(self):
        result = merge_utils.build_sequential_offsets([(1, 10), None, (0, 20), (100, 110)], gap_frames=5)
        expected = [0.0, 0.0, 15.0, -60.0]
        self.assertEqual(expected, result)

    def test_build_spatial_offset(self):
        expected = [0.0, 0.0, 0.0]
        self.assertEqual(expected, merge_utils.build_spatial_offset(1, [200, 0, 10]))
        expected = [400.0, 0.0, 20.0]
        self.assertEqual(expected, merge_utils.build_spatial_offset(3, [200, 0, 10]))

    def test_sort_input_paths(self):
        paths = ["b/second.ma", "A/first.ma", "a/third.ma"]
        expected = ["A/first.ma", "a/third.ma", "b/second.ma"]
        self.assertEqual(expected, merge_utils.sort_input_paths(paths))
        self.assertEqual(paths, merge_utils.sort_input_paths(paths, sort_by_name=False))

    def test_parse_playback_range_uses_last_command(self):
        data = (
            b'setAttr ".b" -type "string" "playbackOptions -min 1 -max 24 -ast 1 -aet 48 ";\n'
            b'setAttr ".b" -type "string" "playbackOptions -min -10 -max 120.5 -ast -10 -aet 200 ";\n'
        )
        expected = (-10.0, 120.5)
        self.assertEqual(expected, merge_utils.parse_playback_range_from_bytes(data))
        self.assertIsNone(merge_utils.parse_playback_range_from_bytes(b"createNode transform;"))

    def test_read_stored_playback_range_from_ascii_scene(self):
        with tempfile.TemporaryDirectory() as directory:
            scene_path = os.path.join(directory, "shot.ma")
            with open(scene_path, "w", encoding="utf-8") as scene_file:
                scene_file.write("//Maya ASCII scene\n")
                scene_file.write('createNode script -n "sceneConfigurationScriptNode";\n')
                scene_file.write('\tsetAttr ".b" -type "string" "playbackOptions -min 12 -max 96 -ast 1 -aet 120 ";\n')
            text_path = os.path.join(directory, "notes.txt")
            with open(text_path, "w", encoding="utf-8") as text_file:
                text_file.write("playbackOptions -min 1 -max 2")
            expected = (12.0, 96.0)
            self.assertEqual(expected, merge_utils.read_stored_playback_range(scene_path))
            self.assertIsNone(merge_utils.read_stored_playback_range(text_path))
            self.assertIsNone(merge_utils.read_stored_playback_range(os.path.join(directory, "missing.ma")))


class TestMergeInputTask(unittest.TestCase):
    """Checks task registration, defaults, validation, and execution flow with a mocked Maya runtime."""

    def setUp(self):
        """Creates a disposable project."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.project.project_file_path = os.path.join(self.directory.name, "project.batch")

    def test_task_is_registered_in_outputs(self):
        task = tasks.create_task(constants.TaskType.MERGE_INPUT)
        expected = "TaskMergeInput"
        self.assertEqual(expected, task.__class__.__name__)
        output_names = [task_class.__name__ for task_class in tasks.get_task_categories().get("Outputs")]
        self.assertIn(expected, output_names)

    def test_defaults_match_agreed_behavior(self):
        settings = task_merge_input.TaskMergeInput().settings
        expected = merge_utils.TIME_RANGE_KEYFRAMES
        self.assertEqual(expected, settings["time_range_mode"])
        expected = merge_utils.TIMING_ORIGINAL
        self.assertEqual(expected, settings["timing_mode"])
        expected = merge_utils.FAILURE_SKIP
        self.assertEqual(expected, settings["on_input_failure"])
        expected = merge_utils.INPUT_NAME_TOKEN
        self.assertEqual(expected, settings["namespace"])
        self.assertFalse(settings["remove_namespace"])
        self.assertFalse(settings["sort_inputs_by_name"])
        self.assertEqual("", settings["base_scene_path"])
        self.assertTrue(settings["run_once_after_multi_instance"])
        for option_key in ("set_framerate", "set_scene_scale", "set_scene_up_axis", "group_each_input",
                           "group_all_inputs", "display_layer_per_input", "offset_inputs"):
            self.assertFalse(settings[option_key], option_key)

    def test_settings_round_trip(self):
        task = self.project.add_task(task_merge_input.TaskMergeInput(settings={"load_mode": "Reference"}))
        saved_path = self.project.save_to_file(os.path.join(self.directory.name, "merge.batch"))
        loaded_task = model.BatchProcessorModel.from_file(saved_path).get_task(task.id)
        expected = "Reference"
        self.assertEqual(expected, loaded_task.settings["load_mode"])
        self.assertIsInstance(loaded_task, task_merge_input.TaskMergeInput)

    def test_reference_mode_flags_ignored_options(self):
        task = task_merge_input.TaskMergeInput(settings={
            "load_mode": merge_utils.LOAD_MODE_REFERENCE,
            "remove_namespace": True,
            "timing_mode": merge_utils.TIMING_SEQUENTIAL,
            "namespace": "",
        })
        result = task.validate(self.project)
        self.assertTrue(result.is_valid())
        warnings_text = " ".join(result.warnings)
        self.assertIn("Remove Namespace is ignored", warnings_text)
        self.assertIn("Sequential timing is ignored", warnings_text)
        self.assertIn("References need a namespace", warnings_text)

    def test_validation_errors(self):
        task = task_merge_input.TaskMergeInput(settings={
            "time_range_mode": merge_utils.TIME_RANGE_MANUAL,
            "manual_start_frame": 50,
            "manual_end_frame": 10,
            "output_mode": task_base.OUTPUT_MODE_MODIFY,
            "run_post_script": True,
            "post_script_text": "",
            "base_scene_path": os.path.join(self.directory.name, "missing_base.ma"),
        })
        errors_text = " ".join(task.validate(self.project).errors)
        self.assertIn("manual start frame", errors_text)
        self.assertIn("cannot modify source files", errors_text)
        self.assertIn("post-merge script is enabled", errors_text)
        self.assertIn("base scene does not exist", errors_text)

    def test_large_merge_warning_and_existing_output(self):
        task = self.project.add_task(task_merge_input.TaskMergeInput(settings={"input_count_warning": 2}))
        output_path = task.build_output_path(self.project, self.directory.name)
        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write("//")
        work_items = [task_base.WorkItem(source_path=f"{index}.ma") for index in range(3)]
        warnings_text = " ".join(task.validate_work_items(work_items, self.project, self.directory.name).warnings)
        self.assertIn("will merge 3 inputs", warnings_text)
        self.assertIn("will be skipped", warnings_text)

    def test_build_output_path_strips_scene_extension(self):
        task = task_merge_input.TaskMergeInput(settings={"output_name": "review.mb", "output_extension": ".ma"})
        expected = os.path.normpath(os.path.join(self.directory.name, "review.ma"))
        self.assertEqual(expected, task.build_output_path(self.project, self.directory.name))

    def test_sample_scripts_are_discoverable(self):
        per_input = [sample["relative_path"] for sample in task_utils.get_script_samples(
            task_merge_input.INPUT_SCRIPT_SAMPLES_DIRECTORY
        )]
        post_merge = [sample["relative_path"] for sample in task_utils.get_script_samples(
            task_merge_input.POST_SCRIPT_SAMPLES_DIRECTORY
        )]
        expected = ["delete_nodes_in_list.py", "print_input_context.py", "remove_namespace.py"]
        self.assertEqual(expected, per_input)
        expected = ["frame_camera_on_node_type.py", "print_merge_context.py", "set_antialiasing.py"]
        self.assertEqual(expected, post_merge)
        for sample_path in per_input + post_merge:
            self.assertTrue(sample_path.endswith(".py"))

    def test_skip_policy_continues_and_stop_policy_raises(self):
        work_items = [task_base.WorkItem(source_path=os.path.join(self.directory.name, name))
                      for name in ("b_bad.ma", "a_good.ma")]
        fake_runtime = self.build_fake_runtime(failing_name="b_bad.ma")
        task = self.project.add_task(
            task_merge_input.TaskMergeInput(settings={"output_mode": task_base.OUTPUT_MODE_PASSTHROUGH})
        )
        messages = []
        progress_events = []
        with mock.patch.dict(sys.modules, {
            "gt.tools.batch_processor.tasks.task_merge_input_maya": fake_runtime,
        }), mock.patch.object(task_merge_input, "batch_processor_maya") as runtime_mock:
            runtime_mock.get_maya_file_type.return_value = "mayaAscii"
            task_merge_input_module = sys.modules["gt.tools.batch_processor.tasks"]
            with mock.patch.object(task_merge_input_module, "task_merge_input_maya", fake_runtime, create=True):
                result = task.execute(None, self.project, self.directory.name, context={
                    "work_items": work_items,
                    "report_message": messages.append,
                    "report_progress": lambda **kwargs: progress_events.append(kwargs),
                })
                self.assertEqual(work_items, result)
                loaded_paths = [call[0] for call in fake_runtime.loaded]
                expected = ["b_bad.ma", "a_good.ma"]  # Incoming order is kept by default.
                self.assertEqual(expected, [os.path.basename(path) for path in loaded_paths])
                expected = [(0, 2), (1, 2), (2, 2)]
                self.assertEqual(
                    expected,
                    [(event["completed_units"], event["total_units"]) for event in progress_events],
                )
                self.assertTrue(any("Skipped after error" in message for message in messages))
                expected = ("b_bad", "a_good")
                self.assertEqual(expected, tuple(call[1] for call in fake_runtime.loaded))

                task.settings["on_input_failure"] = merge_utils.FAILURE_STOP
                fake_runtime.loaded.clear()
                with self.assertRaises(RuntimeError):
                    task.execute(None, self.project, self.directory.name, context={"work_items": work_items})

    @staticmethod
    def build_fake_runtime(failing_name):
        """Builds a stand-in for the Merge Input Maya runtime module.

        Args:
            failing_name (str): Input file name that raises during loading.

        Returns:
            object: Fake runtime exposing the functions used by the task.
        """

        class FakeRuntime:
            """Records load calls and returns predictable values."""

            loaded = []

            @staticmethod
            def get_existing_namespaces():
                """Returns no existing namespaces.

                Returns:
                    set: Empty set.
                """
                return set()

            @classmethod
            def load_input(cls, file_path, load_mode, namespace="", deferred=False, load_plugins=True):
                """Records a load and fails for the configured file.

                Args:
                    file_path (str): Input path.
                    load_mode (str): Load mode.
                    namespace (str, optional): Namespace.
                    deferred (bool, optional): Deferred reference flag.
                    load_plugins (bool, optional): Plugin flag.

                Returns:
                    tuple: Fake nodes and reference node.
                """
                cls.loaded.append((file_path, namespace))
                if os.path.basename(file_path) == failing_name:
                    raise RuntimeError("corrupt file")
                return [f"{namespace}:root"], ""

            get_node_ids = staticmethod(lambda nodes: list(nodes))
            get_nodes_from_ids = staticmethod(lambda node_ids: list(node_ids))
            get_root_transforms = staticmethod(lambda nodes: list(nodes))
            get_key_range = staticmethod(lambda anim_curves=None: (1.0, 10.0))
            get_time_anim_curves = staticmethod(lambda nodes=None: [])
            set_scene_time_range = staticmethod(lambda time_range: None)
            open_base_scene = staticmethod(lambda file_path, load_plugins=True: None)
            set_scene_file_type = staticmethod(lambda file_type: None)

        return FakeRuntime


if __name__ == "__main__":
    unittest.main()
