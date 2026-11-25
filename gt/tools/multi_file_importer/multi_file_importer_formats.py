"""
Multi-File Importer Formats

One small class per file format. Each class only describes the format for this tool (extensions,
options shown in "Format Options", whether it can be referenced) and calls the utility that does the
real work:

    Maya scene  -> gt.core.scene        (load_file_into_scene, read_scene_file_info)
    FBX         -> gt.utils.fbx         (import_fbx_file, read_fbx_file_info)
    OBJ         -> gt.core.scene
    Alembic     -> gt.core.scene + gt.core.alembic
    USD         -> gt.utils.usd         (import_usd_file, create_usd_stage, read_usd_file_info)
    BVH         -> gt.utils.bvh         (import_bvh_file, get_bvh_file_info)
    NumPy       -> gt.utils.numpy
    Other       -> any format a loaded Maya translator can read

To support a new format: add its logic to a utility module, then add a class here and list it in
BUILTIN_FORMAT_CLASSES (or call register_format at runtime).

This module is importable outside Maya; utilities are imported when a file is loaded.
"""

import logging
import os
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

OPTION_BOOL = "bool"
OPTION_INT = "int"
OPTION_FLOAT = "float"
OPTION_CHOICE = "choice"
OPTION_TEXT = "text"

FILE_INFO_FPS = "fps"
FILE_INFO_LINEAR_UNIT = "linear_unit"
FILE_INFO_UP_AXIS = "up_axis"
FILE_INFO_TIME_RANGE = "time_range"

TIME_MODE_LABELS = {"Real Time": "real_time", "One Sample per Frame": "frame_per_frame"}
TIME_MODE_TOOLTIP = (
    "Real Time: keep real-world timing; samples land between frames when the file and scene rates differ.\n"
    "One Sample per Frame: place one sample on every scene frame (faster or slower playback when rates differ)."
)
TRANSLATOR_DENYLIST = {"move", "image", "EPS", "Illustrator", "editMA", "editMB", "audio"}


class FormatOption:
    """Describes one user-facing format option."""

    def __init__(self, key, label, option_type, default, tooltip="", choices=None, minimum=None, maximum=None,
                 decimals=3):
        """Initializes a format option.

        Args:
            key (str): Stable key used in saved settings.
            label (str): Display label.
            option_type (str): One of the OPTION_* values.
            default (object): Default value.
            tooltip (str, optional): Help text.
            choices (list, optional): Allowed values for OPTION_CHOICE.
            minimum (float, optional): Minimum for numeric options.
            maximum (float, optional): Maximum for numeric options.
            decimals (int, optional): Decimals shown for OPTION_FLOAT.
        """
        self.key = key
        self.label = label
        self.option_type = option_type
        self.default = default
        self.tooltip = tooltip
        self.choices = list(choices or [])
        self.minimum = minimum
        self.maximum = maximum
        self.decimals = decimals

    def normalize(self, value):
        """Coerces a stored value to this option's type, falling back to the default.

        Args:
            value (object): Stored or edited value.

        Returns:
            object: Valid value.
        """
        if value is None:
            return self.default
        try:
            if self.option_type == OPTION_BOOL:
                return bool(value)
            if self.option_type == OPTION_INT:
                return self._clamp(int(value))
            if self.option_type == OPTION_FLOAT:
                return self._clamp(float(value))
            if self.option_type == OPTION_CHOICE:
                return value if value in self.choices else self.default
            return str(value)
        except (TypeError, ValueError):
            return self.default

    def _clamp(self, value):
        """Clamps a numeric value to the option limits.

        Args:
            value (float): Value to clamp.

        Returns:
            float: Clamped value of the same type.
        """
        if self.minimum is not None and value < self.minimum:
            value = type(value)(self.minimum)
        if self.maximum is not None and value > self.maximum:
            value = type(value)(self.maximum)
        return value


class FormatResult:
    """What a format added to the scene."""

    def __init__(self, nodes=None, time_range=None, reference_node="", root_nodes=None):
        """Initializes a result.

        Args:
            nodes (list, optional): Every node created.
            time_range (tuple, optional): Frame range when the format knows it without animation curves.
            reference_node (str, optional): Reference node for referenced files.
            root_nodes (list, optional): Top-level transforms. Derived from nodes when omitted.
        """
        self.nodes = list(nodes or [])
        self.time_range = time_range
        self.reference_node = reference_node
        self.root_nodes = list(root_nodes or [])


