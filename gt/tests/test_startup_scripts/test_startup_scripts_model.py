"""Tests for the pure Startup Scripts model and runtime helpers."""

from gt.tools.startup_scripts import startup_scripts_model as startup_model
from gt.tools.startup_scripts import startup_scripts_runtime as startup_runtime
import json
import os
import shutil
import tempfile
import unittest


class FakePrefs:
    """Small file-backed Prefs substitute used to test stored-data guards."""

    def __init__(self, file_path):
        """Initializes an empty preference payload.

        Args:
            file_path (str): Preference JSON file path.
        """
        self.file_name = file_path
        self.preferences = {}
        if os.path.isfile(file_path):
            with open(file_path, "r", encoding="utf-8") as preference_file:
                self.preferences = json.load(preference_file)

    def get_raw_preferences(self):
        """Gets the stored preference dictionary.

        Returns:
            dict: Raw preference payload.
        """
        return self.preferences

    def save(self):
        """Persists the preference payload to its test file."""
        with open(self.file_name, "w", encoding="utf-8") as preference_file:
            json.dump(self.preferences, preference_file, indent=4)


class TestStartupScriptsModel(unittest.TestCase):
    """Validates Startup Scripts data without requiring Maya or Qt."""

    def setUp(self):
        """Creates a unique test workspace and empty preference object."""
        self.temp_dir = tempfile.mkdtemp(prefix="gt_startup_scripts_test_")
        self.preference_path = os.path.join(self.temp_dir, "startup_scripts.json")
        self.prefs = FakePrefs(self.preference_path)

    def tearDown(self):
        """Removes the isolated test workspace."""
        if os.path.isdir(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_default_script_has_empty_inline_source_and_output_messages_enabled(self):
        """Ensures the first unsaved configuration uses the requested defaults."""
        script = startup_model.create_default_script()

        expected = ""
        result = script.get("script_text")
        self.assertEqual(expected, result)
        expected = True
        result = script.get("print_execution_message")
        self.assertEqual(expected, result)
        expected = startup_model.RUN_MODE_MAYA_STARTUP
        result = script.get("run_mode")
        self.assertEqual(expected, result)

    def test_runtime_guard_requires_an_existing_valid_preference_file(self):
        """Ensures in-memory or malformed data cannot trigger startup execution."""
        data = {
            "schema_version": startup_model.PREFS_SCHEMA_VERSION,
            "scripts": [startup_model.create_default_script()],
        }
        self.prefs.preferences[startup_model.PREFS_KEY_CONFIGURATION] = data
        model = startup_model.StartupScriptsModel(prefs=self.prefs)

        expected = False
        result = model.has_valid_preferences_file()
        self.assertEqual(expected, result)

        self.prefs.save()
        expected = True
        result = model.has_valid_preferences_file()
        self.assertEqual(expected, result)

        self.prefs.preferences[startup_model.PREFS_KEY_CONFIGURATION]["scripts"][0]["run_mode"] = "Bad Value"
        self.prefs.save()
        expected = False
        result = model.has_valid_preferences_file()
        self.assertEqual(expected, result)

    def test_model_saves_and_reloads_multiple_configurations(self):
        """Ensures script configuration data is persisted through the Prefs interface."""
        model = startup_model.StartupScriptsModel(prefs=self.prefs)
        added_script = model.add_script(name="Open Files")
        model.update_script(
            added_script.get("id"),
            {"run_mode": startup_model.RUN_MODE_FILE_OPEN, "script_text": "print('opened')"},
        )

        reloaded_model = startup_model.StartupScriptsModel(prefs=FakePrefs(self.preference_path))

        expected = True
        result = reloaded_model.has_valid_preferences_file()
        self.assertEqual(expected, result)
        result = reloaded_model.get_script(added_script.get("id"))
        expected = startup_model.RUN_MODE_FILE_OPEN
        self.assertEqual(expected, result.get("run_mode"))
        expected = "print('opened')"
        self.assertEqual(expected, result.get("script_text"))

    def test_external_files_and_directories_are_collected_in_stable_order(self):
        """Ensures explicit files run before directory content without duplicates."""
        explicit_path = os.path.join(self.temp_dir, "explicit.py")
        scripts_dir = os.path.join(self.temp_dir, "scripts")
        nested_dir = os.path.join(scripts_dir, "nested")
        os.makedirs(nested_dir)
        directory_first_path = os.path.join(scripts_dir, "a_directory.py")
        directory_second_path = os.path.join(nested_dir, "b_nested.py")
        for file_path in [explicit_path, directory_first_path, directory_second_path]:
            with open(file_path, "w", encoding="utf-8") as script_file:
                script_file.write("pass\n")
        script = startup_model.create_default_script()
        script["external_files"] = [
            {"path": explicit_path, "enabled": True},
            {"path": explicit_path, "enabled": True},
        ]
        script["script_directories"] = [{"path": scripts_dir, "enabled": True}]

        result = startup_model.get_script_paths(script)

        expected = [
            os.path.normpath(explicit_path),
            os.path.normpath(directory_first_path),
            os.path.normpath(directory_second_path),
        ]
        self.assertEqual(expected, result)

    def test_runtime_executes_inline_external_and_directory_sources_in_order(self):
        """Ensures the configured source order matches the tool's UI explanation."""
        external_path = os.path.join(self.temp_dir, "external.py")
        scripts_dir = os.path.join(self.temp_dir, "directory_scripts")
        os.makedirs(scripts_dir)
        directory_path = os.path.join(scripts_dir, "directory.py")
        with open(external_path, "w", encoding="utf-8") as script_file:
            script_file.write("execution_log.append('external')\n")
        with open(directory_path, "w", encoding="utf-8") as script_file:
            script_file.write("execution_log.append('directory')\n")
        script = startup_model.create_default_script()
        script["run_mode"] = startup_model.RUN_MODE_BOTH
        script["print_execution_message"] = False
        script["script_text"] = "execution_log.append('inline')"
        script["external_files"] = [{"path": external_path, "enabled": True}]
        script["script_directories"] = [{"path": scripts_dir, "enabled": True}]
        execution_log = []

        result = startup_runtime.run_script_configuration(
            script,
            event_name=startup_runtime.EVENT_MAYA_STARTUP,
            extra_globals={"execution_log": execution_log},
        )

        expected = True
        self.assertEqual(expected, result)
        expected = ["inline", "external", "directory"]
        self.assertEqual(expected, execution_log)

    def test_file_open_mode_does_not_run_during_maya_startup(self):
        """Ensures the requested trigger filters a configuration before execution."""
        script = startup_model.create_default_script()
        script["run_mode"] = startup_model.RUN_MODE_FILE_OPEN
        script["print_execution_message"] = False
        script["script_text"] = "execution_log.append('ran')"
        execution_log = []

        result = startup_runtime.run_script_configuration(
            script,
            event_name=startup_runtime.EVENT_MAYA_STARTUP,
            extra_globals={"execution_log": execution_log},
        )

        expected = False
        self.assertEqual(expected, result)
        expected = []
        self.assertEqual(expected, execution_log)

    def test_sample_script_is_discoverable_and_sets_expected_scene_timing(self):
        """Ensures the requested 30fps sample is packaged with the tool."""
        samples = startup_model.get_sample_scripts()
        sample_paths = {sample.get("relative_path"): sample.get("path") for sample in samples}

        expected_path = "set_scene_defaults.py"
        self.assertIn(expected_path, sample_paths)
        source_text = startup_model.load_script_file(sample_paths[expected_path])
        self.assertIn('FRAME_RATE = "ntsc"', source_text)
        self.assertIn("minTime=TIMELINE_START_FRAME", source_text)
        self.assertIn("maxTime=TIMELINE_END_FRAME", source_text)


if __name__ == "__main__":
    unittest.main()
