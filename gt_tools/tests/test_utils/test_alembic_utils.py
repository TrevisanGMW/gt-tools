import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("test_alembic_utils")
logger.setLevel(logging.DEBUG)

# Import Test Alembic Utilities
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils import alembic_utils

try:
    import maya.cmds as cmds
    import maya.standalone
    import maya.mel as mel
    import maya.OpenMaya as OpenMaya
except Exception as e:
    logger.debug(str(e))
    logger.warning("Unable load maya cmds, maya standalone, mel or OpenMaya")


class Test_SessionUtils(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        maya.standalone.initialize()  # Start Maya Headless (mayapy.exe)

    def test_load_alembic_plugin(self):
        alembic_utils.load_alembic_plugin()
        result = []
        plugins_to_check = ["AbcExport", "AbcImport", "AbcBullet"]
        for plugin in plugins_to_check:
            result.append(cmds.pluginInfo(plugin, q=True, loaded=True))
        expected = [True, True, False]
        self.assertEqual(result, expected)

    def test_load_alembic_plugin_bullet(self):
        alembic_utils.load_alembic_plugin(include_alembic_bullet=True)
        result = []
        plugins_to_check = ["AbcExport", "AbcImport", "AbcBullet"]
        for plugin in plugins_to_check:
            result.append(cmds.pluginInfo(plugin, q=True, loaded=True))
        expected = [True, True, True]
        self.assertEqual(result, expected)

