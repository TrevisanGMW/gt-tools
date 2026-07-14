"""
Batch Processor Multi-Instance Tracker Console
"""

import argparse
import json
import os
import subprocess
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
    parser = argparse.ArgumentParser(description="Batch Processor Tracker")
    parser.add_argument("--project-file", required=True, help="Path to a .batch project snapshot.")
    parser.add_argument("--job-file", required=True, help="Text file containing source files to process.")
    parser.add_argument("--mayapy", required=True, help="Path to mayapy executable.")
    parser.add_argument("--run-from-task-id", default="", help="Optional task id to start from.")
    parser.add_argument("--run-to-task-id", default="", help="Optional task id to stop after.")
    parser.add_argument(
        "--final-task-id",
        action="append",
        default=[],
        help="Task id to run once after every regular job succeeds.",
    )
    parser.add_argument("--worker-count", type=int, default=1, help="Requested worker count.")
    parser.add_argument("--logs-dir", default="", help="Directory used for worker logs.")
    parser.add_argument("--maya-version-warning", default="", help="Optional Maya version fallback warning.")
    parser.add_argument("--no-log", action="store_true", help="Disable worker log files.")
    parser.add_argument(
        "--task-time-logs",
        action="store_true",
        help="Write separate per-job task timing logs.",
    )
    parser.add_argument(
        "--verbose-worker-updates",
        action="store_true",
        help="Print worker details in this tracker.",
    )
    parser.add_argument(
        "--flag-running-tasks",
        action="store_true",
        help="Print running-task updates in this tracker.",
    )
    parser.add_argument(
        "--flag-skipped-tasks",
        action="store_true",
        help="Print skipped-task warnings in this tracker.",
    )
    parser.add_argument("--show-worker-windows", action="store_true", help=argparse.SUPPRESS)
    return parser.parse_args()


def main():
    """Runs the tracker console."""
    configure_utf8_output()
    add_package_root_to_sys_path()
    args = parse_args()
    project_info = get_project_info(args.project_file)

    print("================================================")
    print("--- BATCH PROCESSOR TRACKER ---")
    print("================================================")
    print("Project: {0}".format(project_info.get("name")))
    print("Location: {0}".format(project_info.get("location")))
    print("Requested worker count: {0}".format(args.worker_count))
    if args.maya_version_warning:
        print("[WARNING] - (maya) - {0}".format(args.maya_version_warning))
    verbose_worker_updates = bool(args.verbose_worker_updates or args.show_worker_windows)
    args.verbose_worker_updates = verbose_worker_updates
    print("Verbose worker updates: {0}".format("enabled" if verbose_worker_updates else "disabled"))
    print("Running task updates: {0}".format("enabled" if args.flag_running_tasks else "disabled"))
    print("Skipped task warnings: {0}".format("enabled" if args.flag_skipped_tasks else "disabled"))
    if args.run_from_task_id:
        print("Run from task id: {0}".format(args.run_from_task_id))
    if args.run_to_task_id:
        print("Run to task id: {0}".format(args.run_to_task_id))
    if args.final_task_id:
        print(f"Final run-once tasks: {len(args.final_task_id)}")
    print("Logging: {0}".format("disabled" if args.no_log else "enabled"))
    print("--------------------------------------------")

    try:
        job_queue = read_job_file(args.job_file)
        failed_jobs = run_tracker(job_queue=job_queue, args=args)
    except Exception as exception:
        print("Batch tracker failed: {0}".format(exception))
        traceback.print_exc()
        failed_jobs = 1
    print("--------------------------------------------")
    print("Press ENTER to close this window...")
    try:
        input()
    except EOFError:
        pass
    if failed_jobs:
        sys.exit(1)


def read_job_file(job_file_path):
    """Reads source files from a job queue file.

    Args:
        job_file_path (str): Text file path.

    Returns:
        list: Source file paths.
    """
    with open(job_file_path, "r", encoding="utf-8") as job_file:
        return [line.strip() for line in job_file.readlines() if line.strip()]


def get_project_info(project_file_path):
    """Gets tracker display data from a project file.

    Args:
        project_file_path (str): Batch project file.

    Returns:
        dict: Project name and location.
    """
    fallback_name = os.path.splitext(os.path.basename(project_file_path))[0]
    fallback_location = os.path.dirname(os.path.abspath(project_file_path))
    try:
        with open(project_file_path, "r", encoding="utf-8") as project_file:
            data = json.load(project_file)
        project_name = data.get("project_name") or fallback_name
        environment_variables = data.get("environment_variables") or {}
        project_dir = environment_variables.get("project-dir") or fallback_location
        return {"name": project_name, "location": os.path.normpath(project_dir)}
    except Exception:
        return {"name": fallback_name, "location": fallback_location}


