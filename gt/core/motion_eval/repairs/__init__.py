"""
Motion Evaluation Repairs - Targeted fixes for the problems the checks report.

A patch is a list of steps for one take, kept in a JSON manifest (see manifest.py). Each step
names a registry fix (foot_lock, ground_snap, span_bridge, span_smooth) or a custom script, and
the frame span to repair (usually a span from the evaluation report). Fixes only key the frames
they change.

Pure modules (no scene access): transform_math, solvers, registry, manifest.
Scene modules (through the active host): scene, fixes, apply.

    from motion_eval.repairs import apply, registry
    print(registry.describe_fixes())
    result = apply.apply_manifest("patches.json", ["walk_042_v003"], seed=4711)

Writing keys needs a host with supports_keying (Maya).
"""
