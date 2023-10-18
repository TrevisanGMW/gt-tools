import unittest
import logging
import sys
import os

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
from tests import maya_test_tools
from gt.utils.node_utils import Node


class TestNodeUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    def test_node_init(self):
        cube = maya_test_tools.create_poly_cube()
        result = Node(path=cube)
        expected = maya_test_tools.cmds.ls(cube, uuid=True)[0]
        self.assertEqual(expected, result.uuid)
        self.assertEqual(cube, result)

    def test_node_get_uuid(self):
        cube = maya_test_tools.create_poly_cube()
        result = Node(path=cube)
        expected = maya_test_tools.cmds.ls(cube, uuid=True)[0]
        self.assertEqual(expected, result.get_uuid())

    def test_node_get_long_name(self):
        cube = maya_test_tools.create_poly_cube()
        group = maya_test_tools.cmds.group(empty=True, world=True, name="parent")
        maya_test_tools.cmds.parent(cube, group)
        node = Node(path=cube)
        result = node.get_long_name()
        expected = "|parent|pCube1"
        self.assertEqual(expected, result)

    def test_node_get_short_name(self):
        cube = maya_test_tools.create_poly_cube()
        group = maya_test_tools.cmds.group(empty=True, world=True, name="parent")
        maya_test_tools.cmds.parent(cube, group)
        node = Node(path=cube)
        result = node.get_short_name()
        expected = "pCube1"
        self.assertEqual(expected, result)

    def test_node_is_dag_true(self):
        cube = maya_test_tools.create_poly_cube()
        node = Node(path=cube)
        result = node.is_dag()
        expected = True
        self.assertEqual(expected, result)

    def test_node_is_dag_false(self):
        cube = maya_test_tools.cmds.createNode("multiplyDivide")
        node = Node(path=cube)
        result = node.is_dag()
        expected = False
        self.assertEqual(expected, result)

    def test_node_is_transform(self):
        cube = maya_test_tools.create_poly_cube()
        node = Node(path=cube)
        result = node.is_transform()
        expected = True
        self.assertEqual(expected, result)

    def test_node_is_transform_false(self):
        cube = maya_test_tools.cmds.createNode("multiplyDivide")
        node = Node(path=cube)
        result = node.is_transform()
        expected = False
        self.assertEqual(expected, result)

    def test_node_exists_true(self):
        cube = maya_test_tools.create_poly_cube()
        node = Node(path=cube)
        result = node.exists()
        expected = True
        self.assertEqual(expected, result)

    def test_node_exists_false(self):
        cube = maya_test_tools.create_poly_cube()
        node = Node(path=cube)
        maya_test_tools.cmds.delete(cube)
        result = node.exists()
        expected = False
        self.assertEqual(expected, result)

    def test_node_get_shape_types(self):
        cube = maya_test_tools.create_poly_cube()
        node = Node(path=cube)
        result = node.get_shape_types()
        expected = ['mesh']
        self.assertEqual(expected, result)
