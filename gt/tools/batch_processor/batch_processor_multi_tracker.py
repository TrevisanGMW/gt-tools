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
    parser.add_argument("--worker-count", type=int, default=1, help="Requested worker count.")
    parser.add_argument("--logs-dir", default="", help="Directory used for worker logs.")
    parser.add_argument("--maya-version-warning", default="", help="Optional Maya version fallback warning.")
    parser.add_argument("--no-log", action="store_true", help="Disable worker log files.")
    parser.add_argument("--verbose-worker-updates", action="store_true", help="Print worker details in this tracker.")
    parser.add_argument("--flag-skipped-tasks", action="store_true", help="Print skipped-task warnings in this tracker.")
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
    print("Skipped task warnings: {0}".format("enabled" if args.flag_skipped_tasks else "disabled"))
    if args.run_from_task_id:
        print("Run from task id: {0}".format(args.run_from_task_id))
    if args.run_to_task_id:
        print("Run to task id: {0}".format(args.run_to_task_id))
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
    worker_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch_processor_multi_worker.py")
    logs_dir = args.logs_dir
    if logs_dir and not args.no_log and not os.path.isdir(logs_dir):
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
    print("--------------------------------------------")
    while job_queue or running_processes:
        for process_data in list(running_processes):
            process, source_file, log_handle, log_path = process_data
            return_code = process.poll()
            if return_code is None:
                continue
            if log_handle:
                log_handle.close()
            jobs_done += 1
            file_name = os.path.basename(source_file)
            if args.flag_skipped_tasks and log_path and not args.verbose_worker_updates:
                print_skipped_task_flags_from_log(log_path=log_path, file_name=file_name)
            if return_code == 0:
                print("--- ✅ DONE: '{0}' (Job {1}/{2}) ---".format(file_name, jobs_done, total_jobs))
            else:
                jobs_failed += 1
                print("--- ❌ FAILED: '{0}' (Job {1}/{2}) ---".format(file_name, jobs_done, total_jobs))
            running_processes.remove(process_data)

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
            log_handle = None
            log_path = None
            stdout_target = None
            stderr_target = None
            if args.flag_skipped_tasks:
                command.append("--flag-skipped-tasks")
            if not args.no_log and logs_dir:
                log_path = os.path.join(logs_dir, "{0}.log".format(os.path.splitext(file_name)[0]))
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

    print("--------------------------------------------")
    print("All jobs complete.")
    print("Total jobs: {0}".format(total_jobs))
    print("Failed jobs: {0}".format(jobs_failed))
    return jobs_failed


def print_skipped_task_flags_from_log(log_path, file_name):
    """Prints skipped-task warnings collected from a worker log.

    Args:
        log_path (str): Worker log path.
        file_name (str): Display file name.
    """
    if not log_path or not os.path.isfile(log_path):
        return
    messages = []
    try:
        with open(log_path, "r", encoding="utf-8") as log_file:
            for line in log_file:
                if "SKIPPING:" in line:
                    messages.append(line.strip())
    except Exception:
        return
    if not messages:
        return
    for message in messages:
        print(message)


if __name__ == "__main__":
    main()
