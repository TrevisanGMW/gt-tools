"""Small shared batch adapter for the two Kimodo tasks."""

import os
import re
import string
import hashlib
import json
import shutil
from functools import partial
from gt.core import io as core_io
from gt.tools.batch_processor import batch_processor_task_base as base
from gt.tools.batch_processor.tasks.task_clip import ClipSnapshotFileLock
from gt.ui import resource_library as resources
from gt.utils import kimodo


read_json = partial(core_io.read_json_dict, raise_errors=True)


class TaskKimodoBase(base.BatchTask):
    """Adds filtered discovery, output ownership checks, and per-item recovery paths."""

    icon = resources.Icon.tool_kimodo_generator
    category = "Animation"
    category_icon = resources.Icon.root_animation
    extensions = ()

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
                        purge_cache_on_success=True)
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
        if not self.writes_to_target_path():
            self.add_area_error(result, "Task Setup", "Kimodo tasks require a separate target folder.")
        try:
            if not isinstance(self.settings.get("include_version_suffix", True), bool):
                self.add_area_error(result, "Output Naming", "Include version suffix must be enabled or disabled.")
            output_name(self.settings["name_pattern"], "example",
                        suffix=self.settings.get("filename_suffix", ""),
                        append_variation_suffix=self.settings.get("include_version_suffix", True))
        except (ValueError, TypeError, KeyError) as error:
            self.add_area_error(result, "Output Naming", error)
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
                self.add_area_error(result, "Output Naming", error)
                continue
            key = os.path.normcase(path)
            if key in seen:
                self.add_area_error(
                    result, "Output Naming",
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

    def recovery_lock(self, item, directory, timeout_seconds=3600):
        """Locks one task/input independently of its removable recovery folder.

        Args:
            item (WorkItem): Input whose recovery data is being accessed.
            directory (str): Output root.
            timeout_seconds (float, optional): Maximum time to wait for the lock.

        Returns:
            ClipSnapshotFileLock: Stable coordination lock for this task/input pair.
        """
        identity = fingerprint([self.id, os.path.normcase(os.path.abspath(item.current_path))])[:24]
        lock_path = os.path.join(os.path.abspath(directory), ".kimodo-coordination", "locks", identity)
        return ClipSnapshotFileLock(lock_path, timeout_seconds=timeout_seconds)

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
