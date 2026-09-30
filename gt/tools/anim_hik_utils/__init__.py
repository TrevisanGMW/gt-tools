"""HumanIK Utilities: pose, definition, retargeting, and baking tools."""

__version_tuple__ = (1, 1, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Creates and displays the HumanIK Utilities MVC components.

    Returns:
        AnimHikUtilsController: Controller retained by the window.
    """
    from gt.tools.anim_hik_utils.anim_hik_utils_controller import AnimHikUtilsController
    from gt.tools.anim_hik_utils.anim_hik_utils_model import AnimHikUtilsModel
    from gt.tools.anim_hik_utils.anim_hik_utils_view import AnimHikUtilsView
    from gt.ui.qt_utils import QtApplicationContext

    with QtApplicationContext() as context:
        view = AnimHikUtilsView(parent=context.get_parent(), version=__version__)
        return AnimHikUtilsController(AnimHikUtilsModel(), view)


if __name__ == "__main__":
    launch_tool()
