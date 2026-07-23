"""Batch Processor worker used by the standalone Qt tracker."""

import argparse
import os
import sys
import time
import traceback


def configure_utf8_output():
    """Configures console streams for UTF-8 status output when possible."""
    if os.name == "nt":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            ctypes.windll.kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    for stream in [sys.stdout, sys.stderr]:
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def add_package_root_to_sys_path():
    """Adds the gt-tools package root to sys.path for direct script execution."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)


def parse_args():
    """Parses command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Batch Processor Worker")
    parser.add_argument("--project-file", required=True, help="Path to a .batch project snapshot.")
    parser.add_argument("--source-file", required=True, help="Source file assigned to this worker.")
    parser.add_argument("--job-id", required=True, help="Stable tracker job identifier.")
    parser.add_argument("--event-file", required=True, help="Structured tracker event stream path.")
    parser.add_argument("--run-from-task-id", default="", help="Optional task id to start from.")
    parser.add_argument("--run-to-task-id", default="", help="Optional task id to stop after.")
    parser.add_argument(
        "--skip-task-id",
        action="append",
        default=[],
        help="Task id deferred to the tracker final phase.",
    )
    parser.add_argument("--final-task-id", default="", help="Run only this task using its discovered source path.")
    parser.add_argument(
        "--task-id",
        action="append",
        default=[],
        help="Explicit processing task id to run, in order (used for segmented runs).",
    )
    parser.add_argument("--worker-id", default="", help="Worker identifier for logs.")
    parser.add_argument("--total-jobs", default="1", help="Total job count for tracker messages.")
    parser.add_argument("--log-file", default="", help="Optional log file used while stdout remains visible.")
    parser.add_argument("--task-time-log-file", default="", help="Optional separate task timing log file.")
    parser.add_argument("--flag-running-tasks", action="store_true", help="Print concise running-task updates.")
    parser.add_argument("--flag-skipped-tasks", action="store_true", help="Print explicit skipped-task warnings.")
    parser.add_argument("--hold-open-seconds", type=float, default=0, help="Seconds to keep a worker console open.")
    return parser.parse_args()


