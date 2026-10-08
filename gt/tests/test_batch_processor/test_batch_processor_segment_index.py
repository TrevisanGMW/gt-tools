"""Regression tests for segment task numbering and shared output paths."""

import os
import tempfile
import unittest

from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_worker
from gt.tools.batch_processor.tasks import task_utils


class TestBatchProcessorSegmentIndex(unittest.TestCase):
    """Tests segment numbering without a Maya or Qt runtime."""

    def setUp(self):
        """Creates an empty project for each numbering scenario."""
        self.project = batch_processor_model.BatchProcessorModel()
        self.project.tasks = []

    def _add_input(self, **settings):
        """Adds an input task with the requested boundary settings.

        Args:
            **settings: Input task settings.

        Returns:
            TaskInput: Added input task.
        """
        return self.project.add_task(tasks.TaskInput(settings=settings))

    def _add_task(self, **settings):
        """Adds a file-processing task with the requested index settings.

        Args:
            **settings: Rename task settings.

        Returns:
            TaskRename: Added processing task.
        """
        return self.project.add_task(tasks.TaskRename(settings=settings))

    def test_each_boundary_restarts_the_local_counter(self):
        """Restarts at input resets and visible dividers, including combined markers."""
        cases = [
            ({}, 3),
            ({"start_new_input_list": True}, 1),
            ({"force_segment_separator": True}, 1),
            ({"start_new_input_list": True, "force_segment_separator": True}, 1),
        ]
        for boundary_settings, expected in cases:
            with self.subTest(boundary_settings=boundary_settings):
                self.project.tasks = []
                self._add_input()
                self._add_task()
                self._add_task()
                boundary_task = self._add_input(**boundary_settings)
                task = self._add_task()
                self.assertEqual(expected, self.project.get_segment_task_environment_index(task))
                self.assertEqual(0, self.project.get_segment_task_environment_index(boundary_task))
                self.assertEqual(3, self.project.get_task_environment_index(task))

    def test_divider_on_a_processing_task_counts_that_task_first(self):
        """Includes the divider's own task in its new segment."""
        self._add_task()
        marker = self._add_task(force_segment_separator=True)
        following_task = self._add_task()
        self.assertEqual(1, self.project.get_segment_task_environment_index(marker))
        self.assertEqual(2, self.project.get_segment_task_environment_index(following_task))
        self.assertEqual(1, len(self.project.get_task_segments()))

    def test_checked_input_boundary_counts_before_following_tasks(self):
        """Allows an input task to occupy index 1 when its regular checkbox is enabled."""
        self._add_task()
        marker = self._add_input(start_new_input_list=True, include_in_task_index=True)
        following_task = self._add_task()
        self.assertEqual(1, self.project.get_segment_task_environment_index(marker))
        self.assertEqual(2, self.project.get_segment_task_environment_index(following_task))
        self.assertEqual(2, self.project.get_task_environment_index(marker))

    def test_regular_index_controls_both_counters(self):
        """Uses the same flag even when obsolete segment settings conflict with it."""
        excluded_task = self._add_task(include_in_task_index=False, include_in_segment_task_index=True)
        included_task = self._add_task(include_in_task_index=True, include_in_segment_task_index=False)
        following_task = self._add_task()
        self.assertEqual(0, self.project.get_segment_task_environment_index(excluded_task))
        self.assertEqual(0, self.project.get_task_environment_index(excluded_task))
        self.assertEqual(1, self.project.get_segment_task_environment_index(included_task))
        self.assertEqual(1, self.project.get_task_environment_index(included_task))
        self.assertEqual(2, self.project.get_segment_task_environment_index(following_task))
        self.assertEqual(2, self.project.get_task_environment_index(following_task))
        excluded_task.settings["include_in_task_index"] = True
        included_task.settings["include_in_task_index"] = False
        self.assertTrue(excluded_task.includes_segment_task_index())
        self.assertFalse(included_task.includes_segment_task_index())
        self.assertEqual(2, self.project.get_segment_task_environment_index(following_task))
        self.assertEqual(2, self.project.get_task_environment_index(following_task))

    def test_defaults_match_existing_task_participation(self):
        """Keeps inputs and utility tasks excluded unless explicitly enabled."""
        for task_class in (
            tasks.TaskInput,
            tasks.TaskClipSnapshot,
            tasks.TaskMapHierarchy,
            tasks.TaskValidationMayaScene,
            tasks.TaskRename,
        ):
            with self.subTest(task_class=task_class.__name__):
                task = task_class()
                self.assertEqual(task.includes_task_index(), task.includes_segment_task_index())
                self.assertNotIn("include_in_segment_task_index", task.settings)
        excluded_task = tasks.TaskRename(settings={"include_in_task_index": False})
        self.assertFalse(excluded_task.includes_segment_task_index())

    def test_legacy_parameters_preserve_regular_index_choice(self):
        """Drops obsolete local settings and preserves the saved regular participation."""
        for included in (True, False):
            with self.subTest(included=included):
                data = tasks.TaskRename(settings={"include_in_task_index": included}).to_dict()
                data["parameters"]["include_in_segment_task_index"] = not included
                restored = tasks.create_task_from_dict(data)
                self.assertNotIn("include_in_segment_task_index", restored.settings)
                self.assertEqual(included, restored.includes_segment_task_index())

    def test_shared_participation_survives_save_import_and_duplicate(self):
        """Persists one index choice through project and task transfers."""
        excluded_task = self._add_task(include_in_task_index=False, include_in_segment_task_index=True)
        self._add_task(include_in_task_index=True, include_in_segment_task_index=False)
        with tempfile.TemporaryDirectory(prefix="gt_segment_index_") as directory:
            saved_path = self.project.save_to_file(os.path.join(directory, "project.batch"))
            restored = batch_processor_model.BatchProcessorModel.from_file(saved_path)
        self.assertFalse(restored.tasks[0].includes_segment_task_index())
        self.assertFalse(restored.tasks[0].includes_task_index())
        self.assertTrue(restored.tasks[1].includes_segment_task_index())
        self.assertTrue(restored.tasks[1].includes_task_index())
        duplicate = restored.duplicate_task(restored.tasks[0].id)
        imported = restored.add_task_from_dict(excluded_task.to_dict())
        for task in (duplicate, imported):
            self.assertFalse(task.includes_segment_task_index())
            self.assertFalse(task.includes_task_index())
            self.assertNotEqual(excluded_task.id, task.id)
            self.assertNotIn("include_in_segment_task_index", task.settings)
        excluded_task.settings["include_in_segment_task_index"] = True
        self.assertNotIn("include_in_segment_task_index", excluded_task.to_dict()["parameters"])

    def test_disabled_task_preference_applies_within_each_segment(self):
        """Uses the existing automation preference and explicit enabled-only override."""
        self._add_task(force_segment_separator=True)
        disabled_task = self._add_task()
        disabled_task.enabled = False
        task = self._add_task()
        self.assertEqual(3, self.project.get_segment_task_environment_index(task))
        self.assertEqual(2, self.project.get_segment_task_environment_index(task, enabled_only=True))
        self.project.run_settings["ignore_disabled_tasks_for_task_index"] = True
        self.assertEqual(2, self.project.get_segment_task_environment_index(task))
        self.assertEqual(0, self.project.get_segment_task_environment_index(disabled_task))
        self.assertEqual(3, self.project.get_segment_task_environment_index(task, enabled_only=False))

    def test_disabled_boundary_still_restarts_numbering(self):
        """Keeps segment numbering stable when a boundary task is disabled."""
        for boundary_settings in (
            {"force_segment_separator": True},
            {"start_new_input_list": True},
        ):
            with self.subTest(boundary_settings=boundary_settings):
                self.project.tasks = []
                self._add_task()
                marker = self._add_input(**boundary_settings)
                marker.enabled = False
                task = self._add_task()
                self.assertEqual(1, self.project.get_segment_task_environment_index(task, enabled_only=True))

    def test_environment_formats_aliases_and_nested_custom_values(self):
        """Expands both formats and underscore aliases without a global-index override."""
        self._add_task()
        task = self._add_task(force_segment_separator=True)
        environment = self.project.get_environment_variables(task=task, task_index=99)
        self.assertEqual("01", environment["{seg-task-idx-padded}"])
        self.assertEqual("1", environment["{seg-task-index}"])
        self.assertEqual("99", environment["{task-idx-padded}"])
        self.project.set_custom_environment_variables({
            "stage-folder": {"value": "{seg_task_idx_padded}_shared", "query": False},
        })
        result = self.project.resolve_template("{stage-folder}/{seg_task_index}", task)
        self.assertEqual("01_shared/1", result)
        task.settings["include_in_task_index"] = False
        environment = self.project.get_environment_variables(task=task, include_braces=False)
        self.assertEqual("00", environment["seg-task-idx-padded"])
        self.assertEqual("0", environment["seg-task-index"])

    def test_neighbor_paths_resolve_using_each_neighbors_segment(self):
        """Resolves previous and next task folders with the neighbor's local counter."""
        self.project.environment_variables["project-dir"] = tempfile.gettempdir()
        first = self._add_task(target_path="{project-dir}/{seg-task-idx-padded}_first")
        middle = self._add_task(force_segment_separator=True)
        last = self._add_task(target_path="{project-dir}/{seg-task-idx-padded}_last")
        self.assertEqual(first.resolve_task_path(self.project), self.project.get_previous_task_path(middle))
        self.assertEqual(last.resolve_task_path(self.project), self.project.get_next_task_path(middle))
        self.assertEqual("01_first", os.path.basename(self.project.get_previous_task_path(middle)))
        self.assertEqual("02_last", os.path.basename(self.project.get_next_task_path(middle)))

    def test_neighbor_segment_indices_use_each_tasks_own_segment(self):
        """Reports neighbor indices on either side of a segment boundary."""
        first_task = self._add_task()
        second_task = self._add_task()
        boundary_task = self._add_task(force_segment_separator=True)
        current_task = self._add_task()
        self._add_task()

        environment = self.project.get_environment_variables(task=current_task, include_braces=False)
        expected_values = {"previous": 1, "previous-previous": 2, "pre-previous": 2, "next": 3}
        for prefix, expected_index in expected_values.items():
            with self.subTest(prefix=prefix):
                self.assertEqual(f"{expected_index:02d}", environment[f"seg-{prefix}-task-idx-padded"])
                self.assertEqual(str(expected_index), environment[f"seg-{prefix}-task-index"])
        self.assertEqual("04", environment["task-idx-padded"])
        self.assertEqual("02", environment["seg-task-idx-padded"])

        environment = self.project.get_environment_variables(task=boundary_task, include_braces=False)
        self.assertEqual("02", environment["seg-previous-task-idx-padded"])
        self.assertEqual("01", environment["seg-previous-previous-task-idx-padded"])
        self.assertEqual("02", environment["seg-next-task-idx-padded"])
        self.assertEqual("01", self.project.resolve_template("{seg-task-idx-padded}", task=first_task))
        self.assertEqual("02", self.project.resolve_template("{seg-task-idx-padded}", task=second_task))

    def test_neighbor_indices_skip_disabled_tasks_and_apply_counter_policy(self):
        """Uses enabled neighbors and the shared disabled-task counting preference."""
        self._add_task()
        disabled_task = self._add_task()
        disabled_task.enabled = False
        previous_task = self._add_task()
        current_task = self._add_task()
        next_task = self._add_task()

        environment = self.project.get_environment_variables(task=current_task, include_braces=False)
        self.assertEqual("03", environment["seg-previous-task-idx-padded"])
        self.assertEqual("01", environment["seg-previous-previous-task-idx-padded"])
        self.assertEqual("05", environment["seg-next-task-idx-padded"])
        self.project.run_settings["ignore_disabled_tasks_for_task_index"] = True
        environment = self.project.get_environment_variables(task=current_task, include_braces=False)
        self.assertEqual("02", environment["seg-previous-task-idx-padded"])
        self.assertEqual("01", environment["seg-previous-previous-task-idx-padded"])
        self.assertEqual("04", environment["seg-next-task-idx-padded"])
        previous_task.settings["include_in_task_index"] = False
        next_task.settings["include_in_task_index"] = False
        environment = self.project.get_environment_variables(task=current_task, include_braces=False)
        self.assertEqual("00", environment["seg-previous-task-idx-padded"])
        self.assertEqual("0", environment["seg-previous-task-index"])
        self.assertEqual("00", environment["seg-next-task-idx-padded"])

    def test_missing_neighbors_resolve_zero_indices(self):
        """Uses padded and unpadded zero when neighbor tasks are unavailable."""
        task = self._add_task()
        environment = self.project.get_environment_variables(task=task, include_braces=False)
        for prefix in ("previous", "previous-previous", "pre-previous", "next"):
            with self.subTest(prefix=prefix):
                self.assertEqual("00", environment[f"seg-{prefix}-task-idx-padded"])
                self.assertEqual("0", environment[f"seg-{prefix}-task-index"])
                self.assertEqual("00", environment[f"{prefix}-task-idx-padded"])
                self.assertEqual("0", environment[f"{prefix}-task-index"])

    def test_relative_padded_tokens_use_consistent_names(self):
        """Lists canonical padded names while resolving older neighbor aliases."""
        self._add_task()
        self._add_task()
        current_task = self._add_task()
        self._add_task()
        environment = self.project.get_environment_variables(task=current_task, include_braces=False)
        expected_values = {"previous": "02", "previous-previous": "01", "pre-previous": "01", "next": "04"}
        for prefix, expected_value in expected_values.items():
            with self.subTest(prefix=prefix):
                underscore_prefix = prefix.upper().replace("-", "_")
                self.assertEqual(expected_value, environment[f"{prefix}-task-idx-padded"])
                self.assertNotIn(f"{prefix}-task-idx", environment)
                self.assertEqual(
                    expected_value,
                    self.project.resolve_template(f"{{{prefix}-task-idx}}", task=current_task),
                )
                self.assertEqual(
                    expected_value,
                    self.project.resolve_template(f"{{SEG_{underscore_prefix}_TASK_IDX_PADDED}}", task=current_task),
                )

    def test_legacy_relative_tokens_are_available_only_when_requested(self):
        """Keeps compatibility keys out of listings while exposing them to Python scripts."""
        self._add_task()
        self._add_task()
        current_task = self._add_task()
        self._add_task()
        canonical_environment = self.project.get_environment_variables(task=current_task, include_braces=False)
        runtime_environment = self.project.get_environment_variables(
            task=current_task, include_braces=False, include_legacy_aliases=True
        )
        braced_runtime_environment = self.project.get_environment_variables(
            task=current_task, include_legacy_aliases=True
        )
        expected_values = {"previous": "02", "previous-previous": "01", "pre-previous": "01", "next": "04"}
        for prefix, expected_value in expected_values.items():
            with self.subTest(prefix=prefix):
                legacy_name = f"{prefix}-task-idx"
                canonical_name = f"{legacy_name}-padded"
                self.assertNotIn(legacy_name, canonical_environment)
                self.assertEqual(expected_value, canonical_environment[canonical_name])
                self.assertEqual(expected_value, runtime_environment[legacy_name])
                self.assertEqual(expected_value, runtime_environment[canonical_name])
                self.assertEqual(expected_value, braced_runtime_environment[f"{{{legacy_name}}}"])
        for variable_name in ("task-idx", "seg-task-idx", "segment-task-idx"):
            self.assertNotIn(variable_name, runtime_environment)
        canonical_after_runtime = self.project.get_environment_variables(task=current_task, include_braces=False)
        for prefix, expected_value in expected_values.items():
            self.assertNotIn(f"{prefix}-task-idx", canonical_after_runtime)
            self.assertEqual(expected_value, canonical_after_runtime[f"{prefix}-task-idx-padded"])

    def test_python_script_contexts_preserve_legacy_indices_and_environment_toggle(self):
        """Shares canonical and compatibility indices through both script context builders."""
        self._add_task()
        self._add_task()
        script_task = self.project.add_task(tasks.TaskPythonScript())
        self._add_task()
        work_item = tasks.WorkItem(os.path.join(tempfile.gettempdir(), "input.ma"))
        output_path = os.path.join(tempfile.gettempdir(), "output.ma")
        expected_values = {"previous": "02", "previous-previous": "01", "pre-previous": "01", "next": "04"}
        for builder_name in ("task", "shared"):
            for pass_environment in (True, False):
                with self.subTest(builder_name=builder_name, pass_environment=pass_environment):
                    if builder_name == "task":
                        script_task.settings["pass_environment_arguments"] = pass_environment
                        context = script_task.build_script_context(
                            work_item=work_item,
                            output_path=output_path,
                            project=self.project,
                            script_paths=[],
                        )
                    else:
                        context = task_utils.build_python_script_runtime_context(
                            project=self.project,
                            task=script_task,
                            work_item=work_item,
                            output_path=output_path,
                            pass_environment_arguments=pass_environment,
                        )
                    self.assertIs(context["env"], context["environment_variables"])
                    if not pass_environment:
                        self.assertEqual({}, context["env"])
                        continue
                    for prefix, expected_value in expected_values.items():
                        self.assertEqual(expected_value, context["env"][f"{prefix}-task-idx"])
                        self.assertEqual(expected_value, context["env"][f"{prefix}-task-idx-padded"])
                    self.assertEqual("03", context["env"]["task-idx-padded"])
                    self.assertEqual("03", context["env"]["seg-task-idx-padded"])
                    listed_environment = self.project.get_environment_variables(
                        task=script_task, include_braces=False
                    )
                    for prefix in expected_values:
                        self.assertNotIn(f"{prefix}-task-idx", listed_environment)

    def test_counter_handles_missing_tasks_and_more_than_two_digits(self):
        """Returns zero for unknown tasks and preserves indexes above 99."""
        self.assertEqual(0, self.project.get_segment_task_environment_index(None))
        self.assertEqual(0, self.project.get_segment_task_environment_index(tasks.TaskRename()))
        for task_number in range(101):
            self._add_task()
        environment = self.project.get_environment_variables(
            task=self.project.tasks[-1], include_braces=False, include_neighbor_paths=False
        )
        self.assertEqual("101", environment["seg-task-idx-padded"])
        self.assertEqual("101", environment["seg-task-index"])

    def test_local_variable_names_are_reserved(self):
        """Prevents custom definitions from shadowing segment task counters."""
        variable_names = ["seg-task-idx-padded", "seg-task-index", "SEG_TASK_IDX_PADDED"]
        for prefix in ("previous", "previous-previous", "pre-previous", "next"):
            variable_names.extend((f"seg-{prefix}-task-idx-padded", f"seg-{prefix}-task-index"))
        for variable_name in variable_names:
            with self.subTest(variable_name=variable_name):
                self.assertFalse(self.project.is_custom_environment_name_available(f"{{{variable_name}}}"))
                self.assertIn(
                    batch_processor_model.normalize_environment_key(variable_name),
                    self.project.get_reserved_environment_keys(),
                )

    def test_renamed_variables_have_no_legacy_aliases(self):
        """Exposes only the selected global and segment counter names."""
        task = self._add_task()
        environment = self.project.get_environment_variables(task=task, include_braces=False)
        self.assertEqual("01", environment["task-idx-padded"])
        self.assertEqual("1", environment["task-index"])
        self.assertEqual("01", environment["seg-task-idx-padded"])
        self.assertEqual("1", environment["seg-task-index"])
        for legacy_name in ("task-idx", "segment-task-idx", "segment-task-index"):
            with self.subTest(legacy_name=legacy_name):
                self.assertNotIn(legacy_name, environment)
                self.assertNotIn(legacy_name, self.project.get_reserved_environment_keys())
                template = f"{{{legacy_name}}}"
                self.assertEqual(template, self.project.resolve_template(template, task=task))
        self.assertEqual("01", self.project.resolve_template("{TASK_IDX_PADDED}", task=task))
        self.assertEqual("01/1", self.project.resolve_template(
            "{SEG_TASK_IDX_PADDED}/{seg_task_index}", task=task
        ))

    def test_registered_task_defaults_use_current_variable_names(self):
        """Checks every registered task's output and report defaults after the rename."""
        for task_type in tasks.TASK_TYPES:
            with self.subTest(task_type=task_type):
                task = self.project.add_task(tasks.create_task(task_type))
                default_values = str(task.get_default_settings())
                for legacy_name in ("task-idx", "segment-task-idx", "segment-task-index"):
                    self.assertNotIn(f"{{{legacy_name}}}", default_values)
                task_index = self.project.get_task_environment_index(task)
                self.assertEqual(
                    f"{task_index:02d}",
                    self.project.resolve_template("{task-idx-padded}", task=task),
                )

    def test_selected_run_keeps_its_index_from_the_project_snapshot(self):
        """Uses full project order after loading a snapshot and running only one task."""
        with tempfile.TemporaryDirectory(prefix="gt_segment_subset_") as directory:
            self.project.environment_variables["project-dir"] = directory
            source_dir = os.path.join(directory, "input")
            os.makedirs(source_dir)
            with open(os.path.join(source_dir, "asset.txt"), "w", encoding="utf-8") as source_file:
                source_file.write("asset")
            self._add_task()
            self._add_input(source_path=source_dir, extensions=[".txt"], start_new_input_list=True)
            self._add_task(target_path="{project-dir}/{seg-task-idx-padded}_first")
            selected_task = self._add_task(
                source_path=source_dir,
                target_path="{project-dir}/{seg-task-idx-padded}_selected",
            )
            saved_path = self.project.save_to_file(os.path.join(directory, "snapshot.batch"))
            restored = batch_processor_model.BatchProcessorModel.from_file(saved_path)
            runner = batch_processor_worker.SingleInstanceBatchRunner()
            result = runner.run(
                restored, run_from_task_id=selected_task.id, run_to_task_id=selected_task.id
            )
            self.assertEqual(0, result.failed)
            self.assertTrue(os.path.isfile(os.path.join(directory, "02_selected", "asset.txt")))
            self.assertFalse(os.path.exists(os.path.join(directory, "01_selected")))

    def test_two_segments_write_to_the_same_numbered_folder(self):
        """Runs file copies from two inputs into one segment-numbered output folder."""
        with tempfile.TemporaryDirectory(prefix="gt_segment_output_") as directory:
            self.project.environment_variables["project-dir"] = directory
            for input_name in ("first", "second"):
                source_dir = os.path.join(directory, input_name)
                os.makedirs(source_dir)
                source_path = os.path.join(source_dir, f"{input_name}.txt")
                with open(source_path, "w", encoding="utf-8") as source_file:
                    source_file.write(input_name)
                self._add_input(
                    source_path=source_dir, extensions=[".txt"], start_new_input_list=True
                )
                self._add_task(target_path="{project-dir}/{task-dir}/{seg-task-idx-padded}_shared")
            runner = batch_processor_worker.SingleInstanceBatchRunner()
            result = runner.run(self.project)
            output_dir = os.path.join(directory, self.project.environment_variables["task-dir"], "01_shared")
            self.assertEqual(0, result.failed)
            self.assertEqual(["first.txt", "second.txt"], sorted(os.listdir(output_dir)))
            for input_name in ("first", "second"):
                for file_path in (
                    os.path.join(output_dir, f"{input_name}.txt"),
                    os.path.join(directory, input_name, f"{input_name}.txt"),
                ):
                    with open(file_path, "r", encoding="utf-8") as result_file:
                        self.assertEqual(input_name, result_file.read())


if __name__ == "__main__":
    unittest.main()
