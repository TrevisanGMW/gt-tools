import os
import sys
import logging
import unittest

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
from gt.core import camera as core_camera

cmds = maya_test_tools.cmds


class TestCameraCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_reset_camera_transform_attributes(self):
        camera_transform = "persp"
        cmds.setAttr(f"{camera_transform}.sx", 2)
        cmds.setAttr(f"{camera_transform}.sy", 2)
        cmds.setAttr(f"{camera_transform}.sz", 2)
        logging.disable(logging.WARNING)
        core_camera.reset_camera_attributes()
        logging.disable(logging.NOTSET)
        result = cmds.getAttr(f"{camera_transform}.sx")
        expected = 1
        self.assertEqual(expected, result)

    def test_reset_camera_shape_attributes_focal_length(self):
        camera_shape = "perspShape"
        cmds.setAttr(f"{camera_shape}.focalLength", 2)
        logging.disable(logging.WARNING)
        core_camera.reset_camera_attributes()
        logging.disable(logging.NOTSET)
        result = cmds.getAttr(f"{camera_shape}.focalLength")
        expected = 35
        self.assertEqual(expected, result)
