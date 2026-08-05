"""
Selection Manager Controller
"""

from gt.tools.selection_manager import selection_manager_model as model
import gt.ui.qt_import as ui_qt
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SelectionManagerController:
    """Connects the Selection Manager model and view."""

    def __init__(self, model, view):
        """Initializes the controller.

        Args:
            model (SelectionManagerModel): Model instance.
            view (SelectionManagerView): View instance.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self._syncing_view = False
        self.sync_view_from_model()
        self.refresh_stored_selection_rows()
        self.connect_view()
        self.view.refresh_enabled_states()
        self.view.show()

    def connect_view(self):
        """Connects view signals."""
        for checkbox in [
            self.view.name_contains_checkbox,
            self.view.name_not_contains_checkbox,
            self.view.type_contains_checkbox,
            self.view.type_not_contains_checkbox,
            self.view.visibility_checkbox,
            self.view.outliner_color_checkbox,
            self.view.no_outliner_color_checkbox,
        ]:
            checkbox.toggled.connect(self.on_option_changed)
        for field in [
            self.view.name_contains_field,
            self.view.name_not_contains_field,
            self.view.type_contains_field,
            self.view.type_not_contains_field,
        ]:
            field.textChanged.connect(lambda *args: self.sync_model_from_view(save=True))
        self.view.shape_behavior_combo.currentTextChanged.connect(lambda *args: self.sync_model_from_view(save=True))
        self.view.visibility_on_radio.toggled.connect(lambda *args: self.sync_model_from_view(save=True))

        self.view.outliner_color_button.clicked.connect(
            lambda *args: self.pick_color(self.view.outliner_color_button, "stored_outliner_color")
        )
        self.view.no_outliner_color_button.clicked.connect(
            lambda *args: self.pick_color(self.view.no_outliner_color_button, "stored_no_outliner_color")
        )
        self.view.outliner_color_get_btn.clicked.connect(
            lambda *args: self.get_color_from_selection(self.view.outliner_color_button, "stored_outliner_color")
        )
        self.view.no_outliner_color_get_btn.clicked.connect(
            lambda *args: self.get_color_from_selection(self.view.no_outliner_color_button, "stored_no_outliner_color")
        )

        for slot in sorted(self.view.store_buttons):
            self.connect_stored_selection_buttons(slot)
        self.view.add_stored_slot_btn.clicked.connect(self.add_stored_selection_slot)

        self.view.print_selection_types_btn.clicked.connect(lambda *args: self.model.print_selection_types(True))
        self.view.print_scene_types_btn.clicked.connect(lambda *args: self.model.print_selection_types(False))
        self.view.select_hierarchy_btn.clicked.connect(lambda *args: self.model.select_hierarchy())
        self.view.create_selection_btn.clicked.connect(lambda *args: self.run_selection(create_new_selection=True))
        self.view.update_selection_btn.clicked.connect(lambda *args: self.run_selection(create_new_selection=False))
        self.view.reset_btn.clicked.connect(self.reset_preferences)
        self.view.mode_btn.clicked.connect(self.cycle_ui_mode)

    def connect_stored_selection_buttons(self, slot):
        """Connects buttons for one stored selection row.

        Args:
            slot (int): Stored selection slot.
        """
        buttons = self.view.store_buttons[slot]
        buttons["remove"].clicked.connect(lambda *args, slot=slot: self.remove_from_stored_selection(slot))
        buttons["store"].clicked.connect(lambda *args, slot=slot: self.store_or_load_selection(slot))
        buttons["add"].clicked.connect(lambda *args, slot=slot: self.add_to_stored_selection(slot))
        buttons["clear"].clicked.connect(lambda *args, slot=slot: self.reset_stored_selection(slot))
        buttons["set"].clicked.connect(lambda *args, slot=slot: self.save_stored_selection(slot, as_text=False))
        buttons["text"].clicked.connect(lambda *args, slot=slot: self.save_stored_selection(slot, as_text=True))
        buttons["delete"].clicked.connect(lambda *args, slot=slot: self.delete_stored_selection_slot(slot))

    def on_option_changed(self):
        """Handles option checkbox changes."""
        self.view.refresh_enabled_states()
        self.sync_model_from_view(save=True)

    def sync_model_from_view(self, save=False):
        """Synchronizes model settings with the current view.

        Args:
            save (bool): Whether to persist the synchronized settings.
        """
        """Writes view values into the model."""
        if self._syncing_view:
            return
        self.model.use_contains_string = self.view.name_contains_checkbox.isChecked()
        self.model.use_contains_no_string = self.view.name_not_contains_checkbox.isChecked()
        self.model.use_contains_type = self.view.type_contains_checkbox.isChecked()
        self.model.use_contains_no_type = self.view.type_not_contains_checkbox.isChecked()
        self.model.use_visibility_state = self.view.visibility_checkbox.isChecked()
        self.model.use_outliner_color = self.view.outliner_color_checkbox.isChecked()
        self.model.use_no_outliner_color = self.view.no_outliner_color_checkbox.isChecked()
        self.model.contains_string = self.view.name_contains_field.text()
        self.model.contains_no_string = self.view.name_not_contains_field.text()
        self.model.contains_type = self.view.type_contains_field.text()
        self.model.contains_no_type = self.view.type_not_contains_field.text()
        self.model.shape_node_behavior = self.view.shape_behavior_combo.currentText()
        self.model.visibility_state = self.view.visibility_on_radio.isChecked()
        if save:
            self.model.save_preferences()

    def sync_view_from_model(self):
        """Writes model values into the view."""
        widgets = [
            self.view.name_contains_checkbox,
            self.view.name_not_contains_checkbox,
            self.view.type_contains_checkbox,
            self.view.type_not_contains_checkbox,
            self.view.visibility_checkbox,
            self.view.outliner_color_checkbox,
            self.view.no_outliner_color_checkbox,
            self.view.name_contains_field,
            self.view.name_not_contains_field,
            self.view.type_contains_field,
            self.view.type_not_contains_field,
            self.view.shape_behavior_combo,
            self.view.visibility_on_radio,
            self.view.visibility_off_radio,
        ]
        self._syncing_view = True
        try:
            for widget in widgets:
                widget.blockSignals(True)
            self.view.name_contains_checkbox.setChecked(bool(self.model.use_contains_string))
            self.view.name_not_contains_checkbox.setChecked(bool(self.model.use_contains_no_string))
            self.view.type_contains_checkbox.setChecked(bool(self.model.use_contains_type))
            self.view.type_not_contains_checkbox.setChecked(bool(self.model.use_contains_no_type))
            self.view.visibility_checkbox.setChecked(bool(self.model.use_visibility_state))
            self.view.outliner_color_checkbox.setChecked(bool(self.model.use_outliner_color))
            self.view.no_outliner_color_checkbox.setChecked(bool(self.model.use_no_outliner_color))
            self.view.name_contains_field.setText(self.model.contains_string)
            self.view.name_not_contains_field.setText(self.model.contains_no_string)
            self.view.type_contains_field.setText(self.model.contains_type)
            self.view.type_not_contains_field.setText(self.model.contains_no_type)
            self.view.shape_behavior_combo.setCurrentText(self.model.shape_node_behavior)
            self.view.visibility_on_radio.setChecked(bool(self.model.visibility_state))
            self.view.visibility_off_radio.setChecked(not bool(self.model.visibility_state))
            self.view.set_color_button(self.view.outliner_color_button, self.model.stored_outliner_color)
            self.view.set_color_button(self.view.no_outliner_color_button, self.model.stored_no_outliner_color)
            self.view.apply_ui_mode(self.model.ui_mode)
        finally:
            for widget in widgets:
                widget.blockSignals(False)
            self._syncing_view = False

    def refresh_stored_selection_rows(self):
        """Rebuilds stored selection rows from the model."""
        self.view.clear_stored_selection_rows()
        for index, selection in enumerate(self.model.stored_selections, 1):
            self.view.add_stored_selection_row(index)
            self.view.update_store_button_label(index, selection)
        self.view.apply_ui_mode(self.model.ui_mode)

    def pick_color(self, button, model_attr):
        """Opens a color picker for an outliner color option.

        Args:
            button (QPushButton): Color button.
            model_attr (str): Model color attribute name.
        """
        color = getattr(self.model, model_attr)
        initial_color = ui_qt.QtGui.QColor.fromRgbF(float(color[0]), float(color[1]), float(color[2]))
        chosen_color = ui_qt.QtWidgets.QColorDialog.getColor(initial_color, self.view, "Choose Color")
        if not chosen_color.isValid():
            return
        rgb_color = [chosen_color.redF(), chosen_color.greenF(), chosen_color.blueF()]
        setattr(self.model, model_attr, rgb_color)
        self.view.set_color_button(button, rgb_color)
        self.model.save_preferences()

    def get_color_from_selection(self, button, model_attr):
        """Gets an outliner color from the current Maya selection.

        Args:
            button (QPushButton): Color button to update.
            model_attr (str): Model color attribute name.
        """
        color = self.model.get_color_from_selection()
        if color:
            setattr(self.model, model_attr, color)
            self.view.set_color_button(button, color)
            self.model.save_preferences()

    def run_selection(self, create_new_selection=False):
        """Runs the selection manager.

        Args:
            create_new_selection (bool, optional): Whether to start from all scene nodes.
        """
        self.sync_model_from_view()
        self.model.manage_selection(create_new_selection=create_new_selection)

    def store_or_load_selection(self, slot):
        """Stores selection when empty, otherwise loads the stored slot.

        Args:
            slot (int): Slot number.
        """
        if self.model.get_stored_selection(slot):
            self.model.load_stored_selection(slot)
            return
        selection = self.model.store_selection(slot)
        self.view.update_store_button_label(slot, selection)
        self.model.save_preferences()

    def add_to_stored_selection(self, slot):
        """Adds current selection to a slot.

        Args:
            slot (int): Slot number.
        """
        selection = self.model.add_to_stored_selection(slot)
        self.view.update_store_button_label(slot, selection)
        self.model.save_preferences()

    def remove_from_stored_selection(self, slot):
        """Removes current selection from a slot.

        Args:
            slot (int): Slot number.
        """
        selection = self.model.remove_from_stored_selection(slot)
        self.view.update_store_button_label(slot, selection)
        self.model.save_preferences()

    def reset_stored_selection(self, slot):
        """Clears a stored selection slot.

        Args:
            slot (int): Slot number.
        """
        self.model.reset_stored_selection(slot)
        self.view.update_store_button_label(slot, [])
        self.model.save_preferences()

    def save_stored_selection(self, slot, as_text=False):
        """Saves a stored selection slot.

        Args:
            slot (int): Slot number.
            as_text (bool, optional): If True, export as text. Otherwise save a Maya set.
        """
        self.sync_model_from_view()
        self.model.save_stored_selection(slot, as_text=as_text)

    def add_stored_selection_slot(self):
        """Adds and connects another stored selection slot."""
        slot = self.model.add_stored_selection_slot()
        self.view.add_stored_selection_row(slot)
        self.view.update_store_button_label(slot, [])
        self.connect_stored_selection_buttons(slot)
        self.view.apply_ui_mode(self.model.ui_mode)
        self.model.save_preferences()

    def delete_stored_selection_slot(self, slot):
        """Deletes a stored selection slot.

        Args:
            slot (int): Slot number.
        """
        was_deleted = self.model.delete_stored_selection_slot(slot)
        if was_deleted:
            self.refresh_stored_selection_rows()
            for row_slot in sorted(self.view.store_buttons):
                self.connect_stored_selection_buttons(row_slot)
        else:
            self.view.update_store_button_label(1, [])
        self.model.save_preferences()

    def reset_preferences(self):
        """Resets the Selection Manager state and UI."""
        self.model.reset_preferences()
        self.sync_view_from_model()
        self.refresh_stored_selection_rows()
        for slot in sorted(self.view.store_buttons):
            self.connect_stored_selection_buttons(slot)
        self.view.refresh_enabled_states()
        self.view.apply_ui_mode(self.model.ui_mode)

    def cycle_ui_mode(self):
        """Cycles the Selection Manager UI mode and stores the preference."""
        try:
            current_index = model.UI_MODES.index(self.model.ui_mode)
        except ValueError:
            current_index = 0
        self.model.ui_mode = model.UI_MODES[(current_index + 1) % len(model.UI_MODES)]
        self.view.apply_ui_mode(self.model.ui_mode)
        self.model.save_preferences()


if __name__ == "__main__":
    print('Run it from "__init__.py".')
