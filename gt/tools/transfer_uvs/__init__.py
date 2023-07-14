"""
 GT Transfer UVs - Script for exporting/importing or transferring UVs
 github.com/TrevisanGMW - 2021-06-22
 Tested on Maya 2020.4 - Windows 10

 1.1 - 2021-06-22
 It now iterates through all intermediate objects to guarantee they all have the same UVs

 1.2 - 2021-06-23
 Added a help window
 Added a comparison check before the counter
 Added operation result to output line

 1.3.0 - 2022-07-07
 PEP8 Cleanup
 Added logger
 Added patch to version
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Transfer UVs.
    """
    from gt.tools.transfer_uvs import transfer_uvs
    transfer_uvs.build_gui_uv_transfer()


if __name__ == "__main__":
    launch_tool()
