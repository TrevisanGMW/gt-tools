"""Worker scheduling service for the standalone Batch Processor tracker."""

import json
import os
import re
import subprocess
import sys
import time

from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_events
from gt.tools.batch_processor.tracker import tracker_model
from gt.tools.batch_processor.tracker import tracker_process_utils


class TrackerScheduler:
    """Owns the job queue and all worker subprocesses."""

    def __init__(self, session, options, update_callback=None, finish_callback=None, project=None, segments=None):
        """Initializes the scheduler.

        Args:
            session (TrackerSession): Mutable tracker state.
            options (argparse.Namespace): Tracker launch options.
            update_callback (callable, optional): Called after state changes.
            finish_callback (callable, optional): Called when all work finishes.
            project (BatchProcessorModel, optional): Project model used to discover
                each segment's source files at phase start. Required for segmented runs.
            segments (list, optional): Ordered segment descriptors. When provided
                (more than one), the run executes one segment at a time with a
                barrier between segments.
        """
        self.session = session
        self.options = options
        self.update_callback = update_callback
        self.finish_callback = finish_callback
        self.project = project
        self.segments = list(segments or [])
        self.segmented = len(self.segments) > 1
        self.current_segment_index = 0
        self._materialized_segments = set()
        self.max_retries = max(0, int(getattr(options, "max_retries", 0) or 0))
        self.timeout_seconds = max(0, int(getattr(options, "timeout_minutes", 0) or 0)) * 60
        self.job_retry_counts = {}
        self.timed_out_jobs = set()
        self.pending_restarts = set()
        self._job_counter = 0
        self.running = {}
        self.readers = {}
        self.worker_log_offsets = {}
        self.regular_queue = list(session.regular_jobs)
        self.finalization_job = next(
            (job for job in session.jobs if job.is_finalization and not getattr(job, "is_preflight", False)),
            None,
        )
        self.final_task_index = 0
        self.abort_requested_at = None
        self._finish_notified = False
        self._preserve_terminal_finalization = False
        self._report_parts_cleaned = False
        os.makedirs(self.session.session_dir, exist_ok=True)
        os.makedirs(self.get_events_dir(), exist_ok=True)
        os.makedirs(self.get_logs_dir(), exist_ok=True)
        self.write_state()

    def get_events_dir(self):
        """Gets the session event directory.

        Returns:
            str: Event directory.
        """
        return os.path.join(self.session.session_dir, "events")

    def get_logs_dir(self):
        """Gets the session log directory.

        Returns:
            str: Log directory.
        """
        return os.path.join(self.session.session_dir, "logs")

    def tick(self):
        """Advances worker polling, event consumption, and queue scheduling."""
        changed = self._consume_events()
        changed = self._consume_worker_logs() or changed
        changed = self._collect_finished_processes() or changed
        if self.session.aborting:
            changed = self._advance_abort() or changed
        else:
            changed = self._advance_job_cancellations() or changed
            changed = self._advance_timeouts() or changed
            changed = self._advance_pending_restarts() or changed
            changed = self._advance_retries() or changed
            changed = self._finalize_timed_out_jobs() or changed
            if self.segmented:
                changed = self._advance_segments() or changed
            changed = self._launch_available_jobs() or changed
            changed = self._advance_finalization() or changed
        if self._is_finished() and not self.session.finished:
            self.cleanup_report_parts()
            self.session.finish()
            self._append_project_summary()
            changed = True
        if changed:
            self.write_state()
            if callable(self.update_callback):
                self.update_callback()
        if self.session.finished and not self._finish_notified:
            self._finish_notified = True
            if callable(self.finish_callback):
                self.finish_callback()

    def abort(self):
        """Stops scheduling and begins terminating all worker process trees."""
        if self.session.finished or self.session.aborting:
            return
        self.session.aborting = True
        self.abort_requested_at = time.monotonic()
        for job in self.regular_queue:
            self._mark_job_canceled(job)
        self.regular_queue = []
        if self.finalization_job and self.finalization_job.id not in self.running:
            self._mark_job_canceled(self.finalization_job)
        for process_data in self.running.values():
            process_data["job"].status = tracker_constants.Status.CANCELING
            tracker_process_utils.terminate_process_tree(process_data["process"], force=False)
        self.write_state()
        if callable(self.update_callback):
            self.update_callback()

    def can_cancel_job(self, job):
        """Checks whether a queued or running regular job can be canceled.

        Args:
            job (TrackerJob): Job requested for cancellation.

        Returns:
            bool: True when the job can be canceled independently.
        """
        if not job or job.is_finalization or self.session.aborting:
            return False
        if job in self.regular_queue:
            return job.status == tracker_constants.Status.QUEUED
        return job.id in self.running and job.status in {
            tracker_constants.Status.WAITING,
            tracker_constants.Status.RUNNING,
        }

    def cancel_job(self, job):
        """Cancels one queued job or requests termination of its worker.

        Args:
            job (TrackerJob): Queued or running regular job to cancel.

        Returns:
            bool: True when cancellation was applied or requested.
        """
        if not self.can_cancel_job(job):
            return False
        if job in self.regular_queue:
            self.regular_queue.remove(job)
            self._mark_job_canceled(job)
            self._append_project_log(
                f"[OPERATION] - (Multi-instance) - Canceled queued job '{job.name}'.\n"
            )
        else:
            process_data = self.running[job.id]
            process_data["cancel_requested_at"] = time.monotonic()
            process_data["cancel_force_requested"] = False
            job.status = tracker_constants.Status.CANCELING
            tracker_process_utils.terminate_process_tree(process_data["process"], force=False)
            self._append_project_log(
                f"[OPERATION] - (Multi-instance) - Cancellation requested for '{job.name}'.\n"
            )
        self.write_state()
        if callable(self.update_callback):
            self.update_callback()
        return True

    def can_restart_job(self, job):
        """Checks whether a regular terminal job can be queued again.

        Args:
            job (TrackerJob): Job requested for restart.

        Returns:
            bool: True when the job can safely be restarted.
        """
        if not job or job.is_finalization:
            return False
        if self.segmented and getattr(job, "segment_index", 0) != self.current_segment_index:
            return False
        if job.status not in tracker_constants.TERMINAL_STATUSES:
            return False
        if job.id in self.running or job in self.regular_queue:
            return False
        if self.session.aborting and not self.session.finished:
            return False
        if self.finalization_job and self.finalization_job.id in self.running:
            return False
        return job in self.session.regular_jobs

    def can_request_restart_job(self, job):
        """Checks whether a restart can be requested for a job.

        Unlike ``can_restart_job``, this also accepts active (queued or running)
        jobs, which are canceled first and restarted once they stop.

        Args:
            job (TrackerJob): Job requested for restart.

        Returns:
            bool: True when a restart can be requested.
        """
        return self.can_restart_job(job) or self.can_cancel_job(job)

    def request_restart_job(self, job):
        """Restarts a terminal job, or cancels an active job then restarts it.

        Terminal jobs are queued immediately. Active jobs are canceled and
        marked for a deferred restart, which runs automatically once the worker
        stops and the job reaches a terminal state.

        Args:
            job (TrackerJob): Regular job to run again.

        Returns:
            bool: True when the restart was queued or scheduled.
        """
        if self.can_restart_job(job):
            return self.restart_job(job)
        if not self.can_cancel_job(job):
            return False
        if not self.cancel_job(job):
            return False
        self.pending_restarts.add(job.id)
        self._append_project_log(
            f"[OPERATION] - (Multi-instance) - Restart requested for active job '{job.name}'; "
            "it will run again once it stops.\n"
        )
        return True

    def _advance_pending_restarts(self):
        """Restarts canceled jobs that were flagged for a deferred restart.

        Returns:
            bool: Whether any job was queued for a restart.
        """
        if not self.pending_restarts:
            return False
        changed = False
        for job_id in list(self.pending_restarts):
            job = self.session.get_job(job_id)
            if job is None:
                self.pending_restarts.discard(job_id)
                continue
            if job.id in self.running or job in self.regular_queue:
                continue
            if job.status not in tracker_constants.TERMINAL_STATUSES:
                continue
            self.pending_restarts.discard(job_id)
            if self.restart_job(job):
                changed = True
        return changed

    def restart_job(self, job):
        """Resets and queues one previously completed regular job.

        Args:
            job (TrackerJob): Terminal regular job to execute again.

        Returns:
            bool: True when the job was queued.
        """
        if not self.can_restart_job(job):
            return False
        self.timed_out_jobs.discard(job.id)
        job.reset_for_restart()
        self.regular_queue.append(job)
        self.session.finished = False
        self.session.completed_at = ""
        self.session.aborting = False
        self.abort_requested_at = None
        self._finish_notified = False
        self._preserve_terminal_finalization = bool(
            self.finalization_job
            and self.finalization_job.status in tracker_constants.TERMINAL_STATUSES
        )
        self._append_project_log(
            f"[OPERATION] - (Multi-instance) - Restart queued for '{job.name}'.\n"
        )
        self.write_state()
        if callable(self.update_callback):
            self.update_callback()
        return True

    def _advance_retries(self):
        """Re-queues failed regular jobs that still have retry attempts left.

        Retries are deferred until the active scope drains, so every job runs
        once before any failure is attempted again and all retries batch at the
        end of the run. Each eligible job is reset and queued exactly as a
        manual "Restart Job" would, but driven by the project's configured retry
        count instead of a user action. In segmented runs, only the current
        segment's failures are retried so a segment fully resolves before the
        run advances past its barrier.

        Returns:
            bool: Whether any job was queued for a retry.
        """
        if self.max_retries <= 0 or self.session.aborting:
            return False
        if self.regular_queue:
            return False
        if any(not process_data["job"].is_finalization for process_data in self.running.values()):
            return False
        if self.segmented:
            if self.current_segment_index not in self._materialized_segments:
                return False
            candidate_jobs = self._segment_jobs(self.current_segment_index)
        else:
            candidate_jobs = self.session.regular_jobs
        retry_jobs = [
            job
            for job in candidate_jobs
            if job.status == tracker_constants.Status.FAILED
            and self.job_retry_counts.get(job.id, 0) < self.max_retries
        ]
        if not retry_jobs:
            return False
        for job in retry_jobs:
            attempt = self.job_retry_counts.get(job.id, 0) + 1
            self.job_retry_counts[job.id] = attempt
            self.timed_out_jobs.discard(job.id)
            job.reset_for_restart()
            self.regular_queue.append(job)
            self._append_project_log(
                f"[OPERATION] - (Multi-instance) - Retry {attempt}/{self.max_retries} "
                f"queued for '{job.name}'.\n"
            )
        return True

    def _retries_remaining(self, job):
        """Checks whether a failed job still has configured retry attempts left.

        Args:
            job (TrackerJob): Job to evaluate.

        Returns:
            bool: True when at least one retry attempt remains.
        """
        return self.max_retries > 0 and self.job_retry_counts.get(job.id, 0) < self.max_retries

    def _advance_timeouts(self):
        """Force-cancels regular jobs that exceed the configured runtime timeout.

        A timed-out worker is force-terminated so a stuck job cannot run
        indefinitely. When retries remain the job is retried like any other
        failure; once retries are exhausted its terminal status is changed to
        ``Timed Out`` by ``_finalize_timed_out_jobs``. A timeout of 0 disables
        the check entirely.

        Returns:
            bool: Whether any job timed out this tick.
        """
        if self.timeout_seconds <= 0:
            return False
        changed = False
        current_time = time.monotonic()
        for job_id, process_data in self.running.items():
            job = process_data["job"]
            if job.is_finalization or process_data.get("timed_out"):
                continue
            if process_data.get("cancel_requested_at") is not None:
                continue
            started_monotonic = process_data.get("started_monotonic")
            if started_monotonic is None or current_time - started_monotonic < self.timeout_seconds:
                continue
            process_data["timed_out"] = True
            self.timed_out_jobs.add(job_id)
            job.status = tracker_constants.Status.CANCELING
            tracker_process_utils.terminate_process_tree(process_data["process"], force=True)
            self._append_project_log(
                f"[OPERATION] - (Multi-instance) - Timed out '{job.name}' after "
                f"{self.timeout_seconds // 60} minute(s); stopping worker.\n"
            )
            changed = True
        return changed

    def _finalize_timed_out_jobs(self):
        """Marks exhausted timed-out jobs as ``Timed Out`` instead of ``Failed``.

        A job that timed out and still has retry attempts left is left in the
        ``Failed`` state so the retry logic re-queues it. Once no retries remain,
        its terminal result is relabeled ``Timed Out`` so the cause is visible.

        Returns:
            bool: Whether any job status changed.
        """
        if not self.timed_out_jobs:
            return False
        changed = False
        for job_id in list(self.timed_out_jobs):
            job = self.session.get_job(job_id)
            if job is None:
                self.timed_out_jobs.discard(job_id)
                continue
            if job.id in self.running or job in self.regular_queue:
                continue
            if job.status != tracker_constants.Status.FAILED:
                continue
            if self._retries_remaining(job):
                continue
            job.status = tracker_constants.Status.TIMED_OUT
            self.timed_out_jobs.discard(job_id)
            changed = True
        return changed

    def _launch_available_jobs(self):
        """Launches regular jobs up to the requested worker limit.

        Returns:
            bool: Whether a worker was launched.
        """
        changed = False
        while self.regular_queue and len(self.running) < self.session.worker_count:
            job = self.regular_queue.pop(0)
            try:
                self._launch_job(job)
            except Exception as exception:
                self._record_launch_failure(job, exception)
            changed = True
        return changed

    def _advance_segments(self):
        """Materializes the current segment and advances across barriers.

        The first segment is materialized on the first call. Each later segment
        is materialized only once every job in the current segment reaches a
        terminal state, so a segment can read files produced by the segment
        before it.

        Returns:
            bool: Whether segment state changed.
        """
        if self.current_segment_index not in self._materialized_segments:
            self._materialize_segment(self.current_segment_index)
            self._materialized_segments.add(self.current_segment_index)
            return True
        if not self._segment_complete(self.current_segment_index):
            return False
        if self.current_segment_index + 1 < len(self.segments):
            self.current_segment_index += 1
            self._materialize_segment(self.current_segment_index)
            self._materialized_segments.add(self.current_segment_index)
            return True
        return False

    def _materialize_segment(self, segment_index):
        """Discovers a segment's source files and enqueues one job per file.

        Args:
            segment_index (int): Zero-based segment index to materialize.
        """
        segment = self.segments[segment_index]
        source_files = []
        if self.project:
            source_files = self.project.discover_segment_input_files(segment.get("input_tasks"))
        self._append_project_log(
            "[OPERATION] - (Multi-instance) - Segment {0}/{1} discovered {2} file(s).\n".format(
                segment_index + 1, len(self.segments), len(source_files)
            )
        )
        insert_at = self._get_regular_insert_index()
        new_jobs = []
        for source_file in source_files:
            self._job_counter += 1
            job = tracker_model.TrackerJob(
                job_id="seg{0:02d}-job-{1:04d}".format(segment_index + 1, self._job_counter),
                number=self._job_counter,
                source_file=source_file,
                task_definitions=segment.get("definitions") or [],
                segment_index=segment_index,
            )
            job.name = "[Seg {0}] {1}".format(segment_index + 1, job.name)
            new_jobs.append(job)
        for offset, job in enumerate(new_jobs):
            self.session.jobs.insert(insert_at + offset, job)
        self.regular_queue.extend(new_jobs)

    def _get_regular_insert_index(self):
        """Gets the index in session jobs where new regular jobs should go.

        Keeps the finalization job last so it renders and schedules after every
        regular job.

        Returns:
            int: Insertion index.
        """
        for index, job in enumerate(self.session.jobs):
            if job.is_finalization and not getattr(job, "is_preflight", False):
                return index
        return len(self.session.jobs)

    def _segment_jobs(self, segment_index):
        """Gets materialized regular jobs for a segment.

        Args:
            segment_index (int): Segment index.

        Returns:
            list: Regular jobs belonging to the segment.
        """
        return [
            job
            for job in self.session.regular_jobs
            if getattr(job, "segment_index", 0) == segment_index
        ]

    def _segment_complete(self, segment_index):
        """Checks whether every job in a segment reached a terminal state.

        A segment that discovered no files is complete immediately.

        Args:
            segment_index (int): Segment index.

        Returns:
            bool: True when the segment has no remaining work.
        """
        segment_jobs = self._segment_jobs(segment_index)
        if not segment_jobs:
            return True
        if any(job.id in self.running for job in segment_jobs):
            return False
        if any(job in self.regular_queue for job in segment_jobs):
            return False
        return all(job.status in tracker_constants.TERMINAL_STATUSES for job in segment_jobs)

    def _segments_remaining(self):
        """Checks whether any segment still needs to run.

        Returns:
            bool: True when segments are unmaterialized or the current one is unfinished.
        """
        if not self.segmented:
            return False
        if len(self._materialized_segments) < len(self.segments):
            return True
        return not self._segment_complete(self.current_segment_index)

    def _launch_job(self, job, final_task=None):
        """Launches one job worker.

        Args:
            job (TrackerJob): Job assigned to the worker.
            final_task (TrackerTask, optional): Specific deferred task to run.
        """
        event_path = os.path.join(self.get_events_dir(), f"{job.id}.jsonl")
        safe_name = self._safe_file_stem(job.name)
        suffix = f"_{final_task.number:02d}" if final_task else ""
        log_path = ""
        timing_path = ""
        if not self.options.no_log:
            log_path = os.path.join(self.get_logs_dir(), f"{safe_name}_{job.id}{suffix}.log")
        if self.options.task_time_logs:
            timing_path = os.path.join(self.get_logs_dir(), f"{safe_name}_{job.id}{suffix}_task_times.log")
        job.log_path = log_path or job.log_path
        job.timing_log_path = timing_path or job.timing_log_path
        worker_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tracker_worker.py")
        command = [
            self.options.mayapy,
            worker_script,
            "--project-file",
            self.options.project_file,
            "--source-file",
            job.source_file,
            "--job-id",
            job.id,
            "--event-file",
            event_path,
            "--worker-id",
            str(job.number),
            "--total-jobs",
            str(len(self.session.regular_jobs)),
        ]
        if final_task:
            command.extend(["--final-task-id", final_task.id])
        elif self.segmented:
            segment = self.segments[getattr(job, "segment_index", 0)]
            for task_id in segment.get("task_ids") or []:
                command.extend(["--task-id", task_id])
        else:
            if self.options.run_from_task_id:
                command.extend(["--run-from-task-id", self.options.run_from_task_id])
            if self.options.run_to_task_id:
                command.extend(["--run-to-task-id", self.options.run_to_task_id])
            for task_id in self.options.final_task_id:
                command.extend(["--skip-task-id", task_id])
            for task_id in getattr(self.options, "skip_task_id", []) or []:
                command.extend(["--skip-task-id", task_id])
        if log_path:
            command.extend(["--log-file", log_path])
        if timing_path:
            command.extend(["--task-time-log-file", timing_path])
        environment = dict(os.environ)
        environment["PYTHONIOENCODING"] = "utf-8"
        creation_flags = 0
        popen_kwargs = {}
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        else:
            popen_kwargs["start_new_session"] = True
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            shell=False,
            env=environment,
            creationflags=creation_flags,
            **popen_kwargs,
        )
        job.status = tracker_constants.Status.WAITING
        job.worker = str(job.number)
        if not job.started_at:
            job.started_at = tracker_events.utc_now_iso()
        self.readers.setdefault(job.id, tracker_events.EventReader(event_path))
        self.running[job.id] = {
            "process": process,
            "job": job,
            "final_task": final_task,
            "log_path": log_path,
            "cancel_requested_at": None,
            "cancel_force_requested": False,
            "started_monotonic": time.monotonic(),
            "timed_out": False,
        }
        if log_path:
            self.worker_log_offsets[log_path] = 0
        target_name = final_task.name if final_task else job.name
        self._append_project_log(
            f"[OPERATION] - (Multi-instance) - Launched '{target_name}' "
            f"(Worker {job.worker}).\n"
        )

    def _consume_events(self):
        """Consumes all new worker event records.

        Returns:
            bool: Whether state changed.
        """
        changed = False
        for reader in self.readers.values():
            for event in reader.read_new():
                self.session.apply_event(event)
                process_data = self.running.get(event.get("job_id"))
                if process_data and process_data.get("cancel_requested_at") is not None:
                    process_data["job"].status = tracker_constants.Status.CANCELING
                changed = True
        return changed

    def _collect_finished_processes(self):
        """Collects exited workers and applies fallback terminal states.

        Returns:
            bool: Whether a worker exited.
        """
        changed = False
        for job_id, process_data in list(self.running.items()):
            process = process_data["process"]
            return_code = process.poll()
            if return_code is None:
                continue
            self._consume_worker_log(process_data.get("log_path"))
            reader = self.readers.get(job_id)
            if reader:
                for event in reader.read_new():
                    self.session.apply_event(event)
            job = process_data["job"]
            final_task = process_data["final_task"]
            cancellation_requested = process_data.get("cancel_requested_at") is not None
            if self.session.aborting or cancellation_requested:
                self._mark_job_canceled(job)
                if cancellation_requested:
                    self._append_project_log(
                        f"[OPERATION] - (Multi-instance) - Canceled running job '{job.name}'.\n"
                    )
            elif return_code:
                job.status = tracker_constants.Status.FAILED
                job.completed_at = tracker_events.utc_now_iso()
                active_task = final_task or next(
                    (task for task in job.tasks if task.status == tracker_constants.Status.RUNNING), None
                )
                if active_task:
                    active_task.status = tracker_constants.Status.FAILED
                    active_task.errors = max(1, active_task.errors)
                    active_task.completed_at = job.completed_at
            elif job.status not in tracker_constants.TERMINAL_STATUSES:
                job.status = tracker_constants.Status.COMPLETED_WARNINGS
                job.completed_at = tracker_events.utc_now_iso()
                for task in job.tasks:
                    if task.status not in tracker_constants.TERMINAL_STATUSES:
                        task.status = tracker_constants.Status.COMPLETED_WARNINGS
                        task.progress = 100
                        task.warnings += 1
                        task.messages.append(("Warning", "Worker exited without a terminal tracker event."))
                        task.completed_at = job.completed_at
            if final_task and not self.session.aborting:
                self.final_task_index += 1
                if self.final_task_index < len(job.tasks):
                    job.status = tracker_constants.Status.PENDING_FINALIZATION
                    job.completed_at = ""
            self.running.pop(job_id)
            changed = True
        return changed

    def _consume_worker_logs(self):
        """Copies newly flushed worker output into the main project log.

        Returns:
            bool: Whether any new output was copied.
        """
        copied_output = False
        for process_data in self.running.values():
            copied_output = self._consume_worker_log(process_data.get("log_path")) or copied_output
        return copied_output

    def _consume_worker_log(self, log_path):
        """Copies unread bytes from one worker log into the project log.

        Args:
            log_path (str): Worker log path.

        Returns:
            bool: Whether new output was copied.
        """
        project_log_path = self.session.project_log_path
        if not log_path or not project_log_path or not os.path.isfile(log_path):
            return False
        if os.path.normcase(os.path.abspath(log_path)) == os.path.normcase(os.path.abspath(project_log_path)):
            return False
        try:
            file_size = os.path.getsize(log_path)
            offset = self.worker_log_offsets.get(log_path, 0)
            if file_size < offset:
                offset = 0
            if file_size == offset:
                return False
            with open(log_path, "rb") as log_file:
                log_file.seek(offset)
                output = log_file.read()
            self.worker_log_offsets[log_path] = file_size
        except OSError:
            return False
        if not output:
            return False
        self._append_project_log(output.decode("utf-8", errors="replace"))
        return True

    def _append_project_log(self, text):
        """Appends text to the persistent main project log.

        Args:
            text (str): Text to append.
        """
        project_log_path = self.session.project_log_path
        if not project_log_path or not text:
            return
        try:
            log_dir = os.path.dirname(project_log_path)
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)
            with open(project_log_path, "a", encoding="utf-8") as log_file:
                log_file.write(text)
                log_file.flush()
        except OSError:
            return

    def _append_project_summary(self):
        """Writes a final immutable batch summary to the project log."""
        regular_jobs = self.session.regular_jobs
        tasks = [task for job in self.session.jobs for task in job.tasks]
        completed_files = len(
            [job for job in regular_jobs if job.status in tracker_constants.TERMINAL_STATUSES]
        )
        completed_tasks = len([task for task in tasks if task.status in tracker_constants.TERMINAL_STATUSES])
        failed = len([job for job in regular_jobs if job.status == tracker_constants.Status.FAILED])
        canceled = len([job for job in regular_jobs if job.status == tracker_constants.Status.CANCELED])
        errors = sum(job.errors for job in regular_jobs)
        warnings = sum(job.warnings for job in regular_jobs)
        result = "Aborted" if self.session.aborting or canceled else "Completed"
        self._append_project_log(
            "\n"
            f"[OPERATION] - (Multi-instance) - {result}. "
            f"Tasks {completed_tasks}/{len(tasks)} | Files {completed_files}/{len(regular_jobs)} | "
            f"Progress {self.session.progress}% | "
            f"Failed {failed} | Canceled {canceled} | Errors {errors} | Warnings {warnings}.\n"
        )

    def _advance_finalization(self):
        """Starts or completes the deferred finalization phase.

        Returns:
            bool: Whether finalization state changed.
        """
        job = self.finalization_job
        if not job or self.regular_queue or any(not data["job"].is_finalization for data in self.running.values()):
            return False
        if self._segments_remaining():
            return False
        if job.id in self.running:
            return False
        if self._preserve_terminal_finalization and job.status in tracker_constants.TERMINAL_STATUSES:
            return False
        blocking_statuses = {
            tracker_constants.Status.FAILED,
            tracker_constants.Status.TIMED_OUT,
            tracker_constants.Status.CANCELED,
        }
        blocking_jobs = [
            regular
            for regular in self.session.regular_jobs
            if regular.status in blocking_statuses
        ]
        if blocking_jobs:
            skip_message = self._build_finalization_skip_message(blocking_jobs)
            job.status = tracker_constants.Status.SKIPPED
            job.completed_at = tracker_events.utc_now_iso()
            for task in job.tasks:
                task.status = tracker_constants.Status.SKIPPED
                task.progress = 100
                task.completed_at = job.completed_at
                task.messages.append(("Info", skip_message))
            self._append_project_log(f"[SKIPPED] - (Multi-instance) - {skip_message}\n")
            return True
        if self.final_task_index < len(job.tasks):
            try:
                self._launch_job(job, final_task=job.tasks[self.final_task_index])
            except Exception as exception:
                failed_task = job.tasks[self.final_task_index]
                self._record_launch_failure(job, exception, task=failed_task)
                self.final_task_index += 1
            return True
        if any(task.status == tracker_constants.Status.FAILED for task in job.tasks):
            job.status = tracker_constants.Status.FAILED
        elif any(task.status == tracker_constants.Status.COMPLETED_WARNINGS for task in job.tasks):
            job.status = tracker_constants.Status.COMPLETED_WARNINGS
        else:
            job.status = tracker_constants.Status.COMPLETED
        job.completed_at = tracker_events.utc_now_iso()
        return True

    @staticmethod
    def _build_finalization_skip_message(blocking_jobs):
        """Builds a concise explanation for skipped run-once final tasks.

        Args:
            blocking_jobs (list): Regular jobs that did not complete successfully.

        Returns:
            str: User-facing finalization skip message.
        """
        status_counts = {}
        job_descriptions = []
        for job in blocking_jobs:
            status_name = str(job.status or "Unknown").lower()
            status_counts[status_name] = status_counts.get(status_name, 0) + 1
            source_name = os.path.basename(str(job.source_file or "")) or str(job.name or "Unknown source")
            job_descriptions.append(f"{source_name} ({status_name})")
        status_text = ", ".join(
            f"{status_name}: {count}"
            for status_name, count in sorted(status_counts.items())
        )
        max_job_descriptions = 5
        visible_jobs = job_descriptions[:max_job_descriptions]
        if len(job_descriptions) > max_job_descriptions:
            visible_jobs.append(f"and {len(job_descriptions) - max_job_descriptions} more")
        job_count = len(blocking_jobs)
        job_label = "job" if job_count == 1 else "jobs"
        return (
            f"Run-once final tasks were skipped because {job_count} regular {job_label} did not finish successfully "
            f"({status_text}). Affected jobs: {', '.join(visible_jobs)}."
        )

    def _advance_abort(self):
        """Force-kills workers that exceed the abort grace period.

        Returns:
            bool: Whether force termination was requested.
        """
        if not self.running or self.abort_requested_at is None:
            return False
        if time.monotonic() - self.abort_requested_at < 3.0:
            return False
        for process_data in self.running.values():
            tracker_process_utils.terminate_process_tree(process_data["process"], force=True)
        self.abort_requested_at = time.monotonic() + 3600.0
        return True

    def _advance_job_cancellations(self):
        """Force-terminates individual jobs that exceed the cancellation grace period.

        Returns:
            bool: True when a force-termination request was issued.
        """
        changed = False
        current_time = time.monotonic()
        for process_data in self.running.values():
            requested_at = process_data.get("cancel_requested_at")
            if requested_at is None or process_data.get("cancel_force_requested"):
                continue
            if current_time - requested_at < 3.0:
                continue
            tracker_process_utils.terminate_process_tree(process_data["process"], force=True)
            process_data["cancel_force_requested"] = True
            changed = True
        return changed

    def _is_finished(self):
        """Checks whether the session reached a terminal state.

        Returns:
            bool: True when no scheduling work remains.
        """
        if self.running or self.regular_queue:
            return False
        if self.session.aborting:
            return True
        if self._segments_remaining():
            return False
        if self.finalization_job:
            return self.finalization_job.status in tracker_constants.TERMINAL_STATUSES
        return all(job.status in tracker_constants.TERMINAL_STATUSES for job in self.session.regular_jobs)

    def cleanup_report_parts(self):
        """Removes completed report parts after all tracker workers have stopped.

        Each worker writes a partial report so files must remain available while
        the queue is active. The scheduler is the only component that can
        safely clean them in regular multi-worker mode because it knows every
        worker has reached a terminal state.
        """
        if self._report_parts_cleaned or not self.project:
            return
        self._report_parts_cleaned = True
        try:
            from gt.tools.batch_processor import batch_processor_task_base as task_base
            from gt.tools.batch_processor.tasks import task_report
        except ImportError:
            return

        run_id = task_base.build_run_id(self.get_events_dir())
        for task in self.project.get_enabled_tasks():
            if not isinstance(task, task_report.TaskSceneReport):
                continue
            task_index = self.project.get_task_environment_index(task)
            step_output_dir = task.resolve_task_path(self.project, task_index=task_index)
            base_report_path = task_report.build_report_path(
                task=task,
                step_output_dir=step_output_dir,
                project=self.project,
            )
            parts_dir = task_report.get_parts_dir(base_report_path)
            try:
                with task_report.report_lock(parts_dir, timeout_seconds=0) as acquired:
                    if not acquired:
                        continue
                    deleted_count = task_report.cleanup_report_parts(parts_dir, run_id)
                task_report.remove_parts_directory_if_empty(parts_dir)
                if deleted_count:
                    self._append_project_log(
                        f"[INFO] - (Report) - Removed {deleted_count} temporary report part file(s).\n"
                    )
            except Exception as exception:
                self._append_project_log(
                    f"[WARNING] - (Report) - Unable to clean temporary report parts: {exception}\n"
                )
                continue

    @staticmethod
    def _mark_job_canceled(job):
        """Marks a job and all unfinished tasks as canceled.

        Args:
            job (TrackerJob): Job whose unfinished state should be canceled.
        """
        timestamp = tracker_events.utc_now_iso()
        job.status = tracker_constants.Status.CANCELED
        job.completed_at = timestamp
        job.completion_result = ""
        for task in job.tasks:
            if task.status not in tracker_constants.TERMINAL_STATUSES:
                task.status = tracker_constants.Status.CANCELED
                task.completed_at = timestamp

    def write_state(self):
        """Atomically writes a recoverable session summary."""
        state_path = os.path.join(self.session.session_dir, "session.json")
        temporary_path = state_path + ".tmp"
        data = {
            "project_name": self.session.project_name,
            "project_path": self.session.project_path,
            "project_log_path": self.session.project_log_path,
            "source_project_file": self.session.source_project_file,
            "worker_count": self.session.worker_count,
            "started_at": self.session.started_at,
            "completed_at": self.session.completed_at,
            "finished": self.session.finished,
            "aborting": self.session.aborting,
            "flag_skips_as_warnings": self.session.flag_skips_as_warnings,
            "jobs": [self._serialize_job(job) for job in self.session.jobs],
        }
        with open(temporary_path, "w", encoding="utf-8") as state_file:
            json.dump(data, state_file, indent=2, ensure_ascii=False, sort_keys=True)
        os.replace(temporary_path, state_path)

    @staticmethod
    def _record_launch_failure(job, exception, task=None):
        """Records a worker launch failure without stopping the scheduler.

        Args:
            job (TrackerJob): Job that could not launch.
            exception (Exception): Launch exception.
            task (TrackerTask, optional): Specific finalization task.
        """
        timestamp = tracker_events.utc_now_iso()
        job.status = tracker_constants.Status.FAILED
        job.completed_at = timestamp
        target_task = task or (job.tasks[0] if job.tasks else None)
        if target_task:
            target_task.status = tracker_constants.Status.FAILED
            target_task.progress = 100
            target_task.errors += 1
            target_task.messages.append(("Error", f"Unable to launch worker: {exception}"))
            target_task.completed_at = timestamp

    @staticmethod
    def _serialize_job(job):
        """Serializes one tracker job.

        Args:
            job (TrackerJob): Job to serialize.

        Returns:
            dict: JSON-compatible job state.
        """
        return {
            "id": job.id,
            "number": job.number,
            "name": job.name,
            "source_file": job.source_file,
            "segment_index": getattr(job, "segment_index", 0),
            "status": job.status,
            "progress": job.progress,
            "errors": job.errors,
            "warnings": job.warnings,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "worker": job.worker,
            "log_path": job.log_path,
            "timing_log_path": job.timing_log_path,
            "tasks": [
                {
                    "id": task.id,
                    "number": task.number,
                    "name": task.name,
                    "status": task.status,
                    "progress": task.progress,
                    "errors": task.errors,
                    "warnings": task.warnings,
                    "reported_warnings": task.reported_warnings,
                    "skipped_items": task.skipped_items,
                    "started_at": task.started_at,
                    "completed_at": task.completed_at,
                    "worker": task.worker,
                    "log_paths": list(task.log_paths),
                    "messages": list(task.messages),
                }
                for task in job.tasks
            ],
        }

    @staticmethod
    def _safe_file_stem(value):
        """Builds a filesystem-safe log stem.

        Args:
            value (str): Requested stem.

        Returns:
            str: Safe stem.
        """
        stem = os.path.splitext(os.path.basename(value or "job"))[0]
        return re.sub(r"[^A-Za-z0-9_.-]+", "_", stem).strip("._") or "job"
