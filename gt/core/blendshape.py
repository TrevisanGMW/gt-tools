"""
Blendshape Utilities

Import Line:
    import gt.core.blendshape as core_bs
"""

import maya.cmds as cmds
import maya.mel as mel
import logging
import os
import gt.core.io as core_io

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_blendshape_node_from_target(node, shape=None):
    """
    Gets blendshape targets
    Args:
        node (node): Transform to get the blendshapes from.
        shape (bool, none): If True, the node is a shape.
    Returns:
        bs_list (list) : List of blendshapes
    """
    if not shape:
        shape = cmds.listRelatives(node, type="shape")[0]
    bs_list = cmds.listConnections(shape, type="blendShape")
    return bs_list


def get_targets(blendshape):
    """
    Gets blendshape targets
    Args:
        blendshape (node): Blendshape node to get the targets from
    Returns:
        target_list (list)
    """
    target_list = cmds.listAttr(f"{blendshape}.w", multi=True)
    return target_list


def extract_geo_from_targets(node, blendshape=None):
    """
    Generates the geometries for the targets of the blendshapes of the geometry.
    Args:
        node (node): Transform to get the blendshapes from.
        blendshape (bool, none): Blendshape node to get the targets from. If not specified it will iterate through
        all the blendshapes.
    Returns:
        geo_list (list): List of geometries.
    """
    if blendshape:
        bs_nodes = [blendshape]
    else:
        bs_nodes = get_blendshape_node_from_target(node)
    geo_list = []
    for blendshape in bs_nodes:
        target_list = get_targets(blendshape)
        target_geos = []
        for target in target_list:
            cmds.setAttr(f"{blendshape}.{target}", 1)
            dup_geo = cmds.duplicate(node, n=target)
            target_geos.append(dup_geo)
            cmds.setAttr(f"{blendshape}.{target}", 0)
        geo_list += target_list
    return geo_list


def transfer_blendshapes_to_target(source, target, blendshape=None, retain_duplicates=False):
    """
    Transfers the blendshapes from one geometry to another (they should have the same vertex id).
    Args:
        source (node): Transform to get the blendshapes from.
        target (node): Transform to copy the blendshapes to.
        blendshape (bool, none): Blendshape node to get the targets from. If not specified it will iterate
                                 through all the blendshapes.
        retain_duplicates (bool): If True, it won't delete the duplicate geometries.
    """
    if blendshape:
        source_blendshapes = [blendshape]
    else:
        source_blendshapes = get_blendshape_node_from_target(source)
    for bs in source_blendshapes:
        geos_to_copy = extract_geo_from_targets(source, blendshape=bs)
        new_bs = cmds.blendShape(target, n=f"BS_{target}")[0]
        for geo in geos_to_copy:
            cmds.blendShape(new_bs, e=True, t=(target, geos_to_copy.index(geo), geo, 1))
            if not retain_duplicates:
                cmds.delete(geo)


def transfer_variation_blendshapes_to_lods(mesh):
    """
    Transfers the variation blendshapes to the source one and propagates it to LODs,
    after that it will rename the blendshape targets. It will try to do up to LOD3.
    Args:
        mesh (str): Mesh to transfer the variations to. (ex. 'Male_Mid_Mesh_LOD' , make sure to not include the number)
    """

    variations = ["Slim", "MidAth", "SlimAth", "Big", "BigAth"]
    for index in range(4):
        geo = f"{mesh}{index}"
        geo_bs = cmds.blendShape(geo, n=f"BS_{geo}")[0]
        i = 0
        for var in variations:
            geo_name = geo.replace("Mid", var)
            cmds.blendShape(geo_bs, e=True, t=(geo, variations.index(var), geo_name, 1))
            mel.eval("blendShapeRenameTargetAlias " + "BS_" + geo + " " + str(i) + " " + var)
            i += 1


def get_vertices_world_pos(source_mesh):
    """
    Gets the vertex of the target mesh in worldspace position and returns them.
    Args:
        source_mesh (str): Mesh to extract the vertex positions from.

    Returns:
        vert_pos_map (dict): Dictionary with the vertex index of all the vertex positions.
    """
    vert_pos_map = {}
    mesh_verts = cmds.ls(f"{source_mesh}.vtx[*]", fl=1)

    for v in mesh_verts:
        vert_id = int(v[v.find("[") + 1 :][0:-1])
        vert_pos = cmds.xform(v, q=True, t=True, ws=True)
        vert_pos_map[vert_id] = vert_pos

    return vert_pos_map


