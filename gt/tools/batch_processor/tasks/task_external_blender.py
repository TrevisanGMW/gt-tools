"""
Batch Processor Blender Script Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tasks.task_external_mobu import TaskMotionBuilderScript
from gt.tools.batch_processor.tasks.task_external_mobu import parse_command_arguments
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_INLINE
from gt.tools.batch_processor.tasks.task_python_script import TaskPythonScript
import glob
import os
import sys


DEFAULT_BLENDER_ARGUMENTS = "--background"
DEFAULT_BLENDER_SCRIPT_FLAG = "--python"
DEFAULT_BLENDER_INLINE_SCRIPT = r'''"""
Blender batch example.

Arguments passed by the batch processor when Pass Task Args is enabled:
    --input: Source file.
        Example: C:/project/01_input/character.fbx
    --output: Expected output file.
        Example: C:/project/02_tasks/01_blender/character.fbx
    --project: Batch project file.
        Example: C:/project/Batch_process_project.batch
    --project-dir: Folder containing the batch project.
        Example: C:/project
    --task: Task display name.
        Example: Blender
    --task-id: Stable task id from the .batch file.
        Example: 2f35ec56-8e64-4df7-9a30-612af8d4f2db
    --context: JSON file with the same batch context data.
        Example: C:/Users/name/AppData/Local/Temp/blender_context_ab12.json
    --env-var: Repeated project environment variable pair.
        Example: --env-var output-dir=03_output

