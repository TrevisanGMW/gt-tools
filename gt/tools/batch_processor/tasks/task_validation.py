"""
Batch Processor Validation Tasks
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tasks import task_utils
import hashlib
import os


VALIDATION_LOG_ALL = "Log All"
VALIDATION_LOG_ISSUES = "Log Issues Only"
VALIDATION_LOG_NONE = "No Logs"
VALIDATION_LOG_TARGET_PATH_TEMPLATE = "{log-dir}"
OLD_VALIDATION_LOG_TARGET_PATH_TEMPLATE = "{project-dir}/validation_logs"
LEGACY_VALIDATION_LOG_TARGET_PATH_TEMPLATE = "{project-dir}/{output-dir}/validation_logs"

FOLDER_COMPARE_RELATIVE_PATHS = "Relative Paths"
FOLDER_COMPARE_NAMES_ONLY = "Names Only"
FOLDER_COMPARE_NAMES_WITHOUT_EXTENSIONS = "Names Without Extensions"
FOLDER_COMPARE_CHECKSUM = "Checksum"


def migrate_validation_log_target_path(task):
    """Migrates validation tasks from the old output-folder log path to the project log path.

    Args:
        task (BatchTask): Validation task to update.
    """
    if not task or not getattr(task, "settings", None):
        return
    legacy_paths = [LEGACY_VALIDATION_LOG_TARGET_PATH_TEMPLATE, OLD_VALIDATION_LOG_TARGET_PATH_TEMPLATE]
    if task.settings.get("target_path") in legacy_paths:
        task.settings["target_path"] = VALIDATION_LOG_TARGET_PATH_TEMPLATE


class TaskValidationMayaScene(task_base.BatchTask):
    """Task that validates Maya scenes using the shared gt-tools validator library."""

    task_type = constants.TaskType.MAYA_SCENE_VALIDATE
    default_display_name = "Validate Scene"
    default_target_path_template = VALIDATION_LOG_TARGET_PATH_TEMPLATE
    icon = ui_res_lib.Icon.tool_validator
    category = "Validation"
    category_icon = ui_res_lib.Icon.batch_category_validation
    is_indexless_task = True

    def __init__(self, *args, **kwargs):
        """Initializes a Maya scene validation task.

        Args:
            *args: Positional arguments passed to BatchTask.
            **kwargs: Keyword arguments passed to BatchTask.
        """
        super().__init__(*args, **kwargs)
        migrate_validation_log_target_path(self)

    def get_default_settings(self):
        """Gets default Maya scene validation settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "validators": [],
            "validation_scope": "Scene",
            "log_mode": VALIDATION_LOG_ISSUES,
            "fail_on_issues": False,
            "overwrite": True,
        }

    def validate(self, project):
        """Validates task settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        validator_names = self.get_validator_names()
        if not validator_names:
            result.add_warning("Maya scene validation has no validators configured.")
            return result
        available_validators = get_available_scene_validators()
        for validator_name in validator_names:
            if validator_name not in available_validators:
                result.add_error("Unknown Maya scene validator: {0}".format(validator_name))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Runs configured validators against one Maya scene.

        Args:
            work_item (WorkItem): Work item to validate.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Log output directory.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Original work item.
        """
        task_utils.load_source_scene(
            work_item.current_path,
            source_load_mode=self.settings.get("source_load_mode") or "Open",
            load_relevant_plugins=self.settings.get("load_relevant_plugins", True),
        )
        results = self.run_validators()
        has_issues = any(result_data.get("status_value", 0) > 1 for result_data in results)
        self.write_validation_log_if_needed(
            work_item=work_item,
            step_output_dir=step_output_dir,
            results=results,
            has_issues=has_issues,
            context=context,
        )
        if has_issues and self.settings.get("fail_on_issues"):
            raise RuntimeError("Maya scene validation found issues in: {0}".format(work_item.current_path))
        return task_base.WorkItem(
            source_path=work_item.source_path,
            current_path=work_item.current_path,
            metadata=task_utils.build_metadata(self, work_item),
        )

    def run_validators(self):
        """Runs the selected validators in the current Maya scene.

        Returns:
            list: Serialized validator result dictionaries.
        """
        import gt.core.validator as core_validator

        results = []
        scope = get_validator_scope(self.settings.get("validation_scope"))
        for validator_name in self.get_validator_names():
            validator_class = get_validator_class(validator_name)
            if not validator_class:
                results.append(
                    {
                        "validator": validator_name,
                        "name": validator_name,
                        "status": "MISSING",
                        "status_value": 3,
                        "feedback": "Validator is not registered.",
                    }
                )
                continue
            validator = validator_class()
            try:
                validator.validate(scope=scope)
            except TypeError:
                validator.validate()
            status = validator.get_status()
            status_name = getattr(status, "name", str(status))
            try:
                status_value = int(status)
            except (TypeError, ValueError):
                status_value = 0
            results.append(
                {
                    "validator": validator_name,
                    "name": validator.get_name(),
                    "description": validator.get_description(),
                    "status": status_name,
                    "status_value": status_value,
                    "feedback": validator.get_feedback(),
                    "repair_available": validator.is_repair_available(),
                }
            )
        return results

    def write_validation_log_if_needed(self, work_item, step_output_dir, results, has_issues, context=None):
        """Writes validation logs when requested by settings.

        Args:
            work_item (WorkItem): Validated work item.
            step_output_dir (str): Log output directory.
            results (list): Validation results.
            has_issues (bool): Whether any validator produced warnings or failures.
            context (dict, optional): Runtime context.

        Returns:
            str or None: Written log path, if any.
        """
        return write_task_validation_log(
            task=self,
            step_output_dir=step_output_dir,
            entry={
                "source": work_item.current_path,
                "has_issues": bool(has_issues),
                "validators": results,
            },
            has_issues=has_issues,
            context=context,
        )

    def get_validator_names(self):
        """Gets configured validator names.

        Returns:
            list: Validator names.
        """
        validators = self.settings.get("validators") or []
        if isinstance(validators, str):
            validators = [item.strip() for item in validators.replace(",", "\n").splitlines()]
        return [str(item).strip() for item in validators if str(item).strip()]


