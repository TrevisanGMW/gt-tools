"""Status sound playback for the standalone Batch Processor tracker."""

import logging
import sys

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


def play_sound_file(sound_path):
    """Plays a sound file asynchronously without raising on failure.

    Args:
        sound_path (str): Path to a WAV file.

    Returns:
        bool: True when playback was started.
    """
    if not sound_path:
        return False
    try:
        if sys.platform == "win32":
            import winsound

            winsound.PlaySound(sound_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return True
        import gt.ui.qt_import as ui_qt

        if ui_qt.QtMultimedia is None:
            return False
        effect = ui_qt.QtMultimedia.QSoundEffect()
        effect.setSource(ui_qt.QtCore.QUrl.fromLocalFile(sound_path))
        effect.play()
        play_sound_file.active_effect = effect
        return True
    except Exception as exception:
        logger.debug(f"Unable to play sound '{sound_path}': {exception}")
        return False


def play_health_state_sound(health_state):
    """Plays the sound matching a tracker health state.

    Args:
        health_state (str): Value from ``tracker_constants.HealthState``.

    Returns:
        bool: True when playback was started.
    """
    return play_sound_file(get_sound_for_health_state(health_state))