The task also sets BATCH_INPUT, BATCH_OUTPUT, BATCH_PROJECT,
BATCH_PROJECT_DIR, BATCH_TASK, BATCH_TASK_ID, and BATCH_CONTEXT as process
environment variables.
"""

import argparse
import json
import os
import sys

import bpy


def parse_args():
    """Parses arguments after Blender's -- separator."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--project", default="")
    parser.add_argument("--project-dir", default="")
    parser.add_argument("--task", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--context", default="")
    parser.add_argument("--env-var", action="append", default=[])
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    args, _ = parser.parse_known_args(argv)
    return args


def load_context(context_path):
    """Loads the optional batch context JSON file."""
    if context_path and os.path.isfile(context_path):
        with open(context_path, "r", encoding="utf-8") as context_file:
            return json.load(context_file)
    return {}


def open_input_file(file_path):
    """Opens a Blend file or imports a supported interchange file."""
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".blend":
        bpy.ops.wm.open_mainfile(filepath=file_path)
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if extension == ".fbx":
        bpy.ops.import_scene.fbx(filepath=file_path)
    elif extension == ".obj":
        bpy.ops.wm.obj_import(filepath=file_path)
    elif extension in [".gltf", ".glb"]:
        bpy.ops.import_scene.gltf(filepath=file_path)
    else:
        raise RuntimeError("Unsupported Blender input extension: {0}".format(extension))


def export_fbx(file_path):
    """Exports the current Blender scene as FBX."""
    output_path = os.path.splitext(file_path)[0] + ".fbx"
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    bpy.ops.export_scene.fbx(filepath=output_path)
    return output_path


def main():
    """Runs the Blender batch example."""
    args = parse_args()
    context_path = args.context or os.environ.get("BATCH_CONTEXT", "")
    context = load_context(context_path)
    input_path = args.input or os.environ.get("BATCH_INPUT") or context.get("current_path") or context.get("source_path")
    output_path = args.output or os.environ.get("BATCH_OUTPUT") or context.get("output_path")
    if not input_path or not output_path:
        raise RuntimeError("Input and output paths are required.")
    print("Input Path: {0}".format(input_path))
    print("Output Path: {0}".format(output_path))
    open_input_file(input_path)
    exported_path = export_fbx(output_path)
    print("Exported FBX: {0}".format(exported_path))


main()
'''


class TaskBlenderScript(TaskMotionBuilderScript):
    """Task that runs Blender Python scripts as an external process."""

    task_type = constants.TaskType.BLENDER_SCRIPT
    default_display_name = "Blender"
    application_name = "Blender"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_blender"
    icon = ui_res_lib.Icon.app_blender
    category = "External"
    category_icon = ui_res_lib.Icon.root_miscellaneous
    metadata_scripts_key = "blender_scripts"
    temporary_file_prefix = "blender"

    def get_default_settings(self):
        """Gets default Blender script task settings.

        Returns:
            dict: Default settings.
        """
        settings = TaskPythonScript.get_default_settings(self)
        settings.update(
            {
                "source_path": "{previous-task-path}",
                "target_path": self.default_target_path_template,
                "script_mode": SCRIPT_MODE_INLINE,
                "script_text": DEFAULT_BLENDER_INLINE_SCRIPT,
                "script_path": "{project-dir}/scripts/blender_process.py",
                "scripts_path": "{project-dir}/scripts/blender",
                "blender_executable": "",
                "blender_arguments": DEFAULT_BLENDER_ARGUMENTS,
                "script_flag": DEFAULT_BLENDER_SCRIPT_FLAG,
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

    def validate(self, project):
        """Validates Blender script settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        executable_path = self.resolve_motionbuilder_executable(project)
        if not executable_path:
            result.add_error("Blender executable path cannot be empty.")
        elif not os.path.isfile(executable_path):
            result.add_error("Blender executable does not exist: {0}".format(executable_path))
        if self.is_batch_mode():
            result.extend(self.validate_batch_settings(project))
        elif self.is_external_file_mode():
            result.extend(self.validate_external_file_settings(project))
        else:
            result.extend(self.validate_single_script_settings(project))
        if not self.settings.get("wait_for_completion") and self.settings.get("require_output_file"):
            result.add_warning("Require Output is ignored when Wait For Completion is disabled.")
        return result

    def build_motionbuilder_command(self, executable_path, script_path, work_item, output_path, project, context_path):
        """Builds the Blender process command.

        Args:
            executable_path (str): Blender executable path.
            script_path (str): Python script path.
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            project (BatchProcessorModel): Active project model.
            context_path (str): JSON context path.

        Returns:
            list: Command arguments.
        """
        command = [executable_path]
        command.extend(parse_command_arguments(self.settings.get("blender_arguments")))
        script_flag = str(self.settings.get("script_flag") or "").strip()
        if script_flag:
            command.append(script_flag)
        command.append(script_path)
        command.append("--")
        if self.settings.get("pass_standard_arguments", self.settings.get("pass_context_arguments", True)):
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
                command.extend(["--env-{0}".format(key), str(value)])
                command.extend(["--env-var", "{0}={1}".format(key, value)])
        return command

    def build_process_log_path(self, output_path, step_output_dir, script_path, project=None):
        """Builds a process log path for Blender output.

        Args:
            output_path (str): Expected output path.
            step_output_dir (str): Task output folder.
            script_path (str): Script being executed.
            project (BatchProcessorModel, optional): Active project model.

        Returns:
            str: Process log path.
        """
        if not self.settings.get("write_process_log", True):
            return ""
        log_dir = project.get_logs_dir() if project and hasattr(project, "get_logs_dir") else ""
        target_dir = log_dir or step_output_dir
        output_base = os.path.splitext(os.path.basename(output_path))[0] or "blender"
        script_base = os.path.splitext(os.path.basename(script_path))[0] or "script"
        file_name = "{0}_{1}_blender.log".format(
            task_base.sanitize_filename(output_base, "item"),
            task_base.sanitize_filename(script_base, "script"),
        )
        return task_base.normalize_path(os.path.join(target_dir, file_name))

    def finalize_output(self, work_item, output_path):
        """Resolves Blender output without requiring a specific extension.

        Args:
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path used to derive the file stem.

        Returns:
            str: Matching output path, or the expected path when output checks are disabled.
        """
        matching_path = find_output_file_by_stem(output_path)
        if matching_path:
            return matching_path
        if self.settings.get("copy_input_if_output_missing"):
            return super().finalize_output(work_item=work_item, output_path=output_path)
        if self.settings.get("wait_for_completion", True) and self.settings.get("require_output_file", True):
            output_name = os.path.splitext(os.path.basename(output_path))[0]
            output_dir = os.path.dirname(output_path)
            raise RuntimeError(f"Blender script did not create an output named '{output_name}' in: {output_dir}")
        return output_path

    def resolve_motionbuilder_executable(self, project=None):
        """Resolves the configured Blender executable path.

        Args:
            project (BatchProcessorModel, optional): Active project model.

        Returns:
            str: Resolved executable path.
        """
        value = self.settings.get("blender_executable") or ""
        if project:
            return project.resolve_template_path(value, task=self)
        return task_base.normalize_path(value)


def find_blender_executable(version=None):
    """Finds a Blender executable in common install locations.

    Args:
        version (str, optional): Preferred Blender version.

    Returns:
        str: Blender executable path or an empty string.
    """
    candidates = get_blender_executable_candidates(version=version)
    for candidate in candidates:
        if os.path.isfile(candidate):
            return task_base.normalize_path(candidate)
    return ""


def find_output_file_by_stem(output_path):
    """Finds an output file with the expected name, ignoring its extension.

    Args:
        output_path (str): Expected output path.

    Returns:
        str: Matching file path, or an empty string when none exists.
    """
    if os.path.isfile(output_path):
        return task_base.normalize_path(output_path)
    output_dir = os.path.dirname(output_path)
    expected_stem = os.path.splitext(os.path.basename(output_path))[0].lower()
    if not output_dir or not expected_stem or not os.path.isdir(output_dir):
        return ""
    matching_paths = []
    for file_name in os.listdir(output_dir):
        candidate_path = os.path.join(output_dir, file_name)
        candidate_stem = os.path.splitext(file_name)[0].lower()
        if candidate_stem == expected_stem and os.path.isfile(candidate_path):
            matching_paths.append(candidate_path)
    if not matching_paths:
        return ""
    matching_paths.sort(key=lambda path: os.path.basename(path).lower())
    return task_base.normalize_path(matching_paths[0])


def get_blender_executable_candidates(version=None):
    """Gets likely Blender executable paths.

    Args:
        version (str, optional): Preferred Blender version.

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
        for root in roots:
            if not root:
                continue
            if version:
                candidates.append(os.path.join(root, "Blender Foundation", "Blender {0}".format(version), "blender.exe"))
            candidates.extend(glob.glob(os.path.join(root, "Blender Foundation", "Blender *", "blender.exe")))
            candidates.append(os.path.join(root, "Blender Foundation", "Blender", "blender.exe"))
    elif sys.platform == "darwin":
        if version:
            candidates.append("/Applications/Blender {0}.app/Contents/MacOS/Blender".format(version))
        candidates.extend(glob.glob("/Applications/Blender*.app/Contents/MacOS/Blender"))
    else:
        candidates.extend(["/usr/bin/blender", "/usr/local/bin/blender"])
        candidates.extend(glob.glob("/opt/blender*/blender"))
    return list(dict.fromkeys([task_base.normalize_path(path) for path in candidates if path]))
