"""GT Tools Startup Scripts.

Provides a configurable, preference-backed alternative to ``userSetup.py``
for scripts that should run after GT Tools is available in Maya.
"""

__version_tuple__ = (1, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Launches the Startup Scripts user interface."""
    from gt.tools.startup_scripts import startup_scripts_controller
    from gt.tools.startup_scripts import startup_scripts_model
    from gt.tools.startup_scripts import startup_scripts_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        view = startup_scripts_view.StartupScriptsView(
            parent=context.get_parent(),
            version=__version__,
        )
        model = startup_scripts_model.StartupScriptsModel()
        startup_scripts_controller.StartupScriptsController(model=model, view=view)


if __name__ == "__main__":
    launch_tool()
