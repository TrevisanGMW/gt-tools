"""
Batch Processor Python Validation Task

Runs a custom Python validation script (inline or from a file) against each
incoming file. Scripts report results through a ``validation`` reporter object,
or by returning a simple value from ``run(context)``.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor import batch_processor_run_state as run_state
from gt.tools.batch_processor.tasks import task_validation
from gt.tools.batch_processor.tasks import task_utils
import gt.ui.resource_library as ui_res_lib
import traceback
import uuid
import sys
import os


SCRIPT_MODE_INLINE = "Inline"
SCRIPT_MODE_EXTERNAL_FILE = "External File"
SCRIPT_MODE_VALUES = [SCRIPT_MODE_INLINE, SCRIPT_MODE_EXTERNAL_FILE]
SAMPLE_SCRIPTS_DIRECTORY = "validate_python"
DEFAULT_EXTERNAL_SCRIPT_PATH = "{project-dir}/scripts/validate.py"
INLINE_SCRIPT_NAME = "<validate_python_script>"

SEVERITY_INFO = "Info"
SEVERITY_WARNING = "Warning"
SEVERITY_ERROR = "Error"

STATUS_PASSED = "passed"
STATUS_WARNING = "warning"
STATUS_FAILED = "failed"
STATUS_SKIPPED = "skipped"

FAILED_STATUS_ALIASES = ["failed", "fail", "error", "errors"]
WARNING_STATUS_ALIASES = ["warning", "warnings", "warn"]
SKIPPED_STATUS_ALIASES = ["skipped", "skip"]


class ValidationReporter:
    """Collects the results reported by a Python validation script.

    Scripts receive an instance as the global ``validation`` (also available as
    ``context["validation"]``) and call ``error``, ``warning``, ``info``,
    ``check``, or ``skip`` on it.
    """

    def __init__(self):
        """Initializes an empty reporter."""
        self.entries = []
        self.checks_run = 0
        self.checks_passed = 0
        self.skip_reason = ""
        self.script_error = False

    def add_entry(self, severity, message, node=None, **details):
        """Adds one reported entry.

        Args:
            severity (str): Info, Warning, or Error.
            message (str): Human-readable message.
            node (str, optional): Maya node or item related to the entry.
            **details: Extra JSON-compatible values stored in the log.

        Returns:
            dict: Created entry.
        """
        entry = {"severity": normalize_severity(severity), "message": str(message or "")}
        if node:
            entry["node"] = str(node)
        for key, value in details.items():
            entry[str(key)] = make_json_safe(value)
        self.entries.append(entry)
        return entry

    def info(self, message, node=None, **details):
        """Reports an informational message that never counts as an issue.

        Args:
            message (str): Message text.
            node (str, optional): Related node or item.
            **details: Extra values stored in the log.

        Returns:
            dict: Created entry.
        """
        return self.add_entry(SEVERITY_INFO, message, node=node, **details)

    def warning(self, message, node=None, **details):
        """Reports a warning.

        Args:
            message (str): Message text.
            node (str, optional): Related node or item.
            **details: Extra values stored in the log.

        Returns:
            dict: Created entry.
        """
        return self.add_entry(SEVERITY_WARNING, message, node=node, **details)

    def error(self, message, node=None, **details):
        """Reports an error, which always counts as an issue.

        Args:
            message (str): Message text.
            node (str, optional): Related node or item.
            **details: Extra values stored in the log.

        Returns:
            dict: Created entry.
        """
        return self.add_entry(SEVERITY_ERROR, message, node=node, **details)

    def fail(self, message, node=None, **details):
        """Alias of error for scripts that read better with fail().

        Args:
            message (str): Message text.
            node (str, optional): Related node or item.
            **details: Extra values stored in the log.

        Returns:
            dict: Created entry.
        """
        return self.error(message, node=node, **details)

    def check(self, condition, message, severity=SEVERITY_ERROR, node=None, **details):
        """Records one check and reports the message when the condition is false.

        Args:
            condition (object): Value evaluated for truthiness.
            message (str): Message reported when the check does not pass.
            severity (str, optional): Severity used when the check does not pass.
            node (str, optional): Related node or item.
            **details: Extra values stored in the log.

        Returns:
            bool: True when the check passed.
        """
        self.checks_run += 1
        if condition:
            self.checks_passed += 1
            return True
        self.add_entry(severity, message, node=node, **details)
        return False

    def skip(self, reason=""):
        """Marks the current file as skipped instead of passed or failed.

        Args:
            reason (str, optional): Reason shown in the tracker and logs.
        """
        self.skip_reason = str(reason or "Validation script skipped this file.")

    def get_entries(self, severity):
        """Gets entries with one severity.

        Args:
            severity (str): Info, Warning, or Error.

        Returns:
            list: Matching entries.
        """
        severity = normalize_severity(severity)
        return [entry for entry in self.entries if entry.get("severity") == severity]

    def get_error_count(self):
        """Gets the number of reported errors.

        Returns:
            int: Error count.
        """
        return len(self.get_entries(SEVERITY_ERROR))

    def get_warning_count(self):
        """Gets the number of reported warnings.

        Returns:
            int: Warning count.
        """
        return len(self.get_entries(SEVERITY_WARNING))

    def has_issues(self, warnings_are_issues=True):
        """Checks whether the reported entries count as validation issues.

        Args:
            warnings_are_issues (bool, optional): Whether warnings count as issues.

        Returns:
            bool: True when errors (or counted warnings) were reported.
        """
        if self.get_error_count():
            return True
        return bool(warnings_are_issues and self.get_warning_count())

    def get_status(self):
        """Gets the overall status for the reported entries.

        Returns:
            str: passed, warning, failed, or skipped.
        """
        if self.skip_reason:
            return STATUS_SKIPPED
        if self.get_error_count():
            return STATUS_FAILED
        if self.get_warning_count():
            return STATUS_WARNING
        return STATUS_PASSED

    def get_summary(self):
        """Builds a one-line summary of the reported results.

        Returns:
            str: Summary text.
        """
        if self.skip_reason:
            return f"Skipped: {self.skip_reason}"
        summary = f"{self.get_error_count()} error(s), {self.get_warning_count()} warning(s)"
        if self.checks_run:
            summary += f", {self.checks_passed}/{self.checks_run} check(s) passed"
        return summary

    def to_dict(self, warnings_are_issues=True):
        """Serializes the reporter for logs and previews.

        Args:
            warnings_are_issues (bool, optional): Whether warnings count as issues.

        Returns:
            dict: JSON-compatible report.
        """
        return {
            "status": self.get_status(),
            "has_issues": self.has_issues(warnings_are_issues=warnings_are_issues),
            "summary": self.get_summary(),
            "error_count": self.get_error_count(),
            "warning_count": self.get_warning_count(),
            "checks_run": self.checks_run,
            "checks_passed": self.checks_passed,
            "script_error": bool(self.script_error),
            "skip_reason": self.skip_reason,
            "issues": [dict(entry) for entry in self.entries],
        }


def normalize_severity(severity):
    """Gets a canonical severity name.

    Args:
        severity (str): Raw severity value.

    Returns:
        str: Info, Warning, or Error.
    """
    severity_text = str(severity or "").strip().lower()
    if severity_text in ["info", "information", "message", "note", "passed", "pass"]:
        return SEVERITY_INFO
    if severity_text in WARNING_STATUS_ALIASES:
        return SEVERITY_WARNING
    return SEVERITY_ERROR


def make_json_safe(value):
    """Converts a value into something the JSON log writer can store.

    Args:
        value (object): Value to convert.

    Returns:
        object: JSON-compatible value.
    """
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        return {str(key): make_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [make_json_safe(item) for item in value]
    return str(value)


def add_issue_from_value(reporter, value):
    """Adds an issue described by a returned string or dictionary.

    Args:
        reporter (ValidationReporter): Reporter receiving the issue.
        value (object): A message string or a dict with severity/message keys.
    """
    if isinstance(value, dict):
        details = dict(value)
        severity = details.pop("severity", SEVERITY_ERROR)
        message = details.pop("message", "") or "Validation issue."
        node = details.pop("node", None)
        reporter.add_entry(severity, message, node=node, **details)
        return
    if value not in [None, ""]:
        reporter.error(str(value))


def apply_script_result(result, reporter):
    """Applies the value returned by run(context) to a reporter.

    Supported return values:
        None: Use only what was reported through ``validation``.
        True / False: Pass, or fail with a generic error when nothing else failed.
        str: Reported as one error message.
        list / tuple: Each item is an error string or an issue dict.
        dict: Optional "status" (passed/warning/failed/skipped), "message",
            "reason", and "issues" keys.

    Args:
        result (object): Value returned by the validation script.
        reporter (ValidationReporter): Reporter to update.
    """
    if result is None or result is True:
        return
    if result is False:
        if not reporter.get_error_count():
            reporter.error("Validation script returned False.")
        return
    if isinstance(result, str):
        add_issue_from_value(reporter, result)
        return
    if isinstance(result, (list, tuple)):
        for item in result:
            add_issue_from_value(reporter, item)
        return
    if isinstance(result, dict):
        apply_script_result_dict(result, reporter)
        return
    reporter.info(f"Ignored unsupported validation return value of type {type(result).__name__}.")


def apply_script_result_dict(result, reporter):
    """Applies a dictionary returned by run(context) to a reporter.

    Args:
        result (dict): Returned dictionary.
        reporter (ValidationReporter): Reporter to update.
    """
    for item in result.get("issues") or []:
        add_issue_from_value(reporter, item)
    status = str(result.get("status") or "").strip().lower()
    message = result.get("message") or result.get("reason") or ""
    if status in SKIPPED_STATUS_ALIASES:
        reporter.skip(message)
    elif status in FAILED_STATUS_ALIASES and not reporter.get_error_count():
        reporter.error(message or "Validation script returned a failed status.")
    elif status in WARNING_STATUS_ALIASES and not reporter.get_warning_count():
        reporter.warning(message or "Validation script returned a warning status.")
    elif message and status not in FAILED_STATUS_ALIASES + WARNING_STATUS_ALIASES:
        reporter.info(message)


def build_script_namespace(context, reporter, script_path):
    """Builds the globals used to execute a validation script.

    Args:
        context (dict): Runtime context.
        reporter (ValidationReporter): Reporter exposed as ``validation``.
        script_path (str): Value exposed as __file__.

    Returns:
        dict: Script globals.
    """
    arguments = context.get("arguments") or context.get("args") or {}
    environment_variables = context.get("environment_variables") or context.get("env") or {}
    namespace = dict(context)
    namespace.update(
        {
            "__file__": script_path,
            "__name__": f"gt_batch_validation_{str(uuid.uuid4()).replace('-', '_')}",
            "context": context,
            "batch_context": context,
            "arguments": arguments,
            "args": arguments,
            "environment_variables": environment_variables,
            "env": environment_variables,
            "validation": reporter,
            "sys": sys,
        }
    )
    try:
        import maya.cmds as cmds

        namespace["cmds"] = cmds
    except Exception:
        pass
    return namespace


def execute_validation_script(script_text, context, reporter, script_path=INLINE_SCRIPT_NAME):
    """Executes validation code and applies its optional run(context) result.

    Exceptions raised by the script are recorded as a script error on the
    reporter instead of propagating, so the log still gets written.

    Args:
        script_text (str): Python code to execute.
        context (dict): Runtime context. ``validation`` is added to it.
        reporter (ValidationReporter): Reporter receiving the results.
        script_path (str, optional): File name used in tracebacks and __file__.

    Returns:
        ValidationReporter: The updated reporter.
    """
    context = context if context is not None else {}
    context["validation"] = reporter
    namespace = build_script_namespace(context, reporter, script_path)
    script_dir = os.path.dirname(script_path) if os.path.isfile(script_path) else ""
    added_path = bool(script_dir and script_dir not in sys.path)
    if added_path:
        sys.path.insert(0, script_dir)
    try:
        exec(compile(str(script_text or ""), script_path, "exec"), namespace)
        run_function = namespace.get("run")
        if callable(run_function):
            apply_script_result(run_function(context), reporter)
    except Exception as exception:
        reporter.script_error = True
        reporter.error(
            f"Validation script raised {type(exception).__name__}: {exception}",
            traceback=traceback.format_exc(),
        )
    finally:
        if added_path and script_dir in sys.path:
            sys.path.remove(script_dir)
    return reporter


def get_current_scene_path():
    """Gets the scene currently open in Maya, if any.

    Returns:
        str: Scene path, or an empty string outside Maya or for untitled scenes.
    """
    try:
        import maya.cmds as cmds

        return cmds.file(query=True, sceneName=True) or ""
    except Exception:
        return ""


class TaskValidationPythonScript(task_base.BatchTask):
    """Task that validates each incoming file with a custom Python script."""

    task_type = constants.TaskType.PYTHON_SCRIPT_VALIDATE
    default_display_name = "Validate Python"
    default_target_path_template = task_validation.VALIDATION_LOG_TARGET_PATH_TEMPLATE
    icon = ui_res_lib.Icon.batch_task_validate_python
    category = "Validation"
    category_icon = ui_res_lib.Icon.batch_category_validation
    is_indexless_task = True
    supports_run_once_after_jobs = True
    supports_run_once_before_jobs = True
    sample_scripts_directory = SAMPLE_SCRIPTS_DIRECTORY

    def get_default_settings(self):
        """Gets default Python validation settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "script_mode": SCRIPT_MODE_INLINE,
            "script_text": "",
            "script_path": DEFAULT_EXTERNAL_SCRIPT_PATH,
            "script_font_size": 14,
            "preferences_collapsed": False,
            "pass_standard_arguments": True,
            "pass_environment_arguments": True,
            "load_scene": True,
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "log_mode": task_validation.VALIDATION_LOG_ISSUES,
            "fail_on_issues": False,
            "warnings_are_issues": True,
            "fail_on_script_error": True,
            "overwrite": True,
            "run_once_before_multi_instance": False,
            "run_once_after_multi_instance": False,
            "force_segment_separator": False,
            "segment_name": "",
            "segment_color": "blue_light_sky",
        }

    def get_script_mode(self):
        """Gets the active script mode.

        Returns:
            str: Inline or External File.
        """
        mode = str(self.settings.get("script_mode") or "").strip().lower()
        if mode in ["external", "external file", "file"]:
            return SCRIPT_MODE_EXTERNAL_FILE
        return SCRIPT_MODE_INLINE

    def is_external_file_mode(self):
        """Checks whether the script is loaded from an external file.

        Returns:
            bool: True in External File mode.
        """
        return self.get_script_mode() == SCRIPT_MODE_EXTERNAL_FILE

    def resolve_external_script_path(self, project):
        """Resolves the configured external script path.

        Args:
            project (BatchProcessorModel): Project used to resolve templates.

        Returns:
            str: Resolved script path, empty when not configured.
        """
        script_path = str(self.settings.get("script_path") or "").strip()
        if not script_path:
            return ""
        if project:
            return project.resolve_template_path(script_path, task=self)
        return task_base.normalize_path(script_path)

    def get_script_source(self, project):
        """Gets the code to execute and the name used for tracebacks.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            tuple: (script_text, script_path).

        Raises:
            IOError: The external script file cannot be read.
        """
        if not self.is_external_file_mode():
            return str(self.settings.get("script_text") or ""), INLINE_SCRIPT_NAME
        script_path = self.resolve_external_script_path(project)
        return task_utils.load_script_file(script_path), script_path

    def validate(self, project):
        """Validates task settings before running.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        if self.is_external_file_mode():
            script_path = self.resolve_external_script_path(project)
            if not script_path:
                result.add_error("Validate Python external script path cannot be empty.")
                return result
            if not os.path.isfile(script_path):
                result.add_error(f"Validate Python script does not exist: {script_path}")
                return result
            if not script_path.lower().endswith(".py"):
                result.add_error(f"Validate Python script must use the .py extension: {script_path}")
                return result
        try:
            script_text, script_path = self.get_script_source(project)
        except (IOError, OSError) as exception:
            result.add_error(f"Unable to read Validate Python script: {exception}")
            return result
        if not script_text.strip():
            result.add_error("Validate Python script cannot be empty.")
            return result
        try:
            compile(script_text, script_path, "exec")
        except SyntaxError as exception:
            result.add_error(f"Validate Python script syntax error on line {exception.lineno}: {exception.msg}")
        return result

    def build_runtime_context(self, project, work_item, step_output_dir, context=None, preview=False):
        """Builds the runtime context exposed to the validation script.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Work item being validated, or None.
            step_output_dir (str): Validation log directory.
            context (dict, optional): Runner context.
            preview (bool, optional): Whether this is a current-scene preview run.

        Returns:
            dict: Runtime context.
        """
        return task_utils.build_python_script_runtime_context(
            project=project,
            task=self,
            work_item=work_item,
            output_path=step_output_dir,
            context=context,
            extra_values={
                "project": project,
                "task": self,
                "work_item": work_item,
                "output_path": step_output_dir,
                "log_dir": step_output_dir,
                "scene_loaded": bool(self.settings.get("load_scene", True)),
                "preview": bool(preview),
            },
            pass_standard_arguments=self.settings.get("pass_standard_arguments", True),
            pass_environment_arguments=self.settings.get("pass_environment_arguments", True),
        )

    def run_validation(self, project, work_item, step_output_dir, context=None, preview=False):
        """Runs the validation script and returns its reporter.

        Args:
            project (BatchProcessorModel): Active project.
            work_item (WorkItem): Work item being validated, or None.
            step_output_dir (str): Validation log directory.
            context (dict, optional): Runner context.
            preview (bool, optional): Whether this is a current-scene preview run.

        Returns:
            ValidationReporter: Collected results.
        """
        reporter = ValidationReporter()
        try:
            script_text, script_path = self.get_script_source(project)
        except (IOError, OSError) as exception:
            reporter.script_error = True
            reporter.error(f"Unable to read validation script: {exception}")
            return reporter
        runtime_context = self.build_runtime_context(
            project=project,
            work_item=work_item,
            step_output_dir=step_output_dir,
            context=context,
            preview=preview,
        )
        return execute_validation_script(script_text, runtime_context, reporter, script_path=script_path)

    def warnings_are_issues(self):
        """Checks whether warnings count as issues.

        Returns:
            bool: True when warnings count toward Fail On Issues and Log Issues Only.
        """
        return bool(self.settings.get("warnings_are_issues", True))

    def execute(self, work_item, project, step_output_dir, context=None):
        """Validates one incoming file with the configured script.

        Args:
            work_item (WorkItem): Work item to validate.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Log output directory.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Original work item.

        Raises:
            TaskSkip: The script asked to skip this file.
            RuntimeError: The script crashed or reported issues and the task is set to fail.
        """
        if self.settings.get("load_scene", True):
            task_utils.load_source_scene(
                work_item.current_path,
                source_load_mode=self.settings.get("source_load_mode") or "Open",
                load_relevant_plugins=self.settings.get("load_relevant_plugins", True),
            )
        reporter = self.run_validation(project, work_item, step_output_dir, context=context)
        report = reporter.to_dict(warnings_are_issues=self.warnings_are_issues())
        has_issues = report.get("has_issues")
        self.print_report_summary(os.path.basename(work_item.current_path), reporter)
        if reporter.skip_reason:
            raise task_base.TaskSkip(reporter.skip_reason)
        run_state.record_validation(project, not has_issues)
        entry = {"source": work_item.current_path}
        entry.update(report)
        task_validation.write_task_validation_log(
            task=self,
            step_output_dir=step_output_dir,
            entry=entry,
            has_issues=has_issues,
            context=context,
        )
        if reporter.script_error and self.settings.get("fail_on_script_error", True):
            raise RuntimeError(f"Validation script failed to run for: {work_item.current_path}")
        if has_issues and self.settings.get("fail_on_issues"):
            summary = reporter.get_summary()
            raise RuntimeError(f"Python validation found issues ({summary}) in: {work_item.current_path}")
        return task_base.WorkItem(
            source_path=work_item.source_path,
            current_path=work_item.current_path,
            metadata=task_utils.build_metadata(self, work_item),
        )

    @staticmethod
    def print_report_summary(item_label, reporter):
        """Prints a concise validation summary and every reported issue.

        Args:
            item_label (str): File name or label identifying what was validated.
            reporter (ValidationReporter): Collected results.
        """
        sys.stdout.write(f"Validate Python [{reporter.get_status()}] {item_label}: {reporter.get_summary()}\n")
        for entry in reporter.entries:
            node = f" ({entry.get('node')})" if entry.get("node") else ""
            sys.stdout.write(f"  - {entry.get('severity')}: {entry.get('message')}{node}\n")
        sys.stdout.flush()

    def run_on_current_scene(self, project):
        """Runs the validation script against the scene already open in Maya.

        Nothing is loaded, saved, logged, or recorded in the run state.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            ValidationReporter: Collected results.
        """
        scene_path = get_current_scene_path()
        work_item = task_base.WorkItem(source_path=scene_path, current_path=scene_path)
        return self.run_validation(project, work_item, step_output_dir="", context={}, preview=True)
