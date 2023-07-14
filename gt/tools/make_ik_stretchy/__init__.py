"""
 GT Make IK Stretchy - Solution for making simple IK systems stretchy.
 github.com/TrevisanGMW/gt-tools -  2020-03-13

 1.1 - 2020-06-07
 Fixed random window widthHeight issue.
 Updated naming convention to make it clearer. (PEP8)

 1.2 - 2020-06-17
 Added window icon
 Added help menu
 Changed GUI

 1.3 - 2020-11-15
 Tweaked the color and text for the title and help menu

 1.4 - 2020-12-29
 Recreate a big portion of the main function
 Changed script name from "Make Stretchy Legs" to "Make IK Stretchy"
 Added load ik handle button
 Added load attribute holder button
 Added stretchy name system
 Created functions to validate objects
 Created functions to update GUI
 Updated help

 1.5 - 2021-01-03
 Updated stretchy system to avoid cycles and errors
 Removed incorrect Help GUI call line from standalone version
 Updated the help info to match changes
 Added option to return the joint under the ikHandle
 Updated stretchy system to account for any curvature

 1.5.1 - 2021-01-04
 Changed stretchy system, so it doesn't use a floatConstant node

 1.5.2- 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.5.3
 Added patch to version
 Added logger
 PEP8 Cleanup

"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Make IK Stretchy.
    """
    from gt.tools.make_ik_stretchy import make_ik_stretchy
    make_ik_stretchy.build_gui_make_ik_stretchy()


if __name__ == "__main__":
    launch_tool()
