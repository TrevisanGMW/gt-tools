"""Imports FBX assets and exports a selected asset as FBX in Unreal Engine."""

import argparse
import json
import os
import shlex
import sys
import uuid

import unreal


def parse_args():
    """Parses the batch processor arguments after Unreal's separator.

    Returns:
        argparse.Namespace: Parsed input, output, and context paths.
    """
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--input", default="")
    parser.add_argument("--output", default="")
    parser.add_argument("--context", default="")

    argv = []
    command_line = getattr(unreal.SystemLibrary, "get_command_line", None)
    if command_line:
        raw_command_line = command_line()
        argv = shlex.split(raw_command_line, posix=False)
        if "--" in argv:
            argv = argv[argv.index("--") + 1 :]

        # Unreal's Python commandlet does not forward arguments after the
        # script path to sys.argv. It does preserve them in the full command
        # line, so the command line is the primary source here.
        normalized_argv = []
        for argument in argv:
            if argument.endswith('""') and argument.startswith("--"):
                normalized_argv.extend([argument[:-2], ""])
            else:
                normalized_argv.append(argument.strip('"'))
        argv = normalized_argv
    elif "--" in sys.argv:
        argv = sys.argv[sys.argv.index("--") + 1 :]

    # An empty context can arrive as a missing value when Unreal rebuilds the
    # Windows command line. Keep argparse from treating that as an error.
    for option_name in ("--input", "--output", "--context"):
        if option_name in argv:
            option_index = argv.index(option_name)
            value_index = option_index + 1
            if value_index == len(argv) or argv[value_index].startswith("--"):
                argv.insert(value_index, "")

    args, _ = parser.parse_known_args(argv)
    return args


def load_context(context_path):
    """Loads the optional Batch Processor context JSON file.

    Args:
        context_path (str): Context JSON path.

    Returns:
        dict: Loaded context data, or an empty dictionary.
    """
    if context_path and os.path.isfile(context_path):
        with open(context_path, "r", encoding="utf-8") as context_file:
            return json.load(context_file)
    return {}


def resolve_output_path(output_value, input_path):
    """Resolves a file output path from a file or directory setting.

    Args:
        output_value (str): Requested output file or directory.
        input_path (str): Input FBX path used for a directory fallback.

    Returns:
        str: Output FBX file path.
    """
    output_value = str(output_value or "").strip()
    if not output_value:
        output_value = "C:/Temp/UnrealBatchOutput/processed.fbx"

    output_value = os.path.normpath(output_value)
    if os.path.isdir(output_value) or not os.path.splitext(output_value)[1]:
        output_value = os.path.join(output_value, os.path.basename(input_path))

    return output_value


def import_fbx(input_path):
    """Imports one FBX file into a temporary project content folder.

    Args:
        input_path (str): Source FBX path.

    Returns:
        list: Imported Unreal asset objects.
    """
    input_name = os.path.splitext(os.path.basename(input_path))[0]
    safe_input_name = "".join(
        character if character.isalnum() or character == "_" else "_"
        for character in input_name
    )
    destination_path = (
        "/Game/BatchProcessor/Imported/"
        f"{safe_input_name}_{uuid.uuid4().hex[:8]}"
    )
    unreal.EditorAssetLibrary.make_directory(destination_path)

    import_options = unreal.FbxImportUI()
    import_options.import_mesh = True
    import_options.import_as_skeletal = True
    import_options.import_animations = True
    import_options.import_materials = False
    import_options.import_textures = False

    unreal.log(f"Importing FBX: {input_path}")
    # Avoid Content Browser synchronization, which can initialize Slate in a
    # commandlet and crash UnrealEditor-Cmd before the task returns.
    unreal.SystemLibrary.execute_console_command(
        None, "Interchange.FeatureFlags.Import.SyncToBrowser 0"
    )

    import_task = unreal.AssetImportTask()
    import_task.filename = input_path
    import_task.destination_path = destination_path
    import_task.automated = True
    import_task.replace_existing = True
    import_task.save = False
    import_task.options = import_options

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    asset_tools.import_asset_tasks([import_task])

    imported_objects = list(import_task.get_objects() or [])
    if not imported_objects:
        for object_path in import_task.imported_object_paths:
            imported_object = unreal.load_asset(object_path)
            if imported_object:
                imported_objects.append(imported_object)

    imported_names = [
        f"{asset.get_class().get_name()}: {asset.get_name()}"
        for asset in imported_objects
    ]
    unreal.log(f"Imported Unreal assets: {imported_names}")
    return list(imported_objects or [])


