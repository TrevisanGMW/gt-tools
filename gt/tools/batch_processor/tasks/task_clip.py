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
        self.save_snapshot(snapshot_path=snapshot_path, work_items=work_items)
        return list(work_items)

    def save_snapshot(self, snapshot_path, work_items):
        """Saves clip data from incoming Maya scenes.

        Args:
            snapshot_path (str): Destination JSON path.
            work_items (list): Incoming work items.
        """
        snapshot_dir = os.path.dirname(snapshot_path)
        source_root = os.path.commonpath([item.current_path for item in work_items]) if work_items else ""
        if source_root and os.path.isfile(source_root):
            source_root = os.path.dirname(source_root)
        snapshot_data = {}
        for item in work_items:
            batch_processor_maya.open_scene(item.current_path, load_relevant_plugins=True)
            clip_data = get_scene_clip_data()
            if not clip_data:
                continue
            if source_root:
                rel_path = os.path.relpath(item.current_path, source_root)
            else:
                rel_path = os.path.basename(item.current_path)
            snapshot_data[rel_path.replace("\\", "/")] = clip_data
        task_utils.write_json_log(
            snapshot_path,
            {
                "version": 1,
                "created_at": task_utils.get_timestamp(),
                "source_root": source_root,
                "clips": snapshot_data,
            },
        )
        if snapshot_dir:
            task_utils.ensure_directory(snapshot_dir)

    def load_snapshot(self, snapshot_path, work_items):
        """Loads clip data into incoming Maya scenes.

        Args:
            snapshot_path (str): Source JSON path.
            work_items (list): Incoming work items.

        Returns:
            list: Original work items.
        """
        with open(snapshot_path, "r", encoding="utf-8") as snapshot_file:
            snapshot_payload = json.load(snapshot_file)
        clip_data_by_path = snapshot_payload.get("clips") or snapshot_payload
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
