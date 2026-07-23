"""
Batch Processor Attribute Widgets for Extended Tasks
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks import task_archive
from gt.tools.batch_processor.tasks import task_fbx_export
from gt.tools.batch_processor.tasks import task_clip
from gt.tools.batch_processor.tasks import task_map_rename
from gt.tools.batch_processor.tasks import task_validation
import gt.ui.python_output_view as ui_python_output_view
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial
import json
import os


class AttrWidgetFbxExportTask(AttrWidgetTask):
    """Attribute widget for the FBX export task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the FBX export widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (FbxExportTask, optional): Task model.
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
        self.add_common_task_settings(
            scene_io_settings={
                "load_mode_key": "source_load_mode",
                "output_extension_key": "output_extension",
                "output_extension_value": ".fbx",
                "output_extension_values": [".fbx"],
                "include_load_plugins": True,
            }
        )
        self.add_widget_separator_line(label_text="FBX Export Preferences")
        self.add_combo_box(
            "Export Mode",
            self.task.settings.get("export_mode"),
            task_fbx_export.FBX_EXPORT_MODE_VALUES,
            partial(self.set_task_setting, key="export_mode"),
            tooltip="Preset used when exporting the FBX file.",
        )
        self.add_capture_frame_range_controls()
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Selection", "export_selection", "Export selected nodes only."),
            ("Key Reducer", "key_reducer", "Apply FBX key reducer options."),
            ("ASCII", "ascii", "Write an ASCII FBX when supported."),
            ("Generate Log", "generate_log", "Ask the FBX plugin to generate an export log."),
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
        self.content_layout.addStretch()

    def add_capture_frame_range_controls(self):
        """Adds the FBX frame range row."""
        layout = self.add_labeled_layout("Frame Range", tooltip="Manual frame range for animation exports.")
        self.add_checkbox(
            "Auto",
            self.task.settings.get("auto_frame_range"),
            partial(self.set_task_setting, key="auto_frame_range"),
            layout=layout,
            tooltip="Use the scene playback range.",
        )
        self.add_row_label(layout, "Start", tooltip="Manual start frame.")
        start_spin = self.create_frame_spin_box(
            self.task.settings.get("frame_start"),
            partial(self.set_task_setting, key="frame_start"),
            tooltip="Manual start frame.",
        )
        layout.addWidget(start_spin)
        self.add_row_label(layout, "End", tooltip="Manual end frame.")
        end_spin = self.create_frame_spin_box(
            self.task.settings.get("frame_end"),
            partial(self.set_task_setting, key="frame_end"),
            tooltip="Manual end frame.",
        )
        layout.addWidget(end_spin)
        layout.addStretch()

    @staticmethod
    def create_frame_spin_box(value, setter, tooltip=None):
        """Creates a frame spin box.

        Args:
            value (object): Initial value.
            setter (callable): Setter callback.
            tooltip (str, optional): Tooltip.

        Returns:
            QSpinBox: Created spin box.
        """
        spin_box = ui_qt.QtWidgets.QSpinBox()
        spin_box.setRange(-1000000, 1000000)
        try:
            spin_box.setValue(int(float(value)))
        except (TypeError, ValueError):
            spin_box.setValue(0)
        spin_box.setMinimumHeight(35)
        spin_box.setMinimumWidth(80)
        spin_box.setToolTip(tooltip or "Frame")
        spin_box.valueChanged.connect(lambda value_int: setter(value_int))
        return spin_box


