"""
Auto Rigger Spine Modules
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


class ModuleSpine(ModuleGeneric):
    icon = resource_library.Icon.rigger_module_generic
    __version_tuple__ = (0, 0, 1)
    __version_suffix__ = 'alpha'
    __version__ = '.'.join(str(n) for n in __version_tuple__) + __version_suffix__

    def __init__(self, name="Spine", prefix=None, suffix=None, pos_offset=None, num_spine=3):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        self.num_spine = num_spine

        # Default Proxies
        self.hip = Proxy(name="hip")
        pos_hip = Vector3(y=84.5) + pos_offset
        self.hip.set_initial_position(xyz=pos_hip)
        self.hip.set_locator_scale(scale=1)
        self.hip.set_meta_type(value="hip")

        self.spines = []
        _parent_uuid = self.hip.get_uuid()
        for num in range(0, num_spine):
            new_spine = Proxy(name=f'spine{str(num+1).zfill(2)}')
            new_spine.set_locator_scale(scale=0.5)
            new_spine.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
            new_spine.set_meta_type(value=f'spine{str(num+1).zfill(2)}')
            new_spine.add_meta_parent(line_parent=_parent_uuid)
            new_spine.set_parent_uuid(uuid=_parent_uuid)
            _parent_uuid = new_spine.get_uuid()
            self.spines.append(new_spine)

        self.chest = Proxy(name="chest")
        pos_chest = Vector3(y=114.5) + pos_offset
        self.chest.set_initial_position(xyz=pos_chest)
        self.chest.set_locator_scale(scale=1)
        if self.spines:
            self.chest.add_meta_parent(line_parent=self.spines[-1].get_uuid())
        else:
            self.chest.add_meta_parent(line_parent=self.hip.get_uuid())

        self.chest.set_meta_type(value="chest")
        self.refresh_proxies_list()

    def refresh_proxies_list(self):
        """
        Refreshes the main proxies list used by the module during build (update in case objects were updated)
        """
        self.proxies = [self.hip]
        self.proxies.extend(self.spines)
        self.proxies.append(self.chest)

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
        self.spines = []
        spine_pattern = r'spine\d+'
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(RiggerConstants.PROXY_META_TYPE)
                if meta_type == "hip":
                    self.hip.set_uuid(uuid)
                    self.hip.read_data_from_dict(proxy_dict=description)
                if meta_type == "chest":
                    self.chest.set_uuid(uuid)
                    self.chest.read_data_from_dict(proxy_dict=description)
                if bool(re.match(spine_pattern, meta_type)):
                    new_spine = Proxy()
                    new_spine.set_uuid(uuid)
                    new_spine.read_data_from_dict(proxy_dict=description)
                    self.spines.append(new_spine)
        self.num_spine = len(self.spines)  # Update number of spines
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

    def build_proxy(self):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
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
        hip = find_proxy_node_from_uuid(self.hip.get_uuid())
        chest = find_proxy_node_from_uuid(self.chest.get_uuid())

        spines = []
        for spine in self.spines:
            spine_node = find_proxy_node_from_uuid(spine.get_uuid())
            spines.append(spine_node)
        self.hip.apply_offset_transform()
        self.chest.apply_offset_transform()

        spine_offsets = []
        for spine in spines:
            offset = get_proxy_offset(spine)
            spine_offsets.append(offset)
        equidistant_constraints(start=hip, end=chest, target_list=spine_offsets)

        self.hip.apply_transforms()
        self.chest.apply_transforms()
        for spine in self.spines:
            spine.apply_transforms()
        cmds.select(clear=True)

    def build_skeleton(self):
        super().build_skeleton()  # Passthrough

    def build_skeleton_post(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        self.chest.set_parent_uuid(uuid=self.chest.get_meta_parent_uuid())
        super().build_skeleton_post()  # Passthrough
        self.chest.clear_parent_uuid()


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject

    a_spine = ModuleSpine()
    a_project = RigProject()
    a_project.add_to_modules(a_spine)
    a_project.build_proxy()
    #
    # cmds.setAttr(f'hip.tx', 10)
    # cmds.setAttr(f'spine02.tx', 10)
    #
    # a_project.read_data_from_scene()
    # dictionary = a_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = RigProject()
    # a_project2.read_data_from_dict(dictionary)
    # a_project2.build_proxy()

    # Show all
    cmds.viewFit(all=True)
