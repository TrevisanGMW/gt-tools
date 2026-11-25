"""Regression tests for eased foot locks and independent contact timing."""

import unittest

from gt.core.motion_eval import math_utils
from gt.core.motion_eval.repairs import lock_timing
from gt.core.motion_eval.repairs import registry
from gt.core.motion_eval.repairs import fixes_lock
from gt.core.motion_eval.repairs import solvers
from gt.core.motion_eval.repairs.scene import RepairScene
from gt.tests.test_core.test_motion_eval_repairs import LEFT_FOOT
from gt.tests.test_core.test_motion_eval_repairs import LEFT_KNEE
from gt.tests.test_core.test_motion_eval_repairs import LEFT_THIGH
from gt.tests.test_core.test_motion_eval_repairs import HIPS
from gt.tests.test_core.test_motion_eval_repairs import build_leg_host
from gt.tests.test_core.test_motion_eval_repairs import build_template
from gt.tests.test_core.test_motion_eval_repairs import translation_matrix


class TestLockTiming(unittest.TestCase):
    """Checks duration scaling, explicit overrides and bounded staggering."""

    def test_defaults_scale_with_frame_rate(self):
        """Keeps the default durations constant in seconds."""
        self.assertEqual((12, 16, 8), lock_timing.resolve_timing({}, 30))
        self.assertEqual((24, 32, 16), lock_timing.resolve_timing({}, 60))
        self.assertEqual((10, 13, 6), lock_timing.resolve_timing({}, 24))

    def test_explicit_durations_and_legacy_blend(self):
        """Preserves explicit symmetric blends and independent duration overrides."""
        self.assertEqual((3, 3, 8), lock_timing.resolve_timing({"blend": 3}, 30))
        self.assertEqual((0, 7, 0), lock_timing.resolve_timing(
            {"blend": 3, "blend_in": 0, "blend_out": 7, "stagger": 0}, 60))

    def test_stagger_order(self):
        """Offsets the leading and following foot in opposite directions."""
        spans = [(193, 206), (193, 206)]
        limits = [(170, 230), (170, 230)]
        self.assertEqual([(189, 202), (197, 210)], lock_timing.stagger_spans(spans, limits, 8))
        self.assertEqual([(197, 210), (189, 202)], lock_timing.stagger_spans(spans, limits, 8, 1))

    def test_stagger_respects_contact_and_short_holds(self):
        """Keeps full locks inside available contact, including tiny intervals."""
        spans = [(10, 12), (10, 12)]
        self.assertEqual([(10, 11), (11, 12)], lock_timing.stagger_spans(spans, spans, 8))
        self.assertEqual([(10, 10), (10, 10)], lock_timing.stagger_spans(
            [(10, 10), (10, 10)], [(0, 20), (0, 20)], 8))
        self.assertEqual([(10, 12)], lock_timing.stagger_spans([(10, 12)], [(0, 20)], 8))

    def test_asymmetric_eased_weights(self):
        """Uses smooth entry and release ramps with exact zero outside them."""
        weights = solvers.build_blend_weights(14, 4, 6, 3, 5)
        self.assertEqual(0.0, weights[0])
        self.assertEqual([1.0, 1.0, 1.0], weights[4:7])
        self.assertEqual([0.0, 0.0], weights[12:])
        self.assertAlmostEqual(0.15625, weights[1])
        self.assertGreater(weights[7], weights[8])
        self.assertGreater(weights[8], weights[9])

    def test_pin_targets_extend_into_blend_window(self):
        """Provides a real correction outside the hold instead of a no-op ramp."""
        positions = [(float(index), float(index), 2.0 * index) for index in range(7)]
        targets = solvers.build_pin_targets(positions, 2, 4)
        self.assertEqual((3.0, 0.0, 6.0), targets[0])
        self.assertEqual((3.0, 6.0, 6.0), targets[-1])

    def test_foot_lock_eases_only_inside_issue(self):
        """Preserves every surrounding leg pose and both edge samples."""
        host = build_leg_host(hips_step=0.0)
        host.local_frames[HIPS][15] = translation_matrix((0.0, 95.0, 5.0))
        scene = RepairScene(host=host, template=build_template())
        nodes = [LEFT_THIGH, LEFT_KNEE, LEFT_FOOT]
        before = host.sample_world_matrices(nodes, 0, 29)
        result = registry.get_fix("foot_lock").function(
            scene, (10, 20), [], {"side": "left", "max_extension": 1.0, "extend_contact": True})
        after = host.sample_world_matrices(nodes, 0, 29)
        for node in nodes:
            for frame in list(range(12)) + list(range(19, 30)):
                self.assertEqual(before[node][frame], after[node][frame])
        original = math_utils.matrix_position(before[LEFT_FOOT][15])
        corrected = math_utils.matrix_position(after[LEFT_FOOT][15])
        self.assertGreater(math_utils.distance(original, corrected), 1.0)
        self.assertEqual("applied", result["locks"][0]["status"])
        for unused_node, frames, unused_channels in host.key_calls:
            self.assertGreaterEqual(min(frames), 12)
            self.assertLessEqual(max(frames), 18)

    def test_lock_does_not_key_outside_playback_range(self):
        """Clips default easing to the animation range."""
        host = build_leg_host()
        scene = RepairScene(host=host, template=build_template())
        registry.get_fix("foot_lock").function(scene, (1, 3), [], {"side": "left"})
        for unused_node, frames, unused_channels in host.key_calls:
            self.assertGreaterEqual(min(frames), 0)
            self.assertLessEqual(max(frames), 29)

    def test_default_pair_staggers_and_leading_side_can_reverse(self):
        """Applies automatic staggering through the public repair entry point."""
        for lead, expected in (("left", [(13, 13), (17, 17)]),
                               ("right", [(17, 17), (13, 13)]),
                               ("auto", [(17, 17), (13, 13)])):
            host = build_leg_host(hips_step=0.05)
            template = build_template()
            parent = HIPS
            for left_node, right_node, role in (
                    (LEFT_THIGH, "right_up_leg_jnt", "right_up_leg"),
                    (LEFT_KNEE, "right_leg_jnt", "right_leg"),
                    (LEFT_FOOT, "right_foot_jnt", "right_foot")):
                host.parents[right_node] = parent
                host.local_frames[right_node] = list(host.local_frames[left_node])
                template["roles"][role] = [right_node]
                parent = right_node
            host.local_frames["right_foot_jnt"] = [
                list(matrix) for matrix in host.local_frames["right_foot_jnt"]]
            for frame, matrix in enumerate(host.local_frames["right_foot_jnt"]):
                matrix[14] -= frame * 0.05
            scene = RepairScene(host=host, template=template)
            result = registry.get_fix("foot_lock").function(
                scene, (10, 20), [], {"lead_side": lead})
            self.assertEqual(expected, [tuple(lock["frames"]) for lock in result["locks"]])
            self.assertEqual([[10, 20], [10, 20]], [lock["issue_frames"] for lock in result["locks"]])

    def test_out_of_range_lock_fails_clearly(self):
        """Rejects a hold beyond the available animation instead of sampling an empty window."""
        scene = RepairScene(host=build_leg_host(), template=build_template())
        with self.assertRaises(ValueError):
            registry.get_fix("foot_lock").function(scene, (100, 110), [], {"side": "left"})

    def test_short_spans_skip_without_extending_contact(self):
        """Preserves short intervals instead of creating room by editing adjacent frames."""
        for frame_count in range(1, 7):
            host = build_leg_host()
            scene = RepairScene(host=host, template=build_template())
            result = registry.get_fix("foot_lock").function(
                scene, (10, 9 + frame_count), [],
                {"side": "left", "extend_contact": True, "extend_max": 100})
            self.assertEqual([], host.key_calls)
            self.assertEqual("skipped", result["locks"][0]["status"])
            self.assertTrue(result["warnings"])

    def test_bounded_weights_preserve_edges_and_fit_stagger(self):
        """Fits both phases inside the issue with unchanged interpolation guards."""
        for count in (7, 8, 14, 60):
            for offset in (-8, 0, 8):
                weights = lock_timing.bounded_weights(count, 12, 16, offset)
                self.assertEqual([0.0, 0.0], weights[:2])
                self.assertEqual([0.0, 0.0], weights[-2:])
                self.assertEqual(1.0, max(weights))
                self.assertTrue(all(0.0 <= value <= 1.0 for value in weights))
        self.assertEqual([0.0] * 6, lock_timing.bounded_weights(6, 12, 16))

    def test_target_cannot_overextend_leg(self):
        """Reduces the correction before an otherwise reachable target straightens the knee."""
        target, limited = fixes_lock.limit_target(
            (0.0, 0.0, 0.0), (0.0, -4.0, 3.0), (0.0, -8.0, 0.0),
            (0.0, -12.0, 0.0), 0.98)
        self.assertTrue(limited)
        self.assertAlmostEqual(9.8, math_utils.length(target), places=5)

    def test_lock_rejects_increased_slide_or_speed(self):
        """Leaves constant travel intact when a local pin would require catching up faster."""
        host = build_leg_host()
        scene = RepairScene(host=host, template=build_template())
        result = registry.get_fix("foot_lock").function(
            scene, (10, 20), [], {"side": "left", "max_extension": 1.0})
        self.assertEqual("skipped", result["locks"][0]["status"])
        self.assertEqual([], host.key_calls)
        self.assertIn("increase", result["locks"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
