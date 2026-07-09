"""
Animation Retargeter Addon: Patch
Pre-defined Addon scripts that can be applied by the user to the definition.
"""

import gt.tools.retargeter.retargeter_framework as tools_rt_frm
import gt.core.rig_switch as core_rig_switch
import gt.core.rigging as core_rigging
import gt.core.kinematics as core_kine
import gt.core.color as core_color
import gt.core.math as core_math
import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
import logging
import math

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AddonPatchXsensProportions(tools_rt_frm.TargetingAddon):
    """
    Analyses the Xsens source animation skeleton to match the legs proportions.
    Note: In addition to this patch, to match correctly the proportions, please make sure to have
    a scale value of 1 on the source:offset group in the scene.
    """

    __version__ = "0.0.2-alpha"
    allow_multiple = False

    def __init__(self):
        """
        Initiates the patch.
        """
        super().__init__(name="Xsens Proportions")
        self.execution_order = self.Order.pre_create_links
        self.active = False

    def set_active(self, active):
        """
        Sets the active state.
        Args:
            active (bool): The active state of the addon.
        """
        self.active = active

    def get_active(self):
        """
        Gets the active state for this addon.
        Returns:
            bool: The active state of the addon.
        """
        return self.active

    def apply_addon(self):
        """
        Runs the patch.
        Sets the skeleton leg proportions from the source xsens animation.
        """
        xsens_ref_namespace = "temp_xsens_source"
        source_offset_scale = cmds.getAttr(f"{self._source_namespace}:offset.sx")

        # Get the legs translation values from the source animation
        hips_y = cmds.getAttr(f"{self._source_namespace}:Hips.ty")
        cmds.file(self._source_path, reference=True, namespace=xsens_ref_namespace)
        r_upperleg_tx = cmds.getAttr(f"{xsens_ref_namespace}:RightUpLeg.tx") / source_offset_scale
        r_lowerleg_ty = cmds.getAttr(f"{xsens_ref_namespace}:RightLeg.ty") / source_offset_scale
        r_foot_ty = cmds.getAttr(f"{xsens_ref_namespace}:RightFoot.ty") / source_offset_scale
        l_upperleg_tx = -r_upperleg_tx
        l_lowerleg_ty = r_lowerleg_ty
        l_foot_ty = r_foot_ty
        cmds.file(self._source_path, removeReference=True)

        # Set leg proportion values
        prev_lowerleg_ty = cmds.getAttr(f"{self._source_namespace}:RightLeg.ty")
        prev_foot_ty = cmds.getAttr(f"{self._source_namespace}:RightFoot.ty")
        cmds.setAttr(f"{self._source_namespace}:RightUpLeg.tx", r_upperleg_tx)
        cmds.setAttr(f"{self._source_namespace}:RightLeg.ty", r_lowerleg_ty)
        cmds.setAttr(f"{self._source_namespace}:RightFoot.ty", r_foot_ty)
        cmds.setAttr(f"{self._source_namespace}:LeftUpLeg.tx", l_upperleg_tx)
        cmds.setAttr(f"{self._source_namespace}:LeftLeg.ty", l_lowerleg_ty)
        cmds.setAttr(f"{self._source_namespace}:LeftFoot.ty", l_foot_ty)

        # Restore Initial Hips
        cmds.setAttr(f"{self._source_namespace}:Hips.ty", hips_y)

        # TODO: the below could be improved getting the hips t-pose ty from the source animation
        #       and finding the difference with the source reference skeleton. Unfortunately
        #       the t-pose from the animation it could be not so straight forward to obtain.
        """ Deprecated - retargeting with legs in IK the adjustment doesn't improve anything  
        # Adjust the height based on the new leg length
        prev_leg_length = prev_lowerleg_ty + prev_foot_ty
        xsens_anim_leg_length = r_lowerleg_ty + r_foot_ty
        length_diff = -((xsens_anim_leg_length - prev_leg_length) / source_offset_scale)
        prev_offset_ty = cmds.getAttr(f"{self._source_namespace}:offset.ty")
        new_ty_value = prev_offset_ty + length_diff
        cmds.setAttr(f"{self._source_namespace}:offset.ty", new_ty_value)
        """


