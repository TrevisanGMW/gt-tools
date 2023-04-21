import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_scene_utils")
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from utils import scene_utils


try:
    import maya.cmds as cmds
    import maya.standalone
    import maya.mel as mel
    import maya.OpenMaya as OpenMaya
except Exception as e:
    logger.debug(str(e))
    logger.warning("Unable load maya cmds, maya standalone, mel or OpenMaya")


def get_data_dir_path():
    """
    Returns:
        Path to the data folder. e.g. ".../test_utils/data"
    """
    return os.path.join(os.path.dirname(__file__), "data")


def get_test_file_path(file_name):
    """
    Open files from inside the test_*/data folder
    Args:
        file_name: Name of the file (must exist)
    """
    test_data_folder = get_data_dir_path()
    requested_file = os.path.join(test_data_folder, file_name)
    return requested_file


def import_scene(file_name):
    """
    Open files from inside the test_*/data folder
    Args:
        file_name: Name of the file (must exist)
    """
    file_to_import = get_test_file_path(file_name)
    cmds.file(file_to_import, i=True)


def import_namespace_test_scene():
    """
    Open files from inside the test_*/data folder/cube_namespaces.mb
    Scene contains a cube named: "parentNS:childNS:grandchildNS:pCube1"
    """
    import_scene("cube_namespaces.mb")


class TestSceneUtils(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    @classmethod
    def setUpClass(cls):
        maya.standalone.initialize()  # Start Maya Headless (mayapy.exe)

    def test_get_frame_rate(self):
        import_namespace_test_scene()
        expected = 24
        result = scene_utils.get_frame_rate()
        self.assertEqual(expected, result)

    def test_get_frame_rate_changed(self):
        import_namespace_test_scene()
        cmds.currentUnit(time="ntscf")
        expected = 60
        result = scene_utils.get_frame_rate()
        self.assertEqual(expected, result)

    def test_get_distance_in_meters(self):
        import_namespace_test_scene()
        expected = 100
        result = scene_utils.get_distance_in_meters()
        self.assertEqual(expected, result)
