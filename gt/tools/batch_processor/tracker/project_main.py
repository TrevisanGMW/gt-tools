"""Isolated supervisor entry point for a nested Batch Processor project."""

import argparse
import os
import subprocess
import sys
import time
import traceback
from types import SimpleNamespace


def run_child(request):
    """Launches the saved execution mode and monitors its tracker process.

    Args:
        request (dict): Effective project and reporting manifest.
    """
    from gt.tools.batch_processor import batch_processor_projects as projects
    from gt.tools.batch_processor import batch_processor_worker
    from gt.tools.batch_processor.batch_processor_model import BatchProcessorModel
    from gt.tools.batch_processor.tracker import tracker_process_utils

    project = BatchProcessorModel.from_file(request["project_file"])
    run_dir = request["run_dir"]
    settings = request["settings"]
    options = {
        "session_dir": os.path.join(run_dir, "session"),
        "result_file": os.path.join(run_dir, "result.json"),
        "status_file": os.path.join(run_dir, "status.json"),
        "control_file": os.path.join(run_dir, "control.json"),
        "run_id": request["run_id"], "parent_run_id": request["parent_run_id"],
        "window_policy": settings["window_policy"], "empty_policy": settings["empty_policy"],
        "headless": not settings["show_tracker"],
    }
    project.run_settings["log_path"] = os.path.join(run_dir, "logs")
    projects.write_json(request["project_file"], dict(project.to_dict(), runtime_options={
        "source_project_file": request["source_project_file"]}))
    process = None
    try:
        if project.run_settings.get("multi_instance"):
            runner = batch_processor_worker.MultiInstanceBatchRunner(
                project_log_path=os.path.join(run_dir, "project.log"))
            runner.run(project, runtime_options=options)
            process = runner.process
        else:
            process = launch_single_project(project, request, options)
        cancel_started = None
        while not projects.read_json(options["result_file"]).get("finished"):
            if process.poll() is not None:
                if projects.read_json(options["result_file"]).get("finished"):
                    break
                raise RuntimeError(f"Child tracker exited ({process.returncode}) without a project result.")
            control = projects.read_json(options["control_file"])
            if control.get("action") == "cancel" and control.get("run_id") == request["run_id"]:
                cancel_started = cancel_started or time.monotonic()
                if time.monotonic() - cancel_started > 6:
                    tracker_process_utils.terminate_process_tree(process, force=True)
                    raise RuntimeError("Child project was canceled before it could finish cleanup.")
            time.sleep(0.25)
        result = projects.read_json(options["result_file"])
        should_close = options["headless"] or options["window_policy"] == "Close When Finished" or (
            options["window_policy"] == "Close On Success" and result.get("outcome") in projects.SUCCESS_OUTCOMES)
        if should_close:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                tracker_process_utils.terminate_process_tree(process, force=True)
    except Exception as error:
        if process:
            tracker_process_utils.terminate_process_tree(process, force=True)
        from gt.tools.batch_processor.tracker.tracker_project_reporter import publish_startup_failure

        publish_startup_failure(SimpleNamespace(**options, source_project_file=request["source_project_file"]), error)
        raise
    finally:
        from gt.tools.batch_processor import batch_processor_maya

        batch_processor_maya.shutdown_standalone()


def launch_single_project(project, request, options):
    """Runs a single-instance project in an isolated worker with a tracker.

    Args:
        project (BatchProcessorModel): Effective child model.
        request (dict): Launch manifest.
        options (dict): Reporting and window options.

    Returns:
        subprocess.Popen: Owned tracker process.
    """
    run_dir = request["run_dir"]
    job_file = os.path.join(run_dir, "jobs.txt")
    with open(job_file, "w", encoding="utf-8") as stream:
        stream.write(request["project_file"] + "\n")
    command = [sys.executable, os.path.join(os.path.dirname(__file__), "tracker_main.py"),
               "--project-file", request["project_file"], "--job-file", job_file,
               "--source-project-file", request["source_project_file"], "--mayapy", sys.executable,
               "--worker-count", "1", "--single-project", "--project-log", os.path.join(run_dir, "project.log")]
    for key, value in options.items():
        if key == "headless":
            if value:
                command.append("--headless")
        else:
            command.extend([f"--{key.replace('_', '-')}", str(value)])
    return subprocess.Popen(command, stdin=subprocess.DEVNULL, shell=False,
                            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)


def main():
    """Loads one request and runs its child project in a clean process."""
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
    sys.path.insert(0, package_root)
    from gt.tools.batch_processor import batch_processor_projects as projects
    from gt.tools.batch_processor.tracker.tracker_project_reporter import publish_startup_failure

    parser = argparse.ArgumentParser(description="Nested Batch Processor supervisor")
    parser.add_argument("--request-file", required=True)
    args = parser.parse_args()
    request = projects.read_json(args.request_file)
    try:
        run_child(request)
    except Exception as error:
        traceback.print_exc()
        publish_startup_failure(SimpleNamespace(
            result_file=os.path.join(request["run_dir"], "result.json"),
            run_id=request["run_id"], parent_run_id=request["parent_run_id"],
            source_project_file=request["source_project_file"]), error)
        sys.exit(1)


if __name__ == "__main__":
    main()
