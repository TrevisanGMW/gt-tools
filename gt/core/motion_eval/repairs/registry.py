"""
Repair registry: the fixes a patch step can name, their parameters and presets, and the order
in which to try them for each check (the fallback ladder). Pure data plus small lookups.

A step picks a preset with ``"preset": "<name>"``; its own ``params`` override the preset.
"""

from . import fixes

DEFAULT_PRESET = "default"


class FixDefinition:
    """Describes one fix."""

    def __init__(self, key, label, summary, function, parameters, checks, needs_nodes, side_effects, presets=None):
        """Initializes the definition.

        Args:
            key (str): Stable fix key used in patch files.
            label (str): Readable name.
            summary (str): What the fix does.
            function (callable): ``function(scene, frames, nodes, params)``.
            parameters (dict): Parameter name to (default, description).
            checks (list): Check keys the fix is meant for.
            needs_nodes (str): How the fix picks its nodes.
            side_effects (str): What to watch for after using it.
            presets (dict, optional): Preset name to (params, description). "default" is implied.
        """
        self.key = key
        self.label = label
        self.summary = summary
        self.function = function
        self.parameters = parameters
        self.checks = list(checks)
        self.needs_nodes = needs_nodes
        self.side_effects = side_effects
        self.presets = {DEFAULT_PRESET: ({}, "The parameter defaults.")}
        self.presets.update(presets or {})

    def get_defaults(self):
        """Gets the default parameter values.

        Returns:
            dict: Parameter name to default value.
        """
        return dict((name, value[0]) for name, value in self.parameters.items())

    def get_preset(self, preset_name):
        """Gets a preset's parameters.

        Args:
            preset_name (str): Preset name (empty = default).

        Returns:
            dict: Preset parameters.

        Raises:
            KeyError: When the preset is unknown.
        """
        name = str(preset_name or DEFAULT_PRESET).strip().lower()
        if name not in self.presets:
            raise KeyError(f'Unknown {self.key} preset "{preset_name}". Presets: {", ".join(self.presets)}.')
        return dict(self.presets[name][0])

    def merge_params(self, params, preset_name=""):
        """Merges defaults, then the preset, then the step's own parameters.

        Args:
            params (dict): Step parameters.
            preset_name (str): Preset name.

        Returns:
            dict: Merged parameters.
        """
        merged = self.get_defaults()
        merged.update(self.get_preset(preset_name))
        merged.update(params or {})
        return merged


