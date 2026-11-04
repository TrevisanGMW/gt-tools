"""
Motion Evaluation Runner - Headless evaluation of many scene files with every output.

Runs the same steps as the Batch Processor "Validate Animation" task, using only
this package and Maya:

    1. Open (or import) each file.
    2. Evaluate it with a skeleton (built-in key, Custom Skeleton JSON, or none) and a preset.
    3. Write the enabled per-file outputs, and optionally the score attribute and a saved copy.
    4. Write the enabled whole-batch outputs.

Everything is driven by a JSON-compatible job dictionary (see create_job). Jobs
can be saved and loaded as JSON, so servers can run them from the command line:

    mayapy -m <package>.motion_eval.runner job.json file_a.ma file_b.ma

Maya is imported lazily. Call run_job inside Maya or mayapy; use maya_session()
to initialize maya.standalone when needed.
"""

from .checks_base import MODE_BIPED, MODE_GENERAL, STATUS_FAILED
from . import batch_summary
from . import outputs
from . import presets
from . import sampling
from . import templates
import contextlib
import json
import logging
import os
import sys
import time
import traceback

logger = logging.getLogger(__name__)

JOB_VERSION = 1
SKELETON_NONE = "none"
LOAD_MODE_OPEN = "open"
LOAD_MODE_IMPORT = "import"
STATUS_ERROR = "error"
RANGE_PLAYBACK = sampling.RANGE_PLAYBACK
SCOPE_ALL_JOINTS = sampling.SCOPE_ALL_JOINTS
DEFAULT_JOB = {
    "version": JOB_VERSION,
    "title": outputs.DEFAULT_TITLE,
    "skeleton": SKELETON_NONE,
    "preset": None,
    "range_mode": RANGE_PLAYBACK,
    "custom_start": 1,
    "custom_end": 100,
    "general_scope": SCOPE_ALL_JOINTS,
    "node_list": [],
    "load_mode": LOAD_MODE_OPEN,
    "output_dir": "",
    "outputs": dict(outputs.DEFAULT_OUTPUT_OPTIONS),
    "write_score": False,
    "score": {
        "target_mode": "dedicated_node",
        "node_name": "motionEval",
        "score_attribute": "motionScore",
        "report_attribute": "motionReport",
        "write_report": True,
        "write_policy": "overwrite",
    },
    "save_copy_dir": "",
}


# ------------------------------------------------ Job Setup ------------------------------------------------
def create_job(**overrides):
    """Creates a job dictionary from the defaults.

    Args:
        **overrides: Top-level job keys to replace. "outputs" and "score" are merged with their defaults.

    Returns:
        dict: Job. Keys:
            title (str): Title used in batch summaries and graphs.
            skeleton (str, dict, or None): "none" (General checks only), a built-in key such as
                "maya_humanik", a Custom Skeleton JSON path, or a template dictionary. Any skeleton
                adds the Biped checks.
            preset (dict, str, or None): Preset dictionary, preset JSON path, or None for the defaults.
                The skeleton decides the mode, like the Batch Processor task.
            range_mode (str): "Playback Range", "Animation Range", "Keyed Range", or "Custom".
            custom_start / custom_end (int): Frames used by the "Custom" range.
            general_scope (str): Nodes evaluated without a skeleton: "All Joints", "Animated Transforms",
                or "Node List".
            node_list (list): Node names or wildcards for "Node List".
            load_mode (str): "open" the file, or "import" it into a new scene (for example FBX).
            output_dir (str): Folder receiving the outputs. Required when any output is on.
            outputs (dict): Output options (see outputs.DEFAULT_OUTPUT_OPTIONS).
            write_score (bool): Store the score as a Maya attribute (see score).
            score (dict): Score attribute options passed to scene_io.write_score.
            save_copy_dir (str): When set, save each scene (with the score) as a copy in this folder.
                Input files are never overwritten.
    """
    job = json.loads(json.dumps(DEFAULT_JOB))
    for key, value in overrides.items():
        if key in ("outputs", "score") and isinstance(value, dict):
            job[key].update(value)
        else:
            job[key] = value
    return job


def load_job(file_path):
    """Loads a job JSON file and fills missing keys with the defaults.

    Args:
        file_path (str): Job JSON path.

    Returns:
        dict: Job.
    """
    with open(file_path, "r", encoding="utf-8") as job_file:
        return create_job(**json.load(job_file))


