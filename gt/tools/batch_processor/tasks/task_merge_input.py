"""
Batch Processor Merge Input Task

Imports or references every incoming file into one Maya scene, so the combined
result can be reviewed in a single file.

Pure helpers come first, then the Maya runtime helpers, then the task class. Maya
modules are only imported at run time, so this module stays importable outside Maya.

Name and frame-range helpers shared with other tools live in gt.core.str and gt.core.timeline.
They are re-exported here so existing imports of this module keep working.
"""

from gt.core.str import build_unique_name, sanitize_maya_name  # noqa: F401 (re-exported)
from gt.core.timeline import (  # noqa: F401 (re-exported)
    build_sequential_offsets,
    combine_time_ranges,
    get_key_range,
    get_sequential_offset,
    get_time_anim_curves,
    is_valid_time_range,
    offset_animation,
    parse_playback_range_from_bytes,
    read_stored_playback_range,
)
import gt.core.timeline as core_timeline
from gt.tools.batch_processor import batch_processor_constants as constants
from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor import batch_processor_task_base as task_base
from gt.tools.batch_processor.tasks import task_utils
import gt.ui.resource_library as ui_res_lib
import logging
import os


logger = logging.getLogger(__name__)

INPUT_SCRIPT_SAMPLES_DIRECTORY = "merge_input/per_input"
POST_SCRIPT_SAMPLES_DIRECTORY = "merge_input/post_merge"
SCENE_EXTENSIONS = [".ma", ".mb"]
SCENE_SCALES = ["mm", "cm", "m", "in", "ft", "yd"]
SCENE_UP_AXES = ["Y", "Z"]

LOAD_MODE_IMPORT = "Import"
LOAD_MODE_REFERENCE = "Reference"
LOAD_MODES = [LOAD_MODE_IMPORT, LOAD_MODE_REFERENCE]

TIME_RANGE_KEYFRAMES = "Keyframes (All Inputs)"
TIME_RANGE_FIRST_INPUT = "First Input"
TIME_RANGE_MANUAL = "Manual"
TIME_RANGE_KEEP = "Keep Scene Range"
TIME_RANGE_MODES = [TIME_RANGE_KEYFRAMES, TIME_RANGE_FIRST_INPUT, TIME_RANGE_MANUAL, TIME_RANGE_KEEP]

TIMING_ORIGINAL = "Original Time"
TIMING_SEQUENTIAL = "Sequential"
TIMING_MODES = [TIMING_ORIGINAL, TIMING_SEQUENTIAL]

FAILURE_SKIP = "Skip Input"
FAILURE_STOP = "Fail Merge"
FAILURE_POLICIES = [FAILURE_SKIP, FAILURE_STOP]

INPUT_NAME_TOKEN = "{input-name}"
INPUT_INDEX_TOKEN = "{input-index}"
INPUT_INDEX_PADDED_TOKEN = "{input-index-padded}"
INPUT_TOKENS = [INPUT_NAME_TOKEN, INPUT_INDEX_TOKEN, INPUT_INDEX_PADDED_TOKEN]


def get_input_name(file_path):
    """Gets the display name of an input file without its extension.

    Args:
        file_path (str): Input file path.

    Returns:
        str: File base name without extension.
    """
    return os.path.splitext(os.path.basename(str(file_path or "")))[0]


def resolve_input_tokens(template, file_path, input_index, total_inputs):
    """Replaces Merge Input per-input tokens in a name template.

    Args:
        template (str): Template using {input-name}, {input-index}, or {input-index-padded}.
        file_path (str): Input file path.
        input_index (int): One-based input index.
        total_inputs (int): Number of inputs being merged.

    Returns:
        str: Template with input tokens replaced.
    """
    padding = max(2, len(str(max(1, int(total_inputs or 1)))))
    resolved_text = str(template or "")
    resolved_text = resolved_text.replace(INPUT_NAME_TOKEN, get_input_name(file_path))
    resolved_text = resolved_text.replace(INPUT_INDEX_PADDED_TOKEN, str(int(input_index)).zfill(padding))
    resolved_text = resolved_text.replace(INPUT_INDEX_TOKEN, str(int(input_index)))
    return resolved_text


def sort_input_paths(file_paths, sort_by_name=True):
    """Orders input paths deterministically.

    Args:
        file_paths (list): Input file paths.
        sort_by_name (bool, optional): Sort by case-insensitive path when True, keep incoming order otherwise.

    Returns:
        list: Ordered paths.
    """
    file_paths = list(file_paths or [])
    if not sort_by_name:
        return file_paths
    return sorted(file_paths, key=lambda path: os.path.normcase(os.path.normpath(str(path))))


def build_spatial_offset(input_index, spacing):
    """Builds the translation applied to one input when spreading inputs apart.

    Args:
        input_index (int): One-based input index.
        spacing (list): Per-input translation step as [x, y, z].

    Returns:
        list: Translation [x, y, z] for this input. The first input stays at the origin.
    """
    step_values = list(spacing or [0, 0, 0])[:3]
    while len(step_values) < 3:
        step_values.append(0.0)
    multiplier = max(0, int(input_index) - 1)
    return [float(value) * multiplier for value in step_values]


