"""
 GT Outliner Manager - General Outliner organization script
 github.com/TrevisanGMW/gt-tools - 2022-08-18

 Idea:
 Sort (based on X, Y or Z pos or custom attr)
 auto re-order, re-parent (alphabetically/numerically)

"""
import maya.cmds as cmds
import logging
import random

logging.basicConfig()
logger = logging.getLogger("gt_outliner_manager")
logger.setLevel(logging.INFO)


def reorder_up(obj_list):
    """
    Reorder objects in the outliner relative to their siblings (move them up)
    Args:
        obj_list: List of objects to be reordered (not existing objects are ignored)

    Returns:
        operation_result: True = at least one object was updated, False = unable to find valid objects
    """
    valid_obj_list = []
    for obj in obj_list:
        if cmds.objExists(obj):
            valid_obj_list.append(obj)
    cmds.reorder(valid_obj_list, relative=-1)
    if valid_obj_list:
        return True
    else:
        return False


def reorder_down(obj_list):
    """
    Reorder objects in the outliner relative to their siblings (move them down)
    Args:
        obj_list: List of objects to be reordered (not existing objects are ignored)

    Returns:
        operation_result: True = at least one object was updated, False = unable to find valid objects
    """
    valid_obj_list = []
    for obj in obj_list:
        if cmds.objExists(obj):
            valid_obj_list.append(obj)
    cmds.reorder(valid_obj_list, relative=1)
    if valid_obj_list:
        return True
    else:
        return False


def reorder_front(obj_list):
    """
    Reorder objects in the outliner relative to their siblings (move them to the top)
    Args:
        obj_list: List of objects to be reordered (not existing objects are ignored)

    Returns:
        operation_result: True = at least one object was updated, False = unable to find valid objects
    """
    valid_obj_list = []
    for obj in obj_list:
        if cmds.objExists(obj):
            valid_obj_list.append(obj)
    cmds.reorder(valid_obj_list, front=True)
    if valid_obj_list:
        return True
    else:
        return False


def reorder_back(obj_list):
    """
    Reorder objects in the outliner relative to their siblings (move them to the bottom)
    Args:
        obj_list: List of objects to be reordered (not existing objects are ignored)

    Returns:
        operation_result: True = at least one object was updated, False = unable to find valid objects
    """
    valid_obj_list = []
    for obj in obj_list:
        if cmds.objExists(obj):
            valid_obj_list.append(obj)
    cmds.reorder(valid_obj_list, back=True)
    if valid_obj_list:
        return True
    else:
        return False


def get_short_name(obj):
    """
    Get the name of the objects without its path (Maya returns full path if name is not unique)

    Args:
        obj (string) : object to extract short name

    Returns:
        short_name (string) : Name of the object without its full path
    """
    short_name = ''
    if obj == '':
        return ''
    split_path = obj.split('|')
    if len(split_path) >= 1:
        short_name = split_path[len(split_path) - 1]
    return short_name


def outliner_sort(obj_list, sort_operation='name', is_ascending=True):
    logger.debug('obj_list: ' + str(obj_list))
    issues = ''

    target_objects = {}

    for target_obj in obj_list:
        short_name = get_short_name(target_obj)
        print(short_name)
        target_objects[short_name] = target_obj

    sorted_target = sorted(target_objects, reverse=is_ascending)

    if sort_operation == 'name':
        for target_key in sorted_target:
            try:
                reorder_front([target_objects.get(target_key)])
            except Exception as e:
                issues += str(e) + '\n'
            logger.debug('target_value: ' + str([target_objects.get(target_key)]))

    if sort_operation == 'shuffle':
        random.shuffle(obj_list)
        for target_obj in obj_list:
            try:
                reorder_front([target_obj])
            except Exception as e:
                issues += str(e) + '\n'
            logger.debug('target_value: ' + str([target_obj]))

    if issues:
        print(issues)


if __name__ == '__main__':
    logger.setLevel(logging.DEBUG)
    selection = cmds.ls(selection=True, long=True)
    # cmds.reorder(selection[0], front=True)
    # reorder_up(selection)
    # reorder_back(selection)
    outliner_sort(selection, is_ascending=True)
    # outliner_sort(selection, sort_operation='shuffle')
