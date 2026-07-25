"""
Batch Processor Map Rename Task Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.tasks import task_map_rename
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetMapRenameTask(AttrWidgetTask):
    """Attribute widget for the rename-map task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the rename-map widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskMapRename, optional): Task model.
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


