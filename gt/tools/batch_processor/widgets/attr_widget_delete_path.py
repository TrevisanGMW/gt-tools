"""
Batch Processor Delete Path Task Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetDeleteProjectFilesTask(AttrWidgetTask):
    """Attribute widget for the Delete Path task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Delete Path widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskDeleteProjectFiles, optional): Delete Path task model.
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
        self.delete_count_label = None
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
            placeholder="{project-dir}/logs/delete_path_{task-idx}.json",
            tooltip="Optional JSON report path for matched and deleted files.",
            file_filter="JSON Files (*.json);;All Files (*);;",
        )
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        layout.addStretch()
        for label_text, key, tooltip in [
            ("Dry Run", "dry_run", "Write the report without deleting files."),
            ("Report", "write_report", "Write a JSON report with matched and deleted files."),
            ("Files", "delete_files", "Delete matching files."),
            ("Empty Dirs", "delete_empty_dirs", "Remove empty directories under the delete path."),
            ("Subdirectories", "include_subdirectories", "Search nested folders under the delete path."),
            (
                "Allow Out-of-Project Deletion",
                "allow_out_of_project_deletion",
                "Dangerous: allow deletion outside the active project directory. Avoid unless absolutely necessary.",
            ),
        ]:
            if key == "allow_out_of_project_deletion":
                setter = self._set_allow_out_of_project_deletion
            else:
                setter = partial(self.set_task_setting, key=key)
            checkbox = self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                setter,
                layout=layout,
                tooltip=tooltip,
            )
            if key == "allow_out_of_project_deletion":
                self._allow_out_of_project_checkbox = checkbox
            layout.addStretch()
        self.content_layout.addLayout(layout)

        count_layout = ui_qt.QtWidgets.QVBoxLayout()
        count_layout.setSpacing(6)
        count_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignVCenter)
        self.delete_count_label = ui_qt.QtWidgets.QLabel()
        self.delete_count_label.setWordWrap(True)
        self.delete_count_label.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignCenter)
        self.delete_count_label.setToolTip("Delete path preview statistics.")

        count_buttons_layout = ui_qt.QtWidgets.QHBoxLayout()
        count_buttons_layout.setContentsMargins(0, 0, 0, 0)
        count_buttons_layout.setSpacing(4)
        refresh_button = ui_qt.QtWidgets.QPushButton()
        refresh_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_reset))
        refresh_button.setToolTip("Refresh delete file count.")
        refresh_button.clicked.connect(
            lambda *args: self.refresh_delete_count(update_status=True)
        )
        preview_button = ui_qt.QtWidgets.QPushButton()
        preview_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        preview_button.setToolTip("Show files matched for deletion.")
        preview_button.clicked.connect(lambda *args: self.show_delete_files())
        count_buttons_layout.addStretch()
        count_buttons_layout.addWidget(refresh_button)
        count_buttons_layout.addWidget(preview_button)
        count_buttons_layout.addStretch()
        count_layout.addWidget(self.delete_count_label)
        count_layout.addLayout(count_buttons_layout)
        self.content_layout.addLayout(count_layout)
        self.refresh_delete_count(update_status=False)
        self.add_widget_separator_line()
        self.add_run_selected_task_button(
            label_text="Run Delete Task",
            tooltip="Run only this Delete Path task using the current safety settings.",
        )
        self.content_layout.addStretch()

    def _get_delete_preview_paths(self):
        """Gets files and empty directories matched by the delete settings.

        Returns:
            tuple: Matched file paths and empty directory paths.
        """
        if not self.project:
            return [], []

        delete_path = self.task.get_delete_path(self.project)
        safety_result = self.task.validate_delete_path(self.project, delete_path)
        if safety_result.errors:
            return [], []

        file_paths = self.task.collect_files(delete_path)
        empty_directory_paths = []
        if self.task.settings.get("delete_empty_dirs", True):
            empty_directory_paths = self.task.collect_empty_directories(delete_path)
        return file_paths, empty_directory_paths

    def show_delete_files(self):
        """Shows files matched by the current delete settings."""
        file_paths, _ = self._get_delete_preview_paths()
        self.show_path_list(title="Files To Delete", file_paths=file_paths)
        self.emit_status_message(
            "Delete preview found {0} file(s).".format(len(file_paths))
        )

    def refresh_delete_count(self, update_status=True):
        """Refreshes the delete file and empty-directory count.

        Args:
            update_status (bool): Whether to emit a status message.
        """
        file_paths, empty_directory_paths = self._get_delete_preview_paths()
        self.delete_count_label.setText(
            '<span style="color:#888888;">Files To Delete:</span> '
            '<span style="color:#FFFFFF;">{0}</span><br>'
            '<span style="color:#888888;">Empty Dirs To Delete:</span> '
            '<span style="color:#FFFFFF;">{1}</span>'.format(
                len(file_paths), len(empty_directory_paths)
            )
        )
        self.delete_count_label.setToolTip(
            "Files matched: {0}\nEmpty directories matched: {1}".format(
                len(file_paths), len(empty_directory_paths)
            )
        )
        if update_status:
            self.emit_status_message(
                "Delete Path preview found {0} file(s) and {1} empty directory path(s).".format(
                    len(file_paths), len(empty_directory_paths)
                )
            )

    def _set_allow_out_of_project_deletion(self, value):
        """Sets out-of-project deletion after an explicit warning confirmation.

        Args:
            value (bool): Requested checkbox state.
        """
        if not value:
            self.set_task_setting(False, key="allow_out_of_project_deletion")
            return

        message_box = ui_qt.QtWidgets.QMessageBox(self)
        try:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Warning)
        except AttributeError:
            message_box.setIcon(ui_qt.QtWidgets.QMessageBox.Icon.Warning)
        message_box.setWindowTitle("Dangerous Deletion Option")
        message_box.setText(
            "Allowing Delete Path to target locations outside the active project "
            "directory is dangerous and should be avoided. Continue?"
        )
        message_box.addButton(ui_qt.QtLib.StandardButton.Yes)
        message_box.addButton(ui_qt.QtLib.StandardButton.No)

        result = self.exec_dialog(message_box)
        if result == ui_qt.QtLib.StandardButton.Yes:
            self.set_task_setting(True, key="allow_out_of_project_deletion")
            return

        self._allow_out_of_project_checkbox.blockSignals(True)
        try:
            self._allow_out_of_project_checkbox.setChecked(False)
        finally:
            self._allow_out_of_project_checkbox.blockSignals(False)
