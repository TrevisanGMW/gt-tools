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
from gt.utils import naming_utils


class TestNamingUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    def test_naming_constants(self):
        constant_attributes = vars(naming_utils.NamingConstants)
        constant_keys = [attr for attr in constant_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for constant_key in constant_keys:
            name_class = getattr(naming_utils.NamingConstants, constant_key)
            name_attributes = vars(name_class)
            name_class_keys = [attr for attr in name_attributes if not (attr.startswith('__') and attr.endswith('__'))]
            for name_key in name_class_keys:
                naming_string = getattr(name_class, name_key)
                if not naming_string:
                    raise Exception(f'Missing naming constant: {name_key}')
                if not isinstance(naming_string, str):
                    raise Exception(f'Naming constant has incorrect type: {str(naming_string)}')

    def test_get_short_name(self):
        result = naming_utils.get_short_name(long_name="grandparent|parent|item")
        expected = "item"
        self.assertEqual(expected, result)

    def test_get_short_name_long(self):
        result = naming_utils.get_short_name(long_name="one|two|three|four|five|six|seven|eight|nine|item")
        expected = "item"
        self.assertEqual(expected, result)

    def test_get_short_name_short(self):
        result = naming_utils.get_short_name(long_name="|item")
        expected = "item"
        self.assertEqual(expected, result)

    def test_get_short_name_maya(self):
        group_one = maya_test_tools.cmds.group(world=True, empty=True, name="group_one")
        group_two = maya_test_tools.cmds.group(world=True, empty=True, name="group_two")
        sphere_one = maya_test_tools.create_poly_cube(name="cube")
        maya_test_tools.cmds.parent(sphere_one, group_one)
        sphere_two = maya_test_tools.create_poly_cube(name="cube")
        maya_test_tools.cmds.parent(sphere_two, group_two)
        non_unique_cubes = maya_test_tools.list_objects(type="mesh")
        expected = ['group_two|cube|cubeShape', 'group_one|cube|cubeShape']
        self.assertEqual(expected, non_unique_cubes)
        for cube in non_unique_cubes:
            result = naming_utils.get_short_name(long_name=cube)
            expected = "cubeShape"
            self.assertEqual(expected, result)
