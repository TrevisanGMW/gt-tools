"""
Batch Processor Merge Input Maya Runtime

Maya scene operations used by the Merge Input task. Maya modules are imported lazily
through batch_processor_maya so the task module stays importable outside Maya.
"""

from gt.tools.batch_processor import batch_processor_maya
from gt.tools.batch_processor.tasks import task_merge_input_utils as merge_utils
import logging


logger = logging.getLogger(__name__)

TIME_INPUT_ANIM_CURVE_TYPES = ["animCurveTL", "animCurveTA", "animCurveTT", "animCurveTU"]


def get_time_anim_curves(nodes=None):
    """Gets time-driven animation curves, ignoring driven-key curves.

    Args:
        nodes (list, optional): Nodes to filter. When omitted, every curve in the scene is returned.

    Returns:
        list: Animation curve node names.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    if nodes is None:
        return cmds.ls(type=TIME_INPUT_ANIM_CURVE_TYPES) or []
    existing_nodes = [node for node in nodes if cmds.objExists(node)]
    if not existing_nodes:
        return []
    return cmds.ls(existing_nodes, type=TIME_INPUT_ANIM_CURVE_TYPES) or []


def get_key_range(anim_curves=None):
    """Gets the frame range covered by time-driven animation curves.

    Uses OpenMaya to read only the first and last key of each curve, so the cost stays low
    even for scenes with many curves. Falls back to maya.cmds when OpenMaya is unavailable.

    Args:
        anim_curves (list, optional): Curves to inspect. When omitted, every time-driven curve is used.

    Returns:
        tuple: (start, end) frame range, or None when no keys exist.
    """
    if anim_curves is None:
        anim_curves = get_time_anim_curves()
    anim_curves = list(anim_curves or [])
    if not anim_curves:
        return None
    try:
        return _get_key_range_open_maya(anim_curves)
    except Exception as exception:
        logger.debug("OpenMaya key range failed, using maya.cmds: %s", exception)
    return _get_key_range_cmds(anim_curves)


def _get_key_range_open_maya(anim_curves):
    """Gets the key range with OpenMaya.

    Args:
        anim_curves (list): Animation curve node names.

    Returns:
        tuple: (start, end) frame range, or None when no keys exist.
    """
    import maya.api.OpenMaya as open_maya
    import maya.api.OpenMayaAnim as open_maya_anim

    ui_unit = open_maya.MTime.uiUnit()
    selection_list = open_maya.MSelectionList()
    for curve_name in anim_curves:
        selection_list.add(curve_name)
    time_ranges = []
    for selection_index in range(selection_list.length()):
        curve_function = open_maya_anim.MFnAnimCurve(selection_list.getDependNode(selection_index))
        key_count = curve_function.numKeys
        if not key_count:
            continue
        time_ranges.append(
            (
                curve_function.input(0).asUnits(ui_unit),
                curve_function.input(key_count - 1).asUnits(ui_unit),
            )
        )
    return merge_utils.combine_time_ranges(time_ranges)


def _get_key_range_cmds(anim_curves):
    """Gets the key range with maya.cmds.

    Args:
        anim_curves (list): Animation curve node names.

    Returns:
        tuple: (start, end) frame range, or None when no keys exist.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    first_key = cmds.findKeyframe(anim_curves, which="first")
    last_key = cmds.findKeyframe(anim_curves, which="last")
    return merge_utils.combine_time_ranges([(first_key, last_key)])


def get_scene_playback_range():
    """Gets the current scene playback range.

    Returns:
        tuple: (start, end) frame range.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    return (
        cmds.playbackOptions(query=True, minTime=True),
        cmds.playbackOptions(query=True, maxTime=True),
    )


def set_scene_time_range(time_range):
    """Sets the playback and animation range.

    Args:
        time_range (tuple): (start, end) frame range.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    start_frame, end_frame = float(time_range[0]), float(time_range[1])
    cmds.playbackOptions(
        animationStartTime=start_frame,
        animationEndTime=end_frame,
        minTime=start_frame,
        maxTime=end_frame,
    )
    cmds.currentTime(start_frame, edit=True)


