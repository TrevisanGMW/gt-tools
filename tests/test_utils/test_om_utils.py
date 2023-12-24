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
from gt.utils import om_utils


class TestOpenMayaUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_mobject_from_path_valid_object_path(self):
        cube = maya_test_tools.create_poly_cube()
        mobject = om_utils.get_mobject_from_path(cube)
        self.assertIsNotNone(mobject)
        self.assertIsInstance(mobject, maya_test_tools.OpenMaya.MObject)

    def test_get_mobject_from_path_invalid_object_path(self):
        object_path = "invalid_path"
        mobject = om_utils.get_mobject_from_path(object_path)
        self.assertIsNone(mobject)

    def test_get_mobject_from_path_empty_object_path(self):
        object_path = ""
        mobject = om_utils.get_mobject_from_path(object_path)
        self.assertIsNone(mobject)
