"""
Auto Rigger Piston Module
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.transform as core_trans
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


class ModulePiston(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_piston
    allow_parenting = True
    allow_multiple = True

    def __init__(
        self,
        name="Piston",
        prefix=core_naming.NamingConstants.Prefix.CENTER,
        suffix=None,
        ctrl_shapes="_circle_pos_y",
        parent_end_joint=False,
        end_parent=None,
    ):
        """
        Initializes a Piston module.

        Args:
            name (str): Name of the module.
            prefix (str or None): Optional prefix for naming.
            suffix (str or None): Optional suffix for naming.
            ctrl_shapes (str): Control shape name or identifier.
            parent_end_joint (bool): If we want the parent joint parented under the base joint.
            end_parent (str, optional): Specify the parent uu of the end ctrl if different.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)
        self.set_extra_callable_function(self._build_constraints, order=tools_rig_frm.CodeData.Order.post_build)
        self._jnts = []
        self._ctrls = []

        # Set Extra Module Attrs
        self.setup_name = name.lower()
        self.proxy_inherit_name = True
        self.parent_end_joint = parent_end_joint
        self.piston_base_name = f"{self.setup_name}Base"
        self.piston_end_name = f"{self.setup_name}End"
        self.piston_twist_target_name = f"{self.setup_name}Up"
        self.ctrl_shapes = ctrl_shapes
        self.end_parent = end_parent
        self._module_end_driver = None

        # Orientation
        self.set_orientation_method(tools_rig_frm.OrientationData.Methods.inherit)

        self.piston_base_proxy = tools_rig_frm.Proxy(name=self.piston_base_name)
        pos_piston_base = core_trans.Vector3(x=0, y=0, z=0)
        self.piston_base_proxy.set_initial_position(xyz=pos_piston_base)
        self.piston_base_proxy.set_locator_scale(scale=1.5)
        self.piston_base_proxy.set_meta_purpose(value=self.piston_base_name)
        self.piston_base_proxy.set_rotation_order(rotation_order=0)
        self.piston_base_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )

        self.piston_end_proxy = tools_rig_frm.Proxy(name=self.piston_end_name)
        pos_piston_end = core_trans.Vector3(x=0, y=10, z=0)
        self.piston_end_proxy.set_initial_position(xyz=pos_piston_end)
        self.piston_end_proxy.set_locator_scale(scale=1.5)
        self.piston_end_proxy.set_meta_purpose(value=self.piston_end_name)
        self.piston_end_proxy.set_rotation_order(rotation_order=0)
        self.piston_end_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )

        self.piston_twist_target_proxy = tools_rig_frm.Proxy(name=self.piston_twist_target_name)
        piston_twist_target = core_trans.Vector3(x=7, y=5, z=0)
        self.piston_twist_target_proxy.set_initial_position(xyz=piston_twist_target)
        self.piston_twist_target_proxy.set_locator_scale(scale=1.5)
        self.piston_twist_target_proxy.set_meta_purpose(value=self.piston_twist_target_name)
        self.piston_twist_target_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.PIVOT)
        self.piston_twist_target_proxy.set_rotation_order(rotation_order=0)
        self.piston_twist_target_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )

        self.proxies = [self.piston_end_proxy, self.piston_base_proxy, self.piston_twist_target_proxy]

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

    def set_proxies_name(self, name):
        """
        Sets a new name for the proxies found in this ribbon.
        Args:
            name (str): A new name to use in the renaming of the elements.
        """
        self.setup_name = name
        self.piston_base_name = f"{self.setup_name}Base"
        self.piston_end_name = f"{self.setup_name}End"
        self.piston_twist_target_name = f"{self.setup_name}Up"
        self.piston_base_proxy.set_name(f"{name}Base")
        self.piston_end_proxy.set_name(f"{name}End")
        self.piston_twist_target_proxy.set_name(f"{name}Up")
        self.refresh_proxies_list()

    def refresh_proxies_list(self):
        """
        Refreshes the main proxies list used by the module during build (update in case objects were updated)
        """
        self.proxies = [self.piston_base_proxy]
        self.proxies.append(self.piston_end_proxy)
        self.proxies.append(self.piston_twist_target_proxy)

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
        if self.parent_uuid:
            if self.piston_base_proxy:
                self.piston_base_proxy.set_parent_uuid(self.parent_uuid)
        self.piston_twist_target_proxy.set_parent_uuid(uuid=self.piston_base_proxy.get_uuid())
        self.piston_twist_target_proxy.set_setup_driver_uuid(uuid=self.piston_base_proxy.get_uuid())
        self.piston_end_proxy.set_parent_uuid(uuid=self.piston_base_proxy.get_uuid())
        self.piston_end_proxy.set_setup_driver_uuid(uuid=self.piston_base_proxy.get_uuid())

        proxy = super().build_proxy(**kwargs)  # Passthrough

        if self.end_parent:
            if self.piston_end_proxy:
                self.piston_end_proxy.set_setup_driver_uuid(uuid=self.end_parent)
                self.piston_end_proxy.set_parent_uuid(uuid=self.end_parent)
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """

        self.piston_base_proxy.apply_offset_transform()
        self.piston_end_proxy.apply_offset_transform()
        self.piston_twist_target_proxy.apply_offset_transform()

        # Apply transform after set the order with build_proxy_setup parent function
        super().build_proxy_setup()  # Passthrough

    def build_skeleton_hierarchy(self):
        """
        Runs skeletal hierarchy phase (post skeleton). Joints are parented and oriented during this step.
        Happens after the "build_skeleton_joints" function in a project.
        """

        super().build_skeleton_hierarchy()  # Passthrough

        piston_base_jnt = tools_rig_utils.find_joint_from_uuid(self.piston_base_proxy.get_uuid())
        piston_end_jnt = tools_rig_utils.find_joint_from_uuid(self.piston_end_proxy.get_uuid())
        piston_twist_target_jnt = tools_rig_utils.find_joint_from_uuid(self.piston_twist_target_proxy.get_uuid())
        # Create connection between parent_top_joint attr and piston_base_jnt
        if self.parent_end_joint:
            core_hrchy.parent(source_objects=piston_end_jnt, target_parent=piston_base_jnt)
        # Delete piston_twist_target_jnt
        cmds.delete(piston_twist_target_jnt)

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        piston_base_jnt = tools_rig_utils.find_joint_from_uuid(self.piston_base_proxy.get_uuid())
        piston_end_jnt = tools_rig_utils.find_joint_from_uuid(self.piston_end_proxy.get_uuid())
        piston_base_proxy = tools_rig_utils.find_proxy_from_uuid(self.piston_base_proxy.get_uuid())
        piston_end_proxy = tools_rig_utils.find_proxy_from_uuid(self.piston_end_proxy.get_uuid())
        piston_twist_target_proxy = tools_rig_utils.find_proxy_from_uuid(self.piston_twist_target_proxy.get_uuid())
        piston_scale = core_math.dist_center_to_center(piston_base_jnt, piston_end_jnt)

        # Create piston_base control
        piston_base_rotation_order = cmds.getAttr(
            f"{piston_base_proxy}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}"
        )
        piston_base_ctrl, piston_base_offset = self.create_rig_control(
            control_base_name=self.piston_base_name,
            curve_file_name=self.ctrl_shapes,
            parent_obj=global_offset_ctrl,
            match_obj_pos=piston_base_jnt,
            match_obj_rot=piston_base_jnt,
            rot_order=piston_base_rotation_order,
            shape_scale=piston_scale * 0.2,
            color=core_color.ColorConstants.RigJoint.GENERAL,
        )[:2]

        self._add_driver_uuid_attr(
            target_driver=piston_base_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.piston_base_proxy,
        )
        core_attr.hide_lock_default_attrs(obj_list=piston_base_ctrl, scale=True, visibility=True)

        # Create piston_end control
        if self.end_parent:
            piston_ctrl_end_parent = self.end_parent
        else:
            piston_ctrl_end_parent = global_offset_ctrl
        piston_end_rotation_order = cmds.getAttr(f"{piston_end_proxy}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        piston_end_ctrl, piston_end_offset = self.create_rig_control(
            control_base_name=self.piston_end_name,
            curve_file_name=self.ctrl_shapes,
            parent_obj=piston_ctrl_end_parent,
            match_obj_pos=piston_end_jnt,
            match_obj_rot=piston_end_jnt,
            rot_order=piston_end_rotation_order,
            shape_scale=piston_scale * 0.2,
            color=core_color.ColorConstants.RigJoint.GENERAL,
        )[:2]

        self._add_driver_uuid_attr(
            target_driver=piston_end_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.piston_end_proxy,
        )
        core_attr.hide_lock_default_attrs(obj_list=piston_end_ctrl, scale=True, visibility=True)

        # Create piston_twist_target control
        piston_twist_target_order = cmds.getAttr(
            f"{piston_twist_target_proxy}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}"
        )
        piston_twist_target_ctrl, piston_twist_target_offset = self.create_rig_control(
            control_base_name=self.piston_twist_target_name,
            curve_file_name=self.ctrl_shapes,
            parent_obj=global_offset_ctrl,
            match_obj_pos=piston_twist_target_proxy,
            match_obj_rot=piston_twist_target_proxy,
            rot_order=piston_twist_target_order,
            shape_scale=piston_scale * 0.1,
            color=core_color.ColorConstants.RigProxy.PIVOT,
        )[:2]

        self._add_driver_uuid_attr(
            target_driver=piston_twist_target_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.piston_twist_target_proxy,
        )
        core_attr.hide_lock_default_attrs(obj_list=piston_twist_target_ctrl, scale=True, visibility=True)

        self._jnts = [piston_base_jnt, piston_end_jnt]
        self._ctrls = [piston_base_ctrl, piston_end_ctrl, piston_twist_target_ctrl, piston_twist_target_offset]
        self.module_children_drivers = [piston_base_offset[0], piston_twist_target_offset[0]]
        self._module_end_driver = piston_end_offset[0]

    def build_rig_post(self):
        """
        Runs post rig script phase.
        This step runs after the execution of "build_rig" is completed.
        Usually used to define automation or connections that require external elements to exist.
        """
        logger.debug(f'"build_rig" function from "{self.get_module_class_name()}" was called.')
        if self.end_parent:
            module_end_parent_jnt = tools_rig_utils.find_joint_from_uuid(self.end_parent)
            if module_end_parent_jnt:
                drivers = tools_rig_utils.find_drivers_from_joint(
                    module_end_parent_jnt, as_list=True, create_missing_generic=True, skip_block_drivers=True
                )
                if drivers:
                    core_hrchy.parent(source_objects=self._module_end_driver, target_parent=drivers[0])
        else:
            self.module_children_drivers = self.module_children_drivers + [self._module_end_driver]
        self._parent_module_children_drivers()

    def _build_constraints(self):
        """
        Builds constraint setup, done after building the rig to avoid orientation issues.
        """
        tools_rig_utils.set_rig_apose()
        piston_base_jnt = self._jnts[0]
        piston_end_jnt = self._jnts[1]
        piston_base_ctrl = self._ctrls[0]
        piston_end_ctrl = self._ctrls[1]
        piston_twist_target_ctrl = self._ctrls[2]
        piston_twist_target_offset = self._ctrls[3]

        # Create Locators
        # Base Loc
        cmds.xform(piston_base_jnt, query=True, worldSpace=False, translation=True)
        base_locator_name = core_node.get_short_name(piston_base_jnt).split("_JNT")[0]
        base_locator = cmds.spaceLocator(name=f"{base_locator_name}_locator")[0]
        base_locator = core_node.Node(base_locator)
        core_trans.match_translate(source=piston_base_jnt, target_list=base_locator)

        # End Loc
        cmds.xform(piston_end_jnt, query=True, worldSpace=False, translation=True)
        end_locator_name = core_node.get_short_name(piston_end_jnt).split("_JNT")[0]
        end_locator = cmds.spaceLocator(name=f"{end_locator_name}_locator")[0]
        end_locator = core_node.Node(end_locator)
        core_trans.match_translate(source=piston_end_jnt, target_list=end_locator)

        # Automation Grp
        locator_automation_grp = core_hrchy.create_group(name=f"{self.prefix}_{self.setup_name}_locator_automation_grp")
        general_automation_grp = tools_rig_utils.get_automation_group()
        core_hrchy.parent(source_objects=base_locator, target_parent=locator_automation_grp)
        core_hrchy.parent(source_objects=end_locator, target_parent=locator_automation_grp)
        core_hrchy.parent(source_objects=locator_automation_grp, target_parent=general_automation_grp)
        cmds.setAttr(f"{locator_automation_grp}.visibility", 0)
        # Aim Constraints - locator to locator
        core_cnstr.constraint_targets(
            source_driver=base_locator,
            target_driven=end_locator,
            constraint_type="aim",
            maintain_offset=False,
            worldUpObject=piston_twist_target_ctrl,
            worldUpType="object",
        )

        core_cnstr.constraint_targets(
            source_driver=end_locator,
            target_driven=base_locator,
            constraint_type="aim",
            maintain_offset=False,
            worldUpObject=piston_twist_target_ctrl,
            worldUpType="object",
        )

        # Point Constraints - Ctrl to locator
        core_cnstr.constraint_targets(
            source_driver=piston_base_ctrl,
            target_driven=base_locator,
            constraint_type="point",
            maintain_offset=True,
        )

        core_cnstr.constraint_targets(
            source_driver=piston_end_ctrl,
            target_driven=end_locator,
            constraint_type="point",
            maintain_offset=True,
        )

        # Parent Constraints - Locator to joint
        core_cnstr.constraint_targets(
            source_driver=base_locator,
            target_driven=piston_base_jnt,
            constraint_type="parent",
            maintain_offset=True,
        )

        core_cnstr.constraint_targets(
            source_driver=end_locator,
            target_driven=piston_end_jnt,
            constraint_type="parent",
            maintain_offset=True,
        )

        # Twist Controls constraint
        core_cnstr.constraint_targets(
            source_driver=piston_base_ctrl,
            target_driven=piston_twist_target_offset,
            constraint_type="parent",
            maintain_offset=True,
        )
        core_cnstr.constraint_targets(
            source_driver=piston_end_ctrl,
            target_driven=piston_twist_target_offset,
            constraint_type="parent",
            maintain_offset=True,
        )
        tools_rig_utils.set_rig_tpose()


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)

    import gt.core.session as core_session

    core_session.remove_modules_startswith("gt.tools.auto_rigger.module")
    core_session.remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils

    import gt.tools.auto_rigger.modules.module_root as tools_rig_mod_root
    import gt.tools.auto_rigger.modules.module_biped_arm as tools_rig_mod_arm
    import importlib

    importlib.reload(tools_rig_mod_root)
    importlib.reload(tools_rig_fmr)
    importlib.reload(tools_rig_utils)

    a_piston = ModulePiston()
    an_arm = tools_rig_mod_arm.ModuleBipedArm()

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_piston)

    a_project.build_proxy()
    cmds.setAttr("C_pistonEnd.tx", -25)
    cmds.setAttr("C_pistonEnd.ty", 19)
    cmds.setAttr("C_pistonEnd.rz", 18)
    cmds.setAttr("C_pistonBase.tx", 2)
    cmds.setAttr("C_pistonBase.rz", 30)
    a_project.build_skeleton()
    # a_project.build_rig()
    # obj_1 = cmds.polyCylinder(h=10, sx=3, sy=3, sz=3)
    # obj_2 = cmds.polyCylinder(h=10, r=2, sx=3, sy=3, sz=3)
    # core_trans.match_translate(source="C_piston_end_JNT", target_list="pCylinder1")
    # core_trans.match_translate(source="C_piston_base_JNT", target_list="pCylinder2")

    # Show all
    cmds.viewFit(all=True)
