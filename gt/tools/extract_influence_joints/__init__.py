"""
 GT Extract Bound Joints - Extract or Transfer bound joints
 github.com/TrevisanGMW/gt-tools - 2022-06-22

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

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
# Tool Version
__version_tuple__ = (1, 1, 5)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Extract Bound Joints.
    """
    from gt.tools.extract_influence_joints import extract_influence_joints
    extract_influence_joints.script_version = __version__
    extract_influence_joints.build_gui_extract_influence_joints()


if __name__ == "__main__":
    launch_tool()
