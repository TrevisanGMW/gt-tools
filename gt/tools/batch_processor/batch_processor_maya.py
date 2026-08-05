"""
Batch Processor Maya Runtime Helpers

Maya imports are intentionally lazy so batch processor models and tests remain
usable in a regular Python interpreter.
"""

import os


_STANDALONE_INITIALIZED = False

RELEVANT_PLUGIN_BY_EXTENSION = {
    ".fbx": "fbxmaya",
    ".obj": "objExport",
    ".abc": "AbcImport",
    ".usd": "mayaUsdPlugin",
    ".usda": "mayaUsdPlugin",
    ".usdc": "mayaUsdPlugin",
}


def is_maya_session_available():
    """Checks whether maya.cmds is already connected to a Maya session.

    Returns:
        bool: True when Maya commands are already available.
    """
    try:
        import maya.cmds as cmds

        cmds.about(batch=True)
        return True
    except Exception:
        return False


def get_maya_cmds(initialize_standalone=True):
    """Gets the maya.cmds module, initializing standalone Maya when needed.

    Args:
        initialize_standalone (bool, optional): Whether to initialize maya.standalone.

    Returns:
        module: maya.cmds module.

    Raises:
        RuntimeError: If Maya Python modules are unavailable.
    """
    global _STANDALONE_INITIALIZED
    if initialize_standalone and not is_maya_session_available():
        try:
            import maya.standalone as maya_standalone

            if not _STANDALONE_INITIALIZED:
                try:
                    maya_standalone.initialize(name="python")
                    _STANDALONE_INITIALIZED = True
                except RuntimeError as exception:
                    if "already initialized" not in str(exception).lower():
                        raise
        except ImportError:
            pass
        except Exception as exception:
            raise RuntimeError("Unable to initialize Maya standalone: {0}".format(exception))

    try:
        import maya.cmds as cmds
    except ImportError as exception:
        raise RuntimeError("Maya Python modules are unavailable: {0}".format(exception))
    return cmds


def new_scene():
    """Creates a new empty Maya scene.

    Returns:
        module: maya.cmds module.
    """
    cmds = get_maya_cmds()
    cmds.file(new=True, force=True)
    return cmds


def load_plugin(plugin_name):
    """Loads a Maya plugin when it is not already loaded.

    Args:
        plugin_name (str): Plugin name.

    Returns:
        bool: True when the plugin is loaded.
    """
    cmds = get_maya_cmds()
    if cmds.pluginInfo(plugin_name, query=True, loaded=True):
        return True
    cmds.loadPlugin(plugin_name, quiet=True)
    return bool(cmds.pluginInfo(plugin_name, query=True, loaded=True))


def load_relevant_file_plugin(file_path):
    """Loads a known importer plugin for a file path when one is mapped.

    Args:
        file_path (str): Source file path.

    Returns:
        bool: True when a plugin was mapped and loaded, False when no mapping exists.
    """
    extension = os.path.splitext(file_path)[1].lower()
    plugin_name = RELEVANT_PLUGIN_BY_EXTENSION.get(extension)
    if not plugin_name:
        return False
    return load_plugin(plugin_name)


def is_fbx_file(file_path):
    """Checks whether a file path points to an FBX file.

    Args:
        file_path (str): File path to inspect.

    Returns:
        bool: True when the path extension is .fbx.
    """
    return os.path.splitext(str(file_path or ""))[1].lower() == ".fbx"


def import_file(file_path, namespace=None, load_relevant_plugins=True):
    """Imports a file into the current Maya scene.

    Args:
        file_path (str): File to import.
        namespace (str, optional): Optional namespace.
        load_relevant_plugins (bool, optional): Whether to load known importer plugins.

    Returns:
        list: Nodes returned by Maya for the import command.
    """
    cmds = get_maya_cmds()
    if load_relevant_plugins:
        load_relevant_file_plugin(file_path)
    import_kwargs = {
        "i": True,
        "ignoreVersion": True,
        "returnNewNodes": True,
    }
    if namespace:
        import_kwargs["namespace"] = namespace
    return cmds.file(file_path, **import_kwargs) or []


