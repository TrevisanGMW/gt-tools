"""Ordered text inputs represented by virtual scene identities, never source files."""

import hashlib
import os
import re
import tempfile
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_task_base as base
from gt.tools.batch_processor.tasks.task_input import TaskInput
from gt.ui import resource_library as ui_res_lib

MAX_NUMBER_RANGE_COUNT = 100000
INPUT_MODE_TABLE = "table"
INPUT_MODE_NUMBERS = "number_range"
INPUT_MODE_FILE = "file"
INPUT_MODES = (INPUT_MODE_TABLE, INPUT_MODE_NUMBERS, INPUT_MODE_FILE)
INPUT_MODE_LABELS = {INPUT_MODE_TABLE: "String Table", INPUT_MODE_NUMBERS: "Number Range",
                     INPUT_MODE_FILE: "Input File"}
NUMBER_FILTER_ALL = "all"
NUMBER_FILTER_ODD = "odd"
NUMBER_FILTER_EVEN = "even"
NUMBER_FILTERS = (NUMBER_FILTER_ALL, NUMBER_FILTER_ODD, NUMBER_FILTER_EVEN)
NUMBER_FILTER_LABELS = {NUMBER_FILTER_ALL: "All Numbers", NUMBER_FILTER_ODD: "Odd Only",
                        NUMBER_FILTER_EVEN: "Even Only"}
_SKIP_TOKEN_PATTERN = re.compile(r"^(-?\d+)(?:\s*(?:-|\.\.)\s*(-?\d+))?$")


def get_input_mode(settings):
    """Gets the configured input mode, falling back to the string table.

    Args:
        settings (dict): Input Strings task settings.

    Returns:
        str: One of INPUT_MODES.
    """
    mode = settings.get("input_mode")
    return mode if mode in INPUT_MODES else INPUT_MODE_TABLE


def read_input_file_lines(file_path):
    """Reads the nonblank lines of a UTF-8 text file, keeping their literal text.

    Args:
        file_path (str): Resolved text file path.

    Returns:
        list: Nonblank lines in file order.

    Raises:
        OSError: When the file cannot be read.
        UnicodeDecodeError: When the file is not UTF-8 text.
    """
    with open(file_path, "r", encoding="utf-8-sig") as line_file:
        return [line for line in line_file.read().splitlines() if line.strip()]


def get_row_enabled_states(settings):
    """Gets one active flag per string row; rows without a stored flag are active.

    Args:
        settings (dict): Input Strings task settings.

    Returns:
        list: Booleans aligned with settings["strings"].
    """
    values = settings.get("strings") or []
    states = settings.get("string_enabled")
    states = states if isinstance(states, list) else []
    return [bool(states[index]) if index < len(states) else True for index in range(len(values))]


def get_row_indexes(settings):
    """Gets the one-based run index of each string row, skipping inactive and blank rows.

    Args:
        settings (dict): Input Strings task settings.

    Returns:
        list: One int per row, or None for rows that are not processed.
    """
    indexes = []
    next_index = 1
    for value, enabled in zip(settings.get("strings") or [], get_row_enabled_states(settings)):
        if enabled and isinstance(value, str) and value.strip():
            indexes.append(next_index)
            next_index += 1
        else:
            indexes.append(None)
    return indexes


def is_whole_number(value):
    """Checks whether a setting value is an int and not a bool.

    Args:
        value (object): Value to check.

    Returns:
        bool: True for whole numbers.
    """
    return isinstance(value, int) and not isinstance(value, bool)


def parse_number_skip_list(text):
    """Parses comma or space separated numbers and inclusive ranges such as "4, 8, 10-12".

    Args:
        text (str): User-entered skip list; blank means nothing is skipped.

    Returns:
        set: Numbers to skip.

    Raises:
        ValueError: When an entry is not a whole number or a range.
    """
    tokens = []
    for entry in re.split(r"[,;\n]+", str(text or "")):
        entry = entry.strip()
        tokens.extend([entry] if _SKIP_TOKEN_PATTERN.match(entry) else entry.split())
    skipped = set()
    for token in tokens:
        match = _SKIP_TOKEN_PATTERN.match(token)
        if not match:
            raise ValueError(f'"{token}" is not a number or a range like 10-12.')
        first = int(match.group(1))
        last = int(match.group(2)) if match.group(2) is not None else first
        if abs(last - first) > MAX_NUMBER_RANGE_COUNT:
            raise ValueError(f'Skip range "{token}" is too large.')
        low, high = sorted((first, last))
        skipped.update(range(low, high + 1))
    return skipped


