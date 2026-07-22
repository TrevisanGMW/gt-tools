"""Pure state model for the standalone Batch Processor tracker."""

import os

from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_events


class TrackerTask:
    """Tracks one executable task within a job."""

    def __init__(self, task_id, number, name, icon=""):
        """Initializes task state.

        Args:
            task_id (str): Stable project task identifier.
            number (int): One-based task number.
            name (str): User-facing task name.
            icon (str, optional): Resource-library icon attribute name.
        """
        self.id = task_id
        self.number = int(number)
        self.name = name
        self.icon = icon
        self.status = tracker_constants.Status.QUEUED
        self.progress = 0
        self.completed_items = 0
        self.total_items = 0
        self.errors = 0
        self.warnings = 0
        self.reported_warnings = 0
        self.skipped_items = 0
        self.completion_result = ""
        self.skip_status_message = ""
        self.started_at = ""
        self.completed_at = ""
        self.worker = ""
        self.log_paths = []
        self.messages = []
        self.parent_job = None

    def apply_event(self, event):
        """Applies a worker event to this task.

        Args:
            event (dict): Structured worker event.
        """
        event_name = event.get("event")
        if event_name == "task_started":
            self.status = tracker_constants.Status.RUNNING
            self.started_at = event.get("timestamp") or self.started_at
            self.total_items = max(0, int(event.get("total_items") or 0))
            self.worker = str(event.get("worker_id") or self.worker)
        elif event_name == "task_progress":
            self.completed_items = max(self.completed_items, int(event.get("completed_items") or 0))
            self.total_items = max(self.total_items, int(event.get("total_items") or 0))
            if self.total_items:
                self.progress = min(99, int(100 * self.completed_items / self.total_items))
        elif event_name == "warning":
            self.reported_warnings += 1
            self._refresh_warning_count()
            self.messages.append(("Warning", str(event.get("message") or "Warning reported.")))
        elif event_name == "skip_notice":
            self.messages.append(("Info", str(event.get("message") or "Skipped work reported.")))
        elif event_name == "error":
            self.errors += 1
            self.messages.append(("Error", str(event.get("message") or "Error reported.")))
        elif event_name == "log_artifact":
            log_path = event.get("path")
            if log_path and log_path not in self.log_paths:
                self.log_paths.append(log_path)
        elif event_name == "task_finished":
            self.completed_items = max(self.completed_items, int(event.get("completed_items") or 0))
            self.total_items = max(self.total_items, int(event.get("total_items") or 0))
            self.errors = max(self.errors, int(event.get("errors") or 0))
            self.reported_warnings = max(self.reported_warnings, int(event.get("warnings") or 0))
            result = event.get("status")
            skipped_items = int(event.get("skipped_items") or 0)
            if result == "skipped" and not skipped_items:
                skipped_items = max(1, self.total_items)
            self.skipped_items = max(self.skipped_items, skipped_items)
            if result == "warning" and not self.skipped_items:
                self.reported_warnings = max(1, self.reported_warnings)
            self.completion_result = result or ""
            self._refresh_completed_status()
            self.progress = 100
            self.completed_at = event.get("timestamp") or self.completed_at

    def _refresh_warning_count(self):
        """Recalculates visible warnings reported by the worker."""
        self.warnings = self.reported_warnings

    def _refresh_completed_status(self):
        """Recalculates terminal status and skip-related information."""
        if self.skip_status_message:
            self.messages = [message for message in self.messages if message[1] != self.skip_status_message]
            self.skip_status_message = ""
        self._refresh_warning_count()
        if self.completion_result == "failed" or self.errors:
            self.status = tracker_constants.Status.FAILED
        elif self.skipped_items:
            self.status = tracker_constants.Status.SKIPPED
        elif self.warnings:
            self.status = tracker_constants.Status.COMPLETED_WARNINGS
        else:
            self.status = tracker_constants.Status.COMPLETED
        if self.skipped_items:
            item_label = "item" if self.skipped_items == 1 else "items"
            self.skip_status_message = f"Skipped {self.skipped_items} {item_label}."
            self.messages.append(("Info", self.skip_status_message))

    def get_count_text(self):
        """Gets formatted work-item counts.

        Returns:
            str: Completed and total item counts.
        """
        if not self.total_items:
            return "-"
        return f"{self.completed_items}/{self.total_items}"

    def reset_for_restart(self):
        """Resets runtime state so the task can be executed again."""
        self.status = tracker_constants.Status.QUEUED
        self.progress = 0
        self.completed_items = 0
        self.total_items = 0
        self.errors = 0
        self.warnings = 0
        self.reported_warnings = 0
        self.skipped_items = 0
        self.completion_result = ""
        self.skip_status_message = ""
        self.started_at = ""
        self.completed_at = ""
        self.worker = ""
        self.log_paths = []
        self.messages = []


