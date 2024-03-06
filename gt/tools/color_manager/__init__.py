"""
 GT Color Manager - A script for managing the color of many objects at the same time (outliner and other overrides)
 github.com/TrevisanGMW/gt-tools - 2020-11-13

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.1 - 2020-11-16
 Fixed an issue where the color containing rendering space data would be applied to the outliner.

 1.2 - 2020-11-23
 Fixed an issue with the persistent settings not being updated when importing the script.

 1.3 - 2020-12-03
 Fixed an issue where shape nodes wouldn't reset properly

 1.4 - 2021-05-11
 Made script compatible with Python 3 (Maya 2022+)

 1.5.0 - 2022-07-07
 Added logging
 PEP8 Cleanup
 Added patch to version
"""
# Tool Version
__version_tuple__ = (1, 5, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Color Manager.
    """
    from gt.tools.color_manager import color_manager
    color_manager.script_version = __version__
    color_manager.build_gui_color_manager()


if __name__ == "__main__":
    launch_tool()
