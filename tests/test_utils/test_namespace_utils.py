import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from tests import maya_test_tools
from utils import namespace_utils


def import_namespace_test_scene():
    """
    Open files from inside the test_*/data folder/cube_namespaces.mb
    Scene contains a cube named: "parentNS:childNS:grandchildNS:pCube1"
    """
    maya_test_tools.import_data_file("cube_namespaces.mb")


class TestNamespaceUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

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
            result = maya_test_tools.list_objects(stripped_nodes)
            expected = ['pCube1']
            self.assertEqual(expected, result)
