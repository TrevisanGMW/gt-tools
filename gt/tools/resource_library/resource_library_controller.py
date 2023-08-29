"""
Resource Library Controller

This module contains the ResourceLibraryController class responsible for managing interactions between the
ResourceLibraryModel and the user interface.
"""
from gt.ui.input_window_text import InputWindowText
from PySide2.QtWidgets import QAbstractItemView
from gt.ui.qt_utils import create_color_icon
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


class ResourceLibraryController:
    TYPE_COLOR = "Color"
    TYPE_PACKAGE_ICON = "Package Icon"
    TYPE_MAYA_ICON = "Maya Icon"

    def __init__(self, model, view):
        """
        Initialize the ResourceLibraryController object.

        Args:
            model: The ResourceLibraryModel object used for data manipulation.
            view: The view object to interact with the user interface.
        """
        self.model = model
        self.view = view
        self.view.controller = self

        # Connections
        # self.view.save_btn.clicked.connect(self.build_view_selected_curve)
        # self.view.item_list.itemSelectionChanged.connect(self.on_item_selection_changed)
        # self.view.search_bar.textChanged.connect(self.filter_list)
        # self.view.parameters_button.clicked.connect(self.open_parameter_editor)
        # self.view.add_custom_button.clicked.connect(self.add_user_curve)
        # self.view.delete_custom_button.clicked.connect(self.remove_user_curve)
        # self.view.snapshot_button.clicked.connect(self.render_curve_snapshot)
        self.view.item_list.itemSelectionChanged.connect(self.on_item_selection_changed)
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
        # print(metadata)
        metadata_obj = self.get_selected_item_object()

        new_preview_image = self.model.get_preview_image(item=metadata_obj)

        if new_preview_image:
            self.view.update_preview_image(new_image=new_preview_image)
        if metadata and "item_type" in metadata:
            self.view.update_item_description(metadata.get("item_type"), item_name)
        #     if metadata.get("item_type") == self.TYPE_COLOR:
        #         self.set_view_base_curve_mode()
        #     elif metadata.get("item_type") == self.TYPE_PACKAGE_ICON:
        #         self.set_view_user_curve_mode()
        #         user_preview_image = self.get_custom_curve_preview_image()
        #         self.view.update_preview_image(new_image_path=user_preview_image)
        #     elif metadata.get("item_type") == self.TYPE_MAYA_ICON:
        #         self.set_view_control_curve_mode()

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

    def get_selected_item_object(self):
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
            logger.debug(f'Selected item "{item}" is missing the metadata necessary to retrieve the object.')
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
        colors = self.model.get_colors()
        # control_curves = self.model.get_controls()
        # user_curves = self.model.get_user_curves()
        # icon_control = QIcon(resource_library.Icon.curve_library_control)
        # icon_user_crv = QIcon(resource_library.Icon.curve_library_user_curve)
        for name, clr in colors.items():
            if filter_str and filter_str not in name:
                continue
            metadata_color = {"object": clr, "item_type": self.TYPE_COLOR}

            self.view.add_item_view_library(item_name=name, icon=create_color_icon(clr), metadata=metadata_color)
            # self.view.add_item_view_library(item_name=crv.get_name(), icon=icon_base_crv, metadata=metadata_base_crv)
        # for ctrl in control_curves:
        #     if filter_str and filter_str not in ctrl.get_name():
        #         continue
        #     metadata_control = {"object": ctrl, "item_type": self.TYPE_MAYA_ICON}
        #     self.view.add_item_view_library(item_name=ctrl.get_name(), icon=icon_control, metadata=metadata_control)
        # for crv in user_curves:
        #     if filter_str and filter_str not in crv.get_name():
        #         continue
        #     metadata_user_crv = {"object": crv, "item_type": self.TYPE_PACKAGE_ICON}
        #     self.view.add_item_view_library(item_name=crv.get_name(), icon=icon_user_crv, metadata=metadata_user_crv)
        self.view.item_list.setCurrentRow(0)  # Select index 0

    def open_parameter_editor(self):
        """ Opens an input window so the user can update the parameters of a control """
        item = self.view.item_list.currentItem()
        if not item:
            logger.warning(f'No item selected. Unable to open parameter editor.')
            return
        item_name = self.view.item_list.currentItem().text()
        control = self.get_selected_item_object()
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


if __name__ == "__main__":
    print('Run it from "__init__.py".')