class TaskValidationFileIntegrity(task_base.BatchTask):
    """Task that validates file integrity without opening Maya scenes."""

    task_type = constants.TaskType.FILE_INTEGRITY_VALIDATE
    default_display_name = "Validate Integrity"
    default_target_path_template = VALIDATION_LOG_TARGET_PATH_TEMPLATE
    icon = ui_res_lib.Icon.tool_validator
    category = "Validation"
    category_icon = ui_res_lib.Icon.batch_category_validation
    is_indexless_task = True

    def __init__(self, *args, **kwargs):
        """Initializes a file integrity validation task.

        Args:
            *args: Positional arguments passed to BatchTask.
            **kwargs: Keyword arguments passed to BatchTask.
        """
        super().__init__(*args, **kwargs)
        migrate_validation_log_target_path(self)

    def get_default_settings(self):
        """Gets default file validation settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "log_mode": VALIDATION_LOG_ISSUES,
            "fail_on_issues": False,
            "minimum_file_size_bytes": 1,
            "maximum_file_size_bytes": "",
            "warn_when_empty": True,
            "warn_when_size_differs_from_group": False,
            "detect_duplicate_checksums": False,
            "checksum_algorithm": "sha1",
            "overwrite": True,
        }

    def validate(self, project):
        """Validates file integrity settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        self.validate_optional_integer(result, self.settings.get("minimum_file_size_bytes"), "minimum file size bytes")
        self.validate_optional_integer(result, self.settings.get("maximum_file_size_bytes"), "maximum file size bytes")
        if self.settings.get("checksum_algorithm") not in ["md5", "sha1", "sha256"]:
            result.add_error("Checksum algorithm must be md5, sha1, or sha256.")
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Validates one file and optionally writes a log.

        Args:
            work_item (WorkItem): Work item to validate.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Log output directory.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Original work item.
        """
        context = context or {}
        issues = self.collect_file_issues(work_item, context.get("work_items") or [])
        has_issues = bool(issues)
        self.write_validation_log_if_needed(work_item, step_output_dir, issues, has_issues, context=context)
        if has_issues and self.settings.get("fail_on_issues"):
            raise RuntimeError("File integrity validation found issues in: {0}".format(work_item.current_path))
        return task_base.WorkItem(
            source_path=work_item.source_path,
            current_path=work_item.current_path,
            metadata=task_utils.build_metadata(self, work_item),
        )

    def collect_file_issues(self, work_item, work_items):
        """Collects file integrity issues.

        Args:
            work_item (WorkItem): Work item to inspect.
            work_items (list): All work items in this task.

        Returns:
            list: Issue dictionaries.
        """
        issues = []
        file_path = work_item.current_path
        if not os.path.isfile(file_path):
            return [{"severity": "Error", "message": "File does not exist.", "path": file_path}]
        file_size = os.path.getsize(file_path)
        min_size = parse_optional_int(self.settings.get("minimum_file_size_bytes"))
        max_size = parse_optional_int(self.settings.get("maximum_file_size_bytes"))
        if self.settings.get("warn_when_empty", True) and file_size == 0:
            issues.append({"severity": "Warning", "message": "File is empty.", "size_bytes": file_size})
        if min_size is not None and file_size < min_size:
            issues.append(
                {
                    "severity": "Warning",
                    "message": "File is smaller than the minimum size.",
                    "size_bytes": file_size,
                    "minimum_file_size_bytes": min_size,
                }
            )
        if max_size is not None and file_size > max_size:
            issues.append(
                {
                    "severity": "Warning",
                    "message": "File is larger than the maximum size.",
                    "size_bytes": file_size,
                    "maximum_file_size_bytes": max_size,
                }
            )
        if self.settings.get("warn_when_size_differs_from_group"):
            group_sizes = []
            for item in work_items:
                if os.path.isfile(item.current_path):
                    group_sizes.append(os.path.getsize(item.current_path))
            group_sizes = sorted(set(group_sizes))
            if len(group_sizes) > 1:
                issues.append(
                    {
                        "severity": "Warning",
                        "message": "File size differs from other files in this task.",
                        "size_bytes": file_size,
                        "all_sizes_bytes": group_sizes,
                    }
                )
        if self.settings.get("detect_duplicate_checksums"):
            checksum = get_file_checksum(file_path, self.settings.get("checksum_algorithm") or "sha1")
            matches = []
            for other_item in work_items:
                other_path = other_item.current_path
                if other_path == file_path or not os.path.isfile(other_path):
                    continue
                if get_file_checksum(other_path, self.settings.get("checksum_algorithm") or "sha1") == checksum:
                    matches.append(other_path)
            if matches:
                issues.append(
                    {
                        "severity": "Warning",
                        "message": "File checksum matches another file.",
                        "checksum": checksum,
                        "matches": matches,
                    }
                )
        return issues

    def write_validation_log_if_needed(self, work_item, step_output_dir, issues, has_issues, context=None):
        """Writes a file validation log when requested.

        Args:
            work_item (WorkItem): Validated work item.
            step_output_dir (str): Log output directory.
            issues (list): Issue dictionaries.
            has_issues (bool): Whether any issues were found.
            context (dict, optional): Runtime context.

        Returns:
            str or None: Written log path, if any.
        """
        return write_task_validation_log(
            task=self,
            step_output_dir=step_output_dir,
            entry={
                "source": work_item.current_path,
                "size_bytes": get_file_size(work_item.current_path),
                "has_issues": bool(has_issues),
                "issues": issues,
            },
            has_issues=has_issues,
            context=context,
        )

    @staticmethod
    def validate_optional_integer(result, value, label):
        """Validates an optional integer setting.

        Args:
            result (ValidationResult): Result object to update.
            value (object): Value to validate.
            label (str): Human-readable label.
        """
        if value in [None, ""]:
            return
        try:
            int(value)
        except (TypeError, ValueError):
            result.add_error("{0} must be an integer value.".format(label.capitalize()))


class TaskValidationFolderCompare(task_base.BatchTask):
    """Task that compares two folders and writes a validation report."""

    task_type = constants.TaskType.FOLDER_COMPARE_VALIDATE
    default_display_name = "Validate Parity"
    default_target_path_template = VALIDATION_LOG_TARGET_PATH_TEMPLATE
    icon = ui_res_lib.Icon.tool_validator
    category = "Validation"
    category_icon = ui_res_lib.Icon.batch_category_validation
    is_indexless_task = True
    is_aggregate_task = True

    def __init__(self, *args, **kwargs):
        """Initializes a folder parity validation task.

        Args:
            *args: Positional arguments passed to BatchTask.
            **kwargs: Keyword arguments passed to BatchTask.
        """
        super().__init__(*args, **kwargs)
        migrate_validation_log_target_path(self)

    def get_default_settings(self):
        """Gets default folder comparison settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "folder_a": "{previous-task-path}",
            "folder_b": "{next-task-path}",
            "comparison_method": FOLDER_COMPARE_RELATIVE_PATHS,
            "include_subdirectories": True,
            "log_mode": VALIDATION_LOG_ISSUES,
            "fail_on_differences": False,
            "overwrite": True,
        }

    def validate(self, project):
        """Validates folder comparison settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        method = self.settings.get("comparison_method")
        if method not in get_folder_compare_methods():
            result.add_error("Unknown folder comparison method: {0}".format(method))
        for key in ["folder_a", "folder_b"]:
            folder_path = self.get_resolved_folder(project, key)
            if not folder_path:
                result.add_error("{0} cannot be empty.".format(key))
            elif not os.path.isdir(folder_path):
                result.add_warning("{0} does not exist: {1}".format(key, folder_path))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Compares two folders and returns incoming work items unchanged.

        Args:
            work_item (WorkItem): Unused aggregate item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Log output directory.
            context (dict, optional): Runtime context.

        Returns:
            list: Original incoming work items.
        """
        context = context or {}
        folder_a = self.get_resolved_folder(project, "folder_a")
        folder_b = self.get_resolved_folder(project, "folder_b")
        report = compare_folders(
            folder_a=folder_a,
            folder_b=folder_b,
            method=self.settings.get("comparison_method") or FOLDER_COMPARE_RELATIVE_PATHS,
            include_subdirectories=bool(self.settings.get("include_subdirectories", True)),
        )
        has_issues = bool(report.get("only_in_a") or report.get("only_in_b") or report.get("changed"))
        log_path = self.write_comparison_log_if_needed(step_output_dir, folder_a, folder_b, report, has_issues)
        task_utils.report_log_artifact(context, log_path)
        if has_issues and self.settings.get("fail_on_differences"):
            raise RuntimeError("Folder comparison found differences.")
        return list(context.get("work_items") or [])

    def write_comparison_log_if_needed(self, step_output_dir, folder_a, folder_b, report, has_issues):
        """Writes the folder comparison log when requested.

        Args:
            step_output_dir (str): Log output directory.
            folder_a (str): First folder.
            folder_b (str): Second folder.
            report (dict): Comparison report.
            has_issues (bool): Whether differences were found.

        Returns:
            str or None: Written log path, if any.
        """
        log_mode = self.settings.get("log_mode") or VALIDATION_LOG_ISSUES
        if log_mode == VALIDATION_LOG_NONE:
            return None
        if log_mode == VALIDATION_LOG_ISSUES and not has_issues:
            return None
        task_name = str(self.display_name or "folder_compare").lower().replace(" ", "_")
        file_name = "validate_{0}.json".format(task_base.sanitize_filename(task_name, "folder_compare"))
        output_path = task_base.normalize_path(os.path.join(step_output_dir, file_name))
        return task_utils.write_json_log(
            output_path,
            {
                "task": self.display_name,
                "task_type": self.task_type,
                "folder_a": folder_a,
                "folder_b": folder_b,
                "comparison_method": self.settings.get("comparison_method"),
                "has_issues": bool(has_issues),
                "report": report,
            },
        )

    def get_resolved_folder(self, project, key):
        """Gets a resolved folder path from task settings.

        Args:
            project (BatchProcessorModel): Active project.
            key (str): Setting key.

        Returns:
            str: Resolved folder path.
        """
        value = self.settings.get(key) or ""
        return project.resolve_template_path(value, task=self) if value else ""


