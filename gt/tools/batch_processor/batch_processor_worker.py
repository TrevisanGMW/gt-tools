"""
Batch Processor Worker

Runner and launcher services used by the batch processor.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_tasks as tasks
from gt.tools.batch_processor import batch_processor_tracker
import json
import logging
import os
import subprocess
import sys
import tempfile
import time

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SingleInstanceBatchRunner:
    """Runs enabled tasks in one Python process."""

    def __init__(self, tracker=None, flag_skipped_tasks=False, task_time_log_path=None):
        """Initializes a single-instance runner.

        Args:
            tracker (BatchProgressTracker, optional): Tracker to update during the run.
            flag_skipped_tasks (bool, optional): Whether skipped tasks should emit tracker warnings.
            task_time_log_path (str, optional): Separate file used to record task durations.
        """
        self.tracker = tracker or batch_processor_tracker.BatchProgressTracker()
        self.flag_skipped_tasks = bool(flag_skipped_tasks)
        self.task_time_log_path = task_time_log_path

    def run(self, project, run_from_task_id=None, run_from_module_id=None, run_to_task_id=None):
        """Runs a project through enabled tasks.

        Args:
            project (BatchProcessorModel): Project to run.
            run_from_task_id (str, optional): Task id to start from.
            run_from_module_id (str, optional): Legacy task id alias.
            run_to_task_id (str, optional): Optional last task id to run.

        Returns:
            BatchProgressTracker: Tracker containing final run state.
        """
        if run_from_task_id is None:
            run_from_task_id = run_from_module_id
        process_tasks = self._trim_tasks(project.get_enabled_tasks(), run_from_task_id, run_to_task_id)
        validation = project.validate_project(task_list=process_tasks)
        if validation.errors:
            raise RuntimeError("Project validation failed: {0}".format("; ".join(validation.errors)))

        discovered_files = self._get_initial_source_files(project, process_tasks)
        worker_count = int(project.run_settings.get("worker_count") or 1)
        self.tracker.start_run(
            project_name=project.project_name,
            total_steps=len(process_tasks),
            total_files=len(discovered_files),
            active_workers=worker_count,
            run_mode="single-instance",
        )
        active_task = None
        active_task_index = 0
        active_task_started = None
        task_timing_recorded = True
        try:
            current_items = []
            for step_index, task in enumerate(process_tasks, 1):
                active_task = task
                active_task_index = step_index
                active_task_started = time.perf_counter()
                task_timing_recorded = False
                failures_before = self.tracker.failed
                skipped_before = self.tracker.skipped
                task_environment_index = project.get_task_environment_index(task)
                self.tracker.start_step(step_index, task.display_name)
                self._record_operation(task)
                if task.is_input_task:
                    new_items = task.prepare(project, context={"task_index": task_environment_index})
                    if task.starts_new_input_list():
                        current_items = list(new_items)
                        self.tracker.record_message(
                            'Input task "{0}" started a new input list with {1} file(s).'.format(
                                task.display_name, len(new_items)
                            )
                        )
                    else:
                        current_items.extend(new_items)
                        self.tracker.record_message(
                            'Input task "{0}" discovered {1} file(s).'.format(task.display_name, len(new_items))
                        )
                    self._record_task_timing(
                        task=task,
                        task_index=step_index,
                        total_tasks=len(process_tasks),
                        started_at=active_task_started,
                        status=constants.RunStatus.SUCCEEDED,
                    )
                    task_timing_recorded = True
                    continue

                current_items = self._get_task_source_items(
                    project=project,
                    task=task,
                    task_index=task_environment_index,
                    current_items=current_items,
                )
                if not current_items and not getattr(task, "is_aggregate_task", False):
                    source_path = task.resolve_source_path(project, task_index=task_environment_index)
                    raise RuntimeError(
                        'No source files found for task "{0}" using source path: {1}'.format(
                            task.display_name, source_path
                        )
                    )
                step_output_dir = self._get_step_output_dir(project, task_environment_index, task)
                validation = task.validate_work_items(current_items, project, step_output_dir)
                if validation.errors:
                    raise RuntimeError("; ".join(validation.errors))
                for warning in validation.warnings:
                    self.tracker.record_warning()
                    self.tracker.record_message("[WARNING] - ({0}) - {1}".format(task.task_type, warning))
                current_items = self._run_task(project, task, current_items, step_output_dir)
                task_status = constants.RunStatus.SUCCEEDED
                if self.tracker.failed > failures_before:
                    task_status = constants.RunStatus.FAILED
                elif self.tracker.skipped > skipped_before:
                    task_status = constants.RunStatus.SKIPPED
                self._record_task_timing(
                    task=task,
                    task_index=step_index,
                    total_tasks=len(process_tasks),
                    started_at=active_task_started,
                    status=task_status,
                )
                task_timing_recorded = True
            self.tracker.finish(failed=self.tracker.failed > 0)
            return self.tracker
        except Exception:
            if active_task and active_task_started is not None and not task_timing_recorded:
                self._record_task_timing(
                    task=active_task,
                    task_index=active_task_index,
                    total_tasks=len(process_tasks),
                    started_at=active_task_started,
                    status=constants.RunStatus.FAILED,
                )
            self.tracker.finish(failed=True)
            raise

    def _record_task_timing(self, task, task_index, total_tasks, started_at, status):
        """Appends timing information for one task when timing logs are enabled.

        Args:
            task (BatchTask): Task that finished executing.
            task_index (int): One-based task index.
            total_tasks (int): Total tasks in this run.
            started_at (float): Performance-counter value captured before execution.
            status (str): Task completion status.
        """
        if not self.task_time_log_path:
            return
        duration_seconds = max(0.0, time.perf_counter() - started_at)
        append_task_timing_log(
            log_file_path=self.task_time_log_path,
            task=task,
            task_index=task_index,
            total_tasks=total_tasks,
            duration_seconds=duration_seconds,
            status=status,
        )

    def _trim_tasks(self, process_tasks, run_from_task_id, run_to_task_id=None):
        """Trims tasks when running from a selected step.

        Args:
            process_tasks (list): Enabled processing tasks.
            run_from_task_id (str): Optional task id to start from.
            run_to_task_id (str, optional): Optional last task id to run.

        Returns:
            list: Tasks to execute.
        """
        start_index = 0
        end_index = len(process_tasks)
        for index, task in enumerate(process_tasks):
            if task.id == run_from_task_id:
                start_index = index
            if run_to_task_id and task.id == run_to_task_id:
                end_index = index + 1
        return process_tasks[start_index:end_index]

    def _get_step_output_dir(self, project, step_index, task):
        """Gets the cooked output directory for a task.

        Args:
            project (BatchProcessorModel): Active project model.
            step_index (int): One-based step index.
            task (BatchTask): Task being executed.

        Returns:
            str: Cooked output directory path.
        """
        return task.resolve_task_path(project, task_index=step_index)

    def _get_initial_source_files(self, project, process_tasks):
        """Gets the source files used for the initial tracker file count.

        Args:
            project (BatchProcessorModel): Active project model.
            process_tasks (list): Tasks selected for the run.

        Returns:
            list: Source file paths used to seed the run.
        """
        for task in process_tasks:
            if task.is_input_task:
                continue
            if task.uses_incoming_files():
                return project.discover_input_files()
            if task.source_uses_previous_task_path():
                return project.discover_input_files()
            task_index = project.get_task_environment_index(task)
            return task.discover_source_files(project=project, task_index=task_index)
        return project.discover_input_files()

    def _get_task_source_items(self, project, task, task_index, current_items):
        """Gets work items for the task, honoring explicit source paths.

        Args:
            project (BatchProcessorModel): Active project model.
            task (BatchTask): Task being executed.
            task_index (int): One-based task environment index.
            current_items (list): Work items produced by the previous task.

        Returns:
            list: Work items to feed into this task.
        """
        if task.uses_incoming_files() and current_items:
            return current_items
        if task.uses_incoming_files():
            input_items = project.discover_input_work_items()
            self.tracker.record_message(
                'Task "{0}" loaded {1} incoming input file(s).'.format(task.display_name, len(input_items))
            )
            return input_items
        source_files = task.discover_source_files(project=project, task_index=task_index)
        if not source_files:
            if current_items and task.source_uses_previous_task_path():
                self.tracker.record_message(
                    (
                        'Task "{0}" found no files at its source path and will use '
                        "{1} incoming item(s)."
                    ).format(task.display_name, len(current_items))
                )
                return current_items
            return []
        self.tracker.record_message(
            'Task "{0}" loaded {1} source file(s) from: {2}'.format(
                task.display_name,
                len(source_files),
                task.resolve_source_path(project, task_index=task_index),
            )
        )
        source_root = get_task_source_root(project=project, task=task, task_index=task_index)
        return [tasks.WorkItem(source_path=file_path, source_root=source_root) for file_path in source_files]

    def _record_operation(self, task):
        """Records a task operation message.

        Args:
            task (BatchTask): Task being executed.
        """
        self.tracker.record_message("[OPERATION] - ({0}) - {1}".format(task.task_type, task.display_name))

    def _run_task(self, project, task, work_items, step_output_dir):
        """Runs one task for all work items.

        Args:
            project (BatchProcessorModel): Active project model.
            task (BatchTask): Task being executed.
            work_items (list): Work items entering the task.
            step_output_dir (str): Cooked output directory path.

        Returns:
            list: Work items that completed this task.
        """
        output_items = []
        if task.writes_to_target_path() and not os.path.isdir(step_output_dir):
            os.makedirs(step_output_dir)
        if getattr(task, "is_aggregate_task", False):
            context = {
                "item_index": 1,
                "total_items": len(work_items),
                "work_items": list(work_items),
            }
            self.tracker.record_message(
                "[INFO] - ({0}) - Processing aggregate task with {1} incoming file(s).".format(
                    task.task_type, len(work_items)
                )
            )
            try:
                output_item = task.execute(None, project, step_output_dir, context=context)
                if isinstance(output_item, list):
                    output_items.extend(output_item)
                elif output_item:
                    output_items.append(output_item)
                self.tracker.record_success()
            except tasks.TaskSkip as exception:
                self._append_skipped_output_items(output_items=output_items, exception=exception)
                self._record_skipped_task_flag(
                    task=task,
                    exception=exception,
                    file_name=task.display_name,
                    job_index=1,
                    total_jobs=1,
                )
                self.tracker.record_skipped()
                self.tracker.record_message("[SKIPPED] - ({0}) - {1}".format(task.task_type, exception))
            except Exception as exception:
                logger.warning("Failed processing aggregate task %s: %s", task.display_name, exception)
                self.tracker.record_failure()
                self.tracker.record_message("[ERROR] - ({0}) - {1}".format(task.task_type, exception))
            return output_items
        for index, work_item in enumerate(work_items, 1):
            self.tracker.start_file(work_item.current_path)
            context = {"item_index": index, "total_items": len(work_items), "work_items": list(work_items)}
            self.tracker.record_message(
                "[INFO] - ({0}) - Processing {1}/{2}: {3}".format(
                    task.task_type, index, len(work_items), work_item.current_path
                )
            )
            try:
                output_item = task.execute(work_item, project, step_output_dir, context=context)
                if isinstance(output_item, list):
                    output_items.extend(output_item)
                elif output_item:
                    output_items.append(output_item)
                self.tracker.record_success()
            except tasks.TaskSkip as exception:
                self._append_skipped_output_items(
                    output_items=output_items,
                    exception=exception,
                    work_item=work_item,
                )
                self._record_skipped_task_flag(
                    task=task,
                    exception=exception,
                    file_name=os.path.basename(work_item.current_path),
                    job_index=index,
                    total_jobs=len(work_items),
                )
                self.tracker.record_skipped()
                self.tracker.record_message("[SKIPPED] - ({0}) - {1}".format(task.task_type, exception))
            except Exception as exception:
                logger.warning("Failed processing %s: %s", work_item.current_path, exception)
                self.tracker.record_failure()
                self.tracker.record_message("[ERROR] - ({0}) - {1}".format(task.task_type, exception))
        return output_items

    @staticmethod
    def _append_skipped_output_items(output_items, exception, work_item=None):
        """Appends pass-through output items from a skipped task.

        Args:
            output_items (list): Collected output items for this task.
            exception (TaskSkip): Skip exception carrying optional output data.
            work_item (WorkItem, optional): Current work item used as fallback.
        """
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

    def _record_skipped_task_flag(self, task, exception, file_name="", job_index=1, total_jobs=1):
        """Records an explicit skipped-task warning when enabled.

        Args:
            task (BatchTask): Task that skipped work.
            exception (TaskSkip): Skip exception.
            file_name (str, optional): File name that skipped.
            job_index (int, optional): One-based job index.
            total_jobs (int, optional): Total job count.
        """
        if not self.flag_skipped_tasks:
            return
        self.tracker.record_message(
            "    --- ⏩ SKIPPING TASK: ({0}) '{1}' (Job {2}/{3}) ---".format(
                task.display_name,
                file_name or task.display_name,
                int(job_index or 1),
                int(total_jobs or 1),
            )
        )


class MultiInstanceBatchRunner:
    """Launches an independent Qt tracker for multi-instance processing."""

    def __init__(
        self,
        tracker=None,
        verbose_tracker_updates=False,
        show_worker_windows=False,
        flag_skipped_tasks=False,
        flag_running_tasks=True,
        project_log_path=None,
    ):
        """Initializes a multi-instance launcher.

        Args:
            tracker (BatchProgressTracker, optional): Tracker to update with launch state.
            verbose_tracker_updates (bool, optional): Whether workers should print details to the tracker.
            show_worker_windows (bool, optional): Legacy alias for verbose tracker updates.
            flag_skipped_tasks (bool, optional): Whether skipped tasks should be printed in the tracker.
            flag_running_tasks (bool, optional): Whether running tasks should be printed in the tracker.
            project_log_path (str, optional): Main project log shown by the standalone tracker.
        """
        self.tracker = tracker or batch_processor_tracker.BatchProgressTracker()
        self.verbose_tracker_updates = bool(verbose_tracker_updates or show_worker_windows)
        self.flag_skipped_tasks = bool(flag_skipped_tasks)
        self.flag_running_tasks = bool(flag_running_tasks)
        self.project_log_path = project_log_path

    def run(self, project, run_from_task_id=None, run_from_module_id=None, run_to_task_id=None):
        """Launches the tracker console for a project.

        Args:
            project (BatchProcessorModel): Project to run.
            run_from_task_id (str, optional): Task id to start from.
            run_from_module_id (str, optional): Legacy task id alias.
            run_to_task_id (str, optional): Optional last task id to run.

        Returns:
            BatchProgressTracker: Tracker containing launch state.
        """
        if run_from_task_id is None:
            run_from_task_id = run_from_module_id
        task_trimmer = SingleInstanceBatchRunner()
        process_tasks = task_trimmer._trim_tasks(project.get_enabled_tasks(), run_from_task_id, run_to_task_id)
        validation = project.validate_project(task_list=process_tasks)
        if validation.errors:
            raise RuntimeError("Project validation failed: {0}".format("; ".join(validation.errors)))
        final_tasks = self._get_final_multi_instance_tasks(process_tasks)
        if final_tasks:
            processing_tasks = [task for task in process_tasks if not task.is_input_task]
            trailing_tasks = processing_tasks[len(processing_tasks) - len(final_tasks) :]
            if trailing_tasks != final_tasks:
                offending_task = next(
                    (task for task in final_tasks if task not in trailing_tasks),
                    final_tasks[0],
                )
                raise RuntimeError(
                    f'Task "{offending_task.display_name}" must be the last enabled processing task '
                    'when "Run Once After All Jobs" is enabled. Run-once tasks have to be the final '
                    "enabled processing tasks, in list order."
                )

        project_snapshot_path = self._write_project_snapshot(project)
        source_files = self._get_source_files_for_multi_run(project, run_from_task_id)
        if not source_files:
            raise RuntimeError("No source files found for multi-instance run.")
        job_file_path = self._write_job_file(source_files)
        tracker_script_path = os.path.join(os.path.dirname(__file__), "tracker", "tracker_main.py")
        preferred_maya_version = project.run_settings.get("preferred_maya_version")
        mayapy_path, maya_version_warning = resolve_mayapy_executable(preferred_version=preferred_maya_version)
        worker_count = int(project.run_settings.get("worker_count") or 1)
        max_retries = max(0, int(project.run_settings.get("max_retries") or 0))
        timeout_minutes = max(0, int(project.run_settings.get("timeout_minutes") or 0))
        logs_dir = project.get_logs_dir()
        command = [
            mayapy_path,
            tracker_script_path,
            "--project-file",
            project_snapshot_path,
            "--job-file",
            job_file_path,
            "--mayapy",
            mayapy_path,
            "--worker-count",
            str(worker_count),
            "--logs-dir",
            logs_dir,
        ]
        if self.project_log_path:
            command.extend(["--project-log", self.project_log_path])
        if project.project_file_path:
            command.extend(["--source-project-file", project.project_file_path])
        if maya_version_warning:
            command.extend(["--maya-version-warning", maya_version_warning])
        if run_from_task_id:
            command.extend(["--run-from-task-id", run_from_task_id])
        if run_to_task_id:
            command.extend(["--run-to-task-id", run_to_task_id])
        for final_task in final_tasks:
            command.extend(["--final-task-id", final_task.id])
        if max_retries:
            command.extend(["--max-retries", str(max_retries)])
        if timeout_minutes:
            command.extend(["--timeout-minutes", str(timeout_minutes)])
        if not project.run_settings.get("create_log", True):
            command.append("--no-log")
        if project.run_settings.get("create_task_time_log", True):
            command.append("--task-time-logs")

        creation_flags = 0
        popen_kwargs = {}
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
        else:
            popen_kwargs["start_new_session"] = True
        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creation_flags,
            shell=False,
            env=env,
            **popen_kwargs,
        )

        self.tracker.start_run(
            project_name=project.project_name,
            total_steps=len(process_tasks),
            total_files=len(source_files),
            active_workers=worker_count,
            run_mode="multi-instance",
        )
        self.tracker.record_message("Launched standalone batch tracker: {0}".format(project_snapshot_path))
        if maya_version_warning:
            self.tracker.record_message("[WARNING] - (maya) - {0}".format(maya_version_warning))
        return self.tracker

    @staticmethod
    def _get_final_multi_instance_tasks(process_tasks):
        """Gets tasks configured to run once after regular multi-instance jobs.

        Args:
            process_tasks (list): Enabled tasks selected for the run.

        Returns:
            list: Tasks deferred to the final phase, in task order.
        """
        return [
            task
            for task in process_tasks
            if getattr(task, "supports_run_once_after_jobs", False)
            and task.settings.get("run_once_after_multi_instance", False)
        ]

    @staticmethod
    def _get_source_files_for_multi_run(project, run_from_task_id=None):
        """Gets source files for a multi-instance job queue.

        Args:
            project (BatchProcessorModel): Project to inspect.
            run_from_task_id (str, optional): Optional selected start task.

        Returns:
            list: Source file paths.
        """
        if run_from_task_id:
            task = project.get_task(run_from_task_id)
            if task and not task.is_input_task and not task.uses_incoming_files():
                task_index = project.get_task_environment_index(task)
                return task.discover_source_files(project=project, task_index=task_index)
        segments = project.get_task_segments()
        if len(segments) > 1:
            # Segmented runs fan out one segment at a time. The initial queue only
            # needs the first segment's files; later segments are discovered by the
            # tracker once earlier segments produce their outputs.
            return project.discover_segment_input_files(segments[0])
        return project.discover_input_files()

    @staticmethod
    def _write_job_file(source_files):
        """Writes source files to a temporary job queue file.

        Args:
            source_files (list): Source file paths.

        Returns:
            str: Job file path.
        """
        file_handle, job_file_path = tempfile.mkstemp(prefix="gt_batch_processor_jobs_", suffix=".txt")
        with os.fdopen(file_handle, "w", encoding="utf-8") as job_file:
            for source_file in source_files:
                job_file.write(str(source_file) + "\n")
        return job_file_path

    @staticmethod
    def _write_project_snapshot(project):
        """Writes the current project data to a temporary .batch file.

        Args:
            project (BatchProcessorModel): Project to snapshot.

        Returns:
            str: Temporary project snapshot path.
        """
        data = project.to_dict()
        environment_variables = dict(data.get("environment_variables") or {})
        environment_variables["project-dir"] = project.get_project_dir()
        data["environment_variables"] = environment_variables
        file_handle, snapshot_path = tempfile.mkstemp(prefix="gt_batch_processor_", suffix=".batch")
        with os.fdopen(file_handle, "w", encoding="utf-8") as snapshot_file:
            json.dump(data, snapshot_file, indent=4, sort_keys=True)
        return snapshot_path


def resolve_mayapy_executable(preferred_version=None):
    """Resolves the mayapy executable to use for worker processes.

    Args:
        preferred_version (str, optional): Preferred Maya version, such as 2025.

    Returns:
        tuple: mayapy executable path and warning message.
    """
    preferred_version = str(preferred_version or "").strip()
    fallback_path = find_current_mayapy_executable()
    if not preferred_version:
        return fallback_path, ""
    preferred_path = find_mayapy_for_version(preferred_version)
    if preferred_path:
        return preferred_path, ""
    warning = (
        "Preferred Maya version '{0}' was not found in default Autodesk install locations. "
        "Falling back to: {1}"
    ).format(preferred_version, fallback_path)
    return fallback_path, warning


def append_task_timing_log(log_file_path, task, task_index, total_tasks, duration_seconds, status):
    """Appends one readable task-duration entry to a dedicated timing log.

    Args:
        log_file_path (str): Timing log file path.
        task (BatchTask): Task represented by the timing entry.
        task_index (int): One-based task index.
        total_tasks (int): Total tasks executed for the job.
        duration_seconds (float): Elapsed task execution time in seconds.
        status (str): Task completion status.
    """
    if not log_file_path:
        return
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.isdir(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    create_header = not os.path.isfile(log_file_path)
    with open(log_file_path, "a", encoding="utf-8") as log_file:
        if create_header:
            log_file.write("Batch Processor Task Timing Log\n")
            log_file.write("Task | Status | Duration\n")
        log_file.write(
            f"{int(task_index)}/{int(total_tasks)} | {task.display_name} | "
            f"{status} | {float(duration_seconds):.3f} seconds\n"
        )


def create_initial_work_item(project, source_file, run_from_task_id=None):
    """Creates an initial work item with source-relative path metadata.

    Args:
        project (BatchProcessorModel): Active project model.
        source_file (str): Source file path.
        run_from_task_id (str, optional): Selected start task id.

    Returns:
        WorkItem: Work item with relative source metadata when possible.
    """
    source_root = get_initial_source_root(
        project=project,
        source_file=source_file,
        run_from_task_id=run_from_task_id,
    )
    return tasks.WorkItem(source_path=source_file, source_root=source_root)


def get_initial_source_root(project, source_file, run_from_task_id=None):
    """Gets the source root for an initial source file.

    Args:
        project (BatchProcessorModel): Active project model.
        source_file (str): Source file path.
        run_from_task_id (str, optional): Selected start task id.

    Returns:
        str: Source root path.
    """
    if project and run_from_task_id:
        task = project.get_task(run_from_task_id)
        if task and not task.is_input_task and not task.uses_incoming_files():
            task_index = project.get_task_environment_index(task)
            return get_task_source_root(project=project, task=task, task_index=task_index)
    input_root = get_input_source_root_for_file(project=project, source_file=source_file)
    if input_root:
        return input_root
    source_file = tasks.normalize_path(source_file)
    return os.path.dirname(source_file) if source_file else ""


def get_input_source_root_for_file(project, source_file):
    """Finds the input task root that contains a source file.

    Args:
        project (BatchProcessorModel): Active project model.
        source_file (str): Source file path.

    Returns:
        str: Matching input root, or an empty string.
    """
    if not project:
        return ""
    for input_task in project.get_input_tasks(enabled_only=True):
        input_dir = input_task.get_input_dir(project)
        if input_dir and tasks.path_is_inside_directory(source_file, input_dir):
            return input_dir
    return ""


def get_task_source_root(project, task, task_index=None):
    """Gets the root folder used for preserving task source relative paths.

    Args:
        project (BatchProcessorModel): Active project model.
        task (BatchTask): Task being inspected.
        task_index (int, optional): One-based task index.

    Returns:
        str: Source root path.
    """
    if not project or not task:
        return ""
    source_path = task.resolve_source_path(project=project, task_index=task_index)
    if not source_path:
        return ""
    if os.path.isfile(source_path):
        return os.path.dirname(source_path)
    return source_path


def find_mayapy_executable(preferred_version=None):
    """Finds a mayapy executable.

    Args:
        preferred_version (str, optional): Preferred Maya version.

    Returns:
        str: mayapy executable path, or the current Python executable as a fallback.
    """
    return resolve_mayapy_executable(preferred_version=preferred_version)[0]


def find_current_mayapy_executable():
    """Finds a mayapy executable near the current Python executable.

    Returns:
        str: mayapy executable path, or the current Python executable as a fallback.
    """
    current_executable = sys.executable
    executable_dir = os.path.dirname(current_executable)
    executable_name = "mayapy.exe" if sys.platform == "win32" else "mayapy"
    mayapy_path = os.path.join(executable_dir, executable_name)
    if os.path.isfile(mayapy_path):
        return mayapy_path
    return current_executable


def find_mayapy_for_version(version):
    """Finds mayapy for a specific Maya version in common install locations.

    Args:
        version (str): Maya version, such as 2025.

    Returns:
        str: mayapy path or an empty string.
    """
    for candidate in get_mayapy_version_candidates(version=version):
        if os.path.isfile(candidate):
            return candidate
    return ""


def get_mayapy_version_candidates(version):
    """Gets likely mayapy paths for a Maya version.

    Args:
        version (str): Maya version, such as 2025.

    Returns:
        list: Candidate mayapy paths.
    """
    version = str(version or "").strip()
    if not version:
        return []
    executable_name = "mayapy.exe" if sys.platform == "win32" else "mayapy"
    candidates = []
    if sys.platform == "win32":
        roots = [
            os.environ.get("PROGRAMFILES", r"C:\Program Files"),
            os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"),
        ]
        for root in roots:
            if not root:
                continue
            candidates.append(os.path.join(root, "Autodesk", "Maya{0}".format(version), "bin", executable_name))
            candidates.append(os.path.join(root, "Autodesk", "Maya {0}".format(version), "bin", executable_name))
    elif sys.platform == "darwin":
        candidates.append(
            "/Applications/Autodesk/maya{0}/Maya.app/Contents/bin/{1}".format(version, executable_name)
        )
        candidates.append(
            "/Applications/Autodesk/Maya{0}/Maya.app/Contents/bin/{1}".format(version, executable_name)
        )
    else:
        candidates.append("/usr/autodesk/maya{0}/bin/{1}".format(version, executable_name))
        candidates.append("/opt/Autodesk/Maya{0}/bin/{1}".format(version, executable_name))
    return list(dict.fromkeys([os.path.normpath(path) for path in candidates if path]))
