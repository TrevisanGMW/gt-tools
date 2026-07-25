"""
Batch Processor Archive Task Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks import task_archive
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial
import os


class AttrWidgetArchiveTask(AttrWidgetTask):
    """Attribute widget for the zip compression task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the zip task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskArchive, optional): Task model.
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
        self.add_common_task_settings()
        self.add_widget_separator_line(label_text="Zip Preferences")
        self.archive_name_field = self.add_archive_name_field()
        self.add_archive_version_controls()
        self.add_combo_box(
            "Compression",
            self.task.settings.get("compression"),
            ["Deflated", "Stored"],
            partial(self.set_task_setting, key="compression"),
            tooltip="Compression method used by the zip archive.",
        )
        self.source_path_relative_root_checkbox = self.add_checkbox(
            "Use Source Path Root",
            self.task.settings.get("use_source_path_as_relative_root", True),
            self.set_source_path_relative_root,
            tooltip="Use Source Path as the archive relative root and preserve paths automatically.",
        )
        self.relative_root_widgets = self.add_path_template_field(
            "Relative Root",
            self.task.settings.get("relative_root"),
            partial(self.set_task_setting, key="relative_root"),
            placeholder="Leave empty to use the common incoming root.",
            tooltip="Optional root used to preserve relative archive paths.",
            dir_only=True,
            return_widgets=True,
        )
        self.preserve_relative_paths_checkbox = self.add_checkbox(
            "Preserve Relative Paths",
            self.task.settings.get("preserve_relative_paths"),
            partial(self.set_task_setting, key="preserve_relative_paths"),
            tooltip="Store files using paths relative to a common or explicit root.",
        )
        self.refresh_source_path_relative_root_controls()
        self.add_segmentation_section(
            main_label="Run Once After All Jobs",
            main_key="run_once_after_multi_instance",
            main_tooltip=(
                "In multi-instance mode, wait for every regular job to succeed, then create this archive "
                "once from the resolved Source Path. This Zip Compress task must be the last enabled "
                "processing task. Enable \"Add Separator\" to mark this run-once step in the task list."
            ),
        )
        self.content_layout.addStretch()

    def add_archive_name_field(self):
        """Adds the archive name field with zip-specific path information.

        Returns:
            QLineEdit: Archive name field.
        """
        tooltip = "Name of the zip file to create. Supports the zip-only {version} variable."
        layout = self.add_labeled_layout("Archive Name", tooltip=tooltip)
        field = self.create_text_field(
            text=self.task.settings.get("archive_name"),
            placeholder="{project-sanitized-name}_{version}.zip",
            tooltip=tooltip,
        )
        info_button = ui_qt.QtWidgets.QPushButton()
        info_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        info_button.setToolTip("Get more information about the current archive path.")
        layout.addWidget(field)
        layout.addWidget(info_button)
        field.textChanged.connect(partial(self.set_task_setting, key="archive_name"))
        info_button.clicked.connect(partial(self.open_archive_name_information_dialog, field=field))
        return field

    def add_archive_version_controls(self):
        """Adds manual and automatic archive version controls."""
        layout = self.add_labeled_layout(
            "Version",
            tooltip="Version value used by the Archive Name {version} variable.",
        )
        self.archive_version_auto_checkbox = self.add_checkbox(
            "Auto",
            self.task.settings.get("archive_version_auto"),
            self.set_archive_version_auto,
            layout=layout,
            tooltip="Detect the next version from existing zip files in the target folder.",
        )
        self.add_row_label(layout, "Manual", tooltip="Manual version used when Auto is off.")
        self.archive_version_combo = ui_qt.QtWidgets.QComboBox()
        self.archive_version_combo.setEditable(True)
        self.archive_version_combo.setMinimumHeight(35)
        self.archive_version_combo.setMinimumWidth(80)
        self.archive_version_combo.setToolTip("Manual version used when Auto is off.")
        self.refresh_archive_version_combo_values()
        layout.addWidget(self.archive_version_combo)
        self.archive_version_combo.currentTextChanged.connect(partial(self.set_task_setting, key="archive_version"))
        self.add_row_label(layout, "Padding", tooltip="Minimum number of digits used by the version.")
        self.archive_version_padding_spin = ui_qt.QtWidgets.QSpinBox()
        self.archive_version_padding_spin.setRange(1, 8)
        self.archive_version_padding_spin.setValue(self.get_archive_version_padding())
        self.archive_version_padding_spin.setMinimumHeight(35)
        self.archive_version_padding_spin.setMinimumWidth(64)
        self.archive_version_padding_spin.setToolTip("Minimum number of digits used by the version.")
        self.archive_version_padding_spin.valueChanged.connect(self.set_archive_version_padding)
        layout.addWidget(self.archive_version_padding_spin)
        layout.addStretch()
        self.refresh_archive_version_enabled_state()

    def refresh_archive_version_combo_values(self):
        """Refreshes the archive version combo values."""
        if not hasattr(self, "archive_version_combo"):
            return
        padding = self.get_archive_version_padding()
        current_value = str(self.task.settings.get("archive_version") or "").strip() or str(1).zfill(padding)
        self.archive_version_combo.blockSignals(True)
        self.archive_version_combo.clear()
        for version_number in range(1, 31):
            self.archive_version_combo.addItem(str(version_number).zfill(padding))
        if self.archive_version_combo.findText(current_value) == -1:
            self.archive_version_combo.addItem(current_value)
        index = self.archive_version_combo.findText(current_value)
        if index >= 0:
            self.archive_version_combo.setCurrentIndex(index)
        self.archive_version_combo.blockSignals(False)

    def set_archive_version_auto(self, value):
        """Sets automatic archive version detection.

        Args:
            value (bool): Whether automatic version detection is enabled.
        """
        self.set_task_setting(value, key="archive_version_auto")
        self.refresh_archive_version_enabled_state()

    def set_archive_version_padding(self, value):
        """Sets archive version padding.

        Args:
            value (int): New version padding.
        """
        value = int(value)
        self.set_task_setting(value, key="archive_version_padding")
        self.set_task_setting(
            self.task.format_archive_version(self.task.settings.get("archive_version"), padding=value),
            key="archive_version",
        )
        self.refresh_archive_version_combo_values()

    def refresh_archive_version_enabled_state(self):
        """Refreshes manual archive version control enabled states."""
        auto_version = bool(self.task.settings.get("archive_version_auto", False))
        if hasattr(self, "archive_version_combo"):
            self.archive_version_combo.setEnabled(not auto_version)

    def set_source_path_relative_root(self, value):
        """Sets whether Source Path should be used as the archive relative root.

        Args:
            value (bool): Whether Source Path should drive archive relative paths.
        """
        self.set_task_setting(bool(value), key="use_source_path_as_relative_root")
        self.refresh_source_path_relative_root_controls()

    def refresh_source_path_relative_root_controls(self):
        """Refreshes controls overridden by the source-path relative root option."""
        use_source_root = bool(self.task.settings.get("use_source_path_as_relative_root", True))
        if hasattr(self, "relative_root_widgets") and self.relative_root_widgets:
            for key in ["field", "info_button", "open_button", "browse_button"]:
                widget = self.relative_root_widgets.get(key)
                if widget:
                    widget.setEnabled(not use_source_root)
        if hasattr(self, "preserve_relative_paths_checkbox") and self.preserve_relative_paths_checkbox:
            self.preserve_relative_paths_checkbox.blockSignals(True)
            if use_source_root:
                self.preserve_relative_paths_checkbox.setChecked(True)
            else:
                self.preserve_relative_paths_checkbox.setChecked(
                    bool(self.task.settings.get("preserve_relative_paths", True))
                )
            self.preserve_relative_paths_checkbox.setEnabled(not use_source_root)
            self.preserve_relative_paths_checkbox.blockSignals(False)

    def get_archive_version_padding(self):
        """Gets the archive version padding from task settings.

        Returns:
            int: Minimum digit count.
        """
        try:
            return max(1, int(self.task.settings.get("archive_version_padding", 2)))
        except (TypeError, ValueError):
            return 2

    def open_archive_name_information_dialog(self, field):
        """Opens path information for the resolved archive name.

        Args:
            field (QLineEdit): Archive name field.
        """
        if not self.project:
            self.open_warning_dialog("Project Missing", "Unable to resolve archive path without a project.")
            return
        self.task.settings["archive_name"] = field.text()
        step_output_dir = self.get_zip_step_output_dir()
        archive_path = self.task.build_archive_path(project=self.project, step_output_dir=step_output_dir)
        exists = os.path.exists(archive_path)
        is_dir = os.path.isdir(archive_path)
        is_file = os.path.isfile(archive_path)
        info_lines = self.build_path_information_lines(
            parsed_path=archive_path,
            exists=exists,
            is_dir=is_dir,
            is_file=is_file,
        )
        version_value = self.task.get_archive_version(
            project=self.project,
            step_output_dir=step_output_dir,
        )
        info_lines.append("Archive Version: {0}".format(version_value))
        info_lines.append("Zip-only Variable: {0}".format(task_archive.ZIP_VERSION_TOKEN))
        file_paths = []
        if is_file:
            file_paths = [archive_path]
        self.show_path_list(
            title="Resolved Input Files",
            file_paths=file_paths,
            header_lines=info_lines,
        )
        self.emit_status_message('Resolved archive path information for: "{0}"'.format(field.text()))

    def get_zip_step_output_dir(self):
        """Gets the resolved Zip task output folder.

        Returns:
            str: Resolved output directory.
        """
        if not self.project:
            return ""
        task_index = None
        if hasattr(self.project, "get_task_environment_index"):
            task_index = self.project.get_task_environment_index(self.task)
        return self.task.resolve_task_path(project=self.project, task_index=task_index)


