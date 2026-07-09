import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.hierarchy as core_hrchy
import gt.core.transform as core_trans
import gt.core.iterable as core_iter
import gt.core.naming as core_naming
import gt.core.curve as core_curve
import gt.core.color as core_color
import gt.core.attr as core_attr
import gt.core.node as core_node
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleGenericFK(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_generic_fk
    allow_parenting = True
    DEFAULT_SHAPE = "_circle_pos_x"

    def __init__(self, name="Generic FK", prefix=None, suffix=None, ctrl_color=None, extra_control_parent_groups=None):
        """
        Initialize a Generic FK module.

        Args:
            name (str): Module name.
            prefix (str or None): Naming prefix.
            suffix (str or None): Naming suffix.
            ctrl_color (optional): Color for controls.
            extra_control_parent_groups (optional): Extra control parent groups.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.ctrl_shape = self.DEFAULT_SHAPE
        self.extra_control_parent_groups = extra_control_parent_groups
        self.ctrl_color = ctrl_color
        self.include_scale = False

    def set_control_shape(self, shape):
        """
        Sets a new control shape
        Args:
            shape (str): The name of the control file.
        """
        self.ctrl_shape = shape

    def set_control_color(self, color):
        """
        Sets a new control color
        Args:
            color (str): The name of the color.
        """
        self.ctrl_color = color

    def set_extra_parent_groups(self, groups):
        """
        Set extra control parent groups from a comma-separated string.

        Args:
            groups (str): Comma-separated string of parent group names.
                          Spaces are ignored.
        """
        parent_groups = groups.replace(" ", "")
        unfiltered_parent_groups = parent_groups.split(",")
        filtered_parent_groups = [x for x in unfiltered_parent_groups if x]
        self.extra_control_parent_groups = filtered_parent_groups

    def get_proxies_mirrored(self, **kwargs):
        """
        Mirrors proxy transforms from the opposite side of the rig.

        Args:
            **kwargs: Optional keyword arguments passed to the base implementation.
        """
        if self.get_orientation_method() == self.orientation.Methods.inherit:
            super().get_proxies_mirrored(behaviour=True, specular=False)
        else:
            super().get_proxies_mirrored()

    def build_proxy(self, **kwargs):
        """
        Overrides the proxy build phase, allowing proxy names to be customized via attributes.
        """
        return super().build_proxy(use_naming_attrs=True, **kwargs)  # Allow name overrides

    def build_skeleton_joints(self, **kwargs):
        """
        Overrides the skeletal build phase, allowing joint names to be customized via proxy attributes.
        """
        super().build_skeleton_joints(use_naming_attrs=True)  # Allow name overrides

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        # Helpful Elements
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        module_parent_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())

        # Setup groups
        joint_automation_group = tools_rig_utils.find_or_create_joint_automation_group()
        core_hrchy.parent(source_objects=module_parent_jnt, target_parent=joint_automation_group)
        cmds.setAttr(f"{joint_automation_group}.visibility", 0)

        # Generate Unique Purpose Dict
        names_list = [proxy.get_name() for proxy in self.proxies]
        purpose_list = core_iter.get_unique_name_list(names_list)
        purpose_dict = dict(zip(self.proxies, purpose_list))

        # Define Shape
        _ctrl_shape = self.DEFAULT_SHAPE
        if self.ctrl_shape and core_curve.get_curve(self.ctrl_shape):
            _ctrl_shape = self.ctrl_shape

        # FK Controls ----------------------------------------------------------------------------------------
        fk_controls = []  # Actual Control Transforms (With Curve Shapes Inside)
        offset_groups = []
        parenting_pairs = {}  # To adjust hierarchy after creating
        _module_prefix = self.prefix
        _module_suffix = self.suffix
        _module_color = self.ctrl_color

        for proxy in self.proxies:
            if proxy.get_attr_dict_value(key="prefix") and not None:
                self.prefix = proxy.get_attr_dict_value(key="prefix")
            if proxy.get_attr_dict_value(key="suffix") and not None:
                self.suffix = proxy.get_attr_dict_value(key="suffix")
            _joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            if not self.ctrl_color or self.ctrl_color == "INHERIT COLOR":
                self.ctrl_color = core_color.get_directional_color(object_name=_joint)
            else:
                if not isinstance(self.ctrl_color, (list, tuple)):  # Filtering RBG lists/tuples
                    self.ctrl_color = getattr(core_color.ColorConstants.RGB, self.ctrl_color)
            if not _joint:
                continue  # Missing joint
            _purpose = purpose_dict.get(proxy, "")
            _proxy = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
            _rotation_order = cmds.getAttr(f"{_proxy}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
            _ctrl, _parent_groups = self.create_rig_control(
                control_base_name=proxy.get_name(),
                curve_file_name=_ctrl_shape,
                parent_obj=global_offset_ctrl,
                extra_parent_groups=self.extra_control_parent_groups,
                match_obj=_joint,
                add_offset_ctrl=False,
                rot_order=_rotation_order,
                color=self.ctrl_color,
            )[:2]
            self._add_driver_uuid_attr(
                target_driver=_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=_purpose,
            )

            # Populate Joint Purpose and Driver
            core_attr.set_attr(
                attribute_path=f"{_joint}.{tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE}", value=_purpose
            )
            tools_rig_utils.add_driver_to_joint(target_joint=_joint, new_drivers=tools_rig_const.RiggerDriverTypes.FK)

            # Adjust and Connect Control
            hide_scale = not self.include_scale  # Invert Add Scale
            core_attr.hide_lock_default_attrs(obj_list=_ctrl, scale=hide_scale, visibility=True)
            core_cnstr.constraint_targets(source_driver=_ctrl, target_driven=_joint)
            if self.include_scale:
                core_cnstr.constraint_targets(
                    source_driver=_ctrl,
                    target_driven=_joint,
                    constraint_type=core_cnstr.ConstraintTypes.SCALE,
                )

            # Populate Lists
            offset_group = _parent_groups[0]
            fk_controls.append(_ctrl)
            offset_groups.append(offset_group)
            parenting_pairs[offset_group] = proxy.get_parent_uuid()

            self.prefix = _module_prefix
            self.suffix = _module_suffix
            self.ctrl_color = _module_color

        # Parent Controls --------------------------------------------------------------------------------------
        for offset_group, parent_uuid in parenting_pairs.items():
            if not parent_uuid:
                continue  # No Parent
            _parent_joint = tools_rig_utils.find_joint_from_uuid(parent_uuid)
            if not _parent_joint:
                continue  # Parent joint not found

            _parent_joint_drivers = tools_rig_utils.find_drivers_from_joint(
                _parent_joint, as_list=True, create_missing_generic=True, skip_block_drivers=True
            )
            if _parent_joint_drivers:
                core_hrchy.parent(source_objects=offset_group, target_parent=_parent_joint_drivers[0])

        # Find Control Offsets without Target Parent -----------------------------------------------------------
        offsets_without_parents = [key for key, value in parenting_pairs.items() if value is None]

        # Set Children Drivers ---------------------------------------------------------------------------------
        self.module_children_drivers = offsets_without_parents


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
    a_generic_fk = ModuleGenericFK()
    p1 = a_generic_fk.add_new_proxy()
    p2 = a_generic_fk.add_new_proxy()
    p3 = a_generic_fk.add_new_proxy()
    extra = a_generic_fk.add_new_proxy()

    # Set Initial position
    p1.set_initial_position(x=5)
    p2.set_initial_position(x=10)
    p3.set_initial_position(x=15)
    extra.set_initial_position(z=5)

    # Create Hierarchy
    p1.set_parent_uuid(a_root.root_proxy.get_uuid())
    p2.set_parent_uuid_from_proxy(p1)
    p3.set_parent_uuid_from_proxy(p2)

    root_uuid = a_root.root_proxy.get_uuid()
    a_generic_fk.set_parent_uuid(root_uuid)

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_generic_fk)

    a_project.build_proxy()
    a_project.build_rig()

    # Show all
    cmds.viewFit(all=True)
    cmds.setAttr("skeleton.v", 1)
