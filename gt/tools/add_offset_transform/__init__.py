"""Add Offset Transform tool entry point."""

__version_tuple__ = (2, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Builds and launches the Add Offset Transform MVC tool.

    Returns:
        AddOffsetTransformController: Launched controller.
    """
    from gt.tools.add_offset_transform.add_offset_transform_controller import AddOffsetTransformController
    from gt.tools.add_offset_transform.add_offset_transform_model import AddOffsetTransformModel
    from gt.tools.add_offset_transform.add_offset_transform_view import AddOffsetTransformView
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = AddOffsetTransformModel()
        view = AddOffsetTransformView(parent=context.get_parent(), version=__version__)
        return AddOffsetTransformController(model=model, view=view)


if __name__ == "__main__":
    launch_tool()