FIXES = [
    FixDefinition(
        key="foot_lock",
        label="Foot Lock",
        summary="Pins planted feet over a contact span with two-bone IK (thigh and knee rotate, bone lengths "
                "stay, the foot keeps its world rotation), blending in and out.",
        function=fixes.foot_lock,
        parameters={
            "side": ("auto", '"left", "right", or "auto" (every foot planted during the span; report spans do '
                             'not say which foot slid). Or give "nodes": [thigh, knee, foot].'),
            "blend": (4, "Frames to blend in before and out after the span."),
            "pin_at": ("average", '"average", "start", "end", or "still" (frame where the foot moves least).'),
            "pin_height": (False, "Also pin the height (planted-foot jitter); off keeps heel/toe roll."),
            "min_height": (None, "Lowest allowed foot height in scene units (fixes a sinking foot)."),
            "extend_contact": (False, "Grow the span to the whole contact so the blend does not lift the foot "
                                      "inside it (less contact flicker)."),
            "extend_max": (30, "Most frames extend_contact adds on each side."),
        },
        presets={
            "contact": ({"extend_contact": True}, "Lock the whole contact, not just the reported frames."),
            "still": ({"pin_at": "still", "extend_contact": True}, "Pin where the foot is most still."),
            "planted": ({"pin_height": True, "extend_contact": True}, "Pin height too (jitter, flicker)."),
            "start": ({"pin_at": "start"}, "Pin at the first frame (slide that starts late)."),
        },
        checks=["foot_slide", "planted_foot_jitter", "contact_flicker", "ground_penetration"],
        needs_nodes="none (side auto), side, or nodes [thigh, knee, foot]",
        side_effects="A pin far from the original path bends the knee a lot; short blends can add flicker.",
    ),
    FixDefinition(
        key="hips_follow",
        label="Hips Follow",
        summary="Moves the body along the ground so the planted foot stays put, without bending the legs "
                "(for drift of the whole body during a contact).",
        function=fixes.hips_follow,
        parameters={
            "side": ("auto", '"left", "right", or "auto" (planted feet).'),
            "pin_at": ("average", 'Where the foot is held: "average", "start", "end", or "still".'),
            "blend": (8, "Frames over which the offset fades in and out."),
        },
        presets={"still": ({"pin_at": "still"}, "Hold the foot where it is most still.")},
        checks=["foot_slide"],
        needs_nodes="optional [body node]; defaults to the hips role",
        side_effects="Shifts the path a little around the span; the other foot moves with the body.",
    ),
    FixDefinition(
        key="foot_floor_clamp",
        label="Foot Floor Clamp",
        summary="Lifts only a sinking foot with two-bone IK so it never goes below the floor; the body stays.",
        function=fixes.foot_floor_clamp,
        parameters={
            "side": ("auto", '"left", "right", or "auto" (every foot that goes below the floor in the span).'),
            "floor": (None, "Floor height in scene units. Default: the feet's low height percentile."),
            "margin": (0.0, "Extra height above the floor in scene units."),
            "blend": (3, "Frames to blend in before and out after the span."),
        },
        checks=["ground_penetration", "below_ground"],
        needs_nodes="none (side auto), side, or nodes [thigh, knee, foot]",
        side_effects="Bends the knee more; toes may still dip if the ankle is the only joint lifted.",
    ),
    FixDefinition(
        key="ground_snap",
        label="Ground Snap",
        summary="Moves the body (hips by default) up or down so the lowest foot/toe sits on the floor "
                "during the span, blending in and out.",
        function=fixes.ground_snap,
        parameters={
            "mode": ("both", '"raise" fixes sinking, "lower" fixes floating, "both" does both.'),
            "floor": (None, "Floor height in scene units. Default: 10th percentile of the lowest contact "
                            "over the clip (same idea as the checks)."),
            "contacts": (None, "Contact nodes. Default: foot and toe roles of the skeleton template."),
            "blend": (4, "Frames to blend in before and out after the span."),
            "smooth": (2, "Smoothing half width of the offset curve in frames."),
        },
        presets={"raise": ({"mode": "raise"}, "Only lift (sinking)."),
                 "lower": ({"mode": "lower"}, "Only lower (floating).")},
        checks=["below_ground", "floating", "ground_penetration", "contact_flicker"],
        needs_nodes="optional [body node]; defaults to the hips role",
        side_effects="Moves both feet; a planted foot may start sliding. Re-check foot_slide.",
    ),
    FixDefinition(
        key="spike_clamp",
        label="Spike Clamp",
        summary="Caps how fast the nodes move inside the span (factor x the typical step around it), "
                "flattening a pop while keeping the motion through the span.",
        function=fixes.spike_clamp,
        parameters={
            "channels": ("rotate", '"rotate", "translate", or "both".'),
            "factor": (1.5, "Largest step as a multiple of the median step around the span."),
        },
        presets={"tight": ({"factor": 1.0}, "Cap at the typical step."),
                 "both": ({"channels": "both"}, "Rotation and translation (hips, root).")},
        checks=["position_pops", "rotation_pops"],
        needs_nodes="nodes (report offenders or role keys)",
        side_effects="A real fast move inside the span gets slowed down.",
    ),
    FixDefinition(
        key="span_bridge",
        label="Span Bridge",
        summary="Replaces the span with a smooth transition between the poses just before and after it "
                "(local rotations slerped, translations on a Hermite curve). strength < 1 pulls part way.",
        function=fixes.span_bridge,
        parameters={
            "channels": ("rotate", '"rotate", "translate", or "both".'),
            "strength": (1.0, "0-1. How far to move toward the bridge."),
            "ease": (0, "Frames to fade the bridge in and out inside the span (0 = full from the start)."),
        },
        presets={
            "eased": ({"ease": 2}, "Fade in and out inside the span."),
            "partial": ({"strength": 0.5, "ease": 1}, "Pull half way (joint limits, wrists, head)."),
            "both": ({"channels": "both"}, "Rotation and translation (pops, invalid values on hips/root)."),
        },
        checks=["position_pops", "rotation_pops", "invalid_values", "knee_hyperextension", "knee_side_bend",
                "elbow_hyperextension", "elbow_side_bend", "wrist_bend", "forearm_twist", "head_turn"],
        needs_nodes="nodes (report offenders or role keys)",
        side_effects="Removes any real motion inside the span; keep spans short (pops, a few frames).",
    ),
    FixDefinition(
        key="span_smooth",
        label="Span Smooth",
        summary="Gaussian-smooths the local motion of the nodes over the span, blending in and out.",
        function=fixes.span_smooth,
        parameters={
            "radius": (2, "Kernel half width in frames (bigger = smoother)."),
            "blend": (3, "Frames to blend in before and out after the span."),
            "channels": ("rotate", '"rotate", "translate", or "both" (use "both" on hips/root).'),
            "strength": (1.0, "0-1. How much of the smoothing to apply."),
            "adaptive": (False, "Smooth slow frames more than fast ones (keeps accents)."),
        },
        presets={
            "light": ({"radius": 1}, "Barely visible; small jitter."),
            "strong": ({"radius": 4, "blend": 4}, "Heavy jitter; can look floaty."),
            "adaptive": ({"radius": 3, "adaptive": True}, "Jitter during slow motion, accents kept."),
        },
        checks=["jitter", "planted_foot_jitter", "rotation_pops"],
        needs_nodes="nodes (report offenders or role keys)",
        side_effects="Softens fast accents; a large radius makes motion floaty.",
    ),
    FixDefinition(
        key="limit_clamp",
        label="Limit Clamp",
        summary="Rotates a knee or elbow back inside its limit where it bends too far backward or sideways "
                "(hinge axis learned from the clip, like the checks).",
        function=fixes.limit_clamp,
        parameters={
            "side": ("", '"left" or "right" (or use a report label such as "left knee" in "nodes").'),
            "joint": ("", '"knee" or "elbow".'),
            "measure": ("backward", '"backward" (hyperextension) or "side" (side bend).'),
            "limit": (None, "Largest allowed angle in degrees; use the check's threshold. Default 0 "
                            "(backward) or 30 (side)."),
            "margin": (2.0, "Degrees to stay under the limit."),
            "blend": (3, "Frames to blend in before and out after the span."),
        },
        presets={
            "knee": ({"joint": "knee", "measure": "backward", "limit": 3.0}, "Knee hyperextension."),
            "elbow": ({"joint": "elbow", "measure": "backward", "limit": 30.0}, "Elbow hyperextension."),
            "knee_side": ({"joint": "knee", "measure": "side", "limit": 40.0}, "Knee side bend."),
            "elbow_side": ({"joint": "elbow", "measure": "side", "limit": 55.0}, "Elbow side bend."),
        },
        checks=["knee_hyperextension", "elbow_hyperextension", "knee_side_bend", "elbow_side_bend"],
        needs_nodes='a label like "left knee", side + joint, or nodes [upper, hinge, lower]',
        side_effects="Children follow the hinge: a planted foot or a hand on a prop moves (add foot_lock).",
    ),
]

