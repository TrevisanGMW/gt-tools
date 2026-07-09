"""
Auto Rigger Thumbnail Capture Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_capture_base import *

class AttrWidgetModuleThumbnailCapture(AttrWidgetModuleBaseCapture):
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
        self.add_widget_separator_line(label_text="Thumbnail Capture Preferences")
        self.add_module_attr_widget_path(attr_name="file_path", dir_only=True)
        import gt.core.playblast as core_playblast

        file_extensions = core_playblast.ViewportImageFormats.get_all_formats()
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        self.add_module_attr_widget_combobox(attr_name="file_extension", items=file_extensions, layout=_layout)

        # Resolution (Width and Height)
        _min = 1
        _max = 7680
        self.add_module_attr_widget_int_spinbox(
            attr_name="width",
            min_int=_min,
            max_int=_max,
            tooltip="Width refers to the horizontal measurement of a video's resolution, measured in pixels",
            layout=_layout,
        )
        self.add_module_attr_widget_int_spinbox(
            attr_name="height",
            min_int=_min,
            max_int=_max,
            tooltip="Height refers to the vertical measurement of a video's resolution, measured in pixels",
            layout=_layout,
        )

        # Frame ------------------------------------------------
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        current_frame_checkbox = self.add_module_attr_widget_checkbox(attr_name="current_frame", layout=_layout)
        _layout.addStretch()
        self.frame_spinbox = self.add_module_attr_widget_int_spinbox(attr_name="frame", layout=_layout)
        current_frame_checkbox.toggled.connect(self.on_current_frame_checkbox_toggled)
        # Disable Spinbox if using current frame
        if self.module.current_frame:
            self.frame_spinbox.setEnabled(False)
        _layout.addStretch()

        self.add_widget_separator_line(label_text="Viewport Panel Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
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
        self.add_module_attr_widget_checkbox(
            attr_name="wireframe_on_shaded",
            tooltip="When Wireframe on Shaded is true, meshes show their wireframe even when shaded and not selected.",
            layout=_layout,
        )
        self.add_module_attr_widget_checkbox(
            attr_name="hide_curves",
            tooltip="When true, NURBS Curves are made invisible in the active panel for the thumbnail.\n"
            "This option does not affect the actual visibility of the objects, only the panel preference.\n"
            "The original value is restored after the thumbnail is saved.",
            layout=_layout,
        )

        self.add_widget_separator_line(label_text="Persp Camera Data")
        self.add_persp_camera_data_buttons()
        self.refresh_camera_buttons_enabled_state()

        # ---------------------------------- Utilities ----------------------------------
        self.add_widget_separator_line(label_text="Utilities")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        capture_btn = ui_qt.QtWidgets.QPushButton("Capture Thumbnail")
        capture_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_module_thumbnail_capture))
        capture_btn.clicked.connect(self.capture_thumbnail)
        capture_btn.setToolTip("Captures a thumbnail using the current settings.")
        _layout.addWidget(capture_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_thumbnail_dir)
        open_dir_btn.setToolTip("Opens the thumbnail directory.")
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

    def capture_thumbnail(self):
        """Captures a thumbnail using the current settings"""
        self.module.capture_thumbnail()

    def open_thumbnail_dir(self):
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

    def on_current_frame_checkbox_toggled(self, checked):
        """
        Handles checkbox toggling: disables spinbox if checked, enables if unchecked.
        Args:
            checked (bool): The state of the checkbox.
                            True if checked (spinbox should be disabled),
                            False if unchecked (spinbox should be enabled).
        """
        self.frame_spinbox.setEnabled(not checked)

    def on_add_metadata_toggled(self, state):
        """
        Enable or disable the metadata path QLineEdit based on the checkbox state.

        Args:
            state (int): The state of the checkbox.
                         The QLineEdit will be enabled only when the checkbox is checked.
        """
        self.asset_data_path_widget.setEnabled(state == ui_qt.QtLib.CheckState.Checked)
