"""
Mesh (Polygons) Validators

Import Line:
    import gt.core.validators.validator_node as core_data_val_mesh

Ideas:
    Non-manifold geometry, lamina faces, zero-area faces
    History cleanup (e.g., delete construction history)
    Frozen transforms
    Correct vertex count / shape integrity
    Correct material assignments (not used?)
"""

import gt.core.validators.validator_node as data_val_node
import gt.core.validator as core_val
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ValidatorHistory(core_val.ValidatorBase):
    """
    A validator class to detect construction history on mesh nodes. It identifies
    non-deformer nodes in the dependency graph that should be baked or deleted
    before production export.
    """

    def __init__(self):
        """
        Initializes the ValidatorHistory instance with a description and an
        empty list to track meshes with uncleansed history.
        """
        description = "Ensures meshes have no construction history."
        super().__init__(description=description)
        self.dirty_meshes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries meshes within the given scope and inspects their history.

        It filters out allowed deformation nodes (skinClusters, blendShapes,
        tweaks) and identifies any remaining construction history nodes.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): The node type to filter, though the method
                internally targets "mesh" nodes. Defaults to None.
        """
        meshes = self._get_nodes(scope, node_type="mesh")
        self.dirty_meshes = []

        for mesh in meshes:
            # Check for history connections that are not strictly deformers (skinCluster, blendShape, etc)
            history = cmds.listHistory(mesh, pruneDagObjects=True) or []
            if len(history) > 0:
                # Basic check: if listHistory returns anything for a shape, it usually has history.
                # Refined: Check if history nodes are valid deformers.
                # For this implementation, we assume NO history allowed except skinClusters.
                allowed_types = ["skinCluster", "blendShape", "tweak"]
                bad_history = [
                    n for n in history if cmds.nodeType(n) not in allowed_types and not cmds.nodeType(n) == "mesh"
                ]
                if bad_history:
                    self.dirty_meshes.append(mesh)

        if not self.dirty_meshes:
            self.set_result(core_val.ValidatorStatus.PASS, "No construction history found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.dirty_meshes)} mesh(es) with history.")

    def select(self):
        """
        Selects the meshes in the Maya viewport that were identified as
        having non-deformer construction history.
        """
        if self.dirty_meshes:
            cmds.select(self.dirty_meshes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if the selection functionality is active based on whether
        dirty meshes were discovered.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the base class method.

        Returns:
            bool: True if there are meshes to select, False otherwise.
        """
        return super().is_select_available(item_list=self.dirty_meshes)

    def repair(self):
        """
        Bakes the partial history of identified meshes, effectively removing
        construction history while preserving deformation nodes. Re-runs
        validation after completion.
        """
        if self.dirty_meshes:
            cmds.bakePartialHistory(self.dirty_meshes, prePostDeformers=True)
            self.validate()


class ValidatorMeshSceneNamePrefix(data_val_node.ValidatorNodeSceneNamePrefix):
    """
    Specialized validator that checks if MESH transforms are prefixed
    with the scene file name.
    """

    def __init__(self):
        """Initializes the validator specifically for meshes."""
        # --- 1. Call the parent's __init__ method ---
        # This tells the generic class to configure itself to work only on 'mesh' nodes.
        super().__init__(node_type="mesh")

        # --- 2. (Optional) Override the description for more clarity ---
        self.set_description("Checks that mesh transforms are prefixed with the scene file name.")

    # ------------------------------------------------- Core ----------------------------------------------------
    def validate(self, scope=core_val.ValidatorScope.SCENE, **kwargs):
        """
        Validates mesh transforms by calling the parent's validation logic.

        This override ensures that this validator can only ever check for meshes,
        making it more robust and specialized.

        Args:
            scope (core_val.ValidationScope, optional): The scope of the validation.
        """
        # --- 3. Call the parent's validate method ---
        # We force the node_type to be 'mesh', ensuring this class's specific purpose.
        super().validate(scope=scope, node_type="mesh")


