import traceback
import argparse
import datetime
import sys
import time
import json
import os

# --- Set up argument parsing ---
parser = argparse.ArgumentParser(description="Maya Headless Retargeter Worker")
parser.add_argument("-dj", "--definition_json", required=True, help="Path to the definition JSON file")
parser.add_argument("-sf", "--source_file", required=True, help="Full path to the source file to retarget")
parser.add_argument("-b", "--basedir", required=True, help="Base directory for logs and output")
parser.add_argument("--no-log", action="store_true", help="Disable writing to the error log file")
parser.add_argument(
    "--skip-existing", action="store_true", help="Skip files that already exist in the output directory"
)
args = parser.parse_args()

print("--- RETARGET WORKER SCRIPT STARTED ---")


# --- Setup Logging (Now conditional) ---
def log_error(msg):
    """
    Logs errors during into a worker error file
    Args:
        msg (str): The error message
    """
    if args.no_log:
        return

    today_str = datetime.date.today().strftime("%Y-%m-%d")
    log_filename = f"worker_error_{today_str}.log"
    log_path = os.path.join(args.basedir, log_filename)

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"--- Error for source file: {args.source_file} ---\n")
        f.write(msg + "\n")
        f.write(traceback.format_exc() + "\n")
        f.write("-------------------------------------\n")


# --- Import custom framework (we need core_io early) ---
try:
    print("Importing core_io for file operations...")
    import gt.core.io as core_io
except ImportError:
    print("!!! CRITICAL ERROR: Could not import 'gt.core.io'!")
    log_error("Failed to import gt.core.io")
    time.sleep(10)
    sys.exit(1)  # Exit with an error

# --- File handling logic ---
source_filename = os.path.basename(args.source_file)
source_name_no_ext = os.path.splitext(source_filename)[0]
output_filename = source_name_no_ext + ".ma"
output_path = os.path.join(args.basedir, output_filename)
print(f"Output file will be: {output_path}")

try:
    if os.path.exists(output_path):
        if args.skip_existing:
            print(f"--- ⏩ SKIPPED: '{output_filename}' (Already Exists) ---")
            sys.exit(10)  # Exit with special "SKIPPED" code for the tracker
        else:
            print(f"Setting permissions modifiable for overwrite: {output_path}")
            core_io.set_file_permission_modifiable(output_path)
            print("...Permissions set.")
    else:
        print(f"Reserving file (creating empty file): {output_path}")
        if not os.path.exists(args.basedir):
            os.makedirs(args.basedir)
        with open(output_path, "w") as f:
            pass  # Create the empty file
except Exception as e:
    print(f"!!! CRITICAL ERROR: Failed during pre-flight file operations: {e}")
    log_error(f"Failed during pre-flight file operations: {e}")
    time.sleep(10)
    sys.exit(1)

print("Initializing Maya Standalone...")
try:
    import maya.standalone

    maya.standalone.initialize(name="python")
    print("...Initialized.")
except Exception as e:
    print(f"!!! CRITICAL ERROR: Failed to initialize maya.standalone: {e}")
    log_error(f"Failed to initialize maya.standalone: {e}")
    time.sleep(10)
    sys.exit(1)

# --- Mock maya.utils.executeDeferred ---
print("Mocking maya.utils.executeDeferred for headless mode...")
try:
    import maya.utils

    def dummy_execute_deferred(*args, **kwargs):
        """
        A mock for the GUI-only executeDeferred.
        """
        print("...Executing deferred call immediately.")
        if args:
            try:
                func = args[0]
                func_args = args[1:]
                func(*func_args, **kwargs)
            except Exception as e:
                print(f"!!! ERROR in mocked executeDeferred: {e}")
                pass

    maya.utils.executeDeferred = dummy_execute_deferred
    print("...Mock applied.")

except Exception as e:
    print(f"!!! CRITICAL ERROR: Failed to mock maya.utils: {e}")
    log_error(f"Failed to mock maya.utils: {e}")
    time.sleep(10)
    sys.exit(1)

# --- Import custom framework ---
try:
    print("Importing package loader to set up paths...")
    import gt.core.data.scripts.package_loader

    print("...Package loader imported.")

    import gt.tools.retargeter.retargeter_framework as tools_rt_frm
except ImportError as e:
    print("!!! CRITICAL ERROR !!!")
    print(f"Failed to import a required module: {e}")
    log_error(f"Failed to import a module: {e}")
    time.sleep(10)
    sys.exit(1)

# --- Main Worker Logic ---
try:
    import maya.cmds as cmds

    print(f"Worker processing: {args.source_file}")
    print(f"Using definition: {args.definition_json}")

    print("Loading definition data from JSON...")
    with open(args.definition_json, "r") as f:
        definition_data = json.load(f)
    print("...Data loaded.")

    if not cmds.ls(type="camera"):
        raise RuntimeError("Maya Standalone failed to initialize properly. Check license.")
    print("...Initialization confirmed.")

    print("Creating RetargeterDefinition...")
    definition = tools_rt_frm.RetargeterDefinition()

    print("Reading data from dictionary...")
    definition.read_data_from_dict(definition_data)

    print(f"Setting source path to: {args.source_file}")
    definition.set_source_path(args.source_file)

    print("Running retarget()... (This may take a while)")
    definition.retarget()
    print("...Retarget complete.")

    print(f"Saving new file to: {output_path}")
    cmds.file(rename=output_path)
    cmds.file(save=True, type="mayaAscii", force=True)
    print("...File saved successfully.")

except Exception as e:
    print("!!! AN ERROR OCCURRED !!!")
    log_error(str(e))
    if not args.no_log:
        print(f"ERROR: See error log in output folder.")
    print(traceback.format_exc())
    sys.exit(1)  # Exit with a failure code

finally:
    try:
        print("Uninitializing Maya...")
        maya.standalone.uninitialize()
        print("...Uninitialized.")
    except Exception as e:
        print("!!! ERROR ON UNINITIALIZE !!!")
        log_error("Failed to uninitialize Maya: " + str(e))

print("---------------------------------")
print("Worker script finished.")
print("Closing in 3 seconds...")
time.sleep(3)
sys.exit(0)  # Exit with a success code
