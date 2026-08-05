"""Create Testing Keys package entry point."""

# Tool Version
__version_tuple__ = (2, 0, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """Builds and launches the Create Testing Keys MVC tool.

    Returns:
        CreateTestingKeysController: Controller for the launched tool.
    """
    from gt.tools.create_testing_keys import create_testing_keys_controller
    from gt.tools.create_testing_keys import create_testing_keys_model
    from gt.tools.create_testing_keys import create_testing_keys_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        view = create_testing_keys_view.CreateTestingKeysView(
            parent=context.get_parent(),
            version=__version__,
        )
        model = create_testing_keys_model.CreateTestingKeysModel()
        controller = create_testing_keys_controller.CreateTestingKeysController(
            model=model,
            view=view,
        )
        return controller


if __name__ == "__main__":
    launch_tool()
