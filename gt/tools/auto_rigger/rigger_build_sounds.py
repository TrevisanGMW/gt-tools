"""
Auto Rigger Build Sounds - Tracks the outcome of a build and plays a matching status sound.

Import Line:
    import gt.tools.auto_rigger.rigger_build_sounds as tools_rig_build_sounds
"""

import gt.ui.resource_library as ui_res_lib
import logging


class BuildStatus:
    def __init__(self):
        """
        Final status values for an Auto Rigger build operation.
        """

    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"


class BuildLogMonitor(logging.Handler):
    def __init__(self, loggers=None):
        """
        Logging handler that records the highest severity emitted while a build runs.
        Use it as a context manager to temporarily attach it to the given loggers.

        Args:
            loggers (list, optional): Loggers (logging.Logger) to monitor during the build.
        """
        super().__init__(level=logging.WARNING)
        self.loggers = list(loggers or [])
        self.highest_level = logging.NOTSET

    def emit(self, record):
        """
        Records the severity of a warning-or-higher log record.

        Args:
            record (logging.LogRecord): The emitted log record.
        """
        self.highest_level = max(self.highest_level, record.levelno)

    def __enter__(self):
        """
        Attaches this handler to the monitored loggers.

        Returns:
            BuildLogMonitor: This monitor.
        """
        for monitored_logger in self.loggers:
            if self not in monitored_logger.handlers:
                monitored_logger.addHandler(self)
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """
        Detaches this handler from the monitored loggers. Exceptions are never suppressed.

        Args:
            exc_type (type, None): Exception type raised inside the context, if any.
            exc_value (Exception, None): Exception raised inside the context, if any.
            exc_traceback (traceback, None): Traceback of the raised exception, if any.

        Returns:
            bool: Always False, so exceptions propagate.
        """
        for monitored_logger in self.loggers:
            monitored_logger.removeHandler(self)
        return False

    def get_status(self, build_failed=False):
        """
        Gets the final build status based on the recorded log severity.

        Args:
            build_failed (bool, optional): If True, the build raised an exception and is considered a failure.

        Returns:
            str: Value from "BuildStatus".
        """
        if build_failed or self.highest_level >= logging.ERROR:
            return BuildStatus.FAILURE
        if self.highest_level >= logging.WARNING:
            return BuildStatus.WARNING
        return BuildStatus.SUCCESS


def get_sound_for_build_status(build_status):
    """
    Gets the sound file that represents a build status.

    Args:
        build_status (str): Value from "BuildStatus".

    Returns:
        str: Sound file path, or an empty string when the status has no sound.
    """
    sounds = {
        BuildStatus.SUCCESS: ui_res_lib.Sound.status_success,
        BuildStatus.WARNING: ui_res_lib.Sound.status_warning,
        BuildStatus.FAILURE: ui_res_lib.Sound.status_failure,
    }
    return sounds.get(build_status, "")


def play_build_status_sound(build_status):
    """
    Plays the sound matching a build status.

    Args:
        build_status (str): Value from "BuildStatus".

    Returns:
        bool: True when playback was started.
    """
    return ui_res_lib.play_sound_file(get_sound_for_build_status(build_status))
