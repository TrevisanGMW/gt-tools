"""
Material Module

Import Line:
    import gt.core.material as core_mat
"""

import gt.core.feedback as core_fback
import gt.core.naming as core_naming
import gt.core.undo as core_undo
import gt.core.io as core_io
import maya.api.OpenMaya as om2
import maya.cmds as cmds
import logging
import shutil
import glob
import math
import stat
import os

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


DEFAULT_MATERIALS = {
    "lambert1",
    "particleCloud1",
    "shaderGlow1",
    "standardSurface1",

    # Maya 2027 / modern defaults
    "openPBR_shader1",

    # Arnold defaults (commonly present even if unused)
    "aiStandardSurface1",
    "aiShadowMatte1",
    "aiAmbientOcclusion1",
}


class CommonMaterials:
    def __init__(self):
        """
        Basic Material Types
        """

    lambert = "lambert"
    blinn = "blinn"
    phong = "phong"
    surface = "surfaceShader"
    open_pbr = "openPBRSurface"


def get_all_materials(
    assigned_only=False,
    include_unassigned=True,
    exclude_defaults=False,
    material_types=None,
):
    """
    Get materials from the Maya scene with flexible filtering options.

    Args:
        assigned_only (bool):
            If True, only return materials connected to shading engines.

        include_unassigned (bool):
            If True (default), includes unassigned materials.

        exclude_defaults (bool):
            Removes Maya + renderer default materials.

        material_types (str | list[str] | None):
            Filter by shader type prefix. (Strings are auto converted to a list with one word)

    Returns:
        list[str]: Material node names.
    """

    materials = set()

    # ------------------------------------------------------------
    # 1. Assigned materials ONLY
    # ------------------------------------------------------------
    if assigned_only:
        shading_engines = cmds.ls(type="shadingEngine") or []

        for engine in shading_engines:
            for attr in ("surfaceShader", "volumeShader", "displacementShader"):
                materials.update(
                    cmds.listConnections(
                        f"{engine}.{attr}",
                        source=True,
                        destination=False,
                    ) or []
                )

    # ------------------------------------------------------------
    # 2. All materials (including unassigned)
    # ------------------------------------------------------------
    if include_unassigned:
        materials.update(cmds.ls(materials=True) or [])

    # ------------------------------------------------------------
    # 3. Filter defaults
    # ------------------------------------------------------------
    if exclude_defaults:
        materials -= DEFAULT_MATERIALS

    # ------------------------------------------------------------
    # 4. Filter by type prefix
    # ------------------------------------------------------------
    if material_types:
        if isinstance(material_types, str):
            material_types = [material_types]

        material_types = tuple(material_types)

        materials = {
            m for m in materials
            if cmds.nodeType(m).startswith(material_types)
        }

    return sorted(materials)


def material_exists(material_name):
    """
    Checks if a material exists in the scene by searching through materials connected to shading engines.

    Args:
        material_name (str): The name of the material to check.

    Returns:
        bool: True if the material exists, False otherwise.
    """
    materials = get_all_materials()
    return material_name in materials


def get_shading_engine(material_name):
    """
    Retrieves the shadingEngine node connected to a specified material.

    Args:
        material_name (str): The name of the material.

    Returns:
        str or None: The shadingEngine node if found, otherwise None.
    """
    # Find the shadingEngine connected to the material's outColor or outTransparency
    shading_engines = cmds.listConnections(
        material_name + ".outColor", source=False, destination=True, type="shadingEngine"
    )

    # If no shading engine was found on outColor, try outTransparency (for transparent materials)
    if not shading_engines:
        shading_engines = cmds.listConnections(
            material_name + ".outTransparency", source=False, destination=True, type="shadingEngine"
        )

    # Return the first shading engine if found, otherwise None
    return shading_engines[0] if shading_engines else None


def assign_material(
    obj_list, rgb_color=(1, 0, 0), material_type=CommonMaterials.lambert, material_name=None, is_unique=True
):
    """
    Assigns a material with a specified color to a list of objects.

    Args:
        obj_list (str, List[str]): The name of the Maya object to assign the material to or a list of objects.
        rgb_color (tuple, optional): A tuple of three floats representing RGB values (default is green: (0, 1, 0)).
        material_type (str): A material type. e.g. "lambert". Use elements from the class "CommonMaterials".
        material_name (str, optional): Material name, if not provided it becomes "M_ + material_type"
        is_unique (bool, optional): If True it will try to use an existing material before creating one.
    Returns:
        str: Name of the assigned material.
    """
    # Convert string to list
    if obj_list and isinstance(obj_list, str):
        obj_list = [obj_list]
    if len(obj_list) == 0:
        logger.debug(f'No valid objects provided. "Assign material" operation was skipped.')
        return None
    # Determine material name
    if not material_name:
        material_name = f"{core_naming.NamingConstants.Prefix.MAT}_{material_type}"
    # Find existing
    if is_unique and material_exists(material_name):
        material_name = material_name
        shading_group = get_shading_engine(material_name)
    else:
        material_name = cmds.shadingNode(material_type, asShader=True, name=material_name)
        shading_group = None
    # Create missing shading group
    if not shading_group:
        shading_group = cmds.sets(renderable=True, noSurfaceShader=True, empty=True, name=f"{material_name}SG")
        cmds.connectAttr(f"{material_name}.outColor", f"{shading_group}.surfaceShader", force=True)
    # Set the color of the material (supports legacy + OpenPBR)
    if rgb_color:
        color_attr = None

        # Prefer OpenPBR / modern shaders
        if cmds.attributeQuery("baseColor", node=material_name, exists=True):
            color_attr = "baseColor"
        elif cmds.attributeQuery("color", node=material_name, exists=True):
            color_attr = "color"

        if color_attr:
            cmds.setAttr(
                f"{material_name}.{color_attr}",
                rgb_color[0], rgb_color[1], rgb_color[2],
                type="double3"
            )
        else:
            logger.warning(f"No supported color attribute found on {material_name}")
    # Assign to objects
    for obj in obj_list:
        cmds.sets(obj, edit=True, forceElement=shading_group)

    return material_name


