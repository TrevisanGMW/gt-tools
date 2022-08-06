"""

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
from collections import namedtuple
import maya.cmds as cmds


def add_attributes(target_list, attribute_tuples):
    for target_obj in target_list:
        for attr in attribute_tuples:
            print('target_obj: ' + target_obj)
            print('attr: ' + attr)
            # cmds.addAttr(target_obj, ln=attr, at='double', k=True)


if __name__ == '__main__':

    # Pose Object Setup
    Attribute = namedtuple('Attribute', ['name', 'type'])
    attributes = []

    attributes += [
        Attribute(name='attrOne',
                  type='double'),
        Attribute(name='attrTwo',
                  type='double')
                  ]

    add_attributes(['abc'], attributes)
