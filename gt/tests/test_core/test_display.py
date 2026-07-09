from unittest.mock import patch, MagicMock
from unittest import mock
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
from gt.tests import maya_test_tools
from gt.core import display as core_display

cmds = maya_test_tools.cmds


class TestDisplayCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)\

    def test_toggle_uniform_lra(self):
        cube = maya_test_tools.create_poly_cube()
        lra_visibility_result = core_display.toggle_uniform_lra(obj_list=cube, verbose=False)
        result = cmds.getAttr(f"{cube}.displayLocalAxis")
        expected = True
        self.assertEqual(expected, lra_visibility_result)
        self.assertEqual(expected, result)
        lra_visibility_result = core_display.toggle_uniform_lra(obj_list=cube, verbose=False)
        result = cmds.getAttr(f"{cube}.displayLocalAxis")
        expected = False
        self.assertEqual(expected, lra_visibility_result)
        self.assertEqual(expected, result)

    def test_set_lra_state_true(self):
        cube = maya_test_tools.create_poly_cube()
        affected_list = core_display.set_lra_state(obj_list=cube, state=True, verbose=False)
        result = cmds.getAttr(f"{cube}.displayLocalAxis")
        expected = True
        self.assertEqual([cube], affected_list)
        self.assertEqual(expected, result)

    def test_set_lra_state_false(self):
        cube = maya_test_tools.create_poly_cube()
        affected_list = core_display.set_lra_state(obj_list=cube, state=False, verbose=False)
        result = cmds.getAttr(f"{cube}.displayLocalAxis")
        expected = False
        self.assertEqual([cube], affected_list)
        self.assertEqual(expected, result)

    def test_set_lra_state_multiple(self):
        cube_one = maya_test_tools.create_poly_cube()
        cube_two = maya_test_tools.create_poly_cube()
        to_test = [cube_one, cube_two]
        affected_list = core_display.set_lra_state(obj_list=to_test, state=True, verbose=False)
        self.assertEqual(to_test, affected_list)
        for obj in to_test:
            result = cmds.getAttr(f"{obj}.displayLocalAxis")
            expected = True
            self.assertEqual(expected, result)

    def test_toggle_uniform_jnt_label(self):
        joint = cmds.joint()
        label_visibility_state = core_display.toggle_uniform_jnt_label(jnt_list=joint, verbose=False)
        result = cmds.getAttr(f"{joint}.drawLabel")
        expected = True
        self.assertEqual(expected, label_visibility_state)
        self.assertEqual(expected, result)
        label_visibility_state = core_display.toggle_uniform_jnt_label(jnt_list=joint, verbose=False)
        result = cmds.getAttr(f"{joint}.drawLabel")
        expected = False
        self.assertEqual(expected, label_visibility_state)
        self.assertEqual(expected, result)

    @patch("gt.core.display.cmds")
    @patch("gt.core.display.mel")
    def test_toggle_full_hud(self, mock_mel, mock_cmds):
        mock_eval = MagicMock()
        mock_mel.eval = mock_eval
        label_visibility_state = core_display.toggle_full_hud(verbose=False)
        mock_eval.assert_called()
        expected = False
        self.assertEqual(expected, label_visibility_state)

    def test_set_joint_name_as_label(self):
        joint_one = cmds.joint()
        joint_two = cmds.joint()
        joints_to_test = [joint_one, joint_two]

        for jnt in joints_to_test:
            side_value = cmds.getAttr(f"{jnt}.side")
            expected = 0  # Center
            self.assertEqual(expected, side_value)
            type_value = cmds.getAttr(f"{jnt}.type")
            expected = 0  # None
            self.assertEqual(expected, type_value)
            label_value = cmds.getAttr(f"{jnt}.otherType")
            expected = "jaw"
            self.assertEqual(expected, label_value)
        # Update Label
        affected_joints = core_display.set_joint_name_as_label(joints=joints_to_test, verbose=False)
        expected = 2
        self.assertEqual(expected, affected_joints)
        for jnt in joints_to_test:
            side_value = cmds.getAttr(f"{jnt}.side")
            expected = 0  # Center
            self.assertEqual(expected, side_value)
            type_value = cmds.getAttr(f"{jnt}.type")
            expected = 18  # Other
            self.assertEqual(expected, type_value)
            label_value = cmds.getAttr(f"{jnt}.otherType")
            expected = jnt
            self.assertEqual(expected, label_value)

    @patch("gt.core.display.mel")
    def test_generate_udim_previews(self, mock_mel):
        for index in range(0, 10):
            cmds.createNode("file")
        mock_eval = MagicMock()
        mock_mel.eval = mock_eval
        affected_nodes = core_display.generate_udim_previews(verbose=False)
        mock_eval.assert_called()
        expected = 10
        self.assertEqual(expected, affected_nodes)

    def test_reset_joint_display(self):
        joint_one = cmds.joint()
        joint_two = cmds.joint()
        cmds.joint()  # Purposely left out of affected joints
        joints_to_test = [joint_one, joint_two]

        expected = 2
        cmds.jointDisplayScale(expected)  # Something other than 1
        display_scale = cmds.jointDisplayScale(query=True)
        self.assertEqual(expected, display_scale)

        for jnt in joints_to_test:
            expected = 2
            cmds.setAttr(f"{jnt}.radius", expected)  # Something other than 1
            radius_value = cmds.getAttr(f"{jnt}.radius")
            self.assertEqual(expected, radius_value)
            expected = 2
            cmds.setAttr(f"{jnt}.drawStyle", expected)  # None
            draw_style_value = cmds.getAttr(f"{jnt}.drawStyle")
            self.assertEqual(expected, draw_style_value)
            expected = False
            cmds.setAttr(f"{jnt}.visibility", expected)
            visibility_value = cmds.getAttr(f"{jnt}.visibility")
            self.assertEqual(expected, visibility_value)
        # Update Label
        affected_joints = core_display.reset_joint_display(jnt_list=joints_to_test, verbose=False)
        expected_affected_joints = 2
        self.assertEqual(expected_affected_joints, affected_joints)

        expected_display_scale = 1
        display_scale = cmds.jointDisplayScale(query=True)
        self.assertEqual(expected_display_scale, display_scale)

        for jnt in joints_to_test:
            expected = 1
            cmds.setAttr(f"{jnt}.radius", expected)  # Something other than 1
            radius_value = cmds.getAttr(f"{jnt}.radius")
            self.assertEqual(expected, radius_value)
            expected = 1
            cmds.setAttr(f"{jnt}.drawStyle", expected)  # None
            draw_style_value = cmds.getAttr(f"{jnt}.drawStyle")
            self.assertEqual(expected, draw_style_value)
            expected = True
            cmds.setAttr(f"{jnt}.visibility", expected)
            visibility_value = cmds.getAttr(f"{jnt}.visibility")
            self.assertEqual(expected, visibility_value)

    def test_delete_display_layers(self):
        display_layer_one = cmds.createDisplayLayer(name="mocked_layer_one", empty=True)
        display_layer_two = cmds.createDisplayLayer(name="mocked_layer_two", empty=True)
        affected_layers = core_display.delete_display_layers(layer_list=display_layer_one, verbose=False)
        expected_affected_layers = 1
        self.assertEqual(expected_affected_layers, affected_layers)
        self.assertFalse(cmds.objExists(display_layer_one), "Found unexpected layer.")
        self.assertTrue(cmds.objExists(display_layer_two), "Missing expected layer.")

    @mock.patch("maya.cmds.refresh")
    @mock.patch("maya.cmds.grid")
    def test_set_grid_divisions_default_values(self, mock_grid, mock_refresh):
        expected_size = 12.0
        expected_spacing = 5.0
        expected_divisions = 5

        core_display.set_grid_divisions()

        mock_grid.assert_called_once_with(size=expected_size, spacing=expected_spacing, divisions=expected_divisions)
        mock_refresh.assert_called_once()

    @mock.patch("maya.cmds.refresh")
    @mock.patch("maya.cmds.grid")
    def test_set_grid_divisions_custom_values(self, mock_grid, mock_refresh):
        grid_size = 20.0
        grid_spacing = 2.5
        grid_divisions = 10

        core_display.set_grid_divisions(grid_size=grid_size, grid_spacing=grid_spacing, grid_divisions=grid_divisions)

        mock_grid.assert_called_once_with(size=grid_size, spacing=grid_spacing, divisions=grid_divisions)
        mock_refresh.assert_called_once()
