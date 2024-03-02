"""
Auto Rigger Spine Modules
github.com/TrevisanGMW/gt-tools
"""
from gt.tools.auto_rigger.rig_utils import find_or_create_joint_automation_group, get_driven_joint, create_ctrl_curve
from gt.tools.auto_rigger.rig_utils import find_proxy_from_uuid, find_direction_curve, find_joint_from_uuid
from gt.tools.auto_rigger.rig_utils import get_automation_group
from gt.utils.transform_utils import Vector3, scale_shapes, match_transform, translate_shapes, rotate_shapes
from gt.utils.rigging_utils import expose_rotation_order, offset_control_orientation, rescale_joint_radius
from gt.utils.rigging_utils import duplicate_joint_for_automation, create_stretchy_ik_setup
from gt.utils.surface_utils import create_surface_from_object_list, create_follicle, get_closest_uv_point
from gt.utils.color_utils import ColorConstants, set_color_viewport, set_color_outliner
from gt.tools.auto_rigger.rig_framework import Proxy, ModuleGeneric, OrientationData
from gt.tools.auto_rigger.rig_constants import RiggerConstants, RiggerDriverTypes
from gt.utils.constraint_utils import equidistant_constraints, constraint_targets
from gt.utils.attr_utils import add_separator_attr, set_attr_state
from gt.tools.auto_rigger.rig_utils import get_proxy_offset
from gt.utils.hierarchy_utils import add_offset_transform
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