# --------------------------------------- Component Material Transfer ---------------------------------------
class MaterialTransferMode:
    def __init__(self):
        """
        Strategies available when transferring material assignments between objects.
        """

    object_shader = "object_shader"
    component_index = "component_index"
    component_position = "component_position"


class ComponentSpace:
    def __init__(self):
        """
        Coordinate spaces available when matching components by position.
        """

    world = "world"
    object_space = "object"


# Default distance accepted when matching component positions.
DEFAULT_POSITION_TOLERANCE = 0.001

# Session clipboard used by "copy_component_materials" and "paste_component_materials".
_component_material_clipboard = {}


def get_material_from_shading_engine(shading_engine):
    """
    Retrieves the surface material connected to a shading engine.

    Args:
        shading_engine (str): Name of the shadingEngine node.

    Returns:
        str or None: The material name if found, otherwise None.
    """
    if not shading_engine or not cmds.objExists(shading_engine):
        return None
    materials = cmds.listConnections(f"{shading_engine}.surfaceShader", source=True, destination=False) or []
    return materials[0] if materials else None


def get_mesh_shape(obj):
    """
    Resolves the mesh shape of an object. Accepts transforms, shapes and component strings.

    Args:
        obj (str): Object name. e.g. "pCube1", "pCubeShape1" or "pCube1.f[0]".

    Returns:
        str or None: Long name of the mesh shape, otherwise None when no mesh shape was found.
    """
    if not obj or not isinstance(obj, str):
        return None
    node_name = obj.split(".")[0]
    if not cmds.objExists(node_name):
        return None
    if cmds.objectType(node_name) == "mesh":
        return cmds.ls(node_name, long=True)[0]
    shapes = cmds.listRelatives(node_name, shapes=True, fullPath=True, noIntermediate=True) or []
    for shape in shapes:
        if cmds.objectType(shape) == "mesh":
            return shape
    return None


def get_selected_face_indices(selection=None):
    """
    Extracts polygon faces out of a selection, grouped per mesh shape.

    Args:
        selection (list, optional): Objects/components to inspect. When None, the current selection is used.

    Returns:
        dict: Map of mesh shape long name to a sorted list of face indices.
              Empty dictionary when no face component was found.
    """
    if selection is None:
        selection = cmds.ls(selection=True, long=True) or []
    if not selection:
        return {}
    faces = cmds.filterExpand(selection, selectionMask=34, expand=True) or []
    face_data = {}
    for face in faces:
        shape = get_mesh_shape(face)
        if not shape:
            continue
        try:
            face_index = int(face.rsplit("[", 1)[-1].rstrip("]"))
        except ValueError:
            logger.debug(f'Unable to extract a face index out of "{face}".')
            continue
        face_data.setdefault(shape, set()).add(face_index)
    return {shape: sorted(indices) for shape, indices in face_data.items()}


def _get_mesh_function_set(shape):
    """
    Builds an OpenMaya mesh function set for a mesh shape.

    Args:
        shape (str): Long name of a mesh shape.

    Returns:
        tuple: (MFnMesh, MDagPath) built out of the provided shape.
    """
    selection_list = om2.MSelectionList()
    selection_list.add(shape)
    dag_path = selection_list.getDagPath(0)
    return om2.MFnMesh(dag_path), dag_path


def get_face_shading_engines(mesh):
    """
    Retrieves the shading engines assigned to each face of a mesh.

    Args:
        mesh (str): Mesh transform, shape or component string.

    Returns:
        tuple: (shading_engines, face_slots) where "shading_engines" is a list of shadingEngine names and
               "face_slots" is a list with one entry per face holding the index of the assigned shading
               engine, or "-1" when the face has no assignment. Returns ([], []) for invalid meshes.
    """
    shape = get_mesh_shape(mesh)
    if not shape:
        logger.debug(f'Unable to find a mesh shape for "{mesh}".')
        return [], []
    mesh_fn, dag_path = _get_mesh_function_set(shape)
    shader_objects, face_slots = mesh_fn.getConnectedShaders(dag_path.instanceNumber())
    shading_engines = [om2.MFnDependencyNode(shader_object).name() for shader_object in shader_objects]
    return shading_engines, list(face_slots)


def get_face_centers(mesh, space=ComponentSpace.object_space):
    """
    Computes the average position (center) of every face of a mesh.

    Args:
        mesh (str): Mesh transform, shape or component string.
        space (str, optional): A ComponentSpace value. Defaults to object (local) space.

    Returns:
        list: List of (x, y, z) tuples, one per face. Empty list for invalid meshes.
    """
    shape = get_mesh_shape(mesh)
    if not shape:
        logger.debug(f'Unable to find a mesh shape for "{mesh}".')
        return []
    mesh_fn, _ = _get_mesh_function_set(shape)
    om_space = om2.MSpace.kWorld if space == ComponentSpace.world else om2.MSpace.kObject
    points = mesh_fn.getPoints(om_space)
    vertex_counts, vertex_indices = mesh_fn.getVertices()
    centers = []
    index_offset = 0
    for vertex_count in vertex_counts:
        sum_x = 0.0
        sum_y = 0.0
        sum_z = 0.0
        for offset in range(vertex_count):
            point = points[vertex_indices[index_offset + offset]]
            sum_x += point.x
            sum_y += point.y
            sum_z += point.z
        index_offset += vertex_count
        if vertex_count:
            centers.append((sum_x / vertex_count, sum_y / vertex_count, sum_z / vertex_count))
        else:
            centers.append((0.0, 0.0, 0.0))
    return centers


