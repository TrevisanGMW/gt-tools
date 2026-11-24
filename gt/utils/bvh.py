"""
BVH Utilities - Read Biovision Hierarchy (.bvh) motion files and build them in Maya.

Parsing is pure Python, so it can run and be tested outside Maya. Only build_bvh_skeleton
and import_bvh_file touch the scene, and they import Maya when called.

Import Line:
    import gt.utils.bvh as utils_bvh
"""

import logging
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

TIME_MODE_REAL_TIME = "real_time"
TIME_MODE_FRAME_PER_FRAME = "frame_per_frame"
TIME_MODES = [TIME_MODE_REAL_TIME, TIME_MODE_FRAME_PER_FRAME]

POSITION_CHANNELS = {"xposition": "translateX", "yposition": "translateY", "zposition": "translateZ"}
ROTATION_CHANNELS = {"xrotation": "rotateX", "yrotation": "rotateY", "zrotation": "rotateZ"}
MAYA_ROTATE_ORDERS = ["xyz", "yzx", "zxy", "xzy", "yxz", "zyx"]
END_SITE_SUFFIX = "_end"


class BvhJoint:
    """One joint of a BVH hierarchy."""

    def __init__(self, name, parent_index=-1, offset=(0.0, 0.0, 0.0), channels=None):
        """Initializes a BVH joint.

        Args:
            name (str): Joint name as written in the file.
            parent_index (int, optional): Index of the parent joint, -1 for roots.
            offset (tuple, optional): Rest offset from the parent (x, y, z).
            channels (list, optional): Channel names in file order, e.g. ["Zrotation", "Xrotation", "Yrotation"].
        """
        self.name = name
        self.parent_index = parent_index
        self.offset = tuple(float(value) for value in offset)
        self.channels = list(channels or [])
        self.channel_start = 0
        self.end_site_offset = None

    def get_rotation_axes(self):
        """Gets the rotation axes in file order.

        Returns:
            str: Lowercase axes such as "zxy". Empty when the joint has no rotation channels.
        """
        return "".join(channel[0].lower() for channel in self.channels if channel.lower() in ROTATION_CHANNELS)


class BvhData:
    """Parsed BVH hierarchy and motion."""

    def __init__(self, joints=None, frame_time=1.0 / 30.0, frames=None):
        """Initializes BVH data.

        Args:
            joints (list, optional): BvhJoint objects in file order (parents always come before children).
            frame_time (float, optional): Seconds per frame.
            frames (list, optional): Rows of channel values, one row per frame.
        """
        self.joints = list(joints or [])
        self.frame_time = float(frame_time)
        self.frames = list(frames or [])

    @property
    def frame_count(self):
        """Gets the number of motion frames.

        Returns:
            int: Frame count.
        """
        return len(self.frames)

    @property
    def fps(self):
        """Gets the sample rate of the motion.

        Returns:
            float: Frames per second, or 0.0 when the frame time is not positive.
        """
        if self.frame_time <= 0:
            return 0.0
        return 1.0 / self.frame_time

    @property
    def channel_count(self):
        """Gets the number of values expected per frame.

        Returns:
            int: Total channel count.
        """
        return sum(len(joint.channels) for joint in self.joints)

    def get_channel_values(self, joint_index, channel_name):
        """Gets every frame value for one joint channel.

        Args:
            joint_index (int): Joint index.
            channel_name (str): Channel name, case-insensitive (e.g. "Xrotation").

        Returns:
            list: One float per frame, or an empty list when the joint has no such channel.
        """
        joint = self.joints[joint_index]
        lowered_channels = [channel.lower() for channel in joint.channels]
        if channel_name.lower() not in lowered_channels:
            return []
        column = joint.channel_start + lowered_channels.index(channel_name.lower())
        return [row[column] for row in self.frames]


def get_maya_rotate_order(rotation_axes):
    """Converts BVH rotation channel order to a Maya rotate order index.

    BVH applies the listed rotations from left to right as parent-to-child (intrinsic) rotations,
    so the Maya order (applied first to last) is the reverse of the listed order.

    Args:
        rotation_axes (str): Axes in file order, e.g. "zxy".

    Returns:
        int: Maya rotateOrder index (0 = xyz). Defaults to 0 for incomplete axis lists.
    """
    maya_order = str(rotation_axes or "").lower()[::-1]
    if maya_order in MAYA_ROTATE_ORDERS:
        return MAYA_ROTATE_ORDERS.index(maya_order)
    return 0