class ValidatorMeshFrozenTransforms(core_val.ValidatorBase):
    """
    A validator class to ensure that all mesh transform nodes have been frozen,
    meaning their translate and rotate values are zero, and scales are one.
    """

    def __init__(self):
        """
        Initializes the ValidatorMeshFrozenTransforms instance with a
        description defining the identity matrix requirement.
        """
        description = "Ensures mesh transforms are frozen: T(0,0,0), R(0,0,0), S(1,1,1)."
        super().__init__(description=description)
        self.invalid_transforms = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries transforms associated with meshes and checks if their values
        deviate from the identity matrix within a specific float tolerance.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): The node type to filter, though internal
                logic focuses on mesh-associated transforms. Defaults to None.
        """
        transforms = self._get_nodes(scope=scope, transforms=True, node_type="mesh")
        self.invalid_transforms = []
        for trans in transforms:
            t = cmds.getAttr(f"{trans}.translate")[0]
            r = cmds.getAttr(f"{trans}.rotate")[0]
            s = cmds.getAttr(f"{trans}.scale")[0]

            # Small tolerance for float precision
            is_valid = (
                all(abs(val) < 0.0001 for val in t)
                and all(abs(val) < 0.0001 for val in r)
                and all(abs(val - 1.0) < 0.0001 for val in s)
            )

            if not is_valid:
                self.invalid_transforms.append(trans)

        if not self.invalid_transforms:
            self.set_result(core_val.ValidatorStatus.PASS, "All mesh transforms are frozen.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL, f"Found {len(self.invalid_transforms)} unfrozen mesh transform(s)."
            )

    def select(self):
        """
        Selects the transform nodes identified as having unfrozen values
        in the Maya scene.
        """
        if self.invalid_transforms:
            cmds.select(self.invalid_transforms, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if selection is available based on whether invalid
        transforms were discovered.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if invalid transforms exist, False otherwise.
        """
        return super().is_select_available(item_list=self.invalid_transforms)

    def repair(self):
        """
        Forces the 'freeze transformation' operation on identified meshes.
        Re-runs validation to update the status.
        """
        if self.invalid_transforms:
            # Be careful freezing transforms on rigged items
            cmds.makeIdentity(self.invalid_transforms, apply=True, t=1, r=1, s=1, n=0, pn=1)
            self.validate()


class ValidatorNonManifold(core_val.ValidatorBase):
    """
    A validator class that detects non-manifold topology, such as edges
    shared by more than two faces or T-junctions.
    """

    def __init__(self):
        """
        Initializes the ValidatorNonManifold instance.
        """
        description = "Checks for non-manifold edges or vertices."
        super().__init__(description=description)
        self.invalid_meshes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries meshes and utilizes Maya's polyInfo command to detect
        non-manifold edges or vertices.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Filter for specific node types. Defaults to None.
        """
        meshes = self._get_nodes(scope, node_type="mesh")
        self.invalid_meshes = []

        for mesh in meshes:
            nm_edges = cmds.polyInfo(mesh, nonManifoldEdges=True)
            nm_verts = cmds.polyInfo(mesh, nonManifoldVertices=True)

            if nm_edges or nm_verts:
                self.invalid_meshes.append(mesh)

        if not self.invalid_meshes:
            self.set_result(core_val.ValidatorStatus.PASS, "No non-manifold geometry found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.invalid_meshes)} non-manifold mesh(es).")

    def select(self):
        """
        Selects the meshes identified as having non-manifold geometry.
        """
        if self.invalid_meshes:
            cmds.select(self.invalid_meshes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if selection functionality is enabled.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if invalid meshes were found, False otherwise.
        """
        return super().is_select_available(item_list=self.invalid_meshes)


