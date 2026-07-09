"""
Retargeter Constants

Import Line:
    import gt.tools.retargeter.retargeter_constants as tools_rt_const
"""
import gt.core.prefs as core_prefs
import pathlib
import os


class RetargeterConstants:
    def __init__(self):
        """
        Constant values used by the Retargeting System.
        e.g. Attribute names, dictionary keys or initial values.
        """

    # General Keys and Attributes
    RIG_MA_EXTENSION = "ma"
    RIG_MB_EXTENSION = "mb"
    FBX_EXTENSION = "fbx"
    DATA_EXTENSION = "rtg"
    BASE_FILTER = "All Files (*);;Retarget Definitions (*.rtg);;JSON Files (*.json)"
    DATA_FILTER = f"Retarget Definition (*.{DATA_EXTENSION})"
    RETARGET_FILTER = f"FBX, MA, MB Files (*.{RIG_MA_EXTENSION} *.{RIG_MB_EXTENSION} *.{FBX_EXTENSION})"
    # Preferences Filename
    PREFS_FILENAME = "retargeter"
    # Attributes
    ATTR_RETARGET_STATE = "retargeted"
    # Paths
    _PREFS_DIR = core_prefs.Prefs(PREFS_FILENAME).get_dir_path()
    DEFAULT_DEFINITION_FOLDER = pathlib.Path(os.path.join(_PREFS_DIR, f"{PREFS_FILENAME}_definitions")).as_posix()
    DEFAULT_REFERENCES_FOLDER = pathlib.Path(os.path.join(_PREFS_DIR, f"{PREFS_FILENAME}_references")).as_posix()
    DEFAULT_ROM_DATA_FOLDER = pathlib.Path(os.path.join(_PREFS_DIR, f"{PREFS_FILENAME}_rom_data")).as_posix()
