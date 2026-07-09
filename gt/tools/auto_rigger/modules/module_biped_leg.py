"""
Auto Rigger Biped Leg Module
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.hierarchy as core_hrchy
import gt.core.rigging as core_rigging
import gt.core.transform as core_trans
import gt.core.naming as core_naming
import gt.core.color as core_color
import gt.core.curve as core_curve
import gt.core.attr as core_attr
import gt.core.math as core_math
import gt.core.node as core_node
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleBipedLeg(tools_rig_frm.ModuleGeneric):
    __version__ = "1.0.0"
    icon = ui_res_lib.Icon.rigger_module_biped_leg
    allow_parenting = True

    # Reference Attributes
    REF_ATTR_KNEE_PROXY_PV = "lowerlegProxyPoleVectorLookupAttr"

    def __init__(
        self,
        name="Leg",
        prefix=None,
        suffix=None,
        create_twist_joints=False,
        auto_pole_vector=False,
        ensure_coplanarity=True,
    ):
        """
        Initialize a ModuleBipedLeg instance.

        Args:
            name (str, optional): Name of the module instance. Defaults to "Leg".
            prefix (str or None, optional): Optional prefix for naming rig components.
            suffix (str or None, optional): Optional suffix for naming rig components.
            create_twist_joints (bool, optional): Whether to create twist joints for upper and lower leg.
            auto_pole_vector (bool, optional): Whether to automatically create pole vector for the knee.
            ensure_coplanarity (bool, optional): True by default, this option keeps aligned the ball and tip
                                                 of the foot in order to avoid switching issues between IK and FK.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        # Module Config Vars
        self.setup_name = "leg"
        self.delete_toe_bind_jnt = True
        self.rig_pose_knee_rot = -3.0  # value used to create the control rig pose
        self.create_twist_joints = create_twist_joints
        self.auto_pole_vector = auto_pole_vector
        self.ensure_coplanarity = ensure_coplanarity
        self.upperleg_twist_joints = []
        self.lowerleg_twist_joints = []

        # Private Vars
        self._ankle_init_ty = None
        self._upperleg_dir_curve = None
        self._lowerleg_dir_curve = None

        # Orientation
        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Module Unique Vars
        upperleg_name = "upperLeg"
        lowerleg_name = "lowerLeg"
        foot_name = "foot"
        ball_name = "ball"
        toe_name = "toe"
        heel_name = "heel"
        bank_left_name = "bankLeft"
        bank_right_name = "bankRight"

        # Extra Module Data
        self.set_extra_callable_function(self._delete_unbound_joints)  # Called after the control rig is built

        # Default Proxies
        self.upperleg_proxy = tools_rig_frm.Proxy(name=upperleg_name)
        self.upperleg_proxy.set_locator_scale(scale=2)
        self.upperleg_proxy.set_meta_purpose(value=upperleg_name)
        self.upperleg_proxy.set_rotation_order("yzx")
        self.upperleg_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
            ]
        )

        self.lowerleg_proxy = tools_rig_frm.Proxy(name=lowerleg_name)
        self.lowerleg_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_arrow_pos_z"))
        self.lowerleg_proxy.set_locator_scale(scale=2)
        self.lowerleg_proxy.add_line_parent(line_parent=self.upperleg_proxy)
        self.lowerleg_proxy.set_parent_uuid(uuid=self.upperleg_proxy.get_uuid())
        self.lowerleg_proxy.set_meta_purpose(value=lowerleg_name)
        self.lowerleg_proxy.set_rotation_order("xyz")
        self.lowerleg_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )

        self.foot_proxy = tools_rig_frm.Proxy(name=foot_name)
        self.foot_proxy.set_locator_scale(scale=2)
        self.foot_proxy.add_line_parent(line_parent=self.lowerleg_proxy)
        self.foot_proxy.set_meta_purpose(value=foot_name)
        self.foot_proxy.set_rotation_order("yzx")
        self.foot_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )

        self.ball_proxy = tools_rig_frm.Proxy(name=ball_name)
        self.ball_proxy.set_locator_scale(scale=2)
        self.ball_proxy.add_line_parent(line_parent=self.foot_proxy)
        self.ball_proxy.set_parent_uuid(uuid=self.foot_proxy.get_uuid())
        self.ball_proxy.set_meta_purpose(value="ball")
        self.ball_proxy.set_rotation_order("xyz")
        self.ball_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
            ]
        )

        self.toe_proxy = tools_rig_frm.Proxy(name=toe_name)
        self.toe_proxy.set_locator_scale(scale=1)
        self.toe_proxy.set_parent_uuid(uuid=self.ball_proxy.get_uuid())
        self.toe_proxy.set_parent_uuid_from_proxy(parent_proxy=self.ball_proxy)
        self.toe_proxy.set_meta_purpose(value="toe")
        self.toe_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )

        # Pivots
        self.heel_proxy = tools_rig_frm.Proxy(name=heel_name)
        self.heel_proxy.set_locator_scale(scale=1)
        self.heel_proxy.add_line_parent(line_parent=self.foot_proxy)
        self.heel_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.PIVOT)
        self.heel_proxy.set_meta_purpose(value="heel")

        self.bank_left_proxy = tools_rig_frm.Proxy(name=bank_left_name)
        self.bank_left_proxy.set_locator_scale(scale=1)
        self.bank_left_proxy.add_line_parent(line_parent=self.foot_proxy)
        self.bank_left_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.PIVOT)
        self.bank_left_proxy.set_meta_purpose(value="bankLeft")

        self.bank_right_proxy = tools_rig_frm.Proxy(name=bank_right_name)
        self.bank_right_proxy.set_locator_scale(scale=1)
        self.bank_right_proxy.add_line_parent(line_parent=self.foot_proxy)
        self.bank_right_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.PIVOT)
        self.bank_right_proxy.set_meta_purpose(value="bankRight")

        # Initial Transforms
        upperleg_pos = core_trans.Vector3(y=84.5)
        lowerleg_pos = core_trans.Vector3(y=47.05, z=2)
        foot_pos = core_trans.Vector3(y=9.6)
        ball_pos = core_trans.Vector3(z=13.1)
        toe_pos = core_trans.Vector3(z=23.4)
        heel_pos = core_trans.Vector3()
        bank_left_pos = core_trans.Vector3(x=5, z=13.1)
        bank_right_pos = core_trans.Vector3(x=-5, z=13.1)

        self.upperleg_proxy.start_position = upperleg_pos
        self.upperleg_proxy.set_initial_position(xyz=upperleg_pos)
        self.lowerleg_proxy.start_position = lowerleg_pos
        self.lowerleg_proxy.set_initial_position(xyz=lowerleg_pos)
        self.foot_proxy.start_position = foot_pos
        self.foot_proxy.set_initial_position(xyz=foot_pos)
        self.ball_proxy.start_position = ball_pos
        self.ball_proxy.set_initial_position(xyz=ball_pos)
        self.toe_proxy.start_position = toe_pos
        self.toe_proxy.set_initial_position(xyz=toe_pos)
        self.heel_proxy.start_position = heel_pos
        self.heel_proxy.set_initial_position(xyz=heel_pos)
        self.bank_left_proxy.start_position = bank_left_pos
        self.bank_left_proxy.set_initial_position(xyz=bank_left_pos)
        self.bank_right_proxy.start_position = bank_right_pos
        self.bank_right_proxy.set_initial_position(xyz=bank_right_pos)

        # Update Proxies
        self.proxies = [
            self.upperleg_proxy,
            self.lowerleg_proxy,
            self.foot_proxy,
            self.ball_proxy,
            self.toe_proxy,
            self.heel_proxy,
            self.bank_left_proxy,
            self.bank_right_proxy,
        ]

    def set_orientation_direction(self, is_positive, **kwargs):
        """
        Sets the direction of the orientation.
        If positive, it will use "1" in the desired axis.
        If negative, (not positive) it will use "-1" in the desired axis.
        Args:
            is_positive (bool): If True, it's set to a positive direction, if False to negative.
                                e.g. True = (1, 0, 0) while False (-1, 0, 0)
        """
        super().set_orientation_direction(
            is_positive=is_positive, set_aim_axis=True, set_up_axis=False, set_up_dir=False  # Only Aim Axis
        )

    def set_rig_pose_knee_rot(self, knee_rotation):
        """
        Sets the set_rig_pose_knee_rot class variable used to set the control rig pose for this module.

        Args:
            knee_rotation (int, float): numerical value to set
        """
        if isinstance(knee_rotation, (float, int)):
            self.rig_pose_knee_rot = float(knee_rotation)
        else:
            logger.warning("Given knee rotation is not an int or a float. Skipped.")

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
        self.read_purpose_matching_proxy_from_dict(proxy_dict)

    def create_direction_curve(self, proxy, parent_node):
        """
        Creates a direction proxy curve.
        Args:
            proxy (obj): Proxy object
            parent_node (str): parent node name
        Returns
            dir_curve: core_node.Node object
            dir_curve_offset
        """
        module_aim = self.orientation.get_aim_axis()
        dir_curve = core_curve.get_curve("_joint_arrow_dir_pos_x")
        dir_rot = -90
        if module_aim[0] == -1:
            dir_curve = core_curve.get_curve("_joint_arrow_dir_neg_x")
            dir_rot = 90

        _dir_curve_name = f"{self._assemble_node_name(proxy.get_name())}_dir"
        dir_curve.set_name(_dir_curve_name)
        dir_curve = dir_curve.build()
        dir_curve = core_node.Node(dir_curve)
        cmds.setAttr(f"{dir_curve}.displayLocalAxis", 0)  # turn on for debugging
        core_curve.rescale_curve(dir_curve, 4)
        dir_curve_offset = core_hrchy.add_offset_transform(dir_curve)[0]
        cmds.delete(cmds.parentConstraint(parent_node, dir_curve_offset))
        cmds.parent(dir_curve_offset, parent_node)
        cmds.setAttr(f"{dir_curve_offset}.rx", dir_rot)
        return dir_curve, dir_curve_offset

    def setup_direction_curve(self, dir_curve, aim_object, world_up_object=None, x_offset=None, skip_axis=None):
        """
        Set up a direction proxy curve.
        Args:
            dir_curve (Node or str): direction curve to set up
            aim_object (str): target object
            world_up_object (str, optional): object used to determine the up vector for the aim
            x_offset (int, optional): x offset rotation
            skip_axis (list, optional): axis to skip (e.g. ["x"], ["x", "y"], etc.)
        """
        aim_vec = self.orientation.get_aim_axis()
        up_vec = self.orientation.get_up_axis()

        if not world_up_object:
            world_up_object = aim_object
        if not skip_axis:
            skip_axis = "none"
        dir_aim = cmds.aimConstraint(
            aim_object,
            dir_curve,
            aimVector=aim_vec,
            upVector=up_vec,
            worldUpObject=world_up_object,
            worldUpType="objectrotation",
            skip=skip_axis,
        )[0]

        # Set X Offset
        if not x_offset:
            x_offset = 0
        cmds.setAttr(f"{dir_aim}.offsetX", x_offset)

        # Lock and set attributes
        core_attr.hide_lock_default_attrs(dir_curve, scale=True, translate=True)
        cmds.setAttr(f"{dir_curve}.overrideEnabled", 1)
        cmds.setAttr(f"{dir_curve}.overrideDisplayType", 2)

    def create_coplane_joints(self):
        """Create joints needed to build an Ik solver to ensure the coplane relation for the proxies of the leg."""
        coplane_joints = []
        foot_node = tools_rig_utils.find_proxy_from_uuid(self.foot_proxy.get_uuid())
        _ref_objects = [self._upperleg_dir_curve, self._lowerleg_dir_curve, foot_node]

        for ref_obj in _ref_objects:
            joint_name = ref_obj.get_short_name().replace("_dir", "_proxy_jnt")
            joint = core_node.create_node(node_type="joint", name=joint_name)
            cmds.delete(cmds.parentConstraint(ref_obj, joint))
            if coplane_joints:
                cmds.parent(joint, coplane_joints[-1])
            coplane_joints.append(joint)
        [cmds.makeIdentity(jnt, apply=True, rotate=True) for jnt in coplane_joints]

        return coplane_joints

    def create_pole_joints(self):
        """Create joints needed to build an Ik solver to ensure the pole vector direction for the proxies of the leg."""
        pole_joints = []
        upperleg_node = tools_rig_utils.find_proxy_from_uuid(self.upperleg_proxy.get_uuid())
        foot_node = tools_rig_utils.find_proxy_from_uuid(self.foot_proxy.get_uuid())
        _points = [upperleg_node, foot_node]

        for point_node in _points:
            joint_name = f"{point_node.get_short_name()}_pole_jnt"
            joint = core_node.create_node(node_type="joint", name=joint_name)
            cmds.delete(cmds.pointConstraint(point_node, joint))
            if pole_joints:
                cmds.parent(joint, pole_joints[-1])
            pole_joints.append(joint)
        cmds.joint(pole_joints[0], e=True, zso=True, oj="xyz", sao="yup")
        [cmds.makeIdentity(jnt, apply=True, rotate=True) for jnt in pole_joints]

        return pole_joints

    def setup_proxy_coplane(self, coplane_joints, pole_joints):
        """Create the setup the proxy coplane.
        Args:
            coplane_joints (list): coplane joints
            pole_joints (list): pole joints
        """
        coplane_prefix = f"{self._assemble_node_name(self.setup_name)}_coplane"
        pole_prefix = f"{self._assemble_node_name(self.setup_name)}_pole"

        upperleg_node = tools_rig_utils.find_proxy_from_uuid(self.upperleg_proxy.get_uuid())
        lowerleg_node = tools_rig_utils.find_proxy_from_uuid(self.lowerleg_proxy.get_uuid())
        foot_node = tools_rig_utils.find_proxy_from_uuid(self.foot_proxy.get_uuid())

        coplane_ik_handle = cmds.ikHandle(
            sj=coplane_joints[0], ee=coplane_joints[2], n=f"{coplane_prefix}_ikHandle", sol="ikRPsolver"
        )[0]
        coplane_ik_handle = core_node.Node(coplane_ik_handle)
        cmds.parent(coplane_joints[0], upperleg_node)
        cmds.parent(coplane_ik_handle, foot_node)

        pole_ik_handle = cmds.ikHandle(
            sj=pole_joints[0], ee=pole_joints[1], n=f"{pole_prefix}_ikHandle", sol="ikRPsolver"
        )[0]
        pole_ik_handle = core_node.Node(pole_ik_handle)
        cmds.parent(pole_joints[0], upperleg_node)
        cmds.parent(pole_ik_handle, foot_node)

        upper_length = cmds.distanceDimension(sp=(-0.1, -0.1, 0.0), ep=(0.1, -0.1, 0.0))
        upper_length = cmds.rename(upper_length, f"{coplane_prefix}_upperlengthShape")
        upper_length_transform = cmds.listRelatives(upper_length, parent=True, fullPath=True) or [][0]
        upper_length_transform = cmds.rename(upper_length_transform, f"{coplane_prefix}_upperlength")
        upper_start_loc, upper_end_loc = cmds.listConnections(upper_length)
        cmds.parent(upper_start_loc, upper_end_loc, tools_rig_const.RiggerConstants.GRP_LINE_NAME)
        cmds.parentConstraint(upperleg_node, upper_start_loc, mo=False)
        cmds.parentConstraint(lowerleg_node, upper_end_loc, mo=False)
        cmds.parent(upper_length_transform, upperleg_node)
        upper_divide = core_node.create_node(node_type="multiplyDivide", name=f"{coplane_prefix}_upperdivide")
        _current_length = cmds.getAttr(f"{upper_length}.distance")
        cmds.setAttr(f"{upper_divide}.operation", 2)
        cmds.setAttr(f"{upper_divide}.input2X", _current_length)
        cmds.connectAttr(f"{upper_length}.distance", f"{upper_divide}.input1X")
        cmds.connectAttr(f"{upper_divide}.outputX", f"{coplane_joints[0]}.scaleX")

        lower_length = cmds.distanceDimension(sp=(-0.1, -0.1, 0.0), ep=(0.1, -0.1, 0.0))
        lower_length = cmds.rename(lower_length, f"{coplane_prefix}_lowerlengthShape")
        lower_length_transform = cmds.listRelatives(lower_length, parent=True, fullPath=True) or [][0]
        lower_length_transform = cmds.rename(lower_length_transform, f"{coplane_prefix}_lowerlength")
        lower_start_loc, lower_end_loc = cmds.listConnections(lower_length)
        cmds.parent(lower_start_loc, lower_end_loc, tools_rig_const.RiggerConstants.GRP_LINE_NAME)
        cmds.parentConstraint(lowerleg_node, lower_start_loc, mo=False)
        cmds.parentConstraint(foot_node, lower_end_loc, mo=False)
        cmds.parent(lower_length_transform, lowerleg_node)
        lower_divide = core_node.create_node(node_type="multiplyDivide", name=f"{coplane_prefix}_lowerdivide")
        _current_length = cmds.getAttr(f"{lower_length}.distance")
        cmds.setAttr(f"{lower_divide}.operation", 2)
        cmds.setAttr(f"{lower_divide}.input2X", _current_length)
        cmds.connectAttr(f"{lower_length}.distance", f"{lower_divide}.input1X")
        cmds.connectAttr(f"{lower_divide}.outputX", f"{coplane_joints[1]}.scaleX")

        cmds.poleVectorConstraint(lowerleg_node, coplane_ik_handle)
        cmds.poleVectorConstraint(lowerleg_node, pole_ik_handle)

        # Hide joints
        objs_to_hide = coplane_joints
        objs_to_hide.extend(pole_joints)
        objs_to_hide.append(coplane_ik_handle)
        objs_to_hide.append(pole_ik_handle)
        objs_to_hide.append(upper_length_transform)
        objs_to_hide.append(upper_start_loc)
        objs_to_hide.append(upper_end_loc)
        objs_to_hide.append(lower_length_transform)
        objs_to_hide.append(lower_start_loc)
        objs_to_hide.append(lower_end_loc)
        core_attr.set_attr(obj_list=objs_to_hide, attr_list="visibility", value=0)
        core_attr.set_attr(obj_list=objs_to_hide, attr_list="hiddenInOutliner", value=1)

    def get_proxies_mirrored(self, **kwargs):
        """
        Mirrors proxy transforms from the opposite side of the rig.

        Args:
            **kwargs: Optional keyword arguments passed to the base implementation.
        """
        super().get_proxies_mirrored()

        # Fix right and left bank pivots
        plane = "YZ"
        rotate_order = "xyz"
        bank_left_proxy = self.bank_left_proxy
        bank_right_proxy = self.bank_right_proxy
        bank_left_proxy_item = tools_rig_utils.find_proxy_from_uuid(bank_left_proxy.get_uuid())
        bank_right_proxy_item = tools_rig_utils.find_proxy_from_uuid(bank_right_proxy.get_uuid())
        bank_left_item_to_use = tools_rig_utils.find_drivers_from_module(
            source_uuid=self.mirror_uuid,
            filter_driver_type=tools_rig_const.RiggerDriverTypes.PROXY,
            filter_driver_purpose=bank_right_proxy.get_meta_purpose(),
        )
        if bank_left_item_to_use:
            bank_left_item_to_use = bank_left_item_to_use[0]
        bank_right_item_to_use = tools_rig_utils.find_drivers_from_module(
            source_uuid=self.mirror_uuid,
            filter_driver_type=tools_rig_const.RiggerDriverTypes.PROXY,
            filter_driver_purpose=bank_left_proxy.get_meta_purpose(),
        )
        if bank_right_item_to_use:
            bank_right_item_to_use = bank_right_item_to_use[0]
        bank_proxies_map = {bank_left_proxy_item: bank_left_item_to_use, bank_right_proxy_item: bank_right_item_to_use}

        for target_proxy_item, item_to_use in bank_proxies_map.items():

            # -- calculate the mirrored transformations from the identified opposite item
            matrix_to_use = cmds.xform(item_to_use, q=True, m=True, ws=True)
            mirrored_matrix = core_trans.mirror_transform_matrix(matrix_to_use, plane=plane, behaviour=True)
            mirrored_transform = core_trans.get_transform_from_matrix(mirrored_matrix, rotate_order=rotate_order)

            # -- apply mirrored transforms to the main proxy
            pos = mirrored_transform.position
            rot = mirrored_transform.rotation
            if cmds.getAttr(target_proxy_item + ".rotate", l=True):
                # apply only translation
                cmds.xform(target_proxy_item, t=(pos.x, pos.y, pos.z), ws=True)
            else:
                # apply position and rotation
                cmds.xform(target_proxy_item, t=(pos.x, pos.y, pos.z), ws=True)
                cmds.xform(target_proxy_item, ro=(rot.x, rot.y, rot.z), ws=True)

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
        if self.ensure_coplanarity:
            self.upperleg_proxy.parent_uuid = self.parent_uuid
            self.lowerleg_proxy.set_parent_uuid(self.foot_proxy.get_uuid())
            self.foot_proxy.set_parent_uuid(self.upperleg_proxy.get_uuid())
            self.toe_proxy.set_parent_uuid(self.ball_proxy.get_uuid())
            self.ball_proxy.set_parent_uuid(self.foot_proxy.get_uuid())
            self.heel_proxy.set_parent_uuid(self.foot_proxy.get_uuid())
            self.bank_left_proxy.set_parent_uuid(self.foot_proxy.get_uuid())
            self.bank_right_proxy.set_parent_uuid(self.foot_proxy.get_uuid())
            [proxy.set_setup_driver_uuid(proxy.parent_uuid) for proxy in self.proxies if proxy.parent_uuid]

        else:
            # Set the proxy parent_uuid and driver_uuid for the proxy construction hierarchy
            # (parent_uuid for the skeleton hierarchy, driver_uuid to adjust proxies transformations)
            if self.parent_uuid:
                self.upperleg_proxy.set_parent_uuid(self.parent_uuid)
            self.lowerleg_proxy.set_setup_driver_uuid(uuid=self.foot_proxy.get_uuid())
            self.lowerleg_proxy.set_parent_uuid(uuid=self.upperleg_proxy.get_uuid())
            self.foot_proxy.set_setup_driver_uuid(uuid=self.upperleg_proxy.get_uuid())
            self.foot_proxy.set_parent_uuid(uuid=self.upperleg_proxy.get_uuid())
            self.ball_proxy.set_setup_driver_uuid(uuid=self.foot_proxy.get_uuid())
            self.ball_proxy.set_parent_uuid(uuid=self.foot_proxy.get_uuid())
            self.toe_proxy.set_setup_driver_uuid(uuid=self.ball_proxy.get_uuid())
            self.toe_proxy.set_parent_uuid(uuid=self.ball_proxy.get_uuid())
            self.heel_proxy.set_setup_driver_uuid(uuid=self.foot_proxy.get_uuid())
            self.heel_proxy.set_parent_uuid(uuid=self.foot_proxy.get_uuid())
            self.bank_left_proxy.set_setup_driver_uuid(uuid=self.foot_proxy.get_uuid())
            self.bank_left_proxy.set_parent_uuid(uuid=self.foot_proxy.get_uuid())
            self.bank_right_proxy.set_setup_driver_uuid(uuid=self.foot_proxy.get_uuid())
            self.bank_right_proxy.set_parent_uuid(uuid=self.foot_proxy.get_uuid())

        proxy = super().build_proxy(**kwargs)  # Passthrough
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """
        # Get Maya Elements
        global_proxy = tools_rig_utils.find_ctrl_global_proxy()
        upperleg = tools_rig_utils.find_proxy_from_uuid(self.upperleg_proxy.get_uuid())
        lowerleg = tools_rig_utils.find_proxy_from_uuid(self.lowerleg_proxy.get_uuid())
        foot = tools_rig_utils.find_proxy_from_uuid(self.foot_proxy.get_uuid())
        ball = tools_rig_utils.find_proxy_from_uuid(self.ball_proxy.get_uuid())
        heel = tools_rig_utils.find_proxy_from_uuid(self.heel_proxy.get_uuid())
        toe = tools_rig_utils.find_proxy_from_uuid(self.toe_proxy.get_uuid())
        bank_left = tools_rig_utils.find_proxy_from_uuid(self.bank_left_proxy.get_uuid())
        bank_right = tools_rig_utils.find_proxy_from_uuid(self.bank_right_proxy.get_uuid())

        _dir_off_cnstr = None
        lowerleg_tag = lowerleg.get_short_name()

        if self.ensure_coplanarity:
            # Apply Initial World Orientation - in case the parent has a different one
            upperleg_offset = tools_rig_utils.get_proxy_offset(upperleg)
            foot_offset = tools_rig_utils.get_proxy_offset(foot)
            cmds.xform(upperleg_offset, ws=True, a=True, ro=(0, 0, 0))
            cmds.xform(foot_offset, ws=True, a=True, ro=(0, 0, 0))

            # Apply Initial Proxy Positions
            for proxy in self.get_proxies(sort_by="setup_driver"):
                proxy_node = tools_rig_utils.find_proxy_from_uuid(uuid_string=proxy.uuid)
                proxy_offset = tools_rig_utils.get_proxy_offset(proxy_node)
                _p_start_pos = proxy.start_position
                cmds.xform(proxy_offset, ws=True, a=True, t=(_p_start_pos.x, _p_start_pos.y, _p_start_pos.z))
                cmds.xform(proxy_node, ws=True, a=True, t=(_p_start_pos.x, _p_start_pos.y, _p_start_pos.z))

            # Build Direction Curves
            self._upperleg_dir_curve, upperleg_dir_curve_offset = self.create_direction_curve(
                self.upperleg_proxy, upperleg
            )
            core_attr.hide_lock_default_attrs(upperleg_dir_curve_offset, scale=True, rotate=True, translate=True)
            self._lowerleg_dir_curve, lowerleg_dir_curve_offset = self.create_direction_curve(
                self.lowerleg_proxy, lowerleg
            )

            # Direction Curves Starting Setup
            aim_x = self.orientation.get_aim_axis()[0]  # side
            self.setup_direction_curve(self._upperleg_dir_curve, lowerleg, x_offset=-90 * aim_x)
            _dir_off_cnstr = cmds.orientConstraint(self._upperleg_dir_curve, lowerleg_dir_curve_offset, mo=False)
            self.setup_direction_curve(self._lowerleg_dir_curve, foot, x_offset=90 * aim_x, skip_axis=["x", "y"])

        else:
            self.upperleg_proxy.apply_offset_transform()
            self.foot_proxy.apply_offset_transform()
            self.lowerleg_proxy.apply_offset_transform()
            self.ball_proxy.apply_offset_transform()
            self.heel_proxy.apply_offset_transform()
            self.bank_left_proxy.apply_offset_transform()
            self.bank_right_proxy.apply_offset_transform()

            # UpperLeg -----------------------------------------------------------------------------------
            core_attr.hide_lock_default_attrs(upperleg, scale=True)
            # core_attr.set_attr_state(obj_list=upperleg, attr_list=["rx", "rz"], locked=True, hidden=True)

            # LowerLeg  ---------------------------------------------------------------------------------
            core_attr.hide_lock_default_attrs(lowerleg, rotate=True, scale=True)
            core_attr.set_attr_state(obj_list=lowerleg, attr_list=["tx"], locked=True, hidden=True)

            # LowerLeg Setup - Always Between Hip and Ankle
            lowerleg_offset = tools_rig_utils.get_proxy_offset(lowerleg)
            core_cnstr.constraint_targets(
                source_driver=[upperleg, foot],
                target_driven=lowerleg_offset,
                constraint_type=core_cnstr.ConstraintTypes.POINT,
                maintain_offset=False,
            )

            lowerleg_pv_dir = cmds.spaceLocator(name=f"{lowerleg_tag}_poleVectorDir")[0]
            core_attr.add_attr(
                obj_list=lowerleg_pv_dir, attributes=ModuleBipedLeg.REF_ATTR_KNEE_PROXY_PV, attr_type="string"
            )
            core_trans.match_translate(source=lowerleg, target_list=lowerleg_pv_dir)
            cmds.move(0, 0, 13, lowerleg_pv_dir, relative=True)  # More it forward (in front of the lowerleg)
            core_hrchy.parent(lowerleg_pv_dir, lowerleg)
            core_attr.set_attr(obj_list=[lowerleg_pv_dir], attr_list="visibility", value=0)  # Set Visibility to Off
            core_attr.set_attr(
                obj_list=[lowerleg_pv_dir], attr_list="hiddenInOutliner", value=1
            )  # Set Outline Hidden to On

            cmds.aimConstraint(foot, lowerleg_offset, aimVector=(0, -1, 0), upVector=(0, -1, 0), skip=["x"])

        # Ball -----------------------------------------------------------------------------------
        foot_tag = foot.get_short_name()
        ball_offset = tools_rig_utils.get_proxy_offset(ball)
        ball_driver = core_hrchy.create_group(name=f"{foot_tag}_pivot")
        ball_driver = core_hrchy.parent(source_objects=ball_driver, target_parent=global_proxy)[0]
        foot_pos = cmds.xform(foot, q=True, ws=True, rp=True)
        cmds.move(foot_pos[0], ball_driver, moveX=True)
        cmds.pointConstraint(foot, ball_driver, maintainOffset=True, skip=["y"])
        cmds.orientConstraint(foot, ball_driver, maintainOffset=True, skip=["x", "z"])
        cmds.scaleConstraint(foot, ball_driver, skip=["y"])
        core_hrchy.parent(ball_offset, ball_driver)

        # Heel -----------------------------------------------------------------------------------
        heel_offset = tools_rig_utils.get_proxy_offset(heel)
        core_attr.hide_lock_default_attrs(heel, translate=False, rotate=True, scale=True)
        core_hrchy.parent(heel_offset, ball_driver)

        # Bank Left and Right -----------------------------------------------------------------------------------
        bank_left_offset = tools_rig_utils.get_proxy_offset(bank_left)
        core_attr.hide_lock_default_attrs(bank_left, translate=False, rotate=True, scale=True)
        core_hrchy.parent(bank_left_offset, ball_driver)

        bank_right_offset = tools_rig_utils.get_proxy_offset(bank_right)
        core_attr.hide_lock_default_attrs(bank_right, translate=False, rotate=True, scale=True)
        core_hrchy.parent(bank_right_offset, ball_driver)

        # Keep Grounded
        for to_lock_ty in [toe, ball, bank_left, bank_right, heel]:
            to_lock_ty = str(to_lock_ty)
            cmds.addAttr(to_lock_ty, ln="lockTranslateY", at="bool", k=True, niceName="Keep Grounded")
            cmds.setAttr(f"{to_lock_ty}.lockTranslateY", 0)
            cmds.setAttr(f"{to_lock_ty}.minTransYLimit", 0)
            cmds.setAttr(f"{to_lock_ty}.maxTransYLimit", 0)
            cmds.connectAttr(f"{to_lock_ty}.lockTranslateY", f"{to_lock_ty}.minTransYLimitEnable", f=True)
            cmds.connectAttr(f"{to_lock_ty}.lockTranslateY", f"{to_lock_ty}.maxTransYLimitEnable", f=True)

        # Hide unused ROT order attrs
        rot_order_attr = tools_rig_const.RiggerConstants.ATTR_ROT_ORDER
        core_attr.set_attr_state(f"{bank_left}.{rot_order_attr}", hidden=True)
        core_attr.set_attr_state(f"{bank_right}.{rot_order_attr}", hidden=True)
        core_attr.set_attr_state(f"{toe}.{rot_order_attr}", hidden=True)
        core_attr.set_attr_state(f"{heel}.{rot_order_attr}", hidden=True)

        if self.ensure_coplanarity:
            # Build solver to ensure co-plane relation between upperLeg and foot
            coplane_joints = self.create_coplane_joints()
            pole_joints = self.create_pole_joints()
            self.setup_proxy_coplane(coplane_joints, pole_joints)
            cmds.delete(cmds.listRelatives(self._upperleg_dir_curve, children=True, type="aimConstraint")[0])
            cmds.delete(cmds.listRelatives(self._lowerleg_dir_curve, children=True, type="aimConstraint")[0])
            cmds.delete(_dir_off_cnstr)
            cmds.orientConstraint(coplane_joints[0], self._upperleg_dir_curve, mo=False)
            cmds.orientConstraint(coplane_joints[1], self._lowerleg_dir_curve, mo=False)
            _pole_aim = cmds.orientConstraint(pole_joints[0], lowerleg, mo=False)[0]
            cmds.setAttr(f"{_pole_aim}.offsetX", 90)
            cmds.setAttr(f"{_pole_aim}.offsetY", -90)

            core_attr.hide_lock_default_attrs(ball, rotate=True, scale=True)
            core_attr.set_attr_state(obj_list=ball, attr_list=["tx"], locked=True, hidden=True)
            core_attr.hide_lock_default_attrs(toe, rotate=True, scale=True)
            core_attr.set_attr_state(obj_list=toe, attr_list=["tx"], locked=True, hidden=True)

            # pole vector locator
            lowerleg_pv_dir = cmds.spaceLocator(name=f"{lowerleg_tag}_poleVectorDir")[0]
            core_attr.add_attr(
                obj_list=lowerleg_pv_dir, attributes=ModuleBipedLeg.REF_ATTR_KNEE_PROXY_PV, attr_type="string"
            )
            cmds.delete(cmds.orientConstraint(pole_joints[0], lowerleg_pv_dir, mo=False))
            core_hrchy.parent(lowerleg_pv_dir, lowerleg)
            core_trans.match_translate(source=lowerleg, target_list=lowerleg_pv_dir)
            cmds.makeIdentity(lowerleg_pv_dir, a=True, t=True, r=False, s=False, n=False, pn=True)
            cmds.move(0, 0, 13, lowerleg_pv_dir, relative=True)  # More it forward (in front of the lowerleg)
            core_attr.set_attr(obj_list=[lowerleg_pv_dir], attr_list="visibility", value=0)  # Set Visibility to Off
            core_attr.set_attr(obj_list=[lowerleg_pv_dir], attr_list="hiddenInOutliner", value=1)

            # Apply transforms
            [proxy.apply_transforms() for proxy in self.get_proxies(sort_by="setup_driver")]
            cmds.rotate(0, 0, 0, lowerleg, a=True)  # only translations

        else:
            # Apply transform after set the order with build_proxy_setup parent function
            super().build_proxy_setup()  # Passthrough

            # Set proxy parent for the skeleton hierarchy
            # (the other proxies don't change in terms of hierarchy)
            self.lowerleg_proxy.set_parent_uuid(uuid=self.upperleg_proxy.get_uuid())
            self.foot_proxy.set_parent_uuid(uuid=self.lowerleg_proxy.get_uuid())

    def build_skeleton_joints(self):
        """
        Runs skeleton joints phase, which creates joints out of the proxy elements.
        This  happens after "build_proxy_setup" and as these are used to create the joints.
        """
        super().build_skeleton_joints()  # Passthrough

        # Delete Unnecessary joints (Proxies used as pivots)
        heel_jnt = tools_rig_utils.find_joint_from_uuid(self.heel_proxy.get_uuid())
        bank_left_jnt = tools_rig_utils.find_joint_from_uuid(self.bank_left_proxy.get_uuid())
        bank_right_jnt = tools_rig_utils.find_joint_from_uuid(self.bank_right_proxy.get_uuid())
        joints_to_delete = [heel_jnt, bank_left_jnt, bank_right_jnt]

        for jnt in joints_to_delete:
            if jnt and cmds.objExists(jnt):
                cmds.delete(jnt)

    def build_skeleton_hierarchy(self):
        """
        Runs skeletal hierarchy phase (post skeleton). Joints are parented and oriented during this step.
        Happens after the "build_skeleton_joints" function in a project.
        """
        upperleg_jnt = tools_rig_utils.find_joint_from_uuid(self.upperleg_proxy.get_uuid()).get_short_name()
        lowerleg_jnt = tools_rig_utils.find_joint_from_uuid(self.lowerleg_proxy.get_uuid()).get_short_name()
        foot_jnt = tools_rig_utils.find_joint_from_uuid(self.foot_proxy.get_uuid()).get_short_name()
        ball_jnt = tools_rig_utils.find_joint_from_uuid(self.ball_proxy.get_uuid()).get_short_name()
        toe_jnt = tools_rig_utils.find_joint_from_uuid(self.toe_proxy.get_uuid())

        module_aim = self.orientation.get_aim_axis()
        _side = module_aim[0]
        module_up = (0, _side, 0)

        if self.ensure_coplanarity:
            # Inherit rotation and rotation order
            for proxy in self.proxies:
                joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
                if not joint:
                    continue
                proxy_obj_path = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
                proxy_rotation_order = cmds.getAttr(
                    f"{proxy_obj_path}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}"
                )
                cmds.setAttr(f"{joint}.rotateOrder", proxy_rotation_order)
                if proxy == self.upperleg_proxy:
                    proxy_obj_path = self._upperleg_dir_curve
                elif proxy == self.lowerleg_proxy:
                    proxy_obj_path = self._lowerleg_dir_curve
                cmds.delete(cmds.orientConstraint(proxy_obj_path, joint))
                cmds.makeIdentity(joint, a=True, r=True)

        else:
            super().build_skeleton_hierarchy()  # Passthrough

            # set correct upper/lowerleg orientation
            cmds.parent(lowerleg_jnt, w=True)
            cmds.parent(foot_jnt, w=True)
            cmds.parent(ball_jnt, w=True)
            lowerleg = tools_rig_utils.find_proxy_from_uuid(self.lowerleg_proxy.get_uuid())
            temp_aim_loc = cmds.spaceLocator(n=f"{lowerleg_jnt}_temp_aim_loc")[0]
            cmds.delete(cmds.parentConstraint(lowerleg, temp_aim_loc))
            cmds.parent(temp_aim_loc, lowerleg)
            cmds.setAttr(f"{temp_aim_loc}.translateZ", 30)
            cmds.delete(
                cmds.aimConstraint(
                    lowerleg_jnt,
                    upperleg_jnt,
                    aimVector=module_aim,
                    upVector=module_up,
                    worldUpType="object",
                    worldUpObject=temp_aim_loc,
                )
            )
            cmds.delete(
                cmds.aimConstraint(
                    foot_jnt,
                    lowerleg_jnt,
                    aimVector=module_aim,
                    upVector=module_up,
                    worldUpType="object",
                    worldUpObject=temp_aim_loc,
                )
            )
            cmds.makeIdentity(upperleg_jnt, apply=True, rotate=True)
            cmds.makeIdentity(lowerleg_jnt, apply=True, rotate=True)
            cmds.delete(temp_aim_loc)

        # set the correct foot orientation (world aligned)
        self.orientation.set_aim_axis((-module_aim[0], 0, 0))
        self.orientation.set_world_aligned(world_aligned=True)
        self.orientation.apply_automatic_orientation(joint_list=[foot_jnt])
        cmds.delete(cmds.aimConstraint(ball_jnt, foot_jnt, aimVector=module_up, skip=["y", "z"]))
        cmds.makeIdentity(foot_jnt, apply=True, rotate=True)
        self.orientation.set_aim_axis(module_aim)
        self.orientation.set_world_aligned(world_aligned=False)

        # Parent joints
        if self.ensure_coplanarity:
            parent_uuid = self.upperleg_proxy.get_parent_uuid()
            if parent_uuid:
                parent_joint_node = tools_rig_utils.find_joint_from_uuid(parent_uuid)
                core_hrchy.parent(source_objects=upperleg_jnt, target_parent=parent_joint_node)

        core_hrchy.parent(source_objects=lowerleg_jnt, target_parent=upperleg_jnt)
        core_hrchy.parent(source_objects=foot_jnt, target_parent=lowerleg_jnt)
        core_hrchy.parent(source_objects=ball_jnt, target_parent=foot_jnt)
        core_hrchy.parent(source_objects=toe_jnt, target_parent=ball_jnt)
        self.orientation.apply_automatic_orientation([ball_jnt])
        cmds.select(clear=True)

        # Twist joints
        if self.create_twist_joints:
            self.upperleg_twist_joints = tools_rig_utils.create_twist_joints(
                upperleg_jnt, lowerleg_jnt, copy_start=True
            )
            self.lowerleg_twist_joints = tools_rig_utils.create_twist_joints(lowerleg_jnt, foot_jnt, copy_end=True)

    def build_rig(self, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """

        # Twist Setup
        if self.create_twist_joints:
            tools_rig_utils.create_twist_setup(
                twist_jnt_list=self.upperleg_twist_joints,
                mid_joints=2,
                side=self.prefix,
                reverse=True,
                reverse_matrix=True,
            )
            tools_rig_utils.create_twist_setup(
                twist_jnt_list=self.lowerleg_twist_joints, mid_joints=2, side=self.prefix
            )
            all_twist_jnts = self.upperleg_twist_joints + self.lowerleg_twist_joints
            tools_rig_utils.extract_twist_rotation(twist_jnt_list=all_twist_jnts)

        # Get Elements
        global_ctrl = tools_rig_utils.find_ctrl_global()
        global_offset_ctrl = tools_rig_utils.find_ctrl_global_offset()
        upperleg_jnt = tools_rig_utils.find_joint_from_uuid(self.upperleg_proxy.get_uuid())
        lowerleg_jnt = tools_rig_utils.find_joint_from_uuid(self.lowerleg_proxy.get_uuid())
        foot_jnt = tools_rig_utils.find_joint_from_uuid(self.foot_proxy.get_uuid())
        ball_jnt = tools_rig_utils.find_joint_from_uuid(self.ball_proxy.get_uuid())
        toe_jnt = tools_rig_utils.find_joint_from_uuid(self.toe_proxy.get_uuid())
        module_jnt_list = [upperleg_jnt, lowerleg_jnt, foot_jnt, ball_jnt, toe_jnt]

        # Get Formatted Prefix and Suffix
        _prefix = ""
        if self.prefix:
            _prefix = f"{self.prefix}_"
        _suffix = ""
        if self.suffix:
            _suffix = f"_{self.suffix}"

        # Set Colors
        for jnt in module_jnt_list:
            core_color.set_color_viewport(obj_list=jnt, rgb_color=(0.3, 0.3, 0))

        # Get Scale
        leg_scale = core_math.dist_path_sum(input_list=[upperleg_jnt, lowerleg_jnt, foot_jnt])
        foot_scale = core_math.dist_path_sum(input_list=[foot_jnt, ball_jnt, toe_jnt])

        # Create Parent Automation Elements
        joint_automation_grp = tools_rig_utils.find_or_create_joint_automation_group()
        general_automation_grp = tools_rig_utils.get_automation_group()
        module_parent_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())
        core_hrchy.parent(source_objects=module_parent_jnt, target_parent=joint_automation_grp)

        # Create Automation Skeletons (FK/IK) --------------------------------------------------------------
        upperleg_parent = module_parent_jnt
        if module_parent_jnt:
            core_color.set_color_viewport(
                obj_list=upperleg_parent, rgb_color=core_color.ColorConstants.RigJoint.AUTOMATION
            )
            core_rigging.rescale_joint_radius(
                joint_list=upperleg_parent, multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_DRIVEN
            )
        else:
            upperleg_parent = joint_automation_grp

        upperleg_fk = core_rigging.duplicate_joint_for_automation(upperleg_jnt, suffix="fk", parent=upperleg_parent)
        lowerleg_fk = core_rigging.duplicate_joint_for_automation(lowerleg_jnt, suffix="fk", parent=upperleg_fk)
        foot_fk = core_rigging.duplicate_joint_for_automation(foot_jnt, suffix="fk", parent=lowerleg_fk)
        ball_fk = core_rigging.duplicate_joint_for_automation(ball_jnt, suffix="fk", parent=foot_fk)
        toe_fk = core_rigging.duplicate_joint_for_automation(toe_jnt, suffix="fk", parent=ball_fk)
        fk_joints = [upperleg_fk, lowerleg_fk, foot_fk, ball_fk, toe_fk]

        upperleg_ik = core_rigging.duplicate_joint_for_automation(upperleg_jnt, suffix="ik", parent=upperleg_parent)
        lowerleg_ik = core_rigging.duplicate_joint_for_automation(lowerleg_jnt, suffix="ik", parent=upperleg_ik)
        foot_ik = core_rigging.duplicate_joint_for_automation(foot_jnt, suffix="ik", parent=lowerleg_ik)
        ball_ik = core_rigging.duplicate_joint_for_automation(ball_jnt, suffix="ik", parent=foot_ik)
        toe_ik = core_rigging.duplicate_joint_for_automation(toe_jnt, suffix="ik", parent=ball_ik)
        ik_joints = [upperleg_ik, lowerleg_ik, foot_ik, ball_ik, toe_ik]

        core_rigging.rescale_joint_radius(
            joint_list=fk_joints, multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_FK
        )
        core_rigging.rescale_joint_radius(
            joint_list=ik_joints, multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_IK
        )
        core_color.set_color_viewport(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigJoint.FK)
        core_color.set_color_viewport(obj_list=ik_joints, rgb_color=core_color.ColorConstants.RigJoint.IK)
        core_color.set_color_outliner(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigOutliner.FK)
        core_color.set_color_outliner(obj_list=ik_joints, rgb_color=core_color.ColorConstants.RigOutliner.IK)

        # FK Controls --------------------------------------------------------------------------------------

        fk_offsets_ctrls = []
        # FK UpperLeg Control
        upperleg_fk_ctrl, upperleg_fk_offset = self.create_rig_control(
            control_base_name=self.upperleg_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=global_offset_ctrl,
            match_obj=upperleg_jnt,
            add_offset_ctrl=False,
            rot_order=1,
            shape_scale=leg_scale * 0.1,
            color=core_color.get_directional_color(object_name=upperleg_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=upperleg_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.upperleg_proxy,
        )
        core_cnstr.constraint_targets(source_driver=upperleg_fk_ctrl, target_driven=upperleg_fk)
        fk_offsets_ctrls.append(upperleg_fk_offset[0])

        # FK LowerLeg Control
        lowerleg_fk_ctrl, lowerleg_fk_offset = self.create_rig_control(
            control_base_name=self.lowerleg_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=upperleg_fk_ctrl,
            match_obj=lowerleg_jnt,
            rot_order=0,
            add_offset_ctrl=False,
            shape_scale=leg_scale * 0.1,
            color=core_color.get_directional_color(object_name=lowerleg_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=lowerleg_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.lowerleg_proxy,
        )
        core_cnstr.constraint_targets(source_driver=lowerleg_fk_ctrl, target_driven=lowerleg_fk)
        fk_offsets_ctrls.append(lowerleg_fk_offset[0])

        # FK Foot Control
        foot_fk_ctrl, foot_fk_offset = self.create_rig_control(
            control_base_name=self.foot_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=lowerleg_fk_ctrl,
            match_obj=foot_jnt,
            add_offset_ctrl=False,
            rot_order=1,
            shape_scale=leg_scale * 0.1,
            color=core_color.get_directional_color(object_name=foot_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=foot_fk_ctrl, driver_type=tools_rig_const.RiggerDriverTypes.FK, proxy_purpose=self.foot_proxy
        )
        core_cnstr.constraint_targets(source_driver=foot_fk_ctrl, target_driven=foot_fk)
        fk_offsets_ctrls.append(foot_fk_offset[0])

        # Remove Ankle Shape Orientation
        temp_transform = core_hrchy.create_group(name=f"{foot_fk_ctrl}_rotExtraction")
        core_trans.match_translate(source=toe_jnt, target_list=temp_transform)
        core_trans.match_translate(source=foot_jnt, target_list=temp_transform, skip=["x", "z"])
        cmds.delete(
            cmds.aimConstraint(
                temp_transform,
                foot_fk_ctrl,
                offset=(0, 0, 0),
                aimVector=(0, 1, 0),
                upVector=(1, 0, 0),
                worldUpType="vector",
                worldUpVector=(0, -1, 0),
            )
        )
        cmds.delete(temp_transform)
        cmds.makeIdentity(foot_fk_ctrl, apply=True, rotate=True)

        # FK Ball Control
        ball_fk_ctrl, ball_offset = self.create_rig_control(
            control_base_name=self.ball_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=foot_fk_ctrl,
            rot_order=0,
            match_obj=ball_jnt,
            add_offset_ctrl=False,
            shape_scale=foot_scale * 0.3,
            color=core_color.get_directional_color(object_name=foot_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=ball_fk_ctrl, driver_type=tools_rig_const.RiggerDriverTypes.FK, proxy_purpose=self.ball_proxy
        )
        core_cnstr.constraint_targets(source_driver=ball_fk_ctrl, target_driven=ball_fk)
        fk_offsets_ctrls.append(ball_offset[0])

        # IK Controls --------------------------------------------------------------------------------------
        ik_offsets_ctrls = []

        # IK LowerLeg Control
        ik_suffix = core_naming.NamingConstants.Description.IK.upper()
        lowerleg_ik_ctrl, lowerleg_offset = self.create_rig_control(
            control_base_name=f"{self.lowerleg_proxy.get_name()}_{ik_suffix}",
            curve_file_name="primitive_diamond",
            parent_obj=global_offset_ctrl,
            match_obj_pos=foot_jnt,
            add_offset_ctrl=False,
            shape_scale=leg_scale * 0.05,
            color=core_color.get_directional_color(object_name=foot_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=lowerleg_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.lowerleg_proxy,
        )
        ik_offsets_ctrls.append(lowerleg_offset[0])

        # Find Pole Vector Position
        module_aim = self.orientation.get_aim_axis()
        _side = module_aim[0]

        lowerleg_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.lowerleg_proxy.get_uuid())
        lowerleg_proxy_children = (
            cmds.listRelatives(lowerleg_proxy, children=True, typ="transform", fullPath=True) or []
        )
        lowerleg_pv_dir = tools_rig_utils.find_object_with_attr(
            attr_name=ModuleBipedLeg.REF_ATTR_KNEE_PROXY_PV, lookup_list=lowerleg_proxy_children
        )
        temp_transform = core_hrchy.create_group(name=f"{lowerleg_ik_ctrl}_rotExtraction")
        core_trans.match_translate(source=lowerleg_jnt, target_list=temp_transform)

        if self._project.get_preferences_dict_value(key="apply_control_rig_pose", default=True):
            # We are in T-pose, the legs are straight, the pole vector needs just to be moved forward
            cmds.move(0, 0, leg_scale * 0.5, temp_transform, objectSpace=True, relative=True)
        else:
            cmds.delete(
                cmds.aimConstraint(
                    lowerleg_pv_dir,
                    temp_transform,
                    o=(0, 0, 0),
                    aim=(1, 0, 0),
                    u=(0, -1, 0),
                    wut="vector",
                    wu=(0, 1, 0),
                )
            )
            cmds.move(leg_scale * 0.5, 0, 0, temp_transform, objectSpace=True, relative=True)
        cmds.delete(cmds.pointConstraint(temp_transform, lowerleg_offset[0]))
        cmds.delete(temp_transform)

        # IK Aim Line
        tools_rig_utils.create_control_visualization_line(lowerleg_ik_ctrl, lowerleg_ik)

        # IK Foot Control
        foot_projection = cmds.xform(foot_jnt, ws=True, t=True, q=True)[1]
        if _side == 1:
            rot_offset = (0, 0, 0)
        else:
            rot_offset = (0, 0, 180)
            foot_projection = -foot_projection

        foot_ik_ctrl, foot_ik_offset, foot_o_ctrl, foot_o_data = self.create_rig_control(
            control_base_name=f"{self.foot_proxy.get_name()}_{ik_suffix}",
            curve_file_name="human_foot_outline",
            parent_obj=global_offset_ctrl,
            rot_order=1,
            match_obj_pos=foot_jnt,
            add_offset_ctrl=True,
            shape_scale=foot_scale * 0.5,
            shape_rot_offset=rot_offset,
            shape_pos_offset=(0, -foot_projection, 0),
            color=core_color.get_directional_color(object_name=foot_jnt),
        )
        self._add_driver_uuid_attr(
            target_driver=foot_ik_ctrl, driver_type=tools_rig_const.RiggerDriverTypes.IK, proxy_purpose=self.foot_proxy
        )
        self._add_driver_uuid_attr(
            target_driver=foot_o_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=f"{self.foot_proxy.get_name()}Offset",
        )
        cmds.orientConstraint(foot_ik_ctrl, foot_ik, mo=True)
        ik_offsets_ctrls.append(foot_ik_offset[0])

        # Switch Control
        foot_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.foot_proxy.get_uuid())
        ik_switch_ctrl, ik_switch_offset = self.create_rig_control(
            control_base_name=self.setup_name,
            curve_file_name="gear_eight_sides_smooth",
            parent_obj=global_ctrl,
            match_obj_pos=foot_proxy,
            add_offset_ctrl=False,
            shape_rot_offset=(0, 0, 90),
            shape_pos_offset=(0, 0, leg_scale * -0.3),
            shape_scale=leg_scale * 0.012,
            color=core_color.get_directional_color(object_name=foot_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=ik_switch_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.SWITCH,
            proxy_purpose=self.setup_name,
        )

        # Switch Setup
        core_rigging.create_switch_setup(
            source_a=ik_joints,
            source_b=fk_joints,
            target_base=module_jnt_list,
            attr_holder=ik_switch_ctrl,
            visibility_a=fk_offsets_ctrls,
            visibility_b=ik_offsets_ctrls,
            shape_visibility=False,
            prefix=_prefix,
            invert=True,
        )

        switch_cons = core_cnstr.constraint_targets(
            source_driver=[foot_fk_ctrl, foot_ik_ctrl], target_driven=ik_switch_offset
        )[0]
        leg_rev = cmds.createNode("reverse", name=f"{_prefix}leg_rev{_suffix}")
        cmds.connectAttr(f"{ik_switch_ctrl}.influenceSwitch", f"{leg_rev}.inputX")
        cmds.connectAttr(f"{leg_rev}.outputX", f"{switch_cons}.w0")
        cmds.connectAttr(f"{ik_switch_ctrl}.influenceSwitch", f"{switch_cons}.w1")

        influence_switch_attr_nice_name = "FK/IK"
        cmds.addAttr(f"{ik_switch_ctrl}.influenceSwitch", e=True, nn=influence_switch_attr_nice_name)
        cmds.setAttr(f"{ik_switch_ctrl}.influenceSwitch", 0)  # Default is FK

        # Foot Pivots
        foot_automation_grp = core_hrchy.create_group(
            name=f"{_prefix}{self.foot_proxy.get_name()}{_suffix}_automation_grp"
        )
        core_hrchy.parent(source_objects=foot_automation_grp, target_parent=general_automation_grp)

        foot_pivot_grp = core_hrchy.create_group(name=f"{_prefix}{self.foot_proxy.get_name()}{_suffix}_pivot_grp")
        core_trans.match_transform(source=foot_proxy, target_list=foot_pivot_grp, scale=False)
        core_hrchy.parent(source_objects=foot_pivot_grp, target_parent=foot_automation_grp)
        cmds.parentConstraint(foot_o_ctrl, foot_pivot_grp)

        bank_left_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.bank_left_proxy.get_uuid())
        bank_left_pivot_grp = core_hrchy.create_group(
            name=f"{_prefix}{self.bank_left_proxy.get_name()}{_suffix}_pivot_grp"
        )
        core_trans.match_transform(source=bank_left_proxy, target_list=bank_left_pivot_grp, scale=False)
        core_hrchy.parent(source_objects=bank_left_pivot_grp, target_parent=foot_pivot_grp)

        bank_right_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.bank_right_proxy.get_uuid())
        bank_right_pivot_grp = core_hrchy.create_group(
            name=f"{_prefix}{self.bank_right_proxy.get_name()}{_suffix}_pivot_grp"
        )
        core_trans.match_transform(source=bank_right_proxy, target_list=bank_right_pivot_grp, scale=False)
        core_hrchy.parent(source_objects=bank_right_pivot_grp, target_parent=bank_left_pivot_grp)

        heel_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.heel_proxy.get_uuid())
        heel_pivot_grp = core_hrchy.create_group(name=f"{_prefix}{self.heel_proxy.get_name()}{_suffix}_pivot_grp")
        core_trans.match_transform(source=heel_proxy, target_list=heel_pivot_grp, scale=False)
        core_hrchy.parent(source_objects=heel_pivot_grp, target_parent=bank_right_pivot_grp)

        ball_twist_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.ball_proxy.get_uuid())
        ball_twist_pivot_grp = core_hrchy.create_group(
            name=f"{_prefix}{self.ball_proxy.get_name()}{_suffix}Twist_pivot_grp"
        )
        core_trans.match_transform(source=ball_twist_proxy, target_list=ball_twist_pivot_grp, scale=False)
        core_hrchy.parent(source_objects=ball_twist_pivot_grp, target_parent=heel_pivot_grp)

        core_trans.match_transform(source=ball_twist_proxy, target_list=ball_twist_pivot_grp, scale=False)
        core_hrchy.parent(source_objects=ball_twist_pivot_grp, target_parent=heel_pivot_grp)

        toe_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.toe_proxy.get_uuid())
        toe_pivot_grp = core_hrchy.create_group(name=f"{_prefix}{self.toe_proxy.get_name()}{_suffix}_pivot_grp")
        core_trans.match_transform(source=toe_proxy, target_list=toe_pivot_grp, scale=False)
        core_hrchy.parent(source_objects=toe_pivot_grp, target_parent=ball_twist_pivot_grp)

        ball_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.ball_proxy.get_uuid())
        ball_pivot_grp = core_hrchy.create_group(name=f"{_prefix}{self.ball_proxy.get_name()}{_suffix}_pivot_grp")
        core_trans.match_transform(source=ball_proxy, target_list=ball_pivot_grp, scale=False)
        core_hrchy.parent(source_objects=ball_pivot_grp, target_parent=toe_pivot_grp)

        toe_fk_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.toe_proxy.get_uuid())
        toe_fk_ctrl_offset = core_hrchy.create_group(
            name=f"{_prefix}{self.toe_proxy.get_name()}{_suffix}FK_ctrl_offset"
        )
        core_trans.match_transform(source=ball_proxy, target_list=toe_fk_ctrl_offset, scale=False)
        core_hrchy.parent(source_objects=toe_fk_ctrl_offset, target_parent=toe_pivot_grp)
        toe_fk_ctrl_grp = core_hrchy.create_group(name=f"{_prefix}{self.toe_proxy.get_name()}{_suffix}FK_ctrl")
        core_trans.match_transform(source=ball_proxy, target_list=toe_fk_ctrl_grp, scale=False)
        core_hrchy.parent(source_objects=toe_fk_ctrl_grp, target_parent=toe_fk_ctrl_offset)
        toe_fk_pivot_grp = core_hrchy.create_group(name=f"{_prefix}{self.toe_proxy.get_name()}{_suffix}FK_pivot_grp")
        core_trans.match_transform(source=toe_fk_proxy, target_list=toe_fk_pivot_grp, scale=False)
        core_hrchy.parent(source_objects=toe_fk_pivot_grp, target_parent=toe_fk_ctrl_grp)

        # Foot Automation
        cmds.addAttr(foot_ik_ctrl, ln="kneeTwist", nn="Knee Twist", at="float", keyable=True)
        cmds.addAttr(foot_ik_ctrl, ln="footRolls", nn="Foot Rolls", at="enum", en="-------------:", keyable=True)
        cmds.setAttr(f"{foot_ik_ctrl}.footRolls", lock=True)

        cmds.addAttr(foot_ik_ctrl, ln="footRollWeight", nn="Foot Roll Weight", at="float", keyable=True, min=0, max=1.0)
        cmds.addAttr(foot_ik_ctrl, ln="footRoll", nn="Foot Roll", at="float", keyable=True)

        foot_weight_rev = cmds.createNode("reverse", n=f"{_prefix}footWeight_rev")
        cmds.connectAttr(f"{foot_ik_ctrl}.footRollWeight", f"{foot_weight_rev}.inputX")

        foot_roll_clamp = cmds.createNode("clamp", n=f"{_prefix}footRoll_clamp")
        cmds.connectAttr(f"{foot_ik_ctrl}.footRoll", f"{foot_roll_clamp}.inputR")
        cmds.connectAttr(f"{foot_ik_ctrl}.footRoll", f"{foot_roll_clamp}.inputG")
        cmds.setAttr(f"{foot_roll_clamp}.minR", -180)
        cmds.setAttr(f"{foot_roll_clamp}.maxG", 180)

        foot_mult = cmds.createNode("multiplyDivide", n=f"{_prefix}footWeight_mult")
        cmds.connectAttr(f"{foot_weight_rev}.outputX", f"{foot_mult}.input2X")
        cmds.connectAttr(f"{foot_ik_ctrl}.footRoll", f"{foot_mult}.input1Y")
        cmds.connectAttr(f"{foot_roll_clamp}.outputG", f"{foot_mult}.input1X")
        cmds.connectAttr(f"{foot_ik_ctrl}.footRollWeight", f"{foot_mult}.input2Y")

        cmds.addAttr(foot_ik_ctrl, ln="sideRoll", nn="Side Roll", at="float", keyable=True)
        side_roll_clamp = cmds.createNode("clamp", n=f"{_prefix}sideRoll_clamp")
        cmds.setAttr(f"{side_roll_clamp}.minR", -1000)
        cmds.setAttr(f"{side_roll_clamp}.maxG", 1000)
        cmds.connectAttr(f"{foot_ik_ctrl}.sideRoll", f"{side_roll_clamp}.inputR")
        cmds.connectAttr(f"{foot_ik_ctrl}.sideRoll", f"{side_roll_clamp}.inputG")
        side_roll_rev = cmds.createNode("multiplyDivide", n=f"{_prefix}sideRoll_multRev")
        cmds.setAttr(f"{side_roll_rev}.input2X", -1)
        cmds.setAttr(f"{side_roll_rev}.input2Y", -1)
        cmds.connectAttr(f"{side_roll_clamp}.outputR", f"{side_roll_rev}.input1X")
        cmds.connectAttr(f"{side_roll_clamp}.outputG", f"{side_roll_rev}.input1Y")
        cmds.connectAttr(f"{side_roll_rev}.outputY", f"{bank_left_pivot_grp}.rotateZ")
        cmds.connectAttr(f"{side_roll_rev}.outputX", f"{bank_right_pivot_grp}.rotateZ")

        cmds.addAttr(foot_ik_ctrl, ln="heelRoll", nn="Heel Roll", at="float", keyable=True)
        heel_rev = cmds.createNode("multiplyDivide", n=f"{_prefix}heel_multRev")
        cmds.setAttr(f"{heel_rev}.input2X", -1)
        heel_add = cmds.createNode("plusMinusAverage", n=f"{_prefix}heel_add")
        cmds.setAttr(f"{heel_add}.operation", 1)
        cmds.connectAttr(f"{foot_ik_ctrl}.heelRoll", f"{heel_rev}.input1X")
        cmds.connectAttr(f"{heel_rev}.outputX", f"{heel_add}.input3D[1].input3Dx")
        cmds.connectAttr(f"{foot_roll_clamp}.outputR", f"{heel_add}.input3D[2].input3Dx")
        cmds.connectAttr(f"{heel_add}.output3D.output3Dx", f"{heel_pivot_grp}.rotateX")

        cmds.addAttr(foot_ik_ctrl, ln="ballRoll", nn="Ball Roll", at="float", keyable=True)
        ball_add = cmds.createNode("plusMinusAverage", n=f"{_prefix}ball_add")
        cmds.setAttr(f"{ball_add}.operation", 1)
        cmds.connectAttr(f"{foot_ik_ctrl}.ballRoll", f"{ball_add}.input3D[1].input3Dx")
        cmds.connectAttr(f"{foot_mult}.outputX", f"{ball_add}.input3D[2].input3Dx")
        cmds.connectAttr(f"{ball_add}.output3D.output3Dx", f"{ball_pivot_grp}.rotateX")

        cmds.addAttr(foot_ik_ctrl, ln="toeRoll", nn="Toe Roll", at="float", keyable=True)
        toe_add = cmds.createNode("plusMinusAverage", n=f"{_prefix}toe_add")
        cmds.setAttr(f"{toe_add}.operation", 1)
        cmds.connectAttr(f"{foot_ik_ctrl}.toeRoll", f"{toe_add}.input3D[1].input3Dx")
        cmds.connectAttr(f"{foot_mult}.outputY", f"{toe_add}.input3D[2].input3Dx")
        cmds.connectAttr(f"{toe_add}.output3D.output3Dx", f"{toe_pivot_grp}.rotateX")

        cmds.addAttr(foot_ik_ctrl, ln="heelPivot", nn="Heel Pivot", at="float", keyable=True)
        cmds.connectAttr(f"{foot_ik_ctrl}.heelPivot", f"{heel_pivot_grp}.rotateY")

        cmds.addAttr(foot_ik_ctrl, ln="ballPivot", nn="Ball Pivot", at="float", keyable=True)
        cmds.connectAttr(f"{foot_ik_ctrl}.ballPivot", f"{ball_pivot_grp}.rotateY")

        cmds.addAttr(foot_ik_ctrl, ln="toePivot", nn="Toe Pivot", at="float", keyable=True)
        cmds.connectAttr(f"{foot_ik_ctrl}.toePivot", f"{ball_twist_pivot_grp}.rotateY")

        cmds.addAttr(foot_ik_ctrl, ln="tipPivot", nn="Tip Pivot", at="float", keyable=True)
        cmds.connectAttr(f"{foot_ik_ctrl}.tipPivot", f"{toe_pivot_grp}.rotateY")

        cmds.addAttr(foot_ik_ctrl, ln="toeUpDown", nn="Toe Up Down", at="float", keyable=True)
        cmds.connectAttr(f"{foot_ik_ctrl}.toeUpDown", f"{toe_fk_pivot_grp}.translateY")

        # Foot IK Toe Control
        toe_ik_ctrl, toe_ik_ctrl_offset = self.create_rig_control(
            control_base_name=f"{self.toe_proxy.get_name()}_{ik_suffix}",
            curve_file_name="pin",
            parent_obj=foot_ik_ctrl,
            rot_order=0,
            match_obj_pos=ball_jnt,
            add_offset_ctrl=False,
            shape_scale=foot_scale * 0.2,
            color=core_color.get_directional_color(object_name=foot_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=toe_ik_ctrl, driver_type=tools_rig_const.RiggerDriverTypes.IK, proxy_purpose=self.toe_proxy
        )
        cmds.connectAttr(f"{toe_ik_ctrl}.translate", f"{toe_fk_ctrl_grp}.translate")
        cmds.connectAttr(f"{toe_ik_ctrl}.rotate", f"{toe_fk_ctrl_grp}.rotate")

        cmds.addAttr(
            ik_switch_ctrl, ln="footAutomation", nn="Foot Automation", at="enum", en="-------------:", keyable=True
        )
        cmds.setAttr(f"{ik_switch_ctrl}.footAutomation", lock=True)
        cmds.addAttr(ik_switch_ctrl, ln="fullToeCtrlVisibility", nn="Full Toe Ctrl Visibility", at="bool", keyable=True)
        cmds.connectAttr(f"{ik_switch_ctrl}.fullToeCtrlVisibility", f"{toe_ik_ctrl_offset[0]}.visibility")

        # Foot IK Handle
        foot_ik_handle = cmds.ikHandle(
            sj=upperleg_ik,
            ee=foot_ik,
            n=f"{_prefix}{self.foot_proxy.get_name()}{_suffix}_ikHandle",
            sol="ikRPsolver",
        )[0]
        foot_ik_handle = core_node.Node(foot_ik_handle)
        cmds.poleVectorConstraint(lowerleg_ik_ctrl, foot_ik_handle)
        core_hrchy.parent(source_objects=foot_ik_handle, target_parent=ball_pivot_grp)

        # Knee Twist Ctrl Functionality
        twist_grp = core_hrchy.create_group(name=f"{_prefix}{self.lowerleg_proxy.get_name()}{_suffix}_twistGrp")
        twist_offset_grp = core_hrchy.add_offset_transform(target_list=twist_grp)[0]
        twist_aim_grp = pole_point_cnstr = pole_aim_cnstr = None

        if self.auto_pole_vector:
            twist_aim_grp = core_hrchy.create_group(name=f"{_prefix}{self.lowerleg_proxy.get_name()}{_suffix}_aimGrp")
            core_hrchy.parent(source_objects=[twist_aim_grp, twist_offset_grp], target_parent=global_offset_ctrl)
            if _side == 1:
                cmds.setAttr(f"{twist_aim_grp}.translateX", 1100)
            elif _side == -1:
                cmds.setAttr(f"{twist_aim_grp}.translateX", -1100)
            pole_point_cnstr = cmds.pointConstraint(upperleg_ik, foot_o_data, twist_offset_grp, mo=False)[0]
            pole_aim_cnstr = cmds.aimConstraint(foot_o_data, twist_offset_grp, wuo=twist_aim_grp, wut=1)[0]
            lowerleg_pv_parent = twist_aim_grp
        else:
            core_trans.match_transform(source=lowerleg_jnt, target_list=twist_offset_grp)
            core_hrchy.parent(source_objects=[twist_offset_grp], target_parent=global_offset_ctrl)
            lowerleg_pv_parent = twist_offset_grp
        core_hrchy.parent(source_objects=lowerleg_offset[0], target_parent=twist_grp)
        cmds.connectAttr(f"{foot_ik_ctrl}.kneeTwist", f"{twist_grp}.rotateX")

        # Ball IK Handle
        ball_ik_handle = cmds.ikHandle(
            sj=foot_ik, ee=ball_ik, n=f"{_prefix}{self.ball_proxy.get_name()}{_suffix}_ikHandle", sol="ikSCsolver"
        )
        core_hrchy.parent(source_objects=ball_ik_handle[0], target_parent=ball_pivot_grp)

        # Toe IK Handle
        toe_ik_handle = cmds.ikHandle(
            sj=ball_ik, ee=toe_ik, n=f"{_prefix}{self.toe_proxy.get_name()}{_suffix}_ikHandle", sol="ikSCsolver"
        )
        core_hrchy.parent(source_objects=toe_ik_handle[0], target_parent=toe_fk_pivot_grp)

        # Lock And Hide Attrs
        core_attr.hide_lock_default_attrs(
            [upperleg_fk_ctrl, lowerleg_fk_ctrl, foot_fk_ctrl, ball_fk_ctrl],
            translate=True,
            scale=True,
            visibility=True,
        )
        core_attr.hide_lock_default_attrs([lowerleg_ik_ctrl], rotate=True, scale=True, visibility=True)
        core_attr.hide_lock_default_attrs([foot_ik_ctrl, toe_ik_ctrl], scale=True, visibility=True)
        core_attr.hide_lock_default_attrs([ik_switch_ctrl], translate=True, rotate=True, scale=True, visibility=True)

        cmds.setAttr(f"{general_automation_grp}.visibility", 0)
        cmds.setAttr(f"{joint_automation_grp}.visibility", 0)

        # Follow Parent Setup
        module_parent = tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())
        if module_parent:
            for ctrls in [upperleg_fk_ctrl, lowerleg_ik_ctrl, foot_ik_ctrl]:
                core_attr.add_separator_attr(
                    target_object=ctrls, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE
                )
            tools_rig_utils.create_follow_enum_setup(
                control=upperleg_fk_ctrl,
                parent_list=[tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())],
                constraint_type="orient",
            )
            tools_rig_utils.create_follow_enum_setup(
                control=lowerleg_pv_parent,
                attribute_item=lowerleg_ik_ctrl,
                parent_list=[
                    tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid()),
                    foot_ik_ctrl,
                    global_offset_ctrl,
                ],
                default_value=0,
            )
            tools_rig_utils.create_follow_enum_setup(
                control=foot_ik_ctrl,
                parent_list=[global_offset_ctrl, tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())],
                default_value=0,
            )
        else:
            tools_rig_utils.create_follow_enum_setup(
                control=lowerleg_pv_parent,
                attribute_item=lowerleg_ik_ctrl,
                parent_list=[foot_ik_ctrl, global_offset_ctrl],
                default_value=0,
            )
            tools_rig_utils.create_follow_enum_setup(
                control=foot_ik_ctrl,
                parent_list=[global_offset_ctrl],
                default_value=0,
            )

        # IK/FK Switch Locators ---------------------------------------------------------------------------
        for ik_joint in [upperleg_ik, lowerleg_ik, foot_ik, ball_ik]:
            ik_name = core_node.get_short_name(ik_joint).split("_JNT_ik")[0]

            switch_loc = cmds.spaceLocator(n=f"{ik_name}FkOffsetRef_loc")[0]
            cmds.parent(switch_loc, ik_joint)
            cmds.matchTransform(switch_loc, ik_joint)
            cmds.setAttr(f"{switch_loc}.visibility", 0)

        for fk_joint in [lowerleg_fk, foot_fk, ball_fk]:
            fk_name = core_node.get_short_name(fk_joint).split("_JNT_fk")[0]
            switch_loc = cmds.spaceLocator(n=f"{fk_name}Switch_loc")[0]
            cmds.parent(switch_loc, fk_joint)
            if fk_joint is lowerleg_fk:
                core_trans.match_translate(source=lowerleg_ik_ctrl, target_list=switch_loc)
            else:
                core_trans.match_translate(source=fk_joint, target_list=switch_loc)
            cmds.setAttr(f"{switch_loc}.visibility", 0)

        # Auto pole vector attribute to be able to disable it in animation ----------------------------------
        if self.auto_pole_vector:
            auto_pole_attr = "autoPoleVector"
            auto_pole_attr_fullname = f"{lowerleg_ik_ctrl}.{auto_pole_attr}"
            cmds.addAttr(lowerleg_ik_ctrl, ln=auto_pole_attr, at="bool", k=True)
            cmds.setAttr(auto_pole_attr_fullname, 1)
            pole_parent_cnstr = cmds.parentConstraint(twist_aim_grp, lowerleg_offset[0], mo=True)[0]
            parent_cnstr_aim_attr = cmds.listConnections(
                pole_parent_cnstr, plugs=True, d=False, s=True, scn=True, t="parentConstraint", et=True
            )[0]
            aim_cnstr_foot_attr = cmds.listConnections(
                pole_aim_cnstr, plugs=True, d=False, s=True, scn=True, t="aimConstraint", et=True
            )[0]
            point_cnstr_upperleg_attr, point_cnstr_foot_attr = cmds.listConnections(
                pole_point_cnstr, plugs=True, d=False, s=True, scn=True, t="pointConstraint", et=True
            )
            cmds.setDrivenKeyframe(parent_cnstr_aim_attr, cd=auto_pole_attr_fullname, dv=1, v=0)
            cmds.setDrivenKeyframe(aim_cnstr_foot_attr, cd=auto_pole_attr_fullname, dv=1, v=1)
            cmds.setDrivenKeyframe(point_cnstr_foot_attr, cd=auto_pole_attr_fullname, dv=1, v=1)
            cmds.setDrivenKeyframe(point_cnstr_upperleg_attr, cd=auto_pole_attr_fullname, dv=1, v=1)
            cmds.setDrivenKeyframe(parent_cnstr_aim_attr, cd=auto_pole_attr_fullname, dv=0, v=1)
            cmds.setDrivenKeyframe(aim_cnstr_foot_attr, cd=auto_pole_attr_fullname, dv=0, v=0)
            cmds.setDrivenKeyframe(point_cnstr_foot_attr, cd=auto_pole_attr_fullname, dv=0, v=0)
            cmds.setDrivenKeyframe(point_cnstr_upperleg_attr, cd=auto_pole_attr_fullname, dv=0, v=0)

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [upperleg_fk_offset[0]]

    def build_control_rig_pose(self):
        """
        Builds the rig pose on a biped leg.
        """
        import gt.core.poses as core_poses

        # get joints
        upperleg_jnt = tools_rig_utils.find_joint_from_uuid(self.upperleg_proxy.get_uuid()).get_short_name()
        lowerleg_jnt = tools_rig_utils.find_joint_from_uuid(self.lowerleg_proxy.get_uuid()).get_short_name()
        foot_jnt = tools_rig_utils.find_joint_from_uuid(self.foot_proxy.get_uuid()).get_short_name()
        self._ankle_init_ty = cmds.xform(foot_jnt, q=1, ws=1, t=1)[1]

        # straighten
        core_poses.straighten_objs_by_side(
            [upperleg_jnt],
            forward_rot=90,
            point_down_rot=-90,
            mirror_prefix=core_naming.NamingConstants.Prefix.RIGHT,
        )
        core_poses.straighten_objs_by_side(
            [lowerleg_jnt],
            forward_rot=90,
            point_down_rot=-90,
            mirror_prefix=core_naming.NamingConstants.Prefix.RIGHT,
        )

        # remove rotations
        for jnt in [lowerleg_jnt, foot_jnt]:
            cmds.setAttr(jnt + ".rotate", 0, 0, 0)
            cmds.setAttr(jnt + ".jointOrient", 0, 0, 0)

        # add user rotation
        if self.rig_pose_knee_rot:
            cmds.setAttr(lowerleg_jnt + ".rotateZ", self.rig_pose_knee_rot)

        # set the foot
        core_poses.straighten_objs_by_side(
            [foot_jnt],
            forward_rot=90,
            point_down_rot=-90,
            mirror_prefix=core_naming.NamingConstants.Prefix.RIGHT,
        )

    def _delete_unbound_joints(self):
        """
        Deletes joints that are usually not bound to the mesh. In this case the toe joint.
        """
        if self.delete_toe_bind_jnt:
            toe_jnt = tools_rig_utils.find_joint_from_uuid(self.toe_proxy.get_uuid())
            if toe_jnt:
                cmds.delete(toe_jnt)

    # ------------------------------------------- Extra Module Setters -------------------------------------------
    def set_post_delete_toe_bind_joint(self, delete_joint):
        """
        Sets a variable to determine if the toe joint should be deleted or not
        Args:
            delete_joint (bool): If True, the toe joint will be deleted after the skeleton and control rig are created.
        """
        if not isinstance(delete_joint, bool):
            logger.warning(f'Unable to set "post_delete_toe_bind_joint". Incompatible data type provided.')
        self.delete_toe_bind_jnt = delete_joint


