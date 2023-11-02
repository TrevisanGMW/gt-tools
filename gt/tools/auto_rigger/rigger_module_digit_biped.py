"""
Auto Rigger Digit Modules (Fingers, Toes)
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rigger_utils import RiggerConstants, find_objects_with_attr, find_proxy_node_from_uuid
from gt.utils.attr_utils import hide_lock_default_attrs, set_attr_state, set_attr
from gt.tools.auto_rigger.rigger_framework import Proxy, ModuleGeneric
from gt.tools.auto_rigger.rigger_utils import get_proxy_offset
from gt.utils.transform_utils import match_translate, Vector3
from gt.utils.naming_utils import NamingConstants
from gt.utils.color_utils import ColorConstants
from gt.utils.curve_utils import get_curve
from gt.utils import hierarchy_utils
from gt.utils.node_utils import Node
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleBipedDigits(ModuleGeneric):
    def __init__(self,
                 name="Digits",
                 prefix=None,
                 parent_uuid=None,
                 metadata=None,
                 pos_offset=None,
                 side=None,
                 ):
        super().__init__(name=name, prefix=prefix, parent_uuid=parent_uuid, metadata=metadata)

        self.side = side

        # Thumb -------------------------------------------------------------------------------------
        self.thumb_digits = []
        self.thumb01 = Proxy(name="thumb01")
        self.thumb01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_thumb_base = Vector3(y=130.4) + pos_offset  # Center
        if self.side == "right":
            pos_thumb_base = Vector3(x=-60.8, y=130.4, z=2.9) + pos_offset  # Right
        elif self.side == "left":
            pos_thumb_base = Vector3(x=60.8, y=130.4, z=2.9) + pos_offset  # Left
        self.thumb01.set_initial_position(xyz=pos_thumb_base)
        self.thumb01.set_locator_scale(scale=0.2)
        self.thumb01.set_meta_type(value=self.thumb01.get_name())

        self.thumb02 = Proxy(name="thumb02")
        self.thumb02.set_parent_uuid(self.thumb01.get_uuid())
        self.thumb02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_thumb02 = pos_thumb_base + Vector3(z=4.4)
        self.thumb02.set_initial_position(xyz=pos_thumb02)
        self.thumb02.set_locator_scale(scale=0.2)
        self.thumb02.set_meta_type(value=self.thumb02.get_name())

        self.thumb03 = Proxy(name="thumb03")
        self.thumb03.set_parent_uuid(self.thumb02.get_uuid())
        self.thumb03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_thumb03 = pos_thumb02 + Vector3(z=4.4)
        self.thumb03.set_initial_position(xyz=pos_thumb03)
        self.thumb03.set_locator_scale(scale=0.2)
        self.thumb03.set_meta_type(value=self.thumb03.get_name())

        self.thumb04 = Proxy(name="thumb04")
        self.thumb04.set_parent_uuid(self.thumb03.get_uuid())
        self.thumb04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_thumb04 = pos_thumb03 + Vector3(z=4.6)
        self.thumb04.set_initial_position(xyz=pos_thumb04)
        self.thumb04.set_locator_scale(scale=0.15)
        self.thumb04.set_meta_type(value=self.thumb04.get_name())
        self.thumb04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.thumb_digits = [self.thumb01, self.thumb02, self.thumb03, self.thumb04]

        # Index -------------------------------------------------------------------------------------
        self.index_digits = []
        self.index01 = Proxy(name="index01")
        self.index01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_index_base = Vector3(y=130.4) + pos_offset  # Center
        if self.side == "right":
            pos_index_base = Vector3(x=-66.9, y=130.4, z=3.5) + pos_offset  # Right
        elif self.side == "left":
            pos_index_base = Vector3(x=66.9, y=130.4, z=3.5) + pos_offset  # Left
        self.index01.set_initial_position(xyz=pos_index_base)
        self.index01.set_locator_scale(scale=0.2)
        self.index01.set_meta_type(value=self.index01.get_name())

        self.index02 = Proxy(name="index02")
        self.index02.set_parent_uuid(self.index01.get_uuid())
        self.index02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_index02 = pos_index_base + Vector3(x=3.2)
        self.index02.set_initial_position(xyz=pos_index02)
        self.index02.set_locator_scale(scale=0.2)
        self.index02.set_meta_type(value=self.index02.get_name())

        self.index03 = Proxy(name="index03")
        self.index03.set_parent_uuid(self.index02.get_uuid())
        self.index03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_index03 = pos_index02 + Vector3(x=4.1)
        self.index03.set_initial_position(xyz=pos_index03)
        self.index03.set_locator_scale(scale=0.2)
        self.index03.set_meta_type(value=self.index03.get_name())

        self.index04 = Proxy(name="index04")
        self.index04.set_parent_uuid(self.index03.get_uuid())
        self.index04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_index04 = pos_index03 + Vector3(x=3.3)
        self.index04.set_initial_position(xyz=pos_index04)
        self.index04.set_locator_scale(scale=0.15)
        self.index04.set_meta_type(value=self.index04.get_name())
        self.index04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.index_digits = [self.index01, self.index02, self.index03, self.index04]

        # Middle -------------------------------------------------------------------------------------
        self.middle_digits = []
        self.middle01 = Proxy(name="middle01")
        self.middle01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_middle_base = Vector3(y=130.4) + pos_offset  # Center
        if self.side == "right":
            pos_middle_base = Vector3(x=-66.9, y=130.4, z=1.1) + pos_offset  # Right
        elif self.side == "left":
            pos_middle_base = Vector3(x=66.9, y=130.4, z=1.1) + pos_offset  # Left
        self.middle01.set_initial_position(xyz=pos_middle_base)
        self.middle01.set_locator_scale(scale=0.2)
        self.middle01.set_meta_type(value=self.middle01.get_name())

        self.middle02 = Proxy(name="middle02")
        self.middle02.set_parent_uuid(self.middle01.get_uuid())
        self.middle02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_middle02 = pos_middle_base + Vector3(x=3.8)
        self.middle02.set_initial_position(xyz=pos_middle02)
        self.middle02.set_locator_scale(scale=0.2)
        self.middle02.set_meta_type(value=self.middle02.get_name())

        self.middle03 = Proxy(name="middle03")
        self.middle03.set_parent_uuid(self.middle02.get_uuid())
        self.middle03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_middle03 = pos_middle02 + Vector3(x=3.7)
        self.middle03.set_initial_position(xyz=pos_middle03)
        self.middle03.set_locator_scale(scale=0.2)
        self.middle03.set_meta_type(value=self.middle03.get_name())

        self.middle04 = Proxy(name="middle04")
        self.middle04.set_parent_uuid(self.middle03.get_uuid())
        self.middle04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_middle04 = pos_middle03 + Vector3(x=3.6)
        self.middle04.set_initial_position(xyz=pos_middle04)
        self.middle04.set_locator_scale(scale=0.15)
        self.middle04.set_meta_type(value=self.middle04.get_name())
        self.middle04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.middle_digits = [self.middle01, self.middle02, self.middle03, self.middle04]

        # Ring -------------------------------------------------------------------------------------
        self.ring_digits = []
        self.ring01 = Proxy(name="ring01")
        self.ring01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_ring_base = Vector3(y=130.4) + pos_offset  # Center
        if self.side == "right":
            pos_ring_base = Vector3(x=-66.9, y=130.4, z=-1.1) + pos_offset  # Right
        elif self.side == "left":
            pos_ring_base = Vector3(x=66.9, y=130.4, z=-1.1) + pos_offset  # Left
        self.ring01.set_initial_position(xyz=pos_ring_base)
        self.ring01.set_locator_scale(scale=0.2)
        self.ring01.set_meta_type(value=self.ring01.get_name())

        self.ring02 = Proxy(name="ring02")
        self.ring02.set_parent_uuid(self.ring01.get_uuid())
        self.ring02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_ring02 = pos_ring_base + Vector3(x=3.5)
        self.ring02.set_initial_position(xyz=pos_ring02)
        self.ring02.set_locator_scale(scale=0.2)
        self.ring02.set_meta_type(value=self.ring02.get_name())

        self.ring03 = Proxy(name="ring03")
        self.ring03.set_parent_uuid(self.ring02.get_uuid())
        self.ring03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_ring03 = pos_ring02 + Vector3(x=3.6)
        self.ring03.set_initial_position(xyz=pos_ring03)
        self.ring03.set_locator_scale(scale=0.2)
        self.ring03.set_meta_type(value=self.ring03.get_name())

        self.ring04 = Proxy(name="ring04")
        self.ring04.set_parent_uuid(self.ring03.get_uuid())
        self.ring04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_ring04 = pos_ring03 + Vector3(x=3.5)
        self.ring04.set_initial_position(xyz=pos_ring04)
        self.ring04.set_locator_scale(scale=0.15)
        self.ring04.set_meta_type(value=self.ring04.get_name())
        self.ring04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.ring_digits = [self.ring01, self.ring02, self.ring03, self.ring04]

        # Pinky -------------------------------------------------------------------------------------
        self.pinky_digits = []
        self.pinky01 = Proxy(name="pinky01")
        self.pinky01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_pinky_base = Vector3(y=130.4) + pos_offset  # Center
        if self.side == "right":
            pos_pinky_base = Vector3(x=-66.9, y=130.4, z=-3.2) + pos_offset  # Right
        elif self.side == "left":
            pos_pinky_base = Vector3(x=66.9, y=130.4, z=-3.2) + pos_offset  # Left
        self.pinky01.set_initial_position(xyz=pos_pinky_base)
        self.pinky01.set_locator_scale(scale=0.2)
        self.pinky01.set_meta_type(value=self.pinky01.get_name())

        self.pinky02 = Proxy(name="pinky02")
        self.pinky02.set_parent_uuid(self.pinky01.get_uuid())
        self.pinky02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_pinky02 = pos_pinky_base + Vector3(x=3.3)
        self.pinky02.set_initial_position(xyz=pos_pinky02)
        self.pinky02.set_locator_scale(scale=0.2)
        self.pinky02.set_meta_type(value=self.pinky02.get_name())

        self.pinky03 = Proxy(name="pinky03")
        self.pinky03.set_parent_uuid(self.pinky02.get_uuid())
        self.pinky03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_pinky03 = pos_pinky02 + Vector3(x=3.2)
        self.pinky03.set_initial_position(xyz=pos_pinky03)
        self.pinky03.set_locator_scale(scale=0.2)
        self.pinky03.set_meta_type(value=self.pinky03.get_name())

        self.pinky04 = Proxy(name="pinky04")
        self.pinky04.set_parent_uuid(self.pinky03.get_uuid())
        self.pinky04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_pinky04 = pos_pinky03 + Vector3(x=3.5)
        self.pinky04.set_initial_position(xyz=pos_pinky04)
        self.pinky04.set_locator_scale(scale=0.15)
        self.pinky04.set_meta_type(value=self.pinky04.get_name())
        self.pinky04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.pinky_digits = [self.pinky01, self.pinky02, self.pinky03, self.pinky04]

        # Extra -------------------------------------------------------------------------------------
        self.extra_digits = []
        self.extra01 = Proxy(name="extra01")
        self.extra01.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_extra_base = Vector3(y=130.4) + pos_offset  # Center
        if self.side == "right":
            pos_extra_base = Vector3(x=-66.9, y=130.4, z=-5.3) + pos_offset  # Right
        elif self.side == "left":
            pos_extra_base = Vector3(x=66.9, y=130.4, z=-5.3) + pos_offset  # Left
        self.extra01.set_initial_position(xyz=pos_extra_base)
        self.extra01.set_locator_scale(scale=0.2)
        self.extra01.set_meta_type(value=self.extra01.get_name())

        self.extra02 = Proxy(name="extra02")
        self.extra02.set_parent_uuid(self.extra01.get_uuid())
        self.extra02.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_extra02 = pos_extra_base + Vector3(x=3)
        self.extra02.set_initial_position(xyz=pos_extra02)
        self.extra02.set_locator_scale(scale=0.2)
        self.extra02.set_meta_type(value=self.extra02.get_name())

        self.extra03 = Proxy(name="extra03")
        self.extra03.set_parent_uuid(self.extra02.get_uuid())
        self.extra03.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_extra03 = pos_extra02 + Vector3(x=3)
        self.extra03.set_initial_position(xyz=pos_extra03)
        self.extra03.set_locator_scale(scale=0.2)
        self.extra03.set_meta_type(value=self.extra03.get_name())

        self.extra04 = Proxy(name="extra04")
        self.extra04.set_parent_uuid(self.extra03.get_uuid())
        self.extra04.set_curve(curve=get_curve('_proxy_joint_dir_pos_y'))
        pos_extra04 = pos_extra03 + Vector3(x=3.3)
        self.extra04.set_initial_position(xyz=pos_extra04)
        self.extra04.set_locator_scale(scale=0.15)
        self.extra04.set_meta_type(value=self.extra04.get_name())
        self.extra04.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
        self.extra_digits = [self.extra01, self.extra02, self.extra03, self.extra04]

        # Update Proxies ----------------------------------------------------------------------------
        self.proxies.extend(self.thumb_digits)
        self.proxies.extend(self.index_digits)
        self.proxies.extend(self.middle_digits)
        self.proxies.extend(self.ring_digits)
        self.proxies.extend(self.pinky_digits)
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
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(RiggerConstants.PROXY_META_TYPE)
                for digit in self.proxies:
                    proxy_metadata = digit.get_metadata()
                    if not proxy_metadata or not isinstance(proxy_metadata, dict):
                        continue
                    if meta_type == proxy_metadata.get(RiggerConstants.PROXY_META_TYPE):
                        digit.set_uuid(uuid)
                        digit.read_data_from_dict(proxy_dict=description)


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
        proxy = super().build_proxy()  # Passthrough
        return proxy

    def build_proxy_post(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        Creates leg proxy behavior through constraints and offsets.
        """
        # Get Maya Elements
        root = find_objects_with_attr(RiggerConstants.ROOT_PROXY_ATTR)
        # thumb01 = find_proxy_node_from_uuid(self.thumb01.get_uuid())
        # thumb02 = find_proxy_node_from_uuid(self.thumb02.get_uuid())
        # thumb03 = find_proxy_node_from_uuid(self.thumb03.get_uuid())
        # thumb04 = find_proxy_node_from_uuid(self.thumb04.get_uuid())
        # shoulder = find_proxy_node_from_uuid(self.shoulder.get_uuid())
        # elbow = find_proxy_node_from_uuid(self.elbow.get_uuid())
        # wrist = find_proxy_node_from_uuid(self.wrist.get_uuid())
        #

        for digit in self.proxies:
            digit.apply_offset_transform()


        for digit in self.proxies:
            digit.apply_transforms()
        # self.thumb01.apply_offset_transform()
        # self.thumb02.apply_offset_transform()
        # self.thumb03.apply_offset_transform()
        # self.thumb04.apply_offset_transform()
        # self.shoulder.apply_offset_transform()
        # self.elbow.apply_offset_transform()
        # self.wrist.apply_offset_transform()
        #
        # # Shoulder -----------------------------------------------------------------------------------
        # hide_lock_default_attrs(shoulder, translate=False)
        #
        # # Elbow  -------------------------------------------------------------------------------------
        # elbow_tag = elbow.get_short_name()
        # hide_lock_default_attrs(elbow, translate=False, rotate=False)
        #
        # # Elbow Setup
        # elbow_offset = get_proxy_offset(elbow)
        #
        # elbow_pv_dir = cmds.spaceLocator(name=f'{elbow_tag}_poleVectorDir')[0]
        # elbow_pv_dir = Node(elbow_pv_dir)
        # match_translate(source=elbow, target_list=elbow_pv_dir)
        # cmds.move(0, 0, -10, elbow_pv_dir, relative=True)  # More it backwards (in front of the elbow)
        # hierarchy_utils.parent(elbow_pv_dir, elbow)
        #
        # elbow_dir_loc = cmds.spaceLocator(name=f'{elbow_tag}_dirParent_{NamingConstants.Suffix.LOC}')[0]
        # elbow_aim_loc = cmds.spaceLocator(name=f'{elbow_tag}_dirAim_{NamingConstants.Suffix.LOC}')[0]
        # elbow_upvec_loc = cmds.spaceLocator(name=f'{elbow_tag}_dirParentUp_{NamingConstants.Suffix.LOC}')[0]
        # elbow_upvec_loc_grp = f'{elbow_tag}_dirParentUp_{NamingConstants.Suffix.GRP}'
        # elbow_upvec_loc_grp = cmds.group(name=elbow_upvec_loc_grp, empty=True, world=True)
        #
        # elbow_dir_loc = Node(elbow_dir_loc)
        # elbow_aim_loc = Node(elbow_aim_loc)
        # elbow_upvec_loc = Node(elbow_upvec_loc)
        # elbow_upvec_loc_grp = Node(elbow_upvec_loc_grp)
        #
        # # Hide Reference Elements
        # hierarchy_utils.parent(elbow_aim_loc, elbow_dir_loc)
        # hierarchy_utils.parent(elbow_dir_loc, root)
        # hierarchy_utils.parent(elbow_upvec_loc_grp, root)
        # hierarchy_utils.parent(elbow_upvec_loc, elbow_upvec_loc_grp)
        #
        # cmds.pointConstraint(shoulder, elbow_dir_loc.get_long_name())
        # cmds.pointConstraint([wrist, shoulder], elbow_aim_loc.get_long_name())
        # cmds.aimConstraint(wrist, elbow_dir_loc.get_long_name())
        # cmds.pointConstraint(shoulder, elbow_upvec_loc_grp.get_long_name(), skip=['x', 'z'])
        #
        # elbow_divide_node = cmds.createNode('multiplyDivide', name=f'{elbow_tag}_divide')
        # cmds.setAttr(f'{elbow_divide_node}.operation', 2)  # Change operation to Divide
        # cmds.setAttr(f'{elbow_divide_node}.input2X', -2)
        # cmds.connectAttr(f'{wrist}.ty', f'{elbow_divide_node}.input1X')
        # cmds.connectAttr(f'{elbow_divide_node}.outputX', f'{elbow_upvec_loc}.ty')
        #
        # cmds.pointConstraint(shoulder, elbow_dir_loc.get_long_name())
        # cmds.pointConstraint([shoulder, wrist], elbow_aim_loc.get_long_name())
        #
        # cmds.connectAttr(f'{elbow_dir_loc}.rotate', f'{elbow_offset}.rotate')
        # cmds.pointConstraint([wrist, shoulder], elbow_offset)
        #
        # aim_vec = (-1, 0, 0)
        # if self.side == "right":
        #     aim_vec = (1, 0, 0)
        # elif self.side == "left":
        #     aim_vec = (-1, 0, 0)
        #
        # cmds.aimConstraint(wrist, elbow_dir_loc.get_long_name(), aimVector=aim_vec, upVector=aim_vec,
        #                    worldUpType='object', worldUpObject=elbow_upvec_loc.get_long_name())
        # cmds.aimConstraint(elbow_aim_loc.get_long_name(), elbow.get_long_name(), aimVector=(0, 0, 1),
        #                    upVector=(0, 1, 0), worldUpType='none', skip=['y', 'z'])
        #
        # cmds.setAttr(f'{elbow}.tz', -0.01)
        #
        # # Elbow Limits and Locks
        # cmds.setAttr(f'{elbow}.maxTransZLimit', -0.01)
        # cmds.setAttr(f'{elbow}.maxTransZLimitEnable', True)
        #
        # set_attr_state(obj_list=str(elbow), attr_list="rotate", locked=True)
        #
        # # Elbow Hide Setup
        # set_attr(obj_list=[elbow_pv_dir, elbow_upvec_loc_grp, elbow_dir_loc],
        #          attr_list="visibility", value=0)  # Set Visibility to Off
        # set_attr(obj_list=[elbow_pv_dir, elbow_upvec_loc_grp, elbow_dir_loc],
        #          attr_list="hiddenInOutliner", value=1)  # Set Outline Hidden to On
        #
        # self.clavicle.apply_transforms()
        # self.shoulder.apply_transforms()
        # self.elbow.apply_transforms()
        # self.wrist.apply_transforms()

        cmds.select(clear=True)

    def build_rig(self):
        super().build_rig()  # Passthrough