class AttrWidgetAutoRigBuildTask(AttrWidgetTask):
    """Attribute widget for the Auto Rig build task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Auto Rig build widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (AutoRigBuildTask, optional): Task model.
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
        self.add_widget_separator_line(label_text="Auto Rig Build Preferences")
        self.add_combo_box(
            "Output Extension",
            self.task.settings.get("output_extension"),
            [".ma", ".mb"],
            partial(self.set_task_setting, key="output_extension"),
            tooltip="Maya scene extension used for the built rig.",
        )
        self.add_checkbox(
            "Optimized Proxy",
            self.task.settings.get("optimized_proxy"),
            partial(self.set_task_setting, key="optimized_proxy"),
            tooltip="Build the proxy in optimized mode before building the final rig.",
        )
        self.add_force_disable_controls()
        self.content_layout.addStretch()

    def add_force_disable_controls(self):
        """Adds controls used to force-disable Auto Rigger module classes."""
        layout = self.add_labeled_layout("Disable Module", tooltip="Add a module class to force-disable before build.")
        combo_box = ui_qt.QtWidgets.QComboBox()
        combo_box.setEditable(True)
        combo_box.setMinimumHeight(35)
        combo_box.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        for module_name in get_auto_rigger_module_names():
            combo_box.addItem(module_name)
        layout.addWidget(combo_box)
        add_button = ui_qt.QtWidgets.QPushButton("Add")
        add_button.setMinimumHeight(35)
        add_button.clicked.connect(partial(self.add_force_disabled_module, combo_box=combo_box))
        layout.addWidget(add_button)
        self.force_disable_text_area = self.add_text_area(
            "Force Disabled Modules",
            "\n".join(self.task.settings.get("force_disable_modules") or []),
            partial(self.set_task_setting_list_from_text, key="force_disable_modules"),
            placeholder="One Auto Rigger module class per line.",
            tooltip="Modules listed here are disabled before the rig project builds.",
        )

    def add_force_disabled_module(self, combo_box):
        """Adds a selected module name to the force-disabled list.

        Args:
            combo_box (QComboBox): Module selector.
        """
        module_name = combo_box.currentText().strip()
        current_values = self.task.settings.get("force_disable_modules") or []
        if module_name and module_name not in current_values:
            current_values.append(module_name)
            self.task.settings["force_disable_modules"] = current_values
            self.force_disable_text_area.setPlainText("\n".join(current_values))


class AttrWidgetClipSplitTask(AttrWidgetTask):
    """Attribute widget for the clip split task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the clip split widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (ClipSplitTask, optional): Task model.
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
        self.add_widget_separator_line(label_text="Clip Split Preferences")
        self.add_combo_box(
            "Missing Clips",
            self.task.settings.get("missing_clips_severity"),
            [task_clip.CLIP_SEVERITY_WARNING, task_clip.CLIP_SEVERITY_ERROR],
            partial(self.set_task_setting, key="missing_clips_severity"),
            tooltip="How this task reports files that do not contain clip data.",
        )
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            (
                "Force Current Range",
                "force_current_range_if_no_clips",
                "Export the playback range when no clips exist.",
            ),
            ("Inactive Clips", "include_inactive_clips", "Include inactive clip entries."),
            ("Clip Name", "append_clip_name", "Append the clip name to output files."),
            ("Frame Range", "append_frame_range", "Append the frame range to output files."),
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
        self.content_layout.addStretch()