class TrackerJob:
    """Tracks one source-file job."""

    def __init__(self, job_id, number, source_file, task_definitions, is_finalization=False, segment_index=0):
        """Initializes job state.

        Args:
            job_id (str): Stable job identifier.
            number (int): Original job number.
            source_file (str): Source file assigned to the job.
            task_definitions (list): Task definition dictionaries.
            is_finalization (bool, optional): Whether this is the final run-once phase.
            segment_index (int, optional): Zero-based input segment this job belongs to.
        """
        self.id = job_id
        self.number = int(number)
        self.source_file = source_file
        self.name = "Finalization" if is_finalization else os.path.basename(source_file)
        self.is_finalization = bool(is_finalization)
        self.segment_index = int(segment_index)
        self.status = (
            tracker_constants.Status.PENDING_FINALIZATION
            if self.is_finalization
            else tracker_constants.Status.QUEUED
        )
        self.started_at = ""
        self.completed_at = ""
        self.worker = ""
        self.log_path = ""
        self.timing_log_path = ""
        self.completion_result = ""
        self.flag_skips_as_warnings = True
        self._source_size = None
        self.tasks = []
        for definition in task_definitions:
            task = TrackerTask(
                task_id=definition.get("id"),
                number=definition.get("number"),
                name=definition.get("name"),
                icon=definition.get("icon") or "",
            )
            task.parent_job = self
            self.tasks.append(task)

    def get_task(self, task_id):
        """Gets a task by stable identifier.

        Args:
            task_id (str): Task identifier.

        Returns:
            TrackerTask or None: Matching task.
        """
        return next((task for task in self.tasks if task.id == task_id), None)

    def get_source_size(self):
        """Gets the source file size in bytes, cached after the first lookup.

        The size is read at most once per job and reused for every later
        estimate, so repeated calls never touch the filesystem again.

        Returns:
            int: Source file size in bytes, or 0 when it cannot be read.
        """
        if self._source_size is None:
            try:
                self._source_size = os.path.getsize(self.source_file)
            except (OSError, TypeError, ValueError):
                self._source_size = 0
        return self._source_size

    def get_elapsed_seconds(self):
        """Gets this job's elapsed run time.

        Returns:
            float: Elapsed seconds between the job start and completion, or
                the time since it started when it is still running.
        """
        return tracker_events.elapsed_seconds(self.started_at, self.completed_at)

    def apply_event(self, event, flag_skips_as_warnings=True):
        """Applies a structured event to this job.

        Args:
            event (dict): Worker event.
            flag_skips_as_warnings (bool, optional): Whether skipped work produces warnings.
        """
        event_name = event.get("event")
        if event_name == "worker_started":
            self.status = tracker_constants.Status.WAITING
            self.started_at = event.get("timestamp") or self.started_at
            self.worker = str(event.get("worker_id") or "")
        elif event_name == "job_started":
            self.status = tracker_constants.Status.RUNNING
            self.started_at = event.get("timestamp") or self.started_at
        task = self.get_task(event.get("task_id"))
        if task:
            task.apply_event(event)
            if event_name == "task_started":
                self.status = tracker_constants.Status.RUNNING
        if event_name == "job_finished":
            self.flag_skips_as_warnings = bool(flag_skips_as_warnings)
            self.completion_result = event.get("status") or "completed"
            self.completed_at = event.get("timestamp") or self.completed_at
            self.refresh_completed_status()

    def refresh_completed_status(self):
        """Recalculates a completed job from its current task results.
        """
        if not self.completion_result:
            return
        if self.completion_result == "failed" or self.errors:
            self.status = tracker_constants.Status.FAILED
        elif self.warnings or (
            self.flag_skips_as_warnings and any(task.skipped_items for task in self.tasks)
        ):
            self.status = tracker_constants.Status.COMPLETED_WARNINGS
        else:
            self.status = tracker_constants.Status.COMPLETED

    @property
    def progress(self):
        """Gets aggregate task progress.

        Returns:
            int: Job progress percentage.
        """
        if not self.tasks:
            return 100 if self.status in tracker_constants.TERMINAL_STATUSES else 0
        return int(sum(task.progress for task in self.tasks) / len(self.tasks))

    @property
    def errors(self):
        """Gets aggregate task error count.

        Returns:
            int: Total errors.
        """
        return sum(task.errors for task in self.tasks)

    @property
    def warnings(self):
        """Gets aggregate task warning count.

        Returns:
            int: Total warnings.
        """
        return sum(task.warnings for task in self.tasks)

    @property
    def has_skipped_work(self):
        """Checks whether any task skipped one or more work items.

        Returns:
            bool: True when skipped work was reported for this job.
        """
        return any(
            task.skipped_items or task.status == tracker_constants.Status.SKIPPED
            for task in self.tasks
        )

    def get_count_text(self):
        """Gets formatted completed-task counts.

        Returns:
            str: Completed and total task counts.
        """
        completed = len([task for task in self.tasks if task.status in tracker_constants.TERMINAL_STATUSES])
        return f"{completed}/{len(self.tasks)}"

    def reset_for_restart(self):
        """Resets runtime state so the regular job can be executed again."""
        self.status = tracker_constants.Status.QUEUED
        self.started_at = ""
        self.completed_at = ""
        self.worker = ""
        self.log_path = ""
        self.timing_log_path = ""
        self.completion_result = ""
        for task in self.tasks:
            task.reset_for_restart()


