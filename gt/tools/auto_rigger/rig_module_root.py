"""
Auto Rigger Root Module
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import RiggerConstants, find_objects_with_attr, find_proxy_node_from_uuid
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.utils.constraint_utils import equidistant_constraints
from gt.tools.auto_rigger.rig_utils import get_proxy_offset
from gt.utils.color_utils import ColorConstants
from gt.utils.transform_utils import Vector3
from gt.ui import resource_library
import maya.cmds as cmds
import logging
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleRoot(ModuleGeneric):
    __version__ = '0.0.1-alpha'
    icon = resource_library.Icon.rigger_module_root
    allow_parenting = False
    allow_multiple = False

    def __init__(self, name="Root", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        self.set_orientation_method(method="world")

        # Default Proxies
        self.root = Proxy(name="root")
        self.root.set_locator_scale(scale=1)
        self.root.set_meta_type(value="root")
        self.root.add_color(ColorConstants.RigProxy.TWEAK)
        self.proxies = [self.root]

    def get_module_as_dict(self, **kwargs):
        """
        Overwrite to remove offset data from the export
        Args:
            kwargs: Key arguments, not used for anything
        """
        return super().get_module_as_dict(include_offset_data=False)

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

        proxy = super().build_proxy()  # Passthrough
        return proxy

    def build_proxy_post(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        Creates leg proxy behavior through constraints and offsets.
        """
        # Get Maya Elements
        root = find_objects_with_attr(RiggerConstants.REF_ROOT_PROXY_ATTR)
        print(root)
        super().build_proxy_post()  # Passthrough
        cmds.select(clear=True)

    def build_skeleton(self):
        super().build_skeleton()  # Passthrough

    def build_skeleton_post(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        super().build_skeleton_post()  # Passthrough


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject

    a_root = ModuleRoot()
    a_project = RigProject()
    a_project.add_to_modules(a_root)
    print(a_project.get_modules())
    a_project.build_proxy()
    a_project.build_rig(delete_proxy=False)

    # a_project.read_data_from_scene()
    # dictionary = a_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = RigProject()
    # a_project2.read_data_from_dict(dictionary)
    # a_project2.build_proxy()

    # Show all
    cmds.viewFit(all=True)
