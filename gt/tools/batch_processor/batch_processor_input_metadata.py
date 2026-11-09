"""
Batch Processor Input Metadata

Pure helpers for the Input Metadata task. Rows attach up to five user-defined
text values to incoming work items. Each value is always available by slot
number and, when the slot is named, by its cleaned name:

    {input-meta-1}          slot 1, always available
    {input-meta-seed}       slot 1 when it is named "seed"
    work_item.metadata["input_metadata"] == {"1": "517", "seed": "517"}

This module has no Maya or Qt imports so it stays importable and testable
outside Maya.
"""

import fnmatch
import os
import re
import uuid


MAX_SLOTS = 5
METADATA_KEY = "input_metadata"
VARIABLE_PREFIX = "input-meta-"
WILDCARD_CHARACTERS = ("*", "?", "[")
_INVALID_NAME_CHARACTERS = re.compile(r"[^a-z0-9]+")
_METADATA_VARIABLE_PATTERN = re.compile(r"\{(input[-_]meta[-_][a-zA-Z0-9_-]+)\}", flags=re.IGNORECASE)


def clean_slot_name(raw_name):
    """Converts a user-typed slot name into a variable-safe name.

    Lowercases the name and replaces every run of characters other than
    letters and digits with a single hyphen, so "Shot Code" becomes
    "shot-code" and "speed_scale" becomes "speed-scale".

    Args:
        raw_name (str): Name typed by the user.

    Returns:
        str: Cleaned name, or an empty string when nothing usable remains.
    """
    return _INVALID_NAME_CHARACTERS.sub("-", str(raw_name or "").strip().lower()).strip("-")


def get_slot_name_error(cleaned_name):
    """Gets the reason a cleaned slot name cannot be used.

    Args:
        cleaned_name (str): Name returned by clean_slot_name.

    Returns:
        str: Error message, or an empty string for a valid or empty name.
    """
    if cleaned_name and cleaned_name[0].isdigit():
        return f'Slot name "{cleaned_name}" cannot start with a digit; numbers are reserved for slot IDs.'
    return ""


def get_slot_count(settings):
    """Gets the number of active value slots.

    Args:
        settings (dict): Input Metadata task settings.

    Returns:
        int: Active slot count clamped between 1 and MAX_SLOTS.
    """
    try:
        slot_count = int(settings.get("slot_count", 1))
    except (TypeError, ValueError):
        slot_count = 1
    return max(1, min(MAX_SLOTS, slot_count))


def pad_values(values):
    """Pads or trims a value list to exactly MAX_SLOTS strings.

    Args:
        values (list): Raw slot values.

    Returns:
        list: MAX_SLOTS string values.
    """
    values = list(values) if isinstance(values, (list, tuple)) else []
    values = ["" if value is None else str(value) for value in values[:MAX_SLOTS]]
    return values + [""] * (MAX_SLOTS - len(values))


def get_slot_names(settings):
    """Gets the cleaned name of every slot, including inactive ones.

    Args:
        settings (dict): Input Metadata task settings.

    Returns:
        list: MAX_SLOTS cleaned names; unnamed slots are empty strings.
    """
    return [clean_slot_name(name) for name in pad_values(settings.get("slot_names"))]


def get_slot_keys(slot_index, slot_name):
    """Gets the metadata keys written for one slot.

    Args:
        slot_index (int): Zero-based slot index.
        slot_name (str): Cleaned slot name, possibly empty.

    Returns:
        list: Slot number key followed by the name key when named.
    """
    keys = [str(slot_index + 1)]
    if slot_name:
        keys.append(slot_name)
    return keys


def create_row(input_key="", values=None, enabled=True):
    """Creates a serializable metadata row with a fresh ID.

    Args:
        input_key (str, optional): Input name, relative path, or wildcard pattern.
        values (list, optional): Slot values in slot order.
        enabled (bool, optional): Whether the row applies.

    Returns:
        dict: Row data.
    """
    return {"id": uuid.uuid4().hex, "enabled": bool(enabled), "input": str(input_key or ""),
            "values": pad_values(values)}


def normalize_row(row):
    """Copies a stored row, filling missing fields and an ID.

    Args:
        row (dict): Stored row data.

    Returns:
        dict: Complete row data.
    """
    row = dict(row)
    row["id"] = row.get("id") or uuid.uuid4().hex
    row["enabled"] = bool(row.get("enabled", True))
    row["input"] = str(row.get("input") or "")
    row["values"] = pad_values(row.get("values"))
    return row


def validate_rows(rows):
    """Validates stored rows before they are saved, imported, or applied.

    Args:
        rows (list): Row dictionaries.

    Raises:
        ValueError: If a row is malformed or repeats an ID.
    """
    if not isinstance(rows, list):
        raise ValueError("Metadata rows must be a list of objects.")
    row_ids = set()
    for index, row in enumerate(rows, 1):
        if not isinstance(row, dict):
            raise ValueError(f"Metadata row {index} must be an object.")
        if not isinstance(row.get("input", ""), str):
            raise ValueError(f"Metadata row {index}: input must be text.")
        if not isinstance(row.get("enabled", True), bool):
            raise ValueError(f"Metadata row {index}: enabled must be true or false.")
        values = row.get("values", [])
        if not isinstance(values, list) or len(values) > MAX_SLOTS:
            raise ValueError(f"Metadata row {index}: values must be a list of up to {MAX_SLOTS} strings.")
        if any(not isinstance(value, str) for value in values):
            raise ValueError(f"Metadata row {index}: every value must be text.")
        row_id = row.get("id")
        if row_id is not None:
            if not isinstance(row_id, str) or not row_id or row_id in row_ids:
                raise ValueError(f"Metadata row {index} has an empty or duplicate ID.")
            row_ids.add(row_id)


