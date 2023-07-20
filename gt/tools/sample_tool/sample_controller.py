"""
Sample Tool Controller. (Logic)
The Controller acts as an intermediary between the Model and the View. When the user interacts with the
View, like clicking a button or filling out a form, the Controller receives and processes these actions.
It then instructs the Model to update the data accordingly. After the Model updates, the Controller also
communicates with the View to refresh the display and show any changes.
This of it as the tool logic. It should be able to work independently of the view. One should be able to import it
and run the tool without its GUI.
"""
from PySide2 import QtCore


class SampleToolController:
    CloseView = QtCore.Signal()
    UpdatePath = QtCore.Signal(object)
    UpdateStatus = QtCore.Signal(object)
    UpdateVersion = QtCore.Signal(object, object)

    def __init__(self, model=None, view=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.model = model
        self.view = view
        self.view.text_edit_input.textChanged.connect(self.update_model)

    def update_model(self, text):
        self.model.set_data(text)
        self.model_changed()

    def model_changed(self):
        self.view.label_output.setText("Stored Data: " + self.model.get_data())


if __name__ == "__main__":
    # controller = SampleToolController()
    print("Run it from __init__.py")
