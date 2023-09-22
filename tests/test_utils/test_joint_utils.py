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
from gt.utils import joint_utils


class TestJointUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_convert_joints_to_mesh_selected_one(self):
        joint = maya_test_tools.cmds.joint()
        maya_test_tools.cmds.select(joint)
        result = joint_utils.convert_joints_to_mesh()
        expected = [f'{joint}JointMesh']
        self.assertEqual(expected, result)

    def test_convert_joints_to_mesh_selected_hierarchy(self):
        joint_one = maya_test_tools.cmds.joint()
        maya_test_tools.cmds.joint()
        maya_test_tools.cmds.select(joint_one)
        result = joint_utils.convert_joints_to_mesh()
        expected = [f'{joint_one}AsMesh']
        self.assertEqual(expected, result)

    def test_convert_joints_to_mesh_str_input(self):
        joint_one = maya_test_tools.cmds.joint()
        result = joint_utils.convert_joints_to_mesh(root_jnt=joint_one)
        expected = [f'{joint_one}JointMesh']
        self.assertEqual(expected, result)
