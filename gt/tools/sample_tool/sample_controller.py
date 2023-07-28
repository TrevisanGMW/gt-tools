"""
Sample Tool Controller. (Connections - Model and View)
The Controller acts as an intermediary between the Model and the View. When the user interacts with the
View, like clicking a button or filling out a form, the Controller receives and processes these actions.
It then instructs the Model to update the data accordingly. After the Model updates, the Controller also
communicates with the View to refresh the display and show any changes.
Think of it as the glue between model and view.

A view should contain only logic related to generating the user interface.
A controller should only contain the bare minimum of logic required to return the right view or redirect the user to
another action (flow control). Everything else should be contained in the model.

In general, you should strive for fat models and skinny controllers.
Your controller methods should contain only a few lines of code.
If a controller action gets too fat, then you should consider moving the logic out to the model.
"""
from PySide2.QtWidgets import QInputDialog


class SampleToolController:
    def __init__(self, model, view):
        """
        Initialize the SampleToolController object.

        Args:
            model: The SampleToolModel object used for data manipulation.
            view: The view object to interact with the user interface.
        """
        self.model = model
        self.view = view
        self.view.add_button.clicked.connect(self.add_item_view)
        self.view.remove_button.clicked.connect(self.remove_item_view)
        self.view.controller = self

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
        self.view.update_view(self.model.get_items())


if __name__ == "__main__":
    print('Run it from "__init__.py".')
