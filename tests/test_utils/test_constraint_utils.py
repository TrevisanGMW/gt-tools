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
from gt.utils import constraint_utils


class TestConstraintUtils(unittest.TestCase):
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

        str_formatter = '{0:.' + str(tolerance) + 'e}'
        significand_1 = float(str_formatter.format(arg1).split('e')[0])
        significand_2 = float(str_formatter.format(arg2).split('e')[0])

        exponent_1 = int(str_formatter.format(arg1).split('e')[1])
        exponent_2 = int(str_formatter.format(arg2).split('e')[1])

        self.assertEqual(significand_1, significand_2)
        self.assertEqual(exponent_1, exponent_2)

    def test_create_rivet_poly_creation(self):
        cube = maya_test_tools.create_poly_cube()
        edges = [f'{cube}.e[0]', f'{cube}.e[1]']
        result = constraint_utils.create_rivet(source_components=edges)
        expected = 'rivet1'
        self.assertEqual(expected, result)

    def test_create_rivet_surface_creation(self):
        sphere = maya_test_tools.cmds.sphere()[0]
        point = [f'{sphere}.uv[0][0]']
        result = constraint_utils.create_rivet(source_components=point)
        expected = 'rivet1'
        self.assertEqual(expected, result)

    def test_create_rivet_poly_pos(self):
        cube = maya_test_tools.create_poly_cube()
        edges = [f'{cube}.e[0]', f'{cube}.e[1]']
        rivet = constraint_utils.create_rivet(source_components=edges)
        result = maya_test_tools.cmds.getAttr(f'{rivet}.ty')
        expected = 0.0
        self.assertAlmostEqualSigFig(expected, result)
        result = maya_test_tools.cmds.getAttr(f'{rivet}.tx')
        expected = 0.0
        self.assertAlmostEqualSigFig(expected, result)
        result = maya_test_tools.cmds.getAttr(f'{rivet}.tz')
        expected = 0.5
        self.assertAlmostEqualSigFig(expected, result)
        maya_test_tools.cmds.move(1, 1, 1, cube)
        result = maya_test_tools.cmds.getAttr(f'{rivet}.ty')
        expected = 1.0
        self.assertAlmostEqualSigFig(expected, result)
        result = maya_test_tools.cmds.getAttr(f'{rivet}.tx')
        expected = 1.0
        self.assertAlmostEqualSigFig(expected, result)
        result = maya_test_tools.cmds.getAttr(f'{rivet}.tz')
        expected = 1.5
        self.assertAlmostEqualSigFig(expected, result)
