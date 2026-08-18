"""
Batch Processor Map Hierarchy Task

State-mapping task that records the file/folder hierarchy of a directory, maps
it to a target directory structure, and stores the result as a reusable
Snapshot. The Snapshot can then be applied forward, reverted backward, or
applied to a parallel directory containing related files with different
extensions.

This module is pure Python and stays importable outside Maya.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tasks import task_utils
import hashlib
import json
import os
import shutil


CHECKSUM_ALGORITHMS = ["sha1", "sha256", "md5"]

MODE_RECORD_SOURCE = "Record Source Snapshot"
MODE_RECORD_TARGET = "Record Target Snapshot"
MODE_RECORD_SOURCE_TARGET = "Record Source/Target Snapshot"
MODE_APPLY_FORWARD = "Apply Mapping (Forward)"
MODE_REVERT_BACKWARD = "Revert Mapping (Backward)"
MODE_COPY_APPLY_FORWARD = "Copy Source & Apply (Forward)"
MODE_APPLY_PARALLEL_FORWARD = "Apply to Parallel (Forward)"
MODE_REVERT_PARALLEL_BACKWARD = "Revert Parallel (Backward)"
MODE_BYPASS = "Bypass Task"
MODE_VALUES = [
    MODE_RECORD_SOURCE,
    MODE_RECORD_TARGET,
    MODE_RECORD_SOURCE_TARGET,
    MODE_APPLY_FORWARD,
    MODE_REVERT_BACKWARD,
    MODE_COPY_APPLY_FORWARD,
    MODE_APPLY_PARALLEL_FORWARD,
    MODE_REVERT_PARALLEL_BACKWARD,
    MODE_BYPASS,
]
RECORD_MODES = [MODE_RECORD_SOURCE, MODE_RECORD_TARGET, MODE_RECORD_SOURCE_TARGET]
DIRECTIONAL_MODES = [MODE_APPLY_FORWARD, MODE_REVERT_BACKWARD]
PARALLEL_MODES = [MODE_APPLY_PARALLEL_FORWARD, MODE_REVERT_PARALLEL_BACKWARD]
COPY_MODES = [MODE_COPY_APPLY_FORWARD]
APPLY_MODES = DIRECTIONAL_MODES + COPY_MODES + PARALLEL_MODES
# Modes that read files from the source directory and must never modify it.
FORWARD_MODES = [MODE_APPLY_FORWARD, MODE_COPY_APPLY_FORWARD, MODE_APPLY_PARALLEL_FORWARD]

ENTRY_FILE = "file"
ENTRY_FOLDER = "folder"

STATUS_UNCHANGED = "Unchanged"
STATUS_MOVED = "Moved"
STATUS_RENAMED = "Renamed"
STATUS_DELETED = "Deleted"
STATUS_ADDED = "Added"
MODIFICATION_STATUSES = [STATUS_MOVED, STATUS_RENAMED, STATUS_DELETED]
TRANSFERABLE_STATUSES = [STATUS_UNCHANGED, STATUS_RENAMED, STATUS_MOVED]

# Setting 1: Source is missing, but target exists.
MISSING_SOURCE_ASSUME_APPLIED = "Assume Already Applied (Skip)"
MISSING_SOURCE_FLAG_ERROR = "Flag as Error"
MISSING_SOURCE_OPTIONS = [MISSING_SOURCE_ASSUME_APPLIED, MISSING_SOURCE_FLAG_ERROR]

# Setting 2: Files present in the working directory but missing from the snapshot,
# encountered by forward/copy/parallel-forward modes. Source files are never modified,
# so this setting can only report (never delete or move) these files.
ORPHAN_IGNORE = "Ignore"
ORPHAN_FLAG_WARNING = "Flag as Warning"
ORPHAN_FLAG_ERROR = "Flag as Error"
ORPHAN_OPTIONS = [ORPHAN_IGNORE, ORPHAN_FLAG_WARNING, ORPHAN_FLAG_ERROR]

# Setting 3: Files present in the apply/target directory but missing from the snapshot,
# encountered by revert modes. The apply/target directory is a working copy, so these
# files may be cleaned up.
UNMAPPED_IGNORE = "Ignore (Leave as-is)"
UNMAPPED_DELETE = "Delete Permanently"
UNMAPPED_ISOLATE = "Move to '_unmapped' Folder"
UNMAPPED_OPTIONS = [UNMAPPED_IGNORE, UNMAPPED_DELETE, UNMAPPED_ISOLATE]
UNMAPPED_FOLDER_NAME = "_unmapped"

# Edge case: destination collisions.
COLLISION_SUFFIX = "Append Suffix"
COLLISION_ERROR = "Flag as Error"
COLLISION_OPTIONS = [COLLISION_SUFFIX, COLLISION_ERROR]

ISOLATION_FOLDER_NAMES = [UNMAPPED_FOLDER_NAME]

# Plan operation actions.
ACTION_MOVE = "move"
ACTION_COPY = "copy"
ACTION_DELETE = "delete"
ACTION_ISOLATE = "isolate"
ACTION_SKIP = "skip"
ACTION_WARN = "warn"
ACTION_ERROR = "error"

# Snapshot summary status values and colors used by the UI summary panel.
SUMMARY_STATUS_NO_FILE = "No File"
SUMMARY_STATUS_UNREADABLE = "Unreadable File"
SUMMARY_STATUS_MISSING_BOTH = "Missing Source/Target Data"
SUMMARY_STATUS_MISSING_TARGET = "Missing Target Data"
SUMMARY_STATUS_MISSING_SOURCE = "Missing Source Data"
SUMMARY_STATUS_NO_MAPPING = "Missing Mapping Data"
SUMMARY_STATUS_READY = "Ready"
COLOR_STATUS_READY = "#5fb04f"
COLOR_STATUS_WARNING = "#d6a13d"
COLOR_STATUS_ERROR = "#c0554e"
COLOR_STATUS_NEUTRAL = "#888888"

SNAPSHOT_VERSION = 1


class TaskMapHierarchy(task_base.BatchTask):
    """Task that records, maps, and applies file/folder hierarchy Snapshots."""

    task_type = constants.TaskType.MAP_HIERARCHY
    default_display_name = "Map Hierarchy"
    default_target_path_template = "{project-dir}/{output-dir}"
    icon = ui_res_lib.Icon.batch_task_map_hierarchy
    category = "Utilities"
    category_icon = ui_res_lib.Icon.root_utilities
    is_aggregate_task = True
    is_data_load_task = True
    supports_run_once_after_jobs = True

    def get_default_settings(self):
        """Gets default Map Hierarchy settings.

        Returns:
            dict: Default settings.
        """
        return {
            "include_in_task_index": False,
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "mode": MODE_RECORD_SOURCE,
            "snapshot_path": "{project-dir}/data/hierarchy_snapshot_data.json",
            "source_dir": "{previous-task-path}",
            "target_dir": "{previous-task-path}",
            "apply_dir": "",
            "use_apply_dir": False,
            "include_subdirectories": True,
            "checksum_algorithm": "sha1",
            "missing_source_resolution": MISSING_SOURCE_ASSUME_APPLIED,
            "source_orphan_resolution": ORPHAN_IGNORE,
            "target_unmapped_resolution": UNMAPPED_IGNORE,
            "cleanup_empty_folders": True,
            "collision_resolution": COLLISION_SUFFIX,
            "dry_run": False,
            "write_report": True,
            "report_path": "{project-dir}/logs/map_hierarchy_{task-idx}.json",
            "overwrite": True,
            "run_once_after_multi_instance": True,
            "force_segment_separator": False,
            "segment_name": "",
            "segment_color": "blue_light_sky",
        }

    def validate(self, project):
        """Validates Map Hierarchy settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        mode = self.settings.get("mode")
        if mode not in MODE_VALUES:
            result.add_error(f"Map Hierarchy mode must be one of: {', '.join(MODE_VALUES)}.")
            return result
        if mode == MODE_BYPASS:
            return result
        if self.settings.get("checksum_algorithm") not in CHECKSUM_ALGORITHMS:
            result.add_error(f"Map Hierarchy checksum algorithm must be one of: {', '.join(CHECKSUM_ALGORITHMS)}.")
        snapshot_path = self.get_snapshot_path(project)
        if not snapshot_path:
            result.add_error("Map Hierarchy snapshot path is empty.")
        if mode in [MODE_RECORD_SOURCE, MODE_RECORD_SOURCE_TARGET]:
            self._validate_existing_dir(result, project, "source_dir", "Source directory")
        if mode in [MODE_RECORD_TARGET, MODE_RECORD_SOURCE_TARGET]:
            self._validate_existing_dir(result, project, "target_dir", "Target directory")
        if mode == MODE_RECORD_TARGET and snapshot_path and not self._snapshot_has_source(snapshot_path):
            result.add_error(
                "Map Hierarchy Record Target requires an existing snapshot with a recorded source. "
                f"Run Record Source first: {snapshot_path}"
            )
        apply_root_label = "Apply directory" if self.settings.get("use_apply_dir") else "Target directory"
        if mode in APPLY_MODES:
            self._validate_snapshot_mapping(result, snapshot_path)
            apply_root = self.get_apply_root(project)
            if not apply_root:
                result.add_error(f"Map Hierarchy {apply_root_label} is empty.")
            elif not os.path.isdir(apply_root):
                result.add_error(f"Map Hierarchy {apply_root_label} does not exist: {apply_root}")
            self._validate_enum(result, "missing_source_resolution", MISSING_SOURCE_OPTIONS, "State resolution")
            self._validate_enum(result, "source_orphan_resolution", ORPHAN_OPTIONS, "Source orphan resolution")
            self._validate_enum(result, "target_unmapped_resolution", UNMAPPED_OPTIONS, "Target unmapped resolution")
            self._validate_enum(result, "collision_resolution", COLLISION_OPTIONS, "Collision resolution")
        if mode == MODE_COPY_APPLY_FORWARD:
            self._validate_existing_dir(result, project, "source_dir", "Source directory")
            source_root = self.get_directory(project, "source_dir")
            apply_root = self.get_apply_root(project)
            if source_root and apply_root and paths_overlap(source_root, apply_root):
                result.add_error(
                    "Copy Source & Apply requires the apply directory to be separate from the source "
                    f"directory so the source is never modified: {apply_root}"
                )
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Runs the configured Map Hierarchy mode and returns incoming work items.

        Args:
            work_item (WorkItem): Unused aggregate work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Cooked output folder.
            context (dict, optional): Runtime context containing work_items.

        Returns:
            list: Incoming work items, unchanged.
        """
        context = context or {}
        work_items = context.get("work_items") or []
        mode = self.settings.get("mode")
        if mode == MODE_BYPASS:
            raise task_base.TaskSkip("Map Hierarchy bypassed.", work_item=list(work_items))
        if mode in RECORD_MODES:
            snapshot_path = self.record_snapshot(project=project, mode=mode)
            task_utils.report_log_artifact(context, snapshot_path)
            return list(work_items)
        operations = self.apply_snapshot(project=project, mode=mode)
        self.write_operations_report(project=project, mode=mode, operations=operations, context=context)
        return list(work_items)

    # ------------------------------------------------------------------ record

    def record_snapshot(self, project, mode):
        """Records a source, target, or combined Snapshot to disk.

        Args:
            project (BatchProcessorModel): Active project.
            mode (str): Active record mode.

        Returns:
            str: Written snapshot path.
        """
        snapshot_path = self.get_snapshot_path(project)
        algorithm = self.settings.get("checksum_algorithm") or "sha1"
        include_subdirectories = bool(self.settings.get("include_subdirectories", True))
        snapshot = self.load_snapshot(snapshot_path) if os.path.isfile(snapshot_path) else {}
        snapshot.setdefault("version", SNAPSHOT_VERSION)
        snapshot["checksum_algorithm"] = algorithm
        if mode in [MODE_RECORD_SOURCE, MODE_RECORD_SOURCE_TARGET]:
            source_root = self.get_directory(project, "source_dir")
            snapshot["source_root"] = source_root
            snapshot["source_entries"] = scan_directory_entries(source_root, algorithm, include_subdirectories)
        if mode in [MODE_RECORD_TARGET, MODE_RECORD_SOURCE_TARGET]:
            target_root = self.get_directory(project, "target_dir")
            snapshot["target_root"] = target_root
            snapshot["target_entries"] = scan_directory_entries(target_root, algorithm, include_subdirectories)
        if mode == MODE_RECORD_SOURCE:
            snapshot.pop("target_entries", None)
            snapshot.pop("mapping", None)
        if mode in [MODE_RECORD_TARGET, MODE_RECORD_SOURCE_TARGET]:
            source_entries = snapshot.get("source_entries") or empty_entries()
            snapshot["mapping"] = compute_mapping(source_entries, snapshot.get("target_entries") or empty_entries())
        snapshot["created_at"] = task_utils.get_timestamp()
        snapshot["metadata"] = build_metadata_header(snapshot)
        task_utils.write_json_log(snapshot_path, snapshot)
        return snapshot_path

    # ------------------------------------------------------------------- apply

    def apply_snapshot(self, project, mode):
        """Builds and executes the operation plan for an apply mode.

        Args:
            project (BatchProcessorModel): Active project.
            mode (str): Active apply mode.

        Returns:
            list: Executed operation dictionaries.
        """
        plan = self.build_plan(project=project, mode=mode)
        blocking_errors = [op for op in plan if op.get("action") == ACTION_ERROR]
        if blocking_errors:
            messages = "; ".join(op.get("reason", "") for op in blocking_errors[:5])
            raise RuntimeError(f"Map Hierarchy cannot proceed due to unresolved issues: {messages}")
        dry_run = bool(self.settings.get("dry_run", False))
        operations = execute_plan(plan, dry_run=dry_run)
        if not dry_run and self.settings.get("cleanup_empty_folders", True):
            cleanup_empty_folders(self.get_apply_root(project))
        return operations

    def get_apply_root(self, project):
        """Gets the working directory used by apply, revert, copy, and parallel modes.

        The apply directory also serves as the parallel directory. When the
        dedicated apply directory is disabled, the target directory is used instead.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Resolved working directory path.
        """
        if self.settings.get("use_apply_dir"):
            return self.get_directory(project, "apply_dir")
        return self.get_directory(project, "target_dir")

    def build_plan(self, project, mode):
        """Builds an operation plan for an apply mode without executing it.

        Args:
            project (BatchProcessorModel): Active project.
            mode (str): Active apply mode.

        Returns:
            list: Planned operation dictionaries.
        """
        snapshot_path = self.get_snapshot_path(project)
        snapshot = self.load_snapshot(snapshot_path)
        mapping = snapshot.get("mapping") or []
        apply_root = self.get_apply_root(project)
        if mode in PARALLEL_MODES:
            forward = mode == MODE_APPLY_PARALLEL_FORWARD
            return build_parallel_plan(root=apply_root, mapping=mapping, forward=forward, settings=self.settings)
        if mode == MODE_COPY_APPLY_FORWARD:
            source_root = self.get_directory(project, "source_dir")
            return build_copy_apply_plan(
                source_root=source_root, dest_root=apply_root, mapping=mapping, settings=self.settings
            )
        forward = mode == MODE_APPLY_FORWARD
        return build_directional_plan(root=apply_root, mapping=mapping, forward=forward, settings=self.settings)

    def write_operations_report(self, project, mode, operations, context=None):
        """Writes an audit report describing executed operations.

        Args:
            project (BatchProcessorModel): Active project.
            mode (str): Active apply mode.
            operations (list): Executed operation dictionaries.
            context (dict, optional): Runtime context.
        """
        if not self.settings.get("write_report", True):
            return
        report_path = project.resolve_template_path(self.settings.get("report_path"), task=self)
        if not report_path:
            return
        task_utils.write_json_log(
            report_path,
            {
                "version": SNAPSHOT_VERSION,
                "created_at": task_utils.get_timestamp(),
                "mode": mode,
                "dry_run": bool(self.settings.get("dry_run", False)),
                "snapshot_path": self.get_snapshot_path(project),
                "operations": [serialize_operation(op) for op in operations],
                "summary": summarize_operations(operations),
            },
        )
        task_utils.report_log_artifact(context, report_path)

    # ---------------------------------------------------------------- helpers

    def get_snapshot_path(self, project):
        """Gets the resolved snapshot path.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Resolved snapshot path.
        """
        snapshot_path = self.settings.get("snapshot_path") or ""
        return project.resolve_template_path(snapshot_path, task=self) if snapshot_path else ""

    def get_directory(self, project, key):
        """Gets a resolved directory setting.

        Args:
            project (BatchProcessorModel): Active project.
            key (str): Setting key.

        Returns:
            str: Resolved directory path.
        """
        return project.resolve_template_path(self.settings.get(key), task=self)

    @staticmethod
    def load_snapshot(snapshot_path):
        """Loads a snapshot JSON file.

        Args:
            snapshot_path (str): Snapshot file path.

        Returns:
            dict: Snapshot payload.
        """
        with open(snapshot_path, "r", encoding="utf-8") as snapshot_file:
            data = json.load(snapshot_file)
        return data if isinstance(data, dict) else {}

    def read_snapshot_metadata(self, project):
        """Reads the metadata header of the active snapshot for UI summaries.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict or None: Metadata header, or None when unavailable.
        """
        snapshot_path = self.get_snapshot_path(project)
        if not snapshot_path or not os.path.isfile(snapshot_path):
            return None
        try:
            snapshot = self.load_snapshot(snapshot_path)
        except (ValueError, OSError):
            return None
        metadata = snapshot.get("metadata")
        if isinstance(metadata, dict):
            return metadata
        return build_metadata_header(snapshot)

    def get_snapshot_status(self, project):
        """Gets a readiness status for the active snapshot for the UI summary.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict: Status with "text" and "color" keys.
        """
        snapshot_path = self.get_snapshot_path(project)
        if not snapshot_path or not os.path.isfile(snapshot_path):
            return {"text": SUMMARY_STATUS_NO_FILE, "color": COLOR_STATUS_NEUTRAL}
        try:
            snapshot = self.load_snapshot(snapshot_path)
        except (ValueError, OSError):
            return {"text": SUMMARY_STATUS_UNREADABLE, "color": COLOR_STATUS_ERROR}
        has_source = (snapshot.get("source_entries") or {}).get("files") is not None
        has_target = (snapshot.get("target_entries") or {}).get("files") is not None
        has_mapping = bool(snapshot.get("mapping"))
        if not has_source and not has_target:
            return {"text": SUMMARY_STATUS_MISSING_BOTH, "color": COLOR_STATUS_ERROR}
        if not has_target:
            return {"text": SUMMARY_STATUS_MISSING_TARGET, "color": COLOR_STATUS_WARNING}
        if not has_source:
            return {"text": SUMMARY_STATUS_MISSING_SOURCE, "color": COLOR_STATUS_WARNING}
        if not has_mapping:
            return {"text": SUMMARY_STATUS_NO_MAPPING, "color": COLOR_STATUS_WARNING}
        return {"text": SUMMARY_STATUS_READY, "color": COLOR_STATUS_READY}

    def preview_lines(self, project):
        """Builds human-readable preview lines for the active mode.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            list: Preview text lines.
        """
        mode = self.settings.get("mode")
        if mode not in APPLY_MODES:
            snapshot_path = self.get_snapshot_path(project)
            if not snapshot_path or not os.path.isfile(snapshot_path):
                return ["No snapshot file is available to preview yet."]
            snapshot = self.load_snapshot(snapshot_path)
            return describe_mapping(snapshot.get("mapping") or [])
        plan = self.build_plan(project=project, mode=mode)
        return describe_plan(plan)

    def _validate_existing_dir(self, result, project, key, label):
        """Validates that a resolved directory setting exists.

        Args:
            result (ValidationResult): Result to update.
            project (BatchProcessorModel): Active project.
            key (str): Setting key.
            label (str): User-facing label.
        """
        directory = self.get_directory(project, key)
        if not directory:
            result.add_error(f"Map Hierarchy {label} is empty.")
        elif not os.path.isdir(directory):
            result.add_error(f"Map Hierarchy {label} does not exist: {directory}")

    def _validate_enum(self, result, key, allowed_values, label):
        """Validates that a setting value is one of the allowed values.

        Args:
            result (ValidationResult): Result to update.
            key (str): Setting key.
            allowed_values (list): Allowed values.
            label (str): User-facing label.
        """
        if self.settings.get(key) not in allowed_values:
            result.add_error(f"Map Hierarchy {label} must be one of: {', '.join(allowed_values)}.")

    def _validate_snapshot_mapping(self, result, snapshot_path):
        """Validates that a snapshot file exists and contains a mapping.

        Args:
            result (ValidationResult): Result to update.
            snapshot_path (str): Snapshot path.
        """
        if not snapshot_path:
            return
        if not os.path.isfile(snapshot_path):
            result.add_error(f"Map Hierarchy snapshot file does not exist: {snapshot_path}")
            return
        try:
            snapshot = self.load_snapshot(snapshot_path)
        except (ValueError, OSError) as exception:
            result.add_error(f"Map Hierarchy snapshot file could not be read: {exception}")
            return
        if not snapshot.get("mapping"):
            result.add_error(
                "Map Hierarchy snapshot does not contain a mapping. Record a target snapshot before applying."
            )

    @staticmethod
    def _snapshot_has_source(snapshot_path):
        """Checks whether a snapshot file already recorded a source state.

        Args:
            snapshot_path (str): Snapshot path.

        Returns:
            bool: True when the snapshot has recorded source entries.
        """
        if not os.path.isfile(snapshot_path):
            return False
        try:
            with open(snapshot_path, "r", encoding="utf-8") as snapshot_file:
                data = json.load(snapshot_file)
        except (ValueError, OSError):
            return False
        return bool(isinstance(data, dict) and data.get("source_entries", {}).get("files") is not None)


# --------------------------------------------------------------------- scanning


def empty_entries():
    """Builds an empty directory-entries structure.

    Returns:
        dict: Structure with empty file and folder collections.
    """
    return {"files": [], "folders": []}


def scan_directory_entries(root, algorithm, include_subdirectories=True):
    """Scans a directory and records its files and folders.

    Args:
        root (str): Directory to scan.
        algorithm (str): Checksum algorithm used for file records.
        include_subdirectories (bool, optional): Whether to walk nested folders.

    Returns:
        dict: Structure with hashed file records and relative folder paths.
    """
    root = task_base.normalize_path(root)
    files = []
    folders = set()
    if not root or not os.path.isdir(root):
        return {"files": files, "folders": []}
    if include_subdirectories:
        walker = os.walk(root)
    else:
        walker = [(root, [], os.listdir(root))]
    for current_root, _, file_names in walker:
        relative_dir = to_relative(current_root, root)
        if relative_dir:
            folders.add(relative_dir)
        for file_name in file_names:
            file_path = os.path.join(current_root, file_name)
            if not os.path.isfile(file_path):
                continue
            relative_path = to_relative(file_path, root)
            files.append(
                {
                    "relative_path": relative_path,
                    "checksum": get_file_checksum(file_path, algorithm),
                    "size": os.path.getsize(file_path),
                }
            )
    files.sort(key=lambda record: record["relative_path"])
    return {"files": files, "folders": sorted(folders)}


def to_relative(path, root):
    """Gets a forward-slash relative path from a root.

    Args:
        path (str): Absolute path.
        root (str): Root directory.

    Returns:
        str: Relative path using forward slashes, empty for the root itself.
    """
    relative_path = os.path.relpath(path, root).replace("\\", "/")
    if relative_path == ".":
        return ""
    return relative_path


def get_file_checksum(file_path, algorithm):
    """Gets a checksum for a file.

    Args:
        file_path (str): File path.
        algorithm (str): Hash algorithm name.

    Returns:
        str: Checksum string.
    """
    hash_object = hashlib.new(algorithm or "sha1")
    with open(file_path, "rb") as open_file:
        for chunk in iter(lambda: open_file.read(1024 * 1024), b""):
            hash_object.update(chunk)
    return hash_object.hexdigest()


# ---------------------------------------------------------------------- mapping


def compute_mapping(source_entries, target_entries):
    """Computes a mapping array between recorded source and target states.

    Files are matched by content checksum so renamed or moved files are
    detected even when their path changed. Files present only in the source are
    marked deleted, and files present only in the target are marked added.

    Args:
        source_entries (dict): Recorded source entries.
        target_entries (dict): Recorded target entries.

    Returns:
        list: Mapping entries describing each file and changed folder.
    """
    source_files = source_entries.get("files") or []
    target_files = target_entries.get("files") or []
    target_by_checksum = {}
    for record in target_files:
        target_by_checksum.setdefault(record.get("checksum"), []).append(record.get("relative_path"))
    for candidates in target_by_checksum.values():
        candidates.sort()
    used_targets = set()
    mapping = []
    for record in sorted(source_files, key=lambda item: item.get("relative_path") or ""):
        source_relative = record.get("relative_path") or ""
        checksum = record.get("checksum")
        chosen_target = pick_target(source_relative, target_by_checksum.get(checksum) or [], used_targets)
        if chosen_target is None:
            mapping.append(build_file_entry(source_relative, "", STATUS_DELETED))
            continue
        used_targets.add(chosen_target)
        status = classify_change(source_relative, chosen_target)
        mapping.append(build_file_entry(source_relative, chosen_target, status))
    for record in sorted(target_files, key=lambda item: item.get("relative_path") or ""):
        target_relative = record.get("relative_path") or ""
        if target_relative not in used_targets:
            mapping.append(build_file_entry("", target_relative, STATUS_ADDED))
    mapping.extend(build_folder_entries(source_entries.get("folders") or [], target_entries.get("folders") or []))
    return mapping


def pick_target(source_relative, candidates, used_targets):
    """Picks the best matching target path for a source file.

    Args:
        source_relative (str): Source relative path.
        candidates (list): Target relative paths sharing the source checksum.
        used_targets (set): Target paths already claimed by other source files.

    Returns:
        str or None: Chosen target relative path, or None when unmatched.
    """
    available = [candidate for candidate in candidates if candidate not in used_targets]
    if not available:
        return None
    for candidate in available:
        if candidate == source_relative:
            return candidate
    source_name = os.path.basename(source_relative)
    for candidate in available:
        if os.path.basename(candidate) == source_name:
            return candidate
    return available[0]


def classify_change(source_relative, target_relative):
    """Classifies the change between a source and target path.

    Args:
        source_relative (str): Source relative path.
        target_relative (str): Target relative path.

    Returns:
        str: Status value.
    """
    if source_relative == target_relative:
        return STATUS_UNCHANGED
    if os.path.dirname(source_relative) == os.path.dirname(target_relative):
        return STATUS_RENAMED
    return STATUS_MOVED


def build_file_entry(original_relative_path, target_relative_path, status):
    """Builds a single file mapping entry.

    Args:
        original_relative_path (str): Original relative path.
        target_relative_path (str): Target relative path.
        status (str): Status value.

    Returns:
        dict: Mapping entry.
    """
    return {
        "type": ENTRY_FILE,
        "original_relative_path": original_relative_path,
        "target_relative_path": target_relative_path,
        "status": status,
    }


def build_folder_entries(source_folders, target_folders):
    """Builds mapping entries for added and deleted folders.

    Args:
        source_folders (list): Source relative folder paths.
        target_folders (list): Target relative folder paths.

    Returns:
        list: Folder mapping entries.
    """
    source_set = set(source_folders)
    target_set = set(target_folders)
    entries = []
    for folder in sorted(source_set - target_set):
        entries.append(
            {
                "type": ENTRY_FOLDER,
                "original_relative_path": folder,
                "target_relative_path": "",
                "status": STATUS_DELETED,
            }
        )
    for folder in sorted(target_set - source_set):
        entries.append(
            {
                "type": ENTRY_FOLDER,
                "original_relative_path": "",
                "target_relative_path": folder,
                "status": STATUS_ADDED,
            }
        )
    return entries


def build_metadata_header(snapshot):
    """Builds the metadata header for a snapshot.

    Args:
        snapshot (dict): Snapshot payload.

    Returns:
        dict: Metadata header with counts and required modifications.
    """
    source_entries = snapshot.get("source_entries") or empty_entries()
    target_entries = snapshot.get("target_entries") or empty_entries()
    mapping = snapshot.get("mapping") or []
    modifications = sum(1 for entry in mapping if entry.get("status") in MODIFICATION_STATUSES)
    return {
        "source_file_count": len(source_entries.get("files") or []),
        "source_folder_count": len(source_entries.get("folders") or []),
        "target_file_count": len(target_entries.get("files") or []),
        "target_folder_count": len(target_entries.get("folders") or []),
        "modifications_required": modifications,
    }


# ------------------------------------------------------------------- planning


def build_directional_plan(root, mapping, forward, settings):
    """Builds an operation plan for forward apply or backward revert.

    Args:
        root (str): Working directory whose state is transformed.
        mapping (list): Snapshot mapping entries.
        forward (bool): True for forward apply, False for backward revert.
        settings (dict): Task settings.

    Returns:
        list: Planned operation dictionaries.
    """
    root = task_base.normalize_path(root)
    file_entries = [entry for entry in mapping if entry.get("type", ENTRY_FILE) == ENTRY_FILE]
    plan = []
    known_from = set()
    known_to = set()
    for entry in file_entries:
        from_relative, to_relative, status = directional_endpoints(entry, forward)
        if from_relative:
            known_from.add(normalize_relative(from_relative))
        if to_relative:
            known_to.add(normalize_relative(to_relative))
        if status == STATUS_UNCHANGED:
            continue
        if not to_relative:
            plan.append(build_delete_op(root, from_relative, status))
            continue
        if not from_relative:
            plan.append(
                build_op(
                    ACTION_WARN,
                    status=status,
                    reason=f"Cannot recreate content for added file: {to_relative}",
                    dst_relative=to_relative,
                )
            )
            continue
        plan.append(resolve_move_op(root, from_relative, to_relative, status, settings))
    reference_paths = known_from | known_to
    plan.extend(build_leftover_ops(root, reference_paths, forward=forward, settings=settings))
    return plan


def directional_endpoints(entry, forward):
    """Gets the from-path, to-path, and effective status for a direction.

    Args:
        entry (dict): File mapping entry.
        forward (bool): True for forward apply, False for backward revert.

    Returns:
        tuple: (from_relative, to_relative, status).
    """
    original = entry.get("original_relative_path") or ""
    target = entry.get("target_relative_path") or ""
    status = entry.get("status") or STATUS_UNCHANGED
    if forward:
        return original, target, status
    # Reverting swaps direction; added/deleted invert accordingly.
    if status == STATUS_ADDED:
        return target, "", STATUS_DELETED
    if status == STATUS_DELETED:
        return "", original, STATUS_ADDED
    return target, original, status


def build_parallel_plan(root, mapping, forward, settings):
    """Builds an operation plan for a parallel directory using base-name matches.

    The mapping is applied to a root that holds related files with potentially
    different extensions. Each mapped path has its extension stripped, the
    matching base name is located in the parallel directory, and the file is
    routed to the paired path using the parallel file's actual extension.

    Args:
        root (str): Parallel directory root (the apply directory).
        mapping (list): Snapshot mapping entries.
        forward (bool): True to apply forward, False to revert backward.
        settings (dict): Task settings.

    Returns:
        list: Planned operation dictionaries.
    """
    root = task_base.normalize_path(root)
    parallel_by_stem = index_files_by_stem(root)
    plan = []
    matched_paths = set()
    known_to = set()
    for entry in mapping:
        if entry.get("type", ENTRY_FILE) != ENTRY_FILE:
            continue
        if entry.get("status") not in TRANSFERABLE_STATUSES:
            continue
        original = entry.get("original_relative_path") or ""
        target = entry.get("target_relative_path") or ""
        if not original or not target:
            continue
        from_base = original if forward else target
        to_base = target if forward else original
        stem = strip_extension(from_base)
        for parallel_relative in parallel_by_stem.get(stem, []):
            matched_paths.add(normalize_relative(parallel_relative))
            routed_target = replace_extension(to_base, os.path.splitext(parallel_relative)[1])
            known_to.add(normalize_relative(routed_target))
            if normalize_relative(parallel_relative) == normalize_relative(routed_target):
                continue
            plan.append(resolve_move_op(root, parallel_relative, routed_target, entry.get("status"), settings))
    reference_paths = matched_paths | known_to
    plan.extend(build_leftover_ops(root, reference_paths, forward=forward, settings=settings))
    return plan


def build_copy_apply_plan(source_root, dest_root, mapping, settings):
    """Builds a plan that copies source files into the target structure.

    This is a fully non-destructive forward apply: each mapped source file is
    copied from the source directory into the destination directory at its
    target relative path. The source directory is only read, never modified.

    Args:
        source_root (str): Source directory (read-only).
        dest_root (str): Destination directory that receives the copied structure.
        mapping (list): Snapshot mapping entries.
        settings (dict): Task settings.

    Returns:
        list: Planned operation dictionaries.
    """
    source_root = task_base.normalize_path(source_root)
    dest_root = task_base.normalize_path(dest_root)
    plan = []
    for entry in mapping:
        if entry.get("type", ENTRY_FILE) != ENTRY_FILE:
            continue
        status = entry.get("status")
        if status not in TRANSFERABLE_STATUSES:
            continue
        original = entry.get("original_relative_path") or ""
        target = entry.get("target_relative_path") or ""
        if not original or not target:
            continue
        src_abs = os.path.join(source_root, os.path.normpath(original))
        dst_abs = os.path.join(dest_root, os.path.normpath(target))
        plan.append(
            resolve_transfer_op(
                src_abs=src_abs,
                dst_abs=dst_abs,
                from_relative=original,
                to_relative=target,
                status=status,
                settings=settings,
                action=ACTION_COPY,
                display_root=dest_root,
            )
        )
    return plan


def index_files_by_stem(root):
    """Indexes files in a directory by their extension-stripped relative path.

    Args:
        root (str): Directory root.

    Returns:
        dict: Mapping of stem keys to lists of relative file paths.
    """
    index = {}
    root = task_base.normalize_path(root)
    if not root or not os.path.isdir(root):
        return index
    for current_root, _, file_names in os.walk(root):
        for file_name in file_names:
            file_path = os.path.join(current_root, file_name)
            if not os.path.isfile(file_path):
                continue
            relative_path = to_relative(file_path, root)
            index.setdefault(strip_extension(relative_path), []).append(relative_path)
    for paths in index.values():
        paths.sort()
    return index


def build_leftover_ops(root, reference_paths, forward, settings):
    """Builds operations for files not referenced by the mapping.

    Forward, copy, and parallel-forward modes read source-like data and must
    never modify it, so unreferenced files can only be flagged (Setting 2).
    Revert modes operate on a working copy, so unreferenced files may be
    deleted or isolated (Setting 3).

    Args:
        root (str): Working directory root.
        reference_paths (set): Normalized relative paths accounted for by the mapping.
        forward (bool): True for forward-direction modes, False for revert modes.
        settings (dict): Task settings.

    Returns:
        list: Planned operation dictionaries for leftover files.
    """
    if forward:
        resolution = settings.get("source_orphan_resolution")
        if resolution not in [ORPHAN_FLAG_WARNING, ORPHAN_FLAG_ERROR]:
            return []
    else:
        resolution = settings.get("target_unmapped_resolution")
        if resolution not in [UNMAPPED_DELETE, UNMAPPED_ISOLATE]:
            return []
    root = task_base.normalize_path(root)
    plan = []
    if not root or not os.path.isdir(root):
        return plan
    for current_root, _, file_names in os.walk(root):
        for file_name in file_names:
            file_path = os.path.join(current_root, file_name)
            if not os.path.isfile(file_path):
                continue
            relative_path = to_relative(file_path, root)
            normalized = normalize_relative(relative_path)
            if normalized in reference_paths:
                continue
            if is_inside_isolation_folder(normalized):
                continue
            plan.append(build_leftover_op(root, relative_path, resolution))
    return plan


def build_leftover_op(root, relative_path, resolution):
    """Builds a single leftover-file operation for the given resolution.

    Args:
        root (str): Working directory root.
        relative_path (str): Relative path of the leftover file.
        resolution (str): Resolution policy value.

    Returns:
        dict: Planned operation dictionary.
    """
    if resolution == ORPHAN_FLAG_WARNING:
        return build_op(
            ACTION_WARN,
            status="Leftover",
            reason=f"File not in snapshot (left unchanged): {relative_path}",
            src_relative=relative_path,
        )
    if resolution == ORPHAN_FLAG_ERROR:
        return build_op(
            ACTION_ERROR,
            status="Leftover",
            reason=f"File not in snapshot: {relative_path}",
            src_relative=relative_path,
        )
    if resolution == UNMAPPED_DELETE:
        return build_delete_op(root, relative_path, "Leftover")
    isolated_relative = f"{UNMAPPED_FOLDER_NAME}/{relative_path}"
    return build_op(
        ACTION_ISOLATE,
        status="Leftover",
        reason=f"Isolate unmapped file to {UNMAPPED_FOLDER_NAME}",
        src=os.path.join(root, os.path.normpath(relative_path)),
        dst=os.path.join(root, os.path.normpath(isolated_relative)),
        src_relative=relative_path,
        dst_relative=isolated_relative,
    )


def resolve_move_op(root, from_relative, to_relative, status, settings):
    """Resolves an in-directory move operation against the filesystem state.

    Args:
        root (str): Working directory root.
        from_relative (str): Source relative path.
        to_relative (str): Destination relative path.
        status (str): Mapping status.
        settings (dict): Task settings.

    Returns:
        dict: Planned operation dictionary.
    """
    src_abs = os.path.join(root, os.path.normpath(from_relative))
    dst_abs = os.path.join(root, os.path.normpath(to_relative))
    return resolve_transfer_op(
        src_abs=src_abs,
        dst_abs=dst_abs,
        from_relative=from_relative,
        to_relative=to_relative,
        status=status,
        settings=settings,
        action=ACTION_MOVE,
        display_root=root,
    )


def resolve_transfer_op(src_abs, dst_abs, from_relative, to_relative, status, settings, action, display_root):
    """Resolves a move or copy operation against the current filesystem state.

    Handles idempotency (Setting 1), collisions, and safe directory creation.

    Args:
        src_abs (str): Absolute source path.
        dst_abs (str): Absolute destination path.
        from_relative (str): Source relative path (for display).
        to_relative (str): Destination relative path (for display).
        status (str): Mapping status.
        settings (dict): Task settings.
        action (str): ACTION_MOVE or ACTION_COPY.
        display_root (str): Root used to recompute a collision-suffixed target.

    Returns:
        dict: Planned operation dictionary.
    """
    if not os.path.exists(src_abs):
        if os.path.exists(dst_abs):
            if settings.get("missing_source_resolution") == MISSING_SOURCE_FLAG_ERROR:
                return build_op(
                    ACTION_ERROR,
                    status=status,
                    reason=f"Source missing but target exists: {to_relative}",
                    src_relative=from_relative,
                    dst_relative=to_relative,
                )
            return build_op(
                ACTION_SKIP,
                status=status,
                reason=f"Already applied (source missing, target exists): {to_relative}",
                src_relative=from_relative,
                dst_relative=to_relative,
            )
        return build_op(
            ACTION_WARN,
            status=status,
            reason=f"Source file not found: {from_relative}",
            src_relative=from_relative,
            dst_relative=to_relative,
        )
    if os.path.exists(dst_abs):
        if os.path.normcase(src_abs) == os.path.normcase(dst_abs) or same_file(src_abs, dst_abs):
            return build_op(
                ACTION_SKIP,
                status=status,
                reason=f"Destination already matches source: {to_relative}",
                src_relative=from_relative,
                dst_relative=to_relative,
            )
        if settings.get("collision_resolution") == COLLISION_ERROR:
            return build_op(
                ACTION_ERROR,
                status=status,
                reason=f"Collision: destination already exists: {to_relative}",
                src=src_abs,
                dst=dst_abs,
                src_relative=from_relative,
                dst_relative=to_relative,
            )
        dst_abs = unique_destination(dst_abs)
        to_relative = to_relative_display(display_root, dst_abs)
    return build_op(
        action,
        status=status,
        reason=f"{status}: {from_relative} -> {to_relative}",
        src=src_abs,
        dst=dst_abs,
        src_relative=from_relative,
        dst_relative=to_relative,
    )


def build_delete_op(root, relative_path, status):
    """Builds a delete operation for a relative path.

    Args:
        root (str): Working directory root.
        relative_path (str): Relative path to delete.
        status (str): Mapping status.

    Returns:
        dict: Planned operation dictionary.
    """
    src_abs = os.path.join(root, os.path.normpath(relative_path))
    if not os.path.exists(src_abs):
        return build_op(
            ACTION_SKIP,
            status=status,
            reason=f"Already removed: {relative_path}",
            src_relative=relative_path,
        )
    return build_op(
        ACTION_DELETE,
        status=status,
        reason=f"Delete: {relative_path}",
        src=src_abs,
        src_relative=relative_path,
    )


def build_op(action, status="", reason="", src=None, dst=None, src_relative="", dst_relative=""):
    """Builds a plan operation dictionary.

    Args:
        action (str): Operation action key.
        status (str, optional): Mapping status.
        reason (str, optional): Human-readable reason.
        src (str, optional): Absolute source path.
        dst (str, optional): Absolute destination path.
        src_relative (str, optional): Relative source path.
        dst_relative (str, optional): Relative destination path.

    Returns:
        dict: Operation dictionary.
    """
    return {
        "action": action,
        "status": status,
        "reason": reason,
        "src": src,
        "dst": dst,
        "src_relative": src_relative,
        "dst_relative": dst_relative,
        "executed": False,
    }


# ------------------------------------------------------------------ execution


def execute_plan(plan, dry_run=False):
    """Executes an operation plan on the filesystem.

    Args:
        plan (list): Planned operation dictionaries.
        dry_run (bool, optional): When True, no filesystem changes are made.

    Returns:
        list: Operation dictionaries updated with execution state.
    """
    for operation in plan:
        action = operation.get("action")
        if action in [ACTION_MOVE, ACTION_ISOLATE]:
            if not dry_run:
                safe_move(operation.get("src"), operation.get("dst"))
            operation["executed"] = not dry_run
        elif action == ACTION_COPY:
            if not dry_run:
                safe_copy(operation.get("src"), operation.get("dst"))
            operation["executed"] = not dry_run
        elif action == ACTION_DELETE:
            if not dry_run and operation.get("src") and os.path.isfile(operation.get("src")):
                os.remove(operation.get("src"))
            operation["executed"] = not dry_run
        else:
            operation["executed"] = False
    return plan


def cleanup_empty_folders(root):
    """Removes empty folders left inside a root after operations.

    Isolation folders are preserved so isolated files remain reachable.

    Args:
        root (str): Working directory root.

    Returns:
        list: Removed directory paths.
    """
    root = task_base.normalize_path(root)
    removed = []
    if not root or not os.path.isdir(root):
        return removed
    for current_root, _, _ in os.walk(root, topdown=False):
        if os.path.normcase(current_root) == os.path.normcase(root):
            continue
        relative_root = to_relative(current_root, root)
        if is_inside_isolation_folder(normalize_relative(relative_root)):
            continue
        try:
            if not os.listdir(current_root):
                os.rmdir(current_root)
                removed.append(task_base.normalize_path(current_root))
        except OSError:
            pass
    return removed


def safe_move(src, dst):
    """Moves a file, creating the destination directory tree first.

    Args:
        src (str): Absolute source path.
        dst (str): Absolute destination path.
    """
    destination_dir = os.path.dirname(dst)
    if destination_dir and not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    shutil.move(src, dst)


def safe_copy(src, dst):
    """Copies a file, creating the destination directory tree first.

    Args:
        src (str): Absolute source path.
        dst (str): Absolute destination path.
    """
    destination_dir = os.path.dirname(dst)
    if destination_dir and not os.path.isdir(destination_dir):
        os.makedirs(destination_dir)
    shutil.copy2(src, dst)


def paths_overlap(first_path, second_path):
    """Checks whether two directory paths are equal or nested within each other.

    Args:
        first_path (str): First directory path.
        second_path (str): Second directory path.

    Returns:
        bool: True when either path contains or equals the other.
    """
    first_path = task_base.normalize_path(first_path)
    second_path = task_base.normalize_path(second_path)
    if not first_path or not second_path:
        return False
    try:
        common_path = os.path.commonpath([first_path, second_path])
    except ValueError:
        return False
    common_path = os.path.normcase(common_path)
    return common_path in [os.path.normcase(first_path), os.path.normcase(second_path)]


def unique_destination(dst_abs):
    """Gets a non-colliding destination path by appending a numeric suffix.

    Args:
        dst_abs (str): Desired absolute destination path.

    Returns:
        str: Absolute destination path that does not yet exist.
    """
    if not os.path.exists(dst_abs):
        return dst_abs
    base, extension = os.path.splitext(dst_abs)
    index = 1
    candidate = f"{base}_{index}{extension}"
    while os.path.exists(candidate):
        index += 1
        candidate = f"{base}_{index}{extension}"
    return candidate


def same_file(first_path, second_path):
    """Checks whether two paths point at the same file.

    Args:
        first_path (str): First path.
        second_path (str): Second path.

    Returns:
        bool: True when both paths resolve to the same file.
    """
    try:
        return os.path.samefile(first_path, second_path)
    except (OSError, ValueError):
        return False


def strip_extension(relative_path):
    """Strips the extension from a relative path.

    Args:
        relative_path (str): Relative path.

    Returns:
        str: Relative path without its extension, using forward slashes.
    """
    root, _ = os.path.splitext(relative_path)
    return root.replace("\\", "/")


def replace_extension(relative_path, new_extension):
    """Replaces the extension of a relative path.

    Args:
        relative_path (str): Relative path.
        new_extension (str): New extension including its leading dot.

    Returns:
        str: Relative path with the new extension, using forward slashes.
    """
    root, _ = os.path.splitext(relative_path)
    return f"{root}{new_extension or ''}".replace("\\", "/")


def normalize_relative(relative_path):
    """Normalizes a relative path for comparison.

    Args:
        relative_path (str): Relative path.

    Returns:
        str: Normalized case-folded relative path using forward slashes.
    """
    return os.path.normcase(str(relative_path or "").replace("\\", "/").strip("/"))


def to_relative_display(root, absolute_path):
    """Gets a forward-slash relative path for display.

    Args:
        root (str): Root directory.
        absolute_path (str): Absolute path.

    Returns:
        str: Relative path using forward slashes.
    """
    return os.path.relpath(absolute_path, root).replace("\\", "/")


def is_inside_isolation_folder(normalized_relative):
    """Checks whether a normalized relative path is inside an isolation folder.

    Args:
        normalized_relative (str): Normalized relative path.

    Returns:
        bool: True when the path lives in an orphan or unmapped folder.
    """
    for folder_name in ISOLATION_FOLDER_NAMES:
        marker = os.path.normcase(folder_name)
        if normalized_relative == marker or normalized_relative.startswith(marker + "/"):
            return True
    return False


# ------------------------------------------------------------------- reporting


def serialize_operation(operation):
    """Serializes an operation for reporting.

    Args:
        operation (dict): Operation dictionary.

    Returns:
        dict: Serializable operation summary.
    """
    return {
        "action": operation.get("action"),
        "status": operation.get("status"),
        "reason": operation.get("reason"),
        "source_relative_path": operation.get("src_relative"),
        "target_relative_path": operation.get("dst_relative"),
        "executed": bool(operation.get("executed")),
    }


def summarize_operations(operations):
    """Summarizes operations by action.

    Args:
        operations (list): Operation dictionaries.

    Returns:
        dict: Counts keyed by action, plus a total.
    """
    summary = {"total": len(operations)}
    for operation in operations:
        action = operation.get("action") or "unknown"
        summary[action] = summary.get(action, 0) + 1
    return summary


def describe_plan(plan):
    """Builds human-readable lines describing a plan.

    Args:
        plan (list): Operation dictionaries.

    Returns:
        list: Text lines.
    """
    if not plan:
        return ["No operations are required for the current snapshot and directory."]
    action_labels = {
        ACTION_MOVE: "MOVE",
        ACTION_COPY: "COPY",
        ACTION_DELETE: "DELETE",
        ACTION_ISOLATE: "ISOLATE",
        ACTION_SKIP: "SKIP",
        ACTION_WARN: "WARN",
        ACTION_ERROR: "ERROR",
    }
    lines = []
    for operation in plan:
        label = action_labels.get(operation.get("action"), operation.get("action", "?").upper())
        source = operation.get("src_relative") or ""
        target = operation.get("dst_relative") or ""
        if source and target:
            lines.append(f"[{label}] {source} -> {target}")
        elif source:
            lines.append(f"[{label}] {source}")
        elif target:
            lines.append(f"[{label}] {target}")
        else:
            lines.append(f"[{label}] {operation.get('reason', '')}")
    return lines


def describe_mapping(mapping):
    """Builds human-readable lines describing a mapping array.

    Args:
        mapping (list): Mapping entries.

    Returns:
        list: Text lines.
    """
    if not mapping:
        return ["The snapshot does not contain a mapping yet."]
    lines = []
    for entry in mapping:
        status = entry.get("status", "")
        original = entry.get("original_relative_path") or ""
        target = entry.get("target_relative_path") or ""
        entry_type = entry.get("type", ENTRY_FILE)
        prefix = "DIR " if entry_type == ENTRY_FOLDER else ""
        if original and target:
            lines.append(f"[{status}] {prefix}{original} -> {target}")
        elif original:
            lines.append(f"[{status}] {prefix}{original}")
        else:
            lines.append(f"[{status}] {prefix}{target}")
    return lines