class AttrWidgetClipSnapshotTask(AttrWidgetTask):
    """Attribute widget for the clip snapshot task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the clip snapshot widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (ClipSnapshotTask, optional): Task model.
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
        self.add_common_task_settings(include_target=False)
        self.add_widget_separator_line(label_text="Clip Snapshot Preferences")
        self.add_combo_box(
            "Mode",
            self.task.settings.get("mode"),
            task_clip.CLIP_SNAPSHOT_MODE_VALUES,
            partial(self.set_task_setting, key="mode"),
            tooltip=(
                "Save Snapshot writes clip data from incoming Maya scenes to the snapshot JSON. "
                "Load Snapshot reads the JSON and restores matching clip data into incoming Maya scenes. "
                "Bypass Task skips this task and sends incoming files to the next task unchanged."
            ),
        )
        self.add_path_template_field(
            "Snapshot Path",
            self.task.settings.get("snapshot_path"),
            partial(self.set_task_setting, key="snapshot_path"),
            placeholder="{project-dir}/data/clip_snapshot_data.json",
            tooltip="Project-relative or absolute path to the clip snapshot JSON file.",
            file_filter="JSON Files (*.json);;All Files (*);;",
        )
        self.add_combo_box(
            "Missing Entry",
            self.task.settings.get("missing_snapshot_severity"),
            [task_clip.CLIP_SEVERITY_WARNING, task_clip.CLIP_SEVERITY_ERROR],
            partial(self.set_task_setting, key="missing_snapshot_severity"),
            tooltip="How restore mode reports files missing from the snapshot.",
        )
        self.add_run_selected_task_button(
            label_text="Run Clip Snapshot",
            tooltip="Run this Clip Snapshot task now using the current project and selected mode.",
        )
        self.content_layout.addStretch()


class AttrWidgetMapRenameTask(AttrWidgetTask):
    """Attribute widget for the rename-map task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the rename-map widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (MapRenameTask, optional): Task model.
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
        self.add_widget_separator_line(label_text="Rename Map Preferences")
        self.add_path_template_field(
            "Folder A",
            self.task.settings.get("folder_a"),
            partial(self.set_task_setting, key="folder_a"),
            placeholder="{previous-previous-task-path}",
            tooltip="First folder used when discovering identical files.",
            dir_only=True,
        )
        self.add_path_template_field(
            "Folder B",
            self.task.settings.get("folder_b"),
            partial(self.set_task_setting, key="folder_b"),
            placeholder="{previous-task-path}",
            tooltip="Second folder used when discovering identical files with different names.",
            dir_only=True,
        )
        self.add_path_template_field(
            "Map Path",
            self.task.settings.get("map_path"),
            partial(self.set_task_setting, key="map_path"),
            placeholder="{project-dir}/data/rename_map.json",
            tooltip="JSON file that receives the generated rename map.",
            file_filter="JSON Files (*.json);;All Files (*);;",
        )
        self.add_combo_box(
            "Checksum",
            self.task.settings.get("checksum_algorithm"),
            task_map_rename.CHECKSUM_ALGORITHMS,
            partial(self.set_task_setting, key="checksum_algorithm"),
            tooltip="Hash algorithm used to detect identical file contents.",
        )
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Subdirectories", "include_subdirectories", "Include nested folder files in the map comparison."),
            (
                "Different Names",
                "only_different_names",
                "Only map files that have identical contents and different names.",
            ),
            ("Unmatched", "include_unmatched", "Also record folder A files without a folder B content match."),
            ("Overwrite", "overwrite", "Overwrite the map JSON when it already exists."),
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
            label_text="Create Rename Map",
            tooltip="Run only this Map Rename task and write the configured map JSON.",
        )
        self.content_layout.addStretch()


class AttrWidgetDeleteProjectFilesTask(AttrWidgetTask):
    """Attribute widget for the project-file delete task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the project-file delete widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (DeleteProjectFilesTask, optional): Task model.
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


class AttrWidgetZipCompressTask(AttrWidgetTask):
    """Attribute widget for the zip compression task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the zip task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (ZipCompressTask, optional): Task model.
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


