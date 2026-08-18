"""
Batch Processor Clip Tasks
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


CLIP_NODE_NAME = "animClipData"
CLIP_ATTR_NAME = "clipData"
CLIP_ATTR_EDITED = "clipDataLastEdited"
CLIP_SEVERITY_WARNING = "Warning"
CLIP_SEVERITY_ERROR = "Error"
CLIP_SNAPSHOT_MODE_SAVE = "Save Snapshot"
CLIP_SNAPSHOT_MODE_LOAD = "Load Snapshot"
CLIP_SNAPSHOT_MODE_BYPASS = "Bypass Task"
CLIP_SNAPSHOT_MODE_VALUES = [
    CLIP_SNAPSHOT_MODE_SAVE,
    CLIP_SNAPSHOT_MODE_LOAD,
    CLIP_SNAPSHOT_MODE_BYPASS,
]
CLIP_SNAPSHOT_VERSION = 1
CLIP_SNAPSHOT_LOCK_TIMEOUT_SECONDS = 60
CLIP_SNAPSHOT_LOCK_POLL_SECONDS = 0.05

SNAPSHOT_STATUS_NO_FILE = "No File"
SNAPSHOT_STATUS_UNREADABLE = "Unreadable File"
SNAPSHOT_STATUS_READY = "Ready"
SNAPSHOT_COLOR_READY = "#5fb04f"
SNAPSHOT_COLOR_ERROR = "#c0554e"
SNAPSHOT_COLOR_NEUTRAL = "#888888"


class ClipSnapshotFileLock:
    """Cross-process file lock used to serialize Clip Snapshot JSON writes."""

    def __init__(self, snapshot_path, timeout_seconds=CLIP_SNAPSHOT_LOCK_TIMEOUT_SECONDS):
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
            ClipSnapshotFileLock: Acquired lock instance.
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
                        f"Timed out waiting for Clip Snapshot write lock: {self.lock_path}"
                    )
                time.sleep(CLIP_SNAPSHOT_LOCK_POLL_SECONDS)

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


class TaskClipSplit(task_base.BatchTask):
    """Task that splits Maya scenes into files using stored clip data."""

    task_type = constants.TaskType.CLIP_SPLIT
    default_display_name = "Clip Split"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_clips"
    icon = ui_res_lib.Icon.batch_task_clip_split
    category = "Animation"
    category_icon = ui_res_lib.Icon.root_animation
    def __init__(self, *args, **kwargs):
        """Initializes the clip split task and normalizes old display names.

        Args:
            *args: Positional arguments passed to BatchTask.
            **kwargs: Keyword arguments passed to BatchTask.
        """
        super().__init__(*args, **kwargs)
        if self.display_name == "Split Clips":
            self.display_name = self.default_display_name

    def get_default_settings(self):
        """Gets default clip split settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "missing_clips_severity": CLIP_SEVERITY_WARNING,
            "force_current_range_if_no_clips": False,
            "include_inactive_clips": False,
            "append_clip_name": True,
            "append_frame_range": True,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates clip split settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        if self.settings.get("missing_clips_severity") not in [CLIP_SEVERITY_WARNING, CLIP_SEVERITY_ERROR]:
            result.add_error("Missing clips severity must be Warning or Error.")
        if self.modifies_in_place():
            result.add_error("Split Clips cannot modify source files in place. Use a target path.")
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Splits one Maya scene into clip files.

        Args:
            work_item (WorkItem): Source Maya scene.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            context (dict, optional): Runtime context.

        Returns:
            list: Output clip work items.
        """
        batch_processor_maya.open_scene(work_item.current_path, load_relevant_plugins=True)
        clips = get_scene_clip_data()
        if not self.settings.get("include_inactive_clips", False):
            clips = [clip for clip in clips if clip.get("active", False)]
        if not clips:
            if self.settings.get("force_current_range_if_no_clips"):
                clips = [get_current_range_clip()]
            elif self.settings.get("missing_clips_severity") == CLIP_SEVERITY_ERROR:
                raise RuntimeError("No clips found in scene: {0}".format(work_item.current_path))
            else:
                return []

        output_items = []
        for clip in clips:
            output_path = self.build_clip_output_path(work_item, step_output_dir, clip)
            metadata = task_utils.build_metadata(self, work_item)
            metadata["clip_name"] = clip.get("name", "")
            metadata["clip_start"] = int(float(clip.get("start", 0)))
            metadata["clip_end"] = int(float(clip.get("end", 0)))
            if os.path.exists(output_path) and not self.settings.get("overwrite", False):
                output_items.append(
                    task_base.WorkItem(
                        source_path=work_item.source_path,
                        current_path=output_path,
                        metadata=metadata,
                    )
                )
                continue
            set_timeline_from_clip(clip)
            batch_processor_maya.save_scene(output_path, batch_processor_maya.get_maya_file_type(output_path))
            output_items.append(
                task_base.WorkItem(
                    source_path=work_item.source_path,
                    current_path=output_path,
                    metadata=metadata,
                )
            )
        return output_items

    def build_clip_output_path(self, work_item, step_output_dir, clip):
        """Builds a clip output path.

        Args:
            work_item (WorkItem): Source work item.
            step_output_dir (str): Output directory.
            clip (dict): Clip data.

        Returns:
            str: Output path.
        """
        source_name, extension = os.path.splitext(os.path.basename(work_item.current_path))
        suffix_parts = []
        if self.settings.get("append_clip_name", True) and clip.get("name"):
            suffix_parts.append(task_base.sanitize_filename(clip.get("name"), "clip"))
        if self.settings.get("append_frame_range", True):
            start_frame = int(float(clip.get("start", 0)))
            end_frame = int(float(clip.get("end", 0)))
            suffix_parts.append("f{0:04d}-{1:04d}".format(start_frame, end_frame))
        suffix = ""
        if suffix_parts:
            suffix = "_" + "_".join(suffix_parts)
        file_name = "{0}{1}{2}".format(task_base.sanitize_filename(source_name, "scene"), suffix, extension)
        return task_base.build_work_item_output_path(
            work_item=work_item,
            output_dir=step_output_dir,
            file_name=file_name,
        )


class TaskClipSnapshot(task_base.BatchTask):
    """Task that saves or restores clip data across incoming Maya files."""

    task_type = constants.TaskType.CLIP_SNAPSHOT
    default_display_name = "Clip Snapshot"
    default_target_path_template = "{project-dir}/{output-dir}"
    icon = ui_res_lib.Icon.batch_task_clip_snapshot
    category = "Animation"
    category_icon = ui_res_lib.Icon.root_animation
    is_aggregate_task = True
    is_data_load_task = True

    def get_default_settings(self):
        """Gets default clip snapshot settings.

        Returns:
            dict: Default settings.
        """
        return {
            "include_in_task_index": False,
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "mode": CLIP_SNAPSHOT_MODE_SAVE,
            "snapshot_path": "{project-dir}/data/clip_snapshot_data.json",
            "missing_snapshot_severity": CLIP_SEVERITY_ERROR,
            "overwrite": True,
        }

    def validate(self, project):
        """Validates clip snapshot settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        mode = self.settings.get("mode")
        if mode not in CLIP_SNAPSHOT_MODE_VALUES:
            result.add_error("Clip snapshot mode must be Save Snapshot, Load Snapshot, or Bypass Task.")
        if mode == CLIP_SNAPSHOT_MODE_BYPASS:
            return result
        snapshot_path = self.get_snapshot_path(project)
        if not snapshot_path:
            result.add_error("Clip snapshot path is empty.")
        if mode == CLIP_SNAPSHOT_MODE_LOAD and not os.path.isfile(snapshot_path):
            result.add_error("Clip snapshot file does not exist: {0}".format(snapshot_path))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Saves or loads clip data for all incoming work items.

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
        if self.settings.get("mode") == CLIP_SNAPSHOT_MODE_BYPASS:
            raise task_base.TaskSkip("Clip Snapshot bypassed.", work_item=list(work_items))
        snapshot_path = self.get_snapshot_path(project)
        if self.settings.get("mode") == CLIP_SNAPSHOT_MODE_LOAD:
            return self.load_snapshot(snapshot_path=snapshot_path, work_items=work_items)
        self.save_snapshot(snapshot_path=snapshot_path, work_items=work_items, project=project)
        return list(work_items)

    def save_snapshot(self, snapshot_path, work_items, project=None):
        """Saves clip data from incoming Maya scenes.

        Args:
            snapshot_path (str): Destination JSON path.
            work_items (list): Incoming work items.
            project (BatchProcessorModel, optional): Active project.
        """
        source_root = self.get_snapshot_source_root(project=project, work_items=work_items)
        snapshot_data = {}
        for item in work_items:
            batch_processor_maya.open_scene(item.current_path, load_relevant_plugins=True)
            clip_data = get_scene_clip_data()
            if not clip_data:
                continue
            entry_key = self.get_snapshot_entry_key(item=item, source_root=source_root)
            snapshot_data[entry_key] = clip_data
        update_clip_snapshot(
            snapshot_path=snapshot_path,
            source_root=source_root,
            clip_data_by_path=snapshot_data,
        )

    def load_snapshot(self, snapshot_path, work_items):
        """Loads clip data into incoming Maya scenes.

        Args:
            snapshot_path (str): Source JSON path.
            work_items (list): Incoming work items.

        Returns:
            list: Original work items.
        """
        snapshot_payload = load_clip_snapshot_payload(snapshot_path)
        clip_data_by_path = get_snapshot_clip_data(snapshot_payload)
        for item in work_items:
            matching_key = find_snapshot_key(item.current_path, clip_data_by_path)
            if not matching_key:
                if self.settings.get("missing_snapshot_severity") == CLIP_SEVERITY_ERROR:
                    raise RuntimeError("No clip snapshot entry found for: {0}".format(item.current_path))
                continue
            batch_processor_maya.open_scene(item.current_path, load_relevant_plugins=True)
            set_scene_clip_data(clip_data_by_path.get(matching_key) or [])
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
        """Gets a deterministic clip snapshot entry key for a work item.

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
        """Reads summary metadata from the active clip snapshot.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict or None: Snapshot metadata, or None when the file is unavailable.
        """
        snapshot_path = self.get_snapshot_path(project)
        if not snapshot_path or not os.path.isfile(snapshot_path):
            return None
        try:
            snapshot_payload = load_clip_snapshot_payload(snapshot_path)
        except (ValueError, OSError):
            return None
        return build_clip_snapshot_metadata(snapshot_payload)

    def get_snapshot_status(self, project):
        """Gets the active clip snapshot readiness status for the UI.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            dict: Status text and display color.
        """
        snapshot_path = self.get_snapshot_path(project)
        if not snapshot_path or not os.path.isfile(snapshot_path):
            return {"text": SNAPSHOT_STATUS_NO_FILE, "color": SNAPSHOT_COLOR_NEUTRAL}
        try:
            load_clip_snapshot_payload(snapshot_path)
        except (ValueError, OSError):
            return {"text": SNAPSHOT_STATUS_UNREADABLE, "color": SNAPSHOT_COLOR_ERROR}
        return {"text": SNAPSHOT_STATUS_READY, "color": SNAPSHOT_COLOR_READY}


def load_clip_snapshot_payload(snapshot_path):
    """Loads and validates a Clip Snapshot JSON payload.

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
        raise ValueError("Clip Snapshot data must be a JSON object.")
    if "clips" in snapshot_payload and not isinstance(snapshot_payload.get("clips"), dict):
        raise ValueError("Clip Snapshot clips data must be a JSON object.")
    return snapshot_payload


