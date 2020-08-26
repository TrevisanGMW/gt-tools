import maya.cmds as cmds
import maya.mel as mel

# Simple Script used to export rig into game engines
scriptVersion = "1.0"

def rigging1_proxy_manager():
    if cmds.window("rigging1_proxy_manager", exists =True):
        cmds.deleteUI("rigging1_proxy_manager")    

    # main dialog Start Here =================================================================================

    rigging1_proxy_manager = cmds.window("rigging1_proxy_manager", title="Proxy Manager - " + scriptVersion,\
                          titleBar=True,minimizeButton=False,maximizeButton=False, sizeable =True)
    columnMain = cmds.columnLayout() 
    form = cmds.formLayout(p=columnMain)
    contentMain = cmds.columnLayout(adj = True)
    
    cmds.separator(h=10, p=contentMain, st="none" )
    cmds.text("Proxy Functions:")
    cmds.separator(h=5, p=contentMain, st="none" )
    container = cmds.rowColumnLayout( p=contentMain, numberOfColumns=3, columnWidth=[(1, 100), (2, 100),(3,10)], cs=[(1,10),(2,5),(3,5)])
    cmds.separator(h=10, p=contentMain, st="none" )
    cmds.button(p=container, l ="Attach Proxy", c=lambda x:connect_proxy_geo(), w=100, bgc=(.3,.7,.3))
    cmds.button(p=container, l ="Detach Proxy", c=lambda x:disconnect_proxy_geo(), bgc=(.7,.3,.3))
 
    cmds.showWindow(rigging1_proxy_manager)
    # main dialog Ends Here =================================================================================


# Functions to get all the stuff we need

def get_proxy_meshes():
    all_meshes = cmds.ls(type='mesh')
    filtered_meshes = [mesh for mesh in all_meshes if 'Proxy_geo' in mesh and 'Orig' not in mesh]
    all_mesh_transforms = []
    for mesh in filtered_meshes:
        filtered_relatives = cmds.listRelatives(mesh, p=True, path=True)
        all_mesh_transforms.append(filtered_relatives[0])
    return all_mesh_transforms

def get_bind_joints():
    all_joints = cmds.ls(type='joint')
    character_joints = [joint_ for joint_ in all_joints if '_jnt' in joint_ and '_endJnt' not in joint_]
    return character_joints

def get_proxy_skin_clusters():
    proxy_skin_clusters = []
    for proxy_mesh in get_proxy_meshes():
        relatives = cmds.listRelatives(proxy_mesh)
        connections = cmds.listConnections(relatives[0])
        skin_cluster = [connection for connection in connections if
                        'skinCluster' in connection and 'Set' not in connection and 'GroupId' not in connection]
        if skin_cluster:
            proxy_skin_clusters.append(skin_cluster)

    return proxy_skin_clusters

# Bind proxy geo steps

def connect_proxy_geo():
    go_to_bind_pose_all_geo()
    unbind_all_proxy_geo()
    for bind_joint in get_bind_joints():
        bind_proxy_geo(bind_joint)
    cmds.select(clear=True)


def bind_proxy_geo(bind_joint):
    bind_success = []
    for proxy_mesh in get_proxy_meshes():
        if bind_joint[:-4] in proxy_mesh:
            cmds.skinCluster(bind_joint, proxy_mesh, toSelectedBones=True)
            bind_success.append(bind_joint)
            return None
    if not bind_success:
        cmds.warning(bind_joint + ' is not properly named.')


# Unbind proxy geo steps

def disconnect_proxy_geo():
    go_to_bind_pose_all_geo()
    unbind_all_proxy_geo()
    delete_all_bind_poses()

def go_to_bind_pose_all_geo():
    for mesh_transform in get_proxy_meshes():
        relatives = cmds.listRelatives(mesh_transform)
        connections = cmds.listConnections(relatives[0])
        for connection in connections:
            if 'skinCluster' in connection:
                cmds.select(mesh_transform)
                cmds.GoToBindPose()
            cmds.select(clear=True)

def delete_all_bind_poses():
    all_dag_nodes = cmds.ls()
    for dag_node in all_dag_nodes:
        if 'bindPose' in dag_node:
            cmds.delete(dag_node)

def unbind_all_proxy_geo():
    for skin_cluster in get_proxy_skin_clusters():
        cmds.skinCluster(skin_cluster, edit=True, unbind=True)

# Build UI
if __name__ == "__main__":
    rigging1_proxy_manager()