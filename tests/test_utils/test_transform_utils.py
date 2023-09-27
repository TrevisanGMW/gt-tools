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

# Import Utility and Maya Test Tools
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
        self.vector_a = transform_utils.Vector3(1, 2, 3)
        self.vector_b = transform_utils.Vector3(4, 5, 6)

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    # --------------------------------------------- Vector3 Start -------------------------------------------
    def test_vector3_class_as_string(self):
        vector3_object = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        expected = "(x=1.2, y=3.4, z=5.6)"
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

    def test_Vector3_init(self):
        vec = transform_utils.Vector3()
        result = vec.get_as_tuple()
        expected = (0.0, 0.0, 0.0)
        self.assertEqual(expected, result)

        vec = transform_utils.Vector3(x=1.0, y=2.0, z=3.0)
        result = vec.get_as_tuple()
        expected = (1.0, 2.0, 3.0)
        self.assertEqual(expected, result)

        vec = transform_utils.Vector3(xyz=[4.0, 5.0, 6.0])
        expected = (4.0, 5.0, 6.0)
        result = vec.get_as_tuple()
        self.assertEqual(expected, result)

    def test_Vector3_invalid_input(self):
        with self.assertRaises(ValueError):
            transform_utils.Vector3(x="not a number")

    def test_Vector3_eq(self):
        vec1 = transform_utils.Vector3(1.0, 2.0, 3.0)
        vec2 = transform_utils.Vector3(1.0, 2.0, 3.0)
        vec3 = transform_utils.Vector3(4.0, 5.0, 6.0)
        expected = True
        result = vec1 == vec2
        self.assertEqual(expected, result)

        expected = False
        result = vec1 == vec3
        self.assertEqual(expected, result)

    def test_Vector3_add(self):
        vec1 = transform_utils.Vector3(1.0, 2.0, 3.0)
        vec2 = transform_utils.Vector3(4.0, 5.0, 6.0)
        expected = (5.0, 7.0, 9.0)
        added_vec = vec1 + vec2
        result = added_vec.get_as_tuple()
        self.assertEqual(expected, result)

    def test_Vector3_sub(self):
        vec1 = transform_utils.Vector3(1.0, 2.0, 3.0)
        vec2 = transform_utils.Vector3(4.0, 5.0, 6.0)
        expected = (3.0, 3.0, 3.0)
        result = (vec2 - vec1).get_as_tuple()
        self.assertEqual(expected, result)

    def test_Vector3_mul(self):
        vec = transform_utils.Vector3(1.0, 2.0, 3.0)
        scalar = 2.0
        expected = (2.0, 4.0, 6.0)
        result = (vec * scalar).get_as_tuple()
        self.assertEqual(expected, result)

    def test_Vector3_magnitude(self):
        vec = transform_utils.Vector3(3.0, 4.0, 0.0)
        expected = 5.0
        result = vec.magnitude()
        self.assertEqual(expected, result)

    def test_Vector3_dot(self):
        vec1 = transform_utils.Vector3(1.0, 2.0, 3.0)
        vec2 = transform_utils.Vector3(4.0, 5.0, 6.0)
        expected = 32.0
        result = vec1.dot(vec2)
        self.assertEqual(expected, result)

    def test_Vector3_cross(self):
        vec1 = transform_utils.Vector3(1.0, 0.0, 0.0)
        vec2 = transform_utils.Vector3(0.0, 1.0, 0.0)
        expected = (0.0, 0.0, 1.0)
        result = vec1.cross(vec2).get_as_tuple()
        self.assertEqual(expected, result)

    def test_Vector3_set_from_list(self):
        vec = transform_utils.Vector3()
        vec.set_from_tuple((4.0, 5.0, 6.0))
        expected = (4.0, 5.0, 6.0)
        result = vec.get_as_tuple()
        self.assertEqual(expected, result)

        with self.assertRaises(ValueError):
            vec.set_from_tuple((1.0, 2.0, 3.0, 4.0))

    def test_Vector3_less_than(self):
        v1 = transform_utils.Vector3(1, 2, 3)
        v2 = transform_utils.Vector3(4, 5, 6)
        self.assertTrue(v1 < v2)
        self.assertFalse(v2 < v1)
        self.assertFalse(v1 < v1)

    def test_Vector3_less_than_or_equal(self):
        v1 = transform_utils.Vector3(1, 2, 3)
        v2 = transform_utils.Vector3(4, 5, 6)
        self.assertTrue(v1 <= v2)
        self.assertFalse(v2 <= v1)
        self.assertTrue(v1 <= v1)

    def test_Vector3_greater_than(self):
        v1 = transform_utils.Vector3(1, 2, 3)
        v2 = transform_utils.Vector3(4, 5, 6)
        self.assertFalse(v1 > v2)
        self.assertTrue(v2 > v1)
        self.assertFalse(v1 > v1)

    def test_Vector3_greater_than_or_equal(self):
        v1 = transform_utils.Vector3(1, 2, 3)
        v2 = transform_utils.Vector3(4, 5, 6)
        self.assertFalse(v1 >= v2)
        self.assertTrue(v2 >= v1)
        self.assertTrue(v1 >= v1)

    def test_Vector3_x_setter(self):
        vector = transform_utils.Vector3(0, 0, 0)
        vector.set_x(x=10)
        expected = 10
        self.assertEqual(expected, vector.x)

    def test_Vector3_y_setter(self):
        vector = transform_utils.Vector3(0, 0, 0)
        vector.set_y(y=10)
        expected = 10
        self.assertEqual(expected, vector.y)

    def test_Vector3_z_setter(self):
        vector = transform_utils.Vector3(0, 0, 0)
        vector.set_z(z=10)
        expected = 10
        self.assertEqual(expected, vector.z)

    # --------------------------------------------------- Vector3 End -------------------------------------------------

    # ------------------------------------------------- Transform Start -----------------------------------------------
    def test_transform_class_as_string(self):
        vector3_object = transform_utils.Vector3(x=1.2, y=3.4, z=5.6)
        transform_object = transform_utils.Transform(position=vector3_object,
                                     rotation=vector3_object,
                                     scale=vector3_object)
        result = str(transform_object)
        expected = "position=(x=1.2, y=3.4, z=5.6), " \
                   "rotation=(x=1.2, y=3.4, z=5.6), " \
                   "scale=(x=1.2, y=3.4, z=5.6)"
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

    def test_transform_eq(self):
        transform_a = transform_utils.Transform(self.vector_a, self.vector_a, self.vector_a)
        transform_b = transform_utils.Transform(self.vector_b, self.vector_b, self.vector_b)

        expected = True
        result = transform_a == transform_a
        self.assertEqual(expected, result)

        expected = False
        result = transform_a == transform_b
        self.assertEqual(expected, result)

    def test_transform_set_translation_from_tuple(self):
        transform = transform_utils.Transform()
        transform.set_translation_from_tuple((10, 20, 30))
        expected = transform_utils.Vector3(10, 20, 30)
        self.assertEqual(expected, transform.position)

    def test_transform_set_rotation_from_tuple(self):
        transform = transform_utils.Transform()
        transform.set_rotation_from_tuple((45, 90, 0))
        expected = transform_utils.Vector3(45, 90, 0)
        self.assertEqual(expected, transform.rotation)

    def test_transform_set_scale_from_tuple(self):
        transform = transform_utils.Transform()
        transform.set_scale_from_tuple((2, 2, 2))
        expected = transform_utils.Vector3(2, 2, 2)
        self.assertEqual(expected, transform.scale)

    def test_transform_lt(self):
        transform_a = transform_utils.Transform(self.vector_a, self.vector_a, self.vector_a)
        transform_b = transform_utils.Transform(self.vector_b, self.vector_b, self.vector_b)
        self.assertTrue(transform_a < transform_b)
        self.assertFalse(transform_b < transform_a)
        self.assertFalse(transform_a < transform_a)

    def test_transform_le(self):
        transform_a = transform_utils.Transform(self.vector_a, self.vector_a, self.vector_a)
        transform_b = transform_utils.Transform(self.vector_b, self.vector_b, self.vector_b)
        self.assertTrue(transform_a <= transform_b)
        self.assertFalse(transform_b <= transform_a)
        self.assertTrue(transform_a <= transform_a)

    def test_transform_gt(self):
        transform_a = transform_utils.Transform(self.vector_a, self.vector_a, self.vector_a)
        transform_b = transform_utils.Transform(self.vector_b, self.vector_b, self.vector_b)
        self.assertFalse(transform_a > transform_b)
        self.assertTrue(transform_b > transform_a)
        self.assertFalse(transform_a > transform_a)

    def test_transform_ge(self):
        transform_a = transform_utils.Transform(self.vector_a, self.vector_a, self.vector_a)
        transform_b = transform_utils.Transform(self.vector_b, self.vector_b, self.vector_b)
        self.assertFalse(transform_a >= transform_b)
        self.assertTrue(transform_b >= transform_a)
        self.assertTrue(transform_a >= transform_a)

    def test_transform_set_position_xyz(self):
        transform = transform_utils.Transform()
        new_position = transform_utils.Vector3(1, 2, 3)
        transform.set_position(xyz=new_position)
        self.assertEqual(new_position, transform.position)

    def test_transform_set_rotation_xyz(self):
        transform = transform_utils.Transform()
        new_rotation = transform_utils.Vector3(45, 0, 90)
        transform.set_rotation(xyz=new_rotation)
        self.assertEqual(new_rotation, transform.rotation)

    def test_transform_set_scale_xyz(self):
        transform = transform_utils.Transform()
        new_scale = transform_utils.Vector3(2, 2, 2)
        transform.set_scale(xyz=new_scale)
        self.assertEqual(new_scale, transform.scale)

    def test_transform_set_position_arg(self):
        transform = transform_utils.Transform()
        new_position = transform_utils.Vector3(1, 2, 3)
        transform.set_position(1, 2, 3)
        self.assertEqual(new_position, transform.position)

    def test_transform_set_rotation_arg(self):
        transform = transform_utils.Transform()
        new_rotation = transform_utils.Vector3(45, 0, 90)
        transform.set_rotation(45, 0, 90)
        self.assertEqual(new_rotation, transform.rotation)

    def test_transform_set_scale_arg(self):
        transform = transform_utils.Transform()
        new_scale = transform_utils.Vector3(2, 2, 2)
        transform.set_scale(2, 2, 2)
        self.assertEqual(new_scale, transform.scale)

    def test_transform_set_position_fewer_channels(self):
        transform = transform_utils.Transform()
        new_position = transform_utils.Vector3(1, 2, 3)
        transform.set_position(xyz=new_position.get_as_tuple())
        transform.set_position(x=10)
        new_position.set_x(x=10)
        self.assertEqual(new_position, transform.position)
        transform.set_position(y=15)
        new_position.set_y(y=15)
        self.assertEqual(new_position, transform.position)
        transform.set_position(z=20)
        new_position.set_z(z=20)
        self.assertEqual(new_position, transform.position)
        transform.set_position(x=0, z=20)
        new_position.set_x(x=0)
        new_position.set_z(z=20)
        self.assertEqual(new_position, transform.position)
        transform.set_position(x=5, y=10)
        new_position.set_x(x=5)
        new_position.set_y(y=10)
        self.assertEqual(new_position.get_as_tuple(), transform.position.get_as_tuple())

    def test_transform_set_rotation_fewer_channels(self):
        transform = transform_utils.Transform()
        new_rotation = transform_utils.Vector3(1, 2, 3)
        transform.set_rotation(xyz=new_rotation.get_as_tuple())
        transform.set_rotation(x=10)
        new_rotation.set_x(x=10)
        self.assertEqual(new_rotation, transform.rotation)
        transform.set_rotation(y=15)
        new_rotation.set_y(y=15)
        self.assertEqual(new_rotation, transform.rotation)
        transform.set_rotation(z=20)
        new_rotation.set_z(z=20)
        self.assertEqual(new_rotation, transform.rotation)
        transform.set_rotation(x=0, z=20)
        new_rotation.set_x(x=0)
        new_rotation.set_z(z=20)
        self.assertEqual(new_rotation, transform.rotation)
        transform.set_rotation(x=5, y=10)
        new_rotation.set_x(x=5)
        new_rotation.set_y(y=10)
        self.assertEqual(new_rotation.get_as_tuple(), transform.rotation.get_as_tuple())

    def test_transform_set_scale_fewer_channels(self):
        transform = transform_utils.Transform()
        new_scale = transform_utils.Vector3(1, 2, 3)
        transform.set_scale(xyz=new_scale.get_as_tuple())
        transform.set_scale(x=10)
        new_scale.set_x(x=10)
        self.assertEqual(new_scale, transform.scale)
        transform.set_scale(y=15)
        new_scale.set_y(y=15)
        self.assertEqual(new_scale, transform.scale)
        transform.set_scale(z=20)
        new_scale.set_z(z=20)
        self.assertEqual(new_scale, transform.scale)
        transform.set_scale(x=0, z=20)
        new_scale.set_x(x=0)
        new_scale.set_z(z=20)
        self.assertEqual(new_scale, transform.scale)
        transform.set_scale(x=5, y=10)
        new_scale.set_x(x=5)
        new_scale.set_y(y=10)
        self.assertEqual(new_scale.get_as_tuple(), transform.scale.get_as_tuple())

    def test_transform_set_trs_invalid_input(self):
        transform = transform_utils.Transform()

        invalid_input = "not_a_vector"
        with self.assertLogs(level='WARNING'):
            transform.set_position(invalid_input)
            transform.set_rotation(invalid_input)
            transform.set_scale(invalid_input)

        self.assertEqual(transform_utils.Vector3(0, 0, 0), transform.position)
        self.assertEqual(transform_utils.Vector3(0, 0, 0), transform.rotation)
        self.assertEqual(transform_utils.Vector3(1, 1, 1), transform.scale)

    def test_transform_set_position_tuple(self):
        transform = transform_utils.Transform()
        new_position = (1, 2, 3)
        new_position_vector3 = transform_utils.Vector3(*new_position)
        transform.set_position(xyz=new_position)
        self.assertEqual(new_position_vector3, transform.position)

    def test_transform_set_rotation_tuple(self):
        transform = transform_utils.Transform()
        new_rotation = (45, 0, 90)
        new_rotation_vector3 = transform_utils.Vector3(*new_rotation)
        transform.set_rotation(xyz=new_rotation)
        self.assertEqual(new_rotation_vector3, transform.rotation)

    def test_transform_set_scale_tuple(self):
        transform = transform_utils.Transform()
        new_scale = (2, 2, 2)
        new_scale_vector3 = transform_utils.Vector3(*new_scale)
        transform.set_scale(xyz=new_scale)
        self.assertEqual(new_scale_vector3, transform.scale)

    def test_set_transform_from_object(self):
        cube = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.setAttr(f'{cube}.ty', 5)
        maya_test_tools.cmds.setAttr(f'{cube}.ry', 35)
        maya_test_tools.cmds.setAttr(f'{cube}.sy', 2)
        transform = transform_utils.Transform()
        transform.set_transform_from_object(obj_name=cube)
        expected_position = transform_utils.Vector3(0, 5, 0)
        self.assertEqual(expected_position, transform.position)
        expected_rotate = transform_utils.Vector3(0, 35, 0)
        self.assertEqual(expected_rotate, transform.rotation)
        expected_scale = transform_utils.Vector3(1, 2, 1)
        self.assertEqual(expected_scale, transform.scale)

    def test_get_position(self):
        transform = transform_utils.Transform()
        new_pos = (2, 2, 2)
        new_pos_vector3 = transform_utils.Vector3(*new_pos)
        transform.set_position(xyz=new_pos_vector3)
        self.assertEqual(new_pos_vector3, transform.get_position())
        self.assertEqual(new_pos_vector3.get_as_tuple(), transform.get_position(as_tuple=True))

    def test_get_rotation(self):
        transform = transform_utils.Transform()
        new_rot = (2, 2, 2)
        new_rot_vector3 = transform_utils.Vector3(*new_rot)
        transform.set_rotation(xyz=new_rot_vector3)
        self.assertEqual(new_rot_vector3, transform.get_rotation())
        self.assertEqual(new_rot_vector3.get_as_tuple(), transform.get_rotation(as_tuple=True))

    def test_get_scale(self):
        transform = transform_utils.Transform()
        new_sca = (2, 2, 2)
        new_sca_vector3 = transform_utils.Vector3(*new_sca)
        transform.set_scale(xyz=new_sca_vector3)
        self.assertEqual(new_sca_vector3, transform.get_scale())
        self.assertEqual(new_sca_vector3.get_as_tuple(), transform.get_scale(as_tuple=True))

    def test_get_transform_as_dict(self):
        transform = transform_utils.Transform()
        new_pos = (1, 1, 1)
        new_pos_vector3 = transform_utils.Vector3(*new_pos)
        transform.set_position(xyz=new_pos_vector3)
        new_rot = (2, 2, 2)
        new_rot_vector3 = transform_utils.Vector3(*new_rot)
        transform.set_rotation(xyz=new_rot_vector3)
        new_sca = (3, 3, 3)
        new_sca_vector3 = transform_utils.Vector3(*new_sca)
        transform.set_scale(xyz=new_sca_vector3)
        result = transform.get_transform_as_dict()
        expected = {"position": new_pos,
                    "rotation": new_rot,
                    "scale": new_sca,
                    }
        self.assertEqual(expected, result)

    def test_set_transform_from_dict(self):
        transform = transform_utils.Transform()
        new_pos = (1, 1, 1)
        new_rot = (2, 2, 2)
        new_sca = (3, 3, 3)
        expected = {"position": new_pos,
                    "rotation": new_rot,
                    "scale": new_sca,
                    }
        transform.set_transform_from_dict(transform_dict=expected)
        result = transform.get_transform_as_dict()
        self.assertEqual(expected, result)

    # -------------------------------------------------- Transform End ------------------------------------------------

    def test_move_to_origin(self):
        cube = maya_test_tools.create_poly_cube()
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
        cube = maya_test_tools.create_poly_cube()
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
