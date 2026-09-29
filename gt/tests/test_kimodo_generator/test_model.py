"""Pure authoring-state regression tests without Maya or Qt imports."""

import os
import tempfile
import unittest
from unittest.mock import patch
from types import SimpleNamespace
import sys
import subprocess
from gt.tools.kimodo_generator.kimodo_generator_model import KimodoGeneratorModel
from gt.tools.kimodo_generator.kimodo_generator_model import (
    default_download_directory, query_wsl_distributions, resolve_environment_python,
)
from gt.utils import kimodo
from gt.core.io import write_json


class TestKimodoGeneratorModel(unittest.TestCase):
    """Tests portable setups, stable IDs, constraints, and connection isolation."""

    def setUp(self):
        """Creates isolated in-memory authoring state."""
        self.model = KimodoGeneratorModel(preferences=False)
        self.temporary = tempfile.TemporaryDirectory()

    def tearDown(self):
        """Releases temporary test files."""
        self.temporary.cleanup()

    def test_setup_round_trip_and_token_exclusion(self):
        """Preserves named pose entries without exposing connection secrets."""
        self.model.token = "never serialize this"
        self.model.add_constraint({"type": "root2d", "frame_indices": [0], "smooth_root_2d": [[0, 0]]}, "Start")
        path = os.path.join(self.temporary.name, "setup.json")
        self.model.save_setup(path)
        loaded = KimodoGeneratorModel(preferences=False)
        loaded.load_setup(path)
        self.assertEqual(self.model.constraints, loaded.constraints)
        self.assertEqual(self.model.build_definition().as_dict(), loaded.build_definition().as_dict())
        self.assertNotIn("token", self.model.snapshot())

    def test_import_splits_multiple_keys(self):
        """Makes each native key independently editable and gives it a unique ID."""
        path = os.path.join(self.temporary.name, "constraints.json")
        write_json(path, [{"type": "root2d", "frame_indices": [0, 29], "smooth_root_2d": [[0, 0], [1, 2]]}])
        self.model.import_constraints(path)
        self.assertEqual(2, len(self.model.constraints))
        self.assertEqual([29], self.model.constraints[1]["parameters"]["frame_indices"])
        self.assertNotEqual(self.model.constraints[0]["id"], self.model.constraints[1]["id"])
        self.model.constraints[0]["enabled"] = False
        self.assertEqual(1, len(self.model.build_definition().as_dict()["constraints"]))

    def test_duplicate_timing_and_bounds(self):
        """Rejects overlapping constraints and out-of-range native indices."""
        constraint = {"type": "root2d", "frame_indices": [0], "smooth_root_2d": [[0, 0]]}
        self.model.add_constraint(constraint)
        self.model.add_constraint(constraint)
        with self.assertRaises(ValueError):
            self.model.build_definition()
        with self.assertRaisesRegex(ValueError, "Constraint frame 121.*frames 1 through 120"):
            kimodo.validate_constraints([dict(constraint, frame_indices=[120])], frame_count=120)

    def test_distribute_constraint_frames_spans_the_clip(self):
        """Places ordered path keys from the first through final generated frame."""
        self.assertEqual([0, 24, 47], kimodo.distribute_constraint_frames(3, 48))
        self.assertEqual([0, 39], kimodo.distribute_constraint_frames(2, 40))
        with self.assertRaisesRegex(ValueError, "more path transforms"):
            kimodo.distribute_constraint_frames(4, 3)

    def test_multiple_prompts_samples_and_old_definitions(self):
        """Accepts sequences and fills defaults when loading milestone-one definitions."""
        definition = kimodo.KimodoGenerationDefinition("", prompts=[
            {"text": "Walk", "duration_seconds": 2}, {"text": "Turn", "duration_seconds": 2}], num_samples=3)
        self.assertEqual(3, definition.as_dict()["parameters"]["num_samples"])
        data = definition.as_dict()
        for key in ("guidance", "heading", "transition_frames"):
            data["parameters"].pop(key)
        loaded = kimodo.KimodoGenerationDefinition.from_dict(data).as_dict()
        self.assertEqual([2.0, 2.0], loaded["parameters"]["guidance"])

    def test_generation_sample_limit_matches_kimodo_demo(self):
        """Accepts the demo's 10-sample maximum and rejects higher counts."""
        definition = kimodo.KimodoGenerationDefinition("Walk", num_samples=10)
        self.assertEqual(10, definition.as_dict()["parameters"]["num_samples"])
        with self.assertRaisesRegex(ValueError, "1 through 10"):
            kimodo.KimodoGenerationDefinition("Walk", num_samples=11)

    def test_history_keeps_origin_server(self):
        """Keeps old jobs associated with the URL that accepted them."""
        connection = kimodo.KimodoConnection(url="http://localhost:9000")
        self.model.add_job({"job_id": "test", "status": "queued"}, connection)
        self.model.connection["url"] = "http://localhost:9001"
        self.assertEqual("http://localhost:9000", self.model.jobs[0]["url"])

    def test_prompt_frame_mode_and_import_timing_preferences_restore(self):
        """Persists frame entry and auto-import timing toggles with compatible defaults."""
        self.model.prompt_durations_in_frames = True
        self.model.auto_frame_rate = False
        self.model.auto_frame_range = False
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(self.model.snapshot())
        self.assertTrue(restored.prompt_durations_in_frames)
        self.assertFalse(restored.auto_frame_rate)
        self.assertFalse(restored.auto_frame_range)

        old_preferences = self.model.snapshot()
        old_preferences.pop("prompt_durations_in_frames")
        old_preferences.pop("auto_frame_rate")
        old_preferences.pop("auto_frame_range")
        restored.restore(old_preferences)
        self.assertFalse(restored.prompt_durations_in_frames)
        self.assertTrue(restored.auto_frame_rate)
        self.assertTrue(restored.auto_frame_range)

    def test_pose_preview_template_defaults_and_persists(self):
        """Makes new previews templates by default and retains the user's explicit choice."""
        self.assertTrue(self.model.pose_previews_template)
        saved = self.model.snapshot()
        saved.pop("pose_previews_template")
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(saved)
        self.assertTrue(restored.pose_previews_template)

        self.model.pose_previews_template = False
        restored.restore(self.model.snapshot())
        self.assertFalse(restored.pose_previews_template)

    def test_curve_sample_count_defaults_clamps_and_persists(self):
        """Restores a valid automatic curve-sample count, defaulting older preferences to four."""
        self.assertEqual(4, self.model.path_curve_samples)
        saved = self.model.snapshot()
        saved.pop("path_curve_samples")
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(saved)
        self.assertEqual(4, restored.path_curve_samples)

        saved["path_curve_samples"] = 8
        restored.restore(saved)
        self.assertEqual(8, restored.path_curve_samples)
        saved["path_curve_samples"] = 10000
        restored.restore(saved)
        self.assertEqual(7200, restored.path_curve_samples)

    def test_package_cache_default_and_saved_override(self):
        """Resolves the shared cache while preserving an explicitly chosen folder."""
        from gt.core import prefs

        cache = SimpleNamespace(cache_dir=self.temporary.name)
        with patch.object(prefs, "PackageCache", return_value=cache):
            expected = os.path.join(self.temporary.name, "kimodo", "downloads")
            self.assertEqual(expected, default_download_directory())
            restored = KimodoGeneratorModel(preferences=False)
        chosen = os.path.join(self.temporary.name, "chosen")
        self.model.set_output_directory(chosen)
        restored.restore(self.model.snapshot())
        self.assertEqual(chosen, restored.output_directory)

    def test_invalid_download_folder_does_not_replace_setting(self):
        """Rejects relative destinations and file paths without changing the prior target."""
        previous = self.model.output_directory
        for path in ("", "relative/results", __file__):
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.model.set_output_directory(path)
        self.assertEqual(previous, self.model.output_directory)

    def test_query_wsl_unicode_and_failure(self):
        """Decodes UTF-16 and UTF-8 without treating errors as distribution names."""
        for encoding in ("utf-16", "utf-16-le", "utf-8"):
            response = SimpleNamespace(returncode=0, stderr=b"",
                                       stdout="Ubuntu-26.04\r\nDebian\r\nUbuntu-26.04\r\n".encode(encoding))
            with patch.object(subprocess, "run", return_value=response) as run:
                self.assertEqual(["Ubuntu-26.04", "Debian"], query_wsl_distributions())
                self.assertEqual(["wsl.exe", "--list", "--quiet"], run.call_args.args[0])
        with patch.object(subprocess, "run", side_effect=FileNotFoundError):
            with self.assertRaisesRegex(ValueError, "Check that WSL is installed"):
                query_wsl_distributions()

    def test_environment_folder_resolution(self):
        """Finds interpreters without shell interpolation or losing WSL environment paths."""
        with patch.object(os.path, "isfile", return_value=True):
            native = resolve_environment_python(self.temporary.name, "native")
            self.assertEqual(os.path.join(self.temporary.name, "Scripts", "python.exe"), native)
            linux = resolve_environment_python(r"\\wsl.localhost\Ubuntu-26.04\home\user\kimodo_env",
                                                "wsl", "Ubuntu-26.04")
            self.assertEqual("/home/user/kimodo_env/bin/python", linux)
            with self.assertRaisesRegex(ValueError, "belongs to Debian"):
                resolve_environment_python(r"\\wsl$\Debian\home\user\env", "wsl", "Ubuntu-26.04")
        with patch.object(os.path, "isfile", return_value=False), self.assertRaises(ValueError):
            resolve_environment_python(self.temporary.name, "native")

    def test_wsl_interpreter_symlink_is_checked_inside_linux(self):
        """Accepts Linux virtual-environment symlinks that Windows cannot resolve."""
        with patch.object(os.path, "isfile", return_value=False):
            with patch.object(subprocess, "run", return_value=SimpleNamespace(returncode=0)) as run:
                result = resolve_environment_python(r"\\wsl.localhost\Ubuntu\home\user name\env", "wsl", "Ubuntu")
        self.assertEqual("/home/user name/env/bin/python", result)
        self.assertEqual(["wsl.exe", "--distribution", "Ubuntu", "--exec", "test",
                          "-f", result, "-a", "-x", result], run.call_args.args[0])

    def test_humanik_preferences_round_trip(self):
        """Persists optional HIK overrides while old preferences get empty defaults."""
        from gt.tools.kimodo_generator.kimodo_generator_hik import default_settings

        model = KimodoGeneratorModel(preferences=False)
        self.assertEqual(default_settings(), model.humanik)
        model.humanik.update(character_name="Custom", reference_frame=0, lock_definition=False)
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(model.snapshot())
        self.assertEqual(model.humanik, restored.humanik)
        old = model.snapshot()
        old.pop("humanik")
        restored.restore(old)
        self.assertEqual(default_settings(), restored.humanik)

    def test_pose_authoring_option_and_removed_target_preferences(self):
        """Retains local authoring options but drops obsolete target-rig settings on save."""
        self.model.definition["maya"]["auto_humanik"] = False
        snapshot = self.model.snapshot()
        snapshot["humanik_target"] = {"rig_path": "old_target.ma"}
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(snapshot)
        self.assertEqual(False, restored.definition["maya"]["auto_humanik"])
        self.assertNotIn("humanik_target", restored.snapshot())
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "setup.json")
            restored.save_setup(path)
            self.model.load_setup(path)
            self.assertEqual(False, self.model.definition["maya"]["auto_humanik"])

    def test_pose_translation_limit_definition_option_is_backward_compatible(self):
        """Persists the translation-limit choice and upgrades definitions without the new key."""
        definition = kimodo.KimodoGenerationDefinition("Walk", limit_body_joint_translations=False)
        data = definition.as_dict()
        self.assertFalse(data["maya"]["limit_body_joint_translations"])

        legacy_data = dict(data)
        legacy_data["maya"] = dict(data["maya"])
        legacy_data["maya"].pop("limit_body_joint_translations")
        restored = kimodo.KimodoGenerationDefinition.from_dict(legacy_data)
        self.assertTrue(restored.as_dict()["maya"]["limit_body_joint_translations"])

    def test_history_is_not_silently_truncated_and_auto_download_persists(self):
        """Keeps every tracked job available for explicit cleanup after restart."""
        self.model.auto_download = True
        self.model.jobs = [{"job_id": str(index), "status": "succeeded", "downloading": True} for index in range(130)]
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(self.model.snapshot())
        self.assertEqual(True, restored.auto_download)
        self.assertEqual(130, len(restored.jobs))
        self.assertNotIn("downloading", restored.jobs[0])

    def test_automatic_results_defaults_and_explicit_preferences(self):
        """Checks the complete automatic processing flow by default and preserves saved opt-outs."""
        self.assertEqual((True, True), (self.model.auto_download, self.model.auto_maya_file))
        self.assertEqual((True, True, True), (self.model.auto_import_maya,
                                               self.model.auto_import_all_samples, self.model.auto_clear_scene))
        snapshot = self.model.snapshot()
        snapshot.pop("auto_download")
        snapshot.pop("auto_maya_file")
        snapshot.pop("auto_import_maya")
        snapshot.pop("auto_clear_scene")
        self.model.restore(snapshot)
        self.assertEqual((True, True), (self.model.auto_download, self.model.auto_maya_file))
        self.assertEqual((True, True, True), (self.model.auto_import_maya,
                                               self.model.auto_import_all_samples, self.model.auto_clear_scene))
        snapshot.update(auto_download=False, auto_maya_file=False,
                        auto_import_maya=True, auto_import_all_samples=False, auto_clear_scene=True,
                        jobs=[{"job_id": "test", "exporting_maya": True}])
        self.model.restore(snapshot)
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(self.model.snapshot())
        self.assertEqual((False, False), (restored.auto_download, restored.auto_maya_file))
        self.assertEqual((True, False, True), (restored.auto_import_maya,
                                                restored.auto_import_all_samples, restored.auto_clear_scene))
        self.assertNotIn("exporting_maya", restored.jobs[0])

    def test_bridge_console_defaults_on_and_persists(self):
        """Migrates old preferences to a visible console and retains an explicit opt-out."""
        self.assertEqual(True, self.model.connection["show_console"])
        old = self.model.snapshot()
        old["connection"].pop("show_console")
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(old)
        self.assertEqual(True, restored.connection["show_console"])
        restored.connection["show_console"] = False
        saved = KimodoGeneratorModel(preferences=False)
        saved.restore(restored.snapshot())
        self.assertEqual(False, saved.connection["show_console"])

    def test_auto_connect_defaults_off_and_persists(self):
        """Requires an explicit opt-in before connecting on tool launch."""
        self.assertFalse(self.model.connection["auto_connect"])
        self.model.connection["auto_connect"] = True
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(self.model.snapshot())
        self.assertTrue(restored.connection["auto_connect"])

        legacy_state = self.model.snapshot()
        legacy_state["connection"].pop("auto_connect")
        legacy_restored = KimodoGeneratorModel(preferences=False)
        legacy_restored.restore(legacy_state)
        self.assertFalse(legacy_restored.connection["auto_connect"])

    def test_table_widths_round_trip_and_reject_invalid_values(self):
        """Persists named user widths without accepting malformed preference payloads."""
        self.model.table_widths = {"jobs": [120, 180, 95, 260]}
        restored = KimodoGeneratorModel(preferences=False)
        restored.restore(self.model.snapshot())
        self.assertEqual({"jobs": [120, 180, 95, 260]}, restored.table_widths)
        snapshot = self.model.snapshot()
        snapshot["table_widths"] = {"jobs": [120, -1], "unknown": [100], "prompts": "invalid"}
        restored.restore(snapshot)
        self.assertEqual({}, restored.table_widths)


if __name__ == "__main__":
    unittest.main()