def main():
    """Runs one source file through the selected batch task chain."""
    configure_utf8_output()
    add_package_root_to_sys_path()
    args = parse_args()
    tee_context = install_tee_log(args.log_file)

    from gt.tools.batch_processor import batch_processor_model
    from gt.tools.batch_processor import batch_processor_tasks as tasks
    from gt.tools.batch_processor import batch_processor_worker
    from gt.tools.batch_processor.tracker import tracker_events

    event_writer = tracker_events.EventWriter(file_path=args.event_file, job_id=args.job_id)
    event_writer.emit("worker_started", worker_id=args.worker_id, source_file=args.source_file)
    if args.log_file:
        event_writer.emit("log_artifact", path=args.log_file, kind="worker_log")
    if args.task_time_log_file:
        event_writer.emit("log_artifact", path=args.task_time_log_file, kind="timing_log")

    print("[OPERATION] - (worker) - Starting worker {0}".format(args.worker_id or ""))
    print("[INFO] - (worker) - Source file: {0}".format(args.source_file))
    project = batch_processor_model.BatchProcessorModel.from_file(args.project_file)
    runner = batch_processor_worker.SingleInstanceBatchRunner()
    if args.final_task_id:
        final_task = project.get_task(args.final_task_id)
        if not final_task or final_task.is_input_task or not final_task.enabled:
            raise RuntimeError(f"Unable to resolve enabled final task: {args.final_task_id}")
        process_tasks = [final_task]
    elif args.task_id:
        tasks_by_id = {task.id: task for task in project.get_enabled_tasks()}
        process_tasks = [tasks_by_id[task_id] for task_id in args.task_id if task_id in tasks_by_id]
        if not process_tasks:
            raise RuntimeError("Unable to resolve any segment task id for this worker.")
    else:
        process_tasks = runner._trim_tasks(
            project.get_enabled_tasks(),
            args.run_from_task_id or None,
            args.run_to_task_id or None,
        )
        skipped_task_ids = set(args.skip_task_id or [])
        process_tasks = [task for task in process_tasks if task.id not in skipped_task_ids]
    executable_tasks = [task for task in process_tasks if not task.is_input_task]
    total_task_count = len(executable_tasks)
    if args.final_task_id:
        current_items = discover_final_task_work_items(
            project=project,
            task=executable_tasks[0],
            batch_processor_worker=batch_processor_worker,
            tasks=tasks,
        )
        tracker_file_name = executable_tasks[0].display_name
        print(f"[INFO] - (worker) - Final task discovered {len(current_items)} source item(s).")
    else:
        current_items = [
            batch_processor_worker.create_initial_work_item(
                project=project,
                source_file=args.source_file,
                run_from_task_id=args.run_from_task_id or None,
            )
        ]
        tracker_file_name = os.path.basename(args.source_file)
    failed = False
    skipped = 0
    succeeded = 0
    global_item_index = get_global_item_index(args.worker_id)
    active_task = None
    active_task_index = 0
    active_task_started = None
    task_timing_recorded = True

    try:
        event_writer.emit("job_started", worker_id=args.worker_id)
        for task_index, task in enumerate(executable_tasks, 1):
            active_task = task
            active_task_index = task_index
            active_task_started = time.perf_counter()
            task_timing_recorded = False
            remaining_tasks = max(0, total_task_count - task_index)
            args.current_task_index = task_index
            args.total_tasks = total_task_count
            event_writer.emit(
                "task_started",
                task_id=task.id,
                task_index=task_index,
                total_tasks=total_task_count,
                total_items=max(1, len(current_items)),
                worker_id=args.worker_id,
            )
            print_running_task_flag(
                args=args,
                task=task,
                file_name=tracker_file_name,
            )
            task_environment_index = project.get_task_environment_index(task)
            step_output_dir = task.resolve_task_path(project, task_index=task_environment_index)
            print(
                "[OPERATION] - (worker {0}) - Task {1}/{2}: {3} ({4} left for this job)".format(
                    args.worker_id or "",
                    task_index,
                    total_task_count,
                    task.display_name,
                    remaining_tasks,
                )
            )
            validation_context = {"item_index": global_item_index}
            validation = task.validate_work_items(current_items, project, step_output_dir, context=validation_context)
            if validation.errors:
                raise RuntimeError("; ".join(validation.errors))
            for warning in validation.warnings:
                print("[WARNING] - ({0}) - {1}".format(task.task_type, warning))
                event_name = "skip_notice" if "skip" in str(warning).lower() else "warning"
                event_writer.emit(event_name, task_id=task.id, message=str(warning))
            output_items = []
            task_succeeded = 0
            task_skipped = 0
            if task.writes_to_target_path():
                ensure_directory(step_output_dir)
            if getattr(task, "is_aggregate_task", False):
                context = {
                    "item_index": global_item_index,
                    "total_items": len(current_items),
                    "work_items": list(current_items),
                    "worker_id": args.worker_id,
                    "report_log": lambda path, task_id=task.id: event_writer.emit(
                        "log_artifact", task_id=task_id, path=path, kind="task_log"
                    ),
                }
                print(
                    "[INFO] - ({0}) - Processing aggregate task with {1} incoming file(s).".format(
                        task.task_type, len(current_items)
                    )
                )
                try:
                    output_item = task.execute(None, project, step_output_dir, context=context)
                    if isinstance(output_item, list):
                        output_items.extend(output_item)
                    elif output_item:
                        output_items.append(output_item)
                    succeeded += 1
                    task_succeeded += 1
                    event_writer.emit(
                        "task_progress",
                        task_id=task.id,
                        completed_items=1,
                        total_items=1,
                    )
                except tasks.TaskSkip as exception:
                    skipped += 1
                    task_skipped += 1
                    append_skipped_output_items(output_items=output_items, exception=exception)
                    print("[SKIPPED] - ({0}) - {1}".format(task.task_type, exception))
                    print_skipped_task_flag(args, task, exception, file_name=os.path.basename(args.source_file))
                    event_writer.emit(
                        "task_progress",
                        task_id=task.id,
                        completed_items=1,
                        total_items=1,
                    )
            else:
                for index, work_item in enumerate(current_items, 1):
                    context = {
                        "item_index": global_item_index + index - 1,
                        "total_items": len(current_items),
                        "work_items": list(current_items),
                        "worker_id": args.worker_id,
                        "report_log": lambda path, task_id=task.id: event_writer.emit(
                            "log_artifact", task_id=task_id, path=path, kind="task_log"
                        ),
                    }
                    print(
                        "[INFO] - ({0}) - Processing file {1}/{2}: {3}".format(
                            task.task_type,
                            index,
                            len(current_items),
                            work_item.current_path,
                        )
                    )
                    try:
                        output_item = task.execute(work_item, project, step_output_dir, context=context)
                        if isinstance(output_item, list):
                            output_items.extend(output_item)
                        elif output_item:
                            output_items.append(output_item)
                        succeeded += 1
                        task_succeeded += 1
                    except tasks.TaskSkip as exception:
                        skipped += 1
                        task_skipped += 1
                        append_skipped_output_items(
                            output_items=output_items,
                            exception=exception,
                            work_item=work_item,
                        )
                        print("[SKIPPED] - ({0}) - {1}".format(task.task_type, exception))
                        print_skipped_task_flag(
                            args,
                            task,
                            exception,
                            file_name=os.path.basename(work_item.current_path),
                        )
                    event_writer.emit(
                        "task_progress",
                        task_id=task.id,
                        completed_items=task_succeeded + task_skipped,
                        total_items=len(current_items),
                    )
            print(
                "[INFO] - ({0}) - Task {1}/{2} finished. Processed: {3}. Skipped: {4}.".format(
                    task.task_type,
                    task_index,
                    total_task_count,
                    task_succeeded + task_skipped,
                    task_skipped,
                )
            )
            task_status = "succeeded"
            if task_skipped and task_succeeded:
                task_status = "warning"
            elif task_skipped:
                task_status = "skipped"
            event_writer.emit(
                "task_finished",
                task_id=task.id,
                status=task_status,
                completed_items=task_succeeded + task_skipped,
                total_items=max(1, len(current_items)),
                errors=0,
                warnings=0,
                skipped_items=task_skipped,
            )
            batch_processor_worker.append_task_timing_log(
                log_file_path=args.task_time_log_file,
                task=task,
                task_index=task_index,
                total_tasks=total_task_count,
                duration_seconds=time.perf_counter() - active_task_started,
                status=task_status,
            )
            task_timing_recorded = True
            current_items = output_items
            if not current_items:
                print("[SKIPPED] - ({0}) - No output items remained after this task.".format(task.task_type))
                break
    except Exception as exception:
        failed = True
        if active_task:
            event_writer.emit("error", task_id=active_task.id, message=str(exception))
            event_writer.emit(
                "task_finished",
                task_id=active_task.id,
                status="failed",
                completed_items=0,
                total_items=max(1, len(current_items)),
                errors=1,
                warnings=0,
            )
        if active_task and active_task_started is not None and not task_timing_recorded:
            batch_processor_worker.append_task_timing_log(
                log_file_path=args.task_time_log_file,
                task=active_task,
                task_index=active_task_index,
                total_tasks=total_task_count,
                duration_seconds=time.perf_counter() - active_task_started,
                status="failed",
            )
        print("[ERROR] - (worker) - {0}".format(exception))
        print(traceback.format_exc())

    print(
        (
            "[INFO] - (worker) - Finished worker {0}. Files processed: {1}. "
            "Succeeded: {2}. Skipped: {3}. Failed: {4}."
        ).format(
            args.worker_id or "",
            succeeded + skipped,
            succeeded,
            skipped,
            int(failed),
        )
    )
    hold_worker_window(args.hold_open_seconds)
    event_writer.emit("job_finished", status="failed" if failed else "completed")
    event_writer.close()
    close_tee_log(tee_context)
    if failed:
        sys.exit(1)
    sys.exit(0)


