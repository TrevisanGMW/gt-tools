"""
Batch Processor Tasks

Registry and factory functions for all available batch processor tasks.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor.batch_processor_task_base import BatchTask
from gt.tools.batch_processor.batch_processor_task_base import OUTPUT_MODE_MODIFY
from gt.tools.batch_processor.batch_processor_task_base import OUTPUT_MODE_PASSTHROUGH
from gt.tools.batch_processor.batch_processor_task_base import OUTPUT_MODE_TARGET
from gt.tools.batch_processor.batch_processor_task_base import SOURCE_MODE_INCOMING
from gt.tools.batch_processor.batch_processor_task_base import SOURCE_MODE_PATH
from gt.tools.batch_processor.batch_processor_task_base import TaskSkip
from gt.tools.batch_processor.batch_processor_task_base import ValidationResult
from gt.tools.batch_processor.batch_processor_task_base import WorkItem
from gt.tools.batch_processor.batch_processor_task_base import build_run_id
from gt.tools.batch_processor.batch_processor_task_base import build_source_relative_metadata
from gt.tools.batch_processor.batch_processor_task_base import build_step_folder_name
from gt.tools.batch_processor.batch_processor_task_base import build_work_item_output_path
from gt.tools.batch_processor.batch_processor_task_base import get_output_dir_for_work_item
from gt.tools.batch_processor.batch_processor_task_base import get_work_item_relative_dir
from gt.tools.batch_processor.batch_processor_task_base import get_work_item_relative_path
from gt.tools.batch_processor.batch_processor_task_base import hash_settings
from gt.tools.batch_processor.batch_processor_task_base import has_supported_extension
from gt.tools.batch_processor.batch_processor_task_base import list_files_from_path
from gt.tools.batch_processor.batch_processor_task_base import normalize_extensions
from gt.tools.batch_processor.batch_processor_task_base import normalize_path
from gt.tools.batch_processor.batch_processor_task_base import path_is_inside_directory
from gt.tools.batch_processor.batch_processor_task_base import sanitize_filename
from gt.tools.batch_processor.tasks.task_input import TaskInput
from gt.tools.batch_processor.tasks.task_annotation import TaskAnnotationSnapshot
from gt.tools.batch_processor.tasks.task_archive import TaskArchive
from gt.tools.batch_processor.tasks.task_auto_rig_build import TaskAutoRigBuild
from gt.tools.batch_processor.tasks.task_batch_render import TaskBatchRender
from gt.tools.batch_processor.tasks.task_external_blender import TaskBlenderScript
from gt.tools.batch_processor.tasks.task_external_blender import find_blender_executable
from gt.tools.batch_processor.tasks.task_external_blender import get_blender_executable_candidates
from gt.tools.batch_processor.tasks.task_external_unreal import TaskUnrealScript
from gt.tools.batch_processor.tasks.task_external_unreal import find_unreal_executable
from gt.tools.batch_processor.tasks.task_external_unreal import get_unreal_executable_candidates
from gt.tools.batch_processor.tasks.task_capture import TaskCapturePlayblast
from gt.tools.batch_processor.tasks.task_capture import TaskCaptureThumbnail
from gt.tools.batch_processor.tasks.task_clip import TaskClipSnapshot
from gt.tools.batch_processor.tasks.task_clip import TaskClipSplit
from gt.tools.batch_processor.tasks.task_delete_path import TaskDeleteProjectFiles
from gt.tools.batch_processor.tasks.task_export_fbx import TaskExportFbx
from gt.tools.batch_processor.tasks.task_hik_retarget import HIK_BAKE_TARGET_NONE
from gt.tools.batch_processor.tasks.task_hik_retarget import TaskRetargetHumanIK
from gt.tools.batch_processor.tasks.task_hik_retarget import HIK_BAKE_TARGETS
from gt.tools.batch_processor.tasks.task_map_hierarchy import TaskMapHierarchy
from gt.tools.batch_processor.tasks.task_maya_import import TaskMayaImport
from gt.tools.batch_processor.tasks.task_maya_save import TaskMayaSave
from gt.tools.batch_processor.tasks.task_external_mobu import TaskMotionBuilderScript
from gt.tools.batch_processor.tasks.task_external_mobu import find_motionbuilder_executable
from gt.tools.batch_processor.tasks.task_external_mobu import get_motionbuilder_executable_candidates
from gt.tools.batch_processor.tasks.task_python_script import TaskPythonScript
from gt.tools.batch_processor.tasks.task_python_script import TaskPythonScriptsFolder
from gt.tools.batch_processor.tasks.task_rename import TaskRename
from gt.tools.batch_processor.tasks.task_report import TaskSceneReport
from gt.tools.batch_processor.tasks.task_retarget import TaskRetarget
from gt.tools.batch_processor.tasks.task_export_usd import TaskExportUsd
from gt.tools.batch_processor.tasks.task_validation import TaskValidationFileIntegrity
from gt.tools.batch_processor.tasks.task_validation import TaskValidationFolderCompare
from gt.tools.batch_processor.tasks.task_validation import TaskValidationMayaScene


TASK_TYPES = {
    constants.TaskType.INPUT: TaskInput,
    constants.TaskType.MAYA_IMPORT: TaskMayaImport,
    constants.TaskType.PYTHON_SCRIPT: TaskPythonScript,
    constants.TaskType.RENAME: TaskRename,
    constants.TaskType.MAP_HIERARCHY: TaskMapHierarchy,
    constants.TaskType.SCENE_REPORT: TaskSceneReport,
    constants.TaskType.MOTIONBUILDER_SCRIPT: TaskMotionBuilderScript,
    constants.TaskType.BLENDER_SCRIPT: TaskBlenderScript,
    constants.TaskType.UNREAL_SCRIPT: TaskUnrealScript,
    constants.TaskType.MAYA_SAVE: TaskMayaSave,
    constants.TaskType.USD_EXPORT: TaskExportUsd,
    constants.TaskType.FBX_EXPORT: TaskExportFbx,
    constants.TaskType.RETARGET: TaskRetarget,
    constants.TaskType.HIK_RETARGET: TaskRetargetHumanIK,
    constants.TaskType.AUTO_RIG_BUILD: TaskAutoRigBuild,
    constants.TaskType.CLIP_SPLIT: TaskClipSplit,
    constants.TaskType.CLIP_SNAPSHOT: TaskClipSnapshot,
    constants.TaskType.ANNOTATION_SNAPSHOT: TaskAnnotationSnapshot,
    constants.TaskType.DELETE_PROJECT_FILES: TaskDeleteProjectFiles,
    constants.TaskType.ZIP_COMPRESS: TaskArchive,
    constants.TaskType.MAYA_SCENE_VALIDATE: TaskValidationMayaScene,
    constants.TaskType.FILE_INTEGRITY_VALIDATE: TaskValidationFileIntegrity,
    constants.TaskType.FOLDER_COMPARE_VALIDATE: TaskValidationFolderCompare,
    constants.TaskType.THUMBNAIL_CAPTURE: TaskCaptureThumbnail,
    constants.TaskType.PLAYBLAST_CAPTURE: TaskCapturePlayblast,
    constants.TaskType.BATCH_RENDER: TaskBatchRender,
}

LEGACY_TASK_TYPES = {
    "maya_import": constants.TaskType.MAYA_IMPORT,
    "maya_save": constants.TaskType.MAYA_SAVE,
    "usd_export": constants.TaskType.USD_EXPORT,
    "python_scripts": constants.TaskType.PYTHON_SCRIPT,
    constants.TaskType.PYTHON_SCRIPTS_FOLDER: constants.TaskType.PYTHON_SCRIPT,
}

LEGACY_BATCH_PYTHON_TASK_TYPES = set(["python_scripts", constants.TaskType.PYTHON_SCRIPTS_FOLDER])
LEGACY_PYTHON_DISPLAY_NAMES = set(["Run Python Script", "Run Python Scripts Folder"])


def get_serialized_task_parameters(data):
    """Gets task parameters from current or legacy serialized data.

    Args:
        data (dict): Serialized task data.

    Returns:
        dict: Task parameter data.
    """
    data = data or {}
    if "parameters" in data:
        return dict(data.get("parameters") or {})
    return dict(data.get("settings") or {})


def create_task(task_type, **kwargs):
    """Creates a task from a task type key.

    Args:
        task_type (str): Task type key.
        **kwargs: Keyword arguments forwarded to the task constructor.

    Returns:
        BatchTask: New task instance.
    """
    original_task_type = task_type
    task_type = LEGACY_TASK_TYPES.get(task_type, task_type)
    if "parameters" in kwargs and "settings" not in kwargs:
        kwargs["settings"] = kwargs.pop("parameters")
    if original_task_type in LEGACY_BATCH_PYTHON_TASK_TYPES:
        settings = dict(kwargs.get("settings") or {})
        settings.setdefault("script_mode", "Batch Directory")
        kwargs["settings"] = settings
    task_class = TASK_TYPES.get(task_type)
    if not task_class:
        raise ValueError("Unknown task type: {0}".format(task_type))
    return task_class(**kwargs)


def create_task_from_dict(data):
    """Creates a task from serialized task data.

    Args:
        data (dict): Serialized task data.

    Returns:
        BatchTask: Deserialized task instance.
    """
    data = dict(data or {})
    original_task_type = data.get("task_type") or data.get("module_type")
    task_type = LEGACY_TASK_TYPES.get(original_task_type, original_task_type)
    if original_task_type in LEGACY_BATCH_PYTHON_TASK_TYPES:
        settings = get_serialized_task_parameters(data)
        settings.setdefault("script_mode", "Batch Directory")
        data["parameters"] = settings
        data["task_type"] = task_type
    if task_type == constants.TaskType.PYTHON_SCRIPT and data.get("display_name") in LEGACY_PYTHON_DISPLAY_NAMES:
        data["display_name"] = None
    task_class = TASK_TYPES.get(task_type, BatchTask)
    task = task_class.from_dict(data)
    if task_class is BatchTask and task_type:
        task.task_type = task_type
    return task


def get_task_class(task_type):
    """Gets the task class for a task type.

    Args:
        task_type (str): Task type key.

    Returns:
        type or None: Task class when registered.
    """
    task_type = LEGACY_TASK_TYPES.get(task_type, task_type)
    return TASK_TYPES.get(task_type)


def get_task_categories():
    """Gets registered tasks organized by category.

    Returns:
        dict: Mapping of category names to registered task classes.
    """
    categories = {}
    for task_class in TASK_TYPES.values():
        categories.setdefault(task_class.category, []).append(task_class)
    return categories


def get_task_category_icons():
    """Gets category icon names for registered task categories.

    Returns:
        dict: Mapping of category name to resource library icon attribute names.
    """
    category_icons = {}
    for task_class in TASK_TYPES.values():
        category_icons.setdefault(task_class.category, task_class.category_icon)
    return category_icons
