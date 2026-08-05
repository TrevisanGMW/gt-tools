"""
Namespace Utilities

Import Line:
    import gt.core.namespace as core_nspace
"""

from gt.core.feedback import FeedbackMessage
import maya.api.OpenMaya as OpenMaya
import maya.cmds as cmds
import maya.mel as mel
import logging
import sys

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_namespace_hierarchy_list(obj, root_only=False):
    """
    Breakdown and object's namespace into a list of namespaces including parent, child, grandchild, etc...

    Args:
        obj (str) : Name of the object to extract namespace
        root_only (bool, optional): If True, it will only return the first (parent) namespace and ignore any
                                    other namespaces inside of it. Otherwise, it will return the entire list.

    Returns:
        list: List of namespaces in following its hierarchy order.
              e.g. ["parentNamespace", "childNamespace", "grandChildNamespace"]
              or  ["parentNamespace"]
    """
    namespace_list = []
    obj_namespaces = get_namespaces(obj)
    if obj_namespaces:
        namespace_list = obj_namespaces[0].split(":")
    if len(namespace_list) > 0 and root_only:
        return [namespace_list[0]]
    return namespace_list


def get_namespaces(obj_list):
    """
    Get the all namespaces found in provided objects
    Args:
        obj_list (list, str): A list of objects to extract namespaces from.
                                 If a string is provided, it's automatically converted to a list, so it's compatible.

    Returns:
        list: A list of namespaces
    """
    if isinstance(obj_list, str):  # Convert to list in case a string was provided
        obj_list = [obj_list]
    if not obj_list:
        return []
    namespaces = []
    for node in obj_list:
        ns_shortname = namespaces_split(node)
        if ns_shortname[0]:
            if not namespaces.count(ns_shortname[0]):
                namespaces.append(ns_shortname[0])
    return namespaces


def get_namespace(node):
    """
    Get the all namespaces found in provided objects
    Args:
        node (str): An object to extract namespace from.

    Returns:
        str: Namespace of the provided object. Empty string if it doesn't have a namespace
    """
    namespace = get_namespaces(node)
    if namespace:
        return namespace[0]
    else:
        return ""


def namespaces_split(object_name):
    """
    Extracts namespaces and short name, returns a tuple with this extracted information (namespace, shortname)

    Args:
        object_name (str): Name of the object

    Returns:
        tuple: (namespace, short name)
    """
    if not object_name:
        return None, None

    # Remove full path
    path = [x for x in object_name.split("|") if x]
    object_name = path[-1]

    short_name = [x for x in object_name.split(":") if x]

    if not short_name:
        return "", ""
    if len(short_name) == 1:
        return "", short_name[0]
    else:
        return ":".join(short_name[:-1]), short_name[-1]


def delete_namespaces(object_list=None):
    """
    Deletes all namespaces in the scene
    Args:
        object_list ( list, optional): A list of objects to affect. If not provided, entire scene is used instead.
    Returns:
        Number of namespaces deleted (int)
    """
    counter = 0
    if object_list:
        for obj in object_list:
            if ":" in obj:
                namespace = obj.split(":")[0]
                cmds.namespace(removeNamespace=namespace, mergeNamespaceWithRoot=True)
                counter += 1
        return counter

    function_name = "Delete All Namespaces"
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    counter = 0
    try:
        default_namespaces = ["UI", "shared"]

        def num_children(ns):
            """
            Used as a sort key, this will sort namespaces by how many children they have.
            Sort key function to order namespaces by their depth.

            Counts the number of colon separators to determine how many
            child namespaces the given namespace has.

            Args:
                ns (str): The namespace string to evaluate.

            Returns:
                int: The count of colon characters in the namespace,
                     representing its depth.
            """
            return ns.count(":")

        namespaces = [
            namespace for namespace in cmds.namespaceInfo(lon=True, r=True) if namespace not in default_namespaces
        ]

        # Reverse List
        namespaces.sort(key=num_children, reverse=True)  # So it does the children first

        logger.debug(namespaces)

        for namespace in namespaces:
            if namespace not in default_namespaces:
                mel.eval('namespace -mergeNamespaceWithRoot -removeNamespace "' + namespace + '";')
                counter += 1
    except Exception as e:
        cmds.warning(str(e))
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)
    feedback = FeedbackMessage(
        quantity=counter,
        singular="namespace was",
        plural="namespaces were",
        conclusion="deleted.",
        zero_overwrite_message="No namespaces found in this scene.",
    )
    feedback.print_inview_message(system_write=False)
    feedback.conclusion = 'merged with the "root".'
    sys.stdout.write(f"\n{feedback.get_string_message()}")


