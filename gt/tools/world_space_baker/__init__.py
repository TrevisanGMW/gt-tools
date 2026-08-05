"""World Space Baker tool entry point."""

__version_tuple__ = (2, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Builds and launches the World Space Baker MVC tool.

    Returns:
        WorldSpaceBakerController: Launched controller.
    """
    from gt.tools.world_space_baker.world_space_baker_controller import WorldSpaceBakerController
    from gt.tools.world_space_baker.world_space_baker_model import WorldSpaceBakerModel
    from gt.tools.world_space_baker.world_space_baker_service import WorldSpaceBakerService
    from gt.tools.world_space_baker.world_space_baker_view import WorldSpaceBakerView
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = WorldSpaceBakerModel()
        view = WorldSpaceBakerView(parent=context.get_parent(), version=__version__)
        service = WorldSpaceBakerService()
        return WorldSpaceBakerController(model=model, view=view, service=service)


if __name__ == "__main__":
    launch_tool()
