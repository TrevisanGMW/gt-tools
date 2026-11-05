"""
Motion Evaluation Runner - Headless evaluation of many scene files with every output.

Uses only this package and Maya:

    1. Open (or import) each file.
    2. Evaluate it with a skeleton (built-in key, Custom Skeleton JSON, or none) and a preset.
    3. Write the enabled per-file outputs, and optionally the score attribute and a saved copy.
    4. Write the enabled whole-batch outputs.

Everything is driven by a JSON-compatible job dictionary (see create_job). The
simplest call is run(job): it finds the scenes in job["input_dir"], starts Maya
when needed, hides Maya's console output, prints progress, and writes every
enabled output. Jobs can be saved and loaded as JSON, so servers can run them
from the command line:

    mayapy -m <package>.motion_eval.runner job.json [file_a.ma file_b.ma]

Maya is imported lazily. Call run_job inside Maya or mayapy; use maya_session()
to initialize maya.standalone when needed.
"""

from .checks_base import MODE_BIPED, MODE_GENERAL, STATUS_FAILED
from . import batch_summary
from . import outputs
from . import presets
from . import sampling
from . import templates
from . import usd_scene
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
DEFAULT_EXTENSIONS = [".ma", ".mb", ".fbx", ".usd", ".usda", ".usdc"]
PATH_KEYS = ["input_dir", "output_dir", "result_path", "save_copy_dir"]
DEFAULT_JOB = {
    "version": JOB_VERSION,
    "title": outputs.DEFAULT_TITLE,
    "input_dir": "",
    "extensions": list(DEFAULT_EXTENSIONS),
    "include_subfolders": True,
    "skeleton": SKELETON_NONE,
    "preset": None,
    "range_mode": RANGE_PLAYBACK,
    "custom_start": 1,
    "custom_end": 100,
    "general_scope": SCOPE_ALL_JOINTS,
    "node_list": [],
    "load_mode": LOAD_MODE_OPEN,
    "align_up_axis": True,
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
    "result_path": "",
}


