import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_namespace_utils")
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from utils import namespace_utils


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


class TestStringUtils(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    @classmethod
    def setUpClass(cls):
        maya.standalone.initialize()  # Start Maya Headless (mayapy.exe)

    def test_get_namespaces_string(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        expected = ['parentNS:childNS:grandChildNS']
        result = namespace_utils.get_namespaces(obj_list=object_to_test)
        self.assertEqual(expected, result)

    def test_get_namespaces_list(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        expected = ['parentNS:childNS:grandChildNS']
        result = namespace_utils.get_namespaces(obj_list=[object_to_test])
        self.assertEqual(expected, result)

    def test_namespaces_split(self):
        expected = ('one:two', 'three')
        result = namespace_utils.namespaces_split("|root|child|grandChild|one:two:three")
        self.assertEqual(expected, result)

    def test_get_namespace_hierarchy_list(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        expected = ['parentNS', 'childNS', 'grandChildNS']
        result = namespace_utils.get_namespace_hierarchy_list(obj=object_to_test)
        self.assertEqual(expected, result)

    def test_get_namespace_hierarchy_list_parent(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        expected = ['parentNS']
        result = namespace_utils.get_namespace_hierarchy_list(obj=object_to_test, top_parent_only=True)
        self.assertEqual(expected, result)

    def test_strip_namespace(self):
        import_namespace_test_scene()
        with namespace_utils.StripNamespace('parentNS:childNS:grandChildNS:') as stripped_nodes:
            result = cmds.ls(stripped_nodes)
            expected = ['pCube1']
            self.assertEqual(expected, result)
