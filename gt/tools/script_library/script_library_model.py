"""Persistent data and file services for the Script Library tool."""

from gt.tools.script_library.script_library_constants import ScriptLibraryConstants
from gt.tools.script_library.script_library_item import ScriptLibraryItem
import logging
import os
import re
import shutil
import uuid


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ScriptLibraryModel:
    """Manages Script Library persistence, archives, icons, and execution."""

    def __init__(self, preferences=None):
        """Initializes the Script Library model.

        Args:
            preferences (Prefs, optional): Custom Prefs instance used by tests or callers.
        """
        if preferences is None:
            from gt.core import prefs as core_prefs

            preferences = core_prefs.Prefs(ScriptLibraryConstants.PREFS_NAME)
        self.preferences = preferences
        self.preferences.set_user_files_sub_folder(ScriptLibraryConstants.USER_FILES_SUB_FOLDER)
        self.scripts = []
        self.load_scripts()

    @staticmethod
    def sanitize_file_stem(raw_name):
        """Builds a safe snake-case file stem.

        Args:
            raw_name (str): User-facing name or file stem.

        Returns:
            str: Safe non-empty file stem.
        """
        clean_name = re.sub(r"[^a-zA-Z0-9_\- ]+", "", str(raw_name or "").strip())
        clean_name = re.sub(r"[\-\s]+", "_", clean_name)
        clean_name = re.sub(r"_+", "_", clean_name).strip("_").lower()
        return clean_name or "script"

    @staticmethod
    def ensure_extension(file_path, extension):
        """Adds an extension when a target path does not already include it.

        Args:
            file_path (str): Target file path.
            extension (str): Required extension including the leading period.

        Returns:
            str: Path with the required extension.
        """
        if not str(file_path or "").lower().endswith(extension.lower()):
            return f"{file_path}{extension}"
        return file_path

    def get_scripts_dir(self, create_if_missing=True):
        """Gets the Prefs-managed script directory.

        Args:
            create_if_missing (bool, optional): Whether to create the directory.

        Returns:
            str: Script directory path.
        """
        return self.preferences.get_user_files_dir_path(create_if_missing=create_if_missing)

    def load_scripts(self):
        """Loads script metadata and discovers untracked Python files."""
        raw_items = self.preferences.get_raw_preferences().get(
            ScriptLibraryConstants.PREF_KEY_SCRIPTS, []
        )
        self.scripts = []
        known_ids = set()
        known_files = set()
        if isinstance(raw_items, list):
            for raw_item in raw_items:
                item = ScriptLibraryItem.from_dict(raw_item)
                file_key = os.path.normcase(item.file_name) if item else ""
                if not item or item.script_id in known_ids or file_key in known_files:
                    continue
                known_ids.add(item.script_id)
                known_files.add(file_key)
                self.scripts.append(item)
        self._discover_untracked_scripts(known_files=known_files)
        self._normalize_order()

    def _discover_untracked_scripts(self, known_files):
        """Adds metadata for Python files manually placed in the scripts folder.

        Args:
            known_files (set): Normalized file names already represented by metadata.
        """
        scripts_dir = self.get_scripts_dir(create_if_missing=False)
        if not scripts_dir or not os.path.isdir(scripts_dir):
            return
        discovered = False
        next_order = len(self.scripts)
        for file_name in sorted(os.listdir(scripts_dir)):
            if not file_name.lower().endswith(ScriptLibraryConstants.SCRIPT_EXTENSION):
                continue
            if os.path.normcase(file_name) in known_files:
                continue
            nice_name = os.path.splitext(file_name)[0].replace("_", " ").title()
            self.scripts.append(
                ScriptLibraryItem(
                    script_id=uuid.uuid4().hex,
                    file_name=file_name,
                    nice_name=nice_name,
                    order=next_order,
                )
            )
            next_order += 1
            discovered = True
        if discovered:
            self.save_scripts()

    def _normalize_order(self):
        """Normalizes script ordering to a continuous deterministic sequence."""
        self.scripts.sort(key=lambda item: (item.order, item.nice_name.lower(), item.script_id))
        for index, item in enumerate(self.scripts):
            item.order = index

    def save_scripts(self):
        """Saves all script metadata through Prefs."""
        self._normalize_order()
        preferences = self.preferences.get_raw_preferences()
        preferences[ScriptLibraryConstants.PREF_KEY_SCRIPTS] = [
            item.to_dict() for item in self.scripts
        ]
        self.preferences.save()

    def get_scripts(self, include_hidden=False):
        """Gets scripts in explicit display order.

        Args:
            include_hidden (bool, optional): Whether hidden scripts are included.

        Returns:
            list: Ordered ScriptLibraryItem objects.
        """
        if include_hidden:
            return list(self.scripts)
        return [item for item in self.scripts if item.visible]

    def search_scripts(self, search_text="", include_hidden=False):
        """Searches script names, file names, and descriptions.

        Args:
            search_text (str, optional): Case-insensitive search text.
            include_hidden (bool, optional): Whether hidden scripts are included.

        Returns:
            list: Matching ScriptLibraryItem objects.
        """
        search_value = str(search_text or "").strip().lower()
        items = self.get_scripts(include_hidden=include_hidden)
        if not search_value:
            return items
        matches = []
        for item in items:
            searchable = " ".join((item.nice_name, item.file_name, item.description)).lower()
            if search_value in searchable:
                matches.append(item)
        return matches

    def get_script(self, script_id):
        """Gets one script by stable identifier.

        Args:
            script_id (str): Stable script identifier.

        Returns:
            ScriptLibraryItem or None: Matching script item.
        """
        for item in self.scripts:
            if item.script_id == script_id:
                return item
        return None

    def get_script_path(self, script_or_id):
        """Gets the safe on-disk path for one script.

        Args:
            script_or_id (ScriptLibraryItem or str): Script item or stable identifier.

        Returns:
            str or None: Safe script path when the item exists.
        """
        item = script_or_id
        if not isinstance(item, ScriptLibraryItem):
            item = self.get_script(script_or_id)
        if not item:
            return None
        return self.get_managed_file_path(item.file_name)

    def read_script_content(self, script_or_id):
        """Reads one script as UTF-8 text.

        Args:
            script_or_id (ScriptLibraryItem or str): Script item or stable identifier.

        Returns:
            str: Script text, or an empty string when the file is missing.
        """
        script_path = self.get_script_path(script_or_id)
        if not script_path or not os.path.isfile(script_path):
            return ""
        with open(script_path, "r", encoding="utf-8") as script_file:
            return script_file.read()

    def create_script(
        self,
        nice_name,
        script_content="",
        description="",
        visible=True,
        icon_mode=ScriptLibraryConstants.ICON_MODE_DEFAULT,
        icon_value="",
        allow_name_conflict=False,
    ):
        """Creates a new script file and persistent metadata.

        Args:
            nice_name (str): User-facing script name.
            script_content (str, optional): Python source code.
            description (str, optional): User-facing description.
            visible (bool, optional): Whether the script appears in use mode.
            icon_mode (str, optional): Initial icon mode.
            icon_value (str, optional): Initial icon value.
            allow_name_conflict (bool, optional): Whether a unique suffix may be
                added when the requested file name already exists.

        Returns:
            ScriptLibraryItem: Created script item.

        Raises:
            ValueError: If the nice name is empty.
        """
        nice_name = str(nice_name or "").strip()
        if not nice_name:
            raise ValueError("Script name cannot be empty.")
        if self.has_script_name_conflict(nice_name):
            if not allow_name_conflict:
                raise ValueError(f'A script named "{nice_name}" already exists.')
            file_name = self.get_unique_script_file_name(
                self.sanitize_file_stem(nice_name)
            )
        else:
            file_name = (
                f"{self.sanitize_file_stem(nice_name)}"
                f"{ScriptLibraryConstants.SCRIPT_EXTENSION}"
            )
        self.preferences.write_user_file(file_name=file_name, content=str(script_content or ""))
        item = ScriptLibraryItem(
            script_id=uuid.uuid4().hex,
            file_name=file_name,
            nice_name=nice_name,
            description=description,
            visible=visible,
            icon_mode=icon_mode,
            icon_value=icon_value,
            order=len(self.scripts),
        )
        self.scripts.append(item)
        self.save_scripts()
        self.set_selected_script_id(item.script_id)
        return item

    def has_script_name_conflict(self, requested_name, exclude_script_id=""):
        """Checks whether a requested script file name is already in use.

        Args:
            requested_name (str): Proposed script name or file stem.
            exclude_script_id (str, optional): Existing item that may retain its name.

        Returns:
            bool: True when another managed script or file uses the requested name.
        """
        file_name = (
            f"{self.sanitize_file_stem(requested_name)}"
            f"{ScriptLibraryConstants.SCRIPT_EXTENSION}"
        )
        normalized_name = os.path.normcase(file_name)
        for item in self.scripts:
            if item.script_id == exclude_script_id:
                continue
            if os.path.normcase(item.file_name) == normalized_name:
                return True
        excluded_item = self.get_script(exclude_script_id)
        if excluded_item and os.path.normcase(excluded_item.file_name) == normalized_name:
            return False
        target_path = self.get_managed_file_path(file_name)
        return bool(target_path and os.path.isfile(target_path))

    def rename_script(self, script_id, requested_name):
        """Renames a script source file and its managed custom icon or snapshot.

        Args:
            script_id (str): Stable identifier for the script to rename.
            requested_name (str): New script file name without its extension.

        Returns:
            ScriptLibraryItem: The renamed script item.

        Raises:
            KeyError: If the script cannot be found.
            ValueError: If the requested name is empty or conflicts with another script.
            IOError: If the source script cannot be found or a managed path is invalid.
        """
        item = self.get_script(script_id)
        if not item:
            raise KeyError(f'Unable to find script ID "{script_id}".')
        requested_name = str(requested_name or "").strip()
        if not requested_name:
            raise ValueError("Script name cannot be empty.")
        if self.has_script_name_conflict(requested_name, exclude_script_id=script_id):
            raise ValueError(f'A script named "{requested_name}" already exists.')

        new_stem = self.sanitize_file_stem(requested_name)
        new_file_name = f"{new_stem}{ScriptLibraryConstants.SCRIPT_EXTENSION}"
        old_script_path = self.get_script_path(item)
        new_script_path = self.get_managed_file_path(new_file_name)
        if not old_script_path or not os.path.isfile(old_script_path) or not new_script_path:
            raise IOError("Unable to resolve the managed script file for renaming.")

        old_icon_path = None
        new_icon_name = item.icon_value
        new_icon_path = None
        if item.icon_mode in (
            ScriptLibraryConstants.ICON_MODE_CUSTOM,
            ScriptLibraryConstants.ICON_MODE_SNAPSHOT,
        ) and item.icon_value:
            old_icon_path = self.get_managed_file_path(item.icon_value)
            if old_icon_path and os.path.isfile(old_icon_path):
                extension = os.path.splitext(old_icon_path)[1]
                suffix = (
                    "_snapshot"
                    if item.icon_mode == ScriptLibraryConstants.ICON_MODE_SNAPSHOT
                    else "_icon"
                )
                new_icon_name = f"{new_stem}{suffix}{extension}"
                new_icon_path = self.get_managed_file_path(new_icon_name)
                if not new_icon_path:
                    raise IOError("Unable to resolve the managed icon file for renaming.")

        script_path_changed = (
            os.path.normcase(os.path.abspath(old_script_path))
            != os.path.normcase(os.path.abspath(new_script_path))
        )
        if script_path_changed:
            os.replace(old_script_path, new_script_path)
        try:
            if (
                old_icon_path
                and new_icon_path
                and os.path.normcase(os.path.abspath(old_icon_path))
                != os.path.normcase(os.path.abspath(new_icon_path))
            ):
                os.replace(old_icon_path, new_icon_path)
        except OSError:
            if script_path_changed:
                os.replace(new_script_path, old_script_path)
            raise
        item.file_name = new_file_name
        item.icon_value = new_icon_name
        self.save_scripts()
        return item

    def update_script(
        self,
        script_id,
        nice_name=None,
        script_content=None,
        description=None,
        visible=None,
        icon_mode=None,
        icon_value=None,
    ):
        """Updates one script and writes changed content immediately.

        Args:
            script_id (str): Stable script identifier.
            nice_name (str, optional): New user-facing name.
            script_content (str, optional): New Python source code.
            description (str, optional): New description.
            visible (bool, optional): New visibility state.
            icon_mode (str, optional): New icon mode.
            icon_value (str, optional): New icon value.

        Returns:
            ScriptLibraryItem: Updated item.

        Raises:
            KeyError: If the script cannot be found.
            ValueError: If the new name or icon mode is invalid.
        """
        item = self.get_script(script_id)
        if not item:
            raise KeyError(f'Unable to find script ID "{script_id}".')
        if nice_name is not None:
            nice_name = str(nice_name).strip()
            if not nice_name:
                raise ValueError("Script name cannot be empty.")
            item.nice_name = nice_name
        if description is not None:
            item.description = str(description or "")
        if visible is not None:
            item.visible = bool(visible)
        if icon_mode is not None:
            if icon_mode not in ScriptLibraryConstants.ICON_MODES:
                raise ValueError(f'Unsupported icon mode: "{icon_mode}".')
            item.icon_mode = icon_mode
        if icon_value is not None:
            if item.icon_mode in (
                ScriptLibraryConstants.ICON_MODE_CUSTOM,
                ScriptLibraryConstants.ICON_MODE_SNAPSHOT,
            ):
                item.icon_value = os.path.basename(str(icon_value or ""))
            else:
                item.icon_value = str(icon_value or "")
        if script_content is not None:
            self.preferences.write_user_file(
                file_name=item.file_name,
                content=str(script_content),
            )
        self.save_scripts()
        return item

    def delete_script(self, script_id):
        """Deletes one script and its managed custom icon or snapshot.

        Args:
            script_id (str): Stable script identifier.

        Returns:
            bool: True when a script was found and removed.
        """
        item = self.get_script(script_id)
        if not item:
            return False
        paths_to_delete = [self.get_script_path(item)]
        if item.icon_mode in (
            ScriptLibraryConstants.ICON_MODE_CUSTOM,
            ScriptLibraryConstants.ICON_MODE_SNAPSHOT,
        ):
            paths_to_delete.append(self.get_managed_file_path(item.icon_value))
        script_stem = os.path.splitext(item.file_name)[0]
        scripts_dir = self.get_scripts_dir(create_if_missing=False)
        if scripts_dir and os.path.isdir(scripts_dir):
            for file_name in os.listdir(scripts_dir):
                file_stem, extension = os.path.splitext(file_name)
                if (
                    extension.lower() in ScriptLibraryConstants.SUPPORTED_ICON_EXTENSIONS
                    and file_stem in (f"{script_stem}_icon", f"{script_stem}_snapshot")
                ):
                    paths_to_delete.append(self.get_managed_file_path(file_name))
        for file_path in set(paths_to_delete):
            if file_path and os.path.isfile(file_path):
                os.remove(file_path)
        self.scripts.remove(item)
        self.save_scripts()
        if self.get_selected_script_id() == script_id:
            self.set_selected_script_id("")
        return True

    def duplicate_script(self, script_id):
        """Duplicates a script with a fresh stable ID and managed icon copy.

        Args:
            script_id (str): Stable source script identifier.

        Returns:
            ScriptLibraryItem: Newly created duplicate.

        Raises:
            KeyError: If the source script cannot be found.
        """
        source_item = self.get_script(script_id)
        if not source_item:
            raise KeyError(f'Unable to find script ID "{script_id}".')
        managed_icon_mode = source_item.icon_mode in (
            ScriptLibraryConstants.ICON_MODE_CUSTOM,
            ScriptLibraryConstants.ICON_MODE_SNAPSHOT,
        )
        duplicate = self.create_script(
            nice_name=f"{source_item.nice_name} Copy",
            script_content=self.read_script_content(source_item),
            description=source_item.description,
            visible=source_item.visible,
            icon_mode=(
                ScriptLibraryConstants.ICON_MODE_DEFAULT
                if managed_icon_mode
                else source_item.icon_mode
            ),
            icon_value="" if managed_icon_mode else source_item.icon_value,
            allow_name_conflict=True,
        )
        if managed_icon_mode:
            source_icon_path = self.get_managed_file_path(source_item.icon_value)
            if source_icon_path and os.path.isfile(source_icon_path):
                if source_item.icon_mode == ScriptLibraryConstants.ICON_MODE_SNAPSHOT:
                    self.attach_snapshot(duplicate.script_id, source_icon_path)
                else:
                    self.attach_custom_icon(duplicate.script_id, source_icon_path)
        return duplicate

    def attach_custom_icon(self, script_id, source_path):
        """Copies a user icon beside its script and stores its metadata.

        Args:
            script_id (str): Stable script identifier.
            source_path (str): Existing icon file path.

        Returns:
            str: Managed icon path.

        Raises:
            IOError: If the source icon does not exist.
            ValueError: If the icon extension is unsupported.
        """
        item = self.get_script(script_id)
        if not item:
            raise KeyError(f'Unable to find script ID "{script_id}".')
        if not source_path or not os.path.isfile(source_path):
            raise IOError(f'Icon file does not exist: "{source_path}".')
        extension = os.path.splitext(source_path)[1].lower()
        if extension not in ScriptLibraryConstants.SUPPORTED_ICON_EXTENSIONS:
            raise ValueError(f'Unsupported icon extension: "{extension}".')
        script_stem = os.path.splitext(item.file_name)[0]
        target_name = f"{script_stem}_icon{extension}"
        target_path = self.get_managed_file_path(target_name)
        if os.path.normcase(os.path.abspath(source_path)) != os.path.normcase(target_path):
            shutil.copy2(source_path, target_path)
        self.update_script(
            script_id=script_id,
            icon_mode=ScriptLibraryConstants.ICON_MODE_CUSTOM,
            icon_value=target_name,
        )
        return target_path

    def attach_snapshot(self, script_id, snapshot_path):
        """Stores a viewport snapshot as the selected script icon.

        Args:
            script_id (str): Stable script identifier.
            snapshot_path (str): Existing snapshot image path.

        Returns:
            str: Managed snapshot path.
        """
        item = self.get_script(script_id)
        if not item:
            raise KeyError(f'Unable to find script ID "{script_id}".')
        if not snapshot_path or not os.path.isfile(snapshot_path):
            raise IOError(f'Snapshot file does not exist: "{snapshot_path}".')
        extension = os.path.splitext(snapshot_path)[1].lower()
        if extension not in ScriptLibraryConstants.SUPPORTED_ICON_EXTENSIONS:
            raise ValueError(f'Unsupported snapshot extension: "{extension}".')
        script_stem = os.path.splitext(item.file_name)[0]
        target_name = f"{script_stem}_snapshot{extension}"
        target_path = self.get_managed_file_path(target_name)
        if os.path.normcase(os.path.abspath(snapshot_path)) != os.path.normcase(target_path):
            shutil.copy2(snapshot_path, target_path)
        self.update_script(
            script_id=script_id,
            icon_mode=ScriptLibraryConstants.ICON_MODE_SNAPSHOT,
            icon_value=target_name,
        )
        return target_path

    def get_script_icon_path(self, script_or_id):
        """Resolves an icon path and safely falls back for missing assets.

        Args:
            script_or_id (ScriptLibraryItem or str): Script item or stable identifier.

        Returns:
            str: Existing icon or placeholder path.
        """
        from gt.ui import resource_library

        item = script_or_id
        if not isinstance(item, ScriptLibraryItem):
            item = self.get_script(script_or_id)
        if not item:
            return resource_library.Icon.script_library_missing_icon
        if item.icon_mode == ScriptLibraryConstants.ICON_MODE_DEFAULT:
            return resource_library.Icon.tool_script_library
        if item.icon_mode == ScriptLibraryConstants.ICON_MODE_PACKAGE:
            icon_name = self.normalize_package_icon_name(item.icon_value)
            icon_path = getattr(resource_library.Icon, icon_name, None)
            if icon_path and os.path.isfile(icon_path):
                return icon_path
            return resource_library.Icon.script_library_missing_icon
        icon_path = self.get_managed_file_path(item.icon_value)
        if icon_path and os.path.isfile(icon_path):
            return icon_path
        return resource_library.Icon.script_library_missing_icon

    @staticmethod
    def normalize_package_icon_name(icon_name):
        """Normalizes a package icon reference to an Icon attribute name.

        Args:
            icon_name (str): Icon name or dotted resource-library reference.

        Returns:
            str: Normalized Icon attribute name.
        """
        normalized = str(icon_name or "").strip()
        for prefix in ("resource_library.Icon.", "ui_res_lib.Icon.", "Icon."):
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix) :]
                break
        return normalized

    def execute_script(self, script_id, global_namespace=None):
        """Executes a stored script with useful file metadata.

        Args:
            script_id (str): Stable script identifier.
            global_namespace (dict, optional): Additional execution globals.

        Returns:
            dict: Globals produced by script execution.

        Raises:
            KeyError: If the script cannot be found.
            IOError: If the script file is missing.
            SyntaxError: If the stored code cannot be compiled.
            Exception: Any exception raised by the stored script.
        """
        item = self.get_script(script_id)
        if not item:
            raise KeyError(f'Unable to find script ID "{script_id}".')
        script_path = self.get_script_path(item)
        if not script_path or not os.path.isfile(script_path):
            raise IOError(f'Script file is missing: "{script_path}".')
        script_content = self.read_script_content(item)
        namespace = dict(global_namespace or {})
        namespace.update(
            {
                "__name__": "__main__",
                "__file__": script_path,
                "__package__": None,
            }
        )
        compiled_script = compile(script_content, script_path, "exec")
        exec(compiled_script, namespace, namespace)
        return namespace

    def import_python_file(self, file_path):
        """Imports a raw Python file as a new library script.

        Args:
            file_path (str): Existing Python file path.

        Returns:
            ScriptLibraryItem: Imported script item.
        """
        if not file_path or not os.path.isfile(file_path):
            raise IOError(f'Python file does not exist: "{file_path}".')
        if not file_path.lower().endswith(ScriptLibraryConstants.SCRIPT_EXTENSION):
            raise ValueError("Only Python files can be imported directly.")
        with open(file_path, "r", encoding="utf-8") as script_file:
            content = script_file.read()
        source_stem = os.path.splitext(os.path.basename(file_path))[0]
        nice_name = source_stem.replace("_", " ").title()
        return self.create_script(
            nice_name=nice_name,
            script_content=content,
            allow_name_conflict=True,
        )

    def _get_archive_service(self):
        """Creates a focused archive service bound to this model.

        Returns:
            ScriptLibraryArchiveService: Archive service for the current model.
        """
        from gt.tools.script_library.script_library_archive import (
            ScriptLibraryArchiveService,
        )

        return ScriptLibraryArchiveService(self)

    def export_script(self, script_id, target_path):
        """Exports one script and its managed icon as a compressed archive.

        Args:
            script_id (str): Stable script identifier.
            target_path (str): Target archive path.

        Returns:
            str: Generated archive path.
        """
        return self._get_archive_service().export_script(script_id, target_path)

    def export_all(self, target_path):
        """Exports the complete library as a compressed backup.

        Args:
            target_path (str): Target backup archive path.

        Returns:
            str: Generated backup archive path.
        """
        return self._get_archive_service().export_all(target_path)

    def read_archive_manifest(self, archive_path):
        """Reads and validates a Script Library archive manifest.

        Args:
            archive_path (str): Existing archive path.

        Returns:
            dict: Validated archive manifest.
        """
        return self._get_archive_service().read_archive_manifest(archive_path)

    def get_archive_summary(self, archive_path):
        """Gets archive counts and stable-ID conflicts without changing data.

        Args:
            archive_path (str): Existing archive path.

        Returns:
            dict: Archive count, scope, and conflicting stable IDs.
        """
        return self._get_archive_service().get_archive_summary(archive_path)

    def import_archive(self, archive_path, conflict_policy="copy"):
        """Imports a script or library archive without arbitrary extraction.

        Args:
            archive_path (str): Existing Script Library archive.
            conflict_policy (str, optional): One of copy, replace, or skip.

        Returns:
            dict: Imported, replaced, and skipped stable IDs.
        """
        return self._get_archive_service().import_archive(
            archive_path, conflict_policy=conflict_policy
        )

    def get_unique_script_file_name(self, requested_stem):
        """Builds a non-conflicting Python file name.

        Args:
            requested_stem (str): Requested file stem.

        Returns:
            str: Unique Python file name.
        """
        clean_stem = self.sanitize_file_stem(requested_stem)
        known_files = {os.path.normcase(item.file_name) for item in self.scripts}
        candidate = f"{clean_stem}{ScriptLibraryConstants.SCRIPT_EXTENSION}"
        index = 2
        while os.path.normcase(candidate) in known_files or os.path.exists(
            self.get_managed_file_path(candidate)
        ):
            candidate = f"{clean_stem}_{index}{ScriptLibraryConstants.SCRIPT_EXTENSION}"
            index += 1
        return candidate

    def get_managed_file_path(self, file_name):
        """Resolves a file name inside the exact Prefs-managed scripts folder.

        Args:
            file_name (str): File name without directory traversal.

        Returns:
            str or None: Safe absolute path, or None for invalid input.
        """
        if not file_name or os.path.basename(str(file_name)) != str(file_name):
            return None
        scripts_dir = os.path.abspath(self.get_scripts_dir(create_if_missing=True))
        target_path = os.path.abspath(os.path.join(scripts_dir, file_name))
        if os.path.commonpath([scripts_dir, target_path]) != scripts_dir:
            return None
        return target_path

    def set_edit_mode(self, is_edit_mode):
        """Stores the active edit/use mode through Prefs.

        Args:
            is_edit_mode (bool): New edit-mode state.
        """
        self.preferences.set_bool(
            ScriptLibraryConstants.PREF_KEY_EDIT_MODE, bool(is_edit_mode)
        )
        self.preferences.save()

    def get_edit_mode(self):
        """Gets the stored edit/use mode.

        Returns:
            bool: True when edit mode is active.
        """
        return self.preferences.get_bool(
            ScriptLibraryConstants.PREF_KEY_EDIT_MODE, default=False
        )

    def set_show_details_in_use_mode(self, should_show):
        """Stores whether the use-mode details panel is visible.

        Args:
            should_show (bool): Whether thumbnail and description details are shown.
        """
        self.preferences.set_bool(
            ScriptLibraryConstants.PREF_KEY_SHOW_DETAILS_IN_USE_MODE,
            bool(should_show),
        )
        self.preferences.save()

    def get_show_details_in_use_mode(self):
        """Gets whether the use-mode details panel is visible.

        Returns:
            bool: True when use mode shows the right-side details panel.
        """
        return self.preferences.get_bool(
            ScriptLibraryConstants.PREF_KEY_SHOW_DETAILS_IN_USE_MODE,
            default=True,
        )

    def set_auto_save(self, should_auto_save):
        """Stores whether editor field changes are saved automatically.

        Args:
            should_auto_save (bool): Whether edits should save automatically.
        """
        self.preferences.set_bool(
            ScriptLibraryConstants.PREF_KEY_AUTO_SAVE, bool(should_auto_save)
        )
        self.preferences.save()

    def get_auto_save(self):
        """Gets whether editor field changes are saved automatically.

        Returns:
            bool: True when automatic saving is enabled.
        """
        return self.preferences.get_bool(
            ScriptLibraryConstants.PREF_KEY_AUTO_SAVE, default=True
        )

    def set_selected_script_id(self, script_id):
        """Stores the last selected script identifier.

        Args:
            script_id (str): Stable script identifier or empty string.
        """
        self.preferences.set_string(
            ScriptLibraryConstants.PREF_KEY_SELECTED_SCRIPT_ID, str(script_id or "")
        )
        self.preferences.save()

    def get_selected_script_id(self):
        """Gets the last selected script identifier.

        Returns:
            str: Stored script identifier.
        """
        return self.preferences.get_string(
            ScriptLibraryConstants.PREF_KEY_SELECTED_SCRIPT_ID, default=""
        )

    def set_last_directory(self, directory_path):
        """Stores the last valid file-dialog directory.

        Args:
            directory_path (str): Directory path to store.
        """
        if directory_path and os.path.isdir(directory_path):
            self.preferences.set_string(
                ScriptLibraryConstants.PREF_KEY_LAST_DIRECTORY, directory_path
            )
            self.preferences.save()

    def get_last_directory(self):
        """Gets the last valid file-dialog directory.

        Returns:
            str: Existing directory or the Prefs-managed scripts folder.
        """
        directory_path = self.preferences.get_string(
            ScriptLibraryConstants.PREF_KEY_LAST_DIRECTORY, default=""
        )
        if directory_path and os.path.isdir(directory_path):
            return directory_path
        return self.get_scripts_dir()

    def set_splitter_sizes(self, sizes):
        """Stores the two primary splitter sizes through Prefs.

        Args:
            sizes (list): Integer splitter sizes.
        """
        if not isinstance(sizes, (list, tuple)) or len(sizes) != 2:
            return
        preferences = self.preferences.get_raw_preferences()
        preferences[ScriptLibraryConstants.PREF_KEY_SPLITTER_SIZES] = [
            int(size) for size in sizes
        ]
        self.preferences.save()

    def get_splitter_sizes(self):
        """Gets stored splitter sizes.

        Returns:
            list: Two positive splitter sizes or an empty list.
        """
        sizes = self.preferences.get_raw_preferences().get(
            ScriptLibraryConstants.PREF_KEY_SPLITTER_SIZES, []
        )
        if not isinstance(sizes, list) or len(sizes) != 2:
            return []
        try:
            return [max(1, int(size)) for size in sizes]
        except (TypeError, ValueError):
            return []


def run_script_by_id(script_id):
    """Runs a stored Script Library item by stable identifier.

    This function is intentionally module-level so Maya shelf buttons can call a
    short command that always resolves the latest saved script content.

    Args:
        script_id (str): Stable script identifier.

    Returns:
        dict: Globals produced by script execution.
    """
    model = ScriptLibraryModel()
    return model.execute_script(script_id)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    print(ScriptLibraryModel().get_scripts(include_hidden=True))
