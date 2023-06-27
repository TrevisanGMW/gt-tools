import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities and Maya Test Tools
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from utils import color_utils

try:
    import maya.cmds as cmds
    import maya.standalone
    import maya.mel as mel
    import maya.OpenMaya as OpenMaya
except Exception as e:
    logger.debug(str(e))
    logger.warning("Unable load maya cmds, maya standalone, mel or OpenMaya")


class TestColorUtils(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    @classmethod
    def setUpClass(cls):
        maya.standalone.initialize()  # Start Maya Headless (mayapy.exe)

    def test_set_color_override_viewport(self):
        test_obj = 'test_cube'
        cmds.polyCube(name=test_obj)

        expected = (0, 0.5, 1)
        result = color_utils.set_color_override_viewport(test_obj, rgb_color=expected)
        self.assertEqual(expected, result)

    def test_set_color_override_outliner(self):
        test_obj = 'test_cube'
        cmds.polyCube(name=test_obj)

        expected = (0, 0.5, 1)
        result = color_utils.set_color_override_outliner(test_obj, rgb_color=expected)
        self.assertEqual(expected, result)