def save_job(job, file_path):
    """Saves a job as JSON.

    Args:
        job (dict): Job.
        file_path (str): Destination path.

    Returns:
        str: Written path.
    """
    return outputs.write_json_file(file_path, create_job(**job))


def resolve_skeleton(skeleton):
    """Resolves the job skeleton.

    Args:
        skeleton (str, dict, or None): "none", a built-in key, a Custom Skeleton JSON path, or a template.

    Returns:
        dict or None: Skeleton template, or None for General checks only.

    Raises:
        IOError, ValueError: If a Custom Skeleton file cannot be loaded.
    """
    if not skeleton or skeleton == SKELETON_NONE:
        return None
    if isinstance(skeleton, dict):
        return templates.normalize_template(skeleton)
    if skeleton in templates.BUILTIN_TEMPLATES:
        return templates.get_builtin_template(skeleton)
    return templates.load_template(skeleton)


def resolve_job_preset(preset, skeleton_template):
    """Resolves the job preset with the mode implied by the skeleton.

    Args:
        preset (dict, str, or None): Preset dictionary, preset JSON path, or None.
        skeleton_template (dict or None): Resolved skeleton.

    Returns:
        dict: Compact preset.

    Raises:
        IOError, ValueError: If a preset file cannot be loaded.
    """
    if isinstance(preset, str) and preset:
        preset = presets.load_preset(preset)
    resolved = presets.resolve_preset(preset or presets.DEFAULT_PRESET)
    resolved["mode"] = MODE_BIPED if skeleton_template else MODE_GENERAL
    return presets.compact_preset(resolved)


def validate_job(job):
    """Checks a job before running it.

    Args:
        job (dict): Job.

    Returns:
        list: Error messages. Empty when valid.
    """
    errors = []
    try:
        skeleton_template = resolve_skeleton(job.get("skeleton"))
        preset = resolve_job_preset(job.get("preset"), skeleton_template)
    except (IOError, OSError, ValueError) as exception:
        return [f"Skeleton or preset could not be loaded: {exception}"]
    errors.extend(presets.validate_preset(preset))
    if skeleton_template:
        errors.extend(templates.validate_template(skeleton_template, require_biped=True))
    if outputs.has_outputs(job.get("outputs")) and not str(job.get("output_dir") or "").strip():
        errors.append("Outputs are enabled but output_dir is empty.")
    if job.get("range_mode") == "Custom" and int(job.get("custom_end", 0)) <= int(job.get("custom_start", 0)):
        errors.append("The custom frame range needs an end frame after the start frame.")
    return errors


# ------------------------------------------------ Evaluation ------------------------------------------------
def evaluate_open_scene(preset, template=None, range_mode=RANGE_PLAYBACK, custom_start=None, custom_end=None,
                        general_scope=SCOPE_ALL_JOINTS, node_names=None, include_series=False):
    """Evaluates the scene open in Maya, resolving the frame range like the tools do.

    Args:
        preset (dict): Preset (its mode decides General or Biped checks).
        template (dict, optional): Skeleton template. Required for Biped mode.
        range_mode (str): One of sampling.RANGE_MODES.
        custom_start (int, optional): Start frame for the "Custom" range.
        custom_end (int, optional): End frame for the "Custom" range.
        general_scope (str): Node scope without a skeleton.
        node_names (list, optional): Nodes for the "Node List" scope.
        include_series (bool): Keep graph series (needed for per-file graphs).

    Returns:
        dict: Evaluation report.

    Raises:
        ValueError: If the scene cannot be evaluated.
    """
    from . import evaluation

    mode = presets.resolve_preset(preset)["mode"]
    node_names = list(node_names or [])
    keyed_nodes = None
    if range_mode == sampling.RANGE_KEYED:
        keyed_nodes = sampling.get_keyed_range_nodes(mode, template, general_scope, node_names)
    frame_range = sampling.resolve_frame_range(range_mode or sampling.RANGE_PLAYBACK, custom_start, custom_end,
                                               node_paths=keyed_nodes)
    return evaluation.evaluate_scene(
        preset=preset,
        template=template,
        frame_range=frame_range,
        general_scope=general_scope,
        node_names=node_names,
        include_series=include_series,
    )


