"""
GT Extract Bound Joints - Extract or Transfer bound joints
github.com/TrevisanGMW/gt-tools - 2022-06-22

0.0.1 to 0.0.3 - 2022-06-22 to 2022-07-20
Created main function
Added GUI
Added skinCluster check

1.0.0 to 1.0.2 - 2022-07-20 to 2022-07-22
Added Filter non-existent and include mesh checkboxes
Updated help menu
Increased the size of the output window

1.1.0 to 1.1.4 - 2022-07-26 to 2022-09-12
Added "Save to Shelf" button
Added "Extract Bound Joints to Selection Sets" button
Updated help
Tweaked the UI spacing
Fixed a typo
Removed unnecessary parameter
Changed "Include Bound Mesh" to be be inactive by default
Added option to run bind/unbind skin functions
Centered Checkbox options a bit better
Fixed a few issues caused by the latest changes

Todo:
    Add Transfer functions
    Add option to include maya.cmds
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Extract Bound Joints.
    """
    from gt.tools.extract_bound_joints import extract_bound_joints
    extract_bound_joints.build_gui_extract_bound_joints()


if __name__ == "__main__":
    launch_tool()
