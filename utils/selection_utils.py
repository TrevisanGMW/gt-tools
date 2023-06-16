from naming_utils import get_short_name
import maya.cmds as cmds
import logging
import random
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger("selection_utils")
logger.setLevel(logging.INFO)


def select_non_unique_objects():
    """ Selects all non-unique objects (objects with the same short name) """
    all_transforms = cmds.ls(type='transform')
    short_names = []
    non_unique_transforms = []
    for obj in all_transforms:  # Get all Short Names
        short_names.append(get_short_name(obj))

    for obj in all_transforms:
        short_name = get_short_name(obj)
        if short_names.count(short_name) > 1:
            non_unique_transforms.append(obj)

    cmds.select(non_unique_transforms, r=True)

    if len(non_unique_transforms) > 0:
        in_view_message = '<' + str(random.random()) + '>'
        in_view_message += '<span style=\"color:#FF0000;text-decoration:underline;\">'
        in_view_message += str(len(non_unique_transforms)) + '</span> non-unique objects were selected.'
        message = '\n' + str(len(non_unique_transforms)) + ' non-unique objects were found in this scene. ' \
                                                           'Rename them to avoid conflicts.'
    else:
        in_view_message = '<' + str(random.random()) + '>'
        in_view_message += 'All objects seem to have unique names in this scene.'
        message = 'No repeated names found in this scene.'
    cmds.inViewMessage(amg=in_view_message, pos='botLeft', fade=True, alpha=.9)
    sys.stdout.write(message)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
