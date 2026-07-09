"""
 GT Outliner Manager - General Outliner organization script
 github.com/TrevisanGMW/gt-tools - 2022-08-18

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.

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

 1.0.1 - 2024-03-07
 Imported utility functions
"""
# Tool Version
__version_tuple__ = (1, 0, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool GT Outliner Sorter.
    """
    return build_gui_outliner_sorter()


def build_gui_outliner_sorter():
    """Builds the Outliner Sorter user interface.

    Returns:
        OutlinerSorterController: Controller for the launched tool.
    """
    from gt.tools.outliner_sorter import outliner_sorter_controller
    from gt.tools.outliner_sorter import outliner_sorter_model
    from gt.tools.outliner_sorter import outliner_sorter_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        view = outliner_sorter_view.OutlinerSorterView(parent=context.get_parent(), version=__version__)
        model = outliner_sorter_model.OutlinerSorterModel()
        controller = outliner_sorter_controller.OutlinerSorterController(model=model, view=view)
        return controller


if __name__ == "__main__":
    launch_tool()