def apply_namespace_to_string(in_string, namespace=None):
    """
    Add the supplied namespace to the name.

    Args:
        in_string (string): Maya scene node name
        namespace (string): chosen namespace (if None nothing will happen, if empty string it returns
        the object without namespace, if string it returns the object with the new namespace)

    Returns:
        name (string)
    """

    if namespace is None or namespace == "":
        return in_string

    # check string type
    if not isinstance(namespace, str):
        logger.debug("Namespace supplied must be a string.")
        return in_string

    string_name = in_string.split(":")
    out_string = namespace + ":" + string_name[-1]

    return out_string


def strip_namespace(node_name):
    """
    Removes the namespace prefix from a Maya node's full name.

    If the provided node name does not contain a namespace (a colon ':'),
    the original name will be returned. This is a common utility for getting
    the base name of an object.

    Args:
        node_name (str): The full name of the Maya node, potentially including
                         a namespace (e.g., 'characterName:L_arm_jnt').

    Returns:
        str: The name of the node without any namespace prefix.
    """
    # Split by colon and return the last component
    return node_name.split(":")[-1]


class StripNamespace(object):
    """
    Context manager to temporarily strip a namespace from all dependency nodes within a given namespace.

    This allows nodes to behave as if they have no namespace, including nodes that are normally read-only
    due to file referencing.

    Example:
        with StripNamespace('someNamespace') as stripped_nodes:
            print(cmds.ls(stripped_nodes))

    Attributes:
        original_names (dict): Maps node UUIDs to their original names within the namespace.
        namespace (str): The full namespace path being stripped.
    """

    @classmethod
    def as_name(cls, uuid):
        """
        Get the node name from its UUID.

        Args:
            uuid (str): The unique identifier of the node.

        Returns:
            str or None: The name of the node if found, otherwise None.
        """
        names = cmds.ls(uuid)
        return names[0] if names else None

    def __init__(self, namespace):
        """
        Initialize the StripNamespace context manager.

        Args:
            namespace (str): The namespace to strip from dependency nodes.

        Raises:
            ValueError: If the provided namespace does not exist.
        """
        if cmds.namespace(exists=namespace):
            self.original_names = {}  # (UUID, name_within_namespace)
            self.namespace = cmds.namespaceInfo(namespace, fn=True)
        else:
            raise ValueError('Could not locate supplied namespace, "{0}"'.format(namespace))

    def __enter__(self):
        """
        Enter the context: strip the namespace from all dependency nodes.

        Iterates over all dependency nodes within the namespace, renames them to remove the namespace prefix,
        bypassing any read-only restrictions.

        Returns:
            list[str]: List of node names with the namespace stripped.
        """
        for absolute_name in cmds.namespaceInfo(self.namespace, listOnlyDependencyNodes=True, fullName=True):

            # Ensure node was *not* auto-renamed (IE: shape nodes)
            if cmds.objExists(absolute_name):

                # get an api handle to the node
                try:
                    api_obj = OpenMaya.MGlobal.getSelectionListByName(absolute_name).getDependNode(0)
                    api_node = OpenMaya.MFnDependencyNode(api_obj)

                    # Remember the original name to return upon exit
                    uuid = api_node.uuid().asString()
                    self.original_names[uuid] = api_node.name()

                    # Strip namespace by renaming via api, bypassing read-only restrictions
                    without_namespace = api_node.name().replace(self.namespace, "")
                    api_node.setName(without_namespace)

                except RuntimeError:
                    pass  # Ignores Unrecognized objects (kFailure) Internal Errors

        return [self.as_name(uuid) for uuid in self.original_names]

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context: restore original node names with namespaces.

        Args:
            exc_type (type or None): The exception type if an exception was raised, otherwise None.
            exc_val (Exception or None): The exception instance if an exception was raised, otherwise None.
            exc_tb (traceback or None): The traceback object if an exception was raised, otherwise None.

        Restores the original names of all nodes that were renamed on entering the context.
        """
        for uuid, original_name in self.original_names.items():
            current_name = self.as_name(uuid)
            api_obj = OpenMaya.MGlobal.getSelectionListByName(current_name).getDependNode(0)
            api_node = OpenMaya.MFnDependencyNode(api_obj)
            api_node.setName(original_name)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint

    out = None
    pprint(out)
