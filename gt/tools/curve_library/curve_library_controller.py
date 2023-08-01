"""
Curve Library Controller
"""
from PySide2.QtWidgets import QInputDialog
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CurveLibraryController:
    def __init__(self, model, view):
        """
        Initialize the SampleToolController object.

        Args:
            model: The SampleToolModel object used for data manipulation.
            view: The view object to interact with the user interface.
        """
        self.model = model
        self.view = view
        self.view.build_button.clicked.connect(self.build_view_selected_curve)
        self.view.item_list.itemSelectionChanged.connect(self.on_item_selection_changed)
        self.view.controller = self

    def on_item_selection_changed(self):
        selected_item = self.view.item_list.currentItem().text()
        logger.debug(f"Selected item: {selected_item}")

    def build_view_selected_curve(self):
        selected_curve_name = self.view.item_list.currentItem().text()
        self.model.build_curve(curve_name=selected_curve_name)

    def add_item_view(self):
        """
        Prompt the user for an item name and add it to the model.
        """
        item_text, ok = QInputDialog.getText(self.view, "Enter item name", "Item name:")
        if ok:
            self.model.add_item(item_text)
            self.update_view()

    def remove_item_view(self):
        """
        Remove the selected item from the model based on the user's selection in the view.
        """
        selected_item = self.view.item_list.currentRow()
        if selected_item >= 0:
            self.model.remove_item(selected_item)
            self.update_view()

    def update_view(self):
        """
        Update the view with the current list of items from the model.
        """
        self.view.update_view_library(self.model.get_curve_names())
        self.view.item_list.setCurrentRow(0)  # Select index 0


if __name__ == "__main__":
    print('Run it from "__init__.py".')
