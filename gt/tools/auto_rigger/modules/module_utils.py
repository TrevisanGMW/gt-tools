"""
Auto Rigger Utils Modules
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.playblast as core_playblast
import gt.core.constraint as core_cnstr
import gt.core.outliner as core_outlnr
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.core.iterable as core_iter
import gt.core.surface as core_sur
import gt.core.curve as core_curve
import gt.core.poses as core_poses
import gt.core.scene as core_scene
import gt.core.logger as core_log
import gt.core.skin as core_skin
import gt.core.anim as core_anim
import gt.core.attr as core_attr
import gt.core.io as core_io
import maya.cmds as cmds
import binascii
import logging
import base64
import pathlib
import os

# Logging Setup
logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, propagate=False)
logger.setLevel(logging.INFO)
core_log.add_custom_log_levels()


class ModuleGroup(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_group
    bypass_activation = True  # No activation system for groups

    def __init__(self, name="Group", prefix=None, suffix=None):
        """
        Initialize the ModuleGroup instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.proxies = [tools_rig_frm.Proxy(name="Group")]
        self.active = False  # Must be False, groups don't build anything


class ModuleNewScene(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_new_scene
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="New Scene", prefix=None, suffix=None):
        """
        Initialize the ModuleNewScene instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.set_extra_callable_function(self._force_new_scene, order=tools_rig_frm.CodeData.Order.pre_proxy)
        self.scene_options = {
            "linear_unit": "centimeter",
            "angular_unit": "degree",
            "frame_rate": "30fps",
            "multi_sample": True,
            "multi_sample_count": 8,
            "persp_clip_plane_near": 1,
            "persp_clip_plane_far": 10000.0,
            "display_textures": True,
            "playback_frame_start": 1,
            "playback_frame_end": 120,
            "animation_frame_start": 1,
            "animation_frame_end": 200,
            "current_time": 1,
            "use_default_material": False,
            "grid_size": 12.0,
            "grid_spacing": 5.0,
            "grid_divisions": 5.0,
        }

    def _force_new_scene(self):
        """
        Use maya commands to trigger a new scene without asking if the user wants to save current work.
        If initial scene options were provided, these are set after starting a new scene.
        """
        cmds.file(new=True, force=True)
        if self.scene_options:
            self.apply_scene_options()

    def set_scene_options(self, scene_options_dict):
        """
        Sets the initial options dictionary for the scene.
        The keys are the name of the attributes/options that will be affected.
        The values are the desired preferences.
        See "core_scene.set_scene_from_dict()" docstrings for recognized keys and values.

        Args:
            scene_options_dict: A dictionary describing the initial values of a scene.
        """
        if not scene_options_dict or not isinstance(scene_options_dict, dict):
            logger.warning(f"Unable to set attribute values dictionary. Incorrect input type.")
            return
        self.scene_options = scene_options_dict

    def apply_scene_options(self):
        """
        Applies the stored scene options.
        """
        core_scene.set_scene_from_dict(self.scene_options)


class ModulePython(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_python
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Python", prefix=None, suffix=None):
        """
        Initialize the ModulePython instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.font_size = 14
        self.code = tools_rig_frm.CodeData()
        self.code.set_execution_code("")
        self.code.set_order(tools_rig_frm.CodeData.Order.post_build)

    def set_execution_code(self, code):
        """
        Sets a stored string that is used as python code.
        Args:
            code (str): A string to be executed as python code.
        """
        self.code.set_execution_code(code=code)