def _get_index_ranges(indices):
    """
    Groups indices into contiguous ranges.

    Args:
        indices (list): Iterable of integers.

    Returns:
        list: List of (start, end) tuples, inclusive on both ends.
    """
    ranges = []
    for index in sorted(set(indices)):
        if ranges and index == ranges[-1][1] + 1:
            ranges[-1][1] = index
        else:
            ranges.append([index, index])
    return [(start, end) for start, end in ranges]


def _compress_face_indices(shape, face_indices):
    """
    Builds compact face component strings out of face indices.
    e.g. [0, 1, 2, 7] becomes ["shape.f[0:2]", "shape.f[7]"].

    Args:
        shape (str): Mesh shape (or transform) used as the component prefix.
        face_indices (list): Face indices to compress.

    Returns:
        list: List of component strings.
    """
    components = []
    for start_index, end_index in _get_index_ranges(face_indices):
        if start_index == end_index:
            components.append(f"{shape}.f[{start_index}]")
        else:
            components.append(f"{shape}.f[{start_index}:{end_index}]")
    return components


def assign_faces_to_shading_engine(shape, face_indices, shading_engine):
    """
    Assigns a list of faces to a shading engine.

    Args:
        shape (str): Mesh shape (or transform) used as the component prefix.
        face_indices (list): Face indices to assign.
        shading_engine (str): Target shadingEngine node.

    Returns:
        int: Number of faces assigned. Zero when nothing could be assigned.
    """
    if not face_indices or not shading_engine or not cmds.objExists(shading_engine):
        return 0
    components = _compress_face_indices(shape, face_indices)
    try:
        cmds.sets(components, edit=True, forceElement=shading_engine)
    except Exception as exception:
        logger.warning(f'Unable to assign faces to "{shading_engine}". Issue: "{exception}".')
        return 0
    return len(set(face_indices))


def _get_cell_key(position, cell_size):
    """
    Determines the uniform grid cell of a position.

    Args:
        position (tuple): An (x, y, z) point.
        cell_size (float): Size of each grid cell. Must be greater than zero.

    Returns:
        tuple: Grid cell key as three integers.
    """
    return (
        int(math.floor(position[0] / cell_size)),
        int(math.floor(position[1] / cell_size)),
        int(math.floor(position[2] / cell_size)),
    )


def _build_position_hash(positions, cell_size):
    """
    Buckets positions into a uniform grid so nearby points can be found without comparing every pair.

    Args:
        positions (list): List of (x, y, z) tuples.
        cell_size (float): Size of each grid cell. Must be greater than zero.

    Returns:
        dict: Map of cell key to a list of position indices.
    """
    position_hash = {}
    for position_index, position in enumerate(positions):
        position_hash.setdefault(_get_cell_key(position, cell_size), []).append(position_index)
    return position_hash


def _get_hash_cell_bounds(position_hash):
    """
    Determines the populated area of a position hash.

    Args:
        position_hash (dict): Output of "_build_position_hash".

    Returns:
        tuple or None: (min_cell, max_cell) cell keys covering every populated cell.
                       None when the hash is empty.
    """
    if not position_hash:
        return None
    cell_keys = list(position_hash.keys())
    min_cell = tuple(min(cell_key[axis] for cell_key in cell_keys) for axis in range(3))
    max_cell = tuple(max(cell_key[axis] for cell_key in cell_keys) for axis in range(3))
    return min_cell, max_cell


def _estimate_cell_size(positions, minimum_cell_size=DEFAULT_POSITION_TOLERANCE):
    """
    Estimates a grid cell size that keeps roughly one position per cell. Cells that are too small make
    the closest-position search expand over many empty cells, so the size follows the point density.

    Args:
        positions (list): List of (x, y, z) tuples.
        minimum_cell_size (float, optional): Smallest size accepted. Usually the match tolerance, so the
            neighborhood search stays valid.

    Returns:
        float: Cell size to use when building a position hash.
    """
    smallest_size = max(minimum_cell_size, DEFAULT_POSITION_TOLERANCE)
    if not positions:
        return smallest_size
    largest_extent = 0.0
    for axis in range(3):
        axis_values = [position[axis] for position in positions]
        largest_extent = max(largest_extent, max(axis_values) - min(axis_values))
    if largest_extent <= 0:
        return smallest_size
    divisions = max(1, int(round(len(positions) ** (1.0 / 3.0))))
    return max(largest_extent / divisions, smallest_size)


def _get_cell_shell_keys(base_cell, radius, cell_bounds=None):
    """
    Builds the cell keys sitting exactly at a given distance (in cells) from a base cell, optionally
    limited to the populated area of the grid. Clipping the shell keeps the search cheap when the base
    cell is far away from the populated cells.

    Args:
        base_cell (tuple): Cell key at the center of the search.
        radius (int): Distance in cells. Zero returns the base cell itself.
        cell_bounds (tuple, optional): Output of "_get_hash_cell_bounds". When provided, cells outside
            the populated area are left out.

    Returns:
        list: Cell keys forming the shell.
    """
    axis_ranges = []
    for axis in range(3):
        lowest_cell = base_cell[axis] - radius
        highest_cell = base_cell[axis] + radius
        if cell_bounds:
            lowest_cell = max(lowest_cell, cell_bounds[0][axis])
            highest_cell = min(highest_cell, cell_bounds[1][axis])
        axis_ranges.append(range(lowest_cell, highest_cell + 1))

    shell_keys = []
    for cell_x in axis_ranges[0]:
        for cell_y in axis_ranges[1]:
            for cell_z in axis_ranges[2]:
                offset_x = abs(cell_x - base_cell[0])
                offset_y = abs(cell_y - base_cell[1])
                offset_z = abs(cell_z - base_cell[2])
                if max(offset_x, offset_y, offset_z) != radius:
                    continue
                shell_keys.append((cell_x, cell_y, cell_z))
    return shell_keys


