"""
Scene Utilities
"""
import maya.cmds as cmds
import subprocess
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
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


def force_reload_file():
    """ Reopens the opened file (to revert any changes done to the file) """
    if cmds.file(query=True, exists=True):  # Check to see if it was ever saved
        file_path = cmds.file(query=True, expandName=True)
        if file_path is not None:
            cmds.file(file_path, open=True, force=True)
    else:
        cmds.warning('Unable to force reload. File was never saved.')


def open_file_dir():
    """Opens the directory where the Maya file is saved"""
    fail_message = 'Unable to open directory. Path printed to script editor instead.'

    def open_dir(path):
        """
        Open path
        Parameters:
            path (str): Path to open using
        """
        if sys.platform == "win32":  # Windows
            # explorer needs forward slashes
            filebrowser_path = os.path.join(os.getenv('WINDIR'), 'explorer.exe')
            path = os.path.normpath(path)

            if os.path.isdir(path):
                subprocess.run([filebrowser_path, path])
            elif os.path.isfile(path):
                subprocess.run([filebrowser_path, '/select,', path])
        elif sys.platform == "darwin":  # Mac-OS
            try:
                subprocess.call(["open", "-R", path])
            except Exception as exception:
                logger.debug(str(exception))
                print(path)
                cmds.warning(fail_message)
        else:  # Linux/Other
            print(path)
            cmds.warning(fail_message)

    if cmds.file(query=True, exists=True):  # Check to see if it was ever saved
        file_path = cmds.file(query=True, expandName=True)
        if file_path is not None:
            try:
                open_dir(file_path)
            except Exception as e:
                logger.debug(str(e))
                print(file_path)
                cmds.warning(fail_message)
    else:
        cmds.warning('Unable to open directory. File was never saved.')


if __name__ == "__main__":
    from pprint import pprint
    out = None
    out = get_distance_in_meters()
    pprint(out)
