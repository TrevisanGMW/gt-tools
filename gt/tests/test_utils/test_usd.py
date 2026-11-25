import os
import sys
import unittest

# Import Tested Script
tools_root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
if tools_root_dir not in sys.path:
    sys.path.append(tools_root_dir)
import gt.utils.usd as utils_usd


class TestUsdFileInfo(unittest.TestCase):
    """Checks the pure USD metadata conversion."""

    def test_build_usd_info(self):
        expected = {"fps": 30.0, "linear_unit": "m", "up_axis": "z", "time_range": (1.0, 48.0)}
        result = utils_usd.build_usd_info(time_codes_per_second=30, start_time_code=1, end_time_code=48,
                                          meters_per_unit=1.0, up_axis="Z")
        self.assertEqual(expected, result)

    def test_build_usd_info_partial(self):
        expected = {"fps": 24.0, "linear_unit": "cm"}
        result = utils_usd.build_usd_info(frames_per_second=24, meters_per_unit=0.01, start_time_code=10,
                                          end_time_code=1)
        self.assertEqual(expected, result)
