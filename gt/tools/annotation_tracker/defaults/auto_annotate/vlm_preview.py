"""Saves the images and prompt a VLM run would send, for review. Nothing is sent or changed."""

from gt.tools.annotation_tracker.auto_annotation import preview_vlm_request


ANNOTATION_TRACKER_DISPLAY = {
    "label": "VLM Preview Request",
    "button_color": "#606060",
    "hidden": True,
    "run_checked": False,
}


def run(context=None, **options):
    """Builds the VLM request for the current scene and saves it to the preview folder.

    Args:
        context (dict, optional): Tracker automation or Batch Processor context.
        **options: Explicit settings accepted by run_annotation.

    Returns:
        dict: Run result. ``vlm["preview_folder"]`` holds the review folder.
    """
    result = preview_vlm_request(context or {}, **options)
    folder = result["vlm"].get("preview_folder")
    if folder:
        print(f"[Auto Annotate] Preview: {result['vlm']['preview_images']} image(s) and the prompt saved to {folder}.")
    for message in result["warnings"][:8]:
        print(f"[Auto Annotate] {message}")
    return result


_tracker_context = globals().get("context")
if isinstance(_tracker_context, dict) and "replace_annotation_data" in _tracker_context:
    run(_tracker_context)
elif globals().get("__name__") == "__main__":
    run()
