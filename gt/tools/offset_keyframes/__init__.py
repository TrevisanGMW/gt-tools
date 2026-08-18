"""Offset Keyframes tool entry point."""

__version_tuple__ = (1, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Builds and launches the Offset Keyframes MVC tool.

    Returns:
        OffsetKeyframesController: Launched controller.
    """
    from gt.tools.offset_keyframes.offset_keyframes_controller import OffsetKeyframesController
    from gt.tools.offset_keyframes.offset_keyframes_model import OffsetKeyframesModel
    from gt.tools.offset_keyframes.offset_keyframes_service import OffsetKeyframesService
    from gt.tools.offset_keyframes.offset_keyframes_view import OffsetKeyframesView
    from gt.ui import qt_utils

    with qt_utils.QtApplicationContext() as context:
        model = OffsetKeyframesModel()
        view = OffsetKeyframesView(parent=context.get_parent(), version=__version__)
        service = OffsetKeyframesService()
        return OffsetKeyframesController(model=model, view=view, service=service)


if __name__ == "__main__":
    launch_tool()
