"""
Batch Processor Input Metadata Task

Attaches up to five user-defined text values to incoming work items without
opening, writing, or filtering any file. Downstream tasks read the values
through {input-meta-<number>} / {input-meta-<name>} variables, the Python
task environment, or work_item.metadata["input_metadata"].
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_input_metadata as input_metadata
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib


class TaskInputMetadata(task_base.BatchTask):
    """Pass-through task that attaches per-input metadata values."""

    task_type = constants.TaskType.INPUT_METADATA
    default_display_name = "Input Metadata"
    icon = ui_res_lib.Icon.batch_task_input_metadata
    category = "Inputs"
    category_icon = ui_res_lib.Icon.batch_category_inputs
    is_indexless_task = True
    is_task_path_passthrough = True

    def get_default_settings(self):
        """Gets default Input Metadata settings.

        Returns:
            dict: One active unnamed slot and no rows.
        """
        settings = super().get_default_settings()
        settings.update(source_mode=task_base.SOURCE_MODE_INCOMING, output_mode=task_base.OUTPUT_MODE_PASSTHROUGH)
        settings.update(slot_count=1, slot_names=[""] * input_metadata.MAX_SLOTS, metadata_rows=[])
        return settings

    def _normalize_common_settings(self, incoming_settings=None):
        """Pads slot names and gives every row an ID, keeping malformed rows for validation.

        Args:
            incoming_settings (dict, optional): Raw task settings.
        """
        super()._normalize_common_settings(incoming_settings=incoming_settings)
        self.settings["slot_names"] = input_metadata.pad_values(self.settings.get("slot_names"))
        rows = self.settings.get("metadata_rows")
        if isinstance(rows, list):
            self.settings["metadata_rows"] = [
                input_metadata.normalize_row(row) if isinstance(row, dict) else row for row in rows
            ]

    def uses_incoming_files(self):
        """Always works on incoming items.

        Returns:
            bool: Always True.
        """
        return True

    def writes_to_target_path(self):
        """Prevents target path creation and validation.

        Returns:
            bool: Always False because this task writes no files.
        """
        return False

    def get_slot_count(self):
        """Gets the active slot count.

        Returns:
            int: Number of active slots.
        """
        return input_metadata.get_slot_count(self.settings)

    def get_slot_names(self):
        """Gets cleaned slot names.

        Returns:
            list: MAX_SLOTS cleaned names.
        """
        return input_metadata.get_slot_names(self.settings)

    def get_rows(self):
        """Gets complete copies of the stored rows.

        Returns:
            list: Row dictionaries in table order.

        Raises:
            ValueError: If the stored rows are malformed.
        """
        rows = self.settings.get("metadata_rows", [])
        input_metadata.validate_rows(rows)
        return [input_metadata.normalize_row(row) for row in rows]

    def set_rows(self, rows):
        """Validates and stores rows.

        Args:
            rows (list): Row dictionaries in table order.
        """
        input_metadata.validate_rows(rows)
        self.settings["metadata_rows"] = [input_metadata.normalize_row(row) for row in rows]

    def get_variable_names(self):
        """Gets the variables each active slot provides, for help text and previews.

        Returns:
            list: One list of braced variable names per active slot.
        """
        names = self.get_slot_names()
        prefix = input_metadata.VARIABLE_PREFIX
        return [[f"{{{prefix}{key}}}" for key in input_metadata.get_slot_keys(index, names[index])]
                for index in range(self.get_slot_count())]

    def resolve_item(self, work_item):
        """Resolves the values this task attaches to one work item.

        Args:
            work_item (WorkItem): Incoming item.

        Returns:
            tuple: Slot values by zero-based index (dict) and matched row IDs (list).
        """
        identities = input_metadata.get_item_identities(
            relative_path=task_base.get_work_item_relative_path(work_item),
            source_path=work_item.source_path,
            input_file=(work_item.metadata or {}).get("input_file", ""),
        )
        return input_metadata.resolve_values(self.get_rows(), self.get_slot_count(), identities)

    def get_upstream_input_items(self, project):
        """Discovers the items produced by enabled input tasks above this task in its segment.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            list: Work items in discovery order; empty when the task is disabled or has no inputs.
        """
        for segment in project.get_task_segments():
            if self not in segment:
                continue
            items = []
            for task in segment[:segment.index(self)]:
                if getattr(task, "is_input_task", False):
                    items.extend(task.prepare(project))
            return items
        return []

    def get_unmatched_rows(self, work_items):
        """Gets active rows that match none of the given items.

        Args:
            work_items (list): Items to test.

        Returns:
            list: Unmatched row dictionaries.
        """
        matched_ids = set()
        for work_item in work_items:
            matched_ids.update(self.resolve_item(work_item)[1])
        return [row for row in self.get_rows()
                if row["enabled"] and row["input"].strip() and row["id"] not in matched_ids]

    def validate(self, project):
        """Validates slot names and rows, and warns about rows no current input matches.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Errors for unusable settings, warnings for no-op or unmatched rows.
        """
        result = task_base.ValidationResult()
        errors = input_metadata.get_settings_errors(self.settings)
        for error in errors:
            result.add_error(f'Task "{self.display_name}": {error}')
        if errors:
            return result
        if not any(row["enabled"] and row["input"].strip() for row in self.get_rows()):
            result.add_warning(
                f'Task "{self.display_name}" has no active rows; items pass through with empty values.'
            )
            return result
        if project is None:
            return result
        try:
            work_items = self.get_upstream_input_items(project)
        except Exception:
            return result
        if not work_items:
            return result
        unmatched = [row["input"] for row in self.get_unmatched_rows(work_items)]
        if unmatched:
            preview = ", ".join(unmatched[:5]) + (", ..." if len(unmatched) > 5 else "")
            result.add_warning(
                f'Task "{self.display_name}": {len(unmatched)} row(s) match no current input: {preview}'
            )
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Checks settings before items run.

        Unmatched rows are reported by validate() against all inputs, because a
        multi-instance job only receives its own item.

        Args:
            work_items (list): Incoming items.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Unused output folder.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Settings errors only.
        """
        result = task_base.ValidationResult()
        for error in input_metadata.get_settings_errors(self.settings):
            result.add_error(f'Task "{self.display_name}": {error}')
        return result

    def execute(self, work_item, project, step_output_dir, context=None):
        """Returns a copy of the item with this task's values attached.

        Args:
            work_item (WorkItem): Incoming item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Unused output folder.
            context (dict, optional): Runtime context with an optional report_message callback.

        Returns:
            WorkItem: Same paths with updated input metadata.
        """
        values, matched_row_ids = self.resolve_item(work_item)
        metadata = dict(work_item.metadata or {})
        metadata[input_metadata.METADATA_KEY] = input_metadata.merge_metadata(
            existing=metadata.get(input_metadata.METADATA_KEY),
            values=values,
            slot_names=self.get_slot_names(),
            slot_count=self.get_slot_count(),
        )
        report = (context or {}).get("report_message")
        if report:
            summary = ", ".join(f"{key}={value!r}" for key, value in metadata[input_metadata.METADATA_KEY].items())
            label = f"{len(matched_row_ids)} row(s) matched" if matched_row_ids else "no row matched"
            report(f"[INFO] - ({self.task_type}) - {label}; input metadata: {summary}")
        return task_base.WorkItem(source_path=work_item.source_path, current_path=work_item.current_path,
                                  metadata=metadata)