def open_fbx_scene(file_path, load_relevant_plugins=True):
    """Opens an FBX file as the active scene using animation-aware import settings.

    Args:
        file_path (str): FBX file path.
        load_relevant_plugins (bool, optional): Whether to load known file plugins.

    Returns:
        str: Opened file path.
    """
    import gt.utils.fbx as utils_fbx

    cmds = get_maya_cmds()
    if load_relevant_plugins:
        load_relevant_file_plugin(file_path)
    with utils_fbx.FbxImporter() as fbx_importer:
        fbx_importer.set_preferences_animation()
        return cmds.file(
            file_path,
            open=True,
            force=True,
            type="FBX",
            ignoreVersion=True,
        )


def open_scene(file_path, load_relevant_plugins=True):
    """Opens a Maya scene file.

    Args:
        file_path (str): Maya scene file path.
        load_relevant_plugins (bool, optional): Whether to load known file plugins.

    Returns:
        str: Opened file path.
    """
    if is_fbx_file(file_path):
        return open_fbx_scene(file_path, load_relevant_plugins=load_relevant_plugins)
    cmds = get_maya_cmds()
    if load_relevant_plugins:
        load_relevant_file_plugin(file_path)
    return cmds.file(file_path, open=True, force=True, ignoreVersion=True)


def set_framerate(framerate):
    """Sets the Maya scene framerate.

    Args:
        framerate (int): Frames per second.

    Returns:
        str: Maya time unit used by the command.
    """
    cmds = get_maya_cmds()
    framerate = int(float(framerate))
    time_unit_by_framerate = {
        15: "game",
        24: "film",
        25: "pal",
        30: "ntsc",
        48: "show",
        50: "palf",
        60: "ntscf",
    }
    time_unit = time_unit_by_framerate.get(framerate, "{0}fps".format(framerate))
    cmds.currentUnit(time=time_unit)
    return time_unit


def set_scene_scale(scene_scale):
    """Sets the Maya scene linear unit.

    Args:
        scene_scale (str): Maya linear unit, e.g. cm, m, in, ft.

    Returns:
        str: Applied linear unit.
    """
    cmds = get_maya_cmds()
    scene_scale = str(scene_scale or "cm").lower()
    cmds.currentUnit(linear=scene_scale)
    return scene_scale


def set_scene_up_axis(scene_up_axis):
    """Sets the Maya scene up axis.

    Args:
        scene_up_axis (str): Up axis, either Y or Z.

    Returns:
        str: Applied up axis.
    """
    cmds = get_maya_cmds()
    scene_up_axis = str(scene_up_axis or "y").lower()
    cmds.upAxis(axis=scene_up_axis, rotateView=False)
    return scene_up_axis


def apply_scene_options(settings):
    """Applies optional Maya scene settings from task data.

    Args:
        settings (dict): Task settings.

    Returns:
        dict: Applied option values keyed by option name.
    """
    settings = settings or {}
    applied_options = {}
    if settings.get("set_framerate"):
        applied_options["framerate"] = set_framerate(settings.get("framerate") or 24)
    if settings.get("set_scene_scale"):
        applied_options["scene_scale"] = set_scene_scale(settings.get("scene_scale") or "cm")
    if settings.get("set_scene_up_axis"):
        applied_options["scene_up_axis"] = set_scene_up_axis(settings.get("scene_up_axis") or "Y")
    return applied_options


def save_scene(file_path, file_type=None):
    """Saves the current Maya scene.

    Args:
        file_path (str): Destination Maya scene path.
        file_type (str, optional): Maya file type. If omitted, inferred from extension.

    Returns:
        str: Saved file path.
    """
    cmds = get_maya_cmds()
    output_dir = os.path.dirname(file_path)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    file_type = file_type or get_maya_file_type(file_path)
    cmds.file(rename=file_path)
    cmds.file(save=True, force=True, type=file_type)
    return file_path


def get_maya_file_type(file_path_or_extension):
    """Gets the Maya file type string for a path or extension.

    Args:
        file_path_or_extension (str): File path or extension.

    Returns:
        str: Maya file type string.

    Raises:
        ValueError: If the extension is unsupported.
    """
    extension = str(file_path_or_extension or "").lower()
    if not extension.startswith("."):
        extension = os.path.splitext(extension)[1].lower()
    if extension == ".ma":
        return "mayaAscii"
    if extension == ".mb":
        return "mayaBinary"
    raise ValueError("Unsupported Maya file extension: {0}".format(extension))
