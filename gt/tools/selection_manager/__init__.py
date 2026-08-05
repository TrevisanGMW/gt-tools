"""
 Selection Manager - Script to quickly create or update selections.
 github.com/TrevisanGMW/gt-tools -  2020-02-19

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.
"""
# Tool Version
__version_tuple__ = (1, 7, 1)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool Selection Manager.
    """
    return build_gui_selection_manager()


def build_gui_selection_manager():
    """Builds the Selection Manager user interface.

    Returns:
        SelectionManagerController: Controller for the launched tool.
    """
    from gt.tools.selection_manager import selection_manager_controller
    from gt.tools.selection_manager import selection_manager_model
    from gt.tools.selection_manager import selection_manager_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        view = selection_manager_view.SelectionManagerView(parent=context.get_parent(), version=__version__)
        model = selection_manager_model.SelectionManagerModel()
        controller = selection_manager_controller.SelectionManagerController(model=model, view=view)
        return controller


def build_gui_help_selection_manager():
    """Compatibility wrapper for the removed help action.

    Returns:
        SelectionManagerController: Controller for the launched tool.
    """
    return build_gui_selection_manager()


if __name__ == "__main__":
    launch_tool()
