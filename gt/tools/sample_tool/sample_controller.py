"""
Sample Tool Controller

Connects the sample text saver view and model.
"""

import gt.ui.qt_import as ui_qt
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SampleToolController:
    """Controller for the sample text saver tool."""

    def __init__(self, model, view):
        """Initializes the SampleToolController object.

        Args:
            model (SampleToolModel): Model used for file writing.
            view (SampleToolWindow): View object to connect.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.view.save_button.clicked.connect(self.handle_save)
        self.view.show()

    def handle_save(self):
        """Handles the save button click event."""
        text_to_save = self.view.get_text()
        if not text_to_save:
            logger.warning("No text entered. Skipping save.")
            return
        file_path, _ = ui_qt.QtWidgets.QFileDialog.getSaveFileName(
            self.view,
            "Save Text File",
            os.path.expanduser("~"),
            "Text Files (*.txt);;All Files (*)",
        )
        if not file_path:
            return
        success = self.model.save_text_to_file(text=text_to_save, file_path=file_path)
        if success:
            self.view.text_field.clear()
            logger.info("Text field cleared after successful save.")


if __name__ == "__main__":
    print('Run it from "__init__.py".')
