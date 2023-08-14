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
from gt.utils.control_utils import Control
from gt.utils import control_utils


class TestControlUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_control_class_invalid(self):
        ctrl = Control()
        self.assertFalse(ctrl.is_curve_valid())

    def test_control_class_build_function(self):
        ctrl = Control()
        ctrl.set_build_function(build_function=maya_test_tools.create_poly_cube)
        self.assertTrue(ctrl.is_curve_valid())
        self.assertEqual(maya_test_tools.create_poly_cube, ctrl.build_function)
        result = ctrl.build()
        expected = ['pCube1', 'polyCube1']
        self.assertEqual(expected, result)
        self.assertEqual(expected, ctrl.get_last_callable_output())

    def test_curves_existence(self):
        controls_attributes = vars(control_utils.Controls)
        controls_keys = [attr for attr in controls_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for ctrl_key in controls_keys:
            control_obj = getattr(control_utils.Controls, ctrl_key)
            if not control_obj:
                raise Exception(f'Missing control: {ctrl_key}')
            if not control_obj.is_curve_valid():
                raise Exception(f'Invalid control. Missing build function: "{ctrl_key}"')
