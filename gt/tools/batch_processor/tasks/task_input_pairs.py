"""File descriptions and manually named, independent empty-scene inputs."""

import hashlib
import ntpath
import os
import tempfile
import uuid
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as base
from gt.tools.batch_processor.tasks.task_input import TaskInput
from gt.ui import resource_library as resources


INPUT_MODE_FOLDER = "folder"
INPUT_MODE_MANUAL = "manual"
INPUT_MODE_LABELS = {INPUT_MODE_FOLDER: "Folder Pairs", INPUT_MODE_MANUAL: "Manual Pairs"}
PAIR_FILE_VERSION = 1


def create_pair(input_file="", input_string="", enabled=True):
    """Creates a serializable pair with an independent identity.

    Args:
        input_file (str, optional): Relative file path or custom filename stem.
        input_string (str, optional): Literal associated text.
        enabled (bool, optional): Whether the pair should run.

    Returns:
        dict: Pair data with a fresh ID.
    """
    return {"id": uuid.uuid4().hex, "input_file": input_file, "input_string": input_string,
            "enabled": bool(enabled)}


def get_pair_key(input_file):
    """Gets a normalized file identity without resolving a relative path.

    Args:
        input_file (str): Relative path in a pair.

    Returns:
        str: Platform-aware normalized path key.
    """
    return os.path.normcase(os.path.normpath(input_file.replace("\\", "/")))


def validate_pair_rows(rows, mode):
    """Validates row data before importing, reconciling, or preparing it.

    Args:
        rows (list): Serialized pair rows.
        mode (str): Folder or manual mode.

    Raises:
        ValueError: If rows contain invalid data or unsafe relative file paths.
    """
    if mode not in INPUT_MODE_LABELS:
        raise ValueError(f"Unknown input pairs mode: {mode}")
    if not isinstance(rows, list):
        raise ValueError("Pairs must be a list of objects.")
    file_keys = set()
    row_ids = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Pair {index} must be an object.")
        for key in ("input_file", "input_string"):
            if not isinstance(row.get(key), str) or "\x00" in row[key]:
                raise ValueError(f"Pair {index}: {key} must be text without null characters.")
        if not isinstance(row.get("enabled", True), bool):
            raise ValueError(f"Pair {index}: enabled must be a boolean.")
        row_id = row.get("id")
        if row_id is not None:
            if not isinstance(row_id, str) or not row_id or row_id in row_ids:
                raise ValueError(f"Pair {index} has an empty or duplicate ID.")
            row_ids.add(row_id)
        if mode == INPUT_MODE_FOLDER:
            filename = row["input_file"]
            parts = filename.replace("\\", "/").split("/")
            if not filename or ntpath.splitdrive(filename)[0] or parts[0] == "" or ".." in parts:
                raise ValueError(f"Pair {index}: folder filenames must stay relative to the input folder.")
            file_key = get_pair_key(filename)
            if file_key in file_keys:
                raise ValueError(f"Pair {index} repeats a folder file: {filename}")
            file_keys.add(file_key)


def validate_manual_filename(filename):
    """Checks a requested filename stem against Windows and Maya path constraints.

    Args:
        filename (str): User-defined output stem, used literally.

    Returns:
        str: Validation error or an empty string for a valid name.
    """
    if not filename.strip():
        return ""
    if any(character in '<>:"/\\|?*' or ord(character) < 32 for character in filename):
        return "Custom names cannot contain path separators, control characters, or <>:\"|?*."
    if filename.endswith((" ", ".")) or filename in (".", ".."):
        return "Custom names cannot end with a space or a period."
    reserved = {"CON", "PRN", "AUX", "NUL"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10))
    if filename.split(".")[0].upper() in reserved:
        return f"Custom name is reserved by Windows: {filename}"
    return ""


def read_pair_data(data):
    """Validates an imported pair document before any task data is changed.

    Args:
        data (dict): Decoded JSON document.

    Returns:
        tuple: Mode and copied pair rows.

    Raises:
        ValueError: For unsupported versions, modes, or malformed rows.
    """
    if not isinstance(data, dict) or data.get("version") != PAIR_FILE_VERSION:
        raise ValueError("Expected an Input Pairs JSON document with version 1.")
    mode = data.get("mode")
    rows = data.get("pairs")
    validate_pair_rows(rows, mode)
    if mode == INPUT_MODE_MANUAL:
        for row in rows:
            error = validate_manual_filename(row["input_file"])
            if error:
                raise ValueError(error)
    return mode, [dict(row) for row in rows]


