"""
Batch Processor Rename Map Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
import hashlib
import os


CHECKSUM_ALGORITHMS = ["sha1", "sha256", "md5"]


class TaskMapRename(task_base.BatchTask):
    """Task that builds a rename map by comparing matching file contents in two folders."""

    task_type = constants.TaskType.MAP_RENAME
    default_display_name = "Map Rename"
    default_target_path_template = "{project-dir}/data"
    icon = "tool_renamer"
    category = "Utilities"
    category_icon = "root_utilities"
    is_aggregate_task = True
    is_data_load_task = True

    def get_default_settings(self):
        """Gets default rename-map settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "folder_a": "{previous-previous-task-path}",
            "folder_b": "{previous-task-path}",
            "map_path": "{project-dir}/data/rename_map.json",
            "include_subdirectories": True,
            "checksum_algorithm": "sha1",
            "only_different_names": True,
            "include_unmatched": False,
            "overwrite": True,
        }

    def validate(self, project):
        """Validates rename-map settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        if self.settings.get("checksum_algorithm") not in CHECKSUM_ALGORITHMS:
            result.add_error(
                "Map Rename checksum algorithm must be one of: {0}.".format(", ".join(CHECKSUM_ALGORITHMS))
            )
        folder_a = self.get_folder_path(project, "folder_a")
        folder_b = self.get_folder_path(project, "folder_b")
        if not folder_a:
            result.add_error("Map Rename folder A is empty.")
        elif not os.path.isdir(folder_a):
            result.add_error("Map Rename folder A does not exist: {0}".format(folder_a))
        if not folder_b:
            result.add_error("Map Rename folder B is empty.")
        elif not os.path.isdir(folder_b):
            result.add_error("Map Rename folder B does not exist: {0}".format(folder_b))
        map_path = self.get_map_path(project)
        if not map_path:
            result.add_error("Map Rename output map path is empty.")
        elif os.path.exists(map_path) and not self.settings.get("overwrite", True):
            result.add_warning("Map Rename output map already exists and overwrite is disabled: {0}".format(map_path))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Builds a rename map and returns incoming work items unchanged.

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
        map_path = self.get_map_path(project)
        if os.path.exists(map_path) and not self.settings.get("overwrite", True):
            raise task_base.TaskSkip("Rename map already exists and overwrite is disabled: {0}".format(map_path))
        folder_a = self.get_folder_path(project, "folder_a")
        folder_b = self.get_folder_path(project, "folder_b")
        folder_a_files = self.list_files(folder_a)
        folder_b_files = self.list_files(folder_b)
        folder_b_by_hash = self.group_files_by_checksum(folder_b_files)
        rename_entries = []
        unmatched_files = []
        for file_a in folder_a_files:
            checksum = self.get_file_checksum(file_a)
            matches = folder_b_by_hash.get(checksum) or []
            if not matches:
                if self.settings.get("include_unmatched", False):
                    unmatched_files.append(self.build_unmatched_entry(file_a, folder_a, checksum))
                continue
            for file_b in matches:
                if self.settings.get("only_different_names", True):
                    if os.path.basename(file_a) == os.path.basename(file_b):
                        continue
                rename_entries.append(self.build_map_entry(file_a, file_b, folder_a, folder_b, checksum))
        payload = {
            "version": 1,
            "created_at": task_utils.get_timestamp(),
            "folder_a": folder_a,
            "folder_b": folder_b,
            "checksum_algorithm": self.settings.get("checksum_algorithm"),
            "include_subdirectories": bool(self.settings.get("include_subdirectories", True)),
            "rename_map": rename_entries,
            "unmatched": unmatched_files,
            "summary": {
                "folder_a_files": len(folder_a_files),
                "folder_b_files": len(folder_b_files),
                "mapped_files": len(rename_entries),
                "unmatched_files": len(unmatched_files),
            },
        }
        task_utils.write_json_log(map_path, payload)
        task_utils.report_log_artifact(context, map_path)
        return list(work_items)

    def get_folder_path(self, project, key):
        """Gets a resolved comparison folder path.

        Args:
            project (BatchProcessorModel): Active project.
            key (str): Setting key.

        Returns:
            str: Resolved folder path.
        """
        return project.resolve_template_path(self.settings.get(key), task=self)

    def get_map_path(self, project):
        """Gets the resolved rename map path.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Resolved map path.
        """
        return project.resolve_template_path(self.settings.get("map_path"), task=self)

    def list_files(self, folder_path):
        """Lists files in a folder according to task settings.

        Args:
            folder_path (str): Folder path.

        Returns:
            list: Sorted file paths.
        """
        include_subdirectories = bool(self.settings.get("include_subdirectories", True))
        return task_base.list_files_from_path(folder_path, include_subdirectories=include_subdirectories)

    def group_files_by_checksum(self, file_paths):
        """Groups files by checksum.

        Args:
            file_paths (list): File paths to hash.

        Returns:
            dict: Mapping of checksum strings to file paths.
        """
        grouped_files = {}
        for file_path in file_paths:
            checksum = self.get_file_checksum(file_path)
            grouped_files.setdefault(checksum, []).append(file_path)
        return grouped_files

    def get_file_checksum(self, file_path):
        """Gets a checksum for a file.

        Args:
            file_path (str): File path.

        Returns:
            str: Checksum string.
        """
        algorithm = self.settings.get("checksum_algorithm") or "sha1"
        hash_object = hashlib.new(algorithm)
        with open(file_path, "rb") as open_file:
            for chunk in iter(lambda: open_file.read(1024 * 1024), b""):
                hash_object.update(chunk)
        return hash_object.hexdigest()

    @staticmethod
    def build_map_entry(file_a, file_b, folder_a, folder_b, checksum):
        """Builds one rename-map entry.

        Args:
            file_a (str): Source-side file path.
            file_b (str): Target-side file path.
            folder_a (str): Source-side root folder.
            folder_b (str): Target-side root folder.
            checksum (str): File checksum.

        Returns:
            dict: Rename-map entry.
        """
        rel_a = os.path.relpath(file_a, folder_a).replace("\\", "/")
        rel_b = os.path.relpath(file_b, folder_b).replace("\\", "/")
        return {
            "from_relative_path": rel_a,
            "from_name": os.path.basename(file_a),
            "to_relative_path": rel_b,
            "to_name": os.path.basename(file_b),
            "checksum": checksum,
            "size": os.path.getsize(file_a),
        }

    @staticmethod
    def build_unmatched_entry(file_path, folder_path, checksum):
        """Builds one unmatched-file entry.

        Args:
            file_path (str): File path.
            folder_path (str): Folder root.
            checksum (str): File checksum.

        Returns:
            dict: Unmatched file entry.
        """
        return {
            "relative_path": os.path.relpath(file_path, folder_path).replace("\\", "/"),
            "name": os.path.basename(file_path),
            "checksum": checksum,
            "size": os.path.getsize(file_path),
        }


MapRenameTask = TaskMapRename
