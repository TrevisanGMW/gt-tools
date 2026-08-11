"""
Batch Processor MotionBuilder Script Task
"""


from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks.task_external_script import TaskExternalScript
from gt.tools.batch_processor.tasks.task_external_script import make_json_safe
from gt.tools.batch_processor.tasks.task_external_script import parse_command_arguments
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_INLINE
from gt.tools.batch_processor.tasks.task_python_script import TaskPythonScript
import glob
import os
import sys
import gt.ui.resource_library as ui_res_lib



DEFAULT_MOBU_ARGUMENTS = "-batch\n-verbosePython"
DEFAULT_MOBU_SCRIPT_FLAG = ""
LEGACY_MOBU_SCRIPT_FLAG = "-r"
DEFAULT_MOBU_INLINE_SCRIPT = task_utils.load_script("script_inline_external_mobu.py")


class TaskMotionBuilderScript(TaskExternalScript):
    """Task that runs MotionBuilder Python scripts as an external process."""

    task_type = constants.TaskType.MOTIONBUILDER_SCRIPT
    default_display_name = "MotionBuilder"
    application_name = "MotionBuilder"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_motionbuilder"
    icon = ui_res_lib.Icon.app_mobu
    category = "External"
    category_icon = ui_res_lib.Icon.batch_category_external
    metadata_scripts_key = "motionbuilder_scripts"
    temporary_file_prefix = "mobu"
    process_log_name = "motionbuilder"

    def __init__(self, *args, **kwargs):
        """Initializes the MotionBuilder task and migrates legacy launch defaults."""
        super().__init__(*args, **kwargs)
        if self.task_type == constants.TaskType.MOTIONBUILDER_SCRIPT:
            if str(self.settings.get("script_flag") or "").strip() == LEGACY_MOBU_SCRIPT_FLAG:
                self.settings["script_flag"] = DEFAULT_MOBU_SCRIPT_FLAG

    def get_default_settings(self):
        """Gets default MotionBuilder script task settings.

        Returns:
            dict: Default settings.
        """
        settings = super().get_default_settings()
        settings.update(
            {
                "source_path": "{previous-task-path}",
                "target_path": self.default_target_path_template,
                "script_mode": SCRIPT_MODE_INLINE,
                "script_text": DEFAULT_MOBU_INLINE_SCRIPT,
                "script_path": "{project-dir}/scripts/mobu_process.py",
                "scripts_path": "{project-dir}/scripts/mobu",
                "motionbuilder_executable": "",
                "motionbuilder_arguments": DEFAULT_MOBU_ARGUMENTS,
                "script_flag": DEFAULT_MOBU_SCRIPT_FLAG,
                "pass_standard_arguments": True,
                "pass_context_arguments": True,
                "pass_environment_arguments": True,
                "wait_for_completion": True,
                "timeout_seconds": 0,
                "require_output_file": True,
                "copy_input_if_output_missing": False,
                "write_process_log": True,
                "output_extension": ".fbx",
                "overwrite": False,
            }
        )
        return settings

    def build_external_command(self, executable_path, script_path, work_item, output_path, project, context_path):
        """Builds the MotionBuilder process command.

        Args:
            executable_path (str): MotionBuilder executable path.
            script_path (str): Python script path.
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            project (BatchProcessorModel): Active project model.
            context_path (str): JSON context path.

        Returns:
            list: Command arguments.
        """
        command = [executable_path]
        command.extend(parse_command_arguments(self.settings.get("motionbuilder_arguments")))
        script_flag = str(self.settings.get("script_flag") or "").strip()
        if script_flag and script_flag != LEGACY_MOBU_SCRIPT_FLAG:
            command.append(script_flag)
        command.append(script_path)
        return command

    def resolve_executable(self, project=None):
        """Resolves the configured MotionBuilder executable path.

        Args:
            project (BatchProcessorModel, optional): Active project model.

        Returns:
            str: Resolved executable path.
        """
        value = self.settings.get("motionbuilder_executable") or ""
        if project:
            return project.resolve_template_path(value, task=self)
        return task_base.normalize_path(value)


def find_motionbuilder_executable(version=None):
    """Finds a MotionBuilder executable in common install locations.

    Args:
        version (str, optional): Preferred MotionBuilder version.

    Returns:
        str: MotionBuilder executable path or an empty string.
    """
    candidates = get_motionbuilder_executable_candidates(version=version)
    for candidate in candidates:
        if os.path.isfile(candidate):
            return task_base.normalize_path(candidate)
    return ""


def get_motionbuilder_executable_candidates(version=None):
    """Gets likely MotionBuilder executable paths.

    Args:
        version (str, optional): Preferred MotionBuilder version.

    Returns:
        list: Candidate executable paths.
    """
    version = str(version or "").strip()
    candidates = []
    if sys.platform == "win32":
        roots = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        ]
        folder_names = []
        if version:
            folder_names.extend(["MotionBuilder {0}".format(version), "MotionBuilder{0}".format(version)])
        for root in roots:
            if not root:
                continue
            for folder_name in folder_names:
                candidates.append(os.path.join(root, "Autodesk", folder_name, "bin", "x64", "motionbuilder.exe"))
            candidates.extend(glob.glob(os.path.join(root, "Autodesk", "MotionBuilder *", "bin", "x64", "motionbuilder.exe")))
            candidates.extend(glob.glob(os.path.join(root, "Autodesk", "MotionBuilder*", "bin", "x64", "motionbuilder.exe")))
    else:
        if version:
            candidates.append("/usr/autodesk/motionbuilder{0}/bin/motionbuilder".format(version))
            candidates.append("/opt/Autodesk/MotionBuilder{0}/bin/motionbuilder".format(version))
        candidates.extend(glob.glob("/usr/autodesk/motionbuilder*/bin/motionbuilder"))
        candidates.extend(glob.glob("/opt/Autodesk/MotionBuilder*/bin/motionbuilder"))
    return list(dict.fromkeys([task_base.normalize_path(path) for path in candidates if path]))
