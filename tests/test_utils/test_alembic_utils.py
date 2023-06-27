import os
import sys
import logging
import unittest

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Test Alembic Utilities
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from utils import alembic_utils

try:
    import maya.cmds as cmds
    import maya.standalone
    import maya.mel as mel
    import maya.OpenMaya as OpenMaya
except Exception as e:
    logger.debug(str(e))
    logger.warning("Unable load maya cmds, maya standalone, mel or OpenMaya")


class TestSessionUtils(unittest.TestCase):
    def setUp(self):
        cmds.file(new=True, force=True)

    @classmethod
    def setUpClass(cls):
        maya.standalone.initialize()  # Start Maya Headless (mayapy.exe)

    def test_load_alembic_plugin(self):
        alembic_utils.load_alembic_plugin(include_alembic_bullet=False)  # Default value
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

    def test_get_alembic_nodes(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = cmds.createNode("AlembicNode")
        result = alembic_utils.get_alembic_nodes()
        expected = [alembic_node]
        self.assertEqual(result, expected)

    def test_get_alembic_nodes_two(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node_a = cmds.createNode("AlembicNode")
        alembic_node_b = cmds.createNode("AlembicNode")
        result = alembic_utils.get_alembic_nodes()
        expected = [alembic_node_a, alembic_node_b]
        self.assertEqual(result, expected)

    def test_get_alembic_cycle_as_string(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = cmds.createNode("AlembicNode")  # Default 0 = Hold
        result = alembic_utils.get_alembic_cycle_as_string(alembic_node)  # Make sure alembic nodes can be created
        expected = 'Hold'
        self.assertEqual(result, expected)

    def test_get_alembic_cycle_as_string_reverse(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = cmds.createNode("AlembicNode")  # Default 0 = Hold
        cmds.setAttr(f'{alembic_node}.cycleType', 2)  # Change to 2 = Reverse
        result = alembic_utils.get_alembic_cycle_as_string(alembic_node)  # Make sure alembic nodes can be created
        expected = 'Reverse'
        self.assertEqual(result, expected)

    def test_alembic_node(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = cmds.createNode("AlembicNode")  # Default 0 = Hold
        cmds.setAttr(f'{alembic_node}.cycleType', 2)  # Change to 2 = Reverse
        result = alembic_utils.get_alembic_cycle_as_string(alembic_node)  # Make sure alembic nodes can be created
        expected = 'Reverse'
        self.assertEqual(result, expected)
