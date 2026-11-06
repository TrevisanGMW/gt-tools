"""Durable child project progress, result publication, and cancellation."""

import os
import time

from gt.tools.batch_processor import batch_processor_projects as projects


class ProjectReporter:
    """Bridges a tracker session to its launching project without Qt dependencies."""

    def __init__(self, scheduler):
        """Stores the owned scheduler and publication state.

        Args:
            scheduler (TrackerScheduler): Child scheduler.
        """
        self.scheduler = scheduler
        self.options = scheduler.options
        self.last_publication = 0
        self.published = False
        self.last_run_settings_sequence = 0

    def tick(self):
        """Publishes liveness and terminal results, and consumes cancellation."""
        result_file = getattr(self.options, "result_file", "")
        if not result_file or self.published:
            return
        control = projects.read_json(getattr(self.options, "control_file", ""))
        run_id = getattr(self.options, "run_id", "")
        if control.get("action") == "cancel" and control.get("run_id") == run_id:
            self.scheduler.abort()
        self._consume_run_settings_request(run_id)
        session = self.scheduler.session
        if time.monotonic() - self.last_publication >= 1 or session.finished:
            status_file = getattr(self.options, "status_file", "")
            if status_file:
                projects.write_json(status_file, {
                    "schema_version": projects.SCHEMA_VERSION, "run_id": run_id,
                    "heartbeat": time.time(), "progress": session.progress,
                    "tracker_pid": os.getpid(),
                    "finished": session.finished, "session_dir": session.session_dir,
                    "active_workers": len(self.scheduler.running),
                    "run_settings": self.scheduler.run_settings.to_dict(),
                })
            self.last_publication = time.monotonic()
        if session.finished:
            result = projects.build_result(
                session, self.scheduler.job_retry_counts, run_id,
                getattr(self.options, "parent_run_id", ""), getattr(self.options, "empty_policy", "Warning"))
            result["jobs"] = [self.scheduler._serialize_job(job) for job in session.jobs]
            summary_path = os.path.join(os.path.dirname(result_file), "summary.log")
            with open(summary_path, "w", encoding="utf-8") as summary:
                summary.write(f"Project: {session.source_project_file}\nOutcome: {result['outcome']}\n")
                summary.write(f"Counts: {result['counts']}\nSession: {session.session_dir}\n")
                for job in session.jobs:
                    summary.write(f"{job.name}: {job.status}\n")
            projects.write_json(result_file, result)
            self.published = True

    def _consume_run_settings_request(self, run_id):
        """Applies a new live run settings request written by ``ProjectRun.set_run_settings``.

        Requests carry an increasing sequence number so each one is applied once.
        They count as manual changes, like edits made in the tracker window.

        Args:
            run_id (str): Run id the request must match.
        """
        request_path = projects.get_run_settings_request_path(getattr(self.options, "control_file", ""))
        if not request_path or self.scheduler.session.finished:
            return
        request = projects.read_json(request_path)
        if not request or request.get("run_id") != run_id:
            return
        try:
            sequence = int(request.get("sequence") or 0)
        except (TypeError, ValueError):
            return
        if sequence <= self.last_run_settings_sequence:
            return
        self.last_run_settings_sequence = sequence
        if request.get("keep_manual_changes") is not None:
            self.scheduler.run_settings.keep_manual_changes = bool(request.get("keep_manual_changes"))
        self.scheduler.update_run_settings(request.get("settings") or {}, source="external request", manual=True)


def publish_startup_failure(options, error):
    """Reports failures before a tracker session can be created.

    Args:
        options (argparse.Namespace): Tracker launch options.
        error (Exception): Startup error.
    """
    result_file = getattr(options, "result_file", "")
    if result_file and not projects.read_json(result_file).get("finished"):
        projects.write_json(result_file, {
            "schema_version": projects.SCHEMA_VERSION, "finished": True,
            "run_id": getattr(options, "run_id", ""),
            "parent_run_id": getattr(options, "parent_run_id", ""),
            "source_project_file": getattr(options, "source_project_file", ""),
            "outcome": "failed", "reason": str(error), "counts": {"failed": 1},
        })
