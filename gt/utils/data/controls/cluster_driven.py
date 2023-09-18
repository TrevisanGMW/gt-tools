"""
Controls driven by clusters
"""
from gt.utils.data.controls.control_data import ControlData
from gt.utils.naming_utils import NamingConstants
from gt.utils.curve_utils import get_curve
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_scalable_one_side_arrow(name='scalable_one_side_arrow', initial_scale=1,
                                   min_scale_apply=False, min_scale=0.01):
    """
    Creates a curve in the shape of an arrow and rigs it so when scaling it up the curve doesn't lose its shape.
    Instead, it scales only in the direction of the arrow head. Use the "<name>_scaleCtrl" to determine the scale.

    Args:
        name (str): Name of the generated curves.
        initial_scale (float): Initial Scale of the curve.
        min_scale_apply (bool): If active, it will apply the minimum scale limit. If False, it won't limit anything.
        min_scale (float): Minimum scale of the "scaleCtrl" curve. If None, there is not similar.

    Returns:
        ControlData: object containing: name=curve_transform, drivers=curve_scale_crv, setup=curve_rig_grp
    """
    arrow_curve = get_curve('_scalable_one_side_arrow')
    arrow_curve.set_name(name=name)
    curve_transform = arrow_curve.build()
    curve_shape = cmds.listRelatives(curve_transform, s=True, f=True)[0]
    curve_shape = cmds.rename(curve_shape, '{0}Shape'.format(curve_transform))
    logger.debug(str(curve_shape))
    # Set Initial Scale
    cmds.setAttr(curve_transform + '.sx', initial_scale)
    cmds.setAttr(curve_transform + '.sy', initial_scale)
    cmds.setAttr(curve_transform + '.sz', initial_scale)
    cmds.makeIdentity(curve_transform, apply=True, scale=True, rotate=True)

    # Create Scale Curve
    curve_scale_crv = get_curve('_line_z_length_one')
    curve_scale_crv.set_name(name=curve_transform + '_scale' + NamingConstants.Suffix.CTRL.capitalize())
    curve_scale_crv = curve_scale_crv.build()
    cmds.move(0, 0, 0, f'{curve_scale_crv}.cv[0]')
    cmds.move(0, 0, 1, f'{curve_scale_crv}.cv[1]')
    curve_scale_shape = cmds.listRelatives(curve_scale_crv, s=True, f=True)[0]
    # Set Initial Scale
    cmds.setAttr(curve_scale_crv + '.sx', initial_scale)
    cmds.setAttr(curve_scale_crv + '.sy', initial_scale)
    cmds.setAttr(curve_scale_crv + '.sz', initial_scale)
    cmds.makeIdentity(curve_scale_crv, apply=True, scale=True, rotate=True)

    # Create Clusters
    cmds.select([curve_transform + '.cv[0:2]', curve_transform + '.cv[5:7]'], r=True)
    cluster_end = cmds.cluster(name=curve_transform + '_end', bs=1)

    cmds.select(curve_transform + '.cv[3:4]', r=True)
    cluster_start = cmds.cluster(name=curve_transform + '_start', bs=1)

    # Create Mechanics
    start_point_on_curve_node = cmds.createNode('pointOnCurveInfo', name=curve_transform + '_start_pointOnCurve')
    end_point_on_curve_node = cmds.createNode('pointOnCurveInfo', name=curve_transform + '_end_pointOnCurve')
    cmds.setAttr(start_point_on_curve_node + '.parameter', 0)
    cmds.setAttr(end_point_on_curve_node + '.parameter', 1)

    cmds.connectAttr(curve_scale_shape + '.worldSpace', start_point_on_curve_node + '.inputCurve')
    cmds.connectAttr(curve_scale_shape + '.worldSpace', end_point_on_curve_node + '.inputCurve')

    start_curve_scale_grp = cmds.group(name=curve_transform + '_curveScale_start_grp', world=True, empty=True)
    end_curve_scale_grp = cmds.group(name=curve_transform + '_curveScale_end_grp', world=True, empty=True)

    cmds.delete(cmds.pointConstraint(cluster_start, start_curve_scale_grp))
    cmds.delete(cmds.pointConstraint(cluster_end, end_curve_scale_grp))

    cmds.connectAttr(start_point_on_curve_node + '.result.position', start_curve_scale_grp + '.translate')
    cmds.connectAttr(end_point_on_curve_node + '.result.position', end_curve_scale_grp + '.translate')

    curve_rig_grp = cmds.group(name=curve_transform + '_setup_grp', world=True, empty=True)

    cmds.createNode('pointOnCurveInfo', name=curve_transform + '_start_pointOnCurve')

    # Setup Hierarchy
    cmds.parent(cluster_start[1], start_curve_scale_grp)
    cmds.parent(cluster_end[1], end_curve_scale_grp)
    cmds.parent(curve_scale_crv, curve_rig_grp)
    cmds.parent(start_curve_scale_grp, curve_rig_grp)
    cmds.parent(end_curve_scale_grp, curve_rig_grp)

    # Set Visibility
    cmds.setAttr(cluster_start[1] + '.v', 0)
    cmds.setAttr(cluster_end[1] + '.v', 0)
    cmds.setAttr(curve_scale_crv + '.v', 0)

    # Set Limit
    if min_scale_apply:
        cmds.setAttr(f'{curve_scale_crv}.minScaleZLimit', min_scale)
        cmds.setAttr(f'{curve_scale_crv}.minScaleZLimitEnable', 1)

    # Clean Selection
    cmds.select(d=True)
    return ControlData(name=curve_transform, drivers=curve_scale_crv, setup=curve_rig_grp)