class FormatBase:
    """Base class. Subclasses set the class attributes and implement load."""

    key = ""
    label = ""
    description = ""
    extensions = ()
    plugins = ()
    supports_reference = False

    def get_options(self):
        """Gets the options shown in the Format Options section.

        Returns:
            list: FormatOption objects in display order.
        """
        return []

    def normalize_settings(self, settings):
        """Builds a complete, valid settings dictionary.

        Args:
            settings (dict): Stored settings, possibly partial or outdated.

        Returns:
            dict: Valid value for every option.
        """
        settings = settings if isinstance(settings, dict) else {}
        return {option.key: option.normalize(settings.get(option.key)) for option in self.get_options()}

    def get_extensions(self):
        """Gets the handled extensions.

        Returns:
            list: Lowercase extensions including the dot.
        """
        return [extension.lower() for extension in self.extensions]

    def handles(self, file_path):
        """Checks whether this format handles a file.

        Args:
            file_path (str): File path.

        Returns:
            bool: True when the extension is handled.
        """
        return os.path.splitext(str(file_path or ""))[1].lower() in self.get_extensions()

    def is_available(self):
        """Checks whether the format can be loaded in this session.

        Returns:
            tuple: (available, reason).
        """
        return True, ""

    def load_plugins(self):
        """Loads the Maya plugins this format needs.

        Raises:
            RuntimeError: When a plugin cannot be loaded.
        """
        if not self.plugins:
            return
        import maya.cmds as cmds

        for plugin_name in self.plugins:
            if cmds.pluginInfo(plugin_name, query=True, loaded=True):
                continue
            try:
                cmds.loadPlugin(plugin_name, quiet=True)
            except Exception as exception:
                raise RuntimeError(f'Unable to load plugin "{plugin_name}": {exception}')

    def read_file_info(self, file_path):
        """Reads frame rate, unit, up axis or time range from the file without importing it.

        Args:
            file_path (str): File path.

        Returns:
            dict: Known FILE_INFO_* values. Time ranges use the file's own frame rate.
        """
        return {}

    def load(self, file_path, namespace="", reference=False, settings=None):
        """Loads a file into the current scene.

        Args:
            file_path (str): File path.
            namespace (str, optional): Namespace for new nodes.
            reference (bool, optional): Reference instead of import (only when supports_reference).
            settings (dict, optional): Format settings.

        Returns:
            FormatResult: What was added.
        """
        raise NotImplementedError


class MayaSceneFormat(FormatBase):
    """Maya ASCII and binary scenes."""

    key = "maya_scene"
    label = "Maya Scene"
    description = "Maya ASCII (.ma) and Maya Binary (.mb) scenes."
    extensions = (".ma", ".mb")
    supports_reference = True

    def get_options(self):
        """Gets the options.

        Returns:
            list: FormatOption objects.
        """
        return [
            FormatOption("execute_script_nodes", "Execute Script Nodes", OPTION_BOOL, False,
                         tooltip="Allow script nodes stored in imported scenes to run. Off is safer for review."),
            FormatOption("defer_reference", "Load References Unloaded", OPTION_BOOL, False,
                         tooltip="When referencing, create the references unloaded so they can be loaded later."),
        ]

    def read_file_info(self, file_path):
        """Reads frame rate, unit, up axis and stored playback range.

        Args:
            file_path (str): Scene path.

        Returns:
            dict: Known FILE_INFO_* values.
        """
        import gt.core.scene as core_scene

        return core_scene.read_scene_file_info(file_path)

    def load(self, file_path, namespace="", reference=False, settings=None):
        """Imports or references a Maya scene.

        Args:
            file_path (str): Scene path.
            namespace (str, optional): Namespace for new nodes.
            reference (bool, optional): Reference instead of import.
            settings (dict, optional): Format settings.

        Returns:
            FormatResult: What was added.
        """
        import gt.core.scene as core_scene

        settings = self.normalize_settings(settings)
        nodes, reference_node = core_scene.load_file_into_scene(
            file_path,
            namespace=namespace,
            reference=reference,
            execute_script_nodes=settings["execute_script_nodes"],
            extra_kwargs={"deferReference": settings["defer_reference"]} if reference else None,
        )
        return FormatResult(nodes=nodes, reference_node=reference_node)


