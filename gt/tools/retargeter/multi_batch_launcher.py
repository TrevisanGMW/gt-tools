import maya.cmds as cmds
import subprocess
import tempfile
import sys
import json
import os


def run_retarget_batch(
    definition_json_path,  # This can now be a str OR a dict
    source_files_list,
    output_dir,
    max_workers=2,
    disable_logging=False,
    skip_existing_files=True,
):
    """
    Launches the headless batch retargeting process in a separate console.

    This function is the main entry point for initiating the batch. It
    dynamically finds the necessary executables (mayapy.exe) and scripts
    (tracker/worker) and launches the tracker in a new, separate console
    window, freeing up the main Maya session.

    It then handles long file lists and dictionary-based definitions
    by serializing them to temporary files, avoiding Windows command-line
    length limits.

    Args:
        definition_json_path (str or dict):
            The core retargeter definition. This can be a string
            (a file path to an existing .json file) or a dictionary
            (a definition description). If a dict is provided,
            it will be saved to a temporary JSON file.

        source_files_list (list[str]):
            A list of full file paths to the source animations
            (e.g., .fbx, .ma) that need to be processed.

        output_dir (str):
            The folder where the final retargeted .ma files will be saved.
            This directory will also contain the error log, if enabled.

        max_workers (int, optional):
            The maximum number of `mayapy.exe` worker processes to run
            concurrently. Defaults to 2.

        disable_logging (bool, optional):
            If True, workers will not write to the `worker_error_log.txt`
            file. This is recommended for speed once you are confident
            the process works. Defaults to False.

        skip_existing_files (bool, optional):
            If True, the tracker will check for an existing output file
            and skip the job if it's found, allowing you to resume
            a failed batch. Defaults to False.

    Raises:
        (Implicitly via `cmds.error`):
            This function will halt execution and post an error in the
            Maya Script Editor if a critical file (like mayapy.exe,
            tracker.py, or the definition file) cannot be found, or if
            it fails to create a necessary directory or temp file.
    """
    print("--- Starting New Retarget Batch ---")

    # --- 1. HANDLE DEFINITION (DICT OR PATH) ---
    final_definition_path = ""

    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"[Main Maya] Created output directory: {output_dir}")
        except Exception as e:
            cmds.error(f"Failed to create output directory: {e}")
            return

    if isinstance(definition_json_path, dict):
        print("[Main Maya] Received dictionary as definition. Writing to system temp file.")
        temp_dir = tempfile.gettempdir()
        final_definition_path = os.path.join(temp_dir, "_retargeter_temp_definition.json")
        try:
            with open(final_definition_path, "w", encoding="utf-8") as f:
                json.dump(definition_json_path, f, indent=4)
            print(f"[Main Maya] Wrote temp definition to: {final_definition_path}")
        except Exception as e:
            cmds.error(f"Failed to write temp definition JSON: {e}")
            return

    elif isinstance(definition_json_path, str):
        if not os.path.exists(definition_json_path):
            cmds.error(f"Definition file not found at: {definition_json_path}")
            return
        final_definition_path = definition_json_path
        print(f"[Main Maya] Using definition file: {final_definition_path}")

    else:
        cmds.error(
            f"Invalid definition_json_path type. Must be a str (path) or dict. Got: {type(definition_json_path)}"
        )
        return

    # --- 2. FIND SCRIPTS DIRECTORY (Tracker & Worker) ---
    scripts_dir = ""
    try:
        scripts_dir = os.path.dirname(os.path.realpath(__file__))
    except NameError:
        print("Warning: __file__ not found. Using default script directory.")
        scripts_dir = r"R:\DccTools\maya\tech_anim\tools\retargeter"

    tracker_script_path = os.path.join(scripts_dir, "multi_batch_tracker.py")

    if not os.path.exists(tracker_script_path):
        print(f"Warning: Tracker not found at {tracker_script_path}. Trying default.")
        scripts_dir = r"R:\DccTools\maya\tech_anim\tools\retargeter"
        tracker_script_path = os.path.join(scripts_dir, "multi_batch_tracker.py")

        if not os.path.exists(tracker_script_path):
            cmds.error(f"Could not find tracker.py at default location: {tracker_script_path}")
            return

    print(f"[Main Maya] Using scripts from: {scripts_dir}")

    # --- 3. VALIDATE AND WRITE SOURCE FILES LIST ---
    if not source_files_list:
        cmds.error(f"No source files provided.")
        return

    print(f"[Main Maya] Found {len(source_files_list)} files to process.")

    # Write the job list to a temp file to avoid a long command line
    job_file_path = ""
    try:
        temp_dir = tempfile.gettempdir()
        job_file_path = os.path.join(temp_dir, "_retargeter_job_queue.txt")
        with open(job_file_path, "w", encoding="utf-8") as f:
            for file_path in source_files_list:
                f.write(file_path + "\n")
        print(f"[Main Maya] Wrote job queue to: {job_file_path}")
    except Exception as e:
        cmds.error(f"Failed to write job queue file: {e}")
        return

    # --- 4. FIND MAYAPY.EXE DYNAMICALLY ---
    mayapy_exe_path = ""
    try:
        current_exe_path = sys.executable
        bin_dir = os.path.dirname(current_exe_path)
        exe_name = "mayapy.exe" if sys.platform == "win32" else "mayapy"
        mayapy_exe_path = os.path.join(bin_dir, exe_name)
        if not os.path.exists(mayapy_exe_path):
            cmds.error(f"Could not find mayapy at: {mayapy_exe_path}")
            return
        print(f"[Main Maya] Found mayapy at: {mayapy_exe_path}")
    except Exception as e:
        cmds.error(f"Error finding mayapy.exe: {e}")
        return

    # --- 5. BUILD THE COMMAND TO LAUNCH THE TRACKER ---
    command_list = [
        mayapy_exe_path,
        tracker_script_path,
        "-mp",
        mayapy_exe_path,
        "-b",
        output_dir,
        "-dj",
        final_definition_path,
        "-w",
        str(max_workers),
        "-j",
        job_file_path,
    ]

    if disable_logging:
        command_list.append("--no-log")

    if skip_existing_files:
        command_list.append("--skip-existing")

    print(f"[Main Maya] Executing: {command_list}")

    # --- 6. LAUNCH THE TRACKER PROCESS ---
    try:
        creation_flags = 0
        if sys.platform == "win32":
            creation_flags = subprocess.CREATE_NEW_CONSOLE

        subprocess.Popen(command_list, creationflags=creation_flags, shell=False)
        print("[Main Maya] Tracker Console has been launched.")
        print("[Main Maya] You can continue working.")
    except Exception as e:
        cmds.error(f"Failed to launch tracker console: {e}")


if __name__ == "__main__":
    print("--- Running Batch Manager in test mode ---")

    test_def_path = "C:/external/assets/retargeter_definitions/xsens_to_male_pv_patch_testing.json"

    test_files_list = [
        "C:/Users/S-PC/Desktop/input_batch_dev/Sample_A.fbx",
        # "C:/Users/S-PC/Desktop/input_batch_dev/Sample_B.fbx",
        # "C:/Users/S-PC/Desktop/input_batch_dev/Sample_C.fbx",
        # "C:/Users/S-PC/Desktop/input_batch_dev/Sample_D.fbx",
        # "C:/Users/S-PC/Desktop/input_batch_dev/Sample_E.fbx",
    ]
    test_output_dir = "C:/Users/S-PC/Desktop/output_batch_dev"
    test_output_dir = r"R:\OUTPUT"

    run_retarget_batch(
        definition_json_path=test_def_path,
        source_files_list=test_files_list,
        output_dir=test_output_dir,
        max_workers=2,
        disable_logging=False,
        skip_existing_files=True,
    )
