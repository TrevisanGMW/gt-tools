"""
Auto Rigger Leg Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rigger_utils import find_proxy_with_uuid, RiggerConstants, find_objects_with_attr
from gt.utils.attr_utils import add_attr, hide_lock_default_attrs, set_attr_state, set_attr
from gt.tools.auto_rigger.rigger_framework import Proxy, ModuleGeneric
from gt.utils.naming_utils import get_short_name, NamingConstants
from gt.tools.auto_rigger.rigger_utils import get_proxy_offset
from gt.utils.transform_utils import match_translate
from gt.utils.color_utils import ColorConstants
from gt.utils.curve_utils import get_curve
from gt.utils import hierarchy_utils
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleBipedLeg(ModuleGeneric):
    def __init__(self,
                 name="Leg",
                 prefix=None,
                 parent_uuid=None,
                 metadata=None):
        super().__init__(name=name, prefix=prefix, parent_uuid=parent_uuid, metadata=metadata)

        # Default Proxies
        self.hip = Proxy(name="hip")
        self.hip.set_initial_position(y=84.5)
        self.hip.set_locator_scale(scale=0.4)

        self.knee = Proxy(name="knee")
        self.knee.set_curve(curve=get_curve('_proxy_joint_arrow'))
        self.knee.set_initial_position(y=47.05)
        self.knee.set_locator_scale(scale=0.5)
        self.knee.add_meta_parent(line_parent=self.hip)

        self.ankle = Proxy(name="ankle")
        self.ankle.set_initial_position(y=9.6)
        self.ankle.set_locator_scale(scale=0.4)
        self.ankle.add_meta_parent(line_parent=self.knee)

        self.ball = Proxy(name="ball")
        self.ball.set_initial_position(z=13.1)
        self.ball.set_locator_scale(scale=0.4)
        self.ball.add_meta_parent(line_parent=self.ankle)

        self.toe = Proxy(name="toe")
        self.toe.set_initial_position(z=23.4)
        self.toe.set_locator_scale(scale=0.4)
        self.toe.set_parent_uuid(uuid=self.ball.get_uuid())
        self.toe.set_parent_uuid_from_proxy(parent_proxy=self.ball)

        self.heel_pivot = Proxy(name="heelPivot")
        self.heel_pivot.set_locator_scale(scale=0.1)
        self.heel_pivot.add_meta_parent(line_parent=self.ankle)
        self.heel_pivot.add_color(rgb_color=ColorConstants.RigProxy.PIVOT)

        # Update Proxies
        self.proxies.extend([self.hip, self.knee, self.ankle, self.ball, self.toe, self.heel_pivot])

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig module is valid. This means, it's ready to be used and no issues were detected.
        Returns
            bool: True if valid, False otherwise
        """
        # TODO Other checks here
        is_valid = super().is_valid()  # Passthrough
        return is_valid

    def build_proxy(self):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        proxy = super().build_proxy()  # Passthrough
        return proxy

    def build_proxy_post(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        Creates leg proxy behavior through constraints and offsets.
        """
        # Get Maya Elements
        root = find_objects_with_attr(RiggerConstants.ROOT_PROXY_ATTR)
        hip = find_proxy_with_uuid(self.hip.get_uuid())
        knee = find_proxy_with_uuid(self.knee.get_uuid())
        ankle = find_proxy_with_uuid(self.ankle.get_uuid())
        ball = find_proxy_with_uuid(self.ball.get_uuid())
        heel_pivot = find_proxy_with_uuid(self.heel_pivot.get_uuid())

        # Hip -----------------------------------------------------------------------------------
        hide_lock_default_attrs(hip, translate=False)

        # Knee  ---------------------------------------------------------------------------------
        knee_tag = get_short_name(knee)
        hide_lock_default_attrs(knee, translate=False, rotate=False)

        # Knee Setup - Always Between Hip and Ankle
        knee_offset = get_proxy_offset(knee)
        cmds.pointConstraint([hip, ankle], knee_offset)

        knee_pv_dir = cmds.spaceLocator(name=f'{knee_tag}_poleVectorDir')[0]
        match_translate(source=knee, target_list=knee_pv_dir)
        cmds.move(0, 0, 13, knee_pv_dir, relative=True)  # More it forward (in front of the knee)
        cmds.parent(knee_pv_dir, knee)

        # Lock Knee Unstable Channels
        cmds.addAttr(knee, ln='lockTranslateX', at='bool', k=True, niceName="Lock Unstable Channel")
        cmds.setAttr(knee + '.lockTranslateX', 1)  # Active by default
        cmds.setAttr(knee + '.minTransXLimit', 0)
        cmds.setAttr(knee + '.maxTransXLimit', 0)
        cmds.connectAttr(knee + '.lockTranslateX', knee + '.minTransXLimitEnable')
        cmds.connectAttr(knee + '.lockTranslateX', knee + '.maxTransXLimitEnable')
        
        #  Knee Constraints (Limits)
        knee_dir_loc = cmds.spaceLocator(name=f'{knee_tag}_dirParent_{NamingConstants.Suffix.LOC}')[0]
        knee_aim_loc = cmds.spaceLocator(name=f'{knee_tag}_dirAim_{NamingConstants.Suffix.LOC}')[0]
        knee_upvec_loc = cmds.spaceLocator(name=f'{knee_tag}_dirParentUp_{NamingConstants.Suffix.LOC}')[0]
        knee_upvec_loc_grp = f'{knee_tag}_dirParentUp_{NamingConstants.Suffix.GRP}'
        knee_upvec_loc_grp = cmds.group(name=knee_upvec_loc_grp, empty=True, world=True)
        # Hide Reference Elements
        set_attr(obj_list=[knee_pv_dir, knee_upvec_loc_grp, knee_dir_loc],
                 attr_list="visibility", value=0)  # Set Visibility to Off
        set_attr(obj_list=[knee_pv_dir, knee_upvec_loc_grp, knee_dir_loc],
                 attr_list="hiddenInOutliner", value=1)  # Set Outline Hidden to On
        cmds.parent(knee_upvec_loc, knee_upvec_loc_grp)
        hierarchy_utils.parent(source_objects=[knee_upvec_loc_grp, knee_dir_loc], target_parent=root)
        hierarchy_utils.parent(source_objects=knee_aim_loc, target_parent=knee_dir_loc)

        knee_divide_node = cmds.createNode('multiplyDivide', name=f'{knee_tag}_divide')
        cmds.setAttr(knee_divide_node + '.operation', 2)  # Change operation to Divide
        cmds.setAttr(knee_divide_node + '.input2X', -2)
        cmds.connectAttr(ankle + '.tx', knee_divide_node + '.input1X')
        cmds.connectAttr(knee_divide_node + '.outputX', knee_upvec_loc + '.tx')

        match_translate(source=hip, target_list=knee_upvec_loc_grp)
        cmds.move(10, knee_upvec_loc, moveY=True, relative=True)  # More it forward (in front of the knee)
        cmds.pointConstraint(hip, knee_upvec_loc_grp)
        cmds.pointConstraint(hip, knee_dir_loc)
        cmds.pointConstraint([hip, ankle], knee_aim_loc)

        cmds.connectAttr(f'{knee_dir_loc}.rotate', f'{knee_offset}.rotate')

        cmds.aimConstraint(ankle, knee_dir_loc, aimVector=(0, -1, 0), upVector=(0, -1, 0),
                           worldUpType='object', worldUpObject=knee_upvec_loc)
        cmds.aimConstraint(knee_aim_loc, knee, aimVector=(0, 0, -1), upVector=(0, 1, 0),
                           worldUpType='none', skip=['x', 'z'])
        set_attr_state(obj_list=knee, attr_list="rotate", locked=True)

        cmds.transformLimits(knee, translationZ=(0, 1), enableTranslationZ=(1, 0))

        # Ankle ----------------------------------------------------------------------------------
        ankle_offset = get_proxy_offset(ankle)
        add_attr(target_list=ankle, attributes="followHip", attr_type='bool', default=True)
        constraint = cmds.pointConstraint(hip, ankle_offset, skip='y')[0]
        cmds.connectAttr(f'{ankle}.followHip', f'{constraint}.w0')

        # Ball -----------------------------------------------------------------------------------
        ankle_tag = get_short_name(ankle)
        ball_offset = get_proxy_offset(ball)
        ball_driver = cmds.group(empty=True, world=True, name=f'{ankle_tag}_pivot')
        hierarchy_utils.parent(source_objects=ball_driver, target_parent=root)
        ankle_pos = cmds.xform(ankle, q=True, ws=True, rp=True)
        cmds.move(ankle_pos[0], ball_driver, moveX=True)
        cmds.pointConstraint(ankle, ball_driver, maintainOffset=True, skip=['y'])
        cmds.orientConstraint(ankle, ball_driver, maintainOffset=True, skip=['x', 'z'])
        cmds.scaleConstraint(ankle, ball_driver, skip=['y'])
        cmds.parent(ball_offset, ball_driver)

        # Keep Grounded
        ball = find_proxy_with_uuid(self.ball.get_uuid())  # Refresh
        toe = find_proxy_with_uuid(self.toe.get_uuid())  # Refresh
        for to_lock_ty in [toe, ball]:
            cmds.addAttr(to_lock_ty, ln='lockTranslateY', at='bool', k=True, niceName="Keep Grounded")
            cmds.setAttr(to_lock_ty + '.lockTranslateY', 0)
            cmds.setAttr(to_lock_ty + '.minTransYLimit', 0)
            cmds.setAttr(to_lock_ty + '.maxTransYLimit', 0)
            cmds.connectAttr(to_lock_ty + '.lockTranslateY', to_lock_ty + '.minTransYLimitEnable', f=True)
            cmds.connectAttr(to_lock_ty + '.lockTranslateY', to_lock_ty + '.maxTransYLimitEnable', f=True)

        # Heel -----------------------------------------------------------------------------------
        heel_offset = get_proxy_offset(heel_pivot)
        add_attr(target_list=heel_pivot, attributes="followAnkle", attr_type='bool', default=True)
        constraint = cmds.pointConstraint(ankle, heel_offset, skip='y')[0]
        cmds.connectAttr(f'{heel_pivot}.followAnkle', f'{constraint}.w0')
        hierarchy_utils.parent(source_objects=ball_offset, target_parent=ball_driver)
        hide_lock_default_attrs(heel_pivot, translate=False, rotate=True, scale=True)

    def build_rig(self):
        super().build_rig()  # Passthrough


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rigger_framework import RigProject
    a_leg = ModuleBipedLeg()
    a_project = RigProject()
    a_project.add_to_modules(a_leg)
    a_project.build_proxy()
    # get_curve('_proxy_joint_arrow').build()

    cmds.viewFit(all=True)