def get_deltas_from_pos_maps(source_pos_map, target_pos_map, remove_zeros=False):
    """
    Gets the deltas between two meshes and converts them into a dictionary.
    Args:
        source_pos_map (dict): Dictionary of the mesh we want to have the deltas extracted from (usually the base mesh).
        target_pos_map (dict): Dictionary of the mesh we want to have the deltas applied to.
        remove_zeros (bool): If we want to skip the vertex that don't move.

    Returns:
        deltas_map (dict): Dictionary with the vertex id and the deltas per each vertex.
    """
    deltas_map = {}
    for v_id in source_pos_map.keys():
        delta_pos = [
            target_pos_map[v_id][0] - source_pos_map[v_id][0],
            target_pos_map[v_id][1] - source_pos_map[v_id][1],
            target_pos_map[v_id][2] - source_pos_map[v_id][2],
        ]
        if remove_zeros:
            if delta_pos == [0.0, 0.0, 0.0]:
                continue
        deltas_map[v_id] = delta_pos
    return deltas_map


def apply_deltas_from_pos_map(target_mesh, target_vertex_dict):
    """
    Applies the deltas from one mesh to another
    Args:
        target_mesh (str): Mesh to extract the vertex positions from.
        target_vertex_dict (dict): Dictionary with the deltas to apply to the target mesh.
    """
    for v_id in target_vertex_dict.keys():
        cmds.xform(f"{target_mesh}.vtx[{v_id}]", t=target_vertex_dict[v_id], r=True, ws=True)


def write_deltas_json(source_mesh, target_meshes, file_path, remove_zeros=False):
    """
    Writes a json with all deltas between one mesh and a list of meshes.
    Args:
        source_mesh (str): Mesh to extract the vertex positions from.
        target_meshes (str, list): Mesh/es that we want the deltas from.
        file_path (path): Path to save the json.
        remove_zeros (bool): If we want to skip the vertex that don't move.
    """
    if isinstance(target_meshes, str):
        target_meshes = [target_meshes]
    all_deltas_dict = {}
    source_vtx_dict = get_vertices_world_pos(source_mesh)
    for mesh in target_meshes:
        target_vtx_dict = get_vertices_world_pos(mesh)
        deltas_dict = get_deltas_from_pos_maps(source_vtx_dict, target_vtx_dict, remove_zeros=remove_zeros)
        all_deltas_dict[mesh] = deltas_dict
    if all_deltas_dict:
        if file_path and os.path.exists(file_path):
            core_io.set_file_permission_modifiable(file_path)
        core_io.write_json(path=file_path, data=all_deltas_dict)
        logger.info(f"Saving new json at {file_path}")
    return all_deltas_dict


def apply_all_deltas_to_mesh_from_dict(target_mesh, deltas_dict, apply_bs=True, retain_targets=False):
    """
    Applies deltas to mesh(es) from either a dictionary or a JSON file path.
    Args:
        target_mesh (str): The target mesh (used if deltas are not nested).
        deltas_dict (dict or str): Either a dictionary of deltas, or a path to a JSON file.
        apply_bs (bool): Selects if you want to apply all the resulting meshes as blendshapes to the target mesh.
        retain_targets (bool): Selects if you want to delete all the targets after applying the blendshape.
    """
    if isinstance(deltas_dict, str) and deltas_dict.lower().endswith(".json"):
        if not os.path.exists(deltas_dict):
            logger.error(f"Delta file '{deltas_dict}' not found.")
        else:
            deltas_dict = core_io.read_json_dict(deltas_dict)
    elif isinstance(deltas_dict, dict):
        deltas_dict = deltas_dict
    else:
        logger.error("Please input a dictionary or a .json file for the deltas.")

    new_meshes = []
    # Check if it is a nested dictionary.
    if isinstance(deltas_dict[next(iter(deltas_dict))], dict):
        # Is nested
        for key in deltas_dict.keys():
            target_bs_mesh = cmds.duplicate(target_mesh, n=key)[0]
            apply_deltas_from_pos_map(target_bs_mesh, deltas_dict[key])
            new_meshes.append(target_bs_mesh)
    else:
        target_bs_mesh = cmds.duplicate(target_mesh, n=f"{target_mesh}_delta")[0]
        apply_deltas_from_pos_map(target_bs_mesh, deltas_dict)
        new_meshes.append(target_bs_mesh)

    if apply_bs:
        new_bs = cmds.blendShape(target_mesh, n=f"BS_{target_mesh}")[0]
        for geo in new_meshes:
            cmds.blendShape(new_bs, e=True, t=(target_mesh, new_meshes.index(geo), geo, 1))
            if not retain_targets:
                cmds.delete(geo)