def run_tracker(job_queue, args):
    """Runs the tracker loop that owns worker processes.

    Args:
        job_queue (list): Source files to process.
        args (argparse.Namespace): Parsed arguments.
    """
    worker_count = max(1, int(args.worker_count or 1))
    args.verbose_worker_updates = bool(
        getattr(args, "verbose_worker_updates", False) or getattr(args, "show_worker_windows", False)
    )
    total_jobs = len(job_queue)
    jobs_started = 0
    jobs_done = 0
    jobs_failed = 0
    running_processes = []
    feedback_offsets = {}
    final_task_ids = list(getattr(args, "final_task_id", None) or [])
    worker_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch_processor_multi_worker.py")
    logs_dir = args.logs_dir
    if logs_dir and (not args.no_log or args.task_time_logs) and not os.path.isdir(logs_dir):
        os.makedirs(logs_dir)

    startupinfo = None
    if sys.platform == "win32":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 7

    print("Managing {0} jobs.".format(total_jobs))
    print("Max concurrent workers: {0}".format(worker_count))
    if args.verbose_worker_updates:
        print("Worker task/file details will be printed in this tracker window.")
    if args.flag_skipped_tasks:
        print("Skipped tasks will be flagged in this tracker window.")
    if args.flag_running_tasks:
        print("Running tasks will be flagged with task and job progress.")
    print("--------------------------------------------")
    while job_queue or running_processes:
        for process_data in list(running_processes):
            process, source_file, log_handle, log_path = process_data
            if log_path and not args.verbose_worker_updates:
                feedback_offsets[process.pid] = print_task_feedback_from_log(
                    log_path=log_path,
                    start_offset=feedback_offsets.get(process.pid, 0),
                    include_running=args.flag_running_tasks,
                    include_skipped=args.flag_skipped_tasks,
                )
            return_code = process.poll()
            if return_code is None:
                continue
            if log_handle:
                log_handle.close()
            jobs_done += 1
            file_name = os.path.basename(source_file)
            if return_code == 0:
                print("--- ✅ DONE: '{0}' (Job {1}/{2}) ---".format(file_name, jobs_done, total_jobs))
            else:
                jobs_failed += 1
                print("--- ❌ FAILED: '{0}' (Job {1}/{2}) ---".format(file_name, jobs_done, total_jobs))
            running_processes.remove(process_data)
            feedback_offsets.pop(process.pid, None)

        while len(running_processes) < worker_count and job_queue:
            source_file = job_queue.pop(0)
            jobs_started += 1
            file_name = os.path.basename(source_file)
            print("--- 🚀 LAUNCHING: '{0}' (Job {1}/{2}) ---".format(file_name, jobs_started, total_jobs))
            command = [
                args.mayapy,
                worker_script_path,
                "--project-file",
                args.project_file,
                "--source-file",
                source_file,
                "--worker-id",
                str(jobs_started),
                "--total-jobs",
                str(total_jobs),
            ]
            if args.run_from_task_id:
                command.extend(["--run-from-task-id", args.run_from_task_id])
            if args.run_to_task_id:
                command.extend(["--run-to-task-id", args.run_to_task_id])
            for final_task_id in final_task_ids:
                command.extend(["--skip-task-id", final_task_id])
            log_handle = None
            log_path = None
            stdout_target = None
            stderr_target = None
            if args.flag_skipped_tasks:
                command.append("--flag-skipped-tasks")
            if args.flag_running_tasks:
                command.append("--flag-running-tasks")
            if args.task_time_logs and logs_dir:
                timing_file_name = "{0}_job_{1:04d}_task_times.log".format(
                    os.path.splitext(file_name)[0],
                    jobs_started,
                )
                command.extend(["--task-time-log-file", os.path.join(logs_dir, timing_file_name)])
            if not args.no_log and logs_dir:
                log_name = "{0}_job_{1:04d}.log".format(os.path.splitext(file_name)[0], jobs_started)
                log_path = os.path.join(logs_dir, log_name)
                if args.verbose_worker_updates:
                    command.extend(["--log-file", log_path])
                else:
                    log_handle = open(log_path, "w", encoding="utf-8")
                    stdout_target = log_handle
                    stderr_target = subprocess.STDOUT
            env = dict(os.environ)
            env["PYTHONIOENCODING"] = "utf-8"
            popen_kwargs = {
                "stdout": stdout_target,
                "stderr": stderr_target,
                "startupinfo": startupinfo,
                "shell": False,
                "env": env,
            }
            process = subprocess.Popen(command, **popen_kwargs)
            running_processes.append((process, source_file, log_handle, log_path))
        time.sleep(1)

    if final_task_ids and jobs_failed:
        print("[WARNING] - Final run-once tasks were skipped because one or more regular jobs failed.")
    elif final_task_ids:
        jobs_failed += run_final_tasks(
            args=args,
            task_ids=final_task_ids,
            worker_script_path=worker_script_path,
            logs_dir=logs_dir,
            startupinfo=startupinfo,
        )

    print("--------------------------------------------")
    print("All jobs complete.")
    print("Total jobs: {0}".format(total_jobs))
    print("Failed jobs: {0}".format(jobs_failed))
    return jobs_failed


