import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.ui.validator_widget as ui_validator
import gt.ui.resource_library as ui_res_lib
import gt.core.validator as core_val
import maya.cmds as cmds
import logging
import importlib
import inspect

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleValidation(tools_rig_frm.ModuleGeneric):
    """
    Auto-rigger module to store, manage, and run validations.

    This module holds a list of validation class *names* (str) which
    it retrieves from core_val.ValidatorLibrary. It uses a ValidatorModel
    to manage and run them.
    """

    _default_name = "Validation"
    __version__ = "1.0.4"
    icon = ui_res_lib.Icon.tool_validator
    allow_parenting = False
    allow_multiple = False

    def __init__(self, name=_default_name, prefix=None, suffix=None):
        """
        Initializes the Validation module.

        Args:
            name (str, optional): The module name.
            prefix (str, optional): Prefix string for naming. Defaults to None.
            suffix (str, optional): Suffix string for naming. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        # Hook "run_post_build_validation" into the post-build process
        self.set_extra_callable_function(self.run_post_build_validation, order=tools_rig_frm.CodeData.Order.post_build)

        # List of string *names* of ValidatorBase-derived classes
        # e.g., "NodeSceneNamePrefix"
        self.validations = []

        # It's initialized empty and will be populated by other methods.
        self.validation_model = ui_validator.ValidatorModel(validators=[])

    @staticmethod
    def _get_validation_class_from_library(class_name):
        """
        Retrieves a class object from the ValidatorLibrary by its name.

        Args:
            class_name (str): The string name of the class,
                              e.g., 'NodeSceneNamePrefix'.

        Returns:
            type: The class object, or None if not found or not a valid class.
        """
        validation_class = getattr(core_val.ValidatorLibrary, class_name, None)

        if validation_class is None:
            logger.error(f"Validator '{class_name}' not found in ValidatorLibrary.")
            return None

        if not (inspect.isclass(validation_class) and issubclass(validation_class, core_val.ValidatorBase)):
            logger.error(f"Attribute '{class_name}' in ValidatorLibrary is not a valid Validator class.")
            return None

        return validation_class

    def _sync_model_to_list(self):
        """
        Clears and repopulates the existing model from `self.validations`.

        This method ensures the model instance is in sync with the
        `self.validations` list without replacing the model object itself.
        This assumes `self.validation_model` has `clear_validators()` and
        `add_validator()` methods that emit the correct PySide2 signals.
        """
        logger.debug("Syncing validation model from list...")

        # ValidatorModel that emits signals
        self.validation_model.clear_validators()

        for validation_name in self.validations:
            validation_class = self._get_validation_class_from_library(validation_name)

            if not validation_class:
                continue

            try:
                instance = validation_class()
                # Assumed method on ValidatorModel that emits signals
                self.validation_model.add_validator(instance)
            except Exception as e:
                logger.error(f"Error instantiating validation {validation_name}: {e}")

        logger.debug(f"Validation model synced with {len(self.validations)} validators.")

    # --- Public API for UI ---

    def set_validation_list(self, validation_names):
        """
        Sets the list of validation class names and syncs the model.

        This clears the existing model and repopulates it, notifying any
        connected UI views of the change.

        Args:
            validation_names (list[str]): A list of string names
                                          for the validator classes.
        """
        self.validations = validation_names
        # CHANGED: Instead of invalidating, we sync the persistent model
        self._sync_model_to_list()

    def get_validation_list(self):
        """
        Gets the current list of validation class names.

        Returns:
            list[str]: The list of validation names.
        """
        return self.validations

    def clear_validations(self):
        """Clears the validation list and updates the model."""
        self.validations = []
        # Directly clear the model, which should be faster and emit the correct signals.
        if self.validation_model:
            self.validation_model.clear_validators()

    def add_validation(self, validation_name):
        """
        Adds a single validation name and updates the model.

        Args:
            validation_name (str): The string name of the validator class.
        """
        if validation_name not in self.validations:
            validation_class = self._get_validation_class_from_library(validation_name)
            if not validation_class:
                return  # Error already logged by helper

            try:
                instance = validation_class()
                self.validations.append(validation_name)
                # Add the new instance directly to the model.
                # Assumes ValidatorModel.add_validator() emits signals.
                self.validation_model.add_validator(instance)
            except Exception as e:
                logger.error(f"Error instantiating validation {validation_name}: {e}")

    def remove_validation(self, validation_name):
        """
        Removes a single validation name from the list and updates the model.

        Args:
            validation_name (str): The string name of the validator class.
        """
        if validation_name in self.validations:
            self.validations.remove(validation_name)
            # Tell the model to remove the item by its name.
            # Assumes ValidatorModel.remove_validator_by_name()
            # finds the instance and emits the correct signals.
            self.validation_model.remove_validator_by_name(validation_name)

    def get_validation_model(self, force_rebuild=False):
        """
        Gets the persistent validation model instance.

        This is the primary method the UI will call to get the data model.
        The model instance is persistent and is updated by other methods.

        Args:
            force_rebuild (bool, optional): If True, forces a full sync
                between `self.validations` list and the model.
                Defaults to False.

        Returns:
            ValidatorModel: The persistent instance of the ValidatorModel.
        """
        # The model is never None, so we just check for force_rebuild
        if force_rebuild:
            self._sync_model_to_list()
        return self.validation_model

    # --- Post-Build Hook ---

    def run_post_build_validation(self):
        """
        Runs all validations specified in the `self.validations` list.

        This function is called as a post-build step. It builds the model,
        runs the validators, and logs the results to the script editor.
        """
        _alternative_name = ""
        if self.get_name() != ModuleValidation._default_name:  # If different from original, mention it.
            _alternative_name = f" ({self.get_name()})"
        logger.info(f" Running Validation Module.{_alternative_name}")

        # Get the model, forcing a sync to ensure it matches the list.
        # This now updates the *existing* model instance.
        model = self.get_validation_model(force_rebuild=True)

        if not model or not model.validators:
            logger.warning("No validations specified or model failed to build. Skipping.")
            return

        # Run the validations within the model
        model.run_validators()

        failed_validations = []

        # Log the results from the model
        for validator_instance in model.validators:
            status_name = validator_instance.status.name
            logger.info(f"> {validator_instance.name}: {status_name}")

            if validator_instance.status != core_val.ValidatorStatus.PASS:
                logger.warning(f"    Feedback: {validator_instance.feedback}")

            if validator_instance.status not in [core_val.ValidatorStatus.PASS, core_val.ValidatorStatus.NOT_RUN]:
                failed_validations.append(validator_instance.name)

        if model.all_validations_passed():
            logger.info("Validation Complete: All checks passed!")
        else:
            fail_count = len(failed_validations)
            check_str = "check" if fail_count == 1 else "checks"
            warning_message = f"Validation Complete: {fail_count} {check_str} failed."
            logger.warning(warning_message)
            cmds.warning(warning_message)


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)

    cmds.file(new=True, force=True)

    # --- Setup for integration test ---
    import gt.core.session as core_session
    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils
    import gt.core.validator as core_val
    import importlib
    import tempfile
    import sys
    import os

    # Auto Reload Script
    core_session.remove_modules_startswith("gt.tools.auto_rigger.module")
    core_session.remove_modules_startswith("gt.tools.auto_rigger.rig")
    core_session.remove_modules_startswith("gt.ui.validator_widget")

    # importlib.reload(tools_rig_fmr)
    # importlib.reload(tools_rig_utils)
    # importlib.reload(ui_validator)
    # importlib.reload(core_val)  # Reload validator to get ValidatorLibrary

    # 1. Create an instance of the validation module
    my_validation_module = ModuleValidation()

    # 2. Set the list of validators you want to run, using just their names
    my_validation_module.set_validation_list(["NodeSceneNamePrefix", "MeshSceneNamePrefix"])

    # 3. Add the module to your rig project
    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(my_validation_module)

    # 4. When you build, the module will find those classes
    # in ValidatorLibrary and run them.
    a_project.build_rig()
