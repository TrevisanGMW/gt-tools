"""Tests Animation Clip Tracker timeline helpers."""
import sys
import unittest
from unittest import mock

from gt.tools.anim_clip_tracker import clip_tracker_timeline as clip_timeline


class TestClipTrackerTimeline(unittest.TestCase):
    """Tests timeline helpers and context-menu interactions."""

    @classmethod
    def setUpClass(cls):
        """Creates the shared Qt application used by widget tests."""
        application = clip_timeline.ui_qt.QtWidgets.QApplication.instance()
        if not application:
            cls.application = clip_timeline.ui_qt.QtWidgets.QApplication(sys.argv)
        else:
            cls.application = application

    def test_get_clip_span_supports_inverted_ranges(self):
        """Checks spans are returned from lowest to highest frame."""
        self.assertEqual((10, 20), clip_timeline.get_clip_span({"start": 10, "end": 20}))
        self.assertEqual((10, 20), clip_timeline.get_clip_span({"start": 20, "end": 10}))

    def test_is_inverted_clip_detects_reversed_ranges(self):
        """Checks inverted clips are detected."""
        self.assertEqual(False, clip_timeline.is_inverted_clip({"start": 5, "end": 5}))
        self.assertEqual(True, clip_timeline.is_inverted_clip({"start": 5, "end": 4}))

    def test_get_display_bounds_includes_clips_outside_playback_range(self):
        """Checks clips outside the playback range remain visible."""
        clips = [{"start": -20, "end": 5}, {"start": 200, "end": 150}]
        low_frame, high_frame = clip_timeline.get_display_bounds(clips, 1, 100)
        self.assertEqual(True, low_frame < -20)
        self.assertEqual(True, high_frame > 200)

    def test_get_display_bounds_handles_empty_range(self):
        """Checks a zero-length playback range still produces usable bounds."""
        low_frame, high_frame = clip_timeline.get_display_bounds([], 10, 10)
        self.assertEqual(True, high_frame > low_frame)

    def test_pack_clip_lanes_stacks_overlapping_clips(self):
        """Checks overlapping clips are placed in separate lanes."""
        clips = [
            {"start": 1, "end": 20},
            {"start": 15, "end": 40},
            {"start": 41, "end": 50},
        ]
        expected = {0: 0, 1: 1, 2: 0}
        self.assertEqual(expected, clip_timeline.pack_clip_lanes(clips))

    def test_pack_clip_lanes_uses_inverted_range_span(self):
        """Checks inverted clips are packed using their real frame span."""
        clips = [{"start": 20, "end": 1}, {"start": 10, "end": 30}]
        expected = {0: 0, 1: 1}
        self.assertEqual(expected, clip_timeline.pack_clip_lanes(clips))

    def test_pack_clip_lanes_ignores_clip_list_order(self):
        """Checks clips that do not overlap share a lane even when listed out of order."""
        clips = [{"start": 100, "end": 140}, {"start": 50, "end": 70}]
        expected = {0: 0, 1: 0}
        self.assertEqual(expected, clip_timeline.pack_clip_lanes(clips))

    def test_get_lane_count_defaults_to_one_lane(self):
        """Checks the lane count of an empty timeline."""
        self.assertEqual(1, clip_timeline.get_lane_count({}))
        self.assertEqual(3, clip_timeline.get_lane_count({0: 0, 1: 2}))

    def test_get_clip_display_name_uses_user_name_when_available(self):
        """Checks named clips keep their name."""
        self.assertEqual("Walk", clip_timeline.get_clip_display_name({"start": 1, "end": 24, "name": "Walk"}))

    def test_get_clip_display_name_falls_back_to_frame_range(self):
        """Checks unnamed clips show a padded frame range."""
        self.assertEqual("f0001-f0024", clip_timeline.get_clip_display_name({"start": 1, "end": 24, "name": ""}))
        self.assertEqual("f0060-f0050", clip_timeline.get_clip_display_name({"start": 60, "end": 50, "name": "  "}))

    def test_clamp_frame_keeps_values_inside_range(self):
        """Checks frames are limited to the timeline range."""
        self.assertEqual(10, clip_timeline.clamp_frame(5, 10, 20))
        self.assertEqual(20, clip_timeline.clamp_frame(25, 10, 20))
        self.assertEqual(15, clip_timeline.clamp_frame(15, 10, 20))

    def test_get_clamped_move_delta_preserves_clip_length(self):
        """Checks move offsets stop at the range limits."""
        self.assertEqual(-5, clip_timeline.get_clamped_move_delta(-20, 15, 25, 10, 100))
        self.assertEqual(75, clip_timeline.get_clamped_move_delta(200, 15, 25, 10, 100))
        self.assertEqual(3, clip_timeline.get_clamped_move_delta(3, 15, 25, 10, 100))

    def test_get_clamped_move_delta_supports_inverted_clips(self):
        """Checks inverted clips are limited using their real span."""
        self.assertEqual(-5, clip_timeline.get_clamped_move_delta(-20, 25, 15, 10, 100))

    def test_get_clamped_move_delta_blocks_clips_longer_than_range(self):
        """Checks clips longer than the allowed range do not move."""
        self.assertEqual(0, clip_timeline.get_clamped_move_delta(10, 1, 200, 10, 100))

    def test_get_clip_color_is_stable_and_cycles(self):
        """Checks clip colors are deterministic."""
        color_count = len(clip_timeline.CLIP_COLORS)
        self.assertEqual(clip_timeline.get_clip_color(0), clip_timeline.get_clip_color(color_count))
        self.assertEqual(clip_timeline.CLIP_COLORS[1], clip_timeline.get_clip_color(1))

    def test_context_menu_set_current_frame_as_start(self):
        """Checks the start action preserves the clip end frame."""
        expected = [(0, 15, 20)]
        actual = self.get_context_menu_modified_range("Set Current Frame as Start", 15)
        self.assertEqual(expected, actual)

    def test_context_menu_set_current_frame_as_end(self):
        """Checks the end action preserves the clip start frame."""
        expected = [(0, 10, 15)]
        actual = self.get_context_menu_modified_range("Set Current Frame as End", 15)
        self.assertEqual(expected, actual)

    def get_context_menu_modified_range(self, action_label, current_frame):
        """Runs a context-menu action and captures its edited frame range.

        Args:
            action_label (str): Label of the action to trigger.
            current_frame (int): Current timeline frame.

        Returns:
            list: Ranges emitted by the timeline widget.
        """
        timeline_widget = clip_timeline.ClipTimelineWidget()
        timeline_widget.set_clips([{"start": 10, "end": 20}])
        timeline_widget.set_frame_state(1, 100, current_frame)
        emitted_ranges = []
        timeline_widget.clip_modified.connect(
            lambda index, start, end: emitted_ranges.append((index, start, end))
        )
        with mock.patch.object(
            clip_timeline,
            "execute_menu",
            side_effect=lambda menu, position: next(
                action for action in menu.actions() if action.text() == action_label
            ),
        ):
            timeline_widget.show_context_menu(mock.MagicMock(), 0)
        timeline_widget.close()
        return emitted_ranges


if __name__ == "__main__":
    unittest.main()
