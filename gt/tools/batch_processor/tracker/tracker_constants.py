"""Constants used by the standalone Batch Processor tracker."""


PREFS_FILENAME = "batch_processor_tracker"
PREFS_KEY_FLAG_SKIPS_AS_WARNINGS = "flag_skips_as_warnings"
PREFS_KEY_HIDE_COMPLETED_BY_DEFAULT = "hide_completed_by_default"
PREFS_KEY_PLAY_SOUND_ON_COMPLETION = "play_sound_on_completion"
PREFS_KEY_AUTO_CLOSE_ON_SUCCESS = "auto_close_on_success"
PREFS_KEY_SHOW_PROJECT_ROW = "show_project_row"
PREFS_KEY_START_COMPACT = "start_compact"
PREFS_KEY_START_MINIMIZED = "start_minimized"
PREFS_KEY_USE_SYSTEM_TRAY = "use_system_tray"
PREFS_KEY_KEEP_MANUAL_RUN_SETTINGS = "keep_manual_run_settings"
AUTO_CLOSE_SECONDS = 10
SOUND_TAIL_MS = 1500


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
    BLOCKED = "Blocked"


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
    Status.BLOCKED: "#a16e48",
}

TRAY_BADGE_DEFAULT_COLOR = "#4a90d9"
TRAY_TILE_COLOR = "#1b1e22"
TRAY_TRACK_COLOR = "#454a50"
TRAY_TEXT_COLOR = "#ffffff"
TRAY_BADGE_COLORS = {
    HealthState.COMPLETED: "#5fcf86",
    HealthState.WARNING: "#e6b93a",
    HealthState.ERROR: "#e8645e",
    HealthState.ABORTED: "#e8645e",
}

TERMINAL_STATUSES = {
    Status.COMPLETED,
    Status.COMPLETED_WARNINGS,
    Status.FAILED,
    Status.TIMED_OUT,
    Status.CANCELED,
    Status.SKIPPED,
    Status.BLOCKED,
}

EVENT_SCHEMA_VERSION = 1
