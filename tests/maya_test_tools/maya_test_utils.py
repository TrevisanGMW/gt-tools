try:
    import maya.cmds as cmds
    import maya.OpenMaya as OpenMaya
    import maya.api.OpenMaya as om
    import maya.mel as mel
except ModuleNotFoundError:
    from tests.maya_test_tools.maya_spoof import MayaCmdsSpoof as cmds
    from tests.maya_test_tools.maya_spoof import OpenMayaSpoof as OpenMaya
    from tests.maya_test_tools.maya_spoof import OpenMayaApiSpoof as om
    from tests.maya_test_tools.maya_spoof import MayaMelSpoof as mel

import logging
import inspect
import sys
import os

logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def force_new_scene():
    """
    Force open new empty scene
    """
    cmds.file(new=True, force=True)


def create_poly_cube(*args, **kwargs):
    """
    Creates poly cube
    """
    cmds.polyCube(*args, **kwargs)


def get_data_dir_path():
    """
    Get a path to the data folder using the path from where this script was called.
    Returns:
        Path to the data folder of the caller script.
        pattern:  ".../<caller-script-dir>/data"
        e.g. If the function was called from a script inside "test_utils"
             then the output would be ".../test_utils/data"
             ("..." being the variable portion of the directory path)
    """
    caller = inspect.getsourcefile(sys._getframe(1))
    return os.path.join(os.path.dirname(caller), "data")


def get_data_file_path(file_name):
    """
    Open files from inside the test_*/data folder
    Args:
        file_name: Name of the file (must exist)
    """
    test_data_folder = get_data_dir_path()
    requested_file = os.path.join(test_data_folder, file_name)
    return requested_file


def load_plugins(plugin_list):
    """
    Load provided plug-ins.

    Parameters:
        plugin_list (list): A list of strings containing the name of the plugins that were loaded.
                            If a string is provided, it will be automatically converted to a list
    """
    if isinstance(plugin_list, str):
        plugin_list = [plugin_list]

    now_loaded = []

    # Load Plug-in
    for plugin in plugin_list:
        if not cmds.pluginInfo(plugin, q=True, loaded=True):
            try:
                cmds.loadPlugin(plugin)
                if cmds.pluginInfo(plugin, q=True, loaded=True):
                    now_loaded.append(plugin)
            except Exception as e:
                logger.debug(e)
    return now_loaded


def import_file(file_path):
    """
    Opens file_path in Maya using "cmds.file_path()"
    Parameters:
        file_path (str): Path to the file_path to open

    Returns:
        str: Imported objects. (result of the "cmds.file(returnNewNodes=True)" function)
    """
    if file_path.split('.')[-1] == 'fbx':  # Make sure "fbxmaya" is available
        load_plugins(['fbxmaya'])
    files = cmds.file(file_path, i=True, returnNewNodes=True, force=True)
    return files


def open_file(file_path):
    """
    Opens file in Maya using "cmds.file()"
    Parameters:
        file_path (str): Path to the file to open

    Returns:
        str: Opened file. (result of the "cmds.file()" function)

    """
    return cmds.file(file_path, open=True, force=True)


def import_data_file(file_name):
    """
    Open files from inside the test_*/data folder.
    It automatically determines the location of the data folder using "get_data_dir_path()"
    Args:
        file_name: Name of the file_path (must exist)
    """
    file_to_import = get_data_file_path(file_name)
    cmds.file(file_to_import, i=True)


def open_data_file(file_name):
    """
    Open files from inside the test_*/data folder.
    It automatically determines the location of the data folder using "get_data_dir_path()"
    Args:
        file_name: Name of the file (must exist)
    """
    file_to_import = get_data_file_path(file_name)
    open_file(file_to_import)


def import_maya_standalone(initialize=True):
    """
    Imports Maya Standalone
    Parameters:
        initialize (bool, optional) If true, it will also attempt to initialize "maya.standalone" using "initialize()"
    """
    try:
        import maya.standalone as maya_standalone
    except ModuleNotFoundError:
        from tests.maya_test_tools.maya_spoof import MayaStandaloneSpoof as maya_standalone
    if initialize:
        maya_standalone.initialize()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
