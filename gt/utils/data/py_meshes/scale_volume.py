"""
Parametric Mesh Creation Scripts (Meshes with Logic or extra components)
"""
from gt.utils.data.py_meshes.mesh_data import MeshData
from functools import partial
from random import random
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_scale_cube(name="scale_volume_cube", width=None, height=None, depth=None,
                      width_dimension=True, height_dimension=True, depth_dimension=True,
                      place_on_grid=True, pivot_pos="bottom"):
    """
    Create a scaled cube with optional measurement dimensions and pivot placement.

    Args:
        name (str, optional): The name for the created cube.
        width (float, optional): The width of the cube.
        height (float, optional): The height of the cube.
        depth (float, optional): The depth of the cube.
        width_dimension (bool, optional): Create a width measurement dimension. (Viewport Hud info)
        height_dimension (bool, optional): Create a height measurement dimension. (Viewport Hud info)
        depth_dimension (bool, optional): Create a depth measurement dimension. (Viewport Hud info)
        place_on_grid (bool, optional): Place the cube on the grid. (Grid would be its floor)
        pivot_pos (str or int, optional): The pivot placement options.
            Can be "bottom", "top", or a vertex number (int).

    Returns:
        MeshData: A MeshData object representing the created cube with setup information.
    """
    # Define Parameters
    parameters = {"name": name, "constructionHistory": False}
    if width:
        parameters["width"] = width
    if height:
        parameters["height"] = height
    if depth:
        parameters["depth"] = depth
    # Save selection to recover it later
    selection = cmds.ls(selection=True) or []
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
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{cube}_widthData'))
        if distance_node_locators[0]:
            cmds.xform(distance_node_locators[0], translation=pos_x_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[0], f"{cube}_widthSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=neg_x_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{cube}_widthEP"))
    if height_dimension:
        pos_y_vertex_position = cmds.pointPosition(f"{cube}.vtx[2]", w=True)
        neg_y_vertex_position = cmds.pointPosition(f"{cube}.vtx[0]", w=True)
        distance_node = cmds.distanceDimension(sp=(random(), random() * 2, random() * 3),
                                               ep=(random() * 4, random() * 5, random() * 6))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, fullPath=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        if distance_node_transform:
            cmds.xform(distance_node_locators[0], translation=pos_y_vertex_position, worldSpace=True)
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{cube}_heightData'))
        if distance_node_locators[0]:
            locators.append(cmds.rename(distance_node_locators[0], f"{cube}_heightSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=neg_y_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{cube}_heightEP"))
    if depth_dimension:
        pos_z_vertex_position = cmds.pointPosition(f"{cube}.vtx[1]", w=True)
        neg_z_vertex_position = cmds.pointPosition(f"{cube}.vtx[7]", w=True)
        distance_node = cmds.distanceDimension(sp=(random(), random() * 2, random() * 3),
                                               ep=(random() * 4, random() * 5, random() * 6))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, fullPath=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        if distance_node_transform:
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{cube}_depthData'))
        if distance_node_locators[0]:
            cmds.xform(distance_node_locators[0], translation=pos_z_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[0], f"{cube}_depthSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=neg_z_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{cube}_depthEP"))
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
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection)
        except Exception as e:
            logger.debug(f'Unable to recover selection. Issue: "{e}".')
    return MeshData(name=cube, setup=distance_dimensions + locators)


