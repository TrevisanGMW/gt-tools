import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Utility and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tests import maya_test_tools
from gt.core import namespace as core_namespace
cmds = maya_test_tools.cmds


def import_namespace_test_scene():
    """
    Open files from inside the test_*/data folder/cube_namespaces.mb
    Scene contains a cube named: "parentNS:childNS:grandchildNS:pCube1"
    """
    maya_test_tools.import_data_file("cube_namespaces.ma")


class TestNamespaceCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_namespaces_string(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        expected = ['parentNS:childNS:grandChildNS']
        result = core_namespace.get_namespaces(obj_list=object_to_test)
        self.assertEqual(expected, result)

    def test_get_namespaces_list(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        expected = ['parentNS:childNS:grandChildNS']
        result = core_namespace.get_namespaces(obj_list=[object_to_test])
        self.assertEqual(expected, result)

    def test_get_namespace(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        expected = 'parentNS:childNS:grandChildNS'
        result = core_namespace.get_namespace(node=object_to_test)
        self.assertEqual(expected, result)

    def test_get_namespace_first_in_dag_path(self):
        object_to_test = "|first:root|second:control"
        expected = "first"
        result = core_namespace.get_namespace(node=object_to_test, first_in_path=True)
        self.assertEqual(expected, result)

    def test_get_namespace_free_path(self):
        object_to_test = "|first:rig|second:control"
        expected = "|rig|control"
        result = core_namespace.get_namespace_free_path(object_to_test)
        self.assertEqual(expected, result)

    def test_replace_namespace_in_path(self):
        object_to_test = "|source:rig|source:control"
        expected = "|target:rig|target:control"
        result = core_namespace.replace_namespace_in_path(
            object_to_test,
            source_namespace="source",
            target_namespace="target",
        )
        self.assertEqual(expected, result)

    def test_namespaces_split(self):
        expected = ('one:two', 'three')
        result = core_namespace.namespaces_split("|root|child|grandChild|one:two:three")
        self.assertEqual(expected, result)

    def test_get_namespace_hierarchy_list(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        expected = ['parentNS', 'childNS', 'grandChildNS']
        result = core_namespace.get_namespace_hierarchy_list(obj=object_to_test)
        self.assertEqual(expected, result)

    def test_get_namespace_hierarchy_list_root(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        expected = ['parentNS']
        result = core_namespace.get_namespace_hierarchy_list(obj=object_to_test, root_only=True)
        self.assertEqual(expected, result)

    def test_strip_namespace(self):
        import_namespace_test_scene()
        with core_namespace.StripNamespace('parentNS:childNS:grandChildNS:') as stripped_nodes:
            result = cmds.ls(stripped_nodes)
            expected = ['pCube1']
            self.assertEqual(expected, result)

    def test_strip_namespace_from_item(self):
        import_namespace_test_scene()
        object_to_test = "parentNS:childNS:grandChildNS:pCube1"
        namespace = core_namespace.get_namespace(node=object_to_test)
        with core_namespace.StripNamespace(namespace) as stripped_nodes:
            result = cmds.ls(stripped_nodes)
            expected = ['pCube1']
            self.assertEqual(expected, result)
