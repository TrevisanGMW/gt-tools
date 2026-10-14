"""Read-only browser for resolved Batch Processor environment variables."""

from gt.ui.environment_variables_dialog import (
    EnvironmentVariablesDialog as _EnvironmentVariablesDialog,
)



BUILT_IN_ENVIRONMENT_VARIABLE_DESCRIPTIONS = {
    "input-file": "Name of the current input file, without its extension.",
    "input-string": "Text from the current Input Strings row.",
    "input-string-index": "One-based index of the current Input Strings row.",
    "project-name": "Display name of this Batch Processor project.",
    "project-sanitized-name": "Project name cleaned for use in file and folder names.",
    "project-notes": "Notes saved with this project.",
    "project-dir": "Resolved root folder used by this project.",
    "project-file-dir": "Folder containing the saved .batch project file.",
    "project-path": "Full path to the saved .batch project file.",
    "project-parent-dir": "Parent folder of the project root folder.",
    "project-grandparent-dir": "Folder one level above the project parent folder.",
    "input-dir": "Configured input folder, resolved relative to the project root.",
    "task-dir": "Configured task working folder, resolved relative to the project root.",
    "output-dir": "Configured output folder, resolved relative to the project root.",
    "temp-dir": "Operating system temporary folder.",
    "home-dir": "Current user's home folder.",
    "desktop-dir": "Current user's Desktop folder.",
    "year": "Current year using four digits.",
    "month": "Current month using two digits.",
    "day": "Current day of the month using two digits.",
    "time": "Current time in hours, minutes, and seconds.",
    "hostname": "Name of the computer running the task.",
    "worker-count": "Configured number of concurrent batch workers.",
    "multi-instance": "Whether tasks may run in multiple application instances.",
    "log-dir": "Folder where this project's batch logs are written.",
    "task-name": "Display name of the current task.",
    "task-sanitized-name": "Current task name cleaned for file and folder names.",
    "task-type": "Internal type key for the current task.",
    "task-id": "Stable ID of the current task in this project.",
    "previous-task-name": "Display name of the previous enabled task.",
    "previous-task-sanitized-name": "Previous task name cleaned for file and folder names.",
    "previous-task-path": "Resolved output path of the previous task.",
    "previous-previous-task-name": (
        "Display name of the task two positions before the current task."
    ),
    "previous-previous-task-sanitized-name": (
        "Name of the task two positions before the current task, cleaned for file and folder names."
    ),
    "previous-previous-task-path": "Resolved output path from two tasks before the current task.",
    "pre-previous-task-name": (
        "Alias for the name of the task two positions before the current task."
    ),
    "pre-previous-task-sanitized-name": (
        "Alias for the sanitized name of the task two positions before the current task."
    ),
    "pre-previous-task-path": "Alias for the output path from two tasks before the current task.",
    "next-task-name": "Display name of the next indexed task.",
    "next-task-sanitized-name": "Next task name cleaned for file and folder names.",
    "next-task-path": "Resolved output path of the next task.",
    "future-task-path": "Alias for the resolved output path of the next task.",
    "batch-status-known": "Whether the current batch run has a known result state.",
    "batch-run-scope": "Scope of the available run state: project or individual worker.",
    "batch-run-id": "Unique identifier shared by processes in the current batch run.",
    "batch-tasks-failed": "Whether any task in the current batch run failed.",
    "batch-tasks-incomplete": (
        "Whether any task in the current batch run did not complete successfully."
    ),
    "batch-validation-failed": "Whether a validation task failed during the current batch run.",
    "batch-validation-passed": (
        "Whether validation completed and passed during the current batch run."
    ),
    "batch-previous-tasks-succeeded": (
        "Whether all enabled processing tasks before the current task succeeded."
    ),
    "batch-is-final-task": "Whether the current task is the final enabled task.",
    "batch-previous-task-skipped": "Whether the previous enabled task was skipped.",
    "batch-task-run-once": "Whether this is an aggregate task that runs once for the batch.",
}

_TASK_INDEX_DESCRIPTIONS = {
    "task": "current task",
    "previous-task": "previous task",
    "previous-previous-task": "task two positions before the current task",
    "pre-previous-task": "task two positions before the current task (alias)",
    "next-task": "next task",
}

for _segment_prefix, _scope_description in (
    ("", "in the project"),
    ("seg-", "within the current segment"),
):
    for _task_prefix, _task_description in _TASK_INDEX_DESCRIPTIONS.items():
        for _index_suffix in ("idx-padded", "index"):
            _token_name = f"{_segment_prefix}{_task_prefix}-{_index_suffix}"
            _padded_description = " with leading zeros" if _index_suffix == "idx-padded" else ""
            BUILT_IN_ENVIRONMENT_VARIABLE_DESCRIPTIONS[_token_name] = (
                f"One-based index of the {_task_description} {_scope_description}"
                f"{_padded_description}; 0 if unavailable."
            )

for _legacy_index_name, _canonical_index_name in {
    "previous-task-idx": "previous-task-idx-padded",
    "previous-previous-task-idx": "previous-previous-task-idx-padded",
    "pre-previous-task-idx": "pre-previous-task-idx-padded",
    "next-task-idx": "next-task-idx-padded",
}.items():
    BUILT_IN_ENVIRONMENT_VARIABLE_DESCRIPTIONS[_legacy_index_name] = (
        BUILT_IN_ENVIRONMENT_VARIABLE_DESCRIPTIONS[_canonical_index_name]
        + " Legacy alias."
    )


class EnvironmentVariablesDialog(_EnvironmentVariablesDialog):
    """Batch Processor configuration for the shared environment browser."""

    def __init__(self, refresh_callback, parent=None):
        """Initializes the Batch Processor environment-variable browser.

        Args:
            refresh_callback (callable): Function returning the latest variables.
            parent (QWidget, optional): Parent widget.
        """
        super().__init__(
            refresh_callback=refresh_callback,
            parent=parent,
            title="Batch Project Environment Variables",
            descriptions=BUILT_IN_ENVIRONMENT_VARIABLE_DESCRIPTIONS,
        )
