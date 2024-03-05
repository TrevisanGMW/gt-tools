"""
Auto Rigger Head Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import find_proxy_from_uuid, find_joint_from_uuid, find_direction_curve
from gt.tools.auto_rigger.rig_utils import get_proxy_offset, get_automation_group, create_ctrl_curve
from gt.utils.transform_utils import Vector3, match_transform, scale_shapes, translate_shapes, rotate_shapes
from gt.utils.transform_utils import set_equidistant_transforms
from gt.utils.attr_utils import add_separator_attr, set_attr_state, rescale, hide_lock_default_attrs, set_attr
from gt.utils.rigging_utils import offset_control_orientation, expose_rotation_order, RiggingConstants
from gt.utils.constraint_utils import equidistant_constraints, constraint_targets, ConstraintTypes
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.tools.auto_rigger.rig_constants import RiggerConstants, RiggerDriverTypes
from gt.utils.hierarchy_utils import add_offset_transform, create_group
from gt.utils.color_utils import ColorConstants, set_color_viewport
from gt.utils.joint_utils import copy_parent_orients, reset_orients
from gt.utils.curve_utils import create_connection_line
from gt.utils.math_utils import dist_center_to_center
from gt.utils.naming_utils import NamingConstants
from gt.utils.node_utils import Node
from gt.utils import hierarchy_utils
from gt.ui import resource_library
import maya.cmds as cmds
import logging
import re

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleHead(ModuleGeneric):
    __version__ = '0.0.2-alpha'
    icon = resource_library.Icon.rigger_module_head
    allow_parenting = True

    def __init__(self, name="Head", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        _end_suffix = NamingConstants.Suffix.END.capitalize()
        self.main_eye_ctrl = f"main_eye_{NamingConstants.Suffix.CTRL}"  # Not yet exposed/editable

        # Neck Base (Chain Base)
        self.neck_base = Proxy(name="neckBase")
        pos_neck_base = Vector3(y=137)
        self.neck_base.set_initial_position(xyz=pos_neck_base)
        self.neck_base.set_locator_scale(scale=1.5)
        self.neck_base.set_meta_purpose(value="neckBase")
        self.neck_base.add_driver_type(driver_type=[RiggerDriverTypes.FK])

        # Head (Chain End)
        self.head = Proxy(name="head")
        pos_head = Vector3(y=142.5)
        self.head.set_initial_position(xyz=pos_head)
        self.head.set_locator_scale(scale=1.5)
        self.head.set_meta_purpose(value="head")
        self.head.add_driver_type(driver_type=[RiggerDriverTypes.OFFSET, RiggerDriverTypes.FK])

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
        self.jaw.add_driver_type(driver_type=[RiggerDriverTypes.FK])

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
        self.lt_eye.add_driver_type(driver_type=[RiggerDriverTypes.AIM])

        # Right Eye
        self.rt_eye = Proxy(name=f'{NamingConstants.Prefix.RIGHT}_eye')
        pos_rt_eye = Vector3(x=-3.5, y=151, z=8.7)
        self.rt_eye.set_initial_position(xyz=pos_rt_eye)
        self.rt_eye.set_locator_scale(scale=2.5)
        self.rt_eye.set_meta_purpose(value="eyeRight")
        self.rt_eye.set_parent_uuid(self.head.get_uuid())
        self.rt_eye.add_driver_type(driver_type=[RiggerDriverTypes.AIM])

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
                new_neck_mid.add_line_parent(line_parent=_parent_uuid)
                new_neck_mid.set_parent_uuid(uuid=_parent_uuid)
                new_neck_mid.add_driver_type(driver_type=[RiggerDriverTypes.FK])
                _parent_uuid = new_neck_mid.get_uuid()
                self.neck_mid_list.append(new_neck_mid)
        # New number lower than current - Remove unnecessary proxies
        elif len(self.neck_mid_list) > neck_mid_num:
            self.neck_mid_list = self.neck_mid_list[:neck_mid_num]  # Truncate the list

        if self.neck_mid_list:
            self.head.add_line_parent(line_parent=self.neck_mid_list[-1].get_uuid())
        else:
            self.head.add_line_parent(line_parent=self.neck_base.get_uuid())

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
                meta_type = metadata.get(RiggerConstants.META_PROXY_PURPOSE)
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
        hip = find_proxy_from_uuid(self.neck_base.get_uuid())
        chest = find_proxy_from_uuid(self.head.get_uuid())

        neck_mid_list = []
        for neck_mid in self.neck_mid_list:
            neck_node = find_proxy_from_uuid(neck_mid.get_uuid())
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

    def build_rig(self, **kwargs):
        # Get Elements
        direction_crv = find_direction_curve()
        neck_base_jnt = find_joint_from_uuid(self.neck_base.get_uuid())
        head_jnt = find_joint_from_uuid(self.head.get_uuid())
        head_end_jnt = find_joint_from_uuid(self.head_end.get_uuid())
        jaw_jnt = find_joint_from_uuid(self.jaw.get_uuid())
        jaw_end_jnt = find_joint_from_uuid(self.jaw_end.get_uuid())
        lt_eye = find_joint_from_uuid(self.lt_eye.get_uuid())
        rt_eye = find_joint_from_uuid(self.rt_eye.get_uuid())
        middle_jnt_list = []
        for proxy in self.neck_mid_list:
            mid_jnt = find_joint_from_uuid(proxy.get_uuid())
            if mid_jnt:
                middle_jnt_list.append(mid_jnt)
        copy_parent_orients(joint_list=[head_jnt, head_end_jnt])
        reset_orients(joint_list=[lt_eye, rt_eye], verbose=True)
        set_color_viewport(obj_list=[head_end_jnt, jaw_end_jnt], rgb_color=ColorConstants.RigJoint.END)
        set_color_viewport(obj_list=[lt_eye, rt_eye], rgb_color=ColorConstants.RigJoint.UNIQUE)

        # Get Scale
        head_scale = dist_center_to_center(neck_base_jnt, head_jnt)
        head_scale += dist_center_to_center(head_jnt, head_end_jnt)

        # Neck Base ------------------------------------------------------------------------------------------
        neck_base_ctrl = self._assemble_ctrl_name(name=self.neck_base.get_name())
        neck_base_ctrl = create_ctrl_curve(name=neck_base_ctrl, curve_file_name="_pin_neg_y")
        self.add_driver_uuid_attr(target=neck_base_ctrl,
                                  driver_type=RiggerDriverTypes.FK,
                                  proxy_purpose=self.neck_base)
        neck_base_offset = add_offset_transform(target_list=neck_base_ctrl)[0]
        neck_base_offset = Node(neck_base_offset)
        match_transform(source=neck_base_jnt, target_list=neck_base_offset)
        scale_shapes(obj_transform=neck_base_ctrl, offset=head_scale*.3)
        offset_control_orientation(ctrl=neck_base_ctrl, offset_transform=neck_base_offset, orient_tuple=(-90, -90, 0))
        hierarchy_utils.parent(source_objects=neck_base_offset, target_parent=direction_crv)
        constraint_targets(source_driver=neck_base_ctrl, target_driven=neck_base_jnt)
        # Attributes
        set_attr_state(attribute_path=f"{neck_base_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=neck_base_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        expose_rotation_order(neck_base_ctrl)

        # Neck Mid Controls ----------------------------------------------------------------------------------
        neck_mid_ctrls = []
        last_mid_parent_ctrl = neck_base_ctrl
        for neck_mid_proxy, mid_jnt in zip(self.neck_mid_list, middle_jnt_list):
            neck_mid_ctrl = self._assemble_ctrl_name(name=neck_mid_proxy.get_name())
            neck_mid_ctrl = create_ctrl_curve(name=neck_mid_ctrl, curve_file_name="_pin_neg_y")
            self.add_driver_uuid_attr(target=neck_mid_ctrl, driver_type=RiggerDriverTypes.FK,
                                      proxy_purpose=neck_mid_proxy)
            neck_mid_offset = Node(add_offset_transform(target_list=neck_mid_ctrl)[0])
            _shape_scale_mid = head_scale*.2
            child_joint = cmds.listRelatives(mid_jnt, fullPath=True, children=True, typ="joint")
            if child_joint:
                _distance = dist_center_to_center(obj_a=mid_jnt, obj_b=child_joint[0])
                _shape_scale_mid = _distance*1.5
            scale_shapes(obj_transform=neck_mid_ctrl, offset=_shape_scale_mid)
            # Position and Constraint
            match_transform(source=mid_jnt, target_list=neck_mid_offset)
            offset_control_orientation(ctrl=neck_mid_ctrl,
                                       offset_transform=neck_mid_offset,
                                       orient_tuple=(-90, -90, 0))
            hierarchy_utils.parent(source_objects=neck_mid_offset, target_parent=last_mid_parent_ctrl)
            # Attributes
            set_attr_state(attribute_path=f"{neck_mid_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
            add_separator_attr(target_object=neck_mid_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
            expose_rotation_order(neck_mid_ctrl)
            neck_mid_ctrls.append(neck_mid_ctrl)
            constraint_targets(source_driver=neck_mid_ctrl, target_driven=mid_jnt)
            last_mid_parent_ctrl = neck_mid_ctrl

        # Head Ctrl -----------------------------------------------------------------------------------------
        head_ctrl = self._assemble_ctrl_name(name=self.head.get_name())
        head_ctrl = create_ctrl_curve(name=head_ctrl, curve_file_name="_circle_pos_x")
        self.add_driver_uuid_attr(target=head_ctrl,
                                  driver_type=RiggerDriverTypes.FK,
                                  proxy_purpose=self.head)
        head_offset = add_offset_transform(target_list=head_ctrl)[0]
        head_offset = Node(head_offset)
        match_transform(source=head_jnt, target_list=head_offset)
        scale_shapes(obj_transform=head_ctrl, offset=head_scale * .4)
        offset_control_orientation(ctrl=head_ctrl, offset_transform=head_offset, orient_tuple=(-90, -90, 0))
        head_end_distance = dist_center_to_center(head_jnt, head_end_jnt)
        translate_shapes(obj_transform=head_ctrl, offset=(0, head_end_distance*1.1, 0))  # Move Above Head
        hierarchy_utils.parent(source_objects=head_offset, target_parent=last_mid_parent_ctrl)
        # Attributes
        set_attr_state(attribute_path=f"{head_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=head_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        expose_rotation_order(head_ctrl)

        # Head Offset Ctrl
        head_o_ctrl = self._assemble_ctrl_name(name=self.head.get_name(),
                                               overwrite_suffix=NamingConstants.Control.OFFSET_CTRL)
        head_o_ctrl = create_ctrl_curve(name=head_o_ctrl, curve_file_name="_circle_pos_x")
        match_transform(source=head_ctrl, target_list=head_o_ctrl)
        scale_shapes(obj_transform=head_o_ctrl, offset=head_scale * .35)
        rotate_shapes(obj_transform=head_o_ctrl, offset=(0, 0, -90))
        translate_shapes(obj_transform=head_o_ctrl, offset=(0, head_end_distance*1.1, 0))  # Move Above Head
        set_color_viewport(obj_list=head_o_ctrl, rgb_color=ColorConstants.RigJoint.OFFSET)
        hierarchy_utils.parent(source_objects=head_o_ctrl, target_parent=head_ctrl)
        # Head Offset Data Transform
        head_o_data = self._assemble_ctrl_name(name=self.head.get_name(),
                                               overwrite_suffix=NamingConstants.Control.OFFSET_DATA)
        head_o_data = create_group(name=head_o_data)
        head_o_data = Node(head_o_data)
        self.add_driver_uuid_attr(target=head_o_data,
                                  driver_type=RiggerDriverTypes.OFFSET,
                                  proxy_purpose=self.head)
        hierarchy_utils.parent(source_objects=head_o_data, target_parent=head_ctrl)
        # Connections
        cmds.connectAttr(f'{head_o_ctrl}.translate', f'{head_o_data}.translate')
        cmds.connectAttr(f'{head_o_ctrl}.rotate', f'{head_o_data}.rotate')
        constraint_targets(source_driver=head_o_data, target_driven=head_jnt)
        # Attributes
        set_attr_state(attribute_path=f"{head_o_ctrl}.v", hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=head_o_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        expose_rotation_order(head_o_ctrl)
        cmds.addAttr(head_ctrl, ln='showOffsetCtrl', at='bool', k=True)
        cmds.connectAttr(f'{head_ctrl}.showOffsetCtrl', f'{head_o_ctrl}.v')

        # Jaw Ctrl -----------------------------------------------------------------------------------------
        jaw_ctrl = self._assemble_ctrl_name(name=self.jaw.get_name())
        jaw_ctrl = create_ctrl_curve(name=jaw_ctrl, curve_file_name="_concave_crescent_neg_y")
        self.add_driver_uuid_attr(target=jaw_ctrl,
                                  driver_type=RiggerDriverTypes.FK,
                                  proxy_purpose=self.jaw)
        jaw_offset = add_offset_transform(target_list=jaw_ctrl)[0]
        jaw_offset = Node(jaw_offset)
        jaw_end_distance = dist_center_to_center(jaw_jnt, jaw_end_jnt)
        match_transform(source=jaw_jnt, target_list=jaw_offset)
        scale_shapes(obj_transform=jaw_ctrl, offset=jaw_end_distance * .2)
        offset_control_orientation(ctrl=jaw_ctrl, offset_transform=jaw_offset, orient_tuple=(-90, -90, 0))
        translate_shapes(obj_transform=jaw_ctrl,
                         offset=(0, jaw_end_distance * 1.1, jaw_end_distance*.1))  # Move Shape To Jaw End
        hierarchy_utils.parent(source_objects=jaw_offset, target_parent=head_o_data)
        constraint_targets(source_driver=jaw_ctrl, target_driven=jaw_jnt)
        # Attributes
        set_attr_state(attribute_path=f"{jaw_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=jaw_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        expose_rotation_order(jaw_ctrl)

        # Eye Controls -------------------------------------------------------------------------------------
        lt_eye_ctrl = self._assemble_ctrl_name(name=self.lt_eye.get_name())
        rt_eye_ctrl = self._assemble_ctrl_name(name=self.rt_eye.get_name())
        lt_eye_ctrl = create_ctrl_curve(name=lt_eye_ctrl, curve_file_name="_circle_pos_z")
        rt_eye_ctrl = create_ctrl_curve(name=rt_eye_ctrl, curve_file_name="_circle_pos_z")
        self.add_driver_uuid_attr(target=lt_eye_ctrl,
                                  driver_type=RiggerDriverTypes.AIM,
                                  proxy_purpose=self.lt_eye)
        self.add_driver_uuid_attr(target=rt_eye_ctrl,
                                  driver_type=RiggerDriverTypes.AIM,
                                  proxy_purpose=self.rt_eye)
        main_eye_ctrl = create_ctrl_curve(name=self.main_eye_ctrl, curve_file_name="_peanut_pos_z")
        lt_eye_offset = add_offset_transform(target_list=lt_eye_ctrl)[0]
        rt_eye_offset = add_offset_transform(target_list=rt_eye_ctrl)[0]
        lt_eye_offset = Node(lt_eye_offset)
        rt_eye_offset = Node(rt_eye_offset)
        main_eye_offset = add_offset_transform(target_list=main_eye_ctrl)[0]
        main_eye_offset = Node(main_eye_offset)

        # Create Divergence Drivers
        lt_eye_divergence = add_offset_transform(target_list=lt_eye_ctrl)[0]
        rt_eye_divergence = add_offset_transform(target_list=rt_eye_ctrl)[0]
        lt_eye_divergence = Node(lt_eye_divergence)
        rt_eye_divergence = Node(rt_eye_divergence)
        lt_eye_divergence.rename(f'{self.lt_eye.get_name()}_divergenceData')
        rt_eye_divergence.rename(f'{self.rt_eye.get_name()}_divergenceData')

        # Organize and Position Elements
        hierarchy_utils.parent(source_objects=[lt_eye_offset, rt_eye_offset], target_parent=main_eye_ctrl)
        cmds.move(1.6, 0, 0, lt_eye_offset)
        cmds.move(-1.6, 0, 0, rt_eye_offset)

        pupillary_distance = dist_center_to_center(lt_eye, rt_eye)
        rescale(obj=main_eye_offset, scale=pupillary_distance*.31, freeze=False)

        hierarchy_utils.parent(source_objects=main_eye_offset, target_parent=head_o_data)

        set_equidistant_transforms(start=rt_eye, end=lt_eye, target_list=main_eye_offset)  # Place in-between eyes
        cmds.move(0, 0, head_scale * 2, main_eye_offset, relative=True)

        # Constraints and Vectors
        lt_eye_up_vec = cmds.spaceLocator(name=f'{self.lt_eye.get_name()}_upVec')[0]
        rt_eye_up_vec = cmds.spaceLocator(name=f'{self.rt_eye.get_name()}_upVec')[0]
        match_transform(source=lt_eye, target_list=lt_eye_up_vec)
        match_transform(source=rt_eye, target_list=rt_eye_up_vec)
        cmds.move(head_scale, lt_eye_up_vec, y=True, relative=True, objectSpace=True)
        cmds.move(head_scale, rt_eye_up_vec, y=True, relative=True, objectSpace=True)
        set_attr(obj_list=[lt_eye_up_vec, rt_eye_up_vec],
                 attr_list=["localScaleX", "localScaleY", "localScaleZ"], value=head_scale*.1)
        set_attr(obj_list=[lt_eye_up_vec, rt_eye_up_vec],
                 attr_list="v", value=False)
        hierarchy_utils.parent(source_objects=[lt_eye_up_vec, rt_eye_up_vec], target_parent=head_o_data)

        constraint_targets(source_driver=lt_eye_ctrl, target_driven=lt_eye, constraint_type=ConstraintTypes.AIM,
                           upVector=(0, 1, 0), worldUpType="object", worldUpObject=lt_eye_up_vec)
        constraint_targets(source_driver=rt_eye_ctrl, target_driven=rt_eye, constraint_type=ConstraintTypes.AIM,
                           upVector=(0, 1, 0), worldUpType="object", worldUpObject=rt_eye_up_vec)

        # Attributes and Colors
        lt_lines = create_connection_line(object_a=lt_eye_ctrl,
                                          object_b=lt_eye)
        rt_lines = create_connection_line(object_a=rt_eye_ctrl,
                                          object_b=rt_eye)

        set_color_viewport(obj_list=lt_eye_ctrl, rgb_color=ColorConstants.RigProxy.LEFT)
        set_color_viewport(obj_list=lt_eye_up_vec, rgb_color=ColorConstants.RigProxy.LEFT)
        set_color_viewport(obj_list=rt_eye_ctrl, rgb_color=ColorConstants.RigProxy.RIGHT)
        set_color_viewport(obj_list=rt_eye_up_vec, rgb_color=ColorConstants.RigProxy.RIGHT)
        aim_lines_grp = get_automation_group(name=f"headAutomation_{NamingConstants.Suffix.GRP}",
                                             subgroup=f"aimLines_{NamingConstants.Suffix.GRP}")
        hierarchy_utils.parent(source_objects=lt_lines + rt_lines, target_parent=aim_lines_grp)

        hide_lock_default_attrs(obj_list=[lt_eye_ctrl, rt_eye_ctrl], rotate=True, scale=True, visibility=True)
        hide_lock_default_attrs(obj_list=main_eye_ctrl, scale=True, visibility=True)
        add_separator_attr(target_object=main_eye_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        expose_rotation_order(main_eye_ctrl)

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [neck_base_offset]


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.utils.session_utils import remove_modules_startswith
    remove_modules_startswith("gt.tools.auto_rigger.module")
    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject
    from gt.tools.auto_rigger.module_spine import ModuleSpine

    a_spine = ModuleSpine()
    a_head = ModuleHead()
    spine_chest_uuid = a_spine.chest.get_uuid()
    a_head.set_parent_uuid(spine_chest_uuid)
    a_project = RigProject()
    a_project.add_to_modules(a_spine)
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
