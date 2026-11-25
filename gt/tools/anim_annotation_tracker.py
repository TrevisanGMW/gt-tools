"""Compatibility entry point for scripts using Annotation Tracker's former name."""

from importlib import import_module

from gt.tools.annotation_tracker import (
    __version__,
    __version_suffix__,
    __version_tuple__,
    get_scene_annotation_data,
    get_scene_custom_data,
    launch_tool,
    set_scene_annotation_data,
)


def __getattr__(name):
    """Resolves module imports made through the former tool name.

    Args:
        name (str): Requested attribute.

    Returns:
        module: Corresponding module from the Annotation Tracker package.
    """
    if name in {
        "annotation_tracker",
        "annotation_tracker_controller",
        "annotation_tracker_model",
        "annotation_tracker_scene",
        "annotation_tracker_schema_editor",
        "annotation_tracker_view",
    }:
        return import_module(f"gt.tools.annotation_tracker.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":
    launch_tool()
