"""
Retargeter Sounds - Resolves the final retarget status and plays a matching status sound.

Import Line:
    import gt.tools.retargeter.retargeter_sounds as tools_retargeter_sounds
"""

import gt.ui.resource_library as ui_res_lib


class RetargetStatus:
    def __init__(self):
        """
        Final status values for a retarget operation.
        """

    SUCCESS = "success"
    WARNING = "warning"
    FAILURE = "failure"


def get_retarget_status(failed_count, processed_count):
    """
    Gets the final retarget status from the number of failed files.

    Args:
        failed_count (int): Number of files that failed to retarget.
        processed_count (int): Number of files that attempted to retarget (skipped files are not included).

    Returns:
        str: Value from "RetargetStatus". Failure when every attempted file failed,
             warning when only some failed, success otherwise.
    """
    if failed_count <= 0:
        return RetargetStatus.SUCCESS
    if failed_count >= processed_count:
        return RetargetStatus.FAILURE
    return RetargetStatus.WARNING


def get_sound_for_retarget_status(retarget_status):
    """
    Gets the sound file that represents a retarget status.

    Args:
        retarget_status (str): Value from "RetargetStatus".

    Returns:
        str: Sound file path, or an empty string when the status has no sound.
    """
    sounds = {
        RetargetStatus.SUCCESS: ui_res_lib.Sound.status_success,
        RetargetStatus.WARNING: ui_res_lib.Sound.status_warning,
        RetargetStatus.FAILURE: ui_res_lib.Sound.status_failure,
    }
    return sounds.get(retarget_status, "")


def play_retarget_status_sound(retarget_status):
    """
    Plays the sound matching a retarget status.

    Args:
        retarget_status (str): Value from "RetargetStatus".

    Returns:
        bool: True when playback was started.
    """
    return ui_res_lib.play_sound_file(get_sound_for_retarget_status(retarget_status))
