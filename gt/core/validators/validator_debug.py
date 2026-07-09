"""
Debug Validators
A collection of debugging validators designed to test the validation system
by forcing specific outcomes (pass, warn, fail, critical).

Import Line:
    import gt.core.validators.validator_debug as core_data_val_debug
"""

import gt.core.validator as core_val
import maya.cmds as cmds
import logging


class ValidatorDebugAlwaysPass(core_val.ValidatorBase):
    """
    A debug validator that always returns a successful validation.
    """

    def __init__(self):
        """Initializes the validator."""
        description = "A debug validator that always passes."
        super().__init__(description=description)
        self.set_name("Debug Always Pass")

    def validate(self, **kwargs):
        """
        Runs the validation, always setting the result to PASS.
        Args:
            kwargs (Any): Keyword argument. Not used.
        """
        self.set_result(status=core_val.ValidatorStatus.PASS, feedback="Debug validator passed successfully.")


class ValidatorDebugAlwaysWarn(core_val.ValidatorBase):
    """
    A debug validator that always returns a warning and can select
    the perspective camera.
    """

    def __init__(self):
        """Initializes the validator."""
        description = "A debug validator that always returns a warning."
        super().__init__(description=description)
        self.set_name("Debug Always Warn")
        self.selectable = ["persp"]

    def validate(self, **kwargs):
        """
        Runs the validation, always setting the result to WARNING.
        Args:
            kwargs (Any): Keyword argument. Not used.
        """
        self.set_result(status=core_val.ValidatorStatus.WARNING, feedback="This is a forced debug warning.")

    def select(self):
        """Selects the perspective camera."""
        logging.info('Attempting to select "persp" camera as test.')
        cmds.select(self.selectable, replace=True)


class ValidatorDebugAlwaysFail(core_val.ValidatorBase):
    """
    A debug validator that always fails.
    """

    def __init__(self):
        """Initializes the validator."""
        description = f"A debug validator that always returns a failure"
        super().__init__(description=description)
        self.set_name("Debug Always Fail")

    def validate(self, **kwargs):
        """
        Forces a failure.
        Args:
            kwargs (Any): Keyword argument. Not used.
        """
        self.set_result(status=core_val.ValidatorStatus.FAIL, feedback="This is a forced debug failure.")


class ValidatorDebugRepairableFail(core_val.ValidatorBase):
    """
    A debug validator that always fails if a specific node is missing
    and provides a repair function to create it.
    """

    NODE_NAME = "debug_cube"

    def __init__(self):
        """Initializes the validator."""
        description = (
            f"A debug validator that returns a failure, but it's repairable. "
            f"Checks for the existence of '{self.NODE_NAME}' and fails if it's missing."
        )
        super().__init__(description=description)
        self.set_name("Debug Fail (Repairable)")

    def validate(self, **kwargs):
        """
        Checks for the existence of 'debug_cube'.
        Args:
            kwargs (Any): Keyword argument. Not used.
        """
        if cmds.objExists(self.NODE_NAME):
            self.set_result(status=core_val.ValidatorStatus.PASS, feedback="Debug cube already exists.")
        else:
            self.set_result(status=core_val.ValidatorStatus.FAIL, feedback=f"Node '{self.NODE_NAME}' is missing.")

    def repair(self):
        """
        Repairs the scene by creating the missing 'debug_cube'.
        """
        if not cmds.objExists(self.NODE_NAME):
            cmds.polyCube(name=self.NODE_NAME)

        # Re-validate to update the status
        self.validate()


class ValidatorDebugAlwaysCriticalFail(core_val.ValidatorBase):
    """
    A debug validator that always returns a critical failure.
    """

    def __init__(self):
        """Initializes the validator."""
        description = "A debug validator that always returns a critical failure."
        super().__init__(description=description)
        self.set_name("Debug Critical Fail")

    def validate(self, **kwargs):
        """
        Runs the validation, always setting the result to CRITICAL.
        Args:
            kwargs (Any): Keyword argument. Not used.
        """
        self.set_result(status=core_val.ValidatorStatus.CRITICAL, feedback="This is a forced debug critical failure.")
