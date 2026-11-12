"""
Applies the patch steps of one take to the open scene.

    from motion_eval.repairs import apply
    result = apply.apply_manifest("patches.json", ["walk_042_v003"], seed=4711)

``result["status"]`` is one of: "none" (no entry for the take), "skipped" (fingerprint
mismatch), "applied", "partial" (some steps failed), or "failed".
"""

import importlib.util
import os
import sys
import traceback
import uuid

from .. import templates
from . import fixes
from . import manifest as manifest_module
from . import registry
from . import solvers
from . import transform_math
from .scene import RepairScene

STATUS_NONE = "none"
STATUS_SKIPPED = "skipped"
STATUS_APPLIED = "applied"
STATUS_PARTIAL = "partial"
STATUS_FAILED = "failed"


class PatchError(RuntimeError):
    """A patch failed while the manifest asks to fail on errors."""


def load_template(template_value, base_dir):
    """Loads the skeleton template a manifest names.

    Args:
        template_value (str or dict): Built-in key, file path (relative to the manifest), or template.
        base_dir (str): Manifest folder.

    Returns:
        dict or None: Template.
    """
    if not template_value:
        return None
    if isinstance(template_value, dict):
        return template_value
    if template_value in templates.get_builtin_template_keys():
        return templates.get_builtin_template(template_value)
    return templates.load_template(manifest_module.resolve_path(str(template_value), base_dir))


def get_scene_frame_range(scene):
    """Gets the scene's playback range as whole frames.

    Args:
        scene (RepairScene): Scene access.

    Returns:
        list: [start, end].
    """
    start_frame, end_frame = scene.host.get_time_range("playback")
    return [int(round(start_frame)), int(round(end_frame))]


def run_script_step(scene, step, base_dir, take_name, log):
    """Runs a custom script step: the script defines ``run(context)``.

    The context holds ``scene`` (RepairScene), ``frames``, ``params``, ``take``, ``log``, and the
    helper modules ``fixes``, ``solvers``, ``transform_math``, and ``registry``.

    Args:
        scene (RepairScene): Scene access.
        step (dict): Step with "script".
        base_dir (str): Manifest folder.
        take_name (str): Take being patched.
        log (callable): Message printer.

    Returns:
        object: Whatever the script's run(context) returns.

    Raises:
        ValueError: When the script has no run(context).
    """
    script_path = manifest_module.resolve_path(str(step["script"]), base_dir)
    module_name = f"motion_eval_patch_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    module = importlib.util.module_from_spec(spec)
    script_dir = os.path.dirname(script_path)
    added_path = script_dir not in sys.path
    if added_path:
        sys.path.insert(0, script_dir)
    try:
        spec.loader.exec_module(module)
    finally:
        if added_path and script_dir in sys.path:
            sys.path.remove(script_dir)
    if not hasattr(module, "run"):
        raise ValueError(f"Patch script has no run(context): {script_path}")
    frames = step.get("frames")
    context = {
        "scene": scene, "frames": tuple(frames) if frames else None, "params": dict(step.get("params") or {}),
        "take": take_name, "log": log, "fixes": fixes, "solvers": solvers, "transform_math": transform_math,
        "registry": registry,
    }
    return module.run(context)


def run_step(scene, step, base_dir, take_name, log):
    """Runs one step (a registry fix or a custom script).

    Args:
        scene (RepairScene): Scene access.
        step (dict): Step.
        base_dir (str): Manifest folder.
        take_name (str): Take being patched.
        log (callable): Message printer.

    Returns:
        dict: Step result with "status".
    """
    if "script" in step:
        returned = run_script_step(scene, step, base_dir, take_name, log)
        result = dict(returned) if isinstance(returned, dict) else {}
        result.setdefault("warnings", [])
        result["step"] = f"script {step['script']}"
        return result
    definition = registry.get_fix(step["fix"])
    params = definition.merge_params(step.get("params"), step.get("preset"))
    result = definition.function(scene, tuple(step["frames"]), list(step.get("nodes") or []), params)
    result["step"] = f"{registry.get_rung_key(definition.key, step.get('preset'))} {list(step['frames'])}"
    return result


