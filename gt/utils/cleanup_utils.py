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


def delete_unused_nodes(verbose=True):
    """
    Deleted unused nodes (such as materials not connected to anything or nodes without any connections)
    This is done through a Maya MEL function "MLdeleteUnused()" but it's called here again for better feedback.
    Args:
        verbose (bool, optional): If True, it will print feedback with the number of unused deleted nodes.
    Returns:
        int: Number of unused deleted nodes.
    """
    num_deleted_nodes = mel.eval('MLdeleteUnused();')
    if verbose:
        feedback = FeedbackMessage(quantity=num_deleted_nodes,
                                   singular='unused node was',
                                   plural='unused nodes were',
                                   conclusion='deleted.',
                                   zero_overwrite_message='No unused nodes found in this scene.')
        feedback.print_inview_message()
    return num_deleted_nodes


def delete_nucleus_nodes(verbose=True, include_fields=True):
    """
    Deletes all elements related to particles.
    Args:
        verbose (bool, optional): If True, it will print feedback with the number of deleted nodes.
        include_fields (bool, optional): If True, it will also count field as "nucleus nodes" to be deleted.
    Returns:
        int: Number of nucleus deleted nodes.
    """
    errors = ''
    function_name = 'Delete Nucleus Nodes'
    deleted_counter = 0
    try:
        cmds.undoInfo(openChunk=True, chunkName=function_name)

        # Without Transform Types
        no_transform_types = ['nucleus',
                              'pointEmitter',
                              'instancer']
        # Fields/Solvers Types
        if include_fields:
            field_types = ['airField',
                           'dragField',
                           'newtonField',
                           'radialField',
                           'turbulenceField',
                           'uniformField',
                           'vortexField',
                           'volumeAxisField']
            no_transform_types += field_types
        no_transforms = []
        for node_type in no_transform_types:
            no_transforms += cmds.ls(typ=node_type) or []

        # With Transform
        with_transform_types = ['nParticle',
                                'spring',
                                'particle',
                                'nRigid',
                                'nCloth',
                                'pfxHair',
                                'hairSystem',
                                'dynamicConstraint']
        with_transforms = []
        for transform_node_type in with_transform_types:
            with_transforms += cmds.ls(typ=transform_node_type) or []

        for obj in with_transforms:
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
        if verbose:
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
    return deleted_counter


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

