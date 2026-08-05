"""
Batch Processor Map Hierarchy Task Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks import task_map_hierarchy
import gt.ui.qt_import as ui_qt
from functools import partial


LABEL_MUTED_COLOR = "#888888"
LABEL_VALUE_COLOR = "#FFFFFF"
LABEL_HEADER_COLOR = "#BBBBBB"


class AttrWidgetMapHierarchyTask(AttrWidgetTask):
    """Attribute widget for the Map Hierarchy task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Map Hierarchy widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskMapHierarchy, optional): Task model.
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
        self.summary_cells = {}
        self.status_label = None
        self.apply_dir_widgets = None
        self.use_apply_dir_checkbox = None
        self.add_common_task_settings(include_source=False, include_target=False, include_overwrite=False)
        self.add_widget_separator_line(label_text="Map Hierarchy Preferences")
        self.add_combo_box(
            "Mode",
            self.task.settings.get("mode"),
            task_map_hierarchy.MODE_VALUES,
            self.set_mode,
            tooltip=(
                "Record Source/Target scan directories into a snapshot and compute the mapping. "
                "Apply Mapping (Forward) transforms the source state into the target state. "
                "Revert Mapping (Backward) transforms the target state back into the source state. "
                "Copy Source & Apply (Forward) copies the source into the apply directory first, then "
                "applies the mapping, leaving the source untouched. "
                "Apply/Revert Parallel run the mapping on the apply directory using base-name matches, "
                "ignoring extensions. Bypass Task forwards incoming files unchanged."
            ),
        )
        self.add_path_template_field(
            "Snapshot Path",
            self.task.settings.get("snapshot_path"),
            partial(self.set_task_setting, key="snapshot_path"),
            placeholder="JSON file that stores the hierarchy snapshot and mapping.",
            tooltip="Project-relative or absolute path to the hierarchy snapshot JSON file.",
            file_filter="JSON Files (*.json);;All Files (*);;",
        )
        self.add_path_template_field(
            "Source Dir",
            self.task.settings.get("source_dir"),
            partial(self.set_task_setting, key="source_dir"),
            placeholder="Directory scanned for the original file/folder state (read-only).",
            tooltip="Directory scanned when recording the source snapshot state. It is never modified.",
            dir_only=True,
        )
        self.add_path_template_field(
            "Target Dir",
            self.task.settings.get("target_dir"),
            partial(self.set_task_setting, key="target_dir"),
            placeholder="Directory scanned for the desired target file/folder state.",
            tooltip="Directory scanned when recording the target snapshot state.",
            dir_only=True,
        )
        self.apply_dir_widgets = self.add_path_template_field(
            "Apply Dir",
            self.task.settings.get("apply_dir"),
            partial(self.set_task_setting, key="apply_dir"),
            placeholder="Working directory transformed by apply/revert, or the parallel root for parallel modes.",
            tooltip=(
                "Directory transformed by Apply (Forward), Revert (Backward), Copy Source & Apply, and the "
                "destination for the Parallel modes (which match by base name, ignoring extensions). "
                "Enable the checkbox on the left to use this field; otherwise the target directory is used."
            ),
            dir_only=True,
            return_widgets=True,
        )
        self.use_apply_dir_checkbox = ui_qt.QtWidgets.QCheckBox()
        self.use_apply_dir_checkbox.setChecked(bool(self.task.settings.get("use_apply_dir")))
        self.use_apply_dir_checkbox.setToolTip(
            "Enable to use this dedicated apply directory for apply, revert, copy, and parallel modes. "
            "When unchecked, the target directory is used as the apply directory and this field is disabled."
        )
        self.use_apply_dir_checkbox.stateChanged.connect(
            lambda *args: self.set_use_apply_dir(self.use_apply_dir_checkbox.isChecked())
        )
        self.apply_dir_widgets["layout"].insertWidget(1, self.use_apply_dir_checkbox)
        self.add_combo_box(
            "Checksum",
            self.task.settings.get("checksum_algorithm"),
            task_map_hierarchy.CHECKSUM_ALGORITHMS,
            partial(self.set_task_setting, key="checksum_algorithm"),
            tooltip=(
                "Hash algorithm used to match files by content when recording a snapshot, so renamed or "
                "moved files are detected while computing the mapping.\n"
                "It is only used during Record Source/Target. Apply, Revert, Copy, and Parallel modes act "
                "purely on the stored relative paths, so this setting has no effect once the mapping exists.\n"
                "sha1: Fast and reliable for change detection (default).\n"
                "sha256: Strongest matching, slightly slower on large files.\n"
                "md5: Fastest, but the weakest at avoiding hash collisions."
            ),
        )
        self.add_state_resolution_section()
        self.add_summary_section()
        self.add_widget_separator_line()
        self.add_action_buttons()
        self.refresh_apply_dir_enabled_state()
        self.content_layout.addStretch()

    def add_state_resolution_section(self):
        """Adds the collapsible state-resolution configuration section."""
        self.task.settings.setdefault("state_resolution_collapsed", False)
        section = self.add_collapsible_section(
            "State Resolution",
            collapsed=self.task.settings.get("state_resolution_collapsed", False),
            state_setter=partial(self.set_task_setting, key="state_resolution_collapsed"),
            tooltip="How the apply and revert modes resolve ambiguous or unexpected filesystem states.",
        )
        section_layout = section.get("content_layout")
        self.add_combo_box(
            "Source Missing / Target Exists",
            self.task.settings.get("missing_source_resolution"),
            task_map_hierarchy.MISSING_SOURCE_OPTIONS,
            partial(self.set_task_setting, key="missing_source_resolution"),
            tooltip=(
                "When the source file is gone but the target already exists, assume the step was already "
                "applied and skip it, or flag it as an error."
            ),
            parent_layout=section_layout,
        )
        self.add_combo_box(
            "Files in Source, Missing in Snapshot",
            self.task.settings.get("source_orphan_resolution"),
            task_map_hierarchy.ORPHAN_OPTIONS,
            partial(self.set_task_setting, key="source_orphan_resolution"),
            tooltip=(
                "Forward, copy, and parallel-forward modes read source-like data and never modify it, so "
                "files not present in the snapshot can only be reported (ignored, warned, or errored)."
            ),
            parent_layout=section_layout,
        )
        self.add_combo_box(
            "Files in Apply/Target, Missing in Snapshot",
            self.task.settings.get("target_unmapped_resolution"),
            task_map_hierarchy.UNMAPPED_OPTIONS,
            partial(self.set_task_setting, key="target_unmapped_resolution"),
            tooltip=(
                "Revert modes operate on the apply/target directory (a working copy, not the source), so "
                "files not present in the snapshot may be left alone, deleted, or isolated to '_unmapped'."
            ),
            parent_layout=section_layout,
        )
        self.add_combo_box(
            "Collisions",
            self.task.settings.get("collision_resolution"),
            task_map_hierarchy.COLLISION_OPTIONS,
            partial(self.set_task_setting, key="collision_resolution"),
            tooltip=(
                "When a destination already exists and the source also still exists, append a numeric "
                "suffix or flag it as an error. Files are never overwritten destructively."
            ),
            parent_layout=section_layout,
        )
        toggles_layout = ui_qt.QtWidgets.QHBoxLayout()
        toggles_layout.setContentsMargins(0, 0, 0, 5)
        for label_text, key, tooltip in [
            (
                "Clean Empty Folders",
                "cleanup_empty_folders",
                "Delete empty folders left behind in the apply/target directory after an operation.",
            ),
            ("Subdirectories", "include_subdirectories", "Include nested folders when recording snapshots."),
            ("Dry Run", "dry_run", "Plan operations and write the report without moving, copying, or deleting files."),
            ("Write Report", "write_report", "Write an audit report of the executed operations to the report path."),
        ]:
            self.add_checkbox(
                label_text,
                self.task.settings.get(key),
                partial(self.set_task_setting, key=key),
                layout=toggles_layout,
                tooltip=tooltip,
            )
        toggles_layout.addStretch()
        section_layout.addLayout(toggles_layout)

    def add_summary_section(self):
        """Adds the three-column snapshot summary panel with Source/Target/Status headers."""
        self.add_widget_separator_line(label_text="Snapshot Summary")
        grid = ui_qt.QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 0, 0, 5)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(4)
        grid.addWidget(self._make_summary_header("Source"), 0, 0)
        grid.addWidget(self._make_summary_header("Target"), 0, 1)
        grid.addWidget(self._make_summary_header("Status"), 0, 2)
        grid.addWidget(self._make_summary_cell("Files", "source_file_count"), 1, 0)
        grid.addWidget(self._make_summary_cell("Files", "target_file_count"), 1, 1)
        grid.addWidget(self._make_summary_cell("Folders", "source_folder_count"), 2, 0)
        grid.addWidget(self._make_summary_cell("Folders", "target_folder_count"), 2, 1)
        self.status_label = ui_qt.QtWidgets.QLabel("-")
        self.status_label.setToolTip("Overall readiness of the active snapshot file.")
        grid.addWidget(self.status_label, 1, 2)
        grid.addWidget(self._make_summary_cell("Modifications", "modifications_required"), 2, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        self.content_layout.addLayout(grid)
        self.refresh_summary()

    @staticmethod
    def _make_summary_header(text):
        """Creates a bold column header label for the summary grid.

        Args:
            text (str): Header text.

        Returns:
            QLabel: Created header label.
        """
        header_label = ui_qt.QtWidgets.QLabel(f'<b style="color:{LABEL_HEADER_COLOR};">{text}</b>')
        header_label.setMinimumHeight(22)
        return header_label

    def _make_summary_cell(self, label_text, key):
        """Creates a summary value cell and registers it for refreshing.

        Args:
            label_text (str): Static label text.
            key (str): Metadata key that supplies the value.

        Returns:
            QLabel: Created value label.
        """
        value_label = ui_qt.QtWidgets.QLabel()
        value_label.setMinimumHeight(22)
        value_label.setToolTip(f"{label_text} recorded in the active snapshot.")
        self.summary_cells[key] = (value_label, label_text)
        return value_label

    def add_action_buttons(self):
        """Adds the run, preview, and refresh action buttons in one row."""
        layout = self.add_labeled_layout("Actions", tooltip="Run, preview, and refresh this Map Hierarchy task.")
        run_button = self._make_action_button(
            "Run Map Hierarchy", "Run this Map Hierarchy task now using the current project and selected mode."
        )
        run_button.clicked.connect(self.run_and_refresh)
        layout.addWidget(run_button, 2)
        preview_button = self._make_action_button(
            "Preview", "Show what the current mode will do without changing any files."
        )
        preview_button.clicked.connect(self.open_preview)
        layout.addWidget(preview_button, 1)
        refresh_button = self._make_action_button(
            "Refresh", "Re-read the snapshot file and update the summary panel."
        )
        refresh_button.clicked.connect(self.refresh_summary)
        layout.addWidget(refresh_button, 1)

    @staticmethod
    def _make_action_button(label_text, tooltip):
        """Creates a padded action button.

        Args:
            label_text (str): Button text.
            tooltip (str): Button tooltip.

        Returns:
            QPushButton: Created button.
        """
        button = ui_qt.QtWidgets.QPushButton(label_text)
        button.setMinimumHeight(35)
        button.setStyleSheet("padding: 3px 12px;")
        button.setSizePolicy(ui_qt.QtLib.SizePolicy.Expanding, ui_qt.QtLib.SizePolicy.Fixed)
        button.setToolTip(tooltip)
        return button

    def set_mode(self, value):
        """Sets the active mode and refreshes the summary panel.

        Args:
            value (str): Selected mode value.
        """
        self.set_task_setting(value, key="mode")
        self.refresh_summary()

    def set_use_apply_dir(self, value):
        """Sets the dedicated apply-directory option and refreshes the apply-dir state.

        Args:
            value (bool): Whether the dedicated apply directory is used.
        """
        self.set_task_setting(bool(value), key="use_apply_dir")
        self.refresh_apply_dir_enabled_state()

    def refresh_apply_dir_enabled_state(self):
        """Enables the apply-dir field only when the dedicated apply directory is in use."""
        if not self.apply_dir_widgets:
            return
        is_enabled = bool(self.task.settings.get("use_apply_dir"))
        for key in ["field", "info_button", "open_button", "browse_button"]:
            widget = self.apply_dir_widgets.get(key)
            if widget:
                widget.setEnabled(is_enabled)

    def refresh_summary(self):
        """Refreshes the summary panel from the active snapshot metadata and status."""
        metadata = None
        status = {"text": "-", "color": task_map_hierarchy.COLOR_STATUS_NEUTRAL}
        if self.project:
            try:
                metadata = self.task.read_snapshot_metadata(self.project)
                status = self.task.get_snapshot_status(self.project)
            except Exception:
                metadata = None
        for key, (value_label, label_text) in self.summary_cells.items():
            value = metadata.get(key) if metadata and key in metadata else None
            value_text = str(value) if value is not None else "-"
            value_label.setText(
                f'<span style="color:{LABEL_MUTED_COLOR};">{label_text}:</span> '
                f'<span style="color:{LABEL_VALUE_COLOR};">{value_text}</span>'
            )
        if self.status_label:
            self.status_label.setText(
                f'<span style="color:{LABEL_MUTED_COLOR};">File:</span> '
                f'<span style="color:{status.get("color")};">{status.get("text")}</span>'
            )

    def open_preview(self):
        """Opens a preview list describing the current mode's planned actions."""
        if not self.project:
            self.emit_status_message("Unable to preview: no project is active.", status="warning")
            return
        try:
            lines = self.task.preview_lines(self.project)
        except Exception as exception:
            self.emit_status_message(f"Unable to preview: {exception}", status="warning")
            return
        header_lines = [f"Map Hierarchy Preview - Mode: {self.task.settings.get('mode')}"]
        self.show_path_list(title="Map Hierarchy Preview", file_paths=lines, header_lines=header_lines)
        self.emit_status_message(f"Map Hierarchy preview produced {len(lines)} line(s).")

    def run_and_refresh(self):
        """Runs this task and refreshes the summary panel when it makes sense."""
        self.run_this_task_now()
        if self.task.settings.get("mode") in task_map_hierarchy.RECORD_MODES:
            ui_qt.QtCore.QTimer.singleShot(1000, self.refresh_summary)
