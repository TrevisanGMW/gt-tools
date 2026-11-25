"""
Patch preview: loads a scene, scores it, applies a patch in memory, and scores it again. Nothing
is saved, so it is a quick way to compare fixes and presets before committing to one.

    from motion_eval.repairs import preview
    result = preview.preview_file("walk_042_v003.usd", {"steps": [...]}, job)
    print(result["before"]["score"], "->", result["after"]["score"])

Command line (inside mayapy):

    mayapy -m motion_eval.repairs.preview --job job.json --source walk.usd --patch patch.json --out out.json

``job`` uses the runner job keys (skeleton, preset, range_mode, custom_start, custom_end,
general_scope, node_list, load_mode, align_up_axis); see runner.create_job.
"""

import argparse
import json
import os
import sys

from .. import runner
from . import apply

ISSUE_STATUSES = ("failed", "warning")


def summarize_report(report):
    """Keeps the parts of an evaluation report a preview compares.

    Args:
        report (dict): Evaluation report.

    Returns:
        dict: {"score", "status", "checks": {key: {"score", "status", "spans", "offenders"}}}.
    """
    checks = {}
    for check in report.get("checks") or []:
        if check.get("status") in (None, "disabled"):
            continue
        checks[check.get("key")] = {
            "score": check.get("score"), "status": check.get("status"), "spans": check.get("spans") or [],
            "offenders": [offender.get("name") for offender in check.get("offenders") or []],
        }
    return {"score": report.get("score"), "status": report.get("status"), "checks": checks}


def compare_checks(before, after):
    """Lists the checks whose score changed, worst drop first.

    Args:
        before (dict): Summary before the patch.
        after (dict): Summary after the patch.

    Returns:
        list: {"key", "before", "after", "change", "status"} dictionaries.
    """
    changes = []
    for key, check in after["checks"].items():
        old = (before["checks"].get(key) or {}).get("score")
        new = check.get("score")
        if old is None or new is None or old == new:
            continue
        changes.append({"key": key, "before": old, "after": new, "change": round(new - old, 2),
                        "status": check.get("status")})
    return sorted(changes, key=lambda item: item["change"])


def evaluate_loaded(job, template, preset):
    """Evaluates the open scene with a job's range settings.

    Args:
        job (dict): Job.
        template (dict or None): Skeleton template.
        preset (dict): Resolved preset.

    Returns:
        dict: Evaluation report.
    """
    return runner.evaluate_open_scene(
        preset, template=template, range_mode=job.get("range_mode") or runner.RANGE_PLAYBACK,
        custom_start=job.get("custom_start"), custom_end=job.get("custom_end"),
        general_scope=job.get("general_scope") or runner.SCOPE_ALL_JOINTS, node_names=job.get("node_list") or [])


def preview_file(source_path, entry, job, base_dir="", log=None):
    """Scores a scene before and after applying a patch entry in memory.

    The entry's fingerprint (seed, frame_range) is ignored: the preview always applies.

    Args:
        source_path (str): Scene file to load.
        entry (dict): Take entry ({"steps": [...], optional "template"}).
        job (dict): Runner job with the scoring settings.
        base_dir (str): Folder for relative script and template paths.
        log (callable, optional): Message printer. Defaults to silence.

    Returns:
        dict: {"source", "before", "after", "changes", "patch"}.
    """
    template = runner.resolve_skeleton(job.get("skeleton"))
    preset = runner.resolve_job_preset(job.get("preset"), template)
    runner.load_scene(source_path, job.get("load_mode") or runner.LOAD_MODE_OPEN,
                      align_up_axis=job.get("align_up_axis", True))
    before = summarize_report(evaluate_loaded(job, template, preset))
    patch_entry = dict((key, value) for key, value in entry.items() if key not in ("seed", "frame_range"))
    patch_template = apply.load_template(patch_entry.get("template"), base_dir or ".") or template
    patch = apply.apply_entry(patch_entry, base_dir or ".", take_name=os.path.basename(source_path),
                              template=patch_template, on_error="warn", log=log or (lambda text: None))
    after = summarize_report(evaluate_loaded(job, template, preset))
    steps = [{"step": step.get("step"), "status": step.get("status"), "keys": step.get("keys", 0),
              "error": step.get("error", "")} for step in patch["steps"]]
    return {"source": source_path, "before": before, "after": after, "changes": compare_checks(before, after),
            "patch": {"status": patch["status"], "steps": steps, "warnings": patch["warnings"]}}


def load_json(file_path):
    """Reads a JSON file.

    Args:
        file_path (str): Path.

    Returns:
        object: Parsed data.
    """
    with open(file_path, "r", encoding="utf-8") as stream:
        return json.load(stream)


def main(argv=None):
    """Runs a preview from the command line and writes the result as JSON.

    Args:
        argv (list, optional): Arguments (defaults to sys.argv[1:]).

    Returns:
        int: Exit code (0 on success, 1 when the preview failed).
    """
    parser = argparse.ArgumentParser(description="Score a scene before and after a patch (nothing is saved).")
    parser.add_argument("--job", required=True, help="Runner job JSON with the scoring settings.")
    parser.add_argument("--source", required=True, help="Scene file to load.")
    parser.add_argument("--patch", required=True, help='Patch JSON: {"steps": [...]} or a list of steps.')
    parser.add_argument("--out", required=True, help="Result JSON path.")
    parser.add_argument("--base-dir", default="", help="Folder for relative script and template paths.")
    arguments = parser.parse_args(argv)
    entry = load_json(arguments.patch)
    if isinstance(entry, list):
        entry = {"steps": entry}
    try:
        with runner.maya_session(quiet=True):
            result = preview_file(arguments.source, entry, load_json(arguments.job),
                                  base_dir=arguments.base_dir or os.path.dirname(os.path.abspath(arguments.patch)))
        code = 0
    except Exception as error:
        result = {"source": arguments.source, "error": f"{type(error).__name__}: {error}"}
        code = 1
    with open(arguments.out, "w", encoding="utf-8") as stream:
        json.dump(result, stream, indent=2)
    return code


if __name__ == "__main__":
    sys.exit(main())
