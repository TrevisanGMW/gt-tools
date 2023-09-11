"""
Parametric Mesh Creation Scripts (Meshes with Logic or extra components)
"""
from gt.utils.data.param_meshes.mesh_data import MeshData
from random import random
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_scale_cube(name="scale_cube_volume", width=None, height=None, depth=None,
                      width_dimension=True, height_dimension=True, depth_dimension=True,
                      place_on_grid=True, pivot_pos=None):
    # Define Parameters
    parameters = {"name": name, "constructionHistory": False}
    if width:
        parameters["width"] = width
    if height:
        parameters["height"] = height
    if depth:
        parameters["depth"] = depth
    # Create Volume
    cube = cmds.polyCube(**parameters)[0]
    # Create Measurements
    locators = []
    distance_dimensions = []
    if width_dimension:
        pos_x_vertex_position = cmds.pointPosition(f"{cube}.vtx[0]", w=True)
        neg_x_vertex_position = cmds.pointPosition(f"{cube}.vtx[1]", w=True)
        distance_node = cmds.distanceDimension(sp=(random(), random()*2, random()*3),  # Random values. Set below.
                                               ep=(random()*4, random()*5, random()*6))  # Same values = No locator.
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, fullPath=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        if distance_node_transform:
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{name}_widthData'))
        if distance_node_locators[0]:
            cmds.xform(distance_node_locators[0], translation=pos_x_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[0], f"{name}_widthSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=neg_x_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{name}_widthEP"))
    if height_dimension:
        pos_y_vertex_position = cmds.pointPosition(f"{cube}.vtx[2]", w=True)
        neg_y_vertex_position = cmds.pointPosition(f"{cube}.vtx[0]", w=True)
        distance_node = cmds.distanceDimension(sp=(random(), random() * 2, random() * 3),
                                               ep=(random() * 4, random() * 5, random() * 6))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, fullPath=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        if distance_node_transform:
            cmds.xform(distance_node_locators[0], translation=pos_y_vertex_position, worldSpace=True)
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{name}_heightData'))
        if distance_node_locators[0]:
            locators.append(cmds.rename(distance_node_locators[0], f"{name}_heightSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=neg_y_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{name}_heightEP"))
    if depth_dimension:
        pos_z_vertex_position = cmds.pointPosition(f"{cube}.vtx[1]", w=True)
        neg_z_vertex_position = cmds.pointPosition(f"{cube}.vtx[7]", w=True)
        distance_node = cmds.distanceDimension(sp=(random(), random() * 2, random() * 3),
                                               ep=(random() * 4, random() * 5, random() * 6))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, fullPath=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        if distance_node_transform:
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{name}_depthData'))
        if distance_node_locators[0]:
            cmds.xform(distance_node_locators[0], translation=pos_z_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[0], f"{name}_depthSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=neg_z_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{name}_depthEP"))
    # Set Measurement Visibility
    for loc in locators:
        loc_shape = cmds.listRelatives(loc, shapes=True, fullPath=True)[0]
        for dimension in ['X', 'Y', 'Z']:
            cmds.setAttr(f'{loc_shape}.localScale{dimension}', 0)
    for obj in distance_dimensions + locators:
        cmds.setAttr(f'{obj}.overrideEnabled', 1)
        cmds.setAttr(f'{obj}.overrideDisplayType', 2)
        cmds.parent(obj, cube)
    # Determine Placement
    if place_on_grid:
        neg_y_vertex_position = cmds.pointPosition(f"{cube}.vtx[0]", w=True)  # Bottom
        original_pivot = cmds.xform(cube, piv=True, ws=True, query=True)
        cmds.xform(cube, piv=[original_pivot[0], neg_y_vertex_position[1], original_pivot[2]], ws=True)
        cmds.move(0, 0, 0, cube, a=True, rpr=True)  # rpr flag moves it according to the pivot
        cmds.makeIdentity(cube, translate=True, apply=True)
    # Determine Pivot
    if pivot_pos == "bottom":
        neg_y_vertex_position = cmds.pointPosition(f"{cube}.vtx[0]", w=True)  # Random Bottom
        original_pivot = cmds.xform(cube, piv=True, ws=True, query=True)
        cmds.xform(cube, piv=[original_pivot[0], neg_y_vertex_position[1], original_pivot[2]], ws=True)
    elif pivot_pos == "top":
        pos_y_vertex_position = cmds.pointPosition(f"{cube}.vtx[3]", w=True)  # Random Top
        original_pivot = cmds.xform(cube, piv=True, ws=True, query=True)
        cmds.xform(cube, piv=[original_pivot[0], pos_y_vertex_position[1], original_pivot[2]], ws=True)
    elif pivot_pos is not None and isinstance(pivot_pos, int):  # Vertex Number
        vertex_position = cmds.pointPosition(f"{cube}.vtx[{str(pivot_pos)}]", w=True)  # Vertex Number
        cmds.xform(cube, piv=vertex_position, ws=True)

    return MeshData(name=cube, setup=distance_dimensions + locators)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    # cmds.file(new=True, force=True)
    print(create_scale_cube(name="volume", width=61, depth=61, height=91))
