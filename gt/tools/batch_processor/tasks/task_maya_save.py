"""
Batch Processor Maya Save Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
import os


class TaskMayaSave(task_base.BatchTask):
    """Task that saves incoming work items as Maya scene files."""

    task_type = constants.TaskType.MAYA_SAVE
    default_display_name = "Save Maya File"
    default_target_path_template = "{project-dir}/{output-dir}"
    icon = "rigger_module_save_scene"
    category = "Outputs"
    category_icon = "rigger_module_save_scene"
    is_output_task = True

    def get_default_settings(self):
        """Gets default Maya save settings.

        Returns:
            dict: Default Maya save task settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "output_extension": ".ma",
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates Maya save settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        extension = self.get_output_extension()
        if extension not in [".ma", ".mb"]:
            result.add_error("Maya save output extension must be .ma or .mb.")
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects output collisions before saving files.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for this step.
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
                    "Maya save collision: {0} and {1} both map to {2}".format(
                        output_paths[key], work_item.current_path, output_path
                    )
            )
            output_paths[key] = work_item.current_path
            if self.modifies_in_place():
                current_extension = os.path.splitext(work_item.current_path)[1].lower()
                if current_extension not in [".ma", ".mb"]:
                    result.add_error(
                        "Maya save can only modify Maya scene files in place: {0}".format(work_item.current_path)
                    )
            output_exists = os.path.exists(output_path)
            can_overwrite = self.settings.get("overwrite", False)
            if output_exists and not self.modifies_in_place() and not can_overwrite:
                result.add_warning("Maya save output already exists and will be skipped: {0}".format(output_path))
        return result

    def get_output_extension(self):
        """Gets the normalized output extension.

        Returns:
            str: Output extension with leading dot.
        """
        extension = str(self.settings.get("output_extension") or ".ma").lower()
        if not extension.startswith("."):
            extension = "." + extension
        return extension

    def build_output_path(self, work_item, step_output_dir):
        """Builds the saved Maya scene path for a work item.

        Args:
            work_item (WorkItem): Work item to process.
            step_output_dir (str): Output folder for this step.

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

    def execute(self, work_item, project, step_output_dir, context=None):
        """Saves a work item as a Maya scene.

        Args:
            work_item (WorkItem): Work item to process.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for this step.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Updated work item pointing to the saved Maya file.
        """
        output_path = self.build_output_path(work_item, step_output_dir)
        if os.path.exists(output_path) and not self.modifies_in_place() and not self.settings.get("overwrite", False):
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

        load_relevant_plugins = self.settings.get("load_relevant_plugins", True)
        source_load_mode = self.get_source_load_mode()
        if source_load_mode == "Open":
            batch_processor_maya.open_scene(work_item.current_path, load_relevant_plugins=load_relevant_plugins)
        else:
            batch_processor_maya.new_scene()
            if os.path.isfile(work_item.current_path):
                batch_processor_maya.import_file(
                    work_item.current_path,
                    load_relevant_plugins=load_relevant_plugins,
                )

        batch_processor_maya.save_scene(output_path, file_type=batch_processor_maya.get_maya_file_type(output_path))
        metadata = dict(work_item.metadata)
        metadata["last_task_id"] = self.id
        metadata["last_task_type"] = self.task_type
        metadata["settings_hash"] = task_base.hash_settings(self.settings)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)

    def get_source_load_mode(self):
        """Gets the normalized source load mode.

        Returns:
            str: Either "Open" or "Import".
        """
        source_load_mode = self.settings.get("source_load_mode")
        if source_load_mode:
            return source_load_mode
        if self.settings.get("open_source_scene", True):
            return "Open"
        return "Import"


MayaSaveTask = TaskMayaSave