class ModuleBipedLegLeft(ModuleBipedLeg):
    def __init__(
        self,
        name="L Leg",
        prefix=core_naming.NamingConstants.Prefix.LEFT,
        suffix=None,
        auto_pole_vector=False,
        ensure_coplanarity=True,
    ):
        """
        Initialize a left ModuleBipedLeg instance.

        Args:
            name (str, optional): Name of the module instance. Defaults to "L Leg".
            prefix (str or None, optional): Optional prefix for naming rig components.
            suffix (str or None, optional): Optional suffix for naming rig components.
            auto_pole_vector (bool, optional): Whether to automatically create pole vector for the knee.
            ensure_coplanarity (bool, optional): True by default, this option keeps aligned the ball and tip
                                                 of the foot in order to avoid switching issues between IK and FK.
        """
        super().__init__(
            name=name,
            prefix=prefix,
            suffix=suffix,
            auto_pole_vector=auto_pole_vector,
            ensure_coplanarity=ensure_coplanarity,
        )

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Set Left X position
        left_offset = 10.2
        [proxy.transform.set_position(x=left_offset) for proxy in self.proxies]
        self.bank_left_proxy.transform.set_position(x=left_offset + 7)
        self.bank_right_proxy.transform.set_position(x=left_offset - 7)

    # Align hips only necessary in one leg
    def build_control_rig_pose(self):
        """
        Builds the rig pose by rounding rotate values to be straight (align with world)
        """
        super().build_control_rig_pose()

        parent_joint = tools_rig_utils.find_joint_from_uuid(self.parent_uuid)
        if parent_joint:
            # Control rig pose - align HIPS with the origin and adjust the height based on
            # the resulting difference between poses.
            foot_jnt = tools_rig_utils.find_joint_from_uuid(self.foot_proxy.get_uuid())

            ankle_rig_pose_ty = cmds.xform(foot_jnt, q=1, ws=1, t=1)[1]
            height_difference = self._ankle_init_ty - ankle_rig_pose_ty
            cmds.move(0, 0, 0, parent_joint, xz=True, ws=True)  # only x,z - origin alignment
            cmds.move(0, height_difference, 0, parent_joint, r=True)  # add difference in y-axis


