"""Unit tests for the pure Script Library model and archive services."""

from gt.tools.script_library.script_library_constants import ScriptLibraryConstants
from gt.tools.script_library import script_library_model
import json
import os
import shutil
import tempfile
import unittest
import zipfile


class MemoryPrefs:
    """Small Prefs-compatible test double backed by a temporary directory."""

    def __init__(self, root_dir):
        """Initializes in-memory preference data and its user-files root.

        Args:
            root_dir (str): Existing temporary directory.
        """
        self.root_dir = root_dir
        self.sub_folder = "user_files"
        self.preferences = {}

    def set_user_files_sub_folder(self, sub_folder_name):
        """Sets the user-files subfolder.

        Args:
            sub_folder_name (str): New subfolder name.
        """
        self.sub_folder = sub_folder_name

    def get_user_files_dir_path(self, create_if_missing=True):
        """Gets the user-files directory.

        Args:
            create_if_missing (bool, optional): Whether the directory is created.

        Returns:
            str: User-files directory path.
        """
        directory_path = os.path.join(self.root_dir, self.sub_folder)
        if create_if_missing and not os.path.isdir(directory_path):
            os.makedirs(directory_path)
        return directory_path

    def write_user_file(self, file_name, content, is_json=False):
        """Writes one test user file.

        Args:
            file_name (str): File name stored in the user directory.
            content (str or dict): File content.
            is_json (bool, optional): Whether JSON serialization is used.

        Returns:
            str: Written file path.
        """
        file_path = os.path.join(self.get_user_files_dir_path(), file_name)
        with open(file_path, "w", encoding="utf-8") as output_file:
            if is_json:
                json.dump(content, output_file)
            else:
                output_file.write(content)
        return file_path

    def get_raw_preferences(self):
        """Gets raw test preference data.

        Returns:
            dict: Mutable preference dictionary.
        """
        return self.preferences

    def save(self):
        """Implements the Prefs save interface for in-memory tests."""

    def set_bool(self, key, value):
        """Stores a boolean preference.

        Args:
            key (str): Preference key.
            value (bool): Preference value.
        """
        self.preferences[key] = bool(value)

    def get_bool(self, key, default=None):
        """Gets a boolean preference.

        Args:
            key (str): Preference key.
            default (bool, optional): Missing-key fallback.

        Returns:
            bool: Stored or fallback value.
        """
        return self.preferences.get(key, default)

    def set_string(self, key, value):
        """Stores a string preference.

        Args:
            key (str): Preference key.
            value (str): Preference value.
        """
        self.preferences[key] = str(value)

    def get_string(self, key, default=None):
        """Gets a string preference.

        Args:
            key (str): Preference key.
            default (str, optional): Missing-key fallback.

        Returns:
            str: Stored or fallback value.
        """
        return self.preferences.get(key, default)


