"""
Batch Processor Command Task

Runs a terminal command or program as a batch step, either once per input item
or once before/after all jobs. Typical uses are starting or stopping services
(for example Docker containers), launching or closing programs, and calling
external command-line tools. Output is streamed into the batch log.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_command_process as command_process
from gt.tools.batch_processor.tasks import task_command_utils as command_utils
from gt.tools.batch_processor.tasks import task_utils
import gt.ui.resource_library as ui_res_lib
import os
import re
import shutil
import tempfile
import time

_PER_ITEM_TOKEN_PATTERN = re.compile(r"\{input[-_](file|string|meta)[^}]*\}", re.IGNORECASE)
_STARTUP_CHECK_SECONDS = 1.0


class TaskCommand(task_base.BatchTask):
    """Task that runs a command-line program or shell command."""

    task_type = constants.TaskType.COMMAND
    default_display_name = "Command"
    default_target_path_template = "{previous-task-path}"
    icon = ui_res_lib.Icon.batch_task_command
    category = "Utilities"
    category_icon = ui_res_lib.Icon.root_utilities
    is_task_path_passthrough = True
    supports_run_once_after_jobs = True
    supports_run_once_before_jobs = True

    @property
    def is_aggregate_task(self):
        """Gets whether this task runs once instead of once per item.

        Returns:
            bool: Whether either project-wide run-once option is enabled.
        """
        return bool(
            self.settings.get("run_once_before_multi_instance", False)
            or self.settings.get("run_once_after_multi_instance", False)
        )

    def uses_incoming_files(self):
        """Keeps the incoming work items flowing through this task.

        Returns:
            bool: Always True because the command never discovers source files.
        """
        return True

    def writes_to_target_path(self):
        """Prevents validation of the hidden common target path.

        Returns:
            bool: Always False because the command does not produce task outputs.
        """
        return False

    def get_default_settings(self):
        """Gets default Command task settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "command_mode": command_utils.CommandMode.PROGRAM,
            "executable": "",
            "arguments": "",
            "shell_type": command_utils.ShellType.SYSTEM,
            "command_text": "",
            "working_directory": "{project-dir}",
            "environment_overrides": "",
            "inherit_environment": True,
            "pass_standard_arguments": True,
            "pass_environment_arguments": True,
            "wait_mode": command_utils.WaitMode.WAIT_FOR_EXIT,
            "timeout_seconds": 0,
            "accepted_exit_codes": "0",
            "on_failure": command_utils.FailureAction.FAIL,
            "ready_check": command_utils.ReadyCheck.URL,
            "ready_target": "",
            "ready_timeout_seconds": 600,
            "ready_interval_seconds": 5,
            "log_output": True,
            "write_output_log": False,
            "output_log_path": "{project-dir}/logs/command_{task-idx-padded}.log",
            "run_once_before_multi_instance": False,
            "run_once_after_multi_instance": False,
            "force_segment_separator": False,
            "segment_name": "",
            "segment_color": "blue_light_sky",
        }

    # ------------------------------------------------------------------ Validation
    def validate(self, project):
        """Validates Command task settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        command_mode = self.settings.get("command_mode")
        if command_mode not in command_utils.COMMAND_MODES:
            result.add_error(f'Command task "{self.display_name}" has an unknown command mode: {command_mode}')
            return result
        if command_mode == command_utils.CommandMode.PROGRAM:
            executable_text = str(self.settings.get("executable") or "").strip()
            if not executable_text:
                result.add_error(f'Command task "{self.display_name}" needs an executable.')
            elif not has_per_item_tokens(executable_text):
                environment = self.build_environment(project, work_item=None)
                if not self.resolve_executable(project, environment):
                    result.add_error(
                        f'Command task "{self.display_name}" cannot find the executable: '
                        f"{project.resolve_template(executable_text, task=self)}"
                    )
        elif not str(self.settings.get("command_text") or "").strip():
            result.add_error(f'Command task "{self.display_name}" needs a shell command.')

        _, environment_errors = command_utils.parse_environment_overrides(self.settings.get("environment_overrides"))
        for error in environment_errors:
            result.add_error(f'Command task "{self.display_name}": {error}')
        _, exit_code_errors = command_utils.parse_exit_codes(self.settings.get("accepted_exit_codes"))
        for error in exit_code_errors:
            result.add_error(f'Command task "{self.display_name}": {error}')

        wait_mode = self.settings.get("wait_mode")
        if wait_mode not in command_utils.WAIT_MODES:
            result.add_error(f'Command task "{self.display_name}" has an unknown wait mode: {wait_mode}')
        if wait_mode == command_utils.WaitMode.WAIT_UNTIL_READY:
            result.extend(self.validate_ready_settings(project))
        if wait_mode == command_utils.WaitMode.LAUNCH_AND_CONTINUE and not self.is_aggregate_task:
            result.add_warning(
                f'Command task "{self.display_name}" launches one process per input item and does not wait for them.'
            )

        working_directory = self.resolve_working_directory(project)
        if working_directory and not has_per_item_tokens(self.settings.get("working_directory")):
            if not os.path.isdir(working_directory):
                result.add_warning(
                    f'Command task "{self.display_name}" working directory does not exist yet: {working_directory}'
                )
        return result

    def validate_ready_settings(self, project):
        """Validates the Wait Until Ready settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        ready_check = self.settings.get("ready_check")
        if ready_check not in command_utils.READY_CHECKS:
            result.add_error(f'Command task "{self.display_name}" has an unknown ready check: {ready_check}')
            return result
        ready_target = str(self.settings.get("ready_target") or "")
        if not has_per_item_tokens(ready_target):
            for error in command_utils.validate_ready_target(ready_check, self.resolve_ready_target(project)):
                result.add_error(f'Command task "{self.display_name}": {error}')
        if int(self.settings.get("ready_timeout_seconds") or 0) <= 0:
            result.add_warning(
                f'Command task "{self.display_name}" waits for readiness without a timeout and may never finish.'
            )
        return result

    # ------------------------------------------------------------------ Resolution
    def resolve_text(self, project, text):
        """Resolves batch tokens in free text such as arguments or URLs.

        Args:
            project (BatchProcessorModel): Active project.
            text (str): Text with optional batch tokens.

        Returns:
            str: Resolved text.
        """
        if project is None:
            return str(text or "")
        return project.resolve_template(str(text or ""), task=self)

    def resolve_working_directory(self, project):
        """Resolves the working directory, falling back to the project directory.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Absolute working directory, or an empty string when none is configured.
        """
        working_directory = str(self.settings.get("working_directory") or "").strip()
        if project is None:
            return working_directory
        if working_directory:
            resolved_directory = project.resolve_template_path(working_directory, task=self)
            if resolved_directory:
                return resolved_directory
        return project.get_project_dir() or ""

    def resolve_ready_target(self, project):
        """Resolves the readiness target text.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Resolved target.
        """
        ready_target = str(self.settings.get("ready_target") or "").strip()
        if self.settings.get("ready_check") == command_utils.ReadyCheck.FILE and project is not None:
            return project.resolve_template_path(ready_target, task=self)
        return self.resolve_text(project, ready_target).strip()

    def resolve_executable(self, project, environment):
        """Resolves the Program-mode executable to a full path.

        Bare names such as ``docker`` are searched on the process PATH. Names with
        a folder are resolved as project paths.

        Args:
            project (BatchProcessorModel): Active project.
            environment (dict): Process environment providing PATH.

        Returns:
            str: Executable path, or an empty string when it cannot be found.
        """
        executable_text = self.resolve_text(project, self.settings.get("executable")).strip().strip('"')
        if not executable_text:
            return ""
        if os.path.isabs(executable_text) or "/" in executable_text or "\\" in executable_text:
            if project is not None and not os.path.isabs(executable_text):
                executable_text = project.resolve_template_path(executable_text, task=self)
            if os.path.isfile(executable_text):
                return executable_text
            return shutil.which(executable_text) or ""
        search_path = command_utils.get_environment_value(environment, "PATH") or None
        return shutil.which(executable_text, path=search_path) or ""

    def get_environment_override_pairs(self, project):
        """Gets environment overrides with batch tokens resolved.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            list: Ordered (key, value) pairs.
        """
        pairs, _ = command_utils.parse_environment_overrides(self.settings.get("environment_overrides"))
        return [(key, self.resolve_text(project, value)) for key, value in pairs]

    def get_batch_environment_values(self, project, work_item):
        """Gets BATCH_* variables passed to the process.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Current item, or None when running once.

        Returns:
            dict: Variable names and values.
        """
        values = {}
        if self.settings.get("pass_standard_arguments", True):
            values.update(
                {
                    "BATCH_INPUT": str(getattr(work_item, "current_path", "") or ""),
                    "BATCH_SOURCE": str(getattr(work_item, "source_path", "") or ""),
                    "BATCH_PROJECT": str(getattr(project, "project_file_path", "") or ""),
                    "BATCH_PROJECT_DIR": str(project.get_project_dir() if project else ""),
                    "BATCH_TASK": str(self.display_name or ""),
                    "BATCH_TASK_ID": str(self.id or ""),
                }
            )
        if self.settings.get("pass_environment_arguments", True) and project is not None:
            task_index = None
            if hasattr(project, "get_task_environment_index"):
                task_index = project.get_task_environment_index(self)
            environment_variables = project.get_environment_variables(
                task=self,
                task_index=task_index,
                include_braces=False,
            )
            for key, value in sorted(environment_variables.items()):
                values[command_utils.build_batch_environment_name(key)] = str(value if value is not None else "")
        return values

    def build_environment(self, project, work_item):
        """Builds the full process environment.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Current item, or None when running once.

        Returns:
            dict: Process environment.
        """
        return command_utils.build_process_environment(
            base_environment=os.environ,
            inherit_environment=bool(self.settings.get("inherit_environment", True)),
            batch_values=self.get_batch_environment_values(project, work_item),
            override_pairs=self.get_environment_override_pairs(project),
        )

    def build_command_plan(self, project, work_item=None):
        """Resolves everything needed to start the process.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem, optional): Current item, or None when running once.

        Returns:
            dict: Keys ``command``, ``use_shell``, ``working_directory``, ``environment``,
                ``override_pairs``, and ``display``.

        Raises:
            RuntimeError: When the executable cannot be found or the command is empty.
        """
        environment = self.build_environment(project, work_item)
        if self.settings.get("command_mode") == command_utils.CommandMode.SHELL:
            command_text = self.resolve_text(project, self.settings.get("command_text"))
            if not command_text.strip():
                raise RuntimeError("Shell command is empty.")
            powershell_executable = "powershell" if os.name == "nt" else "pwsh"
            command, use_shell = command_utils.build_shell_command(
                command_text, self.settings.get("shell_type"), powershell_executable=powershell_executable
            )
            display = f"[{self.settings.get('shell_type')}] {command_text.strip()}"
        else:
            executable_path = self.resolve_executable(project, environment)
            if not executable_path:
                raise RuntimeError(
                    "Executable not found: {0}".format(self.resolve_text(project, self.settings.get("executable")))
                )
            arguments = [
                self.resolve_text(project, argument)
                for argument in command_utils.split_arguments(self.settings.get("arguments"))
            ]
            command = [executable_path] + arguments
            use_shell = False
            display = command_utils.format_command_for_display(command)
        override_pairs = self.get_environment_override_pairs(project)
        return {
            "command": command,
            "use_shell": use_shell,
            "working_directory": self.resolve_working_directory(project),
            "environment": environment,
            "override_pairs": override_pairs,
            "display": command_utils.mask_secrets(display, override_pairs),
        }

    def build_preview_lines(self, project):
        """Builds a readable preview of the resolved command.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            list: Preview lines.
        """
        try:
            plan = self.build_command_plan(project)
        except RuntimeError as error:
            return [f"Error: {error}"]
        lines = [
            f"Command: {plan['display']}",
            f"Working Directory: {plan['working_directory'] or '(current process folder)'}",
            f"Wait Mode: {self.settings.get('wait_mode')}",
        ]
        if self.settings.get("wait_mode") == command_utils.WaitMode.WAIT_UNTIL_READY:
            lines.append(f"Ready Check: {self.settings.get('ready_check')} -> {self.resolve_ready_target(project)}")
        environment_lines = command_utils.format_environment_preview(plan["override_pairs"])
        if environment_lines:
            lines.append("Environment Overrides:")
            lines.extend(f"    {line}" for line in environment_lines)
        if not self.settings.get("inherit_environment", True):
            lines.append("Parent environment is NOT inherited (only system essentials are kept).")
        if not self.is_aggregate_task:
            lines.append("Per-item tokens such as {input-file} resolve when each item runs.")
        return lines

    # ------------------------------------------------------------------ Execution
    def execute(self, work_item, project, step_output_dir, context=None):
        """Runs the command for one item, or once when a run-once option is enabled.

        Args:
            work_item (WorkItem): Current item, or None for a run-once task.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Unused; the command writes no task outputs.
            context (dict, optional): Runtime context with reporting callbacks.

        Returns:
            WorkItem or list: The unchanged item, or all incoming items when running once.

        Raises:
            RuntimeError: When the command fails and the failure action is Fail.
        """
        context = context or {}
        plan = self.build_command_plan(project, work_item=work_item)
        item_label = os.path.basename(work_item.current_path) if work_item else "run once"
        report_message(context, f"Running ({item_label}): {plan['display']}")
        report_message(context, f"Working directory: {plan['working_directory'] or '(current process folder)'}")
        for line in command_utils.format_environment_preview(plan["override_pairs"]):
            report_message(context, f"Environment: {line}")

        accepted_codes, _ = command_utils.parse_exit_codes(self.settings.get("accepted_exit_codes"))
        wait_mode = self.settings.get("wait_mode")
        if wait_mode == command_utils.WaitMode.LAUNCH_AND_CONTINUE:
            failure_message = self.launch_and_continue(plan, project, accepted_codes, context)
        elif wait_mode == command_utils.WaitMode.WAIT_UNTIL_READY:
            failure_message = self.wait_until_ready(plan, project, accepted_codes, context)
        else:
            failure_message = self.wait_for_exit(plan, project, accepted_codes, context)

        if failure_message:
            self.handle_failure(failure_message, context)
        if self.is_aggregate_task:
            return list(context.get("work_items") or [])
        return work_item

    def build_line_callback(self, context, override_pairs):
        """Builds the output line callback used while the process runs.

        Args:
            context (dict): Runtime context.
            override_pairs (list): Environment overrides used to mask secrets.

        Returns:
            callable: Callback receiving one line, or None when output logging is off.
        """
        if not self.settings.get("log_output", True):
            return None

        def report_line(line):
            """Reports one process output line.

            Args:
                line (str): Output line.
            """
            report_message(context, f"| {command_utils.mask_secrets(line.rstrip(), override_pairs)}", prefix=False)

        return report_line

    def open_output_log(self, project, plan):
        """Opens the optional output log file in append mode.

        Args:
            project (BatchProcessorModel): Active project.
            plan (dict): Command plan.

        Returns:
            file: Open text file, or None when output logging to a file is off.
        """
        log_path = self.resolve_output_log_path(project)
        if not log_path:
            return None
        task_utils.ensure_directory(os.path.dirname(log_path))
        log_handle = open(log_path, "a", encoding="utf-8", errors="replace")
        log_handle.write(f"\n===== {task_utils.get_timestamp()} | {plan['display']}\n")
        log_handle.flush()
        return log_handle

    def resolve_output_log_path(self, project):
        """Resolves the output log path when writing an output log is enabled.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Log file path, or an empty string when disabled.
        """
        if not self.settings.get("write_output_log", False) or project is None:
            return ""
        return project.resolve_template_path(self.settings.get("output_log_path"), task=self)

    def wait_for_exit(self, plan, project, accepted_codes, context):
        """Runs the command and waits for it to exit.

        Args:
            plan (dict): Command plan.
            project (BatchProcessorModel): Active project.
            accepted_codes (set or None): Accepted exit codes.
            context (dict): Runtime context.

        Returns:
            str: Failure message, or an empty string on success.
        """
        log_handle = self.open_output_log(project, plan)
        try:
            result = command_process.run_and_wait(
                plan["command"],
                plan["use_shell"],
                plan["working_directory"],
                plan["environment"],
                timeout_seconds=float(self.settings.get("timeout_seconds") or 0),
                line_callback=self.build_line_callback(context, plan["override_pairs"]),
                log_handle=log_handle,
            )
        finally:
            if log_handle:
                log_handle.close()
        if result.timed_out:
            return f"Command timed out after {self.settings.get('timeout_seconds')} second(s) and was stopped."
        if not command_utils.is_exit_code_accepted(result.exit_code, accepted_codes):
            return f"Command exited with code {result.exit_code} (accepted: {self.get_accepted_codes_label()})."
        report_message(context, f"Command finished with exit code {result.exit_code} in {result.elapsed_seconds:.1f}s.")
        return ""

    def launch_and_continue(self, plan, project, accepted_codes, context):
        """Starts the command and continues without waiting for it.

        A short startup check catches commands that fail immediately.

        Args:
            plan (dict): Command plan.
            project (BatchProcessorModel): Active project.
            accepted_codes (set or None): Accepted exit codes.
            context (dict): Runtime context.

        Returns:
            str: Failure message, or an empty string on success.
        """
        log_path = self.resolve_output_log_path(project)
        if log_path:
            task_utils.ensure_directory(os.path.dirname(log_path))
        process = command_process.launch_detached(
            plan["command"], plan["use_shell"], plan["working_directory"], plan["environment"], log_path=log_path
        )
        deadline = time.time() + _STARTUP_CHECK_SECONDS
        while time.time() < deadline and process.poll() is None:
            time.sleep(0.1)
        exit_code = process.poll()
        if exit_code is not None and not command_utils.is_exit_code_accepted(exit_code, accepted_codes):
            return f"Launched command exited right away with code {exit_code}."
        report_message(context, f"Launched process {process.pid} and continued without waiting.")
        return ""

    def wait_until_ready(self, plan, project, accepted_codes, context):
        """Starts the command and waits until the readiness check passes.

        Args:
            plan (dict): Command plan.
            project (BatchProcessorModel): Active project.
            accepted_codes (set or None): Accepted exit codes.
            context (dict): Runtime context.

        Returns:
            str: Failure message, or an empty string on success.
        """
        ready_probe, ready_label = self.build_ready_probe(project, plan)
        log_path = self.resolve_output_log_path(project)
        is_temporary_log = not log_path
        if is_temporary_log:
            file_descriptor, log_path = tempfile.mkstemp(prefix="gt_batch_command_", suffix=".log")
            os.close(file_descriptor)
        else:
            task_utils.ensure_directory(os.path.dirname(log_path))
        report_message(context, f"Waiting until ready: {ready_label}")
        result = command_process.run_until_ready(
            plan["command"],
            plan["use_shell"],
            plan["working_directory"],
            plan["environment"],
            log_path=log_path,
            ready_probe=ready_probe,
            ready_timeout_seconds=float(self.settings.get("ready_timeout_seconds") or 0),
            ready_interval_seconds=float(self.settings.get("ready_interval_seconds") or 5),
            line_callback=self.build_line_callback(context, plan["override_pairs"]),
            accepted_exit_check=lambda exit_code: command_utils.is_exit_code_accepted(exit_code, accepted_codes),
        )
        if is_temporary_log and not result.still_running:
            try:
                os.remove(log_path)
            except OSError:
                pass
        if result.ready:
            state_text = f"process {result.pid} still running" if result.still_running else "process finished"
            report_message(context, f"Ready after {result.elapsed_seconds:.1f}s ({state_text}).")
            return ""
        if result.timed_out:
            return (
                f"Not ready after {self.settings.get('ready_timeout_seconds')} second(s): {ready_label}. "
                "The started process was stopped."
            )
        return f"Command exited with code {result.exit_code} (accepted: {self.get_accepted_codes_label()})."

    def build_ready_probe(self, project, plan):
        """Builds the readiness check function.

        Args:
            project (BatchProcessorModel): Active project.
            plan (dict): Command plan, used for the Command Succeeds check environment.

        Returns:
            tuple: (callable returning True when ready, readable description).

        Raises:
            RuntimeError: When the readiness target is invalid.
        """
        ready_check = self.settings.get("ready_check")
        ready_target = self.resolve_ready_target(project)
        errors = command_utils.validate_ready_target(ready_check, ready_target)
        if errors:
            raise RuntimeError("; ".join(errors))
        label = f"{ready_check} - {ready_target}"
        if ready_check == command_utils.ReadyCheck.URL:
            return (lambda: command_process.check_url(ready_target)), label
        if ready_check == command_utils.ReadyCheck.PORT:
            host, port = command_utils.parse_host_port(ready_target)
            return (lambda: command_process.check_port(host, port)), label
        if ready_check == command_utils.ReadyCheck.FILE:
            return (lambda: command_process.check_file(ready_target)), label
        check_command, use_shell = command_utils.build_shell_command(ready_target, command_utils.ShellType.SYSTEM)
        return (
            lambda: command_process.check_command(
                check_command, use_shell, plan["working_directory"], plan["environment"]
            )
        ), label

    def get_accepted_codes_label(self):
        """Gets the accepted exit-code rule for messages.

        Returns:
            str: Exit-code rule text.
        """
        return str(self.settings.get("accepted_exit_codes") or "0").strip() or "0"

    def handle_failure(self, message, context):
        """Applies the configured failure action.

        Args:
            message (str): Failure description.
            context (dict): Runtime context.

        Raises:
            RuntimeError: When the failure action is Fail.
        """
        failure_action = self.settings.get("on_failure", command_utils.FailureAction.FAIL)
        if failure_action == command_utils.FailureAction.IGNORE:
            report_message(context, f"{message} Ignored by the task settings.")
            return
        if failure_action == command_utils.FailureAction.WARNING:
            report_warning(context, f'Command task "{self.display_name}": {message}')
            return
        raise RuntimeError(message)


def has_per_item_tokens(text):
    """Checks whether text uses tokens that only resolve per input item.

    Args:
        text (str): Text to inspect.

    Returns:
        bool: True when per-item tokens are present.
    """
    return bool(_PER_ITEM_TOKEN_PATTERN.search(str(text or "")))


def report_message(context, message, prefix=True):
    """Reports a message to the batch tracker, or stdout outside a run.

    Args:
        context (dict): Runtime context.
        message (str): Message text.
        prefix (bool, optional): Whether to add the ``[Command]`` prefix.
    """
    text = f"[Command] {message}" if prefix else message
    reporter = (context or {}).get("report_message")
    if callable(reporter):
        reporter(text)
    else:
        print(text, flush=True)


def report_warning(context, message):
    """Reports a warning to the batch tracker, falling back to a log message.

    Args:
        context (dict): Runtime context.
        message (str): Warning text.
    """
    report_message(context, f"[WARNING] {message}")
    reporter = (context or {}).get("report_warning")
    if callable(reporter):
        reporter(message)
