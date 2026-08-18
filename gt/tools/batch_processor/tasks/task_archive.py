"""
Batch Processor Archive Tasks
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tasks import task_utils
import os
import re
import zipfile


ZIP_VERSION_TOKEN = "{version}"


class TaskArchive(task_base.BatchTask):
    """Task that compresses incoming files into one zip archive."""

    task_type = constants.TaskType.ZIP_COMPRESS
    default_display_name = "Archive"
    default_target_path_template = "{project-dir}/{output-dir}"
    icon = ui_res_lib.Icon.batch_task_archive
    category = "Outputs"
    category_icon = ui_res_lib.Icon.batch_category_outputs
    is_aggregate_task = True
    is_output_task = True
    supports_run_once_after_jobs = True

    def get_default_settings(self):
        """Gets default zip task settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "archive_name": "{project-sanitized-name}.zip",
            "archive_version": "01",
            "archive_version_auto": False,
            "archive_version_padding": 2,
            "compression": "Deflated",
            "run_once_after_multi_instance": True,
            "use_source_path_as_relative_root": True,
            "preserve_relative_paths": True,
            "relative_root": "",
            "overwrite": False,
            "force_segment_separator": False,
            "segment_name": "",
            "segment_color": "blue_light_sky",
        }

    def validate(self, project):
        """Validates zip settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        if not self.settings.get("archive_name"):
            result.add_error("Zip archive name cannot be empty.")
        if self.modifies_in_place():
            result.add_error("Zip Compress cannot modify source files in place. Use a target path.")
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Compresses all incoming work items into one zip archive.

        Args:
            work_item (WorkItem): Unused aggregate work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            context (dict, optional): Runtime context containing work_items.

        Returns:
            WorkItem: Archive work item.
        """
        context = context or {}
        work_items = context.get("work_items") or []
        if not work_items:
            raise task_base.TaskSkip("No incoming files to compress.")
        output_path = self.build_archive_path(project, step_output_dir)
        if os.path.exists(output_path) and not self.settings.get("overwrite", False):
            raise task_base.TaskSkip("Zip archive already exists and overwrite is disabled: {0}".format(output_path))
        output_dir = os.path.dirname(output_path)
        if output_dir:
            task_utils.ensure_directory(output_dir)
        compression = zipfile.ZIP_DEFLATED
        if self.settings.get("compression") == "Stored":
            compression = zipfile.ZIP_STORED
        relative_root = self.get_relative_root(project, work_items)
        compressed_file_count = 0
        with zipfile.ZipFile(output_path, "w", compression=compression) as zip_file:
            for source_path, arc_name in self.iter_archive_members(work_items, relative_root, output_path):
                if os.path.isdir(source_path):
                    zip_file.write(source_path, arcname=arc_name.replace("\\", "/").rstrip("/") + "/")
                else:
                    zip_file.write(source_path, arcname=arc_name.replace("\\", "/"))
                    compressed_file_count += 1
        metadata = {
            "last_task_id": self.id,
            "last_task_type": self.task_type,
            "settings_hash": task_base.hash_settings(self.settings),
            "compressed_files": compressed_file_count,
        }
        return task_base.WorkItem(source_path=output_path, current_path=output_path, metadata=metadata)

    def discover_source_files(self, project, task_index=None):
        """Discovers files and folders from this task's source path.

        Args:
            project (BatchProcessorModel): Active project model.
            task_index (int, optional): One-based task index.

        Returns:
            list: Sorted normalized source files and folders.
        """
        source_path = self.resolve_source_path(project=project, task_index=task_index)
        include_default = self.source_references_previous_task_path()
        include_subdirectories = bool(self.settings.get("source_include_subdirectories", include_default))
        return list_archive_sources(source_path, include_subdirectories=include_subdirectories)

    def build_archive_path(self, project, step_output_dir):
        """Builds the archive output path.

        Args:
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.

        Returns:
            str: Archive path.
        """
        archive_name = self.resolve_archive_name(project=project, step_output_dir=step_output_dir)
        if not archive_name.lower().endswith(".zip"):
            archive_name += ".zip"
        return task_base.normalize_path(os.path.join(step_output_dir, archive_name))

    def resolve_archive_name(self, project, step_output_dir):
        """Resolves the archive name including the zip-only version token.

        Args:
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.

        Returns:
            str: Resolved archive name.
        """
        archive_name = project.resolve_template(self.settings.get("archive_name") or "archive.zip", task=self)
        if ZIP_VERSION_TOKEN not in archive_name:
            return archive_name
        version = self.get_archive_version(project=project, step_output_dir=step_output_dir, archive_name=archive_name)
        return archive_name.replace(ZIP_VERSION_TOKEN, version)

    def get_archive_version(self, project, step_output_dir, archive_name=None):
        """Gets the archive version value.

        Args:
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            archive_name (str, optional): Archive name with project variables already resolved.

        Returns:
            str: Formatted archive version.
        """
        if self.settings.get("archive_version_auto", False):
            return self.detect_next_archive_version(project=project, step_output_dir=step_output_dir, archive_name=archive_name)
        return self.format_archive_version(self.settings.get("archive_version"))

    def detect_next_archive_version(self, project, step_output_dir, archive_name=None):
        """Detects the next archive version from existing target-folder files.

        Args:
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            archive_name (str, optional): Archive name with project variables already resolved.

        Returns:
            str: Formatted next version.
        """
        archive_name = archive_name or project.resolve_template(self.settings.get("archive_name") or "archive.zip", task=self)
        if ZIP_VERSION_TOKEN not in archive_name:
            return self.format_archive_version(self.settings.get("archive_version"))
        if not archive_name.lower().endswith(".zip"):
            archive_name += ".zip"
        archive_path = os.path.normpath(os.path.join(step_output_dir, archive_name))
        search_dir = os.path.dirname(archive_path)
        archive_pattern = os.path.basename(archive_path)
        if not os.path.isdir(search_dir):
            return self.format_archive_version(1)
        version_regex = build_version_file_regex(archive_pattern)
        highest_version = 0
        detected_padding = self.get_archive_version_padding()
        for file_name in os.listdir(search_dir):
            match = version_regex.match(file_name)
            if not match:
                continue
            version_text = match.group("version")
            try:
                version_number = int(version_text)
            except (TypeError, ValueError):
                continue
            highest_version = max(highest_version, version_number)
            detected_padding = max(detected_padding, len(version_text))
        return self.format_archive_version(highest_version + 1, padding=detected_padding)

    def get_archive_version_padding(self):
        """Gets the archive version padding.

        Returns:
            int: Minimum number of version digits.
        """
        try:
            return max(1, int(self.settings.get("archive_version_padding", 2)))
        except (TypeError, ValueError):
            return 2

    def format_archive_version(self, value, padding=None):
        """Formats a version value.

        Args:
            value (object): Version value.
            padding (int, optional): Minimum digit count.

        Returns:
            str: Formatted version string.
        """
        padding = self.get_archive_version_padding() if padding is None else max(1, int(padding))
        try:
            return str(int(value)).zfill(padding)
        except (TypeError, ValueError):
            return str(value or "").strip() or str(1).zfill(padding)

    def iter_archive_members(self, work_items, relative_root, output_path=""):
        """Iterates all files and folders that should be written to the archive.

        Args:
            work_items (list): Incoming work items.
            relative_root (str): Root used to build archive member paths.
            output_path (str, optional): Archive being written.

        Yields:
            tuple: Source path and archive member path.
        """
        visited_paths = set()
        output_path = task_base.normalize_path(output_path)
        for item in work_items:
            item_path = task_base.normalize_path(item.current_path)
            for source_path in iter_source_members(item_path):
                source_path = task_base.normalize_path(source_path)
                if source_path in visited_paths or source_path == output_path:
                    continue
                visited_paths.add(source_path)
                arc_name = self.build_archive_member_name(source_path=source_path, relative_root=relative_root)
                if arc_name:
                    yield source_path, arc_name

    def build_archive_member_name(self, source_path, relative_root):
        """Builds a zip member name for a source path.

        Args:
            source_path (str): Source file or folder path.
            relative_root (str): Root used to preserve relative paths.

        Returns:
            str: Zip member name.
        """
        source_path = task_base.normalize_path(source_path)
        arc_name = os.path.basename(source_path.rstrip("\\/"))
        if self.should_preserve_relative_paths() and relative_root:
            arc_name = os.path.relpath(source_path, relative_root)
        return task_base.normalize_relative_path(arc_name)

    def should_preserve_relative_paths(self):
        """Gets whether archive members should preserve relative paths.

        Returns:
            bool: True when archive member paths should be relative to a root.
        """
        if self.settings.get("use_source_path_as_relative_root", True):
            return True
        return bool(self.settings.get("preserve_relative_paths", True))

    def get_relative_root(self, project, work_items):
        """Gets the path root used for archive names.

        Args:
            project (BatchProcessorModel): Active project.
            work_items (list): Incoming work items.

        Returns:
            str: Relative root path.
        """
        if self.settings.get("use_source_path_as_relative_root", True):
            source_path = self.resolve_source_path(project=project)
            if os.path.isfile(source_path):
                return os.path.dirname(source_path)
            if os.path.isdir(source_path):
                return source_path
        relative_root = self.settings.get("relative_root") or ""
        if relative_root:
            return project.resolve_template_path(relative_root, task=self)
        try:
            source_paths = [item.current_path for item in work_items if os.path.exists(item.current_path)]
            common_path = os.path.commonpath(source_paths)
            if os.path.isfile(common_path):
                return os.path.dirname(common_path)
            return common_path
        except Exception:
            return ""