class AttrWidgetMayaSceneValidationTask(AttrWidgetTask):
    """Attribute widget for Maya scene validation."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Maya scene validation widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (MayaSceneValidationTask, optional): Task model.
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
        self.add_widget_separator_line(label_text="Scene Validation Preferences")
        self.add_combo_box(
            "Scope",
            self.task.settings.get("validation_scope"),
            ["Scene", "Selection", "Type"],
            partial(self.set_task_setting, key="validation_scope"),
            tooltip="Scope forwarded to validators that support it.",
        )
        self.add_combo_box(
            "Log Mode",
            self.task.settings.get("log_mode"),
            [
                task_validation.VALIDATION_LOG_ISSUES,
                task_validation.VALIDATION_LOG_ALL,
                task_validation.VALIDATION_LOG_NONE,
            ],
            partial(self.set_task_setting, key="log_mode"),
            tooltip="When validation logs should be written.",
        )
        self.add_checkbox(
            "Fail On Issues",
            self.task.settings.get("fail_on_issues"),
            partial(self.set_task_setting, key="fail_on_issues"),
            tooltip="Fail the task when any validator reports warning or worse.",
        )
        self.add_validator_controls()
        self.add_run_current_scene_button()
        self.content_layout.addStretch()

    def add_validator_controls(self):
        """Adds validator selector controls."""
        layout = self.add_labeled_layout("Validator", tooltip="Add a validator from gt.core.validator.")
        combo_box = ui_qt.QtWidgets.QComboBox()
        combo_box.setEditable(True)
        combo_box.setMinimumHeight(35)
        combo_box.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        for validator_name in task_validation.get_available_scene_validators():
            combo_box.addItem(validator_name)
        layout.addWidget(combo_box)
        add_button = ui_qt.QtWidgets.QPushButton("Add")
        add_button.setMinimumHeight(35)
        add_button.clicked.connect(partial(self.add_validator, combo_box=combo_box))
        layout.addWidget(add_button)
        self.validators_text_area = self.add_text_area(
            "Validators",
            "\n".join(self.task.settings.get("validators") or []),
            partial(self.set_task_setting_list_from_text, key="validators"),
            placeholder="One validator name per line.",
            tooltip="Validator class names to run for each scene.",
        )

    def add_validator(self, combo_box):
        """Adds a selected validator to the list.

        Args:
            combo_box (QComboBox): Validator selector.
        """
        validator_name = combo_box.currentText().strip()
        current_values = self.task.settings.get("validators") or []
        if validator_name and validator_name not in current_values:
            current_values.append(validator_name)
            self.task.settings["validators"] = current_values
            self.validators_text_area.setPlainText("\n".join(current_values))

    def add_run_current_scene_button(self):
        """Adds a button used to run validators against the current Maya scene."""
        tooltip = "Run the configured validators against the scene currently open in Maya."
        layout = self.add_labeled_layout("Actions", tooltip=tooltip)
        button = ui_qt.QtWidgets.QPushButton("Run On Current Scene")
        button.setMinimumHeight(35)
        button.setToolTip(tooltip)
        button.clicked.connect(self.run_validators_on_current_scene)
        layout.addWidget(button)
        layout.addStretch()

    def run_validators_on_current_scene(self):
        """Runs this task's validators against the current Maya scene and shows a result window."""
        if not self.task.get_validator_names():
            self.emit_status_message("Validate Scene has no validators configured.", status="warning")
            return
        try:
            results = self.task.run_validators()
        except Exception as exception:
            self.emit_status_message("Unable to run current-scene validation: {0}".format(exception), status="warning")
            return
        has_issues = any(result_data.get("status_value", 0) > 1 for result_data in results)
        title = "Validate Scene Results"
        output_window = ui_python_output_view.PythonOutputView(parent=self, editable=False)
        output_window.setWindowTitle(title)
        output_lines = [
            "Task: {0}".format(self.task.display_name),
            "Validators: {0}".format(len(results)),
            "Issues Found: {0}".format("Yes" if has_issues else "No"),
            "",
            json.dumps(results, indent=4, sort_keys=True),
        ]
        output_window.set_python_output_text("\n".join(output_lines))
        output_window.show()
        status = "warning" if has_issues else "info"
        self.emit_status_message("Validate Scene current-scene test finished.", status=status)


