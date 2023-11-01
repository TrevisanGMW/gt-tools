"""
Node Utilities
github.com/TrevisanGMW/gt-tools
"""
from gt.utils.uuid_utils import get_uuid, get_object_from_uuid
from gt.utils.naming_utils import get_short_name
import maya.cmds as cmds
import logging


# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Node(str):
    """
   Represents a node in Autodesk Maya.

   Args:
       path (str): The path to the Maya node.

   Attributes:
       uuid (str): The UUID (unique identifier) of the Maya node.

   Methods:
       get_uuid: Get the UUID of the Maya node.
       get_long_name: Get the long name of the Maya node.
       get_short_name: Get the short name of the Maya node.
       is_dag: Check if the Maya node is a DAG (Directed Acyclic Graph) node.
       is_transform: Check if the Maya node is a transform node.
       exists: Check if the Maya node exists in the scene.

   """
    def __init__(self, path):
        """
        Initialize a Node instance.

        Args:
           path (str): The path to the Maya node.
        """
        if not path or not isinstance(path, str):
            raise Exception(f'Unable to read node. Provided must be a non-empty string.')
        if not cmds.objExists(path):
            raise Exception(f'Unable to read node. Object "{path}" could not be found in the scene.')
        self.uuid = get_uuid(path)

    def __repr__(self):
        """
        Return the long name of the object when using it as a string/printing.

        Returns:
            str: Long name (path) - Empty string if not found
        """
        path = self.get_long_name()
        if not path:
            path = ''
        return path

    def __str__(self):
        """
        Return the long name of the object when using it as a string/printing.

        Returns:
            str: Long name (path) - Empty string if not found
        """
        return self.get_long_name()

    def __add__(self, other):
        """
        Concatenate the long name of the Node instance with another string.

        Args:
           other (str): The string to concatenate with the long name of the Node instance.

        Returns:
           str: The result of the concatenation as a regular string.

        Raises:
           TypeError: If the 'other' operand is not a string.
        """
        if isinstance(other, str):
            return str(self.get_long_name() + other)
        else:
            raise TypeError('Unsupported operand type for +: "str" and ' + type(other).__name__)

    def __radd__(self, other):
        """
        Concatenate another string with the long name of the Node instance.

        Args:
           other (str): The string to concatenate with the long name of the Node.

        Returns:
           str: The result of the concatenation as a regular string.

        Raises:
           TypeError: If the 'other' operand is not a string.
        """
        if isinstance(other, str):
            return str(other + self.get_long_name())
        else:
            raise TypeError('Unsupported operand type for +: ' + type(other).__name__ + ' and "str"')

    def get_uuid(self):
        """
        Get the UUID of the Maya node.

        Returns:
            str: The UUID of the Maya node.
        """
        return self.uuid

    def get_long_name(self):
        """
        Get the long name of the Maya node.

        Returns:
           str or None: The long name of the Maya node. None if not found.
        """
        long_name = get_object_from_uuid(uuid_string=str(self.uuid))
        if long_name:
            return long_name
        return ""

    def get_short_name(self):
        """
        Get the short name of the Maya node.

        Returns:
            str or None: The short name of the Maya node. None if not found.
        """
        return get_short_name(self.get_long_name())

    def is_dag(self):
        """
        Check if the object is a DAG (Directed Acyclic Graph) node in Maya.

        Returns:
            bool: True if the object is a DAG node, False otherwise.
        """
        path = self.get_long_name()
        if path and 'dagNode' in cmds.nodeType(path, inherited=True):
            return True
        else:
            return False

    def is_transform(self):
        """
        Check if the Maya node is a transform node.

        Returns:
            bool: True if the node is a transform node, False otherwise.
        """
        path = self.get_long_name()
        if path and cmds.ls(path, typ='transform'):
            return True
        else:
            return False

    def exists(self):
        """
        Check if the Maya node exists in the scene.

        Returns:
           bool: True if the node exists, False otherwise.
        """
        return bool(self.get_long_name())

    def get_shape_types(self):
        """
        Get the types of shapes found under a transform in Maya.

        Returns:
            list: A list of shape types found under the transform node.
        """
        # Check if the given node exists
        path = self.get_long_name()
        if not cmds.objExists(path):
            return []
        shapes = cmds.listRelatives(path, shapes=True) or []
        shape_types = [cmds.nodeType(shape) for shape in shapes]
        return shape_types


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    a_node = Node(path="pSphere1")
    print(a_node)