class ModuleBipedLegRight(ModuleBipedLeg):
    def __init__(
        self,
        name="R Leg",
        prefix=core_naming.NamingConstants.Prefix.RIGHT,
        suffix=None,
        auto_pole_vector=False,
        ensure_coplanarity=True,
    ):
        """
        Initialize a right ModuleBipedLeg instance.

        Args:
            name (str, optional): Name of the module instance. Defaults to "R Leg".
            prefix (str or None, optional): Optional prefix for naming rig components.
            suffix (str or None, optional): Optional suffix for naming rig components.
            auto_pole_vector (bool, optional): Whether to automatically create pole vector for the knee.
            ensure_coplanarity (bool, optional): True by default, this option keeps aligned the ball and tip
                                                 of the foot in order to avoid switching issues between IK and FK.
        """
        super().__init__(
            name=name,
            prefix=prefix,
            suffix=suffix,
            auto_pole_vector=auto_pole_vector,
            ensure_coplanarity=ensure_coplanarity,
        )

        _orientation = tools_rig_frm.OrientationData(aim_axis=(-1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Set Right X position
        right_offset = -10.2
        [proxy.transform.set_position(x=right_offset) for proxy in self.proxies]
        self.bank_left_proxy.transform.set_position(x=right_offset + 7)
        self.bank_right_proxy.transform.set_position(x=right_offset - 7)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)

    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.core.session import remove_modules_startswith

    remove_modules_startswith("gt.tools.auto_rigger.module")
    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    import gt.tools.auto_rigger.rig_framework as tools_rig_fmr
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils

    # import gt.tools.auto_rigger.modules.module_biped_leg as tools_rig_mod_biped_leg
    import gt.tools.auto_rigger.modules.module_spine as tools_rig_mod_spine
    import gt.tools.auto_rigger.modules.module_root as module_root
    import importlib

    # importlib.reload(tools_rig_mod_biped_leg)
    importlib.reload(tools_rig_mod_spine)
    importlib.reload(tools_rig_fmr)
    importlib.reload(tools_rig_utils)

    a_root = module_root.ModuleRoot()
    a_spine = tools_rig_mod_spine.ModuleSpine()
    # a_leg = tools_rig_mod_biped_leg.ModuleBipedLeg()
    a_leg_lf = ModuleBipedLegLeft(auto_pole_vector=False)
    a_leg_rt = ModuleBipedLegRight()

    root_uuid = a_root.root_proxy.get_uuid()
    spine_upperleg_uuid = a_spine.hip_proxy.get_uuid()
    a_leg_lf.set_parent_uuid(spine_upperleg_uuid)
    a_leg_rt.set_parent_uuid(spine_upperleg_uuid)
    a_spine.set_parent_uuid(root_uuid)
    # a_leg_lf.set_post_delete_toe_bind_joint(False)

    a_project = tools_rig_fmr.RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_spine)
    a_project.add_to_modules(a_leg_lf)
    a_project.add_to_modules(a_leg_rt)

    a_project.build_proxy()

    # a_project.set_preference_value_using_key(key="apply_control_rig_pose", value=False)
    # a_project.build_skeleton()
    a_project.build_rig()
    # Frame all
    cmds.setAttr(f"skeleton.v", 1)
    cmds.setAttr(f"jointAutomation.v", 1)
    cmds.setAttr(f"L_ballSwitch_loc.v", 1)
    cmds.setAttr(f"generalAutomation.v", 1)
    cmds.setAttr(f"L_leg_CTRL.influenceSwitch", 1)
    cmds.setAttr(f"L_leg_CTRL.fullToeCtrlVisibility", 1)

    cmds.viewFit("C_root_JNT")

    control_name = "L_foot_IK_CTRL"
    attribute_name = "sideRoll"
    full_attribute_path = f"{control_name}.{attribute_name}"

    # Frame 0: Reset roll to 0 and keyframe
    cmds.currentTime(2)
    cmds.setAttr(full_attribute_path, 0)
    cmds.setKeyframe(control_name, attribute=attribute_name)

    # Frame 20: Set roll to 35 and keyframe
    cmds.currentTime(20)
    cmds.setAttr(full_attribute_path, 35)
    cmds.setKeyframe(control_name, attribute=attribute_name)
