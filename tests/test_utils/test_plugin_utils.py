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
from gt.utils import plugin_utils


class TestPluginUtils(unittest.TestCase):
    def setUp(self):
        maya_test_tools.force_new_scene()

    def tearDown(self):
        maya_test_tools.force_new_scene()

    @classmethod
    def setUpClass(cls):
        maya_test_tools.import_maya_standalone(initialize=True)  # Start Maya Headless (mayapy.exe)

    def test_load_plugin(self):
        plugin = "objExport"
        maya_test_tools.unload_plugins([plugin])  # Make sure it's off
        self.assertFalse(maya_test_tools.is_plugin_loaded(plugin))
        result = plugin_utils.load_plugin(plugin)
        expected = True
        self.assertEqual(expected, result)
        self.assertTrue(maya_test_tools.is_plugin_loaded(plugin))

    def test_load_plugin_invalid(self):
        plugin = "mocked_non_existent_plugin"
        result = plugin_utils.load_plugin(plugin)
        expected = False
        self.assertEqual(expected, result)

    def test_load_plugins(self):
        plugins = ["objExport", "Unfold3D"]
        maya_test_tools.unload_plugins(plugins)  # Make sure it's off
        for plugin in plugins:
            self.assertFalse(maya_test_tools.is_plugin_loaded(plugin))
        result = plugin_utils.load_plugins(plugins)
        expected = [('objExport', True), ('Unfold3D', True)]
        self.assertEqual(expected, result)
        for plugin in plugins:
            self.assertTrue(maya_test_tools.is_plugin_loaded(plugin))

    def test_load_plugins_invalid(self):
        plugins = ["mocked_non_existent_plugin_one", "mocked_non_existent_plugin_two"]
        result = plugin_utils.load_plugins(plugins)
        expected = [('mocked_non_existent_plugin_one', False), ('mocked_non_existent_plugin_two', False)]
        self.assertEqual(expected, result)

    def test_unload_plugin(self):
        plugin = "objExport"
        maya_test_tools.load_plugins([plugin])  # Make sure it's on
        self.assertTrue(maya_test_tools.is_plugin_loaded(plugin))
        result = plugin_utils.unload_plugin(plugin)
        expected = True
        self.assertEqual(expected, result)
        self.assertFalse(maya_test_tools.is_plugin_loaded(plugin))

    def test_unload_plugin_invalid(self):
        plugin = "mocked_non_existent_plugin"
        result = plugin_utils.unload_plugin(plugin)
        # not found, so consider it unloaded
        expected = True
        self.assertEqual(expected, result)

    def test_unload_plugins(self):
        plugins = ["objExport", "Unfold3D"]
        maya_test_tools.load_plugins(plugins)  # Make sure it's on
        for plugin in plugins:
            self.assertTrue(maya_test_tools.is_plugin_loaded(plugin))
        result = plugin_utils.unload_plugins(plugins)
        expected = [('objExport', True), ('Unfold3D', True)]
        self.assertEqual(expected, result)
        for plugin in plugins:
            self.assertFalse(maya_test_tools.is_plugin_loaded(plugin))

    def test_unload_plugins_invalid(self):
        plugins = ["mocked_non_existent_plugin_one", "mocked_non_existent_plugin_two"]
        result = plugin_utils.unload_plugins(plugins)
        # not found, so consider it unloaded
        expected = [('mocked_non_existent_plugin_one', True), ('mocked_non_existent_plugin_two', True)]
        self.assertEqual(expected, result)
