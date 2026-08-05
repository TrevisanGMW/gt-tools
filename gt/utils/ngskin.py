"""
ngSkinTools2 Utilities

Import Line:
    import gt.utils.ngskin as utils_ng

The ngSkinTools2 package and Maya plug-in are loaded only when an operation is
executed. This keeps the module importable in environments where ngSkinTools2
is not installed.
"""

import json
import logging
import os

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.INFO)


class VertexTransferMode:
    """Constants describing how source vertices are matched to a target."""

    CLOSEST_POINT = "closestPoint"
    UV_SPACE = "uvSpace"
    VERTEX_ID = "vertexId"

    @classmethod
    def get_values(cls):
        """Gets all supported ngSkinTools2 vertex transfer modes.

        Returns:
            list[str]: Supported transfer mode values.
        """
        return [cls.CLOSEST_POINT, cls.UV_SPACE, cls.VERTEX_ID]


class FileFormat:
    """Constants describing supported ngSkinTools2 weight file formats."""

    JSON = "json"
    COMPRESSED_JSON = "compressed json"

    @classmethod
    def get_values(cls):
        """Gets all supported file formats.

        Returns:
            list[str]: Supported file format values.
        """
        return [cls.JSON, cls.COMPRESSED_JSON]


class PaintMode:
    """Constants describing ngSkinTools2 flood paint operations."""

    REPLACE = "replace"
    ADD = "add"
    SCALE = "scale"
    SMOOTH = "smooth"
    SHARPEN = "sharpen"

    @classmethod
    def get_values(cls):
        """Gets all supported flood paint modes.

        Returns:
            list[str]: Supported paint modes.
        """
        return [cls.REPLACE, cls.ADD, cls.SCALE, cls.SMOOTH, cls.SHARPEN]


class MirrorDirection:
    """Constants describing layer mirror effect directions."""

    POSITIVE_TO_NEGATIVE = "positiveToNegative"
    NEGATIVE_TO_POSITIVE = "negativeToPositive"
    FLIP = "flip"

    @classmethod
    def get_values(cls):
        """Gets all supported mirror directions.

        Returns:
            list[str]: Supported mirror direction names.
        """
        return [cls.POSITIVE_TO_NEGATIVE, cls.NEGATIVE_TO_POSITIVE, cls.FLIP]


class InfluenceMappingSettings:
    """Stores options used to match imported influences to scene influences."""

    def __init__(
        self,
        use_name_matching=True,
        use_label_matching=True,
        use_distance_matching=True,
        use_dg_link_matching=True,
        distance_threshold=0.001,
    ):
        """Initializes influence mapping settings.

        Args:
            use_name_matching (bool): Whether influence names are matched.
            use_label_matching (bool): Whether Maya joint labels are matched.
            use_distance_matching (bool): Whether world positions are matched.
            use_dg_link_matching (bool): Whether dependency graph links are matched.
            distance_threshold (float): Maximum distance for position matching.
        """
        self.use_name_matching = use_name_matching
        self.use_label_matching = use_label_matching
        self.use_distance_matching = use_distance_matching
        self.use_dg_link_matching = use_dg_link_matching
        self.distance_threshold = distance_threshold

    def as_dict(self):
        """Serializes the settings.

        Returns:
            dict: JSON-compatible mapping settings.
        """
        return dict(self.__dict__)


def is_ngskin_available():
    """Checks whether the ngSkinTools2 Python package can be imported.

    Returns:
        bool: True when ngSkinTools2 is available.
    """
    try:
        import ngSkinTools2  # noqa: F401

        return True
    except ImportError:
        return False


def _get_ngskin_api(load_plugin=True):
    """Gets the ngSkinTools2 API and optionally loads its Maya plug-in.

    Args:
        load_plugin (bool): Whether to load the ngSkinTools2 Maya plug-in.

    Returns:
        module: The ngSkinTools2 API module.

    Raises:
        ImportError: If ngSkinTools2 is not installed.
        RuntimeError: If the ngSkinTools2 Maya plug-in cannot be loaded.
    """
    try:
        from ngSkinTools2 import api as ngskin_api
    except ImportError as exception:
        raise ImportError(
            "ngSkinTools2 is required for this operation. Install a compatible "
            "ngSkinTools2 build and make it available to Maya."
        ) from exception
    if load_plugin:
        try:
            from ngSkinTools2.api import plugin

            plugin.load_plugin()
            if not plugin.is_plugin_loaded():
                raise RuntimeError("The ngSkinTools2 Maya plug-in did not load.")
        except Exception as exception:
            raise RuntimeError(f"Unable to load the ngSkinTools2 Maya plug-in: {exception}") from exception
    return ngskin_api


