"""
System switching utilities

TODO: Rework the part of the code hardcoded for the biped.

Import Line:
    import gt.core.core_rig_switch as core_rig_switch
"""

import maya.cmds as cmds
import traceback
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# Constants
SWITCH_ATTR = "influenceSwitch"


class SwitchDirections:
    auto = "auto"
    fk_to_ik = "fk_to_ik"
    ik_to_fk = "ik_to_fk"
    snap_ik_pole_to_fk = "snap_ik_pole_to_fk"

    @staticmethod
    def get_switch_directions():
        """
        Gets all available directions in a list.
        Returns:
            list: list of available directions.
        """
        directions_list = []
        for n, v in vars(SwitchDirections).items():
            if isinstance(v, str):
                if not n.startswith("__"):
                    directions_list.append(v)
        return directions_list


class SwitchPairs:
    """
    Switch data class organized in types.
    For example, the biped_left_arm variable is a switch-type with the data to perform
    the switch operation (pairs of elements) for a specific part of the biped.
    """

    biped_left_arm = {
        "switch_ctrl": "L_arm_CTRL",  # Switch Ctrl
        "end_ik_ctrl": "L_hand_IK_CTRL",  # IK Elements
        "pvec_ik_ctrl": "L_lowerArm_IK_CTRL",
        "base_ik_ref": "L_upperArmFkOffsetRef_loc",
        "mid_ik_ref": "L_lowerArmFkOffsetRef_loc",
        "end_ik_ref": "L_handFkOffsetRef_loc",
        "base_fk_ctrl": "L_upperArm_CTRL",  # FK Elements
        "mid_fk_ctrl": "L_lowerArm_CTRL",
        "end_fk_ctrl": "L_hand_CTRL",
        "base_fk_jnt": "L_shoulder_fk_jnt",  # L_shoulder_fk_jnt
        "mid_fk_jnt": "L_elbow_fk_jnt",  # L_elbow_fk_jnt
        "end_fk_jnt": "L_wrist_fk_jnt",  # L_wrist_fk_jnt
        "mid_ik_reference": "L_lowerArmSwitch_loc",
        "end_ik_reference": "L_handSwitch_loc",
    }

    biped_right_arm = {
        "switch_ctrl": "R_arm_CTRL",  # Switch Ctrl
        "end_ik_ctrl": "R_hand_IK_CTRL",  # IK Elements
        "pvec_ik_ctrl": "R_lowerArm_IK_CTRL",
        "base_ik_ref": "R_upperArmFkOffsetRef_loc",
        "mid_ik_ref": "R_lowerArmFkOffsetRef_loc",
        "end_ik_ref": "R_handFkOffsetRef_loc",
        "base_fk_ctrl": "R_upperArm_CTRL",  # FK Elements
        "mid_fk_ctrl": "R_lowerArm_CTRL",
        "end_fk_ctrl": "R_hand_CTRL",
        "base_fk_jnt": "R_shoulder_fk_jnt",  # R_shoulder_fk_jnt
        "mid_fk_jnt": "R_elbow_fk_jnt",  # R_elbow_fk_jnt
        "end_fk_jnt": "R_wrist_fk_jnt",  # R_wrist_fk_jnt
        "mid_ik_reference": "R_lowerArmSwitch_loc",
        "end_ik_reference": "R_handSwitch_loc",
    }

    biped_left_leg = {
        "switch_ctrl": "L_leg_CTRL",  # Switch Ctrl
        "end_ik_ctrl": "L_foot_IK_CTRL",  # IK Elements
        "pvec_ik_ctrl": "L_lowerLeg_IK_CTRL",
        "base_ik_ref": "L_upperLegFkOffsetRef_loc",
        "mid_ik_ref": "L_lowerLegFkOffsetRef_loc",
        "end_ik_ref": "L_footFkOffsetRef_loc",
        "base_fk_ctrl": "L_upperLeg_CTRL",  # FK Elements
        "mid_fk_ctrl": "L_lowerLeg_CTRL",
        "end_fk_ctrl": "L_foot_CTRL",
        "base_fk_jnt": "L_upperLeg_JNT_fk",
        "mid_fk_jnt": "L_lowerLeg_JNT_fk",
        "end_fk_jnt": "L_foot_JNT_fk",
        "mid_ik_reference": "L_lowerLegSwitch_loc",
        "end_ik_reference": "L_footSwitch_loc",
        "incompatible_attr_holder": "",
        "auxiliary_fk_ball": "L_ball_CTRL",
        "auxiliary_ik_ball": "L_toe_IK_CTRL",
        "auxiliary_roll_ball_ref": "L_ballFkOffsetRef_loc",
        "auxiliary_fk_ball_ref": "L_ballSwitch_loc",
    }

    biped_right_leg = {
        "switch_ctrl": "R_leg_CTRL",  # Switch Ctrl
        "end_ik_ctrl": "R_foot_IK_CTRL",  # IK Elements
        "pvec_ik_ctrl": "R_lowerLeg_IK_CTRL",
        "base_ik_ref": "R_upperLegFkOffsetRef_loc",
        "mid_ik_ref": "R_lowerLegFkOffsetRef_loc",
        "end_ik_ref": "R_footFkOffsetRef_loc",
        "base_fk_ctrl": "R_upperLeg_CTRL",  # FK Elements
        "mid_fk_ctrl": "R_lowerLeg_CTRL",
        "end_fk_ctrl": "R_foot_CTRL",
        "base_fk_jnt": "R_upperLeg_JNT_fk",
        "mid_fk_jnt": "R_lowerLeg_JNT_fk",
        "end_fk_jnt": "R_foot_JNT_fk",
        "mid_ik_reference": "R_lowerLegSwitch_loc",
        "end_ik_reference": "R_footSwitch_loc",
        "incompatible_attr_holder": "",
        "auxiliary_fk_ball": "R_ball_CTRL",
        "auxiliary_ik_ball": "R_toe_IK_CTRL",
        "auxiliary_roll_ball_ref": "R_ballFkOffsetRef_loc",
        "auxiliary_fk_ball_ref": "R_ballSwitch_loc",
    }

    @staticmethod
    def get_switch_pairs():
        """
        Gets all available pairs as a dictionary of dictionaries.
        The main dictionary has the type name as key and the pairs dictionary as value.
        Returns:
            dict: Dictionary of dictionaries in which there are the available pairs.
                  e.g. {'biped_left_arm': {'switch_ctrl': 'L_arm_CTRL', ... }}
        """
        return {n: v for n, v in vars(SwitchPairs).items() if isinstance(v, dict)}


