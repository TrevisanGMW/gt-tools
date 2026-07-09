"""
Auto Rigger Finger Module
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.transform as core_trans
import gt.core.hierarchy as core_hrchy
import gt.core.naming as core_naming
import gt.core.color as core_color
import gt.core.curve as core_curve
import gt.core.attr as core_attr
import gt.core.math as core_math
import gt.core.str as core_str
import gt.core as core
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleBipedFingers(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_biped_fingers
    allow_parenting = True

    def __init__(
        self,
        name="Fingers",
        prefix=None,
        suffix=None,
        meta=True,
        thumb=True,
        index=True,
        middle=True,
        ring=True,
        pinky=True,
        extra=False,
    ):
        """
        Initialize the ModuleBipedFingers instance.

        Args:
            name (str, optional): The name of the module. Defaults to "Fingers".
            prefix (str or None, optional): Optional prefix for naming controls.
            suffix (str or None, optional): Optional suffix for naming controls.
            meta (bool, optional): Whether to include meta finger controls.
            thumb (bool, optional): Whether to include the thumb finger.
            index (bool, optional): Whether to include the index finger.
            middle (bool, optional): Whether to include the middle finger.
            ring (bool, optional): Whether to include the ring finger.
            pinky (bool, optional): Whether to include the pinky finger.
            extra (bool, optional): Whether to include extra finger controls beyond the standard five.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 1, 0), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)

        self.meta = meta
        self.thumb = thumb
        self.index = index
        self.middle = middle
        self.ring = ring
        self.pinky = pinky
        self.extra = extra

        # Extra Module Data
        self.setup_name = "fingers"
        self.meta_name = "Meta"
        self.thumb_name = "thumb"
        self.index_name = "index"
        self.middle_name = "middle"
        self.ring_name = "ring"
        self.pinky_name = "pinky"
        self.extra_name = "extra"

        # Positions
        pos_meta_index = core_trans.Vector3(x=-2, y=125)
        pos_meta_middle = core_trans.Vector3(x=0, y=125)
        pos_meta_ring = core_trans.Vector3(x=-2, y=125)
        pos_meta_pinky = core_trans.Vector3(x=-4, y=125)
        pos_meta_extra = core_trans.Vector3(x=-6, y=125)

        pos_thumb01 = core_trans.Vector3(x=-4, y=130)
        pos_thumb02 = pos_thumb01 + core_trans.Vector3(z=3)
        pos_thumb03 = pos_thumb02 + core_trans.Vector3(z=3)
        pos_thumb04 = pos_thumb03 + core_trans.Vector3(z=3)

        pos_index01 = core_trans.Vector3(x=-2, y=130)
        pos_index02 = pos_index01 + core_trans.Vector3(z=3)
        pos_index03 = pos_index02 + core_trans.Vector3(z=3)
        pos_index04 = pos_index03 + core_trans.Vector3(z=3)

        pos_middle01 = core_trans.Vector3(x=0, y=130)
        pos_middle02 = pos_middle01 + core_trans.Vector3(z=3)
        pos_middle03 = pos_middle02 + core_trans.Vector3(z=3)
        pos_middle04 = pos_middle03 + core_trans.Vector3(z=3)

        pos_ring01 = core_trans.Vector3(x=2, y=130)
        pos_ring02 = pos_ring01 + core_trans.Vector3(z=3)
        pos_ring03 = pos_ring02 + core_trans.Vector3(z=3)
        pos_ring04 = pos_ring03 + core_trans.Vector3(z=3)

        pos_pinky01 = core_trans.Vector3(x=4, y=130)
        pos_pinky02 = pos_pinky01 + core_trans.Vector3(z=3)
        pos_pinky03 = pos_pinky02 + core_trans.Vector3(z=3)
        pos_pinky04 = pos_pinky03 + core_trans.Vector3(z=3)

        pos_extra01 = core_trans.Vector3(x=6, y=130)
        pos_extra02 = pos_extra01 + core_trans.Vector3(z=3)
        pos_extra03 = pos_extra02 + core_trans.Vector3(z=3)
        pos_extra04 = pos_extra03 + core_trans.Vector3(z=3)

        loc_scale = 0.8
        loc_scale_end = 0.4

        # Meta -------------------------------------------------------------------------------------
        self._activated_meta_digits = []  # The ones current being used - Populated when refreshing proxies
        self.meta_digits = []
        self.meta_index_proxy = tools_rig_frm.Proxy(name=f"index{self.meta_name}")
        self.meta_index_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.meta_index_proxy.set_initial_position(xyz=pos_meta_index)
        self.meta_index_proxy.set_locator_scale(scale=loc_scale)
        self.meta_index_proxy.set_meta_purpose(value=self.meta_index_proxy.get_name())
        self.meta_index_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.meta_digits.append(self.meta_index_proxy)

        self.meta_middle_proxy = tools_rig_frm.Proxy(name=f"middle{self.meta_name}")
        self.meta_middle_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.meta_middle_proxy.set_initial_position(xyz=pos_meta_middle)
        self.meta_middle_proxy.set_locator_scale(scale=loc_scale)
        self.meta_middle_proxy.set_meta_purpose(value=self.meta_middle_proxy.get_name())
        self.meta_middle_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.meta_digits.append(self.meta_middle_proxy)

        self.meta_ring_proxy = tools_rig_frm.Proxy(name=f"ring{self.meta_name}")
        self.meta_ring_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.meta_ring_proxy.set_initial_position(xyz=pos_meta_ring)
        self.meta_ring_proxy.set_locator_scale(scale=loc_scale)
        self.meta_ring_proxy.set_meta_purpose(value=self.meta_ring_proxy.get_name())
        self.meta_ring_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.meta_digits.append(self.meta_ring_proxy)

        self.meta_pinky_proxy = tools_rig_frm.Proxy(name=f"pinky{self.meta_name}")
        self.meta_pinky_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.meta_pinky_proxy.set_initial_position(xyz=pos_meta_pinky)
        self.meta_pinky_proxy.set_locator_scale(scale=loc_scale)
        self.meta_pinky_proxy.set_meta_purpose(value=self.meta_pinky_proxy.get_name())
        self.meta_pinky_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.meta_digits.append(self.meta_pinky_proxy)

        self.meta_extra_proxy = tools_rig_frm.Proxy(name=f"extra{self.meta_name}")
        self.meta_extra_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.meta_extra_proxy.set_initial_position(xyz=pos_meta_extra)
        self.meta_extra_proxy.set_locator_scale(scale=loc_scale)
        self.meta_extra_proxy.set_meta_purpose(value=self.meta_extra_proxy.get_name())
        self.meta_extra_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )
        self.meta_digits.append(self.meta_extra_proxy)

        # Thumb -------------------------------------------------------------------------------------
        self.thumb_digits = []
        self.thumb01_proxy = tools_rig_frm.Proxy(name=f"{self.thumb_name}01")
        self.thumb01_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.thumb01_proxy.set_initial_position(xyz=pos_thumb01)
        self.thumb01_proxy.set_locator_scale(scale=loc_scale)
        self.thumb01_proxy.set_meta_purpose(value=self.thumb01_proxy.get_name())
        self.thumb01_proxy.add_driver_type(
            driver_type=[tools_rig_const.RiggerDriverTypes.GENERIC, tools_rig_const.RiggerDriverTypes.FK]
        )

        self.thumb02_proxy = tools_rig_frm.Proxy(name=f"{self.thumb_name}02")
        self.thumb02_proxy.set_parent_uuid(self.thumb01_proxy.get_uuid())
        self.thumb02_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.thumb02_proxy.set_initial_position(xyz=pos_thumb02)
        self.thumb02_proxy.set_locator_scale(scale=loc_scale)
        self.thumb02_proxy.set_meta_purpose(value=self.thumb02_proxy.get_name())
        self.thumb02_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.thumb03_proxy = tools_rig_frm.Proxy(name=f"{self.thumb_name}03")
        self.thumb03_proxy.set_parent_uuid(self.thumb02_proxy.get_uuid())
        self.thumb03_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.thumb03_proxy.set_initial_position(xyz=pos_thumb03)
        self.thumb03_proxy.set_locator_scale(scale=loc_scale)
        self.thumb03_proxy.set_meta_purpose(value=self.thumb03_proxy.get_name())
        self.thumb03_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.thumb04_proxy = tools_rig_frm.Proxy(name=f"{self.thumb_name}End")
        self.thumb04_proxy.set_parent_uuid(self.thumb03_proxy.get_uuid())
        self.thumb04_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.thumb04_proxy.set_initial_position(xyz=pos_thumb04)
        self.thumb04_proxy.set_locator_scale(scale=loc_scale_end)
        self.thumb04_proxy.set_meta_purpose(value=self.thumb04_proxy.get_name())
        self.thumb04_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
        self.thumb_digits = [self.thumb01_proxy, self.thumb02_proxy, self.thumb03_proxy, self.thumb04_proxy]

        # Index -------------------------------------------------------------------------------------\
        self.index_digits = []
        self.index01_proxy = tools_rig_frm.Proxy(name=f"{self.index_name}01")
        if self.meta:
            self.index01_proxy.set_parent_uuid(self.meta_index_proxy.get_uuid())
        self.index01_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.index01_proxy.set_initial_position(xyz=pos_index01)
        self.index01_proxy.set_locator_scale(scale=loc_scale)
        self.index01_proxy.set_meta_purpose(value=self.index01_proxy.get_name())
        self.index01_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.index02_proxy = tools_rig_frm.Proxy(name=f"{self.index_name}02")
        self.index02_proxy.set_parent_uuid(self.index01_proxy.get_uuid())
        self.index02_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.index02_proxy.set_initial_position(xyz=pos_index02)
        self.index02_proxy.set_locator_scale(scale=loc_scale)
        self.index02_proxy.set_meta_purpose(value=self.index02_proxy.get_name())
        self.index02_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.index03_proxy = tools_rig_frm.Proxy(name=f"{self.index_name}03")
        self.index03_proxy.set_parent_uuid(self.index02_proxy.get_uuid())
        self.index03_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.index03_proxy.set_initial_position(xyz=pos_index03)
        self.index03_proxy.set_locator_scale(scale=loc_scale)
        self.index03_proxy.set_meta_purpose(value=self.index03_proxy.get_name())
        self.index03_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.index04_proxy = tools_rig_frm.Proxy(name=f"{self.index_name}End")
        self.index04_proxy.set_parent_uuid(self.index03_proxy.get_uuid())
        self.index04_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.index04_proxy.set_initial_position(xyz=pos_index04)
        self.index04_proxy.set_locator_scale(scale=loc_scale_end)
        self.index04_proxy.set_meta_purpose(value=self.index04_proxy.get_name())
        self.index04_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
        self.index_digits = [self.index01_proxy, self.index02_proxy, self.index03_proxy, self.index04_proxy]

        # Middle -------------------------------------------------------------------------------------
        self.middle_digits = []
        self.middle01_proxy = tools_rig_frm.Proxy(name=f"{self.middle_name}01")
        if self.meta:
            self.middle01_proxy.set_parent_uuid(self.meta_middle_proxy.get_uuid())
        self.middle01_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.middle01_proxy.set_initial_position(xyz=pos_middle01)
        self.middle01_proxy.set_locator_scale(scale=loc_scale)
        self.middle01_proxy.set_meta_purpose(value=self.middle01_proxy.get_name())
        self.middle01_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.middle02_proxy = tools_rig_frm.Proxy(name=f"{self.middle_name}02")
        self.middle02_proxy.set_parent_uuid(self.middle01_proxy.get_uuid())
        self.middle02_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.middle02_proxy.set_initial_position(xyz=pos_middle02)
        self.middle02_proxy.set_locator_scale(scale=loc_scale)
        self.middle02_proxy.set_meta_purpose(value=self.middle02_proxy.get_name())
        self.middle02_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.middle03_proxy = tools_rig_frm.Proxy(name=f"{self.middle_name}03")
        self.middle03_proxy.set_parent_uuid(self.middle02_proxy.get_uuid())
        self.middle03_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.middle03_proxy.set_initial_position(xyz=pos_middle03)
        self.middle03_proxy.set_locator_scale(scale=loc_scale)
        self.middle03_proxy.set_meta_purpose(value=self.middle03_proxy.get_name())
        self.middle03_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.middle04_proxy = tools_rig_frm.Proxy(name=f"{self.middle_name}End")
        self.middle04_proxy.set_parent_uuid(self.middle03_proxy.get_uuid())
        self.middle04_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.middle04_proxy.set_initial_position(xyz=pos_middle04)
        self.middle04_proxy.set_locator_scale(scale=loc_scale_end)
        self.middle04_proxy.set_meta_purpose(value=self.middle04_proxy.get_name())
        self.middle04_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
        self.middle_digits = [
            self.middle01_proxy,
            self.middle02_proxy,
            self.middle03_proxy,
            self.middle04_proxy,
        ]

        # Ring -------------------------------------------------------------------------------------
        self.ring_digits = []
        self.ring01_proxy = tools_rig_frm.Proxy(name=f"{self.ring_name}01")
        if self.meta:
            self.ring01_proxy.set_parent_uuid(self.meta_ring_proxy.get_uuid())
        self.ring01_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.ring01_proxy.set_initial_position(xyz=pos_ring01)
        self.ring01_proxy.set_locator_scale(scale=loc_scale)
        self.ring01_proxy.set_meta_purpose(value=self.ring01_proxy.get_name())
        self.ring01_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.ring02_proxy = tools_rig_frm.Proxy(name=f"{self.ring_name}02")
        self.ring02_proxy.set_parent_uuid(self.ring01_proxy.get_uuid())
        self.ring02_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.ring02_proxy.set_initial_position(xyz=pos_ring02)
        self.ring02_proxy.set_locator_scale(scale=loc_scale)
        self.ring02_proxy.set_meta_purpose(value=self.ring02_proxy.get_name())
        self.ring02_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.ring03_proxy = tools_rig_frm.Proxy(name=f"{self.ring_name}03")
        self.ring03_proxy.set_parent_uuid(self.ring02_proxy.get_uuid())
        self.ring03_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.ring03_proxy.set_initial_position(xyz=pos_ring03)
        self.ring03_proxy.set_locator_scale(scale=loc_scale)
        self.ring03_proxy.set_meta_purpose(value=self.ring03_proxy.get_name())
        self.ring03_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.ring04_proxy = tools_rig_frm.Proxy(name=f"{self.ring_name}End")
        self.ring04_proxy.set_parent_uuid(self.ring03_proxy.get_uuid())
        self.ring04_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.ring04_proxy.set_initial_position(xyz=pos_ring04)
        self.ring04_proxy.set_locator_scale(scale=loc_scale_end)
        self.ring04_proxy.set_meta_purpose(value=self.ring04_proxy.get_name())
        self.ring04_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
        self.ring_digits = [self.ring01_proxy, self.ring02_proxy, self.ring03_proxy, self.ring04_proxy]

        # Pinky -------------------------------------------------------------------------------------
        self.pinky_digits = []
        self.pinky01_proxy = tools_rig_frm.Proxy(name=f"{self.pinky_name}01")
        if self.meta:
            self.pinky01_proxy.set_parent_uuid(self.meta_pinky_proxy.get_uuid())
        self.pinky01_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.pinky01_proxy.set_initial_position(xyz=pos_pinky01)
        self.pinky01_proxy.set_locator_scale(scale=loc_scale)
        self.pinky01_proxy.set_meta_purpose(value=self.pinky01_proxy.get_name())
        self.pinky01_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.pinky02_proxy = tools_rig_frm.Proxy(name=f"{self.pinky_name}02")
        self.pinky02_proxy.set_parent_uuid(self.pinky01_proxy.get_uuid())
        self.pinky02_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.pinky02_proxy.set_initial_position(xyz=pos_pinky02)
        self.pinky02_proxy.set_locator_scale(scale=loc_scale)
        self.pinky02_proxy.set_meta_purpose(value=self.pinky02_proxy.get_name())
        self.pinky02_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.pinky03_proxy = tools_rig_frm.Proxy(name=f"{self.pinky_name}03")
        self.pinky03_proxy.set_parent_uuid(self.pinky02_proxy.get_uuid())
        self.pinky03_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.pinky03_proxy.set_initial_position(xyz=pos_pinky03)
        self.pinky03_proxy.set_locator_scale(scale=loc_scale)
        self.pinky03_proxy.set_meta_purpose(value=self.pinky03_proxy.get_name())
        self.pinky03_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.pinky04_proxy = tools_rig_frm.Proxy(name=f"{self.pinky_name}End")
        self.pinky04_proxy.set_parent_uuid(self.pinky03_proxy.get_uuid())
        self.pinky04_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.pinky04_proxy.set_initial_position(xyz=pos_pinky04)
        self.pinky04_proxy.set_locator_scale(scale=loc_scale_end)
        self.pinky04_proxy.set_meta_purpose(value=self.pinky04_proxy.get_name())
        self.pinky04_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
        self.pinky_digits = [self.pinky01_proxy, self.pinky02_proxy, self.pinky03_proxy, self.pinky04_proxy]

        # Extra -------------------------------------------------------------------------------------

        self.extra_digits = []
        self.extra01_proxy = tools_rig_frm.Proxy(name=f"{self.extra_name}01")
        if self.meta:
            self.extra01_proxy.set_parent_uuid(self.meta_extra_proxy.get_uuid())
        self.extra01_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.extra01_proxy.set_initial_position(xyz=pos_extra01)
        self.extra01_proxy.set_locator_scale(scale=loc_scale)
        self.extra01_proxy.set_meta_purpose(value=self.extra01_proxy.get_name())
        self.extra01_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.extra02_proxy = tools_rig_frm.Proxy(name=f"{self.extra_name}02")
        self.extra02_proxy.set_parent_uuid(self.extra01_proxy.get_uuid())
        self.extra02_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.extra02_proxy.set_initial_position(xyz=pos_extra02)
        self.extra02_proxy.set_locator_scale(scale=loc_scale)
        self.extra02_proxy.set_meta_purpose(value=self.extra02_proxy.get_name())
        self.extra02_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.extra03_proxy = tools_rig_frm.Proxy(name=f"{self.extra_name}03")
        self.extra03_proxy.set_parent_uuid(self.extra02_proxy.get_uuid())
        self.extra03_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.extra03_proxy.set_initial_position(xyz=pos_extra03)
        self.extra03_proxy.set_locator_scale(scale=loc_scale)
        self.extra03_proxy.set_meta_purpose(value=self.extra03_proxy.get_name())
        self.extra03_proxy.add_driver_type(driver_type=[tools_rig_const.RiggerDriverTypes.FK])

        self.extra04_proxy = tools_rig_frm.Proxy(name=f"{self.extra_name}End")
        self.extra04_proxy.set_parent_uuid(self.extra03_proxy.get_uuid())
        self.extra04_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_dir_pos_y"))
        self.extra04_proxy.set_initial_position(xyz=pos_extra04)
        self.extra04_proxy.set_locator_scale(scale=loc_scale_end)
        self.extra04_proxy.set_meta_purpose(value=self.extra04_proxy.get_name())
        self.extra04_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.FOLLOWER)
        self.extra_digits = [
            self.extra01_proxy,
            self.extra02_proxy,
            self.extra03_proxy,
            self.extra04_proxy,
        ]
        self.refresh_proxies_list()

    def refresh_proxies_list(self):
        """
        Refreshes the main proxies list used by the module during build
        """
        self.proxies = []
        # Meta
        _activated_meta_digits = []
        if self.meta and self.index:
            _activated_meta_digits.append(self.meta_index_proxy)
        if self.meta and self.middle:
            _activated_meta_digits.append(self.meta_middle_proxy)
        if self.meta and self.ring:
            _activated_meta_digits.append(self.meta_ring_proxy)
        if self.meta and self.pinky:
            _activated_meta_digits.append(self.meta_pinky_proxy)
        if self.meta and self.extra:
            _activated_meta_digits.append(self.meta_extra_proxy)
        self._activated_meta_digits = _activated_meta_digits
        self.proxies.extend(_activated_meta_digits)
        # Fingers
        if self.thumb:
            self.proxies.extend(self.thumb_digits)
        if self.index:
            self.proxies.extend(self.index_digits)
        if self.middle:
            self.proxies.extend(self.middle_digits)
        if self.ring:
            self.proxies.extend(self.ring_digits)
        if self.pinky:
            self.proxies.extend(self.pinky_digits)
        if self.extra:
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
            logger.debug(f"Unable to read proxies from dictionary. Input must be a dictionary.")
            return
        # Determine Digit Activation
        _meta = False
        _thumb = False
        _index = False
        _middle = False
        _ring = False
        _pinky = False
        _extra = False
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(tools_rig_const.RiggerConstants.META_PROXY_PURPOSE)
                if meta_type and self.meta_name in meta_type:
                    _meta = True
                if meta_type and self.thumb_name in meta_type:
                    _thumb = True
                elif meta_type and self.index_name in meta_type:
                    _index = True
                elif meta_type and self.middle_name in meta_type:
                    _middle = True
                elif meta_type and self.ring_name in meta_type:
                    _ring = True
                elif meta_type and self.pinky_name in meta_type:
                    _pinky = True
                elif meta_type and self.extra_name in meta_type:
                    _extra = True
        self.refresh_proxies_list()
        self.read_purpose_matching_proxy_from_dict(proxy_dict)

    def set_proxies_name(self, proxy_name, proxy_value):
        """
        Set names for the proxy controls of a specific finger group based on the provided naming convention.

        Args:
            proxy_name (str): The name of the finger group whose proxies will be renamed.
                              Expected values are: "meta", "thumb", "index", "middle", "ring", "pinky", "extra".
            proxy_value (str): The base string used to construct the new names for the proxies.
        """
        finger_mapping = {
            "meta": self.meta_digits,
            "index": self.index_digits,
            "middle": self.middle_digits,
            "ring": self.ring_digits,
            "pinky": self.pinky_digits,
            "extra": self.extra_digits,
            "thumb": self.thumb_digits,
        }
        proxy_list = finger_mapping[proxy_name]
        for proxy in proxy_list:
            if proxy_name == "meta":
                finger_keys = [key for key in finger_mapping]
                proxy.set_name(f"{finger_keys[proxy_list.index(proxy)+1]}{proxy_value}")
            else:
                if proxy == proxy_list[-1]:
                    proxy.set_name(f"{proxy_value}End")
                else:
                    proxy.set_name(f"{proxy_value+ str(proxy_list.index(proxy)+ 1).zfill(2)}")
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

    def build_proxy(self, **kwargs):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        self.refresh_proxies_list()
        # Set the proxy parent_uuid and driver_uuid for the proxy construction hierarchy
        # (parent_uuid for the skeleton hierarchy, driver_uuid to adjust proxies transformations)
        if self.parent_uuid:
            if self.thumb:
                self.thumb01_proxy.set_parent_uuid(self.parent_uuid)
            if self.meta:
                if self.index:
                    self.meta_index_proxy.set_parent_uuid(self.parent_uuid)
                if self.middle:
                    self.meta_middle_proxy.set_parent_uuid(self.parent_uuid)
                if self.ring:
                    self.meta_ring_proxy.set_parent_uuid(self.parent_uuid)
                if self.pinky:
                    self.meta_pinky_proxy.set_parent_uuid(self.parent_uuid)
                if self.extra:
                    self.meta_extra_proxy.set_parent_uuid(self.parent_uuid)
            else:
                if self.index:
                    self.index01_proxy.set_parent_uuid(self.parent_uuid)
                if self.middle:
                    self.middle01_proxy.set_parent_uuid(self.parent_uuid)
                if self.ring:
                    self.ring01_proxy.set_parent_uuid(self.parent_uuid)
                if self.pinky:
                    self.pinky01_proxy.set_parent_uuid(self.parent_uuid)
                if self.extra:
                    self.extra01_proxy.set_parent_uuid(self.parent_uuid)

        if self.proxies:
            for prx in self.proxies:
                parent_uuid = prx.get_parent_uuid()
                if parent_uuid:
                    prx.set_setup_driver_uuid(parent_uuid)

        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        for digit in self.proxies:
            digit.apply_offset_transform()

        # Apply transform after set the order with build_proxy_setup parent function
        super().build_proxy_setup()  # Passthrough
        # Don't need to set proxy parent for the skeleton hierarchy, it is the same

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
        logger.debug(f'"build_skeleton_hierarchy" function from "{self.get_module_class_name()}" was called.')
        module_uuids = self.get_proxies_uuids()
        jnt_nodes = []
        for proxy in self.proxies:
            joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            if not joint:
                continue

            proxy_obj_path = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
            # Inherit Orientation (Before Parenting)
            core_trans.match_rotate(source=proxy_obj_path, target_list=joint)
            if self.prefix == core_naming.NamingConstants.Prefix.RIGHT:
                cmds.rotate(-180, joint, rotateX=True, relative=True, objectSpace=True)
                cmds.makeIdentity(joint, a=True, r=True)
            if "thumb" in joint.get_short_name():
                cmds.rotate(-90, joint, rotateY=True, relative=True, objectSpace=True)
                cmds.makeIdentity(joint, a=True, r=True)
            # Inherit Rotation Order
            proxy_rotation_order = cmds.getAttr(f"{proxy_obj_path}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
            cmds.setAttr(f"{joint}.rotateOrder", proxy_rotation_order)
            # Parent Joint (Internal Proxies)
            parent_uuid = proxy.get_parent_uuid()
            if parent_uuid in module_uuids:
                parent_joint_node = tools_rig_utils.find_joint_from_uuid(parent_uuid)
                core_hrchy.parent(source_objects=joint, target_parent=parent_joint_node)
            jnt_nodes.append(joint)

        # Parent Joints (External Proxies)
        for proxy in self.proxies:
            parent_uuid = proxy.get_parent_uuid()
            if parent_uuid not in module_uuids:
                joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
                parent_joint_node = tools_rig_utils.find_joint_from_uuid(parent_uuid)
                core_hrchy.parent(source_objects=joint, target_parent=parent_joint_node)
        cmds.select(clear=True)

    def build_control_rig_pose(self):
        """
        Builds the rig pose on a biped leg.
        """
        import gt.core.pose as core_pose

        # get joints
        (
            meta_joints,
            thumb_joints,
            index_joints,
            middle_joints,
            ring_joints,
            pinky_joints,
            extra_joints,
            end_joints,
        ) = self.get_joints()

        not_thumb_joints = index_joints + middle_joints + ring_joints + pinky_joints + extra_joints
        not_thumb_joints = [ntj.get_short_name() for ntj in not_thumb_joints]

        # the straighten process needs to go in order, from roots to leaves
        if self.thumb:
            # thumb_joints = [tj.get_short_name() for tj in thumb_joints]
            for jnt in thumb_joints:
                cmds.setAttr(jnt + ".rotate", 0, 0, 0)
                cmds.setAttr(jnt + ".jointOrient", 0, 0, 0)
            # straighten thumb
            core_pose.straighten_objs_by_side(
                thumb_joints,
                forward_rot=90,
                mirror_prefix=core_naming.NamingConstants.Prefix.RIGHT,
            )
            # apply thumb root rotation
            thumb_root = thumb_joints[0].get_short_name()
            cmds.setAttr(f"{thumb_root}.rotate", 170, 25, -25)

        # skip the metas if they don't inherit the parent orientation
        # meta_joints = [mj.get_short_name() for mj in meta_joints]
        # core_pose.straighten_objs_by_side(meta_joints, mirror_prefix=core_naming.NamingConstants.Prefix.RIGHT,)
        core_pose.straighten_objs_by_side(not_thumb_joints, mirror_prefix=core_naming.NamingConstants.Prefix.RIGHT)

    def build_rig(self, project_prefix=None, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            project_prefix (str, optional): If provided, the created elements receive this string as an extra prefix.
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """
        # Get Elements -----------------------------------------------------------------------------------------
        (
            meta_joints,
            thumb_joints,
            index_joints,
            middle_joints,
            ring_joints,
            pinky_joints,
            extra_joints,
            end_joints,
        ) = self.get_joints()

        proxy_joint_map = self.get_proxy_joint_map()

        # Helpful Lists
        unfiltered_finger_lists = [
            thumb_joints,
            index_joints,
            middle_joints,
            ring_joints,
            pinky_joints,
            extra_joints,
        ]
        finger_lists = [sublist for sublist in unfiltered_finger_lists if sublist]  # Only non-empty
        joints_no_end = list(set(proxy_joint_map.keys()) - set(end_joints))  # Remove ends
        joints_base_only = [sublist[0] for sublist in finger_lists if sublist]  # Only first element of each list
        end_joints_no_thumb = list(set(end_joints) - set(thumb_joints))

        # Setup name
        setup_name = self.setup_name

        # Get Parent Elements
        direction_crv = tools_rig_utils.find_ctrl_global_offset()
        module_parent_jnt = tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())
        fingers_automation_grp = tools_rig_utils.get_automation_group(f"{setup_name}Automation")
        ik_handles_grp_name = (
            f"{self._assemble_node_name(setup_name)}_ikHandles_{core_naming.NamingConstants.Suffix.GRP}"
        )
        ik_handles_grp = core_hrchy.create_group(ik_handles_grp_name)
        core.hierarchy.parent(source_objects=ik_handles_grp, target_parent=fingers_automation_grp)

        # Set Joint Colors ------------------------------------------------------------------------------------
        for jnt in joints_no_end:
            core_color.set_color_viewport(obj_list=jnt, rgb_color=core_color.ColorConstants.RigJoint.OFFSET)
        for jnt in end_joints:
            core_color.set_color_viewport(obj_list=jnt, rgb_color=core_color.ColorConstants.RigJoint.END)

        # Control Parent (Main System Driver) ------------------------------------------------------------------
        wrist_grp_name = f"{self._assemble_node_name('fingers')}_{core_naming.NamingConstants.Suffix.DRIVEN}"
        wrist_grp = core_hrchy.create_group(name=wrist_grp_name)
        if module_parent_jnt:
            cmds.matchTransform(wrist_grp, module_parent_jnt)
        else:  # No parent, average the position of the fingers group
            base_center_pos = core_math.get_transforms_center_position(transform_list=joints_base_only)
            cmds.xform(wrist_grp, translation=base_center_pos, worldSpace=True)
        core.hierarchy.parent(source_objects=wrist_grp, target_parent=direction_crv)

        # Fingers System Ctrl ---------------------------------------------------------------------------------
        # Find Position and Scale
        end_center_pos = core_math.get_transforms_center_position(transform_list=end_joints_no_thumb)
        if module_parent_jnt:  # Has Parent
            distance_from_wrist = core_math.dist_path_sum(input_list=[module_parent_jnt, end_center_pos])
        else:
            base_center_pos = core_math.get_transforms_center_position(transform_list=joints_base_only)
            distance_from_wrist = core_math.dist_path_sum(input_list=[base_center_pos, end_center_pos])
        # No fingers case
        if not end_joints_no_thumb:
            distance_from_wrist = 19.279
        wrist_directional_pos = core_trans.get_directional_position(object_name=wrist_grp, tolerance=0)  # 0 = No Center
        is_right_side = wrist_directional_pos == -1  # Right Side?
        fingers_ctrl_scale = distance_from_wrist * 0.1
        if self.prefix == core_naming.NamingConstants.Prefix.LEFT:
            ctrl_color = core_color.ColorConstants.RigControl.LEFT
        elif self.prefix == core_naming.NamingConstants.Prefix.RIGHT:
            ctrl_color = core_color.ColorConstants.RigControl.RIGHT
        else:
            ctrl_color = core_color.ColorConstants.RigControl.CENTER

        # Finger Control (Main)
        fingers_ctrl, fingers_ctrl_grps = self.create_rig_control(
            control_base_name=setup_name,
            parent_obj=wrist_grp,
            curve_file_name="target_squared",
            match_obj=wrist_grp,
            shape_rot_offset=(90, 0, 90),
            shape_scale=fingers_ctrl_scale,
            color=ctrl_color,
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=fingers_ctrl, driver_type=tools_rig_const.RiggerDriverTypes.GENERIC, proxy_purpose="fingers"
        )
        # Determine Side Orientation
        if is_right_side:
            cmds.rotate(180, fingers_ctrl_grps[0], rotateY=True, relative=True, objectSpace=True)
            cmds.rotate(180, fingers_ctrl_grps[0], rotateX=True, relative=True, objectSpace=True)
        # Position
        fingers_move_offset = 23
        # fingers_move_offset = distance_from_wrist * 1.2 - Commenting for normalization
        cmds.move(
            fingers_move_offset,
            fingers_ctrl_grps[0],
            moveX=True,
            relative=True,
            objectSpace=True,
        )

        # Fingers Visibility (Attributes)
        cmds.addAttr(
            fingers_ctrl,
            ln="showFkFingerCtrls",
            at="bool",
            k=True,
            niceName="Show FK Finger Ctrls",
        )

        # Add Custom Attributes
        finger_spread = {
            self.index_name: {"spread": 18, "status": self.index},
            self.middle_name: {"spread": 1.2, "status": self.middle},
            self.ring_name: {"spread": 12, "status": self.ring},
            self.pinky_name: {"spread": 41, "status": self.pinky},
            self.thumb_name: {"spread": 6, "status": self.thumb},
            self.extra_name: {"spread": 50, "status": self.extra},
        }
        core_attr.add_separator_attr(target_object=fingers_ctrl, attr_name="fingerPoses")
        if self.thumb:
            core_attr.add_attr(
                obj_list=fingers_ctrl,
                attributes="fistPoseLimitThumb01",
                attr_type="float",
                is_keyable=False,
                default=0,
            )
            core_attr.add_attr(
                obj_list=fingers_ctrl,
                attributes="fistPoseLimitThumb02",
                attr_type="float",
                is_keyable=False,
                default=-17,
            )
            core_attr.add_attr(
                obj_list=fingers_ctrl,
                attributes="fistPoseLimitThumb03",
                attr_type="float",
                is_keyable=False,
                default=-50,
            )
            core_attr.add_attr(
                obj_list=fingers_ctrl, attributes="rotMultiplierThumb", attr_type="float", is_keyable=False, default=0.3
            )
        core_attr.add_attr(obj_list=fingers_ctrl, attributes="curl", attr_type="float")
        for meta, values in finger_spread.items():
            if values["status"]:
                core_attr.add_attr(obj_list=fingers_ctrl, attributes=f"{meta}Curl", attr_type="float")
        core_attr.add_attr(obj_list=fingers_ctrl, attributes="spread", attr_type="float", minimum=-10, maximum=10)
        core_attr.add_separator_attr(target_object=fingers_ctrl, attr_name="fingersAttributes")
        left_fingers_minz_scale = 1
        left_fingers_maxz_scale = 5

        cmds.setAttr(f"{fingers_ctrl}.minScaleZLimit", left_fingers_minz_scale)
        cmds.setAttr(f"{fingers_ctrl}.maxScaleZLimit", left_fingers_maxz_scale)
        cmds.setAttr(f"{fingers_ctrl}.minScaleZLimitEnable", 1)
        cmds.setAttr(f"{fingers_ctrl}.maxScaleZLimitEnable", 1)

        # Global Spread & Curl System
        global_rot_rev_name = f"{self._assemble_node_name(setup_name)}_global_rot_rev"

        global_rot_rev = cmds.createNode("multiplyDivide", n=global_rot_rev_name)
        cmds.setAttr(f"{global_rot_rev}.input2X", -1)
        cmds.connectAttr(f"{fingers_ctrl}.curl", f"{global_rot_rev}.input1X")
        cmds.connectAttr(f"{fingers_ctrl}.spread", f"{global_rot_rev}.input1Y")

        for meta, values in finger_spread.items():
            if values["status"]:
                meta_sum_name = f"{self._assemble_node_name(meta)}_sum"
                meta_curl_clamp_name = f"{self._assemble_node_name(meta)}_curl_clamp"
                meta_global_curl_rev_name = f"{self._assemble_node_name(meta)}_global_curl_rev"
                meta_rot_mult_name = f"{self._assemble_node_name(meta)}_rot_mult"

                curl_plus_minus = cmds.createNode("plusMinusAverage", n=meta_sum_name)
                curl_clamp = cmds.createNode("clamp", n=meta_curl_clamp_name)
                meta_curl_rev = cmds.createNode("multiplyDivide", n=meta_global_curl_rev_name)
                cmds.setAttr(f"{meta_curl_rev}.input2X", -1)
                cmds.connectAttr(f"{fingers_ctrl}.{meta}Curl", f"{meta_curl_rev}.input1X")
                cmds.connectAttr(f"{meta_curl_rev}.outputX", f"{curl_plus_minus}.input2D[0].input2Dx")
                cmds.connectAttr(f"{global_rot_rev}.outputX", f"{curl_plus_minus}.input2D[1].input2Dx")
                if meta == "thumb":
                    cmds.setAttr(f"{curl_clamp}.maxR", 20)
                    cmds.setAttr(f"{curl_clamp}.maxG", 20)
                    cmds.setAttr(f"{curl_clamp}.maxB", 20)
                    curl_mult = cmds.createNode("multiplyDivide", n=meta_rot_mult_name)
                    cmds.connectAttr(f"{curl_plus_minus}.output2Dx", f"{curl_mult}.input1X")
                    cmds.connectAttr(f"{fingers_ctrl}.fistPoseLimitThumb01", f"{curl_clamp}.minR")
                    cmds.connectAttr(f"{fingers_ctrl}.fistPoseLimitThumb02", f"{curl_clamp}.minG")
                    cmds.connectAttr(f"{fingers_ctrl}.fistPoseLimitThumb03", f"{curl_clamp}.minB")
                    cmds.connectAttr(f"{fingers_ctrl}.rotMultiplierThumb", f"{curl_mult}.input2X")
                    cmds.connectAttr(f"{curl_mult}.outputX", f"{curl_clamp}.inputR")
                    cmds.connectAttr(f"{curl_mult}.outputX", f"{curl_clamp}.inputG")
                    cmds.connectAttr(f"{curl_mult}.outputX", f"{curl_clamp}.inputB")

                else:
                    cmds.setAttr(f"{curl_clamp}.maxR", 40)
                    cmds.setAttr(f"{curl_clamp}.minR", -90)
                    cmds.connectAttr(f"{curl_plus_minus}.output2Dx", f"{curl_clamp}.inputR")

        core_attr.hide_lock_default_attrs(
            obj_list=fingers_ctrl, translate=True, rotate=True, scale=True, visibility=True
        )

        # Create Controls -------------------------------------------------------------------------------------
        # Meta
        for meta_jnt in meta_joints:
            meta_proxy = proxy_joint_map.get(meta_jnt)
            ctrl_color = core_color.get_directional_color(object_name=meta_jnt)
            meta_ctrl, meta_ctrl_grps = self.create_rig_control(
                control_base_name=meta_proxy.get_name(),
                parent_obj=wrist_grp,
                curve_file_name="circle",
                extra_parent_groups=["driver"],
                match_obj=meta_jnt,
                shape_rot_offset=(180, 180, -90),
                shape_scale=1,
                color=ctrl_color,
            )[:2]
            if self.meta:
                cmds.connectAttr(f"{fingers_ctrl}.showFkFingerCtrls", f"{meta_ctrl_grps[0]}.visibility")
            self._add_driver_uuid_attr(
                target_driver=meta_ctrl,
                driver_type=tools_rig_const.RiggerDriverTypes.FK,
                proxy_purpose=meta_proxy,
            )
            core_attr.hide_lock_default_attrs(obj_list=meta_ctrl, translate=True, scale=True, visibility=True)
            cmds.parentConstraint(meta_ctrl, meta_jnt)

        # Fingers
        for finger_list in finger_lists:
            if not finger_list:
                continue  # Ignore skipped fingers
            # Unpack elements
            digit_base = finger_list[0]
            digit_middle = finger_list[1]
            digit_tip = finger_list[2]
            digit_tip_end = finger_list[3]
            # Determine finger scale
            finger_scale = core_math.dist_path_sum([digit_base, digit_middle, digit_tip, digit_tip_end]) * 0.08
            # Create FK Controls
            last_ctrl = None
            main_driver = None
            for finger_jnt in finger_list:
                finger_proxy = proxy_joint_map.get(finger_jnt)
                meta_type = tools_rig_utils.get_meta_purpose_from_dict(finger_proxy.get_metadata())
                finger_type = core_str.remove_digits(meta_type)
                if meta_type and str(meta_type).endswith("End"):
                    continue  # Skip end joints
                ctrl_color = core_color.get_directional_color(object_name=finger_jnt)
                ctrl, finger_ctrl_grps = self.create_rig_control(
                    control_base_name=finger_proxy.get_name(),
                    parent_obj=wrist_grp,
                    curve_file_name="circle",
                    extra_parent_groups=["dataCurl", "driver"],
                    match_obj=finger_jnt,
                    shape_rot_offset=(180, 180, -90),
                    shape_scale=finger_scale,
                    color=ctrl_color,
                )[:2]
                if "01" in str(meta_type):
                    main_driver = finger_ctrl_grps[1]
                    if "thumb" in str(meta_type):
                        self._add_driver_uuid_attr(
                            target_driver=ctrl,
                            driver_type=tools_rig_const.RiggerDriverTypes.FK,
                            proxy_purpose=finger_proxy,
                        )
                        cmds.connectAttr(f"{fingers_ctrl}.showFkFingerCtrls", f"{main_driver}.visibility")
                    else:
                        self._add_driver_uuid_attr(
                            target_driver=ctrl,
                            driver_type=tools_rig_const.RiggerDriverTypes.FK,
                            proxy_purpose=finger_proxy,
                        )
                        last_ctrl = self._assemble_ctrl_name(name=f"{finger_type}{self.meta_name}")
                        if not self.meta:
                            cmds.connectAttr(f"{fingers_ctrl}.showFkFingerCtrls", f"{main_driver}.visibility")
                else:
                    self._add_driver_uuid_attr(
                        target_driver=ctrl,
                        driver_type=tools_rig_const.RiggerDriverTypes.FK,
                        proxy_purpose=finger_proxy,
                    )
                core_attr.hide_lock_default_attrs(obj_list=ctrl, translate=True, scale=True, visibility=True)
                cmds.parentConstraint(ctrl, finger_jnt)
                # Create FK Hierarchy
                if last_ctrl:
                    core.hierarchy.parent(source_objects=finger_ctrl_grps[0], target_parent=last_ctrl)
                last_ctrl = ctrl

                # Create Curl Connection
                if "01" in str(meta_type):
                    if "thumb" not in str(meta_type):
                        if self.meta:
                            meta_finger_name = f"{finger_type}Meta"
                            meta_driver_name = f"{self._assemble_node_name(meta_finger_name)}_driver"
                            meta_curl_rev_name = f"{self._assemble_node_name(finger_proxy.get_name())}_meta_curl_rev"
                            meta_attr_name = meta_finger_name

                            core_attr.add_attr(obj_list=fingers_ctrl, attributes=meta_attr_name, attr_type="float")
                            meta_curl_rev = cmds.createNode("multiplyDivide", n=meta_curl_rev_name)
                            cmds.setAttr(f"{meta_curl_rev}.input2X", -1)
                            cmds.connectAttr(f"{fingers_ctrl}.{meta_attr_name}", f"{meta_curl_rev}.input1X")
                            cmds.connectAttr(f"{meta_curl_rev}.outputX", f"{meta_driver_name}.rotateZ")

                curl_rev_name = f"{self._assemble_node_name(finger_proxy.get_name())}_curl_rev"
                curl_rev = cmds.createNode("multiplyDivide", n=curl_rev_name)
                core_attr.add_attr(obj_list=fingers_ctrl, attributes=finger_proxy.get_name(), attr_type="float")
                cmds.setAttr(f"{curl_rev}.input2X", -1)
                cmds.connectAttr(f"{fingers_ctrl}.{finger_proxy.get_name()}", f"{curl_rev}.input1X")
                cmds.connectAttr(f"{curl_rev}.outputX", f"{finger_ctrl_grps[2]}.rotateZ")

                if "03" in str(meta_type):
                    core_attr.add_attr(obj_list=fingers_ctrl, attributes=f"{finger_type}Spread", attr_type="float")
                    cmds.connectAttr(f"{fingers_ctrl}.{finger_type}Spread", f"{main_driver}.rotateY")
                    core_attr.add_attr(obj_list=fingers_ctrl, attributes=f"{finger_type}Twist", attr_type="float")
                    cmds.connectAttr(f"{fingers_ctrl}.{finger_type}Twist", f"{main_driver}.rotateX")

                # Global Spread & Curl System Connection3
                curl_clamp_name = f"{self._assemble_node_name(finger_type)}_curl_clamp"
                spread_mult_name = f"{self._assemble_node_name(finger_type)}_spread_mult"

                if "thumb" in str(meta_type):
                    if "01" in str(meta_type):
                        cmds.connectAttr(f"{curl_clamp_name}.outputR", f"{finger_ctrl_grps[1]}.rotateZ")
                    elif "02" in str(meta_type):
                        cmds.connectAttr(f"{curl_clamp_name}.outputG", f"{finger_ctrl_grps[1]}.rotateZ")
                    elif "03" in str(meta_type):
                        cmds.connectAttr(f"{curl_clamp_name}.outputB", f"{finger_ctrl_grps[1]}.rotateZ")
                else:
                    cmds.connectAttr(f"{curl_clamp_name}.outputR", f"{finger_ctrl_grps[1]}.rotateZ")
                if "01" in str(meta_type):
                    mult_spread = cmds.createNode("multiplyDivide", n=spread_mult_name)
                    if "thumb" in finger_type or "index" in finger_type:
                        cmds.setAttr(f"{mult_spread}.input2X", -(finger_spread[finger_type]["spread"] / 10))
                        cmds.connectAttr(f"{fingers_ctrl}.spread", f"{mult_spread}.input1X")
                        cmds.connectAttr(f"{mult_spread}.outputX", f"{finger_ctrl_grps[2]}.rotateY")
                    else:
                        cmds.setAttr(f"{mult_spread}.input2X", finger_spread[finger_type]["spread"] / 10)
                        cmds.connectAttr(f"{fingers_ctrl}.spread", f"{mult_spread}.input1X")
                        cmds.connectAttr(f"{mult_spread}.outputX", f"{finger_ctrl_grps[2]}.rotateY")

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [wrist_grp]

    def build_rig_post(self):
        """
        Runs post rig script phase.
        This step runs after the execution of "build_rig" is completed.
        Usually used to define automation or connections that require external elements to exist.
        """
        joints_to_delete = []
        if self.index:
            index_end_jnt = tools_rig_utils.find_joint_from_uuid(self.index04_proxy.get_uuid())
            joints_to_delete.append(index_end_jnt)
        if self.middle:
            middle_end_jnt = tools_rig_utils.find_joint_from_uuid(self.middle04_proxy.get_uuid())
            joints_to_delete.append(middle_end_jnt)
        if self.ring:
            ring_end_jnt = tools_rig_utils.find_joint_from_uuid(self.ring04_proxy.get_uuid())
            joints_to_delete.append(ring_end_jnt)
        if self.pinky:
            pinky_end_jnt = tools_rig_utils.find_joint_from_uuid(self.pinky04_proxy.get_uuid())
            joints_to_delete.append(pinky_end_jnt)
        if self.thumb:
            thumb_end = tools_rig_utils.find_joint_from_uuid(self.thumb04_proxy.get_uuid())
            joints_to_delete.append(thumb_end)
        if self.extra:
            extra_end = tools_rig_utils.find_joint_from_uuid(self.extra04_proxy.get_uuid())
            joints_to_delete.append(extra_end)

        for jnt in joints_to_delete:
            if jnt and cmds.objExists(jnt):
                cmds.delete(jnt)

        self._parent_module_children_drivers()

    # ------------------------------------------- Helpers -------------------------------------------
    def get_joints(self):
        """
        Gets the fingers joints.

        Returns:
            meta_joints (list)
            thumb_joints (list)
            index_joints (list)
            middle_joints (list)
            ring_joints (list)
            pinky_joints (list)
            extra_joints (list): all the joints without a known base name
            end_joints (list): the last joints of every digit
        """

        meta_joints = []
        thumb_joints = []
        index_joints = []
        middle_joints = []
        ring_joints = []
        pinky_joints = []
        extra_joints = []
        end_joints = []

        # Get Joints
        for proxy in self.proxies:

            finger_jnt = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            meta_type = tools_rig_utils.get_meta_purpose_from_dict(proxy.get_metadata())
            if not finger_jnt:
                continue  # Skipped finger
            if not meta_type:
                continue  # Unexpected Proxy

            # Store Joints In Lists/Dict
            if self.thumb_name in meta_type:
                thumb_joints.append(finger_jnt)
            elif self.index_name in meta_type and self.meta_name not in meta_type:
                index_joints.append(finger_jnt)
            elif self.middle_name in meta_type and self.meta_name not in meta_type:
                middle_joints.append(finger_jnt)
            elif self.ring_name in meta_type and self.meta_name not in meta_type:
                ring_joints.append(finger_jnt)
            elif self.pinky_name in meta_type and self.meta_name not in meta_type:
                pinky_joints.append(finger_jnt)
            elif self.extra_name in meta_type and self.meta_name not in meta_type:
                extra_joints.append(finger_jnt)
            elif self.meta_name in meta_type:
                meta_joints.append(finger_jnt)
            # End Joints
            if meta_type and str(meta_type).endswith("End"):
                end_joints.append(finger_jnt)

        return (
            meta_joints,
            thumb_joints,
            index_joints,
            middle_joints,
            ring_joints,
            pinky_joints,
            extra_joints,
            end_joints,
        )

    def get_proxy_joint_map(self):
        """
        Gets the proxy-joint map.

        Returns:
            proxy_joint_map (dict): key is joint, value is proxy
        """
        proxy_joint_map = {}  # Key = Joint, Value = Proxy

        for proxy in self.proxies:
            finger_jnt = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            meta_type = tools_rig_utils.get_meta_purpose_from_dict(proxy.get_metadata())
            if not finger_jnt:
                continue  # Skipped finger
            if not meta_type:
                continue  # Unexpected Proxy
            proxy_joint_map[finger_jnt] = proxy  # Add to map

        return proxy_joint_map

    # ------------------------------------------- Extra Module Setters -------------------------------------------
    def set_thumb_name(self, name):
        """
        Sets the thumb digit name by editing the metadata value associated with it.
        Args:
            name (str): New name thumb digit name. If empty the default "thumb" is used instead.
        """
        self.thumb_name = name

    def set_index_name(self, name):
        """
        Sets the index digit name by editing the metadata value associated with it.
        Args:
            name (str): New name index digit name. If empty the default "index" is used instead.
        """
        self.index_name = name

    def set_middle_name(self, name):
        """
        Sets the middle digit name by editing the metadata value associated with it.
        Args:
            name (str): New name middle digit name. If empty the default "middle" is used instead.
        """
        self.middle_name = name

    def set_ring_name(self, name):
        """
        Sets the ring digit name by editing the metadata value associated with it.
        Args:
            name (str): New name ring digit name. If empty the default "ring" is used instead.
        """
        self.ring_name = name

    def set_pinky_name(self, name):
        """
        Sets the pinky digit name by editing the metadata value associated with it.
        Args:
            name (str): New name pinky digit name. If empty the default "pinky" is used instead.
        """
        self.pinky_name = name

    def set_extra_name(self, name):
        """
        Sets the extra digit name by editing the metadata value associated with it.
        Args:
            name (str): New name extra digit name. If empty the default "extra" is used instead.
        """
        self.extra_name = name


class ModuleBipedFingersLeft(ModuleBipedFingers):
    def __init__(
        self,
        name="L Fingers",
        prefix=core_naming.NamingConstants.Prefix.LEFT,
        suffix=None,
        meta=True,
        thumb=True,
        index=True,
        middle=True,
        ring=True,
        pinky=True,
        extra=False,
    ):
        """
        Initialize a left ModuleBipedFingers instance.

        Args:
            name (str, optional): The name of the module. Defaults to "L Fingers".
            prefix (str or None, optional): Optional prefix for naming controls.
            suffix (str or None, optional): Optional suffix for naming controls.
            meta (bool, optional): Whether to include meta finger controls.
            thumb (bool, optional): Whether to include the thumb finger.
            index (bool, optional): Whether to include the index finger.
            middle (bool, optional): Whether to include the middle finger.
            ring (bool, optional): Whether to include the ring finger.
            pinky (bool, optional): Whether to include the pinky finger.
            extra (bool, optional): Whether to include extra finger controls beyond the standard five.
        """
        super().__init__(
            name=name,
            prefix=prefix,
            suffix=suffix,
            meta=meta,
            thumb=thumb,
            index=index,
            middle=middle,
            ring=ring,
            pinky=pinky,
            extra=extra,
        )

        # Describe Positions
        if self.meta:
            if self.index:
                pos_meta_index = core_trans.Vector3(x=63, y=130.4, z=3.5)
                self.meta_index_proxy.set_initial_position(xyz=pos_meta_index)
            if self.middle:
                pos_meta_middle = core_trans.Vector3(x=63, y=130.4, z=1.1)
                self.meta_middle_proxy.set_initial_position(xyz=pos_meta_middle)
            if self.ring:
                pos_meta_ring = core_trans.Vector3(x=63, y=130.4, z=-1.1)
                self.meta_ring_proxy.set_initial_position(xyz=pos_meta_ring)
            if self.pinky:
                pos_meta_pinky = core_trans.Vector3(x=63, y=130.4, z=-3.2)
                self.meta_pinky_proxy.set_initial_position(xyz=pos_meta_pinky)
            if self.extra:
                pos_meta_extra = core_trans.Vector3(x=63, y=130.4, z=-5.3)
                self.meta_extra_proxy.set_initial_position(xyz=pos_meta_extra)
        if self.thumb:
            pos_thumb01 = core_trans.Vector3(x=60.8, y=130.4, z=2.9)
            pos_thumb02 = pos_thumb01 + core_trans.Vector3(z=4.4)
            pos_thumb03 = pos_thumb02 + core_trans.Vector3(z=4.4)
            pos_thumb04 = pos_thumb03 + core_trans.Vector3(z=4.6)
            self.thumb01_proxy.set_initial_position(xyz=pos_thumb01)
            self.thumb02_proxy.set_initial_position(xyz=pos_thumb02)
            self.thumb03_proxy.set_initial_position(xyz=pos_thumb03)
            self.thumb04_proxy.set_initial_position(xyz=pos_thumb04)
        if self.index:
            pos_index01 = core_trans.Vector3(x=66.9, y=130.4, z=3.5)
            pos_index02 = pos_index01 + core_trans.Vector3(x=3.2)
            pos_index03 = pos_index02 + core_trans.Vector3(x=4.1)
            pos_index04 = pos_index03 + core_trans.Vector3(x=3.3)
            self.index01_proxy.set_initial_position(xyz=pos_index01)
            self.index02_proxy.set_initial_position(xyz=pos_index02)
            self.index03_proxy.set_initial_position(xyz=pos_index03)
            self.index04_proxy.set_initial_position(xyz=pos_index04)
        if self.middle:
            pos_middle01 = core_trans.Vector3(x=66.9, y=130.4, z=1.1)
            pos_middle02 = pos_middle01 + core_trans.Vector3(x=3.8)
            pos_middle03 = pos_middle02 + core_trans.Vector3(x=3.7)
            pos_middle04 = pos_middle03 + core_trans.Vector3(x=3.6)
            self.middle01_proxy.set_initial_position(xyz=pos_middle01)
            self.middle02_proxy.set_initial_position(xyz=pos_middle02)
            self.middle03_proxy.set_initial_position(xyz=pos_middle03)
            self.middle04_proxy.set_initial_position(xyz=pos_middle04)
        if self.ring:
            pos_ring01 = core_trans.Vector3(x=66.9, y=130.4, z=-1.1)
            pos_ring02 = pos_ring01 + core_trans.Vector3(x=3.5)
            pos_ring03 = pos_ring02 + core_trans.Vector3(x=3.6)
            pos_ring04 = pos_ring03 + core_trans.Vector3(x=3.5)
            self.ring01_proxy.set_initial_position(xyz=pos_ring01)
            self.ring02_proxy.set_initial_position(xyz=pos_ring02)
            self.ring03_proxy.set_initial_position(xyz=pos_ring03)
            self.ring04_proxy.set_initial_position(xyz=pos_ring04)
        if self.pinky:
            pos_pinky01 = core_trans.Vector3(x=66.9, y=130.4, z=-3.2)
            pos_pinky02 = pos_pinky01 + core_trans.Vector3(x=3.3)
            pos_pinky03 = pos_pinky02 + core_trans.Vector3(x=3.2)
            pos_pinky04 = pos_pinky03 + core_trans.Vector3(x=3.5)
            self.pinky01_proxy.set_initial_position(xyz=pos_pinky01)
            self.pinky02_proxy.set_initial_position(xyz=pos_pinky02)
            self.pinky03_proxy.set_initial_position(xyz=pos_pinky03)
            self.pinky04_proxy.set_initial_position(xyz=pos_pinky04)
        if self.extra:
            pos_extra01 = core_trans.Vector3(x=66.9, y=130.4, z=-5.3)
            pos_extra02 = pos_extra01 + core_trans.Vector3(x=3)
            pos_extra03 = pos_extra02 + core_trans.Vector3(x=3)
            pos_extra04 = pos_extra03 + core_trans.Vector3(x=3.3)
            self.extra01_proxy.set_initial_position(xyz=pos_extra01)
            self.extra02_proxy.set_initial_position(xyz=pos_extra02)
            self.extra03_proxy.set_initial_position(xyz=pos_extra03)
            self.extra04_proxy.set_initial_position(xyz=pos_extra04)


class ModuleBipedFingersRight(ModuleBipedFingers):
    def __init__(
        self,
        name="R Fingers",
        prefix=core_naming.NamingConstants.Prefix.RIGHT,
        suffix=None,
        meta=True,
        thumb=True,
        index=True,
        middle=True,
        ring=True,
        pinky=True,
        extra=False,
    ):
        """
        Initialize a right ModuleBipedFingers instance.

        Args:
            name (str, optional): The name of the module. Defaults to "R Fingers".
            prefix (str or None, optional): Optional prefix for naming controls.
            suffix (str or None, optional): Optional suffix for naming controls.
            meta (bool, optional): Whether to include meta finger controls.
            thumb (bool, optional): Whether to include the thumb finger.
            index (bool, optional): Whether to include the index finger.
            middle (bool, optional): Whether to include the middle finger.
            ring (bool, optional): Whether to include the ring finger.
            pinky (bool, optional): Whether to include the pinky finger.
            extra (bool, optional): Whether to include extra finger controls beyond the standard five.
        """
        super().__init__(
            name=name,
            prefix=prefix,
            suffix=suffix,
            meta=meta,
            thumb=thumb,
            index=index,
            middle=middle,
            ring=ring,
            pinky=pinky,
            extra=extra,
        )

        # Describe Positions
        if self.meta:
            if self.index:
                pos_meta_index = core_trans.Vector3(x=-63, y=130.4, z=3.5)
                self.meta_index_proxy.set_initial_position(xyz=pos_meta_index)
            if self.middle:
                pos_meta_middle = core_trans.Vector3(x=-63, y=130.4, z=1.1)
                self.meta_middle_proxy.set_initial_position(xyz=pos_meta_middle)
            if self.ring:
                pos_meta_ring = core_trans.Vector3(x=-63, y=130.4, z=-1.1)
                self.meta_ring_proxy.set_initial_position(xyz=pos_meta_ring)
            if self.pinky:
                pos_meta_pinky = core_trans.Vector3(x=-63, y=130.4, z=-3.2)
                self.meta_pinky_proxy.set_initial_position(xyz=pos_meta_pinky)
            if self.extra:
                pos_meta_extra = core_trans.Vector3(x=-63, y=130.4, z=-5.3)
                self.meta_extra_proxy.set_initial_position(xyz=pos_meta_extra)
        if self.thumb:
            pos_thumb01 = core_trans.Vector3(x=-60.8, y=130.4, z=2.9)
            pos_thumb02 = pos_thumb01 + core_trans.Vector3(z=4.4)
            pos_thumb03 = pos_thumb02 + core_trans.Vector3(z=4.4)
            pos_thumb04 = pos_thumb03 + core_trans.Vector3(z=4.6)
            self.thumb01_proxy.set_initial_position(xyz=pos_thumb01)
            self.thumb02_proxy.set_initial_position(xyz=pos_thumb02)
            self.thumb03_proxy.set_initial_position(xyz=pos_thumb03)
            self.thumb04_proxy.set_initial_position(xyz=pos_thumb04)
        if self.index:
            pos_index01 = core_trans.Vector3(x=-66.9, y=130.4, z=3.5)
            pos_index02 = pos_index01 + core_trans.Vector3(x=-3.2)
            pos_index03 = pos_index02 + core_trans.Vector3(x=-4.1)
            pos_index04 = pos_index03 + core_trans.Vector3(x=-3.3)
            self.index01_proxy.set_initial_position(xyz=pos_index01)
            self.index02_proxy.set_initial_position(xyz=pos_index02)
            self.index03_proxy.set_initial_position(xyz=pos_index03)
            self.index04_proxy.set_initial_position(xyz=pos_index04)
        if self.middle:
            pos_middle01 = core_trans.Vector3(x=-66.9, y=130.4, z=1.1)
            pos_middle02 = pos_middle01 + core_trans.Vector3(x=-3.8)
            pos_middle03 = pos_middle02 + core_trans.Vector3(x=-3.7)
            pos_middle04 = pos_middle03 + core_trans.Vector3(x=-3.6)
            self.middle01_proxy.set_initial_position(xyz=pos_middle01)
            self.middle02_proxy.set_initial_position(xyz=pos_middle02)
            self.middle03_proxy.set_initial_position(xyz=pos_middle03)
            self.middle04_proxy.set_initial_position(xyz=pos_middle04)
        if self.ring:
            pos_ring01 = core_trans.Vector3(x=-66.9, y=130.4, z=-1.1)
            pos_ring02 = pos_ring01 + core_trans.Vector3(x=-3.5)
            pos_ring03 = pos_ring02 + core_trans.Vector3(x=-3.6)
            pos_ring04 = pos_ring03 + core_trans.Vector3(x=-3.5)
            self.ring01_proxy.set_initial_position(xyz=pos_ring01)
            self.ring02_proxy.set_initial_position(xyz=pos_ring02)
            self.ring03_proxy.set_initial_position(xyz=pos_ring03)
            self.ring04_proxy.set_initial_position(xyz=pos_ring04)
        if self.pinky:
            pos_pinky01 = core_trans.Vector3(x=-66.9, y=130.4, z=-3.2)
            pos_pinky02 = pos_pinky01 + core_trans.Vector3(x=-3.3)
            pos_pinky03 = pos_pinky02 + core_trans.Vector3(x=-3.2)
            pos_pinky04 = pos_pinky03 + core_trans.Vector3(x=-3.5)
            self.pinky01_proxy.set_initial_position(xyz=pos_pinky01)
            self.pinky02_proxy.set_initial_position(xyz=pos_pinky02)
            self.pinky03_proxy.set_initial_position(xyz=pos_pinky03)
            self.pinky04_proxy.set_initial_position(xyz=pos_pinky04)
        if self.extra:
            pos_extra01 = core_trans.Vector3(x=-66.9, y=130.4, z=-5.3)
            pos_extra02 = pos_extra01 + core_trans.Vector3(x=-3)
            pos_extra03 = pos_extra02 + core_trans.Vector3(x=-3)
            pos_extra04 = pos_extra03 + core_trans.Vector3(x=-3.3)
            self.extra01_proxy.set_initial_position(xyz=pos_extra01)
            self.extra02_proxy.set_initial_position(xyz=pos_extra02)
            self.extra03_proxy.set_initial_position(xyz=pos_extra03)
            self.extra04_proxy.set_initial_position(xyz=pos_extra04)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)
    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.core.session import remove_modules_startswith

    remove_modules_startswith("gt.tools.auto_rigger.module")
    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject
    from gt.tools.auto_rigger.modules.module_spine import ModuleSpine
    from gt.tools.auto_rigger.modules.module_biped_arm import ModuleBipedArmLeft
    from gt.tools.auto_rigger.modules.module_biped_arm import ModuleBipedArmRight
    import gt.tools.auto_rigger.modules.module_root as tools_rig_mod_root

    a_root = tools_rig_mod_root.ModuleRoot()
    a_spine = ModuleSpine()
    a_arm_lf = ModuleBipedArmLeft()
    a_arm_rt = ModuleBipedArmRight()
    a_lt_fingers_mod = ModuleBipedFingersLeft()
    a_rt_fingers_mod = ModuleBipedFingersRight()
    # a_fingers_mod = ModuleBipedFingers()

    a_project = RigProject()

    root_uuid = a_root.root_proxy.get_uuid()
    spine_chest_uuid = a_spine.chest_proxy.get_uuid()
    lf_hand_uuid = a_arm_lf.hand_proxy.get_uuid()
    rt_hand_uuid = a_arm_rt.hand_proxy.get_uuid()
    a_spine.set_parent_uuid(root_uuid)
    a_arm_lf.set_parent_uuid(spine_chest_uuid)
    a_arm_rt.set_parent_uuid(spine_chest_uuid)
    a_lt_fingers_mod.set_parent_uuid(lf_hand_uuid)
    a_rt_fingers_mod.set_parent_uuid(rt_hand_uuid)

    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_spine)
    a_project.add_to_modules(a_arm_lf)
    # a_project.add_to_modules(a_arm_rt)
    # a_project.add_to_modules(a_lt_fingers_mod)
    # a_project.add_to_modules(a_rt_fingers_mod)
    # a_project.add_to_modules(a_fingers_mod)
    # a_project.set_preference_value_using_key(key="apply_control_rig_pose", value=False)
    a_project.build_proxy()
    # cmds.setAttr("L_lowerArm.tz", -8)
    # cmds.setAttr("L_hand.ty", -30)
    # cmds.setAttr("L_hand.rz", -45)
    # cmds.setAttr("R_lowerArm.tz", -8)
    # cmds.setAttr("R_hand.ty", -30)
    # cmds.setAttr("R_hand.rz", 45)
    # a_project.build_skeleton()
    a_project.build_rig()

    # cmds.setAttr(f"lf_thumb02.rx", 30)
    # cmds.setAttr(f"lf_ring02.rz", -45)
    # # cmds.setAttr(f"rt_thumb02.rx", 30)

    # a_project.read_data_from_scene()
    # dictionary = a_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = RigProject()
    # a_project2.read_data_from_dict(dictionary)
    # print(a_project2.get_project_as_dict().get("modules"))
    # a_project2.build_proxy()
    # # a_project2.build_rig()

    # Frame elements
    cmds.viewFit(all=True)
    # cmds.viewFit(["lf_thumbEnd", "lf_pinkyEnd"])  # Left
    # cmds.viewFit(["rt_thumbEnd", "rt_pinkyEnd"])  # Right
