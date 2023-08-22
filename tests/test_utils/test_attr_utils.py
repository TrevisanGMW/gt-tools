import os
import sys
import logging
import unittest
from io import StringIO
from unittest.mock import patch

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
from gt.utils import attr_utils


class TestAttributeUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    @patch('sys.stdout', new_callable=StringIO)
    def test_delete_user_defined_attributes(self, mocked_stdout):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='bool', k=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr_two', lock=True)
        maya_test_tools.cmds.select(cube)
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True)
        expected = ['custom_attr_one', 'custom_attr_two']
        self.assertEqual(expected, result)
        attr_utils.delete_user_defined_attributes()
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True) or []
        expected = []
        self.assertEqual(expected, result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_delete_user_defined_attributes_no_locked(self, mocked_stdout):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='bool', k=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr_two', lock=True)
        maya_test_tools.cmds.select(cube)
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True)
        expected = ['custom_attr_one', 'custom_attr_two']
        self.assertEqual(expected, result)
        attr_utils.delete_user_defined_attributes(delete_locked=False)
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True) or []
        expected = ['custom_attr_two']
        self.assertEqual(expected, result)

    def test_add_separator_attr(self):
        cube = maya_test_tools.create_poly_cube()[0]
        attr_utils.add_separator_attr(target_object=cube, attr_name='mySeparator')
        result = maya_test_tools.cmds.objExists(f'{cube}.mySeparator')
        self.assertTrue(result)

    def test_add_separator_attr_custom_value(self):
        cube = maya_test_tools.create_poly_cube()[0]
        attr_utils.add_separator_attr(target_object=cube, attr_name='mySeparator', custom_value="test")
        result = maya_test_tools.cmds.getAttr(f'{cube}.mySeparator', asString=True)
        expected = 'test'
        self.assertEqual(expected, result)

    def test_freeze_channels_default(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ty", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tz", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ry", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rz", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sy", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sz", value=5)
        attr_utils.freeze_channels(object_list=cube)
        result_tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        result_rx = maya_test_tools.get_attribute(obj_name=cube, attr_name="rx")
        result_ry = maya_test_tools.get_attribute(obj_name=cube, attr_name="ry")
        result_rz = maya_test_tools.get_attribute(obj_name=cube, attr_name="rz")
        result_sx = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_sy = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_sz = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        expected_translate_rotate = 0
        expected_scale = 1
        self.assertEqual(expected_translate_rotate, result_tx)
        self.assertEqual(expected_translate_rotate, result_ty)
        self.assertEqual(expected_translate_rotate, result_tz)
        self.assertEqual(expected_translate_rotate, result_rx)
        self.assertEqual(expected_translate_rotate, result_ry)
        self.assertEqual(expected_translate_rotate, result_rz)
        self.assertEqual(expected_scale, result_sx)
        self.assertEqual(expected_scale, result_sy)
        self.assertEqual(expected_scale, result_sz)

    def test_freeze_channels_translate_off(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ty", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tz", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ry", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rz", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sy", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sz", value=5)
        attr_utils.freeze_channels(object_list=cube, freeze_translate=False)
        result_tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        result_rx = maya_test_tools.get_attribute(obj_name=cube, attr_name="rx")
        result_ry = maya_test_tools.get_attribute(obj_name=cube, attr_name="ry")
        result_rz = maya_test_tools.get_attribute(obj_name=cube, attr_name="rz")
        result_sx = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_sy = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_sz = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        expected_translate = 5
        expected_rotate = 0
        expected_scale = 1
        self.assertEqual(expected_translate, result_tx)
        self.assertEqual(expected_translate, result_ty)
        self.assertEqual(expected_translate, result_tz)
        self.assertEqual(expected_rotate, result_rx)
        self.assertEqual(expected_rotate, result_ry)
        self.assertEqual(expected_rotate, result_rz)
        self.assertEqual(expected_scale, result_sx)
        self.assertEqual(expected_scale, result_sy)
        self.assertEqual(expected_scale, result_sz)

    def test_freeze_channels_rotate_off(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ty", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tz", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ry", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rz", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sy", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sz", value=5)
        attr_utils.freeze_channels(object_list=cube, freeze_rotate=False)
        result_tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        result_rx = maya_test_tools.get_attribute(obj_name=cube, attr_name="rx")
        result_ry = maya_test_tools.get_attribute(obj_name=cube, attr_name="ry")
        result_rz = maya_test_tools.get_attribute(obj_name=cube, attr_name="rz")
        result_sx = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_sy = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_sz = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        expected_translate = 0
        expected_rotate = 5
        expected_scale = 1
        self.assertEqual(expected_translate, result_tx)
        self.assertEqual(expected_translate, result_ty)
        self.assertEqual(expected_translate, result_tz)
        self.assertEqual(expected_rotate, result_rx)
        self.assertEqual(expected_rotate, result_ry)
        self.assertEqual(expected_rotate, result_rz)
        self.assertEqual(expected_scale, result_sx)
        self.assertEqual(expected_scale, result_sy)
        self.assertEqual(expected_scale, result_sz)

    def test_freeze_channels_scale_off(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ty", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tz", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ry", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rz", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sy", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sz", value=5)
        attr_utils.freeze_channels(object_list=cube, freeze_scale=False)
        result_tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        result_rx = maya_test_tools.get_attribute(obj_name=cube, attr_name="rx")
        result_ry = maya_test_tools.get_attribute(obj_name=cube, attr_name="ry")
        result_rz = maya_test_tools.get_attribute(obj_name=cube, attr_name="rz")
        result_sx = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_sy = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_sz = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        expected_translate = 0
        expected_rotate = 0
        expected_scale = 5
        self.assertEqual(expected_translate, result_tx)
        self.assertEqual(expected_translate, result_ty)
        self.assertEqual(expected_translate, result_tz)
        self.assertEqual(expected_rotate, result_rx)
        self.assertEqual(expected_rotate, result_ry)
        self.assertEqual(expected_rotate, result_rz)
        self.assertEqual(expected_scale, result_sx)
        self.assertEqual(expected_scale, result_sy)
        self.assertEqual(expected_scale, result_sz)

    def test_freeze_channels_multiple_objects(self):
        cube_one = maya_test_tools.create_poly_cube()[0]
        cube_two = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.set_attribute(obj_name=cube_one, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube_two, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube_one, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube_two, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube_one, attr_name="sx", value=5)
        maya_test_tools.set_attribute(obj_name=cube_two, attr_name="sx", value=5)
        object_list = [cube_one, cube_two]
        attr_utils.freeze_channels(object_list=object_list)
        result_tx_one = maya_test_tools.get_attribute(obj_name=cube_one, attr_name="tx")
        result_rx_one = maya_test_tools.get_attribute(obj_name=cube_one, attr_name="rx")
        result_sx_one = maya_test_tools.get_attribute(obj_name=cube_one, attr_name="sx")
        result_tx_two = maya_test_tools.get_attribute(obj_name=cube_two, attr_name="tx")
        result_rx_two = maya_test_tools.get_attribute(obj_name=cube_two, attr_name="rx")
        result_sx_two = maya_test_tools.get_attribute(obj_name=cube_two, attr_name="sx")
        expected_translate = 0
        expected_rotate = 0
        expected_scale = 1
        self.assertEqual(expected_translate, result_tx_one)
        self.assertEqual(expected_translate, result_tx_two)
        self.assertEqual(expected_rotate, result_rx_one)
        self.assertEqual(expected_rotate, result_rx_two)
        self.assertEqual(expected_scale, result_sx_one)
        self.assertEqual(expected_scale, result_sx_two)

    def test_rescale(self):
        cube = maya_test_tools.create_poly_cube()[0]
        result_y = maya_test_tools.cmds.xform(cube + ".vtx[0]", query=True, translation=True, worldSpace=True)
        expected = [-0.5, -0.5, 0.5]  # Unchanged
        self.assertEqual(expected, result_y)
        attr_utils.rescale(obj=cube, scale=5, freeze=True)
        expected = [-2.5, -2.5, 2.5]  # Changed
        result_y = maya_test_tools.cmds.xform(cube + ".vtx[0]", query=True, translation=True, worldSpace=True)
        self.assertEqual(expected, result_y)

    def test_rescale_no_freeze(self):
        cube = maya_test_tools.create_poly_cube()[0]
        expected = 5
        attr_utils.rescale(obj=cube, scale=expected, freeze=False)
        result_x = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_y = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_z = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        self.assertEqual(expected, result_x)
        self.assertEqual(expected, result_y)
        self.assertEqual(expected, result_z)

    def test_set_attr(self):
        cube = maya_test_tools.create_poly_cube()[0]
        out = attr_utils.set_attr(f'{cube}.tx', 5)
        result = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        expected = 5
        self.assertEqual(expected, result)

    def test_set_attr_string(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, dataType="string")
        attr_utils.set_attr(f'{cube}.custom_attr', "string_value")
        result = maya_test_tools.get_attribute(obj_name=cube, attr_name="custom_attr")
        expected = "string_value"
        self.assertEqual(expected, result)

    def test_set_attr_multiple_objects(self):
        cube_list = []
        for index in range(0, 10):
            cube_list.append(maya_test_tools.create_poly_cube()[0])
        attr_utils.set_attr(value=5, obj_list=cube_list, attr_list=["tx"])

        for cube in cube_list:
            result = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
            expected = 5
            self.assertEqual(expected, result)

    def test_set_attr_multiple_objects_and_attributes(self):
        cube_list = []
        for index in range(0, 10):
            cube_list.append(maya_test_tools.create_poly_cube()[0])
        attr_utils.set_attr(value=5, obj_list=cube_list, attr_list=["tx", "ty", "tz"])

        for cube in cube_list:
            result_x = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
            result_y = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
            result_z = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
            expected = 5
            self.assertEqual(expected, result_x)
            self.assertEqual(expected, result_y)
            self.assertEqual(expected, result_z)

    def test_set_attr_locked_forced(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', lock=True)
        attr_utils.set_attr(f'{cube}.custom_attr', value=5, force_unlock=True)
        result = maya_test_tools.get_attribute(obj_name=cube, attr_name="custom_attr")
        expected = 5
        self.assertEqual(expected, result)

    def test_set_attr_locked_failed(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', lock=True)
        logging.disable(logging.WARNING)
        attr_utils.set_attr(f'{cube}.custom_attr', value=5, force_unlock=False)
        logging.disable(logging.NOTSET)
        result = maya_test_tools.get_attribute(obj_name=cube, attr_name="custom_attr")
        expected = 0
        self.assertEqual(expected, result)

    def test_set_attr_locked_raises_exception(self):
        with self.assertRaises(RuntimeError):
            cube = maya_test_tools.create_poly_cube()[0]
            maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
            maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', lock=True)
            attr_utils.set_attr(f'{cube}.custom_attr', value=5, force_unlock=False,
                                raise_exceptions=True, verbose=False)
            result = maya_test_tools.get_attribute(obj_name=cube, attr_name="custom_attr")
            expected = 0
            self.assertEqual(expected, result)

    def test_get_attr_float(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.setAttr(f'{cube}.tx', 5)
        result = attr_utils.get_attr(f'{cube}.tx')
        expected = 5
        self.assertEqual(expected, result)

    def test_get_attr_double3(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.setAttr(f'{cube}.tx', 5)
        result = attr_utils.get_attr(f'{cube}.translate')
        expected = (5, 0, 0)
        self.assertEqual(expected, result)

    def test_get_attr_string(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, dataType="string")
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', "string_value", typ='string')
        result = attr_utils.get_attr(f'{cube}.custom_attr')
        expected = "string_value"
        self.assertEqual(expected, result)

    def test_get_attr_enum(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, longName="custom_attr", at='enum', en="zero:one:two", keyable=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', 1)
        result = attr_utils.get_attr(f'{cube}.custom_attr')
        expected = 1
        self.assertEqual(expected, result)

    def test_get_attr_enum_as_string(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.cmds.addAttr(cube, longName="custom_attr", at='enum', en="zero:one:two", keyable=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', 1)
        result = attr_utils.get_attr(f'{cube}.custom_attr', enum_as_string=True)
        expected = "one"
        self.assertEqual(expected, result)

