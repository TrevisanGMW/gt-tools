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
from gt.utils import surface_utils


class TestSurfaceUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_is_surface_periodic_false(self):
        sur = maya_test_tools.cmds.nurbsPlane(name="mocked_sur", constructionHistory=False)[0]
        sur_shape = maya_test_tools.cmds.listRelatives(sur, shapes=True)[0]
        result = surface_utils.is_surface_periodic(surface_shape=sur_shape)
        expected = False

        self.assertEqual(expected, result)

    def test_is_surface_periodic_true(self):
        sur = maya_test_tools.cmds.sphere(name="mocked_sur", constructionHistory=False)[0]
        sur_shape = maya_test_tools.cmds.listRelatives(sur, shapes=True)[0]
        result = surface_utils.is_surface_periodic(surface_shape=sur_shape)
        expected = True

        self.assertEqual(expected, result)
