"""
Auto Rigger Module - Quadruped Spine
"""

import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.surface as core_surface
import gt.core.transform as core_trans
import gt.core.rigging as core_rigging
import gt.core.constraint as core_cnstr
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.core.color as core_color
import gt.core.attr as core_attr
import gt.core.math as core_math
import gt.core.node as core_node
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleQuadSpine(tools_rig_frm.ModuleGeneric):
    __version__ = "0.0.1"
    icon = ui_res_lib.Icon.rigger_module_quad_spine
    allow_parenting = True
    allow_multiple = True

    def __init__(
        self,
        name="Quad Spine",
        prefix=core_naming.NamingConstants.Prefix.CENTER,
        suffix=None,
        rot_order=0,
        divisions=5,
        num_ctrls=1,
        ik_ctrl_shapes="_square_pos_x",
        fk_ctrl_shapes="_circle_pos_x",
        cable_ctrls=False,
        rotate_ribbon=False,
    ):
        """
        A rig module representing a quadruped spine setup using a ribbon as a base.

        Args:
            name (str): Name of the module instance.
            prefix (str): Naming prefix for controls.
            suffix (str or None): Optional naming suffix.
            rot_order (int): Rotation order applied to proxies (default is 0).
            divisions (int): Number of spine divisions (default is 5).
            num_ctrls (int): Number of main controls (default is 1).
            ik_ctrl_shapes (str): Shape name for IK controls.
            fk_ctrl_shapes (str): Shape name for FK controls.
            cable_ctrls (bool): Whether cable controls are enabled.
            rotate_ribbon (bool): Whether the ribbon rotates.

        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.setup_name = "spine"
        self.hips_name = f"hips"
        self.chest_name = f"chest"
        self.direction_name = f"direction"
        self.rot_order = rot_order
        self.divisions = divisions
        self.division_last_num = divisions  # Refreshed after every rig or proxy build
        self.num_ctrls = num_ctrls
        self.ik_ctrl_shapes = ik_ctrl_shapes
        self.fk_ctrl_shapes = fk_ctrl_shapes
        self._dropoff_rate = 2
        self.middle_proxies_reset = True
        self.cable_ctrls = cable_ctrls
        self.rotate_ribbon = rotate_ribbon
        self.span_multiplier = 1

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 1, 0), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)

        self.base_proxy = tools_rig_frm.Proxy(name=self.hips_name)
        pos_spine_base = core_trans.Vector3(x=0, y=60, z=-40)
        self.base_proxy.set_initial_position(xyz=pos_spine_base)
        self.base_proxy.set_locator_scale(scale=2)
        self.base_proxy.set_meta_purpose(value=self.hips_name)
        self.base_proxy.set_rotation_order(rotation_order=self.rot_order)
        self.base_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )

        self.end_proxy = tools_rig_frm.Proxy(name=self.chest_name)
        pos_spine_end = core_trans.Vector3(x=0, y=60, z=40)
        self.end_proxy.set_initial_position(xyz=pos_spine_end)
        self.end_proxy.set_locator_scale(scale=1.5)
        self.end_proxy.add_line_parent(self.base_proxy)
        self.end_proxy.set_parent_uuid(self.base_proxy.get_uuid())
        self.end_proxy.set_meta_purpose(value=self.chest_name)
        self.end_proxy.set_rotation_order(rotation_order=self.rot_order)
        self.end_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )

        # In-betweens
        self.mid_proxies = []
        self.set_divisions_num(divisions=self.divisions)

    def set_divisions_num(self, divisions):
        """
        Set a new number of spine proxies. These are the proxies in-between the spine base proxy and spine end proxy
        Args:
            divisions (int): New number of joints to exist in-between base and end.
                             Minimum is zero (0) - No negative numbers.
        """
        spine_len = len(self.mid_proxies)
        # Same as current, skip
        if spine_len == divisions:
            return

        # New number higher than current - Add more proxies
        if spine_len < divisions:
            # Determine Initial Parent
            if self.mid_proxies:
                _parent_uuid = self.mid_proxies[-1].get_uuid()
            else:
                _parent_uuid = self.base_proxy.get_uuid()
            # Create new spines
            for num in range(spine_len, divisions):
                new_spine_name = f"{self.setup_name + str(num + 1).zfill(2)}"
                new_spine = tools_rig_frm.Proxy(name=new_spine_name)
                new_spine.set_locator_scale(scale=1)
                new_spine.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
                new_spine.set_meta_purpose(value=new_spine_name)
                new_spine.add_line_parent(line_parent=_parent_uuid)
                new_spine.set_parent_uuid(uuid=_parent_uuid)
                new_spine.add_driver_type(
                    driver_type=[
                        tools_rig_const.RiggerDriverTypes.GENERIC,
                        tools_rig_const.RiggerDriverTypes.FK,
                        tools_rig_const.RiggerDriverTypes.IK,
                    ]
                )
                new_spine.set_rotation_order(rotation_order=self.rot_order)
                _parent_uuid = new_spine.get_uuid()
                self.mid_proxies.append(new_spine)
        # New number lower than current - Remove unnecessary proxies
        elif len(self.mid_proxies) > divisions:
            self.mid_proxies = self.mid_proxies[:divisions]  # Truncate the list

        if self.mid_proxies:
            self.end_proxy.add_line_parent(line_parent=self.mid_proxies[-1].get_uuid())
        else:
            self.end_proxy.add_line_parent(line_parent=self.base_proxy.get_uuid())

        self.refresh_proxies_list()

    def set_proxies_name(self, setup_name, base, end):
        """
        Sets the names for the start, mid and end proxies
        Args:
            setup_name (str): New setup name, used for the middle joints and other components.
            base (str): New name used for the base control.  e.g. "hips"
            end (str): Name used for the end control. e.g. "chest"
        """
        self.setup_name = setup_name
        self.base_proxy.set_name(base)
        self.end_proxy.set_name(end)
        for proxy in self.mid_proxies:
            proxy.set_name(f"{setup_name+ str(self.mid_proxies.index(proxy) + 1).zfill(2)}")
        self.refresh_proxies_list()

    def refresh_proxies_list(self):
        """
        Refreshes the main proxies list used by the module during build (update in case objects were updated)
        """
        self.proxies = [self.base_proxy]
        self.proxies.extend(self.mid_proxies)
        self.proxies.append(self.end_proxy)

    def set_rot_order(self, rot_order):
        """
        Sets the rotation order for all spine proxies in the module.

        Args:
            rot_order (int): The rotation order to apply (typically 0-5, corresponding
                to specific rotation order enums).
        """
        all_spine_proxies = [self.base_proxy] + self.mid_proxies + [self.end_proxy]
        for proxy in all_spine_proxies:
            proxy.set_rotation_order(rot_order)
        self.refresh_proxies_list()

    def get_module_as_dict(self, **kwargs):
        """
        Overwrite to remove offset data from the export
        Args:
            kwargs: Key arguments, not used for anything in this case.
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

    def read_data_from_dict(self, module_dict):
        """
        Reads the data from a module dictionary and updates the values of this module to match it.
        This is an override to trigger set ribbon number and refresh proxies after reading the data.
        Args:
            module_dict (dict): A dictionary describing the module data. e.g. {"name": "generic"}
        Returns:
            ModuleGeneric: This module (self)
        """
        if isinstance(module_dict, dict):
            _spine_number = module_dict.get("divisions", self.divisions)
            self.set_divisions_num(divisions=_spine_number)
            self.refresh_proxies_list()
        return super().read_data_from_dict(module_dict=module_dict)

        # --------------------------------------------------- Misc ---------------------------------------------------

    def is_valid(self):
        """
        Checks if the rig module is valid. This means, it's ready to be used and no issues were detected.
        Returns
            bool: True if valid, False otherwise
        """
        is_valid = super().is_valid()  # Passthrough
        return is_valid

    def align_proxies_to_joints(self):
        """
        Aligns the proxies to the joints transformations.
        """
        spine_base_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.base_proxy.get_uuid())
        spine_end_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.end_proxy.get_uuid())
        middle_spine_proxy_list = [tools_rig_utils.find_proxy_from_uuid(prx.get_uuid()) for prx in self.mid_proxies]
        spine_base_jnt = tools_rig_utils.find_joint_from_uuid(self.base_proxy.get_uuid())
        spine_end_jnt = tools_rig_utils.find_joint_from_uuid(self.end_proxy.get_uuid())
        middle_spine_jnt_list = [tools_rig_utils.find_joint_from_uuid(prx.get_uuid()) for prx in self.mid_proxies]

        # order: base, end, middle ones
        core_trans.match_translate(source=spine_base_jnt, target_list=spine_base_proxy_item)
        core_trans.match_translate(source=spine_end_jnt, target_list=spine_end_proxy_item)
        [
            core_trans.match_translate(source=jnt, target_list=prx)
            for prx, jnt in zip(middle_spine_proxy_list, middle_spine_jnt_list)
        ]

    def build_proxy(self, **kwargs):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of tools_rig_frm.ProxyData objects. These objects describe the created proxy elements.
        """
        if self.parent_uuid:
            if self.base_proxy:
                self.base_proxy.set_parent_uuid(self.parent_uuid)
        self.end_proxy.set_setup_driver_uuid(self.base_proxy.get_uuid())
        self.end_proxy.set_parent_uuid(self.base_proxy.get_uuid())
        if self.mid_proxies:
            prx_driver = self.base_proxy
            for prx in self.mid_proxies:
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
        spine_base = tools_rig_utils.find_proxy_from_uuid(self.base_proxy.get_uuid())
        spine_end = tools_rig_utils.find_proxy_from_uuid(self.end_proxy.get_uuid())
        reset_middle_transforms = self.middle_proxies_reset and self.division_last_num != self.divisions
        self.division_last_num = self.divisions  # Refresh last division number
        proxies = []
        for proxy in self.mid_proxies:
            proxy_node = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
            proxies.append(proxy_node)
        self.base_proxy.apply_offset_transform()
        self.end_proxy.apply_offset_transform()

        proxy_offsets = []
        for proxy in proxies:
            offset = tools_rig_utils.get_proxy_offset(proxy)
            proxy_offsets.append(offset)
            if reset_middle_transforms:
                cmds.move(0, 0, 0, offset, a=True)
                cmds.rotate(0, 0, 0, offset, a=True)
                cmds.move(0, 0, 0, proxy, a=True)
                cmds.rotate(0, 0, 0, proxy, a=True)
        core_cnstr.equidistant_constraints(start=spine_base, end=spine_end, target_list=proxy_offsets)

        self.base_proxy.apply_transforms()
        self.end_proxy.apply_transforms()
        if not reset_middle_transforms:
            for spine in self.mid_proxies:
                spine.apply_transforms()
        cmds.select(clear=True)

        # Set proxy parent for the skeleton hierarchy
        prx_parent = self.base_proxy
        for prx in self.mid_proxies:
            prx.set_parent_uuid(prx_parent.get_uuid())
            prx_parent = prx
        self.end_proxy.set_parent_uuid(self.mid_proxies[-1].get_uuid())

    def build_skeleton_hierarchy(self):
        """
        Runs skeletal hierarchy phase (post skeleton). Joints are parented and oriented during this step.
        Happens after the "build_skeleton_joints" function in a project.
        """
        self.end_proxy.set_parent_uuid(uuid=self.end_proxy.get_meta_parent_uuid())
        super().build_skeleton_hierarchy()  # Passthrough
        self.end_proxy.clear_parent_uuid()

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        """Builds the quad spine setup"""
        _ik_suffix = core_naming.NamingConstants.Description.IK.upper()

        # Het Joints
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        spine_base_jnt = tools_rig_utils.find_joint_from_uuid(self.base_proxy.get_uuid())
        spine_mid_jnts = [tools_rig_utils.find_joint_from_uuid(prx.get_uuid()) for prx in self.mid_proxies]
        spine_end_jnt = tools_rig_utils.find_joint_from_uuid(self.end_proxy.get_uuid())
        module_parent_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())
        spine_jnt_list = [spine_base_jnt] + spine_mid_jnts + [spine_end_jnt]
        # Get Formatted Prefix
        _prefix = ""
        if self.prefix:
            _prefix = f"{self.prefix}_"

        # Setup groups
        joint_automation_group = tools_rig_utils.find_or_create_joint_automation_group()
        spine_automation_group = tools_rig_utils.get_automation_group("spineAutomation")
        core_hrchy.parent(source_objects=module_parent_jnt, target_parent=joint_automation_group)
        cmds.setAttr(f"{spine_automation_group}.visibility", 0)
        cmds.setAttr(f"{joint_automation_group}.visibility", 0)

        # Spine Ribbon -------------------------
        spine_grp = f"{_prefix}{self.setup_name}_{core_naming.NamingConstants.Suffix.GRP}"
        spine_grp = core_hrchy.create_group(name=spine_grp)
        spine_grp = core_hrchy.parent(source_objects=spine_grp, target_parent=spine_automation_group)[0]
        cmds.setAttr(f"{spine_grp}.inheritsTransform", 0)  # Ignore Hierarchy Transform

        spine_name = self._assemble_ctrl_name(
            name=self.setup_name, overwrite_suffix=core_naming.NamingConstants.Suffix.SUR
        )
        spine_sur = core_surface.create_surface_from_object_list(
            obj_list=spine_jnt_list, surface_name=spine_name, degree=1
        )

        spine_sur = core_node.Node(spine_sur)

        if self.rotate_ribbon:
            num_spans_v = cmds.getAttr(f"{spine_sur}.spansV") + 2
            all_spine_cvs = f"{spine_sur}.cv[0:1][0:{num_spans_v - 1}]"
            cmds.select(all_spine_cvs)
            cmds.rotate(0, 0, 90, all_spine_cvs, cs=True, r=True)

        core_surface.multiply_surface_spans(
            input_surface=spine_sur,
            u_degree=1,
            v_degree=3,
            v_multiplier=self.span_multiplier,
        )
        core_hrchy.parent(source_objects=spine_sur, target_parent=spine_grp)

        # Create Follicles
        follicle_transforms = []
        fk_joints = []
        for index, joint in enumerate(spine_jnt_list):
            joint_pos = cmds.xform(joint, query=True, translation=True, worldSpace=True)
            u_pos, v_pos = core_surface.get_closest_uv_point(surface=spine_sur, xyz_pos=joint_pos)
            v_pos_normalized = v_pos / (len(spine_jnt_list) - 1)
            fol_trans, fol_shape = core_surface.create_follicle(
                input_surface=spine_sur,
                uv_position=(0.5, v_pos_normalized),
                name=f"{_prefix}{self.setup_name}Follicle_{(index + 1):02d}",
            )
            follicle_transforms.append(fol_trans)
            jnt = core_rigging.duplicate_joint_for_automation(joint, suffix="fk", parent=fol_trans)
            core_cnstr.constraint_targets(jnt, joint)
            fk_joints.append(jnt)

        core_hrchy.parent(source_objects=follicle_transforms, target_parent=spine_grp)
        # Set joints colors
        core_color.set_color_viewport(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigJoint.GENERAL)

        # Get chain scale
        spine_scale = core_math.dist_center_to_center(spine_base_jnt, spine_end_jnt)

        # Controls ----------------------------------------------------------------------------------------

        spine_base_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.base_proxy.get_uuid())
        spine_rotation_order = cmds.getAttr(f"{spine_base_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        direction_ctrl, direction_parent_groups = self.create_rig_control(
            control_base_name=f"{self.direction_name}",
            curve_file_name="arrow_direction_two_sides_small",
            parent_obj=global_offset_ctrl,
            match_obj_pos=spine_base_jnt,  # Keep world orients
            add_offset_ctrl=False,
            rot_order=spine_rotation_order,
            shape_rot_offset=(90, 0, 90),
            shape_pos_offset=(spine_scale * 0.6, 0, 0),
            shape_scale=spine_scale * 0.15,
            color=core_color.ColorConstants.RGB.YELLOW,
        )[:2]
        core_attr.hide_lock_default_attrs(obj_list=direction_ctrl, scale=True, visibility=True)

        # Rotate Shape
        base_rot = cmds.xform(spine_base_jnt, query=True, rotation=True, worldSpace=True)
        core_trans.rotate_shapes(direction_ctrl, offset=base_rot)

        # Visibility
        core_attr.add_separator_attr(direction_ctrl, attr_name="ctrlVisibility")
        core_attr.add_attr(obj_list=direction_ctrl, attributes="fkVisibility", attr_type="bool", default=0)
        core_attr.add_attr(obj_list=direction_ctrl, attributes="ikVisibility", attr_type="bool", default=1)

        # General Groups
        bind_grp = f"{_prefix}{self.setup_name}_bind_{core_naming.NamingConstants.Suffix.GRP}"
        bind_grp = core_hrchy.create_group(name=bind_grp)
        bind_grp = core_hrchy.parent(source_objects=bind_grp, target_parent=spine_automation_group)[0]
        cmds.setAttr(f"{bind_grp}.visibility", 0)

        # IK Controls
        bind_jnts = []
        spine_ik_ctrls = []
        spine_ik_ctrls_offsets = []

        spine_base_ik_ctrl, spine_base_ik_parent_groups = self.create_rig_control(
            control_base_name=f"{self.hips_name}_{_ik_suffix}",
            curve_file_name=self.ik_ctrl_shapes,
            parent_obj=direction_ctrl,
            match_obj=spine_base_jnt,
            add_offset_ctrl=False,
            rot_order=spine_rotation_order,
            shape_scale=spine_scale * 0.4,
            color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=spine_base_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.base_proxy,
        )
        spine_ik_ctrls.append(spine_base_ik_ctrl)
        spine_ik_ctrls_offsets.append(spine_base_ik_parent_groups[0])
        core_attr.hide_lock_default_attrs(spine_base_ik_ctrl, scale=True, visibility=True)

        for index in range(self.num_ctrls):
            fol_trans, fol_shape = core_surface.create_follicle(
                input_surface=spine_sur,
                uv_position=(0.5, (1 / (self.num_ctrls + 1)) * (index + 1)),
                name=f"{_prefix}{self.setup_name}Follicle_{(index + 1):02d}",
            )
            spine_ik_ctrl, spine_ik_parent_groups = self.create_rig_control(
                control_base_name=f"{self.setup_name}{(index + 1):02d}_{_ik_suffix}",
                curve_file_name=self.ik_ctrl_shapes,
                parent_obj=direction_ctrl,
                match_obj=fol_trans,
                add_offset_ctrl=False,
                rot_order=spine_rotation_order,
                shape_scale=spine_scale * 0.4,
                color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
            )[:2]

            # Orient Control Offset
            cmds.delete(fol_trans)
            cmds.setAttr(f"{spine_ik_parent_groups[0]}.rotate", 0, 0, 0, type="double3")

            self._add_driver_uuid_attr(
                target_driver=spine_ik_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.IK,
                proxy_purpose=f"{self.setup_name}{(index + 1):02d}",
            )
            core_attr.hide_lock_default_attrs(spine_ik_ctrl, scale=True, visibility=True)
            spine_ik_ctrls.append(spine_ik_ctrl)
            spine_ik_ctrls_offsets.append(spine_ik_parent_groups[0])

        # Align IK mid controls
        start_alignment_obj = spine_ik_ctrls_offsets[0]
        for index, offset_grp in enumerate(spine_ik_ctrls_offsets):
            if index == 0:
                continue
            if len(spine_ik_ctrls_offsets) - 1 == index:
                end_alignment_obj = spine_end_jnt
            else:
                end_alignment_obj = spine_ik_ctrls_offsets[index + 1]
            core_trans.align_object_to_vector(
                start_obj=start_alignment_obj,
                end_obj=end_alignment_obj,
                target_obj=offset_grp,
                aim_axis="x",
            )
            start_alignment_obj = offset_grp
            if self.num_ctrls == self.divisions:  # Snap mid-controls to mid-proxies
                mid_proxy = tools_rig_utils.find_proxy_from_uuid(self.proxies[index].get_uuid())
                core_trans.match_translate(source=mid_proxy, target_list=offset_grp)
                core_trans.match_rotate(source=fk_joints[index], target_list=offset_grp)

        spine_end_ik_ctrl, spine_end_ik_parent_groups = self.create_rig_control(
            control_base_name=f"{self.chest_name}_{_ik_suffix}",
            curve_file_name=self.ik_ctrl_shapes,
            parent_obj=direction_ctrl,
            match_obj=spine_end_jnt,
            add_offset_ctrl=False,
            rot_order=spine_rotation_order,
            shape_scale=spine_scale * 0.4,
            color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=spine_end_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.end_proxy,
        )
        core_attr.hide_lock_default_attrs(spine_end_ik_ctrl, scale=True, visibility=True)
        spine_ik_ctrls.append(spine_end_ik_ctrl)
        spine_ik_ctrls_offsets.append(spine_end_ik_parent_groups[0])

        for offset in spine_ik_ctrls_offsets:
            cmds.connectAttr(f"{direction_ctrl}.ikVisibility", f"{offset}.visibility")

        fk_ctrls = []
        fk_offsets = []
        # Cable Controls ---------------------------------------------------------------
        if self.cable_ctrls:
            core_attr.add_separator_attr(direction_ctrl, attr_name="cable")
            cmds.setAttr(f"{direction_ctrl}.cable", lock=True)
            core_attr.add_attr(
                obj_list=direction_ctrl,
                attributes=["startInfluence", "endInfluence"],
                attr_type="float",
                minimum=0,
                maximum=10,
                default=1,
            )

            # FK Controls
            spine_start_end_ik_ctrls = [spine_base_ik_ctrl, spine_end_ik_ctrl]
            spine_start_end_ik_offsets = [spine_base_ik_parent_groups[0], spine_end_ik_parent_groups[0]]
            _start_end_fk_ctrls = []
            _start_end_fk_offsets = []
            for ik_ctrl, ik_offset in zip(spine_start_end_ik_ctrls, spine_start_end_ik_offsets):
                ctrl_name = ik_ctrl.get_short_name().split(f"_{_ik_suffix}")[0]
                spine_fk_ctrl, spine_fk_parent_groups = self.create_rig_control(
                    control_base_name=f"{ctrl_name}",
                    overwrite_prefix="",
                    curve_file_name=self.fk_ctrl_shapes,
                    parent_obj=direction_ctrl,
                    match_obj=ik_ctrl,
                    add_offset_ctrl=False,
                    rot_order=spine_rotation_order,
                    shape_scale=spine_scale * 0.2,
                    color=core_color.ColorConstants.RGB.BLUE_SKY,
                )[:2]
                purpose = cmds.getAttr(f"{ik_ctrl}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}").split("-")[-1]
                self._add_driver_uuid_attr(
                    target_driver=spine_fk_ctrl,
                    driver_type=tools_rig_const.RiggerDriverTypes.FK,
                    proxy_purpose=purpose,
                )
                core_attr.hide_lock_default_attrs(spine_fk_ctrl, scale=True, visibility=True)
                cmds.parentConstraint(spine_fk_ctrl, ik_offset)
                _start_end_fk_ctrls.append(spine_fk_ctrl)
                _start_end_fk_offsets.append(spine_fk_parent_groups)
            mid_fol_trans, mid_fol_shape = core_surface.create_follicle(
                input_surface=spine_sur,
                uv_position=(0.5, 0.5),
                name=f"{_prefix}{self.setup_name}Follicle_mid_ctrl",
            )
            spine_mid_fk_ctrl, spine_mid_fk_parent_groups = self.create_rig_control(
                control_base_name=f"{self.setup_name}Mid",
                curve_file_name=self.fk_ctrl_shapes,
                parent_obj=direction_ctrl,
                match_obj=mid_fol_trans,
                add_offset_ctrl=False,
                rot_order=spine_rotation_order,
                shape_scale=spine_scale * 0.2,
                color=core_color.ColorConstants.RGB.BLUE_SKY,
            )[:2]
            cmds.delete(mid_fol_trans)
            cmds.setAttr(f"{spine_mid_fk_parent_groups[0]}.rotate", 0, 0, 0, type="double3")
            self._add_driver_uuid_attr(
                target_driver=spine_mid_fk_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=f"{self.setup_name}midFK",
            )
            if self.num_ctrls % 2 == 0:  # Even
                middle_of_list = int(len(spine_ik_ctrls) / 2)
                even_list = True
            else:  # Odd
                middle_of_list = int(((len(spine_ik_ctrls) - 1) / 2) + 1)
                even_list = False
            for ctrl in spine_ik_ctrls[1 : middle_of_list - 1]:
                prev_ctrl = spine_ik_ctrls[spine_ik_ctrls.index(ctrl) - 1]
                influence_constraint = cmds.parentConstraint(
                    prev_ctrl, spine_mid_fk_ctrl, spine_ik_ctrls_offsets[spine_ik_ctrls.index(ctrl)], mo=True
                )[0]
                cmds.connectAttr(f"{direction_ctrl}.startInfluence", f"{influence_constraint}.w0")
            if even_list:
                upper_mid_list = spine_ik_ctrls[middle_of_list + 1 : -1]
            else:
                upper_mid_list = spine_ik_ctrls[middle_of_list:-1]
            for ctrl in upper_mid_list:
                post_ctrl = spine_ik_ctrls[spine_ik_ctrls.index(ctrl) + 1]
                influence_constraint = cmds.parentConstraint(
                    spine_mid_fk_ctrl, post_ctrl, spine_ik_ctrls_offsets[spine_ik_ctrls.index(ctrl)], mo=True
                )[0]
                cmds.connectAttr(f"{direction_ctrl}.endInfluence", f"{influence_constraint}.w1")
            if even_list:
                for ctrl in spine_ik_ctrls[middle_of_list - 1 : middle_of_list + 1]:
                    cmds.parentConstraint(
                        spine_mid_fk_ctrl, spine_ik_ctrls_offsets[spine_ik_ctrls.index(ctrl)], mo=True
                    )
            else:
                cmds.parentConstraint(
                    spine_mid_fk_ctrl,
                    spine_ik_ctrls_offsets[spine_ik_ctrls.index(spine_ik_ctrls[middle_of_list - 1])],
                    mo=True,
                )
            # Append Controls For Later
            fk_ctrls.append(_start_end_fk_ctrls[0])
            fk_ctrls.append(spine_mid_fk_ctrl)
            fk_ctrls.append(_start_end_fk_ctrls[-1])
            fk_offsets.append(_start_end_fk_offsets[0])
            fk_offsets.append(spine_mid_fk_parent_groups[0])
            fk_offsets.append(_start_end_fk_offsets[-1])

        # Bind Joints
        for ctrl in spine_ik_ctrls:
            jnt_name = ctrl.get_short_name().split("_CTRL")[0]
            jnt_name = f"{jnt_name}_bind"
            bind_jnt = core_node.Node(cmds.joint(n=jnt_name))
            cmds.setAttr(f"{bind_jnt}.rotateOrder", spine_rotation_order)
            bind_jnts.append(bind_jnt)
            if spine_ik_ctrls.index(ctrl) == 0:
                cmds.parent(bind_jnt, bind_grp)
            cmds.parentConstraint(ctrl, bind_jnt)

        # Bind the surface
        num_joints = len(bind_jnts)
        num_segments = num_joints - 1
        nurbs_skin_cluster = cmds.skinCluster(
            bind_jnts,
            spine_sur,
            dropoffRate=self._dropoff_rate,
            maximumInfluences=self.divisions + 2,
            nurbsSamples=self.divisions * 4,
            bindMethod=0,  # Closest Distance
            name=f"{_prefix}{self.setup_name}SkinCluster",
        )[0]
        cmds.skinPercent(nurbs_skin_cluster, spine_sur, pruneWeights=0.2)

        # Get number of V CVs
        num_spans_v = cmds.getAttr(f"{spine_sur}.spansV") + 3
        for i in range(num_spans_v):
            cv = f"{spine_sur}.cv[0:1][{i}]"
            t = float(i) / (num_spans_v - 1)  # normalized 0-1

            # Determine which segment the CV is in
            segment_t = t * num_segments
            segment_idx = int(segment_t)

            if segment_idx >= num_segments:
                segment_idx = num_segments - 1
                local_t = 1.0
            else:
                local_t = segment_t - segment_idx  # position within this segment

            jnt_start = bind_jnts[segment_idx]
            jnt_end = bind_jnts[segment_idx + 1]

            weights = [(jnt_start, 1.0 - local_t), (jnt_end, local_t)]
            cmds.skinPercent(nurbs_skin_cluster, cv, transformValue=weights)

        # FK Controls
        if not self.cable_ctrls:
            fk_offsets = []
            # FK Controls
            fk_parent = direction_ctrl
            for ik_ctrl, ik_offset in zip(spine_ik_ctrls, spine_ik_ctrls_offsets):
                ctrl_name = ik_ctrl.get_short_name().split(f"_{_ik_suffix}")[0]
                ribbon_fk_ctrl, ribbon_fk_parent_groups = self.create_rig_control(
                    control_base_name=ctrl_name,
                    overwrite_prefix="",
                    curve_file_name=self.fk_ctrl_shapes,
                    parent_obj=fk_parent,
                    match_obj=ik_ctrl,
                    add_offset_ctrl=False,
                    rot_order=spine_rotation_order,
                    shape_scale=spine_scale * 0.2,
                    color=core_color.ColorConstants.RGB.BLUE_SKY,
                )[:2]
                purpose = cmds.getAttr(f"{ik_ctrl}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}").split("-")[-1]
                self._add_driver_uuid_attr(
                    target_driver=ribbon_fk_ctrl,
                    driver_type=tools_rig_const.RiggerDriverTypes.FK,
                    proxy_purpose=purpose,
                )
                core_attr.hide_lock_default_attrs(ribbon_fk_ctrl, scale=True, visibility=True)
                fk_parent = ribbon_fk_ctrl
                cmds.parentConstraint(ribbon_fk_ctrl, ik_offset)
                fk_ctrls.append(ribbon_fk_ctrl)
                fk_offsets.append(ribbon_fk_parent_groups[0])

        # Spine Blendshapes
        twist_spine = cmds.duplicate(spine_sur, n=f"{spine_sur.get_short_name()}_twist")
        sine_spine = cmds.duplicate(spine_sur, n=f"{spine_sur.get_short_name()}_wave")
        cmds.blendShape(
            twist_spine,
            sine_spine,
            spine_sur,
            n=f"{_prefix}{self.setup_name}Bs",
            w=[(0, 1), (1, 1)],
            foc=True,
            o="local",
        )
        twist_node = cmds.nonLinear(twist_spine, type="twist", n=f"{_prefix}{self.setup_name}Twist")
        sine_node = cmds.nonLinear(sine_spine, type="sine", n=f"{_prefix}{self.setup_name}Sine")
        cmds.parent(twist_node[1], sine_node[1], spine_grp)
        if not self.rotate_ribbon:
            cmds.setAttr(f"{sine_node[1]}.ry", 90)

        # Connect Attributes
        core_attr.add_separator_attr(direction_ctrl, attr_name="twist")
        cmds.setAttr(f"{direction_ctrl}.twist", lock=True)
        core_attr.add_attr(obj_list=direction_ctrl, attributes=["startAngle", "endAngle"], attr_type="float")
        core_attr.add_attr(
            obj_list=direction_ctrl,
            attributes="twistLowBound",
            attr_type="float",
            minimum=-10,
            maximum=0,
            default=-1,
        )
        core_attr.add_attr(
            obj_list=direction_ctrl,
            attributes="twistHighBound",
            attr_type="float",
            minimum=0,
            maximum=10,
            default=1,
        )
        for out_attr, in_attr in [
            ("startAngle", "startAngle"),
            ("endAngle", "endAngle"),
            ("twistLowBound", "lowBound"),
            ("twistHighBound", "highBound"),
        ]:
            cmds.connectAttr(f"{direction_ctrl}.{out_attr}", f"{twist_node[0]}.{in_attr}")
        core_attr.add_separator_attr(direction_ctrl, attr_name="sine")
        cmds.setAttr(f"{direction_ctrl}.sine", lock=True)
        core_attr.add_attr(obj_list=direction_ctrl, attributes="amplitude", attr_type="float", maximum=5, minimum=-5)
        core_attr.add_attr(
            obj_list=direction_ctrl, attributes="wavelength", attr_type="float", maximum=10, minimum=0.1, default=2
        )
        core_attr.add_attr(obj_list=direction_ctrl, attributes="offset", attr_type="float")
        core_attr.add_attr(obj_list=direction_ctrl, attributes="dropoff", attr_type="float", maximum=1, minimum=-1)
        core_attr.add_attr(
            obj_list=direction_ctrl,
            attributes="sineLowBound",
            attr_type="float",
            minimum=-10,
            maximum=0,
            default=-1,
        )
        core_attr.add_attr(
            obj_list=direction_ctrl, attributes="sineHighBound", attr_type="float", minimum=0, maximum=10, default=1
        )
        for out_attr, in_attr in [
            ("amplitude", "amplitude"),
            ("wavelength", "wavelength"),
            ("offset", "offset"),
            ("dropoff", "dropoff"),
            ("sineLowBound", "lowBound"),
            ("sineHighBound", "highBound"),
        ]:
            cmds.connectAttr(f"{direction_ctrl}.{out_attr}", f"{sine_node[0]}.{in_attr}")

        # Align Non-linear Handles
        core_trans.align_object_to_vector(
            start_obj=spine_base_jnt,
            end_obj=spine_end_jnt,
            target_obj=twist_node[1],
            aim_axis="y",
        )
        core_trans.align_object_to_vector(
            start_obj=spine_base_jnt,
            end_obj=spine_end_jnt,
            target_obj=sine_node[1],
            aim_axis="y",
        )

        # Setup One Control Spine
        if self.num_ctrls == 1:
            _start_ik, _mid_ik, _end_ik = spine_ik_ctrls
            driven_grp = core_hrchy.add_offset_transform(target_list=_mid_ik, transform_suffix="driven")
            offset_grp = cmds.listRelatives(driven_grp, parent=True, fullPath=True)[0]
            follow_constraint = cmds.parentConstraint([_start_ik, _end_ik, offset_grp], driven_grp, mo=True)[0]
            # Follow Hip and Chest Attribute
            core_attr.add_attr(obj_list=_mid_ik, attributes="followHipAndChest", default=1, minimum=0, maximum=1)
            cmds.connectAttr(f"{_mid_ik}.followHipAndChest", f"{follow_constraint}.w0")  # Hip
            cmds.connectAttr(f"{_mid_ik}.followHipAndChest", f"{follow_constraint}.w1")  # Chest
            reverse = core_node.create_node(node_type="reverse", name=f"{self.setup_name}_reverseMidFollow")
            cmds.connectAttr(f"{_mid_ik}.followHipAndChest", f"{reverse}.inputX")  # Chest
            cmds.connectAttr(f"{reverse}.outputX", f"{follow_constraint}.w2")  # Chest

        # Constraint Start/End IK Ribbon controls to FK joints to have full control.
        core_cnstr.constraint_targets(source_driver=spine_ik_ctrls[0], target_driven=fk_joints[0])
        core_cnstr.constraint_targets(source_driver=spine_ik_ctrls[-1], target_driven=fk_joints[-1])

        # Shapes Visibility
        for fk_ctrl in fk_ctrls:
            cmds.connectAttr(f"{direction_ctrl}.fkVisibility", f"{fk_ctrl}.shapeVisibility")

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = direction_parent_groups


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    import gt.core.session as core_session

    core_session.remove_modules_startswith("gt.tools.auto_rigger.module")
    core_session.remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils

    import gt.tools.auto_rigger.modules.module_root as tools_rig_mod_root
    import importlib

    importlib.reload(tools_rig_mod_root)
    importlib.reload(tools_rig_fmr)
    importlib.reload(tools_rig_utils)

    a_generic_mod = tools_rig_frm.ModuleGeneric()
    a_root = tools_rig_mod_root.ModuleRoot()
    a_1st_spine = ModuleQuadSpine(divisions=4)
    a_2nd_spine = ModuleQuadSpine()
    a_3rd_spine = ModuleQuadSpine()
    # Configure Modules
    root_uuid = a_root.root_proxy.get_uuid()
    spine_base_proxy_uuid = a_1st_spine.base_proxy.get_uuid()
    spine_end_proxy_uuid = a_1st_spine.end_proxy.get_uuid()
    a_1st_spine.set_parent_uuid(root_uuid)
    a_2nd_spine.set_parent_uuid(root_uuid)
    a_3rd_spine.set_parent_uuid(root_uuid)
    a_1st_proxy = a_generic_mod.add_new_proxy()
    a_2nd_proxy = a_generic_mod.add_new_proxy()
    a_1st_proxy.set_name("base_child")
    a_2nd_proxy.set_name("end_child")
    a_1st_proxy.set_parent_uuid(spine_base_proxy_uuid)
    a_2nd_proxy.set_parent_uuid(spine_end_proxy_uuid)

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_1st_spine)
    a_project.add_to_modules(a_2nd_spine)
    a_project.add_to_modules(a_3rd_spine)
    a_project.add_to_modules(a_generic_mod)

    # Rename proxies
    for a_proxy in a_1st_spine.get_proxies():
        a_proxy.set_name(a_proxy.get_name().replace("chest", "chestOne"))
        a_proxy.set_name(a_proxy.get_name().replace("spine", "spineOne"))
        a_proxy.set_name(a_proxy.get_name().replace("hips", "hipsOne"))
    for a_proxy in a_2nd_spine.get_proxies():
        a_proxy.set_name(a_proxy.get_name().replace("chest", "chestTwo"))
        a_proxy.set_name(a_proxy.get_name().replace("spine", "spineTwo"))
        a_proxy.set_name(a_proxy.get_name().replace("hips", "hipsTwo"))
    for a_proxy in a_3rd_spine.get_proxies():
        a_proxy.set_name(a_proxy.get_name().replace("chest", "chestThree"))
        a_proxy.set_name(a_proxy.get_name().replace("spine", "spineThree"))
        a_proxy.set_name(a_proxy.get_name().replace("hips", "hipsThree"))

    a_project.build_proxy()

    # Adjust Tests
    cmds.setAttr(f"C_hipsTwo.tx", 55)
    cmds.setAttr(f"C_hipsTwo.tz", -120)
    cmds.setAttr(f"C_chestTwo.ty", 55)
    cmds.setAttr(f"base_child.ty", 20)
    cmds.setAttr(f"end_child.ty", 20)
    cmds.setAttr(f"C_hipsThree.tx", -55)
    cmds.setAttr(f"C_hipsThree.rx", -90)

    _build_rig = True
    _show_setup = True
    if _build_rig:
        a_project.build_rig()
        if _show_setup:
            cmds.setAttr("skeleton.visibility", 1)
            cmds.setAttr("spineAutomation.visibility", 1)
            cmds.select("C_root_JNT", hierarchy=True)
            for obj in cmds.ls(selection=True):
                cmds.setAttr(f"{obj}.displayLocalAxis", 1)
            cmds.select(clear=True)
    # Show all
    cmds.viewFit(all=True)
