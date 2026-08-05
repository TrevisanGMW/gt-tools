"""Model and Maya operations for Create Testing Keys."""

import logging


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


SCRIPT_NAME = "Create Testing Keys"
ATTRIBUTES = ("tx", "ty", "tz", "rx", "ry", "rz", "sx", "sy", "sz")
ANIMATION_CURVE_TYPES = ("animCurveTA", "animCurveTL", "animCurveTT", "animCurveTU")
DEFAULT_OFFSETS = {attribute: 0.0 for attribute in ATTRIBUTES}


class CreateTestingKeysModel:
    """Stores tool settings and creates testing animation in Maya."""

    def __init__(self):
        """Initializes the model with the default settings."""
        self.offsets = dict(DEFAULT_OFFSETS)
        self.interval = 5.0
        self.add_inverted = True
        self.delete_previous = True
        self.use_world_space = True

    def reset_offsets(self):
        """Resets all offset values to zero.

        Returns:
            dict: Copy of the reset offset values.
        """
        self.offsets = dict(DEFAULT_OFFSETS)
        return dict(self.offsets)

    def create_testing_keys(self):
        """Creates testing keyframes using the current model settings.

        Returns:
            bool: True when testing keys were created.
        """
        cmds = get_maya_cmds()
        selection = cmds.ls(selection=True, long=True) or []
        if not selection:
            cmds.warning("Select at least one object to create testing keyframes.")
            return False

        active_offsets = get_active_offsets(self.offsets)
        if not active_offsets:
            cmds.warning("Provide at least one non-zero offset value.")
            return False

        original_time = cmds.currentTime(query=True)
        chunk_open = False
        try:
            cmds.undoInfo(openChunk=True, chunkName=SCRIPT_NAME)
            chunk_open = True
            if self.delete_previous:
                delete_connected_keyframes(selection, cmds=cmds)

            start_frame = cmds.playbackOptions(animationStartTime=True, query=True)
            last_frame = start_frame
            for attribute, offset in active_offsets.items():
                last_frame = create_attribute_test(
                    selection=selection,
                    attribute=attribute,
                    offset=offset,
                    interval=self.interval,
                    add_inverted=self.add_inverted,
                    use_world_space=self.use_world_space,
                    start_frame=start_frame,
                    cmds=cmds,
                )
            current_max = cmds.playbackOptions(maxTime=True, query=True)
            if last_frame > current_max:
                cmds.playbackOptions(maxTime=last_frame)
            return True
        except Exception as exception:
            logger.exception("Unable to create testing keyframes.")
            cmds.warning(f"Unable to create testing keyframes. Issue: {exception}")
            return False
        finally:
            cmds.currentTime(original_time)
            existing_selection = [item for item in selection if cmds.objExists(item)]
            if existing_selection:
                cmds.select(existing_selection, replace=True)
            if chunk_open:
                cmds.undoInfo(closeChunk=True, chunkName=SCRIPT_NAME)

    @staticmethod
    def delete_all_keyframes():
        """Deletes every time-based animation curve in the scene.

        Returns:
            int: Number of deleted animation curve nodes.
        """
        from gt.core import anim as core_anim

        return core_anim.delete_time_keyframes()


def get_active_offsets(offsets):
    """Gets valid non-zero offsets in deterministic channel order.

    Args:
        offsets (dict): Attribute names mapped to numeric offset values.

    Returns:
        dict: Valid non-zero offsets ordered by the supported attributes.
    """
    active_offsets = {}
    for attribute in ATTRIBUTES:
        try:
            value = float(offsets.get(attribute, 0.0))
        except (TypeError, ValueError):
            continue
        if value != 0.0:
            active_offsets[attribute] = value
    return active_offsets


def get_offset_vector(attribute, offset):
    """Builds an XYZ offset vector for an attribute.

    Args:
        attribute (str): Short transform attribute, such as ``tx``.
        offset (float): Offset amount.

    Returns:
        tuple: Three numeric XYZ offset values.
    """
    axis_index = {"x": 0, "y": 1, "z": 2}[attribute[-1]]
    values = [0.0, 0.0, 0.0]
    values[axis_index] = float(offset)
    return tuple(values)