def _validate_vertex_transfer_mode(vertex_transfer_mode):
    """Validates a vertex transfer mode.

    Args:
        vertex_transfer_mode (str): Transfer mode to validate.

    Returns:
        str: The validated transfer mode.

    Raises:
        ValueError: If the mode is unsupported.
    """
    if vertex_transfer_mode not in VertexTransferMode.get_values():
        raise ValueError(
            f'Unsupported vertex transfer mode "{vertex_transfer_mode}". '
            f"Expected one of: {VertexTransferMode.get_values()}"
        )
    return vertex_transfer_mode


def build_influence_mapping_config(settings=None):
    """Builds an ngSkinTools2 influence mapping configuration.

    Args:
        settings (InfluenceMappingSettings, optional): Mapping settings. Uses
            ngSkinTools2 transfer defaults when omitted.

    Returns:
        InfluenceMappingConfig: ngSkinTools2 mapping configuration.
    """
    ngskin_api = _get_ngskin_api()
    config = ngskin_api.InfluenceMappingConfig.transfer_defaults()
    if settings is None:
        return config
    if not isinstance(settings, InfluenceMappingSettings):
        raise TypeError("Influence mapping settings must be an InfluenceMappingSettings instance.")
    config.use_name_matching = settings.use_name_matching
    config.use_label_matching = settings.use_label_matching
    config.use_distance_matching = settings.use_distance_matching
    config.use_dg_link_matching = settings.use_dg_link_matching
    config.distance_threshold = settings.distance_threshold
    return config


def get_influences_from_file(file_path):
    """Gets influence paths stored in an ngSkinTools2 JSON export.

    Args:
        file_path (str): Path to an uncompressed ngSkinTools2 JSON file.

    Returns:
        list[str]: Influence paths in export order.
    """
    with open(file_path, "r", encoding="utf-8") as stream:
        data = json.load(stream)
    influences = data.get("influences") or []
    if isinstance(influences, dict):
        influences = influences.values()
    return [item.get("path") or item.get("name") for item in influences if item.get("path") or item.get("name")]


def resolve_name_mapping(source_name, name_mapping):
    """Resolves an influence name using full-path and short-name keys.

    Args:
        source_name (str): Source influence name or DAG path.
        name_mapping (dict): Source-to-destination influence names.

    Returns:
        str: Mapped name, or the original name when no match exists.
    """
    if not name_mapping:
        return source_name
    if source_name in name_mapping:
        return name_mapping[source_name]
    short_name = source_name.rsplit("|", 1)[-1]
    short_name = short_name.rsplit(":", 1)[-1]
    return name_mapping.get(short_name, source_name)


def _apply_name_mapping(influences, name_mapping):
    """Applies explicit source-to-destination names to influence metadata.

    Args:
        influences (list): ngSkinTools2 InfluenceInfo objects.
        name_mapping (dict): Source-to-destination influence names.

    Returns:
        list: Updated influence objects.
    """
    for influence in influences:
        source_name = influence.path_name()
        destination_name = resolve_name_mapping(source_name, name_mapping)
        if destination_name == source_name:
            continue
        if getattr(influence, "path", None) is not None:
            influence.path = destination_name
        else:
            influence.name = destination_name
    return influences


def export_weights(target, file_path, file_format=FileFormat.JSON):
    """Exports all ngSkinTools2 layers and influence metadata to a file.

    Args:
        target (str): Skinned mesh or skinCluster.
        file_path (str): Destination file path.
        file_format (str): One of the FileFormat values.

    Returns:
        str: Exported file path.
    """
    if file_format not in FileFormat.get_values():
        raise ValueError(f"Unsupported ngSkinTools2 file format: {file_format}")
    parent_dir = os.path.dirname(os.path.abspath(file_path))
    if not os.path.isdir(parent_dir):
        os.makedirs(parent_dir)
    ngskin_api = _get_ngskin_api()
    ngskin_api.export_json(target, file=file_path, format=file_format)
    return file_path