def get_existing_namespaces():
    """Gets every namespace currently in the scene.

    Returns:
        set: Namespace names without the leading colon.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    namespaces = cmds.namespaceInfo(":", listOnlyNamespaces=True, recurse=True) or []
    return set(str(namespace).lstrip(":") for namespace in namespaces)


def load_input(file_path, load_mode, namespace="", deferred=False, load_plugins=True):
    """Imports or references one input file.

    Args:
        file_path (str): Input file path.
        load_mode (str): merge_utils.LOAD_MODE_IMPORT or merge_utils.LOAD_MODE_REFERENCE.
        namespace (str, optional): Namespace for the input. Empty imports into the root namespace.
            References always need a namespace; the caller supplies one.
        deferred (bool, optional): Create references unloaded.
        load_plugins (bool, optional): Load the importer plugin required by the file type.

    Returns:
        tuple: (new_nodes, reference_node). reference_node is empty for imports.
    """
    if load_mode != merge_utils.LOAD_MODE_REFERENCE:
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
    cmds = batch_processor_maya.get_maya_cmds()
    existing_nodes = [node for node in (nodes or []) if cmds.objExists(node)]
    if not existing_nodes:
        return []
    transforms = cmds.ls(existing_nodes, type="transform", long=True) or []
    root_transforms = []
    for transform in transforms:
        if transform.count("|") != 1:
            continue
        if transform in root_transforms:
            continue
        root_transforms.append(transform)
    return root_transforms


def get_node_ids(nodes):
    """Gets UUIDs for nodes so they can be found again after renames.

    Args:
        nodes (list): Node names.

    Returns:
        list: Node UUID strings.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    existing_nodes = [node for node in (nodes or []) if cmds.objExists(node)]
    if not existing_nodes:
        return []
    return cmds.ls(existing_nodes, uuid=True) or []


def get_nodes_from_ids(node_ids):
    """Gets current long node names from UUIDs.

    Args:
        node_ids (list): Node UUID strings.

    Returns:
        list: Current long node names, in the same order, skipping deleted nodes.
    """
    if not node_ids:
        return []
    cmds = batch_processor_maya.get_maya_cmds()
    return cmds.ls(node_ids, long=True) or []


def create_group(group_name, parent=None):
    """Creates an empty transform group with a unique name.

    Args:
        group_name (str): Preferred group name.
        parent (str, optional): Parent group.

    Returns:
        str: Long name of the created group.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    group_kwargs = {"empty": True, "name": merge_utils.sanitize_maya_name(group_name, "merge_grp")}
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
        name=merge_utils.sanitize_maya_name(layer_name, "merge_layer"),
        empty=True,
        noRecurse=True,
    )
    existing_members = [member for member in (members or []) if cmds.objExists(member)]
    if existing_members:
        cmds.editDisplayLayerMembers(layer, existing_members, noRecurse=True)
    return layer


def offset_animation(anim_curves, offset):
    """Shifts every key on the requested curves.

    Args:
        anim_curves (list): Animation curves to shift.
        offset (float): Frame offset.
    """
    if not anim_curves or not offset:
        return
    cmds = batch_processor_maya.get_maya_cmds()
    cmds.keyframe(anim_curves, edit=True, relative=True, timeChange=float(offset), option="over")


def remove_namespace(namespace):
    """Merges a namespace into the root namespace.

    Maya renames nodes whose names would clash with existing root nodes.

    Args:
        namespace (str): Namespace to remove.

    Returns:
        bool: True when the namespace was removed.
    """
    cmds = batch_processor_maya.get_maya_cmds()
    namespace = str(namespace or "").strip(":")
    if not namespace or not cmds.namespace(exists=f":{namespace}"):
        return False
    cmds.namespace(removeNamespace=f":{namespace}", mergeNamespaceWithRoot=True)
    return True


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
