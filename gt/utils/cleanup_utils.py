"""
Cleanup Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.feedback_utils import FeedbackMessage
import maya.cmds as cmds
import maya.mel as mel
import logging

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
    feedback = FeedbackMessage(quantity=num_deleted_nodes,
                               singular='unused node was',
                               plural='unused nodes were',
                               conclusion='deleted.',
                               zero_overwrite_message='No unused nodes found in this scene.')
    feedback.print_inview_message()


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

        feedback = FeedbackMessage(quantity=deleted_counter,
                                   singular='object was',
                                   plural='objects were',
                                   conclusion='deleted.',
                                   zero_overwrite_message='No nucleus nodes found in this scene.')
        feedback.print_inview_message()

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
        feedback = FeedbackMessage(quantity=deleted_counter,
                                   singular='locator was',
                                   plural='locators were',
                                   conclusion='deleted.',
                                   zero_overwrite_message='No locators found in this scene.')
        feedback.print_inview_message()

    except Exception as e:
        errors += str(e) + '\n'
        cmds.warning('An error occurred when deleting locators. Open the script editor for more information.')
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    if errors != '':
        print('######## Errors: ########')
        print(errors)