def select_export_asset(imported_objects):
    """Selects a mesh or animation asset from imported FBX objects.

    Args:
        imported_objects (list): Objects returned by the FBX import.

    Returns:
        object: Exportable Unreal asset.

    Raises:
        RuntimeError: If the FBX did not produce a supported asset.
    """
    export_class_names = ("AnimSequence", "SkeletalMesh", "StaticMesh")
    export_classes = []
    for class_name in export_class_names:
        export_class = getattr(unreal, class_name, None)
        if export_class:
            export_classes.append(export_class)

    for class_name in export_class_names:
        for imported_object in imported_objects:
            imported_class = imported_object.get_class().get_name()
            if imported_class == class_name:
                return imported_object

    if export_classes:
        for imported_object in imported_objects:
            if isinstance(imported_object, tuple(export_classes)):
                return imported_object

    imported_names = [
        imported_object.get_name() for imported_object in imported_objects
    ]
    raise RuntimeError(
        "FBX import produced no supported mesh or animation asset. "
        f"Imported objects: {imported_names}"
    )


def export_fbx(asset, output_path):
    """Exports an Unreal asset to an FBX file.

    Args:
        asset (object): Unreal mesh or animation asset.
        output_path (str): Destination FBX path.
        input_path (str): Source FBX path used by the commandlet fallback.

    Raises:
        RuntimeError: If Unreal does not create the output file.
    """
    output_directory = os.path.dirname(output_path)
    if output_directory and not os.path.isdir(output_directory):
        os.makedirs(output_directory)

    command_line = unreal.SystemLibrary.get_command_line().lower()
    commandlet_rendering_enabled = "-allowcommandletrendering" in command_line
    skeletal_mesh_class = getattr(unreal, "SkeletalMesh", None)
    anim_sequence_class = getattr(unreal, "AnimSequence", None)
    is_skeletal_mesh = skeletal_mesh_class and isinstance(
        asset, skeletal_mesh_class
    )
    is_anim_sequence = anim_sequence_class and isinstance(asset, anim_sequence_class)
    if (is_skeletal_mesh or is_anim_sequence) and not commandlet_rendering_enabled:
        # UE 5.7's skeletal FBX exporter requires commandlet rendering flags.
        # Without them it crashes in SkinnedMeshComponent instead of returning
        # an export error, so keep the default task configuration safe.
        unreal.log_warning(
            "Commandlet rendering is disabled; writing the imported FBX "
            "source to the requested output path. Add "
            "-AllowCommandletRendering -AllowSoftwareRendering to "
            "unreal_arguments to enable native Unreal FBX export."
        )
        raise RuntimeError(
            "Native Unreal FBX export requires "
            "-AllowCommandletRendering and -AllowSoftwareRendering "
            "in unreal_arguments. The source FBX will not be copied."
        )

    export_task = unreal.AssetExportTask()
    export_task.object = asset
    export_task.filename = output_path
    export_task.automated = True
    export_task.prompt = False
    export_task.replace_identical = True
    export_options = unreal.FbxExportOption()
    export_options.set_editor_property("export_morph_targets", False)
    export_options.set_editor_property(
        "export_preview_mesh", bool(is_anim_sequence)
    )
    export_task.options = export_options

    unreal.log(f"Exporting FBX: {output_path}")
    unreal.Exporter.run_asset_export_task(export_task)

    if os.path.isfile(output_path):
        return

    export_errors = list(getattr(export_task, "errors", []) or [])
    raise RuntimeError(
        "Unreal did not create the FBX output. "
        f"Export errors: {export_errors}"
    )


def main():
    """Imports the incoming FBX and exports a processed FBX copy."""
    args = parse_args()
    context = load_context(args.context)
    input_path = args.input or context.get("current_path") or ""
    output_value = args.output or context.get("output_path") or ""

    if not input_path or not os.path.isfile(input_path):
        raise RuntimeError(f"Input FBX does not exist: {input_path}")

    output_path = resolve_output_path(output_value, input_path)
    imported_objects = import_fbx(input_path)
    if not imported_objects:
        raise RuntimeError(f"FBX import produced no objects: {input_path}")

    asset = select_export_asset(imported_objects)
    unreal.log(
        "Processing imported asset: "
        f"{asset.get_class().get_name()} / {asset.get_name()}"
    )
    export_fbx(asset, output_path)
    unreal.log(f"Unreal FBX batch example completed: {output_path}")
    unreal.SystemLibrary.quit_editor()


main()
