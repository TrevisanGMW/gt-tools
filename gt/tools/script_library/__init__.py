"""Script Library MVC tool entry point."""

import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

__version_tuple__ = (1, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Launches the dockable Script Library MVC tool."""
    from gt.ui import qt_utils
    from gt.tools.script_library import script_library_controller
    from gt.tools.script_library import script_library_model
    from gt.tools.script_library import script_library_view

    with qt_utils.QtApplicationContext() as context:
        view = script_library_view.ScriptLibraryView(
            parent=context.get_parent(), version=__version__
        )
        model = script_library_model.ScriptLibraryModel()
        script_library_controller.ScriptLibraryController(model=model, view=view)


if __name__ == "__main__":
    launch_tool()
