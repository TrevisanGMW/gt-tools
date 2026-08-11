"""
Batch Processor Python Script Tasks
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor.tasks import task_utils
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
import importlib.util
import fnmatch
import os
import sys
import uuid


SCRIPT_MODE_INLINE = "Inline"
SCRIPT_MODE_EXTERNAL_FILE = "External File"
SCRIPT_MODE_BATCH_DIRECTORY = "Batch Directory"
SCRIPT_MODE_SINGLE = SCRIPT_MODE_INLINE
SCRIPT_MODE_BATCH = SCRIPT_MODE_BATCH_DIRECTORY
SCRIPT_MODE_VALUES = [SCRIPT_MODE_INLINE, SCRIPT_MODE_EXTERNAL_FILE, SCRIPT_MODE_BATCH_DIRECTORY]
LEGACY_DEFAULT_DISPLAY_NAMES = set(["Run Python Script", "Run Python Scripts Folder"])
DEFAULT_PYTHON_INLINE_SCRIPT = task_utils.load_script("script_inline_python_script.py")


class TaskPythonScript(task_base.BatchTask):
    """Task that runs inline Python code or external scripts against each incoming Maya file."""

    task_type = constants.TaskType.PYTHON_SCRIPT
    default_display_name = "Python"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_python"
    icon = ui_res_lib.Icon.batch_task_python
    category = "Utilities"
    category_icon = ui_res_lib.Icon.root_utilities
    def __init__(self, *args, **kwargs):
        """Initializes the Python task and normalizes legacy settings."""
        super().__init__(*args, **kwargs)
        self._normalize_python_settings()

    def get_default_settings(self):
        """Gets default Python script task settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "script_mode": SCRIPT_MODE_INLINE,
            "script_text": DEFAULT_PYTHON_INLINE_SCRIPT,
            "script_path": "{project-dir}/scripts/post_process.py",
            "scripts_path": "{project-dir}/scripts",
            "batch_include_patterns": "",
            "batch_exclude_patterns": "",
            "batch_filters_visible": False,
            "pass_standard_arguments": True,
            "pass_environment_arguments": True,
            "font_size": 14,
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "output_extension": ".ma",
            "overwrite": False,
        }

    def _normalize_python_settings(self):
        """Normalizes script mode values and old default display names."""
        if self.display_name in LEGACY_DEFAULT_DISPLAY_NAMES:
            self.display_name = self.default_display_name
        self.settings["script_mode"] = self.normalize_script_mode(self.settings.get("script_mode"))
        self.settings.setdefault("script_text", "")
        self.settings.setdefault("script_path", "{project-dir}/scripts/post_process.py")
        self.settings.setdefault("scripts_path", "{project-dir}/scripts")
        self.settings.setdefault("batch_include_patterns", "")
        self.settings.setdefault("batch_exclude_patterns", "")
        self.settings.setdefault("batch_filters_visible", False)
        self.settings.setdefault("pass_standard_arguments", True)
        self.settings.setdefault("pass_environment_arguments", True)
        self.settings.setdefault("font_size", 14)
        if "external_scripts" not in self.settings:
            self.settings["external_scripts"] = [
                {"path": self.settings.get("script_path", ""), "enabled": True}
            ]
        if "batch_directories" not in self.settings:
            self.settings["batch_directories"] = [
                {
                    "path": self.settings.get("scripts_path", ""),
                    "include_patterns": self.settings.get("batch_include_patterns", ""),
                    "exclude_patterns": self.settings.get("batch_exclude_patterns", ""),
                }
            ]

        self.settings["external_scripts"] = self._normalize_external_script_entries(
            self.settings.get("external_scripts")
        )
        self.settings["batch_directories"] = self._normalize_batch_directory_entries(
            self.settings.get("batch_directories")
        )

    @staticmethod
    def _normalize_external_script_entries(entries):
        """Normalizes external script entries into a serializable list.

        Args:
            entries (list): Raw external script entries.

        Returns:
            list: Normalized external script dictionaries.
        """
        if entries is None:
            return []
        if not isinstance(entries, (list, tuple)):
            entries = [entries]
        normalized_entries = []
        for entry in entries:
            if isinstance(entry, dict):
                path = entry.get("path", entry.get("script_path", ""))
                enabled = entry.get("enabled", True)
            else:
                path = entry
                enabled = True
            if isinstance(enabled, str):
                enabled = enabled.strip().lower() not in ["", "0", "false", "no", "off"]
            normalized_entries.append({"path": str(path or ""), "enabled": bool(enabled)})
        return normalized_entries

    @staticmethod
    def _normalize_batch_directory_entries(entries):
        """Normalizes batch-directory entries into a serializable list.

        Args:
            entries (list): Raw batch-directory entries.

        Returns:
            list: Normalized batch-directory dictionaries.
        """
        if entries is None:
            return []
        if not isinstance(entries, (list, tuple)):
            entries = [entries]
        normalized_entries = []
        for entry in entries:
            if isinstance(entry, dict):
                path = entry.get("path", entry.get("scripts_path", ""))
                include_patterns = entry.get("include_patterns", entry.get("include", ""))
                exclude_patterns = entry.get("exclude_patterns", entry.get("exclude", ""))
            else:
                path = entry
                include_patterns = ""
                exclude_patterns = ""
            normalized_entries.append(
                {
                    "path": str(path or ""),
                    "include_patterns": str(include_patterns or ""),
                    "exclude_patterns": str(exclude_patterns or ""),
                }
            )
        return normalized_entries

    def get_external_script_entries(self):
        """Gets ordered external script entries.

        Returns:
            list: Copies of external script entry dictionaries.
        """
        entries = self._normalize_external_script_entries(self.settings.get("external_scripts"))
        self.settings["external_scripts"] = entries
        return [dict(entry) for entry in entries]

    def set_external_script_entries(self, entries):
        """Stores ordered external script entries.

        Args:
            entries (list): External script entries to store.
        """
        self.settings["external_scripts"] = self._normalize_external_script_entries(entries)

    def get_batch_directory_entries(self):
        """Gets ordered batch-directory entries.

        Returns:
            list: Copies of batch-directory entry dictionaries.
        """
        entries = self._normalize_batch_directory_entries(self.settings.get("batch_directories"))
        self.settings["batch_directories"] = entries
        return [dict(entry) for entry in entries]

    def set_batch_directory_entries(self, entries):
        """Stores ordered batch-directory entries.

        Args:
            entries (list): Batch-directory entries to store.
        """
        self.settings["batch_directories"] = self._normalize_batch_directory_entries(entries)

    @staticmethod
    def normalize_script_mode(script_mode):
        """Gets a canonical script mode value.

        Args:
            script_mode (str): Raw script mode.

        Returns:
            str: Canonical script mode.
        """
        mode = str(script_mode or "").strip().lower().replace("_", " ")
        if mode in ["inline", "single", "single script"]:
            return SCRIPT_MODE_INLINE
        if mode in ["external", "external file", "file", "script file", "python file"]:
            return SCRIPT_MODE_EXTERNAL_FILE
        if mode in [
            "batch",
            "batch directory",
            "folder",
            "directory",
            "scripts",
            "scripts folder",
            "python scripts",
            "python scripts folder",
        ]:
            return SCRIPT_MODE_BATCH_DIRECTORY
        return SCRIPT_MODE_INLINE

    def set_script_mode(self, script_mode):
        """Sets the script mode after normalizing the value.

        Args:
            script_mode (str): Script mode value.
        """
        self.settings["script_mode"] = self.normalize_script_mode(script_mode)

    def get_script_mode(self):
        """Gets the active script mode.

        Returns:
            str: Active script mode.
        """
        return self.normalize_script_mode(self.settings.get("script_mode"))

    def is_batch_mode(self):
        """Checks whether this task is using folder/batch script mode.

        Returns:
            bool: True when using batch mode.
        """
        return self.get_script_mode() == SCRIPT_MODE_BATCH_DIRECTORY

    def is_external_file_mode(self):
        """Checks whether this task is using one external Python file.

        Returns:
            bool: True when using external file mode.
        """
        return self.get_script_mode() == SCRIPT_MODE_EXTERNAL_FILE

    def is_inline_mode(self):
        """Checks whether this task is using inline Python code.

        Returns:
            bool: True when using inline mode.
        """
        return self.get_script_mode() == SCRIPT_MODE_INLINE

    def validate(self, project):
        """Validates Python script settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        if self.is_batch_mode():
            result.extend(self.validate_batch_settings(project))
        elif self.is_external_file_mode():
            result.extend(self.validate_external_file_settings(project))
        else:
            result.extend(self.validate_single_script_settings(project))
        extension = self.get_output_extension()
        if extension not in [".ma", ".mb"]:
            result.add_error("Python script output extension must be .ma or .mb.")
        return result

    def validate_single_script_settings(self, project):
        """Validates inline Python code settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        script_text = self.get_inline_script_text(project)
        if not str(script_text or "").strip():
            result.add_error("Python script cannot be empty.")
            return result
        try:
            compile(script_text, "<gt_batch_python_script>", "exec")
        except SyntaxError as exception:
            result.add_error("Python script syntax error on line {0}: {1}".format(exception.lineno, exception.msg))
        return result

    def validate_external_file_settings(self, project):
        """Validates enabled external Python script files.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        entries = self.get_external_script_entries()
        enabled_entries = [entry for entry in entries if entry.get("enabled", True)]
        if not enabled_entries:
            result.add_warning("No enabled external Python scripts are configured.")
            return result
        for script_index, entry in enumerate(enabled_entries, start=1):
            script_path = self.resolve_external_script_path(entry.get("path"), project)
            if not script_path:
                result.add_error(f"External Python script {script_index} cannot be empty.")
            elif not os.path.isfile(script_path):
                result.add_error(f"External Python script does not exist: {script_path}")
            elif not script_path.lower().endswith(".py"):
                result.add_error(f"External Python script must use the .py extension: {script_path}")
        return result

    def validate_batch_settings(self, project):
        """Validates folder/batch Python script settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        directory_entries = self.get_batch_directory_entries()
        if not directory_entries:
            result.add_warning("No Python script directories are configured.")
            return result
        for directory_index, entry in enumerate(directory_entries, start=1):
            scripts_dir = self.resolve_batch_directory_path(entry.get("path"), project)
            if not scripts_dir:
                result.add_error(f"Python scripts directory {directory_index} cannot be empty.")
                continue
            if not os.path.isdir(scripts_dir):
                result.add_error(f"Python scripts directory does not exist: {scripts_dir}")
                continue
            script_paths = self.get_batch_script_paths(project, entry)
            if not script_paths:
                result.add_warning(
                    f"Python scripts directory contains no runnable .py scripts: {scripts_dir}"
                )
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects output collisions before running scripts.

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
                    "Python script collision: {0} and {1} both map to {2}".format(
                        output_paths[key], work_item.current_path, output_path
                    )
                )
            output_paths[key] = work_item.current_path
            if self.modifies_in_place():
                current_extension = os.path.splitext(work_item.current_path)[1].lower()
                if current_extension not in [".ma", ".mb"]:
                    result.add_error(
                        "Python script can only modify Maya scene files in place: {0}".format(
                            work_item.current_path
                        )
                    )
            if (
                os.path.exists(output_path)
                and not self.modifies_in_place()
                and not self.settings.get("overwrite", False)
            ):
                result.add_warning("Python script output already exists and will be skipped: {0}".format(output_path))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Runs the configured Python script against one work item.

        Args:
            work_item (WorkItem): Work item to process.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for this task.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Updated work item pointing to the cooked Maya scene.
        """
        output_path = self.build_output_path(work_item, step_output_dir)
        if (
            os.path.exists(output_path)
            and not self.modifies_in_place()
            and not self.settings.get("overwrite", False)
        ):
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

        self.load_source_scene(work_item.current_path)
        script_paths = self.get_script_paths(project)
        runtime_context = self.build_script_context(
            work_item=work_item,
            output_path=output_path,
            project=project,
            script_paths=script_paths,
            context=context,
        )
        if self.is_batch_mode() or self.is_external_file_mode():
            for script_path in script_paths:
                self.run_python_script(script_path=script_path, context=runtime_context)
        else:
            script_text = self.get_inline_script_text(project)
            self.run_inline_python_script(script_text=script_text, context=runtime_context)
        batch_processor_maya.save_scene(output_path, file_type=batch_processor_maya.get_maya_file_type(output_path))
        metadata = dict(work_item.metadata)
        metadata["last_task_id"] = self.id
        metadata["last_task_type"] = self.task_type
        metadata["settings_hash"] = task_base.hash_settings(self.settings)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)

    def get_script_paths(self, project):
        """Gets script paths to run.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            list: Script paths.
        """
        if self.is_external_file_mode():
            script_paths = []
            for entry in self.get_external_script_entries():
                if not entry.get("enabled", True):
                    continue
                script_path = self.resolve_external_script_path(entry.get("path"), project)
                if script_path and os.path.isfile(script_path):
                    script_paths.append(script_path)
            return script_paths
        if self.is_inline_mode():
            return []
        script_paths = []
        for entry in self.get_batch_directory_entries():
            script_paths.extend(self.get_batch_script_paths(project, entry))
        return script_paths

    def get_batch_script_paths(self, project, directory_entry):
        """Gets runnable Python scripts for one ordered directory entry.

        Args:
            project (BatchProcessorModel): Active project model.
            directory_entry (dict): Batch-directory settings.

        Returns:
            list: Sorted script paths from the directory.
        """
        scripts_dir = self.resolve_batch_directory_path(directory_entry.get("path"), project)
        if not os.path.isdir(scripts_dir):
            return []
        include_patterns = parse_filter_patterns(directory_entry.get("include_patterns"))
        exclude_patterns = parse_filter_patterns(directory_entry.get("exclude_patterns"))
        script_paths = []
        for file_name in sorted(os.listdir(scripts_dir)):
            if not file_name.lower().endswith(".py") or file_name.startswith("__"):
                continue
            script_path = task_base.normalize_path(os.path.join(scripts_dir, file_name))
            if not self.is_batch_script_allowed(
                script_path=script_path,
                scripts_dir=scripts_dir,
                include_patterns=include_patterns,
                exclude_patterns=exclude_patterns,
            ):
                continue
            script_paths.append(script_path)
        return script_paths

    def is_batch_script_allowed(self, script_path, scripts_dir, include_patterns=None, exclude_patterns=None):
        """Checks whether a batch script passes include and exclude filters.

        Args:
            script_path (str): Python script path to inspect.
            scripts_dir (str): Root scripts directory.
            include_patterns (list, optional): Include patterns for this directory.
            exclude_patterns (list, optional): Exclude patterns for this directory.

        Returns:
            bool: True when the script should run.
        """
        if include_patterns is None:
            include_patterns = self.get_batch_include_patterns()
        if exclude_patterns is None:
            exclude_patterns = self.get_batch_exclude_patterns()
        relative_path = os.path.relpath(script_path, scripts_dir).replace("\\", "/")
        file_name = os.path.basename(script_path)
        if include_patterns and not self.matches_filter_patterns(
            file_name,
            relative_path,
            script_path,
            include_patterns,
        ):
            return False
        if exclude_patterns and self.matches_filter_patterns(file_name, relative_path, script_path, exclude_patterns):
            return False
        return True

    def get_batch_include_patterns(self):
        """Gets normalized include patterns for batch-directory scripts.

        Returns:
            list: Include glob patterns.
        """
        return parse_filter_patterns(self.settings.get("batch_include_patterns"))

    def get_batch_exclude_patterns(self):
        """Gets normalized exclude patterns for batch-directory scripts.

        Returns:
            list: Exclude glob patterns.
        """
        return parse_filter_patterns(self.settings.get("batch_exclude_patterns"))

    @staticmethod
    def matches_filter_patterns(file_name, relative_path, script_path, patterns):
        """Checks script identifiers against glob patterns.

        Args:
            file_name (str): Script file name.
            relative_path (str): Script path relative to scripts root.
            script_path (str): Absolute script path.
            patterns (list): Glob patterns.

        Returns:
            bool: True if any pattern matches.
        """
        normalized_path = task_base.normalize_path(script_path).replace("\\", "/")
        candidates = [file_name, relative_path, normalized_path]
        lower_candidates = [candidate.lower() for candidate in candidates]
        for pattern in patterns:
            pattern = str(pattern).replace("\\", "/")
            lower_pattern = pattern.lower()
            for candidate in candidates:
                if fnmatch.fnmatch(candidate, pattern):
                    return True
            for candidate in lower_candidates:
                if fnmatch.fnmatch(candidate, lower_pattern):
                    return True
        return False

    def resolve_script_path(self, project):
        """Resolves the configured script path.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            str: Resolved script path.
        """
        return self.resolve_external_script_path(self.settings.get("script_path"), project)

    def resolve_external_script_path(self, script_path, project):
        """Resolves an external script entry path.

        Args:
            script_path (str): External script path or template.
            project (BatchProcessorModel): Project used to resolve templates.

        Returns:
            str: Resolved script path.
        """
        script_path = str(script_path or "")
        if project:
            return project.resolve_template_path(script_path, task=self)
        return task_base.normalize_path(script_path)

    def resolve_scripts_path(self, project):
        """Resolves the configured scripts folder path.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            str: Resolved scripts folder path.
        """
        return self.resolve_batch_directory_path(self.settings.get("scripts_path"), project)

    def resolve_batch_directory_path(self, directory_path, project):
        """Resolves a batch-directory entry path.

        Args:
            directory_path (str): Batch-directory path or template.
            project (BatchProcessorModel): Project used to resolve templates.

        Returns:
            str: Resolved directory path.
        """
        directory_path = str(directory_path or "")
        if project:
            return project.resolve_template_path(directory_path, task=self)
        return task_base.normalize_path(directory_path)

    def get_inline_script_text(self, project=None):
        """Gets inline script text, falling back to old script-path data when possible.

        Args:
            project (BatchProcessorModel, optional): Active project model.

        Returns:
            str: Inline script text.
        """
        script_text = self.settings.get("script_text")
        if script_text:
            return script_text
        legacy_script_path = None
        if project:
            legacy_script_path = self.resolve_script_path(project)
        else:
            legacy_script_path = self.settings.get("script_path")
        if legacy_script_path and os.path.isfile(legacy_script_path):
            try:
                with open(legacy_script_path, "r", encoding="utf-8") as script_file:
                    return script_file.read()
            except UnicodeDecodeError:
                with open(legacy_script_path, "r") as script_file:
                    return script_file.read()
        return ""

    def load_source_scene(self, source_path):
        """Loads a source file into Maya.

        Args:
            source_path (str): Source file path.
        """
        load_relevant_plugins = self.settings.get("load_relevant_plugins", True)
        source_load_mode = str(self.settings.get("source_load_mode") or "Open").lower()
        if source_load_mode == "open" and os.path.splitext(source_path)[1].lower() in [".ma", ".mb", ".fbx"]:
            batch_processor_maya.open_scene(source_path, load_relevant_plugins=load_relevant_plugins)
            return
        batch_processor_maya.new_scene()
        if os.path.isfile(source_path):
            batch_processor_maya.import_file(source_path, load_relevant_plugins=load_relevant_plugins)

    def build_output_path(self, work_item, step_output_dir):
        """Builds the cooked Maya output path.

        Args:
            work_item (WorkItem): Work item to process.
            step_output_dir (str): Output folder for this task.

        Returns:
            str: Resolved output path.
        """
        if self.modifies_in_place():
            return work_item.current_path
        base_name = os.path.splitext(os.path.basename(work_item.current_path))[0]
        file_name = task_base.sanitize_filename(base_name, "scene") + self.get_output_extension()
        return task_base.build_work_item_output_path(
            work_item=work_item,
            output_dir=step_output_dir,
            file_name=file_name,
        )

    def get_output_extension(self):
        """Gets the normalized output extension.

        Returns:
            str: Output extension with leading dot.
        """
        extension = str(self.settings.get("output_extension") or ".ma").lower()
        if not extension.startswith("."):
            extension = "." + extension
        return extension

    def build_script_context(self, work_item, output_path, project, script_paths, context=None):
        """Builds the context dictionary passed to pipeline scripts.

        Args:
            work_item (WorkItem): Work item being processed.
            output_path (str): Output scene path.
            project (BatchProcessorModel): Active project model.
            script_paths (list): Script paths being run.
            context (dict, optional): Runner context.

        Returns:
            dict: Context dictionary.
        """
        context = dict(context or {})
        source_file = os.path.basename(work_item.current_path)
        source_relative_path = task_base.get_work_item_relative_path(work_item)
        rel_path = task_base.get_work_item_relative_dir(work_item) or "."
        json_lookup_key = source_relative_path or source_file
        project_path = getattr(project, "project_file_path", "") or ""
        project_dir = project.get_project_dir() if project else ""
        environment_variables = {}
        if project and self.settings.get("pass_environment_arguments", True):
            task_index = None
            if hasattr(project, "get_task_environment_index"):
                task_index = project.get_task_environment_index(self)
            environment_variables = project.get_environment_variables(
                task=self,
                task_index=task_index,
                include_braces=False,
            )
        arguments = {}
        if self.settings.get("pass_standard_arguments", True):
            arguments = {
                "input": work_item.current_path,
                "output": output_path,
                "project": project_path,
                "project_path": project_path,
                "project_dir": project_dir,
                "task": self.display_name,
                "task_id": self.id,
                "current_path": work_item.current_path,
                "source_path": work_item.source_path,
                "output_path": output_path,
                "task_name": self.display_name,
                "task_type": self.task_type,
                "file_name": source_file,
                "source_relative_path": source_relative_path,
                "source_relative_dir": rel_path if rel_path != "." else "",
            }
        context.update(
            {
                "file_name": source_file,
                "source_path": work_item.current_path,
                "current_path": work_item.current_path,
                "original_source_path": work_item.source_path,
                "output_path": output_path,
                "rel_path": rel_path,
                "json_lookup_key": json_lookup_key,
                "source_relative_path": source_relative_path,
                "source_relative_dir": rel_path if rel_path != "." else "",
                "project_path": project_path,
                "project_dir": project_dir,
                "task_id": self.id,
                "task_name": self.display_name,
                "task_type": self.task_type,
                "scripts_dir": os.path.dirname(script_paths[0]) if script_paths else "",
                "script_paths": list(script_paths),
                "work_item": work_item,
                "arguments": arguments,
                "args": arguments,
                "environment_variables": environment_variables,
                "env": environment_variables,
            }
        )
        return context

    @staticmethod
    def build_script_globals(context, file_path):
        """Builds globals exposed to inline and file-based Python scripts.

        Args:
            context (dict): Runtime context.
            file_path (str): Value to expose as __file__.

        Returns:
            dict: Globals dictionary used to execute Python code.
        """
        if context is None:
            context = {}
        arguments = context.get("arguments") or context.get("args") or {}
        environment_variables = context.get("environment_variables") or context.get("env") or {}
        exec_globals = {
            "__file__": file_path,
            "context": context,
            "batch_context": context,
            "arguments": arguments,
            "args": arguments,
            "environment_variables": environment_variables,
            "env": environment_variables,
        }
        try:
            import maya.cmds as cmds

            exec_globals["cmds"] = cmds
        except Exception:
            pass
        return exec_globals

    @staticmethod
    def run_inline_python_script(script_text, context):
        """Executes inline Python code.

        The code receives global `context`, `arguments`, and
        `environment_variables` dictionaries. If the code defines `run(context)`,
        it is called after the code is executed, matching the behavior of
        file-based batch scripts.

        Args:
            script_text (str): Python code to execute.
            context (dict): Runtime context.
        """
        if context is None:
            context = {}
        module_name = "gt_batch_inline_script_{0}".format(str(uuid.uuid4()).replace("-", "_"))
        exec_globals = TaskPythonScript.build_script_globals(context=context, file_path="<gt_batch_python_script>")
        exec_globals["__name__"] = module_name
        exec(compile(script_text, "<gt_batch_python_script>", "exec"), exec_globals)
        run_function = exec_globals.get("run")
        if callable(run_function):
            run_function(context)

    @staticmethod
    def run_python_script(script_path, context):
        """Imports and runs a Python script.

        Args:
            script_path (str): Python script path.
            context (dict): Context passed to `run(context)` when present.
        """
        if context is None:
            context = {}
        module_name = "gt_batch_script_{0}".format(str(uuid.uuid4()).replace("-", "_"))
        script_dir = os.path.dirname(script_path)
        if script_dir and script_dir not in sys.path:
            sys.path.insert(0, script_dir)
        spec = importlib.util.spec_from_file_location(module_name, script_path)
        module = importlib.util.module_from_spec(spec)
        script_globals = TaskPythonScript.build_script_globals(context=context, file_path=script_path)
        script_globals["__name__"] = module_name
        module.__dict__.update(script_globals)
        spec.loader.exec_module(module)
        if hasattr(module, "run"):
            module.run(context)


class TaskPythonScriptsFolder(TaskPythonScript):
    """Backward-compatible Python task preset that starts in batch mode."""

    task_type = constants.TaskType.PYTHON_SCRIPT
    default_display_name = "Python"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_python"

    def get_default_settings(self):
        """Gets default Python scripts folder task settings.

        Returns:
            dict: Default settings.
        """
        settings = super().get_default_settings()
        settings["script_mode"] = SCRIPT_MODE_BATCH_DIRECTORY
        settings["scripts_path"] = "{project-dir}/scripts"
        return settings


def parse_filter_patterns(value):
    """Parses comma, semicolon, or newline-separated glob patterns.

    Args:
        value (str or list): Raw filter pattern value.

    Returns:
        list: Clean pattern strings.
    """
    if isinstance(value, (list, tuple)):
        raw_items = value
    else:
        raw_text = str(value or "")
        raw_text = raw_text.replace(";", "\n").replace(",", "\n")
        raw_items = raw_text.splitlines()
    return [str(item).strip() for item in raw_items if str(item).strip()]
