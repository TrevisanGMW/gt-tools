"""
Auto Rigger Playblast Capture Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_capture_base import *

class AttrWidgetModulePlayblastCapture(AttrWidgetModuleBaseCapture):
    def __init__(self, parent=None, *args, **kwargs):
        """
        Initialize the attribute widget for the module described in its name.
        Args:
            parent (QWidget, optional): The parent widget for this attribute widget.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()
        self.add_widget_separator_line(label_text="Playblast Capture Preferences")
        self.add_module_attr_widget_path(attr_name="file_path", dir_only=True)
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        import gt.core.playblast as core_playblast

        video_formats = core_playblast.ViewportPlayblastFormats.get_all_formats()
        combobox_format = self.add_module_attr_widget_combobox(
            attr_name="video_format", items=video_formats, layout=_layout
        )
        combobox_format.setMinimumWidth(150)

        # Resolution (Width and Height)
        _min = 1
        _max = 7680
        _spinbox_min_width = 150
        _layout.addStretch()
        spinbox_width = self.add_module_attr_widget_int_spinbox(
            attr_name="width",
            min_int=_min,
            max_int=_max,
            tooltip="Width refers to the horizontal measurement of a video's resolution, measured in pixels",
            layout=_layout,
        )
        _layout.addStretch()
        spinbox_height = self.add_module_attr_widget_int_spinbox(
            attr_name="height",
            min_int=_min,
            max_int=_max,
            tooltip="Height refers to the vertical measurement of a video's resolution, measured in pixels",
            layout=_layout,
        )
        spinbox_width.setMinimumWidth(_spinbox_min_width)
        spinbox_height.setMinimumWidth(_spinbox_min_width)

        # Start and End Frames
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        label = ui_qt.QtWidgets.QLabel("Frame Range:")
        label.setMinimumWidth(260)
        _layout.addWidget(label)
        _layout.addStretch()
        spinbox_start = self.add_module_attr_widget_int_spinbox(
            attr_name="start_frame",
            nice_name="Start",
            tooltip="Determines the frame when the playblast should start.",
            layout=_layout,
        )
        _layout.addStretch()
        spinbox_end = self.add_module_attr_widget_int_spinbox(
            attr_name="end_frame",
            nice_name="End",
            tooltip="Determines the frame when the playblast should end.",
            layout=_layout,
        )
        spinbox_start.setMinimumWidth(_spinbox_min_width)
        spinbox_end.setMinimumWidth(_spinbox_min_width)

        self.add_widget_separator_line(label_text="Viewport Panel Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_checkbox(
            attr_name="show_ornaments",
            tooltip="When True, the playblast will include HUD elements such as the grid, camera name, and other info.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="default_material",
            tooltip="When True, a default material will override all used materials. No textures or colors.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="x_ray",
            tooltip="When True, X-Ray mode is activated during the playblast.",
            layout=_layout,
        )
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_checkbox(
            attr_name="wireframe_on_shaded",
            tooltip="When Wireframe on Shaded is true, meshes show their wireframe even when shaded and not selected.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="hide_curves",
            tooltip="When true, NURBS Curves are made invisible in the active panel during recording.\n"
            "This option does not affect the actual visibility of the objects, only the panel preference.\n"
            "The original value is restored after the playblast recording is saved.",
            layout=_layout,
        )

        self.add_widget_separator_line(label_text="Persp Camera Data")
        self.add_persp_camera_data_buttons()
        self.refresh_camera_buttons_enabled_state()

        # Utilities -----------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Utilities")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        capture_btn = ui_qt.QtWidgets.QPushButton("Capture Playblast")
        capture_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_module_playblast_capture))
        capture_btn.clicked.connect(self.capture_playblast)
        capture_btn.setToolTip("Captures a playblast using the current settings.")
        _layout.addWidget(capture_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_playblast_dir)
        open_dir_btn.setToolTip("Opens the playblast directory.")
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

    def capture_playblast(self):
        """Captures a thumbnail using the current settings"""
        self.module.capture_playblast()

    def open_playblast_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.file_path)
        _parsed_path = os.path.dirname(_parsed_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing directory. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)
