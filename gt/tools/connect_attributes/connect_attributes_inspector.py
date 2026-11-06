"""Read-only Maya scene inspection for Connect Attributes."""

from gt.tools.connect_attributes.connect_attributes_validation import check_connection_types


class ConnectAttributesInspector:
    """Builds structured operation rows without changing the scene."""

    def __init__(self, cmds_module):
        """Stores an injected Maya command interface.

        Args:
            cmds_module (module): Maya commands or a compatible test double.
        """
        self.cmds = cmds_module

    def inspect(self, request):
        """Inspects every requested target plug, including disconnection pairs.

        Args:
            request (dict): Normalized connection or disconnection request.

        Returns:
            list: Operation dictionaries with source, target, via, status and details.
        """
        rows = []
        seen_pairs = set()
        for target_object in request.get("target_objects", []):
            for attribute in request.get("target_attributes", []):
                target_plug = f"{target_object}.{attribute}"
                try:
                    if request.get("operation") == "disconnect":
                        target_rows = self._inspect_disconnect(target_plug)
                    else:
                        target_rows = [self._inspect_connect(request, target_plug)]
                except Exception as exception:
                    source = ""
                    if request.get("operation") == "connect":
                        source = f"{request.get('source_object')}.{request.get('source_attribute')}"
                    target_rows = [self._row(source, target_plug, "blocked", str(exception))]
                for row in target_rows:
                    pair = (row["source"], row["target"])
                    if pair not in seen_pairs:
                        seen_pairs.add(pair)
                        rows.append(row)
        return rows

    def incoming_connections(self, plug):
        """Gets exact source/destination pairs, including connected children.

        Args:
            plug (str): Target plug to inspect.

        Returns:
            list: Unique source/destination plug tuples.
        """
        pairs = []
        for child_plug in self._connection_plugs(plug):
            connections = self.cmds.listConnections(
                child_plug, source=True, destination=False, plugs=True, connections=True,
            ) or []
            for destination, source in zip(connections[::2], connections[1::2]):
                pair = (source, destination)
                if pair not in pairs:
                    pairs.append(pair)
        return pairs

    def _connection_plugs(self, plug):
        """Walks existing compound children and array elements without creating them.

        Args:
            plug (str): Root attribute plug.

        Yields:
            str: Root plug and its existing descendants.
        """
        yield plug
        node, attribute_path = plug.split(".", 1)
        attribute_segment = attribute_path.rsplit(".", 1)[-1]
        attribute = attribute_segment.split("[", 1)[0]
        if self.cmds.attributeQuery(attribute, node=node, multi=True) and "[" not in attribute_segment:
            for index in self.cmds.getAttr(plug, multiIndices=True) or []:
                yield from self._connection_plugs(f"{plug}[{index}]")
            return
        for child in self.cmds.attributeQuery(attribute, node=node, listChildren=True) or []:
            yield from self._connection_plugs(f"{plug}.{child}")

    def _inspect_connect(self, request, target_plug):
        """Checks existence, access, types and existing incoming connections.

        Args:
            request (dict): Normalized connection request.
            target_plug (str): Destination plug.

        Returns:
            dict: Structured connection row.
        """
        source_plug = f"{request.get('source_object')}.{request.get('source_attribute')}"
        self._validate_plug(source_plug, "Source")
        self._validate_plug(target_plug, "Target")
        if source_plug == target_plug:
            return self._row(source_plug, target_plug, "blocked", "Cannot connect a plug to itself.")
        via = []
        if request.get("use_utility_node"):
            utility_type = request.get("utility_node_type")
            if utility_type not in ("plusMinusAverage", "multiplyDivide", "condition"):
                raise RuntimeError(f"Unsupported utility node type: {utility_type}")
            via.append(utility_type)
            if request.get("use_shared_input"):
                shared_type = request.get("shared_input_node_type")
                if shared_type not in ("plusMinusAverage", "multiplyDivide", "condition"):
                    raise RuntimeError(f"Unsupported shared input node type: {shared_type}")
        if request.get("add_reverse_node"):
            via.append("Invert (1 - input)")
        via_text = " -> ".join(via)
        if not via and self.cmds.isConnected(source_plug, target_plug, ignoreUnitConversion=True):
            return self._row(
                source_plug, target_plug, "skipped", "Already connected to this source.", via_text,
            )
        self._validate_access(source_plug, source=True)
        self._validate_access(target_plug)
        source_type = self._get_plug_type(source_plug)
        target_type = self._get_plug_type(target_plug)
        status, details = check_connection_types(
            source_type, target_type,
            use_utility=bool(request.get("use_utility_node")),
            add_reverse=bool(request.get("add_reverse_node")),
        )
        incoming = self.incoming_connections(target_plug)
        if incoming:
            for unused_source, destination in incoming:
                self._validate_access(destination)
            existing_sources = ", ".join(source for source, destination in incoming)
            if not request.get("force_connection"):
                status = "blocked"
                details = f"Existing input: {existing_sources}. Enable Replace existing connections."
            elif status != "blocked":
                status = "warning"
                details = f"Will replace: {existing_sources}. {details}".strip()
        return self._row(source_plug, target_plug, status, details, via_text)

    def _inspect_disconnect(self, target_plug):
        """Inspects actual incoming plugs and reports disconnected targets as no change.

        Args:
            target_plug (str): Target attribute whose inputs would be removed.

        Returns:
            list: Disconnection rows, or one no-change row.
        """
        self._validate_plug(target_plug, "Target")
        pairs = self.incoming_connections(target_plug)
        if not pairs:
            return [self._row("", target_plug, "skipped", "No incoming connections.")]
        rows = []
        for source, destination in pairs:
            try:
                self._validate_access(destination, disconnect=True)
                row = self._row(source, destination, "ready", "Remove incoming connection.")
            except Exception as exception:
                row = self._row(source, destination, "blocked", str(exception))
            rows.append(row)
        return rows

    def _get_plug_type(self, plug):
        """Reads types without allocating absent array elements through getAttr.

        Maya's getAttr(type=True) creates an indexed element when it is absent.
        Schema types avoid that mutation. Indexed custom typed data is reported
        conservatively as an unknown type for Maya to validate during Run.

        Args:
            plug (str): Existing or schema-valid attribute plug.

        Returns:
            str: Maya data type or an attribute schema type.
        """
        if "[" in plug:
            node, attribute_path = plug.split(".", 1)
            attribute = attribute_path.rsplit(".", 1)[-1].split("[", 1)[0]
            return self.cmds.attributeQuery(attribute, node=node, attributeType=True)
        return self.cmds.getAttr(plug, type=True)

    def _validate_plug(self, plug, label):
        """Raises when a requested plug does not exist.

        Args:
            plug (str): Maya plug name.
            label (str): Source or target label for feedback.

        Raises:
            RuntimeError: When the plug is missing.
        """
        if not self.cmds.objExists(plug):
            raise RuntimeError(f"{label} attribute does not exist: {plug}")

    def _validate_access(self, plug, source=False, disconnect=False):
        """Checks locks and attribute access without testing by connecting plugs.

        Args:
            plug (str): Maya attribute plug.
            source (bool, optional): Whether the plug is read as a source.
            disconnect (bool, optional): Whether only a disconnection is planned.

        Raises:
            RuntimeError: When the attribute cannot participate in the operation.
        """
        if not source and self.cmds.getAttr(plug, lock=True):
            raise RuntimeError(f"Target attribute is locked: {plug}")
        if disconnect:
            return
        node, attribute_path = plug.split(".", 1)
        attribute = attribute_path.rsplit(".", 1)[-1].split("[", 1)[0]
        if (self.cmds.attributeQuery(attribute, node=node, multi=True)
                and "[" not in attribute_path.rsplit(".", 1)[-1]):
            raise RuntimeError(f"Choose an explicit array element, for example {plug}[0].")
        if not self.cmds.attributeQuery(attribute, node=node, connectable=True):
            raise RuntimeError(f"Attribute does not allow connections: {plug}")
        access_flag = {"readable": True} if source else {"writable": True}
        if not self.cmds.attributeQuery(attribute, node=node, **access_flag):
            role = "readable" if source else "writable"
            raise RuntimeError(f"Attribute is not {role}: {plug}")

    @staticmethod
    def _row(source, target, status, details, via=""):
        """Builds a JSON-compatible operation row.

        Args:
            source (str): Source plug, empty for an unconnected target.
            target (str): Destination plug.
            status (str): Ready, warning, blocked or skipped status key.
            details (str): Human-readable explanation.
            via (str, optional): Planned utility chain.

        Returns:
            dict: Structured operation data.
        """
        return {"source": source, "target": target, "via": via, "status": status, "details": details}
