from unittest.mock import patch, MagicMock
from io import StringIO
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
from gt.utils import display_utils


class TestDisplayUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)\

    def test_toggle_uniform_lra(self):
        cube = maya_test_tools.create_poly_cube()
        lra_visibility_result = display_utils.toggle_uniform_lra(obj_list=cube, verbose=False)
        result = maya_test_tools.cmds.getAttr(f'{cube}.displayLocalAxis')
        expected = True
        self.assertEqual(expected, lra_visibility_result)
        self.assertEqual(expected, result)
        lra_visibility_result = display_utils.toggle_uniform_lra(obj_list=cube, verbose=False)
        result = maya_test_tools.cmds.getAttr(f'{cube}.displayLocalAxis')
        expected = False
        self.assertEqual(expected, lra_visibility_result)
        self.assertEqual(expected, result)

    def test_toggle_uniform_jnt_label(self):
        joint = maya_test_tools.cmds.joint()
        label_visibility_state = display_utils.toggle_uniform_jnt_label(jnt_list=joint, verbose=False)
        result = maya_test_tools.cmds.getAttr(f'{joint}.drawLabel')
        expected = True
        self.assertEqual(expected, label_visibility_state)
        self.assertEqual(expected, result)
        label_visibility_state = display_utils.toggle_uniform_jnt_label(jnt_list=joint, verbose=False)
        result = maya_test_tools.cmds.getAttr(f'{joint}.drawLabel')
        expected = False
        self.assertEqual(expected, label_visibility_state)
        self.assertEqual(expected, result)

    @patch('gt.utils.display_utils.cmds')
    @patch('gt.utils.display_utils.mel')
    def test_toggle_full_hud(self, mock_mel, mock_cmds):
        mock_eval = MagicMock()
        mock_mel.eval = mock_eval
        label_visibility_state = display_utils.toggle_full_hud(verbose=False)
        mock_eval.assert_called()
        expected = False
        self.assertEqual(expected, label_visibility_state)

    def test_set_joint_name_as_label(self):
        joint_one = maya_test_tools.cmds.joint()
        joint_two = maya_test_tools.cmds.joint()
        joints_to_test = [joint_one, joint_two]

        for jnt in joints_to_test:
            side_value = maya_test_tools.cmds.getAttr(f'{jnt}.side')
            expected = 0  # Center
            self.assertEqual(expected, side_value)
            type_value = maya_test_tools.cmds.getAttr(f'{jnt}.type')
            expected = 0  # None
            self.assertEqual(expected, type_value)
            label_value = maya_test_tools.cmds.getAttr(f'{jnt}.otherType')
            expected = "jaw"
            self.assertEqual(expected, label_value)
        # Update Label
        affected_joints = display_utils.set_joint_name_as_label(jnt_list=joints_to_test, verbose=False)
        expected = 2
        self.assertEqual(expected, affected_joints)
        for jnt in joints_to_test:
            side_value = maya_test_tools.cmds.getAttr(f'{jnt}.side')
            expected = 0  # Center
            self.assertEqual(expected, side_value)
            type_value = maya_test_tools.cmds.getAttr(f'{jnt}.type')
            expected = 18  # Other
            self.assertEqual(expected, type_value)
            label_value = maya_test_tools.cmds.getAttr(f'{jnt}.otherType')
            expected = jnt
            self.assertEqual(expected, label_value)

    @patch('gt.utils.display_utils.mel')
    def test_generate_udim_previews(self, mock_mel):
        for index in range(0, 10):
            maya_test_tools.cmds.createNode("file")
        mock_eval = MagicMock()
        mock_mel.eval = mock_eval
        affected_nodes = display_utils.generate_udim_previews(verbose=False)
        mock_eval.assert_called()
        expected = 10
        self.assertEqual(expected, affected_nodes)
