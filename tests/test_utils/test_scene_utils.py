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
from utils import scene_utils


def import_test_scene():
    """
    Open files from inside the test_*/data folder/cube_namespaces.mb
    Scene contains a cube named: "parentNS:childNS:grandchildNS:pCube1"
    """
    maya_test_tools.import_data_file("cube_namespaces.mb")


class TestSceneUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_frame_rate(self):
        import_test_scene()
        expected = 24
        result = scene_utils.get_frame_rate()
        self.assertEqual(expected, result)

    def test_get_frame_rate_changed(self):
        import_test_scene()
        maya_test_tools.set_scene_framerate(time="ntscf")
        expected = 60
        result = scene_utils.get_frame_rate()
        self.assertEqual(expected, result)

    def test_get_distance_in_meters(self):
        import_test_scene()
        expected = 100
        result = scene_utils.get_distance_in_meters()
        self.assertEqual(expected, result)
