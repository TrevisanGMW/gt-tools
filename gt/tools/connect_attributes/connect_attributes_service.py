"""Maya scene operations for Connect Attributes."""

import logging


logger = logging.getLogger(__name__)


class ConnectAttributesService:
    """Executes attribute connection requests using ``maya.cmds``."""

    NODE_PLUGS = {
        "plusMinusAverage": {
            "scalar_input": "input1D[0]",
            "scalar_secondary": "input1D[1]",
            "scalar_output": "output1D",
            "vector_input": "input3D[0]",
            "vector_secondary": "input3D[1]",
            "vector_output": "output3D",
        },
        "multiplyDivide": {
            "scalar_input": "input1X",
            "scalar_secondary": "input2X",
            "scalar_output": "outputX",
            "vector_input": "input1",
            "vector_secondary": "input2",
            "vector_output": "output",
        },
        "condition": {
            "scalar_input": "colorIfTrueR",
            "scalar_secondary": "colorIfFalseR",
            "scalar_output": "outColorR",
            "vector_input": "colorIfTrue",
            "vector_secondary": "colorIfFalse",
            "vector_output": "outColor",
        },
    }

    def __init__(self, cmds_module=None):
        """Initializes the service.

        Args:
            cmds_module (module, optional): Injected ``maya.cmds`` replacement for tests.
        """
        self._cmds = cmds_module

    def _get_cmds(self):
        """Gets maya.cmds lazily.

        Returns:
            module: Maya commands module.
        """
        if self._cmds is None:
            import maya.cmds as cmds

            self._cmds = cmds
        return self._cmds

    def get_selection(self):
        """Gets the ordered Maya selection.

        Returns:
            list: Selected node names.
        """
        return self._get_cmds().ls(selection=True, long=True) or []

    def node_exists(self, node):
        """Checks whether a Maya node exists.

        Args:
            node (str): Node name.

        Returns:
            bool: True when the node exists.
        """
        return bool(node and self._get_cmds().objExists(node))

    def select_nodes(self, nodes):
        """Selects existing nodes.

        Args:
            nodes (list): Node names.
        """
        existing_nodes = [node for node in nodes or [] if self.node_exists(node)]
        if existing_nodes:
            self._get_cmds().select(existing_nodes, replace=True)

    def list_attributes(self, node, keyable=False):
        """Lists attributes on a node.

        Args:
            node (str): Scene node.
            keyable (bool, optional): Whether to return only keyable attributes.

        Returns:
            list: Sorted attribute names.
        """
        if not self.node_exists(node):
            return []
        attributes = self._get_cmds().listAttr(node, keyable=True) if keyable else self._get_cmds().listAttr(node)
        return sorted(attributes or [], key=lambda item: item.lower())

    def execute(self, request):
        """Executes a connect or disconnect request in one Maya undo chunk.

        Args:
            request (dict): Validated request from the model.

        Returns:
            dict: Counts, created nodes, and per-plug errors.
        """
        cmds = self._get_cmds()
        result = {"succeeded": 0, "skipped": 0, "created_nodes": [], "errors": []}
        shared_input_node = None
        cmds.undoInfo(openChunk=True, chunkName="Connect Attributes")
        try:
            if request.get("operation") == "connect" and request.get("use_utility_node"):
                if request.get("use_shared_input"):
                    shared_input_node = cmds.createNode(request.get("shared_input_node_type"))
                    result["created_nodes"].append(shared_input_node)
            for target_object in request.get("target_objects", []):
                for target_attribute in request.get("target_attributes", []):
                    try:
                        if request.get("operation") == "disconnect":
                            changed = self._disconnect_target(target_object, target_attribute)
                            result["succeeded" if changed else "skipped"] += 1
                        else:
                            created_nodes = self._connect_target(
                                request=request,
                                target_object=target_object,
                                target_attribute=target_attribute,
                                shared_input_node=shared_input_node,
                            )
                            result["created_nodes"].extend(created_nodes)
                            result["succeeded"] += 1
                    except Exception as exception:
                        target_plug = f"{target_object}.{target_attribute}"
                        result["errors"].append(f"{target_plug}: {exception}")
            if shared_input_node and not result["succeeded"]:
                cmds.delete(shared_input_node)
                result["created_nodes"].remove(shared_input_node)
            return result
        finally:
            cmds.undoInfo(closeChunk=True, chunkName="Connect Attributes")

    def _connect_target(self, request, target_object, target_attribute, shared_input_node=None):
        """Builds one source-to-target connection chain.

        Args:
            request (dict): Connection settings.
            target_object (str): Target node.
            target_attribute (str): Target attribute.
            shared_input_node (str, optional): Shared secondary-input node.

        Returns:
            list: Nodes created for this connection.
        """
        cmds = self._get_cmds()
        source_plug = f"{request.get('source_object')}.{request.get('source_attribute')}"
        target_plug = f"{target_object}.{target_attribute}"
        self._validate_plug(source_plug, "Source")
        self._validate_plug(target_plug, "Target")
        if cmds.connectionInfo(target_plug, isDestination=True) and not request.get("force_connection"):
            raise RuntimeError("Target already has an incoming connection. Enable Replace Existing to override it.")

        created_nodes = []
        try:
            chain_output = source_plug
            is_vector = self._is_vector_plug(source_plug)
            if request.get("use_utility_node"):
                utility_type = request.get("utility_node_type")
                utility_node = cmds.createNode(utility_type)
                created_nodes.append(utility_node)
                utility_input = self.get_node_plug(utility_type, "input", is_vector)
                utility_output = self.get_node_plug(utility_type, "output", is_vector)
                cmds.connectAttr(chain_output, f"{utility_node}.{utility_input}", force=True)
                chain_output = f"{utility_node}.{utility_output}"
                if shared_input_node:
                    secondary_input = self.get_node_plug(utility_type, "secondary", is_vector)
                    shared_output = self.get_node_plug(
                        request.get("shared_input_node_type"), "output", is_vector
                    )
                    cmds.connectAttr(
                        f"{shared_input_node}.{shared_output}",
                        f"{utility_node}.{secondary_input}",
                        force=True,
                    )

            if request.get("add_reverse_node"):
                reverse_node = cmds.createNode("reverse")
                created_nodes.append(reverse_node)
                reverse_input = "input" if is_vector else "inputX"
                reverse_output = "output" if is_vector else "outputX"
                cmds.connectAttr(chain_output, f"{reverse_node}.{reverse_input}", force=True)
                chain_output = f"{reverse_node}.{reverse_output}"

            cmds.connectAttr(chain_output, target_plug, force=bool(request.get("force_connection")))
            return created_nodes
        except Exception:
            if created_nodes:
                cmds.delete(created_nodes)
            raise

    def _disconnect_target(self, target_object, target_attribute):
        """Disconnects every incoming connection from one exact target plug.

        Args:
            target_object (str): Target node.
            target_attribute (str): Target attribute.

        Returns:
            bool: True when at least one connection was removed.
        """
        cmds = self._get_cmds()
        target_plug = f"{target_object}.{target_attribute}"
        self._validate_plug(target_plug, "Target")
        connections = cmds.listConnections(
            target_plug,
            source=True,
            destination=False,
            plugs=True,
            connections=True,
            skipConversionNodes=False,
        ) or []
        connection_pairs = zip(connections[1::2], connections[::2])
        removed_count = 0
        for source_plug, destination_plug in connection_pairs:
            cmds.disconnectAttr(source_plug, destination_plug)
            removed_count += 1
        return bool(removed_count)

    def _validate_plug(self, plug, label):
        """Raises when a requested node plug does not exist.

        Args:
            plug (str): Maya plug.
            label (str): User-facing plug role.

        Raises:
            RuntimeError: If the plug does not exist.
        """
        if not self._get_cmds().objExists(plug):
            raise RuntimeError(f"{label} attribute does not exist: {plug}")

    def _is_vector_plug(self, plug):
        """Determines whether a Maya plug carries a three-component value.

        Args:
            plug (str): Maya plug.

        Returns:
            bool: True for common three-component numeric types.
        """
        attribute_type = self._get_cmds().getAttr(plug, type=True)
        return attribute_type in ("double3", "float3", "long3", "short3")

    @classmethod
    def get_node_plug(cls, node_type, role, is_vector):
        """Gets a supported utility-node plug name.

        Args:
            node_type (str): Supported Maya utility node type.
            role (str): ``input``, ``secondary``, or ``output``.
            is_vector (bool): Whether the plug should carry three components.

        Returns:
            str: Relative node plug name.

        Raises:
            ValueError: If the node type or role is unsupported.
        """
        if node_type not in cls.NODE_PLUGS:
            raise ValueError(f"Unsupported utility node type: {node_type}")
        plug_key = f"{'vector' if is_vector else 'scalar'}_{role}"
        if plug_key not in cls.NODE_PLUGS[node_type]:
            raise ValueError(f"Unsupported utility node plug role: {role}")
        return cls.NODE_PLUGS[node_type][plug_key]
