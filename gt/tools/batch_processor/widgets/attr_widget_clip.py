"""
Batch Processor Clip Task Widgets
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks import task_clip
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetClipSplitTask(AttrWidgetTask):
    """Attribute widget for the clip split task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the clip split widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskClipSplit, optional): Task model.
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
            task (TaskClipSnapshot, optional): Task model.
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