def get_number_range_count(settings):
    """Gets how many values the start, end, and step produce before filtering.

    Args:
        settings (dict): Input Strings task settings.

    Returns:
        int: Value count, or 0 when the bounds or step are invalid.
    """
    start, end = settings.get("number_start"), settings.get("number_end")
    step = settings.get("number_step", 1)
    if not all(is_whole_number(value) for value in (start, end, step)) or step < 1:
        return 0
    return abs(end - start) // step + 1


def get_number_values(settings):
    """Gets the stepped number range after the odd/even filter and skip list.

    Args:
        settings (dict): Input Strings task settings.

    Returns:
        list: Number values as strings, or an empty list for invalid settings.
    """
    if not get_number_range_count(settings):
        return []
    try:
        skipped = parse_number_skip_list(settings.get("number_skip"))
    except ValueError:
        return []
    start, end, step = settings["number_start"], settings["number_end"], settings.get("number_step", 1)
    direction = 1 if end >= start else -1
    number_filter = settings.get("number_filter", NUMBER_FILTER_ALL)
    values = []
    for number in range(start, end + direction, step * direction):
        if number in skipped:
            continue
        if number_filter == NUMBER_FILTER_ODD and number % 2 == 0:
            continue
        if number_filter == NUMBER_FILTER_EVEN and number % 2 != 0:
            continue
        values.append(str(number))
    return values


def get_table_values(settings):
    """Gets the active, nonblank string table values in run order.

    Args:
        settings (dict): Input Strings task settings.

    Returns:
        list: Processed table values.
    """
    return [value for value, index in zip(settings.get("strings") or [], get_row_indexes(settings))
            if index is not None]


