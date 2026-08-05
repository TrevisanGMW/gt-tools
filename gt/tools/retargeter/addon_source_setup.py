"""
Animation Retargeter Addon: Source Offset
"""

import gt.tools.retargeter.retargeter_constants as tools_retarget_const
import gt.tools.retargeter.retargeter_framework as tools_rt_frm
import gt.core.namespace as core_nspace
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.core.color as core_color
import gt.core.attr as core_attr
import gt.core.node as core_node
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AddonSourceSetup(tools_rt_frm.TargetingAddon):
    __version__ = "0.0.1-alpha"
    allow_multiple = False

    def __init__(self):
        """
        Initiates a SourceManager
        """
        self._comparison_matrix_loc = "comparison_matrix_B_LOC"

        super().__init__(name="Source Setup")
        self.execution_order = self.Order.post_import
        self.transform_name = "offset"
        self.transform_data = {}
        self.transform_children = []  # If "imported_is_children" is active, this is ignored.
        self.imported_is_children = True  # If active, all transforms imported by the file are used as children
        self.deactivate_meshes_trans_inheritance = True  # If True, Meshes have their inherit transform deactivated.
        self.skeleton_pose = {}  # Pose for the source skeleton.
        self.comparison_loc_data = {}
        self.persp_focus_on_source = True  # If active, it will focus on the source elements after
        self.short_name_fallback = True  # If active, source elements will also rely on short names when long fails.

    # ------------------------------------------------- Setters -------------------------------------------------
    def set_transform_name(self, name):
        """
        Name of the transform used as offset. This is the parent of the "self.children" elements.

        Args:
            name (str): Name of the transform.
        """
        self.transform_name = name

    def set_transform_data(self, data_dict):
        """
        Sets transform data for the source offset transform
        Args:
            data_dict (dict): A dictionary where the key is the name of the attribute and the value is the value
                              to set the attribute to.
        """
        if not isinstance(data_dict, dict):
            logger.warning(
                'Transform data must be a dictionary matching the output of "core_attr.get_attrs_as_dict()".'
            )
            return
        self.transform_data = data_dict

    def set_comparison_loc_data(self, data_dict):
        """
        Sets transform data for the comparison locator transform
        Args:
            data_dict (dict): A dictionary where the key is the name of the attribute and the value is the value
                              to set the attribute to.
        """
        if not isinstance(data_dict, dict):
            logger.warning(
                'Transform data must be a dictionary matching the output of "core_attr.get_attrs_as_dict()".'
            )
            return
        self.comparison_loc_data = data_dict

    def set_children(self, children):
        """
        Sets the children variable. These elements get parented to the offset group.
        Args:
            children (list, str): A list of strings. These strings are paths to maya objects.
        """
        if children and isinstance(children, str):
            children = [children]
        if isinstance(children, list):
            self.transform_children = children
        else:
            raise ValueError("Children must be a list or a single string.")

    def set_children_from_selection(self):
        """
        Sets the "self.children" variable to carry selected objects.
        This function only stores the short name
        """
        selection_short = cmds.ls(selection=True)
        selection_abs = cmds.ls(selection=True, long=True, absoluteName=True)
        if not selection_short:
            logger.warning(f"Nothing selected. Unable to set offset children.")
            return
        filter_source_objs = []
        for obj in selection_short:
            if not obj.startswith(self._source_namespace):
                logger.warning(f'Object outside of source was skipped: "{obj}"')
                continue
            filter_source_objs.append(obj)
        if not filter_source_objs:
            logger.warning(f"No valid objects were selected. Unable to set offset children.")
            return
        self.transform_children = selection_abs

    # ------------------------------------------------- Getters -------------------------------------------------
    def get_transform_name(self):
        """
        Gets name for the transform data.
        Returns:
            str: A string describing the name of the transform used as offset.
        """
        return self.transform_name

    def get_transform_data(self):
        """
        Gets the transform data for the source transform.
        Returns:
            dict: A dictionary with the attributes for the source offset transform.
                  The keys are the attributes and the values are the values to set it.
        """
        return self.transform_data

    def get_children(self):
        """
        Get the children elements to be parented to the source offset transform.
        Returns:
            list: The children (strings) with the names/paths of the objects to be parented to the source offset.
        """
        return self.transform_children

    # -------------------------------------------------- Misc ---------------------------------------------------
    @staticmethod
    def get_root_transforms_and_joints(objects):
        """
        Retrieves all root transforms and joints from a provided list of objects.

        A root transform or joint is defined as an object that does not have a parent.

        Args:
            objects (list): A list of object names to check for root transforms and joints.

        Returns:
            list: A list of root transforms and joints found in the provided list.
        """
        # Initialize lists for root transforms and joints
        root_transforms = []
        root_joints = []

        for obj in objects:
            # Check if the object is a transform
            if cmds.objectType(obj) == "transform":
                # Check if it has a parent
                if not cmds.listRelatives(obj, parent=True):
                    root_transforms.append(obj)

            # Check if the object is a joint
            elif cmds.objectType(obj) == "joint":
                # Check if it has a parent
                if not cmds.listRelatives(obj, parent=True):
                    root_joints.append(obj)

        # Combine both lists
        root_objects = root_transforms + root_joints

        return root_objects

    @staticmethod
    def set_inherit_transform_to_zero_for_mesh_shapes(objects):
        """
        Filter transform objects that have mesh shapes as children and set their "Inherit Transform" attribute to zero.

        Args:
            objects (list): A list of object names to change the inherits transforms attribute to zero.
        """
        # Filter for transform objects
        transform_objects = [obj for obj in objects if cmds.objectType(obj) == "transform"]
        for transform in transform_objects:
            children = cmds.listRelatives(transform, children=True, shapes=True, fullPath=True) or []
            if any(cmds.objectType(child) == "mesh" for child in children):
                cmds.setAttr(f"{transform}.inheritsTransform", 0)

    def _find_object_in_scene(self, obj, namespace):
        """
        Attempts to find an object in the scene while taking in consideration the short name fallback variable.

        Args:
            obj (str): Name/path of the object.
            namespace (str): The namespace used for the source object.
        Returns:
            str or None: A path to the object in the scene. None when not found
        Note:
            The logic is matched by TargetingLink.get_health_score function.
        """

        # recorded namespace embedded in the long-absolute name and the separate
        # associated namespace could be different.
        # 1 - Find the name as it is
        if "|" in obj or ":" in obj:
            expected_path = obj  # obj has long-absolute name or namespace embedded.
        else:
            expected_path = f"{namespace}:{obj}"  # no namespace, apply the link one.
        if cmds.objExists(expected_path):
            return core_naming.get_long_name(expected_path)
        # 2 - Fallback
        if self.short_name_fallback:
            embedded_nspace = core_nspace.get_namespace(obj)
            if embedded_nspace != namespace:
                # get rid of existing wrong namespace in the name
                _short_name = core_naming.get_short_name(obj, remove_namespace=True)
                expected_path = f"{namespace}:{_short_name}"
            else:
                _short_name = core_naming.get_short_name(obj)
                expected_path = _short_name

            if cmds.objExists(expected_path):
                # long and absolute name
                return core_naming.get_long_name(expected_path, absolute=True)
        return None

    # ------------------------------------------------ Read/Write -----------------------------------------------
    def read_transform_offset_data(self):
        """
        Gets attributes and their values from the offset transform object.
        Attributes and their values are stored in the dictionary "self.transform_data".
        """
        offset_path = self.get_offset_group_from_scene()
        if not offset_path:
            logger.warning(f'Unable to read data from missing offset transform: "{offset_path}".')
            return
        self.transform_data = core_attr.get_attrs_as_dict(
            obj=offset_path, filter_locked=True, filter_connected=True, full_attr_path=False, get_user_defined=False
        )

    def read_comparison_loc_data(self):
        """
        Gets attributes and their values from the offset transform object.
        Attributes and their values are stored in the dictionary "self.transform_data".
        """
        comparison_loc = f"{self._source_namespace}:{self._comparison_matrix_loc}"
        if not comparison_loc or not cmds.objExists(comparison_loc):
            logger.warning(f'Unable to read data from missing comparison locator: "{comparison_loc}".')
            return
        self.comparison_loc_data = core_attr.get_attrs_as_dict(
            obj=comparison_loc, filter_locked=True, filter_connected=True, full_attr_path=False, get_user_defined=False
        )

    def read_source_skeleton_pose(self):
        """
        Reads and stores the current pose of the source skeleton joints.

        This method iterates through the cached list of imported source nodes and filters for joints.
        For each detected joint, it collects attribute data (excluding locked or connected attributes),
        and stores the resulting dictionary in `self.skeleton_pose`.
        """
        detected_joints = []
        for obj in self._cached_imported_source_nodes:
            if cmds.objExists(obj) and cmds.objectType(obj) == "joint":
                joint = cmds.ls(obj, long=True, absoluteName=False)[0]
                detected_joints.append(joint)
        pose_data = {}
        for jnt in detected_joints:
            attr_data = core_attr.get_attrs_as_dict(
                obj=jnt,
                filter_locked=True,
                filter_connected=False,
                full_attr_path=False,
                get_user_defined=False,
            )
            pose_data[str(jnt)] = attr_data
        self.skeleton_pose = pose_data

    def apply_offset_transform_data(self):
        """
        Applies transform data to the offset transform.
        """
        offset_grp = self.get_offset_group_from_scene()
        if not cmds.objExists(offset_grp):
            logger.warning(f'Unable to apply offset data to offset transform. Missing expected node: "{offset_grp}".')
            return
        for attr, value in self.transform_data.items():
            attr_path = f"{offset_grp}.{attr}"
            if not cmds.objExists(attr_path):
                logger.warning(f"Unable to set missing attribute: {attr_path}")
                continue
            cmds.setAttr(attr_path, value)

    def apply_comparison_loc_transform_data(self):
        """
        Applies transform data to the offset transform.
        """
        comparison_loc = f"{self._source_namespace}:{self._comparison_matrix_loc}"
        if not cmds.objExists(comparison_loc):
            logger.warning(f'Unable to apply data to comparison locator. Missing expected node: "{comparison_loc}".')
            return
        for attr, value in self.comparison_loc_data.items():
            attr_path = f"{comparison_loc}.{attr}"
            if not cmds.objExists(attr_path):
                logger.warning(f"Unable to set missing attribute: {attr_path}")
                continue
            cmds.setAttr(attr_path, value)

    def apply_source_skeleton_pose(self):
        """Applies source skeleton pose data"""
        for obj, attr_data in self.skeleton_pose.items():
            for attr, value in attr_data.items():
                _obj = self._find_object_in_scene(obj=obj, namespace=self._source_namespace)
                if _obj is None:
                    logger.warning(f"Unable to set pose for missing object: {obj}")
                    continue
                attr_path = f"{_obj}.{attr}"
                if not cmds.objExists(attr_path):
                    logger.warning(f"Unable to set missing pose attribute: {attr_path}")
                    continue
                try:
                    cmds.setAttr(attr_path, value)
                except Exception as e:
                    logger.warning(f"Failed to set source pose attribute. Issue: {e}")

    # -------------------------------------------------- Utils --------------------------------------------------
    def delete_source(self):
        """
        Deletes the imported source nodes and its offset transform
        """
        offset_grp = self.get_offset_group_from_scene()
        if offset_grp:
            cmds.delete(offset_grp)
        else:
            cmds.delete(self._cached_imported_source_nodes)

    def create_offset_group(self):
        """
        Creates an offset group (source objects go inside of it) and plugs a comparison system on its offset matrix.
        Returns:
            str: Path to the created transform offset group.
        """
        namespace = self._source_namespace
        offset_grp = core_hrchy.create_group(name=f"{namespace}:{self.transform_name}")

        # Add System Reference Attributes
        retarget_state_attr = tools_retarget_const.RetargeterConstants.ATTR_RETARGET_STATE
        core_attr.add_attr(obj_list=offset_grp, attributes=retarget_state_attr, attr_type="bool", is_keyable=False)
        # Add Comparison Attributes
        separator_attr = "comparisonSystem"
        goal_vis_attr = "bVisibility"
        goal_weight_attr = "bWeight"
        core_attr.add_separator_attr(target_object=offset_grp, attr_name=separator_attr)
        core_attr.add_attr(obj_list=offset_grp, attr_type="bool", attributes=goal_vis_attr)
        core_attr.add_attr(obj_list=offset_grp, attr_type="double", attributes=goal_weight_attr, minimum=0, maximum=1)
        cmds.addAttr(f"{offset_grp}.{separator_attr}", e=True, niceName="A & B Comparison")
        cmds.addAttr(f"{offset_grp}.{goal_vis_attr}", e=True, niceName="B Visibility")
        cmds.addAttr(f"{offset_grp}.{goal_weight_attr}", e=True, niceName="B Weight")

        # Create Comparison Locators and Setup
        locator_a = cmds.spaceLocator(name=f"{namespace}:comparison_matrix_A_LOC")[0]
        locator_b = cmds.spaceLocator(name=f"{namespace}:comparison_matrix_B_LOC")[0]
        blend = core_node.create_node("blendMatrix", name=f"{namespace}:blend_comparison_A_B")
        cmds.setAttr(f"{locator_b}.inheritsTransform", 0)
        cmds.connectAttr(f"{locator_a}.matrix", f"{blend}.inputMatrix")
        cmds.connectAttr(f"{locator_b}.matrix", f"{blend}.target[0].targetMatrix")
        core_hrchy.parent(source_objects=[locator_a, locator_b], target_parent=offset_grp)
        cmds.connectAttr(f"{blend}.outputMatrix", f"{offset_grp}.offsetParentMatrix")
        cmds.connectAttr(f"{offset_grp}.{goal_vis_attr}", f"{locator_b}.v")
        cmds.connectAttr(f"{offset_grp}.{goal_weight_attr}", f"{blend}.envelope")
        cmds.setAttr(f"{locator_a}.v", 0)
        cmds.setAttr(f"{offset_grp}.{goal_weight_attr}", 0)
        cmds.setAttr(f"{locator_b}.localScaleX", 25)
        cmds.setAttr(f"{locator_b}.localScaleY", 25)
        cmds.setAttr(f"{locator_b}.localScaleZ", 25)
        core_color.set_color_outliner(obj_list=offset_grp, rgb_color=(1, 0, 0))
        core_color.set_color_viewport(obj_list=locator_b, rgb_color=(1, 0, 0))
        cmds.setAttr(f"{locator_a}.hiddenInOutliner", 1)
        cmds.setAttr(f"{locator_b}.hiddenInOutliner", 1)

        return offset_grp

    def get_offset_group_from_scene(self):
        """
        Returns the path to the offset group found in the scene. None if nothing is found.
        Returns:
            str or None: The path to the offset ground or None if not found.
        """
        offset_grp = f"{self._source_namespace}:{self.transform_name}"
        if offset_grp and cmds.objExists(offset_grp):
            return offset_grp

    def set_retargeted_status(self, state):
        """
        If already the offset group is found in the scene, the retargeted status is set to the provided argument.
        Args:
            state (bool): New retargeted status. True flags that it was retargeted, False means it's in edit mode.
        """
        offset_grp = self.get_offset_group_from_scene()
        # The source could have been removed after the retarget (delete_source option).
        if offset_grp:
            attr_path = f"{offset_grp}.{tools_retarget_const.RetargeterConstants.ATTR_RETARGET_STATE}"
            if not cmds.objExists(attr_path):
                logger.warning(f'Unable to set retargeted status. Missing offset group attribute : "{attr_path}".')
                return
            cmds.setAttr(attr_path, state)

    def get_retargeted_status(self):
        """
        Gets the status of the current scene elements. If in edit mode, it will be False, if already retargeted True.
        Checks if an offset transform is detected in the scene, if one is found, then it checks the value of
        "RetargeterConstants.REF_ATTR_SOURCE_OFFSET" to determine if it was retargeted or not.
        Returns:
            bool: True if it was retargeted, False otherwise.
        """
        offset_grp = self.get_offset_group_from_scene()
        attr_path = f"{offset_grp}.{tools_retarget_const.RetargeterConstants.ATTR_RETARGET_STATE}"
        if cmds.objExists(attr_path):
            return cmds.getAttr(attr_path)
        return False

    def clear_scene_data(self):
        """
        Clears transform offset data, comparison transform and source skeleton pose.
        """
        self.transform_data = {}
        self.comparison_loc_data = {}
        self.skeleton_pose = {}

    # ------------------------------------------------ Overrides ------------------------------------------------
    def read_scene_data(self):
        """
        Override of the parent class. Automatically called when the definition reads all scene data.
        Reads transform offset data, comparison transform and source skeleton pose.
        """
        self.read_transform_offset_data()
        self.read_comparison_loc_data()
        self.read_source_skeleton_pose()

    def apply_addon(self):
        """
        Creates group, parent children to group, and apply offset.
        """
        offset_grp = self.create_offset_group()

        # Using imported nodes are children
        if self.imported_is_children:
            _children = self.get_root_transforms_and_joints(self._cached_imported_source_nodes)
            core_hrchy.parent(source_objects=_children, target_parent=offset_grp)
        # Using manually set nodes as children
        else:
            ns_children = []
            for child in self.transform_children:
                _child = child
                if ":" not in child:
                    _child = f":{child}"
                ns_child = _child.replace(":", f"{self._source_namespace}:")
                ns_children.append(ns_child)
            core_hrchy.parent(source_objects=ns_children, target_parent=offset_grp)

        # Set Meshes Inheritance State
        if self.deactivate_meshes_trans_inheritance:
            self.set_inherit_transform_to_zero_for_mesh_shapes(self._cached_imported_source_nodes)

        # Apply Stored Data
        self.apply_offset_transform_data()
        self.apply_comparison_loc_transform_data()
        self.apply_source_skeleton_pose()

        # Adjust Persp Camera
        if self.persp_focus_on_source:
            try:
                cmds.viewFit(offset_grp)
            except Exception as e:
                logger.debug(f"Unable to fit view. Issue: {e}")


if __name__ == "__main__":
    # cmds.file(new=True, force=True)
    a_source_setup_addon = AddonSourceSetup()
    # a_source_setup_addon.apply_addon()
    a_source_setup_addon._cached_imported_source_nodes = ["source:GM_LeftArm"]
    a_source_setup_addon.read_source_skeleton_pose()
    print(a_source_setup_addon.skeleton_pose)
    a_source_setup_addon._source_namespace = "source"  # Emulate project defined values
    a_source_setup_addon.set_retargeted_status(True)
    retargeted_status = a_source_setup_addon.get_retargeted_status()
    print(f"retargeted_status: {retargeted_status}")
