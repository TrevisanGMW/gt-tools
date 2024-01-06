"""
Auto Rigger Root Module
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import find_proxy_root_curve_node, find_control_root_curve_node
from gt.tools.auto_rigger.rig_utils import find_proxy_node_from_uuid, find_vis_lines_from_uuid
from gt.tools.auto_rigger.rig_utils import find_joint_node_from_uuid
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric
from gt.utils.color_utils import ColorConstants, set_color_viewport
from gt.utils.attr_utils import set_attr, add_attr
from gt.ui import resource_library
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleRoot(ModuleGeneric):
    __version__ = '1.0.0'
    icon = resource_library.Icon.rigger_module_root
    allow_parenting = False

    SHOW_ROOT_KEY = "rootVisibility"

    def __init__(self, name="Root", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.set_orientation_method(method="world")

        # Hide Root
        self.add_to_metadata(key=self.SHOW_ROOT_KEY, value=False)

        # Default Proxies
        self.root = Proxy(name="root")
        self.root.set_locator_scale(scale=1)
        self.root.set_meta_purpose(value="root")
        self.root.add_color(ColorConstants.RigProxy.TWEAK)
        self.proxies = [self.root]

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
            logger.debug(f'Unable to read proxies from dictionary. Input must be a dictionary.')
            return
        self.read_purpose_matching_proxy_from_dict(proxy_dict)

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
        if self.parent_uuid:
            self.root.set_parent_uuid(self.parent_uuid)

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
        proxy_root = find_proxy_root_curve_node()
        root = find_proxy_node_from_uuid(self.root.get_uuid())
        root_lines = find_vis_lines_from_uuid(parent_uuid=self.root.get_uuid())
        metadata = self.get_metadata()

        add_attr(obj_list=str(proxy_root),
                 attributes="rootVisibility",
                 attr_type="bool",
                 default=True)
        root_shapes = cmds.listRelatives(str(root), shapes=True, fullPath=True) or []
        for line in list(root_lines) + root_shapes:
            cmds.connectAttr(f'{proxy_root}.rootVisibility', f'{line}.visibility')

        # Set Stored Hide Root
        hide_root = metadata.get(self.SHOW_ROOT_KEY, None)
        if isinstance(hide_root, bool):
            set_attr(obj_list=proxy_root, attr_list="rootVisibility", value=hide_root)

    def build_rig_post(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        root_jnt = find_joint_node_from_uuid(self.root.get_uuid())
        root_ctrl = find_control_root_curve_node()
        cmds.parentConstraint(root_ctrl, root_jnt)
        set_color_viewport(obj_list=root_jnt, rgb_color=ColorConstants.RigJoint.ROOT)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject

    a_module = ModuleGeneric()
    a_proxy = a_module.add_new_proxy()
    a_proxy.set_initial_position(x=5)
    a_root = ModuleRoot()
    a_root_two = ModuleRoot()
    a_root_two.root.set_initial_position(x=10)
    a_proxy.set_parent_uuid_from_proxy(a_root.proxies[0])
    a_project = RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_module)
    a_project.add_to_modules(a_root_two)
    # print(a_project.get_modules())
    a_project.build_proxy()
    # a_project.build_rig(delete_proxy=False)

    a_project.read_data_from_scene()
    dictionary = a_project.get_project_as_dict()

    cmds.file(new=True, force=True)
    a_project2 = RigProject()

    a_project2.read_data_from_dict(dictionary)
    a_project2.build_proxy()

    # Show all
    cmds.viewFit(all=True)
