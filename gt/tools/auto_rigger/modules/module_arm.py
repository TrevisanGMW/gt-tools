"""
Auto Rigger Arm Module
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.transform as core_trans
import gt.core.rigging as core_rigging
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.core.color as core_color
import gt.core.curve as core_curve
import gt.core.attr as core_attr
import gt.core.math as core_math
import gt.core.node as core_node
import gt.core.str as core_str
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleArm(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_biped_arm
    allow_parenting = True
    allow_multiple = True

    # Reference Attributes and Metadata Keys
    REF_ATTR_ELBOW_PROXY_PV = "elbowProxyPoleVectorLookupAttr"

    def __init__(
        self,
        name="Arm",
        prefix=None,
        suffix=None,
        clavicle_world=False,
        create_twist_joints=True,
        auto_pole_vector=True,
        ik_world=True,
    ):
        """
        Initializes an Arm module.

        Args:
            name (str): The name of the module. Default is "Arm".
            prefix (str, optional): Optional prefix for the module.
            suffix (str, optional): Optional suffix for the module.
            clavicle_world (bool): Whether the clavicle control should orient to world space. Default is False.
            create_twist_joints (bool): Whether to create twist joints for the upper and lower arm. Default is True.
            auto_pole_vector (bool): Whether the IK pole vector should be automatically calculated. Default is True.
            ik_world (bool): Whether the IK control should be aligned to world orientation. Default is True.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 0), up_dir=(0, -1, 0))
        self.set_orientation(orientation_data=_orientation)
        self.set_orientation_method(method="inherit")

        # Extra Module Data
        self.setup_name = "arm"
        self.rig_pose_clavicle_rot = (0, 0, 0)  # vector3 - offset value used to create the control rig pose
        self.rig_pose_elbow_rot = -0.2  # float - offset value used to create the control rig pose
        self.create_twist_joints = create_twist_joints
        self.upperarm_twist_joints = []
        self.lowerarm_twist_joints = []
        self.auto_pole_vector = auto_pole_vector
        self.clavicle_world = clavicle_world
        self.ik_world = ik_world
        self.upperarm_dir_curve = None
        self.lowerarm_dir_curve = None
        self.dir_curve = "_joint_arrow_dir_pos_x"
        self.dir_rot = -90

        clavicle_name = "clavicle"
        upperarm_name = "upperArm"
        lowerarm_name = "lowerArm"
        hand_name = "hand"

        pos_clavicle = core_trans.Vector3()
        self.pos_shoulder = core_trans.Vector3(z=17.2, y=0)
        self.pos_elbow = core_trans.Vector3(z=37.7, y=0)
        pos_wrist = core_trans.Vector3(z=58.2, y=0)

        # Default Proxies
        self.clavicle_proxy = tools_rig_frm.Proxy(name=clavicle_name)
        self.clavicle_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_x"))
        self.clavicle_proxy.set_initial_position(xyz=pos_clavicle)
        self.clavicle_proxy.set_locator_scale(scale=2)
        self.clavicle_proxy.set_meta_purpose(value="clavicle")
        self.clavicle_proxy.set_offset_rotation(x=-90, y=-90)
        self.clavicle_proxy.set_rotation(x=180, y=-90)
        self.clavicle_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.clavicle_proxy.set_rotation_order("xzy")

        self.upperarm_proxy = tools_rig_frm.Proxy(name=f"{upperarm_name}")
        self.upperarm_proxy.set_initial_position(xyz=self.pos_shoulder)
        self.upperarm_proxy.set_locator_scale(scale=2)
        self.upperarm_proxy.set_parent_uuid(self.clavicle_proxy.get_uuid())
        self.upperarm_proxy.set_meta_purpose(value="upperArm")
        self.upperarm_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.upperarm_proxy.set_rotation_order("xzy")

        self.lowerarm_proxy = tools_rig_frm.Proxy(name=f"{lowerarm_name}")
        self.lowerarm_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_arrow_neg_z"))
        self.lowerarm_proxy.set_initial_position(xyz=self.pos_elbow)
        self.lowerarm_proxy.set_locator_scale(scale=2.2)
        self.lowerarm_proxy.add_line_parent(line_parent=self.upperarm_proxy)
        self.lowerarm_proxy.set_meta_purpose(value="lowerArm")
        self.lowerarm_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )
        self.lowerarm_proxy.set_rotation_order("xyz")

        self.hand_proxy = tools_rig_frm.Proxy(name=hand_name)
        self.hand_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_x_pos_z_up"))
        self.hand_proxy.set_initial_position(xyz=pos_wrist)
        self.hand_proxy.set_locator_scale(scale=2)
        self.hand_proxy.add_line_parent(line_parent=self.lowerarm_proxy)
        self.hand_proxy.set_meta_purpose(value="hand")
        self.hand_proxy.set_offset_rotation(x=-90, y=-90)
        self.hand_proxy.set_rotation(x=180, y=-90)
        self.hand_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
                tools_rig_const.RiggerDriverTypes.SWITCH,
            ]
        )
        self.hand_proxy.set_rotation_order("zyx")

        # Update Proxies
        self.proxies = [self.clavicle_proxy, self.upperarm_proxy, self.lowerarm_proxy, self.hand_proxy]

    def set_orientation_direction(self, is_positive, **kwargs):
        """
        Sets the direction of the orientation.
        If positive, it will use "1" in the desired axis.
        If negative, (not positive) it will use "-1" in the desired axis.
        Args:
            is_positive (bool): If True, it's set to a positive direction, if False to negative.
                                e.g. True = (1, 0, 0) while False (-1, 0, 0)
            **kwargs: Additional keyword arguments passed to the parent implementation.
        """
        super().set_orientation_direction(
            is_positive=is_positive,
            set_aim_axis=True,
            set_up_axis=True,
            set_up_dir=False,
        )  # No Up Direction

    def set_proxies_name(self, name):
        """
        Sets the base name used to generate proxy node names.

        Args:
            name (str): The name to be used for the proxies.
        """
        self.setup_name = name

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
            logger.debug(f"Unable to read proxies from dictionary. Input must be a dictionary.")
            return
        self.read_purpose_matching_proxy_from_dict(proxy_dict)

    def set_rig_pose_clavicle_rot(self, clavicle_rotation):
        """
        Sets the set_rig_pose_clavicle_rot class variable used to set the control rig pose for this module.

        Args:
            clavicle_rotation (vector3): float vector of 3
        """
        if isinstance(clavicle_rotation, (list, tuple)):
            self.rig_pose_clavicle_rot = clavicle_rotation
        else:
            logger.warning("Given clavicle rotation is not a list or tuple. Skipped.")

    def set_rig_pose_elbow_rot(self, elbow_rotation):
        """
        Sets the set_rig_pose_elbow_rot class variable used to set the control rig pose for this module.

        Args:
            elbow_rotation (int, float): numerical value to set
        """
        if isinstance(elbow_rotation, (float, int)):
            self.rig_pose_elbow_rot = float(elbow_rotation)
        else:
            logger.warning("Given elbow rotation is not an int or a float. Skipped.")

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
        # Set the proxy parent_uuid and driver_uuid for the proxy construction hierarchy
        # (parent_uuid for the skeleton hierarchy, driver_uuid to adjust proxies transformations)

        if self.parent_uuid:
            self.clavicle_proxy.set_parent_uuid(self.parent_uuid)
        self.upperarm_proxy.set_setup_driver_uuid(self.clavicle_proxy.get_uuid())
        self.upperarm_proxy.set_parent_uuid(self.clavicle_proxy.get_uuid())
        self.lowerarm_proxy.set_setup_driver_uuid(self.hand_proxy.get_uuid())
        self.lowerarm_proxy.set_parent_uuid(self.upperarm_proxy.get_uuid())
        self.hand_proxy.set_setup_driver_uuid(self.upperarm_proxy.get_uuid())
        self.hand_proxy.set_parent_uuid(self.upperarm_proxy.get_uuid())

        proxy = super().build_proxy()  # Passthrough

        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """

        # Get Formatted Prefix and Suffix
        _prefix = ""
        if self.prefix:
            _prefix = f"{self.prefix}_"
        _suffix = ""
        if self.suffix:
            _suffix = f"_{self.suffix}"

        # Get Maya Elements
        global_proxy = tools_rig_utils.find_ctrl_global_proxy()
        upperarm = tools_rig_utils.find_proxy_from_uuid(self.upperarm_proxy.get_uuid())
        lowerarm = tools_rig_utils.find_proxy_from_uuid(self.lowerarm_proxy.get_uuid())
        hand = tools_rig_utils.find_proxy_from_uuid(self.hand_proxy.get_uuid())

        self.clavicle_proxy.apply_offset_transform()
        self.upperarm_proxy.apply_offset_transform()
        self.lowerarm_proxy.apply_offset_transform()
        self.hand_proxy.apply_offset_transform()

        self.upperarm_dir_curve = core_curve.get_curve(self.dir_curve)
        self.upperarm_dir_curve.set_name(f"{_prefix}{self.upperarm_proxy.get_name()}{_suffix}_dir")
        self.upperarm_dir_curve = self.upperarm_dir_curve.build()
        self.upperarm_dir_curve = core_node.Node(self.upperarm_dir_curve)
        core_curve.rescale_curve(self.upperarm_dir_curve, 4)
        upperarm_dir_offset = core_hrchy.add_offset_transform(self.upperarm_dir_curve)[0]
        cmds.delete(cmds.parentConstraint(upperarm, upperarm_dir_offset))
        cmds.parent(upperarm_dir_offset, upperarm)
        cmds.setAttr(f"{upperarm_dir_offset}.rx", self.dir_rot)

        self.lowerarm_dir_curve = core_curve.get_curve(self.dir_curve)
        self.lowerarm_dir_curve.set_name(f"{_prefix}{self.lowerarm_proxy.get_name()}{_suffix}_dir")
        self.lowerarm_dir_curve = self.lowerarm_dir_curve.build()
        self.lowerarm_dir_curve = core_node.Node(self.lowerarm_dir_curve)
        core_curve.rescale_curve(self.lowerarm_dir_curve, 4)
        lowerarm_dir_offset = core_hrchy.add_offset_transform(self.lowerarm_dir_curve)[0]
        cmds.delete(cmds.parentConstraint(lowerarm, lowerarm_dir_offset))
        cmds.parent(lowerarm_dir_offset, lowerarm)
        cmds.setAttr(f"{lowerarm_dir_offset}.rx", self.dir_rot)

        # UpperArm -----------------------------------------------------------------------------------
        core_attr.hide_lock_default_attrs(upperarm, rotate=True, scale=True)

        # LowerArm  -------------------------------------------------------------------------------------
        core_attr.hide_lock_default_attrs(lowerarm, scale=True)
        lowerarm_tag = lowerarm.get_short_name()

        # Direction Setup
        aim_vec = self.get_orientation_data().get_aim_axis()
        up_vec = self.get_orientation_data().get_up_axis()

        cmds.aimConstraint(
            lowerarm,
            self.upperarm_dir_curve,
            aimVector=aim_vec,
            upVector=up_vec,
            worldUpObject=lowerarm,
            worldUpType="objectrotation",
        )

        core_attr.hide_lock_default_attrs(self.lowerarm_dir_curve, scale=True, rotate=True, translate=True)
        core_attr.hide_lock_default_attrs(self.upperarm_dir_curve, scale=True, rotate=True, translate=True)
        cmds.setAttr(f"{self.lowerarm_dir_curve}.overrideEnabled", 1)
        cmds.setAttr(f"{self.lowerarm_dir_curve}.overrideDisplayType", 2)
        cmds.setAttr(f"{self.upperarm_dir_curve}.overrideEnabled", 1)
        cmds.setAttr(f"{self.upperarm_dir_curve}.overrideDisplayType", 2)

        # LowerArm Setup
        lowerarm_offset = tools_rig_utils.get_proxy_offset(lowerarm)
        lowerarm_pv_dir = cmds.spaceLocator(name=f"{lowerarm_tag}_poleVectorDir")[0]
        core_attr.add_attr(
            obj_list=lowerarm_pv_dir,
            attributes=ModuleArm.REF_ATTR_ELBOW_PROXY_PV,
            attr_type="string",
        )
        lowerarm_pv_dir = core_node.Node(lowerarm_pv_dir)
        core_trans.match_translate(source=lowerarm, target_list=lowerarm_pv_dir)
        cmds.move(0, 0, -10, lowerarm_pv_dir, relative=True)  # Move it backwards (in front of the elbow)
        core_hrchy.parent(lowerarm_pv_dir, lowerarm)

        lowerarm_dir_loc = cmds.spaceLocator(name=f"{lowerarm_tag}_dirParent_{core_naming.NamingConstants.Suffix.LOC}")[
            0
        ]
        lowerarm_aim_loc = cmds.spaceLocator(name=f"{lowerarm_tag}_dirAim_{core_naming.NamingConstants.Suffix.LOC}")[0]
        lowerarm_upvec_loc = cmds.spaceLocator(
            name=f"{lowerarm_tag}_dirParentUp_{core_naming.NamingConstants.Suffix.LOC}"
        )[0]
        lowerarm_upvec_loc_grp = f"{lowerarm_tag}_dirParentUp_{core_naming.NamingConstants.Suffix.GRP}"
        lowerarm_upvec_loc_grp = core_hrchy.create_group(name=lowerarm_upvec_loc_grp)

        lowerarm_dir_loc = core_node.Node(lowerarm_dir_loc)
        lowerarm_aim_loc = core_node.Node(lowerarm_aim_loc)
        lowerarm_upvec_loc = core_node.Node(lowerarm_upvec_loc)

        dir_aim_con = cmds.aimConstraint(
            hand,
            lowerarm_dir_offset,
            aimVector=aim_vec,
            upVector=up_vec,
            worldUpObject=lowerarm,
            worldUpType="objectrotation",
        )[0]
        if round(cmds.getAttr(f"{lowerarm_dir_offset}.rx"), 2) != self.dir_rot:
            cmds.setAttr(f"{dir_aim_con}.offsetX", self.dir_rot)

        # Hide Reference Elements
        core_hrchy.parent(lowerarm_aim_loc, lowerarm_dir_loc)
        core_hrchy.parent(lowerarm_dir_loc, upperarm)
        core_hrchy.parent(lowerarm_upvec_loc_grp, global_proxy)
        core_hrchy.parent(lowerarm_upvec_loc, lowerarm_upvec_loc_grp)

        cmds.pointConstraint([hand, upperarm], lowerarm_aim_loc.get_long_name())
        cmds.aimConstraint(hand, lowerarm_dir_loc.get_long_name())
        cmds.pointConstraint(upperarm, lowerarm_upvec_loc_grp.get_long_name(), skip=["x", "z"])

        lowerarm_divide_node = core_node.create_node(node_type="multiplyDivide", name=f"{lowerarm_tag}_divide")
        cmds.setAttr(f"{lowerarm_divide_node}.operation", 2)  # Change operation to Divide
        cmds.setAttr(f"{lowerarm_divide_node}.input2X", -2)
        cmds.connectAttr(f"{hand}.ty", f"{lowerarm_divide_node}.input1X")
        cmds.connectAttr(f"{lowerarm_divide_node}.outputX", f"{lowerarm_upvec_loc}.ty")

        cmds.pointConstraint(upperarm, lowerarm_dir_loc.get_long_name())
        cmds.pointConstraint([upperarm, hand], lowerarm_aim_loc.get_long_name())

        cmds.connectAttr(f"{lowerarm_dir_loc}.rotate", f"{lowerarm_offset}.rotate")
        cmds.pointConstraint([hand, upperarm], lowerarm_offset)

        cmds.aimConstraint(
            hand,
            lowerarm_dir_loc.get_long_name(),
            aimVector=aim_vec,
            upVector=aim_vec,
            worldUpType="object",
            worldUpObject=lowerarm_upvec_loc.get_long_name(),
        )
        cmds.aimConstraint(
            lowerarm_aim_loc.get_long_name(),
            lowerarm.get_long_name(),
            aimVector=(0, 0, 1),
            upVector=(0, 1, 0),
            worldUpType="none",
            skip=["y", "z"],
        )

        cmds.setAttr(f"{lowerarm}.tz", -0.01)

        # LowerArm Limits and Locks
        cmds.setAttr(f"{lowerarm}.maxTransZLimit", -0.01)
        cmds.setAttr(f"{lowerarm}.maxTransZLimitEnable", True)

        core_attr.set_attr_state(obj_list=str(lowerarm), attr_list="rotate", locked=True)

        # LowerArm Hide Setup
        core_attr.set_attr(
            obj_list=[lowerarm_pv_dir, lowerarm_upvec_loc_grp, lowerarm_dir_loc],
            attr_list="visibility",
            value=0,
        )  # Set Visibility to Off
        core_attr.set_attr(
            obj_list=[lowerarm_pv_dir, lowerarm_upvec_loc_grp, lowerarm_dir_loc],
            attr_list="hiddenInOutliner",
            value=1,
        )  # Set Outline Hidden to On

        self.clavicle_proxy.apply_transforms()
        self.upperarm_proxy.apply_transforms()
        self.hand_proxy.apply_transforms()
        self.lowerarm_proxy.apply_transforms()

        # Set proxy parent for the skeleton hierarchy
        self.upperarm_proxy.set_parent_uuid(self.clavicle_proxy.get_uuid())
        self.lowerarm_proxy.set_parent_uuid(self.upperarm_proxy.get_uuid())
        self.hand_proxy.set_parent_uuid(self.lowerarm_proxy.get_uuid())

    def build_skeleton_joints(self):
        """
        Runs skeleton joints phase, which creates joints out of the proxy elements.
        This  happens after "build_proxy_setup" and as these are used to create the joints.
        """
        super().build_skeleton_joints()

    def build_skeleton_hierarchy(self):
        """
        Runs skeletal hierarchy phase (post skeleton). Joints are parented and oriented during this step.
        Happens after the "build_skeleton_joints" function in a project.
        """
        logger.debug(f'"build_skeleton_hierarchy" function from "{self.get_module_class_name()}" was called.')
        module_uuids = self.get_proxies_uuids()
        jnt_nodes = []
        for proxy in self.proxies:
            joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            if not joint:
                continue
            proxy_obj_path = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
            # Inherit Rotation Order
            proxy_rotation_order = cmds.getAttr(f"{proxy_obj_path}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
            cmds.setAttr(f"{joint}.rotateOrder", proxy_rotation_order)
            # Inherit Orientation (Before Parenting)
            if proxy == self.upperarm_proxy:
                proxy_obj_path = self.upperarm_dir_curve
            elif proxy == self.lowerarm_proxy:
                proxy_obj_path = self.lowerarm_dir_curve
            cmds.delete(cmds.orientConstraint(proxy_obj_path, joint))
            cmds.makeIdentity(joint, a=True, r=True)
            # Parent Joint (Internal Proxies)
            parent_uuid = proxy.get_parent_uuid()
            if parent_uuid in module_uuids:
                parent_joint_node = tools_rig_utils.find_joint_from_uuid(parent_uuid)
                core_hrchy.parent(source_objects=joint, target_parent=parent_joint_node)
            jnt_nodes.append(joint)
        # Parent Joints (External Proxies)
        for proxy in self.proxies:
            parent_uuid = proxy.get_parent_uuid()
            if parent_uuid not in module_uuids:
                joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
                parent_joint_node = tools_rig_utils.find_joint_from_uuid(parent_uuid)
                core_hrchy.parent(source_objects=joint, target_parent=parent_joint_node)
        cmds.select(clear=True)

        # Twist joints
        if self.create_twist_joints:
            upperarm_jnt = tools_rig_utils.find_joint_from_uuid(self.upperarm_proxy.get_uuid()).get_short_name()
            lowerarm_jnt = tools_rig_utils.find_joint_from_uuid(self.lowerarm_proxy.get_uuid()).get_short_name()
            hand_jnt = tools_rig_utils.find_joint_from_uuid(self.hand_proxy.get_uuid()).get_short_name()
            self.upperarm_twist_joints = tools_rig_utils.create_twist_joints(
                upperarm_jnt, lowerarm_jnt, copy_start=True
            )
            self.lowerarm_twist_joints = tools_rig_utils.create_twist_joints(lowerarm_jnt, hand_jnt, copy_end=True)

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """

        # Twist Setup
        if self.create_twist_joints:
            tools_rig_utils.create_twist_setup(
                twist_jnt_list=self.upperarm_twist_joints, mid_joints=2, side=self.prefix, reverse=True
            )
            tools_rig_utils.create_twist_setup(
                twist_jnt_list=self.lowerarm_twist_joints, mid_joints=2, side=self.prefix
            )
            all_twist_jnts = self.upperarm_twist_joints + self.lowerarm_twist_joints
            tools_rig_utils.extract_twist_rotation(twist_jnt_list=all_twist_jnts)

        # Get Elements
        global_ctrl = tools_rig_utils.find_ctrl_global()
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        clavicle_jnt = tools_rig_utils.find_joint_from_uuid(self.clavicle_proxy.get_uuid())
        upperarm_jnt = tools_rig_utils.find_joint_from_uuid(self.upperarm_proxy.get_uuid())
        lowerarm_jnt = tools_rig_utils.find_joint_from_uuid(self.lowerarm_proxy.get_uuid())
        hand_jnt = tools_rig_utils.find_joint_from_uuid(self.hand_proxy.get_uuid())
        module_jnt_list = [clavicle_jnt, upperarm_jnt, lowerarm_jnt, hand_jnt]

        # Get Formatted Prefix
        _prefix = ""
        if self.prefix:
            _prefix = f"{self.prefix}_"
        _suffix = ""
        if self.suffix:
            _suffix = f"_{self.suffix}"

        # Set Colors
        for jnt in module_jnt_list:
            core_color.set_color_viewport(obj_list=jnt, rgb_color=(0.3, 0.3, 0))

        # Get General Scale
        arm_scale = core_math.dist_center_to_center(upperarm_jnt, lowerarm_jnt)
        arm_scale += core_math.dist_center_to_center(lowerarm_jnt, hand_jnt)

        # Create Parent Automation Elements
        joint_automation_grp = tools_rig_utils.find_or_create_joint_automation_group()
        general_automation_grp = tools_rig_utils.get_automation_group()
        module_parent_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())
        core_hrchy.parent(source_objects=module_parent_jnt, target_parent=joint_automation_grp)

        # Create Automation Skeletons (FK/IK)
        clavicle_parent = module_parent_jnt
        if module_parent_jnt:
            core_color.set_color_viewport(
                obj_list=clavicle_parent,
                rgb_color=core_color.ColorConstants.RigJoint.AUTOMATION,
            )
            core_rigging.rescale_joint_radius(
                joint_list=clavicle_parent,
                multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_DRIVEN,
            )
        else:
            clavicle_parent = joint_automation_grp

        clavicle_fk = core_rigging.duplicate_joint_for_automation(clavicle_jnt, suffix="fk", parent=clavicle_parent)
        upperarm_fk = core_rigging.duplicate_joint_for_automation(upperarm_jnt, suffix="fk", parent=clavicle_fk)
        lowerarm_fk = core_rigging.duplicate_joint_for_automation(lowerarm_jnt, suffix="fk", parent=upperarm_fk)
        hand_fk = core_rigging.duplicate_joint_for_automation(hand_jnt, suffix="fk", parent=lowerarm_fk)
        fk_joints = [clavicle_fk, upperarm_fk, lowerarm_fk, hand_fk]

        clavicle_ik = core_rigging.duplicate_joint_for_automation(clavicle_jnt, suffix="ik", parent=clavicle_parent)
        upperarm_ik = core_rigging.duplicate_joint_for_automation(upperarm_jnt, suffix="ik", parent=clavicle_ik)
        lowerarm_ik = core_rigging.duplicate_joint_for_automation(lowerarm_jnt, suffix="ik", parent=upperarm_ik)
        hand_ik = core_rigging.duplicate_joint_for_automation(hand_jnt, suffix="ik", parent=lowerarm_ik)
        ik_joints = [clavicle_ik, upperarm_ik, lowerarm_ik, hand_ik]

        core_rigging.rescale_joint_radius(
            joint_list=fk_joints,
            multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_FK,
        )
        core_rigging.rescale_joint_radius(
            joint_list=ik_joints,
            multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_IK,
        )
        core_color.set_color_viewport(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigJoint.FK)
        core_color.set_color_viewport(obj_list=ik_joints, rgb_color=core_color.ColorConstants.RigJoint.IK)
        core_color.set_color_outliner(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigOutliner.FK)
        core_color.set_color_outliner(obj_list=ik_joints, rgb_color=core_color.ColorConstants.RigOutliner.IK)

        # FK Controls ----------------------------------------------------------------------------------------

        fk_offsets_ctrls = []
        # Clavicle Control
        clavicle_scale = core_math.dist_center_to_center(clavicle_jnt, upperarm_jnt)
        if self.clavicle_world:
            pos_loc = cmds.spaceLocator()[0]
            core_trans.match_translate(source=clavicle_fk, target_list=pos_loc)
            if self.prefix == core_naming.NamingConstants.Prefix.RIGHT:
                cmds.rotate("90deg", 0, 0, pos_loc)
            else:
                cmds.rotate("-90deg", 0, 0, pos_loc)
            rot_obj = pos_loc
        else:
            rot_obj = clavicle_jnt
        if self.prefix == core_naming.NamingConstants.Prefix.RIGHT:
            rot_offset = (270, 0, 0)
        elif self.prefix == core_naming.NamingConstants.Prefix.LEFT:
            rot_offset = (90, 0, 0)
        else:
            rot_offset = (180, 0, 0)
        clavicle_ctrl, clavicle_offset = self.create_rig_control(
            control_base_name=self.clavicle_proxy.get_name(),
            curve_file_name="primitive_tube_half",
            parent_obj=global_offset_ctrl,
            match_obj_pos=clavicle_jnt,
            match_obj_rot=rot_obj,
            add_offset_ctrl=False,
            rot_order=3,
            shape_scale=clavicle_scale * 1.2,
            shape_rot_offset=rot_offset,
            shape_pos_offset=(0, 5, 0),
            color=core_color.get_directional_color(object_name=clavicle_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=clavicle_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.clavicle_proxy,
        )
        core_cnstr.constraint_targets(source_driver=clavicle_ctrl, target_driven=clavicle_fk)
        if self.clavicle_world:
            cmds.delete(rot_obj)
        # UpperArm FK Control
        upperarm_fk_ctrl, upperarm_fk_offset = self.create_rig_control(
            control_base_name=self.upperarm_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=clavicle_ctrl,
            match_obj=upperarm_jnt,
            add_offset_ctrl=False,
            rot_order=3,
            shape_scale=arm_scale * 0.16,
            color=core_color.get_directional_color(object_name=upperarm_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=upperarm_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.upperarm_proxy,
        )

        core_cnstr.constraint_targets(source_driver=upperarm_fk_ctrl, target_driven=upperarm_fk)
        fk_offsets_ctrls.append(upperarm_fk_offset[0])

        # LowerArm FK Control
        lowerarm_fk_ctrl, lowerarm_fk_offset = self.create_rig_control(
            control_base_name=self.lowerarm_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=upperarm_fk_ctrl,
            match_obj=lowerarm_jnt,
            add_offset_ctrl=False,
            rot_order=0,
            shape_scale=arm_scale * 0.14,
            color=core_color.get_directional_color(object_name=lowerarm_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=lowerarm_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.lowerarm_proxy,
        )
        core_cnstr.constraint_targets(source_driver=lowerarm_fk_ctrl, target_driven=lowerarm_fk)
        fk_offsets_ctrls.append(lowerarm_fk_offset[0])

        # Hand FK Control
        hand_fk_ctrl, hand_fk_offset = self.create_rig_control(
            control_base_name=self.hand_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=lowerarm_fk_ctrl,
            match_obj=hand_jnt,
            add_offset_ctrl=False,
            rot_order=5,
            shape_scale=arm_scale * 0.1,
            color=core_color.get_directional_color(object_name=hand_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=hand_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.hand_proxy,
        )
        core_cnstr.constraint_targets(source_driver=hand_fk_ctrl, target_driven=hand_fk)
        fk_offsets_ctrls.append(hand_fk_offset[0])

        # IK Controls -------------------------------------------------------------------------------------
        ik_offsets_ctrls = []

        # IK LowerArm Control
        ik_suffix = core_naming.NamingConstants.Description.IK.upper()
        lowerarm_ik_ctrl, lowerarm_ik_offset = self.create_rig_control(
            control_base_name=f"{self.lowerarm_proxy.get_name()}_{ik_suffix}",
            curve_file_name="primitive_diamond",
            parent_obj=global_offset_ctrl,
            match_obj_pos=hand_jnt,
            add_offset_ctrl=False,
            shape_scale=arm_scale * 0.05,
            color=core_color.get_directional_color(object_name=lowerarm_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=lowerarm_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.lowerarm_proxy,
        )
        ik_offsets_ctrls.append(lowerarm_ik_offset[0])

        # Find Pole Vector Position
        lowerarm_guide_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.lowerarm_proxy.get_uuid())
        lowerarm_guide_proxy_children = (
            cmds.listRelatives(lowerarm_guide_proxy, children=True, typ="transform", fullPath=True) or []
        )
        lowerarm_pv_dir = tools_rig_utils.find_object_with_attr(
            attr_name=ModuleArm.REF_ATTR_ELBOW_PROXY_PV,
            lookup_list=lowerarm_guide_proxy_children,
        )

        temp_transform = core_hrchy.create_group(name=f"{lowerarm_ik_ctrl}_rotExtraction")
        cmds.delete(cmds.pointConstraint(lowerarm_jnt, temp_transform))
        cmds.delete(
            cmds.aimConstraint(
                lowerarm_pv_dir,
                temp_transform,
                offset=(0, 0, 0),
                aimVector=(1, 0, 0),
                upVector=(0, -1, 0),
                worldUpType="vector",
                worldUpVector=(0, 1, 0),
            )
        )
        cmds.move(arm_scale * 0.6, 0, 0, temp_transform, objectSpace=True, relative=True)
        cmds.delete(cmds.pointConstraint(temp_transform, lowerarm_ik_offset))
        cmds.delete(temp_transform)

        # IK Aim Line
        tools_rig_utils.create_control_visualization_line(lowerarm_ik_ctrl, lowerarm_ik)

        # IK Hand Control
        if self.prefix in [core_naming.NamingConstants.Prefix.RIGHT, core_naming.NamingConstants.Prefix.LEFT]:
            shape_offset = (0, 0, 90)
        else:
            shape_offset = (-90, 0, 90)

        if self.ik_world:
            match_rot = None
            match_rot_order = 1
            match_shape_pos_offset = (0, 0, arm_scale * -0.3)
        else:
            match_rot = hand_jnt
            match_rot_order = 5
            match_shape_pos_offset = (arm_scale * -0.3, 0, 0)

        hand_ik_ctrl, hand_ik_offset, hand_o_ik_ctrl, hand_o_ik_data = self.create_rig_control(
            control_base_name=f"{self.hand_proxy.get_name()}_{ik_suffix}",
            curve_file_name="square",
            parent_obj=global_offset_ctrl,
            rot_order=match_rot_order,
            match_obj_pos=hand_jnt,
            match_obj_rot=match_rot,
            add_offset_ctrl=True,
            shape_rot_offset=shape_offset,
            shape_scale=arm_scale * 0.25,
            color=core_color.get_directional_color(object_name=hand_jnt),
        )
        self._add_driver_uuid_attr(
            target_driver=hand_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.hand_proxy,
        )
        self._add_driver_uuid_attr(
            target_driver=hand_o_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=f"{self.hand_proxy.get_name()}Offset",
        )
        ik_offsets_ctrls.append(hand_ik_offset[0])

        # Transform under ctrl for constraint (avoid orient constraint issue)

        orient_grp = core_hrchy.create_group(name=f"{self.hand_proxy.get_name()}_{ik_suffix}_orient_grp")
        cmds.delete(cmds.parentConstraint(hand_ik, orient_grp))
        cmds.parent(orient_grp, hand_o_ik_ctrl)
        core_attr.hide_lock_default_attrs(
            obj_list=[orient_grp], rotate=True, translate=True, scale=True, visibility=True
        )

        # Attributes
        core_attr.hide_lock_default_attrs(obj_list=[hand_ik_ctrl, hand_o_ik_ctrl], scale=True, visibility=True)

        # Switch Control
        ik_switch_ctrl, ik_switch_offset = self.create_rig_control(
            control_base_name=self.setup_name,
            curve_file_name="gear_eight_sides_smooth",
            parent_obj=global_offset_ctrl,
            rot_order=match_rot_order,
            match_obj_pos=hand_jnt,
            match_obj_rot=match_rot,
            add_offset_ctrl=False,
            shape_rot_offset=shape_offset,
            shape_pos_offset=match_shape_pos_offset,
            shape_scale=arm_scale * 0.012,
            color=core_color.get_directional_color(object_name=hand_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=ik_switch_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.SWITCH,
            proxy_purpose=self.setup_name,
        )

        # Switch Setup
        core_rigging.create_switch_setup(
            source_a=ik_joints,
            source_b=fk_joints,
            target_base=module_jnt_list,
            attr_holder=ik_switch_ctrl,
            visibility_a=fk_offsets_ctrls,
            visibility_b=ik_offsets_ctrls,
            shape_visibility=False,
            prefix=self.prefix,
            invert=True,
        )
        switch_cons = core_cnstr.constraint_targets(
            source_driver=[hand_fk_ctrl, hand_ik_ctrl], target_driven=ik_switch_offset[0]
        )[0]
        arm_rev = cmds.createNode("reverse", name=f"{_prefix}arm_rev{_suffix}")
        cmds.connectAttr(f"{ik_switch_ctrl}.influenceSwitch", f"{arm_rev}.inputX")
        cmds.connectAttr(f"{arm_rev}.outputX", f"{switch_cons}.w0")
        cmds.connectAttr(f"{ik_switch_ctrl}.influenceSwitch", f"{switch_cons}.w1")

        influence_switch_attr_nice_name = "FK/IK"
        cmds.addAttr(f"{ik_switch_ctrl}.influenceSwitch", e=True, nn=influence_switch_attr_nice_name)
        cmds.setAttr(f"{ik_switch_ctrl}.influenceSwitch", 0)  # Default is FK

        # Clavicle
        cmds.parentConstraint(clavicle_ctrl, clavicle_fk, maintainOffset=True)
        cmds.parentConstraint(clavicle_ctrl, clavicle_ik, maintainOffset=True)
        # Automation
        hand_automation_grp = core_hrchy.create_group(
            name=f"{_prefix}{self.hand_proxy.get_name()}{_suffix}_automation_grp"
        )
        core_hrchy.parent(source_objects=hand_automation_grp, target_parent=general_automation_grp)

        cmds.addAttr(hand_ik_ctrl, ln="elbowTwist", nn="Elbow Twist", at="float", keyable=True)

        # Hand IK Handle
        hand_ik_handle = cmds.ikHandle(
            sj=upperarm_ik,
            ee=hand_ik,
            n=f"{_prefix}{self.hand_proxy.get_name()}{_suffix}_ikHandle",
            sol="ikRPsolver",
        )[0]
        hand_ik_handle = core_node.Node(hand_ik_handle)
        core_hrchy.parent(source_objects=hand_ik_handle, target_parent=hand_automation_grp)
        cmds.poleVectorConstraint(lowerarm_ik_ctrl, hand_ik_handle)
        cmds.pointConstraint(hand_o_ik_ctrl, hand_ik_handle, mo=True)
        cmds.orientConstraint(orient_grp, hand_ik, mo=True)

        # Elbow Ctrl Twist Rotation Functionality
        twist_grp = core_hrchy.create_group(name=f"{_prefix}{self.lowerarm_proxy.get_name()}{_suffix}_twistGrp")
        twist_offset_grp = core_hrchy.add_offset_transform(target_list=twist_grp)[0]
        twist_aim_grp = pole_point_cnstr = pole_aim_cnstr = None

        if self.auto_pole_vector:
            twist_aim_grp = core_hrchy.create_group(name=f"{_prefix}{self.lowerarm_proxy.get_name()}{_suffix}_aimGrp")
            upperarm_ref_grp = core_hrchy.create_group(
                name=f"{_prefix}{self.upperarm_proxy.get_name()}{_suffix}_refGrp"
            )
            core_hrchy.parent(source_objects=upperarm_ref_grp, target_parent=clavicle_ctrl)
            core_trans.match_transform(source=upperarm_fk_offset[0], target_list=upperarm_ref_grp, scale=False)
            pole_point_cnstr = cmds.pointConstraint(upperarm_ref_grp, hand_o_ik_data, twist_offset_grp, mo=False)[0]
            core_hrchy.parent(
                source_objects=[twist_aim_grp, twist_offset_grp],
                target_parent=global_offset_ctrl,
            )
            pole_aim_cnstr = cmds.aimConstraint(hand_o_ik_data, twist_offset_grp, wuo=twist_aim_grp, wut=2)[0]
            lowerarm_pv_parent = twist_aim_grp
        else:
            core_trans.match_transform(source=lowerarm_jnt, target_list=twist_offset_grp, scale=False)
            core_hrchy.parent(
                source_objects=[twist_offset_grp],
                target_parent=global_offset_ctrl,
            )
            lowerarm_pv_parent = twist_offset_grp
        if self.prefix == core_naming.NamingConstants.Prefix.RIGHT:
            rot_rev = cmds.createNode("multiplyDivide", n=f"{_prefix}{self.lowerarm_proxy.get_name()}_ik_rot_rev")
            cmds.setAttr(f"{rot_rev}.input2X", -1)
            cmds.connectAttr(f"{hand_ik_ctrl}.elbowTwist", f"{rot_rev}.input1X")
            cmds.connectAttr(f"{rot_rev}.outputX", f"{twist_grp}.rotateX")
        else:
            cmds.connectAttr(f"{hand_ik_ctrl}.elbowTwist", f"{twist_grp}.rotateX")
        core_hrchy.parent(source_objects=lowerarm_ik_offset, target_parent=twist_grp)

        # Follow Parent Setup
        if module_parent_jnt:
            for ctrls in [clavicle_ctrl, hand_ik_ctrl, upperarm_fk_ctrl, lowerarm_ik_ctrl]:
                core_attr.add_separator_attr(
                    target_object=ctrls, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
                )
            tools_rig_utils.create_follow_enum_setup(
                control=clavicle_ctrl,
                parent_list=[tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())],
                constraint_type="orient",
            )
            tools_rig_utils.create_follow_enum_setup(
                control=hand_ik_ctrl,
                parent_list=[
                    clavicle_jnt,
                    tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid()),
                    global_offset_ctrl,
                ],
                default_value=0,
            )
        else:
            for ctrls in [upperarm_fk_ctrl, hand_ik_ctrl, lowerarm_ik_ctrl]:
                core_attr.add_separator_attr(
                    target_object=ctrls, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
                )
            tools_rig_utils.create_follow_enum_setup(
                control=hand_ik_ctrl, parent_list=[clavicle_jnt, global_offset_ctrl], default_value=0
            )

        tools_rig_utils.create_follow_enum_setup(
            control=upperarm_fk_ctrl, parent_list=[clavicle_jnt], constraint_type="orient"
        )
        tools_rig_utils.create_follow_enum_setup(
            control=lowerarm_pv_parent,
            parent_list=[clavicle_jnt, hand_ik_ctrl, global_offset_ctrl],
            attribute_item=lowerarm_ik_ctrl,
            default_value=0,
        )

        # Lock And Hide Attrs
        core_attr.hide_lock_default_attrs(
            [clavicle_ctrl, upperarm_fk_ctrl, lowerarm_fk_ctrl, hand_fk_ctrl],
            translate=True,
            scale=True,
            visibility=True,
        )
        core_attr.hide_lock_default_attrs([lowerarm_ik_ctrl], rotate=True, scale=True, visibility=True)
        core_attr.hide_lock_default_attrs([hand_ik_ctrl], scale=True, visibility=True)
        core_attr.hide_lock_default_attrs([ik_switch_ctrl], translate=True, rotate=True, scale=True, visibility=True)

        cmds.setAttr(f"{general_automation_grp}.visibility", 0)
        cmds.setAttr(f"{joint_automation_grp}.visibility", 0)

        # IKFK Switch Locators

        for ik_joint in [upperarm_ik, lowerarm_ik, hand_ik]:
            ik_name = core_node.get_short_name(ik_joint).split("_JNT_ik")[0]
            switch_loc = cmds.spaceLocator(n=f"{ik_name}FkOffsetRef_loc")[0]
            cmds.parent(switch_loc, ik_joint)
            cmds.matchTransform(switch_loc, ik_joint)
            cmds.setAttr(f"{switch_loc}.visibility", 0)

        for fk_joint in [lowerarm_fk, hand_fk]:
            fk_name = core_node.get_short_name(fk_joint).split("_JNT_fk")[0]
            switch_loc = cmds.spaceLocator(n=f"{fk_name}Switch_loc")[0]
            cmds.parent(switch_loc, fk_joint)
            if fk_joint is lowerarm_fk:
                core_trans.match_translate(source=lowerarm_ik_ctrl, target_list=switch_loc)
            else:
                cmds.matchTransform(switch_loc, fk_joint)
                # core_trans.match_translate(source=fk_joint, target_list=switch_loc)
            cmds.setAttr(f"{switch_loc}.visibility", 0)

        if self.auto_pole_vector:
            # auto pole vector attribute to be able to disable it in animation
            auto_pole_attr = "autoPoleVector"
            auto_pole_attr_fullname = f"{lowerarm_ik_ctrl}.{auto_pole_attr}"
            cmds.addAttr(lowerarm_ik_ctrl, ln=auto_pole_attr, at="bool", k=True)
            cmds.setAttr(auto_pole_attr_fullname, 1)
            pole_parent_cnstr = cmds.parentConstraint(twist_aim_grp, lowerarm_ik_offset[0], mo=True)[0]
            parent_cnstr_aim_attr = cmds.listConnections(
                pole_parent_cnstr, plugs=True, d=False, s=True, scn=True, t="parentConstraint", et=True
            )[0]
            aim_cnstr_foot_attr = cmds.listConnections(
                pole_aim_cnstr, plugs=True, d=False, s=True, scn=True, t="aimConstraint", et=True
            )[0]
            point_cnstr_upperleg_attr, point_cnstr_foot_attr = cmds.listConnections(
                pole_point_cnstr, plugs=True, d=False, s=True, scn=True, t="pointConstraint", et=True
            )
            cmds.setDrivenKeyframe(parent_cnstr_aim_attr, cd=auto_pole_attr_fullname, dv=1, v=0)
            cmds.setDrivenKeyframe(aim_cnstr_foot_attr, cd=auto_pole_attr_fullname, dv=1, v=1)
            cmds.setDrivenKeyframe(point_cnstr_foot_attr, cd=auto_pole_attr_fullname, dv=1, v=1)
            cmds.setDrivenKeyframe(point_cnstr_upperleg_attr, cd=auto_pole_attr_fullname, dv=1, v=1)
            cmds.setDrivenKeyframe(parent_cnstr_aim_attr, cd=auto_pole_attr_fullname, dv=0, v=1)
            cmds.setDrivenKeyframe(aim_cnstr_foot_attr, cd=auto_pole_attr_fullname, dv=0, v=0)
            cmds.setDrivenKeyframe(point_cnstr_foot_attr, cd=auto_pole_attr_fullname, dv=0, v=0)
            cmds.setDrivenKeyframe(point_cnstr_upperleg_attr, cd=auto_pole_attr_fullname, dv=0, v=0)

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [clavicle_offset[0]]

    def get_proxies_mirrored(self, **kwargs):
        """
        Mirrors proxy transforms from the opposite side of the rig.

        Args:
            **kwargs: Optional keyword arguments passed to the base implementation.
        """
        super().get_proxies_mirrored(behaviour=True, specular=False)

    def align_proxies_to_joints(self):
        """
        Aligns the module's proxies to the corresponding joint positions.
        """
        clavicle_jnt = tools_rig_utils.find_joint_from_uuid(self.clavicle_proxy.get_uuid())
        upperarm_jnt = tools_rig_utils.find_joint_from_uuid(self.upperarm_proxy.get_uuid())
        lowerarm_jnt = tools_rig_utils.find_joint_from_uuid(self.lowerarm_proxy.get_uuid())
        hand_jnt = tools_rig_utils.find_joint_from_uuid(self.hand_proxy.get_uuid())

        clavicle_proxy = tools_rig_utils.find_proxy_from_uuid(self.clavicle_proxy.get_uuid())
        upperarm_guide_proxy = tools_rig_utils.find_proxy_from_uuid(self.upperarm_proxy.get_uuid())
        lowerarm_guide_proxy = tools_rig_utils.find_proxy_from_uuid(self.lowerarm_proxy.get_uuid())
        hand_proxy = tools_rig_utils.find_proxy_from_uuid(self.hand_proxy.get_uuid())

        for axis in ["x", "y", "z"]:
            cmds.setAttr(f"{clavicle_proxy}.r{axis}", 0)
            cmds.setAttr(f"{hand_proxy}.r{axis}", 0)
        cmds.delete(cmds.parentConstraint(clavicle_jnt, clavicle_proxy))
        core_trans.match_translate(source=upperarm_jnt, target_list=upperarm_guide_proxy)
        core_trans.match_translate(source=upperarm_jnt, target_list=upperarm_guide_proxy)
        cmds.delete(cmds.parentConstraint(hand_jnt, hand_proxy))
        core_trans.match_translate(source=lowerarm_jnt, target_list=lowerarm_guide_proxy)


class ModuleArmLeft(ModuleArm):
    def __init__(self, name="L Arm", prefix=core_naming.NamingConstants.Prefix.LEFT, suffix=None, clavicle_world=False):
        """
        Initializes a Left Arm module.

        Args:
            name (str): The name of the module. Default is "L Arm".
            prefix (str, optional): Optional prefix for the module.
            suffix (str, optional): Optional suffix for the module.
            clavicle_world (bool): Whether the clavicle control should orient to world space. Default is False.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix, clavicle_world=clavicle_world)

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)
        self.set_orientation_method(method="inherit")

        pos_clavicle = core_trans.Vector3(x=3, y=0)
        self.pos_shoulder = core_trans.Vector3(x=17.2, y=0)
        self.pos_elbow = core_trans.Vector3(x=37.7, y=0)
        pos_wrist = core_trans.Vector3(x=58.2, y=0)

        self.clavicle_proxy.set_initial_position(xyz=pos_clavicle)
        self.clavicle_proxy.set_offset_rotation(x=-90, y=0)
        self.clavicle_proxy.set_rotation(x=-90, y=0)
        self.upperarm_proxy.set_initial_position(xyz=self.pos_shoulder)
        self.lowerarm_proxy.set_initial_position(xyz=self.pos_elbow)
        self.hand_proxy.set_initial_position(xyz=pos_wrist)
        self.hand_proxy.set_offset_rotation(x=-90, y=0)
        self.hand_proxy.set_rotation(x=-90, y=0)


class ModuleArmRight(ModuleArm):
    def __init__(
        self, name="R Arm", prefix=core_naming.NamingConstants.Prefix.RIGHT, suffix=None, clavicle_world=False
    ):
        """
        Initializes a Right Arm module.

        Args:
            name (str): The name of the module. Default is "R Arm".
            prefix (str, optional): Optional prefix for the module.
            suffix (str, optional): Optional suffix for the module.
            clavicle_world (bool): Whether the clavicle control should orient to world space. Default is False.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix, clavicle_world=clavicle_world)

        _orientation = tools_rig_frm.OrientationData(aim_axis=(-1, 0, 0), up_axis=(0, 0, -1), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)
        self.set_orientation_method(method="inherit")

        self.clavicle_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_neg_x"))
        self.clavicle_proxy.set_offset_rotation(x=90, y=0)
        self.clavicle_proxy.set_rotation(x=90, y=0)
        self.hand_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_neg_x_neg_z"))
        self.hand_proxy.set_offset_rotation(x=90, y=0)
        self.hand_proxy.set_rotation(x=90, y=0)

        pos_clavicle = core_trans.Vector3(x=-3, y=0)
        self.pos_shoulder = core_trans.Vector3(x=-17.2, y=0)
        self.pos_elbow = core_trans.Vector3(x=-37.7, y=0)
        pos_wrist = core_trans.Vector3(x=-58.2, y=0)

        self.clavicle_proxy.set_initial_position(xyz=pos_clavicle)
        self.upperarm_proxy.set_initial_position(xyz=self.pos_shoulder)
        self.lowerarm_proxy.set_initial_position(xyz=self.pos_elbow)
        self.hand_proxy.set_initial_position(xyz=pos_wrist)

        self.dir_rot = 90
        self.dir_curve = "_joint_arrow_dir_neg_x"


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.core.session import remove_modules_startswith

    remove_modules_startswith("gt.tools.auto_rigger.module")
    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils

    # import gt.tools.auto_rigger.modules.module_biped_arm as tools_rig_mod_biped_arm
    import gt.tools.auto_rigger.modules.module_spine as tools_rig_mod_spine
    import gt.tools.auto_rigger.modules.module_root as tools_rig_mod_root
    import importlib

    importlib.reload(tools_rig_mod_root)
    # importlib.reload(tools_rig_mod_biped_arm)
    importlib.reload(tools_rig_mod_spine)
    importlib.reload(tools_rig_fmr)
    importlib.reload(tools_rig_utils)

    # -----------------------------------------------------------------------------------------------------
    # Arm Test Complete
    # male_average_project.set_preference_value_using_key(key="apply_control_rig_pose", value=False)
    a_root = tools_rig_mod_root.ModuleRoot()
    a_spine = tools_rig_mod_spine.ModuleSpine()
    a_arm_lf = ModuleArmLeft()
    a_arm = ModuleArm(prefix="C", auto_pole_vector=False)
    a_arm_rt = ModuleArmRight()

    root_uuid = a_root.root_proxy.get_uuid()
    spine_chest_uuid = a_spine.chest_proxy.get_uuid()
    a_spine.set_parent_uuid(root_uuid)
    a_arm_lf.set_parent_uuid(spine_chest_uuid)
    a_arm_rt.set_parent_uuid(spine_chest_uuid)

    a_project = tools_rig_frm.RigProject()
    a_project.add_to_modules(a_root)
    # a_project.add_to_modules(a_spine)
    a_project.add_to_modules(a_arm_rt)
    a_project.add_to_modules(a_arm_lf)
    a_project.add_to_modules(a_arm)
    a_project.set_preference_value_using_key(key="apply_control_rig_pose", value=False)
    # a_project.set_preference_value_using_key(key="delete_proxy_after_build", value=False)

    a_project.build_proxy()
    # cmds.setAttr("L_hand.tx", -11)
    # cmds.setAttr("L_hand.ty", -44)
    # cmds.setAttr("L_lowerArm.tz", -17)
    # cmds.setAttr("L_hand.tz", -30)
    # cmds.setAttr("L_hand.rz", -50)
    # cmds.setAttr("R_hand.tx", -11)
    # cmds.setAttr("R_hand.ty", 44)
    # cmds.setAttr("R_lowerArm.tz", -17)
    # cmds.setAttr("R_hand.tz", 30)
    # cmds.setAttr("R_hand.rz", -50)
    # cmds.setAttr("R_hand.rz", -50)

    # cmds.setAttr("L_clavicle.tx", 12)
    # cmds.setAttr("L_clavicle.tz", 56)
    # cmds.setAttr("L_clavicle.ry", 90)
    # cmds.setAttr("L_clavicle.tx", -10)
    # cmds.setAttr("L_clavicle.tx", 17)
    # cmds.setAttr("L_upperArm.ty", 7)
    # cmds.setAttr("L_upperArm.tx", -14)
    # cmds.setAttr("L_lowerArm.tz", -17)
    # cmds.setAttr("L_hand.tx", -6)

    # a_project.build_skeleton()
    a_project.build_rig()

    # --------------------------------------------------------------------------

    # Frame all
    cmds.viewFit(all=True)
    cmds.setAttr(f"skeleton.v", 1)
    cmds.setAttr(f"jointAutomation.v", 1)
