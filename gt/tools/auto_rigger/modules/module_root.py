"""
Auto Rigger Root Module
"""

import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.rigging as core_rigging
import gt.core.transform as core_trans
import gt.core.naming as core_naming
import gt.core.color as core_color
import gt.core.attr as core_attr
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleRoot(tools_rig_frm.ModuleGeneric):
    __version__ = "1.1.0"
    icon = ui_res_lib.Icon.rigger_module_root
    allow_parenting = False

    def __init__(self, name="Root", prefix=core_naming.NamingConstants.Prefix.CENTER, suffix=None):
        """
        Initializes the Root module.

        Args:
            name (str, optional): Name of the module. Defaults to "Root".
            prefix (str, optional): Naming prefix, commonly used for side designation
                (e.g., center, left, right). Defaults to NamingConstants.Prefix.CENTER.
            suffix (str, optional): Optional suffix for the module name. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.set_orientation_method(method="inherit")

        self.set_extra_callable_function(self.enable_root_scale, order=tools_rig_frm.CodeData.Order.post_build)

        # Root Proxy
        self.root_proxy = tools_rig_frm.Proxy(name="root")
        self.root_proxy.set_locator_scale(scale=3)
        self.root_proxy.set_meta_purpose(value="root")
        self.root_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.BLOCK,
                tools_rig_const.RiggerDriverTypes.FK,
            ]
        )

        self.matches_proxy_rot = False
        self.enable_scale = False

        self.root_proxy.add_color(core_color.ColorConstants.RigProxy.TWEAK)

        self.proxies = [self.root_proxy]

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

    # --------------------------------------------------- Misc ---------------------------------------------------
    def build_proxy(self, **kwargs):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        if self.parent_uuid:
            self.root_proxy.set_parent_uuid(self.parent_uuid)

        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        Creates leg proxy behavior through constraints and offsets.
        """
        super().build_proxy_setup()  # Passthrough
        # Root Visibility Setup
        proxy_global_ctrl = tools_rig_utils.find_ctrl_global_proxy()
        root = tools_rig_utils.find_proxy_from_uuid(self.root_proxy.get_uuid())
        root_lines = tools_rig_utils.find_vis_lines_from_uuid(parent_uuid=self.root_proxy.get_uuid())

        core_attr.add_attr(obj_list=str(proxy_global_ctrl), attributes="rootVisibility", attr_type="bool", default=True)
        root_shapes = cmds.listRelatives(str(root), shapes=True, fullPath=True) or []
        for line in list(root_lines) + root_shapes:
            cmds.connectAttr(f"{proxy_global_ctrl}.rootVisibility", f"{line}.visibility")

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        root_jnt = tools_rig_utils.find_joint_from_uuid(self.root_proxy.get_uuid())
        root_proxy = tools_rig_utils.find_proxy_from_uuid(self.root_proxy.get_uuid())
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()

        # Create root control
        root_rotation_order = cmds.getAttr(f"{root_proxy}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")

        _match_obj_rot = None
        if self.matches_proxy_rot:
            _match_obj_rot = root_jnt

        root_ctrl, root_offset, *_ = self.create_rig_control(
            control_base_name=self.root_proxy.get_name(),
            curve_file_name="_sphere_joint_arrow_pos_z",
            parent_obj=global_offset_ctrl,
            match_obj_pos=root_jnt,
            match_obj_rot=_match_obj_rot,
            rot_order=root_rotation_order,
            color=core_color.ColorConstants.RigProxy.TWEAK,
        )

        self._add_driver_uuid_attr(
            target_driver=root_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.root_proxy,
        )
        core_attr.hide_lock_default_attrs(obj_list=root_ctrl, scale=True, visibility=True)
        core_cnstr.constraint_targets(source_driver=root_ctrl, target_driven=root_jnt)

        # Follow setup
        core_attr.add_separator_attr(target_object=root_ctrl, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE)
        tools_rig_utils.create_follow_setup(
            control=root_ctrl,
            parent=global_offset_ctrl,
            attr_name="followGlobalOffset",
            constraint_type="parent",
            default_value=0,
        )

    def enable_root_scale(self):
        """
        Enable uniform scale behavior for the rig's joint hierarchy.

        This function ensures that the skeleton's scaling is driven
        by the  root joint rather than by the skeleton group
        transformations.
        """
        if self.enable_scale:
            root_jnt = tools_rig_utils.find_joint_from_uuid(self.root_proxy.get_uuid())
            skeleton_grp = tools_rig_utils.find_skeleton_group()
            cmds.select(root_jnt, hierarchy=True, replace=True)
            root_and_children_joints = cmds.ls(selection=True, typ="joint", long=True)
            cmds.select(clear=True)
            for a_jnt in root_and_children_joints:
                cmds.setAttr(f"{a_jnt}.segmentScaleCompensate", 0)
            core_attr.set_attr(f"{root_jnt}.inheritsTransform", value=0)
            cmds.connectAttr(f"{skeleton_grp}.scale", f"{root_jnt}.scale")


if __name__ == "__main__":  # pragma: no cover
    logger.setLevel(logging.DEBUG)

    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    import gt.core.session as core_session

    core_session.remove_modules_startswith("gt.tools.auto_rigger.module")
    core_session.remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject

    # Reload Modules
    import gt.tools.auto_rigger.modules.module_spine as tools_rig_mod_spine
    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.core.rigging as core_rigging
    import gt.core.naming as core_naming
    import importlib

    importlib.reload(tools_rig_mod_spine)
    importlib.reload(tools_rig_fmr)
    importlib.reload(core_rigging)
    importlib.reload(core_naming)

    a_module = tools_rig_frm.ModuleGeneric()
    a_proxy = a_module.add_new_proxy()
    a_proxy.set_initial_position(x=5)
    a_root = ModuleRoot()
    a_root_two = ModuleRoot()
    # a_root_two.root_proxy.set_name("rootTwo")  # turn on to test unique elements
    # a_root_two.root_proxy.set_initial_position(x=10)

    a_root_two.root_proxy.set_initial_transform(core_trans.Transform(position=(10, 0, 0), rotation=(30, 0, 0)))
    a_proxy.set_parent_uuid_from_proxy(a_root.proxies[0])
    a_project = RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_module)
    a_project.add_to_modules(a_root_two)
    a_project.build_proxy()
    a_project.build_rig()

    a_project.read_data_from_scene()
    dictionary = a_project.get_project_as_dict()

    cmds.file(new=True, force=True)
    a_project2 = RigProject()

    a_project2.read_data_from_dict(dictionary)
    a_project2.build_proxy()
    a_project2.build_rig()

    # Show all
    cmds.viewFit(all=True)
