"""Isolated Maya scene export; importing this module does not import Maya."""

import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from gt.core.io import read_json_dict, write_json


def file_digest(path):
    """Hashes a file without loading the whole clip into memory.

    Args:
        path (str): Existing file.

    Returns:
        str: SHA-256 digest.
    """
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def motion_paths(paths):
    """Selects downloaded motion JSON files, excluding manifests and NPZ archives.

    Args:
        paths (dict): Downloaded artifact names mapped to local paths.

    Returns:
        dict: Sample names mapped to absolute existing files.
    """
    motions = {name: path for name, path in sorted(paths.items())
               if name == "motion.json" or re.fullmatch(r"sample_[0-7]\.json", name)}
    if not motions:
        raise ValueError("Download the generation results before creating Maya files.")
    if any(not os.path.isabs(path) or not os.path.isfile(path) for path in motions.values()):
        raise ValueError("Motion files are missing. Use Download Results to repair the download first.")
    return motions


def validate_target(target):
    """Validates optional target settings before starting the Maya worker.

    Args:
        target (dict or None): Target rig settings.

    Returns:
        dict or None: Normalized target settings, or None when disabled.
    """
    if not target:
        return None
    path = target.get("rig_path", "").strip()
    bake = target.get("bake_target", "Skeleton")
    if not os.path.isabs(path) or not os.path.isfile(path):
        raise ValueError("Choose an existing absolute target Maya or FBX rig file.")
    if bake not in ("None", "Skeleton", "Control Rig", "Custom Control Rig"):
        raise ValueError("Invalid HumanIK bake target.")
    if bake == "None" and target.get("delete_source", True):
        raise ValueError("Disable Delete source when using a live HumanIK connection without baking.")
    namespace = target.get("namespace", "").strip() or "kimodo"
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", namespace):
        raise ValueError("Target namespace must begin with a letter or underscore and contain only letters, digits, or underscores.")
    return {"rig_path": path, "character": target.get("character", "").strip(), "namespace": namespace,
            "bake_target": bake, "delete_source": bool(target.get("delete_source", True))}


def retarget_sample(source_group, source_character, target):
    """Imports a target rig and uses the Batch Processor HumanIK bake workflow.

    Args:
        source_group (str): Generated source skeleton root.
        source_character (str): Generated HumanIK character.
        target (dict): Validated target settings.
    """
    import maya.cmds as cmds
    from gt.tools.batch_processor.tasks import task_hik_retarget
    from gt.tools.batch_processor import batch_processor_maya

    # Load Arnold when available so its scene nodes do not become unknown on import.
    try:
        if not cmds.pluginInfo("mtoa", query=True, loaded=True):
            cmds.loadPlugin("mtoa", quiet=True)
    except Exception:
        pass
    if batch_processor_maya.is_fbx_file(target["rig_path"]):
        batch_processor_maya.load_relevant_file_plugin(target["rig_path"])
    before = set(cmds.ls(type="HIKCharacterNode") or [])
    temporary_namespace = "kimodo_target_import"
    suffix = 2
    while cmds.namespace(exists=f":{temporary_namespace}"):
        temporary_namespace = f"kimodo_target_import_{suffix}"
        suffix += 1
    if batch_processor_maya.is_fbx_file(target["rig_path"]):
        previous_namespace = cmds.namespaceInfo(currentNamespace=True, absoluteName=True)
        cmds.namespace(add=temporary_namespace, parent=":")
        try:
            cmds.namespace(set=f":{temporary_namespace}")
            cmds.file(target["rig_path"], i=True, returnNewNodes=True, executeScriptNodes=False)
        finally:
            cmds.namespace(set=previous_namespace)
    else:
        cmds.file(target["rig_path"], i=True, namespace=temporary_namespace, returnNewNodes=True,
                  mergeNamespacesOnClash=False, executeScriptNodes=False)
    # Maya standalone does not register the editor-only saved tab node.
    for node in cmds.ls(type="unknown") or []:
        if node.split(":")[-1] == "hyperShadePrimaryNodeEditorSavedTabsInfo":
            cmds.lockNode(node, lock=False)
            cmds.delete(node)
    candidates = sorted(set(cmds.ls(type="HIKCharacterNode") or []) - before)
    requested = target["character"].strip(":")
    if requested:
        candidates = [name for name in candidates if name == requested or name.endswith(":" + requested)]
    if len(candidates) != 1:
        raise ValueError(f"Expected one matching target HumanIK character; found: {candidates}")
    task = task_hik_retarget.TaskRetargetHumanIK()
    task.settings["bake_target"] = target["bake_target"]
    task.retarget_and_bake(source_character, candidates[0])
    if target["delete_source"]:
        task.delete_source_nodes([source_group, source_character])
    requested_namespace = target.get("namespace") or "kimodo"
    if cmds.namespace(exists=f":{requested_namespace}"):
        nodes = cmds.namespaceInfo(f":{requested_namespace}", listOnlyDependencyNodes=True, recurse=True) or []
        children = cmds.namespaceInfo(f":{requested_namespace}", listOnlyNamespaces=True, recurse=True) or []
        if not nodes and not children:
            cmds.namespace(removeNamespace=f":{requested_namespace}")
    available_namespace = requested_namespace
    suffix = 2
    while cmds.namespace(exists=f":{available_namespace}"):
        available_namespace = f"{requested_namespace}_{suffix}"
        suffix += 1
    cmds.namespace(rename=(temporary_namespace, available_namespace))


