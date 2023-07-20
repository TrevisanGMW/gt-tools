"""
 GT World Space Baker
 github.com/TrevisanGMW/gt-tools - 2021-11-23

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 1. This script stores animation according to the provided time line range for the selected controls
 2. Then forces the control back into that position by baking world space coordinates

 1.0.1 - 2021-11-26
 Deactivated viewport refresh when extracting/baking keys to speed up process
 Created undo chunk to bake operation

 1.0.2 - 2022-07-06
 Added logging
 Minor PEP8 Cleanup
 Dropped Python 2 support (Only Python 3+ now)

 TODO:
    Add sparse key option
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT World Space Baker.
    """
    from gt.tools.world_space_baker import world_space_baker
    world_space_baker.build_gui_world_space_baker()


if __name__ == "__main__":
    launch_tool()
