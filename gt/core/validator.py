"""
Validation Module containing the framework and class with available validators.

Import Line:
    import gt.core.validator as core_val

Importing Validation Objects:
import gt.core.data.validators as data_val

Typical Usage:
    # --------------------------- Example A - Node Validator ---------------------------
    # 1. Subclass ValidatorBase to create a specific check.
    class ValidatorNodeExists(core_val.ValidatorBase):
        '''Checks if a specific node exists in the scene.'''

        def __init__(self, none_name="myScript"):
            # It's good practice to call the parent's __init__.
            description = f'Checks if "{none_name}" node exists in the scene.'
            super().__init__(description=description)
            self.node_name = none_name
            # A custom name can be set to be more descriptive, otherwise it becomes "Node Exists".
            self.set_name(f"Node Exists: '{self.node_name}'")

        def validate(self, *args, **kwargs):
            '''Checks if `self.node_name` exists.'''
            if cmds.objExists(self.node_name):
                status = core_val.ValidatorStatus.PASS
                feedback = f"'{self.node_name}' was found in the scene."
            else:
                status = core_val.ValidatorStatus.FAIL
                feedback = f"Could not find node '{self.node_name}'."
            self.set_result(status=status, feedback=feedback)

        def repair(self):
            '''Creates a script node with the expected name.'''
            cmds.createNode("script", name=self.node_name)
            # Do not re-run validation to confirm the fix, this is handled by upper logic using the validator.

    # 2. Instantiate and run the validator.
    a_node_validation = ValidatorNodeExists('AnotherName')
    a_node_validation.validate()

    # 3. Check the results.
    print(f"Status: {a_node_validation.get_status()}")
    print(f"Feedback: {a_node_validation.get_feedback()}")

    # 4. Attempt a repair if available and needed.
    # The check is now simpler and encapsulated in the method.
    if a_node_validation.is_repair_available():
        a_node_validation.repair()
        a_node_validation.validate()
        print(f"Status after repair: {a_node_validation.get_status().name}")

    # --------------------------- Example B - Forbidden Object Validator ---------------------------
    class ValidatorForbiddenObjects(core_val.ValidatorBase):
        '''Checks for a list of objects that should not be in the scene.'''
        def __init__(self, forbidden_objects):
            description = "Checks for objects that should not be in the scene (e.g., default primitives)."
            super().__init__(description=description)
            self.forbidden_objects = forbidden_objects
            self.found_objects = []

        def validate(self, *args, **kwargs):
            '''Finds any forbidden objects that currently exist.'''
            self.found_objects = [name for name in self.forbidden_objects if cmds.objExists(name)]

            if not self.found_objects:
                status = core_val.ValidatorStatus.PASS
                feedback = "No forbidden objects found."
            else:
                status = core_val.ValidatorStatus.FAIL
                feedback = f"Found {len(self.found_objects)} forbidden object(s)."
            self.set_result(status=status, feedback=feedback)

        def select(self):
            '''Selects the forbidden objects that were found.'''
            if self.found_objects:
                cmds.select(self.found_objects, replace=True)
                logger.info(f"Selected {len(self.found_objects)} forbidden object(s).")

        def is_select_available(self, **kwargs):
            '''
            Overrides the base check to provide the internal list of found objects.
            This simplifies the external API call.
            '''
            return super().is_select_available(item_list=self.found_objects)

    # 1. Create a scene with a valid object and some forbidden objects.
    cmds.polyTorus(name="valid_asset_geo")
    cmds.polyCube(name="pCube1")
    cmds.polySphere(name="pSphere1")

    # 2. Instantiate the validator with the list of names to check for.
    forbidden_list = ['pCube1', 'pSphere1', 'pCylinder1']
    a_forbidden_obj_validation = ValidatorForbiddenObjects(forbidden_list)
    a_forbidden_obj_validation.validate()

    # 3. Check the results. The feedback is now neutral and UI-agnostic.
    print(f"Status: {a_forbidden_obj_validation.get_status().name}")
    print(f"Feedback: {a_forbidden_obj_validation.get_feedback()}") # e.g., "Found 2 forbidden object(s)."

    # 4. The call is simpler because the subclass handles the internal logic.
    if a_forbidden_obj_validation.is_select_available():
        print("Running select to highlight failing objects...")
        a_forbidden_obj_validation.select()
        # The objects pCube1 and pSphere1 will now be selected in Maya.
"""

