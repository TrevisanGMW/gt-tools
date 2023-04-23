"""
Maya Menu UI - Utilities for creating a maya menu
"""
from collections import namedtuple
from functools import partial
import importlib
import logging
import inspect
import sys
import json
import os

# # Paths to Append
# _this_folder = os.path.dirname(__file__)
# _tools_folder = os.path.dirname(_this_folder)
# _pipe_folder = os.path.dirname(_tools_folder)
#
# for to_append in [_this_folder, _tools_folder, _pipe_folder]:
#     if to_append not in sys.path:
#         sys.path.append(to_append)

logging.basicConfig()
logger = logging.getLogger("maya_menu")


try:
    import maya.cmds as cmds
    import maya.mel as mel
    import maya.OpenMaya as OpenMaya
except Exception as e:
    logger.warning("Unable to load maya cmds, mel or OpenMaya")

    # cmds.menu(_menu_path, edit=True, postMenuCommand=_menu.create_menu)  # Re-create/update menu when showing it
    # return _menu_path


def _open_transfer_uvs(*args, **kwargs):
    from tools import transfer_uvs
    #transfer_uvs.


# MenuItem namedtuple - Used to store menuItem parameters before creating them
MenuItem = namedtuple("MenuItem", ['label', 'command', 'tooltip', 'icon', 'enable', 'parent',
                                   'divider', 'divider_label', 'sub_menu', 'enable_command_repeat',
                                   'option_box', 'option_box_icon'])


