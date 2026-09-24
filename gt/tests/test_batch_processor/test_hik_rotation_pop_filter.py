"""Pure Python regression tests for the HumanIK rotation pop sample."""

import unittest
from unittest import mock

from gt.tools.batch_processor.tasks.scripts.hik_retarget import smooth_rotation_pops as pop_filter


class TestRotationPopDetection(unittest.TestCase):
    """Tests motion discrimination, namespaces, and bounded filter windows."""

    def detect(self, values, times=None):
        """Runs the detector with predictable test thresholds.

        Args:
            values (list): Rotation values in degrees.
            times (list, optional): Key times; defaults to consecutive frames.

        Returns:
            list: Detected transition frames.
        """
        if times is None:
            times = list(range(len(values)))
        return pop_filter.detect_pop_frames(times, values, 20.0, 4.0, 10.0, 1.5)

    def test_isolated_jump_and_single_frame_spike(self):
        """Finds both a lasting discontinuity and the two edges of a spike."""
        self.assertEqual([10], self.detect([0.0] * 10 + [80.0] * 10))
        self.assertEqual([10, 11], self.detect([0.0] * 10 + [80.0] + [0.0] * 10))

    def test_fast_smooth_motion_and_small_noise_are_preserved(self):
        """Requires both absolute speed and a local outlier."""
        self.assertEqual([], self.detect([frame * 30.0 for frame in range(30)]))
        self.assertEqual([], self.detect([0.0] * 10 + [2.0] + [0.0] * 10))
        self.assertEqual([], self.detect([frame * frame for frame in range(30)]))

    def test_wraps_and_sparse_keys_do_not_trigger(self):
        """Rejects Euler branch wraps and motion spanning long unkeyed gaps."""
        self.assertEqual([], self.detect([170.0, 175.0, 179.0, -179.0, -175.0, -170.0]))
        self.assertEqual([], self.detect([0.0, 0.0, 80.0, 80.0], [1.0, 2.0, 20.0, 21.0]))
        self.assertEqual([], self.detect([]))
        self.assertEqual([], self.detect([0.0, 90.0]))

    def test_fractional_frames_use_speed_instead_of_raw_delta(self):
        """Detects a small change that happens unusually quickly."""
        values = [0.0] * 10 + [10.0] * 10
        times = [frame * 0.25 for frame in range(20)]
        self.assertEqual([2.5], self.detect(values, times))

    def test_windows_merge_and_clip(self):
        """Merges nearby detections and respects explicit or keyed bounds."""
        result = pop_filter.build_filter_windows([20, 21, 20, 60, 95], 15, 100, 10, 10)
        self.assertEqual([(15, 31), (50, 70), (85, 100)], result)
        self.assertEqual([], pop_filter.build_filter_windows([20], 30, 25, 10, 10))

    def test_namespace_matching(self):
        """Handles root, nested, and exact namespaces without substring matches."""
        names = ["upperarm_r", "upperarm_l"]
        self.assertTrue(pop_filter.matches_joint_name("|rig|shot:hero:upperarm_r", names))
        self.assertTrue(pop_filter.matches_joint_name("|rig|upperarm_l", names, False, ""))
        self.assertTrue(pop_filter.matches_joint_name("shot:hero:upperarm_r", names, False, ":shot:hero:"))
        self.assertFalse(pop_filter.matches_joint_name("shot:hero:upperarm_r", names, False, "hero"))
        self.assertFalse(pop_filter.matches_joint_name("hero:upperarm_r_extra", names))

    def test_empty_batch_target_never_falls_back_to_source(self):
        """An empty imported target produces no scene-wide lookup."""
        commands = mock.Mock()
        self.assertEqual([], pop_filter.get_target_joints(commands, {"imported_target_nodes": []}))
        commands.ls.assert_not_called()

    def test_invalid_settings_fail_before_filtering(self):
        """Rejects invalid frequency, thresholds, and reversed ranges."""
        for setting, value in (("CUTOFF_FREQUENCY", 15), ("MIN_SPEED", -1),
                               ("SPIKE_RATIO", 1), ("FRAMES_BEFORE", float("nan"))):
            with self.subTest(setting=setting), mock.patch.object(pop_filter, setting, value):
                with self.assertRaises(ValueError):
                    pop_filter.validate_settings(30)
        with mock.patch.multiple(pop_filter, START_FRAME=20, END_FRAME=10):
            with self.assertRaises(ValueError):
                pop_filter.validate_settings(30)


if __name__ == "__main__":
    unittest.main()
