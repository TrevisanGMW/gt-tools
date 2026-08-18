"""
Animation Utilities

Import Line:
    import gt.core.anim as core_anim

"""

import gt.core.feedback as core_fback
import gt.core.io as core_io
import gt.core.namespace as core_namespace
import maya.cmds as cmds
import tempfile
import logging
import json
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


KEY_TYPE_TIME = ["animCurveTA", "animCurveTL", "animCurveTT", "animCurveTU"]
KEY_TYPE_DOUBLE = ["animCurveUL", "animCurveUA", "animCurveUT", "animCurveUU"]


class AnimationConstants:
    """Groups animation-clip constants and mode identifiers."""

    class Clip:
        """Constants describing the portable animation-clip format."""

        SCHEMA_VERSION = 1
        CACHE_FILENAME = "gt_copy_paste_animation.json"

    class PasteMode:
        """Constants that define how copied keys affect existing animation."""

        INSERT = "insert"
        REPLACE = "replace"

    class MappingMode:
        """Constants that define how source objects resolve to destinations."""

        SELECTION = "selection"
        NAME = "name"
        NAMESPACE = "namespace"


class KeyframeScope:
    def __init__(self):
        """
        Constant keyframe scope types (strings). Used to determine which keyframe
        (animation curve) nodes an operation should affect.
        """

    TIME = "time"  # Standard animation keyframes (animCurveTA, animCurveTL, ...)
    DOUBLE = "double"  # Set Driven Keys (animCurveUA, animCurveUL, ...)
    BOTH = "both"  # Both time and double keyframes

    @staticmethod
    def get_available_scopes():
        """
        Gets a list of all available keyframe scopes. These are the same as the string
        attributes found above.

        Returns:
            list: A list of available keyframe scopes (strings). e.g. ["time", "double", "both"]
        """
        scopes = []
        attrs = vars(KeyframeScope)
        attrs_keys = [attr for attr in attrs if not (attr.startswith("__") and attr.endswith("__"))]
        for key in attrs_keys:
            attr_value = getattr(KeyframeScope, key)
            if isinstance(attr_value, str) and not callable(attr_value):
                scopes.append(attr_value)
        return scopes


def get_time_keyframes(obj_list=None):
    """
    Gets animation keyframe nodes (excluding Set Driven Keys).

    Args:
        obj_list (list, optional): A list of objects to get keyframes from. If None, retrieves keyframes for the entire scene.

    Returns:
        list: A list of animation curve nodes that have time as input.
    """
    if isinstance(obj_list, str):
        obj_list = [obj_list]
    if obj_list is not None:
        # Get keyframe nodes connected to the provided objects
        keyframe_nodes = set()
        for obj in obj_list:
            key_nodes = cmds.keyframe(obj, query=True, name=True) or []
            keyframe_nodes.update(key_nodes)
        return sorted(list(keyframe_nodes))

    # If no object list is given, return all animation curve nodes in the scene
    return cmds.ls(type=KEY_TYPE_TIME) or []


def get_double_keyframes(obj_list=None):
    """
    Gets driven keyframe nodes (Set Driven Keys).

    Args:
        obj_list (list, optional): A list of objects to get keyframes from. If None, retrieves keys for the whole scene.

    Returns:
        list: A list of animation curve nodes that have a double (non-time) input.
    """

    def get_all_connected_keyframes(obj):
        """
        Helper function to get all the connected keyframe nodes for an object, including those managed by blendWeighted.
        Args:
            obj (str): Path to the object to get the keyframe connections from.
        Returns:
            set: A set with all detected double keyframes.
        """
        _keyframe_nodes = set()
        # Get the connections on the object for its attributes
        connections = cmds.listConnections(obj, source=True, destination=False, skipConversionNodes=True) or []

        for conn in connections:
            # Check if the connection is an animCurve (part of Set Driven Key system)
            if cmds.nodeType(conn) in KEY_TYPE_DOUBLE:
                _keyframe_nodes.add(conn)

            # If the connection is a blendWeighted node, check its connections as well
            elif cmds.nodeType(conn) == "blendWeighted":
                # Get the input attributes of blendWeighted and look for animCurves
                input_attrs = cmds.listAttr(f"{conn}.input", multi=True) or []

                for input_attr in input_attrs:

                    # input_conn = cmds.getAttr(f"{conn}.{input_attr}")
                    input_conn = cmds.listConnections(
                        f"{conn}.{input_attr}", source=True, destination=False, skipConversionNodes=True
                    )[0]
                    if input_conn and cmds.nodeType(input_conn) in KEY_TYPE_DOUBLE:
                        _keyframe_nodes.add(input_conn)

        return _keyframe_nodes

    if isinstance(obj_list, str):
        obj_list = [obj_list]

    keyframe_nodes = set()

    if obj_list is not None:
        for obj in obj_list:
            # Add the keyframes for each object
            keyframe_nodes.update(get_all_connected_keyframes(obj))
        return sorted(list(keyframe_nodes))

    # If no object list is given, return all driven keyframe nodes in the scene
    return sorted(cmds.ls(type=KEY_TYPE_DOUBLE)) or []


def get_keyframes(obj_list=None, key_scope=KeyframeScope.TIME):
    """
    Gets keyframe (animation curve) nodes for the requested scope.

    Args:
        obj_list (list, optional): Objects to get keyframes from. If None, the entire
            scene is considered.
        key_scope (str, optional): Which keyframe nodes to gather. A "KeyframeScope"
            value: TIME (animation keyframes), DOUBLE (Set Driven Keys) or BOTH.
            Defaults to KeyframeScope.TIME.

    Returns:
        list: A sorted list of keyframe (animation curve) nodes matching the scope.
    """
    normalized_scope = str(key_scope).lower()
    keyframe_nodes = set()
    if normalized_scope in (KeyframeScope.TIME, KeyframeScope.BOTH):
        keyframe_nodes.update(get_time_keyframes(obj_list=obj_list))
    if normalized_scope in (KeyframeScope.DOUBLE, KeyframeScope.BOTH):
        keyframe_nodes.update(get_double_keyframes(obj_list=obj_list))
    if normalized_scope not in KeyframeScope.get_available_scopes():
        logger.warning(
            f'Unknown key_scope "{key_scope}". Expected one of: {KeyframeScope.get_available_scopes()}.'
        )
    return sorted(keyframe_nodes)