class ModuleSpine(ModuleGeneric):
    __version__ = '0.0.3-alpha'
    icon = resource_library.Icon.rigger_module_spine
    allow_parenting = True

    # Default Values
    DEFAULT_SETUP_NAME = "spine"

    def __init__(self, name="Spine", prefix=None, suffix=None):
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, 1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Extra Module Data
        self.set_meta_setup_name(name=self.DEFAULT_SETUP_NAME)

        # Hip (Base)
        self.hip = Proxy(name="hip")
        pos_hip = Vector3(y=84.5)
        self.hip.set_initial_position(xyz=pos_hip)
        self.hip.set_locator_scale(scale=1.5)
        self.hip.set_meta_purpose(value="hip")
        self.hip.add_driver_type(driver_type=[RiggerDriverTypes.OFFSET, RiggerDriverTypes.FK, RiggerDriverTypes.COG])

        # Chest (End)
        self.chest = Proxy(name="chest")
        pos_chest = Vector3(y=114.5)
        self.chest.set_initial_position(xyz=pos_chest)
        self.chest.set_locator_scale(scale=1.5)
        self.chest.set_meta_purpose(value="chest")
        self.chest.add_driver_type(driver_type=[RiggerDriverTypes.OFFSET, RiggerDriverTypes.FK])

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
                new_spine.add_driver_type(driver_type=[RiggerDriverTypes.FK])
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
        # module_parent_jnt = find_joint_from_uuid(self.get_parent_uuid())  # TODO TEMP @@@
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
        spine_automation_grp = get_automation_group(f'spineAutomation_{NamingConstants.Suffix.GRP}')
        # Get Formatted Prefix
        _prefix = ''
        if self.prefix:
            _prefix = f'{self.prefix}_'

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
        set_color_outliner(obj_list=ik_joints, rgb_color=ColorConstants.RigOutliner.DATA_QUERY)

        # COG Control ------------------------------------------------------------------------------------
        cog_ctrl = self._assemble_ctrl_name(name="cog")
        cog_ctrl = create_ctrl_curve(name=cog_ctrl, curve_file_name="_circle_pos_x")
        self.add_driver_uuid_attr(target=cog_ctrl, driver_type=RiggerDriverTypes.COG, proxy_purpose=self.hip)
        cog_offset = Node(add_offset_transform(target_list=cog_ctrl)[0])
        match_transform(source=hip_jnt, target_list=cog_offset)
        scale_shapes(obj_transform=cog_ctrl, offset=spine_scale * .4)
        offset_control_orientation(ctrl=cog_ctrl, offset_transform=cog_offset, orient_tuple=(-90, -90, 0))
        hierarchy_utils.parent(source_objects=cog_offset, target_parent=direction_crv)
        # Attributes
        set_attr_state(attribute_path=f"{cog_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=cog_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
        expose_rotation_order(cog_ctrl)
        constraint_targets(source_driver=cog_ctrl, target_driven=hip_fk)

        # Hip Control ----------------------------------------------------------------------------------
        hip_ctrl = self._assemble_ctrl_name(name=self.hip.get_name())
        hip_ctrl = create_ctrl_curve(name=hip_ctrl, curve_file_name="_wavy_circle_pos_x")
        self.add_driver_uuid_attr(target=hip_ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=self.hip)
        hip_offset = Node(add_offset_transform(target_list=hip_ctrl)[0])
        match_transform(source=hip_jnt, target_list=hip_offset)
        scale_shapes(obj_transform=hip_ctrl, offset=spine_scale / 6)
        offset_control_orientation(ctrl=hip_ctrl, offset_transform=hip_offset, orient_tuple=(-90, -90, 0))
        hierarchy_utils.parent(source_objects=hip_offset, target_parent=cog_ctrl)
        # Attributes
        set_attr_state(attribute_path=f"{hip_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=hip_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
        expose_rotation_order(hip_ctrl)

        # Hip Offset Ctrl
        hip_o_ctrl = self._assemble_ctrl_name(name=self.hip.get_name(),
                                             overwrite_suffix=NamingConstants.Suffix.OFFSET_CTRL)
        hip_o_ctrl = create_ctrl_curve(name=hip_o_ctrl, curve_file_name="_wavy_circle_pos_x")
        match_transform(source=hip_ctrl, target_list=hip_o_ctrl)
        scale_shapes(obj_transform=hip_o_ctrl, offset=spine_scale / 7)
        rotate_shapes(obj_transform=hip_o_ctrl, offset=(90, 0, 90))  # Undo rotate offset
        set_color_viewport(obj_list= hip_o_ctrl, rgb_color=ColorConstants.RigJoint.OFFSET)
        hierarchy_utils.parent(source_objects=hip_o_ctrl, target_parent=hip_ctrl)
        # Hip Offset Data Transform
        hip_o_data = self._assemble_ctrl_name(name=self.hip.get_name(),
                                               overwrite_suffix=NamingConstants.Suffix.OFFSET_DATA)
        hip_o_data = cmds.group(name=hip_o_data, empty=True, world=True)
        hip_o_data = Node(hip_o_data)
        self.add_driver_uuid_attr(target=hip_o_data,
                                  driver_type=RiggerDriverTypes.OFFSET,
                                  proxy_purpose=self.hip)
        hierarchy_utils.parent(source_objects=hip_o_data, target_parent=hip_ctrl)
        # Connections
        cmds.connectAttr(f'{hip_o_ctrl}.translate', f'{hip_o_data}.translate')
        cmds.connectAttr(f'{hip_o_ctrl}.rotate', f'{hip_o_data}.rotate')
        # Attributes
        set_attr_state(attribute_path=f"{hip_o_ctrl}.v", hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=hip_o_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
        expose_rotation_order(hip_o_ctrl)
        cmds.addAttr(hip_ctrl, ln=RiggerConstants.ATTR_SHOW_OFFSET, at='bool', k=True)
        cmds.connectAttr(f'{hip_ctrl}.{RiggerConstants.ATTR_SHOW_OFFSET}', f'{hip_o_ctrl}.v')

        # FK Controls ----------------------------------------------------------------------------------
        spine_ctrls = []
        last_mid_parent_ctrl = cog_ctrl
        for spine_proxy, fk_jnt in zip(self.spines, mid_fk_list):
            spine_ctrl = self._assemble_ctrl_name(name=spine_proxy.get_name())
            spine_ctrl = create_ctrl_curve(name=spine_ctrl, curve_file_name="_cube")
            self.add_driver_uuid_attr(target=spine_ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=spine_proxy)
            spine_offset = Node(add_offset_transform(target_list=spine_ctrl)[0])
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
            add_separator_attr(target_object=spine_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
            expose_rotation_order(spine_ctrl)
            spine_ctrls.append(spine_ctrl)
            constraint_targets(source_driver=spine_ctrl, target_driven=fk_jnt)
            last_mid_parent_ctrl = spine_ctrl

        # Chest Control --------------------------------------------------------------------------------
        chest_ctrl = self._assemble_ctrl_name(name=self.chest.get_name())
        chest_ctrl = create_ctrl_curve(name=chest_ctrl, curve_file_name="_cube")
        self.add_driver_uuid_attr(target=chest_ctrl, driver_type=RiggerDriverTypes.FK, proxy_purpose=self.chest)
        chest_offset = Node(add_offset_transform(target_list=chest_ctrl)[0])
        match_transform(source=chest_jnt, target_list=chest_offset)
        translate_shapes(obj_transform=chest_ctrl, offset=(1, 0, 0))  # Move Pivot to Base
        _shape_scale = (spine_scale / 4, spine_scale / 4, spine_scale / 3)
        scale_shapes(obj_transform=chest_ctrl, offset=_shape_scale)
        offset_control_orientation(ctrl=chest_ctrl, offset_transform=chest_offset, orient_tuple=(-90, -90, 0))
        chest_ctrl_parent = spine_ctrls[-1] if spine_ctrls else cog_ctrl  # Same as "last_mid_parent_ctrl"
        hierarchy_utils.parent(source_objects=chest_offset, target_parent=chest_ctrl_parent)
        # Attributes
        set_attr_state(attribute_path=f"{chest_ctrl}.v", locked=True, hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=chest_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
        expose_rotation_order(chest_ctrl)

        # Chest Offset Ctrl
        chest_o_ctrl = self._assemble_ctrl_name(name=self.chest.get_name(),
                                                overwrite_suffix=NamingConstants.Suffix.OFFSET_CTRL)
        chest_o_ctrl = create_ctrl_curve(name=chest_o_ctrl, curve_file_name="_cube")
        match_transform(source=chest_ctrl, target_list=chest_o_ctrl)
        translate_shapes(obj_transform=chest_o_ctrl, offset=(1.1, 0, 0))  # Move Pivot Slightly below base
        scale_shapes(obj_transform=chest_o_ctrl, offset=_shape_scale)
        scale_shapes(obj_transform=chest_o_ctrl, offset=.9)
        rotate_shapes(obj_transform=chest_o_ctrl, offset=(90, 0, 90))  # Undo rotate offset
        set_color_viewport(obj_list=chest_o_ctrl, rgb_color=ColorConstants.RigJoint.OFFSET)
        hierarchy_utils.parent(source_objects=chest_o_ctrl, target_parent=chest_ctrl)
        # Chest Offset Data Transform
        chest_o_data = self._assemble_ctrl_name(name=self.chest.get_name(),
                                                overwrite_suffix=NamingConstants.Suffix.OFFSET_DATA)
        chest_o_data = cmds.group(name=chest_o_data, empty=True, world=True)
        chest_o_data = Node(chest_o_data)
        self.add_driver_uuid_attr(target=chest_o_data,
                                  driver_type=RiggerDriverTypes.OFFSET,
                                  proxy_purpose=self.chest)
        hierarchy_utils.parent(source_objects=chest_o_data, target_parent=chest_ctrl)
        # Connections
        cmds.connectAttr(f'{chest_o_ctrl}.translate', f'{chest_o_data}.translate')
        cmds.connectAttr(f'{chest_o_ctrl}.rotate', f'{chest_o_data}.rotate')
        constraint_targets(source_driver=chest_o_data, target_driven=chest_fk)
        # Attributes
        set_attr_state(attribute_path=f"{chest_o_ctrl}.v", hidden=True)  # Hide and Lock Visibility
        add_separator_attr(target_object=chest_o_ctrl, attr_name=RiggerConstants.SEPARATOR_CONTROL)
        expose_rotation_order(chest_o_ctrl)
        cmds.addAttr(chest_ctrl, ln=RiggerConstants.ATTR_SHOW_OFFSET, at='bool', k=True)
        cmds.connectAttr(f'{chest_ctrl}.{RiggerConstants.ATTR_SHOW_OFFSET}', f'{chest_o_ctrl}.v')

        # IK Spine (Ribbon) -----------------------------------------------------------------------------------
        spine_ik_grp = cmds.group(name=f'spineRibbon_{NamingConstants.Suffix.GRP}', empty=True, world=True)
        # hierarchy_utils.parent(source_objects=spine_ik_grp, target_parent=spine_automation_grp)
        cmds.setAttr(f'{spine_ik_grp}.inheritsTransform', 0)  # Ignore Hierarchy Transform

        ribbon_sur = self._assemble_ctrl_name(name="spineRibbon", overwrite_suffix=NamingConstants.Suffix.SUR)
        ribbon_sur = create_surface_from_object_list(obj_list=spine_jnt_list,
                                                     surface_name=ribbon_sur,
                                                     custom_normal=(0, 0, 1))
        hierarchy_utils.parent(source_objects=ribbon_sur, target_parent=spine_ik_grp)
        # Create Follicles
        follicle_nodes = []
        follicle_transforms = []
        for index, joint in enumerate(spine_jnt_list):
            joint_pos = cmds.xform(joint, query=True, translation=True, worldSpace=True)
            u_pos, v_pos = get_closest_uv_point(surface=ribbon_sur, xyz_pos=joint_pos)
            v_pos_normalized = v_pos/(len(spine_jnt_list)-1)
            fol_trans, fol_shape = create_follicle(input_surface=ribbon_sur,
                                                   uv_position=(u_pos, v_pos_normalized),
                                                   name=f"{_prefix}spineFollicle_{(index + 1):02d}")
            follicle_nodes.append(fol_shape)
            follicle_transforms.append(fol_trans)
        hierarchy_utils.parent(source_objects=follicle_transforms, target_parent=spine_ik_grp)

        # Constraints FK -> Base
        for fk_jnt, base_jnt in zip(fk_joints, module_jnt_list):
            constraint_targets(source_driver=fk_jnt, target_driven=base_jnt)
        # Constraints Follicle -> IK
        for spine_fol, ik_jnt in zip(follicle_transforms, ik_joints):
            constraint_targets(source_driver=spine_fol, target_driven=ik_jnt)

        ik_limit_handle = self._assemble_ctrl_name(name="spineLimit",
                                                   overwrite_suffix=NamingConstants.Suffix.IK_HANDLE_SC)
        ik_limit_handle = cmds.ikHandle(name=ik_limit_handle, solver='ikSCsolver',
                                        startJoint=limit_joints[0], endEffector=limit_joints[-1])[0]
        add_separator_attr(target_object=cog_ctrl, attr_name='squashStretch')
        setup_name = self.get_meta_setup_name()
        if _prefix:
            setup_name = f'{_prefix}{setup_name}'
        create_stretchy_ik_setup(ik_handle=ik_limit_handle, attribute_holder=cog_ctrl, prefix=setup_name)
        # create_stretchy_ik_setup(ik_handle=ik_limit_handle, attribute_holder=cog_ctrl, prefix=f'{_prefix}_spine')

        # for (control, joint) in zip(follicle_transforms, ik_joints):
        #     cmds.parentConstraint(control, joint)
        #     cmds.scaleConstraint(control, joint)

        # # TODO TEMP @@@
        # out_find_driver = self.find_driver(driver_type=RiggerDriverTypes.FK, proxy_purpose=self.hip)
        # out_find_module_drivers = self.find_module_drivers()
        # out_find_proxy_drivers = self.find_proxy_drivers(proxy=self.hip, as_dict=True)
        # print(f"out_find_driver:{out_find_driver}")
        # print(f"out_find_module_drivers:{out_find_module_drivers}")
        # print(f"out_find_proxy_drivers:{out_find_proxy_drivers}")

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [cog_offset]


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.utils.session_utils import remove_modules_startswith
    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    from gt.tools.auto_rigger.rig_framework import RigProject
    from gt.tools.auto_rigger.module_root import ModuleRoot
    a_root = ModuleRoot()
    a_spine = ModuleSpine()
    a_spine.set_spine_num(0)
    a_spine.set_spine_num(6)
    a_spine.set_parent_uuid(a_root.root.get_uuid())
    a_project = RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_spine)
    a_project.build_proxy()

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
