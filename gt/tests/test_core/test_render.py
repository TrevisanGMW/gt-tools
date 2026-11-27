import math
import os
import sys
import unittest

core_tests_dir = os.path.dirname(__file__)
package_root_dir = os.path.dirname(os.path.dirname(core_tests_dir))
for path in (package_root_dir, os.path.dirname(package_root_dir)):
    if path not in sys.path:
        sys.path.append(path)

from gt.core import render


def make_pose(offset_x=0.0, height=1.0, facing=(1.0, 0.0)):
    """Builds a small standing pose facing a ground direction."""
    forward_x, forward_z = facing
    right = (-forward_z, forward_x)

    def point(forward, side, up):
        return (offset_x + forward_x * forward + right[0] * side, up, forward_z * forward + right[1] * side)

    return {
        "pelvis": point(0, 0, height), "chest": point(0, 0, height + 0.5),
        "left_upper_leg": point(0, -0.1, height), "right_upper_leg": point(0, 0.1, height),
        "left_knee": point(0, -0.1, height / 2), "right_knee": point(0, 0.1, height / 2),
        "left_foot": point(0, -0.1, 0), "right_foot": point(0, 0.1, 0),
        "left_toe": point(0.15, -0.1, 0), "right_toe": point(0.15, 0.1, 0),
    }


class TestRender(unittest.TestCase):
    def test_heading_follows_toes_for_any_world_direction(self):
        for facing in ((1.0, 0.0), (0.0, 1.0), (-1.0, 0.0), (0.0, -1.0)):
            expected = facing
            result = render.get_heading(make_pose(facing=facing))
            self.assertAlmostEqual(expected[0], result[0])
            self.assertAlmostEqual(expected[1], result[1])

    def test_side_projection_is_independent_of_world_position(self):
        near = make_pose(offset_x=0.0)
        far = make_pose(offset_x=500.0, facing=(0.0, 1.0))
        results = []
        for sample in (near, far):
            heading = render.get_heading(sample)
            pelvis = sample["pelvis"]
            results.append(render.project_point(sample["left_toe"], pelvis, heading, "side"))
        self.assertAlmostEqual(results[0][0], results[1][0])
        self.assertAlmostEqual(results[0][1], results[1][1])

    def test_bones_skip_missing_roles(self):
        bones = render.build_bones({"pelvis", "left_upper_leg", "left_foot"})
        self.assertEqual([("pelvis", "left_upper_leg", "left"), ("left_upper_leg", "left_foot", "left")], bones)

    def test_pose_selection_favors_motion_and_keeps_ends(self):
        positions = [make_pose() for _ in range(60)] + [make_pose(height=1.0 + 0.05 * step) for step in range(20)]
        positions += [make_pose(height=2.0) for _ in range(60)]
        result = render.select_pose_indices(positions, 6, 1.0)
        self.assertEqual(6, len(result))
        self.assertEqual((0, len(positions) - 1), (result[0], result[-1]))
        self.assertTrue(sum(1 for index in result if 55 <= index <= 85) >= 2)

    def test_pose_selection_returns_all_frames_for_short_spans(self):
        self.assertEqual([0, 1, 2], render.select_pose_indices([make_pose()] * 3, 6, 1.0))

    def test_travel_is_measured_in_leg_lengths(self):
        positions = [make_pose(offset_x=step * 0.5) for step in range(5)]
        result = render.measure_travel(positions, 2.0)
        self.assertAlmostEqual(1.0, result["net"])
        self.assertEqual((1.0, 0.0), tuple(round(value, 6) for value in result["direction"]))
        self.assertFalse(math.isnan(result["path"]))


if __name__ == "__main__":
    unittest.main()
