"""
Outliner Sorter Controller
"""

import logging

from gt.tools.outliner_sorter import outliner_sorter_model as model_module
import gt.ui.qt_import as ui_qt


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OutlinerSorterController:
    """Connects the Outliner Sorter model and view."""

    def __init__(self, model, view):
        """Initializes the controller.

        Args:
            model (OutlinerSorterModel): Model instance.
            view (OutlinerSorterView): View instance.
        """
        self.model = model
        self.view = view
        self.connect_view()
        self.view.show()
        ui_qt.QtCore.QTimer.singleShot(0, self.view.resize_to_contents)

    def connect_view(self):
        """Connects view signals."""
        self.view.move_up_btn.clicked.connect(lambda *args: self.run_operation("reorder_up"))
        self.view.move_down_btn.clicked.connect(lambda *args: self.run_operation("reorder_down"))
        self.view.move_front_btn.clicked.connect(lambda *args: self.run_operation("reorder_front"))
        self.view.move_back_btn.clicked.connect(lambda *args: self.run_operation("reorder_back"))
        self.view.shuffle_btn.clicked.connect(lambda *args: self.run_operation("shuffle"))
        self.view.sort_name_btn.clicked.connect(lambda *args: self.run_operation("sort_name"))
        self.view.sort_attribute_btn.clicked.connect(lambda *args: self.run_operation("sort_attribute"))
        self.view.attribute_combo.currentTextChanged.connect(self.update_attribute_field_state)
        self.update_attribute_field_state()

    def update_attribute_field_state(self):
        """Updates the custom attribute field based on the selected attribute option."""
        option = self.view.attribute_combo.currentText()
        is_custom = option == model_module.ATTR_CUSTOM
        self.view.attribute_field.setEnabled(is_custom)
        if not is_custom:
            self.view.attribute_field.setText(model_module.ATTRIBUTE_NAME_MAP.get(option, "translateY"))

    def run_operation(self, operation):
        """Runs an outliner sorter operation.

        Args:
            operation (str): Operation key.
        """
        self.model.run_operation(
            operation=operation,
            is_ascending=self.view.is_ascending(),
            attr=self.view.get_attribute_name(),
        )
