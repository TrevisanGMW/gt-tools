"""Generates annotations from measured motion and pose cues."""

from gt.tools.annotation_tracker.auto_annotation import run_annotation


ANNOTATION_TRACKER_DISPLAY = {
    "label": "Auto Annotate",
    "button_color": "#6A6A6A",
    "hidden": False,
}


def run(context=None, **options):
    """Runs the same annotator in the Tracker, Batch Processor, or Maya Python.

    Args:
        context (dict, optional): Tracker automation or Batch Processor context.
        **options: Explicit settings accepted by run_annotation.

    Returns:
        dict: Run outcome, generated ranges, and validation diagnostics.
    """
    context = context or {}
    result = run_annotation(context, **options)
    print(f"[Auto Annotate] Motion cue profile: {result.get('profile', 'unknown')}.")
    if result.get("overwritten_ranges"):
        print(f"[Auto Annotate] Replaced {result['overwritten_ranges']} existing range(s) (overwrite mode).")
    count = result["added_ranges"]
    if count:
        summary = f"Added {count} annotation range(s)."
    elif result["changed"]:
        summary = "Updated annotation fields with no new ranges."
    else:
        summary = "No annotation changes."
    print(f"[Auto Annotate] {result['outcome'].capitalize()}. {summary}")
    if result["quality"]:
        report = result["quality"]
        print(f"[Auto Annotate] Motion Evaluator Quality {report['score']}/100 ({report['status']}).")
    messages = result["warnings"] + result["validation_errors"]
    for message in messages[:12]:
        print(f"[Auto Annotate] {message}")
    if len(messages) > 12:
        print(f"[Auto Annotate] {len(messages) - 12} additional diagnostics in the result.")
    if result["vlm"] and "preview_folder" in result["vlm"]:
        print(
            f"[Auto Annotate] Preview: {result['vlm']['preview_images']} image(s) saved to "
            f"{result['vlm']['preview_folder']}."
        )
    elif result["vlm"]:
        applied = result["vlm"]["applied"]
        deferred = len(result["vlm"]["deferred"])
        print(f"[Auto Annotate] Applied {applied} VLM suggestion(s). Deferred {deferred}.")
    if result["outcome"] == "failed" and "control" in context:
        raise RuntimeError("; ".join(result["warnings"]))
    parent = context.get("parent")
    if parent is not None and hasattr(parent, "status_bar"):
        parent.status_bar.setText(messages[0] if messages else summary)
    return result


_tracker_context = globals().get("context")
if (
    isinstance(_tracker_context, dict)
    and "replace_annotation_data" in _tracker_context
    and "control" not in _tracker_context
):
    run(_tracker_context)
elif globals().get("__name__") == "__main__":
    run()
