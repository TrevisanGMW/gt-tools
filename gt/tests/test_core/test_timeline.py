import os
import sys
import tempfile
import unittest

# Import Tested Script
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
import gt.core.timeline as core_timeline


class TestTimelineCore(unittest.TestCase):
    """Checks the pure frame-range helpers of gt.core.timeline."""

    def test_combine_time_ranges_ignores_invalid_ranges(self):
        expected = (-5.0, 40.0)
        result = core_timeline.combine_time_ranges([(1, 10), None, (-5, 3), (20, 40), (9, 2), "bad"])
        self.assertEqual(expected, result)

    def test_combine_time_ranges_empty(self):
        self.assertIsNone(core_timeline.combine_time_ranges([None, (5, 1)]))

    def test_round_time_range_outward(self):
        expected = (1.0, 11.0)
        result = core_timeline.round_time_range((1.4, 10.2), core_timeline.ROUNDING_OUTWARD)
        self.assertEqual(expected, result)

    def test_round_time_range_nearest_and_none(self):
        self.assertEqual((1.0, 10.0), core_timeline.round_time_range((1.4, 10.2), core_timeline.ROUNDING_NEAREST))
        self.assertEqual((1.4, 10.2), core_timeline.round_time_range((1.4, 10.2), core_timeline.ROUNDING_NONE))
        self.assertIsNone(core_timeline.round_time_range(None))

    def test_build_sequential_offsets(self):
        expected = [0.0, 0.0, 5.0]  # The next clip starts on the previous clip's last frame.
        result = core_timeline.build_sequential_offsets([(1, 10), None, (5, 8)], gap_frames=0)
        self.assertEqual(expected, result)

    def test_build_sequential_offsets_with_start_and_gap(self):
        expected = [99.0, 101.0]
        result = core_timeline.build_sequential_offsets([(1, 10), (10, 20)], gap_frames=2, start_frame=100)
        self.assertEqual(expected, result)

    def test_parse_playback_range_uses_last_command(self):
        data = b'playbackOptions -min 1 -max 24;\nplaybackOptions -min 5 -max 120 -ast 1 -aet 200;'
        expected = (5.0, 120.0)
        self.assertEqual(expected, core_timeline.parse_playback_range_from_bytes(data))

    def test_read_stored_playback_range(self):
        temp_dir = tempfile.mkdtemp(prefix="gt_timeline_test_")
        scene_path = os.path.join(temp_dir, "scene.ma")
        with open(scene_path, "wb") as scene_file:
            scene_file.write(b'requires maya "2025";\nplaybackOptions -min 10 -max 70 -ast 10 -aet 70 ;\n')
        expected = (10.0, 70.0)
        self.assertEqual(expected, core_timeline.read_stored_playback_range(scene_path))
        self.assertIsNone(core_timeline.read_stored_playback_range(os.path.join(temp_dir, "missing.ma")))
        self.assertIsNone(core_timeline.read_stored_playback_range(os.path.join(temp_dir, "scene.fbx")))
