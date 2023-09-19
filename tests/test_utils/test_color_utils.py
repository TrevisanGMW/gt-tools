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
from gt.utils import color_utils


class TestColorUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_color_constants_class(self):
        attributes = vars(color_utils.ColorConstants)
        keys = [attr for attr in attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for clr_key in keys:
            color = getattr(color_utils.ColorConstants, clr_key)
            if not color:
                raise Exception(f'Missing color: {clr_key}')
            if not isinstance(color, tuple):
                raise Exception(f'Incorrect color type. Expected tuple, but got: "{type(color)}".')
            if len(color) != 3:
                raise Exception(f'Incorrect color length. Expected 3, but got: "{str(len(color))}".')

    def test_set_color_override_viewport(self):
        test_obj = 'test_cube'
        maya_test_tools.create_poly_cube(name=test_obj)

        expected = (0, 0.5, 1)
        result = color_utils.set_color_override_viewport(test_obj, rgb_color=expected)
        self.assertEqual(expected, result)

    def test_set_color_override_outliner(self):
        test_obj = 'test_cube'
        maya_test_tools.create_poly_cube(name=test_obj)

        expected = (0, 0.5, 1)
        result = color_utils.set_color_override_outliner(test_obj, rgb_color=expected)
        self.assertEqual(expected, result)

    def test_add_side_color_setup(self):
        test_obj = 'test_cube'
        maya_test_tools.create_poly_cube(name=test_obj)

        color_utils.add_side_color_setup(obj=test_obj, color_attr_name="autoColor")

        expected_bool_attrs = ['autoColor']
        expected_double_attrs = ['colorDefault', 'colorRight', 'colorLeft']
        for attr in expected_bool_attrs + expected_double_attrs:
            self.assertTrue(maya_test_tools.cmds.objExists(f'{test_obj}.{attr}'),
                            f'Missing expected attribute: "{attr}".')

        expected = 'bool'
        for attr in expected_bool_attrs:
            attr_type = maya_test_tools.cmds.getAttr(f'{test_obj}.{attr}', type=True)
            self.assertEqual(expected, attr_type)
        expected = 'double3'
        for attr in expected_double_attrs:
            attr_type = maya_test_tools.cmds.getAttr(f'{test_obj}.{attr}', type=True)
            self.assertEqual(expected, attr_type)

        expected = True
        result = maya_test_tools.cmds.getAttr(f'{test_obj}.overrideEnabled')
        self.assertEqual(expected, result)
        expected = 1
        result = maya_test_tools.cmds.getAttr(f'{test_obj}.overrideRGBColors')
        self.assertEqual(expected, result)