def resolve_time_range(mode, keyframe_range=None, first_input_range=None, manual_range=None):
    """Resolves the final playback range for a merged scene.

    Args:
        mode (str): One of TIME_RANGE_MODES.
        keyframe_range (tuple, optional): Range covering all time-based keys in the merged scene.
        first_input_range (tuple, optional): Range stored in, or keyed by, the first input.
        manual_range (tuple, optional): User-defined range.

    Returns:
        tuple: (start, end) range, or None when the scene range should not change.
    """
    candidates = {
        TIME_RANGE_KEYFRAMES: keyframe_range,
        TIME_RANGE_FIRST_INPUT: first_input_range,
        TIME_RANGE_MANUAL: manual_range,
    }
    time_range = candidates.get(mode)
    if not is_valid_time_range(time_range):
        return None
    return float(time_range[0]), float(time_range[1])


def build_input_record(file_path, input_index, load_mode):
    """Builds the per-input result dictionary shared with scripts and logs.

    Args:
        file_path (str): Input file path.
        input_index (int): One-based input index.
        load_mode (str): Import or Reference.

    Returns:
        dict: Record with default values filled in by the merge runtime.
    """
    return {
        "path": file_path,
        "name": get_input_name(file_path),
        "index": int(input_index),
        "load_mode": load_mode,
        "status": "pending",
        "namespace": "",
        "nodes": [],
        "root_nodes": [],
        "reference_node": "",
        "group": "",
        "display_layer": "",
        "time_range": None,
        "time_offset": 0.0,
        "message": "",
    }


# Maya runtime helpers. Maya modules are imported lazily through batch_processor_maya.


def get_scene_playback_range():
    """Gets the current scene playback range.

    Returns:
        tuple: (start, end) frame range.
    """
    return core_timeline.get_playback_range()


def set_scene_time_range(time_range):
    """Sets the playback and animation range.

    Args:
        time_range (tuple): (start, end) frame range.
    """
    core_timeline.set_playback_range(time_range)


def get_existing_namespaces():
    """Gets every namespace currently in the scene.

    Returns:
        set: Namespace names without the leading colon.
    """
    import gt.core.namespace as core_nspace

    return core_nspace.get_all_namespaces()


def load_input(file_path, load_mode, namespace="", deferred=False, load_plugins=True):
    """Imports or references one input file.

    Args:
        file_path (str): Input file path.
        load_mode (str): LOAD_MODE_IMPORT or LOAD_MODE_REFERENCE.
        namespace (str, optional): Namespace for the input. Empty imports into the root namespace.
            References always need a namespace; the caller supplies one.
        deferred (bool, optional): Create references unloaded.
        load_plugins (bool, optional): Load the importer plugin required by the file type.

    Returns:
        tuple: (new_nodes, reference_node). reference_node is empty for imports.
    """
    if load_mode != LOAD_MODE_REFERENCE:
        new_nodes = batch_processor_maya.import_file(
            file_path=file_path,
            namespace=namespace or None,
            load_relevant_plugins=load_plugins,
        )
        return list(new_nodes or []), ""
    cmds = batch_processor_maya.get_maya_cmds()
    if load_plugins:
        batch_processor_maya.load_relevant_file_plugin(file_path)
    references_before = set(cmds.ls(type="reference") or [])
    reference_kwargs = {
        "reference": True,
        "ignoreVersion": True,
        "returnNewNodes": True,
        "deferReference": bool(deferred),
    }
    if namespace:
        reference_kwargs["namespace"] = namespace
    new_nodes = cmds.file(file_path, **reference_kwargs) or []
    new_references = sorted(set(cmds.ls(type="reference") or []) - references_before)
    reference_node = ""
    for candidate_node in new_references:
        if candidate_node.endswith("sharedReferenceNode"):
            continue
        try:
            cmds.referenceQuery(candidate_node, filename=True)
        except RuntimeError:
            continue
        reference_node = candidate_node
        break
    return list(new_nodes), reference_node


def get_root_transforms(nodes):
    """Gets top-level DAG transforms from a node list.

    Args:
        nodes (list): Node names returned by an import or reference.

    Returns:
        list: Long names of transforms without a parent, in a stable order.
    """
    import gt.core.hierarchy as core_hrchy

    return core_hrchy.get_root_transforms(nodes)


def get_node_ids(nodes):
    """Gets UUIDs for nodes so they can be found again after renames.

    Args:
        nodes (list): Node names.

    Returns:
        list: Node UUID strings.
    """
    import gt.core.uuid as core_uuid

    return core_uuid.get_uuids(nodes)


def get_nodes_from_ids(node_ids):
    """Gets current long node names from UUIDs.

    Args:
        node_ids (list): Node UUID strings.

    Returns:
        list: Current long node names, in the same order, skipping deleted nodes.
    """
    import gt.core.uuid as core_uuid

    return core_uuid.get_objects_from_uuids(node_ids)


