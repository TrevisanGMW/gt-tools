"""
Auto Rigger Head Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import find_proxy_node_from_uuid, find_joint_node_from_uuid
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.utils.color_utils import ColorConstants, set_color_viewport
from gt.utils.joint_utils import copy_parent_orients, reset_orients
from gt.tools.auto_rigger.rig_constants import RiggerConstants
from gt.utils.constraint_utils import equidistant_constraints
from gt.tools.auto_rigger.rig_utils import get_proxy_offset
from gt.utils.naming_utils import NamingConstants
from gt.utils.transform_utils import Vector3
from gt.ui import resource_library
import maya.cmds as cmds
import logging
import re


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleHead(ModuleGeneric):
    __version__ = '0.0.1-alpha'
    icon = resource_library.Icon.rigger_module_head
    allow_parenting = True

    def __init__(self, name="Head", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        _end_suffix = NamingConstants.Suffix.END.capitalize()

        # Neck Base (Chain Base)
        self.neck_base = Proxy(name="neckBase")
        pos_neck_base = Vector3(y=137)
        self.neck_base.set_initial_position(xyz=pos_neck_base)
        self.neck_base.set_locator_scale(scale=1.5)
        self.neck_base.set_meta_purpose(value="neckBase")

        # Head (Chain End)
        self.head = Proxy(name="head")
        pos_head = Vector3(y=142.5)
        self.head.set_initial_position(xyz=pos_head)
        self.head.set_locator_scale(scale=1.5)
        self.head.set_meta_purpose(value="head")

        # Head End
        self.head_end = Proxy(name=f"head{_end_suffix}")
        pos_head_end = Vector3(y=160)
        self.head_end.set_initial_position(xyz=pos_head_end)
        self.head_end.set_locator_scale(scale=1)
        self.head_end.set_meta_purpose(value="headEnd")
        self.head_end.set_parent_uuid(self.head.get_uuid())
        self.head_end.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)

        # Jaw
        self.jaw = Proxy(name="jaw")
        pos_jaw = Vector3(y=147.5, z=2.5)
        self.jaw.set_initial_position(xyz=pos_jaw)
        self.jaw.set_locator_scale(scale=1.5)
        self.jaw.set_meta_purpose(value="jaw")
        self.jaw.set_parent_uuid(self.head.get_uuid())

        # Jaw End
        self.jaw_end = Proxy(name=f"jaw{_end_suffix}")
        pos_jaw_end = Vector3(y=142.5, z=11)
        self.jaw_end.set_initial_position(xyz=pos_jaw_end)
        self.jaw_end.set_locator_scale(scale=1)
        self.jaw_end.set_meta_purpose(value="jawEnd")
        self.jaw_end.set_parent_uuid(self.jaw.get_uuid())
        self.jaw_end.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)

        # Left Eye
        self.lt_eye = Proxy(name=f'{NamingConstants.Prefix.LEFT}_eye')
        pos_lt_eye = Vector3(x=3.5, y=151, z=8.7)
        self.lt_eye.set_initial_position(xyz=pos_lt_eye)
        self.lt_eye.set_locator_scale(scale=2.5)
        self.lt_eye.set_meta_purpose(value="eyeLeft")
        self.lt_eye.set_parent_uuid(self.head.get_uuid())

        # Right Eye
        self.rt_eye = Proxy(name=f'{NamingConstants.Prefix.RIGHT}_eye')
        pos_rt_eye = Vector3(x=-3.5, y=151, z=8.7)
        self.rt_eye.set_initial_position(xyz=pos_rt_eye)
        self.rt_eye.set_locator_scale(scale=2.5)
        self.rt_eye.set_meta_purpose(value="eyeRight")
        self.rt_eye.set_parent_uuid(self.head.get_uuid())

        # Neck Mid (In-between)
        self.neck_mid_list = []
        self.set_mid_neck_num(neck_mid_num=1)

    def set_mid_neck_num(self, neck_mid_num):
        """
        Set a new number of neckMid proxies. These are the proxies in-between the hip proxy (base) and head proxy (end)
        Args:
            neck_mid_num (int): New number of neckMid proxies to exist in-between neckBase and head.
                                Minimum is zero (0) - No negative numbers.
        """
        neck_mid_len = len(self.neck_mid_list)
        # Same as current, skip
        if neck_mid_len == neck_mid_num:
            return
        # New number higher than current - Add more proxies (neck_mid_list)
        if neck_mid_len < neck_mid_num:
            # Determine Initial Parent (Last neckMid, or neckBase)
            if self.neck_mid_list:
                _parent_uuid = self.neck_mid_list[-1].get_uuid()
            else:
                _parent_uuid = self.neck_base.get_uuid()
            # Create new proxies
            for num in range(neck_mid_len, neck_mid_num):
                _neck_mid_name = f'neckMid{str(num + 1).zfill(2)}'
                new_neck_mid = Proxy(name=_neck_mid_name)
                new_neck_mid.set_locator_scale(scale=1)
                new_neck_mid.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
                new_neck_mid.set_meta_purpose(value=_neck_mid_name)
                new_neck_mid.add_meta_parent(line_parent=_parent_uuid)
                new_neck_mid.set_parent_uuid(uuid=_parent_uuid)
                _parent_uuid = new_neck_mid.get_uuid()
                self.neck_mid_list.append(new_neck_mid)
        # New number lower than current - Remove unnecessary proxies
        elif len(self.neck_mid_list) > neck_mid_num:
            self.neck_mid_list = self.neck_mid_list[:neck_mid_num]  # Truncate the list

        if self.neck_mid_list:
            self.head.add_meta_parent(line_parent=self.neck_mid_list[-1].get_uuid())
        else:
            self.head.add_meta_parent(line_parent=self.neck_base.get_uuid())

        self.refresh_proxies_list()

    def refresh_proxies_list(self):
        """
        Refreshes the main proxies list used by the module during build (update in case objects were updated)
        """
        self.proxies = [self.neck_base]
        self.proxies.extend(self.neck_mid_list)
        self.proxies.append(self.head)
        self.proxies.append(self.head_end)
        self.proxies.append(self.lt_eye)
        self.proxies.append(self.rt_eye)
        self.proxies.append(self.jaw)
        self.proxies.append(self.jaw_end)

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
        # Determine Number of Spine Proxies
        _neck_mid_num = 0
        neck_mid_pattern = r'neckMid\d+'
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(RiggerConstants.PROXY_META_PURPOSE)
                if bool(re.match(neck_mid_pattern, meta_type)):
                    _neck_mid_num += 1
        self.set_mid_neck_num(_neck_mid_num)
        self.read_purpose_matching_proxy_from_dict(proxy_dict)
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
        if self.parent_uuid:
            if self.neck_base:
                self.neck_base.set_parent_uuid(self.parent_uuid)
        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        # Get Maya Elements
        hip = find_proxy_node_from_uuid(self.neck_base.get_uuid())
        chest = find_proxy_node_from_uuid(self.head.get_uuid())

        neck_mid_list = []
        for neck_mid in self.neck_mid_list:
            neck_node = find_proxy_node_from_uuid(neck_mid.get_uuid())
            neck_mid_list.append(neck_node)
        self.neck_base.apply_offset_transform()
        self.head.apply_offset_transform()
        self.head_end.apply_offset_transform()
        self.jaw.apply_offset_transform()
        self.jaw_end.apply_offset_transform()
        self.lt_eye.apply_offset_transform()
        self.rt_eye.apply_offset_transform()

        neck_mid_offsets = []
        for neck_mid in neck_mid_list:
            offset = get_proxy_offset(neck_mid)
            neck_mid_offsets.append(offset)
        equidistant_constraints(start=hip, end=chest, target_list=neck_mid_offsets)

        self.neck_base.apply_transforms()
        self.head.apply_transforms()
        for neck_mid in self.neck_mid_list:
            neck_mid.apply_transforms()
        self.head_end.apply_transforms()
        self.jaw.apply_transforms()
        self.jaw_end.apply_transforms()
        self.lt_eye.apply_transforms()
        self.rt_eye.apply_transforms()
        cmds.select(clear=True)

    def build_skeleton_joints(self):
        super().build_skeleton_joints()  # Passthrough

    def build_skeleton_hierarchy(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        self.head.set_parent_uuid(uuid=self.head.get_meta_parent_uuid())
        super().build_skeleton_hierarchy()  # Passthrough
        self.head.clear_parent_uuid()

        head_jnt = find_joint_node_from_uuid(self.head.get_uuid())
        head_end_jnt = find_joint_node_from_uuid(self.head_end.get_uuid())
        jaw_jnt = find_joint_node_from_uuid(self.jaw.get_uuid())
        jaw_end_jnt = find_joint_node_from_uuid(self.jaw_end.get_uuid())
        lt_eye = find_joint_node_from_uuid(self.lt_eye.get_uuid())
        rt_eye = find_joint_node_from_uuid(self.rt_eye.get_uuid())
        copy_parent_orients(joint_list=[head_jnt, head_end_jnt])
        reset_orients(joint_list=[lt_eye, rt_eye], verbose=True)
        set_color_viewport(obj_list=[head_end_jnt, jaw_end_jnt], rgb_color=ColorConstants.RigJoint.END)
        set_color_viewport(obj_list=[lt_eye, rt_eye], rgb_color=ColorConstants.RigJoint.UNIQUE)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject

    a_head = ModuleHead()
    # a_head.set_mid_neck_num(0)
    # a_head.set_mid_neck_num(6)
    a_project = RigProject()
    a_project.add_to_modules(a_head)
    a_project.build_proxy()
    a_project.build_rig()

    # cmds.setAttr(f'jaw.rx', -35)
    # cmds.setAttr(f'head.tx', 3)
    # cmds.setAttr(f'head.rz', -30)

    # a_project.read_data_from_scene()
    # dictionary = a_project.get_project_as_dict()
    #
    # cmds.file(new=True, force=True)
    # a_project2 = RigProject()
    # a_project2.read_data_from_dict(dictionary)
    # a_project2.build_proxy()

    # # Show all
    cmds.viewFit(all=True)
