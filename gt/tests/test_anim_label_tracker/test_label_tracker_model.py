"""Tests for Animation Label Tracker pure model helpers."""

import json
import unittest
from types import SimpleNamespace

from gt.tools.anim_label_tracker import label_tracker_model


class TestLabelTrackerModel(unittest.TestCase):
    """Tests import-safe Animation Label Tracker behavior."""

    def test_sample_schema_is_valid_json(self):
        """Checks the packaged sample schema can be loaded."""
        with open(label_tracker_model.get_sample_schema_path(), encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        self.assertEqual("high", schema["file_level"][0]["options"][2])
        self.assertTrue(schema["validation"]["full_coverage"])

    def test_flatten_schema_items_keeps_nested_fields_in_order(self):
        """Checks row items are flattened in display order."""
        schema_items = [
            {"type": "separator"},
            {"type": "row", "items": [{"name": "first"}, {"name": "second"}]},
            {"name": "third"},
        ]

        flattened_items = label_tracker_model.flatten_schema_items(schema_items)

        self.assertEqual(["first", "second", "third"], [
            item["name"] for item in flattened_items
        ])

    def test_validation_reports_all_missing_required_values(self):
        """Checks validation returns every missing required field."""
        schema = {
            "validation": {"full_coverage": False, "allow_overlap": True},
            "file_level": [{"type": "string", "name": "source", "required": True}],
            "frame_range": [{"type": "string", "name": "state", "required": True}],
        }

        errors = label_tracker_model.collect_validation_errors(
            schema,
            [
                SimpleNamespace(
                    start=1,
                    end=10,
                    display_name="Range",
                    custom_data={},
                )
            ],
            {},
            1,
            10,
        )

        self.assertEqual(2, len(errors))
        self.assertIn("source", errors[0])
        self.assertIn("state", errors[1])

    def test_auto_crop_removes_adjacent_overlap_within_tolerance(self):
        """Checks crop mode shortens the previous adjacent range."""
        previous_range = SimpleNamespace(start=0, end=10, locked=False)
        active_range = SimpleNamespace(start=8, end=20, locked=False)

        changed_ranges = label_tracker_model.adjust_adjacent_ranges(
            active_range,
            [previous_range, active_range],
            auto_crop=True,
            crop_tolerance=3,
        )

        self.assertEqual([previous_range], changed_ranges)
        self.assertEqual(7, previous_range.end)

    def test_auto_stretch_closes_adjacent_gap_within_tolerance(self):
        """Checks stretch mode extends the previous adjacent range."""
        previous_range = SimpleNamespace(start=0, end=10, locked=False)
        active_range = SimpleNamespace(start=15, end=20, locked=False)

        changed_ranges = label_tracker_model.adjust_adjacent_ranges(
            active_range,
            [previous_range, active_range],
            auto_stretch=True,
            stretch_tolerance=4,
        )

        self.assertEqual([previous_range], changed_ranges)
        self.assertEqual(14, previous_range.end)
