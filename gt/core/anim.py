"""
Animation Utilities

Import Line:
    import gt.core.anim as core_anim

"""

import gt.core.feedback as core_fback
import gt.core.io as core_io
import maya.cmds as cmds
import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


KEY_TYPE_TIME = ["animCurveTA", "animCurveTL", "animCurveTT", "animCurveTU"]
KEY_TYPE_DOUBLE = ["animCurveUL", "animCurveUA", "animCurveUT", "animCurveUU"]


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
    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]
    if obj_list:
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

    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]

    keyframe_nodes = set()

    if obj_list:
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
