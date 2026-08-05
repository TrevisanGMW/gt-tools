"""Unit tests for the pure World Space Baker model."""

import unittest

from gt.tools.world_space_baker.world_space_baker_model import WorldSpaceBakerModel


class TestWorldSpaceBakerModel(unittest.TestCase):
    """Tests session state and pure presentation helpers."""

    def test_set_targets_removes_empty_and_duplicate_values(self):
        """Stores a clean, ordered target list."""
        model = WorldSpaceBakerModel()

        result = model.set_targets(["|rig|ctrl", "", "|rig|ctrl", "|rig|other"])

        self.assertEqual(["|rig|ctrl", "|rig|other"], result)

    def test_set_targets_clears_stale_animation_data(self):
        """Invalidates extracted data when targets change."""
        model = WorldSpaceBakerModel()
        model.set_animation_data({"old": {"translate": []}})

        model.set_targets(["new"])

        self.assertEqual({}, model.animation_data)

    def test_validate_frame_range_accepts_ordered_range(self):
        """Accepts a start frame lower than the end frame."""
        model = WorldSpaceBakerModel()
        model.set_frame_range(-10, 10)

        result, message = model.validate_frame_range()

        self.assertTrue(result)
        self.assertEqual("", message)

    def test_validate_frame_range_rejects_equal_frames(self):
        """Rejects ranges without forward duration."""
        model = WorldSpaceBakerModel()
        model.set_frame_range(10, 10)

        result, message = model.validate_frame_range()

        self.assertFalse(result)
        self.assertIn("lower", message)

    def test_target_label_uses_single_target_name(self):
        """Uses the target path when exactly one target is loaded."""
        model = WorldSpaceBakerModel()
        model.set_targets(["|rig|ctrl"])

        self.assertEqual("|rig|ctrl", model.get_target_label())

    def test_stored_summary_uses_extracted_target_count(self):
        """Reports only targets that produced extracted data."""
        model = WorldSpaceBakerModel()
        model.set_frame_range(1, 24)
        model.set_animation_data({"one": {}, "two": {}})

        result = model.get_stored_summary()

        self.assertEqual("2 objects stored. Frames: 1-24", result)


if __name__ == "__main__":
    unittest.main()