import gt.utils.system as utils_sys
import gt.core.str as core_str
import traceback
import logging
import inspect
import enum

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ValidatorStatus(enum.IntEnum):
    """
    Defines the potential outcomes of a validation check.

    Members:
        NOT_RUN: The initial state before the validator has been executed.
        PASS: The check was successful and all conditions were met.
        WARNING: The check passed, but there is a non-critical issue or
            additional information for the user.
        FAIL: The check did not meet the requirements, indicating a fixable
            or non-blocking issue.
        CRITICAL: The check failed with a critical error, which could trigger
            failures in other pipeline modules and lead to unpredictable or
            corrupt results.
    """

    NOT_RUN = 0
    PASS = 1
    WARNING = 2
    FAIL = 3
    CRITICAL = 4


class ValidatorScope(enum.IntEnum):
    """
    Defines the scope for a validation check.
    This is not applicable to all validators. If checking the frame-rate for example, the scene will be checked.

    Members:
        SCENE: The validation will run on all applicable objects in the entire scene.
        SELECTION: The validation will only run on the currently selected objects.
    """

    SCENE = 0
    SELECTION = 1
    TYPE = 2  # When using this scope, a type should also be provided. e.g. validate(nope_type="mesh")


class ValidatorBase:
    """
    A base class for creating validators.

    This class provides a standard interface for validation checks. Subclasses
    should implement the `validate` method with their specific logic and can
    optionally override the `repair` or 'select' methods to provide the validation
    with extra functionality.

    Attributes:
        name (str): A display name for the validator. This is by default automatically
                    generated from the class name (e.g., ValidatorFrameRate becomes "Frame Rate")
                    but can be manually overridden or set using the name setter "set_name()".
                    (e.g., self.set_name("Frame Rate 30fps").
        description (str): A short summary of what the validator checks for, which should be ideally
                           provided during initialization, overridden by the subclass or set using the description
                           setter. e.g. self.set_description("Ensures the scene frame rate is set to 30fps.").
        feedback (str): A user-facing message carries a message to explains the outcome of the validation.
                        This should in most cases be set by the validate method by either overriding the variable
                        or using the setter "set_feedback()".
                        e.g., self.set_feedback("Frame rate is 24fps, but should be 30fps.").
                        Alternatively, the feedback can be set using "set_result(status, feedback)",
                        which sets the status and feedback at the same time.
        status (ValidatorStatus): The validator's current state, represented by a ValidationStatus attribute.
                                   The default state is "NOT_RUN" until the validate method sets its final status.
                                   This is ideally set during the validate method.
                                   Alternatively, the status can be set using "set_result(status, feedback)",
                                   which sets the status and feedback at the same time.
    """

    def __init__(self, name=None, description=""):
        """
        Initializes a base validator.
        This method generates the validator's display name from its class name
        and sets the initial status to `NOT_RUN`.
        Args:
            name (str, optional): A name for the validator. In most cases, this is not needed as it will
                                  automatically inherit the name from the class name. Only an option in case
                                   a validation object has different parameters and need a different name
                                   to express that.
            description (str, optional): A description of what this validation is validating.
                                         The validation can be initialized with a description
                                         already or set at any point using the description setter "set_description()".

        Example:
            class ValidatorFrameRate(ValidatorBase):
                description = "Checks if the frame rate is set to 30fps."
            validator = ValidatorFrameRate()
            # Output: My Custom
            # Output: <ValidatorStatus.NOT_RUN: 0>
        """
        self.name = name or self.get_validator_class_name(remove_validator_prefix=True, formatted=True)
        self.description = description
        self.feedback = ""
        self.status = ValidatorStatus.NOT_RUN

    # ----------------------------------------------- Setters ---------------------------------------------------
    def set_name(self, name):
        """
        Sets a custom display name for the validator.

        Args:
            name (str): The desired display name.

        Example:
            self.set_name("Frame Rate 30fps")
        """
        if not isinstance(name, str):
            raise TypeError(f"Expected name to be a string, got {type(name).__name__}")
        self.name = name

    def set_description(self, description):
        """
        Sets or updates the validator's description.

        Args:
            description (str): A human-readable description of what this validation checks.

        Example:
            self.set_description("Ensures that all meshes have proper naming conventions.")
        """
        if not isinstance(description, str):
            raise TypeError(f"Expected description to be a string, got {type(description).__name__}")
        self.description = description

    def set_feedback(self, feedback):
        """
        Sets or updates the feedback message for this validator.

        Args:
            feedback (str): A user-facing message explaining the validation outcome.

        Example:
            self.set_feedback("Frame rate is 24fps, should be 30fps.")
        """
        if not isinstance(feedback, str):
            raise TypeError(f"Expected feedback to be a string, got {type(feedback).__name__}")
        self.feedback = feedback

    def set_result(self, status, feedback=None):
        """
        Sets both the validation status and feedback at once.

        Args:
            status (ValidatorStatus): The result of the validation.
            feedback (str, optional): A message describing the result.

        Example:
            self.set_result(ValidationStatus.PASS, "Frame rate is correct.")
        """
        # Ensure the status is a valid member of ValidatorStatus
        if not isinstance(status, ValidatorStatus):
            if status in ValidatorStatus.__members__.values():
                status = ValidatorStatus(status)
            else:
                raise TypeError(f"Warning: '{status}' is not a valid ValidatorStatus. Status not updated.")

        self.status = status

        if feedback is not None and isinstance(feedback, str):
            self.set_feedback(feedback)

    # ----------------------------------------------- Getters ---------------------------------------------------
    def get_name(self):
        """
        Retrieves the display name of the validator.

        Returns:
            str: The validator's display name.
        """
        return self.name

    def get_description(self):
        """
        Retrieves the description of the validator.

        Returns:
            str: The description of what the validator checks.
        """
        return self.description

    def get_status(self):
        """
        Retrieves the current status of the validator.

        Returns:
            ValidatorStatus: The validator's current status enum member.
        """
        return self.status

    def get_feedback(self):
        """
        Retrieves the current feedback message.

        Returns:
            str: The user-facing feedback message.
        """
        return self.feedback

    # ------------------------------------------------- Core ----------------------------------------------------
    def validate(self, scope=ValidatorScope.SCENE, node_type=None):
        """
        Executes the main validation logic and updates the instance's state.

        This method must be **overridden** by subclasses. The implementation
        should perform a specific check and determine the status and feedback message.

        Args:
        scope (ValidatorScope, optional): Determines the validation scope. (What is being checked)
                                          Defaults to SCENE, but it can be changed to be only selection or types.
        node_type (str, optional): The node type is used to filter by type when validating with the TYPE scope.
                                   Examples, 'mesh' or 'joint'.

        Example:
            class ValidationNodeExists(ValidatorBase):
                def validate(self):
                    if cmds.objExists('pCube1'):
                        _status = ValidatorStatus.PASS
                        _feedback = "'pCube1' was found in the scene."
                    else:
                        _status = ValidatorStatus.FAIL
                        _feedback = "Could not find 'pCube1'."
                    self.set_result(status=_status, feedback=_feedback)
        """
        raise NotImplementedError(f"{self.__class__.__name__}.validate() must be implemented.")

    # ------------------------------------------------ Repair ---------------------------------------------------
    def repair(self):
        """Attempts to automatically fix a failed validation and re-runs the check.

        This method must be **overridden** by subclasses that provide an
        automatic fix.

        The override implementation should contain the specific logic to resolve
        the issue. The override should not set `self.status` or
        `self.feedback` directly; a call to `validate()` can handle that as a separate pass.

        Example:
            # In a subclass:
            def repair(self):
                # 1. Perform the specific fix logic.
                cmds.polyCube(name='pCube1')

                # 2. Re-validate as the very last step.
                self.validate()
        """

    def is_repair_available(self):
        """
        Checks if a repair action can and should be performed.

        A repair is considered available if the `repair` method has been overridden
        in the subclass and the validation status is another status other than NOT_RUN or PASS.

        Returns:
            bool: True if a repair action can be performed, otherwise False.
        """
        method_implemented = utils_sys.is_method_overridden(
            base_class=ValidatorBase,
            target_class_or_instance=self,
            method_name="repair",
        )
        is_necessary = self.status > ValidatorStatus.WARNING
        return method_implemented and is_necessary

    # ------------------------------------------------ Select ---------------------------------------------------
    def select(self):
        """
        Selects objects in the scene relevant to the validation result.

        This method can be **overridden** by subclasses to provide a way to
        select the components related to a validation failure.

        The override implementation should **not** modify the validator's state
        (e.g., `self.feedback` or `self.status`).

        Example:
            # In a subclass designed to select objects with a specific property:
            def select(self):
                '''Finds and selects all currently hidden mesh objects.'''
                # This logic re-queries the scene to find the relevant nodes.
                hidden_mesh_transforms = cmds.listRelatives(
                    cmds.ls(type='mesh', visible=False, long=True),
                    parent=True,
                    fullPath=True
                ) or []

                if hidden_mesh_transforms:
                    cmds.select(hidden_mesh_transforms, replace=True)
        """

    def is_select_available(self, item_list=None):
        """
        Checks if a selection action can and should be performed.

        A selection is available if the `select` method is overridden, the
        status is WARNING or worse, and the optional `item_list` is not empty.

        Args:
            item_list (list, optional): If provided, the check will also ensure
                this list contains items before returning True. This is useful for
                confirming there are objects to select. Defaults to None.

        Returns:
            bool: True if a select action can be performed, otherwise False.
        """
        method_implemented = utils_sys.is_method_overridden(
            base_class=ValidatorBase,
            target_class_or_instance=self,
            method_name="select",
        )
        is_relevant = self.status > ValidatorStatus.PASS

        # If an item_list is passed, it must not be empty.
        has_items = True
        if item_list is not None:
            has_items = bool(item_list)

        return method_implemented and is_relevant and has_items

    # ----------------------------------------------- Utilities -------------------------------------------------
    def get_validator_class_name(self, remove_validator_prefix=False, formatted=False):
        """
        Generates a display name from the validator's class name.

        Args:
            remove_validator_prefix (bool, optional): If True, removes the
                'Validator' prefix from the class name. Defaults to False.
            formatted (bool, optional): If True, splits a CamelCase name into
                separate words. Defaults to False. e.g. "FrameRate" becomes "Frame Rate".

        Returns:
            str: The generated display name.
        """

        _class_name = str(self.__class__.__name__)
        if remove_validator_prefix:
            _class_name = core_str.remove_prefix(input_string=str(self.__class__.__name__), prefix="Validator")
        if formatted:
            _class_name = " ".join(core_str.camel_case_split(_class_name))
        return _class_name

    @staticmethod
    def _get_nodes(scope, node_type, transforms=False):
        """
        Retrieve nodes of a given type based on the validation scope.

        If the scope is SELECTION, all nodes of the given type found under the
        currently selected transforms (including all descendants) are returned.
        Otherwise, all nodes of the given type in the scene are returned.

        Args:
            scope (core_val.ValidatorScope): Scope used to determine whether
                to query the current selection or the entire scene.
            node_type (str): Maya node type to retrieve (e.g. "mesh",
                "nurbsSurface", "nurbsCurve").
            transforms (bool, optional): If True, parent transforms of the found
                nodes are returned instead of the nodes themselves.

        Returns:
            list[str]: Full DAG paths to nodes of the given type or their transforms.
        """
        import maya.cmds as cmds

        if scope == ValidatorScope.SELECTION:
            sel = cmds.ls(selection=True, long=True) or []
            nodes = cmds.listRelatives(sel, allDescendents=True, type=node_type, fullPath=True) or []
        else:
            nodes = cmds.ls(type=node_type, long=True) or []

        if not transforms:
            return nodes

        parent_transforms = cmds.listRelatives(nodes, parent=True, fullPath=True) or []

        # Remove duplicates
        return list(set(parent_transforms))

    @staticmethod
    def _get_transforms(scope, ignore_cameras=True):
        """
        Retrieve transform nodes based on the given validation scope.

        If the scope is SELECTION, only the currently selected transform
        nodes are returned. Otherwise, all transform nodes in the scene
        are returned.

        Args:
            scope (core_val.ValidatorScope): Scope used to determine whether
                to query the current selection or the entire scene.
            ignore_cameras (bool, optional): If True, transforms that have
                camera shapes as children are excluded.

        Returns:
            list[str]: Full DAG paths to transform nodes.
        """
        import maya.cmds as cmds

        if scope == ValidatorScope.SELECTION:
            transforms = cmds.ls(selection=True, type="transform", long=True) or []
        else:
            transforms = cmds.ls(type="transform", long=True) or []

        if not ignore_cameras:
            return transforms

        # Find all camera transforms
        camera_shapes = cmds.ls(type="camera", long=True) or []
        camera_transforms = set(cmds.listRelatives(camera_shapes, parent=True, fullPath=True) or [])

        # Filter out camera transforms
        return [t for t in transforms if t not in camera_transforms]


