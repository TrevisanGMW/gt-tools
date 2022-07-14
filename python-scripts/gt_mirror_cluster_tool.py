"""
 GT Mirror Cluster Tool
 github.com/TrevisanGMW/gt-tools -  2020-06-16
 
 1.1 - 2020-11-15
 Tweaked the color and text for the title and help menu
 
 1.2 - 2021-05-12
 Made script compatible with Python 3 (Maya 2022+)

 1.2.1 - 2022-07-04
 Added logger
 Added patch version
 PEP8 General cleanup
 
 To Do:
 Add option to mirror other deformers
 Mirror multiple clusters and meshes at the same time

"""
import maya.cmds as cmds
import logging
from maya import OpenMayaUI as OpenMayaUI

try:
    from shiboken2 import wrapInstance
except ImportError:
    from shiboken import wrapInstance

try:
    from PySide2.QtGui import QIcon
    from PySide2.QtWidgets import QWidget
except ImportError:
    from PySide.QtGui import QIcon, QWidget

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("gt_mirror_cluster_tool")
logger.setLevel(logging.INFO)

# Script Name
script_name = "GT Mirror Cluster Tool"

# Version
script_version = "1.2.1"

global_settings = {'loaded_mesh': '',
                   'loaded_cluster_handle': '',
                   'default_search_string': 'left_',
                   'default_replace_string': 'right_',
                   }


def build_gui_mirror_cluster_tool():
    window_name = "build_gui_mirror_cluster_tool"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + '  (v' + script_version + ')', mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    cmds.columnLayout("main_column", p=window_name)

    # Title Text
    title_bgc_color = (.4, .4, .4)
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p="main_column")  # Window Size Adjustment
    cmds.rowColumnLayout(nc=3, cw=[(1, 10), (2, 240), (3, 50)], cs=[(1, 10), (2, 0), (3, 0)],
                         p="main_column")  # Title Column
    cmds.text(" ", bgc=title_bgc_color)  # Tiny Empty Green Space
    cmds.text(script_name, bgc=title_bgc_color, fn="boldLabelFont", align="left")
    cmds.button(l="Help", bgc=title_bgc_color, c=lambda x: build_gui_help_mirror_cluster_tool())
    cmds.separator(h=10, style='none', p="main_column")  # Empty Space

    # Body ====================
    cmds.rowColumnLayout("body_column", nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.separator(h=8)
    cmds.separator(h=5, style='none')  # Empty Space

    # Object Loader ====================
    cmds.separator(h=5, style='none')
    cmds.rowColumnLayout(nc=2, cw=[(1, 150), (2, 150)], cs=[(1, 10), (2, 0)], p="main_column")

    # Mesh Loader
    cmds.button(l="Select Mesh", c=lambda x: update_stored_objects("mesh"), w=150)
    mesh_status = cmds.button(l="Not selected yet", bgc=(.2, .2, .2), w=150,
                              c="cmds.headsUpMessage( 'Select the mesh you want to mirror and click on \"Select Mesh\""
                                "', verticalOffset=150 , time=5.0)")
    # Cluster Handle Loader
    cmds.button(l="Select Cluster", c=lambda x: update_stored_objects("clusterHandle"), w=150)
    cluster_handle_status = cmds.button(l="Not selected yet", bgc=(.2, .2, .2), w=150,
                                        c="cmds.headsUpMessage( 'Select the cluster node you want to mirror and click"
                                          " on \"Select Cluster\"', verticalOffset=150 , time=5.0)")
    cmds.separator(h=10, style='none')  # Spacing Before Next Container

    # Mirror Axis ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.radioButtonGrp("mirror_axis_btn_grp", nrb=3, sl=1, l="Mirror Axis", labelArray3=["X", "Y", "Z"],
                        columnAlign4=["center", "left", "left", "left"], cw4=[120, 60, 60, 60])
    cmds.separator(h=10, style='none')  # Spacing Before Next Container

    # Search and Replace Text Boxes ====================
    cmds.rowColumnLayout(nc=2, cw=[(1, 145), (2, 145)], cs=[(1, 10), (2, 10)], p="main_column")
    cmds.text(l="Search for:", align="left")
    cmds.text(l='Replace with:', align="left")
    cmds.separator(h=5, style='none')
    cmds.separator(h=5, style='none')
    cmds.textField("search_text_field", text=global_settings.get("default_search_string"))
    cmds.textField("replace_text_field", text=global_settings.get("default_replace_string"))

    # Bottom Separator ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.separator(h=8, style='none')  # Empty Space
    cmds.separator(h=8)

    # Run Button ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p="main_column")
    cmds.separator(h=10, style='none')
    cmds.button(l='Mirror', h=30, c=lambda args: mirror_cluster(), bgc=[.6, .6, .6])
    cmds.separator(h=8, style='none')

    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Check Selection and Update Buttons
    def update_stored_objects(expected_type):
        # Check If Selection is Valid
        received_valid_object = False

        selection = cmds.ls(selection=True)
        received_object = ''

        if len(selection) == 0:
            cmds.warning("No objects selected. Please select a Mesh or a Cluster and try again")
        elif len(selection) > 1:
            cmds.warning("You selected more than one object! Please select only one.")
        elif cmds.objectType(cmds.listRelatives(selection[0], children=True)[0]) == expected_type:
            received_object = selection[0]
            received_valid_object = True
        else:
            cmds.warning("Something went wrong, make sure you selected the correct object type")

        # If mesh
        if expected_type is "mesh" and received_valid_object is True:
            global_settings["loaded_mesh"] = received_object
            cmds.button(mesh_status, l=received_object, e=True, bgc=(.6, .8, .6),
                        c=lambda x: loader_existence_check(global_settings.get("loaded_mesh")))
        elif expected_type is "mesh":
            cmds.button(mesh_status, l="Failed to Load", e=True, bgc=(1, .4, .4), w=130,
                        c="cmds.headsUpMessage( 'Make sure you select only one mesh and try again', "
                          "verticalOffset=150 , time=5.0)")
        # If clusterHandle
        if expected_type is "clusterHandle" and received_valid_object is True:
            global_settings["loaded_cluster_handle"] = received_object
            cmds.button(cluster_handle_status, l=received_object, e=True, bgc=(.6, .8, .6),
                        c=lambda x: loader_existence_check(global_settings.get("loaded_cluster_handle")))
        elif expected_type is "clusterHandle":
            cmds.button(cluster_handle_status, l="Failed to Load", e=True, bgc=(1, .4, .4), w=130,
                        c="cmds.headsUpMessage( 'Make sure you select a cluster and try again', "
                          "verticalOffset=150 , time=5.0)")

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/cluster.png')
    widget.setWindowIcon(icon)

    # Main GUI End ===================================================================


