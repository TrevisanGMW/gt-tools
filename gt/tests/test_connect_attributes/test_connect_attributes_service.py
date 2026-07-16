"""Unit tests for Connect Attributes Maya service mappings."""

import unittest

from gt.tools.connect_attributes.connect_attributes_service import ConnectAttributesService


class MockMayaCmds:
    """Minimal maya.cmds test double for direct operations."""

    def __init__(self):
        """Initializes fake scene state and call recording."""
        self.existing = {"source.output", "target.input"}
        self.connections = []
        self.disconnections = []
        self.undo_calls = []
        self.deleted = []

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
        return "double"

    def connectionInfo(self, plug, **kwargs):
        """Reports no existing destination connection.

        Args:
            plug (str): Requested plug.
            **kwargs: Maya command flags.

        Returns:
            bool: Always False.
        """
        return False

    def connectAttr(self, source, target, **kwargs):
        """Records a connection.

        Args:
            source (str): Source plug.
            target (str): Target plug.
            **kwargs: Maya command flags.
        """
        self.connections.append((source, target, kwargs))

    def listConnections(self, plug, **kwargs):
        """Returns one incoming source plug.

        Args:
            plug (str): Target plug.
            **kwargs: Maya command flags.

        Returns:
            list: Fake incoming plug.
        """
        return [plug, "driver.output"]

    def disconnectAttr(self, source, target):
        """Records a disconnection.

        Args:
            source (str): Source plug.
            target (str): Target plug.
        """
        self.disconnections.append((source, target))

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


if __name__ == "__main__":
    unittest.main()