class AttrWidgetFileIntegrityValidationTask(AttrWidgetTask):
    """Attribute widget for file integrity validation."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the file validation widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (FileIntegrityValidationTask, optional): Task model.
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
        self.add_widget_separator_line(label_text="File Integrity Preferences")
        self.add_combo_box(
            "Log Mode",
            self.task.settings.get("log_mode"),
            [
                task_validation.VALIDATION_LOG_ISSUES,
                task_validation.VALIDATION_LOG_ALL,
                task_validation.VALIDATION_LOG_NONE,
            ],
            partial(self.set_task_setting, key="log_mode"),
            tooltip="Write JSON integrity reports for every file, only files with issues, or never.",
        )
        self.add_text_field(
            "Min Size (Bytes)",
            self.task.settings.get("minimum_file_size_bytes"),
            partial(self.set_task_setting, key="minimum_file_size_bytes"),
            tooltip="Minimum valid file size in bytes. 1024 bytes = 1 KB. 1048576 bytes = 1 MB.",
        )
        self.add_text_field(
            "Max Size (Bytes)",
            self.task.settings.get("maximum_file_size_bytes"),
            partial(self.set_task_setting, key="maximum_file_size_bytes"),
            placeholder="Optional",
            tooltip="Optional maximum valid file size in bytes. Leave empty when there is no upper limit.",
        )
        self.add_combo_box(
            "Checksum",
            self.task.settings.get("checksum_algorithm"),
            ["sha1", "sha256", "md5"],
            partial(self.set_task_setting, key="checksum_algorithm"),
            tooltip="Hash algorithm used when detecting files with matching contents.",
        )
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            ("Empty Files", "warn_when_empty", "Report zero-byte files as integrity warnings."),
            (
                "Group Size Diff",
                "warn_when_size_differs_from_group",
                "Report files whose byte size differs from the other files processed by this task.",
            ),
            ("Duplicate Hashes", "detect_duplicate_checksums", "Report files that share the same checksum."),
            ("Fail On Issues", "fail_on_issues", "Fail the task when any integrity issue is found."),
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
            label_text="Run Integrity Check",
            tooltip="Run only this Validate Integrity task against its configured source files.",
        )
        self.content_layout.addStretch()


class AttrWidgetFolderCompareValidationTask(AttrWidgetTask):
    """Attribute widget for folder comparison validation."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the folder compare widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (FolderCompareValidationTask, optional): Task model.
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
        self.add_common_task_settings(include_source=False)
        self.add_widget_separator_line(label_text="Parity Validation Preferences")
        self.add_path_template_field(
            "Folder A",
            self.task.settings.get("folder_a"),
            partial(self.set_task_setting, key="folder_a"),
            placeholder="{previous-task-path}",
            tooltip="First folder used as one side of the parity validation.",
            dir_only=True,
        )
        self.add_path_template_field(
            "Folder B",
            self.task.settings.get("folder_b"),
            partial(self.set_task_setting, key="folder_b"),
            placeholder="{next-task-path}",
            tooltip="Second folder used as the other side of the parity validation.",
            dir_only=True,
        )
        self.add_combo_box(
            "Method",
            self.task.settings.get("comparison_method"),
            task_validation.get_folder_compare_methods(),
            partial(self.set_task_setting, key="comparison_method"),
            tooltip=(
                "How folder parity is compared: relative paths, file names, file names without extensions, "
                "or SHA1 checksums for matching relative paths."
            ),
        )
        self.add_combo_box(
            "Log Mode",
            self.task.settings.get("log_mode"),
            [
                task_validation.VALIDATION_LOG_ISSUES,
                task_validation.VALIDATION_LOG_ALL,
                task_validation.VALIDATION_LOG_NONE,
            ],
            partial(self.set_task_setting, key="log_mode"),
            tooltip="Write JSON parity reports for every comparison, only comparisons with differences, or never.",
        )
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Subdirectories",
            self.task.settings.get("include_subdirectories"),
            partial(self.set_task_setting, key="include_subdirectories"),
            layout=layout,
            tooltip="Include files inside nested folders when building the parity comparison.",
        )
        self.add_checkbox(
            "Fail On Differences",
            self.task.settings.get("fail_on_differences"),
            partial(self.set_task_setting, key="fail_on_differences"),
            layout=layout,
            tooltip="Fail this validation task when the compared folders do not match.",
        )
        layout.addStretch()
        self.content_layout.addLayout(layout)
        self.add_run_selected_task_button(
            label_text="Run Parity Check",
            tooltip="Run only this Validate Parity task against its configured folders.",
        )
        self.content_layout.addStretch()


