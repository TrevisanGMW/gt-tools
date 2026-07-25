"""Constants used by the standalone Batch Processor tracker."""


PREFS_FILENAME = "batch_processor_tracker"
PREFS_KEY_FLAG_SKIPS_AS_WARNINGS = "flag_skips_as_warnings"


class HealthState:
    """Overall tracker health states used by the status indicator."""

    STARTING = "starting"
    RUNNING = "running"
    COMPLETED = "completed"
    WARNING = "warning"
    ERROR = "error"
    ABORTED = "aborted"


class Status:
    """User-facing tracker status values."""

    QUEUED = "Queued"
    WAITING = "Waiting to Start"
    RUNNING = "Running"
    COMPLETED = "Completed"
    COMPLETED_WARNINGS = "Completed (Warnings)"
    FAILED = "Failed"
    TIMED_OUT = "Timed Out"
    PENDING_FINALIZATION = "Pending Finalization"
    CANCELING = "Canceling"
    CANCELED = "Canceled"
    SKIPPED = "Skipped"


STATUS_COLORS = {
    Status.QUEUED: "#72777d",
    Status.WAITING: "#4f81a8",
    Status.RUNNING: "#3f8f5f",
    Status.COMPLETED: "#3978b8",
    Status.COMPLETED_WARNINGS: "#c18a2b",
    Status.FAILED: "#b94b4b",
    Status.TIMED_OUT: "#c07a3a",
    Status.PENDING_FINALIZATION: "#9a6bb5",
    Status.CANCELING: "#b06f3c",
    Status.CANCELED: "#696d72",
    Status.SKIPPED: "#75659b",
}

TERMINAL_STATUSES = {
    Status.COMPLETED,
    Status.COMPLETED_WARNINGS,
    Status.FAILED,
    Status.TIMED_OUT,
    Status.CANCELED,
    Status.SKIPPED,
}

EVENT_SCHEMA_VERSION = 1
