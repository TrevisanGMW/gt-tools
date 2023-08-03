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
from gt.utils import anim_utils


def import_anim_test_file():
    """
    Import test alembic file from inside the .../data folder/<name>.abc
    Scene forces alembic plugin to be loaded when importing ("AbcExport", "AbcImport")
    """
    maya_test_tools.import_data_file("cube_animated.ma")


class TestAnimUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_get_time_keyframes(self):
        import_anim_test_file()
        result = anim_utils.get_time_keyframes()
        expected = ['pCube1_rotateY', 'pCube1_translateZ', 'pCube1_scaleY']
        self.assertEqual(expected, result)

    def test_get_double_keyframes(self):
        import_anim_test_file()
        result = anim_utils.get_double_keyframes()
        expected = ['pCube2_translateX', 'pCube2_rotateY', 'pCube2_scaleY']
        self.assertEqual(expected, result)

    def test_delete_time_keyframes(self):
        import_anim_test_file()
        result = anim_utils.delete_time_keyframes()
        expected = 3
        self.assertEqual(expected, result)

    def test_delete_double_keyframes(self):
        import_anim_test_file()
        result = anim_utils.delete_double_keyframes()
        expected = 3
        self.assertEqual(expected, result)
