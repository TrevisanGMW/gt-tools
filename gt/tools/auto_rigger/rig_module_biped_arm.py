"""
Auto Rigger Arm Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import duplicate_joint_for_automation, find_or_create_joint_automation_group
from gt.tools.auto_rigger.rig_utils import find_joint_from_uuid, rescale_joint_radius, find_direction_curve
from gt.tools.auto_rigger.rig_utils import create_ctrl_curve, get_proxy_offset, offset_control_orientation
from gt.tools.auto_rigger.rig_utils import find_objects_with_attr, find_proxy_from_uuid, get_driven_joint
from gt.utils.color_utils import set_color_viewport, ColorConstants, set_color_outliner, get_directional_color
from gt.utils.transform_utils import match_translate, match_transform, Vector3, set_equidistant_transforms
from gt.utils.transform_utils import scale_shapes, rotate_shapes
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.utils.attr_utils import hide_lock_default_attrs, set_attr_state, set_attr
from gt.tools.auto_rigger.rig_constants import RiggerConstants, RiggerDriverTypes
from gt.utils.iterable_utils import multiply_collection_by_number
from gt.utils.hierarchy_utils import add_offset_transform
from gt.utils.math_utils import dist_center_to_center
from gt.utils.node_utils import Node, create_node
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


class ModuleBipedArm(ModuleGeneric):
    __version__ = '0.0.2-alpha'
    icon = resource_library.Icon.rigger_module_biped_arm
    allow_parenting = True

    # Metadata Keys
    META_FOREARM_ACTIVE = "forearmActive"  # Metadata key for forearm activation
    META_FOREARM_NAME = "forearmName"  # Metadata key for a forearm name

    def __init__(self, name="Arm", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)

        # Extra Module Data
        self.add_to_metadata(key=self.META_FOREARM_ACTIVE, value=True)

        clavicle_name = "clavicle"
        shoulder_name = "shoulder"
        elbow_name = "elbow"
        wrist_name = "wrist"

        pos_clavicle = Vector3(y=130)
        pos_shoulder = Vector3(z=17.2, y=130)
        pos_elbow = Vector3(z=37.7, y=130)
        pos_wrist = Vector3(z=58.2, y=130)

        # Default Proxies
        self.clavicle = Proxy(name=clavicle_name)
        self.clavicle.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.clavicle.set_initial_position(xyz=pos_clavicle)
        self.clavicle.set_locator_scale(scale=2)
        self.clavicle.set_meta_purpose(value="clavicle")

        self.shoulder = Proxy(name=shoulder_name)
        self.shoulder.set_initial_position(xyz=pos_shoulder)
        self.shoulder.set_locator_scale(scale=2)
        self.shoulder.set_parent_uuid(self.clavicle.get_uuid())
        self.shoulder.set_meta_purpose(value="shoulder")

        self.elbow = Proxy(name=elbow_name)
        self.elbow.set_curve(curve=get_curve('_proxy_joint_arrow_neg_z'))
        self.elbow.set_initial_position(xyz=pos_elbow)
        self.elbow.set_locator_scale(scale=2.2)
        self.elbow.add_line_parent(line_parent=self.shoulder)
        self.elbow.set_meta_purpose(value="elbow")

        self.wrist = Proxy(name=wrist_name)
        self.wrist.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.wrist.set_initial_position(xyz=pos_wrist)
        self.wrist.set_locator_scale(scale=2)
        self.wrist.add_line_parent(line_parent=self.elbow)
        self.wrist.set_meta_purpose(value="wrist")

        # Update Proxies
        self.proxies = [self.clavicle, self.shoulder, self.elbow, self.wrist]

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
                                          set_aim_axis=True,
                                          set_up_axis=True,
                                          set_up_dir=False)  # No Up Direction

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
            self.clavicle.set_parent_uuid(self.parent_uuid)
            # self.clavicle.add_meta_parent(self.parent_uuid)
        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        # Get Maya Elements
        root = find_objects_with_attr(RiggerConstants.REF_ATTR_ROOT_PROXY)
        clavicle = find_proxy_from_uuid(self.clavicle.get_uuid())
        shoulder = find_proxy_from_uuid(self.shoulder.get_uuid())
        elbow = find_proxy_from_uuid(self.elbow.get_uuid())
        wrist = find_proxy_from_uuid(self.wrist.get_uuid())

        self.clavicle.apply_offset_transform()
        self.shoulder.apply_offset_transform()
        self.elbow.apply_offset_transform()
        self.wrist.apply_offset_transform()

        # Shoulder -----------------------------------------------------------------------------------
        hide_lock_default_attrs(shoulder, rotate=True, scale=True)

        # Elbow  -------------------------------------------------------------------------------------
        elbow_tag = elbow.get_short_name()
        hide_lock_default_attrs(elbow, scale=True)

        # Elbow Setup
        elbow_offset = get_proxy_offset(elbow)

        elbow_pv_dir = cmds.spaceLocator(name=f'{elbow_tag}_poleVectorDir')[0]
        elbow_pv_dir = Node(elbow_pv_dir)
        match_translate(source=elbow, target_list=elbow_pv_dir)
        cmds.move(0, 0, -10, elbow_pv_dir, relative=True)  # More it backwards (in front of the elbow)
        hierarchy_utils.parent(elbow_pv_dir, elbow)

        elbow_dir_loc = cmds.spaceLocator(name=f'{elbow_tag}_dirParent_{NamingConstants.Suffix.LOC}')[0]
        elbow_aim_loc = cmds.spaceLocator(name=f'{elbow_tag}_dirAim_{NamingConstants.Suffix.LOC}')[0]
        elbow_upvec_loc = cmds.spaceLocator(name=f'{elbow_tag}_dirParentUp_{NamingConstants.Suffix.LOC}')[0]
        elbow_upvec_loc_grp = f'{elbow_tag}_dirParentUp_{NamingConstants.Suffix.GRP}'
        elbow_upvec_loc_grp = cmds.group(name=elbow_upvec_loc_grp, empty=True, world=True)

        elbow_dir_loc = Node(elbow_dir_loc)
        elbow_aim_loc = Node(elbow_aim_loc)
        elbow_upvec_loc = Node(elbow_upvec_loc)
        elbow_upvec_loc_grp = Node(elbow_upvec_loc_grp)

        # Hide Reference Elements
        hierarchy_utils.parent(elbow_aim_loc, elbow_dir_loc)
        hierarchy_utils.parent(elbow_dir_loc, root)
        hierarchy_utils.parent(elbow_upvec_loc_grp, root)
        hierarchy_utils.parent(elbow_upvec_loc, elbow_upvec_loc_grp)

        cmds.pointConstraint(shoulder, elbow_dir_loc.get_long_name())
        cmds.pointConstraint([wrist, shoulder], elbow_aim_loc.get_long_name())
        cmds.aimConstraint(wrist, elbow_dir_loc.get_long_name())
        cmds.pointConstraint(shoulder, elbow_upvec_loc_grp.get_long_name(), skip=['x', 'z'])

        elbow_divide_node = create_node(node_type='multiplyDivide', name=f'{elbow_tag}_divide')
        cmds.setAttr(f'{elbow_divide_node}.operation', 2)  # Change operation to Divide
        cmds.setAttr(f'{elbow_divide_node}.input2X', -2)
        cmds.connectAttr(f'{wrist}.ty', f'{elbow_divide_node}.input1X')
        cmds.connectAttr(f'{elbow_divide_node}.outputX', f'{elbow_upvec_loc}.ty')

        cmds.pointConstraint(shoulder, elbow_dir_loc.get_long_name())
        cmds.pointConstraint([shoulder, wrist], elbow_aim_loc.get_long_name())

        cmds.connectAttr(f'{elbow_dir_loc}.rotate', f'{elbow_offset}.rotate')
        cmds.pointConstraint([wrist, shoulder], elbow_offset)

        aim_vec = self.get_orientation_data().get_aim_axis()

        cmds.aimConstraint(wrist, elbow_dir_loc.get_long_name(), aimVector=aim_vec, upVector=aim_vec,
                           worldUpType='object', worldUpObject=elbow_upvec_loc.get_long_name())
        cmds.aimConstraint(elbow_aim_loc.get_long_name(), elbow.get_long_name(), aimVector=(0, 0, 1),
                           upVector=(0, 1, 0), worldUpType='none', skip=['y', 'z'])

        cmds.setAttr(f'{elbow}.tz', -0.01)

        # Elbow Limits and Locks
        cmds.setAttr(f'{elbow}.maxTransZLimit', -0.01)
        cmds.setAttr(f'{elbow}.maxTransZLimitEnable', True)

        set_attr_state(obj_list=str(elbow), attr_list="rotate", locked=True)

        # Elbow Hide Setup
        set_attr(obj_list=[elbow_pv_dir, elbow_upvec_loc_grp, elbow_dir_loc],
                 attr_list="visibility", value=0)  # Set Visibility to Off
        set_attr(obj_list=[elbow_pv_dir, elbow_upvec_loc_grp, elbow_dir_loc],
                 attr_list="hiddenInOutliner", value=1)  # Set Outline Hidden to On

        self.clavicle.apply_transforms()
        self.shoulder.apply_transforms()
        self.wrist.apply_transforms()
        self.elbow.apply_transforms()
        cmds.select(clear=True)

    def build_skeleton_joints(self):
        super().build_skeleton_joints()  # Passthrough

    def build_skeleton_hierarchy(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        self.elbow.set_parent_uuid(self.shoulder.get_uuid())
        self.wrist.set_parent_uuid(self.elbow.get_uuid())
        super().build_skeleton_hierarchy()  # Passthrough
        self.elbow.clear_parent_uuid()
        self.wrist.clear_parent_uuid()

    def build_rig(self, project_prefix=None, **kwargs):
        # Get Elements
        direction_crv = find_direction_curve()
        module_parent_jnt = find_joint_from_uuid(self.get_parent_uuid())  # TODO TEMP @@@
        clavicle_jnt = find_joint_from_uuid(self.clavicle.get_uuid())
        shoulder_jnt = find_joint_from_uuid(self.shoulder.get_uuid())
        elbow_jnt = find_joint_from_uuid(self.elbow.get_uuid())
        wrist_jnt = find_joint_from_uuid(self.wrist.get_uuid())
        arm_jnt_list = [clavicle_jnt, shoulder_jnt, elbow_jnt, wrist_jnt]

        # Set Colors
        for jnt in arm_jnt_list:
            set_color_viewport(obj_list=jnt, rgb_color=(.3, .3, 0))

        # Get General Scale
        arm_scale = dist_center_to_center(shoulder_jnt, elbow_jnt)
        arm_scale += dist_center_to_center(elbow_jnt, wrist_jnt)

        joint_automation_grp = find_or_create_joint_automation_group()
        module_parent_jnt = get_driven_joint(self.get_parent_uuid())
        hierarchy_utils.parent(source_objects=module_parent_jnt, target_parent=joint_automation_grp)

        # Create Automation Skeletons (FK/IK)
        clavicle_parent = module_parent_jnt
        if module_parent_jnt:
            set_color_viewport(obj_list=clavicle_parent, rgb_color=ColorConstants.RigJoint.AUTOMATION)
            rescale_joint_radius(joint_list=clavicle_parent, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_DRIVEN)
        else:
            clavicle_parent = joint_automation_grp

        clavicle_fk = duplicate_joint_for_automation(clavicle_jnt, suffix="fk", parent=clavicle_parent)
        shoulder_fk = duplicate_joint_for_automation(shoulder_jnt, suffix="fk", parent=clavicle_fk)
        elbow_fk = duplicate_joint_for_automation(elbow_jnt, suffix="fk", parent=shoulder_fk)
        wrist_fk = duplicate_joint_for_automation(wrist_jnt, suffix="fk", parent=elbow_fk)
        fk_joints = [clavicle_fk, shoulder_fk, elbow_fk, wrist_fk]

        clavicle_ik = duplicate_joint_for_automation(clavicle_jnt, suffix="ik", parent=clavicle_parent)
        shoulder_ik = duplicate_joint_for_automation(shoulder_jnt, suffix="ik", parent=clavicle_ik)
        elbow_ik = duplicate_joint_for_automation(elbow_jnt, suffix="ik", parent=shoulder_ik)
        wrist_ik = duplicate_joint_for_automation(wrist_jnt, suffix="ik", parent=elbow_ik)
        ik_joints = [clavicle_ik, shoulder_ik, elbow_ik, wrist_ik]

        rescale_joint_radius(joint_list=fk_joints, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_FK)
        rescale_joint_radius(joint_list=ik_joints, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_IK)
        set_color_viewport(obj_list=fk_joints, rgb_color=ColorConstants.RigJoint.FK)
        set_color_viewport(obj_list=ik_joints, rgb_color=ColorConstants.RigJoint.IK)
        set_color_outliner(obj_list=fk_joints, rgb_color=ColorConstants.RigOutliner.FK)
        set_color_outliner(obj_list=ik_joints, rgb_color=ColorConstants.RigOutliner.IK)

        # Forearm Twist ------------------------------------------------------------------------------------
        forearm_name = self._assemble_new_node_name(name=f"forearm_{NamingConstants.Suffix.DRIVEN}",
                                                    project_prefix=project_prefix)
        forearm = duplicate_joint_for_automation(joint=wrist_jnt, parent=joint_automation_grp)
        set_color_viewport(obj_list=forearm, rgb_color=ColorConstants.RigJoint.AUTOMATION)
        forearm.rename(forearm_name)
        set_equidistant_transforms(start=elbow_jnt, end=wrist_jnt, target_list=forearm, constraint='point')
        forearm_radius = (self.elbow.get_locator_scale() + self.wrist.get_locator_scale())/2
        set_attr(obj_list=forearm, attr_list="radius", value=forearm_radius)

        # Is Twist Activated
        if self.get_metadata_value(self.META_FOREARM_ACTIVE) is True:
            print("Forearm is active")

        print(f'arm_scale: {arm_scale}')
        print("build arm rig!")

        # Clavicle Control
        clavicle_scale = dist_center_to_center(clavicle_jnt, shoulder_jnt)
        clavicle_ctrl = self._assemble_ctrl_name(name=self.clavicle.get_name())
        clavicle_ctrl = create_ctrl_curve(name=clavicle_ctrl, curve_file_name="_pin_pos_y")
        self.add_driver_uuid_attr(target=clavicle_ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=self.clavicle)
        clavicle_offset = add_offset_transform(target_list=clavicle_ctrl)[0]
        clavicle_offset = Node(clavicle_offset)
        match_transform(source=clavicle_jnt, target_list=clavicle_offset)
        scale_shapes(obj_transform=clavicle_ctrl, offset=clavicle_scale*.2)
        module_orientation = self.get_orientation_data()
        aim_axis = module_orientation.get_aim_axis()
        rotate_offset = multiply_collection_by_number(collection=aim_axis, number=90)
        rotate_shapes(obj_transform=clavicle_ctrl, offset=(rotate_offset[0], 30, 0))
        offset_control_orientation(ctrl=clavicle_ctrl, offset_transform=clavicle_offset, orient_tuple=(90, 0, 0))
        hierarchy_utils.parent(source_objects=clavicle_offset, target_parent=direction_crv)
        cmds.parentConstraint(clavicle_ctrl, clavicle_jnt, maintainOffset=True)
        color = get_directional_color(object_name=clavicle_ctrl)
        set_color_viewport(obj_list=clavicle_ctrl, rgb_color=color)


        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [clavicle_offset]


class ModuleBipedArmLeft(ModuleBipedArm):
    def __init__(self, name="Left Arm", prefix=NamingConstants.Prefix.LEFT, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)

        pos_clavicle = Vector3(x=3, y=130)
        pos_shoulder = Vector3(x=17.2, y=130)
        pos_elbow = Vector3(x=37.7, y=130)
        pos_wrist = Vector3(x=58.2, y=130)

        self.clavicle.set_initial_position(xyz=pos_clavicle)
        self.shoulder.set_initial_position(xyz=pos_shoulder)
        self.elbow.set_initial_position(xyz=pos_elbow)
        self.wrist.set_initial_position(xyz=pos_wrist)


class ModuleBipedArmRight(ModuleBipedArm):
    def __init__(self, name="Right Arm", prefix=NamingConstants.Prefix.RIGHT, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(-1, 0, 0), up_axis=(0, 0, -1), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)

        pos_clavicle = Vector3(x=-3, y=130)
        pos_shoulder = Vector3(x=-17.2, y=130)
        pos_elbow = Vector3(x=-37.7, y=130)
        pos_wrist = Vector3(x=-58.2, y=130)

        self.clavicle.set_initial_position(xyz=pos_clavicle)
        self.shoulder.set_initial_position(xyz=pos_shoulder)
        self.elbow.set_initial_position(xyz=pos_elbow)
        self.wrist.set_initial_position(xyz=pos_wrist)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.utils.session_utils import remove_modules_startswith
    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject
    from gt.tools.auto_rigger.rig_module_spine import ModuleSpine

    a_spine = ModuleSpine()
    a_arm = ModuleBipedArm()
    a_arm_lf = ModuleBipedArmLeft()
    a_arm_rt = ModuleBipedArmRight()

    spine_chest_uuid = a_spine.chest.get_uuid()
    a_arm_lf.set_parent_uuid(spine_chest_uuid)
    a_arm_rt.set_parent_uuid(spine_chest_uuid)

    a_project = RigProject()
    a_project.add_to_modules(a_spine)
    a_project.add_to_modules(a_arm_rt)
    a_project.add_to_modules(a_arm_lf)
    a_project.build_proxy()
    a_project.build_rig()

    # cmds.setAttr(f'{a_arm_rt.get_prefix()}_{a_arm_rt.clavicle.get_name()}.ty', 15)
    # cmds.setAttr(f'{a_arm_rt.get_prefix()}_{a_arm_rt.elbow.get_name()}.tz', -15)
    # cmds.setAttr(f'{a_arm_lf.get_prefix()}_{a_arm_lf.clavicle.get_name()}.ty', 15)
    # cmds.setAttr(f'{a_arm_lf.get_prefix()}_{a_arm_lf.elbow.get_name()}.tz', -15)
    # cmds.setAttr(f'{a_arm_lf.get_prefix()}_{a_arm_lf.elbow.get_name()}.ty', -35)
    # # cmds.setAttr(f'rt_elbow.tz', -15)
    #
    # a_project.read_data_from_scene()
    # dictionary = a_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = RigProject()
    # a_project2.read_data_from_dict(dictionary)
    # print(a_project2.get_project_as_dict().get("modules"))
    # a_project2.build_proxy()

    # Frame all
    cmds.viewFit(all=True)