def get_settings_errors(settings):
    """Collects slot and row errors from task settings.

    Args:
        settings (dict): Input Metadata task settings.

    Returns:
        list: Error messages; empty when the settings are usable.
    """
    errors = []
    try:
        validate_rows(settings.get("metadata_rows", []))
    except ValueError as exception:
        errors.append(str(exception))
    seen_names = {}
    slot_count = get_slot_count(settings)
    for slot_index, name in enumerate(get_slot_names(settings)[:slot_count]):
        error = get_slot_name_error(name)
        if error:
            errors.append(f"Slot {slot_index + 1}: {error}")
        if name and name in seen_names:
            errors.append(f'Slots {seen_names[name]} and {slot_index + 1} are both named "{name}".')
        seen_names.setdefault(name, slot_index + 1)
    return errors


def normalize_match_text(text):
    """Normalizes a row key or item identity for comparison.

    Args:
        text (str): Raw text.

    Returns:
        str: Lowercase text with forward slashes and no surrounding slashes.
    """
    return str(text or "").strip().replace("\\", "/").strip("/").lower()


def get_item_identities(relative_path, source_path="", input_file=""):
    """Gets every identity a metadata row can use to match an item.

    Args:
        relative_path (str): Source-relative path, such as "walk/walk_090.ma".
        source_path (str, optional): Original source path, used when no relative path exists.
        input_file (str, optional): Input Pairs custom name or file stem.

    Returns:
        list: Unique normalized identities: relative path, relative path
        without extension, file name, file stem, and input file name.
    """
    relative_path = normalize_match_text(relative_path or os.path.basename(str(source_path or "")))
    file_name = relative_path.rsplit("/", 1)[-1]
    candidates = [
        relative_path,
        os.path.splitext(relative_path)[0],
        file_name,
        os.path.splitext(file_name)[0],
        normalize_match_text(input_file),
    ]
    identities = []
    for candidate in candidates:
        if candidate and candidate not in identities:
            identities.append(candidate)
    return identities


def row_matches(row_input, identities):
    """Checks whether a row key matches any identity of an item.

    Keys without wildcards must equal one identity. Keys with *, ?, or [ are
    matched as glob patterns.

    Args:
        row_input (str): Row input key.
        identities (list): Identities from get_item_identities.

    Returns:
        bool: True when the row applies to the item.
    """
    key = normalize_match_text(row_input)
    if not key:
        return False
    if any(character in key for character in WILDCARD_CHARACTERS):
        return any(fnmatch.fnmatchcase(identity, key) for identity in identities)
    return key in identities


def resolve_values(rows, slot_count, identities):
    """Resolves slot values for one item from ordered rows.

    Rows apply top to bottom. A non-empty cell overrides earlier rows, so a
    wildcard default row can sit above specific rows. Empty cells set nothing.

    Args:
        rows (list): Row dictionaries in table order.
        slot_count (int): Number of active slots.
        identities (list): Identities from get_item_identities.

    Returns:
        tuple: Slot values by zero-based index (dict) and the IDs of matched rows (list).
    """
    values = {}
    matched_row_ids = []
    for row in rows:
        row = normalize_row(row)
        if not row["enabled"] or not row_matches(row["input"], identities):
            continue
        matched_row_ids.append(row["id"])
        for slot_index, value in enumerate(row["values"][:slot_count]):
            if value != "":
                values[slot_index] = value
    return values, matched_row_ids


def merge_metadata(existing, values, slot_names, slot_count):
    """Merges resolved values into an item's existing input metadata.

    Every active slot is written so its variables always resolve. A slot this
    task leaves empty keeps any value an earlier Input Metadata task set.

    Args:
        existing (dict): Incoming input metadata, possibly empty.
        values (dict): Slot values by zero-based index.
        slot_names (list): Cleaned slot names.
        slot_count (int): Number of active slots.

    Returns:
        dict: New input metadata dictionary.
    """
    merged = dict(existing or {})
    for slot_index in range(slot_count):
        value = values.get(slot_index, "")
        for key in get_slot_keys(slot_index, slot_names[slot_index]):
            if value != "" or key not in merged:
                merged[key] = value
    return merged


def build_environment_values(input_metadata):
    """Converts item input metadata into runtime variable values.

    Args:
        input_metadata (dict): Values stored under METADATA_KEY.

    Returns:
        dict: Variable names such as "input-meta-seed" mapped to text values.
    """
    if not isinstance(input_metadata, dict):
        return {}
    return {f"{VARIABLE_PREFIX}{clean_slot_name(key)}": "" if value is None else str(value)
            for key, value in input_metadata.items() if clean_slot_name(key)}


def is_metadata_variable_key(key):
    """Checks whether a normalized variable key belongs to input metadata.

    Args:
        key (str): Normalized lowercase hyphenated key without braces.

    Returns:
        bool: True for keys such as "input-meta-1" or "input-meta-seed".
    """
    return str(key or "").startswith(VARIABLE_PREFIX)


def replace_metadata_variables(text, runtime_values):
    """Replaces {input-meta-...} variables with literal runtime values.

    Values are inserted literally; variables inside metadata values are not
    expanded again. Unknown metadata variables resolve to an empty string,
    matching {input-string} outside an item.

    Args:
        text (str): Text that may contain metadata variables.
        runtime_values (dict): Current runtime variable values.

    Returns:
        str: Text with metadata variables replaced.
    """
    def replace_match(match):
        """Replaces one metadata variable.

        Args:
            match (re.Match): Variable match.

        Returns:
            str: Runtime value or an empty string.
        """
        key = match.group(1).lower().replace("_", "-")
        return str(runtime_values.get(key, ""))

    return _METADATA_VARIABLE_PATTERN.sub(replace_match, str(text))
