"""
Auto Rigger Quadruped Rear Leg Module
"""

import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.tools.auto_rigger.rig_framework as tools_rig_frm
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.ui.resource_library as ui_res_lib
import gt.core.constraint as core_cnstr
import gt.core.hierarchy as core_hrchy
import gt.core.transform as core_trans
import gt.core.rigging as core_rigging
import gt.core.naming as core_naming
import gt.core.pose as core_pose
import gt.core.curve as core_curve
import gt.core.color as core_color
import gt.core.attr as core_attr
import gt.core.math as core_math
import gt.core.node as core_node
import gt.core.str as core_str
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ModuleQuadRearLeg(tools_rig_frm.ModuleGeneric):
    __version__ = "0.0.1-alpha"
    icon = ui_res_lib.Icon.rigger_module_quad_rear_leg
    allow_parenting = True
    allow_multiple = True

    def __init__(self, name="Quad Rear Leg", prefix=None, suffix=None, create_twist_joints=True, ik_world=True):
        """
        Module representing a quadruped's rear leg rig setup.

        Args:
            name (str): Name of the module instance. Defaults to "Quad Rear Leg".
            prefix (str or None): Optional naming prefix.
            suffix (str or None): Optional naming suffix.
            create_twist_joints (bool): If True, twist joints will be created.
            ik_world (bool): If True, IK operates in world space.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Extra Module Data
        self.setup_name = "rearLeg"
        self.create_twist_joints = create_twist_joints
        self.upperleg_twist_joints = []
        self.lowerleg_twist_joints = []
        self.ik_world = ik_world
        self.upperleg_dir_curve = None
        self.lowerleg_dir_curve = None
        self.paw_dir_curve = None

        # Extra Module Data
        self.set_extra_callable_function(self._delete_unbound_joints)  # Called after the control rig is built

        # Proxy Names
        upperleg_name = "rearUpperLeg"
        lowerleg_name = "rearLowerLeg"
        paw_name = "rearPaw"
        toes_name = "rearToes"
        ball_name = "rearBall"
        toesend_name = "rearToesEnd"
        # Pivots Names
        heel_name = "rearHeel"
        bank_left_name = "rearBankLeft"
        bank_right_name = "rearBankRight"

        # Proxy Trans
        pos_upperleg = core_trans.Vector3(0, 60, -40)
        pos_lowerleg = core_trans.Vector3(0, 36.82, -40)
        pos_paw = core_trans.Vector3(0, 23.58, -60)
        pos_toes = core_trans.Vector3(0, 6.77, -56.2)
        pos_ball = core_trans.Vector3(0, 4.4, -54.48)
        pos_toesend = core_trans.Vector3(0, 0, -50)
        # Pivots Trans
        pos_heel = core_trans.Vector3(0, 0, -56)
        pos_bank_left = core_trans.Vector3(0, 0, -53)
        pos_bank_right = core_trans.Vector3(0, 0, -53)

        # Proxies
        self.upperleg_proxy = tools_rig_frm.Proxy(name=upperleg_name)
        self.upperleg_proxy.start_position = pos_upperleg
        self.upperleg_proxy.set_initial_position(xyz=pos_upperleg)
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
        self.lowerleg_proxy.start_position = pos_lowerleg
        self.lowerleg_proxy.set_initial_position(xyz=pos_lowerleg)
        self.lowerleg_proxy.set_curve(curve=core_curve.get_curve("_proxy_joint_arrow_neg_z"))
        self.lowerleg_proxy.set_locator_scale(scale=2.2)
        self.lowerleg_proxy.add_line_parent(line_parent=self.upperleg_proxy)
        self.lowerleg_proxy.set_meta_purpose(value=lowerleg_name)
        self.lowerleg_proxy.set_rotation_order("xyz")
        self.lowerleg_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )
        self.paw_proxy = tools_rig_frm.Proxy(name=paw_name)
        self.paw_proxy.start_position = pos_paw
        self.paw_proxy.set_initial_position(xyz=pos_paw)
        self.paw_proxy.set_locator_scale(scale=2)
        self.paw_proxy.add_line_parent(line_parent=self.lowerleg_proxy)
        self.paw_proxy.set_meta_purpose(value=paw_name)
        self.paw_proxy.set_rotation_order("xyz")
        self.paw_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
                tools_rig_const.RiggerDriverTypes.SWITCH,
            ]
        )

        self.toes_proxy = tools_rig_frm.Proxy(name=toes_name)
        self.toes_proxy.start_position = pos_toes
        self.toes_proxy.set_initial_position(xyz=pos_toes)
        self.toes_proxy.set_locator_scale(scale=2)
        self.toes_proxy.add_line_parent(line_parent=self.paw_proxy)
        self.toes_proxy.set_meta_purpose(value=toes_name)
        self.toes_proxy.set_rotation_order("yzx")
        self.toes_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )

        self.ball_proxy = tools_rig_frm.Proxy(name=ball_name)
        self.ball_proxy.start_position = pos_ball
        self.ball_proxy.set_initial_position(xyz=pos_ball)
        self.ball_proxy.set_locator_scale(scale=2)
        self.ball_proxy.add_line_parent(line_parent=self.toes_proxy)
        self.ball_proxy.set_meta_purpose(value=ball_name)
        self.ball_proxy.set_rotation_order("xyz")
        self.ball_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.FK,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )

        self.toesend_proxy = tools_rig_frm.Proxy(name=toesend_name)
        self.toesend_proxy.start_position = pos_toesend
        self.toesend_proxy.set_initial_position(xyz=pos_toesend)
        self.toesend_proxy.set_locator_scale(scale=2)
        self.toesend_proxy.add_line_parent(line_parent=self.ball_proxy)
        self.toesend_proxy.set_meta_purpose(value=toesend_name)
        self.toesend_proxy.set_rotation_order("xyz")
        self.toesend_proxy.add_driver_type(
            driver_type=[
                tools_rig_const.RiggerDriverTypes.GENERIC,
                tools_rig_const.RiggerDriverTypes.IK,
            ]
        )

        # Pivots
        self.heel_proxy = tools_rig_frm.Proxy(name=heel_name)
        self.heel_proxy.start_position = pos_heel
        self.heel_proxy.set_initial_position(xyz=pos_heel)
        self.heel_proxy.set_locator_scale(scale=1)
        self.heel_proxy.add_line_parent(line_parent=self.toes_proxy)
        self.heel_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.PIVOT)
        self.heel_proxy.set_meta_purpose(value=heel_name)

        self.bank_left_proxy = tools_rig_frm.Proxy(name=bank_left_name)
        self.bank_left_proxy.start_position = pos_bank_left
        self.bank_left_proxy.set_initial_position(xyz=pos_bank_left)
        self.bank_left_proxy.set_locator_scale(scale=1)
        self.bank_left_proxy.add_line_parent(line_parent=self.toes_proxy)
        self.bank_left_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.PIVOT)
        self.bank_left_proxy.set_meta_purpose(value=bank_left_name)

        self.bank_right_proxy = tools_rig_frm.Proxy(name=bank_right_name)
        self.bank_right_proxy.start_position = pos_bank_right
        self.bank_right_proxy.set_initial_position(xyz=pos_bank_right)
        self.bank_right_proxy.set_locator_scale(scale=1)
        self.bank_right_proxy.add_line_parent(line_parent=self.toes_proxy)
        self.bank_right_proxy.add_color(rgb_color=core_color.ColorConstants.RigProxy.PIVOT)
        self.bank_right_proxy.set_meta_purpose(value=bank_right_name)

        # Update Proxies
        self.proxies = [
            self.upperleg_proxy,
            self.lowerleg_proxy,
            self.paw_proxy,
            self.toes_proxy,
            self.ball_proxy,
            self.toesend_proxy,
            self.heel_proxy,
            self.bank_left_proxy,
            self.bank_right_proxy,
        ]

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
        _dir_curves = [self.upperleg_dir_curve, self.lowerleg_dir_curve, self.paw_dir_curve]

        for dir_curve in _dir_curves:
            joint_name = dir_curve.get_short_name().replace("_dir", "_proxy_jnt")
            joint = core_node.create_node(node_type="joint", name=joint_name)
            cmds.delete(cmds.parentConstraint(dir_curve, joint))
            if coplane_joints:
                cmds.parent(joint, coplane_joints[-1])
            coplane_joints.append(joint)
        [cmds.makeIdentity(jnt, apply=True, rotate=True) for jnt in coplane_joints]

        return coplane_joints

    def create_pole_joints(self):
        """Create joints needed to build an Ik solver to ensure the pole vector direction for the proxies of the leg."""
        pole_joints = []
        upperleg_node = tools_rig_utils.find_proxy_from_uuid(self.upperleg_proxy.get_uuid())
        paw_node = tools_rig_utils.find_proxy_from_uuid(self.paw_proxy.get_uuid())
        _points = [upperleg_node, paw_node]

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
        paw_node = tools_rig_utils.find_proxy_from_uuid(self.paw_proxy.get_uuid())

        coplane_ik_handle = cmds.ikHandle(
            sj=coplane_joints[0], ee=coplane_joints[2], n=f"{coplane_prefix}_ikHandle", sol="ikRPsolver"
        )[0]
        coplane_ik_handle = core_node.Node(coplane_ik_handle)
        cmds.parent(coplane_joints[0], upperleg_node)
        cmds.parent(coplane_ik_handle, paw_node)

        pole_ik_handle = cmds.ikHandle(
            sj=pole_joints[0], ee=pole_joints[1], n=f"{pole_prefix}_ikHandle", sol="ikRPsolver"
        )[0]
        pole_ik_handle = core_node.Node(pole_ik_handle)
        cmds.parent(pole_joints[0], upperleg_node)
        cmds.parent(pole_ik_handle, paw_node)

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
        cmds.parentConstraint(paw_node, lower_end_loc, mo=False)
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
        super().get_proxies_mirrored(behaviour=True, specular=False)

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

    @staticmethod
    def create_knt_skeleton(source_joints, parent_grp, suffix):
        """
        Creates a chain of duplicate joints from the given source joints and parents them in sequence.

        Args:
            source_joints (list[str]): List of joint names to duplicate.
            parent_grp (str): The parent group or transform under which the first duplicated joint will be parented.
            suffix (str): Suffix to append to the name of each duplicated joint.

        Returns:
            list[str]: A list of duplicated joint names forming the new skeleton chain.
        """
        knt_joints = []
        for i, jnt in enumerate(source_joints):
            parent_obj = parent_grp
            if i > 0:
                parent_obj = knt_joints[-1]
            knt_jnt = core_rigging.duplicate_joint_for_automation(jnt, suffix=suffix, parent=parent_obj)
            knt_joints.append(knt_jnt)
        return knt_joints

    # ----------------------------------------------- Build Functions -------------------------------------------------
    def build_proxy(self, **kwargs):
        """
        Build proxy elements in the viewport
        Returns:
            list: A list of ProxyData objects. These objects describe the created proxy elements.
        """
        self.upperleg_proxy.parent_uuid = self.parent_uuid
        self.paw_proxy.parent_uuid = self.parent_uuid
        self.lowerleg_proxy.set_parent_uuid(self.paw_proxy.get_uuid())
        self.toes_proxy.set_parent_uuid(self.paw_proxy.get_uuid())
        self.ball_proxy.set_parent_uuid(self.toes_proxy.get_uuid())
        self.toesend_proxy.set_parent_uuid(self.ball_proxy.get_uuid())
        self.heel_proxy.set_parent_uuid(self.toes_proxy.get_uuid())
        self.bank_left_proxy.set_parent_uuid(self.toes_proxy.get_uuid())
        self.bank_right_proxy.set_parent_uuid(self.toes_proxy.get_uuid())
        [proxy.set_setup_driver_uuid(proxy.parent_uuid) for proxy in self.proxies if proxy.parent_uuid]
        proxy = super().build_proxy()  # Passthrough
        return proxy

    def build_proxy_setup(self):
        """
        Runs post proxy script.
        When in a project, this runs after the "build_proxy" is done in all modules.
        """

        # Get Maya Elements
        global_proxy = tools_rig_utils.find_ctrl_global_proxy()
        upperleg_node = tools_rig_utils.find_proxy_from_uuid(self.upperleg_proxy.get_uuid())
        lowerleg_node = tools_rig_utils.find_proxy_from_uuid(self.lowerleg_proxy.get_uuid())
        paw_node = tools_rig_utils.find_proxy_from_uuid(self.paw_proxy.get_uuid())
        toes_node = tools_rig_utils.find_proxy_from_uuid(self.toes_proxy.get_uuid())
        ball_node = tools_rig_utils.find_proxy_from_uuid(self.ball_proxy.get_uuid())
        toesend_node = tools_rig_utils.find_proxy_from_uuid(self.toesend_proxy.get_uuid())
        heel_node = tools_rig_utils.find_proxy_from_uuid(self.heel_proxy.get_uuid())
        bank_left_node = tools_rig_utils.find_proxy_from_uuid(self.bank_left_proxy.get_uuid())
        bank_right_node = tools_rig_utils.find_proxy_from_uuid(self.bank_right_proxy.get_uuid())
        _lowerleg_short_name = lowerleg_node.get_short_name()

        # Apply Initial World Orientation - in case the parent has a different one
        upperleg_offset = tools_rig_utils.get_proxy_offset(upperleg_node)
        paw_offset = tools_rig_utils.get_proxy_offset(paw_node)
        cmds.xform(upperleg_offset, ws=True, a=True, ro=(0, 0, 0))
        cmds.xform(paw_offset, ws=True, a=True, ro=(0, 0, 0))

        # Apply Initial Proxy Positions
        for proxy in self.get_proxies(sort_by="setup_driver"):
            proxy_node = tools_rig_utils.find_proxy_from_uuid(uuid_string=proxy.uuid)
            proxy_offset = tools_rig_utils.get_proxy_offset(proxy_node)
            _p_start_pos = proxy.start_position
            cmds.xform(proxy_offset, ws=True, a=True, t=(_p_start_pos.x, _p_start_pos.y, _p_start_pos.z))
            cmds.xform(proxy_node, ws=True, a=True, t=(_p_start_pos.x, _p_start_pos.y, _p_start_pos.z))

        # Build Direction Curves
        self.upperleg_dir_curve, upperleg_dir_curve_offset = self.create_direction_curve(
            self.upperleg_proxy, upperleg_node
        )
        core_attr.hide_lock_default_attrs(upperleg_dir_curve_offset, scale=True, rotate=True, translate=True)
        self.lowerleg_dir_curve, lowerleg_dir_curve_offset = self.create_direction_curve(
            self.lowerleg_proxy, lowerleg_node
        )
        self.paw_dir_curve, paw_dir_curve_offset = self.create_direction_curve(self.paw_proxy, paw_node)
        core_attr.hide_lock_default_attrs(paw_dir_curve_offset, scale=True, rotate=True, translate=True)

        # Direction Curves Starting Setup
        side_x_offset = 180
        paw_x_offset = -90 * self.orientation.get_aim_axis()[0]
        self.setup_direction_curve(self.upperleg_dir_curve, lowerleg_node, x_offset=side_x_offset)
        _dir_off_cnstr = cmds.orientConstraint(self.upperleg_dir_curve, lowerleg_dir_curve_offset, mo=False)
        self.setup_direction_curve(self.lowerleg_dir_curve, paw_node, x_offset=90, skip_axis=["x", "y"])
        self.setup_direction_curve(self.paw_dir_curve, toes_node, x_offset=paw_x_offset)

        # End Pivots
        toes_tag = toes_node.get_short_name()
        toesend_offset = tools_rig_utils.get_proxy_offset(toesend_node)
        pivot_driver = core_hrchy.create_group(name=f"{toes_tag}_pivot")
        pivot_driver = core_hrchy.parent(source_objects=pivot_driver, target_parent=global_proxy)[0]
        cmds.delete(cmds.pointConstraint(toes_node, pivot_driver))
        cmds.pointConstraint(toes_node, pivot_driver, maintainOffset=True, skip=["y"])
        cmds.orientConstraint(toes_node, pivot_driver, maintainOffset=True, skip=["x", "z"])
        cmds.scaleConstraint(toes_node, pivot_driver, skip=["y"])
        core_hrchy.parent(toesend_offset, pivot_driver)

        heel_offset = tools_rig_utils.get_proxy_offset(heel_node)
        core_hrchy.parent(heel_offset, pivot_driver)
        bank_left_offset = tools_rig_utils.get_proxy_offset(bank_left_node)
        core_hrchy.parent(bank_left_offset, pivot_driver)
        bank_right_offset = tools_rig_utils.get_proxy_offset(bank_right_node)
        core_hrchy.parent(bank_right_offset, pivot_driver)

        # Keep Grounded
        for to_lock_ty in [toesend_node, bank_left_node, bank_right_node, heel_node]:
            to_lock_ty = str(to_lock_ty)
            cmds.addAttr(to_lock_ty, ln="lockTranslateY", at="bool", k=True, niceName="Keep Grounded")
            cmds.setAttr(f"{to_lock_ty}.lockTranslateY", 0)
            cmds.setAttr(f"{to_lock_ty}.minTransYLimit", 0)
            cmds.setAttr(f"{to_lock_ty}.maxTransYLimit", 0)
            cmds.connectAttr(f"{to_lock_ty}.lockTranslateY", f"{to_lock_ty}.minTransYLimitEnable", f=True)
            cmds.connectAttr(f"{to_lock_ty}.lockTranslateY", f"{to_lock_ty}.maxTransYLimitEnable", f=True)

        # Build solver to ensure co-plane relation between upperLeg and paw
        coplane_joints = self.create_coplane_joints()
        pole_joints = self.create_pole_joints()
        self.setup_proxy_coplane(coplane_joints, pole_joints)
        cmds.delete(cmds.listRelatives(self.upperleg_dir_curve, children=True, type="aimConstraint")[0])
        cmds.delete(cmds.listRelatives(self.lowerleg_dir_curve, children=True, type="aimConstraint")[0])
        cmds.delete(_dir_off_cnstr)
        cmds.orientConstraint(coplane_joints[0], self.upperleg_dir_curve, mo=False)
        cmds.orientConstraint(coplane_joints[1], self.lowerleg_dir_curve, mo=False)
        _pole_aim = cmds.orientConstraint(pole_joints[0], lowerleg_node, mo=False)[0]
        cmds.setAttr(f"{_pole_aim}.offsetX", 270)
        cmds.setAttr(f"{_pole_aim}.offsetY", -180)

        # Lock Proxy Attributes
        proxies_with_rotation = [self.paw_proxy, self.toes_proxy]
        proxies_locked = list(set(self.proxies) - set(proxies_with_rotation))
        for mod_proxy in proxies_with_rotation:
            proxy_node = tools_rig_utils.find_proxy_from_uuid(mod_proxy.get_uuid())
            core_attr.hide_lock_default_attrs(proxy_node, scale=True)
            cmds.setAttr(f"{proxy_node}.rx", lock=True, keyable=False, channelBox=False)
            cmds.setAttr(f"{proxy_node}.rz", lock=True, keyable=False, channelBox=False)
        for mod_proxy in proxies_locked:
            proxy_node = tools_rig_utils.find_proxy_from_uuid(mod_proxy.get_uuid())
            core_attr.hide_lock_default_attrs(proxy_node, rotate=True, scale=True)
        cmds.setAttr(f"{ball_node}.tx", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{toesend_node}.tx", lock=True, keyable=False, channelBox=False)
        cmds.setAttr(f"{heel_node}.tx", lock=True, keyable=False, channelBox=False)

        # Apply Stored Transforms
        [proxy.apply_transforms() for proxy in self.get_proxies(sort_by="setup_driver")]
        _only_translation_proxies = [upperleg_node, lowerleg_node]
        [cmds.rotate(0, 0, 0, proxy, a=True) for proxy in _only_translation_proxies]

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
        # Get joints
        upperleg_jnt = tools_rig_utils.find_joint_from_uuid(self.upperleg_proxy.get_uuid())
        lowerleg_jnt = tools_rig_utils.find_joint_from_uuid(self.lowerleg_proxy.get_uuid())
        paw_jnt = tools_rig_utils.find_joint_from_uuid(self.paw_proxy.get_uuid())
        toes_jnt = tools_rig_utils.find_joint_from_uuid(self.toes_proxy.get_uuid())
        ball_jnt = tools_rig_utils.find_joint_from_uuid(self.ball_proxy.get_uuid())
        toesend_jnt = tools_rig_utils.find_joint_from_uuid(self.toesend_proxy.get_uuid())

        # Inherit rotation and rotation order
        for proxy in self.proxies:
            joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            if not joint:
                continue
            proxy_obj_path = tools_rig_utils.find_proxy_from_uuid(proxy.get_uuid())
            proxy_rotation_order = cmds.getAttr(f"{proxy_obj_path}.{tools_rig_const.RiggerConstants.ATTR_ROT_ORDER}")
            cmds.setAttr(f"{joint}.rotateOrder", proxy_rotation_order)
            if proxy == self.upperleg_proxy:
                proxy_obj_path = self.upperleg_dir_curve
            elif proxy == self.lowerleg_proxy:
                proxy_obj_path = self.lowerleg_dir_curve
            elif proxy == self.paw_proxy:
                proxy_obj_path = self.paw_dir_curve
            cmds.delete(cmds.orientConstraint(proxy_obj_path, joint))
            cmds.makeIdentity(joint, a=True, r=True)

        # Parent joints
        parent_uuid = self.upperleg_proxy.get_parent_uuid()
        if parent_uuid:
            parent_joint_node = tools_rig_utils.find_joint_from_uuid(parent_uuid)
            core_hrchy.parent(source_objects=upperleg_jnt, target_parent=parent_joint_node)
        core_hrchy.parent(source_objects=lowerleg_jnt, target_parent=upperleg_jnt)
        core_hrchy.parent(source_objects=paw_jnt, target_parent=lowerleg_jnt)
        core_hrchy.parent(source_objects=toes_jnt, target_parent=paw_jnt)
        core_hrchy.parent(source_objects=ball_jnt, target_parent=toes_jnt)
        core_hrchy.parent(source_objects=toesend_jnt, target_parent=ball_jnt)
        cmds.select(clear=True)

        # Toes, Ball and ToesEnd
        cmds.parent(ball_jnt, w=True)
        cmds.parent(toesend_jnt, w=True)
        module_aim = self.orientation.get_aim_axis()
        module_up = (0, module_aim[0], 0)
        toes_node = tools_rig_utils.find_proxy_from_uuid(self.toes_proxy.get_uuid())
        _temp_toes_pv_dir = cmds.spaceLocator(name=f"{toes_node.get_short_name()}_temp_pv_dir")[0]
        core_trans.match_translate(source=toes_node, target_list=_temp_toes_pv_dir)
        cmds.move(10 * -module_up[1], 0, 0, _temp_toes_pv_dir, relative=True)
        core_hrchy.parent(_temp_toes_pv_dir, toes_node)
        self.orientation.set_aim_axis((-module_aim[0], 0, 0))
        self.orientation.set_world_aligned(world_aligned=True)
        self.orientation.apply_automatic_orientation(joint_list=[toes_jnt])
        self.orientation.set_aim_axis(module_aim)
        self.orientation.set_world_aligned(world_aligned=False)

        _toes_aim = cmds.aimConstraint(
            ball_jnt,
            toes_jnt,
            aimVector=module_aim,
            upVector=module_up,
            worldUpObject=_temp_toes_pv_dir,
            worldUpType="objectrotation",
            skip=["y", "z"],
        )[0]
        cmds.delete([_toes_aim, _temp_toes_pv_dir])
        cmds.makeIdentity(toes_jnt, apply=True, rotate=True)
        core_hrchy.parent(source_objects=ball_jnt, target_parent=toes_jnt)
        cmds.setAttr(f"{ball_jnt}.jo", 0, 0, 0)
        cmds.setAttr(f"{ball_jnt}.r", 0, 0, 0)
        core_hrchy.parent(source_objects=toesend_jnt, target_parent=ball_jnt)
        cmds.setAttr(f"{toesend_jnt}.jo", 0, 0, 0)
        cmds.setAttr(f"{toesend_jnt}.r", 0, 0, 0)

        # Create Twist Joints
        if self.create_twist_joints:
            upperleg_jnt = tools_rig_utils.find_joint_from_uuid(self.upperleg_proxy.get_uuid()).get_short_name()
            lowerleg_jnt = tools_rig_utils.find_joint_from_uuid(self.lowerleg_proxy.get_uuid()).get_short_name()
            paw_jnt = tools_rig_utils.find_joint_from_uuid(self.paw_proxy.get_uuid()).get_short_name()
            self.upperleg_twist_joints = tools_rig_utils.create_twist_joints(
                upperleg_jnt,
                lowerleg_jnt,
                copy_start=True,
            )
            self.lowerleg_twist_joints = tools_rig_utils.create_twist_joints(
                lowerleg_jnt,
                paw_jnt,
                copy_end=True,
            )

    def build_rig(self, project_prefix=None, **kwargs):
        """
        Build rig phase initializes the creation of controls or logic using the Proxy/Guide elements defined in the
        previous "build_proxy" step.
        Args:
            project_prefix (str, optional): If provided, the created elements receive this string as an extra prefix.
            **kwargs: Arbitrary keyword arguments used to allow override while maintaining parents requirements.
        """

        # Twist Setup
        if self.create_twist_joints:
            tools_rig_utils.create_twist_setup(
                twist_jnt_list=self.upperleg_twist_joints, mid_joints=2, side=self.prefix, reverse=True
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
        paw_jnt = tools_rig_utils.find_joint_from_uuid(self.paw_proxy.get_uuid())
        toes_jnt = tools_rig_utils.find_joint_from_uuid(self.toes_proxy.get_uuid())
        ball_jnt = tools_rig_utils.find_joint_from_uuid(self.ball_proxy.get_uuid())
        toesend_jnt = tools_rig_utils.find_joint_from_uuid(self.toesend_proxy.get_uuid())
        module_jnt_list = [upperleg_jnt, lowerleg_jnt, paw_jnt, toes_jnt, ball_jnt, toesend_jnt]

        # Set Joints Colors
        [core_color.set_color_viewport(obj_list=jnt, rgb_color=(0.3, 0.3, 0)) for jnt in module_jnt_list]

        # Get General Scale
        quad_leg_scale = core_math.dist_center_to_center(upperleg_jnt, lowerleg_jnt)
        quad_leg_scale += core_math.dist_center_to_center(lowerleg_jnt, paw_jnt)

        # Create Parent Automation Elements
        joint_automation_grp = tools_rig_utils.find_or_create_joint_automation_group()
        general_automation_grp = tools_rig_utils.get_automation_group()
        module_parent_jnt = tools_rig_utils.get_driven_joint(self.get_parent_uuid())
        if not module_parent_jnt:
            global_offset_name = global_offset_ctrl.get_short_name().replace("_CTRL", "_JNT")
            module_parent_jnt_name = f"{self.get_name().lower()}_{global_offset_name}_driver"
            module_parent_jnt = core_node.create_node(node_type="joint", name=module_parent_jnt_name)
            core_trans.match_transform(source=global_offset_ctrl, target_list=module_parent_jnt)
            cmds.makeIdentity(module_parent_jnt, apply=True, rotate=True)
            cmds.parentConstraint(global_offset_ctrl, module_parent_jnt)
        core_hrchy.parent(source_objects=module_parent_jnt, target_parent=joint_automation_grp)

        # Create Automation Skeletons (FK/IK)
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

        fk_joints = self.create_knt_skeleton(module_jnt_list, upperleg_parent, "fk")
        upperleg_fk_jnt = fk_joints[0]
        lowerleg_fk_jnt = fk_joints[1]
        paw_fk_jnt = fk_joints[2]
        toes_fk_jnt = fk_joints[3]
        ball_fk_jnt = fk_joints[4]
        toesend_fk_jnt = fk_joints[5]

        ik_joints = self.create_knt_skeleton(module_jnt_list, upperleg_parent, "ik")
        upperleg_ik_jnt = ik_joints[0]
        lowerleg_ik_jnt = ik_joints[1]
        paw_ik_jnt = ik_joints[2]
        toes_ik_jnt = ik_joints[3]
        ball_ik_jnt = ik_joints[4]
        toesend_ik_jnt = ik_joints[5]

        core_rigging.rescale_joint_radius(
            joint_list=fk_joints,
            multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_FK,
        )
        core_rigging.rescale_joint_radius(
            joint_list=ik_joints,
            multiplier=tools_rig_const.RiggerConstants.LOC_RADIUS_MULTIPLIER_IK,
        )
        core_color.set_color_viewport(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigJoint.FK)
        core_color.set_color_viewport(obj_list=ik_joints, rgb_color=core_color.ColorConstants.RigJoint.IK)
        core_color.set_color_outliner(obj_list=fk_joints, rgb_color=core_color.ColorConstants.RigOutliner.FK)
        core_color.set_color_outliner(obj_list=ik_joints, rgb_color=core_color.ColorConstants.RigOutliner.IK)

        # FK Controls ----------------------------------------------------------------------------------------
        fk_offsets_ctrls = []
        # UpperLeg FK Control
        upperleg_fk_ctrl, upperleg_fk_groups = self.create_rig_control(
            control_base_name=self.upperleg_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=global_offset_ctrl,
            match_obj=upperleg_jnt,
            add_offset_ctrl=False,
            rot_order=cmds.getAttr(f"{upperleg_jnt}.rotateOrder"),
            shape_scale=quad_leg_scale * 0.2,
            color=core_color.get_directional_color(object_name=upperleg_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=upperleg_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.upperleg_proxy,
        )

        core_cnstr.constraint_targets(source_driver=upperleg_fk_ctrl, target_driven=upperleg_fk_jnt)
        fk_offsets_ctrls.append(upperleg_fk_groups[0])

        # LowerLeg FK Control
        lowerleg_fk_ctrl, lowerleg_fk_groups = self.create_rig_control(
            control_base_name=self.lowerleg_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=upperleg_fk_ctrl,
            match_obj=lowerleg_jnt,
            add_offset_ctrl=False,
            rot_order=cmds.getAttr(f"{lowerleg_jnt}.rotateOrder"),
            shape_scale=quad_leg_scale * 0.16,
            color=core_color.get_directional_color(object_name=lowerleg_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=lowerleg_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.lowerleg_proxy,
        )
        core_cnstr.constraint_targets(source_driver=lowerleg_fk_ctrl, target_driven=lowerleg_fk_jnt)
        fk_offsets_ctrls.append(lowerleg_fk_groups[0])

        # Paw FK Control
        paw_fk_ctrl, paw_fk_groups = self.create_rig_control(
            control_base_name=self.paw_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=lowerleg_fk_ctrl,
            match_obj=paw_jnt,
            add_offset_ctrl=False,
            rot_order=cmds.getAttr(f"{paw_jnt}.rotateOrder"),
            shape_scale=quad_leg_scale * 0.14,
            color=core_color.get_directional_color(object_name=paw_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=paw_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.paw_proxy,
        )
        core_cnstr.constraint_targets(source_driver=paw_fk_ctrl, target_driven=paw_fk_jnt)
        fk_offsets_ctrls.append(paw_fk_groups[0])

        # Toes FK Control
        toes_fk_ctrl, toes_fk_groups = self.create_rig_control(
            control_base_name=self.toes_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=paw_fk_ctrl,
            rot_order=cmds.getAttr(f"{toes_jnt}.rotateOrder"),
            match_obj=toes_jnt,
            add_offset_ctrl=False,
            shape_scale=quad_leg_scale * 0.1,
            color=core_color.get_directional_color(object_name=toes_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=toes_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.toes_proxy,
        )
        core_cnstr.constraint_targets(source_driver=toes_fk_ctrl, target_driven=toes_fk_jnt)
        fk_offsets_ctrls.append(toes_fk_groups[0])

        # Ball FK Control
        ball_fk_ctrl, ball_fk_groups = self.create_rig_control(
            control_base_name=self.ball_proxy.get_name(),
            curve_file_name="_circle_pos_x",
            parent_obj=toes_fk_ctrl,
            rot_order=cmds.getAttr(f"{ball_jnt}.rotateOrder"),
            match_obj=ball_jnt,
            shape_scale=quad_leg_scale * 0.09,
            color=core_color.get_directional_color(object_name=ball_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=ball_fk_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.FK,
            proxy_purpose=self.ball_proxy,
        )
        core_cnstr.constraint_targets(source_driver=ball_fk_ctrl, target_driven=ball_fk_jnt)
        fk_offsets_ctrls.append(ball_fk_groups[0])

        # IK Controls --------------------------------------------------------------------------------------
        ik_offsets_ctrls = []

        # IK LowerLeg Control
        ik_suffix = core_naming.NamingConstants.Description.IK.upper()
        lowerleg_ik_ctrl, lowerleg_ik_offset = self.create_rig_control(
            control_base_name=f"{self.lowerleg_proxy.get_name()}_{ik_suffix}",
            curve_file_name="primitive_diamond",
            parent_obj=global_offset_ctrl,
            match_obj_pos=paw_jnt,
            shape_scale=quad_leg_scale * 0.05,
            color=core_color.get_directional_color(object_name=paw_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=lowerleg_ik_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=self.lowerleg_proxy,
        )
        ik_offsets_ctrls.append(lowerleg_ik_offset[0])

        # Find Pole Vector Position
        lowerleg_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.lowerleg_proxy.get_uuid())
        temp_transform = core_hrchy.create_group(name=f"{lowerleg_ik_ctrl.get_short_name()}_rotExtraction")
        cmds.delete(cmds.parentConstraint(lowerleg_proxy, temp_transform, mo=False))
        cmds.move(0, 0, -quad_leg_scale * 0.5, temp_transform, objectSpace=True, relative=True)
        cmds.delete(cmds.pointConstraint(temp_transform, lowerleg_ik_offset[0]))
        cmds.delete(temp_transform)

        # IK Aim Line
        tools_rig_utils.create_control_visualization_line(lowerleg_ik_ctrl, lowerleg_ik_jnt)

        # IK Toes Control
        toes_projection = cmds.xform(toes_jnt, ws=True, t=True, q=True)[1]
        _is_right_side = 0
        _right_side_mult = -1
        if self.prefix == core_naming.NamingConstants.Prefix.RIGHT:
            _is_right_side = 1
            _right_side_mult = 1
            rot_offset = (0, 0, 180)
        else:
            rot_offset = (0, 0, 0)

        toes_base_name = f"{self.toes_proxy.get_name()}_{ik_suffix}"
        toes_ik_ctrl, toes_ik_groups = self.create_rig_control(
            control_base_name=toes_base_name,
            curve_file_name="_square_pos_x",
            parent_obj=global_offset_ctrl,
            rot_order=1,
            match_obj_pos=toes_jnt,
            add_offset_ctrl=False,
            shape_scale=quad_leg_scale * 0.5,
            shape_rot_offset=(0, 0, 90),
            shape_pos_offset=(-toes_projection, 0, 0),
            color=core_color.get_directional_color(object_name=toes_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=toes_ik_ctrl, driver_type=tools_rig_const.RiggerDriverTypes.IK, proxy_purpose=self.toes_proxy
        )

        # -- Specific offset rotation control to retain the orientation of the toes joint
        toes_ik_rot_ctrl, toes_ik_rot_groups = self.create_rig_control(
            control_base_name=f"{toes_base_name}Rotation",
            curve_file_name="sphere_half_top_four_arrows",
            parent_obj=toes_ik_ctrl,
            rot_order=1,
            match_obj=toes_jnt,
            add_offset_ctrl=False,
            shape_scale=quad_leg_scale * 0.1,
            shape_rot_offset=(0, 0, 180 * (not _is_right_side)),
            shape_pos_offset=(0, quad_leg_scale * 0.1, 0),
            color=core_color.get_directional_color(object_name=toes_jnt),
        )[:2]
        cmds.addAttr(toes_ik_ctrl, ln="showRotOffsetCtrl", at="bool", k=True)
        cmds.connectAttr(f"{toes_ik_ctrl}.showRotOffsetCtrl", f"{toes_ik_rot_ctrl}.v")
        core_attr.hide_lock_default_attrs([toes_ik_rot_ctrl], translate=True, scale=True, visibility=True)
        self._add_driver_uuid_attr(
            target_driver=toes_ik_rot_ctrl,
            driver_type=tools_rig_const.RiggerDriverTypes.IK,
            proxy_purpose=f"{self.toes_proxy.get_name()}Rotation",
        )

        offset_data_suffix = core_naming.NamingConstants.Description.OFFSET_DATA
        toes_data_group = self.create_control_groups(
            toes_ik_rot_ctrl,
            control_base_name=f"{toes_base_name}Rotation",
            parent_obj=toes_ik_ctrl,
            suffix_list=offset_data_suffix,
        )[0]
        cmds.orientConstraint(toes_ik_rot_ctrl, toes_data_group, mo=True)

        # Connection with joint
        cmds.orientConstraint(toes_data_group, toes_ik_jnt, mo=True)
        ik_offsets_ctrls.append(toes_ik_groups[0])

        # Switch Control
        toes_proxy_node = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.toes_proxy.get_uuid())
        ik_switch_ctrl, ik_switch_offset = self.create_rig_control(
            control_base_name=self.setup_name,
            curve_file_name="gear_eight_sides_smooth",
            parent_obj=global_ctrl,
            match_obj=toes_proxy_node,
            add_offset_ctrl=False,
            shape_pos_offset=(0, 0, quad_leg_scale * -0.3),
            shape_rot_offset=(0, 0, 90),
            shape_scale=quad_leg_scale * 0.016,
            color=core_color.get_directional_color(object_name=toes_jnt),
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
            prefix=f"{self.prefix}_",
            invert=True,
        )

        switch_cons = core_cnstr.constraint_targets(
            source_driver=[toes_fk_ctrl, toes_data_group], target_driven=ik_switch_offset
        )[0]
        leg_rev_name = f"{self._assemble_node_name('leg_rev')}"
        leg_rev = cmds.createNode("reverse", name=leg_rev_name)
        cmds.connectAttr(f"{ik_switch_ctrl}.influenceSwitch", f"{leg_rev}.inputX")
        cmds.connectAttr(f"{leg_rev}.outputX", f"{switch_cons}.w0")
        cmds.connectAttr(f"{ik_switch_ctrl}.influenceSwitch", f"{switch_cons}.w1")

        influence_switch_attr_nice_name = "FK/IK"
        cmds.addAttr(f"{ik_switch_ctrl}.influenceSwitch", e=True, nn=influence_switch_attr_nice_name)
        cmds.setAttr(f"{ik_switch_ctrl}.influenceSwitch", 0)  # Default is FK

        # Toes Pivots
        toes_automation_grp_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_automation_grp"
        toes_automation_grp = core_hrchy.create_group(name=toes_automation_grp_name)
        core_hrchy.parent(source_objects=toes_automation_grp, target_parent=general_automation_grp)

        toes_pivot_grp_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_pivot_grp"
        toes_pivot_grp = core_hrchy.create_group(name=toes_pivot_grp_name)
        core_trans.match_transform(source=toes_jnt, target_list=toes_pivot_grp)
        core_hrchy.parent(source_objects=toes_pivot_grp, target_parent=toes_automation_grp)
        cmds.parentConstraint(toes_data_group, toes_pivot_grp)

        bank_left_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.bank_left_proxy.get_uuid())
        bank_left_pivot_grp_name = f"{self._assemble_node_name(self.bank_left_proxy.get_name())}_pivot_grp"
        bank_left_offset_grp_name = f"{self._assemble_node_name(self.bank_left_proxy.get_name())}_pivotOffset_grp"
        bank_left_offset_group = core_hrchy.create_group(name=bank_left_offset_grp_name)
        core_trans.match_transform(source=bank_left_proxy, target_list=bank_left_offset_group)
        core_hrchy.parent(source_objects=bank_left_offset_group, target_parent=toes_pivot_grp)
        bank_left_pivot_grp = core_hrchy.create_group(name=bank_left_pivot_grp_name)
        core_trans.match_transform(source=bank_left_proxy, target_list=bank_left_pivot_grp)
        core_hrchy.parent(source_objects=bank_left_pivot_grp, target_parent=bank_left_offset_group)

        bank_right_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.bank_right_proxy.get_uuid())
        bank_left_pivot_grp_name = f"{self._assemble_node_name(self.bank_right_proxy.get_name())}_pivot_grp"
        bank_right_pivot_grp = core_hrchy.create_group(name=bank_left_pivot_grp_name)
        core_trans.match_transform(source=bank_right_proxy, target_list=bank_right_pivot_grp)
        core_hrchy.parent(source_objects=bank_right_pivot_grp, target_parent=bank_left_pivot_grp)

        heel_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.heel_proxy.get_uuid())
        heel_pivot_grp_name = f"{self._assemble_node_name(self.heel_proxy.get_name())}_pivot_grp"
        heel_pivot_grp = core_hrchy.create_group(name=heel_pivot_grp_name)
        core_trans.match_transform(source=heel_proxy, target_list=heel_pivot_grp)
        core_hrchy.parent(source_objects=heel_pivot_grp, target_parent=bank_right_pivot_grp)

        ball_twist_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.ball_proxy.get_uuid())
        ball_twist_pivot_grp_name = f"{self._assemble_node_name(self.ball_proxy.get_name())}Twist_pivot_grp"
        ball_twist_pivot_grp = core_hrchy.create_group(name=ball_twist_pivot_grp_name)
        core_trans.match_transform(source=ball_twist_proxy, target_list=ball_twist_pivot_grp)
        core_hrchy.parent(source_objects=ball_twist_pivot_grp, target_parent=heel_pivot_grp)

        core_trans.match_transform(source=ball_twist_proxy, target_list=ball_twist_pivot_grp)
        core_hrchy.parent(source_objects=ball_twist_pivot_grp, target_parent=heel_pivot_grp)

        toesend_node = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.toesend_proxy.get_uuid())
        toesend_pivot_grp_name = f"{self._assemble_node_name(self.toesend_proxy.get_name())}_pivot_grp"
        toesend_pivot_grp = core_hrchy.create_group(name=toesend_pivot_grp_name)
        core_trans.match_transform(source=toesend_node, target_list=toesend_pivot_grp)
        core_hrchy.parent(source_objects=toesend_pivot_grp, target_parent=ball_twist_pivot_grp)

        ball_proxy = tools_rig_utils.find_proxy_from_uuid(uuid_string=self.ball_proxy.get_uuid())
        ball_pivot_grp_name = f"{self._assemble_node_name(self.ball_proxy.get_name())}_pivot_grp"
        ball_pivot_grp = core_hrchy.create_group(name=ball_pivot_grp_name)
        core_trans.match_transform(source=ball_proxy, target_list=ball_pivot_grp)
        core_hrchy.parent(source_objects=ball_pivot_grp, target_parent=toesend_pivot_grp)

        paw_pivot_grp_name = f"{self._assemble_node_name(self.paw_proxy.get_name())}_pivot_grp"
        paw_pivot_grp = core_hrchy.create_group(name=paw_pivot_grp_name)
        core_trans.match_transform(source=paw_jnt, target_list=paw_pivot_grp)
        core_hrchy.parent(source_objects=paw_pivot_grp, target_parent=ball_pivot_grp)
        core_trans.match_translate(source=toes_jnt, target_list=paw_pivot_grp)
        paw_auto_orient_grp_name = f"{self._assemble_node_name(self.paw_proxy.get_name())}Auto_orient_grp"
        paw_auto_orient_grp = core_hrchy.create_group(name=paw_auto_orient_grp_name)
        paw_pivot_offset_grp_name = f"{self._assemble_node_name(self.paw_proxy.get_name())}Offset_pivot_grp"
        paw_pivot_offset_grp = core_hrchy.create_group(name=paw_pivot_offset_grp_name)
        core_trans.match_transform(source=paw_pivot_grp, target_list=paw_auto_orient_grp)
        core_trans.match_transform(source=paw_pivot_grp, target_list=paw_pivot_offset_grp)
        core_hrchy.parent(source_objects=paw_auto_orient_grp, target_parent=paw_pivot_grp)
        core_hrchy.parent(source_objects=paw_pivot_offset_grp, target_parent=paw_auto_orient_grp)

        ball_fk_ctrl_offset_name = f"{self._assemble_node_name(self.ball_proxy.get_name())}FK_ctrl_offset"
        ball_fk_ctrl_offset = core_hrchy.create_group(name=ball_fk_ctrl_offset_name)
        core_trans.match_transform(source=ball_proxy, target_list=ball_fk_ctrl_offset)
        core_hrchy.parent(source_objects=ball_fk_ctrl_offset, target_parent=toesend_pivot_grp)
        ball_fk_ctrl_grp_name = f"{self._assemble_node_name(self.toesend_proxy.get_name())}FK_ctrl"
        ball_fk_ctrl_grp = core_hrchy.create_group(name=ball_fk_ctrl_grp_name)
        core_trans.match_transform(source=ball_proxy, target_list=ball_fk_ctrl_grp)
        core_hrchy.parent(source_objects=ball_fk_ctrl_grp, target_parent=ball_fk_ctrl_offset)
        ball_fk_pivot_grp_name = f"{self._assemble_node_name(self.toesend_proxy.get_name())}FK_pivot_grp"
        ball_fk_pivot_grp = core_hrchy.create_group(name=ball_fk_pivot_grp_name)
        core_trans.match_transform(source=toesend_fk_jnt, target_list=ball_fk_pivot_grp)
        core_hrchy.parent(source_objects=ball_fk_pivot_grp, target_parent=ball_fk_ctrl_grp)

        # Toes Automation
        cmds.addAttr(toes_ik_ctrl, ln="kneeTwist", nn="Knee Twist", at="float", keyable=True)
        cmds.addAttr(toes_ik_ctrl, ln="footRolls", nn="Foot Rolls", at="enum", en="-------------:", keyable=True)
        cmds.setAttr(f"{toes_ik_ctrl}.footRolls", lock=True)
        cmds.addAttr(toes_ik_ctrl, ln="footRollWeight", nn="Foot Roll Weight", at="float", keyable=True, min=0, max=1.0)
        cmds.addAttr(toes_ik_ctrl, ln="footRoll", nn="Foot Roll", at="float", keyable=True)

        toes_weight_rev_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_footWeight_rev"
        toes_weight_rev = cmds.createNode("reverse", n=toes_weight_rev_name)
        cmds.connectAttr(f"{toes_ik_ctrl}.footRollWeight", f"{toes_weight_rev}.inputX")

        toes_roll_clamp_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_footRoll_clamp"
        toes_roll_clamp = cmds.createNode("clamp", n=toes_roll_clamp_name)
        cmds.connectAttr(f"{toes_ik_ctrl}.footRoll", f"{toes_roll_clamp}.inputR")
        cmds.connectAttr(f"{toes_ik_ctrl}.footRoll", f"{toes_roll_clamp}.inputG")
        cmds.setAttr(f"{toes_roll_clamp}.minR", -180)
        cmds.setAttr(f"{toes_roll_clamp}.maxG", 180)

        toes_mult_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_footWeight_mult"
        toes_mult = cmds.createNode("multiplyDivide", n=toes_mult_name)
        cmds.connectAttr(f"{toes_weight_rev}.outputX", f"{toes_mult}.input2X")
        cmds.connectAttr(f"{toes_ik_ctrl}.footRoll", f"{toes_mult}.input1Y")
        cmds.connectAttr(f"{toes_roll_clamp}.outputG", f"{toes_mult}.input1X")
        cmds.connectAttr(f"{toes_ik_ctrl}.footRollWeight", f"{toes_mult}.input2Y")

        cmds.addAttr(toes_ik_ctrl, ln="sideRoll", nn="Side Roll", at="float", keyable=True)
        toes_side_roll_clamp_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_sideRoll_clamp"
        toes_side_roll_clamp = cmds.createNode("clamp", n=toes_side_roll_clamp_name)
        cmds.setAttr(f"{toes_side_roll_clamp}.minR", -1000)
        cmds.setAttr(f"{toes_side_roll_clamp}.maxG", 1000)
        cmds.connectAttr(f"{toes_ik_ctrl}.sideRoll", f"{toes_side_roll_clamp}.inputR")
        cmds.connectAttr(f"{toes_ik_ctrl}.sideRoll", f"{toes_side_roll_clamp}.inputG")
        toes_side_roll_rev_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_sideRoll_multRev"
        toes_side_roll_rev = cmds.createNode("multiplyDivide", n=toes_side_roll_rev_name)
        cmds.setAttr(f"{toes_side_roll_rev}.input2X", -1)
        cmds.setAttr(f"{toes_side_roll_rev}.input2Y", -1)
        cmds.connectAttr(f"{toes_side_roll_clamp}.outputR", f"{toes_side_roll_rev}.input1X")
        cmds.connectAttr(f"{toes_side_roll_clamp}.outputG", f"{toes_side_roll_rev}.input1Y")
        cmds.connectAttr(f"{toes_side_roll_rev}.outputY", f"{bank_left_pivot_grp}.rotateZ")
        cmds.connectAttr(f"{toes_side_roll_rev}.outputX", f"{bank_right_pivot_grp}.rotateZ")

        cmds.addAttr(toes_ik_ctrl, ln="heelRoll", nn="Heel Roll", at="float", keyable=True)
        toes_heel_rev_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_heel_multRev"
        toes_heel_rev = cmds.createNode("multiplyDivide", n=toes_heel_rev_name)
        cmds.setAttr(f"{toes_heel_rev}.input2X", -1)
        toes_heel_add_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_heel_add"
        toes_heel_add = cmds.createNode("plusMinusAverage", n=toes_heel_add_name)
        cmds.setAttr(f"{toes_heel_add}.operation", 1)
        cmds.connectAttr(f"{toes_ik_ctrl}.heelRoll", f"{toes_heel_rev}.input1X")
        cmds.connectAttr(f"{toes_heel_rev}.outputX", f"{toes_heel_add}.input3D[1].input3Dx")
        cmds.connectAttr(f"{toes_roll_clamp}.outputR", f"{toes_heel_add}.input3D[2].input3Dx")
        cmds.connectAttr(f"{toes_heel_add}.output3D.output3Dx", f"{heel_pivot_grp}.rotateX")

        cmds.addAttr(toes_ik_ctrl, ln="ballRoll", nn="Ball Roll", at="float", keyable=True)
        toes_ball_add_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_ball_add"
        toes_ball_add = cmds.createNode("plusMinusAverage", n=toes_ball_add_name)
        cmds.setAttr(f"{toes_ball_add}.operation", 1)
        cmds.connectAttr(f"{toes_ik_ctrl}.ballRoll", f"{toes_ball_add}.input3D[1].input3Dx")
        cmds.connectAttr(f"{toes_mult}.outputX", f"{toes_ball_add}.input3D[2].input3Dx")
        cmds.connectAttr(f"{toes_ball_add}.output3D.output3Dx", f"{ball_pivot_grp}.rotateX")

        cmds.addAttr(toes_ik_ctrl, ln="tipRoll", nn="Tip Roll", at="float", keyable=True)
        toes_toesend_add_name = f"{self._assemble_node_name(self.toes_proxy.get_name())}_toesend_add"
        toes_toesend_add = cmds.createNode("plusMinusAverage", n=toes_toesend_add_name)
        cmds.setAttr(f"{toes_toesend_add}.operation", 1)
        cmds.connectAttr(f"{toes_ik_ctrl}.tipRoll", f"{toes_toesend_add}.input3D[1].input3Dx")
        cmds.connectAttr(f"{toes_mult}.outputY", f"{toes_toesend_add}.input3D[2].input3Dx")
        cmds.connectAttr(f"{toes_toesend_add}.output3D.output3Dx", f"{toesend_pivot_grp}.rotateX")

        cmds.addAttr(toes_ik_ctrl, ln="heelPivot", nn="Heel Pivot", at="float", keyable=True)
        cmds.connectAttr(f"{toes_ik_ctrl}.heelPivot", f"{heel_pivot_grp}.rotateY")

        cmds.addAttr(toes_ik_ctrl, ln="ballPivot", nn="Ball Pivot", at="float", keyable=True)
        cmds.connectAttr(f"{toes_ik_ctrl}.ballPivot", f"{ball_pivot_grp}.rotateY")

        cmds.addAttr(toes_ik_ctrl, ln="toePivot", nn="Toe Pivot", at="float", keyable=True)
        cmds.connectAttr(f"{toes_ik_ctrl}.toePivot", f"{ball_twist_pivot_grp}.rotateY")

        cmds.addAttr(toes_ik_ctrl, ln="tipPivot", nn="Tip Pivot", at="float", keyable=True)
        cmds.connectAttr(f"{toes_ik_ctrl}.tipPivot", f"{toesend_pivot_grp}.rotateY")

        cmds.addAttr(toes_ik_ctrl, ln="toeUpDown", nn="Toe Up Down", at="float", keyable=True)
        cmds.connectAttr(f"{toes_ik_ctrl}.toeUpDown", f"{ball_fk_pivot_grp}.translateY")

        # Paw IK Control
        _paw_toes_distance = core_math.dist_center_to_center(paw_jnt, toes_jnt)
        paw_ik_ctrl, paw_ik_groups = self.create_rig_control(
            control_base_name=f"{self.paw_proxy.get_name()}_{ik_suffix}",
            curve_file_name="quad_shell",
            parent_obj=toes_ik_groups[0],
            rot_order=0,
            match_obj_rot=paw_jnt,
            match_obj_pos=toes_jnt,
            shape_scale=quad_leg_scale * 0.02,
            shape_pos_offset=(0, _paw_toes_distance * 1.3, 0),
            shape_rot_offset=(70, 90, 180 * (not _is_right_side)),
            color=core_color.get_directional_color(object_name=paw_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=paw_ik_ctrl, driver_type=tools_rig_const.RiggerDriverTypes.IK, proxy_purpose=self.paw_proxy
        )
        cmds.pointConstraint(toes_ik_ctrl, paw_ik_groups[0], mo=True)
        cmds.connectAttr(f"{paw_ik_ctrl}.ry", f"{paw_pivot_offset_grp}.ry")
        cmds.connectAttr(f"{paw_ik_ctrl}.rz", f"{paw_pivot_offset_grp}.rz")

        # Ball IK Toe Control
        ball_projection = cmds.xform(ball_jnt, ws=True, t=True, q=True)[1]
        ball_ik_ctrl, ball_ik_ctrl_groups = self.create_rig_control(
            control_base_name=f"{self.ball_proxy.get_name()}_{ik_suffix}",
            curve_file_name="quad_paw_front",
            parent_obj=toes_data_group,
            rot_order=0,
            match_obj=ball_jnt,
            add_offset_ctrl=False,
            shape_scale=quad_leg_scale * 0.02,
            shape_pos_offset=(0, -ball_projection, 3),
            shape_rot_offset=(90, 90, 180 * (not _is_right_side)),
            color=core_color.get_directional_color(object_name=toes_jnt),
        )[:2]
        self._add_driver_uuid_attr(
            target_driver=ball_ik_ctrl, driver_type=tools_rig_const.RiggerDriverTypes.IK, proxy_purpose=self.ball_proxy
        )
        cmds.parentConstraint(ball_pivot_grp, ball_ik_ctrl_groups[0], mo=True)
        cmds.orientConstraint(ball_ik_ctrl, ball_fk_ctrl_grp, mo=True)
        cmds.addAttr(
            ik_switch_ctrl, ln="pawAutomation", nn="Paw Automation", at="enum", en="-------------:", keyable=True
        )
        cmds.setAttr(f"{ik_switch_ctrl}.pawAutomation", lock=True)
        cmds.addAttr(
            ik_switch_ctrl, ln="fullBallCtrlVisibility", nn="Full Ball Ctrl Visibility", at="bool", keyable=True
        )
        cmds.connectAttr(f"{ik_switch_ctrl}.fullBallCtrlVisibility", f"{ball_ik_ctrl_groups[0]}.visibility")

        # Paw IK Handle
        paw_ik_handle = cmds.ikHandle(
            sj=upperleg_ik_jnt,
            ee=paw_ik_jnt,
            n=f"{self._assemble_node_name(self.paw_proxy.get_name())}_ikHandle",
            sol="ikRPsolver",
        )[0]
        paw_ik_handle = core_node.Node(paw_ik_handle)
        cmds.poleVectorConstraint(lowerleg_ik_ctrl, paw_ik_handle)
        core_hrchy.parent(source_objects=paw_ik_handle, target_parent=paw_pivot_offset_grp)

        # Pole Vector Automation
        auto_pole_prefix = f"{self._assemble_node_name(self.paw_proxy.get_name())}Auto_pole"
        auto_pole_joints = self.create_knt_skeleton(
            [upperleg_jnt, toes_jnt], joint_automation_grp, f"{auto_pole_prefix}_ik"
        )
        auto_pole_ik_handle = cmds.ikHandle(
            sj=auto_pole_joints[0],
            ee=auto_pole_joints[1],
            n=f"{auto_pole_prefix}_ikHandle",
            sol="ikSCsolver",
        )[0]
        auto_pole_joint_node = core_node.Node(auto_pole_joints[0])
        core_attr.add_attr(
            obj_list=auto_pole_joint_node,
            attributes=tools_rig_const.RiggerConstants.ATTR_BASE_NAME,
            attr_type="string",
        )
        core_attr.set_attr(
            obj_list=auto_pole_joint_node,
            attr_list=tools_rig_const.RiggerConstants.ATTR_BASE_NAME,
            value=f"auto_{self.toes_proxy.get_name()}",
        )
        cmds.parentConstraint(module_parent_jnt, auto_pole_joints[0], mo=True)
        core_hrchy.parent(source_objects=auto_pole_ik_handle, target_parent=general_automation_grp)
        cmds.pointConstraint(toes_data_group, auto_pole_ik_handle)

        # Paw Orient Automation
        auto_orient_source_joints = [upperleg_jnt, paw_jnt, toes_jnt]
        auto_orient_prefix = f"{self._assemble_node_name(self.paw_proxy.get_name())}Auto_orient"
        auto_orient_joints = self.create_knt_skeleton(
            auto_orient_source_joints,
            joint_automation_grp,
            f"{auto_orient_prefix}_ik",
        )
        _auto_orient_x = quad_leg_scale * 0.5 * _right_side_mult
        cmds.move(_auto_orient_x, 0, 0, auto_orient_joints[1], objectSpace=True, relative=True)
        cmds.delete(cmds.parentConstraint(toes_jnt, auto_orient_joints[2]))
        auto_paw_ik_handle = cmds.ikHandle(
            sj=auto_orient_joints[0],
            ee=auto_orient_joints[2],
            n=f"{auto_orient_prefix}_ikHandle",
            sol="ikSCsolver",
        )[0]
        cmds.parentConstraint(module_parent_jnt, auto_orient_joints[0], mo=True)
        core_hrchy.parent(source_objects=auto_paw_ik_handle, target_parent=ball_pivot_grp)
        cmds.orientConstraint(auto_orient_joints[1], paw_ik_groups[0], mo=True)
        cmds.orientConstraint(auto_orient_joints[1], paw_auto_orient_grp)

        # Toes IK Handle
        toes_ik_handle = cmds.ikHandle(
            sj=paw_ik_jnt,
            ee=toes_ik_jnt,
            n=f"{self._assemble_node_name(self.toes_proxy.get_name())}_ikHandle",
            sol="ikSCsolver",
        )[0]
        core_hrchy.parent(source_objects=toes_ik_handle, target_parent=ball_pivot_grp)

        # Knee Twist Ctrl Functionality
        twist_grp_name = f"{self._assemble_node_name(self.lowerleg_proxy.get_name())}_twistGrp"
        twist_grp = core_hrchy.create_group(name=twist_grp_name)
        twist_offset_grp = core_hrchy.add_offset_transform(target_list=twist_grp)[0]
        core_trans.match_transform(source=lowerleg_jnt, target_list=twist_offset_grp)
        core_hrchy.parent(source_objects=[twist_offset_grp], target_parent=global_offset_ctrl)
        lowerleg_pv_parent = twist_offset_grp
        core_hrchy.parent(source_objects=lowerleg_ik_offset[0], target_parent=twist_grp)
        cmds.connectAttr(f"{toes_ik_ctrl}.kneeTwist", f"{twist_grp}.rotateX")

        # Ball IK Handle
        ball_ik_handle = cmds.ikHandle(
            sj=toes_ik_jnt,
            ee=ball_ik_jnt,
            n=f"{self._assemble_node_name(self.ball_proxy.get_name())}_ikHandle",
            sol="ikSCsolver",
        )[0]
        core_hrchy.parent(source_objects=ball_ik_handle, target_parent=ball_pivot_grp)

        # Toes End IK Handle
        toesend_ik_handle = cmds.ikHandle(
            sj=ball_ik_jnt,
            ee=toesend_ik_jnt,
            n=f"{self._assemble_node_name(self.toesend_proxy.get_name())}_ikHandle",
            sol="ikSCsolver",
        )[0]
        core_hrchy.parent(source_objects=toesend_ik_handle, target_parent=ball_fk_pivot_grp)

        # Lock And Hide Attrs
        core_attr.hide_lock_default_attrs(
            [
                upperleg_fk_ctrl,
                lowerleg_fk_ctrl,
                paw_fk_ctrl,
                toes_fk_ctrl,
                ball_fk_ctrl,
                ball_ik_ctrl,
                paw_ik_ctrl,
            ],
            translate=True,
            scale=True,
            visibility=True,
        )
        cmds.setAttr(f"{paw_ik_ctrl}.rx", lock=True, keyable=False, channelBox=False)
        core_attr.hide_lock_default_attrs(
            [lowerleg_ik_ctrl],
            rotate=True,
            scale=True,
            visibility=True,
        )
        core_attr.hide_lock_default_attrs(
            [toes_ik_ctrl],
            scale=True,
            visibility=True,
        )
        core_attr.hide_lock_default_attrs(
            [ik_switch_ctrl],
            translate=True,
            rotate=True,
            scale=True,
            visibility=True,
        )
        cmds.setAttr(f"{general_automation_grp}.visibility", 0)
        cmds.setAttr(f"{joint_automation_grp}.visibility", 0)

        # Follow Parent Setup
        module_parent = tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())
        for ctrls in [upperleg_fk_ctrl, lowerleg_ik_ctrl, toes_ik_ctrl]:
            core_attr.add_separator_attr(target_object=ctrls, attr_name=core_rigging.RiggingConstants.SEPARATOR_SPACE)
        if module_parent:
            tools_rig_utils.create_follow_enum_setup(
                control=upperleg_fk_ctrl,
                parent_list=[tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid()), global_offset_ctrl],
                constraint_type="orient",
            )
            tools_rig_utils.create_follow_enum_setup(
                control=lowerleg_pv_parent,
                attribute_item=lowerleg_ik_ctrl,
                parent_list=[
                    tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid()),
                    auto_pole_joint_node,
                    toes_ik_ctrl,
                    global_offset_ctrl,
                ],
                default_value=2,
            )
            tools_rig_utils.create_follow_enum_setup(
                control=toes_ik_ctrl,
                parent_list=[global_offset_ctrl, tools_rig_utils.find_joint_from_uuid(self.get_parent_uuid())],
                default_value=0,
            )
        else:
            tools_rig_utils.create_follow_enum_setup(
                control=upperleg_fk_ctrl,
                parent_list=[global_offset_ctrl],
                constraint_type="orient",
            )
            tools_rig_utils.create_follow_enum_setup(
                control=lowerleg_pv_parent,
                attribute_item=lowerleg_ik_ctrl,
                parent_list=[auto_pole_joint_node, toes_ik_ctrl, global_offset_ctrl],
                default_value=1,
            )
            tools_rig_utils.create_follow_enum_setup(
                control=toes_ik_ctrl,
                parent_list=[global_offset_ctrl],
                default_value=0,
            )

        # IK-FK Switch Locators
        for ik_joint in [upperleg_ik_jnt, lowerleg_ik_jnt, paw_ik_jnt, toes_ik_jnt, ball_ik_jnt]:
            ik_name = core_node.get_short_name(ik_joint).split("_JNT_ik")[0]
            switch_loc = cmds.spaceLocator(n=f"{ik_name}FkOffsetRef_loc")[0]
            cmds.parent(switch_loc, ik_joint)
            cmds.matchTransform(switch_loc, ik_joint)
            cmds.setAttr(f"{switch_loc}.visibility", 0)

        for fk_joint in [lowerleg_fk_jnt, paw_fk_jnt, toes_fk_jnt, ball_fk_jnt]:
            fk_name = core_node.get_short_name(fk_joint).split("_JNT_fk")[0]
            switch_loc = cmds.spaceLocator(n=f"{fk_name}Switch_loc")[0]
            cmds.parent(switch_loc, fk_joint)
            if fk_joint is lowerleg_fk_jnt:
                core_trans.match_translate(source=lowerleg_ik_ctrl, target_list=switch_loc)
            else:
                core_trans.match_translate(source=fk_joint, target_list=switch_loc)
            cmds.setAttr(f"{switch_loc}.visibility", 0)

        # Set Children Drivers -----------------------------------------------------------------------------
        self.module_children_drivers = [upperleg_fk_groups[0]]

    def _delete_unbound_joints(self):
        """
        Deletes joints that are usually not bound to the mesh. In this case the toesEnd joint.
        """
        toesend_jnt = tools_rig_utils.find_joint_from_uuid(self.toesend_proxy.get_uuid())
        if toesend_jnt:
            cmds.delete(toesend_jnt)


class ModuleQuadRearLegLeft(ModuleQuadRearLeg):
    def __init__(self, name="L Quad Rear Leg", prefix=core_naming.NamingConstants.Prefix.LEFT, suffix=None):
        """
        Initialize a left Quadruped rear leg module.

        Args:
            name (str): Name of the module instance (default is "L Quad Rear Leg").
            prefix (str): Naming prefix, defaulting to right side prefix.
            suffix (str or None): Optional naming suffix.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        # Set Left Orientation
        _orientation = tools_rig_frm.OrientationData(aim_axis=(1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Set Left X position
        left_offset = 13
        [proxy.transform.set_position(x=left_offset) for proxy in self.proxies]
        self.bank_left_proxy.transform.set_position(x=left_offset + 5)
        self.bank_right_proxy.transform.set_position(x=left_offset - 5)


class ModuleQuadRearLegRight(ModuleQuadRearLeg):
    def __init__(self, name="R Quad Rear Leg", prefix=core_naming.NamingConstants.Prefix.RIGHT, suffix=None):
        """
        Initialize a right Quadruped rear leg module.

        Args:
            name (str): Name of the module instance (default is "R Quad Rear Leg").
            prefix (str): Naming prefix, defaulting to right side prefix.
            suffix (str or None): Optional naming suffix.
        """
        super().__init__(name=name, prefix=prefix, suffix=suffix)

        # Set Right Orientation
        _orientation = tools_rig_frm.OrientationData(aim_axis=(-1, 0, 0), up_axis=(0, 0, -1), up_dir=(1, 0, 0))
        self.set_orientation(orientation_data=_orientation)

        # Set Right X position
        right_offset = -13
        [proxy.transform.set_position(x=right_offset) for proxy in self.proxies]
        self.bank_left_proxy.transform.set_position(x=right_offset + 5)
        self.bank_right_proxy.transform.set_position(x=right_offset - 5)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # Auto Reload Script - Must have been initialized using "Run-Only" mode.
    from gt.core.session import remove_modules_startswith

    remove_modules_startswith("gt.tools.auto_rigger.module")
    remove_modules_startswith("gt.tools.auto_rigger.rig")
    cmds.file(new=True, force=True)

    import gt.tools.auto_rigger.rig_framework as tools_rig_frm
    import gt.tools.auto_rigger.rig_utils as tools_rig_utils
    import gt.tools.auto_rigger.modules.module_root as tools_rig_mod_root

    # import gt.tools.auto_rigger.modules.module_quad_rear_leg as tools_rig_mod_quad_rear_leg
    import importlib

    importlib.reload(tools_rig_mod_root)
    importlib.reload(tools_rig_frm)
    importlib.reload(tools_rig_utils)
    # importlib.reload(tools_rig_mod_quad_rear_leg)

    # Quadruped Rear Leg Test
    a_root = tools_rig_mod_root.ModuleRoot()
    a_quad_rear_left = ModuleQuadRearLegLeft()
    a_quad_rear_right = ModuleQuadRearLegRight()

    root_uuid = a_root.root_proxy.get_uuid()
    a_quad_rear_left.set_parent_uuid(root_uuid)
    a_quad_rear_right.set_parent_uuid(root_uuid)

    a_project = tools_rig_frm.RigProject()
    a_project.add_to_modules(a_root)
    a_project.add_to_modules(a_quad_rear_left)
    a_project.add_to_modules(a_quad_rear_right)
    # a_project.set_preference_value_using_key(key="delete_proxy_after_build", value=False)
    a_project.set_preference_value_using_key(key="apply_control_rig_pose", value=False)
    a_project.set_preference_value_using_key(key="build_control_rig", value=False)

    a_project.build_proxy()
    # a_project.build_rig()

    # Frame all
    cmds.viewFit(all=True)
