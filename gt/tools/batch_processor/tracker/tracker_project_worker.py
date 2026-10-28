"""Executes a saved single-instance child while emitting ordinary tracker events."""

import os
import sys
import traceback

if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))

from gt.tools.batch_processor.batch_processor_tracker import BatchProgressTracker


class ProjectProgressTracker(BatchProgressTracker):
    """Adapts the existing single-instance runner's counters to tracker events."""

    def __init__(self, project, writer):
        """Stores the project and event transport.

        Args:
            project (BatchProcessorModel): Complete child project.
            writer (EventWriter): Owned worker event writer.
        """
        super().__init__()
        self.project = project
        self.writer = writer
        self.active_task = None
        self.step_counts = (0, 0, 0)

    def start_step(self, step_index, step_name):
        """Publishes task boundaries while preserving native task order.

        Args:
            step_index (int): One-based native task index.
            step_name (str): Task display name.
        """
        self.finish_step()
        super().start_step(step_index, step_name)
        task = self.project.get_enabled_tasks()[step_index - 1]
        self.active_task = None if task.is_input_task else task
        self.step_counts = (self.succeeded, self.failed, self.skipped)
        if self.active_task:
            self.writer.emit("task_started", task_id=task.id, total_items=1)

    def finish_step(self):
        """Publishes counters for the completed native processing task."""
        if not self.active_task:
            return
        succeeded = self.succeeded - self.step_counts[0]
        failed = self.failed - self.step_counts[1]
        skipped = self.skipped - self.step_counts[2]
        self.writer.emit("task_finished", task_id=self.active_task.id,
                         status="failed" if failed else "succeeded",
                         completed_items=succeeded + skipped, total_items=max(1, succeeded + failed + skipped),
                         errors=failed, skipped_items=skipped)
        self.active_task = None

    def record_message(self, message):
        """Writes native runner messages to its captured worker log.

        Args:
            message (str): Runner message.
        """
        super().record_message(message)
        print(message, flush=True)

    def record_warning(self):
        """Forwards warnings to the active tracker task."""
        super().record_warning()
        if self.active_task:
            self.writer.emit("warning", task_id=self.active_task.id, message="Child task reported a warning.")

    def finish(self, failed=False):
        """Finalizes the last native task.

        Args:
            failed (bool, optional): Whether the native run failed.
        """
        if failed and self.active_task and self.failed == self.step_counts[1]:
            self.record_failure()
        self.finish_step()
        super().finish(failed=failed)


def main():
    """Runs a complete child with the existing single-instance semantics."""
    from gt.tools.batch_processor.tracker import tracker_worker
    from gt.tools.batch_processor.tracker.tracker_events import EventWriter
    from gt.tools.batch_processor.batch_processor_model import BatchProcessorModel
    from gt.tools.batch_processor.batch_processor_worker import SingleInstanceBatchRunner
    from gt.tools.batch_processor import batch_processor_maya

    tracker_worker.configure_utf8_output()
    args = tracker_worker.parse_args()
    tee = tracker_worker.install_tee_log(args.log_file)
    writer = EventWriter(args.event_file, args.job_id)
    failed = True
    try:
        project = BatchProcessorModel.from_file(args.project_file)
        writer.emit("worker_started", worker_id=args.worker_id)
        writer.emit("job_started")
        tracker = ProjectProgressTracker(project, writer)
        runner = SingleInstanceBatchRunner(tracker=tracker, task_time_log_path=args.task_time_log_file)
        enabled = project.get_enabled_tasks()
        empty = not runner._get_initial_source_files(project, enabled) and not any(
            getattr(task, "is_aggregate_task", False) for task in enabled)
        if empty:
            writer.emit("project_empty")
            for task in enabled:
                if not task.is_input_task:
                    writer.emit("task_finished", task_id=task.id, status="skipped", skipped_items=1)
            failed = False
        else:
            runner.run(project)
            writer.emit("run_state", state=project._batch_run_state)
            failed = tracker.status == "failed"
    except Exception as error:
        print(traceback.format_exc(), flush=True)
        writer.emit("error", message=str(error))
    finally:
        writer.emit("job_finished", status="failed" if failed else "completed")
        writer.close()
        tracker_worker.close_tee_log(tee)
        batch_processor_maya.shutdown_standalone()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
