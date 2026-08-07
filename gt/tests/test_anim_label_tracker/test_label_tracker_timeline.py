"""Tests Animation Label Tracker timeline layout helpers."""

import unittest

from gt.tools.anim_label_tracker import label_tracker


class TestLabelTrackerTimeline(unittest.TestCase):
    """Tests visual lane assignment for overlapping label ranges."""

    def test_pack_range_lanes_stacks_overlapping_ranges(self):
        """Checks overlapping ranges receive separate visual lanes."""
        ranges = [
            label_tracker.RangeItem("First", 1, 10, (100, 100, 100)),
            label_tracker.RangeItem("Second", 5, 8, (100, 100, 100)),
            label_tracker.RangeItem("Third", 11, 20, (100, 100, 100)),
        ]

        expected_lanes = {0: 0, 1: 1, 2: 0}
        actual_lanes = label_tracker.pack_range_lanes(ranges)

        self.assertEqual(expected_lanes, actual_lanes)

    def test_pack_range_lanes_stacks_shared_endpoints(self):
        """Checks shared endpoint ranges remain visually distinct."""
        ranges = [
            label_tracker.RangeItem("First", 1, 10, (100, 100, 100)),
            label_tracker.RangeItem("Second", 10, 20, (100, 100, 100)),
        ]

        expected_lanes = {0: 0, 1: 1}
        actual_lanes = label_tracker.pack_range_lanes(ranges)

        self.assertEqual(expected_lanes, actual_lanes)


if __name__ == "__main__":
    unittest.main()
