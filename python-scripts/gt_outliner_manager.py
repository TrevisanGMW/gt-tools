"""
 GT Outliner Manager - General Outliner organization script
 github.com/TrevisanGMW/gt-tools - 2022-08-18

 Idea:
 Sort (based on X, Y or Z pos or custom attr)
 auto re-order, re-parent (alphabetically/numerically)

"""
import maya.cmds as cmds
import logging

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


def outliner_sort(target_list):
    logger.debug('target_list: ' + str(target_list))
    issues = ''

    for target_obj in target_list:
        current_user_attributes = cmds.listAttr(target_obj, userDefined=True) or []
        print(current_user_attributes)
        print(target_obj)
        # for attr in attributes:
        #     if attr not in current_user_attributes:
        #         cmds.addAttr(target_obj, ln=attr, at=attr_type, k=True)
        #     else:
        #         issue = '\nUnable to add "' + target_obj + '.' + attr + '".'
        #         issue += ' Object already has an attribute with the same name'
        #         issues += issue

    if issues:
        print(issues)


if __name__ == '__main__':
    selection = cmds.ls(selection=True)
    # cmds.reorder(selection[0], front=True)
    # reorder_up(selection)
    # reorder_back(selection)
    outliner_sort(selection)
