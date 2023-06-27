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
from utils import alembic_utils


class TestSessionUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

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
        self.assertEqual(result, expected)

    def test_load_alembic_plugin_bullet(self):
        alembic_utils.load_alembic_plugin(include_alembic_bullet=True)
        result = []
        plugins_to_check = ["AbcExport", "AbcImport", "AbcBullet"]
        for plugin in plugins_to_check:
            result.append(maya_test_tools.is_plugin_loaded(plugin))
        expected = [True, True, True]
        self.assertEqual(result, expected)

    def test_get_alembic_nodes(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = maya_test_tools.create_node(node_type="AlembicNode")
        result = alembic_utils.get_alembic_nodes()
        expected = [alembic_node]
        self.assertEqual(result, expected)

    def test_get_alembic_nodes_two(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node_a = maya_test_tools.create_node(node_type="AlembicNode")
        alembic_node_b = maya_test_tools.create_node(node_type="AlembicNode")
        result = alembic_utils.get_alembic_nodes()
        expected = [alembic_node_a, alembic_node_b]
        self.assertEqual(result, expected)

    def test_get_alembic_cycle_as_string(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = maya_test_tools.create_node("AlembicNode")  # Default 0 = Hold
        result = alembic_utils.get_alembic_cycle_as_string(alembic_node)  # Make sure alembic nodes can be created
        expected = 'Hold'
        self.assertEqual(result, expected)

    def test_get_alembic_cycle_as_string_reverse(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = maya_test_tools.create_node(node_type="AlembicNode")  # Default 0 = Hold
        maya_test_tools.set_attribute(obj_name=alembic_node, attr_name="cycleType", value=2)  # Change to 2 = Reverse
        result = alembic_utils.get_alembic_cycle_as_string(alembic_node)  # Make sure alembic nodes can be created
        expected = 'Reverse'
        self.assertEqual(result, expected)

    def test_alembic_node(self):
        alembic_utils.load_alembic_plugin()  # Make sure alembic nodes can be created
        alembic_node = maya_test_tools.create_node(node_type="AlembicNode")  # Default 0 = Hold
        maya_test_tools.set_attribute(obj_name=alembic_node, attr_name="cycleType", value=2)  # Change to 2 = Reverse
        result = alembic_utils.get_alembic_cycle_as_string(alembic_node)  # Make sure alembic nodes can be created
        expected = 'Reverse'
        self.assertEqual(result, expected)
