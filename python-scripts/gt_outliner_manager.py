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
    outliner_sort(selection)
