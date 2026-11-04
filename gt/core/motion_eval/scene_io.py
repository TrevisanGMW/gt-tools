"""
Motion Evaluation Scene IO - Stores evaluation scores and reports as Maya attributes.

Maya runtime module. By default the score lives on a dedicated network node so
referenced or locked rig nodes are never touched.
"""

import json
import logging

logger = logging.getLogger(__name__)

DEFAULT_NODE_NAME = "motionEval"
DEFAULT_SCORE_ATTRIBUTE = "motionScore"
DEFAULT_REPORT_ATTRIBUTE = "motionReport"

WRITE_POLICY_OVERWRITE = "overwrite"
WRITE_POLICY_IF_MISSING = "if_missing"
WRITE_POLICY_NEVER = "never"
WRITE_POLICIES = [WRITE_POLICY_OVERWRITE, WRITE_POLICY_IF_MISSING, WRITE_POLICY_NEVER]

TARGET_DEDICATED_NODE = "dedicated_node"
TARGET_ROLE = "role"
TARGET_NAMED_NODE = "named_node"
TARGET_MODES = [TARGET_DEDICATED_NODE, TARGET_ROLE, TARGET_NAMED_NODE]


def get_maya_cmds():
    """Imports maya.cmds lazily.

    Returns:
        module: maya.cmds.
    """
    import maya.cmds as cmds

    return cmds


def build_report_payload(report):
    """Builds the compact JSON stored on the report attribute.

    Spans are kept, but long offender lists and parameters stay in the external log.

    Args:
        report (dict): Evaluation report.

    Returns:
        str: JSON text.
    """
    keys = [
        "version", "evaluator_version", "created_at", "mode", "preset", "template", "settings_hash",
        "score", "status", "frame_range", "fps",
    ]
    payload = {key: report.get(key) for key in keys}
    payload["checks"] = [
        {
            "key": entry.get("key"),
            "score": entry.get("score"),
            "status": entry.get("status"),
            "spans": entry.get("spans", []),
        }
        for entry in report.get("checks") or []
        if entry.get("status") != "disabled"
    ]
    return json.dumps(payload, sort_keys=True)


def resolve_target_node(target_mode=TARGET_DEDICATED_NODE, node_name="", roles=None, create=True):
    """Resolves (and optionally creates) the node that stores the score.

    Args:
        target_mode (str): One of TARGET_MODES.
        node_name (str): Network node name, role key, or node name depending on the mode.
        roles (dict, optional): Resolved role to node path mapping (role mode).
        create (bool): Create the dedicated network node when missing.

    Returns:
        str or None: Node name, or None when it does not exist and was not created.

    Raises:
        ValueError: If the target cannot be used.
    """
    cmds = get_maya_cmds()
    if target_mode == TARGET_ROLE:
        role_path = (roles or {}).get(node_name)
        if not role_path or not cmds.objExists(role_path):
            raise ValueError(f'Score target role "{node_name}" was not resolved in this scene.')
        return role_path
    if target_mode == TARGET_NAMED_NODE:
        matches = cmds.ls(node_name, long=True) or []
        if not matches:
            raise ValueError(f'Score target node "{node_name}" does not exist.')
        if len(matches) > 1:
            raise ValueError(f'Score target name "{node_name}" matches {len(matches)} nodes. Use a unique name.')
        return matches[0]
    node_name = node_name or DEFAULT_NODE_NAME
    if cmds.objExists(node_name):
        if cmds.nodeType(node_name) != "network":
            raise ValueError(f'Score node "{node_name}" exists but is a {cmds.nodeType(node_name)} node.')
        return node_name
    if not create:
        return None
    return cmds.createNode("network", name=node_name, skipSelect=True)


