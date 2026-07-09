"""
Unittest related to core.poses
"""

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

import gt.tests.maya_test_tools as maya_test_tools
import gt.core.naming as core_naming
import gt.core.poses as core_poses

cmds = maya_test_tools.cmds


def import_poses_test_file():
    """
    Import test biped skeleton with dag poses file from inside the .../data folder/<name>.ma
    """
    maya_test_tools.import_data_file("skel_biped_poses.ma")


class TestPosesCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_check_main_poses(self):
        import_poses_test_file()
        result = core_poses.check_main_poses()
        expected = True
        self.assertEqual(expected, result)

    def test_apose_members(self):
        import_poses_test_file()
        result = core_poses.check_dagpose_members()
        expected = True
        self.assertEqual(expected, result)

    def test_delete_dagposes(self):
        import_poses_test_file()

        apose_name = core_naming.NamingConstants.Poses.APOSE
        tpose_name = core_naming.NamingConstants.Poses.TPOSE
        core_poses.delete_dagpose(apose_name)
        core_poses.delete_dagpose(tpose_name)

        result = core_poses.check_main_poses()
        expected = False
        self.assertEqual(expected, result)
