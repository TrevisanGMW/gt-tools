"""
Scene Utilities
"""
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger("scene_utils")
logger.setLevel(logging.INFO)


def get_frame_rate():
    """
    Get the scene frame rate as a number
    Result:
        float describing the scene frame rate. If operation fails "0.0" is returned instead
    """
    playback_rate = cmds.currentUnit(query=True, time=True) or ""
    if playback_rate == 'film':
        return 24.0
    if playback_rate == 'show':
        return 48.0
    if playback_rate == 'pal':
        return 25.0
    if playback_rate == 'ntsc':
        return 30.0
    if playback_rate == 'palf':
        return 50.0
    if playback_rate == 'ntscf':
        return 60.0
    if 'fps' in playback_rate:
        return float(playback_rate.replace('fps', ''))
    logger.debug('Unable to detect scene frame rate. Returned "0.0".')
    return 0.0


def get_distance_in_meters():
    """
    Get the number units necessary to make a meter
    Returns:
        float describing the amount of units necessary to make a meter
    """
    unit = cmds.currentUnit(query=True, linear=True) or ""
    print("unit:" + str(unit))
    if unit == 'mm':
        return 1000
    elif unit == 'cm':
        return 100
    elif unit == 'km':
        return 0.001
    elif unit == 'in':
        return 39.3701
    elif unit == 'ft':
        return 3.28084
    elif unit == 'yd':
        return 1.09361
    elif unit == 'mi':
        return 0.000621371
    return 1


if __name__ == "__main__":
    from pprint import pprint
    out = None
    out = get_distance_in_meters()
    pprint(out)
