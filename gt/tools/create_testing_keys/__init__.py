"""
 GT Create Testing Keys - Script for creating testing keyframes.
 It creates a sequence of keyframes on the selected objects using the provided offset.
 Helpful for when testing controls or painting skin weights.
 github.com/TrevisanGMW/gt-tools -  2021-01-28

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1.0 - 2021-01-28
 Initial Release

 1.1 - 2021-01-29
 Changed way that attributes are updated to account for long hierarchies (changed to setAttr instead of move/xform)
 Added a missing undoInfo(openChunk) function that would break the undo queue
 Updated a few incorrect comments

 1.2 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.3 to 1.3.1 - 2021-06-23 to 2022-07-21
 Added option to use world space to get predictable movement with joints
 Added patch to version
 PEP8 Cleanup
 Added logger
"""
# Tool Version
__version_tuple__ = (1, 3, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Create Testing Keys.
    """
    from gt.tools.create_testing_keys import create_testing_keys
    create_testing_keys.script_version = __version__
    create_testing_keys.build_gui_create_testing_keys()


if __name__ == "__main__":
    launch_tool()
