"""Unit tests for repair presets, fallback ladders, the newer fixes, and preview helpers."""

import math
import tempfile
import unittest

from gt.core.motion_eval import math_utils
from gt.core.motion_eval.repairs import manifest
from gt.core.motion_eval.repairs import preview
from gt.core.motion_eval.repairs import registry
from gt.core.motion_eval.repairs import solvers
from gt.core.motion_eval.repairs.scene import RepairScene
from gt.tests.test_core.test_motion_eval_repairs import FRAME_COUNT
from gt.tests.test_core.test_motion_eval_repairs import HIPS
from gt.tests.test_core.test_motion_eval_repairs import LEFT_FOOT
from gt.tests.test_core.test_motion_eval_repairs import LEFT_THIGH
from gt.tests.test_core.test_motion_eval_repairs import build_leg_host
from gt.tests.test_core.test_motion_eval_repairs import build_template
from gt.tests.test_core.test_motion_eval_repairs import translation_matrix


def get_position(host, node, frame):
    """Gets a node's world position on a frame.

    Args:
        host (FakeKeyHost): Host.
        node (str): Node path.
        frame (int): Frame.

    Returns:
        tuple: Position.
    """
    return math_utils.matrix_position(host.get_world(node, frame))


class TestRepairVariantSolvers(unittest.TestCase):
    def test_pin_anchors(self):
        positions = [(0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1.05, 0.0, 0.0), (1.1, 0.0, 0.0), (3.0, 0.0, 0.0)]
        self.assertEqual((0.0, 0.0, 0.0), solvers.get_pin_position(positions, 0, 4, "start"))
        self.assertEqual((3.0, 0.0, 0.0), solvers.get_pin_position(positions, 0, 4, "end"))
        self.assertEqual((1.05, 0.0, 0.0), solvers.get_pin_position(positions, 0, 4, "still"))
        self.assertAlmostEqual(1.23, solvers.get_pin_position(positions, 0, 4, "average")[0])
        with self.assertRaises(ValueError):
            solvers.get_pin_position(positions, 0, 4, "middle")

    def test_extend_contact_stops_at_drift(self):
        heights = [0.0] * 10
        positions = [(float(index) if index < 3 else 3.0, 0.0, 0.0) for index in range(10)]
        self.assertEqual((0, 9), solvers.extend_contact_span(heights, 5, 6, 1.0, 10))
        self.assertEqual((3, 9), solvers.extend_contact_span(heights, 5, 6, 1.0, 10, positions, 0.5))

    def test_clamp_step_flattens_spike(self):
        vectors = [(float(index), 0.0, 0.0) for index in range(7)]
        vectors[3] = (3.0, 40.0, 0.0)
        result = solvers.clamp_step_vectors(vectors, 3, 3, 1.5)
        self.assertLess(result[3][1], 2.0)
        self.assertEqual(vectors[2], result[2])

    def test_limit_hinge_direction(self):
        upper, hinge = (0.0, -1.0, 0.0), (1.0, 0.0, 0.0)
        normal_bend = math_utils.normalize((0.0, -0.98, -0.2))
        backward_bend = math_utils.normalize((0.0, -0.98, 0.2))
        self.assertIsNone(solvers.limit_hinge_direction(upper, normal_bend, hinge, "backward", 0.0))
        fixed = solvers.limit_hinge_direction(upper, backward_bend, hinge, "backward", 0.0)
        self.assertAlmostEqual(0.0, math_utils.angle_between(upper, fixed), places=4)
        side_bend = math_utils.normalize((0.6, -0.8, 0.0))
        fixed_side = solvers.limit_hinge_direction(upper, side_bend, hinge, "side", 10.0)
        self.assertAlmostEqual(math.sin(math.radians(10.0)), math_utils.dot(fixed_side, hinge), places=4)


