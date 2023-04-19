import os
import sys
import logging
import unittest
import maya.cmds as cmds
from collections import namedtuple

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_session_utils")
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
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

    def tearDown(self):
        pass

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
