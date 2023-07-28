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
from gt.utils import camera_utils


class TestCameraUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_reset_camera_transform_attributes(self):
        camera_transform = 'persp'
        maya_test_tools.set_attribute(obj_name=camera_transform, attr_name="sx", value=2)
        maya_test_tools.set_attribute(obj_name=camera_transform, attr_name="sy", value=2)
        maya_test_tools.set_attribute(obj_name=camera_transform, attr_name="sz", value=2)
        logging.disable(logging.WARNING)
        camera_utils.reset_persp_shape_attributes()
        logging.disable(logging.NOTSET)
        result = maya_test_tools.get_attribute(obj_name=camera_transform, attr_name='sx')
        expected = 1
        self.assertEqual(expected, result)

    def test_reset_camera_shape_attributes_focal_length(self):
        camera_shape = 'perspShape'
        maya_test_tools.set_attribute(obj_name=camera_shape, attr_name="focalLength", value=2)
        logging.disable(logging.WARNING)
        camera_utils.reset_persp_shape_attributes()
        logging.disable(logging.NOTSET)
        result = maya_test_tools.get_attribute(obj_name=camera_shape, attr_name='focalLength')
        expected = 35
        self.assertEqual(expected, result)