def get_snapshot_clip_data(snapshot_payload):
    """Extracts the file-to-clip mapping from a current or legacy payload.

    Args:
        snapshot_payload (dict): Parsed snapshot payload.

    Returns:
        dict: Mapping of snapshot file keys to clip lists.
    """
    if not isinstance(snapshot_payload, dict):
        return {}
    clip_data = snapshot_payload.get("clips") if "clips" in snapshot_payload else snapshot_payload
    return clip_data if isinstance(clip_data, dict) else {}


def build_clip_snapshot_metadata(snapshot_payload):
    """Builds summary metadata for a Clip Snapshot payload.

    Args:
        snapshot_payload (dict): Parsed snapshot payload.

    Returns:
        dict: File and total-clip counts for the snapshot.
    """
    clip_data_by_path = get_snapshot_clip_data(snapshot_payload)
    clip_count = sum(
        len(clip_data)
        for clip_data in clip_data_by_path.values()
        if isinstance(clip_data, list)
    )
    return {
        "file_count": len(clip_data_by_path),
        "clip_count": clip_count,
    }


def merge_clip_snapshot_payload(snapshot_payload, source_root, clip_data_by_path):
    """Merges a worker's clip data into an existing snapshot payload.

    Args:
        snapshot_payload (dict): Existing current or legacy snapshot payload.
        source_root (str): Source directory associated with this worker's data.
        clip_data_by_path (dict): File-to-clip mapping collected by one worker.

    Returns:
        dict: Updated current-format snapshot payload.
    """
    existing_clips = get_snapshot_clip_data(snapshot_payload)
    merged_clips = dict(existing_clips)
    merged_clips.update(clip_data_by_path or {})
    if isinstance(snapshot_payload, dict) and "clips" in snapshot_payload:
        merged_payload = dict(snapshot_payload)
    else:
        merged_payload = {}
    merged_payload["version"] = CLIP_SNAPSHOT_VERSION
    merged_payload["created_at"] = task_utils.get_timestamp()
    if source_root and not merged_payload.get("source_root"):
        merged_payload["source_root"] = source_root
    merged_payload["clips"] = merged_clips
    merged_payload["metadata"] = build_clip_snapshot_metadata(merged_payload)
    return merged_payload


