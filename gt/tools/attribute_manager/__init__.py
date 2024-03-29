"""
 GT Attribute Manager - Script for quickly creating, deleting or updating user defined attributes.
 github.com/TrevisanGMW/gt-tools - 2022-08-06

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 0.0.1 - 2022-08-06
 Created script file
 Added description

 0.0.2 - 2022-08-07
 Added logger
 Added parameters to add_attributes + debug lines

Script would work similar to the "Add attribute" function, but it would retain the parameters and allow for multiple
variables (separated by commas)

TODO:
    GUI Plan:
    Attributes (short)
    NiceName Suffix/Prefix, NiceName Modifier
    Vector, Integer, String, Float, Boolean, ENUM?
    Minimum
    Maximum
    Default
    ____________
    Affected String Filter
    Hide/unhide attributes for selected elements.
    Lock/unlock attributes for selected elements.
    Auto create a list of attributes for selected elements.
    Make Keyable, Displayable, Hidden, Delete, Rename, Move?
    Maybe attempt to change the order of the attributes within Maya.
    Rename Nice Name (search and replace?)
    ____________
    Export Attributes
    Import Attributes

"""

# Tool Version
__version_tuple__ = (0, 0, 2)
__version_suffix__ = '-wip'
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Attribute Manager.
    """
    from gt.tools.attribute_manager import attribute_manager
    print("Tool is still a work in progress.")


if __name__ == "__main__":
    launch_tool()
