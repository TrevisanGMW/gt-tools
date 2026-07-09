"""
Auto Rigger Socket/Attachment Module
"""

import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.rigging as core_rigging
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.core.curve as core_curve
import gt.core.color as core_color
import gt.core.attr as core_attr
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


PURPOSE_SOCKET_PARENT = "socketParent"
PURPOSE_SOCKET_CHILD = "socketChild"


class ModuleSocket(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_socket
    allow_parenting = True

    def __init__(self, name="Socket", prefix=core_naming.NamingConstants.Prefix.CENTER, suffix=None):
        """
        Initializes the Socket module.

        Args:
            name (str, optional): Name of the module. Defaults to "Socket".
            prefix (str, optional): Naming prefix, usually indicating the side
                (e.g., center, left, right). Defaults to NamingConstants.Prefix.CENTER.
            suffix (str, optional): Optional suffix for the module name. Defaults to None.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.set_orientation_method(method=tools_rig_frm.OrientationData.Methods.inherit)

        # Attach Proxy (Parent)
        self.socket_proxy = tools_rig_frm.Proxy(name="socket")
        self.socket_proxy.set_curve(curve=core_curve.get_curve("_sphere_joint_handle"))
        self.socket_proxy.set_meta_purpose(value=PURPOSE_SOCKET_PARENT)
        self.socket_proxy.add_color(core_color.ColorConstants.RigProxy.TWEAK)
        self.socket_proxy.set_initial_position(x=0, y=0, z=0)
        self.socket_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        # Attach Proxy (Child)  - Never built as proxy
        self.socket_child_proxy = tools_rig_frm.Proxy()
        self.socket_child_proxy.set_meta_purpose(value=PURPOSE_SOCKET_CHILD)
        self.socket_child_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.add_child = True
        self.parent_tag = "Parent"
        self.child_tag = "Child"

        self.proxies = [self.socket_proxy]

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
            self.socket_proxy.set_parent_uuid(self.parent_uuid)

        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        Creates leg proxy behavior through constraints and offsets.
        """
        super().build_proxy_setup()  # Passthrough
        self.socket_proxy.apply_offset_transform()
        self.socket_proxy.apply_transforms()

    def build_control_rig_pose(self):
        """
        Builds the rig pose by rounding rotate values to be straight (align with world)
        """
        socket_jnt = tools_rig_utils.find_joint_from_uuid(self.socket_proxy.get_uuid())

        # Get the current joint orientation values
        joint_orient = cmds.getAttr(f"{socket_jnt}.jointOrient")[0]
        joint_rotate = cmds.getAttr(f"{socket_jnt}.rotate")[0]

        # Round each angle to the nearest multiple of 90
        rounded_orient = [round(angle / 90) * 90 for angle in joint_orient]
        rounded_rotate = [round(angle / 90) * 90 for angle in joint_rotate]

        # Set the joint orientation to the new rounded values
        cmds.setAttr(f"{socket_jnt}.jointOrientX", rounded_orient[0])
        cmds.setAttr(f"{socket_jnt}.jointOrientY", rounded_orient[1])
        cmds.setAttr(f"{socket_jnt}.jointOrientZ", rounded_orient[2])
        cmds.setAttr(f"{socket_jnt}.rx", rounded_rotate[0])
        cmds.setAttr(f"{socket_jnt}.ry", rounded_rotate[1])
        cmds.setAttr(f"{socket_jnt}.rz", rounded_rotate[2])

    def build_rig(self, **kwargs):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        socket_proxy = tools_rig_utils.find_proxy_from_uuid(self.socket_proxy.get_uuid())
        socket_jnt = tools_rig_utils.find_joint_from_uuid(self.socket_proxy.get_uuid())
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()

        # Get Useful Attributes
        locator_scale = cmds.getAttr(f"{socket_proxy}.{tools_rig_const.RiggerConstants.ATTR_PROXY_SCALE}")
        rot_order = cmds.getAttr(f"{socket_proxy}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
        color = cmds.getAttr(f"{socket_proxy}.overrideColorRGB")[0]

        socket_ctrl = self.socket_proxy.get_name()
        socket_shape = "_sphere_joint_handle"
        shape_scale = locator_scale
        if self.add_child:
            _parent_jnt_name = self._assemble_node_name(name=self.socket_proxy.get_name())
            _parent_jnt_name += self.parent_tag
            _parent_jnt_name += f"_{core_naming.NamingConstants.Suffix.JNT}"
            socket_jnt.rename(_parent_jnt_name)
            socket_ctrl += self.parent_tag
            socket_shape = "circle_arrow"
            shape_scale = locator_scale * 1.45

        socket_ctrl, socket_offset_ctrl, *_ = self.create_rig_control(
            control_base_name=socket_ctrl,
            curve_file_name=socket_shape,
            parent_obj=global_offset_ctrl,
            match_obj=socket_jnt,
            rot_order=rot_order,
            shape_scale=shape_scale,
            color=color,
        )

        tools_rig_utils.add_driver_uuid_attr(
            target_driver=socket_ctrl,
            module_uuid=self.get_uuid(),
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.socket_proxy.get_meta_purpose(),
        )

        core_attr.hide_lock_default_attrs(socket_ctrl, scale=True, visibility=True)
        core_cnstr.constraint_targets(source_driver=socket_ctrl, target_driven=socket_jnt)

        if self.add_child:
            socket_child_jnt = self._assemble_node_name(name=self.socket_proxy.get_name())
            socket_child_jnt += self.child_tag
            socket_child_jnt += f"_{core_naming.NamingConstants.Suffix.JNT}"
            socket_child_jnt = cmds.duplicate(socket_jnt, parentOnly=True, name=socket_child_jnt)[0]
            core_hrchy.parent(source_objects=socket_child_jnt, target_parent=socket_jnt)

            joint_uuid_attr = f"{socket_child_jnt}.{tools_rig_const.RiggerConstants.ATTR_JOINT_UUID}"
            joint_purpose_attr = f"{socket_child_jnt}.{tools_rig_const.RiggerConstants.ATTR_JOINT_PURPOSE}"
            core_attr.set_attr(attribute_path=joint_uuid_attr, value=self.socket_child_proxy.get_uuid())
            core_attr.set_attr(attribute_path=joint_purpose_attr, value=self.socket_child_proxy.get_meta_purpose())

            socket_child_ctrl = self.socket_proxy.get_name()
            socket_child_ctrl += self.child_tag
            socket_child_ctrl, *_ = self.create_rig_control(
                control_base_name=socket_child_ctrl,
                curve_file_name="_sphere_arrow_attachment_pos_z",
                parent_obj=socket_ctrl,
                match_obj=socket_child_jnt,
                rot_order=rot_order,
                shape_scale=locator_scale,
                color=color,
            )
            # Add Driver UUID
            tools_rig_utils.add_driver_uuid_attr(
                target_driver=socket_child_ctrl,
                module_uuid=self.get_uuid(),
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=self.socket_child_proxy.get_meta_purpose(),
            )

            core_attr.hide_lock_default_attrs(socket_child_ctrl, scale=True, visibility=True)
            core_cnstr.constraint_targets(source_driver=socket_child_ctrl, target_driven=socket_child_jnt)

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [socket_offset_ctrl[0]]


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject

    # Reload Modules
    import gt.tools.auto_rigger.modules.module_socket as tools_mod_socket
    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.core.rigging as core_rigging
    import gt.core.naming as core_naming
    import importlib

    importlib.reload(tools_mod_socket)
    importlib.reload(tools_rig_fmr)
    importlib.reload(core_rigging)
    importlib.reload(core_naming)

    # Create Modules ----------------------------------------------------------------
    a_module = tools_rig_frm.ModuleGeneric()
    a_proxy = a_module.add_new_proxy()
    a_proxy.set_initial_position(z=-5)

    a_socket_no_child = ModuleSocket()
    a_socket_no_child.set_parent_uuid(a_proxy.get_uuid())
    a_socket_no_child.add_child = False

    a_socket_with_child = ModuleSocket()
    a_socket_with_child.socket_proxy.set_initial_position(x=10, z=-5)
    a_socket_with_child.set_parent_uuid(a_proxy.get_uuid())

    a_module_two = tools_rig_frm.ModuleGeneric()
    a_proxy_two = a_module.add_new_proxy()
    a_proxy_two.set_name("child_test")
    a_proxy_two.set_initial_position(x=0, y=0, z=0)
    a_proxy_two.set_parent_uuid_from_proxy(a_socket_with_child.socket_child_proxy)

    # Create Project ----------------------------------------------------------------
    a_project = RigProject()
    a_project.add_to_modules(a_module)
    a_project.add_to_modules(a_socket_no_child)
    a_project.add_to_modules(a_socket_with_child)

    a_project.build_proxy()
    # a_project.set_preference_value_using_key(key="delete_proxy_after_build", value=False)

    cmds.setAttr("C_socket_offset1|C_socket.rx", -6)
    cmds.setAttr("C_socket_offset1|C_socket.ry", 90)
    cmds.setAttr("C_socket_offset1|C_socket.rz", 9)

    a_project.read_data_from_scene()
    a_project.build_rig()

    dictionary = a_project.get_project_as_dict()

    # Rebuild ----------------------------------------------------------------------
    cmds.file(new=True, force=True)
    a_project2 = RigProject()
    a_project2.read_data_from_dict(dictionary)
    a_project2.build_proxy()
    a_project2.build_rig()

    # Adjust for Analysis
    cmds.setAttr(f"skeleton.v", 1)
    cmds.setAttr(f"C_socketParent_JNT.displayLocalAxis", 1)
    cmds.select(f"C_socketParent_CTRL")
    cmds.viewFit()
    # cmds.select(clear=True)