def create_scalable_two_sides_arrow(name='scalable_two_sides_arrow', initial_scale=1,
                                    min_scale_apply=False, min_scale=0.01):
    """
    Creates a curve in the shape of an arrow and rigs it so when scaling it up the curve doesn't lose its shape.
    Instead, it scales only in the direction of the arrow heads. Use the "<name>_scaleCtrl" to determine the scale.

    Args:
        name (str): Name of the generated curves.
        initial_scale (float): Initial Scale of the curve.
        min_scale_apply (bool): If active, it will apply the minimum scale limit. If False, it won't limit anything.
        min_scale (float): Minimum scale of the "scaleCtrl" curve. If None, there is not similar.

    Returns:
        ControlData: object containing: name=curve_transform, drivers=curve_scale_crv, setup=curve_rig_grp
    """
    arrow_curve = get_curve('_scalable_two_sides_arrow')
    arrow_curve.set_name(name=name)
    curve_transform = arrow_curve.build()
    curve_shape = cmds.listRelatives(curve_transform, s=True, f=True)[0]
    curve_shape = cmds.rename(curve_shape, '{0}Shape'.format(curve_transform))
    logger.debug(str(curve_shape))
    # Set Initial Scale
    cmds.setAttr(curve_transform + '.sx', initial_scale)
    cmds.setAttr(curve_transform + '.sy', initial_scale)
    cmds.setAttr(curve_transform + '.sz', initial_scale)
    cmds.makeIdentity(curve_transform, apply=True, scale=True, rotate=True)

    # Create Scale Curve
    curve_scale_crv = get_curve('_line_z_length_two')
    curve_scale_crv.set_name(name=curve_transform + '_scale' + NamingConstants.Suffix.CTRL.capitalize())
    curve_scale_crv = curve_scale_crv.build()
    curve_scale_shape = cmds.listRelatives(curve_scale_crv, s=True, f=True)[0]
    # Set Initial Scale
    cmds.setAttr(curve_scale_crv + '.sx', initial_scale)
    cmds.setAttr(curve_scale_crv + '.sy', initial_scale)
    cmds.setAttr(curve_scale_crv + '.sz', initial_scale)
    cmds.makeIdentity(curve_scale_crv, apply=True, scale=True, rotate=True)

    # Create Clusters
    cmds.select([curve_transform + '.cv[0:2]', curve_transform + '.cv[8:10]'], r=True)
    cluster_end = cmds.cluster(name=curve_transform + '_end', bs=1)

    cmds.select(curve_transform + '.cv[3:7]', r=True)
    cluster_start = cmds.cluster(name=curve_transform + '_start', bs=1)

    # Create Mechanics
    start_point_on_curve_node = cmds.createNode('pointOnCurveInfo', name=curve_transform + '_start_pointOnCurve')
    end_point_on_curve_node = cmds.createNode('pointOnCurveInfo', name=curve_transform + '_end_pointOnCurve')
    cmds.setAttr(start_point_on_curve_node + '.parameter', 0)
    cmds.setAttr(end_point_on_curve_node + '.parameter', 1)

    cmds.connectAttr(curve_scale_shape + '.worldSpace', start_point_on_curve_node + '.inputCurve')
    cmds.connectAttr(curve_scale_shape + '.worldSpace', end_point_on_curve_node + '.inputCurve')

    start_curve_scale_grp = cmds.group(name=curve_transform + '_curveScale_start_grp', world=True, empty=True)
    end_curve_scale_grp = cmds.group(name=curve_transform + '_curveScale_end_grp', world=True, empty=True)

    cmds.delete(cmds.pointConstraint(cluster_start, start_curve_scale_grp))
    cmds.delete(cmds.pointConstraint(cluster_end, end_curve_scale_grp))

    cmds.connectAttr(start_point_on_curve_node + '.result.position', start_curve_scale_grp + '.translate')
    cmds.connectAttr(end_point_on_curve_node + '.result.position', end_curve_scale_grp + '.translate')

    curve_rig_grp = cmds.group(name=curve_transform + '_setup_grp', world=True, empty=True)

    cmds.createNode('pointOnCurveInfo', name=curve_transform + '_start_pointOnCurve')

    # Setup Hierarchy
    cmds.parent(cluster_start[1], start_curve_scale_grp)
    cmds.parent(cluster_end[1], end_curve_scale_grp)
    cmds.parent(curve_scale_crv, curve_rig_grp)
    cmds.parent(start_curve_scale_grp, curve_rig_grp)
    cmds.parent(end_curve_scale_grp, curve_rig_grp)

    # Set Visibility
    cmds.setAttr(cluster_start[1] + '.v', 0)
    cmds.setAttr(cluster_end[1] + '.v', 0)
    cmds.setAttr(curve_scale_crv + '.v', 0)

    # Set Limit
    if min_scale_apply:
        cmds.setAttr(f'{curve_scale_crv}.minScaleZLimit', min_scale)
        cmds.setAttr(f'{curve_scale_crv}.minScaleZLimitEnable', 1)

    # Clean Selection
    cmds.select(d=True)
    return ControlData(name=curve_transform, drivers=curve_scale_crv, setup=curve_rig_grp)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)
    create_scalable_one_side_arrow()