class TaskInputStrings(TaskInput):
    """Creates one independent empty-scene work item per table row, number, or file line."""

    task_type = constants.TaskType.INPUT_STRINGS
    default_display_name = "Input Strings"
    icon = ui_res_lib.Icon.batch_task_input_strings

    def get_default_settings(self):
        """Gets serializable mode, text, number range, file, and segmentation settings.

        Returns:
            dict: Task defaults.
        """
        return {
            "input_mode": INPUT_MODE_TABLE, "strings": [], "string_enabled": [],
            "number_start": 1, "number_end": 10, "number_step": 1, "number_filter": NUMBER_FILTER_ALL,
            "number_skip": "", "input_file_path": "", "include_in_task_index": False,
            "start_new_input_list": False, "force_segment_separator": False,
            "segment_name": "", "segment_color": "blue_light_sky",
        }

    def get_source_path_template(self):
        """Gets the empty source template because this task does not read scene files.

        Returns:
            str: Empty path.
        """
        return ""

    def get_input_dir(self, project):
        """Gets an identity namespace without creating a directory.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            str: Absolute virtual input root.
        """
        root = project.get_project_dir() if project else ""
        task_key = hashlib.sha256(self.id.encode("utf-8")).hexdigest()[:12]
        return os.path.join(root or tempfile.gettempdir(), ".batch-string-inputs", task_key)

    def get_input_file_path(self, project):
        """Resolves the input file path, supporting project-relative and templated paths.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            str: Resolved path, or an empty string when it cannot be resolved.
        """
        path = self.settings.get("input_file_path") or ""
        if not path or not project:
            return path if path and os.path.isabs(path) else ""
        return project.resolve_template_path(path, task=self)

    def get_input_values(self, project):
        """Gets the ordered values that become work items for the active mode.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            list: Processed text values in run order.

        Raises:
            OSError: When the input file cannot be read.
            UnicodeDecodeError: When the input file is not UTF-8 text.
        """
        mode = get_input_mode(self.settings)
        if mode == INPUT_MODE_NUMBERS:
            return get_number_values(self.settings)
        if mode == INPUT_MODE_FILE:
            return read_input_file_lines(self.get_input_file_path(project))
        return get_table_values(self.settings)

    def validate(self, project):
        """Validates the active mode without requiring an input directory.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            ValidationResult: Errors and blank-row diagnostics.
        """
        mode = get_input_mode(self.settings)
        if mode == INPUT_MODE_NUMBERS:
            return self.validate_number_range()
        if mode == INPUT_MODE_FILE:
            return self.validate_input_file(project)
        return self.validate_table()

    def validate_table(self):
        """Validates the string table rows and their active states.

        Returns:
            ValidationResult: Errors and blank-row diagnostics.
        """
        result = base.ValidationResult()
        values = self.settings.get("strings")
        if not isinstance(values, list) or any(not isinstance(value, str) for value in values):
            result.add_error("Strings must be a list of text values.")
            return result
        if not isinstance(self.settings.get("string_enabled", []), list):
            result.add_error("String active states must be a list of booleans.")
            return result
        if any("\x00" in value or "\n" in value or "\r" in value for value in values):
            result.add_error("Each string must occupy one row and cannot contain null characters.")
        states = get_row_enabled_states(self.settings)
        if not any(value.strip() and enabled for value, enabled in zip(values, states)):
            result.add_error("Add at least one active, nonblank input string.")
        elif any(not value.strip() and enabled for value, enabled in zip(values, states)):
            result.add_warning("Blank input string rows will be skipped.")
        return result

    def validate_number_range(self):
        """Validates the number range bounds and size.

        Returns:
            ValidationResult: Errors for invalid or oversized ranges.
        """
        result = base.ValidationResult()
        count = get_number_range_count(self.settings)
        if not count:
            result.add_error("Number range start and end must be whole numbers, and step must be 1 or more.")
            return result
        if count > MAX_NUMBER_RANGE_COUNT:
            result.add_error(f"Number range produces {count} inputs; the limit is {MAX_NUMBER_RANGE_COUNT}.")
            return result
        if self.settings.get("number_filter", NUMBER_FILTER_ALL) not in NUMBER_FILTERS:
            result.add_error(f"Unknown number filter: {self.settings.get('number_filter')}")
            return result
        try:
            parse_number_skip_list(self.settings.get("number_skip"))
        except ValueError as exception:
            result.add_error(f"Invalid skip list: {exception}")
            return result
        if not get_number_values(self.settings):
            result.add_error("The odd/even filter and skip list exclude every number in the range.")
        return result

    def validate_input_file(self, project):
        """Validates that the input file resolves, is readable, and has at least one line.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            ValidationResult: Errors for missing, unreadable, or empty files.
        """
        result = base.ValidationResult()
        if not self.settings.get("input_file_path"):
            result.add_error("Choose an input file.")
            return result
        file_path = self.get_input_file_path(project)
        if not file_path:
            result.add_error("Input file path is relative, but the project directory is not set.")
        elif not os.path.isfile(file_path):
            result.add_error(f"Input file not found: {file_path}")
        else:
            try:
                if not read_input_file_lines(file_path):
                    result.add_error(f"Input file has no nonblank lines: {file_path}")
            except (OSError, UnicodeDecodeError) as exception:
                result.add_error(f"Unable to read input file as UTF-8 text: {exception}")
        return result

    def prepare(self, project, context=None):
        """Builds ordered items, retaining duplicate values and literal text.

        Args:
            project (BatchProcessorModel): Owning project.
            context (dict, optional): Runner context.

        Returns:
            list: Virtual Maya scene work items carrying the original text.
        """
        errors = self.validate(project).errors
        if errors:
            raise ValueError("; ".join(errors))
        root = self.get_input_dir(project)
        items = []
        for index, value in enumerate(self.get_input_values(project), 1):
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
            name = f"string_{index:06d}_{os.path.basename(root)}_{digest}.ma"
            path = os.path.join(root, name)
            items.append(base.WorkItem(source_path=path, source_root=root, metadata={
                "input_string": value, "input_string_index": index,
                "input_string_path": base.normalize_path(path),
            }))
        return items

    def discover_files(self, project):
        """Gets virtual identities for the existing tracker job protocol.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            list: Ordered identities; these paths are never created or opened.
        """
        if self.validate(project).errors:
            return []
        return [item.source_path for item in self.prepare(project)]