def load_scene(file_path, load_mode=LOAD_MODE_OPEN):
    """Opens or imports a scene file, discarding the current scene.

    Args:
        file_path (str): Scene path (.ma, .mb, .fbx, ...).
        load_mode (str): "open" or "import" (into a new empty scene).
    """
    import maya.cmds as cmds

    if file_path.lower().endswith(".fbx") and not cmds.pluginInfo("fbxmaya", query=True, loaded=True):
        cmds.loadPlugin("fbxmaya", quiet=True)
    if load_mode == LOAD_MODE_IMPORT or not file_path.lower().endswith((".ma", ".mb")):
        cmds.file(new=True, force=True)
        cmds.file(file_path, i=True, force=True)
    else:
        cmds.file(file_path, open=True, force=True, prompt=False)


def save_scene_copy(source_path, copy_dir):
    """Saves the open scene as a copy, never over the input file.

    Args:
        source_path (str): Evaluated input path.
        copy_dir (str): Destination folder.

    Returns:
        str: Saved path.

    Raises:
        RuntimeError: If the copy would overwrite the input.
    """
    import maya.cmds as cmds

    os.makedirs(copy_dir, exist_ok=True)
    base_name = os.path.splitext(os.path.basename(source_path))[0]
    target_path = os.path.join(copy_dir, f"{base_name}.ma")
    if os.path.normcase(os.path.abspath(target_path)) == os.path.normcase(os.path.abspath(source_path)):
        raise RuntimeError(f"Refusing to overwrite the input file: {source_path}")
    cmds.file(rename=target_path)
    cmds.file(save=True, force=True, type="mayaAscii")
    return target_path


def evaluate_file(file_path, job, skeleton_template=None, preset=None, relative_dir=""):
    """Evaluates one file and writes its per-file outputs.

    Args:
        file_path (str): Scene path.
        job (dict): Job.
        skeleton_template (dict, optional): Resolved skeleton (resolved from the job when omitted).
        preset (dict, optional): Resolved preset (resolved from the job when omitted).
        relative_dir (str, optional): Source sub-folder kept under the output folder.

    Returns:
        dict: Result with "source", "status", "score", "report" (without series), "entry" (batch entry),
            "outputs" (written paths), "score_write", "saved_copy", and "error" (message or "").
    """
    from . import evaluation

    if preset is None:
        skeleton_template = resolve_skeleton(job.get("skeleton"))
        preset = resolve_job_preset(job.get("preset"), skeleton_template)
    result = {"source": file_path, "status": STATUS_ERROR, "score": None, "report": None, "entry": None,
              "outputs": [], "score_write": None, "saved_copy": "", "error": "", "seconds": 0.0}
    started = time.time()
    try:
        load_scene(file_path, job.get("load_mode") or LOAD_MODE_OPEN)
        report = evaluate_open_scene(
            preset,
            template=skeleton_template,
            range_mode=job.get("range_mode") or RANGE_PLAYBACK,
            custom_start=job.get("custom_start"),
            custom_end=job.get("custom_end"),
            general_scope=job.get("general_scope") or SCOPE_ALL_JOINTS,
            node_names=job.get("node_list") or [],
            include_series=outputs.needs_series(job.get("outputs")),
        )
    except Exception as exception:
        logger.debug(traceback.format_exc())
        result["error"] = f"{type(exception).__name__}: {exception}"
        result["seconds"] = round(time.time() - started, 2)
        return result
    output_dir = str(job.get("output_dir") or "")
    if output_dir:
        result["outputs"] = outputs.write_file_outputs(report, file_path, output_dir, job.get("outputs"),
                                                       relative_dir=relative_dir)
    if job.get("write_score"):
        from . import scene_io

        result["score_write"] = scene_io.write_score(report, **(job.get("score") or {}))
    if job.get("save_copy_dir"):
        result["saved_copy"] = save_scene_copy(file_path, job["save_copy_dir"])
    result.update({
        "status": report.get("status"),
        "score": report.get("score"),
        "report": evaluation.strip_series(report),
        "entry": batch_summary.build_batch_entry(report, file_path),
        "seconds": round(time.time() - started, 2),
    })
    return result


