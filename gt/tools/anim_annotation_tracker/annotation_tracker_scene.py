"""Maya-scene data access for Annotation Tracker."""

import json
import os

from gt.tools.anim_annotation_tracker import annotation_tracker_model


def _get_preferred_schema():
    """Loads the active schema used to order exported custom data.

    Returns:
        dict: Saved schema data, or an empty dictionary when unavailable.
    """
    preferences = annotation_tracker_model.AnnotationTrackerModel()
    schema_path = preferences.get_preference("schema_path", "")
    schema_path = str(schema_path or "").strip(' "\'')
    if not schema_path or not os.path.isfile(schema_path):
        return {}
    try:
        with open(schema_path, encoding="utf-8") as schema_file:
            schema = json.load(schema_file)
    except (OSError, TypeError, ValueError):
        return {}
    return schema if isinstance(schema, dict) else {}


def get_scene_annotation_data():
    """Gets annotation data saved in the current Maya scene.

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
    schema = _get_preferred_schema()
    empty_payload = {"file_data": {}, "range_data": []}
    if not cmds.objExists(node_name):
        return annotation_tracker_model.build_annotation_data(
            empty_payload,
            schema=schema,
        )
    if not cmds.attributeQuery(attribute_name, node=node_name, exists=True):
        return annotation_tracker_model.build_annotation_data(
            empty_payload,
            schema=schema,
        )

    data_string = cmds.getAttr(f"{node_name}.{attribute_name}")
    if not data_string:
        return annotation_tracker_model.build_annotation_data(
            empty_payload,
            schema=schema,
        )
    try:
        payload = json.loads(data_string)
    except (TypeError, ValueError) as exception:
        cmds.warning(f"Failed to parse Annotation Tracker scene data: {exception}")
        return annotation_tracker_model.build_annotation_data(
            empty_payload,
            schema=schema,
        )
    return annotation_tracker_model.build_annotation_data(payload, schema=schema)


def get_scene_custom_data():
    """Gets scene annotation data using the previous helper name.

    This compatibility wrapper preserves existing scripts that used the former
    function name. New integrations should use ``get_scene_annotation_data``.

    Returns:
        dict: User-provided file and frame-range annotation data.
    """
    return get_scene_annotation_data()
