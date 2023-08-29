"""
Resource Library Controller

This module contains the ResourceLibraryController class responsible for managing interactions between the
ResourceLibraryModel and the user interface.
"""
import os

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
        self.view.save_btn.clicked.connect(self.exported_selected_resource)
        self.view.search_bar.textChanged.connect(self.filter_list)
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
        metadata_obj = self.get_selected_item_object()

        # Preview Image
        new_preview_image = self.model.get_preview_image(item=metadata_obj)
        if new_preview_image:
            self.view.update_preview_image(new_image=new_preview_image)

        # UI Updates
        if metadata and "item_type" in metadata:
            # Colors ----------------------------------------------------
            self.view.update_item_description(metadata.get("item_type"), item_name)
            if metadata.get("item_type") == self.TYPE_COLOR:
                color_str = ''
                has_rgb_data = False

                rgb_attributes = vars(resource_library.Color.Hex)
                if item_name in rgb_attributes:
                    color_str += f'resource_library.Color.RGB.{item_name}'
                    color_str_rgb = getattr(resource_library.Color.RGB, item_name)
                    color_str += f'  # {color_str_rgb}'
                    has_rgb_data = True

                if has_rgb_data:
                    color_str += '\n'

                hex_attributes = vars(resource_library.Color.Hex)
                if item_name in hex_attributes:
                    color_str += f'resource_library.Color.Hex.{item_name}'
                    color_str_hex = getattr(resource_library.Color.Hex, item_name)
                    color_str += f'  # {color_str_hex}'
                self.view.update_resource_path(text=color_str)

            # Package Icons ----------------------------------------------
            if metadata.get("item_type") == self.TYPE_PACKAGE_ICON:
                icon_str = ''

                icon_attributes = vars(resource_library.Icon)
                if item_name in icon_attributes:
                    icon_path = getattr(resource_library.Icon, item_name)
                    if icon_path:
                        file_name = os.path.basename(icon_path)
                        icon_str += fr'# ..\gt\ui\resources\icons\{file_name}' + "\n"
                    icon_str += f'resource_library.Icon.{item_name}'
                self.view.update_resource_path(text=icon_str)

            # Maya Icons
        #     elif metadata.get("item_type") == self.TYPE_PACKAGE_ICON:
        #         self.set_view_user_curve_mode()
        #         user_preview_image = self.get_custom_curve_preview_image()
        #         self.view.update_preview_image(new_image_path=user_preview_image)
        #     elif metadata.get("item_type") == self.TYPE_MAYA_ICON:
        #         self.set_view_control_curve_mode()

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
        package_icons = self.model.get_package_icons()
        colors = self.model.get_colors()
        # user_curves = self.model.get_user_curves()
        # icon_control = QIcon(resource_library.Icon.curve_library_control)
        # icon_user_crv = QIcon(resource_library.Icon.curve_library_user_curve)
        for name, icon in package_icons.items():
            if filter_str and filter_str not in name:
                continue
            metadata_icon = {"object": icon, "item_type": self.TYPE_PACKAGE_ICON}

            self.view.add_item_view_library(item_name=name, icon=icon, metadata=metadata_icon)
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

    def exported_selected_resource(self):
        """ Opens an input window so the user can update the parameters of a control """
        item = self.view.item_list.currentItem()
        item_name = item.text()
        metadata = item.data(Qt.UserRole)
        if metadata.get("item_type") == self.TYPE_COLOR:
            self.model.export_resource(key=item_name, source='colors')
        if metadata.get("item_type") == self.TYPE_PACKAGE_ICON:
            self.model.export_resource(key=item_name, source='package_icons')
        if metadata.get("item_type") == self.TYPE_MAYA_ICON:
            self.model.export_resource(key=item_name, source='maya_icons')


if __name__ == "__main__":
    print('Run it from "__init__.py".')
