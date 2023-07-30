import os
import sys
import logging
import unittest

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
from gt.utils import curve_utils


def import_curve_test_file():
    """
    Import test curve file from inside the .../data folder/<name>.abc
    """
    maya_test_tools.import_data_file("curves_nurbs_bezier.ma")


class TestCurveUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_combine_curves_list_two(self):
        import_curve_test_file()
        combined_crv = curve_utils.combine_curves_list(["curve1", "curve2"])
        result = maya_test_tools.list_relatives(combined_crv, shapes=True)
        expected = ['curveShape1', 'curveShape2']
        self.assertEqual(expected, result)

    def test_combine_curves_list_multiple(self):
        import_curve_test_file()
        combined_crv = curve_utils.combine_curves_list(["curve1", "curve2", "bezier1", "bezier2"])
        result = maya_test_tools.list_relatives(combined_crv, shapes=True)
        expected = ['curveShape1', 'curveShape2', 'bezierShape1', 'bezierShape2']
        self.assertEqual(expected, result)

    def test_combine_curves_list_bezier_to_nurbs(self):
        import_curve_test_file()
        combined_crv = curve_utils.combine_curves_list(["bezier1", "bezier2"], convert_bezier_to_nurbs=True)
        shapes = maya_test_tools.list_relatives(combined_crv, shapes=True)
        result = maya_test_tools.list_obj_types(shapes)
        expected = {'bezierShape1': 'nurbsCurve', 'bezierShape2': 'nurbsCurve'}
        self.assertEqual(expected, result)

    def test_combine_curves_list_no_bezier_to_nurbs(self):
        import_curve_test_file()
        combined_crv = curve_utils.combine_curves_list(["bezier1", "bezier2"], convert_bezier_to_nurbs=False)
        shapes = maya_test_tools.list_relatives(combined_crv, shapes=True)
        result = maya_test_tools.list_obj_types(shapes)
        expected = {'bezierShape1': 'bezierCurve', 'bezierShape2': 'bezierCurve'}
        self.assertEqual(expected, result)

    def test_curve_shape_read_existing(self):
        import_curve_test_file()
        curve_shape = curve_utils.CurveShape(read_existing_shape='curveShape1')

        result = curve_shape.get_data_as_dict()
        expected = {'degree': 3,
                    'is_bezier': False,
                    'knot': None,
                    'name': 'curveShape1',
                    'periodic': 0,
                    'points': [[0.0, 0.0, 5.0],
                               [-5.0, 0.0, 5.0],
                               [-5.0, 0.0, 0.0],
                               [0.0, 0.0, 0.0]]}
        self.assertEqual(expected, result)

    def test_curve_shape_set_name(self):
        import_curve_test_file()
        curve_shape = curve_utils.CurveShape(read_existing_shape='bezierShape1')
        curve_shape.set_name(new_name="new_name")
        result = curve_shape.get_data_as_dict().get("name")
        expected = "new_name"
        self.assertEqual(expected, result)

    def test_curve_shape_init(self):
        import_curve_test_file()
        curve_shape = curve_utils.CurveShape(name="my_curve",
                                             points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
                                             degree=1,
                                             is_bezier=False)
        result = curve_shape.get_data_as_dict()
        expected = {'degree': 1,
                    'is_bezier': False,
                    'knot': None,
                    'name': 'my_curve',
                    'periodic': None,
                    'points': [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]}
        self.assertEqual(expected, result)

    def test_curve_shape_to_string(self):
        import_curve_test_file()
        curve_shape = curve_utils.CurveShape(name="my_curve",
                                             points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
                                             degree=1,
                                             is_bezier=False)
        result = str(curve_shape)
        expected = 'CurveShape:\n\t"name": my_curve\n\t"points": [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]' \
                   '\n\t"degree": 1\n\t"knot": None\n\t"periodic": None\n\t"is_bezier": False'
        self.assertEqual(expected, result)

    def test_curve_shape_valid(self):
        import_curve_test_file()
        curve_shape = curve_utils.CurveShape(name="my_curve",
                                             points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
                                             degree=1,
                                             is_bezier=False)
        result = curve_shape.is_curve_shape_valid()
        self.assertTrue(result)

    def test_curve_shape_invalid(self):
        import_curve_test_file()
        curve_shape = curve_utils.CurveShape(name="my_curve",
                                             points=None,
                                             degree=1,
                                             is_bezier=False)
        logging.disable(logging.WARNING)
        result = curve_shape.is_curve_shape_valid()
        logging.disable(logging.NOTSET)
        self.assertFalse(result)

    def test_curve_shape_create(self):
        import_curve_test_file()
        curve_shape = curve_utils.CurveShape(name="my_curve",
                                             points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
                                             degree=1,
                                             is_bezier=False)
        result = curve_shape.create()
        expected = "my_curve_transform"
        self.assertEqual(expected, result)

    def test_curve_shape_create_recursive(self):
        import_curve_test_file()
        curve_shape = curve_utils.CurveShape(name="my_curve",
                                             points=[[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]],
                                             degree=1,
                                             is_bezier=False)
        created_crv = curve_shape.create()
        shapes = maya_test_tools.list_relatives(created_crv, shapes=True)
        new_curve_shape = curve_utils.CurveShape(read_existing_shape=shapes[0])
        result = new_curve_shape.get_data_as_dict()
        expected = {'degree': 1,
                    'is_bezier': False,
                    'knot': None,
                    'name': 'my_curve',
                    'periodic': 0,
                    'points': [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]}
        self.assertEqual(expected, result)

    def test_curve_shape_set_data_from_dict(self):
        import_curve_test_file()
        curve_shape_data = {'degree': 1,
                            'is_bezier': False,
                            'knot': None,
                            'name': 'my_curve',
                            'periodic': 0,
                            'points': [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]}
        curve_shape = curve_utils.CurveShape(read_curve_shape_data=curve_shape_data)
        result = curve_shape.points
        expected = curve_shape_data.get("points")
        self.assertEqual(expected, result)

    def test_curve_shape_replace(self):
        import_curve_test_file()
        curve_shape_data = {'degree': 1,
                            'is_bezier': False,
                            'knot': None,
                            'name': 'my_curve',
                            'periodic': 0,
                            'points': [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]}
        curve_shape = curve_utils.CurveShape(read_curve_shape_data=curve_shape_data)
        curve_shape.replace_target_curve(target_curve='curve1')
        new_curve_shape = curve_utils.CurveShape(read_existing_shape='my_curve')
        result = new_curve_shape.get_data_as_dict()
        expected = {'degree': 1,
                    'is_bezier': False,
                    'knot': None,
                    'name': 'my_curve',
                    'periodic': 0,
                    'points': [[0.0, 0.0, 0.0], [0.0, 0.0, -1.0]]}
        self.assertEqual(expected, result)
