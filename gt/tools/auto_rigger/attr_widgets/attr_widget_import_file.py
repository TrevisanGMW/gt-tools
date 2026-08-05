"""
Auto Rigger Import File Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleImportFile(AttrWidget):
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

        self.add_widget_separator_line(label_text="Import File Preferences")

        self.add_module_attr_widget_path(attr_name="file_path")
        ignore_attrs = [
            "file_path",
            "merge_namespaces_on_clash",
            "reference",
            "deactivate_drawing_overrides",
            "purge_display_layers",
            "purge_namespaces",
            "purge_keyframes",
            "proxy_import",
        ]
        self.add_widget_auto_serialized_fields(ignore_attrs=ignore_attrs)

        # Create and Add Layout Checkbox Layouts
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_checkbox(attr_name="merge_namespaces_on_clash", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="reference", layout=_layout)
        _tooltip = (
            'If active, the import function will also take place when entering in "Edit Proxy" mode.\n'
            "This happens independently of the order settings, and only happens when editing the proxy.\n"
            "The imported elements are automatically parented to a reference group for convenience.\n"
            "This option allows for one import module to simultaneously align proxies and bind of the skin weights."
        )
        self.add_module_attr_widget_checkbox(attr_name="proxy_import", layout=_layout, tooltip=_tooltip)
        self.content_layout.addLayout(_layout)

        self.add_widget_separator_line(label_text="Extra Module Features")

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_checkbox(attr_name="deactivate_drawing_overrides", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="purge_display_layers", layout=_layout)
        self.content_layout.addLayout(_layout)

        _layout = ui_qt.QtWidgets.QHBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 5)  # L-T-R-B
        self.add_module_attr_widget_checkbox(attr_name="purge_namespaces", layout=_layout)
        self.add_module_attr_widget_checkbox(attr_name="purge_keyframes", layout=_layout)
        self.content_layout.addLayout(_layout)

        self.add_widget_separator_line(label_text="Utilities")
        # Useful Buttons
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        import_file_btn = ui_qt.QtWidgets.QPushButton("Import File")
        import_file_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.rigger_module_import_file))
        import_file_btn.clicked.connect(self.module.import_file)
        _layout.addWidget(import_file_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open File Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_file_dir)
        _layout.addWidget(open_dir_btn)
        self.content_layout.addLayout(_layout)

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
