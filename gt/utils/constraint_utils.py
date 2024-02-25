"""
Constraint Utilities
github.com/TrevisanGMW/gt-tools
"""
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_rivet(source_components=None, verbose=True):
    """
    Creates a rivet constraints.
    Args:
        source_components (list): Must be TWO edges from a polygon or ONE point from a surface.
                                  If not provided, the selection is used instead.
        verbose (bool, optional): If active, this function will return warnings.
    Returns:
        str or None: Name of the generated rivet locator or None in case it fails.
    """
    if source_components is None:
        source_components = cmds.ls(selection=True) or []
    # Filter Edges
    source = cmds.filterExpand(source_components, selectionMask=32) or []  # 32 = Polygon Edges

    obj_name = None
    point_surface_node = None
    if len(source) > 0:
        if len(source) != 2:
            if verbose:
                cmds.warning("Unable to create rivet. Select two edges or a surface point and try again.")
            return

        edge_split_list = source[0].split(".")
        obj_name = edge_split_list[0]
        edge_split_list = source[0].split("[")
        edge_a = int(edge_split_list[1].strip("]"))
        edge_split_list = source[1].split("[")
        edge_b = int(edge_split_list[1].strip("]"))

        curve_from_mesh_edge_one = cmds.createNode("curveFromMeshEdge", name=f'{obj_name}_rivetCrv_A')
        cmds.setAttr(curve_from_mesh_edge_one + ".ihi", 1)
        cmds.setAttr(curve_from_mesh_edge_one + ".ei[0]", edge_a)
        curve_from_mesh_edge_two = cmds.createNode("curveFromMeshEdge", name=f'{obj_name}_rivetCrv_B')
        cmds.setAttr(curve_from_mesh_edge_two + ".ihi", 1)
        cmds.setAttr(curve_from_mesh_edge_two + ".ei[0]", edge_b)

        # Create a loft node
        loft_node = cmds.createNode("loft", name=f'{obj_name}_rivetLoft')

        point_surface_node = cmds.createNode("pointOnSurfaceInfo", name=f'{obj_name}_rivetPointInfo')
        cmds.setAttr(point_surface_node + ".turnOnPercentage", 1)
        cmds.setAttr(point_surface_node + ".parameterU", 0.5)
        cmds.setAttr(point_surface_node + ".parameterV", 0.5)

        cmds.connectAttr(loft_node + ".os", point_surface_node + ".is")
        cmds.connectAttr(curve_from_mesh_edge_one + ".oc", loft_node + ".ic[0]")
        cmds.connectAttr(curve_from_mesh_edge_two + ".oc", loft_node + ".ic[1]")
        cmds.connectAttr(obj_name + ".w", curve_from_mesh_edge_one + ".im")
        cmds.connectAttr(obj_name + ".w", curve_from_mesh_edge_two + ".im")

    else:
        # Filter Surface Parameter Points
        source = cmds.filterExpand(source_components, selectionMask=41) or []  # 41 = Surface Parameter Points

        if len(source) > 0:
            if len(source) != 1:
                if verbose:
                    cmds.warning("Unable to create rivet. Select two edges or a surface point and try again.")
                return

            edge_split_list = source[0].split(".")
            obj_name = edge_split_list[0]
            edge_split_list = source[0].split("[")
            u = float(edge_split_list[1].strip("]"))
            v = float(edge_split_list[2].strip("]"))

            point_surface_node = cmds.createNode("pointOnSurfaceInfo", name=f'{obj_name}_rivetPointInfo')
            cmds.setAttr(point_surface_node + ".turnOnPercentage", 0)
            cmds.setAttr(point_surface_node + ".parameterU", u)
            cmds.setAttr(point_surface_node + ".parameterV", v)

            cmds.connectAttr(obj_name + ".ws", point_surface_node + ".is")

    if not obj_name or not point_surface_node:
        if verbose:
            cmds.warning("Unable to create rivet. Input must be two edges or one surface point.")
        return

    # Create Locator
    locator_name = cmds.createNode("transform", name="rivet1")
    cmds.createNode("locator", name=locator_name + "Shape", p=locator_name)

    name_aim_constraint = cmds.createNode("aimConstraint", p=locator_name, name=locator_name + "_rivetAimConstraint1")
    cmds.setAttr(name_aim_constraint + ".tg[0].tw", 1)
    cmds.setAttr(name_aim_constraint + ".a", 0, 1, 0, type="double3")
    cmds.setAttr(name_aim_constraint + ".u", 0, 0, 1, type="double3")
    cmds.setAttr(name_aim_constraint + ".v", lock=True, keyable=False)
    cmds.setAttr(name_aim_constraint + ".tx", lock=True, keyable=False)
    cmds.setAttr(name_aim_constraint + ".ty", lock=True, keyable=False)
    cmds.setAttr(name_aim_constraint + ".tz", lock=True, keyable=False)
    cmds.setAttr(name_aim_constraint + ".rx", lock=True, keyable=False)
    cmds.setAttr(name_aim_constraint + ".ry", lock=True, keyable=False)
    cmds.setAttr(name_aim_constraint + ".rz", lock=True, keyable=False)

    cmds.connectAttr(point_surface_node + ".position", locator_name + ".translate")
    cmds.connectAttr(point_surface_node + ".n", name_aim_constraint + ".tg[0].tt")
    cmds.connectAttr(point_surface_node + ".tv", name_aim_constraint + ".wu")
    cmds.connectAttr(name_aim_constraint + ".crx", locator_name + ".rx")
    cmds.connectAttr(name_aim_constraint + ".cry", locator_name + ".ry")
    cmds.connectAttr(name_aim_constraint + ".crz", locator_name + ".rz")
    cmds.select(locator_name)
    return locator_name