class FbxFormat(FormatBase):
    """Autodesk FBX files."""

    key = "fbx"
    label = "FBX"
    description = "Autodesk FBX files (fbxmaya plugin)."
    extensions = (".fbx",)
    plugins = ("fbxmaya",)
    supports_reference = True

    def get_options(self):
        """Gets the options.

        Returns:
            list: FormatOption objects.
        """
        return [
            FormatOption("import_mode", "Import Mode", OPTION_CHOICE, "Add",
                         choices=["Add", "Merge", "Update Animation"],
                         tooltip="Add: always create new nodes (recommended for many files).\n"
                         "Merge: reuse nodes with matching names.\n"
                         "Update Animation: only update animation on existing nodes with matching names."),
            FormatOption("merge_animation_layers", "Merge Animation Layers", OPTION_BOOL, True),
            FormatOption("cameras", "Import Cameras", OPTION_BOOL, False),
            FormatOption("lights", "Import Lights", OPTION_BOOL, False),
            FormatOption("constraints", "Import Constraints", OPTION_BOOL, False),
            FormatOption("use_file_frame_rate", "Let FBX Set Frame Rate", OPTION_BOOL, False,
                         tooltip="Let the FBX plugin change the scene frame rate to the file frame rate.\n"
                         'With "Reapply after importing" on (Scene Settings), the tool\'s frame rate wins at the end.'),
        ]

    def read_file_info(self, file_path):
        """Reads frame rate, unit and up axis from the FBX header.

        Args:
            file_path (str): FBX path.

        Returns:
            dict: Known FILE_INFO_* values.
        """
        import gt.utils.fbx as utils_fbx

        return utils_fbx.read_fbx_file_info(file_path)

    def load(self, file_path, namespace="", reference=False, settings=None):
        """Imports or references an FBX file.

        Args:
            file_path (str): FBX path.
            namespace (str, optional): Namespace for new nodes.
            reference (bool, optional): Reference instead of import.
            settings (dict, optional): Format settings.

        Returns:
            FormatResult: What was added.
        """
        import gt.utils.fbx as utils_fbx

        nodes, reference_node = utils_fbx.import_fbx_file(
            file_path, namespace=namespace, reference=reference, **self.normalize_settings(settings)
        )
        return FormatResult(nodes=nodes, reference_node=reference_node)


class ObjFormat(FormatBase):
    """Wavefront OBJ files."""

    key = "obj"
    label = "OBJ"
    description = "Wavefront OBJ geometry (objExport plugin)."
    extensions = (".obj",)
    plugins = ("objExport",)

    def load(self, file_path, namespace="", reference=False, settings=None):
        """Imports an OBJ file.

        Args:
            file_path (str): OBJ path.
            namespace (str, optional): Namespace for new nodes.
            reference (bool, optional): Unused.
            settings (dict, optional): Unused.

        Returns:
            FormatResult: What was added.
        """
        import gt.core.scene as core_scene

        nodes, _ = core_scene.load_file_into_scene(file_path, file_type="OBJ", namespace=namespace)
        return FormatResult(nodes=nodes)


class AlembicFormat(FormatBase):
    """Alembic caches."""

    key = "alembic"
    label = "Alembic"
    description = "Alembic caches (AbcImport plugin)."
    extensions = (".abc",)
    plugins = ("AbcImport",)
    supports_reference = True

    def load(self, file_path, namespace="", reference=False, settings=None):
        """Imports or references an Alembic cache.

        Args:
            file_path (str): Alembic path.
            namespace (str, optional): Namespace for new nodes.
            reference (bool, optional): Reference instead of import.
            settings (dict, optional): Unused.

        Returns:
            FormatResult: What was added, with the cached frame range.
        """
        import gt.core.alembic as core_alembic
        import gt.core.scene as core_scene

        nodes, reference_node = core_scene.load_file_into_scene(
            file_path, file_type="Alembic", namespace=namespace, reference=reference
        )
        return FormatResult(nodes=nodes, reference_node=reference_node,
                            time_range=core_alembic.get_alembic_time_range(nodes))


