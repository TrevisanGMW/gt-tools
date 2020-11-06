"""

 Apply Redshift wireframe shader to selected objects
 @Guilherme Trevisan - TrevisanGMW@gmail.com - 2020-11-04
 
 1.0 - 2020-11-04
 Initial Release

"""
import maya.cmds as cmds


redshift_plugin = 'redshift4maya'

# Load Redshift
if not cmds.pluginInfo(redshift_plugin, q=True, loaded=True):
    try:
        cmds.loadPlugin(redshift_plugin)
    except:
        message = '<span style=\"color:#FF0000;text-decoration:underline;\">Redshift</span> doesn\'t seem to be installed.'
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)

is_redshift_available = False
if cmds.pluginInfo(redshift_plugin, q=True, loaded=True):
    is_redshift_available = True

def create_wireframe_node(destination_input):
    rs_wireframe_node = cmds.createNode("RedshiftWireFrame")
    cmds.connectAttr( rs_wireframe_node + '.outColor', destination_input, force=True)
    cmds.setAttr(rs_wireframe_node + '.showHiddenEdges', 0)
    cmds.setAttr(rs_wireframe_node + '.polyColor', 0.5, 0.5, 0.5)

def create_wireframe_shader():
    if cmds.objExists('rsWireframe_lambertSG') and cmds.objExists('rsWireframe_lambert'):
        wireframe_node = cmds.listConnections( 'rsWireframe_lambert.c', s=True ) or []
        if len(wireframe_node) > 0:
            if cmds.objectType(wireframe_node[0]) != 'RedshiftWireFrame':
                create_wireframe_node('rsWireframe_lambert.c')
        else:
            create_wireframe_node('rsWireframe_lambert.c')
        return 'rsWireframe_lambertSG'
    else:
        shd = cmds.shadingNode('lambert', name="rsWireframe_lambert", asShader=True)
        sh_sg = cmds.sets(name='%sSG' % shd, empty=True, renderable=True, noSurfaceShader=True)
        cmds.connectAttr('%s.outColor' % shd, '%s.surfaceShader' % sh_sg)
        create_wireframe_node(shd + '.c')
        return sh_sg

def apply_wireframe_shader():
    selection = cmds.ls(selection=True)

    if len(selection) > 0:
        sh_sg = create_wireframe_shader()
        for obj in selection:
            if cmds.objExists(obj):
                cmds.sets(obj, e=True, forceElement=sh_sg)
                
        is_plural = 'objects'
        if len(selection) == 1:
            is_plural = 'object'
        message = 'The Redshift wireframe shader was applied to <span style=\"color:#FF0000;text-decoration:underline;\">'+ str(len(selection)) + '</span> ' + is_plural + '.'
        
        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)
    else:
        cmds.warning('Nothing selected. Please select select something and try again.')

if is_redshift_available:
    apply_wireframe_shader()