"""
Batch Processor Delete Project Files Task Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetDeleteProjectFilesTask(AttrWidgetTask):
    """Attribute widget for the project-file delete task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the project-file delete widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskDeleteProjectFiles, optional): Task model.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Refresh callback.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.add_common_task_settings(include_source=False, include_target=False)
        self.add_widget_separator_line(label_text="Delete Preferences")
        self.add_path_template_field(
            "Delete Path",
            self.task.settings.get("delete_path"),
            partial(self.set_task_setting, key="delete_path"),
            placeholder="{previous-task-path}",
            tooltip="Project-internal folder containing generated files to delete.",
            dir_only=True,
        )
        self.add_text_field(
            "Patterns",
            ", ".join(self.task.settings.get("patterns") or []),
            partial(self.set_task_setting_list_from_text, key="patterns"),
            placeholder="*",
            tooltip="Comma-separated file name or relative path patterns to delete.",
        )
        self.add_text_field(
            "Exclude Patterns",
            ", ".join(self.task.settings.get("exclude_patterns") or []),
            partial(self.set_task_setting_list_from_text, key="exclude_patterns"),
            placeholder="*.batch, logs/*",
            tooltip="Comma-separated file name or relative path patterns to keep.",
        )
        self.add_path_template_field(
            "Report Path",
            self.task.settings.get("report_path"),
            partial(self.set_task_setting, key="report_path"),
            placeholder="{project-dir}/logs/delete_project_files_{task-idx}.json",
            tooltip="Optional JSON report path for matched and deleted files.",
            file_filter="JSON Files (*.json);;All Files (*);;",
        )
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Dry Run", "dry_run", "Write the report without deleting files."),
            ("Report", "write_report", "Write a JSON report with matched and deleted files."),
            ("Files", "delete_files", "Delete matching files."),
            ("Empty Dirs", "delete_empty_dirs", "Remove empty directories under the delete path."),
            ("Subdirectories", "include_subdirectories", "Search nested folders under the delete path."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=layout,
                tooltip=tooltip,
            )
        layout.addStretch()
        self.content_layout.addLayout(layout)
        self.add_run_selected_task_button(
            label_text="Run Delete Task",
            tooltip="Run only this Delete Project Files task using the current safety settings.",
        )
        self.content_layout.addStretch()


