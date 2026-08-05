"""Add Offset Transform controller."""

import logging


logger = logging.getLogger(__name__)


class AddOffsetTransformController:
    """Connects the Add Offset Transform model and view."""

    def __init__(self, model, view):
        """Initializes bindings.

        Args:
            model (AddOffsetTransformModel): Tool model.
            view (AddOffsetTransformView): Tool view.
        """
        self.model = model
        self.view = view
        self._sync_view()
        self._connect_view()
        self.view.show()

    def _connect_view(self):
        """Connects view signals."""
        self.view.transform_type_combo.currentTextChanged.connect(
            lambda value: self.model.set_setting("transform_type", value)
        )
        self.view.pivot_source_combo.currentTextChanged.connect(
            lambda value: self.model.set_setting("pivot_source", value)
        )
        self.view.transform_suffix_field.textChanged.connect(
            lambda value: self.model.set_setting("transform_suffix", value)
        )
        self.view.color_button.clicked.connect(self.choose_color)
        self.view.reset_button.clicked.connect(self.reset_settings)
        self.view.create_button.clicked.connect(self.create_offsets)

    def _sync_view(self):
        """Copies model settings into the view."""
        settings = self.model.settings
        self.view.transform_type_combo.setCurrentText(settings.get("transform_type"))
        self.view.pivot_source_combo.setCurrentText(settings.get("pivot_source"))
        self.view.transform_suffix_field.setText(settings.get("transform_suffix"))
        self.view.set_color(settings.get("outliner_color"))

    def choose_color(self):
        """Prompts for and stores an outliner color."""
        import gt.ui.qt_import as ui_qt

        color = self.model.settings.get("outliner_color")
        initial = ui_qt.QtGui.QColor.fromRgbF(color[0], color[1], color[2])
        selected = ui_qt.QtWidgets.QColorDialog.getColor(initial, self.view, "Choose Outliner Color")
        if not selected.isValid():
            return
        color = [selected.redF(), selected.greenF(), selected.blueF()]
        self.model.set_setting("outliner_color", color)
        self.view.set_color(color)

    def reset_settings(self):
        """Restores defaults and refreshes the view."""
        self.model.reset_preferences()
        self._sync_view()

    def create_offsets(self):
        """Runs offset creation and reports failures through Maya."""
        try:
            offsets = self.model.create_offsets()
            logger.info("Created %s offset transforms.", len(offsets))
        except Exception as exception:
            logger.exception("Unable to add offset transforms.")
            try:
                import maya.cmds as cmds

                cmds.warning(str(exception))
            except Exception:
                pass
