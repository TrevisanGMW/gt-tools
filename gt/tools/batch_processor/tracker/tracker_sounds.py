"""Status sound playback for the standalone Batch Processor tracker."""

import logging

import gt.ui.resource_library as ui_res_lib

from gt.tools.batch_processor.tracker import tracker_constants

logger = logging.getLogger(__name__)


def get_sound_for_health_state(health_state):
    """Gets the sound file that represents a tracker health state.

    Args:
        health_state (str): Value from ``tracker_constants.HealthState``.

    Returns:
        str: Sound file path, or an empty string when the state has no sound.
    """
    sounds = {
        tracker_constants.HealthState.STARTING: ui_res_lib.Sound.status_starting,
        tracker_constants.HealthState.RUNNING: ui_res_lib.Sound.status_running,
        tracker_constants.HealthState.COMPLETED: ui_res_lib.Sound.status_success,
        tracker_constants.HealthState.WARNING: ui_res_lib.Sound.status_warning,
        tracker_constants.HealthState.ERROR: ui_res_lib.Sound.status_failure,
        tracker_constants.HealthState.ABORTED: ui_res_lib.Sound.status_aborted,
    }
    return sounds.get(health_state, "")


def play_health_state_sound(health_state):
    """Plays the sound matching a tracker health state.

    Args:
        health_state (str): Value from ``tracker_constants.HealthState``.

    Returns:
        bool: True when playback was started.
    """
    return ui_res_lib.play_sound_file(get_sound_for_health_state(health_state))