class TaskInputPairs(TaskInput):
    """Discovers files with saved descriptions or manually named virtual scene jobs."""

    task_type = constants.TaskType.INPUT_PAIRS
    default_display_name = "Input Pairs"
    icon = resources.Icon.batch_task_input_pairs

    def _normalize_common_settings(self, incoming_settings=None):
        """Ensures rows have IDs while retaining malformed data for validation.

        Args:
            incoming_settings (dict, optional): Raw task settings.
        """
        super()._normalize_common_settings(incoming_settings=incoming_settings)
        for key in ("folder_pairs", "manual_pairs"):
            rows = self.settings.get(key)
            if isinstance(rows, list):
                self.settings[key] = [dict(row, id=row.get("id") or uuid.uuid4().hex)
                                      if isinstance(row, dict) else row for row in rows]

    def get_default_settings(self):
        """Gets independent pair tables, discovery options, and segment settings.

        Returns:
            dict: Serializable defaults.
        """
        settings = super().get_default_settings()
        settings.update(input_mode=INPUT_MODE_FOLDER, folder_pairs=[], manual_pairs=[], excluded_files=[])
        return settings

    def get_input_mode(self):
        """Gets the active pair mode.

        Returns:
            str: Folder or manual mode.
        """
        return self.settings.get("input_mode", INPUT_MODE_FOLDER)

    def get_pairs_key(self):
        """Gets the settings key for the active table.

        Returns:
            str: Pair table settings key.
        """
        return "manual_pairs" if self.get_input_mode() == INPUT_MODE_MANUAL else "folder_pairs"

    def get_source_path_template(self):
        """Gets the discovery template or an empty template for manual jobs.

        Returns:
            str: Source folder template in folder mode.
        """
        return "" if self.get_input_mode() == INPUT_MODE_MANUAL else super().get_source_path_template()

    def get_input_dir(self, project):
        """Gets the folder root or a virtual namespace without creating it.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            str: Absolute input root or an empty string for an unset folder.
        """
        if self.get_input_mode() == INPUT_MODE_MANUAL:
            root = project.get_project_dir() if project else ""
            task_key = hashlib.sha256(self.id.encode("utf-8")).hexdigest()[:12]
            return os.path.join(root or tempfile.gettempdir(), ".batch-pair-inputs", task_key)
        if not project or not str(self.settings.get("source_path") or "").strip():
            return ""
        template = self.get_source_path_template()
        if project.path_uses_project_dir(template) and not project.get_project_dir():
            return ""
        return super().get_input_dir(project)

    def get_folder_file_map(self, project):
        """Discovers accepted files keyed by their portable paths within the folder.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            dict: Relative path key to relative and absolute file paths.
        """
        root = self.get_input_dir(project)
        if not root:
            return {}
        excluded = self.get_hidden_file_keys()
        result = {}
        for path in super().discover_files(project):
            relative = os.path.relpath(path, root).replace("\\", "/")
            key = get_pair_key(relative)
            if key not in excluded and base.path_is_inside_directory(path, root):
                result[key] = (relative, path)
        return result

    def get_hidden_file_keys(self):
        """Gets normalized identities of folder pairs hidden by the user.

        Returns:
            set: Relative file path keys.

        Raises:
            ValueError: When the hidden path list contains malformed values.
        """
        excluded_files = self.settings.get("excluded_files", [])
        if not isinstance(excluded_files, list) or any(not isinstance(value, str) for value in excluded_files):
            raise ValueError("Excluded files must be a list of relative file paths.")
        return {get_pair_key(value) for value in excluded_files}

    def set_pair_rows(self, rows):
        """Stores visible rows while preserving hidden folder descriptions, IDs, and order.

        Args:
            rows (list): Visible pair rows for the current mode.
        """
        mode = self.get_input_mode()
        validate_pair_rows(rows, mode)
        stored_rows = list(rows)
        if mode == INPUT_MODE_FOLDER:
            hidden = self.get_hidden_file_keys()
            visible = {get_pair_key(row["input_file"]) for row in stored_rows}
            for index, row in enumerate(self.settings.get("folder_pairs") or []):
                key = get_pair_key(row["input_file"])
                if key in hidden and key not in visible:
                    stored_rows.insert(min(index, len(stored_rows)), dict(row))
        self.settings[self.get_pairs_key()] = stored_rows

    def get_pair_rows(self, project, synchronize=False):
        """Reconciles folder rows, retaining missing descriptions and dropping empty missing rows.

        Args:
            project (BatchProcessorModel): Owning project.
            synchronize (bool, optional): Whether to save reconciled folder rows.

        Returns:
            list: Copied rows in their saved order with newly discovered files appended.

        Raises:
            ValueError: If the active pair table is malformed.
        """
        mode = self.get_input_mode()
        rows = self.settings.get(self.get_pairs_key())
        validate_pair_rows(rows, mode)
        rows = [dict(row) for row in rows]
        if mode == INPUT_MODE_MANUAL:
            return rows
        files = self.get_folder_file_map(project)
        hidden = self.get_hidden_file_keys()
        retained = []
        seen = set()
        for row in rows:
            key = get_pair_key(row["input_file"])
            if key in hidden:
                continue
            if key in files:
                row["input_file"] = files[key][0]
            if key in files or row["input_string"].strip():
                retained.append(row)
                seen.add(key)
        for key, (relative, path) in files.items():
            if key in seen:
                continue
            row = create_pair(relative)
            row["id"] = uuid.uuid5(uuid.NAMESPACE_URL, f"gt-batch-pair:{self.id}:{key}").hex
            retained.append(row)
        if synchronize:
            self.set_pair_rows(retained)
        return retained

    def get_file_statistics(self, project):
        """Extends input file statistics with assignment, availability, and hidden pair counts.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            dict: File discovery statistics and counts specific to the current pair mode.
        """
        statistics = super().get_file_statistics(project)
        rows = self.get_pair_rows(project)
        manual = self.get_input_mode() == INPUT_MODE_MANUAL
        files = {} if manual else self.get_folder_file_map(project)
        root = self.get_input_dir(project)
        unavailable = [row for row in rows if not manual and get_pair_key(row["input_file"]) not in files]
        missing = [row for row in unavailable if not root or not os.path.isfile(os.path.join(root, row["input_file"]))]
        assigned_count = sum(bool(row["input_string"].strip()) for row in rows)
        statistics.update({
            "pair_count": len(rows),
            "assigned_count": assigned_count,
            "unassigned_count": len(rows) - assigned_count,
            "inactive_count": sum(not row.get("enabled", True) for row in rows),
            "hidden_count": 0 if manual else len(self.get_hidden_file_keys()),
            "unavailable_count": len(unavailable),
            "missing_count": len(missing),
            "missing_assigned_count": sum(bool(row["input_string"].strip()) for row in missing),
            "unnamed_count": sum(not row["input_file"].strip() for row in rows),
            "invalid_name_count": (sum(bool(validate_manual_filename(row["input_file"])) for row in rows)
                                   if manual else 0),
        })
        return statistics

    def validate(self, project):
        """Validates discovery and active names while treating missing assignments as warnings.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            ValidationResult: Input errors and retained-row diagnostics.
        """
        result = base.ValidationResult()
        allow_missing_directory = False
        try:
            rows = self.get_pair_rows(project)
        except (ValueError, TypeError, OSError) as exception:
            result.add_error(str(exception))
            return result
        if self.get_input_mode() == INPUT_MODE_FOLDER:
            result.extend(super().validate(project))
            allow_missing_directory = self.can_skip_missing_directory_validation(project)
            files = self.get_folder_file_map(project)
            missing = sum(get_pair_key(row["input_file"]) not in files for row in rows)
            if missing:
                result.add_warning(f"{missing} unavailable file pair(s) retained; these rows will be skipped.")
            active = any(row.get("enabled", True) and get_pair_key(row["input_file"]) in files for row in rows)
        else:
            active = False
            for row in rows:
                if not row.get("enabled", True):
                    continue
                error = validate_manual_filename(row["input_file"])
                if error:
                    result.add_error(error)
                active = active or bool(row["input_file"].strip())
        if not active and not allow_missing_directory:
            result.add_error("Add at least one active, available input pair with a file name.")
        return result

    def prepare(self, project, context=None):
        """Creates work items carrying both values and stable IDs for every active available pair.

        Args:
            project (BatchProcessorModel): Owning project.
            context (dict, optional): Runner context.

        Returns:
            list: Real file or virtual empty-scene items in table order.

        Raises:
            ValueError: If the active settings are invalid.
        """
        errors = self.validate(project).errors
        if errors:
            raise ValueError("; ".join(errors))
        manual = self.get_input_mode() == INPUT_MODE_MANUAL
        root = self.get_input_dir(project)
        files = {} if manual else self.get_folder_file_map(project)
        items = []
        for row in self.get_pair_rows(project, synchronize=True):
            if not row.get("enabled", True) or not row["input_file"].strip():
                continue
            if not manual and get_pair_key(row["input_file"]) not in files:
                continue
            row_id = row.get("id") or uuid.uuid4().hex
            row_key = hashlib.sha256(row_id.encode("utf-8")).hexdigest()[:16]
            path = (os.path.join(root, row_key, f"{row['input_file']}.ma") if manual
                    else files[get_pair_key(row["input_file"])][1])
            metadata = {"input_pair_id": row_id, "input_string": row["input_string"],
                        "input_string_index": len(items) + 1,
                        "input_file": row["input_file"] if manual else os.path.splitext(os.path.basename(path))[0]}
            if manual:
                metadata["input_string_path"] = base.normalize_path(path)
            items.append(base.WorkItem(source_path=path, source_root=os.path.dirname(path) if manual else root,
                                       metadata=metadata))
        return items

    def discover_files(self, project):
        """Gets available pair identities for the existing worker scheduling protocol.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            list: Real or virtual source paths, or an empty list for invalid settings.
        """
        if self.validate(project).errors:
            return []
        return [item.source_path for item in self.prepare(project)]