def _get_search_radius_range(base_cell, cell_bounds):
    """
    Determines the smallest and largest useful search radius (in cells) for a base cell. Starting at the
    smallest radius skips the empty shells between a far away base cell and the populated cells.

    Args:
        base_cell (tuple): Cell key at the center of the search.
        cell_bounds (tuple or None): Output of "_get_hash_cell_bounds".

    Returns:
        tuple: (min_radius, max_radius). Returns (0, 1) when the bounds are unknown.
    """
    if not cell_bounds:
        return 0, 1
    min_cell, max_cell = cell_bounds
    min_radius = 0
    max_radius = 1
    for axis in range(3):
        min_radius = max(min_radius, min_cell[axis] - base_cell[axis], base_cell[axis] - max_cell[axis])
        max_radius = max(max_radius, abs(base_cell[axis] - min_cell[axis]), abs(base_cell[axis] - max_cell[axis]))
    return max(0, min_radius), max_radius


def _find_closest_position_index(position, positions, position_hash, cell_size, tolerance=None, cell_bounds=None):
    """
    Finds the closest position using a uniform grid.
    The cell size must be equal or greater than the tolerance, otherwise valid candidates
    may sit outside the searched neighborhood.

    Args:
        position (tuple): The (x, y, z) point being matched.
        positions (list): Candidate (x, y, z) tuples (the same list used to build the hash).
        position_hash (dict): Output of "_build_position_hash".
        cell_size (float): Cell size used to build the hash.
        tolerance (float, optional): Maximum distance accepted for a match. When None, the search expands
            over the grid until the closest candidate is found, no matter how far away it is.
        cell_bounds (tuple, optional): Output of "_get_hash_cell_bounds". Used to stop the expansion when
            no tolerance is provided.

    Returns:
        int or None: Index of the closest candidate, otherwise None when nothing was found.
    """
    if not positions or not position_hash:
        return None
    base_cell = _get_cell_key(position, cell_size)
    squared_tolerance = None if tolerance is None else tolerance * tolerance
    if squared_tolerance is not None:
        # Anything within the tolerance sits in the immediate neighborhood, since cells are never smaller
        radius, max_radius = 0, 1
        search_bounds = None
    else:
        radius, max_radius = _get_search_radius_range(base_cell, cell_bounds)
        search_bounds = cell_bounds
    closest_index = None
    closest_distance = None
    while radius <= max_radius:
        for cell_key in _get_cell_shell_keys(base_cell, radius, cell_bounds=search_bounds):
            for candidate_index in position_hash.get(cell_key, []):
                candidate = positions[candidate_index]
                delta_x = candidate[0] - position[0]
                delta_y = candidate[1] - position[1]
                delta_z = candidate[2] - position[2]
                squared_distance = delta_x * delta_x + delta_y * delta_y + delta_z * delta_z
                if squared_tolerance is not None and squared_distance > squared_tolerance:
                    continue
                if closest_distance is None or squared_distance < closest_distance:
                    closest_distance = squared_distance
                    closest_index = candidate_index
        if closest_distance is not None:
            # Cells beyond this radius cannot hold anything closer than the current best candidate
            reachable_distance = radius * cell_size
            if closest_distance <= reachable_distance * reachable_distance:
                break
        radius += 1
    return closest_index


def _match_source_position_index(
    position,
    positions,
    position_hash,
    cell_size,
    tolerance,
    fallback_closest=True,
    cell_bounds=None,
):
    """
    Matches a target position against the source positions, optionally accepting the closest position
    available when nothing sits within the tolerance.

    Args:
        position (tuple): The (x, y, z) point being matched.
        positions (list): Candidate (x, y, z) tuples (the same list used to build the hash).
        position_hash (dict): Output of "_build_position_hash".
        cell_size (float): Cell size used to build the hash.
        tolerance (float): Distance within which a candidate counts as an exact match.
        fallback_closest (bool, optional): When True, the closest candidate is used even when it sits
            outside the tolerance. Defaults to True.
        cell_bounds (tuple, optional): Output of "_get_hash_cell_bounds".

    Returns:
        tuple: (index, is_approximate) where "index" is None when nothing was matched and
               "is_approximate" is True when the match was found outside the tolerance.
    """
    match_index = _find_closest_position_index(
        position=position,
        positions=positions,
        position_hash=position_hash,
        cell_size=cell_size,
        tolerance=tolerance,
    )
    if match_index is not None:
        return match_index, False
    if not fallback_closest:
        return None, False
    match_index = _find_closest_position_index(
        position=position,
        positions=positions,
        position_hash=position_hash,
        cell_size=cell_size,
        tolerance=None,
        cell_bounds=cell_bounds,
    )
    return match_index, match_index is not None


def get_component_material_clipboard():
    """
    Retrieves the data stored by the last "copy_component_materials" call.

    Returns:
        dict: A shallow copy of the clipboard data. Empty dictionary when nothing was copied yet.
    """
    return dict(_component_material_clipboard)


def clear_component_material_clipboard():
    """Clears the component material clipboard."""
    _component_material_clipboard.clear()


def _get_clipboard_material_names(clipboard_data):
    """
    Retrieves the sorted material names used by the copied faces.

    Args:
        clipboard_data (dict): Clipboard data as created by "copy_component_materials".

    Returns:
        list: Sorted material names. Shading engine names are used when a material is unavailable.
    """
    shading_engines = clipboard_data.get("shading_engines") or []
    materials = clipboard_data.get("materials") or []
    names = set()
    for slot in set(clipboard_data.get("shader_slots") or []):
        name = None
        if 0 <= slot < len(materials):
            name = materials[slot]
        if not name and 0 <= slot < len(shading_engines):
            name = shading_engines[slot]
        if name:
            names.add(name)
    return sorted(names)


