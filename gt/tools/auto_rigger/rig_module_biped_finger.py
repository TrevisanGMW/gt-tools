"""
Auto Rigger Digit Modules (Fingers, Toes)
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import find_joint_from_uuid, get_meta_purpose_from_dict, find_direction_curve
from gt.tools.auto_rigger.rig_utils import create_ctrl_curve, expose_rotation_order
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.tools.biped_rigger_legacy.rigger_utilities import dist_center_to_center
from gt.tools.auto_rigger.rig_constants import RiggerConstants, RiggerDriverTypes
from gt.utils.transform_utils import Vector3, match_transform, scale_shapes
from gt.utils.attr_utils import add_separator_attr, hide_lock_default_attrs
from gt.utils.color_utils import ColorConstants, set_color_viewport
from gt.utils.math_utils import get_transforms_center_position
from gt.utils.hierarchy_utils import add_offset_transform
from gt.utils.naming_utils import NamingConstants
from gt.utils.curve_utils import get_curve
from gt.utils.node_utils import Node
from gt.utils import hierarchy_utils
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
    tag_thumb = "thumb"
    tag_index = "index"
    tag_middle = "middle"
    tag_ring = "ring"
    tag_pinky = "pinky"
    tag_extra = "extra"

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
        self.thumb01 = Proxy(name=f"{self.tag_thumb}01")
        self.thumb01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb01.set_initial_position(xyz=pos_thumb01)
        self.thumb01.set_locator_scale(scale=loc_scale)
        self.thumb01.set_meta_purpose(value=self.thumb01.get_name())

        self.thumb02 = Proxy(name=f"{self.tag_thumb}02")
        self.thumb02.set_parent_uuid(self.thumb01.get_uuid())
        self.thumb02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb02.set_initial_position(xyz=pos_thumb02)
        self.thumb02.set_locator_scale(scale=loc_scale)
        self.thumb02.set_meta_purpose(value=self.thumb02.get_name())

        self.thumb03 = Proxy(name=f"{self.tag_thumb}03")
        self.thumb03.set_parent_uuid(self.thumb02.get_uuid())
        self.thumb03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb03.set_initial_position(xyz=pos_thumb03)
        self.thumb03.set_locator_scale(scale=loc_scale)
        self.thumb03.set_meta_purpose(value=self.thumb03.get_name())

        self.thumb04 = Proxy(name=f"{self.tag_thumb}End")
        self.thumb04.set_parent_uuid(self.thumb03.get_uuid())
        self.thumb04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb04.set_initial_position(xyz=pos_thumb04)
        self.thumb04.set_locator_scale(scale=loc_scale_end)
        self.thumb04.set_meta_purpose(value=self.thumb04.get_name())
        self.thumb04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.thumb_digits = [self.thumb01, self.thumb02, self.thumb03, self.thumb04]

        # Index -------------------------------------------------------------------------------------
        self.index_digits = []
        self.index01 = Proxy(name=f"{self.tag_index}01")
        self.index01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index01.set_initial_position(xyz=pos_index01)
        self.index01.set_locator_scale(scale=loc_scale)
        self.index01.set_meta_purpose(value=self.index01.get_name())

        self.index02 = Proxy(name=f"{self.tag_index}02")
        self.index02.set_parent_uuid(self.index01.get_uuid())
        self.index02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index02.set_initial_position(xyz=pos_index02)
        self.index02.set_locator_scale(scale=loc_scale)
        self.index02.set_meta_purpose(value=self.index02.get_name())

        self.index03 = Proxy(name=f"{self.tag_index}03")
        self.index03.set_parent_uuid(self.index02.get_uuid())
        self.index03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index03.set_initial_position(xyz=pos_index03)
        self.index03.set_locator_scale(scale=loc_scale)
        self.index03.set_meta_purpose(value=self.index03.get_name())

        self.index04 = Proxy(name=f"{self.tag_index}End")
        self.index04.set_parent_uuid(self.index03.get_uuid())
        self.index04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index04.set_initial_position(xyz=pos_index04)
        self.index04.set_locator_scale(scale=loc_scale_end)
        self.index04.set_meta_purpose(value=self.index04.get_name())
        self.index04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.index_digits = [self.index01, self.index02, self.index03, self.index04]

        # Middle -------------------------------------------------------------------------------------
        self.middle_digits = []
        self.middle01 = Proxy(name=f"{self.tag_middle}01")
        self.middle01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle01.set_initial_position(xyz=pos_middle01)
        self.middle01.set_locator_scale(scale=loc_scale)
        self.middle01.set_meta_purpose(value=self.middle01.get_name())

        self.middle02 = Proxy(name=f"{self.tag_middle}02")
        self.middle02.set_parent_uuid(self.middle01.get_uuid())
        self.middle02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle02.set_initial_position(xyz=pos_middle02)
        self.middle02.set_locator_scale(scale=loc_scale)
        self.middle02.set_meta_purpose(value=self.middle02.get_name())

        self.middle03 = Proxy(name=f"{self.tag_middle}03")
        self.middle03.set_parent_uuid(self.middle02.get_uuid())
        self.middle03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle03.set_initial_position(xyz=pos_middle03)
        self.middle03.set_locator_scale(scale=loc_scale)
        self.middle03.set_meta_purpose(value=self.middle03.get_name())

        self.middle04 = Proxy(name=f"{self.tag_middle}End")
        self.middle04.set_parent_uuid(self.middle03.get_uuid())
        self.middle04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle04.set_initial_position(xyz=pos_middle04)
        self.middle04.set_locator_scale(scale=loc_scale_end)
        self.middle04.set_meta_purpose(value=self.middle04.get_name())
        self.middle04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.middle_digits = [self.middle01, self.middle02, self.middle03, self.middle04]

        # Ring -------------------------------------------------------------------------------------
        self.ring_digits = []
        self.ring01 = Proxy(name=f"{self.tag_ring}01")
        self.ring01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring01.set_initial_position(xyz=pos_ring01)
        self.ring01.set_locator_scale(scale=loc_scale)
        self.ring01.set_meta_purpose(value=self.ring01.get_name())

        self.ring02 = Proxy(name=f"{self.tag_ring}02")
        self.ring02.set_parent_uuid(self.ring01.get_uuid())
        self.ring02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring02.set_initial_position(xyz=pos_ring02)
        self.ring02.set_locator_scale(scale=loc_scale)
        self.ring02.set_meta_purpose(value=self.ring02.get_name())

        self.ring03 = Proxy(name=f"{self.tag_ring}03")
        self.ring03.set_parent_uuid(self.ring02.get_uuid())
        self.ring03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring03.set_initial_position(xyz=pos_ring03)
        self.ring03.set_locator_scale(scale=loc_scale)
        self.ring03.set_meta_purpose(value=self.ring03.get_name())

        self.ring04 = Proxy(name=f"{self.tag_ring}End")
        self.ring04.set_parent_uuid(self.ring03.get_uuid())
        self.ring04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring04.set_initial_position(xyz=pos_ring04)
        self.ring04.set_locator_scale(scale=loc_scale_end)
        self.ring04.set_meta_purpose(value=self.ring04.get_name())
        self.ring04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.ring_digits = [self.ring01, self.ring02, self.ring03, self.ring04]

        # Pinky -------------------------------------------------------------------------------------
        self.pinky_digits = []
        self.pinky01 = Proxy(name=f"{self.tag_pinky}01")
        self.pinky01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky01.set_initial_position(xyz=pos_pinky01)
        self.pinky01.set_locator_scale(scale=loc_scale)
        self.pinky01.set_meta_purpose(value=self.pinky01.get_name())

        self.pinky02 = Proxy(name=f"{self.tag_pinky}02")
        self.pinky02.set_parent_uuid(self.pinky01.get_uuid())
        self.pinky02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky02.set_initial_position(xyz=pos_pinky02)
        self.pinky02.set_locator_scale(scale=loc_scale)
        self.pinky02.set_meta_purpose(value=self.pinky02.get_name())

        self.pinky03 = Proxy(name=f"{self.tag_pinky}03")
        self.pinky03.set_parent_uuid(self.pinky02.get_uuid())
        self.pinky03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky03.set_initial_position(xyz=pos_pinky03)
        self.pinky03.set_locator_scale(scale=loc_scale)
        self.pinky03.set_meta_purpose(value=self.pinky03.get_name())

        self.pinky04 = Proxy(name=f"{self.tag_pinky}End")
        self.pinky04.set_parent_uuid(self.pinky03.get_uuid())
        self.pinky04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky04.set_initial_position(xyz=pos_pinky04)
        self.pinky04.set_locator_scale(scale=loc_scale_end)
        self.pinky04.set_meta_purpose(value=self.pinky04.get_name())
        self.pinky04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.pinky_digits = [self.pinky01, self.pinky02, self.pinky03, self.pinky04]

        # Extra -------------------------------------------------------------------------------------
        self.extra_digits = []
        self.extra01 = Proxy(name=f"{self.tag_extra}01")
        self.extra01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra01.set_initial_position(xyz=pos_extra01)
        self.extra01.set_locator_scale(scale=loc_scale)
        self.extra01.set_meta_purpose(value=self.extra01.get_name())

        self.extra02 = Proxy(name=f"{self.tag_extra}02")
        self.extra02.set_parent_uuid(self.extra01.get_uuid())
        self.extra02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra02.set_initial_position(xyz=pos_extra02)
        self.extra02.set_locator_scale(scale=loc_scale)
        self.extra02.set_meta_purpose(value=self.extra02.get_name())

        self.extra03 = Proxy(name=f"{self.tag_extra}03")
        self.extra03.set_parent_uuid(self.extra02.get_uuid())
        self.extra03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra03.set_initial_position(xyz=pos_extra03)
        self.extra03.set_locator_scale(scale=loc_scale)
        self.extra03.set_meta_purpose(value=self.extra03.get_name())

        self.extra04 = Proxy(name=f"{self.tag_extra}End")
        self.extra04.set_parent_uuid(self.extra03.get_uuid())
        self.extra04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra04.set_initial_position(xyz=pos_extra04)
        self.extra04.set_locator_scale(scale=loc_scale_end)
        self.extra04.set_meta_purpose(value=self.extra04.get_name())
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
                meta_type = metadata.get(RiggerConstants.META_PROXY_PURPOSE)
                if meta_type and self.tag_thumb in meta_type:
                    _thumb = True
                elif meta_type and self.tag_index in meta_type:
                    _index = True
                elif meta_type and self.tag_middle in meta_type:
                    _middle = True
                elif meta_type and self.tag_ring in meta_type:
                    _ring = True
                elif meta_type and self.tag_pinky in meta_type:
                    _pinky = True
                elif meta_type and self.tag_extra in meta_type:
                    _extra = True
        self.refresh_proxies_list(thumb=_thumb, index=_index, middle=_middle,
                                  ring=_ring, pinky=_pinky, extra=_extra)
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

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        for digit in self.proxies:
            digit.apply_offset_transform()
        for digit in self.proxies:
            digit.apply_transforms()
        cmds.select(clear=True)

    def build_skeleton_joints(self):
        super().build_skeleton_joints()  # Passthrough

    def build_rig(self, project_prefix=None, **kwargs):
        """
        Runs post rig script.
        """
        # Get Elements -----------------------------------------------------------------------------------------
        _proxy_joint_map = {} # Key = Joint, Value = Proxy
        _thumb_joints = []
        _index_joints = []
        _middle_joints = []
        _ring_joints = []
        _pinky_joints = []
        _extra_joints = []
        _end_joints = []  # Only the last joints of every digit
        # Get Joints
        for proxy in self.proxies:
            finger_jnt = find_joint_from_uuid(proxy.get_uuid())
            meta_type = get_meta_purpose_from_dict(proxy.get_metadata())
            if not finger_jnt:
                continue  # Skipped finger
            if not meta_type:
                continue  # Unexpected Proxy
            _proxy_joint_map[finger_jnt] = proxy  # Add to map
            # Store Joints In Lists/Dict
            if self.tag_thumb in meta_type:
                _thumb_joints.append(finger_jnt)
            elif self.tag_index in meta_type:
                _index_joints.append(finger_jnt)
            elif self.tag_middle in meta_type:
                _middle_joints.append(finger_jnt)
            elif self.tag_ring in meta_type:
                _ring_joints.append(finger_jnt)
            elif self.tag_pinky in meta_type:
                _pinky_joints.append(finger_jnt)
            elif self.tag_extra in meta_type:
                _extra_joints.append(finger_jnt)
            # End Joints
            if meta_type and str(meta_type).endswith("End"):
                _end_joints.append(finger_jnt)
        _all_joints_no_end = list(set(_proxy_joint_map.keys()) - set(_end_joints))

        # Set Joint Colors
        for jnt in _all_joints_no_end:
            set_color_viewport(obj_list=jnt, rgb_color=ColorConstants.RigJoint.OFFSET)
        for jnt in _end_joints:
            set_color_viewport(obj_list=jnt, rgb_color=ColorConstants.RigJoint.END)

        # Get Misc Elements
        direction_crv = find_direction_curve()
        module_parent_jnt = find_joint_from_uuid(self.get_parent_uuid())

        # Control Parent (Main System Driver) ------------------------------------------------------------------
        finger_lists = [_thumb_joints, _index_joints, _middle_joints,
                        _ring_joints, _pinky_joints, _extra_joints]
        wrist_grp = self._assemble_new_node_name(name=f"fingers_{NamingConstants.Suffix.DRIVEN}",
                                                    project_prefix=project_prefix)
        wrist_grp = cmds.group(name=wrist_grp, empty=True, world=True)
        wrist_grp = Node(wrist_grp)
        if module_parent_jnt:
            match_transform(source=module_parent_jnt, target_list=wrist_grp)
        else: # No parent, average the position of the fingers group
            first_joints = [sublist[0] for sublist in finger_lists if sublist]  # Only first element of each list
            fingers_center = get_transforms_center_position(transform_list=first_joints)
            cmds.xform(wrist_grp, translation=fingers_center, worldSpace=True)
        hierarchy_utils.parent(source_objects=wrist_grp, target_parent=direction_crv)

        # Create Controls -------------------------------------------------------------------------------------
        for finger_list in finger_lists:
            if not finger_list:
                continue # Ignore skipped fingers
            # Unpack elements
            digit_base = finger_list[0]
            digit_middle = finger_list[1]
            digit_tip = finger_list[2]
            digit_tip_end = finger_list[3]
            # Determine finger scale
            finger_scale = dist_center_to_center(digit_base, digit_middle)
            finger_scale += dist_center_to_center(digit_middle, digit_tip)
            finger_scale += dist_center_to_center(digit_tip, digit_tip_end)
            # Create FK Controls
            for finger_jnt in finger_list:
                finger_proxy = _proxy_joint_map.get(finger_jnt)
                meta_type = get_meta_purpose_from_dict(finger_proxy.get_metadata())
                if meta_type and str(meta_type).endswith("End"):
                    continue  # Skip end joints
                ctrl = self._assemble_ctrl_name(name=finger_proxy.get_name())
                ctrl = create_ctrl_curve(name=ctrl, curve_file_name="_pin_pos_y")
                self.add_driver_uuid_attr(target=ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=finger_proxy)
                offset = add_offset_transform(target_list=ctrl)[0]
                offset = Node(offset)
                match_transform(source=finger_jnt, target_list=offset)
                scale_shapes(obj_transform=ctrl, offset=finger_scale*.1)
                hierarchy_utils.parent(source_objects=offset, target_parent=wrist_grp)
                add_separator_attr(target_object=ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
                hide_lock_default_attrs(obj_list=ctrl, scale=True, visibility=True)
                expose_rotation_order(target=ctrl)
                
        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [wrist_grp]


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
    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.utils.session_utils import remove_modules_startswith

    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject
    from gt.tools.auto_rigger.rig_module_spine import ModuleSpine
    from gt.tools.auto_rigger.rig_module_biped_arm import ModuleBipedArmLeft, ModuleBipedArmRight

    a_spine = ModuleSpine()
    a_lt_arm = ModuleBipedArmLeft()
    a_rt_arm = ModuleBipedArmRight()
    a_lt_fingers_mod = ModuleBipedFingersLeft()
    a_rt_fingers_mod = ModuleBipedFingersRight()
    # a_fingers_mod = ModuleBipedFingers()

    a_project = RigProject()
    # a_project.add_to_modules(a_fingers_mod)
    a_project.add_to_modules(a_spine)
    a_project.add_to_modules(a_lt_arm)
    a_project.add_to_modules(a_rt_arm)
    a_project.add_to_modules(a_lt_fingers_mod)
    # a_project.add_to_modules(a_rt_fingers_mod)
    a_lt_arm.set_parent_uuid(uuid=a_spine.chest.get_uuid())
    a_rt_arm.set_parent_uuid(uuid=a_spine.chest.get_uuid())
    a_lt_fingers_mod.set_parent_uuid(uuid=a_lt_arm.wrist.get_uuid())
    a_rt_fingers_mod.set_parent_uuid(uuid=a_rt_arm.wrist.get_uuid())
    # a_project.add_to_modules(a_digit_mod_rt)
    a_project.build_proxy()
    a_project.build_rig()

    # cmds.setAttr(f'lf_thumb02.rx', 30)
    # cmds.setAttr(f'lf_ring02.rz', -45)
    # # cmds.setAttr(f'rt_thumb02.rx', 30)

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
    cmds.viewFit(["lf_thumbEnd", "lf_pinkyEnd"])  # Left
    # cmds.viewFit(["rt_thumbEnd", "rt_pinkyEnd"])  # Right
