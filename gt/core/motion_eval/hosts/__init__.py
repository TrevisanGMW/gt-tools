"""
Motion Evaluation Hosts - The only code that talks to a DCC (Maya, Blender) or reads scene files.

    get_host("auto")    the host of the running program: Blender inside Blender, Maya when
                        maya.cmds can be imported, otherwise the plain-Python sample host
    get_host("maya")    a specific host ("maya", "blender", or "sample")

Hosts are created once and reused. Every host implements host_base.SceneHost; nothing
outside this folder may import maya or bpy. See README.md ("Hosts") to add one.
"""

import contextlib

HOST_AUTO = "auto"
HOST_MAYA = "maya"
HOST_BLENDER = "blender"
HOST_SAMPLE = "sample"
HOST_NAMES = [HOST_MAYA, HOST_BLENDER, HOST_SAMPLE]
HOST_LABELS = {HOST_AUTO: "Auto", HOST_MAYA: "Maya", HOST_BLENDER: "Blender", HOST_SAMPLE: "Python (motion samples)"}

_HOSTS = {}
_active_host_name = None
_detected_host_name = None


def create_host(name):
    """Creates a new host instance.

    Args:
        name (str): One of HOST_NAMES.

    Returns:
        SceneHost: New host.

    Raises:
        ValueError: If the name is unknown.
    """
    if name == HOST_MAYA:
        from .maya_host import MayaHost

        return MayaHost()
    if name == HOST_BLENDER:
        from .blender_host import BlenderHost

        return BlenderHost()
    if name == HOST_SAMPLE:
        from .sample_host import SampleHost

        return SampleHost()
    raise ValueError(f'Unknown host "{name}". Use one of: {", ".join([HOST_AUTO] + HOST_NAMES)}.')


def detect_host_name():
    """Finds the host of the running program.

    Order: a Maya that is already running (GUI or maya.standalone) always wins, so Maya tools
    never switch host; then Blender; then mayapy (Maya importable but not started yet);
    otherwise plain Python. The result is remembered once a DCC is found.

    Returns:
        str: HOST_BLENDER, HOST_MAYA, or HOST_SAMPLE.
    """
    global _detected_host_name
    if _detected_host_name is not None:
        return _detected_host_name
    maya_host = get_host(HOST_MAYA)
    if maya_host.is_running():
        _detected_host_name = HOST_MAYA
    elif get_host(HOST_BLENDER).is_available():
        _detected_host_name = HOST_BLENDER
    elif maya_host.is_available():
        _detected_host_name = HOST_MAYA
    return _detected_host_name or HOST_SAMPLE


def resolve_host_name(name=None):
    """Turns "auto" (or None) into a concrete host name.

    Args:
        name (str, optional): Host name, "auto", or None (the active host, else auto).

    Returns:
        str: One of HOST_NAMES.
    """
    if not name:
        name = _active_host_name or HOST_AUTO
    name = str(name).lower()
    return detect_host_name() if name == HOST_AUTO else name


def get_host(name=None):
    """Gets a shared host instance.

    Args:
        name (str, optional): Host name, "auto", or None (the active host set by set_active_host,
            otherwise auto-detected).

    Returns:
        SceneHost: Host.
    """
    name = str(name).lower() if name else None
    if name not in HOST_NAMES:
        name = resolve_host_name(name)
    if name not in _HOSTS:
        _HOSTS[name] = create_host(name)
    return _HOSTS[name]


def set_active_host(name=None):
    """Chooses the host used when callers do not name one (sampling, scene_io, runner).

    Args:
        name (str, optional): Host name, or None/"auto" to go back to auto-detection.

    Returns:
        SceneHost: The host now active.
    """
    global _active_host_name
    _active_host_name = None if not name or str(name).lower() == HOST_AUTO else resolve_host_name(name)
    return get_host()


def get_scene_extensions(name=None):
    """Gets the file extensions a host can load.

    Args:
        name (str, optional): Host name (see get_host).

    Returns:
        tuple: Lowercase extensions such as ".fbx".
    """
    return tuple(get_host(name).scene_extensions)


@contextlib.contextmanager
def use_host(name=None):
    """Makes a host active inside a block, then restores the previous one.

    Args:
        name (str, optional): Host name or "auto".

    Yields:
        SceneHost: The active host inside the block.
    """
    global _active_host_name
    previous = _active_host_name
    set_active_host(name)
    try:
        yield get_host()
    finally:
        _active_host_name = previous
