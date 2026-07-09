"""
Batch Processor Rename Task
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as task_base
import os
import shutil


class TaskRename(task_base.BatchTask):
    """Task that copies work items to renamed cooked outputs."""

    task_type = constants.TaskType.RENAME
    default_display_name = "Rename"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx}_rename"
    icon = "tool_renamer"
    category = "Utilities"
    category_icon = "root_utilities"
    allowed_tokens = set(["name", "ext", "index", "task-name", "step", "date"])

    def get_default_settings(self):
        """Gets default rename settings.

        Returns:
            dict: Default rename task settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "name_template": "{name}",
            "pattern": "{name}_{index}",
            "use_prefix": False,
            "prefix": "",
            "use_suffix": False,
            "suffix": "",
            "use_search_replace": False,
            "search_text": "",
            "replace_text": "",
            "use_index": False,
            "index_separator": "_",
            "padding": 3,
            "preserve_extension": True,
            "overwrite": False,
        }

    def validate(self, project):
        """Validates rename settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        allowed_tokens = set(self.allowed_tokens)
        if project:
            allowed_tokens.update(project.get_environment_variables(task=self, include_braces=False).keys())
        result = task_base.validate_format_tokens(self.get_name_template(), allowed_tokens)
        if result.errors:
            result.errors = ["Rename {0}".format(error[0].lower() + error[1:]) for error in result.errors]
        if self.settings.get("use_search_replace") and not self.settings.get("search_text"):
            result.add_error("Rename search text cannot be empty when search replace is enabled.")
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Detects rename collisions before writing files.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Cooked output folder for this step.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        output_paths = {}
        context = context or {}
        context_index = context.get("item_index")
        try:
            context_index = int(context_index) if context_index else None
        except (TypeError, ValueError):
            context_index = None
        for index, work_item in enumerate(work_items, 1):
            item_index = index
            if context_index is not None:
                item_index = context_index + index - 1
            output_path = self.build_output_path(work_item, item_index, step_output_dir, project=project)
            key = os.path.normcase(output_path)
            if key in output_paths:
                result.add_error(
                    "Rename collision: {0} and {1} both map to {2}".format(
                        output_paths[key], work_item.current_path, output_path
                    )
                )
            output_paths[key] = work_item.current_path
            same_path = os.path.normcase(output_path) == os.path.normcase(work_item.current_path)
            if os.path.exists(output_path) and not same_path and not self.settings.get("overwrite", False):
                result.add_warning("Rename output already exists and will be skipped: {0}".format(output_path))
        return result

    def get_name_template(self):
        """Gets the active name template.

        Returns:
            str: Name template string.
        """
        name_template = self.settings.get("name_template")
        legacy_pattern = self.settings.get("pattern")
        if legacy_pattern and (not name_template or name_template == "{name}") and legacy_pattern != "{name}_{index}":
            return legacy_pattern
        return name_template or legacy_pattern or "{name}"

    def build_output_path(self, work_item, index, step_output_dir, project=None):
        """Builds the cooked output path for a work item.

        Args:
            work_item (WorkItem): Work item to rename.
            index (int): One-based work item index.
            step_output_dir (str): Cooked output folder for this step.
            project (BatchProcessorModel, optional): Active project model.

        Returns:
            str: Resolved output path for the renamed item.
        """
        source_name = os.path.basename(work_item.current_path)
        base_name, extension = os.path.splitext(source_name)
        extension = extension.lstrip(".")
        padding = int(self.settings.get("padding") or 0)
        index_value = str(index).zfill(padding) if padding > 0 else str(index)
        token_data = {
            "name": base_name,
            "ext": extension,
            "index": index_value,
            "task-name": task_base.sanitize_filename(self.display_name, "task"),
            "step": task_base.sanitize_filename(self.display_name, "step"),
            "date": task_base.get_today_token(),
        }
        render_template = self.get_name_template()
        if project:
            render_template = project.resolve_template(render_template, task=self)
            token_data.update(project.get_environment_variables(task=self, include_braces=False))
        rendered = render_template.format(**token_data)
        if self.settings.get("use_search_replace"):
            rendered = rendered.replace(
                self.settings.get("search_text") or "",
                self.settings.get("replace_text") or "",
            )
        if self.settings.get("use_prefix"):
            prefix = self.settings.get("prefix") or ""
            if project:
                prefix = project.resolve_template(prefix, task=self)
            rendered = prefix + rendered
        if self.settings.get("use_suffix"):
            suffix = self.settings.get("suffix") or ""
            if project:
                suffix = project.resolve_template(suffix, task=self)
            rendered = rendered + suffix
        if self.settings.get("use_index"):
            separator = self.settings.get("index_separator") or ""
            rendered = "{0}{1}{2}".format(rendered, separator, index_value)
        rendered = task_base.sanitize_filename(rendered, "renamed")
        if self.settings.get("preserve_extension", True):
            rendered_base, rendered_ext = os.path.splitext(rendered)
            if not rendered_ext and extension:
                rendered = "{0}.{1}".format(rendered_base or rendered, extension)
        if self.modifies_in_place():
            output_dir = os.path.dirname(work_item.current_path)
        else:
            output_dir = task_base.get_output_dir_for_work_item(work_item=work_item, output_dir=step_output_dir)
        return task_base.normalize_path(os.path.join(output_dir, rendered))

    def execute(self, work_item, project, step_output_dir, context=None):
        """Copies a work item into this step's cooked folder with a new name.

        Args:
            work_item (WorkItem): Work item to process.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Cooked output folder for this step.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Updated work item pointing to the cooked output file.
        """
        context = context or {}
        index = context.get("item_index", 1)
        output_path = self.build_output_path(work_item, index, step_output_dir, project=project)
        same_path = os.path.normcase(output_path) == os.path.normcase(work_item.current_path)
        if os.path.exists(output_path) and not same_path and not self.settings.get("overwrite", False):
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
        if not self.modifies_in_place():
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.isdir(output_dir):
                os.makedirs(output_dir)
        if self.modifies_in_place():
            if not same_path:
                shutil.move(work_item.current_path, output_path)
        else:
            shutil.copy2(work_item.current_path, output_path)
        metadata = dict(work_item.metadata)
        metadata["last_task_id"] = self.id
        metadata["last_task_type"] = self.task_type
        metadata["settings_hash"] = task_base.hash_settings(self.settings)
        return task_base.WorkItem(source_path=work_item.source_path, current_path=output_path, metadata=metadata)


RenameTask = TaskRename
