"""
Rig Validators

Import Line:
    import gt.core.validators.validator_rig as core_data_val_rig
"""

import gt.core.validator as core_val
import maya.cmds as cmds
import re
import os


class ValidatorBasicRigHierarchy(core_val.ValidatorBase):
    """
    A validator class to ensure the fundamental rig structure exists and follows
    the standard parenting hierarchy.
    """

    def __init__(self):
        """
        Initializes the ValidatorBasicRigHierarchy instance with required
        group names and hierarchy rules.
        """
        description = "Ensures 'rig', 'geometry', and 'skeleton' groups exist and respect hierarchy."
        super().__init__(description=description)
        self.missing_groups = []
        self.misparented_groups = []

        self._required_root = "rig"
        self._required_children = ["geometry", "skeleton"]

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Validates the existence of the core rig groups and ensures children are
        properly parented under the root 'rig' node.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): The node type to filter by. Defaults to None.
        """
        # Reset state
        self.missing_groups = []
        self.misparented_groups = []

        # 1. Existence Check (FAIL Condition)
        all_required = [self._required_root] + self._required_children

        for group_name in all_required:
            if not cmds.objExists(group_name):
                self.missing_groups.append(group_name)

        if self.missing_groups:
            message = f"Missing groups: {', '.join(self.missing_groups)}."
            self.set_result(core_val.ValidatorStatus.FAIL, message)
            return

        # 2. Hierarchy Check (WARNING Condition)
        for child_name in self._required_children:
            parents = cmds.listRelatives(child_name, parent=True) or []

            if self._required_root not in parents:
                self.misparented_groups.append(child_name)

        if self.misparented_groups:
            message = (
                f"Groups exist but are not parented to '{self._required_root}': "
                f"{', '.join(self.misparented_groups)}."
            )
            self.set_result(core_val.ValidatorStatus.WARNING, message)
        else:
            self.set_result(core_val.ValidatorStatus.PASS, "Rig hierarchy is complete and correct.")


class ValidatorFullRigHierarchy(ValidatorBasicRigHierarchy):
    """
    A comprehensive validator extending the basic rig hierarchy to include
    'controls' and 'setup' groups.
    """

    def __init__(self):
        """
        Initializes the ValidatorFullRigHierarchy with an expanded set of
        required child groups.
        """
        super().__init__()
        description = (
            "Ensures 'rig', 'geometry', 'skeleton', 'controls', and 'setup' " "groups exist and respect hierarchy."
        )
        self.set_description(description)
        self.missing_groups = []
        self.misparented_groups = []

        self._required_root = "rig"
        self._required_children = ["geometry", "skeleton", "controls", "setup"]


class ValidatorZeroedControls(core_val.ValidatorBase):
    """
    A validator class to verify that all animation controls have been reset
    to their default transform values.
    """

    def __init__(self):
        """
        Initializes the ValidatorZeroedControls with standard transform defaults
        and a tolerance for floating point comparisons.
        """
        description = "Ensures controls ending in _CTRL have default transform values."
        super().__init__(description=description)
        self.non_zeroed = []

        self.transform_defaults = {
            "translateX": 0.0,
            "translateY": 0.0,
            "translateZ": 0.0,
            "rotateX": 0.0,
            "rotateY": 0.0,
            "rotateZ": 0.0,
            "scaleX": 1.0,
            "scaleY": 1.0,
            "scaleZ": 1.0,
        }

    @staticmethod
    def _is_attribute_modifiable(full_attribute_path):
        """
        Determines if an attribute is currently modifiable based on its
        locked and visible status.

        Args:
            full_attribute_path (str): The 'object.attribute' string.

        Returns:
            bool: True if the attribute is not locked and is keyable or visible.
        """
        if cmds.getAttr(full_attribute_path, lock=True):
            return False

        is_keyable = cmds.getAttr(full_attribute_path, keyable=True)
        is_in_channel_box = cmds.getAttr(full_attribute_path, channelBox=True)

        if not is_keyable and not is_in_channel_box:
            return False

        return True

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Identifies '_CTRL' nodes with transform values deviating from the
        default, only checking modifiable attributes.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): The node type to filter. Defaults to None.
        """
        control_list = cmds.ls("*_CTRL", type="transform", long=True) or []
        self.non_zeroed = []
        tolerance = 0.001

        for control in control_list:
            is_dirty = False

            for attribute, default_value in self.transform_defaults.items():
                full_attribute_path = "{}.{}".format(control, attribute)

                if not self._is_attribute_modifiable(full_attribute_path):
                    continue

                current_value = cmds.getAttr(full_attribute_path)
                if abs(current_value - default_value) > tolerance:
                    is_dirty = True
                    break

            if is_dirty:
                self.non_zeroed.append(control)

        if not self.non_zeroed:
            self.set_result(core_val.ValidatorStatus.PASS, "All controls are zeroed.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.non_zeroed)} dirty control(s).")

    def repair(self):
        """
        Resets the non-zeroed attributes on identified controls back to
        their default values.
        """
        if self.non_zeroed:
            for control in self.non_zeroed:
                if not cmds.objExists(control):
                    continue

                for attribute, default_value in self.transform_defaults.items():
                    full_attribute_path = "{}.{}".format(control, attribute)

                    if self._is_attribute_modifiable(full_attribute_path):
                        try:
                            cmds.setAttr(full_attribute_path, default_value)
                        except RuntimeError:
                            pass

            self.validate()

    def select(self):
        """
        Selects the controls that currently have non-zeroed transform values.
        """
        if self.non_zeroed:
            existing_controls = [c for c in self.non_zeroed if cmds.objExists(c)]
            if existing_controls:
                cmds.select(existing_controls, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if selection functionality should be enabled.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if non-zeroed controls exist, False otherwise.
        """
        return super().is_select_available(item_list=self.non_zeroed)


class ValidatorMaxInfluences(core_val.ValidatorBase):
    """
    A validator class to check if skinClusters have their influence limits
    exceeded based on vertex weight distribution.
    """

    def __init__(self, max_limit=1, check_mesh_only=True):
        """
        Initializes the ValidatorMaxInfluences instance.

        Args:
            max_limit (int, optional): The max number of allowed influences.
                Defaults to 1.
            check_mesh_only (bool, optional): If True, ignores non-mesh geometry
                like NURBS. Defaults to True.
        """
        description = f"Ensures max influences per vertex does not exceed {max_limit}."
        super().__init__(description=description)
        self.max_limit = max_limit
        self.check_mesh_only = check_mesh_only
        self.failing_meshes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Performs a fast check on skinCluster attributes to see if influence
        limits are enforced.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): Node type to filter. Defaults to None.
        """
        skin_clusters = cmds.ls(type="skinCluster") or []
        self.failing_meshes = []

        for sc in skin_clusters:
            attached_geo = cmds.skinCluster(sc, query=True, geometry=True) or []

            if self.check_mesh_only:
                mesh_geo = cmds.ls(attached_geo, type="mesh")
                if not mesh_geo:
                    shapes = cmds.listRelatives(attached_geo, shapes=True, path=True) or []
                    mesh_geo = cmds.ls(shapes, type="mesh")
                    if not mesh_geo:
                        continue

            mmi = cmds.getAttr("{}.maintainMaxInfluences".format(sc))
            mi = cmds.getAttr("{}.maxInfluences".format(sc))

            if not mmi or mi > self.max_limit:
                self.failing_meshes.extend(attached_geo)

        self.failing_meshes = list(set(self.failing_meshes))

        if not self.failing_meshes:
            self.set_result(core_val.ValidatorStatus.PASS, "Skin settings enforce influence limits.")
        else:
            self.set_result(
                core_val.ValidatorStatus.WARNING,
                f"Found {len(self.failing_meshes)} objects where skin settings allow > {self.max_limit} influences.",
            )

    def repair(self):
        """
        Forces the skinCluster nodes to maintain the defined maximum influence
        limit and re-validates the scene.
        """
        if not self.failing_meshes:
            return

        for geo in self.failing_meshes:
            if not cmds.objExists(geo):
                continue

            sc_history = cmds.ls(cmds.listHistory(geo), type="skinCluster")
            if not sc_history:
                continue

            sc = sc_history[0]
            try:
                cmds.setAttr("{}.maintainMaxInfluences".format(sc), 1)
                cmds.setAttr("{}.maxInfluences".format(sc), self.max_limit)
            except RuntimeError:
                pass

        self.validate()

    def select(self):
        """
        Selects the transform nodes of geometry associated with failing skinClusters.
        """
        if not self.failing_meshes:
            return

        valid_objects = [obj for obj in self.failing_meshes if cmds.objExists(obj)]
        transforms_to_select = set()

        for obj in valid_objects:
            if cmds.ls(obj, type="shape"):
                parent = cmds.listRelatives(obj, parent=True, fullPath=True)
                if parent:
                    transforms_to_select.add(parent[0])
            else:
                transforms_to_select.add(obj)

        if transforms_to_select:
            cmds.select(list(transforms_to_select), replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if the selection functionality should be enabled.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if failing meshes are found, False otherwise.
        """
        return super().is_select_available(item_list=self.failing_meshes)


class ValidatorMaxInfluencesFour(ValidatorMaxInfluences):
    """
    A specialized validator that enforces a maximum of 4 influences per vertex.

    This limit is a common industry standard for mobile and standard game engine
    performance, ensuring that vertex skinning remains efficient for real-time
    rendering.
    """

    def __init__(self, max_limit=4, check_mesh_only=True):
        """
        Initializes the ValidatorMaxInfluencesFour instance.

        Args:
            max_limit (int, optional): The maximum number of influences allowed
                per vertex. Defaults to 4.
            check_mesh_only (bool, optional): If True, only validates skinClusters
                attached to Mesh geometry. Defaults to True.
        """
        super().__init__(max_limit=max_limit, check_mesh_only=check_mesh_only)


class ValidatorMaxInfluencesEight(ValidatorMaxInfluences):
    """
    A specialized validator that enforces a maximum of 8 influences per vertex.

    This is typically used for high-fidelity skeletal meshes targeting high-end
    platforms where more complex skin deformation is permissible.
    """

    def __init__(self, max_limit=8, check_mesh_only=True):
        """
        Initializes the ValidatorMaxInfluencesEight instance.

        Args:
            max_limit (int, optional): The maximum number of influences allowed
                per vertex. Defaults to 8.
            check_mesh_only (bool, optional): If True, only validates skinClusters
                attached to Mesh geometry. Defaults to True.
        """
        super().__init__(max_limit=max_limit, check_mesh_only=check_mesh_only)


class ValidatorUnusedInfluences(core_val.ValidatorBase):
    """
    A validator class to detect and remove influences in skinClusters that
    have zero weight across all vertices.
    """

    def __init__(self):
        """
        Initializes the ValidatorUnusedInfluences instance.
        """
        description = "Ensures skinClusters do not contain unused influences."
        super().__init__(description=description)
        self.dirty_clusters = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Compares weighted influences against the total influence list for
        every skinCluster in the scene.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): Node type to filter. Defaults to None.
        """
        skin_clusters = cmds.ls(type="skinCluster") or []
        self.dirty_clusters = []

        for sc in skin_clusters:
            weighted = cmds.skinCluster(sc, query=True, weightedInfluence=True) or []
            all_infs = cmds.skinCluster(sc, query=True, influence=True) or []

            if len(weighted) < len(all_infs):
                self.dirty_clusters.append(sc)

        if not self.dirty_clusters:
            self.set_result(core_val.ValidatorStatus.PASS, "No unused influences found.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL,
                f"Found {len(self.dirty_clusters)} skinClusters with unused influences.",
            )

    def repair(self):
        """
        Removes the zero-weighted influences from identified skinClusters.
        """
        if self.dirty_clusters:
            for sc in self.dirty_clusters:
                if not cmds.objExists(sc):
                    continue

                all_infs = cmds.skinCluster(sc, query=True, influence=True) or []
                weighted = set(cmds.skinCluster(sc, query=True, weightedInfluence=True) or [])
                unused = [inf for inf in all_infs if inf not in weighted]

                if unused:
                    try:
                        cmds.skinCluster(sc, edit=True, removeInfluence=unused)
                    except RuntimeError:
                        pass

            self.validate()

    def select(self):
        """
        Selects the geometry transforms associated with dirty skinClusters.
        """
        if not self.dirty_clusters:
            return

        transforms_to_select = set()

        for sc in self.dirty_clusters:
            if not cmds.objExists(sc):
                continue

            geo_list = cmds.skinCluster(sc, query=True, geometry=True) or []

            for geo in geo_list:
                if not cmds.objExists(geo):
                    continue

                if cmds.ls(geo, type="shape"):
                    parents = cmds.listRelatives(geo, parent=True, fullPath=True)
                    if parents:
                        transforms_to_select.add(parents[0])
                else:
                    transforms_to_select.add(geo)

        if transforms_to_select:
            cmds.select(list(transforms_to_select), replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if selection functionality is enabled.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if dirty clusters are found, False otherwise.
        """
        return super().is_select_available(item_list=self.dirty_clusters)


class ValidatorNoUnparentedObjects(core_val.ValidatorBase):
    """
    A validator class to ensure that all significant DAG objects (meshes, curves,
    joints) are parented within a hierarchy rather than living in the scene root.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoUnparentedObjects instance.
        """
        description = "Ensures meshes, curves, and joints are not parented to the world."
        super().__init__(description=description)
        self.root_objects = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Scans top-level assembly nodes and flags those that contain meshes,
        curves, or joints, excluding default cameras.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
            node_type (str, optional): Node type to filter. Defaults to None.
        """
        assemblies = cmds.ls(assemblies=True, long=True) or []
        self.root_objects = []

        target_types = ["mesh", "nurbsCurve", "nurbsSurface", "joint"]

        for transform in assemblies:
            children_shapes = cmds.listRelatives(transform, shapes=True, fullPath=True) or []
            is_target = False

            if cmds.nodeType(transform) == "joint":
                is_target = True

            if children_shapes:
                for shape in children_shapes:
                    if cmds.nodeType(shape) in target_types:
                        is_target = True
                        break

            if transform in ["|persp", "|top", "|front", "|side"]:
                is_target = False

            if is_target:
                self.root_objects.append(transform)

        if not self.root_objects:
            self.set_result(core_val.ValidatorStatus.PASS, "No unparented geometry/rig objects found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.root_objects)} object(s) in scene root.")

    def select(self):
        """
        Selects the objects currently parented to the world root.
        """
        if self.root_objects:
            cmds.select(self.root_objects, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if selection functionality is available.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if unparented objects exist, False otherwise.
        """
        return super().is_select_available(item_list=self.root_objects)


class ValidatorBoundRigMeshes(core_val.ValidatorBase):
    """
    A validator class to ensure that every mesh intended for deformation (inside
     a specific geometry group) is correctly connected to a skinCluster.
    """

    def __init__(self, group_name="geometry"):
        """
        Initializes the ValidatorBoundRigMeshes instance.

        Args:
            group_name (str, optional): The name of the transform group containing
                rig geometry. Defaults to "geometry".
        """
        description = f"Ensures all meshes inside the '{group_name}' group have a skinCluster connection."
        super().__init__(description=description)
        self.group_name = group_name
        self.unbound_meshes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Identifies meshes within the target group and verifies the presence of
        a skinCluster in their history. Intermediate objects are skipped.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator. Defaults to None.
        """
        if not cmds.objExists(self.group_name):
            self.set_result(
                core_val.ValidatorStatus.WARNING, f"Group '{self.group_name}' not found. Cannot validate bound meshes."
            )
            return

        # Get all meshes inside the group
        all_descendents = cmds.listRelatives(self.group_name, allDescendents=True, fullPath=True) or []
        mesh_shapes = cmds.ls(all_descendents, type="mesh", long=True)

        self.unbound_meshes = []

        for shape in mesh_shapes:
            # Check for skinCluster in the upstream history of the shape
            history = cmds.listHistory(shape) or []
            skin_clusters = cmds.ls(history, type="skinCluster")

            if not skin_clusters:
                # If no history found, check if it's an intermediate object
                if cmds.getAttr(f"{shape}.intermediateObject"):
                    continue

                # Store the transform parent for readability
                parent = cmds.listRelatives(shape, parent=True, fullPath=True)[0]
                if parent not in self.unbound_meshes:
                    self.unbound_meshes.append(parent)

        if not self.unbound_meshes:
            self.set_result(core_val.ValidatorStatus.PASS, "All rig meshes are bound.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL,
                f"Found {len(self.unbound_meshes)} unbound mesh(es) in '{self.group_name}'.",
            )

    def select(self):
        """
        Selects the transform nodes of meshes that are missing skinCluster connections.
        """
        if self.unbound_meshes:
            cmds.select(self.unbound_meshes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if selection is possible based on the presence of unbound meshes.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if unbound meshes are found, False otherwise.
        """
        return super().is_select_available(item_list=self.unbound_meshes)


class ValidatorNoEmptyGroups(core_val.ValidatorBase):
    """
    A validator class to find and remove empty transform nodes that contain
    no shapes and no child transforms.
    """

    def __init__(self, check_roots_only=False):
        """
        Initializes the ValidatorNoEmptyGroups instance.

        Args:
            check_roots_only (bool, optional): If True, only top-level DAG nodes
                are inspected. Defaults to False.
        """
        description = "Ensures there are no empty groups (nodes with no shapes and no children)."
        if check_roots_only:
            description += " (Checking Root Nodes Only)"
        super().__init__(description=description)
        self.check_roots_only = check_roots_only
        self.empty_groups = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Filters the scene for transform nodes and flags those without any
        children or shapes.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator. Defaults to None.
        """
        self.empty_groups = []

        if self.check_roots_only:
            nodes_to_check = cmds.ls(assemblies=True, long=True)
        else:
            nodes_to_check = cmds.ls(type="transform", long=True)

        for node in nodes_to_check:
            if cmds.nodeType(node) != "transform":
                continue

            shapes = cmds.listRelatives(node, shapes=True)
            if shapes:
                continue

            children = cmds.listRelatives(node, children=True)
            if not children:
                self.empty_groups.append(node)

        if not self.empty_groups:
            self.set_result(core_val.ValidatorStatus.PASS, "No empty groups found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(self.empty_groups)} empty group(s).")

    def select(self):
        """
        Selects the identified empty transform nodes in the Maya viewport.
        """
        if self.empty_groups:
            cmds.select(self.empty_groups, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if the selection interface should be enabled.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if empty groups exist, False otherwise.
        """
        return super().is_select_available(item_list=self.empty_groups)

    def repair(self):
        """
        Deletes the identified empty groups and re-validates the scene.
        """
        if self.empty_groups:
            cmds.delete(self.empty_groups)
            self.validate()


class ValidatorNoEmptyGroupsRoot(ValidatorNoEmptyGroups):
    """
    A specialized version of ValidatorNoEmptyGroups that only inspects
    top-level assembly nodes.
    """

    def __init__(self):
        """
        Initializes the validator with roots-only checking enabled.
        """
        super().__init__(check_roots_only=True)


class ValidatorSingleRootJoint(core_val.ValidatorBase):
    """
    A validator class to ensure a clean skeleton hierarchy by verifying
    there is exactly one joint at the root of the skeleton group.
    """

    def __init__(self, skeleton_group="skeleton"):
        """
        Initializes the ValidatorSingleRootJoint instance.

        Args:
            skeleton_group (str, optional): The group containing the skeleton
                hierarchy. Defaults to "skeleton".
        """
        description = f"Ensures '{skeleton_group}' group has exactly one child joint."
        super().__init__(description=description)
        self.skeleton_group = skeleton_group
        self.root_joints = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Checks the immediate children of the skeleton group for joint nodes.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator. Defaults to None.
        """
        if not cmds.objExists(self.skeleton_group):
            self.set_result(
                core_val.ValidatorStatus.WARNING, f"Group '{self.skeleton_group}' not found. Skipping check."
            )
            return

        children = cmds.listRelatives(self.skeleton_group, children=True, fullPath=True) or []
        self.root_joints = [child for child in children if cmds.nodeType(child) == "joint"]

        count = len(self.root_joints)

        if count == 1:
            self.set_result(core_val.ValidatorStatus.PASS, "Single root joint found.")
        elif count == 0:
            self.set_result(core_val.ValidatorStatus.FAIL, f"No joints found inside '{self.skeleton_group}'.")
        else:
            self.set_result(
                core_val.ValidatorStatus.FAIL, f"Found {count} root joints inside '{self.skeleton_group}' (Expected 1)."
            )

    def select(self):
        """
        Selects the root joints found within the skeleton group.
        """
        if self.root_joints:
            cmds.select(self.root_joints, replace=True)

    def is_select_available(self, **kwargs):
        """
        Enables the select button if any joints are present at the root level.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if root joints exist, False otherwise.
        """
        return super().is_select_available(item_list=self.root_joints)


class ValidatorJointNaming(core_val.ValidatorBase):
    """
    A validator class to enforce naming conventions (prefixes/suffixes)
    across the skeletal hierarchy, including specific exception handling.
    """

    def __init__(self, skeleton_group="skeleton", exceptions=None):
        """
        Initializes the ValidatorJointNaming instance.

        Args:
            skeleton_group (str, optional): The group to search for joints.
                Defaults to "skeleton".
            exceptions (list, optional): List of string prefixes that bypass
                standard suffix checks. Defaults to ["FACIAL_"].
        """
        description = "Ensures joints have valid prefixes (C_, L_, R_) and suffixes (_JNT), with exceptions."
        self.exceptions = exceptions or ["FACIAL_"]
        description += f"\n Current exceptions: {self.exceptions}"
        super().__init__(description=description)
        self.skeleton_group = skeleton_group
        self.bad_suffix_joints = []
        self.bad_prefix_joints = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Traverses the skeleton group and validates the short name of
        each joint against side prefixes and the JNT suffix.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation.
                Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Unused in this validator. Defaults to None.
        """
        if not cmds.objExists(self.skeleton_group):
            self.set_result(
                core_val.ValidatorStatus.WARNING, f"Group '{self.skeleton_group}' not found. Skipping naming check."
            )
            return

        all_joints = cmds.listRelatives(self.skeleton_group, allDescendents=True, type="joint", fullPath=True) or []

        self.bad_suffix_joints = []
        self.bad_prefix_joints = []
        valid_sides = ("C_", "L_", "R_")

        for jnt in all_joints:
            short_name = jnt.split("|")[-1]
            is_exception = False

            for exc in self.exceptions:
                if short_name.startswith(exc):
                    is_exception = True
                    remainder = short_name[len(exc) :]
                    if not remainder.startswith(valid_sides):
                        self.bad_prefix_joints.append(jnt)
                    break

            if not is_exception:
                if not short_name.endswith("_JNT"):
                    self.bad_suffix_joints.append(jnt)
                if not short_name.startswith(valid_sides):
                    self.bad_prefix_joints.append(jnt)

        if self.bad_suffix_joints:
            self.set_result(
                core_val.ValidatorStatus.FAIL, f"Found {len(self.bad_suffix_joints)} joint(s) missing '_JNT' suffix."
            )
        elif self.bad_prefix_joints:
            self.set_result(
                core_val.ValidatorStatus.WARNING,
                f"Found {len(self.bad_prefix_joints)} joint(s) with invalid side prefix.",
            )
        else:
            self.set_result(core_val.ValidatorStatus.PASS, "Joint naming convention is valid.")

    def select(self):
        """
        Selects offending joints, prioritizing those with missing suffixes.
        """
        if self.bad_suffix_joints:
            cmds.select(self.bad_suffix_joints, replace=True)
        elif self.bad_prefix_joints:
            cmds.select(self.bad_prefix_joints, replace=True)

    def is_select_available(self, **kwargs):
        """
        Checks if selection is available for any joints violating conventions.

        Args:
            **kwargs: Arbitrary keyword arguments.

        Returns:
            bool: True if naming violations are found, False otherwise.
        """
        return super().is_select_available(item_list=self.bad_suffix_joints or self.bad_prefix_joints)


if __name__ == "__main__":
    a_val_test = ValidatorSingleRootJoint()
    a_val_test.validate()
    # a_val_test.repair()
    a_val_test.select()

    print(" Validation ".center(65, "#"))
    print(a_val_test.get_status())
    print(a_val_test.get_feedback())
