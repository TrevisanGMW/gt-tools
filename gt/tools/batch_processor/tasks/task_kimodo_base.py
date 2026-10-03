"""Small shared batch adapter for the two Kimodo tasks."""

import os
import re
import string
import hashlib
import json
import math
import shutil
import tempfile
from functools import partial
from contextlib import ExitStack, contextmanager
from gt.core import io as core_io
from gt.tools.batch_processor import batch_processor_task_base as base
from gt.tools.batch_processor.tasks.task_clip import ClipSnapshotFileLock
from gt.ui import resource_library as resources
from gt.utils import kimodo


read_json = partial(core_io.read_json_dict, raise_errors=True)

MOTION_TEXT_EXAMPLE = '[[2, "A person starts to walk"], [1, "A person comes to a stop"]]'
RUNTIME_KEYS = {
    "input-file",
    "input-string", "input-string-index", "input-file-name", "input-file-stem", "input-file-path",
}
VARIABLE_PATTERN = re.compile(r"\{([\w-]+)\}")


class TaskKimodoBase(base.BatchTask):
    """Adds filtered discovery, output ownership checks, and per-item recovery paths."""

    icon = resources.Icon.tool_kimodo_generator
    category = "Animation"
    category_icon = resources.Icon.root_animation
    extensions = ()
    output_section_name = "Output Naming"

    def __init__(self, *args, **kwargs):
        """Migrates only the old default labels, preserving custom task names and IDs.

        Args:
            *args: Standard batch task arguments.
            **kwargs: Standard batch task keyword arguments.
        """
        super().__init__(*args, **kwargs)
        legacy = {"Create Kimodo Definitions": "Kimodo Definition", "Generate Kimodo Animations": "Kimodo Generate"}
        self.display_name = legacy.get(self.display_name, self.display_name)

    def get_default_settings(self):
        """Returns common safe task settings.

        Returns:
            dict: Settings for incoming files and separate outputs.
        """
        settings = super().get_default_settings()
        settings.update(source_mode=base.SOURCE_MODE_INCOMING, name_pattern="{source}", filename_suffix="",
                        source_include_subdirectories=True, include_version_suffix=True,
                        purge_cache_on_success=True, purge_coordination_on_finish=True)
        return settings

    def discover_source_files(self, project, task_index=None):
        """Discovers supported files, excluding owned recovery and artifact directories.

        Args:
            project (BatchProcessorModel): Owning project.
            task_index (int, optional): Task index.

        Returns:
            list: Filtered source paths.
        """
        paths = super().discover_source_files(project, task_index)
        return [path for path in paths if os.path.splitext(path)[1].lower() in self.extensions
                and not any(part in (".kimodo-cache", ".kimodo-coordination") or part.endswith("_artifacts")
                            for part in path.replace("\\", "/").split("/"))]

    def validate(self, project):
        """Validates common settings without loading a scene or contacting a server.

        Args:
            project (BatchProcessorModel): Owning project.

        Returns:
            ValidationResult: Validation diagnostics.
        """
        result = base.ValidationResult()
        if not isinstance(self.settings.get("purge_coordination_on_finish", True), bool):
            self.add_area_error(result, "Recovery", "Purge coordination folders must be enabled or disabled.")
        if not self.writes_to_target_path():
            self.add_area_error(result, "Task Setup", "Kimodo tasks require a separate target folder.")
        try:
            if not isinstance(self.settings.get("include_version_suffix", True), bool):
                self.add_area_error(result, self.output_section_name,
                                    "Include version suffix must be enabled or disabled.")
            output_name(self.settings["name_pattern"], "example",
                        suffix=self.settings.get("filename_suffix", ""),
                        append_variation_suffix=self.settings.get("include_version_suffix", True))
        except (ValueError, TypeError, KeyError) as error:
            self.add_area_error(result, self.output_section_name, error)
        return result

    @staticmethod
    def add_area_error(result, area, message):
        """Adds a validation error labeled with the matching UI area.

        Args:
            result (ValidationResult): Result receiving the error.
            area (str): Collapsible area or task section name.
            message (object): Error text.
        """
        result.add_error(f"[{area}] {message}")

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Rejects duplicate output stems before processing incoming files.

        Args:
            work_items (list): Incoming work items.
            project (BatchProcessorModel): Owning project.
            step_output_dir (str): Resolved target folder.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Collision and source diagnostics.
        """
        result = base.ValidationResult()
        seen = {}
        for item in work_items:
            try:
                self.check_source(item)
            except (ValueError, OSError) as error:
                self.add_area_error(result, "Input", error)
                continue

            definition = None
            seed = 0
            samples = 1
            if ".json" in self.extensions:
                try:
                    definition = kimodo.normalize_definition(read_json(item.current_path))
                    seed = definition["parameters"].get("seed")
                    if seed is None:
                        seed = int(fingerprint(os.path.normcase(os.path.abspath(item.current_path)))[:8], 16)
                    samples = int(definition["parameters"].get("num_samples", 1))
                except (ValueError, TypeError, KeyError, OSError) as error:
                    self.add_area_error(result, "Input Definition", error)
                    continue
            elif any(extension in self.extensions for extension in (".ma", ".mb")):
                identity = base.get_work_item_relative_path(item) or item.current_path
                seed_policy = self.settings.get("seed_policy", "per_file")
                if seed_policy == "fixed":
                    seed = int(self.settings.get("base_seed", 0))
                elif seed_policy == "per_file":
                    seed = int(fingerprint([int(self.settings.get("base_seed", 0)), identity, 1])[:8], 16)
                else:
                    seed = int(fingerprint([self.id, identity])[:8], 16)
            try:
                path = self.output_path(item, step_output_dir, seed=seed, samples=samples, definition=definition)
            except (ValueError, OSError) as error:
                self.add_area_error(result, self.output_section_name, error)
                continue
            key = os.path.normcase(path)
            if key in seen:
                self.add_area_error(
                    result, self.output_section_name,
                    f"Kimodo output collision: {seen[key]} and {item.current_path}: {path}")
            seen[key] = item.current_path
        return result

    def check_source(self, item):
        """Checks input type and existence before any output work.

        Args:
            item (WorkItem): Incoming item.
        """
        if os.path.splitext(item.current_path)[1].lower() not in self.extensions:
            raise ValueError(f"Unsupported Kimodo task input: {item.current_path}")
        if not os.path.isfile(item.current_path):
            raise ValueError(f"Input file does not exist: {item.current_path}")
        if not self.writes_to_target_path():
            raise ValueError("Kimodo tasks cannot modify inputs in place or pass through.")

    def output_path(self, item, directory, variation=1, seed=0, sample=1, samples=1, definition=None):
        """Builds an owned output path while preserving source-relative folders.

        Args:
            item (WorkItem): Incoming item.
            directory (str): Target root.
            variation (int): Variation index.
            seed (int): Resolved seed.
            sample (int): Sample index.
            samples (int): Number of samples.
            definition (dict, optional): Resolved Kimodo definition for descriptive name tokens.

        Returns:
            str: Output path.
        """
        source_name = os.path.splitext(os.path.basename(item.current_path))[0]
        if self.extensions == (".json",) and not self.settings.get("include_version_suffix", True):
            source_name = re.sub(r"_v[0-9]+$", "", source_name, flags=re.IGNORECASE)
        name = output_name(
            self.settings["name_pattern"], source_name,
            variation, seed, sample, int(self.settings.get("variations", 1)), samples,
            suffix=self.settings.get("filename_suffix", ""), definition=definition,
            append_variation_suffix=self.settings.get("include_version_suffix", True))
        extension = self.settings.get("output_extension", ".json")
        path = base.build_work_item_output_path(item, directory, name + extension)
        if os.path.normcase(os.path.abspath(path)) == os.path.normcase(os.path.abspath(item.current_path)):
            raise ValueError("Output would overwrite the input file.")
        return path

    def recovery_directory(self, item, directory):
        """Returns stable recovery storage for one task/input pair.

        Args:
            item (WorkItem): Incoming item.
            directory (str): Output root.

        Returns:
            str: Absolute cache folder.
        """
        identity = fingerprint([self.id, os.path.normcase(os.path.abspath(item.current_path))])[:24]
        return os.path.join(os.path.abspath(directory), ".kimodo-cache", identity)

    @contextmanager
    def recovery_lock(self, item, directory, timeout_seconds=3600, context=None):
        """Locks one task/input independently of its removable recovery folder.

        Args:
            item (WorkItem): Input whose recovery data is being accessed.
            directory (str): Output root.
            timeout_seconds (float, optional): Maximum time to wait for the lock.
            context (dict, optional): Runner context controlling end-of-run cleanup.

        Yields:
            ClipSnapshotFileLock: Stable coordination lock for this task/input pair.
        """
        identity = fingerprint([self.id, os.path.normcase(os.path.abspath(item.current_path))])[:24]
        with coordination_guard(directory):
            root = checked_coordination_root(directory)
            lock = ClipSnapshotFileLock(os.path.join(root, "locks", identity), timeout_seconds=timeout_seconds)
            lock.acquire()
        try:
            yield lock
        finally:
            lock.release()
            if (self.settings.get("purge_coordination_on_finish", True)
                    and not (context or {}).get("defer_kimodo_coordination_cleanup")):
                try:
                    purge_coordination(directory)
                except (OSError, RuntimeError, ValueError) as error:
                    report_message(context, f"Could not purge coordination folder: {error}")

    def purge_recovery_directory(self, item, directory, cache):
        """Removes one recovery folder and prunes the cache root when it is safe.

        Args:
            item (WorkItem): Input owning the recovery data.
            directory (str): Output root.
            cache (str): Recovery folder to remove.

        Raises:
            ValueError: If the path is not this task's expected recovery folder.
        """
        expected = os.path.normcase(os.path.abspath(self.recovery_directory(item, directory)))
        cache_path = os.path.normcase(os.path.abspath(cache))
        if cache_path != expected or os.path.islink(cache_path):
            raise ValueError(f"Refusing to purge an unexpected Kimodo cache path: {cache}")
        if os.path.isdir(cache_path):
            shutil.rmtree(cache_path)
        self.prune_recovery_root(directory)

    def prune_recovery_root(self, directory):
        """Removes an empty or legacy-control-only recovery root safely.

        Shared coordination has moved to ``.kimodo-coordination``. Older
        versions kept persistent locks and output claims inside
        ``.kimodo-cache``; migrate those claims before removing their legacy
        registry. A cache root containing another input's recovery folder is
        left untouched, so concurrent workers retain their in-progress data.

        Args:
            directory (str): Output root containing the recovery directory.
        """
        cache_root = os.path.join(os.path.abspath(directory), ".kimodo-cache")
        if not os.path.isdir(cache_root) or os.path.islink(cache_root):
            return
        coordination_root = os.path.join(os.path.abspath(directory), ".kimodo-coordination")
        maintenance_lock = os.path.join(coordination_root, "maintenance", "legacy-cache")
        with ClipSnapshotFileLock(maintenance_lock):
            if not os.path.isdir(cache_root) or os.path.islink(cache_root):
                return
            controls = {"locks", "outputs"}
            try:
                entries = set(os.listdir(cache_root))
            except OSError:
                return
            if entries - controls:
                return
            legacy_outputs = os.path.join(cache_root, "outputs")
            if os.path.isdir(legacy_outputs):
                self.migrate_legacy_output_claims(legacy_outputs, coordination_root)
                shutil.rmtree(legacy_outputs)
            legacy_locks = os.path.join(cache_root, "locks")
            if os.path.isdir(legacy_locks):
                shutil.rmtree(legacy_locks)
            try:
                os.rmdir(cache_root)
            except OSError:
                # Another worker may have recreated its per-input folder after
                # the contents check. Removing only an empty directory is safe.
                pass

    def migrate_legacy_cache_claims(self, directory):
        """Preserves old output reservations before they can block cache cleanup.

        Args:
            directory (str): Output root containing a possible legacy cache.
        """
        cache_root = os.path.join(os.path.abspath(directory), ".kimodo-cache")
        legacy_outputs = os.path.join(cache_root, "outputs")
        if not os.path.isdir(legacy_outputs) or os.path.islink(cache_root):
            return
        if os.path.islink(legacy_outputs):
            raise ValueError(f"Refusing to migrate a linked Kimodo output registry: {legacy_outputs}")
        coordination_root = os.path.join(os.path.abspath(directory), ".kimodo-coordination")
        maintenance_lock = os.path.join(coordination_root, "maintenance", "legacy-cache")
        with ClipSnapshotFileLock(maintenance_lock):
            if not os.path.isdir(legacy_outputs):
                return
            self.migrate_legacy_output_claims(legacy_outputs, coordination_root)
            shutil.rmtree(legacy_outputs)

    @staticmethod
    def migrate_legacy_output_claims(legacy_directory, coordination_root):
        """Copies legacy output claims into the persistent coordination registry.

        Args:
            legacy_directory (str): Old claim folder inside ``.kimodo-cache``.
            coordination_root (str): New sibling coordination folder.

        Raises:
            ValueError: If a legacy claim conflicts with a current reservation.
        """
        if os.path.islink(legacy_directory):
            raise ValueError(f"Refusing to migrate a linked Kimodo output registry: {legacy_directory}")
        output_directory = os.path.join(coordination_root, "outputs")
        for filename in os.listdir(legacy_directory):
            if not filename.lower().endswith(".json"):
                continue
            legacy_path = os.path.join(legacy_directory, filename)
            if not os.path.isfile(legacy_path):
                continue
            claim = read_json(legacy_path)
            claim_path = os.path.join(output_directory, filename)
            with ClipSnapshotFileLock(claim_path):
                if os.path.isfile(claim_path):
                    current = read_json(claim_path)
                    if current.get("source") != claim.get("source"):
                        raise ValueError(f"Legacy output reservation conflicts with {claim.get('output')}.")
                else:
                    write_record(claim_path, claim)

    def cleanup_recovery_cache(self, item, directory, cache, context=None):
        """Purges successful per-input recovery data when enabled, reporting cleanup failures.

        Args:
            item (WorkItem): Input owning the recovery data.
            directory (str): Output root.
            cache (str): Per-input recovery folder.
            context (dict, optional): Worker runtime context.
        """
        if self.settings.get("purge_cache_on_success", True) is not True:
            return
        try:
            self.purge_recovery_directory(item, directory, cache)
        except (OSError, RuntimeError, ValueError) as error:
            report_message(context, f"Could not purge recovery cache: {error}")

    def reserve_outputs(self, item, paths, directory):
        """Claims output names across workers before submitting expensive generation.

        Args:
            item (WorkItem): Input owning these outputs.
            paths (list): Planned output paths.
            directory (str): Target root containing the ownership registry.
        """
        self.migrate_legacy_cache_claims(directory)
        owner = os.path.normcase(os.path.abspath(item.current_path))
        for path in paths:
            key = fingerprint(os.path.normcase(os.path.abspath(path)))
            claim_path = os.path.join(directory, ".kimodo-coordination", "outputs", f"{key}.json")
            with ClipSnapshotFileLock(claim_path):
                if os.path.isfile(claim_path):
                    claim = read_json(claim_path)
                    if claim["source"] != owner:
                        raise ValueError(f"Output collision: {path} is reserved for {claim['source']}.")
                else:
                    write_record(claim_path, {"source": owner, "output": path})

    def output_item(self, item, path, metadata):
        """Preserves upstream metadata while attaching Kimodo provenance.

        Args:
            item (WorkItem): Input item.
            path (str): Output path.
            metadata (dict): New provenance.

        Returns:
            WorkItem: Downstream file item.
        """
        values = dict(item.metadata)
        values.update(last_task_id=self.id, last_task_type=self.task_type, kimodo=metadata)
        return base.WorkItem(item.source_path, path, values)


def coordination_guard(directory):
    """Returns a stable lock outside the output tree to protect lock-file lifetimes.

    Args:
        directory (str): Explicit output directory.

    Returns:
        ClipSnapshotFileLock: Guard shared by entrants and coordination cleanup.
    """
    if not directory or not os.path.isabs(directory):
        raise ValueError("Kimodo coordination requires an explicit absolute output directory.")
    identity = os.path.normcase(os.path.realpath(directory))
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return ClipSnapshotFileLock(os.path.join(tempfile.gettempdir(), "gt-kimodo-guards", digest))


def checked_coordination_root(directory):
    """Resolves the task-owned folder, rejecting links outside the output directory.

    Args:
        directory (str): Output directory.

    Returns:
        str: Absolute coordination folder.

    Raises:
        ValueError: If coordination was redirected through a symbolic link or junction.
    """
    if not directory or not os.path.isabs(directory):
        raise ValueError("Kimodo coordination cleanup requires an explicit absolute output directory.")
    output_root = os.path.realpath(os.path.abspath(directory))
    root = os.path.join(output_root, ".kimodo-coordination")
    if os.path.normcase(os.path.realpath(root)) != os.path.normcase(root):
        raise ValueError(f"Refusing linked Kimodo coordination folder: {root}")
    return root


def purge_coordination(directory):
    """Removes recognized coordination files only when no worker holds their locks.

    Entrants acquire the external guard before opening their per-input lock. The
    guard stays stable after cleanup, preventing waiting workers on POSIX from
    acquiring a deleted lock inode while a new worker uses a different one.

    Args:
        directory (str): Output directory whose coordination files are disposable.

    Returns:
        bool: Whether the folder was removed or was already absent.
    """
    with coordination_guard(directory):
        root = checked_coordination_root(directory)
        if not os.path.exists(root):
            return True
        patterns = {"locks": r"[0-9a-f]{24}\.lock",
                    "outputs": r"[0-9a-f]{64}\.json(?:\.lock)?",
                    "maintenance": r"legacy-cache\.lock"}
        paths = []
        folders = []
        with os.scandir(root) as entries:
            root_entries = list(entries)
        for entry in root_entries:
            if entry.name not in patterns or not entry.is_dir(follow_symlinks=False):
                return False
            if os.path.normcase(os.path.realpath(entry.path)) != os.path.normcase(entry.path):
                return False
            folders.append(entry.path)
            with os.scandir(entry.path) as children:
                child_entries = list(children)
            for child in child_entries:
                if (not child.is_file(follow_symlinks=False)
                        or not re.fullmatch(patterns[entry.name], child.name)):
                    return False
                paths.append(child.path)
        try:
            with ExitStack() as locks:
                for path in sorted(paths):
                    if path.endswith(".lock"):
                        locks.enter_context(ClipSnapshotFileLock(path[:-5], timeout_seconds=0))
        except (OSError, RuntimeError):
            return False
        # No new worker can open a lock until the external guard is released.
        for path in paths:
            os.remove(path)
        for folder in folders:
            os.rmdir(folder)
        os.rmdir(root)
        return True


def cleanup_project_coordination(project, task_list=None, report=None):
    """Cleans enabled Kimodo destinations after the owning runner stops its workers.

    Args:
        project (BatchProcessorModel): Owning project.
        task_list (list, optional): Tasks selected for this run.
        report (callable, optional): Receives concise cleanup status.
    """
    destinations = {}
    for task in project.get_enabled_tasks() if task_list is None else task_list:
        if not isinstance(task, TaskKimodoBase):
            continue
        try:
            task_index = project.get_task_environment_index(task)
            directory = task.resolve_task_path(project, task_index=task_index)
        except (OSError, RuntimeError, ValueError) as error:
            if report:
                report(f"[Kimodo] Could not resolve coordination cleanup directory: {error}")
            continue
        if not directory:
            continue
        key = os.path.normcase(os.path.realpath(directory))
        enabled = task.settings.get("purge_coordination_on_finish", True)
        destinations[key] = destinations.get(key, True) and enabled
    for directory, enabled in destinations.items():
        if not enabled:
            continue
        try:
            if not purge_coordination(directory) and report:
                report(f"[Kimodo] Kept coordination folder containing active locks or unrecognized files: {directory}")
        except (OSError, RuntimeError, ValueError) as error:
            if report:
                report(f"[Kimodo] Could not purge coordination folder: {error}")


def report_message(context, message):
    """Reports a concise message to the batch tracker or stdout.

    Args:
        context (dict): Worker runtime context.
        message (str): Status message.
    """
    reporter = (context or {}).get("report_message")
    if callable(reporter):
        reporter(f"[Kimodo] {message}")
    else:
        print(f"[Kimodo] {message}", flush=True)


def write_record(path, record):
    """Atomically writes an owned JSON output or recovery record.

    Args:
        path (str): Destination file.
        record (dict): Serializable record.
    """
    os.makedirs(os.path.dirname(path), exist_ok=True)
    kimodo._write_json(path, record)


def fingerprint(data):
    """Hashes JSON data deterministically.

    Args:
        data (object): JSON-compatible data.

    Returns:
        str: SHA256 digest.
    """
    return hashlib.sha256(json.dumps(data, sort_keys=True, allow_nan=False).encode("utf-8")).hexdigest()


def output_name(pattern, source, variation=1, seed=0, sample=1, variations=1, samples=1,
                suffix="", definition=None, append_variation_suffix=True):
    """Builds a Windows-safe leaf name, adding disambiguating suffixes when necessary.

    Args:
        pattern (str): Format using supported Kimodo output tokens.
        source (str): Source filename stem.
        variation (int): One-based definition variation.
        seed (int): Resolved seed.
        sample (int): One-based generated sample.
        variations (int): Definition count.
        samples (int): Sample count.
        suffix (str, optional): Optional suffix pattern appended to the base name.
        definition (dict, optional): Resolved definition providing descriptive parameter tokens.
        append_variation_suffix (bool, optional): Whether to append an automatic variation suffix.

    Returns:
        str: Safe leaf filename without extension.
    """
    definition = definition or {}
    parameters = definition.get("parameters", {})
    guidance = parameters.get("guidance", [2, 2])
    if not isinstance(guidance, (list, tuple)) or len(guidance) < 2:
        guidance = [0, 0]
    prompts = definition.get("prompts", [])
    first_prompt = prompts[0].get("text", "") if prompts and isinstance(prompts[0], dict) else ""
    prompt = " ".join(str(first_prompt).split())[:32].rstrip()
    try:
        duration = sum(float(item.get("duration_seconds", 0)) for item in prompts if isinstance(item, dict))
    except (TypeError, ValueError):
        duration = 0
    values = {
        "source": source,
        "variation": variation,
        "seed": seed,
        "sample": sample,
        "model": str(definition.get("model") or "model"),
        "steps": int(parameters.get("diffusion_steps", 100)),
        "guidance_text": f"{float(guidance[0]):g}",
        "guidance_constraints": f"{float(guidance[1]):g}",
        "duration": f"{duration:g}" if duration else "duration",
        "prompt": prompt or "prompt",
    }
    suffix = str(suffix or "").strip().lstrip("_-")
    if suffix:
        pattern = f"{pattern}_{suffix}"
    fields = []
    for literal, field, spec, conversion in string.Formatter().parse(pattern):
        if field is not None:
            integer_fields = {"variation", "seed", "sample", "steps"}
            if field not in values or conversion or (
                    spec and (field not in integer_fields or not re.fullmatch(r"0?[1-9][0-9]?d", spec))):
                raise ValueError(f"Unsupported naming token or format: {field}.")
            if field == "source" and spec:
                raise ValueError("Source name cannot have a numeric format.")
            fields.append(field)
    try:
        name = pattern.format(**values)
    except (ValueError, TypeError, KeyError) as error:
        raise ValueError(f"Invalid output name pattern: {error}")
    if append_variation_suffix and variations > 1 and "variation" not in fields:
        name += f"_v{variation:03d}"
    if samples > 1 and "sample" not in fields:
        name += f"_s{sample:03d}"
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    if not name or name in (".", "..") or len(name) > 180:
        raise ValueError("Output name is empty or too long.")
    if name.split(".")[0].upper() in {"CON", "PRN", "AUX", "NUL"} | {
            f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10)}:
        name = f"_{name}"
    return name


def resolve_path(value, project, task=None):
    """Resolves optional project paths without interpreting an empty value as CWD.

    Args:
        value (str): Path or project template.
        project (BatchProcessorModel): Owning project.
        task (BatchTask, optional): Task for template variables.

    Returns:
        str: Absolute path, or empty string.
    """
    if not str(value or "").strip():
        return ""
    path = project.resolve_template_path(str(value), task=task) if project else str(value)
    if not path or not os.path.isabs(path):
        raise ValueError(f"Expected an absolute or project-relative path: {value}")
    return os.path.normpath(path)


def resolve_motion_text(text, project=None, task=None, work_item=None, evaluate_queries=True):
    """Expands project variables before inserting literal per-input values.

    Args:
        text (str): Text or a single segment value containing placeholders.
        project (BatchProcessorModel, optional): Project variable provider.
        task (BatchTask, optional): Task supplying scoped project variables.
        work_item (WorkItem, optional): Current input; absent keeps runtime tokens unresolved.
        evaluate_queries (bool, optional): Whether the current scene is ready for custom queries.

    Returns:
        str: Resolved text, preserving braces inside inserted input values.
    """
    variables = project.get_environment_variables(
        task=task, include_braces=False, include_neighbor_paths=False,
        evaluate_queries=evaluate_queries) if project else {}
    resolved = os.path.expandvars(text)

    def replace_project_variable(match):
        """Resolves a project token while leaving per-input tokens for the final pass.

        Args:
            match (re.Match): Placeholder match.

        Returns:
            str: Project value or the unchanged placeholder.
        """
        key = match.group(1).lower().replace("_", "-")
        if key in RUNTIME_KEYS or key not in variables:
            return match.group(0)
        return str(variables[key] if variables[key] is not None else "")

    for unused_pass in range(10):
        expanded = VARIABLE_PATTERN.sub(replace_project_variable, resolved)
        if expanded == resolved:
            break
        resolved = expanded
    if work_item is None:
        return resolved
    filename = os.path.basename(work_item.current_path)
    values = {
        "input-file": work_item.metadata.get(
            "input_file", os.path.splitext(os.path.basename(work_item.source_path))[0]),
        "input-string": work_item.metadata.get("input_string", ""),
        "input-string-index": work_item.metadata.get("input_string_index", ""),
        "input-file-name": filename,
        "input-file-stem": os.path.splitext(filename)[0],
        "input-file-path": work_item.current_path,
    }

    def replace_runtime_variable(match):
        """Inserts a runtime value once without expanding placeholders in its content.

        Args:
            match (re.Match): Placeholder match.

        Returns:
            str: Literal runtime value or unchanged placeholder.
        """
        key = match.group(1).lower().replace("_", "-")
        return str(values[key]) if key in values else match.group(0)

    return VARIABLE_PATTERN.sub(replace_runtime_variable, resolved)


def uses_runtime_variables(text, project=None):
    """Checks whether text needs a current input before it can be validated.

    Args:
        text (str): Expanded project text to inspect.
        project (BatchProcessorModel, optional): Project supplying deferred custom queries.

    Returns:
        bool: Whether a per-input placeholder is present.
    """
    runtime_keys = set(RUNTIME_KEYS)
    if project:
        runtime_keys.update(name for name, definition in project.custom_environment_variables.items()
                            if definition.get("query"))
    return any(match.group(1).lower().replace("_", "-") in runtime_keys
               for match in VARIABLE_PATTERN.finditer(text))


def parse_motion_text(text, resolver=None):
    """Parses ordered JSON pairs, resolving complete sequences or individual values.

    Args:
        text (str): JSON list of [seconds, description] pairs or a sequence placeholder.
        resolver (callable, optional): Expands a string's variables into literal text.

    Returns:
        list: Prompt dictionaries using text and duration_seconds.

    Raises:
        ValueError: If the format, segment values, or Kimodo duration limits are invalid.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"Enter motion text as JSON pairs, for example {MOTION_TEXT_EXAMPLE}.")
    resolve_values = True
    try:
        pairs = json.loads(text)
    except ValueError:
        try:
            pairs = json.loads(resolver(text) if resolver else text)
            resolve_values = False
        except ValueError as error:
            raise ValueError(f"Motion text must be JSON pairs, for example {MOTION_TEXT_EXAMPLE}.") from error
    if not isinstance(pairs, list) or not 1 <= len(pairs) <= 16:
        raise ValueError("Motion text requires between 1 and 16 [seconds, description] pairs.")
    prompts = []
    for index, pair in enumerate(pairs, 1):
        if not isinstance(pair, list) or len(pair) != 2:
            raise ValueError(f"Motion segment {index} must be [seconds, description].")
        duration, description = pair
        if resolver and resolve_values:
            duration = resolver(duration) if isinstance(duration, str) else duration
            description = resolver(description) if isinstance(description, str) else description
        if isinstance(duration, str):
            try:
                duration = float(duration)
            except ValueError:
                pass
        if (type(duration) not in (int, float) or not 0 < duration <= 30
                or not math.isfinite(duration)):
            raise ValueError(f"Motion segment {index}: seconds must be positive and at most 30.")
        if not isinstance(description, str) or not description.strip() or len(description) > 10000:
            raise ValueError(f"Motion segment {index}: enter a description of 1 through 10000 characters.")
        prompts.append({"duration_seconds": duration, "text": description})
    if sum(prompt["duration_seconds"] for prompt in prompts) > 120:
        raise ValueError("Total motion duration cannot exceed 120 seconds.")
    return prompts
