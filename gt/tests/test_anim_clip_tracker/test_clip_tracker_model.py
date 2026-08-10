"""Tests Animation Clip Tracker automation preference helpers."""

import os
import unittest
from types import SimpleNamespace

from gt.tools.anim_clip_tracker import clip_tracker_model


class TestClipTrackerModelAutomations(unittest.TestCase):
    """Tests automation data that is independent of a Maya scene."""

    def get_model(self):
        """Builds a model instance without loading Maya preferences.

        Returns:
            ClipTrackerModel: Model with default automation preference values.
        """
        model = clip_tracker_model.ClipTrackerModel.__new__(
            clip_tracker_model.ClipTrackerModel
        )
        model.automation_path = ""
        model.automation_check_states = {}
        model.automation_check_states_path = ""
        return model

    def test_automation_check_states_are_scoped_to_the_current_folder(self):
        """Checks changing folders clears stored batch selections."""
        model = self.get_model()
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

    def test_automation_path_is_empty_by_default(self):
        """Checks automations require an explicit user-selected folder."""
        model = clip_tracker_model.ClipTrackerModel.__new__(
            clip_tracker_model.ClipTrackerModel
        )

        model.reset_preferences_to_defaults()

        self.assertEqual("", model.automation_path)

    def test_empty_automation_path_is_omitted_from_saved_preferences(self):
        """Checks an automation folder is only saved after it is configured."""
        model = clip_tracker_model.ClipTrackerModel.__new__(
            clip_tracker_model.ClipTrackerModel
        )
        model.reset_preferences_to_defaults()
        model.prefs = SimpleNamespace(preferences={}, save=lambda: None)

        model.save_preferences()

        state = model.prefs.preferences[clip_tracker_model.PREFS_KEY_STATE]
        self.assertNotIn("automation_path", state)
        self.assertNotIn(clip_tracker_model.AUTOMATION_CHECK_STATES_KEY, state)

        model.automation_path = os.path.join("scripts", "automations")
        model.save_preferences()

        state = model.prefs.preferences[clip_tracker_model.PREFS_KEY_STATE]
        self.assertEqual(model.automation_path, state["automation_path"])

    def test_sample_automation_documents_all_clip_update_helpers(self):
        """Checks the packaged sample exposes the supported automation helpers."""
        with open(
            clip_tracker_model.get_sample_automation_path(),
            encoding="utf-8",
        ) as automation_file:
            script_text = automation_file.read()

        expected_helpers = [
            "create_clip",
            "set_clip_start",
            "set_clip_end",
            "set_clip_name",
            "set_clip_active",
        ]

        self.assertTrue(
            all(helper in script_text for helper in expected_helpers)
        )
        compile(script_text, clip_tracker_model.get_sample_automation_path(), "exec")


if __name__ == "__main__":
    unittest.main()
