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
from gt.utils import math_utils


class TestMathUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_square_matrices(self):
        mat1 = [[1, 2], [3, 4]]
        mat2 = [[5, 6], [7, 8]]
        expected = [[19, 22], [43, 50]]
        result = math_utils.matrix_mult(mat1, mat2)
        self.assertEqual(expected, result)

    def test_rectangular_matrices(self):
        mat1 = [[1, 2, 3], [4, 5, 6]]
        mat2 = [[7, 8], [9, 10], [11, 12]]
        expected = [[58, 64], [139, 154]]
        result = math_utils.matrix_mult(mat1, mat2)
        self.assertEqual(expected, result)

    def test_identity_matrix(self):
        mat1 = [[1, 0], [0, 1]]
        mat2 = [[2, 3], [4, 5]]
        expected = [[2, 3], [4, 5]]
        result = math_utils.matrix_mult(mat1, mat2)
        self.assertEqual(expected, result)

    def test_empty_matrices(self):
        mat1 = []
        mat2 = []
        expected = []
        result = math_utils.matrix_mult(mat1, mat2)
        self.assertEqual(expected, result)

    def test_dot_product(self):
        vector_a = [1, 2, 3]
        vector_b = [4, 5, 6]
        expected = 1 * 4 + 2 * 5 + 3 * 6
        result = math_utils.dot_product(vector_a, vector_b)
        self.assertEqual(expected, result)

    def test_dot_product_vector3(self):
        from gt.utils.transform_utils import Vector3
        vector_a = Vector3(1, 2, 3)
        vector_b = Vector3(4, 5, 6)
        expected = 1 * 4 + 2 * 5 + 3 * 6
        result = math_utils.dot_product(vector_a, vector_b)
        self.assertEqual(expected, result)

    def test_cross_product(self):
        # Test case 1
        vector_a = [1, 2, 3]
        vector_b = [4, 5, 6]
        expected_result = [-3, 6, -3]
        result = math_utils.cross_product(vector_a, vector_b)
        self.assertEqual(result, expected_result)

        # Test case 2
        vector_a = [0, 0, 0]
        vector_b = [1, 2, 3]
        expected_result = [0, 0, 0]
        result = math_utils.cross_product(vector_a, vector_b)
        self.assertEqual(result, expected_result)

        # Test case 3
        vector_a = [2, 3, 4]
        vector_b = [5, 6, 7]
        expected_result = [-3, 6, -3]
        result = math_utils.cross_product(vector_a, vector_b)
        self.assertEqual(result, expected_result)

    def test_is_float_equal_equal_floats(self):
        x = 5.0
        y = 5.0
        tolerance = 0.00001
        expected = True
        result = math_utils.is_float_equal(x, y, tolerance)
        self.assertEqual(expected, result)

    def test_is_float_equal_unequal_floats_within_tolerance(self):
        x = 5.000001
        y = 5.0
        tolerance = 0.00001
        expected = True
        result = math_utils.is_float_equal(x, y, tolerance)
        self.assertEqual(expected, result)

    def test_is_float_equal_unequal_floats_outside_tolerance(self):
        x = 5.0001
        y = 5.0
        tolerance = 0.00001
        expected = False
        result = math_utils.is_float_equal(x, y, tolerance)
        self.assertEqual(expected, result)

    def test_is_float_equal_negative_floats_within_tolerance(self):
        x = -3.0
        y = -3.000001
        tolerance = 0.00001
        expected = True
        result = math_utils.is_float_equal(x, y, tolerance)
        self.assertEqual(expected, result)

    def test_is_float_equal_negative_floats_outside_tolerance(self):
        x = -3.0
        y = -3.0001
        tolerance = 0.00001
        expected = False
        result = math_utils.is_float_equal(x, y, tolerance)
        self.assertEqual(expected, result)

    def test_objects_cross_direction(self):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        cube_three = maya_test_tools.create_poly_cube()
        maya_test_tools.cmds.setAttr(f'{cube_two}.ty', 5)
        maya_test_tools.cmds.setAttr(f'{cube_three}.tx', 5)
        expected = (0, 0, 1)
        result = math_utils.objects_cross_direction(cube_one, cube_two, cube_three)
        self.assertEqual(expected, tuple(result))

    def test_dist_xyz_to_xyz(self):
        pos_a = (1.0, 2.0, 3.0)
        pos_b = (4.0, 5.0, 6.0)
        import math
        expected_result = math.sqrt(
            (pos_a[0] - pos_b[0]) ** 2 + (pos_a[1] - pos_b[1]) ** 2 + (pos_a[2] - pos_b[2]) ** 2)
        result = math_utils.dist_xyz_to_xyz(*pos_a, *pos_b)
        self.assertEqual(expected_result, result)

    def test_dist_center_to_center(self):
        obj_a = maya_test_tools.create_poly_cube(name="cube_a")
        obj_b = maya_test_tools.create_poly_cube(name="cube_b")

        expected_result = 0
        result = math_utils.dist_center_to_center(obj_a, obj_b)
        self.assertEqual(expected_result, result)

    def test_dist_center_to_center_close(self):
        obj_a = maya_test_tools.create_poly_cube(name="cube_a")
        obj_b = maya_test_tools.create_poly_cube(name="cube_b")
        maya_test_tools.cmds.setAttr(f'{obj_b}.ty', 5.35)

        expected_result = 5.35
        result = math_utils.dist_center_to_center(obj_a, obj_b)
        self.assertEqual(expected_result, result)

    def test_dist_center_to_center_far_precise(self):
        obj_a = maya_test_tools.create_poly_cube(name="cube_a")
        obj_b = maya_test_tools.create_poly_cube(name="cube_b")
        maya_test_tools.cmds.setAttr(f'{obj_b}.ty', 100.5)

        expected_result = 100.5
        result = math_utils.dist_center_to_center(obj_a, obj_b)
        self.assertEqual(expected_result, result)

    def test_get_bbox_center_single_object(self):
        obj_a = maya_test_tools.create_poly_cube(name="cube_a")

        expected_result = (0, 0, 0)
        result = math_utils.get_bbox_position(obj_list=obj_a)
        self.assertEqual(expected_result, result)

        maya_test_tools.cmds.setAttr(f'{obj_a}.ty', 100.5)

        expected_result = (0, 100.5, 0)
        result = math_utils.get_bbox_position(obj_list=obj_a)
        self.assertEqual(expected_result, result)

    def test_get_bbox_center_multiple_objects(self):
        obj_a = maya_test_tools.create_poly_cube(name="cube_a")
        obj_b = maya_test_tools.create_poly_cube(name="cube_b")
        maya_test_tools.cmds.setAttr(f'{obj_b}.ty', 5)

        expected_result = (0, 2.5, 0)
        result = math_utils.get_bbox_position(obj_list=[obj_a, obj_b])
        self.assertEqual(expected_result, result)

    def test_get_bbox_center_alignment_pos(self):
        obj_a = maya_test_tools.create_poly_cube(name="cube_a")
        obj_b = maya_test_tools.create_poly_cube(name="cube_b")
        maya_test_tools.cmds.setAttr(f'{obj_b}.ty', 5)

        expected_result = (0.5, 2.5, 0.0)
        result = math_utils.get_bbox_position(obj_list=[obj_a, obj_b], alignment="+", axis="x")
        self.assertEqual(expected_result, result)
        expected_result = (0, 5.5, 0.0)
        result = math_utils.get_bbox_position(obj_list=[obj_a, obj_b], alignment="+", axis="y")
        self.assertEqual(expected_result, result)
        expected_result = (0.0, 2.5, 0.5)
        result = math_utils.get_bbox_position(obj_list=[obj_a, obj_b], alignment="+", axis="z")
        self.assertEqual(expected_result, result)

    def test_get_bbox_center_alignment_neg(self):
        obj_a = maya_test_tools.create_poly_cube(name="cube_a")
        obj_b = maya_test_tools.create_poly_cube(name="cube_b")
        maya_test_tools.cmds.setAttr(f'{obj_b}.ty', 5)

        expected_result = (-0.5, 2.5, 0.0)
        result = math_utils.get_bbox_position(obj_list=[obj_a, obj_b], alignment="-", axis="x")
        self.assertEqual(expected_result, result)
        expected_result = (0.0, -0.5, 0.0)
        result = math_utils.get_bbox_position(obj_list=[obj_a, obj_b], alignment="-", axis="y")
        self.assertEqual(expected_result, result)
        expected_result = (0.0, 2.5, -0.5)
        result = math_utils.get_bbox_position(obj_list=[obj_a, obj_b], alignment="-", axis="z")
        self.assertEqual(expected_result, result)