def equidistant_constraints(start, end, target_list, skip_start_end=True, constraint='parent'):
    """
    Sets equidistant transforms for a list of objects between a start and end point.
    Args:
        start (str): Path to object where it should start. In A->B, this would be "A".
        end (str): Path to the object where it should end. In A->B, this would be "B".
        target_list (list, str): A list of objects to receive the transform update.
        skip_start_end (bool, optional): If True, it will skip the start and end points, which means objects will be
                                         in-between start and end points, but not on top of start/end points.
        constraint (str): Which constraint type should be created. Supported: "parent", "point", "orient", "scale".
    Returns:
        list: A list of the created constraints. Empty if something went wrong
    """
    if not target_list:
        return
    if target_list and isinstance(target_list, str):
        target_list = [target_list]

    if skip_start_end:
        target_list.insert(0, '')  # Skip start point.
        steps = 1.0 / len(target_list)  # How much it should increase % by each iteration.
    else:
        steps = 1.0 / (len(target_list) - 1)  # -1 to reach both end point.
    percentage = 0  # Influence: range of 0.0 to 1.0

    # Determine Constraint Type
    _func = None
    if constraint == "parent":
        _func = cmds.parentConstraint
    elif constraint == "point":
        _func = cmds.pointConstraint
    elif constraint == "orient":
        _func = cmds.orientConstraint
    elif constraint == "scale":
        _func = cmds.scaleConstraint
    if not _func:
        logger.warning(f'Unable to create equidistant constraints. Invalid constraint type: "{str(constraint)}".')
        return []

    # Create Constraints
    constraints = []
    for index, obj in enumerate(target_list):
        if obj and cmds.objExists(obj):
            constraints.append(_func(start, obj, weight=1.0 - percentage)[0])
            _func(end, obj, weight=percentage)
        percentage += steps  # Increase percentage for next iteration.
    return constraints


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # equidistant_constraints(start="locator1", end="locator2", target_list=["pCube1", "pCube2", "pCube3"])
    equidistant_constraints(start="locator1", end="locator2", target_list="pCube1")
