"""
Controls driven by clusters
"""
from gt.utils.data.controls.control_data import ControlData
from gt.utils.naming_utils import NamingConstants
from gt.utils.transform_utils import scale_shapes
from gt.utils.curve_utils import get_curve
from gt.utils.node_utils import Node
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
    curve_transform = Node(curve_transform)
    curve_shape = cmds.listRelatives(curve_transform, shapes=True, fullPath=True)[0]
    cmds.rename(curve_shape, f'{curve_transform.get_short_name()}Shape')

    # Set Initial Scale
    scale_shapes(obj_transform=curve_transform, offset=initial_scale)
    # Create Scale Curve
    curve_scale_crv = get_curve('_line_z_length_one')
    curve_scale_crv_name = f'{curve_transform.get_short_name()}_scale{NamingConstants.Suffix.CTRL.capitalize()}'
    curve_scale_crv.set_name(name=curve_scale_crv_name)
    curve_scale_crv = curve_scale_crv.build()
    curve_scale_crv = Node(curve_scale_crv)
    cmds.move(0, 0, 0, f'{curve_scale_crv}.cv[0]')
    cmds.move(0, 0, 1, f'{curve_scale_crv}.cv[1]')
    curve_scale_shape = cmds.listRelatives(curve_scale_crv, shapes=True, fullPath=True)[0]

    # Set Initial Scale
    cmds.setAttr(f'{curve_scale_crv}.sx', initial_scale)
    cmds.setAttr(f'{curve_scale_crv}.sy', initial_scale)
    cmds.setAttr(f'{curve_scale_crv}.sz', initial_scale)
    cmds.makeIdentity(curve_scale_crv, apply=True, scale=True, rotate=True)

    # Create Clusters
    cmds.select([f'{curve_transform}.cv[0:2]', f'{curve_transform}.cv[5:7]'], replace=True)
    cluster_end = cmds.cluster(name=f'{curve_transform.get_short_name()}_end', bindState=True)

    cmds.select(f'{curve_transform}.cv[3:4]', replace=True)
    cluster_start = cmds.cluster(name=f'{curve_transform.get_short_name()}_start', bindState=True)

    # Create Mechanics
    start_point_on_crv_node = cmds.createNode('pointOnCurveInfo',
                                              name=f'{curve_transform.get_short_name()}_start_pointOnCurve')
    end_point_on_crv_node = cmds.createNode('pointOnCurveInfo',
                                            name=f'{curve_transform.get_short_name()}_end_pointOnCurve')
    cmds.setAttr(f'{start_point_on_crv_node}.parameter', 0)
    cmds.setAttr(f'{end_point_on_crv_node}.parameter', 1)

    cmds.connectAttr(f'{curve_scale_shape}.worldSpace', f'{start_point_on_crv_node}.inputCurve')
    cmds.connectAttr(f'{curve_scale_shape}.worldSpace', f'{end_point_on_crv_node}.inputCurve')

    start_curve_scale_grp = cmds.group(name=f'{curve_transform}_curveScale_start_grp', world=True, empty=True)
    end_curve_scale_grp = cmds.group(name=f'{curve_transform}_curveScale_end_grp', world=True, empty=True)

    cmds.delete(cmds.pointConstraint(cluster_start, start_curve_scale_grp))
    cmds.delete(cmds.pointConstraint(cluster_end, end_curve_scale_grp))

    cmds.connectAttr(f'{start_point_on_crv_node}.result.position', f'{start_curve_scale_grp}.translate')
    cmds.connectAttr(f'{end_point_on_crv_node}.result.position', f'{end_curve_scale_grp}.translate')

    curve_rig_grp = cmds.group(name=f'{curve_transform.get_short_name()}_setup_grp', world=True, empty=True)
    curve_rig_grp = Node(curve_rig_grp)

    cmds.createNode('pointOnCurveInfo', name=f'{curve_transform.get_short_name()}_start_pointOnCurve')

    # Setup Hierarchy
    cmds.parent(cluster_start[1], start_curve_scale_grp)
    cmds.parent(cluster_end[1], end_curve_scale_grp)
    cmds.parent(curve_scale_crv, curve_rig_grp)
    cmds.parent(start_curve_scale_grp, curve_rig_grp)
    cmds.parent(end_curve_scale_grp, curve_rig_grp)

    # Set Visibility
    cmds.setAttr(f'{cluster_start[1]}.v', 0)
    cmds.setAttr(f'{cluster_end[1] }.v', 0)
    cmds.setAttr(f'{curve_scale_crv}.v', 0)

    # Set Limit
    if min_scale_apply:
        cmds.setAttr(f'{curve_scale_crv}.minScaleZLimit', min_scale)
        cmds.setAttr(f'{curve_scale_crv}.minScaleZLimitEnable', 1)

    # Clean Selection
    cmds.select(deselect=True)
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
    curve_transform = Node(curve_transform)
    curve_shape = cmds.listRelatives(curve_transform, shapes=True, fullPath=True)[0]
    cmds.rename(curve_shape, f'{curve_transform.get_short_name()}Shape')

    # Set Initial Scale
    scale_shapes(obj_transform=curve_transform, offset=initial_scale)

    # Create Scale Curve
    curve_scale_crv = get_curve('_line_z_length_two')
    curve_scale_crv_name = f'{curve_transform.get_short_name()}_scale{NamingConstants.Suffix.CTRL.capitalize()}'
    curve_scale_crv.set_name(name=curve_scale_crv_name)
    curve_scale_crv = curve_scale_crv.build()
    curve_scale_crv = Node(curve_scale_crv)
    curve_scale_shape = cmds.listRelatives(curve_scale_crv, shapes=True, fullPath=True)[0]

    # Set Initial Scale
    cmds.setAttr(f'{curve_scale_crv}.sx', initial_scale)
    cmds.setAttr(f'{curve_scale_crv}.sy', initial_scale)
    cmds.setAttr(f'{curve_scale_crv}.sz', initial_scale)
    cmds.makeIdentity(curve_scale_crv, apply=True, scale=True, rotate=True)

    # Create Clusters
    cmds.select([f'{curve_transform}.cv[0:2]', f'{curve_transform}.cv[8:10]'], replace=True)
    cluster_end = cmds.cluster(name=f'{curve_transform.get_short_name()}_end', bindState=True)

    cmds.select(f'{curve_transform}.cv[3:7]', replace=True)
    cluster_start = cmds.cluster(name=f'{curve_transform.get_short_name()}_start', bindState=True)

    # Create Mechanics
    start_point_on_curve_node = cmds.createNode('pointOnCurveInfo',
                                                name=f'{curve_transform.get_short_name()}_start_pointOnCurve')
    end_point_on_curve_node = cmds.createNode('pointOnCurveInfo',
                                              name=f'{curve_transform.get_short_name()}_end_pointOnCurve')
    cmds.setAttr(f'{start_point_on_curve_node}.parameter', 0)
    cmds.setAttr(f'{end_point_on_curve_node}.parameter', 1)

    cmds.connectAttr(f'{curve_scale_shape}.worldSpace', f'{start_point_on_curve_node}.inputCurve')
    cmds.connectAttr(f'{curve_scale_shape}.worldSpace', f'{end_point_on_curve_node}.inputCurve')

    start_curve_scale_grp = cmds.group(name=f'{curve_transform.get_short_name()}_curveScale_start_grp',
                                       world=True, empty=True)
    end_curve_scale_grp = cmds.group(name=f'{curve_transform.get_short_name()}_curveScale_end_grp',
                                     world=True, empty=True)

    cmds.delete(cmds.pointConstraint(cluster_start, start_curve_scale_grp))
    cmds.delete(cmds.pointConstraint(cluster_end, end_curve_scale_grp))

    cmds.connectAttr(f'{start_point_on_curve_node}.result.position', f'{start_curve_scale_grp}.translate')
    cmds.connectAttr(f'{end_point_on_curve_node}.result.position', f'{end_curve_scale_grp}.translate')

    curve_rig_grp = cmds.group(name=f'{curve_transform.get_short_name()}_setup_grp', world=True, empty=True)
    curve_rig_grp = Node(curve_rig_grp)

    cmds.createNode('pointOnCurveInfo', name=f'{curve_transform.get_short_name()}_start_pointOnCurve')

    # Setup Hierarchy
    cmds.parent(cluster_start[1], start_curve_scale_grp)
    cmds.parent(cluster_end[1], end_curve_scale_grp)
    cmds.parent(curve_scale_crv, curve_rig_grp)
    cmds.parent(start_curve_scale_grp, curve_rig_grp)
    cmds.parent(end_curve_scale_grp, curve_rig_grp)

    # Set Visibility
    cmds.setAttr(f'{cluster_start[1]}.v', 0)
    cmds.setAttr(f'{cluster_end[1]}.v', 0)
    cmds.setAttr(f'{curve_scale_crv}.v', 0)

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
    create_scalable_two_sides_arrow()
