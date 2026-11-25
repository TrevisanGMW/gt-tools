"""
Motion Evaluation Scene IO - Stores evaluation scores and reports in the open scene.

Host-agnostic: the write policy and messages live here, the storage itself in the
active host (hosts.get_host). In Maya the score is an attribute; by default it lives on
a dedicated network node so referenced or locked rig nodes are never touched. In Blender
it is a custom property, by default on a dedicated empty object.
"""

from . import hosts

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


def get_score_host():
    """Gets the active host and checks that it can store scores.

    Returns:
        SceneHost: Host.

    Raises:
        ValueError: If the host cannot store scores (for example motion sample files).
    """
    host = hosts.get_host()
    if not host.supports_score_write:
        raise ValueError(f"{host.label} cannot store scores in the scene.")
    return host


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
    """Resolves (and optionally creates) the node that stores the score (Maya node, Blender object or bone).

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
    if target_mode not in (TARGET_ROLE, TARGET_NAMED_NODE):
        node_name = node_name or DEFAULT_NODE_NAME
    return get_score_host().find_score_holder(target_mode, node_name, roles, create=create)


def ensure_attribute(node, attribute_name, is_string):
    """Adds an integer (0-100) or string attribute when missing (Maya only).

    Args:
        node (str): Node name.
        attribute_name (str): Attribute name.
        is_string (bool): Create a string attribute instead of an integer.

    Raises:
        ValueError: If the attribute cannot be added or is locked.
    """
    hosts.get_host(hosts.HOST_MAYA).ensure_attribute(node, attribute_name, is_string)


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
    try:
        host = get_score_host()
        node = resolve_target_node(target_mode, node_name, roles, create=False)
    except ValueError:
        return None
    if not node:
        return None
    return host.read_score_value(node, score_attribute)


def write_score(
    report,
    target_mode=TARGET_DEDICATED_NODE,
    node_name=DEFAULT_NODE_NAME,
    score_attribute=DEFAULT_SCORE_ATTRIBUTE,
    report_attribute=DEFAULT_REPORT_ATTRIBUTE,
    write_policy=WRITE_POLICY_OVERWRITE,
    write_report=True,
):
    """Writes the evaluation score (and optional report) to a scene attribute or custom property.

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
    host = get_score_host()
    node = resolve_target_node(target_mode, node_name, roles, create=True)
    with_report = bool(write_report and report_attribute)
    host.write_score_values(node, score_attribute, int(report.get("score", 0)),
                            report_attribute=report_attribute if with_report else "",
                            report_text=build_report_payload(report) if with_report else "")
    outcome.update(
        {
            "written": True,
            "node": node,
            "attribute": f"{node}.{score_attribute}",
            "message": f"Wrote score {report.get('score')} to {node.split('|')[-1]}.{score_attribute}.",
        }
    )
    return outcome
