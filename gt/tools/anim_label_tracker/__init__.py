"""Animation Label Tracker."""


__version_tuple__ = (1, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool(parent=None):
    """Launches Animation Label Tracker.

    Args:
        parent (QWidget, optional): Parent widget.

    Returns:
        AnimationLabelTrackerController: Active tracker controller.
    """
    from gt.tools.anim_label_tracker import label_tracker_controller
    from gt.tools.anim_label_tracker import label_tracker_model
    from gt.tools.anim_label_tracker import label_tracker_view

    model = label_tracker_model.AnimationLabelTrackerModel()
    view = label_tracker_view.AnimationLabelTrackerView(model=model, parent=parent)
    controller = label_tracker_controller.AnimationLabelTrackerController(
        model=model,
        view=view,
    )
    controller.start()
    return controller


if __name__ == "__main__":
    launch_tool()
