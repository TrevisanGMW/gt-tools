"""
Base Node Validators
These might be used as a base for other validations to further simplify the inheritance of basic checks.

Import Line:
    import gt.core.validators.validator_node as core_data_val_node
"""

import gt.core.validator as core_val
import maya.cmds as cmds
import os


class ValidatorNodeSceneNamePrefix(core_val.ValidatorBase):
    """
    Generic validator that checks if nodes of a given type are prefixed
    with the scene file name.
    """

    def __init__(self, node_type="transform"):
        """
        Initializes the validator for a specific node type.

        Args:
            node_type (str): The default node type to check (e.g., 'mesh', 'joint').
        """
        self.node_type = node_type
        description = f"Checks that '{self.node_type}' nodes are prefixed with the scene file name."
        super().__init__(description=description)
        self.set_name(f"{self.node_type.capitalize()} Scene Name Prefix")
        self.invalid_nodes = []

    # ------------------------------------------------- Core ----------------------------------------------------
    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Checks node transforms against the scene name prefix convention.

        Args:
            scope (ValidatorScope, optional): The scope of the validation.
                Can be `SCENE` to check all nodes, or `SELECTION` to check only
                selected nodes. Defaults to `core_val.ValidatorScope.SCENE`.
            node_type (str, optional): The Maya node type to validate (e.g., 'transform').
                If not provided, it defaults to the `self.node_type` class attribute.
        """
        current_node_type = node_type or self.node_type
        prefix = self._get_scene_prefix()

        if not prefix:
            self.set_result(
                status=core_val.ValidatorStatus.WARNING,
                feedback="Please save the scene before running this check.",
            )
            return

        if scope == core_val.ValidatorScope.SELECTION and not cmds.ls(selection=True):
            self.set_result(
                status=core_val.ValidatorStatus.WARNING,
                feedback="Validation scope is 'Selection', but nothing is selected.",
            )
            return

        nodes_to_check = self._get_nodes_to_validate(scope, current_node_type)

        if not nodes_to_check:
            self.set_result(
                status=core_val.ValidatorStatus.PASS,
                feedback=f"No nodes of type '{current_node_type}' found to validate in the given scope.",
            )
            return

        self.invalid_nodes = [node for node in nodes_to_check if not node.split("|")[-1].startswith(prefix)]

        if not self.invalid_nodes:
            status = core_val.ValidatorStatus.PASS
            feedback = f"All checked '{current_node_type}' names are valid."
        else:
            status = core_val.ValidatorStatus.FAIL
            feedback = f"Found {len(self.invalid_nodes)} '{current_node_type}' object(s) with incorrect names."

        self.set_result(status=status, feedback=feedback)

    # ------------------------------------------------ Repair ---------------------------------------------------
    def repair(self):
        """Renames non-compliant nodes to use the scene name as a prefix."""
        prefix = self._get_scene_prefix()
        if not prefix or not self.invalid_nodes:
            self.validate(node_type=self.node_type)
            return

        for node in self.invalid_nodes:
            if cmds.objExists(node):
                base_name = node.split("|")[-1]
                new_name = f"{prefix}_{base_name}"

                cmds.rename(node, new_name)

    # ------------------------------------------------ Select ---------------------------------------------------
    def select(self):
        """Selects the transforms with incorrect names."""
        if self.invalid_nodes:
            cmds.select(self.invalid_nodes, replace=True)

    def is_select_available(self, **kwargs):
        """Overrides base check to use the internal list of invalid nodes."""
        return super().is_select_available(item_list=self.invalid_nodes)

    # ----------------------------------------------- Utilities -------------------------------------------------
    @staticmethod
    def _get_scene_prefix():
        """Derives a name prefix from the current Maya scene's filename.

        This internal helper method retrieves the full path of the current scene,
        extracts the filename without its extension, and returns it. This
        is used to establish a naming convention prefix.

        Returns:
            str or None: The scene name without the file extension. Returns None
                         if the scene has not yet been saved (is untitled).
        """
        scene_path = cmds.file(query=True, sceneName=True)
        if not scene_path:
            return None
        scene_name = os.path.splitext(os.path.basename(scene_path))[0]
        return scene_name

    @staticmethod
    def _get_nodes_to_validate(scope, node_type):
        """
        Retrieves a list of nodes to be validated based on scope and type.

        This internal helper method gathers a list of nodes for validation. It
        respects the specified scope (`SELECTION` or `SCENE`). If a shape node
        of the given `node_type` is found, its parent transform is added to the
        list instead. The final list is filtered to exclude Maya's default
        startup cameras and any locked nodes.

        Args:
            scope (core_val.ValidatorScope): The validation scope, determining
                whether to check the entire scene or just the current selection.
            node_type (str): The Maya node type to filter for (e.g., 'mesh', 'camera').

        Returns:
            list[str]: A list of unique, full dag paths for the transform nodes
                       that are eligible for validation.
        """
        if scope == core_val.ValidatorScope.SELECTION:
            selection = cmds.ls(selection=True, long=True) or []
            hierarchy = selection + (cmds.listRelatives(selection, allDescendents=True, fullPath=True) or [])
            target_nodes = cmds.ls(hierarchy, type=node_type, long=True)
        else:  # SCENE or TYPE scope
            target_nodes = cmds.ls(type=node_type, long=True)

        if not target_nodes:
            return []

        # Ensure we are validating the transform node, not the shape node.
        transforms_to_check = set()
        for node in target_nodes:
            if cmds.objectType(node, isAType="shape"):
                parent = cmds.listRelatives(node, parent=True, fullPath=True)
                if parent:
                    transforms_to_check.add(parent[0])
            elif cmds.objectType(node, isAType="transform"):
                transforms_to_check.add(node)

        # Remove Startup Cameras (in case checking cameras)
        all_camera_shapes = cmds.ls(type="camera", long=True) or []
        startup_camera_shapes = [cam for cam in all_camera_shapes if cmds.camera(cam, query=True, startupCamera=True)]
        camera_transforms_to_exclude = set(cmds.listRelatives(startup_camera_shapes, parent=True, fullPath=True) or [])

        valid_nodes = [
            node
            for node in transforms_to_check
            if node not in camera_transforms_to_exclude and not cmds.lockNode(node, query=True, lock=True)[0]
        ]

        return valid_nodes


class ValidatorNoUnknownNodes(core_val.ValidatorBase):
    """
    A validator class to identify and remove unknown nodes within the Maya scene.

    Unknown nodes are typically created when a scene is saved with plugins that
    are no longer loaded or available on the current system. These nodes can
    cause stability issues or bloat the scene file.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoUnknownNodes instance with a description
        focusing on plugin-related scene clutter.
        """
        description = "Checks for unknown nodes often caused by missing plugins."
        super().__init__(description=description)
        self.unknown_nodes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries the scene for all nodes of type 'unknown'.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it specifically
                targets 'unknown' nodes. Defaults to None.
        """
        self.unknown_nodes = cmds.ls(type="unknown") or []

        if not self.unknown_nodes:
            self.set_result(core_val.ValidatorStatus.PASS, "No unknown nodes found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.unknown_nodes)} unknown node(s).")

    def repair(self):
        """
        Deletes the identified unknown nodes and re-runs the validation
        to update the status.
        """
        if self.unknown_nodes:
            # Re-query to be safe
            nodes_to_delete = cmds.ls(type="unknown")
            if nodes_to_delete:
                cmds.delete(nodes_to_delete)
            self.validate()

    def select(self):
        """
        Selects the unknown nodes currently present in the Maya scene for
        manual inspection.
        """
        if self.unknown_nodes:
            cmds.select(self.unknown_nodes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if the selection functionality is active based on whether
        unknown nodes were discovered.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the base class method.

        Returns:
            bool: True if unknown nodes exist, False otherwise.
        """
        return super().is_select_available(item_list=self.unknown_nodes)


class ValidatorUniqueDAGNames(core_val.ValidatorBase):
    """
    A base validator class that identifies DAG nodes sharing the same short name.

    In Maya, nodes can have the same short name if they reside under different
    parents, but unique naming is often required for game engine compatibility
    and reliable scripting.
    """

    def __init__(self, description=None):
        """
        Initializes the ValidatorUniqueDAGNames instance.

        Args:
            description (str, optional): A custom description for the validator.
                Defaults to "Ensures all DAG nodes have unique short names."
        """
        if not description:
            description = "Ensures all DAG nodes have unique short names."
        super(ValidatorUniqueDAGNames, self).__init__(description=description)
        self.duplicates = []

    def get_nodes_to_validate(self):
        """
        Retrieves the list of long paths to validate.

        This method is intended to be overridden in subclasses to narrow the
        naming check to specific types (e.g., only transforms or only joints).

        Returns:
            list: A list of full DAG paths (long names).
        """
        return cmds.ls(dag=True, long=True)

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Analyzes the short names of all gathered nodes and flags those that
        appear more than once in the scene.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Specific node type to filter. Defaults to None.
        """
        # 1. Gather nodes based on the specific validator's criteria
        nodes_to_check = self.get_nodes_to_validate()

        name_counts = {}
        self.duplicates = []

        # 2. Process names
        for full_path in nodes_to_check:
            # We use the short name (last part of pipe) for comparison
            short_name = full_path.split("|")[-1]

            if short_name not in name_counts:
                name_counts[short_name] = []
            name_counts[short_name].append(full_path)

        # 3. Identify duplicates
        for name, paths in name_counts.items():
            if len(paths) > 1:
                self.duplicates.extend(paths)

        # 4. Set Result
        if not self.duplicates:
            self.set_result(core_val.ValidatorStatus.PASS, "All checked DAG names are unique.")
        else:
            msg = "Found {} nodes with duplicate names.".format(len(self.duplicates))
            self.set_result(core_val.ValidatorStatus.FAIL, msg)

    def select(self):
        """
        Selects all instances of nodes that share a non-unique short name.
        """
        if self.duplicates:
            cmds.select(self.duplicates, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if selection is possible based on identified duplicates.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the base class method.

        Returns:
            bool: True if duplicate names were found, False otherwise.
        """
        return super(ValidatorUniqueDAGNames, self).is_select_available(item_list=self.duplicates)


class ValidatorUniqueDAGNamesIgnoreShapes(ValidatorUniqueDAGNames):
    """
    A specialized validator that checks for duplicate short names among
    structural DAG nodes while explicitly ignoring shape nodes.

    This is useful for pipelines where transform names must be unique for
    export, but duplicate shape names (e.g., 'pCubeShape1') are tolerated.
    """

    def __init__(self):
        """
        Initializes the ValidatorUniqueDAGNamesIgnoreShapes instance with a
        description focusing on structural DAG nodes.
        """
        description = "Ensures non-shape DAG nodes (e.g. Transforms, Joints) have unique names."
        super(ValidatorUniqueDAGNamesIgnoreShapes, self).__init__(description=description)

    def get_nodes_to_validate(self):
        """
        Retrieves a list of all DAG nodes in the scene, excluding those identified
        as shape nodes.

        Uses set subtraction for optimized performance in scenes with high
        component counts.

        Returns:
            list: A list of full DAG paths for non-shape nodes.
        """
        # Get all DAG nodes
        all_dag = set(cmds.ls(dag=True, long=True))

        # Get all Shapes (this covers meshes, nurbsCurves, locators, etc.)
        all_shapes = set(cmds.ls(dag=True, long=True, type="shape"))

        # Subtract shapes from the total list
        nodes_to_validate = list(all_dag - all_shapes)

        return nodes_to_validate


class ValidatorUniqueDAGNamesLODAware(ValidatorUniqueDAGNames):
    """
    A specialized validator that enforces unique naming while respecting
    Maya's LOD (Level of Detail) group structures.

    This variation allows nodes to share the same short name if they are
    parented under different `lodGroup` transforms. This is essential for
    game engine pipelines where LOD levels (e.g., 'LOD_0') must be named
    identically across different meshes but reside in separate LOD hierarchies.
    """

    def __init__(self):
        """
        Initializes the ValidatorUniqueDAGNamesLODAware instance with a
        description detailing the LOD context rules.
        """
        description = (
            "Ensures DAG names are unique within their specific LOD Group. "
            "Duplicates are permitted if they belong to different lodGroups."
        )
        super(ValidatorUniqueDAGNamesLODAware, self).__init__(description=description)
        self.lod_transforms = set()

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Performs contextual validation by bucketing nodes with identical short
        names based on their parent `lodGroup` node.

        A failure is only triggered if multiple nodes with the same short name
        share the same LOD context (or lack thereof).

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Specific node type to filter. Defaults to None.
        """
        # 1. Gather nodes to check (Default: All DAG nodes)
        nodes_to_check = self.get_nodes_to_validate()

        # 2. Pre-cache LOD Group transforms for fast lookup
        lod_shapes = cmds.ls(type="lodGroup", long=True) or []
        self.lod_transforms = set()
        if lod_shapes:
            parents = cmds.listRelatives(lod_shapes, parent=True, fullPath=True) or []
            self.lod_transforms = set(parents)

        # 3. Group all nodes by their Short Name
        name_counts = {}
        self.duplicates = []

        for full_path in nodes_to_check:
            short_name = full_path.split("|")[-1]
            if short_name not in name_counts:
                name_counts[short_name] = []
            name_counts[short_name].append(full_path)

        # 4. Analyze duplicates based on Context
        for name, paths in name_counts.items():
            # If the name appears only once, it is automatically unique
            if len(paths) < 2:
                continue

            # Bucket by "LOD Context": { "LOD_Group_A": [path1], None: [path3] }
            context_map = {}

            for path in paths:
                # Find which LOD group (if any) this node belongs to
                context_node = self._get_lod_context(path)

                if context_node not in context_map:
                    context_map[context_node] = []
                context_map[context_node].append(path)

            # 5. Determine Failures
            # Failure occurs if any bucket in the context_map has more than 1 item.
            for context, context_paths in context_map.items():
                if len(context_paths) > 1:
                    self.duplicates.extend(context_paths)

        # 6. Set Result
        if not self.duplicates:
            self.set_result(core_val.ValidatorStatus.PASS, "All DAG names are unique within their LOD contexts.")
        else:
            msg = "Found {} nodes with duplicate names inside the same LOD Group.".format(len(self.duplicates))
            self.set_result(core_val.ValidatorStatus.FAIL, msg)

    def _get_lod_context(self, long_path):
        """
        Walks up the hierarchy of the given path to find the nearest ancestor
        that is a lodGroup transform.

        Args:
            long_path (str): The full DAG path of the node.

        Returns:
            str or None: The full path of the lodGroup ancestor, or None if not found.
        """
        if not self.lod_transforms:
            return None

        # Start with the parent of the current node
        current_path = long_path

        # Walk up the pipe structure
        # path: |Group|LODGroup|Child -> parent checks: |Group|LODGroup, then |Group
        while "|" in current_path:
            # Strip the last segment to get the parent
            current_path = current_path.rsplit("|", 1)[0]

            # If we hit the root (empty string in split logic) or just the initial pipe
            if not current_path:
                break

            if current_path in self.lod_transforms:
                return current_path

        return None


class ValidatorInvisibleTransforms(core_val.ValidatorBase):
    """
    A validator class to detect transform nodes that have their visibility
    attribute set to False.
    """

    def __init__(self):
        """
        Initializes the ValidatorInvisibleTransforms instance with a
        description for identifying hidden DAG nodes.
        """
        description = "Ensures all transforms are visible."
        super().__init__(description=description)
        self.hidden_nodes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Iterates through transforms in the given scope and checks the
        Boolean value of the 'visibility' attribute.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Specific node type to filter. Defaults to None.
        """
        transforms = self._get_transforms(scope)
        self.hidden_nodes = []

        for node in transforms:
            # Check visibility attribute
            is_vis = cmds.getAttr(f"{node}.visibility")

            if not is_vis:
                self.hidden_nodes.append(node)

        if not self.hidden_nodes:
            self.set_result(core_val.ValidatorStatus.PASS, "All transforms are visible.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.hidden_nodes)} hidden transform(s).")

    def select(self):
        """
        Selects the transform nodes currently flagged as hidden.
        """
        if self.hidden_nodes:
            cmds.select(self.hidden_nodes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if selection is available based on identified hidden nodes.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if hidden nodes exist, False otherwise.
        """
        return super().is_select_available(item_list=self.hidden_nodes)

    def repair(self):
        """
        Sets the 'visibility' attribute to True for all identified nodes.
        Includes error handling for locked attributes.
        """
        if self.hidden_nodes:
            for node in self.hidden_nodes:
                try:
                    cmds.setAttr(f"{node}.visibility", 1)
                except Exception:
                    pass  # handle locked attributes
            self.validate()


class ValidatorPivotOrigin(core_val.ValidatorBase):
    """
    A validator class to ensure that object pivots are centered at the
    world origin (0, 0, 0).
    """

    def __init__(self):
        """
        Initializes the ValidatorPivotOrigin instance.
        """
        description = "Ensures the pivot is at the world origin."
        super().__init__(description=description)
        self.off_pivot_nodes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries the world space rotate pivot for transforms and flags
        those that deviate from (0, 0, 0) beyond a float tolerance.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): Node type to filter. Defaults to None.
        """
        transforms = self._get_transforms(scope)
        self.off_pivot_nodes = []

        for trans in transforms:
            rp = cmds.xform(trans, query=True, worldSpace=True, rotatePivot=True)
            if any(abs(v) > 0.0001 for v in rp):
                self.off_pivot_nodes.append(trans)

        if not self.off_pivot_nodes:
            self.set_result(core_val.ValidatorStatus.PASS, "All pivots are at origin.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL, f"Found {len(self.off_pivot_nodes)} object(s) with offset pivots."
            )

    def repair(self):
        """
        Resets both the rotate and scale pivots to the world origin
        using the xform command.
        """
        if self.off_pivot_nodes:
            for node in self.off_pivot_nodes:
                cmds.xform(node, worldSpace=True, rotatePivot=(0, 0, 0), scalePivot=(0, 0, 0))
            self.validate()

    def select(self):
        """
        Selects the objects identified as having offset pivots.
        """
        if self.off_pivot_nodes:
            cmds.select(self.off_pivot_nodes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if selection functionality is available.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if offset pivots exist, False otherwise.
        """
        return super().is_select_available(item_list=self.off_pivot_nodes)


class ValidatorNoForeignScriptNodes(core_val.ValidatorBase):
    """
    A validator class to detect and manage script nodes within the scene.

    This validator identifies "foreign" script nodes that may contain malicious
    code or unnecessary overhead, while also monitoring default Maya configuration
    nodes to ensure they are using the expected MEL source type.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoForeignScriptNodes instance with descriptions
        for both foreign node detection and Python-based configuration warnings.
        """
        description = (
            "Ensures the scene contains no foreign script nodes. Warns if default config nodes are set to Python."
        )
        super().__init__(description=description)
        self.foreign_nodes = []
        self.python_config_nodes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Scans the scene for all script nodes and categorizes them as either
        foreign or default configuration nodes.

        Default nodes are checked for their 'sourceType' attribute to warn if
        they are utilizing Python (1) instead of MEL (0).

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it specifically
                targets 'script' nodes. Defaults to None.
        """
        # Define default nodes that are safe to ignore (usually)
        ignored_names = ["sceneConfigurationScriptNode", "uiConfigurationScriptNode"]

        all_nodes = cmds.ls(type="script") or []

        self.foreign_nodes = []
        self.python_config_nodes = []

        for node in all_nodes:
            if node not in ignored_names:
                # 1. Foreign Node -> Automatic Fail
                self.foreign_nodes.append(node)
            else:
                # 2. Ignored Node -> Check if Source Type is Python (1)
                # Source Type: 0 = MEL, 1 = Python
                try:
                    source_type = cmds.getAttr(f"{node}.sourceType")
                    if source_type == 1:
                        self.python_config_nodes.append(node)
                except (ValueError, RuntimeError):
                    pass

        # Determine Result Priority: FAIL > WARNING > PASS
        if self.foreign_nodes:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.foreign_nodes)} foreign script node(s).")
        elif self.python_config_nodes:
            self.set_result(
                core_val.ValidatorStatus.WARNING,
                f"Found {len(self.python_config_nodes)} default config node(s) set to Python (expected MEL).",
            )
        else:
            self.set_result(core_val.ValidatorStatus.PASS, "No foreign script nodes found.")

    def select(self):
        """
        Selects the offending script nodes in the Outliner or Node Editor.
        Prioritizes the selection of foreign nodes over Python configuration nodes.
        """
        nodes_to_select = self.foreign_nodes if self.foreign_nodes else self.python_config_nodes
        if nodes_to_select:
            cmds.select(nodes_to_select, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if the selection button in the UI should be active.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the base class method.

        Returns:
            bool: True if either foreign or incorrectly configured nodes are found.
        """
        has_items = bool(self.foreign_nodes or self.python_config_nodes)
        return super().is_select_available(item_list=self.foreign_nodes) or has_items

    def repair(self):
        """
        Deletes the foreign script nodes identified during validation.

        Note: This does not delete default configuration nodes to avoid
        corrupting Maya's UI or scene preferences.
        """
        if self.foreign_nodes:
            cmds.delete(self.foreign_nodes)
            self.validate()


class ValidatorNoImagePlanes(core_val.ValidatorBase):
    """
    Checks for the existence of image planes in the scene.

    This validator identifies `imagePlane` nodes, which are often used for
    reference during modeling or animation but should be removed before
    export or final delivery to keep the scene clean.
    """

    def __init__(self):
        """Initializes the validator with a description."""
        description = "Ensures no image planes exist in the scene."
        super().__init__(description=description)
        self.image_planes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Finds any image planes based on the provided scope.

        Args:
            scope (ValidatorScope, optional): The scope of the validation.
                If set to `SELECTION`, it checks selected objects and their
                descendants. If set to `SCENE` (default), it checks the
                entire scene.
            node_type (str, optional): The node type to validate. Defaults
                to None as this validator specifically targets 'imagePlane'.
        """
        self.image_planes = []

        if scope == core_val.ValidatorScope.SELECTION:
            selection = cmds.ls(selection=True, long=True)
            if selection:
                # Check descendants of selection
                self.image_planes = (
                    cmds.listRelatives(selection, allDescendents=True, type="imagePlane", fullPath=True) or []
                )
                # Also check if the selection itself is an imagePlane
                self.image_planes.extend(cmds.ls(selection, type="imagePlane", long=True))
        else:
            self.image_planes = cmds.ls(type="imagePlane", long=True) or []

        if not self.image_planes:
            self.set_result(core_val.ValidatorStatus.PASS, "No image planes found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.image_planes)} image plane(s).")

    def select(self):
        """Selects the identified image planes in the scene."""
        if self.image_planes:
            cmds.select(self.image_planes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if the selection action is available.

        Returns:
            bool: True if image planes were found and can be selected, False otherwise.
        """
        return super().is_select_available(item_list=self.image_planes)

    def repair(self):
        """
        Deletes all found image planes.

        After deletion, it re-runs the validation to update the status.
        """
        if self.image_planes:
            cmds.delete(self.image_planes)
            self.validate(scope=core_val.ValidatorScope.SCENE)


if __name__ == "__main__":
    # a_val_transform_scene_prefix = ValidatorNodeSceneNamePrefix()
    # a_val_transform_scene_prefix.validate(core_val.ValidatorScope.SCENE)
    #
    # print(" Initial Validation ".center(65, "#"))
    # print(a_val_transform_scene_prefix.get_status())
    # print(a_val_transform_scene_prefix.get_feedback())
    # print(a_val_transform_scene_prefix.invalid_nodes)
    #
    # print(" After Repair ".center(65, "#"))
    # a_val_transform_scene_prefix.repair()
    # print(a_val_transform_scene_prefix.get_status())
    # print(a_val_transform_scene_prefix.get_feedback())
    # print(a_val_transform_scene_prefix.invalid_nodes)

    a_val_test = ValidatorNoImagePlanes()
    a_val_test.validate(scope=core_val.ValidatorScope.SELECTION)
    # a_val_test.repair()
    a_val_test.select()

    print(" Validation ".center(65, "#"))
    print(a_val_test.get_status())
    print(a_val_test.get_feedback())
