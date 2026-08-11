"""Morphing Utilities MVC tool entry point."""

__version_tuple__ = (2, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Creates the Morphing Utilities model, view, service, and controller.

    Returns:
        MorphingUtilitiesController: Connected tool controller.
    """
    from gt.tools.morphing_utilities import morphing_utilities_controller
    from gt.tools.morphing_utilities import morphing_utilities_model
    from gt.tools.morphing_utilities import morphing_utilities_service
    from gt.tools.morphing_utilities import morphing_utilities_view
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = morphing_utilities_model.MorphingUtilitiesModel()
        view = morphing_utilities_view.MorphingUtilitiesView(
            parent=context.get_parent(),
            version=__version__,
        )
        service = morphing_utilities_service.MorphingUtilitiesService()
        controller = morphing_utilities_controller.MorphingUtilitiesController(
            model=model,
            view=view,
            service=service,
        )
        return controller


if __name__ == "__main__":
    launch_tool()