# ------------------------------------------------ Job Setup ------------------------------------------------
def create_job(**overrides):
    """Creates a job dictionary from the defaults.

    Args:
        **overrides: Top-level job keys to replace. "outputs" and "score" are merged with their defaults.

    Returns:
        dict: Job. Keys:
            title (str): Title used in batch summaries and graphs.
            input_dir (str): Folder searched for scenes by run() (and the command line without files).
            extensions (list): Scene extensions searched in input_dir.
            include_subfolders (bool): Also search the sub-folders of input_dir.
            skeleton (str, dict, or None): "none" (General checks only), a built-in key such as
                "maya_humanik", a Custom Skeleton JSON path, or a template dictionary. Any skeleton
                adds the Biped checks.
            preset (dict, str, or None): Preset dictionary, preset JSON path, or None for the defaults.
                The skeleton decides the mode (General only, or General + Biped).
            range_mode (str): "Playback Range", "Animation Range", "Keyed Range", or "Custom".
            custom_start / custom_end (int): Frames used by the "Custom" range.
            general_scope (str): Nodes evaluated without a skeleton: "All Joints", "Animated Transforms",
                or "Node List".
            node_list (list): Node names or wildcards for "Node List".
            load_mode (str): "open" the file, or "import" it into a new scene (for example FBX).
                USD files are always imported (see usd_scene).
            align_up_axis (bool): USD files: rotate and scale the file into the scene's up axis and
                unit before evaluating (for example a Z-up USD in a Y-up scene).
            output_dir (str): Folder receiving the outputs. Required when any output is on.
            outputs (dict): Output options (see outputs.DEFAULT_OUTPUT_OPTIONS).
            write_score (bool): Store the score as a Maya attribute (see score).
            score (dict): Score attribute options passed to scene_io.write_score.
            save_copy_dir (str): When set, save each scene (with the score) as a copy in this folder.
                Input files are never overwritten.
            result_path (str): When set, run() writes a JSON summary of the run here.
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


def resolve_job_paths(job, base_dir):
    """Makes the relative paths of a job absolute, relative to a base folder.

    Args:
        job (dict): Job.
        base_dir (str): Folder that relative paths start from (for example the script's or job file's folder).

    Returns:
        dict: Job copy with absolute folders, result path, and skeleton or preset file paths.
    """
    job = create_job(**job)
    if not base_dir:
        return job

    def make_absolute(value):
        """Joins a relative path to the base folder.

        Args:
            value (str): Path.

        Returns:
            str: Absolute path, or the value unchanged when empty or already absolute.
        """
        if not value or os.path.isabs(value):
            return value
        return os.path.normpath(os.path.join(base_dir, value))

    for key in PATH_KEYS:
        job[key] = make_absolute(job.get(key))
    for key in ("skeleton", "preset"):
        value = job.get(key)
        if isinstance(value, str) and value.lower().endswith(".json"):
            job[key] = make_absolute(value)
    return job


def find_scene_files(input_dir, extensions=None, include_subfolders=True):
    """Lists the scene files in a folder.

    Args:
        input_dir (str): Folder to search.
        extensions (list, optional): File extensions. Defaults to .ma, .mb, and .fbx.
        include_subfolders (bool): Also search sub-folders.

    Returns:
        list: Sorted file paths.
    """
    extensions = tuple(extension.lower() for extension in (extensions or DEFAULT_EXTENSIONS))
    found = []
    for folder, sub_folders, file_names in os.walk(input_dir):
        if not include_subfolders:
            sub_folders[:] = []
        found.extend(os.path.join(folder, name) for name in file_names if name.lower().endswith(extensions))
    return sorted(found, key=lambda path: path.lower())


def describe_job(job):
    """Describes what a job checks, for console headers.

    Args:
        job (dict): Job.

    Returns:
        str: For example "Skeleton: Maya HumanIK | 19 checks (17 on)".
    """
    skeleton_template = resolve_skeleton(job.get("skeleton"))
    resolved = presets.resolve_preset(resolve_job_preset(job.get("preset"), skeleton_template))
    checks = presets.get_checks_for_mode(resolved["mode"])
    enabled_count = sum(1 for check in checks if resolved["checks"][check.key]["enabled"])
    skeleton_name = skeleton_template["name"] if skeleton_template else "None (General checks only)"
    return f"Skeleton: {skeleton_name} | {len(checks)} checks ({enabled_count} on)"


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
    """Evaluates the scene open in Maya, resolving the frame range from range_mode.

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


def load_scene(file_path, load_mode=LOAD_MODE_OPEN, align_up_axis=True):
    """Opens or imports a scene file, discarding the current scene.

    Args:
        file_path (str): Scene path (.ma, .mb, .fbx, .usd, .usda, .usdc, ...).
        load_mode (str): "open" or "import" (into a new empty scene). USD files are always imported.
        align_up_axis (bool): USD only: rotate and scale the file into the scene's up axis and unit
            (see usd_scene.load_usd_scene).
    """
    import maya.cmds as cmds

    if usd_scene.is_usd_file(file_path):
        usd_scene.load_usd_scene(file_path, align_up_axis=align_up_axis)
        return

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


