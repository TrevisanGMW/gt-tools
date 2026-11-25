import os
import unittest

import gt.ui.resource_library as ui_res_lib
from gt.tools.batch_processor.tracker import tracker_constants
from gt.tools.batch_processor.tracker import tracker_sounds


class TestTrackerSounds(unittest.TestCase):
    """Tests import-safe tracker sound lookup."""

    def test_every_health_state_has_an_existing_sound(self):
        """Checks each health state resolves to a packaged sound file."""
        for health_state in (
            tracker_constants.HealthState.STARTING,
            tracker_constants.HealthState.RUNNING,
            tracker_constants.HealthState.COMPLETED,
            tracker_constants.HealthState.WARNING,
            tracker_constants.HealthState.ERROR,
            tracker_constants.HealthState.ABORTED,
        ):
            sound_path = tracker_sounds.get_sound_for_health_state(health_state)
            self.assertTrue(os.path.isfile(sound_path), health_state)

    def test_completed_maps_to_success_sound(self):
        """Checks the completed state uses the success sound."""
        expected = ui_res_lib.Sound.status_success
        result = tracker_sounds.get_sound_for_health_state(tracker_constants.HealthState.COMPLETED)
        self.assertEqual(expected, result)

    def test_unknown_state_has_no_sound(self):
        """Checks unknown states resolve to an empty path."""
        expected = ""
        result = tracker_sounds.get_sound_for_health_state("unknown")
        self.assertEqual(expected, result)
