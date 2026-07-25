"""
Batch Processor USD Export Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
import gt.utils.usd as utils_usd
import os


class TaskExportUsd(task_base.BatchTask):
    """Task that exports incoming Maya scenes as USD files."""

    task_type = constants.TaskType.USD_EXPORT
    default_display_name = "USD Export"
    default_target_path_template = "{project-dir}/{output-dir}"
    icon = ui_res_lib.Icon.rigger_module_export_sk
    category = "Outputs"
    category_icon = ui_res_lib.Icon.rigger_module_export_sk
    is_output_task = True

    def get_default_settings(self):
        """Gets default USD export settings.

        Returns:
            dict: Default USD export settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "output_extension": ".usd",
            "usd_format": "USD",
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "export_selection": True,
            "static_export": False,
            "animation": True,
            "auto_frame_range": True,
            "frame_start": "",
            "frame_end": "",
            "auto_detect_roots": True,
            "target_roots": [],
            "target_node": "",
            "include_joints": True,
            "include_locators": True,
            "include_curves": True,
            "force_z_up": False,
            "zero_root_rotation": False,
            "materials": False,
            "skeletons": True,
            "skin": True,
            "blend_shapes": True,
            "color_sets": False,
            "uvs": False,
            "visibility": True,
            "strip_namespaces": False,
            "merge_transform_and_shape": False,
            "write_defaults": True,
            "ignore_warnings": True,
            "native_custom_attributes": [],
            "custom_data_attributes": [],
            "overwrite": False,
        }

    def validate(self, project):
        """Validates USD export settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        extension = self.get_output_extension()
        if extension not in [".usd", ".usda", ".usdc"]:
            result.add_error("USD export extension must be .usd, .usda, or .usdc.")
        raw_usd_format = str(self.settings.get("usd_format") or "").lower().strip(".")
        if raw_usd_format and raw_usd_format not in ["usd", "usda", "usdc"]:
            result.add_error("USD format must be USD, USDA, or USDC.")
        if self.modifies_in_place():
            result.add_error("USD export cannot modify source files in place. Use a target path instead.")
        if not self.settings.get("auto_frame_range", True):
            self.validate_frame_value(result, self.settings.get("frame_start"), "start")
            self.validate_frame_value(result, self.settings.get("frame_end"), "end")
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects output collisions before exporting USD files.

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
                    "USD export collision: {0} and {1} both map to {2}".format(
                        output_paths[key], work_item.current_path, output_path
                    )
                )
            output_paths[key] = work_item.current_path
            if os.path.exists(output_path) and not self.settings.get("overwrite", False):
                result.add_warning("USD export output already exists and will be skipped: {0}".format(output_path))
        return result

    def get_output_extension(self):
        """Gets the normalized USD output extension.

        Returns:
            str: Output extension with leading dot.
        """
        usd_format = self.get_usd_format()
        return "." + usd_format

    def get_usd_format(self):
        """Gets the normalized visible USD format.

        Returns:
            str: `usd`, `usda`, or `usdc`.
        """
        usd_format = str(self.settings.get("usd_format") or "").lower().strip(".")
        extension = utils_usd.normalize_usd_extension(self.settings.get("output_extension") or ".usd").strip(".")
        if extension in ["usda", "usdc"] and usd_format == "usd":
            return extension
        if usd_format in ["usd", "usda", "usdc"]:
            return usd_format
        return extension

    def build_output_path(self, work_item, step_output_dir):
        """Builds the USD output path for a work item.

        Args:
            work_item (WorkItem): Work item to process.
            step_output_dir (str): Output folder for this task.

        Returns:
            str: Resolved output path.
        """
        base_name = os.path.splitext(os.path.basename(work_item.current_path))[0]
        file_name = task_base.sanitize_filename(base_name, "scene") + self.get_output_extension()
        return task_base.build_work_item_output_path(
            work_item=work_item,
            output_dir=step_output_dir,
            file_name=file_name,
        )

    def execute(self, work_item, project, step_output_dir, context=None):
        """Exports a work item as a USD file.

        Args:
            work_item (WorkItem): Work item to process.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for this task.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Updated work item pointing to the USD file.
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

        self.load_source_scene(work_item.current_path)
        utils_usd.export_scene_to_usd(output_path=output_path, settings=self.settings)
        metadata = dict(work_item.metadata)
        metadata["last_task_id"] = self.id
        metadata["last_task_type"] = self.task_type
        metadata["settings_hash"] = task_base.hash_settings(self.settings)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)

    def load_source_scene(self, source_path):
        """Loads the source file into Maya for export.

        Args:
            source_path (str): Source file path.
        """
        load_relevant_plugins = self.settings.get("load_relevant_plugins", True)
        source_load_mode = self.get_source_load_mode()
        if source_load_mode == "Open" and os.path.splitext(source_path)[1].lower() in [".ma", ".mb", ".fbx"]:
            batch_processor_maya.open_scene(source_path, load_relevant_plugins=load_relevant_plugins)
            return
        batch_processor_maya.new_scene()
        if os.path.isfile(source_path):
            batch_processor_maya.import_file(source_path, load_relevant_plugins=load_relevant_plugins)

    def get_source_load_mode(self):
        """Gets the normalized source load mode.

        Returns:
            str: Either "Open" or "Import".
        """
        source_load_mode = self.settings.get("source_load_mode")
        if source_load_mode in ["Open", "Import"]:
            return source_load_mode
        return "Open"

    @staticmethod
    def validate_frame_value(result, value, label):
        """Validates a user-provided frame value.

        Args:
            result (ValidationResult): Result object to update.
            value (object): Frame value.
            label (str): Frame label for messages.
        """
        if value in [None, ""]:
            result.add_error(
                "USD export {0} frame cannot be empty when automatic frame range is disabled.".format(label)
            )
            return
        try:
            float(value)
        except (TypeError, ValueError):
            result.add_error("USD export {0} frame must be numeric: {1}".format(label, value))
