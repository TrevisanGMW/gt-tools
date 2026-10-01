"""Kimodo Generator: text and pose guided animation for Maya."""

__version_tuple__ = (1, 11, 2)
__version__ = ".".join(str(number) for number in __version_tuple__)
_controller = None


def launch_tool():
    """Creates the MVC tool using the shared Maya/Qt application context.

    Returns:
        KimodoGeneratorController: Active tool controller.
    """
    from gt.ui.qt_utils import QtApplicationContext
    from gt.ui.qt_import import shiboken
    from gt.tools.kimodo_generator.kimodo_generator_model import KimodoGeneratorModel
    from gt.tools.kimodo_generator.kimodo_generator_view import KimodoGeneratorView
    from gt.tools.kimodo_generator.kimodo_generator_controller import KimodoGeneratorController

    global _controller
    if _controller and shiboken.isValid(_controller.view) and _controller.view.isVisible():
        _controller.view.raise_()
        _controller.view.activateWindow()
        return _controller
    if _controller:
        # A retained Maya workspace can remove the C++ view without a close event.
        # Explicitly retire the old controller before replacing the singleton.
        _controller.close()
    with QtApplicationContext() as context:
        model = KimodoGeneratorModel()
        view = KimodoGeneratorView(parent=context.get_parent(), version=__version__)
        _controller = KimodoGeneratorController(model, view)
    return _controller


if __name__ == "__main__":
    launch_tool()
