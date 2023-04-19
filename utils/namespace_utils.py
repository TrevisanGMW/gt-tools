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


def get_namespaces(obj_list):
    """
    Get the all namespaces found in provided objects
    Args:
        obj_list (list): A list of objects to extract namespaces from

    Returns:
        A sorted list of namespaces
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

    return sorted(namespaces)


def namespaces_split(object_name):
    """
    Extracts namespaces and short name, returns a tuple with this extracted information (namespace, shortname)

    Args:
        object_name (string): Name of the object

    Returns:
        Tuple: (namespace, short name)
    """
    if not object_name:
        return None, None

    # Remove full path
    path = [x for x in object_name.split('|') if x]
    object_name = path[-1]

    short_name = [x for x in object_name.split(":") if x]

    if not short_name:
        return "", ""
    if len(short_name) == 1:
        return "", short_name[0]
    else:
        return ':'.join(short_name[:-1]), short_name[-1]


class StripNamespace(object):
    """
    Temporarily strip a namespace from all dependency nodes within a namespace.

    This allows nodes to masquerade as if they never had namespace, including those considered read-only
    due to file referencing.

    Usage:
        with StripNamespace('someNamespace') as stripped_nodes:
            print(cmds.ls(stripped_nodes))
    """

    @classmethod
    def as_name(cls, uuid):
        """
        Convenience method to extract the name from uuid

        type uuid: basestring
        rtype: unicode|None
        """
        names = cmds.ls(uuid)
        return names[0] if names else None

    def __init__(self, namespace):
        if cmds.namespace(exists=namespace):
            self.original_names = {}  # (UUID, name_within_namespace)
            self.namespace = cmds.namespaceInfo(namespace, fn=True)
        else:
            raise ValueError('Could not locate supplied namespace, "{0}"'.format(namespace))

    def __enter__(self):
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
                    without_namespace = api_node.name().replace(self.namespace, '')
                    api_node.setName(without_namespace)

                except RuntimeError:
                    pass  # Ignores Unrecognized objects (kFailure) Internal Errors

        return [self.as_name(uuid) for uuid in self.original_names]

    def __exit__(self, exc_type, exc_val, exc_tb):
        for uuid, original_name in self.original_names.items():
            current_name = self.as_name(uuid)
            api_obj = OpenMaya.MGlobal.getSelectionListByName(current_name).getDependNode(0)
            api_node = OpenMaya.MFnDependencyNode(api_obj)
            api_node.setName(original_name)
