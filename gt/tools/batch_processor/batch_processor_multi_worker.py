"""
Batch Processor Multi-Instance Worker
"""

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
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)


def parse_args():
    """Parses command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="GT Batch Processor Worker")
    parser.add_argument("--project-file", required=True, help="Path to a .batch project snapshot.")
    parser.add_argument("--source-file", required=True, help="Source file assigned to this worker.")
    parser.add_argument("--run-from-task-id", default="", help="Optional task id to start from.")
    parser.add_argument("--run-to-task-id", default="", help="Optional task id to stop after.")
    parser.add_argument("--worker-id", default="", help="Worker identifier for logs.")
    parser.add_argument("--total-jobs", default="1", help="Total job count for tracker messages.")
    parser.add_argument("--log-file", default="", help="Optional log file used while stdout remains visible.")
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

    print("[OPERATION] - (worker) - Starting worker {0}".format(args.worker_id or ""))
    print("[INFO] - (worker) - Source file: {0}".format(args.source_file))
    project = batch_processor_model.BatchProcessorModel.from_file(args.project_file)
    runner = batch_processor_worker.SingleInstanceBatchRunner()
    process_tasks = runner._trim_tasks(
        project.get_enabled_tasks(),
        args.run_from_task_id or None,
        args.run_to_task_id or None,
    )
    executable_tasks = [task for task in process_tasks if not task.is_input_task]
    total_task_count = len(executable_tasks)
    current_items = [
        batch_processor_worker.create_initial_work_item(
            project=project,
            source_file=args.source_file,
            run_from_task_id=args.run_from_task_id or None,
        )
    ]
    failed = False
    skipped = 0
    succeeded = 0
    global_item_index = get_global_item_index(args.worker_id)

    try:
        for task_index, task in enumerate(executable_tasks, 1):
            remaining_tasks = max(0, total_task_count - task_index)
            task_environment_index = project.get_task_environment_index(task, enabled_only=True)
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
            output_items = []
            task_succeeded = 0
            task_skipped = 0
            if not task.modifies_in_place():
                ensure_directory(step_output_dir)
            if getattr(task, "is_aggregate_task", False):
                context = {
                    "item_index": global_item_index,
                    "total_items": len(current_items),
                    "work_items": list(current_items),
                    "worker_id": args.worker_id,
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
                except tasks.TaskSkip as exception:
                    skipped += 1
                    task_skipped += 1
                    append_skipped_output_items(output_items=output_items, exception=exception)
                    print("[SKIPPED] - ({0}) - {1}".format(task.task_type, exception))
                    print_skipped_task_flag(args, task, exception, file_name=os.path.basename(args.source_file))
            else:
                for index, work_item in enumerate(current_items, 1):
                    context = {
                        "item_index": global_item_index + index - 1,
                        "total_items": len(current_items),
                        "work_items": list(current_items),
                        "worker_id": args.worker_id,
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
                        print_skipped_task_flag(args, task, exception, file_name=os.path.basename(work_item.current_path))
            print(
                "[INFO] - ({0}) - Task {1}/{2} finished. Processed: {3}. Skipped: {4}.".format(
                    task.task_type,
                    task_index,
                    total_task_count,
                    task_succeeded + task_skipped,
                    task_skipped,
                )
            )
            current_items = output_items
            if not current_items:
                print("[SKIPPED] - ({0}) - No output items remained after this task.".format(task.task_type))
                break
    except Exception as exception:
        failed = True
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
    try:
        job_index = max(1, int(args.worker_id or 1))
    except (TypeError, ValueError):
        job_index = 1
    try:
        total_jobs = max(1, int(args.total_jobs or 1))
    except (TypeError, ValueError):
        total_jobs = 1
    print(
        "--- ⏩ SKIPPING: ({0}) '{1}' (Job {2}/{3}) ---".format(
            task.display_name,
            file_name or os.path.basename(args.source_file),
            job_index,
            total_jobs,
        ),
        flush=True,
    )


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
