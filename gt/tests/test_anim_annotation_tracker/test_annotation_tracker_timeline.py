"""Tests Annotation Tracker timeline layout helpers."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock
from unittest.mock import patch

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

    @staticmethod
    def _make_timeline_view_state(start_frame=0, end_frame=100, width=200):
        """Builds a stand-in timeline for view-window math tests.

        Args:
            start_frame (int): Timeline start frame.
            end_frame (int): Timeline end frame.
            width (int): Simulated widget width in pixels.

        Returns:
            SimpleNamespace: Object usable with unbound timeline methods.
        """
        timeline = SimpleNamespace(
            start_frame=start_frame,
            end_frame=end_frame,
            view_start=float(start_frame),
            view_end=float(end_frame),
            MIN_VIEW_SPAN=annotation_tracker.CustomTimelineWidget.MIN_VIEW_SPAN,
            width=lambda: width,
            viewChanged=SimpleNamespace(emit=lambda: None),
            update=lambda: None,
        )
        timeline.get_view_span = (
            lambda: annotation_tracker.CustomTimelineWidget.get_view_span(timeline)
        )
        timeline.set_view_range = (
            lambda view_start, view_end: (
                annotation_tracker.CustomTimelineWidget.set_view_range(
                    timeline,
                    view_start,
                    view_end,
                )
            )
        )
        return timeline

    def test_set_view_range_clamps_to_timeline_bounds(self):
        """Checks zooming can never move the view past the frame range."""
        timeline = self._make_timeline_view_state(start_frame=10, end_frame=110)

        timeline.set_view_range(-50, 40)

        self.assertEqual(10.0, timeline.view_start)
        self.assertEqual(100.0, timeline.view_end)

    def test_set_view_range_enforces_a_minimum_span(self):
        """Checks extreme zoom-in stops at the minimum visible span."""
        timeline = self._make_timeline_view_state(start_frame=0, end_frame=100)

        timeline.set_view_range(50, 50.5)

        expected_span = annotation_tracker.CustomTimelineWidget.MIN_VIEW_SPAN
        self.assertEqual(expected_span, timeline.view_end - timeline.view_start)

    def test_zoom_view_keeps_the_anchor_frame_stationary(self):
        """Checks the frame under the cursor stays put while zooming."""
        timeline = self._make_timeline_view_state(
            start_frame=0,
            end_frame=100,
            width=200,
        )

        annotation_tracker.CustomTimelineWidget.zoom_view(timeline, 2.0, 100)

        self.assertEqual(25.0, timeline.view_start)
        self.assertEqual(75.0, timeline.view_end)

    def test_pan_view_preserves_span_at_timeline_edges(self):
        """Checks panning clamps to the end without shrinking the window."""
        timeline = self._make_timeline_view_state(start_frame=0, end_frame=100)
        timeline.set_view_range(40, 60)

        annotation_tracker.CustomTimelineWidget.pan_view(timeline, 1000)

        self.assertEqual(80.0, timeline.view_start)
        self.assertEqual(100.0, timeline.view_end)

    def test_set_timeline_bounds_resets_an_unzoomed_view(self):
        """Checks a full view keeps following Maya's playback range."""
        timeline = self._make_timeline_view_state(start_frame=0, end_frame=100)
        timeline.is_zoomed = (
            lambda: annotation_tracker.CustomTimelineWidget.is_zoomed(timeline)
        )

        annotation_tracker.CustomTimelineWidget.set_timeline_bounds(
            timeline,
            0,
            250,
        )

        self.assertEqual(0.0, timeline.view_start)
        self.assertEqual(250.0, timeline.view_end)

    def test_set_timeline_bounds_reclamps_a_zoomed_view(self):
        """Checks shrinking the playback range pulls the zoom window inside."""
        timeline = self._make_timeline_view_state(start_frame=0, end_frame=200)
        timeline.is_zoomed = (
            lambda: annotation_tracker.CustomTimelineWidget.is_zoomed(timeline)
        )
        timeline.set_view_range(150, 200)

        annotation_tracker.CustomTimelineWidget.set_timeline_bounds(
            timeline,
            0,
            100,
        )

        self.assertEqual(50.0, timeline.view_start)
        self.assertEqual(100.0, timeline.view_end)

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

    def test_create_example_schema_copies_packaged_file_and_writes_stdout(self):
        """Checks successful sample creation is not reported as a warning."""
        requested_path = "C:/schemas/schema.json"
        copied_path = "C:\\schemas\\schema.json"
        schema_path_field = SimpleNamespace(setText=MagicMock())
        check_schema_path = MagicMock()
        stdout = SimpleNamespace(write=MagicMock())
        view = SimpleNamespace(
            schema_path_fld=schema_path_field,
            check_schema_path=check_schema_path,
        )

        with patch.object(
            annotation_tracker.QtWidgets.QFileDialog,
            "getSaveFileName",
            return_value=(requested_path, "JSON Files (*.json)"),
        ), patch.object(
            annotation_tracker.annotation_tracker_model,
            "copy_sample_schema",
            return_value=copied_path,
        ) as mock_copy, patch.object(
            annotation_tracker.sys,
            "stdout",
            stdout,
        ), patch.object(
            annotation_tracker.cmds,
            "warning",
            create=True,
        ) as mock_warning:
            annotation_tracker.RangeToolWindow.create_example_schema(view)

        mock_copy.assert_called_once_with(requested_path)
        schema_path_field.setText.assert_called_once_with(copied_path)
        check_schema_path.assert_called_once_with(rebuild=True)
        stdout.write.assert_called_once_with(
            f"Created example schema at {copied_path}\n"
        )
        mock_warning.assert_not_called()

    def test_save_to_scene_skips_writes_while_loading_scene_data(self):
        """Checks loading cannot overwrite scene data before schema setup."""
        view = SimpleNamespace(_is_building_ui=False, _is_loading_data=True)

        result = annotation_tracker.RangeToolWindow.save_to_scene(view)

        self.assertIsNone(result)

    def test_setup_scriptjob_registers_time_and_scene_events(self):
        """Checks tracker callbacks cover time, opened, and new scenes."""
        view = SimpleNamespace(
            teardown_scriptjob=MagicMock(),
            on_maya_time_changed=MagicMock(),
            _deferred_scene_refresh=MagicMock(),
            sj_id=None,
            _scene_script_job_ids=[],
        )

        with patch.object(
            annotation_tracker.cmds,
            "scriptJob",
            side_effect=[101, 102, 103],
            create=True,
        ) as mock_script_job:
            annotation_tracker.RangeToolWindow.setup_scriptjob(view)

        expected_events = [
            "timeChanged",
            "SceneOpened",
            "NewSceneOpened",
        ]
        actual_events = [
            call.kwargs["event"][0]
            for call in mock_script_job.call_args_list
        ]
        self.assertEqual(expected_events, actual_events)
        self.assertEqual(101, view.sj_id)
        self.assertEqual([102, 103], view._scene_script_job_ids)

    def test_refresh_scene_data_reloads_changed_scene_payload(self):
        """Checks external scene-data changes repopulate the tracker."""
        loaded_range = annotation_tracker.RangeItem(
            "Walk",
            1,
            24,
            (100, 150, 200),
        )
        loaded_file_data = {"source": "new_scene"}
        handle_data_load = MagicMock()
        refresh_from_maya = MagicMock()
        view = SimpleNamespace(
            runtime_widgets_alive=lambda: True,
            _is_refreshing_scene_data=False,
            _scene_path_cache="C:/scenes/old_scene.ma",
            _scene_payload_cache={"range_data": [], "file_data": {}},
            _get_current_scene_path=lambda: "C:/scenes/new_scene.ma",
            handle_data_load=handle_data_load,
            refresh_from_maya=refresh_from_maya,
        )

        with patch.object(
            annotation_tracker.DataManager,
            "load_data",
            return_value=([loaded_range], loaded_file_data),
        ):
            result = annotation_tracker.RangeToolWindow.refresh_scene_data(view)

        self.assertTrue(result)
        handle_data_load.assert_called_once_with(
            [loaded_range],
            loaded_file_data,
        )
        refresh_from_maya.assert_called_once_with()
        self.assertEqual("C:/scenes/new_scene.ma", view._scene_path_cache)
        self.assertFalse(view._is_refreshing_scene_data)

    def test_refresh_scene_data_preserves_unchanged_in_memory_data(self):
        """Checks focus refresh avoids rebuilding an unchanged scene."""
        loaded_range = annotation_tracker.RangeItem(
            "Walk",
            1,
            24,
            (100, 150, 200),
        )
        loaded_file_data = {"source": "same_scene"}
        scene_payload = annotation_tracker.DataManager.build_payload(
            [loaded_range],
            loaded_file_data,
        )
        handle_data_load = MagicMock()
        refresh_from_maya = MagicMock()
        view = SimpleNamespace(
            runtime_widgets_alive=lambda: True,
            _is_refreshing_scene_data=False,
            _scene_path_cache="C:/scenes/same_scene.ma",
            _scene_payload_cache=scene_payload,
            _get_current_scene_path=lambda: "C:/scenes/same_scene.ma",
            handle_data_load=handle_data_load,
            refresh_from_maya=refresh_from_maya,
        )

        with patch.object(
            annotation_tracker.DataManager,
            "load_data",
            return_value=([loaded_range], loaded_file_data),
        ):
            result = annotation_tracker.RangeToolWindow.refresh_scene_data(view)

        self.assertFalse(result)
        handle_data_load.assert_not_called()
        refresh_from_maya.assert_called_once_with()
        self.assertFalse(view._is_refreshing_scene_data)


if __name__ == "__main__":
    unittest.main()
