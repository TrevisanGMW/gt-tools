"""
Parametric Mesh Creation for Scene Setup
"""
from gt.utils.data.py_meshes.mesh_data import MeshData
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_studio_background(name="studio_background", initial_scale=1):
    """
    Creates a studio background mesh
    Args:
        name (str, optional): The name for the created mesh.
        initial_scale (int, float, optional): Sets the initial scale of the mesh object
    """
    selection = cmds.ls(selection=True)
    plane_transform, poly_plane_node = cmds.polyPlane(name=name, w=1, h=1, sx=10, sy=10, ax=(0, 1, 0), cuv=2, ch=1)

    # Set attributes for the poly plane
    cmds.setAttr(f"{poly_plane_node}.height", 40)
    cmds.setAttr(f"{poly_plane_node}.width", 40)
    cmds.setAttr(f"{poly_plane_node}.subdivisionsHeight", 50)
    cmds.setAttr(f"{poly_plane_node}.subdivisionsWidth", 50)

    cmds.rename(poly_plane_node, f'{name}_polyPlane')

    # Create a bend deformer and set its attributes
    bend_node_one, bend_handle_one = cmds.nonLinear(plane_transform, name=f'{name}_bendY', typ="bend",
                                                    lowBound=0, highBound=1, curvature=90)

    cmds.rotate(0, -90, 0, bend_handle_one, r=True, os=True, fo=True)
    cmds.rotate(0, 0, 90, bend_handle_one, r=True, os=True, fo=True)

    bend_node_two, bend_handle_two = cmds.nonLinear(plane_transform, name=f'{name}_bendZ', typ="bend",
                                                    lowBound=-1, highBound=1, curvature=110)

    bend_handles = [bend_handle_one, bend_handle_two]

    cmds.rotate(0, -90, 0, bend_handle_two, r=True, os=True, fo=True)
    cmds.rotate(-90, 0, 0, bend_handle_two, r=True, os=True, fo=True)
    cmds.move(0, 0, 7, bend_handle_two, r=True)

    cmds.parent([bend_handle_one, bend_handle_two], plane_transform)

    cmds.move(0, 0, -10, plane_transform, r=True)
    cmds.xform(plane_transform, piv=(0, 0, 11), ws=True)
    cmds.move(0, 0, 0, plane_transform, a=True, rpr=True)  # rpr flag moves it according to the pivot

    for handle in bend_handles:
        cmds.setAttr(f'{handle}.v', 0)

    cmds.setAttr(f'{plane_transform}.sx', initial_scale)
    cmds.setAttr(f'{plane_transform}.sy', initial_scale)
    cmds.setAttr(f'{plane_transform}.sz', initial_scale)

    cmds.select(clear=True)
    if selection:
        try:
            cmds.select(selection)
        except Exception as e:
            logger.debug(f'Unable to recover selection. Issue: {str(e)}')

    return MeshData(name=plane_transform, setup=bend_handles)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    cmds.file(new=True, force=True)
    create_studio_background()
