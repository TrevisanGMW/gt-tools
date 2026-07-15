"""Create FK Driver tool entry point."""

__version_tuple__ = (2, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Builds and launches the Create FK Driver MVC tool.

    Returns:
        CreateFkDriverController: Launched controller.
    """
    from gt.tools.create_fk_driver.create_fk_driver_controller import CreateFkDriverController
    from gt.tools.create_fk_driver.create_fk_driver_model import CreateFkDriverModel
    from gt.tools.create_fk_driver.create_fk_driver_view import CreateFkDriverView
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = CreateFkDriverModel()
        view = CreateFkDriverView(parent=context.get_parent(), version=__version__)
        return CreateFkDriverController(model=model, view=view)


if __name__ == "__main__":
    launch_tool()
