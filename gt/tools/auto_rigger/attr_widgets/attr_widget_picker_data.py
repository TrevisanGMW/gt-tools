"""
Auto Rigger Picker Data Attribute Widget
"""

from gt.tools.auto_rigger.attr_widgets.attr_widget_base import *

class AttrWidgetModulePickerData(AttrWidget):
    """
    An attribute widget for managing a list of picker file paths.

    This widget provides a user interface to dynamically add, remove, and
    define string paths to picker data files (e.g., JSON). The data is stored
    in the associated module's `pickers` attribute as a list of strings.
    """

    def __init__(self, parent=None, *args, **kwargs):
        """
        Initializes the attribute widget for the picker data module.

        Args:
            parent (QWidget, optional): The parent widget for this attribute widget. Defaults to None.
            *args: Additional positional arguments passed to the base class.
            **kwargs: Additional keyword arguments passed to the base class.
        """
        super().__init__(parent, *args, **kwargs)

        self.add_widget_module_header()
        self.add_widget_code_data_editor()

        # Picker Section ---------------------------------------------------------------------------------------
        self.add_widget_separator_line(label_text="Picker Data")

        # "Add Picker" Button
        add_picker_button_layout = ui_qt.QtWidgets.QHBoxLayout()
        self.content_layout.addLayout(add_picker_button_layout)
        add_picker_button = ui_qt.QtWidgets.QPushButton("Add Picker")
        add_picker_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_add))
        add_picker_button.setToolTip("Adds a new picker path to the list.")
        add_picker_button.clicked.connect(self.on_add_picker_clicked)
        add_picker_button_layout.addWidget(add_picker_button)

        # Scroll Area for Picker Widgets
        self.picker_scroll_area = ui_qt.QtWidgets.QScrollArea()
        self.picker_scroll_area.setWidgetResizable(True)
        self.picker_scroll_area.setMinimumHeight(220)
        self.picker_container = ui_qt.QtWidgets.QWidget()
        self.picker_vertical_layout = ui_qt.QtWidgets.QVBoxLayout(self.picker_container)
        self.picker_vertical_layout.setContentsMargins(0, 0, 0, 0)
        self.picker_vertical_layout.setSpacing(8)
        self.picker_vertical_layout.setAlignment(ui_qt.QtLib.AlignmentFlag.AlignTop)
        self.picker_scroll_area.setWidget(self.picker_container)
        self.content_layout.addWidget(self.picker_scroll_area)

        # Write Button
        _layout = ui_qt.QtWidgets.QHBoxLayout()
        write_btn = ui_qt.QtWidgets.QPushButton("Write Picker Data to Scene")
        write_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_save))
        write_btn.setToolTip("Writes the picker data to the currently opened scene.")
        write_btn.clicked.connect(self.on_write_pickers_clicked)
        _layout.addWidget(write_btn)

        write_btn = ui_qt.QtWidgets.QPushButton("Clear Picker Data from Scene")
        write_btn.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        write_btn.setToolTip("Clears the picker data from the currently opened scene.")
        write_btn.clicked.connect(self.on_clear_pickers_clicked)
        _layout.addWidget(write_btn)
        self.content_layout.addLayout(_layout)

        # Initial Refresh to populate the UI
        self.refresh_current_widgets()

    # -----------------------------------
    # Interface Assembly
    # -----------------------------------

    def add_picker_widget(self, picker_path):
        """
        Creates and adds a new picker widget to the UI layout.

        This builds a framed widget containing a line edit for the file path,
        buttons for path parsing and file browsing, and a delete button.

        Args:
            picker_path (str): The initial path string for the picker file.
                               This can be an empty string for a new picker entry.
        """
        picker_frame = ui_qt.QtWidgets.QFrame()
        picker_frame.setFrameShape(ui_qt.QtWidgets.QFrame.Box)
        picker_layout = ui_qt.QtWidgets.QHBoxLayout(picker_frame)

        # Picker Path Widgets
        path_label = ui_qt.QtWidgets.QLabel("Picker Path:")
        path_line_edit = ui_qt_utils.ConfirmableQLineEdit(picker_path)
        path_line_edit.setPlaceholderText('Path to a picker file e.g. "humanoid_body.json"')

        show_parsed_path_button = ui_qt.QtWidgets.QPushButton()
        show_parsed_path_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_env_var))
        show_parsed_path_button.setToolTip("Shows the parsed path with environment variables resolved.")

        open_file_dialog_button = ui_qt.QtWidgets.QPushButton()
        open_file_dialog_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_open))
        open_file_dialog_button.setToolTip("Use file dialog to set path.")

        delete_button = ui_qt.QtWidgets.QPushButton()
        delete_button.setIcon(ui_qt.QtGui.QIcon(ui_res_lib.Icon.ui_trash))
        delete_button.setToolTip("Deletes this picker path.")

        # Assemble Layout
        picker_layout.addWidget(path_label)
        picker_layout.addWidget(path_line_edit)
        picker_layout.addWidget(show_parsed_path_button)
        picker_layout.addWidget(open_file_dialog_button)
        picker_layout.addWidget(delete_button)

        self.picker_vertical_layout.addWidget(picker_frame)

        # Connections
        path_line_edit.editingFinished.connect(self.commit_picker_data_to_module)

        # Connect path utility buttons (assuming handlers exist on base class)
        show_parsed_path_function = partial(self.open_env_var_feedback_dialog, field=path_line_edit)
        show_parsed_path_button.clicked.connect(show_parsed_path_function)

        # Connect to the new handler that also commits data
        open_dialog_function = partial(
            self._on_open_file_dialog_clicked,
            line_edit_widget=path_line_edit,
            file_filter="JSON Files (*.json);;All Files (*)",
        )
        open_file_dialog_button.clicked.connect(open_dialog_function)

        delete_function = partial(self.on_delete_picker_widget_clicked, to_delete=picker_frame)
        delete_button.clicked.connect(delete_function)

    # -----------------------------------
    # Refresh Functions
    # -----------------------------------

    def refresh_current_widgets(self):
        """
        Rebuilds the UI to match the module's current state.

        This function clears any existing picker widgets and then creates new ones
        based on the `self.module.pickers` list.
        """
        self._clear_layout(self.picker_vertical_layout)

        if not hasattr(self.module, "pickers"):
            self.module.pickers = []

        for picker_path in self.module.pickers:
            self.add_picker_widget(picker_path=picker_path)

    # -----------------------------------
    # Data Update Functions
    # -----------------------------------

    def get_picker_data_from_layout(self):
        """
        Extracts all picker path strings from the UI widgets.

        Iterates through the picker widgets in the layout, reads the text from
        each line edit, and returns them as a list of strings.

        Returns:
            list[str]: A list of picker path strings currently present in the UI.
        """
        picker_paths = []
        for index in range(self.picker_vertical_layout.count()):
            item = self.picker_vertical_layout.itemAt(index)
            widget = item.widget()
            if not widget:
                continue

            line_edit = widget.findChild(ui_qt.QtWidgets.QLineEdit)
            if line_edit:
                picker_paths.append(line_edit.text())
        return picker_paths

    def commit_picker_data_to_module(self):
        """
        Commits the current picker data from the UI back to the module instance.
        """
        self.module.pickers = self.get_picker_data_from_layout()

    # -----------------------------------
    # Event Handlers
    # -----------------------------------

    def _on_open_file_dialog_clicked(self, line_edit_widget, file_filter):
        """
        Handles the file dialog button click for a picker path.

        This opens the file dialog and, if a file is selected (which updates
        the line edit), it immediately commits the new data to the module.

        Args:
            line_edit_widget (ui_qt.QtWidgets.QLineEdit): The line edit widget to populate
                                                          with the selected file path.
            file_filter (str): The file filter string for the dialog.
        """
        self.open_module_attr_file_dialog(field=line_edit_widget, file_filter=file_filter)
        self.commit_picker_data_to_module()

    def on_add_picker_clicked(self):
        """
        Handles the "Add Picker" button click event.

        This adds a new, empty picker widget to the UI and then updates the module data.
        """
        self.add_picker_widget(picker_path="")
        self.commit_picker_data_to_module()

    def on_delete_picker_widget_clicked(self, to_delete):
        """
        Handles the deletion of a specific picker widget.

        Args:
            to_delete (QWidget): The picker widget (frame) to be removed.
        """
        self._remove_widget(to_delete)
        self.commit_picker_data_to_module()

    def on_write_pickers_clicked(self):
        """Adds picker data to the currently opened scene."""
        self.module.add_picker_data()

    @staticmethod
    def on_clear_pickers_clicked():
        """Removes picker data from the currently opened scene."""
        import maya.cmds as cmds

        _picker_data_nodes = cmds.ls("_dwpicker_data") or []
        if _picker_data_nodes:
            try:
                cmds.delete(_picker_data_nodes)
            except Exception as e:
                logger.warning(f"Unable to delete picker data. Issue: {e}")
            logger.info(f"{len(_picker_data_nodes)} picker data nodes were deleted.")
        else:
            logger.info(f"No picker data nodes found in the scene.")

    # -----------------------------------
    # Utility Functions
    # -----------------------------------

    @staticmethod
    def _clear_layout(layout):
        """
        Removes all widgets from a given layout.

        Args:
            layout (QLayout): The layout to be cleared.
        """
        if not layout:
            return
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    @staticmethod
    def _remove_widget(widget):
        """
        Removes a Qt widget from its parent and schedules it for deletion.

        Args:
            widget (QWidget): The widget to remove and delete.
        """
        if widget:
            widget.setParent(None)
            widget.deleteLater()