def create_group(group_name, parent=None):
    """Creates an empty transform group with a unique name.

    Args:
        group_name (str): Preferred group name.
        parent (str, optional): Parent group.

    Returns:
        str: Long name of the created group.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    group_kwargs = {"empty": True, "name": sanitize_maya_name(group_name, "merge_grp")}
    if parent:
        group_kwargs["parent"] = parent
    created_group = cmds.group(**group_kwargs)
    return (cmds.ls(created_group, long=True) or [created_group])[0]


def parent_nodes(nodes, parent):
    """Parents nodes under a group and returns their new long names.

    Args:
        nodes (list): Transform names to parent.
        parent (str): Parent transform.

    Returns:
        list: New long names of the parented nodes.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    existing_nodes = [node for node in (nodes or []) if cmds.objExists(node)]
    if not existing_nodes:
        return []
    parented_nodes = cmds.parent(existing_nodes, parent) or []
    return cmds.ls(parented_nodes, long=True) or parented_nodes


def set_translation(transform, translation):
    """Sets a transform translation.

    Args:
        transform (str): Transform name.
        translation (list): Translation as [x, y, z].
    """
    cmds = batch_processor_maya.get_maya_cmds()
    cmds.setAttr(f"{transform}.translate", float(translation[0]), float(translation[1]), float(translation[2]))


