"""
Scene Validators

Import Line:
    import gt.core.validators.validator_scene as core_data_val_scene
"""

import gt.core.validator as core_val
import gt.core.scene as core_scene
import maya.cmds as cmds
import re
import os


class ValidatorSceneSaved(core_val.ValidatorBase):
    """
    A validator class to ensure the current Maya session is associated with
    a file on disk rather than being an untitled/unsaved scene.
    """

    def __init__(self):
        """
        Initializes the ValidatorSceneSaved instance with a description
        verifying the existence of a valid file path.
        """
        description = "Ensures the scene is saved and has a valid file path."
        super().__init__(description=description)

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Checks if the scene name is not empty, which indicates the file has
        been saved at least once.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it checks
                the global scene status. Defaults to None.
        """
        scene_name = cmds.file(query=True, sceneName=True)
        if scene_name:
            self.set_result(core_val.ValidatorStatus.PASS, "Scene is saved.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, "Scene is currently untitled/unsaved.")

    def repair(self):
        """
        Triggers Maya's internal 'Save Scene As' dialog to prompt the user
        to save the untitled scene.
        """
        cmds.SaveSceneAs()


class ValidatorCleanSceneName(core_val.ValidatorBase):
    """
    A validator class that enforces strict naming conventions for Maya
    scene files to ensure compatibility with pipeline tools and game engines.
    """

    def __init__(self):
        """
        Initializes the ValidatorCleanSceneName instance with rules regarding
        alphanumeric characters and the avoidance of consecutive underscores.
        """
        description = (
            "Ensures scene name contains only alphanumeric characters and underscores, "
            "and does not contain consecutive underscores (e.g., '__')."
        )
        super().__init__(description=description)

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Analyzes the filename for illegal characters or formatting issues
        such as double underscores.

        If the scene is unsaved, it returns a CRITICAL status as there is no
        filename to validate.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator. Defaults to None.
        """
        scene_path = cmds.file(query=True, sceneName=True)
        if not scene_path:
            self.set_result(core_val.ValidatorStatus.CRITICAL, "Scene is unsaved.")
            return

        # Extract just the filename without extension
        scene_filename = os.path.splitext(os.path.basename(scene_path))[0]

        # Check 1: Ensure only alphanumeric characters and underscores are used
        # \w matches [a-zA-Z0-9_]
        has_valid_characters = bool(re.match(r"^\w+$", scene_filename))

        # Check 2: Explicitly disallow double underscores
        has_double_underscores = "__" in scene_filename

        if has_valid_characters and not has_double_underscores:
            self.set_result(core_val.ValidatorStatus.PASS, f"Scene name '{scene_filename}' is valid.")
        else:
            # Determine specific error message for clarity
            error_message = f"Scene name '{scene_filename}' is invalid."
            if not has_valid_characters:
                error_message += " It contains special characters."
            if has_double_underscores:
                error_message += " It contains double underscores ('__')."

            self.set_result(core_val.ValidatorStatus.FAIL, error_message)


