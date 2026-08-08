"""
Auto Rigger Spine Modules

Potential new features/changes:
1. Add an influence system that allows the user to rotate the "C_spine_IK_CTRL" and influence the in-between
controls as if they were an FK chain (essentially using the pivot of their parents)
Similarly to how the reference rig is capable of driving spine01 and spine02 when we rotate the spine IK control.
2. Change the order of the separator attributes found on many controls so the "controlOptions" come before
the exposed rotation order.
3. Add parenting system to spine FK and IK controls, so they follow or not the rotation of the parent.
"""

import gt.core.attr as core_attr
import gt.core.math as core_math
import gt.core.node as core_node
import gt.core.color as core_color
import gt.core.curve as core_curve
import gt.core.joint as core_joint
import gt.core.naming as core_naming
import gt.core.rigging as core_rigging
import gt.core.surface as core_surface
import gt.core.outliner as core_outlnr
import gt.core.transform as core_trans
import gt.core.hierarchy as core_hrchy
import gt.core.constraint as core_cnstr
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.ui.resource_library as ui_res_lib
import maya.cmds as cmds
import logging
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleSpine(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_spine
    allow_parenting = True

    def __init__(self, name="Spine", prefix=core_naming.NamingConstants.Prefix.CENTER, suffix=None, world_ctrls=False):
        """
        Initializes the Spine module.

        Args:
            name (str, optional): Name of the module. Defaults to "Spine".
            prefix (str, optional): Naming prefix, typically indicating module side
                (e.g., center, left, right). Defaults to NamingConstants.Prefix.CENTER.
            suffix (str, optional): Optional suffix for the module name. Defaults to None.
            world_ctrls (bool, optional): Whether to include world controls in the rig.
                Defaults to False.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        # Set Extra Module Attrs
        self.setup_name = "spine"
        self.cog_name = "cog"
        self.hips_name = "hips"
        self.dropoff_rate = 1.0
        self.spine_number = 2
        self.cog_parent = None  # If None, it uses the module parent.
        self._attr_rot_order_cog = "rotationOrderCOG"  # Used to determine the rotation order of the control COG
        self.world_ctrls = world_ctrls

        # Orientation
        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)
        self.set_orientation_method(method="automatic")
        if self.world_ctrls:
            self.orientation.set_world_aligned(world_aligned=True)

        # Hip (Base)
        self.hip_proxy = tools_rig_frm.Proxy(name=self.hips_name)
        pos_hip = core_trans.Vector3(y=84.5)
        self.hip_proxy.set_initial_position(xyz=pos_hip)
        self.hip_proxy.set_locator_scale(scale=1.5)
        self.hip_proxy.set_meta_purpose(value=self.hips_name)
        self.hip_proxy.set_rotation_order(rotation_order=1)
        self.hip_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,  # Hip Data Offset
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.PIVOT,
                tools_rig_const.RiggerDriverTypes.COG,
            ]
        )  # COG is the IK/FK Switch

        # Chest (End)
        self.chest_proxy = tools_rig_frm.Proxy()  # the correct name and meta purpose will be set with set_spine_number
        pos_chest = core_trans.Vector3(y=114.5)
        self.chest_proxy.set_initial_position(xyz=pos_chest)
        self.chest_proxy.set_locator_scale(scale=1.5)
        self.chest_proxy.set_rotation_order(rotation_order=1)
        self.chest_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,  # Manually created Generic Driver
                tools_rig_const.RiggerDriverTypes.IK,
                tools_rig_const.RiggerDriverTypes.PIVOT,
                tools_rig_const.RiggerDriverTypes.FK,
            ]
        )

        # Spines (In-between)
        self.spine_proxies = []
        self.set_spine_number(self.spine_number)

    def set_spine_number(self, spine_num):
        """
        Set a new number of spine proxies. These are the proxies in-between the hip proxy (base) and chest proxy (end)
        Args:
            spine_num (int): New number of spines to exist in-between hip and chest.
                             Minimum is zero (0) - No negative numbers.
        """
        spines_len = len(self.spine_proxies)
        # Same as current, skip
        if spines_len == spine_num:
            return

        # set the right chest name
        chest_name = f"spine{str(spine_num + 1).zfill(2)}"
        self.chest_proxy.set_name(name=chest_name)
        self.chest_proxy.set_meta_purpose(value=chest_name)

        # New number higher than current - Add more proxies (spines)
        if spines_len < spine_num:
            # Determine Initial Parent (Last spine, or hip)
            if self.spine_proxies:
                _parent_uuid = self.spine_proxies[-1].get_uuid()
            else:
                _parent_uuid = self.hip_proxy.get_uuid()
            # Create new spines
            for num in range(spines_len, spine_num):
                new_spine_name = f"{self.setup_name + str(num + 1).zfill(2)}"
                new_spine = tools_rig_frm.Proxy(name=new_spine_name)
                new_spine.set_locator_scale(scale=1)
                new_spine.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
                new_spine.set_meta_purpose(value=new_spine_name)
                new_spine.add_line_parent(line_parent=_parent_uuid)
                new_spine.set_parent_uuid(uuid=_parent_uuid)
                new_spine.add_driver_type(
                    driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
                )
                new_spine.set_rotation_order(rotation_order=1)
                _parent_uuid = new_spine.get_uuid()
                self.spine_proxies.append(new_spine)
        # New number lower than current - Remove unnecessary proxies
        elif len(self.spine_proxies) > spine_num:
            self.spine_proxies = self.spine_proxies[:spine_num]  # Truncate the list

        if self.spine_proxies:
            self.chest_proxy.add_line_parent(line_parent=self.spine_proxies[-1].get_uuid())
        else:
            self.chest_proxy.add_line_parent(line_parent=self.hip_proxy.get_uuid())

        self.spine_number = spine_num
        self.refresh_proxies_list()

    def refresh_proxies_list(self):
        """
        Refreshes the main proxies list used by the module during build (update in case objects were updated)
        """
        self.proxies = [self.hip_proxy]
        self.proxies.extend(self.spine_proxies)
        self.proxies.append(self.chest_proxy)

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
        # Determine Number of Spine Proxies
        _spine_num = 0
        spine_pattern = r"spine\d+"
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(tools_rig_const.RiggerConstants.META_PROXY_PURPOSE)
                if bool(re.match(spine_pattern, meta_type)):
                    _spine_num += 1

        # the chest (last joint of the spine) is called with the same pattern (spine + num)
        # spine num indicates the number of middle joints
        _spine_num = _spine_num - 1
        self.set_spine_number(_spine_num)

        self.read_purpose_matching_proxy_from_dict(proxy_dict)
        self.refresh_proxies_list()

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
            list: A list of tools_rig_frm.ProxyData objects. These objects describe the created proxy elements.
        """
        # Set the proxy parent_uuid and driver_uuid for the proxy construction hierarchy
        # (parent_uuid for the skeleton hierarchy, driver_uuid to adjust proxies transformations)
        if self.parent_uuid:
            if self.hip_proxy:
                self.hip_proxy.set_parent_uuid(self.parent_uuid)
        self.chest_proxy.set_setup_driver_uuid(self.hip_proxy.get_uuid())
        self.chest_proxy.set_parent_uuid(self.hip_proxy.get_uuid())
        prx_driver = self.chest_proxy
        for prx in self.spine_proxies:
            prx.set_setup_driver_uuid(prx_driver.get_uuid())
            prx.set_parent_uuid(prx_driver.get_uuid())
            prx_driver = prx

        proxy = super().build_proxy(**kwargs)  # Passthrough

        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """

        # Get Maya Elements
        hip = tools_rig_utils.find_proxy_from_uuid(self.hip_proxy.get_uuid())
        chest = tools_rig_utils.find_proxy_from_uuid(self.chest_proxy.get_uuid())

        # Add COG initial ROT order
        cog_rot_order_attr = (
                core_attr.add_attr(
                    obj_list=hip,
                    attributes=self._attr_rot_order_cog,
                    attr_type="enum",
                    enum="xyz:yzx:zxy:xzy:yxz:zyx",
                    default=0,
                )
                or []
        )
        cmds.setAttr(cog_rot_order_attr[0], 2)  # zxy

        # Add IK initial ROT order
        ik_rot_order_attr = (
                core_attr.add_attr(
                    obj_list=chest,
                    attributes=tools_rig_const.RiggerConstants.ATTR_ROT_ORDER_IK,
                    attr_type="enum",
                    enum="xyz:yzx:zxy:xzy:yxz:zyx",
                    default=0,
                )
                or []
        )
        cmds.setAttr(ik_rot_order_attr[0], 2)  # zxy

        spines = []
        for spine in self.spine_proxies:
            spine_node = tools_rig_utils.find_proxy_from_uuid(spine.get_uuid())
            spines.append(spine_node)
        self.hip_proxy.apply_offset_transform()
        self.chest_proxy.apply_offset_transform()

        spine_offsets = []
        for spine in spines:
            offset = tools_rig_utils.get_proxy_offset(spine)
            spine_offsets.append(offset)
        core_cnstr.equidistant_constraints(start=hip, end=chest, target_list=spine_offsets)

        # Apply transform after set the order with build_proxy_setup parent function
        super().build_proxy_setup()  # Passthrough

        # Set proxy parent for the skeleton hierarchy
        prx_parent = self.hip_proxy
        for prx in self.spine_proxies:
            prx.set_parent_uuid(prx_parent.get_uuid())
            prx_parent = prx
        self.chest_proxy.set_parent_uuid(self.spine_proxies[-1].get_uuid())

    def build_skeleton_joints(self):
        """
        Runs skeleton joints phase, which creates joints out of the proxy elements.
        This  happens after "build_proxy_setup" and as these are used to create the joints.
        """
        super().build_skeleton_joints()  # Passthrough

    def build_skeleton_hierarchy(self):
        """
        Runs skeletal hierarchy phase (post skeleton). Joints are parented and oriented during this step.
        Happens after the "build_skeleton_joints" function in a project.
        """
        super().build_skeleton_hierarchy()  # Passthrough
        if not self.world_ctrls:
            hip_jnt = tools_rig_utils.find_joint_from_uuid(self.hip_proxy.get_uuid()).get_short_name()
            # set the correct hip orientation (world aligned)
            self.orientation.set_world_aligned(world_aligned=True)
            self.orientation.apply_automatic_orientation(joint_list=[hip_jnt])
            self.orientation.set_world_aligned(world_aligned=False)

            # Handle neck root if it exists
            # -- hardcoded neck01 purpose TODO: it would be good to find a more flexible solution
            neck_joint = None
            _available_joint_attrs = cmds.ls(f"*.{tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE}")
            # TODO: Update this pattern to be more procedural
            _neck_root_attrs = [attr for attr in _available_joint_attrs if cmds.getAttr(attr) == "neck01"]
            if _neck_root_attrs:
                neck_joint = _neck_root_attrs[0].split(".")[0]

            if self.orientation.get_method() == self.orientation.Methods.inherit:
                neck_joint = None

            if neck_joint:
                # set the correct chest orientation (aim to neck)
                chest_jnt = tools_rig_utils.find_joint_from_uuid(self.chest_proxy.get_uuid())
                cmds.delete(
                    cmds.aimConstraint(
                        neck_joint,
                        chest_jnt,
                        aim=self.orientation.aim_axis,
                        upVector=self.orientation.up_axis,
                        worldUpVector=self.orientation.up_dir,
                        worldUpType="vector",
                    )
                )

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        name_cnst = core_naming.NamingConstants

        # get Joints
        global_o_ctrl = tools_rig_utils.find_ctrl_global_offset()
        hip_jnt = tools_rig_utils.find_joint_from_uuid(self.hip_proxy.get_uuid())
        chest_jnt = tools_rig_utils.find_joint_from_uuid(self.chest_proxy.get_uuid())
        middle_jnt_list = [tools_rig_utils.find_joint_from_uuid(prx.get_uuid()) for prx in self.spine_proxies]
        spine_jnt_list = [hip_jnt] + middle_jnt_list + [chest_jnt]
        module_parent_driven_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())

        # setup names
        setup_name = self.setup_name
        prefix_string = get_formatted_prefix_string(self.prefix)
        prefixed_setup_name = f"{prefix_string}{setup_name}"
        automation_grp_name = "spineAutomation"

        # setup groups
        spine_automation_group = tools_rig_utils.get_automation_group(automation_grp_name)
        joint_automation_group = tools_rig_utils.find_or_create_joint_automation_group()
        core_hrchy.parent(source_objects=module_parent_driven_jnt, target_parent=joint_automation_group)

        # set joints colors
        core_color.set_color_viewport(obj_list=spine_jnt_list, rgb_color=core_color.ColorConstants.RigJoint.GENERAL)

        # get spine scale
        spine_scale = core_math.dist_center_to_center(hip_jnt, chest_jnt)

        # set hip parent
        hip_parent = set_hip_parent(joint_automation_group, module_parent_driven_jnt)

        # setup skeletons - FK, IK, limitQuery
        hip_fk_jnt, mid_fk_jnt_list, chest_fk_jnt, fk_jnt_list = build_knt_skeleton(
            "fk", hip_parent, hip_jnt, middle_jnt_list, chest_jnt
        )
        hip_ik_jnt, mid_ik_jnt_list, chest_ik_jnt, ik_jnt_list = build_knt_skeleton(
            "ik", hip_parent, hip_jnt, middle_jnt_list, chest_jnt
        )
        hip_limit_jnt, mid_limit_jnt_list, chest_limit_jnt, limit_jnt_list = build_knt_skeleton(
            "limitQuery", hip_parent, hip_jnt, middle_jnt_list, chest_jnt
        )

        # constrain hip joint to the limit one
        core_cnstr.constraint_targets(source_driver=hip_jnt, target_driven=hip_limit_jnt)

        # CONTROLS -----------------------------------------------------------------------------------------------------

        # COG main control -------------------------
        hip_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.hip_proxy.get_uuid())
        cog_rotation_order = cmds.getAttr(f"{hip_proxy_item}.{self._attr_rot_order_cog}")
        cog_ctrl, cog_parent_groups, cog_o_ctrl, cog_data_grp = self.create_rig_control(
            control_base_name=self.cog_name,
            curve_file_name="_cog",
            parent_obj=global_o_ctrl,
            match_obj_pos=hip_jnt,
            add_offset_ctrl=True,
            rot_order=cog_rotation_order,
            shape_scale=spine_scale * 0.035,
            color=core_color.ColorConstants.RigControl.CENTER,
        )
        self._add_driver_uuid_attr(
            target_driver=cog_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.COG,
            proxy_purpose=self.cog_name,
        )
        self._add_driver_uuid_attr(
            target_driver=cog_o_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.OFFSET,
            proxy_purpose=self.cog_name,
        )
        # -- pivot control
        cog_pivot_control = self.build_pivot_control(
            control=cog_ctrl,
            start_group=cog_parent_groups[0],
            control_base_name=self.cog_name,
        )[0]
        self._add_driver_uuid_attr(
            target_driver=cog_pivot_control,
            driver_type=tools_rig_const.RiggerDriverTypes.PIVOT,
            proxy_purpose=self.cog_name,
        )
        # -- attributes
        core_attr.hide_lock_default_attrs(obj_list=cog_ctrl, scale=True, visibility=True)

        # Switch control -------------------------
        switch_ctrl, switch_offset_grp = self.create_rig_control(
            control_base_name=self.setup_name,
            curve_file_name="gear_eight_sides_smooth",
            parent_obj=cog_ctrl,
            shape_rot_offset=(0, 0, 90),
            shape_pos_offset=(spine_scale * 0.3, 0, spine_scale * -1.1),
            shape_scale=spine_scale * 0.03,
            color=core_color.get_directional_color(object_name=hip_jnt),
        )[:2]
        # -- driver
        chest_ik_purpose = "spine"
        self._add_driver_uuid_attr(
            target_driver=switch_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.SWITCH,
            proxy_purpose=chest_ik_purpose,
        )
        # -- attributes
        core_attr.hide_lock_default_attrs(
            obj_list=switch_ctrl, translate=True, rotate=True, scale=True, visibility=True
        )

        # Hip control -------------------------
        hip_rotation_order = cmds.getAttr(f"{hip_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        hip_ctrl, hip_parent_groups, hip_o_ctrl, hip_data_grp = self.create_rig_control(
            control_base_name=self.hip_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=cog_data_grp,
            match_obj=hip_jnt,
            add_offset_ctrl=True,
            rot_order=hip_rotation_order,
            shape_pos_offset=(-6, 0, 0),
            shape_scale=spine_scale * 0.8,
            color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
        )
        self._add_driver_uuid_attr(
            target_driver=hip_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.hip_proxy,
        )
        self._add_driver_uuid_attr(
            target_driver=hip_o_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.OFFSET,
            proxy_purpose=self.hip_proxy,
        )
        # -- attributes
        core_attr.hide_lock_default_attrs(obj_list=hip_ctrl, scale=True, visibility=True)
        # -- connect directly the setup chains with the hip
        core_cnstr.constraint_targets(source_driver=hip_o_ctrl, target_driven=hip_fk_jnt)
        core_cnstr.constraint_targets(source_driver=hip_o_ctrl, target_driven=hip_ik_jnt)
        # -- pivot control
        hip_pivot_control = self.build_pivot_control(
            control=hip_ctrl,
            start_group=hip_parent_groups[0],
            control_base_name=self.hip_proxy.get_name(),
        )[0]
        self._add_driver_uuid_attr(
            target_driver=hip_pivot_control,
            driver_type=tools_rig_const.RiggerDriverTypes.PIVOT,
            proxy_purpose=self.hip_proxy,
        )

        # Spine controls -------------------------
        spine_fk_ctrls = []
        last_mid_parent_ctrl = cog_data_grp
        previous_parent = cog_data_grp
        for spine_proxy, fk_jnt in zip(self.spine_proxies, mid_fk_jnt_list):
            spine_proxy_item = tools_rig_utils.find_proxy_from_uuid(spine_proxy.get_uuid())
            spine_rotation_order = cmds.getAttr(f"{spine_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
            spine_fk_ctrl, spine_fk_parent_groups = self.create_rig_control(
                control_base_name=spine_proxy.get_name(),
                curve_file_name="_circle_pos_x",
                parent_obj=last_mid_parent_ctrl,
                match_obj=fk_jnt,
                rot_order=spine_rotation_order,
                shape_scale=spine_scale * 0.8,
                color=core_color.ColorConstants.RGB.BLUE_SKY,
            )[:2]
            self._add_driver_uuid_attr(
                target_driver=spine_fk_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=spine_proxy,
            )
            # -- attributes
            core_attr.hide_lock_default_attrs(spine_fk_ctrl, scale=True, visibility=True)
            # -- constraint
            core_cnstr.constraint_targets(source_driver=spine_fk_ctrl, target_driven=fk_jnt)
            last_mid_parent_ctrl = spine_fk_ctrl
            spine_fk_ctrls.append(spine_fk_ctrl)
            # -- follow setup
            core_attr.add_separator_attr(
                target_object=spine_fk_ctrl, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
            )
            tools_rig_utils.create_follow_setup(control=spine_fk_ctrl, parent=previous_parent)
            previous_parent = fk_jnt

        # Chest FK control -------------------------
        chest_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.chest_proxy.get_uuid())
        chest_rotation_order = cmds.getAttr(f"{chest_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        chest_fk_ctrl = self.create_rig_control(
            control_base_name=self.chest_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=last_mid_parent_ctrl,
            match_obj=chest_jnt,
            rot_order=chest_rotation_order,
            shape_scale=spine_scale * 0.8,
            color=core_color.ColorConstants.RGB.BLUE_SKY,
        )[0]
        self._add_driver_uuid_attr(
            target_driver=chest_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.chest_proxy,
        )
        # -- attributes
        core_attr.hide_lock_default_attrs(chest_fk_ctrl, scale=True, visibility=True)
        # -- constraint
        core_cnstr.constraint_targets(source_driver=chest_fk_ctrl, target_driven=chest_fk_jnt)
        # -- follow setup
        core_attr.add_separator_attr(
            target_object=chest_fk_ctrl, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
        )
        tools_rig_utils.create_follow_setup(control=chest_fk_ctrl, parent=mid_fk_jnt_list[-1])

        # Chest IK Control -------------------------
        ik_suffix = name_cnst.Description.IK.upper()
        chest_ik_base_name = f"{self.setup_name}_{ik_suffix}"
        chest_rot_order_ik = cmds.getAttr(f"{chest_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER_IK}")
        chest_ik_ctrl, chest_ik_parent_groups, chest_ik_o_ctrl, chest_ik_data_grp = self.create_rig_control(
            control_base_name=chest_ik_base_name,
            curve_file_name="_chest_ik",
            parent_obj=cog_data_grp,
            add_offset_ctrl=True,
            rot_order=chest_rot_order_ik,
            shape_scale=spine_scale * 0.025,
            color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
        )
        # -- follow setup
        core_attr.add_separator_attr(
            target_object=chest_ik_ctrl, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
        )
        tools_rig_utils.create_follow_setup(
            control=chest_ik_ctrl, parent=cog_data_grp, attr_name="followCog", constraint_type="orient"
        )
        # -- adjust derivatives suffix
        ctrl_suffix = name_cnst.Suffix.CTRL
        ik_ctrl_suffix = f"_{ik_suffix}_{ctrl_suffix}"
        chest_ik_name = chest_ik_o_ctrl.get_short_name()
        _new_name = chest_ik_name.replace(f"_{ik_suffix}", "").replace(f"_{ctrl_suffix}", ik_ctrl_suffix)
        chest_ik_o_ctrl.rename(_new_name)
        # -- move it in the correct position
        core_trans.match_translate(source=chest_jnt, target_list=chest_ik_parent_groups[0])
        # -- set driver
        self._add_driver_uuid_attr(
            target_driver=chest_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=chest_ik_purpose,
        )
        self._add_driver_uuid_attr(
            target_driver=chest_ik_o_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.OFFSET,
            proxy_purpose=chest_ik_purpose,
        )
        # -- attributes
        core_attr.hide_lock_default_attrs(chest_ik_ctrl, scale=True, visibility=True)
        # -- pivot control
        chest_pivot_ik_ctrl, chest_pivot_ik_line = self.build_pivot_control(
            control=chest_ik_ctrl,
            start_group=chest_ik_parent_groups[0],
            control_base_name=chest_ik_base_name,
        )
        # -- adjust derivatives suffix
        chest_pivot_ik_name = chest_pivot_ik_ctrl.get_short_name()
        _new_name = chest_pivot_ik_name.replace(f"_{ik_suffix}", "").replace(f"_{ctrl_suffix}", ik_ctrl_suffix)
        chest_pivot_ik_ctrl.rename(_new_name)
        _new_name = chest_pivot_ik_line.replace(f"_{ik_suffix}", "").replace(
            f"_{name_cnst.Suffix.LINE}", f"_{ik_suffix}_{name_cnst.Suffix.LINE}"
        )
        cmds.rename(chest_pivot_ik_line, _new_name)
        # -- drivers
        self._add_driver_uuid_attr(
            target_driver=chest_pivot_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.PIVOT,
            proxy_purpose=chest_ik_purpose,
        )

        # IK Spine (Ribbon) -------------------------
        spine_ribbon_grp = f"{prefixed_setup_name}_ribbon_{name_cnst.Suffix.GRP}"
        spine_ribbon_grp = core_hrchy.create_group(name=spine_ribbon_grp)
        spine_ribbon_grp = core_hrchy.parent(source_objects=spine_ribbon_grp, target_parent=spine_automation_group)[0]
        cmds.setAttr(f"{spine_ribbon_grp}.inheritsTransform", 0)  # Ignore Hierarchy Transform

        ribbon_sur = self._assemble_ctrl_name(name="spineRibbon", overwrite_suffix=name_cnst.Suffix.SUR)
        ribbon_sur = core_surface.create_surface_from_object_list(
            obj_list=spine_jnt_list, surface_name=ribbon_sur, custom_normal=(0, 0, 1)
        )
        ribbon_sur = core_hrchy.parent(source_objects=ribbon_sur, target_parent=spine_ribbon_grp)[0]

        # Create Follicles
        follicle_transforms = []
        for index, joint in enumerate(spine_jnt_list):
            if index == 0 or index == len(spine_jnt_list) - 1:  # Skip Hip and Chest
                continue
            joint_pos = cmds.xform(joint, query=True, translation=True, worldSpace=True)
            u_pos, v_pos = core_surface.get_closest_uv_point(surface=ribbon_sur, xyz_pos=joint_pos)
            v_pos_normalized = v_pos / (len(spine_jnt_list) - 1)
            fol_trans, fol_shape = core_surface.create_follicle(
                input_surface=ribbon_sur,
                uv_position=(u_pos, v_pos_normalized),
                name=f"{prefix_string}spineFollicle_{(index + 1):02d}",
            )
            follicle_transforms.append(fol_trans)
        core_hrchy.parent(source_objects=follicle_transforms, target_parent=spine_ribbon_grp)

        # Create Limit Query IK Handle
        ik_limit_handle = self._assemble_ctrl_name(name="spineLimit", overwrite_suffix=name_cnst.Suffix.IK_HANDLE_SC)
        ik_limit_handle = cmds.ikHandle(
            name=ik_limit_handle, solver="ikSCsolver", startJoint=limit_jnt_list[0], endEffector=limit_jnt_list[-1]
        )[0]
        ik_limit_handle = core_node.Node(ik_limit_handle)
        core_cnstr.constraint_targets(source_driver=chest_ik_data_grp, target_driven=ik_limit_handle)

        # Constraints
        # Constraints FK -> Base
        for fk_jnt, base_jnt in zip(fk_jnt_list, spine_jnt_list):
            core_cnstr.constraint_targets(source_driver=fk_jnt, target_driven=base_jnt)
        # Constraints Follicle -> IK
        for spine_fol, ik_jnt in zip(follicle_transforms, mid_ik_jnt_list):
            core_cnstr.constraint_targets(source_driver=spine_fol, target_driven=ik_jnt)

        # Create Squash Stretch System (limitQuery)
        core_attr.add_separator_attr(target_object=chest_ik_ctrl, attr_name="squashStretch")
        stretchy_grp = core_rigging.create_stretchy_ik_setup(
            ik_handle=ik_limit_handle, attribute_holder=chest_ik_ctrl, prefix=prefixed_setup_name
        )
        core_hrchy.parent(source_objects=ik_limit_handle, target_parent=spine_ribbon_grp)
        core_hrchy.parent(source_objects=stretchy_grp, target_parent=spine_automation_group)
        end_loc, start_loc = cmds.listConnections(f"{stretchy_grp}.message")

        # Setup Ribbon Limit Query Logic
        last_limit_query_jnt = limit_jnt_list[-1]
        # Redirect Stretchy System Term Driver
        for child in cmds.listRelatives(end_loc, children=True, typ="pointConstraint") or []:
            cmds.delete(child)
        core_cnstr.constraint_targets(
            source_driver=chest_ik_data_grp,
            target_driven=end_loc,
            maintain_offset=False,
            constraint_type=core_cnstr.ConstraintTypes.POINT,
        )

        # Spine IK control -------------------------
        temp_fol_trans, temp_fol_shape = core_surface.create_follicle(
            input_surface=ribbon_sur,
            uv_position=(0.5, 0.5),
            name=f"{prefix_string}tempFollicle",
        )

        spine_mid_ik_base_name = f"{setup_name}Mid_{ik_suffix}"
        spine_mid_ik_purpose = "spineMid"
        spine_ik_ctrl, spine_ik_parent_groups = self.create_rig_control(
            control_base_name=spine_mid_ik_base_name,
            curve_file_name="square",
            parent_obj=cog_data_grp,
            match_obj=chest_ik_ctrl,
            add_offset_ctrl=False,
            rot_order=chest_rot_order_ik,
            shape_scale=spine_scale * 1.6,
            color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=spine_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=spine_mid_ik_purpose,
        )

        core_trans.match_translate(source=temp_fol_trans, target_list=spine_ik_parent_groups[0])

        cmds.delete(temp_fol_trans)
        # -- attributes
        core_attr.hide_lock_default_attrs(spine_ik_ctrl, scale=True, visibility=True)

        # Ribbon Driver Joints -------------------------
        hip_ribbon_jnt = f"{self.hip_proxy.get_name()}_{name_cnst.Description.RIBBON}_{name_cnst.Suffix.JNT}"
        hip_ribbon_jnt = core_hrchy.duplicate_object(obj=hip_jnt, name=hip_ribbon_jnt)
        core_trans.match_transform(source=cog_ctrl, target_list=hip_ribbon_jnt)

        spine_ribbon_jnt = f"{setup_name}_{name_cnst.Description.RIBBON}_{name_cnst.Suffix.JNT}"
        spine_ribbon_jnt = core_hrchy.duplicate_object(obj=hip_ribbon_jnt, name=spine_ribbon_jnt)
        core_trans.match_transform(source=spine_ik_ctrl, target_list=spine_ribbon_jnt)

        chest_ribbon_jnt = f"{self.chest_proxy.get_name()}_{name_cnst.Description.RIBBON}_{name_cnst.Suffix.JNT}"
        chest_ribbon_jnt = core_hrchy.duplicate_object(obj=chest_jnt, name=chest_ribbon_jnt)
        core_trans.match_transform(source=chest_ik_ctrl, target_list=chest_ribbon_jnt)

        # Attach Extremities (Skipped when creating follicles)
        core_cnstr.constraint_targets(source_driver=chest_ribbon_jnt, target_driven=chest_ik_jnt)

        # Connect Ribbon Controls and Joints
        follow_constraint = core_cnstr.constraint_targets(
            source_driver=[hip_ribbon_jnt, chest_ribbon_jnt], target_driven=spine_ik_parent_groups[0]
        )[0]
        ribbon_driver_joints = [hip_ribbon_jnt, spine_ribbon_jnt, chest_ribbon_jnt]
        core_joint.set_joint_radius(joints=ribbon_driver_joints, radius=spine_scale * 0.1)
        core_color.set_color_viewport(
            obj_list=ribbon_driver_joints, rgb_color=core_color.ColorConstants.RigJoint.AUTOMATION
        )
        ribbon_skin_cluster = cmds.skinCluster(
            ribbon_driver_joints,
            ribbon_sur,
            dropoffRate=self.dropoff_rate,
            nurbsSamples=15,
            bindMethod=0,  # Closest Distance
            name=f"{prefix_string}spineRibbon_skinCluster",
        )[0]

        core_cnstr.constraint_targets(source_driver=cog_data_grp, target_driven=hip_ribbon_jnt)
        core_cnstr.constraint_targets(source_driver=spine_ik_ctrl, target_driven=spine_ribbon_jnt)
        core_cnstr.constraint_targets(
            source_driver=chest_ik_data_grp,
            target_driven=chest_ribbon_jnt,
            constraint_type=core_cnstr.ConstraintTypes.ORIENT,
        )
        core_cnstr.constraint_targets(
            source_driver=last_limit_query_jnt,
            target_driven=chest_ribbon_jnt,
            constraint_type=core_cnstr.ConstraintTypes.POINT,
        )

        spine_ik_ctrl_shape = cmds.listRelatives(spine_ik_ctrl, shapes=True, fullPath=True)[0]
        core_attr.connect_attr(source_attr=f"{cog_ctrl}.visibilityB", target_attr_list=f"{spine_ik_ctrl_shape}.v")
        core_hrchy.parent(source_objects=ribbon_driver_joints, target_parent=joint_automation_group)

        # Follow Hip and Chest Attribute
        core_attr.add_attr(obj_list=spine_ik_ctrl, attributes="followHipAndChest", default=1, minimum=0, maximum=1)
        cmds.connectAttr(f"{spine_ik_ctrl}.followHipAndChest", f"{follow_constraint}.w0")  # Hip
        cmds.connectAttr(f"{spine_ik_ctrl}.followHipAndChest", f"{follow_constraint}.w1")  # Chest

        # Create Switch Setup
        fk_controls = [chest_fk_ctrl] + spine_fk_ctrls
        ik_controls = [chest_ik_ctrl, chest_ik_o_ctrl, chest_pivot_ik_ctrl, spine_ik_ctrl]
        core_attr.add_separator_attr(
            target_object=switch_ctrl, attr_name=core_rigging.RiggingConstants.SEPARATOR_SWITCH
        )
        core_rigging.create_switch_setup(
            source_a=fk_jnt_list,
            source_b=ik_jnt_list,
            target_base=spine_jnt_list,
            attr_holder=switch_ctrl,
            visibility_a=fk_controls,
            visibility_b=ik_controls,
            prefix=prefix_string,
            invert=True,
        )
        influence_switch_attr = core_rigging.RiggingConstants.ATTR_INFLUENCE_SWITCH
        influence_switch_attr_nice_name = "FK/IK"
        cmds.addAttr(f"{switch_ctrl}.{influence_switch_attr}", e=True, nn=influence_switch_attr_nice_name)
        cmds.setAttr(f"{switch_ctrl}.{influence_switch_attr}", 0)  # Default is FK

        # Set Initial Chest Pivot to Spine Control ---------------------------------------------------------
        # core_trans.match_translate(source=spine_ik_ctrl, target_list=chest_ik_pivot_ctrl)

        # Chest Driven Group (For Parented Controls) -------------------------------------------------------
        chest_driven = self._assemble_ctrl_name(
            name=self.chest_proxy.get_name(),
            overwrite_suffix=name_cnst.Suffix.DRIVER,
        )
        chest_driven = core_hrchy.create_group(name=chest_driven)
        self._add_driver_uuid_attr(
            target_driver=chest_driven,
            driver_type=tools_rig_const.RiggerDriverTypes.GENERIC,
            proxy_purpose=self.chest_proxy,
        )
        core_cnstr.constraint_targets(source_driver=chest_jnt, target_driven=chest_driven, maintain_offset=False)
        core_hrchy.parent(source_objects=chest_driven, target_parent=cog_data_grp)

        # Outliner Clean-up --------------------------------------------------------------------------------
        core_outlnr.reorder_front(target_list=joint_automation_group)
        # Set Automation Visibility
        cmds.setAttr(f"{spine_automation_group}.v", 0)
        cmds.setAttr(f"{joint_automation_group}.v", 0)

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [cog_parent_groups[0]]

    def build_rig_post(self, project_prefix=None, **kwargs):
        """
        Runs post rig script phase.
        This step runs after the execution of "build_rig" is completed.
        Usually used to define automation or connections that require external elements to exist.

        Args:
            project_prefix (str, optional): An optional prefix related to the project.
                Not used directly in this method but accepted for extensibility.
            **kwargs: Additional keyword arguments (currently unused).
        """
        super().build_rig_post()  # Passthrough / _parent_module_children_drivers

        # Setup Cog Follow System
        # -- follow setup - Rotation and Position
        parent_module_uuid = self.get_parent_uuid()
        cog_driver_uuid = f"{self.get_uuid()}-{tools_rig_const.RiggerDriverTypes.COG}-{self.cog_name}"
        cog_ctrl = tools_rig_utils.find_driver_from_uuid(uuid_string=cog_driver_uuid)
        _cog_follow_parent = tools_rig_utils.find_joint_from_uuid(parent_module_uuid)
        # define COG parent (potential overwrite)
        if isinstance(self.cog_parent, str):
            _cog_parent = tools_rig_utils.find_driver_from_uuid(uuid_string=self.cog_parent)
            if _cog_parent is not None and cmds.objExists(_cog_parent):
                _cog_follow_parent = core_node.Node(_cog_parent)
            else:
                logger.warning(f'Provided COG parent "{self.cog_parent}" is missing. Module parent was used instead.')
        if parent_module_uuid:
            core_attr.add_separator_attr(
                target_object=cog_ctrl, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
            )
            tools_rig_utils.create_follow_setup(
                control=cog_ctrl,
                parent=_cog_follow_parent,
                attr_name="followGlobal",
                constraint_type="orient",
            )
            tools_rig_utils.create_follow_setup(
                control=cog_ctrl,
                parent=_cog_follow_parent,
                attr_name="followGlobal",
                constraint_type="point",
            )

    # ------------------------------------------- Extra Module Setters -------------------------------------------
    def set_ribbon_dropoff_rate(self, rate):
        """
        Sets the foot control name by editing the metadata value associated with it.
        Args:
            rate (int, float): Dropoff rate for the ribbon controls. Range 0.1 to 10.0
        """
        if not (0.1 <= rate <= 10.0):
            logger.warning("Dropoff rate must be between 0.1 and 10.0")
            return

        self.dropoff_rate = rate

    def set_cog_ctrl_name(self, cog_name):
        """
        Sets the cog (center of gravity) control name by editing the metadata value associated with it.
        Args:
            cog_name (str): New name for the cog control. If empty the default name will be used instead.
        """
        if not isinstance(cog_name, str):
            logger.warning("Unable to set COG control name. Input must be a string.")
            return
        self.cog_name = cog_name

    def set_cog_parent(self, cog_parent_driver_uuid):
        """
        Sets the cog (center of gravity) potential parent.
        This is so the spine can be parented to a root joint and still follow a global control.
        Args:
            cog_parent_driver_uuid (str, None): Driver_uuid to an object to be used as the COG parent.
                              If empty the module parent is used instead.

        """
        if cog_parent_driver_uuid is None or cog_parent_driver_uuid == "":  # Clear parent
            self.cog_parent = None
            return
        if not isinstance(cog_parent_driver_uuid, str):
            logger.warning('Unable to set COG parent "driver_uuid". Input must be a string.')
            return
        self.cog_parent = cog_parent_driver_uuid

    # --------------------------------------------------- Misc ---------------------------------------------------
    def build_pivot_control(
            self,
            control,
            start_group,
            control_base_name=None,
            overwrite_prefix=None,
            control_scale=20,
    ):
        """
        Builds the pivot control related to the given main control.

        Args:
            control (Node): main control of the offset control that you are building.
            start_group (Node, str): the group that drives the start point for the connection line
            control_base_name (str): type/s of the control, the main part of the name, the entire name will be assembled
                                inside this function (e.g. "root", "upperArm", "lowerLegTwist", etc.)
            overwrite_prefix (str): None by default. Control name prefix comes from the module prefix, which usually
                                    it's the side. There are cases in which you need to change it.
            control_scale (float): scale for the shape

        Returns:
            pivot_ctrl (Node): pivot control
            pivot_line (str): curve line name
        """
        name_cnst = core_naming.NamingConstants

        # get pivot control name
        pivot_suffix = name_cnst.Description.PIVOT
        pivot_suffix_cap = pivot_suffix[0].upper() + pivot_suffix[1:]
        pivot_control_base_name = f"{control_base_name}{pivot_suffix_cap}"
        pivot_control_name = self._assemble_ctrl_name(name=pivot_control_base_name, overwrite_prefix=overwrite_prefix)

        # build pivot control
        pivot_control = tools_rig_utils.create_ctrl_default(name=pivot_control_name, curve_file_name="_locator")

        # -- build line
        pivot_line = tools_rig_utils.create_control_visualization_line(pivot_control, start_group)

        # -- move and parent
        core_trans.match_translate(source=control, target_list=pivot_control)
        core_hrchy.parent(source_objects=pivot_control, target_parent=control)

        # -- set pivot control
        core_color.set_color_viewport(obj_list=pivot_control, rgb_color=core_color.ColorConstants.RigControl.PIVOT)
        core_trans.scale_shapes(obj_transform=pivot_control, offset=control_scale)
        core_curve.set_curve_width(obj_list=pivot_control, line_width=3)

        # -- attributes
        cmds.connectAttr(f"{pivot_control}.translate", f"{control}.rotatePivot")
        core_attr.hide_lock_default_attrs(obj_list=pivot_control, rotate=True, scale=True, visibility=False)
        core_attr.add_attr(obj_list=control, attributes=core_rigging.RiggingConstants.ATTR_SHOW_PIVOT, attr_type="bool")
        core_attr.connect_attr(
            source_attr=f"{control}.{core_rigging.RiggingConstants.ATTR_SHOW_PIVOT}",
            target_attr_list=[f"{pivot_control}.v"],
        )

        return pivot_control, pivot_line


# ---- helpers ----
def get_formatted_prefix_string(prefix):
    """
    adds the underscore after the prefix.
    Args:
        prefix (string)

    Returns:
        prefix (string): if not empty, adds the underscore
    """
    formatted_prefix_string = ""
    if prefix:
        formatted_prefix_string = f"{prefix}_"
    return formatted_prefix_string


def set_hip_parent(joint_automation_grp, module_parent_jnt):
    """
    sets the hip parent.

    Args:
        joint_automation_grp (str): Name of the joint automation group.
        module_parent_jnt (str): Name of the module parent joint, if available.

    Returns:
        str: The parent for the hip.
    """
    if module_parent_jnt:
        core_color.set_color_viewport(
            obj_list=module_parent_jnt, rgb_color=core_color.ColorConstants.RigJoint.AUTOMATION
        )
        core_rigging.rescale_joint_radius(
            joint_list=module_parent_jnt, multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_DRIVEN
        )
        hip_parent = module_parent_jnt
    else:
        hip_parent = joint_automation_grp

    return hip_parent


def build_knt_skeleton(skeleton_suffix, hip_parent, hip_jnt, middle_jnt_list, chest_jnt):
    """
    builds the kinematic skeleton for the setup duplicating the main skeleton.

    Args:
        skeleton_suffix (string): "fk", "ik" or "limitQuery"
        hip_parent (string): hip parent item
        hip_jnt (string): hip joint
        middle_jnt_list (list): middle joints
        chest_jnt (string): chest joint

    Returns:
        hip_knt_joint, mid_knt_joints, chest_knt_joint, knt_joints
    """

    if skeleton_suffix == "fk":
        suffix = core_naming.NamingConstants.Description.FK
        color_viewport = core_color.ColorConstants.RigJoint.FK
        color_outliner = core_color.ColorConstants.RigOutliner.FK
        radius_multiplier = tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_FK
    elif skeleton_suffix == "ik":
        suffix = core_naming.NamingConstants.Description.IK
        color_viewport = core_color.ColorConstants.RigJoint.IK
        color_outliner = core_color.ColorConstants.RigOutliner.IK
        radius_multiplier = tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_IK
    elif skeleton_suffix == "limitQuery":
        suffix = skeleton_suffix
        color_viewport = core_color.ColorConstants.RigJoint.DATA_QUERY
        color_outliner = core_color.ColorConstants.RigOutliner.DATA_QUERY
        radius_multiplier = tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_DATA_QUERY
    else:
        logger.error("given kinematic not defined")
        return

    hip_knt_joint = core_rigging.duplicate_joint_for_automation(hip_jnt, suffix=suffix, parent=hip_parent)

    mid_knt_joints = []
    last_mid_parent = hip_knt_joint
    for mid in middle_jnt_list:
        mid_knt_joint = core_rigging.duplicate_joint_for_automation(mid, suffix=suffix, parent=last_mid_parent)
        mid_knt_joints.append(mid_knt_joint)
        last_mid_parent = mid_knt_joint

    chest_knt_joint = core_rigging.duplicate_joint_for_automation(chest_jnt, suffix=suffix, parent=last_mid_parent)
    knt_joints = [hip_knt_joint] + mid_knt_joints + [chest_knt_joint]

    core_rigging.rescale_joint_radius(joint_list=knt_joints, multiplier=radius_multiplier)
    core_color.set_color_viewport(obj_list=knt_joints, rgb_color=color_viewport)
    core_color.set_color_outliner(obj_list=knt_joints, rgb_color=color_outliner)

    return hip_knt_joint, mid_knt_joints, chest_knt_joint, knt_joints


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)

    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    import gt.core.session as core_session

    core_session.remove_modules_startswith("gt.tools.auto_rigger.module")
    core_session.remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils

    # import gt.tools.auto_rigger.modules.module_spine as tools_rig_mod_spine
    import gt.tools.auto_rigger.modules.module_root as tools_rig_mod_root
    import importlib

    importlib.reload(tools_rig_mod_root)
    importlib.reload(tools_rig_fmr)
    importlib.reload(tools_rig_utils)

    a_root = tools_rig_mod_root.ModuleRoot()
    a_spine = ModuleSpine()

    root_uuid = a_root.root_proxy.get_uuid()
    a_spine.set_parent_uuid(root_uuid)
    a_spine.set_spine_number(2)

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_spine)

    a_project.build_proxy()
    # a_project.build_skeleton()
    a_project.build_rig()

    # save user changes
    # new_project.read_data_from_scene()
    # dictionary = new_project.get_project_as_dict()
    # print(dictionary)

    # rebuild with user changes
    # rig_prj = tools_rig_fmr.RigProject()
    # male_biped_spine_dict = {}  # supply dict
    # rig_prj.read_data_from_dict(male_biped_spine_dict)
    # rig_prj.build_proxy()
    # rig_prj.build_skeleton()
    # rig_prj.build_rig()

    # Show all
    cmds.viewFit(all=True)
