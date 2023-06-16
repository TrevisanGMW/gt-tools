"""
 GT Orient Joints - Script for orienting multiple joints in a more predictable way
 github.com/TrevisanGMW/gt-tools - 2023-01-19

 0.0.1 to 0.0.4 - 2023-01-19
 Initial GUI
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Orient Joints.
    """
    from tools.orient_joints import orient_joints
    orient_joints.build_gui_orient_joints()


if __name__ == "__main__":
    launch_tool()