LADDERS = {
    "foot_slide": [
        ("foot_lock", "default", "First try: pin the planted foot over the reported span."),
        ("foot_lock", "contact", "Slide left at the span edges: lock the whole contact (often best on idles)."),
        ("hips_follow", "default", "Locks add flicker, or the whole body drifts: move the body instead."),
        ("foot_lock", "still", "The foot still drifts: pin where it is most still."),
    ],
    "planted_foot_jitter": [
        ("foot_lock", "planted", "Hold the foot (height too) over the whole contact."),
        ("span_smooth", "light", "Jitter remains: smooth the foot and ankle lightly."),
    ],
    "contact_flicker": [
        ("ground_snap", "default", "Feet hover and dip around the floor: settle the body on the floor."),
        ("foot_lock", "planted", "One foot toggles: hold it down over the whole contact."),
    ],
    "ground_penetration": [
        ("foot_floor_clamp", "default", "One foot sinks: lift only that foot."),
        ("foot_lock", "contact", "The sinking foot also slides: pin it (add min_height)."),
        ("ground_snap", "raise", "Both feet sink: lift the body."),
    ],
    "below_ground": [
        ("ground_snap", "raise", "The body sinks: lift it."),
        ("foot_floor_clamp", "default", "Only a foot goes under: lift just that foot."),
    ],
    "floating": [
        ("ground_snap", "lower", "The body floats: lower it."),
    ],
    "position_pops": [
        ("spike_clamp", "both", "Cap the jump, keep the motion."),
        ("span_bridge", "both", "Still popping: replace the few frames."),
        ("span_bridge", "eased", "The bridge looks abrupt: fade it."),
    ],
    "rotation_pops": [
        ("spike_clamp", "default", "Cap the jump, keep the motion."),
        ("span_bridge", "default", "Still popping: replace the few frames."),
        ("span_smooth", "strong", "Several pops close together."),
    ],
    "invalid_values": [
        ("span_bridge", "both", "Replace the broken frames."),
    ],
    "jitter": [
        ("span_smooth", "light", "Small jitter."),
        ("span_smooth", "adaptive", "Jitter in slow parts, accents must stay."),
        ("span_smooth", "strong", "Heavy jitter."),
    ],
    "knee_hyperextension": [
        ("limit_clamp", "knee", "Bend the knee back to just under straight (add foot_lock if planted)."),
        ("span_bridge", "partial", "No hinge learned or the clamp looks stiff."),
    ],
    "elbow_hyperextension": [
        ("limit_clamp", "elbow", "Bend the elbow back under the limit (set limit to the check threshold)."),
        ("span_bridge", "partial", "No hinge learned or the clamp looks stiff."),
    ],
    "knee_side_bend": [
        ("limit_clamp", "knee_side", "Bring the knee back into its hinge plane."),
        ("span_bridge", "partial", "No hinge learned."),
    ],
    "elbow_side_bend": [
        ("limit_clamp", "elbow_side", "Bring the elbow back into its hinge plane."),
        ("span_bridge", "partial", "No hinge learned."),
    ],
    "wrist_bend": [("span_bridge", "partial", "Pull the wrist toward the pose around the span.")],
    "forearm_twist": [("span_bridge", "partial", "Pull the twist toward the pose around the span.")],
    "head_turn": [("span_bridge", "partial", "Pull the head toward the pose around the span.")],
}