class ValidatorSceneFormat(core_val.ValidatorBase):
    """
    A validator class to ensure the Maya scene file is saved using the
    mandated file format (Maya Ascii or Maya Binary).
    """

    def __init__(self, required_format="ma"):
        """
        Initializes the ValidatorSceneFormat instance with the expected
        file extension.

        Args:
            required_format (str, optional): The required extension ('ma' or 'mb').
                Defaults to 'ma'.
        """
        description = f"Ensures scene is saved as a '.{required_format}' file."
        super().__init__(description=description)
        self.required_format = required_format.lower()
        self.set_name(f"Scene Format (.{self.required_format})")

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries the current scene path and validates the file extension
        against the required format.

        If the scene is not yet saved, the validator returns a CRITICAL status.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it checks
                the global scene file extension. Defaults to None.
        """
        scene_path = cmds.file(query=True, sceneName=True)
        if not scene_path:
            self.set_result(core_val.ValidatorStatus.CRITICAL, "Scene is unsaved.")
            return

        if scene_path.lower().endswith(f".{self.required_format}"):
            self.set_result(core_val.ValidatorStatus.PASS, f"Scene is a valid .{self.required_format} file.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Scene is not a .{self.required_format} file.")


class ValidatorNoLayers(core_val.ValidatorBase):
    """
    A validator class to identify and remove custom display, animation, and
    render layers, ensuring the scene remains clean and uses only default layers.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoLayers instance with a description and
        an empty list to track identified non-default layers.
        """
        description = "Ensures no display or animation layers exist (except defaults)."
        super().__init__(description=description)
        self.found_layers = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Scans the scene for all layer types and filters out the mandatory
        Maya default layers.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it targets
                specific layer node types. Defaults to None.
        """
        display_layers = [l for l in cmds.ls(type="displayLayer") if l != "defaultLayer"]
        anim_layers = cmds.ls(type="animLayer") or []
        render_layers = [l for l in cmds.ls(type="renderLayer") if l != "defaultRenderLayer"]

        self.found_layers = display_layers + anim_layers + render_layers

        if not self.found_layers:
            self.set_result(core_val.ValidatorStatus.PASS, "No extra layers found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.found_layers)} layer(s).")

    def select(self):
        """
        Selects the identified non-default display, animation, or render
        layers in the Maya scene.
        """
        if self.found_layers:
            cmds.select(self.found_layers, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if the selection functionality is active based on whether
        non-default layers were discovered.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the base class method.

        Returns:
            bool: True if there are layers to select, False otherwise.
        """
        return super().is_select_available(item_list=self.found_layers)

    def repair(self):
        """
        Deletes the identified non-default layers and re-runs the validation
        to update the status.
        """
        if self.found_layers:
            cmds.delete(self.found_layers)
            self.validate()


class ValidatorNoNamespaces(core_val.ValidatorBase):
    """
    A validator class to identify and remove custom namespaces, ensuring all
    scene nodes are located within the root namespace.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoNamespaces instance with a description
        and an empty list to track identified custom namespaces.
        """
        description = "Ensures no namespaces exist (everything in root)."
        super().__init__(description=description)
        self.namespaces = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries the scene for all namespaces, filtering out Maya's internal
        default namespaces ('UI' and 'shared').

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it checks
                global namespace structures. Defaults to None.
        """
        # Exclude defaults
        defaults = ["UI", "shared"]
        all_ns = cmds.namespaceInfo(listOnlyNamespaces=True, recurse=True) or []
        self.namespaces = [ns for ns in all_ns if ns not in defaults]

        if not self.namespaces:
            self.set_result(core_val.ValidatorStatus.PASS, "No namespaces found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.namespaces)} namespace(s).")

    def repair(self):
        """
        Merges all custom namespaces into the root namespace.

        The namespaces are processed in reverse alphabetical order to ensure
        that nested child namespaces are merged before their parents.
        """
        if self.namespaces:
            # Reverse sort to handle nested namespaces (child first)
            for ns in sorted(self.namespaces, reverse=True):
                try:
                    cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
                except Exception as e:
                    print(f"Could not remove {ns}: {e}")
            self.validate()


class ValidatorNoReferences(core_val.ValidatorBase):
    """
    A validator class to detect the presence of external file references within
    the Maya scene, ensuring all data is local to the file.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoReferences instance with a description
        and an empty list to track identified reference nodes.
        """
        description = "Ensures the scene contains no referenced files."
        super().__init__(description=description)
        self.references = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries the scene for all reference nodes.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it specifically
                targets reference nodes. Defaults to None.
        """
        self.references = cmds.ls(references=True) or []

        if not self.references:
            self.set_result(core_val.ValidatorStatus.PASS, "No references found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.references)} reference(s).")

    def repair(self):
        """
        Attempts to import all identified references into the current scene.
        If a reference cannot be imported, an error is logged to the console.
        Re-runs validation after completion.
        """
        if self.references:
            for ref in self.references:
                try:
                    ref_file = cmds.referenceQuery(ref, filename=True)
                    cmds.file(ref_file, importReference=True)
                except Exception as e:
                    print(f"Could not import reference {ref}: {e}")
            self.validate()


class ValidatorFrameRate(core_val.ValidatorBase):
    """
    A validator class to ensure the Maya scene's playback speed (FPS)
    matches the specified project standard.
    """

    def __init__(self, expected_fps=30.0):
        """
        Initializes the ValidatorFrameRate instance with a target frame rate.

        Args:
            expected_fps (float, optional): The target frames per second for
                the scene. Defaults to 30.0.
        """
        description = f"Ensures scene frame rate is set to {expected_fps}."
        super().__init__(description=description)
        self.expected_fps = float(expected_fps)

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Retrieves the current scene frame rate and compares it against
        the expected value.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it checks
                global scene settings. Defaults to None.
        """
        current_time_unit = core_scene.get_frame_rate()

        if current_time_unit == self.expected_fps:
            self.set_result(core_val.ValidatorStatus.PASS, f"Frame rate is {current_time_unit}.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL, f"Frame rate is {current_time_unit}, expected {self.expected_fps}."
            )

    def repair(self):
        """
        Sets the Maya scene's frame rate to the expected FPS value and
        re-runs the validation to update the status.
        """
        core_scene.set_frame_rate(frame_rate=self.expected_fps)
        self.validate()


class ValidatorSceneUnits(core_val.ValidatorBase):
    """
    A validator class to verify that the Maya scene's linear working units
    are set to the production standard of centimeters.
    """

    def __init__(self):
        """
        Initializes the ValidatorSceneUnits instance with a specific
        description for linear unit requirements.
        """
        description = "Ensures scene linear units are set to 'cm'."
        super().__init__(description=description)

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries the current linear working units in Maya and compares them
        against the required 'cm' setting.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it checks
                global scene settings. Defaults to None.
        """
        current_unit = cmds.currentUnit(query=True, linear=True)

        if current_unit == "cm":
            self.set_result(core_val.ValidatorStatus.PASS, "Scene units are 'cm'.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Scene units are '{current_unit}', expected 'cm'.")

    def repair(self):
        """
        Sets the Maya scene's linear working units to centimeters and
        re-runs the validation to update the status.
        """
        cmds.currentUnit(linear="cm")
        self.validate()


class ValidatorUpAxisY(core_val.ValidatorBase):
    """
    A validator class to ensure the Maya scene adheres to a Y-up coordinate system.
    """

    def __init__(self):
        """
        Initializes the ValidatorUpAxisY instance with a description defining
        the requirement for a Y-up coordinate system.
        """
        description = "Ensures the scene world coordinate system up-axis is set to 'Y' (not Z)."
        super().__init__(description=description)

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries the current Maya world up-axis and compares it against the 'y' standard.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it checks
                global scene settings. Defaults to None.
        """
        current_axis = cmds.upAxis(query=True, axis=True)

        if current_axis == "y":
            self.set_result(core_val.ValidatorStatus.PASS, "Up-axis is correctly set to Y.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Up-axis is '{current_axis}', expected 'y'.")

    def repair(self):
        """
        Fixes the scene configuration by forcefully setting the world up-axis to 'y'.
        Automatically re-runs validation to update the status.
        """
        cmds.upAxis(axis="y")
        self.validate()


if __name__ == "__main__":
    a_val_test = ValidatorUpAxisY()
    a_val_test.validate()
    # a_val_test.repair()

    print(" Validation ".center(65, "#"))
    print(a_val_test.get_status())
    print(a_val_test.get_feedback())