def get_available_scene_validators():
    """Gets validator names registered in the shared validator library.

    Returns:
        list: Validator names.
    """
    try:
        import gt.core.validator as core_validator

        return core_validator.ValidatorLibrary.get_available_validators()
    except Exception:
        return []


def write_task_validation_log(task, step_output_dir, entry, has_issues, context=None):
    """Writes or updates a single validation report for one task.

    Args:
        task (BatchTask): Validation task writing the report.
        step_output_dir (str): Validation log output directory.
        entry (dict): Validation result entry for one work item.
        has_issues (bool): Whether the entry contains issues.
        context (dict, optional): Runtime context.

    Returns:
        str or None: Written log path, if any.
    """
    log_mode = task.settings.get("log_mode") or VALIDATION_LOG_ISSUES
    if log_mode == VALIDATION_LOG_NONE:
        return None
    if log_mode == VALIDATION_LOG_ISSUES and not has_issues:
        return None
    output_path = build_validation_log_path(task, step_output_dir)
    report_entries = get_validation_report_entries(task, output_path, context)
    report_entries.append(dict(entry))
    log_path = task_utils.write_json_log(
        output_path,
        {
            "version": 1,
            "created_at": task_utils.get_timestamp(),
            "task": task.display_name,
            "task_type": task.task_type,
            "has_issues": any(bool(item.get("has_issues")) for item in report_entries),
            "entries": report_entries,
        },
    )
    return task_utils.report_log_artifact(context, log_path)


