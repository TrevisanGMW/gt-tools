"""
Material Module

Import Line:
    import gt.core.material as core_mat
"""

import gt.core.naming as core_naming
import gt.core.io as core_io
import maya.cmds as cmds
import logging
import shutil
import glob
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