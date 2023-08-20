"""
Curve Library Controller

This module contains the CurveLibraryController class responsible for managing interactions between the
CurveLibraryModel and the user interface.
"""
from gt.ui.input_window_text import InputWindowText
from gt.utils import iterable_utils
from gt.ui import resource_library
from PySide2.QtGui import QIcon
from functools import partial
from PySide2.QtCore import Qt
import logging

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
        # Connections
        self.view.build_button.clicked.connect(self.build_view_selected_curve)
        self.view.item_list.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.view.search_edit.textChanged.connect(self.filter_list)
        self.view.parameters_button.clicked.connect(self.open_parameter_editor)
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
        search_text = self.view.search_edit.text().lower()
        self.view.item_list.clear()
        curve_names = self.model.get_base_curve_names()
        filtered_items = [item for item in curve_names if search_text in item.lower()]
        self.view.item_list.addItems(filtered_items)
        self.view.item_list.setCurrentRow(0)  # Select index 0
        if not filtered_items:
            self.view.update_preview_image()

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

    def remove_item_view(self):
        """
        Remove the selected item from the model based on the user's selection in the view.
        """
        selected_item = self.view.item_list.currentRow()
        if selected_item >= 0:
            self.model.remove_item(selected_item)
            self.populate_curve_library()

    def populate_curve_library(self):
        """
        Update the view with the current list of items from the model.
        """
        self.view.clear_view_library()
        base_curves = self.model.get_base_curves()
        control_curves = self.model.get_controls()
        user_curves = self.model.get_user_curves()
        icon_base_crv = QIcon(resource_library.Icon.curve_library_base_curve)
        icon_control = QIcon(resource_library.Icon.curve_library_control)
        icon_user_crv = QIcon(resource_library.Icon.curve_library_user_curve)
        for crv in base_curves:
            metadata_base_crv = {"object": crv, "item_type": self.CURVE_TYPE_BASE}
            self.view.add_item_view_library(item_name=crv.get_name(), icon=icon_base_crv, metadata=metadata_base_crv)
        for ctrl in control_curves:
            metadata_control = {"object": ctrl, "item_type": self.CURVE_TYPE_CONTROL}
            self.view.add_item_view_library(item_name=ctrl.get_name(), icon=icon_control, metadata=metadata_control)
        for crv in user_curves:
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
            logger.warning(f'Selected control does not have any parameters.')
            return
        from gt.utils.control_utils import Control
        if not isinstance(control, Control):
            logger.warning(f'Unable to edit parameters. Selected item is not of the type "Control."')
            return
        param_win = InputWindowText(parent=self.view,
                                    message=control.get_docstrings(),
                                    window_title=f'Parameters for "{item_name}"',
                                    image=resource_library.Icon.dev_code,
                                    image_scale_pct=10)
        param_win.set_confirm_button_text("Build")
        formatted_dict = iterable_utils.format_dict_with_keys_per_line(parameters, keys_per_line=2,
                                                                       bracket_new_line=True)
        param_win.set_text_field_text(formatted_dict)
        param_win.confirm_button.clicked.connect(partial(self.model.build_control_with_custom_parameters,
                                                         param_win.get_text_field_text, control))
        param_win.show()


if __name__ == "__main__":
    print('Run it from "__init__.py".')
