"""
Batch Processor Run Settings

Pure helpers for run settings that may change while a multi-instance run is in
progress. "Settings Override" tasks contribute overrides that take effect at
segment barriers, and the tracker can change the same values live. This module
has no Maya or Qt dependencies so it can be unit tested and imported anywhere.
"""

WORKER_COUNT = "worker_count"
MAX_RETRIES = "max_retries"
TIMEOUT_MINUTES = "timeout_minutes"
PREFERRED_MAYA_VERSION = "preferred_maya_version"

RUNTIME_SETTING_KEYS = (WORKER_COUNT, MAX_RETRIES, TIMEOUT_MINUTES, PREFERRED_MAYA_VERSION)
LIVE_EDITABLE_KEYS = (WORKER_COUNT, MAX_RETRIES, TIMEOUT_MINUTES)

SETTING_LABELS = {
    WORKER_COUNT: "Max workers",
    MAX_RETRIES: "Retries",
    TIMEOUT_MINUTES: "Timeout (min)",
    PREFERRED_MAYA_VERSION: "Preferred Maya",
}

MAX_WORKER_COUNT = 256
MAX_RETRY_COUNT = 64
MAX_TIMEOUT_MINUTES = 100000


def get_override_flag_key(setting_key):
    """Gets the task setting key that enables an override.

    Args:
        setting_key (str): Runtime setting key, such as "worker_count".

    Returns:
        str: Override flag key, such as "override_worker_count".
    """
    return f"override_{setting_key}"


def _clamp_integer(value, minimum, maximum, fallback):
    """Converts a value to a clamped integer.

    Args:
        value (object): Raw value.
        minimum (int): Lowest allowed value.
        maximum (int): Highest allowed value.
        fallback (int): Value used when conversion fails.

    Returns:
        int: Clamped integer.
    """
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = fallback
    return max(minimum, min(maximum, number))


def normalize_setting_value(setting_key, value):
    """Normalizes one runtime setting value.

    Args:
        setting_key (str): Runtime setting key.
        value (object): Raw value.

    Returns:
        object: Normalized value (int for numeric keys, str for the Maya version).
    """
    if setting_key == WORKER_COUNT:
        return _clamp_integer(value, 1, MAX_WORKER_COUNT, 1)
    if setting_key == MAX_RETRIES:
        return _clamp_integer(value, 0, MAX_RETRY_COUNT, 0)
    if setting_key == TIMEOUT_MINUTES:
        return _clamp_integer(value, 0, MAX_TIMEOUT_MINUTES, 0)
    if setting_key == PREFERRED_MAYA_VERSION:
        return str(value or "").strip()
    return value


def build_overrides_from_task_settings(settings):
    """Builds the enabled overrides stored in a "Settings Override" task.

    Args:
        settings (dict): Task settings containing "override_<key>" flags and values.

    Returns:
        dict: Normalized values for every enabled override, keyed by runtime setting key.
    """
    settings = settings or {}
    overrides = {}
    for setting_key in RUNTIME_SETTING_KEYS:
        if settings.get(get_override_flag_key(setting_key)):
            overrides[setting_key] = normalize_setting_value(setting_key, settings.get(setting_key))
    return overrides


def merge_overrides(*override_dicts):
    """Merges override dictionaries in order, later values winning.

    Args:
        *override_dicts (dict): Override dictionaries in application order.

    Returns:
        dict: Merged overrides.
    """
    merged = {}
    for overrides in override_dicts:
        merged.update(overrides or {})
    return merged


def is_settings_override_task(task):
    """Checks whether a task is a "Settings Override" control task.

    Args:
        task (BatchTask): Task to inspect.

    Returns:
        bool: True for Settings Override tasks.
    """
    return bool(getattr(task, "is_settings_override_task", False))


def get_task_overrides(task):
    """Gets the overrides contributed by an enabled Settings Override task.

    Args:
        task (BatchTask): Task to inspect.

    Returns:
        dict: Overrides, or an empty dictionary for other or disabled tasks.
    """
    if not is_settings_override_task(task) or not getattr(task, "enabled", True):
        return {}
    return build_overrides_from_task_settings(getattr(task, "settings", {}))


def collect_overrides(task_list):
    """Merges the overrides of every Settings Override task in a task list.

    Args:
        task_list (list): Tasks in project order.

    Returns:
        dict: Merged overrides, later tasks winning.
    """
    return merge_overrides(*[get_task_overrides(task) for task in task_list or []])


def build_run_settings_schedule(task_segments):
    """Assigns run settings overrides to the segment barriers where they apply.

    A Settings Override task takes effect at the next safe barrier at or after its
    position: tasks before the first processing task of a segment apply when
    that segment starts; tasks placed after a processing task (mid-segment or
    trailing) apply when the next processing segment starts, or before the
    run-once finalization phase when no processing segment follows. Segments
    without processing tasks are skipped (the tracker skips them too) and
    their overrides carry forward.

    Args:
        task_segments (list): Task lists, one per input segment, in project order.

    Returns:
        dict: "segments" holds one override dictionary per processing segment,
            and "final" holds overrides applied before finalization.
    """
    schedule = {"segments": [], "final": {}}
    carried = {}
    for segment_tasks in task_segments or []:
        leading = {}
        trailing = {}
        has_processing = False
        for task in segment_tasks:
            if is_settings_override_task(task):
                target = trailing if has_processing else leading
                target.update(get_task_overrides(task))
            elif not getattr(task, "is_input_task", False):
                has_processing = True
        if not has_processing:
            carried = merge_overrides(carried, leading)
            continue
        schedule["segments"].append(merge_overrides(carried, leading))
        carried = trailing
    schedule["final"] = carried
    return schedule