class AttrWidgetThumbnailCaptureTask(AttrWidgetTask):
    """Attribute widget for thumbnail capture."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the thumbnail capture widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (ThumbnailCaptureTask, optional): Task model.
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
        self.add_widget_separator_line(label_text="Thumbnail Preferences")
        self.add_combo_box(
            "Format",
            self.task.settings.get("image_format"),
            get_image_formats(),
            partial(self.set_task_setting, key="image_format"),
            tooltip="Output image format.",
        )
        self.add_capture_size_controls()
        self.add_camera_controls()
        self.add_thumbnail_frame_controls()
        self.add_panel_option_controls()
        self.content_layout.addStretch()

    def add_capture_size_controls(self):
        """Adds width and height controls."""
        layout = self.add_labeled_layout("Resolution", tooltip="Output capture resolution.")
        self.add_row_label(layout, "Width")
        layout.addWidget(
            self.create_int_spin_box(self.task.settings.get("width"), partial(self.set_task_setting, key="width"))
        )
        self.add_row_label(layout, "Height")
        layout.addWidget(
            self.create_int_spin_box(self.task.settings.get("height"), partial(self.set_task_setting, key="height"))
        )
        layout.addStretch()

    def add_camera_controls(self):
        """Adds camera selection controls for viewport capture."""
        tooltip = "Optional camera transform or shape used for capture. Leave empty to use the active viewport camera."
        layout = self.add_labeled_layout("Camera", tooltip=tooltip)
        self.camera_field = self.create_text_field(
            text=self.task.settings.get("camera_name"),
            placeholder="Active viewport camera",
            tooltip=tooltip,
        )
        self.camera_field.textChanged.connect(partial(self.set_task_setting, key="camera_name"))
        layout.addWidget(self.camera_field)
        view_button = ui_qt.QtWidgets.QPushButton("View")
        view_button.setMinimumHeight(35)
        view_button.setToolTip("Use the camera currently assigned to the active Maya viewport.")
        view_button.clicked.connect(self.set_camera_from_active_view)
        layout.addWidget(view_button)
        selection_button = ui_qt.QtWidgets.QPushButton("Selection")
        selection_button.setMinimumHeight(35)
        selection_button.setToolTip("Use the selected camera transform or camera shape.")
        selection_button.clicked.connect(self.set_camera_from_selection)
        layout.addWidget(selection_button)

    def add_thumbnail_frame_controls(self):
        """Adds thumbnail frame controls."""
        layout = self.add_labeled_layout("Frame", tooltip="Frame used for thumbnail capture.")
        self.add_checkbox(
            "Current",
            self.task.settings.get("current_frame"),
            partial(self.set_task_setting, key="current_frame"),
            layout=layout,
            tooltip="Use the current frame.",
        )
        self.add_row_label(layout, "Frame")
        layout.addWidget(
            self.create_int_spin_box(self.task.settings.get("frame"), partial(self.set_task_setting, key="frame"))
        )
        layout.addStretch()

    def add_panel_option_controls(self):
        """Adds shared viewport panel controls."""
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in get_panel_option_specs():
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=layout,
                tooltip=tooltip,
            )
        layout.addStretch()
        self.content_layout.addLayout(layout)

    @staticmethod
    def create_int_spin_box(value, setter, minimum=1, maximum=7680):
        """Creates an integer spin box.

        Args:
            value (object): Initial value.
            setter (callable): Setter callback.
            minimum (int, optional): Minimum value.
            maximum (int, optional): Maximum value.

        Returns:
            QSpinBox: Created spin box.
        """
        spin_box = ui_qt.QtWidgets.QSpinBox()
        spin_box.setRange(minimum, maximum)
        spin_box.setValue(int(value or minimum))
        spin_box.setMinimumHeight(35)
        spin_box.setMinimumWidth(90)
        spin_box.valueChanged.connect(lambda value_int: setter(value_int))
        return spin_box

    def set_camera_from_active_view(self):
        """Stores the active viewport camera on the task."""
        try:
            import maya.cmds as cmds

            panel = cmds.getPanel(withFocus=True)
            if cmds.getPanel(typeOf=panel) != "modelPanel":
                panels = cmds.getPanel(type="modelPanel") or []
                panel = panels[0] if panels else None
            if not panel:
                self.emit_status_message("Unable to find an active model panel.", status="warning")
                return
            camera_name = cmds.modelEditor(panel, query=True, camera=True)
            self.camera_field.setText(camera_name or "")
            self.emit_status_message('Capture camera set from active view: "{0}".'.format(camera_name))
        except Exception as exception:
            self.emit_status_message("Unable to get active view camera: {0}".format(exception), status="warning")

    def set_camera_from_selection(self):
        """Stores the selected camera transform or shape on the task."""
        try:
            import maya.cmds as cmds

            selection = cmds.ls(selection=True) or []
            for item in selection:
                camera_name = self.get_camera_from_node(cmds, item)
                if camera_name:
                    self.camera_field.setText(camera_name)
                    self.emit_status_message('Capture camera set from selection: "{0}".'.format(camera_name))
                    return
            self.emit_status_message("Select a camera transform or camera shape first.", status="warning")
        except Exception as exception:
            self.emit_status_message("Unable to get selected camera: {0}".format(exception), status="warning")

    @staticmethod
    def get_camera_from_node(cmds, node):
        """Gets a camera transform from a selected node.

        Args:
            cmds (module): Maya commands module.
            node (str): Selected node.

        Returns:
            str: Camera transform, or empty string.
        """
        if cmds.objectType(node) == "camera":
            parents = cmds.listRelatives(node, parent=True, fullPath=False) or []
            return parents[0] if parents else node
        shapes = cmds.listRelatives(node, shapes=True, fullPath=False) or []
        for shape in shapes:
            if cmds.objectType(shape) == "camera":
                return node
        return ""


class AttrWidgetPlayblastCaptureTask(AttrWidgetThumbnailCaptureTask):
    """Attribute widget for playblast capture."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the playblast capture widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (PlayblastCaptureTask, optional): Task model.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Refresh callback.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        AttrWidgetTask.__init__(
            self,
            parent=parent,
            task=task,
            project=project,
            refresh_parent_func=refresh_parent_func,
            *args,
            **kwargs
        )
        self.add_common_task_settings()
        self.add_widget_separator_line(label_text="Playblast Preferences")
        self.add_combo_box(
            "Format",
            self.task.settings.get("video_format"),
            get_video_formats(),
            partial(self.set_task_setting, key="video_format"),
            tooltip="Output playblast format.",
        )
        self.add_capture_size_controls()
        self.add_camera_controls()
        self.add_playblast_frame_controls()
        self.add_panel_option_controls()
        self.content_layout.addStretch()

    def add_playblast_frame_controls(self):
        """Adds playblast frame range controls."""
        layout = self.add_labeled_layout("Frame Range", tooltip="Frame range used for playblast capture.")
        self.add_checkbox(
            "Auto",
            self.task.settings.get("auto_frame_range"),
            partial(self.set_task_setting, key="auto_frame_range"),
            layout=layout,
            tooltip="Use the scene playback range.",
        )
        self.add_row_label(layout, "Start")
        layout.addWidget(
            self.create_int_spin_box(
                self.task.settings.get("start_frame"),
                partial(self.set_task_setting, key="start_frame"),
                minimum=-1000000,
            )
        )
        self.add_row_label(layout, "End")
        layout.addWidget(
            self.create_int_spin_box(
                self.task.settings.get("end_frame"),
                partial(self.set_task_setting, key="end_frame"),
                minimum=-1000000,
            )
        )
        layout.addStretch()

    def add_panel_option_controls(self):
        """Adds shared viewport panel controls."""
        layout = ui_qt.QtWidgets.QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Ornaments",
            self.task.settings.get("show_ornaments"),
            partial(self.set_task_setting, key="show_ornaments"),
            layout=layout,
            tooltip="Include HUD, grid, and viewport ornaments.",
        )
        for label_text, key, tooltip in get_panel_option_specs():
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=layout,
                tooltip=tooltip,
            )
        layout.addStretch()
        self.content_layout.addLayout(layout)


