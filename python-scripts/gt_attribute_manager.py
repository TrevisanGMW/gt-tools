"""

Script would work exactly like the "Add attribute" function, but it would retain the parameters and allow for multiple
variables (separated by commas)

Hide/unhide attributes for selected elements.
Lock/unlock attributes for selected elements.
Auto create a list of attributes for selected elements.
Maybe attempt to change the order of the attributes within Maya.


"""
from collections import namedtuple
import maya.cmds as cmds


def add_attributes(target_list, attributes):
    for target_obj in target_list:
        for attr in attributes:
            print(attr)
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
