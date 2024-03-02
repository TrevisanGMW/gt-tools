"""
Auto Rigger Leg Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import create_ctrl_curve, find_or_create_joint_automation_group, get_proxy_offset
from gt.tools.auto_rigger.rig_utils import find_direction_curve, find_control_root_curve, find_joint_from_uuid
from gt.tools.auto_rigger.rig_utils import find_objects_with_attr, find_proxy_from_uuid, get_driven_joint
from gt.utils.attr_utils import add_attr, hide_lock_default_attrs, set_attr_state, set_attr, add_separator_attr
from gt.utils.color_utils import ColorConstants, set_color_viewport, set_color_outliner, get_directional_color
from gt.utils.rigging_utils import rescale_joint_radius, expose_rotation_order, duplicate_joint_for_automation
from gt.utils.transform_utils import match_translate, Vector3, match_transform, scale_shapes, translate_shapes
from gt.utils.transform_utils import rotate_shapes
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.tools.auto_rigger.rig_constants import RiggerConstants, RiggerDriverTypes
from gt.utils.constraint_utils import constraint_targets, ConstraintTypes
from gt.utils.math_utils import get_bbox_position, dist_path_sum
from gt.utils.hierarchy_utils import add_offset_transform
from gt.utils.naming_utils import NamingConstants
from gt.utils.node_utils import create_node, Node
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
    __version__ = '0.0.3-alpha'
    icon = resource_library.Icon.rigger_module_biped_leg
    allow_parenting = True

    # Reference Attributes and Metadata Keys
    REF_ATTR_KNEE_PROXY_PV = "kneeProxyPoleVectorLookupAttr"
    META_FOOT_IK_NAME = "footCtrlName"  # Metadata key for a custom name used for the foot ik control
    # Default Values
    DEFAULT_SETUP_NAME = "leg"
    DEFAULT_FOOT = "foot"

    def __init__(self, name="Leg", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Module Unique Vars
        hip_name = "hip"
        knee_name = "knee"
        ankle_name = "ankle"
        ball_name = "ball"
        toe_name = "toe"
        heel_name = "heel"

        # Extra Module Data
        self.set_meta_setup_name(name=self.DEFAULT_SETUP_NAME)
        self.add_to_metadata(key=self.META_FOOT_IK_NAME, value=self.DEFAULT_FOOT)

        # Default Proxies
        self.hip = Proxy(name=hip_name)
        self.hip.set_locator_scale(scale=2)
        self.hip.set_meta_purpose(value="hip")
        self.hip.add_driver_type(driver_type=[RiggerDriverTypes.FK])  # TODO Add another IK for translation

        self.knee = Proxy(name=knee_name)
        self.knee.set_curve(curve=get_curve('_proxy_joint_arrow_pos_z'))
        self.knee.set_locator_scale(scale=2)
        self.knee.add_line_parent(line_parent=self.hip)
        self.knee.set_parent_uuid(uuid=self.hip.get_uuid())
        self.knee.set_meta_purpose(value="knee")
        self.knee.add_driver_type(driver_type=[RiggerDriverTypes.FK, RiggerDriverTypes.IK])

        self.ankle = Proxy(name=ankle_name)
        self.ankle.set_locator_scale(scale=2)
        self.ankle.add_line_parent(line_parent=self.knee)
        self.ankle.set_meta_purpose(value="ankle")
        self.ankle.add_driver_type(driver_type=[RiggerDriverTypes.FK, RiggerDriverTypes.IK])

        self.ball = Proxy(name=ball_name)
        self.ball.set_locator_scale(scale=2)
        self.ball.add_line_parent(line_parent=self.ankle)
        self.ball.set_parent_uuid(uuid=self.ankle.get_uuid())
        self.ball.set_meta_purpose(value="ball")
        self.ball.add_driver_type(driver_type=[RiggerDriverTypes.FK])

        self.toe = Proxy(name=toe_name)
        self.toe.set_locator_scale(scale=1)
        self.toe.set_parent_uuid(uuid=self.ball.get_uuid())
        self.toe.set_parent_uuid_from_proxy(parent_proxy=self.ball)
        self.toe.set_meta_purpose(value="toe")
        self.toe.add_driver_type(driver_type=[RiggerDriverTypes.FK])

        self.heel = Proxy(name=heel_name)
        self.heel.set_locator_scale(scale=1)
        self.heel.add_line_parent(line_parent=self.ankle)
        self.heel.add_color(rgb_color=ColorConstants.RigProxy.PIVOT)
        self.heel.set_meta_purpose(value="heel")

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
        self.read_purpose_matching_proxy_from_dict(proxy_dict)

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

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        # Get Maya Elements
        root = find_objects_with_attr(RiggerConstants.REF_ATTR_ROOT_PROXY)
        hip = find_proxy_from_uuid(self.hip.get_uuid())
        knee = find_proxy_from_uuid(self.knee.get_uuid())
        ankle = find_proxy_from_uuid(self.ankle.get_uuid())
        ball = find_proxy_from_uuid(self.ball.get_uuid())
        heel = find_proxy_from_uuid(self.heel.get_uuid())
        toe = find_proxy_from_uuid(self.toe.get_uuid())

        self.hip.apply_offset_transform()
        self.knee.apply_offset_transform()
        self.ankle.apply_offset_transform()
        self.ball.apply_offset_transform()
        self.heel.apply_offset_transform()

        # Hip -----------------------------------------------------------------------------------
        hide_lock_default_attrs(hip, rotate=True, scale=True)

        # Knee  ---------------------------------------------------------------------------------
        knee_tag = knee.get_short_name()
        hide_lock_default_attrs(knee, scale=True)

        # Knee Setup - Always Between Hip and Ankle
        knee_offset = get_proxy_offset(knee)
        constraint_targets(source_driver=[hip, ankle],
                           target_driven=knee_offset,
                           constraint_type=ConstraintTypes.POINT,
                           maintain_offset=False)

        knee_pv_dir = cmds.spaceLocator(name=f'{knee_tag}_poleVectorDir')[0]
        add_attr(obj_list=knee_pv_dir, attributes=ModuleBipedLeg.REF_ATTR_KNEE_PROXY_PV, attr_type="string")
        match_translate(source=knee, target_list=knee_pv_dir)
        cmds.move(0, 0, 13, knee_pv_dir, relative=True)  # More it forward (in front of the knee)
        hierarchy_utils.parent(knee_pv_dir, knee)

        # Lock Knee Unstable Channels
        cmds.addAttr(knee, ln='lockTranslateX', at='bool', k=True, niceName="Lock Unstable Channel")
        cmds.setAttr(f'{knee}.lockTranslateX', 1)  # Active by default
        cmds.setAttr(f'{knee}.minTransXLimit', 0)
        cmds.setAttr(f'{knee}.maxTransXLimit', 0)
        cmds.connectAttr(f'{knee}.lockTranslateX', f'{knee}.minTransXLimitEnable')
        cmds.connectAttr(f'{knee}.lockTranslateX', f'{knee}.maxTransXLimitEnable')

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

        knee_divide_node = create_node(node_type='multiplyDivide', name=f'{knee_tag}_divide')
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

    def build_skeleton_joints(self):
        super().build_skeleton_joints()  # Passthrough

    def build_skeleton_hierarchy(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        self.ankle.set_parent_uuid(self.knee.get_uuid())
        super().build_skeleton_hierarchy()  # Passthrough
        self.ankle.clear_parent_uuid()

        heel_jnt = find_joint_from_uuid(self.heel.get_uuid())
        if heel_jnt and cmds.objExists(heel_jnt):
            cmds.delete(heel_jnt)

    def build_rig(self, **kwargs):
        """
        Build core rig setup for this module.
        """
        # Get Module Orientation  # TODO @@@ CHECK IF USED
        module_orientation = self.get_orientation_data()
        aim_axis = module_orientation.get_aim_axis()
        aim_axis_x = aim_axis[0]  # Positive=Left, Negative=Right

        # Get Elements
        root_ctrl = find_control_root_curve()
        direction_crv = find_direction_curve()
        hip_jnt = find_joint_from_uuid(self.hip.get_uuid())
        knee_jnt = find_joint_from_uuid(self.knee.get_uuid())
        ankle_jnt = find_joint_from_uuid(self.ankle.get_uuid())
        ball_jnt = find_joint_from_uuid(self.ball.get_uuid())
        toe_jnt = find_joint_from_uuid(self.toe.get_uuid())

        # Set Colors
        leg_jnt_list = [hip_jnt, knee_jnt, ankle_jnt, ball_jnt, toe_jnt]
        for jnt in leg_jnt_list:
            set_color_viewport(obj_list=jnt, rgb_color=(.3, .3, 0))
        set_color_viewport(obj_list=toe_jnt, rgb_color=ColorConstants.RigJoint.END)

        # Get Scale
        leg_scale = dist_path_sum(input_list=[hip_jnt, knee_jnt, ankle_jnt])
        foot_scale = dist_path_sum(input_list=[ankle_jnt, ball_jnt, toe_jnt])

        # Set Preferred Angle
        cmds.setAttr(f'{hip_jnt}.preferredAngleZ', 90)
        cmds.setAttr(f'{knee_jnt}.preferredAngleZ', -90)

        # Create Parent Automation Elements
        joint_automation_grp = find_or_create_joint_automation_group()
        module_parent_jnt = get_driven_joint(self.get_parent_uuid())
        hierarchy_utils.parent(source_objects=module_parent_jnt, target_parent=joint_automation_grp)

        # Create Automation Skeletons (FK/IK) --------------------------------------------------------------
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

        # FK Controls --------------------------------------------------------------------------------------

        # FK Hip Control
        hip_fk_ctrl = self._assemble_ctrl_name(name=self.hip.get_name())
        hip_fk_ctrl = create_ctrl_curve(name=hip_fk_ctrl, curve_file_name="_circle_pos_x")
        self.add_driver_uuid_attr(target=hip_fk_ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=self.hip)
        hip_fk_offset = add_offset_transform(target_list=hip_fk_ctrl)[0]
        hip_fk_offset = Node(hip_fk_offset)
        match_transform(source=hip_jnt, target_list=hip_fk_offset)
        scale_shapes(obj_transform=hip_fk_ctrl, offset=leg_scale*.1)
        hierarchy_utils.parent(source_objects=hip_fk_offset, target_parent=direction_crv)
        constraint_targets(source_driver=hip_fk_ctrl,target_driven=hip_fk)
        color = get_directional_color(object_name=hip_fk_ctrl)
        set_color_viewport(obj_list=hip_fk_ctrl, rgb_color=color)

        # FK Knee Control
        knee_fk_ctrl = self._assemble_ctrl_name(name=self.knee.get_name())
        knee_fk_ctrl = create_ctrl_curve(name=knee_fk_ctrl, curve_file_name="_circle_pos_x")
        self.add_driver_uuid_attr(target=knee_fk_ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=self.knee)
        knee_fk_offset = add_offset_transform(target_list=knee_fk_ctrl)[0]
        knee_fk_offset = Node(knee_fk_offset)
        match_transform(source=knee_jnt, target_list=knee_fk_offset)
        scale_shapes(obj_transform=knee_fk_ctrl, offset=leg_scale * .1)
        hierarchy_utils.parent(source_objects=knee_fk_offset, target_parent=hip_fk_ctrl)
        constraint_targets(source_driver=knee_fk_ctrl, target_driven=knee_fk)

        # FK Ankle Control
        ankle_fk_ctrl = self._assemble_ctrl_name(name=self.ankle.get_name())
        ankle_fk_ctrl = create_ctrl_curve(name=ankle_fk_ctrl, curve_file_name="_circle_pos_x")
        self.add_driver_uuid_attr(target=ankle_fk_ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=self.ankle)
        ankle_fk_offset = add_offset_transform(target_list=ankle_fk_ctrl)[0]
        ankle_fk_offset = Node(ankle_fk_offset)
        match_transform(source=ankle_jnt, target_list=ankle_fk_offset)
        scale_shapes(obj_transform=ankle_fk_ctrl, offset=leg_scale * .1)
        hierarchy_utils.parent(source_objects=ankle_fk_offset, target_parent=knee_fk_ctrl)
        constraint_targets(source_driver=ankle_fk_ctrl, target_driven=ankle_fk)
        # Remove Ankle Shape Orientation
        temp_transform = cmds.group(name=ankle_fk_ctrl + '_rotExtraction', empty=True, world=True)
        match_translate(source=toe_jnt, target_list=temp_transform)
        match_translate(source=ankle_jnt, target_list=temp_transform, skip=['x', 'z'])
        cmds.delete(cmds.aimConstraint(temp_transform, ankle_fk_ctrl, offset=(0, 0, 0), aimVector=(0, 1, 0),
                                       upVector=(1, 0, 0), worldUpType='vector', worldUpVector=(0, -1, 0)))
        cmds.delete(temp_transform)
        cmds.makeIdentity(ankle_fk_ctrl, apply=True, rotate=True)

        # FK Ball Control
        ball_fk_ctrl = self._assemble_ctrl_name(name=self.ball.get_name())
        ball_fk_ctrl = create_ctrl_curve(name=ball_fk_ctrl, curve_file_name="_circle_pos_x")
        self.add_driver_uuid_attr(target=ball_fk_ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=self.ball)
        ball_offset = add_offset_transform(target_list=ball_fk_ctrl)[0]
        ball_offset = Node(ball_offset)
        match_transform(source=ball_jnt, target_list=ball_offset)
        scale_shapes(obj_transform=ball_fk_ctrl, offset=foot_scale * .3)
        hierarchy_utils.parent(source_objects=ball_offset, target_parent=ankle_fk_ctrl)
        constraint_targets(source_driver=ball_fk_ctrl, target_driven=ball_fk)

        # IK Controls --------------------------------------------------------------------------------------

        # IK Knee Control
        knee_ik_ctrl = self._assemble_ctrl_name(name=self.knee.get_name(),
                                             overwrite_suffix=NamingConstants.Suffix.IK_CTRL)
        knee_ik_ctrl = create_ctrl_curve(name=knee_ik_ctrl, curve_file_name="_locator")
        self.add_driver_uuid_attr(target=knee_ik_ctrl, driver_type=RiggerDriverTypes.IK, proxy_purpose=self.knee)
        knee_offset = add_offset_transform(target_list=knee_ik_ctrl)[0]
        knee_offset = Node(knee_offset)
        match_translate(source=knee_jnt, target_list=knee_offset)
        scale_shapes(obj_transform=knee_ik_ctrl, offset=leg_scale * .05)
        hierarchy_utils.parent(source_objects=knee_offset, target_parent=direction_crv)
        color = get_directional_color(object_name=knee_ik_ctrl)
        set_color_viewport(obj_list=knee_ik_ctrl, rgb_color=color)

        # Find Pole Vector Position
        knee_proxy = find_proxy_from_uuid(uuid_string=self.knee.get_uuid())
        knee_proxy_children = cmds.listRelatives(knee_proxy, children=True, typ="transform", fullPath=True) or []
        knee_pv_dir = find_objects_with_attr(attr_name=ModuleBipedLeg.REF_ATTR_KNEE_PROXY_PV,
                                             lookup_list=knee_proxy_children)

        temp_transform = cmds.group(name=knee_ik_ctrl + '_rotExtraction', empty=True, world=True)
        match_translate(source=knee_jnt, target_list=temp_transform)
        cmds.delete(cmds.aimConstraint(knee_pv_dir, temp_transform, offset=(0, 0, 0), aimVector=(1, 0, 0),
                                       upVector=(0, -1, 0), worldUpType='vector', worldUpVector=(0, 1, 0)))
        cmds.move(leg_scale*.5, 0, 0, temp_transform, objectSpace=True, relative=True)
        cmds.delete(cmds.pointConstraint(temp_transform, knee_offset))
        cmds.delete(temp_transform)

        # IK Foot Control
        foot_ctrl_name = self.get_metadata_value(key=self.META_FOOT_IK_NAME)
        foot_ctrl = self._assemble_ctrl_name(name=foot_ctrl_name, overwrite_suffix=NamingConstants.Suffix.IK_CTRL)
        foot_ctrl = create_ctrl_curve(name=foot_ctrl, curve_file_name="_cube")
        self.add_driver_uuid_attr(target=foot_ctrl, driver_type=RiggerDriverTypes.IK, proxy_purpose=self.ankle)
        translate_shapes(obj_transform=foot_ctrl, offset=(0, 1, 0))  # Move Pivot to Base
        foot_offset = add_offset_transform(target_list=foot_ctrl)[0]
        foot_offset = Node(foot_offset)
        foot_ctrl_scale = (foot_scale*.3, foot_scale*.15, foot_scale*.6)
        scale_shapes(obj_transform=foot_ctrl, offset=foot_ctrl_scale)
        hierarchy_utils.parent(source_objects=foot_offset, target_parent=direction_crv)

        # Find Foot Position
        ankle_proxy = find_proxy_from_uuid(uuid_string=self.ankle.get_uuid())
        cmds.delete(cmds.pointConstraint([ankle_jnt, toe_jnt], foot_offset, skip='y'))
        desired_rotation = cmds.xform(ankle_proxy, q=True, ro=True)
        desired_translation = cmds.xform(ankle_proxy, q=True, t=True, ws=True)
        cmds.setAttr(f'{foot_offset}.ry', desired_rotation[1])
        # Foot Pivot Adjustment
        cmds.xform(foot_offset, piv=desired_translation, ws=True)
        cmds.xform(foot_ctrl, piv=desired_translation, ws=True)
        # Foot Color
        color = get_directional_color(object_name=foot_ctrl)
        set_color_viewport(obj_list=foot_ctrl, rgb_color=color)

        # Duplicate for Offset Control And Create Data Transform
        foot_o_ctrl = self._assemble_ctrl_name(name=foot_ctrl_name, overwrite_suffix=NamingConstants.Suffix.IK_O_CTRL)
        foot_o_ctrl = cmds.duplicate(foot_ctrl, name=foot_o_ctrl)[0]
        foot_o_data = self._assemble_ctrl_name(name=foot_ctrl_name, overwrite_suffix=NamingConstants.Suffix.IK_O_DATA)
        foot_o_data = cmds.duplicate(foot_offset, parentOnly=True, name=foot_o_data)[0]
        hierarchy_utils.parent(source_objects=[foot_o_ctrl, foot_o_data], target_parent=foot_ctrl)
        cmds.connectAttr(f'{foot_o_ctrl}.translate', f'{foot_o_data}.translate')
        cmds.connectAttr(f'{foot_o_ctrl}.rotate', f'{foot_o_data}.rotate')
        color = get_directional_color(object_name=foot_ctrl,
                                      negative_color=ColorConstants.RigControl.RIGHT_OFFSET,
                                      positive_color=ColorConstants.RigControl.LEFT_OFFSET)
        set_color_viewport(obj_list=foot_o_ctrl, rgb_color=color)
        foot_center = get_bbox_position(obj_list=foot_o_ctrl)
        scale_shapes(obj_transform=foot_o_ctrl, offset=0.9, pivot=foot_center)
        # Attributes
        add_separator_attr(target_object=foot_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
        expose_rotation_order(foot_ctrl)
        add_separator_attr(target_object=foot_o_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
        expose_rotation_order(foot_o_ctrl)
        cmds.addAttr(foot_ctrl, ln=RiggerConstants.ATTR_SHOW_OFFSET, at='bool', k=True)
        cmds.connectAttr(f'{foot_ctrl}.{RiggerConstants.ATTR_SHOW_OFFSET}', f'{foot_o_ctrl}.v')

        # Switch Control
        ik_switch_ctrl = self._assemble_ctrl_name(name=self.get_meta_setup_name(),
                                                  overwrite_suffix=NamingConstants.Suffix.SWITCH_CTRL)
        ik_switch_ctrl = create_ctrl_curve(name=ik_switch_ctrl, curve_file_name="_fk_ik_switch")
        self.add_driver_uuid_attr(target=ik_switch_ctrl,
                                  driver_type=RiggerDriverTypes.SWITCH,
                                  proxy_purpose=self.ankle)
        ik_switch_offset = add_offset_transform(target_list=ik_switch_ctrl)[0]
        ik_switch_offset = Node(ik_switch_offset)
        match_transform(source=ankle_proxy, target_list=ik_switch_offset)
        translate_shapes(obj_transform=ik_switch_ctrl, offset=(0, 0, leg_scale * -.015))  # Move it away from wrist
        scale_shapes(obj_transform=ik_switch_ctrl, offset=leg_scale * .1)
        hierarchy_utils.parent(source_objects=ik_switch_offset, target_parent=root_ctrl)
        # constraint_targets(source_driver=ik_switch_ctrl, target_driven=ik_switch)
        color = get_directional_color(object_name=ik_switch_ctrl)
        set_color_viewport(obj_list=ik_switch_ctrl, rgb_color=color)
        add_separator_attr(target_object=ik_switch_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)

        # Roll Controls ------------------------------------------------------------------------------------
        # Toe Roll
        roll_toe_ctrl = self._assemble_ctrl_name(name="toe", overwrite_suffix=NamingConstants.Suffix.ROLL_CTRL)
        roll_toe_ctrl = create_ctrl_curve(name=roll_toe_ctrl, curve_file_name="_sphere_half_arrow")
        self.add_driver_uuid_attr(target=roll_toe_ctrl,
                                  driver_type=RiggerDriverTypes.ROLL,
                                  proxy_purpose=self.toe)
        roll_toe_offset = add_offset_transform(target_list=roll_toe_ctrl)[0]
        roll_toe_offset = Node(roll_toe_offset)
        match_transform(source=toe_jnt, target_list=roll_toe_offset)
        desired_rotation = cmds.xform(ankle_proxy, query=True, rotation=True)
        cmds.setAttr(f'{roll_toe_offset}.rx', 0)
        cmds.setAttr(f'{roll_toe_offset}.ry', desired_rotation[1])
        scale_shapes(obj_transform=roll_toe_ctrl, offset=foot_scale * .1)
        hierarchy_utils.parent(source_objects=roll_toe_offset, target_parent=foot_o_data)
        cmds.move(foot_scale*.35, roll_toe_offset, z=True, relative=True, objectSpace=True)

        # Toe Up Down
        up_down_toe_ctrl = self._assemble_ctrl_name(name="toe", overwrite_suffix=NamingConstants.Suffix.UP_DOWN_CTRL)
        up_down_toe_ctrl = create_ctrl_curve(name=up_down_toe_ctrl, curve_file_name="_two_sides_arrow_pos_y")
        self.add_driver_uuid_attr(target=up_down_toe_ctrl,
                                  driver_type=RiggerDriverTypes.UP_DOWN,
                                  proxy_purpose=self.ball)
        up_down_toe_offset = add_offset_transform(target_list=up_down_toe_ctrl)[0]
        up_down_toe_offset = Node(up_down_toe_offset)
        match_transform(source=toe_jnt, target_list=up_down_toe_offset)
        desired_rotation = cmds.xform(ankle_proxy, query=True, rotation=True)
        cmds.setAttr(f'{up_down_toe_offset}.rx', 0)
        cmds.setAttr(f'{up_down_toe_offset}.ry', desired_rotation[1])
        scale_shapes(obj_transform=up_down_toe_ctrl, offset=foot_scale * .1)
        hierarchy_utils.parent(source_objects=up_down_toe_offset, target_parent=foot_o_data)
        cmds.move(foot_scale * .55, up_down_toe_offset, z=True, relative=True, objectSpace=True)

        # Ball Roll
        roll_ball_ctrl = self._assemble_ctrl_name(name="ball", overwrite_suffix=NamingConstants.Suffix.ROLL_CTRL)
        roll_ball_ctrl = create_ctrl_curve(name=roll_ball_ctrl, curve_file_name="_sphere_half_arrow")
        self.add_driver_uuid_attr(target=roll_ball_ctrl,
                                  driver_type=RiggerDriverTypes.ROLL,
                                  proxy_purpose=self.ball)
        roll_ball_offset = add_offset_transform(target_list=roll_ball_ctrl)[0]
        roll_ball_offset = Node(roll_ball_offset)
        match_transform(source=ball_jnt, target_list=roll_ball_offset)
        desired_rotation = cmds.xform(ankle_proxy, query=True, rotation=True)
        cmds.setAttr(f'{roll_ball_offset}.rx', 0)
        cmds.setAttr(f'{roll_ball_offset}.ry', desired_rotation[1])
        scale_shapes(obj_transform=roll_ball_ctrl, offset=foot_scale * .1)
        hierarchy_utils.parent(source_objects=roll_ball_offset, target_parent=foot_o_data)
        x_offset = (foot_scale*.45)*aim_axis_x
        cmds.move(x_offset, roll_ball_offset, x=True, relative=True, objectSpace=True)

        # Heel Roll
        roll_heel_ctrl = self._assemble_ctrl_name(name="heel", overwrite_suffix=NamingConstants.Suffix.ROLL_CTRL)
        roll_heel_ctrl = create_ctrl_curve(name=roll_heel_ctrl, curve_file_name="_sphere_half_arrow")
        self.add_driver_uuid_attr(target=roll_heel_ctrl,
                                  driver_type=RiggerDriverTypes.ROLL,
                                  proxy_purpose=self.ankle)
        roll_heel_offset = add_offset_transform(target_list=roll_heel_ctrl)[0]
        roll_heel_offset = Node(roll_heel_offset)
        match_transform(source=ankle_proxy, target_list=roll_heel_offset)
        match_translate(source=ball_jnt, target_list=roll_heel_offset, skip=('x', 'z'))
        rotate_shapes(obj_transform=roll_heel_ctrl, offset=(0, 180, 0))
        desired_rotation = cmds.xform(ankle_proxy, query=True, rotation=True)
        cmds.setAttr(f'{roll_heel_offset}.rx', 0)
        cmds.setAttr(f'{roll_heel_offset}.ry', desired_rotation[1])
        scale_shapes(obj_transform=roll_heel_ctrl, offset=foot_scale * .1)
        hierarchy_utils.parent(source_objects=roll_heel_offset, target_parent=foot_o_data)
        cmds.move(foot_scale * -.4, roll_heel_offset, z=True, relative=True, objectSpace=True)

        # heel_proxy = find_proxy_from_uuid(uuid_string=self.heel.get_uuid())

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [hip_fk_offset]

    # ------------------------------------------- Extra Module Setters -------------------------------------------
    def set_foot_ctrl_name(self, name):
        """
        Sets the foot control name by editing the metadata value associated with it.
        Args:
            name (str): New name for the IK foot control. If empty the default "foot" name will be used instead.
        """
        self.add_to_metadata(self.META_FOOT_IK_NAME, value=name if name else self.DEFAULT_FOOT)


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
    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.utils.session_utils import remove_modules_startswith
    remove_modules_startswith("gt.tools.auto_rigger.module")
    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject
    from gt.tools.auto_rigger.module_spine import ModuleSpine

    a_spine = ModuleSpine()
    a_leg = ModuleBipedLeg()
    a_leg_lf = ModuleBipedLegLeft()
    a_leg_rt = ModuleBipedLegRight()
    a_module = ModuleGeneric()

    spine_hip_uuid = a_spine.hip.get_uuid()
    a_leg_lf.set_parent_uuid(spine_hip_uuid)
    a_leg_rt.set_parent_uuid(spine_hip_uuid)

    a_project = RigProject()
    a_project.add_to_modules(a_spine)
    a_project.add_to_modules(a_leg_lf)
    a_project.add_to_modules(a_leg_rt)
    a_project.build_proxy()
    cmds.setAttr(f'lf_ankle.ry', 30)
    a_project.build_rig()

    # Frame all
    cmds.viewFit(all=True)
