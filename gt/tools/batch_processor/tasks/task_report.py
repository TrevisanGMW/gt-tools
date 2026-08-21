"""
Batch Processor Report Task

Collects read-only information about incoming files and writes a single report.
Metric collection is registry based, so new report items only require a new
metric definition and a matching collector function.
"""

from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tasks import task_utils
import contextlib
import hashlib
import json
import os
import time
import uuid


REPORT_LOG_TARGET_PATH_TEMPLATE = "{log-dir}"
REPORT_FILE_EXTENSION = ".txt"
DEFAULT_REPORT_FILE_NAME = "{project-name}_report.txt"
DEFAULT_REPORT_NOTES = "{project-notes}"

PARTS_DIRECTORY_SUFFIX = "_parts"
PART_FILE_EXTENSION = ".json"
REPORT_TARGET_MARKER_NAME = "_report_target.json"
REPORT_LOCK_NAME = "_report.lock"
LOCK_TIMEOUT_SECONDS = 30.0
FALLBACK_RUN_ID = uuid.uuid4().hex[:16]

REPORT_DETAIL_TOTAL_ONLY = "Total Only"
REPORT_DETAIL_LIST_AND_TOTAL = "List + Total"
REPORT_DETAIL_MODES = [REPORT_DETAIL_TOTAL_ONLY, REPORT_DETAIL_LIST_AND_TOTAL]

AGGREGATION_SUM = "sum"
AGGREGATION_SET = "set"
AGGREGATION_NONE = "none"

FORMAT_INTEGER = "integer"
FORMAT_NUMBER = "number"
FORMAT_BYTES = "bytes"
FORMAT_DURATION = "duration"
FORMAT_TEXT = "text"

FRAME_RATE_BY_TIME_UNIT = {
    "game": 15.0,
    "film": 24.0,
    "pal": 25.0,
    "ntsc": 30.0,
    "show": 48.0,
    "palf": 50.0,
    "ntscf": 60.0,
}


REPORT_METRICS = [
    {
        "key": "frame_count",
        "label": "Frame Count",
        "tooltip": "Number of frames between the start and the end of the timeline.",
        "requires_scene": True,
        "fields": [
            {"name": "frame_count", "label": "Frames", "aggregation": AGGREGATION_SUM, "format": FORMAT_INTEGER},
            {"name": "start_frame", "label": "Start Frame", "aggregation": AGGREGATION_NONE, "format": FORMAT_NUMBER},
            {"name": "end_frame", "label": "End Frame", "aggregation": AGGREGATION_NONE, "format": FORMAT_NUMBER},
        ],
    },
    {
        "key": "frame_rate",
        "label": "Frame Rates",
        "tooltip": "Frame rates found in the processed scenes. Matching scenes only report one value.",
        "requires_scene": True,
        "fields": [
            {
                "name": "frame_rate",
                "label": "Frame Rate",
                "total_label": "Frame Rates",
                "aggregation": AGGREGATION_SET,
                "format": FORMAT_NUMBER,
            },
            {"name": "time_unit", "label": "Time Unit", "aggregation": AGGREGATION_NONE, "format": FORMAT_TEXT},
        ],
    },
    {
        "key": "file_size",
        "label": "File Size",
        "tooltip": "Size on disk of each processed file.",
        "requires_scene": False,
        "fields": [
            {"name": "file_size_bytes", "label": "File Size", "aggregation": AGGREGATION_SUM, "format": FORMAT_BYTES},
        ],
    },
    {
        "key": "time",
        "label": "Time",
        "tooltip": "Duration of each scene, calculated from its frame count and frame rate.",
        "requires_scene": True,
        "fields": [
            {
                "name": "duration_seconds",
                "label": "Duration",
                "aggregation": AGGREGATION_SUM,
                "format": FORMAT_DURATION,
            },
        ],
    },
    {
        "key": "mesh_count",
        "label": "Meshes",
        "tooltip": "Number of mesh shapes found in each scene.",
        "requires_scene": True,
        "fields": [
            {"name": "mesh_count", "label": "Meshes", "aggregation": AGGREGATION_SUM, "format": FORMAT_INTEGER},
        ],
    },
    {
        "key": "joint_count",
        "label": "Joints",
        "tooltip": "Number of joints found in each scene.",
        "requires_scene": True,
        "fields": [
            {"name": "joint_count", "label": "Joints", "aggregation": AGGREGATION_SUM, "format": FORMAT_INTEGER},
        ],
    },
    {
        "key": "transform_count",
        "label": "Transforms",
        "tooltip": "Number of transforms found in each scene.",
        "requires_scene": True,
        "fields": [
            {
                "name": "transform_count",
                "label": "Transforms",
                "aggregation": AGGREGATION_SUM,
                "format": FORMAT_INTEGER,
            },
        ],
    },
    {
        "key": "geometry_counts",
        "label": "Geometry Components",
        "tooltip": "Number of triangles, vertices, edges, and faces found in each scene.",
        "requires_scene": True,
        "fields": [
            {"name": "triangle_count", "label": "Triangles", "aggregation": AGGREGATION_SUM, "format": FORMAT_INTEGER},
            {"name": "vertex_count", "label": "Vertices", "aggregation": AGGREGATION_SUM, "format": FORMAT_INTEGER},
            {"name": "edge_count", "label": "Edges", "aggregation": AGGREGATION_SUM, "format": FORMAT_INTEGER},
            {"name": "face_count", "label": "Faces", "aggregation": AGGREGATION_SUM, "format": FORMAT_INTEGER},
        ],
    },
    {
        "key": "uv_counts",
        "label": "UVs",
        "tooltip": "Number of UV coordinates and UV sets found in each scene.",
        "requires_scene": True,
        "fields": [
            {"name": "uv_count", "label": "UVs", "aggregation": AGGREGATION_SUM, "format": FORMAT_INTEGER},
            {"name": "uv_set_count", "label": "UV Sets", "aggregation": AGGREGATION_SUM, "format": FORMAT_INTEGER},
        ],
    },
    {
        "key": "scene_units",
        "label": "Scene Units",
        "tooltip": "Linear and angular units found in the processed scenes. Matching scenes only report one value.",
        "requires_scene": True,
        "fields": [
            {
                "name": "linear_unit",
                "label": "Linear Unit",
                "total_label": "Linear Units",
                "aggregation": AGGREGATION_SET,
                "format": FORMAT_TEXT,
            },
            {
                "name": "angular_unit",
                "label": "Angular Unit",
                "total_label": "Angular Units",
                "aggregation": AGGREGATION_SET,
                "format": FORMAT_TEXT,
            },
        ],
    },
]

