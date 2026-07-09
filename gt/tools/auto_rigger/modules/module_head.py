"""
Auto Rigger Head Module
"""

import gt.core.attr as core_attr
import gt.core.math as core_math
import gt.core.node as core_node
import gt.core.color as core_color
import gt.core.curve as core_curve
import gt.core.naming as core_naming
import gt.core.rigging as core_rigging
import gt.core.hierarchy as core_hrchy
import gt.core.transform as core_trans
import gt.core.constraint as core_cnstr
import gt.ui.resource_library as ui_res_lib
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import maya.cmds as cmds
import logging
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleHead(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_head
    allow_parenting = True

    def __init__(self, name="Head", prefix=core_naming.NamingConstants.Prefix.CENTER, suffix=None):
        """
        Initialize the head module, setting up orientation, proxies, and defaults.

        Args:
            name (str): Module name.
            prefix (str or None): Prefix for naming.
            suffix (str or None): Suffix for naming.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.neck_number = 1  # number of elements between the base neck and the head

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)
        self.set_orientation_method(method="automatic")
        self.orientation.set_world_aligned(world_aligned=True)

        self._default_neck_mid_name = "neck"
        self._default_neck_base_name = f"{self._default_neck_mid_name}01"
        self._default_neck_suffix = "neckBaseData"
        self._end_suffix = core_naming.NamingConstants.Description.END.capitalize()

        # Extra Module Data
        self.build_jaw = True
        self.build_eyes = True
        self.prefix_eye_left = core_naming.NamingConstants.Prefix.LEFT
        self.prefix_eye_right = core_naming.NamingConstants.Prefix.RIGHT
        self.delete_head_jaw_bind_jnt = True
        self.set_extra_callable_function(self._delete_unbound_joints)  # Called after the control rig is built

        # Neck Base (Chain Base)
        self.neck_base_proxy = tools_rig_frm.Proxy(name=self._default_neck_base_name)
        pos_neck_base = core_trans.Vector3(y=137)
        self.neck_base_proxy.set_initial_position(xyz=pos_neck_base)
        self.neck_base_proxy.set_locator_scale(scale=1.5)
        self.neck_base_proxy.set_meta_purpose(value=self._default_neck_base_name)
        self.neck_base_proxy.set_rotation_order(rotation_order=1)
        self.neck_base_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        # Head (Chain End)
        self.head_proxy = tools_rig_frm.Proxy(name="head")
        pos_head = core_trans.Vector3(y=142.5)
        self.head_proxy.set_initial_position(xyz=pos_head)
        self.head_proxy.set_locator_scale(scale=1.5)
        self.head_proxy.set_meta_purpose(value="head")
        self.head_proxy.set_rotation_order(rotation_order=1)
        self.head_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )

        # Head End
        self.head_end_proxy = tools_rig_frm.Proxy(name=f"head{self._end_suffix}")
        pos_head_end = core_trans.Vector3(y=160)
        self.head_end_proxy.set_initial_position(xyz=pos_head_end)
        self.head_end_proxy.set_locator_scale(scale=1)
        self.head_end_proxy.set_meta_purpose(value="headEnd")
        self.head_end_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
        self.head_end_proxy.set_rotation_order(rotation_order=1)
        self.head_end_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC])
        self.head_end_proxy.set_parent_uuid(self.head_proxy.get_uuid())
        self.head_end_proxy.set_setup_driver_uuid(self.head_proxy.get_uuid())

        # jaw, eyes, neck mid (in-between)
        self.neck_mid_proxies = []
        self.jaw_proxy = None
        self.jaw_end_proxy = None
        self.lt_eye_proxy = None
        self.rt_eye_proxy = None

        # Jaw
        self.jaw_proxy = tools_rig_frm.Proxy(name="jaw")
        pos_jaw = core_trans.Vector3(y=147.5, z=2.5)
        self.jaw_proxy.set_initial_position(xyz=pos_jaw)
        self.jaw_proxy.set_locator_scale(scale=1.5)
        self.jaw_proxy.set_meta_purpose(value="jaw")
        self.jaw_proxy.set_rotation_order(rotation_order=1)
        self.jaw_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])
        self.jaw_proxy.set_setup_driver_uuid(self.head_proxy.get_uuid())
        self.jaw_proxy.set_parent_uuid(self.head_proxy.get_uuid())

        # Jaw End
        self.jaw_end_proxy = tools_rig_frm.Proxy(name=f"jaw{self._end_suffix}")
        pos_jaw_end = core_trans.Vector3(y=142.5, z=11)
        self.jaw_end_proxy.set_initial_position(xyz=pos_jaw_end)
        self.jaw_end_proxy.set_locator_scale(scale=1)
        self.jaw_end_proxy.set_meta_purpose(value="jawEnd")
        self.jaw_end_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
        self.jaw_end_proxy.set_rotation_order(rotation_order=1)
        self.jaw_end_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC])
        self.jaw_end_proxy.set_setup_driver_uuid(self.jaw_proxy.get_uuid())
        self.jaw_end_proxy.set_parent_uuid(self.jaw_proxy.get_uuid())

        self.lt_eye_proxy = tools_rig_frm.Proxy(name="eye")
        pos_lt_eye = core_trans.Vector3(x=3.5, y=151, z=8.7)
        self.lt_eye_proxy.set_initial_position(xyz=pos_lt_eye)
        self.lt_eye_proxy.set_locator_scale(scale=2.5)
        self.lt_eye_proxy.set_meta_purpose(value="eyeLeft")
        self.lt_eye_proxy.set_rotation_order(rotation_order=1)
        self.lt_eye_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.AIM])
        self.lt_eye_proxy.set_setup_driver_uuid(self.head_proxy.get_uuid())
        self.lt_eye_proxy.set_parent_uuid(self.head_proxy.get_uuid())

        # Right Eye
        self.rt_eye_proxy = tools_rig_frm.Proxy(name="eye")
        pos_rt_eye = core_trans.Vector3(x=-3.5, y=151, z=8.7)
        self.rt_eye_proxy.set_initial_position(xyz=pos_rt_eye)
        self.rt_eye_proxy.set_locator_scale(scale=2.5)
        self.rt_eye_proxy.set_meta_purpose(value="eyeRight")
        self.rt_eye_proxy.set_rotation_order(rotation_order=1)
        self.rt_eye_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.AIM])
        self.rt_eye_proxy.set_setup_driver_uuid(self.head_proxy.get_uuid())
        self.rt_eye_proxy.set_parent_uuid(self.head_proxy.get_uuid())

        self.set_mid_neck_num(neck_mid_num=self.neck_number)

    def set_mid_neck_num(self, neck_mid_num):
        """
        Set a new number of neckMid proxies. These are the proxies in-between the hip proxy (base) and head proxy (end)
        Args:
            neck_mid_num (int): New number of neckMid proxies to exist in-between neckBase and head.
                                Minimum is zero (0) - No negative numbers.
        """
        neck_mid_len = len(self.neck_mid_proxies)
        base_num = 1  # neck01 is the neck base

        # Same as current, skip
        if neck_mid_len == neck_mid_num:
            return
        # New number higher than current - Add more proxies (neck_mid_list)
        if neck_mid_len < neck_mid_num:
            # Determine Initial Parent (Last neckMid, or neckBase)
            if self.neck_mid_proxies:
                _parent_uuid = self.neck_mid_proxies[-1].get_uuid()
            else:
                _parent_uuid = self.neck_base_proxy.get_uuid()
            # Create new proxies
            for num in range(neck_mid_len + base_num, neck_mid_num + base_num):
                neck_mid_name = f"{self._default_neck_mid_name}{str(num + 1).zfill(2)}"
                new_neck_mid = tools_rig_frm.Proxy(name=neck_mid_name)
                new_neck_mid.set_locator_scale(scale=1)
                new_neck_mid.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
                new_neck_mid.set_meta_purpose(value=neck_mid_name)
                new_neck_mid.add_line_parent(line_parent=_parent_uuid)
                new_neck_mid.set_rotation_order(rotation_order=1)
                new_neck_mid.add_driver_type(
                    driver_type=[
                        tools_rig_const.RiggerDriverTypes.GENERIC,
                        tools_rig_const.RiggerDriverTypes.FK,
                    ]
                )
                _parent_uuid = new_neck_mid.get_uuid()
                self.neck_mid_proxies.append(new_neck_mid)
        # New number lower than current - Remove unnecessary proxies
        elif len(self.neck_mid_proxies) > neck_mid_num:
            self.neck_mid_proxies = self.neck_mid_proxies[:neck_mid_num]  # Truncate the list

        # If no neckMid, then set neckBase as head's parent
        if self.neck_mid_proxies:
            self.head_proxy.add_line_parent(line_parent=self.neck_mid_proxies[-1].get_uuid())
        else:
            self.head_proxy.add_line_parent(line_parent=self.neck_base_proxy.get_uuid())

        self.neck_number = neck_mid_num
        self.refresh_proxies_list()

    def refresh_proxies_list(self):
        """
        Refreshes the main proxies list used by the module during build (update in case objects were updated)
        """
        self.proxies = [self.neck_base_proxy]
        self.proxies.extend(self.neck_mid_proxies)
        self.proxies.append(self.head_proxy)
        self.proxies.append(self.head_end_proxy)
        if self.build_eyes:
            self.proxies.append(self.lt_eye_proxy)
            self.proxies.append(self.rt_eye_proxy)
        if self.build_jaw:
            self.proxies.append(self.jaw_proxy)
            self.proxies.append(self.jaw_end_proxy)

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
        _neck_mid_num = -1  # Skip required neck base
        neck_mid_pattern = r"neck\d+"
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(tools_rig_const.RiggerConstants.META_PROXY_PURPOSE)
                if bool(re.match(neck_mid_pattern, meta_type)):
                    _neck_mid_num += 1
        self.set_mid_neck_num(_neck_mid_num)
        self.read_purpose_matching_proxy_from_dict(proxy_dict)
        self.refresh_proxies_list()

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
            if self.neck_base_proxy:
                self.neck_base_proxy.set_parent_uuid(self.parent_uuid)
        self.head_proxy.set_setup_driver_uuid(self.neck_base_proxy.get_uuid())
        self.head_proxy.set_parent_uuid(self.neck_base_proxy.get_uuid())
        prx_driver = self.head_proxy
        for prx in self.neck_mid_proxies:
            prx.set_setup_driver_uuid(prx_driver.get_uuid())
            prx.set_parent_uuid(prx_driver.get_uuid())
            prx_driver = prx
        self.head_end_proxy.set_setup_driver_uuid(self.head_proxy.get_uuid())
        self.head_end_proxy.set_parent_uuid(self.head_proxy.get_uuid())
        self.jaw_proxy.set_setup_driver_uuid(self.head_proxy.get_uuid())
        self.jaw_proxy.set_parent_uuid(self.head_proxy.get_uuid())
        self.jaw_end_proxy.set_setup_driver_uuid(self.jaw_proxy.get_uuid())
        self.jaw_end_proxy.set_parent_uuid(self.jaw_proxy.get_uuid())
        self.lt_eye_proxy.set_setup_driver_uuid(self.head_proxy.get_uuid())
        self.lt_eye_proxy.set_parent_uuid(self.head_proxy.get_uuid())
        self.rt_eye_proxy.set_setup_driver_uuid(self.head_proxy.get_uuid())
        self.rt_eye_proxy.set_parent_uuid(self.head_proxy.get_uuid())

        # set module prefix for central proxies (non-eye proxies)
        _center_proxies = [self.neck_base_proxy]
        _center_proxies.extend(self.neck_mid_proxies)
        _center_proxies.append(self.head_proxy)
        _center_proxies.append(self.head_end_proxy)

        if self.build_jaw:
            _center_proxies.append(self.jaw_proxy)
            _center_proxies.append(self.jaw_end_proxy)

        for _center_proxy in _center_proxies:
            _center_proxy.add_to_attr_dict("prefix", self.prefix)

        self.proxies = _center_proxies

        proxy_data = super().build_proxy(**kwargs)

        # Build Eyes
        if self.build_eyes:
            module_prefix = self.prefix
            self.prefix = self.prefix_eye_left
            self.lt_eye_proxy.add_to_attr_dict("prefix", self.prefix_eye_left)
            self.proxies = [self.lt_eye_proxy]
            proxy_data.extend(super().build_proxy(**kwargs))
            self.prefix = self.prefix_eye_right
            self.rt_eye_proxy.add_to_attr_dict("prefix", self.prefix_eye_right)
            self.proxies = [self.rt_eye_proxy]
            proxy_data.extend(super().build_proxy(**kwargs))
            self.prefix = module_prefix

        # reset status
        self.refresh_proxies_list()

        return proxy_data

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        # Get Maya Elements
        hip = tools_rig_utils.find_proxy_from_uuid(self.neck_base_proxy.get_uuid())
        chest = tools_rig_utils.find_proxy_from_uuid(self.head_proxy.get_uuid())

        neck_mid_list = []
        for neck_mid in self.neck_mid_proxies:
            neck_node = tools_rig_utils.find_proxy_from_uuid(neck_mid.get_uuid())
            neck_mid_list.append(neck_node)
        self.neck_base_proxy.apply_offset_transform()
        self.head_proxy.apply_offset_transform()
        self.head_end_proxy.apply_offset_transform()

        if self.jaw_proxy and self.jaw_end_proxy:
            self.jaw_proxy.apply_offset_transform()
            self.jaw_end_proxy.apply_offset_transform()

        if self.lt_eye_proxy and self.rt_eye_proxy:
            self.lt_eye_proxy.apply_offset_transform()
            self.rt_eye_proxy.apply_offset_transform()

        neck_mid_offsets = []
        for neck_mid in neck_mid_list:
            offset = tools_rig_utils.get_proxy_offset(neck_mid)
            neck_mid_offsets.append(offset)
        core_cnstr.equidistant_constraints(start=hip, end=chest, target_list=neck_mid_offsets)

        # Apply transform after set the order with build_proxy_setup parent function
        super().build_proxy_setup()  # Passthrough

        # Set proxy parent for the skeleton hierarchy
        prx_parent = self.neck_base_proxy
        for prx in self.neck_mid_proxies:
            prx.set_parent_uuid(prx_parent.get_uuid())
            prx_parent = prx
        self.head_proxy.set_parent_uuid(self.neck_mid_proxies[-1].get_uuid())

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        # Get direction object
        direction_crv = tools_rig_utils.find_ctrl_global_offset()

        # get joints
        (
            skeleton_joints,
            neck_base_jnt,
            neck_mid_jnt_list,
            head_jnt,
            head_end_jnt,
            jaw_jnt,
            jaw_end_jnt,
            lt_eye_jnt,
            rt_eye_jnt,
        ) = self.get_joints()

        # set joints color
        core_color.set_color_viewport(
            obj_list=[head_end_jnt, jaw_end_jnt],
            rgb_color=core_color.ColorConstants.RigJoint.END,
        )
        core_color.set_color_viewport(
            obj_list=[lt_eye_jnt, rt_eye_jnt],
            rgb_color=core_color.ColorConstants.RigJoint.UNIQUE,
        )

        # head scale
        head_scale = core_math.dist_center_to_center(neck_base_jnt, head_jnt)
        head_scale += core_math.dist_center_to_center(head_jnt, head_end_jnt)

        # neck base control -----------------------------------------------------------
        neck_base_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.neck_base_proxy.get_uuid())
        neck_base_rot_order = cmds.getAttr(f"{neck_base_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        neck_base_ctrl, neck_base_parent_grps = self.create_rig_control(
            control_base_name=self.neck_base_proxy.get_name(),
            # curve_file_name="_pin_neg_y",  # previous control
            curve_file_name="_circle_pos_x",
            parent_obj=direction_crv,
            match_obj=neck_base_jnt,
            rot_order=neck_base_rot_order,
            shape_scale=head_scale * 0.7,
        )[:2]
        # -- driver
        self._add_driver_uuid_attr(
            target_driver=neck_base_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.neck_base_proxy,
        )
        # -- constraint
        core_cnstr.constraint_targets(source_driver=neck_base_ctrl, target_driven=neck_base_jnt)
        # -- attributes
        core_attr.hide_lock_default_attrs(obj_list=neck_base_ctrl, scale=True, visibility=True)
        # -- follow setup - Rotation and Position
        parent_module = self.get_parent_uuid()
        if parent_module:
            core_attr.add_separator_attr(
                target_object=neck_base_ctrl, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
            )
            tools_rig_utils.create_follow_setup(
                control=neck_base_ctrl, parent=tools_rig_utils.find_joint_from_uuid(parent_module)
            )

        # neck mid controls -----------------------------------------------------------
        neck_mid_ctrls = []
        neck_mid_auto_data_grps = []
        last_mid_parent_ctrl = neck_base_ctrl
        for neck_mid_proxy, mid_jnt in zip(self.neck_mid_proxies, neck_mid_jnt_list):
            _shape_scale_mid = head_scale * 0.6
            child_joint = cmds.listRelatives(mid_jnt, fullPath=True, children=True, typ="joint")
            if child_joint:
                _distance = core_math.dist_center_to_center(obj_a=mid_jnt, obj_b=child_joint[0])
                _shape_scale_mid = _distance * 3.8

            neck_mid_proxy_item = tools_rig_utils.find_proxy_from_uuid(neck_mid_proxy.get_uuid())
            neck_mid_rot_order = cmds.getAttr(f"{neck_mid_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
            neck_mid_ctrl, neck_mid_parent_grps = self.create_rig_control(
                control_base_name=neck_mid_proxy.get_name(),
                # curve_file_name="_pin_neg_y",  # previous control
                curve_file_name="_circle_pos_x",
                parent_obj=last_mid_parent_ctrl,
                extra_parent_groups=self._default_neck_suffix,  # neckBaseData group for automation
                match_obj=mid_jnt,
                rot_order=neck_mid_rot_order,
                shape_scale=_shape_scale_mid,
            )[:2]
            # -- driver
            self._add_driver_uuid_attr(
                target_driver=neck_mid_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=neck_mid_proxy,
            )
            # -- constraint
            core_cnstr.constraint_targets(source_driver=neck_mid_ctrl, target_driven=mid_jnt)
            # -- attributes
            core_attr.hide_lock_default_attrs(obj_list=neck_mid_ctrl, scale=True, visibility=True)

            neck_mid_auto_data_grps.append(neck_mid_parent_grps[1])
            neck_mid_ctrls.append(neck_mid_ctrl)
            last_mid_parent_ctrl = neck_mid_ctrl

        # head control -----------------------------------------------------------
        head_end_distance = core_math.dist_center_to_center(head_jnt, head_end_jnt)
        head_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.head_proxy.get_uuid())
        head_rot_order = cmds.getAttr(f"{head_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        head_ctrl, head_parent_groups, head_o_ctrl, head_data_grp = self.create_rig_control(
            control_base_name=self.head_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=last_mid_parent_ctrl,
            extra_parent_groups=self._default_neck_suffix,  # neckBaseData group for automation
            match_obj=head_jnt,
            add_offset_ctrl=True,
            shape_pos_offset=(head_end_distance * 1.1, 0, 0),  # Move Above Head
            rot_order=head_rot_order,
            shape_scale=head_scale * 0.6,
        )
        # -- driver
        self._add_driver_uuid_attr(
            target_driver=head_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.head_proxy,
        )
        self._add_driver_uuid_attr(
            target_driver=head_o_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.OFFSET,
            proxy_purpose=self.head_proxy,
        )
        # -- constraint
        core_cnstr.constraint_targets(source_driver=head_data_grp, target_driven=head_jnt)
        # -- attributes
        core_attr.hide_lock_default_attrs(obj_list=head_ctrl, scale=True, visibility=True)
        # -- follow setup - Rotation and Position
        core_attr.add_separator_attr(target_object=head_ctrl, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE)
        tools_rig_utils.create_follow_setup(control=head_ctrl, parent=neck_mid_jnt_list[-1])

        # build jaw setup if required
        if jaw_jnt and jaw_end_jnt:
            self.build_jaw_setup(jaw_jnt, jaw_end_jnt, parent_obj=head_data_grp)

        # build eyes setup if required
        if lt_eye_jnt and rt_eye_jnt:
            self.build_eyes_setup(lt_eye_jnt, rt_eye_jnt, parent_obj=head_data_grp, setup_scale=head_scale * 0.1)

        # Base neck rotate automation
        core_attr.add_separator_attr(
            target_object=neck_base_ctrl, attr_name=core_rigging.RiggingConstants.SEPARATOR_INFLUENCE
        )
        for index, (mid_ctrl, mid_proxy, mid_data_grp) in enumerate(
            zip(neck_mid_ctrls, self.neck_mid_proxies, neck_mid_auto_data_grps)
        ):
            attr_name = f"{mid_proxy.get_name()}Influence"
            # Create Attribute Long and Nice Names
            cmds.addAttr(
                neck_base_ctrl,
                longName=attr_name,
                attributeType="double",
                defaultValue=1,
                keyable=True,
                minValue=0,
                maxValue=1,
                # **nice_name_param,
            )

            # Create Influence Setup
            influence_multiply = core_node.create_node(
                node_type="multiplyDivide", name=f"{mid_proxy.get_name()}Influence_multiply"
            )
            cmds.connectAttr(f"{neck_base_ctrl}.rotate", f"{influence_multiply}.input1")
            core_attr.connect_attr(
                source_attr=f"{neck_base_ctrl}.{attr_name}",
                target_attr_list=[
                    f"{influence_multiply}.input2X",
                    f"{influence_multiply}.input2Y",
                    f"{influence_multiply}.input2Z",
                ],
            )

            cmds.connectAttr(f"{influence_multiply}.output", f"{mid_data_grp}.rotate")

            # zero controls rotations
            cmds.rotate(0, 0, 0, mid_ctrl, a=True)

        # head automation
        head_rot_attr = core_attr.add_attr(
            obj_list=neck_base_ctrl,
            minimum=0,
            maximum=1,
            attributes=f"{self.head_proxy.get_name()}Influence",
            default=0,
        )[0]

        influence_multiply = core_node.create_node(
            node_type="multiplyDivide", name=f"{self.head_proxy.get_name()}Influence_multiply"
        )
        cmds.connectAttr(f"{neck_base_ctrl}.rotate", f"{influence_multiply}.input1")
        core_attr.connect_attr(
            source_attr=head_rot_attr,
            target_attr_list=[
                f"{influence_multiply}.input2X",
                f"{influence_multiply}.input2Y",
                f"{influence_multiply}.input2Z",
            ],
        )
        cmds.connectAttr(f"{influence_multiply}.output", f"{head_parent_groups[1]}.rotate")

        # zero control rotations
        cmds.rotate(0, 0, 0, head_ctrl, a=True)

        # children drivers
        self.module_children_drivers = [neck_base_parent_grps[0]]

    def _delete_unbound_joints(self):
        """
        Deletes joints that are usually not bound to the mesh. In this case the toe joint.
        """
        if self.delete_head_jaw_bind_jnt:
            head_end_jnt = tools_rig_utils.find_joint_from_uuid(self.head_end_proxy.get_uuid())
            jaw_end_jnt = tools_rig_utils.find_joint_from_uuid(self.jaw_end_proxy.get_uuid())
            if head_end_jnt:
                cmds.delete(head_end_jnt)
            if jaw_end_jnt:
                cmds.delete(jaw_end_jnt)

    # ------------------------------------------- Extra Module Setters -------------------------------------------
    def set_jaw_build_status(self, status=True):
        """
        Set Jaw and Jaw end status.

        Args:
            status (bool): If True, it gets built, otherwise it's ignored.
        """
        self.build_jaw = status

    def set_eyes_build_status(self, status=True):
        """
        Set Left Eye and Right Eye proxies build status.

        Args:
            status (bool): If True, it gets built, otherwise it's ignored.
        """
        self.build_eyes = status

    def set_post_delete_head_jaw_bind_joints(self, delete_joint):
        """
        Sets a variable to determine if the head end and jaw end joints should be deleted or not
        Args:
            delete_joint (bool): If True, the head end and jaw end joints will be deleted after the skeleton and
                                 control rig are created.
        """
        if not isinstance(delete_joint, bool):
            logger.warning(f'Unable to set "post_delete_head_jaw_bind_joints". Incompatible data type provided.')
        self.delete_head_jaw_bind_jnt = delete_joint

    # ------------------------------------------- Extra Module Getters -------------------------------------------
    def get_joints(self):
        """
        Gets skeleton and joints

        Returns:
            skeleton_joints (list): all joints
            neck_base_jnt (string)
            neck_mid_jnt_list (list): neck mid joints
            head_jnt (string)
            head_end_jnt (string)
            jaw_jnt (str, optional): can be None
            jaw_end_jnt (str, optional): can be None
            lt_eye_jnt (string, optional): can be None
            rt_eye_jnt (string, optional): can be None
        """
        neck_base_jnt = tools_rig_utils.find_joint_from_uuid(self.neck_base_proxy.get_uuid())
        neck_mid_jnt_list = [tools_rig_utils.find_joint_from_uuid(prx.get_uuid()) for prx in self.neck_mid_proxies]
        head_jnt = tools_rig_utils.find_joint_from_uuid(self.head_proxy.get_uuid())
        head_end_jnt = tools_rig_utils.find_joint_from_uuid(self.head_end_proxy.get_uuid())

        skeleton_joints = [neck_base_jnt]
        skeleton_joints.extend(neck_mid_jnt_list)
        skeleton_joints.append(head_jnt)
        skeleton_joints.append(head_end_jnt)

        jaw_jnt = None
        jaw_end_jnt = None
        if self.jaw_proxy and self.jaw_end_proxy:
            jaw_jnt = tools_rig_utils.find_joint_from_uuid(self.jaw_proxy.get_uuid())
            jaw_end_jnt = tools_rig_utils.find_joint_from_uuid(self.jaw_end_proxy.get_uuid())
            skeleton_joints.append(jaw_jnt)
            skeleton_joints.append(jaw_end_jnt)

        lt_eye_jnt = None
        rt_eye_jnt = None
        if self.lt_eye_proxy and self.rt_eye_proxy:
            lt_eye_jnt = tools_rig_utils.find_joint_from_uuid(self.lt_eye_proxy.get_uuid())
            rt_eye_jnt = tools_rig_utils.find_joint_from_uuid(self.rt_eye_proxy.get_uuid())
            skeleton_joints.append(lt_eye_jnt)
            skeleton_joints.append(rt_eye_jnt)

        return (
            skeleton_joints,
            neck_base_jnt,
            neck_mid_jnt_list,
            head_jnt,
            head_end_jnt,
            jaw_jnt,
            jaw_end_jnt,
            lt_eye_jnt,
            rt_eye_jnt,
        )

    # --------------------------------------------------- Misc ---------------------------------------------------
    def build_skeleton_joints(self, **kwargs):
        """
        Overrides the skeletal build phase, allowing joint names to be customized via proxy attributes.
        """
        super().build_skeleton_joints(use_naming_attrs=True)  # Allow name overrides

    def build_eyes_setup(self, lt_eye_jnt, rt_eye_jnt, parent_obj, setup_scale):
        """
        Builds eyes setup.

        Args:
            lt_eye_jnt (Node): left eye joint
            rt_eye_jnt (Node): right eye joint
            parent_obj (Node): parent object
            setup_scale (float): setup scale
        """
        pupillary_distance = core_math.dist_center_to_center(lt_eye_jnt, rt_eye_jnt)

        # temp locators to set world orientation
        temp_lt_eye_loc = cmds.spaceLocator(
            name=f"{self.prefix_eye_left}_{self.rt_eye_proxy.get_name()}_temp_loc)",
        )[0]
        core_trans.match_transform(source=lt_eye_jnt, target_list=temp_lt_eye_loc, rotate=False, scale=False)
        temp_rt_eye_loc = cmds.spaceLocator(
            name=f"{self.prefix_eye_right}_{self.rt_eye_proxy.get_name()}_temp_loc)",
        )[0]
        core_trans.match_transform(source=rt_eye_jnt, target_list=temp_rt_eye_loc, rotate=False, scale=False)

        # Main control
        lt_eye_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.lt_eye_proxy.get_uuid())
        lt_eye_rot_order = cmds.getAttr(f"{lt_eye_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        main_eye_ctrl, main_eye_parent_grps = self.create_rig_control(
            control_base_name="mainEye",
            curve_file_name="_peanut_pos_z",
            parent_obj=parent_obj,
            match_obj=temp_lt_eye_loc,
            shape_scale=setup_scale * 1.1,
            rot_order=lt_eye_rot_order,
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=main_eye_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.AIM,
            proxy_purpose="mainEye",
        )
        # -- attributes
        core_attr.hide_lock_default_attrs(obj_list=main_eye_ctrl, scale=True, visibility=True)
        cmds.setAttr(f"{main_eye_parent_grps[0]}.translateZ", 0)

        # Left eye
        lt_eye_ctrl = self.create_rig_control(
            control_base_name=self.rt_eye_proxy.get_name(),
            curve_file_name="_circle_pos_z",
            parent_obj=main_eye_ctrl,
            match_obj=temp_lt_eye_loc,
            shape_scale=setup_scale,
            rot_order=lt_eye_rot_order,
            color=core_color.ColorConstants.RigProxy.LEFT,
            overwrite_prefix=self.prefix_eye_left,
        )[0]
        # -- driver
        self._add_driver_uuid_attr(
            target_driver=lt_eye_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.AIM,
            proxy_purpose=self.lt_eye_proxy,
        )
        # -- attributes
        core_attr.hide_lock_default_attrs(obj_list=lt_eye_ctrl, rotate=True, scale=True, visibility=True)

        # Right eye
        rt_eye_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.rt_eye_proxy.get_uuid())
        rt_eye_rot_order = cmds.getAttr(f"{rt_eye_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        rt_eye_ctrl = self.create_rig_control(
            control_base_name=self.rt_eye_proxy.get_name(),
            curve_file_name="_circle_pos_z",
            parent_obj=main_eye_ctrl,
            match_obj=temp_rt_eye_loc,
            shape_scale=setup_scale,
            rot_order=rt_eye_rot_order,
            color=core_color.ColorConstants.RigProxy.RIGHT,
            overwrite_prefix=self.prefix_eye_right,
        )[0]
        # -- driver
        self._add_driver_uuid_attr(
            target_driver=rt_eye_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.AIM,
            proxy_purpose=self.rt_eye_proxy,
        )
        # -- attributes
        core_attr.hide_lock_default_attrs(obj_list=rt_eye_ctrl, rotate=True, scale=True, visibility=True)

        # delete temp locators
        cmds.delete(temp_lt_eye_loc, temp_rt_eye_loc)

        # move eyes setup forward
        cmds.move(0, 0, pupillary_distance * 3, main_eye_parent_grps[0], r=True)

        # vectors
        lt_eye_up_vec = cmds.spaceLocator(name=f"{self.lt_eye_proxy.get_name()}_upVec")[0]
        rt_eye_up_vec = cmds.spaceLocator(name=f"{self.rt_eye_proxy.get_name()}_upVec")[0]
        core_trans.match_transform(source=lt_eye_jnt, target_list=lt_eye_up_vec)
        core_trans.match_transform(source=rt_eye_jnt, target_list=rt_eye_up_vec)
        cmds.move(setup_scale, lt_eye_up_vec, y=True, relative=True, objectSpace=True)
        cmds.move(setup_scale, rt_eye_up_vec, y=True, relative=True, objectSpace=True)
        core_attr.set_attr(
            obj_list=[lt_eye_up_vec, rt_eye_up_vec],
            attr_list=["localScaleX", "localScaleY", "localScaleZ"],
            value=setup_scale * 0.1,
        )
        core_attr.set_attr(obj_list=[lt_eye_up_vec, rt_eye_up_vec], attr_list="v", value=False)
        lt_eye_up_vec, rt_eye_up_vec = core_hrchy.parent(
            source_objects=[lt_eye_up_vec, rt_eye_up_vec], target_parent=parent_obj
        )

        core_cnstr.constraint_targets(
            source_driver=lt_eye_ctrl,
            target_driven=lt_eye_jnt,
            constraint_type=core_cnstr.ConstraintTypes.AIM,
            upVector=(0, 1, 0),
            worldUpType="object",
            worldUpObject=lt_eye_up_vec,
        )
        core_cnstr.constraint_targets(
            source_driver=rt_eye_ctrl,
            target_driven=rt_eye_jnt,
            constraint_type=core_cnstr.ConstraintTypes.AIM,
            upVector=(0, 1, 0),
            worldUpType="object",
            worldUpObject=rt_eye_up_vec,
        )

        # eye lines
        tools_rig_utils.create_control_visualization_line(lt_eye_ctrl, lt_eye_jnt)
        tools_rig_utils.create_control_visualization_line(rt_eye_ctrl, rt_eye_jnt)

    def build_jaw_setup(self, jaw_jnt, jaw_end_jnt, parent_obj):
        """
        Builds the jaw rig control setup.

        Args:
            jaw_jnt (str): The joint name of the jaw root.
            jaw_end_jnt (str): The joint name of the jaw end.
            parent_obj (str): The parent object to attach the jaw control under.
        """
        jaw_end_distance = core_math.dist_center_to_center(jaw_jnt, jaw_end_jnt)
        jaw_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.jaw_proxy.get_uuid())
        jaw_rot_order = cmds.getAttr(f"{jaw_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        jaw_ctrl = self.create_rig_control(
            control_base_name=self.jaw_proxy.get_name(),
            curve_file_name="_concave_crescent_neg_y",
            parent_obj=parent_obj,
            match_obj=jaw_jnt,
            rot_order=jaw_rot_order,
            shape_pos_offset=(-jaw_end_distance * 0.6, jaw_end_distance * 1.1, 0),
            shape_rot_offset=None,
            shape_scale=jaw_end_distance * 0.4,
        )[0]
        # -- driver
        self._add_driver_uuid_attr(
            target_driver=jaw_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.jaw_proxy,
        )
        # -- constraint
        core_cnstr.constraint_targets(source_driver=jaw_ctrl, target_driven=jaw_jnt)
        # -- attributes
        core_attr.hide_lock_default_attrs(obj_list=jaw_ctrl, translate=True, scale=True, visibility=True)


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)
    import gt.core.session as core_session

    core_session.remove_modules_startswith("gt.tools.auto_rigger.module")
    core_session.remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    import gt.tools.auto_rigger.modules.module_spine as tools_rig_mod_spine

    # import gt.tools.auto_rigger.modules.module_head as tools_rig_mod_head
    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils
    import importlib

    # importlib.reload(tools_rig_mod_head)
    importlib.reload(tools_rig_mod_spine)
    importlib.reload(tools_rig_utils)
    importlib.reload(tools_rig_fmr)

    a_spine = tools_rig_mod_spine.ModuleSpine()
    a_head = ModuleHead()
    a_head.set_mid_neck_num(1)
    # a_head.set_mid_neck_num(4)
    spine_chest_uuid = a_spine.chest_proxy.get_uuid()
    a_head.set_parent_uuid(spine_chest_uuid)

    # skip jaw and eyes (elements built by default)
    # a_head.set_jaw_build_status(False)
    # a_head.set_eyes_build_status(False)
    # a_head.set_post_delete_head_jaw_bind_joints(False)

    # build
    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_spine)
    a_project.add_to_modules(a_head)
    # a_head.set_jaw_status(False)
    # a_head.set_jaw_status(False)
    a_project.build_proxy()
    # a_project.build_skeleton()
    a_project.build_rig()

    # rebuild
    # a_project.read_data_from_scene()
    # a_project_as_dict = a_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = tools_rig_fmr.RigProject()
    # a_project2.read_data_from_dict(a_project_as_dict)
    # a_project2.build_proxy()
    # a_project2.build_rig()

    # # Show all
    cmds.viewFit(all=True)