class TestRepairPresetsAndLadders(unittest.TestCase):
    def test_preset_merge_order(self):
        definition = registry.get_fix("foot_lock")
        merged = definition.merge_params({"blend": 9}, "still")
        self.assertEqual("still", merged["pin_at"])
        self.assertTrue(merged["extend_contact"])
        self.assertEqual(9, merged["blend"])
        with self.assertRaises(KeyError):
            definition.merge_params({}, "nope")

    def test_every_ladder_rung_exists(self):
        for check_key in registry.LADDERS:
            for rung in registry.get_ladder(check_key):
                registry.get_fix(rung["fix"]).get_preset(rung["preset"])

    def test_next_rungs_skip_failed(self):
        remaining = registry.next_rungs("foot_slide", ["foot_lock/default"])
        self.assertEqual("foot_lock/contact", remaining[0]["key"])
        self.assertEqual("foot_lock/default", registry.get_rung_key("foot_lock", ""))

    def test_manifest_rejects_unknown_preset(self):
        errors = manifest.validate_entry({"steps": [{"fix": "span_smooth", "preset": "huge", "frames": [1, 2]}]},
                                         tempfile.gettempdir())
        self.assertEqual(1, len(errors))


class TestRepairNewFixes(unittest.TestCase):
    def test_hips_follow_keeps_foot_still(self):
        host = build_leg_host()
        scene = RepairScene(host=host, template=build_template())
        before_hips = get_position(host, HIPS, 20)
        registry.get_fix("hips_follow").function(scene, (10, 20), [], {"side": "left", "blend": 3})
        travel = math_utils.distance(get_position(host, LEFT_FOOT, 10), get_position(host, LEFT_FOOT, 20))
        self.assertLess(travel, 0.01)
        self.assertNotAlmostEqual(before_hips[2], get_position(host, HIPS, 20)[2], places=3)
        self.assertAlmostEqual(before_hips[1], get_position(host, HIPS, 20)[1], places=6)

    def test_foot_floor_clamp_lifts_only_the_foot(self):
        host = build_leg_host(hips_step=0.0)
        for frame in (13, 14):
            host.local_frames[HIPS][frame] = translation_matrix((0.0, 90.0, 0.0))
        scene = RepairScene(host=host, template=build_template())
        result = registry.get_fix("foot_floor_clamp").function(scene, (13, 14), [],
                                                               {"side": "auto", "blend": 2, "floor": 10.0})
        self.assertAlmostEqual(10.0, get_position(host, LEFT_FOOT, 13)[1], places=4)
        self.assertAlmostEqual(90.0, get_position(host, HIPS, 13)[1], places=6)
        self.assertEqual(3, len(result["nodes"]))

    def test_spike_clamp_reduces_rotation_pop(self):
        host = build_leg_host(hips_step=0.0)
        popped = math_utils.compose_matrix((10.0, -5.0, 0.0), (0.5, 0.0, 0.0, 0.866))
        host.local_frames[LEFT_THIGH][14] = popped
        scene = RepairScene(host=host, template=build_template())
        registry.get_fix("spike_clamp").function(scene, (14, 14), ["left_up_leg"], {"channels": "rotate",
                                                                                     "factor": 1.5})
        result_angle = math_utils.rotation_angle_between(translation_matrix((0.0, 0.0, 0.0)),
                                                         host.local_frames[LEFT_THIGH][14])
        self.assertLess(result_angle, 1.0)

    def test_limit_clamp_needs_a_learned_hinge(self):
        scene = RepairScene(host=build_leg_host(), template=build_template())
        with self.assertRaises(ValueError):
            registry.get_fix("limit_clamp").function(
                scene, (10, 12), ["left_up_leg", "left_leg", "left_foot"],
                registry.get_fix("limit_clamp").merge_params({}, "knee"))
        self.assertEqual(FRAME_COUNT, len(scene.host.local_frames[LEFT_THIGH]))


class TestRepairPreviewHelpers(unittest.TestCase):
    def test_summarize_and_compare(self):
        before = preview.summarize_report({"score": 60, "status": "failed", "checks": [
            {"key": "foot_slide", "score": 70, "status": "warning", "spans": [[1, 2]], "offenders": []},
            {"key": "jitter", "score": 100, "status": "passed"},
            {"key": "balance", "status": "disabled"}]})
        after = preview.summarize_report({"score": 80, "status": "passed", "checks": [
            {"key": "foot_slide", "score": 95, "status": "passed"},
            {"key": "jitter", "score": 90, "status": "passed"}]})
        self.assertNotIn("balance", before["checks"])
        changes = preview.compare_checks(before, after)
        self.assertEqual(["jitter", "foot_slide"], [change["key"] for change in changes])
        self.assertEqual(-10, changes[0]["change"])


if __name__ == "__main__":
    unittest.main()
