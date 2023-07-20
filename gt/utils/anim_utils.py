"""
Animation Utilities
"""
from gt.utils.feedback_utils import FeedbackMessage
import maya.cmds as cmds
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def get_time_keyframes():
    """
    Gets time (animation) keyframes.
    Set Driven Keys are not included.
    Returns:
        list: number of keyframes deleted during the operation
    """
    keys_ta = cmds.ls(type='animCurveTA') or []  # time-angle (default keys - time as input)
    keys_tl = cmds.ls(type='animCurveTL') or []  # time-distance
    keys_tt = cmds.ls(type='animCurveTT') or []  # time-time
    keys_tu = cmds.ls(type='animCurveTU') or []  # time-double

    time_keyframes = keys_ta + keys_tl + keys_tt + keys_tu
    return time_keyframes


def get_double_keyframes():
    """
    Gets double (driven) keyframes.
    Animation keyframes are not included.
    Returns:
        list: number of keyframes deleted during the operation
    """
    keys_ul = cmds.ls(type='animCurveUL') or []  # double-distance - Driven Keys (double as input)
    keys_ua = cmds.ls(type='animCurveUA') or []  # double-angle
    keys_ut = cmds.ls(type='animCurveUT') or []  # double-time
    keys_uu = cmds.ls(type='animCurveUU') or []  # double-double

    double_keyframes = keys_ul + keys_ua + keys_ut + keys_uu
    return double_keyframes


def delete_time_keyframes():
    """
    Deletes time (animation) keyframes. (Set Driven Keys are not included)
    Returns:
        list: number of keyframes deleted during the operation
    """
    function_name = 'Delete Time Keyframes'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    deleted_counter = 0
    try:
        for obj in get_time_keyframes():
            try:
                cmds.delete(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        feedback = FeedbackMessage(quantity=deleted_counter,
                                   singular="keyframe node was",
                                   plural="keyframe nodes were",
                                   conclusion="deleted.",
                                   zero_overwrite_message='No keyframes found in this scene.')
        feedback.print_inview_message()
        return deleted_counter
    except Exception as e:
        cmds.warning(str(e))
        return deleted_counter
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


def delete_double_keyframes():
    """
    Deletes Double (driven) keyframes. (Animation keyframes are not included)
    Returns:
        int: number of keyframes deleted during the operation
    """
    function_name = 'Delete Double Keyframes'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    deleted_counter = 0
    try:
        for obj in get_double_keyframes():
            try:
                cmds.delete(obj)
                deleted_counter += 1
            except Exception as e:
                logger.debug(str(e))

        feedback = FeedbackMessage(quantity=deleted_counter,
                                   singular="driven keyframe node was",
                                   plural="driven keyframe nodes were",
                                   conclusion="deleted.",
                                   zero_overwrite_message='No driven keyframes found in this scene.')
        feedback.print_inview_message()
        return deleted_counter
    except Exception as e:
        cmds.warning(str(e))
        return deleted_counter
    finally:
        cmds.undoInfo(closeChunk=True, chunkName=function_name)


if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    from pprint import pprint
    out = None
    out = delete_time_keyframes()
    pprint(out)
