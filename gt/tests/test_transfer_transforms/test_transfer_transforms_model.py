"""Unit tests for Transfer Transforms model behavior."""

import json
import os
import tempfile
import unittest

from gt.tools.transfer_transforms.transfer_transforms_model import TransferTransformsModel


class MockPreferences:
    """Small Prefs-compatible test double."""

    def __init__(self, values=None):
        """Initializes stored values.

        Args:
            values (dict, optional): Initial preference values.
        """
        self.values = dict(values or {})
        self.save_count = 0

    def get_raw_preferences(self):
        """Gets stored preference values.

        Returns:
            dict: Stored preference values.
        """
        return dict(self.values)

    def set_raw_preferences(self, pref_dict):
        """Replaces stored preference values.

        Args:
            pref_dict (dict): New preference values.
        """
        self.values = dict(pref_dict)

    def save(self):
        """Records a save call."""
        self.save_count += 1


class TestTransferTransformsModel(unittest.TestCase):
    """Tests pure model behavior outside Maya."""

    def test_default_side_tags_use_short_prefixes(self):
        """Uses L_ and R_ as the default side tags."""
        model = TransferTransformsModel(preferences=MockPreferences())

        self.assertEqual("L_", model.settings.get("left_tag"))
        self.assertEqual("R_", model.settings.get("right_tag"))

    def test_load_preferences_preserves_defaults_for_missing_values(self):
        """Loads stored values without dropping unspecified defaults."""
        preferences = MockPreferences(
            {
                "tx_enabled": False,
                "left_tag": "lf_",
                "clipboard": {"tx": 12.5, "sx": "invalid"},
            }
        )

        model = TransferTransformsModel(preferences=preferences)

        self.assertFalse(model.settings.get("tx_enabled"))
        self.assertEqual("lf_", model.settings.get("left_tag"))
        self.assertTrue(model.settings.get("ry_enabled"))
        self.assertEqual(12.5, model.clipboard.get("tx"))
        self.assertEqual(1.0, model.clipboard.get("sx"))

    def test_set_setting_saves_known_value(self):
        """Saves a known setting through the injected Prefs object."""
        preferences = MockPreferences()
        model = TransferTransformsModel(preferences=preferences)

        result = model.set_setting("rz_inverted", True)

        self.assertTrue(result)
        self.assertTrue(preferences.values.get("rz_inverted"))
        self.assertEqual(1, preferences.save_count)

    def test_set_setting_rejects_unknown_key(self):
        """Does not accept arbitrary preference keys."""
        model = TransferTransformsModel(preferences=MockPreferences())

        result = model.set_setting("unknown", True)

        self.assertFalse(result)
        self.assertNotIn("unknown", model.settings)

    def test_clipboard_value_is_saved_as_preference(self):
        """Persists an edited clipboard channel immediately."""
        preferences = MockPreferences()
        model = TransferTransformsModel(preferences=preferences)

        result = model.set_clipboard_value("tx", 14.25)

        self.assertTrue(result)
        self.assertEqual(14.25, preferences.values.get("clipboard", {}).get("tx"))
        self.assertEqual(1, preferences.save_count)

    def test_set_clipboard_saves_all_values_once(self):
        """Persists values captured by Get TRS in one preferences write."""
        preferences = MockPreferences()
        model = TransferTransformsModel(preferences=preferences)

        model.set_clipboard({"tx": 2.0, "ry": 35.0, "sz": 1.5})

        clipboard = preferences.values.get("clipboard", {})
        self.assertEqual(2.0, clipboard.get("tx"))
        self.assertEqual(35.0, clipboard.get("ry"))
        self.assertEqual(1.5, clipboard.get("sz"))
        self.assertEqual(1, preferences.save_count)

    def test_build_side_pairs_uses_matching_tagless_names(self):
        """Pairs left and right nodes while retaining input order."""
        nodes = ["|rig|L_arm", "|rig|R_leg", "|rig|R_arm", "|rig|L_leg"]

        result = TransferTransformsModel.build_side_pairs(nodes, "L_", "R_")

        expected = [("|rig|L_arm", "|rig|R_arm"), ("|rig|L_leg", "|rig|R_leg")]
        self.assertEqual(expected, result)

    def test_build_side_pairs_rejects_empty_or_equal_tags(self):
        """Avoids ambiguous matching when tags cannot identify a side."""
        nodes = ["L_arm", "R_arm"]

        self.assertEqual([], TransferTransformsModel.build_side_pairs(nodes, "", "R_"))
        self.assertEqual([], TransferTransformsModel.build_side_pairs(nodes, "side", "side"))

    def test_reset_preferences_restores_and_saves_defaults(self):
        """Restores every default and writes the result."""
        preferences = MockPreferences()
        model = TransferTransformsModel(preferences=preferences)
        model.set_setting("left_tag", "custom", save=False)
        model.set_clipboard_value("tx", 20.0, save=False)

        model.reset_preferences()

        expected_preferences = dict(TransferTransformsModel.DEFAULT_SETTINGS)
        expected_preferences["clipboard"] = dict(TransferTransformsModel.DEFAULT_CLIPBOARD)
        self.assertEqual(TransferTransformsModel.DEFAULT_SETTINGS, model.settings)
        self.assertEqual(TransferTransformsModel.DEFAULT_CLIPBOARD, model.clipboard)
        self.assertEqual(expected_preferences, preferences.values)
        self.assertEqual(1, preferences.save_count)

    def test_transform_file_round_trip(self):
        """Writes and reads the current JSON schema."""
        records = [
            {
                "long_name": "|cube",
                "short_name": "cube",
                "translate": [1.0, 2.0, 3.0],
                "rotate": [4.0, 5.0, 6.0],
                "scale": [1.0, 1.0, 1.0],
            }
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "transforms.json")

            TransferTransformsModel.write_transform_file(file_path, records, "2.0.0")
            result = TransferTransformsModel.read_transform_file(file_path)

        self.assertEqual(records, result)

    def test_read_transform_file_rejects_unrelated_json(self):
        """Rejects JSON that does not use the current tool schema."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "other.json")
            with open(file_path, "w", encoding="utf-8") as output_file:
                json.dump({"objects": []}, output_file)

            with self.assertRaises(ValueError):
                TransferTransformsModel.read_transform_file(file_path)


if __name__ == "__main__":
    unittest.main()
