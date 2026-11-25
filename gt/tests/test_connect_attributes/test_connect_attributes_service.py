"""Unit tests for Connect Attributes Maya service mappings."""

import unittest

from gt.tools.connect_attributes.connect_attributes_service import ConnectAttributesService
from gt.tools.connect_attributes.connect_attributes_validation import check_connection_types


class MockMayaCmds:
    """Minimal maya.cmds test double for direct operations."""

    def __init__(self):
        """Initializes fake scene state and call recording."""
        self.existing = {"source.output", "target.input"}
        self.connections = []
        self.disconnections = []
        self.undo_calls = []
        self.deleted = []
        self.incoming = {}
        self.types = {}
        self.locked = set()
        self.not_connectable = set()
        self.not_readable = set()
        self.not_writable = set()
        self.created = []
        self.children = {}
        self.multi_indices = {}

    def undoInfo(self, **kwargs):
        """Records undo chunk calls.

        Args:
            **kwargs: Maya command flags.
        """
        self.undo_calls.append(kwargs)

    def objExists(self, item):
        """Checks fake scene existence.

        Args:
            item (str): Node or plug.

        Returns:
            bool: True when registered.
        """
        return item in self.existing

    def getAttr(self, plug, **kwargs):
        """Returns a scalar test type.

        Args:
            plug (str): Requested plug.
            **kwargs: Maya command flags.

        Returns:
            str: Fake attribute type.
        """
        if kwargs.get("lock"):
            return plug in self.locked
        if kwargs.get("multiIndices"):
            return self.multi_indices.get(plug, [])
        return self.types.get(plug, "double")

    def attributeQuery(self, attribute, node, **kwargs):
        """Returns configured attribute access flags.

        Args:
            attribute (str): Attribute name.
            node (str): Owner node.
            **kwargs: Requested access flag.

        Returns:
            bool: Whether the attribute permits the requested access.
        """
        plug = f"{node}.{attribute}"
        if kwargs.get("listChildren"):
            return self.children.get(plug, [])
        if kwargs.get("multi"):
            return plug in self.multi_indices
        if kwargs.get("attributeType"):
            return self.types.get(plug, "double")
        denied = self.not_connectable
        if kwargs.get("readable"):
            denied = self.not_readable
        elif kwargs.get("writable"):
            denied = self.not_writable
        return plug not in denied

    def isConnected(self, source, target, **kwargs):
        """Reports whether the configured source already drives the target.

        Args:
            source (str): Source plug.
            target (str): Target plug.
            **kwargs: Ignored Maya flags.

        Returns:
            bool: Whether the exact pair is connected.
        """
        return self.incoming.get(target) == [target, source]

    def createNode(self, node_type):
        """Records utility creation for cleanup and no-mutation assertions.

        Args:
            node_type (str): Requested Maya node type.

        Returns:
            str: Unique fake utility node name.
        """
        name = f"{node_type}{len(self.created) + 1}"
        self.created.append(name)
        return name

    def connectionInfo(self, plug, **kwargs):
        """Reports no existing destination connection.

        Args:
            plug (str): Requested plug.
            **kwargs: Maya command flags.

        Returns:
            bool: Always False.
        """
        return bool(self.incoming.get(plug))

    def connectAttr(self, source, target, **kwargs):
        """Records a connection.

        Args:
            source (str): Source plug.
            target (str): Target plug.
            **kwargs: Maya command flags.
        """
        self.connections.append((source, target, kwargs))
        self.incoming[target] = [target, source]

    def listConnections(self, plug, **kwargs):
        """Returns one incoming source plug.

        Args:
            plug (str): Target plug.
            **kwargs: Maya command flags.

        Returns:
            list: Fake incoming plug.
        """
        return self.incoming.get(plug, [])

    def disconnectAttr(self, source, target):
        """Records a disconnection.

        Args:
            source (str): Source plug.
            target (str): Target plug.
        """
        self.disconnections.append((source, target))
        for plug, connections in self.incoming.items():
            remaining = []
            for destination, incoming_source in zip(connections[::2], connections[1::2]):
                if (source, target) != (incoming_source, destination):
                    remaining.extend([destination, incoming_source])
            self.incoming[plug] = remaining

    def delete(self, nodes):
        """Records deleted nodes.

        Args:
            nodes (str or list): Nodes being deleted.
        """
        self.deleted.append(nodes)