def export_maya_files(paths, settings=None, mayapy_path=None, target=None, warnings=None, output_time_unit=""):
    """Creates retarget-ready scenes in an owned child process, never the open scene.

    Args:
        paths (dict): Downloaded artifact paths.
        settings (dict): Optional source HumanIK settings. Exports always lock the definition.
        mayapy_path (str): Optional interpreter override, primarily for scripted use/testing.
        target (dict): Optional target rig and HumanIK retargeting settings.
        warnings (list): Optional list to receive warnings when retargeting falls back to the source scene.
        output_time_unit (str): Maya time unit for the output scene. Defaults to the motion frame rate.

    Returns:
        dict: Motion JSON names mapped to saved Maya ASCII paths.
    """
    from gt.tools.kimodo_generator.kimodo_generator_hik import validate_settings

    from gt.tools.kimodo_generator import kimodo_generator_time_units
    if not kimodo_generator_time_units.valid_time_unit(output_time_unit):
        raise ValueError("Unsupported output frame rate.")
    motions = motion_paths(paths)
    settings = validate_settings(settings or {}, check_files=True)
    settings["lock_definition"] = True
    validation_warning = None
    try:
        target = validate_target(target)
    except ValueError as error:
        if warnings is None:
            raise
        validation_warning = f"Target retargeting failed ({error}); imported Kimodo source only."
        target = None
    if not mayapy_path:
        sibling = os.path.join(os.path.dirname(sys.executable), "mayapy.exe" if os.name == "nt" else "mayapy")
        if os.path.isfile(sibling):
            mayapy_path = sibling
        else:
            from gt.utils.system import get_maya_executable

            mayapy_path = get_maya_executable(get_maya_python=True)
    if not mayapy_path or not os.path.isfile(mayapy_path):
        raise ValueError("Could not find mayapy. A local Maya installation is required to create Maya files.")
    package_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    environment = os.environ.copy()
    environment.update(MAYA_SKIP_USERSETUP_PY="1", MAYA_SKIP_USERSETUP_MEL="1", PYTHONIOENCODING="utf-8")
    with tempfile.TemporaryDirectory(prefix="kimodo_export_") as temporary:
        request = os.path.join(temporary, "request.json")
        response = os.path.join(temporary, "response.json")
        if not write_json(request, {"motions": motions, "settings": settings, "target": target, "output_time_unit": output_time_unit}):
            raise RuntimeError("Could not write the temporary Maya export request.")
        code = (f"import sys; sys.path.insert(0, {package_root!r}); "
                "from gt.tools.kimodo_generator.kimodo_generator_export import run_worker; "
                f"run_worker({request!r}, {response!r})")
        with open(os.path.join(temporary, "worker.log"), "w+", encoding="utf-8") as log:
            process = subprocess.run(
                [mayapy_path, "-c", code], env=environment, stdout=log, stderr=subprocess.STDOUT,
                timeout=1800, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            result = read_json_dict(response) if os.path.isfile(response) else {}
            if process.returncode or not result.get("files") or result.get("error"):
                log.seek(0)
                details = result.get("error") or log.read()[-6000:]
                raise RuntimeError(f"Maya file creation failed: {details}")
        if warnings is not None:
            if validation_warning:
                warnings.append(validation_warning)
            warnings.extend(result.get("warnings", []))
        return result["files"]


def _export_sample(path, settings, target=None, output_time_unit=""):
    """Builds one fresh scene inside the child Maya session and publishes exclusively.

    Args:
        path (str): Absolute motion JSON path.
        settings (dict): Validated HumanIK overrides.
        target (dict): Optional validated target rig and HumanIK retargeting settings.
        output_time_unit (str): Maya time unit for the output scene. Defaults to the motion frame rate.

    Returns:
        str: Maya ASCII file beside the motion JSON.
    """
    import maya.cmds as cmds
    from gt.utils import kimodo

    output = os.path.splitext(path)[0] + ".ma"
    receipt_path = output + ".kimodo.json"
    identity = {"source_sha256": file_digest(path), "settings": settings}
    if output_time_unit:
        identity["output_time_unit"] = output_time_unit
    if target:
        identity["target"] = target
        identity["target_sha256"] = file_digest(target["rig_path"])
    # Include external definition/pose contents so edits cannot silently reuse stale scenes.
    identity["overrides"] = {key: file_digest(settings[key]) for key in ("definition_path", "tpose_path")
                             if settings.get(key)}
    if os.path.lexists(receipt_path):
        receipt = read_json_dict(receipt_path)
        if (os.path.islink(receipt_path) or receipt.get("identity") != identity
                or receipt.get("output") != output):
            raise ValueError(f"Export settings/inputs changed or the receipt is invalid. Preserve or move: {output}")
    else:
        receipt = {}
    if os.path.lexists(output):
        if (os.path.islink(output) or not os.path.isfile(output)
                or receipt.get("sha256") != file_digest(output)):
            raise ValueError(f"Refusing to overwrite an existing or edited Maya file: {output}")
        return output
    motion = read_json_dict(path)
    kimodo.validate_motion(motion)
    cmds.file(new=True, force=True)
    cmds.currentUnit(linear="cm", angle="deg", time=output_time_unit or f"{motion['fps']:g}fps")
    cmds.upAxis(axis="y")
    imported = kimodo.import_motion(path, namespace="kimodo_animation", start_frame=1)
    source = kimodo.create_humanik_definition(imported["group"], settings)
    cmds.playbackOptions(minTime=imported["start_frame"], maxTime=imported["end_frame"],
                         animationStartTime=imported["start_frame"], animationEndTime=imported["end_frame"])
    cmds.currentTime(imported["start_frame"])
    if target:
        retarget_sample(imported["group"], source["character"], target)
    with tempfile.TemporaryDirectory(prefix="kimodo_scene_") as temporary:
        staging = os.path.join(temporary, "scene.ma")
        cmds.file(rename=staging)
        cmds.file(save=True, type="mayaAscii", force=True)
        # Exclusive creation also protects against a second tool/process exporting this job.
        with open(staging, "rb") as source, open(output, "xb") as destination:
            shutil.copyfileobj(source, destination)
    if not write_json(receipt_path, {"identity": identity, "output": output, "sha256": file_digest(output)}):
        raise RuntimeError(f"Maya scene was saved, but its verification receipt could not be written: {output}")
    return output


def run_worker(request_path, response_path):
    """Owns standalone initialization only in the separately launched interpreter.

    Args:
        request_path (str): Temporary export request JSON.
        response_path (str): Temporary completion/error JSON.
    """
    import maya.standalone

    initialized = False
    try:
        maya.standalone.initialize(name="python")
        initialized = True
        request = read_json_dict(request_path)
        files = {}
        warnings = []
        for name, path in request["motions"].items():
            try:
                files[name] = _export_sample(path, request["settings"], request.get("target"), request.get("output_time_unit", ""))
            except Exception as error:
                if not request.get("target"):
                    raise
                warnings.append(f"{name}: target retargeting failed ({error}); imported Kimodo source only.")
                files[name] = _export_sample(path, request["settings"], None, request.get("output_time_unit", ""))
        write_json(response_path, {"files": files, "warnings": warnings})
    except Exception:
        write_json(response_path, {"error": traceback.format_exc()})
    finally:
        if initialized:
            maya.standalone.uninitialize()