def build_validation_log_path(task, step_output_dir):
    """Builds the single report path for a validation task.

    Args:
        task (BatchTask): Validation task.
        step_output_dir (str): Validation log output directory.

    Returns:
        str: JSON report path.
    """
    task_name = task.display_name or task.default_display_name or "validation"
    task_name = str(task_name).lower().replace(" ", "_")
    file_name = "validate_{0}.json".format(task_base.sanitize_filename(task_name, "validation"))
    return task_base.normalize_path(os.path.join(step_output_dir, file_name))


def get_validation_report_entries(task, output_path, context=None):
    """Gets the in-memory entry list used while one task run is active.

    Args:
        task (BatchTask): Validation task.
        output_path (str): Report path.
        context (dict, optional): Runtime context.

    Returns:
        list: Mutable report entries.
    """
    context = context or {}
    item_index = int(context.get("item_index") or 0)
    entries_by_path = getattr(task, "_validation_log_entries", None)
    if entries_by_path is None:
        entries_by_path = {}
        setattr(task, "_validation_log_entries", entries_by_path)
    if item_index <= 1 or output_path not in entries_by_path:
        entries_by_path[output_path] = []
    return entries_by_path[output_path]


def get_validator_class(validator_name):
    """Gets a validator class by name.

    Args:
        validator_name (str): Validator name.

    Returns:
        type or None: Validator class.
    """
    try:
        import gt.core.validator as core_validator

        return getattr(core_validator.ValidatorLibrary, str(validator_name), None)
    except Exception:
        return None


