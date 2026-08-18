"""
Renamer Controller
"""

from gt.tools.renamer import renamer_model as model
import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class RenamerController:
    """Connects the Renamer model and view."""

    def __init__(self, model, view):
        """Initializes the renamer controller.

        Args:
            model (RenamerModel): Renamer model.
            view (RenamerView): Renamer view.
        """
        self.model = model
        self.view = view
        self._syncing_view = False
        self.sync_view_from_model()
        self.connect_view()
        self.view.refresh_enabled_states()
        self.view.show()

    def connect_view(self):
        """Connects view signals."""
        for radio_button in [self.view.selected_radio, self.view.hierarchy_radio, self.view.all_radio]:
            radio_button.toggled.connect(
                lambda checked, radio_button=radio_button: self.on_selection_type_changed(radio_button, checked)
            )

        self.view.use_source_checkbox.toggled.connect(self.on_use_source_changed)
        self.view.prefix_auto_radio.toggled.connect(
            lambda checked: self.on_mode_changed("prefix_mode", "auto", checked)
        )
        self.view.prefix_input_radio.toggled.connect(
            lambda checked: self.on_mode_changed("prefix_mode", "input", checked)
        )
        self.view.suffix_auto_radio.toggled.connect(
            lambda checked: self.on_mode_changed("suffix_mode", "auto", checked)
        )
        self.view.suffix_input_radio.toggled.connect(
            lambda checked: self.on_mode_changed("suffix_mode", "input", checked)
        )

        self.connect_setting_field(self.view.rename_field, "rename_text")
        self.connect_setting_field(self.view.transform_suffix_field, "transform_suffix")
        self.connect_setting_field(self.view.mesh_suffix_field, "mesh_suffix")
        self.connect_setting_field(self.view.nurbs_crv_suffix_field, "nurbs_crv_suffix")
        self.connect_setting_field(self.view.joint_suffix_field, "joint_suffix")
        self.connect_setting_field(self.view.locator_suffix_field, "locator_suffix")
        self.connect_setting_field(self.view.surface_suffix_field, "surface_suffix")
        self.connect_setting_field(self.view.left_prefix_field, "left_prefix")
        self.connect_setting_field(self.view.center_prefix_field, "center_prefix")
        self.connect_setting_field(self.view.right_prefix_field, "right_prefix")
        self.connect_setting_field(self.view.prefix_field, "prefix_text")
        self.connect_setting_field(self.view.suffix_field, "suffix_text")
        self.connect_setting_field(self.view.search_field, "search_text")
        self.connect_setting_field(self.view.replace_field, "replace_text")
        self.view.start_number_field.valueChanged.connect(
            lambda value: self.save_setting("def_starting_number", value)
        )
        self.view.padding_number_field.valueChanged.connect(
            lambda value: self.save_setting("def_padding_number", value)
        )
        self.view.uppercase_checkbox.toggled.connect(
            lambda checked: self.save_setting("def_uppercase_letter", "1" if checked else "0")
        )

        self.view.remove_first_btn.clicked.connect(lambda *args: self.run_operation(model.OP_REMOVE_FIRST))
        self.view.remove_last_btn.clicked.connect(lambda *args: self.run_operation(model.OP_REMOVE_LAST))
        self.view.uppercase_btn.clicked.connect(lambda *args: self.run_operation(model.OP_UPPERCASE))
        self.view.capitalize_btn.clicked.connect(lambda *args: self.run_operation(model.OP_CAPITALIZE))
        self.view.lowercase_btn.clicked.connect(lambda *args: self.run_operation(model.OP_LOWERCASE))
        self.view.rename_number_btn.clicked.connect(lambda *args: self.run_operation(model.OP_RENAME_NUMBER))
        self.view.rename_letter_btn.clicked.connect(lambda *args: self.run_operation(model.OP_RENAME_LETTER))
        self.view.add_prefix_btn.clicked.connect(lambda *args: self.run_operation(model.OP_ADD_PREFIX))
        self.view.add_suffix_btn.clicked.connect(lambda *args: self.run_operation(model.OP_ADD_SUFFIX))
        self.view.search_replace_btn.clicked.connect(lambda *args: self.run_operation(model.OP_SEARCH_REPLACE))
        self.view.rename_field.returnPressed.connect(lambda *args: self.run_operation(model.OP_RENAME_NUMBER))
        self.view.prefix_field.returnPressed.connect(lambda *args: self.run_operation(model.OP_ADD_PREFIX))
        self.view.suffix_field.returnPressed.connect(lambda *args: self.run_operation(model.OP_ADD_SUFFIX))
        self.view.search_field.returnPressed.connect(lambda *args: self.run_operation(model.OP_SEARCH_REPLACE))
        self.view.replace_field.returnPressed.connect(lambda *args: self.run_operation(model.OP_SEARCH_REPLACE))
        self.view.reset_btn.clicked.connect(lambda *args: self.reset_preferences())

    def connect_setting_field(self, field, setting_key):
        """Connects a line edit to a persistent setting.

        Args:
            field (QLineEdit): Field to connect.
            setting_key (str): Setting key.
        """
        field.textChanged.connect(lambda value, setting_key=setting_key: self.save_setting(setting_key, value))

    def save_setting(self, setting_key, setting_value):
        """Saves a persistent model setting.

        Args:
            setting_key (str): Setting key.
            setting_value (str): Setting value.
        """
        if self._syncing_view:
            return
        self.model.save_setting(setting_key, setting_value)

    def on_selection_type_changed(self, radio_button, checked):
        """Handles selection type changes.

        Args:
            radio_button (QRadioButton): Changed radio button.
            checked (bool): Whether the button was checked.
        """
        if self._syncing_view or not checked:
            return
        self.model.set_selection_type(radio_button.text())

    def on_use_source_changed(self, checked):
        """Persists the source-name option and refreshes dependent controls.

        Args:
            checked (bool): Whether source names should be used as the base name.
        """
        self.save_setting("use_source", "1" if checked else "0")
        self.view.refresh_enabled_states()

    def on_mode_changed(self, setting_key, mode, checked):
        """Persists an automatic or manual input mode and refreshes the view.

        Args:
            setting_key (str): Name of the persisted mode setting.
            mode (str): Selected mode value.
            checked (bool): Whether the related radio button was selected.
        """
        if checked:
            self.save_setting(setting_key, mode)
        self.view.refresh_enabled_states()

    def sync_view_from_model(self):
        """Writes model values into the view."""
        widgets = [
            self.view.selected_radio,
            self.view.hierarchy_radio,
            self.view.all_radio,
            self.view.rename_field,
            self.view.use_source_checkbox,
            self.view.prefix_auto_radio,
            self.view.prefix_input_radio,
            self.view.prefix_field,
            self.view.suffix_auto_radio,
            self.view.suffix_input_radio,
            self.view.suffix_field,
            self.view.transform_suffix_field,
            self.view.mesh_suffix_field,
            self.view.nurbs_crv_suffix_field,
            self.view.joint_suffix_field,
            self.view.locator_suffix_field,
            self.view.surface_suffix_field,
            self.view.left_prefix_field,
            self.view.center_prefix_field,
            self.view.right_prefix_field,
            self.view.start_number_field,
            self.view.padding_number_field,
            self.view.uppercase_checkbox,
            self.view.search_field,
            self.view.replace_field,
        ]
        self._syncing_view = True
        try:
            for widget in widgets:
                widget.blockSignals(True)
            self.view.set_selection_type(self.model.settings.get("selection_type"))
            self.view.rename_field.setText(self.model.settings.get("rename_text", ""))
            self.view.use_source_checkbox.setChecked(self.get_bool_setting("use_source"))
            self.view.prefix_auto_radio.setChecked(
                self.model.settings.get("prefix_mode") != "input"
            )
            self.view.prefix_field.setText(self.model.settings.get("prefix_text", ""))
            self.view.suffix_auto_radio.setChecked(
                self.model.settings.get("suffix_mode") != "input"
            )
            self.view.suffix_field.setText(self.model.settings.get("suffix_text", ""))
            self.view.transform_suffix_field.setText(self.model.settings.get("transform_suffix"))
            self.view.mesh_suffix_field.setText(self.model.settings.get("mesh_suffix"))
            self.view.nurbs_crv_suffix_field.setText(self.model.settings.get("nurbs_crv_suffix"))
            self.view.joint_suffix_field.setText(self.model.settings.get("joint_suffix"))
            self.view.locator_suffix_field.setText(self.model.settings.get("locator_suffix"))
            self.view.surface_suffix_field.setText(self.model.settings.get("surface_suffix"))
            self.view.left_prefix_field.setText(self.model.settings.get("left_prefix"))
            self.view.center_prefix_field.setText(self.model.settings.get("center_prefix"))
            self.view.right_prefix_field.setText(self.model.settings.get("right_prefix"))
            self.view.start_number_field.setValue(self.get_int_setting("def_starting_number", 1))
            self.view.padding_number_field.setValue(self.get_int_setting("def_padding_number", 2))
            self.view.uppercase_checkbox.setChecked(self.model.settings.get("def_uppercase_letter") != "0")
            self.view.search_field.setText(self.model.settings.get("search_text", ""))
            self.view.replace_field.setText(self.model.settings.get("replace_text", ""))
        finally:
            for widget in widgets:
                widget.blockSignals(False)
            self._syncing_view = False

    def get_int_setting(self, setting_key, fallback):
        """Gets an integer setting with fallback.

        Args:
            setting_key (str): Setting key.
            fallback (int): Fallback value.

        Returns:
            int: Setting value.
        """
        try:
            return int(self.model.settings.get(setting_key))
        except (TypeError, ValueError):
            return fallback

    def get_bool_setting(self, setting_key, fallback=False):
        """Gets a boolean setting with fallback.

        Args:
            setting_key (str): Setting key.
            fallback (bool, optional): Value used when the setting is missing.

        Returns:
            bool: Setting value.
        """
        value = self.model.settings.get(setting_key)
        if value is None:
            return fallback
        return str(value).lower() not in ["0", "false", ""]

    def run_operation(self, operation):
        """Runs a renamer operation.

        Args:
            operation (str): Operation name.
        """
        kwargs = {}
        if operation in [model.OP_RENAME_NUMBER, model.OP_RENAME_LETTER]:
            kwargs["new_name"] = self.view.rename_field.text()
            kwargs["keep_name"] = self.view.use_source_checkbox.isChecked()
            kwargs["start_number"] = self.view.start_number_field.value()
            kwargs["padding_number"] = self.view.padding_number_field.value()
            kwargs["is_uppercase"] = self.view.uppercase_checkbox.isChecked()
        elif operation == model.OP_ADD_PREFIX:
            if self.view.prefix_auto_radio.isChecked():
                kwargs["prefix_list"] = [
                    self.view.left_prefix_field.text(),
                    self.view.center_prefix_field.text(),
                    self.view.right_prefix_field.text(),
                ]
            else:
                kwargs["prefix"] = self.view.prefix_field.text()
        elif operation == model.OP_ADD_SUFFIX:
            if self.view.suffix_auto_radio.isChecked():
                kwargs["suffix_list"] = [
                    self.view.transform_suffix_field.text(),
                    self.view.mesh_suffix_field.text(),
                    self.view.nurbs_crv_suffix_field.text(),
                    self.view.joint_suffix_field.text(),
                    self.view.locator_suffix_field.text(),
                    self.view.surface_suffix_field.text(),
                ]
            else:
                kwargs["suffix"] = self.view.suffix_field.text()
        elif operation == model.OP_SEARCH_REPLACE:
            kwargs["search"] = self.view.search_field.text()
            kwargs["replace"] = self.view.replace_field.text()
        self.model.run_operation(operation, **kwargs)

    def reset_preferences(self):
        """Resets persistent settings and refreshes the view."""
        self.model.reset_preferences()
        self.sync_view_from_model()
        self.view.refresh_enabled_states()


if __name__ == "__main__":
    print('Run it from "__init__.py".')
