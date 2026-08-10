"""Tests for Animation Label Tracker pure model helpers."""

import json
import os
import unittest
from types import SimpleNamespace

from gt.tools.anim_label_tracker import label_tracker_model


class TestLabelTrackerModel(unittest.TestCase):
    """Tests import-safe Animation Label Tracker behavior."""

    def test_default_preferences_leave_automation_folder_empty(self):
        """Checks automations require an explicit user-selected folder."""
        preferences = label_tracker_model.get_default_preferences()

        self.assertEqual("", preferences["automation_path"])

    def test_default_preferences_show_the_timeline(self):
        """Checks the timeline remains visible until a user hides it."""
        preferences = label_tracker_model.get_default_preferences()

        self.assertTrue(preferences["show_timeline"])

    def test_empty_automation_path_is_omitted_from_saved_preferences(self):
        """Checks an automation folder is only saved after it is configured."""
        model = label_tracker_model.AnimationLabelTrackerModel.__new__(
            label_tracker_model.AnimationLabelTrackerModel
        )
        saved_preferences = []
        model.prefs = SimpleNamespace(
            set_raw_preferences=saved_preferences.append,
            save=lambda: None,
        )
        model.preferences = label_tracker_model.get_default_preferences()

        model.save_preferences()

        self.assertNotIn("automation_path", saved_preferences[-1])
        self.assertNotIn(
            label_tracker_model.AUTOMATION_CHECK_STATES_KEY,
            saved_preferences[-1],
        )

        model.preferences["automation_path"] = os.path.join("scripts", "automations")
        model.save_preferences()

        self.assertEqual(
            model.preferences["automation_path"],
            saved_preferences[-1]["automation_path"],
        )

    def test_sample_schema_is_valid_json(self):
        """Checks the packaged sample schema can be loaded."""
        with open(label_tracker_model.get_sample_schema_path(), encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        self.assertEqual("high", schema["file_level"][0]["options"][2])
        self.assertTrue(schema["validation"]["full_coverage"])

    def test_sample_schema_contains_commercial_and_gender_fields(self):
        """Checks the example file metadata fields and gender options."""
        with open(label_tracker_model.get_sample_schema_path(), encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        file_fields = label_tracker_model.flatten_schema_items(schema["file_level"])
        self.assertEqual(
            ["quality", "source", "gender", "clipped", "labelled", "commercial_use"],
            [field["name"] for field in file_fields],
        )
        commercial_field = next(
            field for field in file_fields if field["name"] == "commercial_use"
        )
        gender_field = next(field for field in file_fields if field["name"] == "gender")
        self.assertEqual("boolean", commercial_field["type"])
        self.assertTrue(commercial_field["required"])
        self.assertEqual("enum", gender_field["type"])
        self.assertFalse(gender_field["required"])
        self.assertNotIn("default", gender_field)
        self.assertEqual(["male", "female"], gender_field["options"])

    def test_last_used_data_is_stored_as_a_copy(self):
        """Checks last-used data is isolated from caller mutations."""
        model = label_tracker_model.AnimationLabelTrackerModel.__new__(
            label_tracker_model.AnimationLabelTrackerModel
        )
        model.preferences = {}
        data = {"ranges": [], "file_data": {"source": "previous_file"}}

        model.set_last_used_data(data, save=False)
        data["file_data"]["source"] = "mutated"
        stored_data = model.get_last_used_data()
        stored_data["file_data"]["source"] = "changed_after_read"

        self.assertEqual("previous_file", model.get_last_used_data()["file_data"]["source"])

    def test_automation_check_states_are_scoped_to_the_current_folder(self):
        """Checks automation selections reset after changing folders."""
        model = label_tracker_model.AnimationLabelTrackerModel.__new__(
            label_tracker_model.AnimationLabelTrackerModel
        )
        model.preferences = {}
        first_folder = os.path.join("scripts", "first")
        second_folder = os.path.join("scripts", "second")

        model.set_automation_check_state(
            first_folder,
            "optional_step.py",
            False,
            save=False,
        )

        self.assertEqual(
            {"optional_step.py": False},
            model.get_automation_check_states(first_folder),
        )
        self.assertTrue(
            model.reset_automation_check_states(second_folder, save=False)
        )
        self.assertEqual({}, model.get_automation_check_states(second_folder))
        self.assertEqual({}, model.get_automation_check_states(first_folder))

    def test_automation_check_states_preserve_missing_script_entries(self):
        """Checks stored selections remain available if a script returns later."""
        model = label_tracker_model.AnimationLabelTrackerModel.__new__(
            label_tracker_model.AnimationLabelTrackerModel
        )
        model.preferences = {}
        automation_folder = os.path.join("scripts", "automations")

        model.set_automation_check_state(
            automation_folder,
            "temporary_step.py",
            False,
            save=False,
        )

        self.assertEqual(
            {"temporary_step.py": False},
            model.get_automation_check_states(automation_folder),
        )

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