class UsdFormat(FormatBase):
    """USD layers."""

    key = "usd"
    label = "USD"
    description = "Universal Scene Description, imported as Maya data or loaded as a stage (mayaUsdPlugin)."
    extensions = (".usd", ".usda", ".usdc", ".usdz")
    plugins = ("mayaUsdPlugin",)
    mode_import = "Import as Maya Data"
    mode_stage = "Stage (Proxy Shape)"

    def get_options(self):
        """Gets the options.

        Returns:
            list: FormatOption objects.
        """
        return [
            FormatOption("mode", "Mode", OPTION_CHOICE, self.mode_import, choices=[self.mode_import, self.mode_stage],
                         tooltip="Import as Maya Data: convert prims to regular Maya nodes (joints, meshes, curves).\n"
                         "Stage (Proxy Shape): load the file as a USD stage without converting it."),
            FormatOption("read_animation", "Read Animation", OPTION_BOOL, True,
                         tooltip="Import as Maya Data only: convert time samples to animation curves."),
            FormatOption("import_materials", "Import Materials", OPTION_BOOL, True,
                         tooltip="Import as Maya Data only: convert USD materials."),
            FormatOption("prim_path", "Prim Path", OPTION_TEXT, "/", tooltip="Root prim to load. / loads everything."),
            FormatOption("load_payloads", "Load Payloads", OPTION_BOOL, True,
                         tooltip="Stage mode only: load payloads when the stage opens."),
        ]

    def read_file_info(self, file_path):
        """Reads frame rate, unit, up axis and time range from the layer.

        Args:
            file_path (str): USD path.

        Returns:
            dict: Known FILE_INFO_* values.
        """
        import gt.utils.usd as utils_usd

        return utils_usd.read_usd_file_info(file_path)

    def load(self, file_path, namespace="", reference=False, settings=None):
        """Imports a USD file or loads it as a stage.

        Args:
            file_path (str): USD path.
            namespace (str, optional): Namespace for new nodes.
            reference (bool, optional): Unused; Stage mode keeps the file live instead.
            settings (dict, optional): Format settings.

        Returns:
            FormatResult: What was added.
        """
        import gt.utils.usd as utils_usd

        settings = self.normalize_settings(settings)
        if settings["mode"] == self.mode_stage:
            nodes = utils_usd.create_usd_stage(file_path, namespace, settings["prim_path"], settings["load_payloads"])
            return FormatResult(nodes=nodes, time_range=get_scene_time_range(self.read_file_info(file_path)))
        nodes = utils_usd.import_usd_file(
            file_path, namespace, settings["prim_path"], settings["read_animation"], settings["import_materials"]
        )
        return FormatResult(nodes=nodes)


class BvhFormat(FormatBase):
    """Biovision Hierarchy motion files."""

    key = "bvh"
    label = "BVH"
    description = "Biovision Hierarchy motion capture, built as an animated joint hierarchy."
    extensions = (".bvh",)

    def get_options(self):
        """Gets the options.

        Returns:
            list: FormatOption objects.
        """
        return [
            FormatOption("scale", "Scale", OPTION_FLOAT, 1.0, minimum=0.0001, decimals=4,
                         tooltip="Multiplier applied to joint offsets and root motion."),
            FormatOption("start_frame", "Start Frame", OPTION_FLOAT, 1.0, decimals=2,
                         tooltip="Timeline frame of the first sample."),
            FormatOption("time_mode", "Timing", OPTION_CHOICE, "Real Time", choices=list(TIME_MODE_LABELS),
                         tooltip=TIME_MODE_TOOLTIP),
            FormatOption("include_end_sites", "Create End Joints", OPTION_BOOL, True,
                         tooltip='Create a joint for every "End Site".'),
        ]

    def read_file_info(self, file_path):
        """Reads the sample rate.

        Args:
            file_path (str): BVH path.

        Returns:
            dict: FILE_INFO_FPS when readable.
        """
        import gt.utils.bvh as utils_bvh

        fps = utils_bvh.get_bvh_file_info(file_path).get("fps")
        return {FILE_INFO_FPS: round(fps, 3)} if fps else {}

    def load(self, file_path, namespace="", reference=False, settings=None):
        """Builds the skeleton and animation.

        Args:
            file_path (str): BVH path.
            namespace (str, optional): Namespace for new nodes.
            reference (bool, optional): Unused.
            settings (dict, optional): Format settings.

        Returns:
            FormatResult: What was added.
        """
        import gt.core.uuid as core_uuid
        import gt.utils.bvh as utils_bvh

        settings = self.normalize_settings(settings)
        node_ids_before = core_uuid.capture_scene_uuids()
        build_result = utils_bvh.import_bvh_file(
            file_path,
            namespace=namespace,
            scale=settings["scale"],
            start_frame=settings["start_frame"],
            time_mode=TIME_MODE_LABELS.get(settings["time_mode"], utils_bvh.TIME_MODE_REAL_TIME),
            include_end_sites=settings["include_end_sites"],
        )
        return FormatResult(nodes=core_uuid.get_nodes_created_since(node_ids_before),
                            root_nodes=build_result["root_joints"])


