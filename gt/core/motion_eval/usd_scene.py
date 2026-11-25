"""
Loads USD animation files into Maya so they can be evaluated like Maya scenes.

Maya runtime module (Maya, the mayaUsdPlugin, and pxr are imported lazily).

Loading a USD file:
    1. Starts a new scene and sets its frame rate to the file's time codes per second,
       so every USD time code lands on one Maya frame.
    2. Imports the file with mayaUSDImport (skeleton animation becomes keyed joints). The
       importer's own axis and unit conversion (on by default in Maya 2026 and later) is
       turned off, so every Maya version imports the same way.
    3. Sets the playback and animation range to the file's start and end time codes.
    4. Optionally aligns the file to the scene: USD files are often Z up (for example
       exported with "Force Z Up") while Maya scenes are Y up. The imported top nodes are
       grouped under "usd_align" and rotated (and scaled when the file's meters per unit
       differ from the scene unit), so the checks see a Y-up character in scene units.
"""

import os

USD_EXTENSIONS = (".usd", ".usda", ".usdc")
USD_PLUGIN_NAME = "mayaUsdPlugin"
ALIGN_GROUP_NAME = "usd_align"
TIME_UNITS = {24.0: "film", 25.0: "pal", 30.0: "ntsc", 48.0: "show", 50.0: "palf", 60.0: "ntscf"}
METERS_PER_SCENE_UNIT = {"mm": 0.001, "cm": 0.01, "m": 1.0, "km": 1000.0, "in": 0.0254, "ft": 0.3048,
                         "yd": 0.9144, "mi": 1609.344}


def is_usd_file(file_path):
    """Checks whether a path is a USD file.

    Args:
        file_path (str): File path.

    Returns:
        bool: True for .usd, .usda, and .usdc files.
    """
    return os.path.splitext(str(file_path))[1].lower() in USD_EXTENSIONS


def get_time_unit(frames_per_second):
    """Gets the Maya time unit for a frame rate.

    Args:
        frames_per_second (float): Frames per second.

    Returns:
        str: Maya time unit, for example "ntsc" for 30, or "12fps" for rates without a named unit.
    """
    rate = float(frames_per_second)
    if rate in TIME_UNITS:
        return TIME_UNITS[rate]
    return f"{int(round(rate))}fps"


def get_up_axis_rotation(file_up_axis, scene_up_axis):
    """Gets the X rotation that turns a file's up axis into the scene's up axis.

    Args:
        file_up_axis (str): "y" or "z".
        scene_up_axis (str): "y" or "z".

    Returns:
        float: Degrees around X (-90 for Z up into Y up, 90 for Y up into Z up, 0 when they match).
    """
    file_up_axis = str(file_up_axis).lower()
    scene_up_axis = str(scene_up_axis).lower()
    if file_up_axis == scene_up_axis:
        return 0.0
    return -90.0 if file_up_axis == "z" else 90.0


def get_unit_scale(meters_per_unit, scene_unit):
    """Gets the scale that converts file units into scene units.

    Args:
        meters_per_unit (float): The file's metersPerUnit (0.01 for centimeters).
        scene_unit (str): Maya linear unit such as "cm".

    Returns:
        float: Scale factor (1.0 when the units match or are unknown).
    """
    scene_meters = METERS_PER_SCENE_UNIT.get(str(scene_unit))
    if not meters_per_unit or not scene_meters:
        return 1.0
    return float(meters_per_unit) / scene_meters


def read_stage_info(file_path):
    """Reads the timing and axis metadata of a USD file.

    Args:
        file_path (str): USD path.

    Returns:
        dict: "up_axis" ("y"/"z"), "meters_per_unit", "fps", "start", and "end" (None when not authored).
    """
    from pxr import Usd, UsdGeom

    stage = Usd.Stage.Open(str(file_path))
    has_range = stage.HasAuthoredMetadata("startTimeCode") and stage.HasAuthoredMetadata("endTimeCode")
    return {
        "up_axis": str(UsdGeom.GetStageUpAxis(stage)).lower(),
        "meters_per_unit": UsdGeom.GetStageMetersPerUnit(stage),
        "fps": stage.GetTimeCodesPerSecond(),
        "start": stage.GetStartTimeCode() if has_range else None,
        "end": stage.GetEndTimeCode() if has_range else None,
    }


def import_usd_file(file_path):
    """Imports a USD file with its animation, without the importer's own axis and unit conversion.

    Newer mayaUsd versions (Maya 2026 and later) convert the up axis and unit on import by
    default, older ones do not. The conversion is turned off where it exists, so every Maya
    version imports the same way and load_usd_scene aligns the file exactly once.

    Args:
        file_path (str): USD path.
    """
    import maya.cmds as cmds

    path = str(file_path).replace("\\", "/")
    try:
        cmds.mayaUSDImport(file=path, readAnimData=True, upAxis=False, unit=False)
    except TypeError:
        cmds.mayaUSDImport(file=path, readAnimData=True)


def load_usd_scene(file_path, align_up_axis=True):
    """Opens a USD file in a new Maya scene, ready to evaluate.

    Args:
        file_path (str): USD path.
        align_up_axis (bool): Rotate and scale the imported nodes into the scene's up axis and unit.

    Returns:
        dict: Stage info (see read_stage_info) plus "rotation", "scale", and "align_group" (or "").

    Raises:
        RuntimeError: If the mayaUsdPlugin cannot be loaded.
    """
    import maya.cmds as cmds

    cmds.file(new=True, force=True)
    if not cmds.pluginInfo(USD_PLUGIN_NAME, query=True, loaded=True):
        try:
            cmds.loadPlugin(USD_PLUGIN_NAME, quiet=True)
        except RuntimeError as error:
            raise RuntimeError(f"USD files need the {USD_PLUGIN_NAME} plug-in: {error}")
    info = read_stage_info(file_path)
    cmds.currentUnit(time=get_time_unit(info["fps"]))
    before = set(cmds.ls(assemblies=True, long=True) or [])
    import_usd_file(file_path)
    imported = [node for node in cmds.ls(assemblies=True, long=True) or [] if node not in before]
    if info["start"] is not None and info["end"] is not None:
        cmds.playbackOptions(minTime=info["start"], maxTime=info["end"],
                             animationStartTime=info["start"], animationEndTime=info["end"])
    info.update({"rotation": 0.0, "scale": 1.0, "align_group": ""})
    if align_up_axis and imported:
        info["rotation"] = get_up_axis_rotation(info["up_axis"], cmds.upAxis(query=True, axis=True))
        info["scale"] = get_unit_scale(info["meters_per_unit"], cmds.currentUnit(query=True, linear=True))
        if info["rotation"] or abs(info["scale"] - 1.0) > 1e-6:
            group = cmds.group(imported, name=ALIGN_GROUP_NAME)
            cmds.xform(group, pivots=(0, 0, 0), worldSpace=True)
            cmds.setAttr(f"{group}.rotateX", info["rotation"])
            cmds.setAttr(f"{group}.scale", info["scale"], info["scale"], info["scale"])
            info["align_group"] = group
    return info