class SwitchCombination:
    """The switch combination is an object defined by a switch direction and a switch type."""

    direction_key = "direction"
    switch_type_key = "switch_type"

    def __init__(self, direction=None, switch_type=None):
        """
        Args:
            direction (str, optional): Either "fk_to_ik" or "ik_to_fk".
            switch_type  (str, optional): switch type, for example: "biped_right_leg".
        """
        self.direction = "fk_to_ik"  # "fk_to_ik" or "ik_to_fk". It determines source and target for the switch.
        self.switch_type = None

        self.set_direction(direction)
        self.set_switch_type(switch_type)

    def set_direction(self, direction):
        """
        Sets the direction of the switch between kinematics.
        Args:
            direction (str, optional): Either "fk_to_ik" or "ik_to_fk".
                                          It determines what is the source and what is the target.
        """
        if not isinstance(direction, str):
            logger.warning("Cannot set the given direction, it is not a string.")
            return

        self.direction = direction

    def set_switch_type(self, switch_type):
        """
        Sets the switch type.
        Args:
            switch_type (str): switch type, for example: "biped_right_leg".
        """
        if not isinstance(switch_type, str):
            logger.warning("Cannot set the given switch type, it is not a string.")
            return

        switch_dictionaries_list = get_switch_dictionaries_from_types([switch_type])
        if not switch_dictionaries_list:
            logger.warning("Cannot set the given type, it doesn't have corresponding data defined in SwitchPairs.")
            return

        self.switch_type = switch_type

    def get_direction(self):
        """
        Gets the direction of the switch combination.
        Returns:
            str: Either "fk_to_ik" or "ik_to_fk".
        """
        return self.direction

    def get_switch_type(self):
        """
        Gets the type of the switch combination.
        Returns:
            str: the type name of the switch.
        """
        return self.switch_type

    def get_switch_combination_dict(self):
        """
        Converts the class values direction and type into a dictionary.
        Returns:
            dict: switch combination dictionary, example: {"direction": "fk_to_ik", "switch_type": "biped_right_arm"}
        """
        if not self.switch_type:
            logger.warning("switch_type value hasn't been set.")
            return

        return {SwitchCombination.direction_key: self.direction, SwitchCombination.switch_type_key: self.switch_type}


