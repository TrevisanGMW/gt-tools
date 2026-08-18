"""Tests for Annotation Tracker pure model helpers."""

import json
import os
import unittest
from types import SimpleNamespace

from gt.tools.anim_annotation_tracker import annotation_tracker_model


class TestAnnotationTrackerModel(unittest.TestCase):
    """Tests import-safe Annotation Tracker behavior."""

    def test_default_preferences_leave_automation_folder_empty(self):
        """Checks automations require an explicit user-selected folder."""
        preferences = annotation_tracker_model.get_default_preferences()

        self.assertEqual("", preferences["automation_path"])

    def test_default_preferences_leave_schema_path_empty(self):
        """Checks a new tracker does not point at its packaged sample schema."""
        preferences = annotation_tracker_model.get_default_preferences()

        self.assertEqual("", preferences["schema_path"])

    def test_default_preferences_show_the_timeline(self):
        """Checks the timeline remains visible until a user hides it."""
        preferences = annotation_tracker_model.get_default_preferences()

        self.assertTrue(preferences["show_timeline"])

    def test_default_preferences_use_high_auto_adjust_tolerances(self):
        """Checks crop and stretch are useful with fresh preferences."""
        preferences = annotation_tracker_model.get_default_preferences()

        self.assertEqual(50, preferences["crop_tolerance"])
        self.assertEqual(50, preferences["stretch_tolerance"])

    def test_empty_automation_path_is_omitted_from_saved_preferences(self):
        """Checks an automation folder is only saved after it is configured."""
        model = annotation_tracker_model.AnnotationTrackerModel.__new__(
            annotation_tracker_model.AnnotationTrackerModel
        )
        saved_preferences = []
        model.prefs = SimpleNamespace(
            set_raw_preferences=saved_preferences.append,
            save=lambda: None,
        )
        model.preferences = annotation_tracker_model.get_default_preferences()

        model.save_preferences()

        self.assertNotIn("automation_path", saved_preferences[-1])
        self.assertNotIn(
            annotation_tracker_model.AUTOMATION_CHECK_STATES_KEY,
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
        with open(annotation_tracker_model.get_sample_schema_path(), encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        self.assertEqual("high", schema["file_level"][0]["options"][2])
        self.assertTrue(schema["validation"]["full_coverage"])

    def test_sample_schema_contains_file_data_fields(self):
        """Checks the example file data fields and requirements."""
        with open(annotation_tracker_model.get_sample_schema_path(), encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        file_fields = annotation_tracker_model.flatten_schema_items(schema["file_level"])
        self.assertEqual(
            ["quality", "source", "style", "context", "clipped", "annotated", "commercial_use"],
            [field["name"] for field in file_fields],
        )
        commercial_field = next(
            field for field in file_fields if field["name"] == "commercial_use"
        )
        style_field = next(field for field in file_fields if field["name"] == "style")
        context_field = next(field for field in file_fields if field["name"] == "context")
        self.assertEqual("boolean", commercial_field["type"])
        self.assertTrue(commercial_field["required"])
        self.assertEqual("enum", style_field["type"])
        self.assertTrue(style_field["required"])
        self.assertIn("tense", style_field["options"])
        self.assertIn("old", style_field["options"])
        self.assertEqual("string", context_field["type"])
        self.assertFalse(context_field["required"])
        self.assertEqual(
            "e.g. character exits through a heavy doorway",
            context_field["placeholder"],
        )
        self.assertTrue(schema["file_level"][1]["equal_widths"])

    def test_sample_schema_contains_interaction_tracking_fields(self):
        """Checks interaction metadata has the expected optional fields."""
        with open(annotation_tracker_model.get_sample_schema_path(), encoding="utf-8") as schema_file:
            schema = json.load(schema_file)

        range_fields = annotation_tracker_model.flatten_schema_items(schema["frame_range"])
        fields_by_name = {field["name"]: field for field in range_fields}
        schema_rows = [
            row for row in schema["frame_range"] if row.get("type") == "row"
        ]
        row_field_names = [
            [item["name"] for item in row["items"]] for row in schema_rows
        ]

        self.assertNotIn("transition", fields_by_name["state"]["options"])
        self.assertIn("enter", fields_by_name["state"]["options"])
        self.assertIn("exit", fields_by_name["state"]["options"])
        self.assertNotIn("mixed", fields_by_name["stance"]["options"])
        self.assertNotIn("enter", fields_by_name)
        self.assertNotIn("exit", fields_by_name)
        self.assertNotIn("transition", fields_by_name)
        self.assertFalse(fields_by_name["override_style"]["required"])
        self.assertEqual("enum", fields_by_name["override_style"]["type"])
        self.assertIn("tense", fields_by_name["override_style"]["options"])
        self.assertIn("old", fields_by_name["override_style"]["options"])
        self.assertFalse(fields_by_name["interaction_type"]["required"])
        self.assertIn("sustain", fields_by_name["interaction_type"]["options"])
        self.assertEqual("string", fields_by_name["contact_attributes"]["type"])
        self.assertFalse(fields_by_name["contact_attributes"]["required"])
        self.assertEqual(
            "e.g. pelvis_docking.contactWeight",
            fields_by_name["contact_attributes"]["placeholder"],
        )
        self.assertIn("interaction_item", fields_by_name)
        self.assertNotIn("interaction_context", fields_by_name)
        self.assertNotIn("interaction_attribute", fields_by_name)
        self.assertNotIn("auxiliary_context", fields_by_name)
        self.assertIn(
            ["interaction_type", "interaction_scope"],
            row_field_names,
        )
        self.assertIn(
            ["interaction_item", "contact_attributes"],
            row_field_names,
        )

    def test_last_used_data_is_stored_as_a_copy(self):
        """Checks last-used data is isolated from caller mutations."""
        model = annotation_tracker_model.AnnotationTrackerModel.__new__(
            annotation_tracker_model.AnnotationTrackerModel
        )
        model.preferences = {}
        data = {"range_data": [], "file_data": {"source": "previous_file"}}

        model.set_last_used_data(data, save=False)
        data["file_data"]["source"] = "mutated"
        stored_data = model.get_last_used_data()
        stored_data["file_data"]["source"] = "changed_after_read"

        self.assertEqual("previous_file", model.get_last_used_data()["file_data"]["source"])

    def test_automation_check_states_are_scoped_to_the_current_folder(self):
        """Checks automation selections reset after changing folders."""
        model = annotation_tracker_model.AnnotationTrackerModel.__new__(
            annotation_tracker_model.AnnotationTrackerModel
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
        model = annotation_tracker_model.AnnotationTrackerModel.__new__(
            annotation_tracker_model.AnnotationTrackerModel
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

        flattened_items = annotation_tracker_model.flatten_schema_items(schema_items)

        self.assertEqual(["first", "second", "third"], [
            item["name"] for item in flattened_items
        ])

    def test_get_schema_data_loss_returns_only_removed_fields(self):
        """Checks schema changes identify only fields that would be discarded."""
        schema = {
            "file_level": [{"type": "string", "name": "source"}],
            "frame_range": [{"type": "string", "name": "state"}],
        }
        ranges = [
            SimpleNamespace(custom_data={"state": "walk", "legacy": "value"}),
            {"custom_data": {"legacy": "another value"}},
        ]

        actual = annotation_tracker_model.get_schema_data_loss(
            schema,
            {"source": "mocap", "legacy": "value"},
            ranges,
        )

        self.assertEqual(
            {"file_data": ["legacy"], "range_data": ["legacy"]},
            actual,
        )

    def test_schema_change_detects_values_removed_from_enum_options(self):
        """Checks replaced enum options are protected as potential data loss."""
        schema = {
            "file_level": [
                {"type": "enum", "name": "source", "options": ["mocap"]}
            ],
            "frame_range": [
                {"type": "enum", "name": "state", "options": ["idle"]}
            ],
        }
        ranges = [SimpleNamespace(custom_data={"state": "walk"})]

        actual_loss = annotation_tracker_model.get_schema_data_loss(
            schema,
            {"source": "vendor"},
            ranges,
        )
        actual_file_data = annotation_tracker_model.filter_schema_data(
            schema,
            {"source": "vendor"},
            "file_data",
        )
        actual_range_data = annotation_tracker_model.filter_schema_data(
            schema,
            {"state": "walk"},
            "range_data",
        )

        self.assertEqual(
            {"file_data": ["source"], "range_data": ["state"]},
            actual_loss,
        )
        self.assertEqual({}, actual_file_data)
        self.assertEqual({}, actual_range_data)

    def test_build_usd_custom_data_omits_tracker_only_range_fields(self):
        """Checks the USD data projection preserves only user metadata."""
        payload = {
            "file_data": {"source": "mocap_take_01", "annotated": True},
            "range_data": [
                {
                    "id": "b511c4c0-39a2-4d96-b5b3-5a486f5d5b4d",
                    "name": "Walk Forward",
                    "start": 1,
                    "end": 30,
                    "color": [100, 150, 200],
                    "locked": True,
                    "custom_data": {
                        "state": "walk",
                        "contact_attributes": "door_ctrl.open, door_ctrl.close",
                    },
                }
            ],
        }
        expected = {
            "file_data": {"source": "mocap_take_01", "annotated": True},
            "range_data": {
                "range_000": {
                    "name": "Walk Forward",
                    "start_frame": 1,
                    "end_frame": 30,
                    "metadata": {
                        "state": "walk",
                        "contact_attributes": "door_ctrl.open, door_ctrl.close",
                    },
                }
            },
        }

        actual = annotation_tracker_model.build_usd_custom_data(payload)

        self.assertEqual(expected, actual)
        self.assertNotIn("id", actual["range_data"]["range_000"])
        self.assertNotIn("color", actual["range_data"]["range_000"])
        self.assertNotIn("locked", actual["range_data"]["range_000"])

    def test_validation_reports_all_missing_required_values(self):
        """Checks validation returns every missing required field."""
        schema = {
            "validation": {"full_coverage": False, "allow_overlap": True},
            "file_level": [{"type": "string", "name": "source", "required": True}],
            "frame_range": [{"type": "string", "name": "state", "required": True}],
        }

        errors = annotation_tracker_model.collect_validation_errors(
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

        changed_ranges = annotation_tracker_model.adjust_adjacent_ranges(
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

        changed_ranges = annotation_tracker_model.adjust_adjacent_ranges(
            active_range,
            [previous_range, active_range],
            auto_stretch=True,
            stretch_tolerance=4,
        )

        self.assertEqual([previous_range], changed_ranges)
        self.assertEqual(14, previous_range.end)

    def test_get_uncovered_frame_ranges_returns_all_timeline_gaps(self):
        """Checks overlapping and adjacent coverage produces only real gaps."""
        ranges = [
            SimpleNamespace(start=8, end=12),
            SimpleNamespace(start=1, end=3),
            SimpleNamespace(start=3, end=5),
            SimpleNamespace(start=18, end=14),
            SimpleNamespace(start=30, end=40),
        ]

        gaps = annotation_tracker_model.get_uncovered_frame_ranges(ranges, 1, 20)

        self.assertEqual([(6, 7), (13, 13), (19, 20)], gaps)

    def test_get_uncovered_frame_ranges_covers_empty_timeline(self):
        """Checks an empty tracker produces one gap spanning the timeline."""
        gaps = annotation_tracker_model.get_uncovered_frame_ranges([], 10, 20)

        self.assertEqual([(10, 20)], gaps)

    def test_get_uncovered_frame_range_at_frame_finds_only_empty_areas(self):
        """Checks a frame resolves to its gap only when it is uncovered."""
        ranges = [
            SimpleNamespace(start=1, end=5),
            SimpleNamespace(start=10, end=15),
        ]

        gap = annotation_tracker_model.get_uncovered_frame_range_at_frame(
            ranges,
            1,
            20,
            8,
        )
        covered_result = annotation_tracker_model.get_uncovered_frame_range_at_frame(
            ranges,
            1,
            20,
            4,
        )

        self.assertEqual((6, 9), gap)
        self.assertIsNone(covered_result)
