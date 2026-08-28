"""
FBX Utilities

Properties
https://help.autodesk.com/view/MAYAUL/2023/ENU/?guid=GUID-18A2CDD7-3334-4FC1-A1B3-A308AD331BB2

Autodesk FBX SDK documentation:
https://help.autodesk.com/view/FBX/2020/ENU/?guid=FBX_Developer_Help_welcome_to_the_fbx_sdk_what_new_fbx_sdk_2020_html

# Configure FBX export settings
https://docs.unrealengine.com/en-us/Engine/Content/FBX/BestPractices
https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-animation-pipeline-in-unreal-engine
https://docs.unity3d.com/2017.4/Documentation/Manual/HOWTO-ArtAssetBestPracticeGuide.html
https://docs.unity3d.com/560/Documentation/Manual/HOWTO-exportFBX.html
#

"""
import maya.cmds as cmds
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

_fbx_common_module = None


def get_fbx_common_module():
    """Gets the optional Autodesk FBX SDK helper module.

    Returns:
        module: Imported FbxCommon module.

    Raises:
        ImportError: If FbxCommon cannot be imported.
    """
    global _fbx_common_module
    if _fbx_common_module:
        return _fbx_common_module

    try:
        import FbxCommon as imported_fbx_common
    except ImportError as exception:
        raise ImportError(
            'Optional FBX SDK helper "FbxCommon" is not available. '
            "Maya FBX import and export can still use FbxImporter and FbxExporter, "
            "SDK-level FBX file edits require the Autodesk FBX SDK."
        ) from exception

    _fbx_common_module = imported_fbx_common
    return _fbx_common_module


class FileDialogStyles:
    OS_NATIVE = 1
    MAYA_NATIVE = 2


def suppress_fbx_interface(func):
    """
    Decorator to suppress the FBX Preferences Interface when importing or exporting.

    Temporarily forces the Maya native file dialog to avoid UI interruptions
    during automated FBX operations. After the function executes, the previous
    dialog setting is restored or removed if it didn't previously exist.

    Args:
        func (function): The function to be wrapped.

    Returns:
        function: The wrapped function.
    """

    def wrapper(*args, **kwargs):
        """
        Wrapped function that temporarily modifies Maya's file dialog setting
        to prevent the FBX Preferences Interface from appearing.

        Args:
            *args: Positional arguments passed to the original function.
            **kwargs: Keyword arguments passed to the original function.

        Returns:
            Any: The result of the original function execution, if successful.

        Logs:
            - Errors during optionVar modification.
            - Restoration or removal of the FileDialogStyle setting after execution.
        """
        original_value = None
        option_var_name = "FileDialogStyle"
        result = None

        try:
            # Check if the optionVar exists and get its value, or set a default
            if cmds.optionVar(exists=option_var_name):
                original_value = cmds.optionVar(query=option_var_name)
            else:
                original_value = 2  # Default value 1 = OS native, 2 = Maya default
                cmds.optionVar(intValue=(option_var_name, original_value))

            # Modify the optionVar value
            cmds.optionVar(intValue=(option_var_name, FileDialogStyles.MAYA_NATIVE))  # Force Maya Native

            # Run input function
            result = func(*args, **kwargs)

        except Exception as e:
            logger.error(f"Couldn't set the FileDialogStyle to Maya default: {e}")

        finally:
            if original_value is not None:
                # Restore the original value of the FileDialogStyle
                cmds.optionVar(intValue=(option_var_name, original_value))
                logger.debug(f"Restored FileDialogStyle to its original value: {original_value}")
            else:
                # Cleanup in case original_value was never set
                cmds.optionVar(remove=option_var_name)
                logger.debug("FileDialogStyle optionVar was removed as it did not exist initially.")

            return result

    return wrapper


