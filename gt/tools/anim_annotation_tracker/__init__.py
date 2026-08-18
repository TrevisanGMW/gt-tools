"""Annotation Tracker."""


__version_tuple__ = (1, 0, 0)
__version_suffix__ = ""
__version__ = ".".join(str(number) for number in __version_tuple__) + __version_suffix__


def launch_tool(parent=None):
    """Launches Annotation Tracker.

    Args:
        parent (QWidget, optional): Parent widget.

    Returns:
        AnnotationTrackerController: Active tracker controller.
    """
    from gt.tools.anim_annotation_tracker import annotation_tracker_controller
    from gt.tools.anim_annotation_tracker import annotation_tracker_model
    from gt.tools.anim_annotation_tracker import annotation_tracker_view

    model = annotation_tracker_model.AnnotationTrackerModel()
    view = annotation_tracker_view.AnnotationTrackerView(model=model, parent=parent)
    controller = annotation_tracker_controller.AnnotationTrackerController(
        model=model,
        view=view,
    )
    controller.start()
    return controller


def get_scene_annotation_data():
    """Gets Annotation Tracker annotation data saved in the current Maya scene.

    The returned dictionary contains file metadata and frame-range metadata
    only. It excludes tracker-only state such as range IDs, colors, and locks,
    and uses nested dictionaries and scalar values suitable for USD prim
    ``customData``.

    Returns:
        dict: User-provided Annotation Tracker data, or empty structures
        when the scene has no tracker data.
    """
    from gt.tools.anim_annotation_tracker import annotation_tracker_scene

    return annotation_tracker_scene.get_scene_annotation_data()


def get_scene_custom_data():
    """Gets scene annotation data using the previous helper name.

    This compatibility wrapper preserves existing scripts that used the former
    function name. New integrations should use ``get_scene_annotation_data``.

    Returns:
        dict: User-provided Annotation Tracker data.
    """
    return get_scene_annotation_data()


if __name__ == "__main__":
    launch_tool()
