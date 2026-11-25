"""Tests for Retargeter completion status and sound lookup."""

import os
import unittest
from unittest.mock import patch

import gt.ui.resource_library as ui_res_lib
import gt.tools.retargeter.retargeter_sounds as tools_retargeter_sounds
from gt.tools.retargeter.retargeter_sounds import RetargetStatus


class TestRetargeterSounds(unittest.TestCase):
    """Tests the import-safe retarget status helpers."""

    def test_no_failures_is_success(self):
        """Checks a run without failures resolves to success."""
        expected = RetargetStatus.SUCCESS
        result = tools_retargeter_sounds.get_retarget_status(failed_count=0, processed_count=3)
        self.assertEqual(expected, result)

    def test_nothing_processed_is_success(self):
        """Checks a run where every file was skipped resolves to success."""
        expected = RetargetStatus.SUCCESS
        result = tools_retargeter_sounds.get_retarget_status(failed_count=0, processed_count=0)
        self.assertEqual(expected, result)

    def test_partial_failures_is_warning(self):
        """Checks a run where only some files failed resolves to warning."""
        expected = RetargetStatus.WARNING
        result = tools_retargeter_sounds.get_retarget_status(failed_count=1, processed_count=3)
        self.assertEqual(expected, result)

    def test_all_failures_is_failure(self):
        """Checks a run where every attempted file failed resolves to failure."""
        expected = RetargetStatus.FAILURE
        result = tools_retargeter_sounds.get_retarget_status(failed_count=2, processed_count=2)
        self.assertEqual(expected, result)

    def test_every_status_has_an_existing_sound(self):
        """Checks each status resolves to a packaged sound file."""
        for retarget_status in (RetargetStatus.SUCCESS, RetargetStatus.WARNING, RetargetStatus.FAILURE):
            sound_path = tools_retargeter_sounds.get_sound_for_retarget_status(retarget_status)
            self.assertTrue(os.path.isfile(sound_path), retarget_status)

    def test_unknown_status_has_no_sound(self):
        """Checks unknown statuses are silent."""
        expected = ""
        result = tools_retargeter_sounds.get_sound_for_retarget_status("unknown")
        self.assertEqual(expected, result)

    @patch("gt.tools.retargeter.retargeter_sounds.ui_res_lib.play_sound_file")
    def test_play_retarget_status_sound(self, mock_play_sound_file):
        """Checks playback receives the sound path for the given status."""
        tools_retargeter_sounds.play_retarget_status_sound(RetargetStatus.FAILURE)
        mock_play_sound_file.assert_called_once_with(ui_res_lib.Sound.status_failure)

    def test_tracker_sound_names_exist(self):
        """Checks the file names hardcoded in the multi-process tracker exist in the sounds folder."""
        sounds_dir = ui_res_lib.ResourceDirConstants.DIR_SOUNDS
        for sound_name in ("success.wav", "warning.wav", "failure.wav"):
            self.assertTrue(os.path.isfile(os.path.join(sounds_dir, sound_name)), sound_name)


if __name__ == "__main__":
    unittest.main()