DEFAULT_REPORT_METRICS = ["frame_count", "frame_rate", "file_size", "time"]

LEGACY_METRIC_KEYS = {"node_counts": ["mesh_count", "joint_count", "transform_count"]}


class TaskSceneReport(task_base.BatchTask):
    """Task that reports information about incoming files without changing them."""

    task_type = constants.TaskType.SCENE_REPORT
    default_display_name = "Report"
    default_target_path_template = REPORT_LOG_TARGET_PATH_TEMPLATE
    icon = ui_res_lib.Icon.batch_task_report
    category = "Utilities"
    category_icon = ui_res_lib.Icon.root_utilities
    is_indexless_task = True
    supports_run_once_after_jobs = True

    def get_default_settings(self):
        """Gets default report settings.

        Returns:
            dict: Default settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "target_path": self.default_target_path_template,
            "source_include_subdirectories": True,
            "source_load_mode": "Open",
            "load_relevant_plugins": True,
            "report_metrics": list(DEFAULT_REPORT_METRICS),
            "report_detail_mode": REPORT_DETAIL_TOTAL_ONLY,
            "report_file_name": DEFAULT_REPORT_FILE_NAME,
            "report_notes": DEFAULT_REPORT_NOTES,
            "report_notes_collapsed": True,
            "overwrite": True,
            "run_once_after_multi_instance": True,
            "force_segment_separator": False,
            "segment_name": "",
            "segment_color": "blue_light_sky",
        }

    def validate(self, project):
        """Validates report settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Validation result.
        """
        result = task_base.ValidationResult()
        metric_keys = self.get_metric_keys()
        if not metric_keys:
            result.add_warning("Report has no report items selected. Only the file list will be written.")
        known_keys = [metric.get("key") for metric in REPORT_METRICS]
        for metric_key in metric_keys:
            if metric_key not in known_keys:
                result.add_error("Unknown report item: {0}".format(metric_key))
        if self.settings.get("report_detail_mode") not in REPORT_DETAIL_MODES:
            result.add_error("Unknown report detail mode: {0}".format(self.settings.get("report_detail_mode")))
        return result

    def get_metric_keys(self):
        """Gets the selected report metric keys in registry order.

        Returns:
            list: Selected metric keys.
        """
        return normalize_metric_keys(self.settings.get("report_metrics"))

    def get_detail_mode(self):
        """Gets the configured report detail mode.

        Returns:
            str: Report detail mode name.
        """
        detail_mode = str(self.settings.get("report_detail_mode") or "").strip()
        return detail_mode if detail_mode in REPORT_DETAIL_MODES else REPORT_DETAIL_TOTAL_ONLY

    def requires_scene_load(self):
        """Checks whether the selected report items need a loaded Maya scene.

        Returns:
            bool: True when at least one selected item reads scene data.
        """
        return metrics_require_scene(self.get_metric_keys())

    def get_no_source_files_error(self, project, task_index=None):
        """Builds a clear error when the report has no source files to inspect.

        Args:
            project (BatchProcessorModel): Project containing this task.
            task_index (int, optional): One-based task index used for path resolution.

        Returns:
            str: User-facing error message.
        """
        source_path = self.resolve_source_path(project=project, task_index=task_index)
        if not source_path:
            return "Report could not be generated because its source path resolved to an empty value."
        include_subdirectories = self.settings.get("source_include_subdirectories", True)
        search_scope = "including subdirectories" if include_subdirectories else "top-level files only"
        return f'Report could not be generated: no source files were detected in "{source_path}" ({search_scope}).'

    def execute(self, work_item, project, step_output_dir, context=None):
        """Collects report values for one file and rewrites the report.

        Args:
            work_item (WorkItem): Work item to inspect.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Report output directory.
            context (dict, optional): Runtime context.

        Returns:
            WorkItem: Unchanged work item.
        """
        if not work_item:
            raise RuntimeError("Report could not be generated because no source work item was provided.")
        context = context or {}
        run_id = get_run_id(context)
        entry = self.collect_entry(work_item.current_path)
        base_report_path = build_report_path(self, step_output_dir, project=project)
        parts_dir = get_parts_dir(base_report_path)
        self.purge_stale_parts_once(parts_dir, run_id)
        write_report_part(parts_dir, entry, run_id)
        try:
            with report_lock(parts_dir):
                entries = read_report_parts(parts_dir, run_id)
                report_path = self.write_report(
                    step_output_dir=step_output_dir,
                    entries=entries,
                    project=project,
                    context=context,
                )
        except Exception as exception:
            raise RuntimeError(f'Report could not be written to "{base_report_path}": {exception}')
        if not report_path or not os.path.isfile(report_path):
            raise RuntimeError(f'Report was not generated: expected report file was not found at "{report_path}".')
        task_utils.report_log_artifact(context, report_path)
        return task_base.WorkItem(
            source_path=work_item.source_path,
            current_path=work_item.current_path,
            metadata=task_utils.build_metadata(self, work_item),
        )

    def collect_entry(self, file_path, load_scene=True):
        """Collects every selected report value for one file.

        Args:
            file_path (str): File inspected by this report.
            load_scene (bool, optional): Whether the scene should be opened before collecting values.

        Returns:
            dict: Report entry with collected values and collection errors.
        """
        metric_keys = self.get_metric_keys()
        cmds = None
        if load_scene and metrics_require_scene(metric_keys):
            try:
                task_utils.load_source_scene(
                    file_path,
                    source_load_mode=self.settings.get("source_load_mode") or "Open",
                    load_relevant_plugins=self.settings.get("load_relevant_plugins", True),
                )
            except Exception as exception:
                raise RuntimeError(
                    f'Report could not inspect "{file_path}": failed to load the Maya scene. {exception}'
                )
        return collect_report_entry(file_path=file_path, metric_keys=metric_keys, cmds=cmds)

    def purge_stale_parts_once(self, parts_dir, run_id):
        """Removes partial results left by earlier runs, once per process.

        Args:
            parts_dir (str): Directory holding the partial results of this report.
            run_id (str): Identifier of the current run.
        """
        purged_directories = getattr(self, "_purged_parts_directories", None)
        if purged_directories is None:
            purged_directories = set()
            setattr(self, "_purged_parts_directories", purged_directories)
        if parts_dir in purged_directories:
            return
        purged_directories.add(parts_dir)
        purge_stale_parts(parts_dir, run_id)

    def write_report(self, step_output_dir, entries, project=None, context=None):
        """Writes the report file for the collected entries.

        Args:
            step_output_dir (str): Report output directory.
            entries (list): Collected report entries.
            project (BatchProcessorModel, optional): Active project used to resolve the report name.
            context (dict, optional): Runtime context.

        Returns:
            str: Written report path.
        """
        base_report_path = build_report_path(self, step_output_dir, project=project)
        report_path = resolve_report_path(
            base_report_path=base_report_path,
            run_id=get_run_id(context),
            overwrite=self.settings.get("overwrite", True),
        )
        report_data = self.build_report_data(entries, project=project)
        return write_report_file(report_path, build_report_lines(report_data))

    def build_report_data(self, entries, project=None):
        """Builds the serializable report data for the collected entries.

        Args:
            entries (list): Collected report entries.
            project (BatchProcessorModel, optional): Active project used to resolve report notes.

        Returns:
            dict: Report data used to render the report text.
        """
        metric_keys = self.get_metric_keys()
        return {
            "task": self.display_name,
            "task_type": self.task_type,
            "created_at": task_utils.get_timestamp(),
            "detail_mode": self.get_detail_mode(),
            "metrics": metric_keys,
            "file_count": len(entries),
            "totals": aggregate_entries(entries, metric_keys),
            "entries": list(entries),
            "notes": self.get_report_notes(project=project),
        }

    def get_report_notes(self, project=None):
        """Gets report notes after resolving project environment variables.

        Args:
            project (BatchProcessorModel, optional): Active project used to resolve note tokens.

        Returns:
            str: Report notes, or an empty string when no notes are configured.
        """
        notes = str(self.settings.get("report_notes") or "")
        if project and callable(getattr(project, "resolve_template", None)):
            notes = project.resolve_template(notes, task=self)
        elif notes.strip() == DEFAULT_REPORT_NOTES:
            return ""
        return notes if notes.strip() else ""


def normalize_metric_keys(values):
    """Normalizes stored metric keys into registry order.

    Args:
        values (list or str): Stored metric keys.

    Returns:
        list: Known metric keys, ordered like the metric registry.
    """
    if isinstance(values, str):
        values = [item.strip() for item in values.replace(",", "\n").splitlines()]
    selected_keys = set()
    for item in values or []:
        metric_key = str(item).strip()
        if not metric_key:
            continue
        selected_keys.update(LEGACY_METRIC_KEYS.get(metric_key, [metric_key]))
    return [metric.get("key") for metric in REPORT_METRICS if metric.get("key") in selected_keys]


def get_metric_definition(metric_key):
    """Gets a metric definition by key.

    Args:
        metric_key (str): Metric key.

    Returns:
        dict or None: Metric definition when registered.
    """
    for metric in REPORT_METRICS:
        if metric.get("key") == metric_key:
            return metric
    return None


def metrics_require_scene(metric_keys):
    """Checks whether any metric needs an opened Maya scene.

    Args:
        metric_keys (list): Metric keys.

    Returns:
        bool: True when at least one metric reads scene data.
    """
    for metric_key in metric_keys or []:
        metric = get_metric_definition(metric_key)
        if metric and metric.get("requires_scene"):
            return True
    return False


def collect_report_entry(file_path, metric_keys, cmds=None):
    """Collects report values for one file.

    Args:
        file_path (str): Inspected file path.
        metric_keys (list): Metric keys to collect.
        cmds (module, optional): Maya commands module. Resolved on demand when omitted.

    Returns:
        dict: Report entry with a path, collected values, and collection errors.
    """
    entry = {"path": task_base.normalize_path(file_path), "values": {}, "errors": []}
    for metric_key in metric_keys or []:
        metric = get_metric_definition(metric_key)
        collector = REPORT_METRIC_COLLECTORS.get(metric_key)
        if not metric or not collector:
            entry["errors"].append("Unknown report item: {0}".format(metric_key))
            continue
        try:
            if metric.get("requires_scene") and cmds is None:
                cmds = batch_processor_maya.get_maya_cmds()
            entry["values"].update(collector(cmds, file_path) or {})
        except Exception as exception:
            entry["errors"].append("{0}: {1}".format(metric.get("label"), exception))
    return entry


def aggregate_entries(entries, metric_keys):
    """Aggregates collected entries into report totals.

    Args:
        entries (list): Collected report entries.
        metric_keys (list): Metric keys to aggregate.

    Returns:
        list: Total rows with a label, a raw value, and a formatted value.
    """
    totals = []
    for metric_key in metric_keys or []:
        metric = get_metric_definition(metric_key)
        if not metric:
            continue
        for field in metric.get("fields") or []:
            aggregation = field.get("aggregation")
            if aggregation == AGGREGATION_SUM:
                totals.append(build_sum_total(entries, field))
            elif aggregation == AGGREGATION_SET:
                totals.append(build_set_total(entries, field))
    return totals


def build_sum_total(entries, field):
    """Builds a summed total row for one field.

    Args:
        entries (list): Collected report entries.
        field (dict): Field definition.

    Returns:
        dict: Total row.
    """
    total_value = 0
    for entry in entries or []:
        value = (entry.get("values") or {}).get(field.get("name"))
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            continue
        total_value += value
    return {
        "name": field.get("name"),
        "label": "Total {0}".format(field.get("label")),
        "value": total_value,
        "text": format_value(total_value, field.get("format")),
    }


def build_set_total(entries, field):
    """Builds a distinct-value total row for one field.

    Args:
        entries (list): Collected report entries.
        field (dict): Field definition.

    Returns:
        dict: Total row listing the distinct values found.
    """
    unique_values = []
    for entry in entries or []:
        value = (entry.get("values") or {}).get(field.get("name"))
        if value in [None, ""]:
            continue
        if value not in unique_values:
            unique_values.append(value)
    unique_values = sorted(unique_values, key=lambda item: str(item))
    value_text = ", ".join([format_value(value, field.get("format")) for value in unique_values]) or "None"
    return {
        "name": field.get("name"),
        "label": field.get("total_label") or field.get("label"),
        "value": unique_values,
        "text": "{0} found ({1})".format(len(unique_values), value_text),
    }


def format_value(value, value_format):
    """Formats a report value for the text report.

    Args:
        value (object): Value to format.
        value_format (str): Format name from the metric registry.

    Returns:
        str: Formatted value.
    """
    if value is None:
        return "N/A"
    if value_format == FORMAT_BYTES:
        return format_bytes(value)
    if value_format == FORMAT_DURATION:
        return format_duration(value)
    if value_format == FORMAT_INTEGER:
        return "{0:,}".format(int(value))
    if value_format == FORMAT_NUMBER:
        return format_number(value)
    return str(value)


def format_number(value):
    """Formats a number without trailing zeros.

    Args:
        value (int or float): Value to format.

    Returns:
        str: Formatted number.
    """
    if isinstance(value, float) and value.is_integer():
        return "{0:,}".format(int(value))
    if isinstance(value, (int, float)):
        return "{0:,.3f}".format(value).rstrip("0").rstrip(".")
    return str(value)


def format_bytes(value):
    """Formats a byte count using binary units.

    Args:
        value (int or float): Number of bytes.

    Returns:
        str: Formatted size, for example "1.25 MB".
    """
    size = float(value or 0)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size) < 1024.0 or unit == "TB":
            if unit == "B":
                return "{0:,} B".format(int(size))
            return "{0:,.2f} {1}".format(size, unit)
        size = size / 1024.0
    return "{0:,.2f} TB".format(size)


def format_duration(value):
    """Formats a duration in seconds as a readable time value.

    Args:
        value (int or float): Duration in seconds.

    Returns:
        str: Formatted duration, for example "00:01:23.500 (83.5s)".
    """
    total_seconds = float(value or 0)
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60
    return "{0:02d}:{1:02d}:{2:06.3f} ({3:,.3f}s)".format(hours, minutes, seconds, total_seconds)


def build_report_lines(report_data):
    """Builds the text lines of a report.

    Args:
        report_data (dict): Report data built by the report task.

    Returns:
        list: Report text lines.
    """
    report_data = report_data or {}
    lines = [
        "Batch Processor Report",
        "=" * 60,
        "Task: {0}".format(report_data.get("task") or ""),
        "Created: {0}".format(report_data.get("created_at") or ""),
        "Files: {0}".format(report_data.get("file_count") or 0),
        "Report Items: {0}".format(", ".join(report_data.get("metrics") or []) or "None"),
        "",
        "Totals",
        "-" * 60,
    ]
    totals = report_data.get("totals") or []
    if totals:
        label_width = max([len(str(total.get("label") or "")) for total in totals])
        for total in totals:
            lines.append("{0}: {1}".format(str(total.get("label") or "").ljust(label_width), total.get("text")))
    else:
        lines.append("No report items selected.")
    if report_data.get("detail_mode") == REPORT_DETAIL_LIST_AND_TOTAL:
        lines.extend(build_entry_lines(report_data))
    notes = str(report_data.get("notes") or "").strip()
    if notes:
        lines.extend(["", "Notes", "-" * 60])
        lines.extend(notes.splitlines())
    lines.append("")
    return lines


def build_entry_lines(report_data):
    """Builds the per-file section of a report.

    Args:
        report_data (dict): Report data built by the report task.

    Returns:
        list: Report text lines for every collected entry.
    """
    lines = ["", "Files", "-" * 60]
    entries = (report_data or {}).get("entries") or []
    if not entries:
        lines.append("No files were processed.")
        return lines
    fields = get_report_fields((report_data or {}).get("metrics") or [])
    for index, entry in enumerate(entries, 1):
        lines.append("{0}. {1}".format(index, entry.get("path") or ""))
        values = entry.get("values") or {}
        for field in fields:
            if field.get("name") not in values:
                continue
            value_text = format_value(values.get(field.get("name")), field.get("format"))
            lines.append("    {0}: {1}".format(field.get("label"), value_text))
        for error in entry.get("errors") or []:
            lines.append("    Error: {0}".format(error))
    return lines


def get_report_fields(metric_keys):
    """Gets every field definition used by the selected metrics.

    Args:
        metric_keys (list): Metric keys.

    Returns:
        list: Field definitions in registry order.
    """
    fields = []
    for metric_key in metric_keys or []:
        metric = get_metric_definition(metric_key)
        if metric:
            fields.extend(metric.get("fields") or [])
    return fields


def build_report_path(task, step_output_dir, project=None):
    """Builds the base report path for a task.

    The path is deterministic, so every parallel worker of one run writes to the
    same report file.

    Args:
        task (BatchTask): Report task.
        step_output_dir (str): Report output directory.
        project (BatchProcessorModel, optional): Active project used to resolve path tokens.

    Returns:
        str: Report path.
    """
    file_name = str(task.settings.get("report_file_name") or "").strip() or DEFAULT_REPORT_FILE_NAME
    file_name = resolve_report_file_name(file_name, task=task, project=project)
    base_name, extension = os.path.splitext(file_name.replace(" ", "_"))
    base_name = task_base.sanitize_filename(base_name, "report")
    file_name = "{0}{1}".format(base_name, extension or REPORT_FILE_EXTENSION)
    return task_base.normalize_path(os.path.join(step_output_dir, file_name))


def resolve_report_file_name(file_name, task=None, project=None):
    """Resolves project tokens used by a report file name.

    Args:
        file_name (str): Configured report file name.
        task (BatchTask, optional): Report task used as template context.
        project (BatchProcessorModel, optional): Active project.

    Returns:
        str: Report file name with resolved tokens.
    """
    file_name = str(file_name or "")
    if project and hasattr(project, "resolve_template"):
        try:
            return project.resolve_template(file_name, task=task)
        except Exception:
            pass
    project_name = str(getattr(project, "project_name", "") or "").strip()
    return file_name.replace("{project-name}", project_name or "project")


def get_parts_dir(base_report_path):
    """Gets the directory holding the partial results of one report.

    Every processed file writes one partial result, so parallel workers can
    build a complete report without overwriting each other.

    Args:
        base_report_path (str): Base report path.

    Returns:
        str: Partial results directory.
    """
    base_path = os.path.splitext(base_report_path)[0]
    return task_base.normalize_path("{0}{1}".format(base_path, PARTS_DIRECTORY_SUFFIX))


def get_run_id(context):
    """Gets the identifier shared by every process of the current run.

    Args:
        context (dict): Runtime context.

    Returns:
        str: Run identifier.
    """
    run_id = str((context or {}).get("run_id") or "").strip()
    return run_id or FALLBACK_RUN_ID


def write_report_part(parts_dir, entry, run_id):
    """Writes the partial result collected for one file.

    Args:
        parts_dir (str): Partial results directory.
        entry (dict): Collected report entry.
        run_id (str): Identifier of the current run.

    Returns:
        str: Written partial result path.
    """
    task_utils.ensure_directory(parts_dir)
    part_path = os.path.join(parts_dir, get_part_file_name(entry.get("path")))
    payload = dict(entry)
    payload["run_id"] = run_id
    payload["created_at"] = task_utils.get_timestamp()
    write_file_atomically(part_path, json.dumps(payload, indent=4, sort_keys=True))
    return task_base.normalize_path(part_path)


def get_part_file_name(file_path):
    """Gets the stable partial result file name used by one inspected file.

    Args:
        file_path (str): Inspected file path.

    Returns:
        str: Partial result file name.
    """
    path_key = os.path.normcase(str(file_path or "")).encode("utf-8")
    return "{0}{1}".format(hashlib.sha1(path_key).hexdigest(), PART_FILE_EXTENSION)


def read_report_parts(parts_dir, run_id):
    """Reads every partial result written by the current run.

    Args:
        parts_dir (str): Partial results directory.
        run_id (str): Identifier of the current run.

    Returns:
        list: Report entries sorted by inspected path.
    """
    entries = []
    for part_path in list_part_paths(parts_dir):
        part_data = read_json_file(part_path)
        if not part_data or part_data.get("run_id") != run_id:
            continue
        entries.append(
            {
                "path": part_data.get("path") or "",
                "values": part_data.get("values") or {},
                "errors": part_data.get("errors") or [],
            }
        )
    return sorted(entries, key=lambda entry: str(entry.get("path")).lower())


def purge_stale_parts(parts_dir, run_id):
    """Deletes partial results left by earlier runs.

    Args:
        parts_dir (str): Partial results directory.
        run_id (str): Identifier of the current run.

    Returns:
        int: Number of deleted partial results.
    """
    deleted_count = 0
    for part_path in list_part_paths(parts_dir):
        part_data = read_json_file(part_path)
        if part_data and part_data.get("run_id") == run_id:
            continue
        try:
            os.remove(part_path)
            deleted_count += 1
        except OSError:
            continue
    return deleted_count


def list_part_paths(parts_dir):
    """Lists the partial result files of one report.

    Args:
        parts_dir (str): Partial results directory.

    Returns:
        list: Partial result paths.
    """
    if not os.path.isdir(parts_dir):
        return []
    part_paths = []
    for file_name in sorted(os.listdir(parts_dir)):
        if not file_name.lower().endswith(PART_FILE_EXTENSION) or file_name == REPORT_TARGET_MARKER_NAME:
            continue
        part_path = os.path.join(parts_dir, file_name)
        if os.path.isfile(part_path):
            part_paths.append(part_path)
    return part_paths


def resolve_report_path(base_report_path, run_id, overwrite=True):
    """Resolves the report path shared by every worker of one run.

    When overwrite is enabled the base path is used directly. Otherwise the
    first worker of the run reserves an unused numbered path and records it, so
    every other worker of that run writes to the same report.

    Args:
        base_report_path (str): Base report path.
        run_id (str): Identifier of the current run.
        overwrite (bool, optional): Whether the report may replace an existing file.

    Returns:
        str: Report path used by this run.
    """
    if overwrite:
        return base_report_path
    parts_dir = get_parts_dir(base_report_path)
    marker_path = os.path.join(parts_dir, REPORT_TARGET_MARKER_NAME)
    reserved_path = get_reserved_report_path(marker_path, run_id)
    if reserved_path:
        return reserved_path
    task_utils.ensure_directory(parts_dir)
    report_path = get_unused_report_path(base_report_path)
    marker_text = json.dumps({"run_id": run_id, "report_path": report_path}, indent=4, sort_keys=True)
    try:
        with open(marker_path, "x", encoding="utf-8") as marker_file:
            marker_file.write(marker_text)
        return report_path
    except FileExistsError:
        reserved_path = get_reserved_report_path(marker_path, run_id)
    if reserved_path:
        return reserved_path
    write_file_atomically(marker_path, marker_text)
    return report_path


def get_reserved_report_path(marker_path, run_id):
    """Gets the report path already reserved by the current run.

    Args:
        marker_path (str): Reservation marker path.
        run_id (str): Identifier of the current run.

    Returns:
        str: Reserved report path, or an empty string when the run has none.
    """
    marker_data = read_json_file(marker_path)
    if marker_data and marker_data.get("run_id") == run_id:
        return str(marker_data.get("report_path") or "")
    return ""


@contextlib.contextmanager
def report_lock(parts_dir, timeout_seconds=LOCK_TIMEOUT_SECONDS):
    """Serializes the read-then-write step used to rebuild a shared report.

    Parallel workers each write their own partial result and then rebuild the
    whole report. Without this lock the last worker could rebuild the report
    from a snapshot taken before another worker added its partial result.

    Args:
        parts_dir (str): Partial results directory.
        timeout_seconds (float, optional): Seconds to wait before writing anyway.

    Yields:
        bool: True when the lock was acquired.
    """
    lock_path = os.path.join(parts_dir, REPORT_LOCK_NAME)
    acquired = acquire_report_lock(lock_path, timeout_seconds=timeout_seconds)
    try:
        yield acquired
    finally:
        if acquired:
            release_report_lock(lock_path)


def acquire_report_lock(lock_path, timeout_seconds=LOCK_TIMEOUT_SECONDS, poll_seconds=0.05):
    """Acquires the report lock through an exclusive lock file.

    Args:
        lock_path (str): Lock file path.
        timeout_seconds (float, optional): Seconds to wait before giving up.
        poll_seconds (float, optional): Delay between attempts.

    Returns:
        bool: True when the lock was acquired.
    """
    task_utils.ensure_directory(os.path.dirname(lock_path))
    deadline = time.monotonic() + max(0.0, float(timeout_seconds))
    while True:
        try:
            lock_handle = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(lock_handle)
            return True
        except FileExistsError:
            if is_stale_lock(lock_path, timeout_seconds):
                release_report_lock(lock_path)
                continue
        except OSError:
            return False
        if time.monotonic() >= deadline:
            return False
        time.sleep(poll_seconds)


def is_stale_lock(lock_path, timeout_seconds=LOCK_TIMEOUT_SECONDS):
    """Checks whether a lock file was abandoned by a stopped worker.

    Args:
        lock_path (str): Lock file path.
        timeout_seconds (float, optional): Age after which a lock is considered abandoned.

    Returns:
        bool: True when the lock file is older than the timeout.
    """
    try:
        return (time.time() - os.path.getmtime(lock_path)) > max(1.0, float(timeout_seconds))
    except OSError:
        return False


def release_report_lock(lock_path):
    """Releases the report lock.

    Args:
        lock_path (str): Lock file path.
    """
    try:
        os.remove(lock_path)
    except OSError:
        pass


def read_json_file(file_path):
    """Reads a JSON file written by this task.

    Args:
        file_path (str): JSON file path.

    Returns:
        dict or None: Parsed data, or None when the file is missing or unreadable.
    """
    if not os.path.isfile(file_path):
        return None
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            return json.load(json_file)
    except (OSError, ValueError):
        return None


def write_file_atomically(file_path, text):
    """Writes a file through a temporary path so readers never see partial data.

    Args:
        file_path (str): Destination path.
        text (str): File contents.

    Returns:
        str: Written file path.
    """
    output_dir = os.path.dirname(file_path)
    if output_dir:
        task_utils.ensure_directory(output_dir)
    temporary_path = "{0}.{1}.tmp".format(file_path, os.getpid())
    with open(temporary_path, "w", encoding="utf-8") as output_file:
        output_file.write(text)
    os.replace(temporary_path, file_path)
    return file_path


def get_unused_report_path(report_path, maximum_attempts=1000):
    """Gets a report path that does not exist yet.

    Args:
        report_path (str): Preferred report path.
        maximum_attempts (int, optional): Maximum number of numbered variations.

    Returns:
        str: Unused report path, or the preferred path when no variation is free.
    """
    if not os.path.exists(report_path):
        return report_path
    base_path, extension = os.path.splitext(report_path)
    for index in range(1, maximum_attempts):
        candidate_path = "{0}_{1:03d}{2}".format(base_path, index, extension)
        if not os.path.exists(candidate_path):
            return candidate_path
    return report_path


def write_report_file(report_path, lines):
    """Writes report lines to disk.

    Args:
        report_path (str): Destination report path.
        lines (list): Report text lines.

    Returns:
        str: Written report path.
    """
    return write_file_atomically(report_path, "\n".join(lines))


def get_frame_rate_from_time_unit(time_unit):
    """Gets a frame rate from a Maya time unit name.

    Args:
        time_unit (str): Maya time unit name, for example "film" or "30fps".

    Returns:
        float: Frame rate, or zero when the unit is unknown.
    """
    time_unit = str(time_unit or "").strip().lower()
    if time_unit in FRAME_RATE_BY_TIME_UNIT:
        return FRAME_RATE_BY_TIME_UNIT.get(time_unit)
    if time_unit.endswith("fps"):
        try:
            return float(time_unit[:-3])
        except ValueError:
            return 0.0
    return 0.0


def get_scene_frame_range(cmds):
    """Gets the current playback range and frame count.

    Args:
        cmds (module): Maya commands module.

    Returns:
        tuple: Start frame, end frame, and frame count.
    """
    start_frame = float(cmds.playbackOptions(query=True, minTime=True))
    end_frame = float(cmds.playbackOptions(query=True, maxTime=True))
    frame_count = int(round(end_frame - start_frame)) + 1
    return start_frame, end_frame, max(frame_count, 0)


def get_scene_meshes(cmds):
    """Gets the non-intermediate mesh shapes of the current scene.

    Args:
        cmds (module): Maya commands module.

    Returns:
        list: Mesh shape names.
    """
    return cmds.ls(type="mesh", noIntermediate=True, long=True) or []


def get_poly_evaluate_count(cmds, mesh, **query_flags):
    """Gets one polyEvaluate count for a mesh.

    Args:
        cmds (module): Maya commands module.
        mesh (str): Mesh shape name.
        **query_flags: Single polyEvaluate query flag.

    Returns:
        int: Component count, or zero when the query is unavailable.
    """
    try:
        value = cmds.polyEvaluate(mesh, **query_flags)
    except Exception:
        return 0
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return 0
    return int(value)


def collect_frame_count_values(cmds, file_path):
    """Collects timeline frame values.

    Args:
        cmds (module): Maya commands module.
        file_path (str): Inspected file path.

    Returns:
        dict: Frame range values.
    """
    start_frame, end_frame, frame_count = get_scene_frame_range(cmds)
    return {"start_frame": start_frame, "end_frame": end_frame, "frame_count": frame_count}


def collect_frame_rate_values(cmds, file_path):
    """Collects the scene frame rate.

    Args:
        cmds (module): Maya commands module.
        file_path (str): Inspected file path.

    Returns:
        dict: Frame rate values.
    """
    time_unit = cmds.currentUnit(query=True, time=True)
    return {"time_unit": time_unit, "frame_rate": get_frame_rate_from_time_unit(time_unit)}


def collect_file_size_values(cmds, file_path):
    """Collects the size on disk of the inspected file.

    Args:
        cmds (module): Maya commands module. Unused by this collector.
        file_path (str): Inspected file path.

    Returns:
        dict: File size values.
    """
    if not os.path.isfile(file_path):
        return {"file_size_bytes": None}
    return {"file_size_bytes": os.path.getsize(file_path)}


def collect_time_values(cmds, file_path):
    """Collects the scene duration in seconds.

    Args:
        cmds (module): Maya commands module.
        file_path (str): Inspected file path.

    Returns:
        dict: Duration values.
    """
    frame_count = get_scene_frame_range(cmds)[2]
    frame_rate = get_frame_rate_from_time_unit(cmds.currentUnit(query=True, time=True))
    if not frame_rate:
        return {"duration_seconds": None}
    return {"duration_seconds": frame_count / frame_rate}


def collect_mesh_count_values(cmds, file_path):
    """Collects the mesh count.

    Args:
        cmds (module): Maya commands module.
        file_path (str): Inspected file path.

    Returns:
        dict: Mesh count value.
    """
    return {"mesh_count": len(get_scene_meshes(cmds))}


def collect_joint_count_values(cmds, file_path):
    """Collects the joint count.

    Args:
        cmds (module): Maya commands module.
        file_path (str): Inspected file path.

    Returns:
        dict: Joint count value.
    """
    return {"joint_count": len(cmds.ls(type="joint", long=True) or [])}


def collect_transform_count_values(cmds, file_path):
    """Collects the transform count.

    Args:
        cmds (module): Maya commands module.
        file_path (str): Inspected file path.

    Returns:
        dict: Transform count value.
    """
    return {"transform_count": len(cmds.ls(type="transform", long=True) or [])}


def collect_geometry_count_values(cmds, file_path):
    """Collects triangle, vertex, edge, and face counts.

    Args:
        cmds (module): Maya commands module.
        file_path (str): Inspected file path.

    Returns:
        dict: Geometry component counts.
    """
    counts = {"triangle_count": 0, "vertex_count": 0, "edge_count": 0, "face_count": 0}
    for mesh in get_scene_meshes(cmds):
        counts["triangle_count"] += get_poly_evaluate_count(cmds, mesh, triangle=True)
        counts["vertex_count"] += get_poly_evaluate_count(cmds, mesh, vertex=True)
        counts["edge_count"] += get_poly_evaluate_count(cmds, mesh, edge=True)
        counts["face_count"] += get_poly_evaluate_count(cmds, mesh, face=True)
    return counts


def collect_uv_count_values(cmds, file_path):
    """Collects UV coordinate and UV set counts.

    Args:
        cmds (module): Maya commands module.
        file_path (str): Inspected file path.

    Returns:
        dict: UV counts.
    """
    counts = {"uv_count": 0, "uv_set_count": 0}
    for mesh in get_scene_meshes(cmds):
        counts["uv_count"] += get_poly_evaluate_count(cmds, mesh, uvcoord=True)
        try:
            uv_sets = cmds.polyUVSet(mesh, query=True, allUVSets=True) or []
        except Exception:
            uv_sets = []
        counts["uv_set_count"] += len(uv_sets)
    return counts


def collect_scene_unit_values(cmds, file_path):
    """Collects the linear and angular scene units.

    Args:
        cmds (module): Maya commands module.
        file_path (str): Inspected file path.

    Returns:
        dict: Scene unit values.
    """
    return {
        "linear_unit": cmds.currentUnit(query=True, linear=True),
        "angular_unit": cmds.currentUnit(query=True, angle=True),
    }


REPORT_METRIC_COLLECTORS = {
    "frame_count": collect_frame_count_values,
    "frame_rate": collect_frame_rate_values,
    "file_size": collect_file_size_values,
    "time": collect_time_values,
    "mesh_count": collect_mesh_count_values,
    "joint_count": collect_joint_count_values,
    "transform_count": collect_transform_count_values,
    "geometry_counts": collect_geometry_count_values,
    "uv_counts": collect_uv_count_values,
    "scene_units": collect_scene_unit_values,
}
