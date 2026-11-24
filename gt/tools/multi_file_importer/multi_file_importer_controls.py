"""
Multi-File Importer Controls

Maya runtime helpers that place imported files:
- keep skinned geometry from being moved twice (once by its joints, once by an offset parent);
- apply a static offset; or
- build "layout controls": a node whose attributes keep driving each file's position after the import
  (column/row spacing or line step, plus a separator, offset and visibility per file).

The controls use multiplyDivide/plusMinusAverage/composeMatrix nodes (no expressions or script nodes).
"""

from gt.tools.multi_file_importer import multi_file_importer_constants as constants
from gt.tools.multi_file_importer import multi_file_importer_layout as layout
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

IDENTITY_MATRIX = [1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0]
CONTROL_NODE_ATTRIBUTE = "multiFileImporterLayout"


def get_driven_nodes(record):
    """Gets the nodes that move a file: its group, or its top-level nodes when it has no group.

    Args:
        record (dict): Import record.

    Returns:
        list: Node names.
    """
    return [record["group"]] if record.get("group") else list(record.get("root_nodes") or [])


def protect_skinned_geometry(record):
    """Stops skinned geometry under a file's driven nodes from inheriting parent transforms.

    The world position is preserved, so the geometry stays where it is and keeps following its joints
    when an offset moves the group. Skinned top-level nodes are removed from the record's movable roots.

    Args:
        record (dict): Import record, updated in place ("protected_nodes", "root_nodes").

    Returns:
        list: Messages for nodes that could not be protected.
    """
    import maya.cmds as cmds
    import gt.core.skin as core_skin

    messages = []
    skinned_transforms = core_skin.get_skinned_transforms(get_driven_nodes(record))
    root_nodes = set(record.get("root_nodes") or [])
    protected_nodes = []
    for transform in skinned_transforms:
        if not record.get("group") and transform in root_nodes:
            protected_nodes.append(transform)
            continue
        try:
            if cmds.getAttr(f"{transform}.inheritsTransform"):
                cmds.inheritTransform(transform, off=True, preserve=True)
            protected_nodes.append(transform)
        except Exception as exception:
            messages.append(f'Unable to keep skinned "{transform}" in place: {exception}')
    record["protected_nodes"] = protected_nodes
    if not record.get("group"):
        record["root_nodes"] = [node for node in record.get("root_nodes") or [] if node not in protected_nodes]
    return messages


def apply_static_offset(record, offset):
    """Moves a file's content by a fixed offset.

    The per-file group is translated when it exists. Otherwise each top-level node gets the offset on its
    offsetParentMatrix, which keeps animation on translate untouched.

    Args:
        record (dict): Import record.
        offset (list): Offset [x, y, z].

    Returns:
        list: Messages for nodes that could not be moved.
    """
    import maya.cmds as cmds

    messages = []
    if not any(abs(value) > 0 for value in offset):
        return messages
    if record.get("group"):
        cmds.setAttr(f"{record['group']}.translate", *offset)
        return messages
    matrix = list(IDENTITY_MATRIX)
    matrix[12:15] = offset
    for root_node in record.get("root_nodes") or []:
        try:
            if cmds.attributeQuery("offsetParentMatrix", node=root_node, exists=True):
                cmds.setAttr(f"{root_node}.offsetParentMatrix", matrix, type="matrix")
            else:
                cmds.xform(root_node, translation=offset, relative=True, worldSpace=True)
        except Exception as exception:
            messages.append(f'Unable to offset "{root_node}": {exception}')
    return messages


def create_control_node(settings, top_group=""):
    """Gets the node that holds the layout attributes: the top group, or a new locator at the origin.

    Args:
        settings (dict): Tool settings.
        top_group (str, optional): Top group created by "Parent all under".

    Returns:
        str: Control node long name.
    """
    import maya.cmds as cmds
    import gt.core.str as core_str

    if top_group:
        control_node = top_group
    else:
        control_name = core_str.sanitize_maya_name(settings.get("layout_controls_name"), "imported_files_layout")
        control_node = cmds.spaceLocator(name=control_name)[0]
        control_node = (cmds.ls(control_node, long=True) or [control_node])[0]
    if not cmds.attributeQuery(CONTROL_NODE_ATTRIBUTE, node=control_node, exists=True):
        cmds.addAttr(control_node, longName=CONTROL_NODE_ATTRIBUTE, attributeType="bool", defaultValue=True)
        cmds.setAttr(f"{control_node}.{CONTROL_NODE_ATTRIBUTE}", lock=True)
    return control_node


def add_double_attribute(node, attribute_name, value, nice_name=None):
    """Adds a keyable double attribute.

    Args:
        node (str): Node.
        attribute_name (str): Attribute name.
        value (float): Initial value.
        nice_name (str, optional): Label shown in the Channel Box.

    Returns:
        str: Attribute path.
    """
    import maya.cmds as cmds

    attribute_kwargs = {"longName": attribute_name, "attributeType": "double", "keyable": True}
    if nice_name:
        attribute_kwargs["niceName"] = nice_name
    cmds.addAttr(node, **attribute_kwargs)
    cmds.setAttr(f"{node}.{attribute_name}", float(value))
    return f"{node}.{attribute_name}"


