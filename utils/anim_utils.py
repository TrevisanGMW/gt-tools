"""
Animation Utilities
"""
import maya.cmds as cmds
from feedback_utils import FeedbackMessage
import logging

# Logging Setup
logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def delete_time_keyframes():
    """
    Deletes time (animation) keyframes. (Set Driven Keys are not included)
    Returns:
        int: number of keyframes deleted during the operation
    """
    function_name = 'Delete Time Keyframes'
    cmds.undoInfo(openChunk=True, chunkName=function_name)
    deleted_counter = 0
    try:
        keys_ta = cmds.ls(type='animCurveTA')  # time-angle (default keys - time as input)
        keys_tl = cmds.ls(type='animCurveTL')  # time-distance
        keys_tt = cmds.ls(type='animCurveTT')  # time-time
        keys_tu = cmds.ls(type='animCurveTU')  # time-double

        time_keyframes = keys_ta + keys_tl + keys_tt + keys_tu
        for obj in time_keyframes:
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
        keys_ul = cmds.ls(type='animCurveUL')  # double-distance - Driven Keys (double as input)
        keys_ua = cmds.ls(type='animCurveUA')  # double-angle
        keys_ut = cmds.ls(type='animCurveUT')  # double-time
        keys_uu = cmds.ls(type='animCurveUU')  # double-double

        double_keyframes = keys_ul + keys_ua + keys_ut + keys_uu
        for obj in double_keyframes:
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
