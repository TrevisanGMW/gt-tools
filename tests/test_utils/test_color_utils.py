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
from tests import maya_test_tools
from gt.utils import color_utils


class TestColorUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_color_constants_rig_class(self):
        attributes = vars(color_utils.ColorConstants.Rig)
        keys = [attr for attr in attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for clr_key in keys:
            color = getattr(color_utils.ColorConstants.Rig, clr_key)
            if not color:
                raise Exception(f'Missing color: {clr_key}')
            if not isinstance(color, tuple):
                raise Exception(f'Incorrect color type. Expected tuple, but got: "{type(color)}".')
            if len(color) != 3:
                raise Exception(f'Incorrect color length. Expected 3, but got: "{str(len(color))}".')

    def test_color_constants_rgb_class(self):
        attributes = vars(color_utils.ColorConstants.RGB)
        keys = [attr for attr in attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for clr_key in keys:
            color = getattr(color_utils.ColorConstants.RGB, clr_key)
            if not color:
                raise Exception(f'Missing color: {clr_key}')
            if not isinstance(color, tuple):
                raise Exception(f'Incorrect color type. Expected tuple, but got: "{type(color)}".')
            if len(color) != 3:
                raise Exception(f'Incorrect color length. Expected 3, but got: "{str(len(color))}".')

    def test_set_color_viewport(self):
        cube_one = maya_test_tools.create_poly_cube(name='test_cube_one')
        expected_color = (0, 0.5, 1)
        result = color_utils.set_color_viewport(obj_list=cube_one, rgb_color=expected_color)
        expected_result = [cube_one]
        self.assertEqual(expected_result, result)
        set_color = maya_test_tools.cmds.getAttr(f'{cube_one}.overrideColorRGB')[0]
        self.assertEqual(expected_color, set_color)
        override_state = maya_test_tools.cmds.getAttr(f'{cube_one}.overrideEnabled')
        self.assertTrue(override_state, "Expected override to be enabled.")

    def test_set_color_viewport_list(self):
        cube_one = maya_test_tools.create_poly_cube(name='test_cube_one')
        cube_two = maya_test_tools.create_poly_cube(name='test_cube_two')
        expected_color = (0, 0.5, 1)
        result = color_utils.set_color_viewport(obj_list=[cube_one, cube_two],
                                                rgb_color=expected_color)
        expected_result = [cube_one, cube_two]
        self.assertEqual(expected_result, result)
        for obj in [cube_one, cube_two]:
            set_color = maya_test_tools.cmds.getAttr(f'{obj}.overrideColorRGB')[0]
            self.assertEqual(expected_color, set_color)
            override_state = maya_test_tools.cmds.getAttr(f'{obj}.overrideEnabled')
            self.assertTrue(override_state, "Expected override to be enabled.")

    def test_set_color_outliner(self):
        cube_one = maya_test_tools.create_poly_cube(name='test_cube_one')
        expected_color = (0, 0.5, 1)
        result = color_utils.set_color_outliner(obj_list=cube_one, rgb_color=expected_color)
        expected_result = [cube_one]
        self.assertEqual(expected_result, result)
        clr_r = maya_test_tools.cmds.getAttr(f'{cube_one}.outlinerColorR')
        clr_g = maya_test_tools.cmds.getAttr(f'{cube_one}.outlinerColorG')
        clr_b = maya_test_tools.cmds.getAttr(f'{cube_one}.outlinerColorB')
        self.assertEqual(expected_color, (clr_r, clr_g, clr_b))
        override_state = maya_test_tools.cmds.getAttr(f'{cube_one}.useOutlinerColor')
        self.assertTrue(override_state, "Expected override to be enabled.")

    def test_set_color_outliner_list(self):
        cube_one = maya_test_tools.create_poly_cube(name='test_cube_one')
        cube_two = maya_test_tools.create_poly_cube(name='test_cube_two')
        expected_color = (0, 0.5, 1)
        result = color_utils.set_color_outliner(obj_list=[cube_one, cube_two],
                                                rgb_color=expected_color)
        expected_result = [cube_one, cube_two]
        self.assertEqual(expected_result, result)
        for obj in [cube_one, cube_two]:
            clr_r = maya_test_tools.cmds.getAttr(f'{obj}.outlinerColorR')
            clr_g = maya_test_tools.cmds.getAttr(f'{obj}.outlinerColorG')
            clr_b = maya_test_tools.cmds.getAttr(f'{obj}.outlinerColorB')
            self.assertEqual(expected_color, (clr_r, clr_g, clr_b))
            override_state = maya_test_tools.cmds.getAttr(f'{obj}.useOutlinerColor')
            self.assertTrue(override_state, "Expected override to be enabled.")

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
