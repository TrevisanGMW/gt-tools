"""Pure HumanIK tool state and input-validation regressions."""

import json
import os
import tempfile
import unittest
from unittest.mock import Mock

from gt.tools.anim_hik_utils import anim_hik_utils_model as model_module


class TestAnimHikUtilsModel(unittest.TestCase):
    """Validates settings and portable file inputs without Maya."""

    def test_preferences_validate_types_and_exclude_scene_state(self):
        """Malformed options cannot enable flags or persist character names."""
        prefs = Mock()
        prefs.get_raw_preferences.return_value = {
            "state": {"world_space": "False", "affect_center": True, "prefix": 4, "character": "old"}
        }
        model = model_module.AnimHikUtilsModel(prefs=prefs)
        self.assertFalse(model.settings["world_space"])
        self.assertTrue(model.settings["affect_center"])
        self.assertEqual("", model.settings["prefix"])
        model.character = "hero"
        model.save_preferences()
        self.assertNotIn("character", prefs.set_raw_preferences.call_args.args[0]["state"])

    def test_reset_preserves_session_selection_and_clipboard(self):
        """Reset affects options without losing transient user data."""
        model = model_module.AnimHikUtilsModel(prefs=False)
        model.character = "hero"
        model.copied_properties = {"Scale": 1.0}
        model.update_settings({"world_space": True})
        model.reset_to_defaults()
        self.assertEqual(model_module.DEFAULT_SETTINGS, model.settings)
        self.assertEqual("hero", model.character)
        self.assertEqual({"Scale": 1.0}, model.copied_properties)

    def test_names_reject_native_command_injection(self):
        """Only safe Maya identifiers reach native HumanIK wrappers."""
        self.assertEqual("hero:Character", model_module.validate_node_name(" hero:Character "))
        for name in ('hero"; delete -all;', "", "bad name", "a|b", "9hero"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                model_module.validate_node_name(name)

    def test_xml_mapping_preserves_prefix_then_replacement_order(self):
        """Preview resolves bone names exactly as the shared importer does."""
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "definition.xml")
            with open(path, "w", encoding="utf-8") as stream:
                stream.write('<config_root><match_list><item key="Hips" value="Hips"/>'
                             '<item key="Spine" value=""/></match_list></config_root>')
            result = model_module.read_definition(path, "source:", "source:", "target:")
            self.assertEqual([("Hips", "target:Hips")], result)

    def test_xml_rejects_empty_find_before_reading(self):
        """Replacing an empty string must not inject namespace text between letters."""
        with self.assertRaisesRegex(ValueError, "Enter namespace"):
            model_module.read_definition("unused.xml", replace_namespace="hero:")

    def test_xml_rejects_empty_duplicate_and_wrong_schema(self):
        """Invalid XML cannot reach scene operations."""
        samples = (
            '<config_root><match_list/></config_root>',
            '<config_root><match_list><item key="Hips" value="a"/>'
            '<item key="Hips" value="b"/></match_list></config_root>',
            '<other><item key="Hips" value="a"/></other>',
        )
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "definition.xml")
            for sample in samples:
                with open(path, "w", encoding="utf-8") as stream:
                    stream.write(sample)
                with self.subTest(sample=sample), self.assertRaises(ValueError):
                    model_module.read_definition(path)

    def test_properties_reject_nested_and_nonfinite_values(self):
        """Property import rejects pose files and non-finite numeric payloads."""
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "properties.json")
            for data in ({}, [], {"controls": {}}, {"Scale": float("nan")}):
                with open(path, "w", encoding="utf-8") as stream:
                    json.dump(data, stream)
                with self.subTest(data=data), self.assertRaises(ValueError):
                    model_module.read_properties(path)
            expected = {"Scale": 1.5, "Enabled": True, "Label": "retarget"}
            with open(path, "w", encoding="utf-8") as stream:
                json.dump(expected, stream)
            self.assertEqual(expected, model_module.read_properties(path))


if __name__ == "__main__":
    unittest.main()
