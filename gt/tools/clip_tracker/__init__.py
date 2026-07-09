"""
Animation Clip Tracker
"""

import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

__version_tuple__ = (1, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool():
    """Launches the Animation Clip Tracker.

    Returns:
        ClipTrackerController: Tool controller.
    """
    from gt.tools.clip_tracker import clip_tracker_controller
    from gt.tools.clip_tracker import clip_tracker_model
    from gt.tools.clip_tracker import clip_tracker_view

    model = clip_tracker_model.ClipTrackerModel()
    view = clip_tracker_view.ClipTrackerView(version=__version__)
    controller = clip_tracker_controller.ClipTrackerController(model=model, view=view)
    controller.start()
    return controller


if __name__ == "__main__":
    launch_tool()

