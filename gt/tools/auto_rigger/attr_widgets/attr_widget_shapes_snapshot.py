"""
Auto Rigger Shapes Snapshot Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleShapesSnapshot(AttrWidget):
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
        self.add_widget_separator_line(label_text="Shapes Snapshot Preferences")
        # Purge Directory?
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        checkbox_label = ui_qt.QtWidgets.QLabel("Clear Target Directory When Writing: ")
        self.clear_target_dir_chk = ui_qt.QtWidgets.QCheckBox()
        self.clear_target_dir_chk.setChecked(False)
        _layout.addWidget(checkbox_label)
        _layout.addWidget(self.clear_target_dir_chk)
        self.scroll_content_layout.addLayout(_layout)

        self.add_module_attr_widget_path(attr_name="shapes_dir", dir_only=True)
        self.add_widget_read_write_buttons()

        # Useful Buttons
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        import_file_btn = ui_qt.QtWidgets.QPushButton("Open Shapes Directory")
        import_file_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        import_file_btn.clicked.connect(self.open_shapes_dir)
        _layout.addWidget(import_file_btn)
        self.content_layout.addLayout(_layout)

    def open_shapes_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.shapes_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing file. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)

    def add_widget_read_write_buttons(self):
        """
        Adds actions buttons (read proxy, build proxy, etc…)
        """
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        # Influences
        write_project_controls = ui_qt.QtWidgets.QPushButton("Write Project Controls")
        write_project_controls.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_project_controls.clicked.connect(self.write_project_controls)
        write_project_controls.setToolTip("Write Project Controls")
        # Weights
        write_selected_curves = ui_qt.QtWidgets.QPushButton("Write Curves From Selection")
        write_selected_curves.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_selected_curves.clicked.connect(self.write_selected_curves)
        write_selected_curves.setToolTip("Write Curves From Selection")
        # Layout
        _layout.addWidget(write_project_controls)
        _layout.addWidget(write_selected_curves)
        self.scroll_content_layout.addLayout(_layout)

    def write_project_controls(self):
        """Writes the shapes of the project controls"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_project_shapes(clear_target_dir=clear_target_dir)

    def write_selected_curves(self):
        """Writes the shapes of the selected objects"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_shapes_from_selection(clear_target_dir=clear_target_dir)
