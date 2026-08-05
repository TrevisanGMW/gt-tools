"""
Auto Rigger Ribbon Module
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.rigging as core_rigging
import gt.core.surface as core_surface
import gt.core.transform as core_trans
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.core.color as core_color
import gt.core.node as core_node
import gt.core.math as core_math
import gt.core.attr as core_attr
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleRibbon(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_ribbon
    allow_parenting = True

    def __init__(
        self,
        name="Ribbon",
        prefix=core_naming.NamingConstants.Prefix.CENTER,
        suffix=None,
        rot_order=0,
        divisions=2,
        num_ctrls=2,
        ik_ctrl_shapes="sphere_joint",
        fk_ctrl_shapes="_circle_pos_x",
        cable_ctrls=False,
        rotate_ribbon=False,
    ):
        """
        Initializes the Ribbon module.

        Args:
            name (str, optional): Name of the module. Defaults to "Ribbon".
            prefix (str, optional): Naming prefix, typically indicating side
                (e.g., center, left, right). Defaults to NamingConstants.Prefix.CENTER.
            suffix (str, optional): Optional suffix for the module name. Defaults to None.
            rot_order (int, optional): Rotation order for the proxies. Defaults to 0.
            divisions (int, optional): Number of intermediate divisions between base and end. Defaults to 2.
            num_ctrls (int, optional): Number of main controls (usually along the ribbon). Defaults to 2.
            ik_ctrl_shapes (str, optional): Curve or shape used for IK controls. Defaults to "sphere_joint".
            fk_ctrl_shapes (str, optional): Curve or shape used for FK controls. Defaults to "_circle_pos_x".
            cable_ctrls (bool, optional): Whether to use cable-style controls. Defaults to False.
            rotate_ribbon (bool, optional): Whether the ribbon rotates along its path. Defaults to False.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.setup_name = name.lower()
        self.proxy_inherit_name = True
        self.ribbon_base_name = f"{self.setup_name}Base"
        self.rot_order = rot_order
        self.divisions = divisions
        self.division_last_num = divisions  # Refreshed after every rig or proxy build
        self.num_ctrls = num_ctrls
        self.ribbon_end_name = f"{self.setup_name}End"
        self.ik_ctrl_shapes = ik_ctrl_shapes
        self.fk_ctrl_shapes = fk_ctrl_shapes
        self._dropoff_rate = 2
        self.middle_proxies_reset = True
        self.cable_ctrls = cable_ctrls
        self.rotate_ribbon = rotate_ribbon
        self.span_multiplier = 1
        self.equidistant = False

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 1, 0), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)

        self.base_proxy = tools_rig_frm.Proxy(name=self.ribbon_base_name)
        pos_ribbon_base = core_trans.Vector3(x=0, y=0, z=0)
        self.base_proxy.set_initial_position(xyz=pos_ribbon_base)
        self.base_proxy.set_locator_scale(scale=1.5)
        self.base_proxy.set_meta_purpose(value=self.ribbon_base_name)
        self.base_proxy.set_rotation_order(rotation_order=self.rot_order)
        self.base_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )

        self.end_proxy = tools_rig_frm.Proxy(name=self.ribbon_end_name)
        pos_ribbon_end = core_trans.Vector3(y=30)
        self.end_proxy.set_initial_position(xyz=pos_ribbon_end)
        self.end_proxy.set_locator_scale(scale=1.5)
        self.end_proxy.add_line_parent(self.base_proxy)
        self.end_proxy.set_parent_uuid(self.base_proxy.get_uuid())
        self.end_proxy.set_meta_purpose(value=self.ribbon_end_name)
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
        Set a new number of ribbon proxies. These are the proxies in-between the ribbon base proxy and ribbon end proxy
        Args:
            divisions (int): New number of joints to exist in-between base and end.
                             Minimum is zero (0) - No negative numbers.
        """
        ribbon_len = len(self.mid_proxies)
        # Same as current, skip
        if ribbon_len == divisions:
            return

        # New number higher than current - Add more proxies
        if ribbon_len < divisions:
            # Determine Initial Parent
            if self.mid_proxies:
                _parent_uuid = self.mid_proxies[-1].get_uuid()
            else:
                _parent_uuid = self.base_proxy.get_uuid()
            # Create new ribbons
            for num in range(ribbon_len, divisions):
                new_ribbon_name = f"{self.setup_name + str(num + 1).zfill(2)}"
                new_ribbon = tools_rig_frm.Proxy(name=new_ribbon_name)
                new_ribbon.set_locator_scale(scale=1)
                new_ribbon.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
                new_ribbon.set_meta_purpose(value=new_ribbon_name)
                new_ribbon.add_line_parent(line_parent=_parent_uuid)
                new_ribbon.set_parent_uuid(uuid=_parent_uuid)
                new_ribbon.add_driver_type(
                    driver_type=[
                        tools_rig_const.RiggerDriverTypes.GENERIC,
                        tools_rig_const.RiggerDriverTypes.FK,
                        tools_rig_const.RiggerDriverTypes.IK,
                    ]
                )
                new_ribbon.set_rotation_order(rotation_order=self.rot_order)
                _parent_uuid = new_ribbon.get_uuid()
                self.mid_proxies.append(new_ribbon)
        # New number lower than current - Remove unnecessary proxies
        elif len(self.mid_proxies) > divisions:
            self.mid_proxies = self.mid_proxies[:divisions]  # Truncate the list

        if self.mid_proxies:
            self.end_proxy.add_line_parent(line_parent=self.mid_proxies[-1].get_uuid())
        else:
            self.end_proxy.add_line_parent(line_parent=self.base_proxy.get_uuid())

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
        Sets a new rotation order for the proxies of this ribbon
        Args:
            rot_order (int, str): The rotation order from 0 to 5 or a string describing the rotation order.
                                       e.g. "xyz", "yzx", "zxy", "xzy", "yxz", "zyx"
        """
        all_ribbon_proxies = [self.base_proxy] + self.mid_proxies + [self.end_proxy]
        for proxy in all_ribbon_proxies:
            proxy.set_rotation_order(rot_order)
        self.refresh_proxies_list()

    def set_proxies_name(self, name):
        """
        Sets a new name for the proxies found in this ribbon.
        Args:
            name (str): A new name to use in the renaming of the elements.
        """
        self.setup_name = name
        self.ribbon_base_name = f"{self.setup_name}Base"
        self.ribbon_end_name = f"{self.setup_name}End"
        self.base_proxy.set_name(f"{name}Base")
        for proxy in self.mid_proxies:
            proxy.set_name(f"{name+ str(self.mid_proxies.index(proxy) + 1).zfill(2)}")
        self.end_proxy.set_name(f"{name}End")
        self.refresh_proxies_list()

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
            _divisions = module_dict.get("divisions", self.divisions)
            self.set_divisions_num(divisions=_divisions)
            self.refresh_proxies_list()
        return super().read_data_from_dict(module_dict=module_dict)

    def get_closest_joint(self, main_obj):
        """
        Finds the closest module joint to the supplied transform.

        Args:
            main_obj (str): scene object, origin for the measuring
        Returns:
            closest joint (str)
        """
        ribbon_base_jnt = tools_rig_utils.find_joint_from_uuid(self.base_proxy.get_uuid())
        ribbon_mid_jnts = [tools_rig_utils.find_joint_from_uuid(prx.get_uuid()) for prx in self.mid_proxies]
        ribbon_end_jnt = tools_rig_utils.find_joint_from_uuid(self.end_proxy.get_uuid())
        ribbon_jnt_list = [ribbon_base_jnt] + ribbon_mid_jnts + [ribbon_end_jnt]

        closest_joint = None
        closest_value = None
        for jnt in ribbon_jnt_list:
            distance = core_math.dist_center_to_center(obj_a=main_obj, obj_b=jnt)
            if not closest_value:
                closest_value = distance
                closest_joint = jnt
            elif distance < closest_value:
                closest_value = distance
                closest_joint = jnt

        return closest_joint

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
        ribbon_base_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.base_proxy.get_uuid())
        ribbon_end_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.end_proxy.get_uuid())
        middle_ribbon_proxy_list = [tools_rig_utils.find_proxy_from_uuid(prx.get_uuid()) for prx in self.mid_proxies]
        ribbon_base_jnt = tools_rig_utils.find_joint_from_uuid(self.base_proxy.get_uuid())
        ribbon_end_jnt = tools_rig_utils.find_joint_from_uuid(self.end_proxy.get_uuid())
        middle_ribbon_jnt_list = [tools_rig_utils.find_joint_from_uuid(prx.get_uuid()) for prx in self.mid_proxies]

        # order: base, end, middle ones
        core_trans.match_translate(source=ribbon_base_jnt, target_list=ribbon_base_proxy_item)
        core_trans.match_translate(source=ribbon_end_jnt, target_list=ribbon_end_proxy_item)
        [
            core_trans.match_translate(source=jnt, target_list=prx)
            for prx, jnt in zip(middle_ribbon_proxy_list, middle_ribbon_jnt_list)
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
        ribbon_base = tools_rig_utils.find_proxy_from_uuid(self.base_proxy.get_uuid())
        ribbon_end = tools_rig_utils.find_proxy_from_uuid(self.end_proxy.get_uuid())
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
        core_cnstr.equidistant_constraints(start=ribbon_base, end=ribbon_end, target_list=proxy_offsets)

        self.base_proxy.apply_transforms()
        self.end_proxy.apply_transforms()
        if not reset_middle_transforms:
            for ribbon in self.mid_proxies:
                ribbon.apply_transforms()
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
        super().build_skeleton_hierarchy()  # Passthrough

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        _ik_suffix = core_naming.NamingConstants.Description.IK.upper()
        _ribbon_shape_scale_multiplier = 0.08  # Multiplies the scale of the shapes used by the IK controls

        # Get Joints
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        ribbon_base_jnt = tools_rig_utils.find_joint_from_uuid(self.base_proxy.get_uuid())
        ribbon_mid_jnts = [tools_rig_utils.find_joint_from_uuid(prx.get_uuid()) for prx in self.mid_proxies]
        ribbon_end_jnt = tools_rig_utils.find_joint_from_uuid(self.end_proxy.get_uuid())
        module_parent_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())
        ribbon_jnt_list = [ribbon_base_jnt] + ribbon_mid_jnts + [ribbon_end_jnt]
        # Get Formatted Prefix
        _prefix = ""
        if self.prefix:
            _prefix = f"{self.prefix}_"

        # Setup groups
        joint_automation_group = tools_rig_utils.find_or_create_joint_automation_group()
        ribbon_automation_group = tools_rig_utils.get_automation_group("ribbonAutomation")
        core_hrchy.parent(source_objects=module_parent_jnt, target_parent=joint_automation_group)
        cmds.setAttr(f"{ribbon_automation_group}.visibility", 0)
        cmds.setAttr(f"{joint_automation_group}.visibility", 0)

        # Ribbon -------------------------
        ribbon_grp = f"{_prefix}{self.setup_name}_{core_naming.NamingConstants.Suffix.GRP}"
        ribbon_grp = core_hrchy.create_group(name=ribbon_grp)
        ribbon_grp = core_hrchy.parent(source_objects=ribbon_grp, target_parent=ribbon_automation_group)[0]
        cmds.setAttr(f"{ribbon_grp}.inheritsTransform", 0)  # Ignore Hierarchy Transform

        ribbon_name = self._assemble_ctrl_name(
            name=self.setup_name, overwrite_suffix=core_naming.NamingConstants.Suffix.SUR
        )
        ribbon_sur = core_surface.create_surface_from_object_list(
            obj_list=ribbon_jnt_list,
            surface_name=ribbon_name,
            degree=1,  # custom_normal=(0, 0, 1)
        )
        ribbon_sur = core_node.Node(ribbon_sur)

        if self.rotate_ribbon:
            num_spans_v = cmds.getAttr(f"{ribbon_sur}.spansV") + 2
            all_ribbon_cvs = f"{ribbon_sur}.cv[0:1][0:{num_spans_v-1}]"
            cmds.select(all_ribbon_cvs)
            cmds.rotate(0, 0, 90, all_ribbon_cvs, cs=True, r=True)

        core_surface.multiply_surface_spans(
            input_surface=ribbon_sur,
            u_degree=1,
            v_degree=3,
            v_multiplier=self.span_multiplier,
        )
        core_hrchy.parent(source_objects=ribbon_sur, target_parent=ribbon_grp)

        # Create Follicles
        follicle_transforms = []
        fk_joints = []
        for index, joint in enumerate(ribbon_jnt_list):
            joint_pos = cmds.xform(joint, query=True, translation=True, worldSpace=True)
            u_pos, v_pos = core_surface.get_closest_uv_point(surface=ribbon_sur, xyz_pos=joint_pos)
            v_pos_normalized = v_pos / (len(ribbon_jnt_list) - 1)
            fol_trans, fol_shape = core_surface.create_follicle(
                input_surface=ribbon_sur,
                uv_position=(0.5, v_pos_normalized),
                name=f"{_prefix}{self.setup_name}Follicle_{(index + 1):02d}",
            )
            follicle_transforms.append(fol_trans)
            jnt = core_rigging.duplicate_joint_for_automation(joint, suffix="fk", parent=fol_trans)
            core_cnstr.constraint_targets(jnt, joint)
            fk_joints.append(jnt)

        core_hrchy.parent(source_objects=follicle_transforms, target_parent=ribbon_grp)
        # Set joints colors
        core_color.set_color_viewport(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigJoint.GENERAL)

        # Get chain scale
        ribbon_scale = core_math.dist_center_to_center(ribbon_base_jnt, ribbon_end_jnt)

        # Controls ----------------------------------------------------------------------------------------
        ribbon_base_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.base_proxy.get_uuid())
        ribbon_rotation_order = cmds.getAttr(
            f"{ribbon_base_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}"
        )
        ribbon_global_ctrl, ribbon_base_parent_groups = self.create_rig_control(
            control_base_name=f"{self.setup_name}Global",
            curve_file_name="_circle_pos_x",
            parent_obj=global_offset_ctrl,
            match_obj=ribbon_base_jnt,
            add_offset_ctrl=False,
            rot_order=ribbon_rotation_order,
            shape_scale=ribbon_scale * 0.35,
            color=core_color.ColorConstants.RGB.YELLOW,
        )[:2]
        core_attr.hide_lock_default_attrs(obj_list=ribbon_global_ctrl, scale=True, visibility=True)

        # Visibility
        core_attr.add_separator_attr(ribbon_global_ctrl, attr_name="ctrlVisibility")
        core_attr.add_attr(obj_list=ribbon_global_ctrl, attributes="fkVisibility", attr_type="bool", default=1)
        core_attr.add_attr(obj_list=ribbon_global_ctrl, attributes="ikVisibility", attr_type="bool", default=1)

        # General Groups
        bind_grp = f"{_prefix}{self.setup_name}_bind_{core_naming.NamingConstants.Suffix.GRP}"
        bind_grp = core_hrchy.create_group(name=bind_grp)
        bind_grp = core_hrchy.parent(source_objects=bind_grp, target_parent=ribbon_automation_group)[0]
        cmds.setAttr(f"{bind_grp}.visibility", 0)

        # IK Controls
        bind_jnts = []
        ribbon_ik_ctrls = []
        ribbon_ik_ctrls_offsets = []

        ribbon_base_ik_ctrl, ribbon_base_ik_parent_groups = self.create_rig_control(
            control_base_name=f"{self.ribbon_base_name}_{_ik_suffix}",
            curve_file_name=self.ik_ctrl_shapes,
            parent_obj=ribbon_global_ctrl,
            match_obj=ribbon_base_jnt,
            add_offset_ctrl=False,
            rot_order=ribbon_rotation_order,
            shape_scale=ribbon_scale * 0.08,
            color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=ribbon_base_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.base_proxy,
        )
        ribbon_ik_ctrls.append(ribbon_base_ik_ctrl)
        ribbon_ik_ctrls_offsets.append(ribbon_base_ik_parent_groups[0])
        core_attr.hide_lock_default_attrs(ribbon_base_ik_ctrl, scale=True, visibility=True)

        for index in range(self.num_ctrls):
            fol_trans, fol_shape = core_surface.create_follicle(
                input_surface=ribbon_sur,
                uv_position=(0.5, (1 / (self.num_ctrls + 1)) * (index + 1)),
                name=f"{_prefix}{self.setup_name}Follicle_{(index + 1):02d}",
            )
            ribbon_ik_ctrl, ribbon_ik_parent_groups = self.create_rig_control(
                control_base_name=f"{self.setup_name}{(index + 1):02d}_{_ik_suffix}",
                curve_file_name=self.ik_ctrl_shapes,
                parent_obj=ribbon_global_ctrl,
                match_obj=fol_trans,
                add_offset_ctrl=False,
                rot_order=ribbon_rotation_order,
                shape_scale=ribbon_scale * _ribbon_shape_scale_multiplier,
                color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
            )[:2]
            cmds.delete(fol_trans)
            cmds.setAttr(f"{ribbon_ik_parent_groups[0]}.rotate", 0, 0, 0, type="double3")

            self._add_driver_uuid_attr(
                target_driver=ribbon_ik_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.IK,
                proxy_purpose=f"{self.setup_name}{(index + 1):02d}",
            )
            core_attr.hide_lock_default_attrs(ribbon_ik_ctrl, scale=True, visibility=True)
            ribbon_ik_ctrls.append(ribbon_ik_ctrl)
            ribbon_ik_ctrls_offsets.append(ribbon_ik_parent_groups[0])

        # Align IK mid controls
        start_alignment_obj = ribbon_ik_ctrls_offsets[0]
        for index, offset_grp in enumerate(ribbon_ik_ctrls_offsets):
            if index == 0:
                continue
            if len(ribbon_ik_ctrls_offsets) - 1 == index:
                end_alignment_obj = ribbon_end_jnt
            else:
                end_alignment_obj = ribbon_ik_ctrls_offsets[index + 1]
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
            else:
                if self.get_orientation_method() == tools_rig_frm.OrientationData.Methods.inherit:
                    closest_joint = self.get_closest_joint(offset_grp)
                    core_trans.match_rotate(source=closest_joint, target_list=offset_grp)

        ribbon_end_ik_ctrl, ribbon_end_ik_parent_groups = self.create_rig_control(
            control_base_name=f"{self.ribbon_end_name}_{_ik_suffix}",
            curve_file_name=self.ik_ctrl_shapes,
            parent_obj=ribbon_global_ctrl,
            match_obj=ribbon_end_jnt,
            add_offset_ctrl=False,
            rot_order=ribbon_rotation_order,
            shape_scale=ribbon_scale * _ribbon_shape_scale_multiplier,
            color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=ribbon_end_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.end_proxy,
        )
        core_attr.hide_lock_default_attrs(ribbon_end_ik_ctrl, scale=True, visibility=True)
        ribbon_ik_ctrls.append(ribbon_end_ik_ctrl)
        ribbon_ik_ctrls_offsets.append(ribbon_end_ik_parent_groups[0])

        for offset in ribbon_ik_ctrls_offsets:
            cmds.connectAttr(f"{ribbon_global_ctrl}.ikVisibility", f"{offset}.visibility")

        fk_ctrls = []
        fk_offsets = []
        # Cable Controls ---------------------------------------------------------------
        if self.cable_ctrls:
            core_attr.add_separator_attr(ribbon_global_ctrl, attr_name="cable")
            cmds.setAttr(f"{ribbon_global_ctrl}.cable", lock=True)
            core_attr.add_attr(
                obj_list=ribbon_global_ctrl,
                attributes=["startInfluence", "endInfluence"],
                attr_type="float",
                minimum=0,
                maximum=10,
                default=1,
            )

            # FK Controls
            ribbon_start_end_ik_ctrls = [ribbon_base_ik_ctrl, ribbon_end_ik_ctrl]
            ribbon_start_end_ik_offsets = [ribbon_base_ik_parent_groups[0], ribbon_end_ik_parent_groups[0]]
            _start_end_fk_ctrls = []
            _start_end_fk_offsets = []
            for ik_ctrl, ik_offset in zip(ribbon_start_end_ik_ctrls, ribbon_start_end_ik_offsets):
                ctrl_name = ik_ctrl.get_short_name().split(f"_{_ik_suffix}")[0]
                ribbon_fk_ctrl, ribbon_fk_parent_groups = self.create_rig_control(
                    control_base_name=ctrl_name,
                    overwrite_prefix="",
                    curve_file_name=self.fk_ctrl_shapes,
                    parent_obj=ribbon_global_ctrl,
                    match_obj=ik_ctrl,
                    add_offset_ctrl=False,
                    rot_order=ribbon_rotation_order,
                    shape_scale=ribbon_scale * 0.2,
                    color=core_color.ColorConstants.RGB.BLUE_SKY,
                )[:2]
                purpose = cmds.getAttr(f"{ik_ctrl}.{tools_rig_const.RiggerConstants.ATTR_DRIVER_UUID}").split("-")[-1]
                self._add_driver_uuid_attr(
                    target_driver=ribbon_fk_ctrl,
                    driver_type=tools_rig_const.RiggerDriverTypes.FK,
                    proxy_purpose=purpose,
                )
                core_attr.hide_lock_default_attrs(ribbon_fk_ctrl, scale=True, visibility=True)
                cmds.parentConstraint(ribbon_fk_ctrl, ik_offset)
                _start_end_fk_ctrls.append(ribbon_fk_ctrl)
                _start_end_fk_offsets.append(ribbon_fk_parent_groups)
            mid_fol_trans, mid_fol_shape = core_surface.create_follicle(
                input_surface=ribbon_sur,
                uv_position=(0.5, 0.5),
                name=f"{_prefix}{self.setup_name}Follicle_mid_ctrl",
            )
            ribbon_mid_fk_ctrl, ribbon_mid_fk_parent_groups = self.create_rig_control(
                control_base_name=f"{self.setup_name}Mid",
                curve_file_name=self.fk_ctrl_shapes,
                parent_obj=ribbon_global_ctrl,
                match_obj=mid_fol_trans,
                add_offset_ctrl=False,
                rot_order=ribbon_rotation_order,
                shape_scale=ribbon_scale * 0.2,
                color=core_color.ColorConstants.RGB.BLUE_SKY,
            )[:2]

            cmds.delete(mid_fol_trans)
            cmds.setAttr(f"{ribbon_mid_fk_parent_groups[0]}.rotate", 0, 0, 0, type="double3")
            self._add_driver_uuid_attr(
                target_driver=ribbon_mid_fk_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=f"{self.setup_name}midFK",
            )
            if self.num_ctrls % 2 == 0:  # Even
                middle_of_list = int(len(ribbon_ik_ctrls) / 2)
                even_list = True
            else:  # Odd
                middle_of_list = int(((len(ribbon_ik_ctrls) - 1) / 2) + 1)
                even_list = False
            for ctrl in ribbon_ik_ctrls[1 : middle_of_list - 1]:
                prev_ctrl = ribbon_ik_ctrls[ribbon_ik_ctrls.index(ctrl) - 1]
                influence_constraint = cmds.parentConstraint(
                    prev_ctrl, ribbon_mid_fk_ctrl, ribbon_ik_ctrls_offsets[ribbon_ik_ctrls.index(ctrl)], mo=True
                )[0]
                cmds.connectAttr(f"{ribbon_global_ctrl}.startInfluence", f"{influence_constraint}.w0")
            if even_list:
                upper_mid_list = ribbon_ik_ctrls[middle_of_list + 1 : -1]
            else:
                upper_mid_list = ribbon_ik_ctrls[middle_of_list:-1]
            for ctrl in upper_mid_list:
                post_ctrl = ribbon_ik_ctrls[ribbon_ik_ctrls.index(ctrl) + 1]
                influence_constraint = cmds.parentConstraint(
                    ribbon_mid_fk_ctrl, post_ctrl, ribbon_ik_ctrls_offsets[ribbon_ik_ctrls.index(ctrl)], mo=True
                )[0]
                cmds.connectAttr(f"{ribbon_global_ctrl}.endInfluence", f"{influence_constraint}.w1")
            if even_list:
                for ctrl in ribbon_ik_ctrls[middle_of_list - 1 : middle_of_list + 1]:
                    cmds.parentConstraint(
                        ribbon_mid_fk_ctrl, ribbon_ik_ctrls_offsets[ribbon_ik_ctrls.index(ctrl)], mo=True
                    )
            else:
                cmds.parentConstraint(
                    ribbon_mid_fk_ctrl,
                    ribbon_ik_ctrls_offsets[ribbon_ik_ctrls.index(ribbon_ik_ctrls[middle_of_list - 1])],
                    mo=True,
                )
            # Append Controls For Later
            fk_ctrls.append(_start_end_fk_ctrls[0])
            fk_ctrls.append(ribbon_mid_fk_ctrl)
            fk_ctrls.append(_start_end_fk_ctrls[-1])
            fk_offsets.append(_start_end_fk_offsets[0][0])
            fk_offsets.append(ribbon_mid_fk_parent_groups[0])
            fk_offsets.append(_start_end_fk_offsets[-1][0])

        # Bind Joints
        for ctrl in ribbon_ik_ctrls:
            jnt_name = ctrl.get_short_name().split("_CTRL")[0]
            jnt_name = f"{jnt_name}_bind"
            bind_jnt = core_node.Node(cmds.joint(n=jnt_name))
            cmds.setAttr(f"{bind_jnt}.rotateOrder", ribbon_rotation_order)
            bind_jnts.append(bind_jnt)
            if ribbon_ik_ctrls.index(ctrl) == 0:
                cmds.parent(bind_jnt, bind_grp)
            cmds.parentConstraint(ctrl, bind_jnt)

        # Bind the surface
        num_joints = len(bind_jnts)
        num_segments = num_joints - 1
        nurbs_skin_cluster = cmds.skinCluster(
            bind_jnts,
            ribbon_sur,
            dropoffRate=self._dropoff_rate,
            maximumInfluences=self.divisions + 2,
            nurbsSamples=self.divisions * 4,
            bindMethod=0,  # Closest Distance
            name=f"{_prefix}{self.setup_name}SkinCluster",
        )[0]
        cmds.skinPercent(nurbs_skin_cluster, ribbon_sur, pruneWeights=0.2)

        # Get number of V CVs
        num_spans_v = cmds.getAttr(f"{ribbon_sur}.spansV") + 3
        for i in range(num_spans_v):
            cv = f"{ribbon_sur}.cv[0:1][{i}]"
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

        # FK Controls (Standard non-cable version)
        if not self.cable_ctrls:
            # FK Controls
            fk_parent = ribbon_global_ctrl
            for ik_ctrl, ik_offset in zip(ribbon_ik_ctrls, ribbon_ik_ctrls_offsets):
                ctrl_name = ik_ctrl.get_short_name().split(f"_{_ik_suffix}")[0]
                ribbon_fk_ctrl, ribbon_fk_parent_groups = self.create_rig_control(
                    control_base_name=ctrl_name,
                    overwrite_prefix="",
                    curve_file_name=self.fk_ctrl_shapes,
                    parent_obj=fk_parent,
                    match_obj=ik_ctrl,
                    add_offset_ctrl=False,
                    rot_order=ribbon_rotation_order,
                    shape_scale=ribbon_scale * 0.2,
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

        # Equidistant Setup
        if self.equidistant:
            # Unpack
            last_ctrl = fk_ctrls[-1]
            # Equidistant Control (END)
            ribbon_effector_end_ctrl, ribbon_effector_end_parent_groups = self.create_rig_control(
                control_base_name=f"{self.setup_name}Effector",
                curve_file_name="_circle_pos_x",
                parent_obj=ribbon_global_ctrl,
                match_obj=last_ctrl,
                add_offset_ctrl=False,
                rot_order=ribbon_rotation_order,
                shape_scale=ribbon_scale * 0.35,
                color=core_color.ColorConstants.RGB.YELLOW,
            )[:2]
            core_hrchy.parent(target_parent=ribbon_global_ctrl, source_objects=fk_offsets)
            constraints_point = core_cnstr.equidistant_constraints(
                start=ribbon_global_ctrl,
                end=ribbon_effector_end_ctrl,
                target_list=fk_offsets,
                maintain_offset=True,
                constraint=core_cnstr.ConstraintTypes.PARENT,
                skip_start_end=False,
            )
            core_attr.add_separator_attr(ribbon_global_ctrl, attr_name="equidistant")
            core_attr.add_attr(
                obj_list=ribbon_global_ctrl,
                attributes="equidistantInfluence",
                attr_type="float",
                minimum=0,
                maximum=1,
                default=1,
            )
            core_attr.add_attr(
                obj_list=ribbon_global_ctrl,
                attributes="equidistantEffectorVisibility",
                attr_type="bool",
                default=1,
            )
            cmds.addAttr(f"{ribbon_global_ctrl}.equidistantInfluence", e=True, niceName="Effect Influence")
            cmds.addAttr(f"{ribbon_global_ctrl}.equidistantEffectorVisibility", e=True, niceName="Effector Visibility")
            cmds.connectAttr(
                f"{ribbon_global_ctrl}.equidistantEffectorVisibility", f"{ribbon_effector_end_ctrl}.shapeVisibility"
            )
            # Create Influence Setup
            fallbacks_dict = core_cnstr.blend_constraints_with_influence(
                constraints_point, influence_attr=f"{ribbon_global_ctrl}.equidistantInfluence"
            )
            # Create Chain from Fallback Transforms (Retain FK behaviour)
            fallbacks_list = list(fallbacks_dict.values())
            for i in range(1, len(fallbacks_list)):
                cmds.parent(fallbacks_list[i], fallbacks_list[i - 1])

            # Re-create FK behavior, but not for cable controls
            fallback_grp = core_node.create_node(node_type="transform", name=f"{_prefix}fallback_grp")
            core_hrchy.parent(target_parent=fallback_grp, source_objects=fallbacks_list[0])
            core_hrchy.parent(target_parent=ribbon_automation_group, source_objects=fallback_grp)

            if not self.cable_ctrls:
                last_parent = fallback_grp
                cmds.parentConstraint(ribbon_global_ctrl, fallback_grp)
                reverse_influence = core_node.create_node(
                    node_type="reverse", name=f"{ribbon_global_ctrl}_reverseInfluence"
                )
                cmds.connectAttr(f"{ribbon_global_ctrl}.equidistantInfluence", f"{reverse_influence}.inputX")
                for index, ctrl in enumerate(fk_ctrls):
                    ctrl_shortname = core_naming.get_short_name(ctrl)
                    fallback_offset = f'fallbackOffset_{ctrl_shortname.replace("_CTRL", "")}'
                    fallback_offset = cmds.createNode("transform", name=fallback_offset)
                    core_trans.match_transform(source=ctrl, target_list=fallback_offset)
                    fallback = core_node.Node(fallbacks_list[index])
                    core_hrchy.parent(source_objects=fallback, target_parent=fallback_offset)
                    core_hrchy.parent(source_objects=fallback_offset, target_parent=last_parent)
                    last_parent = fallback
                    cmds.connectAttr(f"{ctrl}.translate", f"{fallback}.translate")
                    cmds.connectAttr(f"{ctrl}.rotate", f"{fallback}.rotate")
                    invert_offset = core_hrchy.add_offset_transform(
                        target_list=ctrl, transform_suffix="invertOffsetMatrix"
                    )[0]
                    blend_matrix = core_node.create_node(node_type="blendMatrix", name=f"{ctrl}_blendInverseMatrix")
                    cmds.connectAttr(f"{fallback}.inverseMatrix", f"{blend_matrix}.target[0].targetMatrix")
                    cmds.connectAttr(f"{blend_matrix}.outputMatrix", f"{invert_offset}.offsetParentMatrix")
                    cmds.connectAttr(f"{reverse_influence}.outputX", f"{blend_matrix}.envelope")

            # Create Follow Attributes
            tools_rig_utils.create_follow_setup(
                control=ribbon_effector_end_ctrl,
                parent=ribbon_global_ctrl,
                attr_name="followGlobalPosition",
                ref_loc=True,
                default_value=1,
                constraint_type="parent",
            )
            tools_rig_utils.create_follow_setup(
                control=ribbon_effector_end_ctrl,
                parent=ribbon_global_ctrl,
                ref_loc=True,
                attr_name="followGlobal",
                default_value=1,
                constraint_type="orient",
            )

        # Ribbon Blend-shapes
        twist_ribbon = cmds.duplicate(ribbon_sur, n=f"{ribbon_sur.get_short_name()}_twist")
        sine_ribbon = cmds.duplicate(ribbon_sur, n=f"{ribbon_sur.get_short_name()}_wave")
        cmds.blendShape(
            twist_ribbon,
            sine_ribbon,
            ribbon_sur,
            n=f"{_prefix}{self.setup_name}Bs",
            w=[(0, 1), (1, 1)],
            foc=True,
            o="local",
        )
        twist_node = cmds.nonLinear(twist_ribbon, type="twist", n=f"{_prefix}{self.setup_name}Twist")
        sine_node = cmds.nonLinear(sine_ribbon, type="sine", n=f"{_prefix}{self.setup_name}Sine")
        cmds.parent(twist_node[1], sine_node[1], ribbon_grp)
        if not self.rotate_ribbon:
            cmds.setAttr(f"{sine_node[1]}.ry", 90)

        # Connect Attributes
        core_attr.add_separator_attr(ribbon_global_ctrl, attr_name="twist")
        cmds.setAttr(f"{ribbon_global_ctrl}.twist", lock=True)
        core_attr.add_attr(obj_list=ribbon_global_ctrl, attributes=["startAngle", "endAngle"], attr_type="float")
        core_attr.add_attr(
            obj_list=ribbon_global_ctrl,
            attributes="twistLowBound",
            attr_type="float",
            minimum=-10,
            maximum=0,
            default=-1,
        )
        core_attr.add_attr(
            obj_list=ribbon_global_ctrl,
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
            cmds.connectAttr(f"{ribbon_global_ctrl}.{out_attr}", f"{twist_node[0]}.{in_attr}")
        core_attr.add_separator_attr(ribbon_global_ctrl, attr_name="sine")
        cmds.setAttr(f"{ribbon_global_ctrl}.sine", lock=True)
        core_attr.add_attr(
            obj_list=ribbon_global_ctrl, attributes="amplitude", attr_type="float", maximum=5, minimum=-5
        )
        core_attr.add_attr(
            obj_list=ribbon_global_ctrl, attributes="wavelength", attr_type="float", maximum=10, minimum=0.1, default=2
        )
        core_attr.add_attr(obj_list=ribbon_global_ctrl, attributes="offset", attr_type="float")
        core_attr.add_attr(obj_list=ribbon_global_ctrl, attributes="dropoff", attr_type="float", maximum=1, minimum=-1)
        core_attr.add_attr(
            obj_list=ribbon_global_ctrl,
            attributes="sineLowBound",
            attr_type="float",
            minimum=-10,
            maximum=0,
            default=-1,
        )
        core_attr.add_attr(
            obj_list=ribbon_global_ctrl, attributes="sineHighBound", attr_type="float", minimum=0, maximum=10, default=1
        )
        for out_attr, in_attr in [
            ("amplitude", "amplitude"),
            ("wavelength", "wavelength"),
            ("offset", "offset"),
            ("dropoff", "dropoff"),
            ("sineLowBound", "lowBound"),
            ("sineHighBound", "highBound"),
        ]:
            cmds.connectAttr(f"{ribbon_global_ctrl}.{out_attr}", f"{sine_node[0]}.{in_attr}")

        # Align Non-linear Handles
        core_trans.align_object_to_vector(
            start_obj=ribbon_base_jnt,
            end_obj=ribbon_end_jnt,
            target_obj=twist_node[1],
            aim_axis="y",
        )
        core_trans.align_object_to_vector(
            start_obj=ribbon_base_jnt,
            end_obj=ribbon_end_jnt,
            target_obj=sine_node[1],
            aim_axis="y",
        )

        # # Constraint Start/End IK Ribbon controls to FK joints to have full control.
        start_lock_attr = "lockStart"
        end_lock_attr = "lockEnd"
        start_ik_ctrl = ribbon_ik_ctrls[0]
        end_ik_ctrl = ribbon_ik_ctrls[-1]
        start_follicle = follicle_transforms[0]
        end_follicle = follicle_transforms[-1]
        start_constraint = core_cnstr.constraint_targets(
            source_driver=[start_ik_ctrl, start_follicle], target_driven=fk_joints[0]
        )[0]
        end_constraint = core_cnstr.constraint_targets(
            source_driver=[end_ik_ctrl, end_follicle], target_driven=fk_joints[-1]
        )[0]
        core_attr.add_separator_attr(ribbon_global_ctrl, attr_name="lockOrientation")
        core_attr.add_attr(obj_list=ribbon_global_ctrl, attributes=start_lock_attr, attr_type="bool", default=True)
        core_attr.add_attr(obj_list=ribbon_global_ctrl, attributes=end_lock_attr, attr_type="bool", default=True)
        reverse_lock = core_node.create_node(node_type="reverse", name=f"{ribbon_global_ctrl}_reverseLock")
        cmds.connectAttr(f"{ribbon_global_ctrl}.{start_lock_attr}", f"{start_constraint}.w0")
        cmds.connectAttr(f"{ribbon_global_ctrl}.{start_lock_attr}", f"{reverse_lock}.inputX")
        cmds.connectAttr(f"{reverse_lock}.outputX", f"{start_constraint}.w1")
        cmds.connectAttr(f"{ribbon_global_ctrl}.{end_lock_attr}", f"{end_constraint}.w0")
        cmds.connectAttr(f"{ribbon_global_ctrl}.{end_lock_attr}", f"{reverse_lock}.inputY")
        cmds.connectAttr(f"{reverse_lock}.outputY", f"{end_constraint}.w1")

        # Shapes Visibility
        for fk_ctrl in fk_ctrls:
            cmds.connectAttr(f"{ribbon_global_ctrl}.fkVisibility", f"{fk_ctrl}.shapeVisibility")

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = ribbon_base_parent_groups


if __name__ == "__main__":  # pragma: no cover
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

    # Test Ribbon
    a_root = tools_rig_mod_root.ModuleRoot()
    a_1st_ribbon = ModuleRibbon(divisions=5, num_ctrls=5, cable_ctrls=True, rotate_ribbon=True)
    root_uuid = a_root.root_proxy.get_uuid()
    a_1st_ribbon.set_parent_uuid(root_uuid)
    # Extra Tests Ribbons
    a_2nd_ribbon = ModuleRibbon(divisions=19, num_ctrls=19)
    a_3rd_ribbon = ModuleRibbon()
    a_2nd_ribbon.set_parent_uuid(root_uuid)
    a_3rd_ribbon.set_parent_uuid(root_uuid)

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_1st_ribbon)
    a_project.add_to_modules(a_2nd_ribbon)
    a_project.add_to_modules(a_3rd_ribbon)

    # Rename proxies
    a_1st_ribbon.setup_name = "one"
    a_2nd_ribbon.setup_name = "two"
    a_3rd_ribbon.setup_name = "three"
    for a_proxy in a_1st_ribbon.get_proxies():
        a_proxy.set_name(a_proxy.get_name().replace("ribbon", "one"))
    for a_proxy in a_2nd_ribbon.get_proxies():
        a_proxy.set_name(a_proxy.get_name().replace("ribbon", "two"))
    for a_proxy in a_3rd_ribbon.get_proxies():
        a_proxy.set_name(a_proxy.get_name().replace("ribbon", "three"))

    # Activate Equidistant Setup
    a_1st_ribbon.equidistant = True
    a_2nd_ribbon.equidistant = True
    a_3rd_ribbon.equidistant = True

    a_project.build_proxy()
    # Setup Extra Tests B
    cmds.setAttr(f"C_twoBase.rx", -45)
    cmds.setAttr(f"C_twoBase.ty", 25)
    cmds.setAttr(f"C_twoBase.tx", 35)
    cmds.setAttr(f"C_twoBase.tz", -25)
    # Setup Extra Tests C
    cmds.setAttr(f"C_threeBase.rz", -90)
    cmds.setAttr(f"C_threeBase.rx", 90)
    cmds.setAttr(f"C_threeBase.ty", 25)
    cmds.setAttr(f"C_threeBase.tx", -35)
    cmds.setAttr(f"C_threeBase.tz", -25)
    cmds.setAttr(f"C_three01.translateX", -5)
    cmds.setAttr(f"C_three02.translateX", -2)

    # a_project.build_skeleton()
    mid_proxies = [
        "C_two01",
        "C_two02",
        "C_one04",
        "C_one05",
        "C_one02",
        "C_one03",
        "C_one01",
        "C_three01",
        "C_three02",
    ]
    cmds.select(mid_proxies)
    proxy_locators = core_trans.convert_transforms_to_locators()
    for _loc in proxy_locators:
        cmds.setAttr(f"{_loc}.localScaleX", 7)
        cmds.setAttr(f"{_loc}.localScaleY", 7)
        cmds.setAttr(f"{_loc}.localScaleZ", 7)
        core_color.set_color_viewport(_loc, (1, 0, 0))

    _build_rig = True
    _show_setup = True
    if _build_rig:
        a_project.build_rig()
        if _show_setup:
            cmds.setAttr("skeleton.visibility", 1)
            # cmds.setAttr("ribbonAutomation.visibility", 1)
            cmds.select("C_root_JNT", hierarchy=True)
            for obj in cmds.ls(selection=True):
                cmds.setAttr(f"{obj}.displayLocalAxis", 1)
            cmds.select(clear=True)
    # Show all
    cmds.viewFit(all=True)
