"""Tests for stable table column resizing and Qt scaling environment cleanup."""

import unittest

from gt.tools.batch_processor.tracker import tracker_columns
from gt.tools.batch_processor.tracker import tracker_process_utils


class TestColumnDistribution(unittest.TestCase):
    """Checks column widths keep their proportions and never drift."""

    def test_widths_follow_ratios_and_fill_the_total(self):
        ratios = tracker_columns.capture_column_ratios([100, 300, 600])
        expected = [150, 450, 900]
        self.assertEqual(expected, tracker_columns.distribute_column_widths(ratios, 1500, 48))

    def test_repeated_resizing_returns_to_the_same_widths(self):
        ratios = tracker_columns.capture_column_ratios([52, 250, 140, 85, 62, 135, 72, 145, 145, 82])
        original = tracker_columns.distribute_column_widths(ratios, 1200, 48)
        for width in (900, 640, 1500, 777, 1013, 1200):
            result = tracker_columns.distribute_column_widths(ratios, width, 48)
        self.assertEqual(original, result)

    def test_total_matches_the_viewport_even_with_rounding(self):
        ratios = tracker_columns.capture_column_ratios([1, 1, 1])
        self.assertEqual(1000, sum(tracker_columns.distribute_column_widths(ratios, 1000, 10)))

    def test_narrow_columns_are_pinned_to_the_minimum(self):
        ratios = tracker_columns.capture_column_ratios([10, 500, 500])
        widths = tracker_columns.distribute_column_widths(ratios, 400, 48)
        self.assertEqual((48, 400), (widths[0], sum(widths)))

    def test_no_columns_gives_no_widths(self):
        self.assertEqual([], tracker_columns.distribute_column_widths([], 400, 48))


class TestQtScalingEnvironment(unittest.TestCase):
    """Checks inherited Qt scaling overrides are removed."""

    def test_scaling_variables_are_removed_and_others_kept(self):
        environment = {"QT_ENABLE_HIGHDPI_SCALING": "0", "QT_SCALE_FACTOR": "1", "PATH": "x"}
        removed = tracker_process_utils.remove_qt_scaling_variables(environment)
        self.assertEqual(({"PATH": "x"}, ["QT_ENABLE_HIGHDPI_SCALING", "QT_SCALE_FACTOR"]), (environment, removed))
