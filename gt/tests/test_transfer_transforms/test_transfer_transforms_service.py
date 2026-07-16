"""Unit tests for Transfer Transforms Maya service logic."""

import unittest

from gt.tools.transfer_transforms.transfer_transforms_service import TransferTransformsService


class MockCmds:
    """Minimal maya.cmds test double for channel operations."""

    def __init__(self):
        """Initializes mock attributes and call tracking."""
        self.attributes = {}
        self.locked = set()
        self.set_calls = []
        self.undo_calls = []

    def getAttr(self, plug, lock=False):
        """Gets a mock attribute or lock state.

        Args:
            plug (str): Maya plug.
            lock (bool, optional): Whether to query lock state.

        Returns:
            object: Stored value or lock state.
        """
        if lock:
            return plug in self.locked
        return self.attributes[plug]

    def setAttr(self, plug, value):
        """Stores a mock attribute value.

        Args:
            plug (str): Maya plug.
            value (float): Value to store.
        """
        self.attributes[plug] = value
        self.set_calls.append((plug, value))

    def undoInfo(self, **kwargs):
        """Records an undo chunk call.

        Args:
            **kwargs: Maya undoInfo arguments.
        """
        self.undo_calls.append(kwargs)


class TestTransferTransformsService(unittest.TestCase):
    """Tests service behavior with an injected maya.cmds replacement."""

    def test_transfer_applies_enabled_and_inverted_value(self):
        """Applies enabled channels and negates inverted channels."""
        cmds = MockCmds()
        cmds.attributes["source.tx"] = 4.5
        service = TransferTransformsService(cmds_module=cmds)
        options = [{"attribute": "tx", "enabled": True, "inverted": True}]

        result = service.transfer("source", ["targetA", "targetB"], options)

        expected_calls = [("targetA.tx", -4.5), ("targetB.tx", -4.5)]
        self.assertEqual(expected_calls, cmds.set_calls)
        self.assertEqual(2, result.get("succeeded"))

    def test_transfer_skips_locked_target_and_continues(self):
        """Reports a locked channel without stopping other targets."""
        cmds = MockCmds()
        cmds.attributes["source.ry"] = 25.0
        cmds.locked.add("targetA.ry")
        service = TransferTransformsService(cmds_module=cmds)
        options = [{"attribute": "ry", "enabled": True, "inverted": False}]

        result = service.transfer("source", ["targetA", "targetB"], options)

        self.assertEqual([("targetB.ry", 25.0)], cmds.set_calls)
        self.assertEqual(1, result.get("succeeded"))
        self.assertEqual(1, len(result.get("errors")))

    def test_set_values_ignores_disabled_channels(self):
        """Does not set clipboard channels disabled in the options."""
        cmds = MockCmds()
        service = TransferTransformsService(cmds_module=cmds)
        options = [
            {"attribute": "tx", "enabled": False, "inverted": False},
            {"attribute": "sx", "enabled": True, "inverted": False},
        ]

        result = service.set_values(["target"], {"tx": 8.0, "sx": 2.0}, options)

        self.assertEqual([("target.sx", 2.0)], cmds.set_calls)
        self.assertEqual(1, result.get("succeeded"))

    def test_transfer_pairs_uses_one_undo_chunk(self):
        """Transfers all name pairs as one undoable user action."""
        cmds = MockCmds()
        cmds.attributes["R_arm.tx"] = 3.0
        cmds.attributes["R_leg.tx"] = 7.0
        service = TransferTransformsService(cmds_module=cmds)
        options = [{"attribute": "tx", "enabled": True, "inverted": False}]

        result = service.transfer_pairs(
            [("L_arm", "R_arm"), ("L_leg", "R_leg")],
            source_side="right",
            transform_options=options,
        )

        expected_calls = [("L_arm.tx", 3.0), ("L_leg.tx", 7.0)]
        self.assertEqual(expected_calls, cmds.set_calls)
        self.assertEqual(2, result.get("succeeded"))
        self.assertEqual(2, len(cmds.undo_calls))

    def test_record_channel_values_flattens_trs_vectors(self):
        """Converts serialized vectors into Maya short channels."""
        record = {
            "translate": [1, 2, 3],
            "rotate": [4, 5, 6],
            "scale": [7, 8, 9],
        }

        result = TransferTransformsService._record_channel_values(record)

        expected = {
            "tx": 1.0,
            "ty": 2.0,
            "tz": 3.0,
            "rx": 4.0,
            "ry": 5.0,
            "rz": 6.0,
            "sx": 7.0,
            "sy": 8.0,
            "sz": 9.0,
        }
        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
