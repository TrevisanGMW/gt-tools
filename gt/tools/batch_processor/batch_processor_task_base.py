"""
Batch Processor Task Base

Pure-Python task primitives and shared helpers used by the batch processor.
This module intentionally avoids Maya imports so it can be tested outside Maya.
"""

from string import Formatter
import datetime
import hashlib
import json
import os
import re
import uuid

import gt.ui.resource_library as ui_res_lib


SOURCE_MODE_INCOMING = "incoming"
SOURCE_MODE_PATH = "source_path"
OUTPUT_MODE_TARGET = "target_path"
OUTPUT_MODE_MODIFY = "modify_in_place"
OUTPUT_MODE_PASSTHROUGH = "pass_through"
METADATA_SOURCE_ROOT = "source_root"
METADATA_SOURCE_RELATIVE_PATH = "source_relative_path"
METADATA_SOURCE_RELATIVE_DIR = "source_relative_dir"


class ValidationResult:
    """Container for validation errors and warnings."""

    def __init__(self, errors=None, warnings=None):
        """Initializes a validation result.

        Args:
            errors (list, optional): Initial validation errors.
            warnings (list, optional): Initial validation warnings.
        """
        self.errors = list(errors) if errors else []
        self.warnings = list(warnings) if warnings else []

    def add_error(self, message):
        """Adds a validation error.

        Args:
            message (str): Error message to add.
        """
        self.errors.append(str(message))

    def add_warning(self, message):
        """Adds a validation warning.

        Args:
            message (str): Warning message to add.
        """
        self.warnings.append(str(message))

    def extend(self, other_result):
        """Adds messages from another result.

        Args:
            other_result (ValidationResult): Result to merge into this one.
        """
        if not other_result:
            return
        self.errors.extend(other_result.errors)
        self.warnings.extend(other_result.warnings)

    def is_valid(self):
        """Checks whether this result has no errors.

        Returns:
            bool: True when no errors were collected.
        """
        return not self.errors

    def to_dict(self):
        """Serializes this result as a dictionary.

        Returns:
            dict: Dictionary containing errors and warnings.
        """
        return {"errors": list(self.errors), "warnings": list(self.warnings)}


class TaskSkip(Exception):
    """Exception used when a task intentionally skips one work item."""

    def __init__(self, message, output_path=None, work_item=None):
        """Initializes a task skip exception.

        Args:
            message (str): Skip reason.
            output_path (str, optional): Existing or expected output path.
            work_item (WorkItem, optional): Work item to pass to following tasks.
        """
        super().__init__(message)
        self.output_path = output_path
        self.work_item = work_item


class WorkItem:
    """A file being processed through the batch pipeline."""

    def __init__(self, source_path, current_path=None, metadata=None, source_root=None):
        """Initializes a work item.

        Args:
            source_path (str): Original source file path.
            current_path (str, optional): Current file path for this pipeline step.
            metadata (dict, optional): Additional serializable work item data.
            source_root (str, optional): Root folder used to preserve source-relative output paths.
        """
        self.source_path = normalize_path(source_path)
        self.current_path = normalize_path(current_path or source_path)
        self.metadata = dict(metadata) if metadata else {}
        if source_root:
            self.metadata = build_source_relative_metadata(
                source_path=self.source_path,
                source_root=source_root,
                metadata=self.metadata,
            )

    def to_dict(self):
        """Serializes this work item.

        Returns:
            dict: Serializable work item data.
        """
        return {
            "source_path": self.source_path,
            "current_path": self.current_path,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, data):
        """Builds a work item from serialized data.

        Args:
            data (dict): Serialized work item data.

        Returns:
            WorkItem: New work item instance.
        """
        data = data or {}
        return cls(
            source_path=data.get("source_path"),
            current_path=data.get("current_path"),
            metadata=data.get("metadata") or {},
        )


def normalize_path(path):
    """Normalizes a file path for consistent Windows-safe comparisons.

    Args:
        path (str): File path to normalize.

    Returns:
        str: Normalized absolute path, or an empty string for empty input.
    """
    if not path:
        return ""
    return os.path.normpath(os.path.abspath(str(path)))