class TeeStream:
    """Writes stream output to multiple target streams."""

    def __init__(self, *streams):
        """Initializes the tee stream.

        Args:
            *streams: Writable stream objects.
        """
        self.streams = streams

    def write(self, data):
        """Writes data to all available streams.

        Args:
            data (str): Text data to write.
        """
        for stream in self.streams:
            try:
                stream.write(data)
                if "\n" in data:
                    stream.flush()
            except Exception:
                pass

    def flush(self):
        """Flushes all available streams."""
        for stream in self.streams:
            try:
                stream.flush()
            except Exception:
                pass


def install_tee_log(log_file_path):
    """Installs a stdout/stderr tee that also writes to a log file.

    Args:
        log_file_path (str): Log file path.

    Returns:
        dict or None: Tee context used to restore streams.
    """
    if not log_file_path:
        return None
    try:
        log_dir = os.path.dirname(log_file_path)
        if log_dir and not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        log_handle = open(log_file_path, "w", encoding="utf-8")
        tee_context = {
            "stdout": sys.stdout,
            "stderr": sys.stderr,
            "log_handle": log_handle,
        }
        sys.stdout = TeeStream(sys.stdout, log_handle)
        sys.stderr = TeeStream(sys.stderr, log_handle)
        return tee_context
    except Exception as exception:
        print("[WARNING] - (worker) - Unable to create worker log file: {0}".format(exception))
        return None


def close_tee_log(tee_context):
    """Restores stdout/stderr after tee logging.

    Args:
        tee_context (dict): Tee context returned by install_tee_log.
    """
    if not tee_context:
        return
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass
    sys.stdout = tee_context.get("stdout") or sys.stdout
    sys.stderr = tee_context.get("stderr") or sys.stderr
    log_handle = tee_context.get("log_handle")
    if log_handle:
        log_handle.close()


