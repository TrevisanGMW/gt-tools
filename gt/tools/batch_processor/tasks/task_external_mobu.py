"""
Batch Processor MotionBuilder Script Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_BATCH_DIRECTORY
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_EXTERNAL_FILE
from gt.tools.batch_processor.tasks.task_python_script import SCRIPT_MODE_INLINE
from gt.tools.batch_processor.tasks.task_python_script import TaskPythonScript
import glob
import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile


DEFAULT_MOBU_ARGUMENTS = "-batch\n-verbosePython"
DEFAULT_MOBU_SCRIPT_FLAG = ""
LEGACY_MOBU_SCRIPT_FLAG = "-r"
DEFAULT_MOBU_INLINE_SCRIPT = r'''"""
MotionBuilder batch example.

Values exposed by the batch processor when Pass Task Args is enabled:
    BATCH_INPUT: Source FBX file or folder.
        Example: C:/project/01_input/walk.fbx
    BATCH_OUTPUT: Expected output FBX file or folder.
        Example: C:/project/02_tasks/01_motionbuilder/walk.fbx
    BATCH_PROJECT: Batch project file.
        Example: C:/project/Batch_process_project.batch
    BATCH_PROJECT_DIR: Folder containing the batch project.
        Example: C:/project
    BATCH_TASK: Task display name.
        Example: MotionBuilder
    BATCH_TASK_ID: Stable task id from the .batch file.
        Example: 2f35ec56-8e64-4df7-9a30-612af8d4f2db
    BATCH_CONTEXT: JSON file with the same batch context data.
        Example: C:/Users/name/AppData/Local/Temp/mobu_context_ab12.json

