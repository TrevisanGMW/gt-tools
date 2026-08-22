"""
Auto Rigger Control Rig Pose Maya Service

Captures and applies evaluated skeleton transforms for custom control rig poses.
"""

import gt.tools.auto_rigger.control_rig_pose as tools_control_pose
import gt.tools.auto_rigger.rig_utils as tools_rig_utils
import gt.tools.auto_rigger.rig_constants as tools_rig_const
import gt.core.logger as core_log
import maya.cmds as cmds
import logging


# Logging Setup
logger_name = core_log.get_logger_name(__name__)
logger = core_log.setup_common_logger(name=logger_name, propagate=False)
logger.setLevel(logging.INFO)


def _get_project_proxy_joint_map(rig_project):
    """Gets existing scene joints mapped by their project proxy UUIDs.

    Args:
        rig_project (RigProject): Project used to resolve active proxies.

    Returns:
        dict: Mapping of proxy UUIDs to long joint paths.
    """
    proxy_joint_map = {}
    for module in rig_project.get_modules():
        if not module.is_active():
            continue
        for proxy in module.get_proxies():
            joint = tools_rig_utils.find_joint_from_uuid(proxy.get_uuid())
            if not joint:
                continue
            joint_paths = cmds.ls(str(joint), long=True) or []
            if joint_paths:
                proxy_joint_map[proxy.get_uuid()] = joint_paths[0]
    return proxy_joint_map


def _get_project_proxy_target_name_map(rig_project):
    """Gets display target names mapped by project proxy UUIDs.

    Existing scene joints are preferred. When the rig is not built, expected
    joint names are assembled from the serialized module and proxy naming data.

    Args:
        rig_project (RigProject): Project used to resolve pose targets.

    Returns:
        dict: Mapping of proxy UUIDs to target joint names.
    """
    target_name_map = {
        proxy_uuid: joint.rsplit("|", 1)[-1]
        for proxy_uuid, joint in _get_project_proxy_joint_map(rig_project).items()
    }
    for module in rig_project.get_modules():
        if not module.is_active():
            continue
        use_proxy_naming = module.get_module_class_name() == "ModuleGeneric"
        for proxy in module.get_proxies():
            proxy_uuid = proxy.get_uuid()
            if proxy_uuid in target_name_map:
                continue
            prefix = module.get_prefix()
            suffix = module.get_suffix()
            if use_proxy_naming:
                prefix = proxy.get_attr_dict_value(key="prefix") or prefix
                suffix = proxy.get_attr_dict_value(key="suffix") or suffix
            name_parts = [prefix, proxy.get_name(), suffix]
            base_name = "_".join(str(part) for part in name_parts if part)
            target_name_map[proxy_uuid] = f"{base_name}_JNT"
    return target_name_map


def get_project_control_rig_pose_report(rig_project):
    """Builds readable stored-pose data with resolved target object names.

    Args:
        rig_project (RigProject): Project carrying the stored control rig pose.

    Returns:
        dict: JSON-compatible report data ordered by target object name.
    """
    pose_data = rig_project.get_control_rig_pose_data()
    target_name_map = _get_project_proxy_target_name_map(rig_project)
    targets = []
    for proxy_uuid, transform_data in pose_data.transforms.items():
        targets.append(
            {
                "target_object": transform_data.get("target") or target_name_map.get(proxy_uuid) or "<unresolved>",
                "proxy_uuid": proxy_uuid,
                "matrix": list(transform_data.get("matrix") or []),
            }
        )
    targets.sort(key=lambda item: (item.get("target_object", "").lower(), item.get("proxy_uuid", "")))
    return {
        "schema_version": pose_data.schema_version,
        "project_uuid": pose_data.project_uuid,
        "proxy_signature": pose_data.proxy_signature,
        "transform_count": pose_data.get_transform_count(),
        "targets": targets,
    }