def import_weights(
    target,
    file_path,
    vertex_transfer_mode=VertexTransferMode.CLOSEST_POINT,
    influence_mapping_settings=None,
    influence_name_mapping=None,
    keep_existing_layers=True,
    file_format=FileFormat.JSON,
):
    """Imports ngSkinTools2 weights with configurable vertex/influence mapping.

    Args:
        target (str): Destination skinned mesh or skinCluster.
        file_path (str): Source ngSkinTools2 weight file.
        vertex_transfer_mode (str): Proximity, UV, or vertex ID matching mode.
        influence_mapping_settings (InfluenceMappingSettings, optional): Rules
            used to match influences.
        influence_name_mapping (dict, optional): Explicit source-to-destination
            influence names. Full DAG paths and short source names are accepted.
        keep_existing_layers (bool): Whether existing target layers are retained.
        file_format (str): One of the FileFormat values.

    Returns:
        bool: True when the transfer executes, otherwise False.

    Raises:
        ValueError: If an input file or option is invalid.
    """
    _validate_vertex_transfer_mode(vertex_transfer_mode)
    if not os.path.isfile(file_path):
        raise ValueError(f'Unable to import missing ngSkinTools2 weights file: "{file_path}"')
    if file_format not in FileFormat.get_values():
        raise ValueError(f"Unsupported ngSkinTools2 file format: {file_format}")

    ngskin_api = _get_ngskin_api()
    config = build_influence_mapping_config(influence_mapping_settings)
    if influence_name_mapping:
        config.use_name_matching = True
    if not influence_name_mapping and keep_existing_layers:
        result = ngskin_api.import_json(
            target,
            file=file_path,
            vertex_transfer_mode=vertex_transfer_mode,
            influences_mapping_config=config,
            format=file_format,
        )
        return result is not False

    from ngSkinTools2.api import transfer

    importer = transfer.LayersTransfer()
    importer.vertex_transfer_mode = vertex_transfer_mode
    importer.influences_mapping.config = config
    importer.keep_existing_layers = keep_existing_layers
    importer.load_source_from_file(file_path, format=file_format)
    _apply_name_mapping(importer.influences_mapping.influences, influence_name_mapping)
    importer.target = target
    result = importer.execute()
    return result is not False


def transfer_weights(
    source,
    destination,
    vertex_transfer_mode=VertexTransferMode.CLOSEST_POINT,
    influence_mapping_settings=None,
):
    """Transfers ngSkinTools2 layers between two bound polygon meshes.

    Args:
        source (str): Source mesh or skinCluster.
        destination (str): Destination mesh or skinCluster.
        vertex_transfer_mode (str): Proximity, UV, or vertex ID matching mode.
        influence_mapping_settings (InfluenceMappingSettings, optional): Rules
            used to match influences.

    Returns:
        bool: True after the transfer call executes.
    """
    _validate_vertex_transfer_mode(vertex_transfer_mode)
    ngskin_api = _get_ngskin_api()
    ngskin_api.transfer_layers(
        source,
        destination,
        vertex_transfer_mode=vertex_transfer_mode,
        influences_mapping_config=build_influence_mapping_config(influence_mapping_settings),
    )
    return True


def initialize_layers(target):
    """Initializes ngSkinTools2 layers on a bound mesh.

    Args:
        target (str): Skinned mesh or skinCluster.

    Returns:
        Layers: ngSkinTools2 layer collection.
    """
    return _get_ngskin_api().init_layers(target)


def get_layers(target):
    """Gets all ngSkinTools2 layers for a target.

    Args:
        target (str): Skinned mesh or skinCluster.

    Returns:
        list[Layer]: Existing layers, or an empty list when not initialized.
    """
    ngskin_api = _get_ngskin_api()
    layers = ngskin_api.Layers(target)
    return layers.list() if layers.is_enabled() else []


def get_related_skin_cluster(target):
    """Gets the skinCluster associated with a target through ngSkinTools2.

    Args:
        target (str): Mesh, shape, or skinCluster.

    Returns:
        str or None: Related skinCluster.
    """
    return _get_ngskin_api().get_related_skin_cluster(target)


def remove_custom_nodes(targets=None):
    """Deletes ngSkinTools2 custom nodes while preserving skinCluster weights.

    Args:
        targets (list[str] or str, optional): Meshes whose custom nodes should
            be removed. When omitted, all custom nodes in the scene are removed.

    Returns:
        bool: True after the cleanup operation executes.
    """
    _get_ngskin_api()
    from ngSkinTools2.operations import removeLayerData

    if isinstance(targets, str):
        targets = [targets]
    remove_function = getattr(removeLayerData, "remove_custom_nodes", None)
    try:
        if remove_function:
            remove_function(interactive=False, meshes=targets or [])
        elif targets:
            removeLayerData.removeCustomNodes(meshes=targets)
        else:
            removeLayerData.removeCustomNodes()
    except RuntimeError:
        if targets:
            remaining_nodes = removeLayerData.list_custom_nodes_for_meshes(targets)
        else:
            remaining_nodes = removeLayerData.list_custom_nodes()
        if remaining_nodes:
            raise
    return True