def find_mid_segment_tasks(task_segments):
    """Finds Settings Override tasks that sit after a processing task in their segment.

    These tasks cannot change settings in the middle of a segment, so they only
    take effect at the next segment barrier.

    Args:
        task_segments (list): Task lists, one per input segment, in project order.

    Returns:
        list: Settings Override tasks placed after a processing task.
    """
    found = []
    for segment_tasks in task_segments or []:
        has_processing = False
        for task in segment_tasks:
            if is_settings_override_task(task):
                if has_processing and getattr(task, "enabled", True):
                    found.append(task)
            elif not getattr(task, "is_input_task", False):
                has_processing = True
    return found


def format_setting_value(setting_key, value):
    """Formats a runtime setting value for logs.

    Args:
        setting_key (str): Runtime setting key.
        value (object): Setting value.

    Returns:
        str: Readable value.
    """
    if setting_key == PREFERRED_MAYA_VERSION:
        return str(value) if value else "(current)"
    if setting_key in (MAX_RETRIES, TIMEOUT_MINUTES) and not value:
        return "0 (off)"
    return str(value)


def describe_changes(changes):
    """Builds a readable summary of applied changes.

    Args:
        changes (list): (key, old_value, new_value) tuples.

    Returns:
        str: Comma-separated summary such as "Max workers 2 -> 6".
    """
    parts = []
    for setting_key, old_value, new_value in changes or []:
        label = SETTING_LABELS.get(setting_key, setting_key)
        parts.append(
            f"{label} {format_setting_value(setting_key, old_value)} -> "
            f"{format_setting_value(setting_key, new_value)}"
        )
    return ", ".join(parts)


class RunSettingsState:
    """Mutable runtime settings for one tracker run."""

    def __init__(
        self,
        worker_count=1,
        max_retries=0,
        timeout_minutes=0,
        preferred_maya_version="",
        mayapy_path="",
        keep_manual_changes=False,
    ):
        """Initializes the run settings state.

        Args:
            worker_count (int, optional): Maximum concurrent workers.
            max_retries (int, optional): Retry attempts per failed job.
            timeout_minutes (int, optional): Per-job timeout in minutes. 0 disables it.
            preferred_maya_version (str, optional): Maya version used for new workers.
            mayapy_path (str, optional): Resolved mayapy executable for new workers.
            keep_manual_changes (bool, optional): When True, settings changed manually
                in the tracker are not overwritten by later Settings Override tasks.
        """
        self.values = {
            WORKER_COUNT: normalize_setting_value(WORKER_COUNT, worker_count),
            MAX_RETRIES: normalize_setting_value(MAX_RETRIES, max_retries),
            TIMEOUT_MINUTES: normalize_setting_value(TIMEOUT_MINUTES, timeout_minutes),
            PREFERRED_MAYA_VERSION: normalize_setting_value(PREFERRED_MAYA_VERSION, preferred_maya_version),
        }
        self.mayapy_path = str(mayapy_path or "")
        self.keep_manual_changes = bool(keep_manual_changes)
        self.manual_keys = set()

    @property
    def worker_count(self):
        """Gets the maximum concurrent workers.

        Returns:
            int: Worker limit.
        """
        return self.values[WORKER_COUNT]

    @property
    def max_retries(self):
        """Gets the retry attempts per failed job.

        Returns:
            int: Retry limit.
        """
        return self.values[MAX_RETRIES]

    @property
    def timeout_minutes(self):
        """Gets the per-job timeout in minutes.

        Returns:
            int: Timeout minutes, 0 when disabled.
        """
        return self.values[TIMEOUT_MINUTES]

    @property
    def timeout_seconds(self):
        """Gets the per-job timeout in seconds.

        Returns:
            int: Timeout seconds, 0 when disabled.
        """
        return self.values[TIMEOUT_MINUTES] * 60

    @property
    def preferred_maya_version(self):
        """Gets the preferred Maya version for new workers.

        Returns:
            str: Maya version, or an empty string for the current mayapy.
        """
        return self.values[PREFERRED_MAYA_VERSION]

    def apply(self, overrides, manual=False):
        """Applies overrides and returns what changed.

        Manual changes are remembered per key. When keep_manual_changes is on,
        task-driven overrides skip keys that were changed manually.

        Args:
            overrides (dict): Values keyed by runtime setting key.
            manual (bool, optional): True when the change comes from the user.

        Returns:
            tuple: (changes, protected_keys) where changes is a list of
                (key, old_value, new_value) tuples and protected_keys lists keys
                skipped because they were changed manually.
        """
        changes = []
        protected_keys = []
        for setting_key in RUNTIME_SETTING_KEYS:
            if setting_key not in (overrides or {}):
                continue
            new_value = normalize_setting_value(setting_key, overrides[setting_key])
            if not manual and self.keep_manual_changes and setting_key in self.manual_keys:
                if new_value != self.values[setting_key]:
                    protected_keys.append(setting_key)
                continue
            if manual:
                self.manual_keys.add(setting_key)
            old_value = self.values[setting_key]
            if new_value == old_value:
                continue
            self.values[setting_key] = new_value
            changes.append((setting_key, old_value, new_value))
        return changes, protected_keys

    def to_dict(self):
        """Serializes the state.

        Returns:
            dict: JSON-compatible settings, mayapy path, and manual flags.
        """
        data = dict(self.values)
        data["mayapy_path"] = self.mayapy_path
        data["keep_manual_changes"] = self.keep_manual_changes
        data["manual_keys"] = sorted(self.manual_keys)
        return data