Project environment variables are exposed as BATCH_ENV_NAME values. For
manual testing, the script also accepts equivalent --input, --output,
--project, --project-dir, --task, --task-id, --context, and --env-var
command-line arguments.
"""

import argparse
import json
import os
import sys

from pyfbsdk import FBApplication, FBSystem, FBFbxOptions


def parse_args():
    """Parses batch arguments while tolerating MotionBuilder arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--project", default="")
    parser.add_argument("--project-dir", default="")
    parser.add_argument("--task", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--context", default="")
    parser.add_argument("--env-var", action="append", default=[])
    args, _ = parser.parse_known_args(sys.argv[1:])
    return args


def load_context(context_path):
    """Loads the optional batch context JSON file."""
    if context_path and os.path.isfile(context_path):
        with open(context_path, "r", encoding="utf-8") as context_file:
            return json.load(context_file)
    return {}


def build_file_pairs(input_path, output_path):
    """Builds input/output FBX file pairs."""
    if os.path.isdir(input_path):
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
        pairs = []
        for file_name in sorted(os.listdir(input_path)):
            if file_name.lower().endswith(".fbx"):
                pairs.append((os.path.join(input_path, file_name), os.path.join(output_path, file_name)))
        return pairs
    return [(input_path, output_path)]


def strip_geometry(input_path, output_path):
    """Opens an FBX, saves skeleton/character data only, and writes the result."""
    app = FBApplication()
    system = FBSystem()
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    app.FileNew()
    app.FileOpen(input_path, False)

    for component in system.Scene.Components:
        component.Selected = False

    safe_classes = [
        "FBModelSkeleton",
        "FBModelRoot",
        "FBModelNull",
        "FBCharacter",
        "FBControlRig",
        "FBCamera",
        "FBLight",
        "FBModelMarker",
        "FBConstraint",
    ]
    for component in system.Scene.Components:
        if component.ClassName() in safe_classes:
            component.Selected = True
            if hasattr(component, "Visibility"):
                component.Visibility = True

    save_options = FBFbxOptions(False)
    save_options.SaveSelectedModelsOnly = True
    save_options.SaveCharacter = True
    save_options.SaveControlRig = True
    app.FileSave(output_path, save_options)
    print("Headless safe export: {0}".format(output_path))


def main():
    """Runs the MotionBuilder batch example."""
    args = parse_args()
    context_path = args.context or os.environ.get("BATCH_CONTEXT", "")
    context = load_context(context_path)
    input_path = args.input or os.environ.get("BATCH_INPUT") or context.get("current_path") or context.get("source_path")
    output_path = args.output or os.environ.get("BATCH_OUTPUT") or context.get("output_path")
    if not input_path or not output_path:
        raise RuntimeError("Input and output paths are required.")
    for source_path, target_path in build_file_pairs(input_path, output_path):
        print("Input Path: {0}".format(source_path))
        print("Output Path: {0}".format(target_path))
        strip_geometry(source_path, target_path)
    FBApplication().FileNew()
    FBApplication().FileExit()


main()
'''


class TaskMotionBuilderScript(TaskPythonScript):
    """Task that runs MotionBuilder Python scripts as an external process."""

    task_type = constants.TaskType.MOTIONBUILDER_SCRIPT
    default_display_name = "MotionBuilder"
    application_name = "MotionBuilder"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_motionbuilder"
    icon = ui_res_lib.Icon.app_mobu
    category = "External"
    category_icon = ui_res_lib.Icon.root_miscellaneous
    metadata_scripts_key = "motionbuilder_scripts"
    temporary_file_prefix = "mobu"

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
                "script_mode": SCRIPT_MODE_EXTERNAL_FILE,
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

    def validate(self, project):
        """Validates MotionBuilder script settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        executable_path = self.resolve_motionbuilder_executable(project)
        if not executable_path:
            result.add_error("MotionBuilder executable path cannot be empty.")
        elif not os.path.isfile(executable_path):
            result.add_error("MotionBuilder executable does not exist: {0}".format(executable_path))
        if self.is_batch_mode():
            result.extend(self.validate_batch_settings(project))
        elif self.is_external_file_mode():
            result.extend(self.validate_external_file_settings(project))
        else:
            result.extend(self.validate_single_script_settings(project))
        if not self.settings.get("wait_for_completion") and self.settings.get("require_output_file"):
            result.add_warning("Require Output is ignored when Wait For Completion is disabled.")
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects output collisions before running MotionBuilder scripts.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for this task.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        output_paths = {}
        for work_item in work_items:
            output_path = self.build_output_path(work_item, step_output_dir)
            key = os.path.normcase(output_path)
            if key in output_paths:
                result.add_error(
                    "{0} output collision: {1} and {2} both map to {3}".format(
                        self.application_name,
                        output_paths[key],
                        work_item.current_path,
                        output_path,
                    )
                )
            output_paths[key] = work_item.current_path
            if os.path.exists(output_path) and not self.settings.get("overwrite", False):
                result.add_warning(
                    "{0} output already exists and will be skipped: {1}".format(self.application_name, output_path)
                )
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Runs configured MotionBuilder scripts against one work item.

        Args:
            work_item (WorkItem): Work item to process.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for this task.
            context (dict, optional): Runner context.

        Returns:
            WorkItem: Updated work item pointing to the expected MotionBuilder output file.
        """
        output_path = self.build_output_path(work_item, step_output_dir)
        if os.path.exists(output_path) and not self.settings.get("overwrite", False):
            skipped_item = task_base.WorkItem(
                source_path=work_item.source_path,
                current_path=output_path,
                metadata=dict(work_item.metadata),
            )
            raise task_base.TaskSkip(
                "Output already exists and overwrite is disabled: {0}".format(output_path),
                output_path=output_path,
                work_item=skipped_item,
            )
        if not self.modifies_in_place():
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.isdir(output_dir):
                os.makedirs(output_dir)
        script_paths, temporary_paths = self.get_runtime_script_paths(project)
        if not script_paths:
            raise RuntimeError("No {0} script was resolved for this task.".format(self.application_name))
        context_path = self.write_context_file(
            work_item=work_item,
            output_path=output_path,
            project=project,
            step_output_dir=step_output_dir,
            script_paths=script_paths,
            context=context,
        )
        temporary_paths.append(context_path)
        try:
            for script_path in script_paths:
                process_log_path = self.build_process_log_path(
                    output_path=output_path,
                    step_output_dir=step_output_dir,
                    script_path=script_path,
                    project=project,
                )
                task_utils.report_log_artifact(context, process_log_path)
                self.run_motionbuilder_script(
                    executable_path=self.resolve_motionbuilder_executable(project),
                    script_path=script_path,
                    work_item=work_item,
                    output_path=output_path,
                    project=project,
                    context_path=context_path,
                    process_log_path=process_log_path,
                )
            output_path = self.finalize_output(work_item=work_item, output_path=output_path)
        finally:
            self.cleanup_temporary_paths(temporary_paths)
        metadata = task_utils.build_metadata(task=self, work_item=work_item)
        metadata[self.metadata_scripts_key] = list(script_paths)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)

    def get_runtime_script_paths(self, project):
        """Gets script paths to run, writing inline code to a temporary script when needed.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            tuple: Script paths list and temporary paths list.
        """
        temporary_paths = []
        if not self.is_inline_mode():
            return self.get_script_paths(project), temporary_paths
        script_text = self.get_inline_script_text(project)
        file_handle, script_path = tempfile.mkstemp(prefix="{0}_inline_".format(self.temporary_file_prefix), suffix=".py")
        with os.fdopen(file_handle, "w", encoding="utf-8") as script_file:
            script_file.write(script_text)
        temporary_paths.append(script_path)
        return [script_path], temporary_paths

    def run_motionbuilder_script(
        self,
        executable_path,
        script_path,
        work_item,
        output_path,
        project,
        context_path,
        process_log_path=None,
    ):
        """Runs one MotionBuilder script.

        Args:
            executable_path (str): MotionBuilder executable path.
            script_path (str): Python script path.
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            project (BatchProcessorModel): Active project model.
            context_path (str): JSON context path.
            process_log_path (str, optional): Path used to capture child-process output.
        """
        command = self.build_motionbuilder_command(
            executable_path=executable_path,
            script_path=script_path,
            work_item=work_item,
            output_path=output_path,
            project=project,
            context_path=context_path,
        )
        process_environment = self.build_external_process_environment(
            project=project,
            work_item=work_item,
            output_path=output_path,
            context_path=context_path,
        )
        self.write_process_log(
            log_path=process_log_path,
            command=command,
            return_code="LAUNCH",
            input_path=work_item.current_path,
            output_path=output_path,
            script_path=script_path,
            context_path=context_path,
        )
        if self.settings.get("wait_for_completion", True):
            timeout_seconds = int(self.settings.get("timeout_seconds") or 0)
            timeout_value = timeout_seconds if timeout_seconds > 0 else None
            working_dir = os.path.dirname(script_path) if os.path.isdir(os.path.dirname(script_path)) else None
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding="utf-8",
                errors="replace",
                cwd=working_dir,
                env=process_environment,
            )
            try:
                stdout_text, stderr_text = process.communicate(timeout=timeout_value)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_text, stderr_text = process.communicate()
                self.write_process_log(
                    log_path=process_log_path,
                    command=command,
                    stdout_text=stdout_text,
                    stderr_text=stderr_text,
                    return_code="TIMEOUT",
                    input_path=work_item.current_path,
                    output_path=output_path,
                    script_path=script_path,
                    context_path=context_path,
                )
                raise RuntimeError(
                    "{0} script timed out. See log: {1}".format(self.application_name, process_log_path)
                )
            self.write_process_log(
                log_path=process_log_path,
                command=command,
                stdout_text=stdout_text,
                stderr_text=stderr_text,
                return_code=process.returncode,
                input_path=work_item.current_path,
                output_path=output_path,
                script_path=script_path,
                context_path=context_path,
            )
            if process.returncode:
                raise RuntimeError(
                    "{0} script failed with exit code {1}. See log: {2}. Script: {3}".format(
                        self.application_name,
                        process.returncode,
                        process_log_path,
                        script_path,
                    )
                )
        else:
            working_dir = os.path.dirname(script_path) if os.path.isdir(os.path.dirname(script_path)) else None
            subprocess.Popen(command, shell=False, cwd=working_dir, env=process_environment)

    def build_motionbuilder_command(self, executable_path, script_path, work_item, output_path, project, context_path):
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

    def build_external_process_environment(self, project, work_item, output_path, context_path):
        """Builds process environment variables for the external application.

        Args:
            project (BatchProcessorModel): Active project model.
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            context_path (str): JSON context path.

        Returns:
            dict: Environment dictionary for subprocess execution.
        """
        process_environment = dict(os.environ)
        if self.settings.get("pass_standard_arguments", self.settings.get("pass_context_arguments", True)):
            process_environment.update(
                {
                    "BATCH_INPUT": str(work_item.current_path or ""),
                    "BATCH_OUTPUT": str(output_path or ""),
                    "BATCH_PROJECT": str(getattr(project, "project_file_path", "") or ""),
                    "BATCH_PROJECT_DIR": str(project.get_project_dir() if project else ""),
                    "BATCH_TASK": str(self.display_name or ""),
                    "BATCH_TASK_ID": str(self.id or ""),
                    "BATCH_CONTEXT": str(context_path or ""),
                }
            )
        if self.settings.get("pass_environment_arguments", True):
            for key, value in self.get_environment_argument_pairs(project=project):
                env_key = "BATCH_ENV_{0}".format(str(key).upper().replace("-", "_"))
                process_environment[env_key] = str(value)
        return process_environment

    def get_environment_argument_pairs(self, project):
        """Gets project environment variables to pass as process arguments.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            list: Sorted environment variable key/value pairs.
        """
        if not project:
            return []
        task_index = None
        if hasattr(project, "get_task_environment_index"):
            task_index = project.get_task_environment_index(self)
        environment_variables = project.get_environment_variables(
            task=self,
            task_index=task_index,
            include_braces=False,
        )
        return sorted(environment_variables.items())

    def write_context_file(self, work_item, output_path, project, step_output_dir, script_paths, context=None):
        """Writes a JSON context file for MotionBuilder scripts.

        Args:
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for this task.
            script_paths (list): Script paths being run.
            context (dict, optional): Runner context.

        Returns:
            str: JSON context file path.
        """
        context = dict(context or {})
        source_relative_path = task_base.get_work_item_relative_path(work_item)
        source_relative_dir = task_base.get_work_item_relative_dir(work_item)
        payload = {
            "source_path": work_item.source_path,
            "current_path": work_item.current_path,
            "output_path": output_path,
            "step_output_dir": step_output_dir,
            "rel_path": source_relative_dir or ".",
            "json_lookup_key": source_relative_path or os.path.basename(work_item.current_path),
            "source_relative_path": source_relative_path,
            "source_relative_dir": source_relative_dir,
            "project_path": getattr(project, "project_file_path", "") or "",
            "project_dir": project.get_project_dir() if project else "",
            "task_id": self.id,
            "task_name": self.display_name,
            "task_type": self.task_type,
            "script_paths": list(script_paths),
            "environment_variables": dict(self.get_environment_argument_pairs(project=project)),
            "work_item": work_item.to_dict(),
            "context": make_json_safe(context),
        }
        file_handle, context_path = tempfile.mkstemp(
            prefix="{0}_context_".format(self.temporary_file_prefix),
            suffix=".json",
        )
        with os.fdopen(file_handle, "w", encoding="utf-8") as context_file:
            json.dump(payload, context_file, indent=4, sort_keys=True)
        return context_path

    def finalize_output(self, work_item, output_path):
        """Applies output-file expectations after MotionBuilder execution.

        Args:
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.

        Returns:
            str: Resolved output path.
        """
        if os.path.isfile(output_path):
            return output_path
        if self.settings.get("copy_input_if_output_missing"):
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.isdir(output_dir):
                os.makedirs(output_dir)
            shutil.copy2(work_item.current_path, output_path)
            return output_path
        if self.settings.get("wait_for_completion", True) and self.settings.get("require_output_file", True):
            raise RuntimeError(
                "{0} script did not create the expected output file: {1}".format(self.application_name, output_path)
            )
        return output_path

    def build_output_path(self, work_item, step_output_dir):
        """Builds the expected MotionBuilder output path.

        Args:
            work_item (WorkItem): Work item to process.
            step_output_dir (str): Output folder for this task.

        Returns:
            str: Expected output path.
        """
        if self.modifies_in_place():
            return work_item.current_path
        return task_utils.build_output_path(
            work_item=work_item,
            output_dir=step_output_dir,
            extension=self.get_output_extension(work_item),
        )

    def build_process_log_path(self, output_path, step_output_dir, script_path, project=None):
        """Builds a process log path for external application output.

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
        output_base = os.path.splitext(os.path.basename(output_path))[0] or "motionbuilder"
        script_base = os.path.splitext(os.path.basename(script_path))[0] or "script"
        file_name = "{0}_{1}_motionbuilder.log".format(
            task_base.sanitize_filename(output_base, "item"),
            task_base.sanitize_filename(script_base, "script"),
        )
        return task_base.normalize_path(os.path.join(target_dir, file_name))

    @staticmethod
    def write_process_log(
        log_path,
        command,
        stdout_text="",
        stderr_text="",
        return_code=None,
        input_path="",
        output_path="",
        script_path="",
        context_path="",
    ):
        """Writes captured external process output to a log file.

        Args:
            log_path (str): Log file path.
            command (list): Executed command.
            stdout_text (str, optional): Captured standard output.
            stderr_text (str, optional): Captured standard error.
            return_code (int or str, optional): Process return code.
            input_path (str, optional): Input path being processed.
            output_path (str, optional): Output path expected from the process.
            script_path (str, optional): Script path being executed.
            context_path (str, optional): Context JSON path.
        """
        if not log_path:
            return
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        with open(log_path, "a", encoding="utf-8", errors="replace") as log_file:
            log_file.write("Command:\n{0}\n\n".format(" ".join([str(item) for item in command])))
            log_file.write("Return Code: {0}\n\n".format(return_code))
            log_file.write("Input Path: {0}\n".format(input_path or ""))
            log_file.write("Output Path: {0}\n".format(output_path or ""))
            log_file.write("Script Path: {0}\n".format(script_path or ""))
            log_file.write("Context Path: {0}\n\n".format(context_path or ""))
            log_file.write("STDOUT:\n{0}\n\n".format(stdout_text or ""))
            log_file.write("STDERR:\n{0}\n\n".format(stderr_text or ""))

    def get_output_extension(self, work_item=None):
        """Gets the output extension.

        Args:
            work_item (WorkItem, optional): Work item used when preserving extension.

        Returns:
            str: Output extension with a leading dot.
        """
        extension = str(self.settings.get("output_extension") or "").strip()
        if not extension and work_item:
            extension = os.path.splitext(work_item.current_path)[1]
        if not extension:
            extension = ".fbx"
        if not extension.startswith("."):
            extension = "." + extension
        return extension.lower()

    def resolve_motionbuilder_executable(self, project=None):
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

    @staticmethod
    def cleanup_temporary_paths(paths):
        """Removes temporary files created for one run.

        Args:
            paths (list): File paths to remove.
        """
        for path in paths or []:
            try:
                if path and os.path.isfile(path):
                    os.remove(path)
            except OSError:
                pass


def parse_command_arguments(value):
    """Parses command-line argument text into a list.

    Args:
        value (str or list): Raw argument text.

    Returns:
        list: Parsed command arguments.
    """
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value if str(item).strip()]
    raw_text = str(value or "").replace("\r\n", "\n").replace(";", "\n")
    arguments = []
    for line in raw_text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            arguments.extend(shlex.split(line, posix=os.name != "nt"))
        except ValueError:
            arguments.append(line)
    return arguments


def make_json_safe(value):
    """Converts values into JSON-safe data.

    Args:
        value (object): Value to convert.

    Returns:
        object: JSON-safe value.
    """
    try:
        json.dumps(value)
        return value
    except TypeError:
        pass
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [make_json_safe(item) for item in value]
    return str(value)


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