def switch(ik_fk_dict, direction=SwitchDirections.fk_to_ik, namespace="", match_only=False):
    """
    Performs the switch operation.
    Commands were wrapped into a function to be used during the bake operation.

    Args:
        ik_fk_dict (dict): A dict containing the elements that are part of the system you want to switch direction.
        direction (str, optional): "fk_to_ik" or "ik_to_fk". It determines what is the source and what is the target.
        namespace (str, optional): In case the rig has a namespace, it will be used to properly select the controls.
        match_only (bool, optional): If active (True) it will only match the pose, but not switch

    Returns:
        attr_value (float): Value which the influence attribute was set to. Either 1 (fk_to_ik) or 0 (ik_to_fk).
                            This value is returned only if "match_only" is False. Otherwise, expect None.
    """
    try:
        foot_ik_attr_list = [
            "footRoll",
            "sideRoll",
            "heelRoll",
            "ballRoll",
            "toeRoll",
            "heelPivot",
            "ballPivot",
            "toePivot",
            "tipPivot",
            "toeUpDown",
        ]
        ik_fk_ns_dict = {}
        for obj in ik_fk_dict:
            ik_fk_ns_dict[obj] = f"{namespace}{ik_fk_dict.get(obj)}"

        fk_pairs = [
            [ik_fk_ns_dict.get("base_ik_ref"), ik_fk_ns_dict.get("base_fk_ctrl")],
            [ik_fk_ns_dict.get("mid_ik_ref"), ik_fk_ns_dict.get("mid_fk_ctrl")],
            [ik_fk_ns_dict.get("end_ik_ref"), ik_fk_ns_dict.get("end_fk_ctrl")],
        ]

        if direction == "fk_to_ik":
            if ik_fk_dict.get("end_ik_reference") != "":
                cmds.matchTransform(
                    ik_fk_ns_dict.get("end_ik_ctrl"), ik_fk_ns_dict.get("end_ik_reference"), pos=1, rot=1
                )
            else:
                cmds.matchTransform(
                    ik_fk_ns_dict.get("end_ik_ctrl"),
                    ik_fk_ns_dict.get("end_fk_jnt"),
                    pos=1,
                    rot=1,
                )
            cmds.matchTransform(ik_fk_ns_dict.get("pvec_ik_ctrl"), ik_fk_ns_dict.get("mid_ik_reference"), pos=1, rot=1)

            if not match_only:
                cmds.setAttr(f"{ik_fk_ns_dict.get('switch_ctrl')}.{SWITCH_ATTR}", 1)

            # Special Cases (Auxiliary Feet Controls)
            if ik_fk_ns_dict.get("auxiliary_roll_ankle"):
                for xyz in ["x", "y", "z"]:
                    cmds.setAttr(f"{ik_fk_ns_dict.get('auxiliary_roll_ankle')}.r{xyz}", 0)
            if ik_fk_ns_dict.get("auxiliary_roll_ball"):
                for xyz in ["x", "y", "z"]:
                    cmds.setAttr(f"{ik_fk_ns_dict.get('auxiliary_roll_ball')}.r{xyz}", 0)
            if ik_fk_ns_dict.get("auxiliary_roll_toe"):
                for xyz in ["x", "y", "z"]:
                    cmds.setAttr(f"{ik_fk_ns_dict.get('auxiliary_roll_toe')}.r{xyz}", 0)
            if ik_fk_ns_dict.get("auxiliary_roll_up_down_toe"):
                for xyz in ["x", "y", "z"]:
                    cmds.setAttr(f"{ik_fk_ns_dict.get('auxiliary_roll_up_down_toe')}.t{xyz}", 0)
            if ik_fk_ns_dict.get("auxiliary_ik_ball"):
                for xyz in ["x", "y", "z"]:
                    cmds.setAttr(f"{ik_fk_ns_dict.get('auxiliary_ik_ball')}.t{xyz}", 0)
                    cmds.setAttr(f"{ik_fk_ns_dict.get('auxiliary_ik_ball')}.r{xyz}", 0)

            # Reset Attrs to 0
            for attr in foot_ik_attr_list:
                if cmds.attributeQuery(attr, node=ik_fk_ns_dict.get("end_ik_ctrl"), ex=True):
                    cmds.setAttr(f"{ik_fk_ns_dict.get('end_ik_ctrl')}.{attr}", 0)
            # Transfer from FK to IK Bal
            if cmds.objExists(ik_fk_ns_dict.get("auxiliary_fk_ball_ref") or ""):
                cmds.matchTransform(
                    ik_fk_ns_dict.get("auxiliary_ik_ball"),
                    ik_fk_ns_dict.get("auxiliary_fk_ball_ref"),
                    pos=1,
                    rot=1,
                )

            return 1
        if direction == "ik_to_fk":
            for pair in fk_pairs:
                cmds.matchTransform(pair[1], pair[0], pos=1, rot=1)
                pass
            if not match_only:
                cmds.setAttr(f"{ik_fk_ns_dict.get('switch_ctrl')}.{SWITCH_ATTR}", 0)

            # Transfer from IK to FK Ball
            if cmds.objExists(ik_fk_ns_dict.get("auxiliary_roll_ball_ref") or ""):
                cmds.matchTransform(
                    ik_fk_ns_dict.get("auxiliary_fk_ball"),
                    ik_fk_ns_dict.get("auxiliary_roll_ball_ref"),
                    pos=1,
                    rot=1,
                )

            return 0
    except Exception as e:
        tb = traceback.format_exc()
        logger.debug(str(tb))
        cmds.warning(
            f"An error occurred. Please check if a namespace is necessary or if a control was deleted.     Error: {e}"
        )


