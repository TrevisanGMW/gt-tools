"""
Batch Processor Capture Task Widgets
"""

from gt.tools.batch_processor.widgets.attr_widget_task import AttrWidgetTask
import gt.ui.qt_import as ui_qt
from functools import partial


class AttrWidgetThumbnailCaptureTask(AttrWidgetTask):
    """Attribute widget for thumbnail capture."""

    def __init__(self, parent=None, task=None, project=None, refresh_parent_func=None, *args, **kwargs):
        """Initializes the thumbnail capture widget.

        Args:
            parent (QWidget, optional): Parent widget.
            task (TaskCaptureThumbnail, optional): Task model.
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
            task (TaskCapturePlayblast, optional): Task model.
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