def set_layer_limits(target, influence_limit=None, prune_threshold=None):
    """Sets ngSkinTools2 per-vertex influence and pruning limits.

    Args:
        target (str): Skinned mesh or skinCluster.
        influence_limit (int, optional): Maximum influences per vertex.
        prune_threshold (float, optional): Weights below this value are pruned.

    Returns:
        Layers: Updated layer collection.
    """
    layers = initialize_layers(target)
    if influence_limit is not None:
        layers.influence_limit_per_vertex = influence_limit
    if prune_threshold is not None:
        layers.prune_weights_filter_threshold = prune_threshold
    return layers


def assign_weights_from_closest_joint(target, layer, influences=None):
    """Assigns selected vertices to their closest influence.

    Args:
        target (str): Skinned mesh or skinCluster.
        layer (Layer or int): Destination layer.
        influences (list[int], optional): Allowed influence logical indexes.

    Returns:
        bool: True after the operation executes.
    """
    _get_ngskin_api().assign_from_closest_joint(target, layer, influences=influences)
    return True


def unify_weights(target, layer, overall_effect=1.0, single_cluster_mode=False):
    """Averages weights across selected vertices or connected shells.

    Args:
        target (str): Skinned mesh or skinCluster.
        layer (Layer or int): Destination layer.
        overall_effect (float): Blend amount from original to averaged weights.
        single_cluster_mode (bool): Treat all selected vertices as one cluster.

    Returns:
        bool: True after the operation executes.
    """
    _get_ngskin_api().unify_weights(target, layer, overall_effect, single_cluster_mode)
    return True


def flood_weights(target, mode, intensity=1.0, iterations=1, influence=None, influences=None):
    """Runs an ngSkinTools2 replace/add/scale/smooth/sharpen flood operation.

    Args:
        target (Layer or str): Layer or mesh receiving the operation.
        mode (str): One of the PaintMode values.
        intensity (float): Flood operation intensity.
        iterations (int): Number of smoothing or sharpening iterations.
        influence (int or str, optional): Single influence or named paint target.
        influences (list[int], optional): Multiple influence logical indexes.

    Returns:
        bool: True after the operation executes.
    """
    if mode not in PaintMode.get_values():
        raise ValueError(f"Unsupported ngSkinTools2 paint mode: {mode}")
    ngskin_api = _get_ngskin_api()
    settings = ngskin_api.PaintModeSettings()
    settings.mode = getattr(ngskin_api.PaintMode, mode)
    settings.intensity = intensity
    settings.iterations = iterations
    ngskin_api.flood_weights(target, influence=influence, influences=influences, settings=settings)
    return True


def configure_layer_mirror(
    layer,
    direction=MirrorDirection.POSITIVE_TO_NEGATIVE,
    mirror_mask=True,
    mirror_weights=True,
    mirror_dq=True,
):
    """Configures the non-destructive mirror effect for a layer.

    Args:
        layer (Layer): ngSkinTools2 layer to configure.
        direction (str): One of the MirrorDirection values.
        mirror_mask (bool): Whether the layer mask is mirrored.
        mirror_weights (bool): Whether influence weights are mirrored.
        mirror_dq (bool): Whether dual-quaternion weights are mirrored.

    Returns:
        Layer: The configured layer.
    """
    if direction not in MirrorDirection.get_values():
        raise ValueError(f"Unsupported ngSkinTools2 mirror direction: {direction}")
    ngskin_api = _get_ngskin_api()
    direction_map = {
        MirrorDirection.POSITIVE_TO_NEGATIVE: ngskin_api.MirrorOptions.directionPositiveToNegative,
        MirrorDirection.NEGATIVE_TO_POSITIVE: ngskin_api.MirrorOptions.directionNegativeToPositive,
        MirrorDirection.FLIP: ngskin_api.MirrorOptions.directionFlip,
    }
    layer.effects.configure_mirror(
        mirror_mask=mirror_mask,
        mirror_weights=mirror_weights,
        mirror_dq=mirror_dq,
        mirror_direction=direction_map[direction],
    )
    return layer