class FbxExporter:
    """
    Object FBXExporter.
    This object is supposed to be used inside a with statement.
    __enter__ and __exit__ are defined to reset and clean FBX preferences.
    """

    def __init__(self, selection=1, key_reducer=False):
        """
        Args:
            selection (bool): export selected objects or the entire scene
            key_reducer (bool): Filters FBX animation FCurves through a Constant Key Reducer.
                                This eliminates constant keys on a FCurve and helps to reduce
                                the size of resampled FCurves, especially Scale.
        """
        self.selection = selection
        self.key_reducer = key_reducer
        self._original_end = None
        self._original_start = None
        self._original_max = None
        self._original_min = None
        self._bake_start = None
        self._bake_end = None
        self._strip_namespace = True
        self._remove_parent_groups = False
        self._parent_groups = None
        self._remove_deformer_joints = False
        self._deformer_joints = None
        self._fbx_nodes_visilibity = True
        self._twist_value_map = {}
        self.read_timeline_settings()

    def __enter__(self, *args, **kwargs):
        """
        Enters the context, resetting FBX export preferences.

        Returns:
            FbxExporter: The instance itself for use within the with block.
        """
        self.reset_preferences()
        return self

    def __exit__(self, *args, **kwargs):
        """
        Exits the context, restoring FBX export preferences and clearing any cached takes.

        Args:
            *args: Unused positional arguments.
            **kwargs: Unused keyword arguments.
        """
        # Re-enable Deformers
        self.set_deformers_status(status=True)
        # Clear takes from FBX cache
        cmds.FBXExportSplitAnimationIntoTakes("-clear")
        try:
            cmds.FBXPopSettings()
        except Exception as e:
            logger.debug(f"Cannot pop FBX settings. Error: {e}")
        self.recover_timeline_settings()

    def read_timeline_settings(self):
        """Reads timeline ranges from the current scene."""
        self._original_min = cmds.playbackOptions(q=True, min=True)
        self._original_max = cmds.playbackOptions(q=True, max=True)
        self._original_start = cmds.playbackOptions(q=True, ast=True)
        self._original_end = cmds.playbackOptions(q=True, aet=True)

    def recover_timeline_settings(self):
        """Sets the timeline ranges back using the stored original values."""
        cmds.playbackOptions(
            e=True,
            min=self._original_min,
            ast=self._original_start,
            max=self._original_max,
            aet=self._original_end,
        )

    @staticmethod
    def reset_preferences():
        """Loads the FBX plug-in and resets its export preferences.

        The FBX commands are registered dynamically by the ``fbxmaya`` plug-in,
        so a Maya scene that does not import an FBX file has not necessarily
        loaded them yet.
        """
        if not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
            cmds.loadPlugin("fbxmaya", quiet=True)
        cmds.FBXResetExport()

    def get_deformer_node_from_joint(self, joint_name):
        """Gets the native twist deformer connected to a joint.

        Args:
            joint_name (str): joint name connected to the deformer.

        Returns:
            str or None: Deformer node or None.
        """
        import gt.core.rigging as core_rigging

        return core_rigging.get_twist_setup_from_target(joint_name)

    def set_deformers_status(self, status=True):
        """
        Set the status of the deformers in the scene, joints based on 'jointDrivers' attribute.

        Args:
            status (bool): True will activate the deformers, False will turn them off.

        Returns:
            list[str]: List of deformer nodes names.
        """
        deformer_nodes = []
        deformer_types = ["twist"]  # the types used in the jointDrivers attribute on the joints
        deformer_joint_attrs = cmds.ls("*.jointDrivers")
        if not deformer_joint_attrs:
            deformer_joint_attrs = cmds.ls("*:*.jointDrivers")
        if not deformer_joint_attrs:
            return []
        for deformer_d_attr in deformer_joint_attrs:
            deformer_drivers = cmds.getAttr(deformer_d_attr)
            if deformer_drivers:
                if any(d_type in deformer_drivers for d_type in deformer_types):
                    joint_name = deformer_d_attr.split(".")[0]
                    deformer_node = self.get_deformer_node_from_joint(joint_name)
                    if deformer_node:
                        deformer_nodes.append(deformer_node)

                        # Set Status - TWIST
                        if cmds.objExists(f"{deformer_node}.twist"):
                            if not status:
                                self._twist_value_map[deformer_node] = cmds.getAttr(f"{deformer_node}.twist")
                                cmds.setAttr(f"{deformer_node}.twist", 0)
                                logger.debug(f"Disabled deformer: {deformer_node}")
                            else:
                                if deformer_node in self._twist_value_map.keys():
                                    twist_value = self._twist_value_map[deformer_node]
                                    cmds.setAttr(f"{deformer_node}.twist", twist_value)
                                    logger.debug(f"Enabled Deformer {deformer_node} to {str(twist_value)}")
                                else:
                                    logger.debug(f"Skipped enabling deformer {deformer_node}, no values to set back")
        return deformer_nodes

    @staticmethod
    def get_rig_metadata_export_anim_bs():
        """
        Checks selected object(s) for rig metadata that specifies whether to export blendshapes.

        Returns:
            bool: True if blendshapes should be exported, False otherwise.
        """
        import gt.tools.auto_rigger.rig_constants as tools_rig_const

        selection = cmds.ls(sl=True)
        export_anim_bs = None
        rig_group = None
        if selection:
            for obj in selection:
                lookup_attr = tools_rig_const.RiggerConstants.REF_ATTR_SKELETON
                if cmds.objExists(f"{obj}.{lookup_attr}"):
                    connected_rig_node = cmds.listConnections(f"{obj}.{lookup_attr}", d=False, s=True)
                    if connected_rig_node:
                        rig_group = connected_rig_node[0]
                        break
        if rig_group:
            export_anim_bs_attr = tools_rig_const.RiggerConstants.ATTR_RIG_EXPORT_ANIM_BS
            if cmds.objExists(f"{rig_group}.{export_anim_bs_attr}"):
                export_anim_bs = cmds.getAttr(f"{rig_group}.{export_anim_bs_attr}")

        return export_anim_bs

    @staticmethod
    def get_skin_related_meshes():
        """Gets meshes influenced by the currently selected joints.

        Returns:
            list[str]: Full paths to meshes skinned to selected joints.
        """
        current_selection = cmds.ls(sl=True)
        related_meshes = []

        if current_selection:
            cmds.select(hi=True)
            expanded_selection = cmds.ls(sl=True)
            selected_joints = [obj for obj in expanded_selection if cmds.nodeType(obj) == "joint"]
            related_skin_clusters = []
            for jnt in selected_joints:
                skin = cmds.listConnections(jnt, type="skinCluster")
                if skin:
                    if skin[0] not in related_skin_clusters:
                        related_skin_clusters.append(skin[0])

            for skin in related_skin_clusters:
                shapes = cmds.skinCluster(skin, g=True, q=True)
                if shapes:
                    geos = cmds.listRelatives(shapes, parent=True, fullPath=True)
                    for geo in geos or []:
                        if geo not in related_meshes:
                            related_meshes.append(geo)

            cmds.select(cl=True)
            cmds.select(current_selection)

        return related_meshes

    @staticmethod
    def get_skin_related_meshes_with_blendshapes():
        """Gets selected-joint meshes that include blendshape deformers.

        Returns:
            list[str]: Full paths to skinned meshes with blendshapes.
        """
        meshes_with_blendshapes = []
        related_meshes = FbxExporter.get_skin_related_meshes()
        for geo in related_meshes:
            related_blendshapes = cmds.ls(*cmds.listHistory(geo) or [], type="blendShape")
            if related_blendshapes:
                meshes_with_blendshapes.append(geo)
        return meshes_with_blendshapes

    def set_preferences_animation(self, start_frame=None, end_frame=None):
        """
        Sets the correct FBX preferences to export animation asset.

        Args:
            start_frame (int): start frame to bake. If None, the start frame of the timeline will be used.
            end_frame (int): end frame to bake. If None, the end frame of the timeline will be used.
        """
        import gt.tools.auto_rigger.rig_constants as tools_rig_const

        self.reset_preferences()
        self.read_timeline_settings()

        # Check for related meshes with blendshapes
        export_anim_bs = self.get_rig_metadata_export_anim_bs()

        # post edits settings
        self._remove_parent_groups = True
        self._parent_groups = [
            tools_rig_const.RiggerConstants.GRP_RIG_NAME,
            tools_rig_const.RiggerConstants.GRP_SKELETON_NAME,
        ]
        if export_anim_bs:
            self._parent_groups.append(tools_rig_const.RiggerConstants.GRP_GEOMETRY_NAME)
        self._remove_deformer_joints = True

        # Disable Deformers
        self.set_deformers_status(status=False)

        # Take note of timeline settings, so we can keep scene as how the user sets it up after
        # and set the bake range for the complex animation preferences
        self._bake_start = self._original_start
        self._bake_end = self._original_end
        if start_frame:
            cmds.playbackOptions(e=True, min=start_frame, ast=start_frame)
            self._bake_start = start_frame
        if end_frame:
            cmds.playbackOptions(e=True, max=end_frame, aet=end_frame)
            self._bake_end = end_frame

        # bake complex animation is needed to export anim curves
        cmds.FBXProperty("Export|IncludeGrp|Animation", "-v", 1)  # it needs 0 or 1
        cmds.FBXExportBakeComplexAnimation("-v", True)
        cmds.FBXExportBakeComplexStart("-v", self._bake_start)
        cmds.FBXExportBakeComplexEnd("-v", self._bake_end)
        cmds.FBXExportBakeComplexStep("-v", True)

        # This command exports animation to transforms when activated
        # Otherwise it will export bone data along with animation
        cmds.FBXExportAnimationOnly("-v", False)
        cmds.FBXExportCameras("-v", False)
        cmds.FBXExportConstraints("-v", False)
        cmds.FBXExportLights("-v", False)
        cmds.FBXExportQuaternion("-v", "quaternion")
        # cmds.FBXExportAxisConversionMethod("none")
        cmds.FBXExportUpAxis("y")
        if self.key_reducer:
            cmds.FBXExportApplyConstantKeyReducer("-v", {True if self.key_reducer else False})

        # Do not export subdivision version
        cmds.FBXExportSmoothMesh("-v", False)
        # Needed for skins and blend shapes
        if export_anim_bs:
            cmds.FBXExportShapes("-v", True)
        else:
            cmds.FBXExportShapes("-v", False)
        cmds.FBXExportSkins("-v", False)
        cmds.FBXExportSkeletonDefinitions("-v", True)
        cmds.FBXExportEmbeddedTextures("-v", False)
        cmds.FBXExportInputConnections("-v", False)

        # preserve instances by sharing same mesh
        cmds.FBXExportInstances("-v", False)
        cmds.FBXExportUseSceneName("-v", False)

        # FBX Version
        # -- The Unreal Engine FBX import pipeline uses FBX 2020.2.
        # ref: https://dev.epicgames.com/documentation/en-us/unreal-engine/fbx-animation-pipeline-in-unreal-engine
        # -- FBX202000, FBX201900, FBX201800, FBX201600, FBX201400
        # -- FBX201300, FBX201200, FBX201100, FBX201000, FBX200900
        # -- FBX200611
        cmds.FBXExportFileVersion("-v", "FBX202000")

        cmds.FBXExportGenerateLog("-v", False)
        cmds.FBXExportInAscii("-v", False)

        # Clear take cache before next animation
        cmds.FBXExportSplitAnimationIntoTakes("-clear")

        # Select related meshes with blendshapes if necessary
        if export_anim_bs:
            meshes_with_bs = self.get_skin_related_meshes_with_blendshapes()
            cmds.select(meshes_with_bs, add=True)

    def set_preferences_animation_with_meshes(self, start_frame=None, end_frame=None):
        """Sets FBX preferences to export baked animation with deforming meshes.

        The skeletal mesh preset establishes the geometry, skin, and shape
        settings. Animation baking is then enabled so deforming meshes
        accompany the exported skeleton animation.

        Args:
            start_frame (int, optional): Start frame to bake. When omitted,
                the scene playback start frame is used.
            end_frame (int, optional): End frame to bake. When omitted, the
                scene playback end frame is used.
        """
        self.set_preferences_skeletal_mesh()

        self._bake_start = self._original_start
        self._bake_end = self._original_end
        if start_frame is not None:
            cmds.playbackOptions(e=True, min=start_frame, ast=start_frame)
            self._bake_start = start_frame
        if end_frame is not None:
            cmds.playbackOptions(e=True, max=end_frame, aet=end_frame)
            self._bake_end = end_frame

        cmds.FBXProperty("Export|IncludeGrp|Animation", "-v", 1)
        cmds.FBXExportBakeComplexAnimation("-v", True)
        cmds.FBXExportBakeComplexStart("-v", self._bake_start)
        cmds.FBXExportBakeComplexEnd("-v", self._bake_end)
        cmds.FBXExportBakeComplexStep("-v", True)
        cmds.FBXExportQuaternion("-v", "quaternion")
        if self.key_reducer:
            cmds.FBXExportApplyConstantKeyReducer("-v", True)
        cmds.FBXExportShapes("-v", True)
        cmds.FBXExportSkins("-v", True)
        if self.selection:
            related_meshes = self.get_skin_related_meshes()
            if related_meshes:
                cmds.select(related_meshes, add=True)

    def set_preferences_skeletal_mesh(self):
        """Sets the correct FBX preferences to export skeletal-mesh asset."""
        import gt.tools.auto_rigger.rig_constants as tools_rig_const

        self.reset_preferences()
        self.read_timeline_settings()

        # post edits settings
        self._remove_parent_groups = True
        self._parent_groups = [
            tools_rig_const.RiggerConstants.GRP_RIG_NAME,
            tools_rig_const.RiggerConstants.GRP_SKELETON_NAME,
            tools_rig_const.RiggerConstants.GRP_GEOMETRY_NAME,
        ]

        # FBX settings
        cmds.FBXProperty("Export|IncludeGrp|Animation", "-v", 1)  # it needs 0 or 1
        cmds.FBXExportBakeComplexAnimation("-v", False)
        cmds.FBXExportAnimationOnly("-v", False)
        cmds.FBXExportSmoothingGroups("-v", True)
        cmds.FBXExportSmoothMesh("-v", True)
        cmds.FBXExportTangents("-v", True)
        cmds.FBXExportInstances("-v", False)
        cmds.FBXExportTriangulate("-v", False)
        cmds.FBXExportShapes("-v", True)
        cmds.FBXExportSkins("-v", True)
        cmds.FBXExportSkeletonDefinitions("-v", True)
        cmds.FBXExportConstraints("-v", False)
        cmds.FBXExportEmbeddedTextures("-v", False)
        cmds.FBXExportInputConnections("-v", False)
        cmds.FBXExportCameras("-v", False)
        cmds.FBXExportLights("-v", False)
        cmds.FBXExportUpAxis("y")

        # FBX Version
        cmds.FBXExportFileVersion("-v", "FBX202000")

        cmds.FBXExportGenerateLog("-v", False)
        cmds.FBXExportInAscii("-v", False)

    def set_preferences_mesh(self):
        """Sets the correct FBX preferences to export mesh asset."""
        self.reset_preferences()
        self.read_timeline_settings()

        # FBX settings
        cmds.FBXProperty("Export|IncludeGrp|Animation", "-v", 0)  # it needs 0 or 1
        cmds.FBXExportBakeComplexAnimation("-v", False)
        cmds.FBXExportAnimationOnly("-v", False)
        cmds.FBXExportSmoothingGroups("-v", True)
        cmds.FBXExportSmoothMesh("-v", True)
        cmds.FBXExportTangents("-v", True)
        cmds.FBXExportInstances("-v", False)
        cmds.FBXExportTriangulate("-v", False)
        cmds.FBXExportShapes("-v", False)
        cmds.FBXExportSkins("-v", False)
        cmds.FBXExportSkeletonDefinitions("-v", False)
        cmds.FBXExportConstraints("-v", False)
        cmds.FBXExportEmbeddedTextures("-v", False)
        cmds.FBXExportInputConnections("-v", False)
        cmds.FBXExportCameras("-v", False)
        cmds.FBXExportLights("-v", False)
        cmds.FBXExportUpAxis("y")

        # FBX Version
        cmds.FBXExportFileVersion("-v", "FBX202000")

        cmds.FBXExportGenerateLog("-v", False)
        cmds.FBXExportInAscii("-v", False)

    @suppress_fbx_interface
    def export_file(self, path):
        """Exports scene contents in FBX.
        Uses original FBX SDK post-edits if available. If the SDK is missing
        and parent groups need to be removed, it falls back to a Bake-and-Undo method.

        Args:
            path: the path of the FBX resulting file.
        """
        # Check scene selection
        current_selection = cmds.ls(sl=True)
        if self.selection and current_selection is None:
            self.selection = False

        # 1. Determine if the optional FBX SDK is available
        sdk_available = True
        try:
            get_fbx_common_module()
        except ImportError:
            sdk_available = False

        # 2. Route the export logic
        if sdk_available or not self._remove_parent_groups or not self.selection:
            # --- ORIGINAL BEHAVIOR ---
            try:
                if self.selection:
                    cmds.FBXExport("-f", path, "-s")
                else:
                    cmds.FBXExport("-f", path)
                logger.info(f"FBX file exported: {str(path)}")

                # FBX file post edits
                self.fbx_post_edits(path=path)

            except Exception as e:
                logger.warning(f"FBX Export failed. Issue: {str(e)}")
        else:
            # --- FALLBACK BEHAVIOR ---
            logger.info("FBX SDK not found. Using Maya Undo-Chunk fallback to remove parent groups.")
            self._export_fallback_without_sdk(path, current_selection)

    def _export_fallback_without_sdk(self, path, current_selection):
        """Exports FBX through the hierarchy-preserving fallback workflow.

        Args:
            path (str): Destination FBX file path.
            current_selection (list): Selected Maya nodes to export.
        """
        """
        Fallback method that safely unparents top-level sub-groups to world
        (preserving internal hierarchy and scale), exports, and then undoes everything.
        Only runs bakeResults on joints driven by complex constraints.
        """
        if not current_selection:
            logger.warning("Nothing selected for export fallback.")
            return

        # 1. Store selection via UUID to survive hierarchy path changes
        sel_uuids = cmds.ls(current_selection, uuid=True)

        undo_was_enabled = cmds.undoInfo(q=True, state=True)
        if not undo_was_enabled:
            cmds.undoInfo(state=True)

        cmds.undoInfo(openChunk=True)

        try:
            # 2. Determine highest-level nodes to extract based on _parent_groups
            nodes_to_unparent = set()
            parent_groups_clean = [grp.split(":")[-1] for grp in self._parent_groups] if self._parent_groups else []

            for obj in cmds.ls(current_selection, long=True):
                parts = [p for p in obj.split("|") if p]
                current_path = ""

                for part in parts:
                    current_path += "|" + part
                    short_name = part.split(":")[-1]

                    if short_name not in parent_groups_clean:
                        nodes_to_unparent.add(current_path)
                        break

            # Helper method to check if a node is driven by constraints (not raw keyframes)
            def has_complex_drivers(node_path):
                """Checks whether a node has drivers requiring baked export handling.

                Args:
                    node_path (str): Maya node path to inspect.

                Returns:
                    bool: Whether complex drivers were found.
                """
                for attr in ["translate", "rotate", "scale"]:
                    for axis in ["x", "y", "z"]:
                        conns = cmds.listConnections(f"{node_path}.{attr}{axis.upper()}", s=True, d=False)
                        # If a connection exists and it is NOT an animCurve, it's complex
                        if conns and not cmds.nodeType(conns[0]).startswith('animCurve'):
                            return True
                return False

            # 3. Bake Animation ONLY on constrained nodes
            start = self._bake_start if self._bake_start is not None else self._original_start
            end = self._bake_end if self._bake_end is not None else self._original_end

            if start is not None and end is not None:
                bake_targets = set()
                for node in nodes_to_unparent:
                    if cmds.nodeType(node) == "joint" and has_complex_drivers(node):
                        bake_targets.add(node)

                    child_joints = cmds.listRelatives(node, ad=True, type="joint", fullPath=True) or []
                    for cj in child_joints:
                        if has_complex_drivers(cj):
                            bake_targets.add(cj)

                if bake_targets:
                    cmds.bakeResults(
                        list(bake_targets),
                        time=(start, end),
                        simulation=True,
                        sampleBy=1,
                        disableImplicitControl=True,
                        preserveOutsideKeys=True,
                        sparseAnimCurveBake=False,
                        removeBakedAttributeFromLayer=False,
                        bakeOnOverrideLayer=False,
                        minimizeRotation=True,
                        controlPoints=False,
                        shape=True,
                    )

            # 4. Decouple targets and inherit scale natively
            for node in nodes_to_unparent:
                if not cmds.objExists(node):
                    continue

                for attr in ["translate", "rotate", "scale"]:
                    for axis in ["x", "y", "z"]:
                        plug = f"{node}.{attr}{axis.upper()}"
                        try:
                            cmds.setAttr(plug, lock=False)
                            # Break driving connections EXCEPT standard animCurves
                            conns = cmds.listConnections(plug, s=True, d=False, plugs=True, c=True)
                            if conns:
                                src_node = conns[1].split('.')[0]
                                if not cmds.nodeType(src_node).startswith('animCurve'):
                                    cmds.disconnectAttr(conns[1], conns[0])
                        except Exception:
                            pass

                # Unparent to world (absolute=True computes & bakes world space natively into pure animCurves)
                if cmds.listRelatives(node, parent=True):
                    cmds.parent(node, world=True, absolute=True)

            # 5. Reselect via UUIDs and Export
            updated_sel = cmds.ls(sel_uuids, long=True)
            if updated_sel:
                cmds.select(updated_sel, replace=True)
                cmds.FBXExport("-f", path, "-s")
                logger.info(f"FBX fallback exported cleanly without parent groups: {path}")
            else:
                logger.error("Could not recover selection from UUIDs. Export aborted.")

        except Exception as e:
            logger.error(f"FBX Fallback Export failed: {e}")

        finally:
            # 6. Close chunk and UNDO to restore the complex rig completely
            cmds.undoInfo(closeChunk=True)
            cmds.undo()

            if current_selection:
                cmds.select(current_selection, replace=True)

    def fbx_post_edits(self, path):
        """
        Applies post-export cleanup and editing operations to the FBX file.

        This includes removing namespaces, parent groups, and deformer joints, and
        setting visibility flags inside the FBX.

        Args:
            path (str): Path to the FBX file to be edited.
        """
        edits = [self._strip_namespace, self._remove_parent_groups, self._fbx_nodes_visilibity]

        if any(edits):
            try:
                fbx_obj = FbxScene(path=path)
                with fbx_obj as fbx_file:
                    if self._strip_namespace:
                        fbx_file.remove_namespace()
                    if self._remove_parent_groups:
                        fbx_file.remove_nodes_by_names(name_list=self._parent_groups)
                    if self._fbx_nodes_visilibity:
                        fbx_file.set_nodes_visibility(self._fbx_nodes_visilibity)

                    fbx_file.save(path=path)
            except ImportError as exception:
                logger.warning(f"Skipped optional FBX SDK post edits. Issue: {exception}")


