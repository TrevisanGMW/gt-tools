"""
Batch Processor Maya Batch Render Task Attribute Widget
"""

from gt.tools.batch_processor.tasks import task_batch_render
from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.resource_library as ui_res_lib
import gt.ui.qt_import as ui_qt
from functools import partial


MAYA_RENDER_TOKENS = [
    ("Insert scene name", "<Scene>"),
    ("Insert camera name", "<Camera>"),
    ("Insert render layer name", "<RenderLayer>"),
    ("Insert render pass name", "<RenderPass>"),
    ("Insert version label", "<Version>"),
    ("Insert extension", "<Extension>"),
]

BATCH_TOKENS = [
    ("Insert incoming file name", "{name}"),
    ("Insert incoming file extension", "{ext}"),
    ("Insert task name", "{task-name}"),
    ("Insert date (YYYYMMDD)", "{date}"),
]


class AttrWidgetBatchRenderTask(AttrWidgetTask):
    """Attribute widget for the Maya batch render task."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the batch render task widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskBatchRender, optional): Task model.
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
        self.prefix_field = None
        self.prefix_menu = None
        self.project_mode_combo = None
        self.project_path_widgets = None
        self.override_widgets = {}
        self.override_checkboxes = {}
        self.add_common_task_settings()
        self.add_render_output_section()
        self.add_maya_project_section()
        self.add_render_override_section()
        self.add_renderer_section()
        self.content_layout.addStretch()

    def add_render_output_section(self):
        """Adds the render output redirection controls."""
        self.add_widget_separator_line(
            label_text="Render Output",
            tooltip="Where rendered images are written and how they are named.",
        )
        self.add_checkbox(
            "Folder Per File",
            self.task.settings.get("create_folder_per_file", True),
            partial(self.set_task_setting, key="create_folder_per_file"),
            tooltip=(
                "Create a subfolder named after each incoming scene inside the target path "
                "so renders from different scenes are not mixed together."
            ),
        )
        tooltip = (
            "File name prefix used during the render. Leave empty to keep the prefix already "
            "stored in each incoming scene."
        )
        layout = self.add_labeled_layout("File Name Prefix", tooltip=tooltip)
        self.prefix_field = self.create_text_field(
            text=self.task.settings.get("file_name_prefix"),
            placeholder="Keep scene prefix",
            tooltip=tooltip,
        )
        self.prefix_field.textChanged.connect(partial(self.set_task_setting, key="file_name_prefix"))
        layout.addWidget(self.prefix_field)
        token_button = ui_qt.QtWidgets.QPushButton()
        token_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_arrow_down))
        token_button.setToolTip("Insert a render or batch token into the file name prefix.")
        token_button.clicked.connect(partial(self.show_prefix_token_menu, button=token_button))
        layout.addWidget(token_button)

    def add_maya_project_section(self):
        """Adds the optional Maya project controls."""
        self.add_widget_separator_line(
            label_text="Maya Project",
            tooltip="Optional Maya project applied to the render process.",
        )
        self.add_checkbox(
            "Set Project",
            self.task.settings.get("set_project", True),
            self.set_project_enabled,
            tooltip=(
                "Pass a Maya project to the renderer. Keeping the project consistent lets scenes "
                "resolve relative textures, references, and caches during batch renders."
            ),
        )
        self.project_mode_combo = self.add_combo_box(
            "Project Mode",
            self.task.settings.get("project_mode"),
            task_batch_render.PROJECT_MODES,
            self.set_project_mode,
            tooltip=(
                "Auto searches upward from each incoming scene for a workspace.mel file. "
                "Custom Path always uses the project folder set below."
            ),
        )
        self.project_path_widgets = self.add_path_template_field(
            "Project Path",
            self.task.settings.get("project_path"),
            partial(self.set_task_setting, key="project_path"),
            placeholder="{project-dir}/maya_project",
            tooltip="Maya project folder used when Project Mode is set to Custom Path.",
            dir_only=True,
            return_widgets=True,
        )
        self.refresh_project_controls()

    def add_render_override_section(self):
        """Adds the optional render setting overrides."""
        self.add_widget_separator_line(
            label_text="Render Setting Overrides",
            tooltip=(
                "Incoming scenes are expected to be pre-configured. Enable an override to replace "
                "one of these renderer-agnostic settings at render time."
            ),
        )
        self.add_resolution_override()
        self.add_frame_range_override()
        self.add_camera_override()
        self.add_image_format_override()
        self.add_version_label_override()
        self.add_checkbox(
            "Skip Existing Frames",
            self.task.settings.get("skip_existing_frames", False),
            partial(self.set_task_setting, key="skip_existing_frames"),
            tooltip="Ask the renderer to skip frames that already exist on disk. Useful for resuming a run.",
        )

    def add_resolution_override(self):
        """Adds the resolution override row."""
        tooltip = "Override the rendered image resolution."
        layout = self.add_labeled_layout("Resolution", tooltip=tooltip)
        checkbox = self.add_override_checkbox(layout, "override_resolution", tooltip)
        self.add_row_label(layout, "Width")
        width_spin = self.create_int_spin_box(
            self.task.settings.get("width"),
            partial(self.set_task_setting, key="width"),
            maximum=32768,
        )
        layout.addWidget(width_spin)
        self.add_row_label(layout, "Height")
        height_spin = self.create_int_spin_box(
            self.task.settings.get("height"),
            partial(self.set_task_setting, key="height"),
            maximum=32768,
        )
        layout.addWidget(height_spin)
        layout.addStretch()
        self.register_override_widgets(checkbox, "override_resolution", [width_spin, height_spin])

    def add_frame_range_override(self):
        """Adds the frame range override row."""
        tooltip = "Override the rendered frame range and frame step."
        layout = self.add_labeled_layout("Frame Range", tooltip=tooltip)
        checkbox = self.add_override_checkbox(layout, "override_frame_range", tooltip)
        self.add_row_label(layout, "Start")
        start_spin = self.create_int_spin_box(
            self.task.settings.get("start_frame"),
            partial(self.set_task_setting, key="start_frame"),
            minimum=-1000000,
            maximum=1000000,
        )
        layout.addWidget(start_spin)
        self.add_row_label(layout, "End")
        end_spin = self.create_int_spin_box(
            self.task.settings.get("end_frame"),
            partial(self.set_task_setting, key="end_frame"),
            minimum=-1000000,
            maximum=1000000,
        )
        layout.addWidget(end_spin)
        self.add_row_label(layout, "Step")
        step_spin = self.create_int_spin_box(
            self.task.settings.get("frame_step"),
            partial(self.set_task_setting, key="frame_step"),
            maximum=1000,
        )
        layout.addWidget(step_spin)
        layout.addStretch()
        self.register_override_widgets(checkbox, "override_frame_range", [start_spin, end_spin, step_spin])

    def add_camera_override(self):
        """Adds the renderable camera override row."""
        tooltip = "Override the camera used for the render."
        layout = self.add_labeled_layout("Camera", tooltip=tooltip)
        checkbox = self.add_override_checkbox(layout, "override_camera", tooltip)
        camera_field = self.create_text_field(
            text=self.task.settings.get("camera_name"),
            placeholder="persp",
            tooltip="Camera transform or shape name rendered in every incoming scene.",
        )
        camera_field.textChanged.connect(partial(self.set_task_setting, key="camera_name"))
        layout.addWidget(camera_field)
        self.register_override_widgets(checkbox, "override_camera", [camera_field])

    def add_image_format_override(self):
        """Adds the image format and frame padding override rows."""
        format_tooltip = "Override the output image format."
        layout = self.add_labeled_layout("Image Format", tooltip=format_tooltip)
        format_checkbox = self.add_override_checkbox(layout, "override_image_format", format_tooltip)
        format_combo = self.create_row_combo_box(
            self.task.settings.get("image_format"),
            task_batch_render.IMAGE_FORMATS,
            tooltip=format_tooltip,
        )
        format_combo.currentTextChanged.connect(partial(self.set_task_setting, key="image_format"))
        layout.addWidget(format_combo)
        padding_tooltip = "Override the number of digits used by the frame number extension."
        self.add_row_label(layout, "Padding", tooltip=padding_tooltip)
        padding_checkbox = ui_qt.QtWidgets.QCheckBox()
        padding_checkbox.setMinimumHeight(padding_checkbox.sizeHint().height() + 2)
        padding_checkbox.setChecked(bool(self.task.settings.get("override_frame_padding")))
        padding_checkbox.setToolTip(padding_tooltip)
        layout.addWidget(padding_checkbox)
        padding_spin = self.create_int_spin_box(
            self.task.settings.get("frame_padding"),
            partial(self.set_task_setting, key="frame_padding"),
            maximum=12,
        )
        layout.addWidget(padding_spin)
        layout.addStretch()
        self.register_override_widgets(format_checkbox, "override_image_format", [format_combo])
        self.register_override_widgets(padding_checkbox, "override_frame_padding", [padding_spin])

    def add_version_label_override(self):
        """Adds the version label override row."""
        tooltip = (
            "Override the render version label. The label is applied to the scene render globals "
            "before rendering and is used by the <Version> token."
        )
        layout = self.add_labeled_layout("Version Label", tooltip=tooltip)
        checkbox = self.add_override_checkbox(layout, "override_version_label", tooltip)
        version_field = self.create_text_field(
            text=self.task.settings.get("version_label"),
            placeholder="v001",
            tooltip=tooltip,
        )
        version_field.textChanged.connect(partial(self.set_task_setting, key="version_label"))
        layout.addWidget(version_field)
        self.register_override_widgets(checkbox, "override_version_label", [version_field])

    def add_renderer_section(self):
        """Adds the renderer process controls."""
        section = self.add_collapsible_section(
            "Renderer Process",
            collapsed=self.task.settings.get("renderer_section_collapsed", True),
            state_setter=partial(self.set_task_setting, key="renderer_section_collapsed"),
            tooltip="Advanced controls for the Maya command-line renderer process.",
        )
        section_layout = section.get("content_layout")
        self.add_path_template_field(
            "Renderer Path",
            self.task.settings.get("render_executable"),
            partial(self.set_task_setting, key="render_executable"),
            placeholder=self.get_detected_renderer_path() or "Auto-detected Maya renderer",
            tooltip=(
                "Optional path to Maya's command-line renderer. Leave empty to detect it from the "
                "worker Maya installation."
            ),
            parent_layout=section_layout,
        )
        self.add_text_field(
            "Maya Version",
            self.task.settings.get("maya_version"),
            partial(self.set_task_setting, key="maya_version"),
            placeholder="2025",
            tooltip="Optional Maya version used to locate the renderer when no explicit path is set.",
            parent_layout=section_layout,
        )
        self.add_text_field(
            "Extra Arguments",
            self.task.settings.get("extra_arguments"),
            partial(self.set_task_setting, key="extra_arguments"),
            placeholder="-rl all",
            tooltip=(
                "Extra command-line arguments appended to the renderer call. Use this for render "
                "layers or renderer-specific flags."
            ),
            parent_layout=section_layout,
        )
        self.add_spin_box(
            "Timeout (Minutes)",
            self.task.settings.get("timeout_minutes"),
            partial(self.set_task_setting, key="timeout_minutes"),
            minimum=0,
            maximum=10080,
            tooltip="Maximum render duration per scene. Use 0 to wait indefinitely.",
            parent_layout=section_layout,
        )
        options_layout = self.add_labeled_layout(
            "Options",
            tooltip="Renderer process options.",
            parent_layout=section_layout,
        )
        self.add_checkbox(
            "Frame Progress",
            self.task.settings.get("report_frame_progress", True),
            partial(self.set_task_setting, key="report_frame_progress"),
            layout=options_layout,
            tooltip=(
                "Report each rendered frame to the tracker progress bar and job log. "
                "Disable for very long frame ranges to keep logs short."
            ),
        )
        self.add_checkbox(
            "Require Images",
            self.task.settings.get("require_rendered_files", True),
            partial(self.set_task_setting, key="require_rendered_files"),
            layout=options_layout,
            tooltip="Fail the task when the renderer finishes without creating any images.",
        )
        self.add_checkbox(
            "Write Log",
            self.task.settings.get("write_process_log", True),
            partial(self.set_task_setting, key="write_process_log"),
            layout=options_layout,
            tooltip="Write the renderer output to a log file in the project log folder.",
        )
        options_layout.addStretch()

    def add_override_checkbox(self, layout, key, tooltip):
        """Adds an override checkbox to a settings row.

        Args:
            layout (QHBoxLayout): Row layout that receives the checkbox.
            key (str): Override setting key.
            tooltip (str): Checkbox tooltip.

        Returns:
            QCheckBox: Created checkbox.
        """
        checkbox = ui_qt.QtWidgets.QCheckBox()
        checkbox.setMinimumHeight(checkbox.sizeHint().height() + 2)
        checkbox.setChecked(bool(self.task.settings.get(key)))
        checkbox.setToolTip(tooltip)
        layout.addWidget(checkbox)
        return checkbox

    def register_override_widgets(self, checkbox, key, widgets):
        """Binds an override checkbox to the widgets it controls.

        Args:
            checkbox (QCheckBox): Override checkbox.
            key (str): Override setting key.
            widgets (list): Widgets enabled only while the override is active.
        """
        self.override_widgets[key] = widgets
        self.override_checkboxes[key] = checkbox
        checkbox.stateChanged.connect(partial(self.set_override_enabled, key=key, checkbox=checkbox))
        self.refresh_override_widgets(key, checkbox.isChecked())

    def set_override_enabled(self, *args, key=None, checkbox=None):
        """Stores an override state and refreshes the widgets it controls.

        Args:
            *args: Signal arguments.
            key (str, optional): Override setting key.
            checkbox (QCheckBox, optional): Override checkbox.
        """
        is_enabled = bool(checkbox.isChecked()) if checkbox else False
        self.set_task_setting(is_enabled, key=key)
        self.refresh_override_widgets(key, is_enabled)

    def refresh_override_widgets(self, key, is_enabled):
        """Refreshes the enabled state of the widgets owned by an override.

        Args:
            key (str): Override setting key.
            is_enabled (bool): Whether the override is active.
        """
        for widget in self.override_widgets.get(key) or []:
            try:
                widget.setEnabled(bool(is_enabled))
            except RuntimeError:
                pass

    def set_project_enabled(self, is_enabled):
        """Stores the Maya project state and refreshes its controls.

        Args:
            is_enabled (bool): Whether a Maya project should be passed to the renderer.
        """
        self.set_task_setting(bool(is_enabled), key="set_project")
        self.refresh_project_controls()

    def set_project_mode(self, project_mode):
        """Stores the Maya project mode and refreshes its controls.

        Args:
            project_mode (str): Selected project mode.
        """
        self.set_task_setting(project_mode, key="project_mode")
        self.refresh_project_controls()

    def refresh_project_controls(self):
        """Refreshes the enabled state of the Maya project controls."""
        is_enabled = bool(self.task.settings.get("set_project", True))
        is_custom = (self.task.settings.get("project_mode") or "") == task_batch_render.PROJECT_MODE_CUSTOM
        try:
            if self.project_mode_combo:
                self.project_mode_combo.setEnabled(is_enabled)
            for widget_key, widget in (self.project_path_widgets or {}).items():
                if widget_key == "layout":
                    continue
                widget.setEnabled(is_enabled and is_custom)
        except RuntimeError:
            pass

    def show_prefix_token_menu(self, *args, button=None):
        """Shows the file name prefix token menu.

        Args:
            *args: Signal arguments.
            button (QPushButton, optional): Button used to position the menu.
        """
        self.prefix_menu = ui_qt.QtWidgets.QMenu(self)
        for label_text, token in MAYA_RENDER_TOKENS:
            action = self.prefix_menu.addAction("{0} {1}".format(label_text, token))
            action.triggered.connect(partial(self.insert_prefix_token, token=token))
        self.prefix_menu.addSeparator()
        for label_text, token in BATCH_TOKENS:
            action = self.prefix_menu.addAction("{0} {1}".format(label_text, token))
            action.triggered.connect(partial(self.insert_prefix_token, token=token))
        position = ui_qt.QtGui.QCursor.pos()
        if button:
            position = button.mapToGlobal(button.rect().bottomLeft())
        exec_menu(self.prefix_menu, position)

    def insert_prefix_token(self, *args, token=""):
        """Inserts a token at the current file name prefix cursor position.

        Args:
            *args: Signal arguments.
            token (str, optional): Token to insert.
        """
        if not self.prefix_field or not token:
            return
        self.prefix_field.insert(token)
        self.prefix_field.setFocus()

    @staticmethod
    def create_int_spin_box(value, setter, minimum=1, maximum=9999):
        """Creates an integer spin box used by the override rows.

        Args:
            value (object): Initial value.
            setter (callable): Setter callback.
            minimum (int, optional): Minimum value.
            maximum (int, optional): Maximum value.

        Returns:
            QSpinBox: Created spin box.
        """
        spin_box = ui_qt.QtWidgets.QSpinBox()
        spin_box.setRange(int(minimum), int(maximum))
        try:
            spin_box.setValue(int(value))
        except (TypeError, ValueError):
            spin_box.setValue(int(minimum))
        spin_box.setMinimumHeight(35)
        spin_box.setMinimumWidth(80)
        spin_box.valueChanged.connect(lambda value_int: setter(value_int))
        return spin_box

    def get_detected_renderer_path(self):
        """Gets the auto-detected Maya command-line renderer path.

        Returns:
            str: Renderer path, or an empty string when none was found.
        """
        try:
            return task_batch_render.find_render_executable(version=self.task.settings.get("maya_version"))
        except Exception:
            return ""


def exec_menu(menu, position):
    """Executes a Qt menu using the binding-compatible method name.

    Args:
        menu (QMenu): Menu to execute.
        position (QPoint): Global position used to show the menu.

    Returns:
        object: Selected action, or None.
    """
    exec_method = getattr(menu, "exec_", None)
    if not exec_method:
        exec_method = getattr(menu, "exec")
    return exec_method(position)
