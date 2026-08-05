import subprocess
import traceback
import argparse
import glob
import time
import sys
import os

# --- Set up argument parsing ---
parser = argparse.ArgumentParser(description="Maya Headless Retargeter Tracker")
parser.add_argument("-mp", "--mayapy", required=True, help="Path to mayapy.exe")
parser.add_argument("-b", "--basedir", required=True, help="Base output directory")
parser.add_argument("-dj", "--definition_json", required=True, help="Path to the definition JSON file")
parser.add_argument("-w", "--workers", type=int, default=2, help="Maximum number of concurrent workers")
parser.add_argument("--no-log", action="store_true", help="Disable writing to the error log file")
parser.add_argument(
    "--skip-existing", action="store_true", help="Skip files that already exist in the output directory"
)
parser.add_argument(
    "-j", "--job-file", required=True, help="Path to a text file containing the list of source files (one per line)."
)
args = parser.parse_args()

# --- Setup ---
MAX_CONCURRENT_WORKERS = args.workers

# Updated Structure: (process, name, output_path, log_handle)
running_processes = []
jobs_done = 0
jobs_started = 0
processed_file_paths = []

job_queue = []
try:
    with open(args.job_file, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                job_queue.append(line)
except Exception as e:
    print(f"!!! CRITICAL TRACKER ERROR: Could not read job file: {args.job_file} !!!")
    print(traceback.format_exc())
    input("Press ENTER to exit...")
    sys.exit(1)

total_jobs = len(job_queue)
current_dir = os.path.dirname(__file__)
worker_script_path = os.path.join(current_dir, "multi_batch_worker.py")
logs_dir = os.path.join(args.basedir, "logs")

if not os.path.exists(args.basedir):
    os.makedirs(args.basedir)

# Only create logs directory if we are actually logging
if not args.no_log and not os.path.exists(logs_dir):
    os.makedirs(logs_dir)

startupinfo = None
if sys.platform == "win32":
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = 7

print("============================================")
print("--- RETARGET TRACKER CONSOLE INITIALIZED ---")
print("============================================")
print(f"Managing {total_jobs} jobs.")
print(f"Max concurrent workers: {MAX_CONCURRENT_WORKERS}")
print(f"Output directory: {args.basedir}")
if args.no_log:
    print("Logging: DISABLED")
else:
    print(f"Logging: ENABLED")

if args.skip_existing:
    print("Skip existing files: ENABLED")
print("--------------------------------------------")

# --- Main Manager Loop ---
try:
    while job_queue or running_processes:

        # --- 1. Check for and remove completed processes ---
        for proc_tuple in list(running_processes):
            # Unpack the full tuple
            process, name, output_path, log_handle = proc_tuple
            return_code = process.poll()

            if return_code is not None:
                # Close the log file handle immediately if it exists
                if log_handle:
                    log_handle.close()

                jobs_done += 1
                # Check for SUCCESS (code 0)
                if return_code == 0:
                    print(f"--- ✅ DONE: '{name}' (Job {jobs_done}/{total_jobs}) ---")
                    processed_file_paths.append(output_path)
                else:
                    # Any other code is a failure
                    print(f"--- ❌ FAILED: '{name}' (Job {jobs_done}/{total_jobs}) ---")
                    if not args.no_log:
                        print(f"    See log for details: {os.path.join(logs_dir, os.path.splitext(name)[0] + '.log')}")

                running_processes.remove(proc_tuple)

        # --- 2. Launch new processes if slots are free and jobs are waiting ---
        while len(running_processes) < MAX_CONCURRENT_WORKERS and job_queue:
            source_file_path = job_queue.pop(0)
            source_filename_only = os.path.basename(source_file_path)

            source_name_no_ext = os.path.splitext(source_filename_only)[0]
            output_filename = source_name_no_ext + ".ma"
            output_path = os.path.join(args.basedir, output_filename)

            if args.skip_existing and os.path.exists(output_path):
                jobs_started += 1
                jobs_done += 1
                print(f"--- ⏩ SKIPPED: '{output_filename}' (Already Exists) (Job {jobs_started}/{total_jobs}) ---")

                # Add to our list for checkout
                processed_file_paths.append(output_path)
                continue

            jobs_started += 1
            print(f"--- 🚀 LAUNCHING: '{source_filename_only}' (Job {jobs_started}/{total_jobs}) ---")

            command_list = [
                args.mayapy,
                worker_script_path,
                "-dj",
                args.definition_json,
                "-sf",
                source_file_path,
                "-b",
                args.basedir,
            ]

            if args.no_log:
                command_list.append("--no-log")

            if args.skip_existing:
                command_list.append("--skip-existing")

            # --- Configure Launch Strategy ---
            log_handle = None
            stdout_target = None
            stderr_target = None
            creation_flags = 0

            try:
                if not args.no_log:
                    # LOGGING ENABLED: Redirect output to file, suppress pop-up window
                    log_file_path = os.path.join(logs_dir, f"{source_name_no_ext}.log")
                    log_handle = open(log_file_path, "w", encoding="utf-8")
                    stdout_target = log_handle
                    stderr_target = subprocess.STDOUT
                else:
                    # LOGGING DISABLED: Restore original behavior (Pop-up Window)
                    if sys.platform == "win32":
                        creation_flags = subprocess.CREATE_NEW_CONSOLE

                process = subprocess.Popen(
                    command_list,
                    stdout=stdout_target,
                    stderr=stderr_target,
                    creationflags=creation_flags,
                    startupinfo=startupinfo,
                    shell=False,
                    env=os.environ,
                )

                # Store the log_handle so we can close it later (it will be None if no-log)
                running_processes.append((process, source_filename_only, output_path, log_handle))

            except Exception as e:
                print(f"!!! FAILED TO LAUNCH WORKER for {source_filename_only}: {e}")
                # Ensure we close the handle if launch failed but file opened
                if "log_handle" in locals() and log_handle:
                    log_handle.close()

        time.sleep(1)

except Exception as e:
    print(f"!!! TRACKER ERROR: {e} !!!")
    traceback.print_exc()

# --- All jobs are done ---
print("--------------------------------------------")
print("--- ALL JOBS COMPLETE ---")
print("--------------------------------------------")
print("You can now check your output directory.")

print("Press ENTER to close this window...")
input()
