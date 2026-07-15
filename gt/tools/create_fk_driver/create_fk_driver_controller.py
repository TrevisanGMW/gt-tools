"""Create FK Driver controller."""

import logging


logger = logging.getLogger(__name__)


class CreateFkDriverController:
    """Connects the Create FK Driver model and view."""

    def __init__(self, model, view):
        """Initializes controller bindings.

        Args:
            model (CreateFkDriverModel): Tool model.
            view (CreateFkDriverView): Tool view.
        """
        self.model = model
        self.view = view
        self._sync_view()
        self._connect_view()
        self.view.show()

    def _connect_view(self):
        """Connects view signals to settings and actions."""
        mappings = [
            (self.view.mimic_hierarchy_checkbox.toggled, "mimic_hierarchy"),
            (self.view.constraint_joints_checkbox.toggled, "constraint_joints"),
            (self.view.colorize_controls_checkbox.toggled, "colorize_controls"),
            (self.view.include_hierarchy_checkbox.toggled, "include_hierarchy"),
            (self.view.radius_spinbox.valueChanged, "curve_radius"),
            (self.view.joint_suffix_field.textChanged, "joint_suffix"),
            (self.view.control_suffix_field.textChanged, "control_suffix"),
            (self.view.control_group_suffix_field.textChanged, "control_group_suffix"),
            (self.view.ignored_strings_field.textChanged, "ignored_strings"),
            (self.view.custom_curve_edit.textChanged, "custom_curve_code"),
        ]
        for signal, key in mappings:
            if key == "custom_curve_code":
                signal.connect(lambda key=key: self.model.set_setting(key, self.view.custom_curve_edit.toPlainText()))
            else:
                signal.connect(lambda value, key=key: self.model.set_setting(key, value))
        self.view.curve_type_combo.currentTextChanged.connect(self._set_curve_type)
        self.view.reset_button.clicked.connect(self.reset_settings)
        self.view.generate_button.clicked.connect(self.generate)

    def _sync_view(self):
        """Copies model settings into the view."""
        settings = self.model.settings
        self.view.mimic_hierarchy_checkbox.setChecked(settings.get("mimic_hierarchy"))
        self.view.constraint_joints_checkbox.setChecked(settings.get("constraint_joints"))
        self.view.colorize_controls_checkbox.setChecked(settings.get("colorize_controls"))
        self.view.include_hierarchy_checkbox.setChecked(settings.get("include_hierarchy"))
        self.view.curve_type_combo.setCurrentText(settings.get("curve_type"))
        self.view.radius_spinbox.setValue(settings.get("curve_radius"))
        self.view.joint_suffix_field.setText(settings.get("joint_suffix"))
        self.view.control_suffix_field.setText(settings.get("control_suffix"))
        self.view.control_group_suffix_field.setText(settings.get("control_group_suffix"))
        self.view.ignored_strings_field.setText(settings.get("ignored_strings"))
        self.view.custom_curve_edit.setPlainText(settings.get("custom_curve_code"))
        self.view.set_custom_curve_visible(settings.get("curve_type") == "Custom Python")

    def _set_curve_type(self, curve_type):
        """Stores the shape type and refreshes advanced controls.

        Args:
            curve_type (str): Selected curve type.
        """
        self.model.set_setting("curve_type", curve_type)
        self.view.set_custom_curve_visible(curve_type == "Custom Python")

    def reset_settings(self):
        """Restores default settings and refreshes the view."""
        self.model.reset_preferences()
        self._sync_view()

    def generate(self):
        """Runs FK driver generation and reports failures through Maya."""
        try:
            created = self.model.generate_fk_drivers()
            logger.info("Created %s FK driver controls.", len(created))
        except Exception as exception:
            logger.exception("Unable to create FK drivers.")
            try:
                import maya.cmds as cmds

                cmds.warning(str(exception))
            except Exception:
                pass
