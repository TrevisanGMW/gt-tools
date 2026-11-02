"""Tests for Auto Rigger build status tracking and sound lookup."""

import logging
import os
import unittest
from unittest.mock import MagicMock, patch

import gt.ui.resource_library as ui_res_lib
import gt.tools.auto_rigger.rigger_build_sounds as tools_rig_build_sounds
from gt.tools.auto_rigger.rigger_build_sounds import BuildStatus


class TestBuildLogMonitor(unittest.TestCase):
    """Tests the log monitor used to determine the final build status."""

    def setUp(self):
        """Creates an isolated logger for each test."""
        self.test_logger = logging.getLogger("gt_tests.auto_rigger.build_sounds")
        self.test_logger.propagate = False
        self.test_logger.setLevel(logging.DEBUG)
        if not self.test_logger.handlers:
            self.test_logger.addHandler(logging.NullHandler())  # Avoids the "last resort" stderr output

    def test_no_records_is_success(self):
        """Checks a quiet build resolves to success."""
        with tools_rig_build_sounds.BuildLogMonitor(loggers=[self.test_logger]) as log_monitor:
            self.test_logger.info("Building")
        expected = BuildStatus.SUCCESS
        result = log_monitor.get_status()
        self.assertEqual(expected, result)

    def test_warning_record_is_warning(self):
        """Checks a logged warning resolves to the warning status."""
        with tools_rig_build_sounds.BuildLogMonitor(loggers=[self.test_logger]) as log_monitor:
            self.test_logger.warning("Something is off")
        expected = BuildStatus.WARNING
        result = log_monitor.get_status()
        self.assertEqual(expected, result)

    def test_error_record_is_failure(self):
        """Checks a logged error resolves to the failure status."""
        with tools_rig_build_sounds.BuildLogMonitor(loggers=[self.test_logger]) as log_monitor:
            self.test_logger.warning("Something is off")
            self.test_logger.error("Something broke")
        expected = BuildStatus.FAILURE
        result = log_monitor.get_status()
        self.assertEqual(expected, result)

    def test_build_failed_is_failure(self):
        """Checks a raised build exception overrides a quiet log."""
        log_monitor = tools_rig_build_sounds.BuildLogMonitor(loggers=[self.test_logger])
        expected = BuildStatus.FAILURE
        result = log_monitor.get_status(build_failed=True)
        self.assertEqual(expected, result)

    def test_handler_detached_on_exit(self):
        """Checks records after the context are ignored and the handler is removed."""
        with tools_rig_build_sounds.BuildLogMonitor(loggers=[self.test_logger]) as log_monitor:
            pass
        self.test_logger.error("After build")
        expected = BuildStatus.SUCCESS
        result = log_monitor.get_status()
        self.assertEqual(expected, result)
        self.assertNotIn(log_monitor, self.test_logger.handlers)

    def test_handler_detached_on_exception(self):
        """Checks the handler is removed and the exception propagates."""
        log_monitor = tools_rig_build_sounds.BuildLogMonitor(loggers=[self.test_logger])
        with self.assertRaises(RuntimeError):
            with log_monitor:
                raise RuntimeError("Build failed")
        self.assertNotIn(log_monitor, self.test_logger.handlers)


class TestBuildSounds(unittest.TestCase):
    """Tests build status sound lookup and playback."""

    def test_every_status_has_an_existing_sound(self):
        """Checks each build status resolves to a packaged sound file."""
        for build_status in (BuildStatus.SUCCESS, BuildStatus.WARNING, BuildStatus.FAILURE):
            sound_path = tools_rig_build_sounds.get_sound_for_build_status(build_status)
            self.assertTrue(os.path.isfile(sound_path), build_status)

    def test_status_sound_mapping(self):
        """Checks each status maps to its matching status sound."""
        expected = [
            ui_res_lib.Sound.status_success,
            ui_res_lib.Sound.status_warning,
            ui_res_lib.Sound.status_failure,
        ]
        result = [
            tools_rig_build_sounds.get_sound_for_build_status(BuildStatus.SUCCESS),
            tools_rig_build_sounds.get_sound_for_build_status(BuildStatus.WARNING),
            tools_rig_build_sounds.get_sound_for_build_status(BuildStatus.FAILURE),
        ]
        self.assertEqual(expected, result)

    def test_unknown_status_has_no_sound(self):
        """Checks unknown statuses are silent."""
        expected = ""
        result = tools_rig_build_sounds.get_sound_for_build_status("unknown")
        self.assertEqual(expected, result)

    @patch("gt.tools.auto_rigger.rigger_build_sounds.ui_res_lib.play_sound_file")
    def test_play_build_status_sound(self, mock_play_sound_file):
        """Checks playback receives the sound path for the given status."""
        mock_play_sound_file.return_value = True
        result = tools_rig_build_sounds.play_build_status_sound(BuildStatus.WARNING)
        mock_play_sound_file.assert_called_once_with(ui_res_lib.Sound.status_warning)
        self.assertTrue(result)


class TestRunBuildWithStatusSound(unittest.TestCase):
    """Tests the controller build wrapper without constructing the Qt interface."""

    def setUp(self):
        """Creates a controller instance bypassing its constructor."""
        from gt.tools.auto_rigger.rigger_controller import RiggerController

        self.test_logger = logging.getLogger("gt_tests.auto_rigger.build_wrapper")
        self.test_logger.propagate = False
        self.controller = object.__new__(RiggerController)
        self.controller.get_build_status_loggers = MagicMock(return_value=[self.test_logger])

    @patch("gt.tools.auto_rigger.rigger_controller.tools_rig_build_sounds.play_build_status_sound")
    def test_disabled_preference_plays_nothing(self, mock_play_sound):
        """Checks the build runs silently when the preference is off."""
        self.controller._on_build_play_sound = False
        build_function = MagicMock()
        self.controller.run_build_with_status_sound(build_function)
        build_function.assert_called_once_with()
        mock_play_sound.assert_not_called()

    @patch("gt.tools.auto_rigger.rigger_controller.tools_rig_build_sounds.play_build_status_sound")
    def test_clean_build_plays_success(self, mock_play_sound):
        """Checks a clean build plays the success sound."""
        self.controller._on_build_play_sound = True
        self.controller.run_build_with_status_sound(MagicMock())
        mock_play_sound.assert_called_once_with(BuildStatus.SUCCESS)

    @patch("gt.tools.auto_rigger.rigger_controller.tools_rig_build_sounds.play_build_status_sound")
    def test_warning_build_plays_warning(self, mock_play_sound):
        """Checks a build that logs a warning plays the warning sound."""
        self.controller._on_build_play_sound = True
        self.controller.run_build_with_status_sound(lambda: self.test_logger.warning("Missing geometry"))
        mock_play_sound.assert_called_once_with(BuildStatus.WARNING)

    @patch("gt.tools.auto_rigger.rigger_controller.tools_rig_build_sounds.play_build_status_sound")
    def test_raising_build_plays_failure_and_reraises(self, mock_play_sound):
        """Checks a raising build plays the failure sound without hiding the exception."""
        self.controller._on_build_play_sound = True
        build_function = MagicMock(side_effect=RuntimeError("Build failed"))
        with self.assertRaises(RuntimeError):
            self.controller.run_build_with_status_sound(build_function)
        mock_play_sound.assert_called_once_with(BuildStatus.FAILURE)


if __name__ == "__main__":
    unittest.main()
