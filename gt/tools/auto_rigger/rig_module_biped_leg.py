"""
Auto Rigger Leg Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import duplicate_joint_for_automation, get_proxy_offset, rescale_joint_radius
from gt.tools.auto_rigger.rig_utils import find_objects_with_attr, find_proxy_node_from_uuid, get_driven_joint
from gt.tools.auto_rigger.rig_utils import find_joint_node_from_uuid, find_or_create_joint_automation_group
from gt.tools.auto_rigger.rig_utils import find_direction_curve_node
from gt.utils.attr_utils import add_attr, hide_lock_default_attrs, set_attr_state, set_attr
from gt.utils.color_utils import ColorConstants, set_color_viewport, set_color_outliner
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.tools.auto_rigger.rig_constants import RiggerConstants
from gt.utils.transform_utils import match_translate, Vector3
from gt.utils.math_utils import dist_center_to_center
from gt.utils.naming_utils import NamingConstants
from gt.utils.curve_utils import get_curve
from gt.utils import hierarchy_utils
from gt.ui import resource_library
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleBipedLeg(ModuleGeneric):
    __version__ = '0.0.1-alpha'
    icon = resource_library.Icon.rigger_module_biped_leg
    allow_parenting = True

    def __init__(self, name="Leg", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        hip_name = "hip"
        knee_name = "knee"
        ankle_name = "ankle"
        ball_name = "ball"
        toe_name = "toe"
        heel_name = "heel"

        # Default Proxies
        self.hip = Proxy(name=hip_name)
        self.hip.set_locator_scale(scale=2)
        self.hip.set_meta_type(value="hip")

        self.knee = Proxy(name=knee_name)
        self.knee.set_curve(curve=get_curve('_proxy_joint_arrow_pos_z'))
        self.knee.set_locator_scale(scale=2)
        self.knee.add_meta_parent(line_parent=self.hip)
        self.knee.set_parent_uuid(uuid=self.hip.get_uuid())
        self.knee.set_meta_type(value="knee")

        self.ankle = Proxy(name=ankle_name)
        self.ankle.set_locator_scale(scale=2)
        self.ankle.add_meta_parent(line_parent=self.knee)
        self.ankle.set_meta_type(value="ankle")

        self.ball = Proxy(name=ball_name)
        self.ball.set_locator_scale(scale=2)
        self.ball.add_meta_parent(line_parent=self.ankle)
        self.ball.set_parent_uuid(uuid=self.ankle.get_uuid())
        self.ball.set_meta_type(value="ball")

        self.toe = Proxy(name=toe_name)
        self.toe.set_locator_scale(scale=1)
        self.toe.set_parent_uuid(uuid=self.ball.get_uuid())
        self.toe.set_parent_uuid_from_proxy(parent_proxy=self.ball)
        self.toe.set_meta_type(value="toe")

        self.heel = Proxy(name=heel_name)
        self.heel.set_locator_scale(scale=1)
        self.heel.add_meta_parent(line_parent=self.ankle)
        self.heel.add_color(rgb_color=ColorConstants.RigProxy.PIVOT)
        self.heel.set_meta_type(value="heel")

        # Initial Pose
        hip_pos = Vector3(y=84.5)
        knee_pos = Vector3(y=47.05)
        ankle_pos = Vector3(y=9.6)
        ball_pos = Vector3(z=13.1)
        toe_pos = Vector3(z=23.4)
        heel_pos = Vector3()

        self.hip.set_initial_position(xyz=hip_pos)
        self.knee.set_initial_position(xyz=knee_pos)
        self.ankle.set_initial_position(xyz=ankle_pos)
        self.ball.set_initial_position(xyz=ball_pos)
        self.toe.set_initial_position(xyz=toe_pos)
        self.heel.set_initial_position(xyz=heel_pos)

        # Update Proxies
        self.proxies = [self.hip, self.knee, self.ankle, self.ball, self.toe, self.heel]

    def set_orientation_direction(self, is_positive, **kwargs):
        """
        Sets the direction of the orientation.
        If positive, it will use "1" in the desired axis.
        If negative, (not positive) it will use "-1" in the desired axis.
        Args:
            is_positive (bool): If True, it's set to a positive direction, if False to negative.
                                e.g. True = (1, 0, 0) while False (-1, 0, 0)
        """
        super().set_orientation_direction(is_positive=is_positive,
                                          set_aim_axis=True,  # Only Aim Axis
                                          set_up_axis=False,
                                          set_up_dir=False)

    def get_module_as_dict(self, **kwargs):
        """
        Overwrite to remove offset data from the export
        Args:
            kwargs: Key arguments, not used for anything
        """
        return super().get_module_as_dict(include_offset_data=False)

    def read_proxies_from_dict(self, proxy_dict):
        """
        Reads a proxy description dictionary and populates (after resetting) the proxies list with the dict proxies.
        Args:
            proxy_dict (dict): A proxy description dictionary. It must match an expected pattern for this to work:
                               Acceptable pattern: {"uuid_str": {<description>}}
                               "uuid_str" being the actual uuid string value of the proxy.
                               "<description>" being the output of the operation "proxy.get_proxy_as_dict()".
        """
        if not proxy_dict or not isinstance(proxy_dict, dict):
            logger.debug(f'Unable to read proxies from dictionary. Input must be a dictionary.')
            return
        self.read_type_matching_proxy_from_dict(proxy_dict)

    # --------------------------------------------------- Misc ---------------------------------------------------
    def is_valid(self):
        """
        Checks if the rig module is valid. This means, it's ready to be used and no issues were detected.
        Returns
            bool: True if valid, False otherwise
        """
        is_valid = super().is_valid()  # Passthrough
        return is_valid

    def build_proxy(self, **kwargs):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        if self.parent_uuid:
            self.hip.set_parent_uuid(self.parent_uuid)
        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_post(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        # Get Maya Elements
        root = find_objects_with_attr(RiggerConstants.REF_ROOT_PROXY_ATTR)
        hip = find_proxy_node_from_uuid(self.hip.get_uuid())
        knee = find_proxy_node_from_uuid(self.knee.get_uuid())
        ankle = find_proxy_node_from_uuid(self.ankle.get_uuid())
        ball = find_proxy_node_from_uuid(self.ball.get_uuid())
        heel = find_proxy_node_from_uuid(self.heel.get_uuid())
        toe = find_proxy_node_from_uuid(self.toe.get_uuid())

        self.hip.apply_offset_transform()
        self.knee.apply_offset_transform()
        self.ankle.apply_offset_transform()
        self.ball.apply_offset_transform()
        self.heel.apply_offset_transform()

        # Hip -----------------------------------------------------------------------------------
        hide_lock_default_attrs(hip, translate=False)

        # Knee  ---------------------------------------------------------------------------------
        knee_tag = knee.get_short_name()
        hide_lock_default_attrs(knee, translate=False, rotate=False)

        # Knee Setup - Always Between Hip and Ankle
        knee_offset = get_proxy_offset(knee)
        cmds.pointConstraint([hip, ankle], knee_offset)

        knee_pv_dir = cmds.spaceLocator(name=f'{knee_tag}_poleVectorDir')[0]
        match_translate(source=knee, target_list=knee_pv_dir)
        cmds.move(0, 0, 13, knee_pv_dir, relative=True)  # More it forward (in front of the knee)
        hierarchy_utils.parent(knee_pv_dir, knee)

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

        knee_upvec_loc_grp = hierarchy_utils.parent(knee_upvec_loc_grp, root)[0]
        knee_upvec_loc = hierarchy_utils.parent(knee_upvec_loc, knee_upvec_loc_grp)[0]
        knee_dir_loc = hierarchy_utils.parent(knee_dir_loc, root)[0]
        knee_aim_loc = hierarchy_utils.parent(knee_aim_loc, knee_dir_loc)[0]

        knee_divide_node = cmds.createNode('multiplyDivide', name=f'{knee_tag}_divide')
        cmds.setAttr(f'{knee_divide_node}.operation', 2)  # Change operation to Divide
        cmds.setAttr(f'{knee_divide_node}.input2X', -2)
        cmds.connectAttr(f'{ankle}.tx', f'{knee_divide_node}.input1X')
        cmds.connectAttr(f'{knee_divide_node}.outputX', f'{knee_upvec_loc}.tx')

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

        # Knee Limits
        cmds.setAttr(f'{knee}.minTransZLimit', 0)
        cmds.setAttr(f'{knee}.minTransZLimitEnable', True)

        # Ankle ----------------------------------------------------------------------------------
        ankle_offset = get_proxy_offset(ankle)
        add_attr(obj_list=ankle.get_long_name(), attributes="followHip", attr_type='bool', default=True)
        constraint = cmds.pointConstraint(hip, ankle_offset, skip='y')[0]
        cmds.connectAttr(f'{ankle}.followHip', f'{constraint}.w0')
        set_attr_state(obj_list=ankle, attr_list=["rx", "rz"], locked=True, hidden=True)

        # Ball -----------------------------------------------------------------------------------
        ankle_tag = ankle.get_short_name()
        ball_offset = get_proxy_offset(ball)
        ball_driver = cmds.group(empty=True, world=True, name=f'{ankle_tag}_pivot')
        ball_driver = hierarchy_utils.parent(source_objects=ball_driver, target_parent=root)[0]
        ankle_pos = cmds.xform(ankle, q=True, ws=True, rp=True)
        cmds.move(ankle_pos[0], ball_driver, moveX=True)
        cmds.pointConstraint(ankle, ball_driver, maintainOffset=True, skip=['y'])
        cmds.orientConstraint(ankle, ball_driver, maintainOffset=True, skip=['x', 'z'])
        cmds.scaleConstraint(ankle, ball_driver, skip=['y'])
        hierarchy_utils.parent(ball_offset, ball_driver)

        # Keep Grounded
        for to_lock_ty in [toe, ball]:
            to_lock_ty = str(to_lock_ty)
            cmds.addAttr(to_lock_ty, ln='lockTranslateY', at='bool', k=True, niceName="Keep Grounded")
            cmds.setAttr(to_lock_ty + '.lockTranslateY', 0)
            cmds.setAttr(to_lock_ty + '.minTransYLimit', 0)
            cmds.setAttr(to_lock_ty + '.maxTransYLimit', 0)
            cmds.connectAttr(to_lock_ty + '.lockTranslateY', to_lock_ty + '.minTransYLimitEnable', f=True)
            cmds.connectAttr(to_lock_ty + '.lockTranslateY', to_lock_ty + '.maxTransYLimitEnable', f=True)

        # Heel -----------------------------------------------------------------------------------
        heel_offset = get_proxy_offset(heel)
        add_attr(obj_list=heel.get_long_name(), attributes="followAnkle", attr_type='bool', default=True)
        constraint = cmds.pointConstraint(ankle, heel_offset, skip='y')[0]
        cmds.connectAttr(f'{heel}.followAnkle', f'{constraint}.w0')
        hierarchy_utils.parent(source_objects=ball_offset, target_parent=ball_driver)
        hide_lock_default_attrs(heel, translate=False, rotate=True, scale=True)

        self.hip.apply_transforms()
        self.ankle.apply_transforms()
        self.ball.apply_transforms()
        self.heel.apply_transforms()
        self.toe.apply_transforms()
        self.knee.apply_transforms()  # Refresh due to automation

        cmds.select(clear=True)

    def build_skeleton(self):
        super().build_skeleton()  # Passthrough

    def build_skeleton_post(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        self.ankle.set_parent_uuid(self.knee.get_uuid())
        super().build_skeleton_post()  # Passthrough
        self.ankle.clear_parent_uuid()

        heel_jnt = find_joint_node_from_uuid(self.heel.get_uuid())
        if heel_jnt and cmds.objExists(heel_jnt):
            cmds.delete(heel_jnt)

    def build_rig(self):
        # Get Elements
        direction_crv = find_direction_curve_node()
        module_parent_jnt = find_joint_node_from_uuid(self.get_parent_uuid())  # TODO TEMP @@@
        hip_jnt = find_joint_node_from_uuid(self.hip.get_uuid())
        knee_jnt = find_joint_node_from_uuid(self.knee.get_uuid())
        ankle_jnt = find_joint_node_from_uuid(self.ankle.get_uuid())
        ball_jnt = find_joint_node_from_uuid(self.ball.get_uuid())
        toe_jnt = find_joint_node_from_uuid(self.toe.get_uuid())

        # Set Colors
        leg_jnt_list = [hip_jnt, knee_jnt, ankle_jnt, ball_jnt, toe_jnt]
        for jnt in leg_jnt_list:
            set_color_viewport(obj_list=jnt, rgb_color=(.3, .3, 0))
        set_color_viewport(obj_list=toe_jnt, rgb_color=ColorConstants.RigJoint.END)

        # Get Scale
        leg_scale = dist_center_to_center(hip_jnt, knee_jnt)
        leg_scale += dist_center_to_center(knee_jnt, ankle_jnt)
        foot_scale = dist_center_to_center(ankle_jnt, ball_jnt)
        foot_scale += dist_center_to_center(ball_jnt, toe_jnt)

        # Set Preferred Angle
        cmds.setAttr(f'{hip_jnt}.preferredAngleZ', 90)
        cmds.setAttr(f'{knee_jnt}.preferredAngleZ', -90)

        joint_automation_grp = find_or_create_joint_automation_group()
        module_parent_jnt = get_driven_joint(self.get_parent_uuid())
        hierarchy_utils.parent(source_objects=module_parent_jnt, target_parent=joint_automation_grp)

        # Create Automation Skeletons (FK/IK)
        hip_parent = module_parent_jnt
        if module_parent_jnt:
            set_color_viewport(obj_list=hip_parent, rgb_color=ColorConstants.RigJoint.AUTOMATION)
            rescale_joint_radius(joint_list=hip_parent, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_DRIVEN)
        else:
            hip_parent = joint_automation_grp

        hip_fk = duplicate_joint_for_automation(hip_jnt, suffix="fk", parent=hip_parent)
        knee_fk = duplicate_joint_for_automation(knee_jnt, suffix="fk", parent=hip_fk)
        ankle_fk = duplicate_joint_for_automation(ankle_jnt, suffix="fk", parent=knee_fk)
        ball_fk = duplicate_joint_for_automation(ball_jnt, suffix="fk", parent=ankle_fk)
        toe_fk = duplicate_joint_for_automation(toe_jnt, suffix="fk", parent=ball_fk)
        fk_joints = [hip_fk, knee_fk, ankle_fk, ball_fk, toe_fk]

        hip_ik = duplicate_joint_for_automation(hip_jnt, suffix="ik", parent=hip_parent)
        knee_ik = duplicate_joint_for_automation(knee_jnt, suffix="ik", parent=hip_ik)
        ankle_ik = duplicate_joint_for_automation(ankle_jnt, suffix="ik", parent=knee_ik)
        ball_ik = duplicate_joint_for_automation(ball_jnt, suffix="ik", parent=ankle_ik)
        toe_ik = duplicate_joint_for_automation(toe_jnt, suffix="ik", parent=ball_ik)
        ik_joints = [hip_ik, knee_ik, ankle_ik, ball_ik, toe_ik]

        rescale_joint_radius(joint_list=fk_joints, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_FK)
        rescale_joint_radius(joint_list=ik_joints, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_IK)
        set_color_viewport(obj_list=fk_joints, rgb_color=ColorConstants.RigJoint.FK)
        set_color_viewport(obj_list=ik_joints, rgb_color=ColorConstants.RigJoint.IK)
        set_color_outliner(obj_list=fk_joints, rgb_color=ColorConstants.RigOutliner.FK)
        set_color_outliner(obj_list=ik_joints, rgb_color=ColorConstants.RigOutliner.IK)

        print(f'leg_scale: {leg_scale}')
        print("build leg rig!")


class ModuleBipedLegLeft(ModuleBipedLeg):
    def __init__(self, name="Left Leg", prefix=NamingConstants.Prefix.LEFT, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Initial Pose
        overall_pos_offset = Vector3(x=10.2)
        hip_pos = Vector3(y=84.5) + overall_pos_offset
        knee_pos = Vector3(y=47.05) + overall_pos_offset
        ankle_pos = Vector3(y=9.6) + overall_pos_offset
        ball_pos = Vector3(z=13.1) + overall_pos_offset
        toe_pos = Vector3(z=23.4) + overall_pos_offset
        heel_pos = Vector3() + overall_pos_offset

        self.hip.set_initial_position(xyz=hip_pos)
        self.knee.set_initial_position(xyz=knee_pos)
        self.ankle.set_initial_position(xyz=ankle_pos)
        self.ball.set_initial_position(xyz=ball_pos)
        self.toe.set_initial_position(xyz=toe_pos)
        self.heel.set_initial_position(xyz=heel_pos)


class ModuleBipedLegRight(ModuleBipedLeg):
    def __init__(self, name="Right Leg", prefix=NamingConstants.Prefix.RIGHT, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(-1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Initial Pose
        overall_pos_offset = Vector3(x=-10.2)
        hip_pos = Vector3(y=84.5) + overall_pos_offset
        knee_pos = Vector3(y=47.05) + overall_pos_offset
        ankle_pos = Vector3(y=9.6) + overall_pos_offset
        ball_pos = Vector3(z=13.1) + overall_pos_offset
        toe_pos = Vector3(z=23.4) + overall_pos_offset
        heel_pos = Vector3() + overall_pos_offset

        self.hip.set_initial_position(xyz=hip_pos)
        self.knee.set_initial_position(xyz=knee_pos)
        self.ankle.set_initial_position(xyz=ankle_pos)
        self.ball.set_initial_position(xyz=ball_pos)
        self.toe.set_initial_position(xyz=toe_pos)
        self.heel.set_initial_position(xyz=heel_pos)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject
    a_proxy = Proxy()
    a_proxy.set_initial_position(y=84.5)
    a_proxy.set_name("pelvis")
    a_leg = ModuleBipedLeg()
    a_leg_lf = ModuleBipedLegLeft()
    a_leg_rt = ModuleBipedLegRight()
    a_module = ModuleGeneric()
    a_module.add_to_proxies(a_proxy)
    a_leg_lf.set_parent_uuid(a_proxy.get_uuid())
    a_leg_rt.set_parent_uuid(a_proxy.get_uuid())

    a_project = RigProject()
    a_project.add_to_modules(a_module)
    a_project.add_to_modules(a_leg_lf)
    a_project.add_to_modules(a_leg_rt)
    # a_project.add_to_modules(a_leg)
    a_project.build_proxy()
    a_project.build_rig()

    # for obj in ["hip", "knee", "ankle", "ball", "toe", "heelPivot"]:
    #     cmds.setAttr(f'{obj}.displayLocalAxis', 1)
    #     cmds.setAttr(f'rt_{obj}.displayLocalAxis', 1)
    #
    # cmds.setAttr(f'{NamingConstants.Prefix.LEFT}_{a_leg_lf.hip.get_name()}.tx', 10)
    # cmds.setAttr(f'{NamingConstants.Prefix.LEFT}_{a_leg_lf.ankle.get_name()}.tz', 5)
    # cmds.setAttr(f'{NamingConstants.Prefix.LEFT}_{a_leg_lf.knee.get_name()}.tz', 3)
    # cmds.setAttr(f'{NamingConstants.Prefix.LEFT}_{a_leg_lf.ankle.get_name()}.ry', 45)
    # a_project.read_data_from_scene()
    # dictionary = a_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = RigProject()
    # a_project2.read_data_from_dict(dictionary)
    # a_project2.build_proxy()

    # Frame all
    cmds.viewFit(all=True)
