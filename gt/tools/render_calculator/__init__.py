"""Render Calculator tool entry point."""


__version_tuple__ = (2, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__)
__version__ += __version_suffix__


def launch_tool():
    """Builds and launches the Render Calculator MVC tool.

    Returns:
        RenderCalculatorController: Controller for the launched tool.
    """
    from gt.tools.render_calculator.render_calculator_controller import (
        RenderCalculatorController,
    )
    from gt.tools.render_calculator.render_calculator_model import (
        RenderCalculatorModel,
    )
    from gt.tools.render_calculator.render_calculator_view import (
        RenderCalculatorView,
    )
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = RenderCalculatorModel()
        view = RenderCalculatorView(parent=context.get_parent(), version=__version__)
        controller = RenderCalculatorController(model=model, view=view)
    return controller


if __name__ == "__main__":
    launch_tool()
