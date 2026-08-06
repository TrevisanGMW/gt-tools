"""
Batch Processor External Script Task
"""

from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor.tasks.task_python_script import TaskPythonScript
import json
import os
import shlex
import shutil
import subprocess
import tempfile


class TaskExternalScript(TaskPythonScript):
    """Base task for running Python scripts in an external application."""

    application_name = "External Application"
    category = "External"
    metadata_scripts_key = "external_scripts"
    temporary_file_prefix = "external"
    process_log_name = "external"

    def get_default_settings(self):
        """Gets common external script task settings.

        Returns:
            dict: Default settings for an external script task.
        """
        settings = super().get_default_settings()
        settings.update(
            {
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
        """Validates external script settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        executable_path = self.resolve_motionbuilder_executable(project)
        if not executable_path:
            result.add_error(
                "{0} executable path cannot be empty.".format(self.application_name)
            )
        elif not os.path.isfile(executable_path):
            result.add_error(
                "{0} executable does not exist: {1}".format(
                    self.application_name, executable_path
                )
            )

        if self.is_batch_mode():
            result.extend(self.validate_batch_settings(project))
        elif self.is_external_file_mode():
            result.extend(self.validate_external_file_settings(project))
        else:
            result.extend(self.validate_single_script_settings(project))

        if (
            not self.settings.get("wait_for_completion")
            and self.settings.get("require_output_file")
        ):
            result.add_warning(
                "Require Output is ignored when Wait For Completion is disabled."
            )
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects output collisions for external script tasks.

        Args:
            work_items (list): Work items entering the task.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for the task.
            context (dict, optional): Runner context.

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

            if os.path.exists(output_path) and not self.settings.get(
                "overwrite", False
            ):
                result.add_warning(
                    "{0} output already exists and will be skipped: {1}".format(
                        self.application_name, output_path
                    )
                )
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Runs configured external scripts for one work item.

        Args:
            work_item (WorkItem): Work item to process.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for the task.
            context (dict, optional): Runner context.

        Returns:
            WorkItem: Updated work item pointing to the external output file.
        """
        output_path = self.build_output_path(work_item, step_output_dir)
        if os.path.exists(output_path) and not self.settings.get("overwrite", False):
            skipped_item = task_base.WorkItem(
                source_path=work_item.source_path,
                current_path=output_path,
                metadata=dict(work_item.metadata),
            )
            raise task_base.TaskSkip(
                "Output already exists and overwrite is disabled: {0}".format(
                    output_path
                ),
                output_path=output_path,
                work_item=skipped_item,
            )

        if not self.modifies_in_place():
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.isdir(output_dir):
                os.makedirs(output_dir)

        script_paths, temporary_paths = self.get_runtime_script_paths(project)
        if not script_paths:
            raise RuntimeError(
                "No {0} script resolved task.".format(
                    self.application_name
                )
            )

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
            output_path = self.finalize_output(
                work_item=work_item,
                output_path=output_path,
            )
        finally:
            self.cleanup_temporary_paths(temporary_paths)

        metadata = task_utils.build_metadata(task=self, work_item=work_item)
        metadata[self.metadata_scripts_key] = list(script_paths)
        return task_base.WorkItem(
            source_path=work_item.source_path,
            current_path=output_path,
            metadata=metadata,
        )

    def get_runtime_script_paths(self, project):
        """Gets script paths, creating a temporary file for inline code.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            tuple: Script paths and temporary paths.
        """
        temporary_paths = []
        if not self.is_inline_mode():
            return self.get_script_paths(project), temporary_paths

        script_text = self.get_inline_script_text(project)
        file_handle, script_path = tempfile.mkstemp(
            prefix="{0}_inline_".format(self.temporary_file_prefix),
            suffix=".py",
        )
        with os.fdopen(file_handle, "w", encoding="utf-8") as script_file:
            script_file.write(script_text)
        temporary_paths.append(script_path)
        return [script_path], temporary_paths

    def run_external_script(
        self,
        executable_path,
        script_path,
        work_item,
        output_path,
        project,
        context_path,
        process_log_path=None,
    ):
        """Runs one external application script.

        Args:
            executable_path (str): External application executable path.
            script_path (str): Python script path.
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            project (BatchProcessorModel): Active project model.
            context_path (str): JSON context path.
            process_log_path (str, optional): Path used to capture output.
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
            working_dir = (
                os.path.dirname(script_path)
                if os.path.isdir(os.path.dirname(script_path))
                else None
            )
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
                stdout_text, stderr_text = process.communicate(
                    timeout=timeout_value
                )
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
                    "{0} script timed out. See log: {1}".format(
                        self.application_name,
                        process_log_path,
                    )
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
            working_dir = (
                os.path.dirname(script_path)
                if os.path.isdir(os.path.dirname(script_path))
                else None
            )
            subprocess.Popen(
                command,
                shell=False,
                cwd=working_dir,
                env=process_environment,
            )

    def build_external_process_environment(
        self, project, work_item, output_path, context_path
    ):
        """Builds environment variables for an external application.

        Args:
            project (BatchProcessorModel): Active project model.
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            context_path (str): JSON context path.

        Returns:
            dict: Environment dictionary for subprocess execution.
        """
        process_environment = dict(os.environ)
        if self.settings.get(
            "pass_standard_arguments",
            self.settings.get("pass_context_arguments", True),
        ):
            process_environment.update(
                {
                    "BATCH_INPUT": str(work_item.current_path or ""),
                    "BATCH_OUTPUT": str(output_path or ""),
                    "BATCH_PROJECT": str(
                        getattr(project, "project_file_path", "") or ""
                    ),
                    "BATCH_PROJECT_DIR": str(
                        project.get_project_dir() if project else ""
                    ),
                    "BATCH_TASK": str(self.display_name or ""),
                    "BATCH_TASK_ID": str(self.id or ""),
                    "BATCH_CONTEXT": str(context_path or ""),
                }
            )

        if self.settings.get("pass_environment_arguments", True):
            for key, value in self.get_environment_argument_pairs(project=project):
                env_key = "BATCH_ENV_{0}".format(
                    str(key).upper().replace("-", "_")
                )
                process_environment[env_key] = str(value)
        return process_environment

    def get_environment_argument_pairs(self, project):
        """Gets project environment arguments.

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

    def write_context_file(
        self,
        work_item,
        output_path,
        project,
        step_output_dir,
        script_paths,
        context=None,
    ):
        """Writes a JSON context file for external scripts.

        Args:
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for the task.
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
            "json_lookup_key": source_relative_path
            or os.path.basename(work_item.current_path),
            "source_relative_path": source_relative_path,
            "source_relative_dir": source_relative_dir,
            "project_path": getattr(project, "project_file_path", "") or "",
            "project_dir": project.get_project_dir() if project else "",
            "task_id": self.id,
            "task_name": self.display_name,
            "task_type": self.task_type,
            "script_paths": list(script_paths),
            "environment_variables": dict(
                self.get_environment_argument_pairs(project=project)
            ),
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
        """Applies output-file expectations after external execution.

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

        if self.settings.get(
            "wait_for_completion", True
        ) and self.settings.get("require_output_file", True):
            raise RuntimeError(
                "{0} script did not create expected output file: {1}".format(
                    self.application_name, output_path
                )
            )
        return output_path

    def build_output_path(self, work_item, step_output_dir):
        """Builds the expected external application output path.

        Args:
            work_item (WorkItem): Work item being processed.
            step_output_dir (str): Output folder for the task.

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

    def build_process_log_path(
        self, output_path, step_output_dir, script_path, project=None
    ):
        """Builds a process log path for an external application.

        Args:
            output_path (str): Expected output path.
            step_output_dir (str): Task output folder.
            script_path (str): Script being executed.
            project (BatchProcessorModel, optional): Active project model.

        Returns:
            str: Process log path, or an empty string when logging is disabled.
        """
        if not self.settings.get("write_process_log", True):
            return ""
        log_dir = project.get_logs_dir() if project and hasattr(project, "get_logs_dir") else ""
        target_dir = log_dir or step_output_dir
        output_base = os.path.splitext(os.path.basename(output_path))[0] or self.process_log_name
        script_base = os.path.splitext(os.path.basename(script_path))[0] or "script"
        file_name = "{0}_{1}_{2}.log".format(
            task_base.sanitize_filename(output_base, "item"),
            task_base.sanitize_filename(script_base, "script"),
            self.process_log_name,
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
            stdout_text (str): Captured standard output.
            stderr_text (str): Captured standard error.
            return_code (int or str): Process return code.
            input_path (str): Input path processed.
            output_path (str): Output path expected from the process.
            script_path (str): Script path executed.
            context_path (str): Context JSON path.
        """
        if not log_path:
            return
        log_dir = os.path.dirname(log_path)
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        with open(log_path, "a", encoding="utf-8", errors="replace") as log_file:
            log_file.write(
                "Command:\n{0}\n\n".format(
                    " ".join([str(item) for item in command])
                )
            )
            log_file.write("Return Code: {0}\n\n".format(return_code))
            log_file.write("Input Path: {0}\n".format(input_path or ""))
            log_file.write("Output Path: {0}\n".format(output_path or ""))
            log_file.write("Script Path: {0}\n".format(script_path or ""))
            log_file.write("Context Path: {0}\n\n".format(context_path or ""))
            log_file.write("STDOUT:\n{0}\n\n".format(stdout_text or ""))
            log_file.write("STDERR:\n{0}\n\n".format(stderr_text or ""))

    def get_output_extension(self, work_item=None):
        """Gets the configured output extension.

        Args:
            work_item (WorkItem, optional): Work item used to preserve extension.

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

    @staticmethod
    def cleanup_temporary_paths(paths):
        """Removes temporary files created during one run.

        Args:
            paths (list): File paths to remove.
        """
        for path in paths or []:
            try:
                if os.path.isfile(path):
                    os.remove(path)
            except OSError:
                pass

    def build_external_command(
        self, executable_path, script_path, work_item, output_path, project, context_path
    ):
        """Builds an external application command.

        Args:
            executable_path (str): External application executable path.
            script_path (str): Script path.
            work_item (WorkItem): Work item being processed.
            output_path (str): Expected output path.
            project (BatchProcessorModel): Active project model.
            context_path (str): Context JSON path.

        Returns:
            list: Command arguments.
        """
        raise NotImplementedError

    def resolve_executable(self, project=None):
        """Resolves the external application executable path.

        Args:
            project (BatchProcessorModel, optional): Active project model.

        Returns:
            str: Resolved executable path.
        """
        raise NotImplementedError

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
        """Compatibility wrapper for the former MotionBuilder runner name."""
        return self.run_external_script(
            executable_path=executable_path,
            script_path=script_path,
            work_item=work_item,
            output_path=output_path,
            project=project,
            context_path=context_path,
            process_log_path=process_log_path,
        )

    def build_motionbuilder_command(
        self, executable_path, script_path, work_item, output_path, project, context_path
    ):
        """Compatibility wrapper for the former command-builder name."""
        return self.build_external_command(
            executable_path=executable_path,
            script_path=script_path,
            work_item=work_item,
            output_path=output_path,
            project=project,
            context_path=context_path,
        )

    def resolve_motionbuilder_executable(self, project=None):
        """Compatibility wrapper for the former executable resolver name."""
        return self.resolve_executable(project=project)


def parse_command_arguments(value):
    """Parses command-line text into a list of arguments.

    Args:
        value (str or list): Raw argument text or argument values.

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
    """Converts values to JSON-safe data.

    Args:
        value (object): Value to convert.

    Returns:
        object: JSON-safe value.
    """
    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, dict):
            return {str(key): make_json_safe(item) for key, item in value.items()}
        if isinstance(value, (list, tuple)):
            return [make_json_safe(item) for item in value]
        return str(value)
