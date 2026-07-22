"""
Batch Processor Model

Project data, serialization, validation, and task ordering live here so the
tool remains usable without loading the UI.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_tasks as tasks
import datetime
import json
import logging
import os
import re
import socket
import tempfile

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_ENVIRONMENT_PATTERN = re.compile(r"\{([a-zA-Z0-9_-]+)\}")


def normalize_environment_key(key):
    """Normalizes an environment variable key.

    Args:
        key (str): Environment variable key with or without braces.

    Returns:
        str: Lowercase hyphen-separated key without braces.
    """
    key = str(key or "").strip()
    key = key.strip("{}")
    key = key.replace("_", "-")
    return key.lower()


def format_environment_key(key):
    """Formats an environment variable key using batch placeholder syntax.

    Args:
        key (str): Environment variable key.

    Returns:
        str: Key wrapped in braces.
    """
    return "{" + normalize_environment_key(key) + "}"


class BatchProcessorModel:
    """Data model for a batch processing project."""

    def __init__(self):
        """Initializes a new batch processor model."""
        self.project_file_path = None
        self.project_name = constants.Project.DEFAULT_NAME
        self.notes = ""
        self.environment_variables = dict(constants.Project.DEFAULT_ENVIRONMENT_VARIABLES)
        self.run_settings = dict(constants.Project.DEFAULT_RUN_SETTINGS)
        self.tasks = []
        self.extra_data = {}
        self.reset_project()

    @property
    def paths(self):
        """Gets legacy path values for backward compatibility.

        Returns:
            dict: Legacy path key mapping.
        """
        return {
            "project_dir": self.environment_variables.get("project-dir", ""),
            "input_dir": self.environment_variables.get("input-dir", ""),
            "process_dir": self.environment_variables.get("task-dir", ""),
            "output_dir": self.environment_variables.get("output-dir", ""),
        }

    @paths.setter
    def paths(self, value):
        """Sets environment variables from legacy path values.

        Args:
            value (dict): Legacy path mapping.
        """
        self.environment_variables = self._environment_from_legacy_paths(value or {})

    @property
    def modules(self):
        """Gets tasks using the old module attribute name.

        Returns:
            list: Batch processor tasks.
        """
        return self.tasks

    @modules.setter
    def modules(self, value):
        """Sets tasks using the old module attribute name.

        Args:
            value (list): Batch processor tasks.
        """
        self.tasks = value

    def reset_project(self):
        """Resets this model to a new default project."""
        self.project_file_path = None
        self.project_name = constants.Project.DEFAULT_NAME
        self.notes = ""
        self.environment_variables = dict(constants.Project.DEFAULT_ENVIRONMENT_VARIABLES)
        self.run_settings = dict(constants.Project.DEFAULT_RUN_SETTINGS)
        self.tasks = [tasks.InputTask()]
        self.extra_data = {}

    def get_project_dir(self):
        """Gets the project folder used to resolve relative paths.

        Returns:
            str: Configured project directory, directory containing the project file, or an empty string.
        """
        configured_project_dir = self.environment_variables.get("project-dir")
        if configured_project_dir:
            if os.path.isabs(str(configured_project_dir)):
                return tasks.normalize_path(configured_project_dir)
            if self.project_file_path:
                project_file_dir = os.path.dirname(os.path.abspath(self.project_file_path))
                return tasks.normalize_path(os.path.join(project_file_dir, str(configured_project_dir)))
            return ""
        if self.project_file_path:
            return os.path.dirname(os.path.abspath(self.project_file_path))
        return ""

    def resolve_path(self, path):
        """Resolves a project-relative, template-based, or absolute path.

        Args:
            path (str): Path to resolve.

        Returns:
            str: Normalized absolute path.
        """
        return self.resolve_template_path(path)

    def resolve_template(self, template, task=None, task_index=None, include_neighbor_paths=True):
        """Resolves a string containing batch environment variables.

        Args:
            template (str): Template string containing variables such as "{project-dir}".
            task (BatchTask, optional): Task used to resolve task-specific variables.
            task_index (int, optional): One-based task index.
            include_neighbor_paths (bool, optional): Whether previous/next task path variables should resolve.

        Returns:
            str: Template with known variables replaced.
        """
        if template is None:
            return ""
        resolved = str(template)
        for _ in range(10):
            environment_variables = self.get_environment_variables(
                task=task,
                task_index=task_index,
                include_braces=False,
                include_neighbor_paths=include_neighbor_paths,
            )

            def replace_variable(match):
                """Replaces one environment variable match.

                Args:
                    match (re.Match): Regex match object.

                Returns:
                    str: Replacement value.
                """
                key = normalize_environment_key(match.group(1))
                if key not in environment_variables:
                    return match.group(0)
                return str(environment_variables.get(key) or "")

            new_resolved = _ENVIRONMENT_PATTERN.sub(replace_variable, resolved)
            if new_resolved == resolved:
                break
            resolved = new_resolved
        return resolved

    def resolve_template_path(self, path, task=None, task_index=None, include_neighbor_paths=True):
        """Resolves a path after expanding batch environment variables.

        Args:
            path (str): Path or path template to resolve.
            task (BatchTask, optional): Task used to resolve task-specific variables.
            task_index (int, optional): One-based task index.
            include_neighbor_paths (bool, optional): Whether previous/next task path variables should resolve.

        Returns:
            str: Normalized absolute path, or an empty string for empty input.
        """
        if not path:
            return ""
        if self.path_uses_project_dir(path) and not self.get_project_dir():
            return ""
        path = self.resolve_template(
            path,
            task=task,
            task_index=task_index,
            include_neighbor_paths=include_neighbor_paths,
        )
        if not path:
            return ""
        if os.path.isabs(str(path)):
            return tasks.normalize_path(path)
        project_dir = self.get_project_dir()
        if not project_dir:
            return ""
        return tasks.normalize_path(os.path.join(project_dir, str(path)))

    def add_task(self, task):
        """Adds a process task to this project.

        Args:
            task (BatchTask): Task to add.

        Returns:
            BatchTask: Added task.
        """
        self.tasks.append(task)
        return task

    def insert_task(self, task, index=None):
        """Inserts a process task into this project.

        Args:
            task (BatchTask): Task to insert.
            index (int, optional): Zero-based insertion index. Appends when omitted or out of range.

        Returns:
            BatchTask: Inserted task.
        """
        if index is None:
            self.tasks.append(task)
            return task
        index = max(0, min(int(index), len(self.tasks)))
        self.tasks.insert(index, task)
        return task

    def add_task_from_dict(self, data, index=None, reinitialize_id=True):
        """Creates and inserts a task from serialized data.

        Args:
            data (dict): Serialized task data.
            index (int, optional): Zero-based insertion index.
            reinitialize_id (bool, optional): Whether to generate a fresh task identifier.

        Returns:
            BatchTask: Inserted task.
        """
        task_data = dict(data or {})
        if reinitialize_id:
            task_data.pop("id", None)
        task = tasks.create_task_from_dict(task_data)
        return self.insert_task(task=task, index=index)

    def add_task_by_type(self, task_type):
        """Creates and adds a process task by type key.

        Args:
            task_type (str): Task type key.

        Returns:
            BatchTask: Added task.
        """
        task = tasks.create_task(task_type=task_type)
        return self.add_task(task)

    def duplicate_task(self, task_id):
        """Duplicates a task and inserts the duplicate after the original.

        Args:
            task_id (str): Identifier for the task to duplicate.

        Returns:
            BatchTask or None: Duplicated task, if the source was found.
        """
        source_task = self.get_task(task_id)
        if not source_task:
            return None
        source_index = self.tasks.index(source_task)
        task_data = source_task.to_dict()
        task_data.pop("id", None)
        task_data["display_name"] = "{0} Copy".format(source_task.display_name)
        return self.add_task_from_dict(data=task_data, index=source_index + 1, reinitialize_id=True)

    def remove_task(self, task_id):
        """Removes a task by identifier.

        Args:
            task_id (str): Task id to remove.

        Returns:
            bool: True when a task was removed.
        """
        for index, task in enumerate(self.tasks):
            if task.id == task_id:
                del self.tasks[index]
                return True
        return False

    def get_task(self, task_id):
        """Gets a task by identifier.

        Args:
            task_id (str): Task id to find.

        Returns:
            BatchTask or None: Matching task, if found.
        """
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def get_input_task(self):
        """Gets the first input task in this project.

        Returns:
            InputTask or None: First input task, if present.
        """
        for task in self.tasks:
            if task.is_input_task:
                return task
        return None

    def get_enabled_tasks(self):
        """Gets enabled tasks in project order.

        Returns:
            list: Enabled process tasks.
        """
        return [task for task in self.tasks if task.enabled]

    def get_input_tasks(self, enabled_only=True):
        """Gets input tasks in project order.

        Args:
            enabled_only (bool, optional): If True, only enabled input tasks are returned.

        Returns:
            list: Input tasks.
        """
        input_tasks = [task for task in self.tasks if task.is_input_task]
        if enabled_only:
            input_tasks = [task for task in input_tasks if task.enabled]
        return input_tasks

    def get_task_segments(self, task_list=None):
        """Splits tasks into ordered segments at input segment boundaries.

        A new segment begins at every input task that starts a new input list.
        Input tasks without that flag join the current segment, preserving the
        merge behavior used to combine multiple input folders. Tasks before the
        first input task form a leading segment of their own.

        Args:
            task_list (list, optional): Tasks to segment. Defaults to the
                enabled tasks in project order.

        Returns:
            list: List of task lists, one per segment, in project order.
        """
        tasks = task_list if task_list is not None else self.get_enabled_tasks()
        segments = []
        current_segment = []
        for task in tasks:
            if task.starts_new_input_list() and current_segment:
                segments.append(current_segment)
                current_segment = []
            current_segment.append(task)
        if current_segment:
            segments.append(current_segment)
        return segments

    def has_input_segments(self, task_list=None):
        """Checks whether tasks split into more than one input segment.

        Args:
            task_list (list, optional): Tasks to inspect. Defaults to enabled tasks.

        Returns:
            bool: True when at least one segment boundary is present.
        """
        return len(self.get_task_segments(task_list=task_list)) > 1

    def discover_segment_input_files(self, segment_tasks):
        """Discovers input files for a single segment's input tasks.

        Unlike discover_input_files, which merges every input task in the
        project, this only considers the input tasks that belong to the given
        segment. It is used by multi-instance runs to fan out one segment at a
        time, discovering later-segment files only once earlier segments have
        produced their outputs.

        Args:
            segment_tasks (list): Tasks that make up one segment.

        Returns:
            list: Sorted discovered input file paths for the segment.
        """
        discovered = []
        for task in segment_tasks or []:
            if getattr(task, "is_input_task", False) and task.enabled:
                discovered.extend(task.discover_files(self))
        return sorted(set(discovered))

    def get_segment_for_task(self, task, task_list=None):
        """Gets the segment that contains a task.

        Args:
            task (BatchTask): Task to locate.
            task_list (list, optional): Tasks to segment. Defaults to enabled tasks.

        Returns:
            list or None: Tasks in the segment containing the task, or None.
        """
        if not task:
            return None
        for segment in self.get_task_segments(task_list=task_list):
            if any(segment_task.id == task.id for segment_task in segment):
                return segment
        return None

    def discover_incoming_files_for_task(self, task):
        """Discovers the incoming input files available to a task in its segment.

        Only the input tasks in the same segment as the given task are used, so a
        task placed after a "Start New Input List" boundary no longer reports the
        earlier segments' files.

        Args:
            task (BatchTask): Task requesting its incoming files.

        Returns:
            list: Sorted discovered incoming file paths for the task's segment.
        """
        segment = self.get_segment_for_task(task)
        if segment is None:
            segment = self.get_segment_for_task(task, task_list=list(self.tasks))
        if segment is None:
            return self.discover_input_files()
        return self.discover_segment_input_files(segment)

    def get_task_environment_index(self, task, enabled_only=None):
        """Gets the one-based task index used by path environment variables.

        Args:
            task (BatchTask): Task to index.
            enabled_only (bool, optional): Whether disabled tasks should be ignored. When
                omitted, the project automation setting determines the behavior.

        Returns:
            int: One-based task index. Tasks excluded from index variables return 0.
        """
        if not task:
            return 0
        if enabled_only is None:
            enabled_only = bool(self.run_settings.get("ignore_disabled_tasks_for_task_index", False))
        task_list = self.get_enabled_tasks() if enabled_only else list(self.tasks)
        task_index = 0
        for current_task in task_list:
            if not current_task.includes_task_index():
                if current_task.id == task.id:
                    return 0
                continue
            task_index += 1
            if current_task.id == task.id:
                return task_index
        return 0

    def get_previous_task(self, task, enabled_only=True):
        """Gets the previous task in project order.

        Args:
            task (BatchTask): Task used as the lookup point.
            enabled_only (bool, optional): Whether disabled tasks should be ignored.

        Returns:
            BatchTask or None: Previous task, if available.
        """
        if not task:
            return None
        task_list = self.get_enabled_tasks() if enabled_only else list(self.tasks)
        previous_task = None
        for current_task in task_list:
            if current_task.id == task.id:
                return previous_task
            previous_task = current_task
        return None

    def get_next_task(self, task, enabled_only=True):
        """Gets the next task in project order.

        Args:
            task (BatchTask): Task used as the lookup point.
            enabled_only (bool, optional): Whether disabled tasks should be ignored.

        Returns:
            BatchTask or None: Next task, if available.
        """
        if not task:
            return None
        task_list = self.get_enabled_tasks() if enabled_only else list(self.tasks)
        for index, current_task in enumerate(task_list):
            if current_task.id == task.id:
                next_index = index + 1
                if next_index < len(task_list):
                    return task_list[next_index]
                return None
        return None

    def get_previous_task_path(self, task, enabled_only=True):
        """Gets the resolved path produced or represented by the previous task.

        Args:
            task (BatchTask): Task used as the lookup point.
            enabled_only (bool, optional): Whether disabled tasks should be ignored.

        Returns:
            str: Resolved previous task path, or an empty string.
        """
        previous_task = self.get_previous_task(task=task, enabled_only=enabled_only)
        if not previous_task:
            return ""
        previous_index = self.get_task_environment_index(previous_task)
        return self.resolve_task_path_without_neighbor_paths(previous_task, previous_index)

    def get_previous_previous_task_path(self, task, enabled_only=True):
        """Gets the resolved path produced by the task before the previous task.

        Args:
            task (BatchTask): Task used as the lookup point.
            enabled_only (bool, optional): Whether disabled tasks should be ignored.

        Returns:
            str: Resolved path, or an empty string.
        """
        previous_task = self.get_previous_task(task=task, enabled_only=enabled_only)
        before_previous_task = self.get_previous_task(task=previous_task, enabled_only=enabled_only)
        if not before_previous_task:
            return ""
        task_index = self.get_task_environment_index(before_previous_task)
        return self.resolve_task_path_without_neighbor_paths(before_previous_task, task_index)

    def get_next_task_path(self, task, enabled_only=True):
        """Gets the resolved path produced or represented by the next task.

        Args:
            task (BatchTask): Task used as the lookup point.
            enabled_only (bool, optional): Whether disabled tasks should be ignored.

        Returns:
            str: Resolved next task path, or an empty string.
        """
        next_task = self.get_next_task(task=task, enabled_only=enabled_only)
        if not next_task:
            return ""
        next_index = self.get_task_environment_index(next_task)
        return self.resolve_task_path_without_neighbor_paths(next_task, next_index)

    def resolve_task_path_without_neighbor_paths(self, task, task_index=None):
        """Resolves a task path without expanding previous/next task path variables.

        Args:
            task (BatchTask): Task to resolve.
            task_index (int, optional): One-based task index.

        Returns:
            str: Resolved task path.
        """
        if not task:
            return ""
        return self.resolve_template_path(
            task.get_task_path_template(),
            task=task,
            task_index=task_index,
            include_neighbor_paths=False,
        )

    def discover_input_files(self):
        """Discovers input files using all enabled input tasks.

        Returns:
            list: Discovered input file paths.
        """
        discovered = []
        for input_task in self.get_input_tasks(enabled_only=True):
            discovered.extend(input_task.discover_files(self))
        return sorted(set(discovered))

    def discover_input_work_items(self):
        """Discovers input work items using all enabled input tasks.

        Returns:
            list: Discovered input work items.
        """
        discovered = {}
        for input_task in self.get_input_tasks(enabled_only=True):
            for work_item in input_task.prepare(self):
                discovered.setdefault(work_item.source_path, work_item)
        return [discovered[key] for key in sorted(discovered.keys())]

    def get_logs_dir(self):
        """Gets the resolved run log directory.

        Returns:
            str: Resolved log directory path.
        """
        log_path = self.run_settings.get("log_path") or constants.Project.DEFAULT_RUN_SETTINGS.get("log_path")
        if self.path_uses_project_dir(log_path) and not self.get_project_dir():
            return ""
        resolved = str(log_path or "")
        basic_variables = {
            "project-dir": self.get_project_dir(),
            "input-dir": self.environment_variables.get("input-dir", ""),
            "task-dir": self.environment_variables.get("task-dir", ""),
            "output-dir": self.environment_variables.get("output-dir", ""),
            "home-dir": os.path.expanduser("~"),
            "desktop-dir": os.path.join(os.path.expanduser("~"), "Desktop"),
        }
        for _ in range(10):
            def replace_variable(match):
                """Replaces one log-path environment variable match.

                Args:
                    match (re.Match): Regex match object.

                Returns:
                    str: Replacement value.
                """
                key = normalize_environment_key(match.group(1))
                if key not in basic_variables:
                    return match.group(0)
                return str(basic_variables.get(key) or "")

            new_resolved = _ENVIRONMENT_PATTERN.sub(replace_variable, resolved)
            if new_resolved == resolved:
                break
            resolved = new_resolved
        if os.path.isabs(resolved):
            return tasks.normalize_path(resolved)
        project_dir = self.get_project_dir()
        if not project_dir:
            return ""
        return tasks.normalize_path(os.path.join(project_dir, resolved))

    def validate_project(self, task_list=None):
        """Validates project paths and task settings.

        Args:
            task_list (list, optional): Specific enabled task range to validate. When omitted, all enabled tasks
                are validated.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = tasks.ValidationResult()
        if not self.tasks:
            result.add_warning("Project has no tasks.")
            return result
        validating_full_project = task_list is None
        task_list = self.get_enabled_tasks() if task_list is None else list(task_list)
        if validating_full_project and not self.get_input_tasks(enabled_only=True):
            result.add_warning("Project has no enabled input tasks.")

        for task in task_list:
            result.extend(task.validate_common_settings(self))
            result.extend(task.validate(self))
        return result

    def to_dict(self):
        """Serializes this project.

        Returns:
            dict: Serializable project data.
        """
        data = dict(self.extra_data)
        run_settings = dict(self.run_settings)
        run_settings.pop("force_recook", None)
        run_settings.pop("stop_on_error", None)
        run_settings = self._filter_current_run_settings(run_settings)
        data.update(
            {
                "version": constants.Project.VERSION,
                "project_name": self.project_name,
                "notes": self.notes,
                "environment_variables": dict(self.environment_variables),
                "run_settings": run_settings,
                "tasks": [task.to_dict() for task in self.tasks],
            }
        )
        return data

    def read_data_from_dict(self, data):
        """Updates this model from serialized project data.

        Args:
            data (dict): Serialized project data.
        """
        data = data or {}
        known_keys = set(
            [
                "version",
                "project_name",
                "notes",
                "paths",
                "environment_variables",
                "run_settings",
                "tasks",
                "modules",
            ]
        )
        self.extra_data = {}
        for key, value in data.items():
            if key not in known_keys:
                self.extra_data[key] = value
        self.project_name = data.get("project_name") or constants.Project.DEFAULT_NAME
        self.notes = data.get("notes") or ""
        self.environment_variables = dict(constants.Project.DEFAULT_ENVIRONMENT_VARIABLES)
        self.environment_variables.update(self._environment_from_legacy_paths(data.get("paths") or {}))
        self.environment_variables.update(
            self._normalize_environment_variables(data.get("environment_variables") or {})
        )
        self.run_settings = dict(constants.Project.DEFAULT_RUN_SETTINGS)
        self.run_settings.update(self._filter_current_run_settings(data.get("run_settings") or {}))
        self.run_settings.pop("force_recook", None)
        self.run_settings.pop("stop_on_error", None)
        task_data = data.get("tasks")
        if task_data is None:
            task_data = data.get("modules", [])
        self.tasks = [tasks.create_task_from_dict(item) for item in task_data]
        if not self.tasks:
            self.tasks = [tasks.InputTask()]

    def get_environment_variables(self, task=None, task_index=None, include_braces=True, include_neighbor_paths=True):
        """Gets project-level and optional task-level environment variables.

        Args:
            task (BatchTask, optional): Task used to add task-specific variables.
            task_index (int, optional): One-based task index.
            include_braces (bool, optional): If True, keys are formatted as "{variable-name}".
            include_neighbor_paths (bool, optional): Whether previous/next task path values should resolve.

        Returns:
            dict: Environment variable names and resolved values.
        """
        now = datetime.datetime.now()
        project_name = self.project_name or constants.Project.DEFAULT_NAME
        project_dir = self.get_project_dir()
        project_path = tasks.normalize_path(self.project_file_path) if self.project_file_path else ""
        project_parent_dir = os.path.dirname(project_dir) if project_dir else ""
        environment_variables = {
            "project-name": project_name,
            "project-sanitized-name": tasks.sanitize_filename(project_name.lower().replace(" ", "_")),
            "project-dir": project_dir,
            "project-path": project_path,
            "project-parent-dir": project_parent_dir,
            "project-grandparent-dir": os.path.dirname(project_parent_dir) if project_parent_dir else "",
            "input-dir": self.environment_variables.get("input-dir", ""),
            "task-dir": self.environment_variables.get("task-dir", ""),
            "output-dir": self.environment_variables.get("output-dir", ""),
            "temp-dir": tempfile.gettempdir(),
            "home-dir": os.path.expanduser("~"),
            "desktop-dir": os.path.join(os.path.expanduser("~"), "Desktop"),
            "year": now.strftime("%Y"),
            "month": now.strftime("%m"),
            "day": now.strftime("%d"),
            "time": now.strftime("%H-%M-%S"),
            "hostname": socket.gethostname(),
            "worker-count": self.run_settings.get("worker_count"),
            "multi-instance": self.run_settings.get("multi_instance"),
            "log-dir": self.get_logs_dir(),
        }
        for key, value in self.environment_variables.items():
            normalized_key = normalize_environment_key(key)
            if normalized_key and normalized_key not in environment_variables:
                environment_variables[normalized_key] = value
        if task:
            task_name = task.display_name or task.default_display_name
            if task_index is None:
                task_index = self.get_task_environment_index(task)
            task_index = task_index or 0
            previous_task = self.get_previous_task(task=task, enabled_only=True)
            previous_task_name = ""
            previous_task_path = ""
            previous_task_index = 0
            previous_previous_task = None
            previous_previous_task_name = ""
            previous_previous_task_path = ""
            previous_previous_task_index = 0
            next_task = self.get_next_task(task=task, enabled_only=True)
            next_task_name = ""
            next_task_path = ""
            next_task_index = 0
            if previous_task:
                previous_task_name = previous_task.display_name or previous_task.default_display_name
                previous_task_index = self.get_task_environment_index(previous_task)
                previous_previous_task = self.get_previous_task(task=previous_task, enabled_only=True)
                if include_neighbor_paths:
                    previous_task_path = self.get_previous_task_path(task=task, enabled_only=True)
                    previous_previous_task_path = self.get_previous_previous_task_path(task=task, enabled_only=True)
            if previous_previous_task:
                previous_previous_task_name = (
                    previous_previous_task.display_name or previous_previous_task.default_display_name
                )
                previous_previous_task_index = self.get_task_environment_index(previous_previous_task)
            if next_task:
                next_task_name = next_task.display_name or next_task.default_display_name
                next_task_index = self.get_task_environment_index(next_task)
                if include_neighbor_paths:
                    next_task_path = self.get_next_task_path(task=task, enabled_only=True)
            environment_variables.update(
                {
                    "task-name": task_name,
                    "task-sanitized-name": tasks.sanitize_filename(task_name.lower().replace(" ", "_")),
                    "task-type": task.task_type,
                    "task-id": task.id,
                    "task-idx": "{0:02d}".format(int(task_index)),
                    "task-index": str(int(task_index)),
                    "previous-task-name": previous_task_name,
                    "previous-task-sanitized-name": tasks.sanitize_filename(
                        previous_task_name.lower().replace(" ", "_"), fallback=""
                    ),
                    "previous-task-path": previous_task_path,
                    "previous-previous-task-path": previous_previous_task_path,
                    "pre-previous-task-path": previous_previous_task_path,
                    "previous-previous-task-name": previous_previous_task_name,
                    "previous-previous-task-sanitized-name": tasks.sanitize_filename(
                        previous_previous_task_name.lower().replace(" ", "_"),
                        fallback="",
                    ),
                    "previous-previous-task-idx": "{0:02d}".format(int(previous_previous_task_index)),
                    "previous-previous-task-index": str(int(previous_previous_task_index)),
                    "pre-previous-task-name": previous_previous_task_name,
                    "pre-previous-task-sanitized-name": tasks.sanitize_filename(
                        previous_previous_task_name.lower().replace(" ", "_"),
                        fallback="",
                    ),
                    "pre-previous-task-idx": "{0:02d}".format(int(previous_previous_task_index)),
                    "pre-previous-task-index": str(int(previous_previous_task_index)),
                    "previous-task-idx": "{0:02d}".format(int(previous_task_index)),
                    "previous-task-index": str(int(previous_task_index)),
                    "next-task-name": next_task_name,
                    "next-task-sanitized-name": tasks.sanitize_filename(
                        next_task_name.lower().replace(" ", "_"), fallback=""
                    ),
                    "next-task-path": next_task_path,
                    "future-task-path": next_task_path,
                    "next-task-idx": "{0:02d}".format(int(next_task_index)),
                    "next-task-index": str(int(next_task_index)),
                }
            )
        if include_braces:
            return {format_environment_key(key): value for key, value in environment_variables.items()}
        return environment_variables

    @staticmethod
    def path_uses_project_dir(path):
        """Checks whether a path template directly references the project directory variable.

        Args:
            path (str): Path template to inspect.

        Returns:
            bool: True if the template contains a project-dir token.
        """
        for match in _ENVIRONMENT_PATTERN.finditer(str(path or "")):
            if normalize_environment_key(match.group(1)) == "project-dir":
                return True
        return False

    @staticmethod
    def _normalize_environment_variables(environment_variables):
        """Normalizes serialized environment variable keys.

        Args:
            environment_variables (dict): Environment variable mapping.

        Returns:
            dict: Normalized environment variable mapping.
        """
        return {
            normalize_environment_key(key): value
            for key, value in (environment_variables or {}).items()
            if normalize_environment_key(key)
        }

    @staticmethod
    def _filter_current_run_settings(run_settings):
        """Filters run settings down to keys supported by the current project schema.

        Args:
            run_settings (dict): Run settings to filter.

        Returns:
            dict: Run settings containing only current keys.
        """
        allowed_keys = set(constants.Project.DEFAULT_RUN_SETTINGS.keys())
        return {key: value for key, value in (run_settings or {}).items() if key in allowed_keys}

    @staticmethod
    def _environment_from_legacy_paths(paths):
        """Converts legacy path settings into environment variables.

        Args:
            paths (dict): Legacy path data.

        Returns:
            dict: Environment variable mapping.
        """
        paths = paths or {}
        environment_variables = {}
        key_map = {
            "project_dir": "project-dir",
            "input_dir": "input-dir",
            "process_dir": "task-dir",
            "output_dir": "output-dir",
        }
        for old_key, new_key in key_map.items():
            if old_key in paths:
                environment_variables[new_key] = paths.get(old_key)
        return environment_variables

    def save_to_file(self, file_path=None):
        """Saves this project to disk using an atomic JSON write.

        Args:
            file_path (str, optional): Destination project file path.

        Returns:
            str: Saved project file path.
        """
        target_path = file_path or self.project_file_path
        if not target_path:
            raise ValueError("A project file path is required.")
        if not target_path.lower().endswith(constants.Project.EXTENSION):
            target_path += constants.Project.EXTENSION
        target_path = tasks.normalize_path(target_path)
        target_dir = os.path.dirname(target_path)
        if target_dir and not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        self._atomic_write_json(target_path, self.to_dict())
        self.project_file_path = target_path
        logger.info('Saved batch project: "%s"', target_path)
        return target_path

    def load_from_file(self, file_path):
        """Loads project data from a .batch file.

        Args:
            file_path (str): Project file path to load.

        Returns:
            BatchProcessorModel: This model after loading data.
        """
        file_path = tasks.normalize_path(file_path)
        with open(file_path, "r", encoding="utf-8") as project_file:
            data = json.load(project_file)
        self.read_data_from_dict(data)
        self.project_file_path = file_path
        logger.info('Loaded batch project: "%s"', file_path)
        return self

    @classmethod
    def from_file(cls, file_path):
        """Creates a model by loading a project file.

        Args:
            file_path (str): Project file path to load.

        Returns:
            BatchProcessorModel: Loaded model.
        """
        model = cls()
        return model.load_from_file(file_path)

    @staticmethod
    def _atomic_write_json(file_path, data):
        """Writes a JSON file atomically.

        Args:
            file_path (str): Destination file path.
            data (dict): Serializable data to write.
        """
        file_dir = os.path.dirname(file_path)
        file_handle, temp_path = tempfile.mkstemp(prefix=".batch_tmp_", suffix=".json", dir=file_dir)
        try:
            with os.fdopen(file_handle, "w", encoding="utf-8") as temp_file:
                json.dump(data, temp_file, indent=4, sort_keys=True)
            os.replace(temp_path, file_path)
        except Exception:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise

    def add_module(self, module):
        """Adds a task using the old module method name.

        Args:
            module (BatchTask): Task to add.

        Returns:
            BatchTask: Added task.
        """
        return self.add_task(module)

    def add_module_by_type(self, module_type):
        """Adds a task using the old module factory method name.

        Args:
            module_type (str): Legacy module type key.

        Returns:
            BatchTask: Added task.
        """
        return self.add_task_by_type(task_type=module_type)

    def remove_module(self, module_id):
        """Removes a task using the old module method name.

        Args:
            module_id (str): Legacy module id.

        Returns:
            bool: True when a task was removed.
        """
        return self.remove_task(task_id=module_id)

    def get_module(self, module_id):
        """Gets a task using the old module method name.

        Args:
            module_id (str): Legacy module id.

        Returns:
            BatchTask or None: Matching task, if found.
        """
        return self.get_task(task_id=module_id)

    def get_input_module(self):
        """Gets the input task using the old module method name.

        Returns:
            InputTask or None: Input task, if present.
        """
        return self.get_input_task()

    def get_enabled_modules(self):
        """Gets enabled tasks using the old module method name.

        Returns:
            list: Enabled tasks.
        """
        return self.get_enabled_tasks()
