"""
Batch Processor FBX Export Task Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets.inline_python_editor import InlinePythonEditorWidget
from gt.tools.batch_processor.tasks import task_export_fbx
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetFbxExportTask(AttrWidgetTask):
    """Attribute widget for the FBX export task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the FBX export widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskExportFbx, optional): Task model.
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
        self.frame_start_label = None
        self.frame_end_label = None
        self.frame_start_spin = None
        self.frame_end_spin = None
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
            task_export_fbx.FBX_EXPORT_MODE_VALUES,
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
        self.add_pre_export_script_section()
        self.content_layout.addStretch()

    def add_capture_frame_range_controls(self):
        """Adds the FBX frame range row."""
        layout = self.add_labeled_layout("Frame Range", tooltip="Manual frame range for animation exports.")
        self.add_checkbox(
            "Auto",
            self.task.settings.get("auto_frame_range"),
            self.set_auto_frame_range,
            layout=layout,
            tooltip="Use the scene playback range.",
        )
        self.frame_start_label = self.add_row_label(layout, "Start", tooltip="Manual start frame.")
        self.frame_start_spin = self.create_frame_spin_box(
            self.task.settings.get("frame_start"),
            partial(self.set_task_setting, key="frame_start"),
            tooltip="Manual start frame.",
        )
        layout.addWidget(self.frame_start_spin)
        self.frame_end_label = self.add_row_label(layout, "End", tooltip="Manual end frame.")
        self.frame_end_spin = self.create_frame_spin_box(
            self.task.settings.get("frame_end"),
            partial(self.set_task_setting, key="frame_end"),
            tooltip="Manual end frame.",
        )
        layout.addWidget(self.frame_end_spin)
        layout.addStretch()
        self.refresh_frame_range_enabled_state()

    def set_auto_frame_range(self, value):
        """Sets automatic frame range and updates manual controls.

        Args:
            value (bool): Whether automatic frame range is enabled.
        """
        self.task.settings["auto_frame_range"] = bool(value)
        self.refresh_frame_range_enabled_state()

    def refresh_frame_range_enabled_state(self):
        """Updates manual frame widgets based on automatic frame range."""
        is_manual = not bool(self.task.settings.get("auto_frame_range", True))
        for widget in [
            self.frame_start_label,
            self.frame_start_spin,
            self.frame_end_label,
            self.frame_end_spin,
        ]:
            if widget:
                widget.setEnabled(is_manual)

    def add_pre_export_script_section(self):
        """Adds the collapsed optional pre-export script section."""
        collapsed = bool(self.task.settings.get("pre_export_script_collapsed", True))
        section = self.add_collapsible_section(
            label_text="Pre-Export Script",
            collapsed=collapsed,
            state_setter=partial(self.set_task_setting, key="pre_export_script_collapsed"),
            tooltip="Optional Python script that runs in the loaded scene before FBX export.",
        )
        layout = section.get("content_layout")
        options_layout = ui_qt.QtWidgets.QHBoxLayout()
        options_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Run",
            self.task.settings.get("run_pre_export_script"),
            partial(self.set_task_setting, key="run_pre_export_script"),
            layout=options_layout,
            tooltip="Run the configured script after the scene loads and before FBX export starts.",
        )
        self.add_checkbox(
            "Pass Task Args",
            self.task.settings.get("pre_export_script_pass_standard_arguments", True),
            partial(self.set_task_setting, key="pre_export_script_pass_standard_arguments"),
            layout=options_layout,
            tooltip="Expose input, output, project, task, and related values as arguments and args.",
        )
        self.add_checkbox(
            "Pass Env",
            self.task.settings.get("pre_export_script_pass_environment_arguments", True),
            partial(self.set_task_setting, key="pre_export_script_pass_environment_arguments"),
            layout=options_layout,
            tooltip="Expose project environment variables as environment_variables and env.",
        )
        options_layout.addStretch()
        layout.addLayout(options_layout)
        editor = InlinePythonEditorWidget(
            parent=self,
            owner=self,
            text=self.task.settings.get("pre_export_script_text") or "",
            placeholder="Write an optional pre-export Python script here, or choose an example.",
            tooltip=(
                "Inline Python pass executed in the loaded scene before FBX export. "
                "Use it to prepare the scene or build the selection used by Export Selection.\n"
                "Use context, arguments/args, environment_variables/env, project, task, work_item, "
                "output_path, and export_mode."
            ),
            text_changed_callback=partial(self.set_task_setting, key="pre_export_script_text"),
            font_size=self.task.settings.get("pre_export_script_font_size") or 14,
            font_size_changed_callback=partial(self.set_task_setting, key="pre_export_script_font_size"),
            sample_scripts_directory=self.task.pre_export_script_samples_directory,
        )
        layout.addWidget(editor)

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


