"""
GT Color Manager
"""
# Tool Version
__version_tuple__ = (2, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Launches the Color Manager tool.

    Returns:
        ColorManagerController: Active tool controller.
    """
    from gt.tools.color_manager import color_manager

    color_manager.script_version = __version__
    return color_manager.build_gui_color_manager()


if __name__ == "__main__":
    launch_tool()
