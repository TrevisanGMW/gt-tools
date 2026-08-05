"""Controller for Create Testing Keys."""

import logging

import gt.ui.qt_import as ui_qt


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CreateTestingKeysController:
    """Connects the Create Testing Keys model and view."""

    def __init__(self, model, view):
        """Initializes and displays the connected tool.

        Args:
            model (CreateTestingKeysModel): Tool model.
            view (CreateTestingKeysView): Tool view.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.connect_view()
        self.view.show()
        ui_qt.QtCore.QTimer.singleShot(0, self.view.resize_to_contents)

    def connect_view(self):
        """Connects view signals to controller actions."""
        self.view.reset_btn.clicked.connect(self.reset_offsets)
        self.view.create_btn.clicked.connect(self.create_testing_keys)
        self.view.delete_all_btn.clicked.connect(self.confirm_delete_all_keyframes)
        self.view.help_btn.clicked.connect(self.show_help)

    def reset_offsets(self):
        """Resets model and view offset values."""
        self.view.set_offsets(self.model.reset_offsets())

    def sync_model_from_view(self):
        """Copies the current UI settings into the model."""
        self.model.offsets = self.view.get_offsets()
        self.model.interval = self.view.interval_field.value()
        self.model.add_inverted = self.view.inverted_checkbox.isChecked()
        self.model.delete_previous = self.view.delete_previous_checkbox.isChecked()
        self.model.use_world_space = self.view.world_space_checkbox.isChecked()

    def create_testing_keys(self):
        """Creates testing keyframes from the current UI settings."""
        self.sync_model_from_view()
        self.model.create_testing_keys()

    def confirm_delete_all_keyframes(self):
        """Confirms and runs the scene-wide keyframe deletion."""
        result = ui_qt.QtWidgets.QMessageBox.question(
            self.view,
            "Delete All Keyframes",
            "Delete all time-based keyframes in the scene?\n\nSet-driven keys are not affected.",
            ui_qt.QtLib.StandardButton.Yes | ui_qt.QtLib.StandardButton.No,
            ui_qt.QtLib.StandardButton.No,
        )
        if result == ui_qt.QtLib.StandardButton.Yes:
            self.model.delete_all_keyframes()

    def show_help(self):
        """Displays concise usage and option help."""
        help_dialog = ui_qt.QtWidgets.QMessageBox(self.view)
        help_dialog.setWindowTitle("Create Testing Keys Help")
        help_dialog.setIcon(ui_qt.QtWidgets.QMessageBox.Information)
        help_dialog.setText("Create a repeatable key sequence for testing controls and skin weights.")
        help_dialog.setInformativeText(
            "1. Select one or more Maya objects.\n"
            "2. Enter at least one translate, rotate, or scale offset.\n"
            "3. Set the frame interval and options.\n"
            "4. Click Create Testing Keyframes.\n\n"
            "Inverted movement adds the opposite pose. Delete Previously Created Keys removes "
            "time-based keys connected to the selection first. World Space applies translate and "
            "rotate offsets independently of the parent hierarchy."
        )
        help_dialog.setStandardButtons(ui_qt.QtWidgets.QMessageBox.Ok)
        help_dialog.exec_()