class MayaMenu(object):
    def __init__(self, name, parent=""):
        self.initialized = False
        self.menu_path = None
        self.menu_name = name
        self.menu_items = []
        self.sub_menus = []
        self.menu_parent = parent

    def create_menu(self, *args):
        # Determine Parent
        menu_parent = self.menu_parent
        if menu_parent == "":  # No parent provided, parent assumed to be the main Maya window
            try:
                menu_parent = mel.eval("$retvalue = $gMainWindow;")  # Get global variable for main Maya window
            except Exception as e:
                cmds.warning("Unable to find Maya Window. Menu creation was ignored.")
                return ""

        # Delete if already in Maya - Singleton
        if cmds.menu(self.menu_name, exists=True):
            cmds.menu(self.menu_name, e=True, deleteAllItems=True)
            cmds.deleteUI(self.menu_name)

        # Create Menu
        self.menu_path = cmds.menu(self.menu_name, label=self.menu_name, parent=menu_parent, tearOff=True)

        # Populate Menu
        if not self.initialized:
            self.initialized = True
        for item in self.menu_items:
            params = self.get_item_parameters(item)
            print(params)
            out = cmds.menuItem(item.label, **params)
            # cmds.setParent(item_path, menu=True)

    def add_menu_item(self, label,
                      command=None,
                      tooltip='',
                      icon='',
                      enable=True,
                      parent=None,
                      enable_command_repeat=True,
                      option_box=False,
                      option_box_command='',
                      option_box_icon=''):
        # Determine Parent
        if parent is not None and parent not in self.sub_menus:
            logger.debug(f'Provided parent not in the list of sub-menus. '
                         f'Parenting for the Menu item "{label}" will be ignored.')
            parent = None
        # Create MenuItem - While ignoring irrelevant parameters
        menu_item = MenuItem(label, command=command, tooltip=tooltip, icon=icon, enable=enable, parent=parent,
                             divider=False, divider_label='', sub_menu=False,
                             enable_command_repeat=enable_command_repeat, option_box=False,
                             option_box_icon='')
        self.menu_items.append(menu_item)
        if option_box:
            label_btn = label + " Options"
            menu_item = MenuItem(label=label_btn, command=option_box_command, tooltip=tooltip, icon=icon, enable=enable,
                                 parent=label, divider=False, divider_label='', sub_menu=False,
                                 enable_command_repeat=enable_command_repeat, option_box=True,
                                 option_box_icon=option_box_icon)

    def add_sub_menu(self, label,
                     enable=True,
                     icon='',
                     parent=None):
        # Determine Parent
        if parent is None:
            parent = self.menu_name
        elif parent not in self.sub_menus:
            logger.debug(f'Provided parent not in the list of sub-menus. '
                         f'Menu item {label} will be added to the menu root menu "{self.menu_name}" instead.')
            parent = self.menu_name
        # Create MenuItem - While ignoring irrelevant parameters
        menu_item = MenuItem(label, command='', tooltip='', icon=icon, enable=enable, parent=parent, divider=False,
                             divider_label='', sub_menu=True, enable_command_repeat=False, option_box=False,
                             option_box_icon='')
        self.menu_items.append(menu_item)
        self.sub_menus.append(label)

    def add_divider(self, label=None, parent=None, divider_label=''):
        if parent is None:
            parent = self.menu_name
        elif parent not in self.sub_menus:
            logger.debug(f'Provided parent not in the list of sub-menus. '
                         f'Menu item {label} will be added to the menu root menu "{self.menu_name}" instead.')
            parent = self.menu_name
        menu_item = MenuItem(label, command='', tooltip='', icon='', enable=True, parent=parent, divider=True,
                             divider_label=divider_label, sub_menu=False, enable_command_repeat=False,
                             option_box=False, option_box_icon='')
        self.menu_items.append(menu_item)

    def get_item_parameters(self, item):
        # Build default menu item param list
        param_dict = {
            "label": item.label,
            "command": item.command,
            "annotation": item.tooltip,
            "image": item.icon,
            "enable": item.enable,
            "divider": item.divider,
            "dividerLabel": item.divider_label,
            "subMenu": item.sub_menu,
            "enableCommandRepeat": item.enable_command_repeat,
        }

        # In case it's a sub-menu, replace with simplified version
        if item.sub_menu:
            param_dict = {
                "label": item.label,
                "image": item.icon,
                "enable": item.enable,
                "subMenu": item.sub_menu,
            }

        # In case it has a parent
        if item.parent is not None:
            param_dict["parent"] = item.parent

        # In case it's an option box
        if item.option_box:
            param_dict["optionBox"] = item.option_box
            param_dict["optionBoxIcon"] = item.option_box_icon

        return param_dict


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    # load_menu()
    # _menu_parent = mel.eval("$retvalue = $gMainWindow;")  # Get the mel global variable value for main window.
    # _menu_name = "TestMenu"
    # name = cmds.menu(
    #     "TestMenu",
    #     label=_menu_name,
    #     parent=_menu_parent,
    #     tearOff=True
    # )
    # if cmds.menu("TestMenu", exists=True):
    #     cmds.menu("TestMenu", e=True, deleteAllItems=True)
    #     cmds.deleteUI("TestMenu")
    # print(cmds.menu("YTAvatarsMenu", exists=True))

    # name = "MyMenu"
    #
    # # Check if the menu already exists, and delete it if it does
    # if cmds.menu(name, exists=True):
    #     cmds.deleteUI(name)
    #
    # # Create a new menu
    # cmds.menu(name, label="My Menu")
    #
    # # Add some items to the menu
    # cmds.menuItem(label="Item 1")
    # cmds.menuItem(label="Item 2")

    #
    #

    # _menu_name = "TestMenu"
    # name = cmds.menu(
    #     "TestMenu",
    #     label=_menu_name,
    #     parent=_menu_parent,
    #     tearOff=True
    # )
    #
    menu = MayaMenu("MyMenu")
    menu.add_sub_menu("SubMenuRootOne")
    menu.add_menu_item('Tool One', _open_texture_helper,  # Previously Texture Loader
                       'Open Texture Helper UI', 'out_layeredTexture.png')
    menu.add_divider()
    menu.add_sub_menu("SubMenuRooTwo")
    menu.add_sub_menu("SubTwo", parent="SubMenuRootOne")
    menu.add_menu_item('Tool Two', _open_texture_helper,  # Previously Texture Loader
                       'Open Texture Helper UI', 'out_layeredTexture.png')
    menu.add_menu_item('Tool A', _open_texture_helper,  # Previously Texture Loader
                       'Open Texture Helper UI', 'out_layeredTexture.png', parent='MyMenu', option_box=True, option_box_command='')
    # menu.add_divider()
    # menu.add_menu_item('Texture Helper', _open_texture_helper,  # Previously Texture Loader
    #                     'Open Texture Helper UI', 'out_layeredTexture.png')
    menu.create_menu()
    # cmds.menuItem(label="test", optionBox=True, optionBoxIcon="blendShape.png")

    print(menu)
    # pprint(out)