def delete_time_keyframes(obj_list=None):
    """
    Deletes time (animation) keyframes. (Set Driven Keys are not included)

    Args:
        obj_list (list, optional): Objects to delete keyframes from. If None, all time
            keyframes in the scene are deleted.

    Returns:
        int: number of keyframe nodes deleted during the operation
    """
    function_name = "Delete Time Keyframes"
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    deleted_counter = 0
    try:
        for obj in get_time_keyframes(obj_list=obj_list):
            try:
                cmds.delete(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        feedback = core_fback.FeedbackMessage(
            quantity=deleted_counter,
            singular="keyframe node was",
            plural="keyframe nodes were",
            conclusion="deleted.",
            zero_overwrite_message="No keyframes found in this scene.",
        )
        feedback.print_inview_message()
        return deleted_counter
    except Exception as e:
        cmds.warning(str(e))
        return deleted_counter
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_double_keyframes(obj_list=None):
    """
    Deletes Double (driven) keyframes. (Animation keyframes are not included)

    Args:
        obj_list (list, optional): Objects to delete driven keyframes from. If None, all
            driven keyframes in the scene are deleted.

    Returns:
        int: number of keyframe nodes deleted during the operation
    """
    function_name = "Delete Double Keyframes"
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    deleted_counter = 0
    try:
        for obj in get_double_keyframes(obj_list=obj_list):
            try:
                cmds.delete(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        feedback = core_fback.FeedbackMessage(
            quantity=deleted_counter,
            singular="driven keyframe node was",
            plural="driven keyframe nodes were",
            conclusion="deleted.",
            zero_overwrite_message="No driven keyframes found in this scene.",
        )
        feedback.print_inview_message()
        return deleted_counter
    except Exception as e:
        cmds.warning(str(e))
        return deleted_counter
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_keyframes(obj_list=None, key_scope=KeyframeScope.TIME):
    """
    Deletes keyframe (animation curve) nodes for the requested scope. This removes the
    entire animation curve for each affected attribute (it does not operate on a time
    range). For range-based removal use "delete_keyframes_in_range".

    Args:
        obj_list (list, optional): Objects to delete keyframes from. If None, the whole
            scene is affected.
        key_scope (str, optional): Which keyframes to delete. A "KeyframeScope" value:
            TIME, DOUBLE or BOTH. Defaults to KeyframeScope.TIME.

    Returns:
        int: number of keyframe nodes deleted during the operation.
    """
    function_name = "Delete Keyframes"
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    deleted_counter = 0
    try:
        for keyframe_node in get_keyframes(obj_list=obj_list, key_scope=key_scope):
            try:
                cmds.delete(keyframe_node)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        feedback = core_fback.FeedbackMessage(
            quantity=deleted_counter,
            singular="keyframe node was",
            plural="keyframe nodes were",
            conclusion="deleted.",
            zero_overwrite_message="No matching keyframes found.",
        )
        feedback.print_inview_message()
        return deleted_counter
    except Exception as e:
        cmds.warning(str(e))
        return deleted_counter
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_keyframes_in_range(obj_list=None, start=None, end=None, key_scope=KeyframeScope.TIME):
    """
    Removes keyframes that fall within a time range, leaving keyframes outside the range
    (and the animation curves themselves) intact. Keys are not shifted to close the gap.
    For a ripple delete that shifts subsequent keys, see "ripple_delete_keyframes".

    Args:
        obj_list (list, optional): Objects whose keyframes are affected. If None, the
            whole scene is considered.
        start (float, optional): Start of the range (inclusive). If None, an open lower
            bound is used (removes everything up to "end").
        end (float, optional): End of the range (inclusive). If None, an open upper bound
            is used (removes everything from "start" onward).
        key_scope (str, optional): Which keyframes to affect. A "KeyframeScope" value:
            TIME, DOUBLE or BOTH. Defaults to KeyframeScope.TIME.

    Returns:
        int: number of keyframe (animation curve) nodes that had keys removed.
    """
    open_bound = 99999999  # Matches the sentinel range used by ripple_delete_keyframes
    range_start = -open_bound if start is None else start
    range_end = open_bound if end is None else end
    if range_start > range_end:
        cmds.warning("Invalid range: start frame is greater than end frame.")
        return 0

    keyframe_nodes = get_keyframes(obj_list=obj_list, key_scope=key_scope)
    if not keyframe_nodes:
        cmds.warning("No matching keyframes found for the provided scope.")
        return 0

    function_name = "Delete Keyframes In Range"
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    affected_counter = 0
    try:
        for keyframe_node in keyframe_nodes:
            try:
                # cutKey(clear=True) does not report how many keys it removed, so query first.
                keys_in_range = cmds.keyframe(
                    keyframe_node, query=True, time=(range_start, range_end), keyframeCount=True
                )
                if keys_in_range:
                    cmds.cutKey(keyframe_node, time=(range_start, range_end), clear=True)
                    affected_counter += 1
            except Exception as e:
                logger.debug(str(e))

        feedback = core_fback.FeedbackMessage(
            quantity=affected_counter,
            singular="keyframe node was",
            plural="keyframe nodes were",
            conclusion="affected.",
            zero_overwrite_message="No keyframes found in the provided range.",
        )
        feedback.print_inview_message()
        return affected_counter
    except Exception as e:
        cmds.warning(str(e))
        return affected_counter
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_keyframes_before_current_frame(obj_list=None, include_current=False, key_scope=KeyframeScope.TIME):
    """
    Removes keyframes located before the current frame.

    Args:
        obj_list (list, optional): Objects whose keyframes are affected. If None, the
            whole scene is considered.
        include_current (bool, optional): If True, keyframes on the current frame are also
            removed. Defaults to False.
        key_scope (str, optional): Which keyframes to affect. A "KeyframeScope" value:
            TIME, DOUBLE or BOTH. Defaults to KeyframeScope.TIME.

    Returns:
        int: number of keyframe (animation curve) nodes that had keys removed.
    """
    current_frame = cmds.currentTime(query=True)
    epsilon = 0.0001
    end = current_frame if include_current else current_frame - epsilon
    return delete_keyframes_in_range(obj_list=obj_list, start=None, end=end, key_scope=key_scope)


def delete_keyframes_after_current_frame(obj_list=None, include_current=False, key_scope=KeyframeScope.TIME):
    """
    Removes keyframes located after the current frame.

    Args:
        obj_list (list, optional): Objects whose keyframes are affected. If None, the
            whole scene is considered.
        include_current (bool, optional): If True, keyframes on the current frame are also
            removed. Defaults to False.
        key_scope (str, optional): Which keyframes to affect. A "KeyframeScope" value:
            TIME, DOUBLE or BOTH. Defaults to KeyframeScope.TIME.

    Returns:
        int: number of keyframe (animation curve) nodes that had keys removed.
    """
    current_frame = cmds.currentTime(query=True)
    epsilon = 0.0001
    start = current_frame if include_current else current_frame + epsilon
    return delete_keyframes_in_range(obj_list=obj_list, start=start, end=None, key_scope=key_scope)


def delete_time_keyframes_outside_range(start, end, obj_list=None, range_name="range"):
    """Removes time keyframes outside an inclusive frame range.

    The range bounds are preserved. This function finds the actual keyframe times on
    each curve before removing the keys, avoiding a fixed maximum frame sentinel.
    Set Driven Keys are intentionally excluded because their inputs are not time
    values.

    Args:
        start (float): First frame to preserve.
        end (float): Last frame to preserve.
        obj_list (list, optional): Objects whose time keyframes are affected. If None,
            the whole scene is considered.
        range_name (str, optional): User-facing name for the preserved range. Defaults
            to "range".

    Returns:
        int: Number of time keyframes deleted.
    """
    if start > end:
        cmds.warning("Invalid range: start frame is greater than end frame.")
        return 0

    keyframe_nodes = get_time_keyframes(obj_list=obj_list)
    if not keyframe_nodes:
        feedback = core_fback.FeedbackMessage(
            general_overwrite="No time keyframes found for the provided scope.",
        )
        feedback.print_inview_message()
        return 0

    function_name = "Delete Time Keyframes Outside Range"
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    deleted_counter = 0
    try:
        for keyframe_node in keyframe_nodes:
            keyframe_times = cmds.keyframe(keyframe_node, query=True, timeChange=True) or []
            out_of_range_times = [
                keyframe_time for keyframe_time in keyframe_times if keyframe_time < start or keyframe_time > end
            ]
            if not out_of_range_times:
                continue
            try:
                cmds.cutKey(
                    keyframe_node,
                    time=(min(out_of_range_times), max(out_of_range_times)),
                    clear=True,
                )
                deleted_counter += len(out_of_range_times)
            except Exception as e:
                logger.debug(str(e))

        feedback = core_fback.FeedbackMessage(
            quantity=deleted_counter,
            singular=f"keyframe outside the {range_name} was",
            plural=f"keyframes outside the {range_name} were",
            conclusion="deleted.",
            zero_overwrite_message=f"No keyframes were found outside the {range_name}.",
        )
        feedback.print_inview_message()
        return deleted_counter
    except Exception as e:
        cmds.warning(str(e))
        return deleted_counter
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_time_keyframes_outside_animation_range(obj_list=None):
    """Removes time keyframes outside Maya's animation timeline range.

    Args:
        obj_list (list, optional): Objects whose time keyframes are affected. If None,
            the whole scene is considered.

    Returns:
        int: Number of time keyframes deleted.
    """
    start = cmds.playbackOptions(query=True, animationStartTime=True)
    end = cmds.playbackOptions(query=True, animationEndTime=True)
    return delete_time_keyframes_outside_range(
        start=start,
        end=end,
        obj_list=obj_list,
        range_name="Timeline",
    )


def delete_time_keyframes_outside_playback_range(obj_list=None):
    """Removes time keyframes outside Maya's current playback range.

    Args:
        obj_list (list, optional): Objects whose time keyframes are affected. If None,
            the whole scene is considered.

    Returns:
        int: Number of time keyframes deleted.
    """
    start = cmds.playbackOptions(query=True, minTime=True)
    end = cmds.playbackOptions(query=True, maxTime=True)
    return delete_time_keyframes_outside_range(
        start=start,
        end=end,
        obj_list=obj_list,
        range_name="Playback Range",
    )


def check_unsaved_animation_changes():
    """
    Checks if the scene has animation keys and if there has been changes to save.
    Returns:
        bool: if True there are animation changes in the scene.
    """
    unsaved_animation_changes = False
    # Are there keys in the scene?
    if cmds.keyframe((cmds.ls(type="transform")), q=True):
        # Are there changes not saved?
        if cmds.file(q=True, anyModified=True):
            unsaved_animation_changes = True
    return unsaved_animation_changes


class DoubleKeyframe:
    """
    Represents a keyframe manager for an animation curve, handling driver and driven attributes.

    Attributes:
        node (str): The name of the animation curve.
        keyframe_data (list[dict]): A list of dictionaries containing keyframe information.
        driver_attr (str): The attribute driving the animation curve.
        driven_attr (str): The attribute being driven by the animation curve.
    """

    def __init__(self, node=None, data=None):
        """
        Initializes the DoubleKeyframe instance by querying keyframe data, driver, and driven attributes.

        Args:
            node (str, optional): The name of an existing animation curve of the type double (set driven key)
                                  If not provided, the data argument becomes a requirement.
            data (dict, optional): A data dictionary describing a double keyframe. If provided it overwrites the data
                                  queried from the scene. If not provided, the node argument becomes a requirement.
        """
        self.translate_multiplier = 1
        self.rotate_multiplier = 1
        self.scale_multiplier = 1

        if not node and not data:
            raise ValueError(f"Unable to create DoubleKeyframe object without a node or initial data.")

        if node and not cmds.objExists(node):
            raise ValueError(f'Unable to create DoubleKeyframe object. Missing provided node: "{node}".')
        if node:
            self.node = node
            self.driver_attr = self._query_driver_attr()
            self.driven_attr = self._query_driven_attr()
            self.keyframe_data = self._query_keyframe_data()
        if data:
            self.node = None
            self.driver_attr = None
            self.driven_attr = None
            self.keyframe_data = None
            self.read_data_from_dict(data)

    def _query_driver_attr(self):
        """
        Queries the driver attribute connected to the animation curve.

        Returns:
            str or None: The driver attribute name if found, otherwise None.
        """
        connected_attrs = cmds.listConnections(f"{self.node}.input", plugs=True, skipConversionNodes=True)
        if connected_attrs:
            return connected_attrs[0]
        return None

    def _query_driven_attr(self):
        """
        Queries the driven attribute connected to the animation curve.

        Returns:
            str or None: The driven attribute name if found, otherwise None.
        """
        connected_attrs = cmds.listConnections(
            f"{self.node}.output",
            plugs=True,
            destination=True,
            skipConversionNodes=True,
        )
        if connected_attrs:
            node, attr = connected_attrs[0].split(".")
            node_type = cmds.nodeType(node)
            if node_type == "blendWeighted":
                blended_weighted_attrs = cmds.listConnections(
                    f"{node}.output",
                    plugs=True,
                    destination=True,
                    skipConversionNodes=True,
                )
                if blended_weighted_attrs:
                    return blended_weighted_attrs[0]
        if connected_attrs:
            return connected_attrs[0]

    def _query_keyframe_data(self):
        """
        Queries and retrieves keyframe data from the animation curve.

        Returns:
            list[dict]: A list of dictionaries containing keyframe data, including time, value, interpolation,
            tangent types, angles, and weights.
        """
        keyframe_data = []
        key_count = cmds.keyframe(self.node, query=True, keyframeCount=True)

        for idx in range(key_count):
            key_index = (idx, idx)
            keyframe_info = {
                "time": cmds.keyframe(self.node, index=key_index, floatChange=True, q=True)[0],
                "value": cmds.keyframe(self.node, index=key_index, valueChange=True, q=True)[0],
                "interpolation": cmds.keyTangent(self.node, index=key_index, weightLock=True, q=True)[0],
                "in_tangent_type": cmds.keyTangent(self.node, index=key_index, inTangentType=True, q=True)[0],
                "out_tangent_type": cmds.keyTangent(self.node, index=key_index, outTangentType=True, q=True)[0],
                "in_angle_tangent": cmds.keyTangent(self.node, index=key_index, inAngle=True, q=True)[0],
                "out_angle_tangent": cmds.keyTangent(self.node, index=key_index, outAngle=True, q=True)[0],
                "in_weight": cmds.keyTangent(self.node, index=key_index, inWeight=True, q=True)[0],
                "out_weight": cmds.keyTangent(self.node, index=key_index, outWeight=True, q=True)[0],
            }
            keyframe_data.append(keyframe_info)

        return keyframe_data

    def get_keyframe_data(self):
        """
        Retrieves the keyframe data stored in the instance.

        Returns:
            list[dict]: A list of dictionaries containing keyframe data.
        """
        return self.keyframe_data

    def get_data_as_dict(self):
        """
        Gets the object values as a dictionary
        Returns:
            dict: The Curve object properties and its values.
        """
        _data = {
            "node": self.node,
            "driver_attr": self.driver_attr,
            "driven_attr": self.driven_attr,
            "keyframe_data": self.keyframe_data,
        }
        return _data

    def read_data_from_dict(self, data):
        """
        Modifies this object to match the data received. (Used to export and import preferences)
        Args:
            data (dict): A dictionary with attributes as keys and values for the preferences as their value.
                        e.g. {"node": "mpCube1_translateY"}
        """
        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def set_translate_multiplier(self, translate_multiplier):
        """
        Defines the scale
        Args:
            translate_multiplier (float, int): A multiplier for the driven key values connected to translate attributes.
        """
        self.translate_multiplier = translate_multiplier

    def set_rotate_multiplier(self, rotate_multiplier):
        """
        Defines the scale
        Args:
            rotate_multiplier (float, int): A multiplier for the driven key values connected to rotate attributes.
        """
        self.rotate_multiplier = rotate_multiplier

    def set_scale_multiplier(self, scale_multiplier):
        """
        Defines the scale
        Args:
            scale_multiplier (float, int): A multiplier for the driven key values connected to scale attributes.
        """
        self.scale_multiplier = scale_multiplier

    def apply(self):
        """
        Applies driven keyframe settings to the driven attribute based on the extracted keyframe data.
        """
        for idx, keyframe in enumerate(self.keyframe_data):
            key_index = (idx, idx)

            value = keyframe.get("value")

            # Determines if the value is being multiplied
            attr_only = str(self.driven_attr).split(".")[-1] if self.driven_attr else ""
            if attr_only in ["translateX", "translateY", "translateZ"]:
                value = value * self.translate_multiplier
            if attr_only in ["rotateX", "rotateY", "rotateZ"]:
                value = value * self.rotate_multiplier
            if attr_only in ["scaleX", "scaleY", "scaleZ"]:
                value = value * self.scale_multiplier

            cmds.setDrivenKeyframe(
                self.driven_attr,
                currentDriver=self.driver_attr,
                value=value,
                driverValue=keyframe.get("time"),
                insertBlend=True,
            )

            sdk = find_set_driven_key(driven_attr_path=self.driven_attr, driver_attr_path=self.driver_attr)

            interpolation = keyframe.get("interpolation")
            in_weight = keyframe.get("in_weight")
            out_weight = keyframe.get("out_weight")
            in_angle_tangent = keyframe.get("in_angle_tangent")
            out_angle_tangent = keyframe.get("out_angle_tangent")
            in_tangent_type = keyframe.get("in_tangent_type")
            out_tangent_type = keyframe.get("out_tangent_type")

            cmds.keyTangent(sdk, index=key_index, weightedTangents=interpolation)
            cmds.keyTangent(sdk, index=key_index, inWeight=in_weight)
            cmds.keyTangent(sdk, index=key_index, outWeight=out_weight)
            cmds.keyTangent(sdk, index=key_index, inAngle=in_angle_tangent)
            cmds.keyTangent(sdk, index=key_index, outAngle=out_angle_tangent)
            cmds.keyTangent(sdk, index=key_index, inTangentType=in_tangent_type)
            cmds.keyTangent(sdk, index=key_index, outTangentType=out_tangent_type)


def find_set_driven_key(driven_attr_path, driver_attr_path):
    """
    Identifies and returns the shared double keyframe node between a driven attribute
    and a driver attribute in Autodesk Maya.

    This function checks for existing connections between the driven and driver attributes,
    skipping blendWeighted nodes, and collects any intersecting double keyframe nodes.

    Args:
        driven_attr_path (str): The full path to the driven attribute.
        driver_attr_path (str): The full path to the driver attribute.

    Returns:
        str or None: The name of the double keyframe node if found, otherwise None.
    """
    if not driven_attr_path or not cmds.objExists(driven_attr_path):
        logger.warning(f'Unable to find set driven key using driven attribute path: "{driven_attr_path}".')
        return
    if not driver_attr_path or not cmds.objExists(driver_attr_path):
        logger.warning(f'Unable to find set driven key using driver attribute path: "{driver_attr_path}".')
        return
    driven_connections = cmds.listConnections(driven_attr_path, source=True, destination=False, plugs=True, scn=True)
    driver_connections = cmds.listConnections(driver_attr_path, source=False, destination=True, plugs=True, scn=True)

    # Skip weight blended nodes and collect double keyframes
    driven_key_nodes = []
    if driven_connections:
        driven_con = driven_connections[0]
        if cmds.nodeType(driven_con) == "blendWeighted":
            node, attr = driven_connections[0].split(".")
            blended_weighted_attrs = cmds.listConnections(
                f"{node}.input",
                plugs=True,
                source=True,
                destination=False,
                skipConversionNodes=True,
            )
            for attr_path in blended_weighted_attrs:
                node, attr = attr_path.split(".")
                if cmds.nodeType(node) in KEY_TYPE_DOUBLE:
                    driven_key_nodes.append(node)
        else:
            node, attr = driven_con.split(".")
            driven_key_nodes.append(node)

    # Collect Driver Double Keyframes
    driver_key_nodes = []
    if driver_connections:
        for driver_con in driver_connections:
            node, attr = driver_con.split(".")
            if cmds.nodeType(node) in KEY_TYPE_DOUBLE:
                driver_key_nodes.append(node)

    # Filter intersection
    source_destination_double_keys = list(set(driven_key_nodes) & set(driver_key_nodes))
    if source_destination_double_keys:
        return source_destination_double_keys[0]


def export_double_keys_to_directory(
    source_objs, target_dir, file_prefix="", file_format="json", override_permissions=True
):
    """
    Exports all double keyframes connected to an object as JSON files.
    Args:
        source_objs (list, str): The path to objects in the scene using double keyframes (driven keys)
        target_dir (str): Path to a directory where the JSON keyframes will be exported to.
        file_prefix (str, optional): An optional prefix to be added to the exported files.
        file_format (str, optional): Format of the exported files.
        override_permissions (bool, optional): If true, even read-only files will be overwritten.
    Returns:
        int: Number of exported files/keyframes.
    """
    if not os.path.isdir(target_dir):
        logger.error(f"Unable to export double keyframes. Invalid target directory.")
        return 0

    if source_objs and isinstance(source_objs, str):
        source_objs = [source_objs]
    _double_key_paths = get_double_keyframes(source_objs)

    counter = 0
    for dkey_path in _double_key_paths:
        try:
            _dkey = DoubleKeyframe(node=dkey_path)
            file_name = f"{file_prefix}{dkey_path}.{file_format}"
            file_path = os.path.join(target_dir, file_name)
            if override_permissions and os.path.exists(file_path):
                core_io.set_file_permission_modifiable(file_path)
            core_io.write_json(path=file_path, data=_dkey.get_data_as_dict())
            counter += 1
        except Exception as e:
            logger.warning(f"Unable to read double key frames. Issue: {e}")
    return counter


def import_double_keys_from_directory(
    source_dir, file_format="json", translate_multiplier=1.0, rotate_multiplier=1.0, scale_multiplier=1.0
):
    """
    Imports double keyframes from a directory and apply them to existing objects in the scene.
    Args:
        source_dir (str): The path to a directory containing json files that describe double keyframes.
                          See "export_double_keys_to_directory()" to create such files.
        file_format (str, optional): Format of the imported files. Only files with this extension will be considered.
        translate_multiplier (float, optional): If provided, the value of the keys connected to the translation channels
                                                are multiplied by this value. Useful for global rig rescale.
        rotate_multiplier (float, optional): If provided, the value of the keys connected to the rotate channels
                                             are multiplied by this value. Useful for global rig rescale.
        scale_multiplier (float, optional): If provided, the value of the keys connected to the scale channels
                                            are multiplied by this value. Useful for global rig rescale.
    Returns:
        int: Number of imported files/keyframes.
    """
    if not os.path.isdir(source_dir):
        logger.error(f"Unable to import double keyframes. Invalid target directory.")
        return

    counter = 0
    for filename in os.listdir(source_dir):
        if filename.lower().endswith(f".{file_format}"):
            file_path = os.path.join(source_dir, filename)
            try:
                data = core_io.read_json_dict(path=file_path)
                _dkey = DoubleKeyframe(data=data)
                _dkey.set_translate_multiplier(translate_multiplier)
                _dkey.set_rotate_multiplier(rotate_multiplier)
                _dkey.set_scale_multiplier(scale_multiplier)
                _dkey.apply()
                counter += 1
            except Exception as e:
                logger.error(f"Error reading {filename}: {e}")
    return counter


def ripple_delete_keyframes(start_frame, end_frame, nodes=None, tolerance=0.5, snap_keys=False):
    """
    Deletes keyframes within a specified time range and shifts subsequent keyframes
    backward to close the gap. Includes sub-frame handling for baked/mocap data.

    Args:
        start_frame (int or float): The exact whole frame where deletion should begin.
        end_frame (int or float): The exact whole frame where deletion should end.
        nodes (list of str, optional): The Maya elements to process. Defaults to selection.
        tolerance (float, optional): A decimal buffer to catch sub-frames. Defaults to 0.5.
            For example, a tolerance of 0.5 expands the range to catch anything from
            0.5 frames before the start to 0.5 frames after the end.
        snap_keys (bool, optional): If True, forces all keyframes on the nodes to snap
            to exact whole numbers before processing. Defaults to False.

    Returns:
        bool: True if the operation was successful, False if no nodes were processed.

    Raises:
        ValueError: If start_frame is greater than or equal to end_frame.
    """
    if start_frame >= end_frame:
        raise ValueError("start_frame must be strictly less than end_frame.")

    # Default to current selection if no specific nodes are provided
    if nodes is None:
        nodes = cmds.ls(selection=True)

    if not nodes:
        cmds.warning("No elements selected or provided to ripple delete keyframes.")
        return False

    # OPTION 1: Clean up the data first by snapping everything to whole frames
    if snap_keys:
        # The ":" syntax means "all time" in Maya's time range formatting
        cmds.snapKey(nodes, time=(":", ":"))

    # OPTION 2: Calculate safe bounds using the tolerance variable to catch sub-frames
    # If start_frame is 1 and tolerance is 0.5, it grabs from 0.5 onward (protecting 0.0)
    # If end_frame is 256 and tolerance is 0.5, it grabs up to 256.5 (catching 256's sub-frames)
    safe_start = start_frame - tolerance
    safe_end = end_frame + tolerance

    # 1. Delete all keyframes within the buffered range
    cmds.cutKey(nodes, time=(safe_start, safe_end), clear=True)

    # 2. Calculate the shift amount using the exact whole frames (to keep timing clean)
    shift_amount = start_frame - end_frame

    # 3. Shift all keyframes that come AFTER the buffered range
    upper_bound = 99999999

    cmds.keyframe(
        nodes,
        edit=True,
        relative=True,
        timeChange=shift_amount,
        time=(safe_end + 0.001, upper_bound)
    )

    print(
        f"Successfully removed frames {safe_start} to {safe_end} and shifted subsequent keys by {shift_amount} frames.")
    return True

# --------------------------------------- Keyframe Offset and Filter Utilities ---------------------------------------

def _get_offset_time_range(scope, current_frame=None):
    """Resolves a key-offset scope into an optional Maya time range.

    Args:
        scope (str): All, current, or playback offset scope.
        current_frame (float, optional): Current timeline frame when already known.

    Returns:
        tuple or None: Inclusive Maya time range, or None for all keys.
    """
    scope = str(scope or "all").lower()
    if scope == "current":
        current_frame = cmds.currentTime(query=True) if current_frame is None else current_frame
        return float(current_frame), 1000000000.0
    if scope == "playback":
        return (
            float(cmds.playbackOptions(query=True, min=True)),
            float(cmds.playbackOptions(query=True, max=True)),
        )
    return None


def _get_selected_keyframes():
    """Gets the current Maya keyframe selection.

    Returns:
        list: Selected keyframe data grouped by animation curve and input type.
    """
    selected_keyframes = []
    selected_curves = cmds.keyframe(query=True, selected=True, name=True) or []
    for curve in selected_curves:
        time_keys = cmds.keyframe(curve, query=True, selected=True, timeChange=True) or []
        if time_keys:
            selected_keyframes.append(
                {
                    "curve": curve,
                    "input_type": "time",
                    "values": [float(key_time) for key_time in time_keys],
                }
            )
        float_keys = cmds.keyframe(curve, query=True, selected=True, floatChange=True) or []
        if float_keys:
            selected_keyframes.append(
                {
                    "curve": curve,
                    "input_type": "float",
                    "values": [float(key_value) for key_value in float_keys],
                }
            )
    return selected_keyframes


def _offset_selected_keyframes(selected_keyframes, moved_key_times, offset):
    """Updates selected time-key locations after a keyframe offset.

    Args:
        selected_keyframes (list): Keyframe selection data from
            :func:`_get_selected_keyframes`.
        moved_key_times (dict): Moved key times grouped by animation curve.
        offset (float): Signed frame offset applied to the affected keys.

    Returns:
        list: Updated keyframe selection data.
    """
    for keyframe_data in selected_keyframes:
        if keyframe_data["input_type"] != "time":
            continue
        moved_times = set(moved_key_times.get(keyframe_data["curve"], []))
        keyframe_data["values"] = [
            key_time + offset if key_time in moved_times else key_time
            for key_time in keyframe_data["values"]
        ]
    return selected_keyframes


def _restore_selected_keyframes(selected_keyframes):
    """Restores a Maya keyframe selection without changing object selection.

    Args:
        selected_keyframes (list): Keyframe selection data from
            :func:`_get_selected_keyframes`.
    """
    try:
        cmds.selectKey(clear=True)
        for keyframe_data in selected_keyframes:
            range_key = keyframe_data["input_type"]
            for key_value in keyframe_data["values"]:
                cmds.selectKey(
                    keyframe_data["curve"],
                    add=True,
                    **{range_key: (key_value, key_value)},
                )
    except RuntimeError as exception:
        logger.warning(f"Unable to restore selected keyframes: {exception}")


def offset_time_keyframes(nodes=None, offset=1.0, scope="all"):
    """Offsets time keyframes while preserving their key values and tangents.

    Args:
        nodes (list, optional): Nodes whose animation curves should be offset. Uses
            the current selection when omitted.
        offset (float, optional): Signed frame offset. Negative offsets move left.
        scope (str, optional): One of all, selected, current, or playback.

    Returns:
        dict: Moved curve count, key count, and the applied offset.
    """
    offset = float(offset)
    if not offset:
        return {"curves": [], "key_count": 0, "offset": 0.0}
    if nodes is None:
        nodes = cmds.ls(selection=True, long=True) or []
    if isinstance(nodes, str):
        nodes = [nodes]
    curves = get_time_keyframes(nodes)
    if not curves:
        return {"curves": [], "key_count": 0, "offset": offset}

    moved_curves = []
    moved_key_times = {}
    key_count = 0
    time_range = _get_offset_time_range(scope)
    selected_keyframes = _get_selected_keyframes()
    undo_opened = False
    try:
        cmds.undoInfo(openChunk=True, chunkName="Offset Keyframes")
        undo_opened = True
        for curve in curves:
            curve_key_times = []
            if str(scope).lower() == "selected":
                curve_key_times = cmds.keyframe(curve, query=True, selected=True, timeChange=True) or []
                for key_time in curve_key_times:
                    cmds.keyframe(
                        curve,
                        edit=True,
                        relative=True,
                        time=(float(key_time), float(key_time)),
                        timeChange=offset,
                    )
            else:
                curve_key_times = cmds.keyframe(
                    curve,
                    query=True,
                    timeChange=True,
                    **({"time": time_range} if time_range else {}),
                ) or []
                if curve_key_times:
                    edit_kwargs = {"edit": True, "relative": True, "timeChange": offset}
                    if time_range:
                        edit_kwargs["time"] = time_range
                    cmds.keyframe(curve, **edit_kwargs)
            if curve_key_times:
                moved_curves.append(curve)
                moved_key_times[curve] = curve_key_times
                key_count += len(curve_key_times)
    finally:
        try:
            selected_keyframes = _offset_selected_keyframes(selected_keyframes, moved_key_times, offset)
            _restore_selected_keyframes(selected_keyframes)
        finally:
            if undo_opened:
                cmds.undoInfo(closeChunk=True, chunkName="Offset Keyframes")
    return {"curves": moved_curves, "key_count": key_count, "offset": offset}


def stagger_time_keyframes(nodes=None, step=1.0, scope="all"):
    """Offsets selected nodes incrementally in their current selection order.

    Args:
        nodes (list, optional): Ordered nodes to stagger. Uses current selection
            when omitted.
        step (float, optional): Signed frame increment between adjacent nodes.
        scope (str, optional): Offset scope passed to offset_time_keyframes.

    Returns:
        dict: Affected object count, curve count, key count, and stagger step.
    """
    if nodes is None:
        nodes = cmds.ls(selection=True, long=True) or []
    if isinstance(nodes, str):
        nodes = [nodes]
    nodes = list(nodes or [])
    affected_objects = 0
    affected_curves = []
    key_count = 0
    undo_opened = False
    try:
        cmds.undoInfo(openChunk=True, chunkName="Stagger Keyframes")
        undo_opened = True
        for index, node in enumerate(nodes):
            offset = float(step) * index
            if not offset:
                continue
            result = offset_time_keyframes(nodes=[node], offset=offset, scope=scope)
            if result["key_count"]:
                affected_objects += 1
                key_count += result["key_count"]
                affected_curves.extend(result["curves"])
    finally:
        if undo_opened:
            cmds.undoInfo(closeChunk=True, chunkName="Stagger Keyframes")
    return {
        "object_count": affected_objects,
        "curves": sorted(set(affected_curves)),
        "key_count": key_count,
        "step": float(step),
    }


def filter_animation_curves(curves):
    """Applies Maya's Euler filter to compatible animation curves.

    Args:
        curves (list): Animation curve nodes to filter.

    Returns:
        int: Number of curves passed to Maya's Euler filter.
    """
    curves = sorted(set(curves or []))
    if not curves:
        return 0
    selected_keyframes = _get_selected_keyframes()
    try:
        cmds.filterCurve(curves)
        return len(curves)
    except RuntimeError as exception:
        logger.warning(f"Unable to Euler filter animation curves: {exception}")
        return 0
    finally:
        _restore_selected_keyframes(selected_keyframes)


# ------------------------------------- Animation Clip Utilities -------------------------------------


def get_animation_clip_cache_path():
    """Gets the persistent temp-file location used by Copy/Paste Animation.

    Returns:
        str: Absolute JSON cache path.
    """
    return os.path.join(tempfile.gettempdir(), "gt_tools", AnimationConstants.Clip.CACHE_FILENAME)


def normalize_animation_clip(clip_data):
    """Validates and normalizes portable animation-clip data.

    Args:
        clip_data (dict): Raw animation-clip payload.

    Returns:
        dict: JSON-compatible normalized animation-clip payload.
    """
    clip_data = clip_data if isinstance(clip_data, dict) else {}
    normalized_objects = []
    for object_data in clip_data.get("objects") or []:
        if not isinstance(object_data, dict):
            continue
        object_name = str(object_data.get("name") or "").strip()
        if not object_name:
            continue
        normalized_attributes = []
        for attribute_data in object_data.get("attributes") or []:
            if not isinstance(attribute_data, dict):
                continue
            attribute_name = str(attribute_data.get("attribute") or "").strip()
            if not attribute_name:
                continue
            normalized_keys = []
            for key_data in attribute_data.get("keys") or []:
                if not isinstance(key_data, dict):
                    continue
                try:
                    time_value = float(key_data.get("time"))
                    value = float(key_data.get("value"))
                except (TypeError, ValueError):
                    continue
                normalized_key = {"time": time_value, "value": value}
                for tangent_key in ["in_tangent", "out_tangent"]:
                    tangent_value = key_data.get(tangent_key)
                    if tangent_value:
                        normalized_key[tangent_key] = str(tangent_value)
                if "weighted" in key_data:
                    normalized_key["weighted"] = bool(key_data.get("weighted"))
                normalized_keys.append(normalized_key)
            if normalized_keys:
                normalized_keys.sort(key=lambda item: item["time"])
                normalized_attributes.append(
                    {
                        "attribute": attribute_name,
                        "keys": normalized_keys,
                    }
                )
        if normalized_attributes:
            normalized_objects.append(
                {
                    "name": object_name,
                    "namespace_free_name": core_namespace.get_namespace_free_path(
                        object_data.get("namespace_free_name") or object_name
                    ),
                    "attributes": normalized_attributes,
                }
            )

    start_frame = clip_data.get("start_frame")
    end_frame = clip_data.get("end_frame")
    all_times = [
        key_data["time"]
        for object_data in normalized_objects
        for attribute_data in object_data["attributes"]
        for key_data in attribute_data["keys"]
    ]
    if all_times:
        start_frame = min(all_times) if start_frame is None else float(start_frame)
        end_frame = max(all_times) if end_frame is None else float(end_frame)
    else:
        start_frame = float(start_frame or 0)
        end_frame = float(end_frame or start_frame)
    return {
        "schema_version": AnimationConstants.Clip.SCHEMA_VERSION,
        "start_frame": float(start_frame),
        "end_frame": float(end_frame),
        "objects": normalized_objects,
    }


def write_animation_clip(clip_data, file_path=None):
    """Writes a portable animation clip to a JSON cache file.

    Args:
        clip_data (dict): Animation-clip payload.
        file_path (str, optional): Destination JSON path. Uses the shared session
            cache when omitted.

    Returns:
        str: Absolute path of the written animation clip.
    """
    file_path = file_path or get_animation_clip_cache_path()
    directory_path = os.path.dirname(os.path.abspath(file_path))
    if not os.path.isdir(directory_path):
        os.makedirs(directory_path)
    normalized_data = normalize_animation_clip(clip_data)
    with open(file_path, "w", encoding="utf-8") as output_file:
        json.dump(normalized_data, output_file, indent=4, sort_keys=True)
    return file_path


def read_animation_clip(file_path=None):
    """Reads a portable animation clip from disk.

    Args:
        file_path (str, optional): Source JSON path. Uses the shared session cache
            when omitted.

    Returns:
        dict: Normalized animation-clip payload, or an empty payload when missing.
    """
    file_path = file_path or get_animation_clip_cache_path()
    if not os.path.isfile(file_path):
        return normalize_animation_clip({})
    try:
        with open(file_path, "r", encoding="utf-8") as input_file:
            return normalize_animation_clip(json.load(input_file))
    except (OSError, ValueError, TypeError) as exception:
        logger.warning(f'Unable to read animation clip "{file_path}": {exception}')
        return normalize_animation_clip({})


def delete_animation_clip(file_path=None):
    """Deletes a portable animation clip cache file.

    Args:
        file_path (str, optional): Cache file to remove. Uses the shared session
            cache when omitted.

    Returns:
        bool: True when a file was removed.
    """
    file_path = file_path or get_animation_clip_cache_path()
    if not os.path.isfile(file_path):
        return False
    os.remove(file_path)
    return True


def get_animation_clip_summary(clip_data):
    """Builds a concise summary for a portable animation clip.

    Args:
        clip_data (dict): Animation-clip payload.

    Returns:
        str: User-facing object, channel, and frame-range summary.
    """
    clip_data = normalize_animation_clip(clip_data)
    object_count = len(clip_data["objects"])
    channel_count = sum(len(object_data["attributes"]) for object_data in clip_data["objects"])
    if not object_count:
        return "No copied animation."
    object_label = "object" if object_count == 1 else "objects"
    channel_label = "channel" if channel_count == 1 else "channels"
    return (
        f"{object_count} {object_label}, {channel_count} {channel_label}, "
        f"frames {clip_data['start_frame']:g}-{clip_data['end_frame']:g}."
    )


def get_animation_clip_details(clip_data):
    """Builds a readable report of all animation stored in a clip.

    Args:
        clip_data (dict): Animation-clip payload.

    Returns:
        str: Multi-line clip report containing object, channel, key, and frame data.
    """
    clip_data = normalize_animation_clip(clip_data)
    object_count = len(clip_data["objects"])
    channel_count = sum(len(object_data["attributes"]) for object_data in clip_data["objects"])
    key_count = sum(
        len(attribute_data["keys"])
        for object_data in clip_data["objects"]
        for attribute_data in object_data["attributes"]
    )
    lines = [
        "# Stored Animation Details",
        f"Schema Version: {clip_data['schema_version']}",
        f"Frame Range: {clip_data['start_frame']:g} - {clip_data['end_frame']:g}",
        f"Objects: {object_count}",
        f"Channels: {channel_count}",
        f"Keys: {key_count}",
        "",
    ]
    if not object_count:
        lines.append("No animation is currently stored.")
        return "\n".join(lines)
    for object_index, object_data in enumerate(clip_data["objects"], start=1):
        lines.extend(
            [
                f"# Object {object_index}: {object_data['name']}",
                f"Namespace-Free Path: {object_data['namespace_free_name']}",
                f"Channels: {len(object_data['attributes'])}",
            ]
        )
        for attribute_data in object_data["attributes"]:
            key_times = [key_data["time"] for key_data in attribute_data["keys"]]
            time_label = ", ".join(f"{key_time:g}" for key_time in key_times)
            lines.append(
                f"  {attribute_data['attribute']}: {len(key_times)} key(s) at frame(s): {time_label}"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def _get_key_tangent_values(node, attribute, query_flag):
    """Gets one optional key-tangent query with a failure-safe fallback.

    Args:
        node (str): Maya animation target.
        attribute (str): Animated attribute name.
        query_flag (str): Maya keyTangent query flag.

    Returns:
        list: Values returned by maya.cmds.keyTangent, or an empty list.
    """
    query_kwargs = {"query": True, query_flag: True}
    if attribute:
        query_kwargs["attribute"] = attribute
    try:
        return cmds.keyTangent(node, **query_kwargs) or []
    except RuntimeError:
        return []


def get_selected_time_keyframes():
    """Gets selected timeline keyframes grouped by animation curve.

    Returns:
        dict: Animation-curve names mapped to their selected key times.
    """
    selected_times = {}
    selected_curves = cmds.keyframe(query=True, selected=True, name=True) or []
    for curve in selected_curves:
        key_times = cmds.keyframe(curve, query=True, selected=True, timeChange=True) or []
        if key_times:
            selected_times[curve] = sorted(set(float(key_time) for key_time in key_times))
    return selected_times


def get_selected_time_keyframe_nodes(selected_key_times=None):
    """Gets animated nodes connected to selected timeline keyframes.

    Args:
        selected_key_times (dict, optional): Selected key times grouped by curve.
            Queries Maya when omitted.

    Returns:
        list: Unique long names for nodes connected to selected keyframes.
    """
    selected_key_times = selected_key_times or get_selected_time_keyframes()
    nodes = []
    for curve in selected_key_times:
        destination_plugs = cmds.listConnections(curve, source=False, destination=True, plugs=True) or []
        for destination_plug in destination_plugs:
            if "." not in destination_plug:
                continue
            destination_node = destination_plug.rsplit(".", 1)[0]
            long_names = cmds.ls(destination_node, long=True) or []
            if long_names and long_names[0] not in nodes:
                nodes.append(long_names[0])
    return nodes


def extract_animation_clip(nodes=None, start_frame=None, end_frame=None, selected_key_times=None):
    """Extracts animation keys from nodes into a portable JSON-compatible payload.

    Args:
        nodes (list, optional): Nodes whose animation should be copied. Uses the
            current selection when omitted.
        start_frame (float, optional): Optional inclusive first frame to copy.
        end_frame (float, optional): Optional inclusive last frame to copy.
        selected_key_times (dict, optional): Animation-curve names mapped to
            selected key times. When provided, only those keys are copied.

    Returns:
        dict: Normalized animation-clip payload containing values and tangent types.
    """
    if nodes is None:
        nodes = cmds.ls(selection=True, long=True) or []
    if isinstance(nodes, str):
        nodes = [nodes]
    selected_key_times = selected_key_times if isinstance(selected_key_times, dict) else None
    if selected_key_times is not None and not nodes:
        nodes = get_selected_time_keyframe_nodes(selected_key_times)

    clip_objects = []
    for node in nodes or []:
        if not cmds.objExists(node):
            continue
        long_node_names = cmds.ls(node, long=True) or [node]
        long_node_name = long_node_names[0]
        curve_attributes = []
        for curve in cmds.keyframe(node, query=True, name=True) or []:
            destination_plugs = cmds.listConnections(curve, source=False, destination=True, plugs=True) or []
            for destination_plug in destination_plugs:
                if "." not in destination_plug:
                    continue
                destination_node, attribute_name = destination_plug.rsplit(".", 1)
                destination_long_names = cmds.ls(destination_node, long=True) or []
                if destination_long_names and destination_long_names[0] == long_node_name:
                    curve_attributes.append((curve, attribute_name))
        attributes = []
        for curve, attribute_name in curve_attributes:
            allowed_key_times = None
            if selected_key_times is not None:
                if curve not in selected_key_times:
                    continue
                allowed_key_times = set(float(key_time) for key_time in selected_key_times[curve])
            key_times = cmds.keyframe(curve, query=True, timeChange=True) or []
            key_values = cmds.keyframe(curve, query=True, valueChange=True) or []
            in_tangents = _get_key_tangent_values(curve, None, "inTangentType")
            out_tangents = _get_key_tangent_values(curve, None, "outTangentType")
            weighted_tangents = _get_key_tangent_values(curve, None, "weightedTangents")
            keys = []
            for index, key_time in enumerate(key_times):
                if allowed_key_times is not None and float(key_time) not in allowed_key_times:
                    continue
                if start_frame is not None and float(key_time) < float(start_frame):
                    continue
                if end_frame is not None and float(key_time) > float(end_frame):
                    continue
                if index >= len(key_values):
                    continue
                key_data = {"time": float(key_time), "value": float(key_values[index])}
                if index < len(in_tangents):
                    key_data["in_tangent"] = in_tangents[index]
                if index < len(out_tangents):
                    key_data["out_tangent"] = out_tangents[index]
                if index < len(weighted_tangents):
                    key_data["weighted"] = bool(weighted_tangents[index])
                keys.append(key_data)
            if keys:
                attributes.append({"attribute": attribute_name, "keys": keys})
        if attributes:
            clip_objects.append(
                {
                    "name": node,
                    "namespace_free_name": core_namespace.get_namespace_free_path(node),
                    "attributes": attributes,
                }
            )
    return normalize_animation_clip({"objects": clip_objects})


def extract_selected_animation_clip(nodes=None):
    """Extracts only the currently selected timeline keyframes.

    Args:
        nodes (list, optional): Nodes that own the selected keyframes. When
            omitted, source nodes are resolved from the selected keyframes.

    Returns:
        dict: Normalized animation-clip payload containing selected keys only.
    """
    selected_key_times = get_selected_time_keyframes()
    return extract_animation_clip(nodes=nodes, selected_key_times=selected_key_times)


def _resolve_paste_targets(clip_data, targets, mapping_mode, source_namespace="", target_namespace=""):
    """Pairs copied objects with destination objects.

    Args:
        clip_data (dict): Normalized animation-clip payload.
        targets (list): Destination nodes selected by the user.
        mapping_mode (str): Selection-order, namespace-free name, or namespace
            swap mapping mode.
        source_namespace (str, optional): Namespace to replace when using
            namespace-swap mapping. Uses each copied object's namespace when
            omitted.
        target_namespace (str, optional): Replacement destination namespace.

    Returns:
        list: Source-object and destination-node pairs.
    """
    copied_objects = clip_data.get("objects") or []
    existing_targets = [target for target in targets or [] if cmds.objExists(target)]
    if not existing_targets:
        existing_targets = [
            object_data["name"]
            for object_data in copied_objects
            if cmds.objExists(object_data.get("name"))
        ]
    if str(mapping_mode).lower() == AnimationConstants.MappingMode.NAMESPACE:
        pairs = []
        for object_data in copied_objects:
            copied_name = object_data.get("name") or ""
            effective_source_namespace = source_namespace or core_namespace.get_namespace(
                copied_name,
                first_in_path=True,
            )
            target_name = core_namespace.replace_namespace_in_path(
                copied_name,
                source_namespace=effective_source_namespace,
                target_namespace=target_namespace,
            )
            target_long_names = cmds.ls(target_name, long=True) or []
            if target_long_names:
                pairs.append((object_data, target_long_names[0]))
        return pairs
    if str(mapping_mode).lower() == AnimationConstants.MappingMode.NAME:
        targets_by_name = {}
        for target in existing_targets:
            targets_by_name.setdefault(core_namespace.get_namespace_free_path(target), []).append(target)
        pairs = []
        for object_data in copied_objects:
            candidates = targets_by_name.get(object_data.get("namespace_free_name"), [])
            if candidates:
                pairs.append((object_data, candidates.pop(0)))
        return pairs

    if len(copied_objects) == 1 and len(existing_targets) > 1:
        return [(copied_objects[0], target) for target in existing_targets]
    return list(zip(copied_objects, existing_targets))


def _set_animation_key(node, attribute, key_data, destination_time):
    """Sets one copied animation key and recreates its tangent types.

    Args:
        node (str): Destination Maya node.
        attribute (str): Destination attribute name.
        key_data (dict): Source key value and tangent data.
        destination_time (float): Destination key time.
    """
    cmds.setKeyframe(node, attribute=attribute, time=destination_time, value=key_data["value"])
    tangent_kwargs = {}
    if key_data.get("in_tangent"):
        tangent_kwargs["inTangentType"] = key_data["in_tangent"]
    if key_data.get("out_tangent"):
        tangent_kwargs["outTangentType"] = key_data["out_tangent"]
    if tangent_kwargs:
        cmds.keyTangent(
            node,
            attribute=attribute,
            time=(destination_time, destination_time),
            edit=True,
            **tangent_kwargs,
        )
    if "weighted" in key_data:
        cmds.keyTangent(
            node,
            attribute=attribute,
            time=(destination_time, destination_time),
            edit=True,
            weightedTangents=bool(key_data["weighted"]),
        )


def paste_animation_clip(
    clip_data,
    targets=None,
    paste_time=None,
    mode=AnimationConstants.PasteMode.INSERT,
    mapping_mode=AnimationConstants.MappingMode.SELECTION,
    source_attribute="",
    destination_attribute="",
    source_namespace="",
    target_namespace="",
):
    """Pastes a portable animation clip onto Maya nodes.

    Paste Insert shifts target keys at and after the destination frame to keep
    future animation intact. Paste Replace clears every affected target channel
    before writing the copied animation, matching its full-replace behavior.

    Args:
        clip_data (dict): Animation payload returned by extract_animation_clip.
        targets (list, optional): Destination nodes. Uses matching source nodes
            when omitted.
        paste_time (float, optional): Destination time for the copied start frame.
            Uses the current frame when omitted.
        mode (str, optional): Insert or replace.
        mapping_mode (str, optional): Selection order, namespace-free name, or
            exact namespace-swap mapping.
        source_attribute (str, optional): Optional copied channel to isolate.
        destination_attribute (str, optional): Optional channel name to receive
            the isolated copied channel.
        source_namespace (str, optional): Source namespace to replace when using
            namespace-swap mapping. Uses the copied object's namespace when empty.
        target_namespace (str, optional): Destination namespace used with
            namespace-swap mapping.

    Returns:
        dict: Counts for pasted targets, channels, keys, and skipped channels.
    """
    clip_data = normalize_animation_clip(clip_data)
    if not clip_data["objects"]:
        return {"targets": 0, "channels": 0, "keys": 0, "skipped": 0, "curves": []}
    if targets is None:
        targets = cmds.ls(selection=True, long=True) or []
    if isinstance(targets, str):
        targets = [targets]
    paste_time = cmds.currentTime(query=True) if paste_time is None else float(paste_time)
    mode = str(mode or AnimationConstants.PasteMode.INSERT).lower()
    if mode not in [AnimationConstants.PasteMode.INSERT, AnimationConstants.PasteMode.REPLACE]:
        raise ValueError(f'Unknown animation paste mode "{mode}".')

    source_attribute = str(source_attribute or "").strip()
    destination_attribute = str(destination_attribute or "").strip()
    pairs = _resolve_paste_targets(
        clip_data,
        targets,
        mapping_mode,
        source_namespace=source_namespace,
        target_namespace=target_namespace,
    )
    source_start = float(clip_data["start_frame"])
    source_end = float(clip_data["end_frame"])
    insert_duration = max(1.0, source_end - source_start + 1.0)
    original_time = cmds.currentTime(query=True)
    pasted_targets = set()
    pasted_channels = 0
    pasted_keys = 0
    skipped_channels = 0
    affected_curves = []
    prepared_channels = set()
    undo_opened = False
    try:
        cmds.undoInfo(openChunk=True, chunkName="Paste Animation")
        undo_opened = True
        cmds.refresh(suspend=True)
        for object_data, target in pairs:
            for attribute_data in object_data["attributes"]:
                source_name = attribute_data["attribute"]
                if source_attribute and source_name != source_attribute:
                    continue
                target_name = destination_attribute if source_attribute and destination_attribute else source_name
                target_plug = f"{target}.{target_name}"
                if not cmds.objExists(target_plug):
                    skipped_channels += 1
                    continue
                channel_key = (target, target_name)
                if channel_key not in prepared_channels:
                    if mode == AnimationConstants.PasteMode.REPLACE:
                        cmds.cutKey(target, attribute=target_name, clear=True)
                    elif insert_duration:
                        existing_times = cmds.keyframe(
                            target,
                            attribute=target_name,
                            query=True,
                            timeChange=True,
                        ) or []
                        if existing_times:
                            cmds.keyframe(
                                target,
                                attribute=target_name,
                                edit=True,
                                relative=True,
                                time=(float(paste_time), 1000000000.0),
                                timeChange=insert_duration,
                            )
                    prepared_channels.add(channel_key)
                channel_keys = attribute_data["keys"]
                for key_data in channel_keys:
                    destination_key_time = float(paste_time) + (float(key_data["time"]) - source_start)
                    _set_animation_key(target, target_name, key_data, destination_key_time)
                    pasted_keys += 1
                if channel_keys:
                    pasted_targets.add(target)
                    pasted_channels += 1
                    affected_curves.extend(cmds.keyframe(target, attribute=target_name, query=True, name=True) or [])
    finally:
        cmds.currentTime(original_time)
        cmds.refresh(suspend=False)
        if undo_opened:
            cmds.undoInfo(closeChunk=True, chunkName="Paste Animation")
    return {
        "targets": len(pasted_targets),
        "channels": pasted_channels,
        "keys": pasted_keys,
        "skipped": skipped_channels,
        "curves": sorted(set(affected_curves)),
    }




if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint

    # out = None
    # # out = delete_time_keyframes()
    # print("#" * 80)
    # out = get_double_keyframes()
    # import gt.utils.system as utils_sys
    #
    # test_path = os.path.join(utils_sys.get_desktop_path(), f"test_dir")
    # exported_count = export_double_keys_to_directory(["pSphere1"], test_path)
    # print(exported_count)
    # delete_double_keyframes()
    # import_double_keys_from_directory(test_path)
    # # print(out)
    # # dkey1 = DoubleKeyframe("animCurveUA1")
    # # dkey2 = DoubleKeyframe("pSphere1_rotateX")
    # # delete_double_keyframes()
    # # dkey1.apply()
    # # dkey2.apply()
    # # pprint(dkey.get_keyframe_data())
    # # extract_driven_key_data(out)
    #
    # # pprint(out)

    ripple_delete_keyframes(0.2, 256, tolerance=0.1)
