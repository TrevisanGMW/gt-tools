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
import gt.tools.auto_rigger.templates.template_biped as template_biped
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
from gt.tests import maya_test_tools

cmds = maya_test_tools.cmds


def get_modified_template_file():
    """
    Gets the path to a modified version of the biped template (used for tests)
    Returns:
        str: A path to the test JSON file that can be read as a RigProject dictionary.
    """
    return maya_test_tools.get_data_file_path("biped_template_average.json")


class TestTemplateBiped(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_template_creation(self):
        biped_template = template_biped.create_template_biped()
        result = isinstance(biped_template, tools_rig_frm.RigProject)
        expected = True
        self.assertEqual(expected, result)
