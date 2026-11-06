"""
Batch Processor Settings Override Task

Control task that changes multi-instance run settings (max workers, retries,
timeout, preferred Maya version) at segment barriers. It never executes inside
worker jobs; the tracker applies its overrides when the segment it belongs to
starts.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_run_settings as run_settings
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib


class TaskSettingsOverride(task_base.BatchTask):
    """Task that overrides run settings for the following segments."""

    task_type = constants.TaskType.SETTINGS_OVERRIDE
    default_display_name = "Settings Override"
    icon = ui_res_lib.Icon.batch_task_settings_override
    category = "Utilities"
    category_icon = ui_res_lib.Icon.root_utilities
    is_settings_override_task = True
    is_indexless_task = True
    is_aggregate_task = True
    is_task_path_passthrough = True

    def get_default_settings(self):
        """Gets default Settings Override task settings.

        Every override starts disabled so a new task changes nothing until the
        user opts into specific values.

        Returns:
            dict: Default settings.
        """
        settings = super().get_default_settings()
        settings.update(
            {
                "override_worker_count": False,
                "worker_count": 4,
                "override_max_retries": False,
                "max_retries": 0,
                "override_timeout_minutes": False,
                "timeout_minutes": 0,
                "override_preferred_maya_version": False,
                "preferred_maya_version": "",
            }
        )
        return settings

    def uses_incoming_files(self):
        """Keeps incoming work items untouched.

        Returns:
            bool: Always True because this task never discovers source files.
        """
        return True

    def writes_to_target_path(self):
        """Prevents validation of the hidden target path.

        Returns:
            bool: Always False because this task produces no files.
        """
        return False

    def get_overrides(self):
        """Gets the enabled run settings overrides.

        Returns:
            dict: Normalized override values keyed by run setting key.
        """
        return run_settings.build_overrides_from_task_settings(self.settings)

    def validate(self, project):
        """Validates the run settings overrides and the task placement.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        overrides = self.get_overrides()
        if not overrides:
            result.add_warning(f'Task "{self.display_name}" has no overrides enabled, so it changes nothing.')
            return result
        if project is None:
            return result
        if not project.run_settings.get("multi_instance"):
            result.add_warning(
                f'Task "{self.display_name}" only affects multi-instance runs; '
                "it is ignored in single-instance mode."
            )
        maya_version = overrides.get(run_settings.PREFERRED_MAYA_VERSION)
        if maya_version and not self._is_maya_version_available(maya_version):
            result.add_warning(
                f'Task "{self.display_name}" Maya version "{maya_version}" was not found in default '
                "Autodesk install locations; the current mayapy will be kept."
            )
        if self.enabled and self in run_settings.find_mid_segment_tasks(project.get_task_segments()):
            result.add_warning(
                f'Task "{self.display_name}" is placed after a processing task in its segment. Settings '
                "cannot change mid-segment, so it takes effect when the next segment starts. Add a "
                "\"Start New Segment\" input above it to change settings between tasks."
            )
        return result

    @staticmethod
    def _is_maya_version_available(maya_version):
        """Checks whether a mayapy executable exists for a Maya version.

        Args:
            maya_version (str): Maya version, such as "2025".

        Returns:
            bool: True when found, or when the lookup itself is unavailable.
        """
        try:
            from gt.tools.batch_processor.batch_processor_worker import find_mayapy_for_version
        except Exception:
            return True
        try:
            return bool(find_mayapy_for_version(maya_version))
        except Exception:
            return True

    def execute(self, work_item, project, step_output_dir, context=None):
        """Passes incoming work items through unchanged.

        Run settings are applied by the tracker at segment barriers, so this
        method only exists as a safe no-op for code paths that execute tasks
        generically.

        Args:
            work_item (WorkItem): Unused aggregate work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Unused output folder.
            context (dict, optional): Runtime context containing work_items.

        Returns:
            list: Incoming work items.
        """
        context = context or {}
        return list(context.get("work_items") or [])
