"""
Kinematics / Solvers / Motion

Import Line:
    import gt.core.kinematics as core_kine
"""

import gt.core.math as core_math
import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_local_bias(root, mid, end, frame=0):
    """
    Calculates ideal geometric normal (Triangle Normal) relative to the root.

    Args:
        root (str): Root joint name.
        mid (str): Middle joint name.
        end (str): End joint name.
        frame (int): Frame to query.

    Returns:
        OpenMaya.MVector: The normal vector in the root's local space.
    """
    cmds.currentTime(frame)
    pos_root = core_math.get_mvector(root)
    pos_mid = core_math.get_mvector(mid)
    pos_end = core_math.get_mvector(end)

    root_to_end = pos_end - pos_root
    chain_len_sq = root_to_end * root_to_end

    if chain_len_sq < 0.001:
        return OpenMaya.MVector(0, 0, -1)

    t = (pos_mid - pos_root) * root_to_end / chain_len_sq
    projection_point = pos_root + (root_to_end * t)
    world_vec = (pos_mid - projection_point).normal()

    root_mat = core_math.get_matrix(root)
    root_inverse = root_mat.inverse()

    return world_vec * root_inverse


def get_pure_knee_vector(knee_node, pv_ctrl_node, frame=0):
    """
    Learns the local forward axis of the knee/elbow relative to the pole vector.

    Args:
        knee_node (str): The knee or elbow joint.
        pv_ctrl_node (str): The pole vector control.
        frame (int): Frame to query.

    Returns:
        OpenMaya.MVector: The local vector.
    """
    cmds.currentTime(frame)
    pos_knee = core_math.get_mvector(knee_node)
    pos_pv = core_math.get_mvector(pv_ctrl_node)

    world_vec = (pos_pv - pos_knee).normal()
    knee_mat = core_math.get_matrix(knee_node)
    knee_inverse = knee_mat.inverse()

    return world_vec * knee_inverse