class TestScriptLibraryModel(unittest.TestCase):
    """Tests Script Library persistence, execution, and archive behavior."""

    def setUp(self):
        """Creates an isolated test model."""
        self.temp_dir = tempfile.mkdtemp(prefix="gt_script_library_test_")
        self.addCleanup(shutil.rmtree, self.temp_dir)
        self.preferences = MemoryPrefs(self.temp_dir)
        self.model = script_library_model.ScriptLibraryModel(
            preferences=self.preferences
        )

    def test_sanitize_file_stem(self):
        """Tests file-name sanitization."""
        expected = "my_quick_script"
        result = self.model.sanitize_file_stem("  My Quick: Script!  ")
        self.assertEqual(expected, result)

    def test_create_script_persists_file_and_metadata(self):
        """Tests creation of script content and Prefs metadata."""
        item = self.model.create_script("Select Controls", "result = 12")
        expected = "result = 12"
        result = self.model.read_script_content(item)
        self.assertEqual(expected, result)
        self.assertTrue(os.path.isfile(self.model.get_script_path(item)))
        stored_items = self.preferences.preferences.get(
            ScriptLibraryConstants.PREF_KEY_SCRIPTS
        )
        self.assertEqual(1, len(stored_items))
        self.assertEqual(item.script_id, stored_items[0].get("id"))

    def test_create_script_rejects_conflicting_name(self):
        """Tests that user-created scripts cannot reuse an existing file name."""
        self.model.create_script("Conflict Name", "pass")
        with self.assertRaises(ValueError):
            self.model.create_script("Conflict Name", "pass")

    def test_model_reload_preserves_stable_id(self):
        """Tests recreation from the same preference object."""
        item = self.model.create_script("Reload Me", "value = 3")
        reloaded_model = script_library_model.ScriptLibraryModel(
            preferences=self.preferences
        )
        expected = item.script_id
        result = reloaded_model.get_scripts(include_hidden=True)[0].script_id
        self.assertEqual(expected, result)

    def test_hidden_script_is_only_returned_when_requested(self):
        """Tests use-mode visibility filtering."""
        item = self.model.create_script("Hidden", "pass", visible=False)
        expected = []
        result = self.model.get_scripts(include_hidden=False)
        self.assertEqual(expected, result)
        self.assertEqual([item], self.model.get_scripts(include_hidden=True))

    def test_tool_state_is_stored_through_preferences(self):
        """Tests edit mode, selection, and splitter-state persistence."""
        item = self.model.create_script("State", "pass")
        self.model.set_edit_mode(True)
        self.model.set_selected_script_id(item.script_id)
        self.model.set_splitter_sizes([250, 500])
        self.assertTrue(self.model.get_edit_mode())
        self.assertEqual(item.script_id, self.model.get_selected_script_id())
        self.assertEqual([250, 500], self.model.get_splitter_sizes())

    def test_library_preferences_default_and_persist(self):
        """Tests edit-only library preference defaults and persistence."""
        self.assertTrue(self.model.get_show_details_in_use_mode())
        self.assertTrue(self.model.get_auto_save())
        self.model.set_show_details_in_use_mode(False)
        self.model.set_auto_save(False)
        self.assertFalse(self.model.get_show_details_in_use_mode())
        self.assertFalse(self.model.get_auto_save())

    def test_search_includes_description(self):
        """Tests searching script descriptions."""
        item = self.model.create_script(
            "Make Locator", "pass", description="Creates a center marker"
        )
        expected = [item]
        result = self.model.search_scripts("center marker")
        self.assertEqual(expected, result)

    def test_execute_script_returns_execution_namespace(self):
        """Tests compilation with a useful execution namespace."""
        item = self.model.create_script("Math", "output_value = input_value * 2")
        expected = 14
        namespace = self.model.execute_script(
            item.script_id, global_namespace={"input_value": 7}
        )
        result = namespace.get("output_value")
        self.assertEqual(expected, result)
        self.assertEqual(self.model.get_script_path(item), namespace.get("__file__"))

    def test_custom_icon_is_copied_beside_script(self):
        """Tests managed custom-icon copying."""
        source_icon = os.path.join(self.temp_dir, "source.svg")
        with open(source_icon, "w", encoding="utf-8") as icon_file:
            icon_file.write("<svg/>")
        item = self.model.create_script("Icon Script", "pass")
        result = self.model.attach_custom_icon(item.script_id, source_icon)
        self.assertTrue(os.path.isfile(result))
        self.assertEqual(
            ScriptLibraryConstants.ICON_MODE_CUSTOM,
            self.model.get_script(item.script_id).icon_mode,
        )

    def test_rename_script_moves_managed_source_and_icon(self):
        """Tests renaming the Python file and associated managed icon together."""
        source_icon = os.path.join(self.temp_dir, "source.svg")
        with open(source_icon, "w", encoding="utf-8") as icon_file:
            icon_file.write("<svg/>")
        item = self.model.create_script("Original Script", "rename_value = 9")
        old_script_path = self.model.get_script_path(item)
        old_icon_path = self.model.attach_custom_icon(item.script_id, source_icon)
        renamed_item = self.model.rename_script(item.script_id, "Renamed Script")
        expected_script_path = os.path.join(
            self.model.get_scripts_dir(), "renamed_script.py"
        )
        expected_icon_path = os.path.join(
            self.model.get_scripts_dir(), "renamed_script_icon.svg"
        )
        self.assertEqual("Original Script", renamed_item.nice_name)
        self.assertEqual("renamed_script.py", renamed_item.file_name)
        self.assertEqual("renamed_script_icon.svg", renamed_item.icon_value)
        self.assertFalse(os.path.exists(old_script_path))
        self.assertFalse(os.path.exists(old_icon_path))
        self.assertTrue(os.path.isfile(expected_script_path))
        self.assertTrue(os.path.isfile(expected_icon_path))

    def test_rename_script_rejects_conflicting_name(self):
        """Tests that renaming cannot replace another managed script."""
        first_item = self.model.create_script("First Script", "pass")
        self.model.create_script("Second Script", "pass")
        with self.assertRaises(ValueError):
            self.model.rename_script(first_item.script_id, "Second Script")

    def test_missing_custom_icon_resolves_to_script_placeholder(self):
        """Tests the safe placeholder used for missing icon assets."""
        from gt.ui import resource_library

        item = self.model.create_script(
            "Missing Icon",
            "pass",
            icon_mode=ScriptLibraryConstants.ICON_MODE_CUSTOM,
            icon_value="missing.svg",
        )
        expected = resource_library.Icon.script_library_missing_icon
        result = self.model.get_script_icon_path(item)
        self.assertEqual(expected, result)

    def test_duplicate_script_uses_fresh_id_and_copies_content(self):
        """Tests duplication with a fresh stable ID and copied source."""
        item = self.model.create_script("Original", "duplicate_value = 5")
        duplicate = self.model.duplicate_script(item.script_id)
        self.assertNotEqual(item.script_id, duplicate.script_id)
        expected = "duplicate_value = 5"
        result = self.model.read_script_content(duplicate)
        self.assertEqual(expected, result)

    def test_export_script_and_import_copy_include_custom_icon(self):
        """Tests a compressed per-script round trip with its icon."""
        source_icon = os.path.join(self.temp_dir, "source.svg")
        with open(source_icon, "w", encoding="utf-8") as icon_file:
            icon_file.write("<svg><path/></svg>")
        item = self.model.create_script("Portable", "portable_value = 9")
        self.model.attach_custom_icon(item.script_id, source_icon)
        archive_path = self.model.export_script(
            item.script_id, os.path.join(self.temp_dir, "portable")
        )

        import_root = os.path.join(self.temp_dir, "imported")
        os.makedirs(import_root)
        imported_model = script_library_model.ScriptLibraryModel(
            preferences=MemoryPrefs(import_root)
        )
        import_result = imported_model.import_archive(archive_path)
        self.assertEqual(1, len(import_result.get("imported")))
        imported_item = imported_model.get_scripts(include_hidden=True)[0]
        expected = "portable_value = 9"
        result = imported_model.read_script_content(imported_item)
        self.assertEqual(expected, result)
        imported_icon = os.path.join(
            imported_model.get_scripts_dir(), imported_item.icon_value
        )
        self.assertTrue(os.path.isfile(imported_icon))

    def test_export_all_replace_restores_matching_script(self):
        """Tests restoring a backup over a matching stable ID."""
        item = self.model.create_script("Backup Name", "backup_value = 1")
        archive_path = self.model.export_all(
            os.path.join(self.temp_dir, "library_backup")
        )
        self.model.update_script(
            item.script_id,
            nice_name="Changed Name",
            script_content="backup_value = 99",
        )
        import_result = self.model.import_archive(
            archive_path, conflict_policy="replace"
        )
        self.assertEqual([item.script_id], import_result.get("replaced"))
        restored_item = self.model.get_script(item.script_id)
        self.assertEqual("Backup Name", restored_item.nice_name)
        self.assertEqual("backup_value = 1", self.model.read_script_content(restored_item))

    def test_import_archive_never_extracts_undeclared_traversal_member(self):
        """Tests that archive members are read explicitly instead of extracted."""
        archive_path = os.path.join(self.temp_dir, "malicious.gtscript")
        manifest = {
            "format": ScriptLibraryConstants.ARCHIVE_FORMAT,
            "version": ScriptLibraryConstants.ARCHIVE_VERSION,
            "scope": "script",
            "scripts": [
                {
                    "id": "malicious",
                    "file_name": "../../outside.py",
                    "nice_name": "Unsafe",
                }
            ],
        }
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr(
                ScriptLibraryConstants.ARCHIVE_MANIFEST, json.dumps(manifest)
            )
            archive.writestr("../../outside.py", "unsafe = True")
        expected = []
        result = self.model.import_archive(archive_path).get("imported")
        self.assertEqual(expected, result)
        self.assertFalse(os.path.exists(os.path.join(self.temp_dir, "outside.py")))

    def test_delete_script_removes_only_managed_files(self):
        """Tests deletion of the selected script and icon without unrelated files."""
        unrelated_path = os.path.join(
            self.model.get_scripts_dir(), "keep_me.txt"
        )
        with open(unrelated_path, "w", encoding="utf-8") as unrelated_file:
            unrelated_file.write("preserve")
        source_icon = os.path.join(self.temp_dir, "delete.svg")
        with open(source_icon, "w", encoding="utf-8") as icon_file:
            icon_file.write("<svg/>")
        item = self.model.create_script("Delete Me", "pass")
        icon_path = self.model.attach_custom_icon(item.script_id, source_icon)
        script_path = self.model.get_script_path(item)
        self.assertTrue(self.model.delete_script(item.script_id))
        self.assertFalse(os.path.exists(script_path))
        self.assertFalse(os.path.exists(icon_path))
        self.assertTrue(os.path.exists(unrelated_path))

    def test_delete_script_removes_managed_snapshot_without_metadata(self):
        """Tests that a stale managed snapshot is removed with its script."""
        item = self.model.create_script("Snapshot Script", "pass")
        snapshot_path = os.path.join(
            self.model.get_scripts_dir(), "snapshot_script_snapshot.png"
        )
        with open(snapshot_path, "wb") as snapshot_file:
            snapshot_file.write(b"image")
        self.assertTrue(self.model.delete_script(item.script_id))
        self.assertFalse(os.path.exists(snapshot_path))


if __name__ == "__main__":
    unittest.main()
