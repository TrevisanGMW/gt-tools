"""Tests Animation Label Tracker view formatting helpers."""

import unittest

from gt.tools.anim_label_tracker.label_tracker_view import AnimationLabelTrackerView


class TestLabelTrackerView(unittest.TestCase):
    """Tests import-safe Animation Label Tracker view helpers."""

    def test_validation_report_separates_sections_only(self):
        """Checks validation issues stay grouped without extra issue spacing."""
        errors = [
            "Overlap detected between 'First' and 'Second'",
            "Timeline has 10 uncovered frame(s).",
            "File 'Quality' is required.",
            "Range 'First': 'State' is required.",
            "Range 'First': 'Style' is required.",
        ]
        expected_report = (
            "Validation Issues (5)\n\n"
            "Timeline\n"
            "- Overlap detected between 'First' and 'Second'\n"
            "- Timeline has 10 uncovered frame(s).\n\n"
            "File Data\n"
            "- File 'Quality' is required.\n\n"
            "Range 'First'\n"
            "- Range 'First': 'State' is required.\n"
            "- Range 'First': 'Style' is required."
        )

        actual_report = AnimationLabelTrackerView._format_validation_report(
            None, errors
        )

        self.assertEqual(expected_report, actual_report)