def add_layout_attributes(control_node, settings, vector_a, vector_b):
    """Adds the shared layout attributes (line step or grid spacing).

    Args:
        control_node (str): Control node.
        settings (dict): Tool settings.
        vector_a (list): Layout vector A.
        vector_b (list): Layout vector B.

    Returns:
        tuple: (vector_a_sources, vector_b_sources). Each is a list of 3 attribute paths or None (constant 0).
    """
    import gt.core.attr as core_attr

    offset_mode = settings.get("offset_mode")
    if offset_mode == constants.OFFSET_NONE:
        return [None, None, None], [None, None, None]
    core_attr.add_separator_attr(control_node, "layoutSeparator", custom_value="Layout")
    if offset_mode == constants.OFFSET_LINE:
        step_sources = [
            add_double_attribute(control_node, f"layoutStep{axis}", vector_a[axis_index], f"Step {axis}")
            for axis_index, axis in enumerate("XYZ")
        ]
        return step_sources, [None, None, None]
    spacing_a = add_double_attribute(control_node, "layoutColumnSpacing", vector_a[0], "Column Spacing")
    row_axis = 1 if abs(vector_b[1]) > 0 or settings.get("grid_plane") == constants.GRID_PLANE_XY else 2
    spacing_b = add_double_attribute(control_node, "layoutRowSpacing", vector_b[row_axis], "Row Spacing")
    vector_b_sources = [None, None, None]
    vector_b_sources[row_axis] = spacing_b
    return [spacing_a, None, None], vector_b_sources


def connect_vector(sources, destination_node, destination_attribute, axis_names="XYZ"):
    """Connects up to three source attributes to a compound XYZ attribute (missing sources are set to 0).

    Args:
        sources (list): Three attribute paths or None.
        destination_node (str): Node receiving the values.
        destination_attribute (str): Compound attribute base name, e.g. "input2".
        axis_names (str, optional): Child suffixes ("XYZ" for multiplyDivide, "xyz" for plusMinusAverage).
    """
    import maya.cmds as cmds

    for axis, source in zip(axis_names, sources):
        destination = f"{destination_node}.{destination_attribute}{axis}"
        if source:
            cmds.connectAttr(source, destination, force=True)
        else:
            cmds.setAttr(destination, 0.0)


def build_file_network(control_node, record, coefficients, vector_a_sources, vector_b_sources):
    """Adds the per-file attributes and the nodes that drive one file's position and visibility.

    Args:
        control_node (str): Control node.
        record (dict): Import record.
        coefficients (tuple): (coefficient_a, coefficient_b) of this file.
        vector_a_sources (list): Attribute paths (or None) of layout vector A.
        vector_b_sources (list): Attribute paths (or None) of layout vector B.

    Returns:
        list: Messages for nodes that could not be connected.
    """
    import maya.cmds as cmds
    import gt.core.attr as core_attr
    import gt.core.str as core_str

    messages = []
    driven_nodes = get_driven_nodes(record)
    if not driven_nodes:
        return messages
    file_index = record["index"]
    base_name = core_str.sanitize_maya_name(record["name"], "file")
    separator_name = layout.build_control_attribute_name(file_index)
    core_attr.add_separator_attr(control_node, separator_name, custom_value=record["name"].replace(":", "_"))
    offset_sources = [
        add_double_attribute(control_node, layout.build_control_attribute_name(file_index, f"Offset{axis}"), 0.0,
                             f"Offset {axis}")
        for axis in "XYZ"
    ]
    visibility_attribute = layout.build_control_attribute_name(file_index, "Visibility")
    cmds.addAttr(control_node, longName=visibility_attribute, niceName="Visibility", attributeType="bool",
                 defaultValue=True, keyable=True)
    sum_node = cmds.createNode("plusMinusAverage", name=f"{base_name}_layout_sum", skipSelect=True)
    for input_index, (coefficient, sources) in enumerate(
        [(coefficients[0], vector_a_sources), (coefficients[1], vector_b_sources)]
    ):
        if not any(sources) or not coefficient:
            continue
        multiply_node = cmds.createNode("multiplyDivide", name=f"{base_name}_layout_multiply", skipSelect=True)
        cmds.setAttr(f"{multiply_node}.input1", coefficient, coefficient, coefficient)
        connect_vector(sources, multiply_node, "input2")
        cmds.connectAttr(f"{multiply_node}.output", f"{sum_node}.input3D[{input_index}]", force=True)
    connect_vector(offset_sources, sum_node, "input3D[2].input3D", axis_names="xyz")
    for driven_node in driven_nodes:
        try:
            if record.get("group"):
                cmds.connectAttr(f"{sum_node}.output3D", f"{driven_node}.translate", force=True)
            else:
                compose_node = cmds.createNode("composeMatrix", name=f"{base_name}_layout_matrix", skipSelect=True)
                cmds.connectAttr(f"{sum_node}.output3D", f"{compose_node}.inputTranslate", force=True)
                cmds.connectAttr(f"{compose_node}.outputMatrix", f"{driven_node}.offsetParentMatrix", force=True)
            cmds.connectAttr(f"{control_node}.{visibility_attribute}", f"{driven_node}.visibility", force=True)
        except Exception as exception:
            messages.append(f'Unable to drive "{driven_node}" from the layout controls: {exception}')
    return messages


def build_layout_controls(records, settings, vector_a, vector_b, coefficients, top_group=""):
    """Builds the layout control node and connects every imported file to it.

    Args:
        records (list): Imported records, in placement order.
        settings (dict): Tool settings.
        vector_a (list): Layout vector A (initial values of the step or column spacing).
        vector_b (list): Layout vector B (initial value of the row spacing).
        coefficients (list): (coefficient_a, coefficient_b) per record.
        top_group (str, optional): Top group; used as the control node when present.

    Returns:
        tuple: (control_node, messages).
    """
    control_node = create_control_node(settings, top_group)
    vector_a_sources, vector_b_sources = add_layout_attributes(control_node, settings, vector_a, vector_b)
    messages = []
    for record, record_coefficients in zip(records, coefficients):
        messages.extend(build_file_network(control_node, record, record_coefficients, vector_a_sources,
                                           vector_b_sources))
    return control_node, messages
