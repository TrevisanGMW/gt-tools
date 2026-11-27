"""Opens profile, calibration, skeleton, and model preferences."""


ANNOTATION_TRACKER_DISPLAY = {
    "label": "Annotation Setup",
    "button_color": "#606060",
    "hidden": False,
    "run_checked": False,
}


def run(context=None):
    """Opens the Annotation Setup window.

    Args:
        context (dict, optional): Annotation Tracker automation context.

    Returns:
        QDialog or None: Active Setup window in interactive Maya.
    """
    from gt.tools.annotation_tracker.auto_annotation_setup import open_setup

    return open_setup(context)


_tracker_context = globals().get("context")
if isinstance(_tracker_context, dict) and "replace_annotation_data" in _tracker_context:
    run(_tracker_context)
elif __name__ == "__main__":
    run()
