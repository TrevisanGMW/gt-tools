"""
Batch Processor FBX Export Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
import os


FBX_EXPORT_MODE_ANIMATION = "Animation"
FBX_EXPORT_MODE_SKELETAL_MESH = "Skeletal Mesh"
FBX_EXPORT_MODE_MESH = "Mesh"
FBX_EXPORT_MODE_VALUES = [FBX_EXPORT_MODE_ANIMATION, FBX_EXPORT_MODE_SKELETAL_MESH, FBX_EXPORT_MODE_MESH]


class TaskExportFbx(task_base.BatchTask):
    """Task that exports incoming scenes or files to FBX."""

    task_type = constants.TaskType.FBX_EXPORT
    default_display_name = "FBX Export"
    default_target_path_template = "{project-dir}/{output-dir}"
    icon = "rigger_module_export_sk"
    category = "Outputs"
    category_icon = "rigger_module_export_sk"
    is_output_task = True

    def get_default_settings(self):
        """Gets default FBX export settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "export_mode": FBX_EXPORT_MODE_ANIMATION,
            "export_selection": False,
            "key_reducer": False,
            "auto_frame_range": True,
            "frame_start": "",
            "frame_end": "",
            "ascii": False,
            "generate_log": False,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates FBX export settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        if self.modifies_in_place():
            result.add_error("FBX export cannot modify source files in place. Use a target path instead.")
        if self.settings.get("export_mode") not in FBX_EXPORT_MODE_VALUES:
            result.add_error("FBX export mode must be Animation, Skeletal Mesh, or Mesh.")
        if not self.settings.get("auto_frame_range", True):
            self.validate_frame_value(result, self.settings.get("frame_start"), "start")
            self.validate_frame_value(result, self.settings.get("frame_end"), "end")
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects FBX output collisions.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output folder.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        output_paths = {}
        for work_item in work_items:
            output_path = self.build_output_path(work_item, step_output_dir)
            key = os.path.normcase(output_path)
            if key in output_paths:
                result.add_error(
                    "FBX export collision: {0} and {1} both map to {2}".format(
                        output_paths[key], work_item.current_path, output_path
                    )
                )
            output_paths[key] = work_item.current_path
            if os.path.exists(output_path) and not self.settings.get("overwrite", False):
                result.add_warning("FBX output already exists and will be skipped: {0}".format(output_path))
        return result

    def build_output_path(self, work_item, step_output_dir):
        """Builds an FBX output path.

        Args:
            work_item (WorkItem): Source work item.
            step_output_dir (str): Output folder.

        Returns:
            str: Output path.
        """
        return task_utils.build_output_path(work_item, step_output_dir, extension=".fbx")

    def execute(self, work_item, project, step_output_dir, context=None):
        """Exports a work item to FBX.

        Args:
            work_item (WorkItem): Work item to export.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output folder.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Output work item.
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

        task_utils.load_source_scene(
            work_item.current_path,
            source_load_mode=self.settings.get("source_load_mode") or "Open",
            load_relevant_plugins=self.settings.get("load_relevant_plugins", True),
        )
        self.export_fbx(output_path)
        metadata = task_utils.build_metadata(self, work_item)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)

    def export_fbx(self, output_path):
        """Exports the current Maya scene to FBX.

        Args:
            output_path (str): Destination FBX path.
        """
        import gt.utils.fbx as utils_fbx
        import maya.cmds as cmds

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        with utils_fbx.FbxExporter(
            selection=bool(self.settings.get("export_selection", False)),
            key_reducer=bool(self.settings.get("key_reducer", False)),
        ) as fbx_exporter:
            export_mode = self.settings.get("export_mode") or FBX_EXPORT_MODE_ANIMATION
            if export_mode == FBX_EXPORT_MODE_SKELETAL_MESH:
                fbx_exporter.set_preferences_skeletal_mesh()
            elif export_mode == FBX_EXPORT_MODE_MESH:
                fbx_exporter.set_preferences_mesh()
            else:
                frame_start = None
                frame_end = None
                if not self.settings.get("auto_frame_range", True):
                    frame_start = float(self.settings.get("frame_start"))
                    frame_end = float(self.settings.get("frame_end"))
                fbx_exporter.set_preferences_animation(start_frame=frame_start, end_frame=frame_end)
            cmds.FBXExportInAscii("-v", bool(self.settings.get("ascii", False)))
            cmds.FBXExportGenerateLog("-v", bool(self.settings.get("generate_log", False)))
            fbx_exporter.export_file(path=output_path)

    @staticmethod
    def validate_frame_value(result, value, label):
        """Validates a frame value.

        Args:
            result (ValidationResult): Result to update.
            value (object): Frame value.
            label (str): Frame label.
        """
        if value in [None, ""]:
            result.add_error("FBX export {0} frame cannot be empty.".format(label))
            return
        try:
            float(value)
        except (TypeError, ValueError):
            result.add_error("FBX export {0} frame must be numeric: {1}".format(label, value))


FbxExportTask = TaskExportFbx