def write_clip_snapshot_payload(snapshot_path, snapshot_payload):
    """Atomically writes a Clip Snapshot payload to disk.

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


def update_clip_snapshot(snapshot_path, source_root, clip_data_by_path):
    """Safely merges one worker's clip data into a shared snapshot file.

    The sidecar lock remains on disk after use so workers never race while
    deleting and recreating the lock file. The lock itself is released when
    its file handle closes, including when a worker process exits unexpectedly.

    Args:
        snapshot_path (str): Destination JSON file path.
        source_root (str): Source directory associated with this worker's data.
        clip_data_by_path (dict): File-to-clip mapping collected by one worker.

    Returns:
        dict: Final merged snapshot payload.
    """
    if not snapshot_path:
        raise ValueError("Clip Snapshot path is empty.")
    with ClipSnapshotFileLock(snapshot_path):
        snapshot_payload = {}
        if os.path.isfile(snapshot_path):
            snapshot_payload = load_clip_snapshot_payload(snapshot_path)
        merged_payload = merge_clip_snapshot_payload(
            snapshot_payload=snapshot_payload,
            source_root=source_root,
            clip_data_by_path=clip_data_by_path,
        )
        write_clip_snapshot_payload(snapshot_path, merged_payload)
    return merged_payload


def get_scene_clip_data():
    """Gets clip data from the current Maya scene.

    Returns:
        list: Clip dictionaries.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    attr_path = "{0}.{1}".format(CLIP_NODE_NAME, CLIP_ATTR_NAME)
    if not cmds.objExists(attr_path):
        return []
    data_string = cmds.getAttr(attr_path)
    if not data_string:
        return []
    data = json.loads(data_string)
    return data if isinstance(data, list) else []


