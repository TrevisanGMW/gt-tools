import gt.core.attr as core_attr
import gt.core.math as core_math
import gt.core.node as core_node
import gt.core.color as core_color
import gt.core.naming as core_naming
import gt.core.rigging as core_rigging
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


class ModuleChain(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_chain
    allow_parenting = True

    def __init__(
        self,
        name="Chain",
        prefix=core_naming.NamingConstants.Prefix.CENTER,
        suffix=None,
        chain_num=1,
        rot_order=0,
        ctrl_shapes="_circle_pos_x",
    ):
        """
        Initializes A generic chain module.

        This module manages a chain of proxies representing joints or controls arranged
        in a linear chain. It supports customization of chain length, rotation order,
        control shapes, and orientation.

        Args:
            name (str): The name of the chain module. Default is "Chain".
            prefix (str): Prefix used for naming, defaults to center prefix.
            suffix (str or None): Optional suffix for naming.
            chain_num (int): Number of intermediate proxies in the chain. Default is 1.
            rot_order (int): Rotation order to apply to proxies. Default is 0.
            ctrl_shapes (str): Shape used for the control proxies. Default is "_circle_pos_x".

        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        # Set Extra Module Attrs
        self.setup_name = name.lower()
        self.chain_base_name = f"{self.setup_name}01"
        self.chain_num = chain_num
        self.rot_order = rot_order
        self.ctrl_shapes = ctrl_shapes
        self._refresh_middle_proxies = False

        # Orientation
        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(0, 0, 1))
        self.set_orientation(orientation_data=_orientation)

        self.chain_base_proxy = tools_rig_frm.Proxy(name=self.chain_base_name)
        pos_chain_base = core_trans.Vector3(x=0, y=0, z=0)
        self.chain_base_proxy.set_initial_position(xyz=pos_chain_base)
        self.chain_base_proxy.set_locator_scale(scale=1.5)
        self.chain_base_proxy.set_meta_purpose(value=self.chain_base_name)
        self.chain_base_proxy.set_rotation_order(rotation_order=self.rot_order)
        self.chain_base_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )

        self.chain_end_proxy = tools_rig_frm.Proxy()  # the correct name and meta purpose will be set with set_chain_num
        pos_chain_end = core_trans.Vector3(x=20, y=0, z=0)
        self.chain_end_proxy.set_initial_position(xyz=pos_chain_end)
        self.chain_end_proxy.set_locator_scale(scale=1.5)
        self.chain_end_proxy.set_rotation_order(rotation_order=rot_order)
        self.chain_end_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )

        # In-betweens
        self.chain_proxies = []
        self.set_chain_num(chain_num=self.chain_num)

    def set_chain_num(self, chain_num):
        """
        Set a new number of chain proxies. These are the proxies in-between the chain base proxy and chain end proxy
        Args:
            chain_num (int): New number of joints to exist in-between base and end.
                             Minimum is zero (0) - No negative numbers.
        """
        chain_len = len(self.chain_proxies)
        # Same as current, skip
        if chain_len == chain_num:
            return

        # set the right chest name
        chain_end_name = f"{self.setup_name}{str(chain_num + 2).zfill(2)}"
        self.chain_end_proxy.set_name(name=chain_end_name)
        self.chain_end_proxy.set_meta_purpose(value=chain_end_name)

        # New number higher than current - Add more proxies
        if chain_len < chain_num:
            # Determine Initial Parent
            if self.chain_proxies:
                _parent_uuid = self.chain_proxies[-1].get_uuid()
            else:
                _parent_uuid = self.chain_base_proxy.get_uuid()
            # Create new spines
            for num in range(chain_len, chain_num):
                new_chain_name = f"{self.setup_name + str(num + 2).zfill(2)}"
                new_chain = tools_rig_frm.Proxy(name=new_chain_name)
                new_chain.set_locator_scale(scale=1)
                new_chain.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
                new_chain.set_meta_purpose(value=new_chain_name)
                new_chain.add_line_parent(line_parent=_parent_uuid)
                new_chain.set_parent_uuid(uuid=_parent_uuid)
                new_chain.add_driver_type(
                    driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
                )
                new_chain.set_rotation_order(rotation_order=self.rot_order)
                _parent_uuid = new_chain.get_uuid()
                self.chain_proxies.append(new_chain)
        # New number lower than current - Remove unnecessary proxies
        elif len(self.chain_proxies) > chain_num:
            self.chain_proxies = self.chain_proxies[:chain_num]  # Truncate the list

        if self.chain_proxies:
            self.chain_end_proxy.add_line_parent(line_parent=self.chain_proxies[-1].get_uuid())
        else:
            self.chain_end_proxy.add_line_parent(line_parent=self.chain_base_proxy.get_uuid())

        self.refresh_proxies_list()

    def set_rot_order(self, rot_order):
        """
        Set the rotation order for all proxies in the chain, including the base, intermediate, and end proxies.

        Args:
            rot_order (str or int): The rotation order to apply to each proxy. This should be in a format
                accepted by the proxy's `set_rotation_order` method (e.g., a string like "xyz" or an integer code).
        """
        all_chain = [self.chain_base_proxy] + self.chain_proxies + [self.chain_end_proxy]
        for proxy in all_chain:
            proxy.set_rotation_order(rot_order)
        self.refresh_proxies_list()

    def refresh_proxies_list(self):
        """
        Refreshes the main proxies list used by the module during build (update in case objects were updated)
        """
        self.proxies = [self.chain_base_proxy]
        self.proxies.extend(self.chain_proxies)
        self.proxies.append(self.chain_end_proxy)

    def set_proxies_name(self, name):
        """
        Rename the chain proxies using a given base name with an incremental numeric suffix.

        Args:
            name (str): The base name to assign to the proxies.
        """
        self.chain_base_proxy.set_name(f"{name}01")
        for proxy in self.chain_proxies:
            proxy.set_name(f"{name + str(self.chain_proxies.index(proxy) + 2).zfill(2)}")
        self.chain_end_proxy.set_name(f"{name+ str(len(self.chain_proxies) + 2).zfill(2)}")
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
        # Determine Number of Chain Proxies
        _chain_num = 0
        chain_pattern = r"chain\d+"
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(tools_rig_const.RiggerConstants.META_PROXY_PURPOSE)
                if bool(re.match(chain_pattern, meta_type)):
                    _chain_num += 1

        # the chain_end (last joint of the chain) is called with the same pattern (chain + num)
        # chain num indicates the number of middle joints
        _chain_num = _chain_num - 2
        self.set_chain_num(_chain_num)

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

    def align_proxies_to_joints(self):
        """
        Aligns the proxies to the joints transformations.
        """
        chain_base_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.chain_base_proxy.get_uuid())
        chain_end_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.chain_end_proxy.get_uuid())
        middle_chain_proxy_list = [tools_rig_utils.find_proxy_from_uuid(prx.get_uuid()) for prx in self.chain_proxies]
        chain_base_jnt = tools_rig_utils.find_joint_from_uuid(self.chain_base_proxy.get_uuid())
        chain_end_jnt = tools_rig_utils.find_joint_from_uuid(self.chain_end_proxy.get_uuid())
        middle_chain_jnt_list = [tools_rig_utils.find_joint_from_uuid(prx.get_uuid()) for prx in self.chain_proxies]

        # order: base, end, middle ones
        core_trans.match_translate(source=chain_base_jnt, target_list=chain_base_proxy_item)
        core_trans.match_translate(source=chain_end_jnt, target_list=chain_end_proxy_item)
        [
            core_trans.match_translate(source=jnt, target_list=prx)
            for prx, jnt in zip(middle_chain_proxy_list, middle_chain_jnt_list)
        ]

    def build_proxy(self, **kwargs):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of tools_rig_frm.ProxyData objects. These objects describe the created proxy elements.
        """
        if self.parent_uuid:
            if self.chain_base_proxy:
                self.chain_base_proxy.set_parent_uuid(self.parent_uuid)
        self.chain_end_proxy.set_setup_driver_uuid(self.chain_base_proxy.get_uuid())
        self.chain_end_proxy.set_parent_uuid(self.chain_base_proxy.get_uuid())
        if self.chain_proxies:
            prx_driver = self.chain_base_proxy
            for prx in self.chain_proxies:
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
        chain_base = tools_rig_utils.find_proxy_from_uuid(self.chain_base_proxy.get_uuid())
        chain_end = tools_rig_utils.find_proxy_from_uuid(self.chain_end_proxy.get_uuid())
        reset_middle_transforms = self._refresh_middle_proxies
        proxies = []
        for chain in self.chain_proxies:
            chain_node = tools_rig_utils.find_proxy_from_uuid(chain.get_uuid())
            proxies.append(chain_node)
        self.chain_base_proxy.apply_offset_transform()
        self.chain_end_proxy.apply_offset_transform()

        proxy_offsets = []
        for proxy in proxies:
            offset = tools_rig_utils.get_proxy_offset(proxy)
            if reset_middle_transforms:
                cmds.move(0, 0, 0, offset, a=True)
                cmds.rotate(0, 0, 0, offset, a=True)
                cmds.move(0, 0, 0, proxy, a=True)
                cmds.rotate(0, 0, 0, proxy, a=True)
            proxy_offsets.append(offset)
        core_cnstr.equidistant_constraints(start=chain_base, end=chain_end, target_list=proxy_offsets)

        self.chain_base_proxy.apply_transforms()
        self.chain_end_proxy.apply_transforms()
        if not reset_middle_transforms:
            for chain in self.chain_proxies:
                chain.apply_transforms()
        cmds.select(clear=True)

        # Set proxy parent for the skeleton hierarchy
        prx_parent = self.chain_base_proxy
        for prx in self.chain_proxies:
            prx.set_parent_uuid(prx_parent.get_uuid())
            prx_parent = prx
        self.chain_end_proxy.set_parent_uuid(self.chain_proxies[-1].get_uuid())

        if self._refresh_middle_proxies:
            self._refresh_middle_proxies = False

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
        self.chain_end_proxy.set_parent_uuid(uuid=self.chain_end_proxy.get_meta_parent_uuid())
        super().build_skeleton_hierarchy()  # Passthrough
        self.chain_end_proxy.clear_parent_uuid()

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        # Get Joints
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        chain_base_jnt = tools_rig_utils.find_joint_from_uuid(self.chain_base_proxy.get_uuid())
        chain_end_jnt = tools_rig_utils.find_joint_from_uuid(self.chain_end_proxy.get_uuid())
        chain_middle_jnt_list = [tools_rig_utils.find_joint_from_uuid(prx.get_uuid()) for prx in self.chain_proxies]
        spine_jnt_list = [chain_base_jnt] + chain_middle_jnt_list + [chain_end_jnt]
        module_parent_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())

        # Get Formatted Prefix
        _prefix = ""
        if self.prefix:
            _prefix = f"{self.prefix}_"

        # Setup groups
        joint_automation_group = tools_rig_utils.find_or_create_joint_automation_group()
        core_hrchy.parent(source_objects=module_parent_jnt, target_parent=joint_automation_group)
        cmds.setAttr(f"{joint_automation_group}.visibility", 0)

        # Set joints colors
        core_color.set_color_viewport(obj_list=spine_jnt_list, rgb_color=core_color.ColorConstants.RigJoint.GENERAL)

        # Get chain scale
        chain_scale = core_math.dist_center_to_center(chain_base_jnt, chain_end_jnt)

        # Create Automation Skeletons (FK)
        if module_parent_jnt:
            chain_base_parent = module_parent_jnt
        else:
            chain_base_parent = joint_automation_group

        chain_base_fk_jnt = core_rigging.duplicate_joint_for_automation(
            chain_base_jnt, suffix="fk", parent=chain_base_parent
        )
        core_cnstr.constraint_targets(chain_base_fk_jnt, chain_base_jnt)
        mid_chain_jnts = []
        last_chain_parent = chain_base_fk_jnt
        for jnt in chain_middle_jnt_list:
            mid_chain_joint = core_rigging.duplicate_joint_for_automation(jnt, suffix="fk", parent=last_chain_parent)
            core_cnstr.constraint_targets(mid_chain_joint, jnt)
            last_chain_parent = mid_chain_joint
            mid_chain_jnts.append(mid_chain_joint)
        chain_end_fk_jnt = core_rigging.duplicate_joint_for_automation(
            chain_end_jnt, suffix="fk", parent=last_chain_parent
        )
        core_cnstr.constraint_targets(chain_end_fk_jnt, chain_end_jnt)
        fk_joints = [chain_base_fk_jnt] + mid_chain_jnts + [chain_end_fk_jnt]
        core_rigging.rescale_joint_radius(
            joint_list=fk_joints,
            multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_FK,
        )
        core_color.set_color_viewport(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigJoint.FK)
        core_color.set_color_outliner(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigOutliner.FK)

        # FK Controls ----------------------------------------------------------------------------------------
        chain_base_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.chain_base_proxy.get_uuid())
        chain_rotation_order = cmds.getAttr(f"{chain_base_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        chain_base_ctrl, chain_base_parent_groups = self.create_rig_control(
            control_base_name=self.chain_base_proxy.get_name(),
            curve_file_name=self.ctrl_shapes,
            parent_obj=global_offset_ctrl,
            match_obj=chain_base_jnt,
            add_offset_ctrl=False,
            rot_order=chain_rotation_order,
            shape_scale=chain_scale * 0.4,
            color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=chain_base_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.chain_base_proxy,
        )
        core_attr.hide_lock_default_attrs(obj_list=chain_base_ctrl, scale=True, visibility=True)
        core_cnstr.constraint_targets(source_driver=chain_base_ctrl, target_driven=chain_base_fk_jnt)

        chain_fk_ctrls = []
        last_mid_parent_ctrl = chain_base_ctrl
        for chain_proxy, fk_jnt in zip(self.chain_proxies, mid_chain_jnts):
            chain_proxy_item = tools_rig_utils.find_proxy_from_uuid(chain_proxy.get_uuid())
            chain_rotation_order = cmds.getAttr(f"{chain_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
            chain_fk_ctrl, chain_fk_parent_groups = self.create_rig_control(
                control_base_name=chain_proxy.get_name(),
                curve_file_name=self.ctrl_shapes,
                parent_obj=last_mid_parent_ctrl,
                match_obj=fk_jnt,
                rot_order=chain_rotation_order,
                shape_scale=chain_scale * 0.25,
                color=core_color.ColorConstants.RGB.BLUE_SKY,
            )[:2]
            self._add_driver_uuid_attr(
                target_driver=chain_fk_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=chain_proxy,
            )
            # -- attributes
            core_attr.hide_lock_default_attrs(chain_fk_ctrl, scale=True, visibility=True)
            # -- constraint
            core_cnstr.constraint_targets(source_driver=chain_fk_ctrl, target_driven=fk_jnt)
            last_mid_parent_ctrl = chain_fk_ctrl
            chain_fk_ctrls.append(chain_fk_ctrl)

        chain_end_proxy_item = tools_rig_utils.find_proxy_from_uuid(self.chain_end_proxy.get_uuid())
        chain_end_rotation_order = cmds.getAttr(
            f"{chain_end_proxy_item}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}"
        )
        chain_end_ctrl, chain_end_parent_groups = self.create_rig_control(
            control_base_name=self.chain_end_proxy.get_name(),
            curve_file_name=self.ctrl_shapes,
            parent_obj=last_mid_parent_ctrl,
            match_obj=chain_end_jnt,
            add_offset_ctrl=False,
            rot_order=chain_end_rotation_order,
            shape_scale=chain_scale * 0.4,
            color=core_color.ColorConstants.RGB.GREEN_LAWN_GREEN,
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=chain_end_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.chain_end_proxy,
        )
        core_attr.hide_lock_default_attrs(obj_list=chain_end_ctrl, scale=True, visibility=True)
        core_cnstr.constraint_targets(source_driver=chain_end_ctrl, target_driven=chain_end_fk_jnt)

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = chain_base_parent_groups


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

    a_root = tools_rig_mod_root.ModuleRoot()
    a_chain = ModuleChain(rot_order=1)

    root_uuid = a_root.root_proxy.get_uuid()
    a_chain.set_parent_uuid(root_uuid)
    a_chain.set_chain_num(10)

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_chain)

    a_project.build_proxy()
    # a_project.build_skeleton()
    # a_project.build_rig()

    # Show all
    cmds.viewFit(all=True)
