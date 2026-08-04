"""
Batch Processor Tracker
"""

from gt.tools.batch_processor import batch_processor_constants as constants
import datetime


class BatchProgressTracker:
    """Tracks progress for a batch processor run."""

    def __init__(self, message_callback=None):
        """Initializes progress tracker.

        Args:
            message_callback (callable, optional): Callback for progress messages.
        """
        """Initializes a progress tracker."""
        self.message_callback = message_callback
        self.reset()

    def reset(self):
        """Resets this tracker to its idle state."""
        self.project_name = ""
        self.current_step_name = ""
        self.current_step_index = 0
        self.total_steps = 0
        self.current_file = ""
        self.total_files = 0
        self.processed_files = 0
        self.remaining_files = 0
        self.succeeded = 0
        self.failed = 0
        self.skipped = 0
        self.warnings = 0
        self.active_workers = 0
        self.run_mode = "single-instance"
        self.status = constants.RunStatus.PENDING
        self.started_at = None
        self.ended_at = None
        self.messages = []

    def start_run(self, project_name, total_steps, total_files, active_workers=1, run_mode="single-instance"):
        """Marks the start of a run.

        Args:
            project_name (str): Active project name.
            total_steps (int): Total enabled processing steps.
            total_files (int): Total work items.
            active_workers (int, optional): Active worker count.
            run_mode (str, optional): Run mode label.
        """
        self.reset()
        self.project_name = project_name
        self.total_steps = int(total_steps)
        self.total_files = int(total_files)
        self.remaining_files = int(total_files)
        self.active_workers = int(active_workers)
        self.run_mode = run_mode
        self.status = constants.RunStatus.RUNNING
        self.started_at = datetime.datetime.utcnow().isoformat()

    def start_step(self, step_index, step_name):
        """Updates tracker state for a processing step.

        Args:
            step_index (int): One-based process step index.
            step_name (str): Process step name.
        """
        self.current_step_index = int(step_index)
        self.current_step_name = str(step_name)

    def start_file(self, file_path):
        """Updates tracker state for the current file.

        Args:
            file_path (str): File currently being processed.
        """
        self.current_file = str(file_path)

    def record_success(self):
        """Records a successfully processed file."""
        self.succeeded += 1
        self._record_processed()

    def record_failure(self):
        """Records a failed file."""
        self.failed += 1
        self._record_processed()

    def record_skipped(self):
        """Records a skipped file."""
        self.skipped += 1
        self._record_processed()

    def record_warning(self):
        """Records a warning."""
        self.warnings += 1

    def record_message(self, message):
        """Records a progress message.

        Args:
            message (str): Message to record.
        """
        self.messages.append(str(message))
        if callable(self.message_callback):
            self.message_callback(str(message))

    def finish(self, failed=False):
        """Marks this run as finished.

        Args:
            failed (bool, optional): Whether the run finished with a failure state.
        """
        self.status = constants.RunStatus.FAILED if failed else constants.RunStatus.SUCCEEDED
        self.active_workers = 0
        self.ended_at = datetime.datetime.utcnow().isoformat()

    def to_dict(self):
        """Serializes tracker state.

        Returns:
            dict: Serializable tracker state.
        """
        return {
            "project_name": self.project_name,
            "current_step_name": self.current_step_name,
            "current_step_index": self.current_step_index,
            "total_steps": self.total_steps,
            "current_file": self.current_file,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "remaining_files": self.remaining_files,
            "succeeded": self.succeeded,
            "failed": self.failed,
            "skipped": self.skipped,
            "warnings": self.warnings,
            "active_workers": self.active_workers,
            "run_mode": self.run_mode,
            "status": self.status,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "messages": list(self.messages),
        }

    def _record_processed(self):
        """Records one processed file in aggregate counters."""
        self.processed_files += 1
        self.remaining_files = max(0, self.total_files - self.processed_files)