def get_component_material_clipboard_summary(clipboard_data=None):
    """
    Builds a short human readable description of the component material clipboard.

    Args:
        clipboard_data (dict, optional): Data to describe. When None, the module clipboard is used.

    Returns:
        str: One line summary. e.g. "pCubeShape1 - 6 faces, 2 materials (M_body, M_head)".
    """
    data = clipboard_data if clipboard_data is not None else _component_material_clipboard
    if not data or not data.get("faces"):
        return "Clipboard is empty."
    source_name = (data.get("source") or "unknown source").split("|")[-1]
    face_quantity = len(data.get("faces") or [])
    material_names = _get_clipboard_material_names(data)
    materials_text = ", ".join(material_names) if material_names else "no materials"
    return f"{source_name} - {face_quantity} faces, {len(material_names)} materials ({materials_text})"


def _resolve_clipboard_shading_engine(clipboard_data, slot):
    """
    Resolves the shading engine stored in a clipboard slot, falling back to the material name when the
    original shading engine is no longer available.

    Args:
        clipboard_data (dict): Clipboard data as created by "copy_component_materials".
        slot (int): Index of the shading engine slot.

    Returns:
        str or None: A shadingEngine node name, otherwise None when it could not be resolved.
    """
    shading_engines = clipboard_data.get("shading_engines") or []
    materials = clipboard_data.get("materials") or []
    shading_engine = shading_engines[slot] if 0 <= slot < len(shading_engines) else None
    if shading_engine and cmds.objExists(shading_engine):
        return shading_engine
    material_name = materials[slot] if 0 <= slot < len(materials) else None
    if material_name and cmds.objExists(material_name):
        resolved_engine = get_shading_engine(material_name)
        if resolved_engine:
            return resolved_engine
    logger.warning(f'Unable to resolve the shading engine stored for the material "{material_name}".')
    return None


def _resolve_copy_source(source, face_indices):
    """
    Determines which mesh and faces should be copied.

    Args:
        source (str or None): Mesh transform, shape or component string. When None, the selection is used.
        face_indices (list or None): Explicit face indices. When None, they are resolved from the selection.

    Returns:
        tuple: (shape, face_indices) where "shape" may be None when no mesh was found and "face_indices"
               may be None, meaning "every face".
    """
    if source is not None:
        return get_mesh_shape(source), face_indices
    selection = cmds.ls(selection=True, long=True) or []
    selected_faces = get_selected_face_indices(selection)
    if selected_faces:
        shapes = list(selected_faces.keys())
        if len(shapes) > 1:
            logger.warning(f'Multiple meshes found in the selection. Using "{shapes[0]}" as the source.')
        if face_indices is None:
            face_indices = selected_faces[shapes[0]]
        return shapes[0], face_indices
    for selected_item in selection:
        shape = get_mesh_shape(selected_item)
        if shape:
            return shape, face_indices
    return None, face_indices


def copy_component_materials(source=None, face_indices=None, verbose=True):
    """
    Copies the per-component (per-face) material assignment of a mesh into the material clipboard.

    Object and world space face centers are both stored, so a paste operation can match components by
    index or by position without reading the source mesh again.

    Args:
        source (str, optional): Mesh transform, shape or component string. When None, the current selection
            is used. Selected faces limit the copy to those faces only.
        face_indices (list, optional): Explicit face indices to copy. When None, indices are resolved from
            the selection, defaulting to every face of the mesh.
        verbose (bool, optional): When True, prints in-view feedback. Defaults to True.

    Returns:
        dict or None: The stored clipboard data, otherwise None when nothing could be copied.
    """
    shape, face_indices = _resolve_copy_source(source=source, face_indices=face_indices)
    if not shape:
        cmds.warning("Unable to copy materials. Select a polygon mesh (or its faces) before copying.")
        return None

    shading_engines, face_slots = get_face_shading_engines(shape)
    if not face_slots:
        cmds.warning(f'Unable to copy materials. No faces were found in "{shape}".')
        return None
    if face_indices is None:
        face_indices = range(len(face_slots))

    object_centers = get_face_centers(shape, space=ComponentSpace.object_space)
    world_centers = get_face_centers(shape, space=ComponentSpace.world)
    materials = [get_material_from_shading_engine(shading_engine) for shading_engine in shading_engines]

    copied_faces = []
    copied_slots = []
    copied_object_centers = []
    copied_world_centers = []
    for face_index in face_indices:
        if face_index < 0 or face_index >= len(face_slots):
            logger.debug(f'Ignoring out of range face index "{face_index}".')
            continue
        slot = face_slots[face_index]
        if slot < 0:
            continue  # Face has no material assigned to it
        copied_faces.append(face_index)
        copied_slots.append(slot)
        copied_object_centers.append(object_centers[face_index])
        copied_world_centers.append(world_centers[face_index])

    if not copied_faces:
        cmds.warning("Unable to copy materials. No material assignment was found in the provided components.")
        return None

    clipboard_data = {
        "source": shape,
        "face_count": len(face_slots),
        "shading_engines": shading_engines,
        "materials": materials,
        "faces": copied_faces,
        "shader_slots": copied_slots,
        "face_centers_object": copied_object_centers,
        "face_centers_world": copied_world_centers,
    }
    _component_material_clipboard.clear()
    _component_material_clipboard.update(clipboard_data)

    if verbose:
        feedback = core_fback.FeedbackMessage(
            prefix="Materials",
            intro="copied from",
            quantity=len(copied_faces),
            singular="face",
            plural="faces",
            conclusion="to the clipboard.",
        )
        feedback.print_inview_message(system_write=False)
        print(f"Copied materials: {get_component_material_clipboard_summary(clipboard_data)}")
    return clipboard_data