def run_final_tasks(args, task_ids, worker_script_path, logs_dir, startupinfo=None):
    """Runs deferred tasks sequentially after all regular jobs succeed.

    Args:
        args (argparse.Namespace): Tracker command-line arguments.
        task_ids (list): Task ids to execute in the final phase.
        worker_script_path (str): Multi-instance worker script path.
        logs_dir (str): Worker log directory.
        startupinfo (subprocess.STARTUPINFO, optional): Windows process startup configuration.

    Returns:
        int: Number of failed final tasks.
    """
    failed_tasks = 0
    total_tasks = len(task_ids)
    for task_index, task_id in enumerate(task_ids, 1):
        print(f"--- 📦 FINALIZING: Task {task_index}/{total_tasks} ---")
        command = [
            args.mayapy,
            worker_script_path,
            "--project-file",
            args.project_file,
            "--source-file",
            args.project_file,
            "--final-task-id",
            task_id,
            "--worker-id",
            "Final",
            "--total-jobs",
            "1",
        ]
        if args.flag_skipped_tasks:
            command.append("--flag-skipped-tasks")
        if args.flag_running_tasks:
            command.append("--flag-running-tasks")

        log_handle = None
        log_path = None
        stdout_target = None
        stderr_target = None
        if args.task_time_logs and logs_dir:
            timing_name = f"final_task_{task_index:02d}_task_times.log"
            command.extend(["--task-time-log-file", os.path.join(logs_dir, timing_name)])
        if not args.no_log and logs_dir:
            log_path = os.path.join(logs_dir, f"final_task_{task_index:02d}.log")
            if args.verbose_worker_updates:
                command.extend(["--log-file", log_path])
            else:
                log_handle = open(log_path, "w", encoding="utf-8")
                stdout_target = log_handle
                stderr_target = subprocess.STDOUT

        env = dict(os.environ)
        env["PYTHONIOENCODING"] = "utf-8"
        process = subprocess.Popen(
            command,
            stdout=stdout_target,
            stderr=stderr_target,
            startupinfo=startupinfo,
            shell=False,
            env=env,
        )
        feedback_offset = 0
        while process.poll() is None:
            if log_path and not args.verbose_worker_updates:
                feedback_offset = print_task_feedback_from_log(
                    log_path=log_path,
                    start_offset=feedback_offset,
                    include_running=args.flag_running_tasks,
                    include_skipped=args.flag_skipped_tasks,
                )
            time.sleep(1)
        if log_path and not args.verbose_worker_updates:
            print_task_feedback_from_log(
                log_path=log_path,
                start_offset=feedback_offset,
                include_running=args.flag_running_tasks,
                include_skipped=args.flag_skipped_tasks,
            )
        if log_handle:
            log_handle.close()
        if process.returncode:
            failed_tasks += 1
            print(f"--- ❌ FINAL TASK FAILED: Task {task_index}/{total_tasks} ---")
        else:
            print(f"--- ✅ FINAL TASK DONE: Task {task_index}/{total_tasks} ---")
    return failed_tasks


def print_task_feedback_from_log(
    log_path,
    start_offset=0,
    include_running=True,
    include_skipped=True,
):
    """Prints new concise task feedback collected from a worker log.

    Args:
        log_path (str): Worker log path.
        start_offset (int, optional): Stream offset previously consumed from the log.
        include_running (bool, optional): Whether running-task markers should print.
        include_skipped (bool, optional): Whether skipped-task markers should print.

    Returns:
        int: Updated stream offset for the next read.
    """
    if not log_path or not os.path.isfile(log_path):
        return int(start_offset or 0)
    messages = []
    end_offset = int(start_offset or 0)
    try:
        with open(log_path, "r", encoding="utf-8") as log_file:
            log_file.seek(end_offset)
            for line in log_file:
                is_running = include_running and "⚙️ RUNNING:" in line
                is_skipped = include_skipped and "⏩ SKIPPING:" in line
                if is_running or is_skipped:
                    messages.append(line.rstrip("\r\n"))
            end_offset = log_file.tell()
    except Exception:
        return int(start_offset or 0)
    for message in messages:
        print(message)
    return end_offset


if __name__ == "__main__":
    main()
