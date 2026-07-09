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
from gt.tests import maya_test_tools
from gt.core import attr as core_attr

cmds = maya_test_tools.cmds


class TestAttributeCore(unittest.TestCase):
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

        str_formatter = "{0:." + str(tolerance) + "e}"
        significand_1 = float(str_formatter.format(arg1).split("e")[0])
        significand_2 = float(str_formatter.format(arg2).split("e")[0])

        exponent_1 = int(str_formatter.format(arg1).split("e")[1])
        exponent_2 = int(str_formatter.format(arg2).split("e")[1])

        self.assertEqual(significand_1, significand_2)
        self.assertEqual(exponent_1, exponent_2)

    @patch("sys.stdout", new_callable=StringIO)
    def test_selection_delete_user_defined_attributes(self, mocked_stdout):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr_one", at="bool", k=True)
        cmds.addAttr(cube, ln="custom_attr_two", at="bool", k=True)
        cmds.setAttr(f"{cube}.custom_attr_two", lock=True)
        cmds.select(cube)
        result = cmds.listAttr(cube, userDefined=True)
        expected = ["custom_attr_one", "custom_attr_two"]
        self.assertEqual(expected, result)
        core_attr.selection_delete_user_defined_attrs()
        result = cmds.listAttr(cube, userDefined=True) or []
        expected = []
        self.assertEqual(expected, result)

    @patch("sys.stdout", new_callable=StringIO)
    def test_selection_delete_user_defined_attributes_no_locked(self, mocked_stdout):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr_one", at="bool", k=True)
        cmds.addAttr(cube, ln="custom_attr_two", at="bool", k=True)
        cmds.setAttr(f"{cube}.custom_attr_two", lock=True)
        cmds.select(cube)
        result = cmds.listAttr(cube, userDefined=True)
        expected = ["custom_attr_one", "custom_attr_two"]
        self.assertEqual(expected, result)
        core_attr.selection_delete_user_defined_attrs(delete_locked=False)
        result = cmds.listAttr(cube, userDefined=True) or []
        expected = ["custom_attr_two"]
        self.assertEqual(expected, result)

    def test_add_separator_attr(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.add_separator_attr(target_object=cube, attr_name="mySeparator")
        result = cmds.objExists(f"{cube}.mySeparator")
        self.assertTrue(result)

    def test_add_separator_attr_custom_value(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.add_separator_attr(target_object=cube, attr_name="mySeparator", custom_value="test")
        result = cmds.getAttr(f"{cube}.mySeparator", asString=True)
        expected = "test"
        self.assertEqual(expected, result)

    def test_freeze_channels_default(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.setAttr(f"{cube}.tx", 5)
        cmds.setAttr(f"{cube}.ty", 5)
        cmds.setAttr(f"{cube}.tz", 5)
        cmds.setAttr(f"{cube}.rx", 5)
        cmds.setAttr(f"{cube}.ry", 5)
        cmds.setAttr(f"{cube}.rz", 5)
        cmds.setAttr(f"{cube}.sx", 5)
        cmds.setAttr(f"{cube}.sy", 5)
        cmds.setAttr(f"{cube}.sz", 5)
        core_attr.freeze_channels(obj_list=cube)
        result_tx = cmds.getAttr(f"{cube}.tx")
        result_ty = cmds.getAttr(f"{cube}.ty")
        result_tz = cmds.getAttr(f"{cube}.tz")
        result_rx = cmds.getAttr(f"{cube}.rx")
        result_ry = cmds.getAttr(f"{cube}.ry")
        result_rz = cmds.getAttr(f"{cube}.rz")
        result_sx = cmds.getAttr(f"{cube}.sx")
        result_sy = cmds.getAttr(f"{cube}.sy")
        result_sz = cmds.getAttr(f"{cube}.sz")
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
        cmds.setAttr(f"{cube}.tx", 5)
        cmds.setAttr(f"{cube}.ty", 5)
        cmds.setAttr(f"{cube}.tz", 5)
        cmds.setAttr(f"{cube}.rx", 5)
        cmds.setAttr(f"{cube}.ry", 5)
        cmds.setAttr(f"{cube}.rz", 5)
        cmds.setAttr(f"{cube}.sx", 5)
        cmds.setAttr(f"{cube}.sy", 5)
        cmds.setAttr(f"{cube}.sz", 5)
        core_attr.freeze_channels(obj_list=cube, freeze_translate=False)
        result_tx = cmds.getAttr(f"{cube}.tx")
        result_ty = cmds.getAttr(f"{cube}.ty")
        result_tz = cmds.getAttr(f"{cube}.tz")
        result_rx = cmds.getAttr(f"{cube}.rx")
        result_ry = cmds.getAttr(f"{cube}.ry")
        result_rz = cmds.getAttr(f"{cube}.rz")
        result_sx = cmds.getAttr(f"{cube}.sx")
        result_sy = cmds.getAttr(f"{cube}.sy")
        result_sz = cmds.getAttr(f"{cube}.sz")
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
        cmds.setAttr(f"{cube}.tx", 5)
        cmds.setAttr(f"{cube}.ty", 5)
        cmds.setAttr(f"{cube}.tz", 5)
        cmds.setAttr(f"{cube}.rx", 5)
        cmds.setAttr(f"{cube}.ry", 5)
        cmds.setAttr(f"{cube}.rz", 5)
        cmds.setAttr(f"{cube}.sx", 5)
        cmds.setAttr(f"{cube}.sy", 5)
        cmds.setAttr(f"{cube}.sz", 5)
        core_attr.freeze_channels(obj_list=cube, freeze_rotate=False)
        result_tx = cmds.getAttr(f"{cube}.tx")
        result_ty = cmds.getAttr(f"{cube}.ty")
        result_tz = cmds.getAttr(f"{cube}.tz")
        result_rx = cmds.getAttr(f"{cube}.rx")
        result_ry = cmds.getAttr(f"{cube}.ry")
        result_rz = cmds.getAttr(f"{cube}.rz")
        result_sx = cmds.getAttr(f"{cube}.sx")
        result_sy = cmds.getAttr(f"{cube}.sy")
        result_sz = cmds.getAttr(f"{cube}.sz")
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
        cmds.setAttr(f"{cube}.tx", 5)
        cmds.setAttr(f"{cube}.ty", 5)
        cmds.setAttr(f"{cube}.tz", 5)
        cmds.setAttr(f"{cube}.rx", 5)
        cmds.setAttr(f"{cube}.ry", 5)
        cmds.setAttr(f"{cube}.rz", 5)
        cmds.setAttr(f"{cube}.sx", 5)
        cmds.setAttr(f"{cube}.sy", 5)
        cmds.setAttr(f"{cube}.sz", 5)
        core_attr.freeze_channels(obj_list=cube, freeze_scale=False)
        result_tx = cmds.getAttr(f"{cube}.tx")
        result_ty = cmds.getAttr(f"{cube}.ty")
        result_tz = cmds.getAttr(f"{cube}.tz")
        result_rx = cmds.getAttr(f"{cube}.rx")
        result_ry = cmds.getAttr(f"{cube}.ry")
        result_rz = cmds.getAttr(f"{cube}.rz")
        result_sx = cmds.getAttr(f"{cube}.sx")
        result_sy = cmds.getAttr(f"{cube}.sy")
        result_sz = cmds.getAttr(f"{cube}.sz")
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
        cmds.setAttr(f"{cube_one}.tx", 5)
        cmds.setAttr(f"{cube_one}.tx", 5)
        cmds.setAttr(f"{cube_one}.rx", 5)
        cmds.setAttr(f"{cube_one}.rx", 5)
        cmds.setAttr(f"{cube_one}.sx", 5)
        cmds.setAttr(f"{cube_one}.sx", 5)
        object_list = [cube_one, cube_two]
        core_attr.freeze_channels(obj_list=object_list)
        result_tx_one = cmds.getAttr(f"{cube_one}.tx")
        result_rx_one = cmds.getAttr(f"{cube_one}.rx")
        result_sx_one = cmds.getAttr(f"{cube_one}.sx")
        result_tx_two = cmds.getAttr(f"{cube_two}.tx")
        result_rx_two = cmds.getAttr(f"{cube_two}.rx")
        result_sx_two = cmds.getAttr(f"{cube_two}.sx")
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
        result_y = cmds.xform(cube + ".vtx[0]", query=True, translation=True, worldSpace=True)
        expected = [-0.5, -0.5, 0.5]  # Unchanged
        self.assertEqual(expected, result_y)
        core_attr.rescale(obj=cube, scale=5, freeze=True)
        expected = [-2.5, -2.5, 2.5]  # Changed
        result_y = cmds.xform(cube + ".vtx[0]", query=True, translation=True, worldSpace=True)
        self.assertEqual(expected, result_y)

    def test_rescale_no_freeze(self):
        cube = maya_test_tools.create_poly_cube()
        expected = 5
        core_attr.rescale(obj=cube, scale=expected, freeze=False)
        result_x = cmds.getAttr(f"{cube}.sx")
        result_y = cmds.getAttr(f"{cube}.sy")
        result_z = cmds.getAttr(f"{cube}.sz")
        self.assertEqual(expected, result_x)
        self.assertEqual(expected, result_y)
        self.assertEqual(expected, result_z)

    def test_set_attr(self):
        cube = maya_test_tools.create_poly_cube()
        out = core_attr.set_attr(f"{cube}.tx", 5)
        result = cmds.getAttr(f"{cube}.tx")
        expected = 5
        self.assertEqual(expected, result)

    def test_set_attr_string(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr", k=True, dataType="string")
        core_attr.set_attr(f"{cube}.custom_attr", "string_value")
        result = cmds.getAttr(f"{cube}.custom_attr")
        expected = "string_value"
        self.assertEqual(expected, result)

    def test_set_attr_double3(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.set_attr(obj_list=cube, attr_list="translate", value=[1, 0, 0])
        expected = [(1.0, 0.0, 0.0)]
        result = cmds.getAttr(f"{cube}.translate")
        self.assertEqual(expected, result)

    def test_set_attr_multiple_objects(self):
        cube_list = []
        for index in range(0, 10):
            cube_list.append(maya_test_tools.create_poly_cube())
        core_attr.set_attr(value=5, obj_list=cube_list, attr_list=["tx"])

        for cube in cube_list:
            result = cmds.getAttr(f"{cube}.tx")
            expected = 5
            self.assertEqual(expected, result)

    def test_set_attr_multiple_objects_and_attributes(self):
        cube_list = []
        for index in range(0, 10):
            cube_list.append(maya_test_tools.create_poly_cube())
        core_attr.set_attr(value=5, obj_list=cube_list, attr_list=["tx", "ty", "tz"])

        for cube in cube_list:
            result_x = cmds.getAttr(f"{cube}.tx")
            result_y = cmds.getAttr(f"{cube}.ty")
            result_z = cmds.getAttr(f"{cube}.tz")
            expected = 5
            self.assertEqual(expected, result_x)
            self.assertEqual(expected, result_y)
            self.assertEqual(expected, result_z)

    def test_set_attr_locked_forced(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
        cmds.setAttr(f"{cube}.custom_attr", lock=True)
        core_attr.set_attr(f"{cube}.custom_attr", value=5, force_unlock=True)
        result = cmds.getAttr(f"{cube}.custom_attr")
        expected = 5
        self.assertEqual(expected, result)

    def test_set_attr_locked_failed(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
        cmds.setAttr(f"{cube}.custom_attr", lock=True)
        logging.disable(logging.WARNING)
        core_attr.set_attr(f"{cube}.custom_attr", value=5, force_unlock=False)
        logging.disable(logging.NOTSET)
        result = cmds.getAttr(f"{cube}.custom_attr")
        expected = 0
        self.assertEqual(expected, result)

    def test_set_attr_locked_raises_exception(self):
        with self.assertRaises(RuntimeError):
            cube = maya_test_tools.create_poly_cube()
            cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
            cmds.setAttr(f"{cube}.custom_attr", lock=True)
            core_attr.set_attr(f"{cube}.custom_attr", value=5, force_unlock=False, raise_exceptions=True, verbose=False)
            result = cmds.getAttr(f"{cube}.custom_attr")
            expected = 0
            self.assertEqual(expected, result)

    def test_get_attr_float(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.setAttr(f"{cube}.tx", 5)
        result = core_attr.get_attr(f"{cube}.tx")
        expected = 5
        self.assertEqual(expected, result)

    def test_get_attr_double3(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.setAttr(f"{cube}.tx", 5)
        result = core_attr.get_attr(f"{cube}.translate")
        expected = (5, 0, 0)
        self.assertEqual(expected, result)

    def test_get_attr_string(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr", k=True, dataType="string")
        cmds.setAttr(f"{cube}.custom_attr", "string_value", typ="string")
        result = core_attr.get_attr(f"{cube}.custom_attr")
        expected = "string_value"
        self.assertEqual(expected, result)

    def test_get_attr_enum(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, longName="custom_attr", at="enum", en="zero:one:two", keyable=True)
        cmds.setAttr(f"{cube}.custom_attr", 1)
        result = core_attr.get_attr(f"{cube}.custom_attr")
        expected = 1
        self.assertEqual(expected, result)

    def test_get_attr_enum_as_string(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, longName="custom_attr", at="enum", en="zero:one:two", keyable=True)
        cmds.setAttr(f"{cube}.custom_attr", 1)
        result = core_attr.get_attr(f"{cube}.custom_attr", enum_as_string=True)
        expected = "one"
        self.assertEqual(expected, result)

    def test_get_multiple_attr_float(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.setAttr(f"{cube}.tx", 5)
        result = core_attr.get_multiple_attr(f"{cube}.tx")
        expected = {"pCube1.tx": 5.0}
        self.assertEqual(expected, result)

    def test_get_multiple_attr_double3(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.setAttr(f"{cube}.tx", 5)
        result = core_attr.get_multiple_attr(f"{cube}.translate")
        expected = {"pCube1.translate": (5.0, 0.0, 0.0)}
        self.assertEqual(expected, result)

    def test_get_multiple_attr_string(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr", k=True, dataType="string")
        cmds.setAttr(f"{cube}.custom_attr", "string_value", typ="string")
        result = core_attr.get_multiple_attr(f"{cube}.custom_attr")
        expected = {"pCube1.custom_attr": "string_value"}
        self.assertEqual(expected, result)

    def test_get_multiple_attr_enum(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, longName="custom_attr", at="enum", en="zero:one:two", keyable=True)
        cmds.setAttr(f"{cube}.custom_attr", 1)
        result = core_attr.get_multiple_attr(f"{cube}.custom_attr")
        expected = {"pCube1.custom_attr": 1}
        self.assertEqual(expected, result)

    def test_get_multiple_attr_enum_as_string(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, longName="custom_attr", at="enum", en="zero:one:two", keyable=True)
        cmds.setAttr(f"{cube}.custom_attr", 1)
        result = core_attr.get_multiple_attr(f"{cube}.custom_attr", enum_as_string=True)
        expected = {"pCube1.custom_attr": "one"}
        self.assertEqual(expected, result)

    def test_set_trs_attr_translate_world(self):
        cube = maya_test_tools.create_poly_cube()
        group = cmds.group(name="temp", empty=True, world=True)
        cmds.parent(cube, group)
        cmds.move(5, 0, 0, group)

        core_attr.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3), translate=True)

        result_tx = cmds.getAttr(f"{cube}.tx")
        result_ty = cmds.getAttr(f"{cube}.ty")
        result_tz = cmds.getAttr(f"{cube}.tz")
        expected_tx = -4  # was 1, but -5 comes from parent
        expected_ty = 2
        expected_tz = 3
        self.assertEqual(expected_tx, result_tx)
        self.assertEqual(expected_ty, result_ty)
        self.assertEqual(expected_tz, result_tz)

    def test_set_trs_attr_all_trs(self):
        cube = maya_test_tools.create_poly_cube()

        core_attr.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3), translate=True, rotate=True, scale=True)

        result_tx = cmds.getAttr(f"{cube}.tx")
        result_ty = cmds.getAttr(f"{cube}.ty")
        result_tz = cmds.getAttr(f"{cube}.tz")
        result_rx = cmds.getAttr(f"{cube}.rx")
        result_ry = cmds.getAttr(f"{cube}.ry")
        result_rz = cmds.getAttr(f"{cube}.rz")
        result_sx = cmds.getAttr(f"{cube}.sx")
        result_sy = cmds.getAttr(f"{cube}.sy")
        result_sz = cmds.getAttr(f"{cube}.sz")
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
        core_attr.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3), translate=True)

        result_tx = cmds.getAttr(f"{cube}.tx")
        result_ty = cmds.getAttr(f"{cube}.ty")
        result_tz = cmds.getAttr(f"{cube}.tz")
        expected_tx = 1
        expected_ty = 2
        expected_tz = 3
        self.assertEqual(expected_tx, result_tx)
        self.assertEqual(expected_ty, result_ty)
        self.assertEqual(expected_tz, result_tz)

    def test_set_trs_attr_rotate(self):
        cube = maya_test_tools.create_poly_cube()
        group = cmds.group(name="temp", empty=True, world=True)
        cmds.parent(cube, group)

        core_attr.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3), translate=False, rotate=True, scale=False)

        result_rx = cmds.getAttr(f"{cube}.rx")
        result_ry = cmds.getAttr(f"{cube}.ry")
        result_rz = cmds.getAttr(f"{cube}.rz")
        expected_rx = 1
        expected_ry = 2
        expected_rz = 3
        self.assertAlmostEqualSigFig(expected_rx, result_rx)
        self.assertAlmostEqualSigFig(expected_ry, result_ry)
        self.assertAlmostEqualSigFig(expected_rz, result_rz)

    def test_set_trs_attr_scale(self):
        cube = maya_test_tools.create_poly_cube()
        group = cmds.group(name="temp", empty=True, world=True)
        cmds.parent(cube, group)

        core_attr.set_trs_attr(target_obj=cube, value_tuple=(1, 2, 3), translate=False, rotate=False, scale=True)

        result_sx = cmds.getAttr(f"{cube}.sx")
        result_sy = cmds.getAttr(f"{cube}.sy")
        result_sz = cmds.getAttr(f"{cube}.sz")
        expected_sx = 1
        expected_sy = 2
        expected_sz = 3
        self.assertEqual(expected_sx, result_sx)
        self.assertEqual(expected_sy, result_sy)
        self.assertEqual(expected_sz, result_sz)

    def test_set_trs_attr_translate_object_space(self):
        cube = maya_test_tools.create_poly_cube()
        group = cmds.group(name="temp", empty=True, world=True)
        cmds.parent(cube, group)

        core_attr.set_trs_attr(
            target_obj=cube, value_tuple=(1, 2, 3), translate=True, rotate=False, scale=False, space="object"
        )

        result_tx = cmds.getAttr(f"{cube}.tx")
        result_ty = cmds.getAttr(f"{cube}.ty")
        result_tz = cmds.getAttr(f"{cube}.tz")
        expected_ty = 2
        expected_tx = 1
        expected_tz = 3
        self.assertAlmostEqualSigFig(expected_tx, result_tx)
        self.assertAlmostEqualSigFig(expected_ty, result_ty)
        self.assertAlmostEqualSigFig(expected_tz, result_tz)

    def test_set_trs_attr_rotate_object_space(self):
        cube = maya_test_tools.create_poly_cube()
        group = cmds.group(name="temp", empty=True, world=True)
        cmds.parent(cube, group)

        core_attr.set_trs_attr(
            target_obj=cube, value_tuple=(1, 2, 3), translate=False, rotate=True, scale=False, space="object"
        )

        result_rx = cmds.getAttr(f"{cube}.rx")
        result_ry = cmds.getAttr(f"{cube}.ry")
        result_rz = cmds.getAttr(f"{cube}.rz")
        expected_rx = 1
        expected_ry = 2
        expected_rz = 3
        self.assertAlmostEqualSigFig(expected_rx, result_rx)
        self.assertAlmostEqualSigFig(expected_ry, result_ry)
        self.assertAlmostEqualSigFig(expected_rz, result_rz)

    def test_set_trs_attr_scale_object_space(self):
        cube = maya_test_tools.create_poly_cube()
        group = cmds.group(name="temp", empty=True, world=True)
        cmds.parent(cube, group)

        core_attr.set_trs_attr(
            target_obj=cube, value_tuple=(1, 2, 3), translate=False, rotate=False, scale=True, space="object"
        )

        result_sx = cmds.getAttr(f"{cube}.sx")
        result_sy = cmds.getAttr(f"{cube}.sy")
        result_sz = cmds.getAttr(f"{cube}.sz")
        expected_sx = 1
        expected_sy = 2
        expected_sz = 3
        self.assertEqual(expected_sx, result_sx)
        self.assertEqual(expected_sy, result_sy)
        self.assertEqual(expected_sz, result_sz)

    def test_hide_lock_default_attributes_with_visibility(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.hide_lock_default_attrs(cube, translate=True, rotate=True, scale=True, visibility=True)

        attr_to_test = ["tx", "ty", "tz", "rx", "ty", "rz", "sx", "sy", "sz", "v"]
        for attr in attr_to_test:
            is_locked = cmds.getAttr(f"{cube}.{attr}", lock=True)
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            is_keyable_ch = cmds.getAttr(f"{cube}.{attr}", channelBox=True)
            self.assertTrue(is_locked)
            self.assertFalse(is_keyable)
            self.assertFalse(is_keyable_ch)

    def test_hide_lock_default_attributes_without_visibility(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.hide_lock_default_attrs(cube, translate=True, rotate=True, scale=True, visibility=False)

        attr_to_test = ["tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz"]
        for attr in attr_to_test:
            is_locked = cmds.getAttr(f"{cube}.{attr}", lock=True)
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            is_keyable_ch = cmds.getAttr(f"{cube}.{attr}", channelBox=True)
            self.assertTrue(is_locked)
            self.assertFalse(is_keyable)
            self.assertFalse(is_keyable_ch)

        is_locked = cmds.getAttr(f"{cube}.v", lock=True)
        is_keyable = cmds.getAttr(f"{cube}.v", keyable=True)
        self.assertFalse(is_locked)
        self.assertTrue(is_keyable)

    def test_hide_lock_default_attributes_no_translate(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.hide_lock_default_attrs(cube, translate=False, rotate=True, scale=True, visibility=False)

        attr_to_test = ["rx", "ry", "rz", "sx", "sy", "sz"]
        attr_to_test_inactive = ["tx", "ty", "tz"]
        for attr in attr_to_test:
            is_locked = cmds.getAttr(f"{cube}.{attr}", lock=True)
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            is_keyable_ch = cmds.getAttr(f"{cube}.{attr}", channelBox=True)
            self.assertTrue(is_locked, f'Expected: "{str(attr)}" to be locked.')
            self.assertFalse(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "False".')
            self.assertFalse(is_keyable_ch, f'Expected: "{str(attr)}" to have "channelBox" set to "False".')
        for attr in attr_to_test_inactive:
            is_locked = cmds.getAttr(f"{cube}.{attr}", lock=True)
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            self.assertFalse(is_locked, f'Expected: "{str(attr)}" to be unlocked.')
            self.assertTrue(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "True".')

        is_locked = cmds.getAttr(f"{cube}.v", lock=True)
        is_keyable = cmds.getAttr(f"{cube}.v", keyable=True)
        self.assertFalse(is_locked)
        self.assertTrue(is_keyable)

    def test_hide_lock_default_attributes_no_rotate(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.hide_lock_default_attrs(cube, translate=True, rotate=False, scale=True, visibility=False)

        attr_to_test = ["tx", "ty", "tz", "sx", "sy", "sz"]
        attr_to_test_inactive = ["rx", "ry", "rz"]
        for attr in attr_to_test:
            is_locked = cmds.getAttr(f"{cube}.{attr}", lock=True)
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            is_keyable_ch = cmds.getAttr(f"{cube}.{attr}", channelBox=True)
            self.assertTrue(is_locked, f'Expected: "{str(attr)}" to be locked.')
            self.assertFalse(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "False".')
            self.assertFalse(is_keyable_ch, f'Expected: "{str(attr)}" to have "channelBox" set to "False".')
        for attr in attr_to_test_inactive:
            is_locked = cmds.getAttr(f"{cube}.{attr}", lock=True)
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            self.assertFalse(is_locked, f'Expected: "{str(attr)}" to be unlocked.')
            self.assertTrue(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "True".')

        is_locked = cmds.getAttr(f"{cube}.v", lock=True)
        is_keyable = cmds.getAttr(f"{cube}.v", keyable=True)
        self.assertFalse(is_locked)
        self.assertTrue(is_keyable)

    def test_hide_lock_default_attributes_no_scale(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.hide_lock_default_attrs(cube, translate=True, rotate=True, scale=False, visibility=False)

        attr_to_test = ["tx", "ty", "tz", "rx", "ry", "rz"]
        attr_to_test_inactive = ["sx", "sy", "sz"]
        for attr in attr_to_test:
            is_locked = cmds.getAttr(f"{cube}.{attr}", lock=True)
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            is_keyable_ch = cmds.getAttr(f"{cube}.{attr}", channelBox=True)
            self.assertTrue(is_locked, f'Expected: "{str(attr)}" to be locked.')
            self.assertFalse(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "False".')
            self.assertFalse(is_keyable_ch, f'Expected: "{str(attr)}" to have "channelBox" set to "False".')
        for attr in attr_to_test_inactive:
            is_locked = cmds.getAttr(f"{cube}.{attr}", lock=True)
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            self.assertFalse(is_locked, f'Expected: "{str(attr)}" to be unlocked.')
            self.assertTrue(is_keyable, f'Expected: "{str(attr)}" to have "keyable" set to "True".')

        is_locked = cmds.getAttr(f"{cube}.v", lock=True)
        is_keyable = cmds.getAttr(f"{cube}.v", keyable=True)
        self.assertFalse(is_locked)
        self.assertTrue(is_keyable)

    def test_add_attr_double_three(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.add_attr_double_three(obj=cube, attr_name="mockedAttr")

        attr_type = cmds.getAttr(f"{cube}.mockedAttr", type=True)
        expected = "double3"
        self.assertEqual(expected, attr_type)
        is_keyable = cmds.getAttr(f"{cube}.mockedAttr", keyable=True)
        self.assertTrue(is_keyable)

        expected = "double"
        attr_to_test = ["mockedAttrR", "mockedAttrG", "mockedAttrB"]
        for attr in attr_to_test:
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            self.assertTrue(is_keyable)
            attr_type = cmds.getAttr(f"{cube}.{attr}", type=True)
            self.assertEqual(expected, attr_type)

    def test_add_attr_double_three_suffix(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.add_attr_double_three(obj=cube, attr_name="mockedAttr", suffix="ABC")

        self.assertTrue(cmds.objExists(f"{cube}.mockedAttr"))
        attr_type = cmds.getAttr(f"{cube}.mockedAttr", type=True)
        expected = "double3"
        self.assertEqual(expected, attr_type)
        is_keyable = cmds.getAttr(f"{cube}.mockedAttr", keyable=True)
        self.assertTrue(is_keyable)

        expected = "double"
        attr_to_test = ["mockedAttrA", "mockedAttrB", "mockedAttrC"]
        for attr in attr_to_test:
            self.assertTrue(cmds.objExists(f"{cube}.{attr}"))
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            self.assertTrue(is_keyable)
            attr_type = cmds.getAttr(f"{cube}.{attr}", type=True)
            self.assertEqual(expected, attr_type)

    def test_add_attr_double_three_keyable(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.add_attr_double_three(obj=cube, attr_name="mockedAttr", suffix="ABC", keyable=False)

        self.assertTrue(cmds.objExists(f"{cube}.mockedAttr"))
        attr_type = cmds.getAttr(f"{cube}.mockedAttr", type=True)
        expected = "double3"
        self.assertEqual(expected, attr_type)

        expected = "double"
        attr_to_test = ["mockedAttrA", "mockedAttrB", "mockedAttrC"]
        for attr in attr_to_test:
            self.assertTrue(cmds.objExists(f"{cube}.{attr}"))
            is_keyable = cmds.getAttr(f"{cube}.{attr}", keyable=True)
            self.assertFalse(is_keyable)
            attr_type = cmds.getAttr(f"{cube}.{attr}", type=True)
            self.assertEqual(expected, attr_type)

    def test_get_trs_attr_as_list(self):
        cube = maya_test_tools.create_poly_cube()

        cmds.setAttr(f"{cube}.tx", 5)
        cmds.setAttr(f"{cube}.rx", 5)
        cmds.setAttr(f"{cube}.sx", 5)

        result = core_attr.get_trs_attr_as_list(cube)
        expected = [5, 0, 0, 5, 0, 0, 5, 1, 1]
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_formatted_string(self):
        cube = maya_test_tools.create_poly_cube()

        cmds.setAttr(f"{cube}.tx", 5)
        cmds.setAttr(f"{cube}.rx", 5)
        cmds.setAttr(f"{cube}.sx", 5)

        result = core_attr.get_trs_attr_as_formatted_string(cube)
        expected = 'source_obj = "pCube1"\ntrs_attr_list = [5, 0, 0, 5, 0, 0, 5, 1, 1]'
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_formatted_string_description(self):
        cube = maya_test_tools.create_poly_cube()

        cmds.setAttr(f"{cube}.tx", 5)
        cmds.setAttr(f"{cube}.rx", 5)
        cmds.setAttr(f"{cube}.sx", 5)

        result = core_attr.get_trs_attr_as_formatted_string(cube, add_description=True)
        expected = '# Transform Data for "pCube1":\nsource_obj = "pCube1"\ntrs_attr_list = [5, 0, 0, 5, 0, 0, 5, 1, 1]'
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_formatted_string_no_object(self):
        cube = maya_test_tools.create_poly_cube()

        cmds.setAttr(f"{cube}.tx", 5)
        cmds.setAttr(f"{cube}.rx", 5)
        cmds.setAttr(f"{cube}.sx", 5)

        result = core_attr.get_trs_attr_as_formatted_string(cube, add_object=False)
        expected = "trs_attr_list = [5, 0, 0, 5, 0, 0, 5, 1, 1]"
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_formatted_string_separated_channels(self):
        cube = maya_test_tools.create_poly_cube()

        cmds.setAttr(f"{cube}.tx", 5)
        cmds.setAttr(f"{cube}.rx", 5)
        cmds.setAttr(f"{cube}.sx", 5)

        result = core_attr.get_trs_attr_as_formatted_string(cube, separate_channels=True, add_object=False)
        expected = "t_attr_list = [5, 0, 0]\nr_attr_list = [5, 0, 0]\ns_attr_list = [5, 1, 1]"
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
        result = core_attr.add_attr(target_list, attributes, attr_type, minimum, maximum, default, is_keyable, verbose)

        # Define expected results
        expected_added_attrs = [f"{cube_one}.attr1", f"{cube_one}.attr2", f"{cube_two}.attr1", f"{cube_two}.attr2"]

        # Assert expected results
        self.assertEqual(result, expected_added_attrs)
        for obj in target_list:
            for attr_name in attributes:
                full_attr_name = f"{obj}.{attr_name}"
                exists = cmds.objExists(full_attr_name)
                self.assertTrue(exists)
                type_result = cmds.getAttr(full_attr_name, type=True)
                self.assertEqual(attr_type, type_result)
                min_val = cmds.attributeQuery(attr_name, node=obj, min=True)
                expected = [minimum]
                self.assertEqual(expected, min_val)
                exists_max = cmds.attributeQuery(attr_name, node=obj, max=True)
                expected = [maximum]
                self.assertEqual(expected, exists_max)
                exists_default = cmds.attributeQuery(attr_name, node=obj, exists=True)
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
        result = core_attr.add_attr(target_list, attribute, attr_type, minimum, maximum, default, is_keyable, verbose)

        # Define expected results
        expected_added_attrs = [f"{cube_one}.attr1"]

        # Assert expected results
        self.assertEqual(result, expected_added_attrs)

        full_attr_name = f"{cube_one}.{attribute}"
        exists = cmds.objExists(full_attr_name)
        self.assertTrue(exists)
        type_result = cmds.getAttr(full_attr_name, type=True)
        self.assertEqual(attr_type, type_result)
        min_val = cmds.attributeQuery(attribute, node=cube_one, min=True)
        expected = [minimum]
        self.assertEqual(expected, min_val)
        exists_max = cmds.attributeQuery(attribute, node=cube_one, max=True)
        expected = [maximum]
        self.assertEqual(expected, exists_max)
        exists_default = cmds.attributeQuery(attribute, node=cube_one, exists=True)
        self.assertTrue(exists_default)

    def test_add_attributes_string_default_value(self):
        cube_one = maya_test_tools.create_poly_cube()

        # Test data
        target_list = cube_one
        attribute = "attr1"
        attr_type = "string"
        default = "mocked_string"
        is_keyable = True
        verbose = False

        # Call the function
        result = core_attr.add_attr(
            obj_list=target_list,
            attributes=attribute,
            attr_type=attr_type,
            default=default,
            is_keyable=is_keyable,
            verbose=verbose,
        )

        # Created Attributes
        expected_added_attrs = [f"{cube_one}.attr1"]
        self.assertEqual(result, expected_added_attrs)

        full_attr_name = f"{cube_one}.{attribute}"
        exists = cmds.objExists(full_attr_name)
        self.assertTrue(exists)
        type_result = cmds.getAttr(full_attr_name, type=True)
        self.assertEqual(attr_type, type_result)
        exists_default = cmds.attributeQuery(attribute, node=cube_one, exists=True)
        self.assertTrue(exists_default)
        string_value = cmds.getAttr(full_attr_name)
        self.assertEqual(default, string_value)

    def test_get_trs_attr_as_python(self):
        cube = maya_test_tools.create_poly_cube()

        result = core_attr.get_trs_attr_as_python(cube)
        expected = (
            '# Transform Data for "pCube1":\ncmds.setAttr("pCube1.tx", 0)\ncmds.setAttr("pCube1.ty", 0)\n'
            'cmds.setAttr("pCube1.tz", 0)\ncmds.setAttr("pCube1.rx", 0)\ncmds.setAttr("pCube1.ry", 0)\n'
            'cmds.setAttr("pCube1.rz", 0)\ncmds.setAttr("pCube1.sx", 1)\ncmds.setAttr("pCube1.sy", 1)\n'
            'cmds.setAttr("pCube1.sz", 1)'
        )
        self.assertEqual(expected, result)
        result = core_attr.get_trs_attr_as_python([cube, cube])
        expected = f"{expected}\n\n{expected}"
        self.assertEqual(expected, result)

    def test_get_trs_attr_as_python_loop(self):
        cube = maya_test_tools.create_poly_cube()

        result = core_attr.get_trs_attr_as_python(cube, use_loop=True)
        expected = (
            '# Transform Data for "pCube1":\nfor key, value in {"tx": 0.0, "ty": 0.0, "tz": 0.0, "rx": 0.0, '
            '"ry": 0.0, "rz": 0.0, "sx": 1.0, "sy": 1.0, "sz": 1.0}.items():\n\tif not '
            'cmds.getAttr(f"pCube1.{key}", lock=True):\n\t\tcmds.setAttr(f"pCube1.{key}", value)'
        )
        self.assertEqual(expected, result)
        result = core_attr.get_trs_attr_as_python([cube, cube], use_loop=True)
        expected = f"{expected}\n\n{expected}"
        self.assertEqual(expected, result)

    def test_get_user_attr_to_python(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr_one", at="bool", k=True)
        cmds.addAttr(cube, ln="custom_attr_two", at="float", k=True)
        result = core_attr.get_user_attr_to_python(cube)
        expected = (
            '# User-Defined Attribute Data for "pCube1":\ncmds.setAttr("pCube1.custom_attr_one", False)\n'
            'cmds.setAttr("pCube1.custom_attr_two", 0.0)'
        )
        self.assertEqual(expected, result)
        result = core_attr.get_user_attr_to_python([cube, cube])
        expected = f"{expected}\n\n{expected}"
        self.assertEqual(expected, result)

    def test_get_user_attr_to_python_locked(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr_one", at="bool", k=True)
        cmds.addAttr(cube, ln="custom_attr_two", at="float", k=True)
        cmds.addAttr(cube, ln="custom_attr_three", at="float", k=True)
        cmds.setAttr(f"{cube}.custom_attr_three", lock=True)
        result = core_attr.get_user_attr_to_python(cube, skip_locked=True)
        expected = (
            '# User-Defined Attribute Data for "pCube1":\ncmds.setAttr("pCube1.custom_attr_one", False)\n'
            'cmds.setAttr("pCube1.custom_attr_two", 0.0)'
        )
        self.assertEqual(expected, result)
        result = core_attr.get_user_attr_to_python([cube, cube], skip_locked=True)
        expected = f"{expected}\n\n{expected}"
        self.assertEqual(expected, result)
        result = core_attr.get_user_attr_to_python(cube, skip_locked=False)
        expected = (
            '# User-Defined Attribute Data for "pCube1":\ncmds.setAttr("pCube1.custom_attr_one", False)\n'
            'cmds.setAttr("pCube1.custom_attr_two", 0.0)\ncmds.setAttr("pCube1.custom_attr_three", 0.0)'
        )
        self.assertEqual(expected, result)
        result = core_attr.get_user_attr_to_python([cube, cube], skip_locked=False)
        expected = f"{expected}\n\n{expected}"
        self.assertEqual(expected, result)

    def test_set_attr_state_lock_attribute(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.set_attr_state(attribute_path=f"{cube}.tx", locked=True)
        locked_state = cmds.getAttr(f"{cube}.tx", lock=True)
        self.assertTrue(locked_state)

    def test_set_attr_state_hide_attribute(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.set_attr_state(attribute_path=f"{cube}.ty", hidden=True)
        keyable_state = cmds.getAttr(f"{cube}.ty", keyable=True)
        channel_box_state = cmds.getAttr(f"{cube}.ty", channelBox=True)
        locked_state = cmds.getAttr(f"{cube}.tx", lock=True)
        self.assertFalse(keyable_state)
        self.assertFalse(channel_box_state)
        self.assertFalse(locked_state)

    def test_set_attr_state_lock_and_hide_attribute(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.set_attr_state(attribute_path=f"{cube}.tz", locked=True, hidden=True)
        locked_state = cmds.getAttr(f"{cube}.tz", lock=True)
        keyable_state = cmds.getAttr(f"{cube}.tz", keyable=True)
        channel_box_state = cmds.getAttr(f"{cube}.tz", channelBox=True)
        self.assertTrue(locked_state)
        self.assertFalse(keyable_state)
        self.assertFalse(channel_box_state)

    def test_set_attr_state_lock_and_hide_multiple_attributes(self):
        cube = maya_test_tools.create_poly_cube()
        core_attr.set_attr_state(obj_list=[cube], attr_list=["tx", "ty"], locked=True, hidden=True)
        tx_locked_state = cmds.getAttr(f"{cube}.tx", lock=True)
        tx_keyable_state = cmds.getAttr(f"{cube}.tx", keyable=True)
        tx_channel_box_state = cmds.getAttr(f"{cube}.tx", channelBox=True)
        ty_locked_state = cmds.getAttr(f"{cube}.ty", lock=True)
        ty_keyable_state = cmds.getAttr(f"{cube}.ty", keyable=True)
        ty_channel_box_state = cmds.getAttr(f"{cube}.ty", channelBox=True)
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
            cmds.setAttr(f"{obj}.tx", lock=True)
            cmds.setAttr(f"{obj}.ty", lock=True)
            cmds.setAttr(f"{obj}.tz", lock=True)
            cmds.setAttr(f"{obj}.rx", lock=True)
            cmds.setAttr(f"{obj}.ry", lock=True)
            cmds.setAttr(f"{obj}.rz", lock=True)
            cmds.setAttr(f"{obj}.sx", lock=True)
            cmds.setAttr(f"{obj}.sy", lock=True)
            cmds.setAttr(f"{obj}.sz", lock=True)
            # Test State -----------------------------------
            tx_locked_state = cmds.getAttr(f"{obj}.tx", lock=True)
            ty_locked_state = cmds.getAttr(f"{obj}.ty", lock=True)
            tz_locked_state = cmds.getAttr(f"{obj}.tz", lock=True)
            rx_locked_state = cmds.getAttr(f"{obj}.rx", lock=True)
            ry_locked_state = cmds.getAttr(f"{obj}.ry", lock=True)
            rz_locked_state = cmds.getAttr(f"{obj}.rz", lock=True)
            sx_locked_state = cmds.getAttr(f"{obj}.sx", lock=True)
            sy_locked_state = cmds.getAttr(f"{obj}.sy", lock=True)
            sz_locked_state = cmds.getAttr(f"{obj}.sz", lock=True)
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
            cmds.select([cube_one, cube_two])
            result = core_attr.selection_unlock_default_channels(feedback=False)
            # Test State -----------------------------------
            tx_locked_state = cmds.getAttr(f"{obj}.tx", lock=True)
            ty_locked_state = cmds.getAttr(f"{obj}.ty", lock=True)
            tz_locked_state = cmds.getAttr(f"{obj}.tz", lock=True)
            rx_locked_state = cmds.getAttr(f"{obj}.rx", lock=True)
            ry_locked_state = cmds.getAttr(f"{obj}.ry", lock=True)
            rz_locked_state = cmds.getAttr(f"{obj}.rz", lock=True)
            sx_locked_state = cmds.getAttr(f"{obj}.sx", lock=True)
            sy_locked_state = cmds.getAttr(f"{obj}.sy", lock=True)
            sz_locked_state = cmds.getAttr(f"{obj}.sz", lock=True)
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
            cmds.setAttr(f"{obj}.tx", lock=True)
            cmds.setAttr(f"{obj}.ty", lock=True)
            cmds.setAttr(f"{obj}.tz", lock=True)
            cmds.setAttr(f"{obj}.rx", lock=True)
            cmds.setAttr(f"{obj}.ry", lock=True)
            cmds.setAttr(f"{obj}.rz", lock=True)
            cmds.setAttr(f"{obj}.sx", lock=True)
            cmds.setAttr(f"{obj}.sy", lock=True)
            cmds.setAttr(f"{obj}.sz", lock=True)
            # Test State -----------------------------------
            tx_locked_state = cmds.getAttr(f"{obj}.tx", lock=True)
            ty_locked_state = cmds.getAttr(f"{obj}.ty", lock=True)
            tz_locked_state = cmds.getAttr(f"{obj}.tz", lock=True)
            rx_locked_state = cmds.getAttr(f"{obj}.rx", lock=True)
            ry_locked_state = cmds.getAttr(f"{obj}.ry", lock=True)
            rz_locked_state = cmds.getAttr(f"{obj}.rz", lock=True)
            sx_locked_state = cmds.getAttr(f"{obj}.sx", lock=True)
            sy_locked_state = cmds.getAttr(f"{obj}.sy", lock=True)
            sz_locked_state = cmds.getAttr(f"{obj}.sz", lock=True)
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
            cmds.select([cube_one, cube_two])
            result = core_attr.selection_unlock_default_channels(feedback=False)
            # Test State -----------------------------------
            tx_locked_state = cmds.getAttr(f"{obj}.tx", lock=True)
            ty_locked_state = cmds.getAttr(f"{obj}.ty", lock=True)
            tz_locked_state = cmds.getAttr(f"{obj}.tz", lock=True)
            rx_locked_state = cmds.getAttr(f"{obj}.rx", lock=True)
            ry_locked_state = cmds.getAttr(f"{obj}.ry", lock=True)
            rz_locked_state = cmds.getAttr(f"{obj}.rz", lock=True)
            sx_locked_state = cmds.getAttr(f"{obj}.sx", lock=True)
            sy_locked_state = cmds.getAttr(f"{obj}.sy", lock=True)
            sz_locked_state = cmds.getAttr(f"{obj}.sz", lock=True)
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
        cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
        cmds.addAttr(cube, ln="custom_attr_two", k=True, at="float")
        cmds.setAttr(f"{cube}.custom_attr", lock=True)

        result = core_attr.delete_user_defined_attrs(cube)

        attr_one = cmds.objExists(f"{cube}.custom_attr")
        self.assertFalse(attr_one)
        attr_two = cmds.objExists(f"{cube}.custom_attr_two")
        self.assertFalse(attr_two)

        expected = [f"{cube}.custom_attr", f"{cube}.custom_attr_two"]
        self.assertEqual(expected, result)

    def test_delete_user_defined_attributes_no_lock(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr", k=True, at="float")
        cmds.addAttr(cube, ln="custom_attr_two", k=True, at="float")
        cmds.setAttr(f"{cube}.custom_attr", lock=True)

        result = core_attr.delete_user_defined_attrs(cube, delete_locked=False)

        attr_one = cmds.objExists(f"{cube}.custom_attr")
        self.assertTrue(attr_one)
        attr_two = cmds.objExists(f"{cube}.custom_attr_two")
        self.assertFalse(attr_two)

        expected = [f"{cube}.custom_attr_two"]
        self.assertEqual(expected, result)

    def test_connect_attr(self):
        cube = maya_test_tools.create_poly_cube()

        target_attr_list = [f"{cube}.scaleX", f"{cube}.scaleZ"]
        core_attr.connect_attr(source_attr=f"{cube}.scaleY", target_attr_list=target_attr_list)

        result = cmds.listConnections(f"{cube}.sy", destination=True, plugs=True)
        for attr in target_attr_list:
            self.assertIn(attr, result)

        result = cmds.listConnections(f"{cube}.sx", source=True, plugs=True) or []
        for attr in result:
            self.assertEqual(f"{cube}.scaleY", attr)

    def test_connect_attr_str_input(self):
        cube = maya_test_tools.create_poly_cube()

        core_attr.connect_attr(source_attr=f"{cube}.scaleY", target_attr_list=f"{cube}.scaleZ")

        result = cmds.listConnections(f"{cube}.sx", source=True, plugs=True) or []
        for attr in result:
            self.assertEqual(f"{cube}.scaleY", attr)
        result = cmds.listConnections(f"{cube}.sx", destination=True, plugs=True) or []
        for attr in result:
            self.assertEqual(f"{cube}.scaleZ", attr)

    def test_list_user_defined_attr_skip_nested(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr_one", at="bool", k=True)
        cmds.addAttr(cube, ln="custom_attr_two", at="double3", k=True)
        cmds.addAttr(cube, ln="custom_attr_twoA", at="double", k=True, parent="custom_attr_two")
        cmds.addAttr(cube, ln="custom_attr_twoB", at="double", k=True, parent="custom_attr_two")
        cmds.addAttr(cube, ln="custom_attr_twoC", at="double", k=True, parent="custom_attr_two")

        result = core_attr.list_user_defined_attr(cube, skip_nested=True, skip_parents=False)
        expected = ["custom_attr_one", "custom_attr_two"]
        self.assertEqual(expected, result)

    def test_list_user_defined_attr_keep_nested_and_parents(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr_one", at="bool", k=True)
        cmds.addAttr(cube, ln="custom_attr_two", at="double3", k=True)
        cmds.addAttr(cube, ln="custom_attr_twoA", at="double", k=True, parent="custom_attr_two")
        cmds.addAttr(cube, ln="custom_attr_twoB", at="double", k=True, parent="custom_attr_two")
        cmds.addAttr(cube, ln="custom_attr_twoC", at="double", k=True, parent="custom_attr_two")

        result = core_attr.list_user_defined_attr(cube, skip_nested=False, skip_parents=False)
        expected = ["custom_attr_one", "custom_attr_two", "custom_attr_twoA", "custom_attr_twoB", "custom_attr_twoC"]
        self.assertEqual(expected, result)

    def test_list_user_defined_attr_skip_parents(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr_one", at="bool", k=True)
        cmds.addAttr(cube, ln="custom_attr_two", at="double3", k=True)
        cmds.addAttr(cube, ln="custom_attr_twoA", at="double", k=True, parent="custom_attr_two")
        cmds.addAttr(cube, ln="custom_attr_twoB", at="double", k=True, parent="custom_attr_two")
        cmds.addAttr(cube, ln="custom_attr_twoC", at="double", k=True, parent="custom_attr_two")

        result = core_attr.list_user_defined_attr(cube, skip_nested=False, skip_parents=True)
        expected = ["custom_attr_one", "custom_attr_twoA", "custom_attr_twoB", "custom_attr_twoC"]
        self.assertEqual(expected, result)

    def test_list_user_defined_attr_skip_nested_and_parents(self):
        cube = maya_test_tools.create_poly_cube()
        cmds.addAttr(cube, ln="custom_attr_one", at="bool", k=True)
        cmds.addAttr(cube, ln="custom_attr_two", at="double3", k=True)
        cmds.addAttr(cube, ln="custom_attr_twoA", at="double", k=True, parent="custom_attr_two")
        cmds.addAttr(cube, ln="custom_attr_twoB", at="double", k=True, parent="custom_attr_two")
        cmds.addAttr(cube, ln="custom_attr_twoC", at="double", k=True, parent="custom_attr_two")

        result = core_attr.list_user_defined_attr(cube, skip_nested=True, skip_parents=True)
        expected = ["custom_attr_one"]
        self.assertEqual(expected, result)

    def test_copy_attr(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.doubleAttr", target_list=cube_two)
        expected = [f"{cube_two}.doubleAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.doubleAttr")
        expected = 2.5
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.intAttr", target_list=cube_two)
        expected = [f"{cube_two}.intAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.intAttr")
        expected = 3
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.enumAttr", target_list=cube_two)
        expected = [f"{cube_two}.enumAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.enumAttr")
        expected = 2
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.boolAttr", target_list=cube_two)
        expected = [f"{cube_two}.boolAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.boolAttr")
        expected = True
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.stringAttr", target_list=cube_two)
        expected = [f"{cube_two}.stringAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.stringAttr")
        expected = "mocked_content"
        self.assertEqual(expected, result)

    def test_copy_attr_prefix(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.doubleAttr", target_list=cube_two, prefix="prefix")
        expected = [f"{cube_two}.prefixDoubleAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.prefixDoubleAttr")
        expected = 2.5
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.intAttr", target_list=cube_two, prefix="prefix")
        expected = [f"{cube_two}.prefixIntAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.prefixIntAttr")
        expected = 3
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.enumAttr", target_list=cube_two, prefix="prefix")
        expected = [f"{cube_two}.prefixEnumAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.prefixEnumAttr")
        expected = 2
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.boolAttr", target_list=cube_two, prefix="prefix")
        expected = [f"{cube_two}.prefixBoolAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.prefixBoolAttr")
        expected = True
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(source_attr_path=f"{cube_one}.stringAttr", target_list=cube_two, prefix="prefix")
        expected = [f"{cube_two}.prefixStringAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.prefixStringAttr")
        expected = "mocked_content"
        self.assertEqual(expected, result)

    def test_copy_attr_override_name(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.doubleAttr", target_list=cube_two, override_name="mockedDouble"
        )
        expected = [f"{cube_two}.mockedDouble"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.mockedDouble")
        expected = 2.5
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.intAttr", target_list=cube_two, override_name="mockedInt"
        )
        expected = [f"{cube_two}.mockedInt"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.mockedInt")
        expected = 3
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.enumAttr", target_list=cube_two, override_name="mockedEnum"
        )
        expected = [f"{cube_two}.mockedEnum"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.mockedEnum")
        expected = 2
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.boolAttr", target_list=cube_two, override_name="mockedBool"
        )
        expected = [f"{cube_two}.mockedBool"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.mockedBool")
        expected = True
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.stringAttr", target_list=cube_two, override_name="mockedString"
        )
        expected = [f"{cube_two}.mockedString"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.mockedString")
        expected = "mocked_content"
        self.assertEqual(expected, result)

    def test_copy_attr_override_keyable(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.doubleAttr", target_list=cube_two, override_keyable=False
        )
        expected = [f"{cube_two}.doubleAttr"]
        self.assertEqual(expected, result)
        result = cmds.getAttr(f"{cube_two}.doubleAttr")
        expected = 2.5
        self.assertEqual(expected, result)

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.intAttr", target_list=cube_two, override_keyable=False
        )
        expected = [f"{cube_two}.intAttr"]
        self.assertEqual(expected, result)
        self.assertFalse(cmds.getAttr(f"{cube_two}.intAttr", keyable=True))

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.enumAttr", target_list=cube_two, override_keyable=False
        )
        expected = [f"{cube_two}.enumAttr"]
        self.assertEqual(expected, result)
        self.assertFalse(cmds.getAttr(f"{cube_two}.enumAttr", keyable=True))

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.boolAttr", target_list=cube_two, override_keyable=False
        )
        expected = [f"{cube_two}.boolAttr"]
        self.assertEqual(expected, result)
        self.assertFalse(cmds.getAttr(f"{cube_two}.boolAttr", keyable=True))

        result = core_attr.copy_attr(
            source_attr_path=f"{cube_one}.stringAttr", target_list=cube_two, override_keyable=False
        )
        expected = [f"{cube_two}.stringAttr"]
        self.assertEqual(expected, result)
        self.assertFalse(cmds.getAttr(f"{cube_two}.stringAttr", keyable=True))

    def test_reroute_attr(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        source_attrs = [
            f"{cube_one}.doubleAttr",
            f"{cube_one}.intAttr",
            f"{cube_one}.enumAttr",
            f"{cube_one}.boolAttr",
            f"{cube_one}.stringAttr",
        ]
        result = core_attr.reroute_attr(source_attrs=source_attrs, target_obj=cube_two)
        expected = [
            f"{cube_two}.doubleAttr",
            f"{cube_two}.intAttr",
            f"{cube_two}.enumAttr",
            f"{cube_two}.boolAttr",
            f"{cube_two}.stringAttr",
        ]
        self.assertEqual(expected, result)

        cmds.setAttr(f"{cube_two}.doubleAttr", 3.5)
        cmds.setAttr(f"{cube_two}.intAttr", 4)
        cmds.setAttr(f"{cube_two}.enumAttr", 1)
        cmds.setAttr(f"{cube_two}.boolAttr", False)
        cmds.setAttr(f"{cube_two}.stringAttr", "mocked_content_two", type="string")

        result = cmds.getAttr(f"{cube_one}.doubleAttr")
        expected = 3.5
        self.assertEqual(expected, result)

        result = cmds.getAttr(f"{cube_one}.intAttr")
        expected = 4
        self.assertEqual(expected, result)

        result = cmds.getAttr(f"{cube_one}.enumAttr")
        expected = 1
        self.assertEqual(expected, result)

        result = cmds.getAttr(f"{cube_one}.boolAttr")
        expected = False
        self.assertEqual(expected, result)

        result = cmds.getAttr(f"{cube_one}.stringAttr")
        expected = "mocked_content_two"
        self.assertEqual(expected, result)

    def test_get_attrs_as_dict(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        expected_attr = [
            "cube_one.tx",
            "cube_one.ty",
            "cube_one.tz",
            "cube_one.rx",
            "cube_one.ry",
            "cube_one.rz",
            "cube_one.sx",
            "cube_one.sy",
            "cube_one.sz",
            "cube_one.v",
            "cube_one.doubleAttr",
            "cube_one.intAttr",
            "cube_one.enumAttr",
            "cube_one.boolAttr",
            "cube_one.stringAttr",
        ]

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one)
        result_keys_list = list(result_dict.keys())

        self.assertEqual(expected_attr, result_keys_list)

        expected_dict = {
            "cube_one.boolAttr": True,
            "cube_one.doubleAttr": 2.5,
            "cube_one.enumAttr": 2,
            "cube_one.intAttr": 3,
            "cube_one.rx": 0.0,
            "cube_one.ry": 0.0,
            "cube_one.rz": 0.0,
            "cube_one.stringAttr": "mocked_content",
            "cube_one.sx": 1.0,
            "cube_one.sy": 1.0,
            "cube_one.sz": 1.0,
            "cube_one.tx": 0.0,
            "cube_one.ty": 0.0,
            "cube_one.tz": 0.0,
            "cube_one.v": True,
        }
        self.assertEqual(expected_dict, result_dict)

        # Change Values
        cmds.setAttr(f"{cube_one}.tx", 1)
        cmds.setAttr(f"{cube_one}.ty", 2)
        cmds.setAttr(f"{cube_one}.tz", 3)
        cmds.setAttr(f"{cube_one}.doubleAttr", 3.5)
        cmds.setAttr(f"{cube_one}.intAttr", 4)
        cmds.setAttr(f"{cube_one}.enumAttr", 1)
        cmds.setAttr(f"{cube_one}.boolAttr", False)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content_two", type="string")

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one)
        expected_dict = {
            "cube_one.boolAttr": False,
            "cube_one.doubleAttr": 3.5,
            "cube_one.enumAttr": 1,
            "cube_one.intAttr": 4,
            "cube_one.rx": 0.0,
            "cube_one.ry": 0.0,
            "cube_one.rz": 0.0,
            "cube_one.stringAttr": "mocked_content_two",
            "cube_one.sx": 1.0,
            "cube_one.sy": 1.0,
            "cube_one.sz": 1.0,
            "cube_one.tx": 1.0,
            "cube_one.ty": 2.0,
            "cube_one.tz": 3.0,
            "cube_one.v": True,
        }
        self.assertEqual(expected_dict, result_dict)

    def test_get_attrs_as_dict_filter_locked(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        # Lock TRS
        cmds.setAttr(f"{cube_one}.tx", lock=True)
        cmds.setAttr(f"{cube_one}.ry", lock=True)
        cmds.setAttr(f"{cube_one}.sz", lock=True)

        expected_attr = [
            # "cube_one.tx",
            "cube_one.ty",
            "cube_one.tz",
            "cube_one.rx",
            # "cube_one.ry",
            "cube_one.rz",
            "cube_one.sx",
            "cube_one.sy",
            # "cube_one.sz",
            "cube_one.v",
            "cube_one.doubleAttr",
            "cube_one.intAttr",
            "cube_one.enumAttr",
            "cube_one.boolAttr",
            "cube_one.stringAttr",
        ]

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, filter_locked=True, filter_connected=False)
        result_keys_list = list(result_dict.keys())

        self.assertEqual(expected_attr, result_keys_list)

        # Lock User-defined
        cmds.setAttr(f"{cube_one}.doubleAttr", lock=True)
        cmds.setAttr(f"{cube_one}.intAttr", lock=True)

        expected_attr = [
            # "cube_one.tx",
            "cube_one.ty",
            "cube_one.tz",
            "cube_one.rx",
            # "cube_one.ry",
            "cube_one.rz",
            "cube_one.sx",
            "cube_one.sy",
            # "cube_one.sz",
            "cube_one.v",
            # "cube_one.doubleAttr",
            # "cube_one.intAttr",
            "cube_one.enumAttr",
            "cube_one.boolAttr",
            "cube_one.stringAttr",
        ]

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, full_attr_path=True)
        result_keys_list = list(result_dict.keys())

        self.assertEqual(expected_attr, result_keys_list)

    def test_get_attrs_as_dict_filter_connected(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        # Lock and Connect TRS
        cmds.setAttr(f"{cube_one}.tx", lock=True)
        cmds.setAttr(f"{cube_one}.ry", lock=True)
        cmds.setAttr(f"{cube_one}.sz", lock=True)
        cmds.connectAttr(f"{cube_two}.ty", f"{cube_one}.ty")
        cmds.connectAttr(f"{cube_two}.rx", f"{cube_one}.rx")
        cmds.connectAttr(f"{cube_two}.sx", f"{cube_one}.sx")

        expected_attr = [
            "cube_one.tx",
            # "cube_one.ty",
            "cube_one.tz",
            # "cube_one.rx",
            "cube_one.ry",
            "cube_one.rz",
            # "cube_one.sx",
            "cube_one.sy",
            "cube_one.sz",
            "cube_one.v",
            "cube_one.doubleAttr",
            "cube_one.intAttr",
            "cube_one.enumAttr",
            "cube_one.boolAttr",
            "cube_one.stringAttr",
        ]

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, filter_locked=False, filter_connected=True)
        result_keys_list = list(result_dict.keys())

        self.assertEqual(expected_attr, result_keys_list)

        # Lock and Connect User-defined
        cmds.setAttr(f"{cube_one}.doubleAttr", lock=True)
        cmds.setAttr(f"{cube_one}.intAttr", lock=True)
        cmds.connectAttr(f"{cube_two}.v", f"{cube_one}.boolAttr")
        cmds.connectAttr(f"{cube_two}.tz", f"{cube_one}.enumAttr")

        expected_attr = [
            "cube_one.tx",
            # "cube_one.ty",
            "cube_one.tz",
            # "cube_one.rx",
            "cube_one.ry",
            "cube_one.rz",
            # "cube_one.sx",
            "cube_one.sy",
            "cube_one.sz",
            "cube_one.v",
            "cube_one.doubleAttr",
            "cube_one.intAttr",
            # "cube_one.enumAttr",
            # "cube_one.boolAttr",
            "cube_one.stringAttr",
        ]

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, filter_locked=False, filter_connected=True)
        result_keys_list = list(result_dict.keys())

        self.assertEqual(expected_attr, result_keys_list)

    def test_get_attrs_as_dict_full_attr_path(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, full_attr_path=True)

        expected_dict = {
            "cube_one.boolAttr": True,
            "cube_one.doubleAttr": 2.5,
            "cube_one.enumAttr": 2,
            "cube_one.intAttr": 3,
            "cube_one.rx": 0.0,
            "cube_one.ry": 0.0,
            "cube_one.rz": 0.0,
            "cube_one.stringAttr": "mocked_content",
            "cube_one.sx": 1.0,
            "cube_one.sy": 1.0,
            "cube_one.sz": 1.0,
            "cube_one.tx": 0.0,
            "cube_one.ty": 0.0,
            "cube_one.tz": 0.0,
            "cube_one.v": True,
        }
        self.assertEqual(expected_dict, result_dict)
        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, full_attr_path=False)

        expected_dict = {
            "boolAttr": True,
            "doubleAttr": 2.5,
            "enumAttr": 2,
            "intAttr": 3,
            "rx": 0.0,
            "ry": 0.0,
            "rz": 0.0,
            "stringAttr": "mocked_content",
            "sx": 1.0,
            "sy": 1.0,
            "sz": 1.0,
            "tx": 0.0,
            "ty": 0.0,
            "tz": 0.0,
            "v": True,
        }
        self.assertEqual(expected_dict, result_dict)

    def test_get_attrs_as_dict_no_trs(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        expected_attr = [
            # "cube_one.tx",
            # "cube_one.ty",
            # "cube_one.tz",
            # "cube_one.rx",
            # "cube_one.ry",
            # "cube_one.rz",
            # "cube_one.sx",
            # "cube_one.sy",
            # "cube_one.sz",
            # "cube_one.v",
            "cube_one.doubleAttr",
            "cube_one.intAttr",
            "cube_one.enumAttr",
            "cube_one.boolAttr",
            "cube_one.stringAttr",
        ]

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, get_default=False)
        result_keys_list = list(result_dict.keys())

        self.assertEqual(expected_attr, result_keys_list)

        expected_dict = {
            "cube_one.boolAttr": True,
            "cube_one.doubleAttr": 2.5,
            "cube_one.enumAttr": 2,
            "cube_one.intAttr": 3,
            "cube_one.stringAttr": "mocked_content",
            # "cube_one.rx": 0.0,
            # "cube_one.ry": 0.0,
            # "cube_one.rz": 0.0,
            # "cube_one.sx": 1.0,
            # "cube_one.sy": 1.0,
            # "cube_one.sz": 1.0,
            # "cube_one.tx": 0.0,
            # "cube_one.ty": 0.0,
            # "cube_one.tz": 0.0,
            # "cube_one.v": True,
        }
        self.assertEqual(expected_dict, result_dict)

    def test_get_attrs_as_dict_no_user_defined(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        expected_attr = [
            "cube_one.tx",
            "cube_one.ty",
            "cube_one.tz",
            "cube_one.rx",
            "cube_one.ry",
            "cube_one.rz",
            "cube_one.sx",
            "cube_one.sy",
            "cube_one.sz",
            "cube_one.v",
            # "cube_one.doubleAttr",
            # "cube_one.intAttr",
            # "cube_one.enumAttr",
            # "cube_one.boolAttr",
            # "cube_one.stringAttr",
        ]

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, get_user_defined=False)
        result_keys_list = list(result_dict.keys())

        self.assertEqual(expected_attr, result_keys_list)

        expected_dict = {
            # "cube_one.boolAttr": True,
            # "cube_one.doubleAttr": 2.5,
            # "cube_one.enumAttr": 2,
            # "cube_one.intAttr": 3,
            # "cube_one.stringAttr": "mocked_content",
            "cube_one.rx": 0.0,
            "cube_one.ry": 0.0,
            "cube_one.rz": 0.0,
            "cube_one.sx": 1.0,
            "cube_one.sy": 1.0,
            "cube_one.sz": 1.0,
            "cube_one.tx": 0.0,
            "cube_one.ty": 0.0,
            "cube_one.tz": 0.0,
            "cube_one.v": True,
        }
        self.assertEqual(expected_dict, result_dict)

    def test_get_attrs_as_dict_ignore_non_keyable(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        core_attr.add_attr(cube_one, attr_type="double", attributes="doubleAttr")
        core_attr.add_attr(cube_one, attr_type="long", attributes="intAttr")
        core_attr.add_attr(cube_one, attr_type="enum", attributes="enumAttr", enum="Option1:Option2:Option3")
        core_attr.add_attr(cube_one, attr_type="bool", attributes="boolAttr")
        core_attr.add_attr(cube_one, attr_type="string", attributes="stringAttr")

        cmds.setAttr(f"{cube_one}.doubleAttr", 2.5)
        cmds.setAttr(f"{cube_one}.intAttr", 3)
        cmds.setAttr(f"{cube_one}.intAttr", keyable=False)
        cmds.setAttr(f"{cube_one}.enumAttr", 2)
        cmds.setAttr(f"{cube_one}.boolAttr", True)
        cmds.setAttr(f"{cube_one}.stringAttr", "mocked_content", type="string")

        expected_attr = [
            "cube_one.tx",
            "cube_one.ty",
            "cube_one.tz",
            "cube_one.rx",
            "cube_one.ry",
            "cube_one.rz",
            "cube_one.sx",
            "cube_one.sy",
            "cube_one.sz",
            "cube_one.v",
            "cube_one.doubleAttr",
            # "cube_one.intAttr",
            "cube_one.enumAttr",
            "cube_one.boolAttr",
            "cube_one.stringAttr",
        ]

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, filter_non_keyable=True)
        result_keys_list = list(result_dict.keys())

        self.assertEqual(expected_attr, result_keys_list)

        expected_dict = {
            "cube_one.boolAttr": True,
            "cube_one.doubleAttr": 2.5,
            "cube_one.enumAttr": 2,
            # "cube_one.intAttr": 3,
            "cube_one.rx": 0.0,
            "cube_one.ry": 0.0,
            "cube_one.rz": 0.0,
            "cube_one.stringAttr": "mocked_content",
            "cube_one.sx": 1.0,
            "cube_one.sy": 1.0,
            "cube_one.sz": 1.0,
            "cube_one.tx": 0.0,
            "cube_one.ty": 0.0,
            "cube_one.tz": 0.0,
            "cube_one.v": True,
        }
        self.assertEqual(expected_dict, result_dict)

        # Change Values
        cmds.setAttr(f"{cube_one}.intAttr", keyable=True)

        result_dict = core_attr.get_attrs_as_dict(obj=cube_one, filter_non_keyable=True)
        expected_dict = {
            "cube_one.boolAttr": True,
            "cube_one.doubleAttr": 2.5,
            "cube_one.enumAttr": 2,
            "cube_one.intAttr": 3,
            "cube_one.rx": 0.0,
            "cube_one.ry": 0.0,
            "cube_one.rz": 0.0,
            "cube_one.stringAttr": "mocked_content",
            "cube_one.sx": 1.0,
            "cube_one.sy": 1.0,
            "cube_one.sz": 1.0,
            "cube_one.tx": 0.0,
            "cube_one.ty": 0.0,
            "cube_one.tz": 0.0,
            "cube_one.v": True,
        }
        self.assertEqual(expected_dict, result_dict)

    def test_disconnect_attr(self):
        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        cmds.connectAttr("cube_two.rx", "cube_one.rx")
        cmds.connectAttr("cube_two.ry", "cube_one.ry")
        cmds.connectAttr("cube_two.rz", "cube_one.rz")
        cmds.setAttr("cube_one.rx", lock=True, edit=True)
        cmds.setAttr("cube_one.ry", lock=True, edit=True)
        cmds.setAttr("cube_one.rz", lock=True, edit=True)
        core_attr.disconnect_attr(obj_list="cube_one", attr_list=["rx", "ry", "rz"], keep_unlocked=True)

        expected = None
        result = cmds.listConnections("cube_one.rx", plugs=True, connections=True, source=True, destination=False)
        self.assertEqual(expected, result)
        result = cmds.listConnections("cube_one.ry", plugs=True, connections=True, source=True, destination=False)
        self.assertEqual(expected, result)
        result = cmds.listConnections("cube_one.rz", plugs=True, connections=True, source=True, destination=False)
        self.assertEqual(expected, result)
