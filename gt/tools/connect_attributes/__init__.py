"""
 GT Connect Attributes - Script for automatically connecting or disconnecting multiple attributes.
 github.com/TrevisanGMW/gt-tools - 2020-02-04

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.2 - 2020-02-18
 Added force connection and some checks.

 1.3 - 2020-06-07
 Updated naming convention to make it clearer. (PEP8)
 Fixed random window widthHeight issue.

 1.4 - 2020-06-17
 Added window icon
 Added help menu
 Changed GUI
 Attribute Listing now exported to txt file instead of script editor

 1.5 - 2020-11-15
 Tweaked the title color and text
 Tweaked a few colors

 1.6 - 2021-05-11
 Made script compatible with Python 3 (Maya 2022+)

 1.7 - 2021-08-22
 Fixed issue where default state for "use selection for source" would cause script to crash

 1.8.0 to 1.8.1 - 2022-07-07 to 2022-07-21
 Added patch to version
 PEP8 cleanup
"""
# Tool Version
__version_tuple__ = (1, 8, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Connect Attributes.
    """
    from gt.tools.connect_attributes import connect_attributes
    connect_attributes.script_version = __version__
    connect_attributes.build_gui_connect_attributes()


if __name__ == "__main__":
    launch_tool()
