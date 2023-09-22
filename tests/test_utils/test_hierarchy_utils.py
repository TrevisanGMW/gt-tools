import unittest
import logging
import sys
import os

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
from gt.utils import hierarchy_utils


class TestHierarchyUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        self.cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        self.cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        self.cube_three = maya_test_tools.create_poly_cube(name="cube_three")
        self.transform_one = maya_test_tools.cmds.group(name="transform_one", empty=True, world=True)
        self.transform_two = maya_test_tools.cmds.group(name="transform_two", empty=True, world=True)
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
        children = maya_test_tools.cmds.listRelatives(self.transform_one, children=True)
        self.assertEqual(expected, children)

    def test_parent_str_input(self):
        result = hierarchy_utils.parent(source_objects=self.cube_one, target_parent=self.transform_one)
        expected = [f'|{self.transform_one}|{self.cube_one}']
        self.assertEqual(expected, result)
        expected = [self.cube_one]
        children = maya_test_tools.cmds.listRelatives(self.transform_one, children=True)
        self.assertEqual(expected, children)

    def test_parent_non_unique(self):
        hierarchy_utils.parent(source_objects=self.cube_one, target_parent=self.transform_one)
        maya_test_tools.cmds.rename(self.cube_two, "cube_one")
        result = hierarchy_utils.parent(source_objects="|cube_one", target_parent=self.transform_two)
        expected = [f"|{self.transform_two}|cube_one"]
        self.assertEqual(expected, result)
        children = maya_test_tools.cmds.listRelatives(self.transform_two, children=True, fullPath=True)
        self.assertEqual(expected, children)