def get_validator_scope(scope_name):
    """Gets a validator scope enum member.

    Args:
        scope_name (str): Visible scope name.

    Returns:
        ValidatorScope: Validator scope.
    """
    import gt.core.validator as core_validator

    scope_name = str(scope_name or "Scene").upper()
    if scope_name == "SELECTION":
        return core_validator.ValidatorScope.SELECTION
    if scope_name == "TYPE":
        return core_validator.ValidatorScope.TYPE
    return core_validator.ValidatorScope.SCENE


def get_folder_compare_methods():
    """Gets folder comparison methods.

    Returns:
        list: Comparison method names.
    """
    return [
        FOLDER_COMPARE_RELATIVE_PATHS,
        FOLDER_COMPARE_NAMES_ONLY,
        FOLDER_COMPARE_NAMES_WITHOUT_EXTENSIONS,
        FOLDER_COMPARE_CHECKSUM,
    ]


def compare_folders(folder_a, folder_b, method=FOLDER_COMPARE_RELATIVE_PATHS, include_subdirectories=True):
    """Compares two folders.

    Args:
        folder_a (str): First folder path.
        folder_b (str): Second folder path.
        method (str, optional): Comparison method.
        include_subdirectories (bool, optional): Whether to walk subdirectories.

    Returns:
        dict: Comparison report.
    """
    files_a = build_folder_signature(folder_a, method, include_subdirectories)
    files_b = build_folder_signature(folder_b, method, include_subdirectories)
    keys_a = set(files_a.keys())
    keys_b = set(files_b.keys())
    shared_keys = sorted(keys_a.intersection(keys_b))
    changed = []
    if method == FOLDER_COMPARE_CHECKSUM:
        for key in shared_keys:
            if files_a.get(key) != files_b.get(key):
                changed.append({"key": key, "folder_a": files_a.get(key), "folder_b": files_b.get(key)})
    return {
        "only_in_a": sorted(keys_a.difference(keys_b)),
        "only_in_b": sorted(keys_b.difference(keys_a)),
        "changed": changed,
        "matched": shared_keys,
        "count_a": len(keys_a),
        "count_b": len(keys_b),
    }


