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


def export_maya_files(paths, settings=None, mayapy_path=None):
    """Creates retarget-ready scenes in an owned child process, never the open scene.

    Args:
        paths (dict): Downloaded artifact paths.
        settings (dict): Optional source HumanIK settings. Exports always lock the definition.
        mayapy_path (str): Optional interpreter override, primarily for scripted use/testing.

    Returns:
        dict: Motion JSON names mapped to saved Maya ASCII paths.
    """
    from gt.tools.kimodo_generator.kimodo_generator_hik import validate_settings

    motions = motion_paths(paths)
    settings = validate_settings(settings or {}, check_files=True)
    settings["lock_definition"] = True
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
        if not write_json(request, {"motions": motions, "settings": settings}):
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
        return result["files"]


def _export_sample(path, settings):
    """Builds one fresh scene inside the child Maya session and publishes exclusively.

    Args:
        path (str): Absolute motion JSON path.
        settings (dict): Validated HumanIK overrides.

    Returns:
        str: Maya ASCII file beside the motion JSON.
    """
    import maya.cmds as cmds
    from gt.utils import kimodo

    output = os.path.splitext(path)[0] + ".ma"
    receipt_path = output + ".kimodo.json"
    identity = {"source_sha256": file_digest(path), "settings": settings}
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
    cmds.currentUnit(linear="cm", angle="deg", time=f"{motion['fps']:g}fps")
    cmds.upAxis(axis="y")
    imported = kimodo.import_motion(path, namespace="kimodo_animation", start_frame=1)
    kimodo.create_humanik_definition(imported["group"], settings)
    cmds.playbackOptions(minTime=imported["start_frame"], maxTime=imported["end_frame"],
                         animationStartTime=imported["start_frame"], animationEndTime=imported["end_frame"])
    cmds.currentTime(imported["start_frame"])
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
        files = {name: _export_sample(path, request["settings"]) for name, path in request["motions"].items()}
        write_json(response_path, {"files": files})
    except Exception:
        write_json(response_path, {"error": traceback.format_exc()})
    finally:
        if initialized:
            maya.standalone.uninitialize()