def print_running_task_flag(args, task, file_name=""):
    """Prints a concise running-task tracker update when requested.

    Args:
        args (argparse.Namespace): Worker command-line arguments.
        task (BatchTask): Task beginning execution.
        file_name (str, optional): File name assigned to the job.
    """
    if not getattr(args, "flag_running_tasks", False):
        return
    task_index = get_positive_tracker_index(getattr(args, "current_task_index", 1))
    total_tasks = get_positive_tracker_index(getattr(args, "total_tasks", 1))
    job_index = get_positive_tracker_index(getattr(args, "worker_id", 1))
    total_jobs = get_positive_tracker_index(getattr(args, "total_jobs", 1))
    print(
        "     ∟ ⚙️ RUNNING: ({0}) '{1}' "
        "(Task {2}/{3} | Job {4}/{5})".format(
            task.display_name,
            file_name or os.path.basename(args.source_file),
            task_index,
            total_tasks,
            job_index,
            total_jobs,
        ),
        flush=True,
    )


def print_skipped_task_flag(args, task, exception, file_name=""):
    """Prints an explicit skipped-task warning when requested.

    Args:
        args (argparse.Namespace): Worker command-line arguments.
        task (BatchTask): Task that skipped work.
        exception (TaskSkip): Skip exception.
        file_name (str, optional): File name that skipped.
    """
    if not getattr(args, "flag_skipped_tasks", False):
        return
    job_index = get_positive_tracker_index(getattr(args, "worker_id", 1))
    total_jobs = get_positive_tracker_index(getattr(args, "total_jobs", 1))
    task_index = get_positive_tracker_index(getattr(args, "current_task_index", 1))
    total_tasks = get_positive_tracker_index(getattr(args, "total_tasks", 1))
    print(
        "     ∟ ⏩ SKIPPING: ({0}) '{1}' "
        "(Task {2}/{3} | Job {4}/{5})".format(
            task.display_name,
            file_name or os.path.basename(args.source_file),
            task_index,
            total_tasks,
            job_index,
            total_jobs,
        ),
        flush=True,
    )


def get_positive_tracker_index(value, fallback=1):
    """Gets a positive numeric tracker index with a safe fallback.

    Args:
        value (object): Requested tracker index.
        fallback (int, optional): Value used when conversion fails.

    Returns:
        int: Positive tracker index.
    """
    try:
        return max(1, int(value or fallback))
    except (TypeError, ValueError):
        return max(1, int(fallback or 1))


def append_skipped_output_items(output_items, exception, work_item=None):
    """Appends pass-through output items from a skipped task.

    Args:
        output_items (list): Collected output items for this task.
        exception (TaskSkip): Skip exception carrying optional output data.
        work_item (WorkItem, optional): Current work item used as fallback.
    """
    from gt.tools.batch_processor import batch_processor_tasks as tasks

    if exception.work_item:
        if isinstance(exception.work_item, list):
            output_items.extend(exception.work_item)
        else:
            output_items.append(exception.work_item)
    elif exception.output_path:
        metadata = dict(work_item.metadata) if work_item else {}
        source_path = work_item.source_path if work_item else exception.output_path
        output_items.append(
            tasks.WorkItem(
                source_path=source_path,
                current_path=exception.output_path,
                metadata=metadata,
            )
        )
    elif work_item:
        output_items.append(work_item)


def hold_worker_window(seconds):
    """Keeps a visible worker console open for a short period.

    Args:
        seconds (float): Seconds to hold the process open.
    """
    try:
        seconds = float(seconds or 0)
    except (TypeError, ValueError):
        seconds = 0
    if seconds <= 0:
        return
    print("[INFO] - (worker) - Closing worker window in {0:g} seconds...".format(seconds))
    time.sleep(seconds)


def ensure_directory(directory_path):
    """Creates a directory while tolerating concurrent worker creation.

    Args:
        directory_path (str): Directory path to create.
    """
    if os.path.isdir(directory_path):
        return
    try:
        os.makedirs(directory_path)
    except OSError:
        if not os.path.isdir(directory_path):
            raise


def discover_final_task_work_items(project, task, batch_processor_worker, tasks):
    """Discovers complete source-folder work items for a deferred final task.

    Args:
        project (BatchProcessorModel): Active project model.
        task (BatchTask): Deferred task to execute.
        batch_processor_worker (module): Worker helpers used to resolve the source root.
        tasks (module): Batch task module providing WorkItem.

    Returns:
        list: Work items discovered from the task's configured source path.
    """
    task_index = project.get_task_environment_index(task)
    source_files = task.discover_source_files(project=project, task_index=task_index)
    source_root = batch_processor_worker.get_task_source_root(
        project=project,
        task=task,
        task_index=task_index,
    )
    return [tasks.WorkItem(source_path=source_file, source_root=source_root) for source_file in source_files]


def get_global_item_index(worker_id):
    """Gets a one-based global item index from a worker id.

    Args:
        worker_id (str): Worker identifier from the tracker.

    Returns:
        int: One-based item index.
    """
    try:
        return max(1, int(worker_id))
    except (TypeError, ValueError):
        return 1


if __name__ == "__main__":
    main()
