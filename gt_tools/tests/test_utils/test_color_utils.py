import os
import sys
import logging
import unittest
from collections import namedtuple

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_session_utils")
logger.setLevel(logging.DEBUG)

# Import Test Session Utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
#from tools.validation import validation_cleanup


# try:
#     import maya.cmds as cmds
#     import maya.standalone
#     import maya.mel as mel
#     import maya.OpenMaya as OpenMaya
# except Exception as e:
#     logger.debug(str(e))
#     logger.warning("Unable load maya cmds, maya standalone, mel or OpenMaya")


class Test_ColorUtils(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        maya.standalone.initialize()  # Start Maya Headless (mayapy.exe)

    def test_color_func(self):

        # Assert Results - Fail
        expected = ""
        result = ""
        self.assertEqual(result, expected)
