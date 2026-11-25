"""Unit tests for the import-safe Animation Evaluator model."""

import tempfile
import unittest
import os

from gt.tools.anim_evaluator import anim_evaluator_model as model_module
from gt.core.motion_eval import presets
from gt.core.motion_eval import templates


class FakePrefs:
    """In-memory preference store."""

    def __init__(self, state=None):
        """Initializes the store.

        Args:
            state (dict, optional): Stored tool state.
        """
        self.data = {"state": state or {}}
        self.save_count = 0

    def get_raw_preferences(self):
        """Gets stored data.

        Returns:
            dict: Stored data.
        """
        return self.data

    def set_raw_preferences(self, data):
        """Replaces stored data.

        Args:
            data (dict): New data.
        """
        self.data = data

    def save(self):
        """Counts saves."""
        self.save_count += 1


class TestAnimEvaluatorModel(unittest.TestCase):
    def test_defaults_use_builtin_template_and_biped_preset(self):
        model = model_module.AnimEvaluatorModel(prefs=False)
        self.assertEqual(templates.DEFAULT_TEMPLATE_KEY, model.get_setting("template_key"))
        self.assertEqual("biped", model.get_mode())

    def test_invalid_preference_types_are_ignored(self):
        model = model_module.AnimEvaluatorModel(prefs=FakePrefs({"custom_start": "abc", "node_list": 5}))
        self.assertEqual(1, model.get_setting("custom_start"))
        self.assertEqual("", model.get_setting("node_list"))

    def test_set_mode_persists(self):
        prefs = FakePrefs()
        model = model_module.AnimEvaluatorModel(prefs=prefs)
        model.set_mode("general")
        self.assertEqual("general", prefs.data["state"]["preset"]["mode"])

    def test_preset_is_stored_compact(self):
        model = model_module.AnimEvaluatorModel(prefs=False)
        model.set_preset(presets.set_check_value(model.get_preset(), "jitter", "weight", 2.0))
        self.assertEqual({"jitter": {"weight": 2.0}}, model.get_preset()["checks"])

    def test_edited_template_becomes_custom(self):
        model = model_module.AnimEvaluatorModel(prefs=False)
        template = templates.create_template("Edited", {"hips": "root_hips"})
        model.update_template(template)
        self.assertEqual(model_module.TEMPLATE_SOURCE_CUSTOM, model.get_setting("template_source"))
        self.assertEqual(["root_hips"], model.template["roles"]["hips"])

    def test_template_file_round_trip(self):
        model = model_module.AnimEvaluatorModel(prefs=False)
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "skeleton.json")
            model.save_template_file(file_path)
            loaded = model_module.AnimEvaluatorModel(prefs=False)
            loaded.load_template_file(file_path)
        self.assertEqual(model_module.TEMPLATE_SOURCE_FILE, loaded.get_setting("template_source"))
        self.assertEqual(model.template["roles"], loaded.template["roles"])

    def test_missing_template_file_falls_back_quietly(self):
        state = {"template_source": model_module.TEMPLATE_SOURCE_FILE, "template_path": "Z:/missing/skeleton.json"}
        model = model_module.AnimEvaluatorModel(prefs=FakePrefs(state))
        self.assertEqual(model_module.TEMPLATE_SOURCE_BUILTIN, model.get_setting("template_source"))

    def test_node_names_are_split(self):
        model = model_module.AnimEvaluatorModel(prefs=False)
        model.set_setting("node_list", "prop_ctrl, *:root; extra")
        self.assertEqual(["prop_ctrl", "*:root", "extra"], model.get_node_names())

    def test_reset_restores_defaults(self):
        model = model_module.AnimEvaluatorModel(prefs=False)
        model.set_mode("general")
        model.reset_to_defaults()
        self.assertEqual("biped", model.get_mode())


if __name__ == "__main__":
    unittest.main()
