"""Tests for the Create Testing Keys model."""

import unittest

from gt.tools.create_testing_keys import create_testing_keys_model as model


class MockMayaCmds:
    """Small maya.cmds substitute used by model unit tests."""

    def __init__(self):
        """Initializes mock scene data and call tracking."""
        self.values = {
            "cube.tx": 2.0,
            "cube.ty": 3.0,
            "cube.tz": 4.0,
            "cube.sx": 1.0,
            "cube.sy": 1.0,
            "cube.sz": 1.0,
        }
        self.key_calls = []
        self.set_calls = []
        self.deleted = []
        self.connections = {}

    @staticmethod
    def objExists(obj):
        """Reports whether a mock object exists.

        Args:
            obj (str): Object name.

        Returns:
            bool: True for the test cube.
        """
        return obj == "cube"

    def getAttr(self, plug, lock=False):
        """Gets a mock attribute value or lock state.

        Args:
            plug (str): Attribute plug.
            lock (bool, optional): Whether to query the lock state.

        Returns:
            float or bool: Mock attribute value or False for lock state.
        """
        if lock:
            return False
        return self.values[plug]

    def setAttr(self, plug, value):
        """Stores a mock attribute value.

        Args:
            plug (str): Attribute plug.
            value (float): New value.
        """
        self.values[plug] = value
        self.set_calls.append((plug, value))

    def setKeyframe(self, obj, **kwargs):
        """Records a mock keyframe call.

        Args:
            obj (str): Keyed object.
            **kwargs: Keyframe arguments.
        """
        self.key_calls.append((obj, kwargs))

    def listConnections(self, obj, type=None):
        """Gets mock connections by curve type.

        Args:
            obj (str): Connected object.
            type (str, optional): Requested node type.

        Returns:
            list: Connected nodes.
        """
        return self.connections.get((obj, type), [])

    def delete(self, objects):
        """Records deleted objects.

        Args:
            objects (list): Object names to delete.
        """
        self.deleted.extend(objects)


class TestCreateTestingKeysModel(unittest.TestCase):
    """Tests pure helpers and isolated Maya operation behavior."""

    def test_get_active_offsets_uses_channel_order_and_accepts_negative(self):
        """Tests valid offsets are filtered and returned deterministically."""
        expected = {"tx": -2.0, "rz": 4.5}
        result = model.get_active_offsets({"rz": 4.5, "tx": -2, "ty": "invalid"})
        self.assertEqual(expected, result)

    def test_get_offset_vector(self):
        """Tests an offset is assigned to the requested axis."""
        expected = (0.0, 3.0, 0.0)
        result = model.get_offset_vector("ry", 3)
        self.assertEqual(expected, result)

    def test_reset_offsets_returns_independent_defaults(self):
        """Tests reset replaces changed offsets with a fresh default mapping."""
        testing_model = model.CreateTestingKeysModel()
        testing_model.offsets["tx"] = 10
        expected = dict(model.DEFAULT_OFFSETS)
        result = testing_model.reset_offsets()
        self.assertEqual(expected, result)
        self.assertIsNot(model.DEFAULT_OFFSETS, testing_model.offsets)

    def test_local_attribute_test_keys_only_requested_attribute(self):
        """Tests local animation keys the requested channel at each pose."""
        mock_cmds = MockMayaCmds()
        expected_frames = [1.0, 6.0, 11.0, 16.0]
        result = model.create_attribute_test(
            selection=["cube"],
            attribute="tx",
            offset=2.0,
            interval=5.0,
            add_inverted=True,
            use_world_space=False,
            start_frame=1.0,
            cmds=mock_cmds,
        )
        keyed_attributes = [call[1]["attribute"] for call in mock_cmds.key_calls]
        keyed_frames = [call[1]["time"] for call in mock_cmds.key_calls]
        self.assertEqual(16.0, result)
        self.assertEqual(["tx", "tx", "tx", "tx"], keyed_attributes)
        self.assertEqual(expected_frames, keyed_frames)
        self.assertEqual(2.0, mock_cmds.values["cube.tx"])

    def test_scale_inverted_pose_is_relative_to_original_value(self):
        """Tests an inverted scale offset subtracts from the original scale."""
        mock_cmds = MockMayaCmds()
        model.create_attribute_test(
            selection=["cube"],
            attribute="sx",
            offset=0.25,
            interval=2.0,
            add_inverted=True,
            use_world_space=False,
            start_frame=1.0,
            cmds=mock_cmds,
        )
        sx_values = [value for plug, value in mock_cmds.set_calls if plug == "cube.sx"]
        self.assertEqual([1.25, 0.75, 1.0], sx_values)

    def test_delete_connected_keyframes_deduplicates_curves(self):
        """Tests connected animation nodes are deleted only once."""
        mock_cmds = MockMayaCmds()
        mock_cmds.connections[("cube", "animCurveTA")] = ["curve_b", "curve_a"]
        mock_cmds.connections[("cube", "animCurveTL")] = ["curve_a"]
        expected = 2
        result = model.delete_connected_keyframes(["cube"], cmds=mock_cmds)
        self.assertEqual(expected, result)
        self.assertEqual(["curve_a", "curve_b"], mock_cmds.deleted)


if __name__ == "__main__":
    unittest.main()
