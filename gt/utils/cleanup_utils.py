import maya.cmds as cmds
import maya.mel as mel
import logging
import random
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def delete_unused_nodes():
    """
    Deleted unused nodes (such as materials not connected to anything or nodes without any connections)
    This is done through a Maya MEL function "MLdeleteUnused()" but it's called here again for better feedback.
    """
    num_deleted_nodes = mel.eval('MLdeleteUnused();')
    logger.debug('Number of unused nodes: ' + str(num_deleted_nodes))
    if num_deleted_nodes > 0:
        is_plural = 'unused nodes were'
        if num_deleted_nodes == 1:
            is_plural = 'unused node was'
        in_view_message = '<' + str(random.random()) + '>'
        in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(num_deleted_nodes)
        in_view_message += '</span> ' + is_plural + ' deleted.'
        message = '\n' + str(num_deleted_nodes) + ' ' + is_plural + ' deleted. Open'
        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
        sys.stdout.write(message)
    else:
        in_view_message = '<' + str(random.random()) + '>'
        in_view_message += 'No unused nodes found in this scene.'
        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)


def delete_nucleus_nodes():
    """ Deletes all elements related to particles """
    errors = ''
    function_name = 'Delete Nucleus Nodes'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)

        # Without Transform
        emitters = cmds.ls(typ='pointEmitter')
        solvers = cmds.ls(typ='nucleus')
        instancers = cmds.ls(typ='instancer')

        no_transforms = emitters + instancers + solvers + instancers

        # With Transform
        nparticle_nodes = cmds.ls(typ='nParticle')
        spring_nodes = cmds.ls(typ='spring')
        particle_nodes = cmds.ls(typ='particle')
        nrigid_nodes = cmds.ls(typ='nRigid')
        ncloth_nodes = cmds.ls(typ='nCloth')
        pfxhair_nodes = cmds.ls(typ='pfxHair')
        hair_nodes = cmds.ls(typ='hairSystem')
        nconstraint_nodes = cmds.ls(typ='dynamicConstraint')

        transforms = nparticle_nodes + spring_nodes + particle_nodes + nrigid_nodes
        transforms += ncloth_nodes + pfxhair_nodes + hair_nodes + nconstraint_nodes

        # Fields/Solvers Types
        # airField
        # dragField
        # newtonField
        # radialField
        # turbulenceField
        # uniformField
        # vortexField
        # volumeAxisField

        deleted_counter = 0
        for obj in transforms:
            try:
                parent = cmds.listRelatives(obj, parent=True) or []
                cmds.delete(parent[0])
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))
        for obj in no_transforms:
            try:
                cmds.delete(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        in_view_message = '<' + str(random.random()) + '>'
        if deleted_counter > 0:
            in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter)
            in_view_message += ' </span>'
            is_plural = 'objects were'
            if deleted_counter == 1:
                is_plural = 'object was'
            in_view_message += is_plural + ' deleted.'
        else:
            in_view_message += 'No nucleus nodes found in this scene.'

        cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)


def delete_all_locators():
    """ Deletes all locators """
    errors = ''
    function_name = 'Delete All Locators'
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)

        # With Transform
        locators = cmds.ls(typ='locator')

        deleted_counter = 0
        for obj in locators:
            try:
                parent = cmds.listRelatives(obj, parent=True) or []
                cmds.delete(parent[0])
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        message = '<span style=\"color:#FF0000;text-decoration:underline;\">' + str(deleted_counter) + ' </span>'
        is_plural = 'locators were'
        if deleted_counter == 1:
            is_plural = 'locator was'
        message += is_plural + ' deleted.'

        cmds.inViewMessage(amg=message, pos='botLeft', fade=True, alpha=.9)

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred when deleting locators. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)

