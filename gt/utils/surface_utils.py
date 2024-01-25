"""
Surface Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.curve_utils import get_curve, get_positions_from_curve, rescale_curve
from gt.utils.attr_utils import hide_lock_default_attrs, set_trs_attr
from gt.utils.color_utils import set_color_viewport, ColorConstants
from gt.utils.transform_utils import match_transform
from gt.utils.math_utils import get_bbox_position
from gt.utils.naming_utils import NamingConstants
from gt.utils.node_utils import Node
from gt.utils import hierarchy_utils
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

SURFACE_TYPE = "nurbsSurface"


def is_surface_periodic(surface_shape):
    """
    Determine if a surface is periodic.
    Args:
        surface_shape (str): The name of the surface shape (or its transform).

    Returns:
        bool: True if the surface is periodic, False otherwise.
    """
    form_u = cmds.getAttr(f"{surface_shape}.formU")
    form_v = cmds.getAttr(f'{surface_shape}.formV')
    if form_u == 2 or form_v == 2:
        return True
    return False


class Ribbon:
    def __init__(self,
                 prefix=None,
                 surface=None,
                 equidistant=True,
                 num_controls=5,
                 num_joints=20,
                 add_fk=False,
                 bind_joint_orient_offset=(90, 0, 0),
                 bind_joint_parenting=True
                 ):
        """
        Args:
            prefix (str): The system name to be added as a prefix to the created nodes.
                        If not provided, the name of the surface is used.
            surface (str, optional): The name of the surface to be used as a ribbon. (Can be its transform or shape)
                                     If not provided one will be created automatically.
            equidistant (int, optional): Determine if the controls should be equally spaced (True) or not (False).
            num_controls (int, optional): The number of controls to create.
            num_joints (int, optional): The number of joints to create on the ribbon.
            add_fk (int): Flag to add FK controls.
            bind_joint_orient_offset (tuple): An offset tuple with the X, Y, and Z rotation values.
            bind_joint_parenting (bool, optional): Define if bind joints will form a hierarchy (True) or not (False)
        """
        self.prefix = None
        self.surface = None
        self.equidistant = True
        self.num_controls = 5
        self.num_joints = 20
        self.fixed_radius = None
        self.add_fk = add_fk
        self.bind_joint_offset = None
        self.bind_joint_parenting = True

        if prefix:
            self.set_prefix(prefix=prefix)
        if surface:
            self.set_surface(surface=surface)
        if isinstance(equidistant, bool):
            self.set_equidistant(is_activated=equidistant)
        if num_controls:
            self.set_num_controls(num_controls=num_controls)
        if num_joints:
            self.set_num_joints(num_joints=num_joints)
        if bind_joint_orient_offset:
            self.set_bind_joint_orient_offset(offset_tuple=bind_joint_orient_offset)
        if isinstance(bind_joint_parenting, bool):
            self.set_bind_joint_hierarchy(state=bind_joint_parenting)

    def set_prefix(self, prefix):
        """
        Set the prefix attribute of the object.

        Args:
            prefix (str): The prefix to be added to the ribbon objects during the "build" process.
        """
        if not prefix or not isinstance(prefix, str):
            logger.debug('Unable to set prefix. Input must be a non-empty string.')
            return
        self.prefix = prefix

    def set_surface(self, surface):
        """
        Set the surface to be used as a ribbon of the object.
        Args:
            surface (str): The name of the surface to be used as a ribbon. (Can be its transform or shape)
                           If not provided one will be created automatically.
        """
        if not surface or not isinstance(surface, str):
            logger.debug(f'Unable to set surface path. Input must be a non-empty string.')
            return
        self.surface = surface

    def set_bind_joint_orient_offset(self, offset_tuple):
        """
        Sets an orientation offset (rotation) for the bind joints. Helpful for when matching orientation.
        Args:
            offset_tuple (tuple): An offset tuple with the X, Y, and Z rotation values.
        """
        if not isinstance(offset_tuple, tuple) or len(offset_tuple) < 3:
            logger.debug(f'Unable to set bind joint orient offset. '
                         f'Invalid input. Must be a tuple with X, Y and Z values.')
            return

        if not all(isinstance(num, (int, float)) for num in offset_tuple):
            logger.debug(f'Unable to set bind joint orient offset. '
                         f'Input must contain only numbers.')
            return

        self.bind_joint_offset = offset_tuple

    def set_bind_joint_hierarchy(self, state):
        """
        Sets Bind joint parenting (hierarchy)
        Args:
            state (bool, optional): Define if bind joints will form a hierarchy (True) or not (False)
        """
        if isinstance(state, bool):
            self.bind_joint_parenting = state

    def clear_surface(self):
        """
        Removes/Clears the currently set surface so a new one is automatically created during the "build" process.
        """
        self.surface = None

    def set_fixed_radius(self, radius):
        """
        Sets a fixed radius values
        Args:
            radius (int, float): A radius value to be set when creating bind joints.
                                 If not provided, one is calculated automatically.
        """
        if not radius or not isinstance(radius, (int, float)):
            logger.debug(f'Unable to set fixed radius. Input must be an integer or a float.')
            return
        self.fixed_radius = radius

    def clear_fixed_radius(self):
        """
        Removes/Clears the currently set fixed radius value.
        This causes the radius to be automatically calculated when building.
        """
        self.fixed_radius = None

    def set_equidistant(self, is_activated):
        """
        Set the equidistant attribute of the object.

        Args:
            is_activated (bool): Determine if the controls should be equally spaced (True) or not (False).
        """
        if not isinstance(is_activated, bool):
            logger.debug('Unable to set equidistant state. Input must be a bool (True or False)')
            return
        self.equidistant = is_activated

    def set_num_controls(self, num_controls):
        """
        Set the number of controls attribute of the object.

        Args:
            num_controls (int): The number of controls to create.
        """
        if not isinstance(num_controls, int) or num_controls <= 1:
            logger.debug('Unable to set number of controls. Input must be two or more.')
            return
        self.num_controls = num_controls

    def set_num_joints(self, num_joints):
        """
        Set the number of joints attribute of the object.
        Args:
            num_joints (int): The number of joints to be set.
        """
        if not isinstance(num_joints, int) or num_joints <= 0:
            logger.debug('Unable to set number of joints. Input must be a positive integer.')
            return
        self.num_joints = num_joints

    def _get_or_create_surface(self, prefix):
        surface = self.surface
        if not self.surface or not cmds.objExists(self.surface):
            surface = cmds.nurbsPlane(axis=(0, 1, 0), width=1, lengthRatio=24, degree=3,
                                      patchesU=1, patchesV=10, constructionHistory=False)[0]
            surface = cmds.rename(surface, f"{prefix}ribbon_surface")
        return surface

    def build(self):
        """
        Build a ribbon rig.
        """
        num_controls = self.num_controls
        num_joints = self.num_joints

        # Determine Prefix
        if not self.prefix:
            prefix = f''
        else:
            prefix = f'{self.prefix}_'

        # Create Surface in case not provided or missing
        input_surface = self._get_or_create_surface(prefix=prefix)
        input_surface = Node(input_surface)

        # Determine Surface Transform and Shape
        surface_shape = None
        if cmds.objectType(input_surface) == "transform":
            surface_shape = cmds.listRelatives(input_surface, shapes=True, fullPath=True)[0]
            surface_shape = Node(surface_shape)
        if cmds.objectType(input_surface) == "nurbsSurface":
            surface_shape = Node(input_surface)
            input_surface = cmds.listRelatives(surface_shape, parent=True, fullPath=True)[0]
            input_surface = Node(input_surface)
        cmds.delete(input_surface, constructionHistory=True)

        # Determine Direction ----------------------------------------------------------------------------
        u_curve = cmds.duplicateCurve(f'{input_surface}.v[.5]', local=True, ch=0)  # (.5 = center)
        v_curve = cmds.duplicateCurve(f'{input_surface}.u[.5]', local=True, ch=0)
        u_length = cmds.arclen(u_curve)
        v_length = cmds.arclen(v_curve)

        if u_length < v_length:
            cmds.reverseSurface(input_surface, direction=3, ch=False, replaceOriginal=True)
            cmds.reverseSurface(input_surface, direction=0, ch=False, replaceOriginal=True)

        u_curve_for_positions = cmds.duplicateCurve(f'{input_surface}.v[.5]', local=True, ch=0)[0]

        # U Positions
        is_periodic = is_surface_periodic(surface_shape=surface_shape)
        u_position_ctrls = get_positions_from_curve(curve=u_curve_for_positions, count=num_controls,
                                                    periodic=is_periodic, space="uv")
        u_position_joints = get_positions_from_curve(curve=u_curve_for_positions, count=num_joints,
                                                     periodic=is_periodic, space="uv")

        length = cmds.arclen(u_curve_for_positions)
        cmds.delete(u_curve, v_curve, u_curve_for_positions)

        # Organization ----------------------------------------------------------------------------------
        grp_suffix = NamingConstants.Suffix.GRP
        parent_group = cmds.group(name=f"{prefix}ribbon_{grp_suffix}", empty=True)
        parent_group = Node(parent_group)
        driver_joints_grp = cmds.group(name=f"{prefix}driver_joints_{grp_suffix}", empty=True)
        driver_joints_grp = Node(driver_joints_grp)
        control_grp = cmds.group(name=f"{prefix}controls_{grp_suffix}", empty=True)
        control_grp = Node(control_grp)
        follicles_grp = cmds.group(name=f"{prefix}follicles_{grp_suffix}", empty=True)
        follicles_grp = Node(follicles_grp)
        bind_grp = cmds.group(name=f"{prefix}bind_{grp_suffix}", empty=True)
        bind_grp = Node(bind_grp)
        setup_grp = cmds.group(name=f"{prefix}setup_{grp_suffix}", empty=True)
        setup_grp = Node(setup_grp)
        ribbon_crv = get_curve("_pin_pos_z")
        ribbon_crv.set_name(f"{prefix}base_{NamingConstants.Suffix.CTRL}")
        ribbon_ctrl = ribbon_crv.build()
        ribbon_ctrl = Node(ribbon_ctrl)
        rescale_curve(curve_transform=ribbon_ctrl, scale=length/10)
        ribbon_offset = cmds.group(name=f"{prefix}ctrl_main_offset", empty=True)
        ribbon_offset = Node(ribbon_offset)

        hierarchy_utils.parent(source_objects=ribbon_ctrl, target_parent=ribbon_offset)
        hierarchy_utils.parent(source_objects=control_grp, target_parent=ribbon_ctrl)
        hierarchy_utils.parent(source_objects=[ribbon_offset, bind_grp, setup_grp],
                               target_parent=parent_group)
        hierarchy_utils.parent(source_objects=[input_surface, driver_joints_grp, follicles_grp],
                               target_parent=setup_grp)
        cmds.setAttr(f"{setup_grp}.visibility", 0)

        # Follicles -----------------------------------------------------------------------------------
        follicle_nodes = []
        follicle_transforms = []
        bind_joints = []
        if self.fixed_radius is None:
            bind_joint_radius = (length/60)/(float(num_joints)/40)
        else:
            bind_joint_radius = self.fixed_radius

        for index in range(num_joints):
            _follicle = Node(cmds.createNode("follicle"))
            _follicle_transform = Node(cmds.listRelatives(_follicle, p=True, fullPath=True)[0])
            _follicle_transform.rename(f"{prefix}follicle_{(index+1):02d}")

            follicle_transforms.append(_follicle_transform)
            follicle_nodes.append(_follicle)

            # Connect Follicle to Transforms
            cmds.connectAttr(f"{_follicle}.outTranslate", f"{_follicle_transform}.translate")
            cmds.connectAttr(f"{_follicle}.outRotate", f"{_follicle_transform}.rotate")

            # Attach Follicle to Surface
            cmds.connectAttr(f"{surface_shape}.worldMatrix[0]", f"{_follicle}.inputWorldMatrix")
            cmds.connectAttr(f"{surface_shape}.local", f"{_follicle}.inputSurface")

            cmds.setAttr(f'{_follicle}.parameterU', u_position_joints[index])
            cmds.setAttr(f'{_follicle}.parameterV', 0.5)

            cmds.parent(_follicle_transform, follicles_grp)

            # Bind Joint
            if prefix:
                joint_name = f"{prefix}{(index+1):02d}_{NamingConstants.Suffix.JNT}"
            else:
                joint_name = f"bind_{(index+1):02d}_{NamingConstants.Suffix.JNT}"
            joint = cmds.createNode("joint", name=joint_name)
            joint = Node(joint)
            bind_joints.append(joint)

            match_transform(source=_follicle_transform, target_list=joint)
            if self.bind_joint_offset:
                cmds.rotate(*self.bind_joint_offset, joint, relative=True, os=True)
            cmds.parentConstraint(_follicle_transform, joint, maintainOffset=True)
            cmds.setAttr(f"{joint}.radius", bind_joint_radius)

        if follicle_transforms:
            match_transform(source=follicle_transforms[0], target_list=ribbon_offset)
        else:
            bbox_center = get_bbox_position(input_surface)
            set_trs_attr(target_obj=ribbon_offset, value_tuple=bbox_center, translate=True)
        hierarchy_utils.parent(source_objects=bind_joints, target_parent=bind_grp)

        # Ribbon Controls -----------------------------------------------------------------------------------
        ctrl_ref_follicle_nodes = []
        ctrl_ref_follicle_transforms = []

        for index in range(num_controls):
            _follicle = Node(cmds.createNode("follicle"))
            _follicle_transform = cmds.listRelatives(_follicle, parent=True)[0]
            ctrl_ref_follicle_nodes.append(_follicle)
            ctrl_ref_follicle_transforms.append(_follicle_transform)

            cmds.connectAttr(f"{_follicle}.outTranslate", f"{_follicle_transform}.translate")
            cmds.connectAttr(f"{_follicle}.outRotate", f"{_follicle_transform}.rotate")
            cmds.connectAttr(f"{surface_shape}.worldMatrix[0]", f"{_follicle}.inputWorldMatrix")
            cmds.connectAttr(f"{surface_shape}.local", f"{_follicle}.inputSurface")

        divider_for_ctrls = num_controls
        if not is_periodic:
            divider_for_ctrls = num_controls-1
        if self.equidistant:
            for index, _follicle_transform in enumerate(ctrl_ref_follicle_nodes):
                cmds.setAttr(f'{_follicle_transform}.parameterU', u_position_ctrls[index])
                cmds.setAttr(f'{_follicle_transform}.parameterV', 0.5)  # Center
        else:
            u_pos = 0
            for _follicle_transform in ctrl_ref_follicle_nodes:
                cmds.setAttr(f'{_follicle_transform}.parameterU', u_pos)
                cmds.setAttr(f'{_follicle_transform}.parameterV', 0.5)  # Center
                u_pos = u_pos + (1.0 / divider_for_ctrls)

        ik_ctrl_scale = (length / 35) / (float(num_controls) / 5)  # TODO TEMP @@@
        ribbon_ctrls = []

        ctrl_offset_grps = []
        ctrl_joints = []
        ctrl_jnt_offset_grps = []
        ctrl_jnt_radius = bind_joint_radius * 2

        for index in range(num_controls):
            crv = get_curve("_cube")
            ctrl = Node(crv.build())
            ctrl.rename(f"{prefix}{NamingConstants.Suffix.CTRL}_{(index+1):02d}")
            scale = ((length/3)/num_controls, 1, 1)

            rescale_curve(curve_transform=ctrl, scale=scale)

            ribbon_ctrls.append(ctrl)

            ctrl_offset_grp = cmds.group(name=f"{ctrl.get_short_name()}_offset", empty=True)
            ctrl_offset_grp = Node(ctrl_offset_grp)
            hierarchy_utils.parent(source_objects=ctrl, target_parent=ctrl_offset_grp)
            match_transform(source=ctrl_ref_follicle_transforms[index], target_list=ctrl_offset_grp)
            ctrl_offset_grps.append(ctrl_offset_grp)

            # Ribbon Driver Joint
            joint = cmds.createNode("joint", name=f'{prefix}driver_{(index+1):02d}_{NamingConstants.Suffix.JNT}')
            joint = Node(joint)
            ctrl_joints.append(joint)
            cmds.setAttr(f"{ctrl_joints[index]}.radius", ctrl_jnt_radius)
            ctrl_jnt_ofs_grp = cmds.group(name=f"{joint}_offset", empty=True)
            ctrl_jnt_ofs_grp = Node(ctrl_jnt_ofs_grp)
            hierarchy_utils.parent(source_objects=joint, target_parent=ctrl_jnt_ofs_grp)
            match_transform(source=ctrl_ref_follicle_transforms[index], target_list=ctrl_jnt_ofs_grp)
            ctrl_jnt_offset_grps.append(ctrl_jnt_ofs_grp)

        hierarchy_utils.parent(source_objects=ctrl_offset_grps, target_parent=control_grp)
        hierarchy_utils.parent(source_objects=ctrl_jnt_offset_grps, target_parent=driver_joints_grp)

        hide_lock_default_attrs(obj_list=ctrl_offset_grps + ctrl_jnt_offset_grps,
                                translate=True, rotate=True, scale=True, visibility=False)

        cmds.delete(ctrl_ref_follicle_transforms)

        for (control, joint) in zip(ribbon_ctrls, ctrl_joints):
            cmds.parentConstraint(control, joint)
            cmds.scaleConstraint(control, joint)

        # Follicle Scale
        for fol in follicle_transforms:
            cmds.scaleConstraint(ribbon_ctrl, fol)

        # Bind the surface to driver joints
        nurbs_skin_cluster = cmds.skinCluster(ctrl_joints, input_surface,
                                              dropoffRate=2,
                                              maximumInfluences=num_controls-1,
                                              nurbsSamples=num_controls*5,
                                              bindMethod=0,  # Closest Distance
                                              name=f"{prefix}skinCluster")[0]
        cmds.skinPercent(nurbs_skin_cluster, input_surface, pruneWeights=0.2)

        cmds.connectAttr(f"{ribbon_ctrl}.sx", f"{ribbon_ctrl}.sy")
        cmds.connectAttr(f"{ribbon_ctrl}.sx", f"{ribbon_ctrl}.sz")
        cmds.aliasAttr("Scale", f"{ribbon_ctrl}.sx")

        cmds.connectAttr(f"{ribbon_offset}.sx", f"{ribbon_offset}.sy")
        cmds.connectAttr(f"{ribbon_offset}.sx", f"{ribbon_offset}.sz")
        cmds.aliasAttr("Scale", f"{ribbon_offset}.sx")

        # FK Controls ---------------------------------------------------------------------------------------
        fk_ctrls = []
        if self.add_fk and is_periodic:
            logger.warning(f'Unable to add FK controls. Input surface is periodic.')
        elif self.add_fk and not is_periodic:
            fk_offset_groups = []
            crv_obj = get_curve("_circle_pos_x")
            for index in range(1, num_controls):
                _ctrl = Node(crv_obj.build())
                _ctrl.rename(f'{prefix}fk_{index:02d}_ctrl')
                _offset = Node(cmds.group(name=f'{prefix}fk_{index:02d}_offset', empty=True))
                fk_ctrls.append(_ctrl)
                fk_offset_groups.append(_offset)
                cmds.parent(_ctrl, _offset)

            for (offset, ctrl) in zip(fk_offset_groups[1:], fk_ctrls[:-1]):
                cmds.parent(offset, ctrl)

            cmds.parent(fk_offset_groups[0], control_grp)

            # Re-scale FK controls
            fk_ctrl_scale = ik_ctrl_scale*2
            for fk_ctrl in fk_ctrls:
                rescale_curve(curve_transform=fk_ctrl, scale=fk_ctrl_scale)

            ik_ctrl_offset_grps = [cmds.group(ctrl,
                                              name=f"{ctrl.get_short_name()}_offset_grp") for ctrl in ribbon_ctrls]
            [cmds.xform(ik_ctrl_offset_grp, piv=(0, 0, 0), os=True) for ik_ctrl_offset_grp in ik_ctrl_offset_grps]

            for ik, fk in zip(ribbon_ctrls[:-1], fk_offset_groups):
                cmds.delete(cmds.parentConstraint(ik, fk))

            for fk, ik in zip(fk_ctrls, ik_ctrl_offset_grps[:-1]):
                cmds.parentConstraint(fk, ik)

            # Constrain Last Ctrl
            cmds.parentConstraint(fk_ctrls[-1], ik_ctrl_offset_grps[-1], mo=True)

            set_color_viewport(obj_list=fk_ctrls, rgb_color=ColorConstants.RigControl.TWEAK)
            hide_lock_default_attrs(fk_offset_groups, translate=True, rotate=True, scale=True)

            cmds.select(cl=True)

        # Parenting Binding Joints
        if self.bind_joint_parenting:
            for index in range(len(bind_joints) - 1):
                parent_joint = bind_joints[index]
                child_joint = bind_joints[index + 1]
                if cmds.objExists(parent_joint) and cmds.objExists(child_joint):
                    cmds.parent(child_joint, parent_joint)

        # Colors  ----------------------------------------------------------------------------------------
        set_color_viewport(obj_list=ribbon_ctrl, rgb_color=ColorConstants.RGB.WHITE)
        set_color_viewport(obj_list=fk_ctrls, rgb_color=ColorConstants.RGB.RED_INDIAN)
        set_color_viewport(obj_list=ribbon_ctrls, rgb_color=ColorConstants.RGB.BLUE_SKY)
        set_color_viewport(obj_list=bind_joints, rgb_color=ColorConstants.RGB.YELLOW)

        # Clear selection
        cmds.select(cl=True)


def create_surface_from_object_list(obj_list, surface_name=None):
    """
    Creates a surface from a list of objects (according to list order)
    The surface is created using curve offsets.
        1. A curve is created using the position of the objects from the list.
        2. Two offset curves are created from the initial curve.
        3. A loft surface is created out of the two offset curves.
    Args:
        obj_list (list): List of objects used to generate the surface (order matters)
        surface_name (str, optional): Name of the generated surface.
    Returns:
        str or None: Generated surface (loft) object, otherwise None.
    """
    # Check if there are at least two objects in the list
    if len(obj_list) < 2:
        cmds.warning("At least two objects are required to create a surface.")
        return

    # Get positions of the objects
    positions = [cmds.xform(obj, query=True, translation=True, worldSpace=True) for obj in obj_list]

    # Create a curve with the given positions as control vertices (CVs)
    crv_mid = cmds.curve(d=1, p=positions, n=f'{surface_name}_curveFromList')
    crv_mid = Node(crv_mid)

    # Offset the duplicated curve positively
    offset_distance = 1
    crv_pos = cmds.offsetCurve(crv_mid, name=f'{crv_mid}PositiveOffset',
                               distance=offset_distance, constructionHistory=False)[0]
    crv_neg = cmds.offsetCurve(crv_mid, name=f'{crv_mid}NegativeOffset',
                               distance=-offset_distance, constructionHistory=False)[0]
    crv_pos = Node(crv_pos)
    crv_neg = Node(crv_neg)

    loft_parameters = {}
    if surface_name and isinstance(surface_name, str):
        loft_parameters["name"] = surface_name

    lofted_surface = cmds.loft(crv_pos, crv_neg,
                               range=True,
                               autoReverse=True,
                               degree=3,
                               uniform=True,
                               constructionHistory=False,
                               **loft_parameters)[0]
    cmds.delete([crv_mid, crv_pos, crv_neg])
    return lofted_surface


if __name__ == "__main__":
    from pprint import pprint
    logger.setLevel(logging.DEBUG)
    # cmds.file(new=True, force=True)

    create_surface_from_object_list(["joint1", "joint2", "joint3", "joint4", "joint5"], surface_name="hello")
    ribbon_factory = Ribbon(equidistant=True,
                            num_controls=5,
                            num_joints=8,
                            add_fk=True)
    ribbon_factory.set_surface("right_eyebrow_sur")
    ribbon_factory.set_prefix("right_eyebrow")
    # ribbon_factory.set_surface("hello")
    # ribbon_factory.set_prefix("test")
    # ribbon_factory.set_surface("abc_ribbon_surface")
    # ribbon_factory.set_prefix("abc")
    # ribbon_factory.build()
