"""
Batch Processor Constants
"""


class Project:
    """Constants used by batch project files."""

    EXTENSION = ".batch"
    VERSION = 1
    DEFAULT_NAME = "Untitled"
    DEFAULT_ENVIRONMENT_VARIABLES = {
        "project-dir": "{project-file-dir}",
        "project-file-dir": "",
        "project-path": "",
        "project-grandparent-dir": "",
        "input-dir": "01_input",
        "task-dir": "02_tasks",
        "output-dir": "03_output",
    }
    DEFAULT_RUN_SETTINGS = {
        "multi_instance": True,
        "worker_count": 30,
        "max_retries": 0,
        "timeout_minutes": 0,
        "preferred_maya_version": "",
        "create_log": True,
        "create_task_time_log": True,
        "log_path": "logs",
        "purge_logs_on_run": True,
        "ignore_disabled_tasks_for_task_index": False,
    }
    PREFS_FILENAME = "batch_processor"
    PREFS_KEY_CONVERT_ABS_PATHS_TO_RELATIVE = "convert_abs_paths_to_relative"
    PREFS_KEY_CONFIRM_DELETE_TASK = "confirm_delete_task"
    PREFS_KEY_FLAG_SKIPPED_TASKS = "flag_skipped_tasks"
    PREFS_KEY_IGNORE_DISABLED_TASKS_FOR_TASK_INDEX = "ignore_disabled_tasks_for_task_index"
    PREFS_KEY_AUTO_SEGMENT_IMPORTED_PROJECTS = "auto_segment_imported_projects"
    PREFS_KEY_RECENT_PROJECTS = "recent_projects"
    PREFS_KEY_SHOW_PACKAGE_TEMPLATES = "show_package_templates"
    MAX_RECENT_PROJECTS = 5


class TaskType:
    """Known process task type keys."""

    INPUT = "input"
    MAYA_IMPORT = "import_maya"
    RENAME = "rename"
    PYTHON_SCRIPT = "python_script"
    PYTHON_SCRIPTS_FOLDER = "python_scripts_folder"
    MOTIONBUILDER_SCRIPT = "motionbuilder_script"
    BLENDER_SCRIPT = "blender_script"
    UNREAL_SCRIPT = "unreal_script"
    MAYA_SAVE = "output_maya_save"
    USD_EXPORT = "output_usd_export"
    FBX_EXPORT = "output_fbx_export"
    RETARGET = "retarget"
    HIK_RETARGET = "retarget_hik"
    AUTO_RIG_BUILD = "auto_rig_build"
    CLIP_SPLIT = "clip_split"
    CLIP_SNAPSHOT = "clip_snapshot"
    MAP_HIERARCHY = "map_hierarchy"
    SCENE_REPORT = "scene_report"
    DELETE_PROJECT_FILES = "delete_project_files"
    ZIP_COMPRESS = "zip_compress"
    MAYA_SCENE_VALIDATE = "validate_maya_scene"
    FILE_INTEGRITY_VALIDATE = "validate_file_integrity"
    FOLDER_COMPARE_VALIDATE = "validate_folder_compare"
    THUMBNAIL_CAPTURE = "thumbnail_capture"
    PLAYBLAST_CAPTURE = "playblast_capture"
    BATCH_RENDER = "output_batch_render"


class ModuleType(TaskType):
    """Backward-compatible alias for old module type keys."""


class RunStatus:
    """Run status values used by trackers and manifests."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SKIPPED = "skipped"
    WARNING = "warning"
