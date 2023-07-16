"""
 GT Outliner Manager - General Outliner organization script
 github.com/TrevisanGMW/gt-tools - 2022-08-18

 0.1.0 - 2022-08-20
 Added reorder utility functions

 0.2.0 - 2022-08-21
 Added main sort function

 0.3.0 - 2022-08-21
 Added main sort function

 0.3.1 - 2022-08-22
 Added ascending/descending option to sort function
 Added attribute operation to sort function

 0.4.0 to 0.4.1 - 2022-08-23
 Changed script name from "Outliner Manager" to "Outliner Sorter"
 Added attribute operation to sort function
 Started GUI
    - Created Main Window
    - Added validate_operation and connected utilities
    - Added Sort by Attribute, custom attribute field and default channel drop-down menu

 0.4.2  to 0.5.1- 2022-08-23
 Connected Sort by Attribute button, drop-down menu and text-field
 Added shuffle order button
 Added link opener as help button
 Added drop-down menu for ascending/descending
 Added sort by name

 1.0.0 - 2022-08-26
 First released version
 Removed some unnecessary lines
"""


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Outliner Sorter.
    """
    from gt.tools.outliner_sorter import outliner_sorter
    outliner_sorter.build_gui_outliner_sorter()


if __name__ == "__main__":
    launch_tool()