def parse_bvh_text(text):
    """Parses the text content of a BVH file.

    Args:
        text (str): Full BVH text.

    Returns:
        BvhData: Parsed hierarchy and motion.

    Raises:
        ValueError: When the text is not a valid BVH file.
    """
    tokens = text.split()
    if not tokens or tokens[0].upper() != "HIERARCHY":
        raise ValueError("Not a BVH file: missing HIERARCHY header.")
    joints = []
    parent_stack = []
    pending_end_site = False
    token_index = 1
    while token_index < len(tokens):
        token = tokens[token_index]
        upper_token = token.upper()
        if upper_token in ("ROOT", "JOINT"):
            parent_index = parent_stack[-1] if parent_stack else -1
            joints.append(BvhJoint(name=tokens[token_index + 1], parent_index=parent_index))
            token_index += 2
        elif upper_token == "END":
            pending_end_site = True
            token_index += 2
        elif token == "{":
            parent_stack.append(-2 if pending_end_site else len(joints) - 1)
            token_index += 1
        elif token == "}":
            if not parent_stack:
                raise ValueError("Invalid BVH hierarchy: unbalanced braces.")
            closed_index = parent_stack.pop()
            if closed_index == -2:
                pending_end_site = False
            token_index += 1
        elif upper_token == "OFFSET":
            offset = tuple(float(value) for value in tokens[token_index + 1 : token_index + 4])
            if pending_end_site:
                owner_index = next((index for index in reversed(parent_stack) if index >= 0), -1)
                if owner_index >= 0:
                    joints[owner_index].end_site_offset = offset
            elif joints:
                joints[-1].offset = offset
            token_index += 4
        elif upper_token == "CHANNELS":
            channel_count = int(tokens[token_index + 1])
            joints[-1].channels = tokens[token_index + 2 : token_index + 2 + channel_count]
            token_index += 2 + channel_count
        elif upper_token == "MOTION":
            token_index += 1
            break
        else:
            raise ValueError(f'Invalid BVH hierarchy: unexpected token "{token}".')
    if not joints:
        raise ValueError("Invalid BVH file: no joints found.")
    channel_start = 0
    for joint in joints:
        joint.channel_start = channel_start
        channel_start += len(joint.channels)
    frame_count, frame_time, token_index = _parse_motion_header(tokens, token_index)
    values = tokens[token_index:]
    expected_values = frame_count * channel_start
    if len(values) < expected_values:
        raise ValueError(f"Invalid BVH motion: expected {expected_values} values, found {len(values)}.")
    frames = []
    for frame_index in range(frame_count):
        row_start = frame_index * channel_start
        frames.append([float(value) for value in values[row_start : row_start + channel_start]])
    return BvhData(joints=joints, frame_time=frame_time, frames=frames)


def _parse_motion_header(tokens, token_index):
    """Parses the "Frames:" and "Frame Time:" lines of a BVH motion section.

    Args:
        tokens (list): Whitespace-separated BVH tokens.
        token_index (int): Index of the first token after "MOTION".

    Returns:
        tuple: (frame_count, frame_time, next_token_index).

    Raises:
        ValueError: When the header is missing or malformed.
    """
    try:
        if tokens[token_index].lower() != "frames:":
            raise ValueError
        frame_count = int(tokens[token_index + 1])
        if tokens[token_index + 2].lower() != "frame" or tokens[token_index + 3].lower() != "time:":
            raise ValueError
        frame_time = float(tokens[token_index + 4])
    except (IndexError, ValueError):
        raise ValueError("Invalid BVH motion header: expected 'Frames:' and 'Frame Time:'.")
    return frame_count, frame_time, token_index + 5