def set_scene_clip_data(clip_data):
    """Sets clip data on the current Maya scene.

    Args:
        clip_data (list): Clip dictionaries.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    if not cmds.objExists(CLIP_NODE_NAME):
        cmds.createNode("network", name=CLIP_NODE_NAME)
    if not cmds.attributeQuery(CLIP_ATTR_NAME, node=CLIP_NODE_NAME, exists=True):
        cmds.addAttr(CLIP_NODE_NAME, longName=CLIP_ATTR_NAME, dataType="string")
    if not cmds.attributeQuery(CLIP_ATTR_EDITED, node=CLIP_NODE_NAME, exists=True):
        cmds.addAttr(CLIP_NODE_NAME, longName=CLIP_ATTR_EDITED, dataType="string")
    cmds.setAttr("{0}.{1}".format(CLIP_NODE_NAME, CLIP_ATTR_NAME), json.dumps(clip_data), type="string")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmds.setAttr("{0}.{1}".format(CLIP_NODE_NAME, CLIP_ATTR_EDITED), timestamp, type="string")


def get_current_range_clip():
    """Gets a clip representing the current Maya playback range.

    Returns:
        dict: Clip data dictionary.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    start_frame = int(cmds.playbackOptions(query=True, minTime=True))
    end_frame = int(cmds.playbackOptions(query=True, maxTime=True))
    return {"name": "CurrentRange", "start": start_frame, "end": end_frame, "active": True}


def set_timeline_from_clip(clip):
    """Sets Maya playback range from a clip.

    Args:
        clip (dict): Clip data.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    start_frame = int(float(clip.get("start", 0)))
    end_frame = int(float(clip.get("end", 0)))
    cmds.playbackOptions(minTime=start_frame, maxTime=end_frame)
    cmds.playbackOptions(animationStartTime=start_frame, animationEndTime=end_frame)


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
