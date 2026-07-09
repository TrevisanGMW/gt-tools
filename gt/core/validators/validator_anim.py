"""
Animation Validators

Import Line:
    import gt.core.validators.validator_anim as core_data_val_anim
"""

import gt.core.validator as core_val
import gt.core.anim as core_anim
import maya.cmds as cmds


class ValidatorNoTimeKeyframes(core_val.ValidatorBase):
    """
    A validator class that identifies and manages standard animation keyframes
    within a Maya scene to ensure no time-based animation exists on objects.
    """

    def __init__(self):
        """
        Initializes the ValidatorNoTimeKeyframes instance with a specific
        description and an empty list to track nodes driven by animation.
        """
        description = "Ensures no standard animation keyframes (Time Keyframes) exist."
        super().__init__(description=description)
        self.animated_nodes = []

    def validate(self, scope=core_val.ValidatorScope.SCENE, node_type=None):
        """
        Scans the scene for animation curves and identifies the nodes they drive.
        Updates the validator status based on whether curves are found.

        Args:
            scope (core_val.ValidatorScope, optional): The scope of the validation
                (e.g., SCENE, SELECTION). Defaults to core_val.ValidatorScope.SCENE.
            node_type (str, optional): Specific node type to filter by. Defaults to None.
        """
        # Find all animCurve nodes
        anim_curves = core_anim.get_time_keyframes()

        # Determine what objects these curves drive
        self.animated_nodes = []
        if anim_curves:
            for crv in anim_curves:
                driven = cmds.listConnections(crv, source=False, destination=True, skipConversionNodes=True)
                if driven:
                    self.animated_nodes.extend(driven)

        if not anim_curves:
            self.set_result(core_val.ValidatorStatus.PASS, "No animation keyframes found.")
        else:
            self.set_result(core_val.ValidatorStatus.FAIL, f"Found {len(anim_curves)} animation curve(s).")

    def select(self):
        """
        Selects the nodes in the Maya scene that are currently being driven
        by animation curves identified during the validation step.
        """
        if self.animated_nodes:
            cmds.select(self.animated_nodes, replace=True)

    def is_select_available(self, **kwargs):
        """
        Determines if the selection functionality is active based on whether
        animated nodes were discovered.

        Args:
            **kwargs: Arbitrary keyword arguments passed to the base class method.

        Returns:
            bool: True if there are nodes available to select, False otherwise.
        """
        return super().is_select_available(item_list=self.animated_nodes)

    def repair(self):
        """
        Removes all identified animation curves from the scene and re-runs
        the validation to confirm the fix.
        """
        anim_curves = core_anim.get_time_keyframes()
        if anim_curves:
            cmds.delete(anim_curves)
            self.validate()


if __name__ == "__main__":
    a_val_test = ValidatorNoTimeKeyframes()
    a_val_test.validate()
    a_val_test.repair()

    print(" Validation ".center(65, "#"))
    print(a_val_test.get_status())
    print(a_val_test.get_feedback())
