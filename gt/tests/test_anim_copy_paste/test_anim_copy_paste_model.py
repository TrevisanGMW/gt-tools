"""Unit tests for the pure Copy/Paste Animation model."""

import unittest
from unittest import mock

from gt.tools.anim_copy_paste.anim_copy_paste_model import (
    AnimCopyPasteModel,
    AnimCopyPasteConstants,
)


class TestAnimCopyPasteModel(unittest.TestCase):
    """Tests Copy/Paste Animation settings and clip state."""

    def test_default_mapping_matches_character_names_and_hierarchy(self):
        """Uses name mapping when no mapping preference has been saved."""
        model = AnimCopyPasteModel()
        with mock.patch.object(model.prefs, "get_raw_preferences", return_value={}):
            model.reset_to_defaults()
            model.load_preferences()

        expected = AnimCopyPasteConstants.MappingMode.NAME
        self.assertEqual(expected, model.mapping_mode)

    def test_reset_restores_name_mapping_after_selection_order(self):
        """Restores character mapping after using positional mapping."""
        model = AnimCopyPasteModel()
        model.set_settings({"mapping_mode": AnimCopyPasteConstants.MappingMode.SELECTION})
        model.reset_to_defaults()

        expected = AnimCopyPasteConstants.MappingMode.NAME
        self.assertEqual(expected, model.mapping_mode)

    def test_set_settings_updates_mapping_and_channel_fields(self):
        model = AnimCopyPasteModel()

        model.set_settings(
            {
                "copy_scope": AnimCopyPasteConstants.CopyScope.SELECTED,
                "mapping_mode": AnimCopyPasteConstants.MappingMode.NAME,
                "source_namespace": "source_rig:",
                "target_namespace": "target_rig:",
                "source_attribute": "translateX",
                "destination_attribute": "rotateY",
                "paste_at_current_frame": False,
                "paste_frame": 24,
                "apply_euler_filter": True,
            }
        )

        expected = {
            "copy_scope": AnimCopyPasteConstants.CopyScope.SELECTED,
            "mapping_mode": AnimCopyPasteConstants.MappingMode.NAME,
            "source_namespace": "source_rig",
            "target_namespace": "target_rig",
            "source_attribute": "translateX",
            "destination_attribute": "rotateY",
            "paste_at_current_frame": False,
            "paste_frame": 24.0,
            "apply_euler_filter": True,
            "reverse_animation": False,
        }
        self.assertEqual(expected, model.get_settings())

    def test_has_clip_data_requires_copied_objects(self):
        model = AnimCopyPasteModel()

        model.set_clip_data({"objects": []})
        empty_result = model.has_clip_data()
        model.set_clip_data({"objects": [{"name": "|ctrl"}]})
        populated_result = model.has_clip_data()

        self.assertFalse(empty_result)
        self.assertTrue(populated_result)

    def test_available_modes_match_grouped_constants(self):
        expected = [
            AnimCopyPasteConstants.MappingMode.SELECTION,
            AnimCopyPasteConstants.MappingMode.NAME,
            AnimCopyPasteConstants.MappingMode.NAMESPACE,
        ]
        result = AnimCopyPasteModel.get_available_mapping_modes()

        self.assertEqual(expected, result)

        expected = [
            AnimCopyPasteConstants.CopyScope.ALL,
            AnimCopyPasteConstants.CopyScope.SELECTED,
            AnimCopyPasteConstants.CopyScope.BEFORE_CURRENT,
            AnimCopyPasteConstants.CopyScope.AFTER_CURRENT,
        ]
        result = AnimCopyPasteModel.get_available_copy_scopes()

        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