def create_display_layer(layer_name, members):
    """Creates a display layer containing the requested members.

    Args:
        layer_name (str): Preferred layer name.
        members (list): Nodes added to the layer.

    Returns:
        str: Created layer name.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    layer = cmds.createDisplayLayer(
        name=sanitize_maya_name(layer_name, "merge_layer"),
        empty=True,
        noRecurse=True,
    )
    existing_members = [member for member in (members or []) if cmds.objExists(member)]
    if existing_members:
        cmds.editDisplayLayerMembers(layer, existing_members, noRecurse=True)
    return layer


def remove_namespace(namespace):
    """Merges a namespace into the root namespace.

    Maya renames nodes whose names would clash with existing root nodes.

    Args:
        namespace (str): Namespace to remove.

    Returns:
        bool: True when the namespace was removed.
    """
    import gt.core.namespace as core_nspace

    return core_nspace.merge_namespace_with_root(namespace)


def set_scene_file_type(file_type):
    """Sets the current scene file type before nodes are merged into it.

    Maya refuses to change a scene's format at save time when it holds unknown nodes, for
    example nodes from a plugin that failed to load (mtoa in mayapy workers). A new scene in
    mayapy is mayaBinary, so saving a .ma output would fail. Setting the type up front means
    the save keeps the same format and the unknown nodes are preserved.

    Args:
        file_type (str): Maya file type, e.g. "mayaAscii" or "mayaBinary".
    """
    cmds = batch_processor_maya.get_maya_cmds()
    cmds.file(type=file_type)


def open_base_scene(file_path, load_plugins=True):
    """Opens the scene used as the merge starting point.

    Args:
        file_path (str): Base scene path.
        load_plugins (bool, optional): Load the plugin required by the file type.
    """
    batch_processor_maya.open_scene(file_path, load_relevant_plugins=load_plugins)


class TaskMergeInput(task_base.BatchTask):
    """Aggregate task that merges every incoming file into one Maya scene."""

    task_type = constants.TaskType.MERGE_INPUT
    default_display_name = "Merge Input"
    default_target_path_template = "{project-dir}/{task-dir}/{task-idx-padded}_merge_input"
    icon = ui_res_lib.Icon.batch_task_merge_input
    category = "Outputs"
    category_icon = ui_res_lib.Icon.batch_category_outputs
    is_aggregate_task = True
    is_output_task = True
    supports_run_once_after_jobs = True
    input_script_samples_directory = INPUT_SCRIPT_SAMPLES_DIRECTORY
    post_script_samples_directory = POST_SCRIPT_SAMPLES_DIRECTORY

    def get_default_settings(self):
        """Gets default Merge Input settings.

        Returns:
            dict: Default task settings.
        """
        return {
            "source_path": "{previous-task-path}",
            "allow_missing_input_directory": False,
            "target_path": self.default_target_path_template,
            "output_name": "{project-sanitized-name}_merged",
            "output_extension": ".ma",
            "load_mode": LOAD_MODE_IMPORT,
            "namespace": INPUT_NAME_TOKEN,
            "remove_namespace": False,
            "reference_deferred": False,
            "load_relevant_plugins": True,
            "sort_inputs_by_name": False,
            "on_input_failure": FAILURE_SKIP,
            "input_count_warning": 50,
            "base_scene_path": "",
            "set_framerate": False,
            "framerate": 30,
            "set_scene_scale": False,
            "scene_scale": "cm",
            "set_scene_up_axis": False,
            "scene_up_axis": "Y",
            "group_each_input": False,
            "input_group_name": f"{INPUT_NAME_TOKEN}_grp",
            "group_all_inputs": False,
            "merge_group_name": "merged_inputs_grp",
            "display_layer_per_input": False,
            "display_layer_name": f"{INPUT_NAME_TOKEN}_lyr",
            "offset_inputs": False,
            "input_offset": [200.0, 0.0, 0.0],
            "time_range_mode": TIME_RANGE_KEYFRAMES,
            "manual_start_frame": 1.0,
            "manual_end_frame": 120.0,
            "timing_mode": TIMING_ORIGINAL,
            "sequential_gap_frames": 0.0,
            "run_input_script": False,
            "input_script_text": "",
            "input_script_collapsed": True,
            "input_script_font_size": 14,
            "input_script_pass_standard_arguments": True,
            "input_script_pass_environment_arguments": True,
            "run_post_script": False,
            "post_script_text": "",
            "post_script_collapsed": True,
            "post_script_font_size": 14,
            "post_script_pass_standard_arguments": True,
            "post_script_pass_environment_arguments": True,
            "overwrite": False,
            "run_once_after_multi_instance": True,
            "force_segment_separator": False,
            "segmentation_collapsed": True,
            "segment_name": self.default_segment_name,
            "segment_color": "blue_light_sky",
        }

    # ------------------------------------------------------------------ validation
    def validate(self, project):
        """Validates Merge Input settings.

        Args:
            project (BatchProcessorModel): Project containing this task.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        if self.modifies_in_place():
            result.add_error("Merge Input cannot modify source files in place. Use a target path or Keep Open.")
        if not self.passes_through():
            if self.get_output_extension() not in SCENE_EXTENSIONS:
                result.add_error("Merge Input output extension must be .ma or .mb.")
            if not str(self.settings.get("output_name") or "").strip():
                result.add_error("Merge Input output name cannot be empty.")
        if self.settings.get("load_mode") not in LOAD_MODES:
            result.add_error(f"Merge Input load mode must be one of: {', '.join(LOAD_MODES)}.")
        if self.settings.get("time_range_mode") not in TIME_RANGE_MODES:
            result.add_error("Merge Input time range mode is not recognized.")
        if self.settings.get("time_range_mode") == TIME_RANGE_MANUAL:
            manual_range = self.get_manual_range()
            if not is_valid_time_range(manual_range):
                result.add_error("Merge Input manual start frame must be lower than or equal to the end frame.")
        result.extend(self.validate_scene_options())
        result.extend(self.validate_reference_options())
        result.extend(self.validate_scripts())
        base_scene_path = self.resolve_base_scene_path(project)
        if self.settings.get("base_scene_path") and not os.path.isfile(base_scene_path):
            missing_path = base_scene_path or self.settings.get("base_scene_path")
            result.add_error(f"Merge Input base scene does not exist: {missing_path}")
        return result

    def validate_scene_options(self):
        """Validates the optional scene unit, framerate, and up-axis settings.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        if self.settings.get("set_framerate"):
            try:
                if int(float(self.settings.get("framerate"))) < 1:
                    result.add_error("Merge Input framerate must be greater than zero.")
            except (TypeError, ValueError):
                result.add_error("Merge Input framerate must be numeric.")
        if self.settings.get("set_scene_scale"):
            if str(self.settings.get("scene_scale") or "").lower() not in SCENE_SCALES:
                result.add_error(f"Merge Input scene scale must be one of: {', '.join(SCENE_SCALES)}.")
        if self.settings.get("set_scene_up_axis"):
            if str(self.settings.get("scene_up_axis") or "").upper() not in SCENE_UP_AXES:
                result.add_error("Merge Input scene up axis must be Y or Z.")
        return result

    def validate_reference_options(self):
        """Flags options that cannot apply to referenced inputs.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        if not self.uses_reference_mode():
            return result
        if self.settings.get("remove_namespace"):
            result.add_warning(
                "Merge Input: Remove Namespace is ignored in Reference mode. Referenced nodes keep their namespace."
            )
        if self.settings.get("timing_mode") == TIMING_SEQUENTIAL:
            result.add_warning(
                "Merge Input: Sequential timing is ignored in Reference mode. Referenced keys keep their original time."
            )
        if not str(self.settings.get("namespace") or "").strip():
            result.add_warning(
                f"Merge Input: References need a namespace. {INPUT_NAME_TOKEN} is used when empty."
            )
        return result

    def validate_scripts(self):
        """Validates the optional per-input and post-merge scripts.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        if self.settings.get("run_input_script") and not str(self.settings.get("input_script_text") or "").strip():
            result.add_error("Merge Input per-input script is enabled but no inline script is set.")
        if self.settings.get("run_post_script") and not str(self.settings.get("post_script_text") or "").strip():
            result.add_error("Merge Input post-merge script is enabled but no inline script is set.")
        return result

    def validate_work_items(self, work_items, project, step_output_dir, context=None):
        """Checks the input list and output path before merging.

        Args:
            work_items (list): Work items entering this task.
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for this step.
            context (dict, optional): Runtime context.

        Returns:
            ValidationResult: Collected validation result.
        """
        result = task_base.ValidationResult()
        warning_count = self.get_input_count_warning()
        if warning_count and len(work_items or []) > warning_count:
            result.add_warning(
                f"Merge Input will merge {len(work_items)} inputs into one scene (warning threshold: "
                f"{warning_count}). Large merges can use a lot of memory."
            )
        if self.passes_through():
            return result
        output_path = self.build_output_path(project, step_output_dir)
        if os.path.exists(output_path) and not self.settings.get("overwrite", False):
            result.add_warning(f"Merge Input output already exists and will be skipped: {output_path}")
        return result

    # ------------------------------------------------------------------ settings helpers
    def uses_reference_mode(self):
        """Checks whether inputs are referenced instead of imported.

        Returns:
            bool: True in Reference mode.
        """
        return self.settings.get("load_mode") == LOAD_MODE_REFERENCE

    def get_output_extension(self):
        """Gets the normalized output extension.

        Returns:
            str: Output extension with a leading dot.
        """
        extension = str(self.settings.get("output_extension") or ".ma").lower()
        if not extension.startswith("."):
            extension = f".{extension}"
        return extension

    def get_manual_range(self):
        """Gets the manual frame range.

        Returns:
            tuple: (start, end), or None when the values are not numeric.
        """
        try:
            return float(self.settings.get("manual_start_frame")), float(self.settings.get("manual_end_frame"))
        except (TypeError, ValueError):
            return None

    def get_input_count_warning(self):
        """Gets the input count that triggers a large-merge warning.

        Returns:
            int: Threshold, or 0 when disabled.
        """
        try:
            return max(0, int(self.settings.get("input_count_warning") or 0))
        except (TypeError, ValueError):
            return 0

    def get_input_offset(self):
        """Gets the per-input spatial offset step.

        Returns:
            list: [x, y, z] offset step.
        """
        offset_values = list(self.settings.get("input_offset") or [0.0, 0.0, 0.0])[:3]
        while len(offset_values) < 3:
            offset_values.append(0.0)
        try:
            return [float(value) for value in offset_values]
        except (TypeError, ValueError):
            return [0.0, 0.0, 0.0]

    def resolve_base_scene_path(self, project):
        """Resolves the optional base scene path.

        Args:
            project (BatchProcessorModel): Active project model.

        Returns:
            str: Resolved base scene path, or an empty string when unset.
        """
        base_scene_path = str(self.settings.get("base_scene_path") or "").strip()
        if not base_scene_path or not project:
            return ""
        task_index = None
        if hasattr(project, "get_task_environment_index"):
            task_index = project.get_task_environment_index(self)
        return project.resolve_template_path(base_scene_path, task=self, task_index=task_index)

    def build_output_path(self, project, step_output_dir):
        """Builds the merged scene output path.

        Args:
            project (BatchProcessorModel): Active project model.
            step_output_dir (str): Output folder for this step.

        Returns:
            str: Merged scene path.
        """
        output_name = str(self.settings.get("output_name") or "merged")
        if project:
            output_name = project.resolve_template(output_name, task=self)
        if output_name.lower().endswith(tuple(SCENE_EXTENSIONS)):
            output_name = os.path.splitext(output_name)[0]
        file_name = f"{task_base.sanitize_filename(output_name, 'merged')}{self.get_output_extension()}"
        return os.path.normpath(os.path.join(step_output_dir, file_name))

    def resolve_input_name(self, setting_key, file_path, input_index, total_inputs, project=None):
        """Resolves a per-input name template into a Maya-safe name.

        Args:
            setting_key (str): Setting containing the template.
            file_path (str): Input file path.
            input_index (int): One-based input index.
            total_inputs (int): Number of inputs being merged.
            project (BatchProcessorModel, optional): Project used for environment variables.

        Returns:
            str: Maya-safe name, or an empty string when the template is empty.
        """
        template = str(self.settings.get(setting_key) or "").strip()
        if not template:
            return ""
        resolved_name = resolve_input_tokens(template, file_path, input_index, total_inputs)
        if project and "{" in resolved_name:
            resolved_name = project.resolve_template(resolved_name, task=self)
        return sanitize_maya_name(resolved_name, get_input_name(file_path))

    # ------------------------------------------------------------------ execution
    def execute(self, work_item, project, step_output_dir, context=None):
        """Merges every incoming file into one Maya scene.

        Args:
            work_item (WorkItem): Unused aggregate work item.
            project (BatchProcessorModel): Active project.
            step_output_dir (str): Output directory.
            context (dict, optional): Runtime context containing work_items.

        Returns:
            WorkItem or list: Merged scene work item, or the incoming items when Keep Open is used.
        """
        context = context or {}
        work_items = list(context.get("work_items") or [])
        if not work_items:
            raise task_base.TaskSkip("No incoming files to merge.")
        output_path = "" if self.passes_through() else self.build_output_path(project, step_output_dir)
        if output_path and os.path.exists(output_path) and not self.settings.get("overwrite", False):
            raise task_base.TaskSkip(
                f"Merged scene already exists and overwrite is disabled: {output_path}",
                output_path=output_path,
            )
        ordered_items = self.order_work_items(work_items)
        self.prepare_scene(project)
        merge_state = {
            "records": [],
            "used_namespaces": get_existing_namespaces(),
            "next_start": None,
            "merge_group": "",
        }
        if self.settings.get("group_all_inputs"):
            merge_group_name = self.settings.get("merge_group_name") or "merged_inputs_grp"
            merge_state["merge_group"] = create_group(merge_group_name)
        progress_total = len(ordered_items)
        self.report_progress(context, 0, progress_total)
        for input_index, input_item in enumerate(ordered_items, 1):
            record = self.merge_input_with_policy(
                project=project,
                input_item=input_item,
                input_index=input_index,
                total_inputs=len(ordered_items),
                merge_state=merge_state,
                output_path=output_path,
                context=context,
            )
            merge_state["records"].append(record)
            self.report_progress(context, input_index, progress_total)
        merged_records = [record for record in merge_state["records"] if record["status"] == "merged"]
        if not merged_records:
            raise RuntimeError("Merge Input could not merge any input. Check the log for per-input errors.")
        time_range = self.apply_time_range(merge_state["records"])
        self.run_post_script(project, merge_state, time_range, output_path, context)
        if output_path:
            batch_processor_maya.save_scene(output_path, file_type=batch_processor_maya.get_maya_file_type(output_path))
        failed_count = len(merge_state["records"]) - len(merged_records)
        self.report(
            context,
            f"Merged {len(merged_records)} of {len(merge_state['records'])} input(s)"
            f"{f' ({failed_count} skipped)' if failed_count else ''}"
            f"{f' into: {output_path}' if output_path else ' (scene kept open, not saved)'}",
        )
        if not output_path:
            return work_items
        metadata = {
            "last_task_id": self.id,
            "last_task_type": self.task_type,
            "settings_hash": task_base.hash_settings(self.settings),
            "merged_inputs": len(merged_records),
            "failed_inputs": failed_count,
            "time_range": list(time_range) if time_range else None,
        }
        return task_base.WorkItem(source_path=output_path, current_path=output_path, metadata=metadata)

    def order_work_items(self, work_items):
        """Orders work items for a deterministic merge.

        Args:
            work_items (list): Incoming work items.

        Returns:
            list: Ordered work items.
        """
        if not self.settings.get("sort_inputs_by_name", False):
            return list(work_items)
        return sorted(
            work_items,
            key=lambda item: os.path.normcase(os.path.normpath(str(item.current_path))),
        )

    def prepare_scene(self, project):
        """Starts the merge scene and applies optional scene settings.

        Args:
            project (BatchProcessorModel): Active project model.
        """
        load_plugins = self.settings.get("load_relevant_plugins", True)
        base_scene_path = self.resolve_base_scene_path(project)
        if base_scene_path:
            open_base_scene(base_scene_path, load_plugins=load_plugins)
        else:
            batch_processor_maya.new_scene()
        if not self.passes_through():
            set_scene_file_type(batch_processor_maya.get_maya_file_type(self.get_output_extension()))
        batch_processor_maya.apply_scene_options(self.settings)

    def merge_input_with_policy(
        self, project, input_item, input_index, total_inputs, merge_state, output_path, context
    ):
        """Merges one input and applies the failure policy.

        Args:
            project (BatchProcessorModel): Active project model.
            input_item (WorkItem): Input being merged.
            input_index (int): One-based input index.
            total_inputs (int): Number of inputs being merged.
            merge_state (dict): Shared merge state.
            output_path (str): Merged scene path.
            context (dict): Runtime context.

        Returns:
            dict: Input record with status "merged" or "failed".

        Raises:
            RuntimeError: When an input fails and the policy is Fail Merge.
        """
        record = build_input_record(
            file_path=input_item.current_path,
            input_index=input_index,
            load_mode=self.settings.get("load_mode") or LOAD_MODE_IMPORT,
        )
        try:
            self.merge_single_input(project, input_item, record, total_inputs, merge_state)
            self.run_input_script(project, input_item, record, merge_state, total_inputs, output_path, context)
            record["status"] = "merged"
            self.report(context, f"[{input_index}/{total_inputs}] Merged: {input_item.current_path}")
        except Exception as exception:
            record["status"] = "failed"
            record["message"] = str(exception)
            logger.warning("Merge Input failed on %s: %s", input_item.current_path, exception, exc_info=True)
            if self.settings.get("on_input_failure") == FAILURE_STOP:
                raise RuntimeError(f"Failed merging {input_item.current_path}: {exception}")
            self.report(
                context,
                f"[{input_index}/{total_inputs}] Skipped after error: {input_item.current_path} - {exception}",
                "WARNING",
            )
        return record

    def merge_single_input(self, project, input_item, record, total_inputs, merge_state):
        """Loads one input and applies namespace, timing, grouping, and layer options.

        Args:
            project (BatchProcessorModel): Active project model.
            input_item (WorkItem): Input being merged.
            record (dict): Input record updated in place.
            total_inputs (int): Number of inputs being merged.
            merge_state (dict): Shared merge state.
        """
        file_path = input_item.current_path
        input_index = record["index"]
        is_reference = self.uses_reference_mode()
        namespace = self.resolve_input_name("namespace", file_path, input_index, total_inputs, project)
        if is_reference and not namespace:
            namespace = sanitize_maya_name(get_input_name(file_path))
        if namespace:
            namespace = build_unique_name(namespace, merge_state["used_namespaces"])
        new_nodes, reference_node = load_input(
            file_path=file_path,
            load_mode=record["load_mode"],
            namespace=namespace,
            deferred=bool(is_reference and self.settings.get("reference_deferred")),
            load_plugins=self.settings.get("load_relevant_plugins", True),
        )
        record.update({"namespace": namespace, "reference_node": reference_node})
        node_ids = get_node_ids(new_nodes)
        record["time_range"] = self.get_input_time_range(file_path, new_nodes, input_index)
        self.apply_sequential_timing(record, new_nodes, merge_state)
        if self.settings.get("remove_namespace") and not is_reference and namespace:
            if remove_namespace(namespace):
                record["namespace"] = ""
        current_nodes = get_nodes_from_ids(node_ids) or list(new_nodes)
        record["nodes"] = current_nodes
        record["root_nodes"] = get_root_transforms(current_nodes)
        self.apply_grouping(project, record, total_inputs, merge_state)
        if self.settings.get("display_layer_per_input"):
            layer_members = [record["group"]] if record["group"] else record["root_nodes"]
            if layer_members:
                layer_name = self.resolve_input_name(
                    "display_layer_name", file_path, input_index, total_inputs, project
                )
                record["display_layer"] = create_display_layer(
                    layer_name or f"{record['name']}_lyr", layer_members
                )

    def get_input_time_range(self, file_path, new_nodes, input_index):
        """Gets an input's own frame range only when an option needs it.

        Keyframe ranges are otherwise computed once, after every input is merged.

        Args:
            file_path (str): Input file path.
            new_nodes (list): Nodes created by this input.
            input_index (int): One-based input index.

        Returns:
            tuple: (start, end) range, or None when not needed or not available.
        """
        uses_first_input = (
            input_index == 1 and self.settings.get("time_range_mode") == TIME_RANGE_FIRST_INPUT
        )
        uses_sequential = (
            self.settings.get("timing_mode") == TIMING_SEQUENTIAL and not self.uses_reference_mode()
        )
        if not uses_first_input and not uses_sequential:
            return None
        if uses_first_input and not uses_sequential:
            stored_range = read_stored_playback_range(file_path)
            if stored_range:
                return stored_range
        return get_key_range(get_time_anim_curves(new_nodes))

    def apply_sequential_timing(self, record, new_nodes, merge_state):
        """Shifts an imported input so it starts after the previous input.

        Args:
            record (dict): Input record updated in place.
            new_nodes (list): Nodes created by this input.
            merge_state (dict): Shared merge state.
        """
        if self.settings.get("timing_mode") != TIMING_SEQUENTIAL or self.uses_reference_mode():
            return
        offset, merge_state["next_start"] = get_sequential_offset(
            record["time_range"],
            merge_state["next_start"],
            gap_frames=self.settings.get("sequential_gap_frames") or 0,
        )
        if not offset:
            return
        offset_animation(get_time_anim_curves(new_nodes), offset)
        record["time_offset"] = offset
        start_frame, end_frame = record["time_range"]
        record["time_range"] = (start_frame + offset, end_frame + offset)

    def apply_grouping(self, project, record, total_inputs, merge_state):
        """Groups an input's root nodes and applies the optional spatial offset.

        Args:
            project (BatchProcessorModel): Active project model.
            record (dict): Input record updated in place.
            total_inputs (int): Number of inputs being merged.
            merge_state (dict): Shared merge state.
        """
        merge_group = merge_state.get("merge_group") or ""
        wants_input_group = self.settings.get("group_each_input") or self.settings.get("offset_inputs")
        if not record["root_nodes"]:
            return
        if not wants_input_group:
            if merge_group:
                record["root_nodes"] = parent_nodes(record["root_nodes"], merge_group)
            return
        group_name = self.resolve_input_name(
            "input_group_name", record["path"], record["index"], total_inputs, project
        )
        record["group"] = create_group(group_name or f"{record['name']}_grp", parent=merge_group or None)
        record["root_nodes"] = parent_nodes(record["root_nodes"], record["group"])
        if self.settings.get("offset_inputs"):
            set_translation(
                record["group"],
                build_spatial_offset(record["index"], self.get_input_offset()),
            )

    def apply_time_range(self, records):
        """Resolves and applies the merged scene time range.

        Args:
            records (list): Input records.

        Returns:
            tuple: Applied (start, end) range, or None when the range was left unchanged.
        """
        mode = self.settings.get("time_range_mode") or TIME_RANGE_KEYFRAMES
        keyframe_range = None
        if mode == TIME_RANGE_KEYFRAMES:
            keyframe_range = get_key_range()
        first_input_range = None
        if records and records[0]["status"] == "merged":
            first_input_range = records[0]["time_range"]
        time_range = resolve_time_range(
            mode,
            keyframe_range=keyframe_range,
            first_input_range=first_input_range,
            manual_range=self.get_manual_range(),
        )
        if time_range:
            set_scene_time_range(time_range)
        elif mode != TIME_RANGE_KEEP:
            logger.info("Merge Input: no %s range found; the scene range was left unchanged.", mode)
        return time_range

    # ------------------------------------------------------------------ scripts
    def run_input_script(self, project, input_item, record, merge_state, total_inputs, output_path, context):
        """Runs the optional per-input script after an input is merged.

        Args:
            project (BatchProcessorModel): Active project model.
            input_item (WorkItem): Input that was merged.
            record (dict): Input record.
            merge_state (dict): Shared merge state.
            total_inputs (int): Number of inputs being merged.
            output_path (str): Merged scene path.
            context (dict): Runtime context.
        """
        script_text = str(self.settings.get("input_script_text") or "")
        if not self.settings.get("run_input_script") or not script_text.strip():
            return
        runtime_context = task_utils.build_python_script_runtime_context(
            project=project,
            task=self,
            work_item=input_item,
            output_path=output_path,
            context=context,
            extra_values={
                "project": project,
                "task": self,
                "work_item": input_item,
                "output_path": output_path,
                "input_record": record,
                "input_path": record["path"],
                "input_index": record["index"],
                "total_inputs": total_inputs,
                "namespace": record["namespace"],
                "load_mode": record["load_mode"],
                "reference_node": record["reference_node"],
                "merged_nodes": list(record["nodes"]),
                "root_nodes": list(record["root_nodes"]),
                "input_group": record["group"],
                "merge_group": merge_state.get("merge_group") or "",
                "merged_records": list(merge_state["records"]),
            },
            pass_standard_arguments=self.settings.get("input_script_pass_standard_arguments", True),
            pass_environment_arguments=self.settings.get("input_script_pass_environment_arguments", True),
        )
        task_utils.run_inline_python_script(script_text, runtime_context, script_name="<merge_input_per_input_script>")

    def run_post_script(self, project, merge_state, time_range, output_path, context):
        """Runs the optional post-merge script before the scene is saved.

        Args:
            project (BatchProcessorModel): Active project model.
            merge_state (dict): Shared merge state.
            time_range (tuple): Applied time range, or None.
            output_path (str): Merged scene path.
            context (dict): Runtime context.
        """
        script_text = str(self.settings.get("post_script_text") or "")
        if not self.settings.get("run_post_script") or not script_text.strip():
            return
        records = list(merge_state["records"])
        summary_item = task_base.WorkItem(source_path=output_path, current_path=output_path)
        runtime_context = task_utils.build_python_script_runtime_context(
            project=project,
            task=self,
            work_item=summary_item,
            output_path=output_path,
            context=context,
            extra_values={
                "project": project,
                "task": self,
                "output_path": output_path,
                "merged_records": records,
                "merged_inputs": [record for record in records if record["status"] == "merged"],
                "failed_inputs": [record for record in records if record["status"] == "failed"],
                "merge_group": merge_state.get("merge_group") or "",
                "time_range": time_range,
            },
            pass_standard_arguments=self.settings.get("post_script_pass_standard_arguments", True),
            pass_environment_arguments=self.settings.get("post_script_pass_environment_arguments", True),
        )
        task_utils.run_inline_python_script(script_text, runtime_context, script_name="<merge_input_post_script>")

    @staticmethod
    def report_progress(context, completed_units, total_units):
        """Sends merge progress to the tracker progress bar when a callback is available.

        One unit per input. The tracker holds the bar below 100% until the task finishes saving.

        Args:
            context (dict): Runtime context.
            completed_units (int): Units finished so far.
            total_units (int): Total units.
        """
        callback = (context or {}).get("report_progress")
        if not callable(callback):
            return
        try:
            callback(completed_units=int(completed_units), total_units=int(total_units), unit_label="")
        except Exception as exception:
            logger.debug("Merge Input progress callback failed: %s", exception)

    def report(self, context, message, level="INFO"):
        """Sends a concise message to the tracker, or stdout when no tracker is attached.

        Args:
            context (dict): Runtime context.
            message (str): Message text.
            level (str, optional): Log level label.
        """
        formatted_message = f"[{level}] - ({self.task_type}) - {message}"
        reporter = (context or {}).get("report_message")
        if callable(reporter):
            try:
                reporter(formatted_message)
                return
            except Exception:
                pass
        print(formatted_message, flush=True)
