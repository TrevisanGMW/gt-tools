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


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    create_rivet()


