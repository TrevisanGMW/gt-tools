"""
Animation Evaluator Service - Maya runtime operations used by the controller.
"""

from gt.core.motion_eval import checks_base
from gt.core.motion_eval import evaluation
from gt.core.motion_eval import presets
from gt.core.motion_eval import sampling
from gt.core.motion_eval import scene_io
from gt.core.motion_eval import templates
import logging

logger = logging.getLogger(__name__)


def get_maya_cmds():
    """Imports maya.cmds lazily.

    Returns:
        module: maya.cmds.
    """
    import maya.cmds as cmds

    return cmds


def get_selected_base_names():
    """Gets the selected transforms as base names (without path or namespace).

    Returns:
        list: Base names of the selected transforms, in selection order.
    """
    cmds = get_maya_cmds()
    names = []
    for node_path in cmds.ls(selection=True, long=True, type="transform") or []:
        names.append(templates.split_node_name(node_path)[1])
    return names


def resolve_template(template, require_biped=False):
    """Resolves template roles against the open scene.

    Args:
        template (dict): Skeleton template.
        require_biped (bool): Report missing biped roles as required.

    Returns:
        dict: Resolution dictionary.
    """
    return sampling.resolve_template_in_scene(template, require_biped=require_biped)


def detect_builtin_template():
    """Finds the built-in template that matches the scene.

    Returns:
        str or None: Built-in template key.
    """
    template_key, _resolution = templates.detect_builtin_template(sampling.list_template_candidates())
    return template_key


def resolve_frame_range(range_mode, custom_start, custom_end, mode, template=None, general_scope=None,
                        node_names=None):
    """Resolves the evaluated frame range.

    Args:
        range_mode (str): One of sampling.RANGE_MODES.
        custom_start (int): Custom start frame.
        custom_end (int): Custom end frame.
        mode (str): Evaluation mode.
        template (dict, optional): Skeleton used in biped mode and by the template scope.
        general_scope (str, optional): General-mode node scope.
        node_names (list, optional): Names for the node list scope.

    Returns:
        tuple: (start, end) frames.
    """
    node_paths = None
    if range_mode == sampling.RANGE_KEYED:
        node_paths = sampling.get_keyed_range_nodes(mode, template, general_scope, node_names)
    return sampling.resolve_frame_range(range_mode, custom_start, custom_end, node_paths=node_paths)


def evaluate(preset, template, range_mode, custom_start, custom_end, general_scope, node_names):
    """Evaluates the open scene and keeps the per-check graph series in the report.

    Args:
        preset (dict): Stored preset.
        template (dict or None): Skeleton, or None when the mode and scope do not use it.
        range_mode (str): Frame range mode.
        custom_start (int): Custom start frame.
        custom_end (int): Custom end frame.
        general_scope (str): General-mode node scope.
        node_names (list): Names for the node list scope.

    Returns:
        dict: Evaluation report.
    """
    mode = presets.resolve_preset(preset)["mode"]
    frame_range = resolve_frame_range(range_mode, custom_start, custom_end, mode, template, general_scope, node_names)
    return evaluation.evaluate_scene(
        preset=preset,
        template=template,
        frame_range=frame_range,
        general_scope=general_scope,
        node_names=node_names,
        include_series=True,
    )


def export_graphs(report, directory):
    """Writes the report graphs as PNG files.

    Args:
        report (dict): Evaluation report with graph series.
        directory (str): Output folder.

    Returns:
        list: Written file paths.
    """
    from gt.core.motion_eval import report_graphs

    return report_graphs.export_report_graphs(report, directory, file_prefix=report.get("scene") or "")


def write_score(report, options):
    """Writes the score attribute inside an undo chunk.

    Args:
        report (dict): Evaluation report.
        options (dict): Keyword arguments for scene_io.write_score.

    Returns:
        dict: Write outcome.
    """
    cmds = get_maya_cmds()
    cmds.undoInfo(openChunk=True, chunkName="Write Motion Score")
    try:
        return scene_io.write_score(report, write_policy=scene_io.WRITE_POLICY_OVERWRITE, **options)
    finally:
        cmds.undoInfo(closeChunk=True)


def go_to_frame(frame):
    """Moves the current time.

    Args:
        frame (int): Frame number.
    """
    get_maya_cmds().currentTime(frame)


def select_nodes(node_paths):
    """Selects existing nodes.

    Args:
        node_paths (list): Node paths.

    Returns:
        list: Selected node paths.
    """
    cmds = get_maya_cmds()
    existing = [path for path in node_paths if path and cmds.objExists(path)]
    if existing:
        cmds.select(existing, replace=True)
    return existing


def get_offender_nodes(report, offender_name):
    """Maps an offender label back to scene nodes where possible.

    Args:
        report (dict): Evaluation report.
        offender_name (str): Offender label from a check entry.

    Returns:
        list: Node paths.
    """
    roles = report.get("roles") or {}
    if "(" in offender_name and offender_name.endswith(")"):
        role_key = offender_name.rsplit("(", 1)[1].rstrip(")")
        if role_key in roles:
            return [roles[role_key]]
    lowered = offender_name.lower()
    for side in ("left", "right"):
        if lowered.startswith(side):
            part = lowered[len(side):].strip().split(" ")[0]
            role_by_part = {"foot": "foot", "knee": "leg", "thigh": "up_leg", "shin": "leg", "forearm": "forearm"}
            role_key = f"{side}_{role_by_part.get(part, part)}"
            if role_key in roles:
                return [roles[role_key]]
    cmds = get_maya_cmds()
    return cmds.ls(offender_name.split(" (")[0], long=True) or []


def is_biped_mode(preset_mode):
    """Checks whether a mode is biped.

    Args:
        preset_mode (str): Evaluation mode.

    Returns:
        bool: True for biped.
    """
    return preset_mode == checks_base.MODE_BIPED
