"""Tests for the Auto Rigger New Scene option definitions."""

import unittest

import gt.tools.auto_rigger.rigger_scene_options as tools_rig_scene_opts


class TestRiggerSceneOptions(unittest.TestCase):
    """Tests pure scene option helpers without Maya."""

    def test_default_scene_options_cover_all_definitions(self):
        """Creates a default value for every known option."""
        result = tools_rig_scene_opts.get_default_scene_options()

        expected = [option.key for option in tools_rig_scene_opts.get_scene_option_definitions()]
        self.assertEqual(expected, list(result.keys()))
        self.assertEqual("centimeter", result.get("linear_unit"))

    def test_disabling_option_removes_key_from_copy(self):
        """Removes disabled options without mutating the original dictionary."""
        original = {"linear_unit": "meter", "grid_size": 10.0}

        result = tools_rig_scene_opts.get_updated_scene_options(original, key="grid_size", is_enabled=False)

        expected = {"linear_unit": "meter"}
        self.assertEqual(expected, result)
        self.assertEqual({"linear_unit": "meter", "grid_size": 10.0}, original)

    def test_enabling_option_without_value_uses_default(self):
        """Uses the option default when enabling a missing option."""
        result = tools_rig_scene_opts.get_updated_scene_options({}, key="grid_divisions", is_enabled=True)

        expected = {"grid_divisions": 5}
        self.assertEqual(expected, result)

    def test_enabling_option_coerces_value_type(self):
        """Converts values to the type expected by the option."""
        result = tools_rig_scene_opts.get_updated_scene_options({}, key="grid_divisions", is_enabled=True, value=7.6)

        expected = {"grid_divisions": 8}
        self.assertEqual(expected, result)

    def test_numeric_frame_rate_is_normalized(self):
        """Stores numeric frame rates using the fps string format."""
        result = tools_rig_scene_opts.get_updated_scene_options({"frame_rate": 24}, key="frame_rate", is_enabled=True)

        expected = {"frame_rate": "24fps"}
        self.assertEqual(expected, result)

    def test_unknown_keys_are_reported_and_preserved(self):
        """Keeps keys without definitions so they remain editable as raw data."""
        original = {"linear_unit": "meter", "playback_frame_end_ceil": True}

        result_keys = tools_rig_scene_opts.get_unknown_scene_option_keys(original)
        result_options = tools_rig_scene_opts.get_updated_scene_options(original, "linear_unit", is_enabled=False)

        self.assertEqual(["playback_frame_end_ceil"], result_keys)
        self.assertEqual({"playback_frame_end_ceil": True}, result_options)

    def test_invalid_value_falls_back_to_default(self):
        """Uses the default when a stored value cannot be converted."""
        option = tools_rig_scene_opts.get_scene_option_definition("grid_size")

        result = option.coerce_value("not_a_number")

        expected = 12.0
        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
