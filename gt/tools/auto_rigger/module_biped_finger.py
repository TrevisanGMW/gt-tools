"""
Auto Rigger Digit Modules (Fingers, Toes)
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import find_joint_from_uuid, get_meta_purpose_from_dict, find_direction_curve
from gt.tools.auto_rigger.rig_utils import create_ctrl_curve, get_automation_group
from gt.utils.transform_utils import Vector3, match_transform, scale_shapes, rotate_shapes, get_directional_position
from gt.utils.attr_utils import add_separator_attr, hide_lock_default_attrs, set_attr, rescale
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.utils.data.controls.cluster_driven import create_scalable_two_sides_arrow
from gt.tools.auto_rigger.rig_constants import RiggerConstants, RiggerDriverTypes
from gt.utils.math_utils import get_transforms_center_position, dist_path_sum
from gt.utils.color_utils import ColorConstants, set_color_viewport
from gt.utils.hierarchy_utils import add_offset_transform
from gt.utils.rigging_utils import expose_rotation_order
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
    __version__ = '0.0.3-alpha'
    icon = resource_library.Icon.rigger_module_biped_fingers
    allow_parenting = True

    # Reference Attributes and Metadata Keys
    META_THUMB_NAME = "thumbName"  # Metadata key for the thumb digit name
    META_INDEX_NAME = "indexName"  # Metadata key for the index digit name
    META_MIDDLE_NAME = "middleName"  # Metadata key for the middle digit name
    META_RING_NAME = "ringName"  # Metadata key for the ring digit name
    META_PINKY_NAME = "pinkyName"  # Metadata key for the pinky digit name
    META_EXTRA_NAME = "extraName"  # Metadata key for the extra digit name
    # Default Label Values
    DEFAULT_SETUP_NAME = "fingers"
    DEFAULT_THUMB = "thumb"
    DEFAULT_INDEX = "index"
    DEFAULT_MIDDLE = "middle"
    DEFAULT_RING = "ring"
    DEFAULT_PINKY = "pinky"
    DEFAULT_EXTRA = "extra"

    def __init__(self, name="Fingers", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 1, 0), up_dir=(0, 1, 0))
        self.set_orientation(orientation_data=_orientation)

        # Extra Module Data
        self.set_meta_setup_name(name=self.DEFAULT_SETUP_NAME)
        self.add_to_metadata(key=self.META_THUMB_NAME, value=self.DEFAULT_THUMB)
        self.add_to_metadata(key=self.META_INDEX_NAME, value=self.DEFAULT_INDEX)
        self.add_to_metadata(key=self.META_MIDDLE_NAME, value=self.DEFAULT_MIDDLE)
        self.add_to_metadata(key=self.META_RING_NAME, value=self.DEFAULT_RING)
        self.add_to_metadata(key=self.META_PINKY_NAME, value=self.DEFAULT_PINKY)
        self.add_to_metadata(key=self.META_EXTRA_NAME, value=self.DEFAULT_EXTRA)

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
        self.thumb01 = Proxy(name=f"{self.DEFAULT_THUMB}01")
        self.thumb01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb01.set_initial_position(xyz=pos_thumb01)
        self.thumb01.set_locator_scale(scale=loc_scale)
        self.thumb01.set_meta_purpose(value=self.thumb01.get_name())

        self.thumb02 = Proxy(name=f"{self.DEFAULT_THUMB}02")
        self.thumb02.set_parent_uuid(self.thumb01.get_uuid())
        self.thumb02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb02.set_initial_position(xyz=pos_thumb02)
        self.thumb02.set_locator_scale(scale=loc_scale)
        self.thumb02.set_meta_purpose(value=self.thumb02.get_name())

        self.thumb03 = Proxy(name=f"{self.DEFAULT_THUMB}03")
        self.thumb03.set_parent_uuid(self.thumb02.get_uuid())
        self.thumb03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb03.set_initial_position(xyz=pos_thumb03)
        self.thumb03.set_locator_scale(scale=loc_scale)
        self.thumb03.set_meta_purpose(value=self.thumb03.get_name())

        self.thumb04 = Proxy(name=f"{self.DEFAULT_THUMB}End")
        self.thumb04.set_parent_uuid(self.thumb03.get_uuid())
        self.thumb04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.thumb04.set_initial_position(xyz=pos_thumb04)
        self.thumb04.set_locator_scale(scale=loc_scale_end)
        self.thumb04.set_meta_purpose(value=self.thumb04.get_name())
        self.thumb04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.thumb_digits = [self.thumb01, self.thumb02, self.thumb03, self.thumb04]

        # Index -------------------------------------------------------------------------------------
        self.index_digits = []
        self.index01 = Proxy(name=f"{self.DEFAULT_INDEX}01")
        self.index01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index01.set_initial_position(xyz=pos_index01)
        self.index01.set_locator_scale(scale=loc_scale)
        self.index01.set_meta_purpose(value=self.index01.get_name())

        self.index02 = Proxy(name=f"{self.DEFAULT_INDEX}02")
        self.index02.set_parent_uuid(self.index01.get_uuid())
        self.index02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index02.set_initial_position(xyz=pos_index02)
        self.index02.set_locator_scale(scale=loc_scale)
        self.index02.set_meta_purpose(value=self.index02.get_name())

        self.index03 = Proxy(name=f"{self.DEFAULT_INDEX}03")
        self.index03.set_parent_uuid(self.index02.get_uuid())
        self.index03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index03.set_initial_position(xyz=pos_index03)
        self.index03.set_locator_scale(scale=loc_scale)
        self.index03.set_meta_purpose(value=self.index03.get_name())

        self.index04 = Proxy(name=f"{self.DEFAULT_INDEX}End")
        self.index04.set_parent_uuid(self.index03.get_uuid())
        self.index04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.index04.set_initial_position(xyz=pos_index04)
        self.index04.set_locator_scale(scale=loc_scale_end)
        self.index04.set_meta_purpose(value=self.index04.get_name())
        self.index04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.index_digits = [self.index01, self.index02, self.index03, self.index04]

        # Middle -------------------------------------------------------------------------------------
        self.middle_digits = []
        self.middle01 = Proxy(name=f"{self.DEFAULT_MIDDLE}01")
        self.middle01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle01.set_initial_position(xyz=pos_middle01)
        self.middle01.set_locator_scale(scale=loc_scale)
        self.middle01.set_meta_purpose(value=self.middle01.get_name())

        self.middle02 = Proxy(name=f"{self.DEFAULT_MIDDLE}02")
        self.middle02.set_parent_uuid(self.middle01.get_uuid())
        self.middle02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle02.set_initial_position(xyz=pos_middle02)
        self.middle02.set_locator_scale(scale=loc_scale)
        self.middle02.set_meta_purpose(value=self.middle02.get_name())

        self.middle03 = Proxy(name=f"{self.DEFAULT_MIDDLE}03")
        self.middle03.set_parent_uuid(self.middle02.get_uuid())
        self.middle03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle03.set_initial_position(xyz=pos_middle03)
        self.middle03.set_locator_scale(scale=loc_scale)
        self.middle03.set_meta_purpose(value=self.middle03.get_name())

        self.middle04 = Proxy(name=f"{self.DEFAULT_MIDDLE}End")
        self.middle04.set_parent_uuid(self.middle03.get_uuid())
        self.middle04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.middle04.set_initial_position(xyz=pos_middle04)
        self.middle04.set_locator_scale(scale=loc_scale_end)
        self.middle04.set_meta_purpose(value=self.middle04.get_name())
        self.middle04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.middle_digits = [self.middle01, self.middle02, self.middle03, self.middle04]

        # Ring -------------------------------------------------------------------------------------
        self.ring_digits = []
        self.ring01 = Proxy(name=f"{self.DEFAULT_RING}01")
        self.ring01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring01.set_initial_position(xyz=pos_ring01)
        self.ring01.set_locator_scale(scale=loc_scale)
        self.ring01.set_meta_purpose(value=self.ring01.get_name())

        self.ring02 = Proxy(name=f"{self.DEFAULT_RING}02")
        self.ring02.set_parent_uuid(self.ring01.get_uuid())
        self.ring02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring02.set_initial_position(xyz=pos_ring02)
        self.ring02.set_locator_scale(scale=loc_scale)
        self.ring02.set_meta_purpose(value=self.ring02.get_name())

        self.ring03 = Proxy(name=f"{self.DEFAULT_RING}03")
        self.ring03.set_parent_uuid(self.ring02.get_uuid())
        self.ring03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring03.set_initial_position(xyz=pos_ring03)
        self.ring03.set_locator_scale(scale=loc_scale)
        self.ring03.set_meta_purpose(value=self.ring03.get_name())

        self.ring04 = Proxy(name=f"{self.DEFAULT_RING}End")
        self.ring04.set_parent_uuid(self.ring03.get_uuid())
        self.ring04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.ring04.set_initial_position(xyz=pos_ring04)
        self.ring04.set_locator_scale(scale=loc_scale_end)
        self.ring04.set_meta_purpose(value=self.ring04.get_name())
        self.ring04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.ring_digits = [self.ring01, self.ring02, self.ring03, self.ring04]

        # Pinky -------------------------------------------------------------------------------------
        self.pinky_digits = []
        self.pinky01 = Proxy(name=f"{self.DEFAULT_PINKY}01")
        self.pinky01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky01.set_initial_position(xyz=pos_pinky01)
        self.pinky01.set_locator_scale(scale=loc_scale)
        self.pinky01.set_meta_purpose(value=self.pinky01.get_name())

        self.pinky02 = Proxy(name=f"{self.DEFAULT_PINKY}02")
        self.pinky02.set_parent_uuid(self.pinky01.get_uuid())
        self.pinky02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky02.set_initial_position(xyz=pos_pinky02)
        self.pinky02.set_locator_scale(scale=loc_scale)
        self.pinky02.set_meta_purpose(value=self.pinky02.get_name())

        self.pinky03 = Proxy(name=f"{self.DEFAULT_PINKY}03")
        self.pinky03.set_parent_uuid(self.pinky02.get_uuid())
        self.pinky03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky03.set_initial_position(xyz=pos_pinky03)
        self.pinky03.set_locator_scale(scale=loc_scale)
        self.pinky03.set_meta_purpose(value=self.pinky03.get_name())

        self.pinky04 = Proxy(name=f"{self.DEFAULT_PINKY}End")
        self.pinky04.set_parent_uuid(self.pinky03.get_uuid())
        self.pinky04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.pinky04.set_initial_position(xyz=pos_pinky04)
        self.pinky04.set_locator_scale(scale=loc_scale_end)
        self.pinky04.set_meta_purpose(value=self.pinky04.get_name())
        self.pinky04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.pinky_digits = [self.pinky01, self.pinky02, self.pinky03, self.pinky04]

        # Extra -------------------------------------------------------------------------------------
        self.extra_digits = []
        self.extra01 = Proxy(name=f"{self.DEFAULT_EXTRA}01")
        self.extra01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra01.set_initial_position(xyz=pos_extra01)
        self.extra01.set_locator_scale(scale=loc_scale)
        self.extra01.set_meta_purpose(value=self.extra01.get_name())

        self.extra02 = Proxy(name=f"{self.DEFAULT_EXTRA}02")
        self.extra02.set_parent_uuid(self.extra01.get_uuid())
        self.extra02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra02.set_initial_position(xyz=pos_extra02)
        self.extra02.set_locator_scale(scale=loc_scale)
        self.extra02.set_meta_purpose(value=self.extra02.get_name())

        self.extra03 = Proxy(name=f"{self.DEFAULT_EXTRA}03")
        self.extra03.set_parent_uuid(self.extra02.get_uuid())
        self.extra03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        self.extra03.set_initial_position(xyz=pos_extra03)
        self.extra03.set_locator_scale(scale=loc_scale)
        self.extra03.set_meta_purpose(value=self.extra03.get_name())

        self.extra04 = Proxy(name=f"{self.DEFAULT_EXTRA}End")
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
                if meta_type and self.DEFAULT_THUMB in meta_type:
                    _thumb = True
                elif meta_type and self.DEFAULT_INDEX in meta_type:
                    _index = True
                elif meta_type and self.DEFAULT_MIDDLE in meta_type:
                    _middle = True
                elif meta_type and self.DEFAULT_RING in meta_type:
                    _ring = True
                elif meta_type and self.DEFAULT_PINKY in meta_type:
                    _pinky = True
                elif meta_type and self.DEFAULT_EXTRA in meta_type:
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
            if self.DEFAULT_THUMB in meta_type:
                _thumb_joints.append(finger_jnt)
            elif self.DEFAULT_INDEX in meta_type:
                _index_joints.append(finger_jnt)
            elif self.DEFAULT_MIDDLE in meta_type:
                _middle_joints.append(finger_jnt)
            elif self.DEFAULT_RING in meta_type:
                _ring_joints.append(finger_jnt)
            elif self.DEFAULT_PINKY in meta_type:
                _pinky_joints.append(finger_jnt)
            elif self.DEFAULT_EXTRA in meta_type:
                _extra_joints.append(finger_jnt)
            # End Joints
            if meta_type and str(meta_type).endswith("End"):
                _end_joints.append(finger_jnt)
        # Helpful Lists
        _unfiltered_finger_lists = [_thumb_joints, _index_joints, _middle_joints,
                                    _ring_joints, _pinky_joints, _extra_joints]
        _finger_lists = [sublist for sublist in _unfiltered_finger_lists if sublist]  # Only non-empty
        _joints_no_end = list(set(_proxy_joint_map.keys()) - set(_end_joints))  # Remove ends
        _joints_base_only = [sublist[0] for sublist in _finger_lists if sublist]  # Only first element of each list
        _end_joints_no_thumb = list(set(_end_joints) - set(_thumb_joints))
        # Get Misc Elements
        direction_crv = find_direction_curve()
        module_parent_jnt = find_joint_from_uuid(self.get_parent_uuid())
        setup_name = self.get_meta_setup_name()
        fingers_automation_grp = get_automation_group(f'{setup_name}Automation_{NamingConstants.Suffix.GRP}')

        # Set Joint Colors ------------------------------------------------------------------------------------
        for jnt in _joints_no_end:
            set_color_viewport(obj_list=jnt, rgb_color=ColorConstants.RigJoint.OFFSET)
        for jnt in _end_joints:
            set_color_viewport(obj_list=jnt, rgb_color=ColorConstants.RigJoint.END)

        # Control Parent (Main System Driver) ------------------------------------------------------------------
        wrist_grp = self._assemble_new_node_name(name=f"fingers_{NamingConstants.Suffix.DRIVEN}",
                                                    project_prefix=project_prefix)
        wrist_grp = cmds.group(name=wrist_grp, empty=True, world=True)
        wrist_grp = Node(wrist_grp)
        if module_parent_jnt:
            match_transform(source=module_parent_jnt, target_list=wrist_grp)
        else: # No parent, average the position of the fingers group
            base_center_pos = get_transforms_center_position(transform_list=_joints_base_only)
            cmds.xform(wrist_grp, translation=base_center_pos, worldSpace=True)
        hierarchy_utils.parent(source_objects=wrist_grp, target_parent=direction_crv)

        # Create Controls -------------------------------------------------------------------------------------
        for finger_list in _finger_lists:
            if not finger_list:
                continue # Ignore skipped fingers
            # Unpack elements
            digit_base = finger_list[0]
            digit_middle = finger_list[1]
            digit_tip = finger_list[2]
            digit_tip_end = finger_list[3]
            # Determine finger scale
            finger_scale = dist_path_sum([digit_base, digit_middle, digit_tip, digit_tip_end])
            # Create FK Controls
            last_ctrl = None
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
                # Create FK Hierarchy
                if last_ctrl:
                    hierarchy_utils.parent(source_objects=offset, target_parent=last_ctrl)
                last_ctrl = ctrl

        # Fingers System Ctrl ---------------------------------------------------------------------------------
        # Find Position and Scale
        end_center_pos = get_transforms_center_position(transform_list=_end_joints_no_thumb)
        if module_parent_jnt:  # Has Parent
            distance_from_wrist = dist_path_sum(input_list=[module_parent_jnt, end_center_pos])
        else:
            base_center_pos = get_transforms_center_position(transform_list=_joints_base_only)
            distance_from_wrist = dist_path_sum(input_list=[base_center_pos, end_center_pos])
        wrist_directional_pos = get_directional_position(object_name=wrist_grp, tolerance=0)  # 0 = No Center
        is_right_side = wrist_directional_pos == -1  # Right Side?
        fingers_ctrl_scale = distance_from_wrist*.07
        # Finger Control (Main)
        fingers_ctrl = self._assemble_ctrl_name(name=setup_name)
        fingers_ctrl = create_ctrl_curve(name=fingers_ctrl, curve_file_name="_sphere_half_double_arrows")
        # self.add_driver_uuid_attr(target=fingers_ctrl,
        #                           driver_type=RiggerDriverTypes.ROLL,
        #                           proxy_purpose=self.ankle)  # TODO Add to every finger as automation? @@@
        fingers_offset = add_offset_transform(target_list=fingers_ctrl)[0]
        fingers_offset = Node(fingers_offset)
        # Shape Scale Inverse Offset
        shape_scale_offset_name = self._assemble_ctrl_name(name=setup_name, overwrite_suffix=f'shapeScaleOffset')
        shape_scale_offset = add_offset_transform(target_list=fingers_ctrl)[0]
        shape_scale_offset = Node(shape_scale_offset)
        shape_scale_offset.rename(shape_scale_offset_name)
        # Abduction Feedback Shape
        abduction_crv_data = self._assemble_ctrl_name(name=setup_name,
                                                      overwrite_suffix=f'abduction_{NamingConstants.Suffix.CRV}')
        abduction_crv_data = create_scalable_two_sides_arrow(name=abduction_crv_data)  # Returns ControlData
        abduction_crv = abduction_crv_data.get_name()
        abduction_driver = abduction_crv_data.get_drivers()[0]
        abduction_setup = abduction_crv_data.get_setup()

        # Set Position and Attributes
        rotate_shapes(obj_transform=fingers_ctrl, offset=(0, 90, 0))
        set_attr(obj_list=abduction_crv, attr_list=["overrideEnabled", "overrideDisplayType"], value=1)
        hierarchy_utils.parent(source_objects=abduction_crv, target_parent=fingers_ctrl)
        hierarchy_utils.parent(source_objects=abduction_setup, target_parent=fingers_automation_grp)
        match_transform(source=wrist_grp, target_list=fingers_offset)
        hierarchy_utils.parent(source_objects=fingers_offset, target_parent=wrist_grp)

        # Determine Side Orientation
        cmds.rotate(90, fingers_offset, rotateX=True, relative=True, objectSpace=True)
        if is_right_side:
            cmds.rotate(180, fingers_offset, rotateY=True, relative=True, objectSpace=True)
            cmds.rotate(180, fingers_offset, rotateX=True, relative=True, objectSpace=True)
        # Position
        fingers_move_offset = (distance_from_wrist*1.2)
        cmds.move(fingers_move_offset, fingers_offset, moveX=True, relative=True, objectSpace=True)
        rescale(obj=fingers_offset, scale=fingers_ctrl_scale, freeze=False)

        # Fingers Visibility (Attributes)
        add_separator_attr(target_object=fingers_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
        cmds.addAttr(fingers_ctrl, ln='showCurlControls', at='bool', k=True)
        cmds.addAttr(fingers_ctrl, ln='showFkFingerCtrls', at='bool', k=True, niceName='Show FK Finger Ctrls')

        # Fingers Limits (Attributes)
        cmds.addAttr(fingers_ctrl, ln='maximumRotationZ', at='double', k=True)
        cmds.setAttr(f'{fingers_ctrl}.maximumRotationZ', 10)
        cmds.addAttr(fingers_ctrl, ln='minimumRotationZ', at='double', k=True)
        cmds.setAttr(f'{fingers_ctrl}.minimumRotationZ', -130)

        cmds.addAttr(fingers_ctrl, ln='rotateShape', at='bool', k=True)
        cmds.setAttr(f'{fingers_ctrl}.rotateShape', 1)

        cmds.setAttr(f'{fingers_ctrl}.maxRotZLimitEnable', 1)
        cmds.setAttr(f'{fingers_ctrl}.minRotZLimitEnable', 1)

        # Curl Controls ------------------------------------------------------------------------------------
        thumb_curl_ctrl = None
        index_curl_ctrl = None
        middle_curl_ctrl = None
        ring_curl_ctrl = None
        pinky_curl_ctrl = None
        extra_curl_ctrl = None
        curl_ctrls = []
        dist_offset_curl = 2*wrist_directional_pos
        if _thumb_joints:
            thumb_name = self.get_metadata_value(key=self.META_THUMB_NAME)
            thumb_curl_ctrl = self._assemble_ctrl_name(name=thumb_name,
                                                      overwrite_suffix=NamingConstants.Suffix.CURL)
            thumb_curl_ctrl = create_ctrl_curve(name=thumb_curl_ctrl, curve_file_name="_sphere_half_arrow")
            self.add_driver_uuid_attr(target=thumb_curl_ctrl,
                                      driver_type=RiggerDriverTypes.CURL,
                                      proxy_purpose=self.thumb01)  # TODO @@@ Apply to other finger controls too?
            thumb_curl_offset = add_offset_transform(target_list=thumb_curl_ctrl)[0]
            thumb_curl_offset = Node(thumb_curl_offset)
            rotate_shapes(obj_transform=thumb_curl_ctrl, offset=(0, 90, 0))
            scale_shapes(obj_transform=thumb_curl_ctrl, offset=fingers_ctrl_scale*.5)
            match_transform(source=fingers_ctrl, target_list=thumb_curl_offset)
            hierarchy_utils.parent(source_objects=thumb_curl_offset, target_parent=fingers_offset)
            cmds.rotate(-90, thumb_curl_offset, rotateY=True, relative=True, objectSpace=True)
            cmds.move(-distance_from_wrist*.15, thumb_curl_offset, z=True, relative=True, objectSpace=True)
            cmds.move(dist_offset_curl*2, thumb_curl_offset, x=True, relative=True, objectSpace=True)
            if is_right_side:
                cmds.rotate(180, thumb_curl_offset, rotateY=True, relative=True, objectSpace=True)
            curl_ctrls.append(thumb_curl_ctrl)
        if _index_joints:
            index_name = self.get_metadata_value(key=self.META_INDEX_NAME)
            index_curl_ctrl = self._assemble_ctrl_name(name=index_name,
                                                       overwrite_suffix=NamingConstants.Suffix.CURL)
            index_curl_ctrl = create_ctrl_curve(name=index_curl_ctrl, curve_file_name="_sphere_half_arrow")
            index_curl_offset = add_offset_transform(target_list=index_curl_ctrl)[0]
            index_curl_offset = Node(index_curl_offset)
            scale_shapes(obj_transform=index_curl_ctrl, offset=fingers_ctrl_scale * .5)
            match_transform(source=fingers_ctrl, target_list=index_curl_offset)
            rotate_shapes(obj_transform=index_curl_ctrl, offset=(0, 90, 0))
            hierarchy_utils.parent(source_objects=index_curl_offset, target_parent=fingers_offset)
            cmds.move(distance_from_wrist * .15, index_curl_offset, x=True, relative=True, objectSpace=True)
            cmds.move(dist_offset_curl, index_curl_offset, z=True, relative=True, objectSpace=True)
            curl_ctrls.append(index_curl_ctrl)
        if _middle_joints:
            middle_name = self.get_metadata_value(key=self.META_MIDDLE_NAME)
            middle_curl_ctrl = self._assemble_ctrl_name(name=middle_name,
                                                        overwrite_suffix=NamingConstants.Suffix.CURL)
            middle_curl_ctrl = create_ctrl_curve(name=middle_curl_ctrl, curve_file_name="_sphere_half_arrow")
            middle_curl_offset = add_offset_transform(target_list=middle_curl_ctrl)[0]
            middle_curl_offset = Node(middle_curl_offset)
            scale_shapes(obj_transform=middle_curl_ctrl, offset=fingers_ctrl_scale * .5)
            match_transform(source=fingers_ctrl, target_list=middle_curl_offset)
            rotate_shapes(obj_transform=middle_curl_ctrl, offset=(0, 90, 0))
            hierarchy_utils.parent(source_objects=middle_curl_offset, target_parent=fingers_offset)
            cmds.move(distance_from_wrist * .15, middle_curl_offset, x=True, relative=True, objectSpace=True)
            curl_ctrls.append(middle_curl_ctrl)
        if _ring_joints:
            ring_name = self.get_metadata_value(key=self.META_RING_NAME)
            ring_curl_ctrl = self._assemble_ctrl_name(name=ring_name,
                                                      overwrite_suffix=NamingConstants.Suffix.CURL)
            ring_curl_ctrl = create_ctrl_curve(name=ring_curl_ctrl, curve_file_name="_sphere_half_arrow")
            ring_curl_offset = add_offset_transform(target_list=ring_curl_ctrl)[0]
            ring_curl_offset = Node(ring_curl_offset)
            scale_shapes(obj_transform=ring_curl_ctrl, offset=fingers_ctrl_scale * .5)
            match_transform(source=fingers_ctrl, target_list=ring_curl_offset)
            rotate_shapes(obj_transform=ring_curl_ctrl, offset=(0, 90, 0))
            hierarchy_utils.parent(source_objects=ring_curl_offset, target_parent=fingers_offset)
            cmds.move(distance_from_wrist * .15, ring_curl_offset, x=True, relative=True, objectSpace=True)
            cmds.move(dist_offset_curl*-1, ring_curl_offset, z=True, relative=True, objectSpace=True)
            curl_ctrls.append(ring_curl_ctrl)
        if _pinky_joints:
            pinky_name = self.get_metadata_value(key=self.META_PINKY_NAME)
            pinky_curl_ctrl = self._assemble_ctrl_name(name=pinky_name,
                                                       overwrite_suffix=NamingConstants.Suffix.CURL)
            pinky_curl_ctrl = create_ctrl_curve(name=pinky_curl_ctrl, curve_file_name="_sphere_half_arrow")
            pinky_curl_offset = add_offset_transform(target_list=pinky_curl_ctrl)[0]
            pinky_curl_offset = Node(pinky_curl_offset)
            scale_shapes(obj_transform=pinky_curl_ctrl, offset=fingers_ctrl_scale * .5)
            match_transform(source=fingers_ctrl, target_list=pinky_curl_offset)
            rotate_shapes(obj_transform=pinky_curl_ctrl, offset=(0, 90, 0))
            hierarchy_utils.parent(source_objects=pinky_curl_offset, target_parent=fingers_offset)
            cmds.move(distance_from_wrist * .15, pinky_curl_offset, x=True, relative=True, objectSpace=True)
            cmds.move(dist_offset_curl*-2, pinky_curl_offset, z=True, relative=True, objectSpace=True)
            curl_ctrls.append(pinky_curl_ctrl)
        if _extra_joints:
            extra_name = self.get_metadata_value(key=self.META_EXTRA_NAME)
            extra_curl_ctrl = self._assemble_ctrl_name(name=extra_name,
                                                       overwrite_suffix=NamingConstants.Suffix.CURL)
            extra_curl_ctrl = create_ctrl_curve(name=extra_curl_ctrl, curve_file_name="_sphere_half_arrow")
            extra_curl_offset = add_offset_transform(target_list=extra_curl_ctrl)[0]
            extra_curl_offset = Node(extra_curl_offset)
            scale_shapes(obj_transform=extra_curl_ctrl, offset=fingers_ctrl_scale * .5)
            match_transform(source=fingers_ctrl, target_list=extra_curl_offset)
            rotate_shapes(obj_transform=extra_curl_ctrl, offset=(0, 90, 0))
            hierarchy_utils.parent(source_objects=extra_curl_offset, target_parent=fingers_offset)
            cmds.move(distance_from_wrist * .15, extra_curl_offset, x=True, relative=True, objectSpace=True)
            cmds.move(dist_offset_curl*-3, extra_curl_offset, z=True, relative=True, objectSpace=True)
            curl_ctrls.append(extra_curl_ctrl)

        # Lock and Hide Unnecessary Attributes
        for ctrl in curl_ctrls:
            hide_lock_default_attrs(obj_list=ctrl, translate=True, scale=True, visibility=True)
            cmds.setAttr(f'{ctrl}.rx', lock=True, keyable=False)
            cmds.setAttr(f'{ctrl}.ry', lock=True, keyable=False)

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [wrist_grp]

    # ------------------------------------------- Extra Module Setters -------------------------------------------
    def set_thumb_name(self, name):
        """
        Sets the thumb digit name by editing the metadata value associated with it.
        Args:
            name (str): New name thumb digit name. If empty the default "thumb" is used instead.
        """
        if name:
            self.add_to_metadata(self.META_THUMB_NAME, value=name)
        else:
            self.add_to_metadata(self.META_THUMB_NAME, value=self.DEFAULT_THUMB)

    def set_index_name(self, name):
        """
        Sets the index digit name by editing the metadata value associated with it.
        Args:
            name (str): New name index digit name. If empty the default "index" is used instead.
        """
        if name:
            self.add_to_metadata(self.META_INDEX_NAME, value=name)
        else:
            self.add_to_metadata(self.META_INDEX_NAME, value=self.DEFAULT_INDEX)

    def set_middle_name(self, name):
        """
        Sets the middle digit name by editing the metadata value associated with it.
        Args:
            name (str): New name middle digit name. If empty the default "middle" is used instead.
        """
        if name:
            self.add_to_metadata(self.META_MIDDLE_NAME, value=name)
        else:
            self.add_to_metadata(self.META_MIDDLE_NAME, value=self.DEFAULT_MIDDLE)

    def set_ring_name(self, name):
        """
        Sets the ring digit name by editing the metadata value associated with it.
        Args:
            name (str): New name ring digit name. If empty the default "ring" is used instead.
        """
        if name:
            self.add_to_metadata(self.META_RING_NAME, value=name)
        else:
            self.add_to_metadata(self.META_RING_NAME, value=self.DEFAULT_RING)

    def set_pinky_name(self, name):
        """
        Sets the pinky digit name by editing the metadata value associated with it.
        Args:
            name (str): New name pinky digit name. If empty the default "pinky" is used instead.
        """
        if name:
            self.add_to_metadata(self.META_PINKY_NAME, value=name)
        else:
            self.add_to_metadata(self.META_PINKY_NAME, value=self.DEFAULT_PINKY)

    def set_extra_name(self, name):
        """
        Sets the extra digit name by editing the metadata value associated with it.
        Args:
            name (str): New name extra digit name. If empty the default "extra" is used instead.
        """
        if name:
            self.add_to_metadata(self.META_EXTRA_NAME, value=name)
        else:
            self.add_to_metadata(self.META_EXTRA_NAME, value=self.DEFAULT_EXTRA)


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
    from gt.tools.auto_rigger.module_spine import ModuleSpine
    from gt.tools.auto_rigger.module_biped_arm import ModuleBipedArmLeft, ModuleBipedArmRight

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
    a_project.add_to_modules(a_rt_fingers_mod)
    a_lt_arm.set_parent_uuid(uuid=a_spine.chest.get_uuid())
    a_rt_arm.set_parent_uuid(uuid=a_spine.chest.get_uuid())
    a_lt_fingers_mod.set_parent_uuid(uuid=a_lt_arm.wrist.get_uuid())
    a_rt_fingers_mod.set_parent_uuid(uuid=a_rt_arm.wrist.get_uuid())

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