class ModuleBipedDigitsLeft(ModuleBipedDigits):
    def __init__(self,
                 name="Left Digits",
                 prefix=NamingConstants.Prefix.LEFT,
                 parent_uuid=None,
                 metadata=None,
                 pos_offset=None):
        super().__init__(name=name,
                         prefix=prefix,
                         parent_uuid=parent_uuid,
                         metadata=metadata,
                         pos_offset=pos_offset,
                         side="left")


class ModuleBipedDigitsRight(ModuleBipedDigits):
    def __init__(self,
                 name="Right Digits",
                 prefix=NamingConstants.Prefix.RIGHT,
                 parent_uuid=None,
                 metadata=None,
                 pos_offset=None):
        super().__init__(name=name,
                         prefix=prefix,
                         parent_uuid=parent_uuid,
                         metadata=metadata,
                         pos_offset=pos_offset,
                         side="right")


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rigger_framework import RigProject
    a_fingers_rt = ModuleBipedDigitsRight()
    a_fingers_lf = ModuleBipedDigitsLeft()
    a_project = RigProject()
    a_project.add_to_modules(a_fingers_rt)
    a_project.add_to_modules(a_fingers_lf)
    a_project.build_proxy()

    # cmds.setAttr(f'lf_thumb02.rx', 30)
    # cmds.setAttr(f'rt_thumb02.rx', 30)
    # cmds.setAttr(f'lf_ring02.rz', -45)
    #
    # print(a_project.get_project_as_dict().get("modules"))
    # a_project.read_data_from_scene()
    # print(a_project.get_project_as_dict().get("modules"))
    # dictionary = a_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = RigProject()
    # a_project2.read_data_from_dict(dictionary)
    # print(a_project2.get_project_as_dict().get("modules"))
    # a_project2.build_proxy()

    # Frame all
    cmds.viewFit(all=True)
