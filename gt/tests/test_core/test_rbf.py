from unittest.mock import patch
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
import gt.core.rbf as core_rbf

cmds = maya_test_tools.cmds


def import_rbf_cube_test_file():
    """
    Import test cube rbf retarget file from the related .../data folder/<name>.ma
    """
    maya_test_tools.import_data_file("cube_rbf_retarget.ma")


class TestRbfCore(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    def tearDown(self):
        cmds.file(new=True, force=True)

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_rbf_mesh_retarget(self):
        import_rbf_cube_test_file()
        result = core_rbf.retarget_mesh("cloth_mesh", "source_mesh", "target_mesh")
        expected = True
        self.assertEqual(expected, result)
