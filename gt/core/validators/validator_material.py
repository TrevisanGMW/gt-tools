"""
Material Validators

Import Line:
    import gt.core.validators.validator_material as core_data_val_mat
"""

import gt.core.validator as core_val
import maya.cmds as cmds
import os


class ValidatorNoUnusedMaterials(core_val.ValidatorBase):
    """
    A validator class that identifies and manages shading networks and materials
    that are not currently assigned to any geometry or objects in the scene.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoUnusedMaterials instance with a description
        and an empty list to track unassigned shading engines.
        """
        description = "Ensures all materials are assigned to objects."
        super().__init__(description=description)
        self.unused_mats = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Scans the scene for shading engines and checks for set membership.
        Shading engines without members (excluding defaults) are flagged as unused.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it specifically
                targets shadingEngine nodes. Defaults to None.
        """
        # List all shading engines
        shading_engines = cmds.ls(type="shadingEngine") or []
        self.unused_mats = []

        defaults = ["initialShadingGroup", "initialParticleSE"]

        for se in shading_engines:
            if se in defaults:
                continue

            # Check set members
            members = cmds.sets(se, query=True)
            if not members:
                self.unused_mats.append(se)

        if not self.unused_mats:
            self.set_result(core_val.ValidatorStatus.PASS, "No unused materials found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.unused_mats)} unused shading engine(s).")

    def repair(self):
        """
        Deletes the shading engines identified as unused and re-runs
        the validation to update the status.
        """
        if self.unused_mats:
            cmds.delete(self.unused_mats)
            self.validate()


class ValidatorBrokenTexturePaths(core_val.ValidatorBase):
    """
    A validator class that identifies Maya file nodes pointing to non-existent
    files or paths on disk.
    """

    def __init__(self):
        """
        Initializes the ValidatorBrokenTexturePaths instance with a description
        and an empty list to track nodes with invalid file paths.
        """
        description = "Ensures all file texture paths exist on disk."
        super().__init__(description=description)
        self.broken_nodes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Iterates through all 'file' nodes in the scene and checks the
        'fileTextureName' attribute against the local file system.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it specifically
                targets file nodes. Defaults to None.
        """
        file_nodes = cmds.ls(type="file") or []
        self.broken_nodes = []

        for node in file_nodes:
            path = cmds.getAttr(f"{node}.fileTextureName")
            # If path is empty, it's technically broken or just unused
            if not path or not os.path.exists(path):
                self.broken_nodes.append(node)

        if not self.broken_nodes:
            self.set_result(core_val.ValidatorStatus.PASS, "All texture paths are valid.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL, f"Found {len(self.broken_nodes)} file node(s) with missing textures."
            )

    def select(self):
        """
        Selects the file nodes in the Maya scene that were identified
        as having broken or missing texture paths.
        """
        if self.broken_nodes:
            cmds.select(self.broken_nodes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if the selection functionality is active based on whether
        broken file nodes were discovered.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the base class method.

        Returns:
            bool: True if there are nodes available to select, False otherwise.
        """
        return super().is_select_available(item_list=self.broken_nodes)


class ValidatorNoLambert1MeshAssignment(core_val.ValidatorBase):
    """
    A validator class to identify meshes assigned to the default 'lambert1'
    shading material via the 'initialShadingGroup'.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoLambert1MeshAssignment instance with a
        description and an empty list to track objects with default assignments.
        """
        description = "Ensures no objects are assigned to 'lambert1'."
        super().__init__(description=description)
        self.default_assigned = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Validates if meshes are assigned to the initialShadingGroup (lambert1).
        Supports both full scene and active selection scopes.

        Args:
            scope (core_val.ValidatorScope, optional): The range of the check
                (e.g., SCENE or SELECTION). Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Specific node type to filter. Defaults to None.
        """
        # initialShadingGroup is the set engine for lambert1
        shading_group_members = cmds.sets("initialShadingGroup", query=True) or []

        # Get long names of all objects assigned to the default shader
        all_default_objects = cmds.ls(shading_group_members, objectsOnly=True, long=True) or []

        if scope == core_val.ValidatorScope.SELECTION:
            # Get current selection (long names for accurate comparison)
            current_selection = cmds.ls(selection=True, long=True)

            # Intersection: items in the shading group that are also in the selection
            selection_set = set(current_selection)
            self.default_assigned = [obj for obj in all_default_objects if obj in selection_set]
        else:
            # Default to Scene scope logic
            self.default_assigned = all_default_objects

        # Result handling
        if not self.default_assigned:
            status = core_val.ValidatorStatus.PASS
            message = "No objects assigned to lambert1."
        else:
            status = core_val.ValidatorStatus.FAIL
            message = f"Found {len(self.default_assigned)} object(s) assigned to lambert1."

        self.set_result(status, message)

    def select(self):
        """
        Selects the objects identified as being assigned to 'lambert1'
        in the Maya viewport.
        """
        if self.default_assigned:
            cmds.select(self.default_assigned, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if the selection functionality is active based on whether
        objects with default assignments were discovered.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the base class method.

        Returns:
            bool: True if there are objects to select, False otherwise.
        """
        return super().is_select_available(item_list=self.default_assigned)


class ValidatorMaterialNaming(core_val.ValidatorBase):
    """
    A validator class to ensure that all non-default materials in the scene
    follow the project's naming convention by starting with the 'M_' prefix.
    """

    def __init__(self):
        """
        Initializes the ValidatorMaterialNaming instance with a description
        of the naming requirement and an empty list for invalid materials.
        """
        description = "Ensures materials are prefixed with 'M_'."
        super().__init__(description=description)
        self.invalid_mats = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Scans the scene's shading engines to find associated surface shaders.
        Checks if the material nodes (excluding defaults) start with 'M_'.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator as it focuses
                specifically on shadingEngine connections. Defaults to None.
        """
        shading_engines = cmds.ls(type="shadingEngine") or []
        self.invalid_mats = []

        defaults = ["lambert1", "particleCloud1", "standardSurface1"]

        for se in shading_engines:
            # get material connected to surfaceShader
            mat_conn = cmds.listConnections(f"{se}.surfaceShader", source=True, destination=False)
            if mat_conn:
                mat = mat_conn[0]
                if mat in defaults:
                    continue

                if not mat.startswith("M_"):
                    self.invalid_mats.append(mat)

        if not self.invalid_mats:
            self.set_result(core_val.ValidatorStatus.PASS, "All materials follow M_ naming.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL, f"Found {len(self.invalid_mats)} material(s) without 'M_' prefix."
            )

    def select(self):
        """
        Selects the material nodes that do not conform to the 'M_'
        naming convention in the Maya scene.
        """
        if self.invalid_mats:
            cmds.select(self.invalid_mats, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if the selection functionality is active based on whether
        invalidly named materials were discovered.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the base class method.

        Returns:
            bool: True if there are materials to select, False otherwise.
        """
        return super().is_select_available(item_list=self.invalid_mats)


if __name__ == "__main__":
    a_val_test = ValidatorNoLambert1MeshAssignment()
    a_val_test.validate(scope=core_val.ValidatorScope.SELECTION)
    # a_val_test.repair()

    print(" Validation ".center(65, "#"))
    print(a_val_test.get_status())
    print(a_val_test.get_feedback())