class ValidatorNGons(core_val.ValidatorBase):
    """
    A validator class to detect polygons with more than four sides,
    which may cause issues in game engines or during subdivision.
    """

    def __init__(self):
        """
        Initializes the ValidatorNGons instance.
        """
        description = "Checks for N-Gons (faces with > 4 edges)."
        super().__init__(description=description)
        self.meshes_with_ngons = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Uses polySelectConstraint to efficiently identify faces with more than
        four sides across the specified scope.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): Node type to filter. Defaults to None.
        """
        meshes = self._get_nodes(scope, node_type="mesh")
        self.meshes_with_ngons = []

        cmds.select(clear=True)
        if meshes:
            cmds.select(meshes)
            cmds.polySelectConstraint(mode=3, type=8, size=3)  # size=3 means > 4 sides
            ngons = cmds.ls(selection=True)
            cmds.polySelectConstraint(disable=True)

            if ngons:
                self.meshes_with_ngons = list(set(cmds.ls(ngons, objectsOnly=True, long=True)))
                cmds.select(clear=True)

        if not self.meshes_with_ngons:
            self.set_result(core_val.ValidatorStatus.PASS, "No N-Gons found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found N-Gons in {len(self.meshes_with_ngons)} mesh(es).")

    def select(self):
        """
        Selects the specific face components that are identified as N-Gons.
        """
        if self.meshes_with_ngons:
            cmds.select(self.meshes_with_ngons)
            cmds.polySelectConstraint(mode=3, type=8, size=3)
            cmds.polySelectConstraint(disable=True)

    def is_select_available(self, **kwargs):
        """
        Determines if selection is available.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if N-Gons were found, False otherwise.
        """
        return super().is_select_available(item_list=self.meshes_with_ngons)


class ValidatorMeshCustomNaming(core_val.ValidatorBase):
    """
    A validator class to ensure meshes do not retain default Maya names like
    'pCube1' or 'polySurface1'.
    """

    def __init__(self):
        """
        Initializes the ValidatorMeshCustomNaming instance.
        """
        description = "Ensures meshes are not using default Maya names."
        super().__init__(description=description)
        self.bad_names = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Checks the short names of transforms against common default Maya
        primitive naming patterns.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): Node type to filter. Defaults to None.
        """
        transforms = self._get_transforms(scope)
        default_patterns = ["pSphere", "pCube", "pCylinder", "pPlane", "polySurface"]
        self.bad_names = []

        for trans in transforms:
            short_name = trans.split("|")[-1]
            if any(short_name.startswith(pat) for pat in default_patterns):
                self.bad_names.append(trans)

        if not self.bad_names:
            self.set_result(core_val.ValidatorStatus.PASS, "Mesh naming looks custom.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.bad_names)} object(s) with default names.")

    def select(self):
        """
        Selects the objects identified as using default names.
        """
        if self.bad_names:
            cmds.select(self.bad_names, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if selection is available.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if bad names exist, False otherwise.
        """
        return super().is_select_available(item_list=self.bad_names)


class ValidatorNoEmptyUVSets(core_val.ValidatorBase):
    """
    A validator class to ensure every mesh has at least one UV coordinate defined.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoEmptyUVSets instance.
        """
        description = "Ensures all meshes have valid UVs."
        super().__init__(description=description)
        self.empty_uv_meshes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Queries the UV count for each mesh in the scope using polyEvaluate.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): Node type to filter. Defaults to None.
        """
        meshes = self._get_nodes(scope=scope, node_type="mesh")
        self.empty_uv_meshes = []

        for mesh in meshes:
            num_uvs = cmds.polyEvaluate(mesh, uv=True)
            if num_uvs == 0:
                self.empty_uv_meshes.append(mesh)

        if not self.empty_uv_meshes:
            self.set_result(core_val.ValidatorStatus.PASS, "All meshes have UVs.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.empty_uv_meshes)} mesh(es) without UVs.")

    def select(self):
        """
        Selects meshes that are missing UV data.
        """
        if self.empty_uv_meshes:
            cmds.select(self.empty_uv_meshes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if selection is available.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if meshes without UVs exist, False otherwise.
        """
        return super().is_select_available(item_list=self.empty_uv_meshes)


class ValidatorSingleUVChannel(core_val.ValidatorBase):
    """
    A validator class to enforce a single UV set requirement per mesh.
    """

    def __init__(self):
        """
        Initializes the ValidatorSingleUVChannel instance.
        """
        description = "Ensures meshes have exactly one UV set."
        super().__init__(description=description)
        self.multi_uv_meshes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Checks the count of UV sets on each mesh.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): Node type to filter. Defaults to None.
        """
        meshes = self._get_nodes(scope=scope, node_type="mesh")
        self.multi_uv_meshes = []

        for mesh in meshes:
            uv_sets = cmds.polyUVSet(mesh, query=True, allUVSets=True) or []
            if len(uv_sets) > 1:
                self.multi_uv_meshes.append(mesh)

        if not self.multi_uv_meshes:
            self.set_result(core_val.ValidatorStatus.PASS, "All meshes have a single UV channel.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL, f"Found {len(self.multi_uv_meshes)} mesh(es) with multiple UV sets."
            )

    def select(self):
        """
        Selects meshes found to have multiple UV sets.
        """
        if self.multi_uv_meshes:
            cmds.select(self.multi_uv_meshes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if selection is available.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if meshes with multiple UV sets exist, False otherwise.
        """
        return super().is_select_available(item_list=self.multi_uv_meshes)


class ValidatorUVFaceCrossQuadrant(core_val.ValidatorBase):
    """
    A high-performance validator class that detects UV faces spanning across
    UDIM/Quadrant boundaries using the Maya API.
    """

    def __init__(self):
        """
        Initializes the ValidatorUVFaceCrossQuadrant instance.
        """
        description = "Ensures no single UV face spans across multiple UV quadrants (UDIMs)."
        super().__init__(description=description)
        self.crossing_meshes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Entry point for validation. Calls the internal API-based check.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): Node type to filter. Defaults to None.
        """
        meshes = self._get_nodes(scope=scope, node_type="mesh")
        self.crossing_meshes = []

        if not meshes:
            self.set_result(core_val.ValidatorStatus.PASS, "No meshes to check.")
            return

        self._validate_via_api(meshes)

        if not self.crossing_meshes:
            self.set_result(core_val.ValidatorStatus.PASS, "No faces cross UV quadrants.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL,
                f"Found {len(self.crossing_meshes)} mesh(es) with faces crossing UV quadrants.",
            )

    def _validate_via_api(self, meshes):
        """
        Uses OpenMaya to iterate over mesh UVs and faces to determine
        if any faces span across integer boundaries.

        Args:
            meshes (list): List of mesh long names to check.
        """
        import maya.api.OpenMaya as om
        import math

        for mesh_name in meshes:
            try:
                selection_list = om.MSelectionList()
                selection_list.add(mesh_name)
                dag_path = selection_list.getDagPath(0)
                mesh_fn = om.MFnMesh(dag_path)

                try:
                    u_arrays, v_arrays = mesh_fn.getUVs()
                except Exception:
                    continue

                if not u_arrays or not v_arrays:
                    continue

                counts, ids = mesh_fn.getAssignedUVs()
                current_id_index = 0
                mesh_has_crossing = False

                for i in range(len(counts)):
                    num_verts = counts[i]
                    if num_verts < 3:
                        current_id_index += num_verts
                        continue

                    face_u_values = []
                    face_v_values = []

                    for k in range(num_verts):
                        uv_id = ids[current_id_index + k]
                        face_u_values.append(u_arrays[uv_id])
                        face_v_values.append(v_arrays[uv_id])

                    current_id_index += num_verts

                    if not face_u_values:
                        continue

                    f_u_min = min(face_u_values)
                    f_u_max = max(face_u_values)
                    f_v_min = min(face_v_values)
                    f_v_max = max(face_v_values)

                    epsilon = 0.0001
                    floor_u_min = math.floor(f_u_min + epsilon)
                    floor_u_max = math.floor(f_u_max - epsilon)
                    floor_v_min = math.floor(f_v_min + epsilon)
                    floor_v_max = math.floor(f_v_max - epsilon)

                    if (floor_u_min != floor_u_max) or (floor_v_min != floor_v_max):
                        mesh_has_crossing = True
                        break

                if mesh_has_crossing:
                    self.crossing_meshes.append(mesh_name)

            except Exception as e:
                print(f"Error checking UVs on {mesh_name}: {e}")

    def select(self):
        """
        Selects meshes identified as having faces that cross UV quadrants.
        """
        if self.crossing_meshes:
            cmds.select(self.crossing_meshes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if selection is available.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if crossing meshes were found, False otherwise.
        """
        return super().is_select_available(item_list=self.crossing_meshes)


if __name__ == "__main__":
    # a_val_mesh_scene_prefix = ValidatorMeshSceneNamePrefix()
    # a_val_mesh_scene_prefix.validate(core_val.ValidatorScope.SCENE)
    #
    # print(" Initial Validation ".center(65, "#"))
    # print(a_val_mesh_scene_prefix.get_status())
    # print(a_val_mesh_scene_prefix.get_feedback())
    # print(a_val_mesh_scene_prefix.invalid_nodes)
    #
    # print(" After Repair ".center(65, "#"))
    # a_val_mesh_scene_prefix.repair()
    # print(a_val_mesh_scene_prefix.get_status())
    # print(a_val_mesh_scene_prefix.get_feedback())
    # print(a_val_mesh_scene_prefix.invalid_nodes)

    a_val_test = ValidatorUVFaceCrossQuadrant()
    a_val_test.validate()
    # a_val_test.repair()
    # a_val_test.select()

    print(" Validation ".center(65, "#"))
    print(a_val_test.get_status())
    print(a_val_test.get_feedback())
