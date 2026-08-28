"""
Batch Processor Annotation Tasks

Stores and restores Annotation Tracker scene data across a sequence of files.
The scene node and attribute names mirror the ones written by the
``anim_annotation_tracker`` tool so snapshots stay compatible with it.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tasks import task_utils
import datetime
import json
import os
import tempfile
import time

try:
    import fcntl
except ImportError:
    fcntl = None

try:
    import msvcrt
except ImportError:
    msvcrt = None


ANNOTATION_NODE_NAME = "animAnnotationData"
ANNOTATION_ATTR_NAME = "annotationData"
ANNOTATION_ATTR_EDITED = "lastEdited"
ANNOTATION_FILE_DATA_KEY = "file_data"
ANNOTATION_RANGE_DATA_KEY = "range_data"
ANNOTATION_SEVERITY_WARNING = "Warning"
ANNOTATION_SEVERITY_ERROR = "Error"
ANNOTATION_SNAPSHOT_MODE_SAVE = "Save Snapshot"
ANNOTATION_SNAPSHOT_MODE_LOAD = "Load Snapshot"
ANNOTATION_SNAPSHOT_MODE_BYPASS = "Bypass Task"
ANNOTATION_SNAPSHOT_MODE_VALUES = [
    ANNOTATION_SNAPSHOT_MODE_SAVE,
    ANNOTATION_SNAPSHOT_MODE_LOAD,
    ANNOTATION_SNAPSHOT_MODE_BYPASS,
]
ANNOTATION_SNAPSHOT_VERSION = 1
ANNOTATION_SNAPSHOT_RESERVED_KEYS = ("version", "created_at", "source_root", "metadata", "annotations")
ANNOTATION_SNAPSHOT_LOCK_TIMEOUT_SECONDS = 60
ANNOTATION_SNAPSHOT_LOCK_POLL_SECONDS = 0.05

SNAPSHOT_STATUS_NO_FILE = "No File"
SNAPSHOT_STATUS_UNREADABLE = "Unreadable File"
SNAPSHOT_STATUS_READY = "Ready"
SNAPSHOT_COLOR_READY = "#5fb04f"
SNAPSHOT_COLOR_ERROR = "#c0554e"
SNAPSHOT_COLOR_NEUTRAL = "#888888"


class AnnotationSnapshotFileLock:
    """Cross-process file lock used to serialize Annotation Snapshot writes."""

    def __init__(self, snapshot_path, timeout_seconds=ANNOTATION_SNAPSHOT_LOCK_TIMEOUT_SECONDS):
        """Initializes the lock for a snapshot JSON path.

        Args:
            snapshot_path (str): Snapshot JSON path to protect.
            timeout_seconds (float, optional): Maximum time to wait for a writer.
        """
        self.lock_path = f"{snapshot_path}.lock"
        self.timeout_seconds = timeout_seconds
        self.lock_file = None
        self.is_locked = False

    def __enter__(self):
        """Acquires the lock before entering the protected block.

        Returns:
            AnnotationSnapshotFileLock: Acquired lock instance.
        """
        self.acquire()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        """Releases the lock after leaving the protected block.

        Args:
            exception_type (type): Exception type, when one was raised.
            exception_value (Exception): Exception instance, when one was raised.
            traceback (traceback): Exception traceback, when one was raised.
        """
        self.release()

    def acquire(self):
        """Waits until this process acquires the snapshot file lock.

        Raises:
            RuntimeError: If file locking is unavailable or the wait times out.
        """
        lock_directory = os.path.dirname(self.lock_path)
        if lock_directory:
            task_utils.ensure_directory(lock_directory)
        self.lock_file = open(self.lock_path, "a+")
        self.lock_file.seek(0, os.SEEK_END)
        if not self.lock_file.tell():
            self.lock_file.write("0")
            self.lock_file.flush()
        deadline = time.time() + self.timeout_seconds
        while True:
            try:
                self._try_lock()
                self.is_locked = True
                return
            except (IOError, OSError):
                if time.time() >= deadline:
                    self.lock_file.close()
                    self.lock_file = None
                    raise RuntimeError(
                        f"Timed out waiting for Annotation Snapshot write lock: {self.lock_path}"
                    )
                time.sleep(ANNOTATION_SNAPSHOT_LOCK_POLL_SECONDS)

    def release(self):
        """Releases and closes the snapshot file lock handle."""
        if not self.lock_file:
            return
        try:
            if self.is_locked:
                self._unlock()
        finally:
            self.lock_file.close()
            self.lock_file = None
            self.is_locked = False

    def _try_lock(self):
        """Attempts to acquire the platform-specific exclusive file lock.

        Raises:
            RuntimeError: If the platform has no supported file-lock API.
            IOError: If another process currently owns the lock.
        """
        self.lock_file.seek(0)
        if os.name == "nt":
            if not msvcrt:
                raise RuntimeError("Windows file locking is unavailable.")
            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            return
        if not fcntl:
            raise RuntimeError("POSIX file locking is unavailable.")
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(self):
        """Releases the platform-specific exclusive file lock."""
        self.lock_file.seek(0)
        if os.name == "nt":
            msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
            return
        fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)


class TaskAnnotationSnapshot(task_base.BatchTask):
    """Task that saves or restores annotation data across incoming Maya files."""

    task_type = constants.TaskType.ANNOTATION_SNAPSHOT
    default_display_name = "Annotation Snapshot"
    default_target_path_template = "{project-dir}/{output-dir}"
    icon = ui_res_lib.Icon.batch_task_annotation_snapshot
    category = "Animation"
    category_icon = ui_res_lib.Icon.root_animation
    is_aggregate_task = True
    is_data_load_task = True

    def get_default_settings(self):
        """Gets default annotation snapshot settings.

        Returns:
            dict: Default settings.
        """
        return {
            "include_in_task_index": False,
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "mode": ANNOTATION_SNAPSHOT_MODE_SAVE,
            "snapshot_path": "{project-dir}/data/annotation_snapshot_data.json",
            "missing_snapshot_severity": ANNOTATION_SEVERITY_ERROR,
            "overwrite": True,
        }

    def validate(self, project):
        """Validates annotation snapshot settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        mode = self.settings.get("mode")
        if mode not in ANNOTATION_SNAPSHOT_MODE_VALUES:
            result.add_error("Annotation snapshot mode must be Save Snapshot, Load Snapshot, or Bypass Task.")
        if mode == ANNOTATION_SNAPSHOT_MODE_BYPASS:
            return result
        snapshot_path = self.get_snapshot_path(project)
        if not snapshot_path:
            result.add_error("Annotation snapshot path is empty.")
        if mode == ANNOTATION_SNAPSHOT_MODE_LOAD and not os.path.isfile(snapshot_path):
            result.add_error("Annotation snapshot file does not exist: {0}".format(snapshot_path))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Saves or loads annotation data for all incoming work items.

        Args:
            work_item (WorkItem): Unused aggregate work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            context (dict, optional): Runtime context containing work_items.

        Returns:
            list: Original incoming work items.
        """
        context = context or {}
        work_items = context.get("work_items") or []
        if self.settings.get("mode") == ANNOTATION_SNAPSHOT_MODE_BYPASS:
            raise task_base.TaskSkip("Annotation Snapshot bypassed.", work_item=list(work_items))
        snapshot_path = self.get_snapshot_path(project)
        if self.settings.get("mode") == ANNOTATION_SNAPSHOT_MODE_LOAD:
            return self.load_snapshot(snapshot_path=snapshot_path, work_items=work_items)
        self.save_snapshot(snapshot_path=snapshot_path, work_items=work_items, project=project)
        return list(work_items)

    def save_snapshot(self, snapshot_path, work_items, project=None):
        """Saves annotation data from incoming Maya scenes.

        Args:
            snapshot_path (str): Destination JSON path.
            work_items (list): Incoming work items.
            project (BatchProcessorModel, optional): Active project.
        """
        source_root = self.get_snapshot_source_root(project=project, work_items=work_items)
        snapshot_data = {}
        for item in work_items:
            batch_processor_maya.open_scene(item.current_path, load_relevant_plugins=True)
            annotation_data = get_scene_annotation_data()
            if not has_annotation_data(annotation_data):
                continue
            entry_key = self.get_snapshot_entry_key(item=item, source_root=source_root)
            snapshot_data[entry_key] = annotation_data
        update_annotation_snapshot(
            snapshot_path=snapshot_path,
            source_root=source_root,
            annotation_data_by_path=snapshot_data,
        )

    def load_snapshot(self, snapshot_path, work_items):
        """Loads annotation data into incoming Maya scenes.

        Args:
            snapshot_path (str): Source JSON path.
            work_items (list): Incoming work items.

        Returns:
            list: Original work items.
        """
        snapshot_payload = load_annotation_snapshot_payload(snapshot_path)
        annotation_data_by_path = get_snapshot_annotation_data(snapshot_payload)
        for item in work_items:
            matching_key = find_snapshot_key(item.current_path, annotation_data_by_path)
            if not matching_key:
                if self.settings.get("missing_snapshot_severity") == ANNOTATION_SEVERITY_ERROR:
                    raise RuntimeError("No annotation snapshot entry found for: {0}".format(item.current_path))
                continue
            batch_processor_maya.open_scene(item.current_path, load_relevant_plugins=True)
            set_scene_annotation_data(annotation_data_by_path.get(matching_key) or {})
            batch_processor_maya.save_scene(
                item.current_path,
                batch_processor_maya.get_maya_file_type(item.current_path),
            )
        return list(work_items)

    def get_snapshot_path(self, project):
        """Gets the resolved snapshot path.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Snapshot path.
        """
        snapshot_path = self.settings.get("snapshot_path") or ""
        return project.resolve_template_path(snapshot_path, task=self) if snapshot_path else ""

    def get_snapshot_source_root(self, project, work_items):
        """Gets the stable source root used for snapshot file keys.

        The task source resolves identically in every tracker worker. Falling
        back to work-item metadata preserves stable relative keys for incoming
        items created by an earlier task.

        Args:
            project (BatchProcessorModel): Active project.
            work_items (list): Incoming work items.

        Returns:
            str: Source root path, or an empty string when unavailable.
        """
        source_root = self.resolve_source_path(project) if project else ""
        if source_root:
            return os.path.dirname(source_root) if os.path.isfile(source_root) else source_root
        source_roots = {
            item.metadata.get(task_base.METADATA_SOURCE_ROOT)
            for item in work_items
            if item.metadata.get(task_base.METADATA_SOURCE_ROOT)
        }
        if len(source_roots) == 1:
            return source_roots.pop()
        current_paths = [item.current_path for item in work_items if item.current_path]
        if not current_paths:
            return ""
        source_root = os.path.commonpath(current_paths)
        return os.path.dirname(source_root) if os.path.isfile(source_root) else source_root

    @staticmethod
    def get_snapshot_entry_key(item, source_root):
        """Gets a deterministic annotation snapshot entry key for a work item.

        Args:
            item (WorkItem): Work item being recorded.
            source_root (str): Resolved source root for the active task.

        Returns:
            str: Forward-slash relative key for the snapshot mapping.
        """
        current_path = task_base.normalize_path(item.current_path)
        source_root = task_base.normalize_path(source_root)
        if source_root and os.path.isfile(source_root):
            source_root = os.path.dirname(source_root)
        if current_path and source_root:
            try:
                common_root = os.path.commonpath([current_path, source_root])
            except ValueError:
                common_root = ""
            if os.path.normcase(common_root) == os.path.normcase(source_root):
                return task_base.get_path_relative_to_root(current_path, source_root)
        relative_path = task_base.get_work_item_relative_path(item)
        if relative_path:
            return relative_path
        return os.path.basename(current_path)

    def read_snapshot_metadata(self, project):
        """Reads summary metadata from the active annotation snapshot.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict or None: Snapshot metadata, or None when the file is unavailable.
        """
        snapshot_path = self.get_snapshot_path(project)
        if not snapshot_path or not os.path.isfile(snapshot_path):
            return None
        try:
            snapshot_payload = load_annotation_snapshot_payload(snapshot_path)
        except (ValueError, OSError):
            return None
        return build_annotation_snapshot_metadata(snapshot_payload)

    def get_snapshot_status(self, project):
        """Gets the active annotation snapshot readiness status for the UI.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict: Status text and display color.
        """
        snapshot_path = self.get_snapshot_path(project)
        if not snapshot_path or not os.path.isfile(snapshot_path):
            return {"text": SNAPSHOT_STATUS_NO_FILE, "color": SNAPSHOT_COLOR_NEUTRAL}
        try:
            load_annotation_snapshot_payload(snapshot_path)
        except (ValueError, OSError):
            return {"text": SNAPSHOT_STATUS_UNREADABLE, "color": SNAPSHOT_COLOR_ERROR}
        return {"text": SNAPSHOT_STATUS_READY, "color": SNAPSHOT_COLOR_READY}


def load_annotation_snapshot_payload(snapshot_path):
    """Loads and validates an Annotation Snapshot JSON payload.

    Args:
        snapshot_path (str): Snapshot JSON file path.

    Returns:
        dict: Parsed snapshot payload.

    Raises:
        ValueError: If the JSON payload is not a supported snapshot mapping.
        OSError: If the snapshot file cannot be read.
    """
    with open(snapshot_path, "r", encoding="utf-8") as snapshot_file:
        snapshot_payload = json.load(snapshot_file)
    if not isinstance(snapshot_payload, dict):
        raise ValueError("Annotation Snapshot data must be a JSON object.")
    if "annotations" in snapshot_payload and not isinstance(snapshot_payload.get("annotations"), dict):
        raise ValueError("Annotation Snapshot annotations data must be a JSON object.")
    return snapshot_payload


def get_snapshot_annotation_data(snapshot_payload):
    """Extracts the file-to-annotation mapping from a snapshot payload.

    A payload without the ``annotations`` key is treated as a hand-written flat
    mapping of file keys to annotation payloads.

    Args:
        snapshot_payload (dict): Parsed snapshot payload.

    Returns:
        dict: Mapping of snapshot file keys to annotation payloads.
    """
    if not isinstance(snapshot_payload, dict):
        return {}
    if "annotations" in snapshot_payload:
        annotation_data = snapshot_payload.get("annotations")
        return annotation_data if isinstance(annotation_data, dict) else {}
    return {
        entry_key: entry_data
        for entry_key, entry_data in snapshot_payload.items()
        if entry_key not in ANNOTATION_SNAPSHOT_RESERVED_KEYS and isinstance(entry_data, dict)
    }


def build_annotation_snapshot_metadata(snapshot_payload):
    """Builds summary metadata for an Annotation Snapshot payload.

    Args:
        snapshot_payload (dict): Parsed snapshot payload.

    Returns:
        dict: File and total frame-range counts for the snapshot.
    """
    annotation_data_by_path = get_snapshot_annotation_data(snapshot_payload)
    range_count = 0
    for annotation_data in annotation_data_by_path.values():
        range_count += len(get_annotation_ranges(annotation_data))
    return {
        "file_count": len(annotation_data_by_path),
        "range_count": range_count,
    }


def merge_annotation_snapshot_payload(snapshot_payload, source_root, annotation_data_by_path):
    """Merges a worker's annotation data into an existing snapshot payload.

    Args:
        snapshot_payload (dict): Existing snapshot payload.
        source_root (str): Source directory associated with this worker's data.
        annotation_data_by_path (dict): File-to-annotation mapping from one worker.

    Returns:
        dict: Updated snapshot payload.
    """
    existing_annotations = get_snapshot_annotation_data(snapshot_payload)
    merged_annotations = dict(existing_annotations)
    merged_annotations.update(annotation_data_by_path or {})
    if isinstance(snapshot_payload, dict) and "annotations" in snapshot_payload:
        merged_payload = dict(snapshot_payload)
    else:
        merged_payload = {}
    merged_payload["version"] = ANNOTATION_SNAPSHOT_VERSION
    merged_payload["created_at"] = task_utils.get_timestamp()
    if source_root and not merged_payload.get("source_root"):
        merged_payload["source_root"] = source_root
    merged_payload["annotations"] = merged_annotations
    merged_payload["metadata"] = build_annotation_snapshot_metadata(merged_payload)
    return merged_payload


def write_annotation_snapshot_payload(snapshot_path, snapshot_payload):
    """Atomically writes an Annotation Snapshot payload to disk.

    Args:
        snapshot_path (str): Destination JSON file path.
        snapshot_payload (dict): Serializable snapshot payload.

    Returns:
        str: Written snapshot path.
    """
    snapshot_directory = os.path.dirname(snapshot_path)
    if snapshot_directory:
        task_utils.ensure_directory(snapshot_directory)
    file_descriptor, temp_path = tempfile.mkstemp(
        prefix=f".{os.path.basename(snapshot_path)}.",
        suffix=".tmp",
        dir=snapshot_directory or None,
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as snapshot_file:
            json.dump(snapshot_payload, snapshot_file, indent=4, sort_keys=True)
            snapshot_file.flush()
            os.fsync(snapshot_file.fileno())
        os.replace(temp_path, snapshot_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return snapshot_path


def update_annotation_snapshot(snapshot_path, source_root, annotation_data_by_path):
    """Safely merges one worker's annotation data into a shared snapshot file.

    The sidecar lock remains on disk after use so workers never race while
    deleting and recreating the lock file. The lock itself is released when
    its file handle closes, including when a worker process exits unexpectedly.

    Args:
        snapshot_path (str): Destination JSON file path.
        source_root (str): Source directory associated with this worker's data.
        annotation_data_by_path (dict): File-to-annotation mapping from one worker.

    Returns:
        dict: Final merged snapshot payload.

    Raises:
        ValueError: If the snapshot path is empty.
    """
    if not snapshot_path:
        raise ValueError("Annotation Snapshot path is empty.")
    with AnnotationSnapshotFileLock(snapshot_path):
        snapshot_payload = {}
        if os.path.isfile(snapshot_path):
            snapshot_payload = load_annotation_snapshot_payload(snapshot_path)
        merged_payload = merge_annotation_snapshot_payload(
            snapshot_payload=snapshot_payload,
            source_root=source_root,
            annotation_data_by_path=annotation_data_by_path,
        )
        write_annotation_snapshot_payload(snapshot_path, merged_payload)
    return merged_payload


def normalize_annotation_data(annotation_data):
    """Normalizes an annotation payload to the Annotation Tracker layout.

    Args:
        annotation_data (dict): Raw annotation payload.

    Returns:
        dict: Payload with valid ``file_data`` and ``range_data`` values.
    """
    annotation_data = annotation_data if isinstance(annotation_data, dict) else {}
    file_data = annotation_data.get(ANNOTATION_FILE_DATA_KEY)
    range_data = annotation_data.get(ANNOTATION_RANGE_DATA_KEY)
    return {
        ANNOTATION_FILE_DATA_KEY: file_data if isinstance(file_data, dict) else {},
        ANNOTATION_RANGE_DATA_KEY: range_data if isinstance(range_data, list) else [],
    }


def get_annotation_ranges(annotation_data):
    """Gets the frame ranges stored in an annotation payload.

    Args:
        annotation_data (dict): Annotation payload.

    Returns:
        list: Frame-range dictionaries.
    """
    return normalize_annotation_data(annotation_data).get(ANNOTATION_RANGE_DATA_KEY)


def has_annotation_data(annotation_data):
    """Checks whether an annotation payload carries user data.

    Args:
        annotation_data (dict): Annotation payload.

    Returns:
        bool: True when file metadata or frame ranges exist.
    """
    normalized_data = normalize_annotation_data(annotation_data)
    return bool(
        normalized_data.get(ANNOTATION_FILE_DATA_KEY) or normalized_data.get(ANNOTATION_RANGE_DATA_KEY)
    )


def get_scene_annotation_data():
    """Gets Annotation Tracker data from the current Maya scene.

    Returns:
        dict: Annotation payload with ``file_data`` and ``range_data`` keys.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    attr_path = "{0}.{1}".format(ANNOTATION_NODE_NAME, ANNOTATION_ATTR_NAME)
    if not cmds.objExists(attr_path):
        return normalize_annotation_data({})
    data_string = cmds.getAttr(attr_path)
    if not data_string:
        return normalize_annotation_data({})
    return normalize_annotation_data(json.loads(data_string))


