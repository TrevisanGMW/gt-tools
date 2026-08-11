"""Batch Processor Unreal Engine script task."""

import glob
import os
import sys

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor.tasks.task_external_script import (
    TaskExternalScript,
    parse_command_arguments,
)
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_INLINE
import gt.ui.resource_library as ui_res_lib


DEFAULT_UNREAL_ARGUMENTS = (
    "-NoUI -UpdateReg -Unattended -stdout -FullStdOutLogOutput "
    "-RenderOffScreen -AllowCommandletRendering -AllowSoftwareRendering"
)
SAMPLE_SCRIPTS_DIRECTORY = "external_unreal"


class TaskUnrealScript(TaskExternalScript):
    """Task for running Python scripts in Unreal Engine headlessly."""

    task_type = constants.TaskType.UNREAL_SCRIPT
    default_display_name = "Unreal Engine"
    application_name = "Unreal Engine"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_unreal"
    icon = ui_res_lib.Icon.app_unreal
    category = "External"
    category_icon = ui_res_lib.Icon.batch_category_external
    metadata_scripts_key = "unreal_scripts"
    temporary_file_prefix = "unreal"
    process_log_name = "unreal"
    sample_scripts_directory = SAMPLE_SCRIPTS_DIRECTORY

    def get_default_settings(self):
        """Gets default Unreal Engine script task settings.

        Returns:
            dict: Default settings for the Unreal Engine task.
        """
        settings = super().get_default_settings()
        settings.update(
            {
                "source_path": "{previous-task-path}",
                "target_path": self.default_target_path_template,
                "script_mode": SCRIPT_MODE_INLINE,
                "script_text": "",
                "script_path": "{project-dir}/scripts/unreal_process.py",
                "scripts_path": "{project-dir}/scripts/unreal",
                "unreal_project_path": "",
                "unreal_executable": "",
                "unreal_arguments": DEFAULT_UNREAL_ARGUMENTS,
            }
        )
        return settings

    def build_external_command(
        self,
        executable_path,
        script_path,
        work_item,
        output_path,
        project,
        context_path,
    ):
        """Builds the Unreal Engine process command.

        Args:
            executable_path (str): Unreal Engine executable path.
            script_path (str): Python script path.
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            project (BatchProcessorModel): Active batch project model.
            context_path (str): JSON context path.

        Returns:
            list: Unreal Engine and batch command arguments.
        """
        project_path = self.settings.get("unreal_project_path") or ""
        if project:
            project_path = project.resolve_template_path(project_path, task=self)
        else:
            project_path = task_base.normalize_path(project_path)

        command = [
            executable_path,
            project_path,
            "-run=pythonscript",
            f"-script={script_path}",
        ]
        command.extend(
            parse_command_arguments(self.settings.get("unreal_arguments"))
        )
        command.append("--")

        if self.settings.get(
            "pass_standard_arguments",
            self.settings.get("pass_context_arguments", True),
        ):
            command.extend(
                [
                    "--input",
                    work_item.current_path,
                    "--output",
                    output_path,
                    "--project",
                    getattr(project, "project_file_path", "") or "",
                    "--project-dir",
                    project.get_project_dir() if project else "",
                    "--task",
                    self.display_name,
                    "--task-id",
                    self.id,
                    "--context",
                    context_path,
                ]
            )

        if self.settings.get("pass_environment_arguments", True):
            for key, value in self.get_environment_argument_pairs(project=project):
                command.extend([f"--env-{key}", str(value)])
                command.extend(["--env-var", f"{key}={value}"])

        return command

    def resolve_executable(self, project=None):
        """Resolves the configured Unreal Engine executable path.

        Args:
            project (BatchProcessorModel, optional): Active batch project model.

        Returns:
            str: Resolved Unreal Engine executable path.
        """
        value = self.settings.get("unreal_executable") or ""
        if project:
            return project.resolve_template_path(value, task=self)
        return task_base.normalize_path(value)


def find_unreal_executable(version=None):
    """Finds an Unreal Editor command executable in common install locations.

    Args:
        version (str, optional): Preferred Unreal Engine version.

    Returns:
        str: Unreal Editor command executable path, or an empty string.
    """
    for candidate in get_unreal_executable_candidates(version=version):
        if os.path.isfile(candidate):
            return task_base.normalize_path(candidate)
    return ""


def get_unreal_executable_candidates(version=None):
    """Gets likely Unreal Engine executable paths.

    UnrealEditor-Cmd.exe candidates are returned before UnrealEditor.exe
    candidates so headless execution keeps stdout routing enabled.

    Args:
        version (str, optional): Preferred Unreal Engine version.

    Returns:
        list: Candidate Unreal Engine executable paths.
    """
    if sys.platform != "win32":
        return []

    roots = []
    for environment_key, default_root in (
        ("PROGRAMFILES", r"C:\Program Files"),
        ("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
    ):
        root = os.environ.get(environment_key) or default_root
        if root and root not in roots:
            roots.append(root)

    version_text = str(version or "").strip()
    version_folder = version_text
    if version_folder and not version_folder.upper().startswith("UE_"):
        version_folder = f"UE_{version_folder}"

    command_candidates = []
    editor_candidates = []
    for root in roots:
        install_root = os.path.join(root, "Epic Games")
        if version_folder:
            version_root = os.path.join(install_root, version_folder)
            command_candidates.append(
                os.path.join(
                    version_root,
                    "Engine",
                    "Binaries",
                    "Win64",
                    "UnrealEditor-Cmd.exe",
                )
            )
            editor_candidates.append(
                os.path.join(
                    version_root,
                    "Engine",
                    "Binaries",
                    "Win64",
                    "UnrealEditor.exe",
                )
            )

        command_candidates.extend(
            glob.glob(
                os.path.join(
                    install_root,
                    "UE_*",
                    "Engine",
                    "Binaries",
                    "Win64",
                    "UnrealEditor-Cmd.exe",
                )
            )
        )
        editor_candidates.extend(
            glob.glob(
                os.path.join(
                    install_root,
                    "UE_*",
                    "Engine",
                    "Binaries",
                    "Win64",
                    "UnrealEditor.exe",
                )
            )
        )

    candidates = command_candidates + editor_candidates
    return list(
        dict.fromkeys(
            task_base.normalize_path(path) for path in candidates if path
        )
    )