def sanitize_filename(name, fallback="item"):
    """Sanitizes a string so it can be used as a file or folder name.

    Args:
        name (str): Raw name to sanitize.
        fallback (str, optional): Name to use when the sanitized value is empty.

    Returns:
        str: Sanitized file-system friendly name.
    """
    sanitized = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "_", str(name or ""))
    sanitized = sanitized.strip(" ._")
    return sanitized or fallback


def build_step_folder_name(step_index, step_name):
    """Builds a stable cooked folder name for a process step.

    Args:
        step_index (int): One-based process step index.
        step_name (str): User-facing process step name.

    Returns:
        str: Sanitized folder name with a numeric prefix.
    """
    return "{0:02d}_{1}".format(int(step_index), sanitize_filename(step_name, "step"))


def hash_settings(settings):
    """Builds a stable hash for task settings.

    Args:
        settings (dict): Serializable task settings.

    Returns:
        str: SHA1 hash of the settings payload.
    """
    payload = json.dumps(settings or {}, sort_keys=True, default=str)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()


def normalize_extensions(extensions):
    """Normalizes extension filters.

    Args:
        extensions (list): Extension values with or without leading dots.

    Returns:
        list: Lowercase extensions with leading dots.
    """
    normalized = []
    for extension in extensions or []:
        extension = str(extension).strip().lower()
        if not extension:
            continue
        if not extension.startswith("."):
            extension = "." + extension
        normalized.append(extension)
    return normalized


def has_supported_extension(file_path, extensions):
    """Checks whether a file path matches the extension filter.

    Args:
        file_path (str): File path to check.
        extensions (list): Extension filters.

    Returns:
        bool: True when the extension is accepted.
    """
    normalized_extensions = normalize_extensions(extensions)
    if not normalized_extensions:
        return True
    return os.path.splitext(file_path)[1].lower() in normalized_extensions


def list_files_from_path(path, include_subdirectories=False):
    """Lists files from a file or directory path.

    Args:
        path (str): File or directory path to inspect.
        include_subdirectories (bool, optional): Whether to walk nested directories.

    Returns:
        list: Sorted normalized file paths.
    """
    resolved_path = normalize_path(path)
    if not resolved_path:
        return []
    if os.path.isfile(resolved_path):
        return [resolved_path]
    if not os.path.isdir(resolved_path):
        return []
    discovered = []
    if include_subdirectories:
        walker = os.walk(resolved_path)
    else:
        walker = [(resolved_path, [], os.listdir(resolved_path))]
    for root, _, file_names in walker:
        for file_name in file_names:
            file_path = os.path.join(root, file_name)
            if os.path.isfile(file_path):
                discovered.append(normalize_path(file_path))
    return sorted(set(discovered))


def path_is_inside_directory(path, directory_path):
    """Checks whether a path is inside a directory.

    Args:
        path (str): Path to inspect.
        directory_path (str): Directory expected to contain the path.

    Returns:
        bool: True when the path is inside the directory.
    """
    path = normalize_path(path)
    directory_path = normalize_path(directory_path)
    if not path or not directory_path:
        return False
    try:
        common_path = os.path.commonpath([path, directory_path])
    except ValueError:
        return False
    return os.path.normcase(common_path) == os.path.normcase(directory_path)


def normalize_relative_path(relative_path):
    """Normalizes a relative path while dropping unsafe traversal segments.

    Args:
        relative_path (str): Relative path to normalize.

    Returns:
        str: Relative path using forward slashes.
    """
    relative_path = str(relative_path or "").replace("\\", "/")
    _, relative_path = os.path.splitdrive(relative_path)
    path_parts = []
    for part in relative_path.split("/"):
        part = str(part or "").strip()
        if not part or part in [".", ".."]:
            continue
        path_parts.append(part)
    return "/".join(path_parts)


