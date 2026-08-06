"""
Blender batch example.

Arguments passed by the batch processor when Pass Task Args is enabled:
    --input: Source file.
        Example: C:/project/01_input/character.fbx
    --output: Expected output file.
        Example: C:/project/02_tasks/01_blender/character.fbx
    --project: Batch project file.
        Example: C:/project/Batch_process_project.batch
    --project-dir: Folder containing the batch project.
        Example: C:/project
    --task: Task display name.
        Example: Blender
    --task-id: Stable task id from the .batch file.
        Example: 2f35ec56-8e64-4df7-9a30-612af8d4f2db
    --context: JSON file with the same batch context data.
        Example: C:/Users/name/AppData/Local/Temp/blender_context_ab12.json
    --env-var: Repeated project environment variable pair.
        Example: --env-var output-dir=03_output

The task also sets BATCH_INPUT, BATCH_OUTPUT, BATCH_PROJECT,
BATCH_PROJECT_DIR, BATCH_TASK, BATCH_TASK_ID, and BATCH_CONTEXT as process
environment variables.
"""

import argparse
import json
import os
import sys

import bpy


def parse_args():
    """Parses arguments after Blender's -- separator."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--project", default="")
    parser.add_argument("--project-dir", default="")
    parser.add_argument("--task", default="")
    parser.add_argument("--task-id", default="")
    parser.add_argument("--context", default="")
    parser.add_argument("--env-var", action="append", default=[])
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []
    args, _ = parser.parse_known_args(argv)
    return args


def load_context(context_path):
    """Loads the optional batch context JSON file."""
    if context_path and os.path.isfile(context_path):
        with open(context_path, "r", encoding="utf-8") as context_file:
            return json.load(context_file)
    return {}


def open_input_file(file_path):
    """Opens a Blend file or imports a supported interchange file."""
    extension = os.path.splitext(file_path)[1].lower()
    if extension == ".blend":
        bpy.ops.wm.open_mainfile(filepath=file_path)
        return
    bpy.ops.wm.read_factory_settings(use_empty=True)
    if extension == ".fbx":
        bpy.ops.import_scene.fbx(filepath=file_path)
    elif extension == ".obj":
        bpy.ops.wm.obj_import(filepath=file_path)
    elif extension in [".gltf", ".glb"]:
        bpy.ops.import_scene.gltf(filepath=file_path)
    else:
        raise RuntimeError("Unsupported Blender input extension: {0}".format(extension))


def export_fbx(file_path):
    """Exports the current Blender scene as FBX."""
    output_path = os.path.splitext(file_path)[0] + ".fbx"
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.isdir(output_dir):
        os.makedirs(output_dir)
    bpy.ops.export_scene.fbx(filepath=output_path)
    return output_path


def main():
    """Runs the Blender batch example."""
    args = parse_args()
    context_path = args.context or os.environ.get("BATCH_CONTEXT", "")
    context = load_context(context_path)
    input_path = args.input or os.environ.get("BATCH_INPUT") or context.get("current_path") or context.get("source_path")
    output_path = args.output or os.environ.get("BATCH_OUTPUT") or context.get("output_path")
    if not input_path or not output_path:
        raise RuntimeError("Input and output paths are required.")
    print("Input Path: {0}".format(input_path))
    print("Output Path: {0}".format(output_path))
    open_input_file(input_path)
    exported_path = export_fbx(output_path)
    print("Exported FBX: {0}".format(exported_path))


main()
