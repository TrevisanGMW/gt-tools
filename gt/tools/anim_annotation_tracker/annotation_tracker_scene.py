"""Maya-scene data access for Annotation Tracker."""

import json

from gt.tools.anim_annotation_tracker import annotation_tracker_model


def get_scene_custom_data():
    """Gets annotation metadata saved in the current Maya scene.

    The result excludes Annotation Tracker implementation fields, including
    range IDs, display colors, and lock states. It contains only nested
    dictionaries and scalar values, making it suitable for USD prim
    ``customData``.

    Returns:
        dict: User-provided file and frame-range metadata.

    Raises:
        RuntimeError: If the function is called outside a Maya Python runtime.
    """
    try:
        from maya import cmds
    except ImportError as exception:
        raise RuntimeError(
            "Annotation Tracker scene data is only available in Maya."
        ) from exception

    node_name = annotation_tracker_model.SCENE_DATA_NODE_NAME
    attribute_name = annotation_tracker_model.SCENE_DATA_ATTRIBUTE
    empty_payload = {"file_data": {}, "range_data": []}
    if not cmds.objExists(node_name):
        return annotation_tracker_model.build_usd_custom_data(empty_payload)
    if not cmds.attributeQuery(attribute_name, node=node_name, exists=True):
        return annotation_tracker_model.build_usd_custom_data(empty_payload)

    data_string = cmds.getAttr(f"{node_name}.{attribute_name}")
    if not data_string:
        return annotation_tracker_model.build_usd_custom_data(empty_payload)
    try:
        payload = json.loads(data_string)
    except (TypeError, ValueError) as exception:
        cmds.warning(f"Failed to parse Annotation Tracker scene data: {exception}")
        return annotation_tracker_model.build_usd_custom_data(empty_payload)
    return annotation_tracker_model.build_usd_custom_data(payload)
