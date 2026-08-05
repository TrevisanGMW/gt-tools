"""
Auto Rigger Camera Setup Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_capture_base import *

class AttrWidgetModuleCameraSetup(AttrWidgetModuleBaseCapture):
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
        self.add_widget_separator_line(label_text="Camera Setup Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        _layout.addStretch()
        cam_name_text_field = self.add_module_attr_widget_text_field(
            attr_name="camera_name",
            placeholder='camera path/name. e.g. "persp"',
            tooltip='This is the name of the camera affected by the operation. Often "persp".',
            layout=_layout,
        )
        cam_name_text_field.setMinimumWidth(300)
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="view_through_camera",
            tooltip="When True, the provided camera becomes the active camera of the current viewport.",
            layout=_layout,
        )
        _layout.addStretch()

        self.add_persp_camera_data_buttons(label="Camera Data:")
        self.refresh_camera_buttons_enabled_state()

        self.add_widget_separator_line(label_text="Viewport Panel Preferences")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="default_material",
            tooltip="When True, a default material will override all used materials. No textures or colors.",
            layout=_layout,
        )
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="x_ray",
            tooltip="When True, X-Ray mode is activated during the playblast.",
            layout=_layout,
        )
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="wireframe_on_shaded",
            tooltip="When Wireframe on Shaded is true, meshes show their wireframe even when shaded and not selected.",
            layout=_layout,
        )
        _layout.addStretch()