def create_attribute_test(
    selection,
    attribute,
    offset,
    interval,
    add_inverted,
    use_world_space,
    start_frame,
    cmds=None,
):
    """Creates one attribute's test sequence on the supplied objects.

    Each object receives a neutral, positive, optional negative, and final
    neutral pose. Objects are placed sequentially on the timeline.

    Args:
        selection (list): Maya objects to animate.
        attribute (str): Short transform attribute to test.
        offset (float): Offset amount added to the original value.
        interval (float): Frames between poses.
        add_inverted (bool): Whether to add a negative offset pose.
        use_world_space (bool): Whether translate and rotate use world space.
        start_frame (float): Frame where the first object starts.
        cmds (module, optional): Maya commands module, primarily for testing.

    Returns:
        float: Last keyed frame.
    """
    if cmds is None:
        cmds = get_maya_cmds()
    current_frame = float(start_frame)
    for obj in selection:
        if not cmds.objExists(obj):
            continue
        channel = attribute[0]
        is_world_channel = use_world_space and channel in ("t", "r")
        original_values = get_channel_values(obj, channel, is_world_channel, cmds)
        key_attributes = get_key_attributes(attribute, is_world_channel)
        set_linear_keys(obj, key_attributes, current_frame, cmds)

        current_frame += interval
        apply_pose(obj, channel, original_values, get_offset_vector(attribute, offset), is_world_channel, cmds)
        set_linear_keys(obj, key_attributes, current_frame, cmds)

        if add_inverted:
            current_frame += interval
            inverted_vector = tuple(value * -1 for value in get_offset_vector(attribute, offset))
            apply_pose(obj, channel, original_values, inverted_vector, is_world_channel, cmds)
            set_linear_keys(obj, key_attributes, current_frame, cmds)

        current_frame += interval
        apply_pose(obj, channel, original_values, (0.0, 0.0, 0.0), is_world_channel, cmds)
        set_linear_keys(obj, key_attributes, current_frame, cmds)
    return current_frame


def get_channel_values(obj, channel, world_space, cmds):
    """Gets the current XYZ values for a transform channel.

    Args:
        obj (str): Maya object.
        channel (str): Channel prefix: t, r, or s.
        world_space (bool): Whether to query in world space.
        cmds (module): Maya commands module.

    Returns:
        tuple: Current XYZ values.
    """
    if world_space and channel == "t":
        return tuple(cmds.xform(obj, query=True, worldSpace=True, translation=True))
    if world_space and channel == "r":
        return tuple(cmds.xform(obj, query=True, worldSpace=True, rotation=True))
    return tuple(cmds.getAttr(f"{obj}.{channel}{axis}") for axis in "xyz")


def get_key_attributes(attribute, world_space):
    """Gets attributes that must be keyed for a pose.

    Args:
        attribute (str): Short transform attribute, such as ``tx``.
        world_space (bool): Whether the pose is applied in world space.

    Returns:
        list: Short Maya attribute names.
    """
    if world_space:
        return [f"{attribute[0]}{axis}" for axis in "xyz"]
    return [attribute]


def apply_pose(obj, channel, original_values, offset_vector, world_space, cmds):
    """Applies a transform pose while respecting locked local attributes.

    Args:
        obj (str): Maya object.
        channel (str): Channel prefix: t, r, or s.
        original_values (tuple): Original XYZ values.
        offset_vector (tuple): XYZ values to add.
        world_space (bool): Whether to apply translate or rotate in world space.
        cmds (module): Maya commands module.
    """
    target_values = tuple(
        original_value + offset_value
        for original_value, offset_value in zip(original_values, offset_vector)
    )
    if world_space and channel == "t":
        cmds.xform(obj, worldSpace=True, translation=target_values)
        return
    if world_space and channel == "r":
        cmds.xform(obj, worldSpace=True, rotation=target_values)
        return
    for axis, value in zip("xyz", target_values):
        plug = f"{obj}.{channel}{axis}"
        if not cmds.getAttr(plug, lock=True):
            cmds.setAttr(plug, value)


def set_linear_keys(obj, attributes, frame, cmds):
    """Sets linear keys on a collection of attributes.

    Args:
        obj (str): Maya object.
        attributes (list): Short attribute names to key.
        frame (float): Keyframe time.
        cmds (module): Maya commands module.
    """
    for attribute in attributes:
        plug = f"{obj}.{attribute}"
        if not cmds.getAttr(plug, lock=True):
            cmds.setKeyframe(
                obj,
                attribute=attribute,
                time=frame,
                inTangentType="linear",
                outTangentType="linear",
            )


def delete_connected_keyframes(selection, cmds=None):
    """Deletes time-based animation curves connected to selected objects.

    Args:
        selection (list): Maya objects whose animation should be deleted.
        cmds (module, optional): Maya commands module, primarily for testing.

    Returns:
        int: Number of animation curve nodes passed to Maya for deletion.
    """
    if cmds is None:
        cmds = get_maya_cmds()
    curves = set()
    for obj in selection:
        for curve_type in ANIMATION_CURVE_TYPES:
            curves.update(cmds.listConnections(obj, type=curve_type) or [])
    if curves:
        cmds.delete(sorted(curves))
    return len(curves)


def get_maya_cmds():
    """Imports Maya commands lazily.

    Returns:
        module: Maya commands module.
    """
    import maya.cmds as cmds

    return cmds
