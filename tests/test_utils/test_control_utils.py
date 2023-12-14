from unittest.mock import MagicMock, patch
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
from gt.utils.control_utils import Control
from gt.utils import control_utils


class TestControlUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        self.mocked_parameters = {'param1': 10, 'param2': 'test'}
        self.mocked_parameters_different_values = {'param1': 20, 'param2': 'test_two'}
        self.mocked_original_parameters = {'param1': 10, 'param2': 'test'}
        self.mocked_function_one = MagicMock(return_value='dummy_curve')
        self.control = Control()

        def mocked_function_two(key1=None, key2=None):
            pass
        self.mocked_function_two = mocked_function_two
        self.mocked_function_two_parameters = {"key1": None, "key2": None}

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
        expected = 'pCube1'
        self.assertEqual(expected, result)
        self.assertEqual(expected, ctrl.get_last_callable_output())

    def test_init_with_name(self):
        expected = 'my_control'
        control = Control(name=expected)
        result = control.get_name()
        self.assertEqual(expected, result)

    def test_init_with_build_function(self):
        expected = self.mocked_function_one
        control = Control(build_function=expected)
        result = control.build_function
        self.assertEqual(expected, result)

    def test_set_parameters_dict(self):
        expected = self.mocked_parameters
        self.control.set_parameters(expected)
        result = self.control.parameters
        self.assertEqual(expected, result)

    def test_set_parameters_json(self):
        dummy_parameters_dict = '{"param1": 10, "param2": "test"}'
        expected = self.mocked_parameters
        self.control.set_parameters(dummy_parameters_dict)
        result = self.control.parameters
        self.assertEqual(expected, result)

    def test_set_parameters_invalid_json(self):
        invalid_dict = 'invalid_dict'
        expected = {}
        logging.disable(logging.WARNING)
        self.control.set_parameters(invalid_dict)
        logging.disable(logging.NOTSET)
        result = self.control.parameters
        self.assertEqual(expected, result)

    def test_get_parameters(self):
        expected = self.mocked_parameters
        self.control.set_parameters(expected)
        result = self.control.get_parameters()
        self.assertEqual(expected, result)

    def test_validate_parameters_valid(self):
        self.control.set_parameters(self.mocked_parameters)
        self.control._set_original_parameters(self.mocked_original_parameters)
        expected = True
        result = self.control.validate_parameters()
        self.assertEqual(expected, result)
        self.control.set_parameters(self.mocked_parameters_different_values)
        expected = True
        result = self.control.validate_parameters()
        self.assertEqual(expected, result)

    def test_validate_parameters_invalid_keys(self):
        self.control.set_parameters(self.mocked_parameters)
        invalid_parameters = {'param1': 20, 'param3': 'new'}
        self.control._set_original_parameters(invalid_parameters)
        expected = False
        result = self.control.validate_parameters()
        self.assertEqual(expected, result)

    def test_validate_parameters_invalid_value_types(self):
        self.control.set_parameters(self.mocked_parameters)
        invalid_parameters = {'param1': 'string', 'param2': 10}
        self.control._set_original_parameters(invalid_parameters)
        expected = False
        result = self.control.validate_parameters()
        self.assertEqual(expected, result)

    def test_set_build_function(self):
        expected = self.mocked_function_one
        self.control.set_build_function(expected)
        result = self.control.build_function
        self.assertEqual(expected, result)

    def test_build_valid_parameters(self):
        self.control.set_build_function(self.mocked_function_one)
        self.control.set_parameters(self.mocked_parameters)
        expected = 'dummy_curve'
        logging.disable(logging.WARNING)
        result = self.control.build()
        logging.disable(logging.NOTSET)
        self.assertEqual(expected, result)

    def test_build_invalid_parameters(self):
        self.control.set_build_function(self.mocked_function_two)
        self.control._set_original_parameters(self.mocked_original_parameters)
        expected = False
        result = self.control.validate_parameters()
        self.assertEqual(expected, result)

    def test_is_curve_valid_with_function(self):
        self.control.set_build_function(self.mocked_function_one)
        expected = True
        result = self.control.is_curve_valid()
        self.assertEqual(expected, result)

    def test_is_curve_valid_without_function(self):
        expected = False
        result = self.control.is_curve_valid()
        self.assertEqual(expected, result)

    def test_get_last_callable_output(self):
        self.control.set_build_function(self.mocked_function_one)
        self.control.set_parameters(self.mocked_parameters)
        logging.disable(logging.WARNING)
        self.control.build()
        logging.disable(logging.NOTSET)
        expected = 'dummy_curve'
        result = self.control.get_last_callable_output()
        self.assertEqual(expected, result)

    def test_get_docstrings_no_function(self):
        expected = None
        result = self.control.get_docstrings()
        self.assertEqual(expected, result)

    def test_get_docstrings_no_docstring(self):
        self.control.set_build_function(self.mocked_function_two)
        expected = ""
        result = self.control.get_docstrings()
        self.assertEqual(expected, result)

    def test_get_docstrings_docstring(self):
        self.control.set_build_function(self.mocked_function_one)
        expected = True
        result = isinstance(self.control.get_docstrings(), str)
        self.assertEqual(expected, result)

    def test_curves_existence(self):
        controls_attributes = vars(control_utils.Controls)
        controls_keys = [attr for attr in controls_attributes if not (attr.startswith('__') and attr.endswith('__'))]
        for ctrl_key in controls_keys:
            control_obj = getattr(control_utils.Controls, ctrl_key)
            if not control_obj:
                raise Exception(f'Missing control: {ctrl_key}')
            if not control_obj.is_curve_valid():
                raise Exception(f'Invalid control. Missing build function: "{ctrl_key}"')

    def test_get_control_preview_image_path(self):
        path = control_utils.get_control_preview_image_path("scalable_one_side_arrow")
        result = os.path.exists(path)
        self.assertTrue(result)
        result = os.path.basename(path)
        expected = "scalable_one_side_arrow.jpg"
        self.assertEqual(expected, result)

    def test_add_snapping_shape(self):
        cube = maya_test_tools.create_poly_cube()
        result = control_utils.add_snapping_shape(target_object=cube)
        cube_shapes = maya_test_tools.cmds.listRelatives(cube, shapes=True, fullPath=True) or []
        expected = '|pCube1|snappingPointShape'
        self.assertIn(expected, cube_shapes)
        self.assertEqual(expected, result)
        result = control_utils.add_snapping_shape(target_object=cube)
        expected = None
        self.assertEqual(expected, result)

    def test_add_snapping_shape_attr_visibility(self):
        cube = maya_test_tools.create_poly_cube()
        shape = control_utils.add_snapping_shape(target_object=cube)
        is_hidden_lpx = maya_test_tools.cmds.getAttr(f'{shape}.lpx', channelBox=True)
        is_hidden_lpy = maya_test_tools.cmds.getAttr(f'{shape}.lpy', channelBox=True)
        is_hidden_lpz = maya_test_tools.cmds.getAttr(f'{shape}.lpz', channelBox=True)
        is_hidden_lsx = maya_test_tools.cmds.getAttr(f'{shape}.lsx', channelBox=True)
        is_hidden_lsy = maya_test_tools.cmds.getAttr(f'{shape}.lsy', channelBox=True)
        is_hidden_lsz = maya_test_tools.cmds.getAttr(f'{shape}.lsz', channelBox=True)
        self.assertFalse(is_hidden_lpx)
        self.assertFalse(is_hidden_lpy)
        self.assertFalse(is_hidden_lpz)
        self.assertFalse(is_hidden_lsx)
        self.assertFalse(is_hidden_lsy)
        self.assertFalse(is_hidden_lsz)

    def test_create_fk(self):
        joint_one = maya_test_tools.cmds.createNode("joint", name="jnt_one")
        joint_two = maya_test_tools.cmds.createNode("joint", name="jnt_two")
        joint_three = maya_test_tools.cmds.createNode("joint", name="jnt_three")
        maya_test_tools.cmds.setAttr(f'{joint_two}.tx', 1)
        maya_test_tools.cmds.setAttr(f'{joint_three}.tx', 2)
        maya_test_tools.cmds.parent(joint_two, joint_one)
        maya_test_tools.cmds.parent(joint_three, joint_two)
        joints = [joint_one, joint_two, joint_three]

        result = control_utils.create_fk(joint_list=joints,
                                         curve_shape=None,
                                         scale_multiplier=1,
                                         colorize=True,
                                         constraint_joint=True,
                                         mimic_joint_hierarchy=True,
                                         filter_string=f"_end",
                                         suffix_ctrl=f"_ctrl",
                                         suffix_offset=f"_offset",
                                         suffix_joint=f"_jnt")
        from gt.utils.node_utils import Node
        ctrl_one = Node("|jnt_one_offset|jnt_one_ctrl")
        ctrl_two = Node("|jnt_one_offset|jnt_one_ctrl|jnt_two_offset|jnt_two_ctrl")
        ctrl_three = Node("|jnt_one_offset|jnt_one_ctrl|jnt_two_offset|jnt_two_ctrl|jnt_three_offset|jnt_three_ctrl")
        expected = [ctrl_one, ctrl_two, ctrl_three]
        self.assertEqual(str(expected), str(result))

    def test_create_fk_no_hierarchy(self):
        joint_one = maya_test_tools.cmds.createNode("joint", name="jnt_one")
        joint_two = maya_test_tools.cmds.createNode("joint", name="jnt_two")
        joint_three = maya_test_tools.cmds.createNode("joint", name="jnt_three")
        maya_test_tools.cmds.setAttr(f'{joint_two}.tx', 1)
        maya_test_tools.cmds.setAttr(f'{joint_three}.tx', 2)
        maya_test_tools.cmds.parent(joint_two, joint_one)
        maya_test_tools.cmds.parent(joint_three, joint_two)
        joints = [joint_one, joint_two, joint_three]

        result = control_utils.create_fk(joint_list=joints,
                                         curve_shape=None,
                                         scale_multiplier=1,
                                         colorize=True,
                                         constraint_joint=True,
                                         mimic_joint_hierarchy=False,
                                         filter_string=f"_end",
                                         suffix_ctrl=f"_ctrl",
                                         suffix_offset=f"_offset",
                                         suffix_joint=f"_jnt")
        from gt.utils.node_utils import Node
        ctrl_one = Node("|jnt_one_offset|jnt_one_ctrl")
        ctrl_two = Node("|jnt_two_offset|jnt_two_ctrl")
        ctrl_three = Node("|jnt_three_offset|jnt_three_ctrl")
        expected = [ctrl_one, ctrl_two, ctrl_three]
        self.assertEqual(str(expected), str(result))

    def test_create_fk_custom_curve_shape(self):
        joint_one = maya_test_tools.cmds.createNode("joint", name="jnt_one")
        joint_two = maya_test_tools.cmds.createNode("joint", name="jnt_two")
        joint_three = maya_test_tools.cmds.createNode("joint", name="jnt_three")
        maya_test_tools.cmds.setAttr(f'{joint_two}.tx', 1)
        maya_test_tools.cmds.setAttr(f'{joint_three}.tx', 2)
        maya_test_tools.cmds.parent(joint_two, joint_one)
        maya_test_tools.cmds.parent(joint_three, joint_two)
        joints = [joint_one, joint_two, joint_three]

        from gt.utils.curve_utils import Curves
        result = control_utils.create_fk(joint_list=joints,
                                         curve_shape=Curves.circle,
                                         scale_multiplier=1,
                                         colorize=True,
                                         constraint_joint=True,
                                         mimic_joint_hierarchy=False,
                                         filter_string=f"_end",
                                         suffix_ctrl=f"_ctrl",
                                         suffix_offset=f"_offset",
                                         suffix_joint=f"_jnt")
        from gt.utils.node_utils import Node
        ctrl_one = Node("|jnt_one_offset|jnt_one_ctrl")
        ctrl_two = Node("|jnt_two_offset|jnt_two_ctrl")
        ctrl_three = Node("|jnt_three_offset|jnt_three_ctrl")
        expected = [ctrl_one, ctrl_two, ctrl_three]
        self.assertEqual(str(expected), str(result))

    def test_create_fk_custom_names(self):
        joint_one = maya_test_tools.cmds.createNode("joint", name="jnt_one")
        joint_two = maya_test_tools.cmds.createNode("joint", name="jnt_two")
        joint_three = maya_test_tools.cmds.createNode("joint", name="jnt_three")
        maya_test_tools.cmds.setAttr(f'{joint_two}.tx', 1)
        maya_test_tools.cmds.setAttr(f'{joint_three}.tx', 2)
        maya_test_tools.cmds.parent(joint_two, joint_one)
        maya_test_tools.cmds.parent(joint_three, joint_two)
        joints = [joint_one, joint_two, joint_three]

        from gt.utils.curve_utils import Curves
        result = control_utils.create_fk(joint_list=joints,
                                         curve_shape=Curves.circle,
                                         scale_multiplier=1,
                                         colorize=True,
                                         constraint_joint=True,
                                         mimic_joint_hierarchy=False,
                                         filter_string=f"_end",
                                         suffix_ctrl=f"_control",
                                         suffix_offset=f"_grp",
                                         suffix_joint=f"_one")
        from gt.utils.node_utils import Node
        ctrl_one = Node("|jnt_grp|jnt_control")
        ctrl_two = Node("|jnt_two_grp|jnt_two_control")
        ctrl_three = Node("|jnt_three_grp|jnt_three_control")
        expected = [ctrl_one, ctrl_two, ctrl_three]
        self.assertEqual(str(expected), str(result))

    def test_selected_create_fk(self):
        joint_one = maya_test_tools.cmds.createNode("joint", name="jnt_one")
        joint_two = maya_test_tools.cmds.createNode("joint", name="jnt_two")
        joint_three = maya_test_tools.cmds.createNode("joint", name="jnt_three")
        maya_test_tools.cmds.setAttr(f'{joint_two}.tx', 1)
        maya_test_tools.cmds.setAttr(f'{joint_three}.tx', 2)
        maya_test_tools.cmds.parent(joint_two, joint_one)
        maya_test_tools.cmds.parent(joint_three, joint_two)
        joints = [joint_one, joint_two, joint_three]
        maya_test_tools.cmds.select(joints)

        result = control_utils.selected_create_fk()
        from gt.utils.node_utils import Node
        ctrl_one = Node("|jnt_one_offset|jnt_one_ctrl")
        ctrl_two = Node("|jnt_one_offset|jnt_one_ctrl|jnt_two_offset|jnt_two_ctrl")
        ctrl_three = Node("|jnt_one_offset|jnt_one_ctrl|jnt_two_offset|jnt_two_ctrl|jnt_three_offset|jnt_three_ctrl")
        expected = [ctrl_one, ctrl_two, ctrl_three]
        self.assertEqual(str(expected), str(result))
