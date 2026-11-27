"""Runs the Motion Evaluator on the character selected by Auto Annotate."""

from gt.core.motion_eval import checks_base, evaluation, presets, sampling, templates


EVALUATOR_ROLE_NAMES = {
    "pelvis": "hips",
    "left_upper_leg": "left_up_leg",
    "right_upper_leg": "right_up_leg",
    "left_knee": "left_leg",
    "right_knee": "right_leg",
}


def evaluate_quality(cmds, mapping, frame_range, preset):
    """Scores motion with the same checks, thresholds and weights as Motion Evaluator.

    Args:
        cmds (module): Maya commands module.
        mapping (dict): Resolved annotation anatomy paths.
        frame_range (tuple): First and last playback frames.
        preset (dict): Motion Evaluator preset with optional overrides.

    Returns:
        dict: Motion Evaluator report with a weighted score from 0 to 100.
    """
    resolved = presets.resolve_preset(preset)
    warnings = presets.validate_preset(resolved)
    if warnings:
        raise ValueError(warnings[0])

    roles = {EVALUATOR_ROLE_NAMES.get(role, role): path for role, path in mapping.items()}
    if resolved["mode"] == checks_base.MODE_BIPED:
        if "spine" not in roles and "chest" in roles:
            roles["spine"] = roles.pop("chest")
        missing = [templates.ROLE_LABELS[role] for role in templates.REQUIRED_BIPED_ROLES if role not in roles]
        if missing:
            labels = ", ".join(missing)
            raise ValueError(f"Biped quality needs these mapped joints: {labels}. Use General or map them.")
        nodes = list(roles.values())
    else:
        pelvis = mapping["pelvis"]
        nodes = [pelvis, *(cmds.listRelatives(pelvis, allDescendents=True, fullPath=True, type="joint") or [])]

    # Scope the sample to exact DAG paths so identically named characters cannot mix.
    sample = sampling.sample_scene(
        frame_range=frame_range,
        general_scope=sampling.SCOPE_NODE_LIST,
        node_names=nodes,
        extra_data=evaluation.get_required_data(resolved),
    )
    sample["roles"] = {role: path for role, path in roles.items() if path in sample["nodes"]}
    report = evaluation.evaluate_sample(sample, preset=resolved)
    if not any(check.get("score") is not None and check.get("weight", 0) > 0 for check in report["checks"]):
        raise ValueError("No enabled Motion Evaluator check produced a weighted score.")
    return report