class FBXImportMode:
    """
    FBX import modes
    """

    Add = "Add"
    Merge = "Merge"
    ExMerge = "Exmerge"


class FbxImporter:
    """
    Object FBXImporter.
    This object is supposed to be used inside a with statement.
    __enter__ and __exit__ are defined to reset and clean FBX preferences.

    Note: by default the reset base settings are fine to import content without animation.
          set_preferences_animation is specifically needed for animation. Something like
          set_preferences_meshes has to be developed if needed.
    """

    def __init__(self):
        """
        Ignore Init
        """
        pass

    def __enter__(self, *args, **kwargs):
        """
        Enters the context, resetting FBX export preferences.

        Returns:
            FbxExporter: The instance itself for use within the with block.
        """
        self.reset_preferences()
        return self

    def __exit__(self, *args, **kwargs):
        """
        Exits the context, restoring FBX export preferences and clearing any cached takes.

        Args:
            *args: Unused positional arguments.
            **kwargs: Unused keyword arguments.
        """
        try:
            cmds.FBXPopSettings()
        except Exception as e:
            logger.debug(f"Cannot pop FBX settings. Error: {e}")

    @staticmethod
    def reset_preferences():
        """Resets any user preferences so we start clean."""
        cmds.FBXResetImport()

    @staticmethod
    def set_preferences_animation():
        """
        Sets the correct FBX preferences to import animation fbx file.
        """
        cmds.FBXImportSetTake("-ti", -1)  # the plug-in retrieves the last take in the take array.
        cmds.FBXImportFillTimeline("-v", True)
        cmds.FBXImportSetMayaFrameRate("-v", True)
        cmds.FBXImportMergeAnimationLayers("-v", True)
        cmds.FBXImportCameras("-v", False)
        cmds.FBXImportLights("-v", False)
        cmds.FBXImportConstraints("-v", False)
        cmds.FBXImportSetLockedAttribute("-v", False)

    @suppress_fbx_interface
    def import_file(self, path, namespace=None):
        """
        Imports Fbx file contents into Maya.

        Args:
            path (str): the path of the FBX file to import.
            namespace (str): the namespace to apply to the imported contents.
        Returns:
            list: imported nodes.
        """
        if not os.path.isfile(path):
            logger.warning(f"The given file path is missing: {path}")
            return
        if not path.lower().endswith("fbx"):
            logger.warning(f"The given file path is not pointing to an fbx: {path}")
            return

        if not namespace:
            cmds.FBXImportMode("-v", FBXImportMode.Merge)
            imported_nodes = cmds.file(
                path,
                i=True,
                type="FBX",
                ignoreVersion=True,
                renameAll=True,
                preserveReferences=True,
                importTimeRange="override",
                importFrameRate=True,
                returnNewNodes=True,
            )
        else:
            cmds.FBXImportMode("-v", FBXImportMode.Add)
            imported_nodes = cmds.file(
                path,
                i=True,
                type="FBX",
                ignoreVersion=True,
                renameAll=True,
                mergeNamespacesOnClash=False,
                namespace=namespace,
                preserveReferences=True,
                importTimeRange="override",
                importFrameRate=True,
                returnNewNodes=True,
            )

        return imported_nodes