class ModuleImportFile(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_import_file
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Import File", prefix=None, suffix=None):
        """
        Initialize the ModuleImportFile instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        # Import Preferences
        self.file_path = "{project-dir}/geo/{project-name}.ma"
        self.file_type = None  # The type of the file (e.g., "OBJ", "mayaAscii").
        self.namespace = ""  # Namespace for the imported objects.
        self.merge_namespaces_on_clash = False  # If True, merges namespaces on name clash.
        self.reference = False  # If True imports as a reference
        self.set_extra_callable_function(self.import_file, order=tools_rig_frm.CodeData.Order.post_skeleton)
        self._imported_cache = []  # A list of imported objects (only populated after first call)
        self.proxy_import = False
        self.transforms_parent = "geometry"
        self.purge_namespaces = True
        self.purge_keyframes = True
        self.purge_display_layers = True  # If displayer layers are detected in the imported scene, these are deleted.
        self.deactivate_drawing_overrides = True  # Deactivates drawing overrides on the imported notes.

    def import_file(self, transforms_parent_override=None):
        """
        Use maya commands to import a file into the current scene.
        When executed, this function stores the name of the imported elements in the "self._imported_cache" variable.

        Args:
            transforms_parent_override (str, optional): If provided, this will override the user variable
                                                        "self.transforms_parent_override" with the provided data.
        """
        # Initial Check
        _parsed_path = self.parse_path(path=self.file_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to import missing file. Path: "{str(_parsed_path)}".')
            return
        self.warn_if_path_outside_project(_parsed_path)
        # Existing Namespaces
        existing_namespaces = set(cmds.namespaceInfo(lon=True) or [])
        # Extra Parameters
        extra_params = {}
        if self.file_type is not None:
            extra_params["typ"] = self.file_type
        if self.namespace:
            extra_params["namespace"] = self.namespace
        if self.merge_namespaces_on_clash is not None:
            extra_params["mergeNamespacesOnClash"] = self.merge_namespaces_on_clash
        # Importing or Referencing
        if self.reference is not None and self.reference is True:
            extra_params["reference"] = self.reference  # Cannot be called at the same time as i=True
        else:
            extra_params["i"] = True  # (i=True is the long name for "import")
        # Import Function Call
        try:
            self._imported_cache = cmds.file(_parsed_path, returnNewNodes=True, **extra_params) or []
        except Exception as e:
            logger.warning(f"Unable to import file. Issue: {str(e)}.")
            return  # Exit if import failed to prevent subsequent errors
        # Purge Display Layers
        if self.purge_display_layers:
            # This captures empty layers (which have no connections) and populated ones.
            imported_layers = cmds.ls(self._imported_cache, type="displayLayer") or []
            for layer in imported_layers:
                # Safety: Ensure we never attempt to delete the default layer
                if layer == "defaultLayer":
                    continue
                # Try to delete, log warning if it fails (e.g. referenced layers)
                if cmds.objExists(layer):
                    try:
                        cmds.delete(layer)
                    except Exception as e:
                        logger.debug(
                            f"Unable to delete imported display layer '{layer}'. It may be referenced. Issue: {e}"
                        )
        # Deactivate Drawing Overrides
        if self.deactivate_drawing_overrides:
            for node in self._imported_cache:
                # Optimized: Only check attribute on DAG nodes to avoid errors on non-DAG nodes
                if cmds.objExists(f"{node}.overrideEnabled"):
                    try:
                        cmds.setAttr(f"{node}.overrideEnabled", 0)
                    except Exception as e:
                        logger.debug(f"Unable to deactivate drawing overrides on {node}. Issue: {e}")

        # Delete keyframes
        if self.purge_keyframes:
            imported_cache = core_iter.sanitize_maya_list(
                input_list=self._imported_cache,
                filter_existing=True,
                filter_unique=False,
                convert_to_nodes=False,
                sort_list=False,
            )
            key_frames = core_anim.get_time_keyframes(obj_list=imported_cache)
            if key_frames:
                cmds.delete(key_frames)
        # Re-parent transforms
        try:
            _transform_parent = self.transforms_parent
            if transforms_parent_override:
                _transform_parent = transforms_parent_override
            if self._imported_cache and _transform_parent:
                if not cmds.objExists(_transform_parent):
                    logger.warning(
                        f'Unable to re-parent imported transforms. Missing target object: "{_transform_parent}".'
                    )
                else:
                    _transforms = cmds.ls(self._imported_cache, typ="transform")
                    for trans in _transforms:
                        # Ensure we only parent root transforms, not children
                        if cmds.listRelatives(trans, parent=True) is None:
                            cmds.parent(trans, _transform_parent)
        except Exception as e:
            logger.warning(f"Unable to re-parent imported transforms. Issue: {str(e)}.")
        # Delete namespaces
        if self.purge_namespaces:
            new_namespaces = set(cmds.namespaceInfo(lon=True) or []) - existing_namespaces
            for ns in new_namespaces:
                try:
                    cmds.namespace(removeNamespace=ns, mergeNamespaceWithRoot=True)
                except RuntimeError as e:
                    logger.warning(f"Unable to remove imported namespaces. Issue: {e}")

    # ------------------------------------------- Extra Module Setters ------------------------------------------
    def set_file_path(self, file_path):
        """
        Sets the path used to import a file.
        Args:
            file_path (str): A file path to be imported. it overwrites the value even if an empty string.
        """
        if file_path is None:
            self.file_path = ""
        if not isinstance(file_path, str):
            logger.warning("Unable to set file path. Invalid data type was provided.")
            return
        self.file_path = file_path

    def set_file_type(self, file_type):
        """
        Sets the path used to import a file.
        Set the type of this file. By default, this can be any one of: "mayaAscii", "mayaBinary", "mel", "OBJ",
        "directory", "plug-in", "audio", "move", "EPS", "Adobe(R) Illustrator(R)", "image".
        Plug-ins may define their own types as well. e.g. "FBX"

        Args:
            file_type (str, None): A file type to be imported. If empty or None the value is cleared and a
                                   file type is considered to not be defined.
        """
        if file_type is None or file_type == "":
            self.file_type = None
            return
        if not isinstance(file_type, str):
            logger.warning("Unable to set file type. Invalid data type was provided.")
            return
        self.file_type = file_type

    def set_namespace(self, namespace):
        """
        Sets the namespace used by the imported elements.
        The new namespace will be created by this command and can not already exist. The old namespace will be removed.

        Args:
            namespace (str, None): A file type to be imported. If empty or None the value is cleared and a
                                   file type is considered to not be defined.
        """
        if namespace is None or namespace == "":
            self.namespace = None
            return
        if not isinstance(namespace, str):
            logger.warning("Unable to set namespace. Invalid data type was provided.")
            return
        self.namespace = namespace

    def set_merge_namespaces_on_clash(self, merge_namespaces_on_clash):
        """
        Used with the -import or -reference flag to prevent new namespaces from being created when namespaces of
        the same name already exist within Maya. For example, lets pretend a file being imported refers to
        "ref:pSphere1" and there is already a namespace called "ref" defined in Maya.
        If -mergeNamespacesOnClash is true, the existing ref namespace will be reused and pSphere1 will be moved
        into the existing namespace. If -mergeNamespacesOnClash is false, a new namespace will be created
        (in this case "ref1") and "pShere1" moved into the ref1 namespace. The default value is false.

        Args:
            merge_namespaces_on_clash (bool): If True, merge namespaces on clash. Read above for more details.
        """
        if not isinstance(merge_namespaces_on_clash, bool):
            logger.warning('Unable to set "merge namespaces on clash" state. Invalid data type was provided.')
            return
        self.merge_namespaces_on_clash = merge_namespaces_on_clash

    def set_reference(self, reference):
        """
        Determines if it should create a reference to the specified file instead of just importing.
        Args:
            reference (bool): If True, imported file will be referenced instead of simply imported.
        """
        if not isinstance(reference, bool):
            logger.warning('Unable to set "reference" state. Invalid data type was provided.')
            return
        self.reference = reference

    def set_transforms_parent(self, transforms_parent):
        """
        Sets a parent for the imported transforms.
        Args:
            transforms_parent (str, None): New parent of the imported elements. If a name is provided, and it's
                                           available in the scene, all imported transforms are re-parented to be
                                           children of this element.
        """
        if transforms_parent is None:
            self.transforms_parent = None  # Clear transforms_parent
            return
        if not isinstance(transforms_parent, str):
            logger.warning("Unable to set transforms parent. Invalid data type was provided.")
            return
        self.transforms_parent = transforms_parent

    def build_proxy(self, project_prefix=None, optimized=False):
        """
        Function override used to force import during proxy step
        Args:
            project_prefix (str, optional): Only here due to overwrite. Not used for the import file module.
            optimized (bool, optional): If True, it's assumed that the control rig is being built, so not in proxy mode.
        """
        if self.proxy_import and not optimized:  # When not optimized, the user is in edit proxy mode.
            proxy_parent_grp = tools_rig_utils.find_root_group_proxy()
            geometry_dict = tools_rig_utils.create_utility_groups(geometry=True, target_parent=proxy_parent_grp)
            geometry_grp = next(iter(geometry_dict.values()))
            core_outlnr.reorder_front(geometry_grp)  # Move group to the top
            # Geometry Selectable Behaviour
            core_attr.add_separator_attr(target_object=geometry_grp, attr_name=f"geometryOptions")
            block_sel_attr = tools_rig_const.RiggerConstants.ATTR_BLOCK_SELECTION
            core_attr.add_attr(obj_list=geometry_grp, attr_type="bool", is_keyable=True, attributes=block_sel_attr)
            cmds.setAttr(f"{geometry_grp}.{block_sel_attr}", 1)
            cmds.setAttr(f"{geometry_grp}.overrideDisplayType", 2)
            cmds.connectAttr(f"{geometry_grp}.{block_sel_attr}", f"{geometry_grp}.overrideEnabled")
            self.import_file(transforms_parent_override=geometry_grp)
        return []  # Must return a list, but not used in this case.


class ModuleSkinWeights(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_skin_weights
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Skin Weights", prefix=None, suffix=None):
        """
        Initialize the ModuleSkinWeights instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        # Module User Preferences
        self.influences_dir = r"{project-dir}\influences"
        self.weights_dir = r"{project-dir}\weights"
        self.remove_unused_influences = False
        self.clear_target_dir = False
        # Module Data
        self._file_format = ".json"

        self.set_extra_callable_function(
            self._read_influences_and_weights, order=tools_rig_frm.CodeData.Order.post_build
        )

    def _read_influences_and_weights(self):
        """
        Reads all influences and skin weights files found under the stored paths.
        """
        self._read_influences()
        self._read_weights()

    def _read_influences(self):
        """
        Reads all influences found under the influences directory and attempts to apply them.
        """
        # Initial Check
        _parsed_path = self.parse_path(path=self.influences_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to import influences. Path: "{str(_parsed_path)}".')
            return
        self.warn_if_path_outside_project(_parsed_path)
        for filename in os.listdir(_parsed_path):
            if filename.endswith(self._file_format):  # TODO add UUID lookup method
                _influence_file = os.path.join(_parsed_path, filename)
                _influence_data = core_io.read_json_dict(_influence_file)
                # Unpack data
                joints = _influence_data.get(core_skin.SkinInfluencesData.INFLUENCES)
                geo = _influence_data.get(core_skin.SkinInfluencesData.MESH) or _influence_data.get(
                    core_skin.SkinInfluencesData.SURFACE
                )
                max_influences = _influence_data.get(core_skin.SkinInfluencesData.MAX_INFLUENCES)
                maintain_max_influences = _influence_data.get(core_skin.SkinInfluencesData.MAINTAIN_MAX_INFL)
                # Basic checks
                if not cmds.objExists(geo):
                    logger.warning(f"Unable to bind missing mesh: {geo}")
                    continue
                if core_skin.is_mesh_bound(geo):
                    logger.warning(f"Mesh is already bound. Influence import was skipped: {geo}")
                    continue
                # Bind elements
                skin_cluster = core_skin.bind_skin(joints=joints, objects=geo, maximum_influences=max_influences)
                if skin_cluster:
                    cmds.setAttr(f"{skin_cluster[0]}.maintainMaxInfluences", maintain_max_influences)

    def _read_weights(self):
        """
        Reads all weights found under the influences directory and attempts to apply them.
        """
        # Initial Check
        _parsed_path = self.parse_path(path=self.weights_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to import skin weights from missing directory. Path: "{str(_parsed_path)}".')
            return
        self.warn_if_path_outside_project(_parsed_path)
        for filename in os.listdir(_parsed_path):
            if filename.endswith(self._file_format):  # TODO add UUID lookup method
                _weights_file = os.path.join(_parsed_path, filename)
                _weights_data = core_io.read_json_dict(_weights_file)

                # Unpack data
                mesh = _weights_data.get(core_skin.SkinWeightsData.MESH)
                surface = _weights_data.get(core_skin.SkinWeightsData.SURFACE)
                weights = _weights_data.get(core_skin.SkinWeightsData.WEIGHTS)
                long_influences = None
                if core_skin.SkinWeightsData.LONG_INFLUENCES in _weights_data.keys():
                    long_influences = _weights_data.get(core_skin.SkinWeightsData.LONG_INFLUENCES)

                # Check types
                if all(geo is False or geo is None for geo in (mesh, surface)):
                    logger.warning(f"Unable to read skin weights data. No recognized target type was detected.")

                # Set Skin Weights
                if mesh:
                    if not cmds.objExists(mesh):
                        logger.warning(f"Unable to apply skin weights on missing mesh: {mesh}")
                        continue
                    if not core_skin.is_mesh_bound(mesh):
                        logger.warning(f"Mesh is not bound. Weights import was skipped: {mesh}")
                        continue

                    core_skin.set_skin_weights(
                        skinned_mesh=mesh,
                        skin_data=weights,
                        remove_unused_inf=self.remove_unused_influences,
                        long_influences=long_influences,
                    )

                elif surface:
                    if not cmds.objExists(surface):
                        logger.warning(f"Unable to apply skin weights on missing surface: {surface}")
                        continue
                    if not core_skin.is_mesh_bound(surface):
                        logger.warning(f"Surface is not bound. Weights import was skipped: {surface}")
                        continue

                    core_skin.set_skin_weights_on_surface(
                        skinned_surface=surface,
                        skin_data=weights,
                        decode_str_keys=True,
                        long_influences=long_influences,
                    )

    def write_influences(self, skinned_geometry, clear_target_dir=True):
        """
        Write influences for the provided elements.
        Args:
            skinned_geometry (list): A list of skinned meshes
            clear_target_dir (bool, optional): If True, all files with the influence extension found in the target
                                               directory get purged/deleted before writing new ones.
        """
        # Get write directory
        _parsed_path = self.parse_path(path=self.influences_dir)
        _parsed_path = core_io.make_directory(_parsed_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to write influences. Invalid path: "{str(_parsed_path)}".')
            return
        # Clear existing
        if clear_target_dir:
            core_io.delete_dir_files(directory_path=_parsed_path, file_extension=self._file_format)

        # Write Influences
        for skinned_geo in skinned_geometry:
            if not core_skin.is_mesh_bound(skinned_geo):
                logger.warning(f"Unable to write influences for unbound geometry: {skinned_geo}")
                continue
            _skin_cluster = core_skin.get_skin_cluster(skinned_geo)
            _bound_joints = core_skin.get_bound_joints(skinned_geo)
            # Define Type
            geo_type = core_skin.SkinInfluencesData.MESH
            if core_sur.is_surface(skinned_geo):
                geo_type = core_skin.SkinInfluencesData.SURFACE
            # Assemble Dictionary
            _influences_dict = {
                geo_type: skinned_geo,
                core_skin.SkinInfluencesData.MAX_INFLUENCES: cmds.getAttr(f"{_skin_cluster}.maxInfluences"),
                core_skin.SkinInfluencesData.MAINTAIN_MAX_INFL: cmds.getAttr(f"{_skin_cluster}.maintainMaxInfluences"),
                core_skin.SkinInfluencesData.INFLUENCES: _bound_joints,
            }
            _mesh_short_name = core_naming.get_short_name(skinned_geo)
            _file_path = os.path.join(_parsed_path, f"{_mesh_short_name}{self._file_format}")

            # If already present, make it modifiable
            if _file_path and os.path.exists(_file_path):
                core_io.set_file_permission_modifiable(_file_path)

            core_io.write_json(path=_file_path, data=_influences_dict)
            logger.info(f'Influences written to: "{_parsed_path}"')

    def write_influences_from_selection(self, clear_target_dir=True):
        """
        Same as "write_influences" but automatically populates the skinned meshes parameter with selection.
        Args:
            clear_target_dir (bool, optional): If True, all files with the influence extension found in the target
                                               directory get purged/deleted before writing new ones.
        """
        selection = cmds.ls(selection=True, long=True) or []
        if not selection:
            logger.warning(f"Nothing selected. Select skinned meshes and try again.")
            return
        # TODO, filter skinned meshes - log bad selection
        self.write_influences(skinned_geometry=selection, clear_target_dir=clear_target_dir)

    def write_weights(self, skinned_meshes, clear_target_dir=True, remove_unused_inf=False):
        """
        Write weights for the provided elements.
        Args:
            skinned_meshes (list): A list of skinned meshes
            clear_target_dir (bool, optional): If True, all files with the influence extension found in the target
                                               directory get purged/deleted before writing new ones.
            remove_unused_inf (bool): removes unused influences at the end of the process.
        """
        # Get write directory
        _parsed_path = self.parse_path(path=self.weights_dir)
        _parsed_path = core_io.make_directory(_parsed_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to write weights. Invalid path: "{str(_parsed_path)}".')
            return
        # Clear existing
        if clear_target_dir:
            core_io.delete_dir_files(directory_path=_parsed_path, file_extension=self._file_format)

        skinned_surfaces = core_iter.sanitize_maya_list(
            input_list=skinned_meshes,
            filter_existing=True,
            filter_unique=True,
            filter_string=None,
            filter_func=None,
            filter_type="nurbsSurface",
            sort_list=False,
            reverse_list=False,
            hierarchy=False,
            convert_to_nodes=False,
            short_names=False,
            consider_shape_type=True,
        )

        skinned_meshes = core_iter.sanitize_maya_list(
            input_list=skinned_meshes,
            filter_existing=True,
            filter_unique=True,
            filter_type="mesh",
            sort_list=False,
            reverse_list=False,
            hierarchy=False,
            convert_to_nodes=False,
            short_names=False,
            consider_shape_type=True,
        )

        # Write Weights (Meshes)
        for skinned_mesh in skinned_meshes:
            if not core_skin.is_mesh_bound(skinned_mesh):
                logger.warning(f"Unable to write skin weights for unbound mesh: {skinned_mesh}")
                continue
            _skin_cluster = core_skin.get_skin_cluster(skinned_mesh)
            _weights = core_skin.get_skin_weights(skinned_mesh, remove_unused_inf=remove_unused_inf)
            _long_influences = core_skin.get_influences_long_dict(_skin_cluster)

            # assemble skin weights data dictionary
            _weights_dict = {
                core_skin.SkinWeightsData.MESH: skinned_mesh,
                core_skin.SkinWeightsData.WEIGHTS: _weights,
                core_skin.SkinWeightsData.LONG_INFLUENCES: _long_influences,
            }

            _mesh_short_name = core_naming.get_short_name(skinned_mesh)
            _file_path = os.path.join(_parsed_path, f"{_mesh_short_name}{self._file_format}")

            # If already present, make it modifiable
            if _file_path and os.path.exists(_file_path):
                core_io.set_file_permission_modifiable(_file_path)

            core_io.write_json(path=_file_path, data=_weights_dict)
            logger.info(f'Weights written to: "{_parsed_path}"')

        # Write Weights (Surfaces)
        for skinned_sur in skinned_surfaces:
            if not core_skin.is_mesh_bound(skinned_sur):
                logger.warning(f"Unable to write skin weights for unbound surface: {skinned_sur}")
                continue
            _skin_cluster = core_skin.get_skin_cluster(skinned_sur)
            _weights = core_skin.get_skin_weights_from_surface(
                skinned_sur, remove_unused_inf=remove_unused_inf, encode_key_as_str=True
            )
            _long_influences = core_skin.get_influences_long_dict(_skin_cluster)

            # assemble skin weights data dictionary
            _weights_dict = {
                core_skin.SkinWeightsData.SURFACE: skinned_sur,
                core_skin.SkinWeightsData.WEIGHTS: _weights,
                core_skin.SkinWeightsData.LONG_INFLUENCES: _long_influences,
            }

            _sur_short_name = core_naming.get_short_name(skinned_sur)
            _file_path = os.path.join(_parsed_path, f"{_sur_short_name}{self._file_format}")

            # If already present, make it modifiable
            if _file_path and os.path.exists(_file_path):
                core_io.set_file_permission_modifiable(_file_path)

            core_io.write_json(path=_file_path, data=_weights_dict)
            logger.info(f'Weights written to: "{_parsed_path}"')

    def write_weights_from_selection(self, clear_target_dir=True, remove_unused_inf=False):
        """
        Same as "write_weights" but automatically populates the skinned meshes parameter with selection.
        Args:
            clear_target_dir (bool, optional): If True, all files with the influence extension found in the target
                                                   directory get purged/deleted before writing new ones.
            remove_unused_inf (bool): removes unused influences at the end of the process.
        """
        selection = cmds.ls(selection=True, long=True) or []
        if not selection:
            logger.warning(f"Nothing selected. Select skinned meshes and try again.")
            return
        # TODO, filter skinned meshes - log bad selection
        self.write_weights(
            skinned_meshes=selection,
            clear_target_dir=clear_target_dir,
            remove_unused_inf=remove_unused_inf,
        )

    # ------------------------------------------- Extra Module Setters ------------------------------------------
    def set_influences_dir(self, influences_dir):
        """
        Sets the directory path used to import influence files.
        Args:
            influences_dir (str): A file path to be used when writing or reading a list of influences.
        """
        if influences_dir is None:
            self.influences_dir = ""
        if not isinstance(influences_dir, str):
            logger.warning("Unable to influences path. Invalid data type was provided.")
            return
        self.influences_dir = influences_dir

    def set_weights_dir(self, weights_dir):
        """
        Sets the directory path used to import weight files.
        Args:
            weights_dir (str): A file path to be used when writing or reading a list of weights.
        """
        if weights_dir is None:
            self.weights_dir = ""
        if not isinstance(weights_dir, str):
            logger.warning("Unable to weight path. Invalid data type was provided.")
            return
        self.weights_dir = weights_dir

    def set_remove_unused_influences(self, status):
        """
        Sets the remove_unused_influences variable.
        Args:
            status (bool): remove_unused_influences on/off
        """
        if not isinstance(status, bool):
            logger.warning("Unable to set remove_unused_influences. Invalid data type was provided.")
            return
        self.remove_unused_influences = status


class ModuleExportSkeletalMesh(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_export_sk
    allow_parenting = True
    allow_multiple = True

    class RootLookupMethods:
        def __init__(self):
            """
            A library of export methods for the skeletal mesh module.
            """

        SINGLE_ROOT = 0  # Expects to find single joint in the skeleton group.
        SKINNED_ROOT = 1  # Grabs the parent joint of a skinned mesh and interprets it as the root.
        SKINNED_ONLY = 2  # Only includes the absolutely necessary joints to drive a skinned mesh.

        @classmethod
        def get_names(cls):
            """
            Returns a list of all defined method names.
            """
            return [name for name in cls.__dict__ if not name.startswith("__") and name.isupper()]

    def __init__(self, name="Export SKM", prefix=None, suffix=None):
        """
        Initialize the ModuleExportSkeletalMesh instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.orientation = None  # Changed to None so it doesn't get serialized.

        # Export preferences
        self.export_dir = r"{project-dir}\exports"
        self.export_filename = "SKM_{project-name}"
        self.export_pose = core_naming.NamingConstants.Poses.APOSE
        self._file_format = ".fbx"

        self.root_lookup_method = ModuleExportSkeletalMesh.RootLookupMethods.SINGLE_ROOT

        self.mesh_filter_include = "*"  # Accepts wild cards, default is "*" so everything is included.
        self.mesh_filter_exclude = ""  # Accepts wild cards e.g. "*1" doesn't include items with 1 as suffix.
        self.mesh_filter_short_names = False  # If True, filters short names, otherwise filters long names.

        # Set function call
        self.set_extra_callable_function(self._export_skeletal_mesh, order=tools_rig_frm.CodeData.Order.post_skeleton)

    def set_export_dir(self, export_dir):
        """
        Sets the directory path used to export the skeletal mesh fbx files.
        Args:
            export_dir (str): A file path to be used when writing or reading the skeletal mesh fbx files.
        """
        if export_dir is None:
            self.export_dir = ""
        if not isinstance(export_dir, str):
            logger.warning("Unable to get the export path. Invalid data type was provided.")
            return
        self.export_dir = export_dir

    def set_export_filename(self, filename=None):
        """
        Sets the filename used to export the skeletal mesh.
        Args:
            filename (str): A filename, basename of the export file path.
                            If empty, it keeps the default initial value.
        """
        if filename is None:
            logger.warning("Unable to set the export filename. Provided None value.")
            return
        if not isinstance(filename, str):
            logger.warning("Unable to set filename. Invalid data type was provided.")
            return
        else:
            self.export_filename = filename

    def set_export_pose(self, pose=None):
        """
        Sets the name of pose that should be used (if it exists) during the export process.
        Args:
            pose (str): name of the pose that the user wants for the export process.
                        If empty, it keeps the default initial value.
        """
        if pose is None:
            logger.warning("Unable to set the export pose. Provided None value.")
            return
        if not isinstance(pose, str):
            logger.warning("Unable to set the export pose. Invalid data type was provided.")
            return
        else:
            self.export_pose = pose

    def _export_skeletal_mesh(self):
        """
        Exports in fbx the skeleton and the meshes plus skin weights related to the skin clusters connected.

        Assumption: the export module utils is part of the auto-rigger tool and since
                    it manages the rigging process of one asset, in the scene there
                    should be just one skeleton.
                    The function will consider the objects without namespace, and the first top root joint
                    in order to identify the skeleton.
        """
        import gt.tools.auto_rigger.rig_utils as tools_rig_utils
        import gt.utils.fbx as utils_fbx

        # Set the export pose if required.
        export_pose_used = False
        if cmds.objExists(self.export_pose):
            core_poses.set_dagpose(pose_name=self.export_pose, namespace="")
            export_pose_used = True

        # Get skeleton joints
        self._export_root_joints = [tools_rig_utils.get_single_skeleton_root_joint()]  # Defaults to single root
        if self.root_lookup_method != self.RootLookupMethods.SINGLE_ROOT:  # Get all joints when not using single root
            self._export_root_joints = tools_rig_utils.get_skeleton_joints()

        if not self._export_root_joints:
            skl_grp = tools_rig_const.RiggerConstants.GRP_SKELETON_NAME
            logger.warning(f"Root joint not found. No joints in world or under the main skeleton group {skl_grp}")
            return

        # Get the meshes connected through the skin clusters
        self._export_joints = []  # filled in _get_export_meshes
        export_meshes = self._get_export_meshes()
        if not export_meshes:
            logger.warning(f"Cannot find skinned meshed connected to the hierarchy of {self._export_root_joints}")
            return

        # Select objects
        cmds.select(cl=True)
        export_objects = self._export_joints
        export_objects.extend(export_meshes)
        cmds.select(export_objects)

        # Export
        fbx_exp = utils_fbx.FbxExporter()
        _parsed_export_dir = self.parse_path(path=self.export_dir)
        self.warn_if_path_outside_project(_parsed_export_dir)
        core_io.make_directory(_parsed_export_dir)
        export_fbx_path = os.path.join(_parsed_export_dir, f"{self.export_filename}{self._file_format}")
        export_fbx_path = self.parse_path(path=export_fbx_path)

        # If already present, make it modifiable
        if export_fbx_path and os.path.exists(export_fbx_path):
            core_io.set_file_permission_modifiable(export_fbx_path)

        with fbx_exp as fbx:
            fbx.set_preferences_skeletal_mesh()
            fbx.export_file(path=export_fbx_path)

        # Clear selection
        cmds.select(cl=True)

        # Restore rig pose if needed
        tpose = core_naming.NamingConstants.Poses.TPOSE  # default rig pose
        if export_pose_used and cmds.objExists(tpose):
            core_poses.set_tpose(namespace="")
        core_cnstr.evaluate_constraints()

    def _get_export_meshes(self):
        """
        Gets the meshes skinned to the export skeleton joints, required to export successfully the skeletal mesh.

        Returns:
            list: the export meshes.
        """
        import maya.OpenMaya as OpenMaya

        self._export_joints = []
        for jnt in self._export_root_joints:
            self._export_joints += core_hrchy.get_hierarchy(root=jnt, maya_type=OpenMaya.MFn.kJoint)

        skel_skin_clusters = []
        for e_jnt in self._export_joints:
            skin_clst = cmds.listConnections(e_jnt, t="skinCluster")
            if skin_clst:
                [skel_skin_clusters.append(sc) for sc in skin_clst if sc not in skel_skin_clusters]

        if not skel_skin_clusters:
            return

        shapes_connected = []
        for sc in skel_skin_clusters:
            shapes = cmds.skinCluster(sc, q=True, g=True)
            if shapes:
                [shapes_connected.append(shape) for shape in shapes if shape not in shapes_connected]

        export_meshes = cmds.listRelatives(shapes_connected, parent=True, fullPath=True)

        # Filter Meshes
        if self.mesh_filter_short_names:
            short_names = [core_naming.get_short_name(long_name) for long_name in export_meshes]
            filtered_short_names = core_iter.filter_elements(
                elements=short_names,
                include_filter=self.mesh_filter_include,
                exclude_filter=self.mesh_filter_exclude,
            )
            _new_export_meshes = [
                long_name
                for long_name in export_meshes
                if any(long_name.split("|")[-1] == short_name for short_name in filtered_short_names)
            ]
            export_meshes = _new_export_meshes
        else:
            export_meshes = core_iter.filter_elements(
                elements=export_meshes,
                include_filter=self.mesh_filter_include,
                exclude_filter=self.mesh_filter_exclude,
            )

        # Filter according to root lookup method
        if self.root_lookup_method != self.RootLookupMethods.SINGLE_ROOT:
            new_export_joints = []
            for mesh in export_meshes:
                skin_cluster = core_skin.get_skin_cluster(obj=mesh)
                new_export_joints += core_skin.get_influences(skin_cluster=skin_cluster)
            self._export_joints = new_export_joints  # SKINNED_ONLY
            if self.root_lookup_method == self.RootLookupMethods.SKINNED_ROOT:  # Get Expanded Root
                top_parents = []
                for jnt in self._export_joints:
                    top_parents.append(core_hrchy.find_top_parent(obj=jnt, target_type="joint"))
                new_export_joints = []
                for jnt in list(set(top_parents)):
                    new_export_joints += core_hrchy.get_hierarchy(root=jnt, maya_type=OpenMaya.MFn.kJoint)
                self._export_joints = new_export_joints  # SKINNED_ROOT

        return export_meshes


class ModuleSaveScene(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_save_scene
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Save Scene", prefix=None, suffix=None):
        """
        Initialize the ModuleSaveScene instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.file_path = r"{project-dir}/{project-name}_rig.ma"
        self.file_extension = ".ma"  # MayaAscii
        self.set_extra_callable_function(self.force_save_scene, order=tools_rig_frm.CodeData.Order.post_build)

    def force_save_scene(self):
        """
        Use maya commands to save the scene as mayaAscii.
        """
        if not self.file_path:
            logger.warning("File path empty. Please first set a file path.")
            return

        _parsed_path = self.parse_path(path=self.file_path)
        if not os.path.isdir(os.path.dirname(_parsed_path)):
            logger.warning("Unable to find the scene directory. Please set a valid directory.")
            return
        if not _parsed_path.lower().endswith(self.file_extension):
            logger.warning(f"File path has a wrong extension. Please set a {self.file_extension} file path.")
            return
        self.warn_if_path_outside_project(_parsed_path)

        # If already present, make it modifiable
        if _parsed_path and os.path.exists(_parsed_path):
            core_io.set_file_permission_modifiable(_parsed_path)

        # Save File
        cmds.file(rename=_parsed_path)
        cmds.file(save=True, force=True, type="mayaAscii")
        logger.info(f"Maya scene has been saved: {_parsed_path}")

        return True

    def set_file_path(self, file_path=None, make_dir=True):
        """
        Sets the file path (complete path with filename) used to save the Maya scene.
        Eventual extension will be replaced by the defined extension value (see set_file_extension).

        Args:
            file_path (str): the complete path of the Maya scene.
            make_dir (bool): if True and the directory is missing, it will create it.
        """
        if not file_path:
            logger.warning("Unable to set the scene path. Provided empty value.")
            return
        if not isinstance(file_path, str):
            logger.warning("Unable to set the scene path. Invalid data type was provided.")
            return

        _parsed_path = self.parse_path(path=file_path)

        # Check folder
        if not os.path.exists(os.path.dirname(_parsed_path)) and make_dir:
            os.makedirs(os.path.dirname(_parsed_path))

        # Force mayaAscii extension
        if not _parsed_path.lower().endswith(self.file_extension):
            if _parsed_path.find(".") > -1:
                extension = _parsed_path.split(".")[-1]
                file_path = _parsed_path.replace(f".{extension}", self.file_extension)
            else:
                file_path = f"{_parsed_path}{self.file_extension}"

        file_path = file_path.replace("\\", "/")
        self.file_path = file_path

    def set_file_extension(self, extension=None):
        """
        Sets the file extension used to save the Maya scene.

        Args:
            extension (str): accepted only: "ma", "mb", by default the value used is "ma".
                             If None, the file extension will remain the default one.
        """
        if not extension:
            logger.warning("Unable to set the scene extension. Provided empty value.")
            return
        if not isinstance(extension, str):
            logger.warning("Unable to set the scene extension. Invalid data type was provided.")
            return
        if extension not in ["ma", "mb"]:
            logger.warning("Unable to set the scene extension. You can use only 'ma' or 'mb'.")
            return
        else:
            self.file_extension = f".{extension}"


class ModuleLoadScene(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_load_scene
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Load Scene", prefix=None, suffix=None):
        """
        Initialize the ModuleLoadScene instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.file_path = r"{project-dir}/{project-name}_rig.ma"
        self.bypass_warnings = False
        self.set_extra_callable_function(self.force_load_scene, order=tools_rig_frm.CodeData.Order.post_build)

    def force_load_scene(self):
        """
        Use maya commands to load a scene.
        """
        if not self.file_path:
            logger.warning("File path empty. Please set first a file path.")
            return

        _parsed_path = self.parse_path(path=self.file_path)
        if not os.path.isdir(os.path.dirname(_parsed_path)):
            logger.warning("Unable to find the file path. Please set a valid file path.")
            return

        # Show out of project warning
        if not self.bypass_warnings:
            self.warn_if_path_outside_project(_parsed_path)

        # If missing, warn the user
        if _parsed_path and not os.path.exists(_parsed_path):
            logging.warning(f"Unable to load scene from missing path: {_parsed_path}")
            return

        cmds.file(_parsed_path, open=True, force=True)

        logger.info(f"Maya scene loaded from: {_parsed_path}")
        return True

    def set_file_path(self, file_path=None):
        """
        Sets the file path (complete path with filename) used to load the Maya scene.

        Args:
            file_path (str): the complete path of a Maya scene or Maya compatible format file.
        """
        if not file_path:
            logger.warning("Unable to set the scene path. Provided empty value.")
            return
        if not isinstance(file_path, str):
            logger.warning("Unable to set the scene path. Invalid data type was provided.")
            return
        _parsed_path = self.parse_path(path=file_path)
        file_path = file_path.replace("\\", "/")
        self.file_path = file_path


class ModuleShapesSnapshot(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_shapes_snapshot
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Shapes Snapshot", prefix=None, suffix=None):
        """
        Initialize the ModuleShapesSnapshot instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        # Module User Preferences
        self.shapes_dir = r"{project-dir}\shapes"
        # Module Data
        self._file_format = ".json"

        self.set_extra_callable_function(self._read_shapes, order=tools_rig_frm.CodeData.Order.post_build)

    def _read_shapes(self):
        """
        Reads the shapes files found under the stored paths.
        """
        # Initial Check
        _parsed_path = self.parse_path(path=self.shapes_dir)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to import the shapes of the controls. Path: "{str(_parsed_path)}".')
            return
        self.warn_if_path_outside_project(_parsed_path)
        for filename in os.listdir(_parsed_path):
            if filename.endswith(self._file_format):
                _shape_file = os.path.join(_parsed_path, filename)
                _shape_data = core_io.read_json_dict(_shape_file)
                # Unpack data
                transform_long_name = _shape_data.get("name")
                transform_uuid = _shape_data.get("uuid")
                if not cmds.objExists(transform_long_name) and transform_uuid:
                    module_uuid, driver_type, driver_purpose = transform_uuid.split("-")
                    _transform_long_name = tools_rig_utils.find_drivers_from_module(
                        module_uuid,
                        filter_driver_type=driver_type,
                        filter_driver_purpose=driver_purpose,
                    )
                    if _transform_long_name:
                        transform_long_name = _transform_long_name[0]
                    else:
                        logger.warning(
                            f"Failed to find transform node using UUID and long path. "
                            f'Skipped: "{str(transform_long_name)}" (UUID: {transform_uuid}).'
                        )
                        continue
                # Checks
                if not cmds.objExists(transform_long_name):
                    logger.warning(
                        f'Curve object does not exist, unable to read shape data. Skipped "{transform_long_name}".'
                    )
                    continue
                target_shapes = cmds.listRelatives(transform_long_name, shapes=True, fullPath=True) or []
                shapes_data = _shape_data.get("shapes")
                if len(target_shapes) != len(shapes_data):
                    logger.warning(
                        f"The number of shapes differs from the stored one, unable to update: {transform_long_name}"
                    )
                    continue

                # Update curve object shapes
                for i, shape_data in enumerate(shapes_data):
                    curve_shape = core_curve.CurveShape(read_curve_shape_data=shape_data)
                    curve_shape.build(replace_crv=target_shapes[i])

    def write_shapes(self, transforms, clear_target_dir=True):
        """
        Write the shapes for the provided elements.
        Args:
            transforms (list, str): Transforms carrying curve shapes inside them (nurbs or bezier)
                              Strings are automatically converted to a list with a single item.
            clear_target_dir (bool, optional): If True, all files with the influence extension found in the target
                                               directory get purged/deleted before writing new ones.
        """
        # Get write directory
        _parsed_path = self.parse_path(path=self.shapes_dir)
        _parsed_path = core_io.make_directory(_parsed_path)
        if not os.path.exists(_parsed_path):
            logger.warning(f'Unable to write the shapes. Invalid path: "{str(_parsed_path)}".')
            return
        # Clear existing
        if clear_target_dir:
            core_io.delete_dir_files(directory_path=_parsed_path, file_extension=self._file_format)

        # Check occurrences
        from collections import Counter

        _short_names_list = [core_naming.get_short_name(transform) for transform in transforms]
        _names_occurrences = Counter(_short_names_list)
        _not_unique = [t_name for t_name, t_value in _names_occurrences.items() if t_value > 1]
        if _not_unique:
            logger.warning(f"Found multiple occurrences of the following provided transformations: {str(_not_unique)}.")
            return

        # Write Shapes
        shapes_written = []
        for transform in transforms:
            if not cmds.objExists(transform):
                logger.warning(f"Cannot write missing object: {transform}.")
                continue

            # Checks
            transform_uuid = None
            if cmds.attributeQuery(tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID, node=transform, ex=True):
                transform_uuid = cmds.getAttr(f"{transform}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}")

            target_shapes = cmds.listRelatives(transform, shapes=True, fullPath=True) or []
            if not target_shapes:
                logger.debug(f"Skipped driver without shapes: {transform}.")
                continue

            _curve_obj = core_curve.Curve(read_existing_curve=transform)
            shapes_dict = _curve_obj.get_data_as_dict()
            shapes_dict["uuid"] = transform_uuid

            transform_short_name = core_naming.get_short_name(transform)
            _file_path = os.path.join(_parsed_path, f"{transform_short_name}{self._file_format}")

            # If already present, make it modifiable
            if _file_path and os.path.exists(_file_path):
                core_io.set_file_permission_modifiable(_file_path)

            core_io.write_json(path=_file_path, data=shapes_dict)
            shapes_written.append(transform_short_name)
        logger.info(f'The following shapes: {str(shapes_written)}\nhave been written to: "{_parsed_path}"')

    def write_shapes_from_selection(self, clear_target_dir=True):
        """
        Same as "write_shapes" but automatically populates the transforms parameter with selection.
        Args:
            clear_target_dir (bool, optional): If True, all shapes files found in the target
                                               directory get purged/deleted before writing new ones.
        """
        selection = cmds.ls(selection=True, long=True) or []
        if not selection:
            logger.warning(f"Nothing selected. Select controls and try again.")
            return
        self.write_shapes(transforms=selection, clear_target_dir=clear_target_dir)

    def write_project_shapes(self, clear_target_dir=True):
        """
        Same as "write_shapes" but automatically populates the transforms parameter with the project controls.
        Args:
            clear_target_dir (bool, optional): If True, all shapes files found in the target
                                               directory get purged/deleted before writing new ones.
        """
        if not self._project:
            logger.warning(f"The module is not associated with a project. Add it to a project first.")
            return
        controls = self._project.get_built_drivers()
        if not controls:
            logger.warning(f"No controls related to the project found in the scene. Build the rig first.")
            return
        controls = [ctrl.get_long_name() for ctrl in controls]
        self.write_shapes(transforms=controls, clear_target_dir=clear_target_dir)

    # ------------------------------------------- Extra Module Setters ------------------------------------------
    def set_shapes_dir(self, shapes_dir):
        """
        Sets the directory path used to import shapes files.
        Args:
            shapes_dir (str): A file path to be used when writing or reading a list of shapes.
        """
        if shapes_dir is None:
            self.shapes_dir = ""
        if not isinstance(shapes_dir, str):
            logger.warning("Unable to set the shapes path. Invalid data type was provided.")
            return
        self.shapes_dir = shapes_dir


class ModuleNotes(tools_rig_frm.ModuleGeneric):
    __version__ = "1.1.0"
    icon = ui_res_lib.Icon.rigger_module_notes
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Notes", prefix=None, suffix=None):
        """
        Initialize the ModuleNotes instance.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None
        self.set_extra_callable_function(self.show_warning, order=tools_rig_frm.CodeData.Order.post_build)
        self.font_size = 14
        self.notes = ""  # Reverted to a standard string for safe serialization
        self.show_warning = False

    def show_warning(self):
        """
        Shows a warning popup with the decoded notes content.
        """
        if self.show_warning:
            import gt.ui.qt_import as ui_qt
            import gt.utils.hypertext as utils_html

            msg_box = ui_qt.QtWidgets.QMessageBox()
            msg_box.setIcon(ui_qt.QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle(f"{self.get_name()}")
            msg_box.setText(utils_html.extract_text_from_html(self.get_notes()))
            msg_box.setStandardButtons(ui_qt.QtWidgets.QMessageBox.Ok)
            msg_box.exec_()

    def set_notes(self, new_notes):
        """
        Encodes notes into a Base64 string for safe serialization.
        This process preserves unicode characters like emojis.

        Args:
            new_notes (str): Updated notes (as a string) to be stored in this module.
        """
        if not isinstance(new_notes, str):
            self.notes = ""
            return
        # The process: String -> UTF-8 Bytes -> Base64 Bytes -> ASCII String
        utf8_bytes = new_notes.encode("utf-8")
        base64_bytes = base64.b64encode(utf8_bytes)
        self.notes = base64_bytes.decode("ascii")

    def get_notes(self):
        """
        Decodes notes from Base64 to retrieve the original string.
        This includes backward compatibility for any old, non-encoded data.

        Returns:
            str: The original notes, decoded and ready for display.
        """
        if not self.notes or not isinstance(self.notes, str):
            return ""
        try:
            # The reverse process: ASCII String -> ASCII Bytes -> UTF-8 Bytes -> String
            ascii_bytes = self.notes.encode("ascii")
            utf8_bytes = base64.b64decode(ascii_bytes)
            return utf8_bytes.decode("utf-8")
        except (binascii.Error, UnicodeEncodeError):
            # If encoding to ASCII or decoding from Base64 fails, it's old data.
            # We return it directly for backward compatibility.
            return self.notes


class ModuleThumbnailCapture(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_thumbnail_capture
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Thumbnail Capture"):
        """
        Initialize the ModuleThumbnailCapture instance.

        Args:
            name (str): Name of the module instance.
        """
        super().__init__(name=name)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.file_path = r"{project-dir}/media/_{project-name}_thumbnail.jpg"
        self.file_extension = "jpg"
        self.width = 1024
        self.height = 1024
        self.current_frame = False  # When active, "self.frame" is ignored.
        self.frame = 1
        self.default_material = False
        self.x_ray = False
        self.wireframe_on_shaded = False
        self.hide_curves = False
        self.use_camera_data = True
        self.camera_data = {}
        self.set_extra_callable_function(self.capture_thumbnail, order=tools_rig_frm.CodeData.Order.post_build)

    def capture_thumbnail(self):
        """
        Saves the viewport image as a thumbnail to the specified path
        """
        if not self.file_path:
            logger.warning("File path empty. Please first set a file path.")
            return

        _parsed_path = self.parse_path(path=self.file_path)
        self.warn_if_path_outside_project(_parsed_path)

        # If already present, make it modifiable
        if _parsed_path and os.path.exists(_parsed_path):
            core_io.set_file_permission_modifiable(_parsed_path)

        directory = os.path.dirname(_parsed_path)
        directory = core_io.make_directory(directory)
        if not os.path.exists(directory):
            logger.warning(f'Unable to store thumbnail. Directory unavailable: "{str(_parsed_path)}".')
            return
        file_name = os.path.basename(_parsed_path)
        name, extension = os.path.splitext(file_name)

        _frame = self.frame
        if self.current_frame:
            _frame = None

        # Panel Setup ---------------------------------------------------------------
        _panel = None
        try:  # Get the active model panel
            _panel = cmds.getPanel(withFocus=True)
            if not cmds.getPanel(typeOf=_panel) == "modelPanel":
                # Try to find a visible model panel if focus is not on one
                for p in cmds.getPanel(type="modelPanel"):
                    if cmds.modelEditor(p, query=True, visible=True):
                        _panel = p
                        break
                else:
                    cmds.warning("No active model panel found.")
        except Exception as e:
            logger.debug(f"Unable to find a model panel. Issue: {e}")

        # Use Default Material
        _current_default_mat = None
        if _panel and self.default_material:
            _current_default_mat = cmds.modelEditor(_panel, query=True, useDefaultMaterial=True)
            if not _current_default_mat:
                cmds.modelEditor(_panel, edit=True, useDefaultMaterial=True)
        # X-Ray
        _current_x_ray = None
        if _panel and self.x_ray:
            _current_x_ray = cmds.modelEditor(_panel, query=True, xray=True)
            if not _current_x_ray:
                cmds.modelEditor(_panel, edit=True, xray=True)
        # Wireframe on Shaded
        _current_wireframe_on_shaded = None
        if _panel and self.wireframe_on_shaded:
            _current_wireframe_on_shaded = cmds.modelEditor(_panel, query=True, wireframeOnShaded=True)
            if not _current_wireframe_on_shaded:
                cmds.modelEditor(_panel, edit=True, wireframeOnShaded=True)
        # Hide NURBS Curves
        _current_hide_nurbs_crv = None
        if _panel and self.hide_curves:
            _current_hide_nurbs_crv = cmds.modelEditor(_panel, query=True, nurbsCurves=True)
            if _current_hide_nurbs_crv:
                cmds.modelEditor(_panel, edit=True, nurbsCurves=False)
        # Current Time
        _current_time = cmds.currentTime(query=True)

        # Camera Data --------------------------------------------------------------
        _current_camera_data = None
        if self.camera_data and self.use_camera_data:
            try:
                import gt.core.camera as core_cam

                _current_camera_data = core_cam.get_camera_data()  # By default, it gets the persp
                core_cam.apply_camera_data(data=self.camera_data)
            except Exception as e:
                logger.warning(f"Unable to apply camera data. Issue: {e}")

        # Capture Image ------------------------------------------------------------
        cmds.select(clear=True)
        image_path = core_playblast.render_viewport_snapshot(
            file_name=name,
            target_dir=directory,
            image_format=self.file_extension,
            width=self.width,
            height=self.height,
            frame=_frame,
        )
        if image_path:
            logger.info(f"Thumbnail has been saved: {image_path}")
        else:
            logger.warning(f"Unable to save thumbnail file.")

        # Restore Original States ---------------------------------------------------
        cmds.currentTime(_current_time)
        if _panel and _current_default_mat is not None:
            try:
                cmds.modelEditor(_panel, edit=True, useDefaultMaterial=_current_default_mat)
            except Exception as e:
                logger.debug(f'Unable to restore panel "Use default material" value. Issue: {e}')
        if _panel and _current_x_ray is not None:
            try:
                cmds.modelEditor(_panel, edit=True, xray=_current_x_ray)
            except Exception as e:
                logger.debug(f'Unable to restore panel "X-Ray" value. Issue: {e}')
        if _panel and _current_wireframe_on_shaded is not None:
            try:
                cmds.modelEditor(_panel, edit=True, wireframeOnShaded=_current_wireframe_on_shaded)
            except Exception as e:
                logger.debug(f'Unable to restore panel "Wireframe on Shaded" value. Issue: {e}')
        if _panel and _current_hide_nurbs_crv is not None:
            try:
                cmds.modelEditor(_panel, edit=True, nurbsCurves=_current_hide_nurbs_crv)
            except Exception as e:
                logger.debug(f'Unable to restore panel "NURBS Curves" visibility value. Issue: {e}')
        if _current_camera_data is not None:
            try:
                import gt.core.camera as core_cam

                core_cam.apply_camera_data(data=_current_camera_data)
            except Exception as e:
                logger.warning(f"Unable to restore initial camera data. Issue: {e}")

        return True


class ModulePlayblastCapture(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_playblast_capture
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Playblast Capture"):
        """
        Initialize the ModulePlayblastCapture instance.

        Args:
            name (str): Name of the module instance.
        """
        super().__init__(name=name)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.file_path = r"{project-dir}/media/{project-name}_playblast.ext"
        self.video_format = "qt"
        self.width = 1024
        self.height = 1024
        self.start_frame = 1
        self.end_frame = 24
        self.show_ornaments = False
        self.default_material = False
        self.x_ray = False
        self.wireframe_on_shaded = False
        self.hide_curves = True
        self.use_camera_data = True
        self.camera_data = {}
        self.set_extra_callable_function(self.capture_playblast, order=tools_rig_frm.CodeData.Order.post_build)

    def capture_playblast(self):
        """
        Saves the viewport playblast to the specified path
        """
        if not self.file_path:
            logger.warning("File path empty. Please first set a file path.")
            return

        _parsed_path = self.parse_path(path=self.file_path)
        self.warn_if_path_outside_project(_parsed_path)

        # If already present, make it modifiable
        if _parsed_path and os.path.exists(_parsed_path):
            core_io.set_file_permission_modifiable(_parsed_path)

        directory = os.path.dirname(_parsed_path)
        directory = core_io.make_directory(directory)
        if not os.path.exists(directory):
            logger.warning(f'Unable to store playblast. Directory unavailable: "{str(_parsed_path)}".')
            return
        file_name = os.path.basename(_parsed_path)
        name, extension = os.path.splitext(file_name)

        # If already present, make it modifiable
        if _parsed_path:
            # Search for all files with same base name and any extension
            for match in pathlib.Path(directory).glob(f"{name}.*"):
                if match.exists():
                    core_io.set_file_permission_modifiable(str(match))

        # Panel Setup ---------------------------------------------------------------
        _panel = None
        try:  # Get the active model panel
            _panel = cmds.getPanel(withFocus=True)
            if not cmds.getPanel(typeOf=_panel) == "modelPanel":
                # Try to find a visible model panel if focus is not on one
                for p in cmds.getPanel(type="modelPanel"):
                    if cmds.modelEditor(p, query=True, visible=True):
                        _panel = p
                        break
                else:
                    cmds.warning("No active model panel found.")
        except Exception as e:
            logger.debug(f"Unable to find a model panel. Issue: {e}")

        # Use Default Material
        _current_default_mat = None
        if _panel and self.default_material:
            _current_default_mat = cmds.modelEditor(_panel, query=True, useDefaultMaterial=True)
            if not _current_default_mat:
                cmds.modelEditor(_panel, edit=True, useDefaultMaterial=True)
        # X-Ray
        _current_x_ray = None
        if _panel and self.x_ray:
            _current_x_ray = cmds.modelEditor(_panel, query=True, xray=True)
            if not _current_x_ray:
                cmds.modelEditor(_panel, edit=True, xray=True)
        # Wireframe on Shaded
        _current_wireframe_on_shaded = None
        if _panel and self.wireframe_on_shaded:
            _current_wireframe_on_shaded = cmds.modelEditor(_panel, query=True, wireframeOnShaded=True)
            if not _current_wireframe_on_shaded:
                cmds.modelEditor(_panel, edit=True, wireframeOnShaded=True)
        # Hide NURBS Curves
        _current_hide_nurbs_crv = None
        if _panel and self.hide_curves:
            _current_hide_nurbs_crv = cmds.modelEditor(_panel, query=True, nurbsCurves=True)
            if _current_hide_nurbs_crv:
                cmds.modelEditor(_panel, edit=True, nurbsCurves=False)
        # Current Time
        _current_time = cmds.currentTime(query=True)

        # Camera Data --------------------------------------------------------------
        _current_camera_data = None
        if self.camera_data and self.use_camera_data:
            try:
                import gt.core.camera as core_cam

                _current_camera_data = core_cam.get_camera_data()  # By default, it gets the persp
                core_cam.apply_camera_data(data=self.camera_data)
            except Exception as e:
                logger.warning(f"Unable to apply camera data. Issue: {e}")

        # Render Playblast ----------------------------------------------------------
        cmds.select(clear=True)

        render_path = core_playblast.render_viewport_playblast(
            file_name=name,
            target_dir=directory,
            start_frame=self.start_frame,
            end_frame=self.end_frame,
            width=self.width,
            height=self.height,
            video_format=self.video_format,
            show_ornaments=self.show_ornaments,
        )
        if render_path:
            logger.info(f"Playblast has been saved: {render_path}")
        else:
            logger.warning(f"Unable to save playblast file.")

        # Restore Original States ---------------------------------------------------
        cmds.currentTime(_current_time)
        if _panel and _current_default_mat is not None:
            try:
                cmds.modelEditor(_panel, edit=True, useDefaultMaterial=_current_default_mat)
            except Exception as e:
                logger.debug(f'Unable to restore panel "Use default material" value. Issue: {e}')
        if _panel and _current_x_ray is not None:
            try:
                cmds.modelEditor(_panel, edit=True, xray=_current_x_ray)
            except Exception as e:
                logger.debug(f'Unable to restore panel "X-Ray" value. Issue: {e}')
        if _panel and _current_wireframe_on_shaded is not None:
            try:
                cmds.modelEditor(_panel, edit=True, wireframeOnShaded=_current_wireframe_on_shaded)
            except Exception as e:
                logger.debug(f'Unable to restore panel "Wireframe on Shaded" value. Issue: {e}')
        if _panel and _current_hide_nurbs_crv is not None:
            try:
                cmds.modelEditor(_panel, edit=True, nurbsCurves=_current_hide_nurbs_crv)
            except Exception as e:
                logger.debug(f'Unable to restore panel "NURBS Curves" visibility value. Issue: {e}')
        if _current_camera_data is not None:
            try:
                import gt.core.camera as core_cam

                core_cam.apply_camera_data(data=_current_camera_data)
            except Exception as e:
                logger.warning(f"Unable to restore initial camera data. Issue: {e}")

        return True


class ModuleCameraSetup(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_camera_setup
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Camera Setup"):
        """
        Initialize the ModulePlayblastCapture instance.

        Args:
            name (str): Name of the module instance.
        """
        super().__init__(name=name)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.camera_name = "persp"
        self.view_through_camera = True
        self.default_material = False
        self.x_ray = False
        self.wireframe_on_shaded = False
        self.use_camera_data = True
        self.camera_data = {}
        self.set_extra_callable_function(self.set_camera_data, order=tools_rig_frm.CodeData.Order.post_build)

    def set_camera_data(self):
        """
        Sets the basic properties of the specified camera. Default is "persp" (perspective camera)
        """
        # Panel Setup ---------------------------------------------------------------
        _panel = None
        try:  # Get the active model panel
            _panel = cmds.getPanel(withFocus=True)
            if not cmds.getPanel(typeOf=_panel) == "modelPanel":
                # Try to find a visible model panel if focus is not on one
                for p in cmds.getPanel(type="modelPanel"):
                    if cmds.modelEditor(p, query=True, visible=True):
                        _panel = p
                        break
                else:
                    cmds.warning("No active model panel found.")
        except Exception as e:
            logger.debug(f"Unable to find a model panel. Issue: {e}")

        # Camera Data --------------------------------------------------------------
        _current_camera_data = None
        if not self.camera_name:
            logger.warning(f"Unable to set camera data. No camera name provided.")
            return
        if not cmds.objExists(self.camera_name):
            logger.warning(f'Unable to set camera data. Missing provided camera: "{self.camera_name}".')
            return

        if self.camera_data and self.use_camera_data:
            try:
                import gt.core.camera as core_cam

                core_cam.apply_camera_data(data=self.camera_data, camera_name=self.camera_name)
            except Exception as e:
                logger.warning(f"Unable to apply camera data. Issue: {e}")

        # Viewport Setup ------------------------------------------------------------
        # Use Default Material
        _current_default_mat = None
        if _panel and self.default_material:
            _current_default_mat = cmds.modelEditor(_panel, query=True, useDefaultMaterial=True)
            if not _current_default_mat:
                cmds.modelEditor(_panel, edit=True, useDefaultMaterial=True)
        # X-Ray
        _current_x_ray = None
        if _panel and self.x_ray:
            _current_x_ray = cmds.modelEditor(_panel, query=True, xray=True)
            if not _current_x_ray:
                cmds.modelEditor(_panel, edit=True, xray=True)
        # Wireframe on Shaded
        _current_wireframe_on_shaded = None
        if _panel and self.wireframe_on_shaded:
            _current_wireframe_on_shaded = cmds.modelEditor(_panel, query=True, wireframeOnShaded=True)
            if not _current_wireframe_on_shaded:
                cmds.modelEditor(_panel, edit=True, wireframeOnShaded=True)
        # View Through Camera
        if self.view_through_camera:
            if not cmds.objectType(self.camera_name, isType="camera"):
                # Check if it's a transform with a shape child that is a camera
                shapes = cmds.listRelatives(self.camera_name, shapes=True) or []
                if not any(cmds.objectType(s, isType="camera") for s in shapes):
                    cmds.warning(f"'{self.camera_name}' is not a camera or doesn't have a camera shape.")
                    return
                # Use the shape instead
                camera_shape = next(s for s in shapes if cmds.objectType(s, isType="camera"))
            else:
                camera_shape = self.camera_name
            cmds.modelEditor(_panel, edit=True, camera=camera_shape)


class ModuleROMLoader(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_rom_loader
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="ROM Loader"):
        """
        Initialize the ModuleROMLoader instance.

        Args:
            name (str): Name of the module instance.
        """
        super().__init__(name=name)
        self.orientation = None  # Changed to None so it doesn't get serialized.
        self.target_file_path = r"{project-dir}/{project-name}_rig.ma"
        self.retarget_definition = "male_poses_01"
        self.comparison_offset = True
        self.comparison_visibility = False

        self.set_extra_callable_function(self.retarget_range_of_motion, order=tools_rig_frm.CodeData.Order.post_build)

    def retarget_range_of_motion(self):
        """
        Loads a profile for a range of motion according to the provided paths and profile.
        """
        import gt.tools.retargeter.retargeter_constants as tools_rt_const
        import gt.tools.retargeter.retargeter_utils as tool_rt_utils

        # Resolve Target File Path --------------------------------------------------
        if not self.target_file_path:
            logger.warning("File path empty. Please first set a file path.")
            return
        _parsed_path = self.parse_path(path=self.target_file_path)
        if not _parsed_path or not os.path.exists(_parsed_path):
            logger.warning(f"Unable to retarget ROM. Missing target file: {_parsed_path}")
            return

        # Retarget ------------------------------------------------------------------
        _definition = tool_rt_utils.get_configured_definition_from_directory(
            directory_path=tools_rt_const.RetargeterConstants.DEFAULT_ROM_DATA_FOLDER,
            target_definition=self.retarget_definition,
            target_rig=_parsed_path,
        )
        if not _definition:
            return
        _definition.retarget()

        # Comparison Preferences ----------------------------------------------------
        if cmds.objExists("source:offset"):
            cmds.setAttr("source:offset.visibility", self.comparison_visibility)  # Comparison Overall Visibility
            cmds.setAttr("source:offset.bWeight", self.comparison_offset)  # A+B Comparison offset


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)
    from gt.tools.auto_rigger.rig_framework import RigProject, ModuleGeneric

    # Create Test Modules ---------------------------------------------------------------------------------
    a_generic_module = ModuleGeneric()
    a_new_scene_module = ModuleNewScene()
    an_import_file_module = ModuleImportFile()
    a_skin_weights_module = ModuleSkinWeights()
    an_export_sk_module = ModuleExportSkeletalMesh()
    a_python_module = ModulePython()
    a_save_scene_module = ModuleSaveScene()

    # Test File Paths -------------------------------------------------------------------------------------
    import gt.tests.test_auto_rigger as test_auto_rigger
    import inspect
    import os

    module_path = inspect.getfile(test_auto_rigger)
    module_dir = os.path.dirname(module_path)
    a_cube_obj = os.path.join(module_dir, "data", "cylinder_project", "cylinder.obj")
    a_cube_fbx = os.path.join(module_dir, "data", "cylinder_project", "cylinder.fbx")

    # Configure Modules -----------------------------------------------------------------------------------
    p1 = a_generic_module.add_new_proxy()
    p2 = a_generic_module.add_new_proxy()
    p3 = a_generic_module.add_new_proxy()
    p1.set_name("first")
    p2.set_name("second")
    p3.set_name("third")
    p2.set_initial_position(y=15)
    p3.set_initial_position(y=30)
    p2.set_parent_uuid(p1.get_uuid())
    p3.set_parent_uuid(p2.get_uuid())
    p1.set_locator_scale(6)
    p2.set_locator_scale(5)
    p3.set_locator_scale(4)
    # New Scene
    scene_options = {
        "frame_rate": "30fps",
        "multi_sample": True,
        "multi_sample_count": 8,
        "persp_clip_plane_near": 0.1,
        "persp_clip_plane_far": 10000.0,
        "display_textures": True,
        "view_fit_all": True,
    }
    a_new_scene_module.set_scene_options(scene_options)
    # Import File
    an_import_file_module.set_file_path(file_path=a_cube_obj)
    an_import_file_module.set_file_path(file_path=a_cube_fbx)
    an_import_file_module.set_file_path(file_path=r"{tests-data-dir}\cylinder_project\geo\cylinder.obj")
    an_import_file_module.set_transforms_parent(transforms_parent="geometry")
    # Skin Weights
    a_skin_weights_module.set_influences_dir(r"{tests-data-dir}\cylinder_project\influences")
    a_skin_weights_module.set_weights_dir(r"{tests-data-dir}\cylinder_project\weights")
    # Export Skeletal Mesh
    an_export_sk_module.set_export_dir(r"{tests-data-dir}\cylinder_project\skeletal_mesh")
    an_export_sk_module.set_export_filename("test_skeletal_mesh")
    # Python Module
    a_python_module.set_execution_code('print("hello world!")')
    # Save Scene
    a_save_scene_module.set_file_path(file_path=r"{tests-data-dir}\Rig\cylinder_rig.ma")

    # Create Project and Build ----------------------------------------------------------------------------
    a_project = RigProject()
    a_project.add_to_modules(a_new_scene_module)
    # a_project.add_to_modules(a_generic_module)
    a_project.add_to_modules(an_import_file_module)
    # a_project.add_to_modules(a_skin_weights_module)
    # a_project.add_to_modules(an_export_sk_module)
    # a_project.add_to_modules(a_python_module)
    # a_project.add_to_modules(a_save_scene_module)
    a_project.set_project_dir_path(r"{desktop-dir}\test_folder")
    # print(a_project.get_project_dir_path(parse_vars=True))  # Absolute path to Desktop\test_folder
    # a_project.add_to_modules(a_generic_module)  # Should be the only thing in the scene after building

    # # Creates new scene after building resulting in empty scene
    a_project.build_proxy()
    a_project.build_rig()

    # # Module Utilities
    # a_skin_weights_module.set_parent_project(a_project)
    # a_skin_weights_module.write_influences_from_selection()
    # a_skin_weights_module._read_influences()
    # a_skin_weights_module.write_weights_from_selection()
    # a_skin_weights_module._read_weights()

    # -----------------------------------------------------------------------------------------------------
    # # Test CodeData Saving Order Capabilities (It should be able to transfer the "post_build" change done above)
    # a_project_as_dict = a_project.get_project_as_dict()
    # a_project_2 = RigProject()
    # a_project_2.read_data_from_dict(a_project_as_dict)
    # a_project_2.build_proxy()
    # a_project_2.build_rig()

    # -----------------------------------------------------------------------------------------------------
    # # Test CodeData String Execution
    # # THIS IS JUST AN EXAMPLE. WE WOULDN'T"T OVERWRITE THE CODE DATA LIKE THAT AS WE CAN USE
    # # "set_extra_callable_function()" to achieve the same thing through python.
    # # THE STRING EXECUTION IS FOR USER INPUT AS CODE IN FUTURE MODULES
    # a_modified_new_scene_module = ModuleNewScene()  # This doesn't create a new scene, but print hello world instead
    # code_data = tools_rig_frm.CodeData()
    # code_data.set_order(tools_rig_frm.CodeData.Order.pre_proxy)
    # code_data.set_execution_code(code="print('hello world')")
    # a_modified_new_scene_module.set_code_data(code_data)
    #
    # a_project_3 = RigProject()
    # a_project_3.add_to_modules(a_modified_new_scene_module)
    # a_project_3.build_proxy()
    # a_project_3.build_rig()

    # Frame all
    cmds.viewFit(all=True)
