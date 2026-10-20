"""Scheduler eligibility rules for child project jobs; never sleeps in a worker."""

import datetime

from gt.tools.batch_processor import batch_processor_projects as projects
from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_events


class ProjectQueue:
    """Evaluates ordered dependencies, group barriers, and launch windows."""

    def __init__(self, scheduler):
        """Stores the scheduler without owning any Maya state.

        Args:
            scheduler (TrackerScheduler): Owning scheduler.
        """
        self.scheduler = scheduler

    def get_settings(self, job):
        """Gets launch settings for an orchestration job.

        Args:
            job (TrackerJob): Queue job.

        Returns:
            dict or None: Child task settings when present.
        """
        project = self.scheduler.project
        if not project or job.is_finalization or not hasattr(project, "get_task"):
            return None
        for definition in job.tasks:
            task = project.get_task(definition.id)
            if task and task.task_type == "run_batch_project":
                return task.settings
        return None

    def retry_limit(self, job):
        """Gets the retry budget from the current project's run settings.

        Args:
            job (TrackerJob): Queue job.

        Returns:
            int: Retry budget, preserving ordinary project retry behavior.
        """
        return self.scheduler.max_retries

    def has_pending_retry(self, job):
        """Checks whether a failed dependency still has retry work remaining.

        Args:
            job (TrackerJob): Dependency job.

        Returns:
            bool: Whether its outcome is still provisional.
        """
        scheduler = self.scheduler
        return job.status == tracker_constants.Status.FAILED and (
            scheduler.job_retry_counts.get(job.id, 0) < self.retry_limit(job))

    def advance_retries(self):
        """Retries child launches even while their dependents remain queued.

        Returns:
            bool: Whether a child job was requeued.
        """
        changed = False
        scheduler = self.scheduler
        for job in scheduler.session.regular_jobs:
            if self.get_settings(job) is None or not self.has_pending_retry(job):
                continue
            if job.id in scheduler.running or job in scheduler.regular_queue:
                continue
            if scheduler.segmented and job.segment_index != scheduler.current_segment_index:
                continue
            count = scheduler.job_retry_counts.get(job.id, 0) + 1
            scheduler.job_retry_counts[job.id] = count
            scheduler.timed_out_jobs.discard(job.id)
            job.reset_for_restart()
            scheduler.regular_queue.append(job)
            scheduler._append_project_log(f"[OPERATION] - Child project retry {count}: {job.name}\n")
            changed = True
        return changed

    def dependencies(self, job, settings):
        """Resolves stable predecessors from input order rather than finish order.

        Args:
            job (TrackerJob): Waiting child job.
            settings (dict): Launch settings.

        Returns:
            list: Dependency jobs.
        """
        jobs = self.scheduler.session.regular_jobs
        if settings["queue_mode"] == "Ordered Chain":
            peers = [candidate for candidate in jobs if candidate.segment_index == job.segment_index]
            index = peers.index(job)
            return peers[index - 1:index] if index else []
        if settings["queue_mode"] == "Groups" and job.segment_index:
            return [candidate for candidate in jobs if candidate.segment_index == job.segment_index - 1]
        return []

    def eligible(self, job):
        """Checks all start conditions and marks impossible dependencies blocked.

        Args:
            job (TrackerJob): Queued child or ordinary job.

        Returns:
            bool: Whether a worker slot may be assigned now.
        """
        settings = self.get_settings(job)
        if settings is None:
            return True
        status = tracker_constants.Status
        now = datetime.datetime.now(datetime.timezone.utc)
        reference_start = tracker_events.parse_timestamp(self.scheduler.session.started_at)
        deadline = projects.parse_start_time(settings.get("launch_deadline"), reference_start)
        if deadline and now > deadline:
            self.block(job, "Launch deadline expired.")
            return False
        predecessors = self.dependencies(job, settings)
        if any(candidate.status not in tracker_constants.TERMINAL_STATUSES or
               candidate.id in self.scheduler.running or self.has_pending_retry(candidate)
               for candidate in predecessors):
            return False
        if predecessors:
            success = all(candidate.status in (status.COMPLETED, status.COMPLETED_WARNINGS)
                          for candidate in predecessors)
            failed = any(candidate.status in (status.FAILED, status.TIMED_OUT) for candidate in predecessors)
            condition = settings["dependency_outcome"]
            if (condition == "Success" and not success) or (condition == "Failure" and not failed):
                self.block(job, f"Dependency condition '{condition}' was not satisfied.")
                return False
        if settings["failure_policy"] == "Stop Launching":
            failures = [candidate for candidate in self.scheduler.session.regular_jobs
                        if candidate is not job and candidate.status in (status.FAILED, status.TIMED_OUT)
                        and candidate.id not in self.scheduler.running and not self.has_pending_retry(candidate)]
            if failures:
                self.block(job, f"Queue stopped after permanent failure: {failures[0].name}")
                return False
        start = projects.parse_start_time(settings.get("not_before"), reference_start)
        reference_times = [tracker_events.parse_timestamp(candidate.completed_at) for candidate in predecessors]
        reference_times = [value for value in reference_times if value]
        reference = max(reference_times) if reference_times else tracker_events.parse_timestamp(
            self.scheduler.session.started_at)
        delay_end = reference + datetime.timedelta(seconds=int(settings.get("delay_seconds", 0)))
        return now >= max(value for value in (start, delay_end) if value is not None)

    def block(self, job, reason):
        """Finalizes a job that cannot satisfy its launch conditions.

        Args:
            job (TrackerJob): Unlaunched job.
            reason (str): User-visible explanation.
        """
        job.status = tracker_constants.Status.BLOCKED
        job.completed_at = tracker_events.utc_now_iso()
        for task in job.tasks:
            task.status = tracker_constants.Status.BLOCKED
            task.progress = 100
            task.completed_at = job.completed_at
            task.messages.append(("Warning", reason))
        self.scheduler._append_project_log(f"[BLOCKED] - {job.name}: {reason}\n")
