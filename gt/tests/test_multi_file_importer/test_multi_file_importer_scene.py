import os
import sys
import unittest

# Import Tested Script
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.tools.multi_file_importer import multi_file_importer_constants as constants
from gt.tools.multi_file_importer import multi_file_importer_model as model
from gt.tools.multi_file_importer import multi_file_importer_scene as scene_settings

FILE_INFO = {
    "first.ma": {"fps": 24.0, "linear_unit": "cm", "up_axis": "y", "time_range": (1.0, 48.0)},
    "last.fbx": {"fps": 60.0, "linear_unit": "m"},
}


def fake_info_reader(file_path):
    return FILE_INFO.get(file_path, {})


class TestMultiFileImporterScene(unittest.TestCase):
    """Checks scene setting and timeline resolution."""

    def setUp(self):
        self.settings = model.normalize_settings({})

    def test_keep_current_changes_nothing(self):
        for source_key in ["frame_rate_source", "linear_unit_source", "up_axis_source"]:
            self.settings[source_key] = constants.SOURCE_KEEP
        expected = ({}, [])
        result = scene_settings.resolve_scene_targets(self.settings, ["first.ma"], fake_info_reader)
        self.assertEqual(expected, result)

    def test_default_sources_use_last_file(self):
        targets, warnings = scene_settings.resolve_scene_targets(self.settings, ["first.ma", "last.fbx"],
                                                                 fake_info_reader)
        self.assertEqual({"fps": 60.0, "linear_unit": "m"}, targets)
        self.assertEqual(1, len(warnings))  # last.fbx stores no up axis

    def test_first_last_and_custom_sources(self):
        self.settings.update({"frame_rate_source": constants.SOURCE_FIRST,
                              "linear_unit_source": constants.SOURCE_LAST,
                              "up_axis_source": constants.SOURCE_CUSTOM, "up_axis_custom": "z"})
        expected = ({"fps": 24.0, "linear_unit": "m", "up_axis": "z"}, [])
        result = scene_settings.resolve_scene_targets(self.settings, ["first.ma", "last.fbx"], fake_info_reader)
        self.assertEqual(expected, result)

    def test_missing_info_warns(self):
        self.settings.update({"frame_rate_source": constants.SOURCE_KEEP, "linear_unit_source": constants.SOURCE_KEEP})
        targets, warnings = scene_settings.resolve_scene_targets(self.settings, ["first.ma", "last.fbx"],
                                                                 fake_info_reader)
        self.assertEqual({}, targets)
        self.assertEqual(1, len(warnings))

    def test_custom_frame_rate(self):
        self.settings.update({"frame_rate_source": constants.SOURCE_CUSTOM, "frame_rate_custom": "29.97",
                              "linear_unit_source": constants.SOURCE_KEEP, "up_axis_source": constants.SOURCE_KEEP})
        targets, _ = scene_settings.resolve_scene_targets(self.settings, [], fake_info_reader)
        self.assertEqual({"fps": 29.97}, targets)

    def test_timeline_modes(self):
        records = [
            {"status": constants.STATUS_IMPORTED, "time_range": (5.2, 30.0), "stored_range": (1, 48)},
            {"status": constants.STATUS_FAILED, "time_range": (-100, 900), "stored_range": None},
            {"status": constants.STATUS_WARNING, "time_range": (0.0, 60.5), "stored_range": None},
        ]
        self.assertEqual((0.0, 61.0), scene_settings.resolve_timeline_range(self.settings, records))
        self.settings["timeline_mode"] = constants.TIMELINE_FIRST
        self.assertEqual((1.0, 48.0), scene_settings.resolve_timeline_range(self.settings, records))
        self.settings["timeline_mode"] = constants.TIMELINE_LAST
        self.assertEqual((0.0, 61.0), scene_settings.resolve_timeline_range(self.settings, records))
        self.settings.update({"timeline_mode": constants.TIMELINE_MANUAL, "timeline_start": 2.5,
                              "timeline_end": 9.5})
        self.assertEqual((2.5, 9.5), scene_settings.resolve_timeline_range(self.settings, records))
        self.settings["timeline_mode"] = constants.TIMELINE_KEEP
        self.assertIsNone(scene_settings.resolve_timeline_range(self.settings, records))

    def test_saved_ranges_mode_uses_widest_range(self):
        records = [
            {"status": constants.STATUS_IMPORTED, "time_range": (5.0, 30.0), "stored_range": (1.0, 48.0)},
            {"status": constants.STATUS_IMPORTED, "time_range": (0.0, 60.0), "stored_range": None},
        ]
        self.settings["timeline_mode"] = constants.TIMELINE_STORED
        self.assertEqual((0.0, 60.0), scene_settings.resolve_timeline_range(self.settings, records))

    def test_final_targets_restore_kept_values(self):
        original_state = {"fps": 30.0, "linear_unit": "cm", "up_axis": "y"}
        expected = {"fps": 24.0, "linear_unit": "cm", "up_axis": "y"}
        self.assertEqual(expected, scene_settings.build_final_targets({"fps": 24.0}, original_state))

    def test_find_changed_values(self):
        expected_state = {"fps": 24.0, "linear_unit": "cm", "up_axis": "y"}
        current_state = {"fps": 60.0, "linear_unit": "cm", "up_axis": "Y"}
        self.assertEqual(["Frame rate"], scene_settings.find_changed_values(expected_state, current_state))

    def test_scale_time_range(self):
        self.assertEqual((2.0, 96.0), scene_settings.scale_time_range((1, 48), 24, 48))
        self.assertEqual((1, 48), scene_settings.scale_time_range((1, 48), None, 48))

    def test_viewport_flags(self):
        self.assertEqual({}, scene_settings.build_viewport_flags(self.settings))
        self.settings.update({"review_joints": True, "review_joints_value": constants.HIDE,
                              "review_shading": True, "review_shading_value": constants.SHADING_WIREFRAME_ON_SHADED,
                              "review_lighting": True, "review_lighting_value": constants.LIGHTING_ALL})
        expected = {"joints": False, "displayAppearance": "smoothShaded", "wireframeOnShaded": True,
                    "displayLights": "all"}
        self.assertEqual(expected, scene_settings.build_viewport_flags(self.settings))