def _resolve_paste_targets(targets, clipboard_data):
    """
    Determines which mesh shapes should receive the clipboard materials.

    Args:
        targets (list or None): Meshes, shapes or component strings. When None, the selection is used.
        clipboard_data (dict): Clipboard data as created by "copy_component_materials".

    Returns:
        tuple: (target_shapes, selected_faces) where "target_shapes" is an ordered list of mesh shapes and
               "selected_faces" maps a mesh shape to the face indices found in the provided targets.
    """
    if targets is None:
        targets = cmds.ls(selection=True, long=True) or []
    if isinstance(targets, str):
        targets = [targets]

    selected_faces = get_selected_face_indices(targets)
    target_shapes = []
    for target in targets:
        shape = get_mesh_shape(target)
        if shape and shape not in target_shapes:
            target_shapes.append(shape)

    # Keep the source out of the way when the user left it selected alongside the targets
    source = clipboard_data.get("source")
    if len(target_shapes) > 1 and source in target_shapes:
        logger.debug(f'Ignoring the copy source "{source}" while pasting.')
        target_shapes.remove(source)
    return target_shapes, selected_faces


def paste_component_materials(
    targets=None,
    match_by=MaterialTransferMode.component_index,
    space=ComponentSpace.object_space,
    tolerance=DEFAULT_POSITION_TOLERANCE,
    fallback_closest=True,
    clipboard_data=None,
    verbose=True,
):
    """
    Pastes the material assignment stored in the material clipboard onto the target meshes.

    Args:
        targets (list, optional): Meshes, shapes or component strings. When None, the current selection is
            used. Selected faces limit the paste to those faces only.
        match_by (str, optional): A MaterialTransferMode value. Use "component_index" when the target shares
            the source topology (matching component ids) and "component_position" when only the shape
            matches. Defaults to "component_index".
        space (str, optional): A ComponentSpace value used when matching by position. Defaults to object
            (local) space, which also works for duplicates that were moved.
        tolerance (float, optional): Distance within which a component counts as an exact position match.
        fallback_closest (bool, optional): When True, components sitting outside the tolerance still receive
            the material of the closest source component, so every target component gets a material.
            Defaults to True.
        clipboard_data (dict, optional): Data to paste. When None, the module clipboard is used.
        verbose (bool, optional): When True, prints in-view feedback. Defaults to True.

    Returns:
        dict: Report with the keys "assigned", "approximate", "unmatched", "targets" and "skipped".
    """
    report = {"assigned": 0, "approximate": 0, "unmatched": 0, "targets": [], "skipped": []}
    data = clipboard_data if clipboard_data is not None else _component_material_clipboard
    if not data or not data.get("faces"):
        cmds.warning("Unable to paste materials. Copy the material assignment of a mesh first.")
        return report

    target_shapes, selected_faces = _resolve_paste_targets(targets=targets, clipboard_data=data)
    if not target_shapes:
        cmds.warning("Unable to paste materials. Select the target objects or components first.")
        return report

    source_positions = None
    position_hash = None
    cell_size = None
    cell_bounds = None
    if match_by == MaterialTransferMode.component_position:
        tolerance = float(tolerance) if tolerance else DEFAULT_POSITION_TOLERANCE
        if tolerance <= 0:
            tolerance = DEFAULT_POSITION_TOLERANCE
        position_key = "face_centers_world" if space == ComponentSpace.world else "face_centers_object"
        source_positions = data.get(position_key) or []
        if not source_positions:
            cmds.warning("Unable to paste materials. The clipboard is missing component positions.")
            return report
        cell_size = _estimate_cell_size(source_positions, minimum_cell_size=tolerance)
        position_hash = _build_position_hash(source_positions, cell_size=cell_size)
        cell_bounds = _get_hash_cell_bounds(position_hash)

    slot_per_source_face = dict(zip(data.get("faces") or [], data.get("shader_slots") or []))

    with core_undo.UndoChunk(chunk_name="Paste Component Materials"):
        for shape in target_shapes:
            face_count = cmds.polyEvaluate(shape, face=True)
            if not isinstance(face_count, int) or face_count <= 0:
                logger.debug(f'Skipping "{shape}". Unable to determine its face count.')
                report["skipped"].append(shape)
                continue

            target_faces = selected_faces.get(shape) or list(range(face_count))
            target_centers = None
            if match_by == MaterialTransferMode.component_position:
                target_centers = get_face_centers(shape, space=space)

            assignments = {}
            for face_index in target_faces:
                if face_index < 0 or face_index >= face_count:
                    continue
                if target_centers is not None:
                    match_index, is_approximate = _match_source_position_index(
                        position=target_centers[face_index],
                        positions=source_positions,
                        position_hash=position_hash,
                        cell_size=cell_size,
                        tolerance=tolerance,
                        fallback_closest=fallback_closest,
                        cell_bounds=cell_bounds,
                    )
                    slot = None if match_index is None else data["shader_slots"][match_index]
                    if is_approximate:
                        report["approximate"] += 1
                else:
                    slot = slot_per_source_face.get(face_index)
                if slot is None:
                    report["unmatched"] += 1
                    continue
                assignments.setdefault(slot, []).append(face_index)

            assigned_faces = 0
            for slot, slot_faces in assignments.items():
                shading_engine = _resolve_clipboard_shading_engine(clipboard_data=data, slot=slot)
                if not shading_engine:
                    report["unmatched"] += len(slot_faces)
                    continue
                assigned_faces += assign_faces_to_shading_engine(
                    shape=shape, face_indices=slot_faces, shading_engine=shading_engine
                )
            report["assigned"] += assigned_faces
            if assigned_faces:
                report["targets"].append(shape)
            else:
                report["skipped"].append(shape)

    if report["approximate"]:
        logger.info(
            f'{report["approximate"]} faces were outside the tolerance and received the material of the '
            f"closest source component."
        )
    if report["unmatched"]:
        logger.warning(f'{report["unmatched"]} faces could not be matched to a source material.')
    if verbose:
        feedback = core_fback.FeedbackMessage(
            prefix="Materials",
            intro="pasted onto",
            quantity=report["assigned"],
            singular="face",
            plural="faces",
            conclusion="from the clipboard.",
            zero_overwrite_message="No faces were updated. Check the mode, space and tolerance options.",
        )
        feedback.print_inview_message(system_write=False)
    return report


