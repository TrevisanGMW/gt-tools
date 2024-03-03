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
from gt.utils import hierarchy_utils
from gt.utils.node_utils import Node
cmds = maya_test_tools.cmds


class TestHierarchyUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        self.cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        self.cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        self.cube_three = maya_test_tools.create_poly_cube(name="cube_three")
        self.transform_one = cmds.group(name="transform_one", empty=True, world=True)
        self.transform_two = cmds.group(name="transform_two", empty=True, world=True)
        self.cubes = [self.cube_one, self.cube_two, self.cube_three]
        self.transforms = [self.transform_one, self.transform_two]

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_parent_basics(self):
        result = hierarchy_utils.parent(source_objects=self.cubes, target_parent=self.transform_one)
        expected = []
        for cube in self.cubes:
            expected.append(f"|{self.transform_one}|{cube}")
        self.assertEqual(expected, result)
        expected = self.cubes
        children = cmds.listRelatives(self.transform_one, children=True)
        self.assertEqual(expected, children)

    def test_parent_str_input(self):
        result = hierarchy_utils.parent(source_objects=self.cube_one, target_parent=self.transform_one)
        expected = [f'|{self.transform_one}|{self.cube_one}']
        self.assertEqual(expected, result)
        expected = [self.cube_one]
        children = cmds.listRelatives(self.transform_one, children=True)
        self.assertEqual(expected, children)

    def test_parent_non_unique(self):
        hierarchy_utils.parent(source_objects=self.cube_one, target_parent=self.transform_one)
        cmds.rename(self.cube_two, "cube_one")
        result = hierarchy_utils.parent(source_objects="|cube_one", target_parent=self.transform_two)
        expected = [f"|{self.transform_two}|cube_one"]
        self.assertEqual(expected, result)
        children = cmds.listRelatives(self.transform_two, children=True, fullPath=True)
        self.assertEqual(expected, children)

    def test_parent_with_nodes(self):
        cube_one_node = Node(self.cube_one)
        transform_one_node = Node(self.transform_one)
        result = hierarchy_utils.parent(source_objects=cube_one_node, target_parent=transform_one_node, verbose=True)

        expected = [f"|{self.transform_one}|{self.cube_one}"]
        self.assertEqual(expected, result)
        children = cmds.listRelatives(self.transform_one, children=True, fullPath=True)
        self.assertEqual(expected, children)

    def test_add_offset_transform(self):
        cube_one_node = Node(self.cube_one)
        cmds.parent(self.cube_one, self.transform_one)
        cmds.setAttr(f'{self.transform_one}.ty', 15)
        cmds.setAttr(f'{self.cube_one}.ty', 5)

        expected = f"|{self.transform_one}|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        created_offsets = hierarchy_utils.add_offset_transform(target_list=cube_one_node,
                                                               transform_type="group",
                                                               pivot_source="target",
                                                               transform_suffix="offset")

        expected = f"|{self.transform_one}|cube_one_offset|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        expected = [f"|{self.transform_one}|cube_one_offset"]
        self.assertEqual(expected, created_offsets)

        expected = "transform"
        result = cmds.objectType(created_offsets[0])
        self.assertEqual(expected, result)

        expected = 5
        result = cmds.getAttr(f'{created_offsets[0]}.ty')
        self.assertEqual(expected, result)

    def test_add_offset_transform_joint(self):
        cube_one_node = Node(self.cube_one)
        cmds.parent(self.cube_one, self.transform_one)
        cmds.setAttr(f'{self.transform_one}.ty', 15)
        cmds.setAttr(f'{self.cube_one}.ty', 5)

        expected = f"|{self.transform_one}|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        created_offsets = hierarchy_utils.add_offset_transform(target_list=cube_one_node,
                                                               transform_type="joint",
                                                               pivot_source="target",
                                                               transform_suffix="offset")

        expected = f"|{self.transform_one}|cube_one_offset|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        expected = [f"|{self.transform_one}|cube_one_offset"]
        self.assertEqual(expected, created_offsets)

        expected = "joint"
        result = cmds.objectType(created_offsets[0])
        self.assertEqual(expected, result)

        expected = 5
        result = cmds.getAttr(f'{created_offsets[0]}.ty')
        self.assertEqual(expected, result)

    def test_add_offset_transform_locator(self):
        cube_one_node = Node(self.cube_one)
        cmds.parent(self.cube_one, self.transform_one)
        cmds.setAttr(f'{self.transform_one}.ty', 15)
        cmds.setAttr(f'{self.cube_one}.ty', 5)

        expected = f"|{self.transform_one}|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        created_offsets = hierarchy_utils.add_offset_transform(target_list=cube_one_node,
                                                               transform_type="locator",
                                                               pivot_source="target",
                                                               transform_suffix="offset")

        expected = f"|{self.transform_one}|cube_one_offset|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        expected = [f"|{self.transform_one}|cube_one_offset"]
        self.assertEqual(expected, created_offsets)

        expected = "locator"
        child = cmds.listRelatives(created_offsets[0], shapes=True)[0]
        result = cmds.objectType(child)
        self.assertEqual(expected, result)

        expected = 5
        result = cmds.getAttr(f'{created_offsets[0]}.ty')
        self.assertEqual(expected, result)

    def test_add_offset_transform_pivot_parent(self):
        cube_one_node = Node(self.cube_one)
        cmds.parent(self.cube_one, self.transform_one)
        cmds.setAttr(f'{self.transform_one}.ty', 15)
        cmds.setAttr(f'{self.cube_one}.ty', 5)

        expected = f"|{self.transform_one}|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        created_offsets = hierarchy_utils.add_offset_transform(target_list=cube_one_node,
                                                               transform_type="group",
                                                               pivot_source="parent",
                                                               transform_suffix="offset")

        expected = f"|{self.transform_one}|cube_one_offset|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        expected = [f"|{self.transform_one}|cube_one_offset"]
        self.assertEqual(expected, created_offsets)

        expected = "transform"
        result = cmds.objectType(created_offsets[0])
        self.assertEqual(expected, result)

        expected = 0
        result = cmds.getAttr(f'{created_offsets[0]}.ty')
        self.assertEqual(expected, result)

    def test_add_offset_transform_suffix(self):
        cube_one_node = Node(self.cube_one)
        cmds.parent(self.cube_one, self.transform_one)
        cmds.setAttr(f'{self.transform_one}.ty', 15)
        cmds.setAttr(f'{self.cube_one}.ty', 5)

        expected = f"|{self.transform_one}|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        created_offsets = hierarchy_utils.add_offset_transform(target_list=cube_one_node,
                                                               transform_type="group",
                                                               pivot_source="parent",
                                                               transform_suffix="mocked_suffix")

        expected = f"|{self.transform_one}|cube_one_mocked_suffix|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        expected = [f"|{self.transform_one}|cube_one_mocked_suffix"]
        self.assertEqual(expected, created_offsets)

    def test_add_offset_transform_multiple(self):
        cube_one_node = Node(self.cube_one)
        cube_two_node = Node(self.cube_two)
        cmds.parent(self.cube_one, self.transform_one)
        cmds.parent(self.cube_two, self.transform_one)
        cmds.setAttr(f'{self.transform_one}.ty', 15)
        cmds.setAttr(f'{self.cube_one}.ty', 5)

        expected = f"|{self.transform_one}|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        created_offsets = hierarchy_utils.add_offset_transform(target_list=[cube_one_node, cube_two_node],
                                                               transform_type="group",
                                                               pivot_source="parent",
                                                               transform_suffix="offset")

        expected = f"|{self.transform_one}|cube_one_offset|{self.cube_one}"
        result = str(cube_one_node)
        self.assertEqual(expected, result)

        expected = [f"|{self.transform_one}|cube_one_offset", f"|{self.transform_one}|cube_two_offset"]
        self.assertEqual(expected, created_offsets)

    def test_duplicate_as_node(self):
        cube_one_node = Node(self.cube_one)
        cmds.addAttr(cube_one_node, longName='mockedAttr', attributeType='double')
        duplicate = hierarchy_utils.duplicate_as_node(to_duplicate=cube_one_node,
                                                      name="pCube2",
                                                      input_connections=False,
                                                      parent_only=False,
                                                      delete_attrs=True)

        expected = f"|pCube2"
        self.assertTrue(cmds.objExists(expected), "Missing duplicated object.")
        self.assertEqual(expected, str(duplicate))
        shapes = cmds.listRelatives(duplicate, shapes=True)
        expected = ['pCube2Shape']
        self.assertEqual(expected, shapes)
        self.assertFalse(cmds.objExists(f'|pCube2.mockedAttr'),
                         "Unexpected attr found in duplicated object.")

    def test_duplicate_as_node_parent_only(self):
        cube_one_node = Node(self.cube_one)
        duplicate = hierarchy_utils.duplicate_as_node(to_duplicate=cube_one_node,
                                                      name="pCube2",
                                                      input_connections=False,
                                                      parent_only=True,
                                                      delete_attrs=True)

        expected = f"|pCube2"
        self.assertTrue(cmds.objExists(expected), "Missing duplicated object.")
        self.assertEqual(expected, str(duplicate))
        shapes = cmds.listRelatives(duplicate, shapes=True)
        expected = None
        self.assertEqual(expected, shapes)

    def test_duplicate_as_node_keep_attrs(self):
        cube_one_node = Node(self.cube_one)
        cmds.addAttr(cube_one_node, longName='mockedAttr', attributeType='double')
        duplicate = hierarchy_utils.duplicate_as_node(to_duplicate=cube_one_node,
                                                      name="pCube2",
                                                      input_connections=False,
                                                      parent_only=False,
                                                      delete_attrs=False)

        expected = f"|pCube2"
        self.assertTrue(cmds.objExists(expected), "Missing duplicated object.")
        self.assertEqual(expected, str(duplicate))
        self.assertTrue(cmds.objExists(f'|pCube2.mockedAttr'),
                        "Unexpected attr found in duplicated object.")

    def test_get_shape_components_mesh_vtx(self):
        cube = Node(self.cube_one)
        cube_shape = cmds.listRelatives(cube, shapes=True)
        components_vtx_a = hierarchy_utils.get_shape_components(shape=cube_shape[0], mesh_component_type="vertices")
        components_vtx_b = hierarchy_utils.get_shape_components(shape=cube_shape[0], mesh_component_type="vtx")

        expected = ['cube_one.vtx[0]', 'cube_one.vtx[1]', 'cube_one.vtx[2]', 'cube_one.vtx[3]',
                    'cube_one.vtx[4]', 'cube_one.vtx[5]', 'cube_one.vtx[6]', 'cube_one.vtx[7]']
        self.assertEqual(expected, components_vtx_a)
        self.assertEqual(expected, components_vtx_b)

    def test_get_shape_components_mesh_edges(self):
        cube = Node(self.cube_one)
        cube_shape = cmds.listRelatives(cube, shapes=True)
        components_edges_a = hierarchy_utils.get_shape_components(shape=cube_shape[0], mesh_component_type="edges")
        components_edges_b = hierarchy_utils.get_shape_components(shape=cube_shape[0], mesh_component_type="e")

        expected = ['cube_one.e[0]', 'cube_one.e[1]', 'cube_one.e[2]', 'cube_one.e[3]',
                    'cube_one.e[4]', 'cube_one.e[5]', 'cube_one.e[6]', 'cube_one.e[7]',
                    'cube_one.e[8]', 'cube_one.e[9]', 'cube_one.e[10]', 'cube_one.e[11]']
        self.assertEqual(expected, components_edges_a)
        self.assertEqual(expected, components_edges_b)

    def test_get_shape_components_mesh_faces(self):
        cube = Node(self.cube_one)
        cube_shape = cmds.listRelatives(cube, shapes=True)
        components_faces_a = hierarchy_utils.get_shape_components(shape=cube_shape[0], mesh_component_type="faces")
        components_faces_b = hierarchy_utils.get_shape_components(shape=cube_shape[0], mesh_component_type="f")

        expected = ['cube_one.f[0]', 'cube_one.f[1]', 'cube_one.f[2]',
                    'cube_one.f[3]', 'cube_one.f[4]', 'cube_one.f[5]']
        self.assertEqual(expected, components_faces_a)
        self.assertEqual(expected, components_faces_b)

    def test_get_shape_components_mesh_all(self):
        cube = Node(self.cube_one)
        cube_shape = cmds.listRelatives(cube, shapes=True)
        components = hierarchy_utils.get_shape_components(shape=cube_shape[0], mesh_component_type="all")

        expected = ['cube_one.vtx[0]', 'cube_one.vtx[1]', 'cube_one.vtx[2]', 'cube_one.vtx[3]',
                    'cube_one.vtx[4]', 'cube_one.vtx[5]', 'cube_one.vtx[6]', 'cube_one.vtx[7]']
        expected += ['cube_one.e[0]', 'cube_one.e[1]', 'cube_one.e[2]', 'cube_one.e[3]',
                     'cube_one.e[4]', 'cube_one.e[5]', 'cube_one.e[6]', 'cube_one.e[7]',
                     'cube_one.e[8]', 'cube_one.e[9]', 'cube_one.e[10]', 'cube_one.e[11]']
        expected += ['cube_one.f[0]', 'cube_one.f[1]', 'cube_one.f[2]',
                     'cube_one.f[3]', 'cube_one.f[4]', 'cube_one.f[5]']
        self.assertEqual(expected, components)

    def test_get_shape_components_mesh_unrecognized(self):
        cube = Node(self.cube_one)
        cube_shape = cmds.listRelatives(cube, shapes=True)
        components = hierarchy_utils.get_shape_components(shape=cube_shape[0], mesh_component_type="nothing")

        expected = []
        self.assertEqual(expected, components)

    def test_get_shape_components_curve(self):
        circle = cmds.circle(ch=False)
        circle_shape = cmds.listRelatives(circle[0], shapes=True)
        components = hierarchy_utils.get_shape_components(shape=circle_shape[0])

        expected = ['nurbsCircle1.cv[0]', 'nurbsCircle1.cv[1]', 'nurbsCircle1.cv[2]', 'nurbsCircle1.cv[3]',
                    'nurbsCircle1.cv[4]', 'nurbsCircle1.cv[5]', 'nurbsCircle1.cv[6]', 'nurbsCircle1.cv[7]']
        self.assertEqual(expected, components)

    def test_get_shape_components_surface(self):
        surface = cmds.nurbsPlane(ch=False)
        surface_shape = cmds.listRelatives(surface[0], shapes=True)
        components = hierarchy_utils.get_shape_components(shape=surface_shape[0])

        expected = ['nurbsPlane1.cv[0][0]', 'nurbsPlane1.cv[0][1]', 'nurbsPlane1.cv[0][2]',
                    'nurbsPlane1.cv[0][3]', 'nurbsPlane1.cv[1][0]', 'nurbsPlane1.cv[1][1]',
                    'nurbsPlane1.cv[1][2]', 'nurbsPlane1.cv[1][3]', 'nurbsPlane1.cv[2][0]',
                    'nurbsPlane1.cv[2][1]', 'nurbsPlane1.cv[2][2]', 'nurbsPlane1.cv[2][3]',
                    'nurbsPlane1.cv[3][0]', 'nurbsPlane1.cv[3][1]', 'nurbsPlane1.cv[3][2]',
                    'nurbsPlane1.cv[3][3]']
        self.assertEqual(expected, components)

    def test_get_shape_components_mesh_vtx_full_path(self):
        cube = Node(self.cube_one)
        cube_shape = cmds.listRelatives(cube, shapes=True)
        components_vtx_a = hierarchy_utils.get_shape_components(shape=cube_shape[0],
                                                                mesh_component_type="vertices",
                                                                full_path=True)

        expected = ['|cube_one.vtx[0]', '|cube_one.vtx[1]', '|cube_one.vtx[2]', '|cube_one.vtx[3]',
                    '|cube_one.vtx[4]', '|cube_one.vtx[5]', '|cube_one.vtx[6]', '|cube_one.vtx[7]']
        self.assertEqual(expected, components_vtx_a)