def run_job(file_paths, job, source_root="", progress_callback=None):
    """Evaluates every file of a job and writes all enabled outputs.

    Args:
        file_paths (list): Scene paths.
        job (dict): Job (see create_job).
        source_root (str, optional): Common input folder. With file folders on, each file's sub-folder
            under it is kept under the output folder.
        progress_callback (callable, optional): Called as progress_callback(index, total, result).

    Returns:
        dict: "results" (one per file, input order), "totals" (batch_summary.build_batch_totals),
            "batch_outputs" (written paths), "failed_files" (failed or errored paths), and "errors".

    Raises:
        ValueError: If the job is invalid.
    """
    job = create_job(**job)
    errors = validate_job(job)
    if errors:
        raise ValueError(errors[0])
    skeleton_template = resolve_skeleton(job.get("skeleton"))
    preset = resolve_job_preset(job.get("preset"), skeleton_template)
    results = []
    for index, file_path in enumerate(file_paths, start=1):
        relative_dir = get_relative_dir(file_path, source_root)
        result = evaluate_file(file_path, job, skeleton_template, preset, relative_dir=relative_dir)
        results.append(result)
        if progress_callback:
            progress_callback(index, len(file_paths), result)
    entries = [result["entry"] for result in results if result["entry"]]
    batch_paths = []
    output_dir = str(job.get("output_dir") or "")
    if output_dir and outputs.has_batch_outputs(job.get("outputs")):
        settings = presets.resolve_preset(preset)["settings"]
        batch_paths = outputs.write_batch_outputs(entries, output_dir, job.get("outputs"), settings=settings,
                                                  title=job.get("title") or outputs.DEFAULT_TITLE)
    return {
        "results": results,
        "totals": batch_summary.build_batch_totals(entries),
        "batch_outputs": batch_paths,
        "failed_files": [
            result["source"] for result in results if result["status"] in (STATUS_FAILED, STATUS_ERROR)
        ],
        "errors": {result["source"]: result["error"] for result in results if result["error"]},
    }


def get_relative_dir(file_path, source_root):
    """Gets the sub-folder of a file under a root folder.

    Args:
        file_path (str): File path.
        source_root (str): Root folder, or empty.

    Returns:
        str: Relative folder, or an empty string when outside the root or without a root.
    """
    if not source_root:
        return ""
    try:
        relative = os.path.relpath(os.path.dirname(os.path.abspath(file_path)), os.path.abspath(source_root))
    except ValueError:
        return ""
    if relative == "." or relative.startswith(".."):
        return ""
    return relative


def build_result_summary(run):
    """Builds a JSON-ready copy of a run result without the full per-file reports.

    Args:
        run (dict): Value returned by run_job.

    Returns:
        dict: Totals, batch output paths, failed files, errors, and one compact result per file
            (source, status, score, error, outputs, seconds, and the batch "entry").
    """
    summary = {key: value for key, value in run.items() if key != "results"}
    summary["results"] = [
        {key: value for key, value in result.items() if key != "report"} for result in run.get("results") or []
    ]
    return summary


@contextlib.contextmanager
def maya_session():
    """Initializes maya.standalone when not already inside Maya, and uninitializes it afterwards.

    Yields:
        bool: True when this context started maya.standalone.
    """
    started = False
    try:
        import maya.cmds as cmds

        inside_maya = hasattr(cmds, "about") and bool(cmds.about(version=True))
    except Exception:
        inside_maya = False
    if not inside_maya:
        import maya.standalone

        maya.standalone.initialize(name="python")
        started = True
    try:
        yield started
    finally:
        if started:
            import maya.standalone

            maya.standalone.uninitialize()


def main(arguments=None):
    """Command line entry point: runs a job JSON on the given files and prints a summary.

    Args:
        arguments (list, optional): Command line arguments (defaults to sys.argv[1:]).

    Returns:
        int: Exit code (0 all passed or warned, 1 some failed or errored, 2 invalid job).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate animation files headlessly.")
    parser.add_argument("job", help="Job JSON file (see runner.create_job).")
    parser.add_argument("files", nargs="+", help="Scene files to evaluate.")
    parser.add_argument("--source-root", default="", help="Common input folder (keeps sub-folders in outputs).")
    parser.add_argument("--result", default="", help="Optional JSON file receiving the run result.")
    options = parser.parse_args(arguments)
    job = load_job(options.job)

    def print_progress(index, total, result):
        """Prints one line per evaluated file.

        Args:
            index (int): File number.
            total (int): File count.
            result (dict): File result.
        """
        detail = result["error"] or f"score {result['score']}"
        sys.stdout.write(f"[{index}/{total}] {result['status']}: {result['source']} ({detail})\n")
        sys.stdout.flush()

    with maya_session():
        try:
            run = run_job(options.files, job, source_root=options.source_root, progress_callback=print_progress)
        except ValueError as exception:
            sys.stderr.write(f"Invalid job: {exception}\n")
            return 2
    if options.result:
        outputs.write_json_file(options.result, build_result_summary(run))
    return 1 if run["failed_files"] else 0


if __name__ == "__main__":
    sys.exit(main())