class TrackerSession:
    """Owns all state for one independent batch session."""

    def __init__(
        self,
        project_name,
        project_path,
        worker_count,
        jobs,
        session_dir,
        project_log_path="",
        source_project_file="",
    ):
        """Initializes session state.

        Args:
            project_name (str): Project display name.
            project_path (str): Project location.
            worker_count (int): Requested concurrent workers.
            jobs (list): Tracker jobs.
            session_dir (str): Run-scoped session directory.
            project_log_path (str, optional): Main Batch Processor project log.
            source_project_file (str, optional): Original saved Batch Processor project.
        """
        self.project_name = project_name
        self.project_path = project_path
        self.worker_count = max(1, int(worker_count or 1))
        self.jobs = jobs
        self.session_dir = session_dir
        self.project_log_path = project_log_path or ""
        self.source_project_file = source_project_file or ""
        self.started_at = tracker_events.utc_now_iso()
        self.completed_at = ""
        self.aborting = False
        self.finished = False
        self.flag_skips_as_warnings = True

    def get_job(self, job_id):
        """Gets a job by identifier.

        Args:
            job_id (str): Stable job identifier.

        Returns:
            TrackerJob or None: Matching job.
        """
        return next((job for job in self.jobs if job.id == job_id), None)

    @property
    def regular_jobs(self):
        """Gets non-finalization jobs.

        Returns:
            list: Regular jobs.
        """
        return [job for job in self.jobs if not job.is_finalization]

    @property
    def progress(self):
        """Gets overall progress across regular and finalization tasks.

        Returns:
            int: Overall percentage.
        """
        tasks = [task for job in self.jobs for task in job.tasks]
        return int(sum(task.progress for task in tasks) / len(tasks)) if tasks else 0

    def estimate_remaining_seconds(self):
        """Estimates wall-clock seconds left until every regular job finishes.

        Uses the completed regular jobs as a sample. When source file sizes are
        available it assumes run time scales with size (seconds per byte);
        otherwise it falls back to a simple per-job average. The projected work
        is divided by the effective worker count to approximate parallel
        wall-clock time, and time already spent on running jobs is credited.

        The per-call cost is a single pass over the regular jobs doing cached
        arithmetic, so it is safe to call on a display timer. Finalization jobs
        are excluded because their source file is not representative.

        Returns:
            float or None: Estimated seconds remaining, 0.0 when nothing is
                left, or None while no regular job has completed yet.
        """
        completed_seconds = 0.0
        completed_bytes = 0
        completed_count = 0
        remaining_bytes = 0
        remaining_count = 0
        running_seconds = 0.0
        for job in self.regular_jobs:
            if job.status in tracker_constants.TERMINAL_STATUSES:
                completed_seconds += job.get_elapsed_seconds()
                completed_bytes += job.get_source_size()
                completed_count += 1
            else:
                remaining_count += 1
                remaining_bytes += job.get_source_size()
                if job.status == tracker_constants.Status.RUNNING:
                    running_seconds += job.get_elapsed_seconds()
        if completed_count == 0:
            return None
        if remaining_count == 0:
            return 0.0
        if completed_bytes > 0 and remaining_bytes > 0:
            seconds_per_byte = completed_seconds / completed_bytes
            remaining_work_seconds = seconds_per_byte * remaining_bytes
        else:
            average_seconds = completed_seconds / completed_count
            remaining_work_seconds = average_seconds * remaining_count
        remaining_work_seconds = max(0.0, remaining_work_seconds - running_seconds)
        effective_workers = max(1, min(self.worker_count, remaining_count))
        return remaining_work_seconds / effective_workers

    @property
    def health_state(self):
        """Gets the most important overall tracker health state.

        Returns:
            str: Value from ``tracker_constants.HealthState``.
        """
        if self.aborting or any(job.status == tracker_constants.Status.CANCELED for job in self.jobs):
            return tracker_constants.HealthState.ABORTED
        if any(job.status == tracker_constants.Status.FAILED or job.errors for job in self.jobs):
            return tracker_constants.HealthState.ERROR
        if any(
            job.status == tracker_constants.Status.COMPLETED_WARNINGS or job.warnings
            for job in self.jobs
        ):
            return tracker_constants.HealthState.WARNING
        if self.finished:
            return tracker_constants.HealthState.COMPLETED
        active_statuses = {tracker_constants.Status.WAITING, tracker_constants.Status.RUNNING}
        if any(job.status in active_statuses for job in self.jobs):
            return tracker_constants.HealthState.RUNNING
        return tracker_constants.HealthState.STARTING

    def apply_event(self, event):
        """Applies an event to its job.

        Args:
            event (dict): Structured event.
        """
        job = self.get_job(event.get("job_id"))
        if job:
            job.apply_event(event, flag_skips_as_warnings=self.flag_skips_as_warnings)

    def set_flag_skips_as_warnings(self, enabled):
        """Updates skip-result presentation for current and future events.

        Args:
            enabled (bool): Whether skipped work should contribute warnings.
        """
        self.flag_skips_as_warnings = bool(enabled)
        for job in self.jobs:
            job.flag_skips_as_warnings = self.flag_skips_as_warnings
            job.refresh_completed_status()

    def get_job_names(self, result_category="all"):
        """Gets regular job file names matching a result category.

        Args:
            result_category (str, optional): One of all, failed, warning,
                completed, or skipped.

        Returns:
            list: Matching job names in original session order.
        """
        category = str(result_category or "all").strip().lower()
        jobs = self.regular_jobs
        if category == "failed":
            jobs = [
                job
                for job in jobs
                if job.status == tracker_constants.Status.FAILED or job.errors
            ]
        elif category == "warning":
            jobs = [job for job in jobs if job.warnings]
        elif category == "completed":
            jobs = [
                job
                for job in jobs
                if job.status == tracker_constants.Status.COMPLETED
                and not job.warnings
                and not job.has_skipped_work
            ]
        elif category == "skipped":
            jobs = [job for job in jobs if job.has_skipped_work]
        elif category != "all":
            return []
        return [job.name for job in jobs]

    def finish(self):
        """Marks the session finished."""
        self.finished = True
        self.completed_at = tracker_events.utc_now_iso()
