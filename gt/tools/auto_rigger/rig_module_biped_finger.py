"""
Auto Rigger Digit Modules (Fingers, Toes)
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import find_joint_node_from_uuid, get_meta_type_from_dict
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.utils.color_utils import ColorConstants, set_color_viewport
from gt.tools.auto_rigger.rig_constants import RiggerConstants
from gt.utils.naming_utils import NamingConstants
from gt.utils.transform_utils import Vector3
from gt.utils.curve_utils import get_curve
from gt.ui import resource_library
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleBipedFingers(ModuleGeneric):
    __version__ = '0.0.2-alpha'
    icon = resource_library.Icon.rigger_module_biped_fingers
    allow_parenting = True

    # Tags
    thumb_tag = "thumb"
    index_tag = "index"
    middle_tag = "middle"
    ring_tag = "ring"
    pinky_tag = "pinky"
    extra_tag = "extra"

    def __init__(self, name="Fingers", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 1, 0), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)

        # Positions
        pos_thumb01 = Vector3(x=-4, y=130)
        pos_thumb02 = pos_thumb01 + Vector3(z=3)
        pos_thumb03 = pos_thumb02 + Vector3(z=3)
        pos_thumb04 = pos_thumb03 + Vector3(z=3)

        pos_index01 = Vector3(x=-2, y=130)
        pos_index02 = pos_index01 + Vector3(z=3)
        pos_index03 = pos_index02 + Vector3(z=3)
        pos_index04 = pos_index03 + Vector3(z=3)

        pos_middle01 = Vector3(x=0, y=130)
        pos_middle02 = pos_middle01 + Vector3(z=3)
        pos_middle03 = pos_middle02 + Vector3(z=3)
        pos_middle04 = pos_middle03 + Vector3(z=3)

        pos_ring01 = Vector3(x=2, y=130)
        pos_ring02 = pos_ring01 + Vector3(z=3)
        pos_ring03 = pos_ring02 + Vector3(z=3)
        pos_ring04 = pos_ring03 + Vector3(z=3)

        pos_pinky01 = Vector3(x=4, y=130)
        pos_pinky02 = pos_pinky01 + Vector3(z=3)
        pos_pinky03 = pos_pinky02 + Vector3(z=3)
        pos_pinky04 = pos_pinky03 + Vector3(z=3)

        pos_extra01 = Vector3(x=6, y=130)
        pos_extra02 = pos_extra01 + Vector3(z=3)
        pos_extra03 = pos_extra02 + Vector3(z=3)
        pos_extra04 = pos_extra03 + Vector3(z=3)

        loc_scale = .8
        loc_scale_end = .4

        # Thumb -------------------------------------------------------------------------------------
        self.thumb_digits = []
        self.thumb01 = Proxy(name=f"{self.thumb_tag}01")
        self.thumb01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb01.set_initial_position(xyz=pos_thumb01)
        self.thumb01.set_locator_scale(scale=loc_scale)
        self.thumb01.set_meta_type(value=self.thumb01.get_name())

        self.thumb02 = Proxy(name=f"{self.thumb_tag}02")
        self.thumb02.set_parent_uuid(self.thumb01.get_uuid())
        self.thumb02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb02.set_initial_position(xyz=pos_thumb02)
        self.thumb02.set_locator_scale(scale=loc_scale)
        self.thumb02.set_meta_type(value=self.thumb02.get_name())

        self.thumb03 = Proxy(name=f"{self.thumb_tag}03")
        self.thumb03.set_parent_uuid(self.thumb02.get_uuid())
        self.thumb03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb03.set_initial_position(xyz=pos_thumb03)
        self.thumb03.set_locator_scale(scale=loc_scale)
        self.thumb03.set_meta_type(value=self.thumb03.get_name())

        self.thumb04 = Proxy(name=f"{self.thumb_tag}End")
        self.thumb04.set_parent_uuid(self.thumb03.get_uuid())
        self.thumb04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb04.set_initial_position(xyz=pos_thumb04)
        self.thumb04.set_locator_scale(scale=loc_scale_end)
        self.thumb04.set_meta_type(value=self.thumb04.get_name())
        self.thumb04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.thumb_digits = [self.thumb01, self.thumb02, self.thumb03, self.thumb04]

        # Index -------------------------------------------------------------------------------------
        self.index_digits = []
        self.index01 = Proxy(name=f"{self.index_tag}01")
        self.index01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index01.set_initial_position(xyz=pos_index01)
        self.index01.set_locator_scale(scale=loc_scale)
        self.index01.set_meta_type(value=self.index01.get_name())

        self.index02 = Proxy(name=f"{self.index_tag}02")
        self.index02.set_parent_uuid(self.index01.get_uuid())
        self.index02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index02.set_initial_position(xyz=pos_index02)
        self.index02.set_locator_scale(scale=loc_scale)
        self.index02.set_meta_type(value=self.index02.get_name())

        self.index03 = Proxy(name=f"{self.index_tag}03")
        self.index03.set_parent_uuid(self.index02.get_uuid())
        self.index03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index03.set_initial_position(xyz=pos_index03)
        self.index03.set_locator_scale(scale=loc_scale)
        self.index03.set_meta_type(value=self.index03.get_name())

        self.index04 = Proxy(name=f"{self.index_tag}End")
        self.index04.set_parent_uuid(self.index03.get_uuid())
        self.index04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index04.set_initial_position(xyz=pos_index04)
        self.index04.set_locator_scale(scale=loc_scale_end)
        self.index04.set_meta_type(value=self.index04.get_name())
        self.index04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.index_digits = [self.index01, self.index02, self.index03, self.index04]

        # Middle -------------------------------------------------------------------------------------
        self.middle_digits = []
        self.middle01 = Proxy(name=f"{self.middle_tag}01")
        self.middle01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle01.set_initial_position(xyz=pos_middle01)
        self.middle01.set_locator_scale(scale=loc_scale)
        self.middle01.set_meta_type(value=self.middle01.get_name())

        self.middle02 = Proxy(name=f"{self.middle_tag}02")
        self.middle02.set_parent_uuid(self.middle01.get_uuid())
        self.middle02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle02.set_initial_position(xyz=pos_middle02)
        self.middle02.set_locator_scale(scale=loc_scale)
        self.middle02.set_meta_type(value=self.middle02.get_name())

        self.middle03 = Proxy(name=f"{self.middle_tag}03")
        self.middle03.set_parent_uuid(self.middle02.get_uuid())
        self.middle03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle03.set_initial_position(xyz=pos_middle03)
        self.middle03.set_locator_scale(scale=loc_scale)
        self.middle03.set_meta_type(value=self.middle03.get_name())

        self.middle04 = Proxy(name=f"{self.middle_tag}End")
        self.middle04.set_parent_uuid(self.middle03.get_uuid())
        self.middle04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle04.set_initial_position(xyz=pos_middle04)
        self.middle04.set_locator_scale(scale=loc_scale_end)
        self.middle04.set_meta_type(value=self.middle04.get_name())
        self.middle04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.middle_digits = [self.middle01, self.middle02, self.middle03, self.middle04]

        # Ring -------------------------------------------------------------------------------------
        self.ring_digits = []
        self.ring01 = Proxy(name=f"{self.ring_tag}01")
        self.ring01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring01.set_initial_position(xyz=pos_ring01)
        self.ring01.set_locator_scale(scale=loc_scale)
        self.ring01.set_meta_type(value=self.ring01.get_name())

        self.ring02 = Proxy(name=f"{self.ring_tag}02")
        self.ring02.set_parent_uuid(self.ring01.get_uuid())
        self.ring02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring02.set_initial_position(xyz=pos_ring02)
        self.ring02.set_locator_scale(scale=loc_scale)
        self.ring02.set_meta_type(value=self.ring02.get_name())

        self.ring03 = Proxy(name=f"{self.ring_tag}03")
        self.ring03.set_parent_uuid(self.ring02.get_uuid())
        self.ring03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring03.set_initial_position(xyz=pos_ring03)
        self.ring03.set_locator_scale(scale=loc_scale)
        self.ring03.set_meta_type(value=self.ring03.get_name())

        self.ring04 = Proxy(name=f"{self.ring_tag}End")
        self.ring04.set_parent_uuid(self.ring03.get_uuid())
        self.ring04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring04.set_initial_position(xyz=pos_ring04)
        self.ring04.set_locator_scale(scale=loc_scale_end)
        self.ring04.set_meta_type(value=self.ring04.get_name())
        self.ring04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.ring_digits = [self.ring01, self.ring02, self.ring03, self.ring04]

        # Pinky -------------------------------------------------------------------------------------
        self.pinky_digits = []
        self.pinky01 = Proxy(name=f"{self.pinky_tag}01")
        self.pinky01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky01.set_initial_position(xyz=pos_pinky01)
        self.pinky01.set_locator_scale(scale=loc_scale)
        self.pinky01.set_meta_type(value=self.pinky01.get_name())

        self.pinky02 = Proxy(name=f"{self.pinky_tag}02")
        self.pinky02.set_parent_uuid(self.pinky01.get_uuid())
        self.pinky02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky02.set_initial_position(xyz=pos_pinky02)
        self.pinky02.set_locator_scale(scale=loc_scale)
        self.pinky02.set_meta_type(value=self.pinky02.get_name())

        self.pinky03 = Proxy(name=f"{self.pinky_tag}03")
        self.pinky03.set_parent_uuid(self.pinky02.get_uuid())
        self.pinky03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky03.set_initial_position(xyz=pos_pinky03)
        self.pinky03.set_locator_scale(scale=loc_scale)
        self.pinky03.set_meta_type(value=self.pinky03.get_name())

        self.pinky04 = Proxy(name=f"{self.pinky_tag}End")
        self.pinky04.set_parent_uuid(self.pinky03.get_uuid())
        self.pinky04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky04.set_initial_position(xyz=pos_pinky04)
        self.pinky04.set_locator_scale(scale=loc_scale_end)
        self.pinky04.set_meta_type(value=self.pinky04.get_name())
        self.pinky04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.pinky_digits = [self.pinky01, self.pinky02, self.pinky03, self.pinky04]

        # Extra -------------------------------------------------------------------------------------
        self.extra_digits = []
        self.extra01 = Proxy(name=f"{self.extra_tag}01")
        self.extra01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra01.set_initial_position(xyz=pos_extra01)
        self.extra01.set_locator_scale(scale=loc_scale)
        self.extra01.set_meta_type(value=self.extra01.get_name())

        self.extra02 = Proxy(name=f"{self.extra_tag}02")
        self.extra02.set_parent_uuid(self.extra01.get_uuid())
        self.extra02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra02.set_initial_position(xyz=pos_extra02)
        self.extra02.set_locator_scale(scale=loc_scale)
        self.extra02.set_meta_type(value=self.extra02.get_name())

        self.extra03 = Proxy(name=f"{self.extra_tag}03")
        self.extra03.set_parent_uuid(self.extra02.get_uuid())
        self.extra03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra03.set_initial_position(xyz=pos_extra03)
        self.extra03.set_locator_scale(scale=loc_scale)
        self.extra03.set_meta_type(value=self.extra03.get_name())

        self.extra04 = Proxy(name=f"{self.extra_tag}End")
        self.extra04.set_parent_uuid(self.extra03.get_uuid())
        self.extra04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra04.set_initial_position(xyz=pos_extra04)
        self.extra04.set_locator_scale(scale=loc_scale_end)
        self.extra04.set_meta_type(value=self.extra04.get_name())
        self.extra04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.extra_digits = [self.extra01, self.extra02, self.extra03, self.extra04]
        self.refresh_proxies_list()

    def refresh_proxies_list(self, thumb=True, index=True, middle=True, ring=True, pinky=True, extra=False):
        """
        Refreshes the main proxies list used by the module during build
        """
        self.proxies = []
        if thumb:
            self.proxies.extend(self.thumb_digits)
        if index:
            self.proxies.extend(self.index_digits)
        if middle:
            self.proxies.extend(self.middle_digits)
        if ring:
            self.proxies.extend(self.ring_digits)
        if pinky:
            self.proxies.extend(self.pinky_digits)
        if extra:
            self.proxies.extend(self.extra_digits)

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
        # Determine Digit Activation
        _thumb = False
        _index = False
        _middle = False
        _ring = False
        _pinky = False
        _extra = False
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(RiggerConstants.PROXY_META_TYPE)
                if meta_type and self.thumb_tag in meta_type:
                    _thumb = True
                elif meta_type and self.index_tag in meta_type:
                    _index = True
                elif meta_type and self.middle_tag in meta_type:
                    _middle = True
                elif meta_type and self.ring_tag in meta_type:
                    _ring = True
                elif meta_type and self.pinky_tag in meta_type:
                    _pinky = True
                elif meta_type and self.extra_tag in meta_type:
                    _extra = True
        self.refresh_proxies_list(thumb=_thumb, index=_index, middle=_middle,
                                  ring=_ring, pinky=_pinky, extra=_extra)
        print(proxy_dict)
        self.read_type_matching_proxy_from_dict(proxy_dict)

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
            if self.thumb01:
                self.thumb01.set_parent_uuid(self.parent_uuid)
            if self.index01:
                self.index01.set_parent_uuid(self.parent_uuid)
            if self.middle01:
                self.middle01.set_parent_uuid(self.parent_uuid)
            if self.ring01:
                self.ring01.set_parent_uuid(self.parent_uuid)
            if self.pinky01:
                self.pinky01.set_parent_uuid(self.parent_uuid)
            if self.extra01:
                self.extra01.set_parent_uuid(self.parent_uuid)
        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_post(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        for digit in self.proxies:
            digit.apply_offset_transform()
        for digit in self.proxies:
            digit.apply_transforms()
        cmds.select(clear=True)

    def build_skeleton(self):
        super().build_skeleton()  # Passthrough

    def build_rig(self):
        """
        Runs post rig script.
        """
        for digit in self.proxies:
            digit_jnt = find_joint_node_from_uuid(digit.get_uuid())
            meta_type = get_meta_type_from_dict(digit.get_metadata())
            if meta_type and str(meta_type).endswith("End"):
                set_color_viewport(obj_list=digit_jnt, rgb_color=ColorConstants.RigJoint.END)
            else:
                set_color_viewport(obj_list=digit_jnt, rgb_color=ColorConstants.RigJoint.OFFSET)


class ModuleBipedFingersLeft(ModuleBipedFingers):
    def __init__(self, name="Left Fingers", prefix=NamingConstants.Prefix.LEFT, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        # Describe Positions
        pos_thumb01 = Vector3(x=60.8, y=130.4, z=2.9)
        pos_thumb02 = pos_thumb01 + Vector3(z=4.4)
        pos_thumb03 = pos_thumb02 + Vector3(z=4.4)
        pos_thumb04 = pos_thumb03 + Vector3(z=4.6)

        pos_index01 = Vector3(x=66.9, y=130.4, z=3.5)
        pos_index02 = pos_index01 + Vector3(x=3.2)
        pos_index03 = pos_index02 + Vector3(x=4.1)
        pos_index04 = pos_index03 + Vector3(x=3.3)

        pos_middle01 = Vector3(x=66.9, y=130.4, z=1.1)
        pos_middle02 = pos_middle01 + Vector3(x=3.8)
        pos_middle03 = pos_middle02 + Vector3(x=3.7)
        pos_middle04 = pos_middle03 + Vector3(x=3.6)

        pos_ring01 = Vector3(x=66.9, y=130.4, z=-1.1)
        pos_ring02 = pos_ring01 + Vector3(x=3.5)
        pos_ring03 = pos_ring02 + Vector3(x=3.6)
        pos_ring04 = pos_ring03 + Vector3(x=3.5)

        pos_pinky01 = Vector3(x=66.9, y=130.4, z=-3.2)
        pos_pinky02 = pos_pinky01 + Vector3(x=3.3)
        pos_pinky03 = pos_pinky02 + Vector3(x=3.2)
        pos_pinky04 = pos_pinky03 + Vector3(x=3.5)

        pos_extra01 = Vector3(x=66.9, y=130.4, z=-5.3)
        pos_extra02 = pos_extra01 + Vector3(x=3)
        pos_extra03 = pos_extra02 + Vector3(x=3)
        pos_extra04 = pos_extra03 + Vector3(x=3.3)

        # Set Positions
        self.thumb01.set_initial_position(xyz=pos_thumb01)
        self.thumb02.set_initial_position(xyz=pos_thumb02)
        self.thumb03.set_initial_position(xyz=pos_thumb03)
        self.thumb04.set_initial_position(xyz=pos_thumb04)

        self.index01.set_initial_position(xyz=pos_index01)
        self.index02.set_initial_position(xyz=pos_index02)
        self.index03.set_initial_position(xyz=pos_index03)
        self.index04.set_initial_position(xyz=pos_index04)

        self.middle01.set_initial_position(xyz=pos_middle01)
        self.middle02.set_initial_position(xyz=pos_middle02)
        self.middle03.set_initial_position(xyz=pos_middle03)
        self.middle04.set_initial_position(xyz=pos_middle04)

        self.ring01.set_initial_position(xyz=pos_ring01)
        self.ring02.set_initial_position(xyz=pos_ring02)
        self.ring03.set_initial_position(xyz=pos_ring03)
        self.ring04.set_initial_position(xyz=pos_ring04)

        self.pinky01.set_initial_position(xyz=pos_pinky01)
        self.pinky02.set_initial_position(xyz=pos_pinky02)
        self.pinky03.set_initial_position(xyz=pos_pinky03)
        self.pinky04.set_initial_position(xyz=pos_pinky04)

        self.extra01.set_initial_position(xyz=pos_extra01)
        self.extra02.set_initial_position(xyz=pos_extra02)
        self.extra03.set_initial_position(xyz=pos_extra03)
        self.extra04.set_initial_position(xyz=pos_extra04)


class ModuleBipedFingersRight(ModuleBipedFingers):
    def __init__(self, name="Right Fingers", prefix=NamingConstants.Prefix.RIGHT, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        # Describe Positions
        pos_thumb01 = Vector3(x=-60.8, y=130.4, z=2.9)
        pos_thumb02 = pos_thumb01 + Vector3(z=4.4)
        pos_thumb03 = pos_thumb02 + Vector3(z=4.4)
        pos_thumb04 = pos_thumb03 + Vector3(z=4.6)

        pos_index01 = Vector3(x=-66.9, y=130.4, z=3.5)
        pos_index02 = pos_index01 + Vector3(x=-3.2)
        pos_index03 = pos_index02 + Vector3(x=-4.1)
        pos_index04 = pos_index03 + Vector3(x=-3.3)

        pos_middle01 = Vector3(x=-66.9, y=130.4, z=1.1)
        pos_middle02 = pos_middle01 + Vector3(x=-3.8)
        pos_middle03 = pos_middle02 + Vector3(x=-3.7)
        pos_middle04 = pos_middle03 + Vector3(x=-3.6)

        pos_ring01 = Vector3(x=-66.9, y=130.4, z=-1.1)
        pos_ring02 = pos_ring01 + Vector3(x=-3.5)
        pos_ring03 = pos_ring02 + Vector3(x=-3.6)
        pos_ring04 = pos_ring03 + Vector3(x=-3.5)

        pos_pinky01 = Vector3(x=-66.9, y=130.4, z=-3.2)
        pos_pinky02 = pos_pinky01 + Vector3(x=-3.3)
        pos_pinky03 = pos_pinky02 + Vector3(x=-3.2)
        pos_pinky04 = pos_pinky03 + Vector3(x=-3.5)

        pos_extra01 = Vector3(x=-66.9, y=130.4, z=-5.3)
        pos_extra02 = pos_extra01 + Vector3(x=-3)
        pos_extra03 = pos_extra02 + Vector3(x=-3)
        pos_extra04 = pos_extra03 + Vector3(x=-3.3)

        # Set Positions
        self.thumb01.set_initial_position(xyz=pos_thumb01)
        self.thumb02.set_initial_position(xyz=pos_thumb02)
        self.thumb03.set_initial_position(xyz=pos_thumb03)
        self.thumb04.set_initial_position(xyz=pos_thumb04)

        self.index01.set_initial_position(xyz=pos_index01)
        self.index02.set_initial_position(xyz=pos_index02)
        self.index03.set_initial_position(xyz=pos_index03)
        self.index04.set_initial_position(xyz=pos_index04)

        self.middle01.set_initial_position(xyz=pos_middle01)
        self.middle02.set_initial_position(xyz=pos_middle02)
        self.middle03.set_initial_position(xyz=pos_middle03)
        self.middle04.set_initial_position(xyz=pos_middle04)

        self.ring01.set_initial_position(xyz=pos_ring01)
        self.ring02.set_initial_position(xyz=pos_ring02)
        self.ring03.set_initial_position(xyz=pos_ring03)
        self.ring04.set_initial_position(xyz=pos_ring04)

        self.pinky01.set_initial_position(xyz=pos_pinky01)
        self.pinky02.set_initial_position(xyz=pos_pinky02)
        self.pinky03.set_initial_position(xyz=pos_pinky03)
        self.pinky04.set_initial_position(xyz=pos_pinky04)

        self.extra01.set_initial_position(xyz=pos_extra01)
        self.extra02.set_initial_position(xyz=pos_extra02)
        self.extra03.set_initial_position(xyz=pos_extra03)
        self.extra04.set_initial_position(xyz=pos_extra04)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject
    a_digit_mod = ModuleBipedFingers()
    a_digit_mod_lf = ModuleBipedFingersLeft()
    a_digit_mod_lf.refresh_proxies_list(index=False, extra=True)
    a_digit_mod_rt = ModuleBipedFingersRight()
    a_project = RigProject()
    # a_project.add_to_modules(a_digit_mod)
    a_project.add_to_modules(a_digit_mod_lf)
    # a_project.add_to_modules(a_digit_mod_rt)
    a_project.build_proxy()
    # a_project.build_rig()

    # cmds.setAttr(f'lf_thumb02.rx', 30)
    cmds.setAttr(f'lf_ring02.rz', -45)
    # # cmds.setAttr(f'rt_thumb02.rx', 30)

    a_project.read_data_from_scene()
    dictionary = a_project.get_project_as_dict()

    cmds.file(new=True, force=True)
    a_project2 = RigProject()
    a_project2.read_data_from_dict(dictionary)
    print(a_project2.get_project_as_dict().get("modules"))
    a_project2.build_proxy()
    # a_project2.build_rig()

    # Frame all
    cmds.viewFit(all=True)
