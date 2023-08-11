from unittest.mock import patch
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Script
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.tools.curve_library import curve_library_model
from gt.utils.curve_utils import Curves, Curve
from tests import maya_test_tools


class TestCurveLibraryModel(unittest.TestCase):
    def setUp(self):
        self.model = curve_library_model.CurveLibraryModel()
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_curves(self):
        self.model.curves = [Curves.circle]
        result = self.model.get_curves()
        expected = [Curves.circle]
        self.assertEqual(expected, result)

    def test_add_curve(self):
        self.model.curves = []
        self.model.add_curve(Curves.circle)
        result = self.model.get_curves()
        expected = [Curves.circle]
        self.assertEqual(expected, result)

    def test_get_curve_names(self):
        self.model.curves = []
        self.model.add_curve(Curves.circle_arrow)
        result = self.model.get_curve_names()
        expected = ['circle_arrow']
        self.assertEqual(expected, result)

    def test_get_curve_names_formatted(self):
        self.model.curves = []
        self.model.add_curve(Curves.circle_arrow)
        result = self.model.get_curve_names(formatted=True)
        expected = ['Circle Arrow']
        self.assertEqual(expected, result)

    def test_import_default_library(self):
        curve = Curve(name="two_lines")
        curve.shapes = "mocked_shapes"

        class TempCurves:  # Mocked curves class
            two_lines = curve

        # with patch('gt.utils.curve_utils.Curves', new=TempCurves):
        with patch('gt.tools.curve_library.curve_library_model.Curves', new=TempCurves):
            self.model.curves = []
            self.model.import_default_library()
            result = self.model.get_curves()
            expected = [curve]
            self.assertEqual(expected, result)

    def test_build_curve(self):
        self.model.build_curve(curve_name="circle_arrow")
        self.assertTrue(maya_test_tools.cmds.objExists("circle_arrow"))

    def test_get_curve_from_name(self):
        curve = Curve(name="two_lines")
        curve.shapes = "mocked_shapes"

        class TempCurves:  # Mocked curves class
            two_lines = curve

        # with patch('gt.utils.curve_utils.Curves', new=TempCurves):
        with patch('gt.tools.curve_library.curve_library_model.Curves', new=TempCurves):
            self.model.curves = []
            self.model.import_default_library()
            result = self.model.get_curve_from_name(curve_name="two_lines")
            expected = curve
            self.assertEqual(expected, result)

    def test_get_preview_image(self):
        result = self.model.get_preview_image("circle")
        self.assertTrue(os.path.exists(result))