def get_path_relative_to_root(file_path, source_root):
    """Gets a file path relative to a source root when safely possible.

    Args:
        file_path (str): File path to make relative.
        source_root (str): Root folder or source file path.

    Returns:
        str: Safe relative path, or the file basename when outside the root.
    """
    file_path = normalize_path(file_path)
    source_root = normalize_path(source_root)
    if not file_path:
        return ""
    if not source_root:
        return os.path.basename(file_path)
    if os.path.isfile(source_root):
        source_root = os.path.dirname(source_root)
    try:
        relative_path = os.path.relpath(file_path, source_root)
    except ValueError:
        return os.path.basename(file_path)
    if relative_path.startswith(os.pardir + os.sep) or relative_path == os.pardir or os.path.isabs(relative_path):
        return os.path.basename(file_path)
    return normalize_relative_path(relative_path) or os.path.basename(file_path)


def build_source_relative_metadata(source_path, source_root, metadata=None):
    """Builds metadata used to preserve source folder structure in task outputs.

    Args:
        source_path (str): Source file path.
        source_root (str): Root folder used for relative path calculation.
        metadata (dict, optional): Existing metadata to update.

    Returns:
        dict: Metadata with source-relative path values.
    """
    metadata = dict(metadata or {})
    source_root = normalize_path(source_root)
    if not source_path or not source_root:
        return metadata
    relative_path = get_path_relative_to_root(source_path, source_root)
    if not relative_path:
        return metadata
    relative_dir = normalize_relative_path(os.path.dirname(relative_path))
    metadata[METADATA_SOURCE_ROOT] = source_root
    metadata[METADATA_SOURCE_RELATIVE_PATH] = relative_path
    metadata[METADATA_SOURCE_RELATIVE_DIR] = relative_dir
    return metadata


def get_work_item_relative_path(work_item):
    """Gets the source-relative file path stored on a work item.

    Args:
        work_item (WorkItem): Work item to inspect.

    Returns:
        str: Source-relative file path, or an empty string.
    """
    metadata = getattr(work_item, "metadata", {}) or {}
    return normalize_relative_path(metadata.get(METADATA_SOURCE_RELATIVE_PATH) or "")


def get_work_item_relative_dir(work_item):
    """Gets the source-relative folder stored on a work item.

    Args:
        work_item (WorkItem): Work item to inspect.

    Returns:
        str: Source-relative folder, or an empty string.
    """
    metadata = getattr(work_item, "metadata", {}) or {}
    relative_dir = metadata.get(METADATA_SOURCE_RELATIVE_DIR)
    if relative_dir:
        return normalize_relative_path(relative_dir)
    relative_path = get_work_item_relative_path(work_item)
    if relative_path:
        return normalize_relative_path(os.path.dirname(relative_path))
    return ""


def get_output_dir_for_work_item(work_item, output_dir):
    """Gets an output directory that preserves the work item's source-relative folder.

    Args:
        work_item (WorkItem): Work item being processed.
        output_dir (str): Base output directory for the task.

    Returns:
        str: Output directory, including the preserved relative folder when available.
    """
    output_dir = normalize_path(output_dir)
    relative_dir = get_work_item_relative_dir(work_item)
    if not output_dir or not relative_dir:
        return output_dir
    resolved_output_dir = normalize_path(os.path.join(output_dir, relative_dir))
    if not path_is_inside_directory(resolved_output_dir, output_dir):
        return output_dir
    return resolved_output_dir


def build_work_item_output_path(work_item, output_dir, file_name):
    """Builds an output file path preserving a work item's source-relative folder.

    Args:
        work_item (WorkItem): Work item being processed.
        output_dir (str): Base output directory.
        file_name (str): Output file name.

    Returns:
        str: Output file path.
    """
    resolved_output_dir = get_output_dir_for_work_item(work_item, output_dir)
    return normalize_path(os.path.join(resolved_output_dir, file_name))


