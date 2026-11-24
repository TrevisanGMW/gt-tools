import os
import shutil
import sys
import tempfile
import unittest

# Import Tested Script
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
from gt.tools.multi_file_importer import multi_file_importer_constants as constants
from gt.tools.multi_file_importer import multi_file_importer_model as model


class TestMultiFileImporterModel(unittest.TestCase):
    """Checks the file list, settings and persistence of the Multi-File Importer model."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="gt_multi_file_importer_test_")
        os.makedirs(os.path.join(self.temp_dir, "sub"))
        for relative_path in ["b.ma", "a.fbx", "notes.txt", os.path.join("sub", "c.bvh")]:
            open(os.path.join(self.temp_dir, relative_path), "w").close()
        self.prefs = model.MemoryPrefs()
        self.model = model.MultiFileImporterModel(prefs=self.prefs)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def get_names(self):
        return [entry.name for entry in self.model.entries]

    def test_add_folder_non_recursive(self):
        result = self.model.add_paths([self.temp_dir])
        self.assertEqual(["a.fbx", "b.ma"], self.get_names())
        self.assertEqual({"added": 2, "duplicates": 0, "unsupported": 0}, result)

    def test_add_folder_recursive_and_duplicates(self):
        self.model.add_paths([self.temp_dir], recursive=True)
        result = self.model.add_paths([os.path.join(self.temp_dir, "b.ma"), os.path.join(self.temp_dir, "notes.txt")])
        self.assertEqual(["a.fbx", "b.ma", "c.bvh"], self.get_names())
        self.assertEqual({"added": 0, "duplicates": 1, "unsupported": 1}, result)

    def test_extension_filter(self):
        self.model.update_settings({"extension_filter": "bvh", "recursive": True})
        self.model.add_paths([self.temp_dir])
        self.assertEqual(["c.bvh"], self.get_names())

    def test_remove_sort_and_enable(self):
        self.model.add_paths([self.temp_dir], recursive=True)
        self.model.sort_entries(constants.SORT_REVERSE)
        self.assertEqual(["c.bvh", "b.ma", "a.fbx"], self.get_names())
        self.model.set_entry_enabled(self.model.entries[0].entry_id, False)
        self.assertEqual(["b.ma", "a.fbx"], [entry.name for entry in self.model.get_enabled_entries()])
        self.assertEqual(1, self.model.remove_entries([self.model.entries[1].entry_id]))
        self.assertEqual(["c.bvh", "a.fbx"], self.get_names())

    def test_normalize_settings_drops_invalid_values(self):
        result = model.normalize_settings({"offset_mode": "Spiral", "grid_columns": "-3", "frame_rate_custom": "abc",
                                           "line_step_x": "12.5", "unknown_key": 1})
        self.assertEqual(constants.OFFSET_NONE, result["offset_mode"])
        self.assertEqual(0, result["grid_columns"])
        self.assertEqual("30", result["frame_rate_custom"])
        self.assertEqual(12.5, result["line_step_x"])
        self.assertNotIn("unknown_key", result)

    def test_validate(self):
        errors, _ = self.model.validate()
        self.assertEqual(1, len(errors))
        self.model.add_paths([self.temp_dir])
        self.model.update_settings({"timeline_mode": constants.TIMELINE_MANUAL, "timeline_start": 50,
                                    "timeline_end": 10})
        errors, _ = self.model.validate()
        self.assertEqual(["Manual timeline start must be lower than or equal to the end."], errors)

    def test_namespaces_and_group_names(self):
        file_path = os.path.join(self.temp_dir, "1 walk-cycle.fbx")
        self.assertEqual("_1_walk_cycle", self.model.build_namespace(file_path, 3))
        self.model.update_settings({"namespace_mode": constants.NAMESPACE_CUSTOM, "namespace_template": "take_{index}"})
        self.assertEqual("take_03", self.model.build_namespace(file_path, 3))
        self.model.update_settings({"namespace_mode": constants.NAMESPACE_NONE})
        self.assertEqual("", self.model.build_namespace(file_path, 3))
        self.model.update_settings({"load_mode": constants.LOAD_MODE_REFERENCE})
        self.assertEqual("_1_walk_cycle", self.model.build_namespace(file_path, 3))
        self.assertEqual("_1_walk_cycle_grp", self.model.build_group_name(file_path, 3))

    def test_persistence_round_trip(self):
        self.model.update_settings({"offset_mode": constants.OFFSET_GRID})
        self.model.set_format_settings("bvh", {"scale": 3.0})
        self.model.set_section_state(constants.SECTION_REVIEW, True)
        self.model.save_preferences()
        reloaded_model = model.MultiFileImporterModel(prefs=self.prefs)
        self.assertEqual(constants.OFFSET_GRID, reloaded_model.settings["offset_mode"])
        self.assertEqual(3.0, reloaded_model.get_format_settings("bvh")["scale"])
        self.assertTrue(reloaded_model.section_states[constants.SECTION_REVIEW])
        reloaded_model.reset_preferences()
        self.assertEqual(constants.DEFAULT_SETTINGS, reloaded_model.settings)

    def test_every_setting_persists(self):
        changed_settings = {"review_anti_aliasing_samples": "16", "post_script": "print(1)", "grid_columns": 4,
                            "reapply_scene_settings": False, "timeline_mode": constants.TIMELINE_STORED}
        self.model.update_settings(changed_settings)
        self.model.save_preferences()
        reloaded_model = model.MultiFileImporterModel(prefs=self.prefs)
        for key, value in changed_settings.items():
            self.assertEqual(value, reloaded_model.settings[key], key)

    def test_file_list_persistence_is_optional(self):
        self.model.add_paths([self.temp_dir])
        self.model.save_preferences()
        self.assertEqual([], model.MultiFileImporterModel(prefs=self.prefs).entries)
        self.model.update_settings({"keep_file_list": True})
        self.model.set_entry_enabled(self.model.entries[0].entry_id, False)
        self.model.save_preferences()
        reloaded_model = model.MultiFileImporterModel(prefs=self.prefs)
        self.assertEqual([("a.fbx", False), ("b.ma", True)],
                         [(entry.name, entry.enabled) for entry in reloaded_model.entries])

    def test_sections_start_collapsed_unless_remembered(self):
        self.model.set_section_state(constants.SECTION_PLACEMENT, True)
        self.assertFalse(any(self.model.get_startup_section_states().values()))
        self.model.update_settings({"remember_section_states": True})
        self.assertTrue(self.model.get_startup_section_states()[constants.SECTION_PLACEMENT])

    def test_export_and_import_settings(self):
        self.model.add_paths([self.temp_dir])
        self.model.update_settings({"offset_mode": constants.OFFSET_LINE, "include_files_in_export": True})
        self.model.set_format_settings("fbx", {"cameras": True})
        settings_path = os.path.join(self.temp_dir, "settings.json")
        self.model.export_settings(settings_path)
        other_model = model.MultiFileImporterModel(prefs=model.MemoryPrefs())
        added_count = other_model.import_settings(settings_path)
        self.assertEqual(2, added_count)
        self.assertEqual(constants.OFFSET_LINE, other_model.settings["offset_mode"])
        self.assertTrue(other_model.get_format_settings("fbx")["cameras"])
        with self.assertRaises(ValueError):
            other_model.apply_import_data({"tool": "something_else"})

    def test_check_actions(self):
        self.model.add_paths([self.temp_dir], recursive=True)
        first_id = self.model.entries[0].entry_id
        self.model.solo_entries([first_id])
        self.assertEqual(["a.fbx"], [entry.name for entry in self.model.get_enabled_entries()])
        self.model.invert_checks()
        self.assertEqual(["b.ma", "c.bvh"], [entry.name for entry in self.model.get_enabled_entries()])
        self.assertEqual(1, self.model.remove_unchecked())
        self.model.set_entries_enabled(None, False)
        self.assertEqual([], self.model.get_enabled_entries())

    def test_parse_pasted_paths(self):
        expected = ["C:/a.ma", "C:/b c.fbx", "D:/folder"]
        result = model.parse_pasted_paths('C:/a.ma\n  "C:/b c.fbx"\n\nfile:///D:/folder\n')
        self.assertEqual(expected, result)
