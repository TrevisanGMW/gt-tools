import logging
import contextlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
import zipfile
from unittest import mock

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Scripts
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_model
from gt.tools.batch_processor import batch_processor_modules as modules
from gt.tools.batch_processor import batch_processor_templates
from gt.tools.batch_processor import batch_processor_tracker
from gt.tools.batch_processor import batch_processor_worker
from gt.tools.batch_processor.tracker import tracker_events
from gt.tools.batch_processor.tracker import tracker_worker as batch_processor_multi_worker
from gt.tools.batch_processor.tasks import task_utils
import gt.utils.usd as utils_usd


class TestBatchProcessorModel(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="gt_batch_processor_test_")

    def tearDown(self):
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_project_save_load_round_trip(self):
        model = batch_processor_model.BatchProcessorModel()
        model.project_name = "Unit Test Batch"
        model.run_settings["create_task_time_log"] = False
        model.add_module(modules.TaskRename(settings={"pattern": "asset_{index}", "padding": 2}))
        project_path = os.path.join(self.temp_dir, "test_project.batch")

        saved_path = model.save_to_file(project_path)
        loaded_model = batch_processor_model.BatchProcessorModel.from_file(saved_path)

        expected = "Unit Test Batch"
        self.assertEqual(expected, loaded_model.project_name)
        expected = 2
        self.assertEqual(expected, len(loaded_model.modules))
        expected = constants.ModuleType.RENAME
        self.assertEqual(expected, loaded_model.modules[1].module_type)
        expected = "asset_{index}"
        self.assertEqual(expected, loaded_model.modules[1].settings.get("pattern"))
        self.assertFalse(loaded_model.run_settings.get("create_task_time_log"))

    def test_project_save_uses_tasks_key(self):
        model = batch_processor_model.BatchProcessorModel()
        model.add_task(modules.TaskRename())
        project_path = os.path.join(self.temp_dir, "test_project.batch")

        saved_path = model.save_to_file(project_path)
        with open(saved_path, "r", encoding="utf-8") as project_file:
            result = json.load(project_file)

        self.assertIn("tasks", result)
        self.assertNotIn("modules", result)
        self.assertIn("environment_variables", result)
        self.assertNotIn("paths", result)
        self.assertIn("parameters", result["tasks"][0])
        self.assertNotIn("settings", result["tasks"][0])

    def test_project_reads_legacy_modules_key(self):
        project_path = os.path.join(self.temp_dir, "legacy_project.batch")
        legacy_data = {
            "version": 1,
            "project_name": "Legacy",
            "paths": {},
            "run_settings": {},
            "modules": [
                modules.TaskInput().to_dict(),
                modules.TaskRename(settings={"pattern": "legacy_{index}"}).to_dict(),
            ],
        }
        with open(project_path, "w", encoding="utf-8") as project_file:
            json.dump(legacy_data, project_file)

        result = batch_processor_model.BatchProcessorModel.from_file(project_path)

        expected = 2
        self.assertEqual(expected, len(result.tasks))
        expected = "legacy_{index}"
        self.assertEqual(expected, result.tasks[1].settings.get("pattern"))

    def test_project_drops_legacy_force_recook_setting(self):
        model = batch_processor_model.BatchProcessorModel()
        data = model.to_dict()
        data["run_settings"]["force_recook"] = True

        model.read_data_from_dict(data)

        self.assertNotIn("force_recook", model.run_settings)
        self.assertIn("create_log", model.run_settings)
        self.assertTrue(model.run_settings.get("create_task_time_log"))

    def test_batch_processor_templates_load_file_templates(self):
        template_dir = os.path.join(self.temp_dir, "batch_processor_templates")
        os.makedirs(template_dir)
        template_path = os.path.join(template_dir, "FbxToMaya.batch")
        template_data = batch_processor_model.BatchProcessorModel().to_dict()
        template_data["project_name"] = "FBX To Maya"
        template_data["tasks"].append(modules.TaskMayaImport().to_dict())
        with open(template_path, "w", encoding="utf-8") as template_file:
            json.dump(template_data, template_file)

        original_template_source_dir = batch_processor_templates.TEMPLATE_SOURCE_DIR
        batch_processor_templates.TEMPLATE_SOURCE_DIR = template_dir
        try:
            templates = batch_processor_templates.BatchProcessorTemplates()
            template_dict = templates.get_dict_templates()
        finally:
            batch_processor_templates.TEMPLATE_SOURCE_DIR = original_template_source_dir

        self.assertIn("FbxToMaya", template_dict)
        result = template_dict["FbxToMaya"]()

        expected = "FBX To Maya"
        self.assertEqual(expected, result.project_name)
        expected = constants.TaskType.MAYA_IMPORT
        self.assertEqual(expected, result.tasks[1].task_type)

    def test_input_module_discovers_extension_filtered_files(self):
        input_dir = os.path.join(self.temp_dir, "input")
        nested_dir = os.path.join(input_dir, "nested")
        os.makedirs(nested_dir)
        self._write_file(os.path.join(input_dir, "a.ma"), "maya")
        self._write_file(os.path.join(input_dir, "b.fbx"), "fbx")
        self._write_file(os.path.join(input_dir, "c.txt"), "text")
        self._write_file(os.path.join(nested_dir, "d.ma"), "maya")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        input_module = model.get_input_module()
        input_module.settings["input_dir"] = input_dir
        input_module.settings["extensions"] = [".ma"]
        input_module.settings["include_subdirectories"] = False

        result = [os.path.basename(path) for path in input_module.discover_files(model)]
        expected = ["a.ma"]
        self.assertEqual(expected, result)

        input_module.settings["include_subdirectories"] = True
        result = [os.path.basename(path) for path in input_module.discover_files(model)]
        expected = ["a.ma", "d.ma"]
        self.assertEqual(expected, result)

    def test_input_module_resolves_explicit_names_patterns_and_templates(self):
        input_dir = os.path.join(self.temp_dir, "input")
        nested_dir = os.path.join(input_dir, "nested")
        os.makedirs(nested_dir)
        self._write_file(os.path.join(input_dir, "hero.ma"), "maya")
        self._write_file(os.path.join(input_dir, "source.fbx"), "fbx")
        self._write_file(os.path.join(nested_dir, "walk.ma"), "maya")
        self._write_file(os.path.join(input_dir, "notes.txt"), "text")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        input_module = model.get_input_module()
        input_module.settings["input_dir"] = input_dir
        input_module.settings["extensions"] = [".ma", ".fbx"]
        input_module.settings["explicit_files"] = [
            "hero.ma",
            "nested/*.ma",
            "{project-dir}/input/source.fbx",
            "notes.txt",
        ]

        result = [os.path.basename(path) for path in input_module.discover_files(model)]
        expected = ["hero.ma", "walk.ma", "source.fbx"]
        self.assertEqual(expected, result)

    def test_input_module_drops_retired_explicit_ignore_setting(self):
        input_module = modules.TaskInput(
            settings={"explicit_ignore_patterns": ["*_preview.ma"]},
        )

        self.assertNotIn("explicit_ignore_patterns", input_module.settings)
        self.assertNotIn("explicit_ignore_patterns", input_module.to_dict().get("parameters"))

    def test_input_module_reports_folder_statistics(self):
        input_dir = os.path.join(self.temp_dir, "input")
        os.makedirs(input_dir)
        self._write_file(os.path.join(input_dir, "a.ma"), "maya")
        self._write_file(os.path.join(input_dir, "b.fbx"), "fbx")
        self._write_file(os.path.join(input_dir, "c.txt"), "text")

        model = batch_processor_model.BatchProcessorModel()
        input_module = model.get_input_module()
        input_module.settings["input_dir"] = input_dir
        input_module.settings["extensions"] = [".ma", ".fbx"]

        result = input_module.get_file_statistics(model)

        expected = 2
        self.assertEqual(expected, result.get("resolved_count"))
        expected = 3
        self.assertEqual(expected, result.get("total_count"))
        expected = 3
        self.assertEqual(expected, result.get("file_type_count"))
        expected = 2
        self.assertEqual(expected, result.get("input_type_count"))
        self.assertIn(".txt", result.get("extension_counts"))
        self.assertNotIn(".txt", result.get("resolved_extension_counts"))

    def test_input_work_items_preserve_source_relative_metadata(self):
        input_dir = os.path.join(self.temp_dir, "input")
        nested_dir = os.path.join(input_dir, "characters", "hero")
        os.makedirs(nested_dir)
        source_path = os.path.join(nested_dir, "walk.ma")
        self._write_file(source_path, "maya")
        model = batch_processor_model.BatchProcessorModel()
        input_module = model.get_input_module()
        input_module.settings["input_dir"] = input_dir
        input_module.settings["extensions"] = [".ma"]

        result = input_module.prepare(model)

        expected = 1
        self.assertEqual(expected, len(result))
        expected = "characters/hero/walk.ma"
        self.assertEqual(expected, modules.get_work_item_relative_path(result[0]))
        expected = "characters/hero"
        self.assertEqual(expected, modules.get_work_item_relative_dir(result[0]))

    def test_task_output_paths_preserve_source_relative_folder(self):
        input_dir = os.path.join(self.temp_dir, "input")
        source_path = os.path.join(input_dir, "characters", "hero", "walk.fbx")
        work_item = modules.WorkItem(source_path=source_path, source_root=input_dir)
        step_output_dir = os.path.join(self.temp_dir, "02_tasks", "01_python")
        python_task = modules.TaskPythonScript()
        usd_task = modules.TaskExportUsd()
        rename_task = modules.TaskRename(settings={"pattern": "renamed_{index}", "padding": 2})

        result = python_task.build_output_path(work_item, step_output_dir)
        expected = os.path.join(step_output_dir, "characters", "hero", "walk.ma")
        self.assertEqual(os.path.normpath(expected), result)

        result = usd_task.build_output_path(work_item, step_output_dir)
        expected = os.path.join(step_output_dir, "characters", "hero", "walk.usd")
        self.assertEqual(os.path.normpath(expected), result)

        result = rename_task.build_output_path(work_item, 1, step_output_dir)
        expected = os.path.join(step_output_dir, "characters", "hero", "renamed_01.fbx")
        self.assertEqual(os.path.normpath(expected), result)

    def test_python_task_modify_mode_uses_current_file_as_output(self):
        source_path = os.path.join(self.temp_dir, "02_tasks", "01_python", "walk.ma")
        work_item = modules.WorkItem(source_path=source_path)
        step_output_dir = os.path.join(self.temp_dir, "02_tasks", "02_python")
        python_task = modules.TaskPythonScript(
            settings={"output_mode": modules.OUTPUT_MODE_MODIFY}
        )

        result = python_task.build_output_path(work_item, step_output_dir)

        self.assertEqual(os.path.normpath(source_path), result)

    def test_python_task_modify_mode_executes_when_current_file_exists(self):
        source_path = os.path.join(self.temp_dir, "walk.ma")
        self._write_file(source_path, "maya scene")
        work_item = modules.WorkItem(source_path=source_path)
        python_task = modules.TaskPythonScript(
            settings={
                "output_mode": modules.OUTPUT_MODE_MODIFY,
                "script_text": "context['script_ran'] = True",
            }
        )
        project = batch_processor_model.BatchProcessorModel()

        with mock.patch.object(python_task, "load_source_scene") as mock_load_scene:
            with mock.patch.object(python_task, "run_inline_python_script") as mock_run_script:
                with mock.patch.object(batch_processor_maya, "save_scene") as mock_save_scene:
                    result = python_task.execute(work_item, project, self.temp_dir)

        self.assertEqual(os.path.normpath(source_path), result.current_path)
        mock_load_scene.assert_called_once_with(source_path)
        mock_run_script.assert_called_once()
        mock_save_scene.assert_called_once_with(source_path, file_type="mayaAscii")

    def test_python_task_modify_mode_rejects_non_maya_scene_files(self):
        source_path = os.path.join(self.temp_dir, "walk.fbx")
        work_item = modules.WorkItem(source_path=source_path)
        python_task = modules.TaskPythonScript(
            settings={"output_mode": modules.OUTPUT_MODE_MODIFY}
        )

        result = python_task.validate_work_items([work_item], None, self.temp_dir)

        self.assertFalse(result.is_valid())
        self.assertTrue(any("only modify Maya scene files" in error for error in result.errors))

    def test_environment_variable_template_resolution(self):
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        model.environment_variables["task-dir"] = "custom_tasks"
        rename_task = modules.TaskRename()
        model.add_task(rename_task)

        result = rename_task.resolve_task_path(model, task_index=2)
        expected = os.path.join(self.temp_dir, "custom_tasks", "02_rename")
        self.assertEqual(os.path.normpath(expected), result)

    def test_environment_variables_include_task_dependent_neighbors(self):
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        rename_task = model.add_task(modules.TaskRename())
        python_task = model.add_task(modules.TaskPythonScript())
        save_task = model.add_task(modules.TaskMayaSave())

        result = model.get_environment_variables(task=save_task, include_braces=True)

        self.assertIn("{previous-task-path}", result)
        self.assertIn("{previous-previous-task-path}", result)
        self.assertIn("{pre-previous-task-path}", result)
        self.assertIn("{previous-previous-task-name}", result)
        self.assertIn("{previous-previous-task-index}", result)
        expected = python_task.resolve_task_path(model, task_index=2)
        self.assertEqual(os.path.normpath(expected), result.get("{previous-task-path}"))
        expected = rename_task.resolve_task_path(model, task_index=1)
        self.assertEqual(os.path.normpath(expected), result.get("{previous-previous-task-path}"))
        self.assertEqual(result.get("{previous-previous-task-path}"), result.get("{pre-previous-task-path}"))
        expected = rename_task.display_name
        self.assertEqual(expected, result.get("{previous-previous-task-name}"))
        expected = "1"
        self.assertEqual(expected, result.get("{previous-previous-task-index}"))

    def test_environment_variables_menu_uses_selected_task_context(self):
        controller_path = os.path.join(
            package_root_dir,
            "tools",
            "batch_processor",
            "batch_processor_controller.py",
        )
        with open(controller_path, "r", encoding="utf-8") as controller_file:
            controller_source = controller_file.read()

        self.assertIn("self.view.get_selected_task_id()", controller_source)
        self.assertIn("task=task", controller_source)
        self.assertIn("task_index=task_index", controller_source)

    def test_unset_project_dir_does_not_resolve_against_current_working_directory(self):
        model = batch_processor_model.BatchProcessorModel()

        result = model.get_project_dir()

        expected = ""
        self.assertEqual(expected, result)

        result = model.resolve_template_path("{project-dir}/{input-dir}")

        expected = ""
        self.assertEqual(expected, result)

        result = model.resolve_template_path("logs")

        expected = ""
        self.assertEqual(expected, result)

    def test_blank_project_dir_uses_project_file_directory_when_available(self):
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")

        result = model.resolve_template_path("{project-dir}/{input-dir}")

        expected = os.path.join(self.temp_dir, "01_input")
        self.assertEqual(os.path.normpath(expected), result)

    def test_task_environment_index_ignores_input_tasks_by_default(self):
        model = batch_processor_model.BatchProcessorModel()
        rename_task = model.add_task(modules.TaskRename())

        result = model.get_task_environment_index(rename_task)

        expected = 1
        self.assertEqual(expected, result)

        result = model.get_task_environment_index(model.tasks[0])

        expected = 0
        self.assertEqual(expected, result)

    def test_duplicate_task_inserts_after_source_with_new_id(self):
        model = batch_processor_model.BatchProcessorModel()
        rename_task = model.add_task(modules.TaskRename(settings={"pattern": "asset_{index}"}))

        result = model.duplicate_task(rename_task.id)

        expected = 3
        self.assertEqual(expected, len(model.tasks))
        self.assertNotEqual(rename_task.id, result.id)
        expected = "asset_{index}"
        self.assertEqual(expected, result.settings.get("pattern"))
        expected = result
        self.assertEqual(expected, model.tasks[2])

    def test_task_environment_index_can_include_input_task_when_checked(self):
        model = batch_processor_model.BatchProcessorModel()
        input_task = model.get_input_task()
        input_task.settings["include_in_task_index"] = True
        rename_task = model.add_task(modules.TaskRename())

        result = model.get_task_environment_index(input_task)

        expected = 1
        self.assertEqual(expected, result)

        result = model.get_task_environment_index(rename_task)

        expected = 2
        self.assertEqual(expected, result)

    def test_task_environment_index_uses_enabled_only_when_requested(self):
        model = batch_processor_model.BatchProcessorModel()
        disabled_task = model.add_task(modules.TaskRename())
        disabled_task.enabled = False
        rename_task = model.add_task(modules.TaskRename())

        result = model.get_task_environment_index(rename_task)

        expected = 2
        self.assertEqual(expected, result)

        result = model.get_task_environment_index(rename_task, enabled_only=True)

        expected = 1
        self.assertEqual(expected, result)

    def test_task_environment_index_automation_controls_disabled_tasks(self):
        model = batch_processor_model.BatchProcessorModel()
        disabled_import_task = model.add_task(modules.TaskMayaImport())
        disabled_import_task.enabled = False
        hik_task = model.add_task(modules.create_task(constants.TaskType.HIK_RETARGET))

        result = model.get_task_environment_index(hik_task)

        expected = 2
        self.assertEqual(expected, result)
        expected = "02"
        self.assertEqual(
            expected,
            model.get_environment_variables(task=hik_task, include_braces=False).get("task-idx"),
        )

        model.run_settings["ignore_disabled_tasks_for_task_index"] = True
        result = model.get_task_environment_index(hik_task)

        expected = 1
        self.assertEqual(expected, result)
        expected = "01"
        self.assertEqual(
            expected,
            model.get_environment_variables(task=hik_task, include_braces=False).get("task-idx"),
        )

    def test_task_environment_index_automation_is_saved_with_project(self):
        model = batch_processor_model.BatchProcessorModel()
        model.run_settings["ignore_disabled_tasks_for_task_index"] = True
        project_path = os.path.join(self.temp_dir, "task_index_automation.batch")

        saved_path = model.save_to_file(project_path)
        loaded_model = batch_processor_model.BatchProcessorModel.from_file(saved_path)

        expected = True
        self.assertEqual(expected, loaded_model.run_settings.get("ignore_disabled_tasks_for_task_index"))

    def test_task_environment_index_excludes_unchecked_output_and_delete_tasks(self):
        model = batch_processor_model.BatchProcessorModel()
        output_task = model.add_task(modules.TaskMayaSave())
        delete_task = model.add_task(modules.TaskDeleteProjectFiles())
        rename_task = model.add_task(modules.TaskRename())

        result = model.get_task_environment_index(rename_task)

        expected = 3
        self.assertEqual(expected, result)

        output_task.settings["include_in_task_index"] = False
        delete_task.settings["include_in_task_index"] = False
        result = model.get_task_environment_index(rename_task)

        expected = 1
        self.assertEqual(expected, result)

        result = model.get_task_environment_index(delete_task)

        expected = 0
        self.assertEqual(expected, result)

    def test_task_environment_index_excludes_unchecked_data_load_tasks(self):
        model = batch_processor_model.BatchProcessorModel()
        clip_task = model.add_task(modules.TaskClipSnapshot())
        map_task = model.add_task(modules.TaskMapHierarchy())
        rename_task = model.add_task(modules.TaskRename())

        # Data-load tasks are excluded from the task index by default.
        result = model.get_task_environment_index(rename_task)

        expected = 1
        self.assertEqual(expected, result)

        # Enabling the data-load tasks in the index makes them count.
        clip_task.settings["include_in_task_index"] = True
        map_task.settings["include_in_task_index"] = True
        result = model.get_task_environment_index(rename_task)

        expected = 3
        self.assertEqual(expected, result)

        result = model.get_task_environment_index(clip_task)

        expected = 1
        self.assertEqual(expected, result)
        self.assertTrue(getattr(map_task, "is_data_load_task", False))

    def test_validation_tasks_do_not_count_by_default(self):
        model = batch_processor_model.BatchProcessorModel()
        validation_task = model.add_task(modules.TaskValidationMayaScene())
        rename_task = model.add_task(modules.TaskRename())

        result = model.get_task_environment_index(validation_task)

        expected = 0
        self.assertEqual(expected, result)

        result = model.get_task_environment_index(rename_task)

        expected = 1
        self.assertEqual(expected, result)

    def test_task_index_participation_saves_with_task_parameters(self):
        model = batch_processor_model.BatchProcessorModel()
        rename_task = model.add_task(modules.TaskRename())
        rename_task.settings["include_in_task_index"] = False
        project_path = os.path.join(self.temp_dir, "test_project.batch")

        saved_path = model.save_to_file(project_path)
        loaded_model = batch_processor_model.BatchProcessorModel.from_file(saved_path)

        expected = False
        self.assertEqual(expected, loaded_model.tasks[1].settings.get("include_in_task_index"))
        expected = 0
        self.assertEqual(expected, loaded_model.get_task_environment_index(loaded_model.tasks[1]))

    def test_project_drops_obsolete_task_index_run_settings(self):
        model = batch_processor_model.BatchProcessorModel()
        data = model.to_dict()
        data["run_settings"]["ignore_input_tasks_for_task_index"] = False
        data["run_settings"]["ignore_output_tasks_for_task_index"] = True

        model.read_data_from_dict(data)

        self.assertNotIn("ignore_input_tasks_for_task_index", model.run_settings)
        self.assertNotIn("ignore_output_tasks_for_task_index", model.run_settings)

    def test_project_resolves_log_directory(self):
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")

        result = model.get_logs_dir()

        expected = os.path.join(self.temp_dir, "logs")
        self.assertEqual(os.path.normpath(expected), result)

    def test_project_path_environment_variables(self):
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")

        result = model.get_environment_variables(include_braces=False)

        expected = model.project_file_path
        self.assertEqual(os.path.normpath(expected), result.get("project-path"))
        expected = os.path.dirname(self.temp_dir)
        self.assertEqual(os.path.normpath(expected), result.get("project-parent-dir"))
        expected = os.path.dirname(os.path.dirname(self.temp_dir))
        self.assertEqual(os.path.normpath(expected), result.get("project-grandparent-dir"))

    def test_input_module_exclude_patterns(self):
        input_dir = os.path.join(self.temp_dir, "input")
        os.makedirs(input_dir)
        self._write_file(os.path.join(input_dir, "keep.ma"), "maya")
        self._write_file(os.path.join(input_dir, "skip_tmp.ma"), "maya")

        model = batch_processor_model.BatchProcessorModel()
        input_module = model.get_input_module()
        input_module.settings["input_dir"] = input_dir
        input_module.settings["extensions"] = ["ma"]
        input_module.settings["exclude_patterns"] = ["*_tmp.ma"]

        result = [os.path.basename(path) for path in input_module.discover_files(model)]
        expected = ["keep.ma"]
        self.assertEqual(expected, result)

    def test_disabled_input_module_does_not_block_validation(self):
        model = batch_processor_model.BatchProcessorModel()
        input_module = model.get_input_module()
        input_module.enabled = False
        input_module.settings["input_path"] = os.path.join(self.temp_dir, "missing")

        result = model.validate_project()

        self.assertTrue(result.is_valid())

    def test_rename_module_detects_duplicate_outputs(self):
        rename_module = modules.TaskRename(settings={"pattern": "same", "preserve_extension": True})
        work_items = [
            modules.WorkItem(source_path=os.path.join(self.temp_dir, "a.ma")),
            modules.WorkItem(source_path=os.path.join(self.temp_dir, "b.ma")),
        ]
        step_output_dir = os.path.join(self.temp_dir, "tasks", "01_rename")

        result = rename_module.validate_work_items(work_items, None, step_output_dir)

        self.assertFalse(result.is_valid())
        self.assertTrue(result.errors)

    def test_rename_module_validate_uses_context_item_index(self):
        rename_module = modules.TaskRename(
            settings={"pattern": "smoke_{index}", "padding": 2, "preserve_extension": True}
        )
        step_output_dir = os.path.join(self.temp_dir, "tasks", "01_rename")
        os.makedirs(step_output_dir)
        self._write_file(os.path.join(step_output_dir, "smoke_01.ma"), "existing")
        work_item = modules.WorkItem(source_path=os.path.join(self.temp_dir, "clip.ma"))

        result = rename_module.validate_work_items(
            [work_item],
            None,
            step_output_dir,
            context={"item_index": 2},
        )

        expected = []
        self.assertEqual(expected, result.warnings)

    def test_rename_module_rejects_unknown_token(self):
        rename_module = modules.TaskRename(settings={"pattern": "{name}_{missing}"})
        result = rename_module.validate(None)

        self.assertFalse(result.is_valid())
        self.assertTrue(result.errors)

    def test_rename_module_rejects_malformed_pattern(self):
        rename_module = modules.TaskRename(settings={"pattern": "{name"})
        result = rename_module.validate(None)

        self.assertFalse(result.is_valid())
        self.assertTrue(result.errors)

    def test_single_instance_runner_writes_cooked_task_outputs_only(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        input_dir = os.path.join(self.temp_dir, "01_input")
        os.makedirs(input_dir)
        self._write_file(os.path.join(input_dir, "clip.ma"), "maya scene")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        input_module = model.get_input_module()
        input_module.settings["input_dir"] = input_dir
        input_module.settings["extensions"] = [".ma"]
        model.add_module(modules.TaskRename(settings={"pattern": "renamed_{index}", "padding": 2}))

        runner = batch_processor_worker.SingleInstanceBatchRunner()
        tracker = runner.run(model)

        expected_cooked = os.path.join(self.temp_dir, "02_tasks", "01_rename", "renamed_01.ma")
        expected_output = os.path.join(self.temp_dir, "03_output", "renamed_01.ma")
        self.assertTrue(os.path.isfile(expected_cooked))
        self.assertFalse(os.path.isfile(expected_output))
        expected = 1
        self.assertEqual(expected, tracker.succeeded)
        expected = 0
        self.assertEqual(expected, tracker.failed)

    def test_single_instance_runner_preserves_nested_input_structure(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        input_dir = os.path.join(self.temp_dir, "01_input")
        nested_dir = os.path.join(input_dir, "characters", "hero")
        os.makedirs(nested_dir)
        self._write_file(os.path.join(nested_dir, "clip.ma"), "maya scene")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        input_module = model.get_input_module()
        input_module.settings["input_dir"] = input_dir
        input_module.settings["extensions"] = [".ma"]
        model.add_module(modules.TaskRename(settings={"pattern": "renamed_{index}", "padding": 2}))

        runner = batch_processor_worker.SingleInstanceBatchRunner()
        tracker = runner.run(model)

        expected_cooked = os.path.join(
            self.temp_dir,
            "02_tasks",
            "01_rename",
            "characters",
            "hero",
            "renamed_01.ma",
        )
        self.assertTrue(os.path.isfile(expected_cooked))
        expected = 1
        self.assertEqual(expected, tracker.succeeded)

    def test_single_instance_runner_skips_existing_outputs_when_overwrite_is_off(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        input_dir = os.path.join(self.temp_dir, "01_input")
        os.makedirs(input_dir)
        self._write_file(os.path.join(input_dir, "clip.ma"), "maya scene")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        input_module = model.get_input_module()
        input_module.settings["input_dir"] = input_dir
        input_module.settings["extensions"] = [".ma"]
        model.add_module(modules.TaskRename(settings={"pattern": "renamed_{index}", "padding": 2}))

        runner = batch_processor_worker.SingleInstanceBatchRunner()
        runner.run(model)
        runner = batch_processor_worker.SingleInstanceBatchRunner()
        tracker = runner.run(model)

        expected = 0
        self.assertEqual(expected, tracker.failed)
        expected = 1
        self.assertEqual(expected, tracker.skipped)

    def test_multi_instance_runner_launches_standalone_tracker(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        input_dir = os.path.join(self.temp_dir, "01_input")
        os.makedirs(input_dir)
        self._write_file(os.path.join(input_dir, "clip.ma"), "maya scene")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        model.run_settings["worker_count"] = 1
        captured_data = {}

        def fake_popen(command, *args, **kwargs):
            """Captures a Popen command without launching a tracker.

            Args:
                command (list): Command passed to Popen.
                *args: Positional arguments.
                **kwargs: Keyword arguments.

            Returns:
                object: Dummy process object.
            """
            captured_data["command"] = command
            captured_data["kwargs"] = kwargs
            return object()

        with mock.patch.object(batch_processor_worker, "find_mayapy_executable", return_value=sys.executable):
            with mock.patch.object(batch_processor_worker.subprocess, "Popen", side_effect=fake_popen):
                project_log_path = os.path.join(self.temp_dir, "project.log")
                runner = batch_processor_worker.MultiInstanceBatchRunner(project_log_path=project_log_path)
                runner.run(model)

        self.assertTrue(captured_data.get("command")[1].endswith("tracker_main.py"))
        self.assertIn("--task-time-logs", captured_data.get("command"))
        project_log_index = captured_data.get("command").index("--project-log")
        self.assertEqual(project_log_path, captured_data.get("command")[project_log_index + 1])
        source_project_index = captured_data.get("command").index("--source-project-file")
        self.assertEqual(project_path, captured_data.get("command")[source_project_index + 1])
        self.assertEqual(subprocess.DEVNULL, captured_data.get("kwargs").get("stdout"))

        model.run_settings["create_task_time_log"] = False
        captured_data.clear()
        with mock.patch.object(batch_processor_worker, "find_mayapy_executable", return_value=sys.executable):
            with mock.patch.object(batch_processor_worker.subprocess, "Popen", side_effect=fake_popen):
                runner = batch_processor_worker.MultiInstanceBatchRunner(flag_running_tasks=False)
                runner.run(model)

        self.assertNotIn("--task-time-logs", captured_data.get("command"))

    def test_multi_instance_runner_defers_run_once_zip_task(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        input_dir = os.path.join(self.temp_dir, "01_input")
        os.makedirs(input_dir)
        self._write_file(os.path.join(input_dir, "clip.ma"), "maya scene")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        zip_task = model.add_module(modules.create_task(constants.TaskType.ZIP_COMPRESS))
        zip_task.settings["run_once_after_multi_instance"] = True
        captured_data = {}

        def fake_popen(command, *args, **kwargs):
            """Captures the tracker command without launching it.

            Args:
                command (list): Command passed to Popen.
                *args: Positional arguments.
                **kwargs: Keyword arguments.

            Returns:
                object: Dummy process object.
            """
            captured_data["command"] = command
            return object()

        with mock.patch.object(batch_processor_worker, "find_mayapy_executable", return_value=sys.executable):
            with mock.patch.object(batch_processor_worker.subprocess, "Popen", side_effect=fake_popen):
                batch_processor_worker.MultiInstanceBatchRunner().run(model)

        command = captured_data.get("command")
        final_task_arg_index = command.index("--final-task-id")
        expected = zip_task.id
        self.assertEqual(expected, command[final_task_arg_index + 1])

    def test_multi_instance_runner_requires_run_once_zip_task_to_be_last(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        input_dir = os.path.join(self.temp_dir, "01_input")
        os.makedirs(input_dir)
        self._write_file(os.path.join(input_dir, "clip.ma"), "maya scene")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        zip_task = model.add_module(modules.create_task(constants.TaskType.ZIP_COMPRESS))
        zip_task.settings["run_once_after_multi_instance"] = True
        model.add_module(modules.create_task(constants.TaskType.RENAME))

        runner = batch_processor_worker.MultiInstanceBatchRunner()
        with self.assertRaisesRegex(RuntimeError, "must be the last enabled processing task"):
            runner.run(model)

    def test_single_instance_runner_writes_separate_task_timing_log(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        input_dir = os.path.join(self.temp_dir, "01_input")
        os.makedirs(input_dir)
        self._write_file(os.path.join(input_dir, "clip.ma"), "maya scene")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        model.add_module(modules.TaskRename(settings={"pattern": "timed_{index}"}))
        timing_log_path = os.path.join(self.temp_dir, "logs", "task_times.log")
        runner = batch_processor_worker.SingleInstanceBatchRunner(
            task_time_log_path=timing_log_path,
        )

        runner.run(model)

        with open(timing_log_path, "r", encoding="utf-8") as timing_log:
            result = timing_log.read()
        self.assertIn("Batch Processor Task Timing Log", result)
        self.assertIn("Input Files", result)
        self.assertIn("Rename", result)
        self.assertIn("seconds", result)

    def test_run_selected_uses_task_source_path(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        source_dir = os.path.join(self.temp_dir, "cache")
        os.makedirs(source_dir)
        self._write_file(os.path.join(source_dir, "clip.ma"), "maya scene")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        model.get_input_module().enabled = False
        rename_task = model.add_module(
            modules.TaskRename(
                settings={
                    "source_path": source_dir,
                    "pattern": "selected_{index}",
                    "padding": 2,
                }
            )
        )

        runner = batch_processor_worker.SingleInstanceBatchRunner()
        tracker = runner.run(model, run_from_task_id=rename_task.id)

        expected_cooked = os.path.join(self.temp_dir, "02_tasks", "01_rename", "selected_01.ma")
        self.assertTrue(os.path.isfile(expected_cooked))
        expected = 1
        self.assertEqual(expected, tracker.succeeded)

    def test_run_selected_preserves_task_source_folder_structure(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        source_dir = os.path.join(self.temp_dir, "cache")
        nested_dir = os.path.join(source_dir, "clips", "locomotion")
        os.makedirs(nested_dir)
        self._write_file(os.path.join(nested_dir, "clip.ma"), "maya scene")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        model.get_input_module().enabled = False
        rename_task = model.add_module(
            modules.TaskRename(
                settings={
                    "source_path": source_dir,
                    "source_include_subdirectories": True,
                    "pattern": "selected_{index}",
                    "padding": 2,
                }
            )
        )

        runner = batch_processor_worker.SingleInstanceBatchRunner()
        tracker = runner.run(model, run_from_task_id=rename_task.id)

        expected_cooked = os.path.join(
            self.temp_dir,
            "02_tasks",
            "01_rename",
            "clips",
            "locomotion",
            "selected_01.ma",
        )
        self.assertTrue(os.path.isfile(expected_cooked))
        expected = 1
        self.assertEqual(expected, tracker.succeeded)

    def test_source_path_discovers_previous_task_folder_files_before_using_incoming_items(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        clips_dir = os.path.join(self.temp_dir, "02_tasks", "01_clips")
        os.makedirs(clips_dir)
        self._write_file(os.path.join(clips_dir, "walk_clip.ma"), "maya scene")
        self._write_file(os.path.join(clips_dir, "run_clip.ma"), "maya scene")
        self._write_file(os.path.join(clips_dir, "jump_clip.ma"), "maya scene")
        original_file = os.path.join(self.temp_dir, "01_input", "source.ma")
        os.makedirs(os.path.dirname(original_file))
        self._write_file(original_file, "source scene")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        model.get_input_module().enabled = False
        clip_task = model.add_task(
            modules.TaskClipSplit(
                settings={
                    "target_path": clips_dir,
                }
            )
        )
        python_task = model.add_task(
            modules.TaskPythonScript(
                settings={
                    "source_path": "{previous-task-path}",
                }
            )
        )
        runner = batch_processor_worker.SingleInstanceBatchRunner()
        current_items = [modules.WorkItem(source_path=original_file)]
        task_index = model.get_task_environment_index(python_task, enabled_only=True)

        result = runner._get_task_source_items(
            project=model,
            task=python_task,
            task_index=task_index,
            current_items=current_items,
        )

        expected = ["jump_clip.ma", "run_clip.ma", "walk_clip.ma"]
        self.assertEqual(expected, sorted([os.path.basename(item.current_path) for item in result]))
        self.assertEqual(clip_task.resolve_task_path(model, task_index=1), clips_dir)

    def test_multi_worker_initial_work_item_restores_input_relative_metadata(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        input_dir = os.path.join(self.temp_dir, "01_input")
        nested_dir = os.path.join(input_dir, "characters", "hero")
        os.makedirs(nested_dir)
        source_path = os.path.join(nested_dir, "clip.ma")
        self._write_file(source_path, "maya scene")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        input_module = model.get_input_module()
        input_module.settings["input_dir"] = input_dir
        input_module.settings["extensions"] = [".ma"]

        result = batch_processor_worker.create_initial_work_item(project=model, source_file=source_path)

        expected = "characters/hero/clip.ma"
        self.assertEqual(expected, modules.get_work_item_relative_path(result))
        expected = "characters/hero"
        self.assertEqual(expected, modules.get_work_item_relative_dir(result))

    def test_incoming_source_uses_all_enabled_input_tasks(self):
        project_path = os.path.join(self.temp_dir, "project.batch")
        first_input_dir = os.path.join(self.temp_dir, "01_input")
        second_input_dir = os.path.join(self.temp_dir, "extra_input")
        os.makedirs(first_input_dir)
        os.makedirs(second_input_dir)
        self._write_file(os.path.join(first_input_dir, "first.ma"), "maya scene")
        self._write_file(os.path.join(second_input_dir, "second.ma"), "maya scene")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = project_path
        first_input_task = model.get_input_task()
        first_input_task.settings["input_dir"] = first_input_dir
        first_input_task.settings["extensions"] = [".ma"]
        second_input_task = model.add_module(
            modules.TaskInput(settings={"input_dir": second_input_dir, "extensions": [".ma"]})
        )
        rename_task = model.add_module(
            modules.TaskRename(
                settings={
                    "source_mode": modules.SOURCE_MODE_INCOMING,
                    "pattern": "incoming_{index}",
                    "padding": 2,
                }
            )
        )

        runner = batch_processor_worker.SingleInstanceBatchRunner()
        tracker = runner.run(model, run_from_task_id=rename_task.id)

        expected_first = os.path.join(self.temp_dir, "02_tasks", "01_rename", "incoming_01.ma")
        expected_second = os.path.join(self.temp_dir, "02_tasks", "01_rename", "incoming_02.ma")
        self.assertTrue(os.path.isfile(expected_first))
        self.assertTrue(os.path.isfile(expected_second))
        expected = 2
        self.assertEqual(expected, tracker.succeeded)
        self.assertEqual(constants.TaskType.INPUT, second_input_task.task_type)

    def test_modify_in_place_rejects_incoming_source_mode(self):
        input_dir = os.path.join(self.temp_dir, "01_input")
        os.makedirs(input_dir)
        self._write_file(os.path.join(input_dir, "clip.ma"), "maya scene")

        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        input_task = model.get_input_task()
        input_task.settings["input_dir"] = input_dir
        input_task.settings["extensions"] = [".ma"]
        model.add_module(
            modules.TaskRename(
                settings={
                    "source_mode": modules.SOURCE_MODE_INCOMING,
                    "output_mode": modules.OUTPUT_MODE_MODIFY,
                }
            )
        )

        result = model.validate_project()

        self.assertFalse(result.is_valid())
        self.assertTrue(any("cannot modify incoming input files" in error for error in result.errors))

    def test_rename_module_applies_optional_name_operations(self):
        model = batch_processor_model.BatchProcessorModel()
        model.project_name = "Show One"
        rename_task = modules.TaskRename(
            settings={
                "name_template": "{name}",
                "use_prefix": True,
                "prefix": "{project-sanitized-name}_",
                "use_suffix": True,
                "suffix": "_done",
                "use_search_replace": True,
                "search_text": "walk",
                "replace_text": "run",
                "use_index": True,
                "index_separator": "-",
                "padding": 2,
            }
        )
        work_item = modules.WorkItem(source_path=os.path.join(self.temp_dir, "walk.ma"))
        step_output_dir = os.path.join(self.temp_dir, "02_tasks", "01_rename")

        result = rename_task.build_output_path(work_item, 1, step_output_dir, project=model)

        expected = os.path.join(step_output_dir, "show_one_run_done-01.ma")
        self.assertEqual(os.path.normpath(expected), result)

    def test_python_scripts_folder_detects_sorted_scripts(self):
        scripts_dir = os.path.join(self.temp_dir, "scripts")
        os.makedirs(scripts_dir)
        self._write_file(os.path.join(scripts_dir, "02_second.py"), "def run(context): pass")
        self._write_file(os.path.join(scripts_dir, "01_first.py"), "def run(context): pass")
        self._write_file(os.path.join(scripts_dir, "__init__.py"), "")
        self._write_file(os.path.join(scripts_dir, "notes.txt"), "")
        model = batch_processor_model.BatchProcessorModel()
        script_task = modules.TaskPythonScriptsFolder(settings={"scripts_path": scripts_dir})

        result = [os.path.basename(path) for path in script_task.get_script_paths(model)]

        expected = ["01_first.py", "02_second.py"]
        self.assertEqual(expected, result)

    def test_python_task_uses_single_visible_python_task_name(self):
        script_task = modules.create_task(constants.TaskType.PYTHON_SCRIPT)
        categories = modules.get_task_categories()
        registered_task_types = []
        for task_classes in categories.values():
            registered_task_types.extend([task_class.task_type for task_class in task_classes])

        expected = "Python"
        self.assertEqual(expected, script_task.display_name)
        self.assertEqual(expected, script_task.default_display_name)
        self.assertNotIn(constants.TaskType.PYTHON_SCRIPTS_FOLDER, registered_task_types)

    def test_task_io_collapsed_state_round_trip(self):
        model = batch_processor_model.BatchProcessorModel()
        rename_task = model.add_task(modules.TaskRename(settings={"task_io_collapsed": True}))
        project_path = os.path.join(self.temp_dir, "test_project.batch")

        saved_path = model.save_to_file(project_path)
        loaded_model = batch_processor_model.BatchProcessorModel.from_file(saved_path)
        loaded_task = loaded_model.get_task(rename_task.id)

        expected = True
        self.assertEqual(expected, loaded_task.settings.get("task_io_collapsed"))

    def test_python_legacy_script_modes_are_normalized(self):
        inline_task = modules.TaskPythonScript(settings={"script_mode": "Single Script"})
        batch_task = modules.TaskPythonScript(settings={"script_mode": "Batch"})

        expected = "Inline"
        self.assertEqual(expected, inline_task.get_script_mode())
        expected = "Batch Directory"
        self.assertEqual(expected, batch_task.get_script_mode())

    def test_python_external_file_mode_detects_single_script(self):
        script_path = os.path.join(self.temp_dir, "external_script.py")
        self._write_file(script_path, "def run(context): pass")
        model = batch_processor_model.BatchProcessorModel()
        script_task = modules.TaskPythonScript(
            settings={
                "script_mode": "External File",
                "script_path": script_path,
            }
        )

        result = [os.path.basename(path) for path in script_task.get_script_paths(model)]

        expected = ["external_script.py"]
        self.assertEqual(expected, result)

    def test_legacy_python_scripts_folder_deserializes_as_python_batch(self):
        scripts_dir = os.path.join(self.temp_dir, "scripts")
        os.makedirs(scripts_dir)
        self._write_file(os.path.join(scripts_dir, "01_first.py"), "def run(context): pass")
        task_data = {
            "task_type": constants.TaskType.PYTHON_SCRIPTS_FOLDER,
            "display_name": "Run Python Scripts Folder",
            "settings": {"scripts_path": scripts_dir},
        }

        script_task = modules.create_task_from_dict(task_data)
        model = batch_processor_model.BatchProcessorModel()
        result = [os.path.basename(path) for path in script_task.get_script_paths(model)]

        expected = constants.TaskType.PYTHON_SCRIPT
        self.assertEqual(expected, script_task.task_type)
        expected = "Python"
        self.assertEqual(expected, script_task.display_name)
        expected = "Batch Directory"
        self.assertEqual(expected, script_task.settings.get("script_mode"))
        expected = ["01_first.py"]
        self.assertEqual(expected, result)

    def test_python_batch_directory_filters_scripts(self):
        scripts_dir = os.path.join(self.temp_dir, "scripts")
        os.makedirs(scripts_dir)
        self._write_file(os.path.join(scripts_dir, "01_build.py"), "def run(context): pass")
        self._write_file(os.path.join(scripts_dir, "02_publish.py"), "def run(context): pass")
        self._write_file(os.path.join(scripts_dir, "03_wip.py"), "def run(context): pass")
        script_task = modules.TaskPythonScript(
            settings={
                "script_mode": "Batch Directory",
                "scripts_path": scripts_dir,
                "batch_include_patterns": "*.py",
                "batch_exclude_patterns": "*wip.py, 01_*",
            }
        )
        model = batch_processor_model.BatchProcessorModel()

        result = [os.path.basename(path) for path in script_task.get_script_paths(model)]

        expected = ["02_publish.py"]
        self.assertEqual(expected, result)

    def test_python_task_executes_inline_script_with_context(self):
        context = {}
        script_text = "context['top_level'] = True\n\ndef run(context):\n    context['run_called'] = True\n"

        modules.TaskPythonScript.run_inline_python_script(script_text=script_text, context=context)

        self.assertTrue(context.get("top_level"))
        self.assertTrue(context.get("run_called"))

    def test_python_task_default_inline_script_documents_arguments_and_environment(self):
        script_task = modules.TaskPythonScript()

        result = script_task.settings.get("script_text")

        self.assertIn("arguments", result)
        self.assertIn("environment_variables", result)
        self.assertIn("project_path", result)
        self.assertNotIn("project_file_path", result)
        self.assertIn("import maya.cmds as cmds", result)
        self.assertIn("print", result)

    def test_python_task_builds_arguments_and_environment_context(self):
        project = batch_processor_model.BatchProcessorModel()
        project.project_file_path = os.path.join(self.temp_dir, "project.batch")
        project.environment_variables["custom-dir"] = "C:/custom"
        script_task = modules.TaskPythonScript()
        project.add_task(script_task)
        source_path = os.path.join(self.temp_dir, "source.ma")
        output_path = os.path.join(self.temp_dir, "output.ma")
        work_item = modules.WorkItem(source_path=source_path)

        result = script_task.build_script_context(
            work_item=work_item,
            output_path=output_path,
            project=project,
            script_paths=[],
            context={"preview": True},
        )

        self.assertEqual(work_item.current_path, result.get("arguments").get("input"))
        self.assertEqual(output_path, result.get("arguments").get("output"))
        self.assertEqual(project.project_file_path, result.get("arguments").get("project"))
        self.assertEqual(project.project_file_path, result.get("arguments").get("project_path"))
        self.assertEqual(project.project_file_path, result.get("project_path"))
        self.assertNotIn("project_file_path", result.get("arguments"))
        self.assertNotIn("project_file_path", result)
        self.assertEqual(script_task.display_name, result.get("arguments").get("task"))
        self.assertEqual("C:/custom", result.get("environment_variables").get("custom-dir"))
        self.assertEqual(project.project_file_path, result.get("environment_variables").get("project-path"))
        self.assertEqual(
            os.path.dirname(os.path.dirname(project.get_project_dir())),
            result.get("environment_variables").get("project-grandparent-dir"),
        )
        self.assertIs(result.get("arguments"), result.get("args"))
        self.assertIs(result.get("environment_variables"), result.get("env"))

    def test_python_task_exposes_arguments_and_environment_to_inline_globals(self):
        context = {
            "arguments": {"input": "source.ma"},
            "environment_variables": {"custom-dir": "C:/custom"},
        }
        script_text = "context['result'] = args.get('input') + '|' + env.get('custom-dir')\n"

        modules.TaskPythonScript.run_inline_python_script(script_text=script_text, context=context)

        expected = "source.ma|C:/custom"
        self.assertEqual(expected, context.get("result"))

    def test_python_task_exposes_arguments_and_environment_to_external_script_globals(self):
        script_path = os.path.join(self.temp_dir, "script.py")
        self._write_file(
            script_path,
            "context['result'] = arguments.get('input') + '|' + environment_variables.get('custom-dir')\n",
        )
        context = {
            "arguments": {"input": "source.ma"},
            "environment_variables": {"custom-dir": "C:/custom"},
        }

        modules.TaskPythonScript.run_python_script(script_path=script_path, context=context)

        expected = "source.ma|C:/custom"
        self.assertEqual(expected, context.get("result"))

    def test_task_utils_inline_python_exposes_arguments_and_environment_aliases(self):
        context = {
            "arguments": {"input": "source.ma"},
            "environment_variables": {"custom-dir": "C:/custom"},
        }
        script_text = "context['result'] = args.get('input') + '|' + env.get('custom-dir')\n"

        task_utils.run_inline_python_script(script_text=script_text, context=context)

        expected = "source.ma|C:/custom"
        self.assertEqual(expected, context.get("result"))

    def test_batch_maya_open_scene_routes_fbx_to_fbx_helper(self):
        source_path = os.path.join(self.temp_dir, "source.fbx")
        with mock.patch.object(batch_processor_maya, "open_fbx_scene", return_value=source_path) as mock_open_fbx:
            result = batch_processor_maya.open_scene(source_path, load_relevant_plugins=False)

        expected = source_path
        self.assertEqual(expected, result)
        mock_open_fbx.assert_called_once_with(source_path, load_relevant_plugins=False)

    def test_batch_maya_open_fbx_scene_uses_animation_preferences(self):
        source_path = os.path.join(self.temp_dir, "source.fbx")
        maya_cmds = mock.Mock()
        maya_cmds.file.return_value = source_path
        fbx_importer = mock.Mock()
        fbx_context = mock.MagicMock()
        fbx_context.__enter__.return_value = fbx_importer
        fbx_context.__exit__.return_value = False
        fake_fbx_module = types.ModuleType("gt.utils.fbx")
        fake_fbx_module.FbxImporter = mock.Mock(return_value=fbx_context)

        with mock.patch.dict(sys.modules, {"gt.utils.fbx": fake_fbx_module}):
            with mock.patch.object(batch_processor_maya, "get_maya_cmds", return_value=maya_cmds):
                with mock.patch.object(batch_processor_maya, "load_relevant_file_plugin") as mock_load_plugin:
                    result = batch_processor_maya.open_fbx_scene(source_path, load_relevant_plugins=True)

        expected = source_path
        self.assertEqual(expected, result)
        mock_load_plugin.assert_called_once_with(source_path)
        fake_fbx_module.FbxImporter.assert_called_once()
        fbx_importer.set_preferences_animation.assert_called_once()
        maya_cmds.file.assert_called_once_with(
            source_path,
            open=True,
            force=True,
            type="FBX",
            ignoreVersion=True,
        )

    def test_python_task_open_mode_opens_fbx_sources(self):
        source_path = os.path.join(self.temp_dir, "source.fbx")
        script_task = modules.TaskPythonScript()
        script_task.settings["source_load_mode"] = "Open"
        with mock.patch(
            "gt.tools.batch_processor.tasks.task_python_script.batch_processor_maya.open_scene"
        ) as mock_open_scene:
            with mock.patch(
                "gt.tools.batch_processor.tasks.task_python_script.batch_processor_maya.new_scene"
            ) as mock_new_scene:
                with mock.patch(
                    "gt.tools.batch_processor.tasks.task_python_script.batch_processor_maya.import_file"
                ) as mock_import_file:
                    script_task.load_source_scene(source_path)

        mock_open_scene.assert_called_once_with(source_path, load_relevant_plugins=True)
        mock_new_scene.assert_not_called()
        mock_import_file.assert_not_called()

    def test_task_utils_open_mode_opens_fbx_sources(self):
        source_path = os.path.join(self.temp_dir, "source.fbx")
        with mock.patch("gt.tools.batch_processor.tasks.task_utils.batch_processor_maya.open_scene") as mock_open_scene:
            with mock.patch(
                "gt.tools.batch_processor.tasks.task_utils.batch_processor_maya.new_scene"
            ) as mock_new_scene:
                with mock.patch(
                    "gt.tools.batch_processor.tasks.task_utils.batch_processor_maya.import_file"
                ) as mock_import_file:
                    task_utils.load_source_scene(
                        source_path,
                        source_load_mode="Open",
                        load_relevant_plugins=False,
                    )

        mock_open_scene.assert_called_once_with(source_path, load_relevant_plugins=False)
        mock_new_scene.assert_not_called()
        mock_import_file.assert_not_called()

    def test_usd_export_open_mode_opens_fbx_sources(self):
        source_path = os.path.join(self.temp_dir, "source.fbx")
        usd_task = modules.TaskExportUsd()
        usd_task.settings["source_load_mode"] = "Open"
        with mock.patch(
            "gt.tools.batch_processor.tasks.task_export_usd.batch_processor_maya.open_scene"
        ) as mock_open_scene:
            with mock.patch(
                "gt.tools.batch_processor.tasks.task_export_usd.batch_processor_maya.new_scene"
            ) as mock_new_scene:
                with mock.patch(
                    "gt.tools.batch_processor.tasks.task_export_usd.batch_processor_maya.import_file"
                ) as mock_import_file:
                    usd_task.load_source_scene(source_path)

        mock_open_scene.assert_called_once_with(source_path, load_relevant_plugins=True)
        mock_new_scene.assert_not_called()
        mock_import_file.assert_not_called()

    def test_maya_import_post_script_defaults_include_arguments_and_environment(self):
        import_task = modules.create_task(constants.TaskType.MAYA_IMPORT)

        result = import_task.settings.get("post_script_text")

        self.assertIn("arguments", result)
        self.assertIn("environment_variables", result)
        self.assertIn("import maya.cmds as cmds", result)
        self.assertTrue(import_task.settings.get("post_script_pass_standard_arguments"))
        self.assertTrue(import_task.settings.get("post_script_pass_environment_arguments"))

    def test_maya_import_open_only_opens_without_writing_output(self):
        import_task = modules.create_task(constants.TaskType.MAYA_IMPORT)
        import_task.settings["output_mode"] = modules.OUTPUT_MODE_PASSTHROUGH
        source_path = os.path.join(self.temp_dir, "incoming.fbx")
        work_item = modules.WorkItem(source_path=source_path)
        project = batch_processor_model.BatchProcessorModel()

        with mock.patch(
            "gt.tools.batch_processor.tasks.task_maya_import.batch_processor_maya.open_scene"
        ) as mock_open_scene:
            with mock.patch(
                "gt.tools.batch_processor.tasks.task_maya_import.batch_processor_maya.import_file"
            ) as mock_import_file:
                with mock.patch(
                    "gt.tools.batch_processor.tasks.task_maya_import.batch_processor_maya.save_scene"
                ) as mock_save_scene:
                    with mock.patch(
                        "gt.tools.batch_processor.tasks.task_maya_import.batch_processor_maya.apply_scene_options"
                    ):
                        result = import_task.execute(work_item, project, self.temp_dir)

        expected = source_path
        self.assertEqual(expected, result.current_path)
        mock_open_scene.assert_called_once_with(source_path, load_relevant_plugins=True)
        mock_import_file.assert_not_called()
        mock_save_scene.assert_not_called()

    def test_maya_import_open_only_does_not_require_target_path(self):
        import_task = modules.create_task(constants.TaskType.MAYA_IMPORT)
        import_task.settings["source_mode"] = modules.SOURCE_MODE_INCOMING
        import_task.settings["output_mode"] = modules.OUTPUT_MODE_PASSTHROUGH
        import_task.settings["target_path"] = ""
        import_task.settings["output_extension"] = ".fbx"

        result = import_task.validate_common_settings(batch_processor_model.BatchProcessorModel())
        task_result = import_task.validate(batch_processor_model.BatchProcessorModel())

        self.assertTrue(result.is_valid())
        self.assertTrue(task_result.is_valid())
        self.assertTrue(import_task.passes_through())
        self.assertFalse(import_task.writes_to_target_path())

    def test_maya_import_post_script_context_includes_arguments_and_environment(self):
        import_task = modules.create_task(constants.TaskType.MAYA_IMPORT)
        import_task.settings["run_post_script"] = True
        project = batch_processor_model.BatchProcessorModel()
        project.project_file_path = os.path.join(self.temp_dir, "project.batch")
        project.environment_variables["custom-dir"] = "C:/custom"
        project.add_task(import_task)
        work_item = modules.WorkItem(source_path=os.path.join(self.temp_dir, "source.fbx"))
        output_path = os.path.join(self.temp_dir, "output.ma")

        with mock.patch(
            "gt.tools.batch_processor.tasks.task_maya_import.task_utils.run_inline_python_script"
        ) as mock_run:
            import_task.run_post_script_if_needed(
                project=project,
                work_item=work_item,
                output_path=output_path,
                imported_nodes=["pCube1"],
                context={"runner": "test"},
            )

        result = mock_run.call_args.kwargs.get("context")
        self.assertEqual(work_item.current_path, result.get("arguments").get("input"))
        self.assertEqual(output_path, result.get("arguments").get("output"))
        self.assertEqual(project.project_file_path, result.get("arguments").get("project_path"))
        self.assertEqual(project.project_file_path, result.get("project_path"))
        self.assertNotIn("project_file_path", result.get("arguments"))
        self.assertNotIn("project_file_path", result)
        self.assertEqual("C:/custom", result.get("environment_variables").get("custom-dir"))
        self.assertEqual(project.project_file_path, result.get("environment_variables").get("project-path"))
        self.assertEqual(
            os.path.dirname(os.path.dirname(project.get_project_dir())),
            result.get("environment_variables").get("project-grandparent-dir"),
        )
        self.assertIs(result.get("arguments"), result.get("args"))
        self.assertIs(result.get("environment_variables"), result.get("env"))
        self.assertEqual(["pCube1"], result.get("imported_nodes"))
        self.assertEqual("test", result.get("runner"))

    def test_validation_task_defaults_use_project_validation_logs(self):
        scene_task = modules.create_task(constants.TaskType.MAYA_SCENE_VALIDATE)
        integrity_task = modules.create_task(constants.TaskType.FILE_INTEGRITY_VALIDATE)
        parity_task = modules.create_task(constants.TaskType.FOLDER_COMPARE_VALIDATE)

        expected = "{log-dir}"
        self.assertEqual(expected, scene_task.default_target_path_template)
        self.assertEqual(expected, integrity_task.default_target_path_template)
        self.assertEqual(expected, parity_task.default_target_path_template)
        self.assertEqual(expected, scene_task.settings.get("target_path"))
        self.assertEqual(expected, integrity_task.settings.get("target_path"))
        self.assertEqual(expected, parity_task.settings.get("target_path"))

    def test_validation_task_migrates_legacy_output_validation_logs(self):
        task_data = {
            "task_type": constants.TaskType.FILE_INTEGRITY_VALIDATE,
            "parameters": {
                "target_path": "{project-dir}/{output-dir}/validation_logs",
            },
        }

        integrity_task = modules.create_task_from_dict(task_data)

        expected = "{log-dir}"
        self.assertEqual(expected, integrity_task.settings.get("target_path"))

    def test_validation_task_migrates_old_project_validation_logs(self):
        task_data = {
            "task_type": constants.TaskType.FILE_INTEGRITY_VALIDATE,
            "parameters": {
                "target_path": "{project-dir}/validation_logs",
            },
        }

        integrity_task = modules.create_task_from_dict(task_data)

        expected = "{log-dir}"
        self.assertEqual(expected, integrity_task.settings.get("target_path"))

    def test_file_integrity_validation_writes_single_validate_report(self):
        file_a = os.path.join(self.temp_dir, "a.ma")
        file_b = os.path.join(self.temp_dir, "b.ma")
        self._write_file(file_a, "maya")
        self._write_file(file_b, "maya")
        work_items = [modules.WorkItem(source_path=file_a), modules.WorkItem(source_path=file_b)]
        task = modules.create_task(
            constants.TaskType.FILE_INTEGRITY_VALIDATE,
            settings={
                "log_mode": "Log All",
            },
        )
        step_output_dir = os.path.join(self.temp_dir, "logs")
        os.makedirs(step_output_dir)

        for index, work_item in enumerate(work_items, start=1):
            task.execute(
                work_item=work_item,
                project=batch_processor_model.BatchProcessorModel(),
                step_output_dir=step_output_dir,
                context={"item_index": index, "work_items": work_items},
            )

        report_path = os.path.join(step_output_dir, "validate_validate_integrity.json")
        with open(report_path, "r", encoding="utf-8") as report_file:
            result = json.load(report_file)

        expected = 2
        self.assertEqual(expected, len(result.get("entries") or []))
        expected = ["validate_validate_integrity.json"]
        self.assertEqual(expected, os.listdir(step_output_dir))

    def test_validation_task_names_are_short(self):
        scene_task = modules.create_task(constants.TaskType.MAYA_SCENE_VALIDATE)
        integrity_task = modules.create_task(constants.TaskType.FILE_INTEGRITY_VALIDATE)
        parity_task = modules.create_task(constants.TaskType.FOLDER_COMPARE_VALIDATE)

        expected = "Validate Scene"
        self.assertEqual(expected, scene_task.display_name)
        expected = "Validate Integrity"
        self.assertEqual(expected, integrity_task.display_name)
        expected = "Validate Parity"
        self.assertEqual(expected, parity_task.display_name)

    def test_clip_snapshot_default_path_uses_project_data_folder(self):
        clip_snapshot_task = modules.create_task(constants.TaskType.CLIP_SNAPSHOT)

        expected = "{project-dir}/data/clip_snapshot_data.json"
        self.assertEqual(expected, clip_snapshot_task.settings.get("snapshot_path"))

    def test_clip_split_default_target_path_uses_clips_task_folder(self):
        clip_split_task = modules.create_task(constants.TaskType.CLIP_SPLIT)

        expected = "{project-dir}/{task-dir}/{task-idx}_clips"
        self.assertEqual(expected, clip_split_task.settings.get("target_path"))

    def test_clip_snapshot_is_excluded_from_task_index_by_default(self):
        clip_snapshot_task = modules.create_task(constants.TaskType.CLIP_SNAPSHOT)

        expected = False
        self.assertEqual(expected, clip_snapshot_task.settings.get("include_in_task_index"))
        self.assertFalse(clip_snapshot_task.includes_task_index())

    def test_clip_snapshot_bypass_mode_validates_without_snapshot_path(self):
        from gt.tools.batch_processor.tasks import task_clip

        clip_snapshot_task = modules.create_task(constants.TaskType.CLIP_SNAPSHOT)
        clip_snapshot_task.settings["mode"] = task_clip.CLIP_SNAPSHOT_MODE_BYPASS
        clip_snapshot_task.settings["snapshot_path"] = ""

        result = clip_snapshot_task.validate(batch_processor_model.BatchProcessorModel())

        self.assertTrue(result.is_valid())

    def test_clip_snapshot_bypass_skips_and_preserves_incoming_items(self):
        from gt.tools.batch_processor import batch_processor_task_base as task_base
        from gt.tools.batch_processor.tasks import task_clip

        clip_snapshot_task = modules.create_task(constants.TaskType.CLIP_SNAPSHOT)
        clip_snapshot_task.settings["mode"] = task_clip.CLIP_SNAPSHOT_MODE_BYPASS
        work_items = [
            modules.WorkItem(source_path=os.path.join(self.temp_dir, "walk.ma")),
            modules.WorkItem(source_path=os.path.join(self.temp_dir, "run.ma")),
        ]

        with self.assertRaises(task_base.TaskSkip) as context_manager:
            clip_snapshot_task.execute(
                work_item=None,
                project=batch_processor_model.BatchProcessorModel(),
                step_output_dir=self.temp_dir,
                context={"work_items": work_items},
            )

        self.assertEqual(work_items, context_manager.exception.work_item)

    def test_skipped_aggregate_task_can_forward_work_item_list(self):
        from gt.tools.batch_processor import batch_processor_task_base as task_base

        runner = batch_processor_worker.SingleInstanceBatchRunner()
        work_items = [
            modules.WorkItem(source_path=os.path.join(self.temp_dir, "walk.ma")),
            modules.WorkItem(source_path=os.path.join(self.temp_dir, "run.ma")),
        ]
        output_items = []
        skip_exception = task_base.TaskSkip("Bypassed.", work_item=list(work_items))

        runner._append_skipped_output_items(output_items=output_items, exception=skip_exception)

        self.assertEqual(work_items, output_items)

    def test_clip_split_legacy_display_name_is_migrated(self):
        clip_task = modules.create_task(constants.TaskType.CLIP_SPLIT, display_name="Split Clips")

        expected = "Clip Split"
        self.assertEqual(expected, clip_task.display_name)

    def test_clip_split_existing_outputs_return_all_clip_work_items(self):
        from gt.tools.batch_processor.tasks import task_clip

        source_path = os.path.join(self.temp_dir, "source.ma")
        output_dir = os.path.join(self.temp_dir, "clips")
        self._write_file(source_path, "maya scene")
        os.makedirs(output_dir)
        clip_task = modules.create_task(constants.TaskType.CLIP_SPLIT)
        work_item = modules.WorkItem(source_path=source_path)
        clips = [
            {"name": "walk", "start": 1, "end": 10, "active": True},
            {"name": "run", "start": 11, "end": 20, "active": True},
        ]
        for clip in clips:
            output_path = clip_task.build_clip_output_path(work_item=work_item, step_output_dir=output_dir, clip=clip)
            self._write_file(output_path, "existing clip")

        with mock.patch.object(task_clip.batch_processor_maya, "open_scene"):
            with mock.patch.object(task_clip.batch_processor_maya, "save_scene") as save_scene_mock:
                with mock.patch.object(task_clip, "get_scene_clip_data", return_value=clips):
                    with mock.patch.object(task_clip, "set_timeline_from_clip"):
                        result = clip_task.execute(
                            work_item=work_item,
                            project=batch_processor_model.BatchProcessorModel(),
                            step_output_dir=output_dir,
                        )

        expected = ["source_run_f0011-0020.ma", "source_walk_f0001-0010.ma"]
        self.assertEqual(expected, sorted([os.path.basename(item.current_path) for item in result]))
        save_scene_mock.assert_not_called()

    def test_capture_tasks_have_optional_camera_setting(self):
        thumbnail_task = modules.create_task(constants.TaskType.THUMBNAIL_CAPTURE)
        playblast_task = modules.create_task(constants.TaskType.PLAYBLAST_CAPTURE)

        expected = ""
        self.assertEqual(expected, thumbnail_task.settings.get("camera_name"))
        self.assertEqual(expected, playblast_task.settings.get("camera_name"))

    def test_registered_task_classes_use_task_prefix(self):
        thumbnail_task = modules.create_task(constants.TaskType.THUMBNAIL_CAPTURE)
        playblast_task = modules.create_task(constants.TaskType.PLAYBLAST_CAPTURE)
        usd_task = modules.create_task(constants.TaskType.USD_EXPORT)

        expected = "TaskCaptureThumbnail"
        self.assertEqual(expected, thumbnail_task.__class__.__name__)
        expected = "TaskCapturePlayblast"
        self.assertEqual(expected, playblast_task.__class__.__name__)
        expected = "TaskExportUsd"
        self.assertEqual(expected, usd_task.__class__.__name__)

    def test_hik_retarget_task_is_registered(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)

        expected = "TaskRetargetHumanIK"
        self.assertEqual(expected, hik_task.__class__.__name__)
        expected = "Animation"
        self.assertEqual(expected, hik_task.category)
        expected = "HumanIK"
        self.assertEqual(expected, hik_task.display_name)
        expected = True
        self.assertEqual(expected, hik_task.settings.get("bake_animation"))
        expected = "Open"
        self.assertEqual(expected, hik_task.settings.get("source_load_mode"))
        expected = ""
        self.assertEqual(expected, hik_task.settings.get("source_root"))
        expected = "source"
        self.assertEqual(expected, hik_task.settings.get("source_namespace"))
        expected = True
        self.assertEqual(expected, hik_task.settings.get("set_framerate"))
        expected = False
        self.assertEqual(expected, hik_task.settings.get("source_character_pre_existing"))
        expected = False
        self.assertEqual(expected, hik_task.settings.get("load_target_properties"))
        expected = ""
        self.assertEqual(expected, hik_task.settings.get("target_properties_path"))
        expected = "{project-dir}/data/source_hik.xml"
        self.assertEqual(expected, hik_task.settings.get("source_definition_path"))
        expected = "{project-dir}/data/source_tpose.pose"
        self.assertEqual(expected, hik_task.settings.get("source_tpose_path"))
        self.assertIn("None", modules.HIK_BAKE_TARGETS)
        self.assertFalse(hik_task.settings.get("run_pre_bake_script"))
        self.assertTrue(hik_task.settings.get("pre_bake_script_collapsed"))
        self.assertIn("pre_bake_script_text", hik_task.settings)
        self.assertIn("import maya.cmds as cmds", hik_task.settings.get("pre_bake_script_text"))
        self.assertIn("post_script_text", hik_task.settings)
        self.assertIn("import maya.cmds as cmds", hik_task.settings.get("post_script_text"))
        self.assertIn("arguments", hik_task.settings.get("post_script_text"))
        self.assertIn("environment_variables", hik_task.settings.get("post_script_text"))
        self.assertTrue(hik_task.settings.get("post_script_pass_standard_arguments"))
        self.assertTrue(hik_task.settings.get("post_script_pass_environment_arguments"))
        self.assertIn("source_namespace", hik_task.settings)
        self.assertIn("target_namespace", hik_task.settings)
        expected = True
        self.assertEqual(expected, hik_task.settings.get("delete_source_namespace"))

    def test_hik_retarget_pre_existing_source_skips_source_definition_validation(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        hik_task.settings["source_character_pre_existing"] = True
        hik_task.settings["source_definition_path"] = os.path.join(self.temp_dir, "missing_source_hik.xml")
        hik_task.settings["source_tpose_path"] = os.path.join(self.temp_dir, "missing_source_tpose.pose")

        result = hik_task.validate(batch_processor_model.BatchProcessorModel())

        self.assertTrue(result.is_valid())
        self.assertFalse(any("Source HIK definition" in error for error in result.errors))
        self.assertFalse(any("Source T-pose" in error for error in result.errors))

    def test_hik_retarget_target_properties_validation_requires_existing_file(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        hik_task.settings["load_target_properties"] = True
        hik_task.settings["target_properties_path"] = os.path.join(self.temp_dir, "missing_properties.json")

        result = hik_task.validate(batch_processor_model.BatchProcessorModel())

        self.assertFalse(result.is_valid())
        self.assertTrue(any("Target HumanIK properties do not exist" in error for error in result.errors))

    def test_hik_retarget_loads_target_properties(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        hik_task.settings["load_target_properties"] = True
        hik_task.settings["target_properties_path"] = "properties.json"
        project = batch_processor_model.BatchProcessorModel()

        with mock.patch.object(hik_task, "get_resolved_path", return_value="C:/properties.json"):
            with mock.patch("gt.core.io.read_json_dict", return_value={"ReachActorLeftWrist": 0.5}):
                with mock.patch(
                    "gt.utils.hik.set_hik_properties",
                    return_value={"ReachActorLeftWrist": 0.5},
                ) as mock_set_properties:
                    with mock.patch.object(hik_task, "evaluate_hik_character") as mock_evaluate:
                        result = hik_task.load_target_hik_properties(project, "TargetCharacter")

        expected = {"ReachActorLeftWrist": 0.5}
        self.assertEqual(expected, result)
        mock_set_properties.assert_called_once_with("TargetCharacter", expected)
        mock_evaluate.assert_called_once_with("TargetCharacter")

    def test_hik_retarget_pre_existing_source_character_is_not_created(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        hik_task.settings["source_character_pre_existing"] = True
        hik_task.settings["source_character_name"] = "ExistingSource"

        with mock.patch.object(hik_task, "get_pre_existing_source_character", return_value="ExistingSource"):
            with mock.patch.object(hik_task, "get_or_create_hik_character") as mock_get_or_create:
                with mock.patch.object(hik_task, "evaluate_hik_character") as mock_evaluate:
                    result = hik_task.setup_source_character(batch_processor_model.BatchProcessorModel())

        expected = "ExistingSource"
        self.assertEqual(expected, result)
        mock_get_or_create.assert_not_called()
        mock_evaluate.assert_called_once_with("ExistingSource")

    def test_hik_retarget_applies_pose_and_creates_character_with_source_namespace(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        project = batch_processor_model.BatchProcessorModel()
        hik_task._runtime_source_namespace = "source"
        hik_task.settings["source_tpose_path"] = "source_tpose.pose"
        hik_task.settings["source_definition_path"] = "source_hik.xml"
        pose_data = {"Hips": {"rx": 10}}
        current_pose = {"Hips": {"rx": 20}}

        with mock.patch.object(hik_task, "get_or_create_hik_character", return_value="source:source") as mock_create:
            with mock.patch.object(hik_task, "get_source_joints", return_value=["source:Hips"]):
                with mock.patch.object(
                    hik_task,
                    "get_resolved_path",
                    side_effect=["source_tpose.pose", "source_hik.xml"],
                ):
                    with mock.patch("gt.core.pose.get_pose_as_dict", return_value=current_pose):
                        with mock.patch(
                            "gt.core.pose.set_pose_from_dict",
                            side_effect=[["source:Hips"], ["source:Hips"]],
                        ) as mock_set_pose:
                            with mock.patch("gt.core.io.read_json_dict", return_value=pose_data):
                                with mock.patch("gt.utils.hik.set_definition_lock") as mock_set_lock:
                                    with mock.patch("gt.utils.hik.import_definition_from_xml") as mock_import_definition:
                                        with mock.patch.object(hik_task, "force_joint_evaluation"):
                                            with mock.patch.object(hik_task, "evaluate_hik_character"):
                                                result = hik_task.setup_source_character(project)

        expected = "source:source"
        self.assertEqual(expected, result)
        mock_create.assert_called_once_with("source:source")
        mock_set_lock.assert_any_call("source:source", False)
        mock_set_lock.assert_any_call("source:source", True)
        mock_set_pose.assert_has_calls(
            [
                mock.call(pose_data, namespace="source"),
                mock.call(current_pose, namespace="source"),
            ]
        )
        mock_import_definition.assert_called_once_with(
            "source:source",
            "source_hik.xml",
            prefix="source:",
        )

    def test_hik_retarget_pre_existing_source_character_missing_errors(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        hik_task.settings["source_character_pre_existing"] = True
        hik_task.settings["source_character_name"] = "MissingSource"

        with mock.patch.object(hik_task, "get_pre_existing_source_character", return_value=""):
            with mock.patch.object(hik_task, "get_hik_characters", return_value=["OtherCharacter"]):
                with self.assertRaises(RuntimeError) as context_manager:
                    hik_task.setup_source_character(batch_processor_model.BatchProcessorModel())

        self.assertIn(
            "Pre-existing HumanIK source character 'MissingSource' does not exist",
            str(context_manager.exception),
        )
        self.assertIn("OtherCharacter", str(context_manager.exception))

    def test_hik_retarget_post_script_context_includes_arguments_and_environment(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        hik_task.settings["run_post_script"] = True
        project = batch_processor_model.BatchProcessorModel()
        project.project_file_path = os.path.join(self.temp_dir, "project.batch")
        project.environment_variables["custom-dir"] = "C:/custom"
        project.add_task(hik_task)
        work_item = modules.WorkItem(source_path=os.path.join(self.temp_dir, "source.fbx"))
        output_path = os.path.join(self.temp_dir, "output.ma")

        with mock.patch("gt.tools.batch_processor.tasks.task_hik_retarget.run_inline_python_script") as mock_run:
            hik_task.run_post_script_if_needed(
                project=project,
                work_item=work_item,
                output_path=output_path,
                source_character="source",
                target_character="target",
                imported_source_nodes=["source:root"],
                imported_target_nodes=["target:root"],
                context={"runner": "test"},
            )

        result = mock_run.call_args.kwargs.get("context")
        self.assertEqual(work_item.current_path, result.get("arguments").get("input"))
        self.assertEqual(output_path, result.get("arguments").get("output"))
        self.assertEqual(project.project_file_path, result.get("arguments").get("project_path"))
        self.assertEqual(project.project_file_path, result.get("project_path"))
        self.assertNotIn("project_file_path", result.get("arguments"))
        self.assertNotIn("project_file_path", result)
        self.assertEqual("C:/custom", result.get("environment_variables").get("custom-dir"))
        self.assertEqual(project.project_file_path, result.get("environment_variables").get("project-path"))
        self.assertEqual(
            os.path.dirname(os.path.dirname(project.get_project_dir())),
            result.get("environment_variables").get("project-grandparent-dir"),
        )
        self.assertIs(result.get("arguments"), result.get("args"))
        self.assertIs(result.get("environment_variables"), result.get("env"))
        self.assertEqual("source", result.get("source_character"))
        self.assertEqual("target", result.get("target_character"))
        self.assertEqual(["source:root"], result.get("imported_source_nodes"))
        self.assertEqual(["target:root"], result.get("imported_target_nodes"))
        self.assertEqual("test", result.get("runner"))

    def test_hik_retarget_pre_bake_script_context_and_bake_gate(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        hik_task.settings["run_pre_bake_script"] = True
        project = batch_processor_model.BatchProcessorModel()
        work_item = modules.WorkItem(source_path=os.path.join(self.temp_dir, "source.fbx"))

        with mock.patch("gt.tools.batch_processor.tasks.task_hik_retarget.run_inline_python_script") as mock_run:
            hik_task.run_pre_bake_script_if_needed(
                project=project,
                work_item=work_item,
                output_path=os.path.join(self.temp_dir, "output.ma"),
                source_character="source",
                target_character="target",
                imported_source_nodes=["source:root"],
                imported_target_nodes=["target:root"],
            )

            expected = "<humanik_pre_bake_script>"
            self.assertEqual(expected, mock_run.call_args.kwargs.get("script_name"))
            result = mock_run.call_args.kwargs.get("context")
            expected = "target"
            self.assertEqual(expected, result.get("target_character"))

            mock_run.reset_mock()
            hik_task.settings["bake_animation"] = False
            hik_task.run_pre_bake_script_if_needed(
                project=project,
                work_item=work_item,
                output_path=os.path.join(self.temp_dir, "output.ma"),
                source_character="source",
                target_character="target",
                imported_source_nodes=[],
                imported_target_nodes=[],
            )
            mock_run.assert_called_once()

    def test_hik_retarget_runs_pre_bake_callback_immediately_before_bake(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        fake_hik_module = types.ModuleType("gt.utils.hik")
        fake_hik_module.set_definition_source = mock.Mock(return_value=True)
        fake_hik_module.bake_to_skeleton = mock.Mock(return_value=True)
        fake_hik_module.bake_to_control_rig = mock.Mock(return_value=True)
        ordered_calls = mock.Mock()
        pre_bake_callback = mock.Mock()
        ordered_calls.attach_mock(pre_bake_callback, "pre_bake")
        ordered_calls.attach_mock(fake_hik_module.bake_to_skeleton, "bake")

        with mock.patch.dict(sys.modules, {"gt.utils.hik": fake_hik_module}):
            with mock.patch.object(hik_task, "evaluate_hik_character"):
                hik_task.retarget_and_bake(
                    source_character="source",
                    target_character="target",
                    pre_bake_callback=pre_bake_callback,
                )

        expected = [
            mock.call.pre_bake(),
            mock.call.bake("target", force_proxy=False),
        ]
        self.assertEqual(expected, ordered_calls.mock_calls)

        ordered_calls.reset_mock()
        hik_task.settings["bake_animation"] = False
        with mock.patch.dict(sys.modules, {"gt.utils.hik": fake_hik_module}):
            with mock.patch.object(hik_task, "evaluate_hik_character"):
                hik_task.retarget_and_bake(
                    source_character="source",
                    target_character="target",
                    pre_bake_callback=pre_bake_callback,
                )

        expected = [mock.call.pre_bake()]
        self.assertEqual(expected, ordered_calls.mock_calls)

    def test_hik_retarget_open_mode_opens_fbx_sources(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        source_path = os.path.join(self.temp_dir, "source.fbx")
        hik_task.settings["source_load_mode"] = "Open"

        with mock.patch.object(hik_task, "open_fbx_source_scene") as mock_open_fbx:
            with mock.patch.object(hik_task, "get_source_scene_nodes", return_value=["SourceRoot"]):
                with mock.patch.object(hik_task, "apply_source_namespace_to_opened_scene", return_value=["SourceRoot"]):
                    with mock.patch.object(hik_task, "detect_runtime_namespace", return_value=""):
                        with mock.patch.object(hik_task, "import_fbx_source_animation") as mock_import_fbx:
                            with mock.patch("gt.tools.batch_processor.batch_processor_maya.new_scene") as mock_new_scene:
                                result = hik_task.load_source(source_path)

        expected = ["SourceRoot"]
        self.assertEqual(expected, result)
        mock_open_fbx.assert_called_once_with(source_path)
        mock_import_fbx.assert_not_called()
        mock_new_scene.assert_not_called()

    def test_hik_retarget_character_namespace_candidates(self):
        result = modules.TaskRetargetHumanIK.get_hik_character_namespace_candidates("my_sourcef", "foo")

        expected = ["foo:my_sourcef", "my_sourcef"]
        self.assertEqual(expected, result)

    def test_hik_retarget_namespaces_character_when_hik_creation_ignores_namespace(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)

        with mock.patch.object(hik_task, "resolve_hik_character", return_value=""):
            with mock.patch.object(
                hik_task,
                "get_hik_characters",
                side_effect=[[], ["source1"]],
            ):
                with mock.patch.object(
                    hik_task,
                    "is_hik_character",
                    side_effect=[False, True],
                ):
                    with mock.patch.object(hik_task, "evaluate_hik_character"):
                        with mock.patch("gt.utils.hik.create_definition", return_value="source:source"):
                            with mock.patch(
                                "gt.utils.hik.rename_definition",
                                return_value="source:source1",
                            ) as mock_rename:
                                result = hik_task.get_or_create_hik_character("source:source")

        expected = "source:source1"
        self.assertEqual(expected, result)
        mock_rename.assert_called_once_with("source1", "source:source")

        result = modules.TaskRetargetHumanIK.get_hik_character_namespace_candidates("foo:my_sourcef", "foo")

        expected = ["foo:my_sourcef", "my_sourcef"]
        self.assertEqual(expected, result)

    def test_hik_retarget_character_resolver_falls_back_to_unnamespaced_hik_node(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)

        with mock.patch.object(hik_task, "is_hik_character", side_effect=lambda name: name == "my_sourcef"):
            result = hik_task.resolve_hik_character_for_namespace("my_sourcef", "foo")

        expected = "my_sourcef"
        self.assertEqual(expected, result)

    def test_hik_resolve_delete_paths_expands_non_unique_names(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        maya_cmds = mock.Mock()
        maya_cmds.ls.side_effect = lambda node, long: {
            "Hips": ["|group_a|Hips", "|group_b|Hips"],
            "source": ["source"],
        }.get(node, [])

        with mock.patch.object(batch_processor_maya, "get_maya_cmds", return_value=maya_cmds):
            result = hik_task.resolve_delete_paths(["Hips", "source"])

        expected = ["|group_a|Hips", "|group_b|Hips", "source"]
        self.assertEqual(expected, result)

    def test_hik_delete_source_nodes_logs_failures_without_raising(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        maya_cmds = mock.Mock()
        maya_cmds.ls.side_effect = lambda node, long: {
            "Hips": ["|group_a|Hips", "|group_b|Hips"],
        }.get(node, [])
        maya_cmds.objExists.return_value = True

        def fake_delete(path):
            if path == "|group_b|Hips":
                raise RuntimeError("More than one object matches name")

        maya_cmds.delete.side_effect = fake_delete

        with mock.patch.object(batch_processor_maya, "get_maya_cmds", return_value=maya_cmds):
            result = hik_task.delete_source_nodes(["Hips"])

        expected = {"deleted": 1, "skipped": 0, "failed": 1}
        self.assertEqual(expected, result)

    def test_hik_export_source_root_prefers_configured_namespace(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        hik_task.settings["source_root"] = "Hips"
        hik_task.settings["source_namespace"] = "source"

        with mock.patch.object(hik_task, "object_exists", return_value=True) as mock_exists:
            result = hik_task.resolve_source_root_for_export()

        expected = "source:Hips"
        self.assertEqual(expected, result)
        mock_exists.assert_called_once_with(expected)

    def test_hik_export_source_root_falls_back_to_unnamespaced_node(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        hik_task.settings["source_root"] = "Hips"
        hik_task.settings["source_namespace"] = "source"

        with mock.patch.object(hik_task, "object_exists", side_effect=lambda node: node == "Hips") as mock_exists:
            result = hik_task.resolve_source_root_for_export()

        expected = "Hips"
        self.assertEqual(expected, result)
        expected_calls = [mock.call("source:Hips"), mock.call("Hips")]
        self.assertEqual(expected_calls, mock_exists.call_args_list)

    def test_hik_retarget_execute_captures_range_after_scene_options(self):
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        work_item = modules.WorkItem(source_path=os.path.join(self.temp_dir, "source.fbx"))
        step_output_dir = os.path.join(self.temp_dir, "output")
        project = batch_processor_model.BatchProcessorModel()
        events = []

        def record_event(name, result=None):
            """Records an event and returns a mocked result.

            Args:
                name (str): Event name.
                result (object, optional): Result to return.

            Returns:
                object: Mocked result.
            """
            events.append(name)
            return result

        with mock.patch.object(hik_task, "load_source", side_effect=lambda *args: record_event("load", [])):
            with mock.patch(
                "gt.tools.batch_processor.tasks.task_hik_retarget.batch_processor_maya.apply_scene_options",
                side_effect=lambda *args: record_event("scene_options", {}),
            ):
                with mock.patch.object(
                    hik_task,
                    "round_playback_range_to_whole_frames",
                    side_effect=lambda *args: record_event("round", {}),
                ):
                    with mock.patch.object(
                        hik_task,
                        "capture_playback_range",
                        side_effect=lambda *args: record_event("capture", {"min": 10, "max": 20}),
                    ):
                        with mock.patch.object(
                            hik_task,
                            "import_target_rig",
                            side_effect=lambda *args: record_event("target", []),
                        ):
                            with mock.patch.object(
                                hik_task,
                                "restore_playback_range",
                                side_effect=lambda *args: record_event("restore"),
                            ):
                                with mock.patch.object(hik_task, "get_hik_characters", return_value=[]):
                                    with mock.patch.object(
                                        hik_task,
                                        "setup_source_character",
                                        side_effect=lambda *args: record_event("source_character", "source"),
                                    ):
                                        with mock.patch.object(
                                            hik_task,
                                            "get_target_character",
                                            side_effect=lambda *args: record_event("target_character", "target"),
                                        ):
                                            with mock.patch.object(
                                                hik_task,
                                                "load_target_hik_properties",
                                                side_effect=lambda *args: record_event("properties", {}),
                                            ):
                                                with mock.patch.object(
                                                    hik_task,
                                                    "retarget_and_bake",
                                                    side_effect=lambda *args, **kwargs: record_event("retarget"),
                                                ):
                                                    with mock.patch.object(
                                                        hik_task,
                                                        "run_post_script_if_needed",
                                                        side_effect=lambda *args, **kwargs: record_event("post"),
                                                    ):
                                                        with mock.patch.object(
                                                            hik_task,
                                                            "cleanup_source",
                                                            side_effect=lambda *args: record_event("cleanup"),
                                                        ):
                                                            with mock.patch.object(
                                                                hik_task,
                                                                "write_output",
                                                                side_effect=lambda *args: record_event("write"),
                                                            ):
                                                                hik_task.execute(work_item, project, step_output_dir)

        self.assertLess(events.index("load"), events.index("scene_options"))
        self.assertLess(events.index("scene_options"), events.index("round"))
        self.assertLess(events.index("round"), events.index("capture"))
        self.assertLess(events.index("capture"), events.index("target"))
        self.assertLess(events.index("target"), events.index("restore"))
        self.assertLess(events.index("target_character"), events.index("properties"))
        self.assertLess(events.index("properties"), events.index("retarget"))

    def test_skipped_task_feedback_uses_short_utf8_tracker_line(self):
        args = mock.Mock()
        args.flag_skipped_tasks = True
        args.worker_id = "1"
        args.total_jobs = "2"
        args.current_task_index = 2
        args.total_tasks = 5
        args.source_file = os.path.join(self.temp_dir, "guilherme-001.fbx")
        hik_task = modules.create_task(constants.TaskType.HIK_RETARGET)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream):
            batch_processor_multi_worker.print_skipped_task_flag(
                args,
                hik_task,
                RuntimeError("This long warning should stay out of the tracker marker."),
                file_name="guilherme-001.fbx",
            )
        result = stream.getvalue().strip()

        self.assertTrue(stream.getvalue().startswith("     ∟"))
        expected = (
            "∟ ⏩ SKIPPING: (HumanIK) 'guilherme-001.fbx' "
            "(Task 2/5 | Job 1/2)"
        )
        self.assertEqual(expected, result)
        self.assertNotIn("long warning", result)

    def test_running_task_feedback_reports_task_and_job_progress(self):
        args = mock.Mock()
        args.flag_running_tasks = True
        args.worker_id = "2"
        args.total_jobs = "4"
        args.current_task_index = 3
        args.total_tasks = 5
        args.source_file = os.path.join(self.temp_dir, "walk.fbx")
        rename_task = modules.create_task(constants.TaskType.RENAME)
        stream = io.StringIO()

        with contextlib.redirect_stdout(stream):
            batch_processor_multi_worker.print_running_task_flag(
                args=args,
                task=rename_task,
                file_name="walk.fbx",
            )

        result = stream.getvalue()
        self.assertTrue(result.startswith("     ∟ ⚙️ RUNNING:"))
        self.assertIn("(Task 3/5 | Job 2/4)", result)

    def test_final_running_task_feedback_accepts_named_worker_id(self):
        args = mock.Mock()
        args.flag_running_tasks = True
        args.worker_id = "Final"
        args.total_jobs = "1"
        args.current_task_index = 1
        args.total_tasks = 1
        args.source_file = os.path.join(self.temp_dir, "project.batch")
        zip_task = modules.create_task(constants.TaskType.ZIP_COMPRESS)
        stream = io.StringIO()

        with contextlib.redirect_stdout(stream):
            batch_processor_multi_worker.print_running_task_flag(
                args=args,
                task=zip_task,
                file_name="Zip Compress",
            )

        expected = "(Task 1/1 | Job 1/1)"
        self.assertIn(expected, stream.getvalue())

    def test_multi_worker_skip_marker_flushes_immediately(self):
        class FlushStream(io.StringIO):
            """String stream that records whether it was flushed."""

            def __init__(self):
                """Initializes the test stream."""
                super(FlushStream, self).__init__()
                self.was_flushed = False

            def flush(self):
                """Records that flush was requested."""
                self.was_flushed = True
                super(FlushStream, self).flush()

        args = mock.Mock()
        args.flag_skipped_tasks = True
        args.worker_id = "1"
        args.total_jobs = "1"
        args.current_task_index = 1
        args.total_tasks = 1
        args.source_file = os.path.join(self.temp_dir, "source.fbx")
        rename_task = modules.create_task(constants.TaskType.RENAME)
        stream = FlushStream()

        with mock.patch("sys.stdout", stream):
            batch_processor_multi_worker.print_skipped_task_flag(
                args,
                rename_task,
                RuntimeError("Skipped because output exists."),
                file_name="source.fbx",
            )

        self.assertTrue(stream.was_flushed)
        self.assertIn("SKIPPING", stream.getvalue())

    def test_single_instance_skip_marker_precedes_done_counter(self):
        class OrderedTracker(batch_processor_tracker.BatchProgressTracker):
            """Tracker that records message and skip-counter call order."""

            def __init__(self):
                """Initializes the ordered tracker."""
                super(OrderedTracker, self).__init__()
                self.events = []

            def record_message(self, message):
                """Records a message event.

                Args:
                    message (str): Message sent to the tracker.
                """
                self.events.append(str(message))
                super(OrderedTracker, self).record_message(message)

            def record_skipped(self):
                """Records a skip counter event."""
                self.events.append("DONE_COUNTER")
                super(OrderedTracker, self).record_skipped()

        source_path = os.path.join(self.temp_dir, "source.fbx")
        step_output_dir = os.path.join(self.temp_dir, "step_output")
        os.makedirs(step_output_dir)
        self._write_file(source_path, "source")
        self._write_file(os.path.join(step_output_dir, "source.fbx"), "existing")
        project = batch_processor_model.BatchProcessorModel()
        rename_task = modules.TaskRename(settings={"name_template": "{name}", "overwrite": False})
        tracker = OrderedTracker()
        runner = batch_processor_worker.SingleInstanceBatchRunner(
            tracker=tracker,
            flag_skipped_tasks=True,
        )

        runner._run_task(
            project=project,
            task=rename_task,
            work_items=[modules.WorkItem(source_path=source_path)],
            step_output_dir=step_output_dir,
        )

        skip_index = next(index for index, event in enumerate(tracker.events) if "SKIPPING" in event)
        done_counter_index = tracker.events.index("DONE_COUNTER")
        self.assertLess(skip_index, done_counter_index)

    def test_tracker_event_reader_returns_only_new_complete_events(self):
        event_path = os.path.join(self.temp_dir, "worker.jsonl")
        writer = tracker_events.EventWriter(event_path, "job-0001")
        reader = tracker_events.EventReader(event_path)
        writer.emit("job_started")

        first_result = reader.read_new()
        writer.emit("task_started", task_id="rename")
        second_result = reader.read_new()
        writer.close()

        expected = ["job_started"]
        self.assertEqual(expected, [event.get("event") for event in first_result])
        expected = ["task_started"]
        self.assertEqual(expected, [event.get("event") for event in second_result])

    def test_hik_export_buttons_do_not_update_task_path_settings(self):
        widget_path = os.path.join(
            package_root_dir,
            "tools",
            "batch_processor",
            "widgets",
            "attr_widget_hik_retarget.py",
        )
        with open(widget_path, "r", encoding="utf-8") as widget_file:
            widget_source = widget_file.read()

        self.assertNotIn('self.set_task_setting(file_path, key="source_tpose_path")', widget_source)
        self.assertNotIn('self.set_task_setting(file_path, key="source_definition_path")', widget_source)
        self.assertNotIn('field.setText(self.path_to_project_relative(file_path))', widget_source)
        self.assertNotIn("self.target_properties_checkbox.setChecked(True)", widget_source)
        self.assertIn("layout.addWidget(export_properties_button)", widget_source)
        self.assertNotIn("properties_layout.addWidget(export_properties_button)", widget_source)

    def test_utilities_task_menu_order_keeps_python_first_and_rename_tasks_together(self):
        categories = modules.get_task_categories()
        utility_names = [task_class.__name__ for task_class in categories.get("Utilities")]

        expected = "TaskPythonScript"
        self.assertEqual(expected, utility_names[0])
        expected = ["TaskRename", "TaskMapHierarchy"]
        self.assertEqual(expected, utility_names[1:3])

    def test_motionbuilder_script_task_is_registered(self):
        motionbuilder_task = modules.create_task(constants.TaskType.MOTIONBUILDER_SCRIPT)

        expected = "TaskMotionBuilderScript"
        self.assertEqual(expected, motionbuilder_task.__class__.__name__)
        expected = "MotionBuilder"
        self.assertEqual(expected, motionbuilder_task.display_name)
        expected = "External"
        self.assertEqual(expected, motionbuilder_task.category)
        expected = ""
        self.assertEqual(expected, motionbuilder_task.settings.get("motionbuilder_executable"))
        self.assertIn("-batch", motionbuilder_task.settings.get("motionbuilder_arguments"))
        self.assertIn("-verbosePython", motionbuilder_task.settings.get("motionbuilder_arguments"))
        expected = ""
        self.assertEqual(expected, motionbuilder_task.settings.get("script_flag"))
        expected = "Inline"
        self.assertEqual(expected, motionbuilder_task.settings.get("script_mode"))

    def test_external_script_tasks_share_external_task_base(self):
        from gt.tools.batch_processor.tasks.task_external_script import TaskExternalScript

        self.assertTrue(issubclass(modules.TaskMotionBuilderScript, TaskExternalScript))
        self.assertTrue(issubclass(modules.TaskBlenderScript, TaskExternalScript))
        self.assertFalse(
            issubclass(modules.TaskBlenderScript, modules.TaskMotionBuilderScript)
        )

    def test_motionbuilder_command_omits_batch_context_cli_arguments(self):
        motionbuilder_task = modules.create_task(constants.TaskType.MOTIONBUILDER_SCRIPT)
        motionbuilder_task.settings["motionbuilder_arguments"] = "-batch\n-verbosePython"
        project = batch_processor_model.BatchProcessorModel()
        project.project_file_path = os.path.join(self.temp_dir, "project.batch")
        project.environment_variables["custom-dir"] = "C:/custom"
        source_path = os.path.join(self.temp_dir, "source.fbx")
        script_path = os.path.join(self.temp_dir, "mobu_script.py")
        context_path = os.path.join(self.temp_dir, "context.json")
        output_path = os.path.join(self.temp_dir, "output.fbx")
        work_item = modules.WorkItem(source_path=source_path)

        result = motionbuilder_task.build_motionbuilder_command(
            executable_path="C:/Program Files/Autodesk/MotionBuilder 2025/bin/x64/motionbuilder.exe",
            script_path=script_path,
            work_item=work_item,
            output_path=output_path,
            project=project,
            context_path=context_path,
        )

        self.assertIn("-batch", result)
        self.assertIn("-verbosePython", result)
        self.assertNotIn("-r", result)
        self.assertIn(script_path, result)
        self.assertNotIn("--input", result)
        self.assertNotIn(work_item.current_path, result)
        self.assertNotIn("--output", result)
        self.assertNotIn(output_path, result)
        self.assertNotIn("--context", result)
        self.assertNotIn(context_path, result)
        self.assertNotIn("--env-custom-dir", result)
        self.assertNotIn("--env-var", result)

    def test_motionbuilder_process_environment_passes_batch_context_values(self):
        motionbuilder_task = modules.create_task(constants.TaskType.MOTIONBUILDER_SCRIPT)
        project = batch_processor_model.BatchProcessorModel()
        project.project_file_path = os.path.join(self.temp_dir, "project.batch")
        project.environment_variables["custom-dir"] = "C:/custom"
        source_path = os.path.join(self.temp_dir, "source.fbx")
        context_path = os.path.join(self.temp_dir, "context.json")
        output_path = os.path.join(self.temp_dir, "output.fbx")
        work_item = modules.WorkItem(source_path=source_path)

        result = motionbuilder_task.build_external_process_environment(
            project=project,
            work_item=work_item,
            output_path=output_path,
            context_path=context_path,
        )

        self.assertEqual(work_item.current_path, result.get("BATCH_INPUT"))
        self.assertEqual(output_path, result.get("BATCH_OUTPUT"))
        self.assertEqual(project.project_file_path, result.get("BATCH_PROJECT"))
        self.assertEqual(project.get_project_dir(), result.get("BATCH_PROJECT_DIR"))
        self.assertEqual(motionbuilder_task.display_name, result.get("BATCH_TASK"))
        self.assertEqual(motionbuilder_task.id, result.get("BATCH_TASK_ID"))
        self.assertEqual(context_path, result.get("BATCH_CONTEXT"))
        self.assertEqual("C:/custom", result.get("BATCH_ENV_CUSTOM_DIR"))
        self.assertEqual(project.project_file_path, result.get("BATCH_ENV_PROJECT_PATH"))
        self.assertEqual(
            os.path.dirname(os.path.dirname(project.get_project_dir())),
            result.get("BATCH_ENV_PROJECT_GRANDPARENT_DIR"),
        )

    def test_motionbuilder_context_file_uses_project_path_key(self):
        motionbuilder_task = modules.create_task(constants.TaskType.MOTIONBUILDER_SCRIPT)
        project = batch_processor_model.BatchProcessorModel()
        project.project_file_path = os.path.join(self.temp_dir, "project.batch")
        work_item = modules.WorkItem(source_path=os.path.join(self.temp_dir, "source.fbx"))
        output_path = os.path.join(self.temp_dir, "output.fbx")

        context_path = motionbuilder_task.write_context_file(
            work_item=work_item,
            output_path=output_path,
            project=project,
            step_output_dir=self.temp_dir,
            script_paths=[],
            context={},
        )
        try:
            with open(context_path, "r", encoding="utf-8") as context_file:
                result = json.load(context_file)
        finally:
            os.remove(context_path)

        self.assertEqual(project.project_file_path, result.get("project_path"))
        self.assertNotIn("project_file_path", result)
        self.assertEqual(project.project_file_path, result.get("environment_variables").get("project-path"))
        self.assertEqual(
            os.path.dirname(os.path.dirname(project.get_project_dir())),
            result.get("environment_variables").get("project-grandparent-dir"),
        )

    def test_motionbuilder_legacy_script_flag_is_removed(self):
        motionbuilder_task = modules.create_task(
            constants.TaskType.MOTIONBUILDER_SCRIPT,
            settings={"script_flag": "-r"},
        )

        expected = ""
        self.assertEqual(expected, motionbuilder_task.settings.get("script_flag"))

    def test_blender_script_task_is_registered(self):
        blender_task = modules.create_task(constants.TaskType.BLENDER_SCRIPT)

        expected = "TaskBlenderScript"
        self.assertEqual(expected, blender_task.__class__.__name__)
        expected = "Blender"
        self.assertEqual(expected, blender_task.display_name)
        expected = "External"
        self.assertEqual(expected, blender_task.category)
        expected = ""
        self.assertEqual(expected, blender_task.settings.get("blender_executable"))
        expected = "Inline"
        self.assertEqual(expected, blender_task.settings.get("script_mode"))

    def test_blender_default_inline_script_opens_input_and_exports_fbx(self):
        blender_task = modules.create_task(constants.TaskType.BLENDER_SCRIPT)

        result = blender_task.settings.get("script_text")

        self.assertIn("open_input_file(input_path)", result)
        self.assertIn("export_fbx(output_path)", result)
        self.assertIn('os.path.splitext(file_path)[0] + ".fbx"', result)

    def test_blender_output_check_ignores_extension(self):
        blender_task = modules.create_task(constants.TaskType.BLENDER_SCRIPT)
        source_path = os.path.join(self.temp_dir, "source.fbx")
        expected_output_path = os.path.join(self.temp_dir, "output", "source.fbx")
        actual_output_path = os.path.join(self.temp_dir, "output", "source.abc")
        os.makedirs(os.path.dirname(actual_output_path))
        self._write_file(source_path, "source")
        self._write_file(actual_output_path, "output")
        work_item = modules.WorkItem(source_path=source_path)

        result = blender_task.finalize_output(work_item=work_item, output_path=expected_output_path)

        expected = os.path.normpath(actual_output_path)
        self.assertEqual(expected, result)

    def test_blender_output_check_rejects_different_file_name(self):
        blender_task = modules.create_task(constants.TaskType.BLENDER_SCRIPT)
        source_path = os.path.join(self.temp_dir, "source.fbx")
        expected_output_path = os.path.join(self.temp_dir, "output", "source.fbx")
        os.makedirs(os.path.dirname(expected_output_path))
        self._write_file(source_path, "source")
        self._write_file(os.path.join(self.temp_dir, "output", "different.abc"), "output")
        work_item = modules.WorkItem(source_path=source_path)

        with self.assertRaises(RuntimeError) as context:
            blender_task.finalize_output(work_item=work_item, output_path=expected_output_path)

        self.assertIn("output named 'source'", str(context.exception))

    def test_blender_command_passes_batch_context_arguments(self):
        blender_task = modules.create_task(constants.TaskType.BLENDER_SCRIPT)
        blender_task.settings["blender_arguments"] = "--background"
        blender_task.settings["script_flag"] = "--python"
        project = batch_processor_model.BatchProcessorModel()
        project.project_file_path = os.path.join(self.temp_dir, "project.batch")
        project.environment_variables["publish-dir"] = "C:/publish"
        source_path = os.path.join(self.temp_dir, "source.fbx")
        script_path = os.path.join(self.temp_dir, "blender_script.py")
        context_path = os.path.join(self.temp_dir, "context.json")
        output_path = os.path.join(self.temp_dir, "output.fbx")
        work_item = modules.WorkItem(source_path=source_path)

        result = blender_task.build_motionbuilder_command(
            executable_path="C:/Program Files/Blender Foundation/Blender 4.1/blender.exe",
            script_path=script_path,
            work_item=work_item,
            output_path=output_path,
            project=project,
            context_path=context_path,
        )

        self.assertIn("--background", result)
        self.assertIn("--python", result)
        self.assertIn(script_path, result)
        self.assertIn("--", result)
        self.assertIn("--input", result)
        self.assertIn(work_item.current_path, result)
        self.assertIn("--output", result)
        self.assertIn(output_path, result)
        self.assertIn("--context", result)
        self.assertIn(context_path, result)
        self.assertIn("--env-publish-dir", result)
        self.assertIn("C:/publish", result)
        self.assertIn("--env-var", result)
        self.assertIn("publish-dir=C:/publish", result)

    def test_blender_candidates_include_default_windows_install_path(self):
        with mock.patch("sys.platform", "win32"):
            with mock.patch.dict(os.environ, {"PROGRAMFILES": "C:\\Program Files"}, clear=False):
                result = modules.get_blender_executable_candidates("4.1")

        expected = os.path.normpath("C:\\Program Files\\Blender Foundation\\Blender 4.1\\blender.exe")
        self.assertIn(expected, result)

    def test_external_app_widgets_do_not_add_redundant_run_task_button(self):
        motionbuilder_widget_path = os.path.join(
            package_root_dir,
            "tools",
            "batch_processor",
            "widgets",
            "attr_widget_external_mobu.py",
        )
        blender_widget_path = os.path.join(
            package_root_dir,
            "tools",
            "batch_processor",
            "widgets",
            "attr_widget_external_blender.py",
        )
        with open(motionbuilder_widget_path, "r", encoding="utf-8") as widget_file:
            motionbuilder_source = widget_file.read()
        with open(blender_widget_path, "r", encoding="utf-8") as widget_file:
            blender_source = widget_file.read()

        self.assertNotIn("Run MotionBuilder Task", motionbuilder_source)
        self.assertNotIn("Run Blender Task", blender_source)
        self.assertNotIn("add_run_selected_task_button", motionbuilder_source)

    def test_task_action_buttons_use_batch_controller_resolver(self):
        widget_path = os.path.join(
            package_root_dir,
            "tools",
            "batch_processor",
            "widgets",
            "attr_widget_task.py",
        )
        base_widget_path = os.path.join(
            package_root_dir,
            "tools",
            "batch_processor",
            "widgets",
            "attr_widget_base.py",
        )
        controller_path = os.path.join(
            package_root_dir,
            "tools",
            "batch_processor",
            "batch_processor_controller.py",
        )
        with open(widget_path, "r", encoding="utf-8") as widget_file:
            widget_source = widget_file.read()
        with open(base_widget_path, "r", encoding="utf-8") as base_widget_file:
            base_widget_source = base_widget_file.read()
        with open(controller_path, "r", encoding="utf-8") as controller_file:
            controller_source = controller_file.read()

        self.assertIn("def get_batch_controller", base_widget_source)
        self.assertIn("controller = self.get_batch_controller()", widget_source)
        self.assertIn("run_to_task_id=self.task.id", widget_source)
        self.assertIn("force_single_instance=bool(getattr(self.task, \"is_aggregate_task\", False))", widget_source)
        self.assertIn("controller=self", controller_source)

    def test_motionbuilder_candidates_include_default_windows_install_path(self):
        with mock.patch("sys.platform", "win32"):
            with mock.patch.dict(os.environ, {"PROGRAMFILES": "C:\\Program Files"}, clear=False):
                result = modules.get_motionbuilder_executable_candidates("2025")

        expected = os.path.normpath(
            "C:\\Program Files\\Autodesk\\MotionBuilder 2025\\bin\\x64\\motionbuilder.exe"
        )
        self.assertIn(expected, result)

    def test_external_process_log_path_uses_project_log_dir(self):
        motionbuilder_task = modules.create_task(constants.TaskType.MOTIONBUILDER_SCRIPT)
        project = batch_processor_model.BatchProcessorModel()
        project.project_file_path = os.path.join(self.temp_dir, "project.batch")
        output_path = os.path.join(self.temp_dir, "02_tasks", "01_motionbuilder", "source.fbx")
        step_output_dir = os.path.dirname(output_path)
        script_path = os.path.join(self.temp_dir, "scripts", "strip_geo.py")

        result = motionbuilder_task.build_process_log_path(
            output_path=output_path,
            step_output_dir=step_output_dir,
            script_path=script_path,
            project=project,
        )

        expected = os.path.normpath(os.path.join(self.temp_dir, "logs", "source_strip_geo_motionbuilder.log"))
        self.assertEqual(expected, result)

    def test_external_process_log_records_input_and_output_paths(self):
        motionbuilder_task = modules.create_task(constants.TaskType.MOTIONBUILDER_SCRIPT)
        log_path = os.path.join(self.temp_dir, "logs", "process.log")
        input_path = os.path.join(self.temp_dir, "input.fbx")
        output_path = os.path.join(self.temp_dir, "output.fbx")
        script_path = os.path.join(self.temp_dir, "script.py")
        context_path = os.path.join(self.temp_dir, "context.json")

        motionbuilder_task.write_process_log(
            log_path=log_path,
            command=["motionbuilder.exe", "-batch", script_path],
            return_code="LAUNCH",
            input_path=input_path,
            output_path=output_path,
            script_path=script_path,
            context_path=context_path,
        )
        with open(log_path, "r", encoding="utf-8") as log_file:
            result = log_file.read()

        self.assertIn("Input Path: {0}".format(input_path), result)
        self.assertIn("Output Path: {0}".format(output_path), result)
        self.assertIn("Script Path: {0}".format(script_path), result)
        self.assertIn("Context Path: {0}".format(context_path), result)

    def test_motionbuilder_inline_temp_names_do_not_use_gt_prefix(self):
        motionbuilder_task = modules.create_task(constants.TaskType.MOTIONBUILDER_SCRIPT)
        motionbuilder_task.set_script_mode("Inline")
        script_paths, temporary_paths = motionbuilder_task.get_runtime_script_paths(
            batch_processor_model.BatchProcessorModel()
        )

        try:
            self.assertTrue(os.path.basename(script_paths[0]).startswith("mobu_inline_"))
            self.assertFalse(os.path.basename(script_paths[0]).startswith("gt_"))
        finally:
            motionbuilder_task.cleanup_temporary_paths(temporary_paths)

    def test_preferred_maya_version_falls_back_with_warning(self):
        with mock.patch.object(
            batch_processor_worker,
            "find_current_mayapy_executable",
            return_value="C:/Current/Maya/bin/mayapy.exe",
        ):
            with mock.patch.object(batch_processor_worker, "find_mayapy_for_version", return_value=""):
                result_path, result_warning = batch_processor_worker.resolve_mayapy_executable(
                    preferred_version="2027"
                )

        expected = "C:/Current/Maya/bin/mayapy.exe"
        self.assertEqual(expected, result_path)
        self.assertIn("2027", result_warning)
        self.assertIn("Falling back", result_warning)

    def test_legacy_task_type_keys_are_migrated(self):
        import_task = modules.create_task("maya_import")
        save_task = modules.create_task("maya_save")
        usd_task = modules.create_task("usd_export")

        expected = constants.TaskType.MAYA_IMPORT
        self.assertEqual(expected, import_task.task_type)
        expected = constants.TaskType.MAYA_SAVE
        self.assertEqual(expected, save_task.task_type)
        expected = constants.TaskType.USD_EXPORT
        self.assertEqual(expected, usd_task.task_type)

    def test_maya_import_and_save_tasks_are_registered(self):
        import_task = modules.create_task(constants.TaskType.MAYA_IMPORT)
        save_task = modules.create_task(constants.TaskType.MAYA_SAVE)
        script_task = modules.create_task(constants.TaskType.PYTHON_SCRIPT)

        expected = constants.TaskType.MAYA_IMPORT
        self.assertEqual(expected, import_task.task_type)
        expected = constants.TaskType.MAYA_SAVE
        self.assertEqual(expected, save_task.task_type)
        expected = constants.TaskType.PYTHON_SCRIPT
        self.assertEqual(expected, script_task.task_type)
        self.assertIn("source_path", import_task.settings)
        self.assertIn("target_path", save_task.settings)

    def test_maya_import_task_validates_scene_options(self):
        import_task = modules.TaskMayaImport(
            settings={
                "set_framerate": True,
                "framerate": 0,
                "set_scene_scale": True,
                "scene_scale": "bad",
                "set_scene_up_axis": True,
                "scene_up_axis": "X",
            }
        )

        result = import_task.validate(None)

        self.assertFalse(result.is_valid())
        self.assertTrue(any("framerate" in error for error in result.errors))
        self.assertTrue(any("scene scale" in error for error in result.errors))
        self.assertTrue(any("up axis" in error for error in result.errors))

    def test_usd_export_task_validates_settings(self):
        usd_task = modules.TaskExportUsd()

        result = usd_task.validate(None)

        self.assertTrue(result.is_valid())

        usd_task.settings["usd_format"] = "FBX"
        result = usd_task.validate(None)

        self.assertFalse(result.is_valid())
        self.assertTrue(any("USD format" in error for error in result.errors))

    def test_usd_export_utility_defaults_match_task_defaults(self):
        result = utils_usd.build_export_options({})

        expected = False
        self.assertEqual(expected, result.get("force_z_up"))
        expected = False
        self.assertEqual(expected, result.get("zero_root_rotation"))
        expected = True
        self.assertEqual(expected, result.get("export_blend_shapes"))
        expected = []
        self.assertEqual(expected, result.get("native_custom_attributes"))
        expected = []
        self.assertEqual(expected, result.get("custom_data_attributes"))

        exporter = utils_usd.UsdExporter(**result)
        self.assertFalse(exporter.force_z_up)
        self.assertFalse(exporter.zero_root_rotation)
        self.assertTrue(exporter.export_blend_shapes)
        self.assertEqual([], exporter.native_custom_attributes)
        self.assertEqual([], exporter.custom_data_attributes)

    def test_usd_export_retries_without_invalid_command_flag(self):
        exporter = utils_usd.UsdExporter()
        export_calls = []

        def export_command(**kwargs):
            """Mock USD export command.

            Args:
                **kwargs: Export keyword arguments.
            """
            export_calls.append(dict(kwargs))
            if "upAxis" in kwargs:
                raise TypeError("Invalid flag 'upAxis'")

        exporter.run_export_command(
            export_command=export_command,
            export_kwargs={"file": "output.usd", "selection": True, "upAxis": "z"},
        )

        expected = 2
        self.assertEqual(expected, len(export_calls))
        self.assertIn("upAxis", export_calls[0])
        self.assertNotIn("upAxis", export_calls[1])

    def test_zip_archive_version_is_task_specific(self):
        model = batch_processor_model.BatchProcessorModel()
        model.project_name = "Project"
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        zip_task = modules.create_task(constants.TaskType.ZIP_COMPRESS)
        zip_task.settings["archive_name"] = "{project-name}_{version}.zip"
        zip_task.settings["archive_version"] = "07"
        output_dir = os.path.join(self.temp_dir, "output")

        result = zip_task.build_archive_path(project=model, step_output_dir=output_dir)

        self.assertTrue(result.endswith(os.path.normpath("Project_07.zip")))
        expected = "{version}"
        self.assertEqual(expected, model.resolve_template("{version}", task=zip_task))

    def test_zip_archive_run_once_setting_defaults_to_false(self):
        zip_task = modules.create_task(constants.TaskType.ZIP_COMPRESS)

        self.assertFalse(zip_task.settings.get("run_once_after_multi_instance"))
        self.assertFalse(zip_task.to_dict().get("parameters").get("run_once_after_multi_instance"))

    def test_final_zip_task_discovers_complete_source_folder(self):
        source_dir = os.path.join(self.temp_dir, "zip_source")
        nested_dir = os.path.join(source_dir, "nested")
        os.makedirs(nested_dir)
        first_path = os.path.join(source_dir, "first.fbx")
        second_path = os.path.join(nested_dir, "second.fbx")
        self._write_file(first_path, "first")
        self._write_file(second_path, "second")
        model = batch_processor_model.BatchProcessorModel()
        zip_task = model.add_module(modules.create_task(constants.TaskType.ZIP_COMPRESS))
        zip_task.settings["source_path"] = source_dir
        zip_task.settings["source_include_subdirectories"] = True

        result = batch_processor_multi_worker.discover_final_task_work_items(
            project=model,
            task=zip_task,
            batch_processor_worker=batch_processor_worker,
            tasks=modules,
        )

        result_paths = [item.current_path for item in result]
        self.assertIn(os.path.normpath(source_dir), result_paths)
        self.assertIn(os.path.normpath(first_path), result_paths)
        self.assertIn(os.path.normpath(second_path), result_paths)

    def test_zip_archive_auto_detects_next_version(self):
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(output_dir)
        self._write_file(os.path.join(output_dir, "Project_01.zip"), "existing zip")
        zip_task = modules.create_task(constants.TaskType.ZIP_COMPRESS)
        zip_task.settings["archive_name"] = "Project_{version}.zip"
        zip_task.settings["archive_version_auto"] = True
        zip_task.settings["archive_version_padding"] = 2

        result = zip_task.build_archive_path(project=model, step_output_dir=output_dir)

        self.assertTrue(result.endswith(os.path.normpath("Project_02.zip")))

    def test_zip_archive_compresses_folder_sources_recursively(self):
        source_dir = os.path.join(self.temp_dir, "source")
        nested_dir = os.path.join(source_dir, "nested")
        empty_dir = os.path.join(source_dir, "empty")
        output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(nested_dir)
        os.makedirs(empty_dir)
        self._write_file(os.path.join(source_dir, "root.txt"), "root")
        self._write_file(os.path.join(nested_dir, "child.txt"), "child")
        zip_task = modules.create_task(constants.TaskType.ZIP_COMPRESS)
        zip_task.settings["archive_name"] = "archive.zip"
        work_item = modules.WorkItem(source_path=source_dir)

        result = zip_task.execute(
            work_item=None,
            project=batch_processor_model.BatchProcessorModel(),
            step_output_dir=output_dir,
            context={"work_items": [work_item]},
        )

        with zipfile.ZipFile(result.current_path, "r") as zip_file:
            result_names = sorted(zip_file.namelist())
        expected = ["empty/", "nested/", "nested/child.txt", "root.txt"]
        self.assertEqual(expected, result_names)
        expected = 2
        self.assertEqual(expected, result.metadata.get("compressed_files"))

    def test_zip_source_path_root_forces_relative_folder_layout(self):
        source_dir = os.path.join(self.temp_dir, "source")
        nested_dir = os.path.join(source_dir, "nested")
        empty_dir = os.path.join(source_dir, "empty")
        output_dir = os.path.join(self.temp_dir, "output")
        os.makedirs(nested_dir)
        os.makedirs(empty_dir)
        self._write_file(os.path.join(source_dir, "root.txt"), "root")
        self._write_file(os.path.join(nested_dir, "child.txt"), "child")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        zip_task = modules.create_task(constants.TaskType.ZIP_COMPRESS)
        zip_task.settings["archive_name"] = "archive.zip"
        zip_task.settings["source_path"] = source_dir
        zip_task.settings["source_include_subdirectories"] = True
        zip_task.settings["use_source_path_as_relative_root"] = True
        zip_task.settings["preserve_relative_paths"] = False
        work_items = [
            modules.WorkItem(source_path=source_path)
            for source_path in zip_task.discover_source_files(project=model)
        ]

        result = zip_task.execute(
            work_item=None,
            project=model,
            step_output_dir=output_dir,
            context={"work_items": work_items},
        )

        with zipfile.ZipFile(result.current_path, "r") as zip_file:
            result_names = sorted(zip_file.namelist())
        expected = ["empty/", "nested/", "nested/child.txt", "root.txt"]
        self.assertEqual(expected, result_names)

    def test_zip_source_discovery_includes_folders(self):
        source_dir = os.path.join(self.temp_dir, "source")
        nested_dir = os.path.join(source_dir, "nested")
        empty_dir = os.path.join(source_dir, "empty")
        os.makedirs(nested_dir)
        os.makedirs(empty_dir)
        self._write_file(os.path.join(nested_dir, "child.txt"), "child")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        zip_task = modules.create_task(constants.TaskType.ZIP_COMPRESS)
        zip_task.settings["source_path"] = source_dir
        zip_task.settings["source_include_subdirectories"] = True

        result = zip_task.discover_source_files(project=model)

        expected = [
            os.path.normpath(empty_dir),
            os.path.normpath(nested_dir),
            os.path.normpath(os.path.join(nested_dir, "child.txt")),
            os.path.normpath(source_dir),
        ]
        self.assertEqual(sorted(expected), sorted(result))

    def test_map_hierarchy_records_snapshot_mapping_for_renamed_files(self):
        from gt.tools.batch_processor.tasks import task_map_hierarchy

        source_dir = os.path.join(self.temp_dir, "source")
        target_dir = os.path.join(self.temp_dir, "target")
        os.makedirs(source_dir)
        os.makedirs(os.path.join(target_dir, "renamed"))
        self._write_file(os.path.join(source_dir, "old_name.ma"), "same data")
        self._write_file(os.path.join(target_dir, "renamed", "new_name.ma"), "same data")
        snapshot_path = os.path.join(self.temp_dir, "hierarchy_snapshot.json")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        task = modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_RECORD_SOURCE_TARGET,
                "source_dir": source_dir,
                "target_dir": target_dir,
                "snapshot_path": snapshot_path,
            }
        )

        result = task.validate(model)
        self.assertTrue(result.is_valid())
        task.execute(None, model, self.temp_dir, context={"work_items": []})

        with open(snapshot_path, "r", encoding="utf-8") as snapshot_file:
            payload = json.load(snapshot_file)
        expected = 1
        self.assertEqual(expected, payload.get("metadata").get("modifications_required"))
        file_entries = [entry for entry in payload.get("mapping") if entry.get("type") == "file"]
        expected = "old_name.ma"
        self.assertEqual(expected, file_entries[0].get("original_relative_path"))
        expected = "renamed/new_name.ma"
        self.assertEqual(expected, file_entries[0].get("target_relative_path"))
        expected = task_map_hierarchy.STATUS_MOVED
        self.assertEqual(expected, file_entries[0].get("status"))

    def test_map_hierarchy_applies_mapping_forward_and_is_idempotent(self):
        from gt.tools.batch_processor.tasks import task_map_hierarchy

        work_dir = os.path.join(self.temp_dir, "work")
        os.makedirs(work_dir)
        self._write_file(os.path.join(work_dir, "old_name.ma"), "same data")
        snapshot_path = os.path.join(self.temp_dir, "hierarchy_snapshot.json")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        record_task = modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_RECORD_SOURCE,
                "source_dir": work_dir,
                "snapshot_path": snapshot_path,
            }
        )
        record_task.execute(None, model, self.temp_dir, context={"work_items": []})

        # Manually author a target state into the snapshot so the mapping renames the file.
        with open(snapshot_path, "r", encoding="utf-8") as snapshot_file:
            payload = json.load(snapshot_file)
        payload["target_entries"] = {
            "files": [dict(payload["source_entries"]["files"][0], relative_path="renamed/new_name.ma")],
            "folders": ["renamed"],
        }
        payload["mapping"] = task_map_hierarchy.compute_mapping(
            payload["source_entries"], payload["target_entries"]
        )
        with open(snapshot_path, "w", encoding="utf-8") as snapshot_file:
            json.dump(payload, snapshot_file)

        apply_task = modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_APPLY_FORWARD,
                "apply_dir": work_dir,
                "use_apply_dir": True,
                "snapshot_path": snapshot_path,
                "write_report": False,
            }
        )
        apply_task.execute(None, model, self.temp_dir, context={"work_items": []})

        self.assertFalse(os.path.isfile(os.path.join(work_dir, "old_name.ma")))
        self.assertTrue(os.path.isfile(os.path.join(work_dir, "renamed", "new_name.ma")))

        # Running again must not raise or move anything (idempotent).
        apply_task.execute(None, model, self.temp_dir, context={"work_items": []})
        self.assertTrue(os.path.isfile(os.path.join(work_dir, "renamed", "new_name.ma")))

    def test_map_hierarchy_applies_to_parallel_directory_ignoring_extensions(self):
        from gt.tools.batch_processor.tasks import task_map_hierarchy

        source_dir = os.path.join(self.temp_dir, "source")
        target_dir = os.path.join(self.temp_dir, "target")
        parallel_dir = os.path.join(self.temp_dir, "parallel")
        os.makedirs(source_dir)
        os.makedirs(os.path.join(target_dir, "renamed"))
        os.makedirs(parallel_dir)
        self._write_file(os.path.join(source_dir, "old_name.ma"), "same data")
        self._write_file(os.path.join(target_dir, "renamed", "new_name.ma"), "same data")
        self._write_file(os.path.join(parallel_dir, "old_name.fbx"), "unrelated fbx data")
        snapshot_path = os.path.join(self.temp_dir, "hierarchy_snapshot.json")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        record_task = modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_RECORD_SOURCE_TARGET,
                "source_dir": source_dir,
                "target_dir": target_dir,
                "snapshot_path": snapshot_path,
            }
        )
        record_task.execute(None, model, self.temp_dir, context={"work_items": []})

        parallel_task = modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_APPLY_PARALLEL_FORWARD,
                "apply_dir": parallel_dir,
                "use_apply_dir": True,
                "snapshot_path": snapshot_path,
                "write_report": False,
            }
        )
        parallel_task.execute(None, model, self.temp_dir, context={"work_items": []})

        self.assertFalse(os.path.isfile(os.path.join(parallel_dir, "old_name.fbx")))
        self.assertTrue(os.path.isfile(os.path.join(parallel_dir, "renamed", "new_name.fbx")))

        # Reverting the parallel directory undoes the change using base-name matching.
        revert_task = modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_REVERT_PARALLEL_BACKWARD,
                "apply_dir": parallel_dir,
                "use_apply_dir": True,
                "snapshot_path": snapshot_path,
                "write_report": False,
            }
        )
        revert_task.execute(None, model, self.temp_dir, context={"work_items": []})

        self.assertTrue(os.path.isfile(os.path.join(parallel_dir, "old_name.fbx")))
        self.assertFalse(os.path.isfile(os.path.join(parallel_dir, "renamed", "new_name.fbx")))

    def test_map_hierarchy_copy_source_and_apply_leaves_source_intact(self):
        from gt.tools.batch_processor.tasks import task_map_hierarchy

        source_dir = os.path.join(self.temp_dir, "source")
        target_dir = os.path.join(self.temp_dir, "target")
        apply_dir = os.path.join(self.temp_dir, "apply")
        os.makedirs(source_dir)
        os.makedirs(os.path.join(target_dir, "renamed"))
        os.makedirs(apply_dir)
        self._write_file(os.path.join(source_dir, "old_name.ma"), "same data")
        self._write_file(os.path.join(target_dir, "renamed", "new_name.ma"), "same data")
        snapshot_path = os.path.join(self.temp_dir, "hierarchy_snapshot_data.json")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_RECORD_SOURCE_TARGET,
                "source_dir": source_dir,
                "target_dir": target_dir,
                "snapshot_path": snapshot_path,
            }
        ).execute(None, model, self.temp_dir, context={"work_items": []})

        copy_task = modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_COPY_APPLY_FORWARD,
                "source_dir": source_dir,
                "apply_dir": apply_dir,
                "use_apply_dir": True,
                "snapshot_path": snapshot_path,
                "write_report": False,
            }
        )
        result = copy_task.validate(model)
        self.assertTrue(result.is_valid())
        copy_task.execute(None, model, self.temp_dir, context={"work_items": []})

        # Source is untouched, apply directory receives the target structure.
        self.assertTrue(os.path.isfile(os.path.join(source_dir, "old_name.ma")))
        self.assertTrue(os.path.isfile(os.path.join(apply_dir, "renamed", "new_name.ma")))

    def test_map_hierarchy_copy_source_blocks_when_apply_overlaps_source(self):
        from gt.tools.batch_processor.tasks import task_map_hierarchy

        source_dir = os.path.join(self.temp_dir, "source")
        os.makedirs(source_dir)
        self._write_file(os.path.join(source_dir, "old_name.ma"), "same data")
        snapshot_path = os.path.join(self.temp_dir, "hierarchy_snapshot_data.json")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_RECORD_SOURCE,
                "source_dir": source_dir,
                "snapshot_path": snapshot_path,
            }
        ).execute(None, model, self.temp_dir, context={"work_items": []})

        copy_task = modules.TaskMapHierarchy(
            settings={
                "mode": task_map_hierarchy.MODE_COPY_APPLY_FORWARD,
                "source_dir": source_dir,
                "apply_dir": source_dir,
                "use_apply_dir": True,
                "snapshot_path": snapshot_path,
            }
        )
        result = copy_task.validate(model)
        self.assertFalse(result.is_valid())

    def test_delete_path_task_blocks_outside_project_by_default(self):
        outside_dir = tempfile.mkdtemp(prefix="gt_batch_processor_outside_")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        task = modules.TaskDeleteProjectFiles(settings={"delete_path": outside_dir})
        try:
            result = task.validate(model)
        finally:
            shutil.rmtree(outside_dir)

        self.assertFalse(result.is_valid())
        self.assertTrue(any("outside of the project directory" in error for error in result.errors))

    def test_delete_path_task_allows_outside_project_when_enabled(self):
        outside_dir = tempfile.mkdtemp(prefix="gt_batch_processor_outside_")
        file_path = os.path.join(outside_dir, "temp.cache")
        self._write_file(file_path, "delete me")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        task = modules.TaskDeleteProjectFiles(
            settings={
                "delete_path": outside_dir,
                "allow_out_of_project_deletion": True,
                "dry_run": False,
                "write_report": False,
            }
        )
        try:
            result = task.validate(model)
            self.assertTrue(result.is_valid())
            task.execute(None, model, self.temp_dir, context={"work_items": []})
            self.assertFalse(os.path.isfile(file_path))
        finally:
            shutil.rmtree(outside_dir)

    def test_delete_path_task_dry_run_preserves_files(self):
        delete_dir = os.path.join(self.temp_dir, "generated")
        os.makedirs(delete_dir)
        file_path = os.path.join(delete_dir, "temp.cache")
        self._write_file(file_path, "delete me")
        report_path = os.path.join(self.temp_dir, "delete_report.json")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        task = modules.TaskDeleteProjectFiles(
            settings={
                "delete_path": delete_dir,
                "report_path": report_path,
                "dry_run": True,
            }
        )

        result = task.validate(model)
        self.assertTrue(result.is_valid())
        task.execute(None, model, self.temp_dir, context={"work_items": []})

        self.assertTrue(os.path.isfile(file_path))
        self.assertTrue(os.path.isfile(report_path))

    def test_delete_path_task_can_run_selected_without_work_items(self):
        delete_dir = os.path.join(self.temp_dir, "generated")
        os.makedirs(delete_dir)
        file_path = os.path.join(delete_dir, "temp.cache")
        self._write_file(file_path, "delete me")
        report_path = os.path.join(self.temp_dir, "delete_report.json")
        model = batch_processor_model.BatchProcessorModel()
        model.project_file_path = os.path.join(self.temp_dir, "project.batch")
        delete_task = model.add_task(
            modules.TaskDeleteProjectFiles(
                settings={
                    "delete_path": delete_dir,
                    "report_path": report_path,
                    "dry_run": True,
                }
            )
        )
        runner = batch_processor_worker.SingleInstanceBatchRunner()

        result = runner.run(model, run_from_task_id=delete_task.id, run_to_task_id=delete_task.id)

        self.assertEqual("succeeded", result.status)
        self.assertTrue(os.path.isfile(file_path))
        self.assertTrue(os.path.isfile(report_path))

    def _write_file(self, file_path, content):
        """Writes a small test file.

        Args:
            file_path (str): File path to write.
            content (str): File content.
        """
        with open(file_path, "w", encoding="utf-8") as test_file:
            test_file.write(content)


if __name__ == "__main__":
    unittest.main()
