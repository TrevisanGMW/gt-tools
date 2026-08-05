"""Tests Animation Clip Tracker timeline mode constants."""
import unittest

from gt.tools.anim_clip_tracker import clip_tracker_constants as clip_constants


class TestClipTrackerConstants(unittest.TestCase):
    """Tests the pure timeline mode helpers."""

    def test_timeline_modes_order_is_stable(self):
        """Checks the mode order used by the preferences radio buttons."""
        expected = ["navigate", "select", "edit"]
        self.assertEqual(expected, clip_constants.TIMELINE_MODES)

    def test_get_valid_mode_falls_back_to_default(self):
        """Checks unknown modes resolve to the default mode."""
        self.assertEqual("edit", clip_constants.get_valid_mode("bogus"))
        self.assertEqual("select", clip_constants.get_valid_mode("select"))

    def test_get_mode_index_matches_radio_button_positions(self):
        """Checks modes convert to one-based radio button indices."""
        self.assertEqual(1, clip_constants.get_mode_index("navigate"))
        self.assertEqual(2, clip_constants.get_mode_index("select"))
        self.assertEqual(3, clip_constants.get_mode_index("edit"))
        self.assertEqual(3, clip_constants.get_mode_index(None))

    def test_get_mode_from_index_handles_out_of_range_values(self):
        """Checks out of range indices resolve to the default mode."""
        self.assertEqual("navigate", clip_constants.get_mode_from_index(1))
        self.assertEqual("edit", clip_constants.get_mode_from_index(0))
        self.assertEqual("edit", clip_constants.get_mode_from_index(9))

    def test_get_mode_label_returns_user_facing_names(self):
        """Checks mode labels used by the preferences UI."""
        self.assertEqual("Navigate", clip_constants.get_mode_label("navigate"))
        self.assertEqual("", clip_constants.get_mode_label("bogus"))


if __name__ == "__main__":
    unittest.main()