def fk_ik_switch(
    ik_fk_data,
    direction=SwitchDirections.fk_to_ik,
    namespace="",
    keyframe=False,
    start_time=0,
    end_time=0,
    method="sparse",
    key_influence=False,
):
    """
    Transfers the position of the FK to IK or IK to FK systems in a seamless way,
    so the animator can easily switch between one and the other

    Args:
        ik_fk_data (dict, list[dict]): A dictionary containing the elements that are part of the system you want
                                       to switch systems.
        direction (str, optional): "fk_to_ik" or "ik_to_fk". It determines what is the source and what is the target.
                                      If set to "auto" it will use the value of the influence attribute to determine
                                      which system to switch to. e.g. If set to FK, it will switch to IK.
        namespace (str, optional): In case the rig has a namespace, it will be used to properly select the controls.
        keyframe (bool, optional): If active it will create a keyframe at the current frame, move to the
        start_time (int, optional): Where to create the first keyframe
        end_time (int, optional): Where to create the last keyframe
        method (str, optional): Method used for creating the keyframes. Either 'sparse' or 'bake'.
        key_influence (bool, optional): Determines whether to key a transition between FK/IK,
                                        when switching with "Auto Key" activated.
    """

    if namespace:
        if namespace.find(":") == -1:
            namespace = f"{namespace}:"

    if isinstance(ik_fk_data, dict):
        ik_fk_list = [ik_fk_data]
    elif isinstance(ik_fk_data, list):
        ik_fk_list = ik_fk_data
    else:
        logger.debug("Given IK-FK data has invalid type.")
        return

    # Find Available Controls
    available_ctrls = []

    for ik_fk_dict in ik_fk_list:  # all dictionaries in one go
        for key in ik_fk_dict:
            if cmds.objExists(f"{namespace}{ik_fk_dict.get(key)}"):
                available_ctrls.append(ik_fk_dict.get(key))
            if cmds.objExists(f"{namespace}{key}"):
                available_ctrls.append(key)

    # No Controls were found
    if len(available_ctrls) == 0:
        cmds.warning("No controls were found. Make sure you are using the correct namespace.")
        return

    # Auto Direction
    if direction and direction.lower() == SwitchDirections.auto:
        data = ik_fk_data[0] if isinstance(ik_fk_data, list) else ik_fk_data
        switch_attr = f"{namespace}{data.get('switch_ctrl')}.{SWITCH_ATTR}"
        if cmds.objExists(switch_attr):
            influence = cmds.getAttr(switch_attr)
            direction = SwitchDirections.ik_to_fk if influence > 0.5 else SwitchDirections.fk_to_ik

    if keyframe:
        # Suspend refresh
        cmds.refresh(suspend=True)

        if method.lower() == "sparse":  # Only Influence Switch
            for ik_fk_dict in ik_fk_list:  # all dictionaries in one go
                original_time = cmds.currentTime(q=True)
                cmds.currentTime(start_time)
                if key_influence:
                    cmds.setKeyframe(
                        f"{namespace}{ik_fk_dict.get('switch_ctrl')}",
                        time=start_time,
                        attribute=SWITCH_ATTR,
                    )
                cmds.currentTime(end_time)
                switch(ik_fk_dict, direction=direction, namespace=namespace)
                if key_influence:
                    cmds.setKeyframe(
                        f"{namespace}{ik_fk_dict.get('switch_ctrl')}",
                        time=end_time,
                        attribute=SWITCH_ATTR,
                    )
                cmds.currentTime(original_time)

        elif method.lower() == "bake":
            if start_time >= end_time:
                cmds.warning("Invalid range. Please review the start and end frames and try again.")
            else:
                original_time = cmds.currentTime(q=True)
                cmds.currentTime(start_time)
                current_time = cmds.currentTime(q=True)

                if key_influence:
                    for ik_fk_dict in ik_fk_list:  # all dictionaries in one go
                        cmds.setKeyframe(
                            f"{namespace}{ik_fk_dict.get('switch_ctrl')}",
                            time=current_time,
                            attribute=SWITCH_ATTR,
                        )  # Start Switch

                # Bake process - loop time range
                for index in range(end_time - start_time):
                    cmds.currentTime(current_time)

                    for ik_fk_dict in ik_fk_list:  # switch all the dictionaries in one bake
                        _match_only = True
                        switch(ik_fk_dict, direction=direction, namespace=namespace, match_only=_match_only)
                        if direction == "fk_to_ik":
                            for channel in ["t", "r"]:
                                for dimension in ["x", "y", "z"]:
                                    cmds.setKeyframe(
                                        f"{namespace}{ik_fk_dict.get('end_ik_ctrl')}",
                                        time=current_time,
                                        attribute=f"{channel}{dimension}",
                                    )  # Wrist IK Ctrl
                                    cmds.setKeyframe(
                                        f"{namespace}{ik_fk_dict.get('pvec_ik_ctrl')}",
                                        time=current_time,
                                        attribute=f"{channel}{dimension}",
                                    )  # PVec Elbow IK Ctrl
                                    if ik_fk_dict.get("auxiliary_ik_ball"):
                                        cmds.setKeyframe(
                                            f"{namespace}{ik_fk_dict.get('auxiliary_ik_ball')}",
                                            time=current_time,
                                            attribute=f"{channel}{dimension}",
                                        )  # Toe Full IK Control

                        if direction == "ik_to_fk":
                            for channel in ["t", "r"]:
                                for dimension in ["x", "y", "z"]:
                                    cmds.setKeyframe(
                                        f"{namespace}{ik_fk_dict.get('base_fk_ctrl')}",
                                        time=current_time,
                                        attribute=f"{channel}{dimension}",
                                    )  # Shoulder FK Ctrl
                                    cmds.setKeyframe(
                                        f"{namespace}{ik_fk_dict.get('end_fk_ctrl')}",
                                        time=current_time,
                                        attribute=f"{channel}{dimension}",
                                    )  # Wrist FK Ctrl
                                    cmds.setKeyframe(
                                        f"{namespace}{ik_fk_dict.get('mid_fk_ctrl')}",
                                        time=current_time,
                                        attribute=f"{channel}{dimension}",
                                    )  # Elbow FK Ctrl
                                    if ik_fk_dict.get("auxiliary_fk_ball"):
                                        cmds.setKeyframe(
                                            f"{namespace}{ik_fk_dict.get('auxiliary_fk_ball')}",
                                            time=current_time,
                                            attribute=f"{channel}{dimension}",
                                        )  # Ball FK Ctrl
                    current_time += 1

                for ik_fk_dict in ik_fk_list:  # all dictionaries in one go
                    switch(ik_fk_dict, direction=direction, namespace=namespace)
                    if key_influence:
                        cmds.setKeyframe(
                            f"{namespace}{ik_fk_dict.get('switch_ctrl')}",
                            time=current_time,
                            attribute=SWITCH_ATTR,
                        )  # End Switch
                    cmds.currentTime(original_time)
        else:
            cmds.warning(f'Invalid method was provided. qMust be either "sparse" or "bake", but got {method}')

        # Re-enable refresh
        cmds.refresh(suspend=False)

    else:
        for ik_fk_dict in ik_fk_list:  # all dictionaries in one go
            switch(ik_fk_dict, direction=direction, namespace=namespace)


