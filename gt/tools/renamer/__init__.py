"""
 GT Renamer - Script for Quickly Renaming Multiple Objects
 github.com/TrevisanGMW/gt-tools - 2020-06-25

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.1 - 2020-08-03
 Fixed little issue when auto adding suffix to object with multiple shapes.
 Added persistent settings.
 Fixed "all" option, so functions handles errors when trying to rename readOnly nodes.
 Added list of nodes to ignore.
 Fixed issue where auto prefix would sometimes raise an error when getting position using xform.

 1.2 - 2020-10-17
 Fixed an issue where the manual input for prefixes and suffixes wouldn't work.

 1.3 - 2020-10-23
 Added feedback to how many objects were renamed. (in view messages)
 Added persistent settings for selection type
 Added a check to ignore renaming when a new name is identical to current

 1.4 - 2020-11-15
 Changed the color and text for a few UI elements
 Removed a few unnecessary lines

 1.5 to 1.5.3 - 2021-05-08 to 2022-08-18
 Made script compatible with Python 3 (Maya 2022+)
 Added patch to version
 PEP8 Cleanup
 Removed unnecessary python version lines
 Added logger
 PEP8 Cleanup
 Updated "rename_and_letter"

 1.6.0 to 1.6.3 - 2022-08-19 to 2022-12-23
 Changed rename and number to allow the user to keep original names
 Added rename and letter
 Adjusted GUI
 Fixed an issue where shape nodes would cause the generator to advance for "Rename and Letter"
 Updated help menu
 Small PEP8 fixes
 Changed "Other Utilities" spacing
"""
# Tool Version
__version_tuple__ = (1, 6, 3)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Renamer.
    """
    from gt.tools.renamer import renamer
    renamer.script_version = __version__
    renamer.get_persistent_settings_renamer()
    renamer.build_gui_renamer()


if __name__ == "__main__":
    launch_tool()