class AddonPatchXsensPoleVector(tools_rt_frm.TargetingAddon):
    """
    Fixes the pole vector animation removing pops due to the overstretch of the limbs (combined arms and legs),
    finding the correct location that stabilizes the IK solver.
    Note: The target rig limbs need to be set in IK before running the patch.
    """

    __version__ = "0.0.3"
    allow_multiple = False

    def __init__(self):
        """
        Initiates the patch.
        """
        super().__init__(name="Xsens Pole Vector")
        self.execution_order = self.Order.post_retarget
        self.active = False

        # Instance variables to toggle arm and leg patches individually
        self.patch_arms = True
        self.patch_legs = False

    def set_active(self, active):
        """
        Sets the active state.
        Args:
            active (bool): The active state of the addon.
        """
        self.active = active

    def get_active(self):
        """
        Gets the active state for this addon.
        Returns:
            bool: The active state of the addon.
        """
        return self.active

    def set_patch_arms(self, active):
        """
        Sets whether the arm pole vector patch should run.
        Args:
            active (bool): The active state for the arm patch.
        """
        self.patch_arms = active

    def set_patch_legs(self, active):
        """
        Sets whether the leg pole vector patch should run.
        Args:
            active (bool): The active state for the leg patch.
        """
        self.patch_legs = active

    def apply_addon(self):
        """
        Runs a pole vector patch for the arms and legs.
        """
        # =========================================================================
        # CONTROL FLAGS
        # =========================================================================
        _debug = False  # Create visual debug items to analyze the solver.
        _leg_patch = self.patch_legs  # Tied to instance variable
        _arm_patch = self.patch_arms  # Tied to instance variable
        _switch = True  # Toggle to run the FK/IK Switch (Bake) function at the very end of the process.

        # =========================================================================
        # CONFIGURATION
        # =========================================================================
        source_ns = self._source_namespace
        ref_frame = 0  # The reference frame (usually 0) used to learn bone lengths and offsets (T-Pose).

        # --- ARMS CONFIG ---
        pv_distance = 35.0  # How far the Arm Pole Vector control is pushed out from the elbow.
        arm_smoothing = 0.5  # Smoothing factor (0.0 = No smoothing, 1.0 = Frozen). Reduces jitter.
        geo_blend_range = (5.0, 15.0)  # Elbow vs ideal plane. Blend Geometric Normal and T-Pose Normal.
        activation_range = (2.0, 8.0)  # Original Animation vs Solver.
        # Activation: If the elbow is very close to the straight line (2.0), we trust the original animation more.

        # --- LEG PV SETTINGS ---
        offset_return_speed = 0.05  # Speed (0.0 to 1.0) at which the foot offset drifts back to the original offset.
        leg_pv_push = 45.0  # How far the Leg Pole Vector control is pushed out from the knee.
        leg_straight_threshold = 0.5  # If distance from hip-foot line to knee is less then, it's considered "Straight".
        leg_activation_min_angle = 10.0  # Min Angle (Degrees) Math Calculated vs Original Animation PV. Fixes Jitter.
        leg_activation_max_angle = 45.0  # > Max Angle (Degrees) Prevents flipping on extreme poses.

        speed_limit_factor = 2.0  # Elastic Velocity Clamp for the PV Control itself.  How much faster than original.
        min_speed_allowance = 0.5  # Minimum movement allowed per frame for the PV, regardless of the speed limit.

        # --- DATA DEFINITIONS ---
        limbs_config = {
            "L_lowerArm_IK_CTRL": ["LeftArm", "LeftForeArm", "LeftHand"],
            "R_lowerArm_IK_CTRL": ["RightArm", "RightForeArm", "RightHand"],
        }

        legs_config = {
            "L_foot_IK_CTRL": {
                "source": "LeftFoot",
                "source_knee": "LeftLeg",
                "fk_ref": "L_foot_CTRL",
                "pv_ctrl": "L_lowerLeg_IK_CTRL",
                "chain": ["L_upperLeg_JNT", "L_lowerLeg_JNT", "L_foot_JNT"],
            },
            "R_foot_IK_CTRL": {
                "source": "RightFoot",
                "source_knee": "RightLeg",
                "fk_ref": "R_foot_CTRL",
                "pv_ctrl": "R_lowerLeg_IK_CTRL",
                "chain": ["R_upperLeg_JNT", "R_lowerLeg_JNT", "R_foot_JNT"],
            },
        }

        snap_list = [
            "Spine : C_hips_JNT : position, world Y only",
            "Spine1 : C_spine01_JNT : position, world Y only",
            "Spine2 : C_spine02_JNT : position, world Y only",
            "Spine3 : C_spine03_JNT : position, world Y only",
            "LeftShoulder : L_clavicle_JNT : position (X, Y, Z)",
            "LeftArm : L_upperArm_JNT : position (X, Y, Z)",
            "LeftForeArm : L_lowerArm_JNT : position (X, Y, Z)",
            "LeftHand : L_hand_JNT : position (X, Y, Z)",
            "RightShoulder : R_clavicle_JNT : position (X, Y, Z)",
            "RightArm : R_upperArm_JNT : position (X, Y, Z)",
            "RightForeArm : R_lowerArm_JNT : position (X, Y, Z)",
            "RightHand : R_hand_JNT : position (X, Y, Z)",
            "Neck : C_neck01_JNT : position (X, Y, Z)",
        ]

        # =========================================================================
        # PRE-COMPUTATION
        # =========================================================================
        self.parse_and_snap(snap_list, frame=ref_frame)

        start_frame = int(cmds.playbackOptions(q=True, min=True))
        end_frame = int(cmds.playbackOptions(q=True, max=True)) + 1

        cmds.waitCursor(state=True)
        initial_autokey = cmds.autoKeyframe(q=True, state=True)
        cmds.autoKeyframe(state=False)

        arm_history = {}
        arm_biases = {}
        active_limbs = []

        leg_static_data = {}
        leg_offsets = {}
        leg_history_vec = {}
        leg_prev_orig_pos = {}
        leg_prev_final_pos = {}
        leg_runtime_data = {}
        leg_prev_dist_val = {}

        active_legs = []

        # Debug Group Setup
        debug_grp = "PATCH_DEBUG_ITEMS"
        if _debug:
            if cmds.objExists(debug_grp):
                cmds.delete(debug_grp)
            cmds.group(empty=True, name=debug_grp)
            core_color.set_color_outliner(obj_list=debug_grp, rgb_color=(1, 0, 0))

        cmds.refresh(suspend=False)

        try:
            # --- SETUP COMPONENTS ---
            logger.info("Initializing Components...")

            rig_ns = ""
            sample_ctrl = core_rigging.find_control("L_foot_IK_CTRL", source_ns)
            if sample_ctrl:
                rig_ns = sample_ctrl.split(":")[0].split("|")[-1]

            # Setup Arms
            if _arm_patch:
                for ctrl_suffix, data in limbs_config.items():
                    ctrl = core_rigging.find_control(ctrl_suffix, source_ns)
                    if not ctrl:
                        continue
                    active_limbs.append(
                        {
                            "ctrl": ctrl,
                            "root": f"{source_ns}:{data[0]}",
                            "mid": f"{source_ns}:{data[1]}",
                            "end": f"{source_ns}:{data[2]}",
                            "name": ctrl_suffix,
                        }
                    )
                    arm_history[ctrl_suffix] = None

            # Setup Legs
            if _leg_patch:
                for ctrl_suffix, data in legs_config.items():
                    ctrl = core_rigging.find_control(ctrl_suffix, source_ns)
                    fk_ref_ctrl = core_rigging.find_control(data["fk_ref"], source_ns)
                    pv_ctrl = core_rigging.find_control(data["pv_ctrl"], source_ns)
                    source_obj = f"{source_ns}:{data['source']}"
                    source_knee_name = f"{source_ns}:{data['source_knee']}"

                    hip = core_rigging.find_joint(data["chain"][0], rig_ns)
                    knee = core_rigging.find_joint(data["chain"][1], rig_ns)
                    foot = core_rigging.find_joint(data["chain"][2], rig_ns)

                    if not ctrl or not fk_ref_ctrl or not pv_ctrl or not cmds.objExists(source_obj):
                        continue

                    active_legs.append(
                        {
                            "ctrl": ctrl,
                            "fk_ref": fk_ref_ctrl,
                            "pv_ctrl": pv_ctrl,
                            "source": source_obj,
                            "source_knee": source_knee_name,
                            "hip": hip,
                            "knee": knee,
                            "foot": foot,
                            "name": ctrl_suffix,
                        }
                    )
                    leg_runtime_data[ctrl_suffix] = {"current_offset": None}
                    leg_history_vec[ctrl_suffix] = None
                    leg_prev_orig_pos[ctrl_suffix] = None
                    leg_prev_final_pos[ctrl_suffix] = None
                    leg_prev_dist_val[ctrl_suffix] = None

                    # Create Debug Locators
                    if _debug:
                        loc_name = f"{ctrl_suffix}_ORIGINAL_DEBUG"
                        if not cmds.objExists(loc_name):
                            loc = cmds.spaceLocator(n=loc_name)[0]
                            cmds.parent(loc, debug_grp)
                            cmds.setAttr(loc + "Shape.overrideEnabled", 1)
                            cmds.setAttr(loc + "Shape.overrideColor", 13)  # Red

                        loc_final = f"{ctrl_suffix}_FINAL_DEBUG"
                        if not cmds.objExists(loc_final):
                            loc = cmds.spaceLocator(n=loc_final)[0]
                            cmds.parent(loc, debug_grp)
                            cmds.setAttr(loc + "Shape.overrideEnabled", 1)
                            cmds.setAttr(loc + "Shape.overrideColor", 6)  # Blue

            # --- LEARNING PHASE (Frame 0) ---
            logger.info(f"Learning Data from Frame {ref_frame}...")
            cmds.currentTime(ref_frame)

            # Learn Arms (Using original helper)
            if _arm_patch:
                for limb in active_limbs:
                    bias = core_kine.get_local_bias(limb["root"], limb["mid"], limb["end"], frame=ref_frame)
                    arm_biases[limb["name"]] = bias

            # Learn Legs
            if _leg_patch:
                for leg in active_legs:
                    p_hip = core_math.get_mvector(leg["hip"])
                    p_knee = core_math.get_mvector(leg["knee"])
                    p_foot = core_math.get_mvector(leg["foot"])
                    p_pv = core_math.get_mvector(leg["pv_ctrl"])

                    src_geo_vec, _ = core_math.get_bend_vector(p_hip, p_knee, p_foot)
                    ctrl_geo_vec, _ = core_math.get_bend_vector(p_hip, p_pv, p_foot)
                    offset_quat = core_math.get_rotation_from_vectors(src_geo_vec, ctrl_geo_vec)
                    leg_offsets[leg["name"]] = offset_quat

                    p_ctrl = core_math.get_mvector(leg["ctrl"])
                    p_src = core_math.get_mvector(leg["source"])
                    offset = p_ctrl - p_src

                    leg_static_data[leg["name"]] = {"initial_offset": offset}

            # =========================================================================
            # EXECUTION PHASE
            # =========================================================================
            logger.info("Running Combined Solver...")

            for f in range(start_frame, end_frame):
                if f == ref_frame:
                    continue
                cmds.currentTime(f)

                # ----------------------------------
                # PART A: ARM PV SOLVER (ORIGINAL LOGIC RESTORED)
                # ----------------------------------
                if _arm_patch:
                    for limb in active_limbs:
                        bias = arm_biases.get(limb["name"])

                        # Get Current Pos for Activation
                        current_ctrl_pos = core_math.get_mvector(limb["ctrl"])

                        prev = arm_history.get(limb["name"])
                        if f == start_frame:
                            prev = None

                        final_pos, new_vec = core_kine.calculate_biased_pv(
                            root=limb["root"],
                            mid=limb["mid"],
                            end_pos=core_math.get_mvector(limb["end"]),
                            local_bias=bias,
                            prev_vec=prev,
                            original_pos=current_ctrl_pos,
                            activation_range=activation_range,
                            smoothing=arm_smoothing,
                            pv_dist=pv_distance,
                            geometry_blend_range=geo_blend_range,
                            strict_snap=False,
                        )
                        arm_history[limb["name"]] = new_vec
                        if final_pos:
                            cmds.xform(limb["ctrl"], ws=True, t=(final_pos.x, final_pos.y, final_pos.z))
                            cmds.setKeyframe(limb["ctrl"], at="translate")

                # ----------------------------------
                # PART B: LEG SOLVER
                # ----------------------------------
                if _leg_patch:
                    for leg in active_legs:
                        runtime = leg_runtime_data[leg["name"]]

                        # --- DEBUG: Capture Original PV Position (RED) ---
                        orig_pv_pos = core_math.get_mvector(leg["pv_ctrl"])
                        if _debug:
                            loc_name = f"{leg['name']}_ORIGINAL_DEBUG"
                            cmds.xform(loc_name, ws=True, t=(orig_pv_pos.x, orig_pv_pos.y, orig_pv_pos.z))
                            cmds.setKeyframe(loc_name, at="translate")

                        # --- 1. FOOT SOLVER (SIMPLE FOLLOW) ---
                        src_pos = core_math.get_mvector(leg["source"])
                        current_offset = runtime["current_offset"]
                        if current_offset is None:
                            current_offset = leg_static_data[leg["name"]]["initial_offset"]
                        drifted_offset = (current_offset * (1.0 - offset_return_speed)) + (
                                leg_static_data[leg["name"]]["initial_offset"] * offset_return_speed
                        )
                        final_foot_pos = src_pos + drifted_offset

                        cmds.xform(leg["ctrl"], ws=True, t=(final_foot_pos.x, final_foot_pos.y, final_foot_pos.z))
                        cmds.setKeyframe(leg["ctrl"], at="translate")
                        runtime["current_offset"] = final_foot_pos - src_pos

                        # --- 2. KNEE PV SOLVER (GEOMETRIC + VELOCITY LIMIT) ---
                        hip_pos = core_math.get_mvector(leg["hip"])
                        src_knee_pos = core_math.get_mvector(leg["source_knee"])

                        # A. Geometric Calculation
                        src_bend_vec, src_bend_mag = core_math.get_bend_vector(hip_pos, src_knee_pos, final_foot_pos)
                        prev_vec = leg_history_vec.get(leg["name"])
                        if f == start_frame:
                            prev_vec = None

                        final_vec = None
                        if src_bend_mag < leg_straight_threshold:
                            if prev_vec:
                                final_vec = prev_vec
                            else:
                                final_vec = src_bend_vec
                        else:
                            offset = leg_offsets.get(leg["name"], OpenMaya.MQuaternion())
                            final_vec = src_bend_vec.rotateBy(offset)

                        # B. Activation (Blend with Original)
                        line_proj = core_math.get_closest_point_on_segment(orig_pv_pos, hip_pos, final_foot_pos)
                        vec_orig = (orig_pv_pos - line_proj).normal()

                        dot = max(-1.0, min(1.0, final_vec * vec_orig))
                        angle_diff = math.degrees(math.acos(dot))

                        blend_factor = 0.0
                        if angle_diff >= leg_activation_max_angle:
                            blend_factor = 1.0
                        elif angle_diff > leg_activation_min_angle:
                            blend_factor = (angle_diff - leg_activation_min_angle) / (
                                    leg_activation_max_angle - leg_activation_min_angle
                            )

                        if blend_factor > 0.001:
                            final_vec = (final_vec * (1.0 - blend_factor)) + (vec_orig * blend_factor)
                            final_vec.normalize()

                        # Project Final Ideal Position
                        rig_midpoint = (hip_pos + final_foot_pos) * 0.5
                        ideal_pv_pos = rig_midpoint + (final_vec * leg_pv_push)
                        leg_history_vec[leg["name"]] = final_vec

                        # C. Velocity Clamp (PV Only)
                        final_clamped_pos = ideal_pv_pos
                        prev_orig = leg_prev_orig_pos.get(leg["name"])
                        prev_final = leg_prev_final_pos.get(leg["name"])

                        if f > start_frame and prev_orig and prev_final:
                            orig_speed = (orig_pv_pos - prev_orig).length()
                            max_speed = (orig_speed * speed_limit_factor) + min_speed_allowance
                            proposed_speed = (ideal_pv_pos - prev_final).length()
                            if proposed_speed > max_speed:
                                travel_dir = (ideal_pv_pos - prev_final).normal()
                                final_clamped_pos = prev_final + (travel_dir * max_speed)

                        leg_prev_orig_pos[leg["name"]] = orig_pv_pos
                        leg_prev_final_pos[leg["name"]] = final_clamped_pos

                        # Debug Blue
                        if _debug:
                            loc_name_final = f"{leg['name']}_FINAL_DEBUG"
                            cmds.xform(
                                loc_name_final,
                                ws=True,
                                t=(final_clamped_pos.x, final_clamped_pos.y, final_clamped_pos.z),
                            )
                            cmds.setKeyframe(loc_name_final, at="translate")

                        if final_clamped_pos:
                            cmds.xform(
                                leg["pv_ctrl"],
                                ws=True,
                                t=(final_clamped_pos.x, final_clamped_pos.y, final_clamped_pos.z),
                            )
                            cmds.setKeyframe(leg["pv_ctrl"], at="translate")

        except Exception as e:
            logger.error(f"Error: {e}")
            import traceback

            traceback.print_exc()
        finally:
            cmds.autoKeyframe(state=initial_autokey)
            cmds.waitCursor(state=False)
            cmds.refresh(suspend=False)
            logger.info("Retarget Pole Vector Patch Applied.")

        # ------------ Transfer to FK for consistency (Optional Switch) ------------
        if _switch:
            try:
                cmds.refresh(suspend=True)
                sample_ctrl = core_rigging.find_control(target_suffix="L_foot_IK_CTRL", ignore_namespace="source")
                if sample_ctrl:
                    rig_namespace = sample_ctrl.split(":")[0].replace("|", "")
                    start_frame = int(cmds.playbackOptions(q=True, animationStartTime=True))
                    end_frame = int(cmds.playbackOptions(q=True, animationEndTime=True)) + 2

                    switch_dicts = core_rig_switch.get_switch_dictionaries_from_types(
                        ["biped_right_arm", "biped_left_arm", "biped_left_leg", "biped_right_leg"]
                    )

                    core_rig_switch.fk_ik_switch(
                        switch_dicts,
                        direction="ik_to_fk",
                        namespace=rig_namespace,
                        keyframe=True,
                        start_time=start_frame,
                        end_time=end_frame,
                        method="bake",
                    )
            except Exception as e:
                logger.error(f"Error during FK Bake: {e}")
                import traceback

                traceback.print_exc()
            finally:
                cmds.refresh(suspend=False)

    # -----------------------------------------------------------------------------
    # UTILITIES
    # -----------------------------------------------------------------------------
    @staticmethod
    def parse_and_snap(snap_data_list, frame=0):
        """
        Parses a list of formatted strings to snap source nodes to target nodes.

        Sets the current Maya time to the specified frame, resolves actual node names
        by searching for suffixes, and applies the snapping logic (e.g., point, orient,
        or parent constraint styles) defined in the data list.

        Args:
            snap_data_list (list[str]): A list of instructions where each string
                is formatted as "source_suffix : target_suffix : mode".
                For example: "fk_ctrl : ik_ctrl : point".
            frame (int, optional): The frame number to set the timeline to before
                processing the list. Defaults to 0.
        """
        cmds.currentTime(frame)
        logger.info(f"--- Snapping Skeleton at Frame {frame} ---")

        for line in snap_data_list:
            if not line.strip():
                continue
            parts = [p.strip() for p in line.split(" : ")]
            if len(parts) < 3:
                continue

            src_name, tgt_name, mode = parts[0], parts[1], parts[2].lower()
            src_node = core_rigging.find_node_by_suffix(src_name)
            tgt_node = core_rigging.find_node_by_suffix(tgt_name)

            if not src_node or not tgt_node:
                continue

            core_rigging.snap_node(src_node, tgt_node, mode)


if __name__ == "__main__":
    patch = AddonPatchXsensPoleVector()
    patch._source_namespace = "source"

    # Toggle them as needed before running
    patch.set_patch_arms(True)
    patch.set_patch_legs(False)

    patch.apply_addon()
    # cmds.setAttr("target:L_leg_CTRL.influenceSwitch", 1)
    # cmds.setAttr("target:R_leg_CTRL.influenceSwitch", 1)
