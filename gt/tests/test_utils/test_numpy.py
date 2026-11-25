import os
import sys
import unittest

# Import Tested Script
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
import gt.utils.numpy as utils_numpy


class TestNumpyUtils(unittest.TestCase):
    """Checks the NumPy point helpers."""

    def test_point_names(self):
        self.assertEqual(["point_00", "point_01"], utils_numpy.build_point_names(2))
        self.assertEqual("point_100", utils_numpy.build_point_names(101)[-1])

    @unittest.skipUnless(utils_numpy.is_numpy_available(), "NumPy is not installed")
    def test_normalize_point_samples(self):
        import numpy

        self.assertEqual((4, 2, 3), utils_numpy.normalize_point_samples(numpy.zeros((4, 6))).shape)
        self.assertEqual((4, 1, 3), utils_numpy.normalize_point_samples(numpy.zeros((4, 3))).shape)
        with self.assertRaises(ValueError):
            utils_numpy.normalize_point_samples(numpy.zeros((4, 5)))