def snap_ik_pole_to_fk(snap_data, namespace="", start_time=0, end_time=0):
    """
    Snaps the IK pole vector to the fk joint in order to maintain better the source animation during the retarget.
    Args:
        snap_data (dict or list of dict): A dictionary containing the elements that are part of the system you want
                                          to snap.
        namespace (str, optional): In case the rig has a namespace, it will be used to properly select the controls.
        start_time (int, optional): Where to create the first keyframe
        end_time (int, optional): Where to create the last keyframe
    """
    if namespace:
        if namespace.find(":") == -1:
            namespace = namespace + ":"

    snap_list = []
    if isinstance(snap_data, dict):
        snap_list = [snap_data]
    elif isinstance(snap_data, list):
        snap_list = snap_data
    else:
        logger.debug("Given snap data has invalid type.")
        return

    # Find Available Controls
    switch_ctrls = []
    pole_to_fk_map = {}

    for snap_dict in snap_list:  # all dictionaries in one go
        if "switch_ctrl" in snap_dict.keys():
            switch_ctrl = namespace + snap_dict.get("switch_ctrl")
            if cmds.objExists(switch_ctrl):
                switch_ctrls.append(switch_ctrl)
        if "pvec_ik_ctrl" in snap_dict.keys() and "mid_fk_ctrl" in snap_dict.keys():
            pole_ctrl = namespace + snap_dict.get("pvec_ik_ctrl")
            fk_ctrl = namespace + snap_dict.get("mid_fk_ctrl")
            if cmds.objExists(pole_ctrl) and cmds.objExists(fk_ctrl):
                pole_to_fk_map[pole_ctrl] = fk_ctrl

    # Snap the IK pole vectors and bake
    snap_cnstr = []
    [cmds.setAttr(f"{ik_swt}.{SWITCH_ATTR}", 1) for ik_swt in switch_ctrls]
    [snap_cnstr.append(cmds.pointConstraint(fk, pole, mo=False)[0]) for pole, fk in pole_to_fk_map.items()]

    cmds.refresh(suspend=True)
    cmds.bakeResults(
        list(pole_to_fk_map.keys()),
        simulation=True,
        t=(start_time, end_time),
        sampleBy=1,
        oversamplingRate=1,
        disableImplicitControl=True,
        preserveOutsideKeys=True,
        sparseAnimCurveBake=True,
        removeBakedAttributeFromLayer=False,
        removeBakedAnimFromLayer=False,
        bakeOnOverrideLayer=False,
        minimizeRotation=True,
    )
    cmds.refresh(suspend=False)

    cmds.delete(snap_cnstr)
    cmds.select(clear=True)
    cmds.currentTime(start_time, edit=True)


def get_switch_dictionaries_from_types(switch_types):
    """
    Gets available switch dictionaries from the given switch types.
    Args:
        switch_types (list): list of switch types related to available switch dictionaries.
    Returns:
        list: list of available switch dictionaries related to the given switch types.
    """
    if not isinstance(switch_types, list):
        logger.error("Invalid input variable type. It must be a list.")

    switch_pairs_data = SwitchPairs.get_switch_pairs()
    switch_dictionaries_list = []
    for s_type in switch_types:
        if s_type in switch_pairs_data.keys():
            switch_dictionaries_list.append(switch_pairs_data[s_type])
        else:
            logger.warning(f"The switch type '{s_type}' does not have a defined dictionary of elements to switch.")

    return switch_dictionaries_list


def get_available_switch_types():
    """
    Gets available switch types from the defined switch pairs data at the top of this module.
    Returns:
        list: list of string, available switch types.
    """
    return list(SwitchPairs.get_switch_pairs().keys())


if __name__ == "__main__":
    fk_ik_switch(ik_fk_data=SwitchPairs.biped_left_leg, direction=SwitchDirections.auto)
    # switch(SwitchPairs.biped_left_leg, direction="fk_to_ik", namespace="", match_only=False)
