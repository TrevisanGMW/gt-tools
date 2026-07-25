"""
Batch Processor Delete Project Files Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tasks import task_utils
import fnmatch
import os


class TaskDeleteProjectFiles(task_base.BatchTask):
    """Task that safely deletes generated files inside the active project folder."""

    task_type = constants.TaskType.DELETE_PROJECT_FILES
    default_display_name = "Delete Project Files"
    default_target_path_template = "{previous-task-path}"
    icon = ui_res_lib.Icon.ui_delete
    category = "Utilities"
    category_icon = ui_res_lib.Icon.root_utilities
    is_aggregate_task = True
    is_delete_task = True

    def get_default_settings(self):
        """Gets default delete task settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "delete_path": "{previous-task-path}",
            "include_subdirectories": True,
            "delete_files": True,
            "delete_empty_dirs": True,
            "patterns": ["*"],
            "exclude_patterns": [],
            "dry_run": True,
            "write_report": True,
            "report_path": "{project-dir}/logs/delete_project_files_{task-idx}.json",
        }

    def validate(self, project):
        """Validates delete task settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        delete_path = self.get_delete_path(project)
        safety_result = self.validate_delete_path(project, delete_path)
        result.errors.extend(safety_result.errors)
        result.warnings.extend(safety_result.warnings)
        if not self.settings.get("delete_files") and not self.settings.get("delete_empty_dirs"):
            result.add_warning("Delete Project Files has both file and empty-directory deletion disabled.")
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Deletes configured files and returns incoming work items unchanged.

        Args:
            work_item (WorkItem): Unused aggregate work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Cooked output folder.
            context (dict, optional): Runtime context containing work_items.

        Returns:
            list: Incoming work items.
        """
        context = context or {}
        work_items = context.get("work_items") or []
        delete_path = self.get_delete_path(project)
        safety_result = self.validate_delete_path(project, delete_path)
        if safety_result.errors:
            raise RuntimeError("; ".join(safety_result.errors))
        if not os.path.isdir(delete_path):
            raise task_base.TaskSkip("Delete path does not exist: {0}".format(delete_path))
        file_paths = self.collect_files(delete_path)
        directory_paths = self.collect_empty_directories(delete_path) if self.settings.get("delete_empty_dirs") else []
        deleted_files = []
        deleted_dirs = []
        if not self.settings.get("dry_run", True):
            if self.settings.get("delete_files", True):
                for file_path in file_paths:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        deleted_files.append(file_path)
            if self.settings.get("delete_empty_dirs", True):
                for directory_path in directory_paths:
                    try:
                        os.rmdir(directory_path)
                        deleted_dirs.append(directory_path)
                    except OSError:
                        pass
        report_path = project.resolve_template_path(self.settings.get("report_path"), task=self)
        if self.settings.get("write_report", True) and report_path:
            task_utils.write_json_log(
                report_path,
                {
                    "version": 1,
                    "created_at": task_utils.get_timestamp(),
                    "dry_run": bool(self.settings.get("dry_run", True)),
                    "delete_path": delete_path,
                    "matched_files": file_paths,
                    "matched_empty_dirs": directory_paths,
                    "deleted_files": deleted_files,
                    "deleted_empty_dirs": deleted_dirs,
                    "warnings": list(safety_result.warnings),
                },
            )
            task_utils.report_log_artifact(context, report_path)
        return list(work_items)

    def get_delete_path(self, project):
        """Gets the resolved delete path.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Resolved delete path.
        """
        return project.resolve_template_path(self.settings.get("delete_path"), task=self)

    def validate_delete_path(self, project, delete_path):
        """Validates delete-path safety.

        Args:
            project (BatchProcessorModel): Active project.
            delete_path (str): Resolved delete path.

        Returns:
            ValidationResult: Safety validation result.
        """
        result = task_base.ValidationResult()
        project_dir = project.get_project_dir()
        if not project_dir:
            result.add_error("Delete Project Files requires a saved or configured project directory.")
            return result
        if not delete_path:
            result.add_error("Delete Project Files path is empty.")
            return result
        project_dir = os.path.abspath(project_dir)
        delete_path = os.path.abspath(delete_path)
        try:
            common_path = os.path.commonpath([project_dir, delete_path])
        except ValueError:
            common_path = ""
        if os.path.normcase(common_path) != os.path.normcase(project_dir):
            result.add_error("Delete Project Files cannot delete outside the project path: {0}".format(delete_path))
            return result
        if os.path.normcase(project_dir) == os.path.normcase(delete_path):
            result.add_error("Delete Project Files cannot target the project root folder.")
        if not os.path.isdir(delete_path):
            result.add_warning("Delete Project Files path does not exist yet: {0}".format(delete_path))
        return result

    def collect_files(self, delete_path):
        """Collects files matching delete patterns.

        Args:
            delete_path (str): Directory to inspect.

        Returns:
            list: Matching file paths.
        """
        if not self.settings.get("delete_files", True):
            return []
        include_subdirectories = bool(self.settings.get("include_subdirectories", True))
        if include_subdirectories:
            walker = os.walk(delete_path)
        else:
            walker = [(delete_path, [], os.listdir(delete_path))]
        file_paths = []
        for root, _, file_names in walker:
            for file_name in file_names:
                file_path = os.path.join(root, file_name)
                if os.path.isfile(file_path) and self.is_file_allowed(file_path, delete_path):
                    file_paths.append(task_base.normalize_path(file_path))
        return sorted(file_paths)

    def collect_empty_directories(self, delete_path):
        """Collects empty directories under the delete path.

        Args:
            delete_path (str): Directory to inspect.

        Returns:
            list: Empty directory paths, deepest first.
        """
        directory_paths = []
        for root, dir_names, file_names in os.walk(delete_path, topdown=False):
            if root == delete_path:
                continue
            if not dir_names and not file_names:
                directory_paths.append(task_base.normalize_path(root))
        return directory_paths

    def is_file_allowed(self, file_path, delete_path):
        """Checks whether a file matches delete filters.

        Args:
            file_path (str): File path.
            delete_path (str): Delete root.

        Returns:
            bool: True when the file can be deleted.
        """
        normalized_path = task_base.normalize_path(file_path).replace("\\", "/")
        relative_path = os.path.relpath(file_path, delete_path).replace("\\", "/")
        file_name = os.path.basename(file_path)
        include_patterns = self.settings.get("patterns") or ["*"]
        exclude_patterns = self.settings.get("exclude_patterns") or []
        is_included = any(
            fnmatch.fnmatch(file_name, pattern) or fnmatch.fnmatch(relative_path, pattern)
            for pattern in include_patterns
        )
        is_excluded = any(
            fnmatch.fnmatch(file_name, pattern)
            or fnmatch.fnmatch(relative_path, pattern)
            or fnmatch.fnmatch(normalized_path, pattern)
            for pattern in exclude_patterns
        )
        return bool(is_included and not is_excluded)