def read_bvh_file(file_path):
    """Reads and parses a BVH file.

    Args:
        file_path (str): Path to a .bvh file.

    Returns:
        BvhData: Parsed hierarchy and motion.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as bvh_file:
        return parse_bvh_text(bvh_file.read())


def build_frame_times(frame_count, frame_time, scene_fps, start_frame=1.0, time_mode=TIME_MODE_REAL_TIME):
    """Builds the timeline frame for every BVH sample.

    Args:
        frame_count (int): Number of BVH frames.
        frame_time (float): Seconds per BVH frame.
        scene_fps (float): Scene frames per second.
        start_frame (float, optional): Timeline frame of the first sample.
        time_mode (str, optional): TIME_MODE_REAL_TIME keeps real-world timing (samples can land
            between frames when rates differ). TIME_MODE_FRAME_PER_FRAME puts one sample on every frame.

    Returns:
        list: One timeline frame per sample.
    """
    start_frame = float(start_frame)
    if time_mode == TIME_MODE_FRAME_PER_FRAME or frame_time <= 0 or scene_fps <= 0:
        return [start_frame + index for index in range(int(frame_count))]
    step = float(frame_time) * float(scene_fps)
    return [start_frame + index * step for index in range(int(frame_count))]


def get_bvh_file_info(file_path):
    """Reads basic BVH information without touching Maya.

    Args:
        file_path (str): Path to a .bvh file.

    Returns:
        dict: {"fps": float, "frame_count": int, "joint_count": int}, or an empty dict when unreadable.
    """
    try:
        bvh_data = read_bvh_file(file_path)
    except (IOError, OSError, ValueError) as exception:
        logger.debug(f'Unable to read BVH info from "{file_path}". Issue: {exception}')
        return {}
    return {"fps": bvh_data.fps, "frame_count": bvh_data.frame_count, "joint_count": len(bvh_data.joints)}


# ------------------------------------------------------------------ Maya runtime
def build_bvh_skeleton(
    bvh_data,
    namespace="",
    scale=1.0,
    start_frame=1.0,
    time_mode=TIME_MODE_REAL_TIME,
    include_end_sites=True,
    tangent_type="linear",
):
    """Builds an animated joint hierarchy from parsed BVH data.

    Args:
        bvh_data (BvhData): Parsed BVH data.
        namespace (str, optional): Namespace for the created nodes. Created when missing.
        scale (float, optional): Multiplier applied to offsets and position channels.
        start_frame (float, optional): Timeline frame of the first sample.
        time_mode (str, optional): One of TIME_MODES. See build_frame_times.
        include_end_sites (bool, optional): Create a joint for every "End Site".
        tangent_type (str, optional): Tangent type for the created keys.

    Returns:
        dict: {"root_joints": list, "joints": list, "curves": list, "time_range": tuple or None}.
    """
    import maya.cmds as cmds
    import maya.api.OpenMaya as open_maya
    import gt.core.anim as core_anim

    prefix = ""
    if namespace:
        if not cmds.namespace(exists=f":{namespace}"):
            cmds.namespace(add=namespace, parent=":")
        prefix = f"{namespace}:"
    scene_fps = open_maya.MTime(1.0, open_maya.MTime.kSeconds).asUnits(open_maya.MTime.uiUnit())
    frames = build_frame_times(bvh_data.frame_count, bvh_data.frame_time, scene_fps, start_frame, time_mode)
    joint_nodes = []
    created_curves = []
    for joint_index, bvh_joint in enumerate(bvh_data.joints):
        parent_node = joint_nodes[bvh_joint.parent_index] if bvh_joint.parent_index >= 0 else None
        create_kwargs = {"name": f"{prefix}{bvh_joint.name}", "skipSelect": True}
        if parent_node:
            create_kwargs["parent"] = parent_node
        joint_node = cmds.createNode("joint", **create_kwargs)
        joint_node = (cmds.ls(joint_node, long=True) or [joint_node])[0]
        cmds.setAttr(f"{joint_node}.translate", *[value * scale for value in bvh_joint.offset])
        cmds.setAttr(f"{joint_node}.rotateOrder", get_maya_rotate_order(bvh_joint.get_rotation_axes()))
        joint_nodes.append(joint_node)
        if include_end_sites and bvh_joint.end_site_offset is not None:
            end_node = cmds.createNode(
                "joint", name=f"{prefix}{bvh_joint.name}{END_SITE_SUFFIX}", parent=joint_node, skipSelect=True
            )
            cmds.setAttr(f"{end_node}.translate", *[value * scale for value in bvh_joint.end_site_offset])
        if not frames:
            continue
        for channel in bvh_joint.channels:
            lowered_channel = channel.lower()
            attribute_name = POSITION_CHANNELS.get(lowered_channel) or ROTATION_CHANNELS.get(lowered_channel)
            if not attribute_name:
                continue
            values = bvh_data.get_channel_values(joint_index, channel)
            if lowered_channel in POSITION_CHANNELS:
                values = [value * scale for value in values]
            curve = core_anim.create_keyed_curve(f"{joint_node}.{attribute_name}", frames, values, tangent_type)
            if curve:
                created_curves.append(curve)
    root_joints = [joint_nodes[index] for index, joint in enumerate(bvh_data.joints) if joint.parent_index < 0]
    root_joints = cmds.ls(root_joints, long=True) or root_joints
    all_joints = cmds.listRelatives(root_joints, allDescendents=True, type="joint", fullPath=True) or []
    time_range = (frames[0], frames[-1]) if frames else None
    return {
        "root_joints": root_joints,
        "joints": list(root_joints) + all_joints,
        "curves": created_curves,
        "time_range": time_range,
    }


def import_bvh_file(file_path, **build_kwargs):
    """Reads a BVH file and builds it in the current Maya scene.

    Args:
        file_path (str): Path to a .bvh file.
        **build_kwargs: Keyword arguments forwarded to build_bvh_skeleton.

    Returns:
        dict: Result of build_bvh_skeleton.
    """
    if not os.path.isfile(file_path):
        raise IOError(f"BVH file not found: {file_path}")
    return build_bvh_skeleton(read_bvh_file(file_path), **build_kwargs)
