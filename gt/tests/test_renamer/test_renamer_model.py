"""Unit tests for Renamer preference persistence."""

import unittest

from gt.tools.renamer import renamer_model
from gt.tools.renamer.renamer_controller import RenamerController


class MockMayaCmds:
    """Small Maya commands test double for optionVar operations."""

    def __init__(self):
        """Initializes stored option variables."""
        self.option_vars = {}

    def optionVar(self, exists=None, q=None, sv=None, remove=None):
        """Imitates the optionVar calls used by the Renamer model.

        Args:
            exists (str, optional): Variable name to look up.
            q (str, optional): Variable name to query.
            sv (tuple, optional): Variable name and value to store.
            remove (str, optional): Variable name to remove.

        Returns:
            bool or str or None: Result for the requested optionVar action.
        """
        if exists is not None:
            return exists in self.option_vars
        if q is not None:
            return self.option_vars.get(q)
        if sv is not None:
            self.option_vars[sv[0]] = sv[1]
            return None
        if remove is not None:
            self.option_vars.pop(remove, None)
        return None


class MockControllerModel:
    """Small model test double that records persisted settings."""

    def __init__(self):
        """Initializes the model test double."""
        self.settings = {}

    def save_setting(self, setting_key, setting_value):
        """Stores a setting written by the controller.

        Args:
            setting_key (str): Setting key.
            setting_value (str): Setting value.
        """
        self.settings[setting_key] = setting_value


class MockControllerView:
    """Small view test double that records enabled-state refreshes."""

    def __init__(self):
        """Initializes the view test double."""
        self.refresh_count = 0

    def refresh_enabled_states(self):
        """Records a view enabled-state refresh."""
        self.refresh_count += 1


class TestRenamerModel(unittest.TestCase):
    """Tests persistent Renamer settings without a Maya session."""

    def setUp(self):
        """Replaces the lazy Maya commands import with a controllable test double."""
        self.mock_cmds = MockMayaCmds()
        self.original_get_maya_cmds = renamer_model.get_maya_cmds
        renamer_model.get_maya_cmds = lambda: self.mock_cmds

    def tearDown(self):
        """Restores the original lazy Maya commands import."""
        renamer_model.get_maya_cmds = self.original_get_maya_cmds

    def test_user_entered_state_round_trips_through_option_vars(self):
        """Persists every editable Renamer field and mode across model instances."""
        model = renamer_model.RenamerModel()
        expected_settings = {
            "rename_text": "character",
            "use_source": "1",
            "prefix_mode": "input",
            "prefix_text": "char_",
            "suffix_mode": "input",
            "suffix_text": "_ctrl",
            "search_text": "left",
            "replace_text": "right",
        }

        for setting_key, value in expected_settings.items():
            model.save_setting(setting_key, value)

        loaded_model = renamer_model.RenamerModel()

        for setting_key, expected_value in expected_settings.items():
            self.assertEqual(expected_value, loaded_model.settings.get(setting_key))
            self.assertEqual(
                expected_value,
                self.mock_cmds.option_vars.get(renamer_model.OPTION_VAR_MAP[setting_key]),
            )

    def test_reset_preferences_clears_user_entered_state(self):
        """Removes every persisted user-entered state value when Reset is used."""
        model = renamer_model.RenamerModel()
        model.save_setting("rename_text", "character")
        model.save_setting("search_text", "old")
        model.save_setting("replace_text", "new")

        model.reset_preferences()

        self.assertEqual(renamer_model.DEFAULT_SETTINGS, model.settings)
        self.assertEqual({}, self.mock_cmds.option_vars)

    def test_mode_and_source_selection_changes_are_persisted(self):
        """Saves mode and source-name choices as soon as their controls change."""
        controller = RenamerController.__new__(RenamerController)
        controller.model = MockControllerModel()
        controller.view = MockControllerView()
        controller._syncing_view = False

        controller.on_use_source_changed(True)
        controller.on_mode_changed("prefix_mode", "input", True)
        controller.on_mode_changed("suffix_mode", "input", True)

        expected_settings = {
            "use_source": "1",
            "prefix_mode": "input",
            "suffix_mode": "input",
        }
        self.assertEqual(expected_settings, controller.model.settings)
        self.assertEqual(3, controller.view.refresh_count)


if __name__ == "__main__":
    unittest.main()
