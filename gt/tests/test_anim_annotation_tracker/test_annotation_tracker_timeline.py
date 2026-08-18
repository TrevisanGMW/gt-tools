"""Tests Annotation Tracker timeline layout helpers."""

import unittest
from types import SimpleNamespace

from gt.tools.anim_annotation_tracker import annotation_tracker


class TestAnnotationTrackerTimeline(unittest.TestCase):
    """Tests visual lane assignment for overlapping annotation ranges."""

    def test_pack_range_lanes_stacks_overlapping_ranges(self):
        """Checks overlapping ranges receive separate visual lanes."""
        ranges = [
            annotation_tracker.RangeItem("First", 1, 10, (100, 100, 100)),
            annotation_tracker.RangeItem("Second", 5, 8, (100, 100, 100)),
            annotation_tracker.RangeItem("Third", 11, 20, (100, 100, 100)),
        ]

        expected_lanes = {0: 0, 1: 1, 2: 0}
        actual_lanes = annotation_tracker.pack_range_lanes(ranges)

        self.assertEqual(expected_lanes, actual_lanes)

    def test_pack_range_lanes_stacks_shared_endpoints(self):
        """Checks shared endpoint ranges remain visually distinct."""
        ranges = [
            annotation_tracker.RangeItem("First", 1, 10, (100, 100, 100)),
            annotation_tracker.RangeItem("Second", 10, 20, (100, 100, 100)),
        ]

        expected_lanes = {0: 0, 1: 1}
        actual_lanes = annotation_tracker.pack_range_lanes(ranges)

        self.assertEqual(expected_lanes, actual_lanes)

    def test_apply_schema_refreshes_controls_and_discards_only_removed_data(self):
        """Checks a confirmed schema change rebuilds with compatible values."""
        range_item = SimpleNamespace(
            custom_data={"state": "walk", "legacy_range": "remove"}
        )
        rebuilt_file_data = []
        view = SimpleNamespace(
            file_data={"source": "mocap", "legacy_file": "remove"},
            scene_file_data_cache={},
            timeline=SimpleNamespace(ranges=[range_item]),
        )

        def confirm_data_loss(data_loss):
            return data_loss == {
                "file_data": ["legacy_file"],
                "range_data": ["legacy_range"],
            }

        def rebuild_schema_ui(file_data=None):
            rebuilt_file_data.append(file_data)

        view._confirm_schema_data_loss = confirm_data_loss
        view.rebuild_schema_ui = rebuild_schema_ui
        schema = {
            "file_level": [{"type": "string", "name": "source"}],
            "frame_range": [{"type": "string", "name": "state"}],
        }

        result = annotation_tracker.RangeToolWindow._apply_schema(view, schema)

        self.assertTrue(result)
        self.assertEqual({"source": "mocap"}, view.file_data)
        self.assertEqual({"source": "mocap"}, view.scene_file_data_cache)
        self.assertEqual({"state": "walk"}, range_item.custom_data)
        self.assertEqual([{"source": "mocap"}], rebuilt_file_data)

    def test_schema_mismatch_ignores_missing_optional_fields(self):
        """Checks incomplete optional data does not trigger a schema warning."""
        view = SimpleNamespace(
            schema={
                "file_level": [
                    {"type": "string", "name": "source"},
                    {"type": "string", "name": "context"},
                ],
                "frame_range": [
                    {"type": "string", "name": "state"},
                    {"type": "string", "name": "interaction_item"},
                ],
            }
        )
        ranges = [SimpleNamespace(custom_data={"state": "walk"})]

        result = annotation_tracker.RangeToolWindow.check_schema_mismatch(
            view,
            ranges,
            {"source": "mocap"},
        )

        self.assertFalse(result)

    def test_schema_mismatch_is_skipped_without_an_active_schema(self):
        """Checks unloaded schemas cannot discard saved scene data."""
        view = SimpleNamespace(schema={})

        result = annotation_tracker.RangeToolWindow.check_schema_mismatch(
            view,
            [SimpleNamespace(custom_data={"removed_range_field": "value"})],
            {"removed_file_field": "value"},
        )

        self.assertFalse(result)

    def test_confirmed_schema_loss_filters_file_and_range_data(self):
        """Checks acknowledged loss is removed before data is persisted."""
        view = SimpleNamespace(
            schema={
                "file_level": [{"type": "string", "name": "source"}],
                "frame_range": [{"type": "string", "name": "state"}],
            }
        )
        range_item = SimpleNamespace(
            custom_data={"state": "walk", "removed_range_field": "value"}
        )

        file_data = annotation_tracker.RangeToolWindow._filter_loaded_data_for_schema(
            view,
            [range_item],
            {"source": "mocap", "removed_file_field": "value"},
        )

        self.assertEqual({"source": "mocap"}, file_data)
        self.assertEqual({"state": "walk"}, range_item.custom_data)

    def test_initial_schema_path_is_available_before_scene_data_load(self):
        """Checks the saved schema is restored before scene data is checked."""
        view = SimpleNamespace(
            model=SimpleNamespace(
                preferences={"schema_path": ' "C:/schemas/annotation.json" '}
            )
        )

        schema_path = annotation_tracker.RangeToolWindow._get_initial_schema_path(
            view
        )

        self.assertEqual("C:/schemas/annotation.json", schema_path)

    def test_save_to_scene_skips_writes_while_loading_scene_data(self):
        """Checks loading cannot overwrite scene data before schema setup."""
        view = SimpleNamespace(_is_building_ui=False, _is_loading_data=True)

        result = annotation_tracker.RangeToolWindow.save_to_scene(view)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