# Creates Help GUI
def build_gui_help_mirror_cluster_tool():
    window_name = "build_gui_help_mirror_cluster_tool"
    if cmds.window(window_name, exists=True):
        cmds.deleteUI(window_name, window=True)

    cmds.window(window_name, title=script_name + " Help", mnb=False, mxb=False, s=True)
    cmds.window(window_name, e=True, s=True, wh=[1, 1])

    main_column = cmds.columnLayout(p=window_name)

    # Title Text
    cmds.separator(h=12, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=1, cw=[(1, 310)], cs=[(1, 10)], p=main_column)  # Window Size Adjustment
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)  # Title Column
    cmds.text(script_name + " Help", bgc=[.4, .4, .4], fn="boldLabelFont", align="center")
    cmds.separator(h=10, style='none', p=main_column)  # Empty Space

    # Body ====================
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
    cmds.text(l='Script mirroring clusters on mesh objects.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Step 1:', align="left", fn="boldLabelFont")
    cmds.text(l='Load your mesh by selecting it in the viewport or in the', align="left")
    cmds.text(l='outliner, then click on \"Select Mesh\".', align="left")
    cmds.text(l='Requirements: Must be one single mesh transform.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Step 2:', align="left", fn="boldLabelFont")
    cmds.text(l='Load your clusterHandle by selecting it in the viewport ', align="left")
    cmds.text(l='or in the outliner, then click on \"Select Cluster\".', align="left")
    cmds.text(l='Requirements: Must be one single clusterHandle.', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Step 3:', align="left", fn="boldLabelFont")
    cmds.text(l='Select your mirror axis ', align="left")
    cmds.text(l='X, Y or Z. It will always mirror on the negative direction', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='Step 4:', align="left", fn="boldLabelFont")
    cmds.text(l='To save time you can automatically rename the mirrored', align="left")
    cmds.text(l='clusters using the search and replace text fields.', align="left")
    cmds.text(l='For example search for "left_" and replace with "right_"', align="left")
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p=main_column)
    cmds.text('Guilherme Trevisan  ')
    cmds.text(l='<a href="mailto:trevisangmw@gmail.com">TrevisanGMW@gmail.com</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.rowColumnLayout(nc=2, cw=[(1, 140), (2, 140)], cs=[(1, 10), (2, 0)], p=main_column)
    cmds.separator(h=15, style='none')  # Empty Space
    cmds.text(l='<a href="https://github.com/TrevisanGMW">Github</a>', hl=True, highlightColor=[1, 1, 1])
    cmds.separator(h=7, style='none')  # Empty Space

    # Close Button 
    cmds.rowColumnLayout(nc=1, cw=[(1, 300)], cs=[(1, 10)], p=main_column)
    cmds.separator(h=10, style='none')
    cmds.button(l='OK', h=30, c=lambda args: close_help_gui())
    cmds.separator(h=8, style='none')

    # Show and Lock Window
    cmds.showWindow(window_name)
    cmds.window(window_name, e=True, s=False)

    # Set Window Icon
    qw = OpenMayaUI.MQtUtil.findWindow(window_name)
    widget = wrapInstance(int(qw), QWidget)
    icon = QIcon(':/question.png')
    widget.setWindowIcon(icon)

    def close_help_gui():
        if cmds.window(window_name, exists=True):
            cmds.deleteUI(window_name, window=True)


# Start of Main Function ===============================================================
def mirror_cluster():
    is_current_setup_valid = True
    mesh_transform = global_settings.get("loaded_mesh")
    cluster_handle = global_settings.get("loaded_cluster_handle")
    mirror_axis = cmds.radioButtonGrp("mirror_axis_btn_grp", q=1, sl=1)

    if cmds.objExists(mesh_transform) is True:
        if cmds.objectType(cmds.listRelatives(mesh_transform, children=True)[0]) != "mesh":
            is_current_setup_valid = False
    else:
        is_current_setup_valid = False

    if cmds.objExists(cluster_handle) is True:
        if cmds.objectType(cmds.listRelatives(cluster_handle, children=True)[0]) != "clusterHandle":
            is_current_setup_valid = False
    else:
        is_current_setup_valid = False

    if is_current_setup_valid:
        mesh_shape = cmds.listRelatives(mesh_transform, s=1, c=1)
        vertices_selected_mesh = get_cluster_vertices_on_mesh(mesh_transform, cluster_handle)
        mirrored_vertices = []

        for vertex in vertices_selected_mesh:
            vertex_position = cmds.pointPosition(vertex[0], local=1)

            # Utility node used to collect information about the other side of the mesh
            closest_point_node = cmds.createNode('closestPointOnMesh')

            if mirror_axis == 1:

                cmds.setAttr((closest_point_node + ".inPosition"), -vertex_position[0], vertex_position[1],
                             vertex_position[2])
            elif mirror_axis == 2:
                cmds.setAttr((closest_point_node + ".inPosition"), vertex_position[0], -vertex_position[1],
                             vertex_position[2])
            else:
                cmds.setAttr((closest_point_node + ".inPosition"), vertex_position[0], vertex_position[1],
                             -vertex_position[2])

            try:
                cmds.connectAttr((mesh_shape[0] + ".outMesh"), (closest_point_node + ".inMesh"), force=1)
            except Exception as e:
                logger.debug(str(e))

            mirrored_vertex = (mesh_transform + ".vtx[" + str(
                cmds.getAttr((closest_point_node + ".closestVertexIndex"))) + "]")  # Find mirrored vertex
            vertex[0] = mirrored_vertex  # Replace previous pair vertex with newly found one
            mirrored_vertices.append(mirrored_vertex)
            cmds.delete(closest_point_node)  # Delete utility node

        cluster_deform_node = cmds.listConnections((cluster_handle + ".worldMatrix[0]"), type="cluster",
                                                   destination=1)
        is_relative = cmds.getAttr((cluster_deform_node[0] + ".relative"))

        new_cluster_name = cluster_handle.replace(cmds.textField("search_text_field", q=True, text=True),
                                                  cmds.textField("replace_text_field", q=True, text=True))
        new_cluster = cmds.cluster(mirrored_vertices, rel=is_relative)

        # Transfer weight back to new cluster
        for num in range(len(vertices_selected_mesh)):
            cmds.percent(new_cluster[0], vertices_selected_mesh[num][0], v=vertices_selected_mesh[num][1])

        cmds.rename(new_cluster_name)
    else:
        cmds.warning("Something went wrong. Please try loading the objects again.")
    # End of Main Function ===============================================================


def get_cluster_vertices_on_mesh(mesh_transform, cluster_handle):
    """
    Returns vertices influenced by a cluster

    Args:
        mesh_transform: a selected mesh, for example "pSphere1"
        cluster_handle: a cluster handle that has influence over the mesh
    Returns:
        A list of paired vertices and weights [vertex, weight]
    """
    cluster_deform_node = cmds.listConnections((cluster_handle + ".worldMatrix[0]"), type="cluster", destination=1)
    cluster_set = cmds.listConnections(cluster_deform_node[0], type="objectSet")
    extracted_vertices = cmds.sets(cluster_set[0], q=1)

    # 28: Control Vertices (CVs)     31: Polygon Vertices
    # 36: Subdivision Mesh Points    46: Lattice Points
    extracted_vertices = cmds.filterExpand(extracted_vertices, selectionMask=(28, 31, 36, 46))  # Filter Points Only

    # Isolate vertices on mesh
    vertices_on_mesh = []
    for vertex in extracted_vertices:
        name = vertex.encode('utf-8')
        if name.startswith(mesh_transform):
            vertices_on_mesh.append(vertex)

    # Pair Vertices with their weights
    vertices_with_weights = []
    for vertex in vertices_on_mesh:
        vertex_weight_pair = [vertex]
        value_w = cmds.percent(cluster_deform_node[0], vertex, q=1, v=1)
        vertex_weight_pair.append(value_w[0])
        vertices_with_weights.append(vertex_weight_pair)

    return vertices_with_weights


def loader_existence_check(obj):
    """
    Loader existence check. 
    If object exists, select it.

    Args:
        obj (string): any Maya node
    """
    if cmds.objExists(obj):
        cmds.select(obj)
        cmds.headsUpMessage(obj + " selected", verticalOffset=150)
    else:
        cmds.warning("Object doesn't exist! Did you delete or rename it after loading it?")


# Build GUI
if __name__ == '__main__':
    build_gui_mirror_cluster_tool()
