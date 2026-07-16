"""Controller for the Shape Text to Curve tool."""

import logging

from gt.tools.shape_text_to_curve import shape_text_to_curve_model
import gt.ui.qt_import as ui_qt


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ShapeTextToCurveController:
    """Connects the text-curve model to the Qt view and Maya actions."""

    def __init__(self, model, view):
        """Initializes and displays the connected tool.

        Args:
            model (ShapeTextToCurveModel): Tool data and curve service.
            view (ShapeTextToCurveView): Tool user interface.
        """
        self.model = model
        self.view = view
        self.help_dialog = None
        self.view.controller = self
        self._connect_view()
        self.view.set_font_name(self.model.get_font_display_name())
        self.view.set_text(shape_text_to_curve_model.DEFAULT_TEXT)
        self.view.show()
        ui_qt.QtCore.QTimer.singleShot(0, self.view.resize_to_contents)

    def _connect_view(self):
        """Connects user interface signals to controller actions."""
        self.view.generate_button.clicked.connect(self.generate_curves)
        self.view.text_field.returnPressed.connect(self.generate_curves)
        self.view.font_button.clicked.connect(self.choose_font)
        self.view.help_button.clicked.connect(self.show_help)

    def generate_curves(self):
        """Creates curves from the current text and reports the result."""
        try:
            created_curves = self.model.generate_curves(self.view.get_text())
        except Exception as exception:
            logger.exception("Unable to create text curves.")
            self.view.set_status(f"Unable to generate curves: {exception}", is_error=True)
            return

        if not created_curves:
            self.view.set_status("Enter text before generating curves.", is_error=True)
            return
        curve_label = "curve" if len(created_curves) == 1 else "curves"
        self.view.set_status(f"Created {len(created_curves)} text {curve_label}.")

    def choose_font(self):
        """Opens Maya's font picker and stores the chosen font."""
        try:
            import maya.cmds as cmds

            selected_font = cmds.fontDialog()
        except Exception as exception:
            logger.exception("Unable to open Maya's font dialog.")
            self.view.set_status(f"Unable to open the font picker: {exception}", is_error=True)
            return

        if self.model.set_font(selected_font):
            self.view.set_font_name(self.model.get_font_display_name())
            self.view.set_status(f"Font changed to {self.model.get_font_display_name()}.")

    def show_help(self):
        """Creates or raises the tool's help dialog."""
        if self.help_dialog is None:
            self.help_dialog = self.view.create_help_dialog()
        self.help_dialog.show()
        self.help_dialog.raise_()
        self.help_dialog.activateWindow()
