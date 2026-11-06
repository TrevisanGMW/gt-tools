"""Validate Animation task: registration, settings validation, and execution with a patched evaluator."""

from unittest.mock import patch
import tempfile
import unittest
import json
import os

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_run_state as run_state
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor import batch_processor_tasks
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor.tasks import task_validation_animation as validation_animation
from gt.core.motion_eval import presets

NO_WRITE = {"written": False, "node": "", "attribute": "", "previous": None, "message": ""}


def build_report(score, status):
    """Builds a minimal evaluation report.

    Args:
        score (int): Overall score.
        status (str): Overall status.

    Returns:
        dict: Report dictionary.
    """
    return {
        "score": score,
        "status": status,
        "mode": "general",
        "mode_label": "General",
        "frame_range": [1, 10],
        "fps": 30.0,
        "template": "",
        "warnings": [],
        "checks": [{"key": "jitter", "label": "Jitter", "score": score, "status": status, "spans": [[2, 4]],
                    "flagged_frames": 3, "events": 1}],
    }


class TestTaskValidationAnimation(unittest.TestCase):
    """Checks the task without Maya by patching the scene evaluation."""

    def setUp(self):
        """Creates a temporary project with one input file."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.input_path = os.path.join(self.temp_dir.name, "walk.ma")
        with open(self.input_path, "w", encoding="utf-8") as file_stream:
            file_stream.write("//Maya ASCII")
        self.log_dir = os.path.join(self.temp_dir.name, "logs")
        self.project = batch_processor_model.BatchProcessorModel()
        run_state.initialize(self.project, "sample-run")

    def tearDown(self):
        """Removes the temporary project."""
        self.temp_dir.cleanup()

    def create_task(self, **settings):
        """Creates a scene-less task.

        Args:
            **settings: Setting overrides.

        Returns:
            TaskValidationAnimation: Configured task.
        """
        task = batch_processor_tasks.create_task(constants.TaskType.ANIMATION_VALIDATE)
        task.settings.update(
            {"load_scene": False, "write_score": False, "post_script_pass_environment_arguments": False}
        )
        task.settings.update(settings)
        return task

    def execute(self, task, report, context=None, write_outcome=None):
        """Executes a task with a patched evaluation.

        Args:
            task (TaskValidationAnimation): Task to execute.
            report (dict): Report returned by the patched evaluation.
            context (dict, optional): Runner context.
            write_outcome (dict, optional): Patched score write outcome.

        Returns:
            WorkItem: Returned work item.
        """
        work_item = task_base.WorkItem(source_path=self.input_path)
        with patch.object(task, "evaluate_current_scene", return_value=report):
            with patch.object(task, "write_score_if_needed", return_value=write_outcome or dict(NO_WRITE)):
                return task.execute(work_item, self.project, self.log_dir, context=context or {"item_index": 1})

    def read_log(self):
        """Reads the validation log.

        Returns:
            dict: Log data.
        """
        log_name = [name for name in os.listdir(self.log_dir) if name.endswith(".json")][0]
        with open(os.path.join(self.log_dir, log_name), "r", encoding="utf-8") as file_stream:
            return json.load(file_stream)

    def test_task_is_registered(self):
        task = batch_processor_tasks.create_task(constants.TaskType.ANIMATION_VALIDATE)
        self.assertIsInstance(task, validation_animation.TaskValidationAnimation)
        self.assertEqual("Validation", task.category)
        self.assertEqual(validation_animation.SKELETON_NONE, task.settings["skeleton_source"])
        self.assertEqual("general", task.get_mode())
        self.assertEqual("{project-dir}/data/custom_skeleton.json", task.settings["custom_skeleton_path"])
        self.assertTrue(task.settings["summary_batch"])
        self.assertFalse(task.settings["graphs_per_file"])
        self.assertTrue(task.settings["graphs_only_on_failure"])
        self.assertEqual(validation_animation.DEFAULT_OUTPUT_PATH, task.settings["output_path"])

    def test_default_settings_validate(self):
        self.assertEqual([], self.create_task().validate(self.project).errors)

    def test_skeleton_choice_sets_the_mode(self):
        task = self.create_task(skeleton_source="unreal_mannequin")
        self.assertEqual([], task.validate(self.project).errors)
        self.assertEqual("biped", task.get_mode())
        self.assertEqual("biped", presets.resolve_preset(task.load_preset(self.project))["mode"])

    def test_no_skeleton_forces_general_checks(self):
        task = self.create_task(preset=presets.create_preset(mode="biped"))
        self.assertEqual("general", presets.resolve_preset(task.load_preset(self.project))["mode"])
        self.assertIsNone(task.load_skeleton_template(self.project))

    def test_missing_custom_skeleton_is_an_error(self):
        task = self.create_task(
            skeleton_source=validation_animation.SKELETON_CUSTOM,
            custom_skeleton_path=os.path.join(self.temp_dir.name, "missing.json"),
        )
        self.assertTrue(task.validate(self.project).errors)

    def test_legacy_general_settings_migrate_to_no_skeleton(self):
        task = batch_processor_tasks.create_task(
            constants.TaskType.ANIMATION_VALIDATE,
            settings={"template_source": "maya_humanik", "preset": presets.create_preset(mode="general")},
        )
        self.assertEqual(validation_animation.SKELETON_NONE, task.settings["skeleton_source"])
        self.assertNotIn("template_source", task.settings)

    def test_legacy_biped_file_settings_migrate_to_custom_skeleton(self):
        task = batch_processor_tasks.create_task(
            constants.TaskType.ANIMATION_VALIDATE,
            settings={
                "template_source": "file",
                "template_path": "{project-dir}/templates/rig.json",
                "preset": presets.create_preset(mode="biped"),
            },
        )
        self.assertEqual(validation_animation.SKELETON_CUSTOM, task.settings["skeleton_source"])
        self.assertEqual("{project-dir}/templates/rig.json", task.settings["custom_skeleton_path"])

    def get_output_dir(self):
        """Gets an absolute output folder inside the temporary project.

        Returns:
            str: Output folder path.
        """
        return os.path.join(self.temp_dir.name, "output").replace("\\", "/")

    def test_graphs_are_skipped_unless_failed(self):
        task = self.create_task(graphs_per_file=True, summary_batch=False, output_path=self.get_output_dir())
        work_item = task_base.WorkItem(source_path=self.input_path)
        self.assertEqual([], task.write_file_outputs(self.project, work_item, build_report(70, "warning")))

    def test_outputs_skip_relative_folders(self):
        task = self.create_task(output_path="relative/output")
        work_item = task_base.WorkItem(source_path=self.input_path)
        self.assertEqual([], task.write_outputs(self.project, work_item, build_report(10, "failed")))
        self.assertFalse(os.path.exists(os.path.join(os.getcwd(), "relative", "output")))

    def test_legacy_graph_settings_migrate_to_output(self):
        task = batch_processor_tasks.create_task(
            constants.TaskType.ANIMATION_VALIDATE,
            settings={"export_graphs": True, "graphs_path": "D:/graphs", "graphs_only_on_failure": False},
        )
        self.assertTrue(task.settings["graphs_per_file"])
        self.assertEqual("D:/graphs", task.settings["output_path"])
        self.assertNotIn("export_graphs", task.settings)
        self.assertNotIn("graphs_path", task.settings)

    def test_per_file_summary_and_report_are_written(self):
        task = self.create_task(summary_per_file=True, report_per_file=True, summary_batch=False,
                                output_path=self.get_output_dir())
        work_item = task_base.WorkItem(source_path=self.input_path)
        written = task.write_file_outputs(self.project, work_item, build_report(70, "warning"))
        self.assertEqual(["walk_summary.txt", "walk_report.json"], [os.path.basename(path) for path in written])
        with open(written[1], "r", encoding="utf-8") as file_stream:
            self.assertEqual(70, json.load(file_stream)["score"])

    def test_batch_outputs_combine_files_sorted_by_score(self):
        task = self.create_task(summary_batch=True, report_batch=True, output_path=self.get_output_dir())
        context = {"run_id": "run-a"}
        for file_name, score, status in (("good.ma", 95, "passed"), ("bad.ma", 20, "failed")):
            work_item = task_base.WorkItem(source_path=os.path.join(self.temp_dir.name, file_name))
            task.write_batch_outputs(self.project, work_item, build_report(score, status), context)
        with open(os.path.join(self.get_output_dir(), validation_animation.BATCH_REPORT_FILE_NAME), "r",
                  encoding="utf-8") as file_stream:
            batch_report = json.load(file_stream)
        self.assertEqual(["bad.ma", "good.ma"], [entry["name"] for entry in batch_report["files"]])
        self.assertEqual(1, batch_report["totals"]["statuses"]["failed"])
        with open(os.path.join(self.get_output_dir(), validation_animation.BATCH_SUMMARY_FILE_NAME), "r",
                  encoding="utf-8") as file_stream:
            summary = file_stream.read()
        self.assertLess(summary.index("bad.ma"), summary.index("good.ma"))

    def test_batch_outputs_ignore_parts_from_earlier_runs(self):
        output_dir = self.get_output_dir()
        old_task = self.create_task(report_batch=True, output_path=output_dir)
        old_item = task_base.WorkItem(source_path=os.path.join(self.temp_dir.name, "old.ma"))
        old_task.write_batch_outputs(self.project, old_item, build_report(50, "warning"), {"run_id": "run-old"})
        task = self.create_task(report_batch=True, output_path=output_dir)
        task.id = old_task.id
        work_item = task_base.WorkItem(source_path=self.input_path)
        task.write_batch_outputs(self.project, work_item, build_report(90, "passed"), {"run_id": "run-new"})
        with open(os.path.join(output_dir, validation_animation.BATCH_REPORT_FILE_NAME), "r",
                  encoding="utf-8") as file_stream:
            self.assertEqual(["walk.ma"], [entry["name"] for entry in json.load(file_stream)["files"]])

    def test_file_folders_off_writes_into_the_output_folder(self):
        task = self.create_task(summary_per_file=True, summary_batch=False, file_folders=False,
                                output_path=self.get_output_dir())
        work_item = task_base.WorkItem(source_path=self.input_path)
        written = task.write_file_outputs(self.project, work_item, build_report(70, "warning"))
        self.assertEqual(os.path.normcase(self.get_output_dir()), os.path.normcase(os.path.dirname(written[0])))

    def test_parts_live_in_the_log_folder_and_are_deleted_on_the_last_item(self):
        task = self.create_task(summary_batch=True, output_path=self.get_output_dir())
        parts_dir = task.get_parts_dir(self.log_dir)
        work_item = task_base.WorkItem(source_path=self.input_path)
        task.write_batch_outputs(self.project, work_item, build_report(90, "passed"), {"run_id": "run-a"},
                                 step_output_dir=self.log_dir)
        self.assertTrue(os.path.isdir(parts_dir))
        self.assertFalse(os.path.isdir(os.path.join(self.get_output_dir(), "_parts")))
        context = {"run_id": "run-a", "is_last_item": True, "cleanup_report_parts": True}
        task.write_batch_outputs(self.project, work_item, build_report(90, "passed"), context,
                                 step_output_dir=self.log_dir)
        self.assertFalse(os.path.isdir(parts_dir))

    def test_parts_are_kept_when_delete_is_off(self):
        task = self.create_task(summary_batch=True, delete_parts=False, output_path=self.get_output_dir())
        work_item = task_base.WorkItem(source_path=self.input_path)
        context = {"run_id": "run-a", "is_last_item": True, "cleanup_report_parts": True}
        task.write_batch_outputs(self.project, work_item, build_report(90, "passed"), context,
                                 step_output_dir=self.log_dir)
        self.assertTrue(os.path.isdir(task.get_parts_dir(self.log_dir)))

    def test_empty_post_script_is_an_error(self):
        task = self.create_task(run_post_script=True, post_script_text="")
        self.assertTrue(task.validate(self.project).errors)

    def test_unsaved_score_is_a_warning(self):
        task = self.create_task(write_score=True, save_scene=False)
        self.assertTrue(task.validate(self.project).warnings)

    def test_preset_file_is_loaded(self):
        preset_path = os.path.join(self.temp_dir.name, "preset.json")
        presets.save_preset(presets.set_global_value(presets.create_preset(), "overall_fail_below", 10), preset_path)
        task = self.create_task(preset_source=validation_animation.PRESET_SOURCE_FILE, preset_path=preset_path)
        self.assertEqual({"overall_fail_below": 10}, task.load_preset(self.project)["settings"])

    def test_source_discovery_keeps_only_animation_files(self):
        source_dir = os.path.join(self.temp_dir.name, "usd_exports")
        os.makedirs(source_dir)
        for name in ("walk.usd", "run.usda", "jump.usdc", "idle.fbx", "report.txt", "notes.json"):
            with open(os.path.join(source_dir, name), "w", encoding="utf-8") as file_stream:
                file_stream.write("")
        task = self.create_task(source_mode="source_path", source_path=source_dir.replace("\\", "/"))
        found = [os.path.basename(path) for path in task.discover_source_files(self.project)]
        self.assertEqual(["idle.fbx", "jump.usdc", "run.usda", "walk.usd"], sorted(found))

    def test_name_filters_are_off_by_default(self):
        task = self.create_task()
        self.assertFalse(task.settings.get("filter_enabled"))
        self.assertTrue(task.passes_name_filters("C:/data/anything.usd"))

    def test_name_filters_include_and_exclude(self):
        source_dir = os.path.join(self.temp_dir.name, "filtered")
        os.makedirs(source_dir)
        for name in ("Blue_Fox_010.usd", "blue_fox_020.usd", "blue_fox_020_backup.usd", "idle_001.usd"):
            with open(os.path.join(source_dir, name), "w", encoding="utf-8") as file_stream:
                file_stream.write("")
        task = self.create_task(source_mode="source_path", source_path=source_dir.replace("\\", "/"),
                                filter_enabled=True, filter_include_patterns="blue_fox",
                                filter_exclude_patterns="*_backup*")
        found = [os.path.basename(path) for path in task.discover_source_files(self.project)]
        self.assertEqual(["Blue_Fox_010.usd", "blue_fox_020.usd"], sorted(found))

    def test_parse_name_patterns_wraps_plain_text(self):
        expected = ["*blue_fox*", "idle_*.usd", "*take*"]
        self.assertEqual(expected, validation_animation.parse_name_patterns("Blue_Fox, idle_*.usd; take"))

    def test_filtered_incoming_file_is_skipped(self):
        task = self.create_task(load_scene=True, filter_enabled=True, filter_exclude_patterns="walk")
        usd_path = os.path.join(self.temp_dir.name, "walk.usd")
        with patch.object(validation_animation.usd_scene, "load_usd_scene") as load_usd:
            with self.assertRaises(task_base.TaskSkip):
                task.execute(task_base.WorkItem(source_path=usd_path), self.project, self.log_dir, context={})
        load_usd.assert_not_called()

    def test_unsupported_incoming_file_is_skipped(self):
        task = self.create_task(load_scene=True)
        text_path = os.path.join(self.temp_dir.name, "report.txt")
        with open(text_path, "w", encoding="utf-8") as file_stream:
            file_stream.write("")
        with self.assertRaises(task_base.TaskSkip):
            task.execute(task_base.WorkItem(source_path=text_path), self.project, self.log_dir, context={})

    def test_usd_files_load_with_up_axis_alignment(self):
        task = self.create_task(load_scene=True, align_up_axis=False)
        usd_path = os.path.join(self.temp_dir.name, "walk.usd")
        with patch.object(validation_animation.usd_scene, "load_usd_scene") as load_usd, \
                patch.object(validation_animation.batch_processor_maya, "load_relevant_file_plugin"), \
                patch.object(validation_animation.task_utils, "load_source_scene") as load_maya:
            task.load_scene(usd_path)
        load_usd.assert_called_once_with(usd_path, align_up_axis=False)
        load_maya.assert_not_called()

    def test_maya_scenes_use_the_scene_load_settings(self):
        task = self.create_task(load_scene=True, source_load_mode="Import")
        with patch.object(validation_animation.usd_scene, "load_usd_scene") as load_usd, \
                patch.object(validation_animation.task_utils, "load_source_scene") as load_maya:
            task.load_scene(self.input_path)
        load_maya.assert_called_once_with(self.input_path, source_load_mode="Import", load_relevant_plugins=True)
        load_usd.assert_not_called()

    def test_task_can_run_once_before_jobs(self):
        task = self.create_task(run_once_before_multi_instance=True)
        self.assertTrue(task.supports_run_once_before_jobs)
        self.assertFalse(task.get_default_settings()["run_once_before_multi_instance"])
        self.assertTrue(task.get_default_settings()["align_up_axis"])

    def test_run_once_only_project_does_not_warn_about_inputs(self):
        task = self.create_task(run_once_after_multi_instance=True, source_mode="source_path",
                                source_path=self.temp_dir.name.replace("\\", "/"))
        self.project.tasks = [task]
        warnings = self.project.validate_project().warnings
        self.assertNotIn("Project has no enabled input tasks.", warnings)
        task.settings["run_once_after_multi_instance"] = False
        self.assertIn("Project has no enabled input tasks.", self.project.validate_project().warnings)

    def test_passed_item_is_logged(self):
        task = self.create_task()
        result = self.execute(task, build_report(97, "passed"))
        self.assertEqual(self.input_path, result.current_path)
        entry = self.read_log()["entries"][0]
        self.assertEqual(97, entry["score"])
        self.assertFalse(entry["has_issues"])

    def test_failed_item_raises_when_configured(self):
        task = self.create_task()
        with self.assertRaises(RuntimeError):
            self.execute(task, build_report(20, "failed"))
        self.assertEqual("failed", self.read_log()["entries"][0]["status"])

    def test_failed_item_passes_through_when_allowed(self):
        task = self.create_task(fail_on_failed=False)
        result = self.execute(task, build_report(20, "failed"))
        self.assertEqual(self.input_path, result.current_path)

    def test_warning_is_reported(self):
        warnings = []
        task = self.create_task()
        self.execute(task, build_report(70, "warning"), context={"report_warning": warnings.append})
        self.assertEqual(1, len(warnings))

    def test_evaluation_error_skips_when_fail_on_error_is_off(self):
        task = self.create_task(fail_on_error=False)
        work_item = task_base.WorkItem(source_path=self.input_path)
        with patch.object(task, "evaluate_current_scene", side_effect=ValueError("missing roles")):
            with self.assertRaises(task_base.TaskSkip):
                task.execute(work_item, self.project, self.log_dir, context={})

    def test_post_script_receives_score(self):
        output_path = os.path.join(self.temp_dir.name, "score.txt").replace("\\", "/")
        script = f"with open(r'{output_path}', 'w') as stream:\n    stream.write(str(score) + status)"
        task = self.create_task(run_post_script=True, post_script_text=script)
        self.execute(task, build_report(88, "passed"))
        with open(output_path, "r", encoding="utf-8") as file_stream:
            self.assertEqual("88passed", file_stream.read())

    def test_save_refuses_to_overwrite_original_input(self):
        task = self.create_task(save_scene=True)
        written = dict(NO_WRITE, written=True)
        with self.assertRaises(RuntimeError):
            self.execute(task, build_report(90, "passed"), write_outcome=written)

    def test_save_is_skipped_when_nothing_changed(self):
        task = self.create_task(save_scene=True)
        work_item = task_base.WorkItem(source_path=self.input_path)
        self.assertEqual("", task.save_scene_if_needed(work_item, scene_changed=False))

    def test_sample_scripts_compile(self):
        samples = task_utils.get_script_samples(validation_animation.POST_SCRIPT_SAMPLES_DIRECTORY)
        self.assertGreaterEqual(len(samples), 2)
        for sample in samples:
            compile(task_utils.load_script_file(sample["path"]), sample["path"], "exec")


if __name__ == "__main__":
    unittest.main()
