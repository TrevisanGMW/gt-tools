"""
Auto Rigger Spine Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import find_or_create_joint_automation_group, get_driven_joint, create_ctrl_curve
from gt.tools.auto_rigger.rig_utils import find_proxy_from_uuid, find_direction_curve, find_joint_from_uuid
from gt.tools.auto_rigger.rig_utils import get_automation_group, get_proxy_offset, connect_supporting_driver
from gt.utils.attr_utils import add_separator_attr, set_attr_state, connect_attr, hide_lock_default_attrs, add_attr
from gt.utils.rigging_utils import duplicate_joint_for_automation, create_stretchy_ik_setup, duplicate_object
from gt.utils.rigging_utils import expose_rotation_order, offset_control_orientation, rescale_joint_radius
from gt.utils.rigging_utils import RiggingConstants, create_switch_setup, add_limit_lock_translate_setup
from gt.utils.transform_utils import Vector3, scale_shapes, match_transform, translate_shapes, rotate_shapes
from gt.utils.transform_utils import match_translate, set_equidistant_transforms
from gt.utils.surface_utils import create_surface_from_object_list, create_follicle, get_closest_uv_point
from gt.utils.constraint_utils import equidistant_constraints, constraint_targets, ConstraintTypes
from gt.utils.color_utils import ColorConstants, set_color_viewport, set_color_outliner
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.tools.auto_rigger.rig_constants import RiggerConstants, RiggerDriverTypes
from gt.utils.curve_utils import set_curve_width, create_connection_line
from gt.utils.hierarchy_utils import add_offset_transform, create_group
from gt.utils.math_utils import dist_center_to_center
from gt.utils.joint_utils import set_joint_radius
from gt.utils.naming_utils import NamingConstants
from gt.utils.node_utils import Node, create_node
from gt.utils.outliner_utils import reorder_front
from gt.utils import hierarchy_utils
from gt.ui import resource_library
import maya.cmds as cmds
import logging
import re


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleSpine(ModuleGeneric):
    __version__ = '0.1.4-beta'
    icon = resource_library.Icon.rigger_module_spine
    allow_parenting = True

    # Metadata Keys
    META_DROPOFF_RATE = "ribbonDropoffRate"
    META_COG_NAME = "cogCtrlName"  # Metadata key for a custom name used for the center of gravity control
    # Default Values
    DEFAULT_SETUP_NAME = "spine"
    DEFAULT_COG_NAME = "cog"
    DEFAULT_DROPOFF_RATE = 1

    def __init__(self, name="Spine", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Extra Module Data
        self.set_meta_setup_name(name=self.DEFAULT_SETUP_NAME)
        self.add_to_metadata(key=self.META_DROPOFF_RATE, value=self.DEFAULT_DROPOFF_RATE)
        self.add_to_metadata(key=self.META_COG_NAME, value=self.DEFAULT_COG_NAME)

        # Hip (Base)
        self.hip = Proxy(name="hip")
        pos_hip = Vector3(y=84.5)
        self.hip.set_initial_position(xyz=pos_hip)
        self.hip.set_locator_scale(scale=1.5)
        self.hip.set_meta_purpose(value="hip")
        self.hip.add_driver_type(driver_type=[RiggerDriverTypes.GENERIC,  # Hip Data Offset
                                              RiggerDriverTypes.FK,
                                              RiggerDriverTypes.PIVOT,
                                              RiggerDriverTypes.COG])  # COG is the IK/FK Switch

        # Chest (End)
        self.chest = Proxy(name="chest")
        pos_chest = Vector3(y=114.5)
        self.chest.set_initial_position(xyz=pos_chest)
        self.chest.set_locator_scale(scale=1.5)
        self.chest.set_meta_purpose(value="chest")
        self.chest.add_driver_type(driver_type=[RiggerDriverTypes.GENERIC,  # Manually created Generic Driver
                                                RiggerDriverTypes.IK,
                                                RiggerDriverTypes.PIVOT,
                                                RiggerDriverTypes.FK])
        # Spines (In-between)
        self.spines = []
        self.set_spine_num(spine_num=3)

    def set_spine_num(self, spine_num):
        """
        Set a new number of spine proxies. These are the proxies in-between the hip proxy (base) and chest proxy (end)
        Args:
            spine_num (int): New number of spines to exist in-between hip and chest.
                             Minimum is zero (0) - No negative numbers.
        """
        spines_len = len(self.spines)
        # Same as current, skip
        if spines_len == spine_num:
            return
        # New number higher than current - Add more proxies (spines)
        if spines_len < spine_num:
            # Determine Initial Parent (Last spine, or hip)
            if self.spines:
                _parent_uuid = self.spines[-1].get_uuid()
            else:
                _parent_uuid = self.hip.get_uuid()
            # Create new spines
            for num in range(spines_len, spine_num):
                new_spine = Proxy(name=f'spine{str(num + 1).zfill(2)}')
                new_spine.set_locator_scale(scale=1)
                new_spine.add_color(rgb_color=ColorConstants.RigProxy.FOLLOWER)
                new_spine.set_meta_purpose(value=f'spine{str(num + 1).zfill(2)}')
                new_spine.add_line_parent(line_parent=_parent_uuid)
                new_spine.set_parent_uuid(uuid=_parent_uuid)
                new_spine.add_driver_type(driver_type=[RiggerDriverTypes.GENERIC,
                                                       RiggerDriverTypes.FK])
                _parent_uuid = new_spine.get_uuid()
                self.spines.append(new_spine)
        # New number lower than current - Remove unnecessary proxies
        elif len(self.spines) > spine_num:
            self.spines = self.spines[:spine_num]  # Truncate the list

        if self.spines:
            self.chest.add_line_parent(line_parent=self.spines[-1].get_uuid())
        else:
            self.chest.add_line_parent(line_parent=self.hip.get_uuid())

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
        # Determine Number of Spine Proxies
        _spine_num = 0
        spine_pattern = r'spine\d+'
        for uuid, description in proxy_dict.items():
            metadata = description.get("metadata")
            if metadata:
                meta_type = metadata.get(RiggerConstants.META_PROXY_PURPOSE)
                if bool(re.match(spine_pattern, meta_type)):
                    _spine_num += 1
        self.set_spine_num(_spine_num)
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
            if self.hip:
                self.hip.set_parent_uuid(self.parent_uuid)
        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        # Get Maya Elements
        hip = find_proxy_from_uuid(self.hip.get_uuid())
        chest = find_proxy_from_uuid(self.chest.get_uuid())

        spines = []
        for spine in self.spines:
            spine_node = find_proxy_from_uuid(spine.get_uuid())
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

    def build_skeleton_joints(self):
        super().build_skeleton_joints()  # Passthrough

    def build_skeleton_hierarchy(self):
        """
        Runs post rig script.
        When in a project, this runs after the "build_rig" is done in all modules.
        """
        self.chest.set_parent_uuid(uuid=self.chest.get_meta_parent_uuid())
        super().build_skeleton_hierarchy()  # Passthrough
        self.chest.clear_parent_uuid()

    def build_rig(self, **kwargs):
        # Get Elements ------------------------------------------------------------------------------------
        direction_crv = find_direction_curve()
        hip_jnt = find_joint_from_uuid(self.hip.get_uuid())
        chest_jnt = find_joint_from_uuid(self.chest.get_uuid())
        middle_jnt_list = []
        for proxy in self.spines:
            mid_jnt = find_joint_from_uuid(proxy.get_uuid())
            if mid_jnt:
                middle_jnt_list.append(mid_jnt)
        spine_jnt_list = [hip_jnt] + middle_jnt_list + [chest_jnt]

        module_jnt_list = [hip_jnt]
        module_jnt_list.extend(middle_jnt_list)
        module_jnt_list.append(chest_jnt)
        # Get Formatted Prefix
        _prefix = ''
        if self.prefix:
            _prefix = f'{self.prefix}_'
        setup_name = self.get_meta_setup_name()
        prefixed_setup_name = setup_name
        if _prefix:
            prefixed_setup_name = f'{_prefix}{setup_name}'
        # Get Setup Groups
        spine_automation_grp = get_automation_group(f'spineAutomation_{NamingConstants.Suffix.GRP}')
        spine_line_grp = f'{prefixed_setup_name}_lines_{NamingConstants.Suffix.GRP}'
        spine_line_grp = create_group(name=spine_line_grp)
        hierarchy_utils.parent(source_objects=spine_line_grp, target_parent=spine_automation_grp)

        # Set Joint Colors  -------------------------------------------------------------------------------
        set_color_viewport(obj_list=module_jnt_list, rgb_color=ColorConstants.RigJoint.GENERAL)

        # Get General Scale
        spine_scale = dist_center_to_center(hip_jnt, chest_jnt)

        joint_automation_grp = find_or_create_joint_automation_group()
        module_parent_jnt = get_driven_joint(self.get_parent_uuid())
        hierarchy_utils.parent(source_objects=module_parent_jnt, target_parent=joint_automation_grp)

        # Create Automation Skeletons (FK/IK/LimitQuery) ------------------------------------------------------------
        hip_parent = module_parent_jnt
        if module_parent_jnt:
            set_color_viewport(obj_list=hip_parent, rgb_color=ColorConstants.RigJoint.AUTOMATION)
            rescale_joint_radius(joint_list=hip_parent, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_DRIVEN)
        else:
            hip_parent = joint_automation_grp

        # FK
        suffix = NamingConstants.Description.FK
        hip_fk = duplicate_joint_for_automation(hip_jnt, suffix=suffix, parent=hip_parent)
        fk_joints = [hip_fk]
        last_mid_parent = hip_fk
        mid_fk_list = []
        for mid in middle_jnt_list:
            mid_fk = duplicate_joint_for_automation(mid, suffix=suffix, parent=last_mid_parent)
            mid_fk_list.append(mid_fk)
            last_mid_parent = mid_fk
        fk_joints.extend(mid_fk_list)
        chest_fk = duplicate_joint_for_automation(chest_jnt, suffix=suffix, parent=last_mid_parent)
        fk_joints.append(chest_fk)
        rescale_joint_radius(joint_list=fk_joints, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_FK)
        set_color_viewport(obj_list=fk_joints, rgb_color=ColorConstants.RigJoint.FK)
        set_color_outliner(obj_list=fk_joints, rgb_color=ColorConstants.RigOutliner.FK)

        # IK
        suffix = NamingConstants.Description.IK
        hip_ik = duplicate_joint_for_automation(hip_jnt, suffix=suffix, parent=hip_parent)
        ik_joints = [hip_ik]
        last_mid_parent = hip_ik
        mid_ik_list = []
        for mid in middle_jnt_list:
            mid_ik = duplicate_joint_for_automation(mid, suffix=suffix, parent=last_mid_parent)
            mid_ik_list.append(mid_ik)
            last_mid_parent = mid_ik
        ik_joints.extend(mid_ik_list)
        chest_ik = duplicate_joint_for_automation(chest_jnt, suffix=suffix, parent=last_mid_parent)
        ik_joints.append(chest_ik)
        rescale_joint_radius(joint_list=ik_joints, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_IK)
        set_color_viewport(obj_list=ik_joints, rgb_color=ColorConstants.RigJoint.IK)
        set_color_outliner(obj_list=ik_joints, rgb_color=ColorConstants.RigOutliner.IK)

        # Limit Chain
        suffix = "limitQuery"
        hip_limit = duplicate_joint_for_automation(hip_jnt, suffix=suffix, parent=hip_parent)
        limit_joints = [hip_limit]
        last_mid_parent = hip_limit
        mid_limit_list = []
        for mid in middle_jnt_list:
            mid_limit = duplicate_joint_for_automation(mid, suffix=suffix, parent=last_mid_parent)
            mid_limit_list.append(mid_limit)
            last_mid_parent = mid_limit
        limit_joints.extend(mid_limit_list)
        chest_limit = duplicate_joint_for_automation(chest_jnt, suffix=suffix, parent=last_mid_parent)
        limit_joints.append(chest_limit)
        rescale_joint_radius(joint_list=limit_joints, multiplier=RiggerConstants.LOC_RADIUS_MULTIPLIER_DATA_QUERY)
        set_color_viewport(obj_list=limit_joints, rgb_color=ColorConstants.RigJoint.DATA_QUERY)
        set_color_outliner(obj_list=limit_joints, rgb_color=ColorConstants.RigOutliner.DATA_QUERY)
        constraint_targets(source_driver=hip_jnt, target_driven=hip_limit)

        # COG Control ------------------------------------------------------------------------------------
        cog_ctrl_name = self.get_metadata_value(key=self.META_COG_NAME)
        cog_ctrl = self._assemble_ctrl_name(name=cog_ctrl_name)
        cog_ctrl = create_ctrl_curve(name=cog_ctrl, curve_file_name="_circle_pos_x")
        self._add_driver_uuid_attr(target_driver=cog_ctrl, driver_type=RiggerDriverTypes.COG, proxy_purpose=self.hip)
        cog_offset = add_offset_transform(target_list=cog_ctrl)[0]
        match_transform(source=hip_jnt, target_list=cog_offset)
        _cog_scale = spine_scale * .5
        scale_shapes(obj_transform=cog_ctrl, offset=_cog_scale)
        offset_control_orientation(ctrl=cog_ctrl, offset_transform=cog_offset, orient_tuple=(-90, -90, 0))
        hierarchy_utils.parent(source_objects=cog_offset, target_parent=direction_crv)
        # Attributes
        set_attr_state(attribute_path=f"{cog_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=cog_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        hide_lock_default_attrs(obj_list=cog_ctrl, scale=True, visibility=True)
        expose_rotation_order(cog_ctrl)
        set_curve_width(obj_list=cog_ctrl, line_width=2)

        # COG Offset Ctrl
        cog_o_ctrl = self._assemble_ctrl_name(name=cog_ctrl_name,
                                              overwrite_suffix=NamingConstants.Control.OFFSET_CTRL)
        cog_o_ctrl = create_ctrl_curve(name=cog_o_ctrl, curve_file_name="_circle_pos_x")
        match_transform(source=cog_ctrl, target_list=cog_o_ctrl)
        scale_shapes(obj_transform=cog_o_ctrl, offset=_cog_scale*0.9)
        rotate_shapes(obj_transform=cog_o_ctrl, offset=(90, 0, 90))  # Undo rotate offset
        set_color_viewport(obj_list=cog_o_ctrl, rgb_color=ColorConstants.RigJoint.OFFSET)
        hierarchy_utils.parent(source_objects=cog_o_ctrl, target_parent=cog_ctrl)
        # COG Offset Data Transform
        cog_o_data = self._assemble_ctrl_name(name=cog_ctrl_name,
                                              overwrite_suffix=NamingConstants.Control.OFFSET_DATA)
        cog_o_data = create_group(name=cog_o_data)
        connect_supporting_driver(source_driver=cog_ctrl,
                                  target_support_driver=cog_o_ctrl,
                                  support_driver_data=cog_o_data)
        hierarchy_utils.parent(source_objects=cog_o_data, target_parent=cog_ctrl)
        # Connections
        cmds.connectAttr(f'{cog_o_ctrl}.translate', f'{cog_o_data}.translate')
        cmds.connectAttr(f'{cog_o_ctrl}.rotate', f'{cog_o_data}.rotate')
        constraint_targets(source_driver=cog_o_data, target_driven=hip_fk)
        # Attributes
        set_attr_state(attribute_path=f"{cog_o_ctrl}.v", hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=cog_o_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        hide_lock_default_attrs(obj_list=cog_o_ctrl, scale=True)
        expose_rotation_order(cog_o_ctrl)
        cmds.addAttr(cog_ctrl, ln=RiggingConstants.ATTR_SHOW_OFFSET, at='bool', k=True)
        cmds.connectAttr(f'{cog_ctrl}.{RiggingConstants.ATTR_SHOW_OFFSET}', f'{cog_o_ctrl}.v')

        # Cog Movable Pivot (Rotate Pivot Ctrl) ------------------------------------------------------------
        cog_piv_data = self._assemble_ctrl_name(name=cog_ctrl_name,
                                                overwrite_suffix=NamingConstants.Control.PIVOT_CTRL)
        cog_piv_data = create_ctrl_curve(name=cog_piv_data, curve_file_name="_locator")

        # Aim Lines - Setup and Connections
        cog_piv_line_data = create_connection_line(object_a=cog_offset, object_b=cog_piv_data, line_width=3)
        cog_piv_aim_crv = cog_piv_line_data[0]
        hierarchy_utils.parent(source_objects=cog_piv_line_data, target_parent=spine_line_grp)
        hierarchy_utils.parent(source_objects=spine_line_grp, target_parent=spine_automation_grp)
        cmds.setAttr(f'{cog_piv_aim_crv}.inheritsTransform', 0)  # So it can be parented to control
        cmds.setAttr(f'{cog_piv_aim_crv}.overrideEnabled', 1)  # Enable Modes (So it can be seen as template)
        cmds.setAttr(f'{cog_piv_aim_crv}.overrideDisplayType', 1)  # Template
        hierarchy_utils.parent(source_objects=cog_piv_aim_crv, target_parent=cog_piv_data)
        match_transform(source=cog_ctrl, target_list=cog_piv_data)
        scale_shapes(obj_transform=cog_piv_data, offset=spine_scale * 0.7)
        set_curve_width(obj_list=cog_piv_data, line_width=3)
        self._add_driver_uuid_attr(target_driver=cog_piv_data,
                                   driver_type=RiggerDriverTypes.PIVOT,
                                   proxy_purpose=self.hip)
        hierarchy_utils.parent(source_objects=cog_piv_data, target_parent=cog_ctrl)
        cmds.connectAttr(f'{cog_piv_data}.translate', f'{cog_ctrl}.rotatePivot')
        hide_lock_default_attrs(obj_list=cog_piv_data, rotate=True, scale=True)
        add_attr(obj_list=cog_ctrl, attributes=RiggingConstants.ATTR_SHOW_PIVOT, attr_type="bool")
        connect_attr(source_attr=f'{cog_ctrl}.{RiggingConstants.ATTR_SHOW_PIVOT}',
                     target_attr_list=[f'{cog_piv_data}.v'])
        set_attr_state(attribute_path=f'{cog_piv_data}.v', hidden=True)
        set_color_viewport(obj_list=cog_piv_data, rgb_color=ColorConstants.RigControl.PIVOT)

        # Hip Control ----------------------------------------------------------------------------------
        hip_ctrl = self._assemble_ctrl_name(name=self.hip.get_name())
        hip_ctrl = create_ctrl_curve(name=hip_ctrl, curve_file_name="_wavy_circle_pos_x")
        self._add_driver_uuid_attr(target_driver=hip_ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=self.hip)
        hip_offset = add_offset_transform(target_list=hip_ctrl)[0]
        match_transform(source=hip_jnt, target_list=hip_offset)
        scale_shapes(obj_transform=hip_ctrl, offset=spine_scale / 6)
        offset_control_orientation(ctrl=hip_ctrl, offset_transform=hip_offset, orient_tuple=(-90, -90, 0))
        hierarchy_utils.parent(source_objects=hip_offset, target_parent=cog_o_data)
        # Attributes
        set_attr_state(attribute_path=f"{hip_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=hip_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        hide_lock_default_attrs(obj_list=hip_ctrl, scale=True)
        expose_rotation_order(hip_ctrl)
        add_limit_lock_translate_setup(target=hip_ctrl)

        # Hip Offset Ctrl
        hip_o_ctrl = self._assemble_ctrl_name(name=self.hip.get_name(),
                                              overwrite_suffix=NamingConstants.Control.OFFSET_CTRL)
        hip_o_ctrl = create_ctrl_curve(name=hip_o_ctrl, curve_file_name="_wavy_circle_pos_x")
        match_transform(source=hip_ctrl, target_list=hip_o_ctrl)
        scale_shapes(obj_transform=hip_o_ctrl, offset=spine_scale / 7)
        rotate_shapes(obj_transform=hip_o_ctrl, offset=(90, 0, 90))  # Undo rotate offset
        set_color_viewport(obj_list=hip_o_ctrl, rgb_color=ColorConstants.RigJoint.OFFSET)
        hierarchy_utils.parent(source_objects=hip_o_ctrl, target_parent=hip_ctrl)
        # Hip Offset Data Transform
        hip_o_data = self._assemble_ctrl_name(name=self.hip.get_name(),
                                              overwrite_suffix=NamingConstants.Control.OFFSET_DATA)
        hip_o_data = create_group(name=hip_o_data)
        self._add_driver_uuid_attr(target_driver=hip_o_data,
                                   driver_type=RiggerDriverTypes.GENERIC,
                                   proxy_purpose=self.hip)
        connect_supporting_driver(source_driver=hip_ctrl,
                                  target_support_driver=hip_o_ctrl,
                                  support_driver_data=hip_o_data)
        hierarchy_utils.parent(source_objects=hip_o_data, target_parent=hip_ctrl)
        # Connections
        cmds.connectAttr(f'{hip_o_ctrl}.translate', f'{hip_o_data}.translate')
        cmds.connectAttr(f'{hip_o_ctrl}.rotate', f'{hip_o_data}.rotate')
        # Attributes
        set_attr_state(attribute_path=f"{hip_o_ctrl}.v", hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=hip_o_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        hide_lock_default_attrs(obj_list=hip_o_ctrl, scale=True)
        expose_rotation_order(hip_o_ctrl)
        cmds.addAttr(hip_ctrl, ln=RiggingConstants.ATTR_SHOW_OFFSET, at='bool', k=True)
        cmds.connectAttr(f'{hip_ctrl}.{RiggingConstants.ATTR_SHOW_OFFSET}', f'{hip_o_ctrl}.v')

        # Spine FK Controls ----------------------------------------------------------------------------------
        spine_ctrls = []
        last_mid_parent_ctrl = cog_o_data
        for spine_proxy, fk_jnt in zip(self.spines, mid_fk_list):
            spine_ctrl = self._assemble_ctrl_name(name=spine_proxy.get_name())
            spine_ctrl = create_ctrl_curve(name=spine_ctrl, curve_file_name="_cube")
            self._add_driver_uuid_attr(target_driver=spine_ctrl,
                                       driver_type=RiggerDriverTypes.FK,
                                       proxy_purpose=spine_proxy)
            spine_offset = add_offset_transform(target_list=spine_ctrl)[0]
            # Move Pivot to Base
            translate_shapes(obj_transform=spine_ctrl, offset=(1, 0, 0))
            # Define Shape Scale
            _shape_scale = (spine_scale / 20, spine_scale / 4, spine_scale / 3)
            child_joint = cmds.listRelatives(fk_jnt, fullPath=True, children=True, typ="joint")
            if child_joint:
                _distance = dist_center_to_center(obj_a=fk_jnt, obj_b=child_joint[0])
                _shape_height = _distance/4
                _shape_scale = _shape_height, _shape_scale[1], _shape_scale[2]
            scale_shapes(obj_transform=spine_ctrl, offset=_shape_scale)
            # Position and Constraint
            match_transform(source=fk_jnt, target_list=spine_offset)
            offset_control_orientation(ctrl=spine_ctrl, offset_transform=spine_offset, orient_tuple=(-90, -90, 0))
            hierarchy_utils.parent(source_objects=spine_offset, target_parent=last_mid_parent_ctrl)
            # Attributes
            set_attr_state(attribute_path=f"{spine_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
            add_separator_attr(target_object=spine_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
            hide_lock_default_attrs(spine_ctrl, scale=True)
            expose_rotation_order(spine_ctrl)
            spine_ctrls.append(spine_ctrl)
            constraint_targets(source_driver=spine_ctrl, target_driven=fk_jnt)
            last_mid_parent_ctrl = spine_ctrl

        # Chest FK Control --------------------------------------------------------------------------------
        chest_fk_ctrl = self._assemble_ctrl_name(name=self.chest.get_name())
        chest_fk_ctrl = create_ctrl_curve(name=chest_fk_ctrl, curve_file_name="_cube")
        self._add_driver_uuid_attr(target_driver=chest_fk_ctrl,
                                   driver_type=RiggerDriverTypes.FK,
                                   proxy_purpose=self.chest)
        chest_fk_offset = add_offset_transform(target_list=chest_fk_ctrl)[0]
        match_transform(source=chest_jnt, target_list=chest_fk_offset)
        translate_shapes(obj_transform=chest_fk_ctrl, offset=(1, 0, 0))  # Move Pivot to Base
        _shape_scale = (spine_scale / 4, spine_scale / 4, spine_scale / 3)
        scale_shapes(obj_transform=chest_fk_ctrl, offset=_shape_scale)
        offset_control_orientation(ctrl=chest_fk_ctrl, offset_transform=chest_fk_offset, orient_tuple=(-90, -90, 0))
        chest_ctrl_parent = spine_ctrls[-1] if spine_ctrls else cog_o_data  # Same as "last_mid_parent_ctrl"
        hierarchy_utils.parent(source_objects=chest_fk_offset, target_parent=chest_ctrl_parent)
        constraint_targets(source_driver=chest_fk_ctrl, target_driven=chest_fk)
        # Attributes
        set_attr_state(attribute_path=f"{chest_fk_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=chest_fk_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        expose_rotation_order(chest_fk_ctrl)

        # Chest Ribbon (IK) Control -----------------------------------------------------------------------
        chest_ik_ctrl = self._assemble_ctrl_name(name=self.chest.get_name(),
                                                 overwrite_suffix=NamingConstants.Control.IK_CTRL)
        chest_ik_ctrl = duplicate_object(obj=chest_fk_ctrl, name=chest_ik_ctrl)
        self._add_driver_uuid_attr(target_driver=chest_ik_ctrl,
                                   driver_type=RiggerDriverTypes.IK,
                                   proxy_purpose=self.chest)
        chest_ik_offset = add_offset_transform(target_list=chest_ik_ctrl)[0]
        hierarchy_utils.parent(source_objects=chest_ik_offset, target_parent=cog_o_data)
        add_separator_attr(target_object=chest_ik_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        hide_lock_default_attrs(chest_ik_ctrl, scale=True, visibility=True)
        expose_rotation_order(chest_ik_ctrl)

        # Chest Ribbon (IK) Offset Ctrl --------------------------------------------------------------------
        chest_o_ik_ctrl = self._assemble_ctrl_name(name=self.chest.get_name(),
                                                   overwrite_suffix=NamingConstants.Control.IK_O_CTRL)
        chest_o_ik_ctrl = create_ctrl_curve(name=chest_o_ik_ctrl, curve_file_name="_cube")
        match_transform(source=chest_fk_ctrl, target_list=chest_o_ik_ctrl)
        translate_shapes(obj_transform=chest_o_ik_ctrl, offset=(1.1, 0, 0))  # Move Pivot Slightly below base
        scale_shapes(obj_transform=chest_o_ik_ctrl, offset=_shape_scale)
        scale_shapes(obj_transform=chest_o_ik_ctrl, offset=.9)
        rotate_shapes(obj_transform=chest_o_ik_ctrl, offset=(90, 0, 90))  # Undo rotate offset
        set_color_viewport(obj_list=chest_o_ik_ctrl, rgb_color=ColorConstants.RigJoint.OFFSET)
        hierarchy_utils.parent(source_objects=chest_o_ik_ctrl, target_parent=chest_ik_ctrl)
        # Chest Offset Data Transform
        chest_o_ik_data = self._assemble_ctrl_name(name=self.chest.get_name(),
                                                   overwrite_suffix=NamingConstants.Control.OFFSET_DATA)
        chest_o_ik_data = create_group(name=chest_o_ik_data)
        connect_supporting_driver(source_driver=chest_ik_ctrl,
                                  target_support_driver=chest_o_ik_ctrl,
                                  support_driver_data=chest_o_ik_data)
        hierarchy_utils.parent(source_objects=chest_o_ik_data, target_parent=chest_ik_ctrl)
        # Connections
        cmds.connectAttr(f'{chest_o_ik_ctrl}.translate', f'{chest_o_ik_data}.translate')
        cmds.connectAttr(f'{chest_o_ik_ctrl}.rotate', f'{chest_o_ik_data}.rotate')
        # Attributes
        set_attr_state(attribute_path=f"{chest_o_ik_ctrl}.v", hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=chest_o_ik_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        hide_lock_default_attrs(chest_o_ik_ctrl, scale=True)
        expose_rotation_order(chest_o_ik_ctrl)
        cmds.addAttr(chest_ik_ctrl, ln=RiggingConstants.ATTR_SHOW_OFFSET, at='bool', k=True)
        cmds.connectAttr(f'{chest_ik_ctrl}.{RiggingConstants.ATTR_SHOW_OFFSET}', f'{chest_o_ik_ctrl}.v')

        # Chest Movable Pivot (Rotate Pivot Ctrl) ------------------------------------------------------------
        chest_piv_ik_data = self._assemble_ctrl_name(name=self.chest.get_name(),
                                                     overwrite_suffix=NamingConstants.Control.PIVOT_CTRL)
        chest_piv_ik_data = create_ctrl_curve(name=chest_piv_ik_data, curve_file_name="_locator")

        # Aim Lines - Setup and Connections
        piv_line_data = create_connection_line(object_a=chest_ik_offset, object_b=chest_piv_ik_data, line_width=3)
        piv_aim_crv = piv_line_data[0]
        hierarchy_utils.parent(source_objects=piv_line_data, target_parent=spine_line_grp)
        cmds.setAttr(f'{piv_aim_crv}.inheritsTransform', 0)  # So it can be parented to control
        cmds.setAttr(f'{piv_aim_crv}.overrideEnabled', 1)  # Enable Modes (So it can be seen as template)
        cmds.setAttr(f'{piv_aim_crv}.overrideDisplayType', 1)  # Template
        hierarchy_utils.parent(source_objects=piv_aim_crv, target_parent=chest_piv_ik_data)
        match_transform(source=chest_ik_ctrl, target_list=chest_piv_ik_data)
        scale_shapes(obj_transform=chest_piv_ik_data, offset=spine_scale * 0.7)
        set_curve_width(obj_list=chest_piv_ik_data, line_width=3)
        self._add_driver_uuid_attr(target_driver=chest_piv_ik_data,
                                   driver_type=RiggerDriverTypes.PIVOT,
                                   proxy_purpose=self.chest)
        hierarchy_utils.parent(source_objects=chest_piv_ik_data, target_parent=chest_ik_ctrl)
        cmds.connectAttr(f'{chest_piv_ik_data}.translate', f'{chest_ik_ctrl}.rotatePivot')
        hide_lock_default_attrs(obj_list=chest_piv_ik_data, rotate=True, scale=True)
        add_attr(obj_list=chest_ik_ctrl, attributes=RiggingConstants.ATTR_SHOW_PIVOT, attr_type="bool")
        connect_attr(source_attr=f'{chest_ik_ctrl}.{RiggingConstants.ATTR_SHOW_PIVOT}',
                     target_attr_list=[f'{chest_piv_ik_data}.v'])
        set_attr_state(attribute_path=f'{chest_piv_ik_data}.v', hidden=True)
        set_color_viewport(obj_list=chest_piv_ik_data, rgb_color=ColorConstants.RigControl.PIVOT)

        # IK Spine (Ribbon) -----------------------------------------------------------------------------------
        spine_ribbon_grp = f'{prefixed_setup_name}_ribbon_{NamingConstants.Suffix.GRP}'
        spine_ribbon_grp = create_group(name=spine_ribbon_grp)
        cmds.setAttr(f'{spine_ribbon_grp}.inheritsTransform', 0)  # Ignore Hierarchy Transform

        ribbon_sur = self._assemble_ctrl_name(name="spineRibbon", overwrite_suffix=NamingConstants.Suffix.SUR)
        ribbon_sur = create_surface_from_object_list(obj_list=spine_jnt_list,
                                                     surface_name=ribbon_sur,
                                                     custom_normal=(0, 0, 1))
        hierarchy_utils.parent(source_objects=ribbon_sur, target_parent=spine_ribbon_grp)

        # Create Follicles
        follicle_transforms = []
        for index, joint in enumerate(spine_jnt_list):
            if index == 0 or index == len(spine_jnt_list)-1:  # Skip Hip and Chest
                continue
            joint_pos = cmds.xform(joint, query=True, translation=True, worldSpace=True)
            u_pos, v_pos = get_closest_uv_point(surface=ribbon_sur, xyz_pos=joint_pos)
            v_pos_normalized = v_pos/(len(spine_jnt_list)-1)
            fol_trans, fol_shape = create_follicle(input_surface=ribbon_sur,
                                                   uv_position=(u_pos, v_pos_normalized),
                                                   name=f"{_prefix}spineFollicle_{(index + 1):02d}")
            follicle_transforms.append(fol_trans)
        hierarchy_utils.parent(source_objects=follicle_transforms, target_parent=spine_ribbon_grp)

        # Create Limit Query IK Handle ------------------------------------------------------------------------
        ik_limit_handle = self._assemble_ctrl_name(name="spineLimit",
                                                   overwrite_suffix=NamingConstants.Suffix.IK_HANDLE_SC)
        ik_limit_handle = cmds.ikHandle(name=ik_limit_handle, solver='ikSCsolver',
                                        startJoint=limit_joints[0], endEffector=limit_joints[-1])[0]
        ik_limit_handle = Node(ik_limit_handle)
        constraint_targets(source_driver=chest_o_ik_data, target_driven=ik_limit_handle)

        # Constraints -----------------------------------------------------------------------------------------
        # Constraints FK -> Base
        for fk_jnt, base_jnt in zip(fk_joints, module_jnt_list):
            constraint_targets(source_driver=fk_jnt, target_driven=base_jnt)
        # Constraints Follicle -> IK
        for spine_fol, ik_jnt in zip(follicle_transforms, mid_ik_list):
            constraint_targets(source_driver=spine_fol, target_driven=ik_jnt)

        # Create Switch Setup ---------------------------------------------------------------------------------
        fk_controls = [chest_fk_ctrl] + spine_ctrls
        add_separator_attr(target_object=cog_ctrl, attr_name=RiggingConstants.SEPARATOR_SWITCH)
        create_switch_setup(source_a=fk_joints, source_b=ik_joints, target_base=module_jnt_list, attr_holder=cog_ctrl,
                            visibility_a=fk_controls, visibility_b=[chest_ik_ctrl, chest_o_ik_ctrl, chest_piv_ik_data],
                            prefix=_prefix)
        cmds.setAttr(f'{cog_ctrl}.{RiggingConstants.ATTR_INFLUENCE_SWITCH}', 0)  # Default is IK

        # Create Squash Stretch System (limitQuery) -----------------------------------------------------------
        add_separator_attr(target_object=chest_ik_ctrl, attr_name='squashStretch')
        stretchy_grp = create_stretchy_ik_setup(ik_handle=ik_limit_handle,
                                                attribute_holder=chest_ik_ctrl,
                                                prefix=prefixed_setup_name)
        hierarchy_utils.parent(source_objects=ik_limit_handle, target_parent=spine_ribbon_grp)
        hierarchy_utils.parent(source_objects=[stretchy_grp, spine_ribbon_grp], target_parent=spine_automation_grp)
        end_loc, start_loc = cmds.listConnections(f'{stretchy_grp}.message')

        # Setup Ribbon Limit Query Logic ----------------------------------------------------------------------
        last_limit_query_jnt = limit_joints[-1]
        # Redirect Stretchy System Term Driver
        for child in cmds.listRelatives(end_loc, children=True, typ="pointConstraint") or []:
            cmds.delete(child)
        constraint_targets(source_driver=chest_o_ik_data, target_driven=end_loc,
                           maintain_offset=False, constraint_type=ConstraintTypes.POINT)

        # Spine IK Control ----------------------------------------------------------------------------------
        temp_fol_trans, _ = create_follicle(input_surface=ribbon_sur,
                                            uv_position=(0.5, 0.5),
                                            name=f"{_prefix}tempFollicle")
        spine_ik_ctrl = self._assemble_ctrl_name(name=f'{setup_name}_ik')
        spine_ik_ctrl = create_ctrl_curve(name=spine_ik_ctrl, curve_file_name="_cube")
        connect_supporting_driver(source_driver=chest_ik_ctrl,
                                  target_support_driver=spine_ik_ctrl)
        spine_ik_offset = add_offset_transform(target_list=spine_ik_ctrl)[0]
        spine_ik_hip_chest_data = add_offset_transform(target_list=spine_ik_ctrl)[0]
        spine_ik_hip_chest_name = self._assemble_ctrl_name(name=f'{setup_name}_ik', overwrite_suffix="hipChestData")
        spine_ik_hip_chest_data.rename(spine_ik_hip_chest_name)
        set_equidistant_transforms(start=chest_ik_ctrl, end=cog_ctrl, target_list=spine_ik_offset)
        match_translate(source=temp_fol_trans, target_list=spine_ik_offset)
        cmds.delete(temp_fol_trans)
        # Scale
        _shape_scale = (spine_scale / 3, spine_scale / 10, spine_scale / 4)
        scale_shapes(obj_transform=spine_ik_ctrl, offset=_shape_scale)
        # Attributes
        set_attr_state(attribute_path=f"{spine_ik_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=spine_ik_ctrl, attr_name=RiggingConstants.SEPARATOR_CONTROL)
        hide_lock_default_attrs(spine_ik_ctrl, scale=True)
        expose_rotation_order(spine_ik_ctrl)
        hierarchy_utils.parent(source_objects=spine_ik_offset, target_parent=cog_o_data)

        # Ribbon Driver Joints
        hip_ribbon_jnt = f'{self.hip.get_name()}_{NamingConstants.Description.RIBBON}_{NamingConstants.Suffix.JNT}'
        hip_ribbon_jnt = duplicate_object(obj=hip_jnt, name=hip_ribbon_jnt)
        match_transform(source=cog_ctrl, target_list=hip_ribbon_jnt)

        spine_ribbon_jnt = f'{setup_name}_{NamingConstants.Description.RIBBON}_{NamingConstants.Suffix.JNT}'
        spine_ribbon_jnt = duplicate_object(obj=hip_ribbon_jnt, name=spine_ribbon_jnt)
        match_transform(source=spine_ik_ctrl, target_list=spine_ribbon_jnt)

        chest_ribbon_jnt = f'{self.chest.get_name()}_{NamingConstants.Description.RIBBON}_{NamingConstants.Suffix.JNT}'
        chest_ribbon_jnt = duplicate_object(obj=chest_jnt, name=chest_ribbon_jnt)
        match_transform(source=chest_ik_ctrl, target_list=chest_ribbon_jnt)

        # Attach Extremities (Skipped when creating follicles)
        constraint_targets(source_driver=hip_ribbon_jnt, target_driven=hip_ik)
        constraint_targets(source_driver=chest_ribbon_jnt, target_driven=chest_ik)

        # Connect Ribbon Controls and Joints
        constraint_targets(source_driver=[hip_ribbon_jnt, chest_ribbon_jnt], target_driven=spine_ik_hip_chest_data)
        ribbon_driver_joints = [hip_ribbon_jnt, spine_ribbon_jnt, chest_ribbon_jnt]
        set_joint_radius(joints=ribbon_driver_joints, radius=spine_scale * .1)
        set_color_viewport(obj_list=ribbon_driver_joints, rgb_color=ColorConstants.RigJoint.AUTOMATION)
        dropoff_rate = self.get_metadata_value(key=self.META_DROPOFF_RATE)
        ribbon_skin_cluster = cmds.skinCluster(ribbon_driver_joints, ribbon_sur,
                                               dropoffRate=dropoff_rate,
                                               nurbsSamples=15,
                                               bindMethod=0,  # Closest Distance
                                               name=f"{_prefix}spineRibbon_skinCluster")[0]

        constraint_targets(source_driver=cog_o_data, target_driven=hip_ribbon_jnt)
        constraint_targets(source_driver=spine_ik_ctrl, target_driven=spine_ribbon_jnt)
        constraint_targets(source_driver=chest_o_ik_data, target_driven=chest_ribbon_jnt,
                           constraint_type=ConstraintTypes.ORIENT)
        constraint_targets(source_driver=last_limit_query_jnt, target_driven=chest_ribbon_jnt,
                           constraint_type=ConstraintTypes.POINT)

        spine_ik_ctrl_shape = cmds.listRelatives(spine_ik_ctrl, shapes=True, fullPath=True)[0]
        connect_attr(source_attr=f'{cog_ctrl}.visibilityB', target_attr_list=f'{spine_ik_ctrl_shape}.v')
        set_color_viewport(obj_list=spine_ik_ctrl, rgb_color=ColorConstants.RigControl.CENTER)
        hierarchy_utils.parent(source_objects=ribbon_driver_joints, target_parent=joint_automation_grp)

        # Follow Hip and Chest Attribute
        add_attr(obj_list=spine_ik_ctrl, attributes="followHipAndChest", default=1, minimum=0, maximum=1)
        follow_constraint = constraint_targets(source_driver=spine_ik_offset, target_driven=spine_ik_hip_chest_data)[0]
        spine_follow_reverse_node = create_node('reverse', name='spine_midRibbonFollow_reverse')
        cmds.connectAttr(f'{spine_ik_ctrl}.followHipAndChest', spine_follow_reverse_node + '.inputX')
        cmds.connectAttr(f'{spine_ik_ctrl}.followHipAndChest', f'{follow_constraint}.w0')  # Hip
        cmds.connectAttr(f'{spine_ik_ctrl}.followHipAndChest', f'{follow_constraint}.w1')  # Chest
        cmds.connectAttr(f'{spine_follow_reverse_node}.outputX', f'{follow_constraint}.w2')  # Offset (No Automation)

        # Set Initial Chest Pivot to Spine Control ---------------------------------------------------------
        match_translate(source=spine_ik_ctrl, target_list=chest_piv_ik_data)

        # Chest Driven Group (For Parented Controls) -------------------------------------------------------
        chest_driven = self._assemble_ctrl_name(name=self.chest.get_name(),
                                                overwrite_suffix=NamingConstants.Suffix.DRIVER)
        chest_driven = create_group(name=chest_driven)
        self._add_driver_uuid_attr(target_driver=chest_driven,
                                   driver_type=RiggerDriverTypes.GENERIC,
                                   proxy_purpose=self.chest)
        constraint_targets(source_driver=chest_jnt, target_driven=chest_driven, maintain_offset=False)
        hierarchy_utils.parent(source_objects=chest_driven, target_parent=cog_o_data)

        # Outliner Clean-up --------------------------------------------------------------------------------
        reorder_front(target_list=joint_automation_grp)
        # Set Automation Visibility
        cmds.setAttr(f'{spine_automation_grp}.v', 0)
        cmds.setAttr(f'{joint_automation_grp}.v', 0)

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [cog_offset]

    # ------------------------------------------- Extra Module Setters -------------------------------------------
    def set_ribbon_dropoff_rate(self, rate):
        """
        Sets the foot control name by editing the metadata value associated with it.
        Args:
            rate (int, float): Dropoff rate for the ribbon controls. Range 0.1 to 10.0
        """
        if not (0.1 <= rate <= 10.0):
            logger.warning("Dropoff rate must be between 0.1 and 10.0")
            return

        self.add_to_metadata(self.META_DROPOFF_RATE, value=rate)

    def set_cog_ctrl_name(self, name):
        """
        Sets the cog (center of gravity) control name by editing the metadata value associated with it.
        Args:
            name (str): New name for the cog control. If empty the default name will be used instead.
        """
        self.add_to_metadata(self.META_COG_NAME, value=name if name else self.DEFAULT_COG_NAME)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.utils.session_utils import remove_modules_startswith
    remove_modules_startswith("gt.tools.auto_rigger.module")
    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject
    from gt.tools.auto_rigger.module_root import ModuleRoot
    from gt.tools.auto_rigger.module_biped_arm import ModuleBipedArmRight
    a_arm_rt = ModuleBipedArmRight()
    a_root = ModuleRoot()
    a_spine = ModuleSpine()
    # a_spine.set_spine_num(0)
    a_spine.set_spine_num(6)
    a_spine.set_parent_uuid(a_root.root.get_uuid())
    a_project = RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_spine)
    a_project.add_to_modules(a_arm_rt)

    spine_chest_uuid = a_spine.chest.get_uuid()
    a_arm_rt.set_parent_uuid(spine_chest_uuid)

    a_project.build_proxy()
    #
    # cmds.setAttr(f'hip.tx', 10)
    # cmds.setAttr(f'spine02.tx', 10)

    a_project.read_data_from_scene()
    dictionary = a_project.get_project_as_dict()

    cmds.file(new=True, force=True)
    a_project2 = RigProject()
    a_project2.read_data_from_dict(dictionary)
    a_project2.build_proxy()
    a_project2.build_rig()

    # Show all
    cmds.viewFit(all=True)
