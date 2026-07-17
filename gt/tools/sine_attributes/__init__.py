"""
 GT Sine Attributes - Create Sine output attributes without using third-party plugins or expressions.
 github.com/TrevisanGMW/gt-tools - 2021-01-25

 1.0 - 2021-01-25
 Initial Release

 1.1 to 1.1.1 - 2021-05-10 to 2021-06-30
 Made script compatible with Python 3 (Maya 2022+)
 Added patch to version
 General cleanup

 2.0.0 - 2026-07-17
 Refactored to MVC pattern.
 Added persistent settings.
"""
# Tool Version
__version_tuple__ = (2, 0, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """Launch user interface and create any necessary connections for the tool to function.

    Entry point for when using the tool GT Sine Attributes.
    Creates Model, View and Controller.
    """
    from gt.tools.sine_attributes import sine_attributes_controller
    from gt.tools.sine_attributes import sine_attributes_model
    from gt.tools.sine_attributes import sine_attributes_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        _model = sine_attributes_model.SineAttributesModel()
        _view = sine_attributes_view.SineAttributesView(parent=context.get_parent(), version=__version__)
        _controller = sine_attributes_controller.SineAttributesController(model=_model, view=_view)


if __name__ == "__main__":
    launch_tool()