def ensure_attribute(node, attribute_name, is_string):
    """Adds an integer (0-100) or string attribute when missing.

    Args:
        node (str): Node name.
        attribute_name (str): Attribute name.
        is_string (bool): Create a string attribute instead of an integer.

    Raises:
        ValueError: If the attribute cannot be added or is locked.
    """
    cmds = get_maya_cmds()
    if not cmds.attributeQuery(attribute_name, node=node, exists=True):
        if is_string:
            cmds.addAttr(node, longName=attribute_name, dataType="string")
        else:
            cmds.addAttr(node, longName=attribute_name, attributeType="long", minValue=0, maxValue=100)
        cmds.setAttr(f"{node}.{attribute_name}", channelBox=False)
    if cmds.getAttr(f"{node}.{attribute_name}", lock=True):
        raise ValueError(f'Attribute "{node}.{attribute_name}" is locked.')


def read_score(target_mode=TARGET_DEDICATED_NODE, node_name="", score_attribute=DEFAULT_SCORE_ATTRIBUTE, roles=None):
    """Reads a stored score.

    Args:
        target_mode (str): One of TARGET_MODES.
        node_name (str): Target name (see resolve_target_node).
        score_attribute (str): Score attribute name.
        roles (dict, optional): Resolved roles for the role mode.

    Returns:
        int or None: Stored score, or None when missing.
    """
    cmds = get_maya_cmds()
    try:
        node = resolve_target_node(target_mode, node_name, roles, create=False)
    except ValueError:
        return None
    if not node or not cmds.attributeQuery(score_attribute, node=node, exists=True):
        return None
    return int(cmds.getAttr(f"{node}.{score_attribute}"))


def write_score(
    report,
    target_mode=TARGET_DEDICATED_NODE,
    node_name=DEFAULT_NODE_NAME,
    score_attribute=DEFAULT_SCORE_ATTRIBUTE,
    report_attribute=DEFAULT_REPORT_ATTRIBUTE,
    write_policy=WRITE_POLICY_OVERWRITE,
    write_report=True,
):
    """Writes the evaluation score (and optional report) to a Maya attribute.

    Args:
        report (dict): Evaluation report.
        target_mode (str): One of TARGET_MODES.
        node_name (str): Network node name, role key, or node name depending on the mode.
        score_attribute (str): Integer attribute that receives the 0-100 score.
        report_attribute (str): String attribute that receives the compact JSON report.
        write_policy (str): One of WRITE_POLICIES.
        write_report (bool): Also store the compact report JSON.

    Returns:
        dict: {"written": bool, "node": str, "attribute": str, "previous": int or None, "message": str}

    Raises:
        ValueError: If the target or attributes cannot be used.
    """
    cmds = get_maya_cmds()
    score_attribute = str(score_attribute or DEFAULT_SCORE_ATTRIBUTE).strip()
    report_attribute = str(report_attribute or DEFAULT_REPORT_ATTRIBUTE).strip()
    outcome = {"written": False, "node": "", "attribute": "", "previous": None, "message": ""}
    if write_policy == WRITE_POLICY_NEVER:
        outcome["message"] = "Score writing is disabled."
        return outcome
    roles = report.get("roles") or {}
    previous = read_score(target_mode, node_name, score_attribute, roles)
    outcome["previous"] = previous
    if write_policy == WRITE_POLICY_IF_MISSING and previous is not None:
        outcome["message"] = f"Kept existing score {previous} (write policy: only if missing)."
        return outcome
    node = resolve_target_node(target_mode, node_name, roles, create=True)
    ensure_attribute(node, score_attribute, is_string=False)
    cmds.setAttr(f"{node}.{score_attribute}", int(report.get("score", 0)))
    if write_report and report_attribute:
        ensure_attribute(node, report_attribute, is_string=True)
        cmds.setAttr(f"{node}.{report_attribute}", build_report_payload(report), type="string")
    outcome.update(
        {
            "written": True,
            "node": node,
            "attribute": f"{node}.{score_attribute}",
            "message": f"Wrote score {report.get('score')} to {node.split('|')[-1]}.{score_attribute}.",
        }
    )
    return outcome
