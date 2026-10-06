"""Regression tests for input folders produced by earlier batch segments."""

import os
import tempfile
import unittest

from gt.tools.batch_processor import batch_processor_model as model
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_worker as worker
from gt.tools.batch_processor.tasks import task_input_pairs as pairs


class TestInputDirectoryValidation(unittest.TestCase):
    """Checks per-task folder validation, persistence, and segment execution."""

    def setUp(self):
        """Creates a disposable project without any generated input directories."""
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.project = model.BatchProcessorModel()
        self.project.environment_variables["project-dir"] = self.directory.name
        self.project.run_settings["create_log"] = False
        self.project.run_settings["create_task_time_log"] = False
        self.missing_directory = os.path.join(self.directory.name, "generated")

    def test_new_and_loaded_tasks_require_existing_directories_by_default(self):
        """Keeps strict validation for new tasks and projects without the new setting."""
        for task_class in (tasks.TaskInput, tasks.TaskInputPairs):
            with self.subTest(task_type=task_class.task_type):
                task = tasks.create_task_from_dict({
                    "task_type": task_class.task_type,
                    "parameters": {"source_path": self.missing_directory},
                })
                self.assertEqual(False, task_class().settings["allow_missing_input_directory"])
                self.assertEqual(False, task.settings["allow_missing_input_directory"])
                expected = f"Input directory does not exist: {self.missing_directory}"
                self.assertIn(expected, task.validate(self.project).errors)

    def test_allowed_missing_directories_warn_without_creating_them(self):
        """Allows preflight and discovery to wait for generated folders without writing them."""
        for task_class in (tasks.TaskInput, tasks.TaskInputPairs):
            with self.subTest(task_type=task_class.task_type):
                task = task_class(settings={
                    "source_path": self.missing_directory,
                    "allow_missing_input_directory": True,
                })
                result = task.validate(self.project)
                self.assertEqual([], result.errors)
                self.assertEqual(1, len(result.warnings))
                self.assertIn(self.missing_directory, result.warnings[0])
                self.assertEqual([], task.discover_files(self.project))
                self.assertEqual([], task.prepare(self.project))
                self.assertFalse(os.path.exists(self.missing_directory))

    def test_allowing_one_missing_directory_keeps_other_input_validation(self):
        """Scopes the opt-in setting to the selected input task."""
        deferred_input = tasks.TaskInput(settings={
            "source_path": self.missing_directory,
            "allow_missing_input_directory": True,
        })
        required_directory = os.path.join(self.directory.name, "required")
        required_input = tasks.TaskInput(settings={"source_path": required_directory})
        self.project.tasks = [deferred_input, required_input]
        expected = [f"Input directory does not exist: {required_directory}"]
        self.assertEqual(expected, self.project.validate_project().errors)

    def test_existing_file_cannot_be_used_as_an_allowed_missing_directory(self):
        """Keeps a file supplied as a folder path invalid with the option enabled."""
        with open(self.missing_directory, "w", encoding="utf-8") as input_file:
            input_file.write("Existing input must be preserved.")
        for task_class in (tasks.TaskInput, tasks.TaskInputPairs):
            with self.subTest(task_type=task_class.task_type):
                task = task_class(settings={
                    "source_path": self.missing_directory,
                    "allow_missing_input_directory": True,
                })
                expected = f"Input directory does not exist: {self.missing_directory}"
                self.assertIn(expected, task.validate(self.project).errors)

    def test_project_save_load_preserves_each_tasks_setting(self):
        """Saves the option in task parameters while other tasks keep the strict default."""
        self.project.tasks = [tasks.TaskInput(), tasks.TaskInputPairs(), tasks.TaskInput()]
        for task in self.project.tasks[:2]:
            task.settings["allow_missing_input_directory"] = True
        project_path = os.path.join(self.directory.name, "project.batch")
        self.project.save_to_file(project_path)
        restored_project = model.BatchProcessorModel.from_file(project_path)
        expected = [True, True, False]
        restored_settings = [task.settings["allow_missing_input_directory"] for task in restored_project.tasks]
        self.assertEqual(expected, restored_settings)

    def test_explicit_file_diagnostics_are_preserved(self):
        """Keeps unresolved explicit file warnings when the folder option is enabled."""
        task = tasks.TaskInput(settings={
            "source_path": self.missing_directory,
            "allow_missing_input_directory": True,
            "explicit_files": ["missing.ma"],
        })
        expected = ["Explicit input file entries did not resolve: 1"]
        self.assertEqual(expected, task.validate(self.project).warnings)

    def test_invalid_folder_pairs_remain_invalid(self):
        """Keeps unsafe pair paths invalid even when their folder will be generated."""
        task = tasks.TaskInputPairs(settings={
            "source_path": self.missing_directory,
            "allow_missing_input_directory": True,
            "folder_pairs": [pairs.create_pair("../outside.ma", "Description")],
        })
        result = task.validate(self.project)
        self.assertEqual(1, len(result.errors))
        self.assertIn("must stay relative to the input folder", result.errors[0])

    def test_empty_and_unset_pair_folders_still_fail_validation(self):
        """Skips availability checks only while a configured folder is missing."""
        for source_path in (self.directory.name, ""):
            with self.subTest(source_path=source_path):
                task = tasks.TaskInputPairs(settings={
                    "source_path": source_path,
                    "allow_missing_input_directory": True,
                })
                expected = "Add at least one active, available input pair with a file name."
                self.assertIn(expected, task.validate(self.project).errors)

    def test_manual_pair_validation_is_preserved(self):
        """Keeps manual pair name and active input validation independent of the folder option."""
        for manual_pairs in ([], [pairs.create_pair("CON", "Description")]):
            with self.subTest(manual_pairs=manual_pairs):
                task = tasks.TaskInputPairs(settings={
                    "input_mode": pairs.INPUT_MODE_MANUAL,
                    "allow_missing_input_directory": True,
                    "manual_pairs": manual_pairs,
                })
                self.assertTrue(task.validate(self.project).errors)

    def test_later_segment_discovers_files_created_by_an_earlier_segment(self):
        """Runs two real file-copy segments with no pre-created intermediate folder."""
        source_directory = os.path.join(self.directory.name, "source")
        os.makedirs(source_directory)
        source_path = os.path.join(source_directory, "clip.ma")
        with open(source_path, "w", encoding="utf-8") as input_file:
            input_file.write("// Disposable input contents.\n")
        for task_class in (tasks.TaskInput, tasks.TaskInputPairs):
            with self.subTest(task_type=task_class.task_type):
                generated_directory = os.path.join(self.directory.name, task_class.task_type, "generated")
                final_directory = os.path.join(self.directory.name, task_class.task_type, "processed")
                generated_input = task_class(settings={
                    "source_path": generated_directory,
                    "start_new_input_list": True,
                    "allow_missing_input_directory": True,
                })
                self.project.tasks = [
                    tasks.TaskInput(settings={"source_path": source_directory}),
                    tasks.TaskRename(settings={
                        "target_path": generated_directory, "name_template": "generated_{name}",
                    }),
                    generated_input,
                    tasks.TaskRename(settings={
                        "target_path": final_directory, "name_template": "processed_{name}",
                    }),
                ]
                self.assertFalse(os.path.exists(generated_directory))
                self.assertEqual([], self.project.validate_project().errors)
                tracker = worker.SingleInstanceBatchRunner().run(self.project)
                expected = os.path.join(final_directory, "processed_generated_clip.ma")
                self.assertTrue(os.path.isfile(expected))
                with open(expected, encoding="utf-8") as output_file:
                    self.assertEqual("// Disposable input contents.\n", output_file.read())
                self.assertEqual(2, tracker.succeeded)
                self.assertEqual(0, tracker.failed)
                self.assertTrue(os.path.isfile(source_path))

    def test_allowing_missing_directory_does_not_make_an_empty_run_succeed(self):
        """Still fails processing if no earlier task produced the required inputs."""
        self.project.tasks = [
            tasks.TaskInput(settings={
                "source_path": self.missing_directory,
                "allow_missing_input_directory": True,
            }),
            tasks.TaskRename(settings={"target_path": os.path.join(self.directory.name, "processed")}),
        ]
        self.assertEqual([], self.project.validate_project().errors)
        with self.assertRaises(RuntimeError):
            worker.SingleInstanceBatchRunner().run(self.project)
        self.assertFalse(os.path.exists(self.missing_directory))


if __name__ == "__main__":
    unittest.main(verbosity=2)