def create_scale_cylinder(name="scale_volume_cylinder", height=None, radius=None,
                          height_dimension=True, radius_dimension=True,
                          place_on_grid=True, pivot_pos="bottom"):
    """
    Create a scaled cylinder with optional measurement dimensions and pivot placement.

    Args:
        name (str, optional): The name for the created cylinder.
        height (float, optional): The height of the cylinder.
        radius (float, optional): The radius of the cylinder.
        height_dimension (bool, optional): Create a height measurement dimension. (Viewport Hud info)
        radius_dimension (bool, optional): Create a radius measurement dimension. (Viewport Hud info)
        place_on_grid (bool, optional): Place the cylinder on the grid. (Grid would be its floor)
        pivot_pos (str or int, optional): The pivot placement options.
            Can be "bottom", "top", or a vertex number (int).

    Returns:
        MeshData: A MeshData object representing the created cylinder with setup information.
    """
    # Define Parameters
    parameters = {"name": name, "constructionHistory": False,
                  "subdivisionsX": 16, "subdivisionsY": 1, "subdivisionsZ": 1,
                  "createUVs": 3}
    if height:
        parameters["height"] = height
    if radius:
        parameters["radius"] = radius
    # Save selection to recover it later
    selection = cmds.ls(selection=True) or []
    # Create Volume
    cylinder = cmds.polyCylinder(**parameters)[0]
    # Create Measurements
    locators = []
    distance_dimensions = []
    if height_dimension:
        pos_y_vertex_position = cmds.pointPosition(f"{cylinder}.vtx[27]", w=True)
        neg_y_vertex_position = cmds.pointPosition(f"{cylinder}.vtx[11]", w=True)
        distance_node = cmds.distanceDimension(sp=(random(), random() * 2, random() * 3),
                                               ep=(random() * 4, random() * 5, random() * 6))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, fullPath=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        if distance_node_transform:
            cmds.xform(distance_node_locators[0], translation=pos_y_vertex_position, worldSpace=True)
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{cylinder}_heightData'))
        if distance_node_locators[0]:
            locators.append(cmds.rename(distance_node_locators[0], f"{cylinder}_heightSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=neg_y_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{cylinder}_heightEP"))
    if radius_dimension:
        pos_z_vertex_position = cmds.pointPosition(f"{cylinder}.vtx[19]", w=True)
        neg_z_vertex_position = cmds.pointPosition(f"{cylinder}.vtx[33]", w=True)
        distance_node = cmds.distanceDimension(sp=(random(), random() * 2, random() * 3),
                                               ep=(random() * 4, random() * 5, random() * 6))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, fullPath=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        if distance_node_transform:
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{cylinder}_radiusData'))
        if distance_node_locators[0]:
            cmds.xform(distance_node_locators[0], translation=pos_z_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[0], f"{cylinder}_radiusSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=neg_z_vertex_position, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{cylinder}_radiusEP"))
    # Set Measurement Visibility
    for loc in locators:
        loc_shape = cmds.listRelatives(loc, shapes=True, fullPath=True)[0]
        for dimension in ['X', 'Y', 'Z']:
            cmds.setAttr(f'{loc_shape}.localScale{dimension}', 0)
    for obj in distance_dimensions + locators:
        cmds.setAttr(f'{obj}.overrideEnabled', 1)
        cmds.setAttr(f'{obj}.overrideDisplayType', 2)
        cmds.parent(obj, cylinder)
    # Determine Placement
    if place_on_grid:
        neg_y_vertex_position = cmds.pointPosition(f"{cylinder}.vtx[32]", w=True)  # Bottom
        original_pivot = cmds.xform(cylinder, piv=True, ws=True, query=True)
        cmds.xform(cylinder, piv=[original_pivot[0], neg_y_vertex_position[1], original_pivot[2]], ws=True)
        cmds.move(0, 0, 0, cylinder, a=True, rpr=True)  # rpr flag moves it according to the pivot
        cmds.makeIdentity(cylinder, translate=True, apply=True)
    # Determine Pivot
    if pivot_pos == "bottom":
        neg_y_vertex_position = cmds.pointPosition(f"{cylinder}.vtx[32]", w=True)  # Random Bottom
        original_pivot = cmds.xform(cylinder, piv=True, ws=True, query=True)
        cmds.xform(cylinder, piv=[original_pivot[0], neg_y_vertex_position[1], original_pivot[2]], ws=True)
    elif pivot_pos == "top":
        pos_y_vertex_position = cmds.pointPosition(f"{cylinder}.vtx[33]", w=True)  # Random Top
        original_pivot = cmds.xform(cylinder, piv=True, ws=True, query=True)
        cmds.xform(cylinder, piv=[original_pivot[0], pos_y_vertex_position[1], original_pivot[2]], ws=True)
    elif pivot_pos is not None and isinstance(pivot_pos, int):  # Vertex Number
        vertex_position = cmds.pointPosition(f"{cylinder}.vtx[{str(pivot_pos)}]", w=True)  # Vertex Number
        cmds.xform(cylinder, piv=vertex_position, ws=True)
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection)
        except Exception as e:
            logger.debug(f'Unable to recover selection. Issue: "{e}".')
    return MeshData(name=cylinder, setup=distance_dimensions + locators)


