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
from gt.utils import playblast_utils


class TestPlayblastUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()
        self.temp_dir = maya_test_tools.generate_test_temp_dir()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def tearDown(self):
        maya_test_tools.delete_test_temp_dir()

    def test_render_viewport_snapshot(self):
        result = playblast_utils.render_viewport_snapshot(file_name="mocked_file_name", target_dir=self.temp_dir)
        expected = os.path.join(self.temp_dir, "mocked_file_name.jpg")
        self.assertEqual(expected, result)
