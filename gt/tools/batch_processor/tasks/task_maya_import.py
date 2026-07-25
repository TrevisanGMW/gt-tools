"""
Batch Processor Maya Import Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tasks import task_utils
import os


DEFAULT_POST_SCRIPT_TEXT = """# Optional Import/Open Maya cleanup pass.
# Available values:
#   context / batch_context: Full runtime dictionary.
#   arguments / args: input, output, project, project_dir, task, task_id, etc.
#   environment_variables / env: Project environment variables.
#   project, task, work_item, output_path, imported_nodes.
import pprint
import sys
import maya.cmds as cmds

sys.stdout.write("Import/Open Maya post script\\n")
sys.stdout.write("Input: {0}\\n".format(args.get("input") or context.get("source_path")))
sys.stdout.write("Output: {0}\\n".format(args.get("output") or output_path))
sys.stdout.write("Arguments:\\n")
pprint.pprint(arguments)
sys.stdout.write("Environment Variables:\\n")
pprint.pprint(environment_variables)
"""


class TaskMayaImport(task_base.BatchTask):
    """Task that opens or imports incoming files in Maya with optional scene output."""

    task_type = constants.TaskType.MAYA_IMPORT
    default_display_name = "Import/Open Maya"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_import_maya"
    icon = ui_res_lib.Icon.rigger_module_import_file
    category = "Inputs"
    category_icon = ui_res_lib.Icon.rigger_module_import_file
    def get_default_settings(self):
        """Gets default Maya import settings.

        Returns:
            dict: Default Maya import task settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "scene_load_mode": "Import",
            "output_extension": ".ma",
            "namespace": "",
            "clear_scene": True,
            "load_relevant_plugins": True,
            "set_framerate": False,
            "framerate": 30,
            "set_scene_scale": False,
            "scene_scale": "cm",
            "set_scene_up_axis": False,
            "scene_up_axis": "Y",
            "run_post_script": False,
            "post_script_text": DEFAULT_POST_SCRIPT_TEXT,
            "post_script_collapsed": True,
            "post_script_font_size": 14,
            "post_script_pass_standard_arguments": True,
            "post_script_pass_environment_arguments": True,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates Maya import settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        extension = self.get_output_extension()
        if not self.passes_through() and extension not in [".ma", ".mb"]:
            result.add_error("Maya import output extension must be .ma or .mb.")
        if self.settings.get("set_framerate"):
            try:
                framerate = int(float(self.settings.get("framerate")))
                if framerate < 1:
                    result.add_error("Maya import framerate must be greater than zero.")
            except (TypeError, ValueError):
                result.add_error("Maya import framerate must be numeric.")
        if self.settings.get("set_scene_scale"):
            scene_scale = str(self.settings.get("scene_scale") or "").lower()
            if scene_scale not in ["mm", "cm", "m", "in", "ft", "yd"]:
                result.add_error("Maya import scene scale must be one of: mm, cm, m, in, ft, yd.")
        if self.settings.get("set_scene_up_axis"):
            scene_up_axis = str(self.settings.get("scene_up_axis") or "").upper()
            if scene_up_axis not in ["Y", "Z"]:
                result.add_error("Maya import scene up axis must be Y or Z.")
        post_script_text = self.settings.get("post_script_text")
        if post_script_text is None:
            post_script_text = DEFAULT_POST_SCRIPT_TEXT
        if self.settings.get("run_post_script") and not post_script_text:
            result.add_error("Import/Open Maya post script is enabled but no inline script is set.")
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects output collisions before importing files.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Cooked output folder for this step.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        if self.passes_through():
            return result
        output_paths = {}
        for work_item in work_items:
            output_path = self.build_output_path(work_item, step_output_dir)
            key = os.path.normcase(output_path)
            if key in output_paths:
                result.add_error(
                    "Maya import collision: {0} and {1} both map to {2}".format(
                        output_paths[key], work_item.current_path, output_path
                    )
                )
            output_paths[key] = work_item.current_path
            if self.modifies_in_place() and os.path.splitext(work_item.current_path)[1].lower() not in [".ma", ".mb"]:
                result.add_error(
                    "Maya import/open can only modify Maya scene files in place: {0}".format(work_item.current_path)
                )
            output_exists = os.path.exists(output_path)
            can_overwrite = self.settings.get("overwrite", False)
            if output_exists and not self.modifies_in_place() and not can_overwrite:
                result.add_warning("Maya import output already exists and will be skipped: {0}".format(output_path))
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
        """Builds the cooked Maya scene path for a work item.

        Args:
            work_item (WorkItem): Work item to process.
            step_output_dir (str): Cooked output folder for this step.

        Returns:
            str: Resolved output path.
        """
        base_name = os.path.splitext(os.path.basename(work_item.current_path))[0]
        if self.modifies_in_place() or self.passes_through():
            return work_item.current_path
        file_name = task_base.sanitize_filename(base_name, "imported") + self.get_output_extension()
        return task_base.build_work_item_output_path(
            work_item=work_item,
            output_dir=step_output_dir,
            file_name=file_name,
        )

    def execute(self, work_item, project, step_output_dir, context=None):
        """Imports a work item into Maya and saves a cooked Maya scene.

        Args:
            work_item (WorkItem): Work item to process.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Cooked output folder for this step.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Updated work item pointing to the cooked Maya scene.
        """
        output_path = self.build_output_path(work_item, step_output_dir)
        if os.path.exists(output_path) and self.writes_to_target_path() and not self.settings.get("overwrite", False):
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
        if self.settings.get("load_fbx_plugin", False):
            load_relevant_plugins = True
        load_mode = "Open" if self.passes_through() else self.settings.get("scene_load_mode") or "Import"
        imported_nodes = []
        if load_mode == "Open":
            batch_processor_maya.open_scene(work_item.current_path, load_relevant_plugins=load_relevant_plugins)
        elif self.settings.get("clear_scene", True):
            batch_processor_maya.new_scene()
        if load_mode != "Open":
            imported_nodes = batch_processor_maya.import_file(
                file_path=work_item.current_path,
                namespace=self.settings.get("namespace") or None,
                load_relevant_plugins=load_relevant_plugins,
            )
        batch_processor_maya.apply_scene_options(self.settings)
        self.run_post_script_if_needed(
            project=project,
            work_item=work_item,
            output_path=output_path,
            imported_nodes=imported_nodes,
            context=context,
        )
        if not self.passes_through():
            batch_processor_maya.save_scene(
                output_path,
                file_type=batch_processor_maya.get_maya_file_type(output_path),
            )
        metadata = dict(work_item.metadata)
        metadata["last_task_id"] = self.id
        metadata["last_task_type"] = self.task_type
        metadata["settings_hash"] = task_base.hash_settings(self.settings)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)

    def run_post_script_if_needed(self, project, work_item, output_path, imported_nodes, context=None):
        """Runs the optional post-import Python cleanup script.

        Args:
            project (BatchProcessorModel): Active project model.
            work_item (WorkItem): Work item being processed.
            output_path (str): Output scene path.
            imported_nodes (list): Nodes imported by this task.
            context (dict, optional): Runtime context.
        """
        if not self.settings.get("run_post_script"):
            return
        script_text = self.settings.get("post_script_text")
        if script_text is None:
            script_text = DEFAULT_POST_SCRIPT_TEXT
        if not script_text.strip():
            return
        runtime_context = task_utils.build_python_script_runtime_context(
            project=project,
            task=self,
            work_item=work_item,
            output_path=output_path,
            context=context,
            extra_values={
                "project": project,
                "task": self,
                "work_item": work_item,
                "output_path": output_path,
                "imported_nodes": list(imported_nodes or []),
            },
            pass_standard_arguments=self.settings.get("post_script_pass_standard_arguments", True),
            pass_environment_arguments=self.settings.get("post_script_pass_environment_arguments", True),
        )
        task_utils.run_inline_python_script(
            script_text=script_text,
            context=runtime_context,
            script_name="<maya_import_post_script>",
        )