def capture_project_control_rig_pose(rig_project):
    """Captures the current evaluated skeleton pose for a rig project.

    The user can pose the existing control rig with FK, IK, or other controls. This function stores the resulting
    proxy-backed skeleton matrices, so the pose can be applied before controls exist during a later rebuild.

    Args:
        rig_project (RigProject): Project whose built rig should be captured.

    Returns:
        ControlRigPoseData: Captured custom control rig pose.

    Raises:
        RuntimeError: If no matching built rig or proxy-backed joints can be found.
    """
    rigs_metadata = tools_rig_utils.get_rigs_metadata() or {}
    if rig_project.get_uuid() not in rigs_metadata:
        raise RuntimeError("A built rig matching the current rig project must exist before capturing a custom pose.")

    rig_metadata = rigs_metadata.get(rig_project.get_uuid()) or {}
    project_data_key = tools_rig_const.RiggerConstants.ATTR_RIG_PROJECT_DATA
    scene_project_data = rig_metadata.get(project_data_key) or {}
    scene_proxy_signature = tools_control_pose.build_proxy_signature(scene_project_data)
    if scene_proxy_signature != rig_project.get_control_rig_pose_proxy_signature():
        raise RuntimeError(
            "The current project proxy configuration differs from the project used to build the scene rig. "
            "Rebuild the rig before capturing a custom pose."
        )

    proxy_joint_map = _get_project_proxy_joint_map(rig_project)
    if not proxy_joint_map:
        raise RuntimeError("No proxy-backed skeleton joints were found for the current rig project.")

    transforms = {}
    for proxy_uuid, joint in proxy_joint_map.items():
        matrix = cmds.xform(joint, query=True, matrix=True, worldSpace=True)
        transforms[proxy_uuid] = {
            "target": joint.rsplit("|", 1)[-1],
            "matrix": [round(float(component), 8) for component in matrix],
        }

    pose_data = tools_control_pose.ControlRigPoseData(
        project_uuid=rig_project.get_uuid(),
        proxy_signature=rig_project.get_control_rig_pose_proxy_signature(),
        transforms=transforms,
    )
    return pose_data


def validate_project_control_rig_pose(rig_project, require_scene_joints=False):
    """Validates a project's stored custom control rig pose.

    Args:
        rig_project (RigProject): Project carrying the custom control rig pose.
        require_scene_joints (bool, optional): Whether every stored target must also exist as a scene joint.

    Returns:
        dict: Validation result containing valid, errors, warnings, and transform_count keys.
    """
    pose_data = rig_project.get_control_rig_pose_data()
    proxy_joint_map = _get_project_proxy_joint_map(rig_project) if require_scene_joints else {}
    validation = pose_data.validate(
        project_uuid=rig_project.get_uuid(),
        proxy_signature=rig_project.get_control_rig_pose_proxy_signature(),
    )

    if require_scene_joints:
        stored_proxy_uuids = set(pose_data.transforms.keys())
        missing_scene_joints = sorted(stored_proxy_uuids - set(proxy_joint_map.keys()))
        if missing_scene_joints:
            validation["errors"].append(
                f"Unable to find {len(missing_scene_joints)} proxy-backed skeleton joint(s) in the scene."
            )
            validation["valid"] = False
    return validation


def apply_project_control_rig_pose(rig_project):
    """Applies a project's stored custom pose to its scene skeleton.

    Args:
        rig_project (RigProject): Project carrying the custom control rig pose.

    Returns:
        int: Number of skeleton joints updated.

    Raises:
        RuntimeError: If the custom pose is invalid or required scene joints are missing.
    """
    validation = validate_project_control_rig_pose(rig_project=rig_project, require_scene_joints=True)
    if not validation.get("valid"):
        error_message = " ".join(validation.get("errors") or ["The custom control rig pose is invalid."])
        raise RuntimeError(error_message)

    pose_data = rig_project.get_control_rig_pose_data()
    proxy_joint_map = _get_project_proxy_joint_map(rig_project)
    ordered_targets = []
    for proxy_uuid, transform_data in pose_data.transforms.items():
        joint = proxy_joint_map.get(proxy_uuid)
        matrix = transform_data.get("matrix")
        ordered_targets.append((joint.count("|"), joint, matrix))

    for _, joint, matrix in sorted(ordered_targets):
        cmds.xform(joint, matrix=matrix, worldSpace=True)
    logger.info(f"Applied custom control rig pose to {len(ordered_targets)} skeleton joint(s).")
    return len(ordered_targets)
