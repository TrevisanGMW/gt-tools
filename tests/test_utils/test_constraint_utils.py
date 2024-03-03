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
cmds = maya_test_tools.cmds


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

    def test_constraint_type_constants(self):
        attributes = vars(constraint_utils.ConstraintTypes)
        keys = [attr for attr in attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for key in keys:
            constraint_type = getattr(constraint_utils.ConstraintTypes, key)
            if not constraint_type:
                raise Exception(f'Missing constraint type: {key}')
            if not isinstance(constraint_type, str):
                raise Exception(f'Incorrect constraint type. Expected string, but got: "{type(constraint_type)}".')

    def test_get_constraint_function_parent(self):
        expected = cmds.parentConstraint
        constraint_type = constraint_utils.ConstraintTypes.PARENT
        function = constraint_utils.get_constraint_function(constraint_type=constraint_type)
        self.assertEqual(expected, function)

        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        result = function(cube_one, cube_two)
        expected = ["cube_two_parentConstraint1"]
        self.assertEqual(expected, result)

    def test_get_constraint_function_point(self):
        expected = cmds.pointConstraint
        constraint_type = constraint_utils.ConstraintTypes.POINT
        function = constraint_utils.get_constraint_function(constraint_type=constraint_type)
        self.assertEqual(expected, function)

        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        result = function(cube_one, cube_two)
        expected = ["cube_two_pointConstraint1"]
        self.assertEqual(expected, result)

    def test_get_constraint_function_orient(self):
        expected = cmds.orientConstraint
        constraint_type = constraint_utils.ConstraintTypes.ORIENT
        function = constraint_utils.get_constraint_function(constraint_type=constraint_type)
        self.assertEqual(expected, function)

        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        result = function(cube_one, cube_two)
        expected = ["cube_two_orientConstraint1"]
        self.assertEqual(expected, result)

    def test_get_constraint_function_scale(self):
        expected = cmds.scaleConstraint
        constraint_type = constraint_utils.ConstraintTypes.SCALE
        function = constraint_utils.get_constraint_function(constraint_type=constraint_type)
        self.assertEqual(expected, function)

        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        result = function(cube_one, cube_two)
        expected = ["cube_two_scaleConstraint1"]
        self.assertEqual(expected, result)

    def test_get_constraint_function_aim(self):
        expected = cmds.aimConstraint
        constraint_type = constraint_utils.ConstraintTypes.AIM
        function = constraint_utils.get_constraint_function(constraint_type=constraint_type)
        self.assertEqual(expected, function)

        cube_one = maya_test_tools.create_poly_cube(name="cube_one")
        cube_two = maya_test_tools.create_poly_cube(name="cube_two")
        result = function(cube_one, cube_two)
        expected = ["cube_two_aimConstraint1"]
        self.assertEqual(expected, result)

    def test_get_constraint_function_other(self):
        expected = cmds.geometryConstraint
        constraint_type = constraint_utils.ConstraintTypes.GEOMETRY
        function = constraint_utils.get_constraint_function(constraint_type=constraint_type)
        self.assertEqual(expected, function)
        expected = cmds.normalConstraint
        constraint_type = constraint_utils.ConstraintTypes.NORMAL
        function = constraint_utils.get_constraint_function(constraint_type=constraint_type)
        self.assertEqual(expected, function)
        expected = cmds.tangentConstraint
        constraint_type = constraint_utils.ConstraintTypes.TANGENT
        function = constraint_utils.get_constraint_function(constraint_type=constraint_type)
        self.assertEqual(expected, function)
        expected = cmds.poleVectorConstraint
        constraint_type = constraint_utils.ConstraintTypes.POLE_VECTOR
        function = constraint_utils.get_constraint_function(constraint_type=constraint_type)
        self.assertEqual(expected, function)

    def test_create_rivet_poly_creation(self):
        cube = maya_test_tools.create_poly_cube()
        edges = [f'{cube}.e[0]', f'{cube}.e[1]']
        result = constraint_utils.create_rivet(source_components=edges)
        expected = 'rivet1'
        self.assertEqual(expected, result)

    def test_create_rivet_surface_creation(self):
        sphere = cmds.sphere()[0]
        point = [f'{sphere}.uv[0][0]']
        result = constraint_utils.create_rivet(source_components=point)
        expected = 'rivet1'
        self.assertEqual(expected, result)

    def test_create_rivet_poly_pos(self):
        cube = maya_test_tools.create_poly_cube()
        edges = [f'{cube}.e[0]', f'{cube}.e[1]']
        rivet = constraint_utils.create_rivet(source_components=edges)
        result = cmds.getAttr(f'{rivet}.ty')
        expected = 0.0
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f'{rivet}.tx')
        expected = 0.0
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f'{rivet}.tz')
        expected = 0.5
        self.assertAlmostEqualSigFig(expected, result)
        cmds.move(1, 1, 1, cube)
        result = cmds.getAttr(f'{rivet}.ty')
        expected = 1.0
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f'{rivet}.tx')
        expected = 1.0
        self.assertAlmostEqualSigFig(expected, result)
        result = cmds.getAttr(f'{rivet}.tz')
        expected = 1.5
        self.assertAlmostEqualSigFig(expected, result)

    def test_equidistant_constraints(self):
        cube_start = maya_test_tools.create_poly_cube()
        cube_end = maya_test_tools.create_poly_cube()

        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        cube_three = maya_test_tools.create_poly_cube()

        targets = [cube_one, cube_two, cube_three]

        maya_test_tools.set_attribute(obj_name=cube_end, attr_name="ty", value=10)
        maya_test_tools.set_attribute(obj_name=cube_end, attr_name="tz", value=10)
        maya_test_tools.set_attribute(obj_name=cube_end, attr_name="rx", value=90)

        constraints = constraint_utils.equidistant_constraints(start=cube_start,
                                                               end=cube_end,
                                                               target_list=targets,
                                                               skip_start_end=True,
                                                               constraint='parent')
        expected_constraints = ['pCube3_parentConstraint1', 'pCube4_parentConstraint1', 'pCube5_parentConstraint1']
        self.assertEqual(expected_constraints, constraints)

        weight_1 = [0.75, 0.25]
        weight_2 = [0.5, 0.5]
        weight_3 = [0.25, 0.75]
        weights = [weight_1, weight_2, weight_3]
        for index, constraint in enumerate(expected_constraints):
            weight0 = cmds.getAttr(f'{constraint}.w0')
            weight1 = cmds.getAttr(f'{constraint}.w1')
            self.assertEqual(weights[index][0], weight0)
            self.assertEqual(weights[index][1], weight1)

        expected_values = {cube_one: [0, 2.5, 2.5,
                                      21.59, 0, 0],
                           cube_two: [0, 5, 5,
                                      45, 0, 0],
                           cube_three: [0, 7.5, 7.5,
                                        68.4, 0, 0]}
        for cube, expected in expected_values.items():
            tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
            ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
            tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
            rx = maya_test_tools.get_attribute(obj_name=cube, attr_name="rx")
            ry = maya_test_tools.get_attribute(obj_name=cube, attr_name="ry")
            rz = maya_test_tools.get_attribute(obj_name=cube, attr_name="rz")
            self.assertAlmostEqualSigFig(tx, expected[0])
            self.assertAlmostEqualSigFig(ty, expected[1])
            self.assertAlmostEqualSigFig(tz, expected[2])
            self.assertAlmostEqualSigFig(rx, expected[3])
            self.assertAlmostEqualSigFig(ry, expected[4])
            self.assertAlmostEqualSigFig(rz, expected[5])

    def test_equidistant_constraints_skip_start_end(self):
        cube_start = maya_test_tools.create_poly_cube()
        cube_end = maya_test_tools.create_poly_cube()

        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        cube_three = maya_test_tools.create_poly_cube()

        targets = [cube_one, cube_two, cube_three]

        maya_test_tools.set_attribute(obj_name=cube_end, attr_name="ty", value=10)
        maya_test_tools.set_attribute(obj_name=cube_end, attr_name="tz", value=10)
        maya_test_tools.set_attribute(obj_name=cube_end, attr_name="rx", value=90)

        constraints = constraint_utils.equidistant_constraints(start=cube_start,
                                                               end=cube_end,
                                                               target_list=targets,
                                                               skip_start_end=False,
                                                               constraint='parent')

        expected_constraints = ['pCube3_parentConstraint1', 'pCube4_parentConstraint1', 'pCube5_parentConstraint1']
        self.assertEqual(expected_constraints, constraints)

        weight_1 = [1, 0]
        weight_2 = [0.5, 0.5]
        weight_3 = [0, 1]
        weights = [weight_1, weight_2, weight_3]
        for index, constraint in enumerate(expected_constraints):
            weight0 = cmds.getAttr(f'{constraint}.w0')
            weight1 = cmds.getAttr(f'{constraint}.w1')
            self.assertEqual(weights[index][0], weight0)
            self.assertEqual(weights[index][1], weight1)

        expected_values = {cube_one: [0, 0, 0,
                                      0, 0, 0],
                           cube_two: [0, 5, 5,
                                      45, 0, 0],
                           cube_three: [0, 10, 10,
                                        90, 0, 0]}
        for cube, expected_constraints in expected_values.items():
            tx = maya_test_tools.get_attribute(obj_name=cube, attr_name="tx")
            ty = maya_test_tools.get_attribute(obj_name=cube, attr_name="ty")
            tz = maya_test_tools.get_attribute(obj_name=cube, attr_name="tz")
            rx = maya_test_tools.get_attribute(obj_name=cube, attr_name="rx")
            ry = maya_test_tools.get_attribute(obj_name=cube, attr_name="ry")
            rz = maya_test_tools.get_attribute(obj_name=cube, attr_name="rz")
            self.assertAlmostEqualSigFig(tx, expected_constraints[0])
            self.assertAlmostEqualSigFig(ty, expected_constraints[1])
            self.assertAlmostEqualSigFig(tz, expected_constraints[2])
            self.assertAlmostEqualSigFig(rx, expected_constraints[3])
            self.assertAlmostEqualSigFig(ry, expected_constraints[4])
            self.assertAlmostEqualSigFig(rz, expected_constraints[5])

    def test_equidistant_constraints_types(self):
        types_to_test = ['parent', 'point', 'orient', 'scale']
        for typ in types_to_test:
            cube_start = maya_test_tools.create_poly_cube()
            cube_end = maya_test_tools.create_poly_cube()

            cube_one = maya_test_tools.create_poly_cube()
            cube_two = maya_test_tools.create_poly_cube()
            cube_three = maya_test_tools.create_poly_cube()

            targets = [cube_one, cube_two, cube_three]

            maya_test_tools.set_attribute(obj_name=cube_end, attr_name="ty", value=10)
            maya_test_tools.set_attribute(obj_name=cube_end, attr_name="tz", value=10)
            maya_test_tools.set_attribute(obj_name=cube_end, attr_name="rx", value=90)

            constraints = constraint_utils.equidistant_constraints(start=cube_start,
                                                                   end=cube_end,
                                                                   target_list=targets,
                                                                   skip_start_end=False,
                                                                   constraint=typ)

            for constraint in constraints:
                result = cmds.objectType(constraint)
                expected = f'{typ}Constraint'
                self.assertEqual(expected, result)

            maya_test_tools.force_new_scene()

    def test_equidistant_constraints_string_input(self):
        cube_start = maya_test_tools.create_poly_cube()
        cube_end = maya_test_tools.create_poly_cube()
        cube_target = maya_test_tools.create_poly_cube()

        maya_test_tools.set_attribute(obj_name=cube_end, attr_name="ty", value=10)
        maya_test_tools.set_attribute(obj_name=cube_end, attr_name="tz", value=10)
        maya_test_tools.set_attribute(obj_name=cube_end, attr_name="rx", value=90)

        constraints = constraint_utils.equidistant_constraints(start=cube_start,
                                                               end=cube_end,
                                                               target_list=cube_target,
                                                               skip_start_end=True,
                                                               constraint='parent')
        expected_constraints = ['pCube3_parentConstraint1']
        self.assertEqual(expected_constraints, constraints)

    def test_constraint_targets_single_source_single_target(self):
        cube_source = maya_test_tools.create_poly_cube(name="cube_source")
        cube_target = maya_test_tools.create_poly_cube(name="cube_target")

        maya_test_tools.set_attribute(obj_name=cube_source, attr_name="tx", value=10)
        maya_test_tools.set_attribute(obj_name=cube_source, attr_name="tz", value=10)
        maya_test_tools.set_attribute(obj_name=cube_source, attr_name="rx", value=90)

        constraint_type = constraint_utils.ConstraintTypes.PARENT
        constraints = constraint_utils.constraint_targets(source_driver=cube_source,
                                                          target_driven=cube_target,
                                                          constraint_type=constraint_type,
                                                          maintain_offset=False,
                                                          inter_type=0,
                                                          rename_constraint=True)
        expected_constraints = ["|cube_target|cube_target_parentConstraint"]
        self.assertEqual(expected_constraints, constraints)

        tx = cmds.getAttr(f'{cube_target}.tx')
        tz = cmds.getAttr(f'{cube_target}.tz')
        rx = cmds.getAttr(f'{cube_target}.rx')
        expected_tx = 10
        expected_tz = 10
        expected_rx = 90
        self.assertEqual(expected_tx, tx)
        self.assertEqual(expected_tz, tz)
        self.assertEqual(expected_rx, rx)

    def test_constraint_targets_multiple_sources_multiple_targets(self):
        cube_source_one = maya_test_tools.create_poly_cube(name="cube_source_one")
        cube_source_two = maya_test_tools.create_poly_cube(name="cube_source_two")
        cube_target_one = maya_test_tools.create_poly_cube(name="cube_target_one")
        cube_target_two = maya_test_tools.create_poly_cube(name="cube_target_two")

        maya_test_tools.set_attribute(obj_name=cube_source_one, attr_name="tx", value=5)

        constraint_type = constraint_utils.ConstraintTypes.PARENT
        constraints = constraint_utils.constraint_targets(source_driver=[cube_source_one, cube_source_two],
                                                          target_driven=[cube_target_one, cube_target_two],
                                                          constraint_type=constraint_type,
                                                          maintain_offset=False,
                                                          inter_type=0,
                                                          rename_constraint=True)
        expected_constraints = ["|cube_target_one|cube_target_one_parentConstraint",
                                "|cube_target_two|cube_target_two_parentConstraint"]
        self.assertEqual(expected_constraints, constraints)

        tx = cmds.getAttr(f'{cube_target_one}.tx')
        expected_tx = 2.5
        self.assertEqual(expected_tx, tx)
        tx = cmds.getAttr(f'{cube_target_two}.tx')
        expected_tx = 2.5
        self.assertEqual(expected_tx, tx)

    def test_constraint_targets_offset_and_naming(self):
        cube_source_one = maya_test_tools.create_poly_cube(name="cube_source")
        cube_target_one = maya_test_tools.create_poly_cube(name="cube_target")

        maya_test_tools.set_attribute(obj_name=cube_source_one, attr_name="tx", value=5)

        constraint_type = constraint_utils.ConstraintTypes.POINT
        constraints = constraint_utils.constraint_targets(source_driver=cube_source_one,
                                                          target_driven=cube_target_one,
                                                          constraint_type=constraint_type,
                                                          maintain_offset=True,
                                                          inter_type=0,
                                                          rename_constraint=False)
        expected_constraints = ["|cube_target|cube_target_pointConstraint1"]
        self.assertEqual(expected_constraints, constraints)

        tx = cmds.getAttr(f'{cube_target_one}.tx')
        expected_tx = 0
        self.assertEqual(expected_tx, tx)
