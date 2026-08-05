"""
Auto Rigger Skin Weights Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModuleSkinWeights(AttrWidget):
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

        self.add_widget_separator_line(label_text="Skin Weights Preferences")

        self.add_module_attr_widget_path(attr_name="influences_dir", dir_only=True)
        self.add_module_attr_widget_path(attr_name="weights_dir", dir_only=True)

        # Preferences
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        self.remove_unused_infl_chk = self.add_module_attr_widget_checkbox(
            attr_name="remove_unused_influences", layout=_layout
        )

        self.clear_target_dir_chk = self.add_module_attr_widget_checkbox(
            attr_name="clear_target_dir", nice_name="Clear Target Directory When Writing", layout=_layout
        )
        self.scroll_content_layout.addLayout(_layout)

        self.add_widget_separator_line(label_text="Utilities")

        # Useful Buttons
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        import_file_btn = ui_qt.QtWidgets.QPushButton("Open Influences Directory")
        import_file_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        import_file_btn.clicked.connect(self.open_influence_dir)
        _layout.addWidget(import_file_btn)
        open_dir_btn = ui_qt.QtWidgets.QPushButton("Open Weights Directory")
        open_dir_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.util_open_dir))
        open_dir_btn.clicked.connect(self.open_weights_dir)
        _layout.addWidget(open_dir_btn)
        self.scroll_content_layout.addLayout(_layout)

        self.add_widget_read_write_buttons()

    def open_influence_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.influences_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing file. Path: "{str(_parsed_path)}".')
            return
        if not _parsed_path or _parsed_path == "." or not os.path.exists(_parsed_path):
            logger.warning(f'Unable to open missing path: "{str(_parsed_path)}".')
            return
        utils_system.open_file_dir(_parsed_path)

    def open_weights_dir(self):
        """Opens the file path directory"""
        _parsed_path = self.module.parse_path(path=self.module.weights_dir)
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
        write_influences = ui_qt.QtWidgets.QPushButton("Write Influences")
        write_influences.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_influences.clicked.connect(self.write_influences)
        write_influences.setToolTip("Write Influences From Selection")
        # Weights
        write_weights = ui_qt.QtWidgets.QPushButton("Write Weights")
        write_weights.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.library_build))
        write_weights.clicked.connect(self.write_weights)
        write_weights.setToolTip("Write Weights From Selection")
        # Layout
        _layout.addWidget(write_influences)
        _layout.addWidget(write_weights)
        self.scroll_content_layout.addLayout(_layout)

    def write_influences(self):
        """Writes influences to set directory"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_influences_from_selection(clear_target_dir=clear_target_dir)

    def write_weights(self):
        """Writes weights to set directory"""
        clear_target_dir = self.clear_target_dir_chk.isChecked()
        self.module.write_weights_from_selection(
            clear_target_dir=clear_target_dir,
            remove_unused_inf=self.remove_unused_infl_chk.isChecked(),
        )

    def set_module_remove_unused_influences(self):
        """Sets the checkbox remove unused influences user choice into the module variable."""
        self.module.set_remove_unused_influences(status=self.remove_unused_infl_chk.isChecked())
