"""Entry point for the independent Batch Processor Qt tracker."""

import argparse
import datetime
import os
import sys
import tempfile
import traceback
import uuid


def add_package_root_to_sys_path():
    """Adds the gt-tools package root for direct script execution."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
    if package_root not in sys.path:
        sys.path.insert(0, package_root)


def parse_args():
    """Parses tracker launch arguments.

    Returns:
        argparse.Namespace: Parsed options.
    """
    parser = argparse.ArgumentParser(description="Batch Processor Tracker")
    parser.add_argument("--project-file", required=True, help="Immutable .batch project snapshot.")
    parser.add_argument("--job-file", required=True, help="Text file containing source jobs.")
    parser.add_argument("--mayapy", required=True, help="mayapy executable used for workers.")
    parser.add_argument("--run-from-task-id", default="", help="Optional first task id.")
    parser.add_argument("--run-to-task-id", default="", help="Optional last task id.")
    parser.add_argument("--final-task-id", action="append", default=[], help="Deferred run-once task id.")
    parser.add_argument("--worker-count", type=int, default=1, help="Maximum concurrent workers.")
    parser.add_argument(
        "--max-retries",
        type=int,
        default=0,
        help="Times a failed job is retried at the end of the run. 0 disables retries.",
    )
    parser.add_argument(
        "--timeout-minutes",
        type=int,
        default=0,
        help="Minutes a job may run before it is automatically canceled. 0 disables the timeout.",
    )
    parser.add_argument("--logs-dir", default="", help="Base directory for run-scoped session data.")
    parser.add_argument("--project-log", default="", help="Main Batch Processor project log path.")
    parser.add_argument("--source-project-file", default="", help="Original saved Batch Processor project path.")
    parser.add_argument("--maya-version-warning", default="", help="Optional Maya resolution warning.")
    parser.add_argument("--no-log", action="store_true", help="Disable human-readable worker logs.")
    parser.add_argument("--task-time-logs", action="store_true", help="Write task timing logs.")
    return parser.parse_args()


def read_jobs(job_file_path):
    """Reads source job paths.

    Args:
        job_file_path (str): Job queue file.

    Returns:
        list: Source file paths.
    """
    with open(job_file_path, "r", encoding="utf-8") as job_file:
        return [line.strip() for line in job_file if line.strip()]


def build_task_definitions(project, args):
    """Builds regular and final tracker task definitions.

    Args:
        project (BatchProcessorModel): Snapshot project.
        args (argparse.Namespace): Tracker options.

    Returns:
        tuple: Regular and final task definition lists.
    """
    from gt.tools.batch_processor import batch_processor_worker

    runner = batch_processor_worker.SingleInstanceBatchRunner()
    selected_tasks = runner._trim_tasks(
        project.get_enabled_tasks(),
        args.run_from_task_id or None,
        args.run_to_task_id or None,
    )
    final_ids = set(args.final_task_id or [])
    regular_tasks = [task for task in selected_tasks if not task.is_input_task and task.id not in final_ids]
    final_tasks = [task for task in selected_tasks if not task.is_input_task and task.id in final_ids]
    return create_definitions(regular_tasks), create_definitions(final_tasks)


def build_segments(project, args):
    """Builds ordered input-segment descriptors for a multi-instance run.

    Args:
        project (BatchProcessorModel): Snapshot project.
        args (argparse.Namespace): Tracker options.

    Returns:
        tuple: (segments, final_definitions, final_tasks) where segments is a
            list of descriptor dictionaries in run order.
    """
    from gt.tools.batch_processor import batch_processor_worker

    runner = batch_processor_worker.SingleInstanceBatchRunner()
    selected_tasks = runner._trim_tasks(
        project.get_enabled_tasks(),
        args.run_from_task_id or None,
        args.run_to_task_id or None,
    )
    final_ids = set(args.final_task_id or [])
    final_tasks = [task for task in selected_tasks if not task.is_input_task and task.id in final_ids]
    final_definitions = create_definitions(final_tasks)
    content_tasks = [task for task in selected_tasks if task.id not in final_ids]
    segments = []
    for segment_tasks in project.get_task_segments(task_list=content_tasks):
        processing_tasks = [task for task in segment_tasks if not task.is_input_task]
        input_tasks = [task for task in segment_tasks if task.is_input_task]
        if not processing_tasks:
            continue
        segments.append(
            {
                "index": len(segments),
                "input_tasks": input_tasks,
                "processing_tasks": processing_tasks,
                "definitions": create_definitions(processing_tasks),
                "task_ids": [task.id for task in processing_tasks],
            }
        )
    return segments, final_definitions, final_tasks


def create_definitions(tasks):
    """Converts task objects to tracker definitions.

    Args:
        tasks (list): Batch task objects.

    Returns:
        list: Tracker definition dictionaries.
    """
    return [
        {
            "id": task.id,
            "number": index,
            "name": task.display_name,
            "icon": task.icon,
        }
        for index, task in enumerate(tasks, 1)
    ]


def create_session_dir(logs_dir):
    """Creates a unique run-scoped session directory.

    Args:
        logs_dir (str): Configured log root.

    Returns:
        str: Created session directory.
    """
    base_dir = logs_dir or os.path.join(tempfile.gettempdir(), "gt_batch_processor_sessions")
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    session_name = f"batch_session_{timestamp}_{uuid.uuid4().hex[:8]}"
    session_dir = os.path.join(base_dir, session_name)
    os.makedirs(session_dir, exist_ok=True)
    return session_dir


def run_tracker(args):
    """Creates and executes the standalone tracker application.

    Args:
        args (argparse.Namespace): Tracker options.

    Returns:
        int: Qt application exit code.
    """
    import gt.ui.qt_import as ui_qt
    from gt.tools.batch_processor import batch_processor_model
    from gt.tools.batch_processor.tracker import tracker_controller
    from gt.tools.batch_processor.tracker import tracker_model
    from gt.tools.batch_processor.tracker import tracker_scheduler
    from gt.tools.batch_processor.tracker import tracker_view

    project = batch_processor_model.BatchProcessorModel.from_file(args.project_file)
    segments, segmented_final_definitions, _segmented_final_tasks = build_segments(project, args)
    segmented = len(segments) > 1
    finalization_number = 10_000_000
    if segmented:
        # Segment jobs are materialized lazily by the scheduler, one phase at a
        # time, so later segments can discover files produced by earlier ones.
        jobs = []
        if segmented_final_definitions:
            jobs.append(
                tracker_model.TrackerJob(
                    job_id="finalization",
                    number=finalization_number,
                    source_file=args.project_file,
                    task_definitions=segmented_final_definitions,
                    is_finalization=True,
                )
            )
        scheduler_segments = segments
    else:
        regular_definitions, final_definitions = build_task_definitions(project, args)
        source_files = read_jobs(args.job_file)
        jobs = [
            tracker_model.TrackerJob(
                job_id=f"job-{index:04d}",
                number=index,
                source_file=source_file,
                task_definitions=regular_definitions,
            )
            for index, source_file in enumerate(source_files, 1)
        ]
        if final_definitions:
            jobs.append(
                tracker_model.TrackerJob(
                    job_id="finalization",
                    number=len(source_files) + 1,
                    source_file=args.project_file,
                    task_definitions=final_definitions,
                    is_finalization=True,
                )
            )
        scheduler_segments = None
    session = tracker_model.TrackerSession(
        project_name=project.project_name,
        project_path=project.get_project_dir(),
        worker_count=args.worker_count,
        jobs=jobs,
        session_dir=create_session_dir(args.logs_dir),
        project_log_path=args.project_log,
        source_project_file=args.source_project_file,
    )
    application = ui_qt.QtWidgets.QApplication.instance() or ui_qt.QtWidgets.QApplication(sys.argv)
    application.setApplicationName("Batch Processor Tracker")
    # Installed on the application (not on widgets) so Qt Style Sheets still
    # render while menu icons are pinned to the check-indicator size.
    application.setStyle(tracker_view.MenuIconStyle(application.style()))
    view = tracker_view.TrackerView(project_name=project.project_name)
    scheduler = tracker_scheduler.TrackerScheduler(
        session=session,
        options=args,
        project=project,
        segments=scheduler_segments,
    )
    controller = tracker_controller.TrackerController(session=session, scheduler=scheduler, view=view)
    if args.maya_version_warning:
        view.statusBar().showMessage(args.maya_version_warning)
    application.controller = controller
    return application.exec_()


def main():
    """Runs the tracker and records startup failures beside the snapshot."""
    add_package_root_to_sys_path()
    args = parse_args()
    try:
        exit_code = run_tracker(args)
    except Exception:
        crash_path = os.path.join(os.path.dirname(args.project_file), "gt_batch_tracker_crash.log")
        with open(crash_path, "w", encoding="utf-8") as crash_file:
            crash_file.write(traceback.format_exc())
        raise
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
