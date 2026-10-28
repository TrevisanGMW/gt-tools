"""Run another saved Batch Processor project as one tracked task."""

import os

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_projects as projects
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib


class TaskRunBatchProject(task_base.BatchTask):
    """Serializable settings for a child project launch."""

    task_type = "run_batch_project"
    default_display_name = "Run Batch Project"
    category = "Utilities"
    category_icon = ui_res_lib.Icon.root_utilities
    icon = ui_res_lib.Icon.batch_task_run_batch_project
    is_task_path_passthrough = True

    def __init__(self, *args, **kwargs):
        """Initializes launch settings and removes retired launch controls.

        Args:
            *args: Base task positional arguments.
            **kwargs: Base task keyword arguments.
        """
        super().__init__(*args, **kwargs)
        for key in ("disabled_task_types", "project_timeout_minutes", "project_retries",
                    "launch_timeout_seconds", "heartbeat_timeout_seconds"):
            self.settings.pop(key, None)

    def get_default_settings(self):
        """Gets settings for scheduling and supervising child projects.

        Returns:
            dict: JSON-compatible defaults.
        """
        return {
            "source_mode": task_base.SOURCE_MODE_INCOMING,
            "output_mode": task_base.OUTPUT_MODE_PASSTHROUGH,
            "queue_mode": "Independent", "dependency_outcome": "Success",
            "not_before": "", "launch_deadline": "", "delay_seconds": 0,
            "failure_policy": "Continue", "ignore_self": True,
            "override_worker_count": False, "worker_count": 1,
            "override_timeout_minutes": False, "timeout_minutes": 0,
            "override_max_retries": False, "max_retries": 0,
            "show_tracker": True, "window_policy": "Close On Success",
            "logs_path": "{project-dir}/logs/child_projects",
            "empty_policy": "Warning", "maximum_depth": 4,
        }

    def validate(self, project):
        """Checks launch settings and scheduling placement.

        Args:
            project (BatchProcessorModel): Parent model.

        Returns:
            ValidationResult: Settings errors and warnings.
        """
        result = task_base.ValidationResult()
        for key, choices in (("queue_mode", projects.QUEUE_MODES),
                             ("dependency_outcome", projects.DEPENDENCY_OUTCOMES),
                             ("window_policy", projects.WINDOW_POLICIES),
                             ("failure_policy", projects.FAILURE_POLICIES),
                             ("empty_policy", ["Warning", "Failure"])):
            if self.settings.get(key) not in choices:
                result.add_error(f"Invalid child project setting: {key}.")
        try:
            start = projects.parse_start_time(self.settings.get("not_before"))
            deadline = projects.parse_start_time(self.settings.get("launch_deadline"))
            if start and deadline and deadline < start:
                result.add_error("Child project launch deadline precedes its scheduled start.")
        except (ValueError, TypeError) as error:
            result.add_error(str(error))
        for key in ("worker_count", "timeout_minutes", "max_retries", "delay_seconds", "maximum_depth"):
            try:
                minimum = 1 if key in ("worker_count", "maximum_depth") else 0
                if int(self.settings.get(key)) < minimum:
                    raise ValueError()
            except (ValueError, TypeError):
                result.add_error(f"Child project {key} must be an integer of at least {minimum}.")
        if not str(self.settings.get("logs_path") or "").strip():
            result.add_error("A child project log folder is required.")
        if project:
            for segment in project.get_task_segments():
                processing = [task for task in segment if task.enabled and not task.is_input_task]
                if self in processing and processing[0] is not self:
                    result.add_error("Run Batch Project must be the first processing task in its input segment.")
            if not project.run_settings.get("multi_instance"):
                result.add_error(
                    "Projects containing Run Batch Project must use multi-instance mode (one worker is allowed).")
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Rejects invalid and duplicate child project inputs before launching.

        Args:
            work_items (list): Incoming work items.
            project (BatchProcessorModel): Parent model.
            step_output_dir (str): Parent task output directory.
            context (dict, optional): Execution context.

        Returns:
            ValidationResult: File and recursion errors.
        """
        result = task_base.ValidationResult()
        seen = set()
        for item in work_items:
            try:
                if projects.is_ignored_project(item.current_path, self, project):
                    continue
                path = projects.canonical_path(item.current_path)
                if path in seen:
                    raise ValueError(f"Duplicate child project: {item.current_path}")
                seen.add(path)
                if not os.path.isfile(path) or os.path.splitext(path)[1].lower() != constants.Project.EXTENSION:
                    raise ValueError(f"Expected an existing .batch file: {path}")
                projects.get_ancestry(path, project.project_file_path, self.settings["maximum_depth"])
            except (ValueError, TypeError) as error:
                result.add_error(str(error))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Runs a child and returns the incoming project with result metadata.

        Args:
            work_item (WorkItem): Child .batch input.
            project (BatchProcessorModel): Parent model.
            step_output_dir (str): Parent task output directory.
            context (dict, optional): Tracker callbacks.

        Returns:
            WorkItem: Original input with child result metadata.
        """
        from gt.tools.batch_processor import batch_processor_project_service

        if projects.is_ignored_project(work_item.current_path, self, project):
            return work_item
        result = batch_processor_project_service.run_project(self, work_item, project, context or {})
        metadata = dict(work_item.metadata)
        metadata["child_project_result"] = result
        return task_base.WorkItem(work_item.source_path, work_item.current_path, metadata)
