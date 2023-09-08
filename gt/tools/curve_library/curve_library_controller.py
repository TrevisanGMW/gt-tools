"""
Curve Library Controller

This module contains the CurveLibraryController class responsible for managing interactions between the
CurveLibraryModel and the user interface.
"""
from PySide2.QtWidgets import QMessageBox, QAbstractItemView
from gt.ui.input_window_text import InputWindowText
from gt.utils.prefs_utils import Prefs
from gt.utils import iterable_utils
from gt.ui import resource_library
from PySide2.QtGui import QIcon
from functools import partial
from PySide2.QtCore import Qt
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CurveLibraryController:
    CURVE_TYPE_BASE = "Curve"
    CURVE_TYPE_USER = "User Curve"
    CURVE_TYPE_CONTROL = "Control"

    def __init__(self, model, view):
        """
        Initialize the CurveLibraryController object.

        Args:
            model: The CurveLibraryModel object used for data manipulation.
            view: The view object to interact with the user interface.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        # Preferences
        self.preferences = Prefs("curve_library")
        self.preferences.set_user_files_sub_folder("user_curves")
        user_curves_dir = self.preferences.get_user_files_dir_path(create_if_missing=False)
        self.model.import_user_curve_library(source_dir=user_curves_dir)
        # Connections
        self.view.build_button.clicked.connect(self.build_view_selected_curve)
        self.view.item_list.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.view.search_bar.textChanged.connect(self.filter_list)
        self.view.parameters_button.clicked.connect(self.open_parameter_editor)
        self.view.add_custom_button.clicked.connect(self.add_user_curve)
        self.view.delete_custom_button.clicked.connect(self.remove_user_curve)
        self.view.snapshot_button.clicked.connect(self.render_curve_snapshot)
        self.populate_curve_library()
        self.view.show()

    def on_item_selection_changed(self):
        """
        Update the preview image in the view when the selected item in the list changes.
        """
        item = self.view.item_list.currentItem()
        if not item:
            logger.debug(f'No item selected. Skipping UI update.')
            return
        item_name = self.view.item_list.currentItem().text()
        metadata = item.data(Qt.UserRole)
        new_preview_image = self.model.get_preview_image(object_name=item_name)
        if new_preview_image:
            self.view.update_preview_image(new_image_path=new_preview_image)
        if metadata and "item_type" in metadata:
            self.view.update_curve_description(metadata.get("item_type"), item_name)
            if metadata.get("item_type") == self.CURVE_TYPE_BASE:
                self.set_view_base_curve_mode()
            elif metadata.get("item_type") == self.CURVE_TYPE_USER:
                self.set_view_user_curve_mode()
                user_preview_image = self.get_custom_curve_preview_image()
                self.view.update_preview_image(new_image_path=user_preview_image)
            elif metadata.get("item_type") == self.CURVE_TYPE_CONTROL:
                self.set_view_control_curve_mode()

    def set_view_base_curve_mode(self):
        """ Changes the UI to look like you have a package curve (base) selected """
        self.view.set_snapshot_button_enabled(False)
        self.view.set_parameters_button_enabled(False)
        self.view.set_delete_button_enabled(False)

    def set_view_user_curve_mode(self):
        """ Changes the UI to look like you have a user-defined curve selected """
        self.view.set_snapshot_button_enabled(True)
        self.view.set_parameters_button_enabled(False)
        self.view.set_delete_button_enabled(True)

    def set_view_control_curve_mode(self):
        """ Changes the UI to look like you have a package control selected """
        self.view.set_snapshot_button_enabled(False)
        self.view.set_parameters_button_enabled(True)
        self.view.set_delete_button_enabled(False)

    def filter_list(self):
        """
        Filter the curve library list based on the search text entered by the user.
        """
        search_text = self.view.search_bar.text().lower()
        self.populate_curve_library(filter_str=search_text)

    def build_view_selected_curve(self):
        """
        Build the selected curve from the curve library in the model.
        """
        current_curve = self.get_selected_item_curve()
        self.model.build_curve(curve=current_curve)

    def get_selected_item_curve(self):
        """
        Gets the curve of the currently selected element in the list
        Returns:
            Curve, Control or None: Object stored in the metadata of the selected item.
                                    None if not found or nothing selected.
        """
        item = self.view.item_list.currentItem()
        if not item:
            logger.debug(f'No item selected.')
            return
        metadata = item.data(Qt.UserRole)
        if not metadata or not metadata.get("object"):
            logger.debug(f'Selected item "{item}" is missing the metadata necessary to retrieve a curve.')
            return
        return metadata.get("object")

    def select_item_by_name(self, item_name):
        """
        Selects item based on its name
        Returns:
            bool: True if item was found and selected. False if item with given name was not found.
        """
        list_widget = self.view.item_list
        for index in range(list_widget.count()):
            item = list_widget.item(index)
            if item.text() == item_name:
                item.setSelected(True)
                list_widget.scrollToItem(item, QAbstractItemView.PositionAtCenter)
                self.view.item_list.setCurrentItem(item)
                self.on_item_selection_changed()
                return True
        return False

    def populate_curve_library(self, filter_str=None):
        """
        Update the view with the current list of items from the model.
        Args:
            filter_str (str, None): If provided, it will be used to filter desired objects when populating the list.
        """
        self.view.clear_view_library()
        base_curves = self.model.get_base_curves()
        control_curves = self.model.get_controls()
        user_curves = self.model.get_user_curves()
        icon_base_crv = QIcon(resource_library.Icon.curve_library_base_curve)
        icon_control = QIcon(resource_library.Icon.curve_library_control)
        icon_user_crv = QIcon(resource_library.Icon.curve_library_user_curve)
        for crv in base_curves:
            if filter_str and filter_str not in crv.get_name():
                continue
            metadata_base_crv = {"object": crv, "item_type": self.CURVE_TYPE_BASE}
            self.view.add_item_view_library(item_name=crv.get_name(), icon=icon_base_crv, metadata=metadata_base_crv)
        for ctrl in control_curves:
            if filter_str and filter_str not in ctrl.get_name():
                continue
            metadata_control = {"object": ctrl, "item_type": self.CURVE_TYPE_CONTROL}
            self.view.add_item_view_library(item_name=ctrl.get_name(), icon=icon_control, metadata=metadata_control)
        for crv in user_curves:
            if filter_str and filter_str not in crv.get_name():
                continue
            metadata_user_crv = {"object": crv, "item_type": self.CURVE_TYPE_USER}
            self.view.add_item_view_library(item_name=crv.get_name(), icon=icon_user_crv, metadata=metadata_user_crv)
        self.view.item_list.setCurrentRow(0)  # Select index 0

    def open_parameter_editor(self):
        """ Opens an input window so the user can update the parameters of a control """
        item = self.view.item_list.currentItem()
        if not item:
            logger.warning(f'No item selected. Unable to open parameter editor.')
            return
        item_name = self.view.item_list.currentItem().text()
        control = self.get_selected_item_curve()
        parameters = control.get_parameters()
        if not parameters:
            logger.debug(f'Selected control does not have any parameters.')
            parameters = "{\n# This control does not have any parameters.\n}"
        from gt.utils.control_utils import Control
        if not isinstance(control, Control):
            logger.warning(f'Unable to edit parameters. Selected item is not of the type "Control."')
            return
        param_win = InputWindowText(parent=self.view,
                                    message=control.get_docstrings(),
                                    window_title=f'Parameters for "{item_name}"',
                                    image=resource_library.Icon.curve_library_control,
                                    window_icon=resource_library.Icon.curve_library_parameters,
                                    image_scale_pct=10,
                                    is_python_code=True)
        param_win.set_confirm_button_text("Build")
        if isinstance(parameters, dict):
            formatted_dict = iterable_utils.format_dict_with_keys_per_line(parameters, keys_per_line=1,
                                                                           bracket_new_line=True)
        elif isinstance(parameters, str):
            formatted_dict = parameters
        param_win.set_text_field_text(formatted_dict)
        param_win.confirm_button.clicked.connect(partial(self.model.build_control_with_custom_parameters,
                                                         param_win.get_text_field_text, control))
        param_win.show()

    def add_user_curve(self):
        """
        Attempts to create a user-defined curve (saved to the preferences' folder)
        Nothing is created in case operation fails.
        """
        curve = self.model.get_potential_user_curve_from_selection()
        if curve:
            curve_name = curve.get_name()
            path_dir = self.preferences.get_user_files_dir_path()
            if os.path.exists(path_dir):
                path_file = os.path.join(path_dir, f'{curve_name}.crv')
                curve.write_curve_to_file(file_path=path_file)
                sys.stdout.write(f'Curve written to: "{path_file}".\n')
                # Refresh model and view
                self.model.import_user_curve_library(source_dir=path_dir)
                self.populate_curve_library()
                self.select_item_by_name(curve_name)
                self.set_view_user_curve_mode()

    def remove_user_curve(self):
        """
        Deletes selected curve (only user curves) - Asks for confirmation through a dialog before deleting it.
        """
        curve = self.get_selected_item_curve()
        if not curve:
            logger.warning(f'Unable to retrieve curve object associated to selected item.')
            return
        curve_name = curve.get_name()
        user_choice = QMessageBox.question(None, f'Curve: "{curve.get_name()}"',
                                           f'Are you sure you want to delete curve "{curve_name}"?',
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if user_choice == QMessageBox.Yes:
            path_dir = self.preferences.get_user_files_dir_path()
            path_file = os.path.join(path_dir, f'{curve_name}.crv')
            path_preview_image = os.path.join(path_dir, f'{curve_name}.jpg')
            from gt.utils.data_utils import delete_paths
            delete_paths([path_file, path_preview_image])
            self.model.import_user_curve_library(source_dir=path_dir)
            selected_item = self.view.item_list.currentItem()
            if selected_item:
                self.view.item_list.takeItem(self.view.item_list.row(selected_item))
            sys.stdout.write(f'Curve "{curve_name}" was deleted.\n')

    def render_curve_snapshot(self):
        """ Saves a snapshot to be used as preview image for a custom user curve """
        curve = self.get_selected_item_curve()
        if not curve:
            logger.warning(f'Unable to retrieve curve object associated to selected item.')
            return
        curve_name = curve.get_name()
        path_dir = self.preferences.get_user_files_dir_path()
        from gt.utils.playblast_utils import render_viewport_snapshot
        path_file = render_viewport_snapshot(file_name=curve_name, target_dir=path_dir)
        if path_file and os.path.exists(path_file):
            sys.stdout.write(f'Snapshot written to: "{path_file}".')
            self.on_item_selection_changed()
        else:
            logger.warning(f'Unable to save snapshot. Failed to create image file.')

    def get_custom_curve_preview_image(self):
        """
        Gets the preview image for a custom curve (in case it exists)
        Returns:
            str: Path to the preview image or the path to the missing file image.
        """
        curve = self.get_selected_item_curve()
        if not curve:
            logger.warning(f'Unable to retrieve curve object associated to selected item.')
            return
        curve_name = curve.get_name()
        path_dir = self.preferences.get_user_files_dir_path()
        preview_image = os.path.join(path_dir, f'{curve_name}.jpg')
        if os.path.exists(preview_image):
            return preview_image
        else:
            return resource_library.Icon.library_missing_file


if __name__ == "__main__":
    print('Run it from "__init__.py".')
