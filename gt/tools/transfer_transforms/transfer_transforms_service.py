"""Maya scene operations for Transfer Transforms."""


class TransferTransformsService:
    """Executes transform operations using ``maya.cmds``."""

    def __init__(self, cmds_module=None):
        """Initializes the service.

        Args:
            cmds_module (module, optional): Injected ``maya.cmds`` replacement.
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
            list: Selected long node names.
        """
        return self._get_cmds().ls(selection=True, long=True) or []

    def transfer(self, source, targets, transform_options, chunk_name="Transfer Transforms"):
        """Transfers enabled values from one source to multiple targets.

        Args:
            source (str): Source node.
            targets (list): Target nodes.
            transform_options (list): Channel option dictionaries.
            chunk_name (str, optional): Maya undo chunk label.

        Returns:
            dict: Succeeded count and per-plug errors.
        """
        cmds = self._get_cmds()
        result = {"succeeded": 0, "errors": []}
        cmds.undoInfo(openChunk=True, chunkName=chunk_name)
        try:
            self._transfer_values(source, targets, transform_options, result)
            return result
        finally:
            cmds.undoInfo(closeChunk=True, chunkName=chunk_name)

    def transfer_pairs(self, pairs, source_side, transform_options):
        """Transfers multiple side pairs in a single undo chunk.

        Args:
            pairs (list): ``(left_node, right_node)`` pairs.
            source_side (str): ``left`` or ``right``.
            transform_options (list): Channel option dictionaries.

        Returns:
            dict: Succeeded count and per-plug errors.
        """
        cmds = self._get_cmds()
        result = {"succeeded": 0, "errors": []}
        cmds.undoInfo(openChunk=True, chunkName="Side-to-Side Transfer")
        try:
            for left_node, right_node in pairs:
                source = right_node if source_side == "right" else left_node
                target = left_node if source_side == "right" else right_node
                self._transfer_values(source, [target], transform_options, result)
            return result
        finally:
            cmds.undoInfo(closeChunk=True, chunkName="Side-to-Side Transfer")

    def get_values(self, source, transform_options):
        """Gets enabled transform values from a source.

        Args:
            source (str): Source node.
            transform_options (list): Channel option dictionaries.

        Returns:
            tuple: Attribute values and per-plug errors.
        """
        cmds = self._get_cmds()
        values = {}
        errors = []
        for option in transform_options:
            if not option.get("enabled"):
                continue
            attribute = option.get("attribute")
            try:
                values[attribute] = cmds.getAttr(f"{source}.{attribute}")
            except Exception as exception:
                errors.append(f"{source}.{attribute}: {exception}")
        return values, errors

    def set_values(self, targets, values, transform_options):
        """Sets session clipboard values on target nodes.

        Args:
            targets (list): Target nodes.
            values (dict): Attribute-to-value mapping.
            transform_options (list): Channel option dictionaries.

        Returns:
            dict: Succeeded count and per-plug errors.
        """
        cmds = self._get_cmds()
        result = {"succeeded": 0, "errors": []}
        cmds.undoInfo(openChunk=True, chunkName="Set Transforms")
        try:
            for option in transform_options:
                if not option.get("enabled"):
                    continue
                attribute = option.get("attribute")
                value = float(values.get(attribute, 0.0))
                if option.get("inverted"):
                    value *= -1
                for target in targets:
                    self._set_value(target, attribute, value, result)
            return result
        finally:
            cmds.undoInfo(closeChunk=True, chunkName="Set Transforms")

    def collect_records(self, nodes):
        """Collects TRS compound values for export.

        Args:
            nodes (list): Maya nodes to inspect.

        Returns:
            list: JSON-compatible transform records.
        """
        cmds = self._get_cmds()
        records = []
        for node in nodes:
            records.append(
                {
                    "long_name": node,
                    "short_name": str(node).rsplit("|", 1)[-1],
                    "translate": list(cmds.getAttr(f"{node}.translate")[0]),
                    "rotate": list(cmds.getAttr(f"{node}.rotate")[0]),
                    "scale": list(cmds.getAttr(f"{node}.scale")[0]),
                }
            )
        return records

    def apply_records(self, records):
        """Applies imported transform records to existing nodes.

        Args:
            records (list): Transform records from the model.

        Returns:
            dict: Succeeded count, missing nodes, and per-plug errors.
        """
        cmds = self._get_cmds()
        result = {"succeeded": 0, "missing": [], "errors": []}
        prepared_records = []
        for record in records:
            prepared_records.append((record, self._record_channel_values(record)))
        cmds.undoInfo(openChunk=True, chunkName="Import Transforms")
        try:
            for record, channel_values in prepared_records:
                long_name = record.get("long_name")
                short_name = record.get("short_name")
                target = long_name if cmds.objExists(long_name) else short_name
                if not target or not cmds.objExists(target):
                    result["missing"].append(short_name or long_name or "<unnamed>")
                    continue
                for attribute, value in channel_values.items():
                    self._set_value(target, attribute, value, result)
            return result
        finally:
            cmds.undoInfo(closeChunk=True, chunkName="Import Transforms")

    @staticmethod
    def _record_channel_values(record):
        """Flattens one record's TRS vectors into channels.

        Args:
            record (dict): Imported transform record.

        Returns:
            dict: Attribute-to-value mapping.

        Raises:
            ValueError: When a transform vector is invalid.
        """
        values = {}
        for prefix, key in (("t", "translate"), ("r", "rotate"), ("s", "scale")):
            vector = record.get(key)
            if not isinstance(vector, (list, tuple)) or len(vector) != 3:
                raise ValueError(f'Invalid "{key}" data for {record.get("short_name", "object")}')
            for axis, value in zip(("x", "y", "z"), vector):
                values[f"{prefix}{axis}"] = float(value)
        return values

    def _set_value(self, target, attribute, value, result):
        """Sets one unlocked transform value and updates a result dictionary.

        Args:
            target (str): Target node.
            attribute (str): Transform channel.
            value (float): Value to apply.
            result (dict): Mutable operation result.
        """
        cmds = self._get_cmds()
        plug = f"{target}.{attribute}"
        try:
            if cmds.getAttr(plug, lock=True):
                result["errors"].append(f"{plug}: attribute is locked")
                return
            cmds.setAttr(plug, value)
            result["succeeded"] += 1
        except Exception as exception:
            result["errors"].append(f"{plug}: {exception}")

    def _transfer_values(self, source, targets, transform_options, result):
        """Transfers channel values without managing an undo chunk.

        Args:
            source (str): Source node.
            targets (list): Target nodes.
            transform_options (list): Channel option dictionaries.
            result (dict): Mutable operation result.
        """
        cmds = self._get_cmds()
        for option in transform_options:
            if not option.get("enabled"):
                continue
            attribute = option.get("attribute")
            try:
                value = cmds.getAttr(f"{source}.{attribute}")
                if option.get("inverted"):
                    value *= -1
            except Exception as exception:
                result["errors"].append(f"{source}.{attribute}: {exception}")
                continue
            for target in targets:
                self._set_value(target, attribute, value, result)
