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

    def test_is_conflicting_name_true(self):
        a_curve = Curves.circle
        a_curve.set_name("circle")
        self.model.base_curves = [a_curve]
        self.model.user_curves = []
        self.model.controls = []
        result = self.model.is_conflicting_name("circle")
        expected = True
        self.assertEqual(expected, result)

    def test_is_conflicting_name_false(self):
        self.model.base_curves = []
        self.model.user_curves = []
        self.model.controls = []
        result = self.model.is_conflicting_name("mocked_non_existing_name")
        expected = False
        self.assertEqual(expected, result)

    def test_validate_curve_true(self):
        self.model.base_curves = []
        self.model.user_curves = []
        self.model.controls = []
        result = self.model.validate_curve(Curves.circle)
        expected = True
        self.assertEqual(expected, result)

    def test_validate_curve_false(self):
        self.model.base_curves = [Curves.circle]
        result = self.model.validate_curve(Curves.circle)
        expected = False
        self.assertEqual(expected, result)

    def test_get_base_curves(self):
        self.model.base_curves = [Curves.circle]
        result = self.model.get_base_curves()
        expected = [Curves.circle]
        self.assertEqual(expected, result)

    def test_add_base_curve(self):
        self.model.base_curves = []
        self.model.user_curves = []
        self.model.controls = []
        self.model.add_base_curve(Curves.circle)
        result = self.model.get_base_curves()
        expected = [Curves.circle]
        self.assertEqual(expected, result)

    def test_get_user_curves(self):
        self.model.user_curves = [Curves.circle]
        result = self.model.get_user_curves()
        expected = [Curves.circle]
        self.assertEqual(expected, result)

    def test_add_user_curve(self):
        self.model.base_curves = []
        self.model.user_curves = []
        self.model.controls = []
        self.model.add_user_curve(Curves.circle)
        result = self.model.get_user_curves()
        expected = [Curves.circle]
        self.assertEqual(expected, result)

    def test_get_control_curves(self):
        self.model.controls = [Curves.circle]
        result = self.model.get_controls()
        expected = [Curves.circle]
        self.assertEqual(expected, result)

    def test_add_control_curve(self):
        self.model.base_curves = []
        self.model.user_curves = []
        self.model.controls = []
        self.model.add_control(Curves.circle)
        result = self.model.get_controls()
        expected = [Curves.circle]
        self.assertEqual(expected, result)

    def test_get_all_curves(self):
        self.model.base_curves = [Curves.circle]
        self.model.user_curves = [Curves.circle]
        self.model.controls = [Curves.circle]
        result = self.model.get_all_curves()
        expected = [Curves.circle, Curves.circle, Curves.circle]
        self.assertEqual(expected, result)

    def test_get_base_curve_names(self):
        self.model.base_curves = []
        self.model.user_curves = []
        self.model.controls = []
        self.model.add_base_curve(Curves.circle_arrow)
        result = self.model.get_base_curve_names()
        expected = ['circle_arrow']
        self.assertEqual(expected, result)

    def test_get_user_curve_names(self):
        self.model.base_curves = []
        self.model.user_curves = []
        self.model.controls = []
        self.model.add_user_curve(Curves.circle_arrow)
        result = self.model.get_user_curve_names()
        expected = ['circle_arrow']
        self.assertEqual(expected, result)

    def test_get_control_names(self):
        self.model.base_curves = []
        self.model.user_curves = []
        self.model.controls = []
        self.model.add_control(Curves.circle_arrow)
        result = self.model.get_control_names()
        expected = ['circle_arrow']
        self.assertEqual(expected, result)

    def test_get_all_curve_names(self):
        self.model.base_curves = []
        self.model.user_curves = []
        self.model.controls = []
        self.model.add_user_curve(Curves.circle_arrow)
        self.model.add_user_curve(Curves.circle_arrow)
        self.model.add_control(Curves.circle_arrow)
        result = self.model.get_all_curve_names()
        expected = ['circle_arrow']  # Only one because unique names are enforced.
        self.assertEqual(expected, result)

    def test_get_curve_names_formatted(self):
        self.model.base_curves = []
        self.model.add_base_curve(Curves.circle_arrow)
        result = self.model.get_base_curve_names(formatted=True)
        expected = ['Circle Arrow']
        self.assertEqual(expected, result)

    def test_import_default_library(self):
        curve = Curve(name="two_lines")
        curve.shapes = "mocked_shapes"

        class TempCurves:  # Mocked curves class
            two_lines = curve

        # with patch('gt.utils.curve_utils.Curves', new=TempCurves):
        with patch('gt.tools.curve_library.curve_library_model.Curves', new=TempCurves):
            self.model.base_curves = []
            self.model.user_curves = []
            self.model.controls = []
            self.model.import_default_library()
            result = self.model.get_base_curves()
            expected = [curve]
            self.assertEqual(expected, result)

    def test_import_control_library(self):
        curve = Curve(name="two_lines")
        curve.shapes = "mocked_shapes"

        class TempCurves:  # Mocked curves class
            two_lines = curve

        # with patch('gt.utils.curve_utils.Curves', new=TempCurves):
        with patch('gt.tools.curve_library.curve_library_model.Controls', new=TempCurves):
            self.model.base_curves = []
            self.model.user_curves = []
            self.model.controls = []
            self.model.import_controls_library()
            result = self.model.get_controls()
            expected = [curve]
            self.assertEqual(expected, result)

    def test_build_curve_from_name(self):
        self.model.build_curve_from_name(curve_name="circle_arrow")
        self.assertTrue(maya_test_tools.cmds.objExists("circle_arrow"))

    def test_build_curve(self):
        self.model.build_curve(curve=Curves.circle_arrow)
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
