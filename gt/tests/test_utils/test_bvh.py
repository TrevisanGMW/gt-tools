import os
import sys
import unittest

# Import Tested Script
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
import gt.utils.bvh as utils_bvh

SAMPLE_BVH = """HIERARCHY
ROOT Hips
{
    OFFSET 0.0 0.0 0.0
    CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation
    JOINT Spine
    {
        OFFSET 0.0 10.0 0.0
        CHANNELS 3 Zrotation Xrotation Yrotation
        End Site
        {
            OFFSET 0.0 5.0 0.0
        }
    }
    JOINT LeftLeg
    {
        OFFSET 5.0 -2.0 0.0
        CHANNELS 3 Xrotation Yrotation Zrotation
    }
}
MOTION
Frames: 2
Frame Time: 0.04
1 2 3 10 20 30 1 2 3 7 8 9
4 5 6 40 50 60 4 5 6 10 11 12
"""


class TestBvhUtils(unittest.TestCase):
    """Checks the pure BVH parser and timing helpers."""

    def setUp(self):
        self.bvh_data = utils_bvh.parse_bvh_text(SAMPLE_BVH)

    def test_hierarchy(self):
        expected = [("Hips", -1), ("Spine", 0), ("LeftLeg", 0)]
        result = [(joint.name, joint.parent_index) for joint in self.bvh_data.joints]
        self.assertEqual(expected, result)

    def test_offsets_and_end_site(self):
        self.assertEqual((5.0, -2.0, 0.0), self.bvh_data.joints[2].offset)
        self.assertEqual((0.0, 5.0, 0.0), self.bvh_data.joints[1].end_site_offset)
        self.assertIsNone(self.bvh_data.joints[2].end_site_offset)

    def test_motion(self):
        self.assertEqual(2, self.bvh_data.frame_count)
        self.assertEqual(12, self.bvh_data.channel_count)
        self.assertAlmostEqual(25.0, self.bvh_data.fps)

    def test_channel_values(self):
        expected = [8.0, 11.0]
        self.assertEqual(expected, self.bvh_data.get_channel_values(2, "yrotation"))
        self.assertEqual([], self.bvh_data.get_channel_values(1, "Xposition"))

    def test_rotate_order(self):
        self.assertEqual(4, utils_bvh.get_maya_rotate_order(self.bvh_data.joints[0].get_rotation_axes()))  # yxz
        self.assertEqual(5, utils_bvh.get_maya_rotate_order("xyz"))  # zyx
        self.assertEqual(0, utils_bvh.get_maya_rotate_order(""))

    def test_frame_times(self):
        expected = [1.0, 2.2, 3.4]
        result = utils_bvh.build_frame_times(3, 0.04, 30.0, 1.0, utils_bvh.TIME_MODE_REAL_TIME)
        self.assertEqual(expected, [round(value, 6) for value in result])
        expected = [1.0, 2.0, 3.0]
        result = utils_bvh.build_frame_times(3, 0.04, 30.0, 1.0, utils_bvh.TIME_MODE_FRAME_PER_FRAME)
        self.assertEqual(expected, result)

    def test_invalid_files(self):
        with self.assertRaises(ValueError):
            utils_bvh.parse_bvh_text("not a bvh")
        truncated_text = SAMPLE_BVH.replace("4 5 6 40 50 60 4 5 6 10 11 12\n", "")
        with self.assertRaises(ValueError):
            utils_bvh.parse_bvh_text(truncated_text)