def apply_entry(entry, base_dir, take_name="", template=None, seed=None, frame_range=None, on_error="warn",
                host=None, log=print):
    """Applies one take entry to the open scene.

    Args:
        entry (dict): Take entry from a manifest.
        base_dir (str): Manifest folder (for relative script paths).
        take_name (str): Take name for messages.
        template (dict, optional): Skeleton template for role names.
        seed (int, optional): Seed of the scene's generation (fingerprint).
        frame_range (list, optional): Scene frame range. Defaults to the playback range.
        on_error (str): "warn" records failed steps, "fail" raises PatchError.
        host (SceneHost, optional): Host. Defaults to the active host.
        log (callable): Message printer.

    Returns:
        dict: {"status", "take", "steps", "warnings", "reason"}.

    Raises:
        PatchError: When a step fails or the fingerprint differs and on_error is "fail".
    """
    scene = RepairScene(host=host, template=template)
    frame_range = frame_range or get_scene_frame_range(scene)
    matches, reason = manifest_module.check_fingerprint(entry, seed=seed, frame_range=frame_range)
    summary = {"status": STATUS_SKIPPED, "take": take_name, "steps": [], "warnings": [], "reason": reason}
    if not matches:
        message = f"Patch for {take_name} skipped: {reason}. The take changed since the patch was written."
        if on_error == "fail":
            raise PatchError(message)
        log(f"WARNING: {message}")
        return summary
    if not scene.host.supports_keying:
        raise PatchError(f"The {scene.host.label} host cannot write keys, so patches cannot run there.")
    failed = 0
    with scene.host.edit_block(f"patch_{take_name or 'take'}"):
        for step in entry.get("steps") or []:
            try:
                result = run_step(scene, step, base_dir, take_name, log)
                result["status"] = "ok"
                log(f"Patched {take_name}: {result['step']} ({result.get('keys', 0)} keys)")
            except Exception as error:
                failed += 1
                result = {"step": str(step.get("fix") or step.get("script")), "status": "failed",
                          "error": f"{type(error).__name__}: {error}", "traceback": traceback.format_exc()}
                if on_error == "fail":
                    raise PatchError(f"Patch step failed for {take_name}: {result['error']}") from error
                log(f"WARNING: patch step failed for {take_name}: {result['error']}")
            summary["steps"].append(result)
            summary["warnings"].extend(result.get("warnings") or [])
    summary["warnings"].extend(scene.warnings)
    for warning in summary["warnings"]:
        log(f"WARNING: {warning}")
    total = len(summary["steps"])
    summary["status"] = STATUS_APPLIED if not failed else (STATUS_FAILED if failed == total else STATUS_PARTIAL)
    return summary


def apply_manifest(manifest_path, take_names, seed=None, frame_range=None, host=None, log=print):
    """Finds the take in a manifest and applies its steps to the open scene.

    Args:
        manifest_path (str): Manifest file.
        take_names (list): Candidate take names (file stems), in priority order.
        seed (int, optional): Seed of the scene's generation (fingerprint).
        frame_range (list, optional): Scene frame range. Defaults to the playback range.
        host (SceneHost, optional): Host. Defaults to the active host.
        log (callable): Message printer.

    Returns:
        dict: Result of apply_entry, or {"status": "none"} when the take has no entry.
    """
    manifest = manifest_module.load_manifest(manifest_path)
    take_name, entry = manifest_module.find_take(manifest, take_names)
    if entry is None:
        return {"status": STATUS_NONE, "take": "", "steps": [], "warnings": [], "reason": "no patch for this take"}
    base_dir = os.path.dirname(os.path.abspath(manifest_path))
    on_error = str(manifest.get("on_error") or "warn")
    errors = manifest_module.validate_entry(entry, base_dir)
    if errors:
        message = f"Invalid patch for {take_name}: {'; '.join(errors)}"
        if on_error == "fail":
            raise PatchError(message)
        log(f"WARNING: {message}")
        return {"status": STATUS_FAILED, "take": take_name, "steps": [], "warnings": errors, "reason": message}
    template = load_template(entry.get("template") or manifest.get("template"), base_dir)
    return apply_entry(entry, base_dir, take_name=take_name, template=template, seed=seed, frame_range=frame_range,
                       on_error=on_error, host=host, log=log)
