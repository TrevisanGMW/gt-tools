"""
Outliner Utilities
github.com/TrevisanGMW/gt-tools
"""
import random

from gt.utils.iterable_utils import sanitize_maya_list
import maya.cmds as cmds
import logging

from utils.naming_utils import get_short_name

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OutlinerSortOptions:
    def __init__(self):
        """
        A library of sort options to be used with the "outliner_sort" function.
        """
    NAME = "name"  # Sorts by name
    SHUFFLE = "shuffle"  # Shuffles elements
    ATTRIBUTE = "attribute"  # Sorts by attribute


def reorder_up(target_list):
    """
    Reorder objects in the outliner relative to their siblings (move them up)
    If already the first item of the list, the function will cause it to pop down at the bottom of the list instead.

    Args:
        target_list (list, str, Node): List of objects to be reordered (not existing objects are ignored)

    Returns:
        bool: True if at least one object was updated, False = unable to find valid objects
    """
    if isinstance(target_list, str):
        target_list = [target_list]
    sanitized_list = sanitize_maya_list(target_list)
    if sanitized_list:
        cmds.reorder(sanitized_list, relative=-1)
        return True
    return False


def reorder_down(target_list):
    """
    Reorder objects in the outliner relative to their siblings (move them down)
    When already at the bottom of the list, it pops up as the first object.

    Args:
        target_list (list, str, Node): List of objects to be reordered (not existing objects are ignored)

    Returns:
        bool: True if at least one object was updated, False = unable to find valid objects
    """
    if isinstance(target_list, str):
        target_list = [target_list]
    sanitized_list = sanitize_maya_list(target_list)
    if sanitized_list:
        cmds.reorder(sanitized_list, relative=1)
        return True
    return False


def reorder_front(target_list):
    """
    Reorder objects in the outliner relative to their siblings (move them to the top)
    Args:
        target_list (list, str, Node): List of objects to be reordered (not existing objects are ignored)

    Returns:
        bool: True if at least one object was updated, False = unable to find valid objects
    """
    if isinstance(target_list, str):
        target_list = [target_list]
    sanitized_list = sanitize_maya_list(target_list)
    if sanitized_list:
        cmds.reorder(sanitized_list, front=True)
        return True
    return False


def reorder_back(target_list):
    """
    Reorder objects in the outliner relative to their siblings (move them to the bottom)
    Args:
        target_list (list, str, Node): List of objects to be reordered (not existing objects are ignored)

    Returns:
        bool: True if at least one object was updated, False = unable to find valid objects
    """
    if isinstance(target_list, str):
        target_list = [target_list]
    sanitized_list = sanitize_maya_list(target_list)
    if sanitized_list:
        cmds.reorder(sanitized_list, back=True)
        return True
    return False


def outliner_sort(target_list, operation=OutlinerSortOptions.NAME, is_ascending=True, attr='ty', verbose=False):
    """
    Outliner Sorting function: Moves objects up/down to arrange them in a certain order
    Args:
        target_list (list, str, Node): List of objects to be reordered (not existing objects are ignored)
        operation (string, optional): Name of the sorting operation: "name", "shuffle", "attribute"
        is_ascending (bool, optional): If active, operation will be ascending, if not descending
        attr (string, optional): attribute used to extract a value for when sorting by attribute
        verbose (bool, optional): If True, it will log issues as warnings instead of debug.
    """
    target_objects = {}
    for target_obj in target_list:
        short_name = get_short_name(target_obj)
        target_objects[short_name] = target_obj

    # Define Logger
    logger_output = logger.debug
    if verbose:
        logger_output = logger.warning

    if operation == OutlinerSortOptions.NAME:
        sorted_target = sorted(target_objects, reverse=is_ascending)
        for target_key in sorted_target:
            try:
                reorder_front([target_objects.get(target_key)])
            except Exception as e:
                logger_output(f'Errors happened during name sort operation. Issue: {e}')

    if operation == OutlinerSortOptions.SHUFFLE:
        random.shuffle(target_list)
        for target_obj in target_list:
            try:
                reorder_front([target_obj])
            except Exception as e:
                logger_output(f'Errors happened during shuffle operation. Issue: {e}')

    if operation == OutlinerSortOptions.ATTRIBUTE:
        value_dict = {}
        for target_obj in target_list:
            try:
                value = cmds.getAttr(f'{target_obj}.{attr}')
            except Exception as e:
                logger_output(f'Unable to get value of an attribute for ordering. Issue: {e}')
                value = 0
            value_dict[target_obj] = value

        sorted_dict = dict(sorted(value_dict.items(), key=lambda item: item[1], reverse=not is_ascending))
        for key in sorted_dict:
            try:
                reorder_front([key])
            except Exception as e:
                logger_output(f'Errors happened during sort by attribute operation. Issue: {e}')


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
