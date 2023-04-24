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


def _print_args_kwargs(*args, **kwargs):
    print(args)
    print(kwargs)


# MenuItem namedtuple - Used to store menuItem parameters before creating them
MenuItem = namedtuple("MenuItem", ['label', 'command', 'tooltip', 'icon', 'enable', 'parent', 'divider',
                                   'divider_label', 'sub_menu', 'tear_off', 'enable_command_repeat',
                                   'option_box', 'option_box_icon'])


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

    TODO:
     Write docstrings
     explain parent types (e.g. window with menuBar for MayaMenu parent)

    """
    def __init__(self, name, parent=""):
        """

        """
        self.initialized = False
        self.menu_path = None
        self.menu_name = name
        self.menu_items = []
        self.sub_menus = []
        self.menu_parent = parent

    def create_menu(self, *args):
        # Determine Parent
        menu_name = self.menu_name.replace(" ", '')
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

        # Populate Menu
        if not self.initialized:
            self.initialized = True
        for item in self.menu_items:
            params = self.get_item_parameters(item)
            print(params)
            cmds.menuItem(item.label, **params)

        return self.menu_path

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
            parent = self.menu_path
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
            parent = self.menu_path
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
            parent = self.menu_path
        elif parent is not None and parent not in self.sub_menus:
            logger.debug(f'Provided parent not in the list of sub-menus. '
                         f'Divider {label} will be added to the menu root menu "{self.menu_path}" instead.')
            parent = self.menu_path
        menu_item = MenuItem(label, command='', tooltip='', icon='', enable=True, parent=parent, divider=True,
                             divider_label=divider_label, sub_menu=False, tear_off=True, enable_command_repeat=False,
                             option_box=False, option_box_icon='')
        self.menu_items.append(menu_item)

    def determine_parent(self, parent, parent_to_root):
        """ TODO WIP """
        if parent_to_root:
            parent = self.menu_path
        elif parent is not None and parent not in self.sub_menus:
            logger.debug(f'Provided parent "{parent}" not in the list of sub-menus. '
                         f'Menu Item will be added to the menu root menu "{self.menu_path}" instead.')
            parent = self.menu_path
        return parent

    @staticmethod
    def get_item_parameters(item):
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
                "tearOff": item.tear_off,
            }

        # In case it has a parent
        if item.parent is not None:
            param_dict["parent"] = item.parent

        # In case it's an option box
        if item.option_box:
            param_dict["optionBox"] = item.option_box
            # param_dict["optionBoxIcon"] = item.option_box_icon

        return param_dict


def _open_renamer(*args):
    print("Open Renamer")
    #-c ("python(\"gt_tools.execute_script('gt_renamer', 'build_gui_renamer')\");")


def load_menu():
    # window_test = cmds.window(title="Simple Window", widthHeight=(300, 200), menuBar=True)
    # cmds.columnLayout()
    # cmds.text(label="Hello, Maya!")
    # cmds.showWindow(window_test)
    #
    # menu = MayaMenu("MyMenu", parent=window_test)
    menu = MayaMenu("GT Tools WIP")
    menu.add_sub_menu("Tools", icon="toolSettings.png")
    menu.add_menu_item(label='Renamer', command=_print_args_kwargs,
                       tooltip='Script for renaming multiple objects."', icon='renamePreset.png')
    # menu.add_divider()
    # menu.add_sub_menu("SubMenuRooTwo", icon='out_layeredTexture.png')
    # menu.add_sub_menu("SubTwo", parent="SubMenuRootOne")
    # menu.add_menu_item('Tool Two', _print_args_kwargs,
    #                    'Open Texture Helper UI', 'out_layeredTexture.png')
    # menu.add_menu_item('Tool With Options Box', _print_args_kwargs,
    #                    'Tool With Options Box', 'out_layeredTexture.png', parent='MyMenu', option_box=True,
    #                    option_box_command=_print_args_kwargs)
    menu_path = menu.create_menu()

    # menu.add_divider()
    # menu.add_menu_item('Texture Helper', _open_texture_helper,  # Previously Texture Loader
    #                     'Open Texture Helper UI', 'out_layeredTexture.png')

    # cmds.menu(_menu_path, edit=True, postMenuCommand=_menu.create_menu)  # Re-create/update menu when showing it
    # return _menu_path


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    load_menu()
    # pprint(out)
