"""Safe compressed import and export service for Script Library data."""

from gt.tools.script_library.script_library_constants import ScriptLibraryConstants
from gt.tools.script_library.script_library_item import ScriptLibraryItem
import json
import os
import uuid
import zipfile


class ScriptLibraryArchiveService:
    """Reads and writes self-contained Script Library archives."""

    def __init__(self, model):
        """Initializes the archive service.

        Args:
            model (ScriptLibraryModel): Model that owns scripts and managed files.
        """
        self.model = model

    def export_script(self, script_id, target_path):
        """Exports one script and its managed icon as a compressed archive.

        Args:
            script_id (str): Stable script identifier.
            target_path (str): Target archive path.

        Returns:
            str: Generated archive path.
        """
        item = self.model.get_script(script_id)
        if not item:
            raise KeyError(f'Unable to find script ID "{script_id}".')
        target_path = self.model.ensure_extension(
            target_path, ScriptLibraryConstants.SCRIPT_ARCHIVE_EXTENSION
        )
        manifest = self._build_archive_manifest([item], scope="script")
        self._write_archive(target_path=target_path, items=[item], manifest=manifest)
        return target_path

    def export_all(self, target_path):
        """Exports the complete library as a compressed backup.

        Args:
            target_path (str): Target backup archive path.

        Returns:
            str: Generated backup archive path.
        """
        target_path = self.model.ensure_extension(
            target_path, ScriptLibraryConstants.LIBRARY_ARCHIVE_EXTENSION
        )
        manifest = self._build_archive_manifest(self.model.scripts, scope="library")
        self._write_archive(
            target_path=target_path,
            items=self.model.scripts,
            manifest=manifest,
        )
        return target_path

    @staticmethod
    def _build_archive_manifest(items, scope):
        """Builds the manifest stored in a script archive.

        Args:
            items (list): ScriptLibraryItem objects included in the archive.
            scope (str): Archive scope, either script or library.

        Returns:
            dict: JSON-compatible archive manifest.
        """
        return {
            "format": ScriptLibraryConstants.ARCHIVE_FORMAT,
            "version": ScriptLibraryConstants.ARCHIVE_VERSION,
            "scope": scope,
            "scripts": [item.to_dict() for item in items],
        }

    def _write_archive(self, target_path, items, manifest):
        """Writes a compressed archive without mutating source files.

        Args:
            target_path (str): Target archive path.
            items (list): ScriptLibraryItem objects to include.
            manifest (dict): Archive manifest.
        """
        missing_scripts = []
        for item in items:
            script_path = self.model.get_script_path(item)
            if not script_path or not os.path.isfile(script_path):
                missing_scripts.append(item.file_name)
        if missing_scripts:
            missing_list = ", ".join(sorted(missing_scripts))
            raise IOError(f"Unable to export missing script file(s): {missing_list}")
        target_dir = os.path.dirname(os.path.abspath(target_path))
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir)
        written_assets = set()
        with zipfile.ZipFile(
            target_path, "w", compression=zipfile.ZIP_DEFLATED
        ) as archive:
            archive.writestr(
                ScriptLibraryConstants.ARCHIVE_MANIFEST,
                json.dumps(manifest, indent=2, ensure_ascii=False),
            )
            for item in items:
                script_path = self.model.get_script_path(item)
                script_archive_path = self._get_script_archive_member(item.file_name)
                archive.write(script_path, script_archive_path)
                if item.icon_mode not in (
                    ScriptLibraryConstants.ICON_MODE_CUSTOM,
                    ScriptLibraryConstants.ICON_MODE_SNAPSHOT,
                ):
                    continue
                icon_path = self.model.get_managed_file_path(item.icon_value)
                icon_name = os.path.basename(item.icon_value)
                if (
                    not icon_path
                    or not os.path.isfile(icon_path)
                    or icon_name in written_assets
                ):
                    continue
                archive.write(icon_path, self._get_asset_archive_member(icon_name))
                written_assets.add(icon_name)

    def read_archive_manifest(self, archive_path):
        """Reads and validates a Script Library archive manifest.

        Args:
            archive_path (str): Existing archive path.

        Returns:
            dict: Validated archive manifest.

        Raises:
            IOError: If the archive does not exist.
            ValueError: If the archive is invalid or exceeds safety limits.
        """
        if not archive_path or not os.path.isfile(archive_path):
            raise IOError(f'Archive does not exist: "{archive_path}".')
        try:
            with zipfile.ZipFile(archive_path, "r") as archive:
                self._validate_archive_sizes(archive)
                manifest_bytes = archive.read(ScriptLibraryConstants.ARCHIVE_MANIFEST)
        except (KeyError, zipfile.BadZipFile) as exception:
            raise ValueError(f"Invalid Script Library archive: {exception}")
        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exception:
            raise ValueError(f"Invalid Script Library manifest: {exception}")
        if not isinstance(manifest, dict):
            raise ValueError("Archive manifest must contain a JSON object.")
        if manifest.get("format") != ScriptLibraryConstants.ARCHIVE_FORMAT:
            raise ValueError("Archive format is not recognized.")
        if manifest.get("version") != ScriptLibraryConstants.ARCHIVE_VERSION:
            raise ValueError(f'Unsupported archive version: "{manifest.get("version")}".')
        if not isinstance(manifest.get("scripts"), list):
            raise ValueError("Archive manifest is missing its scripts list.")
        return manifest

    def get_archive_summary(self, archive_path):
        """Gets import counts and stable-ID conflicts without changing data.

        Args:
            archive_path (str): Existing archive path.

        Returns:
            dict: Archive count, scope, and conflicting stable IDs.
        """
        manifest = self.read_archive_manifest(archive_path)
        incoming_ids = []
        for raw_item in manifest.get("scripts", []):
            item = ScriptLibraryItem.from_dict(raw_item)
            if item:
                incoming_ids.append(item.script_id)
        current_ids = {item.script_id for item in self.model.scripts}
        conflicts = [script_id for script_id in incoming_ids if script_id in current_ids]
        return {
            "count": len(incoming_ids),
            "scope": manifest.get("scope", ""),
            "conflicts": conflicts,
        }

    def import_archive(self, archive_path, conflict_policy="copy"):
        """Imports a script or library archive without arbitrary extraction.

        Args:
            archive_path (str): Existing Script Library archive.
            conflict_policy (str, optional): One of copy, replace, or skip.

        Returns:
            dict: Imported, replaced, and skipped stable IDs.

        Raises:
            ValueError: If the policy or archive is invalid.
        """
        if conflict_policy not in ("copy", "replace", "skip"):
            raise ValueError(f'Unsupported conflict policy: "{conflict_policy}".')
        manifest = self.read_archive_manifest(archive_path)
        result = {"imported": [], "replaced": [], "skipped": []}
        with zipfile.ZipFile(archive_path, "r") as archive:
            self._validate_archive_sizes(archive)
            available_members = set(archive.namelist())
            for raw_item in manifest.get("scripts", []):
                incoming_item = ScriptLibraryItem.from_dict(raw_item)
                if not incoming_item:
                    raw_id = raw_item.get("id", "") if isinstance(raw_item, dict) else ""
                    result["skipped"].append(str(raw_id))
                    continue
                script_member = self._get_script_archive_member(incoming_item.file_name)
                if script_member not in available_members:
                    result["skipped"].append(incoming_item.script_id)
                    continue
                script_bytes = archive.read(script_member)
                try:
                    script_content = script_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    result["skipped"].append(incoming_item.script_id)
                    continue
                existing_item = self.model.get_script(incoming_item.script_id)
                if existing_item and conflict_policy == "skip":
                    result["skipped"].append(incoming_item.script_id)
                    continue
                if existing_item and conflict_policy == "replace":
                    target_item = existing_item
                    target_item.nice_name = incoming_item.nice_name
                    target_item.description = incoming_item.description
                    target_item.visible = incoming_item.visible
                    target_item.icon_mode = incoming_item.icon_mode
                    self.model.preferences.write_user_file(
                        target_item.file_name, script_content
                    )
                    result["replaced"].append(target_item.script_id)
                else:
                    target_id = (
                        incoming_item.script_id if not existing_item else uuid.uuid4().hex
                    )
                    target_file_name = self.model.get_unique_script_file_name(
                        os.path.splitext(incoming_item.file_name)[0]
                    )
                    self.model.preferences.write_user_file(
                        target_file_name, script_content
                    )
                    target_item = ScriptLibraryItem(
                        script_id=target_id,
                        file_name=target_file_name,
                        nice_name=incoming_item.nice_name,
                        description=incoming_item.description,
                        visible=incoming_item.visible,
                        icon_mode=incoming_item.icon_mode,
                        order=len(self.model.scripts),
                    )
                    self.model.scripts.append(target_item)
                    result["imported"].append(target_item.script_id)
                target_item.icon_value = self._import_archive_icon(
                    archive=archive,
                    available_members=available_members,
                    incoming_item=incoming_item,
                    target_item=target_item,
                )
        self.model.save_scripts()
        return result

    def _import_archive_icon(self, archive, available_members, incoming_item, target_item):
        """Imports one declared icon asset from an open archive.

        Args:
            archive (ZipFile): Open source archive.
            available_members (set): Archive member names.
            incoming_item (ScriptLibraryItem): Source item metadata.
            target_item (ScriptLibraryItem): Destination item metadata.

        Returns:
            str: Imported icon value or package icon name.
        """
        if incoming_item.icon_mode not in (
            ScriptLibraryConstants.ICON_MODE_CUSTOM,
            ScriptLibraryConstants.ICON_MODE_SNAPSHOT,
        ):
            return incoming_item.icon_value
        source_icon_name = os.path.basename(incoming_item.icon_value)
        icon_member = self._get_asset_archive_member(source_icon_name)
        if not source_icon_name or icon_member not in available_members:
            return source_icon_name
        extension = os.path.splitext(source_icon_name)[1].lower()
        if extension not in ScriptLibraryConstants.SUPPORTED_ICON_EXTENSIONS:
            return ""
        script_stem = os.path.splitext(target_item.file_name)[0]
        suffix = (
            "snapshot"
            if incoming_item.icon_mode == ScriptLibraryConstants.ICON_MODE_SNAPSHOT
            else "icon"
        )
        target_icon_name = f"{script_stem}_{suffix}{extension}"
        target_icon_path = self.model.get_managed_file_path(target_icon_name)
        icon_data = archive.read(icon_member)
        with open(target_icon_path, "wb") as icon_file:
            icon_file.write(icon_data)
        return target_icon_name

    @staticmethod
    def _validate_archive_sizes(archive):
        """Rejects archives with unexpectedly large declared files.

        Args:
            archive (ZipFile): Open archive to validate.

        Raises:
            ValueError: If a member or total archive size exceeds limits.
        """
        total_size = 0
        for file_info in archive.infolist():
            total_size += file_info.file_size
            if file_info.file_size > ScriptLibraryConstants.MAX_ARCHIVE_FILE_SIZE:
                raise ValueError(f'Archive member is too large: "{file_info.filename}".')
        if total_size > ScriptLibraryConstants.MAX_ARCHIVE_SIZE:
            raise ValueError("Archive contents exceed the Script Library size limit.")

    @staticmethod
    def _get_script_archive_member(file_name):
        """Gets the normalized archive member for a Python file.

        Args:
            file_name (str): Python file name.

        Returns:
            str: Safe archive member name.
        """
        return (
            f"{ScriptLibraryConstants.ARCHIVE_SCRIPT_FOLDER}/"
            f"{os.path.basename(file_name)}"
        )

    @staticmethod
    def _get_asset_archive_member(file_name):
        """Gets the normalized archive member for an icon asset.

        Args:
            file_name (str): Icon asset file name.

        Returns:
            str: Safe archive member name.
        """
        return (
            f"{ScriptLibraryConstants.ARCHIVE_ASSET_FOLDER}/"
            f"{os.path.basename(file_name)}"
        )