# ------------------------------------------------- Textures -------------------------------------------------
def get_file_texture_paths(file_nodes=None, resolve_udims=True):
    """
    Retrieves the file paths for specified Maya 'file' texture nodes.

    The path values returned are always lists of strings, where a single file
    is returned as a list with one element.

    Args:
        file_nodes (list, optional): A list of 'file' node names to query.
                                     If None, all 'file' nodes in the scene are queried.
                                     Defaults to None.
        resolve_udims (bool, optional): If True, and the node uses UDIM or sequence mode,
                                        the function attempts to search the disk for all
                                        corresponding files and return them as a list.
                                        If False, it returns the raw pattern string (e.g.,
                                        'path/to/texture_<UDIM>.ext') as a single-element list.
                                        Defaults to False.

    Returns:
        dict: A dictionary where the key is the file node name and the value is
              a list of path strings. The list will be empty if no path is set
              or if the query fails.
    """

    texture_paths = {}

    try:
        # We need this internal Maya module to reliably get the pattern for UDIM/Sequences
        import maya.app.general.fileTexturePathResolver as texture_path_resolver
    except ImportError:
        logger.warning(
            "Could not import maya.app.general.fileTexturePathResolver. " "UDIM/Sequence logic may be inaccurate."
        )
        texture_path_resolver = None

    # Determine which nodes to process
    if file_nodes is None:
        nodes_to_process = cmds.ls(type="file", long=True) or []
    else:
        nodes_to_process = [node for node in file_nodes if cmds.objExists(node) and cmds.objectType(node) == "file"]
        if not nodes_to_process:
            logger.info("Provided list of nodes contained no existing 'file' nodes.")
            return {}

    # Process the nodes
    for node_name in nodes_to_process:
        attribute_path = f"{node_name}.fileTextureName"
        path_list = []  # Initialize as empty list for the final result

        if not cmds.attributeQuery("fileTextureName", node=node_name, exists=True):
            logger.debug(f"Skipping node {node_name}: Missing fileTextureName attribute.")
            texture_paths[node_name] = path_list
            continue

        try:
            base_path = cmds.getAttr(attribute_path) or ""

            if not base_path:
                texture_paths[node_name] = path_list
                continue

            # Normalize path separators early for consistency
            normalized_base_path = os.path.normpath(base_path).replace("\\", "/")

            # Check if this node is configured for UDIM/Sequence
            uv_tiling_mode = cmds.getAttr(f"{node_name}.uvTilingMode")
            use_frame_extension = cmds.getAttr(f"{node_name}.useFrameExtension")

            is_pattern_node = uv_tiling_mode != 0 or use_frame_extension

            # --- 1. Get the Pattern String ---
            if texture_path_resolver and is_pattern_node:
                # Get the pattern string, e.g., 'C:/tex/color_<UDIM>.ext'
                pattern_string = texture_path_resolver.getFilePatternString(
                    normalized_base_path, use_frame_extension, uv_tiling_mode
                )
            else:
                pattern_string = normalized_base_path

            # --- 2. Determine Output based on `resolve_udims` ---
            if is_pattern_node and resolve_udims and pattern_string:
                # RESOLVE MODE: Find all matching files on disk

                # Convert the Maya pattern string into a glob pattern
                glob_pattern = pattern_string.replace("<UDIM>", "[0-9][0-9][0-9][0-9]")
                glob_pattern = glob_pattern.replace("<f>", "*")
                glob_pattern = glob_pattern.replace("<F>", "*")

                # Extract the directory to search within
                search_dir = os.path.dirname(glob_pattern)
                if not search_dir:
                    search_dir = os.path.dirname(os.path.abspath(pattern_string))

                # Since glob can be unreliable with UDIM-style patterns,
                # we'll use a combination of glob for listing and regex for filtering.
                # However, for simplicity and production reliability (assuming only UDIM/Frame in pattern),
                # we will use glob after converting the pattern.

                # Check for absolute path to avoid unexpected glob behavior
                if not os.path.isabs(glob_pattern):
                    logger.warning(f"Skipping disk search for relative path: {pattern_string}")
                    path_list = [pattern_string]
                else:
                    resolved_paths = glob.glob(glob_pattern)
                    # Normalize paths found by glob for consistency
                    path_list = [os.path.normpath(p).replace("\\", "/") for p in resolved_paths]

                if not path_list:
                    logger.debug(f"Resolved mode: No files found on disk matching {pattern_string}")
                    # If nothing is found on disk, fall back to the pattern path itself
                    path_list = [pattern_string]

            else:
                # PATTERN MODE (resolve_udims=False) or Single File: Return the pattern string
                # Even single files are returned as a list of one element for consistent output type
                path_list = [pattern_string]

            texture_paths[node_name] = path_list

        except Exception as error:
            logger.error(f"Failed to query path for {node_name}: {error}")
            texture_paths[node_name] = []  # Return empty list on failure

    return texture_paths


