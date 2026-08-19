"""Maya-scene data access for Annotation Tracker."""

import json
import os
from datetime import datetime

from gt.tools.anim_annotation_tracker import annotation_tracker_model


def _get_maya_cmds():
    """Gets Maya commands without making this module Maya-dependent on import.

    Returns:
        module: Maya commands module.

    Raises:
        RuntimeError: If called outside a Maya Python runtime.
    """
    try:
        from maya import cmds
    except ImportError as exception:
        raise RuntimeError(
            "Annotation Tracker scene data is only available in Maya."
        ) from exception
    return cmds


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
    cmds = _get_maya_cmds()

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


def set_scene_annotation_data(file_data, ranges):
    """Replaces Annotation Tracker data in the current Maya scene.

    This UI-independent API is intended for automation and batch scripts. A
    range can use the internal tracker layout with ``start``, ``end``, and
    ``custom_data`` or the flattened public layout with ``start_frame``,
    ``end_frame``, and metadata fields alongside the range name.

    Args:
        file_data (dict): File-level annotation metadata.
        ranges (list): Range dictionaries or range-like objects.

    Returns:
        dict: JSON-compatible payload written to ``animAnnotationData``.

    Raises:
        RuntimeError: If called outside a Maya Python runtime.
        TypeError: If the existing scene data node is not a network node.
        ValueError: If supplied range data is invalid.
    """
    cmds = _get_maya_cmds()
    payload = annotation_tracker_model.build_scene_payload(file_data, ranges)
    node_name = annotation_tracker_model.SCENE_DATA_NODE_NAME
    data_attribute = annotation_tracker_model.SCENE_DATA_ATTRIBUTE
    edited_attribute = annotation_tracker_model.SCENE_LAST_EDITED_ATTRIBUTE

    if cmds.objExists(node_name):
        node_type = cmds.nodeType(node_name)
        if node_type != "network":
            raise TypeError(
                f"Scene node '{node_name}' must be a network node, not "
                f"'{node_type}'."
            )
    else:
        cmds.createNode("network", name=node_name)

    for attribute_name in (data_attribute, edited_attribute):
        if not cmds.attributeQuery(attribute_name, node=node_name, exists=True):
            cmds.addAttr(node_name, longName=attribute_name, dataType="string")

    cmds.setAttr(
        f"{node_name}.{data_attribute}",
        json.dumps(payload),
        type="string",
    )
    last_edited = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cmds.setAttr(
        f"{node_name}.{edited_attribute}",
        last_edited,
        type="string",
    )
    return payload


def get_scene_custom_data():
    """Gets scene annotation data using the previous helper name.

    This compatibility wrapper preserves existing scripts that used the former
    function name. New integrations should use ``get_scene_annotation_data``.

    Returns:
        dict: User-provided file and frame-range annotation data.
    """
    return get_scene_annotation_data()
