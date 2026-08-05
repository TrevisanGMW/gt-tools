"""
Auto Rigger ngSkinTools2 Skin Weights Module
"""

import logging
import os

import maya.cmds as cmds

import gt.core.io as core_io
import gt.core.logger as core_log
import gt.core.naming as core_naming
import gt.core.skin as core_skin
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.ui.resource_library as ui_res_lib
import gt.utils.ngskin as utils_ng


logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, propagate=False)
logger.setLevel(logging.INFO)


class ModuleNGSkinWeights(tools_rig_frm.ModuleGeneric):
    """Imports and exports skinning layers through the ngSkinTools2 API."""

    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_ngskin_weights
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="ngSkinTools Weights", prefix=None, suffix=None):
        """Initializes the ngSkinTools2 skin weights module.

        Args:
            name (str): Name of the module instance.
            prefix (str, optional): Prefix string.
            suffix (str, optional): Suffix string.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.orientation = None
        self.weights_dir = r"{project-dir}\ngskin_weights"
        self.vertex_transfer_mode = utils_ng.VertexTransferMode.CLOSEST_POINT
        self.keep_existing_layers = False
        self.delete_custom_nodes_after_import = True
        self.bind_missing_targets = True
        self.clear_target_dir = False
        self.use_name_matching = True
        self.use_label_matching = True
        self.use_distance_matching = True
        self.use_dg_link_matching = True
        self.influence_distance_threshold = 0.001
        self.influence_name_mapping = {}
        self.target_name_mapping = {}
        self._file_format = ".json"

        self.set_extra_callable_function(self.read_weights, order=tools_rig_frm.CodeData.Order.post_build)

    def _get_mapping_settings(self):
        """Builds influence mapping settings from module preferences.

        Returns:
            InfluenceMappingSettings: Current influence mapping settings.
        """
        return utils_ng.InfluenceMappingSettings(
            use_name_matching=self.use_name_matching,
            use_label_matching=self.use_label_matching,
            use_distance_matching=self.use_distance_matching,
            use_dg_link_matching=self.use_dg_link_matching,
            distance_threshold=self.influence_distance_threshold,
        )

    def _get_target_from_file(self, file_path):
        """Resolves a target mesh from a weight file name.

        Args:
            file_path (str): ngSkinTools2 weight file path.

        Returns:
            str: Mapped or inferred target mesh name.
        """
        source_name = os.path.splitext(os.path.basename(file_path))[0]
        return self.target_name_mapping.get(source_name, source_name)

    def _get_mapped_influences(self, file_path):
        """Gets mapped influence names stored in an ngSkinTools2 file.

        Args:
            file_path (str): ngSkinTools2 JSON file path.

        Returns:
            list[str]: Destination influence names.
        """
        influences = utils_ng.get_influences_from_file(file_path)
        return [utils_ng.resolve_name_mapping(name, self.influence_name_mapping) for name in influences]

    def _bind_target_from_file(self, target, file_path):
        """Creates a required skinCluster from influence metadata when missing.

        Args:
            target (str): Target polygon mesh.
            file_path (str): ngSkinTools2 JSON file path.

        Returns:
            bool: True when the target is already bound or binding succeeds.
        """
        if utils_ng.get_related_skin_cluster(target):
            return True
        if not self.bind_missing_targets:
            logger.warning(f'Unable to import ngSkinTools2 weights. Target is not bound: "{target}".')
            return False
        influences = self._get_mapped_influences(file_path)
        missing_influences = [influence for influence in influences if not cmds.objExists(influence)]
        if missing_influences:
            logger.warning(
                f'Unable to bind "{target}". Missing mapped influences: {", ".join(missing_influences)}'
            )
            return False
        skin_clusters = core_skin.bind_skin(joints=influences, objects=target)
        return bool(skin_clusters)

    def read_weights(self):
        """Imports every ngSkinTools2 JSON file from the configured directory.

        Returns:
            list[str]: Targets that imported successfully.
        """
        parsed_path = self.parse_path(path=self.weights_dir)
        if not parsed_path or not os.path.isdir(parsed_path):
            logger.warning(f'Unable to import ngSkinTools2 weights from missing directory: "{parsed_path}".')
            return []
        self.warn_if_path_outside_project(parsed_path)
        imported_targets = []
        for filename in sorted(os.listdir(parsed_path)):
            if not filename.lower().endswith(self._file_format):
                continue
            file_path = os.path.join(parsed_path, filename)
            target = self._get_target_from_file(file_path)
            if not cmds.objExists(target):
                logger.warning(f'Unable to import ngSkinTools2 weights on missing target: "{target}".')
                continue
            if not self._bind_target_from_file(target, file_path):
                continue
            try:
                imported = utils_ng.import_weights(
                    target=target,
                    file_path=file_path,
                    vertex_transfer_mode=self.vertex_transfer_mode,
                    influence_mapping_settings=self._get_mapping_settings(),
                    influence_name_mapping=self.influence_name_mapping,
                    keep_existing_layers=self.keep_existing_layers,
                )
                if imported:
                    imported_targets.append(target)
                    logger.info(f'ngSkinTools2 weights imported from: "{file_path}"')
            except Exception as exception:
                logger.exception(f'Unable to import ngSkinTools2 weights from "{file_path}": {exception}')

        if imported_targets and self.delete_custom_nodes_after_import:
            utils_ng.remove_custom_nodes(imported_targets)
            logger.info("Removed ngSkinTools2 custom nodes after importing weights.")
        return imported_targets

    def write_weights(self, skinned_meshes, clear_target_dir=True):
        """Exports ngSkinTools2 layer data for the supplied meshes.

        Args:
            skinned_meshes (list[str]): Skinned polygon meshes to export.
            clear_target_dir (bool): Whether existing JSON files are removed first.

        Returns:
            list[str]: Exported file paths.
        """
        parsed_path = core_io.make_directory(self.parse_path(path=self.weights_dir))
        if not parsed_path or not os.path.isdir(parsed_path):
            logger.warning(f'Unable to write ngSkinTools2 weights to invalid path: "{parsed_path}".')
            return []
        if clear_target_dir:
            core_io.delete_dir_files(directory_path=parsed_path, file_extension=self._file_format)

        exported_files = []
        for mesh in skinned_meshes:
            if not cmds.objExists(mesh):
                logger.warning(f'Unable to export ngSkinTools2 weights for missing mesh: "{mesh}".')
                continue
            if not utils_ng.get_related_skin_cluster(mesh):
                logger.warning(f'Unable to export ngSkinTools2 weights for unbound mesh: "{mesh}".')
                continue
            short_name = core_naming.get_short_name(mesh)
            short_name = short_name.replace("|", "_").replace(":", "_")
            file_path = os.path.join(parsed_path, f"{short_name}{self._file_format}")
            if os.path.isfile(file_path):
                core_io.set_file_permission_modifiable(file_path)
            try:
                layers = utils_ng.initialize_layers(mesh)
                if not layers.list():
                    layers.add("Base Weights")
                exported_files.append(utils_ng.export_weights(mesh, file_path))
                logger.info(f'ngSkinTools2 weights written to: "{file_path}"')
            except Exception as exception:
                logger.exception(f'Unable to export ngSkinTools2 weights for "{mesh}": {exception}')
        return exported_files

    def write_weights_from_selection(self, clear_target_dir=True):
        """Exports ngSkinTools2 weights for selected polygon transforms.

        Args:
            clear_target_dir (bool): Whether existing JSON files are removed first.

        Returns:
            list[str]: Exported file paths.
        """
        selection = cmds.ls(selection=True, long=True, objectsOnly=True) or []
        if not selection:
            logger.warning("Nothing selected. Select skinned meshes and try again.")
            return []
        return self.write_weights(selection, clear_target_dir=clear_target_dir)

    def set_weights_dir(self, weights_dir):
        """Sets the directory used for ngSkinTools2 weight files.

        Args:
            weights_dir (str): Directory path or an empty value.
        """
        if weights_dir is None:
            weights_dir = ""
        if not isinstance(weights_dir, str):
            logger.warning("Unable to set ngSkinTools2 weights path. Expected a string.")
            return
        self.weights_dir = weights_dir

    def set_vertex_transfer_mode(self, vertex_transfer_mode):
        """Sets the vertex transfer mode.

        Args:
            vertex_transfer_mode (str): One of VertexTransferMode values.
        """
        if vertex_transfer_mode not in utils_ng.VertexTransferMode.get_values():
            logger.warning(f"Unable to set unsupported vertex transfer mode: {vertex_transfer_mode}")
            return
        self.vertex_transfer_mode = vertex_transfer_mode
