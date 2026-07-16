"""Shape Text to Curve package entry point."""

# Tool Version
__version_tuple__ = (2, 0, 0)
__version_suffix__ = ''
__version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__


def launch_tool():
    """Launches and connects the Shape Text to Curve MVC components.

    Returns:
        ShapeTextToCurveController: Connected controller instance.
    """
    from gt.tools.shape_text_to_curve import shape_text_to_curve_controller
    from gt.tools.shape_text_to_curve import shape_text_to_curve_model
    from gt.tools.shape_text_to_curve import shape_text_to_curve_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        view = shape_text_to_curve_view.ShapeTextToCurveView(parent=context.get_parent(), version=__version__)
        model = shape_text_to_curve_model.ShapeTextToCurveModel()
        controller = shape_text_to_curve_controller.ShapeTextToCurveController(model=model, view=view)
        return controller


if __name__ == "__main__":
    launch_tool()