NOT_PATCHABLE = {
    "airborne_gravity": "Jump arcs need a new generation.",
    "excessive_speed": "Speed comes from the path; change speed or reseed.",
    "frozen_motion": "Missing motion cannot be patched in.",
    "bone_length_changes": "A rig/export problem, not a motion problem.",
    "scale_changes": "A rig/export problem, not a motion problem.",
    "t_pose": "Trim or regenerate instead.",
    "balance": "Whole-body balance needs a new generation.",
    "gait_asymmetry": "Whole-gait problem; regenerate.",
    "limb_intersection": "Only with a custom script (move the limb away); usually regenerate.",
}


def list_fixes():
    """Lists every fix.

    Returns:
        list: FixDefinition objects.
    """
    return list(FIXES)


def get_fix(fix_key):
    """Gets a fix by key.

    Args:
        fix_key (str): Fix key.

    Returns:
        FixDefinition: Definition.

    Raises:
        KeyError: When the key is unknown.
    """
    for definition in FIXES:
        if definition.key == str(fix_key).strip().lower():
            return definition
    raise KeyError(f'Unknown fix "{fix_key}". Known fixes: {", ".join(item.key for item in FIXES)}.')


def get_rung_key(fix_key, preset_name=""):
    """Builds the "fix/preset" key used to track what was tried.

    Args:
        fix_key (str): Fix key.
        preset_name (str): Preset name (empty = default).

    Returns:
        str: Key such as "foot_lock/contact".
    """
    return f"{str(fix_key).strip().lower()}/{str(preset_name or DEFAULT_PRESET).strip().lower()}"


def get_ladder(check_key):
    """Gets the fallback order of fixes for a check.

    Args:
        check_key (str): Check key such as "foot_slide".

    Returns:
        list: {"fix", "preset", "key", "when"} dictionaries, first to try first.
    """
    return [{"fix": fix_key, "preset": preset_name, "key": get_rung_key(fix_key, preset_name), "when": when}
            for fix_key, preset_name, when in LADDERS.get(check_key, [])]


def suggest_fixes(check_key):
    """Lists the fixes meant for a check, in ladder order.

    Args:
        check_key (str): Check key.

    Returns:
        list: Fix keys without duplicates. Empty when the check should be regenerated instead.
    """
    keys = []
    for rung in get_ladder(check_key):
        if rung["fix"] not in keys:
            keys.append(rung["fix"])
    return keys


def next_rungs(check_key, failed_keys):
    """Lists the ladder rungs of a check that were not tried without success yet.

    Args:
        check_key (str): Check key.
        failed_keys (list): Rung keys ("fix/preset") that did not help.

    Returns:
        list: Remaining rungs in order.
    """
    failed = set(str(key).lower() for key in failed_keys or [])
    return [rung for rung in get_ladder(check_key) if rung["key"] not in failed]


def describe_fixes():
    """Builds a plain-text overview of every fix, its presets, and the per-check ladders.

    Returns:
        str: Multi-line description.
    """
    lines = ["Fixes:"]
    for definition in FIXES:
        lines.append(f"  {definition.key}: {definition.summary}")
        lines.append(f"    nodes: {definition.needs_nodes}")
        for name, (default, description) in definition.parameters.items():
            lines.append(f"    {name} (default {default!r}): {description}")
        for name, (params, description) in definition.presets.items():
            if name != DEFAULT_PRESET:
                lines.append(f"    preset {name} {params}: {description}")
        lines.append(f"    watch: {definition.side_effects}")
    lines.append("Try in this order (fix/preset), moving on when a rung does not help:")
    for check_key in sorted(set(LADDERS) | set(NOT_PATCHABLE)):
        rungs = get_ladder(check_key)
        if rungs:
            lines.append(f"  {check_key}: " + " -> ".join(rung["key"] for rung in rungs) + " -> regenerate")
        else:
            lines.append(f"  {check_key}: regenerate ({NOT_PATCHABLE[check_key]})")
    return "\n".join(lines)
