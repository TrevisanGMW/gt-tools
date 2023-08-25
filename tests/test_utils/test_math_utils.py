from unittest.mock import MagicMock, patch
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
