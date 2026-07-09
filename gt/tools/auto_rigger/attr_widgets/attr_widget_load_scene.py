"""
Auto Rigger Load Scene Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleLoadScene(AttrWidget):
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
        self.add_widget_separator_line(label_text="Load Scene Preferences")
        self.add_module_attr_widget_path(attr_name="file_path", dir_only=False)
        # Utilities
        self.add_widget_separator_line(label_text="Utilities")

        # Useful Buttons
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        import_file_btn = ui_qt.QtWidgets.QPushButton("Load Scene")
        import_file_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_module_import_file))
        import_file_btn.clicked.connect(self.module.force_load_scene)
        _layout.addWidget(import_file_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open File Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_file_dir)
        _layout.addWidget(open_dir_btn)
        self.content_layout.addLayout(_layout)

        # Warning
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(_layout)
        _tooltip = (
            "When enabled, this module will suppress warnings for files loaded from outside the rig project "
            "path.\nThis is useful when the project is based on another rig project and changes need to be "
            "quickly propagated."
        )
        _layout.addStretch()
        self.add_module_attr_widget_checkbox(
            attr_name="bypass_warnings", nice_name="Suppress External File Warnings", tooltip=_tooltip, layout=_layout
        )
        _layout.addStretch()

    def open_file_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.file_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing file. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)
