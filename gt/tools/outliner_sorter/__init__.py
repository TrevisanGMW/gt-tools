"""
 Outliner Manager - General Outliner organization script
 github.com/TrevisanGMW/gt-tools - 2022-08-18

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.
"""
# Tool Version
__version_tuple__ = (1, 0, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool Outliner Sorter.
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
