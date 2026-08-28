"""Tests for the pure Startup Scripts model and runtime helpers."""

from gt.tools import startup_scripts
from gt.tools.startup_scripts import startup_scripts_model as startup_model
from gt.tools.startup_scripts import startup_scripts_runtime as startup_runtime
import json
import os
import shutil
import tempfile
import unittest
from unittest import mock
from datetime import date


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
        expected = False
        result = script.get("run_interval_enabled")
        self.assertEqual(expected, result)
        expected = 1
        result = script.get("run_interval_value")
        self.assertEqual(expected, result)
        expected = startup_model.RUN_INTERVAL_DAYS
        result = script.get("run_interval_unit")
        self.assertEqual(expected, result)

    def test_run_modes_cover_each_supported_event_combination(self):
        """Ensures every useful Interactive Maya, mayapy, and File Open combination is available."""
        expected = [
            startup_model.RUN_MODE_INTERACTIVE_MAYA,
            startup_model.RUN_MODE_MAYAPY,
            startup_model.RUN_MODE_FILE_OPEN,
            startup_model.RUN_MODE_INTERACTIVE_MAYA_AND_MAYAPY,
            startup_model.RUN_MODE_INTERACTIVE_MAYA_AND_FILE_OPEN,
            startup_model.RUN_MODE_MAYAPY_AND_FILE_OPEN,
            startup_model.RUN_MODE_ALL,
        ]
        result = startup_model.RUN_MODE_VALUES
        self.assertEqual(expected, result)

        expected = [
            startup_model.RUN_MODE_INTERACTIVE_MAYA,
            startup_model.RUN_MODE_MAYAPY,
            startup_model.RUN_MODE_FILE_OPEN,
        ]
        result = startup_model.get_run_mode_events(startup_model.RUN_MODE_ALL)
        self.assertEqual(expected, result)

        expected = set(startup_model.RUN_MODE_VALUES)
        result = set(startup_model.RUN_MODE_TOOLTIPS)
        self.assertEqual(expected, result)

        expected = "user interface"
        result = startup_model.RUN_MODE_TOOLTIPS[startup_model.RUN_MODE_INTERACTIVE_MAYA]
        self.assertIn(expected, result)
        expected = "command-line Python interpreter"
        result = startup_model.RUN_MODE_TOOLTIPS[startup_model.RUN_MODE_MAYAPY]
        self.assertIn(expected, result)
        expected = "after a scene finishes opening"
        result = startup_model.RUN_MODE_TOOLTIPS[startup_model.RUN_MODE_FILE_OPEN]
        self.assertIn(expected, result)

        expected = 2
        result = startup_model.RUN_MODE_TOOLTIPS[startup_model.RUN_MODE_INTERACTIVE_MAYA].count("\n")
        self.assertEqual(expected, result)
        result = startup_model.RUN_MODE_TOOLTIPS[startup_model.RUN_MODE_MAYAPY].count("\n")
        self.assertEqual(expected, result)
        result = startup_model.RUN_MODE_TOOLTIPS[startup_model.RUN_MODE_FILE_OPEN].count("\n")
        self.assertEqual(expected, result)

    def test_legacy_run_modes_load_as_their_current_equivalents(self):
        """Ensures existing Startup Scripts preferences retain their prior behavior."""
        interactive_script = startup_model.create_default_script()
        interactive_script["run_mode"] = startup_model.LEGACY_RUN_MODE_MAYA_STARTUP
        both_script = startup_model.create_default_script()
        both_script["run_mode"] = startup_model.LEGACY_RUN_MODE_BOTH
        self.prefs.preferences[startup_model.PREFS_KEY_CONFIGURATION] = {
            "schema_version": startup_model.PREFS_SCHEMA_VERSION,
            "scripts": [interactive_script, both_script],
        }
        self.prefs.save()

        model = startup_model.StartupScriptsModel(prefs=FakePrefs(self.preference_path))

        expected = startup_model.RUN_MODE_INTERACTIVE_MAYA
        result = model.get_scripts()[0].get("run_mode")
        self.assertEqual(expected, result)
        expected = startup_model.RUN_MODE_INTERACTIVE_MAYA_AND_FILE_OPEN
        result = model.get_scripts()[1].get("run_mode")
        self.assertEqual(expected, result)

    def test_run_frequency_uses_calendar_days_weeks_months_and_years(self):
        """Ensures optional run frequency compares calendar dates correctly."""
        script = startup_model.create_default_script()
        script["last_run_date"] = "2024-01-01"

        expected = True
        result = startup_model.is_script_run_due(script, current_date=date(2024, 1, 1))
        self.assertEqual(expected, result)

        script["run_interval_enabled"] = True
        script["run_interval_value"] = 7
        script["run_interval_unit"] = startup_model.RUN_INTERVAL_DAYS
        expected = False
        result = startup_model.is_script_run_due(script, current_date=date(2024, 1, 7))
        self.assertEqual(expected, result)
        expected = True
        result = startup_model.is_script_run_due(script, current_date=date(2024, 1, 8))
        self.assertEqual(expected, result)

        script["last_run_date"] = "2024-01-01"
        script["run_interval_value"] = 2
        script["run_interval_unit"] = startup_model.RUN_INTERVAL_WEEKS
        expected = False
        result = startup_model.is_script_run_due(script, current_date=date(2024, 1, 14))
        self.assertEqual(expected, result)
        expected = True
        result = startup_model.is_script_run_due(script, current_date=date(2024, 1, 15))
        self.assertEqual(expected, result)

        script["last_run_date"] = "2024-01-31"
        script["run_interval_value"] = 1
        script["run_interval_unit"] = startup_model.RUN_INTERVAL_MONTHS
        expected = True
        result = startup_model.is_script_run_due(script, current_date=date(2024, 2, 29))
        self.assertEqual(expected, result)

        script["last_run_date"] = "2024-02-29"
        script["run_interval_unit"] = startup_model.RUN_INTERVAL_YEARS
        expected = True
        result = startup_model.is_script_run_due(script, current_date=date(2025, 2, 28))
        self.assertEqual(expected, result)

    def test_frequency_limited_runs_persist_last_run_date_only_when_enabled(self):
        """Ensures the default always-run path does not write run-date preferences."""
        model = startup_model.StartupScriptsModel(prefs=self.prefs)
        script_id = model.get_scripts()[0].get("id")

        expected = False
        result = model.record_scheduled_runs([script_id], current_date=date(2025, 1, 1))
        self.assertEqual(expected, result)

        model.update_script(script_id, {"run_interval_enabled": True})
        expected = True
        result = model.record_scheduled_runs([script_id], current_date=date(2025, 1, 1))
        self.assertEqual(expected, result)

        expected = "2025-01-01"
        result = model.get_script(script_id).get("last_run_date")
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

    def test_backup_export_and_import_replace_the_complete_setup(self):
        """Ensures a JSON backup restores every saved startup-script configuration."""
        model = startup_model.StartupScriptsModel(prefs=self.prefs)
        model.update_script(model.get_scripts()[0].get("id"), {"script_text": "print('first')"})
        added_script = model.add_script(name="Batch Setup")
        model.update_script(
            added_script.get("id"),
            {
                "run_mode": startup_model.RUN_MODE_MAYAPY,
                "script_text": "print('batch')",
            },
        )
        backup_path = os.path.join(self.temp_dir, "startup_scripts_backup.json")

        result = model.export_backup(backup_path)

        expected = backup_path
        self.assertEqual(expected, result)
        with open(backup_path, "r", encoding="utf-8") as backup_file:
            backup_data = json.load(backup_file)
        expected = True
        result = startup_model.is_preferences_data_valid(backup_data)
        self.assertEqual(expected, result)

        model.add_script(name="Temporary Setup")
        imported_scripts = model.import_backup(backup_path)

        expected = ["Startup Script", "Batch Setup"]
        result = [script.get("name") for script in imported_scripts]
        self.assertEqual(expected, result)
        expected = "print('batch')"
        result = imported_scripts[1].get("script_text")
        self.assertEqual(expected, result)

    def test_invalid_backup_does_not_replace_the_current_setup(self):
        """Ensures an invalid backup is rejected before the model changes its configuration."""
        model = startup_model.StartupScriptsModel(prefs=self.prefs)
        original_scripts = model.get_scripts()
        backup_path = os.path.join(self.temp_dir, "invalid_startup_scripts_backup.json")
        with open(backup_path, "w", encoding="utf-8") as backup_file:
            json.dump({"scripts": []}, backup_file)

        with self.assertRaises(ValueError):
            model.import_backup(backup_path)

        expected = original_scripts
        result = model.get_scripts()
        self.assertEqual(expected, result)

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

    def test_frequency_limited_script_does_not_run_before_its_due_date(self):
        """Ensures runtime skips a configuration before its next eligible calendar date."""
        script = startup_model.create_default_script()
        script["run_interval_enabled"] = True
        script["run_interval_value"] = 1
        script["run_interval_unit"] = startup_model.RUN_INTERVAL_DAYS
        script["last_run_date"] = startup_model.get_current_run_date()
        script["script_text"] = "execution_log.append('ran')"
        execution_log = []

        result = startup_runtime.run_script_configuration(
            script,
            event_name=startup_runtime.EVENT_INTERACTIVE_MAYA,
            extra_globals={"execution_log": execution_log},
        )

        expected = False
        self.assertEqual(expected, result)
        expected = []
        self.assertEqual(expected, execution_log)

    def test_runtime_records_a_successful_frequency_limited_run(self):
        """Ensures automatic execution persists the date only after a successful run."""
        model = startup_model.StartupScriptsModel(prefs=self.prefs)
        script_id = model.get_scripts()[0].get("id")
        model.update_script(
            script_id,
            {
                "run_interval_enabled": True,
                "run_interval_value": 1,
                "run_interval_unit": startup_model.RUN_INTERVAL_DAYS,
                "script_text": "scheduled_run_result = True",
            },
        )

        result = startup_runtime.run_configurations(
            model.get_scripts(),
            startup_runtime.EVENT_INTERACTIVE_MAYA,
            startup_model=model,
        )

        expected = 1
        self.assertEqual(expected, result)
        expected = startup_model.get_current_run_date()
        result = model.get_script(script_id).get("last_run_date")
        self.assertEqual(expected, result)

    def test_run_mode_event_matching_distinguishes_interactive_maya_and_mayapy(self):
        """Ensures startup configurations run only for their configured Maya context."""
        script = startup_model.create_default_script()
        script["run_mode"] = startup_model.RUN_MODE_MAYAPY_AND_FILE_OPEN

        expected = False
        result = startup_runtime.matches_event(script, startup_runtime.EVENT_INTERACTIVE_MAYA)
        self.assertEqual(expected, result)
        expected = True
        result = startup_runtime.matches_event(script, startup_runtime.EVENT_MAYAPY)
        self.assertEqual(expected, result)
        expected = True
        result = startup_runtime.matches_event(script, startup_runtime.EVENT_FILE_OPEN)
        self.assertEqual(expected, result)

    def test_startup_event_resolves_interactive_maya_first(self):
        """Ensures Interactive Maya startup uses its dedicated event."""
        session_module = mock.Mock()
        session_module.is_script_in_interactive_maya.return_value = True
        session_module.is_script_in_py_maya.return_value = False

        expected = startup_runtime.EVENT_INTERACTIVE_MAYA
        result = startup_runtime.get_startup_event(session_module=session_module)
        self.assertEqual(expected, result)
        session_module.is_script_in_interactive_maya.assert_called_once()
        session_module.is_script_in_py_maya.assert_not_called()

    def test_startup_event_resolves_mayapy(self):
        """Ensures mayapy startup uses its dedicated event."""
        session_module = mock.Mock()
        session_module.is_script_in_interactive_maya.return_value = False
        session_module.is_script_in_py_maya.return_value = True

        expected = startup_runtime.EVENT_MAYAPY
        result = startup_runtime.get_startup_event(session_module=session_module)
        self.assertEqual(expected, result)
        session_module.is_script_in_interactive_maya.assert_called_once()
        session_module.is_script_in_py_maya.assert_called_once()

    def test_sample_script_is_discoverable_and_sets_expected_scene_timing(self):
        """Ensures the requested scene-defaults sample is packaged with the tool."""
        samples = startup_model.get_sample_scripts()
        sample_paths = {sample.get("relative_path"): sample.get("path") for sample in samples}

        expected_path = "set_scene_defaults.py"
        self.assertIn(expected_path, sample_paths)
        source_text = startup_model.load_script_file(sample_paths[expected_path])
        self.assertIn('FRAME_RATE = "ntsc"', source_text)
        self.assertIn("minTime=TIMELINE_START_FRAME", source_text)
        self.assertIn("maxTime=TIMELINE_END_FRAME", source_text)
        self.assertIn("ANTI_ALIASING_SAMPLE_COUNT = 16", source_text)
        self.assertIn("hardwareRenderingGlobals.multiSampleCount", source_text)

    def test_current_frame_sample_is_discoverable_and_sets_frame_one(self):
        """Ensures the configurable current-frame sample is included in the examples menu."""
        samples = startup_model.get_sample_scripts()
        sample_paths = {sample.get("relative_path"): sample.get("path") for sample in samples}

        expected_path = "set_current_frame.py"
        self.assertIn(expected_path, sample_paths)
        source_text = startup_model.load_script_file(sample_paths[expected_path])
        self.assertIn("CURRENT_FRAME = 1", source_text)
        self.assertIn("cmds.currentTime(CURRENT_FRAME, edit=True)", source_text)

    def test_extra_maya_preferences_sample_is_discoverable_and_is_disabled_by_default(self):
        """Ensures the Extra Maya Preferences sample exposes every requested setting safely."""
        samples = startup_model.get_sample_scripts()
        sample_paths = {sample.get("relative_path"): sample.get("path") for sample in samples}

        expected_path = "extra_maya_preferences.py"
        self.assertIn(expected_path, sample_paths)
        source_text = startup_model.load_script_file(sample_paths[expected_path])
        expected_options = [
            "SET_HOMESCREEN_ON_STARTUP_STATE = False",
            "HOMESCREEN_ON_STARTUP_STATE = False",
            "SET_HOME_MENU_BAR_ICON_STATE = False",
            "HOME_MENU_BAR_ICON_STATE = False",
            "SET_VIEW_CUBE_STATE = False",
            "VIEW_CUBE_STATE = False",
            "SET_CACHED_PLAYBACK_STATE = False",
            "CACHED_PLAYBACK_STATE = False",
            "SET_PLAYBACK_SPEED = False",
            "PLAYBACK_SPEED = 1.0",
            "SET_PERSP_NEAR_CLIP_PLANE = False",
            "PERSP_NEAR_CLIP_PLANE = 1.0",
            "RESET_MOVE_TOOL_SETTINGS = False",
            "RESET_ROTATE_TOOL_SETTINGS = False",
            "RESET_SCALE_TOOL_SETTINGS = False",
        ]
        for expected_option in expected_options:
            self.assertIn(expected_option, source_text)
        self.assertNotIn("multiSampleCount", source_text)

    def test_tool_version_is_1_1_0(self):
        """Ensures the Startup Scripts version reflects the feature update."""
        expected = "1.1.0"
        result = startup_scripts.__version__
        self.assertEqual(expected, result)


if __name__ == "__main__":
    unittest.main()