class TestConnectAttributesService(unittest.TestCase):
    """Tests service behavior without importing Maya."""

    def test_get_node_plug_returns_scalar_mapping(self):
        """Returns the expected scalar plusMinusAverage secondary input."""
        result = ConnectAttributesService.get_node_plug(
            "plusMinusAverage", "secondary", is_vector=False
        )

        expected = "input1D[1]"
        self.assertEqual(expected, result)

    def test_get_node_plug_returns_vector_mapping(self):
        """Returns the expected vector condition output."""
        result = ConnectAttributesService.get_node_plug("condition", "output", is_vector=True)

        expected = "outColor"
        self.assertEqual(expected, result)

    def test_execute_direct_connection(self):
        """Connects the requested source and target plugs in an undo chunk."""
        cmds = MockMayaCmds()
        service = ConnectAttributesService(cmds_module=cmds)
        request = {
            "operation": "connect",
            "source_object": "source",
            "source_attribute": "output",
            "target_objects": ["target"],
            "target_attributes": ["input"],
            "force_connection": False,
            "use_utility_node": False,
            "add_reverse_node": False,
        }

        result = service.execute(request)

        self.assertEqual(1, result.get("succeeded"))
        self.assertEqual([], result.get("errors"))
        self.assertEqual(("source.output", "target.input", {"force": False}), cmds.connections[0])
        self.assertEqual(2, len(cmds.undo_calls))

    def test_execute_disconnects_exact_target_plug(self):
        """Disconnects incoming connections only from the requested target plug."""
        cmds = MockMayaCmds()
        cmds.incoming["target.input"] = ["target.input", "driver.output"]
        service = ConnectAttributesService(cmds_module=cmds)
        request = {
            "operation": "disconnect",
            "target_objects": ["target"],
            "target_attributes": ["input"],
        }

        result = service.execute(request)

        self.assertEqual(1, result.get("succeeded"))
        self.assertEqual([("driver.output", "target.input")], cmds.disconnections)

    def test_unsupported_node_type_raises(self):
        """Rejects utility node types that have no known plug mapping."""
        with self.assertRaises(ValueError):
            ConnectAttributesService.get_node_plug("unknown", "input", is_vector=False)


