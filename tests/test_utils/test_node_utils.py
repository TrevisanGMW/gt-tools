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
from gt.utils import node_utils


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
        self.assertEqual(f'|{cube}', str(result))

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

    def test_node_string_conversion(self):
        cube = maya_test_tools.create_poly_cube()
        node = Node(path=cube)
        maya_test_tools.cmds.setAttr(f"{node}.ty", 5)
        result = maya_test_tools.cmds.getAttr(f"{node}.ty")
        expected = 5
        self.assertEqual(expected, result)
        expected = '|pCube1'
        result = str(node)
        self.assertEqual(expected, result)

    def test_node_string_conversion_non_unique(self):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        node = Node(path=cube_one)
        group = maya_test_tools.cmds.group(empty=True, world=True, name="group")
        maya_test_tools.cmds.parent(cube_two, group)
        maya_test_tools.cmds.rename(cube_one, "mocked_name")
        maya_test_tools.cmds.rename(cube_two, "mocked_name")
        maya_test_tools.cmds.setAttr(f"{node}.ty", 5)
        result = maya_test_tools.cmds.getAttr(f"{node}.ty")
        expected = 5
        self.assertEqual(expected, result)

    def test_node_string_conversion_add(self):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        node_one = Node(path=cube_one)
        node_two = Node(path=cube_two)

        result = node_one + " mocked string " + node_two
        expected = "|pCube1 mocked string |pCube2"
        self.assertEqual(expected, result)
        result = "cube_one " + node_one
        expected = "cube_one |pCube1"
        self.assertEqual(expected, result)

    def test_node_with_non_string_operand(self):
        cube_one = maya_test_tools.create_poly_cube()
        node_one = Node(cube_one)
        with self.assertRaises(TypeError):
            result = node_one + 42  # 42 is not a string, TypeError

    def test_node_inheritance(self):
        cube_one = maya_test_tools.create_poly_cube()
        node_one = Node(cube_one)
        self.assertTrue(isinstance(node_one, str))

    def test_node_rename(self):
        cube_one = maya_test_tools.create_poly_cube()
        node_one = Node(cube_one)
        node_one.rename("mockedName")
        expected = "mockedName"
        result = node_one.get_short_name()
        self.assertEqual(expected, result)

    def test_node_string_cmds_use(self):
        cube_one = maya_test_tools.create_poly_cube()
        group = maya_test_tools.cmds.group(name="group", empty=True, world=True)
        a_node = Node(path=cube_one)
        maya_test_tools.cmds.parent(a_node, group)
        a_node.rename("mockedName")
        maya_test_tools.cmds.parent(a_node, world=True)
        expected = "mockedName"
        result = a_node.get_short_name()
        self.assertEqual(expected, result)
        expected = "|mockedName"
        result = a_node.get_long_name()
        self.assertEqual(expected, result)

    def test_node_is_unique_false(self):
        cube = maya_test_tools.create_poly_cube(name="cube_one")
        cube_node = Node(path=cube)
        group_one = maya_test_tools.cmds.group(name="group1", empty=True, world=True)
        maya_test_tools.cmds.parent(cube_node, group_one)

        cube_b = maya_test_tools.create_poly_cube(name="cube_one")
        cube_b_node = Node(path=cube_b)
        group_two = maya_test_tools.cmds.group(name="group2", empty=True, world=True)
        maya_test_tools.cmds.parent(cube_b_node, group_two)

        self.assertFalse(cube_node.is_unique(), "Node is unique, but it should not be.")
        self.assertFalse(cube_b_node.is_unique(), "Node is unique, but it should not be.")

    def test_node_is_unique_true(self):
        cube = maya_test_tools.create_poly_cube(name="cube_one")
        cube_node = Node(path=cube)
        group_one = maya_test_tools.cmds.group(name="group1", empty=True, world=True)
        maya_test_tools.cmds.parent(cube_node, group_one)

        cube_b = maya_test_tools.create_poly_cube(name="cube_two")
        cube_b_node = Node(path=cube_b)
        group_two = maya_test_tools.cmds.group(name="group2", empty=True, world=True)
        maya_test_tools.cmds.parent(cube_b_node, group_two)

        self.assertTrue(cube_node.is_unique(), "Node is not unique, but it should be.")
        self.assertTrue(cube_b_node.is_unique(), "Node is not unique, but it should be.")

    def test_node_str_add_radd(self):
        cube = maya_test_tools.create_poly_cube(name="cube_one")
        cube_node = Node(path=cube)

        expected = "|cube_one"
        result = cube_node.get_long_name()
        self.assertEqual(expected, result)

        expected = "|cube_one_test"
        result = cube_node + "_test"
        self.assertEqual(expected, result)

        expected = "test_|cube_one"
        result = "test_" + cube_node
        self.assertEqual(expected, result)

    def test_node_len(self):
        cube = maya_test_tools.create_poly_cube(name="cube_one")
        cube_node = Node(path=cube)

        expected = 9
        result = len(cube_node)
        self.assertEqual(expected, result)

    def test_node_namespaces(self):
        maya_test_tools.import_data_file("cube_namespaces.ma")
        node_to_test = Node("parentNS:childNS:grandChildNS:pCube1")
        expected = ['parentNS', 'childNS', 'grandChildNS']
        result = node_to_test.get_namespaces(root_only=False)
        self.assertEqual(expected, result)

    def test_node_namespaces_root_only(self):
        maya_test_tools.import_data_file("cube_namespaces.ma")
        node_to_test = Node("parentNS:childNS:grandChildNS:pCube1")
        expected = ['parentNS']
        result = node_to_test.get_namespaces(root_only=True)
        self.assertEqual(expected, result)

    def test_node_equality(self):
        cube = maya_test_tools.create_poly_cube(name="cube_one")
        node_one = Node(cube)
        node_two = Node(cube)
        self.assertEqual(node_one, node_two)

    def test_create_node_transform(self):
        result = node_utils.create_node("transform", name="mockedName", shared=False)
        expected = Node("|mockedName")
        self.assertEqual(expected, result)
        expected = "|mockedName"
        self.assertEqual(expected, result)

    def test_create_node_no_name(self):
        result = node_utils.create_node("transform", name=None, shared=False)
        expected = Node("|transform1")
        self.assertEqual(expected, result)
        expected = "|transform1"
        self.assertEqual(expected, result)

    def test_create_node_shared(self):
        result_one = node_utils.create_node("transform", name="mockedName", shared=True)
        result_two = node_utils.create_node("transform", name="mockedName", shared=True)
        expected = Node("|mockedName")
        self.assertEqual(expected, result_one)
        self.assertEqual(expected, result_two)
        self.assertFalse(maya_test_tools.cmds.objExists("mockedName1"))