def migrate_textures_to_directory(texture_data, target_directory, remove_missing_nodes=False):
    """
    Copies texture files found outside the target directory to that directory,
    and updates the corresponding Maya file nodes to point to the new location.

    Args:
        texture_data (dict): Output dictionary from get_file_texture_paths.
                             Key is node name (str), value is a list of paths (list[str]).
        target_directory (str): The absolute path to the directory where textures
                                should be copied.
        remove_missing_nodes (bool, optional): If True, and all resolved paths for
                                               a file node are missing from the disk,
                                               the file node itself is deleted from the scene.
                                               Defaults to False.

    Returns:
        dict: A report dictionary summarizing the operation results, including:
              'copied_count': (int) Number of files copied.
              'updated_count': (int) Number of Maya nodes updated.
              'removed_nodes': (list) List of file nodes that were removed.
              'failed_copies': (list) List of paths that *truly* failed to copy.
    """

    # 1. Normalize and validate the target directory
    normalized_target_dir = os.path.normpath(target_directory).replace("\\", "/")
    if not os.path.isdir(normalized_target_dir):
        try:
            os.makedirs(normalized_target_dir)
            logger.info(f"Created target directory: {normalized_target_dir}")
        except OSError as e:
            logger.error(f"Failed to create target directory {normalized_target_dir}. Aborting. Error: {e}")
            return {"copied_count": 0, "updated_count": 0, "removed_nodes": [], "failed_copies": []}

    if not normalized_target_dir.endswith("/"):
        normalized_target_dir += "/"

    report = {"copied_count": 0, "updated_count": 0, "removed_nodes": [], "failed_copies": []}

    # Process each file node
    for node_name, path_list in texture_data.items():
        if not cmds.objExists(node_name):
            continue

        # --- MISSING NODE CHECK (Executed regardless of migration status) ---
        if remove_missing_nodes and path_list:
            # Check if ANY of the paths exist. If all are missing, we consider the node orphaned.
            # We assume path_list contains resolved paths (or the single file path).
            is_any_file_found = any(os.path.exists(path) for path in path_list)

            if not is_any_file_found:
                try:
                    cmds.delete(node_name)
                    report["removed_nodes"].append(node_name)
                    logger.info(f"Removed missing file node: {node_name}")
                    continue  # Skip to the next node, as this one is deleted
                except Exception as e:
                    logger.error(f"Failed to delete node {node_name}. Error: {e}")
                    # If deletion fails, we proceed to the migration logic below, hoping for a successful re-path.

        # If path_list is empty, we also skip as there's nothing to copy or re-path.
        if not path_list:
            continue

        first_source_path = path_list[0]

        # Check if the texture is already in the target directory
        is_already_in_target = first_source_path.startswith(normalized_target_dir)

        if is_already_in_target:
            logger.debug(f"Skipping {node_name}: Already in target directory.")
            continue

        new_node_path = None

        # Process individual files (tiles or single file)
        for source_path in path_list:
            if not os.path.exists(source_path):
                logger.warning(f"Source file does not exist, skipping copy: {source_path}")
                continue  # Skip copy if file is missing (but don't fail the whole node yet)

            file_name = os.path.basename(source_path)
            destination_path = os.path.join(normalized_target_dir, file_name)

            # --- Robust Copy with Error Suppression ---
            try:
                if destination_path and os.path.exists(destination_path):
                    core_io.set_file_permission_modifiable(destination_path)

                # 1. Use shutil.copyfile for data transfer only
                shutil.copyfile(source_path, destination_path)

                # 2. Ensure writability (metadata fix)
                current_permissions = os.stat(destination_path).st_mode
                os.chmod(destination_path, current_permissions | stat.S_IWRITE)

                # Successful Copy Logic
                report["copied_count"] += 1
                logger.debug(f"Copied and ensured writability: {source_path} to {destination_path}")

            except PermissionError as e:
                # Catch Errno 13
                if os.path.exists(destination_path) and os.path.getsize(destination_path) == os.path.getsize(
                    source_path
                ):
                    # Data transfer confirmed. Treat as success.
                    report["copied_count"] += 1
                    logger.info(f"Copied (Attribute Error Suppressed): {source_path} to {destination_path}")
                else:
                    # True copy failure (file size mismatch/non-existent destination file).
                    logger.error(f"True copy failure: {source_path}. Error: {e}")
                    report["failed_copies"].append(source_path)
                    new_node_path = None
                    break  # Abort migration for this node

            except Exception as e:
                # Catch any other true filesystem error
                logger.error(f"Failed to copy {source_path} to {normalized_target_dir}. Error: {e}")
                report["failed_copies"].append(source_path)
                new_node_path = None
                break  # Abort migration for this node

            # Determine the path to write back to the Maya node (run only once per node)
            if new_node_path is None:
                original_file_name_part = os.path.basename(first_source_path)

                if (
                    "<UDIM>" in original_file_name_part
                    or "<f>" in original_file_name_part
                    or "<F>" in original_file_name_part
                ):
                    new_node_path = os.path.join(normalized_target_dir, original_file_name_part).replace("\\", "/")
                else:
                    new_node_path = os.path.normpath(destination_path).replace("\\", "/")

        # --- Update Maya Node ---
        if new_node_path and cmds.objExists(node_name):
            attribute_path = f"{node_name}.fileTextureName"

            try:
                cmds.setAttr(attribute_path, new_node_path, type="string")
                report["updated_count"] += 1
                logger.info(f"Updated node {node_name} to new path: {new_node_path}")
            except Exception as e:
                logger.error(f"Failed to update attribute {attribute_path}. Error: {e}")

    return report


if __name__ == "__main__":
    # assign_material(cmds.ls(selection=True), rgb_color=(1, 0, 0))
    # assign_material(cmds.ls(selection=True), rgb_color=(1, 0, 0), material_name="M_mocked")
    txt_data = get_file_texture_paths()

    import pprint
    import gt.utils.system as utils_sys

    test_target_path = os.path.join(utils_sys.get_desktop_path(), "test_target")

    pprint.pprint(
        migrate_textures_to_directory(
            texture_data=txt_data, target_directory=test_target_path, remove_missing_nodes=True
        )
    )
    print(get_all_materials(material_types=CommonMaterials.lambert))