def validate_format_tokens(pattern, allowed_tokens):
    """Validates token names used by a format string.

    Args:
        pattern (str): Format string to validate.
        allowed_tokens (set): Supported token names.

    Returns:
        ValidationResult: Collected validation messages.
    """
    result = ValidationResult()
    if not pattern:
        result.add_error("Pattern cannot be empty.")
        return result
    try:
        parsed_pattern = list(Formatter().parse(pattern))
    except ValueError as exception:
        result.add_error("Invalid pattern: {0}".format(exception))
        return result
    for _, field_name, format_spec, conversion in parsed_pattern:
        if field_name and field_name not in allowed_tokens:
            result.add_error("Unsupported token: {{{0}}}".format(field_name))
        if format_spec:
            result.add_error("Token format specifiers are not supported: {0}".format(format_spec))
        if conversion:
            result.add_error("Token conversions are not supported: {0}".format(conversion))
    return result


def get_today_token():
    """Gets the current date token used by rename-style tasks.

    Returns:
        str: Current date formatted as YYYYMMDD.
    """
    return datetime.date.today().strftime("%Y%m%d")


class BatchTask:
    """Base class for serializable batch processor tasks."""

    task_type = "base"
    default_display_name = "Task"
    default_source_path_template = "{previous-task-path}"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_{task-name}"
    default_task_path_template = default_target_path_template
    icon = ui_res_lib.Icon.batch_task_generic
    category = "General"
    category_icon = ui_res_lib.Icon.batch_task_generic
    default_segment_name = "New Segment"
    can_be_removed = True
    is_input_task = False
    is_indexless_task = False
    is_aggregate_task = False
    is_output_task = False
    is_delete_task = False
    is_data_load_task = False

    def __init__(self, task_id=None, display_name=None, enabled=True, settings=None, extra_data=None, **kwargs):
        """Initializes a batch task.

        Args:
            task_id (str, optional): Stable task instance identifier.
            display_name (str, optional): User-facing task name.
            enabled (bool, optional): Whether this task should run.
            settings (dict, optional): Serializable task settings.
            extra_data (dict, optional): Unknown serialized task fields.
            **kwargs: Additional compatibility arguments.
        """
        if not task_id:
            task_id = kwargs.get("module_id")
        self.id = task_id or str(uuid.uuid4())
        self.display_name = display_name or self.default_display_name
        self.enabled = bool(enabled)
        self.settings = self.get_default_settings()
        if settings is None and "parameters" in kwargs:
            settings = kwargs.get("parameters")
        incoming_settings = settings or {}
        self.settings.update(incoming_settings)
        if incoming_settings.get("task_path") and not incoming_settings.get("target_path"):
            self.settings["target_path"] = incoming_settings.get("task_path")
        self._normalize_common_settings(incoming_settings=incoming_settings)
        self.extra_data = dict(extra_data) if extra_data else {}

    @property
    def module_type(self):
        """Gets a backward-compatible module type alias.

        Returns:
            str: Task type value.
        """
        return self.task_type

    @module_type.setter
    def module_type(self, value):
        """Sets a backward-compatible module type alias.

        Args:
            value (str): Task type value.
        """
        self.task_type = value

    def get_default_settings(self):
        """Gets default settings for this task.

        Returns:
            dict: Default task settings.
        """
        return {
            "include_in_task_index": self.get_default_include_in_task_index(),
            "source_mode": SOURCE_MODE_PATH,
            "source_path": self.default_source_path_template,
            "output_mode": OUTPUT_MODE_TARGET,
            "target_path": self.default_target_path_template,
            "overwrite": False,
            "task_io_collapsed": False,
        }

    def _normalize_common_settings(self, incoming_settings=None):
        """Normalizes common task settings for legacy and current project data.

        Args:
            incoming_settings (dict, optional): Raw settings supplied to the constructor.
        """
        incoming_settings = incoming_settings or {}
        self.settings.setdefault("include_in_task_index", self.get_default_include_in_task_index())
        if self.is_input_task:
            return
        if "use_incoming_files" in self.settings and "source_mode" not in self.settings:
            if self.settings.get("use_incoming_files"):
                self.settings["source_mode"] = SOURCE_MODE_INCOMING
            else:
                self.settings["source_mode"] = SOURCE_MODE_PATH
        if "source_path" in incoming_settings and "source_mode" not in incoming_settings:
            self.settings["source_mode"] = SOURCE_MODE_PATH
        if "modify_in_place" in self.settings and "output_mode" not in self.settings:
            if self.settings.get("modify_in_place"):
                self.settings["output_mode"] = OUTPUT_MODE_MODIFY
            else:
                self.settings["output_mode"] = OUTPUT_MODE_TARGET
        self.settings.setdefault("source_mode", SOURCE_MODE_PATH)
        self.settings.setdefault("source_path", self.default_source_path_template)
        self.settings.setdefault("output_mode", OUTPUT_MODE_TARGET)
        self.settings.setdefault("target_path", self.default_target_path_template)
        self.settings.setdefault("overwrite", False)
        self.settings.setdefault("task_io_collapsed", False)

    def get_default_include_in_task_index(self):
        """Gets the default task-index participation state.

        Returns:
            bool: True when tasks should count toward task index variables.
        """
        if self.is_input_task:
            return False
        if self.is_indexless_task:
            return False
        return True

    def includes_task_index(self):
        """Checks whether this task contributes to task index variables.

        Returns:
            bool: True when this task should count toward task index values.
        """
        return bool(self.settings.get("include_in_task_index", self.get_default_include_in_task_index()))

    def uses_incoming_files(self):
        """Checks whether this task should use incoming work items.

        Returns:
            bool: True when incoming work items should be used instead of source path discovery.
        """
        return self.settings.get("source_mode") == SOURCE_MODE_INCOMING

    def starts_new_input_list(self):
        """Checks whether this task starts a new input segment.

        A segment boundary resets the accumulated incoming work items so a
        single project can process unrelated file sets in sequence. Only input
        tasks can start a new segment; the check is safe to call on any task.

        Returns:
            bool: True when this input task begins a fresh input list.
        """
        return bool(self.is_input_task and self.settings.get("start_new_input_list", False))

    def shows_segment_separator(self):
        """Checks whether this task shows a segment divider in the task list.

        The divider is controlled solely by the "Add Separator" option, so it can
        appear on any task that exposes it and is independent of starting a new
        input list. It is purely presentational.

        Returns:
            bool: True when a segment divider should be drawn above this task.
        """
        return bool(self.settings.get("force_segment_separator", False))

    def get_segment_display_name(self):
        """Gets the label shown on this task's segment divider.

        Returns:
            str: User-defined segment name, or the task's default when empty.
        """
        segment_name = str(self.settings.get("segment_name") or "").strip()
        return segment_name or self.default_segment_name

    def get_segment_color_name(self):
        """Gets the UI color name used for this task's segment divider.

        Returns:
            str: Color name from the UI color library, defaulting to a soft blue.
        """
        return str(self.settings.get("segment_color") or "blue_light_sky").strip() or "blue_light_sky"

    def modifies_in_place(self):
        """Checks whether this task should modify received files in place.

        Returns:
            bool: True when the task should not write to its target path.
        """
        return self.settings.get("output_mode") == OUTPUT_MODE_MODIFY

    def passes_through(self):
        """Checks whether this task should pass work items through without writing.

        Returns:
            bool: True when the task should not create or modify an output file.
        """
        return self.settings.get("output_mode") == OUTPUT_MODE_PASSTHROUGH

    def writes_to_target_path(self):
        """Checks whether this task writes files to its configured target path.

        Returns:
            bool: True when a target directory is required for task output.
        """
        return not self.modifies_in_place() and not self.passes_through()

    def get_source_path_template(self):
        """Gets this task's source path template.

        Returns:
            str: Path template used to find input files for this task.
        """
        return self.settings.get("source_path") or self.default_source_path_template

    def get_target_path_template(self):
        """Gets this task's target path template.

        Returns:
            str: Path template used by runner services.
        """
        return self.settings.get("target_path") or self.settings.get("task_path") or self.default_target_path_template

    def get_task_path_template(self):
        """Gets this task's output path template.

        Returns:
            str: Path template used by runner services.
        """
        return self.get_target_path_template()

    def source_uses_previous_task_path(self):
        """Checks whether this task source path points at the previous task path.

        Returns:
            bool: True when the source path is exactly the previous task path token.
        """
        source_template = str(self.get_source_path_template() or "").strip().replace("\\", "/")
        return source_template.strip("/") == "{previous-task-path}"

    def source_references_previous_task_path(self):
        """Checks whether this task source path references the previous task path.

        Returns:
            bool: True when the source path contains the previous task path token.
        """
        return "{previous-task-path}" in str(self.get_source_path_template() or "")

    def resolve_source_path(self, project, task_index=None):
        """Resolves this task's source path template against a project.

        Args:
            project (BatchProcessorModel): Active project model.
            task_index (int, optional): One-based task index.

        Returns:
            str: Resolved normalized source path.
        """
        return project.resolve_template_path(self.get_source_path_template(), task=self, task_index=task_index)

    def resolve_task_path(self, project, task_index=None):
        """Resolves this task's path template against a project.

        Args:
            project (BatchProcessorModel): Active project model.
            task_index (int, optional): One-based task index.

        Returns:
            str: Resolved normalized task path.
        """
        return project.resolve_template_path(self.get_task_path_template(), task=self, task_index=task_index)

    def discover_source_files(self, project, task_index=None):
        """Discovers files from this task's source path.

        Args:
            project (BatchProcessorModel): Active project model.
            task_index (int, optional): One-based task index.

        Returns:
            list: Sorted normalized source files.
        """
        source_path = self.resolve_source_path(project=project, task_index=task_index)
        include_default = self.source_references_previous_task_path()
        include_subdirectories = bool(self.settings.get("source_include_subdirectories", include_default))
        return list_files_from_path(source_path, include_subdirectories=include_subdirectories)

    def validate(self, project):
        """Validates this task against a project.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        return ValidationResult()

    def validate_common_settings(self, project):
        """Validates task settings shared by most processing tasks.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = ValidationResult()
        if self.is_input_task:
            return result
        if self.uses_incoming_files() and self.modifies_in_place():
            result.add_error(
                (
                    'Task "{0}" cannot modify incoming input files in place. '
                    "Disable incoming files or use a target path."
                ).format(self.display_name)
            )
        if not self.uses_incoming_files():
            source_path = self.resolve_source_path(project)
            if not source_path:
                result.add_error('Task "{0}" source path is empty.'.format(self.display_name))
            elif not os.path.exists(source_path):
                result.add_warning('Task "{0}" source path does not exist: {1}'.format(self.display_name, source_path))
        if self.writes_to_target_path():
            target_path = self.resolve_task_path(project)
            if not target_path:
                result.add_error('Task "{0}" target path is empty.'.format(self.display_name))
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Validates work items before this task executes.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Cooked output folder for this step.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Collected validation result.
        """
        return ValidationResult()

    def execute(self, work_item, project, step_output_dir, context=None):
        """Executes this task for a single work item.

        Args:
            work_item (WorkItem): Work item to process.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Cooked output folder for this step.
            context (dict, optional): Runtime context.

        Raises:
            NotImplementedError: If the task does not implement execution.
        """
        raise NotImplementedError("Task execution has not been implemented.")

    def to_dict(self):
        """Serializes this task.

        Returns:
            dict: Serializable task data.
        """
        data = dict(self.extra_data)
        data.update(
            {
                "id": self.id,
                "task_type": self.task_type,
                "display_name": self.display_name,
                "enabled": self.enabled,
                "parameters": dict(self.settings),
            }
        )
        return data

    @classmethod
    def from_dict(cls, data):
        """Builds a task from serialized data.

        Args:
            data (dict): Serialized task data.

        Returns:
            BatchTask: New task instance.
        """
        known_keys = set(["id", "task_type", "module_type", "display_name", "enabled", "settings", "parameters"])
        extra_data = {}
        for key, value in (data or {}).items():
            if key not in known_keys:
                extra_data[key] = value
        if "parameters" in (data or {}):
            settings = (data or {}).get("parameters") or {}
        else:
            settings = (data or {}).get("settings") or {}
        return cls(
            task_id=(data or {}).get("id"),
            display_name=(data or {}).get("display_name"),
            enabled=(data or {}).get("enabled", True),
            settings=settings,
            extra_data=extra_data,
        )
