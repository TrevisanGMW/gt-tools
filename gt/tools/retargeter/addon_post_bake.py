"""
Animation Retargeter Addon: Post Bake
"""

import gt.tools.retargeter.retargeter_framework as tools_rt_frm
import gt.core.rig_switch as core_rig_switch
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class AddonPostBake(tools_rt_frm.TargetingAddon):
    __version__ = "0.0.2"
    allow_multiple = False

    def __init__(self):
        """
        Initiates the post bake process
        """
        super().__init__(name="Post Bake")
        self.execution_order = self.Order.post_bake
        self.active = False
        self.switch_combinations = []

    def set_active(self, active):
        """
        Sets the active state.
        Args:
            active (bool): The active state of the addon.
        """
        self.active = active

    def add_combination(self, direction, switch_type):
        """
        Adds a combination dictionary into the list of combinations
        Args:
            direction (str): The direction for the switch combination (e.g., 'left', 'right').
            switch_type (str): The type of switch to be combined.

        Returns:
            None
        """
        switch_combo = core_rig_switch.SwitchCombination(direction=direction, switch_type=switch_type)
        combo_dict = switch_combo.get_switch_combination_dict()
        if combo_dict:
            self.switch_combinations.append(combo_dict)

    def remove_combination_by_index(self, combo_index):
        """
        Removes a combination dictionary from the combination list by index.
        Args:
            combo_index (int): The index of the combination to remove.
        """
        if not isinstance(combo_index, int):
            logger.warning("Given index is not an integer.")
            return

        if self.switch_combinations:
            if (0 <= combo_index) and (combo_index < len(self.switch_combinations)):
                self.switch_combinations.pop(combo_index)

    def get_active(self):
        """
        Gets the active state for this addon.
        Returns:
            bool: The active state of the addon.
        """
        return self.active

    def get_switch_combinations(self):
        """
        Gets the switch combinations of the post bake.
        Returns:
            list: list of switch combination dictionaries in witch there are two keys "direction" and "switch_type".
                  example: [{"direction": "fk_to_ik", "switch_type": "biped_right_arm"},
                            {"direction": "fk_to_ik", "switch_type": "biped_left_arm"}]
        """
        return self.switch_combinations

    def apply_addon(self):
        """
        Post-bakes the defined switch types.
        """
        if self.active and self.switch_combinations:

            # Get time range
            start_frame = int(cmds.playbackOptions(q=True, animationStartTime=True))
            end_frame = int(cmds.playbackOptions(q=True, animationEndTime=True)) + 1

            # Stack Bake - stack of combinations with the same direction to optimize the number of bakes
            _stack_bake_list = []
            _prev_direction = None

            for combination in self.switch_combinations:
                combo_direction = combination["direction"]
                combo_type = combination["switch_type"]
                if _prev_direction != combo_direction:
                    _stack_bake_list.append([combo_direction, []])
                    _prev_direction = combo_direction
                _stack_bake_list[-1][1].append(combo_type)

            # Loop the stacks of switches
            for stack_bake in _stack_bake_list:
                switch_dicts = core_rig_switch.get_switch_dictionaries_from_types(stack_bake[1])

                if "snap_ik_pole_to_fk" in stack_bake[0]:
                    # Snap IK pole vector to the fk joint to get a better precision
                    core_rig_switch.snap_ik_pole_to_fk(
                        switch_dicts,
                        namespace=self._target_namespace,
                        start_time=start_frame,
                        end_time=end_frame,
                    )
                else:
                    # Switch and bake
                    core_rig_switch.fk_ik_switch(
                        switch_dicts,
                        direction=stack_bake[0],
                        namespace=self._target_namespace,
                        keyframe=True,
                        start_time=start_frame,
                        end_time=end_frame,
                        method="bake",
                    )
