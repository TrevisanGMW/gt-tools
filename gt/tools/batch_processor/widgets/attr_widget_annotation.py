"""
Batch Processor Annotation Task Widgets
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks import task_annotation
import gt.ui.qt_import as ui_qt
from functools import partial


LABEL_MUTED_COLOR = "#888888"
LABEL_VALUE_COLOR = "#FFFFFF"
LABEL_HEADER_COLOR = "#BBBBBB"


class AttrWidgetAnnotationSnapshotTask(AttrWidgetTask):
    """Attribute widget for the annotation snapshot task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the annotation snapshot widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskAnnotationSnapshot, optional): Task model.
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
        self.add_common_task_settings(include_target=False)
        self.add_widget_separator_line(label_text="Annotation Snapshot Preferences")
        self.add_combo_box(
            "Mode",
            self.task.settings.get("mode"),
            task_annotation.ANNOTATION_SNAPSHOT_MODE_VALUES,
            self.set_mode,
            tooltip=(
                "Save Snapshot writes Annotation Tracker data from incoming Maya scenes to the snapshot JSON. "
                "Load Snapshot reads the JSON and restores matching annotation data into incoming Maya scenes. "
                "Bypass Task skips this task and sends incoming files to the next task unchanged."
            ),
        )
        self.add_path_template_field(
            "Snapshot Path",
            self.task.settings.get("snapshot_path"),
            partial(self.set_task_setting, key="snapshot_path"),
            placeholder="{project-dir}/data/annotation_snapshot_data.json",
            tooltip="Project-relative or absolute path to the annotation snapshot JSON file.",
            file_filter="JSON Files (*.json);;All Files (*);;",
        )
        self.add_combo_box(
            "Missing Entry",
            self.task.settings.get("missing_snapshot_severity"),
            [task_annotation.ANNOTATION_SEVERITY_WARNING, task_annotation.ANNOTATION_SEVERITY_ERROR],
            partial(self.set_task_setting, key="missing_snapshot_severity"),
            tooltip="How restore mode reports files missing from the snapshot.",
        )
        self.add_summary_section()
        self.add_widget_separator_line()
        self.add_action_buttons()
        self.content_layout.addStretch()

    def add_summary_section(self):
        """Adds the Annotation Snapshot file and range-count summary panel."""
        self.add_widget_separator_line(label_text="Snapshot Summary")
        grid = ui_qt.QtWidgets.QGridLayout()
        grid.setContentsMargins(0, 0, 0, 5)
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(4)
        grid.addWidget(self._make_summary_header("Snapshot"), 0, 0)
        grid.addWidget(self._make_summary_header("Status"), 0, 1)
        grid.addWidget(self._make_summary_cell("Files", "file_count"), 1, 0)
        grid.addWidget(self._make_summary_cell("Ranges", "range_count"), 2, 0)
        self.status_label = ui_qt.QtWidgets.QLabel("-")
        self.status_label.setToolTip("Overall readiness of the active snapshot file.")
        grid.addWidget(self.status_label, 1, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
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
        """Creates and registers one mutable snapshot summary cell.

        Args:
            label_text (str): Static label text.
            key (str): Metadata key providing the displayed value.

        Returns:
            QLabel: Created value label.
        """
        value_label = ui_qt.QtWidgets.QLabel()
        value_label.setMinimumHeight(22)
        value_label.setToolTip(f"{label_text} stored in the active annotation snapshot.")
        self.summary_cells[key] = (value_label, label_text)
        return value_label

    def add_action_buttons(self):
        """Adds run and refresh actions for the Annotation Snapshot task."""
        layout = self.add_labeled_layout("Actions", tooltip="Run or refresh this Annotation Snapshot task.")
        run_button = self._make_action_button(
            "Run Annotation Snapshot",
            "Run this Annotation Snapshot task now using the current project and selected mode.",
        )
        run_button.clicked.connect(self.run_and_refresh)
        layout.addWidget(run_button, 2)
        refresh_button = self._make_action_button(
            "Refresh",
            "Re-read the snapshot file and update the summary panel.",
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
        """Sets the active mode and refreshes the snapshot summary.

        Args:
            value (str): Selected mode value.
        """
        self.set_task_setting(value, key="mode")
        self.refresh_summary()

    def refresh_summary(self):
        """Refreshes the snapshot summary from the active JSON file."""
        metadata = None
        status = {"text": "-", "color": task_annotation.SNAPSHOT_COLOR_NEUTRAL}
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

    def run_and_refresh(self):
        """Runs the active task and refreshes Save Snapshot results."""
        self.run_this_task_now()
        if self.task.settings.get("mode") == task_annotation.ANNOTATION_SNAPSHOT_MODE_SAVE:
            ui_qt.QtCore.QTimer.singleShot(1000, self.refresh_summary)
