"""
 GT Attribute Manager
 github.com/TrevisanGMW/gt-tools - 2022-08-06

 0.0.1 - 2022-08-06
 Created script file
 Added description

 0.0.2 - 2022-08-07
 Added logger
 Added parameters to add_attributes + debug lines

Script would work exactly like the "Add attribute" function, but it would retain the parameters and allow for multiple
variables (separated by commas)

Hide/unhide attributes for selected elements.
Lock/unlock attributes for selected elements.
Auto create a list of attributes for selected elements.
Maybe attempt to change the order of the attributes within Maya.


Plan:

Attributes (short)
Vector, Integer, String, Float, Boolean, ENUM?
Minimum
Maximum
Default

_______________
Search Filter
Make Keyable, Displayable, Hidden, Delete, Rename, Move?

Rename Nice Name (search and replace?)

"""
# from collections import namedtuple
import maya.cmds as cmds
import logging

logging.basicConfig()
logger = logging.getLogger("gt_attribute_manager")
logger.setLevel(logging.INFO)


def add_attributes(target_list,
                   attributes,
                   attr_type,
                   minimum, maximum,
                   default, status='keyable'):

    logger.debug('target_list: ' + str(target_list))
    logger.debug('attributes: ' + str(attributes))
    logger.debug('attr_type: ' + str(attr_type))
    logger.debug('minimum: ' + str(minimum))
    logger.debug('maximum: ' + str(maximum))
    logger.debug('default: ' + str(default))
    logger.debug('status: ' + str(status))

    issues = ''

    for target_obj in target_list:
        current_user_attributes = cmds.listAttr(target_obj, userDefined=True) or []
        print(current_user_attributes)
        for attr in attributes:
            if attr not in current_user_attributes:
                cmds.addAttr(target_obj, ln=attr, at=attr_type, k=True)
            else:
                issue = '\nUnable to add "' + target_obj + '.' + attr + '".'
                issue += ' Object already has an attribute with the same name'
                issues += issue

    if issues:
        print(issues)


if __name__ == '__main__':

    # Pose Object Setup
    # Attribute = namedtuple('Attribute', ['name', 'type'])
    # attributes = []
    #
    # attributes += [
    #     Attribute(name='attrOne',
    #               type='double'),
    #     Attribute(name='attrTwo',
    #               type='double')
    #               ]
    selection = cmds.ls(selection=True)
    add_attributes(['abc', 'def'], ['first', 'second'], 'double', 0, 10, 1)
