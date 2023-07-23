"""
Selection Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.feedback_utils import FeedbackMessage
from gt.utils.naming_utils import get_short_name
import maya.cmds as cmds
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
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
    feedback = FeedbackMessage(quantity=len(non_unique_transforms),
                               singular='non-unique object was.',
                               plural='non-unique objects were',
                               conclusion='selected.',
                               zero_overwrite_message='All objects seem to have unique names in this scene.')
    feedback.print_inview_message(system_write=False)
    if len(non_unique_transforms):
        message = f'\n{str(len(non_unique_transforms))} non-unique objects were found in this scene. '
        message += 'Rename them to avoid conflicts.'
        sys.stdout.write(message)
    else:
        sys.stdout.write('\nNo repeated names found in this scene.')


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    pprint(out)