def list_archive_sources(path, include_subdirectories=False):
    """Lists files and folders from a source path.

    Args:
        path (str): File or directory path to inspect.
        include_subdirectories (bool, optional): Whether to walk nested directories.

    Returns:
        list: Sorted normalized source paths.
    """
    resolved_path = task_base.normalize_path(path)
    if not resolved_path or not os.path.exists(resolved_path):
        return []
    if os.path.isfile(resolved_path):
        return [resolved_path]
    discovered = [resolved_path]
    if include_subdirectories:
        for root, dir_names, file_names in os.walk(resolved_path):
            for dir_name in dir_names:
                discovered.append(task_base.normalize_path(os.path.join(root, dir_name)))
            for file_name in file_names:
                discovered.append(task_base.normalize_path(os.path.join(root, file_name)))
    else:
        for entry_name in os.listdir(resolved_path):
            discovered.append(task_base.normalize_path(os.path.join(resolved_path, entry_name)))
    return sorted(set(discovered))


def iter_source_members(source_path):
    """Iterates a source path and all nested archive members.

    Args:
        source_path (str): File or directory path.

    Yields:
        str: Source file or folder path.
    """
    if os.path.isfile(source_path):
        yield source_path
        return
    if not os.path.isdir(source_path):
        return
    yield source_path
    for root, dir_names, file_names in os.walk(source_path):
        for dir_name in dir_names:
            yield os.path.join(root, dir_name)
        for file_name in file_names:
            yield os.path.join(root, file_name)


def build_version_file_regex(archive_pattern):
    """Builds a filename regex using the zip version token.

    Args:
        archive_pattern (str): Archive filename pattern containing `{version}`.

    Returns:
        re.Pattern: Compiled filename pattern.
    """
    escaped_pattern = re.escape(archive_pattern)
    escaped_token = re.escape(ZIP_VERSION_TOKEN)
    regex_pattern = escaped_pattern.replace(escaped_token, r"(?P<version>\d+)", 1)
    return re.compile(r"^{0}$".format(regex_pattern))
