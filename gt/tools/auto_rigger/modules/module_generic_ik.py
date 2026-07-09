"""
Auto Rigger Generic IK Module
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


class ModuleGenericIK(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_generic_ik
    allow_parenting = True
    allow_multiple = True

    # Reference Attributes and Metadata Keys
    REF_ATTR_MID_PROXY_PV = "midProxyPoleVectorLookupAttr"

    def __init__(
        self,
        name="Generic IK",
        prefix=None,
        suffix=None,
        create_twist_joints=True,
        auto_pole_vector=False,
        ik_world=True,
    ):
        """
        Initialize a Generic IK module.

        Args:
            name (str): Name of the module instance.
            prefix (str | None): Optional prefix for naming conventions.
            suffix (str | None): Optional suffix for naming conventions.
            create_twist_joints (bool): Whether to generate twist joints along the IK chain. Default is True.
            auto_pole_vector (bool): If enabled, automatically calculate the pole vector position. Default is False.
            ik_world (bool): If True, allows IK controls to operate in world space. Default is True.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 0), up_dir=(0, -1, 0))
        self.set_orientation(orientation_data=_orientation)
        self.set_orientation_method(method="inherit")

        # Extra Module Data
        self.setup_name = "generic"
        self.rig_pose_mid_rot = -0.2  # float - offset value used to create the control rig pose
        self.create_twist_joints = create_twist_joints
        self.base_twist_joints = []
        self.mid_twist_joints = []
        self.auto_pole_vector = auto_pole_vector
        self.ik_world = ik_world
        self.base_dir_curve = None
        self.mid_dir_curve = None
        self.dir_curve = "_joint_arrow_dir_pos_x"
        self.dir_rot = -90

        base_name = "base"
        mid_name = "mid"
        end_name = "end"

        self.pos_base = core_trans.Vector3()
        self.pos_mid = core_trans.Vector3(z=18.85, y=0)
        pos_wrist = core_trans.Vector3(z=37.7, y=0)

        # Default Proxies
        self.base_proxy = tools_rig_frm.Proxy(name=f"{base_name}")
        self.base_proxy.set_initial_position(xyz=self.pos_base)
        self.base_proxy.set_locator_scale(scale=2)
        self.base_proxy.set_meta_purpose(value="base")
        self.base_proxy.set_offset_rotation(x=-90, y=-90)
        self.base_proxy.set_rotation(x=-90, y=-90)
        self.base_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.base_proxy.set_rotation_order("xzy")

        self.mid_proxy = tools_rig_frm.Proxy(name=f"{mid_name}")
        self.mid_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_arrow_neg_z"))
        self.mid_proxy.set_initial_position(xyz=self.pos_mid)
        self.mid_proxy.set_locator_scale(scale=2.2)
        self.mid_proxy.add_line_parent(line_parent=self.base_proxy)
        self.mid_proxy.set_meta_purpose(value="mid")
        self.mid_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )
        self.mid_proxy.set_rotation_order("xyz")

        self.end_proxy = tools_rig_frm.Proxy(name=end_name)
        self.end_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_x_pos_z_up"))
        self.end_proxy.set_initial_position(xyz=pos_wrist)
        self.end_proxy.set_locator_scale(scale=2)
        self.end_proxy.add_line_parent(line_parent=self.mid_proxy)
        self.end_proxy.set_meta_purpose(value="end")
        self.end_proxy.set_offset_rotation(x=-90, y=-90)
        self.end_proxy.set_rotation(x=-90, y=-90)
        self.end_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
                tools_rig_const.RiggerDriverTypes.SWITCH,
            ]
        )
        self.end_proxy.set_rotation_order("zyx")

        # Update Proxies
        self.proxies = [self.base_proxy, self.mid_proxy, self.end_proxy]

    def set_orientation_direction(self, is_positive, **kwargs):
        """
        Sets the direction of the orientation.
        If positive, it will use "1" in the desired axis.
        If negative, (not positive) it will use "-1" in the desired axis.
        Args:
            is_positive (bool): If True, it's set to a positive direction, if False to negative.
                                e.g. True = (1, 0, 0) while False (-1, 0, 0)
        """
        super().set_orientation_direction(
            is_positive=is_positive,
            set_aim_axis=True,
            set_up_axis=True,
            set_up_dir=False,
        )  # No Up Direction

    def set_proxies_name(self, name):
        """
        Set the base name used for the proxy setup.

        Args:
            name (str): The name to assign to the setup.
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

    def set_rig_pose_mid_rot(self, mid_rotation):
        """
        Sets the set_rig_pose_mid_rot class variable used to set the control rig pose for this module.

        Args:
            mid_rotation (int, float): numerical value to set
        """
        if isinstance(mid_rotation, (float, int)):
            self.rig_pose_mid_rot = float(mid_rotation)
        else:
            logger.warning("Given mid rotation is not an int or a float. Skipped.")

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
            self.base_proxy.set_parent_uuid(self.parent_uuid)
        self.mid_proxy.set_setup_driver_uuid(self.end_proxy.get_uuid())
        self.mid_proxy.set_parent_uuid(self.base_proxy.get_uuid())
        self.end_proxy.set_setup_driver_uuid(self.base_proxy.get_uuid())
        self.end_proxy.set_parent_uuid(self.base_proxy.get_uuid())

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
        base = tools_rig_utils.find_proxy_from_uuid(self.base_proxy.get_uuid())
        mid = tools_rig_utils.find_proxy_from_uuid(self.mid_proxy.get_uuid())
        end = tools_rig_utils.find_proxy_from_uuid(self.end_proxy.get_uuid())

        self.base_proxy.apply_offset_transform()
        self.mid_proxy.apply_offset_transform()
        self.end_proxy.apply_offset_transform()

        self.base_dir_curve = core_curve.get_curve(self.dir_curve)
        self.base_dir_curve.set_name(f"{_prefix}{self.base_proxy.get_name()}{_suffix}_dir")
        self.base_dir_curve = self.base_dir_curve.build()
        self.base_dir_curve = core_node.Node(self.base_dir_curve)
        core_curve.rescale_curve(self.base_dir_curve, 4)
        base_dir_offset = core_hrchy.add_offset_transform(self.base_dir_curve)[0]
        cmds.delete(cmds.parentConstraint(base, base_dir_offset))
        cmds.parent(base_dir_offset, base)
        cmds.setAttr(f"{base_dir_offset}.rx", self.dir_rot)

        self.mid_dir_curve = core_curve.get_curve(self.dir_curve)
        self.mid_dir_curve.set_name(f"{_prefix}{self.mid_proxy.get_name()}{_suffix}_dir")
        self.mid_dir_curve = self.mid_dir_curve.build()
        self.mid_dir_curve = core_node.Node(self.mid_dir_curve)
        core_curve.rescale_curve(self.mid_dir_curve, 4)
        mid_dir_offset = core_hrchy.add_offset_transform(self.mid_dir_curve)[0]
        cmds.delete(cmds.parentConstraint(mid, mid_dir_offset))
        cmds.parent(mid_dir_offset, mid)
        cmds.setAttr(f"{mid_dir_offset}.rx", self.dir_rot)

        # Base -----------------------------------------------------------------------------------
        core_attr.hide_lock_default_attrs(base, scale=True)

        # Mid  -------------------------------------------------------------------------------------
        core_attr.hide_lock_default_attrs(mid, scale=True)
        mid_tag = mid.get_short_name()

        # Direction Setup
        aim_vec = self.get_orientation_data().get_aim_axis()
        up_vec = self.get_orientation_data().get_up_axis()

        cmds.aimConstraint(
            mid,
            self.base_dir_curve,
            aimVector=aim_vec,
            upVector=up_vec,
            worldUpObject=mid,
            worldUpType="objectrotation",
        )

        core_attr.hide_lock_default_attrs(self.mid_dir_curve, scale=True, rotate=True, translate=True)
        core_attr.hide_lock_default_attrs(self.base_dir_curve, scale=True, rotate=True, translate=True)
        cmds.setAttr(f"{self.mid_dir_curve}.overrideEnabled", 1)
        cmds.setAttr(f"{self.mid_dir_curve}.overrideDisplayType", 2)
        cmds.setAttr(f"{self.base_dir_curve}.overrideEnabled", 1)
        cmds.setAttr(f"{self.base_dir_curve}.overrideDisplayType", 2)

        # Mid Setup
        mid_offset = tools_rig_utils.get_proxy_offset(mid)
        mid_pv_dir = cmds.spaceLocator(name=f"{mid_tag}_poleVectorDir")[0]
        core_attr.add_attr(
            obj_list=mid_pv_dir,
            attributes=ModuleGenericIK.REF_ATTR_MID_PROXY_PV,
            attr_type="string",
        )
        mid_pv_dir = core_node.Node(mid_pv_dir)
        core_trans.match_translate(source=mid, target_list=mid_pv_dir)
        cmds.move(0, 0, -10, mid_pv_dir, relative=True)  # Move it backwards (in front of the mid/elbow)
        core_hrchy.parent(mid_pv_dir, mid)

        mid_dir_loc = cmds.spaceLocator(name=f"{mid_tag}_dirParent_{core_naming.NamingConstants.Suffix.LOC}")[0]
        mid_aim_loc = cmds.spaceLocator(name=f"{mid_tag}_dirAim_{core_naming.NamingConstants.Suffix.LOC}")[0]
        mid_upvec_loc = cmds.spaceLocator(name=f"{mid_tag}_dirParentUp_{core_naming.NamingConstants.Suffix.LOC}")[0]
        mid_upvec_loc_grp = f"{mid_tag}_dirParentUp_{core_naming.NamingConstants.Suffix.GRP}"
        mid_upvec_loc_grp = core_hrchy.create_group(name=mid_upvec_loc_grp)

        mid_dir_loc = core_node.Node(mid_dir_loc)
        mid_aim_loc = core_node.Node(mid_aim_loc)
        mid_upvec_loc = core_node.Node(mid_upvec_loc)

        dir_aim_con = cmds.aimConstraint(
            end,
            mid_dir_offset,
            aimVector=aim_vec,
            upVector=up_vec,
            worldUpObject=mid,
            worldUpType="objectrotation",
        )[0]

        if round(cmds.getAttr(f"{mid_dir_offset}.rx"), 2) != self.dir_rot:
            cmds.setAttr(f"{dir_aim_con}.offsetX", self.dir_rot)

        # Hide Reference Elements
        core_hrchy.parent(mid_aim_loc, mid_dir_loc)
        core_hrchy.parent(mid_dir_loc, base)
        core_hrchy.parent(mid_upvec_loc_grp, global_proxy)
        core_hrchy.parent(mid_upvec_loc, mid_upvec_loc_grp)

        cmds.pointConstraint([end, base], mid_aim_loc.get_long_name())
        cmds.aimConstraint(end, mid_dir_loc.get_long_name())
        cmds.pointConstraint(base, mid_upvec_loc_grp.get_long_name(), skip=["x", "z"])

        mid_divide_node = core_node.create_node(node_type="multiplyDivide", name=f"{mid_tag}_divide")
        cmds.setAttr(f"{mid_divide_node}.operation", 2)  # Change operation to Divide
        cmds.setAttr(f"{mid_divide_node}.input2X", -2)
        cmds.connectAttr(f"{end}.ty", f"{mid_divide_node}.input1X")
        cmds.connectAttr(f"{mid_divide_node}.outputX", f"{mid_upvec_loc}.ty")

        cmds.pointConstraint(base, mid_dir_loc.get_long_name())
        cmds.pointConstraint([base, end], mid_aim_loc.get_long_name())

        cmds.connectAttr(f"{mid_dir_loc}.rotate", f"{mid_offset}.rotate")
        cmds.pointConstraint([end, base], mid_offset)

        cmds.aimConstraint(
            end,
            mid_dir_loc.get_long_name(),
            aimVector=aim_vec,
            upVector=aim_vec,
            worldUpType="object",
            worldUpObject=mid_upvec_loc.get_long_name(),
        )
        cmds.aimConstraint(
            mid_aim_loc.get_long_name(),
            mid.get_long_name(),
            aimVector=(0, 0, 1),
            upVector=(0, 1, 0),
            worldUpType="none",
            skip=["y", "z"],
        )

        cmds.setAttr(f"{mid}.tz", -0.01)

        # Mid Limits and Locks
        cmds.setAttr(f"{mid}.maxTransZLimit", -0.01)
        cmds.setAttr(f"{mid}.maxTransZLimitEnable", True)

        core_attr.set_attr_state(obj_list=str(mid), attr_list="rotate", locked=True)

        # Mid Hide Setup
        core_attr.set_attr(
            obj_list=[mid_pv_dir, mid_upvec_loc_grp, mid_dir_loc],
            attr_list="visibility",
            value=0,
        )  # Set Visibility to Off
        core_attr.set_attr(
            obj_list=[mid_pv_dir, mid_upvec_loc_grp, mid_dir_loc],
            attr_list="hiddenInOutliner",
            value=1,
        )  # Set Outline Hidden to On

        self.base_proxy.apply_transforms()
        self.end_proxy.apply_transforms()
        self.mid_proxy.apply_transforms()

        # Set proxy parent for the skeleton hierarchy
        self.mid_proxy.set_parent_uuid(self.base_proxy.get_uuid())
        self.end_proxy.set_parent_uuid(self.mid_proxy.get_uuid())

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
            if proxy == self.base_proxy:
                proxy_obj_path = self.base_dir_curve
            elif proxy == self.mid_proxy:
                proxy_obj_path = self.mid_dir_curve
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
            base_jnt = tools_rig_utils.find_joint_from_uuid(self.base_proxy.get_uuid()).get_short_name()
            mid_jnt = tools_rig_utils.find_joint_from_uuid(self.mid_proxy.get_uuid()).get_short_name()
            end_jnt = tools_rig_utils.find_joint_from_uuid(self.end_proxy.get_uuid()).get_short_name()
            self.base_twist_joints = tools_rig_utils.create_twist_joints(base_jnt, mid_jnt, copy_start=True)
            self.mid_twist_joints = tools_rig_utils.create_twist_joints(mid_jnt, end_jnt, copy_end=True)

    def build_rig(self, project_prefix=None, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            project_prefix (str, optional): If provided, the created elements receive this string as an extra prefix.
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """

        # Twist Setup
        if self.create_twist_joints:
            tools_rig_utils.create_twist_setup(
                twist_jnt_list=self.base_twist_joints, mid_joints=2, side=self.prefix, reverse=True
            )
            tools_rig_utils.create_twist_setup(twist_jnt_list=self.mid_twist_joints, mid_joints=2, side=self.prefix)
            all_twist_jnts = self.base_twist_joints + self.mid_twist_joints
            tools_rig_utils.extract_twist_rotation(twist_jnt_list=all_twist_jnts)

        # Get Elements
        global_ctrl = tools_rig_utils.find_ctrl_global()
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        base_jnt = tools_rig_utils.find_joint_from_uuid(self.base_proxy.get_uuid())
        mid_jnt = tools_rig_utils.find_joint_from_uuid(self.mid_proxy.get_uuid())
        end_jnt = tools_rig_utils.find_joint_from_uuid(self.end_proxy.get_uuid())
        module_jnt_list = [base_jnt, mid_jnt, end_jnt]

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
        system_scale = core_math.dist_center_to_center(base_jnt, mid_jnt)
        system_scale += core_math.dist_center_to_center(mid_jnt, end_jnt)

        # Create Parent Automation Elements
        joint_automation_grp = tools_rig_utils.find_or_create_joint_automation_group()
        general_automation_grp = tools_rig_utils.get_automation_group()
        module_parent_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())
        core_hrchy.parent(source_objects=module_parent_jnt, target_parent=joint_automation_grp)

        # Create Automation Skeletons (FK/IK)
        base_parent = module_parent_jnt
        if module_parent_jnt:
            core_color.set_color_viewport(
                obj_list=base_parent,
                rgb_color=core_color.ColorConstants.RigJoint.AUTOMATION,
            )
            core_rigging.rescale_joint_radius(
                joint_list=base_parent,
                multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_DRIVEN,
            )
        else:
            base_parent = joint_automation_grp

        base_fk = core_rigging.duplicate_joint_for_automation(base_jnt, suffix="fk", parent=base_parent)
        mid_fk = core_rigging.duplicate_joint_for_automation(mid_jnt, suffix="fk", parent=base_fk)
        end_fk = core_rigging.duplicate_joint_for_automation(end_jnt, suffix="fk", parent=mid_fk)
        fk_joints = [base_fk, mid_fk, end_fk]

        base_ik = core_rigging.duplicate_joint_for_automation(base_jnt, suffix="ik", parent=base_parent)
        mid_ik = core_rigging.duplicate_joint_for_automation(mid_jnt, suffix="ik", parent=base_ik)
        end_ik = core_rigging.duplicate_joint_for_automation(end_jnt, suffix="ik", parent=mid_ik)
        ik_joints = [base_ik, mid_ik, end_ik]

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
        # Base FK Control
        base_fk_ctrl, base_fk_offset = self.create_rig_control(
            control_base_name=self.base_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=global_offset_ctrl,
            match_obj=base_jnt,
            add_offset_ctrl=False,
            rot_order=3,
            shape_scale=system_scale * 0.16,
            color=core_color.get_directional_color(object_name=base_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=base_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.base_proxy,
        )

        core_cnstr.constraint_targets(source_driver=base_fk_ctrl, target_driven=base_fk)
        fk_offsets_ctrls.append(base_fk_offset[0])

        # Mid FK Control
        mid_fk_ctrl, mid_fk_offset = self.create_rig_control(
            control_base_name=self.mid_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=base_fk_ctrl,
            match_obj=mid_jnt,
            add_offset_ctrl=False,
            rot_order=0,
            shape_scale=system_scale * 0.14,
            color=core_color.get_directional_color(object_name=mid_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=mid_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.mid_proxy,
        )
        core_cnstr.constraint_targets(source_driver=mid_fk_ctrl, target_driven=mid_fk)
        fk_offsets_ctrls.append(mid_fk_offset[0])

        # End FK Control
        end_fk_ctrl, end_fk_offset = self.create_rig_control(
            control_base_name=self.end_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=mid_fk_ctrl,
            match_obj=end_jnt,
            add_offset_ctrl=False,
            rot_order=5,
            shape_scale=system_scale * 0.1,
            color=core_color.get_directional_color(object_name=end_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=end_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.end_proxy,
        )
        core_cnstr.constraint_targets(source_driver=end_fk_ctrl, target_driven=end_fk)
        fk_offsets_ctrls.append(end_fk_offset[0])

        # IK Controls -------------------------------------------------------------------------------------
        ik_offsets_ctrls = []

        # IK Mid Control
        ik_suffix = core_naming.NamingConstants.Description.IK.upper()
        mid_ik_ctrl, mid_ik_offset = self.create_rig_control(
            control_base_name=f"{self.mid_proxy.get_name()}_{ik_suffix}",
            curve_file_name="primitive_diamond",
            parent_obj=global_offset_ctrl,
            match_obj_pos=end_jnt,
            add_offset_ctrl=False,
            shape_scale=system_scale * 0.05,
            color=core_color.get_directional_color(object_name=mid_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=mid_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.mid_proxy,
        )
        ik_offsets_ctrls.append(mid_ik_offset[0])

        # Find Pole Vector Position
        mid_guide_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.mid_proxy.get_uuid())
        mid_guide_proxy_children = (
            cmds.listRelatives(mid_guide_proxy, children=True, typ="transform", fullPath=True) or []
        )
        mid_pv_dir = tools_rig_utils.find_object_with_attr(
            attr_name=ModuleGenericIK.REF_ATTR_MID_PROXY_PV,
            lookup_list=mid_guide_proxy_children,
        )

        temp_transform = core_hrchy.create_group(name=f"{mid_ik_ctrl}_rotExtraction")
        cmds.delete(cmds.pointConstraint(mid_jnt, temp_transform))
        cmds.delete(
            cmds.aimConstraint(
                mid_pv_dir,
                temp_transform,
                offset=(0, 0, 0),
                aimVector=(1, 0, 0),
                upVector=(0, -1, 0),
                worldUpType="vector",
                worldUpVector=(0, 1, 0),
            )
        )
        cmds.move(system_scale * 0.6, 0, 0, temp_transform, objectSpace=True, relative=True)
        cmds.delete(cmds.pointConstraint(temp_transform, mid_ik_offset))
        cmds.delete(temp_transform)

        # IK Aim Line
        tools_rig_utils.create_control_visualization_line(mid_ik_ctrl, mid_ik)

        # IK End Control
        if self.prefix in [core_naming.NamingConstants.Prefix.RIGHT, core_naming.NamingConstants.Prefix.LEFT]:
            shape_offset = (0, 0, 90)
        else:
            shape_offset = (-90, 0, 90)

        if self.ik_world:
            match_rot = None
            match_rot_order = 1
            match_shape_pos_offset = (0, 0, system_scale * -0.3)
        else:
            match_rot = end_jnt
            match_rot_order = 5
            match_shape_pos_offset = (system_scale * -0.3, 0, 0)

        end_ik_ctrl, end_ik_offset, end_o_ik_ctrl, end_o_ik_data = self.create_rig_control(
            control_base_name=f"{self.end_proxy.get_name()}_{ik_suffix}",
            curve_file_name="square",
            parent_obj=global_offset_ctrl,
            rot_order=match_rot_order,
            match_obj_pos=end_jnt,
            match_obj_rot=match_rot,
            add_offset_ctrl=True,
            shape_rot_offset=shape_offset,
            shape_scale=system_scale * 0.25,
            color=core_color.get_directional_color(object_name=end_jnt),
        )
        self._add_driver_uuid_attr(
            target_driver=end_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.end_proxy,
        )
        self._add_driver_uuid_attr(
            target_driver=end_o_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=f"{self.end_proxy.get_name()}Offset",
        )
        ik_offsets_ctrls.append(end_ik_offset[0])

        # Transform under ctrl for constraint (avoid orient constraint issue)

        orient_grp = core_hrchy.create_group(name=f"{self.end_proxy.get_name()}_{ik_suffix}_orient_grp")
        cmds.delete(cmds.parentConstraint(end_ik, orient_grp))
        cmds.parent(orient_grp, end_o_ik_ctrl)
        core_attr.hide_lock_default_attrs(
            obj_list=[orient_grp], rotate=True, translate=True, scale=True, visibility=True
        )

        # Attributes
        core_attr.hide_lock_default_attrs(obj_list=[end_ik_ctrl, end_o_ik_ctrl], scale=True, visibility=True)

        # Switch Control
        ik_switch_ctrl, ik_switch_offset = self.create_rig_control(
            control_base_name=self.setup_name,
            curve_file_name="gear_eight_sides_smooth",
            parent_obj=global_offset_ctrl,
            rot_order=match_rot_order,
            match_obj_pos=end_jnt,
            match_obj_rot=match_rot,
            add_offset_ctrl=False,
            shape_rot_offset=shape_offset,
            shape_pos_offset=match_shape_pos_offset,
            shape_scale=system_scale * 0.012,
            color=core_color.get_directional_color(object_name=end_jnt),
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
            source_driver=[end_fk_ctrl, end_ik_ctrl], target_driven=ik_switch_offset[0]
        )[0]
        system_rev = cmds.createNode("reverse", name=f"{_prefix}{self.setup_name}_rev{_suffix}")
        cmds.connectAttr(f"{ik_switch_ctrl}.influenceSwitch", f"{system_rev}.inputX")
        cmds.connectAttr(f"{system_rev}.outputX", f"{switch_cons}.w0")
        cmds.connectAttr(f"{ik_switch_ctrl}.influenceSwitch", f"{switch_cons}.w1")

        influence_switch_attr_nice_name = "FK/IK"
        cmds.addAttr(f"{ik_switch_ctrl}.influenceSwitch", e=True, nn=influence_switch_attr_nice_name)
        cmds.setAttr(f"{ik_switch_ctrl}.influenceSwitch", 1)  # Default is IK

        # Automation
        end_automation_grp = core_hrchy.create_group(
            name=f"{_prefix}{self.end_proxy.get_name()}{_suffix}_automation_grp"
        )
        core_hrchy.parent(source_objects=end_automation_grp, target_parent=general_automation_grp)

        cmds.addAttr(end_ik_ctrl, ln="midTwist", nn="Mid Twist", at="float", keyable=True)

        # End IK handle
        end_ik_handle = cmds.ikHandle(
            sj=base_ik,
            ee=end_ik,
            n=f"{_prefix}{self.end_proxy.get_name()}{_suffix}_ikHandle",
            sol="ikRPsolver",
        )[0]
        end_ik_handle = core_node.Node(end_ik_handle)
        core_hrchy.parent(source_objects=end_ik_handle, target_parent=end_automation_grp)
        cmds.poleVectorConstraint(mid_ik_ctrl, end_ik_handle)
        cmds.pointConstraint(end_o_ik_ctrl, end_ik_handle, mo=True)
        cmds.orientConstraint(orient_grp, end_ik, mo=True)

        # Mid Ctrl Twist Rotation Functionality
        twist_grp = core_hrchy.create_group(name=f"{_prefix}{self.mid_proxy.get_name()}{_suffix}_twistGrp")
        twist_offset_grp = core_hrchy.add_offset_transform(target_list=twist_grp)[0]
        twist_aim_grp = pole_point_cnstr = pole_aim_cnstr = None

        if self.auto_pole_vector:
            twist_aim_grp = core_hrchy.create_group(name=f"{_prefix}{self.mid_proxy.get_name()}{_suffix}_aimGrp")
            base_ref_grp = core_hrchy.create_group(name=f"{_prefix}{self.base_proxy.get_name()}{_suffix}_refGrp")
            core_hrchy.parent(source_objects=base_ref_grp, target_parent=global_offset_ctrl)
            core_trans.match_transform(source=base_fk_offset[0], target_list=base_ref_grp)
            pole_point_cnstr = cmds.pointConstraint(base_ref_grp, end_o_ik_data, twist_offset_grp, mo=False)[0]
            core_hrchy.parent(
                source_objects=[twist_aim_grp, twist_offset_grp],
                target_parent=global_offset_ctrl,
            )
            pole_aim_cnstr = cmds.aimConstraint(end_o_ik_data, twist_offset_grp, wuo=twist_aim_grp, wut=2)[0]
            mid_pv_parent = twist_aim_grp
        else:
            core_trans.match_transform(source=mid_jnt, target_list=twist_offset_grp)
            core_hrchy.parent(
                source_objects=[twist_offset_grp],
                target_parent=global_offset_ctrl,
            )
            mid_pv_parent = twist_offset_grp
        if self.prefix == core_naming.NamingConstants.Prefix.RIGHT:
            rot_rev = cmds.createNode("multiplyDivide", n=f"{_prefix}{self.mid_proxy.get_name()}_ik_rot_rev")
            cmds.setAttr(f"{rot_rev}.input2X", -1)
            cmds.connectAttr(f"{end_ik_ctrl}.midTwist", f"{rot_rev}.input1X")
            cmds.connectAttr(f"{rot_rev}.outputX", f"{twist_grp}.rotateX")
        else:
            cmds.connectAttr(f"{end_ik_ctrl}.midTwist", f"{twist_grp}.rotateX")
        core_hrchy.parent(source_objects=mid_ik_offset, target_parent=twist_grp)

        # Follow Parent Setup
        if module_parent_jnt:
            for ctrls in [base_fk_ctrl, end_ik_ctrl, mid_ik_ctrl]:
                core_attr.add_separator_attr(
                    target_object=ctrls, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
                )
            tools_rig_utils.create_follow_enum_setup(
                control=base_fk_ctrl,
                parent_list=[tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())],
                constraint_type="orient",
            )
            tools_rig_utils.create_follow_enum_setup(
                control=end_ik_ctrl,
                parent_list=[
                    tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid()),
                    global_offset_ctrl,
                ],
                default_value=0,
            )
        else:
            for ctrls in [end_ik_ctrl, mid_ik_ctrl]:
                core_attr.add_separator_attr(
                    target_object=ctrls, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
                )
            tools_rig_utils.create_follow_enum_setup(
                control=end_ik_ctrl, parent_list=[global_offset_ctrl], default_value=0
            )

        tools_rig_utils.create_follow_enum_setup(
            control=mid_pv_parent,
            parent_list=[end_ik_ctrl, global_offset_ctrl],
            attribute_item=mid_ik_ctrl,
            default_value=0,
        )

        # Lock And Hide Attrs
        core_attr.hide_lock_default_attrs(
            [base_fk_ctrl, mid_fk_ctrl, end_fk_ctrl],
            translate=True,
            scale=True,
            visibility=True,
        )
        core_attr.hide_lock_default_attrs([mid_ik_ctrl], rotate=True, scale=True, visibility=True)
        core_attr.hide_lock_default_attrs([end_ik_ctrl], scale=True, visibility=True)
        core_attr.hide_lock_default_attrs([ik_switch_ctrl], translate=True, rotate=True, scale=True, visibility=True)

        cmds.setAttr(f"{general_automation_grp}.visibility", 0)
        cmds.setAttr(f"{joint_automation_grp}.visibility", 0)

        # IKFK Switch Locators

        for ik_joint in [base_ik, mid_ik, end_ik]:
            ik_name = core_node.get_short_name(ik_joint).split("_JNT_ik")[0]
            switch_loc = cmds.spaceLocator(n=f"{ik_name}FkOffsetRef_loc")[0]
            cmds.parent(switch_loc, ik_joint)
            cmds.matchTransform(switch_loc, ik_joint)
            cmds.setAttr(f"{switch_loc}.visibility", 0)

        for fk_joint in [mid_fk, end_fk]:
            fk_name = core_node.get_short_name(fk_joint).split("_JNT_fk")[0]
            switch_loc = cmds.spaceLocator(n=f"{fk_name}Switch_loc")[0]
            cmds.parent(switch_loc, fk_joint)
            if fk_joint is mid_fk:
                core_trans.match_translate(source=mid_ik_ctrl, target_list=switch_loc)
            else:
                cmds.matchTransform(switch_loc, fk_joint)
                # core_trans.match_translate(source=fk_joint, target_list=switch_loc)
            cmds.setAttr(f"{switch_loc}.visibility", 0)

        if self.auto_pole_vector:
            # auto pole vector attribute to be able to disable it in animation
            auto_pole_attr = "autoPoleVector"
            auto_pole_attr_fullname = f"{mid_ik_ctrl}.{auto_pole_attr}"
            cmds.addAttr(mid_ik_ctrl, ln=auto_pole_attr, at="bool", k=True)
            cmds.setAttr(auto_pole_attr_fullname, 1)
            pole_parent_cnstr = cmds.parentConstraint(twist_aim_grp, mid_ik_offset[0], mo=True)[0]
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
        self.module_children_drivers = [base_fk_offset[0]]

    def get_proxies_mirrored(self, **kwargs):
        """
        Mirrors proxy transforms from the opposite side of the rig.

        Args:
            **kwargs: Optional keyword arguments passed to the base implementation.
        """
        super().get_proxies_mirrored()
        end_proxy = tools_rig_utils.find_proxy_from_uuid(self.end_proxy.get_uuid())
        cmds.rotate(-180, 0, 0, end_proxy, r=True, os=True)

    def align_proxies_to_joints(self):
        """
        Aligns the proxies to the joints transformations.
        """
        base_jnt = tools_rig_utils.find_joint_from_uuid(self.base_proxy.get_uuid())
        mid_jnt = tools_rig_utils.find_joint_from_uuid(self.mid_proxy.get_uuid())
        end_jnt = tools_rig_utils.find_joint_from_uuid(self.end_proxy.get_uuid())

        base_guide_proxy = tools_rig_utils.find_proxy_from_uuid(self.base_proxy.get_uuid())
        mid_guide_proxy = tools_rig_utils.find_proxy_from_uuid(self.mid_proxy.get_uuid())
        end_proxy = tools_rig_utils.find_proxy_from_uuid(self.end_proxy.get_uuid())

        for axis in ["x", "y", "z"]:
            cmds.setAttr(f"{end_proxy}.r{axis}", 0)
        core_trans.match_translate(source=base_jnt, target_list=base_guide_proxy)
        core_trans.match_translate(source=base_jnt, target_list=base_guide_proxy)
        cmds.delete(cmds.parentConstraint(end_jnt, end_proxy))
        core_trans.match_translate(source=mid_jnt, target_list=mid_guide_proxy)


class ModuleGenericIKLeft(ModuleGenericIK):
    def __init__(self, name="L Generic IK", prefix=core_naming.NamingConstants.Prefix.LEFT, suffix=None):
        """
        Initialize a left generic IK module.

        Args:
            name (str): Name of the module instance.
            prefix (str | None): Optional prefix for naming conventions.
            suffix (str | None): Optional suffix for naming conventions.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)
        self.set_orientation_method(method="inherit")

        self.base_proxy.set_offset_rotation(x=0, y=0)
        self.base_proxy.set_rotation(x=0, y=0)
        self.pos_base = core_trans.Vector3(x=17.2, y=0)
        self.pos_mid = core_trans.Vector3(x=37.7, y=0)
        pos_wrist = core_trans.Vector3(x=58.2, y=0)

        self.base_proxy.set_initial_position(xyz=self.pos_base)
        self.mid_proxy.set_initial_position(xyz=self.pos_mid)
        self.end_proxy.set_initial_position(xyz=pos_wrist)
        self.end_proxy.set_offset_rotation(x=-90, y=0)
        self.end_proxy.set_rotation(x=-90, y=0)


class ModuleGenericIKRight(ModuleGenericIK):
    def __init__(self, name="R Generic IK", prefix=core_naming.NamingConstants.Prefix.RIGHT, suffix=None):
        """
        Initialize a right generic IK module.

        Args:
            name (str): Name of the module instance.
            prefix (str | None): Optional prefix for naming conventions.
            suffix (str | None): Optional suffix for naming conventions.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = tools_rig_frm.OrientationData(aim_axis=(-1, 0, 0), up_axis=(0, 0, -1), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)
        self.set_orientation_method(method="inherit")

        self.base_proxy.set_offset_rotation(x=0, y=0)
        self.base_proxy.set_rotation(x=0, y=0)
        self.end_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_neg_x_neg_z"))
        self.end_proxy.set_offset_rotation(x=90, y=0)
        self.end_proxy.set_rotation(x=90, y=0)

        self.pos_base = core_trans.Vector3(x=-17.2, y=0)
        self.pos_mid = core_trans.Vector3(x=-37.7, y=0)
        pos_wrist = core_trans.Vector3(x=-58.2, y=0)

        self.base_proxy.set_initial_position(xyz=self.pos_base)
        self.mid_proxy.set_initial_position(xyz=self.pos_mid)
        self.end_proxy.set_initial_position(xyz=pos_wrist)

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

    import gt.tools.auto_rigger.modules.module_spine as tools_rig_mod_spine
    import gt.tools.auto_rigger.modules.module_root as tools_rig_mod_root
    import importlib

    importlib.reload(tools_rig_mod_root)
    importlib.reload(tools_rig_mod_spine)
    importlib.reload(tools_rig_fmr)
    importlib.reload(tools_rig_utils)

    # -----------------------------------------------------------------------------------------------------
    # Generic IK Test Complete
    a_root = tools_rig_mod_root.ModuleRoot()
    a_spine = tools_rig_mod_spine.ModuleSpine()
    a_generic_ik_lf = ModuleGenericIKLeft()
    a_generic_ik = ModuleGenericIK(prefix="C", auto_pole_vector=False)
    a_generic_ik_rt = ModuleGenericIKRight()

    root_uuid = a_root.root_proxy.get_uuid()
    # spine_chest_uuid = a_spine.chest_proxy.get_uuid()
    # a_spine.set_parent_uuid(root_uuid)
    a_generic_ik_lf.set_parent_uuid(root_uuid)
    a_generic_ik_rt.set_parent_uuid(root_uuid)

    a_project = tools_rig_frm.RigProject()
    a_project.add_to_modules(a_root)
    # a_project.add_to_modules(a_spine)
    a_project.add_to_modules(a_generic_ik_rt)
    a_project.add_to_modules(a_generic_ik_lf)
    a_project.add_to_modules(a_generic_ik)
    a_project.set_preference_value_using_key(key="apply_control_rig_pose", value=False)
    # a_project.set_preference_value_using_key(key="delete_proxy_after_build", value=False)

    a_project.build_proxy()
    # cmds.setAttr("L_end.tx", -11)
    # cmds.setAttr("L_end.ty", -44)
    # cmds.setAttr("L_mid.tz", -17)
    # cmds.setAttr("L_end.tz", -30)
    # cmds.setAttr("L_end.rz", -50)
    # cmds.setAttr("R_end.tx", -11)
    # cmds.setAttr("R_end.ty", 44)
    # cmds.setAttr("R_mid.tz", -17)
    # cmds.setAttr("R_end.tz", 30)
    # cmds.setAttr("R_end.rz", -50)
    # cmds.setAttr("R_end.rz", -50)

    # cmds.setAttr("L_base.ty", 7)
    # cmds.setAttr("L_base.tx", -14)
    # cmds.setAttr("L_mid.tz", -17)
    # cmds.setAttr("L_end.tx", -6)

    # a_project.build_skeleton()
    a_project.build_rig()

    # --------------------------------------------------------------------------

    # Frame all
    cmds.viewFit(all=True)
    cmds.setAttr(f"skeleton.v", 1)
    cmds.setAttr(f"jointAutomation.v", 1)