def build_error_result(file_path, exception=None):
    """Builds the result of a file that could not be evaluated.

    Args:
        file_path (str): Scene path.
        exception (Exception, optional): Error that stopped the file.

    Returns:
        dict: Result in the evaluate_file format with status "error".
    """
    return {"source": file_path, "status": STATUS_ERROR, "score": None, "report": None, "entry": None,
            "outputs": [], "score_write": None, "saved_copy": "", "warnings": [], "seconds": 0.0,
            "error": f"{type(exception).__name__}: {exception}" if exception else ""}


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
            "outputs" (written paths), "score_write", "saved_copy", "error" (message or ""), and "warnings".
    """
    from . import evaluation

    if preset is None:
        skeleton_template = resolve_skeleton(job.get("skeleton"))
        preset = resolve_job_preset(job.get("preset"), skeleton_template)
    result = build_error_result(file_path)
    started = time.time()
    try:
        load_scene(file_path, job.get("load_mode") or LOAD_MODE_OPEN, align_up_axis=job.get("align_up_axis", True))
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
    for label, step in (
        ("outputs", lambda: outputs.write_file_outputs(report, file_path, output_dir, job.get("outputs"),
                                                       relative_dir=relative_dir) if output_dir else []),
        ("score_write", lambda: write_job_score(report, job)),
        ("saved_copy", lambda: save_scene_copy(file_path, job["save_copy_dir"]) if job.get("save_copy_dir") else ""),
    ):
        try:
            result[label] = step()
        except Exception as exception:
            logger.debug(traceback.format_exc())
            result["warnings"].append(f"{label} failed: {type(exception).__name__}: {exception}")
    result.update({
        "status": report.get("status"),
        "score": report.get("score"),
        "report": evaluation.strip_series(report),
        "entry": batch_summary.build_batch_entry(report, file_path),
        "seconds": round(time.time() - started, 2),
    })
    return result


def write_job_score(report, job):
    """Writes the score attribute when the job asks for it.

    Args:
        report (dict): Evaluation report.
        job (dict): Job.

    Returns:
        dict or None: scene_io.write_score outcome, or None when score writing is off.
    """
    if not job.get("write_score"):
        return None
    from . import scene_io

    return scene_io.write_score(report, **(job.get("score") or {}))


def flush_stream(stream):
    """Flushes a console stream, ignoring streams that are missing or cannot be flushed.

    Args:
        stream (file): Stream such as sys.stdout. Can be None (for example under pythonw).
    """
    try:
        if stream:
            stream.flush()
    except (OSError, ValueError):
        pass


@contextlib.contextmanager
def quiet_output(enabled=True):
    """Hides everything printed to the console (including Maya's own messages) inside the block.

    Works at the operating-system level, so plugin and scene-loading messages printed by Maya
    are hidden too. Python's own sys.stdout and sys.stderr are swapped for a null stream as well:
    in a Windows console they write with console-only calls that fail on a redirected handle.
    Python exceptions still propagate normally.

    Args:
        enabled (bool): False runs the block without hiding anything.

    Yields:
        None
    """
    if not enabled:
        yield
        return
    saved_streams = (sys.stdout, sys.stderr)
    flush_stream(sys.stdout)
    flush_stream(sys.stderr)
    saved_handles = [os.dup(1), os.dup(2)]
    null_handle = os.open(os.devnull, os.O_WRONLY)
    null_stream = open(os.devnull, "w", encoding="utf-8")
    os.dup2(null_handle, 1)
    os.dup2(null_handle, 2)
    sys.stdout = sys.stderr = null_stream
    try:
        yield
    finally:
        sys.stdout, sys.stderr = saved_streams
        null_stream.close()
        os.dup2(saved_handles[0], 1)
        os.dup2(saved_handles[1], 2)
        for handle in saved_handles + [null_handle]:
            os.close(handle)


class ProgressPrinter:
    """Progress callbacks for run_job: a "running" line while a file evaluates, then its result."""

    def __init__(self, stream=None):
        """Initializes the printer. The clock starts with the first file, so Maya's startup is not counted.

        Args:
            stream (file, optional): Output stream. Defaults to sys.stdout.
        """
        self.stream = stream or sys.stdout
        self.started = None
        self.is_console = bool(getattr(self.stream, "isatty", lambda: False)())
        self.pending_width = 0

    def message(self, text):
        """Prints a status line such as "Starting Maya...".

        Args:
            text (str): Message.
        """
        self.stream.write(f"{text}\n")
        self.stream.flush()

    def start(self, index, total, file_path):
        """Shows which file is being evaluated, so a long file does not look frozen.

        In a console the line is replaced by the result line; in a log a separate line is written.

        Args:
            index (int): File number.
            total (int): File count.
            file_path (str): Scene being evaluated.
        """
        if self.started is None:
            self.started = time.time()
        width = len(str(total))
        text = f"[{index:>{width}}/{total}] running... {os.path.basename(file_path)}"
        if self.is_console:
            self.stream.write(text)
            self.pending_width = len(text)
        else:
            self.stream.write(f"{text}\n")
        self.stream.flush()

    def __call__(self, index, total, result):
        """Prints the result of one file.

        Args:
            index (int): File number.
            total (int): File count.
            result (dict): File result from evaluate_file.
        """
        if self.started is None:
            self.started = time.time()
        elapsed = time.time() - self.started
        seconds_left = elapsed / index * (total - index)
        detail = result["error"] or f"score {result['score']:>3}"
        width = len(str(total))
        text = (
            f"[{index:>{width}}/{total}] {total - index:>{width}} left, ~{format_duration(seconds_left)} | "
            f"{str(result['status']).upper():<7} {detail} | {os.path.basename(result['source'])}"
        )
        if self.pending_width:
            self.stream.write("\r" + " " * self.pending_width + "\r")
            self.pending_width = 0
        self.stream.write(f"{text}\n")
        self.stream.flush()


def format_duration(seconds):
    """Formats seconds as m:ss.

    Args:
        seconds (float): Duration.

    Returns:
        str: For example "1:05".
    """
    minutes, seconds = divmod(int(round(seconds)), 60)
    return f"{minutes}:{seconds:02d}"


def run_job(file_paths, job, source_root="", progress_callback=None, quiet=False, start_callback=None):
    """Evaluates every file of a job and writes all enabled outputs.

    Args:
        file_paths (list): Scene paths.
        job (dict): Job (see create_job).
        source_root (str, optional): Common input folder. With file folders on, each file's sub-folder
            under it is kept under the output folder.
        progress_callback (callable, optional): Called as progress_callback(index, total, result).
        quiet (bool): Hide Maya's console messages while files load and evaluate.
        start_callback (callable, optional): Called as start_callback(index, total, file_path)
            before each file is evaluated.

    Returns:
        dict: "results" (one per file, input order), "totals" (batch_summary.build_batch_totals),
            "batch_outputs" (written paths), "failed_files" (failed or errored paths), "errors", and
            "warnings" (outputs, score writes, or copies that could not be written; the run continues).

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
        if start_callback:
            start_callback(index, len(file_paths), file_path)
        try:
            with quiet_output(quiet):
                result = evaluate_file(file_path, job, skeleton_template, preset, relative_dir=relative_dir)
        except Exception as exception:
            logger.debug(traceback.format_exc())
            result = build_error_result(file_path, exception)
        results.append(result)
        if progress_callback:
            progress_callback(index, len(file_paths), result)
    entries = [result["entry"] for result in results if result["entry"]]
    batch_paths = []
    batch_warnings = []
    output_dir = str(job.get("output_dir") or "")
    if output_dir and outputs.has_batch_outputs(job.get("outputs")):
        settings = presets.resolve_preset(preset)["settings"]
        try:
            batch_paths = outputs.write_batch_outputs(entries, output_dir, job.get("outputs"), settings=settings,
                                                      title=job.get("title") or outputs.DEFAULT_TITLE)
        except Exception as exception:
            logger.debug(traceback.format_exc())
            batch_warnings.append(f"batch outputs failed: {type(exception).__name__}: {exception}")
    return {
        "results": results,
        "totals": batch_summary.build_batch_totals(entries),
        "batch_outputs": batch_paths,
        "failed_files": [
            result["source"] for result in results if result["status"] in (STATUS_FAILED, STATUS_ERROR)
        ],
        "errors": {result["source"]: result["error"] for result in results if result["error"]},
        "warnings": batch_warnings + [
            f"{result['source']}: {warning}" for result in results for warning in result["warnings"]
        ],
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


def run(job, base_dir="", file_paths=None, quiet=True, show_progress=True):
    """Runs a job end to end: find files, start Maya if needed, evaluate, write outputs, print a summary.

    Args:
        job (dict): Job (see create_job). Scenes come from job["input_dir"] unless file_paths is given.
        base_dir (str, optional): Folder that relative job paths start from.
        file_paths (list, optional): Scenes to evaluate instead of searching input_dir.
        quiet (bool): Hide Maya's console messages (scene loading, plugins, startup).
        show_progress (bool): Print a header, one line per file, and a final summary.

    Returns:
        dict: Value returned by run_job.

    Raises:
        ValueError: If the job is invalid or no scene was found.
    """
    job = resolve_job_paths(job, base_dir)
    errors = validate_job(job)
    if file_paths is None:
        if not job.get("input_dir") or not os.path.isdir(job["input_dir"]):
            errors.append(f"Input folder not found: {job.get('input_dir') or '(empty)'}")
        else:
            file_paths = find_scene_files(job["input_dir"], job.get("extensions"), job.get("include_subfolders"))
            if not file_paths:
                errors.append(f"No scene files found in {job['input_dir']}")
    if errors:
        raise ValueError("; ".join(errors))
    printer = ProgressPrinter() if show_progress else None
    if printer:
        printer.message(f"{job.get('title')}: {len(file_paths)} file(s) | {describe_job(job)}\n"
                        f"Output: {job.get('output_dir') or '(none)'}\n")
        if not is_inside_maya():
            printer.message("Starting Maya (this can take a few seconds)...")
    with maya_session(quiet=quiet):
        run_result = run_job(file_paths, job, source_root=job.get("input_dir") or "",
                             progress_callback=printer, quiet=quiet,
                             start_callback=printer.start if printer else None)
    if job.get("result_path"):
        outputs.write_json_file(job["result_path"], build_result_summary(run_result))
    if show_progress:
        sys.stdout.write("\n" + "\n".join(build_run_summary_lines(run_result, job)) + "\n")
    return run_result


def build_run_summary_lines(run_result, job=None):
    """Builds the short summary printed after a run.

    Args:
        run_result (dict): Value returned by run_job.
        job (dict, optional): Job, for the output and result paths.

    Returns:
        list: Text lines.
    """
    statuses = run_result["totals"]["statuses"]
    lines = [
        f"Done: {run_result['totals']['files']} evaluated | passed {statuses.get('passed', 0)} | "
        f"warning {statuses.get('warning', 0)} | failed {statuses.get('failed', 0)} | "
        f"errors {len(run_result['errors'])}"
    ]
    for source, message in run_result["errors"].items():
        lines.append(f"  error: {os.path.basename(source)}: {message}")
    for warning in run_result.get("warnings") or []:
        lines.append(f"  warning: {warning}")
    if job and job.get("output_dir"):
        lines.append(f"Outputs: {job['output_dir']}")
    if job and job.get("result_path"):
        lines.append(f"Result: {job['result_path']}")
    return lines


def is_inside_maya():
    """Checks whether Maya is already running in this process (GUI or maya.standalone).

    Returns:
        bool: True when maya.cmds is usable.
    """
    try:
        import maya.cmds as cmds

        return hasattr(cmds, "about") and bool(cmds.about(version=True))
    except Exception:
        return False


@contextlib.contextmanager
def maya_session(quiet=False):
    """Initializes maya.standalone when not already inside Maya, and uninitializes it afterwards.

    Args:
        quiet (bool): Hide Maya's startup and shutdown messages.

    Yields:
        bool: True when this context started maya.standalone.
    """
    started = False
    if not is_inside_maya():
        import maya.standalone

        with quiet_output(quiet):
            maya.standalone.initialize(name="python")
        started = True
    try:
        yield started
    finally:
        if started:
            import maya.standalone

            with quiet_output(quiet):
                maya.standalone.uninitialize()


def main(arguments=None):
    """Command line entry point: runs a job JSON and prints progress and a summary.

    Relative paths in the job start from the job file's folder. Without files, the scenes come
    from the job's input_dir.

    Args:
        arguments (list, optional): Command line arguments (defaults to sys.argv[1:]).

    Returns:
        int: Exit code (0 all passed or warned, 1 some failed or errored, 2 invalid job).
    """
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate animation files headlessly.")
    parser.add_argument("job", help="Job JSON file (see runner.create_job).")
    parser.add_argument("files", nargs="*", help="Scene files to evaluate. Defaults to the job's input_dir.")
    parser.add_argument("--result", default="", help="Optional JSON file receiving the run result.")
    parser.add_argument("--verbose", action="store_true", help="Show Maya's console messages.")
    options = parser.parse_args(arguments)
    job = load_job(options.job)
    if options.result:
        job["result_path"] = os.path.abspath(options.result)
    try:
        run_result = run(job, base_dir=os.path.dirname(os.path.abspath(options.job)),
                         file_paths=options.files or None, quiet=not options.verbose)
    except ValueError as exception:
        sys.stderr.write(f"Invalid job: {exception}\n")
        return 2
    return 1 if run_result["failed_files"] else 0


if __name__ == "__main__":
    sys.exit(main())
