"""
Batch Processor Auto Rig Build Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
import os


class TaskAutoRigBuild(task_base.BatchTask):
    """Task that builds Auto Rigger project files."""

    task_type = constants.TaskType.AUTO_RIG_BUILD
    default_display_name = "Build Auto Rig"
    default_target_path_template = "{project-dir}/{output-dir}"
    icon = "tool_auto_rigger"
    category = "Rigging"
    category_icon = "root_biped"

    def get_default_settings(self):
        """Gets default Auto Rig build settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "output_extension": ".ma",
            "force_disable_modules": ["ModuleSaveScene", "ModuleExportSkeletalMesh"],
            "optimized_proxy": True,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates Auto Rig build settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        extension = self.get_output_extension()
        if extension not in [".ma", ".mb"]:
            result.add_error("Auto Rig build output extension must be .ma or .mb.")
        if self.modifies_in_place():
            result.add_error("Auto Rig build cannot modify source project files in place. Use a target path.")
        for module_name in self.settings.get("force_disable_modules") or []:
            if not self.module_name_exists(module_name):
                result.add_warning("Force-disabled Auto Rigger module is not known: {0}".format(module_name))
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects output collisions before building rigs.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        output_paths = {}
        for work_item in work_items:
            if not os.path.isfile(work_item.current_path):
                result.add_error("Auto Rig project file does not exist: {0}".format(work_item.current_path))
                continue
            output_path = self.build_output_path(work_item, step_output_dir)
            key = os.path.normcase(output_path)
            if key in output_paths:
                result.add_error(
                    "Auto Rig build output collision: {0} and {1} both map to {2}".format(
                        output_paths[key], work_item.current_path, output_path
                    )
                )
            output_paths[key] = work_item.current_path
            if os.path.exists(output_path) and not self.settings.get("overwrite", False):
                result.add_warning("Auto Rig build output already exists and will be skipped: {0}".format(output_path))
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Builds one Auto Rigger project file.

        Args:
            work_item (WorkItem): Work item pointing to a rig project.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output folder.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Built Maya scene work item.
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

        import gt.tools.auto_rigger.rigger_model as rigger_model

        batch_processor_maya.new_scene()
        model = rigger_model.RiggerModel()
        model.load_project_from_file(work_item.current_path)
        rig_project = model.get_project()
        self.force_disable_project_modules(rig_project)
        rig_project.build_proxy(optimized=bool(self.settings.get("optimized_proxy", True)))
        rig_project.build_rig()
        batch_processor_maya.save_scene(output_path, batch_processor_maya.get_maya_file_type(output_path))
        metadata = task_utils.build_metadata(self, work_item)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)

    def force_disable_project_modules(self, rig_project):
        """Disables configured module classes in a rig project.

        Args:
            rig_project (RigProject): Auto Rigger project.

        Returns:
            list: Disabled module names.
        """
        disabled = []
        disabled_names = set([str(name).strip() for name in self.settings.get("force_disable_modules") or []])
        disabled_names = set([name for name in disabled_names if name])
        for module in rig_project.get_modules():
            class_name = module.get_module_class_name(remove_module_prefix=False)
            short_name = module.get_module_class_name(remove_module_prefix=True)
            formatted_name = module.get_module_class_name(remove_module_prefix=True, formatted=True)
            if class_name in disabled_names or short_name in disabled_names or formatted_name in disabled_names:
                module.set_active_state(False)
                disabled.append(class_name)
        return disabled

    def build_output_path(self, work_item, step_output_dir):
        """Builds the built-rig scene output path.

        Args:
            work_item (WorkItem): Rig project work item.
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

    @staticmethod
    def module_name_exists(module_name):
        """Checks whether an Auto Rigger module class name exists.

        Args:
            module_name (str): Module name to inspect.

        Returns:
            bool: True when the module name matches a known module.
        """
        try:
            from gt.tools.auto_rigger.rig_modules import RigModules

            available_modules = RigModules.get_modules_dict()
            available_names = set(available_modules.keys())
            for module_class in available_modules.values():
                available_names.add(module_class.__name__)
                if module_class.__name__.startswith("Module"):
                    available_names.add(module_class.__name__[len("Module"):])
            return str(module_name or "").strip() in available_names
        except Exception:
            return True


AutoRigBuildTask = TaskAutoRigBuild
