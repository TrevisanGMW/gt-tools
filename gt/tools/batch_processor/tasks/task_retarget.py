"""
Batch Processor Retarget Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
import os


class TaskRetarget(task_base.BatchTask):
    """Task that retargets animation using a Retargeter definition."""

    task_type = constants.TaskType.RETARGET
    default_display_name = "Retarget"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_retarget"
    icon = "tool_retargeter"
    category = "Animation"
    category_icon = "root_animation"

    def get_default_settings(self):
        """Gets default retarget settings.

        Returns:
            dict: Default retarget settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "definition_path": "",
            "target_rig_path": "",
            "source_namespace": "source",
            "target_namespace": "target",
            "reference_rig": True,
            "delete_source": True,
            "delete_static_channels": True,
            "shortname_fallback": True,
            "bake_animation": True,
            "export_result": True,
            "output_extension": ".ma",
            "fbx_key_reducer": False,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates retarget settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        definition_path = self.get_resolved_definition_path(project)
        if not definition_path:
            result.add_error("Retarget definition path is required.")
        elif not os.path.isfile(definition_path):
            result.add_error("Retarget definition does not exist: {0}".format(definition_path))
        output_extension = self.get_output_extension()
        if output_extension not in [".ma", ".mb", ".fbx"]:
            result.add_error("Retarget output extension must be .ma, .mb, or .fbx.")
        if self.modifies_in_place() and self.settings.get("export_result", True):
            result.add_error("Retarget cannot modify source files in place. Use a target path instead.")
        target_rig_path = self.get_resolved_target_rig_path(project)
        if target_rig_path and not os.path.isfile(target_rig_path):
            result.add_error("Retarget target rig does not exist: {0}".format(target_rig_path))
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects output collisions before retargeting.

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
                    "Retarget output collision: {0} and {1} both map to {2}".format(
                        output_paths[key], work_item.current_path, output_path
                    )
                )
            output_paths[key] = work_item.current_path
            if os.path.exists(output_path) and not self.settings.get("overwrite", False):
                result.add_warning("Retarget output already exists and will be skipped: {0}".format(output_path))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Retargets a work item.

        Args:
            work_item (WorkItem): Source animation work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output folder.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Retargeted output work item.
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

        definition = self.load_definition(project=project, source_path=work_item.current_path)
        if self.settings.get("bake_animation", True):
            definition.retarget(verbose=False)
        else:
            definition.retarget_edit_mode(linked_mode=True)

        if not self.settings.get("export_result", True):
            return task_base.WorkItem(
                source_path=work_item.source_path,
                current_path=work_item.current_path,
                metadata=task_utils.build_metadata(self, work_item),
            )

        self.write_output(output_path)
        metadata = task_utils.build_metadata(self, work_item)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)

    def load_definition(self, project, source_path):
        """Loads and configures a retargeter definition.

        Args:
            project (BatchProcessorModel): Active project.
            source_path (str): Source animation path.

        Returns:
            RetargeterDefinition: Configured definition.
        """
        import gt.tools.retargeter.retargeter_model as retargeter_model

        definition_path = self.get_resolved_definition_path(project)
        model = retargeter_model.RetargeterModel()
        model.load_project_from_file(definition_path)
        definition = model.get_project()
        definition.set_source_path(source_path)
        target_rig_path = self.get_resolved_target_rig_path(project)
        if target_rig_path:
            definition.set_target_path(target_rig_path)
        if self.settings.get("source_namespace") is not None:
            definition.set_source_namespace(str(self.settings.get("source_namespace") or ""))
        if self.settings.get("target_namespace") is not None:
            definition.set_target_namespace(str(self.settings.get("target_namespace") or ""))
        definition.set_reference_rig_status(bool(self.settings.get("reference_rig", True)))
        definition.set_delete_source_status(bool(self.settings.get("delete_source", True)))
        definition.set_delete_static_channels_status(bool(self.settings.get("delete_static_channels", True)))
        definition.set_shortname_fallback_status(bool(self.settings.get("shortname_fallback", True)))
        return definition

    def write_output(self, output_path):
        """Writes the retargeted scene.

        Args:
            output_path (str): Destination file path.
        """
        output_extension = self.get_output_extension()
        if output_extension in [".ma", ".mb"]:
            batch_processor_maya.save_scene(output_path, batch_processor_maya.get_maya_file_type(output_path))
            return
        self.export_fbx(output_path)

    def export_fbx(self, output_path):
        """Exports the current scene to FBX.

        Args:
            output_path (str): Destination FBX path.
        """
        import gt.utils.fbx as utils_fbx

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.isdir(output_dir):
            os.makedirs(output_dir)
        with utils_fbx.FbxExporter(selection=False, key_reducer=bool(self.settings.get("fbx_key_reducer"))) as fbx:
            fbx.set_preferences_animation()
            fbx.export_file(path=output_path)

    def build_output_path(self, work_item, step_output_dir):
        """Builds the retarget output path.

        Args:
            work_item (WorkItem): Source work item.
            step_output_dir (str): Output directory.

        Returns:
            str: Output path.
        """
        return task_utils.build_output_path(work_item, step_output_dir, extension=self.get_output_extension())

    def get_output_extension(self):
        """Gets the normalized output extension.

        Returns:
            str: Output extension.
        """
        extension = str(self.settings.get("output_extension") or ".ma").lower()
        if not extension.startswith("."):
            extension = "." + extension
        return extension

    def get_resolved_definition_path(self, project):
        """Gets the resolved retarget definition path.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Resolved path.
        """
        definition_path = self.settings.get("definition_path") or ""
        return project.resolve_template_path(definition_path, task=self) if definition_path else ""

    def get_resolved_target_rig_path(self, project):
        """Gets the optional target rig override path.

        Args:
            project (BatchProcessorModel): Active project.

        Returns:
            str: Resolved target rig path.
        """
        target_rig_path = self.settings.get("target_rig_path") or ""
        return project.resolve_template_path(target_rig_path, task=self) if target_rig_path else ""


RetargetTask = TaskRetarget