def build_folder_signature(folder_path, method, include_subdirectories):
    """Builds a dictionary representing a folder for comparison.

    Args:
        folder_path (str): Folder path.
        method (str): Comparison method.
        include_subdirectories (bool): Whether to include nested files.

    Returns:
        dict: Mapping of comparison keys to file paths or hashes.
    """
    signature = {}
    if not os.path.isdir(folder_path):
        return signature
    if include_subdirectories:
        walker = os.walk(folder_path)
    else:
        walker = [(folder_path, [], os.listdir(folder_path))]
    for root, _, file_names in walker:
        for file_name in file_names:
            file_path = os.path.join(root, file_name)
            if not os.path.isfile(file_path):
                continue
            key = build_folder_compare_key(file_path, folder_path, method)
            value = task_base.normalize_path(file_path)
            if method == FOLDER_COMPARE_CHECKSUM:
                value = get_file_checksum(file_path, "sha1")
            signature[key] = value
    return signature


def build_folder_compare_key(file_path, folder_path, method):
    """Builds a comparison key for a file.

    Args:
        file_path (str): File path.
        folder_path (str): Root folder path.
        method (str): Comparison method.

    Returns:
        str: Comparison key.
    """
    if method == FOLDER_COMPARE_NAMES_ONLY:
        return os.path.basename(file_path).lower()
    if method == FOLDER_COMPARE_NAMES_WITHOUT_EXTENSIONS:
        return os.path.splitext(os.path.basename(file_path))[0].lower()
    relative_path = os.path.relpath(file_path, folder_path).replace("\\", "/")
    return relative_path.lower()


def get_file_checksum(file_path, algorithm="sha1", block_size=65536):
    """Gets a file checksum.

    Args:
        file_path (str): File path.
        algorithm (str, optional): Hash algorithm.
        block_size (int, optional): Read block size.

    Returns:
        str: Hex digest.
    """
    hash_object = hashlib.new(algorithm)
    with open(file_path, "rb") as file_stream:
        for chunk in iter(lambda: file_stream.read(block_size), b""):
            hash_object.update(chunk)
    return hash_object.hexdigest()


def get_file_size(file_path):
    """Gets the size of a file if it exists.

    Args:
        file_path (str): File path.

    Returns:
        int or None: File size in bytes.
    """
    if not os.path.isfile(file_path):
        return None
    return os.path.getsize(file_path)


def parse_optional_int(value):
    """Parses an optional integer.

    Args:
        value (object): Value to parse.

    Returns:
        int or None: Parsed integer.
    """
    if value in [None, ""]:
        return None
    return int(value)