def create_scale_sphere(name="scale_volume_sphere", radius=None,
                        height_dimension=True, radius_dimension=True,
                        add_curves=True, place_on_grid=True, pivot_pos="bottom"):
    """
    Create a scaled sphere with optional measurement dimensions and pivot placement.

    Args:
        name (str, optional): The name for the created sphere.
        radius (float, optional): The radius of the sphere.
        height_dimension (bool, optional): Create a height measurement dimension. (Viewport Hud info)
        radius_dimension (bool, optional): Create a radius measurement dimension. (Viewport Hud info)
        add_curves (bool, optional): If active, it will create a curve connecting the dimension info.
        place_on_grid (bool, optional): Place the sphere on the grid. (Grid would be its floor)
        pivot_pos (str or int, optional): The pivot placement options.
            Can be "bottom", "top", or a vertex number (int).

    Returns:
        MeshData: A MeshData object representing the created sphere with setup information.
    """
    # Define Parameters
    parameters = {"name": name, "constructionHistory": False,
                  "subdivisionsX": 16, "subdivisionsY": 16,
                  "createUVs": 2}
    # polySphere -r 1 -sx 20 -sy 20 -ax 0 1 0 -cuv 2 -ch 1;
    if radius:
        parameters["radius"] = radius
    # Save selection to recover it later
    selection = cmds.ls(selection=True) or []
    # Create Volume
    sphere = cmds.polySphere(**parameters)[0]
    # Create Measurements
    locators = []
    distance_dimensions = []
    curves = []
    if height_dimension:
        pos_y_vertex_position = cmds.pointPosition(f"{sphere}.vtx[241]", w=True)
        neg_y_vertex_position = cmds.pointPosition(f"{sphere}.vtx[240]", w=True)
        out_z_vertex_pos = cmds.pointPosition(f"{sphere}.vtx[123]", w=True)
        out_x_vertex_pos = cmds.pointPosition(f"{sphere}.vtx[119]", w=True)
        distance_node = cmds.distanceDimension(sp=(random(), random() * 2, random() * 3),
                                               ep=(random() * 4, random() * 5, random() * 6))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, fullPath=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        sp_trans = [out_x_vertex_pos[0], pos_y_vertex_position[1], out_z_vertex_pos[2]]
        ep_trans = [out_x_vertex_pos[0], neg_y_vertex_position[1], out_z_vertex_pos[2]]
        if distance_node_transform:
            cmds.xform(distance_node_locators[0], translation=sp_trans, worldSpace=True)
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{sphere}_heightData'))
        if distance_node_locators[0]:
            locators.append(cmds.rename(distance_node_locators[0], f"{sphere}_heightSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=ep_trans, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{sphere}_heightEP"))
        if add_curves:
            sp_crv = cmds.curve(name=f"{sphere}_heightSP_crv",
                                point=[pos_y_vertex_position, sp_trans],
                                degree=1)
            ep_crv = cmds.curve(name=f"{sphere}_heightEP_crv",
                                point=[neg_y_vertex_position, ep_trans],
                                degree=1)
            curves.append(sp_crv)
            curves.append(ep_crv)
    if radius_dimension:
        center_vertex_position = cmds.pointPosition(f"{sphere}.vtx[241]", w=True)
        pos_x_vertex_position = cmds.pointPosition(f"{sphere}.vtx[127]", w=True)
        neg_z_vertex_position = cmds.pointPosition(f"{sphere}.vtx[115]", w=True)
        distance_node = cmds.distanceDimension(sp=(random(), random() * 2, random() * 3),
                                               ep=(random() * 4, random() * 5, random() * 6))
        distance_node_transform = cmds.listRelatives(distance_node, parent=True, fullPath=True) or [][0]
        distance_node_locators = cmds.listConnections(distance_node)
        sp_trans = [pos_x_vertex_position[0], center_vertex_position[1], neg_z_vertex_position[2]]
        ep_trans = [center_vertex_position[0], center_vertex_position[1], neg_z_vertex_position[2]]
        if distance_node_transform:
            distance_dimensions.append(cmds.rename(distance_node_transform, f'{sphere}_radiusData'))
        if distance_node_locators[0]:
            cmds.xform(distance_node_locators[0], translation=sp_trans, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[0], f"{sphere}_radiusSP"))
        if distance_node_locators[1]:
            cmds.xform(distance_node_locators[1], translation=ep_trans, worldSpace=True)
            locators.append(cmds.rename(distance_node_locators[1], f"{sphere}_radiusEP"))
        if add_curves:
            sp_middle_pos = [sp_trans[0], neg_z_vertex_position[1], sp_trans[2]]
            sp_crv = cmds.curve(name=f"{sphere}_radiusSP_crv",
                                point=[pos_x_vertex_position, sp_middle_pos, sp_trans],
                                degree=1)
            ep_crv = cmds.curve(name=f"{sphere}_radiusEP_crv",
                                point=[neg_z_vertex_position, ep_trans],
                                degree=1)
            curves.append(sp_crv)
            curves.append(ep_crv)
    # Set Measurement Visibility
    for loc in locators:
        loc_shape = cmds.listRelatives(loc, shapes=True, fullPath=True)[0]
        for dimension in ['X', 'Y', 'Z']:
            cmds.setAttr(f'{loc_shape}.localScale{dimension}', 0)
    for obj in distance_dimensions + locators + curves:
        cmds.setAttr(f'{obj}.overrideEnabled', 1)
        cmds.setAttr(f'{obj}.overrideDisplayType', 2)
        cmds.parent(obj, sphere)
    # Determine Placement
    if place_on_grid:
        neg_y_vertex_position = cmds.pointPosition(f"{sphere}.vtx[240]", w=True)  # Bottom
        original_pivot = cmds.xform(sphere, piv=True, ws=True, query=True)
        cmds.xform(sphere, piv=[original_pivot[0], neg_y_vertex_position[1], original_pivot[2]], ws=True)
        cmds.move(0, 0, 0, sphere, a=True, rpr=True)  # rpr flag moves it according to the pivot
        cmds.makeIdentity(sphere, translate=True, apply=True)
    # Determine Pivot
    if pivot_pos == "bottom":
        neg_y_vertex_position = cmds.pointPosition(f"{sphere}.vtx[240]", w=True)  # Random Bottom
        original_pivot = cmds.xform(sphere, piv=True, ws=True, query=True)
        cmds.xform(sphere, piv=[original_pivot[0], neg_y_vertex_position[1], original_pivot[2]], ws=True)
    elif pivot_pos == "top":
        pos_y_vertex_position = cmds.pointPosition(f"{sphere}.vtx[241]", w=True)  # Random Top
        original_pivot = cmds.xform(sphere, piv=True, ws=True, query=True)
        cmds.xform(sphere, piv=[original_pivot[0], pos_y_vertex_position[1], original_pivot[2]], ws=True)
    elif pivot_pos is not None and isinstance(pivot_pos, int):  # Vertex Number
        vertex_position = cmds.pointPosition(f"{sphere}.vtx[{str(pivot_pos)}]", w=True)  # Vertex Number
        cmds.xform(sphere, piv=vertex_position, ws=True)
    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection)
        except Exception as e:
            logger.debug(f'Unable to recover selection. Issue: "{e}".')
    return MeshData(name=sphere, setup=distance_dimensions + locators)


create_kitchen_cabinet = partial(create_scale_cube, name="scale_volume_kitchen_cabinet", width=61, depth=61, height=91)
create_kitchen_cabinet.__doc__ = create_scale_cube.__doc__
create_kitchen_stool = partial(create_scale_cylinder, name="scale_volume_kitchen_stool", radius=18, height=76.5)
create_kitchen_stool.__doc__ = create_scale_cylinder.__doc__


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)
    create_scale_sphere()
