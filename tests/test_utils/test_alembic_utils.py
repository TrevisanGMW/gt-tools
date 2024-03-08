import os
import sys
import logging
import unittest

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
from gt.utils import alembic_utils
cmds = maya_test_tools.cmds


def import_alembic_test_file():
    """
    Import test alembic file from inside the .../data folder/<name>.abc
    Scene forces alembic plugin to be loaded when importing ("AbcExport", "AbcImport")
    Returns:
        str: Name of the test alembic node: "cube_move_z_AlembicNode"
    """
    maya_test_tools.import_data_file("cube_move_z.abc")
    alembic_nodes = cmds.ls(typ='AlembicNode') or []
    if alembic_nodes:
        return alembic_nodes[0]


class TestAlembicUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    def tearDown(self):
        maya_test_tools.force_new_scene()  # To make sure Abc can be unloaded
        maya_test_tools.unload_plugins(["AbcExport", "AbcImport", "AbcBullet"])  # Unload plugins after every test

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_load_alembic_plugin(self):
        alembic_utils.load_alembic_plugin(include_alembic_bullet=False)  # Default value
        result = []
        plugins_to_check = ["AbcExport", "AbcImport", "AbcBullet"]
        for plugin in plugins_to_check:
            result.append(maya_test_tools.is_plugin_loaded(plugin))
        expected = [True, True, False]
        self.assertEqual(expected, result)

    def test_load_alembic_plugin_bullet(self):
        alembic_utils.load_alembic_plugin(include_alembic_bullet=True)
        result = []
        plugins_to_check = ["AbcExport", "AbcImport", "AbcBullet"]
        for plugin in plugins_to_check:
            result.append(maya_test_tools.is_plugin_loaded(plugin))
        expected = [True, True, True]
        self.assertEqual(expected, result)

    def test_get_alembic_nodes(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = cmds.createNode("AlembicNode")
        result = alembic_utils.get_alembic_nodes()
        expected = [alembic_node]
        self.assertEqual(expected, result)

    def test_get_alembic_nodes_two(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node_a = cmds.createNode("AlembicNode")
        alembic_node_b = cmds.createNode("AlembicNode")
        result = alembic_utils.get_alembic_nodes()
        expected = [alembic_node_a, alembic_node_b]
        self.assertEqual(expected, result)

    def test_get_alembic_cycle_as_string(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = cmds.createNode("AlembicNode")  # Default 0 = Hold
        result = alembic_utils.get_alembic_cycle_as_string(alembic_node)  # Make sure alembic nodes can be created
        expected = 'Hold'
        self.assertEqual(expected, result)

    def test_get_alembic_cycle_as_string_reverse(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = cmds.createNode("AlembicNode")  # Default 0 = Hold
        cmds.setAttr(f"{alembic_node}.cycleType", 2)  # Change to 2 = Reverse
        result = alembic_utils.get_alembic_cycle_as_string(alembic_node)  # Make sure alembic nodes can be created
        expected = 'Reverse'
        self.assertEqual(expected, result)

    def test_alembic_node(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = cmds.createNode("AlembicNode")  # Default 0 = Hold
        cmds.setAttr(f"{alembic_node}.cycleType", 2)  # Change to 2 = Reverse
        result = alembic_utils.get_alembic_cycle_as_string(alembic_node)  # Make sure alembic nodes can be created
        expected = 'Reverse'
        self.assertEqual(expected, result)

    def test_alembic_node_class_name(self):
        alembic_node = import_alembic_test_file()
        result = alembic_utils.AlembicNode(alembic_node)
        expected = "cube_move_z_AlembicNode"
        self.assertEqual(expected, result.name)

    def test_alembic_node_class_time(self):
        alembic_node = import_alembic_test_file()
        result = alembic_utils.AlembicNode(alembic_node)
        expected = 1.0
        self.assertEqual(expected, result.time)

    def test_alembic_node_class_offset(self):
        alembic_node = import_alembic_test_file()
        result = alembic_utils.AlembicNode(alembic_node)
        expected = 0.0
        self.assertEqual(expected, result.offset)

    def test_alembic_node_class_start_time(self):
        alembic_node = import_alembic_test_file()
        result = alembic_utils.AlembicNode(alembic_node)
        expected = 1.0
        self.assertEqual(expected, result.start_time)

    def test_alembic_node_class_end_time(self):
        alembic_node = import_alembic_test_file()
        result = alembic_utils.AlembicNode(alembic_node)
        expected = 10.0
        self.assertEqual(expected, result.end_time)

    def test_alembic_node_class_cycle_type(self):
        alembic_node = import_alembic_test_file()
        result = alembic_utils.AlembicNode(alembic_node)
        expected = "Hold"
        self.assertEqual(expected, result.cycle_type)

    def test_alembic_node_class_mesh_cache(self):
        alembic_node = import_alembic_test_file()
        result = alembic_utils.AlembicNode(alembic_node)
        expected = cmds.getAttr(f"{alembic_node}.abc_File")
        self.assertEqual(expected, result.mesh_cache)

    def test_alembic_node_class_transform(self):
        alembic_node = import_alembic_test_file()
        maya_test_tools.set_current_time(10)
        alembic_object = alembic_utils.AlembicNode(alembic_node)
        expected = "position=(x=0.0, y=0.0, z=-10.0), " \
                   "rotation=(x=0.0, y=0.0, z=0.0), " \
                   "scale=(x=1.0, y=1.0, z=1.0)"
        result = str(alembic_object.transform)
        self.assertEqual(expected, result)
