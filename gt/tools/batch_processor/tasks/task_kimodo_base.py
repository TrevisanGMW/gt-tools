"""Small shared batch adapter for the two Kimodo tasks."""

import os
import re
import string
import hashlib
import json
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
        settings.update(source_mode=base.SOURCE_MODE_INCOMING, name_pattern="{source}",
                        source_include_subdirectories=True)
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
                and not any(part == ".kimodo-cache" or part.endswith("_artifacts")
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
            result.add_error("Kimodo tasks require a separate target folder.")
        try:
            output_name(self.settings["name_pattern"], "example")
        except (ValueError, TypeError, KeyError) as error:
            result.add_error(str(error))
        return result

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
                path = self.output_path(item, step_output_dir, seed=0)
                key = os.path.normcase(path)
                if key in seen:
                    result.add_error(f"Kimodo output collision: {seen[key]} and {item.current_path}: {path}")
                seen[key] = item.current_path
            except (ValueError, OSError) as error:
                result.add_error(str(error))
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

    def output_path(self, item, directory, variation=1, seed=0, sample=1, samples=1):
        """Builds an owned output path while preserving source-relative folders.

        Args:
            item (WorkItem): Incoming item.
            directory (str): Target root.
            variation (int): Variation index.
            seed (int): Resolved seed.
            sample (int): Sample index.
            samples (int): Number of samples.

        Returns:
            str: Output path.
        """
        name = output_name(self.settings["name_pattern"], os.path.splitext(os.path.basename(item.current_path))[0],
                                variation, seed, sample, int(self.settings.get("variations", 1)), samples)
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

    def reserve_outputs(self, item, paths, directory):
        """Claims output names across workers before submitting expensive generation.

        Args:
            item (WorkItem): Input owning these outputs.
            paths (list): Planned output paths.
            directory (str): Target root containing the ownership registry.
        """
        owner = os.path.normcase(os.path.abspath(item.current_path))
        for path in paths:
            key = fingerprint(os.path.normcase(os.path.abspath(path)))
            claim_path = os.path.join(directory, ".kimodo-cache", "outputs", f"{key}.json")
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


def output_name(pattern, source, variation=1, seed=0, sample=1, variations=1, samples=1):
    """Builds a Windows-safe leaf name, adding disambiguating suffixes when necessary.

    Args:
        pattern (str): Format using source, variation, seed, and sample.
        source (str): Source filename stem.
        variation (int): One-based definition variation.
        seed (int): Resolved seed.
        sample (int): One-based generated sample.
        variations (int): Definition count.
        samples (int): Sample count.

    Returns:
        str: Safe leaf filename without extension.
    """
    values = {"source": source, "variation": variation, "seed": seed, "sample": sample}
    fields = []
    for literal, field, spec, conversion in string.Formatter().parse(pattern):
        if field is not None:
            if field not in values or conversion or (spec and not re.fullmatch(r"0?[1-9][0-9]?d", spec)):
                raise ValueError(f"Unsupported naming token or format: {field}.")
            if field == "source" and spec:
                raise ValueError("Source name cannot have a numeric format.")
            fields.append(field)
    name = pattern.format(**values)
    if variations > 1 and "variation" not in fields:
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
