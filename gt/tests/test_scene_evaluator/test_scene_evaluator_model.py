"""Tests Scene Evaluator preferences and presets without starting Maya."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from gt.tools.scene_evaluator.scene_evaluator_model import (
    ACTION_ALWAYS_ALLOW,
    ACTION_CONFIRM_BYPASS,
    ACTION_REQUIRE_PASS,
    DEFAULT_SETTINGS,
    PRESET_VERSION,
    SceneEvaluatorModel,
)


class TestSceneEvaluatorModel(unittest.TestCase):
    """Checks persistence, preset validation and recovery from failed saves."""

    def setUp(self):
        """Creates isolated preferences and preset paths for each test."""
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        self.location = Path(temp_dir.name)
        self.prefs = Mock()
        self.prefs.get_raw_preferences.return_value = {}
        self.prefs.set_raw_preferences.side_effect = self.set_preferences
        self.model = SceneEvaluatorModel(prefs=self.prefs)

    def set_preferences(self, settings):
        """Reflects changes in subsequent preference reads.

        Args:
            settings (dict): Settings written to the preferences backend.
        """
        self.prefs.get_raw_preferences.return_value = settings

    def test_new_model_does_not_write_preferences(self):
        """Starts with an empty checklist and a hidden action button."""
        self.assertEqual(DEFAULT_SETTINGS, self.model.settings)
        self.prefs.save.assert_not_called()

    def test_reopening_restores_settings(self):
        """Restores saved selections in order, along with the action configuration."""
        self.model.save_settings(
            {
                **self.model.settings,
                "validators": ["SceneSaved", "NoReferences", "SceneSaved"],
                "action": {
                    "enabled": True,
                    "label": " Export Scene ",
                    "script": "print('ready')",
                    "mode": ACTION_REQUIRE_PASS,
                },
            }
        )
        self.prefs.save.assert_called_once()
        restored_model = SceneEvaluatorModel(prefs=self.prefs)
        self.assertEqual(["SceneSaved", "NoReferences"], restored_model.settings["validators"])
        self.assertEqual("Export Scene", restored_model.settings["action"]["label"])
        self.assertEqual(self.model.settings, restored_model.settings)

    def test_preset_round_trip_preserves_script_without_executing_it(self):
        """Preserves unknown validator IDs and Unicode script text when staging a preset."""
        marker_path = self.location / "action_ran"
        script = f"from pathlib import Path\nPath({str(marker_path)!r}).write_text('ação', encoding='utf-8')\n"
        settings = {
            **self.model.settings,
            "validators": ["NoNamespaces", "UnavailableValidator"],
            "action": {"enabled": True, "label": "Exportação", "script": script, "mode": ACTION_CONFIRM_BYPASS},
        }
        preset_path = self.location / "preset.json"
        self.model.write_preset(preset_path, settings)
        restored_settings = self.model.read_preset(preset_path)

        self.assertEqual(settings, restored_settings)
        self.assertEqual(DEFAULT_SETTINGS, self.model.settings)
        self.assertFalse(marker_path.exists())

    def test_action_only_export_omits_validators(self):
        """Distinguishes excluding validator choices from exporting an empty checklist."""
        preset_path = self.location / "action_only.json"
        settings = {**DEFAULT_SETTINGS, "validators": ["SceneSaved"]}
        self.model.write_preset(preset_path, settings, include_validators=False)

        payload = json.loads(preset_path.read_text(encoding="utf-8"))
        self.assertNotIn("validators", payload)
        self.assertEqual(payload, self.model.read_preset(preset_path))
        self.assertEqual(["SceneSaved"], settings["validators"])

        self.model.write_preset(preset_path, DEFAULT_SETTINGS)
        self.assertEqual([], self.model.read_preset(preset_path)["validators"])

    def test_version_two_preset_preserves_action_mode_and_validators(self):
        """Migrates presets from before action-only export was available."""
        settings = {
            **DEFAULT_SETTINGS,
            "validators": ["SceneSaved"],
            "action": {**DEFAULT_SETTINGS["action"], "mode": ACTION_CONFIRM_BYPASS},
        }
        preset_path = self.location / "version_two.json"
        preset_path.write_text(json.dumps({**settings, "version": 2}), encoding="utf-8")

        self.assertEqual(settings, self.model.read_preset(preset_path))

    def test_invalid_action_leaves_saved_preferences_unchanged(self):
        """Rejects syntax errors before replacing the previous settings."""
        self.model.save_settings({**self.model.settings, "validators": ["SceneSaved"]})
        previous_settings = self.model.settings
        invalid_settings = {
            **self.model.settings,
            "action": {"enabled": True, "label": "Export", "script": "if", "mode": ACTION_REQUIRE_PASS},
        }

        with self.assertRaisesRegex(ValueError, "Python action line 1"):
            self.model.save_settings(invalid_settings)

        self.prefs.save.assert_called_once()
        self.assertEqual(previous_settings, self.prefs.get_raw_preferences())
        self.assertFalse(self.model.settings["action"]["enabled"])

    def test_rejects_unsupported_preset(self):
        """Rejects future formats and malformed JSON during import."""
        preset_path = self.location / "preset.json"
        future_preset = {**DEFAULT_SETTINGS, "version": PRESET_VERSION + 1}
        preset_path.write_text(json.dumps(future_preset), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unsupported"):
            self.model.read_preset(preset_path)

        preset_path.write_text('{"format":', encoding="utf-8")
        with self.assertRaises(ValueError):
            self.model.read_preset(preset_path)

    def test_legacy_preferences_and_presets_keep_their_action_behavior(self):
        """Migrates both legacy checkbox values while preserving the checklist and script."""
        preset_path = self.location / "legacy.json"
        for require_pass, expected_mode in ((True, ACTION_REQUIRE_PASS), (False, ACTION_ALWAYS_ALLOW)):
            with self.subTest(require_pass=require_pass):
                legacy_action = {"enabled": True, "label": "Export", "script": "print('ready')"}
                legacy = {
                    **DEFAULT_SETTINGS,
                    "version": 1,
                    "validators": ["SceneSaved"],
                    "action": {**legacy_action, "require_pass": require_pass},
                }
                expected = {
                    **DEFAULT_SETTINGS,
                    "validators": ["SceneSaved"],
                    "action": {**legacy_action, "mode": expected_mode},
                }
                self.set_preferences(legacy)
                preset_path.write_text(json.dumps(legacy), encoding="utf-8")

                self.assertEqual(expected, SceneEvaluatorModel(prefs=self.prefs).settings)
                self.assertEqual(expected, self.model.read_preset(preset_path))
        self.prefs.save.assert_not_called()

    def test_rejects_unknown_action_mode(self):
        """Rejects a preset that requests an unsupported action behavior."""
        settings = {**DEFAULT_SETTINGS, "action": {**DEFAULT_SETTINGS["action"], "mode": "unknown"}}
        with self.assertRaisesRegex(ValueError, "Invalid action button mode"):
            self.model.save_settings(settings)
        self.prefs.save.assert_not_called()

    def test_failed_save_restores_preferences_in_memory(self):
        """Keeps the current settings available after a failed preferences write."""
        self.model.save_settings({**self.model.settings, "validators": ["SceneSaved"]})
        previous_settings = self.model.settings

        self.prefs.save.return_value = False
        with self.assertRaises(OSError):
            self.model.save_settings({**previous_settings, "validators": []})

        self.assertEqual(previous_settings, self.model.settings)
        self.assertEqual(previous_settings, self.prefs.get_raw_preferences())