class NumpyPointsFormat(FormatBase):
    """NumPy arrays of positions."""

    key = "numpy_points"
    label = "NumPy Points"
    description = "NumPy position arrays (.npy, .npz), built as animated locators."
    extensions = (".npy", ".npz")

    def get_options(self):
        """Gets the options.

        Returns:
            list: FormatOption objects.
        """
        return [
            FormatOption("array_key", "Array Key (.npz)", OPTION_TEXT, "posed_joints",
                         tooltip="Array to read inside .npz archives (ignored for .npy).\n"
                         "Positions shaped (frames, points, 3), (frames, 3) or (frames, points*3)."),
            FormatOption("fps", "Sample Rate (fps)", OPTION_FLOAT, 30.0, minimum=0.001,
                         tooltip="Samples per second stored in the array."),
            FormatOption("source_unit", "Source Unit", OPTION_CHOICE, "m", choices=["m", "cm", "mm"],
                         tooltip="Unit of the stored positions. Values are converted to the scene unit."),
            FormatOption("source_up_axis", "Source Up Axis", OPTION_CHOICE, "y", choices=["y", "z"],
                         tooltip="Up axis of the stored positions; the group is rotated when the scene differs."),
            FormatOption("start_frame", "Start Frame", OPTION_FLOAT, 1.0, decimals=2),
            FormatOption("time_mode", "Timing", OPTION_CHOICE, "Real Time", choices=list(TIME_MODE_LABELS),
                         tooltip=TIME_MODE_TOOLTIP),
            FormatOption("locator_scale", "Locator Size", OPTION_FLOAT, 2.0, minimum=0.001),
        ]

    def is_available(self):
        """Checks whether NumPy is installed.

        Returns:
            tuple: (available, reason).
        """
        import gt.utils.numpy as utils_numpy

        if utils_numpy.is_numpy_available():
            return True, ""
        return False, "NumPy is not available in this Python session."

    def load(self, file_path, namespace="", reference=False, settings=None):
        """Creates animated locators from the array.

        Args:
            file_path (str): Array path.
            namespace (str, optional): Namespace for new nodes.
            reference (bool, optional): Unused.
            settings (dict, optional): Format settings.

        Returns:
            FormatResult: What was added.
        """
        import gt.core.uuid as core_uuid
        import gt.utils.numpy as utils_numpy

        available, reason = self.is_available()
        if not available:
            raise RuntimeError(reason)
        settings = self.normalize_settings(settings)
        settings["time_mode"] = TIME_MODE_LABELS.get(settings["time_mode"], "real_time")
        node_ids_before = core_uuid.capture_scene_uuids()
        build_result = utils_numpy.import_point_array_file(file_path, namespace=namespace, **settings)
        return FormatResult(nodes=core_uuid.get_nodes_created_since(node_ids_before),
                            root_nodes=[build_result["root"]])


class MayaTranslatorFormat(FormatBase):
    """Fallback for any other format a loaded Maya translator can read."""

    key = "maya_translator"
    label = "Other Maya Formats"
    description = "Any other format readable by a loaded Maya translator plugin."

    def __init__(self, excluded_extensions=None):
        """Initializes the fallback format.

        Args:
            excluded_extensions (list, optional): Extensions handled by dedicated formats.
        """
        self.excluded_extensions = tuple(extension.lower() for extension in (excluded_extensions or []))
        self._translator_by_extension = None

    def get_translator_map(self):
        """Gets the readable translators of the current Maya session, by extension.

        Returns:
            dict: Extension to translator name. Empty outside an initialized Maya session.
        """
        if self._translator_by_extension is not None:
            return self._translator_by_extension
        translator_map = {}
        try:
            import maya.cmds as cmds

            for translator in cmds.translator(query=True, list=True) or []:
                if translator in TRANSLATOR_DENYLIST or not cmds.translator(translator, query=True, readSupport=True):
                    continue
                for extension in parse_translator_extensions(cmds.translator(translator, query=True, filter=True)):
                    if extension not in self.excluded_extensions:
                        translator_map.setdefault(extension, translator)
        except Exception as exception:
            logger.debug(f"Maya translators unavailable: {exception}")
            return {}
        self._translator_by_extension = translator_map
        return translator_map

    def get_extensions(self):
        """Gets the extensions readable by loaded translators.

        Returns:
            list: Lowercase extensions including the dot.
        """
        return sorted(self.get_translator_map())

    def load(self, file_path, namespace="", reference=False, settings=None):
        """Imports a file with the matching translator.

        Args:
            file_path (str): File path.
            namespace (str, optional): Namespace for new nodes.
            reference (bool, optional): Unused.
            settings (dict, optional): Unused.

        Returns:
            FormatResult: What was added.
        """
        import gt.core.scene as core_scene

        translator = self.get_translator_map().get(os.path.splitext(file_path)[1].lower())
        nodes, _ = core_scene.load_file_into_scene(file_path, file_type=translator, namespace=namespace)
        return FormatResult(nodes=nodes)