class FbxScene:
    """
    Helper FBX class to manage the content within an FBX file. It uses the FBX SDK.
    __enter__ and __exit__ are defined to load and close correctly the FBX file.

    Autodesk FBX SDK Python documentation:
    https://help.autodesk.com/view/FBX/2020/ENU/?guid=FBX_Developer_Help_scripting_with_python_fbx_html
    """

    def __init__(self, path):
        """
        Init Object

        Args:
            path (string): fbx file path
        """
        self.path = path
        self.scene = None
        self.sdk_manager = None
        self.fbx_common = None
        self.scene_nodes = None
        self.root_node = None

    def __enter__(self, *args, **kwargs):
        """
        Loads the fbx file and its content.
        """
        self.fbx_common = get_fbx_common_module()
        self.sdk_manager, self.scene = self.fbx_common.InitializeSdkObjects()
        self.fbx_common.LoadScene(self.sdk_manager, self.scene, self.path)
        self.root_node = self.scene.GetRootNode()
        self.scene_nodes = self.get_scene_nodes()
        return self

    def __exit__(self, *args, **kwargs):
        """
        Closes the FBX scene safely.
        """
        # destroy objects created by the sdk
        if self.sdk_manager:
            self.sdk_manager.Destroy()

    def _get_scene_nodes_recursive(self, node):
        """
        Recursive method to get all scene nodes.

        Args:
            node (fbx node): fbx node object from the loaded fbx file
        """
        self.scene_nodes.append(node)
        for i in range(node.GetChildCount()):
            self._get_scene_nodes_recursive(node.GetChild(i))

    def get_scene_nodes(self):
        """
        Gets all the nodes in the fbx loaded file.
        """
        self.scene_nodes = []
        for i in range(self.root_node.GetChildCount()):
            self._get_scene_nodes_recursive(self.root_node.GetChild(i))
        return self.scene_nodes

    def remove_namespace(self):
        """
        Removes the namespace from all nodes in the fbx file.
        """
        self.get_scene_nodes()

        try:
            for node in self.scene_nodes:
                node_name = node.GetName()
                split_name = node_name.split(":")
                if len(split_name) > 1:
                    string_without_namespace = split_name[-1:][0]
                    node.SetName(string_without_namespace)
        except Exception as e:
            logger.error(f"Failed to strip the namespace. Issue: {e}")

    def remove_nodes_by_names(self, name_list):
        """
        Removes nodes from the fbx file.

        Args:
            name_list (list): The names of the nodes that need to be removed from the fbx file.
        """

        if not isinstance(name_list, list):
            logger.warning("Given name_list is not type list.")
            return False

        removed_nodes = []
        if name_list:
            self.get_scene_nodes()
            remove_nodes = [node for node in self.scene_nodes if node.GetName() in name_list]
            for node in remove_nodes:

                # parent children to world before removing the node
                for c_i in reversed(range(node.GetChildCount())):
                    child_node = node.GetChild(c_i)
                    if child_node:
                        self.root_node.AddChild(child_node)

                # remove parent node
                self.scene.DisconnectSrcObject(node)
                self.scene.RemoveNode(node)
                removed_nodes.append(node)
            self.get_scene_nodes()

        return removed_nodes

    def set_nodes_visibility(self, status=True):
        """
        Sets the visibility for all the nodes in the fbx file.

        Args:
            status (bool): turn on/off the visibility
        """
        self.get_scene_nodes()
        remove_nodes = [node.SetVisibility(status) for node in self.scene_nodes]

    def save(self, path=None):
        """
        Saves the current fbx scene or a given fbx file path

        Args:
            path (str, optional): if not None, it will be used as path to save the fbx file.
        """

        try:
            if not self.fbx_common:
                self.fbx_common = get_fbx_common_module()
            if path is not None:
                self.fbx_common.SaveScene(self.sdk_manager, self.scene, path)
            else:
                self.fbx_common.SaveScene(self.sdk_manager, self.scene, self.path)
        except Exception as e:
            logger.error(f"Failed to save the fbx file. Issue: {e}")


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    import gt.utils.system as utils_sys
    import os

    desktop_dir = utils_sys.get_desktop_path()

    """
    # ANIMATION EXPORT
    # -- TO TEST: open any maya animation file in ../source_art_main/Animation/
    # -- export selection is active by default, make sure to select the skeleton in the scene
    fbx_exp = FbxExporter()
    # fbx_exp = FBXExporter(selection=0)  # export all
    anim_fbx_name = "test_anim.fbx"
    anim_fbx_path = os.path.join(desktop_dir, anim_fbx_name)
    with fbx_exp as fbx:
        # fbx.set_preferences_animation()
        fbx.set_preferences_animation(start_frame=10, end_frame=30)
        fbx.export_file(path=anim_fbx_path)
    """

    # SKELETAL-MESH EXPORT
    # -- TO TEST: open average rig, delete "setup" and "controls" and set the a_pose (core_pose.set_apose()).
    # -- export selection is active by default, make sure to select the skeleton and the meshes
    # fbx_exp = FbxExporter()
    # --export all
    fbx_exp = FbxExporter(selection=False)
    skl_mesh_fbx_name = "test_skl_mesh.fbx"
    skl_mesh_fbx_path = os.path.join(desktop_dir, skl_mesh_fbx_name)
    with fbx_exp as fbx:
        fbx.set_preferences_skeletal_mesh()
        fbx.export_file(path=skl_mesh_fbx_path)

    """
    # SKELETAL-MESH EXPORT
    # -- TO TEST: open any maya environment file, or create a new mesh and select the meshes that you want to test.
    # -- export selection is active by default, make sure to select the meshes you need
    fbx_exp = FbxExporter()
    mesh_fbx_name = "test_mesh.fbx"
    mesh_fbx_path = os.path.join(desktop_dir, mesh_fbx_name)
    with fbx_exp as fbx:
        fbx.set_preferences_mesh()
        fbx.export_file(path=mesh_fbx_path)
    """
