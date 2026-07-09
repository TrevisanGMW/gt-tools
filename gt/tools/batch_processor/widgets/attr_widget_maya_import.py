"""
Batch Processor Maya Import Task Attribute Widget
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
from gt.tools.batch_processor.widgets.inline_python_editor import InlinePythonEditorWidget
from gt.tools.batch_processor.tasks import task_maya_import
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetMayaImportTask(AttrWidgetTask):
    """Attribute widget for the Maya import task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the Maya import task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (MayaImportTask, optional): Maya import task.
            project (BatchProcessorModel, optional): Project model.
            refresh_parent_func (callable, optional): Function used to refresh parent UI.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.
        """
        self.framerate_spin_box = None
        self.scene_scale_combo_box = None
        self.up_axis_combo_box = None
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
                "load_mode_key": "scene_load_mode",
                "output_extension_key": "output_extension",
                "output_extension_values": [".ma", ".mb"],
            },
            collapsible=False,
        )
        self.add_widget_separator_line(label_text="Maya Import Preferences")
        self.add_text_field(
            "Namespace",
            self.task.settings.get("namespace"),
            partial(self.set_task_setting, key="namespace"),
            placeholder="Leave empty to import without a namespace.",
            tooltip="Optional namespace used when importing the source file.",
        )
        self.add_scene_option_controls()
        self.add_post_script_section()
        self.content_layout.addStretch()

    def add_scene_option_controls(self):
        """Adds optional Maya scene unit and orientation controls."""
        self.add_widget_separator_line(label_text="Maya Scene Options")

        clear_scene_layout = self.add_labeled_layout(
            "Scene",
            label_width=110,
            tooltip="Scene reset options applied before loading the source file.",
        )
        self.add_checkbox(
            "Clear Scene",
            self.task.settings.get("clear_scene"),
            partial(self.set_task_setting, key="clear_scene"),
            layout=clear_scene_layout,
            tooltip="Start a new empty Maya scene before each import.",
        )
        clear_scene_layout.addStretch()

        framerate_layout = self.add_labeled_layout(
            "Framerate",
            label_width=110,
            tooltip="Optionally set the Maya scene framerate after opening or importing.",
        )
        self.add_checkbox(
            "Set",
            self.task.settings.get("set_framerate"),
            self.set_framerate_enabled,
            layout=framerate_layout,
            tooltip="Set the scene framerate after loading the source file.",
        )
        self.framerate_spin_box = ui_qt.QtWidgets.QSpinBox()
        self.framerate_spin_box.setRange(1, 6000)
        self.framerate_spin_box.setValue(int(self.task.settings.get("framerate") or 30))
        self.framerate_spin_box.setMinimumHeight(35)
        self.framerate_spin_box.setFixedWidth(90)
        self.framerate_spin_box.setToolTip("Frames per second.")
        self.framerate_spin_box.valueChanged.connect(partial(self.set_task_setting, key="framerate"))
        framerate_layout.addWidget(self.framerate_spin_box)
        self.add_row_label(framerate_layout, "fps", tooltip="Frames per second.")
        framerate_layout.addStretch()

        scale_layout = self.add_labeled_layout(
            "Scene Scale",
            label_width=110,
            tooltip="Optionally set the Maya linear unit after opening or importing.",
        )
        self.add_checkbox(
            "Set",
            self.task.settings.get("set_scene_scale"),
            self.set_scene_scale_enabled,
            layout=scale_layout,
            tooltip="Set the scene linear unit after loading the source file.",
        )
        self.scene_scale_combo_box = self.create_row_combo_box(
            value=self.task.settings.get("scene_scale"),
            values=["mm", "cm", "m", "in", "ft", "yd"],
            tooltip="Maya linear unit.",
        )
        self.scene_scale_combo_box.currentTextChanged.connect(partial(self.set_task_setting, key="scene_scale"))
        scale_layout.addWidget(self.scene_scale_combo_box)
        scale_layout.addStretch()

        up_axis_layout = self.add_labeled_layout(
            "Scene Up Axis",
            label_width=110,
            tooltip="Optionally set the Maya scene up axis after opening or importing.",
        )
        self.add_checkbox(
            "Set",
            self.task.settings.get("set_scene_up_axis"),
            self.set_scene_up_axis_enabled,
            layout=up_axis_layout,
            tooltip="Set the scene up axis after loading the source file.",
        )
        self.up_axis_combo_box = self.create_row_combo_box(
            value=self.task.settings.get("scene_up_axis"),
            values=["Y", "Z"],
            tooltip="Maya scene up axis.",
        )
        self.up_axis_combo_box.currentTextChanged.connect(partial(self.set_task_setting, key="scene_up_axis"))
        up_axis_layout.addWidget(self.up_axis_combo_box)
        up_axis_layout.addStretch()
        self.refresh_scene_option_enabled_state()

    def set_framerate_enabled(self, value):
        """Sets whether the framerate option is enabled.

        Args:
            value (bool): Whether framerate should be set during execution.
        """
        self.task.settings["set_framerate"] = bool(value)
        self.refresh_scene_option_enabled_state()

    def set_scene_scale_enabled(self, value):
        """Sets whether the scene scale option is enabled.

        Args:
            value (bool): Whether scene scale should be set during execution.
        """
        self.task.settings["set_scene_scale"] = bool(value)
        self.refresh_scene_option_enabled_state()

    def set_scene_up_axis_enabled(self, value):
        """Sets whether the scene up-axis option is enabled.

        Args:
            value (bool): Whether scene up axis should be set during execution.
        """
        self.task.settings["set_scene_up_axis"] = bool(value)
        self.refresh_scene_option_enabled_state()

    def refresh_scene_option_enabled_state(self):
        """Refreshes enabled states for optional Maya scene controls."""
        if self.framerate_spin_box:
            self.framerate_spin_box.setEnabled(bool(self.task.settings.get("set_framerate")))
        if self.scene_scale_combo_box:
            self.scene_scale_combo_box.setEnabled(bool(self.task.settings.get("set_scene_scale")))
        if self.up_axis_combo_box:
            self.up_axis_combo_box.setEnabled(bool(self.task.settings.get("set_scene_up_axis")))

    def add_post_script_section(self):
        """Adds the collapsed optional post-script section."""
        collapsed = bool(self.task.settings.get("post_script_collapsed", True))
        section = self.add_collapsible_section(
            label_text="Post Script",
            collapsed=collapsed,
            state_setter=partial(self.set_task_setting, key="post_script_collapsed"),
            tooltip="Optional Python cleanup script that runs after importing/opening and before writing output.",
        )
        layout = section.get("content_layout")
        post_layout = ui_qt.QtWidgets.QHBoxLayout()
        post_layout.setContentsMargins(0, 0, 0, 5)
        self.add_checkbox(
            "Run",
            self.task.settings.get("run_post_script"),
            partial(self.set_task_setting, key="run_post_script"),
            layout=post_layout,
            tooltip="Run the configured post-import Python script.",
        )
        self.add_checkbox(
            "Pass Task Args",
            self.task.settings.get("post_script_pass_standard_arguments", True),
            partial(self.set_task_setting, key="post_script_pass_standard_arguments"),
            layout=post_layout,
            tooltip="Expose input, output, project, task, and related values as arguments and args.",
        )
        self.add_checkbox(
            "Pass Env",
            self.task.settings.get("post_script_pass_environment_arguments", True),
            partial(self.set_task_setting, key="post_script_pass_environment_arguments"),
            layout=post_layout,
            tooltip="Expose project environment variables as environment_variables and env.",
        )
        post_layout.addStretch()
        layout.addLayout(post_layout)
        editor = InlinePythonEditorWidget(
            parent=self,
            owner=self,
            text=self.task.settings.get("post_script_text") or task_maya_import.DEFAULT_POST_SCRIPT_TEXT,
            placeholder=task_maya_import.DEFAULT_POST_SCRIPT_TEXT,
            tooltip=(
                "Inline Python cleanup pass executed after Import/Open Maya loads the file and before output is "
                "written. Use context, arguments/args, environment_variables/env, project, task, work_item, "
                "output_path, and imported_nodes."
            ),
            text_changed_callback=partial(self.set_task_setting, key="post_script_text"),
            font_size=self.task.settings.get("post_script_font_size") or 14,
            font_size_changed_callback=partial(self.set_task_setting, key="post_script_font_size"),
        )
        layout.addWidget(editor)
