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

# Import Utility and Maya Test Tools
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

    def assertAlmostEqualSigFig(self, arg1, arg2, tolerance=2):
        """
        Asserts that two numbers are almost equal up to a given number of significant figures.

        Args:
            self (object): The current test case or class object.
            arg1 (float): The first number for comparison.
            arg2 (float): The second number for comparison.
            tolerance (int, optional): The number of significant figures to consider for comparison. Default is 2.

        Returns:
            None

        Raises:
            AssertionError: If the significands of arg1 and arg2 differ by more than the specified tolerance.

        Example:
            obj = TestClass()
            obj.assertAlmostEqualSigFig(3.145, 3.14159, tolerance=3)
            # No assertion error will be raised as the first 3 significant figures are equal (3.14)
        """
        if tolerance > 1:
            tolerance = tolerance - 1

        str_formatter = '{0:.' + str(tolerance) + 'e}'
        significand_1 = float(str_formatter.format(arg1).split('e')[0])
        significand_2 = float(str_formatter.format(arg2).split('e')[0])

        exponent_1 = int(str_formatter.format(arg1).split('e')[1])
        exponent_2 = int(str_formatter.format(arg2).split('e')[1])

        self.assertEqual(significand_1, significand_2)
        self.assertEqual(exponent_1, exponent_2)

    @patch('sys.stdout', new_callable=StringIO)
    def test_selection_delete_user_defined_attributes(self, mocked_stdout):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='bool', k=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr_two', lock=True)
        maya_test_tools.cmds.select(cube)
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True)
        expected = ['custom_attr_one', 'custom_attr_two']
        self.assertEqual(expected, result)
        attr_utils.selection_delete_user_defined_attributes()
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True) or []
        expected = []
        self.assertEqual(expected, result)

    @patch('sys.stdout', new_callable=StringIO)
    def test_selection_delete_user_defined_attributes_no_locked(self, mocked_stdout):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='bool', k=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr_two', lock=True)
        maya_test_tools.cmds.select(cube)
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True)
        expected = ['custom_attr_one', 'custom_attr_two']
        self.assertEqual(expected, result)
        attr_utils.selection_delete_user_defined_attributes(delete_locked=False)
        result = maya_test_tools.cmds.listAttr(cube, userDefined=True) or []
        expected = ['custom_attr_two']
        self.assertEqual(expected, result)

    def test_add_separator_attr(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.add_separator_attr(target_object=cube, attr_name='mySeparator')
        result = maya_test_tools.cmds.objExists(f'{cube}.mySeparator')
        self.assertTrue(result)

    def test_add_separator_attr_custom_value(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.add_separator_attr(target_object=cube, attr_name='mySeparator', custom_value="test")
        result = maya_test_tools.cmds.getAttr(f'{cube}.mySeparator', asString=True)
        expected = 'test'
        self.assertEqual(expected, result)

    def test_freeze_channels_default(self):
        cube = maya_test_tools.create_poly_cube()
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
        cube = maya_test_tools.create_poly_cube()
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
        cube = maya_test_tools.create_poly_cube()
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
        cube = maya_test_tools.create_poly_cube()
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
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
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
        cube = maya_test_tools.create_poly_cube()
        result_y = maya_test_tools.cmds.xform(cube + ".vtx[0]", query=True, translation=True, worldSpace=True)
        expected = [-0.5, -0.5, 0.5]  # Unchanged
        self.assertEqual(expected, result_y)
        attr_utils.rescale(obj=cube, scale=5, freeze=True)
        expected = [-2.5, -2.5, 2.5]  # Changed
        result_y = maya_test_tools.cmds.xform(cube + ".vtx[0]", query=True, translation=True, worldSpace=True)
        self.assertEqual(expected, result_y)

    def test_rescale_no_freeze(self):
        cube = maya_test_tools.create_poly_cube()
        expected = 5
        attr_utils.rescale(obj=cube, scale=expected, freeze=False)
        result_x = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_y = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_z = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        self.assertEqual(expected, result_x)
        self.assertEqual(expected, result_y)
        self.assertEqual(expected, result_z)

    def test_set_attr(self):
        cube = maya_test_tools.create_poly_cube()
        out = attr_utils.set_attr(f'{cube}.tx', 5)
        result = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        expected = 5
        self.assertEqual(expected, result)

    def test_set_attr_string(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, dataType="string")
        attr_utils.set_attr(f'{cube}.custom_attr', "string_value")
        result = maya_test_tools.get_attribute(obj_name=cube, attr_name="custom_attr")
        expected = "string_value"
        self.assertEqual(expected, result)

    def test_set_attr_double3(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.set_attr(obj_list=cube, attr_list="translate", value=[1, 0, 0])
        expected = [(1.0, 0.0, 0.0)]
        result = maya_test_tools.get_attribute(obj_name=cube, attr_name="translate")
        self.assertEqual(expected, result)

    def test_set_attr_multiple_objects(self):
        cube_list = []
        for index in range(0, 10):
            cube_list.append(maya_test_tools.create_poly_cube())
        attr_utils.set_attr(value=5, obj_list=cube_list, attr_list=["tx"])

        for cube in cube_list:
            result = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
            expected = 5
            self.assertEqual(expected, result)

    def test_set_attr_multiple_objects_and_attributes(self):
        cube_list = []
        for index in range(0, 10):
            cube_list.append(maya_test_tools.create_poly_cube())
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
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', lock=True)
        attr_utils.set_attr(f'{cube}.custom_attr', value=5, force_unlock=True)
        result = maya_test_tools.get_attribute(obj_name=cube, attr_name="custom_attr")
        expected = 5
        self.assertEqual(expected, result)

    def test_set_attr_locked_failed(self):
        cube = maya_test_tools.create_poly_cube()
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
            cube = maya_test_tools.create_poly_cube()
            maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
            maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', lock=True)
            attr_utils.set_attr(f'{cube}.custom_attr', value=5, force_unlock=False,
                                raise_exceptions=True, verbose=False)
            result = maya_test_tools.get_attribute(obj_name=cube, attr_name="custom_attr")
            expected = 0
            self.assertEqual(expected, result)

    def test_get_attr_float(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.setAttr(f'{cube}.tx', 5)
        result = attr_utils.get_attr(f'{cube}.tx')
        expected = 5
        self.assertEqual(expected, result)

    def test_get_attr_double3(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.setAttr(f'{cube}.tx', 5)
        result = attr_utils.get_attr(f'{cube}.translate')
        expected = (5, 0, 0)
        self.assertEqual(expected, result)

    def test_get_attr_string(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, dataType="string")
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', "string_value", typ='string')
        result = attr_utils.get_attr(f'{cube}.custom_attr')
        expected = "string_value"
        self.assertEqual(expected, result)

    def test_get_attr_enum(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, longName="custom_attr", at='enum', en="zero:one:two", keyable=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', 1)
        result = attr_utils.get_attr(f'{cube}.custom_attr')
        expected = 1
        self.assertEqual(expected, result)

    def test_get_attr_enum_as_string(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, longName="custom_attr", at='enum', en="zero:one:two", keyable=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', 1)
        result = attr_utils.get_attr(f'{cube}.custom_attr', enum_as_string=True)
        expected = "one"
        self.assertEqual(expected, result)

    def test_get_multiple_attr_float(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.setAttr(f'{cube}.tx', 5)
        result = attr_utils.get_multiple_attr(f'{cube}.tx')
        expected = {'pCube1.tx': 5.0}
        self.assertEqual(expected, result)

    def test_get_multiple_attr_double3(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.setAttr(f'{cube}.tx', 5)
        result = attr_utils.get_multiple_attr(f'{cube}.translate')
        expected = {'pCube1.translate': (5.0, 0.0, 0.0)}
        self.assertEqual(expected, result)

    def test_get_multiple_attr_string(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, dataType="string")
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', "string_value", typ='string')
        result = attr_utils.get_multiple_attr(f'{cube}.custom_attr')
        expected = {'pCube1.custom_attr': 'string_value'}
        self.assertEqual(expected, result)

    def test_get_multiple_attr_enum(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, longName="custom_attr", at='enum', en="zero:one:two", keyable=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', 1)
        result = attr_utils.get_multiple_attr(f'{cube}.custom_attr')
        expected = {'pCube1.custom_attr': 1}
        self.assertEqual(expected, result)

    def test_get_multiple_attr_enum_as_string(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, longName="custom_attr", at='enum', en="zero:one:two", keyable=True)
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', 1)
        result = attr_utils.get_multiple_attr(f'{cube}.custom_attr', enum_as_string=True)
        expected = {'pCube1.custom_attr': "one"}
        self.assertEqual(expected, result)

    def test_set_trs_attr_translate_world(self):
        cube = maya_test_tools.create_poly_cube()
        group = maya_test_tools.cmds.group(name="temp", empty=True, world=True)
        maya_test_tools.cmds.parent(cube, group)
        maya_test_tools.cmds.move(5, 0, 0, group)

        attr_utils.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3), translate=True)

        result_tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        expected_tx = -4  # was 1, but -5 comes from parent
        expected_ty = 2
        expected_tz = 3
        self.assertEqual(expected_tx, result_tx)
        self.assertEqual(expected_ty, result_ty)
        self.assertEqual(expected_tz, result_tz)

    def test_set_trs_attr_all_trs(self):
        cube = maya_test_tools.create_poly_cube()

        attr_utils.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3),
                                translate=True, rotate=True, scale=True)

        result_tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        result_rx = maya_test_tools.get_attribute(obj_name=cube, attr_name="rx")
        result_ry = maya_test_tools.get_attribute(obj_name=cube, attr_name="ry")
        result_rz = maya_test_tools.get_attribute(obj_name=cube, attr_name="rz")
        result_sx = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_sy = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_sz = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        expected_x = 1
        for attr in [result_tx, result_rx, result_sx]:
            self.assertAlmostEqualSigFig(expected_x, attr)
        expected_y = 2
        for attr in [result_ty, result_ry, result_sy]:
            self.assertAlmostEqualSigFig(expected_y, attr)
        expected_z = 3
        for attr in [result_tz, result_rz, result_sz]:
            self.assertAlmostEqualSigFig(expected_z, attr)

    def test_set_trs_attr_translate(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3), translate=True)

        result_tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        expected_tx = 1
        expected_ty = 2
        expected_tz = 3
        self.assertEqual(expected_tx, result_tx)
        self.assertEqual(expected_ty, result_ty)
        self.assertEqual(expected_tz, result_tz)

    def test_set_trs_attr_rotate(self):
        cube = maya_test_tools.create_poly_cube()
        group = maya_test_tools.cmds.group(name="temp", empty=True, world=True)
        maya_test_tools.cmds.parent(cube, group)

        attr_utils.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3),
                                translate=False, rotate=True, scale=False)

        result_rx = maya_test_tools.get_attribute(obj_name=cube, attr_name="rx")
        result_ry = maya_test_tools.get_attribute(obj_name=cube, attr_name="ry")
        result_rz = maya_test_tools.get_attribute(obj_name=cube, attr_name="rz")
        expected_rx = 1
        expected_ry = 2
        expected_rz = 3
        self.assertAlmostEqualSigFig(expected_rx, result_rx)
        self.assertAlmostEqualSigFig(expected_ry, result_ry)
        self.assertAlmostEqualSigFig(expected_rz, result_rz)

    def test_set_trs_attr_scale(self):
        cube = maya_test_tools.create_poly_cube()
        group = maya_test_tools.cmds.group(name="temp", empty=True, world=True)
        maya_test_tools.cmds.parent(cube, group)

        attr_utils.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3),
                                translate=False, rotate=False, scale=True)

        result_sx = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_sy = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_sz = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        expected_sx = 1
        expected_sy = 2
        expected_sz = 3
        self.assertEqual(expected_sx, result_sx)
        self.assertEqual(expected_sy, result_sy)
        self.assertEqual(expected_sz, result_sz)

    def test_set_trs_attr_translate_object_space(self):
        cube = maya_test_tools.create_poly_cube()
        group = maya_test_tools.cmds.group(name="temp", empty=True, world=True)
        maya_test_tools.cmds.parent(cube, group)

        attr_utils.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3),
                                translate=True, rotate=False, scale=False, space="object")

        result_tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        expected_ty = 2
        expected_tx = 1
        expected_tz = 3
        self.assertAlmostEqualSigFig(expected_tx, result_tx)
        self.assertAlmostEqualSigFig(expected_ty, result_ty)
        self.assertAlmostEqualSigFig(expected_tz, result_tz)

    def test_set_trs_attr_rotate_object_space(self):
        cube = maya_test_tools.create_poly_cube()
        group = maya_test_tools.cmds.group(name="temp", empty=True, world=True)
        maya_test_tools.cmds.parent(cube, group)

        attr_utils.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3),
                                translate=False, rotate=True, scale=False, space="object")

        result_rx = maya_test_tools.get_attribute(obj_name=cube, attr_name="rx")
        result_ry = maya_test_tools.get_attribute(obj_name=cube, attr_name="ry")
        result_rz = maya_test_tools.get_attribute(obj_name=cube, attr_name="rz")
        expected_rx = 1
        expected_ry = 2
        expected_rz = 3
        self.assertAlmostEqualSigFig(expected_rx, result_rx)
        self.assertAlmostEqualSigFig(expected_ry, result_ry)
        self.assertAlmostEqualSigFig(expected_rz, result_rz)

    def test_set_trs_attr_scale_object_space(self):
        cube = maya_test_tools.create_poly_cube()
        group = maya_test_tools.cmds.group(name="temp", empty=True, world=True)
        maya_test_tools.cmds.parent(cube, group)

        attr_utils.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3),
                                translate=False, rotate=False, scale=True, space="object")

        result_sx = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_sy = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_sz = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        expected_sx = 1
        expected_sy = 2
        expected_sz = 3
        self.assertEqual(expected_sx, result_sx)
        self.assertEqual(expected_sy, result_sy)
        self.assertEqual(expected_sz, result_sz)

    def test_hide_lock_default_attributes_with_visibility(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.hide_lock_default_attrs(cube, visibility=True)

        attr_to_test = ['tx', 'ty', 'tz', 'rx', 'ty', 'rz', 'sx', 'sy', 'sz', 'v']
        for attr in attr_to_test:
            is_locked = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', lock=True)
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            is_keyable_ch = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', channelBox=True)
            self.assertTrue(is_locked)
            self.assertFalse(is_keyable)
            self.assertFalse(is_keyable_ch)

    def test_hide_lock_default_attributes_without_visibility(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.hide_lock_default_attrs(cube, visibility=False)

        attr_to_test = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
        for attr in attr_to_test:
            is_locked = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', lock=True)
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            is_keyable_ch = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', channelBox=True)
            self.assertTrue(is_locked)
            self.assertFalse(is_keyable)
            self.assertFalse(is_keyable_ch)

        is_locked = maya_test_tools.cmds.getAttr(f'{cube}.v', lock=True)
        is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.v', keyable=True)
        self.assertFalse(is_locked)
        self.assertTrue(is_keyable)

    def test_hide_lock_default_attributes_no_translate(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.hide_lock_default_attrs(cube, translate=False, visibility=False)

        attr_to_test = ['rx', 'ry', 'rz', 'sx', 'sy', 'sz']
        attr_to_test_inactive = ['tx', 'ty', 'tz']
        for attr in attr_to_test:
            is_locked = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', lock=True)
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            is_keyable_ch = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', channelBox=True)
            self.assertTrue(is_locked, f'Expected: "{str(attr)}" to be locked.')
            self.assertFalse(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "False".')
            self.assertFalse(is_keyable_ch, f'Expected: "{str(attr)}" to have "channelBox" set to "False".')
        for attr in attr_to_test_inactive:
            is_locked = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', lock=True)
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            self.assertFalse(is_locked, f'Expected: "{str(attr)}" to be unlocked.')
            self.assertTrue(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "True".')

        is_locked = maya_test_tools.cmds.getAttr(f'{cube}.v', lock=True)
        is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.v', keyable=True)
        self.assertFalse(is_locked)
        self.assertTrue(is_keyable)

    def test_hide_lock_default_attributes_no_rotate(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.hide_lock_default_attrs(cube, rotate=False, visibility=False)

        attr_to_test = ['tx', 'ty', 'tz', 'sx', 'sy', 'sz']
        attr_to_test_inactive = ['rx', 'ry', 'rz']
        for attr in attr_to_test:
            is_locked = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', lock=True)
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            is_keyable_ch = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', channelBox=True)
            self.assertTrue(is_locked, f'Expected: "{str(attr)}" to be locked.')
            self.assertFalse(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "False".')
            self.assertFalse(is_keyable_ch, f'Expected: "{str(attr)}" to have "channelBox" set to "False".')
        for attr in attr_to_test_inactive:
            is_locked = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', lock=True)
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            self.assertFalse(is_locked, f'Expected: "{str(attr)}" to be unlocked.')
            self.assertTrue(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "True".')

        is_locked = maya_test_tools.cmds.getAttr(f'{cube}.v', lock=True)
        is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.v', keyable=True)
        self.assertFalse(is_locked)
        self.assertTrue(is_keyable)

    def test_hide_lock_default_attributes_no_scale(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.hide_lock_default_attrs(cube, scale=False, visibility=False)

        attr_to_test = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz']
        attr_to_test_inactive = ['sx', 'sy', 'sz']
        for attr in attr_to_test:
            is_locked = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', lock=True)
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            is_keyable_ch = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', channelBox=True)
            self.assertTrue(is_locked, f'Expected: "{str(attr)}" to be locked.')
            self.assertFalse(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "False".')
            self.assertFalse(is_keyable_ch, f'Expected: "{str(attr)}" to have "channelBox" set to "False".')
        for attr in attr_to_test_inactive:
            is_locked = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', lock=True)
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            self.assertFalse(is_locked, f'Expected: "{str(attr)}" to be unlocked.')
            self.assertTrue(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "True".')

        is_locked = maya_test_tools.cmds.getAttr(f'{cube}.v', lock=True)
        is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.v', keyable=True)
        self.assertFalse(is_locked)
        self.assertTrue(is_keyable)

    def test_add_attr_double_three(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.add_attr_double_three(obj=cube, attr_name="mockedAttr")

        attr_type = maya_test_tools.cmds.getAttr(f'{cube}.mockedAttr', type=True)
        expected = 'double3'
        self.assertEqual(expected, attr_type)
        is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.mockedAttr', keyable=True)
        self.assertTrue(is_keyable)

        expected = 'double'
        attr_to_test = ['mockedAttrR', 'mockedAttrG', 'mockedAttrB']
        for attr in attr_to_test:
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            self.assertTrue(is_keyable)
            attr_type = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', type=True)
            self.assertEqual(expected, attr_type)

    def test_add_attr_double_three_suffix(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.add_attr_double_three(obj=cube, attr_name="mockedAttr", suffix="ABC")

        self.assertTrue(maya_test_tools.cmds.objExists(f'{cube}.mockedAttr'))
        attr_type = maya_test_tools.cmds.getAttr(f'{cube}.mockedAttr', type=True)
        expected = 'double3'
        self.assertEqual(expected, attr_type)
        is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.mockedAttr', keyable=True)
        self.assertTrue(is_keyable)

        expected = 'double'
        attr_to_test = ['mockedAttrA', 'mockedAttrB', 'mockedAttrC']
        for attr in attr_to_test:
            self.assertTrue(maya_test_tools.cmds.objExists(f'{cube}.{attr}'))
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            self.assertTrue(is_keyable)
            attr_type = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', type=True)
            self.assertEqual(expected, attr_type)

    def test_add_attr_double_three_keyable(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.add_attr_double_three(obj=cube, attr_name="mockedAttr", suffix="ABC", keyable=False)

        self.assertTrue(maya_test_tools.cmds.objExists(f'{cube}.mockedAttr'))
        attr_type = maya_test_tools.cmds.getAttr(f'{cube}.mockedAttr', type=True)
        expected = 'double3'
        self.assertEqual(expected, attr_type)

        expected = 'double'
        attr_to_test = ['mockedAttrA', 'mockedAttrB', 'mockedAttrC']
        for attr in attr_to_test:
            self.assertTrue(maya_test_tools.cmds.objExists(f'{cube}.{attr}'))
            is_keyable = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', keyable=True)
            self.assertFalse(is_keyable)
            attr_type = maya_test_tools.cmds.getAttr(f'{cube}.{attr}', type=True)
            self.assertEqual(expected, attr_type)

    def test_get_trs_attr_as_list(self):
        cube = maya_test_tools.create_poly_cube()

        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sx", value=5)

        result = attr_utils.get_trs_attr_as_list(cube)
        expected = [5, 0, 0, 5, 0, 0, 5, 1, 1]
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_formatted_string(self):
        cube = maya_test_tools.create_poly_cube()

        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sx", value=5)

        result = attr_utils.get_trs_attr_as_formatted_string(cube)
        expected = 'source_obj = "pCube1"\ntrs_attr_list = [5, 0, 0, 5, 0, 0, 5, 1, 1]'
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_formatted_string_description(self):
        cube = maya_test_tools.create_poly_cube()

        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sx", value=5)

        result = attr_utils.get_trs_attr_as_formatted_string(cube, add_description=True)
        expected = '# Transform Data for "pCube1":\nsource_obj = "pCube1"\ntrs_attr_list = [5, 0, 0, 5, 0, 0, 5, 1, 1]'
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_formatted_string_no_object(self):
        cube = maya_test_tools.create_poly_cube()

        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sx", value=5)

        result = attr_utils.get_trs_attr_as_formatted_string(cube, add_object=False)
        expected = 'trs_attr_list = [5, 0, 0, 5, 0, 0, 5, 1, 1]'
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_formatted_string_separated_channels(self):
        cube = maya_test_tools.create_poly_cube()

        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="rx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="sx", value=5)

        result = attr_utils.get_trs_attr_as_formatted_string(cube, separate_channels=True, add_object=False)
        expected = 't_attr_list = [5, 0, 0]\nr_attr_list = [5, 0, 0]\ns_attr_list = [5, 1, 1]'
        self.assertEqual(expected, result)

    def test_add_attributes(self):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()

        # Test data
        target_list = [cube_one, cube_two]
        attributes = ["attr1", "attr2"]
        attr_type = "double"
        minimum = 1
        maximum = 10
        default = 5
        is_keyable = True
        verbose = False

        # Call the function
        result = attr_utils.add_attr(target_list, attributes, attr_type, minimum, maximum,
                                     default, is_keyable, verbose)

        # Define expected results
        expected_added_attrs = [f"{cube_one}.attr1", f"{cube_one}.attr2", f"{cube_two}.attr1", f"{cube_two}.attr2"]

        # Assert expected results
        self.assertEqual(result, expected_added_attrs)
        for obj in target_list:
            for attr_name in attributes:
                full_attr_name = f"{obj}.{attr_name}"
                exists = maya_test_tools.cmds.objExists(full_attr_name)
                self.assertTrue(exists)
                type_result = maya_test_tools.cmds.getAttr(full_attr_name, type=True)
                self.assertEqual(attr_type, type_result)
                min_val = maya_test_tools.cmds.attributeQuery(attr_name, node=obj, min=True)
                expected = [minimum]
                self.assertEqual(expected, min_val)
                exists_max = maya_test_tools.cmds.attributeQuery(attr_name, node=obj, max=True)
                expected = [maximum]
                self.assertEqual(expected, exists_max)
                exists_default = maya_test_tools.cmds.attributeQuery(attr_name, node=obj, exists=True)
                self.assertTrue(exists_default)

    def test_add_attributes_string_inputs(self):
        cube_one = maya_test_tools.create_poly_cube()

        # Test data
        target_list = cube_one
        attribute = "attr1"
        attr_type = "double"
        minimum = 1
        maximum = 10
        default = 5
        is_keyable = True
        verbose = False

        # Call the function
        result = attr_utils.add_attr(target_list, attribute, attr_type, minimum, maximum,
                                     default, is_keyable, verbose)

        # Define expected results
        expected_added_attrs = [f"{cube_one}.attr1"]

        # Assert expected results
        self.assertEqual(result, expected_added_attrs)

        full_attr_name = f"{cube_one}.{attribute}"
        exists = maya_test_tools.cmds.objExists(full_attr_name)
        self.assertTrue(exists)
        type_result = maya_test_tools.cmds.getAttr(full_attr_name, type=True)
        self.assertEqual(attr_type, type_result)
        min_val = maya_test_tools.cmds.attributeQuery(attribute, node=cube_one, min=True)
        expected = [minimum]
        self.assertEqual(expected, min_val)
        exists_max = maya_test_tools.cmds.attributeQuery(attribute, node=cube_one, max=True)
        expected = [maximum]
        self.assertEqual(expected, exists_max)
        exists_default = maya_test_tools.cmds.attributeQuery(attribute, node=cube_one, exists=True)
        self.assertTrue(exists_default)

    def test_get_trs_attr_as_python(self):
        cube = maya_test_tools.create_poly_cube()

        result = attr_utils.get_trs_attr_as_python(cube)
        expected = '# Transform Data for "pCube1":\ncmds.setAttr("pCube1.tx", 0)\ncmds.setAttr("pCube1.ty", 0)\n' \
                   'cmds.setAttr("pCube1.tz", 0)\ncmds.setAttr("pCube1.rx", 0)\ncmds.setAttr("pCube1.ry", 0)\n' \
                   'cmds.setAttr("pCube1.rz", 0)\ncmds.setAttr("pCube1.sx", 1)\ncmds.setAttr("pCube1.sy", 1)\n' \
                   'cmds.setAttr("pCube1.sz", 1)'
        self.assertEqual(expected, result)
        result = attr_utils.get_trs_attr_as_python([cube, cube])
        expected = f'{expected}\n\n{expected}'
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_python_loop(self):
        cube = maya_test_tools.create_poly_cube()

        result = attr_utils.get_trs_attr_as_python(cube, use_loop=True)
        expected = '# Transform Data for "pCube1":\nfor key, value in {"tx": 0.0, "ty": 0.0, "tz": 0.0, "rx": 0.0, ' \
                   '"ry": 0.0, "rz": 0.0, "sx": 1.0, "sy": 1.0, "sz": 1.0}.items():\n\tif not ' \
                   'cmds.getAttr(f"pCube1.{key}", lock=True):\n\t\tcmds.setAttr(f"pCube1.{key}", value)'
        self.assertEqual(expected, result)
        result = attr_utils.get_trs_attr_as_python([cube, cube], use_loop=True)
        expected = f'{expected}\n\n{expected}'
        self.assertEqual(expected, result)

    def test_get_user_attr_to_python(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='float', k=True)
        result = attr_utils.get_user_attr_to_python(cube)
        expected = '# User-Defined Attribute Data for "pCube1":\ncmds.setAttr("pCube1.custom_attr_one", False)\n' \
                   'cmds.setAttr("pCube1.custom_attr_two", 0.0)'
        self.assertEqual(expected, result)
        result = attr_utils.get_user_attr_to_python([cube, cube])
        expected = f'{expected}\n\n{expected}'
        self.assertEqual(expected, result)

    def test_set_attr_state_lock_attribute(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.set_attr_state(attribute_path=f"{cube}.tx", locked=True)
        locked_state = maya_test_tools.cmds.getAttr(f"{cube}.tx", lock=True)
        self.assertTrue(locked_state)

    def test_set_attr_state_hide_attribute(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.set_attr_state(attribute_path=f"{cube}.ty", hidden=True)
        keyable_state = maya_test_tools.cmds.getAttr(f"{cube}.ty", keyable=True)
        channel_box_state = maya_test_tools.cmds.getAttr(f"{cube}.ty", channelBox=True)
        locked_state = maya_test_tools.cmds.getAttr(f"{cube}.tx", lock=True)
        self.assertFalse(keyable_state)
        self.assertFalse(channel_box_state)
        self.assertFalse(locked_state)

    def test_set_attr_state_lock_and_hide_attribute(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.set_attr_state(attribute_path=f"{cube}.tz", locked=True, hidden=True)
        locked_state = maya_test_tools.cmds.getAttr(f"{cube}.tz", lock=True)
        keyable_state = maya_test_tools.cmds.getAttr(f"{cube}.tz", keyable=True)
        channel_box_state = maya_test_tools.cmds.getAttr(f"{cube}.tz", channelBox=True)
        self.assertTrue(locked_state)
        self.assertFalse(keyable_state)
        self.assertFalse(channel_box_state)

    def test_set_attr_state_lock_and_hide_multiple_attributes(self):
        cube = maya_test_tools.create_poly_cube()
        attr_utils.set_attr_state(obj_list=[cube], attr_list=["tx", "ty"], locked=True, hidden=True)
        tx_locked_state = maya_test_tools.cmds.getAttr(f"{cube}.tx", lock=True)
        tx_keyable_state = maya_test_tools.cmds.getAttr(f"{cube}.tx", keyable=True)
        tx_channel_box_state = maya_test_tools.cmds.getAttr(f"{cube}.tx", channelBox=True)
        ty_locked_state = maya_test_tools.cmds.getAttr(f"{cube}.ty", lock=True)
        ty_keyable_state = maya_test_tools.cmds.getAttr(f"{cube}.ty", keyable=True)
        ty_channel_box_state = maya_test_tools.cmds.getAttr(f"{cube}.ty", channelBox=True)
        self.assertTrue(tx_locked_state)
        self.assertFalse(tx_keyable_state)
        self.assertFalse(tx_channel_box_state)
        self.assertTrue(ty_locked_state)
        self.assertFalse(ty_keyable_state)
        self.assertFalse(ty_channel_box_state)

    def test_selection_unlock_default_channels(self):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        for obj in [cube_one, cube_two]:
            maya_test_tools.cmds.setAttr(f'{obj}.tx', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.ty', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.tz', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.rx', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.ry', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.rz', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.sx', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.sy', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.sz', lock=True)
            # Test State -----------------------------------
            tx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.tx", lock=True)
            ty_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.ty", lock=True)
            tz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.tz", lock=True)
            rx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.rx", lock=True)
            ry_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.ry", lock=True)
            rz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.rz", lock=True)
            sx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sx", lock=True)
            sy_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sy", lock=True)
            sz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sz", lock=True)
            self.assertTrue(tx_locked_state)
            self.assertTrue(ty_locked_state)
            self.assertTrue(tz_locked_state)
            self.assertTrue(rx_locked_state)
            self.assertTrue(ry_locked_state)
            self.assertTrue(rz_locked_state)
            self.assertTrue(sx_locked_state)
            self.assertTrue(sy_locked_state)
            self.assertTrue(sz_locked_state)
            # Select and Unlock ----------------------------
            maya_test_tools.cmds.select([cube_one, cube_two])
            result = attr_utils.selection_unlock_default_channels(feedback=False)
            # Test State -----------------------------------
            tx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.tx", lock=True)
            ty_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.ty", lock=True)
            tz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.tz", lock=True)
            rx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.rx", lock=True)
            ry_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.ry", lock=True)
            rz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.rz", lock=True)
            sx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sx", lock=True)
            sy_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sy", lock=True)
            sz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sz", lock=True)
            self.assertFalse(tx_locked_state)
            self.assertFalse(ty_locked_state)
            self.assertFalse(tz_locked_state)
            self.assertFalse(rx_locked_state)
            self.assertFalse(ry_locked_state)
            self.assertFalse(rz_locked_state)
            self.assertFalse(sx_locked_state)
            self.assertFalse(sy_locked_state)
            self.assertFalse(sz_locked_state)
            expected = 2
            self.assertEqual(expected, result)

    def test_selection_unhide_default_channels(self):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        for obj in [cube_one, cube_two]:
            maya_test_tools.cmds.setAttr(f'{obj}.tx', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.ty', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.tz', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.rx', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.ry', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.rz', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.sx', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.sy', lock=True)
            maya_test_tools.cmds.setAttr(f'{obj}.sz', lock=True)
            # Test State -----------------------------------
            tx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.tx", lock=True)
            ty_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.ty", lock=True)
            tz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.tz", lock=True)
            rx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.rx", lock=True)
            ry_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.ry", lock=True)
            rz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.rz", lock=True)
            sx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sx", lock=True)
            sy_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sy", lock=True)
            sz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sz", lock=True)
            self.assertTrue(tx_locked_state)
            self.assertTrue(ty_locked_state)
            self.assertTrue(tz_locked_state)
            self.assertTrue(rx_locked_state)
            self.assertTrue(ry_locked_state)
            self.assertTrue(rz_locked_state)
            self.assertTrue(sx_locked_state)
            self.assertTrue(sy_locked_state)
            self.assertTrue(sz_locked_state)
            # Select and Unlock ----------------------------
            maya_test_tools.cmds.select([cube_one, cube_two])
            result = attr_utils.selection_unlock_default_channels(feedback=False)
            # Test State -----------------------------------
            tx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.tx", lock=True)
            ty_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.ty", lock=True)
            tz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.tz", lock=True)
            rx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.rx", lock=True)
            ry_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.ry", lock=True)
            rz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.rz", lock=True)
            sx_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sx", lock=True)
            sy_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sy", lock=True)
            sz_locked_state = maya_test_tools.cmds.getAttr(f"{obj}.sz", lock=True)
            self.assertFalse(tx_locked_state)
            self.assertFalse(ty_locked_state)
            self.assertFalse(tz_locked_state)
            self.assertFalse(rx_locked_state)
            self.assertFalse(ry_locked_state)
            self.assertFalse(rz_locked_state)
            self.assertFalse(sx_locked_state)
            self.assertFalse(sy_locked_state)
            self.assertFalse(sz_locked_state)
            expected = 2
            self.assertEqual(expected, result)

    def test_delete_user_defined_attributes(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", k=True, at="float")
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', lock=True)

        result = attr_utils.delete_user_defined_attributes(cube)

        attr_one = maya_test_tools.cmds.objExists(f'{cube}.custom_attr')
        self.assertFalse(attr_one)
        attr_two = maya_test_tools.cmds.objExists(f'{cube}.custom_attr_two')
        self.assertFalse(attr_two)

        expected = [f'{cube}.custom_attr', f'{cube}.custom_attr_two']
        self.assertEqual(expected, result)

    def test_delete_user_defined_attributes_no_lock(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", k=True, at="float")
        maya_test_tools.cmds.setAttr(f'{cube}.custom_attr', lock=True)

        result = attr_utils.delete_user_defined_attributes(cube, delete_locked=False)

        attr_one = maya_test_tools.cmds.objExists(f'{cube}.custom_attr')
        self.assertTrue(attr_one)
        attr_two = maya_test_tools.cmds.objExists(f'{cube}.custom_attr_two')
        self.assertFalse(attr_two)

        expected = [f'{cube}.custom_attr_two']
        self.assertEqual(expected, result)

    def test_connect_attr(self):
        cube = maya_test_tools.create_poly_cube()

        target_attr_list = [f'{cube}.scaleX', f'{cube}.scaleZ']
        attr_utils.connect_attr(source_attr=f'{cube}.scaleY', target_attr_list=target_attr_list)

        result = maya_test_tools.cmds.listConnections(f'{cube}.sy', destination=True, plugs=True)
        for attr in target_attr_list:
            self.assertIn(attr, result)

        result = maya_test_tools.cmds.listConnections(f'{cube}.sx', source=True, plugs=True) or []
        for attr in result:
            self.assertEqual(f'{cube}.scaleY', attr)

    def test_connect_attr_str_input(self):
        cube = maya_test_tools.create_poly_cube()

        attr_utils.connect_attr(source_attr=f'{cube}.scaleY', target_attr_list=f'{cube}.scaleZ')

        result = maya_test_tools.cmds.listConnections(f'{cube}.sx', source=True, plugs=True) or []
        for attr in result:
            self.assertEqual(f'{cube}.scaleY', attr)
        result = maya_test_tools.cmds.listConnections(f'{cube}.sx', destination=True, plugs=True) or []
        for attr in result:
            self.assertEqual(f'{cube}.scaleZ', attr)

    def test_list_user_defined_attr_skip_nested(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='double3', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoA", at='double', k=True, parent="custom_attr_two")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoB", at='double', k=True, parent="custom_attr_two")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoC", at='double', k=True, parent="custom_attr_two")

        result = attr_utils.list_user_defined_attr(cube, skip_nested=True, skip_parents=False)
        expected = ['custom_attr_one', 'custom_attr_two']
        self.assertEqual(expected, result)

    def test_list_user_defined_attr_keep_nested_and_parents(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='double3', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoA", at='double', k=True, parent="custom_attr_two")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoB", at='double', k=True, parent="custom_attr_two")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoC", at='double', k=True, parent="custom_attr_two")

        result = attr_utils.list_user_defined_attr(cube, skip_nested=False, skip_parents=False)
        expected = ['custom_attr_one', 'custom_attr_two',
                    'custom_attr_twoA', 'custom_attr_twoB', 'custom_attr_twoC']
        self.assertEqual(expected, result)

    def test_list_user_defined_attr_skip_parents(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='double3', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoA", at='double', k=True, parent="custom_attr_two")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoB", at='double', k=True, parent="custom_attr_two")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoC", at='double', k=True, parent="custom_attr_two")

        result = attr_utils.list_user_defined_attr(cube, skip_nested=False, skip_parents=True)
        expected = ['custom_attr_one', 'custom_attr_twoA', 'custom_attr_twoB', 'custom_attr_twoC']
        self.assertEqual(expected, result)

    def test_list_user_defined_attr_skip_nested_and_parents(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_one", at='bool', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_two", at='double3', k=True)
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoA", at='double', k=True, parent="custom_attr_two")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoB", at='double', k=True, parent="custom_attr_two")
        maya_test_tools.cmds.addAttr(cube, ln="custom_attr_twoC", at='double', k=True, parent="custom_attr_two")

        result = attr_utils.list_user_defined_attr(cube, skip_nested=True, skip_parents=True)
        expected = ['custom_attr_one']
        self.assertEqual(expected, result)