def set_scene_annotation_data(annotation_data):
    """Sets Annotation Tracker data on the current Maya scene.

    Args:
        annotation_data (dict): Annotation payload with file and range data.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    if not cmds.objExists(ANNOTATION_NODE_NAME):
        cmds.createNode("network", name=ANNOTATION_NODE_NAME)
    for attribute_name in [ANNOTATION_ATTR_NAME, ANNOTATION_ATTR_EDITED]:
        if not cmds.attributeQuery(attribute_name, node=ANNOTATION_NODE_NAME, exists=True):
            cmds.addAttr(ANNOTATION_NODE_NAME, longName=attribute_name, dataType="string")
    cmds.setAttr(
        "{0}.{1}".format(ANNOTATION_NODE_NAME, ANNOTATION_ATTR_NAME),
        json.dumps(normalize_annotation_data(annotation_data)),
        type="string",
    )
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmds.setAttr("{0}.{1}".format(ANNOTATION_NODE_NAME, ANNOTATION_ATTR_EDITED), timestamp, type="string")


def find_snapshot_key(file_path, snapshot_data):
    """Finds the snapshot entry that matches a file path.

    Args:
        file_path (str): Maya scene path.
        snapshot_data (dict): Snapshot mapping.

    Returns:
        str or None: Matching key.
    """
    normalized_path = file_path.replace("\\", "/")
    for key in snapshot_data.keys():
        if normalized_path.endswith(str(key).replace("\\", "/")):
            return key
    return None
