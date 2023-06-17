"""
Maya Menu UI - Utilities for creating a maya menu
"""
from collections import namedtuple
import logging


logging.basicConfig()
logger = logging.getLogger("maya_menu")

try:
    import maya.cmds as cmds
    import maya.mel as mel
    import maya.OpenMaya as OpenMaya
except Exception as e:
    logger.warning("Unable to load maya cmds, mel or OpenMaya")


# MenuItem namedtuple - Used to store menuItem parameters before creating them
MenuItem = namedtuple("MenuItem", ['label', 'command', 'tooltip', 'icon', 'enable', 'parent', 'divider',
                                   'divider_label', 'sub_menu', 'tear_off', 'enable_command_repeat',
                                   'option_box', 'option_box_icon'])
MENU_ROOT_PLACEHOLDER = "TempMayaMenuPlaceholderRoot"


class MayaMenu:
    """
    Helper class used to create a Maya drop-down menu
    Attributes:
        initialized (bool): If the menu was created (initialized)
        menu_path (string): Output received from an initialized menu (it's path)
        menu_name (string): Menu name (a.k.a. Label)
        menu_items (list): A list of menu items to be used when building the menu
        sub_menus (list): A list of sub_menus added to the menu
        menu_parent (string): Parent of the menu (e.g. Maya or a window)

    Methods:
        create_menu(): Creates the menu and populates it with objects that were previously added to it (aka initialize)
        add_menu_item():
    """
    def __init__(self, name, parent=""):
        """
        Initializes Maya Menu Object
        Parameters:
            name (str): Name of the menu. This also become its label.
            parent (str, optional): Menu parent. It could be a maya window for example.
                                    Optional: If not provided, Maya is used instead.
        """
        self.initialized = False
        self.menu_path = None
        self.menu_name = name
        self.menu_items = []
        self.sub_menus = []
        self.menu_parent = parent

    def create_menu(self, *args):
        """
        Creates menu. Deletes existing menu with the same name and re-creates it using settings found in the object.
        Usually called after populating it with "add" functions.
        """
        # Determine Parent
        menu_name = self.menu_name.replace(" ", "")
        menu_parent = self.menu_parent
        if menu_parent == "":  # No parent provided, parent assumed to be the main Maya window
            try:
                menu_parent = mel.eval("$retvalue = $gMainWindow;")  # Get global variable for main Maya window
            except Exception as e:
                cmds.warning("Unable to find Maya Window. Menu creation was ignored.")
                return ""

        # Delete if already in Maya - Singleton
        if cmds.menu(menu_name, exists=True):
            cmds.menu(menu_name, e=True, deleteAllItems=True)
            cmds.deleteUI(menu_name)

        # Create Menu
        self.menu_path = cmds.menu(menu_name, label=self.menu_name, parent=menu_parent, tearOff=True)

        # Set Status
        if not self.initialized:
            self.initialized = True
        # Populate Menu
        for item in self.menu_items:
            params = self.get_item_parameters(item)
            # Populate root values
            if params.get('parent') is not None and params.get('parent') == MENU_ROOT_PLACEHOLDER:
                params['parent'] = self.menu_path
            cmds.menuItem(item.label, **params)

    def add_menu_item(self, label,
                      command=None,
                      tooltip='',
                      icon='',
                      enable=True,
                      parent=None,
                      enable_command_repeat=True,
                      option_box=False,
                      option_box_command=None,
                      option_box_icon='',
                      parent_to_root=False):
        # Determine Parent
        if parent_to_root:
            parent = MENU_ROOT_PLACEHOLDER
        elif parent is not None and parent not in self.sub_menus:
            logger.debug(f'Provided parent not in the list of sub-menus. '
                         f'Parenting for the Menu item "{label}" will be ignored.')
            parent = None
        # Create MenuItem - While ignoring irrelevant parameters
        menu_item = MenuItem(label, command=command, tooltip=tooltip, icon=icon, enable=enable, parent=parent,
                             divider=False, divider_label='', sub_menu=False, tear_off=True,
                             enable_command_repeat=enable_command_repeat, option_box=False,
                             option_box_icon='')
        self.menu_items.append(menu_item)
        if option_box:
            label_btn = label + " Options"
            menu_item = MenuItem(label=label_btn, command=option_box_command, tooltip=tooltip, icon=icon, enable=enable,
                                 parent=None, divider=False, divider_label='', sub_menu=False, tear_off=True,
                                 enable_command_repeat=enable_command_repeat, option_box=True,
                                 option_box_icon=option_box_icon)
            self.menu_items.append(menu_item)

    def add_sub_menu(self, label,
                     enable=True,
                     icon='',
                     tear_off=True,
                     parent=None,
                     parent_to_root=True):
        # Determine Parent
        if parent_to_root:
            parent = MENU_ROOT_PLACEHOLDER
        elif parent is not None and parent not in self.sub_menus:
            logger.debug(f'Provided parent not in the list of sub-menus. '
                         f'Menu item {label} will be added to the menu root menu "{self.menu_path}" instead.')
            parent = self.menu_path
        # Create MenuItem - While ignoring irrelevant parameters
        menu_item = MenuItem(label, command='', tooltip='', icon=icon, enable=enable, parent=parent, divider=False,
                             divider_label='', sub_menu=True, tear_off=tear_off, enable_command_repeat=False,
                             option_box=False, option_box_icon='')
        self.menu_items.append(menu_item)
        self.sub_menus.append(label)

    def add_divider(self, label=None, parent=None, divider_label='', parent_to_root=False):
        # Determine Parent
        if parent_to_root:
            parent = MENU_ROOT_PLACEHOLDER
        elif parent is not None and parent not in self.sub_menus:
            logger.debug(f'Provided parent not in the list of sub-menus. '
                         f'Divider {label} will be added to the menu root menu "{self.menu_path}" instead.')
            parent = self.menu_path
        menu_item = MenuItem(label, command='', tooltip='', icon='', enable=True, parent=parent, divider=True,
                             divider_label=divider_label, sub_menu=False, tear_off=True, enable_command_repeat=False,
                             option_box=False, option_box_icon='')
        self.menu_items.append(menu_item)

    @staticmethod
    def get_item_parameters(item):
        # Build default menu item param list
        param_dict = {
            "label": item.label,
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
                "tearOff": item.tear_off,
            }

        # In case it has a parent
        if item.parent is not None:
            param_dict["parent"] = item.parent

        # In case it has a command
        if item.command is not None:
            param_dict["command"] = item.command

        # In case it's an option box
        if item.option_box:
            param_dict["optionBox"] = item.option_box
            # param_dict["optionBoxIcon"] = item.option_box_icon

        return param_dict


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    print("Loading menu...")
    # load_menu()
    print(out)