ValidatorLibrary = None
try:
    """Try/catch used to avoid circular imports when running validators directly from their scripts."""

    class ValidatorLibrary:
        """
        A library of available validators.
        This might not be a comprehensive list because validators in development might not be included here.
        """

        import gt.core.validators.validator_anim as core_data_val_anim
        import gt.core.validators.validator_debug as core_data_val_debug
        import gt.core.validators.validator_material as core_data_val_mat
        import gt.core.validators.validator_mesh as core_data_val_mesh
        import gt.core.validators.validator_node as core_data_val_node
        import gt.core.validators.validator_rig as core_data_val_rig
        import gt.core.validators.validator_scene as core_data_val_scene

        # Anim
        NoTimeKeyframes = core_data_val_anim.ValidatorNoTimeKeyframes

        # Debug
        DebugAlwaysPass = core_data_val_debug.ValidatorDebugAlwaysPass
        DebugAlwaysWarn = core_data_val_debug.ValidatorDebugAlwaysWarn
        DebugAlwaysFail = core_data_val_debug.ValidatorDebugAlwaysFail
        DebugRepairableFail = core_data_val_debug.ValidatorDebugRepairableFail
        DebugAlwaysCriticalFail = core_data_val_debug.ValidatorDebugAlwaysCriticalFail

        # Material
        NoUnusedMaterials = core_data_val_mat.ValidatorNoUnusedMaterials
        BrokenTexturePaths = core_data_val_mat.ValidatorBrokenTexturePaths
        NoLambert1MeshAssignment = core_data_val_mat.ValidatorNoLambert1MeshAssignment
        MaterialNaming = core_data_val_mat.ValidatorMaterialNaming

        # Mesh
        ValidatorHistory = core_data_val_mesh.ValidatorHistory
        MeshSceneNamePrefix = core_data_val_mesh.ValidatorMeshSceneNamePrefix
        MeshFrozenTransforms = core_data_val_mesh.ValidatorMeshFrozenTransforms
        NonManifold = core_data_val_mesh.ValidatorNonManifold
        NGons = core_data_val_mesh.ValidatorNGons
        MeshCustomNaming = core_data_val_mesh.ValidatorMeshCustomNaming
        NoEmptyUVSets = core_data_val_mesh.ValidatorNoEmptyUVSets
        SingleUVChannel = core_data_val_mesh.ValidatorSingleUVChannel
        UVFaceCrossQuadrant = core_data_val_mesh.ValidatorUVFaceCrossQuadrant

        # Node
        NodeSceneNamePrefix = core_data_val_node.ValidatorNodeSceneNamePrefix
        NoUnknownNodes = core_data_val_node.ValidatorNoUnknownNodes
        UniqueDAGNames = core_data_val_node.ValidatorUniqueDAGNames
        UniqueDAGNamesIgnoreShapes = core_data_val_node.ValidatorUniqueDAGNamesIgnoreShapes
        UniqueDAGNamesLODAware = core_data_val_node.ValidatorUniqueDAGNamesLODAware
        InvisibleTransforms = core_data_val_node.ValidatorInvisibleTransforms
        PivotOrigin = core_data_val_node.ValidatorPivotOrigin
        NoForeignScriptNodes = core_data_val_node.ValidatorNoForeignScriptNodes
        NoImagePlanes = core_data_val_node.ValidatorNoImagePlanes

        # Rig
        BasicRigHierarchy = core_data_val_rig.ValidatorBasicRigHierarchy
        FullRigHierarchy = core_data_val_rig.ValidatorFullRigHierarchy
        ZeroedControls = core_data_val_rig.ValidatorZeroedControls
        MaxInfluences = core_data_val_rig.ValidatorMaxInfluences
        MaxInfluencesFour = core_data_val_rig.ValidatorMaxInfluencesFour
        MaxInfluencesEight = core_data_val_rig.ValidatorMaxInfluencesEight
        UnusedInfluences = core_data_val_rig.ValidatorUnusedInfluences
        BoundRigMeshes = core_data_val_rig.ValidatorBoundRigMeshes
        NoEmptyGroups = core_data_val_rig.ValidatorNoEmptyGroups
        NoEmptyGroupsRoot = core_data_val_rig.ValidatorNoEmptyGroupsRoot
        SingleRootJoint = core_data_val_rig.ValidatorSingleRootJoint
        JointNaming = core_data_val_rig.ValidatorJointNaming

        # Scene
        SceneSaved = core_data_val_scene.ValidatorSceneSaved
        CleanSceneName = core_data_val_scene.ValidatorCleanSceneName
        SceneFormat = core_data_val_scene.ValidatorSceneFormat
        NoLayers = core_data_val_scene.ValidatorNoLayers
        NoNamespaces = core_data_val_scene.ValidatorNoNamespaces
        NoReferences = core_data_val_scene.ValidatorNoReferences
        FrameRate = core_data_val_scene.ValidatorFrameRate
        SceneUnits = core_data_val_scene.ValidatorSceneUnits
        UpAxisY = core_data_val_scene.ValidatorUpAxisY

        @classmethod
        def get_available_validators(cls):
            """
            Inspects the ValidatorLibrary and returns all found validator class names.

            This is a helper function for a UI to discover available validators.

            Returns:
                list[str]: A sorted list of class names (str) found in
                           this class that inherit from ValidatorBase.
            """
            validator_names = []
            # Use inspect.getmembers to get all attributes of this class
            for name, obj in inspect.getmembers(cls):
                if name.startswith("_"):
                    continue  # Skip private/dunder attributes

                # Check if it's a class and if it inherits from ValidatorBase
                if (
                    inspect.isclass(obj)
                    and issubclass(obj, ValidatorBase)
                    and obj != ValidatorBase  # Don't include the base class
                ):
                    validator_names.append(name)

            return sorted(list(set(validator_names)))

except Exception as e:
    logger.debug(e)
    traceback.print_exc()
    logger.warning(
        f"Unable to initialize ValidatorLibrary. Likely due to local script initialization. See script editor."
    )

if __name__ == "__main__":
    a_validation = ValidatorBase()
    a_validation.select()
    if a_validation.is_repair_available():
        a_validation.repair()
    else:
        print("No repair function")

    print(ValidatorLibrary.NodeSceneNamePrefix())
