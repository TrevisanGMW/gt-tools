"""
Repair fixes (public entry point). Each fix reads the scene through a RepairScene, computes the
new motion with the pure solvers, and keys only the frames it changes.

Every fix has the signature ``fix(scene, frames, nodes, params)``:
    scene (RepairScene): Scene access.
    frames (tuple): Inclusive (start, end) frame span to repair.
    nodes (list): Node names, labels, or role keys (may be empty when the fix has defaults).
    params (dict): Fix parameters, already merged with the registry defaults (and preset).
and returns ``{"keys": int, "nodes": list, "frames": [start, end], "warnings": list}``.

Implementations live in fixes_feet (feet and ground) and fixes_spans (any joint); shared helpers
in fixes_common. Custom patch scripts receive this module as ``context["fixes"]``.
"""

from .fixes_common import CHANNELS
from .fixes_common import add_key_result
from .fixes_common import build_result
from .fixes_common import get_channels
from .fixes_common import get_parent_matrices
from .fixes_common import key_local_series
from .fixes_common import require_nodes
from .fixes_common import sample_local_series
from .fixes_feet import foot_floor_clamp
from .fixes_feet import foot_lock
from .fixes_feet import ground_snap
from .fixes_feet import hips_follow
from .fixes_feet import measure_leg
from .fixes_feet import pick_planted_legs
from .fixes_feet import resolve_legs
from .fixes_feet import solve_leg_window
from .fixes_spans import limit_clamp
from .fixes_spans import span_bridge
from .fixes_spans import span_smooth
from .fixes_spans import spike_clamp

__all__ = [
    "CHANNELS", "add_key_result", "build_result", "get_channels", "get_parent_matrices", "key_local_series",
    "require_nodes", "sample_local_series", "foot_floor_clamp", "foot_lock", "ground_snap", "hips_follow",
    "measure_leg", "pick_planted_legs", "resolve_legs", "solve_leg_window", "limit_clamp", "span_bridge",
    "span_smooth", "spike_clamp",
]
