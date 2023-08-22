from unittest.mock import patch
from io import StringIO
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
from gt.utils import transform_utils


class TestTransformUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_vector3_class_as_string(self):
        vector3_object = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        expected = "Vector3(x=1.2, y=3.4, z=5.6)"
        result = str(vector3_object)
        self.assertEqual(expected, result)

    def test_vector3_class_as_list(self):
        vector3_object = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        result = [vector3_object.x, vector3_object.y, vector3_object.z]
        expected = [1.2, 3.4, 5.6]
        self.assertEqual(expected, result)

    def test_vector3_class_equality_true(self):
        vector3_object_a = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        vector3_object_b = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        result = vector3_object_a == vector3_object_b
        expected = True
        self.assertEqual(expected, result)

    def test_vector3_class_equality_false(self):
        vector3_object_a = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        vector3_object_b = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        result = vector3_object_a == vector3_object_b
        expected = True
        self.assertEqual(expected, result)

    def test_transform_class_as_string(self):
        vector3_object = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        transform_object = transform_utils.Transform(position=vector3_object,
                                                     rotation=vector3_object,
                                                     scale=vector3_object)
        result = str(transform_object)
        expected = "Transform(position=Vector3(x=1.2, y=3.4, z=5.6), " \
                   "rotation=Vector3(x=1.2, y=3.4, z=5.6), " \
                   "scale=Vector3(x=1.2, y=3.4, z=5.6))"
        self.assertEqual(expected, result)

    def test_transform_class_position_as_list(self):
        vector3_object = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        transform_object = transform_utils.Transform(position=vector3_object,
                                                     rotation=vector3_object,
                                                     scale=vector3_object)
        result = [transform_object.position.x, transform_object.position.y, transform_object.position.z]
        expected = [1.2, 3.4, 5.6]
        self.assertEqual(expected, result)

    def test_transform_class_rotation_as_list(self):
        vector3_object = transform_utils.Vector3(x=30, y=-45, z=90)
        transform_object = transform_utils.Transform(position=vector3_object,
                                                     rotation=vector3_object,
                                                     scale=vector3_object)
        result = [transform_object.rotation.x, transform_object.rotation.y, transform_object.rotation.z]
        expected = [30, -45, 90]
        self.assertEqual(expected, result)

    def test_transform_class_scale_as_list(self):
        vector3_object = transform_utils.Vector3(x=1, y=2, z=3)
        transform_object = transform_utils.Transform(position=vector3_object,
                                                     rotation=vector3_object,
                                                     scale=vector3_object)
        result = [transform_object.scale.x, transform_object.scale.y, transform_object.scale.z]
        expected = [1, 2, 3]
        self.assertEqual(expected, result)

    def test_transform_class_equality_one(self):
        vector3_object = transform_utils.Vector3(x=1, y=2, z=3)
        transform_object_one = transform_utils.Transform(position=vector3_object,
                                                         rotation=vector3_object,
                                                         scale=vector3_object)
        transform_object_two = transform_utils.Transform(position=vector3_object,
                                                         rotation=vector3_object,
                                                         scale=vector3_object)
        result = transform_object_one == transform_object_two
        expected = True
        self.assertEqual(expected, result)

    def test_transform_class_equality_two(self):
        vector3_object_one = transform_utils.Vector3(x=1, y=2, z=3)
        vector3_object_two = transform_utils.Vector3(x=4, y=5, z=6)
        transform_object_one = transform_utils.Transform(position=vector3_object_one,
                                                         rotation=vector3_object_one,
                                                         scale=vector3_object_one)
        transform_object_two = transform_utils.Transform(position=vector3_object_two,
                                                         rotation=vector3_object_two,
                                                         scale=vector3_object_two)
        result = transform_object_one == transform_object_two
        expected = False
        self.assertEqual(expected, result)

    def test_move_to_origin(self):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ty", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tz", value=5)
        transform_utils.move_to_origin(cube)
        expected = 0
        result_x = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_y = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_z = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        self.assertEqual(expected, result_x)
        self.assertEqual(expected, result_y)
        self.assertEqual(expected, result_z)

    @patch('sys.stdout', new_callable=StringIO)
    def test_move_selection_to_origin(self, mocked_stdout):
        cube = maya_test_tools.create_poly_cube()[0]
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tx", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="ty", value=5)
        maya_test_tools.set_attribute(obj_name=cube, attr_name="tz", value=5)
        maya_test_tools.cmds.select(cube)
        transform_utils.move_selection_to_origin()
        expected = 0
        result_x = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
        result_y = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
        result_z = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
        self.assertEqual(expected, result_x)
        self.assertEqual(expected, result_y)
        self.assertEqual(expected, result_z)
        printed_value = mocked_stdout.getvalue()
        expected = '"pCube1" was moved to the origin\n'
        self.assertEqual(expected, printed_value)

    def test_rescale(self):
        cube = maya_test_tools.create_poly_cube()[0]
        result_y = maya_test_tools.cmds.xform(cube + ".vtx[0]", query=True, translation=True, worldSpace=True)
        expected = [-0.5, -0.5, 0.5]  # Unchanged
        self.assertEqual(expected, result_y)
        transform_utils.rescale(obj=cube, scale=5, freeze=True)
        expected = [-2.5, -2.5, 2.5]  # Changed
        result_y = maya_test_tools.cmds.xform(cube + ".vtx[0]", query=True, translation=True, worldSpace=True)
        self.assertEqual(expected, result_y)

    def test_rescale_no_freeze(self):
        cube = maya_test_tools.create_poly_cube()[0]
        expected = 5
        transform_utils.rescale(obj=cube, scale=expected, freeze=False)
        result_x = maya_test_tools.get_attribute(obj_name=cube, attr_name="sx")
        result_y = maya_test_tools.get_attribute(obj_name=cube, attr_name="sy")
        result_z = maya_test_tools.get_attribute(obj_name=cube, attr_name="sz")
        self.assertEqual(expected, result_x)
        self.assertEqual(expected, result_y)
        self.assertEqual(expected, result_z)

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
        transform_utils.freeze_channels(object_list=cube)
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
        transform_utils.freeze_channels(object_list=cube, freeze_translate=False)
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
        transform_utils.freeze_channels(object_list=cube, freeze_rotate=False)
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
        transform_utils.freeze_channels(object_list=cube, freeze_scale=False)
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
        transform_utils.freeze_channels(object_list=object_list)
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
