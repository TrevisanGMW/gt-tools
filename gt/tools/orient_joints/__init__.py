"""
 GT Orient Joints - Script for orienting multiple joints in a more predictable way
 github.com/TrevisanGMW/gt-tools - 2023-01-19

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

 0.0.1 to 0.0.4 - 2023-01-19
 Initial GUI
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Orient Joints.
    """
    from gt.tools.orient_joints import orient_joints
    orient_joints.build_gui_orient_joints()


if __name__ == "__main__":
    launch_tool()
