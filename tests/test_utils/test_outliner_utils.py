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
from gt.utils import outliner_utils
cmds = maya_test_tools.cmds


class TestOutlinerUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_reorder_up(self):
        cube_a = maya_test_tools.create_poly_cube(name="cube_a")
        cube_b = maya_test_tools.create_poly_cube(name="cube_b")
        cube_c = maya_test_tools.create_poly_cube(name="cube_c")
        cube_d = maya_test_tools.create_poly_cube(name="cube_d")
        cubes = [cube_a, cube_b, cube_c, cube_d]
        group = maya_test_tools.create_group()
        cmds.parent(cubes, group)

        expected = ['cube_a', 'cube_b', 'cube_c', 'cube_d']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

        result = outliner_utils.reorder_up(target_list=['cube_b', 'cube_c'])
        expected = True
        self.assertEqual(expected, result)

        expected = ['cube_b', 'cube_c', 'cube_a', 'cube_d']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

    def test_reorder_up_invalid_object(self):
        result = outliner_utils.reorder_up(target_list=['mocked_a', 'mocked_b'])
        expected = False
        self.assertEqual(expected, result)

    def test_reorder_down(self):
        cube_a = maya_test_tools.create_poly_cube(name="cube_a")
        cube_b = maya_test_tools.create_poly_cube(name="cube_b")
        cube_c = maya_test_tools.create_poly_cube(name="cube_c")
        cube_d = maya_test_tools.create_poly_cube(name="cube_d")
        cubes = [cube_a, cube_b, cube_c, cube_d]
        group = maya_test_tools.create_group()
        cmds.parent(cubes, group)

        expected = ['cube_a', 'cube_b', 'cube_c', 'cube_d']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

        result = outliner_utils.reorder_down(target_list=['cube_b', 'cube_c'])
        expected = True
        self.assertEqual(expected, result)

        expected = ['cube_a', 'cube_d', 'cube_b', 'cube_c']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

    def test_reorder_down_invalid_object(self):
        result = outliner_utils.reorder_down(target_list=['mocked_a', 'mocked_b'])
        expected = False
        self.assertEqual(expected, result)

    def test_reorder_front(self):
        cube_a = maya_test_tools.create_poly_cube(name="cube_a")
        cube_b = maya_test_tools.create_poly_cube(name="cube_b")
        cube_c = maya_test_tools.create_poly_cube(name="cube_c")
        cube_d = maya_test_tools.create_poly_cube(name="cube_d")
        cubes = [cube_a, cube_b, cube_c, cube_d]
        group = maya_test_tools.create_group()
        cmds.parent(cubes, group)

        expected = ['cube_a', 'cube_b', 'cube_c', 'cube_d']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

        result = outliner_utils.reorder_front(target_list=['cube_b', 'cube_c'])
        expected = True
        self.assertEqual(expected, result)

        expected = ['cube_b', 'cube_c', 'cube_a', 'cube_d']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

    def test_reorder_front_invalid_object(self):
        result = outliner_utils.reorder_front(target_list=['mocked_a', 'mocked_b'])
        expected = False
        self.assertEqual(expected, result)

    def test_reorder_back(self):
        cube_a = maya_test_tools.create_poly_cube(name="cube_a")
        cube_b = maya_test_tools.create_poly_cube(name="cube_b")
        cube_c = maya_test_tools.create_poly_cube(name="cube_c")
        cube_d = maya_test_tools.create_poly_cube(name="cube_d")
        cubes = [cube_a, cube_b, cube_c, cube_d]
        group = maya_test_tools.create_group()
        cmds.parent(cubes, group)

        expected = ['cube_a', 'cube_b', 'cube_c', 'cube_d']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

        result = outliner_utils.reorder_back(target_list=['cube_a', 'cube_b'])
        expected = True
        self.assertEqual(expected, result)

        expected = ['cube_c', 'cube_d', 'cube_a', 'cube_b']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

    def test_reorder_back_invalid_object(self):
        result = outliner_utils.reorder_back(target_list=['mocked_a', 'mocked_b'])
        expected = False
        self.assertEqual(expected, result)

    def test_outliner_sort_name(self):
        cube_a = maya_test_tools.create_poly_cube(name="cube_a")
        cube_b = maya_test_tools.create_poly_cube(name="cube_b")
        cube_c = maya_test_tools.create_poly_cube(name="cube_c")
        cube_d = maya_test_tools.create_poly_cube(name="cube_d")
        shuffled_cubes = [cube_d, cube_b, cube_c, cube_a]
        group = maya_test_tools.create_group()
        cmds.parent(shuffled_cubes, group)

        expected = shuffled_cubes
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

        outliner_utils.outliner_sort(target_list=shuffled_cubes)

        expected = ['cube_a', 'cube_b', 'cube_c', 'cube_d']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

    def test_outliner_sort_name_not_ascending(self):
        cube_a = maya_test_tools.create_poly_cube(name="cube_a")
        cube_b = maya_test_tools.create_poly_cube(name="cube_b")
        cube_c = maya_test_tools.create_poly_cube(name="cube_c")
        cube_d = maya_test_tools.create_poly_cube(name="cube_d")
        shuffled_cubes = [cube_d, cube_b, cube_c, cube_a]
        group = maya_test_tools.create_group()
        cmds.parent(shuffled_cubes, group)

        expected = shuffled_cubes
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

        outliner_utils.outliner_sort(target_list=shuffled_cubes, is_ascending=False)

        expected = ['cube_d', 'cube_c', 'cube_b', 'cube_a']
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

    def test_outliner_sort_shuffle(self):
        cube_a = maya_test_tools.create_poly_cube(name="cube_a")
        cube_b = maya_test_tools.create_poly_cube(name="cube_b")
        cube_c = maya_test_tools.create_poly_cube(name="cube_c")
        cube_d = maya_test_tools.create_poly_cube(name="cube_d")
        cube_e = maya_test_tools.create_poly_cube(name="cube_e")
        cube_f = maya_test_tools.create_poly_cube(name="cube_f")
        cubes = [cube_a, cube_b, cube_c, cube_d, cube_e, cube_f]
        group = maya_test_tools.create_group()
        cmds.parent(cubes, group)

        expected = cubes
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

        outliner_utils.outliner_sort(target_list=cubes, operation=outliner_utils.OutlinerSortOptions.SHUFFLE)

        expected = cubes
        result = cmds.listRelatives(group, children=True)
        self.assertNotEqual(expected, result)

    def test_outliner_sort_attribute(self):
        cube_a = maya_test_tools.create_poly_cube(name="cube_a")
        cube_b = maya_test_tools.create_poly_cube(name="cube_b")
        cube_c = maya_test_tools.create_poly_cube(name="cube_c")
        cube_d = maya_test_tools.create_poly_cube(name="cube_d")
        cube_e = maya_test_tools.create_poly_cube(name="cube_e")
        cube_f = maya_test_tools.create_poly_cube(name="cube_f")
        cubes = [cube_a, cube_b, cube_c, cube_d, cube_e, cube_f]
        cmds.setAttr(f'{cube_d}.ty', 5)
        cmds.setAttr(f'{cube_e}.ty', 2)
        group = maya_test_tools.create_group()
        cmds.parent(cubes, group)

        expected = cubes
        result = cmds.listRelatives(group, children=True)
        self.assertEqual(expected, result)

        outliner_utils.outliner_sort(target_list=cubes,
                                     operation=outliner_utils.OutlinerSortOptions.ATTRIBUTE,
                                     attr='ty')

        expected = cube_d
        result = cmds.listRelatives(group, children=True)[0]  # 1st Slot
        self.assertEqual(expected, result)

        expected = cube_e
        result = cmds.listRelatives(group, children=True)[1]  # 2nd Slot
        self.assertEqual(expected, result)