# ------------------------------------------------------------------ helpers
def parse_translator_extensions(filter_text):
    """Extracts extensions from a Maya translator filter such as "*.obj" or "*.ma;*.mb".

    Args:
        filter_text (str): Translator filter.

    Returns:
        list: Lowercase extensions including the dot.
    """
    extensions = re.findall(r"\*(\.[A-Za-z0-9_]+)", str(filter_text or ""))
    return [extension.lower() for extension in extensions]


def get_scene_time_range(file_info):
    """Converts a file's stored time range to the current scene frame rate.

    Args:
        file_info (dict): Result of read_file_info.

    Returns:
        tuple: (start, end) in scene frames, or None.
    """
    time_range = file_info.get(FILE_INFO_TIME_RANGE)
    file_fps = file_info.get(FILE_INFO_FPS)
    if not time_range or not file_fps:
        return time_range
    import gt.core.scene as core_scene

    scene_fps = core_scene.get_frame_rate()
    ratio = float(scene_fps) / float(file_fps)
    return float(time_range[0]) * ratio, float(time_range[1]) * ratio


# ------------------------------------------------------------------ registry
BUILTIN_FORMAT_CLASSES = [
    MayaSceneFormat,
    FbxFormat,
    ObjFormat,
    AlembicFormat,
    UsdFormat,
    BvhFormat,
    NumpyPointsFormat,
]
_FORMATS = []


def get_formats():
    """Gets every format, in priority order (the Maya translator fallback is last).

    Returns:
        list: FormatBase instances.
    """
    if not _FORMATS:
        builtin_formats = [format_class() for format_class in BUILTIN_FORMAT_CLASSES]
        _FORMATS.extend(builtin_formats)
        dedicated_extensions = [extension for item in builtin_formats for extension in item.get_extensions()]
        _FORMATS.append(MayaTranslatorFormat(excluded_extensions=dedicated_extensions))
    return list(_FORMATS)


def register_format(file_format, replace=False):
    """Adds a custom format (checked before the Maya translator fallback).

    Args:
        file_format (FormatBase): Format instance with a unique key.
        replace (bool, optional): Replace a format with the same key.

    Returns:
        bool: True when registered.
    """
    if not isinstance(file_format, FormatBase) or not file_format.key:
        raise ValueError("Formats must inherit FormatBase and define a key.")
    formats = get_formats()
    existing = next((item for item in formats if item.key == file_format.key), None)
    if existing and not replace:
        return False
    if existing:
        _FORMATS[_FORMATS.index(existing)] = file_format
    else:
        _FORMATS.insert(len(_FORMATS) - 1, file_format)
    return True


def unregister_format(key):
    """Removes a format.

    Args:
        key (str): Format key.

    Returns:
        bool: True when removed.
    """
    file_format = get_format(key)
    if not file_format:
        return False
    _FORMATS.remove(file_format)
    return True


def get_format(key):
    """Gets a format by key.

    Args:
        key (str): Format key.

    Returns:
        FormatBase: Matching format, or None.
    """
    return next((item for item in get_formats() if item.key == key), None)


def get_format_for_path(file_path):
    """Gets the format that handles a file.

    Args:
        file_path (str): File path.

    Returns:
        FormatBase: Matching format, or None when unsupported.
    """
    return next((item for item in get_formats() if item.handles(file_path)), None)


def get_supported_extensions():
    """Gets every supported extension (translator extensions only inside an initialized Maya session).

    Returns:
        list: Sorted lowercase extensions.
    """
    extensions = set()
    for file_format in get_formats():
        extensions.update(file_format.get_extensions())
    return sorted(extensions)


def read_file_info(file_path):
    """Reads file information with the matching format, never raising.

    Args:
        file_path (str): File path.

    Returns:
        dict: Known FILE_INFO_* values.
    """
    file_format = get_format_for_path(file_path)
    if not file_format:
        return {}
    try:
        return file_format.read_file_info(file_path) or {}
    except Exception as exception:
        logger.debug(f'Unable to read file info from "{file_path}": {exception}')
        return {}
