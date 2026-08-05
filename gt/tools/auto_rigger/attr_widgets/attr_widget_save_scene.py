"""
Auto Rigger Save Scene Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleSaveScene(AttrWidget):
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
        self.add_widget_separator_line(label_text="Save Scene Preferences")
        self.add_module_attr_widget_path(attr_name="file_path", dir_only=True)
        file_extensions = [".ma", ".mb"]
        self.add_module_attr_widget_combobox(attr_name="file_extension", items=file_extensions)
        # --------------------------------- Utilities ---------------------------------
        self.add_widget_separator_line(label_text="Utilities")
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        save_btn = ui_qt.QtWidgets.QPushButton("Save Scene")
        save_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        save_btn.clicked.connect(self.save_scene_utility)
        save_btn.setToolTip("Saves the current scene.")
        _layout.addWidget(save_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_save_dir_utility)
        open_dir_btn.setToolTip("Opens the thumbnail directory.")
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

    def save_scene_utility(self):
        """Saves the scene using current preferences"""
        self.module.force_save_scene()

    def open_save_dir_utility(self):
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


# Capture Base (Used by other AttrWidgets)