def calculate_biased_pv(
    root,
    mid,
    end_pos,
    local_bias,
    prev_vec,
    original_pos=None,
    activation_range=(3.0, 10.0),
    smoothing=0.5,
    pv_dist=35.0,
    geometry_blend_range=(5.0, 15.0),
    strict_snap=False,
    knee_local_vec=None,
    knee_world_matrix=None,
    source_vec_current=None,
    source_vec_prev=None,
):
    """
    Calculates Pole Vector using Temporal Consistency and Adaptive Smoothing.

    Args:
        root (str): Root node name.
        mid (str): Middle node name.
        end_pos (OpenMaya.MVector): World position of the end effector.
        local_bias (OpenMaya.MVector): The preferred local normal direction.
        prev_vec (OpenMaya.MVector): The calculated vector from the previous frame.
        original_pos (OpenMaya.MVector, optional): Original PV position for blending.
        activation_range (tuple): Distance range for activation blending.
        smoothing (float): Base smoothing factor (0.0 to 1.0).
        pv_dist (float): Distance to push the PV out.
        geometry_blend_range (tuple): Range to blend between Geometry and Ideal.
        strict_snap (bool): If True, ignores original_pos and snaps strictly.
        knee_local_vec (OpenMaya.MVector): For legs, local knee orientation.
        knee_world_matrix (OpenMaya.MMatrix): World matrix of the knee.
        source_vec_current (OpenMaya.MVector): Current frame thigh vector.
        source_vec_prev (OpenMaya.MVector): Previous frame thigh vector.

    Returns:
        tuple: (OpenMaya.MVector final_position, OpenMaya.MVector final_direction)
    """
    pos_root = core_math.get_mvector(root)
    pos_mid = core_math.get_mvector(mid)
    pos_end = end_pos

    root_to_end = pos_end - pos_root
    chain_len_sq = root_to_end * root_to_end

    if chain_len_sq < 0.001:
        return (original_pos if original_pos else pos_mid), prev_vec

    # 1. Geometric Data
    t = (pos_mid - pos_root) * root_to_end / chain_len_sq
    projection_point = pos_root + (root_to_end * t)

    raw_vec_geo = pos_mid - projection_point
    dist_from_line = raw_vec_geo.length()

    # 2. Safe T-Pose Reference
    root_mat = core_math.get_matrix(root)
    ideal_dir = local_bias * root_mat
    ideal_dir.normalize()

    final_dir = ideal_dir  # Default

    # =========================================================================
    # LOGIC BRANCH
    # =========================================================================

    if strict_snap and knee_local_vec and knee_world_matrix:
        # --- LEG LOGIC: TEMPORAL STABILITY ---

        rot_dir = knee_local_vec * knee_world_matrix
        rot_dir.normalize()

        if dist_from_line > 0.001:
            geo_dir = raw_vec_geo.normal()
        else:
            geo_dir = rot_dir

            # Align to History
        if prev_vec:
            if (geo_dir * prev_vec) < 0.0:
                geo_dir *= -1.0
            if (rot_dir * prev_vec) < 0.0:
                rot_dir *= -1.0
        else:
            if (geo_dir * rot_dir) < 0.0:
                geo_dir *= -1.0

        # Blend Factors
        BLEND_MIN = 1.0
        BLEND_MAX = 5.0

        geo_weight = 0.0
        if dist_from_line >= BLEND_MAX:
            geo_weight = 1.0
        elif dist_from_line > BLEND_MIN:
            geo_weight = (dist_from_line - BLEND_MIN) / (BLEND_MAX - BLEND_MIN)

        merged_dir = (geo_dir * geo_weight) + (rot_dir * (1.0 - geo_weight))
        merged_dir.normalize()

        # Adaptive Smoothing
        current_smoothing = smoothing

        if prev_vec and source_vec_current and source_vec_prev:
            src_vel = core_math.get_angle(source_vec_current, source_vec_prev)
            calc_vel = core_math.get_angle(merged_dir, prev_vec)
            allowed_vel = src_vel + 2.0

            if calc_vel > allowed_vel:
                excess = calc_vel - allowed_vel
                dampening = min(1.0, excess / 10.0)
                current_smoothing = core_math.lerp(smoothing, 0.98, dampening)

        if prev_vec:
            final_dir = (merged_dir * (1.0 - current_smoothing)) + (prev_vec * current_smoothing)
            final_dir.normalize()
        else:
            final_dir = merged_dir

    else:
        # --- ARM LOGIC ---
        geo_dir = raw_vec_geo.normal()
        if dist_from_line < 0.01:
            geo_dir = ideal_dir

        final_geo_dir = OpenMaya.MVector(geo_dir)
        if prev_vec:
            if (final_geo_dir * prev_vec) < 0:
                final_geo_dir *= -1.0
        else:
            if dist_from_line <= geometry_blend_range[0]:
                if (final_geo_dir * ideal_dir) < 0:
                    final_geo_dir *= -1.0

        min_blend, max_blend = geometry_blend_range
        geo_blend_factor = 0.0
        if dist_from_line >= max_blend:
            geo_blend_factor = 1.0
        elif dist_from_line > min_blend:
            geo_blend_factor = (dist_from_line - min_blend) / (max_blend - min_blend)

        final_dir = (final_geo_dir * geo_blend_factor) + (ideal_dir * (1.0 - geo_blend_factor))
        final_dir.normalize()

        if prev_vec and smoothing > 0.001:
            final_dir = (final_dir * smoothing) + (prev_vec * (1.0 - smoothing))
            final_dir.normalize()

    # =========================================================================

    if strict_snap:
        computed_pos = pos_mid + (final_dir * pv_dist)
    else:
        computed_pos = projection_point + (final_dir * (dist_from_line + pv_dist))

    final_output_pos = computed_pos
    if original_pos and not strict_snap:
        min_act, max_act = activation_range
        activation_alpha = 0.0
        if dist_from_line >= max_act:
            activation_alpha = 1.0
        elif dist_from_line <= min_act:
            activation_alpha = 0.0
        else:
            activation_alpha = (dist_from_line - min_act) / (max_act - min_act)

        final_output_pos = (computed_pos * activation_alpha) + (original_pos * (1.0 - activation_alpha))

    return final_output_pos, final_dir
