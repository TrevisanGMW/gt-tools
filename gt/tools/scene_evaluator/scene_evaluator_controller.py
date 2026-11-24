"""Connects Scene Evaluator settings, validation and Python actions."""

import logging
from pathlib import Path

from gt.core.validator import ValidatorLibrary, ValidatorScope
from gt.tools.scene_evaluator.scene_evaluator_model import (
    ACTION_ALWAYS_ALLOW,
    ACTION_CONFIRM_BYPASS,
    ACTION_REQUIRE_PASS,
    ACTION_SCRIPT_FILENAME,
)
from gt.tools.scene_evaluator.scene_evaluator_view import SceneEvaluatorPreferencesDialog, ValidatorSelectionDialog
from gt.ui import qt_import as ui_qt


logger = logging.getLogger(__name__)
PRESET_FILE_FILTER = "Scene Evaluator Preset (*.json)"


class SceneEvaluatorController:
    """Manages the Maya window and applies changes to its validator checklist."""

    def __init__(self, model, view):
        """Connects and opens the evaluator.

        Args:
            model (SceneEvaluatorModel): Persistent evaluator settings.
            view (SceneEvaluatorView): Main evaluator window.
        """
        self.model = model
        self.view = view
        self.view.controller = self
        self.validator_model = view.validator_widget.list_validator_model
        self.validator_classes = {
            validator_id: getattr(ValidatorLibrary, validator_id)
            for validator_id in ValidatorLibrary.get_available_validators()
        }
        self.unavailable_validators = []
        self.running_action = False

        view.edit_validators_button.clicked.connect(self.edit_validators)
        view.preferences_button.clicked.connect(self.open_preferences)
        view.action_button.clicked.connect(self.run_action)
        self.validator_model.layoutChanged.connect(self.update_action_button)
        self.refresh_validators()
        self.view.show()

    def refresh_validators(self):
        """Rebuilds the checklist from the saved validator IDs."""
        validators = []
        self.unavailable_validators = []
        for validator_id in self.model.settings["validators"]:
            validator_class = self.validator_classes.get(validator_id)
            if validator_class is None:
                self.unavailable_validators.append(validator_id)
                continue
            try:
                validators.append(validator_class())
            except Exception:
                logger.exception("Could not create Scene Evaluator validator %s.", validator_id)
                self.unavailable_validators.append(validator_id)

        self.validator_model.set_validators(validators)
        self.view.validator_widget.reset_gui()
        self.view.validator_widget.run_validations_btn.setEnabled(bool(validators))
        if self.unavailable_validators:
            self.view.set_status(f"Unavailable validators ({', '.join(self.unavailable_validators)}).")
        else:
            self.view.set_status("" if validators else "No validators selected.")
        self.update_action_button()

    def edit_validators(self):
        """Opens the validator chooser and saves the confirmed selection."""
        selected_ids = self.model.settings["validators"]
        options = []
        for validator_id, validator_class in self.validator_classes.items():
            try:
                validator = validator_class()
                options.append((validator_id, validator.get_name(), validator.get_description()))
            except Exception:
                logger.exception("Could not load details for validator %s.", validator_id)
                options.append((validator_id, validator_id, "Validator could not be initialized."))
        options.sort(key=lambda option: option[1].casefold())
        options.extend(
            (validator_id, f"{validator_id} (unavailable)", "This validator is missing from the installed library.")
            for validator_id in selected_ids
            if validator_id not in self.validator_classes
        )

        dialog = ValidatorSelectionDialog(options, selected_ids, parent=self.view)
        try:
            if dialog.exec_() != ui_qt.QtWidgets.QDialog.Accepted:
                return
            checked_ids = dialog.selected_validator_ids()
            updated_ids = [validator_id for validator_id in selected_ids if validator_id in checked_ids]
            updated_ids.extend(validator_id for validator_id in checked_ids if validator_id not in selected_ids)
        finally:
            dialog.deleteLater()

        if updated_ids == selected_ids:
            return
        try:
            self.model.save_settings({**self.model.settings, "validators": updated_ids})
        except (ValueError, OSError) as error:
            self.view.set_status(str(error))
            return
        self.refresh_validators()

    def open_preferences(self):
        """Opens the action editor and preset controls."""
        dialog = SceneEvaluatorPreferencesDialog(self.model.settings, parent=self.view)
        dialog.buttons.accepted.connect(lambda: self.save_preferences(dialog))
        dialog.import_button.clicked.connect(lambda: self.import_preset(dialog))
        dialog.export_button.clicked.connect(lambda: self.export_preset(dialog))
        try:
            dialog.exec_()
        finally:
            dialog.deleteLater()

    def save_preferences(self, dialog):
        """Commits the preference draft and closes the dialog on success.

        Args:
            dialog (SceneEvaluatorPreferencesDialog): Dialog containing the staged settings.
        """
        previous_validators = self.model.settings["validators"]
        try:
            self.model.save_settings(dialog.get_settings())
        except (ValueError, OSError) as error:
            dialog.set_status(str(error))
            return
        if previous_validators != self.model.settings["validators"]:
            self.refresh_validators()
        else:
            self.update_action_button()
        dialog.accept()

    def import_preset(self, dialog):
        """Loads a preset into the preference dialog.

        Args:
            dialog (SceneEvaluatorPreferencesDialog): Dialog receiving the imported draft.
        """
        path, _ = ui_qt.QtWidgets.QFileDialog.getOpenFileName(
            dialog, "Import Scene Evaluator Preset", "", PRESET_FILE_FILTER
        )
        if not path:
            return
        try:
            settings = self.model.read_preset(path)
        except (ValueError, OSError) as error:
            dialog.set_status(f"Could not import preset. {error}")
            return
        imports_validators = dialog.include_validators.isChecked() and "validators" in settings
        if not imports_validators:
            settings["validators"] = dialog.draft_settings["validators"]
        dialog.load_settings(settings)
        if imports_validators:
            dialog.set_status("Preset loaded with validator selection. Click Save to apply.")
        else:
            dialog.set_status("Action settings loaded. Click Save to apply them with the current validator selection.")

    def export_preset(self, dialog):
        """Exports the displayed settings with the validator choices if requested.

        Args:
            dialog (SceneEvaluatorPreferencesDialog): Dialog containing the draft to export.
        """
        path, _ = ui_qt.QtWidgets.QFileDialog.getSaveFileName(
            dialog, "Export Scene Evaluator Preset", "scene_evaluator.json", PRESET_FILE_FILTER
        )
        if not path:
            return
        include_validators = dialog.include_validators.isChecked()
        try:
            self.model.write_preset(path, dialog.get_settings(), include_validators=include_validators)
        except (ValueError, OSError) as error:
            dialog.set_status(f"Could not export preset. {error}")
            return
        selection_details = "with validator selection" if include_validators else "with action settings only"
        dialog.set_status(f"Exported {Path(path).name} {selection_details}.")

    def update_action_button(self):
        """Updates the action label, visibility and validation requirement."""
        action = self.model.settings["action"]
        mode = action["mode"]
        action_allowed = True
        tooltip = ""
        if mode == ACTION_REQUIRE_PASS:
            action_allowed = (
                self.validator_model.rowCount() > 0
                and not self.unavailable_validators
                and self.validator_model.all_validations_passed()
            )
            tooltip = "Run validations first. All selected checks must pass."
        elif mode == ACTION_CONFIRM_BYPASS:
            tooltip = "Rechecks validation and asks for confirmation if the checks cannot pass."
        self.view.action_button.setText(action["label"])
        self.view.action_button.setVisible(action["enabled"])
        self.view.action_button.setEnabled(action["enabled"] and action_allowed and not self.running_action)
        self.view.action_button.setToolTip(tooltip)

    def get_action_validation_issue(self, selection_scope, cmds):
        """Rechecks the active scope and reports any obstacle to a passing run.

        Args:
            selection_scope (bool): Whether the scope is the current selection.
            cmds (module): Maya commands for querying the selection.

        Returns:
            str: The unmet requirement, or an empty string if every validator passes.
        """
        if self.unavailable_validators:
            return f"Unavailable validators ({', '.join(self.unavailable_validators)})."
        if self.validator_model.rowCount() == 0:
            return "No validators selected."

        self.view.validator_widget.reset_validators()
        if selection_scope and not cmds.ls(selection=True):
            return "No objects are selected."
        try:
            self.validator_model.run_validators()
        except Exception:
            logger.exception("Scene Evaluator could not complete validation before the action.")
            return "Validation could not complete. See the Script Editor for details."
        if not self.validator_model.all_validations_passed():
            return "Validation did not pass. See the results for details."
        return ""

    def run_action(self):
        """Runs the configured Python action after any required validation."""
        if not self.view.action_button.isEnabled():
            return
        action = self.model.settings["action"]
        selection_scope = self.validator_model.get_scope() == ValidatorScope.SELECTION
        self.running_action = True
        self.update_action_button()
        try:
            from maya import cmds

            mode = action["mode"]
            if mode != ACTION_ALWAYS_ALLOW:
                issue = self.get_action_validation_issue(selection_scope, cmds)
                if issue:
                    if mode == ACTION_REQUIRE_PASS or not self.view.confirm_validation_bypass(issue, action["label"]):
                        self.view.set_status(issue)
                        return

            namespace = {
                "__name__": "__main__",
                "cmds": cmds,
                "validation_scope": "selection" if selection_scope else "scene",
            }
            exec(compile(action["script"], ACTION_SCRIPT_FILENAME, "exec"), namespace)
            self.view.set_status(f"Ran {action['label']}.")
        except (Exception, SystemExit) as error:
            logger.exception("Scene Evaluator action failed.")
            self.view.set_status(f"{action['label']} failed. {error}")
        finally:
            self.running_action = False
            self.update_action_button()
