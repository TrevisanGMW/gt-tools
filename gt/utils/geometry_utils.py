"""
Geometry Utilities
github.com/TrevisanGMW/gt-tools
"""
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def convert_bif_to_mesh():
    """
    Converts Bifrost geometry to Maya geometry
    """
    errors = ''
    function_name = 'Convert Bif to Mesh'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)
        valid_selection = True

        selection = cmds.ls(selection=True)
        bif_objects = []
        bif_graph_objects = []

        if len(selection) < 1:
            valid_selection = False
            cmds.warning('You need to select at least one bif object.')

        if valid_selection:
            for obj in selection:
                shapes = cmds.listRelatives(obj, shapes=True, fullPath=True) or []
                for shape in shapes:
                    if cmds.objectType(shape) == 'bifShape':
                        bif_objects.append(shape)
                    if cmds.objectType(shape) == 'bifrostGraphShape':
                        bif_graph_objects.append(shape)

            for bif in bif_objects:
                parent = cmds.listRelatives(bif, parent=True) or []
                for par in parent:
                    source_mesh = cmds.listConnections(par + '.inputSurface', source=True, plugs=True) or []
                    for sm in source_mesh:
                        conversion_node = cmds.createNode("bifrostGeoToMaya")
                        cmds.connectAttr(sm, conversion_node + '.bifrostGeo')
                        mesh_node = cmds.createNode("mesh")
                        mesh_transform = cmds.listRelatives(mesh_node, parent=True) or []
                        cmds.connectAttr(conversion_node + '.mayaMesh[0]', mesh_node + '.inMesh')
                        cmds.rename(mesh_transform[0], 'bifToGeo1')
                        try:
                            cmds.hyperShade(assign='lambert1')
                        except Exception as e:
                            logger.debug(str(e))

            for bif in bif_graph_objects:
                bifrost_attributes = cmds.listAttr(bif, fp=True, inUse=True, read=True) or []
                for output in bifrost_attributes:
                    conversion_node = cmds.createNode("bifrostGeoToMaya")
                    cmds.connectAttr(bif + '.' + output, conversion_node + '.bifrostGeo')
                    mesh_node = cmds.createNode("mesh")
                    mesh_transform = cmds.listRelatives(mesh_node, parent=True) or []
                    cmds.connectAttr(conversion_node + '.mayaMesh[0]', mesh_node + '.inMesh')
                    bif_mesh = cmds.rename(mesh_transform[0], 'bifToGeo1')
                    try:
                        cmds.hyperShade(assign='lambert1')
                    except Exception as e:
                        logger.debug(str(e))

                    vtx = cmds.ls(bif_mesh + '.vtx[*]', fl=True) or []
                    if len(vtx) == 0:
                        try:
                            cmds.delete(bif_mesh)
                            # cmds.delete(conversion_node)
                            # cmds.delete(mesh_node)
                        except Exception as e:
                            logger.debug(str(e))
    except Exception as e:
        errors += str(e) + '\n'
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        cmds.warning('An error occurred when converting bif to mesh. Open the script editor for more information.')
        print('######## Errors: ########')
        print(errors)


def get_vertices(mesh):
    """
    Retrieves the vertices of a given mesh.
    This function returns a list of vertex names that belong to the specified mesh.

    Parameters:
        mesh (str): The name of the mesh for which vertices will be retrieved.

    Returns:
        list[str]: A list of vertex names as strings, representing the vertices
                   of the specified mesh.

    Raises:
        ValueError: If the provided 'mesh' name does not correspond to an existing mesh.

    Examples:
        mesh_name = 'my_mesh'
        vertices = get_vertices(mesh_name)
        print(vertices)
        ['my_mesh.vtx[0]', 'my_mesh.vtx[1]', 'my_mesh.vtx[2]', ...]
    """

    if not cmds.objExists(mesh):
        raise ValueError(f'The mesh "{mesh}" does not exist.')
    vertices = cmds.ls(f"{mesh}.vtx[*]", flatten=True)
    return vertices