def get_auto_rigger_module_names():
    """Gets Auto Rigger module names.

    Returns:
        list: Sorted module names.
    """
    try:
        from gt.tools.auto_rigger.rig_modules import RigModules

        return sorted(RigModules.get_module_names())
    except Exception:
        return ["ModuleSaveScene", "ModuleExportSkeletalMesh"]


def get_image_formats():
    """Gets supported viewport image formats.

    Returns:
        list: Image format names.
    """
    try:
        import gt.core.playblast as core_playblast

        return core_playblast.ViewportImageFormats.get_all_formats()
    except Exception:
        return ["jpg", "png"]


def get_video_formats():
    """Gets supported viewport playblast formats.

    Returns:
        list: Video format names.
    """
    try:
        import gt.core.playblast as core_playblast

        return core_playblast.ViewportPlayblastFormats.get_all_formats()
    except Exception:
        return ["qt", "avi", "image"]


def get_panel_option_specs():
    """Gets shared viewport panel option specs.

    Returns:
        list: Tuples containing label, setting key, and tooltip.
    """
    return [
        ("Default Material", "default_material", "Use default material while capturing."),
        ("X-Ray", "x_ray", "Enable X-Ray while capturing."),
        ("Wireframe", "wireframe_on_shaded", "Enable wireframe on shaded while capturing."),
        ("Hide Curves", "hide_curves", "Hide NURBS curves in the model panel while capturing."),
    ]