class TestConnectAttributesInspection(unittest.TestCase):
    """Checks that Preview and Run share read-only preflight behavior."""

    def setUp(self):
        """Creates a scalar connection request and fake scene."""
        self.cmds = MockMayaCmds()
        self.service = ConnectAttributesService(cmds_module=self.cmds)
        self.request = {
            "operation": "connect", "source_object": "source", "source_attribute": "output",
            "target_objects": ["target"], "target_attributes": ["input"],
        }

    def test_inspection_leaves_scene_unchanged(self):
        """Inspects utility chains without creating nodes or opening undo chunks."""
        self.request.update(
            use_utility_node=True, utility_node_type="multiplyDivide", use_shared_input=True,
            shared_input_node_type="condition", add_reverse_node=True,
        )
        rows = self.service.inspect(self.request)
        self.assertEqual("ready", rows[0]["status"])
        self.assertEqual("multiplyDivide -> Invert (1 - input)", rows[0]["via"])
        self.assertEqual([], self.cmds.created)
        self.assertEqual([], self.cmds.connections)
        self.assertEqual([], self.cmds.undo_calls)

    def test_missing_attribute_blocks_preview_and_run(self):
        """Reports missing attributes without creating any utility nodes."""
        self.cmds.existing.remove("target.input")
        self.request.update(
            use_utility_node=True, utility_node_type="multiplyDivide", use_shared_input=True,
            shared_input_node_type="condition",
        )
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])
        result = self.service.execute(self.request)
        self.assertEqual(0, result["succeeded"])
        self.assertEqual(1, len(result["errors"]))
        self.assertEqual([], self.cmds.created)
        self.assertEqual([], self.cmds.undo_calls)

    def test_run_rechecks_lock_after_preview(self):
        """Rejects a target locked after a ready preview snapshot."""
        self.assertEqual("ready", self.service.inspect(self.request)[0]["status"])
        self.cmds.locked.add("target.input")
        result = self.service.execute(self.request)
        self.assertEqual(0, result["succeeded"])
        self.assertIn("locked", result["errors"][0])
        self.assertEqual([], self.cmds.connections)

    def test_existing_input_requires_explicit_replacement(self):
        """Identifies the existing driver and only allows replacement when enabled."""
        self.cmds.incoming["target.input"] = ["target.input", "other.output"]
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])
        self.request["force_connection"] = True
        row = self.service.inspect(self.request)[0]
        self.assertEqual("warning", row["status"])
        self.assertIn("Will replace: other.output", row["details"])
        result = self.service.execute(self.request)
        self.assertEqual(1, result["succeeded"])
        self.assertEqual(True, self.cmds.connections[0][2]["force"])

    def test_same_direct_connection_is_no_change(self):
        """Skips an existing identical connection, even if its target is locked."""
        self.cmds.incoming["target.input"] = ["target.input", "source.output"]
        self.cmds.locked.add("target.input")
        self.assertEqual("skipped", self.service.inspect(self.request)[0]["status"])
        result = self.service.execute(self.request)
        self.assertEqual(1, result["skipped"])
        self.assertEqual([], result["errors"])
        self.assertEqual([], self.cmds.undo_calls)

    def test_numeric_units_are_compatible(self):
        """Allows Maya numeric conversions between float and angle attributes."""
        self.cmds.types.update({"source.output": "float", "target.input": "doubleAngle"})
        self.assertEqual("ready", self.service.inspect(self.request)[0]["status"])

    def test_vector_to_scalar_is_blocked(self):
        """Detects dimensional mismatches before attempting a connection."""
        self.cmds.types["source.output"] = "double3"
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])
        self.assertEqual(0, self.service.execute(self.request)["succeeded"])

    def test_unknown_custom_types_are_warnings(self):
        """Leaves custom type conversion to Maya instead of falsely blocking it."""
        self.cmds.types["source.output"] = "pluginData"
        self.assertEqual("warning", self.service.inspect(self.request)[0]["status"])

    def test_unconnectable_source_is_blocked(self):
        """Rejects attributes whose connectable flag is false."""
        self.cmds.not_connectable.add("source.output")
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])

    def test_unreadable_source_and_unwritable_target_are_blocked(self):
        """Checks attribute access in addition to lock and type state."""
        self.cmds.not_readable.add("source.output")
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])
        self.cmds.not_readable.clear()
        self.cmds.not_writable.add("target.input")
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])

    def test_blocked_rows_do_not_prevent_other_valid_operations(self):
        """Preserves per-target execution and reports failed targets explicitly."""
        self.cmds.existing.add("other.input")
        self.cmds.locked.add("target.input")
        self.request["target_objects"] = ["target", "other"]
        result = self.service.execute(self.request)
        self.assertEqual(1, result["succeeded"])
        self.assertEqual(1, len(result["errors"]))
        self.assertEqual("other.input", self.cmds.connections[0][1])

    def test_disconnect_reports_actual_child_pairs_without_duplicates(self):
        """Lists compound inputs precisely and deduplicates overlapping requests."""
        self.request.update(operation="disconnect", target_attributes=["input", "inputX"])
        self.cmds.existing.add("target.inputX")
        self.cmds.incoming["target.input"] = ["target.inputX", "driver.output"]
        self.cmds.incoming["target.inputX"] = ["target.inputX", "driver.output"]
        rows = self.service.inspect(self.request)
        self.assertEqual(1, len(rows))
        self.assertEqual("target.inputX", rows[0]["target"])
        result = self.service.execute(self.request)
        self.assertEqual(1, result["succeeded"])
        self.assertEqual([("driver.output", "target.inputX")], self.cmds.disconnections)

    def test_disconnect_finds_inputs_on_compound_children(self):
        """Inspects child plugs when Maya returns no connections for their parent."""
        self.request.update(operation="disconnect", target_attributes=["input"])
        self.cmds.children["target.input"] = ["inputX"]
        self.cmds.incoming["target.input.inputX"] = ["target.inputX", "driver.output"]
        rows = self.service.inspect(self.request)
        self.assertEqual(1, len(rows))
        self.assertEqual("target.inputX", rows[0]["target"])
        self.assertEqual("ready", rows[0]["status"])

    def test_array_root_requires_an_element_for_connect(self):
        """Does not present an unindexed multi attribute as a valid destination."""
        self.cmds.multi_indices["target.input"] = []
        row = self.service.inspect(self.request)[0]
        self.assertEqual("blocked", row["status"])
        self.assertIn("explicit array element", row["details"])

    def test_disconnected_target_is_no_change(self):
        """Skips unconnected targets without opening an undo chunk."""
        self.request["operation"] = "disconnect"
        self.assertEqual("skipped", self.service.inspect(self.request)[0]["status"])
        self.assertEqual(1, self.service.execute(self.request)["skipped"])
        self.assertEqual([], self.cmds.undo_calls)

    def test_locked_disconnect_is_blocked(self):
        """Checks the actual incoming destination before disconnecting it."""
        self.request["operation"] = "disconnect"
        self.cmds.incoming["target.input"] = ["target.input", "driver.output"]
        self.cmds.locked.add("target.input")
        self.assertEqual("blocked", self.service.inspect(self.request)[0]["status"])
        self.assertEqual(0, self.service.execute(self.request)["succeeded"])
        self.assertEqual([], self.cmds.disconnections)


class TestConnectionTypeValidation(unittest.TestCase):
    """Checks pure type rules independently of Maya or Qt."""

    def test_supported_numeric_conversions(self):
        """Allows scalar numeric conversions and vectors of the same dimension."""
        for source, target in (("enum", "bool"), ("time", "double"), ("double3", "float3")):
            with self.subTest(source=source, target=target):
                self.assertEqual(("ready", ""), check_connection_types(source, target))

    def test_known_incompatible_data(self):
        """Rejects known numeric, message and typed-data mismatches."""
        for source, target in (("message", "double"), ("string", "double"), ("double3", "double2")):
            with self.subTest(source=source, target=target):
                self.assertEqual("blocked", check_connection_types(source, target)[0])

    def test_same_typed_data_is_allowed(self):
        """Allows exact supported typed data such as message or matrix plugs."""
        for data_type in ("message", "matrix", "mesh", "string"):
            with self.subTest(data_type=data_type):
                self.assertEqual(("ready", ""), check_connection_types(data_type, data_type))

    def test_utility_requires_numeric_scalar_or_vector3(self):
        """Rejects typed data and two-component vectors for the supported chains."""
        for data_type in ("string", "double2", "matrix"):
            with self.subTest(data_type=data_type):
                self.assertEqual("blocked", check_connection_types(data_type, data_type, True)[0])


if __name__ == "__main__":
    unittest.main()
