"""
 Renamer - Script for Quickly Renaming Multiple Objects
 github.com/TrevisanGMW/gt-tools - 2020-06-25

 ATTENTION!!: This is a legacy tool. It was created before version "3.0.0" and it should NOT be used as an example of
 how to create new tools. As a legacy tool, its code and structure may not align with the current package standards.
 Please read the "CONTRIBUTING.md" file for more details and examples on how to create new tools.
"""
# Tool Version
__version_tuple__ = (1, 6, 3)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """
    Launch user interface and create any necessary connections for the tool to function.
    Entry point for when using the tool Renamer.
    """
    return build_gui_renamer()


def build_gui_renamer():
    """Builds the Renamer user interface.

    Returns:
        RenamerController: Controller for the launched tool.
    """
    from gt.tools.renamer import renamer_controller
    from gt.tools.renamer import renamer_model
    from gt.tools.renamer import renamer_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        view = renamer_view.RenamerView(parent=context.get_parent(), version=__version__)
        model = renamer_model.RenamerModel()
        controller = renamer_controller.RenamerController(model=model, view=view)
        return controller


def build_gui_help_renamer():
    """Compatibility wrapper for the removed help window.

    Returns:
        RenamerController: Controller for the launched tool.
    """
    return build_gui_renamer()


if __name__ == "__main__":
    launch_tool()
