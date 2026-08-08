"""
MotionBuilder batch example.

Values exposed by the batch processor when Pass Task Args is enabled:
    BATCH_INPUT: Source FBX file or folder.
        Example: C:/project/01_input/walk.fbx
    BATCH_OUTPUT: Expected output FBX file or folder.
        Example: C:/project/02_tasks/01_motionbuilder/walk.fbx
    BATCH_PROJECT: Batch project file.
        Example: C:/project/Batch_process_project.batch
    BATCH_PROJECT_DIR: Folder containing the batch project.
        Example: C:/project
    BATCH_TASK: Task display name.
        Example: MotionBuilder
    BATCH_TASK_ID: Stable task id from the .batch file.
        Example: 2f35ec56-8e64-4df7-9a30-612af8d4f2db
    BATCH_CONTEXT: JSON file with the same batch context data.
        Example: C:/Users/name/AppData/Local/Temp/mobu_context_ab12.json

Project environment variables are exposed as BATCH_ENV_NAME values. For
manual testing, the script also accepts equivalent --input, --output,
--project, --project-dir, --task, --task-id, --context, and --env-var
command-line arguments.
"""

import argparse
import json
import os
import sys

from pyfbsdk import FBApplication, FBSystem, FBFbxOptions


def parse_args():
    """Parses batch arguments while tolerating MotionBuilder arguments."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--project", default="")
    parser.add_argument("--project-dir", default="")
    parser.add_argument("--task", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--context", default="")
    parser.add_argument("--env-var", action="append", default=[])
    args, _ = parser.parse_known_args(sys.argv[1:])
    return args


def load_context(context_path):
    """Loads the optional batch context JSON file.

    Args:
        context_path (str): Path to the batch context JSON file.

    Returns:
        dict: Loaded context data, or an empty dictionary when unavailable.
    """
    if context_path and os.path.isfile(context_path):
        with open(context_path, "r", encoding="utf-8") as context_file:
            return json.load(context_file)
    return {}


def build_file_pairs(input_path, output_path):
    """Builds input/output FBX file pairs.

    Args:
        input_path (str): Source FBX file or directory.
        output_path (str): Destination FBX file or directory.

    Returns:
        list: Input/output file path pairs.
    """
    if os.path.isdir(input_path):
        if not os.path.isdir(output_path):
            os.makedirs(output_path)
        pairs = []
        for file_name in sorted(os.listdir(input_path)):
            if file_name.lower().endswith(".fbx"):
                pairs.append((os.path.join(input_path, file_name), os.path.join(output_path, file_name)))
        return pairs
    return [(input_path, output_path)]


def strip_geometry(input_path, output_path):
    """Opens an FBX, saves skeleton/character data only, and writes the result.

    Args:
        input_path (str): Source FBX file path.
        output_path (str): Destination FBX file path.
    """
    app = FBApplication()
    system = FBSystem()
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    app.FileNew()
    app.FileOpen(input_path, False)

    for component in system.Scene.Components:
        component.Selected = False

    safe_classes = [
        "FBModelSkeleton",
        "FBModelRoot",
        "FBModelNull",
        "FBCharacter",
        "FBControlRig",
        "FBCamera",
        "FBLight",
        "FBModelMarker",
        "FBConstraint",
    ]
    for component in system.Scene.Components:
        if component.ClassName() in safe_classes:
            component.Selected = True
            if hasattr(component, "Visibility"):
                component.Visibility = True

    save_options = FBFbxOptions(False)
    save_options.SaveSelectedModelsOnly = True
    save_options.SaveCharacter = True
    save_options.SaveControlRig = True
    app.FileSave(output_path, save_options)
    print("Headless safe export: {0}".format(output_path))


def main():
    """Runs the MotionBuilder batch example."""
    args = parse_args()
    context_path = args.context or os.environ.get("BATCH_CONTEXT", "")
    context = load_context(context_path)
    input_path = args.input or os.environ.get("BATCH_INPUT") or context.get("current_path") or context.get("source_path")
    output_path = args.output or os.environ.get("BATCH_OUTPUT") or context.get("output_path")
    if not input_path or not output_path:
        raise RuntimeError("Input and output paths are required.")
    for source_path, target_path in build_file_pairs(input_path, output_path):
        print("Input Path: {0}".format(source_path))
        print("Output Path: {0}".format(target_path))
        strip_geometry(source_path, target_path)
    FBApplication().FileNew()
    FBApplication().FileExit()


main()
