"""
 GT Selection Manager - Script to quickly create or update selections.
 github.com/TrevisanGMW/gt-tools -  2020-02-19

 1.0 - 2020-03-05
 Included Help Button

 1.1 - 2020-06-07
 Updated naming convention to make it clearer. (PEP8)
 Fixed random window widthHeight issue.

 1.2 - 2020-06-18
 Updated GUI
 Added window icon

 1.2.1 - 2020-06-25
 Fixed minor issue with non-unique names when listing shapes

 1.3 - 20202-10-25
 Added more documentation
 Replaced "headsUpMessage" with "inViewMessage"
 Made a few minor changes

 1.4 - 20202-11-15
 Updated a few UI elements (color and text)

 1.5 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.6 - 2021-08-18
 Added a select hierarchy button for convenience

 1.7.0 to 1.7.1 - 2022-07-04 to 2022-10-26
 Added patch to the script version
 Added logger
 Added debug message to broad exceptions
 Refactored big portion of the script
 Fixed issue with the selection of outliner colors
 Updated selection variable name from "selectedObjects" to "selected_objects"

 Todo:
     Add Selection base on Shader name, Texture, TRS
     Add choice between transform and shape for outliner color
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Selection Manager.
    """
    from tools.selection_manager import selection_manager
    selection_manager.build_gui_selection_manager()


if __name__ == "__main__":
    launch_tool()
