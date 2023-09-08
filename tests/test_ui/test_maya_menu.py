from PySide2.QtWidgets import QApplication
import unittest
import logging
import sys
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Import Tested Script
test_utils_dir = os.path.dirname(__file__)
tests_dir = os.path.dirname(test_utils_dir)
package_root_dir = os.path.dirname(tests_dir)
for to_append in [package_root_dir, tests_dir]:
    if to_append not in sys.path:
        sys.path.append(to_append)
from gt.ui.maya_menu import MayaMenu, MenuItem
from tests import maya_test_tools


class TestMayaMenu(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = QApplication.instance()
        if not app:
            cls.app = QApplication(sys.argv)

    def setUp(self):
        # Create a MayaMenu object for testing
        self.menu = MayaMenu(name="TestMenu", parent=None)
        maya_test_tools.import_maya_standalone(initialize=True)

    def tearDown(self):
        # Delete the menu after each test
        self.menu.delete_menu()

    def test_create_menu(self):
        # Test if the menu is created successfully
        self.menu.create_menu()
        self.assertTrue(self.menu.initialized)

    def test_add_menu_item(self):
        # Add a menu item and check if it exists in the menu items list
        label = "TestMenuItem"
        self.menu.add_menu_item(label)
        self.assertTrue(any(item.label == label for item in self.menu.menu_items))

    def test_add_sub_menu(self):
        # Add a sub-menu and check if it exists in the sub_menus list
        label = "TestSubMenu"
        self.menu.add_sub_menu(label)
        self.assertTrue(label in self.menu.sub_menus)

    def test_add_divider(self):
        # Add a divider and check if it exists in the menu items list
        label = "TestDivider"
        self.menu.add_divider(label)
        self.assertTrue(any(item.label == label for item in self.menu.menu_items))

    def test_get_item_parameters(self):
        # Test the get_item_parameters method
        item = MenuItem(label="label",
                        command='command',
                        tooltip='tooltip',
                        icon='icon',
                        enable=True,
                        parent="parent",
                        divider=True,
                        divider_label="divider_label",
                        sub_menu=False,
                        tear_off=False,
                        enable_command_repeat=False,
                        option_box=False,
                        option_box_icon='')
        params = self.menu.get_item_parameters(item)
        self.assertEqual(params["label"], "label")
        self.assertEqual(params["command"], "command")
        self.assertEqual(params["annotation"], "tooltip")
        self.assertEqual(params["image"], "icon")
        self.assertEqual(params["enable"], True)
        self.assertEqual(params["parent"], "parent")
        self.assertEqual(params["divider"], True)
        self.assertEqual(params["dividerLabel"], "divider_label")
        self.assertEqual(params["subMenu"], False)
        self.assertEqual(params.get("tearOff"), None)
        self.assertEqual(params["enableCommandRepeat"], False)
        self.assertEqual(params.get("optionBox"), None)
